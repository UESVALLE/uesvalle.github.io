# -*- coding: utf-8 -*-
"""
DESCARGA DE MUESTRAS Y RESULTADOS PDF - UESVALLE
Versión: MANUAL_FECHAS_ESTABLE
Fecha: 2026-05-26

Actualización principal:
- Mantiene el flujo existente de consulta por ARO y fecha.
- Agrega descarga automática de resultados PDF desde la página:
  https://gestion-muestras.valledelcauca.gov.co/results
- Conserva el nombre original del PDF generado por la plataforma.
- Organiza los PDF por año y ARO: PDFs_Resultados/2026/Cartago, Cali o Tulua.
- Genera control de descargas en Excel/CSV.
- Permite ejecutar:
    1) Solo fichas de muestra
    2) Solo PDF de resultados
    3) Fichas + PDF de resultados
- Permite alcance 0: solo Agua, o 1-5: filtrar una clasificación específica.

Notas:
- El selector del botón PDF se basa en el HTML revisado:
  button[mattooltip*='Descargar resultado']
- Para conservar el nombre original del PDF, el script NO renombra el archivo descargado.
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
import shutil
import unicodedata
import pandas as pd


# ---------------------------------------------------------
#  CONFIGURACIÓN DE USUARIOS / MUNICIPIOS
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

# ---------------------------------------------------------
#  CLASIFICACIÓN OPCIONAL DE RESULTADOS DE AGUA
# ---------------------------------------------------------
# Opción 0: NO aplica Tipo de servicio. Solo Clase de muestra = Agua.
# Opciones 1-5: aplican Tipo de servicio para reducir tiempo de procesamiento.
TIPOS_SERVICIO = {
    "1": {
        "codigo": "MR",
        "nombre": "MAPAS DE RIESGOS",
        "valor_select": "MAPAS DE RIESGOS"
    },
    "2": {
        "codigo": "VDM",
        "nombre": "VIGILANCIA DE MAPAS",
        "valor_select": "VIGILANCIA DE MAPAS"
    },
    "3": {
        "codigo": "VIG",
        "nombre": "VIGILANCIA RUTINARIA",
        "valor_select": "VIGILANCIA RUTINARIA"
    },
    "4": {
        "codigo": "DIAG",
        "nombre": "APOYO DIAGNÓSTICO",
        "valor_select": "APOYO DIAGNÓSTICO"
    },
    "5": {
        "codigo": "DSAN",
        "nombre": "DIAGNÓSTICO SANITARIO",
        "valor_select": "DIAGNÓSTICO SANITARIO"
    }
}

LOGIN_URL = "https://gestion-muestras.valledelcauca.gov.co/login"
LISTADO_URL = "https://gestion-muestras.valledelcauca.gov.co/home/simple-list-samples"
RESULTADOS_URL = "https://gestion-muestras.valledelcauca.gov.co/results"

# ---------------------------------------------------------
#  RUTAS INSTITUCIONALES UESVALLE
# ---------------------------------------------------------
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M")

# Carpeta del portal UESVALLE: aquí deben ubicarse tablero, scripts y CSV operativos.
PORTAL_UESVALLE_DIR = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

# Carpeta documental oficial del proceso Agua para Consumo: aquí quedan los PDF y controles de descarga.
REPOSITORIO_RESULTADOS_DIR = Path(
    r"G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras"
)

# Salidas documentales del proceso de descarga.
PDFS_DIR = REPOSITORIO_RESULTADOS_DIR / "PDF_Resultados"
CONTROL_DESCARGAS_DIR = REPOSITORIO_RESULTADOS_DIR / "Control_Descargas"
LOGS_DIR = REPOSITORIO_RESULTADOS_DIR / "Logs"

# Cada ejecución queda trazada en un lote de control, pero los PDF quedan consolidados en PDF_Resultados.
SALIDAS_DIR = CONTROL_DESCARGAS_DIR / f"Lote_{RUN_ID}"
TEMP_DOWNLOAD_DIR = SALIDAS_DIR / "_tmp_descargas_chrome"
HTML_DEBUG_DIR = SALIDAS_DIR / "HTML_Debug"

# Carpetas del módulo en el portal. Se crean para dejar lista la estructura del tablero.
PORTAL_DATA_DIR = PORTAL_UESVALLE_DIR / "data" / "resultados_agua" / "current"
PORTAL_SCRIPTS_DIR = PORTAL_UESVALLE_DIR / "scripts" / "resultados_agua"
PORTAL_DASHBOARD_DIR = PORTAL_UESVALLE_DIR / "dashboards" / "resultados_agua"

for carpeta in [
    REPOSITORIO_RESULTADOS_DIR, PDFS_DIR, CONTROL_DESCARGAS_DIR, LOGS_DIR,
    SALIDAS_DIR, TEMP_DOWNLOAD_DIR, HTML_DEBUG_DIR,
    PORTAL_DATA_DIR, PORTAL_SCRIPTS_DIR, PORTAL_DASHBOARD_DIR
]:
    carpeta.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
#  UTILIDADES GENERALES
# ---------------------------------------------------------
def limpiar_texto(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def normalizar_nombre_carpeta(texto):
    """
    Devuelve un nombre de carpeta seguro para Windows.
    Conserva legibilidad y elimina caracteres problemáticos.
    """
    texto = limpiar_texto(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace(" ", "_")
    texto = re.sub(r"[^\w\-\.]", "_", texto, flags=re.UNICODE)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto or "SIN_DATO"


def normalizar_fecha_usuario(fecha_raw: str):
    """
    Recibe fecha en dd/mm/aaaa o dd-mm-aaaa.
    Devuelve:
      - fecha_input: yyyy-mm-dd (para el input HTML)
      - fecha_tabla: dd/mm/aaaa (como se ve en la tabla)
      - dt: datetime
    """
    f = fecha_raw.strip().replace("-", "/")
    dt = datetime.strptime(f, "%d/%m/%Y")
    fecha_input = dt.strftime("%Y-%m-%d")
    fecha_tabla = dt.strftime("%d/%m/%Y")
    return fecha_input, fecha_tabla, dt


def anio_desde_fecha_o_nombre(fecha_resultado="", nombre_pdf=""):
    """
    Prioriza el año del nombre del PDF si inicia con AAAA.
    Si no, usa la fecha visible de resultados o recepción.
    """
    nombre_pdf = limpiar_texto(nombre_pdf)
    m = re.match(r"^(20\d{2})", nombre_pdf)
    if m:
        return m.group(1)

    fecha_resultado = limpiar_texto(fecha_resultado)
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(fecha_resultado, fmt).strftime("%Y")
        except Exception:
            pass

    return datetime.now().strftime("%Y")


def listar_archivos_recursivo(base_dir: Path):
    if not base_dir.exists():
        return []
    return [p for p in base_dir.rglob("*") if p.is_file()]


# ---------------------------------------------------------
#  DRIVER
# ---------------------------------------------------------
def iniciar_driver(download_dir: Path = TEMP_DOWNLOAD_DIR, headless=True):
    """
    Crea driver de Chrome con descargas automáticas a download_dir.
    Se fuerza que los PDF no se abran en el visor interno de Chrome.
    """
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    prefs = {
        "download.default_directory": str(download_dir.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=service, options=options)

    # Refuerzo para descargas en modo headless.
    try:
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(download_dir.resolve())}
        )
    except Exception:
        pass

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


def aplicar_filtro_fecha(driver, fecha_input, label="Fecha de recepción"):
    """
    Aplica fecha a un mat-form-field por etiqueta.
    """
    wait = WebDriverWait(driver, 30)
    input_el = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//mat-form-field[.//mat-label[contains(., '{label}')]]//input")
        )
    )

    script_js = """
    const el = arguments[0];
    const val = arguments[1];
    el.removeAttribute('readonly');
    el.focus();
    el.value = '';
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.value = val;
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
    """
    driver.execute_script(script_js, input_el, fecha_input)
    input_el.send_keys(Keys.ENTER)
    print(f"   📅 Filtro aplicado: {label} = {fecha_input}")
    time.sleep(1.0)


def seleccionar_mat_select_por_label(driver, label, valor, obligatorio=False):
    """
    Selecciona un valor en un mat-select localizando el campo por mat-label.
    Funciona para 'Clase de muestra', 'Tipo de servicio' y 'Estado'.
    """
    wait = WebDriverWait(driver, 20)

    try:
        campo = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//mat-form-field[.//mat-label[contains(., '{label}')]]")
            )
        )

        # Si ya tiene el valor, no se cambia.
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


def aplicar_filtros_base_resultados(driver, fecha_input, estado="FINALIZADA", tipo_servicio_cfg=None):
    """
    Filtros para la página de resultados PDF.

    Regla principal:
      - Siempre intenta aplicar Clase de muestra = Agua.
      - Si tipo_servicio_cfg es None, NO aplica Tipo de servicio.
      - Si tipo_servicio_cfg viene informado, aplica Tipo de servicio para reducir tiempo.
    """
    limpiar_busqueda(driver)

    # Clase de muestra Agua: este filtro trae internamente todas las clasificaciones de agua.
    seleccionar_mat_select_por_label(driver, "Clase de muestra", "Agua", obligatorio=False)

    # Filtro opcional por clasificación de agua.
    if tipo_servicio_cfg:
        seleccionar_mat_select_por_label(
            driver,
            "Tipo de servicio",
            tipo_servicio_cfg.get("valor_select", ""),
            obligatorio=False
        )
        print(f"   🎯 Alcance específico: {tipo_servicio_cfg.get('codigo')} - {tipo_servicio_cfg.get('nombre')}")
    else:
        print("   🎯 Alcance: TODAS las muestras de AGUA, sin filtrar por Tipo de servicio.")

    # Filtro principal solicitado: Fecha de recepción.
    aplicar_filtro_fecha(driver, fecha_input, label="Fecha de recepción")

    # Estado finalizada.
    seleccionar_mat_select_por_label(driver, "Estado", estado, obligatorio=False)

    time.sleep(1.5)


def aplicar_filtros_base_fichas(driver, fecha_input):
    """
    Filtros para el listado de fichas de muestra.
    """
    limpiar_busqueda(driver)
    aplicar_filtro_fecha(driver, fecha_input, label="Fecha de recepción")
    seleccionar_mat_select_por_label(driver, "Clase de muestra", "Agua", obligatorio=False)
    time.sleep(1.0)


def esperar_fecha_en_tabla(driver, fecha_tabla, timeout=40):
    wait = WebDriverWait(driver, timeout)
    print(f"   ⏳ Esperando registros con fecha visible: {fecha_tabla} ...")
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//table//tbody//tr//td[contains(., '{fecha_tabla}')]")
        )
    )
    print("   ✔ Fecha encontrada en la tabla.")


def esperar_tabla_con_filas(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )
    filas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    return filas


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
    """
    Devuelve el botón de siguiente página si está habilitado.
    """
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


# ---------------------------------------------------------
#  EXTRACCIÓN DE FILAS DE RESULTADOS
# ---------------------------------------------------------
def texto_celda(fila, selector_css):
    try:
        return limpiar_texto(fila.find_element(By.CSS_SELECTOR, selector_css).text)
    except Exception:
        return ""


def extraer_metadata_fila_resultado(fila):
    """
    Extrae metadata visible de una fila de la página /results.
    Usa clases generadas por Angular Material.
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

    # Fallback por posiciones si las clases cambian.
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


