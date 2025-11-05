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


def extraer_ruta(nombre_archivo):
    """
    Lee un archivo de texto, busca la línea que contiene 'ruta =',
    y extrae el valor de la ruta.
    """
    ruta = ''
    velocidad = 0
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
        
        # Si termina el bucle y no se encuentra la línea
        return ruta, velocidad

    except FileNotFoundError:
        return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
    

def main():
    ruta, velocidad = extraer_ruta('config.txt')
    # system('pause')
    ruta, config = tools.init(ruta)
    usuarios_con_errores = []
    indice = 1
    for usuario in config:
        # if usuario['cuit'] == '20240375002':
        #     continue
        try:
            print(f"\n[INFO] Procesando usuario {indice}/{len(config)}: {usuario['nombre']} (CUIT: {usuario['cuit']})") 
            indice += 1
            dd.main(usuario, ruta, velocidad)
        except Exception as e:
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['nombre']}'")
            usuarios_con_errores.append({'usuario': usuario['nombre'], 'error': str(e)})
        system('pause')
            

    if usuarios_con_errores:
        print("\nUsuarios con errores durante el procesamiento:")
        for ue in usuarios_con_errores:
            print(f" - Usuario: {ue['usuario']}")


if __name__ == '__main__':
    main()