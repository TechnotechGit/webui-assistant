import sys
sys.path.insert(0, './exllama')
from model import ExLlama, ExLlamaCache, ExLlamaConfig
from tokenizer import ExLlamaTokenizer
from generator import ExLlamaGenerator
import model_init
import argparse
import torch
import os
import time

# class Generate:
#     def __init__(self):
#         torch.set_grad_enabled(False)
#         torch.cuda._lazy_init()

#         base_folder = "Wizard-Vicuna-7B-Uncensored-GPTQ"
#         # Load the tokenizer, model config, and model
#         self.tokenizer_model_path = f"./{base_folder}/tokenizer.model"
#         # self.model_config_path = f"./{base_folder}/config.json"
#         # for fname in os.listdir('.'):
#         #     if fname.endswith('.safetensors'):
#         #         # do stuff on the file
#         #         self.model_path = f"./{base_folder}/{fname}"
#         #         break
#         # else:
#         #     print("No .safetensors file found.")
#         #     return

#         self.tokenizer = ExLlamaTokenizer(self.tokenizer_model_path)

#         args = argparse.Namespace(
#             prompt=None,
#             username="User",
#             botname="Assistant",
#             botfirst=False,
#             no_newline=False,
#             temperature=0.95,
#             top_k=20,
#             top_p=0.65,
#             min_p=0.00,
#             repetition_penalty=1.15,
#             repetition_penalty_sustain=256,
#             beams=1,
#             beam_length=1,
#             directory=base_folder,
#         )

#         args.gpu_split = None
#         args.length = 2048
#         args.gpu_peer_fix = False
#         args.matmul_recons_thd = 8
#         args.fused_mlp_thd = 2
#         args.sdp_thd = 8
#         args.matmul_fused_remap = False
#         args.rmsnorm_no_half2 = False
#         args.rope_no_half2 = False
#         args.matmul_no_half2 = False
#         args.silu_no_half2 = False
#         args.no_half2 = False
#         args.force_half2 = False
#         # args.no_fused_attn = False

#         model_init.post_parse(args)
#         model_init.get_model_files(args)
#         config = model_init.make_config(args)
#         self.model = ExLlama(config)
#         self.cache = ExLlamaCache(self.model)

#         model_init.print_stats(self.model)

#         # Instantiate the generator
#         self.generator = ExLlamaGenerator(self.model, self.tokenizer, self.cache)

#         # Set generator settings
#         self.generator.settings = ExLlamaGenerator.Settings()
#         self.generator.settings.temperature = 0.95
#         self.generator.settings.top_k = 20
#         self.generator.settings.top_p = 0.65
#         self.generator.settings.min_p = 0.00
#         self.generator.settings.token_repetition_penalty_max = 1.15
#         self.generator.settings.token_repetition_penalty_sustain = 256
#         self.generator.settings.token_repetition_penalty_decay = self.generator.settings.token_repetition_penalty_sustain // 2
#         self.generator.settings.beams = 1
#         self.generator.settings.beam_length = 1

#     def generate_simple(self, prompt, max_new_tokens):
#         print(self.generator)
#         _MESSAGE = prompt
#         t0 = time.time()
#         new_text = ""
#         last_text = ""
#         _full_answer = ""

#         self.generator.end_beam_search()

#         ids = self.tokenizer.encode(prompt)
#         self.generator.gen_begin_reuse(ids)

#         for i in range(max_new_tokens):
#             token = self.generator.gen_single_token()
#             text = self.tokenizer.decode(self.generator.sequence[0])
#             new_text = text[len(_MESSAGE):]

#             # Get new token by taking difference from last response:
#             new_token = new_text.replace(last_text, "")
#             last_text = new_text

#             #print(new_token, end="", flush=True)
#             yield new_token

