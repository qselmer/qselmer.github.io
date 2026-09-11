#!/usr/bin/env python3
"""Enrich rendered pages with Phase 9 persistent-identifier and machine-interface metadata."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from site_config import ROOT

SITE = ROOT / "_site"
CONFIG = ROOT / "config" / "site.json"
METRICS = ROOT / "assets" / "data" / "research-metrics.json"
INFRASTRUCTURE = ROOT / "assets" / "data" / "scholarly-infrastructure.json"
SITE_URL = "https://qselmer.github.io"


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def insert_before_head_end(text: str, fragment: str) -> str:
    if "</head>" not in text:
        raise RuntimeError("Rendered HTML is missing </head>")
    return text.replace("</head>", fragment + "\n</head>", 1)


def add_machine_links(text: str) -> str:
    links = (
        '<link rel="alternate" type="application/json" title="Unified Scholarly Graph" '
        f'href="{SITE_URL}/assets/data/scholarly-graph.json">\n'
        '<link rel="alternate" type="application/json" title="Scholarly infrastructure metadata" '
        f'href="{SITE_URL}/assets/data/scholarly-infrastructure.json">'
    )
    if "Scholarly infrastructure metadata" in text:
        return text
    return insert_before_head_end(text, links)


def enrich_homepage(text: str) -> str:
    config = load(CONFIG)
    metrics = load(METRICS)
    infrastructure = load(INFRASTRUCTURE)
    identity = config.get("identity") or {}
    affiliation = identity.get("affiliation") or {}
    openalex = str((metrics.get("openalex") or {}).get("author_id") or "")

    pattern = re.compile(
        r'<script id="qs-structured-data" type="application/ld\+json">(?P<payload>.*?)</script>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Homepage is missing qs-structured-data JSON-LD")
    payload = json.loads(match.group("payload"))
    if payload.get("@type") != "Person":
        raise RuntimeError("Homepage structured data must be a Person before Phase 9 enrichment")

    ror = str(affiliation.get("ror") or "")
    organization = {
        "@type": "Organization",
        "@id": ror,
        "name": str(affiliation.get("name") or ""),
        "alternateName": str(affiliation.get("acronym") or ""),
        "url": str(affiliation.get("url") or ""),
        "sameAs": ror,
    }
    payload["worksFor"] = organization
    payload["affiliation"] = organization
    payload["identifier"] = [
        {"@type": "PropertyValue", "propertyID": "ORCID", "value": str(identity.get("orcid") or "")},
        {"@type": "PropertyValue", "propertyID": "ROR affiliation", "value": ror},
    ]
    if openalex:
        payload["identifier"].append({"@type": "PropertyValue", "propertyID": "OpenAlex", "value": openalex})

    same_as = list(payload.get("sameAs") or [])
    for value in (
        openalex,
        str(identity.get("web_of_science") or ""),
        str(identity.get("researchgate") or ""),
    ):
        if value and value not in same_as:
            same_as.append(value)
    payload["sameAs"] = same_as
    payload["subjectOf"] = [
        {"@type": "Dataset", "name": "Unified Scholarly Graph", "url": SITE_URL + "/assets/data/scholarly-graph.json"},
        {"@type": "Dataset", "name": "Scholarly infrastructure metadata", "url": SITE_URL + "/assets/data/scholarly-infrastructure.json"},
    ]

    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    replacement = f'<script id="qs-structured-data" type="application/ld+json">{encoded}</script>'
    text = pattern.sub(replacement, text, count=1)
    if infrastructure.get("phase") != 9:
        raise RuntimeError("Phase 9 infrastructure metadata is unavailable during postprocess")
    return add_machine_links(text)


def main() -> None:
    home = SITE / "index.html"
    if not home.is_file():
        raise RuntimeError("Rendered homepage is missing")
    home.write_text(enrich_homepage(home.read_text(encoding="utf-8")), encoding="utf-8")

    open_science = SITE / "open-science" / "index.html"
    if not open_science.is_file():
        raise RuntimeError("Rendered Open science page is missing")
    text = open_science.read_text(encoding="utf-8")
    open_science.write_text(add_machine_links(text), encoding="utf-8")
    print("Phase 9 rendered scholarly identity metadata enriched.")


if __name__ == "__main__":
    main()
