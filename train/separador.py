import pandas as pd

# Carga el CSV (ajusta la ruta si es necesario)
df = pd.read_csv("C:/Voice asistant V2/train/rin_dataset_comandos_naturales.csv")

# Extrae las columnas como listas
entradas = df["entrada"].dropna().tolist()
respuestas = df["respuesta"].dropna().tolist()

# Guarda cada lista en un archivo de texto, añadiendo comillas alrededor de cada entrada/respuesta
with open("entradas.txt", "w", encoding="utf-8") as f:
    for entrada in entradas:
        f.write(f'"{entrada.strip()}"\n')

with open("respuestas.txt", "w", encoding="utf-8") as f:
    for respuesta in respuestas:
        f.write(f'"{respuesta.strip()}"\n')

print("¡Listo! Archivos 'entradas.txt' y 'respuestas.txt' generados con comillas.")
