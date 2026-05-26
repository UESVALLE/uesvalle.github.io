# -*- coding: utf-8 -*-
r"""
GENERAR ÍNDICE DE RESULTADOS DE AGUA - UESVALLE

Objetivo:
- Leer los archivos de control generados por el descargador de resultados.
- Validar los PDF existentes en el repositorio documental.
- Generar CSV operativos para el tablero resultados_agua.html.

Entradas:
1) PDF:
   G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras\PDF_Resultados

2) Control de descargas:
   G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras\Control_Descargas

Salidas:
   G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\data\resultados_agua\current
"""

from pathlib import Path
from datetime import datetime
import json
import re
import unicodedata
import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PORTAL_ROOT = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

REPOSITORIO_RESULTADOS = Path(
    r"G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras"
)

PDF_ROOT = REPOSITORIO_RESULTADOS / "PDF_Resultados"
CONTROL_ROOT = REPOSITORIO_RESULTADOS / "Control_Descargas"

DATA_OUT_DIR = PORTAL_ROOT / "data" / "resultados_agua" / "current"
LOG_OUT_DIR = PORTAL_ROOT / "scripts" / "resultados_agua" / "logs"

OUT_INDICE = DATA_OUT_DIR / "indice_resultados_agua.csv"
OUT_RESUMEN = DATA_OUT_DIR / "resumen_resultados_agua.csv"
OUT_METADATA = DATA_OUT_DIR / "metadata_resultados_agua.json"

TIPOS_RESULTADO = {
    "MR": "MAPAS DE RIESGOS",
    "VDM": "VIGILANCIA DE MAPAS",
    "VIG": "VIGILANCIA RUTINARIA",
    "DIAG": "APOYO DIAGNÓSTICO",
    "DSAN": "DIAGNÓSTICO SANITARIO",
}


# =============================================================================
# UTILIDADES
# =============================================================================

def limpiar_texto(valor) -> str:
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def sin_tildes(texto: str) -> str:
    texto = limpiar_texto(texto)
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar_aro(valor: str) -> str:
    v = sin_tildes(valor).strip().lower()
    if "cartago" in v:
        return "Cartago"
    if "tulua" in v or "tuluá" in v:
        return "Tulua"
    if "cali" in v:
        return "Cali"
    return limpiar_texto(valor) or "SIN_ARO"


def extraer_aro_desde_ruta_o_nombre(path_pdf: Path, nombre_pdf: str = "") -> str:
    partes = [sin_tildes(p).lower() for p in path_pdf.parts]
    for aro in ["cartago", "cali", "tulua"]:
        if aro in partes:
            return "Tulua" if aro == "tulua" else aro.capitalize()

    n = sin_tildes(nombre_pdf).lower()
    if "uesvallecartago" in n:
        return "Cartago"
    if "uesvallecali" in n:
        return "Cali"
    if "uesvalletulua" in n:
        return "Tulua"

    return "SIN_ARO"


def windows_file_uri(ruta: str) -> str:
    """
    Genera una URL local tipo file:///G:/...
    En algunos navegadores puede abrir si el HTML se ejecuta localmente.
    En GitHub Pages normalmente el navegador bloqueará file:// por seguridad.
    """
    ruta = limpiar_texto(ruta)
    if not ruta:
        return ""
    uri = ruta.replace("\\", "/")
    uri = uri.replace(" ", "%20")
    if re.match(r"^[A-Za-z]:/", uri):
        return "file:///" + uri
    return uri


def extraer_lote_desde_ruta(ruta: str) -> str:
    ruta = limpiar_texto(ruta)
    m = re.search(r"(Lote_\d{8}_\d{4})", ruta, flags=re.IGNORECASE)
    return m.group(1) if m else ""


