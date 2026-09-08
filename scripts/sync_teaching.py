#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from site_config import ROOT, profile_source

REGISTRY = ROOT / "teaching" / "registry.json"
TARGET = ROOT / "assets" / "data" / "teaching.json"


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def load_catalog(path: Path | None) -> dict:
    if path is not None:
        return load_json(path)

    source = profile_source("repository_catalog")
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "qselmer.github.io academic-profile-sync/3.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError("Canonical repository catalogue must be a JSON object")
    return payload


def select_repo(entry: dict, repo: dict, allowed_types: set[str]) -> dict:
    full_name = str(entry.get("repository") or "").strip()
    if not full_name:
        raise RuntimeError("Teaching registry entries require repository")
    if repo.get("private"):
        raise RuntimeError(f"Website teaching records must be public: {full_name}")
    if repo.get("archived"):
        raise RuntimeError(f"Website teaching records must be active: {full_name}")
    if repo.get("repository_type") not in allowed_types:
        raise RuntimeError(
            f"Incompatible repository type for {full_name}: "
            f"{repo.get('repository_type')} not in {sorted(allowed_types)}"
        )
    return {
        "name": repo.get("name", ""),
        "full_name": full_name,
        "html_url": repo.get("html_url", ""),
        "description": repo.get("description", ""),
        "language": repo.get("language", "—"),
        "updated_at": repo.get("updated_at", ""),
        "repository_type": repo.get("repository_type", ""),
        "repository_type_label": repo.get("repository_type_label", ""),
        "category": entry.get("category", ""),
        "maturity": entry.get("maturity", ""),
        "site_path": entry.get("site_path", ""),
        "summary": entry.get("summary", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        type=Path,
        help="Optional local canonical repository-catalog.json; avoids a second network fetch.",
    )
    args = parser.parse_args()

    registry = load_json(REGISTRY)
    catalog = load_catalog(args.catalog)
    repositories = catalog.get("repositories")
    if not isinstance(repositories, list):
        raise RuntimeError("Invalid repository catalogue: repositories must be a list")

    by_name = {
        str(repo.get("full_name") or "").strip(): repo
        for repo in repositories
        if str(repo.get("full_name") or "").strip()
    }

    teaching = []
    for entry in registry.get("published", []):
        full_name = str(entry.get("repository") or "").strip()
        repo = by_name.get(full_name)
        if repo is None:
            raise RuntimeError(f"Repository not found in canonical catalogue: {full_name}")
        teaching.append(select_repo(entry, repo, {"type-training"}))

    infrastructure = []
    for entry in registry.get("infrastructure", []):
        full_name = str(entry.get("repository") or "").strip()
        repo = by_name.get(full_name)
        if repo is None:
            raise RuntimeError(f"Repository not found in canonical catalogue: {full_name}")
        infrastructure.append(select_repo(entry, repo, {"type-template"}))

    source = profile_source("repository_catalog")
    payload = {
        "schema_version": 1,
        "source_repository": source["repository"],
        "source_path": source["path"],
        "catalog_updated_at": catalog.get("updated_at", ""),
        "count": len(teaching),
        "infrastructure_count": len(infrastructure),
        "teaching": teaching,
        "infrastructure": infrastructure,
    }

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if current == rendered:
        print(
            f"Teaching catalogue already synchronized "
            f"({len(teaching)} teaching, {len(infrastructure)} infrastructure)"
        )
    else:
        TARGET.write_text(rendered, encoding="utf-8")
        print(
            f"Synchronized {len(teaching)} teaching records and "
            f"{len(infrastructure)} infrastructure records"
        )


if __name__ == "__main__":
    main()
