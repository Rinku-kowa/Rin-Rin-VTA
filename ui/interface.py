from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout,
    QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont, QTextCursor, QColor, QTextCharFormat
from PySide6.QtCore import Qt, QThread, Signal, QUrl
import traceback
from PySide6.QtWebEngineWidgets import QWebEngineView
import os


class WorkerThread(QThread):
    resultado = Signal(str)

    def __init__(self, callback, texto):
        super().__init__()
        self.callback = callback
        self.texto = texto

    def run(self):
        print(f"[WorkerThread] Iniciando con texto: {self.texto}")
        try:
            respuesta = self.callback(self.texto)
            print(f"[WorkerThread] Callback completado, emitiendo resultado")
            self.resultado.emit(respuesta)
        except Exception as e:
            print(f"[WorkerThread] Excepción en run(): {e}")
            traceback.print_exc()
            # Emitir un mensaje de error al GUI para notificar
            self.resultado.emit("Lo siento, ocurrió un error inesperado.")


class RinInterface(QWidget):
    def __init__(self, enviar_callback):
        super().__init__()
        self.setWindowTitle("Asistente Rin")
        self.setFixedSize(600, 700)
        self.setStyleSheet("background-color: #fef6fb;")

        self.enviar_callback = enviar_callback
        self.modo = "texto"
        self.worker = None

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Imagen Rin centrada
        self.web_view = QWebEngineView()
        ruta_html = os.path.abspath("ui/rin_live2d.html")
        self.web_view.load(QUrl.fromLocalFile(ruta_html))
        self.web_view.setFixedSize(280, 280)
        main_layout.insertWidget(0, self.web_view)

        # Área de conversación (solo lectura)
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet(
            """
            background-color: #ffffff;
            border-radius: 12px;
            padding: 10px;
            font-family: Consolas, monospace;
            font-size: 14px;
            """
        )
        self.chat_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.chat_box)

        # Campo de entrada de texto
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(60)
        self.text_input.setStyleSheet(
            """
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            """
        )
        self.text_input.setPlaceholderText("Escribe tu mensaje aquí...")
        self.text_input.textChanged.connect(self._toggle_send_button)
        main_layout.addWidget(self.text_input)

        # Fila de botones: Enviar/Escuchar y Cambiar modo
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.setEnabled(False)
        self.send_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f06292;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:disabled {
                background-color: #f8bbd0;
                color: #eee;
            }
            QPushButton:hover:!disabled {
                background-color: #ec407a;
            }
            """
        )
        self.send_btn.clicked.connect(self.enviar_texto)
        btn_layout.addWidget(self.send_btn)

        self.mode_btn = QPushButton("Cambiar a Voz")
        self.mode_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #cccccc;
                color: #333;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #bbbbbb;
            }
            """
        )
        self.mode_btn.clicked.connect(self.cambiar_modo)
        btn_layout.addWidget(self.mode_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def _toggle_send_button(self):
        texto = self.text_input.toPlainText().strip()
        self.send_btn.setEnabled(bool(texto))

    def enviar_texto(self):
        # Dependiendo del modo, enviamos texto o solicitamos STT
        if self.modo == "voz":
            texto_a_procesar = ""
        else:
            texto_a_procesar = self.text_input.toPlainText().strip()
            if not texto_a_procesar:
                return
            self._append_chat("Tú", texto_a_procesar, is_usuario=True)
            self.text_input.clear()
            self.send_btn.setEnabled(False)

        # Ejecutar callback en hilo para no bloquear UI
        self.worker = WorkerThread(self.enviar_callback, texto_a_procesar)
        self.worker.resultado.connect(self.mostrar_respuesta)
        self.worker.start()

    def mostrar_respuesta(self, respuesta):
        if respuesta:
            self._append_chat("Rin", respuesta, is_usuario=False)

    def cambiar_modo(self):
        if self.modo == "texto":
            self.modo = "voz"
            self.mode_btn.setText("Cambiar a Texto")
            self.text_input.setDisabled(True)
            self.send_btn.setText("Escuchar")
            self.send_btn.setEnabled(True)
        else:
            self.modo = "texto"
            self.mode_btn.setText("Cambiar a Voz")
            self.text_input.setDisabled(False)
            self.send_btn.setText("Enviar")
            self.send_btn.setEnabled(False)

    def _append_chat(self, quien, texto, is_usuario):
        cursor = self.chat_box.textCursor()
        cursor.movePosition(QTextCursor.End)

        formato_usuario = QTextCharFormat()
        formato_usuario.setForeground(QColor("#49e5eb"))
        formato_usuario.setFontWeight(QFont.Bold)

        formato_rin = QTextCharFormat()
        formato_rin.setForeground(QColor("#6A36F8"))
        formato_rin.setFontWeight(QFont.Bold)

        formato = formato_usuario if is_usuario else formato_rin
        cursor.insertText(f"{quien}: ", formato)
        cursor.insertText(texto + "\n\n")

        self.chat_box.ensureCursorVisible()
