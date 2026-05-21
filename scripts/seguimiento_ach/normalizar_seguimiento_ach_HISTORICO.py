# -*- coding: utf-8 -*-
"""
Normalización histórica de seguimiento de actividades ACH - UESVALLE
Versión: HISTÓRICO Enero-Marzo + Enero-Junio
Autor: ChatGPT
Fecha: 2026-05-20

Objetivo:
- Leer varios cortes de seguimiento, por ejemplo:
  1) Enero - Marzo
  2) Enero - Junio
- Consolidarlos en un solo detalle histórico.
- Generar CSV compatibles con el tablero seguimiento_ach.html.
- Mantener el filtro PERIODO_NORMALIZADO para comparar cortes.

Ruta esperada:
G:\Mi unidad\8.UES\PAGINA INDICADORES\Seguimiento

Estructura esperada:
Seguimiento/
├── 01_Entrada/
│   ├── Seguimiento_EneroMarzo.xlsx
│   └── Seguimiento_EneroJunio.xlsx
├── 02_Salidas/
└── 03_Script/

Nota:
Si no existe el archivo fuente de Enero-Marzo en 01_Entrada, el script intenta usar el Excel
ya generado previamente en 02_Salidas:
seguimiento_actividades_ACH_2026_Enero_Marzo.xlsx
"""

from pathlib import Path
import os
import re
import unicodedata
import pandas as pd
import numpy as np


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

BASE_DIR = Path(
    os.environ.get(
        "SEGUIMIENTO_ACH_BASE_DIR",
        r"G:\Mi unidad\8.UES\PAGINA INDICADORES\Seguimiento"
    )
)

ENTRADA_DIR = BASE_DIR / "01_Entrada"
OUT_DIR = BASE_DIR / "02_Salidas"

SHEET_RAW = "Seguimiento"
SHEET_DEPURADO = "Detalle_Depurado"

ANIO = 2026

# Agrega aquí nuevos cortes cuando lleguen otros periodos.
# El script busca cada archivo en 01_Entrada y, si no lo encuentra, en 02_Salidas.
CORTES = [
    {
        "periodo": "Enero - Marzo",
        "periodo_orden": 1,
        "mes_inicio": "Enero",
        "mes_fin": "Marzo",
        "archivos_posibles": [
            "Seguimiento_EneroMarzo.xlsx",
            "seguimiento_actividades_ACH_2026_Enero_Marzo.xlsx",
            "seguimiento_actividades_ACH_enero_marzo.xlsx",
        ],
    },
    {
        "periodo": "Enero - Junio",
        "periodo_orden": 2,
        "mes_inicio": "Enero",
        "mes_fin": "Junio",
        "archivos_posibles": [
            "Seguimiento_EneroJunio.xlsx",
            "seguimiento_actividades_ACH_2026_Enero_Junio.xlsx",
            "seguimiento_actividades_ACH_2026_EneroJunio.xlsx",
        ],
    },
]


# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

def quitar_tildes(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in texto if not unicodedata.combining(c)])


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto.upper()


def limpiar_nombre(nombre):
    nombre_limpio = limpiar_texto(nombre)
    nombre_limpio = nombre_limpio.replace("  ", " ")
    return nombre_limpio


def normalizar_codigo_actividad(codigo):
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
    m = limpiar_texto(municipio)
    m_sin_tilde = quitar_tildes(m)

    administrativos = {
        "PQRS",
        "ADMINISTRATIVO",
        "ADMINSITRATIVO",
        "ADMINISTRATIVA",
        "ADMINSITRATIVA",
    }

    if m_sin_tilde in administrativos:
        return "Administrativo"

    if m_sin_tilde in {"JURISDICCION", "JURISDICCION DEPARTAMENTAL"}:
        return "General"

    if m == "":
        return "Sin dato"

    return "Municipio"


def estado_cumplimiento(valor):
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


def normalizar_columnas(df):
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
    cols = list(df.columns)
    for p in posibles:
        p_norm = quitar_tildes(limpiar_texto(p))
        for c in cols:
            if quitar_tildes(c) == p_norm:
                return c
    return None


def encontrar_archivo_corte(corte):
    """
    Busca el archivo del corte en 01_Entrada y 02_Salidas.
    Retorna Path si lo encuentra.
    """
    rutas_busqueda = [ENTRADA_DIR, OUT_DIR, BASE_DIR]

    for carpeta in rutas_busqueda:
        for nombre in corte["archivos_posibles"]:
            p = carpeta / nombre
            if p.exists():
                return p

    return None


