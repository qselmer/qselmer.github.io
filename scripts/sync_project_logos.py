#!/usr/bin/env python3
"""Mirror canonical project logos from their source repositories.

The source repository remains authoritative. This script copies only an existing
canonical ``assets/images/logo.svg`` or ``assets/images/logo.png`` into the
website's ``images/projects/<slug>/`` directory. It never generates substitute
artwork.

Private cross-repository reads require a token with read access to the source
repositories. Token preference is PROJECT_REPO_TOKEN, PROFILE_REPO_TOKEN, then
GITHUB_TOKEN.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from site_config import ROOT

REGISTRY = ROOT / "projects" / "registry.json"
TARGET_ROOT = ROOT / "images" / "projects"
API_ROOT = "https://api.github.com"
SUPPORTED_NAMES = ("logo.svg", "logo.png")


def load_registry() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RuntimeError("projects/registry.json must use schema_version 1")
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise RuntimeError("projects/registry.json must contain a projects list")
    return payload


def cross_repository_token() -> str:
    for name in ("PROJECT_REPO_TOKEN", "PROFILE_REPO_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def token() -> str:
    cross_repo = cross_repository_token()
    if cross_repo:
        return cross_repo
    return os.environ.get("GITHUB_TOKEN", "").strip()


def request_json(url: str, auth_token: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "qselmer.github.io project-logo-sync/1.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected GitHub API response for {url}")
    return payload


def repository_accessible(repository: str, auth_token: str) -> bool:
    url = f"{API_ROOT}/repos/{repository}"
    try:
        request_json(url, auth_token)
        return True
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403, 404}:
            return False
        raise


def fetch_candidate(
    repository: str,
    branch: str,
    source_path: str,
    auth_token: str,
) -> bytes | None:
    encoded_path = urllib.parse.quote(source_path, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = f"{API_ROOT}/repos/{repository}/contents/{encoded_path}?ref={ref}"
    try:
        payload = request_json(url, auth_token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

    if payload.get("type") != "file":
        raise RuntimeError(f"Configured logo candidate is not a file: {repository}:{source_path}")
    if payload.get("encoding") != "base64" or not payload.get("content"):
        raise RuntimeError(f"GitHub did not return base64 logo content: {repository}:{source_path}")
    return base64.b64decode(str(payload["content"]).encode("ascii"), validate=False)


def remove_stale(target_dir: Path, keep_name: str | None = None) -> bool:
    changed = False
    for name in SUPPORTED_NAMES:
        path = target_dir / name
        if name != keep_name and path.exists():
            path.unlink()
            changed = True
    return changed


def sync_project(project: dict, auth_token: str) -> tuple[str, bool, str]:
    slug = str(project.get("slug") or "").strip()
    repository = str(project.get("source_repository") or "").strip()
    branch = str(project.get("source_branch") or "main").strip()
    candidates = project.get("logo_candidates") or []

    if not slug or not repository:
        raise RuntimeError(f"Project registry entry lacks slug/source_repository: {project}")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError(f"Project {slug} has no logo_candidates")

    target_dir = TARGET_ROOT / slug

    if not repository_accessible(repository, auth_token):
        return (
            f"SKIP {slug}: source repository is not accessible with the configured token",
            False,
            "inaccessible",
        )

    for source_path_raw in candidates:
        source_path = str(source_path_raw).strip()
        suffix = Path(source_path).suffix.lower()
        if suffix not in {".svg", ".png"}:
            raise RuntimeError(f"Unsupported project logo extension for {slug}: {source_path}")

        content = fetch_candidate(repository, branch, source_path, auth_token)
        if content is None:
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        target_name = f"logo{suffix}"
        target = target_dir / target_name
        changed = not target.exists() or target.read_bytes() != content
        if changed:
            target.write_bytes(content)
        changed = remove_stale(target_dir, keep_name=target_name) or changed
        return (
            f"SYNC {slug}: {repository}/{source_path} -> {target.relative_to(ROOT)}",
            changed,
            "synced",
        )

    changed = False
    if target_dir.exists():
        changed = remove_stale(target_dir)
        try:
            target_dir.rmdir()
        except OSError:
            pass
    return (
        f"EMPTY {slug}: no canonical logo exists in the source repository",
        changed,
        "missing",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fail-on-inaccessible",
        action="store_true",
        help="Fail when a configured source repository cannot be read.",
    )
    args = parser.parse_args()

    payload = load_registry()
    auth_token = token()
    cross_repo_auth = bool(cross_repository_token())

    if not cross_repo_auth:
        print(
            "WARNING: PROJECT_REPO_TOKEN/PROFILE_REPO_TOKEN is not configured. "
            "The repository GITHUB_TOKEN cannot read unrelated private repositories.",
            file=sys.stderr,
        )

    changed_any = False
    counts = {"synced": 0, "missing": 0, "inaccessible": 0}
    for project in payload["projects"]:
        message, changed, status = sync_project(project, auth_token)
        print(message)
        changed_any = changed_any or changed
        counts[status] += 1

    print(
        "Project logo summary: "
        f"{counts['synced']} source logo(s) available; "
        f"{counts['missing']} source repository/repositories without a canonical logo; "
        f"{counts['inaccessible']} inaccessible source repository/repositories."
    )

    if counts["inaccessible"]:
        print(
            "ACTION REQUIRED: configure PROFILE_REPO_TOKEN (or PROJECT_REPO_TOKEN) "
            "with read access to the private source repositories.",
            file=sys.stderr,
        )
        if args.fail_on_inaccessible:
            raise SystemExit(2)

    print("Project logo mirrors updated." if changed_any else "Project logo mirrors already synchronized or unavailable.")


if __name__ == "__main__":
    main()