# ---------------------------------------------------------
#  DESCARGA PDF
# ---------------------------------------------------------
def esperar_descarga_pdf(carpeta: Path, archivos_antes, timeout=90):
    """
    Espera un PDF nuevo en la carpeta de descargas.
    Ignora archivos temporales .crdownload.
    Retorna Path del PDF descargado o None.
    """
    inicio = time.time()

    while time.time() - inicio < timeout:
        archivos_actuales = set(p.name for p in carpeta.iterdir() if p.is_file())
        nuevos = archivos_actuales - archivos_antes

        temporales = [a for a in nuevos if a.lower().endswith(".crdownload")]
        pdfs = [a for a in nuevos if a.lower().endswith(".pdf")]

        # También puede ocurrir que un temporal se convierta a PDF.
        if pdfs and not temporales:
            # Si hay varios, toma el más reciente.
            rutas_pdf = [carpeta / p for p in pdfs]
            rutas_pdf = sorted(rutas_pdf, key=lambda p: p.stat().st_mtime, reverse=True)
            return rutas_pdf[0]

        time.sleep(1)

    return None


def resolver_destino_sin_sobrescribir(destino: Path):
    """
    Evita sobrescribir si ya existe. Conserva el nombre base y agrega sufijo.
    """
    if not destino.exists():
        return destino

    base = destino.stem
    ext = destino.suffix
    parent = destino.parent

    for i in range(1, 1000):
        candidato = parent / f"{base}_duplicado_{i:02d}{ext}"
        if not candidato.exists():
            return candidato

    raise RuntimeError(f"No se pudo resolver nombre sin sobrescribir para: {destino}")


