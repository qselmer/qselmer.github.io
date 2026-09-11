#!/usr/bin/env python3
"""Build the public honors catalogue and machine-readable mirror."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from site_config import ROOT

SOURCE = ROOT / "honors" / "registry.json"
TARGET_JSON = ROOT / "assets" / "data" / "honors.json"
TARGET_MD = ROOT / "honors" / "_generated.md"


def load_registry() -> dict[str, Any]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RuntimeError("honors/registry.json must be a schema_version 1 object")
    categories = payload.get("categories")
    honors = payload.get("honors")
    if not isinstance(categories, list) or not isinstance(honors, list):
        raise RuntimeError("Honors registry must contain categories and honors lists")
    category_ids = {str(item.get("id") or "").strip() for item in categories if isinstance(item, dict)}
    if not category_ids or "" in category_ids or len(category_ids) != len(categories):
        raise RuntimeError("Honor category ids must be present and unique")
    ids: set[str] = set()
    for index, item in enumerate(honors, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"Honor {index} is not an object")
        for field in ("id", "year", "category", "type", "title", "organization", "scope", "evidence_status"):
            if not str(item.get(field) or "").strip():
                raise RuntimeError(f"Honor {index} is missing required field: {field}")
        item_id = str(item["id"])
        if item_id in ids:
            raise RuntimeError(f"Duplicate honor id: {item_id}")
        ids.add(item_id)
        if str(item["category"]) not in category_ids:
            raise RuntimeError(f"Honor {item_id} references unknown category {item['category']}")
        if item.get("visibility") != "public":
            raise RuntimeError(f"Public honors catalogue cannot contain non-public item: {item_id}")
    return payload


def badge(label: str, value: str, tone: str = "neutral") -> str:
    body = (
        f'<span class="qs-badge-label">{html.escape(label)}</span>'
        f'<span class="qs-badge-value">{html.escape(value)}</span>'
    )
    return f'<span class="qs-badge qs-badge-{tone}">{body}</span>'


def render_item(item: dict[str, Any]) -> str:
    year = html.escape(str(item["year"]))
    title = html.escape(str(item["title"]))
    organization = html.escape(str(item["organization"]))
    location = html.escape(str(item.get("location") or ""))
    summary = html.escape(str(item.get("summary") or ""))
    work_title = html.escape(str(item.get("work_title") or ""))
    evidence_status = html.escape(str(item.get("evidence_status") or ""))

    reference = f'<strong>{year}.</strong> <span class="qs-academic-output-title">{title}</span>. {organization}.'
    if location:
        reference += f" {location}."
    details: list[str] = []
    if summary:
        details.append(summary)
    if work_title:
        details.append(f'<em>Recognized work:</em> “{work_title}”.')
    if evidence_status:
        details.append(f'<span class="qs-honor-evidence"><em>Evidence:</em> {evidence_status}.</span>')
    badges = "".join([
        badge("Type", str(item["type"]), "blue"),
        badge("Scope", str(item["scope"]), "neutral"),
    ])
    return (
        '<li class="qs-academic-output-item qs-honor-output-item">'
        f'<div class="qs-academic-output-reference">{reference}</div>'
        f'<div class="qs-academic-output-meta">{" ".join(details)}</div>'
        f'<div class="qs-academic-output-badges">{badges}</div>'
        '</li>'
    )


def build_markdown(payload: dict[str, Any]) -> str:
    honors = [item for item in payload["honors"] if item.get("visibility") == "public"]
    honors.sort(key=lambda item: (-int(item.get("year") or 0), str(item.get("title") or "").casefold()))
    grouped = {str(category["id"]): [] for category in payload["categories"]}
    for item in honors:
        grouped[str(item["category"])].append(item)

    active = [category for category in payload["categories"] if grouped[str(category["id"])]]
    lines = ["<!-- AUTO-GENERATED FROM honors/registry.json. DO NOT EDIT BY HAND. -->", ""]
    if active:
        lines += ['<nav class="qs-publication-nav" aria-label="Honors sections">']
        for category in active:
            cid = html.escape(str(category["id"]), quote=True)
            label = html.escape(str(category.get("nav_label") or category.get("heading") or cid))
            lines.append(f'<a href="#{cid}"><strong>{label}</strong></a>')
        lines += ["</nav>", ""]

    for category in active:
        cid = str(category["id"])
        lines += [f'## {category["heading"]} {{#{cid}}}', "", '<ul class="qs-academic-output-list qs-honors-output-list">']
        lines.extend(render_item(item) for item in grouped[cid])
        lines += ["</ul>", ""]
    return "\n".join(lines).rstrip() + "\n"


def build_json(payload: dict[str, Any]) -> str:
    public_items = [item for item in payload["honors"] if item.get("visibility") == "public"]
    result = {
        "schema_version": 1,
        "count": len(public_items),
        "categories": payload["categories"],
        "honors": public_items,
        "source": "honors/registry.json",
    }
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def write_or_check(path: Path, expected: str, check: bool) -> None:
    if check:
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual != expected:
            raise RuntimeError(f"Generated artifact is stale: {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = load_registry()
    write_or_check(TARGET_JSON, build_json(payload), args.check)
    write_or_check(TARGET_MD, build_markdown(payload), args.check)
    print(f"Honors catalogue {'verified' if args.check else 'built'}: {len(payload['honors'])} records")


if __name__ == "__main__":
    main()
