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
        act._wait_for_page_ready(dv, modo="clickeable", by=By.ID,
                                  identifier='btnConsultarRetenciones')
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
        act._write_input_force(dv, "datePickerFechasRetencionesDesde__input", primer_dia, press_enter=False)
        tools.pausa(velocidad)
        act._write_input_force(dv, "datePickerFechasRetencionesHasta__input", ultimo_dia, press_enter=False)
        tools.pausa(velocidad)

        # Ejecutar la consulta
        act._click_element_by(dv, By.ID, 'btnConsultarRetenciones')
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
            act._click_span_descarga(dv, type="Retenciones")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "OK")
        except Exception as e:
            print(f"[ERROR] No se pudo descargar retenciones para impuesto {impuesto}: {e}")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "ERROR", str(e))