def detectar_tipo_servicio_desde_texto(*valores):
    """
    Detecta MR, VDM, VIG, DIAG o DSAN desde código, tipo o nombre del PDF.
    No afecta la carpeta de salida; solo alimenta el Excel de control.
    """
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


def descargar_pdf_resultado(driver, fila, user_cfg, metadata_fila):
    """
    Descarga el PDF desde la fila actual.
    Conserva el nombre original descargado por la plataforma.
    Devuelve dict con estado de la descarga.
    """
    registro = dict(metadata_fila)
    registro["ARO"] = user_cfg["nombre"]
    registro["Usuario"] = user_cfg["usuario"]
    registro["Descargado"] = "NO"
    registro["Nombre_PDF"] = ""
    registro["Ruta_PDF"] = ""
    tipo_cod_ini, tipo_nom_ini = detectar_tipo_servicio_desde_texto(
        metadata_fila.get("Codigo", ""),
        metadata_fila.get("Tipo", "")
    )
    registro["Tipo_servicio_detectado_codigo"] = tipo_cod_ini
    registro["Tipo_servicio_detectado_nombre"] = tipo_nom_ini
    registro["Estado_descarga"] = ""
    registro["Error"] = ""

    try:
        boton_pdf = fila.find_element(By.CSS_SELECTOR, "button[mattooltip*='Descargar resultado']")
    except Exception:
        try:
            boton_pdf = fila.find_element(By.XPATH, ".//button[.//mat-icon[normalize-space()='picture_as_pdf']]")
        except Exception as e:
            registro["Estado_descarga"] = "SIN_BOTON_PDF"
            registro["Error"] = str(e)
            return registro

    archivos_antes = set(p.name for p in TEMP_DOWNLOAD_DIR.iterdir() if p.is_file())

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", boton_pdf)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", boton_pdf)

        pdf_tmp = esperar_descarga_pdf(TEMP_DOWNLOAD_DIR, archivos_antes, timeout=90)

        if not pdf_tmp:
            registro["Estado_descarga"] = "TIMEOUT_DESCARGA"
            registro["Error"] = "No apareció un PDF nuevo en la carpeta temporal."
            return registro

        nombre_original = pdf_tmp.name
        anio = anio_desde_fecha_o_nombre(
            fecha_resultado=metadata_fila.get("Fecha_resultados", "") or metadata_fila.get("Fecha_recepcion", ""),
            nombre_pdf=nombre_original
        )

        # Salida solicitada: primero año y luego ARO.
        # No se crean carpetas por MR, VDM, VIG, DIAG o DSAN porque el nombre del PDF ya lo contiene.
        carpeta_destino = PDFS_DIR / anio / normalizar_nombre_carpeta(user_cfg["nombre"])
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        tipo_cod, tipo_nom = detectar_tipo_servicio_desde_texto(
            metadata_fila.get("Codigo", ""),
            metadata_fila.get("Tipo", ""),
            nombre_original
        )
        registro["Tipo_servicio_detectado_codigo"] = tipo_cod
        registro["Tipo_servicio_detectado_nombre"] = tipo_nom

        destino = carpeta_destino / nombre_original
        destino = resolver_destino_sin_sobrescribir(destino)

        shutil.move(str(pdf_tmp), str(destino))

        registro["Descargado"] = "SI"
        registro["Nombre_PDF"] = destino.name
        registro["Ruta_PDF"] = str(destino)
        registro["Estado_descarga"] = "OK"

        print(f"         📥 PDF descargado: {destino.name}")

    except Exception as e:
        registro["Estado_descarga"] = "ERROR"
        registro["Error"] = str(e)
        print(f"         ⚠ Error descargando PDF {metadata_fila.get('Codigo', '')}: {e}")

    return registro


