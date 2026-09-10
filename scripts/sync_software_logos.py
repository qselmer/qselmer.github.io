#!/usr/bin/env python3
"""Mirror canonical software logos from public source repositories.

The source repository remains authoritative. Common R-package and project logo
locations are checked in order, and any existing canonical SVG or PNG is copied
unchanged into images/software/<name>/. No substitute artwork is generated.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from site_config import ROOT

DATA = ROOT / "assets" / "data" / "software.json"
TARGET_ROOT = ROOT / "images" / "software"
API_ROOT = "https://api.github.com"
CANDIDATES = (
    "man/figures/logo.svg",
    "man/figures/logo.png",
    "assets/images/logo.svg",
    "assets/images/logo.png",
    "logo.svg",
    "logo.png",
)
SUPPORTED = ("logo.svg", "logo.png")


def auth_token() -> str:
    return (
        os.environ.get("PROFILE_REPO_TOKEN", "").strip()
        or os.environ.get("GITHUB_TOKEN", "").strip()
    )


def headers(token: str, accept: str = "application/vnd.github+json") -> dict[str, str]:
    values = {
        "Accept": accept,
        "User-Agent": "qselmer.github.io software-logo-sync/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        values["Authorization"] = f"Bearer {token}"
    return values


def request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers=headers(token))
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected GitHub API response for {url}")
    return payload


def request_bytes(url: str, token: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers=headers(token, "application/vnd.github.raw+json"),
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_file(repository: str, branch: str, path: str, token: str) -> bytes | None:
    encoded = urllib.parse.quote(path, safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = f"{API_ROOT}/repos/{repository}/contents/{encoded}?ref={ref}"
    try:
        payload = request_json(url, token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if payload.get("type") != "file":
        return None
    content = payload.get("content")
    if payload.get("encoding") == "base64" and content:
        return base64.b64decode(str(content).encode("ascii"), validate=False)
    return request_bytes(url, token)


def remove_stale(directory: Path, keep: str | None = None) -> bool:
    changed = False
    for name in SUPPORTED:
        path = directory / name
        if name != keep and path.exists():
            path.unlink()
            changed = True
    return changed


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    items = payload.get("software")
    if not isinstance(items, list):
        raise RuntimeError("assets/data/software.json must contain a software list")

    token = auth_token()
    for item in items:
        name = str(item.get("name") or "").strip()
        repository = str(item.get("full_name") or "").strip()
        if not name or not repository:
            raise RuntimeError(f"Software record lacks name/full_name: {item}")

        repo_meta = request_json(f"{API_ROOT}/repos/{repository}", token)
        branch = str(repo_meta.get("default_branch") or "main")
        directory = TARGET_ROOT / name
        found = False
        for candidate in CANDIDATES:
            content = fetch_file(repository, branch, candidate, token)
            if content is None:
                continue
            suffix = Path(candidate).suffix.lower()
            target_name = f"logo{suffix}"
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / target_name
            changed = not target.exists() or target.read_bytes() != content
            if changed:
                target.write_bytes(content)
            remove_stale(directory, target_name)
            print(f"SYNC {name}: {repository}/{candidate} -> {target.relative_to(ROOT)}")
            found = True
            break

        if not found:
            if directory.exists():
                remove_stale(directory)
                try:
                    directory.rmdir()
                except OSError:
                    pass
            print(f"EMPTY {name}: no canonical software logo found")


if __name__ == "__main__":
    main()
