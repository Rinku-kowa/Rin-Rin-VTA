import os
import sys
import torch
from PySide6.QtWidgets import QApplication

from modules.conversational import ConversationalModule
from modules.memory import MemoryModule
from modules.speech_to_text import SpeechToTextModule
from modules.text_to_speech import TextToSpeechModule
from modules.spotify import SpotifyModule
from modules.youtube import BrowserModule
from modules.internet_search import InternetSearchModule
from modules.Calculator import CalculatorModule 
from ui.interface import RinInterface
from config import (
    EDGE_DRIVER_PATH,
    MEMORIA_PATH,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    MAX_HISTORY,
    OPENAI_API_KEY
)


def main():
    print("🚀 Iniciando programa con ConversationalModule…")

    # Inicializar TTS y STT
    tts = TextToSpeechModule()
    print("🗣️ Módulo TTS inicializado")

    stt = SpeechToTextModule()
    print("🎙️ Módulo STT inicializado")

    # Inicializar memoria
    memory_module = MemoryModule(file_path=MEMORIA_PATH, max_history=MAX_HISTORY)
    print("🧠 Memoria cargada")

    # Inicializar herramientas externas
    spotify = SpotifyModule()

    print("🎵 Módulo Spotify listo")

    browser = BrowserModule(EDGE_DRIVER_PATH)
    print("🌐 Youtube listo")

    # Inicializar módulo de búsqueda en Internet con navegador y clave de OpenAI
    internet_search = InternetSearchModule(edge_driver_path=EDGE_DRIVER_PATH)
    print("🔎 Módulo Búsqueda en Internet listo")

    calculator = CalculatorModule()
    print("🧮 Módulo Calculadora listo")

    # Inicializar ConversationalModule con todas las herramientas
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    conversational = ConversationalModule(
        model_dir="C:/Voice asistant V2/models",
        memory_module=memory_module,
        calculator=calculator,
        internet_search=internet_search,
        browser=browser,
        spotify=spotify,
        device=device
    )
    print("🤖 Módulo Conversacional cargado")

    # Obtener o preguntar el nombre del dueño
    dueno = memory_module.get_dueno()
    if not dueno:
        pregunta_nombre = memory_module.ask_for_dueno()
        tts.speak(pregunta_nombre)

        modo_input = input("¿Modo 'voz' o 'texto'? ").strip().lower()
        if modo_input == "voz":
            nombre_respuesta = stt.escuchar().strip()
        else:
            nombre_respuesta = input("Tú: ").strip()

        memory_module.update_memory("dueno", nombre_respuesta)
        dueno = nombre_respuesta

    # Saludo inicial
    saludo = f"Hola {dueno}. ¿Qué deseas ahora?"
    memory_module.add_to_history("Rin", saludo)
    tts.speak(saludo)

    # Inicializar interfaz gráfica
    app = QApplication(sys.argv)
    interface = RinInterface(enviar_callback=None)
    interface.show()

    # Asignar callback y pasar referencia de interfaz
    interface.enviar_callback = lambda texto_usuario: procesar_entrada(
        texto_usuario, stt, tts, conversational, memory_module, interface
    )

    sys.exit(app.exec())


def procesar_entrada(texto_input, stt, tts, conversational, memory_module, interface):
    """
    Callback que procesa la entrada desde la interfaz gráfica.
    Usa STT o texto directo según interface.modo, genera respuesta, guarda en memoria y la reproduce.
    """
    # Determinar texto del usuario según modo
    if interface.modo == "voz":
        texto_usuario = stt.escuchar().strip()
        if texto_usuario:
            interface._append_chat("Tú", texto_usuario, is_usuario=True)
    else:
        texto_usuario = texto_input.strip()
        # En modo texto, RinInterface ya agregó "Tú: texto_usuario" en enviar_texto()

    if not texto_usuario:
        return

    # Comando de salida
    if texto_usuario.lower() in ["salir", "adiós", "hasta luego"]:
        despedida = "Adiós... tonto :b."
        memory_module.add_to_history("Usuario", texto_usuario)
        memory_module.add_to_history("Rin", despedida)
        tts.speak(despedida)
        QApplication.quit()
        return

    # Guardar entrada en memoria
    memory_module.add_to_history("Usuario", texto_usuario)

    # Obtener respuesta del módulo conversacional
    respuesta = conversational.generar_respuesta(texto_usuario)

    # Guardar respuesta en memoria (pero NO mostrarla aquí)
    memory_module.add_to_history("Rin", respuesta)

    # Reproducir respuesta por voz
    tts.speak(respuesta)

    # Devuelve la respuesta para que el WorkerThread la emita y solo la señal muestre en UI
    return respuesta

if __name__ == "__main__":
    main()
