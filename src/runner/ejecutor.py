"""
runner/ejecutor.py
------------------
Funciones de ejecución masiva y prueba.
Orquestan el procesamiento sobre la lista de usuarios cargada desde el Excel.
"""

import runner.programas as prog
from estado_usuario import nuevo_estado, set_estado, imprimir_estado


# ---------------------------------------------------------------------------
# Ejecución completa
# ---------------------------------------------------------------------------

def ejecutar_codigo(config, ruta, velocidad, modo):
    """
    Procesa TODOS los usuarios de la configuración en el modo indicado.

    Args:
        config (list): Lista de usuarios generada por tools.init().
        ruta (str): Carpeta base de descargas.
        velocidad (int/float): Factor de velocidad.
        modo (str): 'Comprobantes' | 'Retenciones' | 'PortalIVA'.
    """
    if modo not in ["Comprobantes", "Retenciones", "PortalIVA"]:
        print("[ERROR] Modo no reconocido.")
        return

    indice = 0
    usuarios_con_errores = []

    for usuario in config:
        estado = nuevo_estado(usuario)
        try:
            indice += 1
            print(f"\n[INFO] Procesando usuario {indice}/{len(config)}: "
                  f"{usuario['nombre']} (CUIT: {usuario['cuit']})")

            _ejecutar_para_usuario(usuario, ruta, velocidad, modo, estado)

        except Exception as e:
            set_estado(estado, "login", "ERROR", str(e))
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
            usuarios_con_errores.append({
                'indice': indice,
                'usuario': usuario['nombre'],
                'error': str(e)
            })

        imprimir_estado(estado)

    if usuarios_con_errores:
        print("\nUsuarios con errores durante el procesamiento:")
        for ue in usuarios_con_errores:
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
