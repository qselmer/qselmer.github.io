#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from build_research_graph import build_payload as build_research_graph_payload, normalize as graph_normalize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "data" / "publications.json"
CONFIG = ROOT / "config" / "site.json"
PROJECTS_REGISTRY = ROOT / "projects" / "registry.json"
TARGET = ROOT / "publications" / "_generated.md"

DISPLAY_ORDER = [
    "Journal articles",
    "Preprints & working papers",
    "Books & chapters",
    "Theses",
    "Reports & technical outputs",
]

HEADING = {
    "Journal articles": ("Peer-reviewed articles", "papers"),
    "Preprints & working papers": ("Preprints and forthcoming manuscripts", "preprints"),
    "Books & chapters": ("Books and book chapters", "books"),
    "Theses": ("Theses", "theses"),
    "Reports & technical outputs": ("Reports and institutional technical outputs", "reports"),
}

NAV_LABEL = {
    "Journal articles": "Papers",
    "Preprints & working papers": "Preprints",
    "Books & chapters": "Books",
    "Theses": "Theses",
    "Reports & technical outputs": "Reports",
}

# Only outlets or repositories whose open-access status is known are labelled.
# Scientia Marina distributes its online content under CC BY 4.0.
OPEN_ACCESS_OUTLETS = {"scientia marina"}
OPEN_ACCESS_HOSTS = {
    "zenodo.org",
    "www.zenodo.org",
    "arxiv.org",
    "www.arxiv.org",
    "biorxiv.org",
    "www.biorxiv.org",
    "osf.io",
    "www.osf.io",
}

YEAR_GROUP_THRESHOLD = 4


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def load_catalogue() -> dict[str, Any]:
    payload = load_json(SOURCE)
    publications = payload.get("publications")
    if not isinstance(publications, list):
        raise RuntimeError("assets/data/publications.json must contain a publications list")
    declared = payload.get("count")
    if declared is not None and declared != len(publications):
        raise RuntimeError("Publication count does not match publications list length")
    for index, pub in enumerate(publications, start=1):
        if not isinstance(pub, dict):
            raise RuntimeError(f"Publication {index} is not an object")
        for field in ("title", "year", "output_category"):
            if not str(pub.get(field) or "").strip():
                raise RuntimeError(f"Publication {index} is missing required field: {field}")
    return payload


def load_identity() -> dict[str, Any]:
    identity = load_json(CONFIG).get("identity")
    if not isinstance(identity, dict):
        raise RuntimeError("config/site.json must contain identity metadata")
    return identity


def initials(given: str) -> str:
    parts = re.findall(r"[^\W\d_]+", given, flags=re.UNICODE)
    return " ".join(f"{part[0].upper()}." for part in parts if part)


def apa_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip())
    if not clean:
        return ""
    if "," in clean:
        family, given = [part.strip() for part in clean.split(",", 1)]
    else:
        parts = clean.split()
        family = parts[-1]
        given = " ".join(parts[:-1])
    rendered = f"{family}, {initials(given)}".strip().rstrip(",")
    low = clean.casefold()
    if "quispe-salazar" in low and "elmer" in low:
        return f"**{rendered}**"
    return rendered


def authors(pub: dict[str, Any]) -> list[str]:
    names = [str(value).strip() for value in (pub.get("authors") or []) if str(value).strip()]
    return names or ["Elmer Quispe-Salazar"]


def authors_apa(pub: dict[str, Any]) -> str:
    rendered = [apa_name(name) for name in authors(pub)]
    if len(rendered) == 1:
        return rendered[0]
    if len(rendered) == 2:
        return f"{rendered[0]} & {rendered[1]}"
    return f"{', '.join(rendered[:-1])}, & {rendered[-1]}"


def source_apa(pub: dict[str, Any]) -> str:
    journal = str(pub.get("journal") or pub.get("outlet") or pub.get("type") or "").strip()
    volume = str(pub.get("volume") or "").strip()
    issue = str(pub.get("issue") or "").strip()
    pages = str(pub.get("pages") or "").strip()
    if not journal:
        return ""
    source = f"*{journal}*"
    if volume:
        source = f"*{journal}, {volume}*"
    if issue:
        source += f"({issue})"
    if pages:
        source += f", {pages}"
    return source + "."


