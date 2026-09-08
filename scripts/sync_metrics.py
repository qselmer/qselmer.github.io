#!/usr/bin/env python3
"""Synchronize public research metrics from the canonical qselmer profile."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "data" / "research-metrics.json"
SOURCE = "https://raw.githubusercontent.com/qselmer/qselmer/main/assets/data/research-metrics.json"


def validate(data: dict) -> None:
    required = {"updated_at", "orcid", "public_orcid_works", "openalex"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"research-metrics.json missing fields: {sorted(missing)}")

    openalex = data["openalex"]
    oa_required = {"available", "works_count", "cited_by_count", "h_index", "i10_index"}
    oa_missing = oa_required - openalex.keys()
    if oa_missing:
        raise ValueError(f"research-metrics.json openalex missing fields: {sorted(oa_missing)}")


def main() -> None:
    request = Request(
        SOURCE,
        headers={"User-Agent": "qselmer.github.io academic-profile-sync"},
    )
    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    validate(data)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Synchronized research metrics -> {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
