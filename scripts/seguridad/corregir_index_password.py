from pathlib import Path
from datetime import datetime
import shutil
import re

REPO = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")
INDEX = REPO / "index.html"

backup = REPO / "archive" / "backups_password_tableros" / f"index_fix_{datetime.now():%Y%m%d_%H%M%S}.html"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(INDEX, backup)

html = INDEX.read_text(encoding="utf-8", errors="ignore")

# 1. Eliminar el dashboardContent mal cerrado antes de <main>
html = re.sub(
    r'<div id="dashboardContent" style="display:none;">\s*<!--[\s\S]*?BLOQUE DE ACCESO UESVALLE - FIN[\s\S]*?-->\s*</div>\s*</div>\s*(?=<main class="page">)',
    '<div id="dashboardContent" style="display:none;">\n',
    html,
    count=1,
    flags=re.IGNORECASE
)

# 2. Si no encontró por comentario, aplicar corrección alternativa cercana a <main>
html = re.sub(
    r'<div id="dashboardContent" style="display:none;">\s*</div>\s*</div>\s*(?=<main class="page">)',
    '<div id="dashboardContent" style="display:none;">\n',
    html,
    count=1,
    flags=re.IGNORECASE
)

# 3. Insertar cierre del dashboardContent antes del script de acceso si no está correctamente
html = re.sub(
    r'(?=<!-- ============================================================\s*SCRIPT DE ACCESO UESVALLE - INICIO)',
    '\n</div>\n',
    html,
    count=1,
    flags=re.IGNORECASE
)

INDEX.write_text(html, encoding="utf-8")

print("Corrección aplicada a index.html")
print(f"Backup creado en: {backup}")