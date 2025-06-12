import sympy as sp

class CalculatorModule:
    def __init__(self):
        pass
    
    def calcular(self, entrada):
        try:
            # Convertir la entrada en una expresión de sympy
            expr = sp.sympify(entrada)
            resultado = sp.simplify(expr)
            
            # Evitar respuestas como "El resultado es: entrada" (no resolvió nada)
            if str(resultado) == entrada:
                return None  # No hubo simplificación o cálculo real

            return f"El resultado es: {resultado}"
        
        except Exception as e:
            # Opcional: log del error para debug
            print(f"[Error al calcular]: {e}")
            return None
