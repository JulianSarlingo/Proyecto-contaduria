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
import config_loader as cl
from datetime import datetime, timedelta
from estado_usuario import nuevo_estado, set_estado, imprimir_estado
import base64
from selenium.webdriver.common.print_page_options import PrintOptions


# ruta_origen = "C:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\Datos Afip\\"
# ruta_descargas = "C:\\Users\\Julian\\Downloads"
# Inicializador de datos

def init(ruta_base, sheet_name):
    
    config = cl.procesar_config(ruta_base, sheet_name) # Carga la configuración del Excel
    base_dir = os.path.dirname(ruta_base)+"\\Datos Afip"

    os.makedirs(base_dir, exist_ok=True)

    return base_dir, config
    
# === Funciones de ayuda ===
def pausa(velocidad):
    time.sleep(1/velocidad)

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

def obtener_mes_anterior():
    hoy = datetime.now()
    # Si estamos en enero → mes anterior es diciembre del año anterior
    if hoy.month == 1:
        año = hoy.year - 1
        mes = 12
    else:
        año = hoy.year
        mes = hoy.month - 1
    
    return f"{año}{mes:02d}"

def _formato_cuit_visual(cuit_plano):
    """
    Convierte '30123456789' en '30-12345678-9' para buscarlo en el HTML.
    """
    cuit = str(cuit_plano).strip()
    if len(cuit) == 11:
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10:]}"
    return cuit # Si viene mal, lo devolvemos igual por si acaso

def guardar_pdf_en_ruta(dv, carpeta_destino, nombre_archivo):
    # 1. (Opcional) Si la carpeta no existe, la crea automáticamente.
    # Esto evita errores si borraste la carpeta sin querer.
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # 2. Construimos la ruta completa de forma segura
    # Esto une "C:\MisDescargas" con "factura.pdf" poniendo la barra correcta
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    # 3. Generamos el PDF con Selenium 4
    print_options = PrintOptions()
    print_options.background = True # Incluir fondos y colores
    
    pdf_base64 = dv.print_page(print_options)

    # 4. Guardamos el archivo en la ruta específica
    with open(ruta_completa, "wb") as f:
        f.write(base64.b64decode(pdf_base64))

    print(f"PDF guardado en: {ruta_completa}")

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

def change_window(dv, estado, original_window, timeout=10):
    """
    Cambia el foco del navegador a la nueva pestaña abierta, distinta de la original.
    Registra el resultado en el estado.
    """
    try:
        # Esperar a que aparezca al menos 1 pestaña nueva
        WebDriverWait(dv, timeout).until(lambda d: len(d.window_handles) > 1)
    except Exception:
        # No apareció la nueva pestaña
        set_estado(
            estado,
            "cambio_pestania",
            "ERROR",
            "No se abrió la nueva pestaña"
        )
        return False

    # Intentar cambiar a la nueva pestaña
    try:
        for handle in dv.window_handles:
            if handle != original_window:
                dv.switch_to.window(handle)

                # Registrar éxito
                set_estado(
                    estado,
                    "cambio_pestania",
                    "OK"
                )
                return True

        # Si nunca entró al if, no encontró pestaña distinta
        set_estado(
            estado,
            "cambio_pestania",
            "ERROR",
            "No se encontró una pestaña distinta para cambiar"
        )
        return False

    except Exception as e:
        set_estado(
            estado,
            "cambio_pestania",
            "ERROR",
            f"Excepción al cambiar de pestaña: {e}"
        )
        return False

def open_chrome(download_dir):
    """
    Abre una nueva instancia del navegador Chrome y carga la página de login de AFIP.
    """
    # download_dir = r"c:\Users\Julian\Desktop\Programacion\Proyectos\MarianoMortero\Datos Afip"
    
    # Crea el directorio si no existe (descomenta si es necesario)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

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

# === Login en AFIP ===

def login_afip(dv, user, password, velocidad, estado):
    """
    Inicia sesión en AFIP usando las credenciales extraídas del archivo de texto.
    Maneja errores como login incorrecto y cambio obligatorio de contraseña.
    """

    try:
        ct._login_user(dv, user, password, velocidad)

        # Si llegamos acá, quiere decir que el login fue exitoso
        set_estado(estado, "login", "OK")

    except Exception as e:
        mensaje = str(e)

        # 🔥 Detectamos exactamente qué error fue
        if "Cambio obligatorio de contraseña" in mensaje:
            set_estado(estado, "login", "ERROR", "El usuario debe cambiar la contraseña")

        elif "Login incorrecto" in mensaje:
            set_estado(estado, "login", "ERROR", "CUIT o contraseña incorrecta")

        else:
            # Cualquier otro error real de Selenium
            set_estado(estado, "login", "ERROR", f"Excepción: {mensaje}")

        # Importante: devolvemos False para evitar que el flujo continúe
        return False

    return True

