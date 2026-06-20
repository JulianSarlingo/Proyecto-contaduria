"""
browser/login.py
----------------
Lógica de autenticación en el portal de AFIP.
"""

from selenium.webdriver.common.by import By
from browser.actions import _wait_for_page_ready, _write_input
from logger import log_error
import tools


def detectar_error_login(dv):
    """
    Detecta si hay un mensaje de error de credenciales en la pantalla de login.

    Returns:
        bool: True si se detectó un error de login.
    """
    try:
        error_xpath = "//span[contains(text(), 'incorrecto') or contains(text(), 'incorrecta')]"
        errores = dv.find_elements(By.XPATH, error_xpath)
        return len(errores) > 0
    except Exception:
        return False


def detectar_cambio_clave(dv):
    """
    Detecta si AFIP exige un cambio obligatorio de contraseña.

    Returns:
        bool: True si se detectó la pantalla de cambio de clave.
    """
    patrones = [
        "//h4[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cambiar clave fiscal')]",
        "//span[@id='F1:msg']",
    ]
    for xp in patrones:
        try:
            _wait_for_page_ready(dv, "elemento", 1, By.XPATH, xp, silent=True)
            return True
        except Exception:
            pass
    return False


def _login_user(dv, user, password, velocidad):
    """
    Completa el formulario de login en AFIP.

    Args:
        dv: WebDriver con la página de login abierta.
        user (str): CUIT del usuario.
        password (str): Contraseña del usuario.
        velocidad (int/float): Factor de velocidad para pausas.

    Raises:
        Exception: Si se detecta cambio obligatorio, login incorrecto u otro error.
    """
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
        raise
