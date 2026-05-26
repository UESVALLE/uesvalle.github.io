# -*- coding: utf-8 -*-
"""
INVENTARIO GENERAL DE RESULTADOS DE AGUA - UESVALLE V4

Objetivo:
- Consultar la tabla general de resultados en:
  https://gestion-muestras.valledelcauca.gov.co/results
- Aplicar únicamente filtros base:
    Clase de muestra = Agua
    Estado = Finalizada
    Tipo de servicio = opcional
- Cambiar el paginador a 100 registros por página.
- Recorrer todas las páginas de la tabla.
- Descargar la información visible de la tabla SIN descargar PDF y SIN entrar a registros.

Uso:
- Este script genera un inventario general de resultados disponibles.
- A partir de ese inventario se identifican las fechas reales de recepción para luego descargar PDF solo en esas fechas.

Salidas principales:
- data/resultados_agua/current/inventario_resultados_agua.csv
- data/resultados_agua/current/fechas_disponibles_resultados_agua.csv
- data/resultados_agua/current/resumen_fechas_disponibles_resultados_agua.csv
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
SALIDAS_DIR = CONTROL_DESCARGAS_DIR / f"Lote_Inventario_{RUN_ID}"
HTML_DEBUG_DIR = SALIDAS_DIR / "HTML_Debug"

PORTAL_DATA_DIR = PORTAL_UESVALLE_DIR / "data" / "resultados_agua" / "current"
PORTAL_SCRIPTS_DIR = PORTAL_UESVALLE_DIR / "scripts" / "resultados_agua"

OUT_INVENTARIO_CURRENT_CSV = PORTAL_DATA_DIR / "inventario_resultados_agua.csv"
OUT_INVENTARIO_CURRENT_XLSX = PORTAL_DATA_DIR / "inventario_resultados_agua.xlsx"
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


def fecha_sort_key(fecha):
    try:
        return datetime.strptime(str(fecha), "%d/%m/%Y")
    except Exception:
        return datetime.min


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
    time.sleep(1.2)


def esperar_tabla_con_filas(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    return driver.find_elements(By.CSS_SELECTOR, "table tbody tr")


def contar_filas_visibles(driver):
    try:
        return len(driver.find_elements(By.CSS_SELECTOR, "table tbody tr"))
    except Exception:
        return 0


def texto_paginador(driver):
    """
    Intenta leer el texto del rango del paginador.
    Ejemplo esperado: '1 – 100 de 1158' o 'Página 1 de 12'.
    """
    selectores = [
        ".mat-mdc-paginator-range-label",
        "mat-paginator .mat-mdc-paginator-range-label",
        "mat-paginator"
    ]
    for sel in selectores:
        try:
            txt = limpiar_texto(driver.find_element(By.CSS_SELECTOR, sel).text)
            if txt:
                return txt
        except Exception:
            pass
    return ""


def esperar_page_size_aplicado(driver, esperado=100, timeout=25):
    """
    Después de seleccionar 100 elementos por página, Angular puede tardar en
    reconstruir la tabla. Esta espera evita leer solo los primeros 10 registros
    y luego saltar a la página 2, lo cual omite registros 11-100.
    """
    inicio = time.time()
    ultimo_estado = ""

    while time.time() - inicio < timeout:
        filas = contar_filas_visibles(driver)
        pag = texto_paginador(driver)
        estado = f"filas={filas} | paginador={pag}"
        if estado != ultimo_estado:
            print(f"   ⏳ Esperando aplicación de tamaño de página: {estado}")
            ultimo_estado = estado

        # Si hay menos de 100 registros totales, podría mostrar menos.
        # Para inventarios grandes, esperamos al menos 50 como señal de que ya no está en 10.
        if esperado == 100 and filas >= 50:
            return True

        # También aceptamos texto explícito del paginador.
        pag_norm = pag.replace("–", "-").replace("—", "-")
        if esperado == 100 and ("1 - 100" in pag_norm or "1-100" in pag_norm or "100 de" in pag_norm):
            return True

        if esperado == 50 and filas >= 40:
            return True

        time.sleep(0.8)

    print("   ⚠ No se confirmó el tamaño de página esperado; se continuará con las filas visibles.")
    return False


def set_page_size_100(driver):
    wait = WebDriverWait(driver, 20)

    def seleccionar_opcion(valor):
        select_page_size = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//mat-paginator//mat-select"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_page_size)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", select_page_size)
        time.sleep(0.7)

        opcion = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//mat-option//span[normalize-space()='{valor}']"))
        )
        driver.execute_script("arguments[0].click();", opcion)
        time.sleep(1.5)

    try:
        # Primer intento: 100 registros por página.
        seleccionar_opcion("100")
        print("   📌 Elementos por página solicitados: 100")

        ok = esperar_page_size_aplicado(driver, esperado=100, timeout=30)
        filas = contar_filas_visibles(driver)

        if ok or filas >= 50:
            print(f"   ✅ Tamaño de página aplicado. Filas visibles: {filas}")
            return 100

        # Si siguió en 10, intenta una segunda vez.
        print("   🔁 Reintentando aplicar 100 registros por página...")
        seleccionar_opcion("100")
        ok = esperar_page_size_aplicado(driver, esperado=100, timeout=30)
        filas = contar_filas_visibles(driver)

        if ok or filas >= 50:
            print(f"   ✅ Tamaño de página aplicado en segundo intento. Filas visibles: {filas}")
            return 100

    except Exception as e:
        print(f"   ⚠ No se pudo seleccionar 100 elementos por página: {e}")

    # Fallback a 50 si 100 no está disponible o no se confirma.
    try:
        seleccionar_opcion("50")
        print("   📌 Elementos por página solicitados: 50")
        esperar_page_size_aplicado(driver, esperado=50, timeout=25)
        filas = contar_filas_visibles(driver)
        print(f"   ✅ Tamaño de página fallback aplicado. Filas visibles: {filas}")
        return 50
    except Exception as e:
        print(f"   ⚠ No se pudo cambiar elementos por página: {e}")
        return None


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


def extraer_tabla_visible_rapido(driver):
    """
    Lectura rápida de la tabla visible usando JavaScript.
    Evita hacer find_element celda por celda con Selenium.
    Retorna una lista de diccionarios con las columnas visibles.
    """
    script = """
    const rows = Array.from(document.querySelectorAll('table tbody tr'));
    return rows.map((tr) => {
        const cells = Array.from(tr.querySelectorAll('td')).map(td => (td.innerText || '').trim());
        return cells;
    });
    """
    try:
        filas = driver.execute_script(script)
    except Exception:
        filas = []

    registros = []
    for cells in filas:
        # Estructura esperada:
        # Código | Fecha envío | Fecha recepción | Hora recepción | Fecha resultados |
        # Tipo | Entidad | # recibidas | # rechazadas | Estado | Acciones
        if not cells or len(cells) < 10:
            continue

        datos = {
            "Codigo": limpiar_texto(cells[0] if len(cells) > 0 else ""),
            "Fecha_envio": limpiar_texto(cells[1] if len(cells) > 1 else ""),
            "Fecha_recepcion": limpiar_texto(cells[2] if len(cells) > 2 else ""),
            "Hora_recepcion": limpiar_texto(cells[3] if len(cells) > 3 else ""),
            "Fecha_resultados": limpiar_texto(cells[4] if len(cells) > 4 else ""),
            "Tipo": limpiar_texto(cells[5] if len(cells) > 5 else ""),
            "Entidad_que_remite": limpiar_texto(cells[6] if len(cells) > 6 else ""),
            "Muestras_recibidas": limpiar_texto(cells[7] if len(cells) > 7 else ""),
            "Muestras_rechazadas": limpiar_texto(cells[8] if len(cells) > 8 else ""),
            "Estado": limpiar_texto(cells[9] if len(cells) > 9 else ""),
        }

        if datos["Codigo"]:
            registros.append(datos)

    return registros


def esperar_cambio_pagina_o_tabla(driver, codigos_antes, timeout=18):
    """
    Espera a que la tabla cambie después de hacer clic en siguiente.
    Compara los códigos visibles para evitar leer dos veces la misma página.
    """
    inicio = time.time()
    codigos_antes = set(codigos_antes or [])

    while time.time() - inicio < timeout:
        time.sleep(0.7)
        registros = extraer_tabla_visible_rapido(driver)
        codigos_actuales = set(r.get("Codigo", "") for r in registros if r.get("Codigo", ""))

        if codigos_actuales and codigos_actuales != codigos_antes:
            return True

    return False


def consultar_inventario_usuario(user_cfg, tipo_servicio_cfg=None, guardar_debug=False, max_paginas=None):
    registros = []

    print("
" + "=" * 70)
    print(f"Inventario general ARO: {user_cfg['nombre']} ({user_cfg['usuario']})")
    print("=" * 70)

    driver = iniciar_driver(headless=True)

    try:
        login(driver, user_cfg)

        driver.get(RESULTADOS_URL)
        WebDriverWait(driver, 30).until(EC.url_contains("/results"))
        time.sleep(1.2)
        print("   🔄 Vista 'Muestras y resultados' cargada.")

        # ---------------------------------------------------------------------
        # V4: primero asegurar tamaño de página ANTES de aplicar filtros.
        # Esto evita que el primer filtro cargue solo 10 registros y luego,
        # al pasar a la página 2 con paginador 100, se pierdan los registros 11-100.
        # ---------------------------------------------------------------------
        try:
            esperar_tabla_con_filas(driver, timeout=25)
            print("   🔧 Ajustando paginador a 100 ANTES de filtrar...")
            page_size_pre = set_page_size_100(driver)
            time.sleep(0.8)
            print(f"   🔎 Filas visibles antes de filtrar: {contar_filas_visibles(driver)}")
        except Exception as e:
            print(f"   ⚠ No se pudo ajustar paginador antes de filtrar: {e}")
            page_size_pre = None

        # Aplicar filtros base.
        aplicar_filtros_base_resultados(driver, tipo_servicio_cfg=tipo_servicio_cfg)

        try:
            esperar_tabla_con_filas(driver, timeout=25)
        except TimeoutException:
            print("   ⚠ No se encontraron filas en la tabla general después de filtrar.")
            if guardar_debug:
                guardar_html_debug(driver, f"sin_inventario_{normalizar_nombre_carpeta(user_cfg['nombre'])}.html")
            return registros

        # ---------------------------------------------------------------------
        # V4: confirmar nuevamente 100 DESPUÉS de filtrar.
        # Algunas tablas Angular conservan el page-size, otras lo reinician.
        # ---------------------------------------------------------------------
        print("   🔧 Confirmando paginador a 100 DESPUÉS de filtrar...")
        page_size = set_page_size_100(driver) or page_size_pre

        # Espera adicional de estabilización para evitar leer la tabla antes de que
        # Angular cargue los 100 registros de la primera página.
        time.sleep(1.0)
        filas_post_size = contar_filas_visibles(driver)
        print(f"   🔎 Filas visibles después de ajustar paginador y filtrar: {filas_post_size}")

        # Si aún hay solo 10 filas, esperar/reintentar una vez más antes de leer.
        if filas_post_size <= 10:
            print("   🔁 La primera página aún muestra 10 filas. Reintentando paginador 100...")
            page_size = set_page_size_100(driver) or page_size
            time.sleep(1.5)
            filas_post_size = contar_filas_visibles(driver)
            print(f"   🔎 Filas visibles luego del reintento: {filas_post_size}")

        if guardar_debug:
            guardar_html_debug(driver, f"inventario_general_{normalizar_nombre_carpeta(user_cfg['nombre'])}.html")

        pagina = 1
        codigos_vistos = set()

        while True:
            if max_paginas and pagina > max_paginas:
                print(f"      ⏹ Corte por máximo de páginas configurado: {max_paginas}")
                break

            print(f"      📄 Leyendo página {pagina} de inventario general...")

            registros_pagina = extraer_tabla_visible_rapido(driver)

            # Fallback al método Selenium por fila si JavaScript no retorna nada.
            if not registros_pagina:
                print("      ⚠ Lectura rápida sin registros; usando fallback Selenium por fila.")
                try:
                    filas = esperar_tabla_con_filas(driver, timeout=20)
                except TimeoutException:
                    print("      ⚠ No se encontraron filas en la página actual.")
                    break

                registros_pagina = []
                for idx, fila in enumerate(filas):
                    try:
                        metadata = extraer_metadata_fila_resultado(fila)
                        if metadata.get("Codigo"):
                            registros_pagina.append(metadata)
                    except Exception:
                        continue

            total_filas = len(registros_pagina)
            print(f"      🔎 Filas leídas página {pagina}: {total_filas}")

            # Advertencia específica para página 1.
            if pagina == 1 and total_filas <= 10:
                print("      ⚠ ADVERTENCIA: página 1 se está leyendo con 10 filas. Revise si el paginador quedó en 100.")

            nuevos_pagina = 0

            for idx, metadata in enumerate(registros_pagina, start=1):
                codigo = metadata.get("Codigo", "")
                if not codigo:
                    continue

                clave = (user_cfg["nombre"], codigo)
                if clave in codigos_vistos:
                    continue

                codigos_vistos.add(clave)
                nuevos_pagina += 1

                tipo_cod, tipo_nom = detectar_tipo_servicio_desde_texto(
                    metadata.get("Codigo", ""),
                    metadata.get("Tipo", "")
                )

                metadata["ARO"] = user_cfg["nombre"]
                metadata["Usuario"] = user_cfg["usuario"]
                metadata["Tipo_servicio_detectado_codigo"] = tipo_cod
                metadata["Tipo_servicio_detectado_nombre"] = tipo_nom
                metadata["Pagina"] = pagina
                metadata["Fila_en_pagina"] = idx
                metadata["Page_size_configurado"] = page_size or ""
                metadata["Fecha_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                registros.append(metadata)

            print(f"      ✔ Nuevos registros página {pagina}: {nuevos_pagina}")
            print(f"      📦 Total acumulado {user_cfg['nombre']}: {len(registros)}")

            codigos_actuales = [r.get("Codigo", "") for r in registros_pagina if r.get("Codigo", "")]

            btn_next = pagina_siguiente_disponible(driver)
            if not btn_next:
                break

            try:
                driver.execute_script("arguments[0].click();", btn_next)
                cambio_ok = esperar_cambio_pagina_o_tabla(driver, codigos_actuales, timeout=18)
                if not cambio_ok:
                    print("      ⚠ No se confirmó cambio de tabla; se continuará con precaución.")
                    time.sleep(1.0)
                pagina += 1
            except Exception as e:
                print(f"      ⚠ No se pudo avanzar a la página siguiente: {e}")
                break

        print(f"      ✔ Total registros inventariados {user_cfg['nombre']}: {len(registros)}")

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

    # Ordenar por ARO y fecha descendente aproximada.
    df = df.copy()
    df["_fecha_sort"] = df["Fecha_recepcion"].apply(fecha_sort_key)
    df = df.sort_values(["ARO", "_fecha_sort", "Codigo"], ascending=[True, False, True])
    df = df.drop(columns=["_fecha_sort"], errors="ignore")

    detalle_xlsx = SALIDAS_DIR / f"inventario_resultados_agua_lote_{RUN_ID}.xlsx"
    detalle_csv = SALIDAS_DIR / f"inventario_resultados_agua_lote_{RUN_ID}.csv"

    df.to_excel(detalle_xlsx, index=False)
    df.to_csv(detalle_csv, index=False, encoding="utf-8-sig")

    # Fechas disponibles por ARO, fecha y tipo.
    fechas = (
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
    )
    fechas["_fecha_sort"] = fechas["Fecha_recepcion"].apply(fecha_sort_key)
    fechas = fechas.sort_values(["ARO", "_fecha_sort", "Tipo_servicio_detectado_codigo"], ascending=[True, False, True])
    fechas = fechas.drop(columns=["_fecha_sort"], errors="ignore")

    resumen_aro = (
        df.groupby(["ARO", "Tipo_servicio_detectado_codigo", "Tipo_servicio_detectado_nombre"], dropna=False)
        .agg(
            Total_resultados=("Codigo", "count"),
            Fechas_recepcion_distintas=("Fecha_recepcion", pd.Series.nunique),
            Fecha_recepcion_min=("Fecha_recepcion", "min"),
            Fecha_recepcion_max=("Fecha_recepcion", "max")
        )
        .reset_index()
        .sort_values(["ARO", "Tipo_servicio_detectado_codigo"])
    )

    fechas_xlsx = SALIDAS_DIR / f"fechas_disponibles_resultados_agua_lote_{RUN_ID}.xlsx"
    fechas_csv = SALIDAS_DIR / f"fechas_disponibles_resultados_agua_lote_{RUN_ID}.csv"
    resumen_xlsx = SALIDAS_DIR / f"resumen_inventario_resultados_agua_lote_{RUN_ID}.xlsx"
    resumen_csv = SALIDAS_DIR / f"resumen_inventario_resultados_agua_lote_{RUN_ID}.csv"

    fechas.to_excel(fechas_xlsx, index=False)
    fechas.to_csv(fechas_csv, index=False, encoding="utf-8-sig")
    resumen_aro.to_excel(resumen_xlsx, index=False)
    resumen_aro.to_csv(resumen_csv, index=False, encoding="utf-8-sig")

    # Current para portal/proceso.
    df.to_csv(OUT_INVENTARIO_CURRENT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUT_INVENTARIO_CURRENT_XLSX, index=False)

    fechas.to_csv(OUT_FECHAS_CURRENT_CSV, index=False, encoding="utf-8-sig")
    fechas.to_excel(OUT_FECHAS_CURRENT_XLSX, index=False)
    resumen_aro.to_csv(OUT_RESUMEN_CURRENT_CSV, index=False, encoding="utf-8-sig")

    print("\n📁 Archivos generados en lote:")
    print(f"   Inventario Excel: {detalle_xlsx}")
    print(f"   Inventario CSV:   {detalle_csv}")
    print(f"   Fechas Excel:     {fechas_xlsx}")
    print(f"   Fechas CSV:       {fechas_csv}")
    print(f"   Resumen Excel:    {resumen_xlsx}")
    print(f"   Resumen CSV:      {resumen_csv}")

    print("\n📁 Archivos current para tablero/proceso:")
    print(f"   {OUT_INVENTARIO_CURRENT_CSV}")
    print(f"   {OUT_INVENTARIO_CURRENT_XLSX}")
    print(f"   {OUT_FECHAS_CURRENT_CSV}")
    print(f"   {OUT_FECHAS_CURRENT_XLSX}")
    print(f"   {OUT_RESUMEN_CURRENT_CSV}")

    return df, fechas, resumen_aro


def escribir_log(inicio, df, alcance_txt):
    fin = datetime.now()
    duracion = fin - inicio
    log_path = SALIDAS_DIR / "log_inventario_resultados_agua.txt"

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("===== LOG INVENTARIO GENERAL RESULTADOS AGUA UESVALLE =====\n\n")
        log.write(f"Fecha ejecución: {fin}\n")
        log.write(f"Tiempo total: {duracion}\n")
        log.write(f"Alcance: {alcance_txt}\n")
        log.write(f"Registros inventariados: {len(df)}\n")
        log.write(f"Carpeta salida: {SALIDAS_DIR}\n")
        if not df.empty:
            log.write("\nResumen por ARO:\n")
            resumen = df.groupby("ARO").size().reset_index(name="Total")
            for _, row in resumen.iterrows():
                log.write(f" - {row['ARO']}: {row['Total']}\n")

    print(f"\n📝 Log generado: {log_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    inicio = datetime.now()

    print("\n" + "=" * 80)
    print("INVENTARIO GENERAL DE RESULTADOS DE AGUA - UESVALLE V4")
    print("=" * 80)
    print("Este proceso consulta la tabla general de resultados sin descargar PDF.")
    print("No requiere ingresar fechas. Recorre todas las páginas disponibles. V4 aplica el tamaño de página antes y después de filtrar para evitar perder registros de la primera página.")
    print(f"📁 Carpeta de salida del lote: {SALIDAS_DIR}")
    print("=" * 80)

    tipo_servicio_cfg = solicitar_alcance_resultados()
    ids_validos = seleccionar_usuarios()

    if not ids_validos:
        return

    max_paginas_txt = input(
        "\nMáximo de páginas a leer por ARO [Enter = todas]: "
    ).strip()

    max_paginas = None
    if max_paginas_txt:
        try:
            max_paginas = int(max_paginas_txt)
        except Exception:
            print("   ⚠ Valor no válido. Se leerán todas las páginas.")
            max_paginas = None

    guardar_debug = input("\n¿Guardar HTML debug? [N]: ").strip().upper() == "S"

    registros = []

    for uid in ids_validos:
        user_cfg = USUARIOS[uid]
        regs = consultar_inventario_usuario(
            user_cfg=user_cfg,
            tipo_servicio_cfg=tipo_servicio_cfg,
            guardar_debug=guardar_debug,
            max_paginas=max_paginas
        )
        registros.extend(regs)

    df = pd.DataFrame(registros)

    if df.empty:
        print("\n⚠ No se detectaron resultados en la tabla general.")
    else:
        _, fechas, resumen_aro = exportar_salidas(df)

        print("\n===== RESUMEN GENERAL INVENTARIO =====")
        resumen_simple = (
            df.groupby(["ARO", "Tipo_servicio_detectado_codigo"], dropna=False)
            .size()
            .reset_index(name="Total_resultados")
            .sort_values(["ARO", "Tipo_servicio_detectado_codigo"])
        )
        print(resumen_simple.to_string(index=False))

        print("\n===== FECHAS DISPONIBLES DETECTADAS =====")
        fechas_simple = (
            df.groupby(["ARO", "Fecha_recepcion"], dropna=False)
            .size()
            .reset_index(name="Total_resultados")
        )
        fechas_simple["_fecha_sort"] = fechas_simple["Fecha_recepcion"].apply(fecha_sort_key)
        fechas_simple = fechas_simple.sort_values(["ARO", "_fecha_sort"], ascending=[True, False]).drop(columns=["_fecha_sort"])
        print(fechas_simple.to_string(index=False))

    alcance_txt = "TODAS AGUA"
    if tipo_servicio_cfg:
        alcance_txt = f"{tipo_servicio_cfg.get('codigo')} - {tipo_servicio_cfg.get('nombre')}"

    escribir_log(inicio, df, alcance_txt)

    print("\n✨ PROCESO FINALIZADO ✨")


if __name__ == "__main__":
    main()
