#!/usr/bin/env python3
"""Build Phase 10 reproducibility certification outputs from verified public evidence."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from site_config import ROOT

POLICY = ROOT / "certification" / "registry.json"
GRAPH_POLICY = ROOT / "graph" / "registry.json"
REPOSITORIES = ROOT / "assets" / "data" / "repository-scholarly-metadata.json"
TARGET = ROOT / "assets" / "data" / "reproducibility-certification.json"
FRAGMENT = ROOT / "reproducibility" / "_generated.md"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def slug_repo(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def level_for(record: dict[str, Any]) -> int:
    level = 0
    if record.get("readme"):
        level = 1
    level2 = (
        bool(record.get("readme"))
        and bool(record.get("license_file"))
        and bool(record.get("citation_cff"))
        and bool(record.get("tests") or record.get("environment"))
    )
    if level2:
        level = 2
    if level2 and record.get("ci"):
        level = 3
    if level >= 3 and record.get("release") and str(record.get("archival_doi") or "").strip():
        level = 4
    if level >= 4 and record.get("research_object"):
        level = 5
    return level


def next_actions(record: dict[str, Any], level: int) -> list[str]:
    actions: list[str] = []
    if level < 2:
        if not record.get("license_file"):
            actions.append("add an explicit license")
        if not record.get("citation_cff"):
            actions.append("add CITATION.cff")
        if not (record.get("tests") or record.get("environment")):
            actions.append("document a computational environment or add tests")
    elif level == 2:
        if not record.get("ci"):
            actions.append("add continuous integration")
    elif level == 3:
        if not record.get("release"):
            actions.append("create a versioned release")
        if not str(record.get("archival_doi") or "").strip():
            actions.append("archive a stable release and register a DOI")
    elif level == 4:
        actions.append("publish a bounded machine-readable research object with provenance")

    if record.get("citation_cff") and not record.get("citation_orcid"):
        actions.append("add ORCID to CITATION.cff")
    if not record.get("codemeta"):
        actions.append("add CodeMeta metadata when useful")
    if record.get("release") and not record.get("zenodo_metadata"):
        actions.append("link release preservation metadata when archived")
    return actions


def build_payload() -> dict[str, Any]:
    policy = load_json(POLICY)
    graph_policy = load_json(GRAPH_POLICY)
    repository_payload = load_json(REPOSITORIES)

    if policy.get("schema_version") != 1 or policy.get("phase") != 10:
        raise RuntimeError("certification/registry.json must define Phase 10 schema_version 1")
    approved = [str(x).strip() for x in graph_policy.get("public_repositories") or [] if str(x).strip()]
    if not approved:
        raise RuntimeError("Phase 10 requires the Phase 7 public repository allowlist")

    raw_records = repository_payload.get("repositories") or []
    by_name = {str(item.get("repository") or "").strip(): item for item in raw_records if isinstance(item, dict)}
    missing = [name for name in approved if name not in by_name]
    if missing:
        raise RuntimeError("Missing verified scholarly metadata for: " + ", ".join(missing))
    extras = sorted(set(by_name) - set(approved))
    if extras:
        raise RuntimeError("Repository scholarly metadata exceeds public allowlist: " + ", ".join(extras))

    certified_from = int((policy.get("policy") or {}).get("certified_from_level", 2))
    prefix = str((policy.get("policy") or {}).get("certificate_prefix") or "QS-RC1")
    level_labels = {
        int(item["level"]): str(item["label"])
        for item in policy.get("levels") or []
        if isinstance(item, dict) and "level" in item and "label" in item
    }

    records: list[dict[str, Any]] = []
    for name in approved:
        evidence = by_name[name]
        level = level_for(evidence)
        certified = level >= certified_from
        signals = {
            "readme": bool(evidence.get("readme")),
            "license": bool(evidence.get("license_file")),
            "citation_cff": bool(evidence.get("citation_cff")),
            "citation_orcid": bool(evidence.get("citation_orcid")),
            "tests": bool(evidence.get("tests")),
            "environment": bool(evidence.get("environment")),
            "ci": bool(evidence.get("ci")),
            "release": bool(evidence.get("release")),
            "archival_doi": bool(str(evidence.get("archival_doi") or "").strip()),
            "codemeta": bool(evidence.get("codemeta")),
            "zenodo_metadata": bool(evidence.get("zenodo_metadata")),
        }
        records.append({
            "repository": name,
            "url": str(evidence.get("url") or f"https://github.com/{name}"),
            "certificate_id": f"{prefix}-{slug_repo(name)}",
            "status": "certified" if certified else "not-certified",
            "level": level,
            "level_label": level_labels.get(level, str(level)),
            "assessed_at": str(repository_payload.get("generated_at") or ""),
            "evidence": signals,
            "release_tag": str(evidence.get("release_tag") or ""),
            "archival_doi": str(evidence.get("archival_doi") or ""),
            "next_actions": next_actions(evidence, level),
        })

    records.sort(key=lambda item: (-int(item["level"]), item["repository"].casefold()))
    counts = Counter(item["status"] for item in records)
    levels = Counter(int(item["level"]) for item in records)
    return {
        "schema_version": 1,
        "phase": 10,
        "title": str(policy.get("title") or "Reproducibility Certification"),
        "assessment_type": "internal technical self-certification",
        "external_accreditation": False,
        "scientific_quality_claim": False,
        "evidence_source": "assets/data/repository-scholarly-metadata.json",
        "public_repository_scope": approved,
        "certified_from_level": certified_from,
        "summary": {
            "repositories_assessed": len(records),
            "certified": counts.get("certified", 0),
            "not_certified": counts.get("not-certified", 0),
            "levels": {str(k): v for k, v in sorted(levels.items())},
        },
        "levels": policy.get("levels") or [],
        "records": records,
        "policy": policy.get("policy") or {},
    }


def render(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "<!-- Generated by scripts/build_reproducibility_certification.py; do not edit manually. -->",
        "",
        "This page reports an **internal technical self-certification** of approved public repositories. It is not external accreditation and it does not assess scientific validity, novelty, or inferential quality.",
        "",
        f"Repositories assessed: **{summary['repositories_assessed']}** · certified at Level {payload['certified_from_level']} or above: **{summary['certified']}** · below certification threshold: **{summary['not_certified']}**.",
        "",
        "## Certification records",
        "",
        "| Repository | Status | Level | Certification ID | Next priority |",
        "|---|---|---:|---|---|",
    ]
    for item in payload["records"]:
        status = "Certified" if item["status"] == "certified" else "Not certified"
        next_priority = item["next_actions"][0] if item["next_actions"] else "No blocking action recorded"
        lines.append(
            f"| [{html.escape(item['repository'])}]({html.escape(item['url'], quote=True)}) | {status} | {item['level']} - {html.escape(item['level_label'])} | `{html.escape(item['certificate_id'])}` | {html.escape(next_priority)} |"
        )

    lines += [
        "",
        "## Certification standard",
        "",
    ]
    for item in payload["levels"]:
        req = "; ".join(str(x) for x in item.get("requirements") or [])
        lines.append(f"- **Level {item['level']} - {html.escape(str(item['label']))}:** {html.escape(req)}.")

    lines += [
        "",
        "## Remediation queue",
        "",
        "The queue is generated from missing evidence. It deliberately does not create licenses, DOIs, releases, or archive records automatically where those require a scientific or legal decision.",
        "",
    ]
    for item in payload["records"]:
        if not item["next_actions"]:
            continue
        actions = "; ".join(item["next_actions"])
        lines.append(f"- **{html.escape(item['repository'])}:** {html.escape(actions)}.")

    lines += [
        "",
        "## Machine-readable record",
        "",
        "The complete assessment is published as [`reproducibility-certification.json`](/assets/data/reproducibility-certification.json). Every certification record is derived from the Phase 9 verified public-repository evidence layer and the Phase 7 public allowlist.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    expected_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    expected_md = render(payload)

    if args.check:
        stale: list[str] = []
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != expected_json:
            stale.append(str(TARGET.relative_to(ROOT)))
        if not FRAGMENT.exists() or FRAGMENT.read_text(encoding="utf-8") != expected_md:
            stale.append(str(FRAGMENT.relative_to(ROOT)))
        if stale:
            raise SystemExit("Phase 10 generated outputs are stale: " + ", ".join(stale))
        print("Phase 10 reproducibility certification outputs are synchronized.")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected_json, encoding="utf-8")
    FRAGMENT.write_text(expected_md, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    print(f"Wrote {FRAGMENT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
