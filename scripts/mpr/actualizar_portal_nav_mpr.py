# -*- coding: utf-8 -*-
"""
ACTUALIZAR PORTAL Y NAVEGACIÓN COMÚN - TABLERO MPR UESVALLE
Versión: V1.0

Objetivo:
1. Agregar el módulo "1.6 Mapas de Riesgo MPR" al portal principal index.html.
2. Agregar el enlace al tablero MPR en la navegación común de los tableros HTML existentes.
3. Crear backup antes de modificar archivos.
4. Opcionalmente hacer git add/commit/push.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(r"G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE")

MPR_URL_REL = "dashboards/mpr/seguimiento_mpr.html"
MPR_URL_GH = "https://javiermarin7.github.io/UESVALLE/dashboards/mpr/seguimiento_mpr.html"

MPR_DROPDOWN_ITEM = (
    '<li><a class="dropdown-item" '
    f'href="{MPR_URL_GH}">1.6 Mapas de Riesgo MPR</a></li>'
)

PORTAL_CARD_MARKER = "dashboards/mpr/seguimiento_mpr.html"
BACKUP_ROOT = REPO_ROOT / "archive" / "backups_nav_mpr"


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def backup_file(path: Path, stamp: str) -> Path:
    rel = path.relative_to(REPO_ROOT)
    dst = BACKUP_ROOT / stamp / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def list_html_files() -> list[Path]:
    files = []
    if (REPO_ROOT / "index.html").exists():
        files.append(REPO_ROOT / "index.html")
    dash = REPO_ROOT / "dashboards"
    if dash.exists():
        files.extend(sorted(dash.rglob("*.html")))
    return files


def mark_active_for_file(html: str, file_path: Path) -> str:
    html = re.sub(
        r'(<a\s+class="dropdown-item)\s+active(" href="[^"]*dashboards/mpr/seguimiento_mpr\.html")',
        r'\1\2',
        html,
        flags=re.IGNORECASE,
    )

    if file_path.as_posix().lower().endswith("/dashboards/mpr/seguimiento_mpr.html"):
        html = re.sub(
            r'(<a\s+class="dropdown-item)(" href="[^"]*dashboards/mpr/seguimiento_mpr\.html")',
            r'\1 active\2',
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return html


def update_dashboard_nav(path: Path, stamp: str) -> tuple[bool, str]:
    html = read_text(path)

    if "dashboards/mpr/seguimiento_mpr.html" in html:
        new_html = mark_active_for_file(html, path)
        if new_html != html:
            backup_file(path, stamp)
            write_text(path, new_html)
            return True, "actualizado active MPR"
        return False, "ya contiene enlace MPR"

    patterns = [
        r'(<li><a class="dropdown-item[^"]*" href="[^"]*dashboards/muestras/muestras\.html">[^<]*Muestras</a></li>)',
        r'(<li><a class="dropdown-item[^"]*" href="[^"]*dashboards/dosificacion_cloro/dosificacion_cloro\.html">[^<]*Dosificaci[oó]n de cloro</a></li>)',
        r'(<li><a class="dropdown-item[^"]*" href="[^"]*dashboards/seguimiento_ach/seguimiento_ach\.html">[^<]*Seguimiento[^<]*</a></li>)',
    ]

    new_html = html
    inserted = False

    for pat in patterns:
        m = re.search(pat, new_html, flags=re.IGNORECASE)
        if m:
            insert = m.group(1) + "\n                    " + MPR_DROPDOWN_ITEM
            new_html = new_html[:m.start(1)] + insert + new_html[m.end(1):]
            inserted = True
            break

    if not inserted:
        marker = "1. Agua para consumo humano y saneamiento básico"
        pos = new_html.find(marker)
        if pos != -1:
            ul_start = new_html.find('<ul class="dropdown-menu"', pos)
            ul_end = new_html.find("</ul>", ul_start)
            if ul_start != -1 and ul_end != -1:
                new_html = new_html[:ul_end] + "\n                    " + MPR_DROPDOWN_ITEM + new_html[ul_end:]
                inserted = True

    if not inserted:
        return False, "no se encontró ubicación de navegación"

    new_html = mark_active_for_file(new_html, path)
    backup_file(path, stamp)
    write_text(path, new_html)
    return True, "enlace MPR agregado"


def build_portal_card() -> str:
    return f"""
      <a class="portal-card process-agua" href="{MPR_URL_REL}">
        <div class="portal-card-icon">🗺️</div>
        <div class="portal-card-body">
          <h3>Mapas de Riesgo MPR</h3>
          <p>Seguimiento a sistemas programados frente a visitas 1.3, muestreos 1.4 y actos administrativos 1.5.</p>
          <span class="portal-card-tag">Agua para Consumo Humano</span>
        </div>
      </a>
