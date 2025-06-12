# 🎙 Voice Assistant V2

**Voice Assistant V2** es un asistente virtual avanzado con personalidad personalizada, diseñado para ejecutarse localmente. Integra reconocimiento de voz, síntesis de voz, un modelo conversacional personalizado, control de aplicaciones y soporte visual mediante Live2D para simular expresiones y emociones del personaje.

---

## 🧠 Características

- 🔊 Reconocimiento y síntesis de voz en tiempo real.
- 💬 Modelo conversacional entrenado con personalidad (ej. tsundere).
- 🧮 Módulo de cálculo y comandos útiles integrados.
- 🎭 Visualización animada mediante Live2D.
- 🔗 Control de aplicaciones desde comandos de voz.
- 📁 Sistema de preguntas frecuentes basado en JSON.
- 📊 Dataset personalizable para entrenamiento adicional (`dataset_rin.csv`).

---

## 🗂 Estructura del Proyecto
Voice Assistant V2/
├── Main.py # Script principal para iniciar el asistente
├── config.py # Configuración general
├── requirements.txt # Dependencias necesarias
├── dataset_rin.csv # Dataset de diálogo personalizado
├── preguntas_recientes.json # Memoria temporal de interacciones recientes
├── IA_TEST/ # Módulos relacionados con IA o pruebas
├── Live2DModule/ # Integración con modelo Live2D
└── modules/ # Funcionalidades del asistente
├── application.py # Control de aplicaciones
├── Calculator.py # Módulo de cálculos
└── conversational.py # Motor de conversación

---

## 🛠 Instalación

1. Clona o descomprime el repositorio.
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```
---
3. Ejecuta el archivo principal:
```bash
python Main.py
```
#⚙️ Requisitos
Python 3.8+

Librerías incluidas en requirements.txt:

speech_recognition, pyttsx3, pydub, librosa, etc.

Dependencias para visualización Live2D (consultar carpeta Live2DModule).

#🗣 Personalización
Dataset: Puedes modificar dataset_rin.csv para entrenar el modelo con nuevas respuestas o estilos de personalidad.

Modelo de voz: El proyecto puede integrarse con transformadores de voz como RVC.

Personaje Live2D: Reemplaza el modelo en Live2DModule con tu propio .model3.json o archivos compatibles con VTube Studio.

#📌 Notas
Algunas funcionalidades están pensadas para ejecutarse en local con recursos moderados.

Se recomienda GPU para funciones de IA avanzada.

Puedes ampliar el sistema agregando nuevos módulos a la carpeta modules/.

recuerda instalar pipper los modelos que incluye este son los base no los modificados para descargarlos basicos de pruebas
3. Ejecuta el archivo principal:
```bash
python IA_TEST.py
```
#🤝 Contribuciones
Sugerencias, mejoras y contribuciones son bienvenidas.

Abre un issue

O haz un pull request

¡Gracias por tu interés en el proyecto!