def leer_excel_corte(path_excel):
    """
    Lee el Excel según la estructura disponible.
    Prioriza hoja Seguimiento si existe; si no, usa Detalle_Depurado.
    """
    xls = pd.ExcelFile(path_excel)
    hojas = xls.sheet_names

    if SHEET_RAW in hojas:
        return pd.read_excel(path_excel, sheet_name=SHEET_RAW), "raw"

    if SHEET_DEPURADO in hojas:
        return pd.read_excel(path_excel, sheet_name=SHEET_DEPURADO), "depurado"

    # Si no encuentra nombres esperados, usa la primera hoja.
    return pd.read_excel(path_excel, sheet_name=hojas[0]), "raw"


def preparar_detalle_raw(df, corte):
    """Crea la base depurada desde el Excel fuente original."""
    df = normalizar_columnas(df)

    col_nombre = detectar_columna(df, ["NOMBRE"])
    col_municipio = detectar_columna(df, ["MUNICIPIO"])
    col_codigo = detectar_columna(df, ["CODIGO ACTIVIDAD", "CÓDIGO ACTIVIDAD", "CODIGO", "CODIGO_ACTIVIDAD"])
    col_aro = detectar_columna(df, ["ARO"])
    col_periodo = detectar_columna(df, ["PERIODO", "PERÍODO"])
    col_tipo = detectar_columna(df, ["TIPO"])
    col_programado = detectar_columna(df, ["PROGRAMADO"])
    col_ejecutado = detectar_columna(df, ["EJECUTADO RASEM", "EJECUTADO", "EJECUTADO_RASEM"])
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

    out["CODIGO"] = df[col_codigo].apply(normalizar_codigo_actividad)
    out["CODIGO_ACTIVIDAD"] = out["CODIGO"]
    out["ACTIVIDADES"] = out["CODIGO"].apply(clasificar_actividad)

    out["ARO"] = df[col_aro].apply(limpiar_texto)

    if col_periodo:
        out["PERIODO_ORIGINAL"] = df[col_periodo]
    else:
        out["PERIODO_ORIGINAL"] = corte["periodo"]

    out["PERIODO_NORMALIZADO"] = corte["periodo"]
    out["PERIODO_ORDEN"] = corte["periodo_orden"]
    out["ANIO"] = ANIO
    out["MES_INICIO"] = corte["mes_inicio"]
    out["MES_FIN"] = corte["mes_fin"]

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


