import time
from unittest import result
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
    stream_with_context,
)
from httpx import head
from requests import get, post

# from generate import GenerateResponse
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
import asyncio
import json
import sys
import os
import re
from oobaAPI import OobaModel
from exllamaAPI import ExLlamaModel
import yagooglesearch
import numpy as np
import string
import random
import chromadb
from chromadb.config import Settings
import websocket

# import env vars
from dotenv import load_dotenv

load_dotenv()

client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chromadb",  # Optional, defaults to .chromadb/ in the current directory
    )
)
chroma_collection = client.get_or_create_collection(name="history")


# user_token = "[INST]"
# assistant_token = "[/INST]"
user_token = "### Instruction: \n"
assistant_token = "### Response: \n"
separator_token = "\n"

modelAPI = 2

sentence_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2", cache_folder="./cache"
)


def get_start_menu_shortcuts() -> dict:
    start_menu_path = os.path.join(
        os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs"
    )
    shortcuts_dict = {}

    # Search for shortcuts in the user's Start Menu folder
    for root, dirs, files in os.walk(start_menu_path):
        for file in files:
            if file.endswith(".lnk"):
                shortcut_path = os.path.join(root, file)
                target_path = os.path.realpath(shortcut_path)
                app_name = os.path.splitext(os.path.basename(target_path))[0]
                shortcuts_dict[app_name] = target_path

    # Search for shortcuts in the ProgramData Start Menu folder
    programdata_path = os.environ.get("ProgramData")
    if programdata_path:
        programdata_start_menu_path = os.path.join(
            programdata_path, "Microsoft", "Windows", "Start Menu", "Programs"
        )
        for root, dirs, files in os.walk(programdata_start_menu_path):
            for file in files:
                if file.endswith(".lnk"):
                    shortcut_path = os.path.join(root, file)
                    target_path = os.path.realpath(shortcut_path)
                    app_name = os.path.splitext(os.path.basename(target_path))[0]
                    shortcuts_dict[app_name] = target_path

    return shortcuts_dict


def launch_app(shortcuts_dict, input_text):
    # Check if the entered name matches any keys in the shortcuts_dict
    if input_text in shortcuts_dict:
        # Launch the selected application using os.startfile
        os.startfile(shortcuts_dict[input_text])


shortcuts_dict = get_start_menu_shortcuts()
# for app_name in shortcuts_dict.keys():
#     print(app_name)

app_list = [app_name for app_name in shortcuts_dict.keys()]


def get_closest_name(query: str, options: list):
    """Get the closest matching name from a list of options based on a given query.
    @param query (str): The query string to search for.
    @param options (list): A list of strings to search through.
    @return: The closest matching string from the options list, or None if no match is close enough.
    @rtype: str or None"""

    query_embedding = sentence_model.encode(query)
    option_embeddings = sentence_model.encode(options)
    similarities = np.dot(query_embedding, option_embeddings.T)
    closest_match_index = np.argmax(similarities)
    closest_match_similarity = similarities[closest_match_index]

    print(closest_match_similarity)

    if closest_match_similarity < 0.4:
        return None
    else:
        return options[closest_match_index]


def parse_open_app(input_str):
    """Parses a given input string for an Open command, which is denoted by a string that begins with 'Open>'.
    @param input_str (str): The input string to parse.
    @returns tuple: A tuple containing a boolean flag indicating whether the input string matches the expected pattern, and a search term (str) extracted from the input string. If the input string does not match the pattern, the flag will be False and the search term will be None.
    """

    pattern = r"^Open>(.+)$"
    match = re.match(pattern, input_str)
    if match:
        flag = True
        search_term = match.group(1)
    else:
        flag = False
        search_term = None
    return flag, search_term


def parse_web_search(input_str):
    """Parses a given input string for an Search command, which is denoted by a string that begins with 'Search>'.
    @param input_str: The input string to be parsed.
    @returns tuple: A tuple where flag is a boolean indicating if the input string matches the expected pattern and search term is the extracted search term. If the input string does not match the pattern, flag is False and search_term is None.
    """

    # pattern = r'^Search>(.+)$'
    # match = re.match(pattern, input_str)
    # if match:
    #     flag = True
    #     search_term = match.group(1)
    # else:
    #     flag = False
    #     search_term = None
    regex = r"^Search>(.+)$"
    match = re.search(regex, input_str)
    if match:
        flag = True
        search_term = match.group(1)
    else:
        flag = False
        search_term = None
    return flag, search_term


