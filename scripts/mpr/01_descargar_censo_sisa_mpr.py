# -*- coding: utf-8 -*-
"""
DESCARGAR CENSO DE VISITAS SISA - MPR UESVALLE
Version: V1.5

Objetivo:
1. Ingresar a SISA.
2. Seleccionar ARO de trabajo al iniciar sesion.
3. Abrir Agua para Consumo Humano > Censos de visitas.
4. Generar reporte de visitas realizadas desde 01/01/2026 hasta la fecha actual.
5. Guardar el archivo descargado como data/mpr/raw/censo_visitasMPR.xlsx.
6. Opcionalmente ejecutar normalizar_mpr.py.

Credenciales:
- Preferido: variables de entorno SISA_USER y SISA_PASS.
- Alternativo: archivo local config_sisa.env en scripts/mpr/ con:
    SISA_USER=usuario
    SISA_PASS=contrasena

No suba config_sisa.env a GitHub.
"""
from __future__ import annotations

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except Exception:
    HAS_WDM = False

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2] if SCRIPT_PATH.parent.name.lower() == "mpr" else Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")
RAW_DIR = REPO_ROOT / "data" / "mpr" / "raw"
OUT_CENSO = RAW_DIR / "censo_visitasMPR.xlsx"
TMP_DOWNLOAD = REPO_ROOT / "archive" / "tmp_descargas_sisa_mpr"
LOG_DIR = REPO_ROOT / "archive" / "logs_sisa_mpr"
NORMALIZER = REPO_ROOT / "scripts" / "mpr" / "normalizar_mpr.py"
PYTHON_EXE = Path(r"C:\Users\Javier\miniconda3\envs\analitica\python.exe")

SISA_URL = "https://sisaweb.nexura.com.co/SISAcloud/login.xhtml"
LOGIN_ARO = os.getenv("SISA_LOGIN_ARO", "3-Aro Sur Cali")
MODULO_ARO = os.getenv("SISA_MODULO_ARO", "Todos los aros")
FECHA_INICIAL = os.getenv("SISA_FECHA_INICIAL", "01/01/2026")
FECHA_FINAL = os.getenv("SISA_FECHA_FINAL", datetime.now().strftime("%d/%m/%Y"))
CENSO_OPCION = os.getenv("SISA_CENSO_OPCION", "Visitas realizadas")
ESTADO_ESTABLECIMIENTO = os.getenv("SISA_ESTADO_ESTABLECIMIENTO", "Todos")
HEADLESS = os.getenv("SISA_HEADLESS", "0") == "1"
EJECUTAR_NORMALIZADOR = os.getenv("SISA_EJECUTAR_NORMALIZADOR", "1") == "1"
TIMEOUT = int(os.getenv("SISA_TIMEOUT", "45"))


def log(msg: str) -> None:
    print(msg, flush=True)


def load_env_file() -> None:
    env_path = SCRIPT_PATH.parent / "config_sisa.env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_credentials() -> tuple[str, str]:
    load_env_file()
    user = os.getenv("SISA_USER", "").strip()
    password = os.getenv("SISA_PASS", "").strip()
    if not user:
        user = input("Usuario SISA: ").strip()
    if not password:
        password = getpass("Contraseña SISA: ").strip()
    if not user or not password:
        raise RuntimeError("Usuario o contraseña SISA vacíos.")
    return user, password


def prepare_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DOWNLOAD.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for p in TMP_DOWNLOAD.glob("*"):
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def build_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": str(TMP_DOWNLOAD),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
        "autofill.profile_enabled": False,
        "autofill.credit_card_enabled": False,
    }
    opts.add_argument("--start-maximized")
    opts.add_argument("--incognito")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-save-password-bubble")
    opts.add_argument("--disable-features=PasswordLeakDetection,PasswordManagerOnboarding,PasswordGeneration,AutofillServerCommunication")
    opts.add_experimental_option("prefs", prefs)
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    if HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1600,1000")

    # V1.1: no usar por defecto C:\chromedriver-win64\chromedriver.exe,
    # porque puede quedar desactualizado frente a la versión instalada de Chrome.
    # Prioridad:
    # 1) Si el usuario define CHROMEDRIVER en variables de entorno, usar ese ejecutable.
    # 2) Si existe webdriver-manager, descargar/usar el driver compatible.
    # 3) Si no, dejar que Selenium Manager resuelva automáticamente el driver.
    chrome_driver = os.getenv("CHROMEDRIVER", "").strip()
    if chrome_driver and Path(chrome_driver).exists():
        print(f"Usando ChromeDriver definido por CHROMEDRIVER: {chrome_driver}")
        service = Service(chrome_driver)
    elif HAS_WDM:
        print("Usando webdriver-manager para resolver ChromeDriver compatible...")
        service = Service(ChromeDriverManager().install())
    else:
        print("Usando Selenium Manager para resolver ChromeDriver compatible...")
        service = Service()

    driver = webdriver.Chrome(service=service, options=opts)
    # Forzar comportamiento de descarga sin ventana nativa "Guardar como".
    # Esto es clave cuando Chrome tiene activada la opción "Preguntar dónde guardar"
    # o cuando la descarga proviene de una respuesta POST de PrimeFaces.
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(TMP_DOWNLOAD)
        })
    except Exception as exc:
        print(f"[AVISO] No se pudo aplicar Page.setDownloadBehavior: {exc}")
    return driver


