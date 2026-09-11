#!/usr/bin/env python3
"""Build the public Unified Scholarly Graph and its human-readable index."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from site_config import ROOT

SITE_URL = "https://qselmer.github.io"
CONFIG = ROOT / "config" / "site.json"
GRAPH_REGISTRY = ROOT / "graph" / "registry.json"
PROJECTS = ROOT / "projects" / "registry.json"
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
TALKS = ROOT / "assets" / "data" / "conferences.json"
SOFTWARE = ROOT / "assets" / "data" / "software.json"
TEACHING = ROOT / "assets" / "data" / "teaching.json"
BLOG = ROOT / "blog" / "registry.json"
METRICS = ROOT / "assets" / "data" / "research-metrics.json"
TARGET = ROOT / "assets" / "data" / "scholarly-graph.json"
FRAGMENT = ROOT / "research-graph" / "_generated.md"

FORMAL_PUBLICATION_TYPES = {
    "Journal articles": "Paper",
    "Preprints & working papers": "Preprint",
    "Books & chapters": "Book",
    "Theses": "Thesis",
    "Reports & technical outputs": "Report",
}
PUBLICATION_ANCHORS = {
    "Journal articles": "papers",
    "Preprints & working papers": "preprints",
    "Books & chapters": "books",
    "Theses": "theses",
    "Reports & technical outputs": "reports",
}
SCHOLARLY_KINDS = {"Publication", "Talk", "Poster", "Software", "Teaching", "Post"}


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


def slug(value: object) -> str:
    text = normalize(value)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "untitled"


def canonical_doi(value: object) -> str:
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(value or "").strip(), flags=re.I).casefold()


def absolute_url(value: object, *, project_path: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith(("https://", "http://")):
        return text
    if not text.startswith("/"):
        text = f"/projects/{text}" if project_path else f"/{text}"
    return SITE_URL + text


def repo_id(full_name: str) -> str:
    return f"repository:github:{full_name.casefold()}"


def add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    node_id = str(node.get("id") or "").strip()
    if not node_id:
        raise RuntimeError("Graph node is missing id")
    if node_id in nodes:
        if nodes[node_id] != node:
            raise RuntimeError(f"Conflicting graph node id: {node_id}")
        return
    if node.get("visibility") != "public":
        raise RuntimeError(f"Public graph cannot contain non-public node: {node_id}")
    url = str(node.get("canonical_url") or "").strip()
    if url and urlparse(url).scheme not in {"http", "https"}:
        raise RuntimeError(f"Canonical URL must be absolute HTTP(S): {node_id}: {url}")
    nodes[node_id] = node


def add_edge(edges: list[dict[str, str]], seen: set[tuple[str, str, str]], source: str, relation: str, target: str) -> None:
    key = (source, relation, target)
    if key in seen:
        return
    seen.add(key)
    edges.append({"source": source, "relation": relation, "target": target})


def theme_for_text(
    text: str,
    sections: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    kind: str,
    match_value: str,
) -> str | None:
    norm_match = normalize(match_value)
    for rule in overrides:
        if str(rule.get("kind") or "").casefold() != kind.casefold():
            continue
        if normalize(rule.get("match")) == norm_match:
            return str(rule.get("theme") or "").strip() or None

    scores: list[tuple[int, int, str]] = []
    norm_text = normalize(text)
    for index, section in enumerate(sections):
        theme_id = str(section.get("id") or "").strip()
        keywords = section.get("keywords") or []
        score = sum(1 for keyword in keywords if normalize(keyword) and normalize(keyword) in norm_text)
        if score:
            scores.append((score, -index, theme_id))
    if not scores:
        return None
    scores.sort(reverse=True)
    return scores[0][2]


def project_theme_overrides(project_registry: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for item in project_registry.get("output_theme_overrides") or []:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        kind = {"publications": "Publication", "talks": "Talk"}.get(source)
        if kind:
            rules.append({
                "kind": kind,
                "match": str(item.get("title") or ""),
                "theme": str(item.get("section") or ""),
            })
    return rules


def build_payload() -> dict[str, Any]:
    config = load_json(CONFIG)
    graph_registry = load_json(GRAPH_REGISTRY)
    project_registry = load_json(PROJECTS)
    publications = load_json(PUBLICATIONS)
    talks = load_json(TALKS)
    software = load_json(SOFTWARE)
    teaching = load_json(TEACHING)
    blog = load_json(BLOG)
    metrics = load_json(METRICS)

    if graph_registry.get("schema_version") != 1:
        raise RuntimeError("graph/registry.json must use schema_version 1")
    if project_registry.get("schema_version") != 1:
        raise RuntimeError("projects/registry.json must use schema_version 1")

    policy = graph_registry.get("visibility_policy") or {}
    if policy.get("public_only") is not True:
        raise RuntimeError("Unified Scholarly Graph must use public_only visibility policy")

    forbidden = [str(x).casefold() for x in policy.get("forbidden_source_substrings") or []]
    declared_sources = [
        "config/site.json",
        "graph/registry.json",
        "projects/registry.json",
        "assets/data/publications.json",
        "assets/data/conferences.json",
        "assets/data/software.json",
        "assets/data/teaching.json",
        "blog/registry.json",
        "assets/data/research-metrics.json",
    ]
    for path in declared_sources:
        if any(token and token in path.casefold() for token in forbidden):
            raise RuntimeError(f"Forbidden source entered public graph pipeline: {path}")

    sections = project_registry.get("sections") or []
    projects = project_registry.get("projects") or []
    if not isinstance(sections, list) or not isinstance(projects, list):
        raise RuntimeError("projects/registry.json must contain sections and projects lists")

    theme_ids = {str(item.get("id") or "").strip() for item in sections}
    if "" in theme_ids or len(theme_ids) != len(sections):
        raise RuntimeError("Theme ids must be present and unique")

    registry_overrides = graph_registry.get("theme_overrides") or []
    if not isinstance(registry_overrides, list):
        raise RuntimeError("graph theme_overrides must be a list")
    overrides = project_theme_overrides(project_registry) + registry_overrides
    for rule in overrides:
        if str(rule.get("theme") or "") not in theme_ids:
            raise RuntimeError(f"Theme override references unknown theme: {rule}")

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    person_id = "person:elmer-quispe-salazar"

    identity = config.get("identity") or {}
    oa = metrics.get("openalex") or {}
    add_node(nodes, {
        "id": person_id,
        "kind": "Person",
        "title": str(identity.get("name") or "Elmer Quispe-Salazar"),
        "canonical_url": SITE_URL + "/",
        "visibility": "public",
        "identifiers": {
            "orcid": str(identity.get("orcid") or ""),
            "github": str(identity.get("github") or ""),
            "google_scholar": str(identity.get("google_scholar") or ""),
        },
        "metrics": {
            "citations": oa.get("cited_by_count"),
            "h_index": oa.get("h_index"),
            "i10_index": oa.get("i10_index"),
            "orcid_works": metrics.get("public_orcid_works"),
            "openalex_works": oa.get("works_count"),
        },
        "provenance": [
            {"source": "config/site.json", "authority": "curated"},
            {"source": "assets/data/research-metrics.json", "authority": "ORCID + OpenAlex"},
        ],
    })

    for section in sections:
        theme_id = str(section["id"])
        node_id = f"theme:{theme_id}"
        add_node(nodes, {
            "id": node_id,
            "kind": "Theme",
            "title": str(section.get("heading") or theme_id),
            "canonical_url": SITE_URL + f"/projects/#{theme_id}",
            "visibility": "public",
            "research_question": str(section.get("research_question") or ""),
            "why_it_matters": str(section.get("why_it_matters") or ""),
            "provenance": [{"source": "projects/registry.json", "authority": "curated"}],
        })

    project_ids: set[str] = set()
    for project in projects:
        project_slug = str(project.get("slug") or "").strip()
        if not project_slug:
            raise RuntimeError("Project is missing slug")
        theme_id = str(project.get("section") or "").strip()
        if theme_id not in theme_ids:
            raise RuntimeError(f"Project {project_slug} references unknown theme {theme_id}")
        node_id = f"project:{project_slug}"
        project_ids.add(node_id)
        source_repository = str(project.get("source_repository") or "").strip()
        canonical_url = absolute_url(project.get("site_path"), project_path=True)
        add_node(nodes, {
            "id": node_id,
            "kind": "Project",
            "title": str(project.get("title") or project_slug),
            "canonical_url": canonical_url,
            "visibility": "public",
            "status": str(project.get("stage") or ""),
            "summary": str(project.get("summary") or ""),
            "repository": source_repository,
            "provenance": [{"source": "projects/registry.json", "authority": "curated"}],
        })
        add_edge(edges, seen_edges, node_id, "part_of_theme", f"theme:{theme_id}")
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        if source_repository:
            rid = repo_id(source_repository)
            add_node(nodes, {
                "id": rid,
                "kind": "Repository",
                "title": source_repository.split("/", 1)[-1],
                "canonical_url": f"https://github.com/{source_repository}",
                "visibility": "public",
                "full_name": source_repository,
                "provenance": [{"source": "projects/registry.json", "authority": "curated"}],
            })
            add_edge(edges, seen_edges, rid, "repository_for", node_id)
            add_edge(edges, seen_edges, rid, "owned_by", person_id)

    for pub in publications.get("publications") or []:
        category = str(pub.get("output_category") or "")
        output_type = FORMAL_PUBLICATION_TYPES.get(category)
        if not output_type:
            continue
        title = str(pub.get("title") or "").strip()
        year = str(pub.get("year") or "").strip()
        if not title:
            continue
        doi = canonical_doi(pub.get("doi"))
        node_id = f"publication:doi:{doi}" if doi else f"publication:{slug(title)}:{year or 'nd'}"
        url = f"https://doi.org/{doi}" if doi else str(pub.get("url") or "").strip()
        if not url:
            anchor = PUBLICATION_ANCHORS.get(category, "papers")
            url = SITE_URL + f"/publications/#{anchor}"
        elif url.startswith("/"):
            url = SITE_URL + url
        text = " ".join(str(pub.get(key) or "") for key in ("title", "journal", "type", "source", "output_category"))
        theme_id = theme_for_text(text, sections, overrides, "Publication", title)
        add_node(nodes, {
            "id": node_id,
            "kind": "Publication",
            "subtype": output_type,
            "title": title,
            "year": year,
            "canonical_url": url,
            "visibility": "public",
            "identifiers": {"doi": doi} if doi else {},
            "venue": str(pub.get("journal") or ""),
            "provenance": [{"source": "assets/data/publications.json", "authority": str(pub.get("source") or "ORCID")}],
        })
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        if theme_id:
            add_edge(edges, seen_edges, node_id, "contributes_to_theme", f"theme:{theme_id}")

    for talk in talks.get("conferences") or []:
        title = str(talk.get("title") or "").strip()
        date = str(talk.get("date") or "").strip()
        if not title or not date:
            continue
        ptype = str(talk.get("presentation_type") or "Talk")
        kind = "Poster" if "poster" in ptype.casefold() else "Talk"
        node_id = f"talk:{date}:{slug(title)}"
        text = " ".join(str(talk.get(key) or "") for key in ("title", "summary", "event", "presentation_type"))
        theme_id = theme_for_text(text, sections, overrides, "Talk", title)
        add_node(nodes, {
            "id": node_id,
            "kind": kind,
            "title": title,
            "year": str(talk.get("year") or date[:4]),
            "canonical_url": absolute_url(talk.get("site_path") or "/talks/"),
            "visibility": "public",
            "event": str(talk.get("event") or ""),
            "presentation_type": ptype,
            "provenance": [{
                "source": "assets/data/conferences.json",
                "authority": str(talk.get("source") or talk.get("record_origin") or "curated"),
            }],
        })
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        if theme_id:
            add_edge(edges, seen_edges, node_id, "contributes_to_theme", f"theme:{theme_id}")

    for item in software.get("software") or []:
        full_name = str(item.get("full_name") or "").strip()
        name = str(item.get("name") or full_name.rsplit("/", 1)[-1]).strip()
        if not full_name:
            continue
        node_id = f"software:github:{full_name.casefold()}"
        text = " ".join(str(item.get(key) or "") for key in ("name", "summary", "description", "category", "language"))
        theme_id = theme_for_text(text, sections, overrides, "Software", full_name)
        add_node(nodes, {
            "id": node_id,
            "kind": "Software",
            "title": name,
            "canonical_url": absolute_url(item.get("site_path") or item.get("html_url")),
            "visibility": "public",
            "status": str(item.get("maturity") or ""),
            "language": str(item.get("language") or ""),
            "repository": full_name,
            "provenance": [{"source": "assets/data/software.json", "authority": "curated public mirror"}],
        })
        rid = repo_id(full_name)
        add_node(nodes, {
            "id": rid,
            "kind": "Repository",
            "title": full_name.split("/", 1)[-1],
            "canonical_url": f"https://github.com/{full_name}",
            "visibility": "public",
            "full_name": full_name,
            "provenance": [{"source": "assets/data/software.json", "authority": "curated public mirror"}],
        })
        add_edge(edges, seen_edges, node_id, "implemented_in", rid)
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        add_edge(edges, seen_edges, rid, "owned_by", person_id)
        if theme_id:
            add_edge(edges, seen_edges, node_id, "contributes_to_theme", f"theme:{theme_id}")

    teaching_items: list[dict[str, Any]] = []
    teaching_items.extend(teaching.get("teaching") or [])
    teaching_items.extend(teaching.get("infrastructure") or [])
    for item in teaching_items:
        full_name = str(item.get("full_name") or "").strip()
        name = str(item.get("name") or full_name.rsplit("/", 1)[-1]).strip()
        if not full_name:
            continue
        node_id = f"teaching:github:{full_name.casefold()}"
        text = " ".join(str(item.get(key) or "") for key in ("name", "summary", "description", "category"))
        theme_id = theme_for_text(text, sections, overrides, "Teaching", full_name)
        add_node(nodes, {
            "id": node_id,
            "kind": "Teaching",
            "title": name,
            "canonical_url": absolute_url(item.get("site_path") or item.get("html_url")),
            "visibility": "public",
            "status": str(item.get("maturity") or ""),
            "repository": full_name,
            "provenance": [{"source": "assets/data/teaching.json", "authority": "curated public mirror"}],
        })
        rid = repo_id(full_name)
        add_node(nodes, {
            "id": rid,
            "kind": "Repository",
            "title": full_name.split("/", 1)[-1],
            "canonical_url": f"https://github.com/{full_name}",
            "visibility": "public",
            "full_name": full_name,
            "provenance": [{"source": "assets/data/teaching.json", "authority": "curated public mirror"}],
        })
        add_edge(edges, seen_edges, node_id, "implemented_in", rid)
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        add_edge(edges, seen_edges, rid, "owned_by", person_id)
        if theme_id:
            add_edge(edges, seen_edges, node_id, "contributes_to_theme", f"theme:{theme_id}")

    for post in blog.get("posts") or []:
        if str(post.get("status") or "published") != "published":
            continue
        post_slug = str(post.get("slug") or "").strip()
        title = str(post.get("title") or "").strip()
        if not post_slug or not title:
            continue
        node_id = f"post:{post_slug}"
        text = " ".join(str(post.get(key) or "") for key in ("title", "excerpt", "topic", "level"))
        theme_id = theme_for_text(text, sections, overrides, "Post", title)
        add_node(nodes, {
            "id": node_id,
            "kind": "Post",
            "title": title,
            "year": str(post.get("date") or "")[:4],
            "canonical_url": absolute_url(post.get("route")),
            "visibility": "public",
            "topic": str(post.get("topic") or ""),
            "provenance": [{"source": "blog/registry.json", "authority": "curated"}],
        })
        add_edge(edges, seen_edges, node_id, "created_by", person_id)
        if theme_id:
            add_edge(edges, seen_edges, node_id, "contributes_to_theme", f"theme:{theme_id}")

    relations = graph_registry.get("project_relations") or []
    if not isinstance(relations, list):
        raise RuntimeError("project_relations must be a list")
    for rel in relations:
        source = str(rel.get("node") or "").strip()
        project = str(rel.get("project") or "").strip()
        relation = str(rel.get("relation") or "related_to_project").strip()
        project_id = project if project.startswith("project:") else f"project:{project}"
        if source not in nodes:
            raise RuntimeError(f"Graph relation references unknown node: {source}")
        if project_id not in project_ids:
            raise RuntimeError(f"Graph relation references unknown project: {project_id}")
        add_edge(edges, seen_edges, source, relation, project_id)

    node_ids = set(nodes)
    for edge in edges:
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise RuntimeError(f"Dangling graph edge: {edge}")

    dois: dict[str, str] = {}
    for node in nodes.values():
        doi = str((node.get("identifiers") or {}).get("doi") or "").casefold()
        if doi:
            if doi in dois and dois[doi] != node["id"]:
                raise RuntimeError(f"Duplicate DOI in public graph: {doi}")
            dois[doi] = node["id"]

    kinds = Counter(node["kind"] for node in nodes.values())
    featured = graph_registry.get("featured") or {}
    if not isinstance(featured, dict):
        raise RuntimeError("featured must be an object")
    for label, node_id in featured.items():
        if node_id and node_id not in nodes:
            raise RuntimeError(f"Featured {label} references unknown graph node: {node_id}")

    linked_to_project = {
        edge["source"]
        for edge in edges
        if edge["relation"] in {"related_to_project", "supports_project", "output_of_project"}
    }
    unlinked_outputs = sorted(
        node["id"] for node in nodes.values()
        if node["kind"] in SCHOLARLY_KINDS and node["id"] not in linked_to_project
    )

    return {
        "schema_version": 1,
        "graph_id": "qselmer-unified-scholarly-graph",
        "public_only": True,
        "person": person_id,
        "source_contract": {
            "canonical_publications": "ORCID/Crossref public mirror",
            "metrics": "ORCID/OpenAlex public metrics mirror",
            "repositories": "GitHub metadata filtered through curated public registries",
            "curated_relations": "graph/registry.json + projects/registry.json",
            "forbidden": "Raw repository catalogue and private-repository metadata are never serialized into this graph"
        },
        "sources": declared_sources,
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "by_kind": dict(sorted(kinds.items())),
            "unlinked_outputs_to_project": len(unlinked_outputs)
        },
        "featured": featured,
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], str(item.get("title") or "").casefold(), item["id"])),
        "edges": sorted(edges, key=lambda item: (item["source"], item["relation"], item["target"])),
        "unlinked_outputs_to_project": unlinked_outputs
    }


def badge(value: str) -> str:
    return f'<span class="qs-graph-kind">{html.escape(value)}</span>'


def build_fragment(payload: dict[str, Any]) -> str:
    nodes = {node["id"]: node for node in payload["nodes"]}
    incoming: dict[str, list[dict[str, str]]] = defaultdict(list)
    for edge in payload["edges"]:
        incoming[edge["target"]].append(edge)

    stats = payload["stats"]
    by_kind = stats["by_kind"]
    summary_order = ("Theme", "Project", "Publication", "Talk", "Poster", "Software", "Teaching", "Post")
    cards = []
    for kind in summary_order:
        count = int(by_kind.get(kind, 0))
        if count:
            cards.append(
                f'<div class="qs-graph-stat"><strong>{count}</strong><span>{html.escape(kind)}'
                f'{"s" if count != 1 and kind not in {"Software", "Teaching"} else ""}</span></div>'
            )

    lines = [
        "<!-- Generated by scripts/build_scholarly_graph.py; do not edit manually. -->",
        "",
        "```{=html}",
        '<div class="qs-graph-summary" aria-label="Scholarly graph summary">',
        *cards,
        "</div>",
        '<p class="qs-graph-contract"><strong>Public graph:</strong> canonical public mirrors and curated registries only. Private repository metadata is excluded before serialization.</p>',
        "```",
        ""
    ]

    theme_nodes = [node for node in payload["nodes"] if node["kind"] == "Theme"]
    for theme in theme_nodes:
        theme_id = theme["id"]
        anchor = theme_id.split(":", 1)[1]
        lines += [f"## {theme['title']} {{#{anchor}}}", ""]
        question = str(theme.get("research_question") or "")
        why = str(theme.get("why_it_matters") or "")
        if question or why:
            lines += ["```{=html}", '<p class="qs-graph-rationale">']
            if question:
                lines.append(f"<strong>Research question:</strong> {html.escape(question)} ")
            if why:
                lines.append(f"<strong>Why it matters:</strong> {html.escape(why)}")
            lines += ["</p>", "```", ""]

        project_edges = [edge for edge in incoming[theme_id] if edge["relation"] == "part_of_theme"]
        output_edges = [edge for edge in incoming[theme_id] if edge["relation"] == "contributes_to_theme"]
        project_nodes = [nodes[edge["source"]] for edge in project_edges]
        output_nodes = [nodes[edge["source"]] for edge in output_edges]

        if project_nodes:
            lines += ["### Projects", "", "```{=html}", '<ul class="qs-graph-list">']
            for project in sorted(project_nodes, key=lambda item: item["title"].casefold()):
                repos = [nodes[edge["source"]] for edge in incoming[project["id"]] if edge["relation"] == "repository_for"]
                repo_link = ""
                if repos:
                    repo = repos[0]
                    repo_link = f' <a class="qs-graph-repo" href="{html.escape(repo["canonical_url"], quote=True)}">Repository</a>'
                lines.append(
                    '<li><span class="qs-graph-kind">Project</span>'
                    f'<a href="{html.escape(project["canonical_url"], quote=True)}">{html.escape(project["title"])}</a>'
                    f'{repo_link}</li>'
                )
            lines += ["</ul>", "```", ""]

        if output_nodes:
            lines += ["### Outputs and resources", "", "```{=html}", '<ul class="qs-graph-list">']
            for node in sorted(output_nodes, key=lambda item: (str(item.get("year") or ""), item["title"].casefold()), reverse=True):
                year = f' <span class="qs-graph-year">{html.escape(str(node.get("year") or ""))}</span>' if node.get("year") else ""
                lines.append(
                    f'<li>{badge(node["kind"])}'
                    f'<a href="{html.escape(node["canonical_url"], quote=True)}">{html.escape(node["title"])}</a>{year}</li>'
                )
            lines += ["</ul>", "```", ""]

    lines += [
        "## Provenance and graph contract {#provenance}",
        "",
        "The graph is generated from public scholarly mirrors and curated website registries. Repository metadata enters the public graph only after it has been selected for a public Project, Software, or Teaching catalogue. ORCID and OpenAlex contribute public scholarly records and metrics; the raw repository catalogue is not serialized into this website graph.",
        ""
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = build_payload()
    expected_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    expected_fragment = build_fragment(payload)

    if args.check:
        stale: list[str] = []
        for path, expected in ((TARGET, expected_json), (FRAGMENT, expected_fragment)):
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != expected:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            raise SystemExit("Unified Scholarly Graph outputs are stale; run python scripts/build_scholarly_graph.py: " + ", ".join(stale))
        print(f"Unified Scholarly Graph synchronized: {payload['stats']['nodes']} nodes, {payload['stats']['edges']} edges.")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected_json, encoding="utf-8")
    FRAGMENT.write_text(expected_fragment, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    print(f"Wrote {FRAGMENT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
