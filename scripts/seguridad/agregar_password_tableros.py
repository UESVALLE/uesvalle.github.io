from pathlib import Path
from datetime import datetime
import shutil
import re

# ============================================================
# CONFIGURACIÓN
# ============================================================

REPO = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

PASSWORD = "Uesvalle2026"

BACKUP_DIR = REPO / "archive" / "backups_password_tableros" / datetime.now().strftime("%Y%m%d_%H%M%S")

# Archivos HTML a proteger
html_files = []

# index principal
index_file = REPO / "index.html"
if index_file.exists():
    html_files.append(index_file)

# todos los html dentro de dashboards
dashboards_dir = REPO / "dashboards"
if dashboards_dir.exists():
    html_files.extend(dashboards_dir.rglob("*.html"))


# ============================================================
# BLOQUES A INSERTAR
# ============================================================

LOGIN_HTML = """
<!-- ============================================================
BLOQUE DE ACCESO UESVALLE - INICIO
============================================================ -->
<div id="loginScreen" style="
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  background:linear-gradient(135deg,#f1f5f9,#e0f2fe);
  font-family:Arial, sans-serif;
  padding:20px;
">
  <div style="
    background:white;
    padding:34px;
    border-radius:18px;
    box-shadow:0 14px 35px rgba(15,23,42,.16);
    width:380px;
    max-width:95%;
    text-align:center;
    border:1px solid #e5e7eb;
  ">
    <div style="
      width:64px;
      height:64px;
      margin:0 auto 16px auto;
      border-radius:18px;
      background:#0f766e;
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:30px;
      font-weight:800;
    ">
      U
    </div>

    <h2 style="margin:0 0 8px 0;color:#0f172a;font-size:24px;">
      Acceso UESVALLE
    </h2>

    <p style="margin:0 0 20px 0;color:#64748b;font-size:14px;">
      Ingrese la contraseña para consultar los tableros.
    </p>

    <input
      id="passwordInput"
      type="password"
      placeholder="Contraseña"
      autocomplete="current-password"
      onkeydown="if(event.key === 'Enter') validarAcceso();"
      style="
        width:100%;
        box-sizing:border-box;
        padding:13px 14px;
        margin:0 0 14px 0;
        border:1px solid #cbd5e1;
        border-radius:10px;
        font-size:15px;
        outline:none;
      "
    >

    <button
      onclick="validarAcceso()"
      style="
        width:100%;
        padding:13px;
        background:#0f766e;
        color:white;
        border:none;
        border-radius:10px;
        font-weight:800;
        font-size:15px;
        cursor:pointer;
      "
    >
      Ingresar
    </button>

    <div id="loginError" style="
      display:none;
      margin-top:14px;
      color:#b91c1c;
      background:#fee2e2;
      border:1px solid #fecaca;
      border-radius:10px;
      padding:10px;
      font-size:13px;
      font-weight:700;
    ">
      Contraseña incorrecta.
    </div>

    <p style="margin:18px 0 0 0;color:#94a3b8;font-size:12px;">
      Portal de tableros institucionales
    </p>
  </div>
</div>

<div id="dashboardContent" style="display:none;">
<!-- ============================================================
BLOQUE DE ACCESO UESVALLE - FIN
============================================================ -->
"""

ACCESS_SCRIPT = f"""
<!-- ============================================================
SCRIPT DE ACCESO UESVALLE - INICIO
============================================================ -->
<script>
const PASSWORD_TABLERO = "{PASSWORD}";
const ACCESS_KEY_UESVALLE = "accesoTableroUESVALLE";

function mostrarTableroUESVALLE() {{
  const loginScreen = document.getElementById("loginScreen");
  const dashboardContent = document.getElementById("dashboardContent");

  if (loginScreen) loginScreen.style.display = "none";
  if (dashboardContent) dashboardContent.style.display = "block";

  setTimeout(() => {{
    window.dispatchEvent(new Event("resize"));
  }}, 300);
}}

function validarAcceso() {{
  const input = document.getElementById("passwordInput");
  const error = document.getElementById("loginError");
  const pass = input ? input.value : "";

  if (pass === PASSWORD_TABLERO) {{
    localStorage.setItem(ACCESS_KEY_UESVALLE, "ok");
    mostrarTableroUESVALLE();
  }} else {{
    if (error) error.style.display = "block";
    if (input) {{
      input.value = "";
      input.focus();
    }}
  }}
}}

function cerrarSesionTablero() {{
  localStorage.removeItem(ACCESS_KEY_UESVALLE);
  location.reload();
}}

window.addEventListener("DOMContentLoaded", () => {{
  if (localStorage.getItem(ACCESS_KEY_UESVALLE) === "ok") {{
    mostrarTableroUESVALLE();
  }} else {{
    const input = document.getElementById("passwordInput");
    if (input) input.focus();
  }}
}});
</script>
<!-- ============================================================
SCRIPT DE ACCESO UESVALLE - FIN
============================================================ -->
"""


# ============================================================
# FUNCIONES
# ============================================================

def ya_tiene_password(html: str) -> bool:
    marcas = [
        "BLOQUE DE ACCESO UESVALLE",
        "SCRIPT DE ACCESO UESVALLE",
        "accesoTableroUESVALLE",
        "loginScreen",
        "dashboardContent"
    ]
    return any(marca in html for marca in marcas)


def proteger_html(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="ignore")

    if ya_tiene_password(html):
        return "YA_PROTEGIDO"

    if "<body" not in html.lower() or "</body>" not in html.lower():
        return "SIN_BODY"

    # Backup
    relative = path.relative_to(REPO)
    backup_path = BACKUP_DIR / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)

    # Insertar login justo después de la apertura de <body ...>
    body_open_pattern = re.compile(r"(<body[^>]*>)", re.IGNORECASE)
    html = body_open_pattern.sub(r"\1\n" + LOGIN_HTML, html, count=1)

    # Cerrar dashboardContent y agregar script antes de </body>
    body_close_pattern = re.compile(r"(</body>)", re.IGNORECASE)
    html = body_close_pattern.sub("\n</div>\n" + ACCESS_SCRIPT + r"\n\1", html, count=1)

    path.write_text(html, encoding="utf-8")

    return "PROTEGIDO"


# ============================================================
# EJECUCIÓN
# ============================================================

def main():
    print("=" * 80)
    print("AGREGAR CONTRASEÑA A TABLEROS HTML UESVALLE")
    print("=" * 80)
    print(f"Repositorio: {REPO}")
    print(f"Archivos encontrados: {len(html_files)}")
    print(f"Backup: {BACKUP_DIR}")
    print("-" * 80)

    resultados = {
        "PROTEGIDO": 0,
        "YA_PROTEGIDO": 0,
        "SIN_BODY": 0,
        "ERROR": 0
    }

    for path in html_files:
        try:
            estado = proteger_html(path)
            resultados[estado] = resultados.get(estado, 0) + 1
            print(f"[{estado}] {path.relative_to(REPO)}")
        except Exception as e:
            resultados["ERROR"] += 1
            print(f"[ERROR] {path.relative_to(REPO)} -> {e}")

    print("-" * 80)
    print("RESUMEN")
    for k, v in resultados.items():
        print(f"{k}: {v}")

    print("=" * 80)
    print("Proceso finalizado.")


if __name__ == "__main__":
    main()