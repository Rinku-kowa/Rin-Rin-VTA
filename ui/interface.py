import os
import sys
import threading
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSizePolicy,
    QListWidget, QListWidgetItem, QLabel, QApplication
)
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QObject
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

# HTTP server thread
default_http_port = 8000
class HTTPServerThread(threading.Thread):
    def __init__(self, directory, port=default_http_port):
        super().__init__(daemon=True)
        self.directory = directory
        self.port = port
    def run(self):
        os.chdir(self.directory)
        HTTPServer(('localhost', self.port), SimpleHTTPRequestHandler).serve_forever()

# Custom WebEnginePage for JS logs
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, src):
        print(f"[JS][{line}] {msg}")

# Thread for conversational callbacks
class WorkerThread(QThread):
    resultado = Signal(str)
    def __init__(self, callback, texto):
        super().__init__()
        self.callback = callback
        self.texto = texto
    def run(self):
        try:
            resp = self.callback(self.texto)
        except Exception:
            traceback.print_exc()
            resp = "Lo siento, ocurrió un error inesperado."
        self.resultado.emit(resp)

# Thread for TTS playback
class TTSWorker(QObject):
    terminado = Signal()
    def __init__(self, tts, texto):
        super().__init__()
        self.tts = tts
        self.texto = texto
    def run(self):
        self.tts.speak(self.texto)
        self.terminado.emit()

class RinInterface(QWidget):
    # Signals to marshal STT callbacks into the Qt thread
    stt_result = Signal(str)
    stt_error = Signal(str)

    def __init__(self, enviar_callback=None, memory_module=None, tts=None, stt=None):
        super().__init__()
        self.enviar_callback = enviar_callback or (lambda x: "")
        self.memory = memory_module
        self.tts = tts
        self.stt = stt
        self.modo = 'texto'
        self._drag = None
        self.worker = None
        self.tts_thread = None

        # Connect STT signals
        self.stt_result.connect(self._on_stt_result)
        self.stt_error.connect(lambda msg: self._bubble('Rin', msg, False))

        # Start HTTP server
        HTTPServerThread(os.path.join(os.getcwd(), 'ui')).start()

        # Window setup
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(800, 500)

        # Layouts
        main = QVBoxLayout(self)
        main.setContentsMargins(5,5,5,5)
        main.setSpacing(5)
        content = QHBoxLayout()
        main.addLayout(content)

        # Chat
        self.chat = QListWidget()
        self.chat.setStyleSheet("QListWidget{background:transparent;border:none;} QListWidget::item{margin:6px;}" )
        content.addWidget(self.chat, stretch=2)

        # Live2D
        self.web = QWebEngineView()
        page = WebEnginePage(self)
        self.web.setPage(page)
        self.web.setStyleSheet("background:transparent;")
        self.web.page().setBackgroundColor(Qt.transparent)
        self.web.load(QUrl(f"http://localhost:{default_http_port}/rin_live2d.html"))
        content.addWidget(self.web, stretch=3)

        # Input controls
        bottom = QHBoxLayout()
        main.addLayout(bottom)
        self.input = QTextEdit()
        self.input.setFixedHeight(60)
        self.input.setPlaceholderText("Escribe tu mensaje...")
        self.input.textChanged.connect(self._toggle_send)
        bottom.addWidget(self.input, stretch=4)

        self.btn_send = QPushButton('Enviar')
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self._send)
        bottom.addWidget(self.btn_send, stretch=1)

        self.btn_mode = QPushButton('Cambiar a Voz')
        self.btn_mode.clicked.connect(self._toggle_mode)
        bottom.addWidget(self.btn_mode, stretch=1)

    def _toggle_send(self):
        enabled = (self.modo == 'voz') or bool(self.input.toPlainText().strip())
        self.btn_send.setEnabled(enabled)

    def _toggle_mode(self):
        if self.modo == 'texto':
            self.modo = 'voz'
            self.btn_mode.setText('Cambiar a Texto')
            self.input.setDisabled(True)
            self.btn_send.setText('Escuchar')
            self.btn_send.setEnabled(True)
        else:
            self.modo = 'texto'
            self.btn_mode.setText('Cambiar a Voz')
            self.input.setDisabled(False)
            self.btn_send.setText('Enviar')
            self.btn_send.setEnabled(False)

    def _send(self):
        if self.modo == 'voz':
            # Disable button and show listening bubble
            self.btn_send.setEnabled(False)
            self._bubble('Rin', 'Escuchando…', False)
            # Use SpeechToTextModule with Qt signals
            self.stt.escuchar(callback=self._stt_callback)
        else:
            text = self.input.toPlainText().strip()
            self.input.clear()
            self._start_worker(text)

    def _stt_callback(self, text):
        # Called in non-Qt thread; emit signals to Qt thread
        if text:
            self.stt_result.emit(text)
        else:
            self.stt_error.emit('No te escuché bien, intenta otra vez.')
            # Re-enable after error
            QThread.currentThread().msleep(100)
            self.btn_send.setEnabled(True)

    def _on_stt_result(self, text):
        # Re-enable button
        if self.modo == 'voz':
            self.btn_send.setEnabled(True)
        # Start processing
        self._start_worker(text)

    def _start_worker(self, text):
        if not text:
            return
        self._bubble('Tú', text, True)
        # Stop previous worker if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self.worker = WorkerThread(self.enviar_callback, text)
        self.worker.resultado.connect(self._on_response)
        self.worker.start()

    def _on_response(self, resp):
        self._bubble('Rin', resp, False)
        # TTS
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.quit()
            self.tts_thread.wait()
        self.tts_thread = QThread()
        tts_worker = TTSWorker(self.tts, resp)
        tts_worker.moveToThread(self.tts_thread)
        self.tts_thread.started.connect(tts_worker.run)
        tts_worker.terminado.connect(self.tts_thread.quit)
        tts_worker.terminado.connect(tts_worker.deleteLater)
        self.tts_thread.finished.connect(self.tts_thread.deleteLater)
        self.tts_thread.start()
        # Re-enable in voice mode
        if self.modo == 'voz':
            self.btn_send.setEnabled(True)

    def _bubble(self, who, msg, is_user):
        item = QListWidgetItem()
        lbl = QLabel(msg)
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl.setMaximumWidth(self.chat.width() * 0.8)
        color = '#1E3A5F' if is_user else '#4527A0'
        lbl.setStyleSheet(f"background: {color}; color: white; padding:12px; border-radius:12px; font-size:14px;")
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4,4,4,4)
        if is_user:
            layout.addStretch()
            layout.addWidget(lbl)
        else:
            layout.addWidget(lbl)
            layout.addStretch()
        item.setSizeHint(container.sizeHint())
        self.chat.addItem(item)
        self.chat.setItemWidget(item, container)
        self.chat.scrollToBottom()

    # Draggable
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e: QMouseEvent):
        if getattr(self, '_drag', None) and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)
    def mouseReleaseEvent(self, e: QMouseEvent):
        self._drag = None
