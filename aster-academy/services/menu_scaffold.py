"""Safe starter-template creation for registered Aster admin menus."""
from __future__ import annotations

import html
import re
from pathlib import Path


_ROUTE_KEY = re.compile(r"[a-zA-Z0-9_.-]{2,100}\Z")


def template_name_for_route_key(route_key):
    if not _ROUTE_KEY.fullmatch(route_key):
        raise ValueError("Kunci menu tidak valid.")
    return route_key.replace(".", "_").replace("-", "_")


def ensure_menu_scaffold(template_root, route_key, path, label):
    """Create one non-destructive admin template for a new local admin route."""
    safe_name = template_name_for_route_key(route_key)
    if not path.startswith("/admin/") or "?" in path or "#" in path:
        raise ValueError("Scaffold otomatis hanya untuk path admin lokal.")
    target = Path(template_root) / f"{safe_name}.html"
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_label = html.escape(label, quote=True)
    target.write_text(
        "<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{safe_label} · Aster Academy</title></head><body>"
        "<main class=\"admin-page\"><h1>" + safe_label + "</h1>"
        "<p>Halaman baru ini memakai shell admin, sidebar berbasis role, dan CSRF otomatis untuk form POST.</p>"
        "</main></body></html>",
        encoding="utf-8",
    )
    return target
