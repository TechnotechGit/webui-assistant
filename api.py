'''

This is an example on how to use the API for oobabooga/text-generation-webui.

Make sure to start the web UI with the following flags:

python server.py --model MODEL --listen --no-stream

Optionally, you can also add the --share flag to generate a public gradio URL,
allowing you to use the API remotely.

'''
import json

import requests
from transformers import LlamaTokenizer

# Server address
server = "127.0.0.1"

tokeniser = LlamaTokenizer.from_pretrained("samwit/koala-7b", cache_dir="./cache")

eos_token = "</s>"
eos_token_id = tokeniser.encode(eos_token)

# Generation parameters
# Reference: https://huggingface.co/docs/transformers/main_classes/text_generation#transformers.GenerationConfig
params = {
    'max_new_tokens': 100,
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
    'custom_stopping_strings': ["</s>"],
    # 'eos_token_id': eos_token_id,
    'truncation_length': 2048,
    # 'ban_eos_token': False,
}

# Input prompt
prompt = """Here is a chat between a curious human and an artificial intelligence assistant, who now has the ability to open applications and search the web. 
If and only if the human wishes to open an app, the assistant returns the following format: 'Open>search_term_for_app'. 
If asked to search by the human, the assistant returns the following format: 'Search>search_term'.
If and only if the human wishes to end the conversation or says goodbye, the assistant returns '!Close'.
The assistant ends generation when the message is done.
USER: Hi! Can you tell me what the capital of the United States is?
ASSISTANT: The capital of the United States is Washington D.C.
USER: Can you open apps for me?
ASSISTANT: Yes, I can! What would you like me to open?
USER: Can you please open Chrome
ASSISTANT: Open>chrome
USER: Search for holiday locations
ASSISTANT: Search>Best holiday locations
USER: Open Notepad
ASSISTANT:"""

payload = json.dumps([prompt, params])

response = requests.post(f"http://{server}:7860/run/textgen", json={
    "data": [
        payload
    ]
}).json()

reply = response["data"][0].replace(prompt, "")
print(reply)