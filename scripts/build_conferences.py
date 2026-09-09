#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
REGISTRY = ROOT / "talks" / "registry.json"
DATA_TARGET = ROOT / "assets" / "data" / "conferences.json"
MARKDOWN_TARGET = ROOT / "talks" / "_generated.md"

MONTHS = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
REQUIRED_PRESENTATION_FIELDS = ("site_path", "date", "presentation_type", "event", "location", "authors")


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def normalize_title(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"-{2,}", "-", text)
    return " ".join(text.casefold().split())


def date_label(value: str) -> str:
    date = dt.date.fromisoformat(value)
    return f"{date.day} {MONTHS[date.month]} {date.year}"


def validate_presentation(entry: dict, label: str) -> None:
    for field in REQUIRED_PRESENTATION_FIELDS:
        if not entry.get(field):
            raise RuntimeError(f"Conference registry entry is missing {field}: {label}")
    if not isinstance(entry.get("authors"), list):
        raise RuntimeError(f"Conference authors must be a list: {label}")


def build_records() -> tuple[dict, list[dict]]:
    publications = load_json(PUBLICATIONS)
    registry = load_json(REGISTRY)
    outputs = publications.get("publications")
    records = registry.get("records")
    historical = registry.get("historical_records", [])
    if not isinstance(outputs, list):
        raise RuntimeError("assets/data/publications.json must contain publications")
    if not isinstance(records, list):
        raise RuntimeError("talks/registry.json must contain records")
    if not isinstance(historical, list):
        raise RuntimeError("talks/registry.json historical_records must be a list")

    conference_outputs = [item for item in outputs if item.get("output_category") == "Conference outputs"]
    by_title = {}
    for item in conference_outputs:
        key = normalize_title(item.get("title"))
        if not key:
            raise RuntimeError("Conference output is missing title")
        if key in by_title:
            raise RuntimeError(f"Duplicate normalized conference title: {item.get('title')}")
        by_title[key] = item

    selected: list[dict] = []
    matched = set()
    for entry in records:
        source_title = str(entry.get("source_title") or "").strip()
        if not source_title:
            raise RuntimeError("Conference registry entries require source_title")
        key = normalize_title(source_title)
        publication = by_title.get(key)
        if publication is None:
            raise RuntimeError(f"Conference output not found in publication catalogue: {source_title}")
        if key in matched:
            raise RuntimeError(f"Conference output appears more than once in registry: {source_title}")
        matched.add(key)
        validate_presentation(entry, source_title)
        selected.append({
            "record_origin": "canonical_profile",
            "source_title": publication.get("title", ""),
            "title": entry.get("display_title") or publication.get("title", ""),
            "year": publication.get("year", ""),
            "source_type": publication.get("type", ""),
            "source_url": publication.get("url", ""),
            "doi": publication.get("doi", ""),
            "source": publication.get("source", ""),
            "site_path": entry.get("site_path", ""),
            "date": entry.get("date", ""),
            "presentation_type": entry.get("presentation_type", ""),
            "event": entry.get("event", ""),
            "location": entry.get("location", ""),
            "authors": entry.get("authors", []),
            "presenter": entry.get("presenter", ""),
            "summary": entry.get("summary", ""),
            "source_status": "",
            "legacy_path": "",
            "related_links": entry.get("related_links", []),
        })

    unmatched = set(by_title) - matched
    if unmatched:
        titles = [by_title[key].get("title", "") for key in sorted(unmatched)]
        raise RuntimeError(f"Conference outputs are missing from talks/registry.json: {titles}")

    historical_paths: set[str] = set()
    for entry in historical:
        if not isinstance(entry, dict):
            raise RuntimeError("Historical conference entries must be JSON objects")
        title = str(entry.get("display_title") or "").strip()
        if not title:
            raise RuntimeError("Historical conference entries require display_title")
        validate_presentation(entry, title)
        site_path = str(entry["site_path"]).strip()
        if site_path in historical_paths:
            raise RuntimeError(f"Duplicate historical conference site_path: {site_path}")
        historical_paths.add(site_path)
        if not entry.get("source_status"):
            raise RuntimeError(f"Historical conference entry requires source_status: {title}")
        selected.append({
            "record_origin": "legacy_site",
            "source_title": "",
            "title": title,
            "year": str(entry["date"])[:4],
            "source_type": "Historical conference contribution",
            "source_url": "",
            "doi": "",
            "source": "Legacy qselmer.github.io record",
            "site_path": site_path,
            "date": entry.get("date", ""),
            "presentation_type": entry.get("presentation_type", ""),
            "event": entry.get("event", ""),
            "location": entry.get("location", ""),
            "authors": entry.get("authors", []),
            "presenter": entry.get("presenter", ""),
            "summary": entry.get("summary", ""),
            "source_status": entry.get("source_status", ""),
            "legacy_path": entry.get("legacy_path", ""),
            "related_links": entry.get("related_links", []),
        })

    selected.sort(key=lambda item: item["date"], reverse=True)
    payload = {
        "schema_version": 1,
        "source": "assets/data/publications.json + talks/registry.json historical records",
        "source_updated_at": publications.get("updated_at", ""),
        "count": len(selected),
        "canonical_count": len(records),
        "historical_count": len(historical),
        "conferences": selected,
    }
    return payload, selected