def wait(driver: webdriver.Chrome) -> WebDriverWait:
    return WebDriverWait(driver, TIMEOUT)


def safe_click(driver: webdriver.Chrome, element) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
    time.sleep(0.2)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def find_first(driver: webdriver.Chrome, locators: list[tuple[str, str]], timeout: int = TIMEOUT):
    end = time.time() + timeout
    last_exc = None
    while time.time() < end:
        for by, sel in locators:
            try:
                els = driver.find_elements(by, sel)
                els = [e for e in els if e.is_displayed() or e.get_attribute("type") == "hidden"]
                if els:
                    return els[0]
            except Exception as exc:
                last_exc = exc
        time.sleep(0.4)
    raise TimeoutException(f"No se encontró elemento con locators: {locators}. Último error: {last_exc}")


def login(driver: webdriver.Chrome, user: str, password: str) -> None:
    log("[1/6] Abriendo SISA...")
    driver.get(SISA_URL)

    user_el = find_first(driver, [
        (By.ID, "username"), (By.ID, "usuario"), (By.ID, "user"), (By.NAME, "username"),
        (By.NAME, "usuario"), (By.NAME, "user"),
        (By.XPATH, "//label[contains(normalize-space(.),'Usuario')]/following::input[1]"),
        (By.CSS_SELECTOR, "input[type='text']"),
    ])
    pass_el = find_first(driver, [
        (By.ID, "password"), (By.NAME, "password"),
        (By.XPATH, "//input[@type='password']"),
    ])
    user_el.clear(); user_el.send_keys(user)
    pass_el.clear(); pass_el.send_keys(password)

    btn = find_first(driver, [
        (By.ID, "log"), (By.NAME, "log"),
        (By.XPATH, "//button[contains(normalize-space(.),'Ingresar') or contains(@value,'Ingresar')]"),
        (By.XPATH, "//input[@type='submit' and (contains(@value,'Ingresar') or contains(@id,'log'))]"),
    ])
    safe_click(driver, btn)
    wait(driver).until(lambda d: "principal.xhtml" in d.current_url or len(d.find_elements(By.XPATH, "//*[contains(.,'Selección de ARO') or contains(.,'Sistema de Informacion') or contains(.,'SISTEMA DE INFORMACION')]") ) > 0)
    log("     Login enviado.")


def visible_elements(driver: webdriver.Chrome, by: str, selector: str):
    """Retorna elementos visibles. PrimeFaces deja paneles ocultos en el DOM y eso confunde Selenium."""
    out = []
    for e in driver.find_elements(by, selector):
        try:
            if e.is_displayed():
                out.append(e)
        except Exception:
            pass
    return out




def dismiss_browser_overlays(driver: webdriver.Chrome) -> None:
    """Reduce interferencias de overlays/diálogos del navegador o de PrimeFaces si aparecen."""
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass
    # Cerrar diálogos internos de la aplicación que tengan una X visible y no sean necesarios.
    for xp in [
        "//a[contains(@class,'ui-dialog-titlebar-close') and not(ancestor::div[contains(.,'Selección de ARO')])]",
        "//span[contains(@class,'ui-icon-closethick')]/ancestor::a[1]",
    ]:
        for el in visible_elements(driver, By.XPATH, xp):
            try:
                safe_click(driver, el)
                time.sleep(0.2)
            except Exception:
                pass


