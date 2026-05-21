# -*- coding: utf-8 -*-
"""
Normalización de seguimiento de actividades ACH - UESVALLE
Versión: V4 Enero-Junio
Autor: ChatGPT
Fecha: 2026-05-11

Este script toma el archivo Excel de seguimiento de actividades del proceso
Agua para Consumo Humano y genera:

1. CSV detalle depurado
2. CSV resumen municipal
3. CSV resumen por responsable
4. CSV resumen por actividad
5. Excel consolidado con hojas para lectura y análisis

Ruta del proyecto:
G:\Mi unidad\8.UES\PAGINA INDICADORES\Seguimiento
"""

from pathlib import Path
import re
import unicodedata
import pandas as pd
import numpy as np


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

BASE_DIR = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\Seguimiento")

ENTRADA_DIR = BASE_DIR / "01_Entrada"
OUT_DIR = BASE_DIR / "02_Salidas"

SHEET_NAME = "Seguimiento"

# IMPORTANTE:
# El archivo debe estar exactamente en:
# G:\Mi unidad\8.UES\PAGINA INDICADORES\Seguimiento\01_Entrada\Seguimiento_EneroJunio.xlsx
NOMBRE_ARCHIVO_ENTRADA = "Seguimiento_EneroJunio.xlsx"
INPUT_XLSX = ENTRADA_DIR / NOMBRE_ARCHIVO_ENTRADA

PERIODO_NORMALIZADO = "Enero - Junio"
ANIO = 2026
MES_INICIO = "Enero"
MES_FIN = "Junio"


# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

def quitar_tildes(texto):
    """Quita tildes y caracteres diacríticos."""
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in texto if not unicodedata.combining(c)])


def limpiar_texto(texto):
    """Limpia espacios dobles y deja texto en mayúsculas."""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto.upper()


def limpiar_nombre(nombre):
    """Limpia nombres de responsables y separa sufijos tipo ING AGUAS."""
    nombre_limpio = limpiar_texto(nombre)
    nombre_limpio = nombre_limpio.replace("  ", " ")
    return nombre_limpio


def normalizar_codigo_actividad(codigo):
    """Normaliza el código de actividad para clasificar y usar en tablero."""
    c = limpiar_texto(codigo)
    c = c.replace(",", ".")
    c = re.sub(r"\s+", "", c)
    c = re.sub(r"\.+$", "", c)
    return c


def clasificar_actividad(codigo):
    """
    Clasifica el código de actividad en grandes grupos para el tablero.

    Reglas:
    - Códigos 12, 12.1, 12.x => Actividades Administrativas
    - Códigos específicos 1.x, 2.x y 5.x definidos por el usuario => Operativo
    - Los demás => OTROS
    """
    c = normalizar_codigo_actividad(codigo)

    if c == "12" or c.startswith("12."):
        return "Actividades Administrativas"

    codigos_operativos = {
        "1.1", "1.10", "1.13", "1.17", "1.2", "1.3", "1.4", "1.5", "1.7", "1.8",
        "2.1", "2.10", "2.18", "2.2", "2.20", "2.3",
        "5.2", "5.24", "5.34", "5.4",
    }

    if c in codigos_operativos:
        return "Operativo"

    return "OTROS"


def clasificar_tipo_territorio(municipio):
    """Clasifica si el registro corresponde a municipio o actividad general/administrativa."""
    m = limpiar_texto(municipio)
    m_sin_tilde = quitar_tildes(m)

    administrativos = {
        "PQRS",
        "ADMINISTRATIVO",
        "ADMINSITRATIVO",
        "ADMINISTRATIVA",
        "ADMINSITRATIVA",
    }

    generales = {
        "JURISDICCION",
        "JURISDICCIÓN",
        "JURISDICCION DEPARTAMENTAL",
        "JURISDICCIÓN DEPARTAMENTAL",
    }

    if m_sin_tilde in administrativos:
        return "Administrativo"

    if m_sin_tilde in quitar_tildes(" ".join(generales)).split("  "):
        return "General"

    if m_sin_tilde in {"JURISDICCION", "JURISDICCION DEPARTAMENTAL"}:
        return "General"

    if m == "":
        return "Sin dato"

    return "Municipio"


