# qselmer.github.io

Personal academic website of **Elmer Quispe-Salazar**, implemented with Quarto and deployed through GitHub Pages Actions.

> Production status: the controlled migration from Academic Pages/Jekyll to Quarto was completed on 8 September 2026. The production branch is currently `master`; the final pre-migration Jekyll implementation remains preserved at `legacy/jekyll-v0.9`.

## Information architecture

The website is a discovery and presentation layer. Scientific repositories remain the source of truth for code, analyses, manuscripts, software, and teaching materials.

- **About** - concise scientific identity, research focus, and recent posts.
- **Research** - the unified thematic catalogue for research questions, active projects, and related papers, reports, talks, theses, and software. The stable public route remains `/projects/`.
- **Publications** - formal scholarly outputs organized by publication type.
- **Talks** - oral presentations, posters, and other scientific presentations.
- **Software** - curated scientific packages and applications with explicit maturity and canonical repository links.
- **Teaching** - structured courses/training and reusable teaching infrastructure.
- **Posts** - tutorials, technical notes, methodological explanations, and reproducible-science guidance.
- **CV** - curriculum vitae and language-specific download layer as files become available.
- **More** - secondary navigation containing **Data Sources**, **Miscellaneous**, and **Contact**.

`/research/` is retained only as a noindex compatibility redirect to the unified Research catalogue at `/projects/`. Retired substantive routes such as `/services/`, `/engagement/`, `/resources/`, `/follow/`, and `/resume/` are no longer rendered as content pages; where useful, noindex redirects preserve older inbound links without exposing the retired material.

## Metadata sources

Canonical academic-profile metadata is maintained in `qselmer/qselmer`.

The website synchronizes only the public metadata required for presentation:

- `assets/data/publications.json`
- `assets/data/research-metrics.json`

The canonical repository catalogue is fetched transiently during automation because it can contain private-repository metadata. Only curated public subsets are written to:

- `assets/data/software.json`
- `assets/data/teaching.json`

Website-specific editorial decisions remain in local registries such as `software/registry.json`, `teaching/registry.json`, `talks/registry.json`, `data/registry.json`, and `blog/registry.json` (public label: **Posts**).

See [`AUTOMATION.md`](AUTOMATION.md) for the complete data flow.

## Local validation

```bash
python scripts/validate_site.py source
quarto render
python scripts/validate_site.py rendered
python scripts/check_external_links.py _site
```

The source validator rejects obsolete Academic Pages/Jekyll runtime paths. The rendered validator checks identity consistency, deterministic generated fragments, CV delivery, compatibility redirects, metadata, sitemap policy, and internal `href`/`src` targets.

## Synchronizing academic-profile metadata

```bash
python scripts/sync_profile.py
```

This synchronizes canonical public profile metadata, derives the curated software/teaching subsets, rebuilds generated fragments, and runs source validation.

## Production deployment

The production site is deployed through GitHub Pages Actions. `.github/workflows/quarto-pages.yml` validates the source, renders the Quarto project, validates the rendered site and external links, uploads `_site`, and deploys it to GitHub Pages on pushes to `master`.

The first Quarto production cutover was deployed from merge commit `0cf243eb7f68e67fe322bb1036e7ac10e97d4f33` by GitHub Actions run `34276777663`.

## Privacy and data policy

Restricted fisheries, biological, institutional, or private-repository metadata is not published through this website. The external Data Sources directory stores discovery metadata and provider links only; it does not mirror third-party datasets.

## Legacy preservation

The final pre-migration Jekyll production snapshot is preserved at:

```text
branch: legacy/jekyll-v0.9
commit: f84307690cc573b7b2e83a548d2d56102a05218d
```

Migration design, route parity, validation, and cutover evidence are documented in [`MIGRATION.md`](MIGRATION.md). Historical attribution is documented in [`NOTICE.md`](NOTICE.md).
