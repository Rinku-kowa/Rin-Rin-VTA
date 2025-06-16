import speech_recognition as sr
import threading

class SpeechToTextModule:
    def __init__(
        self,
        language='es-ES',               # alias para primary_lang
        secondary_lang='en-US',
        mic_index=None
    ):
        """
        Inicializa el módulo de STT con idioma principal y secundario.
        Parámetros:
        - language: código de idioma principal para reconocimiento (p.ej. 'es-ES').
        - secondary_lang: idioma fallback (p.ej. 'en-US').
        - mic_index: índice del micrófono a usar (opcional).
        """
        self.recognizer = sr.Recognizer()
        self.primary_lang = language
        self.secondary_lang = secondary_lang
        self.mic_index = mic_index
        try:
            self.mic_list = sr.Microphone.list_microphone_names()
            print("🎤 Micrófonos disponibles:")
            for i, name in enumerate(self.mic_list):
                print(f"  [{i}] {name}")
        except Exception as e:
            print(f"⚠️ No se pudo listar micrófonos: {e}")

    @staticmethod
    def limpiar_errores_comunes(texto: str) -> str:
        reemplazos = {
            "you tube": "youtube",
            "play list": "playlist",
            "de the": "de",
        }
        for error, correccion in reemplazos.items():
            texto = texto.replace(error, correccion)
        return texto

    def escuchar(self, callback=None, timeout=5, phrase_time_limit=8):
        """Escucha usando dos idiomas si es necesario, y ejecuta callback(texto)"""
        def stt_thread():
            mic_args = {}
            if hasattr(self, 'mic_list') and self.mic_index is not None:
                if 0 <= self.mic_index < len(self.mic_list):
                    mic_args['device_index'] = self.mic_index

            try:
                with sr.Microphone(**mic_args) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )

                    # Intento con primary y luego secondary
                    for lang in (self.primary_lang, self.secondary_lang):
                        try:
                            texto = self.recognizer.recognize_google(
                                audio,
                                language=lang
                            )
                            texto = texto.strip().lower()
                            texto = self.limpiar_errores_comunes(texto)
                            print(f"🗣️ Reconocido ({lang}): {texto}")
                            if callback:
                                callback(texto)
                            return
                        except sr.UnknownValueError:
                            print(f"🤷 No entendí en {lang}.")
                        except sr.RequestError as e:
                            print(f"❌ Error de red en STT ({lang}): {e}")
                            break

                    # Si no se entendió en ninguno
                    if callback:
                        callback("")

            except sr.WaitTimeoutError:
                print("⏱️ Timeout: no se detectó voz.")
                if callback:
                    callback("")
            except Exception as e:
                print(f"⚠️ Error inesperado en STT: {e}")
                if callback:
                    callback("")

        threading.Thread(target=stt_thread, daemon=True).start()