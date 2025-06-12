import os
import random
import torch
import pandas as pd
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    Trainer, TrainingArguments
)
from datasets import load_dataset, Dataset
from peft import LoraConfig, get_peft_model, PeftModel

# --------------------------
# ✅ Confirmar uso de GPU o CPU
# --------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[✅] Dispositivo: {device}")

# --------------------------
# FASE 1: Entrenar modelo base en diálogo general
# --------------------------
# 1. Carga de datos generales (DailyDialog como ejemplo)
dataset_general = load_dataset("daily_dialog", trust_remote_code=True)["train"]
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
tokenizer.pad_token = tokenizer.eos_token

def tokenize_general(batch):
    enc = tokenizer(batch["dialog"], padding="max_length",
                    truncation=True, max_length=256)
    enc["labels"] = enc["input_ids"].copy()
    return enc

tokenized_general = dataset_general.map(
    tokenize_general, batched=True, remove_columns=dataset_general.column_names
)

model_base = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium").to(device)

training_args_base = TrainingArguments(
    output_dir="./modelo_base",
    per_device_train_batch_size=2,
    num_train_epochs=1,
    learning_rate=5e-5,
    fp16=torch.cuda.is_available(),
    logging_steps=100,
    save_strategy="epoch",
    report_to="none",
)

trainer_base = Trainer(
    model=model_base,
    args=training_args_base,
    train_dataset=tokenized_general
)
trainer_base.train()
model_base.save_pretrained("./modelo_base")
tokenizer.save_pretrained("./modelo_base")

# --------------------------
# FASE 2: Inyectar personalidad con LoRA
# --------------------------
# 1. Leer dataset de Rin
df = pd.read_csv("dataset_rin.csv")[["entrada","respuesta"]]

def estilo_tsundere(entrada, respuesta_modelo):
    entrada_l = entrada.lower()
    # tus frases fijas...
    frases_fijas = {
        "1+1": "¡¿Q-qué clase de pregunta infantil es esa?! Es claramente 2... baka.",
        # ...
    }
    for clave, resp in frases_fijas.items():
        if clave in entrada_l:
            return resp
    # variaciones
    opciones = [
        f"N-no es como que me importe... {respuesta_modelo}",
        # ...
    ]
    return random.choice(opciones)

df["respuesta"] = df.apply(
    lambda x: estilo_tsundere(x["entrada"], x["respuesta"]), axis=1
)
df["text"] = df.apply(
    lambda x: f"<|startoftext|>Usuario: {x['entrada']}\nRin: {x['respuesta']}<|endoftext|>",
    axis=1
)
dataset_persona = Dataset.from_pandas(df[["text"]])

# 2. Carga modelo base desde ./modelo_base
tokenizer = AutoTokenizer.from_pretrained("./modelo_base")
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained("./modelo_base").to(device)

# 3. Configurar LoRA y aplicar
peft_config = LoraConfig(
    r=8, lora_alpha=16, target_modules=["c_attn","c_proj"],
    lora_dropout=0.05, bias="none", task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# 4. Tokenizar dataset de personalidad
def tokenize_persona(batch):
    enc = tokenizer(batch["text"], padding="max_length",
                    truncation=True, max_length=256)
    enc["labels"] = enc["input_ids"].copy()
    return enc

tokenized_persona = dataset_persona.map(
    tokenize_persona, batched=True, remove_columns=["text"]
)

# 5. Entrenar solo LoRA
training_args_persona = TrainingArguments(
    output_dir="./RinAi_adapter",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=5e-5,
    fp16=torch.cuda.is_available(),
    save_strategy="epoch",
    logging_steps=50,
    report_to="none",
)
trainer_persona = Trainer(
    model=model,
    args=training_args_persona,
    train_dataset=tokenized_persona
)
trainer_persona.train()

# 6. Guardar adapter
model.save_pretrained("./RinAi_adapter")
print("✅ Personalidad Rin inyectada con LoRA")

# --------------------------
# USO: Carga en producción
# --------------------------
# from peft import PeftModel
# base = AutoModelForCausalLM.from_pretrained("./modelo_base")
# model = PeftModel.from_pretrained(base, "./RinAi_adapter")
# tokenizer = AutoTokenizer.from_pretrained("./modelo_base")
