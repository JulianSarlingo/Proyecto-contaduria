Sos un asistente con acceso a GitHub (conector/herramienta de GitHub, o manejando la web). Necesito que dejes armados los **Releases** para la auto-actualización de mi programa, en un repo público dedicado. **Verificá cada paso antes de pasar al siguiente**: si algo no quedó bien, corregilo o avisame, no sigas de largo.

## Contexto (son DOS repos)

- **Código (PRIVADO):** `JulianSarlingo/Proyecto-contaduria` → NO se toca, queda privado.
- **Releases (PÚBLICO):** `JulianSarlingo/arca-releases` → YA lo creé, pero está **completamente vacío** (sin commits, sin README). Acá van el `.exe` y el `manifest.json`.

Mi programa se auto-actualiza leyendo `manifest.json` desde el repo público, en un Release con tag fijo **`latest`**; ese manifest apunta al `.exe` más nuevo (Release con tag versionado, ej. `v2.3.0`). El programa **ya tiene compilada** esta URL (NO cambiarla):
`https://github.com/JulianSarlingo/arca-releases/releases/download/latest/manifest.json`

Forma del `manifest.json` (el `sha256` lo completo yo con un script local):
```json
{
  "version": "2.3.0",
  "url": "https://github.com/JulianSarlingo/arca-releases/releases/download/v2.3.0/arca.exe",
  "sha256": "<lo completo yo>",
  "changelog": "Ejecucion en paralelo, menu interactivo, aborto de Chrome y auto-actualizacion."
}
```

## Pasos (verificá SIEMPRE cada uno antes de seguir)

**Paso 1 — Repo público y ya no vacío.**
- Confirmá que `arca-releases` es **público**. Si es privado, la descarga de assets pide token y el updater falla → decime que lo haga público.
- Como está vacío, todavía no se pueden crear tags ni releases. Creá un commit inicial: un `README.md` en la rama `main` con algo como: "Releases y actualizaciones de ARCA Downloader. No borrar el release 'latest'."
- **Verificá:** que el repo sea público y que tenga la rama `main` con el README. Si no, corregí antes de avanzar.

**Paso 2 — Release `v2.3.0` (para el .exe).**
- Creá un Release con tag **`v2.3.0`** (sobre el commit del README), título "v2.3.0", notas = el changelog de arriba.
- **No vas a poder subir el `.exe`** (~44 MB): pausá y decime "subí `arca.exe` como asset al release v2.3.0". Esperá a que confirme.
- **Verificá:** que el release exista con su tag y que, una vez que yo suba el exe, `https://github.com/JulianSarlingo/arca-releases/releases/download/v2.3.0/arca.exe` descargue.

**Paso 3 — Release `latest` (para el manifest).**
- (Mientras tanto yo genero el `manifest.json` con el hash del exe.)
- Creá un Release con tag **`latest`**, título "Manifiesto de actualizaciones — NO BORRAR", con una nota aclarando que solo contiene el `manifest.json` que leen los updaters.
- Pausá y decime "subí `manifest.json` como asset al release latest". Esperá a que confirme.
- **Verificá:** que `https://github.com/JulianSarlingo/arca-releases/releases/download/latest/manifest.json` devuelva el JSON, y que su `version`, `url` y `sha256` sean coherentes.

**Paso 4 — Verificación final.**
- Confirmá que las DOS URLs (manifest y exe) resuelven y descargan.
- Confirmá que el `version` del manifest ("2.3.0") coincide con la del programa.

## Cosas que hago YO (no las podés hacer vos)
- Compilar el `.exe` (VERSION 2.3.0) y subirlo como asset al release `v2.3.0`.
- Generar el `manifest.json` con el hash (`python release/generar_manifest.py <exe> 2.3.0 <url_exe> "<changelog>"`) y subirlo como asset al release `latest`.

## Forma de trabajo
Andá de a un paso. Cada vez que necesites que suba un archivo o haga algo de mi lado, **pará y decímelo en una sola línea clara**: qué archivo, a qué release/tag y con qué nombre exacto. **Verificá cada paso antes de avanzar** y no des por terminado hasta confirmar que las dos URLs finales funcionan.
