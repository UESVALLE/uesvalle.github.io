# Registro de decisiones y estado del programa

**Corte:** 28 de octubre de 2026. Actualizar sólo cuando exista evidencia comprobable.

## Línea de base verificada

| Elemento | Evidencia técnica | Estado |
|---|---|---|
| Repositorio `UESVALLE/uesvalle.github.io` | Consulta de metadatos del repositorio: `visibility=private` | VERIFICADO |
| Inventario de `main` | Árbol Git: 704 archivos; 561 en `data/`; 19 módulos | VERIFICADO (fotografía) |
| Vercel `uesvalle-ai-api` | Configuración: `ssoProtection.deploymentType=all` | CONFIGURADO; prueba anónima pendiente |
| Dominio `uesvalle-tableros.vercel.app` | Asociado al proyecto Vercel anterior | VERIFICADO |
| GitHub Pages, crudos, copias personales, CDN | Requieren pruebas externas de acceso; un 404 no basta para determinar toda la exposición | PENDIENTE |
| Supabase institucional, RLS y Storage privado | No verificados/provisionados como infraestructura objetivo | NO IMPLEMENTADO EN ESTE PROGRAMA |
| Gobierno de datos, roles y clasificación legal | Sin decisión institucional registrada | POR APROBAR |
| Tableros migrados a nueva arquitectura | No se han cambiado scripts ni fuentes mediante esta documentación | PENDIENTE |

## Decisiones arquitectónicas (ADR)

**ADR-001 · Repositorio único para documentación de transición — adoptada para el plan.**  
Crear carpeta `docs/arquitectura_seguridad/` en el repositorio privado, no crear un repositorio anidado (GitHub no admite esa estructura lógica). La ejecución se coordina con Issues. Documentos en rama aislada con PR en borrador; `main` sin cambios hasta revisión.

**ADR-002 · Separación código / datos — propuesta.**  
GitHub privado sólo para código, scripts y documentación; datos operativos migran a base/almacenamiento con controles. La migración es progresiva, con copias respaldadas, validación funcional y aprobación.

**ADR-003 · Protección de acceso — propuesta.**  
Vercel mantiene protección mientras se implementa identidad y autorizaciones propias; la protección actual no es un directorio institucional de usuarios.

**ADR-004 · Piloto — propuesta.**  
Iniciar con Estado de Acueductos para retirar control por hash cliente y demostrar almacenamiento de evidencias y autorizaciones reales, previa validación de datos y permisos.

**ADR-005 · Publicación — política propuesta.**  
Ningún dato se publica por ser técnicamente accesible: sólo vistas/artefactos agregados con autorización del propietario institucional y pruebas de no filtración.

## Preguntas y aprobaciones externas necesarias

- Quién es responsable institucional del dato, quién autoriza divulgación y quién firma el paso a producción.
- Quién administra y paga GitHub, Vercel y la futura cuenta Supabase; si se exige dominio oficial institucional.
- Elección de identidad, roles/ARO, MFA, mecanismos de revocación y acceso externo temporal.
- Qué datasets y evidencias pueden ser públicos, internos o restringidos.
- Reglas de retención, requisitos normativos y flujo institucional de respuesta a incidentes.
- Objetivos de recuperación, costos de respaldo, almacenamiento, operaciones y egreso.

## Tablero de ejecución (fuente de verdad: Issues)

