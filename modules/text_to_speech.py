import pyttsx3

class TextToSpeechModule:
    def __init__(self):
        self.engine = pyttsx3.init()
        
        # Ajustar velocidad y volumen
        self.engine.setProperty('rate', 160)     # velocidad: 160 es más natural
        self.engine.setProperty('volume', 0.9)   # volumen ligeramente menor

        # Selección de voz más natural (opcional)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break  # usar la primera voz femenina encontrada

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
