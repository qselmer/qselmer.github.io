#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
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


def citation_date_label(value: str, end_value: str = "") -> str:
    start = dt.date.fromisoformat(value)
    if not end_value:
        return f"{start.year}, {MONTHS[start.month]} {start.day}"
    end = dt.date.fromisoformat(end_value)
    if end == start:
        return f"{start.year}, {MONTHS[start.month]} {start.day}"
    if start.year == end.year and start.month == end.month:
        return f"{start.year}, {MONTHS[start.month]} {start.day}-{end.day}"
    if start.year == end.year:
        return f"{start.year}, {MONTHS[start.month]} {start.day}-{MONTHS[end.month]} {end.day}"
    return f"{MONTHS[start.month]} {start.day}, {start.year}-{MONTHS[end.month]} {end.day}, {end.year}"


def validate_presentation(entry: dict, label: str) -> None:
    for field in REQUIRED_PRESENTATION_FIELDS:
        if not entry.get(field):
            raise RuntimeError(f"Conference registry entry is missing {field}: {label}")
    if not isinstance(entry.get("authors"), list):
        raise RuntimeError(f"Conference authors must be a list: {label}")
    compact = compact_type(str(entry.get("presentation_type") or ""))
    if compact not in {"Oral", "Poster"} and str(entry.get("presentation_type") or "").strip() not in {"Conference presentation"}:
        raise RuntimeError(f"Presentation type must resolve to Oral or Poster: {label}")


def build_records() -> tuple[dict, list[dict]]:
    publications = load_json(PUBLICATIONS)
    registry = load_json(REGISTRY)
    outputs = publications.get("publications")
    records = registry.get("records")
    standalone = registry.get("standalone_records", [])
    historical = registry.get("historical_records", [])
    if not isinstance(outputs, list) or not isinstance(records, list) or not isinstance(standalone, list) or not isinstance(historical, list):
        raise RuntimeError("Invalid publications or talks registry structure")

    conference_outputs = [item for item in outputs if item.get("output_category") == "Conference outputs"]
    by_title: dict[str, dict] = {}
    for item in conference_outputs:
        key = normalize_title(item.get("title"))
        if not key or key in by_title:
            raise RuntimeError(f"Invalid or duplicate normalized conference title: {item.get('title')}")
        by_title[key] = item

    selected: list[dict] = []
    matched: set[str] = set()
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
            "end_date": entry.get("end_date", ""),
            "presentation_type": entry.get("presentation_type", ""),
            "event": entry.get("event", ""),
            "location": entry.get("location", ""),
            "authors": entry.get("authors", []),
            "presenter": entry.get("presenter", ""),
            "presenter_note": entry.get("presenter_note", ""),
            "summary": entry.get("summary", ""),
            "source_status": "",
            "legacy_path": "",
            "related_links": entry.get("related_links", []),
        })

    unmatched = set(by_title) - matched
    if unmatched:
        raise RuntimeError(f"Conference outputs are missing from talks/registry.json: {[by_title[key].get('title', '') for key in sorted(unmatched)]}")

    standalone_titles: set[str] = set()
    for entry in standalone:
        if not isinstance(entry, dict):
            raise RuntimeError("Standalone conference entries must be JSON objects")
        title = str(entry.get("display_title") or "").strip()
        if not title:
            raise RuntimeError("Standalone conference entries require display_title")
        validate_presentation(entry, title)
        normalized = normalize_title(title)
        if normalized in standalone_titles:
            raise RuntimeError(f"Duplicate standalone conference title: {title}")
        standalone_titles.add(normalized)
        selected.append({
            "record_origin": "career_master",
            "source_title": title,
            "title": title,
            "year": str(entry.get("date") or "")[:4],
            "source_type": entry.get("source_type", "Conference Abstract"),
            "source_url": entry.get("source_url", ""),
            "doi": entry.get("doi", ""),
            "source": entry.get("source", "Career master"),
            "site_path": entry.get("site_path", ""),
            "date": entry.get("date", ""),
            "end_date": entry.get("end_date", ""),
            "presentation_type": entry.get("presentation_type", ""),
            "event": entry.get("event", ""),
            "location": entry.get("location", ""),
            "authors": entry.get("authors", []),
            "presenter": entry.get("presenter", ""),
            "presenter_note": entry.get("presenter_note", ""),
            "summary": entry.get("summary", ""),
            "source_status": entry.get("source_status", ""),
            "legacy_path": "",
            "related_links": entry.get("related_links", []),
        })

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
            "end_date": entry.get("end_date", ""),
            "presentation_type": entry.get("presentation_type", ""),
            "event": entry.get("event", ""),
            "location": entry.get("location", ""),
            "authors": entry.get("authors", []),
            "presenter": entry.get("presenter", ""),
            "presenter_note": entry.get("presenter_note", ""),
            "summary": entry.get("summary", ""),
            "source_status": entry.get("source_status", ""),
            "legacy_path": entry.get("legacy_path", ""),
            "related_links": entry.get("related_links", []),
        })

    selected.sort(key=lambda item: item["date"], reverse=True)
    return {
        "schema_version": 1,
        "source": "assets/data/publications.json + talks/registry.json",
        "source_updated_at": publications.get("updated_at", ""),
        "count": len(selected),
        "canonical_count": len(records),
        "standalone_count": len(standalone),
        "historical_count": len(historical),
        "conferences": selected,
    }, selected


