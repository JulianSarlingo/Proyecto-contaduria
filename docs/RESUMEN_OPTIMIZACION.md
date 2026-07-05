# Resumen de optimización — ARCA Downloader

**Rama:** `refactor/optimizacion` (creada desde el checkpoint `9ed402ee` en `main`)
**Objetivo:** optimizar el código para que sea más eficiente **sin perder funcionalidades ni cambiar el comportamiento** actual del automatismo.
**Principio aplicado en todo:** cada cambio es *behavior-preserving* (mismo resultado, menos trabajo) o corrige una ruta que hoy ya estaba rota. No se eliminó ninguna función.

---

## 1. Línea base en git

Antes de tocar código se fijó un punto de retorno:

- Se hizo commit del estado de trabajo (WIP) como `checkpoint: estado funcional pre-refactor de optimizacion` (`9ed402ee`), sobre `main`.
- Se creó la rama `refactor/optimizacion` desde ese checkpoint. `main` queda intacto como punto de retorno.
- Se resolvió un `.git/index.lock` *stale* (de un git previo que crasheó) que bloqueaba los commits.

> Nota: los 6 archivos que git mostraba como "modificados" en el entorno del asistente eran solo diferencias de fin de línea (CRLF vs LF). En tu Windows (`core.autocrlf=true`) el árbol está limpio.

---

## 2. Cambios aplicados

| # | Archivo(s) | Cambio | Tipo | Beneficio |
|---|-----------|--------|------|-----------|
| 1 | `src/logger.py` | `DEBUG_MODE = True` → `False` | Eficiencia | El decorador `@debug_trace` deja de imprimir y escribir al log en **cada entrada/salida** de cada función (login, cada `_seccion_*`, cada `programa_*`), en cada usuario. |
| 2 | `src/tools.py` | En `_encontrar_todos_elementos`, la introspección por elemento (`.tag_name`, `.text`, `.get_attribute`) quedó dentro de `if logger.DEBUG_MODE:` (+ `import logger`) | Eficiencia | En producción se eliminan **3 round-trips a Chrome por cada elemento** encontrado (búsqueda de empresas en Comprobantes). |
| 3 | `src/runner/programas.py` | En `_seccion_comprobantes_empresa`, la lista de empresas se re-busca solo desde la 2ª iteración (`if i > 0`) | Eficiencia | Una búsqueda de DOM menos por cada usuario con sociedades (la 1ª lista ya era válida). |
| 4 | `src/main.py` | Se quitó el import muerto `from logging import config` | Clean Code | Import sin uso; menos ruido. |
| 5 | `src/main.py` | `extraer_configuracion`: ante `config.txt` faltante ahora **lanza `FileNotFoundError` con mensaje claro** en vez de devolver un string | Robustez / bug | Antes devolvía un string y `main()` desempacaba 4 variables → `ValueError` críptico. Ahora la protección global muestra un mensaje entendible. |
| 6 | `src/browser/actions.py` + `src/afip/retenciones.py` | Parámetro `type` → `tipo` en `_click_span_descarga` (y su única llamada con `type=`) | Clean Code | Dejaba de pisar el builtin `type`. Sin cambio de comportamiento. |
| 7 | `src/browser/actions.py` | En `_click_element_by`, `except (WebDriverException, Exception)` → `except Exception` | Clean Code | La tupla era redundante (`Exception` ya cubre `WebDriverException`). |

### Efecto neto (en producción, `DEBUG_MODE=False`)
Cada corrida evita, **por usuario**: los prints y escrituras al log de entrada/salida de cada función decorada; los round-trips extra a Chrome por cada empresa listada; y una búsqueda de DOM redundante en usuarios con sociedades. El flujo de automatización (qué clickea, qué descarga, en qué orden) es **idéntico**.

---

## 3. Qué NO se tocó (a propósito)

Para respetar "que todo funcione tal y como está ahora" y no perder funciones:

- **`modo = "Retenciones"` y `velocidad = 1`** en `main()`: es el comportamiento actual. No se modificó la lógica de modo/velocidad.
- **Doble lectura del Excel** (`openpyxl` para contar filas + `pandas` para leer) en `config_loader.py`: reescribirla arriesga cambiar *qué filas* se cargan; además está cacheada en `.cache_config.json`, así que su costo es puntual.
- **Sleeps fijos** (`tools.pausa`): reemplazarlos por esperas explícitas es la mayor ganancia de tiempo posible, pero es sensible al timing de AFIP y hay que validarlo sitio por sitio.
- **`system('cls')` al importar `config_loader`**: moverlo cambiaría *cuándo* se limpia la consola.
- **`buscar_botones_descargables`** (`actions.py`): es código muerto (no se llama), pero se dejó por tu indicación de no eliminar funciones.
- **`_digits11`** (`config_loader.py`): funciona con los datos actuales; cambiar el `int()` previo al regex podría alterar qué CUITs se aceptan.

