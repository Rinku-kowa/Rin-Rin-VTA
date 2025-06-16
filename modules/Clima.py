import requests

class ClimaModule:
    def __init__(self, api_key: str, location: str = "Monterrey,MX"):
        self.api_key = api_key
        self.location = location
        self.endpoint = "https://api.openweathermap.org/data/2.5/weather"

    def obtener_clima(self) -> str:
        """
        Retorna un string con descripción del clima, temperatura, humedad y velocidad del viento.
        Ejemplo de salida: "Nublado, 22.5°C, humedad 60%, viento 3.2 m/s"
        """
        try:
            params = {
                "q": self.location,
                "appid": self.api_key,
                "units": "metric",
                "lang": "es"
            }
            resp = requests.get(self.endpoint, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            desc = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            return f"{desc}, {temp:.1f}°C, humedad {humidity}%, viento {wind} m/s"
        except requests.RequestException as e:
            # Problema de red o API
            return f"No pude obtener el clima (error de conexión)."
        except (KeyError, IndexError):
            # Datos inesperados
            return "Error procesando datos de clima."