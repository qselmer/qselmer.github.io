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
CONFIG = ROOT / "config" / "site.json"
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

NAV_LABEL = {
    "Journal articles": "Papers",
    "Preprints & working papers": "Preprints",
    "Books & chapters": "Books",
    "Theses": "Theses",
    "Reports & technical outputs": "Reports",
}

OPEN_ACCESS_OUTLETS = {"scientia marina"}
OPEN_ACCESS_HOSTS = {
    "zenodo.org", "www.zenodo.org", "arxiv.org", "www.arxiv.org",
    "biorxiv.org", "www.biorxiv.org", "osf.io", "www.osf.io",
}
YEAR_GROUP_THRESHOLD = 4


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def load_catalogue() -> dict[str, Any]:
    payload = load_json(SOURCE)
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


def load_identity() -> dict[str, Any]:
    identity = load_json(CONFIG).get("identity")
    if not isinstance(identity, dict):
        raise RuntimeError("config/site.json must contain identity metadata")
    return identity


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
    if "quispe-salazar" in clean.casefold() and "elmer" in clean.casefold():
        return f"**{rendered}**"
    return rendered


def authors_apa(pub: dict[str, Any]) -> str:
    names = [str(value).strip() for value in (pub.get("authors") or []) if str(value).strip()] or ["Elmer Quispe-Salazar"]
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
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.I)


def badge(label: str, value: str, tone: str = "blue", url: str = "") -> str:
    body = (
        f'<span class="qs-badge-label">{html.escape(label)}</span>'
        f'<span class="qs-badge-value">{html.escape(value)}</span>'
    )
    classes = f"qs-badge qs-badge-{tone}"
    if url:
        return f'<a class="{classes}" href="{html.escape(url, quote=True)}">{body}</a>'
    return f'<span class="{classes}">{body}</span>'


def first_url(pub: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = pub.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def is_open_access(pub: dict[str, Any]) -> bool:
    journal = str(pub.get("journal") or pub.get("outlet") or "").strip().casefold()
    if journal in OPEN_ACCESS_OUTLETS:
        return True
    url = str(pub.get("url") or "").strip()
    return bool(url) and urlparse(url).netloc.casefold() in OPEN_ACCESS_HOSTS


def reference(pub: dict[str, Any]) -> str:
    year = str(pub.get("year") or "n.d.")
    title = str(pub.get("title") or "Untitled work").strip()
    parts = [f"- {authors_apa(pub)} ({year}). {title}."]
    source = source_apa(pub)
    if source:
        parts.append(source)

    doi = str(pub.get("doi") or "").strip()
    url = str(pub.get("url") or "").strip()
    badges: list[str] = []
    if doi:
        clean = canonical_doi(doi)
        badges.append(badge("DOI", clean, "blue", f"https://doi.org/{clean}"))
    elif url:
        badges.append(badge("Output", "view", "blue", url))
    if is_open_access(pub):
        badges.append(badge("Open", "access", "green", url or f"https://doi.org/{canonical_doi(doi)}"))

    pdf_url = first_url(pub, "pdf_url", "pdf")
    code_url = first_url(pub, "code_url", "code")
    data_url = first_url(pub, "data_url", "data")
    if pdf_url:
        badges.append(badge("PDF", "open", "neutral", pdf_url))
    if code_url:
        badges.append(badge("Code", "repository", "neutral", code_url))
    if data_url:
        badges.append(badge("Data", "dataset", "neutral", data_url))
    if badges:
        parts.append(f'<span class="qs-badge-row qs-publication-badges">{"".join(badges)}</span>')
    return " ".join(parts)


def year_value(pub: dict[str, Any]) -> int:
    try:
        return int(pub.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def render_items(items: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(items, key=lambda item: (-year_value(item), str(item.get("title") or "").casefold()))
    years = list(dict.fromkeys(str(item.get("year") or "n.d.") for item in ordered))
    lines: list[str] = []
    if len(ordered) >= YEAR_GROUP_THRESHOLD and len(years) > 1:
        for year in years:
            lines.extend([f"### {year}", ""])
            for pub in [item for item in ordered if str(item.get("year") or "n.d.") == year]:
                lines.append(reference(pub))
            lines.append("")
    else:
        for pub in ordered:
            lines.append(reference(pub))
        lines.append("")
    return lines


def build_text(payload: dict[str, Any]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in DISPLAY_ORDER}
    for pub in payload["publications"]:
        category = str(pub.get("output_category") or "")
        if category in grouped:
            grouped[category].append(pub)

    active = [category for category in DISPLAY_ORDER if grouped[category]]
    identity = load_identity()
    lines = ["<!-- AUTO-GENERATED FROM assets/data/publications.json. DO NOT EDIT BY HAND. -->", ""]

    if active:
        lines += ['<nav class="qs-publication-nav" aria-label="Publication sections">']
        lines += [f'<a href="#{HEADING[category][1]}"><strong>{NAV_LABEL[category]}</strong></a>' for category in active]
        lines += ["</nav>", ""]

    orcid = str(payload.get("orcid") or identity.get("orcid") or "").strip()
    scholar = str(identity.get("google_scholar") or "").strip()
    if orcid:
        lines.append(f'<p class="qs-publication-profile"><em>My ORCID iD is</em> <a href="https://orcid.org/{html.escape(orcid, quote=True)}"><strong>{html.escape(orcid)}</strong></a>.</p>')
    if scholar:
        lines.append(f'<p class="qs-publication-profile"><em>My Google Scholar profile is</em> <a href="{html.escape(scholar, quote=True)}"><strong>here</strong></a>.</p>')
    if orcid or scholar:
        lines.append("")

    for category in active:
        heading, anchor = HEADING[category]
        lines += [f"## {heading} {{#{anchor}}}", ""]
        lines += render_items(grouped[category])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
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
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Rendered {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
