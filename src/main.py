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

from logging import config
import os
from os import system

import tools
import logger
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
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."


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

def verificar_aprobacion():
    """
    Verifica que el dispositivo tenga licencia activa para usar el programa.

    Flujo:
        1. Licencia autorizada  → retorna True.
        2. Solicitud pendiente  → informa y retorna False.
        3. Sin solicitud        → crea solicitud y retorna False.

    Returns:
        bool: True si el dispositivo está autorizado.
    """
    hwid = licencia.obtener_hwid()

    if licencia.licencia_autorizada(hwid):
        print("✔ Licencia autorizada. Iniciando programa...")
        return True

    print("❌ Licencia no autorizada.")

    if licencia.solicitud_existente(hwid):
        print("⚠ Ya existe una solicitud pendiente. Espere aprobación.")
        return False

    print("Por favor, ingrese un nombre con el que el desarrollador pueda identificar este PC.")
    nombre = input("Ingrese un nombre: ")
    licencia.crear_solicitud(hwid, nombre)
    print("✔ Solicitud enviada. Espere la aprobación.")
    return False


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

def main():
    """Carga la configuración e inicia el procesamiento de todos los usuarios."""
    ruta, velocidad, sheet_name, modo = extraer_configuracion('config.txt')
    ruta, config = tools.init(ruta, sheet_name)
    

    # --- Opciones de prueba (descomentar según necesidad) ---
    # base_dir = os.path.dirname(ruta) + "\\Datos Afip"
    # probar_usuario_manual(base_dir, velocidad, modo)
    # probar_usuario(config, 40, ruta, velocidad, modo) #
    #  
    # Probar usuarios específicos para Mis comprobantes:
    # config2 = [config[155], config[124], config[127], config[164], config[101]]
    # probar_usuario()
    # probar_usuario(config, 40-1, ruta, velocidad, "Comprobantes") # Dicuzzo Fernando Nicolas
    # probar_usuario(config, 124-1, ruta, velocidad, "Comprobantes") # Vera Nilda Ignacia
    # probar_usuario(config, 127-1, ruta, velocidad, "Comprobantes") # Viviani Clarisa
    # probar_usuario(config, 164-1, ruta, velocidad, "Comprobantes") # Morteo Maria Ignacio
    # probar_usuario(config, 101-1, ruta, velocidad, "Comprobantes") # Peralta Maximiliano Gaston

    # probar_rango(config2, [3, 10], ruta, velocidad, "Comprobantes")
    # extraer_informacion(config)

    ejecutar_codigo(config, ruta, velocidad, "Retenciones")


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

if __name__ == '__main__':
    logger.iniciar_proteccion()
    principal(modo_prueba=True)
    system('pause')