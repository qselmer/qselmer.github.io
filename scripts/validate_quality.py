#!/usr/bin/env python3
"""Phase 6 QA certification for responsive, accessible, lightweight academic pages.

This complements validate_site.py with design-contract checks that are specific to
catalogue consistency, scholarly metadata, RSS discovery, and the unified Research
project-card system.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from site_config import ROOT

SITE = ROOT / "_site"
REGISTRY = ROOT / "projects" / "registry.json"
GENERATED_PROJECTS = ROOT / "projects" / "_generated.md"
ABOUT_SELECTED = ROOT / "includes" / "about-selected.html"
CATALOGUE_CSS = ROOT / "catalogue.css"
ACCESSIBILITY_CSS = ROOT / "accessibility.css"
BLOG_REGISTRY = ROOT / "blog" / "registry.json"
RSS_SOURCE = ROOT / "blog" / "index.xml"
SITE_URL = "https://qselmer.github.io"


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def text(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing QA artifact: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="strict")


def require(haystack: str, needle: str, label: str) -> None:
    if needle not in haystack:
        raise RuntimeError(f"{label} is missing required QA marker: {needle}")


def reject(haystack: str, needle: str, label: str) -> None:
    if needle in haystack:
        raise RuntimeError(f"{label} contains forbidden QA marker: {needle}")


def project_count() -> int:
    projects = load_json(REGISTRY).get("projects")
    if not isinstance(projects, list) or not projects:
        raise RuntimeError("projects/registry.json must contain at least one project")
    return len(projects)


def validate_rss(path: Path) -> int:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"RSS feed is missing or empty: {path}")
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        raise RuntimeError(f"RSS feed is not valid XML: {path}") from exc
    if root.tag.lower() != "rss":
        raise RuntimeError("Posts feed must use an RSS root element")
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("Posts RSS feed is missing channel")
    items = channel.findall("item")
    published = [
        item for item in load_json(BLOG_REGISTRY).get("posts", [])
        if isinstance(item, dict) and item.get("status") == "published"
    ]
    if len(items) != len(published):
        raise RuntimeError(
            f"RSS item count ({len(items)}) does not match published post count ({len(published)})"
        )
    for item in items:
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        if not link.startswith(SITE_URL + "/blog/") or link != guid:
            raise RuntimeError(f"RSS item has non-canonical link/guid: {link!r} / {guid!r}")
    return len(items)


def validate_source() -> None:
    count = project_count()
    generated = text(GENERATED_PROJECTS)
    selected = text(ABOUT_SELECTED)
    css = text(CATALOGUE_CSS)
    accessibility = text(ACCESSIBILITY_CSS)

    # One project-card contract: every Research card uses the same editorial markup,
    # the Research catalogue never conditionally inserts logos, and About reuses the
    # same card component instead of maintaining a second card implementation.
    if generated.count('class="qs-project-tile"') != count:
        raise RuntimeError("Generated Research project-card count does not match registry")
    if generated.count('class="qs-project-type"') != count:
        raise RuntimeError("Every Research project card must include the PROJECT type marker")
    reject(generated, "qs-project-visual", "projects/_generated.md")
    reject(generated, "qs-project-logo", "projects/_generated.md")
    reject(generated, "/images/projects/", "projects/_generated.md")
    require(selected, 'class="qs-project-tile"', "includes/about-selected.html")
    require(selected, 'class="qs-project-type"', "includes/about-selected.html")
    reject(selected, "qs-selected-item", "includes/about-selected.html")
    reject(selected, "qs-selected-type", "includes/about-selected.html")

    # Responsive and visual contract for project cards and thematic navigation.
    # Research projects are full-width rows across themes; About can use its own
    # compact grid while reusing exactly the same card component.
    for marker in (
        "border-top: 3px solid #0b1320",
        "grid-template-columns: 1fr !important",
        ".qs-project-type",
        "@media (max-width: 900px)",
        "@media (max-width: 760px)",
        "grid-template-columns: repeat(3, minmax(0, 1fr))",
    ):
        require(css, marker, "catalogue.css")

    # Accessibility must remain explicit rather than relying on browser defaults.
    for marker in (":focus-visible", "prefers-reduced-motion", ".qs-skip-link"):
        require(accessibility, marker, "accessibility.css")

    rss_items = validate_rss(RSS_SOURCE)
    print(
        f"Phase 6 source QA PASS: {count} projects use one card system; "
        f"About reuses the Research cards; responsive/focus/reduced-motion contracts present; "
        f"RSS has {rss_items} item(s)"
    )


def rendered_file(route: str) -> Path:
    if route == "/":
        return SITE / "index.html"
    return SITE / route.strip("/") / "index.html"


def require_jsonld(route: str, schema_type: str) -> None:
    page = rendered_file(route)
    body = text(page)
    require(body, 'id="qs-structured-data"', route)
    if f'"@type":"{schema_type}"' not in body and f'"@type": "{schema_type}"' not in body:
        raise RuntimeError(f"{route} is missing JSON-LD type {schema_type}")


def require_social_image(route: str) -> None:
    body = text(rendered_file(route))
    if not re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']https://qselmer\.github\.io/', body, re.I):
        raise RuntimeError(f"{route} is missing a canonical og:image")
    if not re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']https://qselmer\.github\.io/', body, re.I):
        raise RuntimeError(f"{route} is missing a canonical twitter:image")


def validate_rendered() -> None:
    if not SITE.is_dir():
        raise RuntimeError("_site does not exist; render Quarto before Phase 6 QA")

    count = project_count()
    research = text(rendered_file("/projects/"))
    about = text(rendered_file("/"))
    if research.count('class="qs-project-tile"') != count:
        raise RuntimeError("Rendered Research project-card count does not match registry")
    if research.count('class="qs-project-type"') != count:
        raise RuntimeError("Rendered Research cards do not all use the unified PROJECT marker")
    reject(research, "qs-project-visual", "rendered Research")
    reject(research, "qs-project-logo", "rendered Research")
    reject(research, "/images/projects/", "rendered Research")
    require(about, 'class="qs-project-tile"', "rendered About")
    require(about, 'class="qs-project-type"', "rendered About")
    reject(about, "qs-selected-item", "rendered About")
    reject(about, "qs-selected-type", "rendered About")

    # Route-specific scholarly structured data.
    require_jsonld("/", "Person")
    require_jsonld("/publications/", "ScholarlyArticle")
    require_jsonld("/software/oceancube/", "SoftwareSourceCode")
    require_jsonld("/teaching/git-github-training/", "Course")
    require_jsonld("/blog/statistical-distributions-fisheries-marine-ecology/", "BlogPosting")

    # Social previews for content types that benefit from link sharing.
    for route in ("/publications/", "/talks/", "/software/", "/blog/"):
        require_social_image(route)

    rss_items = validate_rss(SITE / "blog" / "index.xml")
    blog_index = text(rendered_file("/blog/"))
    require(blog_index, 'type="application/rss+xml"', "rendered Posts")

    print(
        f"Phase 6 rendered QA PASS: {count} uniform project cards, About card reuse, "
        f"scholarly JSON-LD, social previews, responsive catalogue contract, and {rss_items} RSS item(s)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()
    if args.mode in {"source", "all"}:
        validate_source()
    if args.mode in {"rendered", "all"}:
        validate_rendered()


if __name__ == "__main__":
    main()