def _servicios(dv, timeout=3):
    """
    Accede al menú general de servicios dentro del portal de AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct._click_element_by(dv, By.CSS_SELECTOR, "a[href='/portal/app/mis-servicios']", timeout)
    # ct._click_element_css(dv, "a[href='/portal/app/mis-servicios']")


# === Navegación a "Mis Comprobantes" ===
# === Y sus 4 funciones ===
def ingresar_mis_comprobantes(dv):
    """
    Hace clic en la sección "MIS COMPROBANTES" del portal AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    # ct.wait_until_page_loaded(dv)
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

def seleccionar_empresa_portal_iva(dv, cuit_destino):
    """
    Busca en la lista de 'Representados' la tarjeta que corresponda al CUIT
    y le hace clic.
    """
    # 1. Preparamos el CUIT con guiones porque así aparece en el HTML de AFIP
    cuit_fmt = _formato_cuit_visual(cuit_destino)
    
    print(f"[INFO] Buscando empresa con CUIT: {cuit_fmt}")

    # 2. Armamos un XPath que busque un DIV con clase 'media' 
    #    que tenga dentro un SMALL con ese CUIT.
    #    La estructura es: <div class="media"> ... <small>[CUIT XX-XX-X]</small> ... </div>
    xpath_tarjeta = f"//div[contains(@class, 'media') and .//small[contains(., '{cuit_fmt}')]]"

    # 3. Intentamos hacer clic
    try:
        # Usamos tu herramienta de click seguro
        ct._click_element_by(dv, By.XPATH, xpath_tarjeta, timeout=5)
        return True
    except Exception as e:
        print(f"[ERROR] No se encontró la empresa con CUIT {cuit_fmt}: {e}")
        return False

def obtener_representado_actual_portal_iva(dv):
    """
    Detecta y devuelve el nombre del contribuyente que figura en la barra superior
    del Portal IVA ("Representando a: ...").
    """
    xpath_texto = "//span[contains(@class, 'text-uppercase') and contains(., 'Representando a:')]"
    
    try:
        # Usamos tu herramienta para esperar que el elemento exista
        elemento = ct._wait_for_page_ready(dv, "elemento", 5, By.XPATH, xpath_texto, returnable=True)
        
        # Obtenemos el texto completo (Ej: "Representando a: JUAN PEREZ [20-12345678-9]")
        texto_completo = elemento.text
        
        # Opcional: Limpiamos para devolver solo lo importante si quieres
        print(f"[INFO] {texto_completo}") 
        return texto_completo

    except Exception as e:
        print("[WARN] No se pudo detectar a quién se está representando en Portal IVA.")
        return None

# === Funcion auxiliar para registrar errores en comprobantes ===

def registrar_resultado_comprobantes(estado, clave, resultados):
    """
    Registra el resultado de la descarga de comprobantes.
    Usa .get() para evitar KeyErrors si solo se buscó Excel o solo CSV.
    """
    # Si la clave existe Y su valor es "OK"
    excel_ok = (resultados.get("Excel") == "OK")
    csv_ok = (resultados.get("CSV") == "OK")
    
    ok = excel_ok or csv_ok

    if ok:
        set_estado(estado, clave, "OK")
    else:
        # Si falla, mostramos los estados de las claves que sí se buscaron
        fallo = f"Excel: {resultados.get('Excel', 'NO BUSCADO')} - CSV: {resultados.get('CSV', 'NO BUSCADO')}"
        set_estado(estado, clave, "ERROR", fallo)

# === Descargar comprobantes ===

def buscar_descargar(dv, xpath, velocidad, formatos=["Excel", "CSV"]): # <-- Acepta formatos
    """
    Realiza el flujo de búsqueda y descarga de comprobantes para una sección específica.
    """
    ct._click_element_by(dv, By.XPATH, xpath)
    pausa(velocidad)
    ct._click_element_by(dv, By.ID, "btnCalendarioFechaEmision")
    pausa(velocidad)
    ct._click_element_by(dv, By.CSS_SELECTOR, "li[data-range-key='Mes Pasado']")
    pausa(velocidad)
    ct._click_element_by(dv, By.ID, "buscarComprobantes")
    pausa(velocidad)
    # Pasa el formato o formatos que se desean descargar
    return ct._click_span_descarga(dv, formatos=formatos) # <-- Pasa formatos

