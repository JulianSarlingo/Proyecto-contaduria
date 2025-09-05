import tools
import dataDowloader as dd
from os import system


def main():
    # ruta_base = "c:\\Users\\Julian\\Desktop\\Programacion\\Proyectos\\MarianoMortero\\V1\\"
    ruta_base = "C:\\Users\\CLAUDIA\\Desktop\\V1\\"
    config = tools.init(ruta_base)
    # system('pause')

    for usuario in config:
        # if usuario['cuit'] == '20240375002':
        #     continue
        # if usuario['cuit'] == '27251063805':
        #     continue
        # if usuario['cuit'] == '32542159542':
        #     break
        try:
            dd.main(usuario)
        except Exception as e:
            print(f"[ERROR] Fallo en el procesamiento del usuario '{usuario['cuit']}': {e}")
        system('pause')


if __name__ == '__main__':
    main()