"""
runner/programas.py
-------------------
Flujos de alto nivel para cada programa: Comprobantes, Retenciones y Portal IVA.
Cada función de 'programa_*' representa una ejecución completa de inicio a fin
para un único usuario.
"""

import logger
import tools
import tab_navigation as tn
from browser import driver as drv
from browser import login as lgn
from browser.actions import _click_element_by
from selenium.webdriver.common.by import By
from estado_usuario import set_estado
import afip.comprobantes as comp
import afip.retenciones as ret
import afip.portal_iva as iva


# ---------------------------------------------------------------------------
# Helpers comunes
# ---------------------------------------------------------------------------

def _return_to_original_window(dv, original_window):
    """Devuelve el foco a la pestaña original."""
    dv.switch_to.window(original_window)


@logger.debug_trace
def login(usuario, ruta, estado, velocidad):
    """
    Abre Chrome, navega a AFIP e inicia sesión con las credenciales del usuario.

    Args:
        usuario (dict): Datos del usuario con 'nombre', 'cuit' y 'password'.
        ruta (str): Carpeta base de descargas (sin el subdirectorio del usuario).
        estado (dict): Estado del usuario para registrar el resultado del login.
        velocidad (int/float): Factor de velocidad para pausas.

    Returns:
        webdriver.Chrome: Driver con sesión iniciada.

    Raises:
        Exception: Si el login falla, para que el llamador lo maneje.
    """
    ruta_descarga_chrome = ruta + f"\\{usuario['nombre']}"
    dv = drv.open_chrome(ruta_descarga_chrome)
    tools.pausa(velocidad)

    ok_login = _login_afip(dv, usuario['cuit'], usuario['password'], velocidad, estado)
    if not ok_login:
        print(f"[INFO] Login falló para {usuario['nombre']}, se salta al siguiente.")
        raise Exception("Fallo en login: no se pudo iniciar sesión")

    return dv


def _login_afip(dv, user, password, velocidad, estado):
    """
    Wrapper que ejecuta el login y registra el resultado en el estado.

    Returns:
        bool: True si el login fue exitoso.
    """
    try:
        lgn._login_user(dv, user, password, velocidad)
        set_estado(estado, "login", "OK")
    except Exception as e:
        mensaje = str(e)
        if "Cambio obligatorio de contraseña" in mensaje:
            set_estado(estado, "login", "ERROR", "El usuario debe cambiar la contraseña")
        elif "Login incorrecto" in mensaje:
            set_estado(estado, "login", "ERROR", "CUIT o contraseña incorrecta")
        else:
            set_estado(estado, "login", "ERROR", f"Excepción: {mensaje}")
        return False
    return True


def _pausa_y_servicios(dv, velocidad):
    """
    Pausa breve y navega al menú de servicios de AFIP.

    Returns:
        str: Handle de la pestaña original (antes de abrir nuevas ventanas).
    """
    tools.pausa(velocidad)
    _click_element_by(dv, By.CSS_SELECTOR, "a[href='/portal/app/mis-servicios']")
    tools.pausa(velocidad)
    return dv.current_window_handle


# ---------------------------------------------------------------------------
# Secciones — Comprobantes
# ---------------------------------------------------------------------------

@logger.debug_trace
def _seccion_comprobantes_empresa(dv, usuario, estado, velocidad):
    """Descarga comprobantes para cada empresa asociada al usuario."""
    empresas = comp.encontrar_empresas(dv)
    for i in range(len(empresas)):
        empresas = comp.encontrar_empresas(dv)
        comp.seleccionar_empresa(dv, empresas[i])
        tools.pausa(velocidad)
        comp.descargar_comprobantes(dv, usuario, estado, velocidad)
        tn.retroceder_paginas(dv, 2)


@logger.debug_trace
def _seccion_comprobantes_personales(dv, usuario, estado, velocidad):
    """Descarga comprobantes del propio contribuyente."""
    comp.descargar_comprobantes(dv, usuario, estado, velocidad)


@logger.debug_trace
def _seccion_mis_comprobantes(dv, usuario, estado, original_window, velocidad, sociedades=False):
    """
    Entra a 'Mis Comprobantes', cambia de ventana y ejecuta la descarga
    según si el usuario tiene sociedades o no.
    """
    comp.ingresar_mis_comprobantes(dv)
    drv.change_window(dv, estado, original_window)

    if sociedades:
        _seccion_comprobantes_empresa(dv, usuario, estado, velocidad)
    else:
        _seccion_comprobantes_personales(dv, usuario, estado, velocidad)


