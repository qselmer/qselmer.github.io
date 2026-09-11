#!/usr/bin/env python3
"""Validate Phase 10 reproducibility certification source and rendered outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_reproducibility_certification import build_payload
from site_config import ROOT

TARGET = ROOT / "assets" / "data" / "reproducibility-certification.json"
FRAGMENT = ROOT / "reproducibility" / "_generated.md"
PAGE = ROOT / "reproducibility" / "index.qmd"
SITE = ROOT / "_site"


def validate_payload(payload: dict) -> None:
    if payload.get("phase") != 10 or payload.get("schema_version") != 1:
        raise RuntimeError("Invalid Phase 10 certification schema")
    if payload.get("external_accreditation") is not False:
        raise RuntimeError("Phase 10 must not claim external accreditation")
    if payload.get("scientific_quality_claim") is not False:
        raise RuntimeError("Phase 10 must not claim scientific quality certification")

    records = payload.get("records") or []
    scope = payload.get("public_repository_scope") or []
    if len(records) != len(scope):
        raise RuntimeError("Certification records must match the public repository scope exactly")
    if {item.get("repository") for item in records} != set(scope):
        raise RuntimeError("Certification scope mismatch with Phase 7 public allowlist")

    ids = [str(item.get("certificate_id") or "") for item in records]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("Certification IDs must be present and unique")

    threshold = int(payload.get("certified_from_level", 2))
    for item in records:
        level = int(item.get("level", -1))
        status = str(item.get("status") or "")
        expected = "certified" if level >= threshold else "not-certified"
        if status != expected:
            raise RuntimeError(f"Over/under certification detected for {item.get('repository')}")
        if level < 0 or level > 5:
            raise RuntimeError(f"Invalid reproducibility level for {item.get('repository')}")


def validate_source() -> None:
    expected = build_payload()
    validate_payload(expected)
    if not TARGET.exists() or not FRAGMENT.exists() or not PAGE.exists():
        raise RuntimeError("Phase 10 source outputs/page are missing")
    current = json.loads(TARGET.read_text(encoding="utf-8"))
    if current != expected:
        raise RuntimeError("Phase 10 machine-readable certification is stale")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    if "internal technical self-certification" not in fragment:
        raise RuntimeError("Phase 10 disclaimer is missing from generated page fragment")
    print("Phase 10 source certification PASS")


def validate_rendered() -> None:
    page = SITE / "reproducibility" / "index.html"
    machine = SITE / "assets" / "data" / "reproducibility-certification.json"
    if not page.is_file():
        raise RuntimeError("Rendered /reproducibility/ page is missing")
    if not machine.is_file():
        raise RuntimeError("Rendered Phase 10 machine-readable output is missing")
    html = page.read_text(encoding="utf-8")
    if "Reproducibility certification" not in html:
        raise RuntimeError("Rendered Phase 10 page title is missing")
    if "internal technical self-certification" not in html:
        raise RuntimeError("Rendered Phase 10 disclaimer is missing")
    payload = json.loads(machine.read_text(encoding="utf-8"))
    validate_payload(payload)
    print("Phase 10 rendered certification PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered"))
    args = parser.parse_args()
    if args.mode == "source":
        validate_source()
    else:
        validate_rendered()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
