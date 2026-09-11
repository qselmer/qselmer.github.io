#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "registry.json"
TARGET = ROOT / "data" / "_generated.md"

REQUIRED_FIELDS = {
    "id", "name", "provider", "category", "access", "access_group",
    "coverage", "formats", "description", "use_case", "terms", "url",
    "recommended",
}
ACCESS_GROUPS = {"open", "registered", "licensed_or_restricted"}

PROVIDER_SHORT = {
    "Global Fishing Watch": "GFW",
    "International Council for the Exploration of the Sea": "ICES",
    "RAM Legacy Stock Assessment Database": "RAM Legacy",
    "University of British Columbia": "UBC",
    "IOC-UNESCO / OBIS": "OBIS",
    "Global Biodiversity Information Facility": "GBIF",
    "Flanders Marine Institute and collaborators": "VLIZ",
    "Flanders Marine Institute": "VLIZ",
    "European Union / Mercator Ocean International": "Copernicus",
    "NOAA CoastWatch / OceanWatch / PolarWatch": "NOAA CW",
    "International Argo Program": "Argo",
    "ECMWF / Copernicus Climate Change Service": "ECMWF/C3S",
    "Met Office Hadley Centre": "Met Office",
    "NOAA Physical Sciences Laboratory": "NOAA PSL",
    "GEBCO / Seabed 2030": "GEBCO",
    "IMARPE / PRODUCE Open Data": "IMARPE",
    "Ministerio de la Producción, Peru": "PRODUCE",
    "FONDEPES / PRODUCE": "FONDEPES",
    "Kpler / MarineTraffic": "MarineTraffic",
    "Planet Labs": "Planet",
    "Spire Global": "Spire",
}

ACCESS_SHORT = {
    "open": "Open",
    "registered": "Register",
    "licensed_or_restricted": "Licensed",
}


def load_registry() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("data/registry.json must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported data registry schema_version")
    categories = payload.get("categories")
    resources = payload.get("resources")
    if not isinstance(categories, list) or not categories:
        raise RuntimeError("data registry categories must be a non-empty list")
    if not isinstance(resources, list) or not resources:
        raise RuntimeError("data registry resources must be a non-empty list")
    return payload


def validate(payload: dict) -> None:
    categories = payload["categories"]
    ids: set[str] = set()
    for item in payload["resources"]:
        if not isinstance(item, dict):
            raise RuntimeError("Every data resource must be a JSON object")
        missing = sorted(REQUIRED_FIELDS - set(item))
        if missing:
            raise RuntimeError(f"Data resource is missing required fields: {missing}")
        resource_id = str(item["id"]).strip()
        if not resource_id or resource_id in ids:
            raise RuntimeError(f"Invalid or duplicate data resource id: {resource_id}")
        ids.add(resource_id)
        category = str(item["category"]).strip()
        if category not in categories:
            raise RuntimeError(f"Unknown data category for {resource_id}: {category}")
        access_group = str(item["access_group"]).strip()
        if access_group not in ACCESS_GROUPS:
            raise RuntimeError(f"Invalid access_group for {resource_id}: {access_group}")
        parsed = urlparse(str(item["url"]).strip())
        if parsed.scheme != "https" or not parsed.netloc:
            raise RuntimeError(f"Authoritative URL must be absolute HTTPS: {resource_id}")
        if not isinstance(item["recommended"], bool):
            raise RuntimeError(f"recommended must be boolean: {resource_id}")


def anchor(value: object) -> str:
    text = str(value or "").strip().casefold()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def badge(label: str, value: str, tone: str = "neutral", detail: str = "") -> str:
    title = ""
    if detail and detail != value:
        title = f' title="{html.escape(detail, quote=True)}"'
    body = (
        f'<span class="qs-badge-label">{html.escape(label)}</span>'
        f'<span class="qs-badge-value">{html.escape(value)}</span>'
    )
    return f'<span class="qs-badge qs-badge-{tone}"{title}>{body}</span>'


def compact_provider(value: str) -> str:
    return PROVIDER_SHORT.get(value, value if len(value) <= 18 else value.split(" / ")[0])


def compact_coverage(value: str) -> str:
    lower = value.casefold()
    if "peru" in lower or "peruvian" in lower:
        return "Peru"
    if "ices" in lower:
        return "ICES"
    if "global" in lower:
        return "Global"
    if "regional" in lower:
        return "Regional"
    return value if len(value) <= 18 else "Regional"


def compact_format(value: str) -> str:
    lower = value.casefold()
    ordered = (
        ("fishstatj", "FishStatJ"),
        ("geoparquet", "GeoParquet"),
        ("netcdf", "NetCDF"),
        ("erddap", "ERDDAP"),
        ("rest api", "API"),
        ("graphql", "API"),
        ("api", "API"),
        ("geotiff", "GeoTIFF"),
        ("geopackage", "GIS"),
        ("shapefile", "GIS"),
        ("csv", "CSV"),
        ("excel", "Excel"),
        ("xlsx", "Excel"),
        ("text", "Text"),
        ("ais", "AIS"),
    )
    for token, label in ordered:
        if token in lower:
            return label
    return "Data"


def render_resource(item: dict) -> str:
    name = str(item["name"]).strip()
    url = str(item["url"]).strip()
    provider = str(item["provider"]).strip()
    access = str(item["access"]).strip()
    access_group = str(item["access_group"]).strip()
    coverage = str(item["coverage"]).strip()
    formats = str(item["formats"]).strip()
    description = str(item["description"]).strip()
    use_case = str(item["use_case"]).strip()

    badges = [
        badge("Provider", compact_provider(provider), "neutral", provider),
        badge("Access", ACCESS_SHORT[access_group], "green", access),
        badge("Coverage", compact_coverage(coverage), "blue", coverage),
        badge("Format", compact_format(formats), "amber", formats),
    ]
    return (
        f'- <strong><a href="{html.escape(url, quote=True)}">{html.escape(name)}</a></strong>. '
        f'{html.escape(description)} <span class="qs-data-use"><strong>Useful for:</strong> {html.escape(use_case)}</span> '
        f'<span class="qs-badge-row qs-publication-badges qs-data-badges">{"".join(badges)}</span>'
    )


def render(payload: dict) -> str:
    validate(payload)
    resources = payload["resources"]
    categories = payload["categories"]
    lines = ["<!-- Generated by scripts/build_data_resources.py; do not edit manually. -->", ""]
    for category in categories:
        group = [item for item in resources if item["category"] == category]
        if not group:
            continue
        lines += [f"## {category} {{#{anchor(category)}}}", ""]
        for item in sorted(group, key=lambda value: (not bool(value.get("recommended")), str(value.get("name") or "").casefold())):
            lines += [render_resource(item), ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = load_registry()
    expected = render(payload)
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != expected:
            raise SystemExit("data/_generated.md is stale; run python scripts/build_data_resources.py")
        print(f"Data catalogue synchronized: {len(payload['resources'])} external sources.")
        return
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
