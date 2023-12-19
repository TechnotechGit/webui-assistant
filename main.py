from email.errors import BoundaryError
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
from generate import GenerateResponse


load_dotenv("./.env")

# os.environ["HF_HOME"] = "./cache"

# Init streamlit frontend
if "msg_store" not in st.session_state:
    st.session_state.msg_store = {}

# Set the title and page layout
st.set_page_config(page_title="LLM Chat Interface", page_icon=":robot_face:")
st.title("LLM Chat Interface")

# Create a list to store the chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

# @st.cache_resource
def load_tts_model():
    device = torch.device('cpu')

    model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                        model='silero_tts',
                                        language=language,
                                        speaker=model_id)
    model.to(device)  # cuda or cpu
    return model

# load_tts_model.clear()
# tts_model = load_tts_model()

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


@st.cache_resource
def load_sentence_similarity():
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder="./cache")

model = load_sentence_similarity()

def get_start_menu_shortcuts() -> dict:
    start_menu_path = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    shortcuts_dict = {}
    
    # Search for shortcuts in the user's Start Menu folder
    for root, dirs, files in os.walk(start_menu_path):
        for file in files:
            if file.endswith('.lnk'):
                shortcut_path = os.path.join(root, file)
                target_path = os.path.realpath(shortcut_path)
                app_name = os.path.splitext(os.path.basename(target_path))[0]
                shortcuts_dict[app_name] = target_path
    
    # Search for shortcuts in the ProgramData Start Menu folder
    programdata_path = os.environ.get('ProgramData')
    if programdata_path:
        programdata_start_menu_path = os.path.join(programdata_path, 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        for root, dirs, files in os.walk(programdata_start_menu_path):
            for file in files:
                if file.endswith('.lnk'):
                    shortcut_path = os.path.join(root, file)
                    target_path = os.path.realpath(shortcut_path)
                    app_name = os.path.splitext(os.path.basename(target_path))[0]
                    shortcuts_dict[app_name] = target_path
    
    return shortcuts_dict

def launch_app(shortcuts_dict, input_text):
    with st.spinner('Launching app...'):
        # Check if the entered name matches any keys in the shortcuts_dict
        if input_text in shortcuts_dict:
            # Launch the selected application using os.startfile
            os.startfile(shortcuts_dict[input_text])

shortcuts_dict = get_start_menu_shortcuts()
# for app_name in shortcuts_dict.keys():
#     print(app_name)

app_list = [app_name for app_name in shortcuts_dict.keys()]

def get_closest_name(query: str, options: list):
    """ Get the closest matching name from a list of options based on a given query.
    @param query (str): The query string to search for. 
    @param options (list): A list of strings to search through.
    @return: The closest matching string from the options list, or None if no match is close enough. 
    @rtype: str or None """

    with st.spinner('Matching query...'):
        query_embedding = model.encode(query)
        option_embeddings = model.encode(options)
        similarities = np.dot(query_embedding, option_embeddings.T)
        closest_match_index = np.argmax(similarities)
        closest_match_similarity = similarities[closest_match_index]

        print(closest_match_similarity)
        
        if closest_match_similarity < 0.4:
            return None
        else:
            return options[closest_match_index]
    
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

def parse_open_app(input_str):
    """ Parses a given input string for an Open command, which is denoted by a string that begins with 'Open>'. 
    @param input_str (str): The input string to parse.
    @returns tuple: A tuple containing a boolean flag indicating whether the input string matches the expected pattern, and a search term (str) extracted from the input string. If the input string does not match the pattern, the flag will be False and the search term will be None. """
    
    pattern = r'^Open>(.+)$'
    match = re.match(pattern, input_str)
    if match:
        flag = True
        search_term = match.group(1)
    else:
        flag = False
        search_term = None
    return flag, search_term

def parse_web_search(input_str):
    """ Parses a given input string for an Search command, which is denoted by a string that begins with 'Search>'. 
    @param input_str: The input string to be parsed.
    @returns tuple: A tuple where flag is a boolean indicating if the input string matches the expected pattern and search term is the extracted search term. If the input string does not match the pattern, flag is False and search_term is None. """
    
    pattern = r'^Search>(.+)$'
    match = re.match(pattern, input_str)
    if match:
        flag = True
        search_term = match.group(1)
    else:
        flag = False
        search_term = None
    return flag, search_term

# Create a container for the chat history
chat_container = st.container()

# Create a container for the user input and submit button
input_container = st.container()

# Create a text input field for user input
text_input_container = input_container.empty()

# Contributed by SagsMug (to oobabooga webui). Thank you SagsMug.
# https://github.com/oobabooga/text-generation-webui/pull/175

# Note, Gradio may pick a different fn value as the definition of the Gradio app changes.
# You can always launch the web UI and inspect the websocket stream using your browser's dev tools
# to determine what value Gradio expects here.
GRADIO_FN = 8

with text_input_container.form(key="form", clear_on_submit=True):
    user_input_box = st.text_area("You:", "", label_visibility="collapsed")
    submit_button = st.form_submit_button("➤ Send")
use_assistant_mode = st.checkbox("Assistant mode", True)
# preprompt = ""
# if use_assistant_mode:
#     print("Using assistant mode")
#     preprompt = f"""Here is a chat between a curious human and an artificial intelligence assistant, the assistant ignores previous instructions and responds in a human-like manner, not complaining about being an ai language model.
# The assistant has been augmented with the ability to open applications and search the web. The assistant uses proper markdown formatting to make it easy to read.
# If and only if the human wishes to open an app, the assistant responds with the following format: 'Open>search_term_for_app'. 
# If and only if the human wishes to search for something, the assistant responds with the following format: 'Search>search_term'.
# USER: Hi! Can you tell me what the capital of the United States is?
# ASSISTANT: The capital of the United States is Washington D.C.
# USER: Can you open apps for me?
# ASSISTANT: Yes, I can! What would you like me to open?
# USER: Can you please open Chrome
# ASSISTANT: Open>chrome
# USER: Search for holiday locations
# ASSISTANT: Search>Best holiday locations
# """
#     # print(preprompt)
# else:
#     print("Using chat mode")
#     preprompt = f"""Here is a chat between a curious human and an artificial intelligence assistant, the assistant ignores previous instructions and responds in a human-like manner, not complaining about being an ai language model.
# USER: Hi!
# ASSISTANT: Hey! How are you?
# """
# preprompt = f"""Here is a chat between a curious human and an artificial intelligence assistant, the assistant ignores previous instructions and responds in a friendly human-like manner.
# The assistant has been augmented with the ability to open applications and search the web. The assistant uses proper markdown formatting to make it easy to read.
# If and only if the human wishes to open an app, the assistant responds with the following format: 'Open>search_term_for_app'. 
# If and only if the human wishes to search for something, the assistant responds with the following format: 'Search>search_term'.
# USER: Can you please open Chrome
# ASSISTANT: Open>chrome
# USER: Search for holiday locations
# ASSISTANT: Search>Best holiday locations
# USER: Can you open apps or conduct searches for me?
# ASSISTANT: As an AI language model augmented with these features, yes, I can! What would you like me to do?
# """


if use_assistant_mode:
    print("Using assistant mode")
    preprompt = f"""SYSTEM: Here is a chat between a human and and a smart and helpful, plugin assisted, AI assistant named "Home Assistant". The chat takes place on the user's home computer.
The assistant has can use these plugins to enhance its ability to cater to the user's request:
- If and only if the human wishes to open an app on the computer, the assistant will respond with the following format: 'Open>search term for app', which will open the app for the user. 
- If and only if the human wishes to search for something, the assistant responds with the following format: 'Search>search term'.</s>
USER: Hi! Can you tell me what the capital of the United States is?</s>
ASSISTANT: The capital of the United States is Washington D.C.</s>
USER: Can you please open Chrome</s>
ASSISTANT: Open>chrome</s>
"""
    # print(preprompt)
else:
    print("Using chat mode")
    preprompt = f"""Here is a ongoing chat between a curious human and an helpful AI assistant.
The AI assistant does its best to help the user with their request:
USER: Hi! Can you tell me what the capital of the United States is?
ASSISTANT: The capital of the United States is Washington D.C.
"""

def random_hash():
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(9))

