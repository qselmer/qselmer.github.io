# qselmer.github.io

Personal academic website of **Elmer Quispe-Salazar**, implemented with Quarto.

> Migration status: `migration/quarto-v1` is now Quarto-only and remains under final certification. Production `master` still serves the legacy Jekyll implementation until the controlled deployment phase.

## Information architecture

The website is a discovery and presentation layer. Scientific repositories remain the source of truth for code, analyses, manuscripts, software, and teaching materials.

- **Research** - long-term scientific questions and methodological themes.
- **Projects** - active research programmes and manuscript-oriented work.
- **Publications** - formal scholarly outputs; conference outputs are separated.
- **Conferences** - presentations, posters, and explicitly labelled historical conference contributions.
- **Software** - curated scientific packages and applications with explicit maturity.
- **Teaching** - structured courses/training and reusable teaching infrastructure.
- **Data Sources** - curated external sources for students and collaborators; these are not datasets owned or produced by the site author.
- **Blog** - extended educational articles in the pathway `social post -> Blog -> class`.
- **CV / Contact** - professional record and collaboration channels.

Compatibility entry points such as `/resources/`, `/services/`, `/engagement/`, `/follow/`, and `/terms/` are retained as lightweight Quarto pages.

## Metadata sources

Canonical academic-profile metadata is maintained in `qselmer/qselmer`.

The website synchronizes only the public metadata required for presentation:

- `assets/data/publications.json`
- `assets/data/research-metrics.json`

The canonical repository catalogue is fetched transiently during automation because it can contain private-repository metadata. Only curated public subsets are written to:

- `assets/data/software.json`
- `assets/data/teaching.json`

Website-specific editorial decisions remain in local registries such as `software/registry.json`, `teaching/registry.json`, `talks/registry.json`, `data/registry.json`, and `blog/registry.json`.

See [`AUTOMATION.md`](AUTOMATION.md) for the complete data flow.

## Local validation

```bash
python scripts/validate_site.py source
quarto render
python scripts/validate_site.py rendered
```

The source validator rejects obsolete Academic Pages/Jekyll runtime paths. The rendered validator checks identity consistency, deterministic generated fragments, CV delivery, expected compatibility pages, and all internal `href`/`src` targets.

## Synchronizing academic-profile metadata

```bash
python scripts/sync_profile.py
```

This synchronizes canonical public profile metadata, derives the curated software/teaching subsets, rebuilds generated fragments, and runs source validation.

## Privacy and data policy

Restricted fisheries, biological, institutional, or private-repository metadata is not published through this website. The external Data Sources directory stores discovery metadata and provider links only; it does not mirror third-party datasets.

## Legacy preservation

The final pre-migration Jekyll production snapshot is preserved at:

```text
branch: legacy/jekyll-v0.9
commit: f84307690cc573b7b2e83a548d2d56102a05218d
```

Meaningful historical routes and required redirects are inventoried in `config/legacy-routes.json`. Phase 7 certifies those routes before production cutover.

Migration design and checkpoints are documented in [`MIGRATION.md`](MIGRATION.md). Historical attribution is documented in [`NOTICE.md`](NOTICE.md).