def estado_cumplimiento(valor):
    """Clasifica el cumplimiento en rangos para tablero."""
    if pd.isna(valor):
        return "Sin dato"

    try:
        v = float(valor)
    except Exception:
        return "Sin dato"

    if v < 0:
        return "Sin dato"
    if v <= 0.30:
        return "Crítico"
    if v <= 0.60:
        return "Bajo"
    if v <= 0.80:
        return "Medio"
    if v <= 1.00:
        return "Cumplido"
    return "Supera meta"


def extraer_rol_equipo(nombre):
    """Extrae etiquetas de equipo dentro del nombre, por ejemplo ING AGUAS1."""
    n = limpiar_texto(nombre)

    patrones = [
        r"(ING\s*AGUAS\s*\d*)",
        r"(AGUAS\s*\d*)",
    ]

    for patron in patrones:
        m = re.search(patron, n)
        if m:
            return limpiar_texto(m.group(1))

    return ""


def validar_rutas():
    """Valida carpetas y archivo de entrada antes de procesar."""
    print("=" * 80)
    print("CONFIGURACIÓN DE RUTAS - NORMALIZACIÓN SEGUIMIENTO ACH V4 ENERO-JUNIO")
    print(f"BASE_DIR:    {BASE_DIR}")
    print(f"ENTRADA_DIR: {ENTRADA_DIR}")
    print(f"INPUT_XLSX:  {INPUT_XLSX}")
    print(f"OUT_DIR:     {OUT_DIR}")
    print("=" * 80)

    if not BASE_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta base:\n{BASE_DIR}\n\n"
            "Verifica que Google Drive esté sincronizado y que la unidad G: esté disponible."
        )

    if not ENTRADA_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de entrada:\n{ENTRADA_DIR}\n\n"
            "Crea la carpeta 01_Entrada o revisa que Google Drive esté sincronizado."
        )

    if not INPUT_XLSX.exists():
        disponibles_xlsx = sorted([x.name for x in ENTRADA_DIR.glob("*.xlsx")])
        disponibles_excel = sorted([x.name for x in ENTRADA_DIR.glob("*.xls*")])

        raise FileNotFoundError(
            f"No se encontró el archivo de entrada:\n{INPUT_XLSX}\n\n"
            f"Archivos .xlsx encontrados en 01_Entrada:\n{disponibles_xlsx if disponibles_xlsx else 'Ninguno'}\n\n"
            f"Archivos Excel encontrados en 01_Entrada:\n{disponibles_excel if disponibles_excel else 'Ninguno'}\n\n"
            "Solución:\n"
            f"1. Verifica que el archivo se llame exactamente: {NOMBRE_ARCHIVO_ENTRADA}\n"
            "2. Verifica que esté dentro de la carpeta 01_Entrada.\n"
            "3. Revisa que no tenga espacios adicionales ni extensión diferente."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)


def normalizar_columnas(df):
    """Normaliza nombres de columnas para reducir errores."""
    df = df.copy()
    df.columns = [
        limpiar_texto(c)
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        for c in df.columns
    ]
    return df


def detectar_columna(df, posibles):
    """Busca una columna por posibles nombres normalizados."""
    cols = list(df.columns)
    for p in posibles:
        p_norm = limpiar_texto(p)
        p_norm = quitar_tildes(p_norm)
        for c in cols:
            if quitar_tildes(c) == p_norm:
                return c
    return None


