import tools
import dataDowloader as dd
from os import system
from Seguridad import licencia
from estado_usuario import nuevo_estado, set_estado, imprimir_estado
import logger

"""
Antes de empezar recuerda ejecutar estos comandos
para mantener el trabajo actualizado en todas tus maquinas:
1. Traer cambios de GitHub

git pull origin main

2. Ver qué cambió en tu carpeta

git status

3. Guardar cambios en Git

git add .
git commit -m "mensaje"

4. Subir cambios a GitHub

git push origin main

"""

"""
Para configurar el ejecutable
abre una terminal y ejecuta:
.\venv_nuevo\Scripts\auto-py-to-exe.exe

e incluye estos archivos adicionales:

"""

def esperar_salida():
    input("\nPresione Enter para salir...")

def extraer_configuracion(nombre_archivo):
    """
    Lee un archivo de texto, busca la línea que contiene 'ruta =',
    y extrae el valor de la ruta.
    """
    ruta = ''
    velocidad = 0
    sheet_name = ''
    modo = ''
    try:
        with open(nombre_archivo, 'r') as archivo:
            for linea in archivo:
                # Elimina espacios en blanco al inicio/final y verifica si contiene 'ruta ='
                linea = linea.strip()
                if linea.startswith('ruta ='):
                    # Divide la línea en el símbolo '='. La ruta será el segundo elemento [1]
                    # y usamos .strip() de nuevo para eliminar espacios adicionales.
                    ruta = linea.split('=', 1)[1].strip()
                elif linea.startswith('velocidad ='):
                    velocidad_str = linea.split('=', 1)[1].strip()
                    try:
                        velocidad = int(velocidad_str)
                    except ValueError:
                        print(f"[WARNING] No se pudo convertir la velocidad '{velocidad_str}' a entero.")
                    # No retornamos aquí porque queremos seguir buscando la ruta
                elif linea.startswith('hoja ='):
                    sheet_name = linea.split('=', 1)[1].strip()
                elif linea.startswith('modo ='):
                    modo = linea.split('=', 1)[1].strip()
        
        # Si termina el bucle y no se encuentra la línea
        return ruta, velocidad, sheet_name, modo

    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."


def ejecutar_codigo(config, ruta, velocidad, modo):
    indice = 0
    usuarios_con_errores = []

    if modo not in ["Comprobantes", "Retenciones", "PortalIVA"]:
        print("[ERROR] Modo no reconocido.")
        return

    for usuario in config:
        estado = nuevo_estado(usuario) # Manejo de errores
        try:
            indice += 1
            print(f"\n[INFO] Procesando usuario {indice}/{len(config)}: {usuario['nombre']} (CUIT: {usuario['cuit']})") 

            if modo == "Comprobantes":
                dd.programa_Comprobantes(usuario, ruta, estado, velocidad)
            elif modo == "Retenciones":
                if usuario["tipo_monotributo"] == "Resp. Inscripto":
                    dd.programa_Retenciones(usuario, ruta, estado, velocidad)
                else:
                    print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Retenciones.")
            elif modo == "PortalIVA":
                if usuario["tipo_monotributo"] == "Resp. Inscripto":
                    dd.programa_Portal_IVA(usuario, ruta, estado, velocidad)
                else:
                    print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Portal IVA.")
            # system('pause')
            
        except Exception as e:
            set_estado(estado, "login", "ERROR", str(e))
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
            usuarios_con_errores.append({'indice': indice, 'usuario': usuario['nombre'], 'error': str(e)})
        # system('pause')
        imprimir_estado(estado)
                

    if usuarios_con_errores:
        print("\nUsuarios con errores durante el procesamiento:")
        for ue in usuarios_con_errores:
            print(f" - Usuario: [{ue['indice']}] {ue['usuario']}")


