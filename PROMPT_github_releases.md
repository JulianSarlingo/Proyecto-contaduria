Sos un asistente con acceso a GitHub (mediante un conector/herramienta de GitHub, o manejando la web de GitHub). Ayudame a configurar la **distribución de actualizaciones** de mi programa. La idea: mi **código queda privado**, y **solo los releases** (el `.exe` y el `manifest.json`) van en un repo **público aparte**. Hacé todo lo que puedas con tus herramientas; lo que no puedas (subir archivos binarios), pausá y decime **exactamente qué subir y dónde**, y lo hago yo.

## Contexto (importante: son DOS repos)

- **Código (PRIVADO):** `JulianSarlingo/Proyecto-contaduria` → NO se toca acá y queda privado.
- **Releases (PÚBLICO):** `JulianSarlingo/arca-releases` → repo dedicado SOLO a publicar el `.exe` y el `manifest.json`. Si todavía no existe, hay que crearlo **público**.

Mi programa se auto-actualiza leyendo un `manifest.json` desde el repo **público** de releases, en un Release con tag fijo **`latest`**. Ese manifest apunta al `.exe` más nuevo, que vive en un Release con tag versionado (ej. `v2.3.0`). El programa **ya tiene compilada** esta URL (NO cambiarla, tiene que quedar válida):
`https://github.com/JulianSarlingo/arca-releases/releases/download/latest/manifest.json`

## Estructura que hay que dejar armada (todo en el repo PÚBLICO `arca-releases`)

1. Un Release con tag **`v2.3.0`** que contenga el asset **`arca.exe`**. Su URL de descarga será:
   `https://github.com/JulianSarlingo/arca-releases/releases/download/v2.3.0/arca.exe`
2. Un Release con tag **`latest`** que contenga el asset **`manifest.json`** (la URL de arriba, la que está compilada en el exe).
3. El `manifest.json` tiene esta forma (el `sha256` lo genero yo con un script local):
   ```json
   {
     "version": "2.3.0",
     "url": "https://github.com/JulianSarlingo/arca-releases/releases/download/v2.3.0/arca.exe",
     "sha256": "<lo completo yo>",
     "changelog": "Ejecucion en paralelo, menu interactivo, aborto de Chrome y auto-actualizacion."
   }
   ```

## Qué necesito que hagas vos

1. **Asegurate de que exista el repo PÚBLICO `arca-releases`.** Si no existe, crealo **público** con un README mínimo (ej. "Releases y actualizaciones de ARCA Downloader. No borrar el release 'latest'."). Si no podés crearlo o hacerlo público, decime que lo haga yo. **No toques el repo del código (`Proyecto-contaduria`); ese queda privado.**
2. En **`arca-releases`**, creá el Release con tag **`v2.3.0`**, título "v2.3.0", notas = el changelog de arriba. **No vas a poder subir el `.exe`** (~44 MB): al crearlo, pausá y decime "subí `arca.exe` como asset a este release".
3. En **`arca-releases`**, creá el Release con tag **`latest`**, título tipo "Manifiesto de actualizaciones — NO BORRAR", con una nota que aclare que solo contiene el `manifest.json` que leen los updaters. Igual: decime que suba `manifest.json` como asset ahí.
4. **Verificá al final** (si podés hacer requests web): que `https://github.com/JulianSarlingo/arca-releases/releases/download/latest/manifest.json` devuelva el JSON, y que la `url` del `.exe` que figura adentro exista y descargue.

## Cosas que hago YO (no las podés hacer vos)

- Compilar el `.exe` (con `VERSION = "2.3.0"`) en mi máquina.
- Generar el `manifest.json` con mi script local (`python release/generar_manifest.py <exe> 2.3.0 <url_exe> "<changelog>"`), que calcula el SHA-256.
- Subir los dos archivos (`arca.exe` y `manifest.json`) como assets a los releases que vos crees.

## Orden sugerido (para que me pauses en el momento justo)

1. Verificás/creás el repo público `arca-releases`.
2. Creás el release `v2.3.0` → me pedís que suba `arca.exe`.
3. (Yo subo el exe y genero el `manifest.json` con el hash.)
4. Creás el release `latest` → me pedís que suba `manifest.json`.
5. Verificás que las dos URLs resuelvan.

## Cómo trabajamos

Andá paso a paso. Cada vez que necesites que suba un archivo o haga algo de mi lado, **pará y decímelo en una sola línea clara**: qué archivo, a qué repo/release/tag y con qué nombre exacto. Yo lo hago y te aviso para seguir. No des por terminado hasta confirmar que las dos URLs finales funcionan.
