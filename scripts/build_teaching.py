#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data" / "teaching.json"
REGISTRY = ROOT / "teaching" / "registry.json"
TARGET = ROOT / "teaching" / "_generated.md"


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def badge(label: str, value: str, tone: str = "neutral") -> str:
    body = (
        f'<span class="qs-badge-label">{html.escape(label)}</span>'
        f'<span class="qs-badge-value">{html.escape(value)}</span>'
    )
    return f'<span class="qs-badge qs-badge-{tone}">{body}</span>'


def display_name(name: str) -> str:
    if name == ".template-training":
        return "SCIENTIFIC TRAINING TEMPLATE"
    cleaned = re.sub(r"-training$", "", name, flags=re.IGNORECASE)
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    cleaned = " ".join(cleaned.split())
    if cleaned.casefold() == "git github":
        return "GIT & GITHUB"
    return cleaned.upper()


def curated_by_repo(registry: dict, key: str) -> dict[str, dict]:
    return {
        str(item.get("repository") or "").strip(): item
        for item in registry.get(key, [])
        if str(item.get("repository") or "").strip()
    }


def teaching_visual(item: dict, curated: dict, display: str) -> str:
    image = str(curated.get("image") or item.get("image") or "").strip()
    image_alt = str(curated.get("image_alt") or item.get("image_alt") or f"{display} teaching resource").strip()
    if image:
        return (
            f'<div class="qs-academic-output-media">'
            f'<img src="{html.escape(image, quote=True)}" alt="{html.escape(image_alt, quote=True)}" '
            'loading="lazy" decoding="async">'
            '</div>'
        )
    return (
        '<div class="qs-academic-output-media qs-academic-output-media-fallback" aria-hidden="true">'
        '<i class="bi bi-mortarboard-fill"></i>'
        '</div>'
    )


def render_item(item: dict, curated: dict) -> str:
    name = str(item.get("name") or "Unnamed resource").strip()
    summary = str(curated.get("summary") or item.get("summary") or item.get("description") or "").strip()
    site_path = str(curated.get("site_path") or item.get("site_path") or "").strip()
    repo_url = str(item.get("html_url") or "").strip()
    display = display_name(name)
    target = site_path or repo_url

    role = str(curated.get("role") or "-").strip()
    audience = str(curated.get("audience") or "-").strip()
    duration = str(curated.get("duration") or "-").strip()
    language = str(curated.get("language_display") or "-").strip()
    materials = str(curated.get("materials") or "-").strip()

    badges = [
        badge("Role", role, "neutral"),
        badge("Audience", audience, "green"),
        badge("Language", language, "blue"),
    ]

    title = html.escape(display)
    if target:
        title = f'<a class="qs-academic-output-title" href="{html.escape(target, quote=True)}">{title}</a>'

    links: list[str] = []
    if site_path:
        links.append(f'<a href="{html.escape(site_path, quote=True)}">Teaching page</a>')
    if repo_url:
        links.append(f'<a href="{html.escape(repo_url, quote=True)}">Repository</a>')

    pieces = [f"{title}."]
    if summary:
        pieces.append(html.escape(summary))
    pieces.append(
        '<span class="qs-academic-output-meta-inline">'
        f'<strong>Duration:</strong> {html.escape(duration)} '
        '<span aria-hidden="true">·</span> '
        f'<strong>Materials:</strong> {html.escape(materials)}.'
        '</span>'
    )
    if links:
        pieces.append(
            '<span class="qs-academic-output-links-inline">'
            + ' <span aria-hidden="true">·</span> '.join(links)
            + '.</span>'
        )
    pieces.append(
        f'<span class="qs-badge-row qs-publication-badges qs-academic-output-badges-inline">'
        f'{"".join(badges)}</span>'
    )

    return "".join([
        '<li class="qs-academic-output-item qs-teaching-output-item">',
        '<div class="qs-academic-output-layout qs-academic-output-layout-inline">',
        teaching_visual(item, curated, display),
        '<div class="qs-academic-output-copy">',
        f'<p class="qs-academic-output-reference qs-academic-output-reference-inline">{" ".join(pieces)}</p>',
        '</div>',
        '</div>',
        '</li>',
    ])


def render_group(lines: list[str], heading: str, anchor: str, items: list[dict], metadata: dict[str, dict]) -> None:
    lines += [
        f"## {heading} {{#{anchor}}}",
        "",
        "```{=html}",
        '<ul class="qs-academic-output-list qs-teaching-output-list">',
    ]
    for item in sorted(items, key=lambda x: str(x.get("name") or "").casefold()):
        full_name = str(item.get("full_name") or "").strip()
        lines.append(render_item(item, metadata.get(full_name, {})))
    lines += ["</ul>", "```", ""]


def render() -> str:
    data = load_json(DATA)
    registry = load_json(REGISTRY)
    teaching = data.get("teaching")
    infrastructure = data.get("infrastructure")
    if not isinstance(teaching, list) or not isinstance(infrastructure, list):
        raise RuntimeError("assets/data/teaching.json must contain teaching and infrastructure lists")

    published_meta = curated_by_repo(registry, "published")
    infrastructure_meta = curated_by_repo(registry, "infrastructure")

    expected_teaching = set(published_meta)
    found_teaching = {str(item.get("full_name") or "").strip() for item in teaching}
    if found_teaching != expected_teaching:
        raise RuntimeError(f"Teaching mirror does not match registry; missing={sorted(expected_teaching - found_teaching)}, unexpected={sorted(found_teaching - expected_teaching)}")

    expected_infra = set(infrastructure_meta)
    found_infra = {str(item.get("full_name") or "").strip() for item in infrastructure}
    if found_infra != expected_infra:
        raise RuntimeError(f"Teaching infrastructure mirror does not match registry; missing={sorted(expected_infra - found_infra)}, unexpected={sorted(found_infra - expected_infra)}")

    lines = ["<!-- Generated by scripts/build_teaching.py; do not edit manually. -->", ""]
    if teaching:
        render_group(lines, "Courses and workshops", "courses", teaching, published_meta)
    if infrastructure:
        render_group(lines, "Teaching infrastructure", "infrastructure", infrastructure, infrastructure_meta)
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != expected:
            raise SystemExit("teaching/_generated.md is stale; run python scripts/build_teaching.py")
        print("Teaching fragment is synchronized.")
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
