# Tablero MPR – Seguimiento Mapas de Riesgo

## 1. Objetivo

Este módulo permite realizar el seguimiento operativo a las actividades de Mapas de Riesgo MPR asociadas al proceso de Agua para Consumo Humano de la UESVALLE.

El tablero consolida la información de sistemas programados y actividades ejecutadas registradas en SISA, específicamente para las actividades:

| Código | Actividad |
|---|---|
| 1.3 | Visita MPR / Ficha y Anexo Técnico 1 |
| 1.4 | Toma de muestra para MPR |
| 1.5 | Elaboración de Anexo Técnico 2 / Resolución |

El flujo actual elimina la necesidad de separar manualmente archivos de visitas, muestreos o resoluciones. La fuente principal es el censo general descargado desde SISA.

---

## 2. Flujo general de actualización

```text
SISA
↓
Descarga automática del censo de visitas realizadas
↓
data/mpr/raw/censo_visitasMPR.xlsx
↓
scripts/mpr/normalizar_mpr.py
↓
data/mpr/current/
↓
dashboards/mpr/seguimiento_mpr.html
↓
GitHub Pages
```

---

## 3. Archivo principal de ejecución

Para actualizar el tablero se debe ejecutar:

```text
scripts/mpr/actualizar_mpr_desde_sisa.bat
```

Este archivo realiza el proceso completo:

1. Abre SISA con Selenium.
2. Inicia sesión usando las credenciales locales.
3. Selecciona el ARO de sesión.
4. Ingresa a `Agua para Consumo Humano > Censos de visitas`.
5. Configura el reporte de visitas realizadas.
6. Descarga el censo del periodo.
7. Guarda el archivo como `data/mpr/raw/censo_visitasMPR.xlsx`.
8. Crea respaldo del censo anterior.
9. Ejecuta `scripts/mpr/normalizar_mpr.py`.
10. Actualiza los archivos en `data/mpr/current/`.
11. Permite confirmar el commit y push hacia GitHub.

---

## 4. Archivos de entrada

### 4.1. Censo descargado desde SISA

```text
data/mpr/raw/censo_visitasMPR.xlsx
```

Es el archivo crudo descargado desde SISA. No es leído directamente por el tablero.

Este archivo es usado únicamente como insumo del script de normalización.

### 4.2. Sistemas programados

```text
data/mpr/raw/Programados.csv
```

Define el universo de sistemas programados para seguimiento MPR.

Actualmente este archivo es el denominador del tablero.

### 4.3. Catálogo de códigos POA

```text
data/mpr/raw/Codigos_poa.csv
```

Contiene la referencia de actividades POA utilizadas para clasificar las actividades 1.3, 1.4 y 1.5.

---

## 5. Archivos generados para el tablero

El tablero HTML consume únicamente los archivos generados en:

```text
data/mpr/current/
```

Archivos principales:

```text
seguimiento_mpr_sistemas.csv
actividades_mpr_ejecutadas.csv
resumen_mpr_aro.csv
resumen_mpr_municipio.csv
resumen_mpr_funcionario.csv
alertas_mpr.csv
catalogo_codigos_poa_mpr.csv
metadata_mpr.json
```

Estos archivos alimentan los KPIs, gráficas, filtros y tablas del tablero.

---

## 6. Lógica de cruce

El cruce principal se realiza entre:

```text
Programados.CODIGO_ANTIGUO
↔
censo_visitasMPR.CODIGO ANTERIOR
```

El script también conserva una lógica de apoyo por texto mediante municipio, localidad, nombre del sistema y persona prestadora, para mejorar el cruce cuando existan diferencias en los códigos.

---

## 7. Indicadores del tablero

El tablero permite consultar:

- Sistemas programados.
- Visitas 1.3 ejecutadas.
- Pendientes de visita 1.3.
- Muestreos 1.4 ejecutados.
- Pendientes de muestreo 1.4.
- Resoluciones 1.5 ejecutadas.
- Pendientes de resolución 1.5.
- Actividades por ARO.
- Actividades por municipio.
- Actividades por funcionario.
- Alertas operativas.

---

## 8. Seguridad y archivos excluidos de GitHub

Por seguridad, los siguientes archivos no deben subirse al repositorio:

```text
scripts/mpr/config_sisa.env
data/mpr/raw/censo_visitasMPR.xlsx
data/mpr/raw/censo_visitasMPR_backup_*.xlsx
data/mpr/historical/
archive/
```

El archivo `config_sisa.env` contiene credenciales locales y debe permanecer únicamente en el equipo donde se ejecuta el proceso.

El `.gitignore` debe incluir como mínimo:

```gitignore
# Credenciales locales SISA
scripts/mpr/config_sisa.env

# Archivos temporales y logs de automatizaciones
archive/

# Censos crudos MPR descargados desde SISA
data/mpr/raw/censo_visitasMPR.xlsx
data/mpr/raw/censo_visitasMPR_backup_*.xlsx
data/mpr/historical/
```

---

## 9. Publicación en GitHub

El repositorio oficial de publicación es:

```text
UESVALLE/uesvalle.github.io
```

La rama local `main` debe hacer seguimiento a:

```text
uesvalle/main
```

Para verificar:

```powershell
git status
```

Debe mostrar:

```text
Your branch is up to date with 'uesvalle/main'.
```

---

## 10. Procedimiento operativo

### Actualización local y publicación

Ejecutar:

```text
scripts/mpr/actualizar_mpr_desde_sisa.bat
```

Al finalizar, el proceso solicitará confirmación para realizar commit y push a GitHub.

Responder:

```text
S
```

solo si ya se verificó que el proceso terminó correctamente.

### Verificación posterior

Después de la actualización, revisar:

```powershell
git status
```

Validar que no aparezcan archivos sensibles como:

```text
scripts/mpr/config_sisa.env
data/mpr/raw/censo_visitasMPR.xlsx
```

---

## 11. Validaciones recomendadas en el tablero

Después de publicar, revisar en GitHub Pages:

1. Que el tablero cargue sin errores.
2. Que los KPIs coincidan con los resultados del proceso.
3. Que los filtros por ARO, municipio, funcionario y actividad funcionen.
4. Que las tablas carguen correctamente.
5. Que `metadata_mpr.json` muestre una fecha reciente de actualización.
6. Que las actividades 1.3, 1.4 y 1.5 estén visibles en el catálogo del tablero.

---

## 12. Estado del flujo

El flujo de datos del tablero MPR queda completo y funcional.

A partir de esta versión, no se deben separar manualmente archivos como:

```text
1.3_VisitasMPR.csv
1.4_MuestreoMPR.csv
1.5_ResolucionesMPR.csv
```

El proceso oficial parte del censo general descargado desde SISA.
