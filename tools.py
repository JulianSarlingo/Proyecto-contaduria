from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import click_tool as ct
import tab_navigation as tn
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import os
# import config_loader as cl
import config_loader as cl
from datetime import datetime, timedelta

# ruta_origen = "C:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\Datos Afip\\"
# ruta_descargas = "C:\\Users\\Julian\\Downloads"
# Inicializador de datos

def init(ruta_base, sheet_name):
    # config_file_path = "C:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\config_program.xlsx"
    # config_file_path = ruta_base+"config_program.xlsx"
    # config_file_path = ruta_base+"Clientes 2025 juli.xlsm"
    # config = cl.configuracion(config_file_path) # Carga la configuración del Excel
    config = cl.procesar_config(ruta_base, sheet_name) # Carga la configuración del Excel
    base_dir = os.path.dirname(ruta_base)+"\\Datos Afip"

    
    # base_dir = ruta_base.strip("\\")+"\\Datos Afip"
    # base_dir = +"\\Datos Afip"
    os.makedirs(base_dir, exist_ok=True)

    return base_dir, config
    
# === Funciones de ayuda ===
def pausa(velocidad):
    time.sleep(1/velocidad)

# --- COMIENZO DE LA FUNCIÓN _encontrar_todos_elementos (CÓPIALA EXACTAMENTE COMO LA TENEMOS) ---
def _encontrar_todos_elementos(dv, xpath, timeout=10):
    """
    Busca y retorna una lista de todos los WebElements que coinciden con el XPath dado.
    Útil para depuración y para manejar múltiples elementos.

    Args:
        dv (webdriver): Instancia del navegador (driver de Selenium).
        xpath (str): Expresión XPath de los elementos a buscar.
        timeout (int): Tiempo máximo de espera en segundos para que al menos un elemento aparezca.

    Returns:
        list[WebElement]: Una lista de WebElements encontrados. Si no se encuentra ninguno, devuelve una lista vacía.
    """
    try:
        # Espera hasta que al menos un elemento sea visible o presente
        WebDriverWait(dv, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        # Una vez que sabemos que al menos uno existe, obtenemos todos.
        elementos = dv.find_elements(By.XPATH, xpath)

        for i, el in enumerate(elementos):
            try:
                print(f"[DEBUG]   Elemento {i+1}: Tag '{el.tag_name}', Texto: '{el.text}', Atributos: 'class={el.get_attribute('class')}'")
            except Exception as e:
                print(f"[DEBUG]   No se pudo obtener el texto o atributos del elemento {i+1}: {e}")
        return elementos
    except TimeoutException:
        print(f"[DEBUG] No se encontraron elementos con el XPath '{xpath}' dentro del tiempo de espera de {timeout} segundos.")
        return [] # Devuelve una lista vacía si no se encuentra ninguno
    except Exception as e:
        print(f"[ERROR] Fallo al buscar elementos con XPath '{xpath}': {e}")
        return []

# === Ventanas ===

def change_window(dv, original_window):
    """
    Cambia el foco del navegador a la nueva pestaña abierta, distinta de la original.

    Args:
        dv (webdriver): Driver de Selenium.
        original_window (str): Handle de la ventana original.
    """
    WebDriverWait(dv, 10).until(lambda d: len(d.window_handles) > 1)
    for handle in dv.window_handles:
        if handle != original_window:
            dv.switch_to.window(handle)
            # print("[INFO] Cambiado a la nueva pestaña")
            break

def open_chrome(download_dir):
    """
    Abre una nueva instancia del navegador Chrome y carga la página de login de AFIP.
    """
    # download_dir = r"c:\Users\Julian\Desktop\Programacion\Proyectos\MarianoMortero\Datos Afip"
    
    # Crea el directorio si no existe (descomenta si es necesario)
    # if not os.path.exists(download_dir):
    #     os.makedirs(download_dir)

    options = Options()

    # 1. Combina TODAS las preferencias en un único diccionario 'prefs'
    #    Tanto la ruta de descarga como la configuración de descargas automáticas.
    prefs = {
        # Configuración de DESCARGA
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,  # No preguntar dónde guardar
        "download.directory_upgrade": True,
        
        # Configuración de CONTENIDO/SEGURIDAD (para descargas automáticas, etc.)
        "profile.default_content_setting_values.automatic_downloads": 1
    }

    # Aplica TODAS las preferencias en UNA SOLA LLAMADA.
    options.add_experimental_option("prefs", prefs)

    # Opciones que SÍ están bien
    options.add_experimental_option("detach", True)
    
    # --- Opciones para suprimir errores de consola ---
    options.add_argument("--log-level=3") 
    options.add_experimental_option('excludeSwitches', ['enable-logging']) 
    # -----------------------------------------------------

    dv = webdriver.Chrome(options=options)

    # Abrir la página
    dv.get("https://auth.afip.gob.ar/contribuyente_/login.xhtml")
    # ct.wait_until_page_loaded(dv) 
    return dv

def open_chrome2(download_directory):
    """
    Abre una nueva instancia del navegador Chrome y carga la página de login de AFIP.

    - Mantiene el navegador abierto tras la ejecución.
    - Permite múltiples descargas automáticas desde el sitio.

    Returns:
        webdriver: Instancia del navegador Chrome configurada.
    """
    download_directory = os.path.join("c:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\", "Datos Afip\\")
    # if not os.path.exists(download_directory):
    #     os.makedirs(download_directory)

    options = Options()
    # Esta es la opción clave para cambiar la ruta de descarga
    options.add_experimental_option("prefs", {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,  # No preguntar dónde guardar
        "download.directory_upgrade": True
    })
    options.add_experimental_option("detach", True)
    prefs = {
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    options.add_experimental_option("prefs", prefs)

    # --- NUEVAS OPCIONES PARA SUPRIMIR ERRORES DE CONSOLA ---
    # 1. Suprimir logs de Chrome (especialmente útiles para errores como DEPRECATED_ENDPOINT)
    options.add_argument("--log-level=3") # 0=INFO, 1=WARNING, 2=LOG_ERROR, 3=FATAL. 3 suprime la mayoría.
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # Esto también ayuda a suprimir mensajes
    # -----------------------------------------------------

    dv = webdriver.Chrome(options=options)

    # Abrir la página
    dv.get("https://auth.afip.gob.ar/contribuyente_/login.xhtml")
    ct.wait_until_page_loaded(dv)
    # print("Página cargada completamente.")
    return dv

# === Login en AFIP ===

def login_afip(dv, user, password, velocidad):
    """
    Inicia sesión en AFIP usando las credenciales extraídas del archivo de texto.

    Args:
        dv (webdriver): Driver de Selenium.
        user (str): Nombre de usuario (CUIT).
        password (str): Contraseña del usuario.
        velocidad (int): Velocidad de espera entre acciones.
    """

    # Escribir usuario
    ct._login_user(dv, user, password, velocidad)

def _servicios(dv):
    """
    Accede al menú general de servicios dentro del portal de AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct._click_element_by(dv, By.CSS_SELECTOR, "a[href='/portal/app/mis-servicios']")
    # ct._click_element_css(dv, "a[href='/portal/app/mis-servicios']")


# === Navegación a "Mis Comprobantes" ===
# === Y sus 4 funciones ===
def ingresar_mis_comprobantes(dv):
    """
    Hace clic en la sección "MIS COMPROBANTES" del portal AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct.wait_until_page_loaded(dv)
    ct._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='MIS COMPROBANTES']")
    # ct._click_element_xpath(dv, "//h3[normalize-space(text())='MIS COMPROBANTES']")

# === Selección de empresa ===

def encontrar_empresas(dv):
    xpath = "//small[contains(normalize-space(.), '-') and string-length(normalize-space(.)) > 10]"

    # os.system('cls')
    elementos = _encontrar_todos_elementos(dv, xpath)
    return elementos

def seleccionar_empresa(dv, element):
    """
    Selecciona la empresa o CUIT visible dentro de la interfaz, buscando un elemento tipo <p> con texto estructurado.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct._click_element(dv, element)


# === Descargar comprobantes ===

def buscar_descargar(dv, xpath, velocidad):
    """
    Realiza el flujo de búsqueda y descarga de comprobantes para una sección específica (emitidos o recibidos).

    Args:
        dv (webdriver): Driver de Selenium.
        xpath (str): XPath del encabezado de sección (h3).
    """
    ct._click_element_by(dv, By.XPATH, xpath)
    pausa(velocidad)
    ct._click_element_by(dv, By.ID, "btnCalendarioFechaEmision")
    pausa(velocidad)
    ct._click_element_by(dv, By.CSS_SELECTOR, "li[data-range-key='Mes Pasado']")
    pausa(velocidad)
    ct._click_element_by(dv, By.ID, "buscarComprobantes")
    pausa(velocidad)
    return ct._click_span_descarga(dv)


def descargar_comprobantes(dv, ruta_carpeta="", velocidad=1):
    """
    Descarga los comprobantes de las secciones "Emitidos" y "Recibidos".

    Para "Emitidos", retrocede a la página anterior usando `tn.retroceder_paginas()`.
    Para "Recibidos", simplemente espera unos segundos tras la descarga.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    # ruta_destino = ruta_origen+""
    secciones = ["Emitidos", "Recibidos"]
    for titulo in range(len(secciones)):
        pausa(velocidad)

        xpath = f"//h3[normalize-space(text())='{secciones[titulo]}']"
        tipo = buscar_descargar(dv, xpath, velocidad)

        if titulo == 0:
            tn.retroceder_paginas(dv)
        else:
            pausa(velocidad)
        
# === Navegación a "Mis Retenciones" ===

def ingresar_mis_retenciones(dv):
    """
    Hace clic en la sección "MIS RETENCIONES" del portal AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='MIS RETENCIONES']")
    # print("[INFO] Ingresando a MIS RETENCIONES...")
    # print("[ORDEN] Espere mientras se carga la página...")
    # print("[ORDEN] Haga click en el boton que le indica la pagina para ir a la versión anterior...")
    # print("[ORDEN] Cuando la página haya cargado completamente, presione Enter en esta consola para continuar...")
    # os.system('pause')

    # ct._click_element_by(dv, By.ID, "__EVID__481888__EV__e-button__")
    # ct._click_element_by(dv, By.XPATH, "//button[contains(., 'click aquí')]")
    # ct._click_element_by(dv, By.CSS_SELECTOR, "button.e-button")


def obtener_fechas_mes_pasado_formato_ddMMAAAA():
    """
    Obtiene el primer y último día del mes pasado en formato ddMMyyyy.

    Retorna:
        tuple: Una tupla que contiene dos cadenas de texto (strings):
               (primer_dia_mes_pasado_str, ultimo_dia_mes_pasado_str)
    """
    hoy = datetime.now()

    # Calculamos el primer día del mes actual.
    # Por ejemplo, si hoy es 2025-07-19, esto será 2025-07-01.
    primer_dia_mes_actual = hoy.replace(day=1)

    # Restamos un día para obtener el último día del mes pasado.
    # Si primer_dia_mes_actual es 2025-07-01, esto será 2025-06-30.
    ultimo_dia_mes_pasado_dt = primer_dia_mes_actual - timedelta(days=1)

    # El primer día del mes pasado es simplemente el último día del mes pasado
    # con el día fijado a 1.
    # Si ultimo_dia_mes_pasado_dt es 2025-06-30, esto será 2025-06-01.
    primer_dia_mes_pasado_dt = ultimo_dia_mes_pasado_dt.replace(day=1)

    # Formateamos las fechas a 'ddMMyyyy'
    primer_dia_str = primer_dia_mes_pasado_dt.strftime("%d/%m/%Y")
    ultimo_dia_str = ultimo_dia_mes_pasado_dt.strftime("%d/%m/%Y")

    return primer_dia_str, ultimo_dia_str


def descarga_retenciones(dv, cuit, velocidad=1):
    """
    Inicia el proceso de descarga de retenciones para un CUIT específico.

    Args:
        dv (webdriver): Driver de Selenium.
        cuit (str): CUIT a utilizar para filtrar las retenciones.
    """
    ct.seleccionar_opcion_por_value(dv, "select#cuitRetenido", cuit)
    impuesto = ""
    for i in range(2):
        if i == 0:
            impuesto = "216"
        elif i == 1:
            impuesto = "767"  # Corregido el bug de asignación
        ct.seleccionar_opcion_por_value(dv, "select#impuestos", impuesto)

        primer_dia, ultimo_dia = obtener_fechas_mes_pasado_formato_ddMMAAAA()

        # primer_dia, ultimo_dia = '01012024', '01012025'
        ct._write_input(dv, "fechaRetencionDesde", primer_dia, by=By.NAME, press_enter=False)
        ct._write_input(dv, "fechaRetencionHasta", ultimo_dia, by=By.NAME, press_enter=False)
        
        pausa(velocidad)

        ct._click_element_by(dv, By.CSS_SELECTOR, 'input.inputbutton[type="submit"][value="Consultar"]')

        ct._click_span_descarga(dv, type="Retenciones")

        tn.retroceder_paginas(dv)

# === Nueva función de descarga de retenciones (cambió la web, usar cuando esté lista) ===

def descarga_retenciones_nueva(dv, cuit, velocidad=1):
    """
    Inicia el proceso de descarga de retenciones para un CUIT específico.

    Args:
        dv (webdriver): Driver de Selenium.
        cuit (str): CUIT a utilizar para filtrar las retenciones.
    """
    # ct.wait_until_page_loaded(dv)
    impuesto = ""
    for i in range(2):
        ct._wait_for_page_ready(dv, modo="clickeable", by=By.ID, identifier='btnConsultarRetenciones')
        pausa(velocidad)
        if i == 0:
            impuesto = "216"
        elif i == 1:
            impuesto = "767"  # Corregido el bug de asignación
        ct._write_input(dv, "selectImpuestos", impuesto)
        ct._write_input(dv, "cuitAgenteRetencion", cuit)

        if i == 1:
            ct._click_element_by(dv, By.XPATH, '//label[contains(text(), "Retención y percepción")]')

        primer_dia, ultimo_dia = obtener_fechas_mes_pasado_formato_ddMMAAAA()

        # primer_dia, ultimo_dia = '01012024', '01012025'
        pausa(velocidad)
        ct._write_input_force(dv, "datePickerFechasRetencionesDesde__input", primer_dia, by=By.ID, press_enter=False)
        # ct._write_input(dv, "datePickerFechasRetencionesDesde__input", primer_dia, by=By.ID, press_enter=False)
        pausa(velocidad)
        ct._write_input_force(dv, "datePickerFechasRetencionesHasta__input", ultimo_dia, by=By.ID, press_enter=False)


        ct._click_element_by(dv, By.ID, 'btnConsultarRetenciones')

        ct._click_span_descarga(dv, type="Retenciones")

        # tn.retroceder_paginas(dv)