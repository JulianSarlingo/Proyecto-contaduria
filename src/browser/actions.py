"""
browser/actions.py
------------------
Funciones de interacción con el navegador: clics, escritura en inputs,
esperas de elementos y descarga de archivos.
"""

import time
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    InvalidSelectorException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)


# ---------------------------------------------------------------------------
# Esperas
# ---------------------------------------------------------------------------

def _wait_for_page_ready(driver, modo="completo", timeout=15, by=None,
                          identifier=None, loader_class=None,
                          returnable=False, silent=False):
    """
    Espera a que la página o un elemento específico estén listos.

    Args:
        driver: Instancia del WebDriver.
        modo (str): 'document' | 'elemento' | 'clickeable' | 'invisible' | 'completo'.
        timeout (int): Segundos máximos de espera.
        by: Estrategia de búsqueda (By.ID, By.XPATH, etc.).
        identifier (str): Valor del selector del elemento.
        loader_class (str): Clase CSS del loader a esperar que desaparezca.
        returnable (bool): Si True, devuelve el WebElement encontrado.
        silent (bool): Si True, no imprime errores en consola al agotar timeout.

    Returns:
        WebElement | None
    """
    try:
        if modo in ["document", "completo"]:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

        if modo in ["elemento", "completo"] and by and identifier:
            elemento = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, identifier))
            )
            if returnable:
                return elemento

        if modo in ["clickeable", "completo"] and by and identifier:
            elemento = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, identifier))
            )
            if returnable:
                return elemento

        if modo in ["invisible", "completo"] and loader_class:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, loader_class))
            )

    except Exception as e:
        if not silent:
            info_extra = f" -> Buscando: '{identifier}'" if identifier else ""
            print(f"[ERROR] Tiempo de espera agotado en modo '{modo}'{info_extra}. (Timeout: {timeout}s)")
        raise


def wait_until_page_loaded(dv):
    """Espera hasta que el documento esté completamente cargado."""
    _wait_for_page_ready(dv, "document", 10)


# ---------------------------------------------------------------------------
# Escritura en inputs
# ---------------------------------------------------------------------------

def _write_input(dv, field_identifier, value, by=By.ID, press_enter=True):
    """
    Escribe un valor en un campo de entrada estándar.

    Args:
        dv: WebDriver.
        field_identifier (str): ID u otro selector del campo.
        value: Valor a escribir.
        by: Estrategia de búsqueda (defecto: By.ID).
        press_enter (bool): Si True, presiona Enter al finalizar.
    """
    try:
        wait_until_page_loaded(dv)
        input_field = dv.find_element(by, field_identifier)
        input_field.clear()
        input_field.send_keys(value)
        if press_enter:
            input_field.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"[ERROR] Falló escritura en '{field_identifier}': {e}")


