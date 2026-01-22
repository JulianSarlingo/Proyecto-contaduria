# estado_usuario.py

def nuevo_estado(usuario):
    """
    Crea una estructura de estado para un usuario.
    """
    return {
        "nombre": usuario.get("nombre", ""),
        "cuit": usuario.get("cuit", ""),
        "login": None,
        "empresas": None,
        "comprobantes_emitidos": None,
        "comprobantes_recibidos": None,
        "retenciones": None,
    }


def set_estado(estado, campo, valor, detalle=""):
    """
    Registra un estado individual: OK o ERROR, con detalle opcional.
    """
    estado[campo] = {
        "status": valor,           # "OK" o "ERROR"
        "detalle": detalle
    }


def imprimir_estado(estado):
    """
    Muestra un reporte legible y ordenado.
    """
    print("\n=========================================")
    print(f"Usuario: {estado['nombre']} - CUIT: {estado['cuit']}")
    print("=========================================")

    def mostrar(campo, leyenda):
        info = estado[campo]
        if info is None:
            print(f"  {leyenda}: SIN DATOS")
        elif info["status"] == "OK":
            print(f"  {leyenda}: OK")
        else:
            print(f"  {leyenda}: ERROR ({info['detalle']})")

    mostrar("login", "Login")
    mostrar("empresas", "Empresas cargadas")
    mostrar("comprobantes_emitidos", "Comprobantes Emitidos")
    mostrar("comprobantes_recibidos", "Comprobantes Recibidos")
    mostrar("retenciones", "Retenciones")

    print("=========================================\n")
