# qselmer.github.io

Personal academic website of **Elmer Quispe-Salazar**, implemented with Quarto and deployed through GitHub Pages Actions.

> Production status: the controlled migration from Academic Pages/Jekyll to Quarto was completed on 8 September 2026. The production branch is currently `master`; the final pre-migration Jekyll implementation remains preserved at `legacy/jekyll-v0.9`.

## Information architecture

The website is a discovery and presentation layer. Scientific repositories remain the source of truth for code, analyses, manuscripts, software, and teaching materials.

- **Research** - scientific questions and thematic programmes linking canonical project repositories with selected papers, talks, theses, reports, and software.
- **Publications** - formal scholarly outputs; conference outputs are separated.
- **Talks** - conference talks, invited talks and seminars, posters, and workshops when those record types are present.
- **Software** - curated scientific packages and applications with explicit maturity.
- **Teaching** - structured courses/training and reusable teaching infrastructure.
- **Posts** - tutorials, technical notes, methodological explanations, reproducible-science guidance, and an RSS feed.
- **CV** - professional record and current PDF curriculum vitae.
- **More** - curated Data Sources, Miscellaneous material, and Contact.

Legacy routes that no longer belong to the public architecture are retained only as deterministic `noindex` redirects when old inbound links remain meaningful. The retired substantive pages are not rendered as public content.

## Metadata sources

Canonical academic-profile metadata is maintained in `qselmer/qselmer`.

The website synchronizes only the public metadata required for presentation:

- `assets/data/publications.json`
- `assets/data/research-metrics.json`

The canonical repository catalogue is fetched transiently during automation because it can contain private-repository metadata. Only curated public subsets are written to:

- `assets/data/software.json`
- `assets/data/teaching.json`

Website-specific editorial decisions remain in local registries such as `projects/registry.json`, `software/registry.json`, `teaching/registry.json`, `talks/registry.json`, `data/registry.json`, and `blog/registry.json` (public label: **Posts**).

Rendered pages receive canonical URLs, Open Graph/Twitter previews, RSS discovery metadata for Posts, and schema.org JSON-LD for the researcher profile, journal articles, published software, the Git/GitHub course, and technical posts.

See [`AUTOMATION.md`](AUTOMATION.md) for the complete data flow.

## Local validation

```bash
python scripts/build_publications.py
python scripts/build_conferences.py
python scripts/build_software.py
python scripts/build_teaching.py
python scripts/build_data_resources.py
python scripts/build_blog.py
python scripts/build_research_graph.py
python scripts/build_projects.py
python scripts/build_home.py
python scripts/validate_site.py source
quarto render
python scripts/validate_site.py rendered
python scripts/check_external_links.py _site
```

The source validator rejects obsolete Academic Pages/Jekyll runtime paths. The rendered validator checks identity consistency, deterministic generated fragments, CV delivery, compatibility redirects, metadata, and internal `href`/`src` targets.

## Synchronizing academic-profile metadata

```bash
python scripts/sync_profile.py
```

This synchronizes canonical public profile metadata, derives the curated software/teaching subsets, rebuilds generated fragments, and runs source validation.

## Production deployment

The production site is deployed through GitHub Pages Actions. `.github/workflows/quarto-pages.yml` rebuilds deterministic catalogue fragments, validates the source, synchronizes canonical visual assets, renders the Quarto project, validates the rendered site and external links, uploads `_site`, and deploys it to GitHub Pages on pushes to `master`.

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
