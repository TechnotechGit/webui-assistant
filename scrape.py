import time
from transformers import PegasusTokenizer
import ctranslate2

import requests
from bs4 import BeautifulSoup
import random
import string
import json
import websockets
import re
import asyncio

# url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
url = "https://github.com/kuleshov/minillm"

response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

title = soup.title.string

# remove the "hatnote" section
hatnote_sections = soup.find_all('div', class_=lambda value: value and 'hatnote' in value.split())
for section in hatnote_sections:
    section.extract()

nav_sections = soup.find_all('div', class_=lambda value: value and 'nav' in value.split())
for section in nav_sections:
    section.extract()

menu_sections = soup.find_all('div', class_=lambda value: value and 'menu' in value.split())
for section in menu_sections:
    section.extract()

# remove the "catlinks" section
catlinks_section = soup.find('div', class_='catlinks')
if catlinks_section:
    catlinks_section.extract()

# remove unwanted elements by class name
for element in soup.find_all(class_=lambda value: value and 'references' in value.lower()):
    element.extract()

# remove other unwanted elements
for script in soup(["script", "style", "button", "nav", "footer", "select"]):
    script.extract()

# Find all headers using the 'find_all' method and loop through them
for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
    # Prepend the new header text to the existing header text
    header.string = f"Header: {header.string}"

# extract text and remove everything after "See also"
text = soup.get_text()
text = text.split('See also', 1)[0]

text = "".join([s for s in text.splitlines(True) if s.strip("\r\n")])

# print(text)
# exit()

# print(text[:512])

# checkpoint = "google/pegasus-cnn_dailymail"
# tokenizer = PegasusTokenizer.from_pretrained(checkpoint, cache_dir="./cache")
# translator = ctranslate2.Translator("pegasus-cnn-ct", compute_type="int8")
# batch = tokenizer.convert_ids_to_tokens(tokenizer.encode(text, truncation=True))
# # batch = tokenizer([input_text], truncation=True, padding='longest').input_ids

# start = time.time()

# results = translator.translate_batch([batch], min_decoding_length=64, max_decoding_length=128, use_vmap=True)
# target = results[0].hypotheses[0]
# print(tokenizer.decode(tokenizer.convert_tokens_to_ids(target), skip_special_tokens=True).replace("<n>", "\n"))
# end = time.time()
# print(end - start)

# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# # from optimum.bettertransformer import BetterTransformer

# # checkpoint = "pszemraj/long-t5-tglobal-base-16384-book-summary"
# # checkpoint = "mrm8488/t5-base-finetuned-summarize-news"
# # checkpoint = "philschmid/flan-t5-base-samsum"
# # checkpoint = "domenicrosati/led-base-8192-biolaysum-elife"
# # checkpoint = "sshleifer/distilbart-cnn-6-6"
# # checkpoint = "ccdv/lsg-bart-base-16384-mediasum"
# # checkpoint = "ccdv/lsg-bart-base-16384-arxiv"
# checkpoint = "ccdv/lsg-bart-base-16384-pubmed"
# # checkpoint = "tuner007/pegasus_paraphrase"
# # checkpoint = "google/pegasus-cnn_dailymail"

# tokenizer = AutoTokenizer.from_pretrained(checkpoint, use_fast=True, cache_dir="./cache", trust_remote_code=True)

# model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, cache_dir="./cache", trust_remote_code=True)

# # model_bt = BetterTransformer.transform(model, keep_original_model=True)

# # n = 512
# start = time.time()
# input_ids = tokenizer(text, return_tensors="pt").input_ids
# # # streamer = TextStreamer(input_ids)streamer=streamer
# outputs = model.generate(input_ids, min_length=96, max_new_tokens=200, do_sample=True)
# result = tokenizer.decode(outputs[0]).replace("<pad>", "")
# result = result.replace("</s>", "").replace(text, "").strip()
# print(result)
# end = time.time()
# print(end - start)

# Contributed by SagsMug (to oobabooga webui). Thank you SagsMug.
# https://github.com/oobabooga/text-generation-webui/pull/175

# Note, Gradio may pick a different fn value as the definition of the Gradio app changes.
# You can always launch the web UI and inspect the websocket stream using your browser's dev tools
# to determine what value Gradio expects here.
GRADIO_FN = 8

def random_hash():
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(9))

async def run(prompt):
    server = "127.0.0.1"
    params = {
        'max_new_tokens': 300,
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.73,
        'typical_p': 1,
        'repetition_penalty': 1.1,
        'encoder_repetition_penalty': 1.0,
        'top_k': 0,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': True,
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'custom_stopping_strings': ["</s>"],
        'ban_eos_token': False
    }
    payload = json.dumps([prompt, params])
    session = random_hash()

    async with websockets.connect(f"ws://{server}:7860/queue/join") as websocket:
        while content := json.loads(await websocket.recv()):
            if content["msg"] == "send_hash":
                await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": GRADIO_FN
                }))
            elif content["msg"] == "estimation":
                pass
            elif content["msg"] == "send_data":
                 await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": GRADIO_FN,
                    "params": params,
                    "data": [
                        prompt
                    ]
                }))
            elif content["msg"] == "process_starts":
                pass
            elif content["msg"] == "process_generating" or "process_completed":
                val = content["output"]["data"][0].replace(prompt, "").replace("</s>", "").replace("\[", "[").replace("\]", "]")
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

                val = '\n'.join(result)
                if len(val) >= 1:
                    if val[-1] == '#':
                        val = val[:-1]

                if len(content["output"]["data"][0]) == 0:
                    continue
                if ("</s>" in content["output"]["data"][0].replace(prompt, "")):
                    yield val
                    break
                yield val
                # You can search for your desired end indicator and
                #  stop generation by closing the websocket here
                if (content["msg"] == "process_completed"):
                    break

async def llama_query(prompt):
    # """
    # Asynchronously queries the Llama AI with the given prompt and optional history.

    # @param prompt (str): The prompt to send to the Llama AI.
    # @param history (str, optional): The optional history to include in the query.

    # @returns: The response from the Llama AI.
    # @rtype: str
    # """
    async for response in run(prompt):
        yield response


async def stream_response_tokens(input_tokens):
    response_tokens_generator = llama_query(input_tokens)
    id_str = random_hash()
    async for token in response_tokens_generator:
        token = token.replace(":", "").strip()
        print(token)
    # Add the LLaMa response to the chat history
    return token

print(title)

output = asyncio.run(stream_response_tokens(f"""You are an AI Summary Generator. You generate summaries of the human's input.
The human inputs unparsed content from websites. It is your job to parse and summarise it.
USER: Title: {title}
Website content: {text}
ASSISTANT: Here is a summary of the website you provided:\n"""))
print(output)