def preparar_detalle_depurado(df, corte):
    """
    Estandariza un Detalle_Depurado generado por versiones anteriores del script.
    Útil para recuperar Enero-Marzo cuando ya no se tiene el archivo fuente original.
    """
    df = normalizar_columnas(df)

    def col(posibles):
        return detectar_columna(df, posibles)

    c_resp = col(["RESPONSABLE", "NOMBRE"])
    c_nombre_original = col(["NOMBRE_ORIGINAL", "NOMBRE"])
    c_rol = col(["ROL_EQUIPO"])
    c_mun = col(["MUNICIPIO_NORMALIZADO", "MUNICIPIO"])
    c_mun_original = col(["MUNICIPIO_ORIGINAL", "MUNICIPIO"])
    c_codigo = col(["CODIGO", "CODIGO_ACTIVIDAD", "CODIGO ACTIVIDAD"])
    c_actividades = col(["ACTIVIDADES"])
    c_aro = col(["ARO"])
    c_tipo = col(["TIPO"])
    c_prog = col(["PROGRAMADO"])
    c_ejec = col(["EJECUTADO_RASEM", "EJECUTADO RASEM", "EJECUTADO"])
    c_pend_orig = col(["PENDIENTE_ORIGINAL", "PENDIENTE"])
    c_cump_orig = col(["CUMPLIMIENTO_ORIGINAL", "% CUMPLIMIENTO", "CUMPLIMIENTO"])

    requeridas = {
        "RESPONSABLE": c_resp,
        "MUNICIPIO": c_mun,
        "CODIGO": c_codigo,
        "ARO": c_aro,
        "TIPO": c_tipo,
        "PROGRAMADO": c_prog,
        "EJECUTADO_RASEM": c_ejec,
    }

    faltantes = [k for k, v in requeridas.items() if v is None]
    if faltantes:
        raise ValueError(
            "No se pudieron estandarizar columnas de Detalle_Depurado:\n"
            + "\n".join(f"- {x}" for x in faltantes)
            + "\n\nColumnas encontradas:\n"
            + "\n".join(df.columns)
        )

    out = pd.DataFrame()
    out["NOMBRE_ORIGINAL"] = df[c_nombre_original] if c_nombre_original else df[c_resp]
    out["RESPONSABLE"] = df[c_resp].apply(limpiar_nombre)
    out["ROL_EQUIPO"] = df[c_rol].apply(limpiar_texto) if c_rol else out["RESPONSABLE"].apply(extraer_rol_equipo)

    out["MUNICIPIO_ORIGINAL"] = df[c_mun_original] if c_mun_original else df[c_mun]
    out["MUNICIPIO_NORMALIZADO"] = df[c_mun].apply(limpiar_texto)
    out["TIPO_TERRITORIO"] = out["MUNICIPIO_NORMALIZADO"].apply(clasificar_tipo_territorio)
    out["ES_MUNICIPIO"] = np.where(out["TIPO_TERRITORIO"] == "Municipio", "Sí", "No")

    out["CODIGO"] = df[c_codigo].apply(normalizar_codigo_actividad)
    out["CODIGO_ACTIVIDAD"] = out["CODIGO"]
    if c_actividades:
        out["ACTIVIDADES"] = df[c_actividades].apply(lambda x: x if str(x).strip() else clasificar_actividad(x))
        out["ACTIVIDADES"] = out["CODIGO"].apply(clasificar_actividad)
    else:
        out["ACTIVIDADES"] = out["CODIGO"].apply(clasificar_actividad)

    out["ARO"] = df[c_aro].apply(limpiar_texto)
    out["PERIODO_ORIGINAL"] = corte["periodo"]
    out["PERIODO_NORMALIZADO"] = corte["periodo"]
    out["PERIODO_ORDEN"] = corte["periodo_orden"]
    out["ANIO"] = ANIO
    out["MES_INICIO"] = corte["mes_inicio"]
    out["MES_FIN"] = corte["mes_fin"]

    out["TIPO"] = df[c_tipo].apply(limpiar_texto)
    out["PROGRAMADO"] = pd.to_numeric(df[c_prog], errors="coerce").fillna(0)
    out["EJECUTADO_RASEM"] = pd.to_numeric(df[c_ejec], errors="coerce").fillna(0)

    out["PENDIENTE_ORIGINAL"] = pd.to_numeric(df[c_pend_orig], errors="coerce") if c_pend_orig else np.nan
    out["PENDIENTE_CALCULADO"] = out["PROGRAMADO"] - out["EJECUTADO_RASEM"]
    out["PENDIENTE_VISUAL"] = out["PENDIENTE_CALCULADO"].clip(lower=0)
    out["EXCEDENTE"] = (out["EJECUTADO_RASEM"] - out["PROGRAMADO"]).clip(lower=0)

    out["CUMPLIMIENTO_CALCULADO"] = np.where(
        out["PROGRAMADO"] > 0,
        out["EJECUTADO_RASEM"] / out["PROGRAMADO"],
        np.nan
    )

    if c_cump_orig:
        cumplimiento_original = pd.to_numeric(df[c_cump_orig], errors="coerce")
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


def crear_resumenes(detalle):
    detalle_municipios = detalle[detalle["ES_MUNICIPIO"] == "Sí"].copy()

    resumen_municipal = resumen_agrupado(
        detalle_municipios,
        ["PERIODO_NORMALIZADO", "PERIODO_ORDEN", "MUNICIPIO_NORMALIZADO", "ARO", "ANIO"]
    )

    resumen_responsable = resumen_agrupado(
        detalle,
        ["PERIODO_NORMALIZADO", "PERIODO_ORDEN", "RESPONSABLE", "ROL_EQUIPO", "TIPO", "ARO", "ANIO"]
    )

    resumen_actividad = resumen_agrupado(
        detalle,
        ["PERIODO_NORMALIZADO", "PERIODO_ORDEN", "ACTIVIDADES", "CODIGO", "CODIGO_ACTIVIDAD", "ARO", "TIPO", "ANIO"]
    )

    resumen_aro = resumen_agrupado(
        detalle,
        ["PERIODO_NORMALIZADO", "PERIODO_ORDEN", "ARO", "ANIO"]
    )

    resumen_tipo = resumen_agrupado(
        detalle,
        ["PERIODO_NORMALIZADO", "PERIODO_ORDEN", "TIPO", "ANIO"]
    )

    return resumen_municipal, resumen_responsable, resumen_actividad, resumen_aro, resumen_tipo