def render_markdown(records: list[dict]) -> str:
    lines = ["<!-- Generated by scripts/build_conferences.py; do not edit manually. -->", ""]
    years = sorted({str(item.get("year") or "") for item in records if item.get("year")}, reverse=True)
    for year in years:
        lines += [f"## {year}", ""]
        group = [item for item in records if str(item.get("year") or "") == year]
        for item in group:
            lines += [
                f"### {item['title']}", "",
                f"**{item['presentation_type']} · {date_label(item['date'])} · {item['location']}**", "",
                f"*{item['event']}*", "",
            ]
            if item.get("summary"):
                lines += [item["summary"], ""]
            lines += [f"**Authors:** {', '.join(item['authors'])}.", ""]
            if item.get("presenter"):
                lines += [f"**Presenter:** {item['presenter']}.", ""]
            if item.get("source_status"):
                lines += [f"*Source status:* {item['source_status']}", ""]
            links = []
            if item.get("site_path"):
                links.append(f"[Details]({item['site_path']})")
            if item.get("source_url"):
                links.append(f"[Public material]({item['source_url']})")
            if item.get("doi"):
                doi_url = f"https://doi.org/{item['doi']}"
                links.append(f"[{doi_url}]({doi_url})")
            if links:
                lines += [" · ".join(links), ""]
    return "\n".join(lines).rstrip() + "\n"


def render_data(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload, records = build_records()
    expected_data = render_data(payload)
    expected_markdown = render_markdown(records)
    if args.check:
        current_data = DATA_TARGET.read_text(encoding="utf-8") if DATA_TARGET.exists() else ""
        current_markdown = MARKDOWN_TARGET.read_text(encoding="utf-8") if MARKDOWN_TARGET.exists() else ""
        stale = []
        if current_data != expected_data:
            stale.append(str(DATA_TARGET.relative_to(ROOT)))
        if current_markdown != expected_markdown:
            stale.append(str(MARKDOWN_TARGET.relative_to(ROOT)))
        if stale:
            raise SystemExit("Conference outputs are stale; run python scripts/build_conferences.py: " + ", ".join(stale))
        print(f"Conference catalogue is synchronized: {payload['canonical_count']} canonical + {payload['historical_count']} historical.")
        return
    DATA_TARGET.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_TARGET.parent.mkdir(parents=True, exist_ok=True)
    DATA_TARGET.write_text(expected_data, encoding="utf-8")
    MARKDOWN_TARGET.write_text(expected_markdown, encoding="utf-8")
    print(f"Wrote {DATA_TARGET.relative_to(ROOT)}")
    print(f"Wrote {MARKDOWN_TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
