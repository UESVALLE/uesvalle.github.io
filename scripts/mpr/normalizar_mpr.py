# -*- coding: utf-8 -*-
"""
Normalización tablero Mapas de Riesgo MPR - UESVALLE
Autor: ChatGPT + UESVALLE

Uso esperado desde la raíz del repositorio:
    python scripts/normalizar_mpr.py

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
# Si el script está en scripts/mpr, la raíz es parents[2].
# Si queda temporalmente en scripts, la raíz es parents[1].
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
    return s


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_upper(value) -> str:
    s = strip_accents(clean_text(value)).upper()
    return s


def normalize_code(value) -> str:
    """Convierte códigos tipo 115502.0, '115502 ', NaN en texto limpio."""
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
    s = re.sub(r"\.0$", "", s)
    return s.strip()


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


def standardize_activity(df: pd.DataFrame, actividad_default: str, fuente_archivo: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    # Garantizar columnas mínimas
    for col in [
        "ACTIVIDAD", "CODIGO ANTERIOR", "CODIGO_SISTEMA", "MUNICIPIO", "LOCALIDADES_ABASTECIDAS",
        "NOMBRE_SISTEMA", "PERSONA_PRESTADORA", "ARO", "NOMBRE_ARO", "FUNCIONARIO",
        "FEC_VISITA", "FECHA CARGUE", "ACTA", "CONSECUTIVO VISITA", "ESTADO", "OBSERVACION"
    ]:
        if col not in df.columns:
            df[col] = ""

    df["ACTIVIDAD"] = df["ACTIVIDAD"].replace("", np.nan).fillna(actividad_default).astype(str).str.strip()
    df["CODIGO_ANTERIOR"] = df["CODIGO ANTERIOR"].map(normalize_code)
    df["CODIGO_SISTEMA_LIMPIO"] = df["CODIGO_SISTEMA"].map(normalize_code)
    # Llave preferente: CODIGO ANTERIOR. Si viene vacío, usar CODIGO_SISTEMA como respaldo.
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
    # Agregar columnas extra si existen y son útiles para 1.5
    for extra in ["NUMERO_RESOLUCION", "AÑO", "CUENCA", "FUENTE", "RIESGO", "SE_EXPIDE", "SE_ACTUALIZA"]:
        if extra in df.columns and extra not in keep:
            keep.append(extra)
    return df[keep]


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
    print("="*100)
    print("NORMALIZACIÓN SEGUIMIENTO MAPAS DE RIESGO MPR - UESVALLE")
    print("="*100)
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

    print(f"Programados: {len(programados):,}")
    print(f"1.3 Visitas: {len(visitas13):,}")
    print(f"1.4 Muestreo: {len(muestreo14):,}")
    print(f"1.5 Resolución: {len(resol15):,} {'(opcional no cargado)' if resol15.empty else ''}")

    # Programados como universo base
    for col in ["ID", "ARO", "MUNICIPIO", "LOCALIDAD", "CODIGO ANTERIOR"]:
        if col not in programados.columns:
            programados[col] = ""

    base = programados.copy()
    base["CODIGO_LLAVE"] = base["CODIGO ANTERIOR"].map(normalize_code)
    base["ARO_PROGRAMADO"] = base["ARO"].map(normalize_upper)
    base["MUNICIPIO_PROGRAMADO"] = base["MUNICIPIO"].map(normalize_upper)
    base["LOCALIDAD_PROGRAMADA"] = base["LOCALIDAD"].map(clean_text)
    base["LOCALIDAD_PROGRAMADA_NORM"] = base["LOCALIDAD"].map(normalize_upper)

    # Actividades ejecutadas
    act13 = standardize_activity(visitas13, "1.3", "1.3_VisitasMPR.csv")
    act14 = standardize_activity(muestreo14, "1.4", "1.4_MuestreoMPR.csv")
    act15 = standardize_activity(resol15, "1.5", "1.5_ResolucionesMPR.csv") if not resol15.empty else pd.DataFrame()
    actividades = pd.concat([act13, act14, act15], ignore_index=True)

    # Enriquecer actividad con catálogo POA
    if not codigos.empty and "Código" in codigos.columns:
        cod = codigos.copy()
        cod["Código"] = cod["Código"].astype(str).str.strip()
        actividades = actividades.merge(cod, how="left", left_on="ACTIVIDAD", right_on="Código")
        # Catálogo MPR
        catalogo_mpr = cod[cod["Código"].isin(["1.3", "1.4", "1.5"])].copy()
    else:
        catalogo_mpr = pd.DataFrame({"Código":["1.3","1.4","1.5"], "Actividad_Resumen":["Visita MPR", "Muestreo MPR", "Resolución MPR"]})

    # Agregados por código
    a13 = agg_activity_flags(actividades, "1.3", "13")
    a14 = agg_activity_flags(actividades, "1.4", "14")
    a15 = agg_activity_flags(actividades, "1.5", "15")

    seguimiento = base.merge(a13, on="CODIGO_LLAVE", how="left").merge(a14, on="CODIGO_LLAVE", how="left").merge(a15, on="CODIGO_LLAVE", how="left")

    for p in ["13", "14", "15"]:
        if f"ejecuto_{p}" not in seguimiento.columns:
            seguimiento[f"ejecuto_{p}"] = "NO"
        seguimiento[f"ejecuto_{p}"] = seguimiento[f"ejecuto_{p}"].fillna("NO")
        for c in [f"registros_{p}"]:
            if c not in seguimiento.columns: seguimiento[c] = 0
            seguimiento[c] = pd.to_numeric(seguimiento[c], errors="coerce").fillna(0).astype(int)

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
    seguimiento["CODIGO_VALIDO"] = np.where(seguimiento["CODIGO_LLAVE"].eq(""), "NO", "SI")

    # Diferencia días 1.3 -> 1.4
    seguimiento["DIAS_13_A_14"] = (pd.to_datetime(seguimiento.get("fecha_14"), errors="coerce") - pd.to_datetime(seguimiento.get("fecha_13"), errors="coerce")).dt.days

    # Actividades no programadas
    cod_prog = set(seguimiento["CODIGO_LLAVE"].dropna().astype(str)) - {""}
    actividades["PROGRAMADO"] = np.where(actividades["CODIGO_LLAVE"].isin(cod_prog), "SI", "NO")

    # Alertas
    alertas = []
    for _, r in seguimiento.iterrows():
        if r["CODIGO_VALIDO"] == "NO":
            alertas.append({"TIPO_ALERTA":"PROGRAMADO SIN CODIGO", "CODIGO_LLAVE":"", "ARO":r.get("ARO_PROGRAMADO",""), "MUNICIPIO":r.get("MUNICIPIO_PROGRAMADO",""), "LOCALIDAD":r.get("LOCALIDAD_PROGRAMADA","")})
        if str(r["ESTADO_MPR"]).startswith("ALERTA") or r["ESTADO_MPR"] in ["SIN EJECUCIÓN", "PENDIENTE 1.4 MUESTREO", "PENDIENTE 1.5 RESOLUCIÓN"]:
            alertas.append({"TIPO_ALERTA":r["ESTADO_MPR"], "CODIGO_LLAVE":r.get("CODIGO_LLAVE",""), "ARO":r.get("ARO_PROGRAMADO",""), "MUNICIPIO":r.get("MUNICIPIO_PROGRAMADO",""), "LOCALIDAD":r.get("LOCALIDAD_PROGRAMADA","")})

    no_prog = actividades[(actividades["CODIGO_LLAVE"].astype(str).ne("")) & (~actividades["CODIGO_LLAVE"].isin(cod_prog))]
    for _, r in no_prog.iterrows():
        alertas.append({"TIPO_ALERTA":"EJECUTADO NO PROGRAMADO", "CODIGO_LLAVE":r.get("CODIGO_LLAVE",""), "ARO":r.get("ARO_NORM",""), "MUNICIPIO":r.get("MUNICIPIO_NORM",""), "LOCALIDAD":r.get("LOCALIDADES_ABASTECIDAS","")})

    # Duplicados por actividad/código
    if not actividades.empty:
        dup = actividades.groupby(["ACTIVIDAD", "CODIGO_LLAVE"], dropna=False).size().reset_index(name="REGISTROS")
        dup = dup[(dup["CODIGO_LLAVE"].astype(str).ne("")) & (dup["REGISTROS"] > 1)]
        for _, r in dup.iterrows():
            alertas.append({"TIPO_ALERTA":f"DUPLICADO ACTIVIDAD {r['ACTIVIDAD']}", "CODIGO_LLAVE":r["CODIGO_LLAVE"], "ARO":"", "MUNICIPIO":"", "LOCALIDAD":f"{int(r['REGISTROS'])} registros"})

    alertas_df = pd.DataFrame(alertas).drop_duplicates() if alertas else pd.DataFrame(columns=["TIPO_ALERTA","CODIGO_LLAVE","ARO","MUNICIPIO","LOCALIDAD"])

    # Resúmenes
    def summarize(group_cols):
        g = seguimiento.groupby(group_cols, dropna=False).agg(
            PROGRAMADOS=("CODIGO_LLAVE", "count"),
            CON_CODIGO_VALIDO=("CODIGO_VALIDO", lambda s: int((s == "SI").sum())),
            EJECUTADOS_13=("ejecuto_13", lambda s: int((s == "SI").sum())),
            EJECUTADOS_14=("ejecuto_14", lambda s: int((s == "SI").sum())),
            EJECUTADOS_15=("ejecuto_15", lambda s: int((s == "SI").sum())),
            COMPLETOS_13_14=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.5 RESOLUCIÓN").sum() + (s == "COMPLETO 1.3 + 1.4 + 1.5").sum())),
            SIN_EJECUCION=("ESTADO_MPR", lambda s: int((s == "SIN EJECUCIÓN").sum())),
            PENDIENTE_14=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.4 MUESTREO").sum())),
            PENDIENTE_15=("ESTADO_MPR", lambda s: int((s == "PENDIENTE 1.5 RESOLUCIÓN").sum())),
            ALERTAS=("ESTADO_MPR", lambda s: int(s.astype(str).str.startswith("ALERTA").sum())),
        ).reset_index()
        g["AVANCE_13_PCT"] = (g["EJECUTADOS_13"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        g["AVANCE_14_PCT"] = (g["EJECUTADOS_14"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        g["AVANCE_CICLO_13_14_PCT"] = (g["COMPLETOS_13_14"] / g["PROGRAMADOS"].replace(0, np.nan) * 100).round(1)
        return g.fillna(0)

    resumen_aro = summarize(["ARO_PROGRAMADO"])
    resumen_municipio = summarize(["ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO"])

    # Orden columnas tabla maestra
    ordered_cols = [
        "ID", "ARO_PROGRAMADO", "MUNICIPIO_PROGRAMADO", "LOCALIDAD_PROGRAMADA", "CODIGO_LLAVE", "CODIGO_VALIDO",
        "ejecuto_13", "fecha_13", "funcionario_13", "acta_13", "registros_13",
        "ejecuto_14", "fecha_14", "funcionario_14", "acta_14", "registros_14",
        "ejecuto_15", "fecha_15", "funcionario_15", "acta_15", "registros_15",
        "DIAS_13_A_14", "ESTADO_MPR", "PROGRAMADO"
    ]
    for c in ordered_cols:
        if c not in seguimiento.columns:
            seguimiento[c] = ""
    seguimiento_out = seguimiento[ordered_cols].copy()

    # Exportar fechas como YYYY-MM-DD
    for df in [seguimiento_out, actividades, resumen_aro, resumen_municipio, alertas_df, catalogo_mpr]:
        for col in df.columns:
            if "fecha" in col.lower() or col in ["FECHA_ACTIVIDAD", "FECHA_CARGUE_DT"]:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
                except Exception:
                    pass

    # Guardar histórico con timestamp y current
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hist_run = HIST_DIR / stamp
    hist_run.mkdir(parents=True, exist_ok=True)

    outputs = {
        "seguimiento_mpr_sistemas.csv": seguimiento_out,
        "actividades_mpr_ejecutadas.csv": actividades,
        "resumen_mpr_aro.csv": resumen_aro,
        "resumen_mpr_municipio.csv": resumen_municipio,
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
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "raw_dir": str(RAW_DIR),
        "out_dir": str(OUT_DIR),
        "programados": int(len(programados)),
        "actividades_ejecutadas": int(len(actividades)),
        "visitas_13": int(len(act13)),
        "muestreo_14": int(len(act14)),
        "resolucion_15": int(len(act15)) if not act15.empty else 0,
        "programados_con_codigo": int((seguimiento_out["CODIGO_VALIDO"] == "SI").sum()),
        "ejecutados_13": int((seguimiento_out["ejecuto_13"] == "SI").sum()),
        "ejecutados_14": int((seguimiento_out["ejecuto_14"] == "SI").sum()),
        "ejecutados_15": int((seguimiento_out["ejecuto_15"] == "SI").sum()),
        "salidas": list(outputs.keys()),
    }
    (OUT_DIR / "metadata_mpr.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (hist_run / "metadata_mpr.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] metadata_mpr.json")
    print("="*100)
    print("Proceso finalizado.")


if __name__ == "__main__":
    main()
