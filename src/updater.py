"""
updater.py
----------
Módulo de actualización remota, autocontenido y REUTILIZABLE: no importa nada de
este proyecto, así que se puede copiar tal cual a cualquier programa (ARCA,
Cronos, etc.). Solo usa la librería estándar de Python.

Flujo de check_for_updates():
  1. Lee un manifiesto JSON remoto (por URL) con la última versión disponible.
  2. Lo compara contra la versión local.
  3. Si hay una más nueva, pide confirmación, descarga el nuevo .exe y verifica
     su hash SHA-256.
  4. Aplica el reemplazo en Windows: un .exe en ejecución no puede sobrescribirse
     a sí mismo, así que se escribe un .bat que espera a que el programa cierre,
     reemplaza el viejo por el nuevo y relanza; luego se lanza ese .bat y se
     cierra el programa.

Pensado para un ejecutable empaquetado (PyInstaller / auto-py-to-exe, one-file).
En modo desarrollo (corriendo como .py) detecta que no hay .exe y no hace el
reemplazo.

Formato esperado del manifiesto (JSON):
    {
        "version":   "2.2.6",
        "url":       "https://.../arca_2.2.6.exe",
        "sha256":    "<hash sha-256 del exe, en hex>",
        "changelog": "Qué cambió en esta versión"
    }
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
import urllib.request


# ---------------------------------------------------------------------------
# Manifiesto y comparación de versiones
# ---------------------------------------------------------------------------

def _leer_manifiesto(url, timeout=15):
    """Descarga y parsea el manifiesto JSON remoto. Devuelve dict o None."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[Update] No se pudo leer el manifiesto: {e}")
        return None


def _a_tupla(v):
    """'2.2.10' -> (2, 2, 10). Ignora lo no numérico para poder comparar."""
    partes = []
    for x in str(v).strip().split("."):
        num = "".join(ch for ch in x if ch.isdigit())
        partes.append(int(num) if num else 0)
    return tuple(partes)


def _hay_version_nueva(actual, remota):
    """True si 'remota' es estrictamente mayor que 'actual'."""
    return _a_tupla(remota) > _a_tupla(actual)


# ---------------------------------------------------------------------------
# Descarga y verificación
# ---------------------------------------------------------------------------

def _descargar(url, destino, timeout=60):
    """Descarga 'url' a 'destino'. Devuelve True si salió bien."""
    try:
        print("[Update] Descargando la nueva versión...")
        with urllib.request.urlopen(url, timeout=timeout) as r, open(destino, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"[Update] Falló la descarga: {e}")
        return False


def _sha256(archivo):
    """Devuelve el SHA-256 (hex) de un archivo, leyéndolo por bloques."""
    h = hashlib.sha256()
    with open(archivo, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Aplicación de la actualización (Windows, .exe one-file)
# ---------------------------------------------------------------------------

def _aplicar_actualizacion_windows(nuevo_exe):
    """
    Reemplaza el .exe actual por 'nuevo_exe' y relanza, mediante un .bat que
    espera a que este proceso cierre. Cierra el programa al final (os._exit),
    para que el ejecutable quede libre y se pueda sobrescribir.
    """
    exe_actual = sys.executable
    exe_nombre = os.path.basename(exe_actual)
    bat = os.path.join(tempfile.gettempdir(),
                       os.path.splitext(exe_nombre)[0] + "_update.bat")

    # El .bat: espera a que el proceso desaparezca, reemplaza el exe, relanza y
    # se borra a sí mismo.
    contenido = (
        "@echo off\r\n"
        f"echo Actualizando {exe_nombre}, no cierres esta ventana...\r\n"
        ":esperar\r\n"
        f'tasklist /fi "imagename eq {exe_nombre}" 2>nul | find /i "{exe_nombre}" >nul\r\n'
        "if not errorlevel 1 (\r\n"
        "    timeout /t 1 /nobreak >nul\r\n"
        "    goto esperar\r\n"
        ")\r\n"
        f'move /y "{nuevo_exe}" "{exe_actual}" >nul\r\n'
        f'start "" "{exe_actual}"\r\n'
        'del "%~f0"\r\n'
    )
    with open(bat, "w", encoding="utf-8") as f:
        f.write(contenido)

    print("[Update] Cerrando el programa para aplicar la actualización...")
    subprocess.Popen(["cmd", "/c", bat],
                     creationflags=subprocess.CREATE_NEW_CONSOLE,
                     close_fds=True)
    os._exit(0)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def check_for_updates(program_id, version_actual, url_manifiesto):
    """
    Chequea si hay una versión más nueva y, si el usuario acepta, la instala.

    Args:
        program_id (str): Identificador del programa (ej. 'arca').
        version_actual (str): Versión de este build (ej. '2.2.5').
        url_manifiesto (str): URL del manifiesto JSON con la última versión.
    """
    if not url_manifiesto:
        print("[Update] No hay URL de manifiesto configurada (ver version.py).")
        return

    print(f"[Update] Buscando actualizaciones de '{program_id}' "
          f"(versión actual {version_actual})...")

    manifiesto = _leer_manifiesto(url_manifiesto)
    if not manifiesto:
        return

    version_remota = manifiesto.get("version", "")
    url_exe        = manifiesto.get("url", "")
    hash_esperado  = manifiesto.get("sha256", "")
    changelog      = manifiesto.get("changelog", "")

    if not _hay_version_nueva(version_actual, version_remota):
        print(f"[Update] Ya tenés la última versión ({version_actual}).")
        return

    print(f"\n[Update] Hay una nueva versión disponible: {version_remota} "
          f"(tenés la {version_actual}).")
    if changelog:
        print(f"[Update] Novedades: {changelog}")

    # Si no corremos como .exe empaquetado, no hay reemplazo posible.
    if not getattr(sys, "frozen", False):
        print("[Update] Estás en modo desarrollo (no .exe): no se aplica el "
              "reemplazo automático. Actualizá el código manualmente.")
        return

    if not url_exe:
        print("[Update] El manifiesto no trae la URL del ejecutable.")
        return

    respuesta = input("¿Descargar e instalar ahora? (s/n): ").strip().lower()
    if respuesta not in ("s", "si", "sí", "y", "yes"):
        print("[Update] Actualización pospuesta.")
        return

    destino = os.path.join(tempfile.gettempdir(),
                           f"{program_id}_{version_remota}.exe")
    if not _descargar(url_exe, destino):
        return

    # Verificación de integridad: clave porque estamos bajando un ejecutable.
    if hash_esperado:
        real = _sha256(destino)
        if real.lower() != hash_esperado.lower():
            print("[Update] ¡El hash NO coincide! Descarga corrupta o alterada. "
                  "Se cancela por seguridad.")
            try:
                os.remove(destino)
            except OSError:
                pass
            return
        print("[Update] Hash SHA-256 verificado OK.")
    else:
        print("[Update] (Aviso: el manifiesto no trae 'sha256'; no se pudo "
              "verificar la integridad del archivo descargado.)")

    _aplicar_actualizacion_windows(destino)
