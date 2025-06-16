import pyttsx3

class TextToSpeechModule:
    def __init__(self):
        self.engine = pyttsx3.init()

        # Ajustar velocidad y volumen
        self.engine.setProperty('rate', 150)    # un poco más lenta para claridad
        self.engine.setProperty('volume', 1.0)  # al máximo sin distorsión

        # Selección de voz en español femenino
        voices = self.engine.getProperty('voices')
        selected = None
        for v in voices:
            name = v.name.lower()
            lang = getattr(v, 'languages', [])
            # buscar “spanish” o código “es_”
            if 'spanish' in name or any('es_' in str(l).lower() for l in lang):
                if 'female' in name or 'voz' in name or 'sabina' in name or 'helena' in name:
                    selected = v.id
                    break
                elif not selected:
                    selected = v.id  # reserva primera española si no hay indicativo
        if selected:
            self.engine.setProperty('voice', selected)
        else:
            print("⚠️ No encontré voz en español; usando voz por defecto.")

    def speak(self, text: str):
        """Sintetiza y bloquea hasta completar la frase."""
        self.engine.say(text)
        self.engine.runAndWait()
