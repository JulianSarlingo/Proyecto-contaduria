import os
# import shutil
from datetime import date
import time

def obtener_fecha_actual():
    """
    Devuelve la fecha actual en formato YYYY-MM-DD.
    """
    return date.today().isoformat()

def crear_estructura_base(base_dir, nombre_persona, nombre_sociedad=None):
    """
    Crea la estructura de carpetas para almacenar archivos descargados.

    Args:
        base_dir (str): Carpeta base (ej: "descargas_afip").
        nombre_persona (str): Nombre del titular.
        nombre_sociedad (str, optional): Nombre de la sociedad, si aplica.

    Returns:
        str: Ruta absoluta a la carpeta de destino final.
    """
    fecha = obtener_fecha_actual()
    ruta = os.path.join(base_dir, fecha, nombre_persona)
    if nombre_sociedad:
        ruta = os.path.join(ruta, nombre_sociedad)

    os.makedirs(ruta, exist_ok=True)
    return ruta

def renombrar_archivo(ruta_actual_archivo, nombre_deseado_sin_extension, extension_deseada=None):
    """
    Genera la ruta del nuevo nombre para un archivo específico, sin moverlo aún.
    Maneja conflictos de nombre añadiendo un contador (ej: archivo_1.xls).

    Args:
        ruta_actual_archivo (str): La ruta completa actual del archivo a renombrar (ej. 'C:\\Users\\Usuario\\Downloads\\descarga.pdf').
        nombre_deseado_sin_extension (str): El nombre base que quieres para el archivo (ej. "comprobantes_emitidos").
        extension_deseada (str, optional): La extensión que se espera (ej. ".xls", ".pdf").
                                           Si es None, se usa la extensión del archivo original.

    Returns:
        str: La ruta completa que el archivo DEBERÍA tener después de renombrarse y antes de moverse.
             Retorna None si la ruta_actual_archivo no existe.
    """
    if not os.path.exists(ruta_actual_archivo):
        print(f"[ADVERTENCIA] El archivo '{ruta_actual_archivo}' no existe para renombrar.")
        return None

    directorio_original, nombre_original_con_ext = os.path.split(ruta_actual_archivo)
    # ^ Separa el directorio de la ruta y el nombre del archivo.

    # Determinar la extensión final
    if extension_deseada:
        extension = extension_deseada.lower() if extension_deseada.startswith('.') else f".{extension_deseada.lower()}"
    else:
        # Si no se especifica, usar la extensión del archivo original
        _, original_ext = os.path.splitext(nombre_original_con_ext)
        extension = original_ext.lower()

    # Construir el nombre final deseado con la extensión
    nombre_final_con_extension = f"{nombre_deseado_sin_extension}{extension}"

    # Generar la ruta final temporal en el mismo directorio de descarga
    ruta_final_temporal = os.path.join(directorio_original, nombre_final_con_extension)

    # Lógica para evitar sobrescribir si el nombre ya existe en el directorio de descarga
    # (esto es útil si descargas el mismo tipo de archivo varias veces antes de moverlo)
    contador = 1
    base_nombre_temp = nombre_deseado_sin_extension
    while os.path.exists(ruta_final_temporal) and ruta_final_temporal != ruta_actual_archivo:
        ruta_final_temporal = os.path.join(directorio_original, f"{base_nombre_temp}_{contador}{extension}")
        contador += 1
    
    # Renombra el archivo en su ubicación actual. Esto es una operación atómica en muchos sistemas.
    try:
        os.rename(ruta_actual_archivo, ruta_final_temporal)
        print(f"[INFO] Archivo renombrado de '{nombre_original_con_ext}' a '{os.path.basename(ruta_final_temporal)}' en el directorio de descarga.")
        return ruta_final_temporal
    except Exception as e:
        print(f"[ERROR] No se pudo renombrar el archivo '{ruta_actual_archivo}': {e}")
        return None


def obtener_ultimo_archivo_descargado(directorio_descarga):
    """
    Encuentra y devuelve la ruta completa del archivo más reciente (último creado/modificado)
    en el directorio especificado.

    Args:
        directorio_descarga (str): La ruta de la carpeta donde se buscará el archivo.

    Returns:
        str: La ruta completa del archivo más reciente.
        None: Si la carpeta no existe o no contiene ningún archivo.
    """
    if not os.path.exists(directorio_descarga):
        print(f"[ADVERTENCIA] El directorio '{directorio_descarga}' no existe.")
        return None

    time.sleep(2)
    
    archivos = [
        os.path.join(directorio_descarga, f)
        for f in os.listdir(directorio_descarga)
        if os.path.isfile(os.path.join(directorio_descarga, f))
    ]
    # ^ Crea una lista de rutas completas para todos los archivos dentro del directorio_descarga,
    #   filtrando para asegurar que solo incluya archivos (no subcarpetas).

    if not archivos:
        print(f"[ADVERTENCIA] No se encontraron archivos en '{directorio_descarga}'.")
        return None
    # ^ Si la lista de archivos está vacía, significa que no hay archivos en la carpeta.

    # Ordena la lista de archivos por su fecha de última modificación (os.path.getmtime)
    # de más reciente a más antiguo (reverse=True) y toma el primero.
    ultimo_archivo = max(archivos, key=os.path.getmtime)
    
    print(f"[INFO] Último archivo encontrado en '{directorio_descarga}': {os.path.basename(ultimo_archivo)}")
    return ultimo_archivo