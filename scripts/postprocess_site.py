#!/usr/bin/env python3
"""Post-render certification helpers for qselmer.github.io.

This script runs from Quarto's project post-render hook. It adds canonical URLs
and 404 indexing policy to rendered pages, hardens target=_blank links, and
materializes static compatibility redirects declared in config/legacy-routes.json.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
SITE_URL = "https://qselmer.github.io"
ROUTES = ROOT / "config" / "legacy-routes.json"


def route_for_page(page: Path) -> str:
    rel = page.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def canonical_url(route: str) -> str:
    return SITE_URL + route


def insert_before_head_end(text: str, fragment: str) -> str:
    marker = "</head>"
    if marker not in text:
        raise RuntimeError("Rendered HTML is missing </head>")
    return text.replace(marker, fragment + "\n" + marker, 1)


def harden_blank_links(text: str) -> str:
    pattern = re.compile(r'<a(?P<attrs>[^>]*\btarget="_blank"[^>]*)>', re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        if re.search(r"\brel\s*=", attrs, flags=re.IGNORECASE):
            return match.group(0)
        return f'<a{attrs} rel="noopener noreferrer">'

    return pattern.sub(repl, text)


def postprocess_rendered_pages() -> None:
    if not SITE.is_dir():
        raise RuntimeError("_site does not exist")

    for page in sorted(SITE.rglob("*.html")):
        text = page.read_text(encoding="utf-8", errors="strict")
        route = route_for_page(page)

        if route != "/404.html" and 'rel="canonical"' not in text:
            href = html.escape(canonical_url(route), quote=True)
            text = insert_before_head_end(text, f'<link rel="canonical" href="{href}">')

        if route == "/404.html" and 'name="robots"' not in text:
            text = insert_before_head_end(
                text, '<meta name="robots" content="noindex,follow">'
            )

        text = harden_blank_links(text)
        page.write_text(text, encoding="utf-8")


def redirect_output_path(legacy: str) -> Path:
    if not legacy.startswith("/") or ".." in legacy:
        raise RuntimeError(f"Unsafe legacy route: {legacy}")
    rel = legacy.lstrip("/")
    if legacy.endswith("/"):
        rel += "index.html"
    if not rel:
        raise RuntimeError("Root route cannot be a redirect")
    return SITE / rel


def redirect_document(legacy: str, target: str) -> str:
    target_url = canonical_url(target)
    escaped_url = html.escape(target_url, quote=True)
    label = html.escape(target, quote=False)
    js_url = json.dumps(target_url)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="noindex,follow">\n'
        '<meta name="description" content="Compatibility redirect for a moved page on qselmer.github.io.">\n'
        f'<link rel="canonical" href="{escaped_url}">\n'
        f'<meta http-equiv="refresh" content="0; url={escaped_url}">\n'
        "<title>Page moved - Elmer Quispe-Salazar</title>\n"
        f"<script>window.location.replace({js_url});</script>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        "<h1>Page moved</h1>\n"
        f'<p>This address has moved to <a href="{escaped_url}">{label}</a>.</p>\n'
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


def build_redirects() -> int:
    payload = json.loads(ROUTES.read_text(encoding="utf-8"))
    routes = payload.get("routes", [])
    count = 0
    for item in routes:
        if item.get("status") != "redirect_required":
            continue
        legacy = str(item["legacy"])
        target = str(item["target"])
        output = redirect_output_path(legacy)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(redirect_document(legacy, target), encoding="utf-8")
        count += 1
    return count


def main() -> None:
    postprocess_rendered_pages()
    count = build_redirects()
    print(f"Post-render PASS: canonical metadata hardened; {count} legacy redirects generated")


if __name__ == "__main__":
    main()
