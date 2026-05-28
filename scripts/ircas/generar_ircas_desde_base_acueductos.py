# -*- coding: utf-8 -*-
r"""
UESVALLE - Generador de IRCAS.csv desde Base_Datos_Acueductos_2026.xlsx
Versión: 2026-05-27 / estructura IRCA 2020-2026

Objetivo
--------
Tomar como entrada única:

    data/ircas/input/Base_Datos_Acueductos_2026.xlsx
    Hoja: Acueductos

y generar el archivo operativo del tablero IRCAS:

    data/ircas/current/IRCAS.csv

Cambios principales de esta versión
-----------------------------------
1. Incorpora el año 2026.
2. Estandariza columnas anuales:
      IRCA_AAAA
      Nivel_de_Riesgo_AAAA
      Fecha_Ultimo_IRCA_AAAA
      Punto_Muestreo_AAAA / Punto_Toma_2026
3. Limpia #N/D, #N/A, N/D, N/A, nan, null como vacío para IRCA, riesgo y fechas.
4. Para Punto_Toma general y Punto_Toma_2026:
      vacío / #N/D -> Sin Toma
5. Para Punto_Muestreo_2020 a Punto_Muestreo_2025:
      vacío / #N/D -> Sin Dato
6. Conserva campos de compatibilidad usados por el tablero actual.
7. Conserva Latitud_X, Longitud_Y e Img_bocatoma desde el IRCAS.csv anterior.
8. Crea backup automático y reportes de control.

Uso recomendado desde PowerShell
--------------------------------
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
& "C:\Users\Javier\miniconda3\envs\analitica\python.exe" `
  "scripts\ircas\generar_ircas_desde_base_acueductos.py"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


ANIOS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]

# Valores que se consideran vacíos en la fuente.
VALORES_VACIOS = {
    "",
    "NAN",
    "NONE",
    "NULL",
    "NA",
    "N/A",
    "#N/A",
    "#N/D",
    "N/D",
    "ND",
    "NO APLICA",
    "NO APLICA.",
    "SIN INFORMACION",
    "SIN INFORMACIÓN",
}

# Columnas finales. Incluye estructura nueva + columnas de compatibilidad
# para que el HTML actual no se rompa mientras se ajusta el tablero a 2026.
COLUMNAS_IRCAS = [
    "No.",
    "CODIGO_ANTERIOR",
    "CODIGO_SISTEMA",
    "Latitud_X",
    "Longitud_Y",
    "MUNICIPIO",
    "TIPO",
    "CODIGO IVC2",
    "CODIGO MUESTREO",
    "CODIGO_AT",
    "ID_SSPD",
    "TIPO_SISTEMA_TRATAMIENTO",
    "TIPO_SISTEMA_TRATAMIENTO_AGRUPADO",
    "ALGUN_TIPO_TRATAMIENTO",
    "LOCALIDADES ABASTECIDAS",
    "NUMERO_LOCALIDADES",
    "ARO",
    "Persona Prestadora",
    "Forma_organizativa",
    "Registrados_SSPD",
    "SIVICAP_Registrados_SSPD",
    "SUSCRIPTORES",
    "POBLACION",

    # Último IRCA reportado general, independiente del año.
    "Ultimo_IRCA_reportado",
    "Nivel_Riesgo_ultimo_IRCA",
    "Fecha_Ultimo_IRCA_reportado",
    "Punto_Toma_Ultimo_IRCA",

    # Estructura anual nueva 2020-2026.
    "IRCA_2020",
    "Nivel_de_Riesgo_2020",
    "Fecha_Ultimo_IRCA_2020",
    "Punto_Muestreo_2020",

    "IRCA_2021",
    "Nivel_de_Riesgo_2021",
    "Fecha_Ultimo_IRCA_2021",
    "Punto_Muestreo_2021",

    "IRCA_2022",
    "Nivel_de_Riesgo_2022",
    "Fecha_Ultimo_IRCA_2022",
    "Punto_Muestreo_2022",

    "IRCA_2023",
    "Nivel_de_Riesgo_2023",
    "Fecha_Ultimo_IRCA_2023",
    "Punto_Muestreo_2023",

    "IRCA_2024",
    "Nivel_de_Riesgo_2024",
    "Fecha_Ultimo_IRCA_2024",
    "Punto_Muestreo_2024",

    "IRCA_2025",
    "Nivel_de_Riesgo_2025",
    "Fecha_Ultimo_IRCA_2025",
    "Punto_Muestreo_2025",

    "IRCA_2026",
    "Nivel_de_Riesgo_2026",
    "Fecha_Ultimo_IRCA_2026",
    "Punto_Toma_2026",

    "IRCA_Promedio",
    "Img_bocatoma",

    # Compatibilidad con ircas.html actual.
    "Nivel de Riesgo_2020",
    "Fecha ultimo IRCA_2020",
    "Nivel de Riesgo_2021",
    "Fecha ultimo IRCA_2021",
    "Nivel de Riesgo_2022",
    "Fecha ultimo IRCA_2022",
    "Nivel de Riesgo_2023",
    "FECHA_IRCA_2023",
    "Fecha_IRCA_2024",
    "Nivel_Riesgo_2025",
    "Punto_Toma_2025",
]

CAMPOS_COORDENADAS = ["Latitud_X", "Longitud_Y", "Img_bocatoma"]

# Mapeo base de campos administrativos.
MAPEO_ADMIN = {
    "No.": ["No."],
    "CODIGO_ANTERIOR": ["CODIGO_ANTERIOR"],
    "CODIGO_SISTEMA": ["CODIGO_SISTEMA"],
    "MUNICIPIO": ["MUNICIPIO"],
    "TIPO": ["TIPO", "TIPO\n"],
    "CODIGO IVC2": ["CODIGO IVC2"],
    "CODIGO MUESTREO": ["CODIGO MUESTREO"],
    "CODIGO_AT": ["CODIGO_AT"],
    "ID_SSPD": ["ID_SSPD"],
    "TIPO_SISTEMA_TRATAMIENTO": ["TIPO_SISTEMA_TRATAMIENTO"],
    "ALGUN_TIPO_TRATAMIENTO": ["ALGUN_TIPO_TRATAMIENTO"],
    "LOCALIDADES ABASTECIDAS": ["LOCALIDADES ABASTECIDAS"],
    "NUMERO_LOCALIDADES": ["NÚMERO_LOCALIDADES", "NUMERO_LOCALIDADES"],
    "ARO": ["ARO"],
    "Persona Prestadora": ["Persona Prestadora"],
    "Forma_organizativa": ["Forma_organizativa"],
    "Registrados_SSPD": ["Registrados_SSPD"],
    "SIVICAP_Registrados_SSPD": ["SIVICAP_Registrados_SSPD"],
    "SUSCRIPTORES": ["SUSCRIPTORES"],
    "POBLACION": ["POBLACION"],
}

# Fuente anual desde la hoja Acueductos.
# Nota: en el Excel actual pandas renombra columnas duplicadas como Ultimo_IRCA.1 y Punto_Toma.1.
MAPEO_ANUAL = {
    "2020": {
        "irca": ["IRCA_2020"],
        "riesgo": ["Nivel de Riesgo_2020", "Nivel_de_Riesgo_2020"],
        "fecha": ["Fecha ultimo IRCA_2020", "Fecha_Ultimo_IRCA_2020"],
        "punto": [],
        "tipo_punto": "muestreo",
    },
    "2021": {
        "irca": ["IRCA_2021"],
        "riesgo": ["Nivel de Riesgo_2021", "Nivel_de_Riesgo_2021"],
        "fecha": ["Fecha ultimo IRCA_2021", "Fecha_Ultimo_IRCA_2021"],
        "punto": [],
        "tipo_punto": "muestreo",
    },
    "2022": {
        "irca": ["IRCA_2022"],
        "riesgo": ["Nivel de Riesgo_2022", "Nivel_de_Riesgo_2022"],
        "fecha": ["Fecha ultimo IRCA_2022", "Fecha_Ultimo_IRCA_2022"],
        "punto": [],
        "tipo_punto": "muestreo",
    },
    "2023": {
        "irca": ["IRCA_Anterior_2023", "IRCA_2023"],
        "riesgo": ["Nivel de Riesgo_Anterior_2023", "Nivel_de_Riesgo_2023", "Nivel de Riesgo_2023"],
        "fecha": ["FECHA_IRCA_Anterior_2023", "Fecha_Ultimo_IRCA_2023", "FECHA_Ultimo_IRCA_2023"],
        "punto": [],
        "tipo_punto": "muestreo",
    },
    "2024": {
        "irca": ["IRCA_2024"],
        "riesgo": ["Nivel_de_Riesgo_2024", "Nivel de Riesgo_2024"],
        "fecha": ["Fecha_IRCA_2024", "Fecha_Ultimo_IRCA_2024"],
        "punto": ["Punto_Muestreo2", "Punto_Muestreo_2024"],
        "tipo_punto": "muestreo",
    },
    "2025": {
        "irca": ["IRCA_2025"],
        "riesgo": ["Nivel_de_Riesgo_2025", "Nivel_Riesgo_2025"],
        "fecha": ["Fecha_IRCA-2025", "Fecha_Ultimo_IRCA_2025"],
        "punto": ["Punto_Muestreo", "Punto_Muestreo_2025"],
        "tipo_punto": "muestreo",
    },
    "2026": {
        # No usar Ultimo_IRCA general como primera opción porque puede ser último de 2024/2025
        # en sistemas que aún no tienen muestra 2026.
        "irca": ["IRCA_2026", "Ultimo_IRCA_2026", "Ultimo_IRCA.1"],
        "riesgo": ["Nivel_de_Riesgo_2026", "Nivel_Riesgo_2026"],
        "fecha": ["Fecha_Ultimo_IRCA_2026"],
        "punto": ["Punto_Toma_2026", "Punto_Toma.1"],
        "tipo_punto": "toma",
    },
}


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def norm_header(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_accents(value: object) -> str:
    if value is None:
        return ""
    s = str(value)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def is_empty_value(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    s = str(value).strip()
    if s == "":
        return True
    s_norm = strip_accents(s).upper().strip()
    return s_norm in VALORES_VACIOS


def clean_text(value: object, upper: bool = True, remove_accents: bool = True) -> str:
    if is_empty_value(value):
        return ""
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)
    if remove_accents:
        s = strip_accents(s)
    if upper:
        s = s.upper()
    return s


def clean_numeric(value: object, decimals: int | None = None) -> str:
    if is_empty_value(value):
        return ""

    if isinstance(value, str):
        s = value.strip().replace("%", "")
        if is_empty_value(s):
            return ""
        # Normaliza decimal colombiano.
        if re.match(r"^-?\d{1,3}(\.\d{3})+,\d+$", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        try:
            num = float(s)
        except ValueError:
            return ""
    else:
        try:
            num = float(value)
        except Exception:
            return ""

    if decimals is not None:
        return f"{num:.{decimals}f}"
    if abs(num - round(num)) < 1e-9:
        return str(int(round(num)))
    return f"{num:.6f}".rstrip("0").rstrip(".")


def clean_date(value: object) -> str:
    if is_empty_value(value):
        return ""
    dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return dt.strftime("%d/%m/%Y")


def clean_punto_toma(value: object) -> str:
    if is_empty_value(value):
        return "Sin Toma"
    return clean_text(value, upper=False, remove_accents=False)


def clean_punto_muestreo(value: object) -> str:
    if is_empty_value(value):
        return "Sin Dato"
    return clean_text(value, upper=False, remove_accents=False)


def agrupar_tipo_sistema_tratamiento(value: object) -> str:
    """Agrupa el tipo de sistema de tratamiento para filtros y analítica del tablero.

    Mantiene el valor original en TIPO_SISTEMA_TRATAMIENTO y genera una columna
    operativa TIPO_SISTEMA_TRATAMIENTO_AGRUPADO con categorías consolidadas.
    """
    if is_empty_value(value):
        return "Sin Dato"

    original = clean_text(value, upper=False, remove_accents=False)
    v = strip_accents(original).upper().strip()
    v = re.sub(r"\s+", " ", v)
    v_key = v.replace(" ", "").replace("_", "").replace("-", "")

    # Prioridad: combinaciones con soluciones individuales se consolidan en esa categoría.
    if "SOLUCIONESINDIVIDUALES" in v_key or "SOLUCIONINDIVIDUAL" in v_key:
        return "Soluciones_Individuales"

    if "POZO" in v_key:
        return "Pozo"

    if v_key in {"CONVENCIONALMODULAR", "CONVENCIONAL", "PLANTACONVENCIONAL"}:
        return "Convencional"

    if v_key in {"FD+DESINFECCION", "FILTRACIONCOMPACTA", "FILTRACION", "FILTRACIONCOMPACTA"}:
        return "Filtracion"

    if v_key == "FIME":
        return "FIME"

    if v_key == "NINGUNO":
        return "Ninguno"

    if v_key == "PLANTAMODULAR":
        return "Planta Modular"

    if v_key in {"SOLODESINFECCION", "DESINFECCION"}:
        return "Solo desinfección"

    return "Otro"


def normalize_risk(value: object) -> str:
    if is_empty_value(value):
        return ""
    s = clean_text(value, upper=True, remove_accents=True)
    replacements = {
        "SIN RIESGO": "SIN RIESGO",
        "BAJO": "BAJO",
        "MEDIO": "MEDIO",
        "ALTO": "ALTO",
        "INVIABLE SANITARIAMENTE": "INVIABLE SANITARIAMENTE",
        "INVIABLE": "INVIABLE SANITARIAMENTE",
        "INVIABLE SANITARIO": "INVIABLE SANITARIAMENTE",
    }
    return replacements.get(s, s)


def risk_from_irca(irca_value: object) -> str:
    s = clean_numeric(irca_value)
    if s == "":
        return ""
    try:
        n = float(s)
    except Exception:
        return ""
    if 0 <= n <= 5:
        return "SIN RIESGO"
    if 5 < n <= 14:
        return "BAJO"
    if 14 < n <= 35:
        return "MEDIO"
    if 35 < n <= 80:
        return "ALTO"
    if n > 80:
        return "INVIABLE SANITARIAMENTE"
    return ""


def normalize_yes_no(value: object) -> str:
    if is_empty_value(value):
        return ""
    s = clean_text(value, upper=True, remove_accents=True)
    if s in {"1", "SI", "S", "TRUE", "VERDADERO", "YES"}:
        return "Si"
    if s in {"0", "NO", "N", "FALSE", "FALSO"}:
        return "No"
    return s.title()


def normalize_tipo(value: object) -> str:
    s = clean_text(value, upper=True, remove_accents=True)
    if s == "CABECERA MUNICIPAL":
        return "URBANO"
    return s


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [norm_header(c) for c in df.columns]
    return df


def first_existing_column(df: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    normalized = {norm_header(c): c for c in df.columns}
    for alias in aliases:
        key = norm_header(alias)
        if key in normalized:
            return normalized[key]
    return None


def coalesce_from_aliases(df: pd.DataFrame, aliases: Iterable[str]) -> pd.Series:
    result = pd.Series([""] * len(df), index=df.index, dtype="object")
    for alias in aliases:
        col = first_existing_column(df, [alias])
        if not col:
            continue
        candidate = df[col]
        mask = result.map(is_empty_value) & ~candidate.map(is_empty_value)
        result.loc[mask] = candidate.loc[mask]
    return result


def read_csv_robusto(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            return pd.read_csv(path, sep=";", encoding=enc, dtype=str)
        except Exception:
            continue
    raise RuntimeError(f"No se pudo leer el CSV actual: {path}")


def build_key_no(value: object) -> str:
    return clean_numeric(value)


def build_key_codigo_municipio(codigo: object, municipio: object) -> str:
    return f"{clean_numeric(codigo)}|{clean_text(municipio, upper=True, remove_accents=True)}"


def fecha_year(value: object) -> str:
    if is_empty_value(value):
        return ""
    dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return str(dt.year)


def limpiar_admin(out: pd.DataFrame) -> pd.DataFrame:
    for col in ["No.", "CODIGO_ANTERIOR", "CODIGO_SISTEMA", "CODIGO IVC2", "CODIGO MUESTREO",
                "CODIGO_AT", "ID_SSPD", "NUMERO_LOCALIDADES", "Registrados_SSPD",
                "SIVICAP_Registrados_SSPD", "SUSCRIPTORES", "POBLACION"]:
        if col in out.columns:
            out[col] = out[col].map(clean_numeric)

    for col in ["MUNICIPIO", "ARO", "Persona Prestadora", "Forma_organizativa",
                "LOCALIDADES ABASTECIDAS", "TIPO_SISTEMA_TRATAMIENTO"]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: clean_text(x, upper=True, remove_accents=True))

    if "TIPO" in out.columns:
        out["TIPO"] = out["TIPO"].map(normalize_tipo)
    if "ALGUN_TIPO_TRATAMIENTO" in out.columns:
        out["ALGUN_TIPO_TRATAMIENTO"] = out["ALGUN_TIPO_TRATAMIENTO"].map(normalize_yes_no)

    if "TIPO_SISTEMA_TRATAMIENTO" in out.columns:
        out["TIPO_SISTEMA_TRATAMIENTO_AGRUPADO"] = out["TIPO_SISTEMA_TRATAMIENTO"].map(agrupar_tipo_sistema_tratamiento)
    else:
        out["TIPO_SISTEMA_TRATAMIENTO_AGRUPADO"] = "Sin Dato"

    return out


def construir_ircas(base: pd.DataFrame, actual: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = normalizar_columnas(base)

    # Elimina fila TOTAL.
    if "No." in base.columns:
        base = base[base["No."].astype(str).str.strip().str.upper() != "TOTAL"].copy()

    if first_existing_column(base, ["CODIGO_SISTEMA"]) is None:
        raise ValueError("La hoja Acueductos no contiene la columna CODIGO_SISTEMA.")

    out = pd.DataFrame(index=base.index)

    # Campos administrativos.
    for target, aliases in MAPEO_ADMIN.items():
        out[target] = coalesce_from_aliases(base, aliases)

    out = limpiar_admin(out)

    # Campos generales de último IRCA reportado.
    out["Ultimo_IRCA_reportado"] = coalesce_from_aliases(base, ["Ultimo_IRCA"]).map(lambda x: clean_numeric(x, decimals=2))
    out["Nivel_Riesgo_ultimo_IRCA"] = coalesce_from_aliases(base, ["Nivel_Riesgo"]).map(normalize_risk)
    out["Fecha_Ultimo_IRCA_reportado"] = coalesce_from_aliases(base, ["Fecha_Ultimo_IRCA"]).map(clean_date)
    out["Punto_Toma_Ultimo_IRCA"] = coalesce_from_aliases(base, ["Punto_Toma"]).map(clean_punto_toma)

    # Campos anuales.
    for year in ANIOS:
        cfg = MAPEO_ANUAL[year]

        irca_col = f"IRCA_{year}"
        riesgo_col = f"Nivel_de_Riesgo_{year}"
        fecha_col = f"Fecha_Ultimo_IRCA_{year}"
        if year == "2026":
            punto_col = "Punto_Toma_2026"
        else:
            punto_col = f"Punto_Muestreo_{year}"

        # Caso especial: si no hay columnas específicas 2026, se deriva desde último reportado
        # únicamente cuando la fecha del último reporte sea del año 2026.
        if year == "2026" and first_existing_column(base, cfg["irca"]) is None:
            fecha_general = coalesce_from_aliases(base, ["Fecha_Ultimo_IRCA"])
            mask_2026 = fecha_general.map(fecha_year).eq("2026")
            out[irca_col] = ""
            out.loc[mask_2026, irca_col] = coalesce_from_aliases(base, ["Ultimo_IRCA"]).loc[mask_2026]
            out[riesgo_col] = ""
            out.loc[mask_2026, riesgo_col] = coalesce_from_aliases(base, ["Nivel_Riesgo"]).loc[mask_2026]
            out[fecha_col] = ""
            out.loc[mask_2026, fecha_col] = fecha_general.loc[mask_2026]
            out[punto_col] = ""
            out.loc[mask_2026, punto_col] = coalesce_from_aliases(base, ["Punto_Toma"]).loc[mask_2026]
        else:
            out[irca_col] = coalesce_from_aliases(base, cfg["irca"])
            out[riesgo_col] = coalesce_from_aliases(base, cfg["riesgo"])
            out[fecha_col] = coalesce_from_aliases(base, cfg["fecha"])
            if cfg["punto"]:
                out[punto_col] = coalesce_from_aliases(base, cfg["punto"])
            else:
                out[punto_col] = ""

        out[irca_col] = out[irca_col].map(lambda x: clean_numeric(x, decimals=2))
        out[riesgo_col] = out[riesgo_col].map(normalize_risk)
        out[fecha_col] = out[fecha_col].map(clean_date)

        # Si hay IRCA y no hay riesgo, calcula riesgo.
        mask_riesgo_vacio = out[riesgo_col].astype(str).str.strip().eq("") & out[irca_col].astype(str).str.strip().ne("")
        out.loc[mask_riesgo_vacio, riesgo_col] = out.loc[mask_riesgo_vacio, irca_col].map(risk_from_irca)

        if year == "2026":
            out[punto_col] = out[punto_col].map(clean_punto_toma)
        else:
            out[punto_col] = out[punto_col].map(clean_punto_muestreo)

    # Promedio con los años disponibles 2020-2026.
    irca_cols = [f"IRCA_{y}" for y in ANIOS]
    irca_nums = out[irca_cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    calc_prom = irca_nums.mean(axis=1, skipna=True).round(2)
    out["IRCA_Promedio"] = calc_prom.map(lambda x: "" if pd.isna(x) else f"{x:.2f}")

    # Coordenadas desde IRCAS actual.
    for c in CAMPOS_COORDENADAS:
        out[c] = ""

    control_rows = []
    if actual is not None and not actual.empty:
        actual = actual.copy()
        for c in ["No.", "CODIGO_SISTEMA", "MUNICIPIO"] + CAMPOS_COORDENADAS:
            if c not in actual.columns:
                actual[c] = ""

        actual["_KEY_NO"] = actual["No."].map(build_key_no)
        actual["_KEY_CM"] = actual.apply(lambda r: build_key_codigo_municipio(r.get("CODIGO_SISTEMA"), r.get("MUNICIPIO")), axis=1)
        out["_KEY_NO"] = out["No."].map(build_key_no)
        out["_KEY_CM"] = out.apply(lambda r: build_key_codigo_municipio(r.get("CODIGO_SISTEMA"), r.get("MUNICIPIO")), axis=1)

        actual_by_no = actual.drop_duplicates("_KEY_NO").set_index("_KEY_NO")
        actual_by_cm = actual.drop_duplicates("_KEY_CM").set_index("_KEY_CM")

        matched_no = 0
        matched_cm = 0
        unmatched = 0

        for idx, row in out.iterrows():
            key_no = row["_KEY_NO"]
            key_cm = row["_KEY_CM"]
            source_row = None
            source_type = ""

            if key_no and key_no in actual_by_no.index:
                source_row = actual_by_no.loc[key_no]
                source_type = "No."
                matched_no += 1
            elif key_cm and key_cm in actual_by_cm.index:
                source_row = actual_by_cm.loc[key_cm]
                source_type = "CODIGO_SISTEMA+MUNICIPIO"
                matched_cm += 1
            else:
                unmatched += 1

            if source_row is not None:
                out.at[idx, "Latitud_X"] = clean_numeric(source_row.get("Latitud_X", ""), decimals=6)
                out.at[idx, "Longitud_Y"] = clean_numeric(source_row.get("Longitud_Y", ""), decimals=6)
                out.at[idx, "Img_bocatoma"] = clean_text(source_row.get("Img_bocatoma", ""), upper=False, remove_accents=False)

            control_rows.append({
                "No.": row.get("No.", ""),
                "CODIGO_SISTEMA": row.get("CODIGO_SISTEMA", ""),
                "MUNICIPIO": row.get("MUNICIPIO", ""),
                "MATCH_COORDENADAS": source_type or "SIN_MATCH",
                "Latitud_X": out.at[idx, "Latitud_X"],
                "Longitud_Y": out.at[idx, "Longitud_Y"],
            })

        out = out.drop(columns=["_KEY_NO", "_KEY_CM"])
        control = pd.DataFrame(control_rows)
        control.attrs["matched_no"] = matched_no
        control.attrs["matched_cm"] = matched_cm
        control.attrs["unmatched"] = unmatched
    else:
        control = pd.DataFrame()

    # Compatibilidad con HTML actual.
    out["Nivel de Riesgo_2020"] = out["Nivel_de_Riesgo_2020"]
    out["Fecha ultimo IRCA_2020"] = out["Fecha_Ultimo_IRCA_2020"]
    out["Nivel de Riesgo_2021"] = out["Nivel_de_Riesgo_2021"]
    out["Fecha ultimo IRCA_2021"] = out["Fecha_Ultimo_IRCA_2021"]
    out["Nivel de Riesgo_2022"] = out["Nivel_de_Riesgo_2022"]
    out["Fecha ultimo IRCA_2022"] = out["Fecha_Ultimo_IRCA_2022"]
    out["Nivel de Riesgo_2023"] = out["Nivel_de_Riesgo_2023"]
    out["FECHA_IRCA_2023"] = out["Fecha_Ultimo_IRCA_2023"]
    out["Fecha_IRCA_2024"] = out["Fecha_Ultimo_IRCA_2024"]
    out["Nivel_Riesgo_2025"] = out["Nivel_de_Riesgo_2025"]
    out["Punto_Toma_2025"] = out["Punto_Muestreo_2025"]

    # Orden final.
    for c in COLUMNAS_IRCAS:
        if c not in out.columns:
            out[c] = ""
    out = out[COLUMNAS_IRCAS].fillna("")

    return out, control


def generar_reporte_control(out: pd.DataFrame, control: pd.DataFrame, ruta_reporte: Path) -> None:
    filas = []
    campos_criticos = [
        "No.", "CODIGO_SISTEMA", "MUNICIPIO", "ARO", "Persona Prestadora",
        "Latitud_X", "Longitud_Y", "IRCA_2025", "IRCA_2026",
        "Nivel_de_Riesgo_2025", "Nivel_de_Riesgo_2026",
        "Fecha_Ultimo_IRCA_2026", "Punto_Toma_2026", "IRCA_Promedio",
    ]

    for col in campos_criticos:
        if col not in out.columns:
            filas.append({"INDICADOR": f"Columna {col}", "VALOR": "NO EXISTE"})
        else:
            vacios = int(out[col].astype(str).str.strip().eq("").sum())
            filas.append({"INDICADOR": f"Vacíos en {col}", "VALOR": vacios})

    # Control de residuos #N/D.
    residuos_nd = 0
    for col in out.columns:
        residuos_nd += int(out[col].astype(str).str.strip().str.upper().isin({"#N/D", "#N/A", "N/D", "N/A"}).sum())

    filas.extend([
        {"INDICADOR": "Registros generados", "VALOR": len(out)},
        {"INDICADOR": "Códigos únicos", "VALOR": out["CODIGO_SISTEMA"].nunique(dropna=True)},
        {"INDICADOR": "Duplicados por No.", "VALOR": int(out.duplicated(["No."]).sum())},
        {"INDICADOR": "Duplicados por CODIGO_SISTEMA", "VALOR": int(out.duplicated(["CODIGO_SISTEMA"]).sum())},
        {"INDICADOR": "Residuos #N/D o #N/A en salida", "VALOR": residuos_nd},
    ])

    if control is not None and not control.empty:
        filas.extend([
            {"INDICADOR": "Coordenadas emparejadas por No.", "VALOR": control.attrs.get("matched_no", "")},
            {"INDICADOR": "Coordenadas emparejadas por CODIGO_SISTEMA+MUNICIPIO", "VALOR": control.attrs.get("matched_cm", "")},
            {"INDICADOR": "Registros sin match de coordenadas", "VALOR": control.attrs.get("unmatched", "")},
        ])

    reporte = pd.DataFrame(filas)
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.to_csv(ruta_reporte, index=False, sep=";", encoding="utf-8-sig")


def _compare_value(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def generar_reporte_actualizacion_2026(actual: pd.DataFrame, nuevo: pd.DataFrame, ruta_detalle: Path, ruta_resumen: Path) -> dict:
    """Compara la versión anterior vs la nueva, enfocándose en la información IRCA 2026."""
    columnas_base = ["No.", "CODIGO_SISTEMA", "MUNICIPIO", "Persona Prestadora"]
    columnas_2026 = ["IRCA_2026", "Nivel_de_Riesgo_2026", "Fecha_Ultimo_IRCA_2026", "Punto_Toma_2026"]
    columnas_2026_con_dato = ["IRCA_2026", "Nivel_de_Riesgo_2026", "Fecha_Ultimo_IRCA_2026"]

    if actual is None or actual.empty:
        detalle = nuevo.copy()
        for col in columnas_base + columnas_2026:
            if col not in detalle.columns:
                detalle[col] = ""
        detalle = detalle[columnas_base + columnas_2026].copy()
        for col in columnas_2026:
            detalle[f"{col}_ANTERIOR"] = ""
            detalle[f"{col}_NUEVO"] = detalle[col]
        detalle["ESTADO_ACTUALIZACION_2026"] = "SIN_VERSION_ANTERIOR"
        detalle["CAMPOS_CAMBIADOS_2026"] = "SIN_REFERENCIA_PREVIA"
        detalle.to_csv(ruta_detalle, index=False, sep=";", encoding="utf-8-sig")

        resumen = pd.DataFrame([
            {"INDICADOR": "Total registros nuevos", "VALOR": len(detalle)},
            {"INDICADOR": "Con IRCA_2026 reportado", "VALOR": int(detalle["IRCA_2026_NUEVO"].astype(str).str.strip().ne("").sum())},
            {"INDICADOR": "Estado", "VALOR": "SIN_VERSION_ANTERIOR"},
        ])
        resumen.to_csv(ruta_resumen, index=False, sep=";", encoding="utf-8-sig")
        return {"estado": "SIN_VERSION_ANTERIOR", "detalle": detalle, "resumen": resumen}

    a = actual.copy()
    n = nuevo.copy()

    for col in columnas_base + columnas_2026:
        if col not in a.columns:
            a[col] = ""
        if col not in n.columns:
            n[col] = ""

    a = a[columnas_base + columnas_2026].copy()
    n = n[columnas_base + columnas_2026].copy()

    # Usa CODIGO_SISTEMA como llave principal y conserva referencia descriptiva.
    a["_key"] = a["CODIGO_SISTEMA"].astype(str).str.strip()
    n["_key"] = n["CODIGO_SISTEMA"].astype(str).str.strip()
    a = a.sort_values(["_key", "No."]).drop_duplicates(subset=["_key"], keep="first")
    n = n.sort_values(["_key", "No."]).drop_duplicates(subset=["_key"], keep="first")

    a_ren = a.rename(columns={c: f"{c}_ANTERIOR" for c in columnas_base + columnas_2026 if c != "CODIGO_SISTEMA"} | {c: f"{c}_ANTERIOR" for c in columnas_2026})
    # Recupera llave y codigo para merge.
    a_ren["CODIGO_SISTEMA"] = a["CODIGO_SISTEMA"].values
    a_ren["_key"] = a["_key"].values

    detalle = n.merge(a_ren.drop(columns=["CODIGO_SISTEMA"]), on="_key", how="left")

    estados = []
    campos_changed = []
    for _, row in detalle.iterrows():
        diffs = []
        anterior_tiene_2026 = False
        nuevo_tiene_2026 = False
        for col in columnas_2026:
            v_ant = _compare_value(row.get(f"{col}_ANTERIOR", ""))
            v_new = _compare_value(row.get(col, ""))
            if col in columnas_2026_con_dato and v_ant != "":
                anterior_tiene_2026 = True
            if col in columnas_2026_con_dato and v_new != "":
                nuevo_tiene_2026 = True
            if v_ant != v_new:
                diffs.append(col)

        if not anterior_tiene_2026 and not nuevo_tiene_2026:
            estado = "SIN_2026_EN_AMBAS_VERSIONES"
        elif not anterior_tiene_2026 and nuevo_tiene_2026:
            estado = "SE_AGREGO_2026"
        elif anterior_tiene_2026 and not nuevo_tiene_2026:
            estado = "SE_ELIMINO_2026"
        elif diffs:
            estado = "SE_ACTUALIZO_2026"
        else:
            estado = "SIN_CAMBIO_2026"

        estados.append(estado)
        campos_changed.append(", ".join(diffs) if diffs else "")

    detalle["ESTADO_ACTUALIZACION_2026"] = estados
    detalle["CAMPOS_CAMBIADOS_2026"] = campos_changed

    # Renombra columnas nuevas para dejar claro el contraste.
    detalle = detalle.rename(columns={c: f"{c}_NUEVO" for c in columnas_2026})
    if "MUNICIPIO_ANTERIOR" not in detalle.columns:
        detalle["MUNICIPIO_ANTERIOR"] = ""
    if "Persona Prestadora_ANTERIOR" not in detalle.columns:
        detalle["Persona Prestadora_ANTERIOR"] = ""
    if "No._ANTERIOR" not in detalle.columns:
        detalle["No._ANTERIOR"] = ""

    columnas_salida = [
        "No.", "CODIGO_SISTEMA", "MUNICIPIO", "Persona Prestadora",
        "IRCA_2026_ANTERIOR", "IRCA_2026_NUEVO",
        "Nivel_de_Riesgo_2026_ANTERIOR", "Nivel_de_Riesgo_2026_NUEVO",
        "Fecha_Ultimo_IRCA_2026_ANTERIOR", "Fecha_Ultimo_IRCA_2026_NUEVO",
        "Punto_Toma_2026_ANTERIOR", "Punto_Toma_2026_NUEVO",
        "ESTADO_ACTUALIZACION_2026", "CAMPOS_CAMBIADOS_2026",
    ]
    for col in columnas_salida:
        if col not in detalle.columns:
            detalle[col] = ""
    detalle = detalle[columnas_salida].sort_values(["ESTADO_ACTUALIZACION_2026", "MUNICIPIO", "CODIGO_SISTEMA"], ascending=[True, True, True])
    detalle.to_csv(ruta_detalle, index=False, sep=";", encoding="utf-8-sig")

    resumen_rows = [
        {"INDICADOR": "Registros comparados", "VALOR": len(detalle)},
        {"INDICADOR": "SE_AGREGO_2026", "VALOR": int((detalle["ESTADO_ACTUALIZACION_2026"] == "SE_AGREGO_2026").sum())},
        {"INDICADOR": "SE_ACTUALIZO_2026", "VALOR": int((detalle["ESTADO_ACTUALIZACION_2026"] == "SE_ACTUALIZO_2026").sum())},
        {"INDICADOR": "SIN_CAMBIO_2026", "VALOR": int((detalle["ESTADO_ACTUALIZACION_2026"] == "SIN_CAMBIO_2026").sum())},
        {"INDICADOR": "SE_ELIMINO_2026", "VALOR": int((detalle["ESTADO_ACTUALIZACION_2026"] == "SE_ELIMINO_2026").sum())},
        {"INDICADOR": "SIN_2026_EN_AMBAS_VERSIONES", "VALOR": int((detalle["ESTADO_ACTUALIZACION_2026"] == "SIN_2026_EN_AMBAS_VERSIONES").sum())},
    ]
    resumen = pd.DataFrame(resumen_rows)
    resumen.to_csv(ruta_resumen, index=False, sep=";", encoding="utf-8-sig")
    return {"estado": "OK", "detalle": detalle, "resumen": resumen}


def generar_metadata_ircas(out: pd.DataFrame, comparacion: dict, ruta_metadata: Path, stamp: str, rutas_reportes: dict | None = None) -> dict:
    """Genera metadata estable para que el HTML muestre estado de carga y comparación de versiones."""
    rutas_reportes = rutas_reportes or {}
    vacios_coord = int((out["Latitud_X"].astype(str).str.strip().eq("") | out["Longitud_Y"].astype(str).str.strip().eq("")).sum())
    con_irca_2026 = int(out["IRCA_2026"].astype(str).str.strip().ne("").sum())
    sin_irca_2026 = int(out["IRCA_2026"].astype(str).str.strip().eq("").sum())
    con_irca_ultimo = int(out["Ultimo_IRCA_reportado"].astype(str).str.strip().ne("").sum())

    resumen_cmp = {}
    sistemas_cambiados = []
    if comparacion and comparacion.get("estado") == "OK":
        resumen_cmp = comparacion["resumen"].set_index("INDICADOR")["VALOR"].to_dict()
        cambios = comparacion["detalle"]
        cambios = cambios[cambios["ESTADO_ACTUALIZACION_2026"].isin(["SE_AGREGO_2026", "SE_ACTUALIZO_2026"])]
        for row in cambios[["CODIGO_SISTEMA", "MUNICIPIO", "Persona Prestadora", "IRCA_2026_NUEVO", "Nivel_de_Riesgo_2026_NUEVO"]].head(25).itertuples(index=False):
            sistemas_cambiados.append({
                "codigo_sistema": str(row.CODIGO_SISTEMA),
                "municipio": str(row.MUNICIPIO),
                "persona_prestadora": str(getattr(row, "_2", "")),
                "irca_2026": str(getattr(row, "IRCA_2026_NUEVO", "")),
                "nivel_riesgo_2026": str(getattr(row, "Nivel_de_Riesgo_2026_NUEVO", "")),
            })

    agregados = int(resumen_cmp.get("SE_AGREGO_2026", 0) or 0)
    actualizados = int(resumen_cmp.get("SE_ACTUALIZO_2026", 0) or 0)
    sin_cambio = int(resumen_cmp.get("SIN_CAMBIO_2026", 0) or 0)
    sin_2026 = int(resumen_cmp.get("SIN_2026_EN_AMBAS_VERSIONES", 0) or 0)
    eliminados = int(resumen_cmp.get("SE_ELIMINO_2026", 0) or 0)

    if agregados or actualizados:
        mensaje = f"Se incorporaron o actualizaron registros IRCA 2026 en {agregados + actualizados:,} sistemas.".replace(",", ".")
        detalle = f"Agregados: {agregados:,}; actualizados: {actualizados:,}; sin cambio: {sin_cambio:,}; sin dato 2026: {sin_2026:,}.".replace(",", ".")
    else:
        mensaje = "No se identificaron cambios en los registros IRCA 2026 frente a la versión anterior."
        detalle = f"Sin cambio: {sin_cambio:,}; sin dato 2026: {sin_2026:,}; eliminados: {eliminados:,}.".replace(",", ".")

    metadata = {
        "version_procesamiento": "IRCA_2020_2026_V4_METADATA",
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "stamp": stamp,
        "archivo_salida": "data/ircas/current/IRCAS.csv",
        "registros_generados": int(len(out)),
        "registros_con_ultimo_irca_reportado": con_irca_ultimo,
        "registros_con_irca_2026": con_irca_2026,
        "registros_sin_irca_2026": sin_irca_2026,
        "registros_sin_coordenadas_completas": vacios_coord,
        "comparacion_2026": {
            "se_agrego_2026": agregados,
            "se_actualizo_2026": actualizados,
            "sin_cambio_2026": sin_cambio,
            "sin_2026_en_ambas_versiones": sin_2026,
            "se_elimino_2026": eliminados,
            "mensaje": mensaje,
            "detalle": detalle,
            "sistemas_cambiados_muestra": sistemas_cambiados,
        },
        "reportes": rutas_reportes,
    }

    ruta_metadata.parent.mkdir(parents=True, exist_ok=True)
    ruta_metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def inferir_rutas(args: argparse.Namespace) -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    repo = Path(args.repo).resolve() if args.repo else None

    if repo is None:
        if script_path.parent.name.lower() == "ircas" and script_path.parent.parent.name.lower() == "scripts":
            repo = script_path.parent.parent.parent
        else:
            repo = Path.cwd().resolve()

    args.repo = repo
    args.base = Path(args.base).resolve() if args.base else repo / "data" / "ircas" / "input" / "Base_Datos_Acueductos_2026.xlsx"
    args.actual = Path(args.actual).resolve() if args.actual else repo / "data" / "ircas" / "current" / "IRCAS.csv"
    args.salida = Path(args.salida).resolve() if args.salida else repo / "data" / "ircas" / "current" / "IRCAS.csv"
    args.archive = Path(args.archive).resolve() if args.archive else repo / "data" / "ircas" / "archive"
    args.logs = Path(args.logs).resolve() if args.logs else repo / "data" / "ircas" / "logs"
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera IRCAS.csv desde Base_Datos_Acueductos_2026.xlsx")
    parser.add_argument("--repo", help="Ruta raíz del repositorio UESVALLE")
    parser.add_argument("--base", help="Ruta del archivo Base_Datos_Acueductos_2026.xlsx")
    parser.add_argument("--actual", help="Ruta del IRCAS.csv actual usado para conservar coordenadas")
    parser.add_argument("--salida", help="Ruta de salida del nuevo IRCAS.csv")
    parser.add_argument("--archive", help="Carpeta de backups")
    parser.add_argument("--logs", help="Carpeta de reportes de control")
    parser.add_argument("--hoja", default="Acueductos", help="Nombre de la hoja de entrada. Default: Acueductos")
    parser.add_argument("--sin-backup", action="store_true", help="No crear backup del IRCAS.csv anterior")
    args = inferir_rutas(parser.parse_args())

    log("UESVALLE - Generador IRCAS.csv 2020-2026")
    log(f"Repositorio : {args.repo}")
    log(f"Entrada    : {args.base}")
    log(f"Hoja       : {args.hoja}")
    log(f"Actual     : {args.actual}")
    log(f"Salida     : {args.salida}")

    if not args.base.exists():
        log("ERROR: No existe el archivo de entrada.")
        log("Ubica Base_Datos_Acueductos_2026.xlsx en data/ircas/input/ o usa --base.")
        return 1

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.archive.mkdir(parents=True, exist_ok=True)
    args.logs.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.actual.exists() and not args.sin_backup:
        backup = args.archive / f"IRCAS_backup_{stamp}.csv"
        shutil.copy2(args.actual, backup)
        log(f"Backup creado: {backup}")

    log("Leyendo hoja Acueductos...")
    base = pd.read_excel(args.base, sheet_name=args.hoja, dtype=object)
    log(f"Registros leídos incluyendo posibles totales: {len(base):,}")

    actual = read_csv_robusto(args.actual)
    if actual.empty:
        log("Advertencia: no se leyó IRCAS.csv actual. Coordenadas e Img_bocatoma quedarán vacíos si no están en la base.")
    else:
        log(f"IRCAS actual leído para conservar coordenadas: {len(actual):,} registros")

    out, control = construir_ircas(base, actual)
    log(f"Registros generados: {len(out):,}")

    reporte_resumen = args.logs / f"control_generacion_ircas_{stamp}.csv"
    generar_reporte_control(out, control, reporte_resumen)
    log(f"Reporte resumen: {reporte_resumen}")

    if control is not None and not control.empty:
        reporte_coord = args.logs / f"control_coordenadas_ircas_{stamp}.csv"
        control.to_csv(reporte_coord, index=False, sep=";", encoding="utf-8-sig")
        log(f"Reporte coordenadas: {reporte_coord}")

    reporte_actualizacion_det = args.logs / f"comparacion_actualizacion_irca_2026_detalle_{stamp}.csv"
    reporte_actualizacion_res = args.logs / f"comparacion_actualizacion_irca_2026_resumen_{stamp}.csv"
    comparacion = generar_reporte_actualizacion_2026(actual, out, reporte_actualizacion_det, reporte_actualizacion_res)
    log(f"Reporte comparación 2026 (detalle): {reporte_actualizacion_det}")
    log(f"Reporte comparación 2026 (resumen): {reporte_actualizacion_res}")

    if comparacion.get("estado") == "OK":
        resumen_cmp = comparacion["resumen"].set_index("INDICADOR")["VALOR"].to_dict()
        agregados_2026 = int(resumen_cmp.get("SE_AGREGO_2026", 0))
        actualizados_2026 = int(resumen_cmp.get("SE_ACTUALIZO_2026", 0))
        sin_cambio_2026 = int(resumen_cmp.get("SIN_CAMBIO_2026", 0))
        log(f"Comparación 2026: agregados = {agregados_2026}, actualizados = {actualizados_2026}, sin cambio = {sin_cambio_2026}")

        cambios = comparacion["detalle"]
        sistemas_cambiados = cambios[cambios["ESTADO_ACTUALIZACION_2026"].isin(["SE_AGREGO_2026", "SE_ACTUALIZO_2026"])][["CODIGO_SISTEMA", "MUNICIPIO"]].head(12)
        if not sistemas_cambiados.empty:
            lista = "; ".join([f"{r.CODIGO_SISTEMA} ({r.MUNICIPIO})" for r in sistemas_cambiados.itertuples(index=False)])
            log(f"Sistemas con actualización 2026 (primeros 12): {lista}")

    metadata_path = args.salida.parent / "metadata_ircas.json"
    metadata = generar_metadata_ircas(
        out,
        comparacion,
        metadata_path,
        stamp,
        rutas_reportes={
            "control_generacion": str(reporte_resumen),
            "control_coordenadas": str(reporte_coord) if control is not None and not control.empty else "",
            "comparacion_2026_detalle": str(reporte_actualizacion_det),
            "comparacion_2026_resumen": str(reporte_actualizacion_res),
        },
    )
    log(f"Metadata tablero IRCAS: {metadata_path}")
    log(f"Estado carga: {metadata['comparacion_2026']['mensaje']} {metadata['comparacion_2026']['detalle']}")

    out.to_csv(
        args.salida,
        index=False,
        sep=";",
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    vacios_coord = int((out["Latitud_X"].astype(str).str.strip().eq("") | out["Longitud_Y"].astype(str).str.strip().eq("")).sum())
    vacios_irca_2025 = int(out["IRCA_2025"].astype(str).str.strip().eq("").sum())
    vacios_irca_2026 = int(out["IRCA_2026"].astype(str).str.strip().eq("").sum())
    residuos_nd = 0
    for col in out.columns:
        residuos_nd += int(out[col].astype(str).str.strip().str.upper().isin({"#N/D", "#N/A", "N/D", "N/A"}).sum())

    log(f"OK: IRCAS.csv actualizado: {args.salida}")
    log(f"Control: registros sin coordenadas completas = {vacios_coord}")
    log(f"Control: registros sin IRCA_2025 = {vacios_irca_2025}")
    log(f"Control: registros sin IRCA_2026 = {vacios_irca_2026}")
    log(f"Control: residuos #N/D/#N/A en salida = {residuos_nd}")

    if len(out) == 0:
        log("ERROR: salida vacía. No es válido para el tablero.")
        return 2

    log("Proceso finalizado correctamente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"ERROR NO CONTROLADO: {exc}")
        raise
