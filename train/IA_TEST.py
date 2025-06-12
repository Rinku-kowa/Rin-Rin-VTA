import os
import torch
from transformers import (
    BlenderbotTokenizer,
    BlenderbotForConditionalGeneration,
    MarianMTModel,
    MarianTokenizer
)

# ===============================
# Configuración para 100% offline
# ===============================
os.environ["TRANSFORMERS_OFFLINE"] = "1"         # Nunca intentes conectarte
os.environ["HF_HUB_OFFLINE"] = "1"               # Desactiva el Hub online
os.environ["HF_HOME"] = "./hf_offline_cache"     # Redirige la caché a carpeta local controlada

# Ruta local a los modelos descargados
model_dir = "C:/Voice asistant V2/models"

# Configuración del dispositivo
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================
# Cargar modelos MarianMT
# ============================
# Español → Inglés
tokenizer_es_en = MarianTokenizer.from_pretrained(
    f"{model_dir}/models--Helsinki-NLP--opus-mt-es-en", local_files_only=True
)
model_es_en = MarianMTModel.from_pretrained(
    f"{model_dir}/models--Helsinki-NLP--opus-mt-es-en", local_files_only=True
).to(device)

# Inglés → Español
tokenizer_en_es = MarianTokenizer.from_pretrained(
    f"{model_dir}/models--Helsinki-NLP--opus-mt-en-es", local_files_only=True
)
model_en_es = MarianMTModel.from_pretrained(
    f"{model_dir}/models--Helsinki-NLP--opus-mt-en-es", local_files_only=True
).to(device)

# ============================
# Cargar BlenderBot
# ============================
blender_model_path = f"{model_dir}/models--facebook--blenderbot-400M-distill"

blender_tokenizer = BlenderbotTokenizer.from_pretrained(
    blender_model_path, local_files_only=True
)
blender_model = BlenderbotForConditionalGeneration.from_pretrained(
    blender_model_path, local_files_only=True
).to(device)

# ============================
# Funciones de traducción
# ============================
def traducir_es_a_en(texto):
    inputs = tokenizer_es_en(texto, return_tensors="pt", padding=True, truncation=True).to(device)
    outputs = model_es_en.generate(**inputs)
    return tokenizer_es_en.decode(outputs[0], skip_special_tokens=True)

def traducir_en_a_es(texto):
    inputs = tokenizer_en_es(texto, return_tensors="pt", padding=True, truncation=True).to(device)
    outputs = model_en_es.generate(**inputs)
    return tokenizer_en_es.decode(outputs[0], skip_special_tokens=True)

# ============================
# Interacción principal
# ============================
def generate_blender_response_traducido(texto_espanol):
    texto_en = traducir_es_a_en(texto_espanol)
    inputs = blender_tokenizer(texto_en, return_tensors="pt").to(device)
    outputs = blender_model.generate(**inputs)
    respuesta_en = blender_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return traducir_en_a_es(respuesta_en)

# ============================
# Interfaz de consola
# ============================
def interactive_input():
    print("Asistente OFFLINE (BlenderBot + traducción en/es)")
    while True:
        user_input = input("\nTu mensaje ('salir' para terminar): ").strip()
        if user_input.lower() == 'salir':
            print("Adiós!")
            break

        respuesta = generate_blender_response_traducido(user_input)
        print("\nRespuesta:\n", respuesta)

# ============================
# Ejecutar
# ============================
if __name__ == "__main__":
    interactive_input()
