"""
main.py
-------
Punto de entrada del programa.

Antes de empezar, recordá mantener el repo sincronizado:
    git pull origin main          # traer cambios
    git status                    # ver diferencias
    git add . && git commit -m "mensaje" && git push origin main

Para generar el ejecutable:
    .\\venv_nuevo\\Scripts\\auto-py-to-exe.exe
"""

import os
from os import system

import keyboard

import tools
import logger
import menu
from browser import driver as drv
from runner.ejecutor import ejecutar_codigo, probar_usuario, probar_rango, probar_usuario_manual
from estado_usuario import nuevo_estado, set_estado, imprimir_estado
from Seguridad import licencia


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

def extraer_configuracion(nombre_archivo):
    """
    Lee el archivo config.txt y extrae los parámetros del programa.

    Args:
        nombre_archivo (str): Ruta al archivo de configuración.

    Returns:
        tuple: (ruta, velocidad, sheet_name, modo)
    """
    ruta       = ''
    velocidad  = 1
    sheet_name = ''
    modo       = ''

    try:
        with open(nombre_archivo, 'r') as archivo:
            for linea in archivo:
                linea = linea.strip()
                if linea.startswith('ruta ='):
                    ruta = linea.split('=', 1)[1].strip()
                elif linea.startswith('hoja ='):
                    sheet_name = linea.split('=', 1)[1].strip()
                elif linea.startswith('modo ='):
                    modo = linea.split('=', 1)[1].strip()
        return ruta, velocidad, sheet_name, modo

    except FileNotFoundError:
        # Antes se devolvía un string acá, pero main() desempaqueta 4 valores
        # (ruta, velocidad, sheet_name, modo) -> daba un ValueError críptico.
        # Lanzamos un error claro que la protección global (excepthook) muestra
        # al usuario en el messagebox de logger.
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración '{nombre_archivo}'. "
            f"Verificá que exista junto al programa."
        )


def extraer_informacion(config):
    """
    Genera un reporte de depuración con todos los usuarios cargados.
    Escribe el resultado en 'depuracion_usuarios.txt'.

    Args:
        config (list): Lista de usuarios generada por tools.init().
    """
    try:
        with open("depuracion_usuarios.txt", "w", encoding="utf-8") as f:
            f.write("=== REPORTE DE DEPURACIÓN DE USUARIOS ===\n")
            f.write(f"Total de usuarios encontrados: {len(config)}\n")
            f.write("-" * 40 + "\n")

            for usuario in config:
                nombre    = usuario.get('nombre', 'N/A')
                cuit      = usuario.get('cuit', 'N/A')
                password  = usuario.get('password', 'N/A')
                tipo      = usuario.get('tipo_monotributo', 'N/A')
                sociedades = usuario.get('sociedades', 'N/A')

                linea = (f"Nombre: {nombre}, CUIT: {cuit}, "
                         f"Contraseña: {password}, Tipo: {tipo}, Sociedades: {sociedades}")
                print(linea)
                f.write(linea + "\n")

            f.write("-" * 40 + "\n")
            f.write("Fin del reporte.")

        print("\n[OK] Se ha generado 'depuracion_usuarios.txt' con éxito.")

    except Exception as e:
        print(f"[ERROR] No se pudo generar el archivo de depuración: {e}")


# ---------------------------------------------------------------------------
# Licencia
# ---------------------------------------------------------------------------

# Nombre de este programa dentro del esquema de licencias por
# programa (ver Seguridad/firestore.py). Este repo es ARCA Downloader
# (confirmado por el título de los diálogos de error en logger.py).
PROGRAMA = "arca"


def verificar_aprobacion():
    """
    Verifica que este equipo tenga licencia activa para PROGRAMA
    ("arca"). La licencia ahora es por programa individual, no por
    equipo completo: un HWID autorizado para Cronos ya no habilita
    automáticamente ARCA Downloader, y viceversa.

    Flujo:
        1. Licencia autorizada  → retorna True.
        2. Solicitud pendiente  → informa y retorna False.
        3. Sin solicitud        → crea solicitud y retorna False.

    Returns:
        bool: True si el dispositivo está autorizado para PROGRAMA.
    """
    hwid = licencia.obtener_hwid()

    if licencia.licencia_autorizada(hwid, PROGRAMA):
        print("✔ Licencia autorizada. Iniciando programa...")
        return True

    print("❌ Licencia no autorizada.")

    if licencia.solicitud_existente(hwid, PROGRAMA):
        print("⚠ Ya existe una solicitud pendiente. Espere aprobación.")
        return False

    print("Por favor, ingrese un nombre con el que el desarrollador pueda identificar este PC.")
    nombre = input("Ingrese un nombre: ")
    licencia.crear_solicitud(hwid, nombre, PROGRAMA)
    print("✔ Solicitud enviada. Espere la aprobación.")
    return False


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

def main():
    """Carga la configuración e inicia el menú interactivo."""
    ruta, velocidad, sheet_name, modo = extraer_configuracion('config.txt')

    # --- Opciones de prueba manual (descomentar según necesidad) ---
    # Siguen disponibles; corren un usuario/rango puntual sin pasar por el menú.
    # base_dir, config = tools.init(ruta, sheet_name)
    # probar_usuario_manual(base_dir, velocidad, "Comprobantes")
    # probar_usuario(config, 40, base_dir, velocidad, "Comprobantes")   # Dicuzzo Fernando Nicolas
    # probar_usuario(config, 124, base_dir, velocidad, "Comprobantes")  # Vera Nilda Ignacia
    # probar_usuario(config, 127, base_dir, velocidad, "Comprobantes")  # Viviani Clarisa
    # probar_rango(config, [3, 10], base_dir, velocidad, "Comprobantes")
    # extraer_informacion(config)

    # Menú: 1) Ejecutar  2) Actualizar Excel  3) Chequear actualizaciones
    menu.iniciar(ruta, velocidad, sheet_name)


def principal(modo_prueba):
    """
    Punto de entrada condicional: ejecuta sin verificación de licencia
    en modo prueba, o verifica licencia antes de ejecutar.
    """
    if modo_prueba:
        main()
    elif verificar_aprobacion():
        main()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _configurar_tecla_panico(combinacion="ctrl+shift+q"):
    """
    Registra una tecla de pánico GLOBAL: al presionarla (desde cualquier
    ventana) cierra todos los Chrome abiertos y mata el programa al instante.
    """
    def _panico():
        print("\n[PÁNICO] Cerrando todos los Chrome y terminando el programa...")
        drv.cerrar_todos_los_chrome()
        os._exit(1)  # corte inmediato: no esperamos a los hilos

    try:
        keyboard.add_hotkey(combinacion, _panico)
        print(f"[INFO] Tecla de pánico activa: '{combinacion.upper()}' "
              f"cierra todo y mata el programa.")
    except Exception as e:
        print(f"[WARN] No se pudo activar la tecla de pánico ({e}).")


if __name__ == '__main__':
    logger.iniciar_proteccion()
    _configurar_tecla_panico()
    principal(modo_prueba=False)
    system('pause')