# -*- coding: utf-8 -*-
r"""
CRUZAR ÍNDICE DE RESULTADOS DE AGUA CON ENLACES DE GOOGLE DRIVE - UESVALLE
===========================================================================

Entradas esperadas:
  G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\data\resultados_agua\current\indice_resultados_agua.csv
  G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\data\resultados_agua\current\indice_drive_resultados_agua.csv

Salida:
  - Actualiza indice_resultados_agua.csv agregando:
      DRIVE_FILE_ID
      URL_DRIVE_VIEW
      URL_DRIVE_PREVIEW
      MATCH_DRIVE

  - Genera backup automático del índice anterior.
  - Genera resumen_cruce_indice_drive_resultados_agua.json
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


PORTAL_ROOT = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")
CURRENT_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "current"
ARCHIVE_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "archive"

INDICE_RESULTADOS = CURRENT_DIR / "indice_resultados_agua.csv"
INDICE_DRIVE = CURRENT_DIR / "indice_drive_resultados_agua.csv"

OUT_INDICE = CURRENT_DIR / "indice_resultados_agua.csv"
OUT_RESUMEN = CURRENT_DIR / "resumen_cruce_indice_drive_resultados_agua.json"


def leer_csv(path: Path):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f)), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"No se pudo leer el CSV por codificación: {path}")


def escribir_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def limpiar(v):
    return str(v or "").strip()


def normalizar_nombre(v):
    return limpiar(v).lower()


def extraer_codigo_desde_nombre(nombre: str) -> str:
    """
    Extrae código tipo 20260406-7499-VIG desde el nombre del PDF.
    """
    nombre = limpiar(nombre)
    m = re.search(r"(20\d{6}-\d{4}-(?:MR|VDM|VIG|DIAG|DSAN))", nombre, flags=re.I)
    return m.group(1).upper() if m else ""


def main():
    inicio = datetime.now()
    timestamp = inicio.strftime("%Y%m%d_%H%M%S")

    print("=" * 90)
    print("CRUZAR ÍNDICE RESULTADOS AGUA CON ENLACES DRIVE - UESVALLE")
    print("=" * 90)
    print(f"Índice resultados: {INDICE_RESULTADOS}")
    print(f"Índice Drive:      {INDICE_DRIVE}")
    print("=" * 90)

    if not INDICE_RESULTADOS.exists():
        raise FileNotFoundError(f"No existe: {INDICE_RESULTADOS}")

    if not INDICE_DRIVE.exists():
        raise FileNotFoundError(f"No existe: {INDICE_DRIVE}")

    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    rows_indice, enc_indice = leer_csv(INDICE_RESULTADOS)
    rows_drive, enc_drive = leer_csv(INDICE_DRIVE)

    print(f"Filas índice resultados: {len(rows_indice):,}".replace(",", "."))
    print(f"Filas índice Drive:      {len(rows_drive):,}".replace(",", "."))

    if not rows_indice:
        raise RuntimeError("El índice de resultados está vacío.")

    drive_por_nombre = {}
    drive_por_codigo = {}

    for d in rows_drive:
        nombre_pdf = limpiar(d.get("Nombre_PDF"))
        if not nombre_pdf:
            continue

        nombre_norm = normalizar_nombre(nombre_pdf)
        if nombre_norm not in drive_por_nombre:
            drive_por_nombre[nombre_norm] = d

        codigo = extraer_codigo_desde_nombre(nombre_pdf)
        if codigo and codigo not in drive_por_codigo:
            drive_por_codigo[codigo] = d

    backup_path = ARCHIVE_DIR / f"indice_resultados_agua_backup_antes_drive_{timestamp}.csv"
    shutil.copy2(INDICE_RESULTADOS, backup_path)
    print(f"Backup generado: {backup_path}")

    out_rows = []
    match_nombre = 0
    match_codigo = 0
    sin_nombre_pdf = 0
    sin_match = 0

    for r in rows_indice:
        row = dict(r)

        nombre_pdf = limpiar(
            row.get("NOMBRE_PDF")
            or row.get("Nombre_PDF")
            or row.get("nombre_pdf")
        )

        codigo = limpiar(
            row.get("CODIGO_MUESTRA")
            or row.get("Codigo")
            or row.get("Código")
            or row.get("ID_RESULTADO")
        ).upper()

        d = None
        match_tipo = ""

        if nombre_pdf:
            d = drive_por_nombre.get(normalizar_nombre(nombre_pdf))
            if d:
                match_tipo = "SI_NOMBRE"
                match_nombre += 1

        if d is None and codigo:
            d = drive_por_codigo.get(codigo)
            if d:
                match_tipo = "SI_CODIGO"
                match_codigo += 1

        if d:
            row["DRIVE_FILE_ID"] = limpiar(d.get("Drive_File_ID"))
            row["URL_DRIVE_VIEW"] = limpiar(d.get("URL_DRIVE_VIEW"))
            row["URL_DRIVE_PREVIEW"] = limpiar(d.get("URL_DRIVE_PREVIEW"))
            row["MATCH_DRIVE"] = match_tipo
        else:
            row["DRIVE_FILE_ID"] = ""
            row["URL_DRIVE_VIEW"] = ""
            row["URL_DRIVE_PREVIEW"] = ""
            if not nombre_pdf:
                row["MATCH_DRIVE"] = "SIN_NOMBRE_PDF"
                sin_nombre_pdf += 1
            else:
                row["MATCH_DRIVE"] = "NO"
                sin_match += 1

        out_rows.append(row)

    original_cols = list(rows_indice[0].keys())
    nuevas_cols = ["DRIVE_FILE_ID", "URL_DRIVE_VIEW", "URL_DRIVE_PREVIEW", "MATCH_DRIVE"]
    fieldnames = original_cols + [c for c in nuevas_cols if c not in original_cols]

    escribir_csv(OUT_INDICE, out_rows, fieldnames)

    resumen = {
        "fecha_generacion": inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "indice_resultados": str(INDICE_RESULTADOS),
        "indice_drive": str(INDICE_DRIVE),
        "backup_indice_anterior": str(backup_path),
        "filas_indice_resultados": len(rows_indice),
        "filas_indice_drive": len(rows_drive),
        "coincidencias_por_nombre_pdf": match_nombre,
        "coincidencias_por_codigo": match_codigo,
        "coincidencias_total": match_nombre + match_codigo,
        "filas_sin_nombre_pdf": sin_nombre_pdf,
        "filas_sin_match_drive": sin_match,
        "salida_indice_actualizado": str(OUT_INDICE),
    }

    OUT_RESUMEN.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 90)
    print("PROCESO FINALIZADO")
    print("=" * 90)
    print(f"Coincidencias por nombre PDF: {match_nombre}")
    print(f"Coincidencias por código:     {match_codigo}")
    print(f"Coincidencias total:          {match_nombre + match_codigo}")
    print(f"Sin nombre PDF:               {sin_nombre_pdf}")
    print(f"Sin match Drive:              {sin_match}")
    print(f"Índice actualizado:           {OUT_INDICE}")
    print(f"Resumen:                      {OUT_RESUMEN}")
    print("=" * 90)


if __name__ == "__main__":
    main()