# ---------------------------------------------------------
#  PROCESAR RESULTADOS PDF
# ---------------------------------------------------------
def procesar_resultados_pdf_fecha(driver, user_cfg, fecha_input, fecha_tabla, tipo_servicio_cfg=None, guardar_debug=False):
    """
    Procesa todas las páginas de resultados para una fecha.
    """
    registros = []

    driver.get(RESULTADOS_URL)
    WebDriverWait(driver, 30).until(EC.url_contains("/results"))
    time.sleep(2.0)
    print("   🔄 Vista 'Muestras y resultados' cargada.")

    aplicar_filtros_base_resultados(driver, fecha_input, tipo_servicio_cfg=tipo_servicio_cfg)

    try:
        esperar_fecha_en_tabla(driver, fecha_tabla, timeout=25)
    except TimeoutException:
        print(f"   ⚠ No se encontraron resultados PDF para la fecha {fecha_tabla}.")
        if guardar_debug:
            guardar_html_debug(driver, f"sin_resultados_{normalizar_nombre_carpeta(user_cfg['nombre'])}_{fecha_tabla.replace('/', '-')}.html")
        return registros

    set_page_size_50(driver)

    if guardar_debug:
        guardar_html_debug(driver, f"resultados_{normalizar_nombre_carpeta(user_cfg['nombre'])}_{fecha_tabla.replace('/', '-')}.html")

    pagina = 1

    while True:
        print(f"      📄 Procesando página {pagina} de resultados...")

        try:
            filas = esperar_tabla_con_filas(driver, timeout=20)
        except TimeoutException:
            print("      ⚠ No se encontraron filas en la página actual.")
            break

        total_filas = len(filas)
        print(f"      🔎 Filas visibles: {total_filas}")

        # Iteración por índice para recuperar la fila si Angular refresca el DOM.
        for idx in range(total_filas):
            try:
                filas_actualizadas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if idx >= len(filas_actualizadas):
                    continue

                fila = filas_actualizadas[idx]
                metadata = extraer_metadata_fila_resultado(fila)
                metadata["Fecha_filtro_recepcion"] = fecha_tabla
                metadata["Pagina"] = pagina
                metadata["Fila_en_pagina"] = idx + 1

                if not metadata.get("Codigo"):
                    print(f"         ⚠ Fila {idx+1}: sin código, se omite.")
                    continue

                print(f"         ➜ {idx+1}/{total_filas} | {metadata.get('Codigo')} | {metadata.get('Estado')}")

                registro = descargar_pdf_resultado(driver, fila, user_cfg, metadata)
                registros.append(registro)

                # Pequeña pausa para evitar saturar la aplicación.
                time.sleep(0.7)

            except StaleElementReferenceException:
                print(f"         ⚠ Fila {idx+1}: referencia obsoleta, se continúa.")
                continue
            except Exception as e:
                print(f"         ⚠ Fila {idx+1}: error no controlado: {e}")
                registros.append({
                    "ARO": user_cfg["nombre"],
                    "Fecha_filtro_recepcion": fecha_tabla,
                    "Pagina": pagina,
                    "Fila_en_pagina": idx + 1,
                    "Descargado": "NO",
                    "Estado_descarga": "ERROR_FILA",
                    "Error": str(e)
                })

        btn_next = pagina_siguiente_disponible(driver)
        if not btn_next:
            break

        try:
            driver.execute_script("arguments[0].click();", btn_next)
            pagina += 1
            time.sleep(2.0)
        except Exception as e:
            print(f"      ⚠ No se pudo avanzar a la página siguiente: {e}")
            break

    print(f"      ✔ Fecha {fecha_tabla}: registros de descarga generados: {len(registros)}")
    return registros


