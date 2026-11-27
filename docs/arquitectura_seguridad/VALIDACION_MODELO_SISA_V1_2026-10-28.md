# Verificación del prototipo canónico SISA / MPR (V1)

**Fecha:** 28 de octubre de 2026. **Ambiente:** contenedor efímero PostgreSQL 16 en GitHub Actions, sin datos reales. **No se aplicó DDL a Supabase UESVALLE**.

## Evidencia ejecutada

- [GitHub Actions #40781003546](https://github.com/UESVALLE/uesvalle.github.io/actions/runs/40781003546), job `postgres-security-smoke`: **SUCCESS**.
- `infra/supabase/tests/001_base_privada_smoke.sql`: verifica rol privado, RLS y privilegios mínimos de la base inicial.
- `infra/supabase/tests/002_modelo_sisa_smoke.sql`: incorpora `infra/supabase/proposals/002_modelo_sisa_borrador.sql` y ejecuta transacciones sintéticas.

### Resultados comprobados

| Condición | Resultado |
|---|---|
| 13 tablas nuevas del modelo distribuidas en cuatro esquemas | PASS |
| Todas con RLS y sin SELECT para `anon` / `authenticated` | PASS |
| Esquema `ues_core` no usable desde rol anónimo | PASS |
| Alias de sistema provisional y validado diferenciados | PASS |
| Rechazo de alias validado duplicado | PASS |
| Rechazo de carga duplicada por fuente, hash y versión ETL | PASS |
| Dos actividades del mismo sistema en igual fecha se conservan | PASS |
| Cruce `CANDIDATO_TEXTO` no puede confirmarse automáticamente | PASS |
| Cruce confirmado exige método permitido y validación | PASS |
| Prueba sintética de vinculación de muestra a sistema | PASS |

La ejecución incluye trazas `NOTICE: PASS: 13 tablas privadas, RLS/GRANT, deduplicación de lotes, alias validados, 2 eventos y cruces controlados`.

## Limitaciones del test

- No prueba funciones de SISA, autenticación de usuario real, expedientes, calidad de datos, RASEM, SIVICAP, PostGIS o rendimiento.
- No es una restauración de la base histórica.
- No se han definido todavía permisos **efectivos por ARO** para los usuarios institucionales.
- No han sido auditadas relaciones ni claves reales de las 33 tablas heredadas: sólo contamos con resumen técnico del respaldo.
- No se han migrado fotografías, PDFs, usuarios, sesiones, datos de muestras ni información de carácter personal.

## Puertas para una implementación real

1. Recuperar DDL y claves del respaldo antiguo en entorno privado y validar relaciones/normalización.
2. Validar con responsables institucionales sistema maestro, prestadores, códigos SISA, municipio y ARO.
3. Acordar clasificación y autorización de uso de información que procede de otra organización/cuenta.
4. Aprobar titularidad/licenciamiento Vercel y Supabase y políticas de acceso (SEC-10).
5. Elaborar y ejecutar migración final versionada, auditar con Supabase Advisor y ensayar autorización por perfiles.
6. Ejecutar piloto MPR contra extracto SISA autorizado con conciliación de indicadores; conservar operación anterior intacta hasta aceptar.

**Control de cambios:** [SEC-11](https://github.com/UESVALLE/uesvalle.github.io/issues/13); [PR #11](https://github.com/UESVALLE/uesvalle.github.io/pull/11).
