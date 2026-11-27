# Verificación HTTP anónima — 28/10/2026

**Método:** GitHub Actions con `tools/security/check_public_urls.py`, sin credenciales, sin cookies, sin seguir redirecciones; HEAD y respaldo GET `Range: bytes=0-0` sólo para comprobar estado HTTP, **sin leer ni registrar cuerpos**.

**Evidencia verificable:** [Workflow Run 40717110938](https://github.com/UESVALLE/uesvalle.github.io/actions/runs/40717110938), job `anonymous-http-audit` terminado exitosamente.

| ID | Recurso evaluado | HTTP | Destino/redirección | Interpretación |
|---|---|---:|---|---|
| GH01 | Portal `https://uesvalle.github.io/` | 404 | — | No encontrado en prueba |
| GH02 | Dataset `data/ircas/current/IRCAS.csv` en GitHub Pages | 404 | — | Ruta no encontrada |
| GH03 | `data/inspeccion_sedes/current/inspecciones.json` en GitHub Pages | 404 | — | Ruta no encontrada |
| VR01 | Portal `uesvalle-tableros.vercel.app` | 302 | `vercel.com` | Redirección coherente con autenticación de despliegue |
| VR02 | Dataset directo IRCA en Vercel | 302 | `vercel.com` | Redirección en vez de entrega directa |
| GH04 | Recurso `raw.githubusercontent.com/UESVALLE/uesvalle.github.io/main/data/ircas/current/IRCAS.csv` | 404 | — | No encontrado desde contexto anónimo |
| GH05 | Copia personal `github.com/JavierMarin7/UESVALLE` | 404 | — | No encontrado desde contexto anónimo |

## Dictamen limitado

Las **siete rutas específicas** no entregaron directamente una respuesta de datos `200 OK` durante la prueba anónima, y el proyecto Vercel mantiene `ssoProtection.deploymentType=all`. La redirección `302` no equivale por sí sola a prueba de identidades/roles; un `404` no demuestra eliminación definitiva de otras URL, cachés, forks, copias descargadas o publicaciones antiguas.

No se utilizaron tokens de bypass ni URLs compartidas. No se consultaron todas las URL, ni se verificaron sesiones de usuarios internos ni autorizaciones por ARO.

## Acciones todavía necesarias

- Ampliar muestreo a módulos y rutas históricas; comprobar rutas con y sin barra final.
- Verificar que ninguna publicación alternativa ajena a los dominios evaluados expone archivos.
- Revisar permisos de Google Drive y evidencias incrustadas.
- Implementar autorización en API/BBDD y comprobar pruebas negativas por rol y proceso.
- Repetir prueba anónima tras cada despliegue; registrar sólo códigos, destinos y fecha.

**Seguimiento:** [SEC-01](https://github.com/UESVALLE/uesvalle.github.io/issues/2), [SEC-03](https://github.com/UESVALLE/uesvalle.github.io/issues/4) y [SEC-09](https://github.com/UESVALLE/uesvalle.github.io/issues/10).
