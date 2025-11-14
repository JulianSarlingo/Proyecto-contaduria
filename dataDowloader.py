import tools
import tab_navigation as tn
import os
# os.system('cls')

def return_to_original_window(dv, original_window):
    dv.switch_to.window(original_window)

def seccion_comprobantes_empresa(dv, velocidad):
    # print("[INFO] Buscando empresa para acceder...")
    empresas = tools.encontrar_empresas(dv)
    for empresa in range(len(empresas)):
        empresas = tools.encontrar_empresas(dv)
        tools.seleccionar_empresa(dv, empresas[empresa])
        tools.pausa(velocidad)
        # os.system('pause')
        tools.descargar_comprobantes(dv, velocidad)
        tn.retroceder_paginas(dv, 2)

def seccion_comprobantes_personales(dv, velocidad):
    tools.descargar_comprobantes(dv, velocidad)
    tn.retroceder_paginas(dv)

def seccion_mis_comprobantes(dv, original_window, velocidad, sociedades = False):
    tools.ingresar_mis_comprobantes(dv)

    tools.change_window(dv, original_window)
    if sociedades:
        seccion_comprobantes_empresa(dv, velocidad)
    else:
        seccion_comprobantes_personales(dv, velocidad)

    # Cierro la pestaña para que no haya confusiones luego
    tn.cerrar_pestana_actual(dv) # Cierra pestaña de comprobantes

    return_to_original_window(dv, original_window)
    
def seccion_mis_retenciones(dv, original_window, cuit, velocidad):
    tools.ingresar_mis_retenciones(dv)

    tools.change_window(dv, original_window)

    tools.descarga_retenciones_nueva(dv, cuit, velocidad)

    tn.cerrar_pestana_actual(dv) # Cierra pestaña de retenciones

    return_to_original_window(dv, original_window)
    
def main(usuario, ruta, velocidad=1):
    
    # print("[INFO] Iniciando navegador...")
    dv = tools.open_chrome(ruta)
    tools.pausa(velocidad)

    # print("[INFO] Iniciando sesión en AFIP...")
    tools.login_afip(dv, usuario['cuit'], usuario['password'], velocidad)
    tools.pausa(velocidad)

    # os.system('pause')
    # os.system('cls')
    # print(f'Cuit seleccionado: {usuario['cuit']}')

    tools._servicios(dv)
    tools.pausa(velocidad)

    # Guardar pestaña secciones
    original_window = dv.current_window_handle


    # Serie de acciones de la seccion mis comprobantes
    if len(usuario['sociedades']) > 0:
        seccion_mis_comprobantes(dv, original_window, velocidad, sociedades=True)
    else:
        seccion_mis_comprobantes(dv, original_window, velocidad, sociedades=False)

    tools.pausa(velocidad)

    """Activar si querés volver a la pestaña original luego"""
    dv.switch_to.window(original_window)

    # os.system('pause')
    seccion_mis_retenciones(dv, original_window, usuario['cuit'], velocidad)
    """Usa el cuit del inicio de sesion, pero no siempre debera ser asi, cambiar luego"""
    tools.pausa(velocidad)

    # tn.cerrar_pestana_actual(dv)
    dv.quit()