def formatWebSearchPrompt(prompt, query):
    # Model expects
    # BEGININPUT
    # BEGINCONTEXT
    # url:
    # date:
    # ENDCONTEXT
    # ENDINPUT
    # BEGININSTRUCTION
    # instruction
    # ENDINSTRUCTION
    result = ""
    result += f"""{user_token}Respond to the question '{query}' by utilising the following web search results:"""
    for url in prompt:
         result += f"""---
url: {url['url']}
title: {url['title']}
info: {url['description']}
    """
    result += f"""---\n{assistant_token}"""
         
#     result += f"""USER: With the provided web search information, answer the following question:
# BEGININPUT\n"""
#     print(prompt)
#     for url in prompt:
#         result += f"""BEGINCONTEXT
# url: {url['url']}
# title: {url['title']}
# info: {url['description']}
# ENDCONTEXT\n"""
#     result += f"""ENDINPUT\n"""
#     result += f"""BEGININSTRUCTION
# Summarise the provided information.
# ENDINSTRUCTION
# {assistant_token}:"""
    return result


# def formatWebSearchPrompt(prompt):
#     result = ""
#     result += f"""SYSTEM: The following is a conversation between a user and a helpful summarisation assistant. The assistant summarises user provided information.
# USER: With the web search information below, summarise and respond to the following question: {prompt}\n"""
#     print(prompt)
#     for url in prompt:
#         result += f"""
# title: {url['title']}
# url: {url['url']}
# info: {url['description']}\n"""
#         # {user_token}: Summarise the provided information.
#     result += f"""{assistant_token}:"""
#     return result


def webSearch(prompt):
    client = yagooglesearch.SearchClient(
        prompt,
        tbs="li:1",
        max_search_result_urls_to_return=7,
        http_429_cool_off_time_in_minutes=45,
        http_429_cool_off_factor=1.5,
        verbosity=1,
        verbose_output=True,  # False (only URLs) or True (rank, title, description, and URL)
    )
    client.assign_random_user_agent()

    urls = client.search()

    # result = []
    # for url in urls:
    # print(url)
    # result.append(f"Citation: [{url['rank']}], title: {url['title']}, info: {url['description']} |")

    # result = "".join(result).strip()

    return urls

current_time = time.strftime("%I:%M %p")

def formatPrompt(prompt):
    """
    Formats a prompt for a conversation between a user and an AI assistant.

    Parameters:
        prompt (str): The user's prompt for the conversation.

    Returns:
        str: The formatted prompt for the conversation.
    """
    current_date = time.strftime("%Y-%m-%d")

#     preprompt = f"""### System: The following is a conversation between a user and an AI assistant. The assistant is helpful, creative, clever, and very friendly.
# CURRENT DATE: {current_date}.
# CURRENT TIME: {current_time}.
# - Assistant only responds in English.
# MODULES:
# The response must contain **only** the command (it **must not** include other text, such as 'Sure, I can do that'). **The user cannot use these commands**, so you should not tell the user to use them.
# `Search`
#     - Syntax: `Search>search term`
#     - Function: Searches Google. Use if the query is time based (news in 2023, for example), or you do not know the answer.
# `Open`: 
#     - Syntax: `Open>search term for app`
#     - Function: Opens an app for the user.
# {user_token}Search for latest news.{separator_token}{assistant_token}Search>latest news{separator_token}"""
    preprompt = f"""### System: The following is a conversation between a user and an AI assistant. The assistant is helpful, creative, clever, and very friendly.
"""
#     preprompt = f"""CURRENT DATE: {current_date}.
# BEGIN TIME: {current_time}.
# No emojis.
# """
    # Iterate through chat history and add each message to preprompt with prefix
    for message in chat_history:
        preprompt += f"{user_token}" + message["user"] + separator_token
        preprompt += f"{assistant_token}" + message["bot"] + separator_token
    preprompt += f"{user_token}" + prompt
    return preprompt


generator = ""

modelSettings = {
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9,
    "repetition_penalty": 1.15,
    "max_tokens": 1024,
    "min_p": 0.02,
}

current_model = None

