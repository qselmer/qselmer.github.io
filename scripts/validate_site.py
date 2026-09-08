#!/usr/bin/env python3
"""Central source and rendered-site validation for qselmer.github.io."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from site_config import ROOT, load_config


BUILD_CHECKS = (
    "build_publications.py",
    "build_conferences.py",
    "build_software.py",
    "build_teaching.py",
    "build_data_resources.py",
    "build_blog.py",
    "build_home.py",
)

LEGACY_JEKYLL_PATHS = (
    ".devcontainer",
    ".github/ISSUE_TEMPLATE",
    ".github/workflows/jekyll.yml",
    ".github/workflows/scrape_talks.yml",
    "CONTRIBUTING.md",
    "Dockerfile",
    "Gemfile",
    "PHASE04_README.txt",
    "_config.yml",
    "_config_docker.yml",
    "_data",
    "_drafts",
    "_includes",
    "_layouts",
    "_pages",
    "_posts",
    "_projects",
    "_publications",
    "_sass",
    "_software",
    "_talks",
    "assets/css",
    "assets/fonts",
    "assets/js",
    "assets/webfonts",
    "docker-compose.yaml",
    "markdown_generator",
    "package.json",
    "talkmap",
    "talkmap.py",
    "talkmap.ipynb",
    "talkmap_out.ipynb",
    "scripts/cv_markdown_to_json.py",
    "scripts/update_cv_json.sh",
)

EXPECTED_COMPATIBILITY_PAGES = (
    "404.html",
    "engagement/index.html",
    "follow/index.html",
    "resources/index.html",
    "services/index.html",
    "terms/index.html",
    "talks/2022-09-01-anchoveta-biomass-variability/index.html",
)

SITE_URL = "https://qselmer.github.io"


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def normalized_text(path: Path) -> str:
    return html_lib.unescape(path.read_text(encoding="utf-8"))


def require_text(path: Path, expected: str) -> None:
    text = normalized_text(path)
    if expected not in text:
        raise RuntimeError(f"{path.relative_to(ROOT)} is missing canonical value: {expected}")


def reject_text(path: Path, forbidden: str) -> None:
    text = normalized_text(path)
    if forbidden in text:
        raise RuntimeError(f"{path.relative_to(ROOT)} contains forbidden legacy value: {forbidden}")


def run_build_checks() -> None:
    for script in BUILD_CHECKS:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), "--check"],
            cwd=ROOT,
            check=True,
        )


def validate_source() -> None:
    config = load_config()
    identity = config["identity"]

    for relative in LEGACY_JEKYLL_PATHS:
        if (ROOT / relative).exists():
            raise RuntimeError(f"Legacy Academic Pages/Jekyll residue is present: {relative}")

    routes = load_json(ROOT / "config/legacy-routes.json")
    route_items = routes.get("routes", [])
    if routes.get("schema_version") != 1 or not route_items:
        raise RuntimeError("config/legacy-routes.json is missing a valid route inventory")
    legacy_routes = [str(item.get("legacy", "")) for item in route_items]
    if len(legacy_routes) != len(set(legacy_routes)):
        raise RuntimeError("config/legacy-routes.json contains duplicate legacy routes")
    for item in route_items:
        if item.get("status") not in {"preserved", "redirect_required"}:
            raise RuntimeError(f"Unsupported route status: {item}")
        if not str(item.get("legacy", "")).startswith("/") or not str(item.get("target", "")).startswith("/"):
            raise RuntimeError(f"Routes must be site-root absolute: {item}")

    json_paths = (
        ["config/site.json"]
        + config.get("website_mirrors", [])
        + config.get("website_registries", [])
        + config.get("derived_json", [])
    )
    for relative in json_paths:
        load_json(ROOT / relative)

    for relative in config.get("generated_fragments", []):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty generated artifact: {relative}")

    publications = load_json(ROOT / "assets/data/publications.json")
    metrics = load_json(ROOT / "assets/data/research-metrics.json")
    conferences = load_json(ROOT / "assets/data/conferences.json")
    if str(publications.get("orcid") or "") != identity["orcid"]:
        raise RuntimeError("Publications ORCID does not match config/site.json")
    if str(metrics.get("orcid") or "") != identity["orcid"]:
        raise RuntimeError("Research-metrics ORCID does not match config/site.json")
    if conferences.get("historical_count") != 1:
        raise RuntimeError("Expected exactly one explicitly retained historical conference record")

    contact = ROOT / "contact" / "index.qmd"
    quarto = ROOT / "_quarto.yml"
    home = ROOT / "index.qmd"
    cv = ROOT / "cv" / "index.qmd"
    styles = ROOT / "accessibility.css"
    historical_talk = ROOT / "talks" / "2022-09-01-anchoveta-biomass-variability" / "index.qmd"

    require_text(contact, identity["email"])
    require_text(contact, identity["linkedin"])
    require_text(quarto, identity["linkedin"])
    require_text(quarto, "open-graph: true")
    require_text(quarto, "twitter-card: true")
    require_text(quarto, "scripts/postprocess_site.py")
    require_text(quarto, "includes/skip-link.html")
    require_text(home, identity["headline"])
    require_text(home, identity["signature"])
    require_text(historical_talk, "stable public proceedings or abstract-book source has not yet been verified")
    reject_text(cv, "# Elmer Quispe-Salazar")

    for marker in (
        ".qs-skip-link",
        ":focus-visible",
        "prefers-reduced-motion",
        "@media (max-width: 760px)",
        ".quarto-title-block",
    ):
        require_text(styles, marker)

    for required in (
        ROOT / "scripts" / "postprocess_site.py",
        ROOT / "scripts" / "check_external_links.py",
        ROOT / "includes" / "skip-link.html",
    ):
        if not required.is_file() or required.stat().st_size == 0:
            raise RuntimeError(f"Missing Phase 7 source: {required.relative_to(ROOT)}")

    for forbidden in config.get("forbidden_legacy_identity", []):
        reject_text(contact, forbidden)
        reject_text(quarto, forbidden)
        reject_text(home, forbidden)

    cv_pdf = ROOT / "files" / "CV.pdf"
    if not cv_pdf.is_file() or cv_pdf.stat().st_size == 0:
        raise RuntimeError("files/CV.pdf is missing or empty")

    run_build_checks()
    print(
        "Source validation PASS: Quarto-only source, route inventory, canonical identity, "
        "SEO/accessibility hooks, JSON catalogues, registries, generated fragments, CV, "
        "and deterministic builders"
    )


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.append(value)


class PageAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = ""
        self.h1_count = 0
        self.missing_img_alt: list[str] = []
        self.missing_iframe_title: list[str] = []
        self.skip_link = False
        self.main_target = False
        self.description = ""
        self.viewport = ""
        self.canonical = ""
        self.robots = ""
        self.refresh = ""
        self.og_title = ""
        self.og_description = ""
        self.twitter_card = ""
        self.twitter_title = ""
        self.insecure_blank_links: list[str] = []

    @staticmethod
    def attrmap(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {k: (v or "") for k, v in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = self.attrmap(attrs)
        if tag == "html":
            self.lang = data.get("lang", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "img" and "alt" not in data:
            self.missing_img_alt.append(data.get("src", "<unknown>"))
        elif tag == "iframe" and not data.get("title"):
            self.missing_iframe_title.append(data.get("src", "<unknown>"))
        elif tag == "meta":
            name = data.get("name", "").lower()
            prop = data.get("property", "").lower()
            equiv = data.get("http-equiv", "").lower()
            content = data.get("content", "")
            if name == "description":
                self.description = content
            elif name == "viewport":
                self.viewport = content
            elif name == "robots":
                self.robots = content
            elif name == "twitter:card":
                self.twitter_card = content
            elif name == "twitter:title":
                self.twitter_title = content
            if prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content
            if equiv == "refresh":
                self.refresh = content
        elif tag == "link":
            rel = data.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = data.get("href", "")
        elif tag == "a":
            classes = set(data.get("class", "").split())
            if "qs-skip-link" in classes and data.get("href") == "#quarto-document-content":
                self.skip_link = True
            if data.get("target") == "_blank":
                rel = set(data.get("rel", "").lower().split())
                if not {"noopener", "noreferrer"}.issubset(rel):
                    self.insecure_blank_links.append(data.get("href", "<unknown>"))
        if data.get("id") == "quarto-document-content":
            self.main_target = True


def parse_page(path: Path) -> PageAuditParser:
    parser = PageAuditParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def internal_target(site: Path, page: Path, reference: str) -> list[Path]:
    ref = reference.strip()
    if not ref or ref.startswith(("#", "//")):
        return []
    parsed = urlsplit(ref)
    if parsed.scheme:
        return []
    path_text = unquote(parsed.path)
    if not path_text:
        return []
    target = site / path_text.lstrip("/") if path_text.startswith("/") else page.parent / path_text
    candidates: list[Path] = []
    if path_text.endswith("/"):
        candidates.append(target / "index.html")
    else:
        candidates.append(target)
        if target.suffix == "":
            candidates.extend((target.with_suffix(".html"), target / "index.html"))
        if target.is_dir():
            candidates.append(target / "index.html")
    return candidates


def validate_internal_links(site: Path) -> tuple[int, int]:
    html_files = sorted(site.rglob("*.html"))
    checked = 0
    missing: list[tuple[Path, str]] = []
    for page in html_files:
        parser = ReferenceParser()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for ref in parser.references:
            candidates = internal_target(site, page, ref)
            if not candidates:
                continue
            checked += 1
            if not any(candidate.exists() for candidate in candidates):
                missing.append((page.relative_to(site), ref))
    if missing:
        details = "\n".join(f"  {page}: {ref}" for page, ref in missing[:50])
        raise RuntimeError(f"{len(missing)} missing internal references detected:\n{details}")
    return len(html_files), checked


def route_file(site: Path, route: str) -> Path:
    if route == "/":
        return site / "index.html"
    relative = route.lstrip("/")
    if route.endswith("/"):
        return site / relative / "index.html"
    return site / relative


def validate_redirects(site: Path, routes: dict) -> set[Path]:
    redirect_files: set[Path] = set()
    for item in routes["routes"]:
        if item.get("status") != "redirect_required":
            continue
        legacy = str(item["legacy"])
        target = str(item["target"])
        page = route_file(site, legacy)
        target_file = route_file(site, target)
        if not page.is_file():
            raise RuntimeError(f"Missing legacy redirect page: {legacy}")
        if not target_file.is_file():
            raise RuntimeError(f"Redirect target is missing: {legacy} -> {target}")
        audit = parse_page(page)
        expected = SITE_URL + target
        if "noindex" not in audit.robots.lower():
            raise RuntimeError(f"Redirect page must be noindex: {legacy}")
        if audit.canonical != expected:
            raise RuntimeError(f"Redirect canonical mismatch: {legacy}")
        if expected not in audit.refresh:
            raise RuntimeError(f"Redirect meta-refresh mismatch: {legacy}")
        if audit.h1_count != 1:
            raise RuntimeError(f"Redirect page must have exactly one h1: {legacy}")
        redirect_files.add(page.resolve())
    return redirect_files


def validate_page_metadata(site: Path, redirect_files: set[Path]) -> int:
    audited = 0
    for page in sorted(site.rglob("*.html")):
        if page.resolve() in redirect_files:
            continue
        audit = parse_page(page)
        rel = page.relative_to(site).as_posix()
        audited += 1
        if audit.lang.lower() != "en":
            raise RuntimeError(f"Missing/incorrect html lang on {rel}")
        if audit.h1_count != 1:
            raise RuntimeError(f"Expected exactly one h1 on {rel}; found {audit.h1_count}")
        if not audit.description.strip():
            raise RuntimeError(f"Missing meta description on {rel}")
        if "width=device-width" not in audit.viewport:
            raise RuntimeError(f"Missing responsive viewport on {rel}")
        if audit.missing_img_alt:
            raise RuntimeError(f"Images without alt text on {rel}: {audit.missing_img_alt}")
        if audit.missing_iframe_title:
            raise RuntimeError(f"Iframes without title on {rel}: {audit.missing_iframe_title}")
        if audit.insecure_blank_links:
            raise RuntimeError(f"target=_blank links missing noopener/noreferrer on {rel}")
        if not audit.skip_link or not audit.main_target:
            raise RuntimeError(f"Skip-link/main target missing on {rel}")

        if rel == "404.html":
            if "noindex" not in audit.robots.lower():
                raise RuntimeError("404 page must be noindex")
            continue

        if not audit.canonical.startswith(SITE_URL):
            raise RuntimeError(f"Missing canonical URL on {rel}")
        if not audit.og_title or not audit.og_description:
            raise RuntimeError(f"Missing Open Graph metadata on {rel}")
        if not audit.twitter_card or not audit.twitter_title:
            raise RuntimeError(f"Missing Twitter card metadata on {rel}")
    return audited


def validate_sitemap(site: Path, routes: dict) -> None:
    sitemap = site / "sitemap.xml"
    robots = site / "robots.txt"
    if not sitemap.is_file() or not robots.is_file():
        raise RuntimeError("sitemap.xml or robots.txt is missing")
    sitemap_text = sitemap.read_text(encoding="utf-8")
    robots_text = robots.read_text(encoding="utf-8")
    if f"Sitemap: {SITE_URL}/sitemap.xml" not in robots_text:
        raise RuntimeError("robots.txt does not advertise the canonical sitemap")
    for item in routes["routes"]:
        if item.get("status") == "redirect_required":
            legacy_url = SITE_URL + str(item["legacy"])
            if f"<loc>{legacy_url}</loc>" in sitemap_text:
                raise RuntimeError(f"Redirect route must not be indexed in sitemap: {legacy_url}")


def validate_rendered() -> None:
    config = load_config()
    identity = config["identity"]
    site = ROOT / "_site"
    if not site.is_dir():
        raise RuntimeError("_site does not exist; render Quarto before rendered validation")

    routes = load_json(ROOT / "config/legacy-routes.json")
    redirect_files = validate_redirects(site, routes)

    home = site / "index.html"
    contact = site / "contact" / "index.html"
    cv_page = site / "cv" / "index.html"
    resume = site / "resume" / "index.html"
    rendered_pdf = site / "files" / "CV.pdf"
    source_pdf = ROOT / "files" / "CV.pdf"

    required = [home, contact, cv_page, resume, rendered_pdf]
    required.extend(site / relative for relative in EXPECTED_COMPATIBILITY_PAGES)
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Rendered artifact missing or empty: {path.relative_to(site)}")

    require_text(home, identity["headline"])
    require_text(home, identity["signature"])
    for label in ("ORCID works", "OpenAlex works", "Citations", "h-index", "i10-index", "OpenAlex"):
        require_text(home, label)
    require_text(home, "research/index.html")
    reject_text(home, '<pre><code><p class="qs-eyebrow">')
    reject_text(home, '<pre><code><span class="qs-metric-value">')

    require_text(contact, identity["email"])
    require_text(contact, "elmer-quispe-salazar-104b6b1a4")
    for forbidden in config.get("forbidden_legacy_identity", []):
        reject_text(contact, forbidden)

    historical = site / "talks" / "2022-09-01-anchoveta-biomass-variability" / "index.html"
    require_text(historical, "stable public proceedings or abstract-book source has not yet been verified")

    if source_pdf.stat().st_size != rendered_pdf.stat().st_size:
        raise RuntimeError("Rendered CV.pdf size differs from source CV.pdf")

    audited = validate_page_metadata(site, redirect_files)
    validate_sitemap(site, routes)
    pages, references = validate_internal_links(site)
    print(
        f"Rendered validation PASS: {pages} HTML pages, {audited} substantive pages audited, "
        f"{len(redirect_files)} redirects certified, {references} internal references checked, 0 missing"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("source", "rendered", "all"))
    args = parser.parse_args()
    if args.mode in {"source", "all"}:
        validate_source()
    if args.mode in {"rendered", "all"}:
        validate_rendered()


if __name__ == "__main__":
    main()
