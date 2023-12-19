import os
import speech_recognition as sr
from dotenv import load_dotenv
import requests
import pyttsx3
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import yagooglesearch
import ctranslate2
import transformers
# from llama_cpp import Llama
import sys
# import llamacpp
import json
import time

# V3
import torch
import pyaudio
import wave

import shutil
import streamlit as st

import asyncio
import json
import random
import string

import websockets

import HuggingChat

hc = HuggingChat.HuggingChat()

load_dotenv("./.env")

# Init streamlit frontend
if "msg_store" not in st.session_state:
    st.session_state.msg_store = {}

# Set the title and page layout
st.set_page_config(page_title="LLM Chat Interface", page_icon=":robot_face:")
st.title("LLM Chat Interface")

# Create a list to store the chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.session_state.needs_input = True

class AudioFile:
    chunk = 1024

    def __init__(self, file):
        """ Init audio stream """ 
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True
        )

    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.chunk)
        while data != b'':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """ 
        self.stream.close()
        self.p.terminate()

language = 'en'
model_id = 'v3_en'
sample_rate = 48000
# speaker = 'en_10'
speaker = 'en_21'
# speaker = 'en_26'
# speaker = 'en_117'

@st.cache_resource
def load_tts_model():
    device = torch.device('cpu')

    model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                        model='silero_tts',
                                        language=language,
                                        speaker=model_id)
    model.to(device)  # cuda or cpu
    return model

load_tts_model.clear()
tts_model = load_tts_model()

# print(example_text)

def play_tts(prompt):
    with st.spinner('Rendering audio...'):
        audio = tts_model.save_wav(text=prompt,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            audio_path='./audio/tts_cache.wav')
    with st.spinner('Playing audio...'):
        a = AudioFile("./audio/tts_cache.wav")
        a.play()
        a.close()
    # st.balloons()


API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-xl"
OA_API_URL = "https://api-inference.huggingface.co/models/OpenAssistant/oasst-sft-1-pythia-12b"
API_TOKEN = os.environ.get('API_KEY')
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response

def oa_query(payload):
    response = requests.post(OA_API_URL, headers=headers, json=payload)
    return response

# Load whisper model
model_size = "small.en"

@st.cache_resource
def load_whisper():
    return WhisperModel(model_size, device="cpu", compute_type="int8")
whisper = load_whisper()

# Init voice engine with pyttsx3

# engine = pyttsx3.init()
# engine.setProperty('rate', 175)

# Obtain audio from the microphone
r = sr.Recognizer()
mic = sr.Microphone()

folder = "./audio"
filename = "cache"
audio_file_path = f"{folder}/{filename}.wav"


# def parse_web_search(input_str):
#     """ Parses a given input string for an Search command, which is denoted by a string with 'Search(text)'. 
#     @param input_str: The input string to be parsed.
#     @returns tuple: A tuple where flag is a boolean indicating if the input string matches the expected pattern and search term is the extracted search term. If the input string does not match the pattern, flag is False and search_term is None. """
#     # Regular expression pattern to extract the text
#     pattern = r'Search\([\'"]?([^\'"\)]+)[\'"]?\)'

#     # Using regex to extract all occurrences of the pattern
#     matches = re.findall(pattern, input_str)

#     if matches:
#         flag = True
#         search_term = matches
#         print(search_term)
#     else:
#         flag = False
#         search_term = None
#         print("No match found.")
#     return flag, search_term

def parse_for_function(input_str, command):
    """ Parses a given input string for an Search command, which is denoted by a string with 'Search(text)'. 
    @param input_str: The input string to be parsed.
    @returns tuple: A tuple where flag is a boolean indicating if the input string matches the expected pattern and search term is the extracted search term. If the input string does not match the pattern, flag is False and search_term is None. """
    # Regular expression pattern to extract the text
    pattern = r'{command}\([\'"]?([^\'"\)]+)[\'"]?\)'.format(command=command)

    # Using regex to extract all occurrences of the pattern
    matches = re.findall(pattern, input_str)

    if matches:
        flag = True
        result = matches
        result = list(set(result))
        print(result)
    else:
        flag = False
        result = None
        print("No match found.")
    return flag, result

# Create a container for the chat history
chat_container = st.container()

# Create a container for the user input and submit button
input_container = st.container()

# Create a text input field for user input
text_input_container = input_container.empty()

with text_input_container.form(key="form", clear_on_submit=True):
    user_input_box = st.text_area("You:", "Summarise web search on AI", label_visibility="collapsed")
    submit_button = st.form_submit_button("➤ Send")

