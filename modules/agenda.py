from datetime import datetime

class AgendaModule:
    def __init__(self):
        self.eventos = []

    def agregar_evento(self, descripcion: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.eventos.append(f"{timestamp}: {descripcion}")

    def consultar_eventos(self):
        return "\n".join(self.eventos) if self.eventos else ""