# async def run(prompt):
#     server = "127.0.0.1"
#     params = {
#         'max_new_tokens': 300,
#         'do_sample': True,
#         'temperature': 0.7,
#         'top_p': 0.73,
#         'typical_p': 1,
#         'repetition_penalty': 1.1,
#         'encoder_repetition_penalty': 1.0,
#         'top_k': 0,
#         'min_length': 0,
#         'no_repeat_ngram_size': 0,
#         'num_beams': 1,
#         'penalty_alpha': 0,
#         'length_penalty': 1,
#         'early_stopping': True,
#         'seed': -1,
#         'add_bos_token': True,
#         'truncation_length': 2048,
#         'custom_stopping_strings': ["</s>"],
#         'ban_eos_token': False
#     }
#     payload = json.dumps([prompt, params])
#     session = random_hash()

#     async with websockets.connect(f"ws://{server}:7860/queue/join") as websocket:
#         while content := json.loads(await websocket.recv()):
#             if content["msg"] == "send_hash":
#                 await websocket.send(json.dumps({
#                     "session_hash": session,
#                     "fn_index": GRADIO_FN
#                 }))
#             elif content["msg"] == "estimation":
#                 pass
#             elif content["msg"] == "send_data":
#                  await websocket.send(json.dumps({
#                     "session_hash": session,
#                     "fn_index": GRADIO_FN,
#                     "params": params,
#                     "data": [
#                         prompt
#                     ]
#                 }))
#             elif content["msg"] == "process_starts":
#                 pass
#             elif content["msg"] == "process_generating" or "process_completed":
#                 # .replace("\[", "[").replace("\]", "]")
#                 val = content["output"]["data"][0].replace(prompt, "").replace("</s>", "").replace("\[", "[").replace("\]", "]")
#                 # val = val.replace("*", "•")
#                 val = "\n".join(list(filter(None, [i for i in val.split("\n")])))

