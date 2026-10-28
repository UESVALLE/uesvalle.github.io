# Hoja de ruta · Migración segura UESVALLE

**Fecha base:** 28/10/2026. **Estado inicial:** repositorio principal privado; autenticación Vercel configurada para todos los despliegues; protección de rutas, archivos externos y copias históricas **no verificada integralmente**. **Alcance de este documento:** coordinación de ejecución y aceptación, no autorización para manipular bases ni publicar.

## Secuencia obligatoria y puertas de control

| Fase | Prioridad | Trabajo y tarea | Depende de | Evidencia de salida |
|---|---|---|---|---|
| F0 Contención | Crítica | [SEC-01](https://github.com/UESVALLE/uesvalle.github.io/issues/2) Superficies y copias públicas | Ninguna | Pruebas anónimas de cada URL, accesos restringidos o exposición aceptada formalmente |
| F0–F1 Inventario | Crítica | [SEC-02](https://github.com/UESVALLE/uesvalle.github.io/issues/3) Clasificación por archivo y flujo | F0 en paralelo | Inventario 100% con propietario/clasificación |
| F0–F1 Endurecimiento | Alta | [SEC-03](https://github.com/UESVALLE/uesvalle.github.io/issues/4) Claves cliente, histórico, evidencia y credenciales | F0 en paralelo | Riesgos críticos mitigados/registrados |
| F1 Gobierno | Alta | [SEC-04](https://github.com/UESVALLE/uesvalle.github.io/issues/5) Roles, procesos, ARO, operaciones | F0–F1 | Matriz de acceso institucional aprobada |
| F2 Backend | Alta | [SEC-05](https://github.com/UESVALLE/uesvalle.github.io/issues/6) Supabase DB + Storage + políticas | SEC-02/04 | RLS/GRANT probados con datos sintéticos |
| F2 Automatización | Alta | [SEC-06](https://github.com/UESVALLE/uesvalle.github.io/issues/7) Python ETL seguro | SEC-02/05 | Conciliación y carga idempotente sin exposición |
| F3 Piloto | Alta | [SEC-07](https://github.com/UESVALLE/uesvalle.github.io/issues/8) Estado de acueductos | SEC-04/05/06 | Funcionalidad y acceso controlado demostrados |
| F4 Escalamiento | Media-alta | [SEC-08](https://github.com/UESVALLE/uesvalle.github.io/issues/9) Restantes tableros y evidencias | Piloto aprobado | Cada módulo migrado con acta de aceptación y rollback |
| F5 Operación | Alta | [SEC-09](https://github.com/UESVALLE/uesvalle.github.io/issues/10) Backups, auditoría, costos, pruebas y reapertura | Todas | Restauración exitosa, accesos probados, operación aprobada |

**Regla de prioridad:** ninguna mejora estética o función nueva puede reabrir datos mientras persistan hallazgos críticos de exposición.

## Sprint/iteraciones sugeridas (orientativas, no compromisos de fecha)

**Iteración A: contención y mapa de activos.** Ejecutar SEC-01, levantar SEC-02 y SEC-03, congelar nuevos despliegues de archivos restringidos. Confirmar dependencia de GitHub Pages, Vercel y copia personal. Producto: inventario y matriz de riesgos.

**Iteración B: identidad y diseño de datos.** Acordar roles y operaciones con el responsable institucional. Crear ambiente aislado de pruebas, esquema de BD y Storage, grants y RLS. Producto: autorización validada con datos sintéticos.

**Iteración C: ETL y tablero piloto.** Automatización Python, reconciliación, carga; migrar Estado de Acueductos sin hash cliente. Producto: flujo reproducible y prueba anónima denegada.

**Iteración D: olas de migración.** Primero módulos con evidencias, datos de establecimientos/personas o seguimiento operativo; después analítica agregada y geográfica. Producto: módulos aceptados y documentos enlazados seguros.

**Iteración E: operación y transferencia.** Recuperación, respaldos, observabilidad, costos, responsables, capacitación y control de cambios. Producto: acta de entrada a producción.

## Orden recomendado dentro de la migración por módulo

1. Inspección sedes, Vigilancia sanitaria (fotos/videos; datos de establecimientos).
2. EDAN y Alojamientos temporales (poblaciones afectadas y gestión operativa).
3. Seguimiento ACH y MPR (información de funcionarios/ejecución).
4. Estado de Acueductos (piloto técnico; puede ejecutarse en paralelo tras controles mínimos).
5. IRCAS, Muestras IRCA y Resultados Agua (históricos y puntos; validar autorización de publicación).
6. Zoonosis, Sedes educativas, Filtros, Piscinas, Plaguicidas, Cementerios, El Niño y demás módulos.
   
**El orden definitivo se ajusta tras la clasificación; no supone que todo el dato de un módulo sea reservado.**

## Plantilla única de ejecución por cambio

- ID SEC-xx / módulo / responsable técnico / aprobador de datos.
- Estado: **pendiente → análisis → propuesta → aprobado → implementado → validado → cerrado**; 'bloqueado' si falta permiso.
- Riesgo inicial / fuentes / datos afectados / alcance del cambio.
- Evidencia antes (sin copiar datos), backup verificado y plan de reversión.
- Archivos y políticas editadas; PR; resultado de pruebas funcionales y negativas de acceso.
- Conformidad del responsable antes de merge/despliegue.
- Actualización de la matriz de activos, decisión y manual.

## Puertas de aceptación transversales

**G0 Contención:** no hay URL no autorizada con retorno 200 a contenido restringido.  
**G1 Datos:** origen, propietario, minimización, clasificación, retención y consumidores registrados.  
**G2 Autorización:** sin sesión/rol no se obtiene dato, API, imagen ni archivo.  
**G3 Integridad:** totales y métricas clave cuadran antes/después de migrar.  
**G4 Continuidad:** backup/restore, reversión y alertas ensayadas.  
**G5 Publicación:** aprobación institucional de contenido y usuarios; checklist firmado.

## Seguimiento

La fuente de verdad de estado operativo son los [issues del repositorio](https://github.com/UESVALLE/uesvalle.github.io/issues); este archivo contiene fases y dependencias. Mantener [REGISTRO_DECISIONES_Y_ESTADO.md](REGISTRO_DECISIONES_Y_ESTADO.md) sólo con hitos verificados, no con proyecciones.
