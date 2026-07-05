"""
runner/ejecutor.py
------------------
Funciones de ejecución masiva y prueba.
Orquestan el procesamiento sobre la lista de usuarios cargada desde el Excel.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import runner.programas as prog
from browser import driver as drv
from estado_usuario import nuevo_estado, set_estado, imprimir_estado


# Cantidad máxima de clientes procesados en paralelo. Configurable: subilo con
# cuidado (cada cliente abre su propio Chrome y hace su propio login en AFIP;
# demasiados simultáneos pueden saturar RAM/CPU o hacer que AFIP marque la
# actividad). 2-3 es un punto de partida conservador.
MAX_PARALELO = 3

# Lock para imprimir el bloque de estado de cada usuario sin que se mezcle con
# el de otros hilos.
_print_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Ejecución completa
# ---------------------------------------------------------------------------

def _procesar_un_usuario(usuario, indice, total, ruta, velocidad, modo):
    """
    Procesa un único usuario. Pensada para correr dentro de un hilo del pool.

    Mantiene la MISMA lógica por usuario que la versión secuencial: arma el
    estado, ejecuta el programa y captura cualquier excepción. El bloque de
    salida se imprime bajo lock para no entremezclarse con otros hilos.

    Returns:
        tuple: (usuario, estado, error_str | None)
    """
    estado = nuevo_estado(usuario)
    error = None
    try:
        _ejecutar_para_usuario(usuario, ruta, velocidad, modo, estado)
    except Exception as e:
        set_estado(estado, "login", "ERROR", str(e))
        error = str(e)

    with _print_lock:
        print(f"\n[INFO] Usuario {indice}/{total}: "
              f"{usuario['nombre']} (CUIT: {usuario['cuit']})")
        if error:
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
        imprimir_estado(estado)

    return usuario, estado, error


def ejecutar_codigo(config, ruta, velocidad, modo):
    """
    Procesa TODOS los usuarios en el modo indicado, hasta MAX_PARALELO en
    paralelo (hilos). Cada usuario abre su propio Chrome y su propia carpeta de
    descarga, así que son independientes entre sí.

    Args:
        config (list): Lista de usuarios generada por tools.init().
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): 'Comprobantes' | 'Retenciones' | 'PortalIVA'.
    """
    if modo not in ["Comprobantes", "Retenciones", "PortalIVA"]:
        print("[ERROR] Modo no reconocido.")
        return

    total = len(config)
    usuarios_con_errores = []

    print(f"\n[INFO] Procesando {total} usuarios (hasta {MAX_PARALELO} en paralelo)...")

    executor = ThreadPoolExecutor(max_workers=MAX_PARALELO)
    abortado = False
    try:
        futuros = {
            executor.submit(_procesar_un_usuario, usuario, i + 1, total,
                            ruta, velocidad, modo): i + 1
            for i, usuario in enumerate(config)
        }

        for futuro in as_completed(futuros):
            indice = futuros[futuro]
            try:
                usuario, estado, error = futuro.result()
                if error:
                    usuarios_con_errores.append({
                        'indice': indice,
                        'usuario': usuario['nombre'],
                        'error': error,
                    })
            except Exception as e:
                # Salvaguarda: _procesar_un_usuario ya captura; esto es por si
                # algo fallara fuera de ese try (no debería ocurrir).
                with _print_lock:
                    print(f"[ERROR] Excepción inesperada en usuario {indice}: {e}")
                usuarios_con_errores.append({
                    'indice': indice,
                    'usuario': f'(índice {indice})',
                    'error': str(e),
                })

    except KeyboardInterrupt:
        # Ctrl+C: cortamos la corrida, cerramos TODOS los Chrome abiertos y
        # volvemos al menú (no matamos el programa; para eso está la tecla de
        # pánico o salir desde el menú).
        abortado = True
        with _print_lock:
            print("\n[INFO] Interrupción (Ctrl+C): cerrando todos los Chrome y abortando...")
        drv.cerrar_todos_los_chrome()
    finally:
        # cancel_futures cancela los usuarios que todavía no arrancaron; los que
        # están en curso terminan al cerrarse su Chrome.
        executor.shutdown(wait=False, cancel_futures=True)

    if abortado:
        return

    if usuarios_con_errores:
        with _print_lock:
            print("\nUsuarios con errores durante el procesamiento:")
            for ue in sorted(usuarios_con_errores, key=lambda x: x['indice']):
                print(f" - Usuario: [{ue['indice']}] {ue['usuario']}")


# ---------------------------------------------------------------------------
# Ejecución individual y por rango
# ---------------------------------------------------------------------------

def probar_usuario(config, indice, ruta, velocidad, modo):
    """
    Procesa SOLO un usuario específico según su índice (1-based).

    Args:
        config (list): Lista completa de usuarios.
        indice (int): Número del usuario a procesar (empieza en 1).
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): 'Comprobantes' | 'Retenciones' | 'PortalIVA'.
    """
    if indice < 1 or indice > len(config):
        print(f"[ERROR] El índice {indice} está fuera de rango. Total de usuarios: {len(config)}")
        return

    usuario = config[indice - 1]  # Convertimos a 0-based
    estado  = nuevo_estado(usuario)

    print(f"\n[PRUEBA] Procesando SOLO al usuario {indice}/{len(config)}: "
          f"{usuario['nombre']} (CUIT: {usuario['cuit']})")

    try:
        _ejecutar_para_usuario(usuario, ruta, velocidad, modo, estado)
    except Exception as e:
        set_estado(estado, "login", "ERROR", str(e))
        print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")

    imprimir_estado(estado)


def probar_rango(config, rango, ruta, velocidad, modo):
    """
    Procesa un rango de usuarios (ambos extremos inclusive).

    Args:
        config (list): Lista completa de usuarios.
        rango (tuple | list): (inicio, fin) — índices 1-based.
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): 'Comprobantes' | 'Retenciones' | 'PortalIVA'.
    """
    inicio, fin = rango
    total = len(config)

    if inicio < 1:  inicio = 1
    if fin > total: fin = total
    if inicio > fin:
        print(f"[ERROR] El inicio ({inicio}) es mayor que el fin ({fin}).")
        return

    print(f"\n{'='*40}")
    print(f"[MODO PRUEBA] Ejecutando rango: Usuarios {inicio} al {fin}")
    print(f"{'='*40}")

    for i in range(inicio, fin + 1):
        probar_usuario(config, i, ruta, velocidad, modo)

    print(f"\n{'='*40}")
    print(f"[FIN PRUEBA] Rango {inicio}-{fin} completado.")
    print(f"{'='*40}\n")


def probar_usuario_manual(ruta, velocidad, modo, usuario_dict=None):
    """
    Prueba un usuario definido manualmente, sin leer el Excel.
    Ideal para testing y debug rápido.

    Args:
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): 'Comprobantes' | 'Retenciones' | 'PortalIVA'.
        usuario_dict (dict | None): Datos del usuario. Si es None, usa uno de prueba por defecto.
    """
    if usuario_dict is None:
        usuario_dict = {
            'nombre':           'VIVIANI CLARISA',
            'cuit':             '27309803529',
            'password':         'C14ri54Viv',
            'tipo_monotributo': 'Monot. Unificado',
            'sociedades':       []
        }

    estado = nuevo_estado(usuario_dict)
    print(f"\n[DEBUG MANUAL] Procesando usuario de prueba: "
          f"{usuario_dict['nombre']} (CUIT: {usuario_dict['cuit']})")

    try:
        _ejecutar_para_usuario(usuario_dict, ruta, velocidad, modo, estado)
    except Exception as e:
        set_estado(estado, "login", "ERROR", str(e))
        print(f"[ERROR] Fallo en el procesamiento del usuario de prueba '{usuario_dict['nombre']}'")

    imprimir_estado(estado)


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------

def _ejecutar_para_usuario(usuario, ruta, velocidad, modo, estado):
    """
    Llama al programa correspondiente según el modo y la condición del usuario.

    Args:
        usuario (dict): Datos del usuario.
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): Modo de ejecución.
        estado (dict): Estado del usuario para registrar resultados.
    """
    if modo == "Comprobantes":
        prog.programa_Comprobantes(usuario, ruta, estado, velocidad)

    elif modo == "Retenciones":
        if usuario["tipo_monotributo"] == "Resp. Inscripto":
            prog.programa_Retenciones(usuario, ruta, estado, velocidad)
        else:
            print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Retenciones.")

    elif modo == "PortalIVA":
        if usuario["tipo_monotributo"] == "Resp. Inscripto":
            prog.programa_Portal_IVA(usuario, ruta, estado, velocidad)
        else:
            print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Portal IVA.")
