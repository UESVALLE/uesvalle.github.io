# Política y matriz de acceso — propuesta inicial

**Importante:** borrador para aprobación institucional; sin políticas RLS configuradas ni cuentas nuevas creadas.

## Identidades y autorizaciones

| Perfil propuesto | Consultar datos generales | Consultar detalle interno | Cargar/corregir datos | Aprobar publicación | Administrar plataforma |
|---|---|---|---|---|---|
| Público anónimo | Sólo agregados autorizados | No | No | No | No |
| Consulta institucional | Sí, según permisos | Limitado a módulos autorizados | No | No | No |
| Profesional ARO | Sí | Registros de su ámbito de trabajo | Según proceso y atribución | No | No |
| Coordinador | Sí | Proceso/territorio a cargo | Revisar/validar según atribución | Según delegación formal | No |
| Responsable del dato | Sí | Su proceso | Según atribución | Sí, con autorización institucional | No |
| Administrador técnico | Infraestructura necesaria | **No por defecto** a datos personales | Migraciones técnicas controladas | No | Sí, bajo registro de cambios |

**Regla:** el rol define operación y **ámbito** (proceso, ARO, municipio, sistema o caso). Ser administrador del software no equivale a tener derecho a consultar todos los datos.

## Controles no negociables

1. **Autenticación fuerte:** usuario individual, ciclo de alta/baja, MFA cuando aplique, caducidad de sesiones, bloqueo y revocación.
2. **Autorización en servidor y BD:** validación de sesión en API, GRANT mínimo, RLS habilitado para cada tabla expuesta, denegación por defecto; no confiar en la UI.
3. **Almacenamiento:** buckets privados, descarga mediada por autorización o URL firmada de corta duración; fotos y documentos sensibles no deben residir en `public/`.
4. **Secretos:** sólo variables de entorno protegidas o gestor de secretos; evitar credenciales en frontend, Git, issues, logs y artefactos; rotar si hay indicios de exposición.
5. **Datos y privacidad:** minimización, finalidad, clasificación, retención, anonimización/agregación aprobada para difusión.
6. **Transporte y despliegue:** HTTPS, pruebas de CORS y cabeceras de seguridad, revisión de caché/CDN, builds de producción sólo con revisión.
7. **Trazabilidad:** auditoría de acciones sensibles (consulta/descarga de evidencia cuando corresponda, cambios, administración), alertas y mínimo acceso a logs.
8. **Continuidad:** respaldo en ubicación separada, restauración ensayada, control de versiones y rollback documentado.
9. **Protección existente:** Vercel Authentication para todos los despliegues es capa de contención; la aplicación debe tener control de acceso institucional propio.
10. **Presupuesto/capacidad:** aprobar límites de almacenamiento, base, egreso y operaciones antes de depender del nivel gratuito.

## Reglas concretas de Supabase

- Aplicar **RLS y permisos GRANT** a tablas/vistas: RLS por sí sola no sustituye la revisión de privilegios.
- Nunca colocar `service_role` o secret keys en JavaScript de navegador. Si el frontend consulta Supabase, sólo key publicable con RLS y permisos verificables.
- Las cuentas técnicas de ETL deben ejecutarse exclusivamente en servidor/runner privado.
- Migraciones de esquema versionadas; tests positivos/negativos para cada política; evitar exponer esquemas internos sin API controlada.
- Storage sin buckets públicos para evidencias internas. Evitar que rutas predecibles permitan descargar objetos.

## Responsabilidades de aprobación

| Decisión | Responsable técnico prepara | Validador requerido |
|---|---|---|
| Datos clasificados como públicos | Equipo de datos | Propietario institucional / jurídico si aplica |
| Roles y ámbitos | Equipo de desarrollo | Responsable de proceso y TI |
| Despliegue de producción | Equipo técnico | Administrador designado y dueño funcional |
| Restauración/retención | Administrador de datos | Responsable institucional |
| Incidente y notificación | Responsable seguridad/TI | Autoridades competentes según política institucional |

## Diseño de pruebas de autorización

Probar siempre: sin sesión, sesión caducada, usuario de otra ARO, rol de consulta intentando editar, enlace directo a archivo, URL firmada vencida, endpoint de exportación, código no autenticado, usuario eliminado, y acceso desde otro navegador. No registrar el dato sensible devuelto; registrar sólo resultado/error/fecha.

Referencia: [SEC-04](https://github.com/UESVALLE/uesvalle.github.io/issues/5), [SEC-05](https://github.com/UESVALLE/uesvalle.github.io/issues/6). Documentación: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security) y [Securing your data](https://supabase.com/docs/guides/database/secure-data).
