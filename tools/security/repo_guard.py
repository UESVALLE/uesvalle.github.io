#!/usr/bin/env python3
"""Control preventivo para NUEVOS cambios en un repositorio con deuda heredada.

No imprime valores de datos ni de credenciales. No sustituye CI, revisión humana,
clasificación institucional ni inspección del historial previo.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

CODE_SUFFIXES = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".py", ".json", ".yaml", ".yml"}
# Código legado ya contiene datos: este control examina los archivos CAMBIADOS,
# no marca como nuevos todos los datos heredados.
BLOCK_PREFIXES = ("data/", "archive/")
BLOCK_PATH_TOKENS = ("/evidencias/", "/raw/", "/historical/", "/backups/")
BLOCK_SUFFIXES = {".env", ".p12", ".pem", ".key", ".pfx"}
CREDENTIAL_ASSIGNMENT = re.compile(
    r"""(?im)\b(?:const|let|var|export\s+const)\s+
    (?:PASSWORD_TABLERO|PASSWORD_HASH|ACCESS_PASSWORD|SECRET_KEY|
       SERVICE_ROLE_KEY|SUPABASE_SERVICE_ROLE_KEY|API_SECRET)\s*=\s*
    [\"'][^\"'\r\n]{1,}[\"']""",
    re.VERBOSE,
)
KEY_TOKEN_ASSIGNMENT = re.compile(
    r"""(?im)\b(?:api[_-]?key|secret[_-]?key|service[_-]?role[_-]?key)
    \s*[:=]\s*[\"'][A-Za-z0-9_-]{20,}[\"']""",
    re.VERBOSE,
)
# Detección de clave real en .env sin valores impresos.
ENV_ASSIGNMENT = re.compile(r"(?im)^(?:[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|SERVICE_ROLE_KEY))\s*=\s*\S+")


def inspect_file(repo: pathlib.Path, name: str) -> list[str]:
    """Devuelve códigos de regla, sin extraer ni mostrar información del archivo."""
    rel = name.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    path = repo / rel
    if not path.is_file():
        return []
    reason: list[str] = []
    low = rel.lower()
    if low.startswith(BLOCK_PREFIXES) or any(x in "/" + low for x in BLOCK_PATH_TOKENS):
        reason.append("DATA_OR_EVIDENCE_IN_GIT")
    if path.suffix.lower() in BLOCK_SUFFIXES or path.name == ".env":
        reason.append("SENSITIVE_FILE_EXTENSION")
    if path.suffix.lower() in CODE_SUFFIXES or path.name.startswith(".env"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return [*reason, "UNREADABLE_FILE"]
        if CREDENTIAL_ASSIGNMENT.search(content):
            reason.append("CLIENT_OR_SOURCE_CREDENTIAL")
        if KEY_TOKEN_ASSIGNMENT.search(content):
            reason.append("EMBEDDED_KEY_LIKE_TOKEN")
        if path.name.startswith(".env") and ENV_ASSIGNMENT.search(content):
            reason.append("ENVIRONMENT_SECRET")
    return list(dict.fromkeys(reason))


def changed_files(base: str) -> list[str]:
    if not re.fullmatch(r"[a-zA-Z0-9_./-]{1,200}", base) or base.startswith("-"):
        raise ValueError("Referencia Git base inválida")
    res = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--name-only", "--diff-filter=ACMR", "-z", f"{base}...HEAD"],
        check=True, capture_output=True,
    )
    return [s.decode("utf-8", errors="replace") for s in res.stdout.split(b"\0") if s]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Control preventivo de publicación de archivos")
    ap.add_argument("--base", default="origin/main", help="Ref de comparación del PR")
    ap.add_argument("--paths", nargs="*", help="Rutas específicas para prueba o inspección")
    args = ap.parse_args(argv)
    try:
        paths = args.paths if args.paths is not None else changed_files(args.base)
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: No fue posible determinar cambios: {type(exc).__name__}", file=sys.stderr)
        return 2
    repo = pathlib.Path.cwd()
    findings = [(name, inspect_file(repo, name)) for name in paths]
    findings = [(p, rules) for p, rules in findings if rules]
    print(f"Archivos inspeccionados: {len(paths)}. Alertas preventivas: {len(findings)}.")
    for path, rules in findings:
        print(f"BLOQUEADO: {path} | {', '.join(rules)}")
    if findings:
        print("Mover datos/evidencias a almacenamiento controlado y gestionar revisión institucional.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
