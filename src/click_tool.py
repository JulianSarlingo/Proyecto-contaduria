from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time, tools
from logger import log_error

# === Funciones generales ===

# Agregamos el parámetro 'silent=False' al final
def _wait_for_page_ready(driver, modo="completo", timeout=15, by=None, identifier=None, loader_class=None, returnable=False, silent=False):
    """
    Espera elementos o estados de página.
    Args:
        silent (bool): Si es True, NO imprime mensaje de error en consola al fallar el timeout.
    """
    try:
        if modo in ["document", "completo"]:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # print("[INFO] DOM completamente cargado") # <--- COMENTADO

        if modo in ["elemento", "completo"] and by and identifier:
            elemento = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, identifier))
            )
            # print(f"[INFO] Elemento '{identifier}' presente") # <--- COMENTADO
            if returnable:
                return elemento

        if modo in ["clickeable", "completo"] and by and identifier:
            elemento = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, identifier))
            )
            # print(f"[INFO] Elemento '{identifier}' está clickeable") # <--- COMENTADO
            if returnable:
                return elemento

        if modo in ["invisible", "completo"] and loader_class:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, loader_class))
            )
            # print(f"[INFO] Loader '{loader_class}' desapareció") # <--- COMENTADO

    except Exception as e:
        # SOLO imprimimos si NO estamos en modo silencioso
        if not silent:
            info_extra = f" -> Buscando: '{identifier}'" if identifier else ""
            print(f"[ERROR] Tiempo de espera agotado en modo '{modo}'{info_extra}. (Timeout: {timeout}s)")
        raise


def wait_until_page_loaded(dv):
    """Espera hasta que el documento esté completely cargado."""
    _wait_for_page_ready(dv, "document", 10)

def detectar_error_login(dv):
    try:
        error_xpath = "//span[contains(text(), 'incorrecto') or contains(text(), 'incorrecta')]"
        errores = dv.find_elements(By.XPATH, error_xpath)
        return len(errores) > 0
    except:
        return False

def detectar_cambio_clave(dv):
    """Detecta si AFIP exige cambio obligatorio de contraseña."""
    patrones = [
        "//h4[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cambiar clave fiscal')]",
        "//span[@id='F1:msg']",
    ]
    for xp in patrones:
        try:
            _wait_for_page_ready(dv, "elemento", 1, By.XPATH, xp, silent=True)
            return True
        except:
            pass
    return False

def _login_user(dv, user, password, velocidad):
    """Completa login AFIP."""
    try:
        _write_input(dv, "F1:username", user)
        tools.pausa(velocidad)

        _write_input(dv, "F1:password", password)
        tools.pausa(velocidad)

        if detectar_cambio_clave(dv):
            log_error(user, "El usuario debe cambiar la contraseña")
            raise Exception("Cambio obligatorio de contraseña")

        if detectar_error_login(dv):
            log_error(user, "Login incorrecto (CUIT o contraseña inválidos)")
            raise Exception("Login incorrecto")

    except Exception as e:
        log_error(user, f"Falló login: {e}")
        # print(f"[ERROR] Login fallido usuario '{user}': {e}") # Opcional: silenciar si ya sale en el log
        raise 

def _write_input_force(dv, field_identifier, value, by=By.ID, press_enter=True):
    """Fuerza escritura con JS + SendKeys."""
    try:
        wait_until_page_loaded(dv)
        input_field = dv.find_element(by, field_identifier)
        dv.execute_script("arguments[0].value = '';", input_field)
        input_field.send_keys(value)
        if press_enter:
            input_field.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"[ERROR] Falló escritura forzada en '{field_identifier}': {e}")

def _write_input(dv, field_identifier, value, by=By.ID, press_enter=True):
    """Escribe valor normal."""
    try:
        wait_until_page_loaded(dv)
        input_field = dv.find_element(by, field_identifier)
        input_field.clear()
        input_field.send_keys(value)
        if press_enter:
            input_field.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"[ERROR] Falló escritura en '{field_identifier}': {e}")

def _click_element(dv, element, scroll=True, force_js=True):
    if scroll:
        dv.execute_script("arguments[0].scrollIntoView(true);", element)
    if force_js:
        dv.execute_script("arguments[0].click();", element)
    else:
        element.click()

def _click_element_by(dv, by, value, timeout=10, scroll=True, force_js=True):
    """Busca y clickea elemento."""
    for intento in range (4):
        try:
            element = _wait_for_page_ready(dv, "elemento", timeout, by, value, returnable=True)
            _click_element(dv, element, scroll, force_js)
            break
        except:
            time.sleep(1)

def seleccionar_opcion_por_value(dv, selector_css, valor):
    """Selecciona en <select> por value."""
    try:
        select_element = dv.find_element(By.CSS_SELECTOR, selector_css)
        select_obj = Select(select_element)
        select_obj.select_by_value(valor)
    except Exception as e:
        print(f"[ERROR] Falló selección en '{selector_css}' valor '{valor}': {e}")

def buscar_botones_descargables(dv, textos=["Excel", "CSV"], timeout=10):
    """Devuelve botones visibles."""
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
            # print(f"[WARN] No botón '{texto}': {e}") # Silenciado WARN leve
            pass
    return botones_validos

def _click_span_descarga(dv, formatos=["Excel", "CSV"], type="Comprobantes"):
    """
    Clickea botones de descarga solo para los formatos especificados.
    """
    wait_until_page_loaded(dv)
    
    if type == "Comprobantes" or type == "Portal":
        # Inicializa un diccionario con los formatos que estamos buscando
        resultados = {f: None for f in formatos}
        
        # Itera SOLO sobre los formatos solicitados (Ej: solo "Excel" o solo "CSV")
        for texto in formatos:
            try:
                # Busca el botón con el texto (Excel o CSV)
                xpath = f"//button[.//span[normalize-space(text())='{texto}']]"
                _click_element_by(dv, By.XPATH, xpath, 4)
                resultados[texto] = "OK"
                time.sleep(0.4)
            except Exception as e:
                # Si no encuentra el botón, marca error para ese formato
                resultados[texto] = "ERROR"
        return resultados
            
    # La lógica para Retenciones no necesita cambios ya que no usa el parámetro 'formatos'
    elif type == "Retenciones":
        try:
            selector = "a[href*='consultaMisRetenciones.do?method=exportExcel']"
            _click_element_by(dv, By.CSS_SELECTOR, selector, 4)
            return {"Excel": "OK"}
        except Exception as e:
            boton = "btnNuevaBusqueda"
            _click_element_by(dv, By.ID, boton, 4)
            return {"Excel": "ERROR"}

def click_cambiar_representado_portal_iva(dv):

    """
    Busca el botón de 'cambio relación' (las dos personitas) en la barra superior
    y hace clic en él.
    """
    # Selector CSS exacto basado en el HTML que pasaste: a[title='cambio relación']
    selector_boton = "a[title='cambio relación']"
    
    print("[INFO] Buscando botón de cambio de relación...")
    
    try:
        # Usamos tu función _click_element_by que ya maneja esperas y scrolls
        _click_element_by(dv, By.CSS_SELECTOR, selector_boton, timeout=5)
        return True
        
    except Exception as e:
        print(f"[ERROR] No se pudo hacer clic en el botón de cambio de relación: {e}")
        return False
    
