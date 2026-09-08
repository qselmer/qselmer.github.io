#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "software" / "registry.json"
TARGET = ROOT / "assets" / "data" / "software.json"
SOURCE_URL = "https://raw.githubusercontent.com/qselmer/qselmer/main/assets/data/repository-catalog.json"


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def main() -> None:
    registry = load_json(REGISTRY)
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "qselmer-website-software-sync/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        catalog = json.load(response)

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

    payload = {
        "schema_version": 1,
        "source_repository": "qselmer/qselmer",
        "source_path": "assets/data/repository-catalog.json",
        "catalog_updated_at": catalog.get("updated_at", ""),
        "count": len(selected),
        "software": selected,
    }

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Synchronized {len(selected)} software records")


if __name__ == "__main__":
    main()