def preparar_detalle(df):
    """Crea la base depurada con campos calculados."""
    df = normalizar_columnas(df)

    col_nombre = detectar_columna(df, ["NOMBRE"])
    col_municipio = detectar_columna(df, ["MUNICIPIO"])
    col_codigo = detectar_columna(df, ["CODIGO ACTIVIDAD", "CÓDIGO ACTIVIDAD"])
    col_aro = detectar_columna(df, ["ARO"])
    col_periodo = detectar_columna(df, ["PERIODO", "PERÍODO"])
    col_tipo = detectar_columna(df, ["TIPO"])
    col_programado = detectar_columna(df, ["PROGRAMADO"])
    col_ejecutado = detectar_columna(df, ["EJECUTADO RASEM", "EJECUTADO"])
    col_pendiente = detectar_columna(df, ["PENDIENTE"])
    col_cumplimiento = detectar_columna(df, ["% CUMPLIMIENTO", "CUMPLIMIENTO"])

    requeridas = {
        "NOMBRE": col_nombre,
        "MUNICIPIO": col_municipio,
        "CODIGO ACTIVIDAD": col_codigo,
        "ARO": col_aro,
        "TIPO": col_tipo,
        "PROGRAMADO": col_programado,
        "EJECUTADO RASEM": col_ejecutado,
    }

    faltantes = [k for k, v in requeridas.items() if v is None]
    if faltantes:
        raise ValueError(
            "No se encontraron columnas requeridas en el Excel:\n"
            + "\n".join(f"- {x}" for x in faltantes)
            + "\n\nColumnas encontradas:\n"
            + "\n".join(df.columns)
        )

    out = pd.DataFrame()
    out["NOMBRE_ORIGINAL"] = df[col_nombre]
    out["RESPONSABLE"] = df[col_nombre].apply(limpiar_nombre)
    out["ROL_EQUIPO"] = df[col_nombre].apply(extraer_rol_equipo)

    out["MUNICIPIO_ORIGINAL"] = df[col_municipio]
    out["MUNICIPIO_NORMALIZADO"] = df[col_municipio].apply(limpiar_texto)
    out["TIPO_TERRITORIO"] = out["MUNICIPIO_NORMALIZADO"].apply(clasificar_tipo_territorio)
    out["ES_MUNICIPIO"] = np.where(out["TIPO_TERRITORIO"] == "Municipio", "Sí", "No")

    # Código operativo original y clasificación funcional para tablero
    out["CODIGO"] = df[col_codigo].apply(normalizar_codigo_actividad)
    out["CODIGO_ACTIVIDAD"] = out["CODIGO"]  # Se conserva por compatibilidad con versiones anteriores del tablero.
    out["ACTIVIDADES"] = out["CODIGO"].apply(clasificar_actividad)

    out["ARO"] = df[col_aro].apply(limpiar_texto)

    if col_periodo:
        out["PERIODO_ORIGINAL"] = df[col_periodo]
    else:
        out["PERIODO_ORIGINAL"] = PERIODO_NORMALIZADO

    out["PERIODO_NORMALIZADO"] = PERIODO_NORMALIZADO
    out["ANIO"] = ANIO
    out["MES_INICIO"] = MES_INICIO
    out["MES_FIN"] = MES_FIN

    out["TIPO"] = df[col_tipo].apply(limpiar_texto)

    out["PROGRAMADO"] = pd.to_numeric(df[col_programado], errors="coerce").fillna(0)
    out["EJECUTADO_RASEM"] = pd.to_numeric(df[col_ejecutado], errors="coerce").fillna(0)

    if col_pendiente:
        out["PENDIENTE_ORIGINAL"] = pd.to_numeric(df[col_pendiente], errors="coerce")
    else:
        out["PENDIENTE_ORIGINAL"] = np.nan

    out["PENDIENTE_CALCULADO"] = out["PROGRAMADO"] - out["EJECUTADO_RASEM"]
    out["PENDIENTE_VISUAL"] = out["PENDIENTE_CALCULADO"].clip(lower=0)
    out["EXCEDENTE"] = (out["EJECUTADO_RASEM"] - out["PROGRAMADO"]).clip(lower=0)

    out["CUMPLIMIENTO_CALCULADO"] = np.where(
        out["PROGRAMADO"] > 0,
        out["EJECUTADO_RASEM"] / out["PROGRAMADO"],
        np.nan
    )

    if col_cumplimiento:
        cumplimiento_original = pd.to_numeric(df[col_cumplimiento], errors="coerce")
        # Si viene en porcentaje 50, lo convierte a 0.50.
        out["CUMPLIMIENTO_ORIGINAL"] = np.where(
            cumplimiento_original > 1,
            cumplimiento_original / 100,
            cumplimiento_original
        )
    else:
        out["CUMPLIMIENTO_ORIGINAL"] = np.nan

    out["CUMPLIMIENTO_VISUAL"] = pd.Series(out["CUMPLIMIENTO_CALCULADO"]).clip(upper=1)
    out["ESTADO_CUMPLIMIENTO"] = out["CUMPLIMIENTO_CALCULADO"].apply(estado_cumplimiento)

    return out


