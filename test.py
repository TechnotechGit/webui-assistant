from generate import GenerateResponse

generator = GenerateResponse()
# generator.generate_response("User: Chatbot, what is the meaning of life?\nAssistant:", 200)
for token in generator.generate_simple("User: Chatbot, what is the meaning of life?\nAssistant:", 200):
    print(token, end="")