#!/usr/bin/env python3
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/qselmer/qselmer/main/assets/data/publications.json"
TARGET = Path(__file__).resolve().parents[1] / "_data" / "publications.json"

request = urllib.request.Request(SOURCE, headers={"User-Agent": "qselmer-website-publication-sync/1.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    payload = json.load(response)

if not isinstance(payload.get("publications"), list):
    raise RuntimeError("Invalid publication payload")

TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Synchronized {len(payload['publications'])} publications")
