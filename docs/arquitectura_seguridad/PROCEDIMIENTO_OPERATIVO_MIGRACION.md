# Procedimiento operativo para migración segura por módulos

## Preparación (por módulo)

- Dueño del dato, aprobador, propósito y base de acceso registrados.
- Fuente original y corte temporal definidos; inventario de archivos y tableros consumidores.
- Clasificación **aprobada** en matriz; asignación de roles y ámbito territorial.
- Análisis de datos personales, fotografías, URLs externas, originales en Drive y exportaciones.
- Copia verificada y restaurable fuera del despliegue; plan de reversión documentado.

## Contrato de datos

1. Congelar nombres de campos vigentes y KPIs de referencia de la versión actual.
2. Definir tipos SQL, claves y relaciones; municipio DIVIPOLA y ARO sin heurísticas de nombre ambiguas.
3. Diseñar migración idempotente que preserve fuente y fecha de corte.
4. Comparar conteos, nulos, claves duplicadas, IRCA, niveles, agregaciones y coordenadas.
5. Conservar versiones de transformaciones y bitácoras de ejecución sin valores privados.

## API de lectura y descarga

- Verificar identidad en servidor (JWT de proveedor aprobado).
- Verificar autorización por proceso, operación y ámbito, **antes** de realizar consulta/descarga.
- RLS y permisos de BD como última capa de defensa; no confiar en filtros del frontend.
- Entregar sólo campos estrictamente necesarios y paginar los conjuntos grandes.
- PDF/evidencias por Storage privado con URL firmada temporal y verificación de autorización por objeto.
- Exportación registrada y limitada por rol, módulo y ámbito.

## Cambios de interfaz

- Mantener filtros y comportamiento funcional al sustituir lectura de archivos `data/` por API.
- No introducir `PASSWORD_TABLERO`, `PASSWORD_HASH` ni flags de autorización en LocalStorage.
- Mensajes 401/403 claros; sin datos visibles en el navegador antes del permiso.
- Documentar y probar caché, CORS, cabeceras, expiración de sesión y manejo de errores.

## Despliegue y rollback

- Rama y PR específicos; datos sintéticos y pruebas automatizadas.
- Revisar diff, firmas de cambios y listas de archivos publicados.
- Deploy en entorno protegido; ejecutar T01–T20 de `PLAN_DE_PRUEBAS.md`.
- Aprobar por responsable institucional; publicar sólo cuando pruebas y backup/restauración estén aprobadas.
- En incidente, bloquear acceso de inmediato; revertir frontend y API según plan sin restaurar datasets públicos.

## Dependencias institucionales

No puede concluirse producción sin titularidad/autorización de Supabase, permisos de la entidad, política de backup/retención y reglas de acceso aprobadas. El diseño y pruebas locales sí pueden continuar sin credenciales ni datos reales.
