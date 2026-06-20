"""
afip/portal_iva.py
------------------
Navegación y descarga del Libro IVA en el Portal IVA de AFIP.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser import actions as act
import tab_navigation as tn
import tools


def ingresar_Portal_IVA(dv):
    """
    Intenta hacer clic en la opción 'PORTAL IVA' del menú de servicios.

    Returns:
        bool: True si se encontró y clickeó, False si no aparece en el menú.
    """
    try:
        act._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='PORTAL IVA']")
        return True
    except Exception:
        print("[INFO] Portal IVA no figura en el menú.")
        return False


def portal_iva_disponible(dv, timeout=2):
    """
    Verifica si el Portal IVA cargó correctamente buscando un botón exclusivo del sistema.

    Args:
        dv: WebDriver.
        timeout (int): Segundos de espera.

    Returns:
        bool: True si el Portal IVA está disponible.
    """
    act.wait_until_page_loaded(dv)
    try:
        WebDriverWait(dv, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[aria-label="Sin texto (iva.home.btn.nueva.declaracion.alt)"]')
            )
        )
        return True
    except Exception:
        return False


def obtener_representado_actual_portal_iva(dv):
    """
    Lee y devuelve el nombre del contribuyente que figura en la barra superior
    del Portal IVA ('Representando a: ...').

    Returns:
        str | None: Texto completo del representado, o None si no se pudo detectar.
    """
    xpath_texto = "//span[contains(@class, 'text-uppercase') and contains(., 'Representando a:')]"
    try:
        elemento = act._wait_for_page_ready(dv, "elemento", 5, By.XPATH, xpath_texto, returnable=True)
        texto_completo = elemento.text
        print(f"[INFO] {texto_completo}")
        return texto_completo
    except Exception:
        print("[WARN] No se pudo detectar a quién se está representando en Portal IVA.")
        return None


def seleccionar_empresa_portal_iva(dv, cuit_destino):
    """
    Busca en la lista de 'Representados' la tarjeta que corresponde al CUIT dado
    y hace clic sobre ella.

    Args:
        dv: WebDriver.
        cuit_destino (str): CUIT de la empresa a seleccionar (11 dígitos sin guiones).

    Returns:
        bool: True si se seleccionó con éxito, False en caso contrario.
    """
    cuit_fmt = tools._formato_cuit_visual(cuit_destino)
    print(f"[INFO] Buscando empresa con CUIT: {cuit_fmt}")

    xpath_tarjeta = f"//div[contains(@class, 'media') and .//small[contains(., '{cuit_fmt}')]]"
    try:
        act._click_element_by(dv, By.XPATH, xpath_tarjeta, timeout=5)
        return True
    except Exception as e:
        print(f"[ERROR] No se encontró la empresa con CUIT {cuit_fmt}: {e}")
        return False


def descargar_libro_IVA(dv, usuario, ruta, velocidad=1, estado=None):
    """
    Descarga el Libro IVA (Ventas y Compras) del mes anterior en el Portal IVA.

    Flujo:
        1. Abre nueva declaración del período anterior.
        2. Importa datos desde AFIP para Ventas y Compras.
        3. Genera y guarda la vista previa como PDF.

    Args:
        dv: WebDriver posicionado en el Portal IVA.
        usuario (dict): Datos del usuario con clave 'nombre'.
        ruta (str): Carpeta raíz donde se guardará el PDF.
        velocidad (int/float): Factor de velocidad para pausas.
        estado (dict | None): Estado del usuario (no usado actualmente, reservado).
    """
    act.wait_until_page_loaded(dv)

    # 1. Abrir nueva declaración
    act._click_element_by(dv, By.CSS_SELECTOR,
                           'button[aria-label="Sin texto (iva.home.btn.nueva.declaracion.alt)"]')
    tools.pausa(velocidad / 3)

    # 2. Seleccionar período anterior
    act.seleccionar_opcion_por_value(dv, 'select[name="periodo"]', tools.obtener_mes_anterior())
    tools.pausa(velocidad / 3)

    act._click_element_by(dv, By.CSS_SELECTOR,
                           'button[aria-label="Sin texto (iva.btn.home.validar.periodo.alt)"]')
    tools.pausa(velocidad / 3)

    act._click_element_by(dv, By.CSS_SELECTOR,
                           'button[aria-label="Sin texto (iva.btn.home.liva.alt)"]')
    tools.pausa(velocidad / 3)

    # 3. Importar datos de Ventas y Compras desde AFIP
    debug_saltar_importacion = False
    if debug_saltar_importacion:
        print("[DEBUG] Saltando importación de datos en Portal IVA (modo debug).")
    else:
        secciones = ["Ventas", "Compras"]
        for seccion in secciones:
            if seccion == "Ventas":
                act._click_element_by(dv, By.ID, 'btnLibroVentas')
                tools.pausa(velocidad / 3)

            act._click_element_by(dv, By.ID, 'lnkImportarAFIP')
            tools.pausa(velocidad / 3)
            act._click_element_by(dv, By.ID, 'btnImportarAFIPImportar')
            tools.pausa(velocidad / 3)
            act._click_element_by(dv, By.ID, 'btnTareasCerrar')
            tools.pausa(velocidad / 3)
            act._click_span_descarga(dv)
            tools.pausa(velocidad / 3)

            if seccion == "Ventas":
                act._click_element_by(dv, By.CSS_SELECTOR, 'a[href="verCompras.do?t=21"]')

    # 4. Generar y guardar PDF
    act._click_element_by(dv, By.CSS_SELECTOR, 'a[href="menuPresentacion.do"]')
    tools.pausa(velocidad / 3)
    act._click_element_by(dv, By.ID, 'btnVistaPrevia')
    tools.pausa(velocidad / 5)

    ruta_descarga_chrome = ruta + f"\\{usuario['nombre']}"
    tools.guardar_pdf_en_ruta(dv, ruta_descarga_chrome, f"LibroIVA_{usuario['nombre']}.pdf")
    act._click_element_by(dv, By.ID, 'btnDescargarVistaPrevia')
    tools.pausa(velocidad)
