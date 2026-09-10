#!/usr/bin/env python3
"""Build a deterministic research-theme graph from site catalogues.

Theme definitions and keyword rules live in projects/registry.json. Project
membership is explicit there, while scholarly outputs are classified
conservatively from publications, talks, and software metadata. The generated
graph is an auditable derived artefact used by the Projects page.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from site_config import ROOT

REGISTRY = ROOT / "projects" / "registry.json"
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
TALKS = ROOT / "assets" / "data" / "conferences.json"
SOFTWARE = ROOT / "assets" / "data" / "software.json"
TARGET = ROOT / "assets" / "data" / "research-graph.json"

PUBLICATION_TYPES = {
    "Journal articles": "Paper",
    "Preprints & working papers": "Preprint",
    "Books & chapters": "Book",
    "Theses": "Thesis",
    "Reports & technical outputs": "Report",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().replace("–", "-").replace("—", "-")
    return " ".join(re.sub(r"[^a-z0-9+.-]+", " ", text).split())


def output_url(pub: dict[str, Any]) -> str:
    category = str(pub.get("output_category") or "")
    anchors = {
        "Journal articles": "papers",
        "Preprints & working papers": "preprints",
        "Books & chapters": "books",
        "Theses": "theses",
        "Reports & technical outputs": "reports",
    }
    if category in anchors:
        return f"/publications/#{anchors[category]}"
    return str(pub.get("url") or "").strip()


def candidates() -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []

    for pub in load_json(PUBLICATIONS).get("publications", []):
        category = str(pub.get("output_category") or "")
        output_type = PUBLICATION_TYPES.get(category)
        if not output_type:
            continue
        title = str(pub.get("title") or "").strip()
        if not title:
            continue
        text = " ".join(
            str(pub.get(key) or "")
            for key in ("title", "journal", "outlet", "type", "source")
        )
        outputs.append({
            "id": f"publication:{normalize(title)}:{pub.get('year', '')}",
            "type": output_type,
            "year": str(pub.get("year") or ""),
            "title": title,
            "url": output_url(pub),
            "search_text": normalize(text),
            "source": "publications",
        })

    for talk in load_json(TALKS).get("conferences", []):
        title = str(talk.get("title") or "").strip()
        if not title:
            continue
        presentation_type = str(talk.get("presentation_type") or "Talk").strip()
        output_type = "Poster" if "poster" in presentation_type.casefold() else "Talk"
        text = " ".join(
            str(talk.get(key) or "")
            for key in ("title", "summary", "event", "presentation_type")
        )
        outputs.append({
            "id": f"talk:{talk.get('date', '')}:{normalize(title)}",
            "type": output_type,
            "year": str(talk.get("year") or str(talk.get("date") or "")[:4]),
            "title": title,
            "url": str(talk.get("site_path") or "").strip() or "/talks/",
            "search_text": normalize(text),
            "source": "talks",
        })

    for item in load_json(SOFTWARE).get("software", []):
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        text = " ".join(
            str(item.get(key) or "")
            for key in ("name", "description", "summary", "category", "language")
        )
        outputs.append({
            "id": f"software:{str(item.get('full_name') or name)}",
            "type": "Software",
            "year": str(item.get("updated_at") or "")[:4],
            "title": name,
            "url": str(item.get("site_path") or "").strip() or str(item.get("html_url") or "").strip(),
            "search_text": normalize(text),
            "source": "software",
        })

    return outputs


def classify(output: dict[str, Any], sections: list[dict[str, Any]]) -> str | None:
    text = str(output.get("search_text") or "")
    scores: list[tuple[int, int, str]] = []
    for index, section in enumerate(sections):
        section_id = str(section.get("id") or "").strip()
        keywords = section.get("keywords") or []
        if not section_id or not isinstance(keywords, list):
            raise RuntimeError(f"Invalid theme keyword configuration: {section}")
        score = sum(1 for keyword in keywords if normalize(keyword) and normalize(keyword) in text)
        if score:
            scores.append((score, -index, section_id))
    if not scores:
        return None
    scores.sort(reverse=True)
    return scores[0][2]


def build_payload() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    sections = registry.get("sections")
    projects = registry.get("projects")
    if not isinstance(sections, list) or not sections:
        raise RuntimeError("projects/registry.json must contain sections")
    if not isinstance(projects, list):
        raise RuntimeError("projects/registry.json must contain projects")

    section_ids = [str(section.get("id") or "").strip() for section in sections]
    if any(not value for value in section_ids) or len(set(section_ids)) != len(section_ids):
        raise RuntimeError("Research theme ids must be present and unique")

    output_groups: dict[str, list[dict[str, Any]]] = {section_id: [] for section_id in section_ids}
    unclassified: list[dict[str, Any]] = []
    for output in candidates():
        theme_id = classify(output, sections)
        clean = {key: value for key, value in output.items() if key != "search_text"}
        if theme_id is None:
            unclassified.append(clean)
        else:
            output_groups[theme_id].append(clean)

    themes = []
    for section in sections:
        section_id = str(section["id"])
        theme_projects = [
            str(project.get("slug") or "")
            for project in projects
            if str(project.get("section") or "") == section_id
        ]
        theme_outputs = sorted(
            output_groups[section_id],
            key=lambda item: (str(item.get("year") or ""), str(item.get("title") or "").casefold()),
            reverse=True,
        )
        themes.append({
            "id": section_id,
            "heading": str(section.get("heading") or ""),
            "description": str(section.get("description") or ""),
            "projects": theme_projects,
            "outputs": theme_outputs,
        })

    return {
        "schema_version": 1,
        "sources": [
            "projects/registry.json",
            "assets/data/publications.json",
            "assets/data/conferences.json",
            "assets/data/software.json",
        ],
        "themes": themes,
        "unclassified_outputs": sorted(
            unclassified,
            key=lambda item: (str(item.get("year") or ""), str(item.get("title") or "").casefold()),
            reverse=True,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = json.dumps(build_payload(), ensure_ascii=False, indent=2) + "\n"
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if args.check:
        if current != expected:
            raise SystemExit("assets/data/research-graph.json is stale; run python scripts/build_research_graph.py")
        print("Research graph is synchronized.")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