#             # [End conditions]:
#             #if break_on_newline and # could add `break_on_newline` as a GenerateRequest option?
#             #if token.item() == tokenizer.newline_token_id:
#             #    print(f"newline_token_id: {tokenizer.newline_token_id}")
#             #    break
#             if token.item() == self.tokenizer.eos_token_id:
#                 #print(f"eos_token_id: {tokenizer.eos_token_id}")
#                 break

#         # all done:
#         self.generator.end_beam_search() 
#         _full_answer = new_text

#         # get num new tokens:
#         prompt_tokens = self.tokenizer.encode(_MESSAGE)
#         prompt_tokens = len(prompt_tokens[0])
#         new_tokens = self.tokenizer.encode(_full_answer)
#         new_tokens = len(new_tokens[0])

#         # calc tokens/sec:
#         t1 = time.time()
#         _sec = t1-t0
#         _tokens_sec = new_tokens/(_sec)

#         #print(f"full answer: {_full_answer}")

#         print(f"\nOutput generated in {_sec} ({_tokens_sec} tokens/s, {new_tokens}, context {prompt_tokens})")

#     # Usage example
#     # prompt = "Chatbot, what is the meaning of life?"

#     # max_new_tokens = 100

#     # for token in generate_simple(prompt, max_new_tokens):
#     #     print(token, end="")

torch.set_grad_enabled(False)
torch.cuda._lazy_init()