# ---------------------------------------------------------
#  FUNCIONES ORIGINALES: FICHAS DE MUESTRA
# ---------------------------------------------------------
def extraer_campos_muestra(driver):
    """
    Extrae campos de la ficha de muestra.
    Se conserva del flujo original para no perder funcionalidad.
    """
    wait = WebDriverWait(driver, 20)
    datos = {}

    try:
        campos = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "mat-form-field"))
        )
    except TimeoutException:
        print("      ⚠ No se pudieron leer los campos de la ficha.")
        return {}

    muni_count = 0
    depto_count = 0
    label_counts = {}

    for campo in campos:
        try:
            label_el = campo.find_element(By.CSS_SELECTOR, "mat-label")
            label = limpiar_texto(label_el.text)
        except Exception:
            continue

        valor = ""
        for selector in ["input", "textarea", "span.mat-mdc-select-min-line", "span.mat-mdc-select-value-text", ".mat-mdc-select-value"]:
            try:
                el = campo.find_element(By.CSS_SELECTOR, selector)
                valor = limpiar_texto(el.get_attribute("value") if selector in ["input", "textarea"] else el.text)
                if valor:
                    break
            except Exception:
                pass

        base_label = label.replace("*", "").strip()

        if "Municipio" in base_label:
            muni_count += 1
            key = {
                1: "Municipio_punto_muestreo",
                2: "Municipio_acueducto",
                3: "Municipio_entidad_remite",
            }.get(muni_count, f"Municipio_{muni_count}")
        elif "Departamento" in base_label:
            depto_count += 1
            key = {
                1: "Departamento_punto_muestreo",
                2: "Departamento_acueducto",
                3: "Departamento_entidad_remite",
            }.get(depto_count, f"Departamento_{depto_count}")
        else:
            count = label_counts.get(base_label, 0)
            key = base_label if count == 0 else f"{base_label}_{count+1}"
            label_counts[base_label] = count + 1

        datos[key] = valor

    return datos


