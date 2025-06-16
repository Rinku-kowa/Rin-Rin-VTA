# modules/live2d_sync.py
import asyncio
import websockets
import threading


class Live2DSyncServer:
    def __init__(self, host='localhost', port=6969):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        print(f"Cliente conectado: {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"Mensaje recibido: {message}")
                # Aquí podrías procesar mensajes o reenviarlos a otros clientes
                # Por ejemplo, reenviar a todos menos al emisor:
                await self.broadcast(message, sender=websocket)
        except websockets.ConnectionClosed:
            print(f"Cliente desconectado: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, message, sender=None):
        # Reenvía mensaje a todos los clientes menos al que envió
        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients if client != sender])

    def iniciar(self):
        print(f"Servidor Live2D Sync iniciado en ws://{self.host}:{self.port}")
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(self.handler, self.host, self.port)
        )
        asyncio.get_event_loop().run_forever()
        
class Live2DClient:
    def __init__(self, uri="ws://localhost:6969"):
        self.uri = uri
        self.loop = asyncio.new_event_loop()
        self.ws = None
        self.connected = threading.Event()
        threading.Thread(target=self._start_loop, daemon=True).start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        try:
            self.ws = await websockets.connect(self.uri)
            self.connected.set()
            print("✅ Cliente Live2D conectado al servidor")
        except Exception as e:
            print(f"❌ Error al conectar al servidor Live2D: {e}")

    def notificar_inicio_habla(self):
        if self.connected.is_set():
            asyncio.run_coroutine_threadsafe(self.ws.send("start"), self.loop)

    def notificar_fin_habla(self):
        if self.connected.is_set():
            asyncio.run_coroutine_threadsafe(self.ws.send("stop"), self.loop)

# Instancia global
cliente_live2d = Live2DClient()

# Funciones que puede usar el TTS
def notificar_inicio_habla():
    cliente_live2d.notificar_inicio_habla()

def notificar_fin_habla():
    cliente_live2d.notificar_fin_habla()
