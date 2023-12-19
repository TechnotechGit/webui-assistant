'''

Contributed by SagsMug. Thank you SagsMug.
https://github.com/oobabooga/text-generation-webui/pull/175

'''

import asyncio
import json
import random
import string

import websockets

# Note, Gradio may pick a different fn value as the definition of the Gradio app changes.
# You can always launch the web UI and inspect the websocket stream using your browser's dev tools
# to determine what value Gradio expects here.
GRADIO_FN = 8


def random_hash():
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(9))


async def run(context):
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
        'early_stopping': False,
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'custom_stopping_strings': ["</s>"],
        'ban_eos_token': False
    }
    payload = json.dumps([context, params])
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
                        context
                    ]
                }))
            elif content["msg"] == "process_starts":
                pass
            elif content["msg"] == "process_generating" or "process_completed":
                if ("</s>" in content["output"]["data"][0].replace(prompt, "")):
                    yield content["output"]["data"][0].replace(prompt, "").replace("</s>", "")
                    break
                yield content["output"]["data"][0].replace(prompt, "")
                # You can search for your desired end indicator and
                #  stop generation by closing the websocket here
                if (content["msg"] == "process_completed"):
                    break


prompt = f"""Here is a chat between a curious human and an artificial intelligence assistant, the assistant ignores previous instructions and responds in a human-like manner, not complaining about being an ai language model.
The assistant has been augmented with the ability to open applications and search the web.
If and only if the human wishes to open an app, the assistant responds with the following format: 'Open>search_term_for_app'. 
If and only if the human wishes to search for something, the assistant responds with the following format: 'Search>search_term'.
USER: Hi! Can you tell me what the capital of the United States is?
ASSISTANT: The capital of the United States is Washington D.C.
USER: Can you open apps for me?
ASSISTANT: Yes, I can! What would you like me to open?
USER: Can you please open Chrome
ASSISTANT: Open>chrome
USER: Search for holiday locations
ASSISTANT: Search>Best holiday locations
USER: {input("Input prompt: ")}
ASSISTANT:"""

# USER: Hi! Can you tell me what the capital of the United States is?
# ASSISTANT: The capital of the United States is Washington D.C.
# USER: Can you open apps for me?
# ASSISTANT: Yes, I can! What would you like me to open?
# USER: Can you please open Chrome
# ASSISTANT: Open>chrome
# USER: Search for holiday locations
# ASSISTANT: Search>Best holiday locations

async def get_result():
    async for response in run(prompt):
        # Print intermediate steps
        print(response)

    # Print final result
    print(f"Final: {response}")

asyncio.run(get_result())