import json
import os
import random
import time
from collections import Counter

class MemoryModule:
    def __init__(self, file_path="memoria.json", max_history=5):
        self.file_path = file_path
        self.max_history = max_history
        self.memoria = self._cargar_memoria()

        # Inicializar estructuras si no existen
        self.memoria.setdefault("dialog_history", [])
        self.memoria.setdefault("gustos", [])
        self.memoria.setdefault("favoritos", [])
        self.memoria.setdefault("recomendaciones", [])
        self.memoria.setdefault("comandos_usados", {})

    def _cargar_memoria(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        else:
            return {}

    def _guardar_memoria(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error guardando memoria: {e}")

    # --- Dueño ---
    def get_dueno(self):
        return self.memoria.get("dueno", None)

    def set_dueno(self, nombre):
        self.memoria["dueno"] = nombre
        self._guardar_memoria()

    def ask_for_dueno(self):
        if not self.get_dueno():
            opciones = [
                "hola soy rin, ¿cómo te llamas?",
                "hola soy rin, ¿cuál es tu nombre?",
                "hola soy rin, no sé tu nombre; dime qué nombre me debería molestar a mí.",
                "hola soy rin, dime tu nombre de una vez.",
                "hola soy rin, ¿quién eres tú? Díme tu nombre."
            ]
            return random.choice(opciones)
        return None

    # --- Historial ---
    def add_to_history(self, rol, texto):
        entrada = [rol, texto, time.time()]
        self.memoria["dialog_history"].append(entrada)
        max_msgs = self.max_history * 2
        if len(self.memoria["dialog_history"]) > max_msgs:
            self.memoria["dialog_history"] = self.memoria["dialog_history"][-max_msgs:]
        self._guardar_memoria()

    def get_history(self):
        return self.memoria.get("dialog_history", [])

    def construir_contexto(self, personalidad):
        contexto = personalidad + "\n\n"
        for entrada in self.get_history():
            rol, texto = entrada[0], entrada[1]
            contexto += f"{rol}: {texto}\n"
        return contexto

    # --- Gustos y favoritos ---
    def agregar_gusto(self, categoria):
        if categoria:
            self.memoria["gustos"].append(categoria)
            self.memoria["gustos"] = list(set(self.memoria["gustos"]))
            self._guardar_memoria()

    def agregar_favorito(self, item):
        if item:
            self.memoria["favoritos"].append(item)
            self.memoria["favoritos"] = list(set(self.memoria["favoritos"]))
            self._guardar_memoria()

    def get_favoritos(self):
        return self.memoria.get("favoritos", [])

    def get_gustos(self):
        return self.memoria.get("gustos", [])

    def sugerir_recomendacion(self):
        gustos = self.get_gustos()
        if gustos:
            conteo = Counter(gustos)
            for gusto, _ in conteo.most_common():
                sugerencia = f"Tal vez te guste algo más de '{gusto}'. ¿Quieres que te recomiende algo?"
                if sugerencia not in self.memoria["recomendaciones"]:
                    self.memoria["recomendaciones"].append(sugerencia)
                    self._guardar_memoria()
                    return sugerencia
            return "Creo que ya te recomendé todo lo que podía... ¡por ahora!"
        else:
            return "Aún no sé bien qué te gusta. Háblame más de tus gustos."

    def get_recomendaciones(self):
        return self.memoria.get("recomendaciones", [])

    # --- Comandos usados ---
    def registrar_comando(self, comando):
        if comando:
            comandos = self.memoria.get("comandos_usados", {})
            comandos[comando] = comandos.get(comando, 0) + 1
            self.memoria["comandos_usados"] = comandos
            self._guardar_memoria()

    def get_comandos_frecuentes(self, top_n=3):
        comandos = self.memoria.get("comandos_usados", {})
        return sorted(comandos.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # --- Reset general (útil para pruebas o reinicio eliminar cuando se acaben las pruebas) ---
    def reset_memoria(self):
        self.memoria = {
            "dialog_history": [],
            "gustos": [],
            "favoritos": [],
            "recomendaciones": [],
            "comandos_usados": {},
        }
        self._guardar_memoria()
