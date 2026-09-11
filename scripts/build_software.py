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
    body = (
        f'<span class="qs-badge-label">{html.escape(label)}</span>'
        f'<span class="qs-badge-value">{html.escape(value)}</span>'
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


def compact_type(category: str) -> str:
    return "R package" if category == "R package" else "Application"


def compact_stage(maturity: str) -> str:
    value = maturity.casefold()
    if "stable" in value:
        return "Stable"
    if "experimental" in value:
        return "Experimental"
    if "active" in value:
        return "Active"
    return maturity or "Development"


def software_entry(item: dict, curated: dict) -> list[str]:
    name = str(item.get("name") or "Unnamed software").strip()
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

    release = str(item.get("latest_release") or item.get("version") or "Unreleased").strip()
    release_url = str(item.get("latest_release_url") or "").strip()
    stage = compact_stage(maturity)
    badges = [
        badge("Type", compact_type(category), "neutral"),
        badge("Stage", stage, "green" if stage == "Stable" else "amber"),
        badge("Language", language if language and language != "-" else "Mixed", "blue"),
        badge("Release", release, "blue", release_url),
    ]

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
    if links:
        separator = ' <span aria-hidden="true">|</span> '
        lines.append(f'<p class="qs-software-links qs-software-links-after-title">{separator.join(links)}</p>')
    if summary:
        lines.append(f'<p>{html.escape(summary)}</p>')
    lines.append(f'<div class="qs-badge-row">{"".join(badges)}</div>')
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
        raise RuntimeError(f"Software mirror does not match registry; missing={sorted(expected - found)}, unexpected={sorted(found - expected)}")

    groups = [
        ("R package", "Software packages I am a lead developer for", "packages"),
        ("Experimental application", "Research applications I develop", "applications"),
    ]
    lines = ["<!-- Generated by scripts/build_software.py; do not edit manually. -->", ""]
    for category, heading, anchor in groups:
        group = [item for item in items if item.get("category") == category]
        if not group:
            continue
        lines += [f"## {heading} {{#{anchor}}}", "", "```{=html}"]
        for item in sorted(group, key=lambda x: str(x.get("name") or "").casefold()):
            full_name = str(item.get("full_name") or "").strip()
            lines.extend(software_entry(item, curated.get(full_name, {})))
        lines += ["```", ""]

    incubating = registry.get("incubating") or []
    concepts = registry.get("concepts") or []
    if incubating or concepts:
        lines += ["## Incubating and concept-stage work {#incubating}", ""]
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
            raise SystemExit("software/_generated.md is stale; run python scripts/build_software.py")
        print("Software fragment is synchronized.")
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
