"""
afip/retenciones.py
-------------------
Navegación y descarga en la sección "Mis Retenciones" de AFIP.
"""

from selenium.webdriver.common.by import By
from browser import actions as act
from estado_usuario import set_estado
import tools


def ingresar_mis_retenciones(dv):
    """
    Hace clic en la sección 'MIS RETENCIONES' del portal AFIP.

    Args:
        dv: WebDriver.
    """
    act._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='MIS RETENCIONES']")


def hay_retenciones_renderizadas(dv):
    """
    Verifica si la tabla de resultados de retenciones contiene datos.

    Returns:
        bool: True si hay datos, False si aparece el mensaje 'Sin resultados'.
    """
    try:
        xpath_sin_datos = "//h4[contains(normalize-space(.), 'No hay resultados para tu consulta')]"
        if len(dv.find_elements(By.XPATH, xpath_sin_datos)) > 0:
            return False

        filas = dv.find_elements(By.CSS_SELECTOR, "table tbody tr")
        return len(filas) > 0

    except Exception:
        return False


def descarga_retenciones(dv, cuit, velocidad=1, estado=None):
    """
    Descarga las retenciones del mes pasado para los dos impuestos principales
    (216 - Ganancias y 767 - IVA).

    Si no hay datos para un impuesto, lo registra como OK con nota 'Sin datos'
    y continúa con el siguiente.

    Args:
        dv: WebDriver posicionado en la sección Mis Retenciones.
        cuit (str): CUIT del agente de retención (11 dígitos).
        velocidad (int/float): Factor de velocidad para pausas.
        estado (dict | None): Estado del usuario para registrar resultados.
    """
    for i in range(2):
        # Señuelo de carga: esperamos la PRESENCIA del botón de consulta, no que
        # sea "clickeable". El botón existe en el DOM antes de estar visible/
        # habilitado, y de todos modos lo clickeamos por JS (que ignora la
        # visibilidad). Usar element_to_be_clickable acá daba timeout aunque el
        # botón estuviera y fuera usable. Timeout amplio: la pestaña recién
        # cambiada puede seguir cargando (redirects de AFIP).
        try:
            act._wait_for_page_ready(dv, modo="elemento", timeout=30, by=By.ID,
                                     identifier='btnConsultarRetenciones')
        except Exception as e:
            print(f"[ERROR] No apareció 'btnConsultarRetenciones' en la página: {e}")

        tools.pausa(velocidad)

        # Impuesto 216 = Ganancias, 767 = IVA
        impuesto = "216" if i == 0 else "767"
        act._write_input(dv, "selectImpuestos", impuesto)
        act._write_input(dv, "cuitAgenteRetencion", cuit)

        if i == 1:
            act._click_element_by(dv, By.XPATH, '//label[contains(text(), "Retención y percepción")]')

        # Rango de fechas del mes anterior
        primer_dia, ultimo_dia = tools.obtener_fechas_mes_pasado_formato_ddMMAAAA()
        tools.pausa(velocidad)
        act._write_input_force(dv, "datePickerFechasRetencionesDesdeSiap__input", primer_dia, press_enter=False)
        tools.pausa(velocidad)
        act._write_input_force(dv, "datePickerFechasRetencionesHastaSiap__input", ultimo_dia, press_enter=False)
        tools.pausa(velocidad)

        # Ejecutar la consulta. Click REAL (force_js=False): el botón es un
        # componente Vue que ignora el click sintético de JS (isTrusted=false y
        # sin secuencia mousedown/mouseup). El click nativo de Selenium sí
        # dispara su handler.
        act._click_element_by(dv, By.ID, 'btnConsultarRetenciones', force_js=False)
        tools.pausa(velocidad)

        # Sin datos → registrar y continuar
        if not hay_retenciones_renderizadas(dv):
            print(f"[INFO] No hay retenciones para impuesto {impuesto} (CUIT {cuit})")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "OK", "Sin datos")
            if i == 0:
                act._click_element_by(dv, By.ID, "btnNuevaBusqueda", 4)
            continue

        # Con datos → descargar
        try:
            act._click_span_descarga(dv, tipo="Retenciones")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "OK")
        except Exception as e:
            print(f"[ERROR] No se pudo descargar retenciones para impuesto {impuesto}: {e}")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "ERROR", str(e))

        # Volver al formulario de búsqueda antes de la próxima iteración.
        # Sin esto, la siguiente vuelta arranca en la página de resultados y
        # 'btnConsultarRetenciones' nunca llega a estar clickeable (timeout).
        if i == 0:
            act._click_element_by(dv, By.ID, "btnNuevaBusqueda", 4)
