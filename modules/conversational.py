import torch
import random
import re
from datetime import datetime
from config import PERSONALIDAD 
from transformers import (
    BlenderbotTokenizer,
    BlenderbotForConditionalGeneration,
    MarianMTModel,
    MarianTokenizer
)

class ComandoDetector:
    def __init__(self):
        # 1) Sinónimos de verbos
        self.verbos = {
            "traducir_es_en":  ["traduce al inglés", "traduce inglés", "a inglés"],
            "traducir_en_es":  ["traduce al español", "traduce español", "a español"],
            "youtube_play_index": ["reproduce", "toca", "pon", "play"],
            "youtube_search":  ["busca en youtube", "buscar en youtube", "haz una búsqueda en youtube", "encuentra en youtube"],
            "youtube_open":    ["abre youtube", "ve a youtube", "ir a youtube"],
            "spotify":         ["pon", "toca", "play", "reproduce", "escucha", "dale"],
            "calculo":         ["calcula", "calcular", "resuelve", "dame resultado de", "qué es"],
            "buscar":          ["busca", "buscar", "encuentra", "investiga", "qué es", "infórmame sobre"],
            "recomendar":      ["recomiéndame", "dame recomendaciones de", "qué me sugieres de", "sugiere"],
            "agendar":         ["agenda", "agendar", "programa", "añade a mi agenda", "anota", "recuerda"],
            "consultar_agenda":["qué tengo agendado", "muéstrame mi agenda", "mostrar agenda", "ver eventos"],
            "clima":           ["clima", "tiempo", "qué tiempo hace", "estado del tiempo"],
            "hora":            ["qué hora es", "dime la hora", "hora exacta"],
            "temporizador":    ["temporizador", "pon temporizador de", "cuenta regresiva de", "timer de"],
            "alarma":          ["pon alarma a las", "despiértame a las", "alarma para las"],
            "definir":         ["define", "qué significa", "definición de"],
            "imagen_search":   ["busca imagen de", "imagen de", "fotos de", "haz una imagen de"],
            "resumir":         ["resume", "haz un resumen de", "resume esto:", "resume el texto"],
            "chiste":          ["cuéntame un chiste", "broma", "hazme reír", "dime un chiste"],
            "abrir_sitio":     ["abre sitio", "ve a", "navega a", "ir a página"],
            "noticias":        ["dame noticias de", "últimas noticias", "qué hay de nuevo en"],
        }

        # 2) Objetos (para comandos que lo requieran)
        self.target = {
            "youtube_open":    ["youtube"],
            "youtube_search":  ["youtube"],
            "spotify":         ["spotify"],
            "youtube_play_index": ["video", "número", "el video"],
        }

        # 3) Construcción de patrones con prioridad (más específicos primero)
        # Ordenamos para que traducción se detecte antes que busquedas generales
        self.orden = [
            "traducir_es_en",
            "traducir_en_es",
            "youtube_play_index",
            "youtube_search",
            "youtube_open",
            "spotify",
            "calculo",
            "buscar",
            "recomendar",
            "agendar",
            "consultar_agenda",
            "clima",
            "hora",
            "temporizador",
            "alarma",
            "definir",
            "imagen_search",
            "resumir",
            "chiste",
            "abrir_sitio",
            "noticias"
        ]

        self.patrones = []
        for tipo in self.orden:
            verbs = self.verbos.get(tipo, [])
            verb_group = r"(?:{})".format("|".join([re.escape(v) for v in verbs if v]))
            tgt_group = ""
            if tipo in self.target:
                tgt_group = r"(?:\s+(?:{}))?".format("|".join(self.target[tipo]))

            if tipo == "youtube_play_index":
                # Comando con índice exacto
                pattern = rf"^\s*{verb_group}{tgt_group}\s+(\d+)\s*$"
                grupo = 1
            elif tipo in ("youtube_open", "hora", "consultar_agenda", "chiste"):
                # Comandos sin argumento
                pattern = rf"^\s*{verb_group}{tgt_group}\s*$"
                grupo = None
            else:
                # Comandos con argumento libre
                pattern = rf"^\s*{verb_group}{tgt_group}\s+(.+?)\s*$"
                grupo = 1

            self.patrones.append(
                (tipo, re.compile(pattern, re.IGNORECASE), grupo)
            )

    def detectar(self, entrada: str):
        entrada = entrada.lower().strip()

        for tipo, regex, grupo in self.patrones:
            match = regex.match(entrada)
            if match:
                if grupo is not None:
                    return tipo, match.group(grupo).strip()
                else:
                    return tipo, None
        return None, None

    def detectar(self, entrada: str):
        for tipo, regex, grupo in self.patrones:
            match = regex.match(entrada)
            if match:
                if grupo is not None:
                    return tipo, match.group(grupo)
                else:
                    return tipo, None
        return None, None

