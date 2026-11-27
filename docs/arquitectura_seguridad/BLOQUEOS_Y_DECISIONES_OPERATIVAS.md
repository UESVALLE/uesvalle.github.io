# Bloqueos operativos y decisiones externas

**Registrado:** 28/10/2026.

| Tema | Puede ejecutarse sin acceso adicional | Requiere acción externa |
|---|---|---|
| Repositorio privado | Auditoría estática, documentación, ramas, PR, código seguro, pruebas sintéticas | Aprobación de fusión y reglas de rama institucional |
| Vercel | Consultar configuración y solicitar endurecimiento; seguridad de código | Prueba desde navegador anónimo, titularidad de dominio/cuentas y aprobación de despliegue |
| Supabase | Diseñar SQL/ETL, políticas y casos de prueba offline | Comprobar que la conexión Supabase exponga operaciones de consulta/SQL en esta sesión; habilitar proyecto institucional y permisos adecuados |
| GitHub Pages histórico | Revisar fuentes y catalogar URLs | Verificación HTTP desde red externa; despublicación en Settings si continúa activo |
| Copia personal histórica | Catalogar hallazgos y revisar referencias | Acceso a cuenta titular para verificar si fue privatizada/eliminada o redirigida |
| Datos institucionales | Inventariar rutas y campos sin copiar registros | Propietario del dato debe aprobar clasificación, retención y divulgación |
| Control de claves | Detectar y señalizar claves heredadas sin imprimir valores | Rotación de cualquier secreto reutilizado, realizada en el sistema de origen |

## Conexión requerida para Supabase

La integración Supabase figura como **instalada** después de la autorización del usuario, pero en esta ejecución las operaciones de Supabase todavía no aparecen entre las herramientas invocables. **No se han consultado ni modificado proyectos, usuarios, tablas ni almacenamiento real.** Debe habilitarse la sesión de herramientas de Supabase y comprobar la titularidad del proyecto institucional antes de aplicar SQL. No pegar credenciales en el chat ni en Issues.

## Acciones en espera

- Probar HTTP anónimo de portal Vercel, página GitHub y archivos CSV/JSON (registrar códigos, no datos).
- Aprobar la matriz usuario × rol × proceso × ARO.
- Evaluar respaldo y titularidad de cuenta, costos y residencia de datos antes de aprovisionar producción.
- Revisar los permisos del origen Google Drive para los documentos referenciados.

## Continuidad

Continuar con pruebas sintéticas, herramientas de seguridad y documentación en rama; no fusionar un nuevo flujo de datos sin las aprobaciones correspondientes.

## Avances verificados en GitHub Actions

- 6/6 pruebas unitarias de guard preventivo y comprobación de PR: **éxito** ([ejecución 40716977661](https://github.com/UESVALLE/uesvalle.github.io/actions/runs/40716977661)).
- Comprobación de rutas HTTP anónimas: **ejecutada** (ver `VERIFICACION_ACCESO_ANONIMO_2026-10-28.md`).
- Matriz de dependencias por 19 módulos: `MATRIZ_DEPENDENCIAS_FRONTEND_2026-10-28.csv`.
