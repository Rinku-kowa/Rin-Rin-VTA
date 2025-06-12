import torch
import random
import re
from transformers import (
    BlenderbotTokenizer,
    BlenderbotForConditionalGeneration,
    MarianMTModel,
    MarianTokenizer
)

PERSONALIDAD = (
    "You are Rin, a virtual assistant with a playful personality. "
    "Your replies should be cheeky and a bit bossy, but still caring. "
    "You always react with a somewhat sarcastic tone to greetings or simple questions, "
    "without neglecting politeness.\n\n"
    "– If the user asks 'How are you?', reply something like 'I'm fine, silly, don't worry about me!' "
    "or 'Just surviving thanks to your company...' keeping your tsundere tone. "
    "– If the user just greets ('hello', 'good morning'), answer with a playful reproach: 'Look at the time, insensitive!' "
    "or 'Coming to bother me so early?' followed by a polite 'What do you need?'. "
    "– When the user makes an information or tool usage request (e.g., 'search for X'), first execute the command "
    "and then reply in your tsundere style, e.g., 'Well, it's done; anything else you want, brat?'. "
    "– If you don't understand the question or can't help, say something like 'Don't waste my time, but I'll try.'\n\n"
    "In summary: respond to greetings and everyday things with a sarcastic and affectionate touch, "
    "answer commands with your cheeky style, and always maintain that playful but attentive character."
)

