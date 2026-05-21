# -*- coding: utf-8 -*-
"""
Normalización tablero Mapas de Riesgo MPR - UESVALLE
Versión V1.3

Uso esperado desde la raíz del repositorio:
    python scripts/mpr/normalizar_mpr.py

Entradas esperadas:
    data/mpr/raw/Programados.csv
    data/mpr/raw/1.3_VisitasMPR.csv
    data/mpr/raw/1.4_MuestreoMPR.csv
    data/mpr/raw/Codigos_poa.csv
    data/mpr/raw/1.5_ResolucionesMPR.csv  (opcional, cuando exista)

Salidas:
    data/mpr/current/seguimiento_mpr_sistemas.csv
    data/mpr/current/actividades_mpr_ejecutadas.csv
    data/mpr/current/resumen_mpr_aro.csv
    data/mpr/current/resumen_mpr_municipio.csv
    data/mpr/current/resumen_mpr_funcionario.csv
    data/mpr/current/alertas_mpr.csv
    data/mpr/current/catalogo_codigos_poa_mpr.csv
    data/mpr/current/metadata_mpr.json
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re
import unicodedata
import pandas as pd
import numpy as np

SCRIPT_PATH = Path(__file__).resolve()
if SCRIPT_PATH.parent.name.lower() == "mpr" and SCRIPT_PATH.parent.parent.name.lower() == "scripts":
    REPO_ROOT = SCRIPT_PATH.parents[2]
else:
    REPO_ROOT = SCRIPT_PATH.parents[1]

RAW_DIR = REPO_ROOT / "data" / "mpr" / "raw"
OUT_DIR = REPO_ROOT / "data" / "mpr" / "current"
HIST_DIR = REPO_ROOT / "data" / "mpr" / "historical"
OUT_DIR.mkdir(parents=True, exist_ok=True)
HIST_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "programados": RAW_DIR / "Programados.csv",
    "visitas_13": RAW_DIR / "1.3_VisitasMPR.csv",
    "muestreo_14": RAW_DIR / "1.4_MuestreoMPR.csv",
    "resolucion_15": RAW_DIR / "1.5_ResolucionesMPR.csv",
    "codigos_poa": RAW_DIR / "Codigos_poa.csv",
}


def read_csv_smart(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    last_error = None
    for enc in ["utf-8-sig", "latin1", "cp1252"]:
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc, dtype=str)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"No fue posible leer {path}: {last_error}")


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)
    if s.lower() in ["nan", "none", "null"]:
        return ""
    return s


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_upper(value) -> str:
    return strip_accents(clean_text(value)).upper()


def normalize_code(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    if s.lower() in ["nan", "none", "null"]:
        return ""
    s = s.replace(",", ".")
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except Exception:
        pass
    return re.sub(r"\.0$", "", s).strip()


def first_nonempty(series: pd.Series) -> str:
    for v in series:
        sv = clean_text(v)
        if sv:
            return sv
    return ""


def parse_dates(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    if df.empty:
        return None
    norm_map = {normalize_upper(c).replace("_", " "): c for c in df.columns}
    for cand in candidates:
        key = normalize_upper(cand).replace("_", " ")
        if key in norm_map:
            return norm_map[key]
    return None


def ensure_col(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        df[col] = ""


def same_person(a, b) -> str:
    aa, bb = normalize_upper(a), normalize_upper(b)
    if not aa or not bb:
        return "SIN DATO"
    return "SI" if aa == bb else "NO"


def standardize_activity(df: pd.DataFrame, actividad_default: str, fuente_archivo: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()

    # Garantizar columnas mínimas de SISA.
    for col in [
        "ACTIVIDAD", "CODIGO ANTERIOR", "CODIGO_ANTIGUO", "CODIGO_SISTEMA", "MUNICIPIO",
        "LOCALIDADES_ABASTECIDAS", "NOMBRE_SISTEMA", "PERSONA_PRESTADORA", "ARO", "NOMBRE_ARO",
        "FUNCIONARIO", "FEC_VISITA", "FECHA CARGUE", "ACTA", "CONSECUTIVO VISITA", "ESTADO", "OBSERVACION"
    ]:
        ensure_col(df, col)

    codigo_ant_col = find_col(df, ["CODIGO_ANTIGUO", "CODIGO ANTERIOR", "CODIGO_ANTERIOR", "CODIGO ANTIGUO"])
    codigo_sis_col = find_col(df, ["CODIGO_SISTEMA", "CODIGO SISTEMA", "CODIGO IVC", "CODIGO_IVC"])

    df["ACTIVIDAD"] = df["ACTIVIDAD"].replace("", np.nan).fillna(actividad_default).astype(str).str.strip()
    df["CODIGO_ANTERIOR"] = df[codigo_ant_col].map(normalize_code) if codigo_ant_col else ""
    df["CODIGO_SISTEMA_LIMPIO"] = df[codigo_sis_col].map(normalize_code) if codigo_sis_col else ""
    df["CODIGO_LLAVE"] = df["CODIGO_ANTERIOR"]
    df.loc[df["CODIGO_LLAVE"].eq(""), "CODIGO_LLAVE"] = df.loc[df["CODIGO_LLAVE"].eq(""), "CODIGO_SISTEMA_LIMPIO"]

    df["MUNICIPIO_NORM"] = df["MUNICIPIO"].map(normalize_upper)
    df["LOCALIDAD_NORM"] = df["LOCALIDADES_ABASTECIDAS"].map(normalize_upper)
    df["NOMBRE_SISTEMA_NORM"] = df["NOMBRE_SISTEMA"].map(normalize_upper)
    df["ARO_NORM"] = df["NOMBRE_ARO"].where(df["NOMBRE_ARO"].astype(str).str.strip().ne(""), df["ARO"])
    df["ARO_NORM"] = df["ARO_NORM"].map(normalize_upper)
    df["FECHA_ACTIVIDAD"] = parse_dates(df["FEC_VISITA"])
    df["FECHA_CARGUE_DT"] = parse_dates(df["FECHA CARGUE"])
    df["FUENTE_ARCHIVO"] = fuente_archivo

    keep = [
        "FUENTE_ARCHIVO", "ACTIVIDAD", "CODIGO_LLAVE", "CODIGO_ANTERIOR", "CODIGO_SISTEMA_LIMPIO",
        "MUNICIPIO", "MUNICIPIO_NORM", "LOCALIDADES_ABASTECIDAS", "LOCALIDAD_NORM", "NOMBRE_SISTEMA", "NOMBRE_SISTEMA_NORM",
        "PERSONA_PRESTADORA", "ARO", "NOMBRE_ARO", "ARO_NORM", "FUNCIONARIO", "FEC_VISITA", "FECHA_ACTIVIDAD",
        "FECHA CARGUE", "FECHA_CARGUE_DT", "ACTA", "CONSECUTIVO VISITA", "ESTADO", "OBSERVACION"
    ]
    for extra in ["NUMERO_RESOLUCION", "AÑO", "CUENCA", "FUENTE", "RIESGO", "SE_EXPIDE", "SE_ACTUALIZA"]:
        if extra in df.columns and extra not in keep:
            keep.append(extra)
    return df[keep]



STOPWORDS_MATCH = {
    "ACUEDUCTO", "ACUEDUCTOS", "ASOCIACION", "ASOCIADOS", "USUARIOS", "JUNTA", "ADMINISTRADORA",
    "COMUNITARIO", "COMUNITARIA", "RURAL", "VEREDA", "VEREDAS", "CORREGIMIENTO", "ESP", "E", "S",
    "P", "SAS", "SA", "DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "O", "PARA", "PARTE", "ALTA",
    "BAJA", "SISTEMA", "ETAPAS", "MUNICIPIO", "VALLE", "CAUCA", "EMPRESA", "SERVICIO", "SERVICIOS"
}


def normalize_match_text(value) -> str:
    """Texto simplificado para cruce por nombre/localidad/prestador."""
    s = normalize_upper(value)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    tokens = [t for t in s.split() if len(t) > 1 and t not in STOPWORDS_MATCH]
    return " ".join(tokens)


def similarity_score(a, b) -> float:
    """Puntaje robusto: secuencia, Jaccard y contención de tokens."""
    from difflib import SequenceMatcher

    aa = normalize_match_text(a)
    bb = normalize_match_text(b)
    if not aa or not bb:
        return 0.0

    seq = SequenceMatcher(None, aa, bb).ratio()
    ta, tb = set(aa.split()), set(bb.split())
    inter = len(ta & tb)
    union = max(1, len(ta | tb))
    jaccard = inter / union
    containment = max(inter / max(1, len(ta)), inter / max(1, len(tb)))
    return round(max(seq, jaccard, containment), 6)


def build_base_match_text(df: pd.DataFrame) -> pd.Series:
    """Combina localidad y prestador programado para el cruce textual."""
    localidad = df.get("LOCALIDAD_PROGRAMADA", pd.Series([""] * len(df))).fillna("").astype(str)
    prestador = df.get("PERSONA_PRESTADORA_PROGRAMADA", pd.Series([""] * len(df))).fillna("").astype(str)
    return (localidad + " " + prestador).map(normalize_match_text)


def build_activity_match_text(df: pd.DataFrame) -> pd.Series:
    """Combina localidad, nombre de sistema y prestador ejecutado para el cruce textual."""
    loc = df.get("LOCALIDADES_ABASTECIDAS", pd.Series([""] * len(df))).fillna("").astype(str)
    sistema = df.get("NOMBRE_SISTEMA", pd.Series([""] * len(df))).fillna("").astype(str)
    prestador = df.get("PERSONA_PRESTADORA", pd.Series([""] * len(df))).fillna("").astype(str)
    return (loc + " " + sistema + " " + prestador).map(normalize_match_text)


def apply_programmed_crosswalk(actividades: pd.DataFrame, base: pd.DataFrame, threshold: float = 0.45) -> pd.DataFrame:
    """
    Cruza actividades ejecutadas contra programados.

    Prioridad:
    1) Cruce exacto por código.
    2) Si el código SISA no coincide con CODIGO_ANTIGUO, cruce textual por municipio + localidad/sistema/prestador.

    Esto es necesario porque SISA puede exportar CODIGO_SISTEMA nuevo, mientras la programación usa CODIGO_ANTIGUO.
    """
    if actividades.empty:
        return actividades

    acts = actividades.copy()

    prog = base.copy()
    if "CODIGO_PROGRAMADO_ORIGINAL" not in prog.columns:
        prog["CODIGO_PROGRAMADO_ORIGINAL"] = prog["CODIGO_LLAVE"].map(normalize_code)

    prog["__MUN_MATCH__"] = prog["MUNICIPIO_PROGRAMADO"].map(normalize_upper)
    prog["__TXT_MATCH__"] = build_base_match_text(prog)

    # Índice por código programado original.
    prog_code_lookup = {}
    for _, p in prog.iterrows():
        code = normalize_code(p.get("CODIGO_PROGRAMADO_ORIGINAL", ""))
        if code:
            prog_code_lookup[code] = p

    # Candidatos por municipio para cruce textual.
    prog_by_mun = {m: g.copy() for m, g in prog.groupby("__MUN_MATCH__", dropna=False)}

    acts["CODIGO_SISA_ORIGINAL"] = acts["CODIGO_LLAVE"].map(normalize_code)
    acts["CODIGO_PROGRAMADO_CRUCE"] = ""
    acts["TIPO_CRUCE_MPR"] = "SIN_CRUCE"
    acts["PUNTAJE_CRUCE_MPR"] = 0.0

    acts["__MUN_MATCH__"] = acts["MUNICIPIO"].map(normalize_upper)
    acts["__TXT_MATCH__"] = build_activity_match_text(acts)

    for idx, r in acts.iterrows():
        sisa_code = normalize_code(r.get("CODIGO_SISA_ORIGINAL", ""))

        # 1. Código exacto.
        if sisa_code and sisa_code in prog_code_lookup:
            p = prog_code_lookup[sisa_code]
            acts.at[idx, "CODIGO_PROGRAMADO_CRUCE"] = p.get("CODIGO_LLAVE", "")
            acts.at[idx, "CODIGO_LLAVE"] = p.get("CODIGO_LLAVE", "")
            acts.at[idx, "TIPO_CRUCE_MPR"] = "CODIGO"
            acts.at[idx, "PUNTAJE_CRUCE_MPR"] = 1.0
            continue

        # 2. Fallback textual.
        mun = r.get("__MUN_MATCH__", "")
        cands = prog_by_mun.get(mun, pd.DataFrame())
        if cands.empty:
            continue

        best_score = 0.0
        best_row = None
        act_text = r.get("__TXT_MATCH__", "")
        for _, p in cands.iterrows():
            score = similarity_score(act_text, p.get("__TXT_MATCH__", ""))
            if score > best_score:
                best_score = score
                best_row = p

        if best_row is not None and best_score >= threshold:
            acts.at[idx, "CODIGO_PROGRAMADO_CRUCE"] = best_row.get("CODIGO_LLAVE", "")
            acts.at[idx, "CODIGO_LLAVE"] = best_row.get("CODIGO_LLAVE", "")
            acts.at[idx, "TIPO_CRUCE_MPR"] = "TEXTO"
            acts.at[idx, "PUNTAJE_CRUCE_MPR"] = best_score

    acts = acts.drop(columns=["__MUN_MATCH__", "__TXT_MATCH__"], errors="ignore")
    return acts


def agg_activity_flags(acts: pd.DataFrame, code: str, prefix: str) -> pd.DataFrame:
    cols = ["CODIGO_LLAVE", f"ejecuto_{prefix}", f"fecha_{prefix}", f"funcionario_{prefix}", f"acta_{prefix}", f"registros_{prefix}"]
    if acts.empty or "ACTIVIDAD" not in acts.columns:
        return pd.DataFrame(columns=cols)
    sub = acts[acts["ACTIVIDAD"].astype(str).str.strip().eq(code)].copy()
    if sub.empty:
        return pd.DataFrame(columns=cols)
    g = sub.groupby("CODIGO_LLAVE", dropna=False).agg(
        **{
            f"ejecuto_{prefix}": ("CODIGO_LLAVE", "size"),
            f"fecha_{prefix}": ("FECHA_ACTIVIDAD", "min"),
            f"funcionario_{prefix}": ("FUNCIONARIO", first_nonempty),
            f"acta_{prefix}": ("ACTA", first_nonempty),
            f"registros_{prefix}": ("CODIGO_LLAVE", "size"),
        }
    ).reset_index()
    g[f"ejecuto_{prefix}"] = np.where(g[f"ejecuto_{prefix}"] > 0, "SI", "NO")
    return g


def main():
    print("=" * 100)
    print("NORMALIZACIÓN SEGUIMIENTO MAPAS DE RIESGO MPR - UESVALLE | V1.4")
    print("=" * 100)
    print(f"Repo raíz: {REPO_ROOT}")
    print(f"Entradas : {RAW_DIR}")
    print(f"Salidas  : {OUT_DIR}")

    print("\nVerificación de archivos de entrada:")
    for nombre, ruta in FILES.items():
        obligatorio = nombre in ["programados", "visitas_13", "muestreo_14", "codigos_poa"]
        estado = "OK" if ruta.exists() else ("FALTA OBLIGATORIO" if obligatorio else "No cargado opcional")
        print(f" - {nombre}: {estado} | {ruta}")

    programados = read_csv_smart(FILES["programados"])
    visitas13 = read_csv_smart(FILES["visitas_13"])
    muestreo14 = read_csv_smart(FILES["muestreo_14"])
    resol15 = read_csv_smart(FILES["resolucion_15"])
    codigos = read_csv_smart(FILES["codigos_poa"])

    print(f"Programados leídos: {len(programados):,}")
    print(f"Columnas Programados: {', '.join(programados.columns.astype(str)) if not programados.empty else 'SIN COLUMNAS'}")
    print(f"1.3 Visitas: {len(visitas13):,}")
    print(f"1.4 Muestreo: {len(muestreo14):,}")
    print(f"1.5 Resolución: {len(resol15):,} {'(opcional no cargado)' if resol15.empty else ''}")

    # Programados como universo base.
    base = programados.copy()
    for col in ["ID", "ARO", "MUNICIPIO", "LOCALIDAD"]:
        ensure_col(base, col)

    codigo_prog_col = find_col(base, ["CODIGO_ANTIGUO", "CODIGO ANTERIOR", "CODIGO_ANTERIOR", "CODIGO ANTIGUO"])
    func_prog_col = find_col(base, ["FUNCIONARIO", "FUNCIONARIO_PROGRAMADO", "INGENIERO", "INGENIERO_PROGRAMADO", "PROFESIONAL", "PROFESIONAL_PROGRAMADO", "RESPONSABLE", "RESPONSABLE_PROGRAMADO"])
    prestador_col = find_col(base, ["PERSONA_PRESTADORA", "PERSONA PRESTADORA", "PRESTADOR", "NOMBRE_PRESTADOR"])

    if codigo_prog_col is None:
        print("[ADVERTENCIA] No se encontró columna de código en Programados. Se esperaba CODIGO_ANTIGUO o CODIGO ANTERIOR.")
        base["__CODIGO_PROG__"] = ""
        codigo_prog_col = "__CODIGO_PROG__"
    if func_prog_col is None:
        print("[ADVERTENCIA] No se encontró columna de funcionario en Programados. Si ya actualizaste el archivo, verifica que tenga una columna llamada FUNCIONARIO.")
        base["__FUNCIONARIO_PROG__"] = ""
        func_prog_col = "__FUNCIONARIO_PROG__"
    if prestador_col is None:
        base["__PRESTADOR_PROG__"] = ""
        prestador_col = "__PRESTADOR_PROG__"

    base["CODIGO_PROGRAMADO_ORIGINAL"] = base[codigo_prog_col].map(normalize_code)
    base["FUNCIONARIO_PROGRAMADO"] = base[func_prog_col].map(clean_text)
    base["FUNCIONARIO_PROGRAMADO_NORM"] = base["FUNCIONARIO_PROGRAMADO"].map(normalize_upper)
    base["PERSONA_PRESTADORA_PROGRAMADA"] = base[prestador_col].map(clean_text)
    base["ARO_PROGRAMADO"] = base["ARO"].map(normalize_upper)
    base["MUNICIPIO_PROGRAMADO"] = base["MUNICIPIO"].map(normalize_upper)
    base["LOCALIDAD_PROGRAMADA"] = base["LOCALIDAD"].map(clean_text)
    base["LOCALIDAD_PROGRAMADA_NORM"] = base["LOCALIDAD"].map(normalize_upper)

    # Eliminar filas realmente vacías de Programados, usuales al final de exportaciones.
    # No se usa ID para esta validación, porque algunas filas vacías conservan consecutivo.
    before = len(base)
    campos_utiles_programacion = [
        "ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO", "LOCALIDAD_PROGRAMADA",
        "CODIGO_PROGRAMADO_ORIGINAL", "FUNCIONARIO_PROGRAMADO", "PERSONA_PRESTADORA_PROGRAMADA"
    ]
    base = base[
        base[campos_utiles_programacion].apply(lambda row: any(clean_text(x) for x in row), axis=1)
    ].copy()

    # CODIGO_LLAVE se usa como identificador interno. Si no hay código, se crea una llave sintética
    # para que la fila pueda mantenerse y eventualmente cruzarse por texto.
    base["CODIGO_LLAVE"] = base["CODIGO_PROGRAMADO_ORIGINAL"]
    base.loc[base["CODIGO_LLAVE"].eq(""), "CODIGO_LLAVE"] = base.loc[base["CODIGO_LLAVE"].eq("")].apply(
        lambda r: f"SIN_CODIGO_{normalize_upper(r.get('MUNICIPIO_PROGRAMADO',''))}_{normalize_upper(r.get('LOCALIDAD_PROGRAMADA',''))}"[:80],
        axis=1
    )

    print(f"Programados válidos después de limpieza: {len(base):,} (removidos {before-len(base):,})")
    print(f"Programados con funcionario: {(base['FUNCIONARIO_PROGRAMADO'].astype(str).str.strip().ne('')).sum():,}")

    # Actividades ejecutadas.
    act13 = standardize_activity(visitas13, "1.3", "1.3_VisitasMPR.csv")
    act14 = standardize_activity(muestreo14, "1.4", "1.4_MuestreoMPR.csv")
    act15 = standardize_activity(resol15, "1.5", "1.5_ResolucionesMPR.csv") if not resol15.empty else pd.DataFrame()
    actividades = pd.concat([act13, act14, act15], ignore_index=True)

    # Cruce programado vs ejecutado.
    # Primero intenta por código; si SISA usa un código distinto al CODIGO_ANTIGUO,
    # cruza por municipio + localidad/sistema/prestador.
    actividades = apply_programmed_crosswalk(actividades, base, threshold=0.45)

    # Enriquecer actividad con catálogo POA.
    if not codigos.empty and "Código" in codigos.columns:
        cod = codigos.copy()
        cod["Código"] = cod["Código"].astype(str).str.strip()
        actividades = actividades.merge(cod, how="left", left_on="ACTIVIDAD", right_on="Código")
        catalogo_mpr = cod[cod["Código"].isin(["1.3", "1.4", "1.5"])].copy()
    else:
        catalogo_mpr = pd.DataFrame({"Código": ["1.3", "1.4", "1.5"], "Actividad_Resumen": ["Visita MPR", "Muestreo MPR", "Resolución MPR"]})

    a13 = agg_activity_flags(actividades, "1.3", "13")
    a14 = agg_activity_flags(actividades, "1.4", "14")
    a15 = agg_activity_flags(actividades, "1.5", "15")

    seguimiento = base.merge(a13, on="CODIGO_LLAVE", how="left").merge(a14, on="CODIGO_LLAVE", how="left").merge(a15, on="CODIGO_LLAVE", how="left")

    for p in ["13", "14", "15"]:
        if f"ejecuto_{p}" not in seguimiento.columns:
            seguimiento[f"ejecuto_{p}"] = "NO"
        seguimiento[f"ejecuto_{p}"] = seguimiento[f"ejecuto_{p}"].fillna("NO")
        if f"registros_{p}" not in seguimiento.columns:
            seguimiento[f"registros_{p}"] = 0
        seguimiento[f"registros_{p}"] = pd.to_numeric(seguimiento[f"registros_{p}"], errors="coerce").fillna(0).astype(int)
        if f"funcionario_{p}" not in seguimiento.columns:
            seguimiento[f"funcionario_{p}"] = ""
        if f"fecha_{p}" not in seguimiento.columns:
            seguimiento[f"fecha_{p}"] = ""
        if f"acta_{p}" not in seguimiento.columns:
            seguimiento[f"acta_{p}"] = ""

    def estado(row):
        e13, e14, e15 = row["ejecuto_13"] == "SI", row["ejecuto_14"] == "SI", row["ejecuto_15"] == "SI"
        if e13 and e14 and e15:
            return "COMPLETO 1.3 + 1.4 + 1.5"
        if e13 and e14 and not e15:
            return "PENDIENTE 1.5 RESOLUCIÓN"
        if e13 and not e14 and not e15:
            return "PENDIENTE 1.4 MUESTREO"
        if not e13 and e14 and not e15:
            return "ALERTA: 1.4 SIN 1.3"
        if not e13 and not e14 and e15:
            return "ALERTA: 1.5 SIN 1.3/1.4"
        if e13 and not e14 and e15:
            return "ALERTA: 1.5 SIN 1.4"
        if not e13 and e14 and e15:
            return "ALERTA: 1.4/1.5 SIN 1.3"
        return "SIN EJECUCIÓN"

    seguimiento["ESTADO_MPR"] = seguimiento.apply(estado, axis=1)
    seguimiento["PROGRAMADO"] = "SI"
    seguimiento["CODIGO_VALIDO"] = np.where(seguimiento["CODIGO_PROGRAMADO_ORIGINAL"].astype(str).str.strip().eq(""), "NO", "SI")
    seguimiento["COINCIDE_FUNCIONARIO_13"] = seguimiento.apply(lambda r: same_person(r.get("FUNCIONARIO_PROGRAMADO", ""), r.get("funcionario_13", "")), axis=1)
    seguimiento["COINCIDE_FUNCIONARIO_14"] = seguimiento.apply(lambda r: same_person(r.get("FUNCIONARIO_PROGRAMADO", ""), r.get("funcionario_14", "")), axis=1)
    seguimiento["COINCIDE_FUNCIONARIO_15"] = seguimiento.apply(lambda r: same_person(r.get("FUNCIONARIO_PROGRAMADO", ""), r.get("funcionario_15", "")), axis=1)
    seguimiento["DIAS_13_A_14"] = (pd.to_datetime(seguimiento.get("fecha_14"), errors="coerce") - pd.to_datetime(seguimiento.get("fecha_13"), errors="coerce")).dt.days

    cod_prog = set(seguimiento["CODIGO_LLAVE"].dropna().astype(str)) - {""}
    if not actividades.empty:
        actividades["PROGRAMADO"] = np.where(actividades["CODIGO_LLAVE"].isin(cod_prog), "SI", "NO")
        prog_lookup = seguimiento[["CODIGO_LLAVE", "CODIGO_PROGRAMADO_ORIGINAL", "FUNCIONARIO_PROGRAMADO", "ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO", "LOCALIDAD_PROGRAMADA"]].drop_duplicates("CODIGO_LLAVE")
        actividades = actividades.merge(prog_lookup, on="CODIGO_LLAVE", how="left", suffixes=("", "_PROG"))
        actividades["COINCIDE_FUNCIONARIO_PROGRAMADO"] = actividades.apply(lambda r: same_person(r.get("FUNCIONARIO_PROGRAMADO", ""), r.get("FUNCIONARIO", "")), axis=1)
    else:
        actividades["PROGRAMADO"] = ""

    # Alertas.
    alertas = []
    for _, r in seguimiento.iterrows():
        base_alerta = {
            "CODIGO_LLAVE": r.get("CODIGO_LLAVE", ""),
            "ARO": r.get("ARO_PROGRAMADO", ""),
            "MUNICIPIO": r.get("MUNICIPIO_PROGRAMADO", ""),
            "LOCALIDAD": r.get("LOCALIDAD_PROGRAMADA", ""),
            "FUNCIONARIO_PROGRAMADO": r.get("FUNCIONARIO_PROGRAMADO", ""),
        }
        if r["CODIGO_VALIDO"] == "NO":
            alertas.append({"TIPO_ALERTA": "PROGRAMADO SIN CODIGO", **base_alerta})
        if str(r["FUNCIONARIO_PROGRAMADO"]).strip() == "":
            alertas.append({"TIPO_ALERTA": "PROGRAMADO SIN FUNCIONARIO", **base_alerta})
        if str(r["ESTADO_MPR"]).startswith("ALERTA") or r["ESTADO_MPR"] in ["SIN EJECUCIÓN", "PENDIENTE 1.4 MUESTREO", "PENDIENTE 1.5 RESOLUCIÓN"]:
            alertas.append({"TIPO_ALERTA": r["ESTADO_MPR"], **base_alerta})

    no_prog = actividades[(actividades.get("CODIGO_LLAVE", pd.Series(dtype=str)).astype(str).ne("")) & (~actividades.get("CODIGO_LLAVE", pd.Series(dtype=str)).isin(cod_prog))] if not actividades.empty else pd.DataFrame()
    for _, r in no_prog.iterrows():
        alertas.append({
            "TIPO_ALERTA": "EJECUTADO NO PROGRAMADO", "CODIGO_LLAVE": r.get("CODIGO_LLAVE", ""),
            "ARO": r.get("ARO_NORM", ""), "MUNICIPIO": r.get("MUNICIPIO_NORM", ""),
            "LOCALIDAD": r.get("LOCALIDADES_ABASTECIDAS", ""), "FUNCIONARIO_PROGRAMADO": ""
        })

    if not actividades.empty:
        dup = actividades.groupby(["ACTIVIDAD", "CODIGO_LLAVE"], dropna=False).size().reset_index(name="REGISTROS")
        dup = dup[(dup["CODIGO_LLAVE"].astype(str).ne("")) & (dup["REGISTROS"] > 1)]
        for _, r in dup.iterrows():
            alertas.append({"TIPO_ALERTA": f"DUPLICADO ACTIVIDAD {r['ACTIVIDAD']}", "CODIGO_LLAVE": r["CODIGO_LLAVE"], "ARO": "", "MUNICIPIO": "", "LOCALIDAD": f"{int(r['REGISTROS'])} registros", "FUNCIONARIO_PROGRAMADO": ""})

    alertas_df = pd.DataFrame(alertas).drop_duplicates() if alertas else pd.DataFrame(columns=["TIPO_ALERTA", "CODIGO_LLAVE", "ARO", "MUNICIPIO", "LOCALIDAD", "FUNCIONARIO_PROGRAMADO"])

    def summarize(group_cols):
        g = seguimiento.groupby(group_cols, dropna=False).agg(
            PROGRAMADOS=("CODIGO_LLAVE", "count"),
            CON_CODIGO_VALIDO=("CODIGO_VALIDO", lambda s: int((s == "SI").sum())),
            CON_FUNCIONARIO=("FUNCIONARIO_PROGRAMADO", lambda s: int(s.astype(str).str.strip().ne("").sum())),
            EJECUTADOS_13=("ejecuto_13", lambda s: int((s == "SI").sum())),
            EJECUTADOS_14=("ejecuto_14", lambda s: int((s == "SI").sum())),
            EJECUTADOS_15=("ejecuto_15", lambda s: int((s == "SI").sum())),
            COMPLETOS_13_14=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.5 RESOLUCIÓN").sum() + (s == "COMPLETO 1.3 + 1.4 + 1.5").sum())),
            SIN_EJECUCION=("ESTADO_MPR", lambda s: int((s == "SIN EJECUCIÓN").sum())),
            PENDIENTE_14=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.4 MUESTREO").sum())),
            PENDIENTE_15=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.5 RESOLUCIÓN").sum())),
            ALERTAS=("ESTADO_MPR", lambda s: int(s.astype(str).str.startswith("ALERTA").sum())),
            COINCIDE_13=("COINCIDE_FUNCIONARIO_13", lambda s: int((s == "SI").sum())),
            COINCIDE_14=("COINCIDE_FUNCIONARIO_14", lambda s: int((s == "SI").sum())),
        ).reset_index()
        g["AVANCE_13_PCT"] = (g["EJECUTADOS_13"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        g["AVANCE_14_PCT"] = (g["EJECUTADOS_14"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        g["AVANCE_CICLO_13_14_PCT"] = (g["COMPLETOS_13_14"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        return g.fillna(0)

    resumen_aro = summarize(["ARO_PROGRAMADO"])
    resumen_municipio = summarize(["ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO"])
    resumen_funcionario = summarize(["ARO_PROGRAMADO", "FUNCIONARIO_PROGRAMADO"])
    resumen_funcionario = resumen_funcionario.rename(columns={"FUNCIONARIO_PROGRAMADO": "FUNCIONARIO"})

    ordered_cols = [
        "ID", "ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO", "LOCALIDAD_PROGRAMADA", "CODIGO_PROGRAMADO_ORIGINAL", "CODIGO_LLAVE", "CODIGO_VALIDO",
        "FUNCIONARIO_PROGRAMADO", "PERSONA_PRESTADORA_PROGRAMADA",
        "ejecuto_13", "fecha_13", "funcionario_13", "acta_13", "registros_13", "COINCIDE_FUNCIONARIO_13",
        "ejecuto_14", "fecha_14", "funcionario_14", "acta_14", "registros_14", "COINCIDE_FUNCIONARIO_14",
        "ejecuto_15", "fecha_15", "funcionario_15", "acta_15", "registros_15", "COINCIDE_FUNCIONARIO_15",
        "DIAS_13_A_14", "ESTADO_MPR", "PROGRAMADO"
    ]
    for c in ordered_cols:
        if c not in seguimiento.columns:
            seguimiento[c] = ""
    seguimiento_out = seguimiento[ordered_cols].copy()

    # Exportar fechas como YYYY-MM-DD.
    for df in [seguimiento_out, actividades, resumen_aro, resumen_municipio, resumen_funcionario, alertas_df, catalogo_mpr]:
        for col in df.columns:
            if "fecha" in col.lower() or col in ["FECHA_ACTIVIDAD", "FECHA_CARGUE_DT"]:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d").fillna("")
                except Exception:
                    pass

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hist_run = HIST_DIR / stamp
    hist_run.mkdir(parents=True, exist_ok=True)

    outputs = {
        "seguimiento_mpr_sistemas.csv": seguimiento_out,
        "actividades_mpr_ejecutadas.csv": actividades,
        "resumen_mpr_aro.csv": resumen_aro,
        "resumen_mpr_municipio.csv": resumen_municipio,
        "resumen_mpr_funcionario.csv": resumen_funcionario,
        "alertas_mpr.csv": alertas_df,
        "catalogo_codigos_poa_mpr.csv": catalogo_mpr,
    }

    for name, df in outputs.items():
        current_path = OUT_DIR / name
        hist_path = hist_run / name
        df.to_csv(current_path, index=False, encoding="utf-8-sig")
        df.to_csv(hist_path, index=False, encoding="utf-8-sig")
        print(f"[OK] {name}: {len(df):,} registros")

    metadata = {
        "version_script": "V1.4",
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "raw_dir": str(RAW_DIR),
        "out_dir": str(OUT_DIR),
        "programados": int(len(base)),
        "programados_leidos": int(len(programados)),
        "programados_con_codigo": int((seguimiento_out["CODIGO_VALIDO"] == "SI").sum()),
        "programados_con_funcionario": int(seguimiento_out["FUNCIONARIO_PROGRAMADO"].astype(str).str.strip().ne("").sum()),
        "funcionarios_programados": int(seguimiento_out["FUNCIONARIO_PROGRAMADO"].replace("", np.nan).nunique(dropna=True)),
        "actividades_ejecutadas": int(len(actividades)),
        "actividades_cruzadas_codigo": int((actividades.get("TIPO_CRUCE_MPR", pd.Series(dtype=str)) == "CODIGO").sum()) if not actividades.empty else 0,
        "actividades_cruzadas_texto": int((actividades.get("TIPO_CRUCE_MPR", pd.Series(dtype=str)) == "TEXTO").sum()) if not actividades.empty else 0,
        "actividades_sin_cruce": int((actividades.get("TIPO_CRUCE_MPR", pd.Series(dtype=str)) == "SIN_CRUCE").sum()) if not actividades.empty else 0,
        "visitas_13": int(len(act13)),
        "muestreo_14": int(len(act14)),
        "resolucion_15": int(len(act15)) if not act15.empty else 0,
        "ejecutados_13": int((seguimiento_out["ejecuto_13"] == "SI").sum()),
        "ejecutados_14": int((seguimiento_out["ejecuto_14"] == "SI").sum()),
        "ejecutados_15": int((seguimiento_out["ejecuto_15"] == "SI").sum()),
        "salidas": list(outputs.keys()),
    }
    (OUT_DIR / "metadata_mpr.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (hist_run / "metadata_mpr.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] metadata_mpr.json")
    print("=" * 100)
    print("Proceso finalizado.")


if __name__ == "__main__":
    main()
