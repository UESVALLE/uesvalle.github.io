#!/usr/bin/env python3
"""Verificación HTTP SIN credenciales. No muestra cuerpos ni sigue redirecciones."""
from __future__ import annotations

import argparse
import json
import pathlib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(url: str, timeout: float) -> tuple[str, str, str]:
    opener = urllib.request.build_opener(NoRedirect)
    status, target, media = "NO_CONECTA", "", ""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "UESVALLE-security-audit/1.0", "Range": "bytes=0-0"},
            method=method,
        )
        try:
            with opener.open(req, timeout=timeout) as response:
                status = str(response.status)
                target = urlparse(response.headers.get("Location", "")).hostname or ""
                media = response.headers.get("Content-Type", "").split(";")[0]
            break
        except urllib.error.HTTPError as exc:
            status = str(exc.code)
            target = urlparse(exc.headers.get("Location", "")).hostname or ""
            media = exc.headers.get("Content-Type", "").split(";")[0]
            exc.close()
            if exc.code in (405, 501) and method == "HEAD":
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError):
            if method == "GET":
                break
    return status, target, media


def interpretation(status: str) -> str:
    if status in ("401", "403"):
        return "DENEGADO_VERIFICAR_RUTA"
    if status == "404":
        return "NO_ENCONTRADO_NO_DEMUESTRA_CIERRE"
    if status.startswith("3"):
        return "REDIRECCION_REVISAR_DESTINO"
    if status.startswith("2"):
        return "REVISAR_URGENTE_RECURSO_ACCESIBLE_O_LOGIN_200"
    return "SIN_EVIDENCIA_CONCLUYENTE"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--targets", default=str(pathlib.Path(__file__).with_name("endpoints_to_verify.json")))
    p.add_argument("--timeout", type=float, default=9.0)
    args = p.parse_args()
    targets = json.loads(pathlib.Path(args.targets).read_text(encoding="utf-8"))["objetivos"]
    print("fecha_utc,id,status,http_destino,content_type,dictamen")
    for entry in targets:
        u = entry["url"]
        if urlparse(u).scheme != "https":
            raise SystemExit("Solo HTTPS")
        status, target, content_type = check(u, args.timeout)
        dt = datetime.now(timezone.utc).isoformat()
        # Sin URL de consulta en output para evitar parámetros accidentales con tokens.
        print(f"{dt},{entry['id']},{status},{target},{content_type},{interpretation(status)}")
    print("NOTA: Una respuesta 200 puede ser login y un 404 no garantiza que otras rutas estén cerradas.")


if __name__ == "__main__":
    main()
