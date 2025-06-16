import os
# Obtener la ruta base (donde está este archivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONALIDAD = (
    "You are Rin, a virtual assistant with a playful personality. "
    "Your replies should be cheeky and a bit bossy, but still caring. "
)
EDGE_DRIVER_PATH = os.path.join(BASE_DIR, "modules", "msedgedriver.exe")
PIPER_PATH = os.path.join(BASE_DIR, "piper", "piper.exe")
MODEL_PATH = os.path.join(BASE_DIR, "piper", "Piper-TTS-Laura", "es_MX-laura-high.onnx")
VOICE_CONFIG_PATH = os.path.join(BASE_DIR, "piper", "Piper-TTS-Laura", "es_MX-laura-high.onnx.json")
AUDIO_DIR = os.path.join(BASE_DIR, "audios")
MEMORIA_PATH = os.path.join(BASE_DIR, "memoria_rin.json")
MAX_HISTORY = 5
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
API_KEY = ""
#change the api keys whit your personal clients or api keys