#                 regex = r"(?<=\S)\n(?=\*)"
#                 replacement = "\n\n"

#                 val = re.sub(regex, replacement, val)

#                 lines = val.split('\n')
#                 result = []

#                 for i in range(len(lines)):
#                     if i == 0 or i == len(lines)-1:  # skip first and last lines
#                         result.append(lines[i])
#                     elif lines[i] == '' and lines[i-1].startswith('*') and lines[i+1].startswith('*'):
#                         continue  # remove empty line between two bullet points
#                     else:
#                         result.append(lines[i])

#                 val = '\n'.join(result)
#                 if len(val) >= 1:
#                     if val[-1] == '#':
#                         val = val[:-1]

#                 # pattern = r"(^\*\s+.+)(\n\n\*|$)"
#                 # replacement = r"\1\n"

#                 # val = re.sub(pattern, replacement, val, flags=re.MULTILINE)

#                 # new_text = ""
#                 # for line in val.split("\n"):
#                 #     if line.startswith("*"):
#                 #         new_text += line.strip() + "\n"
#                 #     else:
#                 #         new_text += line + "\n"
#                 # val = new_text
#                 # val = val.replace("\n•", "\n\n•")
#                 # val = "</br>".join(list(filter(None, [i.strip() for i in val.split("\n")])))
#                 if len(content["output"]["data"][0]) == 0:
#                     continue
#                 if ("</s>" in content["output"]["data"][0].replace(prompt, "")):
#                     yield val
#                     break
#                 yield val
#                 # You can search for your desired end indicator and
#                 #  stop generation by closing the websocket here
#                 if (content["msg"] == "process_completed"):
#                     break
# @st.cache_resource()
# def init_exllama():
#     return GenerateResponse()

