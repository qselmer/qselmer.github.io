#!/usr/bin/env python3
"""Central source and rendered-site validation for qselmer.github.io."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from site_config import ROOT, load_config


BUILD_CHECKS = (
    "build_publications.py",
    "build_conferences.py",
    "build_software.py",
    "build_teaching.py",
    "build_data_resources.py",
    "build_blog.py",
    "build_home.py",
)


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def normalized_text(path: Path) -> str:
    return html_lib.unescape(path.read_text(encoding="utf-8"))


def require_text(path: Path, expected: str) -> None:
    text = normalized_text(path)
    if expected not in text:
        raise RuntimeError(f"{path.relative_to(ROOT)} is missing canonical value: {expected}")


def reject_text(path: Path, forbidden: str) -> None:
    text = normalized_text(path)
    if forbidden in text:
        raise RuntimeError(f"{path.relative_to(ROOT)} contains forbidden legacy value: {forbidden}")


def run_build_checks() -> None:
    for script in BUILD_CHECKS:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), "--check"],
            cwd=ROOT,
            check=True,
        )


def validate_source() -> None:
    config = load_config()
    identity = config["identity"]

    json_paths = (
        ["config/site.json"]
        + config.get("website_mirrors", [])
        + config.get("website_registries", [])
        + config.get("derived_json", [])
    )
    for relative in json_paths:
        load_json(ROOT / relative)

    for relative in config.get("generated_fragments", []):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty generated artifact: {relative}")

    publications = load_json(ROOT / "assets/data/publications.json")
    metrics = load_json(ROOT / "assets/data/research-metrics.json")
    if str(publications.get("orcid") or "") != identity["orcid"]:
        raise RuntimeError("Publications ORCID does not match config/site.json")
    if str(metrics.get("orcid") or "") != identity["orcid"]:
        raise RuntimeError("Research-metrics ORCID does not match config/site.json")

    contact = ROOT / "contact" / "index.qmd"
    quarto = ROOT / "_quarto.yml"
    home = ROOT / "index.qmd"

    require_text(contact, identity["email"])
    require_text(contact, identity["linkedin"])
    require_text(quarto, identity["linkedin"])
    require_text(home, identity["headline"])
    require_text(home, identity["signature"])

    for forbidden in config.get("forbidden_legacy_identity", []):
        reject_text(contact, forbidden)
        reject_text(quarto, forbidden)
        reject_text(home, forbidden)

    cv = ROOT / "files" / "CV.pdf"
    if not cv.is_file() or cv.stat().st_size == 0:
        raise RuntimeError("files/CV.pdf is missing or empty")

    run_build_checks()
    print(
        "Source validation PASS: canonical identity, JSON catalogues, registries, "
        "generated fragments, CV, and deterministic builders"
    )


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.append(value)


def internal_target(site: Path, page: Path, reference: str) -> list[Path]:
    ref = reference.strip()
    if not ref or ref.startswith(("#", "//")):
        return []

    parsed = urlsplit(ref)
    if parsed.scheme:
        return []
    path_text = unquote(parsed.path)
    if not path_text:
        return []

    if path_text.startswith("/"):
        target = site / path_text.lstrip("/")
    else:
        target = page.parent / path_text

    candidates: list[Path] = []
    if path_text.endswith("/"):
        candidates.append(target / "index.html")
    else:
        candidates.append(target)
        if target.suffix == "":
            candidates.extend((target.with_suffix(".html"), target / "index.html"))
        if target.is_dir():
            candidates.append(target / "index.html")
    return candidates


def validate_internal_links(site: Path) -> tuple[int, int]:
    html_files = sorted(site.rglob("*.html"))
    checked = 0
    missing: list[tuple[Path, str]] = []

    for page in html_files:
        parser = ReferenceParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for ref in parser.references:
            candidates = internal_target(site, page, ref)
            if not candidates:
                continue
            checked += 1
            if not any(candidate.exists() for candidate in candidates):
                missing.append((page.relative_to(site), ref))

    if missing:
        details = "\n".join(f"  {page}: {ref}" for page, ref in missing[:50])
        raise RuntimeError(
            f"{len(missing)} missing internal references detected:\n{details}"
        )
    return len(html_files), checked


def validate_rendered() -> None:
    config = load_config()
    identity = config["identity"]
    site = ROOT / "_site"
    if not site.is_dir():
        raise RuntimeError("_site does not exist; render Quarto before rendered validation")

    home = site / "index.html"
    contact = site / "contact" / "index.html"
    cv_page = site / "cv" / "index.html"
    resume = site / "resume" / "index.html"
    rendered_pdf = site / "files" / "CV.pdf"
    source_pdf = ROOT / "files" / "CV.pdf"

    for path in (home, contact, cv_page, resume, rendered_pdf):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Rendered artifact missing or empty: {path.relative_to(site)}")

    require_text(home, identity["headline"])
    require_text(home, identity["signature"])
    for label in ("ORCID works", "OpenAlex works", "Citations", "h-index", "i10-index", "OpenAlex"):
        require_text(home, label)
    require_text(home, "research/index.html")
    reject_text(home, '<pre><code><p class="qs-eyebrow">')
    reject_text(home, '<pre><code><span class="qs-metric-value">')

    require_text(contact, identity["email"])
    require_text(contact, "elmer-quispe-salazar-104b6b1a4")
    for forbidden in config.get("forbidden_legacy_identity", []):
        reject_text(contact, forbidden)

    if source_pdf.stat().st_size != rendered_pdf.stat().st_size:
        raise RuntimeError("Rendered CV.pdf size differs from source CV.pdf")

    pages, references = validate_internal_links(site)
    print(
        f"Rendered validation PASS: {pages} HTML pages, "
        f"{references} internal references checked, 0 missing"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()

    if args.mode in {"source", "all"}:
        validate_source()
    if args.mode in {"rendered", "all"}:
        validate_rendered()


if __name__ == "__main__":
    main()