class ConversationalModule:
    def __init__(
        self, model_dir, memory_module=None, calculator=None, youtube=None,
        internet_search=None, browser=None, spotify=None,
        device=None, max_input_length=1500, detector=None,agenda= None,
        clima = None,
    ):

        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.memory = memory_module
        self.calculator = calculator
        self.internet_search = internet_search
        self.youtube = youtube
        self.browser = browser
        self.spotify = spotify
        self.max_input_length = max_input_length
        self.detector = detector or ComandoDetector()
        self.es_en_dir = f"{model_dir}/models--Helsinki-NLP--opus-mt-es-en".replace("\\", "/")
        self.en_es_dir = f"{model_dir}/models--Helsinki-NLP--opus-mt-en-es".replace("\\", "/")
        self.blender_dir = f"{model_dir}/models--facebook--blenderbot-400M-distill".replace("\\", "/")
        self.clima = clima
        self.agenda = agenda
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

    def detectar_comando(self, texto: str):
        # Limpiar texto de puntuaciones comunes y espacios extras
        texto = re.sub(r"[¿?¡!]+", "", texto).strip().lower()
        texto = re.sub(r"\s+", " ", texto)

        # Iterar sobre los patrones definidos
        for tipo, patron, grupo in self.detector.patrones:
            m = patron.match(texto)
            if m:
                arg = m.group(grupo).strip() if grupo and m.group(grupo) else None
                # Si se esperaba un argumento pero está vacío, retornar None
                if grupo and not arg:
                    return tipo, None
                return tipo, arg

        return None, None

    def ejecutar_comando(self, tipo, argumento):
        # Cálculo
        if tipo == "calculo" and self.calculator:
            resultado = self.calculator.calcular(argumento)
            return f"Ya lo calculé... {resultado}"

        # YouTube: búsqueda
        elif tipo == "youtube_search" and self.youtube:
            resultados, mensaje = self.youtube.buscar_youtube(argumento)
            if self.memory and resultados:
                self.memory.memoria["ultimos_resultados_youtube"] = resultados
            return mensaje

        # YouTube: reproducir por índice
        elif tipo == "youtube_play_index" and self.youtube:
            if not self.memory or "ultimos_resultados_youtube" not in self.memory.memoria:
                return "Primero dime qué quieres buscar en YouTube."
            try:
                idx = int(argumento) - 1
                resultados = self.memory.memoria["ultimos_resultados_youtube"]
                respuesta = self.youtube.reproducir_video_por_indice(idx, resultados)
                del self.memory.memoria["ultimos_resultados_youtube"]
                return respuesta
            except (ValueError, IndexError):
                return "Número inválido. Intenta con otro."
            except Exception as e:
                return f"Error reproduciendo video: {e}"

        # YouTube: abrir
        elif tipo == "youtube_open" and self.youtube:
            return self.youtube.abrir_youtube()

        # Búsqueda web
        elif tipo == "buscar" and self.internet_search:
            resultado = self.internet_search.buscar_internet(argumento)
            return f"Esto fue lo que encontré: {resultado}"

        # Spotify
        elif tipo == "spotify" and self.spotify:
            query = (argumento or "").strip()
            if not query:
                return "¿Qué quieres reproducir en Spotify?"

            # Inferir tipo básico
            if any(p in query.lower() for p in ["playlist", "lista"]):
                kind = "playlist"
            elif any(p in query.lower() for p in ["álbum", "album"]):
                kind = "album"
            elif any(p in query.lower() for p in ["artista", "banda"]):
                kind = "artista"
            else:
                # Si no se infiere, guardar el pendiente y preguntar
                if self.memory and hasattr(self.memory, "memoria"):
                    self.memory.memoria["spotify_pendiente"] = query
                return "¿Canción, álbum, playlist o artista?"

            # Ejecutar reproducción y capturar respuesta
            respuesta = self.spotify.reproducir(kind, query)
            return respuesta or f"Intenté reproducir {kind}, pero ocurrió un problema."

        # Traducción
        elif tipo == "traducir_es_en":
            return f"En inglés sería: {self.traducir_es_a_en(argumento)}"
        elif tipo == "traducir_en_es":
            return f"Eso en español sería: {self.traducir_en_a_es(argumento)}"

        # Recomendaciones
        elif tipo == "recomendar" and self.recomendador:
            recs = self.recomendador.obtener(argumento)
            return f"Sugerencias: {recs}"

        # Agenda
        elif tipo == "agendar" and self.agenda:
            self.agenda.agregar_evento(argumento)
            return "Evento agregado a tu agenda."
        elif tipo == "consultar_agenda" and self.agenda:
            eventos = self.agenda.consultar_eventos()
            return eventos or "Tu agenda está vacía."

        # Hora
        elif tipo == "hora":
            ahora = datetime.now().strftime("%H:%M")
            return f"Son las {ahora}."

        # Clima
        elif tipo == "clima" and self.clima:
            return f"El clima actual es: {self.clima.obtener_clima()}"

        # Para chistes y demás usa BlenderBot (no manejar aquí)
        # Fallback
        mensajes_fallback = [
            "No puedo hacer eso ahora.",
            "Intenta con algo más útil… tal vez.",
            "No estoy programada para eso… aún.",
            "¿Y ahora qué quieres? Eso no puedo hacerlo.",
        ]
        return random.choice(mensajes_fallback)

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
        # 1) Detectar comando explícito
        tipo, argumento = self.detectar_comando(entrada_usuario)
        if tipo:
            respuesta = self.ejecutar_comando(tipo, argumento)
            # Registrar en memoria
            if self.memory:
                self.memory.registrar_comando(tipo)
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", respuesta)
            # Solo aquí añadimos el extra
            return self.incluir_memoria_en_respuesta(respuesta, extra_comando=True)

        # 2) Respuesta rápida (saludos, despedidas, etc.)
        rapida = self._respuesta_basica(entrada_usuario)
        if rapida:
            if self.memory:
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", rapida)
            return self.incluir_memoria_en_respuesta(rapida, extra_comando=False)

        # 3) Spotify pendiente
        pendiente = None
        if self.memory and hasattr(self.memory, 'memoria'):
            pendiente = self.memory.memoria.get("spotify_pendiente")
        if pendiente:
            tipo_resp = entrada_usuario.lower().strip()
            if tipo_resp in ["canción", "cancion", "álbum", "album", "playlist", "artista"]:
                self.memory.memoria.pop("spotify_pendiente", None)
                tipo_sp = "cancion" if "cancion" in tipo_resp else tipo_resp
                self.spotify.reproducir(tipo_sp, pendiente)
                texto = f"Perfecto, reproduciendo {tipo_sp} '{pendiente}' 🎶"
                return self.incluir_memoria_en_respuesta(texto, extra_comando=True)
            else:
                return "Solo dime si es una canción, álbum, playlist o artista."

        # 4) Sin modelo disponible
        if not self.blender_model or not self.blender_tokenizer:
            return "No estoy disponible ahora."

        # 5) Llamada a BlenderBot con historial para coherencia
        try:
            nombre = (self.memory.get_dueno() if self.memory else None) or "usuario"
            ctx = self._construir_contexto_con_historial(nombre, entrada_usuario)

            # Traducir → generar → traducir
            ctx_en = self.traducir_es_a_en(ctx)
            inputs = self.blender_tokenizer([ctx_en], return_tensors="pt", truncation=True).to(self.device)
            outputs = self.blender_model.generate(**inputs, max_length=150)
            resp_en = self.blender_tokenizer.decode(outputs[0], skip_special_tokens=True)
            resp_es = self.traducir_en_a_es(resp_en)

            if self.memory:
                self.memory.add_to_history("usuario", entrada_usuario)
                self.memory.add_to_history("rin", resp_es)
            return self.incluir_memoria_en_respuesta(resp_es, extra_comando=False)

        except Exception as e:
            return f"No pude generar respuesta ahora... grrr. ({e})"

    def incluir_memoria_en_respuesta(self, respuesta, extra_comando=False):
        # Solo añadimos frase extra en comandos explícitos
        if not extra_comando or not self.memory or not hasattr(self.memory, 'memoria'):
            return respuesta

        nombre = self.memory.memoria.get("nombre")
        if not nombre:
            return respuesta

        extras = [
            f"¿Algo más, {nombre}? No me dejes aburrida.",
            f"Oye {nombre}, ¿me vas a dar trabajo o qué?",
            f"Bueno {nombre}, ¿qué quieres ahora?",
            f"¡Hmph! Ya cumplí, {nombre}.",
        ]
        return f"{respuesta} {random.choice(extras)}"

    def _construir_contexto_con_historial(self, nombre, entrada_usuario):
        # Incluye personalidad y últimos 4 turnos para coherencia
        contexto = f"{PERSONALIDAD}\n\n"
        if self.memory:
            hist = self.memory.get_history(turnos=4)
            for rol, texto, _ in hist:
                quien = "Rin" if rol.lower() == "rin" else nombre
                contexto += f"{quien}: {texto}\n"
        contexto += f"{nombre}: {entrada_usuario}\nRin:"
        return contexto
