from .util import obtener_hwid
from .firestore import (
    licencia_autorizada,
    solicitud_existente,
    crear_solicitud
)

# Este archivo expone directamente:
# - obtener_hwid()
# - licencia_autorizada(hwid)
# - solicitud_existente(hwid)
# - crear_solicitud(hwid, nombre)
#
# No contiene lógica de flujo, solo funciones utilizables.