def resumen_agrupado(df, group_cols):
    """Genera resumen estándar por columnas seleccionadas."""
    res = (
        df.groupby(group_cols, dropna=False)
        .agg(
            REGISTROS=("CODIGO_ACTIVIDAD", "count"),
            RESPONSABLES=("RESPONSABLE", "nunique"),
            CODIGOS_DISTINTOS=("CODIGO", "nunique"),
            PROGRAMADO=("PROGRAMADO", "sum"),
            EJECUTADO_RASEM=("EJECUTADO_RASEM", "sum"),
            PENDIENTE_CALCULADO=("PENDIENTE_CALCULADO", "sum"),
            PENDIENTE_VISUAL=("PENDIENTE_VISUAL", "sum"),
            EXCEDENTE=("EXCEDENTE", "sum"),
        )
        .reset_index()
    )

    res["CUMPLIMIENTO_CALCULADO"] = np.where(
        res["PROGRAMADO"] > 0,
        res["EJECUTADO_RASEM"] / res["PROGRAMADO"],
        np.nan
    )
    res["CUMPLIMIENTO_VISUAL"] = pd.Series(res["CUMPLIMIENTO_CALCULADO"]).clip(upper=1)
    res["ESTADO_CUMPLIMIENTO"] = res["CUMPLIMIENTO_CALCULADO"].apply(estado_cumplimiento)

    return res


def crear_resumen_general(df, resumen_aro, resumen_tipo, resumen_actividad, resumen_municipal):
    """Crea una hoja de resumen para Excel."""
    total_programado = df["PROGRAMADO"].sum()
    total_ejecutado = df["EJECUTADO_RASEM"].sum()
    total_pendiente = df["PENDIENTE_VISUAL"].sum()
    cumplimiento = total_ejecutado / total_programado if total_programado > 0 else np.nan

    kpis = pd.DataFrame({
        "Indicador": [
            "Periodo",
            "Año",
            "Registros",
            "Responsables",
            "Municipios reales",
            "Actividades diferentes",
            "Total programado",
            "Total ejecutado",
            "Total pendiente visual",
            "Cumplimiento global",
        ],
        "Valor": [
            PERIODO_NORMALIZADO,
            ANIO,
            len(df),
            df["RESPONSABLE"].nunique(),
            df.loc[df["ES_MUNICIPIO"] == "Sí", "MUNICIPIO_NORMALIZADO"].nunique(),
            df["CODIGO"].nunique() if "CODIGO" in df.columns else df["CODIGO_ACTIVIDAD"].nunique(),
            total_programado,
            total_ejecutado,
            total_pendiente,
            cumplimiento,
        ]
    })

    top_act_pend = resumen_actividad.sort_values("PENDIENTE_VISUAL", ascending=False).head(10)
    top_mun_pend = resumen_municipal.sort_values("PENDIENTE_VISUAL", ascending=False).head(10)

    return kpis, top_act_pend, top_mun_pend


