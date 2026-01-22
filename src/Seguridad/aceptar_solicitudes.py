import hashlib
import uuid
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Tuple, Dict, Any
from os import system
system('cls')


# ---------- Inicialización ----------
def init_firebase(service_account_path: str):
    """Inicializa el SDK Admin y retorna el cliente Firestore."""
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    return firestore.client()

# ---------- HWID ----------
def obtener_hwid() -> str:
    """Devuelve HWID en formato hex SHA256 (cadena)."""
    raw = uuid.getnode()
    return hashlib.sha256(str(raw).encode()).hexdigest()

# ---------- Lectura de solicitudes ----------
def obtener_solicitudes(db) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Recupera todas las solicitudes de Firestore.
    Retorna lista de tuplas (doc_id, data).
    """
    try:
        coll = db.collection("solicitudes")
        docs = coll.get()  # .stream() también es válido
    except Exception as e:
        raise RuntimeError(f"Error al consultar Firestore: {e}")

    resultados: List[Tuple[str, Dict[str, Any]]] = []
    for doc in docs:
        try:
            data = doc.to_dict() or {}
            resultados.append((doc.id, data))
        except Exception as e:
            # Si algo extraño viene en doc, seguimos con los demás
            print(f"[WARNING] No pude leer documento {getattr(doc, 'id', '<sin id>')}: {e}")
    return resultados

# ---------- Mostrar solicitudes ----------
def mostrar_solicitudes(solicitudes: List[Tuple[str, Dict[str, Any]]]) -> None:
    """Imprime en pantalla las solicitudes con índice y campos básicos."""
    if not solicitudes:
        print("No hay solicitudes pendientes.")
        return

    for i, (doc_id, data) in enumerate(solicitudes):
        hwid = data.get("hwid", "<sin hwid>")
        nombre = data.get("client_name", data.get("nombre", "<sin nombre>"))
        # timestamp puede venir como SERVER_TIMESTAMP (Timestamp de Firestore) o string
        ts = data.get("fecha", data.get("timestamp"))
        fecha_str = "<sin fecha>"
        try:
            # Si es Timestamp de Firestore tiene .to_datetime()
            if hasattr(ts, "to_datetime"):
                fecha_str = ts.to_datetime().strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(ts, datetime):
                fecha_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(ts, str):
                fecha_str = ts
        except Exception:
            fecha_str = "<formato fecha desconocido>"

        procesado = data.get("procesado", False)
        autorizado = data.get("autorizado", False)
        print(f"[{i}] ID_doc: {doc_id}")
        print(f"    HWID:      {hwid}")
        print(f"    Nombre:    {nombre}")
        print(f"    Fecha:     {fecha_str}")
        print(f"    Procesado: {procesado} | Autorizado: {autorizado}\n")

# ---------- Autorizar solicitud ----------
def autorizar_por_hwid(db, hwid: str, client_name: str = None) -> None:
    """
    Crea/actualiza un documento en 'licencias' con ID == hwid marcando autorizado=True.
    """
    doc_ref = db.collection("licencias").document(hwid)
    payload = {
        "hwid": hwid,
        "autorizado": True,
        "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    if client_name:
        payload["client_name"] = client_name

    doc_ref.set(payload)
    print(f"HWID {hwid} autorizado y guardado en 'licencias'.")

def marcar_solicitud_procesada(db, doc_id: str, procesado: bool = True, autorizado: bool = False) -> None:
    """
    Marca la solicitud en 'solicitudes' como procesada y actualiza campos.
    """
    ref = db.collection("solicitudes").document(doc_id)
    updates = {
        "procesado": procesado,
        "autorizado": autorizado,
        "procesado_en": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    ref.update(updates)
    print(f"Solicitud {doc_id} actualizada: procesado={procesado}, autorizado={autorizado}")

# ---------- Función principal ----------
def main(service_account_path: str):
    db = init_firebase(service_account_path)
    solicitudes = obtener_solicitudes(db)
    mostrar_solicitudes(solicitudes)

    if not solicitudes:
        return

    # Selección por índice
    try:
        seleccionado = int(input("Ingrese el número de la solicitud que desea procesar (o ENTER para salir): ").strip() or -1)
    except ValueError:
        print("No se seleccionó un índice válido. Saliendo.")
        return

    if seleccionado < 0 or seleccionado >= len(solicitudes):
        print("Índice fuera de rango. Saliendo.")
        return

    doc_id, data = solicitudes[seleccionado]
    hwid = data.get("hwid")
    nombre = data.get("client_name", data.get("nombre"))

    if not hwid:
        print("La solicitud no contiene HWID. No se puede autorizar.")
        marcar_solicitud_procesada(db, doc_id, procesado=True, autorizado=False)
        return

    confirm = input(f"Autorizar HWID {hwid} para '{nombre}'? (s/N): ").strip().lower()
    if confirm != "s":
        print("Operación cancelada por el usuario.")
        return

    # Autorizar creando documento en 'licencias'
    autorizar_por_hwid(db, hwid, client_name=nombre)
    # Marcar la solicitud como procesada y autorizada
    marcar_solicitud_procesada(db, doc_id, procesado=True, autorizado=True)
    print("Hecho.")
    

# ---------- Ejecutar ----------
if __name__ == "__main__":
    # Reemplazá aquí la ruta a tu serviceAccount JSON
    SERVICE_ACCOUNT_PATH = "./version_separada/Seguridad/firebase_key.json"
    main(SERVICE_ACCOUNT_PATH)
    system('pause')
