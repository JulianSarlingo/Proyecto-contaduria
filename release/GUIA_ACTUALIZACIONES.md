# Cómo publicar actualizaciones (Firebase) — paso a paso

Guía para vos (el desarrollador). Explica cómo subir una versión nueva para que los programas se actualicen solos con la opción **"3) Chequear actualizaciones"**.

## La idea en 30 segundos

1. Subís el `.exe` nuevo a **Firebase Storage**.
2. Subís un archivo `manifest.json` que dice: *"la última versión es X, está en tal URL, su hash es tal"*.
3. El programa lee ese `manifest.json`, ve que hay una versión más nueva que la suya, la baja, valida el hash y se reemplaza solo.

## ⚠️ Importante: el arranque (leé esto primero)

El auto-updater **solo funciona en exes que ya lo tienen adentro**. El `.exe` viejo (2.2.5) no lo tiene, así que ese no se puede auto-actualizar. Por eso:

- **La primera vez** compilás el `.exe` con este código nuevo (que ya trae el updater) y lo repartís a mano, como venías haciendo.
- **De ahí en adelante**, todas las próximas actualizaciones ya son automáticas.

---

## PARTE A — Preparar Firebase (una sola vez)

1. Entrá a **https://console.firebase.google.com** y abrí tu proyecto (el mismo que usás para las licencias).
2. Menú izquierdo: **Compilación → Storage** ("Build → Storage"). Si nunca lo usaste, tocá **"Comenzar" / "Get started"**, aceptá y elegí una ubicación.
3. Arriba de la pestaña **Files** vas a ver el nombre de tu *bucket*, algo como `gs://tu-proyecto.appspot.com` (o `...firebasestorage.app`). **Anotá ese nombre** (sin el `gs://`): lo vas a usar para armar las URLs.
4. Creá una carpeta llamada **`updates`** (botón "Create folder" / "Crear carpeta").
5. Reglas para que el programa pueda **leer sin loguearse**. Andá a la pestaña **Rules (Reglas)** y pegá esto, luego **Publish**:

   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {

       // Actualizaciones: lectura pública, nadie escribe desde afuera
       match /updates/{allPaths=**} {
         allow read: if true;
         allow write: if false;
       }

     }
   }
   ```

   > Estas son las reglas de **Storage**, que son **distintas** de las de Firestore que usás para las licencias — no se pisan entre sí. Con esto, solo la carpeta `updates` queda de lectura pública.

---

## PARTE B — Publicar una versión nueva (cada vez que saques una)

1. **Subí la versión** en `src/version.py` (ej. `VERSION = "2.3.0"`) y **compilá** el `.exe`.
2. **Subí el `.exe`** a Storage: pestaña **Files → carpeta `updates` → "Upload file"**, elegí tu `arca_2.3.0.exe`.
3. **Armá la URL pública del `.exe`** (formato estable, ver más abajo). Ejemplo:
   `https://firebasestorage.googleapis.com/v0/b/tu-proyecto.appspot.com/o/updates%2Farca_2.3.0.exe?alt=media`
4. **Generá el `manifest_arca.json`** con el script (te calcula el hash solo):

   ```
   python release/generar_manifest.py "ruta\al\arca_2.3.0.exe" 2.3.0 "URL_DEL_EXE_DEL_PASO_3" "Que cambio en esta version"
   ```

5. **Subí ese `manifest_arca.json`** a la carpeta `updates` de Storage (reemplaza el anterior si ya había).
6. Listo. Los clientes, al tocar la opción `3`, ven la nueva versión y se actualizan.

> **Solo la primera vez** además pegás la URL del **manifest** en `src/version.py` → `URL_MANIFIESTO`. Después nunca más: siempre reemplazás el *contenido* del mismo `manifest_arca.json`, no su URL.

---

## Cómo se arma la URL pública (estable)

Formato:

```
https://firebasestorage.googleapis.com/v0/b/BUCKET/o/updates%2FARCHIVO?alt=media
```

- **BUCKET** = tu bucket, sin el `gs://` (ej. `tu-proyecto.appspot.com`).
- **ARCHIVO** = el nombre del archivo (ej. `arca_2.3.0.exe` o `manifest_arca.json`).
- La barra `/` entre `updates` y el archivo se escribe **`%2F`**.

Ejemplos:

- **Manifest** (esta URL va en `version.py`):
  `https://firebasestorage.googleapis.com/v0/b/tu-proyecto.appspot.com/o/updates%2Fmanifest_arca.json?alt=media`
- **Exe 2.3.0** (esta URL va DENTRO del manifest):
  `https://firebasestorage.googleapis.com/v0/b/tu-proyecto.appspot.com/o/updates%2Farca_2.3.0.exe?alt=media`

⚠️ Usá esta URL con `?alt=media`. **No** uses el botón *"Copiar URL de descarga"* de la consola: esa trae un `&token=...` que puede cambiar si re-subís el archivo, y rompería la URL que quedó compilada en el `.exe`.

---

## Chequeo rápido (si algo no anda)

- **¿La URL del manifest funciona?** Pegala en el navegador: tenés que ver el JSON. Si te da error de permisos → revisá las reglas (Parte A, paso 5).
- **El programa dice "no hay URL configurada"** → falta completar `URL_MANIFIESTO` en `version.py`.
- **Dice "el hash no coincide"** → el `sha256` del manifest no corresponde al exe subido. Regenerá el manifest con el script sobre el exe correcto y volvé a subirlo.
- **"Ya tenés la última versión"** aunque subiste una nueva → el número de `version` en el manifest no es mayor que el `VERSION` del programa. Revisá que subiste el número (ej. 2.3.0 → 2.3.1).

---

## Resumen del flujo por release

`subir VERSION en version.py` → `compilar exe` → `subir exe a Storage` → `armar URL del exe` → `python generar_manifest.py ...` → `subir manifest_arca.json a Storage` → listo.
