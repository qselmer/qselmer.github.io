#!/usr/bin/env python3
"""Shared configuration helpers for the Quarto academic website."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "site.json"


def load_config() -> dict[str, Any]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("config/site.json must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported config/site.json schema_version")
    return payload


def profile_source(key: str) -> dict[str, str]:
    config = load_config()
    profile = config.get("canonical_profile", {})
    sources = profile.get("sources", {})
    path = str(sources.get(key) or "").strip()
    repository = str(profile.get("repository") or "").strip()
    branch = str(profile.get("branch") or "").strip()
    if not path or not repository or not branch:
        raise RuntimeError(f"Canonical profile source is not configured for {key!r}")
    return {
        "repository": repository,
        "branch": branch,
        "path": path,
        "url": f"https://raw.githubusercontent.com/{repository}/{branch}/{path}",
    }


def synchronized_artifacts() -> list[str]:
    config = load_config()
    paths = config.get("synchronized_artifacts", [])
    if not isinstance(paths, list) or not all(isinstance(x, str) and x.strip() for x in paths):
        raise RuntimeError("synchronized_artifacts must be a non-empty list of paths")
    return [x.strip() for x in paths]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("tracked", "source-url"))
    parser.add_argument("key", nargs="?")
    args = parser.parse_args()

    if args.command == "tracked":
        for path in synchronized_artifacts():
            print(path)
        return

    if not args.key:
        parser.error("source-url requires a source key")
    print(profile_source(args.key)["url"])


if __name__ == "__main__":
    main()
