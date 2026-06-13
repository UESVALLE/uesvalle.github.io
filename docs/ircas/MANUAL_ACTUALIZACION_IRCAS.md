# Manual operativo - Actualización del Tablero IRCAS UESVALLE

## 1. Objetivo

Estandarizar la actualización del tablero IRCAS para que el archivo operativo `IRCAS.csv` se genere siempre desde una única fuente oficial:

```text
Base_Datos_Acueductos_2026.xlsx
Hoja: Acueductos
```

El tablero `ircas.html` no lee directamente el Excel. El tablero lee el CSV generado:

```text
data/ircas/current/IRCAS.csv
```

## 2. Estructura recomendada

Dentro del repositorio `UESVALLE`:

```text
UESVALLE/
├─ dashboards/
│  └─ ircas/
│     └─ ircas.html
├─ data/
│  └─ ircas/
│     ├─ input/
│     │  └─ Base_Datos_Acueductos_2026.xlsx
│     ├─ current/
│     │  └─ IRCAS.csv
│     ├─ archive/
│     │  └─ IRCAS_backup_YYYYMMDD_HHMMSS.csv
│     └─ logs/
│        ├─ control_generacion_ircas_YYYYMMDD_HHMMSS.csv
│        └─ control_coordenadas_ircas_YYYYMMDD_HHMMSS.csv
└─ scripts/
   └─ ircas/
      └─ generar_ircas_desde_base_acueductos.py
```

## 3. Flujo de actualización

1. Actualizar el archivo maestro:

```text
data/ircas/input/Base_Datos_Acueductos_2026.xlsx
```

2. Ejecutar el script:

```powershell
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
python "scripts\ircas\generar_ircas_desde_base_acueductos.py"
```

3. Verificar que se actualizó:

```text
data/ircas/current/IRCAS.csv
```

4. Revisar los reportes de control:

```text
data/ircas/logs/
```

5. Probar el tablero localmente o desde GitHub Pages.

6. Subir cambios a GitHub:

```powershell
git status
git add data/ircas/current/IRCAS.csv data/ircas/logs scripts/ircas
git commit -m "Actualizar datos tablero IRCAS"
git push
```

## 4. Qué hace el script

El script realiza las siguientes tareas:

- Lee la hoja `Acueductos` del archivo `Base_Datos_Acueductos_2026.xlsx`.
- Elimina la fila final `Total`.
- Conserva los 690 registros operativos, incluidos sistemas sin `CODIGO_SISTEMA`.
- Normaliza campos de texto, riesgos, fechas y números.
- Construye las columnas exactas que espera el tablero `ircas.html`.
- Conserva `Latitud_X`, `Longitud_Y` e `Img_bocatoma` desde el `IRCAS.csv` actual.
- Genera backup automático del CSV anterior.
- Genera reportes de control.

## 5. Columnas críticas del archivo generado

El archivo `IRCAS.csv` debe conservar estas columnas principales:

```text
No.
CODIGO_ANTERIOR
CODIGO_SISTEMA
Latitud_X
Longitud_Y
MUNICIPIO
TIPO
CODIGO IVC2
CODIGO MUESTREO
CODIGO_AT
ID_SSPD
TIPO_SISTEMA_TRATAMIENTO
ALGUN_TIPO_TRATAMIENTO
LOCALIDADES ABASTECIDAS
NUMERO_LOCALIDADES
ARO
Persona Prestadora
Forma_organizativa
Registrados_SSPD
SIVICAP_Registrados_SSPD
SUSCRIPTORES
POBLACION
IRCA_2020
Nivel de Riesgo_2020
Fecha ultimo IRCA_2020
IRCA_2021
Nivel de Riesgo_2021
Fecha ultimo IRCA_2021
IRCA_2022
Nivel de Riesgo_2022
Fecha ultimo IRCA_2022
IRCA_2023
Nivel de Riesgo_2023
FECHA_IRCA_2023
IRCA_2024
Nivel_de_Riesgo_2024
Fecha_IRCA_2024
IRCA_2025
Nivel_Riesgo_2025
Fecha_Ultimo_IRCA_2025
Punto_Toma_2025
IRCA_Promedio
Img_bocatoma
```

## 6. Validaciones mínimas después de ejecutar

Revisar en los reportes:

- número de registros generados;
- vacíos en `CODIGO_SISTEMA`;
- vacíos en `MUNICIPIO`;
- vacíos en `Latitud_X` y `Longitud_Y`;
- vacíos en `IRCA_2025`;
- duplicados por `No.`;
- registros sin cruce de coordenadas.

## 7. Nota técnica

Los archivos de `data/muestras_irca/current/` pertenecen al tablero de muestras o resultados analíticos. No son requeridos para actualizar el tablero IRCAS general.

El tablero IRCAS general usa únicamente:

```text
data/ircas/current/IRCAS.csv
```
