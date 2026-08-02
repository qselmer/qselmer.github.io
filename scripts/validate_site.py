"""Validate accessibility and internal references in the generated Jekyll site."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.image_alt_missing: list[str] = []
        self.buttons: list[dict[str, str | None]] = []
        self._button: dict[str, str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "img" and "alt" not in values:
            self.image_alt_missing.append(values.get("src") or "<unknown>")
        if tag == "button":
            self._button = {"aria-label": values.get("aria-label"), "title": values.get("title"), "text": ""}
            self.buttons.append(self._button)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button":
            self._button = None

    def handle_data(self, data: str) -> None:
        if self._button is not None:
            self._button["text"] = (self._button.get("text") or "") + data


def output_path(site: Path, url_path: str) -> Path:
    clean = unquote(url_path).lstrip("/")
    candidate = site / clean
    if clean == "":
        return site / "index.html"
    if candidate.is_dir() or url_path.endswith("/"):
        return candidate / "index.html"
    if candidate.suffix:
        return candidate
    html_candidate = candidate.with_suffix(".html")
    if html_candidate.exists():
        return html_candidate
    return candidate / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", default="_site")
    args = parser.parse_args()
    site = Path(args.site).resolve()
    documents: dict[Path, DocumentParser] = {}
    failures: list[str] = []

    for html_file in sorted(site.rglob("*.html")):
        parsed = DocumentParser()
        parsed.feed(html_file.read_text(encoding="utf-8"))
        documents[html_file.resolve()] = parsed
        duplicates = [value for value, count in Counter(parsed.ids).items() if count > 1]
        if duplicates:
            failures.append(f"{html_file}: duplicate IDs: {', '.join(duplicates)}")
        if parsed.image_alt_missing:
            failures.append(f"{html_file}: images without alt: {', '.join(parsed.image_alt_missing)}")
        for button in parsed.buttons:
            name = button.get("aria-label") or button.get("title") or button.get("text")
            if not name or not name.strip():
                failures.append(f"{html_file}: button without an accessible name")

    site_url = "https://qselmer.github.io/"
    for html_file, parsed in documents.items():
        relative = html_file.relative_to(site).as_posix()
        source_url = urljoin(site_url, relative.replace("index.html", ""))
        for raw_href in parsed.links:
            href = raw_href.strip()
            if not href or href == "#" or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            absolute = urlsplit(urljoin(source_url, href))
            if absolute.netloc and absolute.netloc != "qselmer.github.io":
                continue
            target = output_path(site, absolute.path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                failures.append(f"{html_file}: broken internal link {href}")
                continue
            if absolute.fragment and target.suffix.lower() == ".html":
                target_doc = documents.get(target)
                if target_doc is not None and unquote(absolute.fragment) not in target_doc.ids:
                    failures.append(f"{html_file}: missing fragment target {href}")

    demo_markers = (
        "A variety of common markup showing how the theme styles them.",
        "This is a page not in the menu.",
        "Locations of key files/directories",
    )
    for html_file in site.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        for marker in demo_markers:
            if marker in text:
                failures.append(f"{html_file}: visible demo content: {marker}")

    if failures:
        print("Site validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Site validation passed: {len(documents)} HTML documents checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
