from .licencia import (
    obtener_hwid,
    licencia_autorizada,
    solicitud_existente,
    crear_solicitud
)

def esperar_salida():
    input("\nPresione Enter para salir...")


def main():
    print("========== SISTEMA DE LICENCIAS ==========\n")

    hwid = obtener_hwid()
    print("HWID detectado:\n", hwid, "\n")

    print("Verificando licencia...")
    if licencia_autorizada(hwid):
        print("\n✔ Esta computadora está autorizada.")
        return esperar_salida()

    print("\n❌ No está autorizada.\n")

    print("Buscando solicitud previa...")
    if solicitud_existente(hwid):
        print("\n⚠ Ya existe una solicitud pendiente.")
        return esperar_salida()

    print("\nNo existe solicitud previa.")
    nombre = input("Ingrese su nombre para enviar la solicitud: ")

    print("\nEnviando solicitud...")
    if crear_solicitud(hwid, nombre):
        print("\n✔ Solicitud enviada correctamente.")
    else:
        print("\n❌ Error al enviar la solicitud.")

    esperar_salida()


if __name__ == "__main__":
    main()
