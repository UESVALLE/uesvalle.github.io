# -*- coding: utf-8 -*-
"""
ENRIQUECER SEGUIMIENTO DE MUESTRAS CON FICHAS DESCARGADAS - UESVALLE
Versión: V1
Fecha: 2026-05-27

Objetivo:
- Tomar el seguimiento semanal generado desde "Listado de Muestras Registradas".
- Cruzarlo con los archivos de fichas generados en Control_Descargas:
    muestras_fichas_CONSOLIDADO_lote_*.csv
- Agregar campos útiles para el tablero:
    MUNICIPIO
    PRESTADOR
    MUNICIPIO_PUNTO_MUESTREO
    PUNTO_MUESTREO
    LUGAR_TOMA_MUESTRA
    DIRECCION
    TIPO_LUGAR
    CORREGIMIENTO_VEREDA
    BARRIO
    TIPO_FUENTE
    NOMBRE_FUENTE
    NUMERO_ACTA
    TIPO_SERVICIO_FICHA

Salidas:
- Actualiza:
    data/resultados_agua/seguimiento_muestras/current/seguimiento_muestras_registradas_agua.csv
    data/resultados_agua/seguimiento_muestras/current/seguimiento_muestras_registradas_agua.xlsx
- Genera respaldo previo en:
    data/resultados_agua/seguimiento_muestras/archive/
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


PORTAL_ROOT = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

CONTROL_ROOT = Path(
    r"G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras\Control_Descargas"
)

CURRENT_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "seguimiento_muestras" / "current"
ARCHIVE_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "seguimiento_muestras" / "archive"

SEGUIMIENTO_CSV = CURRENT_DIR / "seguimiento_muestras_registradas_agua.csv"
SEGUIMIENTO_XLSX = CURRENT_DIR / "seguimiento_muestras_registradas_agua.xlsx"
METADATA_JSON = CURRENT_DIR / "metadata_seguimiento_muestras.json"

OUT_FICHAS_CONSOLIDADAS = CURRENT_DIR / "fichas_muestras_consolidadas_para_cruce.csv"
OUT_RESUMEN_CRUCE = CURRENT_DIR / "resumen_cruce_seguimiento_fichas.json"


def limpiar_texto(valor) -> str:
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor).strip())


def normalizar_codigo(valor) -> str:
    return limpiar_texto(valor).upper()


def extraer_run_lote(path: Path) -> str:
    """
    Extrae el identificador del lote desde una ruta tipo:
    Lote_20260526_2110/muestras_fichas_CONSOLIDADO_lote_20260526_2110.csv
    """
    txt = str(path)
    m = re.search(r"Lote_(\d{8}_\d{4,6})", txt, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"lote_(\d{8}_\d{4,6})", path.name, flags=re.IGNORECASE)
    return m.group(1) if m else ""


def leer_csv_robusto(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, dtype=str)


def seleccionar_col(df: pd.DataFrame, opciones: list[str]) -> str:
    cols_norm = {c.strip().upper(): c for c in df.columns}
    for op in opciones:
        key = op.strip().upper()
        if key in cols_norm:
            return cols_norm[key]
    return ""


def cargar_fichas() -> pd.DataFrame:
    archivos = sorted(CONTROL_ROOT.rglob("muestras_fichas_CONSOLIDADO_lote_*.csv"))

    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron archivos muestras_fichas_CONSOLIDADO_lote_*.csv en: {CONTROL_ROOT}"
        )

    print(f"[INFO] Archivos de fichas encontrados: {len(archivos)}")

    partes = []
    for path in archivos:
        try:
            df = leer_csv_robusto(path)
            df["ARCHIVO_FICHA"] = path.name
            df["LOTE_FICHA"] = extraer_run_lote(path)
            df["RUTA_ARCHIVO_FICHA"] = str(path)
            partes.append(df)
            print(f"  OK: {path.name} ({len(df):,} registros)".replace(",", "."))
        except Exception as e:
            print(f"  [ERROR] {path.name}: {e}")

    if not partes:
        raise RuntimeError("No fue posible leer archivos de fichas.")

    fichas = pd.concat(partes, ignore_index=True)

    col_codigo = seleccionar_col(fichas, ["Código Interno", "Codigo Interno", "CODIGO_INTERNO", "CODIGO_MUESTRA"])
    if not col_codigo:
        raise KeyError("No se encontró columna de código en fichas. Se esperaba 'Código Interno'.")

    fichas["CODIGO_MUESTRA"] = fichas[col_codigo].map(normalizar_codigo)

    # Campos propuestos para tablero y trazabilidad.
    mapping = {
        "TIPO_SERVICIO_FICHA": ["Tipo de servicio"],
        "FECHA_TOMA_MUESTRA": ["Fecha toma de muestra 1"],
        "NUMERO_ACTA": ["Número del acta", "Numero del acta"],
        "TIPO_MUESTRA": ["Tipo de muestra"],
        "PUNTO_MUESTREO": ["Punto de muestreo"],
        "LUGAR_TOMA_MUESTRA": ["Lugar toma de muestra"],
        "DIRECCION": ["Dirección", "Direccion"],
        "DEPARTAMENTO_PUNTO_MUESTREO": ["Departamento_punto_muestreo"],
        "MUNICIPIO_PUNTO_MUESTREO": ["Municipio_punto_muestreo"],
        "TIPO_LUGAR": ["Tipo de lugar"],
        "CORREGIMIENTO_VEREDA": ["Corregimiento / Vereda"],
        "BARRIO": ["Barrio"],
        "TIPO_FUENTE": ["Tipo de fuente"],
        "NOMBRE_FUENTE": ["Nombre de la fuente"],
        "DEPARTAMENTO_ACUEDUCTO": ["Departamento_acueducto"],
        "MUNICIPIO": ["Municipio_acueducto", "Municipio_punto_muestreo"],
        "TIPO_ENTIDAD_PRESTADOR": ["Tipo de entidad"],
        "PRESTADOR": ["Nombre del acueducto"],
        "TELEFONO_PRESTADOR": ["Teléfono", "Telefono"],
        "DIRECCION_PRESTADOR": ["Dirección_2", "Direccion_2"],
        "ENTIDAD_REMITE_FICHA": ["Nombre de la entidad que remite la muestra"],
        "MUESTRA_TOMADA_POR": ["Muestra tomada por"],
        "OBSERVACIONES_FICHA": ["Observaciones"],
        "FECHA_FILTRO_RECEPCION_FICHA": ["Fecha filtro (recepción)", "Fecha filtro recepcion"],
        "ARO_FICHA": ["ARO"],
    }

    out = pd.DataFrame()
    out["CODIGO_MUESTRA"] = fichas["CODIGO_MUESTRA"]

    for nuevo, opciones in mapping.items():
        col = seleccionar_col(fichas, opciones)
        out[nuevo] = fichas[col].map(limpiar_texto) if col else ""

    out["ARCHIVO_FICHA"] = fichas["ARCHIVO_FICHA"]
    out["LOTE_FICHA"] = fichas["LOTE_FICHA"]
    out["RUTA_ARCHIVO_FICHA"] = fichas["RUTA_ARCHIVO_FICHA"]

    out = out[out["CODIGO_MUESTRA"] != ""].copy()

    # Si un código aparece en varios lotes, nos quedamos con el último lote por nombre.
    out["_ORDEN_LOTE"] = out["LOTE_FICHA"].fillna("")
    out = (
        out.sort_values(["CODIGO_MUESTRA", "_ORDEN_LOTE"])
           .drop_duplicates(subset=["CODIGO_MUESTRA"], keep="last")
           .drop(columns=["_ORDEN_LOTE"])
    )

    return out


def main():
    inicio = datetime.now()
    run_id = inicio.strftime("%Y%m%d_%H%M%S")

    print("=" * 90)
    print("ENRIQUECER SEGUIMIENTO DE MUESTRAS CON FICHAS DESCARGADAS - UESVALLE")
    print("=" * 90)
    print(f"Portal:      {PORTAL_ROOT}")
    print(f"Control:     {CONTROL_ROOT}")
    print(f"Seguimiento: {SEGUIMIENTO_CSV}")
    print("=" * 90)

    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    if not SEGUIMIENTO_CSV.exists():
        raise FileNotFoundError(f"No existe el seguimiento actual: {SEGUIMIENTO_CSV}")

    print("\n1. Leyendo seguimiento actual...")
    seguimiento = leer_csv_robusto(SEGUIMIENTO_CSV)
    seguimiento["CODIGO_MUESTRA"] = seguimiento["CODIGO_MUESTRA"].map(normalizar_codigo)
    print(f"   Registros seguimiento: {len(seguimiento):,}".replace(",", "."))

    print("\n2. Leyendo fichas de Control_Descargas...")
    fichas = cargar_fichas()
    fichas.to_csv(OUT_FICHAS_CONSOLIDADAS, index=False, encoding="utf-8-sig")
    print(f"   Fichas únicas por código: {len(fichas):,}".replace(",", "."))
    print(f"   Consolidado fichas: {OUT_FICHAS_CONSOLIDADAS}")

    print("\n3. Generando backup del seguimiento actual...")
    backup_csv = ARCHIVE_DIR / f"seguimiento_muestras_registradas_agua_backup_antes_enriquecer_{run_id}.csv"
    backup_xlsx = ARCHIVE_DIR / f"seguimiento_muestras_registradas_agua_backup_antes_enriquecer_{run_id}.xlsx"

    seguimiento.to_csv(backup_csv, index=False, encoding="utf-8-sig")
    seguimiento.to_excel(backup_xlsx, index=False)
    print(f"   Backup CSV:  {backup_csv}")
    print(f"   Backup XLSX: {backup_xlsx}")

    print("\n4. Cruzando seguimiento con fichas por CODIGO_MUESTRA...")
    columnas_agregar = [c for c in fichas.columns if c != "CODIGO_MUESTRA"]

    # Evitar duplicar columnas si el seguimiento ya fue enriquecido antes.
    seguimiento_base = seguimiento.drop(columns=[c for c in columnas_agregar if c in seguimiento.columns], errors="ignore")

    enriquecido = seguimiento_base.merge(
        fichas,
        on="CODIGO_MUESTRA",
        how="left",
        indicator="MATCH_FICHA_TMP"
    )

    enriquecido["MATCH_FICHA"] = enriquecido["MATCH_FICHA_TMP"].map({
        "both": "SI",
        "left_only": "NO",
        "right_only": "NO",
    }).fillna("NO")
    enriquecido = enriquecido.drop(columns=["MATCH_FICHA_TMP"])

    total_match = int((enriquecido["MATCH_FICHA"] == "SI").sum())
    total_no = int((enriquecido["MATCH_FICHA"] != "SI").sum())

    print(f"   Con ficha: {total_match:,}".replace(",", "."))
    print(f"   Sin ficha: {total_no:,}".replace(",", "."))

    print("\n5. Guardando seguimiento enriquecido...")
    enriquecido.to_csv(SEGUIMIENTO_CSV, index=False, encoding="utf-8-sig")
    enriquecido.to_excel(SEGUIMIENTO_XLSX, index=False)

    # Actualiza metadata sin romper la estructura existente.
    metadata = {}
    if METADATA_JSON.exists():
        try:
            metadata = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

    metadata["enriquecimiento_fichas"] = {
        "fecha_enriquecimiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_id": run_id,
        "total_seguimiento": int(len(enriquecido)),
        "total_fichas_unicas": int(len(fichas)),
        "match_ficha_si": total_match,
        "match_ficha_no": total_no,
        "control_root": str(CONTROL_ROOT),
        "fichas_consolidadas": str(OUT_FICHAS_CONSOLIDADAS),
        "backup_csv": str(backup_csv),
        "backup_xlsx": str(backup_xlsx),
    }
    METADATA_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    resumen = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_id": run_id,
        "total_seguimiento": int(len(enriquecido)),
        "total_fichas_unicas": int(len(fichas)),
        "match_ficha_si": total_match,
        "match_ficha_no": total_no,
        "duracion_segundos": round((datetime.now() - inicio).total_seconds(), 2),
    }
    OUT_RESUMEN_CRUCE.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n==========================================================================================")
    print("PROCESO FINALIZADO")
    print("==========================================================================================")
    print(f"Seguimiento enriquecido CSV:  {SEGUIMIENTO_CSV}")
    print(f"Seguimiento enriquecido XLSX: {SEGUIMIENTO_XLSX}")
    print(f"Resumen cruce:                {OUT_RESUMEN_CRUCE}")
    print(f"Metadata actualizada:         {METADATA_JSON}")
    print(f"Duración segundos:            {resumen['duracion_segundos']}")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
