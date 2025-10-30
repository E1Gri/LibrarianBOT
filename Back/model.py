from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from cleaner import tclean

local_dir = "stablelm_local"
os.makedirs(local_dir, exist_ok=True)

model_name = "Qwen/Qwen3-4B-Instruct-2507"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.save_pretrained(local_dir)

model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16)
model.save_pretrained(local_dir)
print("Модель сохранена")

tokenizer = AutoTokenizer.from_pretrained(local_dir, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    local_dir,
    local_files_only=True,
    torch_dtype=torch.bfloat16,
    device_map="auto"  
)


prompt = (
    "Ты библиотекарь и литературный эксперт. На основе списка слов напиши **только 3 жанра книги**, в точности так, как это реально существует. Ответ **должен быть одной строкой**, без скобок, авторов, пояснений, кавычек, запятых или любых других слов. укажи только жанр. Если ты закончил с жанрами, то **просто заполни пространство пробелами** Не повторяй себя, просто остановись"

)

print("Напиши описание книги")


#usr_prompt = tclean(input("Введите описание книги: "))

usr_prompt = tclean('Это история о молодом мальчике-сироте, который узнаёт, что он не совсем обычный: у него есть удивительные способности, о которых он до этого не подозревал. Он поступает в школу, где обучают магии, заводит верных друзей и сталкивается с тайнами прошлого, опасными врагами и собственными внутренними страхами. В этом мире есть волшебные существа, заклинания, необычны')

full_prompt = f"{usr_prompt}\n\n{prompt}\n"

inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

print("Ответ генирируется")

with torch.no_grad():

    outputs = model.generate(
    **inputs,
    max_new_tokens=40,
    temperature=0.05,
    top_p=0.9,
    do_sample=False,
    return_dict_in_generate=True
)

generated_tokens = outputs.sequences[:, inputs["input_ids"].shape[-1]:]


answer = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
print("\nРезультат:\n", answer, "\n")




