#!/usr/bin/env python3
"""Post-render certification and scholarly metadata helpers for qselmer.github.io.

This script runs from Quarto's project post-render hook. It adds canonical URLs,
structured JSON-LD, route-specific social preview metadata, RSS discovery links,
404 indexing policy, hardened target=_blank links, and compatibility redirects.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
SITE_URL = "https://qselmer.github.io"
ROUTES = ROOT / "config" / "legacy-routes.json"
PUBLICATIONS = ROOT / "assets" / "data" / "publications.json"
SOFTWARE = ROOT / "assets" / "data" / "software.json"
BLOG = ROOT / "blog" / "registry.json"
PERSON_ID = SITE_URL + "/#person"


def route_for_page(page: Path) -> str:
    rel = page.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def canonical_url(route: str) -> str:
    return SITE_URL + route


def insert_before_head_end(text: str, fragment: str) -> str:
    marker = "</head>"
    if marker not in text:
        raise RuntimeError("Rendered HTML is missing </head>")
    return text.replace(marker, fragment + "\n" + marker, 1)


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def harden_blank_links(text: str) -> str:
    pattern = re.compile(r'<a(?P<attrs>[^>]*\btarget="_blank"[^>]*)>', re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        if re.search(r"\brel\s*=", attrs, flags=re.IGNORECASE):
            return match.group(0)
        return f'<a{attrs} rel="noopener noreferrer">'

    return pattern.sub(repl, text)


def set_meta(text: str, attr: str, key: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    replacement = f'<meta {attr}="{html.escape(key, quote=True)}" content="{escaped}">'
    pattern = re.compile(
        rf'<meta(?=[^>]*\b{re.escape(attr)}=["\']{re.escape(key)}["\'])[^>]*>',
        flags=re.IGNORECASE,
    )
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return insert_before_head_end(text, replacement)


def add_rss_discovery(text: str, route: str) -> str:
    if route != "/blog/" and not route.startswith("/blog/"):
        return text
    if 'type="application/rss+xml"' in text:
        return text
    href = SITE_URL + "/blog/index.xml"
    fragment = (
        '<link rel="alternate" type="application/rss+xml" '
        f'title="Elmer Quispe-Salazar - Posts" href="{html.escape(href, quote=True)}">'
    )
    return insert_before_head_end(text, fragment)


def social_preview(route: str) -> tuple[str, str, str] | None:
    if route == "/publications/":
        return ("/images/profile.png", "Elmer Quispe-Salazar publications", "article")
    if route in {"/talks/", "/talks/2024-11-11-anchoveta-gsi-sibecorp/", "/talks/2022-09-01-anchoveta-biomass-variability/"}:
        return ("/images/editing-talk.png", "Scientific talks by Elmer Quispe-Salazar", "article")
    if route == "/talks/2026-05-06-anchovy-health-index/":
        return ("/images/talks/anchovy-health-index-thumbnail.png", "Multivariate Health Index of the anchovy presentation", "article")
    if route == "/talks/2026-05-08-critical-points-anchovy-stock/":
        return ("/images/talks/anchovy-critical-points-thumbnail.png", "Critical points in the anchovy stock presentation", "article")
    if route == "/software/" or route.startswith("/software/"):
        return ("/images/favicon-512x512.png", "Open research software by Elmer Quispe-Salazar", "website")
    if route == "/blog/":
        return ("/images/home/statistical-modelling-workflow.png", "Technical posts in fisheries and marine ecology", "website")
    if route.startswith("/blog/"):
        return ("/images/home/statistical-modelling-workflow.png", "Statistical modelling workflow for fisheries and marine ecology", "article")
    return None


def apply_social_preview(text: str, route: str) -> str:
    preview = social_preview(route)
    if preview is None:
        return text
    image_path, image_alt, og_type = preview
    image_url = SITE_URL + image_path
    text = set_meta(text, "property", "og:image", image_url)
    text = set_meta(text, "property", "og:image:alt", image_alt)
    text = set_meta(text, "property", "og:type", og_type)
    text = set_meta(text, "name", "twitter:image", image_url)
    text = set_meta(text, "name", "twitter:image:alt", image_alt)
    text = set_meta(text, "name", "twitter:card", "summary_large_image")
    return text


def person_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Elmer Quispe-Salazar",
        "url": SITE_URL + "/",
        "image": SITE_URL + "/images/profile.png",
        "jobTitle": ["Marine Quantitative Ecologist", "Fisheries Scientist"],
        "worksFor": {
            "@type": "Organization",
            "name": "Instituto del Mar del Perú (IMARPE)",
            "url": "https://www.gob.pe/imarpe",
        },
        "sameAs": [
            "https://orcid.org/0000-0001-9229-6379",
            "https://scholar.google.com/citations?user=wz83egoAAAAJ&hl=en",
            "https://github.com/qselmer",
            "https://www.linkedin.com/in/elmer-quispe-salazar-104b6b1a4/",
        ],
        "knowsAbout": [
            "quantitative marine ecology",
            "fisheries science",
            "stock assessment",
            "population dynamics",
            "spatial ecology",
            "environmental variability",
            "reproducible scientific computing",
        ],
    }


def scholarly_schema() -> dict | None:
    payload = load_json(PUBLICATIONS)
    articles: list[dict] = []
    for item in payload.get("publications", []):
        if item.get("output_category") != "Journal articles":
            continue
        authors = []
        for name in item.get("authors", []):
            if name == "Elmer Quispe-Salazar":
                authors.append({"@id": PERSON_ID})
            else:
                authors.append({"@type": "Person", "name": name})
        node: dict = {
            "@type": "ScholarlyArticle",
            "headline": item.get("title", ""),
            "name": item.get("title", ""),
            "datePublished": item.get("year", ""),
            "author": authors or [{"@id": PERSON_ID}],
            "isPartOf": {"@type": "Periodical", "name": item.get("journal", "")},
            "url": item.get("url", ""),
            "mainEntityOfPage": SITE_URL + "/publications/#papers",
        }
        if item.get("volume"):
            node["volumeNumber"] = item["volume"]
        if item.get("issue"):
            node["issueNumber"] = item["issue"]
        if item.get("pages"):
            node["pagination"] = item["pages"]
        if item.get("doi"):
            node["identifier"] = {
                "@type": "PropertyValue",
                "propertyID": "DOI",
                "value": item["doi"],
            }
            node["sameAs"] = "https://doi.org/" + item["doi"]
        articles.append(node)
    if not articles:
        return None
    return {"@context": "https://schema.org", "@graph": [person_schema(), *articles]}


def software_schema(route: str) -> dict | None:
    payload = load_json(SOFTWARE)
    for item in payload.get("software", []):
        if item.get("site_path") != route:
            continue
        node: dict = {
            "@context": "https://schema.org",
            "@type": "SoftwareSourceCode",
            "name": item.get("name", ""),
            "description": item.get("summary") or item.get("description") or "",
            "url": canonical_url(route),
            "codeRepository": item.get("html_url", ""),
            "author": {"@id": PERSON_ID},
        }
        if item.get("language"):
            node["programmingLanguage"] = item["language"]
        if item.get("latest_release"):
            node["version"] = item["latest_release"]
        elif item.get("version"):
            node["version"] = item["version"]
        if item.get("documentation"):
            node["softwareHelp"] = {"@type": "CreativeWork", "url": item["documentation"]}
        return node
    return None


def course_schema(route: str) -> dict | None:
    if route != "/teaching/git-github-training/":
        return None
    return {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": "Git and GitHub Training",
        "description": "Structured teaching materials and practical exercises for Git, GitHub, and reproducible version-control workflows.",
        "url": canonical_url(route),
        "provider": {"@id": PERSON_ID},
        "inLanguage": "es",
        "educationalLevel": "Beginner",
        "about": ["Git", "GitHub", "version control", "reproducible research"],
    }


def blog_schema(route: str) -> dict | None:
    payload = load_json(BLOG)
    for post in payload.get("posts", []):
        if post.get("route") != route:
            continue
        image = str(post.get("thumbnail") or "/images/profile.png")
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.get("title", ""),
            "description": post.get("excerpt", ""),
            "datePublished": post.get("date", ""),
            "dateModified": post.get("updated") or post.get("date", ""),
            "author": {"@id": PERSON_ID},
            "mainEntityOfPage": canonical_url(route),
            "url": canonical_url(route),
            "image": SITE_URL + image,
            "articleSection": post.get("topic", ""),
        }
    return None


def schema_for_route(route: str) -> dict | None:
    if route == "/":
        return person_schema()
    if route == "/publications/":
        return scholarly_schema()
    software = software_schema(route)
    if software is not None:
        return software
    course = course_schema(route)
    if course is not None:
        return course
    blog = blog_schema(route)
    if blog is not None:
        return blog
    return None


def inject_json_ld(text: str, route: str) -> str:
    schema = schema_for_route(route)
    if schema is None:
        return text
    pattern = re.compile(
        r'<script id="qs-structured-data" type="application/ld\+json">.*?</script>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = pattern.sub("", text)
    payload = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    fragment = f'<script id="qs-structured-data" type="application/ld+json">{payload}</script>'
    return insert_before_head_end(text, fragment)


def postprocess_rendered_pages() -> None:
    if not SITE.is_dir():
        raise RuntimeError("_site does not exist")

    for page in sorted(SITE.rglob("*.html")):
        text = page.read_text(encoding="utf-8", errors="strict")
        route = route_for_page(page)

        if route != "/404.html" and 'rel="canonical"' not in text:
            href = html.escape(canonical_url(route), quote=True)
            text = insert_before_head_end(text, f'<link rel="canonical" href="{href}">')

        if route == "/404.html" and 'name="robots"' not in text:
            text = insert_before_head_end(
                text, '<meta name="robots" content="noindex,follow">'
            )

        text = apply_social_preview(text, route)
        text = add_rss_discovery(text, route)
        text = inject_json_ld(text, route)
        text = harden_blank_links(text)
        page.write_text(text, encoding="utf-8")


def redirect_output_path(legacy: str) -> Path:
    if not legacy.startswith("/") or ".." in legacy:
        raise RuntimeError(f"Unsafe legacy route: {legacy}")
    rel = legacy.lstrip("/")
    if legacy.endswith("/"):
        rel += "index.html"
    if not rel:
        raise RuntimeError("Root route cannot be a redirect")
    return SITE / rel


def redirect_document(legacy: str, target: str) -> str:
    target_url = canonical_url(target)
    escaped_url = html.escape(target_url, quote=True)
    label = html.escape(target, quote=False)
    js_url = json.dumps(target_url)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="noindex,follow">\n'
        '<meta name="description" content="Compatibility redirect for a moved page on qselmer.github.io.">\n'
        f'<link rel="canonical" href="{escaped_url}">\n'
        f'<meta http-equiv="refresh" content="0; url={escaped_url}">\n'
        "<title>Page moved - Elmer Quispe-Salazar</title>\n"
        f"<script>window.location.replace({js_url});</script>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        "<h1>Page moved</h1>\n"
        f'<p>This address has moved to <a href="{escaped_url}">{label}</a>.</p>\n'
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


def build_redirects() -> int:
    payload = json.loads(ROUTES.read_text(encoding="utf-8"))
    routes = payload.get("routes", [])
    count = 0
    for item in routes:
        if item.get("status") != "redirect_required":
            continue
        legacy = str(item["legacy"])
        target = str(item["target"])
        output = redirect_output_path(legacy)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(redirect_document(legacy, target), encoding="utf-8")
        count += 1
    return count


def main() -> None:
    postprocess_rendered_pages()
    count = build_redirects()
    print(
        "Post-render PASS: canonical, structured-data, social, and RSS metadata hardened; "
        f"{count} legacy redirects generated"
    )


if __name__ == "__main__":
    main()
