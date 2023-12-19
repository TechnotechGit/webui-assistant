import time
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from oobaAPI import AIModel

model = AIModel(host="neat-teams-cheat.loca.lt")

app = Flask(__name__)

# Add chat history sidebar later
chat_history = []

def generate_response_tokens(input_text):
    current_date = time.strftime("%Y-%m-%d")
    current_time = time.strftime("%I:%M %p")

    preprompt = f"The following is conversation between a user and a helpful and truthful AI assistant that often uses emojis. The AI assistant will attempt to answer the user's questions as truthfully and accurately as possible.\nDATE: {current_date}.\nTIME: {current_time}.\nLATEST TRAINING DATA: September, 2021.\n"
    # Iterate through chat history and add each message to preprompt with prefix
    for message in chat_history:
        preprompt += "USER: " + message['user'] + "\n"
        preprompt += "ASSISTANT: "+ message['bot'] + "\n"
    preprompt += "USER: " + input_text + "\nASSISTANT:"
    print(preprompt)

    full_text = ""
    # tokens = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nibh nisl condimentum id venenatis a. Dui id ornare arcu odio ut sem nulla. Consequat id porta nibh venenatis. At quis risus sed vulputate odio ut enim blandit. Nisl condimentum id venenatis a condimentum vitae sapien pellentesque. Ut aliquam purus sit amet luctus venenatis lectus magna fringilla. Egestas tellus rutrum tellus pellentesque eu tincidunt tortor aliquam. Scelerisque varius morbi enim nunc faucibus a pellentesque sit amet. Dignissim cras tincidunt lobortis feugiat vivamus at.".split(" ")
    tokens = model.response_stream(preprompt)
    
    for token in tokens:
        # time.sleep(0.04)  # Simulating some processing time
        # token += " "
        token = token.replace(preprompt, "")
        full_text += token
        yield token
    chat_history.append({'user': input_text, 'bot': full_text})


@app.route('/')
def index():
    return render_template('index.html', chat_history=chat_history)


@app.route('/stream', methods=['POST'])
def stream():
    input_text = request.json['message']
    return Response(stream_with_context(generate_response_tokens(input_text)), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
