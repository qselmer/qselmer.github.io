#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "data" / "publications.json"
TARGET = ROOT / "publications" / "_generated.md"

DISPLAY_ORDER = [
    "Journal articles",
    "Preprints & working papers",
    "Books & chapters",
    "Theses",
    "Reports & technical outputs",
]

HEADING = {
    "Journal articles": ("Peer-reviewed articles", "papers"),
    "Preprints & working papers": ("Preprints and forthcoming manuscripts", "preprints"),
    "Books & chapters": ("Books and book chapters", "books"),
    "Theses": ("Theses", "theses"),
    "Reports & technical outputs": ("Reports and institutional technical outputs", "reports"),
}

EMPTY_MESSAGE = {
    "Journal articles": "_No journal articles are currently listed._",
    "Preprints & working papers": "_No preprints or forthcoming manuscripts are currently listed._",
    "Books & chapters": "_No books or book chapters are currently listed._",
    "Theses": "_No theses are currently listed._",
    "Reports & technical outputs": "_No reports or institutional technical outputs are currently listed._",
}

# Only outlets or repositories whose open-access status is known are labelled.
# Scientia Marina distributes its online content under CC BY 4.0.
OPEN_ACCESS_OUTLETS = {"scientia marina"}
OPEN_ACCESS_HOSTS = {
    "zenodo.org",
    "www.zenodo.org",
    "arxiv.org",
    "www.arxiv.org",
    "biorxiv.org",
    "www.biorxiv.org",
    "osf.io",
    "www.osf.io",
}


def load_catalogue() -> dict[str, Any]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    publications = payload.get("publications")
    if not isinstance(publications, list):
        raise RuntimeError("assets/data/publications.json must contain a publications list")
    declared = payload.get("count")
    if declared is not None and declared != len(publications):
        raise RuntimeError("Publication count does not match publications list length")
    for index, pub in enumerate(publications, start=1):
        if not isinstance(pub, dict):
            raise RuntimeError(f"Publication {index} is not an object")
        for field in ("title", "year", "output_category"):
            if not str(pub.get(field) or "").strip():
                raise RuntimeError(f"Publication {index} is missing required field: {field}")
    return payload


def initials(given: str) -> str:
    parts = re.findall(r"[^\W\d_]+", given, flags=re.UNICODE)
    return " ".join(f"{part[0].upper()}." for part in parts if part)


def apa_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip())
    if not clean:
        return ""
    if "," in clean:
        family, given = [part.strip() for part in clean.split(",", 1)]
    else:
        parts = clean.split()
        family = parts[-1]
        given = " ".join(parts[:-1])
    rendered = f"{family}, {initials(given)}".strip().rstrip(",")
    low = clean.casefold()
    if "quispe-salazar" in low and "elmer" in low:
        return f"**{rendered}**"
    return rendered


def authors_apa(pub: dict[str, Any]) -> str:
    names = [str(value).strip() for value in (pub.get("authors") or []) if str(value).strip()]
    if not names:
        names = ["Elmer Quispe-Salazar"]
    rendered = [apa_name(name) for name in names]
    if len(rendered) == 1:
        return rendered[0]
    if len(rendered) == 2:
        return f"{rendered[0]} & {rendered[1]}"
    return f"{', '.join(rendered[:-1])}, & {rendered[-1]}"


def source_apa(pub: dict[str, Any]) -> str:
    journal = str(pub.get("journal") or pub.get("outlet") or pub.get("type") or "").strip()
    volume = str(pub.get("volume") or "").strip()
    issue = str(pub.get("issue") or "").strip()
    pages = str(pub.get("pages") or "").strip()
    if not journal:
        return ""
    source = f"*{journal}*"
    if volume:
        source = f"*{journal}, {volume}*"
    if issue:
        source += f"({issue})"
    if pages:
        source += f", {pages}"
    return source + "."


def canonical_doi(value: str) -> str:
    doi = value.strip()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)


def canonical_doi_url(value: str) -> str:
    doi = canonical_doi(value)
    return f"https://doi.org/{doi}" if doi else ""


def badge(label: str, value: str, tone: str = "blue", url: str = "") -> str:
    label_html = html.escape(label)
    value_html = html.escape(value)
    body = (
        f'<span class="qs-badge-label">{label_html}</span>'
        f'<span class="qs-badge-value">{value_html}</span>'
    )
    classes = f"qs-badge qs-badge-{tone}"
    if url:
        return f'<a class="{classes}" href="{html.escape(url, quote=True)}">{body}</a>'
    return f'<span class="{classes}">{body}</span>'


def is_open_access(pub: dict[str, Any]) -> bool:
    journal = str(pub.get("journal") or pub.get("outlet") or "").strip().casefold()
    if journal in OPEN_ACCESS_OUTLETS:
        return True
    url = str(pub.get("url") or "").strip()
    if not url:
        return False
    return urlparse(url).netloc.casefold() in OPEN_ACCESS_HOSTS


def reference(pub: dict[str, Any]) -> str:
    authors = authors_apa(pub)
    year = str(pub.get("year") or "n.d.")
    title = str(pub.get("title") or "Untitled work").strip()
    parts = [f"- {authors} ({year}). {title}."]
    source = source_apa(pub)
    if source:
        parts.append(source)

    doi = str(pub.get("doi") or "").strip()
    url = str(pub.get("url") or "").strip()
    badges: list[str] = []
    if doi:
        clean_doi = canonical_doi(doi)
        badges.append(badge("DOI", clean_doi, "blue", canonical_doi_url(doi)))
    elif url:
        parts.append(f"[View output]({url})")
    if is_open_access(pub):
        badges.append(badge("Open", "access", "green", url or canonical_doi_url(doi)))
    if badges:
        parts.append(f'<span class="qs-badge-row qs-publication-badges">{"".join(badges)}</span>')
    return " ".join(parts)


def year_value(pub: dict[str, Any]) -> int:
    try:
        return int(pub.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def build_text(payload: dict[str, Any]) -> str:
    publications = payload["publications"]
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in DISPLAY_ORDER}
    for pub in publications:
        category = str(pub.get("output_category") or "Other research outputs")
        if category in grouped:
            grouped[category].append(pub)

    lines = [
        "<!-- AUTO-GENERATED FROM assets/data/publications.json. DO NOT EDIT BY HAND. -->",
        "",
    ]
    for category in DISPLAY_ORDER:
        heading, anchor = HEADING[category]
        items = grouped[category]
        lines.extend([f"## {heading} {{#{anchor}}}", ""])
        if items:
            for pub in sorted(items, key=lambda item: (-year_value(item), str(item.get("title") or "").casefold())):
                lines.append(reference(pub))
            lines.append("")
        else:
            lines.extend([EMPTY_MESSAGE[category], ""])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Quarto publication fragment from the canonical local JSON mirror.")
    parser.add_argument("--check", action="store_true", help="Fail if the generated fragment is stale.")
    args = parser.parse_args()

    payload = load_catalogue()
    expected = build_text(payload)
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""

    if args.check:
        if current != expected:
            raise SystemExit("publications/_generated.md is stale; run python scripts/build_publications.py")
        print("Publication fragment is synchronized with assets/data/publications.json")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if current == expected:
        print("Publication fragment already up to date")
        return 0
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Rendered {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