def _write_input_force(dv, field_identifier, value, by=By.ID, press_enter=True):
    """
    Escribe un valor en un campo íntegramente por JavaScript.

    A diferencia de send_keys, esto funciona en campos 'readonly', 'disabled'
    o cubiertos por un overlay (caso típico de los date pickers de AFIP, que
    de otro modo lanzan 'element not interactable'). Setea el value y dispara
    los eventos input/change/blur para que el framework (JSF/Angular) registre
    el cambio como si el usuario hubiera tipeado.

    Args:
        dv: WebDriver.
        field_identifier (str): ID u otro selector del campo.
        value: Valor a escribir.
        by: Estrategia de búsqueda (defecto: By.ID).
        press_enter (bool): Si True, despacha un evento Enter al finalizar.
    """
    try:
        wait_until_page_loaded(dv)
        input_field = WebDriverWait(dv, 15).until(
            EC.presence_of_element_located((by, field_identifier))
        )
        dv.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)

        resultado = dv.execute_script(
            """
            const el = arguments[0], val = arguments[1];
            const antes = el.value;
            el.removeAttribute('readonly');
            el.removeAttribute('disabled');
            el.focus();

            // Setter NATIVO del prototipo: imprescindible para que Angular/React
            // detecten el cambio. Asignar el.value directo suele ser ignorado o
            // pisado por el change-detection del framework (su modelo conserva el
            // valor por defecto, y el botón Consultar puede quedar deshabilitado).
            const desc = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value');
            desc.set.call(el, val);

            // React: invalidar su value tracker interno para que registre el input.
            if (el._valueTracker) { el._valueTracker.setValue(''); }

            ['keydown', 'input', 'keyup', 'change', 'blur'].forEach(function (t) {
                el.dispatchEvent(new Event(t, {bubbles: true}));
            });
            return {antes: antes, despues: el.value};
            """,
            input_field, value,
        )

        # Verificación: los campos traen un valor por defecto, así que no alcanza
        # con mirar si están vacíos. Avisamos si el valor no cambió respecto al
        # previo (el componente revirtió al default → probablemente exija
        # selección por calendario).
        if resultado.get("despues") == resultado.get("antes"):
            print(f"[WARN] '{field_identifier}' no cambió: sigue en "
                  f"'{resultado.get('despues')}' tras intentar poner '{value}'. "
                  f"El componente puede requerir interacción por calendario.")

        if press_enter:
            dv.execute_script(
                "arguments[0].dispatchEvent(new KeyboardEvent('keydown', "
                "{key: 'Enter', keyCode: 13, which: 13, bubbles: true}));",
                input_field,
            )
    except Exception as e:
        print(f"[ERROR] Falló escritura forzada en '{field_identifier}': {e}")


# ---------------------------------------------------------------------------
# Clics
# ---------------------------------------------------------------------------

def _click_element(dv, element, scroll=True, force_js=True):
    """
    Hace clic en un WebElement ya localizado.

    Args:
        dv: WebDriver.
        element: WebElement a clickear.
        scroll (bool): Si True, hace scroll hasta el elemento antes de clickear.
        force_js (bool): Si True, usa JavaScript para el clic. OJO: el click de
            JS tiene isTrusted=false y dispara solo 'click' (sin mousedown/mouseup),
            por lo que algunos componentes (Vue/React) lo ignoran. Para esos casos
            usar force_js=False, que hace un click nativo/confiable.
    """
    if scroll:
        # Centrar (no 'true', que alinea el elemento arriba de todo y lo puede
        # tapar un header sticky, provocando ElementClickInterceptedException).
        dv.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            element,
        )

    if force_js:
        dv.execute_script("arguments[0].click();", element)
    else:
        try:
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            # El click nativo directo quedó tapado o mal posicionado: reintentar
            # moviendo el mouse al elemento con ActionChains (también genera un
            # click real/confiable, no un sintético).
            ActionChains(dv).move_to_element(element).pause(0.1).click().perform()


def _first_visible_element(dv, by, value):
    """
    Devuelve el primer elemento VISIBLE (con tamaño real) que matchea el selector.

    Necesario porque el layout responsive de AFIP puede renderizar el mismo id
    varias veces (versión desktop y mobile) y ocultar por CSS la que no
    corresponde al viewport. find_element devolvería el primero del DOM —que
    suele ser el oculto— y el click falla con 'has no size and location'.

    Returns:
        WebElement visible, o el primero encontrado como último recurso, o None.
    """
    elementos = dv.find_elements(by, value)
    for el in elementos:
        try:
            size = el.size
            if el.is_displayed() and size.get("width", 0) > 0 and size.get("height", 0) > 0:
                return el
        except Exception:
            continue
    return elementos[0] if elementos else None


