#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from site_config import ROOT, profile_source

REGISTRY = ROOT / "software" / "registry.json"
TARGET = ROOT / "assets" / "data" / "software.json"


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

    selected = []
    for entry in registry.get("published", []):
        full_name = str(entry.get("repository") or "").strip()
        if not full_name:
            raise RuntimeError("Published software registry entries require repository")
        repo = by_name.get(full_name)
        if repo is None:
            raise RuntimeError(f"Repository not found in canonical catalogue: {full_name}")
        if repo.get("private"):
            raise RuntimeError(f"Published software must be public: {full_name}")
        if repo.get("archived"):
            raise RuntimeError(f"Published software must be active: {full_name}")
        if repo.get("repository_type") not in {"type-package", "type-app"}:
            raise RuntimeError(
                f"Published software has incompatible repository type: "
                f"{full_name} ({repo.get('repository_type')})"
            )

        selected.append(
            {
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
        )

    source = profile_source("repository_catalog")
    payload = {
        "schema_version": 1,
        "source_repository": source["repository"],
        "source_path": source["path"],
        "catalog_updated_at": catalog.get("updated_at", ""),
        "count": len(selected),
        "software": selected,
    }

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if current == rendered:
        print(f"Software catalogue already synchronized ({len(selected)} records)")
    else:
        TARGET.write_text(rendered, encoding="utf-8")
        print(f"Synchronized {len(selected)} software records")


if __name__ == "__main__":
    main()
