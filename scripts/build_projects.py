#!/usr/bin/env python3
"""Render the thematic project catalogue from registry and research graph."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from site_config import ROOT

REGISTRY = ROOT / "projects" / "registry.json"
GRAPH = ROOT / "assets" / "data" / "research-graph.json"
TARGET = ROOT / "projects" / "_generated.md"
LOGO_ROOT = ROOT / "images" / "projects"
CLASS_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")
LOGO_NAMES = ("logo.svg", "logo.png")


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def load_registry() -> dict:
    payload = load_json(REGISTRY)
    if payload.get("schema_version") != 1:
        raise RuntimeError("projects/registry.json must use schema_version 1")
    sections = payload.get("sections")
    projects = payload.get("projects")
    if not isinstance(sections, list) or not sections:
        raise RuntimeError("projects/registry.json must contain sections")
    if not isinstance(projects, list):
        raise RuntimeError("projects/registry.json must contain a projects list")
    return payload


def load_graph() -> dict[str, dict]:
    payload = load_json(GRAPH)
    if payload.get("schema_version") != 1:
        raise RuntimeError("assets/data/research-graph.json must use schema_version 1")
    themes = payload.get("themes")
    if not isinstance(themes, list):
        raise RuntimeError("Research graph must contain themes")
    return {str(theme.get("id") or "").strip(): theme for theme in themes}


def clean_class(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text or not CLASS_TOKEN.fullmatch(text):
        raise RuntimeError(f"Invalid CSS class token for {label}: {text!r}")
    return text


def logo_for(slug: str) -> str | None:
    directory = LOGO_ROOT / slug
    for name in LOGO_NAMES:
        if (directory / name).is_file():
            return name
    return None


def render_card(project: dict) -> list[str]:
    slug = clean_class(project.get("slug"), "project slug")
    tone = clean_class(project.get("tone"), f"{slug} tone")
    extra = project.get("extra_classes") or []
    if not isinstance(extra, list):
        raise RuntimeError(f"extra_classes must be a list for {slug}")
    extra_classes = [clean_class(item, f"{slug} extra class") for item in extra]

    title = str(project.get("title") or "").strip()
    summary = str(project.get("summary") or "").strip()
    meta = str(project.get("meta") or "").strip()
    footer = str(project.get("footer") or "").strip()
    site_path = str(project.get("site_path") or "").strip()
    if not all((title, summary, meta, footer, site_path)):
        raise RuntimeError(f"Project {slug} is missing card content")

    logo_name = logo_for(slug)
    article_classes = ["qs-project-tile", f"qs-project-tone-{tone}", *extra_classes]
    if not logo_name:
        article_classes.append("qs-project-no-logo")

    lines = [f'<article class="{" ".join(article_classes)}">']
    if logo_name:
        src = f"/images/projects/{slug}/{logo_name}"
        lines += [
            '<div class="qs-project-visual">',
            f'<img class="qs-project-logo" src="{html.escape(src, quote=True)}" alt="{html.escape(title, quote=True)} project logo" loading="lazy">',
            "</div>",
        ]

    lines += [
        '<div class="qs-project-body">',
        f'<p class="qs-card-meta">{html.escape(meta)}</p>',
        f'<h3><a href="{html.escape(site_path, quote=True)}">{html.escape(title)}</a></h3>',
        f'<p class="qs-project-card-summary">{html.escape(summary)}</p>',
        f'<div class="qs-project-footer"><span>{html.escape(footer)}</span><a href="{html.escape(site_path, quote=True)}">Details</a></div>',
        "</div>",
        "</article>",
    ]
    return lines


def render_output(item: dict) -> str:
    output_type = str(item.get("type") or "Output").strip()
    year = str(item.get("year") or "").strip()
    title = str(item.get("title") or "").strip()
    url = str(item.get("url") or "").strip()
    if not title or not url:
        raise RuntimeError(f"Related output is missing title/url: {item}")
    year_text = f" ({html.escape(year)})" if year else ""
    return (
        '<li class="qs-related-output">'
        f'<span class="qs-output-type">{html.escape(output_type)}</span>'
        f'<a href="{html.escape(url, quote=True)}">{html.escape(title)}</a>{year_text}'
        "</li>"
    )


def render() -> str:
    payload = load_registry()
    sections = payload["sections"]
    projects = payload["projects"]
    graph = load_graph()

    section_ids: set[str] = set()
    for section in sections:
        section_id = clean_class(section.get("id"), "section id")
        if section_id in section_ids:
            raise RuntimeError(f"Duplicate project section id: {section_id}")
        section_ids.add(section_id)
        if section_id not in graph:
            raise RuntimeError(f"Research graph is missing theme: {section_id}")

    extra_graph_ids = set(graph) - section_ids
    if extra_graph_ids:
        raise RuntimeError(f"Research graph contains unknown themes: {sorted(extra_graph_ids)}")

    seen_slugs: set[str] = set()
    for project in projects:
        slug = clean_class(project.get("slug"), "project slug")
        if slug in seen_slugs:
            raise RuntimeError(f"Duplicate project slug: {slug}")
        seen_slugs.add(slug)
        section_id = str(project.get("section") or "").strip()
        if section_id not in section_ids:
            raise RuntimeError(f"Project {slug} references unknown section {section_id!r}")

    lines = [
        "<!-- Generated by scripts/build_projects.py; do not edit manually. -->",
        "",
        "```{=html}",
        '<nav class="qs-project-theme-nav" aria-label="Research themes">',
    ]
    for section in sections:
        section_id = str(section["id"]).strip()
        heading = str(section.get("heading") or "").strip()
        if not heading:
            raise RuntimeError(f"Project section {section_id} is missing a heading")
        lines.append(f'<a href="#{html.escape(section_id, quote=True)}">{html.escape(heading)}</a>')
    lines += ["</nav>", "```", ""]

    for section in sections:
        section_id = str(section["id"]).strip()
        heading = str(section.get("heading") or "").strip()
        description = str(section.get("description") or "").strip()
        grid_class = str(section.get("grid_class") or "qs-project-grid").strip()
        class_tokens = [clean_class(token, f"{section_id} grid class") for token in grid_class.split()]
        group = [project for project in projects if project.get("section") == section_id]
        outputs = graph[section_id].get("outputs") or []
        if not isinstance(outputs, list):
            raise RuntimeError(f"Research graph outputs must be a list for {section_id}")
        if not group and not outputs:
            continue

        lines += [f"## {heading} {{#{section_id}}}", ""]
        if description:
            lines += [description, ""]

        if group:
            lines += ["```{=html}", f'<div class="{" ".join(class_tokens)}">']
            for project in group:
                lines.extend(render_card(project))
                lines.append("")
            if lines[-1] == "":
                lines.pop()
            lines += ["</div>", "```", ""]

        if outputs:
            lines += ["### Related outputs", "", "```{=html}", '<ul class="qs-related-output-list">']
            for item in outputs:
                lines.append(render_output(item))
            lines += ["</ul>", "```", ""]

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != expected:
            raise SystemExit("projects/_generated.md is stale; run python scripts/build_projects.py")
        print("Project cards and related outputs are synchronized.")
        return

    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
