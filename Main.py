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
from modules.agenda import AgendaModule
from modules.Clima import ClimaModule
from ui.interface import RinInterface
from config import (
    EDGE_DRIVER_PATH,
    MEMORIA_PATH,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    MAX_HISTORY,
    API_KEY
)


def main():
    
    print("🚀 Iniciando programa con ConversationalModule…")
    agenda = AgendaModule()
    clima = ClimaModule(api_key=API_KEY, location="Monterrey,MX")
    # Inicializar TTS y STT
    tts = TextToSpeechModule()
    print("🗣️ Módulo TTS inicializado")

    # Inicializar STT indicando explícitamente el micrófono 0 (ajusta si tienes otro)
    stt = SpeechToTextModule(language='es-ES', mic_index=0)
    print("🎙️ Módulo STT inicializado con micrófono index 0")

    # Inicializar memoria
    memory_module = MemoryModule(file_path=MEMORIA_PATH, max_history=MAX_HISTORY)
    print("🧠 Memoria cargada")

    # Inicializar herramientas externas
    spotify = SpotifyModule()

    print("🎵 Módulo Spotify listo")

    youtube = BrowserModule(EDGE_DRIVER_PATH)
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
        youtube= youtube,
        spotify= spotify,
        device= device,
        agenda= agenda,
        clima = clima
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
    interface = RinInterface(enviar_callback=None, memory_module=memory_module, tts=tts, stt= stt)
    interface.show()

    # Asignar callback y pasar referencia de interfaz
    interface.enviar_callback = lambda texto_usuario: procesar_entrada(
        texto_usuario, stt, tts, conversational, memory_module, interface
    )

    sys.exit(app.exec())

def procesar_entrada(texto_input, stt, tts, conversational, memory_module, interface):
    texto_usuario = texto_input.strip()
    if not texto_usuario:
        return "No entendí nada, intenta otra vez."

    if texto_usuario.lower() in ["salir", "adiós", "hasta luego"]:
        despedida = "Adiós... :b."
        memory_module.add_to_history("Usuario", texto_usuario)
        memory_module.add_to_history("Rin", despedida)
        tts.speak(despedida)
        QApplication.quit()
        return despedida

    memory_module.add_to_history("Usuario", texto_usuario)

    try:
        respuesta = conversational.generar_respuesta(texto_usuario)
    except Exception as e:
        print("[Conversational Error]", e)
        respuesta = "Ups, tuve un problema procesando eso."

    if not respuesta:
        respuesta = "No tengo una respuesta para eso todavía."

    memory_module.add_to_history("Rin", respuesta)
    tts.speak(respuesta)
    return respuesta

if __name__ == "__main__":
    main()