def crear_kpis_historicos(detalle):
    data = []
    for periodo, d in detalle.groupby(["PERIODO_NORMALIZADO", "PERIODO_ORDEN"], dropna=False):
        periodo_nombre, periodo_orden = periodo
        total_programado = d["PROGRAMADO"].sum()
        total_ejecutado = d["EJECUTADO_RASEM"].sum()
        total_pendiente = d["PENDIENTE_VISUAL"].sum()
        cumplimiento = total_ejecutado / total_programado if total_programado > 0 else np.nan

        data.append({
            "PERIODO_NORMALIZADO": periodo_nombre,
            "PERIODO_ORDEN": periodo_orden,
            "ANIO": ANIO,
            "REGISTROS": len(d),
            "RESPONSABLES": d["RESPONSABLE"].nunique(),
            "MUNICIPIOS_REALES": d.loc[d["ES_MUNICIPIO"] == "Sí", "MUNICIPIO_NORMALIZADO"].nunique(),
            "CODIGOS_DISTINTOS": d["CODIGO"].nunique(),
            "PROGRAMADO": total_programado,
            "EJECUTADO_RASEM": total_ejecutado,
            "PENDIENTE_VISUAL": total_pendiente,
            "EXCEDENTE": d["EXCEDENTE"].sum(),
            "CUMPLIMIENTO_CALCULADO": cumplimiento,
            "ESTADO_CUMPLIMIENTO": estado_cumplimiento(cumplimiento),
        })

    return pd.DataFrame(data).sort_values("PERIODO_ORDEN")


