"""
tools.py
--------
Utilidades generales del sistema: inicialización, pausas, fechas,
manejo de PDFs y helpers de Selenium de bajo nivel.
"""

import os
import base64
import time
from datetime import datetime, timedelta
import keyboard

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.print_page_options import PrintOptions

import config_loader as cl


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

def init(ruta_base, sheet_name):
    """
    Inicializa el sistema: carga la configuración del Excel y crea
    la carpeta de destino de descargas si no existe.

    Args:
        ruta_base (str): Ruta completa al archivo Excel de configuración.
        sheet_name (str): Nombre de la hoja a leer en el Excel.

    Returns:
        tuple: (base_dir, config)
            base_dir (str): Ruta de la carpeta 'Datos Afip'.
            config (list): Lista de dicts con los datos de cada usuario.
    """
    config   = cl.procesar_config(ruta_base, sheet_name)
    base_dir = os.path.dirname(ruta_base) + "\\Datos Afip"
    os.makedirs(base_dir, exist_ok=True)
    return base_dir, config


# ---------------------------------------------------------------------------
# Tiempo
# ---------------------------------------------------------------------------

def pausa(velocidad):
    """
    Pausa la ejecución. A mayor velocidad, menor pausa.

    Args:
        velocidad (int/float): Factor de velocidad. Pausa = 1/velocidad segundos.
    """
    time.sleep(1 / velocidad)


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------

def obtener_fechas_mes_pasado_formato_ddMMAAAA():
    """
    Calcula el primer y último día del mes anterior en formato dd/mm/AAAA.

    Returns:
        tuple: (primer_dia_str, ultimo_dia_str) — ejemplo: ('01/06/2025', '30/06/2025').
    """
    hoy = datetime.now()
    primer_dia_mes_actual    = hoy.replace(day=1)
    ultimo_dia_mes_pasado_dt = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_pasado_dt = ultimo_dia_mes_pasado_dt.replace(day=1)

    return (
        primer_dia_mes_pasado_dt.strftime("%d/%m/%Y"),
        ultimo_dia_mes_pasado_dt.strftime("%d/%m/%Y"),
    )


def obtener_mes_anterior():
    """
    Devuelve el año y mes anterior en formato 'YYYYMM'.

    Returns:
        str: Ejemplo: '202506'.
    """
    hoy = datetime.now()
    if hoy.month == 1:
        return f"{hoy.year - 1}12"
    return f"{hoy.year}{hoy.month - 1:02d}"


# ---------------------------------------------------------------------------
# Formateo de CUIT
# ---------------------------------------------------------------------------

def _formato_cuit_visual(cuit_plano):
    """
    Convierte un CUIT de 11 dígitos al formato visual con guiones: XX-XXXXXXXX-X.
    Ejemplo: '30123456789' → '30-12345678-9'.

    Args:
        cuit_plano (str | int): CUIT sin guiones.

    Returns:
        str: CUIT con guiones, o el valor original si no tiene 11 dígitos.
    """
    cuit = str(cuit_plano).strip()
    if len(cuit) == 11:
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10:]}"
    return cuit


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def guardar_pdf_en_ruta(dv, carpeta_destino, nombre_archivo):
    """
    Genera un PDF de la página actual con Selenium y lo guarda en disco.

    Args:
        dv: WebDriver.
        carpeta_destino (str): Carpeta donde se guardará el archivo.
        nombre_archivo (str): Nombre del archivo PDF (con extensión).
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    print_options = PrintOptions()
    print_options.background = True
    pdf_base64 = dv.print_page(print_options)

    with open(ruta_completa, "wb") as f:
        f.write(base64.b64decode(pdf_base64))

    print(f"PDF guardado en: {ruta_completa}")


# ---------------------------------------------------------------------------
# Debug / Selenium de bajo nivel
# ---------------------------------------------------------------------------

def _encontrar_todos_elementos(dv, xpath, timeout=10):
    """
    Busca y retorna todos los WebElements que coinciden con el XPath dado.
    Útil para depuración y para manejar múltiples elementos dinámicos.

    Args:
        dv: WebDriver.
        xpath (str): Expresión XPath a buscar.
        timeout (int): Segundos de espera para que aparezca al menos un elemento.

    Returns:
        list[WebElement]: Lista de elementos encontrados (vacía si ninguno aparece).
    """
    try:
        WebDriverWait(dv, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        elementos = dv.find_elements(By.XPATH, xpath)
        for i, el in enumerate(elementos):
            try:
                print(f"[DEBUG]   Elemento {i+1}: Tag '{el.tag_name}', "
                      f"Texto: '{el.text}', class='{el.get_attribute('class')}'")
            except Exception as e:
                print(f"[DEBUG]   No se pudo leer el elemento {i+1}: {e}")
        return elementos

    except TimeoutException:
        print(f"[DEBUG] No se encontraron elementos con XPath '{xpath}' "
              f"en {timeout}s.")
        return []
    except Exception as e:
        print(f"[ERROR] Fallo al buscar elementos con XPath '{xpath}': {e}")
        return []