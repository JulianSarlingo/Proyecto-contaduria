import requests
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURACIÓN
# Cambia estos valores una sola vez
# ---------------------------------------------------------
PROJECT_ID = "licencias-arcadownloader-2305"
API_KEY = "TU_API_KEY_HERE"

BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"


# ---------------------------------------------------------
# 1) Verificar licencia existente
# ---------------------------------------------------------
def licencia_autorizada(hwid: str) -> bool:
    url = f"{BASE_URL}/licencias/{hwid}?key={API_KEY}"
    resp = requests.get(url, timeout=8)

    if resp.status_code != 200:
        return False

    fields = resp.json().get("fields", {})
    return fields.get("autorizado", {}).get("booleanValue", False)


# ---------------------------------------------------------
# 2) Verificar si existe una solicitud previa
# ---------------------------------------------------------
def solicitud_existente(hwid: str) -> bool:
    url = f"{BASE_URL}:runQuery?key={API_KEY}"

    body = {
        "structuredQuery": {
            "select": {"fields": [{"fieldPath": "hwid"}]},
            "from": [{"collectionId": "solicitudes"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "hwid"},
                    "op": "EQUAL",
                    "value": {"stringValue": hwid}
                }
            },
            "limit": 1
        }
    }

    resp = requests.post(url, json=body, timeout=8)

    if resp.status_code != 200:
        print("[ERROR Firestore]", resp.text)
        return False

    for r in resp.json():
        if "document" in r:
            return True

    return False


# ---------------------------------------------------------
# 3) Crear una nueva solicitud
# ---------------------------------------------------------
def crear_solicitud(hwid: str, nombre: str) -> bool:
    url = f"{BASE_URL}/solicitudes?key={API_KEY}"

    body = {
        "fields": {
            "hwid": {"stringValue": hwid},
            "nombre": {"stringValue": nombre},
            "fecha": {"stringValue": datetime.now().isoformat()},
            "procesado": {"booleanValue": False},
            "autorizado": {"booleanValue": False}
        }
    }

    resp = requests.post(url, json=body, timeout=10)
    return resp.status_code in (200, 202)