def descargar_comprobantes(dv, usuario, estado, velocidad=1):
    """
    Descarga los comprobantes filtrando Compras para Monotributistas.
    """
    
    condicion = usuario.get('tipo_monotributo', 'Monotributo')
    secciones = ["Emitidos", "Recibidos"]
    
    print(f"[INFO] Aplicando lógica de descarga para condición: {condicion}")

    for titulo in range(len(secciones)):
        pausa(velocidad)
        tipo_comprobante = secciones[titulo]
        
        # --- MODIFICACIÓN CLAVE AQUÍ ---
        # Si estamos en 'Recibidos' Y el usuario tiene 'Monot' en su condición
        # (cubre "Monotributo", "Monot. Unificado", "Monot. Convenio"),
        # saltamos esta iteración y no descargamos nada.
        if tipo_comprobante == "Recibidos" and "Monot" in condicion:
            print(f"[INFO] Omitiendo descarga de Compras (Recibidos) para {condicion}")
            continue
        # -------------------------------

        xpath = f"//h3[normalize-space(text())='{tipo_comprobante}']"
        formatos_a_bajar = []

        if tipo_comprobante == "Emitidos": # VENTAS
            if condicion in ["Resp. Inscripto", "Monot. Convenio"]:
                formatos_a_bajar = ["CSV"]
            elif condicion == "Monot. Unificado":
                formatos_a_bajar = ["Excel"]
            else:
                formatos_a_bajar = ["Excel"] 
        
        else: # RECIBIDOS / COMPRAS
            # Si llegó hasta acá, es porque NO es Monotributista (gracias al filtro de arriba)
            # o es RI, así que bajamos Excel.
            formatos_a_bajar = ["Excel"]

        # Ejecutamos la búsqueda y descarga
        resultados = buscar_descargar(dv, xpath, velocidad, formatos=formatos_a_bajar)

        if tipo_comprobante == "Emitidos":
            registrar_resultado_comprobantes(estado, "comprobantes_emitidos", resultados)
            tn.retroceder_paginas(dv)
        else:
            registrar_resultado_comprobantes(estado, "comprobantes_recibidos", resultados)
            pausa(velocidad)
  
# === Navegación a "Mis Retenciones" ===

def ingresar_mis_retenciones(dv):
    """
    Hace clic en la sección "MIS RETENCIONES" del portal AFIP.

    Args:
        dv (webdriver): Driver de Selenium.
    """
    ct._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='MIS RETENCIONES']")
    
    # ct._click_element_by(dv, By.ID, "__EVID__481888__EV__e-button__")
    # ct._click_element_by(dv, By.XPATH, "//button[contains(., 'click aquí')]")
    # ct._click_element_by(dv, By.CSS_SELECTOR, "button.e-button")

def hay_retenciones_renderizadas(dv):
    """
    Devuelve True si la tabla/lista de resultados de retenciones contiene datos.
    Devuelve False si aparece un mensaje tipo 'No se encontraron resultados'.
    """
    try:
        # Este texto aparece en la nueva versión cuando NO hay datos
        xpath_no = "//h4[contains(normalize-space(.), 'No hay resultados para tu consulta')]"

        elementos = dv.find_elements(By.XPATH, xpath_no)
        if len(elementos) > 0:
            return False

        # Si existe una tabla con filas, entonces hay datos
        filas = dv.find_elements(By.CSS_SELECTOR, "table tbody tr")
        return len(filas) > 0

    except Exception:
        return False