def escribir_excel_salida(
    output_xlsx,
    detalle,
    resumen_municipal,
    resumen_responsable,
    resumen_actividad,
    resumen_aro,
    resumen_tipo
):
    """Genera Excel con formato básico y varias hojas."""
    kpis, top_act_pend, top_mun_pend = crear_resumen_general(
        detalle,
        resumen_aro,
        resumen_tipo,
        resumen_actividad,
        resumen_municipal
    )

    diccionario = pd.DataFrame({
        "Campo": [
            "RESPONSABLE",
            "ROL_EQUIPO",
            "MUNICIPIO_NORMALIZADO",
            "TIPO_TERRITORIO",
            "ES_MUNICIPIO",
            "CODIGO",
            "ACTIVIDADES",
            "CODIGOS_DISTINTOS",
            "PENDIENTE_CALCULADO",
            "PENDIENTE_VISUAL",
            "EXCEDENTE",
            "CUMPLIMIENTO_CALCULADO",
            "CUMPLIMIENTO_VISUAL",
            "ESTADO_CUMPLIMIENTO",
        ],
        "Descripción": [
            "Nombre del responsable normalizado en mayúsculas.",
            "Etiqueta de equipo o rol extraída del nombre, cuando existe.",
            "Municipio depurado para filtros y cruces con mapa.",
            "Clasificación del registro: Municipio, General, Administrativo, Sin dato.",
            "Indica si el registro puede usarse para mapa municipal.",
            "Código de actividad depurado. Sustituye el uso visual de CODIGO_ACTIVIDAD en el tablero.",
            "Clasificación funcional del código: Operativo, Actividades Administrativas u OTROS.",
            "Número de códigos de actividad distintos en el grupo agregado.",
            "PROGRAMADO - EJECUTADO_RASEM. Puede ser negativo si hay sobrecumplimiento.",
            "Pendiente usado para visualización. No baja de cero.",
            "Actividades ejecutadas por encima de lo programado.",
            "EJECUTADO_RASEM / PROGRAMADO.",
            "Cumplimiento limitado a 100% para gráficos.",
            "Clasificación semafórica del cumplimiento.",
        ]
    })

    with pd.ExcelWriter(output_xlsx, engine="xlsxwriter") as writer:
        workbook = writer.book

        fmt_header = workbook.add_format({
            "bold": True,
            "bg_color": "#1F4E78",
            "font_color": "white",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        })
        fmt_percent = workbook.add_format({"num_format": "0.0%"})
        fmt_number = workbook.add_format({"num_format": "#,##0"})
        fmt_title = workbook.add_format({
            "bold": True,
            "font_size": 14,
            "font_color": "#1F4E78",
        })

        # Hoja resumen organizada por bloques
        sheet_name = "Resumen"
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        worksheet.write(0, 0, "Resumen seguimiento actividades ACH", fmt_title)
        worksheet.write(1, 0, f"Periodo: {PERIODO_NORMALIZADO} {ANIO}")

        start = 3
        worksheet.write(start, 0, "Indicadores generales", fmt_title)
        kpis.to_excel(writer, sheet_name=sheet_name, startrow=start + 1, startcol=0, index=False)

        start2 = start + len(kpis) + 4
        worksheet.write(start2, 0, "Resumen por ARO", fmt_title)
        resumen_aro.to_excel(writer, sheet_name=sheet_name, startrow=start2 + 1, startcol=0, index=False)

        start3 = start2 + len(resumen_aro) + 4
        worksheet.write(start3, 0, "Resumen por tipo", fmt_title)
        resumen_tipo.to_excel(writer, sheet_name=sheet_name, startrow=start3 + 1, startcol=0, index=False)

        start4 = 3
        col4 = 11
        worksheet.write(start4, col4, "Top 10 actividades con mayor pendiente", fmt_title)
        top_act_pend.to_excel(writer, sheet_name=sheet_name, startrow=start4 + 1, startcol=col4, index=False)

        start5 = start4 + len(top_act_pend) + 4
        worksheet.write(start5, col4, "Top 10 municipios con mayor pendiente", fmt_title)
        top_mun_pend.to_excel(writer, sheet_name=sheet_name, startrow=start5 + 1, startcol=col4, index=False)

        # Otras hojas
        hojas = {
            "Detalle_Depurado": detalle,
            "Resumen_Municipal": resumen_municipal,
            "Resumen_Responsable": resumen_responsable,
            "Resumen_Actividad": resumen_actividad,
            "Resumen_ARO": resumen_aro,
            "Resumen_Tipo": resumen_tipo,
            "Diccionario": diccionario,
        }

        for nombre_hoja, data in hojas.items():
            data.to_excel(writer, sheet_name=nombre_hoja, index=False)
            ws = writer.sheets[nombre_hoja]

            # Encabezado
            for col_num, value in enumerate(data.columns.values):
                ws.write(0, col_num, value, fmt_header)

            # Filtro y congelar primera fila
            ws.autofilter(0, 0, max(len(data), 1), max(len(data.columns) - 1, 0))
            ws.freeze_panes(1, 0)

            # Anchos y formatos
            for idx, col in enumerate(data.columns):
                ancho = min(max(len(str(col)) + 3, 14), 35)
                ws.set_column(idx, idx, ancho)

                if "CUMPLIMIENTO" in col:
                    ws.set_column(idx, idx, 18, fmt_percent)

                if col in [
                    "PROGRAMADO",
                    "EJECUTADO_RASEM",
                    "PENDIENTE_CALCULADO",
                    "PENDIENTE_VISUAL",
                    "EXCEDENTE",
                    "REGISTROS",
                    "RESPONSABLES",
                    "ACTIVIDADES",
                ]:
                    ws.set_column(idx, idx, 16, fmt_number)

        # Formato básico hoja Resumen
        for ws_name in ["Resumen"]:
            ws = writer.sheets[ws_name]
            ws.set_column(0, 0, 28)
            ws.set_column(1, 1, 20)
            ws.set_column(11, 25, 18)

    print(f"Excel generado: {output_xlsx}")