| ID | Tarea | Estado inicial |
|---|---|---|
| [SEC-01](https://github.com/UESVALLE/uesvalle.github.io/issues/2) | Contención y URLs | ABIERTO |
| [SEC-02](https://github.com/UESVALLE/uesvalle.github.io/issues/3) | Inventario y clasificación | ABIERTO; inventario técnico generado |
| [SEC-03](https://github.com/UESVALLE/uesvalle.github.io/issues/4) | Secretos y clave en navegador | ABIERTO |
| [SEC-04](https://github.com/UESVALLE/uesvalle.github.io/issues/5) | Gobierno y permisos | ABIERTO |
| [SEC-05](https://github.com/UESVALLE/uesvalle.github.io/issues/6) | Supabase/RLS/Storage | ABIERTO |
| [SEC-06](https://github.com/UESVALLE/uesvalle.github.io/issues/7) | Automatización ETL | ABIERTO |
| [SEC-07](https://github.com/UESVALLE/uesvalle.github.io/issues/8) | Piloto acueductos | ABIERTO |
| [SEC-08](https://github.com/UESVALLE/uesvalle.github.io/issues/9) | Migración resto módulos | ABIERTO |
| [SEC-09](https://github.com/UESVALLE/uesvalle.github.io/issues/10) | Recuperación/operación | ABIERTO |

## Bitácora de hitos

| Fecha | Cambio | Alcance y validación |
|---|---|---|
| 2026-10-28 | Inventario técnico (704 rutas) | Lectura de árbol Git; **clasificación de contenido pendiente** |
| 2026-10-28 | Repositorio principal privado | Metadatos de GitHub confirmados |
| 2026-10-28 | Vercel Authentication `all` | Configuración consultada; falta prueba anónima de aplicación/archivos |
| 2026-10-28 | Issues SEC-01..09 | Planeación publicada en repo privado |
| 2026-10-28 | Carpeta documental de arquitectura | Rama de documentación; no cambios en despliegue principal |

## Validación automatizada adicional — 28/10/2026

- [GitHub Actions #40718025470](https://github.com/UESVALLE/uesvalle.github.io/actions/runs/40718025470): **SUCCESS** para los tres jobs: `guard` (seis pruebas unitarias + revisión de nuevos archivos), `anonymous-http-audit` (7 URLs sin credenciales) y `postgres-security-smoke` (migración SQL de esquema privado probada sobre PostgreSQL 16 efímero con roles simulados).
- Resultado PostgreSQL confirma en entorno sintético: permisos privados, RLS activo, cuentas iniciales inactivas y restricción para declarar un dataset público sin aprobación.
- **Precisión:** la prueba PostgreSQL no equivale a migración en Supabase, no utiliza un proyecto real y no prueba aún políticas específicas por municipio/ARO. Las operaciones de Supabase no fueron invocables en la sesión pese a figurar la integración como instalada.
- `main` permanece intacto; el PR #11 sigue como borrador para no provocar producción de archivos de configuración antes de cerrar política de publicación.

## Hallazgo de gobernanza — 28/10/2026

- Proyecto Vercel `uesvalle-ai-api` asociado a `uesvalle-tableros.vercel.app` bajo equipo personal `Javier Marin's projects` con plan **Hobby** (consulta de conexión Vercel).
- Condiciones oficiales del plan: [Hobby](https://vercel.com/docs/plans/hobby) y [fair use](https://vercel.com/docs/limits/fair-use-guidelines). **Se requiere valorar el uso institucional/contractual concreto**; no se concluye incumplimiento automático.
- [SEC-10](https://github.com/UESVALLE/uesvalle.github.io/issues/12) abierto. No se autoriza transferencia, contratación ni creación de cuentas con costos.

## Hito real — Supabase (28/10/2026)

- Se aplicó la migración `20261028154625_uesvalle_private_security_foundation` al proyecto Supabase `UESVALLE`, ref `hzenpizteypjydwgfhce`, región `us-west-2`.
- Se creó `ues_private` con `user_memberships`, `dataset_registry` y `audit_events`; RLS habilitado en las tres tablas, roles `anon` y `authenticated` sin SELECT.
- Los avisos `rls_enabled_no_policy` (INFO) son esperados bajo denegación predeterminada. [Consulta de referencia](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy).
- No hay cuentas institucionales nuevas, datasets cargados ni políticas que autoricen consultas.
- Sigue pendiente validar titularidad institucional, política de roles, almacenamiento privado, permisos y plan de respaldos antes de producción.