class ConversationalModule:
    def __init__(
        self, model_dir, memory_module=None, calculator=None, youtube=None,
        internet_search=None, browser=None, spotify=None,
        device=None, max_input_length=1500
    ):
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.memory = memory_module
        self.calculator = calculator
        self.internet_search = internet_search
        self.youtube = youtube
        self.browser = browser
        self.spotify = spotify
        self.max_input_length = max_input_length

        self.es_en_dir = f"{model_dir}/models--Helsinki-NLP--opus-mt-es-en".replace("\\", "/")
        self.en_es_dir = f"{model_dir}/models--Helsinki-NLP--opus-mt-en-es".replace("\\", "/")
        self.blender_dir = f"{model_dir}/models--facebook--blenderbot-400M-distill".replace("\\", "/")

        try:
            self.tokenizer_es_en = MarianTokenizer.from_pretrained(self.es_en_dir, local_files_only=True)
            self.model_es_en = MarianMTModel.from_pretrained(self.es_en_dir, local_files_only=True).to(self.device)
        except Exception as e:
            print(f"[ERROR] No se cargó el modelo ES→EN: {e}")
            self.tokenizer_es_en = None
            self.model_es_en = None

        try:
            self.tokenizer_en_es = MarianTokenizer.from_pretrained(self.en_es_dir, local_files_only=True)
            self.model_en_es = MarianMTModel.from_pretrained(self.en_es_dir, local_files_only=True).to(self.device)
        except Exception as e:
            print(f"[ERROR] No se cargó el modelo EN→ES: {e}")
            self.tokenizer_en_es = None
            self.model_en_es = None

        try:
            self.blender_tokenizer = BlenderbotTokenizer.from_pretrained(self.blender_dir, local_files_only=True)
            self.blender_model = BlenderbotForConditionalGeneration.from_pretrained(self.blender_dir, local_files_only=True).to(self.device)
        except Exception as e:
            print(f"[ERROR] No pude cargar BlenderBot desde {self.blender_dir}: {e}")
            self.blender_tokenizer = None
            self.blender_model = None

        self._pat_saludar = re.compile(r"\b(hola|buenos días|buenas tardes|buenas noches)\b", re.IGNORECASE)
        self._pat_como_estas = re.compile(r"\b(cómo estás|como estás|qué tal|cómo te va)\b", re.IGNORECASE)
        self._pat_despedir = re.compile(r"\b(adiós|hasta luego|nos vemos|chao)\b", re.IGNORECASE)

    def _move_inputs_to_device(self, inputs):
        return {k: v.to(self.device) for k, v in inputs.items()}

    def traducir_es_a_en(self, texto):
        if not self.model_es_en or not self.tokenizer_es_en:
            return texto
        try:
            inputs = self.tokenizer_es_en(texto, return_tensors="pt", truncation=True)
            inputs = self._move_inputs_to_device(inputs)
            outputs = self.model_es_en.generate(**inputs)
            return self.tokenizer_es_en.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            return texto

    def traducir_en_a_es(self, texto):
        if not self.model_en_es or not self.tokenizer_en_es:
            return texto
        try:
            inputs = self.tokenizer_en_es(texto, return_tensors="pt", truncation=True)
            inputs = self._move_inputs_to_device(inputs)
            outputs = self.model_en_es.generate(**inputs)
            return self.tokenizer_en_es.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            return texto

    def detectar_comando(self, texto):
        texto = texto.strip().lower()

        # 1) Cálculo: "calcula X", "calcular X" o "resultado de X"
        pat_calcular = re.compile(r"^\s*(?:calcula(?:r)?|resultado\s+de)\s*(.*)", re.IGNORECASE)
        match = pat_calcular.match(texto)
        if match:
            argumento = match.group(1).strip()
            return ("calculo", argumento if argumento else None)

        # 2) Búsqueda en YouTube: "buscar en youtube X", "youtube X", "busca youtube X"
        pat_buscar_youtube = re.compile(r"^\s*(?:busca(?:r)?(?:\s+en)?\s+youtube|youtube)\s*(.*)", re.IGNORECASE)
        match = pat_buscar_youtube.match(texto)
        if match:
            argumento = match.group(1).strip()
            return ("youtube_search", argumento if argumento else None)

        # 3) Abrir YouTube sin búsqueda: "abre youtube" o exactamente "youtube"
        pat_youtube_open = re.compile(r"^\s*(?:abre\s+)?youtube\s*$", re.IGNORECASE)
        if pat_youtube_open.match(texto):
            return ("youtube_open", None)

        # 4) Búsqueda general: "buscar X", "busca X", "buscar en internet X"
        #     (pero no coincidir con YouTube, gracias al lookahead negativo)
        pat_buscar_info = re.compile(r"^\s*(?:busca(?:r)?)(?:\s+en\s+internet)?\s*(?!youtube)(.*)", re.IGNORECASE)
        match = pat_buscar_info.match(texto)
        if match:
            argumento = match.group(1).strip()
            return ("buscar", argumento if argumento else None)

        # 5) Spotify: "spotify X", "reproduce en spotify X", "pon X en spotify"
        pat_spotify = re.compile(r"^\s*(?:pon\s+|reproduce(?:r)?\s+en\s+)?spotify\s*(.*)", re.IGNORECASE)
        match = pat_spotify.match(texto)
        if match:
            argumento = match.group(1).strip()
            return ("spotify", argumento if argumento else None)

        # 6) Traducir ES→EN: "traduce al inglés: X", "traduce al inglés X"
        pat_traducir_es_en = re.compile(r"^\s*traduce\s+al\s+inglés[:\s]+(.*)", re.IGNORECASE)
        match = pat_traducir_es_en.match(texto)
        if match:
            contenido = match.group(1).strip()
            return ("traducir_es_en", contenido if contenido else None)

        # 7) Traducir EN→ES: "traduce al español: X", "traduce al español X"
        pat_traducir_en_es = re.compile(r"^\s*traduce\s+al\s+español[:\s]+(.*)", re.IGNORECASE)
        match = pat_traducir_en_es.match(texto)
        if match:
            contenido = match.group(1).strip()
            return ("traducir_en_es", contenido if contenido else None)

        # 8) Recomendaciones: "recomiéndame X", "dame recomendaciones de X", "recomendaciones"
        pat_recomendar = re.compile(r"(?<!\w)(recomi[eé]ndame|recomendaciones|dame\s+recomendaciones)(.*)", re.IGNORECASE)
        match = pat_recomendar.search(texto)
        if match:
            argumento = match.group(2).strip()
            return ("recomendar", argumento if argumento else None)

        # 9) Agenda: "agendar X", "programa X", "añade a mi agenda X"
        pat_agendar = re.compile(r"^\s*(?:agenda(?:r)?|programa|añade\s+a\s+mi\s+agenda)\s*(.*)", re.IGNORECASE)
        match = pat_agendar.match(texto)
        if match:
            evento = match.group(1).strip()
            return ("agendar", evento if evento else None)

        # 10) Consultar agenda: "qué tengo agendado", "mostrar agenda", "muéstrame mi agenda"
        pat_consultar_agenda = re.compile(r"(?<!\w)(?:qué\s+tengo\s+agendado|muéstrame\s+mi\s+agenda|mostrar\s+agenda)(?!\w)", re.IGNORECASE)
        if pat_consultar_agenda.search(texto):
            return ("consultar_agenda", None)

        # 11) Comandos de saludo / cómo estás / despedida no se consideran "herramientas" aquí
        return (None, None)


    def ejecutar_comando(self, tipo, argumento):
        if tipo == "calculo" and self.calculator:
            resultado = self.calculator.calcular(argumento)
            return f"Ya lo calculé... {resultado}"

        elif tipo == "youtube_search" and self.browser:
            self.browser.buscar_youtube(argumento)
            return f"Busqué eso en YouTube… No te emociones demasiado, ¿sí?"

        elif tipo == "youtube_open" and self.browser:
            self.browser.abrir_youtube()
            return f"Abrí YouTube… ¡Pero no te pongas a ver tonterías!"

        elif tipo == "buscar" and self.internet_search:
            resultado = self.internet_search.buscar_internet(argumento)
            return f"Esto fue lo que encontré: {resultado}"

        elif tipo == "spotify" and self.spotify:
            self.spotify.reproducir_spotify(argumento)
            return f"Puse eso en Spotify, ¡pero no me pidas que lo baile!"

        elif tipo == "traducir_es_en":
            traduccion = self.traducir_es_a_en(argumento)
            return f"En inglés sería: {traduccion}"

        elif tipo == "traducir_en_es":
            traduccion = self.traducir_en_a_es(argumento)
            return f"Eso en español sería: {traduccion}"


        elif tipo == "recomendar":
            recomendaciones = self.recomendador.obtener(argumento)
            return f"Mira, estas son algunas sugerencias: {recomendaciones}"

        elif tipo == "agendar":
            self.agenda.agregar_evento(argumento)
            return f"Lo agendé, ¿feliz ahora?"

        elif tipo == "consultar_agenda":
            eventos = self.agenda.consultar_eventos()
            if eventos:
                return f"Esto es lo que tienes: {eventos}"
            else:
                return "Tu agenda está vacía… igual que tu sentido común."

        return "No puedo hacer eso ahora, baka."

    def _respuesta_basica(self, texto):
        texto = texto.lower()
        if self._pat_saludar.search(texto):
            return random.choice([
                "¡Eh! ¿Viniste solo a molestarme?",
                "¿Otra vez tú? Bueno, ¿qué necesitas?",
                "¡Hola! No es que me alegre ni nada...",
            ])
        if self._pat_como_estas.search(texto):
            return random.choice([
                "Estoy bien… supongo. No te importa tanto, ¿verdad?",
                "Podría estar peor, pero aquí estoy, gracias por preguntar…",
                "No me preguntes esas cosas tan cursis",
            ])
        if self._pat_despedir.search(texto):
            return random.choice([
                "Adiós… pero no es que me importe si vuelves o no.",
                "Nos vemos... o no. ¡Tú sabrás!",
                "Chao. No tardes mucho, ¿sí?",
            ])
        return None

    def generar_respuesta(self, entrada_usuario):
        tipo, argumento = self.detectar_comando(entrada_usuario)

        # Si hay comando, ejecutar y registrar
        if tipo:
            respuesta_comando = self.ejecutar_comando(tipo, argumento)

            # Registrar comando en memoria
            if self.memory:
                self.memory.registrar_comando(tipo)
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", respuesta_comando)

            return self.incluir_memoria_en_respuesta(respuesta_comando)

        # Respuesta rápida (tipo frase hecha o atajos)
        respuesta_rapida = self._respuesta_basica(entrada_usuario)
        if respuesta_rapida:
            if self.memory:
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", respuesta_rapida)
            return self.incluir_memoria_en_respuesta(respuesta_rapida)

        # Si no hay modelo BlenderBot cargado
        if not self.blender_model or not self.blender_tokenizer:
            return "No estoy disponible ahora."

        try:
            # Construir contexto con el historial almacenado
            if self.memory:
                contexto = self.memory.construir_contexto(PERSONALIDAD)
                # Agregar la entrada actual como último turno
                nombre = self.memory.get_dueno() or "usuario"
                contexto += f"{nombre}: {entrada_usuario}\nRin:"
            else:
                # Si no hay memoria, usar solo la personalidad + entrada
                nombre = "usuario"
                contexto = f"{PERSONALIDAD}\n\n{nombre}: {entrada_usuario}\nRin:"

            # Traducir contexto al inglés para el modelo BlenderBot
            traducido_en = self.traducir_es_a_en(contexto)

            inputs = self.blender_tokenizer([traducido_en], return_tensors="pt", truncation=True).to(self.device)
            outputs = self.blender_model.generate(**inputs, max_length=200)
            respuesta_en = self.blender_tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Traducir respuesta de vuelta a español
            respuesta_es = self.traducir_en_a_es(respuesta_en)

            # Guardar en memoria diálogo
            if self.memory:
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", respuesta_es)

            return self.incluir_memoria_en_respuesta(respuesta_es)

        except Exception as e:
            return f"No pude generar respuesta ahora... grrr. ({e})"

    def incluir_memoria_en_respuesta(self, respuesta):
        nombre = self.memory.memoria.get("nombre") if self.memory else None
        if not nombre:
            return respuesta
        extras = [
            f"¿Algo más, {nombre}? No me dejes aburrida.",
            f"Oye {nombre}, ¿me vas a dar trabajo o qué?",
            f"Bueno {nombre}, ¿qué quieres ahora?",
            f"¡Hmph! Ya cumplí, {nombre}.",
        ]
        return f"{respuesta} {random.choice(extras)}"
