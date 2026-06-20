# from datetime import datetime
import sys
import logging
import traceback
import tkinter as tk
from tkinter import messagebox
# from datetime import datetime

# --- Configuración ---
ARCHIVO_LOG = "historial_errores.log"

# Configuramos el sistema de logging profesional de Python
# Esto reemplaza el uso de 'open(file, "a")' manual
logging.basicConfig(
    filename=ARCHIVO_LOG,
    level=logging.INFO, # Captura desde INFO hacia arriba (INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

# ==========================================
# 1. Funciones de compatibilidad (Lo que ya usabas)
# ==========================================

def log_error(usuario, mensaje):
    """
    Registra un error funcional conocido (ej: Clave incorrecta).
    Mantiene compatibilidad con tu código existente.
    """
    texto = f"Usuario: {usuario} | Error: {mensaje}"
    logging.error(texto)
    # Opcional: Imprimir en consola también
    print(f"[LOG-ERROR] {texto}")

def log_info(mensaje):
    """
    Registra información general.
    """
    logging.info(mensaje)
    print(f"[LOG-INFO] {mensaje}")

# ==========================================
# 2. Sistema Anti-Crash (La red de seguridad)
# ==========================================

def _mostrar_alerta_visual(mensaje_error):
    """
    Muestra una ventana emergente si el programa muere inesperadamente.
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Ocultamos la ventana principal de Tkinter
        
        mensaje_amigable = (
            "⚠️ Ocurrió un error crítico y el programa debe cerrarse.\n\n"
            f"El detalle ha sido guardado en '{ARCHIVO_LOG}'.\n"
            "Por favor, contacte al soporte con este archivo.\n\n"
            f"Error: {mensaje_error}"
        )
        
        messagebox.showerror("Error Crítico - ARCA Downloader", mensaje_amigable)
        root.destroy()
    except Exception:
        pass

def _hook_excepciones(exc_type, exc_value, exc_traceback):
    """
    Atrapa cualquier error que no haya sido capturado por un try/except.
    """
    # Si el usuario presiona Ctrl+C, dejamos que se cierre normal
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Formateamos el error completo
    lista_traza = traceback.format_exception(exc_type, exc_value, exc_traceback)
    traza_completa = "".join(lista_traza)
    
    # 1. Guardamos en el LOG
    logging.critical("⛔ CRASH DEL SISTEMA DETECTADO ⛔")
    logging.critical(f"Tipo: {exc_type.__name__}")
    logging.critical(f"Mensaje: {exc_value}")
    logging.critical("Traceback:\n" + traza_completa)
    logging.critical("-" * 50)

    # 2. Mostramos en consola
    print("\n🔥 ¡ERROR FATAL! El programa se cerrará. 🔥")
    print(traza_completa)

    # 3. Alerta visual al usuario
    _mostrar_alerta_visual(str(exc_value))

    # 4. Salir
    sys.exit(1)

def iniciar_proteccion():
    """
    Activa la protección global. Llamar al inicio de Main.
    """
    sys.excepthook = _hook_excepciones
    logging.info("=== SISTEMA INICIADO: Protección de errores activada ===")








# ==========================================
# 3. Herramienta de Depuración (DEBUG)
# ==========================================
import functools

DEBUG_MODE = True  # Variable global para activar/desactivar el modo debug

def debug_trace(func):
    """
    Decorador para imprimir y registrar el flujo de ejecución (solo para debug).
    Muestra mensajes claros sobre qué función inicia, termina o falla con detalle de errores.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if DEBUG_MODE:
            msg_inicio = f"[DEBUG] ---> Entrando a función: {func.__name__} <---"
            print(msg_inicio)
            logging.info(msg_inicio)
        try:
            resultado = func(*args, **kwargs)
            if DEBUG_MODE:
                msg_fin = f"[DEBUG] <--- Saliendo de función (ÉXITO): {func.__name__} <---"
                print(msg_fin)
                logging.info(msg_fin)
            return resultado
        except Exception as e:
            if DEBUG_MODE:
                detalle = traceback.format_exc()
                print(f"\n{'='*60}")
                print(f"❌ [DEBUG ERROR] FALLÓ LA FUNCIÓN: {func.__name__}")
                print(f"Tipo de error: {type(e).__name__}")
                print(f"Detalle completo del traceback:")
                print(detalle)
                print(f"{'='*60}\n")
                logging.error(f"[DEBUG ERROR] Falló {func.__name__}: {str(e)}\n{detalle}")
            raise # Relanza la excepción para que el programa maneje el error normalmente
    return wrapper

# def log_error(usuario, mensaje):
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open("errores.log", "a", encoding="utf-8") as f:
#         f.write(f"[{timestamp}] Usuario {usuario}: {mensaje}\n")

# def log_info(mensaje):
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open("errores.log", "a", encoding="utf-8") as f:
#         f.write(f"[{timestamp}] INFO: {mensaje}\n")