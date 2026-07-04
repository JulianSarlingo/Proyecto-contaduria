# Licencias por programa individual — cambios y guía de modularización

> **Actualización 2026-06-30:** la sección 2 ya se ejecutó. `Seguridad` fue
> movida fuera de este repo a `C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias\`.
> Ver la sección **"Estado actual y qué falta"** al final de este documento
> antes de seguir los pasos de abajo como si fueran pendientes — la mayoría
> ya está hecha.

## 1. Qué cambió y por qué

**Problema original:** el ID del documento en `licencias` era directamente el `hwid`. Un equipo autorizado para un programa quedaba autorizado para todos.

**Solución:** el ID del documento ahora es una clave combinada `"<programa>_<hwid>"` (`cronos_<hwid>` / `arca_<hwid>`), generada y validada en un único lugar (`firestore._clave_combinada`) para evitar inconsistencias entre archivos.

Archivos modificados en `src/Seguridad/`:

- **`firestore.py`** — Reescrito. Se eliminó la lógica de subcolección (`licencias/{hwid}/productos/{programa}`) que convivía con la búsqueda antigua por HWID; ahora hay un solo esquema (documento con ID combinado). `licencia_autorizada`, `solicitud_existente` y `crear_solicitud` piden `programa` obligatorio, validado contra `PROGRAMAS_VALIDOS = {"cronos", "arca"}`. `solicitud_existente` ahora filtra por `hwid` **y** `programa` (antes solo por `hwid`, así que una solicitud pendiente de un programa bloqueaba la solicitud del otro). Se agregó manejo de `requests.RequestException` en las tres funciones (antes un timeout de red tiraba una excepción no capturada).
- **`licencia.py`** — Sin lógica propia, solo re-exporta con las nuevas firmas.
- **`interfaz.py`** — `main()` ahora exige el parámetro `programa` ("cronos"/"arca") y lo propaga a las tres llamadas de licencia.
- **`aceptar_solicitudes.py`** — Lee el campo `programa` de cada solicitud y arma la clave combinada para el documento en `licencias`. Si una solicitud vieja no tiene `programa` (pre-migración), lo pide por consola en vez de fallar. Se quitó la definición duplicada de `obtener_hwid` (ahora importa la de `util.py`). Se movió `system('cls')` de nivel de módulo (se ejecutaba al solo importar el archivo, un bug si este módulo se importa desde otro script) a dentro del bloque `if __name__ == "__main__"`.
- **`util.py`** — Sin cambios funcionales, solo documentación.
- **`__init__.py`** (nuevo) — No existía; sin él, `Seguridad` funcionaba como *namespace package* implícito, lo cual es fràgil para el empaquetado editable que se describe más abajo.
- **`main.py`** (raíz del proyecto) — Este repo resultó ser **ARCA Downloader**, no Cronos (confirmado por el título de los diálogos de error en `logger.py`: *"Error Crítico - ARCA Downloader"*). Se agregó `PROGRAMA = "arca"` y `verificar_aprobacion()` ahora pasa ese valor a las tres llamadas de licencia.
- **`Seguridad/tests/`** (nuevo) — `test_util.py` y `test_firestore.py`, 14 tests con `unittest.mock` (no hacen llamadas de red real). Todos pasan.

**Backup:** antes de tocar nada, se copiaron los 5 archivos originales sin modificar a la carpeta temporal de trabajo (no en este repo, para no interferir con git). Si querés revertir, pedímelo o restaurá desde tu propio historial de git — noté que `git status` ya mostraba estos archivos como modificados respecto al último commit *antes* de que yo tocara nada, así que probablemente ya tenías cambios propios sin commitear. Te recomiendo hacer `git add -A && git commit -m "checkpoint"` vos mismo/a cuando puedas (al intentarlo yo, `.git/index.lock` estaba tomado por otro proceso — probablemente la app de escritorio).

### Pendiente de tu parte
- **`API_KEY = "TU_API_KEY_HERE"`** en `firestore.py` sigue sin completar (no la inventé). Reemplazala por la key real del proyecto Firebase.
- **`firebase_admin`** se usa en `aceptar_solicitudes.py` pero no está en `requirements.txt`. Agregalo (`pip install firebase-admin` dentro del venv y despues actualizar el archivo).
- Documentos `licencias/{hwid}` viejos (esquema anterior) no se leen más. Si hay licencias activas en producción con ese formato, hay que migrarlas a mano a `cronos_{hwid}` o `arca_{hwid}` antes de desplegar esto, o el equipo pedirá una licencia nueva.

## 2. Modularización externa: sacar `Seguridad` de ambos proyectos

Objetivo: una sola copia de `Seguridad/` reutilizada por Cronos y ARCA Downloader vía `from Seguridad.interfaz import main`, sin duplicar el código en cada repo.

### Paso 1 — Elegir la ubicación centralizada

Ejemplo:

```
C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias\
├── pyproject.toml
└── src\
    └── Seguridad\
        ├── __init__.py
        ├── util.py
        ├── firestore.py
        ├── licencia.py
        ├── interfaz.py
        └── aceptar_solicitudes.py
