import requests
import json

apiUrl = "http://127.0.0.1:5000/api/v1/generate";
parameters = {
    'prompt': "USER: Can you search the internet for cats?\nASSISTANT:",
    'max_new_tokens': 200,
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
    'stopping_strings': ["USER:"],
    'ban_eos_token': False
}

payload = json.dumps(parameters)
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
response = requests.post(apiUrl, data=payload, headers=headers)
print(response.json()['results'][0]["text"])