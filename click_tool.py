from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
# from tkinter import messagebox
import os


# === Funciones generales ===

def wait_until_page_loaded(dv):
    """
    Espera hasta que el documento esté completamente cargado (readyState == 'complete').

    Args:
        dv (webdriver): Instancia del navegador (driver de Selenium).
    """
    WebDriverWait(dv, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def _login_user(dv, user, password):
    """
    Completa los campos de usuario y contraseña en el formulario de login de AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
        user (str): Nombre de usuario.
        password (str): Contraseña.
    """
    try:
        _write_input(dv, "F1:username", user)
        _write_input(dv, "F1:password", password)
    except Exception as e:
        print(f"[ERROR] Fallo al intentar loguear usuario '{user}': {e}")

def _write_input(dv, field_identifier, value, by=By.ID, press_enter=True):
    """
    Escribe un valor en un campo de texto, identificado por ID o NAME, y opcionalmente simula ENTER.

    Args:
        dv (webdriver): Driver de Selenium.
        field_identifier (str): Valor del atributo (ID o NAME).
        value (str): Texto a escribir.
        by (By): Tipo de localizador (By.ID o By.NAME).
        press_enter (bool): Si debe simular ENTER al final.
    """
    try:
        wait_until_page_loaded(dv)
        input_field = dv.find_element(by, field_identifier)
        input_field.clear()
        input_field.send_keys(value)
        if press_enter:
            input_field.send_keys(Keys.RETURN)
        # print(f"[INFO] Escribiendo '{value}' en el campo ({by}='{field_identifier}')")
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en el campo: {e}")


def _click_element(dv, element, scroll=True, force_js=True):
    # try:
    if scroll:
        dv.execute_script("arguments[0].scrollIntoView(true);", element)
    if force_js:
        dv.execute_script("arguments[0].click();", element)
    else:
        element.click()


def _click_element_by(dv, by, value, timeout=10, scroll=True, force_js=True):
    """
    Hace clic en un elemento ubicado por cualquier estrategia (ID, CSS, XPath, etc.).

    Args:
        dv (webdriver): Driver de Selenium.
        by (By): Estrategia de localización (By.ID, By.CSS_SELECTOR, By.XPATH, etc.).
        value (str): Valor asociado a la estrategia (por ejemplo, el selector o XPath).
        timeout (int): Tiempo máximo de espera.
        scroll (bool): Si se debe hacer scroll hacia el elemento.
        force_js (bool): Si se debe hacer clic usando JavaScript (recomendado).
    """
    # try:
    element = WebDriverWait(dv, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    for intento in range (4):
        try:
            _click_element(dv, element, scroll, force_js)
            break
        except:
            time.sleep(1)

def seleccionar_opcion_por_value(dv, selector_css, valor):
    """
    Selecciona una opción en un <select> por su atributo 'value'.

    Args:
        driver (webdriver): Driver de Selenium.
        selector_css (str): Selector CSS que identifica el <select>.
        valor (str): Valor del atributo 'value' de la opción a seleccionar.
    """
    try:
        # print(f"[INFO] Buscando <select> con selector: {selector_css}")
        select_element = dv.find_element(By.CSS_SELECTOR, selector_css)
        select_obj = Select(select_element)
        select_obj.select_by_value(valor)
        # print(f"[INFO] Opción con value='{valor}' seleccionada correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo seleccionar la opción con value='{valor}':")


def buscar_botones_descargables(dv, textos=["Excel", "CSV"], timeout=10):
    """
    Busca todos los botones visibles que contengan un <span> con texto específico
    y devuelve los elementos clickeables (visibles y renderizados).

    Args:
        dv (webdriver): WebDriver de Selenium.
        textos (list): Lista de textos esperados dentro del <span> (por ejemplo, ["Excel", "CSV"]).
        timeout (int): Tiempo máximo para esperar que aparezcan en el DOM.

    Returns:
        list: Lista de elementos <button> que son válidos para hacer clic.
    """
    botones_validos = []

    for texto in textos:
        try:
            xpath = f"//button[.//span[normalize-space(text())='{texto}']]"
            botones = WebDriverWait(dv, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )

            for boton in botones:
                visible = dv.execute_script(
                    "return (arguments[0].offsetParent !== null && arguments[0].offsetWidth > 0);",
                    boton
                )
                if visible:
                    botones_validos.append((texto, boton))

        except Exception as e:
            print(f"[WARN] No se encontraron botones para texto '{texto}': {e}")

    return botones_validos

def _click_span_descarga(dv, excel="Excel", csv="CSV", type="Comprobantes"):
    """
    Busca y hace clic en botones de descarga según el tipo de proceso.

    Para type="Comprobantes":
        Busca botones visuales con etiquetas <span> que tengan texto igual a 'Excel' o 'CSV'.

    Para type="Retenciones":
        Busca un enlace <a> con un href que contiene 'consultaMisRetenciones.do?method=exportExcel'.

    Args:
        dv (webdriver): Instancia activa del driver de Selenium.
        excel (str): Texto del botón de descarga para Excel. Default: "Excel".
        csv (str): Texto del botón de descarga para CSV. Default: "CSV".
        type (str): Tipo de proceso para aplicar la estrategia de búsqueda. Puede ser "Comprobantes" o "Retenciones".
    """
    wait_until_page_loaded(dv)
    opciones = [excel, csv]
    # 👉 Buscar botones tipo <span> por texto visible
    if type == "Comprobantes":
        for texto in opciones:
            try:
                xpath = f"//button[.//span[normalize-space(text())='{texto}']]"
                _click_element_by(dv, By.XPATH, xpath, 4)
                print(f"[INFO] Se hizo clic en el botón <span> '{texto}' correctamente.")
                # os.system('pause')
                time.sleep(0.4)
                return texto
            except Exception as e:
                print(f"[WARN] No se encontró el botón <span> '{texto}': {e}")
            
    elif type == "Retenciones":
        # 👉 Buscar enlace <a> con exportExcel en el href
        try:
            selector = "a[href*='consultaMisRetenciones.do?method=exportExcel']"
            _click_element_by(dv, By.CSS_SELECTOR, selector, 4)
        except Exception as e:
            print(f"[WARN] No se encontró el enlace de exportación: {e}")