```

Mové ahí los 5 archivos `.py` (ya actualizados) y el `__init__.py` nuevo.

**No muevas `firebase_key.json`** a esta carpeta compartida: es la credencial de administrador y solo la usás vos al correr `aceptar_solicitudes.py`. Dejala en una ruta separada (por ejemplo `C:\Users\Julian\Secrets\firebase_key.json`, fuera de cualquier repo) y pasá la ruta como argumento:

```python
from Seguridad.aceptar_solicitudes import main
main(r"C:\Users\Julian\Secrets\firebase_key.json")
```

### Paso 2 — Crear `pyproject.toml` en esa carpeta

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "seguridad-licencias"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "requests",
    "firebase-admin",
]

[tool.setuptools.packages.find]
where = ["src"]
```

### Paso 3 — Instalar en modo editable en CADA venv (Cronos y ARCA)

Desde cada proyecto, activando su propio venv:

```powershell
# Ejemplo para el venv de este proyecto (ARCA Downloader)
.\venv_nuevo\Scripts\pip.exe install -e "C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias"
```

Repetí lo mismo con el venv de Cronos. A partir de acá, en cualquiera de los dos proyectos:

```python
from Seguridad.interfaz import main
main(programa="arca")     # o "cronos", según el proyecto
```

Con `-e` (editable), si mañana corregís algo en la carpeta compartida, el cambio se refleja al toque en ambos proyectos sin reinstalar nada.

### Paso 4 — Compatibilidad con PyInstaller / auto-py-to-exe

Vi que usás `auto-py-to-exe` para generar el ejecutable. Los instalables editables modernos de `pip` (PEP 660) a veces no son detectados correctamente por PyInstaller porque no copian archivos reales al `site-packages`, solo un "puente" de importación. Si al generar el `.exe` te tira `ModuleNotFoundError: Seguridad`, dos salidas:

1. Instalar en modo editable "compatible" (heredado), que sí deja un `.pth` apuntando a la carpeta real:
   ```powershell
   pip install -e "C:\...\seguridad-licencias" --config-settings editable_mode=compat
   ```
2. O decirle explícitamente a PyInstaller dónde buscar, agregando en `auto-py-to-exe` (pestaña "Advanced" → "Additional Search Path") o en el `.spec` generado:
   ```python
   pathex=[r"C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias\src"]
   ```

Probá generar el `.exe` una vez después de migrar, antes de asumir que quedó andando.

### Alternativa más simple (sin empaquetar): variable `PYTHONPATH`

Si no querés lidiar con `pyproject.toml`, alcanza con que el intérprete tenga en su `PYTHONPATH` la carpeta que **contiene** a `Seguridad` (no `Seguridad` en sí):

```powershell
setx PYTHONPATH "C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias\src"
```