# ============================================================
# 3. PROCESAMIENTO PRINCIPAL
# ============================================================

def main():
    validar_rutas()

    print("Leyendo archivo Excel...")
    print(f"Archivo: {INPUT_XLSX}")

    df_raw = pd.read_excel(INPUT_XLSX, sheet_name=SHEET_NAME)

    print(f"Registros leídos: {len(df_raw):,}")
    print("Columnas encontradas:")
    for c in df_raw.columns:
        print(f" - {c}")

    print("Normalizando detalle...")
    detalle = preparar_detalle(df_raw)

    print("Generando resúmenes...")
    detalle_municipios = detalle[detalle["ES_MUNICIPIO"] == "Sí"].copy()

    resumen_municipal = resumen_agrupado(
        detalle_municipios,
        ["MUNICIPIO_NORMALIZADO", "ARO", "PERIODO_NORMALIZADO", "ANIO"]
    )

    resumen_responsable = resumen_agrupado(
        detalle,
        ["RESPONSABLE", "ROL_EQUIPO", "TIPO", "ARO", "PERIODO_NORMALIZADO", "ANIO"]
    )

    resumen_actividad = resumen_agrupado(
        detalle,
        ["ACTIVIDADES", "CODIGO", "CODIGO_ACTIVIDAD", "ARO", "TIPO", "PERIODO_NORMALIZADO", "ANIO"]
    )

    resumen_aro = resumen_agrupado(
        detalle,
        ["ARO", "PERIODO_NORMALIZADO", "ANIO"]
    )

    resumen_tipo = resumen_agrupado(
        detalle,
        ["TIPO", "PERIODO_NORMALIZADO", "ANIO"]
    )

    # Nombres de salida
    csv_detalle = OUT_DIR / "seguimiento_actividades_ACH_detalle.csv"
    csv_municipal = OUT_DIR / "seguimiento_actividades_ACH_resumen_municipal.csv"
    csv_responsable = OUT_DIR / "seguimiento_actividades_ACH_resumen_responsable.csv"
    csv_actividad = OUT_DIR / "seguimiento_actividades_ACH_resumen_actividad.csv"
    csv_aro = OUT_DIR / "seguimiento_actividades_ACH_resumen_aro.csv"
    csv_tipo = OUT_DIR / "seguimiento_actividades_ACH_resumen_tipo.csv"

    excel_salida = OUT_DIR / f"seguimiento_actividades_ACH_{ANIO}_{MES_INICIO}_{MES_FIN}.xlsx"

    print("Guardando CSV...")
    detalle.to_csv(csv_detalle, index=False, encoding="utf-8-sig")
    resumen_municipal.to_csv(csv_municipal, index=False, encoding="utf-8-sig")
    resumen_responsable.to_csv(csv_responsable, index=False, encoding="utf-8-sig")
    resumen_actividad.to_csv(csv_actividad, index=False, encoding="utf-8-sig")
    resumen_aro.to_csv(csv_aro, index=False, encoding="utf-8-sig")
    resumen_tipo.to_csv(csv_tipo, index=False, encoding="utf-8-sig")

    print("Guardando Excel de lectura...")
    escribir_excel_salida(
        excel_salida,
        detalle,
        resumen_municipal,
        resumen_responsable,
        resumen_actividad,
        resumen_aro,
        resumen_tipo
    )

    print("=" * 80)
    print("PROCESO FINALIZADO CORRECTAMENTE")
    print("Archivos generados en:")
    print(OUT_DIR)
    print("=" * 80)
    print(f"- {csv_detalle.name}")
    print(f"- {csv_municipal.name}")
    print(f"- {csv_responsable.name}")
    print(f"- {csv_actividad.name}")
    print(f"- {csv_aro.name}")
    print(f"- {csv_tipo.name}")
    print(f"- {excel_salida.name}")


if __name__ == "__main__":
    main()