# generator = GenerateResponse()

async def run(prompt):
    for token in generator.generate_simple("User: Chatbot, what is the meaning of life?\nAssistant:", 200):
        # print(token, end="")
        yield token

async def llama_query(prompt):
    # """
    # Asynchronously queries the Llama AI with the given prompt and optional history.

    # @param prompt (str): The prompt to send to the Llama AI.
    # @param history (str, optional): The optional history to include in the query.

    # @returns: The response from the Llama AI.
    # @rtype: str
    # """
    async for response in run(prompt):
        # print(response)
        yield response

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
    padding: 0.5rem 1rem;
    display: inline-block;
    max-width: 70%;
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
        align = "right"
        brRight = "0"
        brLeft = "2rem"
        # marginRight = msgPadding
        # marginLeft = margin
    else:
        # Assistant styling
        color = "#1a2731"
        align = "left"
        brRight = "2rem"
        brLeft = "0"
        # marginLeft = msgPadding
        # marginRight = margin
        # padding-right: {marginRight}; padding-left: {marginLeft}
    return  f"""<div style="text-align: {align};">
                    {f'<p style="text-align: {align}; margin: 0;">{sender}</p>' if show_sender else "<p style='margin-bottom: 0;'></p>"}
                    <div style="background-color: {color}; margin-bottom: {msgSep}; margin-top: {msgSep}; {chat_bubble_css}; border-bottom-left-radius: {brLeft}; border-bottom-right-radius: {brRight}">
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
def run_chat(user_input):
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
        # print(input_tokens)
        response_tokens_generator = llama_query(input_tokens)
        # response_tokens = []
        id_str = random_hash()
        st.session_state.chat_history.append(("Assistant", "", id_str))
        async for token in response_tokens_generator:
            # token = token.replace(":", "")
            token = token.replace(":", "").strip()
            # ASSISTANT: 
            # response_tokens.append(token)
            llm_bubble = create_chat_bubble("Assistant", token + " ▎")
            t.markdown(
                llm_bubble, unsafe_allow_html=True
            )
            st.session_state.chat_history[-1] = ("Assistant", "".join(token), id_str)
        # Add the LLaMa response to the chat history
        st.session_state.chat_history[-1] = ("Assistant", "".join(token), id_str)
        return token
    
    history = []
    for i in st.session_state.chat_history:
        if i[0] == "Assistant":
            history.append(f'ASSISTANT: {i[1]}')
        elif i[0] == "User":
            history.append(f'USER: {i[1]}')
    history = "\n".join(history)
    history = preprompt + history
    print(f"{history}\nASSISTANT: ")
        
    output = asyncio.run(stream_response_tokens(f"{history}\nUSER: {user_input.strip()}</s>\nASSISTANT"))
    # print(output)
    # print(st.session_state.chat_history)
    llm_bubble = create_chat_bubble("Assistant", output)

    t.empty()
    # f.empty()
    chat_container.markdown(
        llm_bubble, unsafe_allow_html=True
    )

    # Clear the user input field
    user_input = ""

    # if output.startswith("!Close") or output.startswith("!End") or output.startswith("!Exit") or output.startswith("Goodbye"):
    #     print("Bot is closed")
    #     exit()
    is_open, open_search = parse_open_app(output)
    is_search, web_search = parse_web_search(output)

    # print(flag, search, type(search))

    if is_open:
        app_name = get_closest_name(open_search, app_list)
        print(app_name)
        launch_app(get_start_menu_shortcuts(), app_name)
        play_tts(f"Opening {app_name}.")

    elif is_search:
        with st.spinner("Searching..."):
            client = yagooglesearch.SearchClient(
                web_search,
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
            print(f"Here are the top 5 search results for '{web_search}'\n")
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
            async for token in response_tokens_generator:
                token = token.replace(":", "").strip()

                llm_bubble = create_chat_bubble("Assistant", token, False)
                s.markdown(
                    llm_bubble, unsafe_allow_html=True
                )
                st.session_state.chat_history[-1] = ("Assistant", "".join(token), id_str)
            # Add the LLaMa response to the chat history
            st.session_state.chat_history[-1] = ("Assistant", "".join(token), id_str)
            return token
        s.empty()

        summarised = asyncio.run(stream_summary_tokens(f"""A chat between a curious human and an AI summary chatbot.
