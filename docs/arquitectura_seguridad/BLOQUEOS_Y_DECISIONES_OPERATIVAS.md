# Bloqueos operativos y decisiones externas

**Registrado:** 28/10/2026.

| Tema | Puede ejecutarse sin acceso adicional | Requiere acción externa |
|---|---|---|
| Repositorio privado | Auditoría estática, documentación, ramas, PR, código seguro, pruebas sintéticas | Aprobación de fusión y reglas de rama institucional |
| Vercel | Consultar configuración y solicitar endurecimiento; seguridad de código | Prueba desde navegador anónimo, titularidad de dominio/cuentas y aprobación de despliegue |
| Supabase | Diseñar SQL/ETL, políticas y casos de prueba offline | Conectar servicio Supabase a ChatGPT o habilitar proyecto institucional y permisos para configurar |
| GitHub Pages histórico | Revisar fuentes y catalogar URLs | Verificación HTTP desde red externa; despublicación en Settings si continúa activo |
| Copia personal histórica | Catalogar hallazgos y revisar referencias | Acceso a cuenta titular para verificar si fue privatizada/eliminada o redirigida |
| Datos institucionales | Inventariar rutas y campos sin copiar registros | Propietario del dato debe aprobar clasificación, retención y divulgación |
| Control de claves | Detectar y señalizar claves heredadas sin imprimir valores | Rotación de cualquier secreto reutilizado, realizada en el sistema de origen |

## Conexión requerida para Supabase

La integración Supabase existe como opción, pero **no está conectada** a esta conversación. No se han creado proyectos, usuarios, tablas ni almacenamiento real. La arquitectura propuesta no significa implementación. El responsable puede autorizar y conectar el servicio mediante la interfaz de ChatGPT; nunca pegar credenciales en el chat ni en Issues.

## Acciones en espera

- Probar HTTP anónimo de portal Vercel, página GitHub y archivos CSV/JSON (registrar códigos, no datos).
- Aprobar la matriz usuario × rol × proceso × ARO.
- Evaluar respaldo y titularidad de cuenta, costos y residencia de datos antes de aprovisionar producción.
- Revisar los permisos del origen Google Drive para los documentos referenciados.

## Continuidad

Continuar con pruebas sintéticas, herramientas de seguridad y documentación en rama; no fusionar un nuevo flujo de datos sin las aprobaciones correspondientes.
