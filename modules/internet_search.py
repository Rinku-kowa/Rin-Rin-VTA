import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from urllib.parse import quote_plus
from bs4 import BeautifulSoup  # <-- necesitas instalar beautifulsoup4

class InternetSearchModule:
    def __init__(self, edge_driver_path):
        self.edge_driver_path = edge_driver_path
        self.driver = None
        self._null_file = None
        self._stderr_saved = None

    def _init_driver(self):
        if self.driver is not None:
            return
        try:
            self._null_file = open(os.devnull, "w")
            self._stderr_saved = sys.stderr
            sys.stderr = self._null_file

            options = webdriver.EdgeOptions()
            options.add_argument("--log-level=3")
            options.add_argument("--start-maximized")

            service = Service(executable_path=self.edge_driver_path)
            self.driver = webdriver.Edge(service=service, options=options)

        except Exception as e:
            print(f"⚠️ No pude iniciar el driver de Edge: {e}")
            self.driver = None
            if self._stderr_saved:
                sys.stderr = self._stderr_saved
            if self._null_file:
                self._null_file.close()

    def abrir_busqueda_google(self, query):
        self._init_driver()
        if not self.driver:
            return "El navegador no está disponible."
        try:
            url = f"https://www.google.com/search?q={quote_plus(query)}"
            self.driver.get(url)
            return f"Abrí la búsqueda en Google para: {query}"
        except Exception as e:
            print(f"⚠️ Error al abrir Google: {e}")
            return "No pude abrir la búsqueda en Google."

    def obtener_resumen_duckduckgo(self, query):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Buscar el primer resultado (en DuckDuckGo html versión)
            resultado = soup.find("a", class_="result__a")
            if resultado:
                titulo = resultado.get_text(strip=True)
                enlace = resultado.get('href')
                return f"{titulo}\nEnlace: {enlace}"
            else:
                return "No encontré un resumen para eso."
        except Exception as e:
            return f"No pude obtener resultados ({e})."

    def buscar_internet(self, query):
        abrir = self.abrir_busqueda_google(query)
        resumen = self.obtener_resumen_duckduckgo(query)
        return f"{abrir}\n\n{resumen}\n\n¿Quieres que busque algo más?"

    def cerrar(self):
        if self.driver:
            self.driver.quit()
        if self._stderr_saved:
            sys.stderr = self._stderr_saved
        if self._null_file:
            self._null_file.close()