def _click_element_by(dv, by, value, timeout=10, scroll=True, force_js=True):
    """
    Busca un elemento por selector y le hace clic. Reintenta hasta 4 veces.

    Entre múltiples coincidencias prioriza la que está visible (ver
    _first_visible_element), para evitar clickear duplicados ocultos.
    """
    ultimo_error = None

    for intento in range(4):
        try:
            # Esperar a que exista al menos uno en el DOM.
            _wait_for_page_ready(dv, "elemento", timeout, by, value,
                                 returnable=True, silent=True)

            # Elegir el elemento VISIBLE (no un duplicado oculto sin tamaño).
            element = _first_visible_element(dv, by, value)
            if element is None:
                raise WebDriverException(f"Sin coincidencias para [{by}: {value}]")

            _click_element(dv, element, scroll, force_js)
            return # Éxito, salimos de la función inmediatamente
            
        except InvalidSelectorException as e:
            # Si el XPath/CSS está mal redactado, rompemos el bucle porque nunca va a funcionar
            raise e
            
        except Exception as e:
            ultimo_error = e
            # Bajamos el tiempo de espera en el reintento si es un fallo de click/interacción
            time.sleep(0.5) 
            
    # Si llegó acá es porque falló los 4 intentos
    raise RuntimeError(f"No se pudo hacer clic en el elemento [{by}: {value}] después de 4 intentos. Último error: {ultimo_error}")


# ---------------------------------------------------------------------------
# Selects
# ---------------------------------------------------------------------------

def seleccionar_opcion_por_value(dv, selector_css, valor):
    """
    Selecciona una opción en un elemento <select> por su atributo 'value'.

    Args:
        dv: WebDriver.
        selector_css (str): Selector CSS del elemento <select>.
        valor (str): Valor del <option> a seleccionar.
    """
    try:
        select_element = dv.find_element(By.CSS_SELECTOR, selector_css)
        select_obj = Select(select_element)
        select_obj.select_by_value(valor)
    except Exception as e:
        print(f"[ERROR] Falló selección en '{selector_css}' valor '{valor}': {e}")


# ---------------------------------------------------------------------------
# Descarga de archivos
# ---------------------------------------------------------------------------

def buscar_botones_descargables(dv, textos=["Excel", "CSV"], timeout=10):
    """
    Busca y devuelve los botones de descarga visibles en la página.

    Args:
        dv: WebDriver.
        textos (list): Textos de los botones a buscar.
        timeout (int): Segundos de espera.

    Returns:
        list[tuple]: Lista de (texto, WebElement) de botones visibles.
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
        except Exception:
            pass
    return botones_validos


def _click_span_descarga(dv, formatos=["Excel", "CSV"], tipo="Comprobantes"):
    """
    Hace clic en los botones de descarga según el tipo de sección.

    Args:
        dv: WebDriver.
        formatos (list): Formatos a descargar ['Excel', 'CSV'].
        tipo (str): 'Comprobantes', 'Portal' o 'Retenciones'.

    Returns:
        dict: Resultado por formato {"Excel": "OK"/"ERROR", "CSV": "OK"/"ERROR"}.
    """
    wait_until_page_loaded(dv)

    if tipo in ["Comprobantes", "Portal"]:
        resultados = {f: None for f in formatos}
        for texto in formatos:
            try:
                xpath = f"//button[.//span[normalize-space(text())='{texto}']]"
                _click_element_by(dv, By.XPATH, xpath, 4)
                resultados[texto] = "OK"
                time.sleep(0.4)
            except Exception:
                resultados[texto] = "ERROR"
        return resultados

    elif tipo == "Retenciones":
        try:
            selector = "a[href*='consultaMisRetenciones.do?method=exportExcel']"
            _click_element_by(dv, By.CSS_SELECTOR, selector, 4)
            return {"Excel": "OK"}
        except Exception:
            boton = "btnNuevaBusqueda"
            _click_element_by(dv, By.ID, boton, 4)
            return {"Excel": "ERROR"}


# ---------------------------------------------------------------------------
# Portal IVA — Cambio de representado
# ---------------------------------------------------------------------------

def click_cambiar_representado_portal_iva(dv):
    """
    Hace clic en el botón de cambio de representado (ícono de personitas)
    en la barra superior del Portal IVA.

    Returns:
        bool: True si se hizo clic correctamente, False en caso contrario.
    """
    selector_boton = "a[title='cambio relación']"
    print("[INFO] Buscando botón de cambio de relación...")
    try:
        _click_element_by(dv, By.CSS_SELECTOR, selector_boton, timeout=5)
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo hacer clic en el botón de cambio de relación: {e}")
        return False