class GenerateResponse:
    def __init__(self, model_name):
        # self.tokenizer_model_path = "./TheBloke_Wizard-Vicuna-13B-Uncensored-GPTQ/tokenizer.model"
        # self.model_config_path = "./TheBloke_Wizard-Vicuna-13B-Uncensored-GPTQ/config.json"
        # self.model_path = "./TheBloke_Wizard-Vicuna-13B-Uncensored-GPTQ/Wizard-Vicuna-13B-Uncensored-GPTQ-4bit-128g.compat.no-act-order.safetensors"
        # airoboros-7B-gpt4-1.2-GPTQ
        # Wizard-Vicuna-7B-Uncensored-GPTQ
        self.base_folder = model_name
        # Load the tokenizer, model config, and model
        self.tokenizer_model_path = f"./{self.base_folder}/tokenizer.model"
        self.tokenizer = ExLlamaTokenizer(self.tokenizer_model_path)
        self.args = self._parse_arguments()
        self.model, self.cache = self._initialize_model()

        self.generator = ExLlamaGenerator(self.model, self.tokenizer, self.cache)
        self.generator.settings = ExLlamaGenerator.Settings()

    def _parse_arguments(self):
        args = argparse.Namespace(
            prompt=None,
            username="User",
            botname="Chatbort",
            botfirst=False,
            no_newline=False,
            temperature=0.95,
            top_k=20,
            top_p=0.65,
            min_p=0.00,
            repetition_penalty=1.15,
            repetition_penalty_sustain=256,
            beams=1,
            beam_length=1,
            directory=self.base_folder,
        )
        args.gpu_split = None
        args.length = 2048
        args.gpu_peer_fix = False
        args.matmul_recons_thd = 8
        args.fused_mlp_thd = 2
        args.sdp_thd = 8
        args.matmul_fused_remap = False
        args.rmsnorm_no_half2 = False
        args.rope_no_half2 = False
        args.matmul_no_half2 = False
        args.silu_no_half2 = False
        args.no_half2 = False
        args.force_half2 = False
        args.no_fused_attn = False
        args.concurrent_streams = 1

        model_init.post_parse(args)
        model_init.get_model_files(args)
        self.config = model_init.make_config(args)
        return args

    def _initialize_model(self):
        # config = model_init.make_config(args)
        model = ExLlama(self.config)
        cache = ExLlamaCache(model)
        model_init.print_stats(model)
        # model.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu')))
        return model, cache

    def _initialize_generator_settings(self):
        settings = ExLlamaGenerator.Settings()
        settings.temperature = self.args.temperature
        settings.top_k = self.args.top_k
        settings.top_p = self.args.top_p
        settings.min_p = self.args.min_p
        settings.token_repetition_penalty_max = self.args.repetition_penalty
        settings.token_repetition_penalty_sustain = self.args.repetition_penalty_sustain
        settings.token_repetition_penalty_decay = settings.token_repetition_penalty_sustain // 2
        settings.beams = self.args.beams
        settings.beam_length = self.args.beam_length
        return settings

    # def generate_simple(self, prompt, max_new_tokens):
    #     _MESSAGE = prompt
    #     t0 = time.time()
    #     new_text = ""
    #     last_text = ""
    #     _full_answer = ""

    #     self.generator.end_beam_search()

    #     ids = self.tokenizer.encode(prompt)
    #     self.generator.gen_begin_reuse(ids)

    #     for i in range(max_new_tokens):
    #         token = self.generator.gen_single_token()
    #         text = self.tokenizer.decode(self.generator.sequence[0])
    #         new_text = text[len(_MESSAGE):]

    #         # Get new token by taking difference from last response:
    #         new_token = new_text.replace(last_text, "")
    #         last_text = new_text

    #         yield new_token

    #         if token.item() == self.tokenizer.eos_token_id:
    #             break

    #     self.generator.end_beam_search()
    #     _full_answer = new_text

    #     prompt_tokens = self.tokenizer.encode(_MESSAGE)
    #     prompt_tokens = len(prompt_tokens[0])
    #     new_tokens = self.tokenizer.encode(_full_answer)
    #     new_tokens = len(new_tokens[0])

    #     t1 = time.time()
    #     _sec = t1 - t0
    #     _tokens_sec = new_tokens / (_sec)

    #     print(f"\nOutput generated in {_sec} ({_tokens_sec} tokens/s, {new_tokens}, context {prompt_tokens})")

    def generate_simple(self, prompt, max_new_tokens):
        _MESSAGE = prompt
        t0 = time.time()
        new_text = ""
        last_text = ""
        _full_answer = ""

        self.generator.end_beam_search()

        ids = self.tokenizer.encode(prompt)
        self.generator.gen_begin_reuse(ids)

        print(max_new_tokens)

        for i in range(max_new_tokens):
            token = self.generator.gen_single_token()
            text = self.tokenizer.decode(self.generator.sequence[0])
            new_text = text[len(_MESSAGE):]

            # Get new token by taking difference from last response:
            new_token = new_text.replace(last_text, "")
            last_text = new_text

            #print(new_token, end="", flush=True)
            yield new_token

            # [End conditions]:
            #if break_on_newline and # could add `break_on_newline` as a GenerateRequest option?
            #if token.item() == tokenizer.newline_token_id:
            #    print(f"newline_token_id: {tokenizer.newline_token_id}")
            #    break
            if token.item() == self.tokenizer.eos_token_id:
                # print(f"eos_token_id: {self.tokenizer.eos_token_id}")
                break

        # all done:
        self.generator.end_beam_search() 
        _full_answer = new_text

        # get num new tokens:
        prompt_tokens = self.tokenizer.encode(_MESSAGE)
        prompt_tokens = len(prompt_tokens[0])
        new_tokens = self.tokenizer.encode(_full_answer)
        new_tokens = len(new_tokens[0])

        # calc tokens/sec:
        t1 = time.time()
        _sec = t1-t0
        _tokens_sec = new_tokens/(_sec)

        #print(f"full answer: {_full_answer}")

        print(f"\nOutput generated in {_sec} ({_tokens_sec} tokens/s, {new_tokens}, context {prompt_tokens})")

    def generate_response(self, prompt, max_new_tokens):
        for token in self.generate_simple(prompt, max_new_tokens):
            print(token, end="")


# # Usage example
# if __name__ == "__main__":
#     prompt = "Chatbot, what is the meaning of life?"
#     max_new_tokens = 100

#     generator = GenerateResponse()
#     generator.generate_response(prompt, max_new_tokens)