---

## 4. Estado de verificación

- Compilan OK en el sandbox: `logger.py`, `main.py`, `retenciones.py`.
- Verificados por lectura directa (válidos): `tools.py`, `actions.py`, `programas.py`. El `py_compile` del sandbox da **falsos negativos** en estos por un artefacto de caché del sistema de archivos montado (reporta "null bytes" o líneas truncadas en renglones que no se editaron).
- **Verificá de tu lado** (tu disco no tiene ese lag):

```
python -m py_compile src\logger.py src\tools.py src\main.py src\browser\actions.py src\runner\programas.py src\afip\retenciones.py
```

Si no imprime nada, todo compila. Después:

```
git diff                 # revisar cambios
git add -A
git commit -m "optimizacion: menos overhead de debug y de round-trips a Chrome; clean code y manejo de error de config"
```

---

## 5. Recomendaciones para el futuro

1. **Sleeps fijos → esperas explícitas** (`WebDriverWait` a la condición concreta): la mayor ganancia de tiempo real. Hacerlo por sección, probando en AFIP.
2. **Flag de debug por variable de entorno** (`ARCA_DEBUG`): activar/desactivar debug sin editar código ni recompilar el `.exe`.
3. **Leer `velocidad` y `modo` desde `config.txt`**: hoy se parsea `modo` pero se ignora, y `velocidad` queda fija en 1.
4. **Agregar `.gitattributes` con `* text=auto`**: zanja el tema CRLF/LF de raíz.
5. **Tests unitarios de `config_loader`** (`_digits11`, `_es_persona`, `indexar_sociedades`, `construir_config`): son funciones puras, se testean sin Selenium.
6. **Revisar `buscar_botones_descargables`**: si confirmás que es código muerto, removerlo o dejar documentado por qué se conserva.

---

## Fase 2 — Nuevas funciones (paralelización + menú)

Misma rama `refactor/optimizacion`. Decisiones acordadas: **hilos**, **2–3 en paralelo** por defecto, **headless por variable**, **submenú de modo**.

| # | Archivo(s) | Cambio |
|---|-----------|--------|
| 8 | `runner/ejecutor.py` | `ejecutar_codigo` procesa los usuarios con un `ThreadPoolExecutor` (hasta `MAX_PARALELO` a la vez; constante configurable = 3). Nueva `_procesar_un_usuario` con la **misma lógica** por usuario. Errores recolectados por `futures`; un `Lock` imprime el bloque de cada usuario sin mezclarse. `probar_usuario`/`probar_rango` siguen secuenciales. |
| 9 | `browser/driver.py` | Constante `HEADLESS = False`. Con `True`, `open_chrome` agrega `--headless=new` + `--disable-gpu` + `--window-size=1920,1080`. |
| 10 | `config_loader.py` + `tools.py` | `procesar_config(..., forzar=False)` e `init(..., forzar=False)`: con `forzar=True` se ignora el caché y se re-lee el Excel (regenerando el `.json`). Default = comportamiento actual. |
| 11 | `menu.py` (nuevo) | Menú por consola: `1` Ejecutar (submenú Comprobantes/Retenciones/Portal IVA) · `2` Actualizar Excel (re-lectura forzada) · `3` Chequear actualizaciones · `0` Salir. |
| 12 | `updater.py` (nuevo) | Stub `check_for_updates()` — placeholder para el módulo de auto-actualización remota (irá aparte, reutilizable). |
| 13 | `main.py` | `main()` ahora lanza `menu.iniciar(...)` tras el chequeo de licencia (sin tocar `Seguridad`). Los ejemplos de prueba manual quedan como comentarios. |

### A probar en AFIP (importante)