Esto funciona para correr los scripts con `python main.py`, pero **no** para el `.exe` compilado: PyInstaller no lee `PYTHONPATH` del sistema al momento de build, así que con esta alternativa vas a tener que agregar el `pathex` (paso 4, opción 2) de todos modos antes de compilar. Por eso, para tu caso (que compilás a `.exe`), la opción de `pip install -e` es la más segura a largo plazo.

## 3. Recomendaciones a futuro

- **No commitear `firebase_key.json` ni la `API_KEY` real** a git. Si `firebase_key.json` ya está en el historial del repo, hay que rotar esa credencial en Firebase (revocarla y generar una nueva), porque borrarla del working tree no la saca del historial.
- **Reglas de seguridad de Firestore**: como `licencia_autorizada` usa la API REST con una API key pública (no admin), asegurate de que las reglas de Firestore solo permitan `read` en `licencias` y `create` (no `read`/`update`/`delete`) en `solicitudes` para clientes no autenticados. Si no las revisaste últimamente, vale la pena chequearlas ahora que cambia el esquema de IDs.
- **Test de integración manual** antes de distribuir: crear una solicitud de prueba para "cronos", aprobarla con `aceptar_solicitudes.py`, y confirmar que NO aparece como autorizada al pedir licencia con `programa="arca"` en el mismo equipo (y viceversa). Los tests unitarios ya cubren esto a nivel de código, pero vale la pena verlo una vez contra Firestore real.
- **Versión de Python**: tus instrucciones de proyecto piden 3.9.13, pero el intérprete del venv que encontré en `venv_nuevo` es 3.10.12. No debería causar problemas con este código (no usa sintaxis exclusiva de 3.10+), pero si te importa la consistencia exacta, valdría la pena recrear el venv con 3.9.13.

## 4. Estado actual y qué falta (actualizado 2026-06-30)

Lo que ya está hecho:

- `src/Seguridad/` fue **eliminada de este repo**.
- El paquete compartido quedó armado en `C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias\` (con `pyproject.toml`, `src/Seguridad/...`, tests y `README.md`).
- Validé la instalación editable y los 14 tests en un entorno de prueba descartable (no en tu venv real, porque no puedo ejecutar `.exe` de Windows desde donde trabajo) — todo pasó.
- `aceptar_solicitudes.py` ya no asume una ruta relativa al `firebase_key.json`; ahora la toma de la variable de entorno `FIREBASE_KEY_PATH` o la pide por consola.
- **Encontré `firebase_key.json` trackeado en git** (commit `ed8c3f71`) dentro de `src/Seguridad/`. Lo moví a `MarianoMorteo/secrets/firebase_key.json` (carpeta nueva, gitignoreada) y actualicé `.gitignore`.

Lo que falta que hagas vos (no lo puedo hacer desde acá):

1. **Instalar el paquete en tu venv real:**
   ```powershell
   cd "C:\Users\Julian\Desktop\Programacion\Proyectos\MarianoMorteo"
   .\venv_nuevo\Scripts\pip.exe install -e "C:\Users\Julian\Desktop\Programacion\libs\seguridad-licencias"
   ```
   Hasta que corras esto, `main.py` va a fallar con `ModuleNotFoundError: Seguridad`.

2. **Rotar la credencial de Firebase.** Que ahora esté gitignoreada no la invalida — si el repo llegó a subirse a GitHub (el mensaje del commit dice "renovacion completa del github"), esa clave quedó expuesta en el historial. Andá a Firebase Console → configuración del proyecto → Cuentas de servicio → generar una clave nueva, y borrá/revocá la vieja (`private_key_id` que empieza con `46e9b451...`). Después reemplazá `MarianoMorteo/secrets/firebase_key.json` con la nueva.

3. Sacar `firebase_key.json` del **historial** de git si te importa (no solo del working tree). Esto requiere reescribir historia (`git filter-repo` o similar) y forzar push — hacelo recién después de rotar la clave, total la vieja ya no sirve.

4. Repetir el paso 1 en el venv del proyecto Cronos cuando lo tengas a mano.
