# from llm_rs import AutoModel, KnownModels
from llm_rs import Gpt2, SessionConfig, Precision, GenerationConfig
import time

session_config = SessionConfig(
    threads=8,
    batch_size=8,
    use_gpu=True,
    # gpu_layers=1,
    context_length=512,
    prefer_mmap=True,
    keys_memory_type=Precision.FP16,
    values_memory_type=Precision.FP16
)

llm = Gpt2('./TheBloke_WizardCoder-15B-1.0-GGML/WizardCoder-15B-1.0.ggmlv3.q4_0.bin', session_config=session_config, verbose=False)
chat_history = []

stop_tokens = ["USER:", "<fim_suffix>", "<fim_middle>"]

generation_config = GenerationConfig(top_p=0.8, top_k=50, temperature=0.7, max_new_tokens=10)

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
    # tokens = llm.tokenize(preprompt + "\n### Response:")
    num_tokens = []
    for token in llm.stream(preprompt + "\n### Response:", generation_config):
        if token in stop_tokens:
            break
        for l in stop_tokens:
            if l in response:
                response = response.replace(l, "")
                break
        response += token
        num_tokens.append(token)
        print(token, end='', flush=True)
    chat_history.append({'user': user, 'bot': response})
    # Print tokens per second
    print(f" ({len(num_tokens) / (time.time() - start_time):.2f} t/s, {len(num_tokens)} tokens)")