def probar_rango(config, rango, ruta, velocidad, modo):
    """
    Ejecuta la prueba para un rango de usuarios (inclusive).
    
    Args:
        rango (tuple): Tupla con dos enteros (inicio, fin) representando el rango de usuarios a procesar.
        config (list): Lista de usuarios generada por tools.init().
    """
    inicio, fin = rango
    total = len(config)
    
    # Validaciones básicas para que no rompa si pones números locos
    if inicio < 1: inicio = 1
    if fin > total: fin = total
    if inicio > fin:
        print(f"[ERROR] El inicio ({inicio}) es mayor que el fin ({fin}).")
        return

    print(f"\n{'='*40}")
    print(f"[MODO PRUEBA] Ejecutando rango: Usuarios {inicio} al {fin}")
    print(f"{'='*40}")
    
    # Iteramos desde el inicio hasta el fin (el +1 es porque range excluye el último número)
    for i in range(inicio, fin + 1):
        # Llamamos a tu función individual, que ya maneja la lógica y errores por usuario
        probar_usuario(config, i, ruta, velocidad, modo)
        
    print(f"\n{'='*40}")
    print(f"[FIN PRUEBA] Rango {inicio}-{fin} completado.")
    print(f"{'='*40}\n")

def probar_usuario(config, indice, ruta, velocidad, modo):
    ## Hacer esta funcion igual a ejecutar_codigo pero solo para un usuario
    """
    Ejecuta el proceso SOLO para un usuario específico según su índice (1-based).
    
    Args:
        config (list): Lista completa de usuarios generada por tools.init().
        indice (int): Número del usuario a procesar (empieza en 1).
        ruta (str): Carpeta de destino de descargas.
        velocidad (int): Velocidad de ejecución.
        modo (str): El modo de ejecución ("Comprobantes", "Retenciones", "PortalIVA").
    """
    if indice < 1 or indice > len(config):
        print(f"[ERROR] El índice {indice} está fuera de rango. Total de usuarios: {len(config)}")
        return
    
    usuario = config[indice - 1]  # Convertimos a índice 0-based
    estado = nuevo_estado(usuario)

    print(f"\n[PRUEBA] Procesando SOLO al usuario {indice}/{len(config)}: {usuario['nombre']} (CUIT: {usuario['cuit']})")

    try:
        if modo == "Comprobantes":
            dd.programa_Comprobantes(usuario, ruta, estado, velocidad)
        elif modo == "Retenciones":
            if usuario["tipo_monotributo"] == "Resp. Inscripto":
                dd.programa_Retenciones(usuario, ruta, estado, velocidad)
            else:
                print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Retenciones.")
        elif modo == "PortalIVA":
            if usuario["tipo_monotributo"] == "Resp. Inscripto":
                dd.programa_Portal_IVA(usuario, ruta, estado, velocidad)
            else:
                print("[INFO] Usuario no es Responsable Inscripto. Se omite programa de Portal IVA.")
    except Exception as e:
        set_estado(estado, "login", "ERROR", str(e))
        print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
    
    imprimir_estado(estado)

def main():
    ruta, velocidad, sheet_name, modo = extraer_configuracion('config.txt')
    # system('pause')
    ruta, config = tools.init(ruta, sheet_name)

    # modo = ["Comprobantes", "Retenciones", "PortalIVA"]
    # probar_usuario(config, 40, ruta, velocidad, modo[2])
    # probar_rango(config, [14, 18], ruta, velocidad, modo[2])

    ejecutar_codigo(config, ruta, velocidad, modo)


def principal(modo_prueba):
    if modo_prueba:
        main()
        # probar_usuario(config, 1, ruta, velocidad)
    elif verificar_aprobacion():
        main()



def verificar_aprobacion():
    hwid = licencia.obtener_hwid()

    # 1) Verificación de licencia
    if licencia.licencia_autorizada(hwid):
        print("✔ Licencia autorizada. Iniciando programa...")
        return True

    print("❌ Licencia no autorizada.")

    # 2) Verificar si ya existe solicitud previa
    if licencia.solicitud_existente(hwid):
        print("⚠ Ya existe una solicitud pendiente. Espere aprobación.")
        return False

    # 3) Crear solicitud si no existe
    print("Por favor, ingrese un nombre con el que el desarrollador pueda identificar este PC.")
    nombre = input("Ingrese un nombre: ")
    licencia.crear_solicitud(hwid, nombre)

    print("✔ Solicitud enviada. Espere la aprobación.")

if __name__ == '__main__':

    logger.iniciar_proteccion()

    # principal(modo_prueba=False)
    principal(modo_prueba=True)
    # if verificar_aprobacion():
    #     main()
    system('pause')