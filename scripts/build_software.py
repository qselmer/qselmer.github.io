#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data" / "software.json"
REGISTRY = ROOT / "software" / "registry.json"
TARGET = ROOT / "software" / "_generated.md"
LOGO_ROOT = ROOT / "images" / "software"
LOGO_NAMES = ("logo.svg", "logo.png")


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def badge(label: str, value: str, tone: str = "neutral", url: str = "") -> str:
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


def registry_by_repo(registry: dict) -> dict[str, dict]:
    return {
        str(item.get("repository") or "").strip(): item
        for item in registry.get("published", [])
        if str(item.get("repository") or "").strip()
    }


def synchronized_logo(name: str) -> str:
    directory = LOGO_ROOT / name
    for filename in LOGO_NAMES:
        if (directory / filename).is_file():
            return f"/images/software/{name}/{filename}"
    return ""


def software_entry(item: dict, curated: dict) -> list[str]:
    name = str(item.get("name") or "Unnamed software").strip()
    full_name = str(item.get("full_name") or "").strip()
    category = str(item.get("category") or "Software").strip()
    maturity = str(item.get("maturity") or "Development").strip()
    language = str(item.get("language") or "-").strip()
    summary = str(curated.get("summary") or item.get("summary") or item.get("description") or "").strip()
    site_path = str(curated.get("site_path") or item.get("site_path") or "").strip()
    repo_url = str(item.get("html_url") or "").strip()
    mark = str(curated.get("mark") or name).strip()
    logo = str(curated.get("logo") or item.get("logo") or synchronized_logo(name)).strip()

    if logo:
        visual = (
            f'<img class="qs-software-logo" src="{html.escape(logo, quote=True)}" '
            f'alt="{html.escape(name, quote=True)} logo" loading="lazy">'
        )
    else:
        visual = f'<span class="qs-software-mark-text">{html.escape(mark)}</span>'

    badges = [badge("repo status", "Active", "green", repo_url)]
    if category == "R package":
        badges.append(badge("package", "R", "blue"))
        version = str(item.get("version") or curated.get("version") or "").strip()
        if version:
            badges.append(badge("version", version, "green"))
        check_url = str(item.get("r_cmd_check") or curated.get("r_cmd_check") or "").strip()
        if check_url:
            badges.append(badge("R-CMD-check", "configured", "blue", check_url))
        docs = str(item.get("documentation") or curated.get("documentation") or "").strip()
        if docs:
            badges.append(badge("docs", "online", "blue", docs))
    else:
        badges.append(badge("stage", maturity, "amber" if maturity.casefold() == "experimental" else "neutral"))
        if language and language != "-":
            badges.append(badge("language", language, "blue"))
        application = str(item.get("application") or curated.get("application") or "").strip()
        if application:
            badges.append(badge("app", application, "green"))

    doi = str(item.get("doi") or "").strip()
    if doi:
        doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        badges.append(badge("DOI", doi.replace("https://doi.org/", ""), "blue", doi_url))

    release = str(item.get("latest_release") or "").strip()
    release_url = str(item.get("latest_release_url") or "").strip()
    if release:
        badges.append(badge("release", release, "green", release_url))

    title_href = site_path or repo_url or "#"
    links: list[str] = []
    if repo_url:
        links.append(f'<a href="{html.escape(repo_url, quote=True)}">Repository</a>')
    docs = str(item.get("documentation") or curated.get("documentation") or "").strip()
    if docs:
        links.append(f'<a href="{html.escape(docs, quote=True)}">Documentation</a>')
    if site_path:
        links.append(f'<a href="{html.escape(site_path, quote=True)}">Project page</a>')

    lines = [
        '<article class="qs-software-entry">',
        f'<div class="qs-software-visual" aria-label="{html.escape(name, quote=True)} software mark">{visual}</div>',
        '<div class="qs-software-copy">',
        f'<h3><a href="{html.escape(title_href, quote=True)}">{html.escape(name)}</a></h3>',
    ]
    if summary:
        lines.append(f'<p>{html.escape(summary)}</p>')
    lines.append(f'<div class="qs-badge-row">{"".join(badges)}</div>')
    if links:
        separator = ' <span aria-hidden="true">|</span> '
        lines.append(f'<p class="qs-software-links">{separator.join(links)}</p>')
    lines += ["</div>", "</article>"]
    return lines


def render() -> str:
    data = load_json(DATA)
    registry = load_json(REGISTRY)

    items = data.get("software")
    if not isinstance(items, list):
        raise RuntimeError("assets/data/software.json must contain a software list")

    curated = registry_by_repo(registry)
    expected = set(curated)
    found = {str(item.get("full_name") or "").strip() for item in items}
    if found != expected:
        missing = sorted(expected - found)
        unexpected = sorted(found - expected)
        raise RuntimeError(
            f"Software mirror does not match registry; missing={missing}, unexpected={unexpected}"
        )

    groups = [
        ("R package", "Software packages I am a lead developer for"),
        ("Experimental application", "Research applications I develop"),
    ]

    lines = [
        "<!-- Generated by scripts/build_software.py; do not edit manually. -->",
        "",
    ]

    for category, heading in groups:
        group = [item for item in items if item.get("category") == category]
        if not group:
            continue
        lines += [f"## {heading}", "", "```{=html}"]
        for item in sorted(group, key=lambda x: str(x.get("name") or "").casefold()):
            full_name = str(item.get("full_name") or "").strip()
            lines.extend(software_entry(item, curated.get(full_name, {})))
        lines += ["```", ""]

    incubating = registry.get("incubating") or []
    concepts = registry.get("concepts") or []
    if incubating or concepts:
        lines += [
            "## Incubating and concept-stage work",
            "",
            "These records are preserved for continuity but are not presented as released or validated scientific software.",
            "",
        ]
        for item in incubating:
            full_name = str(item.get("repository") or "")
            name = full_name.split("/", 1)[-1] if full_name else "Unnamed repository"
            site_path = str(item.get("site_path") or "").strip()
            reason = str(item.get("reason") or "").strip()
            label = f"[`{name}`]({site_path})" if site_path else f"`{name}`"
            lines.append(f"- {label} - {reason}")
        for item in concepts:
            name = str(item.get("name") or "Unnamed concept")
            site_path = str(item.get("site_path") or "").strip()
            reason = str(item.get("reason") or "").strip()
            label = f"[{name}]({site_path})" if site_path else name
            lines.append(f"- {label} - {reason}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != expected:
            raise SystemExit(
                "software/_generated.md is stale; run python scripts/build_software.py"
            )
        print("Software fragment is synchronized.")
        return

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
