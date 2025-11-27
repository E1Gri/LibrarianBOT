from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from .cleaner import tclean

class LLM:

    def __init__(self):
        self.local_dir = "stablelm_local"
        self.flag_file = os.path.join(self.local_dir, "model_ready.flag")
        os.makedirs(self.local_dir, exist_ok=True)

        self.model_name = "Qwen/Qwen3-4B-Instruct-2507"
        
        if not os.path.exists(self.flag_file):

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            tokenizer.save_pretrained(self.local_dir)

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                local_files_only=False,
                dtype=torch.bfloat16,
                device_map="auto" 
            )
            model.save_pretrained(self.local_dir)

            
            with open(self.flag_file, "w") as f:
                f.write("ok")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.local_dir,
            local_files_only=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.local_dir,
            local_files_only=False,
            dtype=torch.bfloat16,
            device_map="auto"
        )

    def describeGenres(self, usr_prompt: str):
        
        # with open(genres_path) as f:
        #     genres = f.read()

        prompt = (
            "Ты библиотекарь и литературный эксперт. На основе списка слов напиши **только 5 жанров книги**, в точности так, как это реально существует. Ответ **должен быть одной строкой**, без скобок, авторов, пояснений, кавычек, запятых или любых других слов. укажи только жанр. Если ты закончил с жанрами, то **просто заполни пространство пробелами** Не повторяй себя, просто остановись"
            ) #+ "Выбирай жанры и ключевые слова из следуйщего списка: " + genres + " "
        
        usr_prompt = tclean(usr_prompt)

        full_prompt = f"{usr_prompt}\n\n{prompt}\n"

        device = next(self.model.parameters()).device 
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(device)

        with torch.inference_mode():
            outputs = self.model.generate(
            **inputs,
            max_new_tokens=20
            )   

        # generated_tokens = outputs.sequences[:, inputs["input_ids"].shape[-1]:]
        generated_tokens = outputs[:, inputs["input_ids"].shape[-1]:]

        answer = self.tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
        # print("\nРезультат:\n", answer, "\n")    
        return answer  