def procesar_muestras_fichas_fecha(driver, user_cfg, fecha_input, fecha_tabla):
    """
    Procesa fichas de muestra desde /home/simple-list-samples.
    Mantiene la lógica base del script anterior.
    """
    resultados = []

    driver.get(LISTADO_URL)
    WebDriverWait(driver, 30).until(EC.url_contains("simple-list-samples"))
    time.sleep(1.5)
    print("   🔄 Vista 'Listado de muestras registradas' cargada.")

    aplicar_filtros_base_fichas(driver, fecha_input)

    try:
        esperar_fecha_en_tabla(driver, fecha_tabla, timeout=25)
    except TimeoutException:
        print(f"   ⚠ No se encontraron fichas para la fecha {fecha_tabla}.")
        return resultados

    set_page_size_50(driver)

    pagina = 1

    while True:
        print(f"      📄 Procesando página {pagina} de fichas...")

        try:
            filas = esperar_tabla_con_filas(driver, timeout=20)
        except TimeoutException:
            break

        total_filas = len(filas)

        for idx in range(total_filas):
            try:
                filas_actualizadas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if idx >= len(filas_actualizadas):
                    continue

                fila = filas_actualizadas[idx]

                try:
                    boton_ver = fila.find_element(By.CSS_SELECTOR, "a[mattooltip='Ver datos de la muestra']")
                except Exception:
                    boton_ver = fila.find_element(By.XPATH, ".//*[contains(@mattooltip,'Ver datos de la muestra') or .//mat-icon[normalize-space()='remove_red_eye']]")

                driver.execute_script("arguments[0].click();", boton_ver)
                time.sleep(1.0)

                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2.0)

                datos = extraer_campos_muestra(driver)

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                if datos:
                    datos["Fecha filtro (recepción)"] = fecha_tabla
                    datos["ARO"] = user_cfg["nombre"]
                    resultados.append(datos)
                    print(f"         ✔ Ficha {idx+1}/{total_filas}")
                else:
                    print(f"         ⚠ Ficha {idx+1}/{total_filas} sin datos")

            except Exception as e:
                print(f"         ⚠ Error procesando ficha {idx+1}: {e}")
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass

        btn_next = pagina_siguiente_disponible(driver)
        if not btn_next:
            break

        try:
            driver.execute_script("arguments[0].click();", btn_next)
            pagina += 1
            time.sleep(2.0)
        except Exception:
            break

    return resultados


# ---------------------------------------------------------
#  EXPORTACIÓN
# ---------------------------------------------------------
def exportar_dataframe(df, nombre_base):
    if df is None or df.empty:
        print(f"⚠ No hay datos para exportar: {nombre_base}")
        return None

    xlsx_name = SALIDAS_DIR / f"{nombre_base}.xlsx"
    csv_name = SALIDAS_DIR / f"{nombre_base}.csv"

    df.to_excel(xlsx_name, index=False)
    df.to_csv(csv_name, index=False, encoding="utf-8-sig")

    print(f"📁 Excel generado: {xlsx_name}")
    print(f"📁 CSV generado:   {csv_name}")
    return df


def generar_resumen_descargas(df_control, nombre_base="resumen_descargas_resultados"):
    if df_control is None or df_control.empty:
        print("⚠ No hay control de descargas para resumir.")
        return None

    cols_group = ["ARO", "Fecha_filtro_recepcion", "Estado_descarga", "Descargado"]
    for col in cols_group:
        if col not in df_control.columns:
            df_control[col] = ""

    resumen = (
        df_control
        .groupby(cols_group, dropna=False)
        .size()
        .reset_index(name="Total")
        .sort_values(["ARO", "Fecha_filtro_recepcion", "Estado_descarga"])
    )

    exportar_dataframe(resumen, nombre_base)
    print("\n===== RESUMEN DESCARGAS PDF =====")
    print(resumen.to_string(index=False))
    return resumen


def generar_resumen_fichas(df_fichas, nombre_base="resumen_fichas"):
    if df_fichas is None or df_fichas.empty:
        return None

    if "ARO" not in df_fichas.columns or "Fecha filtro (recepción)" not in df_fichas.columns:
        return None

    resumen = (
        df_fichas
        .groupby(["ARO", "Fecha filtro (recepción)"])
        .size()
        .reset_index(name="Total_registros")
        .sort_values(["ARO", "Fecha filtro (recepción)"])
    )
    exportar_dataframe(resumen, nombre_base)
    return resumen


def escribir_log(inicio_global, modo, dfs_info=None):
    fin = datetime.now()
    duracion = fin - inicio_global

    log_path = SALIDAS_DIR / "log.txt"
    archivos = listar_archivos_recursivo(SALIDAS_DIR)

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("===== LOG DE EJECUCIÓN SCRIPT MUESTREO UESVALLE V2 =====\n\n")
        log.write(f"Fecha de ejecución: {fin}\n")
        log.write(f"Tiempo total: {duracion}\n")
        log.write(f"Modo ejecutado: {modo}\n")
        log.write(f"Carpeta de salida: {SALIDAS_DIR}\n\n")
        log.write("Archivos generados:\n")
        for p in archivos:
            log.write(f" - {p.relative_to(SALIDAS_DIR)}\n")

        if dfs_info:
            log.write("\nResumen técnico:\n")
            for k, v in dfs_info.items():
                log.write(f" - {k}: {v}\n")

    print("\n📝 Log generado en:")
    print(f"   ➤ {log_path}")


