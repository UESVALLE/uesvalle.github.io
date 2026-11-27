# Plan de pruebas y puerta de publicación

**Uso:** crear evidencia de seguridad y continuidad **sin incluir capturas de información restringida**. No marcar los casos como aprobados hasta su ejecución real.

## Matriz mínima

| ID | Escenario | Resultado esperado | Estado |
|---|---|---|---|
| T01 | Visitante anónimo abre portal Vercel | Autenticación requerida | PENDIENTE |
| T02 | Visitante anónimo abre un CSV/JSON directo de un despliegue | Acceso denegado si no es público autorizado | PENDIENTE |
| T03 | Visitante anónimo abre GitHub Pages histórico | No entrega datos operativos restringidos | PENDIENTE |
| T04 | Visitante anónimo consulta repositorio principal | Sin acceso a archivos privados | PENDIENTE |
| T05 | Copia personal, forks, etiquetas y URLs anteriores | No exponen datos no autorizados | PENDIENTE |
| T06 | Google Drive y PDF por URL directa | Acceso controlado por permisos del documento | PENDIENTE |
| T07 | Usuario sin sesión llama API privada | 401/403; sin datos | PENDIENTE |
| T08 | Usuario válido de otra ARO | No obtiene registros fuera de alcance | PENDIENTE |
| T09 | Rol sólo lectura intenta modificar/exportar fuera de permisos | Denegado con auditoría | PENDIENTE |
| T10 | Lectura directa Supabase sin permiso (RLS/GRANT) | Denegada | PENDIENTE |
| T11 | Storage privado: objeto por URL directa | Denegado sin autorización | PENDIENTE |
| T12 | URL firmada vencida/revocada | No permite descarga | PENDIENTE |
| T13 | Compilación JS y variables expuestas al navegador | Sin secretos ni service keys | PENDIENTE |
| T14 | Revisión de caché/CDN/URLs antiguas | No sirve artefactos restringidos | PENDIENTE |
| T15 | ETL en entorno controlado con datos sintéticos | Totales, claves y calidad consistentes | PENDIENTE |
| T16 | ETL repetido o interrumpido | Idempotencia o rollback controlado | PENDIENTE |
| T17 | Regresión visual y de filtros/exportación del piloto | Misma funcionalidad autorizada | PENDIENTE |
| T18 | Restauración de respaldo | Datos y permisos recuperados | PENDIENTE |
| T19 | Baja/revocación de usuario y sesiones | No puede continuar accediendo | PENDIENTE |
| T20 | Revisión de costos/alertas ante cuotas | Límites documentados y monitoreados | PENDIENTE |

## Registro de evidencia por caso

- ID, fecha/hora, entorno, dominio/ruta **sin token**, rol de prueba, resultado esperado, resultado observado (HTTP / estado), responsable, evidencia sanitizada, incidencia relacionada, veredicto.
- No almacenar contraseñas, cookies, accesos de prueba, PII, imágenes privadas ni parámetros de bypass en GitHub.
- Marcar resultado como **APROBADO / FALLIDO / BLOQUEADO / NO APLICA justificado**.

## Criterios para pasar a producción

- T01–T14 y T19 aprobados o con excepción **formal, justificada, sin riesgo crítico**.
- T15–T18 aprobados para el módulo intervenido.
- Clasificación del dataset aprobada; permisos validados; backups probados; plan de rollback escrito; costo y titularidad claros.
- El responsable de datos y el aprobador de producción confirman el alcance. Ninguna publicación automática debe saltar esta puerta.

Seguimiento de validación y operación: [SEC-09](https://github.com/UESVALLE/uesvalle.github.io/issues/10).