def parsear_nombre_pdf(nombre_pdf: str) -> dict:
    """
    Estructura esperada:
    20260406-7483-MR-0024-06-04-2026-uesvallecartago.pdf
    """
    nombre_pdf = limpiar_texto(nombre_pdf)
    stem = Path(nombre_pdf).stem

    patron = re.compile(
        r"^(?P<fecha_ini>\d{8})-"
        r"(?P<num>\d+)-"
        r"(?P<tipo>MR|VDM|VIG|DIAG|DSAN)-"
        r"(?P<consecutivo>\d+)-"
        r"(?P<dia>\d{2})-(?P<mes>\d{2})-(?P<anio>\d{4})-"
        r"(?P<usuario>.+)$",
        flags=re.IGNORECASE
    )

    m = patron.match(stem)
    if not m:
        # Fallback para detectar tipo dentro del nombre
        tipo = ""
        mtipo = re.search(r"-(MR|VDM|VIG|DIAG|DSAN)-", stem, flags=re.IGNORECASE)
        if mtipo:
            tipo = mtipo.group(1).upper()

        anio = ""
        manio = re.search(r"(20\d{2})", stem)
        if manio:
            anio = manio.group(1)

        return {
            "CODIGO_MUESTRA_PARSE": "",
            "TIPO_CODIGO_PARSE": tipo,
            "TIPO_NOMBRE_PARSE": TIPOS_RESULTADO.get(tipo, ""),
            "CONSECUTIVO_PARSE": "",
            "FECHA_NOMBRE_PARSE": "",
            "ANIO_PARSE": anio,
            "USUARIO_PDF_PARSE": "",
        }

    g = m.groupdict()
    tipo = g["tipo"].upper()
    fecha_nombre = f"{g['dia']}/{g['mes']}/{g['anio']}"
    codigo_muestra = f"{g['fecha_ini']}-{g['num']}-{tipo}"

    return {
        "CODIGO_MUESTRA_PARSE": codigo_muestra,
        "TIPO_CODIGO_PARSE": tipo,
        "TIPO_NOMBRE_PARSE": TIPOS_RESULTADO.get(tipo, ""),
        "CONSECUTIVO_PARSE": g["consecutivo"],
        "FECHA_NOMBRE_PARSE": fecha_nombre,
        "ANIO_PARSE": g["anio"],
        "USUARIO_PDF_PARSE": g["usuario"],
    }


def preparar_directorios():
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_OUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# LECTURA DE INSUMOS
# =============================================================================

def listar_pdfs() -> pd.DataFrame:
    if not PDF_ROOT.exists():
        print(f"[AVISO] No existe la carpeta PDF: {PDF_ROOT}")
        return pd.DataFrame()

    registros = []
    for pdf in PDF_ROOT.rglob("*.pdf"):
        parsed = parsear_nombre_pdf(pdf.name)
        aro = extraer_aro_desde_ruta_o_nombre(pdf, pdf.name)
        anio = parsed.get("ANIO_PARSE") or ""

        registros.append({
            "NOMBRE_PDF": pdf.name,
            "RUTA_LOCAL_REAL": str(pdf),
            "URL_LOCAL_REAL": windows_file_uri(str(pdf)),
            "EXISTE_PDF_REAL": "SI",
            "ANIO_REAL": anio,
            "ARO_REAL": aro,
            **parsed
        })

    df = pd.DataFrame(registros)
    if not df.empty:
        df = df.sort_values(["ANIO_REAL", "ARO_REAL", "NOMBRE_PDF"])
    return df


def listar_archivos_control() -> list[Path]:
    if not CONTROL_ROOT.exists():
        print(f"[AVISO] No existe la carpeta de control: {CONTROL_ROOT}")
        return []

    archivos = []
    archivos.extend(CONTROL_ROOT.rglob("control_descarga_resultados_CONSOLIDADO_lote_*.csv"))
    archivos.extend(CONTROL_ROOT.rglob("control_descarga_resultados_CONSOLIDADO_lote_*.xlsx"))
    return sorted(set(archivos))


def leer_archivo_control(path: Path) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        elif path.suffix.lower() == ".xlsx":
            df = pd.read_excel(path, dtype=str)
        else:
            return pd.DataFrame()

        df["ARCHIVO_CONTROL"] = path.name
        df["RUTA_ARCHIVO_CONTROL"] = str(path)
        df["LOTE_DESCARGA"] = extraer_lote_desde_ruta(str(path)) or extraer_lote_desde_ruta(path.name)
        return df

    except Exception as e:
        print(f"[ERROR] No se pudo leer control: {path} | {e}")
        return pd.DataFrame()