# ---------------------------------------------------------
#  PROCESAR USUARIO
# ---------------------------------------------------------
def procesar_usuario(user_cfg, fechas, modo, tipo_servicio_cfg=None, guardar_debug=False):
    """
    modo:
      1 = fichas
      2 = PDF resultados
      3 = fichas + PDF resultados
    """
    print("\n" + "=" * 70)
    print(f"Procesando ARO: {user_cfg['nombre']} ({user_cfg['usuario']})")
    print("=" * 70)

    driver = iniciar_driver(TEMP_DOWNLOAD_DIR, headless=True)

    fichas_usuario = []
    descargas_usuario = []

    try:
        login(driver, user_cfg)

        for fecha_input, fecha_tabla, _ in fechas:
            print(f"\n=== Fecha de recepción: {fecha_tabla} ===")

            if modo in ["1", "3"]:
                print("\n--- Módulo 1: extracción de fichas ---")
                datos_fichas = procesar_muestras_fichas_fecha(driver, user_cfg, fecha_input, fecha_tabla)
                fichas_usuario.extend(datos_fichas)

            if modo in ["2", "3"]:
                print("\n--- Módulo 2: descarga PDF de resultados ---")
                registros_pdf = procesar_resultados_pdf_fecha(
                    driver,
                    user_cfg,
                    fecha_input,
                    fecha_tabla,
                    tipo_servicio_cfg=tipo_servicio_cfg,
                    guardar_debug=guardar_debug
                )
                descargas_usuario.extend(registros_pdf)

    finally:
        driver.quit()
        print(f"🚪 Navegador cerrado para {user_cfg['nombre']}")

    return fichas_usuario, descargas_usuario


# ---------------------------------------------------------
#  SELECCIÓN DE ALCANCE
# ---------------------------------------------------------
def solicitar_alcance_resultados():
    """
    Devuelve None para TODAS AGUA o dict TIPOS_SERVICIO para una clasificación específica.
    """
    print("\nSeleccione alcance de resultados de Agua a procesar:")
    print("  0. TODAS las muestras de AGUA (sin filtrar Tipo de servicio)")
    print("  1. MR   - MAPAS DE RIESGOS")
    print("  2. VDM  - VIGILANCIA DE MAPAS")
    print("  3. VIG  - VIGILANCIA RUTINARIA")
    print("  4. DIAG - APOYO DIAGNÓSTICO")
    print("  5. DSAN - DIAGNÓSTICO SANITARIO")

    opcion = input("\nAlcance [0 = TODAS AGUA]: ").strip().upper() or "0"

    # Permite digitar el código directamente.
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


