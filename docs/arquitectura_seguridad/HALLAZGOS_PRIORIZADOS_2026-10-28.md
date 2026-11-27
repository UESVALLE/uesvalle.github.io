# Auditoría técnica — Hallazgos priorizados (28/10/2026)

**Importante:** lectura estática de código y configuración. No representa pentest, ni demuestra fuga de datos. No se copian claves ni contenidos privados en este documento.

| ID | Severidad | Evidencia identificada | Acción obligatoria | Estado |
|---|---|---|---|---|
| H01 | CRÍTICA | Contraseñas literales definidas en HTML cliente: `dashboards/ircas/ircas.html`, `dashboards/filtros/filtros.html`, `dashboards/muestras/muestras.html`, `dashboards/piscinas/piscinas.html`, `dashboards/dosificacion_cloro/dosificacion_cloro.html`, `dashboards/empresas_plaguicidas/empresas_plaguicidas.html`, `dashboards/sedes_educativas/sedes_educativas.html`. | Retirar controles visuales; rotar claves que se hayan reutilizado; sustituir por autenticación/autorización del servidor. No publicar hash ni contraseña de reemplazo en cliente. | ABIERTO |
| H02 | ALTA | `dashboards/estado_acueductos/estado_acueductos.html` incluye SHA-256 de contraseña y un indicador de autorización en `sessionStorage`; código cliente carga `data/estado_acueductos/current/acueductos_data.js`. | Privar datos y evidencias; API autorizada; validación de rol en servidor/RLS; sustituir hash estático. | ABIERTO |
| H03 | ALTA | Numerosos tableros acceden directamente a CSV/JSON/JS en `data/<módulo>/` y varios permiten exportar tablas; los datos se habían colocado en el despliegue estático. | Clasificar datos, bloquear descargas no autorizadas en **origen**, migrar a API/Storage protegido, evitar artefactos incrustados; pruebas anónimas por ruta. | ABIERTO |
| H04 | ALTA | `dashboards/fenomeno_nino/fenomeno_nino.html` usa `raw.githubusercontent.com/UESVALLE/uesvalle.github.io/main/data/fenomeno_nino/`, incompatible con uso anónimo tras privatizar el repositorio. | Sustituir por backend autorizado y revisar mapas; no restaurar accesibilidad pública del repositorio. | ABIERTO |
| H05 | ALTA | Información detallada de inspecciones, actividad institucional, sedes escolares, resultados analíticos, imágenes y videos en árbol de Git. | Clasificación en origen, minimización, revisión de archivo adjunto y almacenamiento privado. | ABIERTO |
| H06 | ALTA | Índices de resultados de agua con identificadores y URL de Google Drive, sujetos a permisos externos independientes. | Comprobar recursos en Drive individualmente; impedir referencias públicas si el recurso es interno; revisar permisos de compartición. | ABIERTO |
| H07 | MEDIA-ALTA | `data/portal/catalogo_tableros.json` marca `requiere_clave=true` para algunas páginas pero otras aparecen con `false`; es dato de UI, no control del servidor. | Política de acceso por rol/proceso fuera del frontend; tratar todos los módulos por clasificación real. | ABIERTO |
| H08 | MEDIA | GitHub `main` no contiene directorio `scripts/` versionado, y `.gitignore` excluye `scripts/`. | Llevar automatizaciones auditables a `tools/` o `etl/` versionados sin datos; mantener fuentes y credenciales fuera de Git. | DIAGNOSTICADO |
| H09 | POR VERIFICAR | GitHub Pages histórico, copia personal previa, rutas de CDNs y dominios heredados. GitHub devolvió 404 para copia personal en comprobaciones posteriores; **404 no acredita inexistencia ni cierre completo**. | Prueba HTTP en cliente anónimo con evidencia, revisión de cuenta correspondiente. | BLOQUEADO: verificación HTTP externa |
| H10 | POR VERIFICAR | Protección Vercel `ssoProtection.deploymentType=all` confirmada por API; falta prueba real en ventana anónima y ruta directa a dataset. | Ejecución de batería HTTP anónima, evitar URL de compartir/bypass. | CONFIGURADO, PRUEBA PENDIENTE |

## Riesgos de claves heredadas

**No imprimir, copiar, descifrar ni compartir** las contraseñas antiguas en este repositorio ni en incidencias. Si alguna se usa fuera del tablero, su propietario deberá **rotarla**. La sustitución por credenciales nuevas en HTML no remedia el problema.

## Orden de mitigación

1. Mantener GitHub privado y Vercel protegido; confirmar accesos anónimos reales al origen y activos.
2. Tratar H01–H02 como deuda crítica: eliminar acceso basado en clave JS **junto con** migración del dato, no antes si eso destruye funcionalidad.
3. Identificar qué archivos son públicos aprobados, cuáles requieren ámbito y cuáles deben permanecer sólo en servidor/Storage.
4. Migrar un tablero piloto con API, roles y pruebas de descarga antes de ejecutar cambios masivos.
5. Conservar historial Git para trazabilidad, sin asumir que eliminar una ruta borra versiones anteriores.

**Seguimiento:** [SEC-01](https://github.com/UESVALLE/uesvalle.github.io/issues/2), [SEC-02](https://github.com/UESVALLE/uesvalle.github.io/issues/3) y [SEC-03](https://github.com/UESVALLE/uesvalle.github.io/issues/4).
