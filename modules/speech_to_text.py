import speech_recognition as sr

class SpeechToTextModule:
    def __init__(self, language='es-ES'):
        self.recognizer = sr.Recognizer()
        self.language = language

    def escuchar(self):
        with sr.Microphone() as source:
            print("🎤 Ajustando al ruido ambiental...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
            print("👂 Estoy escuchando, habla ahora...")

            try:
                # Tiempo máximo de espera sin hablar: 5 segundos
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                texto = self.recognizer.recognize_google(audio, language=self.language)
                return texto.strip().lower()

            except sr.WaitTimeoutError:
                print("⏱️ No se detectó ninguna voz a tiempo.")
            except sr.UnknownValueError:
                print("🤷 No entendí lo que dijiste.")
            except sr.RequestError:
                print("❌ Error al conectar con el servicio de reconocimiento.")
            except Exception as e:
                print(f"⚠️ Error inesperado: {e}")
            
            return ""