# ---------------------------------------------------------------------------
# Secciones — Retenciones
# ---------------------------------------------------------------------------

@logger.debug_trace
def _seccion_mis_retenciones(dv, estado, original_window, cuit, velocidad):
    """
    Entra a 'Mis Retenciones', cambia de ventana, descarga y cierra la pestaña.
    """
    ret.ingresar_mis_retenciones(dv)
    tools.pausa(velocidad)
    drv.change_window(dv, estado, original_window)
    ret.descarga_retenciones(dv, cuit, velocidad, estado)
    tn.cerrar_pestana_actual(dv)
    _return_to_original_window(dv, original_window)


# ---------------------------------------------------------------------------
# Secciones — Portal IVA
# ---------------------------------------------------------------------------

@logger.debug_trace
def _seccion_portal_iva_personales(dv, usuario, ruta, estado, velocidad):
    """Descarga el Libro IVA del contribuyente personal."""
    iva.descargar_libro_IVA(dv, usuario, ruta, velocidad, estado)


@logger.debug_trace
def _seccion_portal_iva_empresa(dv, usuario, ruta, estado, velocidad):
    """Descarga el Libro IVA de la(s) sociedad(es) asociada(s) al usuario."""
    iva.obtener_representado_actual_portal_iva(dv)

    if len(usuario['sociedades']) > 0:
        from browser.actions import click_cambiar_representado_portal_iva
        click_cambiar_representado_portal_iva(dv)
        iva.seleccionar_empresa_portal_iva(dv, usuario['sociedades'][0]['cuit'])
        _seccion_portal_iva_personales(dv, usuario, ruta, estado, velocidad)
        tn.retroceder_paginas(dv)


@logger.debug_trace
def _seccion_portal_iva(dv, usuario, ruta, estado, original_window, velocidad, sociedades=False):
    """
    Entra al Portal IVA, verifica disponibilidad y ejecuta la descarga.
    Cierra el driver al finalizar.
    """
    if not iva.ingresar_Portal_IVA(dv):
        print("[INFO] Saltando sección Portal IVA porque no está disponible.")
        return

    drv.change_window(dv, estado, original_window)

    if not iva.portal_iva_disponible(dv):
        print("[INFO] Portal IVA no está habilitado o no cargó correctamente.")
        tn.cerrar_pestana_actual(dv)
        _return_to_original_window(dv, original_window)
        return

    if sociedades:
        _seccion_portal_iva_empresa(dv, usuario, ruta, estado, velocidad)
    else:
        _seccion_portal_iva_personales(dv, usuario, ruta, estado, velocidad)

    dv.quit()


# ---------------------------------------------------------------------------
# Programas principales (punto de entrada por programa)
# ---------------------------------------------------------------------------

@logger.debug_trace
def programa_Comprobantes(usuario, ruta, estado, velocidad=1):
    """
    Flujo completo: abre Chrome → login → descarga Mis Comprobantes → cierra.

    Args:
        usuario (dict): Datos del usuario.
        ruta (str): Carpeta base de descargas.
        estado (dict): Estado del usuario.
        velocidad (int/float): Factor de velocidad.
    """
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return

    original_window = _pausa_y_servicios(dv, velocidad)
    tiene_sociedades = len(usuario['sociedades']) > 0
    _seccion_mis_comprobantes(dv, usuario, estado, original_window, velocidad, sociedades=tiene_sociedades)

    dv.quit()


@logger.debug_trace
def programa_Retenciones(usuario, ruta, estado, velocidad=1):
    """
    Flujo completo: abre Chrome → login → descarga Mis Retenciones → cierra.
    """
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return

    original_window = _pausa_y_servicios(dv, velocidad)
    _seccion_mis_retenciones(dv, estado, original_window, usuario['cuit'], velocidad)

    dv.quit()


@logger.debug_trace
def programa_Portal_IVA(usuario, ruta, estado, velocidad=1):
    """
    Flujo completo: abre Chrome → login → descarga Portal IVA → cierra.
    """
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return

    original_window = _pausa_y_servicios(dv, velocidad)
    tiene_sociedades = len(usuario['sociedades']) > 0
    _seccion_portal_iva(dv, usuario, ruta, estado, original_window, velocidad, tiene_sociedades)
    # Nota: dv.quit() ya se ejecuta dentro de _seccion_portal_iva
