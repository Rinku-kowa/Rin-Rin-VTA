import os
import sys
import urllib.parse

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BrowserModule:
    """
    Módulo para controlar YouTube via Selenium WebDriver.
    Provee búsqueda de videos, apertura de YouTube y reproducción por índice.
    """
    def __init__(self, edge_driver_path: str):
        self.edge_driver_path = edge_driver_path
        self.driver = None
        self._null_file = None
        self._stderr_saved = None

    def _init_driver(self):
        """Inicializa el WebDriver de Edge, silenciando logs innecesarios."""
        if self.driver:
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
        finally:
            # restaurar stderr siempre
            if self._stderr_saved:
                sys.stderr = self._stderr_saved
            if self._null_file:
                self._null_file.close()

    def _check_driver(self):
        """Verifica que el driver esté activo; si no, (re)inicializa."""
        if not self.driver:
            self._init_driver()
        else:
            try:
                _ = self.driver.title
            except Exception:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
                self._init_driver()

    def abrir_youtube(self) -> str:
        """Abre la página principal de YouTube."""
        self._check_driver()
        if not self.driver:
            return "El navegador no está disponible."
        try:
            self.driver.get("https://www.youtube.com")
            return "YouTube abierto."
        except Exception as e:
            print(f"⚠️ Error al abrir YouTube: {e}")
            return "No pude abrir YouTube en este momento."

    def buscar_youtube(self, query: str) -> tuple[list[tuple[str, str]], str]:
        """Busca hasta 10 videos en YouTube y retorna (lista de (título, URL), mensaje)."""
        self._check_driver()
        if not self.driver:
            return [], "El módulo de navegador no está disponible en este momento."

        encoded = urllib.parse.quote_plus(query)
        print(f"🔍 Buscando en YouTube: {query}")
        try:
            self.driver.get(f"https://www.youtube.com/results?search_query={encoded}")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "video-title"))
            )
            elems = self.driver.find_elements(By.XPATH, "//a[@id='video-title']")[:10]
            if not elems:
                return [], "No se encontraron videos."
            resultados = [(e.get_attribute("title"), e.get_attribute("href")) for e in elems]
            return resultados, f"Encontré {len(resultados)} videos. ¿Cuál quieres reproducir? (1-{len(resultados)})"
        except Exception as e:
            print(f"⚠️ Error al buscar videos: {e}")
            return [], "No pude buscar videos en YouTube ahora."

    def reproducir_video_por_indice(self, index: int, resultados: list[tuple[str, str]]) -> str:
        """Reproduce el video en la posición `index` de la lista `resultados`."""
        self._check_driver()
        if not self.driver:
            return "El módulo de navegador no está disponible."
        if index < 0 or index >= len(resultados):
            return "El número está fuera de rango. Intenta con otro."
        try:
            titulo, url = resultados[index]
            self.driver.get(url)
            print(f"▶️ Reproduciendo: {titulo}")
            return f"Reproduciendo: {titulo}"
        except Exception as e:
            print(f"⚠️ Error al reproducir video: {e}")
            return "No pude reproducir el video seleccionado."

    def cerrar_pestana_actual(self) -> None:
        """Cierra la pestaña activa sin cerrar todo el navegador."""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                print(f"⚠️ Error al cerrar pestaña: {e}")

    def cerrar(self) -> None:
        """Cierra el navegador completamente."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"⚠️ Error al cerrar el driver: {e}")
            self.driver = None
