Actuá como un desarrollador Python senior. En ESTA carpeta (vacía) quiero construir un **programa de prueba mínimo** que sirva para **probar de punta a punta un sistema de auto-actualización remota basado en Firebase**, antes de aplicarlo en un proyecto real más grande.

La idea: es un ejecutable de Windows (compilado con PyInstaller / auto-py-to-exe, modo one-file) que puede **actualizarse solo**, sin reenviar el `.exe` a mano cada vez. Quiero un programita tonto pero completo para validar que el mecanismo de actualización realmente funciona.

## Qué construir

### 1. App de prueba (`main.py`)
Un programa de consola trivial cuyo único objetivo es que se vea fácil "qué versión soy". Al arrancar y en cada vuelta del menú, mostrá bien grande la versión actual (ej. `=== App de Prueba v1.0.0 ===`). Menú:
- `1) Hacer algo` → imprime algo simple (ej. la hora actual o un número al azar).
- `2) Chequear actualizaciones` → llama al updater.
- `0) Salir`.

Que la versión se lea desde `version.py` (no hardcodeada en el print), así al actualizar se ve cambiar el número.

### 2. `version.py`
Constantes: `PROGRAM_ID = "testapp"`, `VERSION = "1.0.0"`, y `URL_MANIFIESTO = ""` (a completar con la URL del manifest en Firebase Storage). Documentá que hay que subir `VERSION` antes de cada build.

### 3. `updater.py` — AUTOCONTENIDO y REUTILIZABLE
Solo librería estándar (sin dependencias externas) y sin importar nada del resto del proyecto, para poder copiarlo tal cual a cualquier programa futuro. Función pública `check_for_updates(program_id, version_actual, url_manifiesto)` que:
1. Descarga un manifiesto JSON desde `url_manifiesto` (con `urllib`). Formato esperado:
   `{"version": "...", "url": "<url del exe nuevo>", "sha256": "<hash hex>", "changelog": "..."}`.
2. Compara la versión remota contra la local con comparación **numérica por partes** (que `"1.0.10"` sea mayor que `"1.0.2"`).
3. Si hay una más nueva: muestra el changelog y pide confirmación (s/n).
4. Descarga el nuevo `.exe` a un archivo temporal y **verifica el SHA-256** (si no coincide, cancela y borra el archivo).
5. Aplica el reemplazo en Windows: como un `.exe` en ejecución no puede sobrescribirse a sí mismo, escribí un `.bat` que espere a que el proceso cierre (por nombre de imagen, con `tasklist`), reemplace el exe viejo por el nuevo (`move /y`), relance el programa (`start`) y se autoborre. Lanzá ese `.bat` en una consola nueva y cerrá el programa con `os._exit(0)`.
6. Detectá modo desarrollo: si `getattr(sys, "frozen", False)` es False (corriendo como `.py`, no como exe), avisá que no se puede reemplazar y **no hagas nada destructivo**.

Manejá errores de red/lectura sin crashear (mensajes claros y retorno limpio).

### 4. Tooling de release (`release/generar_manifest.py`)
Script para el desarrollador (NO se compila en el exe): recibe por línea de comandos `<ruta_al_exe> <version> <url_del_exe> "<changelog>"`, calcula el SHA-256 del exe y escribe un `manifest.json` listo para subir.

### 5. Guía de Firebase (`release/GUIA.md`)
Paso a paso, pensado para alguien que NO sabe Firebase:
- Activar **Storage** en la consola de Firebase y crear una carpeta `updates`.
- Reglas de **lectura pública SOLO** de la carpeta `updates` (y aclarar que las reglas de Storage son distintas de las de Firestore).
- Cómo armar la **URL pública estable**: `https://firebasestorage.googleapis.com/v0/b/BUCKET/o/updates%2FARCHIVO?alt=media` (el `/` va como `%2F`). Aclarar que NO se use el botón "Copiar URL de descarga" de la consola, porque trae un `&token=` que puede cambiar y rompería la URL que queda compilada en el exe.
- El flujo por release.

### 6. Instrucciones de build (`README.md`)
Cómo compilar el one-file exe (comando de PyInstaller o auto-py-to-exe) y el recordatorio de subir `VERSION` antes de compilar.

## Requisitos técnicos
- Python 3.9, Windows.
- Seguí PEP 8, docstrings claros y manejo de errores robusto.
- El `updater.py` no debe depender de nada del proyecto (copiable) ni de librerías externas (solo stdlib).

## Plan de prueba (ponelo en el README)
Explicá cómo probar el ciclo completo:
1. Compilá la app con `VERSION = "1.0.0"` → ese es tu exe "instalado".
2. Cambiá algo visible y `VERSION = "1.0.1"`, compilá de nuevo → ese es el exe "nuevo".
3. En Firebase, subí a `updates/` el exe 1.0.1 y un `manifest.json` con `version: "1.0.1"`, su URL y su hash (usá `generar_manifest.py`).
4. Completá `URL_MANIFIESTO` en `version.py` con la URL del manifest… pero OJO: eso ya tiene que estar en el build 1.0.0. Así que en la práctica: poné la URL del manifest en `version.py` ANTES del paso 1, y recién después subí el manifest a Firebase.
5. Corré el exe 1.0.0 → opción "Chequear actualizaciones" → confirmá.
6. Verificá que baje el 1.0.1, valide el hash, se reemplace y relance mostrando `v1.0.1`.

Antes de empezar a codear, si algo no está claro o hay decisiones importantes, preguntame. Cuando termines, dame un resumen de lo que creaste y las instrucciones para probarlo.
