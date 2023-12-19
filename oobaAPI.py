import json
import sys
import websocket

class AIModel:
    def __init__(self, host='localhost:5005'):
        self.host = host
        self.uri = f'ws://{self.host}/api/v1/stream'
        self.websocket = None

    def connect(self):
        self.websocket = websocket.WebSocket()
        self.websocket.connect(self.uri)

    def disconnect(self):
        if self.websocket is not None:
            self.websocket.close()
            self.websocket = None

    def send_request(self, request):
        if self.websocket is not None:
            self.websocket.send(json.dumps(request))

    def receive_response(self):
        if self.websocket is not None:
            response = self.websocket.recv()
            return json.loads(response)
        return None

    def run(self, context, stopping_strings = []):
        request = {
            'prompt': context,
            'max_new_tokens': 1024,
            'preset': 'None',
            'do_sample': True,
            'temperature': 0.75,
            'top_p': 0.9,
            'typical_p': 1,
            'epsilon_cutoff': 0,
            'eta_cutoff': 0,
            'top_a': 0,
            'repetition_penalty': 1.18,
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
            'stopping_strings': stopping_strings
        }

        self.connect()
        self.send_request(request)

        yield context

        while True:
            incoming_data = self.receive_response()

            if incoming_data is None:
                break

            if incoming_data['event'] == 'text_stream':
                yield incoming_data['text']
            elif incoming_data['event'] == 'stream_end':
                self.disconnect()
                return

    def response_stream(self, prompt, stopping_strings = []):
        for response in self.run(prompt, stopping_strings):
            # print(response, end='')
            # sys.stdout.flush()
            yield response

    def run_stream(self, prompt, stopping_strings = []):
        self.response_stream(prompt, stopping_strings)