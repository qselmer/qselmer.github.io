#!/usr/bin/env python3
"""Check external HTTP(S) links in a rendered Quarto site.

The checker fails on confirmed 404/410 responses and unresolved network failures.
Authentication, anti-bot and rate-limit responses (401/403/429) are treated as
reachable-but-restricted rather than dead links.
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

USER_AGENT = "qselmer.github.io-link-check/1.0 (+https://qselmer.github.io)"
OK_RESTRICTED = {401, 403, 405, 429}
FAIL_CODES = {404, 410}


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
        if method == "GET":
            response.read(1)
        return int(response.status), str(response.geturl())


def check_url(url: str) -> tuple[str, str, int | None, str]:
    errors: list[str] = []
    for method in ("HEAD", "GET"):
        for attempt in range(2):
            try:
                code, final_url = request_once(url, method)
                return url, "ok", code, final_url
            except HTTPError as exc:
                code = int(exc.code)
                if code in OK_RESTRICTED:
                    return url, "restricted", code, str(exc.geturl())
                if code in FAIL_CODES:
                    if method == "HEAD":
                        break
                    return url, "dead", code, str(exc.geturl())
                errors.append(f"{method} HTTP {code}")
            except (URLError, TimeoutError, OSError) as exc:
                errors.append(f"{method} {type(exc).__name__}: {exc}")
            if attempt == 0:
                time.sleep(0.5)
    return url, "error", None, "; ".join(errors[-4:])


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

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for result in pool.map(check_url, links):
            results.append(result)

    failures = [r for r in results if r[1] in {"dead", "error"}]
    restricted = [r for r in results if r[1] == "restricted"]

    for url, status, code, detail in failures:
        print(f"FAIL {status.upper():10} {code or '-':>3} {url} -> {detail}")
    if failures:
        raise SystemExit(f"External-link validation FAIL: {len(failures)} of {len(results)} URLs failed")

    print(
        f"External-link validation PASS: {len(results)} unique HTTP(S) URLs checked; "
        f"{len(restricted)} reachable but access/rate restricted"
    )


if __name__ == "__main__":
    main()
