import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By

class BrowserModule:
    def __init__(self, edge_driver_path):
        self.edge_driver_path = edge_driver_path
        self.driver = None

        # Preparar para silenciar stderr cuando se inicie el driver
        self._null_file = None
        self._stderr_saved = None

    def _init_driver(self):
        """Crea el Edge webdriver sólo la primera vez, atrapa errores."""
        if self.driver is not None:
            return

        try:
            # silenciar stderr de Selenium/Edge
            self._null_file = open(os.devnull, "w")
            self._stderr_saved = sys.stderr
            sys.stderr = self._null_file

            options = webdriver.EdgeOptions()
            options.add_argument("--log-level=3")
            options.add_argument("--start-maximized")

            service = Service(executable_path=self.edge_driver_path)
            self.driver = webdriver.Edge(service=service, options=options)

        except Exception as e:
            # Si falla, informamos y dejamos driver en None
            print(f"⚠️ No pude iniciar el driver de Edge: {e}")
            self.driver = None
            # restaurar stderr si quedó cambiado
            if self._stderr_saved:
                sys.stderr = self._stderr_saved
            if self._null_file:
                self._null_file.close()

    def buscar_youtube(self, query):
        # Asegurarnos de haber intentado iniciar el driver
        self._init_driver()
        if not self.driver:
            return [], "El módulo de navegador no está disponible en este momento."

        print(f"🔍 Buscando en YouTube: {query}")
        try:
            self.driver.get(f"https://www.youtube.com/results?search_query={query}")
            time.sleep(2)

            videos = self.driver.find_elements(By.XPATH, "//a[@id='video-title']")[:10]
            if not videos:
                return [], "No se encontraron videos."

            resultados = [(v.get_attribute("title"), v.get_attribute("href")) for v in videos]
            return resultados, f"Encontré {len(resultados)} videos. ¿Cuál quieres reproducir? (1-{len(resultados)})"

        except Exception as e:
            print(f"⚠️ Error al buscar videos: {e}")
            return [], "No pude buscar videos en YouTube ahora."

    def reproducir_video_por_indice(self, index, resultados):
        if not self.driver:
            return "El módulo de navegador no está disponible."
        try:
            titulo, url = resultados[index]
            self.driver.get(url)
            print(f"▶️ Reproduciendo: {titulo}")
            return f"Reproduciendo: {titulo}"
        except Exception as e:
            print(f"⚠️ Error al reproducir video: {e}")
            return "No pude reproducir el video seleccionado."

    def cerrar(self):
        if self.driver:
            self.driver.quit()
        # Restaurar stderr si habíamos silenciado
        if self._stderr_saved:
            sys.stderr = self._stderr_saved
        if self._null_file:
            self._null_file.close()
