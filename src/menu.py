"""
menu.py
-------
Menú interactivo por consola. Permite:
    1) Ejecutar el programa (con submenú para elegir el modo).
    2) Actualizar el Excel (releer y regenerar el caché .json).
    3) Chequear actualizaciones (stub, ver updater.py).
    0) Salir.
"""

import tools
import updater
import version
from runner.ejecutor import ejecutar_codigo

# Mapea la opción del submenú al modo que entiende ejecutar_codigo.
_MODOS = {
    "1": "Comprobantes",
    "2": "Retenciones",
    "3": "PortalIVA",
}


def _leer_opcion(prompt, validas):
    """
    Pide una opción por teclado hasta que sea una de las válidas.

    Args:
        prompt (str): Texto a mostrar.
        validas (set): Conjunto de strings aceptados.

    Returns:
        str: La opción elegida (garantizada dentro de 'validas').
    """
    while True:
        opcion = input(prompt).strip()
        if opcion in validas:
            return opcion
        print(f"[ERROR] Opción inválida: '{opcion}'. Elegí una de {sorted(validas)}.")


def _submenu_modo():
    """
    Muestra el submenú de modos.

    Returns:
        str | None: El modo elegido ('Comprobantes'/'Retenciones'/'PortalIVA'),
        o None si el usuario elige volver.
    """
    print("\n--- ¿Qué querés descargar? ---")
    print("  1) Comprobantes")
    print("  2) Retenciones")
    print("  3) Portal IVA")
    print("  0) Volver")
    opcion = _leer_opcion("Opción: ", {"0", "1", "2", "3"})
    if opcion == "0":
        return None
    return _MODOS[opcion]


def iniciar(ruta, velocidad, sheet_name):
    """
    Bucle principal del menú.

    Args:
        ruta (str): Ruta al archivo Excel de configuración.
        velocidad (int/float): Factor de velocidad para las pausas.
        sheet_name (str): Hoja del Excel a leer.
    """
    # Carga inicial de la configuración (usa el caché si sigue vigente).
    base_dir, config = tools.init(ruta, sheet_name)

    while True:
        print("\n=========== ARCA Downloader ===========")
        print("  1) Ejecutar programa")
        print("  2) Actualizar Excel (releer y regenerar caché)")
        print("  3) Chequear actualizaciones")
        print("  0) Salir")
        print("=======================================")
        opcion = _leer_opcion("Opción: ", {"0", "1", "2", "3"})

        if opcion == "1":
            modo = _submenu_modo()
            if modo is not None:
                ejecutar_codigo(config, base_dir, velocidad, modo)

        elif opcion == "2":
            print("[INFO] Releyendo el Excel y regenerando el caché...")
            base_dir, config = tools.init(ruta, sheet_name, forzar=True)
            print(f"[OK] Configuración actualizada ({len(config)} usuarios).")

        elif opcion == "3":
            updater.check_for_updates(version.PROGRAM_ID, version.VERSION,
                                      version.URL_MANIFIESTO)

        elif opcion == "0":
            print("Saliendo...")
            break
