#!/usr/bin/env python3
"""Validate the Honors & Awards catalogue and rendered page."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from site_config import ROOT

REGISTRY = ROOT / "honors" / "registry.json"
DATA = ROOT / "assets" / "data" / "honors.json"
FRAGMENT = ROOT / "honors" / "_generated.md"
PAGE = ROOT / "honors" / "index.qmd"
SITE = ROOT / "_site"

REQUIRED_IDS = {
    "honor-2024-sibecorp-best-doctoral-work-oral-presentation",
    "honor-2023-pucv-fisheries-resource-assessment-scholarship",
}


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def validate_source() -> None:
    registry = load(REGISTRY)
    data = load(DATA)
    if registry.get("schema_version") != 1 or data.get("schema_version") != 1:
        raise RuntimeError("Honors registry and mirror must use schema_version 1")
    records = registry.get("honors")
    mirrored = data.get("honors")
    if not isinstance(records, list) or not isinstance(mirrored, list):
        raise RuntimeError("Honors records must be lists")
    ids = {str(item.get("id") or "") for item in records if isinstance(item, dict)}
    if not REQUIRED_IDS.issubset(ids):
        raise RuntimeError("Required documented honors are missing from the canonical registry")
    if data.get("count") != len(mirrored) or len(mirrored) != len(records):
        raise RuntimeError("Honors mirror count does not match canonical registry")
    for item in records:
        if item.get("visibility") != "public":
            raise RuntimeError(f"Honors public catalogue contains non-public item: {item.get('id')}")
        evidence_status = str(item.get("evidence_status") or "").strip()
        if not evidence_status.casefold().startswith("verified"):
            raise RuntimeError(f"Honor lacks verified documentary evidence: {item.get('id')}")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    for marker in (
        "Awards & distinctions",
        "Scholarships & fellowships",
        "Best Doctoral Work",
        "Fisheries Resource Assessment Diploma",
        "qs-academic-output-badges",
        ">Type<",
        ">Scope<",
        "qs-badge-green",
    ):
        if marker not in fragment:
            raise RuntimeError(f"Honors fragment is missing {marker!r}")
    if '>Status<' in fragment:
        raise RuntimeError("Honors fragment must expose only Type and Scope badges")
    if "{{< include _generated.md >}}" not in PAGE.read_text(encoding="utf-8"):
        raise RuntimeError("Honors page must include its generated fragment")


def validate_rendered() -> None:
    page = SITE / "honors" / "index.html"
    data = SITE / "assets" / "data" / "honors.json"
    if not page.is_file():
        raise RuntimeError("Rendered Honors & Awards page is missing")
    if not data.is_file() or data.stat().st_size == 0:
        raise RuntimeError("Rendered honors.json is missing")
    body = page.read_text(encoding="utf-8", errors="strict")
    for marker in (
        "Honors &amp; Awards",
        "Best Doctoral Work",
        "Fisheries Resource Assessment Diploma",
        "qs-honor-output-item",
        ">Type<",
        ">Scope<",
        "qs-badge-green",
    ):
        if marker not in body:
            raise RuntimeError(f"Rendered Honors page is missing {marker!r}")
    if '>Status<' in body:
        raise RuntimeError("Rendered Honors page must expose only Type and Scope badges")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()
    if args.mode in {"source", "all"}:
        validate_source()
        print("Honors source QA PASS: canonical registry, generated catalogue, and evidence verification are synchronized.")
    if args.mode in {"rendered", "all"}:
        validate_rendered()
        print("Honors rendered QA PASS: only Type and Scope badges are displayed, with Scope highlighted in green.")


if __name__ == "__main__":
    main()