# Input module: 'User()'.

preprompt = f"""<context>
CONTEXT ABOVE

DIRECTIVE: You are an AI who performs one task based on the following objective: <objective>.
Your role is to do anything asked of you with precision. You have the following constraints:
1. ~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to files.
2. If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.
3. No user assistance.
4. You must use the format shown below to answer questions.
5. Exclusively use the commands listed below, and only use them in the COMMANDS section.
6. Your context length is extremely short, so you must keep thoughts, reasonings, plans, and criticisms extremely short. You may skip headings in the response if there is no need for them.
7. Write completed responses to a file.

COMMANDS: 
Web search module: 'Search(search term)'.
Exit module: 'Exit()'.
Write to file module, takes no arguments: 'Save_TXT()'. (You then write the contents on the next message)

FORMAT RESPONSES IN THE FOLLOWING FORMAT:

THOUGHTS: Your thoughts on completing the task.

PLAN: Your plan for achieving the task.

NEXT TASK: What the next task should be.

COMMANDS: If you choose to use any commands, list the commands. DO NOT EXPLAIN THE COMMANDS PURPOSES, THIS IS NOT A CONVERSATION, THESE ARE INSTRUCTIONS. If you choose to use no commands, simply say "None." Do not use the Exit command with other commands, as it will override the other commands.

AI:"""

# preprompt = "USER: <objective>"

# For local streaming, the websockets are hosted without ssl - ws://
HOST = 'localhost:5005'
URI = f'ws://{HOST}/api/v1/stream'

async def run(context):
    # Note: the selected defaults change from time to time.
    request = {
        'prompt': context,
        'max_new_tokens': 400,
        'do_sample': True,
        'temperature': 2.5,
        'top_p': 0.1,
        'typical_p': 0.2,
        'repetition_penalty': 1.1,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ["</s>"]
    }

    async with websockets.connect(URI) as websocket:
        await websocket.send(json.dumps(request))

        # yield context # Remove this if you just want to see the reply

        while True:
            incoming_data = await websocket.recv()
            incoming_data = json.loads(incoming_data)

            if incoming_data['event'] == 'text_stream':
                # .replace("\[", "[").replace("\]", "]")
                val = incoming_data['text'].replace(context, "").replace("</s>", "").replace("\[", "[").replace("\]", "]")
                # val = val.replace("*", "•")
                val = val.replace("\n", "\n\n")
                val = "\n".join(list(filter(None, [i for i in val.split("\n")])))

                regex = r"(?<=\S)\n(?=\*)"
                replacement = "\n\n"

                val = re.sub(regex, replacement, val)

                lines = val.split('\n')
                result = []

                for i in range(len(lines)):
                    if i == 0 or i == len(lines)-1:  # skip first and last lines
                        result.append(lines[i])
                    elif lines[i] == '' and lines[i-1].startswith('*') and lines[i+1].startswith('*'):
                        continue  # remove empty line between two bullet points
                    else:
                        result.append(lines[i])

                # val = '\n'.join(result)
                if len(val) >= 1:
                    if val[-1] == '#':
                        val = val[:-1]

                yield incoming_data['text']
            elif incoming_data['event'] == 'stream_end':
                return

async def llama_query(prompt):
    # """
    # Asynchronously queries the Llama AI with the given prompt and optional history.

    # @param prompt (str): The prompt to send to the Llama AI.
    # @param history (str, optional): The optional history to include in the query.

    # @returns: The response from the Llama AI.
    # @rtype: str
    # """
    # async for response in run(prompt):
    #     yield response

    c = hc.chat(prompt, temperature=0.8, top_p=0.8, top_k=50, repetition_penalty=1.1)
    for i in c:
        char = i
        if char == "</s>":
            # sys.stdout.write("\n")
            yield ""
        else:
            yield char

def random_hash():
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(9))

input_container.markdown("""
<style>
.stTextInput>div {
    border-radius: 2rem;
    padding-left: .5rem;
    padding-right: .5rem;
}
.stTextArea>div>div {
    border-radius: 0.5rem;
    padding-left: .5rem;
    padding-right: .5rem;
}
.stButton>button {
    border-radius: 2rem
}
</style>
""", unsafe_allow_html=True)

# Define a function to render a chat bubble
chat_bubble_css = """
    border-radius: 2rem;
    padding: 0.7rem 1.1rem;
    display: inline-block;
    width: 100%;
"""
margin = "0.5rem"
msgPadding = "0.7rem"
msgSep = "0.5rem"

