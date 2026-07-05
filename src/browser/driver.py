"""
browser/driver.py
-----------------
Manejo del navegador Chrome: apertura y cambio de ventanas.
"""

import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from estado_usuario import set_estado


# Modo sin ventana. Flip a True para correr Chrome headless (útil/necesario al
# procesar varios clientes en paralelo, para no llenar la pantalla). OJO: hay
# que verificar en AFIP que las descargas y la generación de PDF (print_page)
# sigan funcionando en headless.
HEADLESS = False

# Registro de todas las instancias de Chrome abiertas, para poder cerrarlas de
# golpe al abortar (Ctrl+C o tecla de pánico). Protegido por lock porque los
# clientes se abren desde varios hilos.
_drivers_abiertos = set()
_drivers_lock = threading.Lock()


def open_chrome(download_dir):
    """
    Abre una nueva instancia del navegador Chrome configurado para
    descargas automáticas y carga la página de login de AFIP.

    Args:
        download_dir (str): Ruta donde se guardarán las descargas.

    Returns:
        webdriver.Chrome: Instancia del driver lista para usar.
    """
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    options.add_experimental_option("prefs", prefs)
    # detach=False: cuando el proceso termina (o lo matás), Chrome se cierra
    # también (antes quedaba abierto con detach=True).
    options.add_experimental_option("detach", False)

    # Suprimir errores de consola de Chrome
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    dv = webdriver.Chrome(options=options)
    with _drivers_lock:
        _drivers_abiertos.add(dv)
    dv.get("https://auth.afip.gob.ar/contribuyente_/login.xhtml")
    return dv


def cerrar_driver(dv):
    """
    Cierra una instancia de Chrome y la saca del registro.

    Usar en vez de dv.quit() para mantener el registro consistente.
    """
    with _drivers_lock:
        _drivers_abiertos.discard(dv)
    try:
        dv.quit()
    except Exception:
        pass


def cerrar_todos_los_chrome():
    """
    Cierra TODAS las instancias de Chrome abiertas de una sola vez.

    Pensada para abortar el programa (Ctrl+C o tecla de pánico).
    """
    with _drivers_lock:
        drivers = list(_drivers_abiertos)
        _drivers_abiertos.clear()
    for dv in drivers:
        try:
            dv.quit()
        except Exception:
            pass
    if drivers:
        print(f"[INFO] Se cerraron {len(drivers)} instancia(s) de Chrome.")


def change_window(dv, estado, original_window, timeout=10):
    """
    Cambia el foco del navegador a la nueva pestaña abierta,
    distinta de la pestaña original.

    Args:
        dv (webdriver): Instancia del driver.
        estado (dict): Estado del usuario actual.
        original_window (str): Handle de la pestaña original.
        timeout (int): Segundos de espera para que aparezca la nueva pestaña.

    Returns:
        bool: True si el cambio fue exitoso, False en caso contrario.
    """
    try:
        WebDriverWait(dv, timeout).until(lambda d: len(d.window_handles) > 1)
    except Exception:
        set_estado(estado, "cambio_pestania", "ERROR", "No se abrió la nueva pestaña")
        return False

    try:
        for handle in dv.window_handles:
            if handle != original_window:
                dv.switch_to.window(handle)

                # Esperar a que la nueva pestaña termine de cargar antes de
                # devolver el control. AFIP hace redirects intermedios, así que
                # sin esto el llamador puede empezar a buscar elementos sobre una
                # página aún en blanco o transitoria.
                try:
                    WebDriverWait(dv, timeout).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except Exception:
                    # No es fatal: el llamador tiene sus propias esperas.
                    pass

                set_estado(estado, "cambio_pestania", "OK")
                return True

        set_estado(estado, "cambio_pestania", "ERROR", "No se encontró una pestaña distinta")
        return False

    except Exception as e:
        set_estado(estado, "cambio_pestania", "ERROR", f"Excepción al cambiar de pestaña: {e}")
        return False
