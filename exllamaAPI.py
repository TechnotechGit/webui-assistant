import json
import sys
import websocket

class ExLlamaModel:
    def __init__(self, host='localhost:8000'):
        self.host = host
        self.uri = f'ws://{self.host}'
        self.websocket = None

    def connect(self):
        self.websocket = websocket.WebSocket()
        print("Connecting")
        self.websocket.connect(self.uri)

    def disconnect(self):
        if self.websocket is not None:
            self.websocket.close()
            self.websocket = None

    def send_request(self, request):
        if self.websocket is not None:
            print("Sending")
            self.websocket.send(json.dumps(request))

    def receive_response(self):
        if self.websocket is not None:
            response = self.websocket.recv()
            return json.loads(response)
        return None

    def run(self, context, stopping_strings = []):
        request = {
            "action": "infer",
            'text': context,
            'max_new_tokens': 1024,
            'stream': True,
            'temperature': 0.75,
            'top_p': 0.9,
            'top_k': 40,
            'rep_pen': 1.0,
            'min_p': 0.02,
            'stop_conditions': stopping_strings
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

    # async def call_api():
    #     # Define the API endpoint
    #     api_endpoint = "ws://api.example.com:8080"

    #     # Define your request payload
    #     request_payload = {
    #         "action": "echo",
    #         "request_id": "123",
    #         "response_id": "456",
    #         # Add other necessary fields for your specific request
    #     }

    #     # Create a WebSocket connection
    #     async with websocket.create_connection(api_endpoint) as ws:
    #         # Send the request payload as a JSON string
    #         await ws.send(json.dumps(request_payload))

    #         # Wait for the response from the server
    #         response = await ws.recv()

    #         # Process the response (assuming it's in JSON format)
    #         response_data = json.loads(response)
    #         print("Response:", response_data)


    def run_stream(self, prompt, stopping_strings = []):
        self.response_stream(prompt, stopping_strings)