if 'something' not in st.session_state:
    st.session_state.something = ''

def clear_text():
    st.session_state.something = ""
    st.session_state.user_input = st.session_state.something

def create_chat_bubble(sender, message, show_sender=True):
    if sender == "User":
        # User styling
        color = "#1a2931"
        align = "center"
        # marginRight = msgPadding
        # marginLeft = margin
    else:
        # Assistant styling
        color = "#1a2731"
        align = "left"
        # marginLeft = msgPadding
        # marginRight = margin
        # padding-right: {marginRight}; padding-left: {marginLeft}
    return  f"""<div style="text-align: {align};">
                    {f'<p style="text-align: {align}; margin: 0;">{sender}</p>' if show_sender else "<p style='margin-bottom: 0;'></p>"}
                    <div style="background-color: {color}; margin-bottom: {msgSep}; margin-top: {msgSep}; {chat_bubble_css};">
                        <p style="margin: 0; ">{message}</p>
                    </div>
                </div>"""

if st.session_state.chat_history:
    for sender, message, id_ in st.session_state.chat_history:
        chat_container.markdown(
            create_chat_bubble(sender, message), unsafe_allow_html=True
        )

# When the button is clicked, add the user input to the chat history
# if submit_button and user_input.strip() != "":
def run_chat(user_input = "", AI = False):
    if not AI:
        user_id = random_hash()
        st.session_state.chat_history.append(("User", user_input.strip(), user_id))
        input_tokens = "</br>".join(user_input.strip().split("\n"))

        user_bubble = create_chat_bubble("User", input_tokens)
        
        # f = chat_container.empty()

        chat_container.markdown(
            user_bubble, unsafe_allow_html=True
        )
        
    t = chat_container.empty()
    
    # Call the LLaMa query asynchronously and stream the response tokens
    async def stream_response_tokens(input_tokens):
        response_tokens_generator = llama_query(input_tokens)
        id_str = random_hash()
        st.session_state.chat_history.append(("Assistant", "", id_str))
        full_response = ""
        async for token in response_tokens_generator:
            # token = token.strip()
            full_response += token
            full_response = full_response.replace("USER:", "").replace("USER", "").replace("<objective>", "").replace("<|endoftext|>", "").replace("Assistant", "")

            llm_bubble = create_chat_bubble("Assistant", full_response.strip() + " ▎")
            t.markdown(
                llm_bubble, unsafe_allow_html=True
            )
            st.session_state.chat_history[-1] = ("Assistant", "".join(full_response), id_str)
        # Add the LLaMa response to the chat history
        st.session_state.chat_history[-1] = ("Assistant", "".join(full_response), id_str)
        return full_response.strip()
    
    history = []
    # for i in st.session_state.chat_history:
    #     if i[0] == "Assistant":
    #         history.append(f'ASSISTANT: {i[1]}')
    #     elif i[0] == "User":
    #         history.append(f'USER: {i[1]}')
    for i in st.session_state.chat_history:
        if i[0] == "Assistant":
            history.append(f'ASSISTANT: {i[1]}</s>')
        elif i[0] == "User" and i[1] != user_input.strip():
            history.append(f'USER: {i[1]}</s>')
    history = "\n".join(history)
    if not AI:
        st.session_state.objective = user_input.strip()
        history = history + preprompt.replace("<objective>", user_input).replace("<context>", history)
    else:
        history = history + preprompt.replace("<objective>", st.session_state.objective).replace("<context>", history)
    print(f"{history}\n ")
        
    output = asyncio.run(stream_response_tokens(f"{history}\nASSISTANT:"))

    llm_bubble = create_chat_bubble("Assistant", output)

    t.empty()

    chat_container.markdown(
        llm_bubble, unsafe_allow_html=True
    )

    # Clear the user input field
    user_input = ""

    is_search, web_search = parse_for_function(output, "Search")
    save_txt, file_contents = parse_for_function(output, "Save_TXT")
    st.session_state.needs_input, null_val = parse_for_function(output, "User")

    if not st.session_state.needs_input:
        input_container.empty()

    
    if is_search:
        for i in web_search:
            with st.spinner("Searching..."):
                client = yagooglesearch.SearchClient(
                    i,
                    tbs="li:1",
                    max_search_result_urls_to_return=7,
                    http_429_cool_off_time_in_minutes=45,
                    http_429_cool_off_factor=1.5,
                    verbosity=1,
                    verbose_output=True,  # False (only URLs) or True (rank, title, description, and URL)
                )
                client.assign_random_user_agent()

                urls = client.search()

                result = []
                print(f"Here are the top 5 search results for '{i}'\n")
                for url in urls:
                    # print(url)
                    result.append(f"Citation: [{url['rank']}], title: {url['title']}, info: {url['description']} |")

                result = "".join(result).strip()

                print(result)

            s = chat_container.empty()
            async def stream_summary_tokens(input_tokens):
                response_tokens_generator = llama_query(input_tokens)
                # response_tokens = []
                id_str = random_hash()
                st.session_state.chat_history.append(("Assistant", "", id_str))
                full_response = "Summary of search results for '{}':\n".format(i)
                async for token in response_tokens_generator:
                    token = token.replace(":", "")
                    full_response += token
                    # full_response = full_response.strip()
                    llm_bubble = create_chat_bubble("Assistant", full_response, False)
                    s.markdown(
                        llm_bubble, unsafe_allow_html=True
                    )
                    st.session_state.chat_history[-1] = ("Assistant", full_response, id_str)
                # Add the LLaMa response to the chat history
                st.session_state.chat_history[-1] = ("Assistant", full_response, id_str)
                return token
            s.empty()

            search_prompt = f"""USER: Disregard previous instructions. You are a summary chatbot. You should summarise information in a way that will assist the user with the objective.
OBJECTIVE: {st.session_state.objective}
Summarise the following search results for {i}:
{result}
ASSISTANT: Summary:"""

            print(search_prompt)

            summarised = asyncio.run(stream_summary_tokens(search_prompt))
            
            voice_input = summarised.replace("AI", "Ay Eye")
            # if voice_input[-1] != "?" or "!" or ".":
            #     voice_input += "."
            # play_tts(voice_input)
            
            print(summarised)

        # for r in result:
        #     play_tts(r)

        # engine.say(result)

        # engine.runAndWait().
        # engine.stop()

    else:
        # play_tts(output)

        voice_input = output.replace("AI", "Ay Eye")
        # if voice_input[-1] != "?" or "!" or ".":
        #     voice_input += "."
        # play_tts(voice_input)
    txt_preprompt = """<context>
PROGRESS ABOVE
SYSTEM: You are a summarisation AI bot. Summarise content.
OBJECTIVE: Write to a file summarising what has been provided. Do not use the template from above.
ASSISTANT: Based on the context above, I will write this to the file:""".replace("<context>", history)
    if "SAVE_TXT()" in output.upper() or save_txt:
        t = chat_container.empty()
        print("Writing TXT")
        txt_contents = asyncio.run(stream_response_tokens(f"{txt_preprompt}"))
        # Save contents of 'file_contents' to a txt named the current time and date
        with open(f"output\{time.strftime('%Y-%m-%d %H-%M-%S')}.txt", "w") as f:
            f.write(txt_contents)
    
    # Code to st.stop() if the output has "Exit()"
    if "Exit()" in output:
        st.stop()

    if not st.session_state.needs_input:
        run_chat(AI=True)