def chooseModel(i):
    """
    Generates a response token based on the input text using different models depending on the value of `modelAPI`.

    Args:
        input_text (str): The input text to generate a response for.

    Returns:
        Generator[str, None, None]: A generator that yields response tokens.

    Raises:
        None
    """
    modelAPI = i

    def generate_response_tokens_default(input_text):
        # Default implementation
        pass

    if modelAPI == 0:
        generator = OobaModel(host="localhost:7860")

        def generate_response_tokens(input_text):
            tokens = generator.response_stream(input_text, [user_token])
            full_text = ""

            for token in tokens:
                token = token.replace(input_text, "")
                full_text += token
                yield token

    elif modelAPI == 1:
        generator = ""
        # tokens = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nibh nisl condimentum id venenatis a. Dui id ornare arcu odio ut sem nulla. Consequat id porta nibh venenatis. At quis risus sed vulputate odio ut enim blandit. Nisl condimentum id venenatis a condimentum vitae sapien pellentesque. Ut aliquam purus sit amet luctus venenatis lectus magna fringilla. Egestas tellus rutrum tellus pellentesque eu tincidunt tortor aliquam. Scelerisque varius morbi enim nunc faucibus a pellentesque sit amet. Dignissim cras tincidunt lobortis feugiat vivamus at.".split(" ")
        tokens = "Open>notepad".split(" ")

        def generate_response_tokens(input_text):
            full_text = ""
            for token in tokens:
                time.sleep(0.04)  # Simulating some processing time
                token += " "
                yield token

    elif modelAPI == 2:
        def generate_response_tokens(input_text):
            _python_server = False
            OPENAI_API_BASE_URL = "http://localhost:8080"

            if _python_server:
                stream_url = f"{OPENAI_API_BASE_URL}/v1/completions"
                data = {
                    "prompt": input_text,
                    "stop": [
                        "###",
                        "<s>",
                        "</s>"
                    ],
                    "min_p": float(modelSettings["min_p"]),
                    "n_predict": float(modelSettings["max_tokens"]),
                    "temperature": float(modelSettings["temperature"]),
                    "repeat_penalty": float(modelSettings["repetition_penalty"]),
                    "top_k": float(modelSettings["top_k"]),
                    "top_p": float(modelSettings["top_p"]),
                    "stream": "true"
                }
                headers = {
                    "Authorization": f"Bearer apikey",
                    "Content-Type": "application/json",
                }
            else:
                stream_url = f"{OPENAI_API_BASE_URL}/completion"
                data = {
                    "prompt": input_text,
                    "stop": [
                        user_token,
                        separator_token + user_token,
                        "###",
                        "<s>",
                        "</s>"
                    ],
                    # "min_p": 0.02,
                    # "n_predict": 500,
                    # "temperature": 1.1,
                    # "repeat_penalty": 1.0,
                    # "top_k": 32000,
                    "min_p": float(modelSettings["min_p"]),
                    "n_predict": float(modelSettings["max_tokens"]),
                    "temperature": float(modelSettings["temperature"]),
                    "repeat_penalty": float(modelSettings["repetition_penalty"]),
                    "top_k": float(modelSettings["top_k"]),
                    "top_p": float(modelSettings["top_p"]),
                    "cache_prompt": True,
                    "stream": True
                }
                headers = {
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'Authorization': f"Bearer {None}",
                }

            # Open a streaming connection to the server
            with post(stream_url, data=json.dumps(data), headers=headers, stream=True) as response:
                for line in response.iter_lines():
                    # if line:  # filter out keep-alive new lines
                    try:
                        # Decode the line of text
                        decoded_line = line.decode('utf-8')

                        # Process the event data here
                        if decoded_line.startswith("data:"):
                            # Load the data from the json
                            json_data = json.loads(decoded_line[len("data:"):])
                            print(json_data)
                            if _python_server:
                                data = json_data["choices"][0]["text"]
                            else:
                                if json_data["stop"]:
                                    global current_model
                                    current_model = json_data["model"] 
                                data = json_data["content"]
                            # print(data)
                            yield data
                    except Exception as e:
                        print(f"Exception while processing line: {e}")
                        continue
    elif modelAPI == 3:
        generator = ExLlamaModel(host="tough-times-beam.loca.lt:8000")

        def generate_response_tokens(input_text):
            tokens = generator.response_stream(input_text, [user_token])
            full_text = ""

            for token in tokens:
                token = token.replace(input_text, "")
                full_text += token
                print(token)
                yield " . "
    elif modelAPI == 4:
        # We are going to implement the hf api here
        # With streaming
        client = InferenceClient(token=os.getenv('API_KEY'))
        def generate_response_tokens(input_text):
            for token in client.text_generation(
                input_text, 
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                return_full_text=False,
                temperature=float(modelSettings["temperature"]),
                top_k=int(modelSettings["top_k"]),
                top_p=float(modelSettings["top_p"]),
                repetition_penalty=float(modelSettings["repetition_penalty"]),
                max_new_tokens=1024,
                stop_sequences=[
                    user_token,
                    separator_token + user_token,
                    # "###",
                    "</s>",
                ],
                stream=True):
                yield token

    # else:
    #     generator = GenerateResponse("airoboros-7B-gpt4-1.4-GPTQ")
    #     async def generate_response_tokens(input_text):
    #         full_text = ""
    #         tokens = generator.generate_simple(formatPrompt(input_text), 500)

    #         async for token in tokens:
    #             yield token

    # Change the function definition based on the modelAPI value
    chooseModel.generate_response_tokens = generate_response_tokens

    # Assign the default implementation as the fallback
    chooseModel.generate_response_tokens_default = generate_response_tokens_default

    # Return the chooseModel function
    return chooseModel


