import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

class SpotifyModule:
    def __init__(self):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri="http://127.0.0.1:8888/callback",
                scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
            ))
            print("🎵 Spotify autenticado correctamente.")
        except Exception as e:
            print(f"❌ Error al autenticar Spotify: {e}")
            self.sp = None

    def _get_active_device(self):
        devices = self.sp.devices()
        for device in devices.get("devices", []):
            if device.get("is_active"):
                return device["id"]
        if devices.get("devices"):
            return devices["devices"][0]["id"]
        return None

    def reproducir(self, tipo, query):
        if not self.sp:
            print("⚠️ Spotify no está autenticado.")
            return "Spotify no está autenticado."

        device_id = self._get_active_device()
        if not device_id:
            print("⚠️ No hay dispositivos activos para reproducir.")
            return "No hay dispositivos activos. Abre Spotify en algún dispositivo."

        try:
            if tipo == "cancion":
                resultados = self.sp.search(q=query, type="track", limit=1)
                tracks = resultados.get('tracks', {}).get('items', [])
                if tracks:
                    uri = tracks[0]['uri']
                    self.sp.start_playback(device_id=device_id, uris=[uri])
                    nombre = tracks[0]['name']
                    artista = tracks[0]['artists'][0]['name']
                    return f"🎶 Reproduciendo '{nombre}' de {artista}"
                return f"No encontré una canción con el nombre '{query}'."

            elif tipo == "playlist":
                resultados = self.sp.search(q=query, type="playlist", limit=1)
                items = resultados.get('playlists', {}).get('items', [])
                if items:
                    uri = items[0]['uri']
                    self.sp.start_playback(device_id=device_id, context_uri=uri)
                    return f"📀 Reproduciendo playlist '{items[0]['name']}'"
                return f"No encontré una playlist llamada '{query}'."

            elif tipo == "album":
                resultados = self.sp.search(q=query, type="album", limit=1)
                items = resultados.get('albums', {}).get('items', [])
                if items:
                    uri = items[0]['uri']
                    self.sp.start_playback(device_id=device_id, context_uri=uri)
                    return f"💿 Reproduciendo álbum '{items[0]['name']}'"
                return f"No encontré un álbum llamado '{query}'."

            elif tipo == "artista":
                resultados = self.sp.search(q=query, type="artist", limit=1)
                artistas = resultados.get('artists', {}).get('items', [])
                if artistas:
                    artista_id = artistas[0]['id']
                    top_tracks = self.sp.artist_top_tracks(artista_id, country='MX')
                    tracks = top_tracks.get('tracks', [])
                    if tracks:
                        uris = [track['uri'] for track in tracks]
                        self.sp.start_playback(device_id=device_id, uris=uris)
                        return f"👩‍🎤 Reproduciendo top tracks de '{artistas[0]['name']}'"
                    return f"No encontré canciones del artista '{query}'."
                return f"No encontré un artista llamado '{query}'."

            else:
                print(f"⚠️ Tipo de reproducción no reconocido: {tipo}")
                return f"No reconozco el tipo de reproducción '{tipo}'."

        except Exception as e:
            print(f"❌ Error al intentar reproducir: {e}")
            return "Ocurrió un error al intentar reproducir en Spotify."