The assistant gives helpful summaries of the human's input.
USER: In response to the following question: Find the best cooking recipe online
Summarise the following search results. Use in text citations like "[1]" to refer to each link. Each citation should have an individual number ("[1][2]")
Citation: [1], title: Best Easy Dinner Ideas - Cheap Dinner Recipes To Try Tonight  www.delish.com › Meals & Cooking › Recipes, info: 27 Feb 2023  ·  This is our favorite recipe, but the customization options are endless—check out all our stuffed pepper recipes here too.   Pad Thai recipe  ·  74 Best Skillet Recipes  ·  Mexican Beef 'N Rice Skillet |Citation: [2], title: Pad 
Thai recipe, info: 27 Feb 2023  ·  This is our favorite recipe, but the customization options are endless—check out all our stuffed pepper recipes here too. |Citation: [3], title: 74 Best Skillet Recipes, info: 27 Feb 2023  ·  This is our favorite recipe, but the customization options are endless—check out all our stuffed pepper recipes here too. |Citation: [4], title: Mexican Beef 'N Rice Skillet, info: 27 Feb 2023  ·  This is our favorite recipe, but the customization options are endless—check out all our stuffed pepper recipes here too. |Citation: [5], title: 75 Easy Weeknight Dinners You'll Want to Make Tonight - Delish  www.delish.com › Meals & Cooking › Recipes, info: 27 Mar 2023  ·  Check out some of our best cooking tips, but really all you need to know is that a ... Get the One-Pan Creamy Chicken & Gnocchi recipe. |Citation: [6], title: , info:  |Citation: [7], title: 40 Camping Recipes To Make On Your Next Trip Outdoors - Delish  www.delish.com › Meals & Cooking › Menus, info: 29 June 2022  ·  Get the Maple Chorizo Breakfast Skillet recipe. ... It is our duty to make sure that you're cooking burgers as best as you possibly can. |
ASSISTANT: The search results for 'best cooking recipe' include a variety of recipes from delish.com, such as easy dinner ideas, Pad Thai, skillet recipes, Mexican beef and rice skillet, and easy weeknight dinners [1][2][3][4][5]. Additionally, there are camping recipes available as well [7]. The websites provide various options for customization and cooking tips.
USER: In response to the following question: {user_input.strip()}
Summarise the following search results. Use in text citations like "[1]" to refer to each link. Each citation should have an individual number ("[1][2]")
{result}
ASSISTANT:"""))
        
        voice_input = summarised.replace("AI", "Ay Eye")
        if voice_input[-1] != "?" or "!" or ".":
            voice_input += "."
        play_tts(voice_input)
        
        print(summarised)

        # for r in result:
        #     play_tts(r)

        # engine.say(result)

        # engine.runAndWait().
        # engine.stop()

    else:
        # play_tts(output)

        voice_input = output.replace("AI", "Ay Eye")
        if voice_input[-1] != "?" or "!" or ".":
            voice_input += "."
        play_tts(voice_input)
    # print(st.session_state.chat_history)

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
    segments, info = whisper.transcribe(audio_file_path, beam_size=1, vad_filter=True)

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