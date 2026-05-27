# -*- coding: utf-8 -*-
"""
SEGUIMIENTO SEMANAL DE MUESTRAS REGISTRADAS DE AGUA - UESVALLE
Versión: V2_Historico
Fecha: 2026-05-26

Objetivo:
- Consultar el módulo:
  https://gestion-muestras.valledelcauca.gov.co/home/simple-list-samples
- NO descarga PDF.
- NO abre fichas una por una.
- NO entra a cada registro.
- Solo lee la tabla inicial "Listado de Muestras Registradas".
- Usa el mismo esquema de usuarios, contraseñas y login del script V7 de descarga de resultados.
- Genera CSV/XLSX para seguimiento semanal de estados de muestras.

Salidas:
  data/resultados_agua/seguimiento_muestras/current/
    seguimiento_muestras_registradas_agua.csv
    seguimiento_muestras_registradas_agua.xlsx
    resumen_estado_muestras.csv
    metadata_seguimiento_muestras.json
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime, timedelta
from pathlib import Path
import re
import time
import unicodedata
import json
import pandas as pd


# ---------------------------------------------------------
#  CONFIGURACIÓN DE USUARIOS / ARO
#  Misma lógica del script V7.
# ---------------------------------------------------------
USUARIOS = {
    "1": {
        "nombre": "Cartago",
        "usuario": "16232927",
        "password": "16232927"
    },
    "2": {
        "nombre": "Tuluá",
        "usuario": "16551281",
        "password": "16551281"
    },
    "3": {
        "nombre": "Cali",
        "usuario": "31641854",
        "password": "31641854"
    }
}

LOGIN_URL = "https://gestion-muestras.valledelcauca.gov.co/login"
LISTADO_URL = "https://gestion-muestras.valledelcauca.gov.co/home/simple-list-samples"

PORTAL_UESVALLE_DIR = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")
OUT_DIR = PORTAL_UESVALLE_DIR / "data" / "resultados_agua" / "seguimiento_muestras" / "current"
HIST_DIR = PORTAL_UESVALLE_DIR / "data" / "resultados_agua" / "seguimiento_muestras" / "historical"
SCRIPT_DIR = PORTAL_UESVALLE_DIR / "scripts" / "resultados_agua" / "04_seguimiento_muestras"
LOG_DIR = SCRIPT_DIR / "logs"

for carpeta in [OUT_DIR, HIST_DIR, SCRIPT_DIR, LOG_DIR]:
    carpeta.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
#  UTILIDADES
# ---------------------------------------------------------
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


def normalizar_aro(texto):
    texto = limpiar_texto(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def parse_fecha(fecha_txt):
    fecha_txt = limpiar_texto(fecha_txt)
    if not fecha_txt:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(fecha_txt, fmt).date()
        except Exception:
            pass
    return None


def extraer_tipo_desde_codigo(codigo):
    codigo = limpiar_texto(codigo).upper()
    m = re.search(r"-(MR|VDM|VIG|DIAG|DSAN)\b", codigo)
    return m.group(1) if m else ""


def clasificar_pendiente(dias, tiene_resultado):
    if tiene_resultado == "SI":
        return "Finalizada"
    if dias is None:
        return "Sin fecha"
    if dias <= 7:
        return "En término"
    if dias <= 15:
        return "En seguimiento"
    if dias <= 30:
        return "Rezago"
    return "Crítico"


def clasificar_respuesta(dias):
    if dias is None:
        return "No calculado"
    if dias <= 7:
        return "Oportuno"
    if dias <= 15:
        return "Normal"
    if dias <= 30:
        return "Tardío"
    return "Crítico"


def texto_celda(fila, selector_css):
    try:
        return limpiar_texto(fila.find_element(By.CSS_SELECTOR, selector_css).text)
    except Exception:
        return ""


# ---------------------------------------------------------
#  DRIVER Y LOGIN
# ---------------------------------------------------------
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
    """
    Mismo patrón de login del script V7:
    input[formcontrolname='username']
    input[formcontrolname='password']
    """
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


# ---------------------------------------------------------
#  FILTROS Y TABLA
# ---------------------------------------------------------
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


def set_page_size(driver, page_size=100):
    """
    Intenta configurar el paginador a 100, 50 o el valor solicitado.
    """
    wait = WebDriverWait(driver, 15)
    page_size = str(page_size)

    try:
        select_page_size = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//mat-paginator//mat-select"))
        )
        driver.execute_script("arguments[0].click();", select_page_size)
        time.sleep(0.5)

        opcion = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[normalize-space()='{page_size}']"))
        )
        driver.execute_script("arguments[0].click();", opcion)
        time.sleep(1.2)
        print(f"   📌 Elementos por página configurados en: {page_size}")
        return True
    except Exception as e:
        print(f"   ⚠ No se pudo cambiar 'Elementos por página' a {page_size}: {e}")
        return False


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


def obtener_texto_paginador(driver):
    for selector in [".mat-mdc-paginator-range-label", ".mat-paginator-range-label"]:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elementos:
                txt = limpiar_texto(el.text)
                if txt:
                    return txt
        except Exception:
            pass
    return ""


def esperar_tabla_con_filas(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    return driver.find_elements(By.CSS_SELECTOR, "table tbody tr")


def ir_a_listado_muestras(driver):
    driver.get(LISTADO_URL)
    WebDriverWait(driver, 30).until(EC.url_contains("simple-list-samples"))
    time.sleep(1.5)
    print("   🔄 Vista 'Listado de Muestras Registradas' cargada.")


def aplicar_filtros_base(driver):
    limpiar_busqueda(driver)
    seleccionar_mat_select_por_label(driver, "Clase de muestra", "Agua", obligatorio=False)
    time.sleep(1.0)


def extraer_fila_listado(fila):
    """
    Extrae datos visibles de una fila del módulo /home/simple-list-samples.
    Usa clases de columnas si están disponibles y fallback por posición.
    """
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
        tds = [limpiar_texto(td.text) for td in fila.find_elements(By.CSS_SELECTOR, "td")]
        tds = [v for v in tds if v != ""]
        keys = list(datos.keys())
        for i, key in enumerate(keys):
            if i < len(tds):
                datos[key] = tds[i]

    return datos


# ---------------------------------------------------------
#  PROCESAMIENTO
# ---------------------------------------------------------
def procesar_aro(user_cfg, dias_rango=15, max_paginas=3, page_size=100, headless=True):
    registros = []

    hoy = datetime.now().date()
    fecha_min = hoy - timedelta(days=dias_rango)

    print("\n" + "=" * 70)
    print(f"Procesando ARO: {user_cfg['nombre']} ({user_cfg['usuario']})")
    print("=" * 70)
    print(f"Rango de revisión: últimos {dias_rango} días")
    print(f"Fecha mínima: {fecha_min.strftime('%d/%m/%Y')}")
    print(f"Máximo páginas: {max_paginas}")
    print("=" * 70)

    driver = iniciar_driver(headless=headless)

    try:
        login(driver, user_cfg)
        ir_a_listado_muestras(driver)
        aplicar_filtros_base(driver)
        set_page_size(driver, page_size)

        pagina = 1
        while pagina <= max_paginas:
            print(f"      📄 Leyendo página {pagina} de listado...")
            paginador = obtener_texto_paginador(driver)
            if paginador:
                print(f"      📍 Paginador: {paginador}")

            try:
                filas = esperar_tabla_con_filas(driver, timeout=25)
            except TimeoutException:
                print("      ⚠ No se encontraron filas.")
                break

            print(f"      🔎 Filas visibles: {len(filas)}")

            fechas_pagina = []

            for idx, fila in enumerate(filas, start=1):
                datos = extraer_fila_listado(fila)

                if not datos.get("Codigo"):
                    continue

                fecha_recepcion = parse_fecha(datos.get("Fecha_recepcion", ""))
                fecha_resultados = parse_fecha(datos.get("Fecha_resultados", ""))

                if fecha_recepcion:
                    fechas_pagina.append(fecha_recepcion)

                # Solo guarda dentro del rango semanal definido.
                if not fecha_recepcion or fecha_recepcion < fecha_min:
                    continue

                dias_desde_recepcion = (hoy - fecha_recepcion).days if fecha_recepcion else None
                dias_respuesta = (fecha_resultados - fecha_recepcion).days if fecha_recepcion and fecha_resultados else None
                tiene_resultado = "SI" if fecha_resultados else "NO"

                registro = {
                    "ARO": normalizar_aro(user_cfg["nombre"]),
                    "USUARIO_ARO": user_cfg["usuario"],
                    "CODIGO_MUESTRA": datos.get("Codigo", ""),
                    "FECHA_ENVIO": datos.get("Fecha_envio", ""),
                    "FECHA_RECEPCION": datos.get("Fecha_recepcion", ""),
                    "HORA_RECEPCION": datos.get("Hora_recepcion", ""),
                    "FECHA_RESULTADOS": datos.get("Fecha_resultados", ""),
                    "TIPO": datos.get("Tipo", ""),
                    "TIPO_CODIGO": extraer_tipo_desde_codigo(datos.get("Codigo", "")),
                    "ENTIDAD_QUE_REMITE": datos.get("Entidad_que_remite", ""),
                    "MUESTRAS_RECIBIDAS": datos.get("Muestras_recibidas", ""),
                    "MUESTRAS_RECHAZADAS": datos.get("Muestras_rechazadas", ""),
                    "ESTADO": datos.get("Estado", ""),
                    "TIENE_RESULTADO": tiene_resultado,
                    "DIAS_DESDE_RECEPCION": dias_desde_recepcion,
                    "DIAS_RESPUESTA": dias_respuesta,
                    "SEMAFORO_PENDIENTE": clasificar_pendiente(dias_desde_recepcion, tiene_resultado),
                    "SEMAFORO_RESPUESTA": clasificar_respuesta(dias_respuesta),
                    "FECHA_CORTE": hoy.strftime("%d/%m/%Y"),
                    "FUENTE": LISTADO_URL,
                    "PAGINA": pagina,
                    "FILA_EN_PAGINA": idx,
                }
                registros.append(registro)

            if fechas_pagina and min(fechas_pagina) < fecha_min:
                print("      🛑 Se encontraron fechas anteriores al rango. Se detiene lectura de este ARO.")
                break

            btn_next = pagina_siguiente_disponible(driver)
            if not btn_next:
                print("      ✅ No hay siguiente página disponible.")
                break

            driver.execute_script("arguments[0].click();", btn_next)
            pagina += 1
            time.sleep(2.0)

    finally:
        driver.quit()
        print(f"🚪 Navegador cerrado para {user_cfg['nombre']}")

    return registros


def exportar_salidas(df, parametros):
    """
    Guarda dos capas de salida:

    1. current/
       Archivos fijos que alimentan el tablero.

    2. historical/
       Copia con timestamp para trazabilidad semanal.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HIST_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    ruta_csv = OUT_DIR / "seguimiento_muestras_registradas_agua.csv"
    ruta_xlsx = OUT_DIR / "seguimiento_muestras_registradas_agua.xlsx"
    ruta_resumen = OUT_DIR / "resumen_estado_muestras.csv"
    ruta_metadata = OUT_DIR / "metadata_seguimiento_muestras.json"

    hist_csv = HIST_DIR / f"seguimiento_muestras_registradas_agua_{run_id}.csv"
    hist_xlsx = HIST_DIR / f"seguimiento_muestras_registradas_agua_{run_id}.xlsx"
    hist_resumen = HIST_DIR / f"resumen_estado_muestras_{run_id}.csv"
    hist_metadata = HIST_DIR / f"metadata_seguimiento_muestras_{run_id}.json"

    if not df.empty:
        df["_FECHA_ORDEN"] = pd.to_datetime(df["FECHA_RECEPCION"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(["_FECHA_ORDEN", "ARO", "CODIGO_MUESTRA"], ascending=[False, True, True])
        df = df.drop(columns=["_FECHA_ORDEN"])

    # Salida current: reemplaza última corrida.
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    df.to_excel(ruta_xlsx, index=False)

    # Salida historical: conserva evidencia de la corrida.
    df.to_csv(hist_csv, index=False, encoding="utf-8-sig")
    df.to_excel(hist_xlsx, index=False)

    if not df.empty:
        resumen = (
            df.groupby(["ARO", "ESTADO", "TIENE_RESULTADO", "SEMAFORO_PENDIENTE"], dropna=False)
            .size()
            .reset_index(name="TOTAL")
            .sort_values(["ARO", "ESTADO", "SEMAFORO_PENDIENTE"])
        )
    else:
        resumen = pd.DataFrame(columns=["ARO", "ESTADO", "TIENE_RESULTADO", "SEMAFORO_PENDIENTE", "TOTAL"])

    resumen.to_csv(ruta_resumen, index=False, encoding="utf-8-sig")
    resumen.to_csv(hist_resumen, index=False, encoding="utf-8-sig")

    metadata = {
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_id": run_id,
        "version_script": "V2_Historico",
        "total_registros": int(len(df)),
        "total_con_resultado": int((df["TIENE_RESULTADO"] == "SI").sum()) if not df.empty else 0,
        "total_sin_resultado": int((df["TIENE_RESULTADO"] == "NO").sum()) if not df.empty else 0,
        "parametros": parametros,
        "salidas_current": {
            "seguimiento_csv": str(ruta_csv),
            "seguimiento_xlsx": str(ruta_xlsx),
            "resumen_csv": str(ruta_resumen),
            "metadata_json": str(ruta_metadata),
        },
        "salidas_historical": {
            "seguimiento_csv": str(hist_csv),
            "seguimiento_xlsx": str(hist_xlsx),
            "resumen_csv": str(hist_resumen),
            "metadata_json": str(hist_metadata),
        }
    }

    ruta_metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    hist_metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n📁 Archivos current actualizados:")
    print(f"   📄 {ruta_csv}")
    print(f"   📄 {ruta_xlsx}")
    print(f"   📄 {ruta_resumen}")
    print(f"   📄 {ruta_metadata}")

    print("\n🗄️ Copia histórica guardada:")
    print(f"   📄 {hist_csv}")
    print(f"   📄 {hist_xlsx}")
    print(f"   📄 {hist_resumen}")
    print(f"   📄 {hist_metadata}")

def main():
    inicio = datetime.now()

    print("\n" + "=" * 80)
    print("SEGUIMIENTO SEMANAL DE MUESTRAS REGISTRADAS DE AGUA - UESVALLE V2")
    print("=" * 80)
    print("Este proceso NO descarga PDF y NO abre fichas.")
    print("Solo lee la tabla inicial del módulo Listado de Muestras Registradas.")
    print("=" * 80)

    print("\nSeleccione Área Operativa - ARO / usuario:\n")
    for key, info in USUARIOS.items():
        print(f"  {key}. {info['nombre']} ({info['usuario']})")
    print("  0. Todas")
    print()

    selec = input("Opción(es) [0 = todas, ej: 1 o 1,2,3]: ").strip() or "0"
    if selec == "0":
        ids_validos = list(USUARIOS.keys())
    else:
        ids_raw = [s.strip() for s in selec.split(",") if s.strip()]
        ids_validos = [i for i in ids_raw if i in USUARIOS]

    if not ids_validos:
        print("❌ No se seleccionó ningún usuario válido. Saliendo...")
        return

    dias_rango = int(input("\nRango de revisión en días [15]: ").strip() or "15")
    max_paginas = int(input("Máximo de páginas por ARO [3]: ").strip() or "3")
    page_size = int(input("Registros por página [100]: ").strip() or "100")
    headless_txt = input("Ejecutar en modo oculto/headless? [S]: ").strip().upper() or "S"
    headless = headless_txt == "S"

    print("\nUsuarios seleccionados:")
    for uid in ids_validos:
        print(f"  - {USUARIOS[uid]['nombre']} ({USUARIOS[uid]['usuario']})")

    confirmar = input("\n¿Continuar con el seguimiento semanal? [S/N]: ").strip().upper()
    if confirmar != "S":
        print("Proceso cancelado.")
        return

    todos = []
    for uid in ids_validos:
        user_cfg = USUARIOS[uid]
        registros = procesar_aro(
            user_cfg,
            dias_rango=dias_rango,
            max_paginas=max_paginas,
            page_size=page_size,
            headless=headless
        )
        todos.extend(registros)

    df = pd.DataFrame(todos)

    print("\n" + "=" * 80)
    print("RESUMEN FINAL DE SEGUIMIENTO")
    print("=" * 80)
    print(f"🕒 Tiempo total: {str(datetime.now() - inicio).split('.')[0]}")
    print(f"📌 Registros dentro del rango: {len(df)}")

    if not df.empty:
        print("\nResumen por ARO y estado:")
        resumen_print = df.groupby(["ARO", "ESTADO"]).size().reset_index(name="TOTAL")
        print(resumen_print.to_string(index=False))

    parametros = {
        "aros": [USUARIOS[i]["nombre"] for i in ids_validos],
        "dias_rango": dias_rango,
        "max_paginas": max_paginas,
        "page_size": page_size,
        "headless": headless,
        "url": LISTADO_URL,
        "duracion_segundos": round((datetime.now() - inicio).total_seconds(), 2)
    }

    exportar_salidas(df, parametros)

    print("\n✨ PROCESO FINALIZADO ✨")


if __name__ == "__main__":
    main()
