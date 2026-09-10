#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from site_config import ROOT, profile_source

REGISTRY = ROOT / "software" / "registry.json"
TARGET = ROOT / "assets" / "data" / "software.json"
API_ROOT = "https://api.github.com"


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
        headers={"User-Agent": "qselmer.github.io academic-profile-sync/4.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError("Canonical repository catalogue must be a JSON object")
    return payload


def github_token() -> str:
    return (
        os.environ.get("PROFILE_REPO_TOKEN", "").strip()
        or os.environ.get("GITHUB_TOKEN", "").strip()
    )


def github_headers(token: str, accept: str = "application/vnd.github+json") -> dict[str, str]:
    values = {
        "Accept": accept,
        "User-Agent": "qselmer.github.io software-metadata-sync/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        values["Authorization"] = f"Bearer {token}"
    return values


def optional_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers=github_headers(token))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {}
    return payload if isinstance(payload, dict) else {}


def optional_text(repository: str, branch: str, path: str, token: str) -> str:
    encoded = urllib.parse.quote(path, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = f"{API_ROOT}/repos/{repository}/contents/{encoded}?ref={ref}"
    request = urllib.request.Request(
        url,
        headers=github_headers(token, "application/vnd.github.raw+json"),
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return ""


def content_exists(repository: str, branch: str, path: str, token: str) -> bool:
    encoded = urllib.parse.quote(path, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = f"{API_ROOT}/repos/{repository}/contents/{encoded}?ref={ref}"
    return bool(optional_json(url, token))


def parse_description(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current = ""
    for raw in text.splitlines():
        if raw[:1].isspace() and current:
            fields[current] = f"{fields[current]} {raw.strip()}".strip()
            continue
        if ":" not in raw:
            current = ""
            continue
        key, value = raw.split(":", 1)
        current = key.strip()
        fields[current] = value.strip()
    return fields


def first_http_url(value: str) -> str:
    for candidate in re.split(r"[,\s]+", value or ""):
        candidate = candidate.strip()
        if candidate.startswith("https://") or candidate.startswith("http://"):
            return candidate
    return ""


def discover_metadata(full_name: str, category: str, curated: dict, token: str) -> dict[str, str]:
    repo_meta = optional_json(f"{API_ROOT}/repos/{full_name}", token)
    branch = str(repo_meta.get("default_branch") or "main")
    homepage = str(repo_meta.get("homepage") or "").strip()

    description_text = optional_text(full_name, branch, "DESCRIPTION", token) if category == "R package" else ""
    description = parse_description(description_text) if description_text else {}

    version = str(description.get("Version") or curated.get("version") or "").strip()
    documentation = homepage or first_http_url(str(description.get("URL") or "")) or str(curated.get("documentation") or "").strip()

    check_url = ""
    if category == "R package":
        for workflow in (
            ".github/workflows/R-CMD-check.yaml",
            ".github/workflows/R-CMD-check.yml",
            ".github/workflows/check-standard.yaml",
            ".github/workflows/check-standard.yml",
        ):
            if content_exists(full_name, branch, workflow, token):
                check_url = f"https://github.com/{full_name}/actions/workflows/{Path(workflow).name}"
                break
        if not check_url:
            check_url = str(curated.get("r_cmd_check") or "").strip()

    release = optional_json(f"{API_ROOT}/repos/{full_name}/releases/latest", token)
    latest_release = str(release.get("tag_name") or "").strip()
    latest_release_url = str(release.get("html_url") or "").strip()

    citation = optional_text(full_name, branch, "CITATION.cff", token)
    doi = ""
    if citation:
        match = re.search(r"(?im)^\s*doi\s*:\s*['\"]?([^'\"\s]+)", citation)
        if match:
            doi = match.group(1).strip()

    result = {
        "default_branch": branch,
        "version": version,
        "documentation": documentation,
        "r_cmd_check": check_url,
        "latest_release": latest_release,
        "latest_release_url": latest_release_url,
        "doi": doi,
        "application": str(curated.get("application") or "").strip(),
    }
    return {key: value for key, value in result.items() if value}


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

    token = github_token()
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

        category = str(entry.get("category") or "")
        item = {
            "name": repo.get("name", ""),
            "full_name": full_name,
            "html_url": repo.get("html_url", ""),
            "description": repo.get("description", ""),
            "language": repo.get("language", "-"),
            "updated_at": repo.get("updated_at", ""),
            "repository_type": repo.get("repository_type", ""),
            "repository_type_label": repo.get("repository_type_label", ""),
            "category": category,
            "maturity": entry.get("maturity", ""),
            "site_path": entry.get("site_path", ""),
            "summary": entry.get("summary", ""),
        }
        item.update(discover_metadata(full_name, category, entry, token))
        selected.append(item)

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
        print(f"Synchronized {len(selected)} software records with repository metadata")


if __name__ == "__main__":
    main()
