import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset
from peft import LoraConfig, get_peft_model
import os

# --------------------------
# ✅ Confirmar uso de GPU o CPU
# --------------------------
if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"[✅] GPU detectada: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("[⚠️] No se detectó GPU. Usando CPU.")

# --------------------------
# 1. Cargar y preparar datos
# --------------------------
df = pd.read_csv("dataset_rin.csv")  # Asumiendo que ya tienes tu dataset
df = df[['entrada', 'respuesta']]

# Adaptar las respuestas al estilo tsundere
def estilo_tsundere(entrada, respuesta):
    entrada = str(entrada).lower()
    if "katrosh" in entrada:
        return "¡¿Q-qué quieres ahora, Katrosh?! Tch... eres tan molesto... ¡No creas que me importas ni nada, baka!"
    else:
        return f"N-no es como que me importe lo que digas... pero está bien. {respuesta}"

df['respuesta'] = df.apply(lambda x: estilo_tsundere(x['entrada'], x['respuesta']), axis=1)
df['text'] = df.apply(lambda x: f"<|startoftext|>Usuario: {x['entrada']}\nRin: {x['respuesta']}<|endoftext|>", axis=1)

# Convertir el DataFrame en un dataset compatible con Hugging Face
dataset = Dataset.from_pandas(df[['text']])

# --------------------------
# 2. Cargar el tokenizador y el modelo base desde el almacenamiento local
# --------------------------

model_dir = "./modelo_rin"  # Carpeta donde guardamos el modelo preentrenado

# Verifica si el modelo y el tokenizador ya están guardados localmente
if os.path.exists(model_dir):
    print(f"[✅] Cargando modelo y tokenizador desde la carpeta local: {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)
else:
    # Si no están guardados, descargar y guardar el modelo y el tokenizador
    print("[⚠️] No se encontraron modelos locales. Descargando modelo desde Hugging Face...")
    model_name = "microsoft/DialoGPT-medium"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.resize_token_embeddings(len(tokenizer))

    # Guardar el modelo y el tokenizador localmente
    print("[✅] Guardando modelo y tokenizador localmente en", model_dir)
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

# Configuración de LoRA (para hacer un ajuste fino más eficiente)
peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["c_attn", "c_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# Tokenización del dataset
def tokenize_fn(batch):
    inputs = tokenizer(batch["text"], padding="max_length", truncation=True, max_length=256)
    inputs["labels"] = inputs["input_ids"].copy()
    return inputs

tokenized_dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

# --------------------------
# 3. Configuración de entrenamiento
# --------------------------
training_args = TrainingArguments(
    output_dir="./modelo_rin",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=5e-5,
    fp16=torch.cuda.is_available(),
    save_strategy="epoch",
    logging_dir="./logs_rin",
    logging_steps=50,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset
)

# --------------------------
# 4. Entrenamiento y guardado del modelo ajustado
# --------------------------
trainer.train()
model.save_pretrained("./RinAi")  # Guardar el modelo ajustado
tokenizer.save_pretrained("./RinAi")  # Guardar el tokenizador ajustado
print("✅ Entrenamiento completo. Modelo guardado en ./RinAi")
