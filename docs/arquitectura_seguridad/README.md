# Arquitectura segura UESVALLE · Centro de control

**Estado:** propuesta de arquitectura y hoja de ruta en ejecución documental (28/10/2026). **Versión:** 1.0. **Repositorio:** privado. **Rama:** `docs/arquitectura-seguridad-2026`. **Producción:** sin cambios con estos documentos.

## Objetivo

Unificar el gobierno de datos, desarrollo, publicación y operación de los tableros institucionales sin exponer archivos operativos: GitHub privado (código/versiones), Python (ETL), Supabase PostgreSQL/PostGIS + Storage privado (datos/evidencias), Vercel (portal y API protegida), autenticación institucional y autorizaciones por roles. **La seguridad se verifica con pruebas, no con una contraseña visual ni por ocultar enlaces.**

## Orden de lectura y trabajo

1. [HOJA_DE_RUTA.md](HOJA_DE_RUTA.md): fases, dependencias, criterios de salida y tareas GitHub.
2. [ARQUITECTURA_OBJETIVO.md](ARQUITECTURA_OBJETIVO.md): componentes, flujos y decisiones técnicas.
3. [INVENTARIO_Y_CLASIFICACION.md](INVENTARIO_Y_CLASIFICACION.md): alcance por módulo y plantilla de inventario.
4. [MATRIZ_SEGURIDAD_Y_ACCESOS.md](MATRIZ_SEGURIDAD_Y_ACCESOS.md): roles, permisos, requisitos mínimos.
5. [PLAN_DE_PRUEBAS.md](PLAN_DE_PRUEBAS.md): pruebas de seguridad, recuperación y operación.
6. [REGISTRO_DECISIONES_Y_ESTADO.md](REGISTRO_DECISIONES_Y_ESTADO.md): estado comprobado, incertidumbres, decisiones pendientes.

## Implementación y evidencia adicional

- [MATRIZ_DEPENDENCIAS_FRONTEND_2026-10-28.csv](MATRIZ_DEPENDENCIAS_FRONTEND_2026-10-28.csv): dependencias, claves cliente y riesgo técnico de 19 tableros.
- [HALLAZGOS_PRIORIZADOS_2026-10-28.md](HALLAZGOS_PRIORIZADOS_2026-10-28.md): riesgos H01–H10 sin divulgar claves ni registros privados.
- [VERIFICACION_ACCESO_ANONIMO_2026-10-28.md](VERIFICACION_ACCESO_ANONIMO_2026-10-28.md): HTTP anónimo, evidencia de Actions.
- [PROCEDIMIENTO_OPERATIVO_MIGRACION.md](PROCEDIMIENTO_OPERATIVO_MIGRACION.md): procedimiento de migración módulo por módulo.
- [BLOQUEOS_Y_DECISIONES_OPERATIVAS.md](BLOQUEOS_Y_DECISIONES_OPERATIVAS.md): pendientes institucionales y técnicos.
- [../../tools/security/README.md](../../tools/security/README.md): control preventivo de GitHub y auditoría HTTP.
- [../../infra/supabase/README.md](../../infra/supabase/README.md): DDL de arranque privado, **sin ejecutar**.

**Estado de validación:** workflow de PR y auditoría HTTP anónima han completado ejecuciones exitosas, pero ninguna base o módulo ha sido migrado a Supabase. La conexión instalada todavía no ofrece operaciones disponibles en esta ejecución.

**Tablero de tareas:** [GitHub Issues](https://github.com/UESVALLE/uesvalle.github.io/issues). Cada SEC-xx tiene checklist y criterio de aceptación. La documentación y las incidencias deben mantenerse sincronizadas; una tarea no se marca completa por haber creado el documento.

## Reglas de ejecución

- No alterar `main`, los archivos `data/`, `dashboards/`, `archive/`, ni las URL de producción durante la fase documental.
- No reactivar GitHub Pages ni desactivar protección Vercel por conveniencia.
- No publicar copias de datos, fotografías, contraseñas, hashes de claves, tokens, archivos .env ni bitácoras sensibles en repositorios, tickets o capturas.
- Aprobar con el responsable institucional la clasificación del dato y los usuarios autorizados antes de publicar o migrar.
- Cada modificación posterior requiere plan de cambio, rama, respaldo, pruebas con datos sintéticos, revisión por pull request, despliegue protegido y reversión.
- Este repositorio contiene actualmente bases en `data/`; su permanencia en privado es **contención**, no sustituto de migrarlas a almacenamiento con control de acceso.

## Primer hito real

Completar [SEC-01](https://github.com/UESVALLE/uesvalle.github.io/issues/2), [SEC-02](https://github.com/UESVALLE/uesvalle.github.io/issues/3) y [SEC-03](https://github.com/UESVALLE/uesvalle.github.io/issues/4): comprobar sitios y URL directas, clasificar archivos, revisar credenciales y evidencias. Luego iniciar [SEC-04](https://github.com/UESVALLE/uesvalle.github.io/issues/5) y diseño de [SEC-05](https://github.com/UESVALLE/uesvalle.github.io/issues/6).

## Fuentes técnicas

- [Vercel: protección de producción en todos los planes (09/09/2026)](https://vercel.com/changelog/protect-production-deployments-for-free-on-every-plan).
- [GitHub Pages: visibilidad distinta de visibilidad del repositorio](https://docs.github.com/es/enterprise-cloud%40latest/pages/getting-started-with-github-pages/creating-a-github-pages-site).
- [Supabase: RLS, privilegios y políticas](https://supabase.com/docs/guides/database/postgres/row-level-security).
- [Supabase: proteger secretos y datos](https://supabase.com/docs/guides/database/secure-data).

## Puerta de gobierno de servicios

[SEC-10 — Titularidad institucional, licenciamiento y continuidad](https://github.com/UESVALLE/uesvalle.github.io/issues/12) es un requisito antes de migrar **datos reales** o habilitar operación institucional continua. Vercel opera actualmente bajo un equipo personal Hobby; confirmar con la entidad y términos del proveedor.
