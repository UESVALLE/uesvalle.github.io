# -*- coding: utf-8 -*-
"""
DETECTAR FECHAS DISPONIBLES DE RESULTADOS DE AGUA - UESVALLE

Objetivo:
- Consultar la base general de la página /results sin entrar a las fichas ni descargar PDF.
- Identificar las fechas de recepción que realmente tienen resultados.
- Generar un CSV/Excel con las fechas disponibles por ARO y tipo de resultado.
- Servir como insumo para ejecutar posteriormente la descarga de resultados PDF solo en fechas con registros.

Ventaja:
- Evita recorrer rangos completos día por día.
- Reduce tiempos de consulta cuando en un mes solo hay 10 a 12 días con muestreo.

Salida principal:
- data/resultados_agua/current/fechas_disponibles_resultados_agua.csv
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime
from pathlib import Path
import os
import re
import time
import unicodedata
import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

USUARIOS = {
    "1": {"nombre": "Cartago", "usuario": "16232927", "password": "16232927"},
    "2": {"nombre": "Tuluá", "usuario": "16551281", "password": "16551281"},
    "3": {"nombre": "Cali", "usuario": "31641854", "password": "31641854"},
}

TIPOS_SERVICIO = {
    "1": {"codigo": "MR", "nombre": "MAPAS DE RIESGOS", "valor_select": "MAPAS DE RIESGOS"},
    "2": {"codigo": "VDM", "nombre": "VIGILANCIA DE MAPAS", "valor_select": "VIGILANCIA DE MAPAS"},
    "3": {"codigo": "VIG", "nombre": "VIGILANCIA RUTINARIA", "valor_select": "VIGILANCIA RUTINARIA"},
    "4": {"codigo": "DIAG", "nombre": "APOYO DIAGNÓSTICO", "valor_select": "APOYO DIAGNÓSTICO"},
    "5": {"codigo": "DSAN", "nombre": "DIAGNÓSTICO SANITARIO", "valor_select": "DIAGNÓSTICO SANITARIO"},
}

LOGIN_URL = "https://gestion-muestras.valledelcauca.gov.co/login"
RESULTADOS_URL = "https://gestion-muestras.valledelcauca.gov.co/results"

RUN_ID = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"

PORTAL_UESVALLE_DIR = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")
REPOSITORIO_RESULTADOS_DIR = Path(
    r"G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras"
)

CONTROL_DESCARGAS_DIR = REPOSITORIO_RESULTADOS_DIR / "Control_Descargas"
SALIDAS_DIR = CONTROL_DESCARGAS_DIR / f"Lote_Fechas_{RUN_ID}"
HTML_DEBUG_DIR = SALIDAS_DIR / "HTML_Debug"

PORTAL_DATA_DIR = PORTAL_UESVALLE_DIR / "data" / "resultados_agua" / "current"
PORTAL_SCRIPTS_DIR = PORTAL_UESVALLE_DIR / "scripts" / "resultados_agua"

OUT_FECHAS_CURRENT_CSV = PORTAL_DATA_DIR / "fechas_disponibles_resultados_agua.csv"
OUT_FECHAS_CURRENT_XLSX = PORTAL_DATA_DIR / "fechas_disponibles_resultados_agua.xlsx"
OUT_RESUMEN_CURRENT_CSV = PORTAL_DATA_DIR / "resumen_fechas_disponibles_resultados_agua.csv"

for carpeta in [CONTROL_DESCARGAS_DIR, SALIDAS_DIR, HTML_DEBUG_DIR, PORTAL_DATA_DIR, PORTAL_SCRIPTS_DIR]:
    carpeta.mkdir(parents=True, exist_ok=True)


# =============================================================================
# UTILIDADES
# =============================================================================

def limpiar_texto(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def normalizar_nombre_carpeta(texto):
    texto = limpiar_texto(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace(" ", "_")
    texto = re.sub(r"[^\w\-\.]", "_", texto, flags=re.UNICODE)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto or "SIN_DATO"


def normalizar_fecha_usuario(fecha_raw: str):
    f = fecha_raw.strip().replace("-", "/")
    dt = datetime.strptime(f, "%d/%m/%Y")
    return dt.strftime("%d/%m/%Y"), dt


def detectar_tipo_servicio_desde_texto(*valores):
    texto = " ".join(limpiar_texto(v).upper() for v in valores if v)
    patrones = [
        ("DSAN", "DIAGNÓSTICO SANITARIO", [r"\bDSAN\b", "DIAGNOSTICO SANITARIO", "DIAGNÓSTICO SANITARIO"]),
        ("DIAG", "APOYO DIAGNÓSTICO", [r"\bDIAG\b", "APOYO DIAGNOSTICO", "APOYO DIAGNÓSTICO"]),
        ("VDM", "VIGILANCIA DE MAPAS", [r"\bVDM\b", "VIGILANCIA DE MAPAS"]),
        ("VIG", "VIGILANCIA RUTINARIA", [r"\bVIG\b", "VIGILANCIA RUTINARIA"]),
        ("MR", "MAPAS DE RIESGOS", [r"\bMR\b", "MAPAS DE RIESGO", "MAPAS DE RIESGOS"]),
    ]

    for codigo, nombre, pats in patrones:
        for pat in pats:
            if pat.startswith(r"\b"):
                if re.search(pat, texto):
                    return codigo, nombre
            elif pat in texto:
                return codigo, nombre

    return "SIN_CLASIFICAR", "SIN CLASIFICAR"


def fecha_en_rango(fecha_str, fecha_ini_dt=None, fecha_fin_dt=None):
    if not fecha_str:
        return False
    try:
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
    except Exception:
        return False

    if fecha_ini_dt and dt < fecha_ini_dt:
        return False
    if fecha_fin_dt and dt > fecha_fin_dt:
        return False
    return True


# =============================================================================
# SELENIUM
# =============================================================================

def iniciar_driver(headless=True):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def login(driver, user_cfg):
    wait = WebDriverWait(driver, 30)

    driver.get(LOGIN_URL)

    usuario = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='username']"))
    )
    password = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='password']"))
    )

    usuario.clear()
    usuario.send_keys(user_cfg["usuario"])
    password.clear()
    password.send_keys(user_cfg["password"])
    password.send_keys(Keys.ENTER)

    wait.until(EC.url_contains("/home"))
    print("✅ Login exitoso:", driver.current_url)


def limpiar_busqueda(driver):
    wait = WebDriverWait(driver, 5)
    try:
        btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@aria-label,'Limpiar búsqueda') "
                    "or contains(@mattooltip,'Limpiar búsqueda') "
                    "or .//mat-icon[normalize-space()='clear_all']]"
                )
            )
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.7)
        print("   🧹 Búsqueda limpiada.")
    except Exception:
        pass


def seleccionar_mat_select_por_label(driver, label, valor, obligatorio=False):
    wait = WebDriverWait(driver, 20)

    try:
        campo = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//mat-form-field[.//mat-label[contains(., '{label}')]]")
            )
        )

        valor_actual = ""
        for selector in [
            "span.mat-mdc-select-min-line",
            "span.mat-mdc-select-value-text",
            ".mat-mdc-select-value"
        ]:
            try:
                valor_actual = limpiar_texto(campo.find_element(By.CSS_SELECTOR, selector).text)
                if valor_actual:
                    break
            except Exception:
                pass

        if valor_actual and valor.lower() in valor_actual.lower():
            print(f"   📌 {label} ya está seleccionado: {valor_actual}")
            return True

        trigger = campo.find_element(By.CSS_SELECTOR, "div.mat-mdc-select-trigger")
        driver.execute_script("arguments[0].click();", trigger)
        time.sleep(0.5)

        valor_min = valor.lower()
        opcion = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//mat-option//span[contains("
                    "translate(normalize-space(.),"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ',"
                    "'abcdefghijklmnopqrstuvwxyzáéíóúü'),"
                    f"'{valor_min}')]"
                )
            )
        )
        driver.execute_script("arguments[0].click();", opcion)
        time.sleep(0.8)
        print(f"   ✅ {label} filtrado: {valor}")
        return True

    except Exception as e:
        msg = f"⚠ No se pudo seleccionar {label} = {valor}: {e}"
        if obligatorio:
            raise RuntimeError(msg)
        print("   " + msg)
        return False


def aplicar_filtros_base_resultados(driver, estado="FINALIZADA", tipo_servicio_cfg=None):
    limpiar_busqueda(driver)

    seleccionar_mat_select_por_label(driver, "Clase de muestra", "Agua", obligatorio=False)

    if tipo_servicio_cfg:
        seleccionar_mat_select_por_label(
            driver,
            "Tipo de servicio",
            tipo_servicio_cfg.get("valor_select", ""),
            obligatorio=False
        )
        print(f"   🎯 Alcance específico: {tipo_servicio_cfg.get('codigo')} - {tipo_servicio_cfg.get('nombre')}")
    else:
        print("   🎯 Alcance: TODAS AGUA, sin filtrar por Tipo de servicio.")

    seleccionar_mat_select_por_label(driver, "Estado", estado, obligatorio=False)
    time.sleep(2.0)


def esperar_tabla_con_filas(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    return driver.find_elements(By.CSS_SELECTOR, "table tbody tr")


def set_page_size_50(driver):
    wait = WebDriverWait(driver, 15)
    try:
        select_page_size = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//mat-paginator//mat-select"))
        )
        driver.execute_script("arguments[0].click();", select_page_size)
        time.sleep(0.5)

        opcion_50 = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//mat-option//span[normalize-space()='50']"))
        )
        driver.execute_script("arguments[0].click();", opcion_50)
        time.sleep(1.0)
        print("   📌 Elementos por página configurados en: 50")
    except Exception as e:
        print(f"   ⚠ No se pudo cambiar 'Elementos por página' a 50: {e}")


def pagina_siguiente_disponible(driver):
    posibles = driver.find_elements(By.CSS_SELECTOR, "button.mat-mdc-paginator-navigation-next")
    if not posibles:
        posibles = driver.find_elements(By.XPATH, "//button[contains(@aria-label,'Siguiente') or contains(@aria-label,'Next')]")

    if not posibles:
        return None

    btn = posibles[0]
    disabled = btn.get_attribute("disabled")
    aria_disabled = btn.get_attribute("aria-disabled")
    clase = btn.get_attribute("class") or ""

    if disabled is not None or aria_disabled == "true" or "mat-mdc-button-disabled" in clase:
        return None

    return btn


def guardar_html_debug(driver, nombre_archivo):
    ruta = HTML_DEBUG_DIR / nombre_archivo
    try:
        ruta.write_text(driver.page_source, encoding="utf-8")
        print(f"   📄 HTML debug guardado: {ruta}")
        return str(ruta)
    except Exception as e:
        print(f"   ⚠ No se pudo guardar HTML debug: {e}")
        return ""


# =============================================================================
# EXTRACCIÓN DE TABLA GENERAL
# =============================================================================

def texto_celda(fila, selector_css):
    try:
        return limpiar_texto(fila.find_element(By.CSS_SELECTOR, selector_css).text)
    except Exception:
        return ""


def extraer_metadata_fila_resultado(fila):
    datos = {
        "Codigo": texto_celda(fila, "td.cdk-column-code"),
        "Fecha_envio": texto_celda(fila, "td.cdk-column-date"),
        "Fecha_recepcion": texto_celda(fila, "td.cdk-column-reception-date"),
        "Hora_recepcion": texto_celda(fila, "td.cdk-column-reception-time"),
        "Fecha_resultados": texto_celda(fila, "td.cdk-column-result-date"),
        "Tipo": texto_celda(fila, "td.cdk-column-type"),
        "Entidad_que_remite": texto_celda(fila, "td.cdk-column-entity"),
        "Muestras_recibidas": texto_celda(fila, "td.cdk-column-numeroMuestras"),
        "Muestras_rechazadas": texto_celda(fila, "td.cdk-column-analysisRejected"),
        "Estado": texto_celda(fila, "td.cdk-column-status"),
    }

    if not datos["Codigo"]:
        try:
            tds = [limpiar_texto(td.text) for td in fila.find_elements(By.CSS_SELECTOR, "td")]
            keys = list(datos.keys())
            for i, key in enumerate(keys):
                if i < len(tds):
                    datos[key] = tds[i]
        except Exception:
            pass

    return datos


def consultar_fechas_usuario(user_cfg, fecha_ini_dt=None, fecha_fin_dt=None, tipo_servicio_cfg=None, guardar_debug=False):
    registros = []

    print("\n" + "=" * 70)
    print(f"Consultando fechas disponibles ARO: {user_cfg['nombre']} ({user_cfg['usuario']})")
    print("=" * 70)

    driver = iniciar_driver(headless=True)

    try:
        login(driver, user_cfg)

        driver.get(RESULTADOS_URL)
        WebDriverWait(driver, 30).until(EC.url_contains("/results"))
        time.sleep(2.0)
        print("   🔄 Vista 'Muestras y resultados' cargada.")

        aplicar_filtros_base_resultados(driver, tipo_servicio_cfg=tipo_servicio_cfg)

        try:
            esperar_tabla_con_filas(driver, timeout=25)
        except TimeoutException:
            print("   ⚠ No se encontraron filas en la tabla general.")
            if guardar_debug:
                guardar_html_debug(driver, f"sin_fechas_{normalizar_nombre_carpeta(user_cfg['nombre'])}.html")
            return registros

        set_page_size_50(driver)

        if guardar_debug:
            guardar_html_debug(driver, f"fechas_general_{normalizar_nombre_carpeta(user_cfg['nombre'])}.html")

        pagina = 1

        while True:
            print(f"      📄 Leyendo página {pagina} de resultados generales...")

            try:
                filas = esperar_tabla_con_filas(driver, timeout=20)
            except TimeoutException:
                print("      ⚠ No se encontraron filas en la página actual.")
                break

            total_filas = len(filas)
            print(f"      🔎 Filas visibles: {total_filas}")

            for idx in range(total_filas):
                try:
                    filas_actualizadas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    if idx >= len(filas_actualizadas):
                        continue

                    fila = filas_actualizadas[idx]
                    metadata = extraer_metadata_fila_resultado(fila)

                    fecha_rec = metadata.get("Fecha_recepcion", "")
                    if not fecha_en_rango(fecha_rec, fecha_ini_dt, fecha_fin_dt):
                        continue

                    tipo_cod, tipo_nom = detectar_tipo_servicio_desde_texto(
                        metadata.get("Codigo", ""),
                        metadata.get("Tipo", "")
                    )

                    metadata["ARO"] = user_cfg["nombre"]
                    metadata["Usuario"] = user_cfg["usuario"]
                    metadata["Tipo_servicio_detectado_codigo"] = tipo_cod
                    metadata["Tipo_servicio_detectado_nombre"] = tipo_nom
                    metadata["Pagina"] = pagina
                    metadata["Fila_en_pagina"] = idx + 1
                    metadata["Fecha_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    registros.append(metadata)

                except StaleElementReferenceException:
                    print(f"         ⚠ Fila {idx+1}: referencia obsoleta.")
                    continue
                except Exception as e:
                    print(f"         ⚠ Fila {idx+1}: error no controlado: {e}")
                    continue

            btn_next = pagina_siguiente_disponible(driver)
            if not btn_next:
                break

            try:
                driver.execute_script("arguments[0].click();", btn_next)
                pagina += 1
                time.sleep(1.5)
            except Exception as e:
                print(f"      ⚠ No se pudo avanzar a la página siguiente: {e}")
                break

        print(f"      ✔ Registros dentro del rango: {len(registros)}")

    finally:
        driver.quit()
        print(f"🚪 Navegador cerrado para {user_cfg['nombre']}")

    return registros


# =============================================================================
# ENTRADAS DE USUARIO
# =============================================================================

def solicitar_alcance_resultados():
    print("\nSeleccione alcance de resultados de Agua a consultar:")
    print("  0. TODAS las muestras de AGUA")
    print("  1. MR   - MAPAS DE RIESGOS")
    print("  2. VDM  - VIGILANCIA DE MAPAS")
    print("  3. VIG  - VIGILANCIA RUTINARIA")
    print("  4. DIAG - APOYO DIAGNÓSTICO")
    print("  5. DSAN - DIAGNÓSTICO SANITARIO")

    opcion = input("\nAlcance [0 = TODAS AGUA]: ").strip().upper() or "0"

    codigos = {v["codigo"]: k for k, v in TIPOS_SERVICIO.items()}
    if opcion in codigos:
        opcion = codigos[opcion]

    if opcion == "0":
        print("   ✅ Alcance seleccionado: TODAS AGUA.")
        return None

    if opcion in TIPOS_SERVICIO:
        cfg = TIPOS_SERVICIO[opcion]
        print(f"   ✅ Alcance seleccionado: {cfg['codigo']} - {cfg['nombre']}.")
        return cfg

    print("   ⚠ Alcance no válido. Se usará TODAS AGUA.")
    return None


def solicitar_rango_fechas():
    print("\nIngrese el rango de fechas de recepción a consultar.")
    print("Formato: DD/MM/AAAA")
    print("Ejemplo: 01/01/2026 a 31/01/2026")

    while True:
        fi = input("\nFecha inicial: ").strip()
        ff = input("Fecha final:   ").strip()

        try:
            fi_txt, fi_dt = normalizar_fecha_usuario(fi)
            ff_txt, ff_dt = normalizar_fecha_usuario(ff)
            if ff_dt < fi_dt:
                print("   ⚠ La fecha final no puede ser menor que la inicial.")
                continue

            print(f"   ✅ Rango seleccionado: {fi_txt} a {ff_txt}")
            return fi_dt, ff_dt, fi_txt, ff_txt

        except Exception:
            print("   ⚠ Fechas inválidas. Intente de nuevo.")


def seleccionar_usuarios():
    print("\nSeleccione Área Operativa - ARO / usuario:\n")
    for key, info in USUARIOS.items():
        print(f"  {key}. {info['nombre']} ({info['usuario']})")
    print()

    selec = input("Opción(es) (ej: 1 o 1,2,3): ").strip()
    ids_raw = [s.strip() for s in selec.split(",") if s.strip()]
    ids_validos = [i for i in ids_raw if i in USUARIOS]

    if not ids_validos:
        print("❌ No se seleccionó ningún usuario válido.")
        return []

    print("\nUsuarios seleccionados:")
    for uid in ids_validos:
        print(f"  - {USUARIOS[uid]['nombre']} ({USUARIOS[uid]['usuario']})")

    return ids_validos


# =============================================================================
# EXPORTACIÓN
# =============================================================================

def exportar_salidas(df):
    if df.empty:
        print("⚠ No hay registros para exportar.")
        return None, None

    # Detalle completo.
    detalle_xlsx = SALIDAS_DIR / f"fechas_disponibles_resultados_detalle_lote_{RUN_ID}.xlsx"
    detalle_csv = SALIDAS_DIR / f"fechas_disponibles_resultados_detalle_lote_{RUN_ID}.csv"

    df.to_excel(detalle_xlsx, index=False)
    df.to_csv(detalle_csv, index=False, encoding="utf-8-sig")

    # Resumen por fecha.
    resumen = (
        df.groupby(
            [
                "ARO",
                "Fecha_recepcion",
                "Tipo_servicio_detectado_codigo",
                "Tipo_servicio_detectado_nombre"
            ],
            dropna=False
        )
        .agg(
            Total_resultados=("Codigo", "count"),
            Fecha_resultados_min=("Fecha_resultados", "min"),
            Fecha_resultados_max=("Fecha_resultados", "max")
        )
        .reset_index()
        .sort_values(["ARO", "Fecha_recepcion", "Tipo_servicio_detectado_codigo"])
    )

    resumen_xlsx = SALIDAS_DIR / f"fechas_disponibles_resultados_RESUMEN_lote_{RUN_ID}.xlsx"
    resumen_csv = SALIDAS_DIR / f"fechas_disponibles_resultados_RESUMEN_lote_{RUN_ID}.csv"

    resumen.to_excel(resumen_xlsx, index=False)
    resumen.to_csv(resumen_csv, index=False, encoding="utf-8-sig")

    # Archivos current para el portal.
    resumen.to_csv(OUT_FECHAS_CURRENT_CSV, index=False, encoding="utf-8-sig")
    resumen.to_excel(OUT_FECHAS_CURRENT_XLSX, index=False)
    resumen.to_csv(OUT_RESUMEN_CURRENT_CSV, index=False, encoding="utf-8-sig")

    print("\n📁 Archivos generados:")
    print(f"   Detalle Excel: {detalle_xlsx}")
    print(f"   Detalle CSV:   {detalle_csv}")
    print(f"   Resumen Excel: {resumen_xlsx}")
    print(f"   Resumen CSV:   {resumen_csv}")
    print("\n📁 Archivos current para tablero/proceso:")
    print(f"   {OUT_FECHAS_CURRENT_CSV}")
    print(f"   {OUT_FECHAS_CURRENT_XLSX}")
    print(f"   {OUT_RESUMEN_CURRENT_CSV}")

    return detalle_csv, resumen


def escribir_log(inicio, df, fi_txt, ff_txt, alcance_txt):
    fin = datetime.now()
    duracion = fin - inicio
    log_path = SALIDAS_DIR / "log_detectar_fechas.txt"

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("===== LOG DETECCIÓN FECHAS RESULTADOS AGUA UESVALLE =====\n\n")
        log.write(f"Fecha ejecución: {fin}\n")
        log.write(f"Tiempo total: {duracion}\n")
        log.write(f"Rango consultado: {fi_txt} a {ff_txt}\n")
        log.write(f"Alcance: {alcance_txt}\n")
        log.write(f"Registros detectados: {len(df)}\n")
        log.write(f"Carpeta salida: {SALIDAS_DIR}\n")

    print(f"\n📝 Log generado: {log_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    inicio = datetime.now()

    print("\n" + "=" * 80)
    print("DETECTAR FECHAS DISPONIBLES DE RESULTADOS DE AGUA - UESVALLE")
    print("=" * 80)
    print("Este proceso consulta la tabla general de resultados sin descargar PDF.")
    print("Objetivo: identificar solo las fechas que realmente tienen resultados.")
    print(f"📁 Carpeta de salida del lote: {SALIDAS_DIR}")
    print("=" * 80)

    tipo_servicio_cfg = solicitar_alcance_resultados()
    ids_validos = seleccionar_usuarios()

    if not ids_validos:
        return

    fi_dt, ff_dt, fi_txt, ff_txt = solicitar_rango_fechas()

    guardar_debug = input("\n¿Guardar HTML debug? [N]: ").strip().upper() == "S"

    registros = []

    for uid in ids_validos:
        user_cfg = USUARIOS[uid]
        regs = consultar_fechas_usuario(
            user_cfg=user_cfg,
            fecha_ini_dt=fi_dt,
            fecha_fin_dt=ff_dt,
            tipo_servicio_cfg=tipo_servicio_cfg,
            guardar_debug=guardar_debug
        )
        registros.extend(regs)

    df = pd.DataFrame(registros)

    if df.empty:
        print("\n⚠ No se detectaron resultados en el rango consultado.")
    else:
        exportar_salidas(df)

        print("\n===== RESUMEN FECHAS DISPONIBLES =====")
        resumen_simple = (
            df.groupby(["ARO", "Fecha_recepcion"], dropna=False)
            .size()
            .reset_index(name="Total_resultados")
            .sort_values(["ARO", "Fecha_recepcion"])
        )
        print(resumen_simple.to_string(index=False))

    alcance_txt = "TODAS AGUA"
    if tipo_servicio_cfg:
        alcance_txt = f"{tipo_servicio_cfg.get('codigo')} - {tipo_servicio_cfg.get('nombre')}"

    escribir_log(inicio, df, fi_txt, ff_txt, alcance_txt)

    print("\n✨ PROCESO FINALIZADO ✨")


if __name__ == "__main__":
    main()
