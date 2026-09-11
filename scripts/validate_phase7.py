#!/usr/bin/env python3
"""Phase 7 certification for the Unified Scholarly Graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from site_config import ROOT

GRAPH = ROOT / "assets" / "data" / "scholarly-graph.json"
REGISTRY = ROOT / "graph" / "registry.json"
PAGE_FRAGMENT = ROOT / "research-graph" / "_generated.md"
SITE = ROOT / "_site"

ALLOWED_RELATIONS = {
    "part_of_theme",
    "created_by",
    "owned_by",
    "repository_for",
    "implemented_in",
    "contributes_to_theme",
    "related_to_project",
    "supports_project",
    "output_of_project",
}
FORBIDDEN_PUBLIC_SOURCE_MARKERS = (
    "repository-catalog.json",
    "private_repository",
    '"private": true',
)


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def validate_graph() -> tuple[int, int]:
    payload = load(GRAPH)
    registry = load(REGISTRY)

    if payload.get("schema_version") != 1:
        raise RuntimeError("scholarly-graph.json must use schema_version 1")
    if payload.get("public_only") is not True:
        raise RuntimeError("scholarly-graph.json must be public_only")
    if registry.get("schema_version") != 1:
        raise RuntimeError("graph/registry.json must use schema_version 1")

    approved_repositories = {
        str(value).strip()
        for value in registry.get("public_repositories") or []
        if str(value).strip()
    }
    if not approved_repositories:
        raise RuntimeError("graph/registry.json must define a non-empty public_repositories allowlist")
    graph_allowlist = {
        str(value).strip()
        for value in payload.get("public_repository_allowlist") or []
        if str(value).strip()
    }
    if graph_allowlist != approved_repositories:
        raise RuntimeError("Public graph repository allowlist does not match graph/registry.json")

    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise RuntimeError("Scholarly graph must contain nodes and edges lists")

    ids: set[str] = set()
    dois: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise RuntimeError("Every graph node must be an object")
        node_id = str(node.get("id") or "").strip()
        if not node_id or node_id in ids:
            raise RuntimeError(f"Missing or duplicate graph node id: {node_id!r}")
        ids.add(node_id)
        if node.get("visibility") != "public":
            raise RuntimeError(f"Non-public node serialized into public graph: {node_id}")
        url = str(node.get("canonical_url") or "").strip()
        if url:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise RuntimeError(f"Invalid canonical URL for {node_id}: {url}")

        full_name = str(node.get("full_name") or "").strip()
        repository = str(node.get("repository") or "").strip()
        if node.get("kind") == "Repository":
            if not full_name or full_name not in approved_repositories:
                raise RuntimeError(f"Repository node bypasses public allowlist: {node_id} -> {full_name!r}")
        if repository and repository not in approved_repositories:
            raise RuntimeError(f"Node exposes repository outside public allowlist: {node_id} -> {repository}")

        doi = str((node.get("identifiers") or {}).get("doi") or "").casefold()
        if doi:
            if doi in dois:
                raise RuntimeError(f"Duplicate DOI {doi} in {dois[doi]} and {node_id}")
            dois[doi] = node_id

    edge_keys: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise RuntimeError("Every graph edge must be an object")
        source = str(edge.get("source") or "")
        relation = str(edge.get("relation") or "")
        target = str(edge.get("target") or "")
        if source not in ids or target not in ids:
            raise RuntimeError(f"Dangling graph edge: {edge}")
        if relation not in ALLOWED_RELATIONS:
            raise RuntimeError(f"Unknown graph relation: {relation}")
        key = (source, relation, target)
        if key in edge_keys:
            raise RuntimeError(f"Duplicate graph edge: {key}")
        edge_keys.add(key)

    featured = payload.get("featured") or {}
    if not isinstance(featured, dict):
        raise RuntimeError("featured must be an object")
    for label, node_id in featured.items():
        if node_id and node_id not in ids:
            raise RuntimeError(f"Featured {label} references missing node: {node_id}")

    source_text = GRAPH.read_text(encoding="utf-8").casefold()
    for marker in FORBIDDEN_PUBLIC_SOURCE_MARKERS:
        if marker.casefold() in source_text:
            raise RuntimeError(f"Private/source-firewall violation in scholarly graph: {marker}")

    source_contract = payload.get("source_contract") or {}
    if "raw repository catalogue" not in str(source_contract.get("forbidden") or "").casefold():
        raise RuntimeError("Scholarly graph must declare the raw repository-catalogue firewall")

    stats = payload.get("stats") or {}
    if stats.get("nodes") != len(nodes) or stats.get("edges") != len(edges):
        raise RuntimeError("Graph stats do not match node/edge counts")

    fragment = PAGE_FRAGMENT.read_text(encoding="utf-8")
    for marker in ("qs-graph-summary", "Public graph:", "Provenance and graph contract"):
        if marker not in fragment:
            raise RuntimeError(f"Research Graph fragment is missing {marker!r}")

    return len(nodes), len(edges)


def validate_rendered() -> None:
    page = SITE / "research-graph" / "index.html"
    graph_json = SITE / "assets" / "data" / "scholarly-graph.json"
    if not page.is_file():
        raise RuntimeError("Rendered Research Graph page is missing")
    if not graph_json.is_file() or graph_json.stat().st_size == 0:
        raise RuntimeError("Machine-readable scholarly graph was not published")
    body = page.read_text(encoding="utf-8", errors="strict")
    for marker in ("qs-graph-summary", "Public graph:", "Provenance and graph contract"):
        if marker not in body:
            raise RuntimeError(f"Rendered Research Graph is missing {marker!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()

    if args.mode in {"source", "all"}:
        nodes, edges = validate_graph()
        print(
            f"Phase 7 source QA PASS: {nodes} public nodes, {edges} validated edges, "
            "repository allowlist and privacy firewall active."
        )
    if args.mode in {"rendered", "all"}:
        validate_rendered()
        print("Phase 7 rendered QA PASS: public Research Graph page and machine-readable JSON deployed.")


if __name__ == "__main__":
    main()