model_generator = chooseModel(modelAPI)  # Replace 0 with the desired modelAPI value


def random_hash():
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for i in range(9))


chat_history = []
app = Flask(__name__)



def non_streaming_response(prompt):
    res_str = ""
    for i in model_generator.generate_response_tokens(prompt):
        res_str += i
    return res_str


def chat_response_request(prompt):
    input_text = formatPrompt(prompt)
    # print(non_streaming_response(f"{user_token}: {formatPrompt(prompt)}\nWill this request need conversation history? Yes or no?\n{assistant_token}: The answer is:"))
    # print(chroma_collection.query(query_texts=[prompt], n_results=5))
    input_text = input_text + separator_token + f"{assistant_token}"
    print(input_text)
    res_str = ""
    for i in model_generator.generate_response_tokens(
        input_text
    ):
        res_str += i
        yield f"{i}"
    print(res_str)

    is_open, open_search = parse_open_app(res_str)
    if is_open:
        app_name = get_closest_name(open_search, app_list)
        print(app_name)
        launch_app(get_start_menu_shortcuts(), app_name)
        yield f'{{data: {{"info": "{app_name}", "task": "open", "success": true}}}}'
    is_search, web_search = parse_web_search(res_str)

    print(is_search, web_search)
    if is_search:
        search_results = webSearch(web_search)
        new_input = formatWebSearchPrompt(search_results, prompt)
        yield f'{{data: {{"info": "{web_search}", "task": "search", "success": true}}}}'
        print(f"Here are the top 5 search results for '{prompt}'\n{search_results}")
        sr = ""
        for i in model_generator.generate_response_tokens(new_input):
            sr += i
            yield f"{i}"
        res_str += "\n---\n" + sr

    chat_history.append({"user": prompt, "bot": res_str})
    get_date_time = time.strftime("%Y-%m-%d %I:%M %p")
    # chroma_collection.add(
    #     documents=[f"USER: {prompt}", f"ASSISTANT: {res_str}"],
    #     metadatas=[{"source": f"user-{get_date_time}"}, {"source": f"bot-{get_date_time}"}],
    #     ids=[random_hash(), random_hash()]
    # )
    return

def write_response_request(prompt):
    res_str = ""
    for i in model_generator.generate_response_tokens(
        prompt
    ):
        res_str += i
        yield f"{i}"
    return


@app.route("/")
def index():
    return render_template("index.html", chat_history=chat_history)


@app.route("/stream", methods=["POST"])
def stream():
    input_text = request.json["message"]
    # print(chroma_collection.peek()['documents'])
    return Response(
        stream_with_context(chat_response_request(input_text)), mimetype="text/event-stream"
    )

@app.route("/write-stream", methods=["POST"])
def writeStream():
    input_text = request.json["message"]
    return Response(
        stream_with_context(write_response_request(input_text)), mimetype="text/event-stream"
    )

@app.route('/edit_settings', methods=['POST'])
def receive_data():
    data = request.json
    global modelSettings
    modelSettings = {
        'temperature': data['temperature'],
        'top_k': data['top_k'],
        'top_p': data['top_p'],
        'repetition_penalty': data['repetition_penalty'],
        'max_tokens': data['max_tokens'],
        'min_p': data['min_p']
    }
    print(modelSettings)
    return jsonify({'status': 'success'}), 200

@app.route('/clear-history')
def clear_history():
    global chat_history
    chat_history = []
    return jsonify({'status': 'success'}), 200

@app.route('/get-model')
def get_data():
    data = {'model': current_model}  # Replace with your actual data
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