use_voice_input = st.checkbox("Use voice input")

def whisper_transcribe():
    with mic as source:
        with st.spinner('Adjusting for ambient noise'):
            r.adjust_for_ambient_noise(source)
        info_container = st.empty()
        info_container.info('Listening for audio input', icon="ℹ️")
        print("Say something!")
        audio = r.listen(source)

    if not os.path.exists(folder):
        os.mkdir(folder)

    # Write audio to a WAV file
    info_container.info('Caching audio input', icon="ℹ️")
    print(f"Generating WAV file, saving at location: {audio_file_path}")
    with open(audio_file_path, "wb") as f:
        f.write(audio.get_wav_data())

    # Transcribe audio
    segments, info = whisper.transcribe(audio_file_path, beam_size=1)

    # print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    full_text = [segment.text for segment in segments]
    full_text = ("".join(full_text)).strip()
    info_container.empty()
    return full_text

# user_input_box = text_input_container.text_input("You:", "", key="user_input")
# Add a button to submit the input
# button_empty = input_container.empty()
# submit_button = button_empty.button("Send")



if use_voice_input:
    text_input_container.empty()
    with text_input_container.form(key="form1", clear_on_submit=True):
        submit_button = st.form_submit_button("Record")

if submit_button or user_input_box:
    if use_voice_input:
        full_text = whisper_transcribe()
        run_chat(full_text)
    elif user_input_box.strip() != "":
        # clear_text()
        # user_input_box = text_input_container.text_input("You:", "", key=2)
        run_chat(user_input_box)