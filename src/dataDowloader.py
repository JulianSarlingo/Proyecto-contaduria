import tools
import tab_navigation as tn
# import os

# os.system('cls')

# ======= Herramientas Generales ======== #

def return_to_original_window(dv, original_window):
    dv.switch_to.window(original_window)

## Login comun a ambos programas
def login(usuario, ruta, estado, velocidad):
    # print("[INFO] Iniciando navegador...")
    ruta_descarga_chrome = ruta + f"\\{usuario['nombre']}"
    dv = tools.open_chrome(ruta_descarga_chrome)
    tools.pausa(velocidad)

    # print("[INFO] Iniciando sesión en AFIP...")
    ok_login = tools.login_afip(dv, usuario['cuit'], usuario['password'], velocidad, estado) # Corregido: pasar 'estado'
    
    if not ok_login:
        print(f"[INFO] Login falló para {usuario['nombre']}, se salta al siguiente.")
        raise Exception("Fallo en login: no se pudo iniciar sesión")
    return dv

def pausa_servicios(dv, velocidad):
    tools.pausa(velocidad)

    tools._servicios(dv)
    tools.pausa(velocidad)
    original_window = dv.current_window_handle
    return original_window


# ======= Funciones Mis Comprobantes ======== #

def seccion_comprobantes_empresa(dv, estado, velocidad):
    # print("[INFO] Buscando empresa para acceder...")
    empresas = tools.encontrar_empresas(dv)
    for empresa in range(len(empresas)):
        empresas = tools.encontrar_empresas(dv)
        tools.seleccionar_empresa(dv, empresas[empresa])
        tools.pausa(velocidad)
        # os.system('pause')
        tools.descargar_comprobantes(dv, estado, velocidad)
        tn.retroceder_paginas(dv, 2)

def seccion_comprobantes_personales(dv, usuario, estado, velocidad): # <-- Recibe usuario
    # Ahora tools.descargar_comprobantes sabe la condición del usuario
    tools.descargar_comprobantes(dv, usuario, estado, velocidad) # <-- Pasa usuario
    # tn.retroceder_paginas(dv)

def seccion_mis_comprobantes(dv, usuario, estado, original_window, velocidad, sociedades = False): # <-- Recibe usuario
    tools.ingresar_mis_comprobantes(dv)
    tools.change_window(dv, estado, original_window)

    if sociedades:
        # Aquí se asume que las sociedades son RI o que se manejará la lógica de la sociedad
        seccion_comprobantes_empresa(dv, estado, velocidad)
    else:
        # Se pasa el usuario para que se aplique la lógica de formatos (RI, MU, CM)
        seccion_comprobantes_personales(dv, usuario, estado, velocidad) # <-- Pasa usuario


# ======= Funciones Mis Retenciones ======== #
    
def seccion_mis_retenciones(dv, estado, original_window, cuit, velocidad):
    tools.ingresar_mis_retenciones(dv)

    tools.change_window(dv, estado, original_window)

    tools.descarga_retenciones(dv, cuit, velocidad, estado)

    tn.cerrar_pestana_actual(dv) # Cierra pestaña de retenciones

    return_to_original_window(dv, original_window)

# ======= Funciones Portal IVA ======== #

def seccion_Portal_IVA_personales(dv, usuario, ruta, estado, velocidad):
    tools.descargar_libro_IVA(dv, usuario, ruta, velocidad, estado)
    # tn.retroceder_paginas(dv)

def seccion_Portal_IVA_empresa(dv, usuario, ruta, estado, velocidad):
    # Detectamos a quién tenemos en pantalla
    usuario_actual = tools.obtener_representado_actual_portal_iva(dv)

    # seccion_Portal_IVA_personales(dv, estado, velocidad)

    if len(usuario['sociedades']) > 0:
        tools.ct.click_cambiar_representado_portal_iva(dv)
        tools.seleccionar_empresa_portal_iva(dv, usuario['sociedades'][0]['cuit'])
        seccion_Portal_IVA_personales(dv, usuario, ruta, estado, velocidad)
        tn.retroceder_paginas(dv)


def seccion_Portal_IVA(dv, usuario, ruta, estado, original_window, velocidad, sociedades=False):
    # 1) Entrar al portal IVA
    if not tools.ingresar_Portal_IVA(dv):
        print("[INFO] Saltando sección Portal IVA porque no está disponible.")
        return  # Cortamos acá sin errores
    # 2) Cambiar a la nueva ventana
    tools.change_window(dv, estado, original_window)

    if not tools.portal_iva_disponible(dv):
        print("[INFO] Portal IVA no está habilitado o no cargó correctamente.")
        tn.cerrar_pestana_actual(dv)               # Cerramos la pestaña vacía
        return_to_original_window(dv, original_window)
        return

    if sociedades:
        seccion_Portal_IVA_empresa(dv, usuario, ruta, estado, velocidad)
    else:
        seccion_Portal_IVA_personales(dv, usuario, ruta, estado, velocidad)

    dv.quit()


## El programa que solo descarga comprobantes

def programa_Comprobantes(usuario, ruta, estado, velocidad=1):
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return
    
    # Guardar pestaña secciones
    original_window = pausa_servicios(dv, velocidad)

    # Serie de acciones de la seccion mis comprobantes
    if len(usuario['sociedades']) > 0:
        seccion_mis_comprobantes(dv, usuario, estado, original_window, velocidad, sociedades=True) # <-- Pasa usuario
    else:
        seccion_mis_comprobantes(dv, usuario, estado, original_window, velocidad, sociedades=False) # <-- Pasa usuario

    dv.quit()

## El programa que solo descarga retenciones

def programa_Retenciones(usuario, ruta, estado, velocidad=1):
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return

    original_window = pausa_servicios(dv, velocidad)

    seccion_mis_retenciones(dv, estado, original_window, usuario['cuit'], velocidad)

    # Cierra el navegador al finalizar
    dv.quit()

## El programa que solo descarga retenciones

def programa_Portal_IVA(usuario, ruta, estado, velocidad=1):
    dv = login(usuario, ruta, estado, velocidad)
    if not dv:
        return

    original_window = pausa_servicios(dv, velocidad)

    # Serie de acciones de la seccion mis comprobantes
    if len(usuario['sociedades']) > 0:
        sociedades = True
    else:
        sociedades = False
    seccion_Portal_IVA(dv, usuario, ruta, estado, original_window, velocidad, sociedades)

    # Cierra el navegador al finalizar
    dv.quit()