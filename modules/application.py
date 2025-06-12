import subprocess

class ApplicationModule:
    def __init__(self):
        pass

    def abrir_aplicacion(self, nombre):
        try:
            subprocess.Popen(nombre, shell=True)
            print(f"⚙️ Abriendo {nombre}...")
        except Exception as e:
            print(f"⚠️ No se pudo abrir {nombre}")