def click_by_js_or_action(driver: webdriver.Chrome, locator: tuple[str, str], timeout: int = 20) -> None:
    el = wait(driver).until(EC.presence_of_element_located(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
    time.sleep(0.3)
    try:
        wait(driver).until(EC.element_to_be_clickable(locator))
        el.click()
    except Exception:
        try:
            ActionChains(driver).move_to_element(el).pause(0.2).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
    time.sleep(0.8)

def select_primefaces_option_by_component(driver: webdriver.Chrome, component_xpath: str, option_text: str) -> None:
    """Selecciona una opción en un selectOneMenu de PrimeFaces.

    V1.2: hace clic sobre el trigger visible y no sobre elementos ocultos del panel.
    """
    comp = wait(driver).until(EC.visibility_of_element_located((By.XPATH, component_xpath)))

    # Abrir el desplegable. Preferir el trigger visible.
    triggers = comp.find_elements(By.XPATH, ".//*[contains(@class,'ui-selectonemenu-trigger')]")
    if triggers:
        safe_click(driver, triggers[0])
    else:
        safe_click(driver, comp)
    time.sleep(0.8)

    # Seleccionar opción visible.
    option_xpaths = [
        f"//li[@role='option' and @data-label={xpath_literal(option_text)}]",
        f"//li[@role='option' and normalize-space(.)={xpath_literal(option_text)}]",
        f"//li[contains(@class,'ui-selectonemenu-item') and contains(normalize-space(.),{xpath_literal(option_text)})]",
    ]
    opt = None
    end = time.time() + 20
    while time.time() < end and opt is None:
        for xp in option_xpaths:
            candidates = visible_elements(driver, By.XPATH, xp)
            if candidates:
                opt = candidates[0]
                break
        if opt is None:
            time.sleep(0.3)
    if opt is None:
        raise TimeoutException(f"No se encontró opción visible PrimeFaces: {option_text}")

    safe_click(driver, opt)
    time.sleep(0.6)


def xpath_literal(s: str) -> str:
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    return "concat(" + ", \"'\", ".join([f"'{p}'" for p in s.split("'")]) + ")"


def select_login_aro(driver: webdriver.Chrome) -> None:
    log(f"[2/6] Seleccionando ARO de sesión: {LOGIN_ARO}")

    # PrimeFaces selectOneMenu de la ventana inicial.
    # En el DOM observado, el componente visible es form-aro:j_idt44.
    select_primefaces_option_by_component(
        driver,
        "//div[@id='form-aro:j_idt44' and contains(@class,'ui-selectonemenu')]",
        LOGIN_ARO,
    )

    # Validar visualmente que el texto seleccionado haya quedado en el label.
    try:
        wait(driver).until(lambda d: LOGIN_ARO in d.find_element(By.ID, "form-aro:j_idt44_label").text)
    except Exception:
        pass

    # Clic en Aceptar dentro del formulario/modal de ARO.
    btn = find_first(driver, [
        (By.XPATH, "//form[@id='form-aro']//button[.//span[contains(normalize-space(.),'Aceptar')] or contains(normalize-space(.),'Aceptar')]") ,
        (By.XPATH, "//form[@id='form-aro']//span[contains(normalize-space(.),'Aceptar')]/ancestor::button[1]"),
        (By.XPATH, "//form[@id='form-aro']//input[contains(@value,'Aceptar')]") ,
        (By.XPATH, "//button[contains(normalize-space(.),'Aceptar')]") ,
    ], timeout=20)
    safe_click(driver, btn)

    # Esperar cierre del modal o carga del menú principal.
    wait(driver).until(lambda d:
        len(visible_elements(d, By.XPATH, "//div[contains(@class,'ui-dialog') and .//*[contains(.,'Selección de ARO')]]")) == 0
        or len(d.find_elements(By.XPATH, "//*[contains(normalize-space(.),'Agua para Consumo Humano')]") ) > 0
    )
    log("     ARO aceptado.")

def expand_tree_node_by_id(driver: webdriver.Chrome, node_id: str, label_text: str) -> None:
    """Expande un nodo PrimeFaces Tree usando el toggler, no el label.

    En SISA el label puede quedar seleccionado sin expandir el nodo; por eso se fuerza
    el clic sobre `.ui-tree-toggler` y se valida que los hijos queden visibles.
    """
    node_xpath = f"//li[@id={xpath_literal(node_id)}]"
    node = wait(driver).until(EC.presence_of_element_located((By.XPATH, node_xpath)))

    def children_visible() -> bool:
        try:
            child_ul = node.find_element(By.XPATH, "./ul[contains(@class,'ui-treenode-children')]")
            style = (child_ul.get_attribute("style") or "").lower().replace(" ", "")
            return child_ul.is_displayed() and "display:none" not in style
        except Exception:
            return False

    if children_visible():
        return

    # Clic preferente en el triángulo/toggler. No usar el label porque solo selecciona.
    for xp in [
        f"{node_xpath}//span[contains(@class,'ui-tree-toggler')]",
        f"{node_xpath}/span[contains(@class,'ui-treenode-content')]//span[contains(@class,'ui-icon-triangle')]",
    ]:
        try:
            toggler = wait(driver).until(EC.presence_of_element_located((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", toggler)
            time.sleep(0.2)
            try:
                ActionChains(driver).move_to_element(toggler).pause(0.2).click().perform()
            except Exception:
                driver.execute_script("arguments[0].click();", toggler)
            time.sleep(1.2)
            if children_visible():
                return
        except Exception:
            pass

    # Fallback: llamar el widget PrimeFaces del árbol y luego click al toggler.
    try:
        driver.execute_script("""
            var t = document.querySelector("#form-menu\\:idtreemenu\\:1 > span .ui-tree-toggler");
            if (t) { t.click(); }
        """)
        time.sleep(1.2)
        if children_visible():
            return
    except Exception:
        pass

    raise TimeoutException(f"No fue posible desplegar el nodo {label_text} ({node_id}).")


def click_tree_leaf_by_id(driver: webdriver.Chrome, node_id: str, label_text: str) -> None:
    node_xpath = f"//li[@id={xpath_literal(node_id)}]"
    label_xpath = f"{node_xpath}//span[contains(@class,'ui-treenode-label') and normalize-space(.)={xpath_literal(label_text)}]"
    content_xpath = f"{node_xpath}/span[contains(@class,'ui-treenode-content')]"

    # Primero clic sobre el label visible.
    for xp in [label_xpath, content_xpath]:
        try:
            el = wait(driver).until(EC.visibility_of_element_located((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
            time.sleep(0.3)
            try:
                ActionChains(driver).move_to_element(el).pause(0.2).click().perform()
            except Exception:
                driver.execute_script("arguments[0].click();", el)
            time.sleep(1.5)
            return
        except Exception:
            pass

    raise TimeoutException(f"No fue posible hacer clic en {label_text} ({node_id}).")


def open_censos_visitas(driver: webdriver.Chrome) -> None:
    log("[3/6] Abriendo Agua para Consumo Humano > Censos de visitas...")
    dismiss_browser_overlays(driver)

    # V1.4: el HTML de error mostró que el nodo Agua queda seleccionado pero colapsado:
    # <li id="form-menu:idtreemenu:1" ...><ul ... style="display:none">.
    # Por eso hay que hacer clic específicamente en el toggler antes de seleccionar el hijo 1_7.
    wait(driver).until(EC.presence_of_element_located((By.ID, "form-menu:idtreemenu")))
    expand_tree_node_by_id(driver, "form-menu:idtreemenu:1", "Agua para Consumo Humano")
    time.sleep(0.5)
    click_tree_leaf_by_id(driver, "form-menu:idtreemenu:1_7", "Censos de visitas")

    # Esperar que cargue el formulario del módulo.
    wait(driver).until(lambda d: len(d.find_elements(By.XPATH, "//*[contains(.,'Agua para Consumo Humano - Censos de visitas') or contains(.,'Censos:') or contains(.,'Fechas Reporte') or contains(.,'Fecha inicial')]") ) > 0)
    log("     Módulo abierto.")

def select_option_near_label(driver: webdriver.Chrome, label_text: str, option_text: str) -> None:
    # Busca el selectOneMenu después del texto de etiqueta.
    component_xpath = (
        f"//*[contains(normalize-space(.),{xpath_literal(label_text)})]"
        "/following::*[contains(@class,'ui-selectonemenu')][1]"
    )
    select_primefaces_option_by_component(driver, component_xpath, option_text)


def set_input_near_label(driver: webdriver.Chrome, label_text: str, value: str) -> None:
    inp = find_first(driver, [
        (By.XPATH, f"//*[contains(normalize-space(.),{xpath_literal(label_text)})]/following::input[not(@type='hidden')][1]")
    ], timeout=15)
    safe_click(driver, inp)
    inp.send_keys(Keys.CONTROL, "a")
    inp.send_keys(value)
    inp.send_keys(Keys.TAB)
    time.sleep(0.2)


def force_primefaces_select_by_label(driver: webdriver.Chrome, label_text: str, option_text: str) -> bool:
    """Fuerza el valor de un selectOneMenu de PrimeFaces localizado por etiqueta.

    SISA deja algunos paneles de opciones sin poblar o ocultos; en esos casos,
    seleccionar por clic visible puede fallar aunque el <select> oculto tenga
    las opciones correctas. Esta función cambia el <select> oculto, actualiza
    el label visible y dispara eventos change/input.
    """
    script = r"""
    const labelText = arguments[0].toLowerCase();
    const optionText = arguments[1];
    const all = Array.from(document.querySelectorAll('body *'));
    let labelNode = all.find(e => (e.innerText || '').trim().toLowerCase() === labelText.toLowerCase() + ':')
                 || all.find(e => (e.innerText || '').trim().toLowerCase().includes(labelText.toLowerCase()));
    if (!labelNode) return false;
    let container = labelNode.closest('.ui-g') || labelNode.parentElement;
    let comp = null;
    let cursor = container;
    for (let i=0; i<5 && cursor && !comp; i++, cursor=cursor.nextElementSibling) {
        comp = cursor.querySelector ? cursor.querySelector('.ui-selectonemenu') : null;
        if (!comp && cursor.classList && cursor.classList.contains('ui-selectonemenu')) comp = cursor;
    }
    if (!comp) {
        const comps = Array.from(document.querySelectorAll('.ui-selectonemenu'));
        const idx = comps.findIndex(c => c.compareDocumentPosition(labelNode) & Node.DOCUMENT_POSITION_PRECEDING);
        comp = comps.find(c => c.compareDocumentPosition(labelNode) & Node.DOCUMENT_POSITION_PRECEDING);
    }
    if (!comp) return false;
    const sel = comp.querySelector('select');
    if (!sel) return false;
    let opt = Array.from(sel.options).find(o => (o.textContent || '').trim() === optionText)
           || Array.from(sel.options).find(o => (o.textContent || '').trim().toLowerCase().includes(optionText.toLowerCase()));
    if (!opt) return false;
    sel.value = opt.value;
    opt.selected = true;
    const lbl = comp.querySelector('.ui-selectonemenu-label');
    if (lbl) lbl.textContent = (opt.textContent || optionText).trim();
    sel.dispatchEvent(new Event('change', {bubbles:true}));
    sel.dispatchEvent(new Event('input', {bubbles:true}));
    if (window.jQuery) { try { window.jQuery(sel).trigger('change'); } catch(e) {} }
    return true;
    """
    try:
        return bool(driver.execute_script(script, label_text, option_text))
    except Exception:
        return False


def force_date_input_by_id(driver: webdriver.Chrome, element_id: str, value: str) -> None:
    """Asigna fechas directamente evitando que el datepicker quede abierto."""
    el = wait(driver).until(EC.presence_of_element_located((By.ID, element_id)))
    driver.execute_script("""
        const el = arguments[0], value = arguments[1];
        el.value = value;
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        el.blur();
    """, el, value)
    time.sleep(0.2)


def configure_report(driver: webdriver.Chrome) -> None:
    log("[4/6] Configurando filtros del reporte...")

    # El HTML observado muestra que los controles ya quedan con estos valores:
    # ARO = Todos los aros, Censos = Visitas realizadas, Estado = Todos.
    # Se fuerzan por JS para evitar problemas con paneles PrimeFaces ocultos.
    if force_primefaces_select_by_label(driver, "ARO", MODULO_ARO):
        log(f"     ARO módulo: {MODULO_ARO}")
    else:
        log("     [AVISO] No se pudo forzar ARO del módulo; se usará el valor visible actual.")

    if force_primefaces_select_by_label(driver, "Censos", CENSO_OPCION):
        log(f"     Censos: {CENSO_OPCION}")
    else:
        log("     [AVISO] No se pudo forzar Censos; se usará el valor visible actual.")

    if force_primefaces_select_by_label(driver, "Estado establecimiento", ESTADO_ESTABLECIMIENTO):
        log(f"     Estado establecimiento: {ESTADO_ESTABLECIMIENTO}")
    else:
        log("     [AVISO] No se pudo forzar Estado establecimiento; se usará el valor visible actual.")

    # Fechas por ID observado en el HTML de error: fechainicio_input y fechafinal_input.
    force_date_input_by_id(driver, "achcensoscuadros-form:fechainicio_input", FECHA_INICIAL)
    force_date_input_by_id(driver, "achcensoscuadros-form:fechafinal_input", FECHA_FINAL)
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    except Exception:
        pass
    log(f"     Fechas: {FECHA_INICIAL} a {FECHA_FINAL}")


def wait_for_download(timeout: int = 240) -> Path:
    log("[5/6] Esperando descarga...")
    log(f"     Carpeta temporal de descarga: {TMP_DOWNLOAD}")
    end = time.time() + timeout
    last_seen = []
    while time.time() < end:
        files = [p for p in TMP_DOWNLOAD.glob("*") if p.is_file()]
        partial = [p for p in files if p.suffix.lower() in [".crdownload", ".tmp"]]
        completed = [p for p in files if p.suffix.lower() not in [".crdownload", ".tmp"]]
        if completed and not partial:
            latest = max(completed, key=lambda p: p.stat().st_mtime)
            # Esperar a que el tamaño se estabilice.
            size1 = latest.stat().st_size
            time.sleep(1.0)
            size2 = latest.stat().st_size
            if size1 == size2 and size2 > 0:
                log(f"     Archivo descargado: {latest.name} ({size2:,} bytes)")
                return latest
        last_seen = files
        time.sleep(1)
    raise TimeoutException(f"No se detectó descarga completa en {TMP_DOWNLOAD}. Archivos vistos: {[p.name for p in last_seen]}")


def generate_and_save(driver: webdriver.Chrome) -> Path:
    log("     Clic en Generar...")
    btn = find_first(driver, [
        (By.ID, "achcensoscuadros-form:j_idt6307"),
        (By.XPATH, "//span[contains(normalize-space(.),'Generar')]/ancestor::button[1]"),
        (By.XPATH, "//button[contains(normalize-space(.),'Generar')]"),
        (By.XPATH, "//input[contains(@value,'Generar')]"),
    ], timeout=20)
    safe_click(driver, btn)
    downloaded = wait_for_download()

    if OUT_CENSO.exists():
        backup = RAW_DIR / f"censo_visitasMPR_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{OUT_CENSO.suffix}"
        shutil.copy2(OUT_CENSO, backup)
        log(f"     Backup del censo anterior: {backup.name}")

    shutil.copy2(downloaded, OUT_CENSO)
    log(f"     Censo actualizado: {OUT_CENSO}")
    return OUT_CENSO


def run_normalizer() -> None:
    if not EJECUTAR_NORMALIZADOR:
        return
    log("[6/6] Ejecutando normalizar_mpr.py...")
    py = str(PYTHON_EXE if PYTHON_EXE.exists() else sys.executable)
    result = subprocess.run([py, str(NORMALIZER)], cwd=str(REPO_ROOT), text=True)
    if result.returncode != 0:
        raise RuntimeError(f"normalizar_mpr.py terminó con código {result.returncode}")
    log("     Normalización finalizada.")


def main() -> None:
    print("=" * 100)
    print("DESCARGA AUTOMATICA CENSO SISA MPR - UESVALLE | V1.5")
    print("=" * 100)
    print(f"Repo      : {REPO_ROOT}")
    print(f"Descargas : {TMP_DOWNLOAD}")
    print(f"Salida    : {OUT_CENSO}")
    print(f"ARO login : {LOGIN_ARO}")
    print(f"Rango     : {FECHA_INICIAL} a {FECHA_FINAL}")

    prepare_dirs()
    user, password = get_credentials()
    driver = build_driver()
    try:
        login(driver, user, password)
        select_login_aro(driver)
        open_censos_visitas(driver)
        configure_report(driver)
        generate_and_save(driver)
        run_normalizer()
        print("=" * 100)
        print("Proceso finalizado correctamente.")
    except Exception as exc:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        png = LOG_DIR / f"error_sisa_mpr_{stamp}.png"
        html = LOG_DIR / f"error_sisa_mpr_{stamp}.html"
        try:
            driver.save_screenshot(str(png))
            html.write_text(driver.page_source, encoding="utf-8", errors="ignore")
            print(f"[ERROR] Captura guardada: {png}")
            print(f"[ERROR] HTML guardado: {html}")
        except Exception:
            pass
        raise
    finally:
        if os.getenv("SISA_DEJAR_NAVEGADOR_ABIERTO", "0") != "1":
            driver.quit()


if __name__ == "__main__":
    main()