def cargar_controles() -> pd.DataFrame:
    archivos = listar_archivos_control()

    if not archivos:
        print("[AVISO] No se encontraron archivos de control.")
        return pd.DataFrame()

    frames = []
    print(f"[INFO] Archivos de control encontrados: {len(archivos)}")

    for path in archivos:
        df = leer_archivo_control(path)
        if not df.empty:
            frames.append(df)
            print(f"  OK: {path.name} ({len(df):,} registros)")

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)

    # Normalizar nombres de columnas esperados.
    df_all.columns = [limpiar_texto(c) for c in df_all.columns]

    return df_all


# =============================================================================
# CONSTRUCCIÓN DEL ÍNDICE
# =============================================================================

def construir_indice(df_control: pd.DataFrame, df_pdf: pd.DataFrame) -> pd.DataFrame:
    fecha_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    # Caso 1: existe control de descargas. Este será la base principal.
    # -------------------------------------------------------------------------
    if not df_control.empty:
        df = df_control.copy()

        # Asegurar columnas mínimas.
        columnas_minimas = [
            "Codigo", "Fecha_envio", "Fecha_recepcion", "Hora_recepcion",
            "Fecha_resultados", "Tipo", "Entidad_que_remite", "Muestras_recibidas",
            "Muestras_rechazadas", "Estado", "Fecha_filtro_recepcion",
            "ARO", "Usuario", "Descargado", "Nombre_PDF", "Ruta_PDF",
            "Tipo_servicio_detectado_codigo", "Tipo_servicio_detectado_nombre",
            "Estado_descarga", "Error", "LOTE_DESCARGA",
        ]

        for col in columnas_minimas:
            if col not in df.columns:
                df[col] = ""

        # Parsear nombre PDF.
        parsed = df["Nombre_PDF"].apply(parsear_nombre_pdf).apply(pd.Series)
        df = pd.concat([df, parsed], axis=1)

        # Unir validación física de PDF por nombre.
        if not df_pdf.empty:
            cols_pdf = [
                "NOMBRE_PDF", "RUTA_LOCAL_REAL", "URL_LOCAL_REAL", "EXISTE_PDF_REAL",
                "ANIO_REAL", "ARO_REAL"
            ]
            df_pdf_join = df_pdf[cols_pdf].drop_duplicates("NOMBRE_PDF", keep="last")
            df = df.merge(
                df_pdf_join,
                how="left",
                left_on="Nombre_PDF",
                right_on="NOMBRE_PDF"
            )
        else:
            df["RUTA_LOCAL_REAL"] = ""
            df["URL_LOCAL_REAL"] = ""
            df["EXISTE_PDF_REAL"] = ""
            df["ANIO_REAL"] = ""
            df["ARO_REAL"] = ""

        df["ID_RESULTADO"] = df["Codigo"].where(df["Codigo"].astype(str).str.len() > 0, df["CODIGO_MUESTRA_PARSE"])
        df["ANIO"] = df["ANIO_REAL"].fillna("").where(df["ANIO_REAL"].fillna("") != "", df["ANIO_PARSE"].fillna(""))
        df["ARO_FINAL"] = df["ARO"].apply(normalizar_aro)
        df.loc[df["ARO_FINAL"].eq("SIN_ARO"), "ARO_FINAL"] = df["ARO_REAL"].fillna("").apply(normalizar_aro)

        df["CODIGO_MUESTRA"] = df["Codigo"].where(df["Codigo"].astype(str).str.len() > 0, df["CODIGO_MUESTRA_PARSE"])
        df["TIPO_CODIGO"] = df["Tipo_servicio_detectado_codigo"].where(
            df["Tipo_servicio_detectado_codigo"].astype(str).str.len() > 0,
            df["TIPO_CODIGO_PARSE"]
        )
        df["TIPO_NOMBRE"] = df["Tipo_servicio_detectado_nombre"].where(
            df["Tipo_servicio_detectado_nombre"].astype(str).str.len() > 0,
            df["TIPO_NOMBRE_PARSE"]
        )

        df["CONSECUTIVO"] = df["CONSECUTIVO_PARSE"]
        df["FECHA_NOMBRE"] = df["FECHA_NOMBRE_PARSE"]

        # Ruta final real si existe; si no, usar ruta del control.
        df["RUTA_LOCAL"] = df["RUTA_LOCAL_REAL"].fillna("").where(
            df["RUTA_LOCAL_REAL"].fillna("") != "",
            df["Ruta_PDF"].fillna("")
        )
        df["URL_LOCAL"] = df["RUTA_LOCAL"].apply(windows_file_uri)
        df["EXISTE_PDF"] = df["EXISTE_PDF_REAL"].fillna("").where(
            df["EXISTE_PDF_REAL"].fillna("") != "",
            df["RUTA_LOCAL"].apply(lambda p: "SI" if Path(str(p)).exists() else "NO")
        )

        df["FUENTE_REGISTRO"] = "CONTROL_DESCARGA"

        # Agregar PDF que existan físicamente pero no estén en controles.
        if not df_pdf.empty:
            pdfs_control = set(df["Nombre_PDF"].dropna().astype(str))
            faltantes = df_pdf[~df_pdf["NOMBRE_PDF"].isin(pdfs_control)].copy()

            if not faltantes.empty:
                extra = pd.DataFrame({
                    "ID_RESULTADO": faltantes["CODIGO_MUESTRA_PARSE"],
                    "ANIO": faltantes["ANIO_REAL"],
                    "ARO_FINAL": faltantes["ARO_REAL"],
                    "CODIGO_MUESTRA": faltantes["CODIGO_MUESTRA_PARSE"],
                    "TIPO_CODIGO": faltantes["TIPO_CODIGO_PARSE"],
                    "TIPO_NOMBRE": faltantes["TIPO_NOMBRE_PARSE"],
                    "CONSECUTIVO": faltantes["CONSECUTIVO_PARSE"],
                    "FECHA_NOMBRE": faltantes["FECHA_NOMBRE_PARSE"],
                    "Fecha_envio": "",
                    "Fecha_recepcion": "",
                    "Hora_recepcion": "",
                    "Fecha_resultados": "",
                    "Tipo": "Agua",
                    "Entidad_que_remite": "",
                    "Muestras_recibidas": "",
                    "Muestras_rechazadas": "",
                    "Estado": "",
                    "Descargado": "SI",
                    "Estado_descarga": "OK_SIN_CONTROL",
                    "Nombre_PDF": faltantes["NOMBRE_PDF"],
                    "RUTA_LOCAL": faltantes["RUTA_LOCAL_REAL"],
                    "URL_LOCAL": faltantes["URL_LOCAL_REAL"],
                    "EXISTE_PDF": "SI",
                    "LOTE_DESCARGA": "",
                    "ARCHIVO_CONTROL": "",
                    "RUTA_ARCHIVO_CONTROL": "",
                    "FUENTE_REGISTRO": "PDF_FISICO",
                    "Error": "",
                })
                df = pd.concat([df, extra], ignore_index=True, sort=False)

    # -------------------------------------------------------------------------
    # Caso 2: no hay controles, se construye solo desde PDF.
    # -------------------------------------------------------------------------
    else:
        if df_pdf.empty:
            return pd.DataFrame()

        df = pd.DataFrame({
            "ID_RESULTADO": df_pdf["CODIGO_MUESTRA_PARSE"],
            "ANIO": df_pdf["ANIO_REAL"],
            "ARO_FINAL": df_pdf["ARO_REAL"],
            "CODIGO_MUESTRA": df_pdf["CODIGO_MUESTRA_PARSE"],
            "TIPO_CODIGO": df_pdf["TIPO_CODIGO_PARSE"],
            "TIPO_NOMBRE": df_pdf["TIPO_NOMBRE_PARSE"],
            "CONSECUTIVO": df_pdf["CONSECUTIVO_PARSE"],
            "FECHA_NOMBRE": df_pdf["FECHA_NOMBRE_PARSE"],
            "Fecha_envio": "",
            "Fecha_recepcion": "",
            "Hora_recepcion": "",
            "Fecha_resultados": "",
            "Tipo": "Agua",
            "Entidad_que_remite": "",
            "Muestras_recibidas": "",
            "Muestras_rechazadas": "",
            "Estado": "",
            "Descargado": "SI",
            "Estado_descarga": "OK_SIN_CONTROL",
            "Nombre_PDF": df_pdf["NOMBRE_PDF"],
            "RUTA_LOCAL": df_pdf["RUTA_LOCAL_REAL"],
            "URL_LOCAL": df_pdf["URL_LOCAL_REAL"],
            "EXISTE_PDF": "SI",
            "LOTE_DESCARGA": "",
            "ARCHIVO_CONTROL": "",
            "RUTA_ARCHIVO_CONTROL": "",
            "FUENTE_REGISTRO": "PDF_FISICO",
            "Error": "",
        })

    # -------------------------------------------------------------------------
    # Estandarización final de columnas.
    # -------------------------------------------------------------------------
    df["FECHA_ACTUALIZACION"] = fecha_actualizacion

    columnas_salida = [
        "ID_RESULTADO",
        "ANIO",
        "ARO_FINAL",
        "CODIGO_MUESTRA",
        "TIPO_CODIGO",
        "TIPO_NOMBRE",
        "CONSECUTIVO",
        "FECHA_NOMBRE",
        "Fecha_envio",
        "Fecha_recepcion",
        "Hora_recepcion",
        "Fecha_resultados",
        "Tipo",
        "Entidad_que_remite",
        "Muestras_recibidas",
        "Muestras_rechazadas",
        "Estado",
        "Descargado",
        "Estado_descarga",
        "Nombre_PDF",
        "RUTA_LOCAL",
        "URL_LOCAL",
        "EXISTE_PDF",
        "LOTE_DESCARGA",
        "ARCHIVO_CONTROL",
        "RUTA_ARCHIVO_CONTROL",
        "FUENTE_REGISTRO",
        "Error",
        "FECHA_ACTUALIZACION",
    ]

    for col in columnas_salida:
        if col not in df.columns:
            df[col] = ""

    df = df[columnas_salida].copy()

    # Renombrar a mayúsculas institucionales.
    df = df.rename(columns={
        "ARO_FINAL": "ARO",
        "Fecha_envio": "FECHA_ENVIO",
        "Fecha_recepcion": "FECHA_RECEPCION",
        "Hora_recepcion": "HORA_RECEPCION",
        "Fecha_resultados": "FECHA_RESULTADOS",
        "Tipo": "CLASE_MUESTRA",
        "Entidad_que_remite": "ENTIDAD_QUE_REMITE",
        "Muestras_recibidas": "MUESTRAS_RECIBIDAS",
        "Muestras_rechazadas": "MUESTRAS_RECHAZADAS",
        "Estado": "ESTADO",
        "Descargado": "DESCARGADO",
        "Estado_descarga": "ESTADO_DESCARGA",
        "Nombre_PDF": "NOMBRE_PDF",
        "Error": "ERROR",
    })

    # Limpiar celdas de texto.
    for col in df.columns:
        df[col] = df[col].apply(limpiar_texto)

    # Deduplicar: el nombre del PDF es el identificador operativo más estable.
    if "NOMBRE_PDF" in df.columns:
        df = df.sort_values(["FECHA_ACTUALIZACION", "LOTE_DESCARGA"])
        df = df.drop_duplicates(subset=["NOMBRE_PDF"], keep="last")

    df = df.sort_values(["ANIO", "ARO", "TIPO_CODIGO", "CODIGO_MUESTRA", "NOMBRE_PDF"])

    return df


