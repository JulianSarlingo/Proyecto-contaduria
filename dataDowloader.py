import tools
import tab_navigation as tn
import os
os.system('cls')

def return_to_original_window(dv, original_window):
    dv.switch_to.window(original_window)

def seccion_comprobantes_empresa(dv):
    # print("[INFO] Buscando empresa para acceder...")
    empresas = tools.encontrar_empresas(dv)
    for empresa in range(len(empresas)):
        empresas = tools.encontrar_empresas(dv)
        tools.seleccionar_empresa(dv, empresas[empresa])
        # os.system('pause')
        tools.descargar_comprobantes(dv) 
        tn.retroceder_paginas(dv, 2)

def seccion_mis_comprobantes(dv, original_window):
    tools.ingresar_mis_comprobantes(dv)

    tools.change_window(dv, original_window)

    seccion_comprobantes_empresa(dv)

    # Cierro la pestaña para que no haya confusiones luego
    tn.cerrar_pestana_actual(dv) # Cierra pestaña de comprobantes

    return_to_original_window(dv, original_window)
    
def seccion_mis_retenciones(dv, original_window, cuit):
    tools.ingresar_mis_retenciones(dv)

    tools.change_window(dv, original_window)

    tools.descarga_retenciones(dv, cuit)

    tn.cerrar_pestana_actual(dv) # Cierra pestaña de retenciones

    return_to_original_window(dv, original_window)
    
def main(usuario):
    # ruta_base = "c:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\"
    # config = tools.init(ruta_base)
    # ruta_origen = "c:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\Datos Afip\\"


    # print("[INFO] Iniciando navegador...")
    dv = tools.open_chrome()

    # print("[INFO] Iniciando sesión en AFIP...")
    tools.login_afip(dv, usuario['cuit'], usuario['password'])

    os.system('cls')
    # print(f'Cuit seleccionado: {usuario['cuit']}')

    tools._servicios(dv)

    # Guardar pestaña secciones
    original_window = dv.current_window_handle


    # Serie de acciones de la seccion mis comprobantes
    seccion_mis_comprobantes(dv, original_window)

    """Activar si querés volver a la pestaña original luego"""
    dv.switch_to.window(original_window)

    # os.system('pause')
    seccion_mis_retenciones(dv, original_window, usuario['cuit'])
    """Usa el cuit del inicio de sesion, pero no siempre debera ser asi, cambiar luego"""

    # tn.cerrar_pestana_actual(dv)



# if __name__ == "__main__":
#     main()
