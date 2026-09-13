#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

from site_config import ROOT, profile_source

TARGET = ROOT / "assets" / "data" / "publications.json"

OUTPUT_CATEGORIES = [
    "Journal articles",
    "Preprints & working papers",
    "Books & chapters",
    "Theses",
    "Conference outputs",
    "Reports & technical outputs",
    "Data & software",
    "Other research outputs",
]


def validate(payload: dict[str, Any]) -> None:
    publications = payload.get("publications")
    if not isinstance(publications, list):
        raise RuntimeError("Invalid publication payload: publications must be a list")
    declared = payload.get("count")
    if declared is not None and declared != len(publications):
        raise RuntimeError("Invalid publication payload: count does not match publications list")
    for index, publication in enumerate(publications, start=1):
        if not isinstance(publication, dict):
            raise RuntimeError(f"Invalid publication payload: item {index} is not an object")
        for field in ("title", "year", "output_category"):
            if not str(publication.get(field) or "").strip():
                raise RuntimeError(f"Invalid publication payload: item {index} is missing {field}")


def publication_key(item: dict[str, Any]) -> tuple[str, str]:
    title = re.sub(r"\s+", " ", str(item.get("title") or "").strip()).casefold()
    year = str(item.get("year") or "").strip()
    return title, year


def curated_records() -> list[dict[str, Any]]:
    """Keep explicitly curated website outputs across canonical-profile refreshes.

    The GitHub profile remains the canonical automated source for ORCID/Crossref
    publications. Website-only records marked ``curated: true`` are reviewed
    against the private career master before publication and are deliberately
    preserved when the automated source is refreshed.
    """
    if not TARGET.exists():
        return []
    try:
        current = json.loads(TARGET.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    records = current.get("publications") or []
    if not isinstance(records, list):
        return []
    return [item for item in records if isinstance(item, dict) and item.get("curated") is True]


def merge_curated(payload: dict[str, Any], curated: list[dict[str, Any]]) -> dict[str, Any]:
    publications = list(payload.get("publications") or [])
    seen = {publication_key(item) for item in publications if isinstance(item, dict)}
    for item in curated:
        key = publication_key(item)
        if key not in seen:
            publications.append(item)
            seen.add(key)

    payload["publications"] = publications
    payload["count"] = len(publications)

    counts = {category: 0 for category in OUTPUT_CATEGORIES}
    for item in publications:
        category = str(item.get("output_category") or "Other research outputs")
        counts[category] = counts.get(category, 0) + 1
    payload["output_counts"] = counts

    years: list[int] = []
    for item in publications:
        try:
            year = int(item.get("year") or 0)
        except (TypeError, ValueError):
            continue
        if 1000 <= year <= 9999:
            years.append(year)
    payload["publishing_since"] = str(min(years)) if years else "-"
    payload["website_curated_count"] = sum(1 for item in publications if item.get("curated") is True)
    return payload


def main() -> None:
    source = profile_source("publications")
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "qselmer.github.io academic-profile-sync/3.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    validate(payload)
    payload = merge_curated(payload, curated_records())
    validate(payload)

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if current == rendered:
        print(f"Publication catalogue already synchronized ({len(payload['publications'])} records)")
    else:
        TARGET.write_text(rendered, encoding="utf-8")
        print(
            f"Synchronized {len(payload['publications'])} publication records "
            f"({payload.get('website_curated_count', 0)} website-curated)"
        )


if __name__ == "__main__":
    main()