"""


def update_portal_index(stamp: str) -> tuple[bool, str]:
    path = REPO_ROOT / "index.html"
    if not path.exists():
        return False, "index.html no existe"

    html = read_text(path)
    if PORTAL_CARD_MARKER in html:
        return False, "portal ya contiene tarjeta MPR"

    card = build_portal_card()
    inserted = False
    new_html = html

    pos_muestras = new_html.lower().find("dashboards/muestras/muestras.html")
    if pos_muestras != -1:
        pos_close_a = new_html.find("</a>", pos_muestras)
        if pos_close_a != -1:
            new_html = new_html[:pos_close_a + 4] + "\n" + card + new_html[pos_close_a + 4:]
            inserted = True

    if not inserted:
        for marker in ("</section>", "</main>", "</body>"):
            pos = new_html.lower().find(marker)
            if pos != -1:
                new_html = new_html[:pos] + "\n" + card + "\n" + new_html[pos:]
                inserted = True
                break

    if not inserted:
        return False, "no se encontró sitio para insertar tarjeta"

    if ".portal-card" not in new_html:
        css = """
<style>
.portal-card{
  display:block;
  background:#fff;
  border:1px solid #dbeafe;
  border-radius:1rem;
  box-shadow:0 8px 24px rgba(0,0,0,.06);
  padding:1rem;
  text-decoration:none;
  color:#1f2937;
  transition:all .2s ease;
}
.portal-card:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(29,78,216,.14)}
.portal-card-icon{font-size:2rem;margin-bottom:.5rem}
.portal-card h3{font-size:1.1rem;font-weight:850;color:#1d4ed8;margin:0 0 .35rem}
.portal-card p{font-size:.88rem;color:#667085;margin:0 0 .6rem}
.portal-card-tag{display:inline-block;border-radius:999px;background:#eef4ff;color:#1d4ed8;border:1px solid #c7d7fe;padding:.2rem .55rem;font-size:.75rem;font-weight:800}
</style>
"""
        new_html = new_html.replace("</head>", css + "\n</head>") if "</head>" in new_html else css + new_html

    backup_file(path, stamp)
    write_text(path, new_html)
    return True, "tarjeta MPR agregada al portal"


def run_git(commit_and_push: bool) -> None:
    if not commit_and_push:
        return

    cmds = [
        ["git", "add", "index.html"],
        ["git", "add", "dashboards"],
        ["git", "add", "data/mpr/current"],
        ["git", "add", "data/mpr/raw"],
        ["git", "add", "scripts/mpr"],
        ["git", "commit", "-m", "Agregar modulo MPR al portal y navegacion"],
        ["git", "push"],
    ]

    for cmd in cmds:
        print(f"\n$ {' '.join(cmd)}")
        p = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
        print(p.stdout)
        if p.stderr:
            print(p.stderr)


def main() -> None:
    print("=" * 92)
    print("ACTUALIZAR PORTAL Y NAVEGACIÓN COMÚN - MPR UESVALLE")
    print("=" * 92)
    print(f"Repo raíz: {REPO_ROOT}")

    if not REPO_ROOT.exists():
        raise FileNotFoundError(f"No existe REPO_ROOT: {REPO_ROOT}")

    stamp = now_stamp()
    print(f"Backup: {BACKUP_ROOT / stamp}")

    changed = []

    ok, msg = update_portal_index(stamp)
    print(f"[PORTAL] {msg}")
    if ok:
        changed.append("index.html")

    html_files = list_html_files()
    for path in html_files:
        if path.name.lower() == "index.html":
            continue
        ok, msg = update_dashboard_nav(path, stamp)
        rel = path.relative_to(REPO_ROOT)
        print(f"[{'OK' if ok else '--'}] {rel} | {msg}")
        if ok:
            changed.append(str(rel))

    print("\n" + "=" * 92)
    print(f"Archivos modificados: {len(changed)}")
    for item in changed:
        print(f" - {item}")

    print("\nEnlace esperado:")
    print(MPR_URL_GH)

    ans = input("\n¿Deseas hacer commit y push a GitHub? Escribe S para SI: ").strip().upper()
    run_git(ans == "S")

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()
