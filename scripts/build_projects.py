#!/usr/bin/env python3
"""Render the thematic Research catalogue from the project registry and research graph."""

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
CLASS_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")
THEME_BADGE_LABELS = ("System", "Focus", "Data")


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


def render_badges(items: list[dict], owner: str, expected_labels: tuple[str, ...] | None = None) -> str:
    if not items:
        return ""
    if expected_labels is not None:
        labels = tuple(str(item.get("label") or "").strip() for item in items if isinstance(item, dict))
        if labels != expected_labels:
            raise RuntimeError(f"{owner} badges must use labels {expected_labels}; found {labels}")
    parts = ['<div class="qs-badge-row">']
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"{owner} badge {index} must be an object")
        label = str(item.get("label") or "").strip()
        value = str(item.get("value") or "").strip()
        tone = clean_class(item.get("tone") or "blue", f"{owner} badge tone")
        if not label or not value:
            raise RuntimeError(f"{owner} badge {index} needs label and value")
        parts.append(
            f'<span class="qs-badge qs-badge-{html.escape(tone, quote=True)}">'
            f'<span class="qs-badge-label">{html.escape(label)}</span>'
            f'<span class="qs-badge-value">{html.escape(value)}</span>'
            '</span>'
        )
    parts.append("</div>")
    return "".join(parts)


def render_card(project: dict) -> list[str]:
    """Render every Research project with one editorial card format.

    Project logos remain canonical assets for project detail pages, but the Research
    catalogue intentionally does not use them. This keeps projects with and without
    logos visually identical and avoids loading large logo files in the catalogue.
    """
    slug = clean_class(project.get("slug"), "project slug")
    title = str(project.get("title") or "").strip()
    summary = str(project.get("summary") or "").strip()
    context = str(project.get("context") or "").strip()
    site_path = str(project.get("site_path") or "").strip()
    link_label = str(project.get("link_label") or "Details").strip()
    if not all((title, summary, context, site_path, link_label)):
        raise RuntimeError(f"Project {slug} is missing card content")

    return [
        '<article class="qs-project-tile">',
        '<div class="qs-project-body">',
        '<span class="qs-project-type">PROJECT</span>',
        f'<h3><a href="{html.escape(site_path, quote=True)}">{html.escape(title)}</a></h3>',
        f'<p class="qs-project-card-summary">{html.escape(summary)}</p>',
        f'<div class="qs-project-footer"><span>{html.escape(context)}</span><a href="{html.escape(site_path, quote=True)}">{html.escape(link_label)}</a></div>',
        "</div>",
        "</article>",
    ]


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
        nav_label = str(section.get("nav_label") or heading).strip()
        if not heading or not nav_label:
            raise RuntimeError(f"Project section {section_id} is missing a heading or nav label")
        lines.append(f'<a href="#{html.escape(section_id, quote=True)}">{html.escape(nav_label)}</a>')
    lines += ["</nav>", "```", ""]

    for section in sections:
        section_id = str(section["id"]).strip()
        heading = str(section.get("heading") or "").strip()
        question = str(section.get("research_question") or "").strip()
        why = str(section.get("why_it_matters") or "").strip()
        badges = section.get("badges") or []
        if not isinstance(badges, list):
            raise RuntimeError(f"Research theme {section_id} badges must be a list")
        grid_class = str(section.get("grid_class") or "qs-project-grid").strip()
        class_tokens = [clean_class(token, f"{section_id} grid class") for token in grid_class.split()]
        group = [project for project in projects if project.get("section") == section_id]
        outputs = graph[section_id].get("outputs") or []
        if not isinstance(outputs, list):
            raise RuntimeError(f"Research graph outputs must be a list for {section_id}")
        if not question or not why:
            raise RuntimeError(f"Research theme {section_id} needs research_question and why_it_matters")

        lines += [f"## {heading} {{#{section_id}}}", "", "```{=html}"]
        badge_html = render_badges(badges, f"Research theme {section_id}", THEME_BADGE_LABELS)
        if badge_html:
            lines.append(f'<div class="qs-theme-badges">{badge_html}</div>')
        lines += [
            '<p class="qs-theme-rationale">'
            f'<strong>Research question:</strong> {html.escape(question)} '
            f'<strong>Why it matters:</strong> {html.escape(why)}'
            "</p>",
            "```",
            "",
        ]

        if group:
            lines += ["### Current projects", "", "```{=html}", f'<div class="{" ".join(class_tokens)}">']
            for project in group:
                lines.extend(render_card(project))
                lines.append("")
            if lines[-1] == "":
                lines.pop()
            lines += ["</div>", "```", ""]

        if outputs:
            lines += ["### Outputs", "", "```{=html}", '<ul class="qs-related-output-list">']
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
        print("Research themes, project cards, and outputs are synchronized.")
        return

    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
