#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://raw.githubusercontent.com/qselmer/qselmer/main/assets/data/publications.json"
TARGET = ROOT / "assets" / "data" / "publications.json"


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


request = urllib.request.Request(
    SOURCE,
    headers={"User-Agent": "qselmer-website-publication-sync/2.0"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    payload = json.load(response)

validate(payload)
rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
TARGET.parent.mkdir(parents=True, exist_ok=True)
current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
if current == rendered:
    print(f"Publication catalogue already synchronized ({len(payload['publications'])} records)")
else:
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"Synchronized {len(payload['publications'])} publication records")
