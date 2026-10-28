# Plantilla de control de migraciones Supabase

**Estado:** script SQL de arranque redactado, **sin ejecutar** ni crear proyecto. No contiene datos reales.

`schema/001_base_privada.sql` crea:
- Un esquema `ues_private` no expuesto al público.
- Registro de roles/accesos con activación inicial deshabilitada.
- Registro de datasets y clasificación.
- Bitácora de auditoría sin información personal cruda.
- RLS activado y sin políticas permisivas para `anon` ni `authenticated`.
- Privilegios del esquema reservados al rol de servicio **sólo servidor**.

**No es autorización de acceso completa.** No hay todavía tablas operativas, API, buckets, ni políticas de acceso por módulo/ARO. Sólo se aplicará en un ambiente de pruebas institucional una vez conectado Supabase y validada la titularidad, el presupuesto y la política de cuentas.

Antes de ejecutar:
1. Revisar migración con el administrador de BD y responsable de protección de datos.
2. Probar identidad, denegación por defecto, RLS, privilegios `GRANT`, auditoría.
3. Confirmar que ningún secreto de rol servidor salga a Vercel client bundle o GitHub.
4. Probar copia de seguridad y procedimiento de recuperación antes de cargar datos.
5. Crear Storage privado y establecer políticas concretas por objeto con pruebas de URL directa.

**Exposición futura:** si se desea consulta pública de indicadores, generar vistas agregadas _aprobadas_ con esquema separado y política de mínimo acceso. No abrir lectura de `ues_private` ni Storage evidencias.
