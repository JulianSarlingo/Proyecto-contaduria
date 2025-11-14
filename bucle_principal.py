import tools
import dataDowloader as dd
from os import system

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



def extraer_configuracion(nombre_archivo):
    """
    Lee un archivo de texto, busca la línea que contiene 'ruta =',
    y extrae el valor de la ruta.
    """
    ruta = ''
    velocidad = 0
    sheet_name = ''
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
        
        # Si termina el bucle y no se encuentra la línea
        return ruta, velocidad, sheet_name

    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
    

def ejecutar_codigo(config, ruta, velocidad):
    indice = 0
    usuarios_con_errores = []

    for usuario in config:
        # if usuario['cuit'] == '20240375002':
        #     continue
        try:
            print(f"\n[INFO] Procesando usuario {indice}/{len(config)}: {usuario['nombre']} (CUIT: {usuario['cuit']})") 
            indice += 1
            dd.main(usuario, ruta, velocidad)
        except Exception as e:
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
            usuarios_con_errores.append({'indice': indice, 'usuario': usuario['nombre'], 'error': str(e)})
        # system('pause')
                

    if usuarios_con_errores:
        print("\nUsuarios con errores durante el procesamiento:")
        for ue in usuarios_con_errores:
            print(f" - Usuario: [{ue['indice']}] {ue['usuario']}")

def test(config, ruta, velocidad):
    indice = 1
    usuarios_con_errores = []

    usuarios_a_probar = [config[0], config[3], config[4], config[6], config[8], config[9], config[11]]  # Aquí puedes agregar más usuarios si lo deseas

    for usuario in usuarios_a_probar:
        try:
            print(f"\n[INFO] Procesando usuario {indice}/{len(usuarios_a_probar)}: {usuario['nombre']} (CUIT: {usuario['cuit']})") 
            indice += 1
            dd.main(usuario, ruta, velocidad)
        except Exception as e:
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
            usuarios_con_errores.append({'indice': indice, 'usuario': usuario['nombre'], 'error': str(e)})
        system('pause')
            

    if usuarios_con_errores:
        print("\nUsuarios con errores durante el procesamiento:")
        for ue in usuarios_con_errores:
            print(f" - Usuario: [{ue['indice']}] {ue['usuario']}")



def main():
    ruta, velocidad, sheet_name = extraer_configuracion('config.txt')
    # system('pause')
    ruta, config = tools.init(ruta, sheet_name)

    ejecutar_codigo(config, ruta, velocidad)
    # test(config, ruta, velocidad)

    

if __name__ == '__main__':
    main()
    system('pause')