def author_apa(name: str) -> str:
    clean = " ".join(str(name).split())
    if not clean:
        return ""
    if "quispe" in clean.casefold() and "salazar" in clean.casefold():
        return "**Quispe-Salazar, E.**"
    parts = clean.split()
    family = parts[-1]
    initials = " ".join(token if "." in token else f"{token[0]}." for token in parts[:-1] if token)
    return f"{family}, {initials}".strip().rstrip(",")


def authors_apa(authors: list[str]) -> str:
    values = [author_apa(name) for name in authors if str(name).strip()]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} & {values[1]}"
    return f"{', '.join(values[:-1])}, & {values[-1]}"


def badge(label: str, value: str, tone: str = "neutral", url: str = "") -> str:
    body = f'<span class="qs-badge-label">{html.escape(label)}</span><span class="qs-badge-value">{html.escape(value)}</span>'
    classes = f"qs-badge qs-badge-{tone}"
    return f'<a class="{classes}" href="{html.escape(url, quote=True)}">{body}</a>' if url else f'<span class="{classes}">{body}</span>'


def compact_type(value: str) -> str:
    text = value.strip().casefold()
    if "poster" in text:
        return "Poster"
    if "oral" in text:
        return "Oral"
    return ""


def group_key(item: dict) -> str:
    return "posters" if compact_type(str(item.get("presentation_type") or "")) == "Poster" else "conference-talks"


def short_location(value: str) -> str:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) >= 2 and len(parts[-1]) == 2:
        return f"{parts[0]}, {parts[-1].upper()}"
    return value or "-"


def render_entry(item: dict) -> str:
    authors = authors_apa(item.get("authors", []))
    date_value = str(item.get("date") or "")
    end_date = str(item.get("end_date") or "")
    date = citation_date_label(date_value, end_date)
    title = str(item.get("title") or "").strip()
    event = str(item.get("event") or "").strip()
    location = str(item.get("location") or "").strip()
    site_path = str(item.get("site_path") or "").strip()
    presentation_type = compact_type(str(item.get("presentation_type") or ""))

    badges = []
    if presentation_type:
        badges.append(badge("Type", presentation_type, "neutral"))
    if location:
        badges.append(badge("Location", short_location(location), "green"))
    if site_path and site_path != "/talks/":
        badges.append(badge("Details", "page", "blue", site_path))
    badges_html = f'<span class="qs-badge-row qs-publication-badges">{"".join(badges)}</span>' if badges else ""
    return (
        f"- {authors} ({date}). {title}. *{event}*, {location}. "
        f"{badges_html}"
    ).rstrip()


def render_markdown(records: list[dict]) -> str:
    groups = [
        ("conference-talks", "Conference talks"),
        ("posters", "Posters"),
    ]
    active = [(key, heading) for key, heading in groups if any(group_key(item) == key for item in records)]
    lines = ["<!-- Generated by scripts/build_conferences.py; do not edit manually. -->", ""]
    if active:
        lines += ['<nav class="qs-publication-nav" aria-label="Talk sections">']
        for key, heading in active:
            lines.append(f'<a href="#{key}"><strong>{html.escape(heading)}</strong></a>')
        lines += ["</nav>", ""]

    for key, heading in active:
        group = [item for item in records if group_key(item) == key]
        lines += [f"## {heading} {{#{key}}}", ""]
        for item in sorted(group, key=lambda value: str(value.get("date") or ""), reverse=True):
            lines += [render_entry(item), ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload, records = build_records()
    expected_data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    expected_markdown = render_markdown(records)
    if args.check:
        stale = []
        if (DATA_TARGET.read_text(encoding="utf-8") if DATA_TARGET.exists() else "") != expected_data:
            stale.append(str(DATA_TARGET.relative_to(ROOT)))
        if (MARKDOWN_TARGET.read_text(encoding="utf-8") if MARKDOWN_TARGET.exists() else "") != expected_markdown:
            stale.append(str(MARKDOWN_TARGET.relative_to(ROOT)))
        if stale:
            raise SystemExit("Conference outputs are stale; run python scripts/build_conferences.py: " + ", ".join(stale))
        print(
            f"Conference catalogue is synchronized: {payload['canonical_count']} canonical + "
            f"{payload['standalone_count']} standalone + {payload['historical_count']} historical."
        )
        return
    DATA_TARGET.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_TARGET.parent.mkdir(parents=True, exist_ok=True)
    DATA_TARGET.write_text(expected_data, encoding="utf-8")
    MARKDOWN_TARGET.write_text(expected_markdown, encoding="utf-8")
    print(f"Wrote {DATA_TARGET.relative_to(ROOT)}")
    print(f"Wrote {MARKDOWN_TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
