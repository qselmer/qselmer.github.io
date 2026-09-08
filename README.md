# qselmer.github.io

Personal academic website of **Elmer Quispe-Salazar**, implemented with Quarto.

> Migration status: the Quarto site is being validated on `migration/quarto-v1`. The legacy Jekyll site remains the production implementation on `master` until the final deployment phase.

## Information architecture

The website is a discovery and presentation layer. Scientific repositories remain the source of truth for code, analyses, manuscripts, software, and teaching materials.

- **Research** — long-term scientific questions and methodological themes.
- **Projects** — active research programmes and manuscript-oriented work.
- **Publications** — formal scholarly outputs; conference outputs are separated.
- **Conferences** — presentations, posters, and historical conference contributions.
- **Software** — curated scientific packages and applications with explicit maturity.
- **Teaching** — structured courses/training and reusable teaching infrastructure.
- **Data Sources** — curated external data sources for students and collaborators; these are not datasets owned or produced by the site author.
- **Blog** — extended educational articles in the pathway `social post → Blog → class`.
- **CV / Contact** — professional record and collaboration channels.

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

The rendered validator checks identity consistency, deterministic generated fragments, CV delivery, and all internal `href`/`src` targets.

## Synchronizing academic-profile metadata

```bash
python scripts/sync_profile.py
```

This synchronizes the canonical public profile metadata, derives the curated software/teaching subsets, rebuilds generated fragments, and runs source validation.

## Privacy and data policy

Restricted fisheries, biological, institutional, or private-repository metadata is not published through this website. The external Data Sources directory stores discovery metadata and provider links only; it does not mirror third-party datasets.

## Migration

Migration design and checkpoints are documented in [`MIGRATION.md`](MIGRATION.md).