def escribir_excel_salida(
    output_xlsx,
    detalle,
    resumen_municipal,
    resumen_responsable,
    resumen_actividad,
    resumen_aro,
    resumen_tipo,
    kpis_historicos
):
    diccionario = pd.DataFrame({
        "Campo": [
            "PERIODO_NORMALIZADO",
            "PERIODO_ORDEN",
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
            "Corte del seguimiento: Enero - Marzo, Enero - Junio, etc.",
            "Orden numérico del corte para visualización histórica.",
            "Nombre del responsable normalizado en mayúsculas.",
            "Etiqueta de equipo o rol extraída del nombre, cuando existe.",
            "Municipio depurado para filtros y cruces con mapa.",
            "Clasificación del registro: Municipio, General, Administrativo, Sin dato.",
            "Indica si el registro puede usarse para mapa municipal.",
            "Código de actividad depurado.",
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

        hojas = {
            "KPIs_Historicos": kpis_historicos,
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

            for col_num, value in enumerate(data.columns.values):
                ws.write(0, col_num, value, fmt_header)

            ws.autofilter(0, 0, max(len(data), 1), max(len(data.columns) - 1, 0))
            ws.freeze_panes(1, 0)

            for idx, col in enumerate(data.columns):
                ancho = min(max(len(str(col)) + 3, 14), 38)
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
                    "CODIGOS_DISTINTOS",
                    "PERIODO_ORDEN",
                ]:
                    ws.set_column(idx, idx, 16, fmt_number)

        # Hoja de lectura ejecutiva
        ws = workbook.add_worksheet("Resumen_Ejecutivo")
        writer.sheets["Resumen_Ejecutivo"] = ws
        ws.write(0, 0, "Resumen histórico seguimiento actividades ACH", fmt_title)
        ws.write(2, 0, "Cortes incluidos", fmt_title)
        kpis_historicos.to_excel(writer, sheet_name="Resumen_Ejecutivo", startrow=3, startcol=0, index=False)

    print(f"Excel histórico generado: {output_xlsx}")


def validar_rutas():
    print("=" * 80)
    print("NORMALIZACIÓN HISTÓRICA SEGUIMIENTO ACH")
    print(f"BASE_DIR:    {BASE_DIR}")
    print(f"ENTRADA_DIR: {ENTRADA_DIR}")
    print(f"OUT_DIR:     {OUT_DIR}")
    print("=" * 80)

    if not BASE_DIR.exists():
        raise FileNotFoundError(f"No existe BASE_DIR:\n{BASE_DIR}")

    if not ENTRADA_DIR.exists():
        raise FileNotFoundError(f"No existe ENTRADA_DIR:\n{ENTRADA_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)


def procesar_cortes():
    detalles = []

    for corte in CORTES:
        print("-" * 80)
        print(f"Procesando corte: {corte['periodo']}")

        archivo = encontrar_archivo_corte(corte)

        if archivo is None:
            print(f"[ADVERTENCIA] No se encontró archivo para {corte['periodo']}. Se omitirá este corte.")
            print("Nombres buscados:")
            for n in corte["archivos_posibles"]:
                print(f" - {n}")
            continue

        print(f"Archivo encontrado: {archivo}")
        df, tipo_fuente = leer_excel_corte(archivo)
        print(f"Tipo de fuente detectada: {tipo_fuente}")
        print(f"Registros leídos: {len(df):,}")

        if tipo_fuente == "depurado":
            detalle = preparar_detalle_depurado(df, corte)
        else:
            detalle = preparar_detalle_raw(df, corte)

        detalle["FUENTE_ARCHIVO"] = archivo.name
        detalles.append(detalle)

        print(f"Registros normalizados: {len(detalle):,}")

    if not detalles:
        raise RuntimeError("No se pudo procesar ningún corte. Revisa los archivos de entrada.")

    return pd.concat(detalles, ignore_index=True)


def main():
    validar_rutas()

    print("Leyendo y normalizando cortes...")
    detalle = procesar_cortes()

    print("=" * 80)
    print("Consolidado histórico")
    print(f"Registros totales: {len(detalle):,}")
    print("Periodos incluidos:")
    print(detalle["PERIODO_NORMALIZADO"].value_counts(dropna=False).sort_index())
    print("=" * 80)

    print("Generando resúmenes históricos...")
    resumen_municipal, resumen_responsable, resumen_actividad, resumen_aro, resumen_tipo = crear_resumenes(detalle)
    kpis_historicos = crear_kpis_historicos(detalle)

    # Salidas oficiales para el tablero.
    csv_detalle = OUT_DIR / "seguimiento_actividades_ACH_detalle.csv"
    csv_municipal = OUT_DIR / "seguimiento_actividades_ACH_resumen_municipal.csv"
    csv_responsable = OUT_DIR / "seguimiento_actividades_ACH_resumen_responsable.csv"
    csv_actividad = OUT_DIR / "seguimiento_actividades_ACH_resumen_actividad.csv"
    csv_aro = OUT_DIR / "seguimiento_actividades_ACH_resumen_aro.csv"
    csv_tipo = OUT_DIR / "seguimiento_actividades_ACH_resumen_tipo.csv"
    csv_kpis = OUT_DIR / "seguimiento_actividades_ACH_kpis_historicos.csv"

    excel_salida = OUT_DIR / f"seguimiento_actividades_ACH_{ANIO}_Historico_Enero_Marzo_Enero_Junio.xlsx"

    print("Guardando CSV históricos...")
    detalle.to_csv(csv_detalle, index=False, encoding="utf-8-sig")
    resumen_municipal.to_csv(csv_municipal, index=False, encoding="utf-8-sig")
    resumen_responsable.to_csv(csv_responsable, index=False, encoding="utf-8-sig")
    resumen_actividad.to_csv(csv_actividad, index=False, encoding="utf-8-sig")
    resumen_aro.to_csv(csv_aro, index=False, encoding="utf-8-sig")
    resumen_tipo.to_csv(csv_tipo, index=False, encoding="utf-8-sig")
    kpis_historicos.to_csv(csv_kpis, index=False, encoding="utf-8-sig")

    print("Guardando Excel histórico...")
    escribir_excel_salida(
        excel_salida,
        detalle,
        resumen_municipal,
        resumen_responsable,
        resumen_actividad,
        resumen_aro,
        resumen_tipo,
        kpis_historicos
    )

    print("=" * 80)
    print("PROCESO HISTÓRICO FINALIZADO CORRECTAMENTE")
    print("Archivos generados en:")
    print(OUT_DIR)
    print("=" * 80)
    for p in [
        csv_detalle,
        csv_municipal,
        csv_responsable,
        csv_actividad,
        csv_aro,
        csv_tipo,
        csv_kpis,
        excel_salida,
    ]:
        print(f"- {p.name}")


if __name__ == "__main__":
    main()
