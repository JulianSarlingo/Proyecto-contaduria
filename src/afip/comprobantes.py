"""
afip/comprobantes.py
--------------------
Navegación y descarga en la sección "Mis Comprobantes" de AFIP.
"""

from selenium.webdriver.common.by import By
from browser import actions as act
from estado_usuario import set_estado
import tab_navigation as tn
import tools


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _registrar_resultado(estado, clave, resultados):
    """
    Registra el resultado de una descarga de comprobantes en el estado del usuario.
    Considera exitoso si al menos uno de los formatos (Excel o CSV) fue OK.

    Args:
        estado (dict): Estado del usuario.
        clave (str): Clave del estado a actualizar ('comprobantes_emitidos', etc.).
        resultados (dict): {"Excel": "OK"/"ERROR", "CSV": "OK"/"ERROR"}.
    """
    excel_ok = (resultados.get("Excel") == "OK")
    csv_ok   = (resultados.get("CSV")   == "OK")

    if excel_ok or csv_ok:
        set_estado(estado, clave, "OK")
    else:
        fallo = f"Excel: {resultados.get('Excel', 'NO BUSCADO')} - CSV: {resultados.get('CSV', 'NO BUSCADO')}"
        set_estado(estado, clave, "ERROR", fallo)


# ---------------------------------------------------------------------------
# Navegación
# ---------------------------------------------------------------------------

def ingresar_mis_comprobantes(dv):
    """
    Hace clic en la sección 'MIS COMPROBANTES' del portal AFIP.

    Args:
        dv: WebDriver.
    """
    act._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='MIS COMPROBANTES']")


def encontrar_empresas(dv):
    """
    Busca y retorna todos los elementos de empresa disponibles en la pantalla.

    Returns:
        list[WebElement]: Lista de elementos de empresa encontrados.
    """
    xpath = "//small[contains(normalize-space(.), '-') and string-length(normalize-space(.)) > 10]"
    return tools._encontrar_todos_elementos(dv, xpath)


def seleccionar_empresa(dv, element):
    """
    Hace clic en un elemento de empresa para seleccionarla.

    Args:
        dv: WebDriver.
        element: WebElement de la empresa a seleccionar.
    """
    act._click_element(dv, element)


# ---------------------------------------------------------------------------
# Búsqueda y descarga
# ---------------------------------------------------------------------------

def buscar_descargar(dv, xpath, velocidad, formatos=["Excel", "CSV"]):
    """
    Ejecuta el flujo completo de búsqueda y descarga de comprobantes:
    entra a la sección, selecciona 'Mes Pasado' y descarga en los formatos indicados.

    Args:
        dv: WebDriver.
        xpath (str): XPath de la sección (Emitidos o Recibidos).
        velocidad (int/float): Factor de velocidad para pausas.
        formatos (list): Formatos a descargar ['Excel', 'CSV'].

    Returns:
        dict: Resultado por formato {"Excel": "OK"/"ERROR"}.
    """

    act._click_element_by(dv, By.XPATH, xpath)
    tools.pausa(velocidad)
    act._click_element_by(dv, By.ID, "btnCalendarioFechaEmision", force_js=False)
    tools.pausa(velocidad)
    act._click_element_by(dv, By.CSS_SELECTOR, "li[data-range-key='Mes Pasado']", force_js=False)
    tools.pausa(velocidad)
    act._click_element_by(dv, By.ID, "buscarComprobantes")
    tools.pausa(velocidad)
    return act._click_span_descarga(dv, formatos=formatos)


def descargar_comprobantes(dv, usuario, estado, velocidad=1):
    """
    Descarga los comprobantes del mes pasado aplicando la lógica correcta
    según la condición impositiva del usuario (RI, Monotributo, etc.).

    - Emitidos (Ventas): siempre se descargan.
    - Recibidos (Compras): solo para Responsables Inscriptos.

    Args:
        dv: WebDriver posicionado en la sección Mis Comprobantes.
        usuario (dict): Datos del usuario con clave 'tipo_monotributo'.
        estado (dict): Estado del usuario para registrar resultados.
        velocidad (int/float): Factor de velocidad.
    """
    condicion = usuario.get('tipo_monotributo', 'Monotributo')
    secciones = ["Emitidos", "Recibidos"]

    print(f"[INFO] Aplicando lógica de descarga para condición: {condicion}")

    for tipo_comprobante in secciones:
        tools.pausa(velocidad)

        # Los Monotributistas no tienen comprobantes recibidos (Compras)
        if tipo_comprobante == "Recibidos" and "Monot" in condicion:
            print(f"[INFO] Omitiendo descarga de Compras (Recibidos) para {condicion}")
            continue

        xpath = f"//h3[normalize-space(text())='{tipo_comprobante}']"
        formatos_a_bajar = []

        if tipo_comprobante == "Emitidos":
            if condicion in ["Resp. Inscripto", "Monot. Convenio"]:
                formatos_a_bajar = ["CSV"]
            elif condicion == "Monot. Unificado":
                formatos_a_bajar = ["Excel"]
            else:
                formatos_a_bajar = ["Excel"]
        else:
            # Recibidos — solo llega acá si NO es Monotributista
            formatos_a_bajar = ["Excel"]

        resultados = buscar_descargar(dv, xpath, velocidad, formatos=formatos_a_bajar)

        if tipo_comprobante == "Emitidos":
            _registrar_resultado(estado, "comprobantes_emitidos", resultados)
            tn.retroceder_paginas(dv)
        else:
            _registrar_resultado(estado, "comprobantes_recibidos", resultados)
            tools.pausa(velocidad)
