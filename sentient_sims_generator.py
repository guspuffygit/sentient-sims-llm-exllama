import glob
import json
import os
import threading
import time
import torch

from generator import ExLlamaGenerator
from model import ExLlama, ExLlamaCache, ExLlamaConfig
from tokenizer import ExLlamaTokenizer
from sentient_sims_logger import ss_logger


class TooManyTokensError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SentientSimsGenerator:
    def __init__(self, model_path: str, max_token_length: int):
        self.model_path = model_path
        self.max_token_length = max_token_length
        self.lock = threading.Lock()

        tokenizer_path = os.path.join(model_path, "tokenizer.model")
        model_config_path = os.path.join(model_path, "config.json")
        st_pattern = os.path.join(model_path, "*.safetensors")
        model_path = glob.glob(st_pattern)[0]

        # Create config, model, tokenizer and generator
        self.config = ExLlamaConfig(model_config_path)  # create config from config.json
        self.config.model_path = model_path  # supply path to model weights file
        self.config.max_seq_len = max_token_length
        self.config.max_input_len = max_token_length
        self.config.max_attention_size = max_token_length ** 2
        self.config.alpha_value = 1000000

        with open(model_config_path, 'r') as config_json:
            data = json.load(config_json)
            if '_name_or_path' in data:
                self.config.name = data['_name_or_path']
            else:
                self.config.name = 'NA'

        self.model = ExLlama(self.config)  # create ExLlama instance and load the weights
        self.tokenizer = ExLlamaTokenizer(tokenizer_path)  # create tokenizer from tokenizer model file

        self.cache = ExLlamaCache(self.model)  # create cache for inference
        self.generator = ExLlamaGenerator(self.model, self.tokenizer, self.cache)

        # Configure generator
        self.generator.disallow_tokens([self.tokenizer.eos_token_id])
        self.generator.settings.token_repetition_penalty_max = 1.1
        self.generator.settings.temperature = 0.8
        self.generator.settings.top_p = 0.9
        self.generator.settings.top_k = 40
        self.generator.settings.typical = 1
        self.generator.settings.token_repetition_penalty_sustain = self.config.max_seq_len

        self.gpu_name = torch.cuda.get_device_name(torch.cuda.current_device())

    def get_model_name(self):
        return self.config.name

    def get_gpu_name(self):
        return self.gpu_name

    def is_busy(self):
        return self.lock.locked()

    def get_hf_model_name(self):
        model_folder = self.model_path.split('/')[-1]
        model_folder = model_folder.split('\\')[-1]

        username = model_folder.split('_')[0]
        repo_name = '_'.join(model_folder.split('_')[1:])
        return f"{username}/{repo_name}"

    def generate(self, prompt, max_new_tokens):
        with self.lock:
            start_time = time.time()

            total_tokens = self.tokenizer.num_tokens(prompt)
            if total_tokens > (self.config.max_seq_len - max_new_tokens):
                message = f"Total tokens is too high, total tokens: {total_tokens}"
                ss_logger.error(message)
                raise TooManyTokensError(message)

            output = self.generator.generate_simple(prompt, max_new_tokens)
            formatted_output = output[len(prompt):]

            elapsed_time = time.time() - start_time
            output_tokens = self.tokenizer.num_tokens(formatted_output)
            tokens_per_second = output_tokens / elapsed_time
            ss_logger.info(f"{round(tokens_per_second, 2)} tk/s in {round(elapsed_time, 2)} seconds")

            return formatted_output
