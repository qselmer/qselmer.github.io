#!/usr/bin/env python3
"""Phase 9 certification for scholarly visibility, interoperability, and preservation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from site_config import ROOT

CONFIG = ROOT / "config" / "site.json"
REGISTRY = ROOT / "scholarly" / "registry.json"
METRICS = ROOT / "assets" / "data" / "research-metrics.json"
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
GRAPH_REGISTRY = ROOT / "graph" / "registry.json"
REPOSITORIES = ROOT / "assets" / "data" / "repository-scholarly-metadata.json"
INFRASTRUCTURE = ROOT / "assets" / "data" / "scholarly-infrastructure.json"
FRAGMENT = ROOT / "open-science" / "_generated.md"
SITE = ROOT / "_site"

ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ROR_RE = re.compile(r"^https://ror\.org/0[a-hj-km-np-tv-z0-9]{8}$", re.I)
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
FORMAL_CATEGORIES = {
    "Journal articles",
    "Preprints & working papers",
    "Books & chapters",
    "Theses",
    "Reports & technical outputs",
}


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def validate_url(value: str, label: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(f"{label} must be an absolute HTTPS URL: {value}")


def validate_source() -> tuple[int, int]:
    config = load(CONFIG)
    registry = load(REGISTRY)
    metrics = load(METRICS)
    publications = load(PUBLICATIONS)
    graph_registry = load(GRAPH_REGISTRY)
    repo_meta = load(REPOSITORIES)
    infrastructure = load(INFRASTRUCTURE)

    identity = config.get("identity") or {}
    orcid = str(identity.get("orcid") or "")
    if not ORCID_RE.fullmatch(orcid):
        raise RuntimeError(f"Invalid ORCID in config/site.json: {orcid}")
    if str(metrics.get("orcid") or "") != orcid:
        raise RuntimeError("ORCID mismatch between config and research metrics")

    affiliation = identity.get("affiliation") or {}
    ror = str(affiliation.get("ror") or "")
    if not ROR_RE.fullmatch(ror):
        raise RuntimeError(f"Invalid ROR identifier: {ror}")
    for key in ("url", "ror"):
        validate_url(str(affiliation.get(key) or ""), f"Affiliation {key}")

    evidence = registry.get("affiliation_evidence") or {}
    if evidence.get("ror") != ror or evidence.get("name") != affiliation.get("name"):
        raise RuntimeError("Curated affiliation evidence does not match config/site.json")
    validate_url(str(evidence.get("verification_source") or ""), "Affiliation verification source")
    if (registry.get("identity_policy") or {}).get("no_identifier_invention") is not True:
        raise RuntimeError("Phase 9 must enforce no_identifier_invention")

    openalex = str((metrics.get("openalex") or {}).get("author_id") or "")
    if not openalex.startswith("https://openalex.org/A"):
        raise RuntimeError("Verified OpenAlex author identifier is missing")

    approved = {str(x) for x in graph_registry.get("public_repositories") or []}
    records = repo_meta.get("repositories") or []
    mirrored = {str(item.get("repository") or "") for item in records if isinstance(item, dict)}
    if mirrored != approved:
        missing = sorted(approved - mirrored)
        extra = sorted(mirrored - approved)
        raise RuntimeError(f"Repository scholarly mirror differs from public allowlist; missing={missing}, extra={extra}")

    for item in records:
        repo = str(item.get("repository") or "")
        url = str(item.get("url") or "")
        if url != f"https://github.com/{repo}":
            raise RuntimeError(f"Repository canonical URL mismatch: {repo}: {url}")
        if item.get("citation_orcid") and not item.get("citation_cff"):
            raise RuntimeError(f"citation_orcid cannot be true without CITATION.cff: {repo}")
        doi = str(item.get("archival_doi") or "")
        if doi and not DOI_RE.fullmatch(doi):
            raise RuntimeError(f"Invalid archival DOI for {repo}: {doi}")

    if infrastructure.get("schema_version") != 1 or infrastructure.get("phase") != 9:
        raise RuntimeError("scholarly-infrastructure.json must use schema_version 1 and phase 9")
    if infrastructure.get("public_only") is not True:
        raise RuntimeError("Phase 9 machine output must be public_only")
    if (infrastructure.get("source_contract") or {}).get("no_identifier_invention") is not True:
        raise RuntimeError("Phase 9 machine output lost the no-identifier-invention contract")
    if (infrastructure.get("identity") or {}).get("orcid") != f"https://orcid.org/{orcid}":
        raise RuntimeError("Phase 9 ORCID URL does not match canonical identity")
    if (infrastructure.get("identity") or {}).get("openalex") != openalex:
        raise RuntimeError("Phase 9 OpenAlex ID does not match research metrics")
    if (infrastructure.get("affiliation") or {}).get("ror") != ror:
        raise RuntimeError("Phase 9 ROR does not match canonical affiliation")

    works = publications.get("publications") or []
    formal = [item for item in works if str(item.get("output_category") or "") in FORMAL_CATEGORIES]
    formal_doi = [item for item in formal if str(item.get("doi") or "").strip()]
    all_doi = [item for item in works if str(item.get("doi") or "").strip()]
    coverage = infrastructure.get("identifier_coverage") or {}
    expected_coverage = {
        "profile_outputs": len(works),
        "profile_outputs_with_doi": len(all_doi),
        "formal_outputs": len(formal),
        "formal_outputs_with_doi": len(formal_doi),
    }
    if coverage != expected_coverage:
        raise RuntimeError(f"Identifier coverage is inconsistent: expected {expected_coverage}, found {coverage}")

    repo_outputs = infrastructure.get("repositories") or []
    if {str(item.get("repository") or "") for item in repo_outputs} != approved:
        raise RuntimeError("Phase 9 repository readiness output is incomplete")
    for item in repo_outputs:
        level = item.get("readiness_level")
        if not isinstance(level, int) or level < 0 or level > 5:
            raise RuntimeError(f"Invalid reproducibility readiness level: {item}")

    interfaces = infrastructure.get("machine_interfaces") or []
    expected_interfaces = {
        "https://qselmer.github.io/assets/data/scholarly-graph.json",
        "https://qselmer.github.io/assets/data/scholarly-infrastructure.json",
    }
    if set(interfaces) != expected_interfaces:
        raise RuntimeError("Phase 9 machine interfaces are incomplete")

    fragment = FRAGMENT.read_text(encoding="utf-8")
    for marker in ("Persistent identity", "Identifier coverage", "Repository readiness", "Preservation and interoperability"):
        if marker not in fragment:
            raise RuntimeError(f"Open science fragment is missing {marker!r}")

    return len(records), len(formal)


def validate_rendered() -> None:
    page = SITE / "open-science" / "index.html"
    data = SITE / "assets" / "data" / "scholarly-infrastructure.json"
    if not page.is_file():
        raise RuntimeError("Rendered /open-science/ page is missing")
    if not data.is_file():
        raise RuntimeError("Rendered scholarly-infrastructure.json is missing")
    body = page.read_text(encoding="utf-8", errors="strict")
    for marker in ("Persistent identity", "Identifier coverage", "Repository readiness", "Preservation and interoperability"):
        if marker not in body:
            raise RuntimeError(f"Rendered Open science page is missing {marker!r}")
    payload = json.loads(data.read_text(encoding="utf-8"))
    if payload.get("phase") != 9 or payload.get("public_only") is not True:
        raise RuntimeError("Rendered Phase 9 machine resource is invalid")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()
    if args.mode in {"source", "all"}:
        repositories, formal = validate_source()
        print(f"Phase 9 source QA PASS: {repositories} public repositories audited; {formal} formal scholarly outputs checked; persistent-identifier contract active.")
    if args.mode in {"rendered", "all"}:
        validate_rendered()
        print("Phase 9 rendered QA PASS: Open science page and machine-readable scholarly infrastructure are published.")


if __name__ == "__main__":
    main()
