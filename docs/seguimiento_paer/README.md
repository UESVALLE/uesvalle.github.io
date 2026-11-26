# Tablero PAER · Seguimiento del diagnóstico (acceso con clave en servidor)

## Arquitectura
| Qué | Dónde |
|---|---|
| Página (`dashboards/seguimiento_paer/index.html`) y funciones (`api/paer/*`) | Este repositorio (código, sin cifras) |
| Datos agregados (`paer/paer_tablero.json`) | **Vercel Blob privado**, solo lo lee `api/paer/data.js` con sesión válida |
| Maestros M01–M05, actas, bitácora y scripts | Drive `05_PROYECTOS\02_PAER` (no se suben a GitHub) |

Flujo: el navegador pide `/api/paer/data`; sin cookie válida responde 401 y la página muestra el acceso; `POST /api/paer/login` valida la clave en el servidor y entrega una cookie firmada (HttpOnly, 8 h).

## Configuración única en Vercel (la hace el administrador)
1. Proyecto `uesvalle-tableros` > Storage > Create > Blob > **Private** (conectado al proyecto).
2. Settings > Environment Variables (Production y Preview):
   - `PAER_PASSWORD`: clave de acceso.
   - `PAER_SESSION_SECRET`: texto largo aleatorio (mínimo 32 caracteres).
3. Redesplegar. Cambiar la clave = cambiar la variable y redesplegar.

## Actualizar los datos (desde el equipo del proyecto, no desde el repositorio)
`python3 build_paer_json.py <carpeta_maestros> paer_tablero.json` genera el JSON desde M01, M03 y M04.
`node subir_blob.mjs paer_tablero.json` lo sube a `paer/paer_tablero.json` (requiere `BLOB_READ_WRITE_TOKEN` del almacén).
No hay que hacer commit ni redespliegue: el tablero lee el último archivo.

## Reglas
- Nunca subir datos del PAER a `data/` ni a GitHub (el repositorio es público; ya está en `.gitignore`).
- El JSON solo trae programación y estado de ejecución, sin NIT, representantes ni contactos.
