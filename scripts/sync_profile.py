#!/usr/bin/env python3
"""Synchronize canonical academic-profile metadata and rebuild site derivatives."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from site_config import ROOT, profile_source


def run_script(name: str, *args: str) -> None:
    command = [sys.executable, str(ROOT / "scripts" / name), *args]
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def fetch_repository_catalog(target: Path) -> None:
    source = profile_source("repository_catalog")
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "qselmer.github.io academic-profile-sync/4.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        raise RuntimeError("Invalid repository catalogue: repositories must be a list")
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Fetched canonical repository catalogue ({len(repositories)} records) for in-memory derivation")


def main() -> None:
    # Public mirrors that are safe to persist in the website repository.
    run_script("sync_publications.py")
    run_script("sync_metrics.py")

    # The canonical repository catalogue can contain private-repository metadata.
    # Fetch it once to a temporary file and derive only the curated public subsets.
    with tempfile.TemporaryDirectory(prefix="qselmer-profile-") as tmp:
        catalog_path = Path(tmp) / "repository-catalog.json"
        fetch_repository_catalog(catalog_path)
        run_script("sync_software.py", "--catalog", str(catalog_path))
        run_script("sync_teaching.py", "--catalog", str(catalog_path))

    # Phase 9 audits only repositories that are explicitly approved as public.
    run_script("sync_scholarly_metadata.py")

    # Canonical artwork is mirrored unchanged from its source repositories.
    run_script("sync_project_logos.py", "--fail-on-inaccessible")
    run_script("sync_software_logos.py")

    # Deterministic presentation and relationship layers.
    for script in (
        "build_publications.py",
        "build_conferences.py",
        "build_software.py",
        "build_teaching.py",
        "build_data_resources.py",
        "build_blog.py",
        "build_research_graph.py",
        "build_scholarly_graph.py",
        "build_scholarly_infrastructure.py",
        "build_projects.py",
        "build_home.py",
    ):
        run_script(script)

    run_script("validate_site.py", "source")
    run_script("validate_phase7.py", "source")
    run_script("validate_phase9.py", "source")
    print("Academic profile synchronization complete")


if __name__ == "__main__":
    main()