def depurar_indice_final(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el índice antes de exportar:
    1. Recalcula EXISTE_PDF con base en RUTA_LOCAL física.
    2. Elimina registros fallidos cuando existe un registro OK para el mismo código + ARO.
    3. Prioriza registros OK y con PDF existente.
    """
    if df.empty:
        return df

    df = df.copy()

    for col in ["CODIGO_MUESTRA", "ARO", "NOMBRE_PDF", "RUTA_LOCAL", "ESTADO_DESCARGA", "DESCARGADO"]:
        if col not in df.columns:
            df[col] = ""

    def existe_pdf_real(row):
        ruta = limpiar_texto(row.get("RUTA_LOCAL", ""))
        nombre = limpiar_texto(row.get("NOMBRE_PDF", ""))
        if not ruta or not nombre:
            return "NO"
        try:
            return "SI" if Path(ruta).exists() else "NO"
        except Exception:
            return "NO"

    df["EXISTE_PDF"] = df.apply(existe_pdf_real, axis=1)

    # Puntaje de calidad del registro.
    def calidad(row):
        score = 0
        if limpiar_texto(row.get("ESTADO_DESCARGA", "")).upper() in ["OK", "OK_SIN_CONTROL"]:
            score += 100
        if limpiar_texto(row.get("DESCARGADO", "")).upper() == "SI":
            score += 50
        if limpiar_texto(row.get("EXISTE_PDF", "")).upper() == "SI":
            score += 50
        if limpiar_texto(row.get("NOMBRE_PDF", "")):
            score += 20
        if limpiar_texto(row.get("RUTA_LOCAL", "")):
            score += 20
        return score

    df["_CALIDAD_REGISTRO"] = df.apply(calidad, axis=1)

    # Si un mismo CODIGO_MUESTRA + ARO tiene al menos un registro con PDF real,
    # elimina los registros del mismo código que no tengan PDF.
    claves = ["CODIGO_MUESTRA", "ARO"]
    tiene_pdf_por_clave = (
        df.groupby(claves, dropna=False)["EXISTE_PDF"]
        .transform(lambda s: "SI" in set(s.astype(str).str.upper()))
    )
    df = df[~((tiene_pdf_por_clave) & (df["EXISTE_PDF"].str.upper() != "SI"))].copy()

    # Deduplicación principal:
    # primero por NOMBRE_PDF cuando existe, luego por CODIGO_MUESTRA + ARO cuando no hay nombre.
    df["_NOMBRE_PDF_SORT"] = df["NOMBRE_PDF"].replace("", pd.NA)
    df = df.sort_values(
        ["_CALIDAD_REGISTRO", "FECHA_ACTUALIZACION", "LOTE_DESCARGA"],
        ascending=[False, False, False]
    )

    con_pdf = df[df["NOMBRE_PDF"].astype(str).str.len() > 0].copy()
    sin_pdf = df[df["NOMBRE_PDF"].astype(str).str.len() == 0].copy()

    if not con_pdf.empty:
        con_pdf = con_pdf.drop_duplicates(subset=["NOMBRE_PDF"], keep="first")

    if not sin_pdf.empty:
        sin_pdf = sin_pdf.drop_duplicates(subset=["CODIGO_MUESTRA", "ARO"], keep="first")

    df = pd.concat([con_pdf, sin_pdf], ignore_index=True, sort=False)

    # Segunda depuración: si aún queda un registro sin PDF para una clave que ya tiene PDF, eliminarlo.
    tiene_pdf_por_clave = (
        df.groupby(claves, dropna=False)["EXISTE_PDF"]
        .transform(lambda s: "SI" in set(s.astype(str).str.upper()))
    )
    df = df[~((tiene_pdf_por_clave) & (df["EXISTE_PDF"].str.upper() != "SI"))].copy()

    df = df.drop(columns=[c for c in ["_CALIDAD_REGISTRO", "_NOMBRE_PDF_SORT"] if c in df.columns], errors="ignore")

    if {"ANIO", "ARO", "TIPO_CODIGO", "CODIGO_MUESTRA", "NOMBRE_PDF"}.issubset(df.columns):
        df = df.sort_values(["ANIO", "ARO", "TIPO_CODIGO", "CODIGO_MUESTRA", "NOMBRE_PDF"])

    return df


def generar_resumen(df_indice: pd.DataFrame) -> pd.DataFrame:
    if df_indice.empty:
        return pd.DataFrame()

    resumen = (
        df_indice
        .groupby(["ANIO", "ARO", "TIPO_CODIGO", "TIPO_NOMBRE", "EXISTE_PDF"], dropna=False)
        .size()
        .reset_index(name="TOTAL_RESULTADOS")
        .sort_values(["ANIO", "ARO", "TIPO_CODIGO", "EXISTE_PDF"])
    )

    return resumen


def guardar_salidas(df_indice: pd.DataFrame, df_resumen: pd.DataFrame):
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    df_indice.to_csv(OUT_INDICE, index=False, encoding="utf-8-sig")
    df_resumen.to_csv(OUT_RESUMEN, index=False, encoding="utf-8-sig")

    metadata = {
        "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "portal_root": str(PORTAL_ROOT),
        "repositorio_resultados": str(REPOSITORIO_RESULTADOS),
        "pdf_root": str(PDF_ROOT),
        "control_root": str(CONTROL_ROOT),
        "total_resultados_indice": int(len(df_indice)),
        "total_pdf_existentes": int((df_indice.get("EXISTE_PDF", pd.Series(dtype=str)) == "SI").sum()),
        "total_por_aro": df_indice.groupby("ARO").size().to_dict() if not df_indice.empty else {},
        "total_por_tipo": df_indice.groupby("TIPO_CODIGO").size().to_dict() if not df_indice.empty else {},
        "archivo_indice": str(OUT_INDICE),
        "archivo_resumen": str(OUT_RESUMEN),
    }

    OUT_METADATA.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Log sencillo.
    log_path = LOG_OUT_DIR / f"log_indice_resultados_agua_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    LOG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join([
            "LOG GENERACIÓN ÍNDICE RESULTADOS AGUA",
            f"Fecha: {metadata['fecha_actualizacion']}",
            f"Total índice: {metadata['total_resultados_indice']}",
            f"PDF existentes: {metadata['total_pdf_existentes']}",
            f"Índice: {OUT_INDICE}",
            f"Resumen: {OUT_RESUMEN}",
            f"Metadata: {OUT_METADATA}",
        ]),
        encoding="utf-8"
    )

    return metadata, log_path


# =============================================================================
# EJECUCIÓN
# =============================================================================

def main():
    print("=" * 80)
    print("GENERAR ÍNDICE DE RESULTADOS DE AGUA - UESVALLE")
    print("=" * 80)
    print(f"Portal:      {PORTAL_ROOT}")
    print(f"PDF root:    {PDF_ROOT}")
    print(f"Control:     {CONTROL_ROOT}")
    print(f"Salida CSV:  {DATA_OUT_DIR}")
    print("=" * 80)

    preparar_directorios()

    print("\n1. Leyendo PDF existentes...")
    df_pdf = listar_pdfs()
    print(f"   PDF encontrados: {len(df_pdf):,}")

    print("\n2. Leyendo controles de descarga...")
    df_control = cargar_controles()
    print(f"   Registros de control: {len(df_control):,}")

    print("\n3. Construyendo índice maestro...")
    df_indice = construir_indice(df_control, df_pdf)
    print(f"   Registros índice bruto: {len(df_indice):,}")

    print("\n3.1. Depurando duplicados y registros sin PDF...")
    df_indice = depurar_indice_final(df_indice)
    print(f"   Registros índice depurado: {len(df_indice):,}")

    if df_indice.empty:
        print("\n[AVISO] No se generó índice porque no se encontraron PDF ni controles.")
        return

    print("\n4. Generando resumen...")
    df_resumen = generar_resumen(df_indice)
    print(f"   Registros resumen: {len(df_resumen):,}")

    print("\n5. Guardando salidas...")
    metadata, log_path = guardar_salidas(df_indice, df_resumen)

    print("\n" + "=" * 80)
    print("PROCESO FINALIZADO")
    print("=" * 80)
    print(f"Índice:       {OUT_INDICE}")
    print(f"Resumen:      {OUT_RESUMEN}")
    print(f"Metadata:     {OUT_METADATA}")
    print(f"Log:          {log_path}")
    print(f"Total índice: {metadata['total_resultados_indice']:,}")
    print(f"PDF OK:       {metadata['total_pdf_existentes']:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
