import re

def extract_data(data):
    # Diccionario donde guardaremos los datos
    usuarios_dict = {}

    # Abrimos el archivo en modo lectura
    with open(data, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            print(linea)
            # Buscamos usuario y contraseña con expresiones regulares
            match = re.search(r"Usuario:\s*(\S+)\s+Contraseña:\s*(\S+)", linea)
            if match:
                usuario = match.group(1)
                contraseña = match.group(2)
                usuarios_dict[usuario] = contraseña

    return usuarios_dict
    # Mostramos los resultados
    # for usuario, contraseña in usuarios_dict.items():
    #     print(f"Usuario: {usuario}, Contraseña: {contraseña}")

# extract_data()