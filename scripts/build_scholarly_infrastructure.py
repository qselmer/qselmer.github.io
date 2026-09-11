#!/usr/bin/env python3
"""Build Phase 9 scholarly visibility, interoperability, and preservation outputs."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from site_config import ROOT

SITE_URL = "https://qselmer.github.io"
CONFIG = ROOT / "config" / "site.json"
REGISTRY = ROOT / "scholarly" / "registry.json"
METRICS = ROOT / "assets" / "data" / "research-metrics.json"
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
SOFTWARE = ROOT / "assets" / "data" / "software.json"
TEACHING = ROOT / "assets" / "data" / "teaching.json"
REPOSITORIES = ROOT / "assets" / "data" / "repository-scholarly-metadata.json"
GRAPH = ROOT / "assets" / "data" / "scholarly-graph.json"
TARGET = ROOT / "assets" / "data" / "scholarly-infrastructure.json"
FRAGMENT = ROOT / "open-science" / "_generated.md"

FORMAL_CATEGORIES = {
    "Journal articles",
    "Preprints & working papers",
    "Books & chapters",
    "Theses",
    "Reports & technical outputs",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def role_map(software: dict[str, Any], teaching: dict[str, Any], graph: dict[str, Any]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for item in software.get("software") or []:
        full_name = str(item.get("full_name") or "").strip()
        if full_name:
            roles[full_name] = "Software"
    for key in ("teaching", "infrastructure"):
        for item in teaching.get(key) or []:
            full_name = str(item.get("full_name") or "").strip()
            if full_name:
                roles[full_name] = "Teaching"
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict) or node.get("kind") != "Repository":
            continue
        full_name = str(node.get("full_name") or "").strip()
        if full_name and full_name not in roles:
            roles[full_name] = "Project"
    return roles


def readiness(record: dict[str, Any]) -> tuple[int, list[str]]:
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

    gaps: list[str] = []
    if not record.get("license_file"):
        gaps.append("license")
    if not record.get("citation_cff"):
        gaps.append("CITATION.cff")
    elif not record.get("citation_orcid"):
        gaps.append("ORCID in citation metadata")
    if not record.get("codemeta"):
        gaps.append("CodeMeta")
    if not record.get("ci"):
        gaps.append("CI")
    if not record.get("release"):
        gaps.append("versioned release")
    if not str(record.get("archival_doi") or "").strip():
        gaps.append("archival DOI")
    return level, gaps


def build_payload() -> dict[str, Any]:
    config = load_json(CONFIG)
    registry = load_json(REGISTRY)
    metrics = load_json(METRICS)
    publications = load_json(PUBLICATIONS)
    software = load_json(SOFTWARE)
    teaching = load_json(TEACHING)
    repo_metadata = load_json(REPOSITORIES)
    graph = load_json(GRAPH)

    if registry.get("schema_version") != 1:
        raise RuntimeError("scholarly/registry.json must use schema_version 1")
    if repo_metadata.get("schema_version") != 1:
        raise RuntimeError("repository-scholarly-metadata.json must use schema_version 1")

    identity = config.get("identity") or {}
    affiliation = identity.get("affiliation") or {}
    openalex = metrics.get("openalex") or {}
    person = {
        "name": str(identity.get("name") or ""),
        "orcid": f"https://orcid.org/{identity.get('orcid', '')}",
        "openalex": str(openalex.get("author_id") or ""),
        "google_scholar": str(identity.get("google_scholar") or ""),
        "web_of_science": str(identity.get("web_of_science") or ""),
        "github": str(identity.get("github") or ""),
    }

    works = publications.get("publications") or []
    formal = [item for item in works if str(item.get("output_category") or "") in FORMAL_CATEGORIES]
    formal_with_doi = [item for item in formal if str(item.get("doi") or "").strip()]
    all_with_doi = [item for item in works if str(item.get("doi") or "").strip()]

    roles = role_map(software, teaching, graph)
    repository_records: list[dict[str, Any]] = []
    for record in repo_metadata.get("repositories") or []:
        if not isinstance(record, dict):
            raise RuntimeError("Every repository scholarly metadata record must be an object")
        name = str(record.get("repository") or "").strip()
        if not name:
            raise RuntimeError("Repository scholarly metadata record is missing repository")
        level, gaps = readiness(record)
        repository_records.append({
            "repository": name,
            "url": str(record.get("url") or f"https://github.com/{name}"),
            "role": roles.get(name, "Repository"),
            "readiness_level": level,
            "readiness_label": next(
                (str(item.get("label") or "") for item in registry.get("reproducibility_levels") or [] if item.get("level") == level),
                str(level),
            ),
            "citation_cff": bool(record.get("citation_cff")),
            "citation_orcid": bool(record.get("citation_orcid")),
            "codemeta": bool(record.get("codemeta")),
            "license": str(record.get("license_spdx") or ""),
            "tests": bool(record.get("tests")),
            "ci": bool(record.get("ci")),
            "environment": bool(record.get("environment")),
            "release": str(record.get("release_tag") or "") if record.get("release") else "",
            "archival_doi": str(record.get("archival_doi") or ""),
            "gaps": gaps,
        })
    repository_records.sort(key=lambda item: (item["role"], item["repository"].casefold()))

    level_counts = Counter(item["readiness_level"] for item in repository_records)
    return {
        "schema_version": 1,
        "phase": 9,
        "title": "Scholarly Visibility, Interoperability & Preservation",
        "public_only": True,
        "identity": person,
        "affiliation": {
            "name": str(affiliation.get("name") or ""),
            "acronym": str(affiliation.get("acronym") or ""),
            "url": str(affiliation.get("url") or ""),
            "ror": str(affiliation.get("ror") or ""),
            "verification_source": str((registry.get("affiliation_evidence") or {}).get("verification_source") or ""),
        },
        "identifier_coverage": {
            "profile_outputs": len(works),
            "profile_outputs_with_doi": len(all_with_doi),
            "formal_outputs": len(formal),
            "formal_outputs_with_doi": len(formal_with_doi),
        },
        "repositories": repository_records,
        "readiness_distribution": {str(level): count for level, count in sorted(level_counts.items())},
        "standards": registry.get("standards") or {},
        "reproducibility_levels": registry.get("reproducibility_levels") or [],
        "machine_interfaces": [
            SITE_URL + "/assets/data/scholarly-graph.json",
            SITE_URL + "/assets/data/scholarly-infrastructure.json",
        ],
        "source_contract": {
            "identity": "config/site.json + assets/data/research-metrics.json",
            "outputs": "assets/data/publications.json",
            "repository_evidence": "assets/data/repository-scholarly-metadata.json",
            "policy": "scholarly/registry.json",
            "no_identifier_invention": True,
        },
    }


def yn(value: bool) -> str:
    return "Yes" if value else "No"


def render(payload: dict[str, Any]) -> str:
    identity = payload["identity"]
    affiliation = payload["affiliation"]
    coverage = payload["identifier_coverage"]
    repositories = payload["repositories"]
    lines = [
        "<!-- Generated by scripts/build_scholarly_infrastructure.py; do not edit manually. -->",
        "",
        "## Persistent identity",
        "",
        "This site uses persistent scholarly identifiers only when they have been verified. It does not generate placeholder DOIs, ROR IDs, or archive records.",
        "",
        f"- **Researcher:** [{html.escape(identity['name'])}]({SITE_URL}/)",
        f"- **ORCID:** [{html.escape(identity['orcid'])}]({html.escape(identity['orcid'], quote=True)})",
        f"- **OpenAlex:** [{html.escape(identity['openalex'])}]({html.escape(identity['openalex'], quote=True)})" if identity.get("openalex") else "",
        f"- **Affiliation:** {html.escape(affiliation['name'])} ({html.escape(affiliation['acronym'])})",
        f"- **ROR:** [{html.escape(affiliation['ror'])}]({html.escape(affiliation['ror'], quote=True)})",
        "",
        "## Identifier coverage",
        "",
        f"Formal scholarly outputs with a DOI: **{coverage['formal_outputs_with_doi']} / {coverage['formal_outputs']}**. Across all ORCID-profile outputs mirrored by the site, **{coverage['profile_outputs_with_doi']} / {coverage['profile_outputs']}** currently carry a DOI.",
        "",
        "DOI coverage is reported as observed metadata, not as a quality score. Conference contributions and works without an assigned DOI remain valid scholarly outputs.",
        "",
        "## Repository readiness",
        "",
        "The table below is generated from public repository metadata. The readiness level is an internal reproducibility diagnostic; it is not a claim of scientific quality.",
        "",
        "| Repository | Role | Level | Citation | License | CI | Release | Archive DOI |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for item in repositories:
        repo = html.escape(item["repository"])
        url = html.escape(item["url"], quote=True)
        citation = "CFF" if item["citation_cff"] else "-"
        if item["citation_cff"] and item["citation_orcid"]:
            citation = "CFF + ORCID"
        license_value = html.escape(item["license"] or "-")
        release = html.escape(item["release"] or "-")
        doi = html.escape(item["archival_doi"] or "-")
        lines.append(
            f"| [{repo}]({url}) | {html.escape(item['role'])} | {item['readiness_level']} | {citation} | {license_value} | {yn(item['ci'])} | {release} | {doi} |"
        )
    lines += [
        "",
        "## Reproducibility scale",
        "",
    ]
    for item in payload["reproducibility_levels"]:
        lines.append(f"- **Level {item['level']} - {html.escape(str(item['label']))}:** {html.escape(str(item['criterion']))}")
    lines += [
        "",
        "## Preservation and interoperability",
        "",
        "The preservation target is a versioned public release linked to persistent identifiers when those identifiers actually exist. Software citation uses `CITATION.cff`; CodeMeta is tracked as an interoperability target; archival DOI and RO-Crate are promoted only for stable, bounded research objects.",
        "",
        "Machine-readable interfaces:",
        "",
        f"- [Unified Scholarly Graph]({payload['machine_interfaces'][0]})",
        f"- [Scholarly infrastructure metadata]({payload['machine_interfaces'][1]})",
        "",
        "::: {.qs-footnote-note}",
        "**Provenance.** Identity and affiliation identifiers are curated; publication identifiers come from the canonical academic profile; repository readiness comes only from approved public repositories. Missing metadata is reported as missing rather than inferred.",
        ":::",
        "",
    ]
    return "\n".join(line for line in lines if line is not None).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    expected_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    expected_md = render(payload)

    if args.check:
        current_json = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        current_md = FRAGMENT.read_text(encoding="utf-8") if FRAGMENT.exists() else ""
        stale = []
        if current_json != expected_json:
            stale.append(str(TARGET.relative_to(ROOT)))
        if current_md != expected_md:
            stale.append(str(FRAGMENT.relative_to(ROOT)))
        if stale:
            raise SystemExit("Phase 9 generated outputs are stale: " + ", ".join(stale))
        print("Phase 9 scholarly infrastructure outputs are synchronized.")
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
