from ctransformers import AutoModelForCausalLM
import time
import sys

llm = AutoModelForCausalLM.from_pretrained('./TheBloke_WizardCoder-15B-1.0-GGML/WizardCoder-15B-1.0.ggmlv3.q4_0.bin', model_type='starcoder')
chat_history = []

stop_tokens = ["USER:"]

while True:
    user = input("USER: ")
    print("ASSISTANT:", end='', flush=True)

    preprompt = "Below is an instruction that describes a task. Write a response that appropriately completes the request\n"
    # for message in chat_history:
    #     preprompt += "USER: " + message['user'] + "\n"
    #     preprompt += "ASSISTANT: "+ message['bot'] + "\n"
    # preprompt += "USER: " + user
    # response = ""

    # start_time = time.time()
    # tokens = llm.tokenize(preprompt + "\nASSISTANT:")
    for message in chat_history:
        preprompt += "### Instruction: " + message['user'] + "\n"
        preprompt += "### Response: "+ message['bot'] + "\n"
    preprompt += "### Instruction: " + user
    response = ""

    start_time = time.time()
    tokens = llm.tokenize(preprompt + "\n### Response:")
    num_tokens = []
    stop_generator = False
    for t in llm.generate(tokens, threads=6):
        token = llm.detokenize(t)
        if token in stop_tokens:
            stop_generator = True
            break
        for l in stop_tokens:
            if l in response:
                response = response.replace(l, "")
                stop_generator = True
                break
        if stop_generator:
            break
        response += token
        num_tokens.append(t)
        print(token, end='', flush=True)

    # Replace the previous line by adding \r and a comma at the end
    # Move the cursor one line up and print t/s and tokens
    if stop_generator:
        print(f"\r({len(num_tokens) / (time.time() - start_time):.2f} t/s, {len(num_tokens)} tokens)")
    else:
        print(f" ({len(num_tokens) / (time.time() - start_time):.2f} t/s, {len(num_tokens)} tokens)")

    # Move the cursor one line down
    # print("\033[1B", end='')
    chat_history.append({'user': user, 'bot': response})

    # Print tokens per second
    # print(f" ({len(num_tokens) / (time.time() - start_time):.2f} t/s, {len(num_tokens)} tokens)")