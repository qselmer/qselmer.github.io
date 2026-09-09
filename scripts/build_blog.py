#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "blog" / "registry.json"
TARGET = ROOT / "blog" / "_generated.md"
MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def load_registry() -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("blog/registry.json must contain a JSON object")
    if payload.get("schema_version") != 2:
        raise RuntimeError("Unsupported blog/registry.json schema_version")
    posts = payload.get("posts")
    if not isinstance(posts, list):
        raise RuntimeError("blog/registry.json must contain a posts list")
    return payload


def parse_iso_date(value: object, label: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise RuntimeError(f"Invalid {label}: {value}") from exc


def format_date(value: object) -> str:
    parsed = parse_iso_date(value, "post date")
    return f"{MONTHS[parsed.month - 1]} {parsed.day}, {parsed.year}"


def validate_post(post: dict) -> None:
    required = ("slug", "title", "date", "route", "author", "excerpt")
    missing = [key for key in required if not str(post.get(key) or "").strip()]
    if missing:
        raise RuntimeError(f"Post is missing required fields: {missing}")

    parse_iso_date(post["date"], f"date for {post['slug']}")
    if post.get("updated"):
        parse_iso_date(post["updated"], f"updated date for {post['slug']}")

    route = str(post["route"])
    if not route.startswith("/blog/") or not route.endswith("/"):
        raise RuntimeError(f"Post route must be /blog/<slug>/: {route}")

    thumbnail = str(post.get("thumbnail") or "").strip()
    if thumbnail and not thumbnail.startswith("/"):
        raise RuntimeError(f"Post thumbnail must use a site-root path: {thumbnail}")


def source_path(post: dict) -> Path:
    return ROOT / "blog" / str(post["slug"]) / "index.qmd"


def estimate_read_minutes(post: dict) -> int:
    explicit = post.get("read_minutes")
    if explicit is not None:
        value = int(explicit)
        if value < 1:
            raise RuntimeError(f"read_minutes must be >= 1 for {post['slug']}")
        return value

    path = source_path(post)
    if not path.is_file():
        raise RuntimeError(f"Post source does not exist: {path.relative_to(ROOT)}")

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[`*_#>|\[\](){}]", " ", text)
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'-]+\b", text, flags=re.UNICODE)
    return max(1, math.ceil(len(words) / 220))


def render_post(post: dict) -> list[str]:
    route = html.escape(str(post["route"]), quote=True)
    title = html.escape(str(post["title"]).strip())
    author = html.escape(str(post["author"]).strip())
    excerpt = html.escape(str(post["excerpt"]).strip())
    updated = post.get("updated") or post["date"]
    updated_label = html.escape(format_date(updated))
    minutes = estimate_read_minutes(post)
    minute_label = "min read" if minutes == 1 else "min read"

    thumbnail = str(post.get("thumbnail") or "").strip()
    thumbnail_alt = html.escape(str(post.get("thumbnail_alt") or "").strip())
    aria_title = html.escape(f"Open {post['title']}", quote=True)

    lines = [
        '<article class="qs-post-row">',
        '<div class="qs-post-copy">',
        f'<h2><a href="{route}">{title}</a></h2>',
        f'<p class="qs-post-summary">{excerpt}</p>',
        f'<p class="qs-post-author">{author}</p>',
        f'<p class="qs-post-meta">Last updated on {updated_label} <span aria-hidden="true">·</span> {minutes} {minute_label}</p>',
        "</div>",
    ]

    if thumbnail:
        src = html.escape(thumbnail, quote=True)
        lines += [
            f'<a class="qs-post-thumb" href="{route}" aria-label="{aria_title}">',
            f'<img src="{src}" alt="{thumbnail_alt}" loading="lazy" decoding="async">',
            "</a>",
        ]
    else:
        lines += [
            f'<a class="qs-post-thumb qs-post-thumb-fallback" href="{route}" aria-label="{aria_title}">',
            '<span aria-hidden="true">EQS</span>',
            "</a>",
        ]

    lines.append("</article>")
    return lines


def render() -> str:
    payload = load_registry()
    posts = payload["posts"]
    slugs: set[str] = set()
    routes: set[str] = set()

    for post in posts:
        if not isinstance(post, dict):
            raise RuntimeError("Every post record must be a JSON object")
        validate_post(post)
        slug = str(post["slug"])
        route = str(post["route"])
        if slug in slugs:
            raise RuntimeError(f"Duplicate post slug: {slug}")
        if route in routes:
            raise RuntimeError(f"Duplicate post route: {route}")
        slugs.add(slug)
        routes.add(route)

    lines = [
        "<!-- Generated by scripts/build_blog.py; do not edit manually. -->",
        "",
        "```{=html}",
        '<div class="qs-post-list" aria-label="Technical posts">',
    ]

    for post in sorted(posts, key=lambda item: str(item.get("updated") or item["date"]), reverse=True):
        lines += render_post(post)

    lines += ["</div>", "```", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != expected:
            raise SystemExit("blog/_generated.md is stale; run python scripts/build_blog.py")
        print("Posts fragment is synchronized.")
        return

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