# ---------------------------------------------------------
#  FLUJO PRINCIPAL
# ---------------------------------------------------------
def main():
    inicio_global = datetime.now()
    hoy = inicio_global.strftime("%d/%m/%Y")

    print("\n" + "=" * 80)
    print("DESCARGA DE MUESTRAS Y RESULTADOS PDF - UESVALLE V7")
    print("=" * 80)
    print(f"📅 Fecha de ejecución: {hoy}")
    print(f"📁 Carpeta de salida del lote: {SALIDAS_DIR}")
    print("=" * 80 + "\n")

    print("Seleccione proceso a ejecutar:")
    print("  1. Solo extraer fichas de muestra")
    print("  2. Solo descargar PDF de resultados")
    print("  3. Extraer fichas + descargar PDF de resultados")
    modo = input("\nOpción [2]: ").strip() or "2"

    if modo not in ["1", "2", "3"]:
        print("❌ Modo inválido. Saliendo...")
        return

    tipo_servicio_cfg = None
    if modo in ["2", "3"]:
        tipo_servicio_cfg = solicitar_alcance_resultados()

    print("\nSeleccione Área Operativa - ARO / usuario:\n")
    for key, info in USUARIOS.items():
        print(f"  {key}. {info['nombre']} ({info['usuario']})")
    print()

    selec = input("Opción(es) (ej: 1 o 1,2,3): ").strip()
    ids_raw = [s.strip() for s in selec.split(",") if s.strip()]
    ids_validos = [i for i in ids_raw if i in USUARIOS]

    if not ids_validos:
        print("❌ No se seleccionó ningún usuario válido. Saliendo...")
        return

    print("\nUsuarios seleccionados:")
    for uid in ids_validos:
        print(f"  - {USUARIOS[uid]['nombre']} ({USUARIOS[uid]['usuario']})")

    texto_fechas = input(
        "\nIngrese las fechas de recepción a procesar\n"
        "(separadas por coma, ej: 06/04/2026,21/04/2026):\n> "
    )

    crudos = [f.strip() for f in texto_fechas.split(",") if f.strip()]
    if not crudos:
        print("❌ No se ingresaron fechas. Saliendo...")
        return

    fechas = []
    for f_raw in crudos:
        try:
            fechas.append(normalizar_fecha_usuario(f_raw))
        except Exception:
            print(f"   ⚠ Fecha inválida, se omite: {f_raw}")

    if not fechas:
        print("❌ Ninguna fecha válida. Saliendo...")
        return

    print("\nFechas válidas:")
    for _, ftabla, _ in fechas:
        print("  -", ftabla)

    guardar_debug = input("\n¿Guardar HTML debug de resultados? [N]: ").strip().upper() == "S"

    fichas_todas = []
    descargas_todas = []

    for uid in ids_validos:
        user_cfg = USUARIOS[uid]
        fichas_usuario, descargas_usuario = procesar_usuario(
            user_cfg,
            fechas,
            modo=modo,
            tipo_servicio_cfg=tipo_servicio_cfg,
            guardar_debug=guardar_debug
        )
        fichas_todas.extend(fichas_usuario)
        descargas_todas.extend(descargas_usuario)

    # Exportar fichas
    df_fichas = pd.DataFrame(fichas_todas) if fichas_todas else pd.DataFrame()
    if not df_fichas.empty:
        exportar_dataframe(df_fichas, f"muestras_fichas_CONSOLIDADO_lote_{RUN_ID}")
        generar_resumen_fichas(df_fichas, f"resumen_fichas_CONSOLIDADO_lote_{RUN_ID}")

    # Exportar control descargas
    df_descargas = pd.DataFrame(descargas_todas) if descargas_todas else pd.DataFrame()
    if not df_descargas.empty:
        exportar_dataframe(df_descargas, f"control_descarga_resultados_CONSOLIDADO_lote_{RUN_ID}")
        generar_resumen_descargas(df_descargas, f"resumen_descargas_resultados_CONSOLIDADO_lote_{RUN_ID}")

    # Limpieza opcional de carpeta temporal si queda vacía o solo temporales.
    try:
        for p in TEMP_DOWNLOAD_DIR.glob("*.crdownload"):
            p.unlink(missing_ok=True)
    except Exception:
        pass

    alcance_txt = "TODAS AGUA"
    try:
        if tipo_servicio_cfg:
            alcance_txt = f"{tipo_servicio_cfg.get('codigo')} - {tipo_servicio_cfg.get('nombre')}"
    except Exception:
        pass

    dfs_info = {
        "Alcance resultados": alcance_txt,
        "Total fichas extraídas": len(df_fichas) if not df_fichas.empty else 0,
        "Total registros control PDF": len(df_descargas) if not df_descargas.empty else 0,
        "PDF descargados OK": int((df_descargas.get("Estado_descarga", pd.Series(dtype=str)) == "OK").sum()) if not df_descargas.empty else 0,
        "Carpeta PDF": str(PDFS_DIR)
    }
    escribir_log(inicio_global, modo, dfs_info=dfs_info)

    fin = datetime.now()
    duracion = fin - inicio_global

    print("\n\n📦🌟====================================================")
    print("             RESUMEN FINAL DE LA EJECUCIÓN")
    print("====================================================🌟📦\n")
    print(f"🕒 Tiempo total: {str(duracion).split('.')[0]}")
    print(f"📁 Carpeta de salida: {SALIDAS_DIR}")
    print(f"📂 Carpeta PDF:       {PDFS_DIR}")

    if not df_descargas.empty:
        ok = int((df_descargas["Estado_descarga"] == "OK").sum())
        err = len(df_descargas) - ok
        print(f"📥 PDF descargados OK: {ok}")
        print(f"⚠ Registros con novedad: {err}")

    print("\n🗂️ Archivos principales generados:")
    for p in sorted(SALIDAS_DIR.glob("*")):
        if p.is_file():
            print(f"   📄 {p.name}")
        elif p.is_dir() and p.name != "_tmp_descargas_chrome":
            print(f"   📁 {p.name}/")

    print("\n✨ PROCESO FINALIZADO ✨")
    print("====== FIN DE LA EJECUCIÓN ======")


if __name__ == "__main__":
    main()
