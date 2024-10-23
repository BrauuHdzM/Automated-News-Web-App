# -*- coding: utf-8 -*-
"""Fine Tuning GPT 3.5 for news

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1VY7vACxrNqbI5p6vh2KakDRhvYuTZL47

### Installing all necessary dependencies
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install openai tiktoken langchain
!python -m spacy download es_core_news_lg
!pip install -q datasets

"""### Setup the environment data"""

from google.colab import userdata
import os
os.environ['OPENAI_API_KEY'] = " " # Your OpenAI API key

import openai

"""### Preprocessing the dataset of news"""

from datasets import load_dataset
import spacy
import datasets

data = load_dataset("BrauuHdzM/Noticias-con-resumen")

nlp = spacy.load("es_core_news_lg")

"""Apply the format required by OpenAI:
```
{
  "messages": [
    { "role": "system", "content": "You are an assistant that occasionally misspells words" },
    { "role": "user", "content": "Tell me a story." },
    { "role": "assistant", "content": "One day a student went to schoool." }
  ]
}
```
"""

def extract_first_loc(text):
    doc = nlp(text)
    first_loc = next((ent.text for ent in doc.ents if ent.label_ == "LOC"), None) # Find the first entity of type LOC

    return first_loc

def formatear_ejemplo(example, system_message=None):
    messages = []

    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })

    if(extract_first_loc(example["Contenido"])):
          content = "Crea un artículo de noticias con esta información: " + example["resumen"] + ". " + "Fecha: " + example["Fecha"] + ". Lugar: " + extract_first_loc(example["Contenido"])
    else:
          content = "Crea un artículo de noticias con esta información: " + example["resumen"] + ". " + "Fecha: " + example["Fecha"]

    message = {
            "role": "user",
            "content": content
        }

    messages.append(message)

    if(extract_first_loc(example["Contenido"])):
          content = "El " + example["Fecha"] +  ", en " + extract_first_loc(example["Contenido"]) + ". " + example["Contenido"]
    else:
          content = "El " + example["Fecha"] +  ". " + example["Contenido"]

    message = {
            "role": "assistant",
            "content": content
        }

    messages.append(message)

    dict_final = {
        "messages": messages
    }

    return dict_final

train_dataset = data['train']

system_message = 'Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal.'

dataset = []
ejemplo = []

for elemento in train_dataset:
  ejemplo_formateado = formatear_ejemplo(elemento, system_message=system_message)
  dataset.append(ejemplo_formateado)

"""### Validate format, errors, and estimate price"""

# Format error checks
from collections import defaultdict
format_errors = defaultdict(int)

for ex in dataset:
    if not isinstance(ex, dict):
        format_errors["data_type"] += 1
        continue

    messages = ex.get("messages", None)
    if not messages:
        format_errors["missing_messages_list"] += 1
        continue

    for message in messages:
        if "role" not in message or "content" not in message:
            format_errors["message_missing_key"] += 1

        if any(k not in ("role", "content", "name") for k in message):
            format_errors["message_unrecognized_key"] += 1

        if message.get("role", None) not in ("system", "user", "assistant"):
            format_errors["unrecognized_role"] += 1

        content = message.get("content", None)
        if not content or not isinstance(content, str):
            format_errors["missing_content"] += 1

    if not any(message.get("role", None) == "assistant" for message in messages):
        format_errors["example_missing_assistant_message"] += 1

if format_errors:
    print("Found errors:")
    for k, v in format_errors.items():
        print(f"{k}: {v}")
else:
    print("No errors found")

import tiktoken
import numpy as np
encoding = tiktoken.get_encoding("cl100k_base")

# not exact!
# simplified from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1):
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens

def num_assistant_tokens_from_messages(messages):
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            num_tokens += len(encoding.encode(message["content"]))
    return num_tokens

def print_distribution(values, name):
    print(f"\n#### Distribución de {name}:")
    print(f"min / max: {min(values)}, {max(values)}")
    print(f"media / mediana: {np.mean(values)}, {np.median(values)}")
    print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")

# Last, we can look at the results of the different formatting operations before proceeding with creating a fine-tuning job:

# Warnings and tokens counts
n_missing_system = 0
n_missing_user = 0
n_messages = []
convo_lens = []
assistant_message_lens = []

for ex in dataset:
    messages = ex["messages"]
    if not any(message["role"] == "system" for message in messages):
        n_missing_system += 1
    if not any(message["role"] == "user" for message in messages):
        n_missing_user += 1
    n_messages.append(len(messages))
    convo_lens.append(num_tokens_from_messages(messages))
    assistant_message_lens.append(num_assistant_tokens_from_messages(messages))

print("Num de ejemplos sin el system message:", n_missing_system)
print("Num de ejemplos sin el user message:", n_missing_user)
print_distribution(n_messages, "num_mensajes_por_ejemplo")
print_distribution(convo_lens, "num_total_tokens_por_ejemplo")
print_distribution(assistant_message_lens, "num_assistant_tokens_por_ejemplo")
n_too_long = sum(l > 4096 for l in convo_lens)
print(f"\n{n_too_long} ejemplos que excedan el límite de tokenes de 4096, ellos serán truncados durante el fine-tuning")

# Pricing and default n_epochs estimate
MAX_TOKENS_PER_EXAMPLE = 4096

MIN_TARGET_EXAMPLES = 100
MAX_TARGET_EXAMPLES = 25000
TARGET_EPOCHS = 4
MIN_EPOCHS = 1
MAX_EPOCHS = 25

n_epochs = TARGET_EPOCHS
n_train_examples = len(dataset)
if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
    n_epochs = min(MAX_EPOCHS, MIN_TARGET_EXAMPLES // n_train_examples)
elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
    n_epochs = max(MIN_EPOCHS, MAX_TARGET_EXAMPLES // n_train_examples)

n_billing_tokens_in_dataset = sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in convo_lens)
print(f"El conjunto de datos tiene ~{n_billing_tokens_in_dataset} tokens que serán cargados durante el entrenamiento")
print(f"Por defecto, entrenarás para {n_epochs} epochs en este conjunto de datos")
print(f"Por defecto, serás cargado con ~{n_epochs * n_billing_tokens_in_dataset} tokens")
print("Revisa la página para estimar el costo total")

"""### We save the data formatted in JSONL"""

import json

def save_to_jsonl(dataset, file_path):
    with open(file_path, 'w') as file:
        for ejemplo in dataset:
            json_line = json.dumps(ejemplo, ensure_ascii=False)
            file.write(json_line + '\n')

save_to_jsonl(dataset, 'noticias-100-resumen.jsonl')

"""### Create a request to perform Fine Tuning

"""

from openai import OpenAI
client = OpenAI()

train_full_response_file = client.files.create(
  file=open("noticias-100-resumen.jsonl", "rb"),
  purpose="fine-tune"
)

print(f'id: {train_full_response_file.id}')

response = client.fine_tuning.jobs.create(training_file=train_full_response_file.id,
                                       model="gpt-3.5-turbo", # Check all the models available
                                       suffix=' ', # Add a suffix to the model name
                                       hyperparameters={'n_epochs':4}) # Put the number of epochs

response