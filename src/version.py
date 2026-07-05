"""
version.py
----------
Identidad y versión de ESTE programa, más la configuración de actualizaciones.

IMPORTANTE: subí VERSION en cada build nuevo ANTES de compilar el .exe. El
updater compara esta versión contra la del manifiesto remoto para saber si hay
que actualizar.
"""

# Identificador del programa (mismo esquema que la licencia por programa).
PROGRAM_ID = "arca"

# Versión de este build.
VERSION = "2.2.5"

# URL del manifiesto de actualizaciones (JSON) para este programa.
# Completá con la URL pública de tu archivo en Firebase Storage.
#
# Formato esperado del JSON:
#   {
#       "version":   "2.2.6",
#       "url":       "https://.../arca_2.2.6.exe",
#       "sha256":    "<hash sha-256 del exe>",
#       "changelog": "Qué cambió"
#   }
URL_MANIFIESTO = ""  # <-- COMPLETAR con tu URL de Firebase Storage
