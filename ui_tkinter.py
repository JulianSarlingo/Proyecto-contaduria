import tkinter as tk
from tkinter import messagebox
import tools
import tab_navigation as tn
import dataDowloader as dd

# === Variables de estado ===
driver = None
original_window = None
cuit = None

# === Funciones principales para la GUI ===

def iniciar_y_loguear():
    """
    Abre Chrome y realiza login con AFIP. Guarda driver y CUIT globalmente.
    """
    global driver, original_window, cuit
    try:
        log("Iniciando navegador...")
        driver = tools.open_chrome()

        log("Iniciando sesión en AFIP...")
        cuit = tools.login_afip(driver)
        original_window = driver.current_window_handle

        tools._servicios(driver)
        log(f"CUIT logueado: {cuit}")
        messagebox.showinfo("Éxito", f"CUIT logueado: {cuit}")
    except Exception as e:
        messagebox.showerror("Error", f"Fallo al iniciar: {e}")

def ejecutar_mis_comprobantes():
    """
    Ejecuta el flujo completo de descarga de comprobantes desde la GUI.
    """
    try:
        log("Ejecutando comprobantes...")
        # tools.ingresar_mis_comprobantes(driver)
        # tools.change_window(driver, original_window)
        # tools.seleccionar_empresa(driver)
        # tools.descargar_comprobantes(driver)
        # tn.cerrar_pestana_actual(driver)
        dd.seccion_mis_comprobantes(driver, original_window)
        log("✔ Comprobantes descargados.")
    except Exception as e:
        messagebox.showerror("Error", f"Fallo comprobantes: {e}")

def ejecutar_mis_retenciones():
    """
    Ejecuta el flujo de descarga de retenciones usando el CUIT activo.
    """
    try:
        log("Ejecutando retenciones...")
        # tools.ingresar_mis_retenciones(driver)
        # tools.change_window(driver, original_window)
        # tools.descarga_retenciones(driver, cuit)
        dd.seccion_mis_retenciones(driver, original_window, cuit)
        log("✔ Retenciones descargadas.")
    except Exception as e:
        messagebox.showerror("Error", f"Fallo retenciones: {e}")

def log(texto):
    """
    Agrega una línea de texto en la consola de salida dentro de la interfaz.
    """
    text_output.insert(tk.END, texto + "\n")
    text_output.see(tk.END)

# === Inicialización de ventana principal ===

def iniciar_interfaz():
    global text_output

    ventana = tk.Tk()
    ventana.title("AFIP Automation")
    ventana.geometry("400x300")
    ventana.resizable(False, False)

    frame = tk.Frame(ventana, padx=20, pady=20)
    frame.pack(expand=True)

    tk.Button(frame, text="Iniciar y Login", width=25, command=iniciar_y_loguear).pack(pady=5)
    tk.Button(frame, text="Mis Comprobantes", width=25, command=ejecutar_mis_comprobantes).pack(pady=5)
    tk.Button(frame, text="Mis Retenciones", width=25, command=ejecutar_mis_retenciones).pack(pady=5)

    text_output = tk.Text(frame, height=8, width=40)
    text_output.pack(pady=10)

    ventana.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()