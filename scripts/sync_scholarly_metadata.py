#!/usr/bin/env python3
"""Synchronize citation, release, and reproducibility metadata for approved public repositories."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from site_config import ROOT

GRAPH_REGISTRY = ROOT / "graph" / "registry.json"
TARGET = ROOT / "assets" / "data" / "repository-scholarly-metadata.json"
API = "https://api.github.com/repos"
ORCID = "0000-0001-9229-6379"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def request_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "qselmer.github.io scholarly-metadata-sync/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def optional_json(url: str) -> Any | None:
    try:
        return request_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def decoded_content(item: dict[str, Any] | None) -> str:
    if not item or item.get("type") != "file":
        return ""
    content = str(item.get("content") or "")
    if item.get("encoding") == "base64" and content:
        return base64.b64decode(content).decode("utf-8", errors="replace")
    return content


def infer_license(repo_meta: dict[str, Any], license_text: str) -> str:
    license_meta = repo_meta.get("license") or {}
    spdx = str(license_meta.get("spdx_id") or "").strip()
    if spdx and spdx != "NOASSERTION":
        return spdx
    first = license_text.lstrip().splitlines()[0].strip() if license_text.strip() else ""
    if first.casefold() == "mit license":
        return "MIT"
    return ""


def canonical_doi(value: str) -> str:
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.I)
    return text.rstrip(".,;)")


def doi_from_cff(text: str) -> str:
    for pattern in (
        r"(?mi)^doi:\s*[\"']?([^\s\"']+)",
        r"https?://doi\.org/([^\s\"']+)",
    ):
        match = re.search(pattern, text)
        if match:
            return canonical_doi(match.group(1))
    return ""


def repository_record(full_name: str) -> dict[str, Any]:
    meta = request_json(f"{API}/{full_name}")
    if meta.get("private"):
        raise RuntimeError(f"Private repository entered public scholarly metadata sync: {full_name}")
    branch = str(meta.get("default_branch") or "main")
    root = request_json(f"{API}/{full_name}/contents?ref={branch}")
    if not isinstance(root, list):
        raise RuntimeError(f"Unexpected repository root payload for {full_name}")
    names = {str(item.get("name") or "") for item in root}

    citation_item = optional_json(f"{API}/{full_name}/contents/CITATION.cff?ref={branch}")
    citation_text = decoded_content(citation_item if isinstance(citation_item, dict) else None)
    license_item = optional_json(f"{API}/{full_name}/contents/LICENSE?ref={branch}")
    license_text = decoded_content(license_item if isinstance(license_item, dict) else None)
    workflows = optional_json(f"{API}/{full_name}/contents/.github/workflows?ref={branch}") if ".github" in names else None
    latest_release = optional_json(f"{API}/{full_name}/releases/latest")

    environment_names = {
        "requirements.txt", "requirements-dev.txt", "requirements-regulatory.txt",
        "pyproject.toml", "environment.yml", "environment.yaml", "renv.lock",
        "DESCRIPTION", "Pipfile", "poetry.lock", "environment",
    }
    changelog_names = {"CHANGELOG", "CHANGELOG.md", "NEWS", "NEWS.md"}
    citation = bool(citation_text)
    release_tag = str((latest_release or {}).get("tag_name") or "") if isinstance(latest_release, dict) else ""
    return {
        "repository": full_name,
        "url": str(meta.get("html_url") or f"https://github.com/{full_name}"),
        "default_branch": branch,
        "updated_at": str(meta.get("updated_at") or ""),
        "readme": any(name.casefold().startswith("readme") for name in names),
        "license_file": "LICENSE" in names or "LICENSE.md" in names,
        "license_spdx": infer_license(meta, license_text),
        "citation_cff": citation,
        "citation_orcid": citation and ORCID in citation_text,
        "codemeta": "codemeta.json" in names,
        "tests": "tests" in names or "test" in names,
        "ci": isinstance(workflows, list) and len(workflows) > 0,
        "environment": bool(names & environment_names),
        "changelog": bool(names & changelog_names),
        "release": bool(release_tag),
        "release_tag": release_tag,
        "archival_doi": doi_from_cff(citation_text),
        "zenodo_metadata": ".zenodo.json" in names,
    }


def build_payload() -> dict[str, Any]:
    registry = load_json(GRAPH_REGISTRY)
    repositories = [str(x).strip() for x in registry.get("public_repositories") or [] if str(x).strip()]
    if not repositories:
        raise RuntimeError("graph/registry.json has no public_repositories")
    records = [repository_record(name) for name in repositories]
    records.sort(key=lambda item: item["repository"].casefold())
    timestamps = [str(item.get("updated_at") or "") for item in records if item.get("updated_at")]
    return {
        "schema_version": 1,
        "source_updated_at": max(timestamps) if timestamps else "",
        "source": "GitHub public API; repositories approved by graph/registry.json",
        "repositories": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the committed mirror differs from live public repository metadata.")
    args = parser.parse_args()
    expected = json.dumps(build_payload(), ensure_ascii=False, indent=2) + "\n"
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if args.check:
        if current != expected:
            raise SystemExit("repository scholarly metadata is stale; run python scripts/sync_scholarly_metadata.py")
        print("Repository scholarly metadata is current.")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
