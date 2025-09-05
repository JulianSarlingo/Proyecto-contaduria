# 🔙 Retroceder páginas
def retroceder_paginas(dv, cantidad=1):
    dv.execute_script(f"window.history.go(-{cantidad})")

# 🆕 Abrir nueva pestaña
def abrir_nueva_pestana(dv, url="about:blank"):
    dv.execute_script(f"window.open('{url}', '_blank')")

# 🔄 Cambiar a pestaña por índice
def cambiar_a_pestana(dv, indice):
    handles = dv.window_handles
    if indice < len(handles):
        dv.switch_to.window(handles[indice])
    else:
        print(f"[ERROR] Índice fuera de rango: {indice}")

# 🧭 Obtener índice de pestaña actual
def obtener_indice_actual(dv):
    actual = dv.current_window_handle
    return dv.window_handles.index(actual)

# ❌ Cerrar pestaña actual
def cerrar_pestana_actual(dv):
    dv.close()