def descarga_retenciones(dv, cuit, velocidad=1, estado=None):
    """
    Inicia el proceso de descarga de retenciones para un CUIT específico.
    Si no encuentra retenciones, lo marca en estado (si se pasó) y continúa.
    """

    for i in range(2):
        ct._wait_for_page_ready(dv, modo="clickeable", by=By.ID, identifier='btnConsultarRetenciones')
        pausa(velocidad)

        # Selección de impuesto
        impuesto = "216" if i == 0 else "767"
        ct._write_input(dv, "selectImpuestos", impuesto)
        ct._write_input(dv, "cuitAgenteRetencion", cuit)

        if i == 1:
            ct._click_element_by(dv, By.XPATH, '//label[contains(text(), "Retención y percepción")]')

        # Selección de rango de fechas
        primer_dia, ultimo_dia = obtener_fechas_mes_pasado_formato_ddMMAAAA()

        pausa(velocidad)
        ct._write_input_force(dv, "datePickerFechasRetencionesDesde__input", primer_dia, press_enter=False)
        pausa(velocidad)
        ct._write_input_force(dv, "datePickerFechasRetencionesHasta__input", ultimo_dia, press_enter=False)
        pausa(velocidad)

        # Consultar
        ct._click_element_by(dv, By.ID, 'btnConsultarRetenciones')
        pausa(velocidad)

        # 1) ❗ Detectar si no hay datos
        if not hay_retenciones_renderizadas(dv):
            msg = f"No hay retenciones para impuesto {impuesto} (CUIT {cuit})"
            print("[INFO]", msg)

            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "OK", "Sin datos")
            if i == 0:
                boton = "btnNuevaBusqueda"
                ct._click_element_by(dv, By.ID, boton, 4)
                
            # Dejamos que la función que llama decida si retroceder o no
            continue

        # 2) Si hay datos → intentar descarga
        try:
            ct._click_span_descarga(dv, type="Retenciones")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "OK")
        except Exception as e:
            print(f"[ERROR] No se pudo descargar retenciones para {impuesto}: {e}")
            if estado is not None:
                set_estado(estado, f"retenciones_{impuesto}", "ERROR", str(e))


# === Seccion de funciones Portal_IVA ===

def portal_iva_disponible(dv, timeout=2):
    """
    Devuelve True si el Portal IVA cargó correctamente
    buscando un botón exclusivo del sistema.
    """
    ct.wait_until_page_loaded(dv)
    try:
        WebDriverWait(dv, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[aria-label="Sin texto (iva.home.btn.nueva.declaracion.alt)"]')
            )
        )
        return True
    except:
        return False

def ingresar_Portal_IVA(dv):
    # Intento de click en el menú PORTAL IVA
    try:
        ct._click_element_by(dv, By.XPATH, "//h3[normalize-space(text())='PORTAL IVA']")
        return True
    except:
        print("[INFO] Portal IVA no figura en el menú.")
        return False

def descargar_libro_IVA(dv, usuario, ruta, velocidad=1, estado=None):
    ct.wait_until_page_loaded(dv)
    ct._click_element_by(dv, By.CSS_SELECTOR, 'button[aria-label="Sin texto (iva.home.btn.nueva.declaracion.alt)"]')
    pausa(velocidad/3)
    ct.seleccionar_opcion_por_value(dv, 'select[name="periodo"]', obtener_mes_anterior())
    pausa(velocidad/3)
    ct._click_element_by(dv, By.CSS_SELECTOR, 'button[aria-label="Sin texto (iva.btn.home.validar.periodo.alt)"]')
    pausa(velocidad/3)
    ct._click_element_by(dv, By.CSS_SELECTOR, 'button[aria-label="Sin texto (iva.btn.home.liva.alt)"]')
    pausa(velocidad/3)

    #DEBUG: SALTEAR IMPORTACIÓN
    debug_saltar_importacion = True
    if debug_saltar_importacion:
        print("[DEBUG] Saltando importación de datos en Portal IVA (modo debug).")
    else:
        secciones = ["Ventas", "Compras"]
        for seccion in secciones:
            if seccion == "Ventas":
                ct._click_element_by(dv, By.ID, f'btnLibroVentas')
                pausa(velocidad/3)
            # ct._click_element_by(dv, By.ID, 'btnDropdownImportar')
            # pausa(velocidad/3)
            ct._click_element_by(dv, By.ID, 'lnkImportarAFIP')
            pausa(velocidad/3)
            ct._click_element_by(dv, By.ID, 'btnImportarAFIPImportar')
            pausa(velocidad/3)
            ct._click_element_by(dv, By.ID, 'btnTareasCerrar')
            pausa(velocidad/3)
            ct._click_span_descarga(dv)
            pausa(velocidad/3)
            if seccion == "Ventas":
                ct._click_element_by(dv, By.CSS_SELECTOR, 'a[href="verCompras.do?t=21"]')
    
    ct._click_element_by(dv, By.CSS_SELECTOR, 'a[href="menuPresentacion.do"]')
    pausa(velocidad/3)
    ct._click_element_by(dv, By.ID, 'btnVistaPrevia')
    pausa(velocidad/3)
    ruta_descarga_chrome = ruta + f"\\{usuario['nombre']}"
    guardar_pdf_en_ruta(dv, ruta_descarga_chrome, f"LibroIVA_{usuario['nombre']}.pdf")