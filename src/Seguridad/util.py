import uuid
import hashlib

def obtener_hwid() -> str:
    """Genera un HWID único basado en la MAC address."""
    raw = str(uuid.getnode()).encode()
    return hashlib.sha256(raw).hexdigest()