def canonical_doi(value: str) -> str:
    doi = value.strip()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)


def canonical_doi_url(value: str) -> str:
    doi = canonical_doi(value)
    return f"https://doi.org/{doi}" if doi else ""


def badge(label: str, value: str, tone: str = "blue", url: str = "") -> str:
    label_html = html.escape(label)
    value_html = html.escape(value)
    body = (
        f'<span class="qs-badge-label">{label_html}</span>'
        f'<span class="qs-badge-value">{value_html}</span>'
    )
    classes = f"qs-badge qs-badge-{tone}"
    if url:
        return f'<a class="{classes}" href="{html.escape(url, quote=True)}">{body}</a>'
    return f'<span class="{classes}">{body}</span>'


def string_url(pub: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = pub.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def is_open_access(pub: dict[str, Any]) -> bool:
    journal = str(pub.get("journal") or pub.get("outlet") or "").strip().casefold()
    if journal in OPEN_ACCESS_OUTLETS:
        return True
    url = str(pub.get("url") or "").strip()
    if not url:
        return False
    return urlparse(url).netloc.casefold() in OPEN_ACCESS_HOSTS


def publication_graph_id(pub: dict[str, Any]) -> str:
    title = str(pub.get("title") or "").strip()
    return f"publication:{graph_normalize(title)}:{pub.get('year', '')}"


def research_context() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    graph = build_research_graph_payload()
    registry = load_json(PROJECTS_REGISTRY)
    sections = registry.get("sections") or []
    projects = registry.get("projects") or []

    nav_labels: dict[str, str] = {}
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id") or "").strip()
        if section_id:
            nav_labels[section_id] = str(section.get("nav_label") or section.get("heading") or section_id).strip()

    publication_themes: dict[str, dict[str, str]] = {}
    for theme in graph.get("themes", []):
        if not isinstance(theme, dict):
            continue
        theme_id = str(theme.get("id") or "").strip()
        heading = str(theme.get("heading") or "").strip()
        for output in theme.get("outputs") or []:
            if not isinstance(output, dict) or output.get("source") != "publications":
                continue
            output_id = str(output.get("id") or "").strip()
            if output_id:
                publication_themes[output_id] = {
                    "id": theme_id,
                    "heading": heading,
                    "label": nav_labels.get(theme_id, heading or theme_id),
                }

    project_titles = {
        str(project.get("slug") or "").strip(): str(project.get("title") or project.get("slug") or "").strip()
        for project in projects
        if isinstance(project, dict) and str(project.get("slug") or "").strip()
    }
    return publication_themes, project_titles


def bibtex_escape(value: object) -> str:
    text = str(value or "").strip()
    text = text.replace("\\", "\\textbackslash{}")
    for char in ("&", "%", "$", "#", "_"):
        text = text.replace(char, f"\\{char}")
    return text


def citation_key(pub: dict[str, Any]) -> str:
    first_author = authors(pub)[0]
    if "," in first_author:
        family = first_author.split(",", 1)[0]
    else:
        family = first_author.split()[-1]
    family = unicodedata.normalize("NFKD", family)
    family = "".join(ch for ch in family if not unicodedata.combining(ch))
    family = re.sub(r"[^A-Za-z0-9]+", "", family).lower() or "author"
    year = re.sub(r"[^0-9]", "", str(pub.get("year") or "")) or "nd"
    title_words = re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKD", str(pub.get("title") or "")))
    stop = {"a", "an", "and", "of", "the", "to", "in", "for", "on", "with"}
    keyword = next((word for word in title_words if word.casefold() not in stop), "work")
    return f"{family}{year}{keyword.lower()}"


def bibtex_entry(pub: dict[str, Any]) -> str:
    category = str(pub.get("output_category") or "")
    work_type = str(pub.get("type") or "").casefold()
    if category == "Journal articles":
        entry_type = "article"
    elif category == "Books & chapters" and "chapter" in work_type:
        entry_type = "incollection"
    elif category == "Books & chapters":
        entry_type = "book"
    elif category == "Reports & technical outputs":
        entry_type = "techreport"
    else:
        entry_type = "misc"

    fields: list[tuple[str, str]] = [
        ("author", " and ".join(authors(pub))),
        ("title", str(pub.get("title") or "")),
        ("year", str(pub.get("year") or "")),
    ]

    source = str(pub.get("journal") or pub.get("outlet") or "").strip()
    if entry_type == "article" and source:
        fields.append(("journal", source))
    elif entry_type == "incollection" and source:
        fields.append(("booktitle", source))
    elif entry_type == "techreport" and source:
        fields.append(("institution", source))
    elif entry_type == "misc" and source:
        fields.append(("howpublished", source))

    for source_key, bib_key in (("volume", "volume"), ("issue", "number"), ("pages", "pages"), ("publisher", "publisher")):
        value = str(pub.get(source_key) or "").strip()
        if value:
            fields.append((bib_key, value))

    doi = canonical_doi(str(pub.get("doi") or ""))
    url = str(pub.get("url") or "").strip()
    if doi:
        fields.append(("doi", doi))
    if url:
        fields.append(("url", url))
    if entry_type == "misc":
        note = str(pub.get("type") or category).strip()
        if note:
            fields.append(("note", note))

    rendered_fields = ",\n".join(
        f"  {key} = {{{bibtex_escape(value)}}}" for key, value in fields if str(value).strip()
    )
    return f"@{entry_type}{{{citation_key(pub)},\n{rendered_fields}\n}}"


def bibtex_details(pub: dict[str, Any]) -> str:
    code = html.escape(bibtex_entry(pub), quote=False)
    return (
        '<details class="qs-publication-bibtex">'
        '<summary aria-label="Show BibTeX citation">'
        '<span class="qs-badge qs-badge-neutral">'
        '<span class="qs-badge-label">BibTeX</span><span class="qs-badge-value">view</span>'
        '</span>'
        '</summary>'
        f'<pre><code>{code}</code></pre>'
        '</details>'
    )


def reference(
    pub: dict[str, Any],
    publication_themes: dict[str, dict[str, str]],
    project_titles: dict[str, str],
) -> str:
    author_text = authors_apa(pub)
    year = str(pub.get("year") or "n.d.")
    title = str(pub.get("title") or "Untitled work").strip()
    parts = [f"- {author_text} ({year}). {title}."]
    source = source_apa(pub)
    if source:
        parts.append(source)

    doi = str(pub.get("doi") or "").strip()
    url = str(pub.get("url") or "").strip()
    badges: list[str] = []
    if doi:
        clean_doi = canonical_doi(doi)
        badges.append(badge("DOI", clean_doi, "blue", canonical_doi_url(doi)))
    elif url:
        badges.append(badge("Output", "view", "blue", url))

    if is_open_access(pub):
        badges.append(badge("Open", "access", "green", url or canonical_doi_url(doi)))

    pdf_url = string_url(pub, "pdf_url", "pdf")
    code_url = string_url(pub, "code_url", "code")
    data_url = string_url(pub, "data_url", "data")
    if pdf_url:
        badges.append(badge("PDF", "open", "neutral", pdf_url))
    if code_url:
        badges.append(badge("Code", "repository", "neutral", code_url))
    if data_url:
        badges.append(badge("Data", "dataset", "neutral", data_url))

    theme = publication_themes.get(publication_graph_id(pub))
    if theme and theme.get("id"):
        badges.append(
            badge(
                "Research",
                str(theme.get("label") or theme.get("heading") or "theme"),
                "amber",
                f"/projects/#{theme['id']}",
            )
        )

    project_slugs: list[str] = []
    raw_projects = pub.get("project_slugs")
    if isinstance(raw_projects, list):
        project_slugs.extend(str(value).strip() for value in raw_projects if str(value).strip())
    single_project = str(pub.get("project_slug") or "").strip()
    if single_project:
        project_slugs.append(single_project)
    for slug in dict.fromkeys(project_slugs):
        badges.append(badge("Project", project_titles.get(slug, slug), "amber", f"/projects/{slug}/"))

    related_talk_url = string_url(pub, "related_talk_url")
    if related_talk_url:
        related_talk_label = str(pub.get("related_talk_label") or "related").strip()
        badges.append(badge("Talk", related_talk_label, "amber", related_talk_url))

    if badges:
        parts.append(f'<span class="qs-badge-row qs-publication-badges">{"".join(badges)}</span>')
    parts.append(bibtex_details(pub))
    return " ".join(parts)


def year_value(pub: dict[str, Any]) -> int:
    try:
        return int(pub.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def sorted_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (-year_value(item), str(item.get("title") or "").casefold()))


def render_items(
    items: list[dict[str, Any]],
    publication_themes: dict[str, dict[str, str]],
    project_titles: dict[str, str],
) -> list[str]:
    ordered = sorted_items(items)
    years = list(dict.fromkeys(str(item.get("year") or "n.d.") for item in ordered))
    lines: list[str] = []
    if len(ordered) >= YEAR_GROUP_THRESHOLD and len(years) > 1:
        for year in years:
            lines.extend([f"### {year}", ""])
            for pub in [item for item in ordered if str(item.get("year") or "n.d.") == year]:
                lines.append(reference(pub, publication_themes, project_titles))
            lines.append("")
    else:
        for pub in ordered:
            lines.append(reference(pub, publication_themes, project_titles))
        lines.append("")
    return lines


def build_text(payload: dict[str, Any]) -> str:
    publications = payload["publications"]
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in DISPLAY_ORDER}
    for pub in publications:
        category = str(pub.get("output_category") or "Other research outputs")
        if category in grouped:
            grouped[category].append(pub)

    active_categories = [category for category in DISPLAY_ORDER if grouped[category]]
    identity = load_identity()
    publication_themes, project_titles = research_context()

    lines = [
        "<!-- AUTO-GENERATED FROM assets/data/publications.json. DO NOT EDIT BY HAND. -->",
        "",
    ]

    if active_categories:
        lines.extend([
            '<nav class="qs-publication-nav" aria-label="Publication sections">',
            *[
                f'<a href="#{HEADING[category][1]}"><strong>{NAV_LABEL[category]}</strong></a>'
                for category in active_categories
            ],
            "</nav>",
            "",
        ])

    orcid = str(payload.get("orcid") or identity.get("orcid") or "").strip()
    scholar = str(identity.get("google_scholar") or "").strip()
    if orcid:
        lines.append(
            f'<p class="qs-publication-profile"><em>My ORCID iD is</em> '
            f'<a href="https://orcid.org/{html.escape(orcid, quote=True)}"><strong>{html.escape(orcid)}</strong></a>.</p>'
        )
    if scholar:
        lines.append(
            f'<p class="qs-publication-profile"><em>My Google Scholar profile is</em> '
            f'<a href="{html.escape(scholar, quote=True)}"><strong>here</strong></a>.</p>'
        )
    if orcid or scholar:
        lines.append("")

    for category in active_categories:
        heading, anchor = HEADING[category]
        lines.extend([f"## {heading} {{#{anchor}}}", ""])
        lines.extend(render_items(grouped[category], publication_themes, project_titles))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Quarto publication fragment from the canonical local JSON mirror.")
    parser.add_argument("--check", action="store_true", help="Fail if the generated fragment is stale.")
    args = parser.parse_args()

    payload = load_catalogue()
    expected = build_text(payload)
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""

    if args.check:
        if current != expected:
            raise SystemExit("publications/_generated.md is stale; run python scripts/build_publications.py")
        print("Publication fragment is synchronized with assets/data/publications.json")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if current == expected:
        print("Publication fragment already up to date")
        return 0
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Rendered {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