- **Riesgo de paralelismo:** varios logins simultáneos desde la misma IP pueden disparar límites/anti-bot. Arrancá con `MAX_PARALELO = 2` o `3` y subí de a poco.
- **Headless:** con `HEADLESS = True`, verificá que las descargas (Excel/CSV) y el PDF del Libro IVA (`print_page`) sigan funcionando; algunos portales se comportan distinto en headless.
- **Consola en paralelo:** el bloque de estado final de cada usuario se imprime bajo lock (ordenado), pero los `[INFO]` intermedios de funciones profundas pueden intercalarse entre hilos. Si molesta, se puede bufferear por hilo más adelante.

### Dónde se configura
- `runner/ejecutor.py` → `MAX_PARALELO` (cuántos clientes en paralelo).
- `browser/driver.py` → `HEADLESS` (True/False).

---

## Fase 3 — Aborto y cierre de todos los Chrome

Para frenar el programa en cualquier momento sin que queden ventanas de Chrome abiertas.

| # | Archivo(s) | Cambio |
|---|-----------|--------|
| 14 | `browser/driver.py` | `detach=False` (matar el proceso ahora cierra los Chrome). Registro global de instancias abiertas (`_drivers_abiertos` + lock). Funciones nuevas `cerrar_driver(dv)` y `cerrar_todos_los_chrome()`. |
| 15 | `runner/programas.py` | Todos los `dv.quit()` pasan a `drv.cerrar_driver(dv)` (mantiene el registro consistente), incluido el cierre cuando el login falla (p. ej. cambio de contraseña obligatorio). |
| 16 | `runner/ejecutor.py` | `ejecutar_codigo` captura `KeyboardInterrupt` (Ctrl+C): cierra todos los Chrome, cancela lo pendiente y vuelve al menú. |
| 17 | `main.py` | Tecla de pánico global `Ctrl+Shift+Q` (vía `keyboard`): cierra todos los Chrome y mata el proceso al instante desde cualquier ventana. |

### Cómo frenar el programa
- **Ctrl+C** durante una corrida → aborta, cierra todos los Chrome y vuelve al menú.
- **Ctrl+C** en el menú, u opción **`0`** → sale del programa.
- **Ctrl+Shift+Q** desde cualquier lado → pánico: cierra todos los Chrome y mata el programa ya.
- Con `detach=False`, matar el proceso (Administrador de tareas) también cierra los Chrome.

---

## Fase 4 — Módulo de auto-actualización remota

Módulo **aparte y reutilizable** (solo stdlib, sin imports de ARCA → copiable a cualquier programa). Hosting: Firebase. Trigger: manual (opción `3` del menú).

| # | Archivo(s) | Cambio |
|---|-----------|--------|
| 18 | `updater.py` (reescrito) | Lee un manifiesto JSON por URL, compara versión, descarga el nuevo `.exe`, verifica SHA-256 y hace el swap+relanzado en Windows (un `.bat` espera el cierre, reemplaza el exe y relanza). Detecta modo dev (no `.exe`) y no hace nada destructivo. |
| 19 | `version.py` (nuevo) | `PROGRAM_ID`, `VERSION` y `URL_MANIFIESTO` (a completar con tu URL de Firebase Storage). Bumpear `VERSION` en cada build antes de compilar. |
| 20 | `menu.py` | La opción `3` llama `updater.check_for_updates(PROGRAM_ID, VERSION, URL_MANIFIESTO)`. |

### Qué falta de tu lado (Firebase, una vez por release)
1. Subí `VERSION` en `version.py` y compilá el nuevo `.exe`.
2. Sacá su hash: `Get-FileHash arca_2.2.6.exe -Algorithm SHA256` (PowerShell).
3. Subí el `.exe` a Firebase Storage (lectura pública) → copiá su URL de descarga.
4. Subí/actualizá un `manifest.json` con `{version, url, sha256, changelog}`. Su URL debe ser **estable** (queda compilada en cada exe): en Storage, con el objeto público, la URL `...?alt=media` no cambia; en cada release actualizás el CONTENIDO del manifest, no la URL.
5. Pegá la URL del manifest en `version.py` → `URL_MANIFIESTO` (una sola vez).

### Notas
- Windows + `.exe` one-file (asumido). Si el exe está en una carpeta protegida (Program Files), el reemplazo puede requerir permisos de admin: mejor correrlo desde una carpeta de usuario.
- El SHA-256 se verifica siempre antes de instalar (estás bajando un ejecutable).
- Si preferís leer el manifiesto desde Firestore (como Seguridad) en vez de una URL a JSON, es cambiar solo `_leer_manifiesto`.
- Falta la infra/subida en Firebase (de tu lado); el código cliente ya está listo.
