import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

class SpotifyModule:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state user-modify-playback-state"
        ))

    def reproducir_spotify(self, query):
        results = self.sp.search(q=query, limit=1, type="track")
        if results['tracks']['items']:
            uri = results['tracks']['items'][0]['uri']
            self.sp.start_playback(uris=[uri])
            print(f"🎶 Reproduciendo {query} en Spotify")
        else:
            print(f"⚠️ No encontré resultados para '{query}'")
