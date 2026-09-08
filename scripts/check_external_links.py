#!/usr/bin/env python3
"""Audit external HTTP(S) links in a rendered Quarto site.

CI fails only for terminal link failures confirmed by an HTTP GET (404/410).
Authentication, anti-bot, rate-limit, gateway, TLS, timeout and other network
conditions are reported separately as restricted or unverified. This avoids
turning third-party availability and CI-proxy behaviour into false dead-link
failures while still making every unresolved URL visible in the build log.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import ssl
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

USER_AGENT = "qselmer.github.io-link-check/1.1 (+https://qselmer.github.io)"
RESTRICTED_CODES = {401, 403, 405, 429}
TERMINAL_CODES = {404, 410}
TRANSIENT_CODES = {408, 425, 500, 502, 503, 504}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        data = dict(attrs)
        href = (data.get("href") or "").strip()
        if urlsplit(href).scheme in {"http", "https"}:
            self.links.add(href)


def collect_links(site: Path) -> list[str]:
    links: set[str] = set()
    for page in site.rglob("*.html"):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        links.update(parser.links)
    return sorted(links)


def request_once(url: str, method: str) -> tuple[int, str]:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
        },
        method=method,
    )
    context = ssl.create_default_context()
    with urlopen(req, timeout=12, context=context) as response:
        # Opening the response is sufficient for link validation. Do not read
        # the body: some redirect/streaming endpoints close it immediately.
        return int(response.status), str(response.geturl())


def check_url(url: str) -> tuple[str, str, int | None, str]:
    observations: list[str] = []
    terminal_head_code: int | None = None

    for method in ("HEAD", "GET"):
        for attempt in range(2):
            try:
                code, final_url = request_once(url, method)
                if 200 <= code < 400:
                    return url, "ok", code, final_url
                observations.append(f"{method} HTTP {code}")
            except HTTPError as exc:
                code = int(exc.code)
                final_url = str(exc.geturl())
                if code in RESTRICTED_CODES:
                    return url, "restricted", code, final_url
                if code in TERMINAL_CODES:
                    if method == "GET":
                        return url, "dead", code, final_url
                    terminal_head_code = code
                    observations.append(f"HEAD HTTP {code}; GET confirmation required")
                    break
                if code in TRANSIENT_CODES:
                    observations.append(f"{method} transient HTTP {code}")
                else:
                    observations.append(f"{method} HTTP {code}")
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                observations.append(f"{method} {type(exc).__name__}: {exc}")
            except Exception as exc:  # third-party transport quirks must be visible, not fatal
                observations.append(f"{method} {type(exc).__name__}: {exc}")

            if attempt == 0:
                time.sleep(0.5)

    detail = "; ".join(observations[-6:]) or "No conclusive HTTP response"
    if terminal_head_code is not None:
        detail = f"HEAD returned {terminal_head_code}, but GET did not confirm a terminal failure; {detail}"
    return url, "unverified", None, detail


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", default="_site")
    args = parser.parse_args()
    site = Path(args.site)
    if not site.is_dir():
        raise SystemExit(f"Rendered site not found: {site}")

    links = collect_links(site)
    if not links:
        raise SystemExit("No external links found")

    results: list[tuple[str, str, int | None, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results.extend(pool.map(check_url, links))

    dead = [r for r in results if r[1] == "dead"]
    restricted = [r for r in results if r[1] == "restricted"]
    unverified = [r for r in results if r[1] == "unverified"]
    ok = [r for r in results if r[1] == "ok"]

    for url, status, code, detail in dead:
        print(f"FAIL {status.upper():10} {code or '-':>3} {url} -> {detail}")
    for url, status, code, detail in restricted:
        print(f"INFO {status.upper():10} {code or '-':>3} {url} -> {detail}")
    for url, status, code, detail in unverified:
        print(f"WARN {status.upper():10} {code or '-':>3} {url} -> {detail}")

    if dead:
        raise SystemExit(
            f"External-link audit FAIL: {len(dead)} confirmed dead URL(s) of {len(results)} checked"
        )

    print(
        "External-link audit PASS: "
        f"{len(results)} unique HTTP(S) URLs; {len(ok)} reachable, "
        f"{len(restricted)} restricted, {len(unverified)} unverified, "
        "0 confirmed 404/410"
    )


if __name__ == "__main__":
    main()
