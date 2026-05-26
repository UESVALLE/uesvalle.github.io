# -*- coding: utf-8 -*-
"""
GENERAR INVENTARIO MANUAL DE RESULTADOS DE AGUA - UESVALLE
==========================================================

Lee archivos TXT copiados manualmente desde gestion-muestras.valledelcauca.gov.co/results
y genera CSV limpios para tablero, control de duplicados y descarga de PDFs.

Entrada esperada:
  scripts/resultados_agua/02_inventario_manual/
    - FECHAS CARTAGO.txt
    - FECHAS CALI.txt
    - FECHAS TULUA.txt

Salida:
  data/resultados_agua/current/
    - inventario_resultados_agua_bruto.csv
    - inventario_resultados_agua.csv
    - duplicados_inventario_resultados_agua.csv
    - resumen_fechas_resultados_agua.csv
    - resumen_resultados_agua.csv
    - metadata_resultados_agua.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PORTAL_ROOT = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

INPUT_DIR = PORTAL_ROOT / "scripts" / "resultados_agua" / "02_inventario_manual"
OUTPUT_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "current"
LOG_DIR = PORTAL_ROOT / "scripts" / "resultados_agua" / "logs"

ARCHIVOS_ENTRADA = {
    "Cartago": "FECHAS CARTAGO.txt",
    "Cali": "FECHAS CALI.txt",
    "Tulua": "FECHAS TULUA.txt",
}

COLUMNAS = [
    "Codigo",
    "Fecha_envio",
    "Fecha_recepcion",
    "Hora_recepcion",
    "Fecha_resultados",
    "Tipo",
    "Entidad_que_remite",
    "Muestras_recibidas",
    "Muestras_rechazadas",
    "Estado",
]

PATRON_CODIGO = re.compile(
    r"^\d{8}-\d{4}-(?:MR|VDM|VIG|DIAG|DSAN)(?:-C\d+)?$",
    flags=re.IGNORECASE,
)

PATRON_PAGINA = re.compile(r"^PAG\s*(\d+)$", flags=re.IGNORECASE)


# =============================================================================
# UTILIDADES
# =============================================================================

def limpiar_texto(valor: object) -> str:
    if valor is None:
        return ""
    txt = str(valor)
    txt = txt.replace("\ufeff", "")
    txt = txt.replace("\xa0", " ")
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def normalizar_aro(nombre: str) -> str:
    txt = limpiar_texto(nombre).lower()
    if "cartago" in txt:
        return "Cartago"
    if "cali" in txt:
        return "Cali"
    if "tulu" in txt or "tulua" in txt or "tuluá" in txt:
        return "Tulua"
    return limpiar_texto(nombre)


def detectar_tipo_codigo(codigo: str) -> str:
    codigo = limpiar_texto(codigo).upper()
    partes = codigo.split("-")
    if len(partes) >= 3:
        tipo = partes[2]
        if tipo in {"MR", "VDM", "VIG", "DIAG", "DSAN"}:
            return tipo
    return ""


def tipo_nombre(tipo: str) -> str:
    mapa = {
        "MR": "MAPAS DE RIESGOS",
        "VDM": "VIGILANCIA DE MAPAS",
        "VIG": "VIGILANCIA RUTINARIA",
        "DIAG": "APOYO DIAGNÓSTICO",
        "DSAN": "DIAGNÓSTICO SANITARIO",
    }
    return mapa.get(tipo, "")


def extraer_anio(codigo: str, fecha_recepcion: str = "") -> str:
    codigo = limpiar_texto(codigo)
    if re.match(r"^\d{8}-", codigo):
        return codigo[:4]
    fecha = limpiar_texto(fecha_recepcion)
    m = re.search(r"(\d{4})$", fecha)
    if m:
        return m.group(1)
    return ""


def parse_fecha_ddmmyyyy(fecha: str):
    fecha = limpiar_texto(fecha)
    if not fecha:
        return pd.NaT
    return pd.to_datetime(fecha, format="%d/%m/%Y", errors="coerce")


def log_lineas(log_path: Path, lineas: list[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        for linea in lineas:
            f.write(linea.rstrip() + "\n")


# =============================================================================
# PARSEO DE TXT MANUAL
# =============================================================================

def parsear_txt_manual(path_txt: Path, aro_nombre: str) -> pd.DataFrame:
    """
    Parsea un TXT copiado manualmente desde la tabla de resultados.

    Cada fila válida inicia con un código tipo:
      20260513-8324-VIG
      20250826-3979-VIG-C1

    Se esperan columnas separadas por tabulación. Si por alguna razón hay más
    columnas después de Estado, se ignoran como Acciones.
    """
    registros = []
    pagina_actual = None

    if not path_txt.exists():
        print(f"   [AVISO] No existe: {path_txt}")
        return pd.DataFrame(columns=COLUMNAS + ["ARO", "Pagina_manual", "Fila_archivo"])

    with path_txt.open("r", encoding="utf-8-sig", errors="replace") as f:
        lineas = f.readlines()

    for idx, linea in enumerate(lineas, start=1):
        linea_original = linea.rstrip("\n\r")
        linea_limpia = limpiar_texto(linea_original)

        if not linea_limpia:
            continue

        m_pag = PATRON_PAGINA.match(linea_limpia)
        if m_pag:
            pagina_actual = int(m_pag.group(1))
            continue

        # Saltar encabezados repetidos
        if linea_limpia.lower() in {
            "código",
            "codigo",
            "fecha de envío",
            "fecha de envio",
            "fecha de recepción",
            "fecha de recepcion",
            "hora de recepción",
            "hora de recepcion",
            "fecha de resultados",
            "tipo",
            "entidad que remite",
            "# muestras recibidas",
            "# muestras rechazadas",
            "estado",
            "acciones",
        }:
            continue

        # Solo procesar filas cuyo primer campo sea un código válido.
        partes_tab = [limpiar_texto(x) for x in linea_original.split("\t")]
        if not partes_tab:
            continue

        codigo = limpiar_texto(partes_tab[0])
        if not PATRON_CODIGO.match(codigo):
            continue

        # Completar campos faltantes.
        partes = partes_tab[:10]
        while len(partes) < 10:
            partes.append("")

        registro = dict(zip(COLUMNAS, partes))
        registro["ARO"] = aro_nombre
        registro["Pagina_manual"] = pagina_actual
        registro["Fila_archivo"] = idx
        registros.append(registro)

    df = pd.DataFrame(registros)
    if df.empty:
        return pd.DataFrame(columns=COLUMNAS + ["ARO", "Pagina_manual", "Fila_archivo"])

    return df


def enriquecer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        df[col] = df[col].map(limpiar_texto)

    df["ARO"] = df["ARO"].map(normalizar_aro)
    df["Tipo_servicio_codigo"] = df["Codigo"].map(detectar_tipo_codigo)
    df["Tipo_servicio_nombre"] = df["Tipo_servicio_codigo"].map(tipo_nombre)
    df["Anio"] = [
        extraer_anio(codigo, fecha)
        for codigo, fecha in zip(df["Codigo"], df["Fecha_recepcion"])
    ]

    df["Fecha_envio_dt"] = df["Fecha_envio"].map(parse_fecha_ddmmyyyy)
    df["Fecha_recepcion_dt"] = df["Fecha_recepcion"].map(parse_fecha_ddmmyyyy)
    df["Fecha_resultados_dt"] = df["Fecha_resultados"].map(parse_fecha_ddmmyyyy)

    df["Muestras_recibidas_num"] = pd.to_numeric(
        df["Muestras_recibidas"].str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["Muestras_rechazadas_num"] = pd.to_numeric(
        df["Muestras_rechazadas"].str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df["Clave_ARO_Codigo"] = df["ARO"] + "|" + df["Codigo"]
    df["Es_codigo_valido"] = df["Codigo"].map(lambda x: bool(PATRON_CODIGO.match(x)))

    # Orden sugerido para consulta y tablero
    orden = [
        "ARO",
        "Anio",
        "Tipo_servicio_codigo",
        "Tipo_servicio_nombre",
        "Codigo",
        "Fecha_envio",
        "Fecha_recepcion",
        "Hora_recepcion",
        "Fecha_resultados",
        "Tipo",
        "Entidad_que_remite",
        "Muestras_recibidas",
        "Muestras_rechazadas",
        "Estado",
        "Pagina_manual",
        "Fila_archivo",
        "Muestras_recibidas_num",
        "Muestras_rechazadas_num",
        "Clave_ARO_Codigo",
        "Es_codigo_valido",
    ]

    existentes = [c for c in orden if c in df.columns]
    restantes = [c for c in df.columns if c not in existentes]
    return df[existentes + restantes]


def construir_duplicados(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return pd.DataFrame()

    conteos = df_bruto.groupby(["ARO", "Codigo"], dropna=False).size().reset_index(name="Repeticiones")
    duplicados_keys = conteos[conteos["Repeticiones"] > 1][["ARO", "Codigo"]]

    if duplicados_keys.empty:
        return pd.DataFrame(columns=list(df_bruto.columns) + ["Repeticiones"])

    df_dup = df_bruto.merge(duplicados_keys, on=["ARO", "Codigo"], how="inner")
    df_dup = df_dup.merge(conteos, on=["ARO", "Codigo"], how="left")
    df_dup = df_dup.sort_values(["ARO", "Codigo", "Pagina_manual", "Fila_archivo"])
    return df_dup


def construir_unicos(df_bruto: pd.DataFrame) -> pd.DataFrame:
    if df_bruto.empty:
        return df_bruto.copy()

    df = df_bruto.copy()
    # Conserva la primera ocurrencia según el orden de copiado manual.
    df = df.sort_values(["ARO", "Fila_archivo"])
    df["Es_duplicado_por_codigo"] = df.duplicated(subset=["ARO", "Codigo"], keep="first")
    df_unico = df[~df["Es_duplicado_por_codigo"]].copy()
    return df_unico


def construir_resumen_fechas(df_unico: pd.DataFrame) -> pd.DataFrame:
    if df_unico.empty:
        return pd.DataFrame()

    resumen = (
        df_unico
        .groupby(["ARO", "Anio", "Fecha_recepcion", "Tipo_servicio_codigo"], dropna=False)
        .agg(
            Total_codigos=("Codigo", "count"),
            Muestras_recibidas_total=("Muestras_recibidas_num", "sum"),
            Muestras_rechazadas_total=("Muestras_rechazadas_num", "sum"),
            Fecha_resultados_min=("Fecha_resultados", "min"),
            Fecha_resultados_max=("Fecha_resultados", "max"),
        )
        .reset_index()
    )

    resumen["Fecha_recepcion_dt"] = resumen["Fecha_recepcion"].map(parse_fecha_ddmmyyyy)
    resumen = resumen.sort_values(["ARO", "Fecha_recepcion_dt", "Tipo_servicio_codigo"], ascending=[True, False, True])
    resumen = resumen.drop(columns=["Fecha_recepcion_dt"])
    return resumen


def construir_resumen_general(df_bruto: pd.DataFrame, df_unico: pd.DataFrame, df_dup: pd.DataFrame) -> pd.DataFrame:
    filas = []

    aros = sorted(set(df_bruto["ARO"].dropna().unique()) | set(df_unico["ARO"].dropna().unique()))

    for aro in aros:
        b = df_bruto[df_bruto["ARO"] == aro]
        u = df_unico[df_unico["ARO"] == aro]
        d = df_dup[df_dup["ARO"] == aro] if not df_dup.empty else pd.DataFrame()

        fila = {
            "ARO": aro,
            "Registros_brutos": int(len(b)),
            "Codigos_unicos": int(len(u)),
            "Filas_duplicadas": int(len(d)),
            "Codigos_duplicados": int(d["Codigo"].nunique()) if not d.empty else 0,
            "Fecha_recepcion_min": u["Fecha_recepcion_dt"].min().strftime("%d/%m/%Y") if not u.empty and pd.notna(u["Fecha_recepcion_dt"].min()) else "",
            "Fecha_recepcion_max": u["Fecha_recepcion_dt"].max().strftime("%d/%m/%Y") if not u.empty and pd.notna(u["Fecha_recepcion_dt"].max()) else "",
        }

        for tipo in ["MR", "VDM", "VIG", "DIAG", "DSAN"]:
            fila[f"Unicos_{tipo}"] = int((u["Tipo_servicio_codigo"] == tipo).sum()) if not u.empty else 0

        filas.append(fila)

    total = {
        "ARO": "TOTAL",
        "Registros_brutos": int(len(df_bruto)),
        "Codigos_unicos": int(len(df_unico)),
        "Filas_duplicadas": int(len(df_dup)) if not df_dup.empty else 0,
        "Codigos_duplicados": int(df_dup[["ARO", "Codigo"]].drop_duplicates().shape[0]) if not df_dup.empty else 0,
        "Fecha_recepcion_min": df_unico["Fecha_recepcion_dt"].min().strftime("%d/%m/%Y") if not df_unico.empty and pd.notna(df_unico["Fecha_recepcion_dt"].min()) else "",
        "Fecha_recepcion_max": df_unico["Fecha_recepcion_dt"].max().strftime("%d/%m/%Y") if not df_unico.empty and pd.notna(df_unico["Fecha_recepcion_dt"].max()) else "",
    }

    for tipo in ["MR", "VDM", "VIG", "DIAG", "DSAN"]:
        total[f"Unicos_{tipo}"] = int((df_unico["Tipo_servicio_codigo"] == tipo).sum()) if not df_unico.empty else 0

    filas.append(total)
    return pd.DataFrame(filas)


def guardar_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df_out = df.copy()

    # Convertir columnas datetime a texto ISO para evitar problemas en CSV.
    for col in df_out.columns:
        if pd.api.types.is_datetime64_any_dtype(df_out[col]):
            df_out[col] = df_out[col].dt.strftime("%Y-%m-%d")

    df_out.to_csv(path, index=False, encoding="utf-8-sig")


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    inicio = datetime.now()
    timestamp = inicio.strftime("%Y%m%d_%H%M%S")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log = []
    log.append("=" * 90)
    log.append("GENERAR INVENTARIO MANUAL DE RESULTADOS DE AGUA - UESVALLE")
    log.append("=" * 90)
    log.append(f"Fecha ejecución: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    log.append(f"Portal:  {PORTAL_ROOT}")
    log.append(f"Entrada: {INPUT_DIR}")
    log.append(f"Salida:  {OUTPUT_DIR}")
    log.append("=" * 90)

    print("\n".join(log))

    dataframes = []
    archivos_leidos = {}

    for aro, nombre_archivo in ARCHIVOS_ENTRADA.items():
        path_txt = INPUT_DIR / nombre_archivo
        print(f"\n1. Leyendo {aro}: {path_txt}")

        df_aro = parsear_txt_manual(path_txt, aro)
        df_aro = enriquecer_dataframe(df_aro)

        archivos_leidos[aro] = {
            "archivo": str(path_txt),
            "existe": path_txt.exists(),
            "registros_brutos": int(len(df_aro)),
        }

        print(f"   Registros brutos detectados: {len(df_aro):,}".replace(",", "."))
        if len(df_aro) > 0:
            print(f"   Fecha mínima: {df_aro['Fecha_recepcion_dt'].min().strftime('%d/%m/%Y') if pd.notna(df_aro['Fecha_recepcion_dt'].min()) else ''}")
            print(f"   Fecha máxima: {df_aro['Fecha_recepcion_dt'].max().strftime('%d/%m/%Y') if pd.notna(df_aro['Fecha_recepcion_dt'].max()) else ''}")

        dataframes.append(df_aro)

    print("\n2. Consolidando archivos...")
    if dataframes:
        df_bruto = pd.concat(dataframes, ignore_index=True)
    else:
        df_bruto = pd.DataFrame()

    df_bruto = enriquecer_dataframe(df_bruto) if not df_bruto.empty else df_bruto

    print(f"   Registros brutos consolidados: {len(df_bruto):,}".replace(",", "."))

    print("\n3. Detectando duplicados por ARO + Código...")
    df_duplicados = construir_duplicados(df_bruto)
    codigos_duplicados = (
        df_duplicados[["ARO", "Codigo"]].drop_duplicates().shape[0]
        if not df_duplicados.empty else 0
    )
    print(f"   Filas duplicadas involucradas: {len(df_duplicados):,}".replace(",", "."))
    print(f"   Códigos duplicados: {codigos_duplicados:,}".replace(",", "."))

    if not df_duplicados.empty:
        print("   Duplicados detectados:")
        resumen_dup = df_duplicados.groupby(["ARO", "Codigo"]).size().reset_index(name="Filas")
        for _, row in resumen_dup.iterrows():
            print(f"    - {row['ARO']} | {row['Codigo']} | filas: {row['Filas']}")

    print("\n4. Construyendo inventario único...")
    df_unico = construir_unicos(df_bruto)
    print(f"   Códigos únicos consolidados: {len(df_unico):,}".replace(",", "."))

    print("\n5. Generando resúmenes...")
    df_resumen_fechas = construir_resumen_fechas(df_unico)
    df_resumen_general = construir_resumen_general(df_bruto, df_unico, df_duplicados)
    print(f"   Fechas resumidas: {len(df_resumen_fechas):,}".replace(",", "."))
    print(f"   Filas resumen general: {len(df_resumen_general):,}".replace(",", "."))

    print("\n6. Guardando salidas CSV...")
    paths = {
        "inventario_bruto": OUTPUT_DIR / "inventario_resultados_agua_bruto.csv",
        "inventario_unico": OUTPUT_DIR / "inventario_resultados_agua.csv",
        "duplicados": OUTPUT_DIR / "duplicados_inventario_resultados_agua.csv",
        "resumen_fechas": OUTPUT_DIR / "resumen_fechas_resultados_agua.csv",
        "resumen_general": OUTPUT_DIR / "resumen_resultados_agua.csv",
    }

    guardar_csv(df_bruto, paths["inventario_bruto"])
    guardar_csv(df_unico, paths["inventario_unico"])
    guardar_csv(df_duplicados, paths["duplicados"])
    guardar_csv(df_resumen_fechas, paths["resumen_fechas"])
    guardar_csv(df_resumen_general, paths["resumen_general"])

    metadata = {
        "proceso": "generar_inventario_manual_resultados_agua",
        "fecha_ejecucion": inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "portal_root": str(PORTAL_ROOT),
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "archivos_leidos": archivos_leidos,
        "total_registros_brutos": int(len(df_bruto)),
        "total_codigos_unicos": int(len(df_unico)),
        "total_filas_duplicadas": int(len(df_duplicados)) if not df_duplicados.empty else 0,
        "total_codigos_duplicados": int(codigos_duplicados),
        "salidas": {k: str(v) for k, v in paths.items()},
    }

    metadata_path = OUTPUT_DIR / "metadata_resultados_agua.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()

    log_final = [
        "",
        "=" * 90,
        "PROCESO FINALIZADO",
        "=" * 90,
        f"Duración segundos: {duracion:.1f}",
        f"Inventario bruto:   {paths['inventario_bruto']}",
        f"Inventario único:   {paths['inventario_unico']}",
        f"Duplicados:         {paths['duplicados']}",
        f"Resumen fechas:     {paths['resumen_fechas']}",
        f"Resumen general:    {paths['resumen_general']}",
        f"Metadata:           {metadata_path}",
        "-" * 90,
        f"Total bruto:        {len(df_bruto):,}".replace(",", "."),
        f"Total único:        {len(df_unico):,}".replace(",", "."),
        f"Códigos duplicados: {codigos_duplicados:,}".replace(",", "."),
        "=" * 90,
    ]

    print("\n".join(log_final))

    log_path = LOG_DIR / f"log_inventario_manual_resultados_agua_{timestamp}.txt"
    log_lineas(log_path, log + log_final)
    print(f"\nLog: {log_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("\n[ERROR] Falló el proceso:")
        print(str(exc))
        raise
