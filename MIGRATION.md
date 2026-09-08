# Website migration: Jekyll → Quarto

This branch contains the controlled migration of `qselmer.github.io` from Academic Pages/Jekyll to Quarto.

## Governing rules

1. `master` remains the production site until final deployment validation.
2. GitHub repositories remain the scientific source of truth; the website is the discovery and presentation layer.
3. Repository-specific code, analyses, manuscripts, and full teaching content are not duplicated into the website.
4. Publications and research metrics use canonical public metadata from `qselmer/qselmer`.
5. The canonical repository catalogue is used to curate Software and Teaching, but the complete catalogue is never persisted in the public website because it may contain private-repository metadata.
6. Conference records retain ORCID-derived bibliographic identity with website-specific presentation metadata in `talks/registry.json`.
7. Data Sources are external resources for students and collaborators, not datasets owned or produced by Elmer Quispe-Salazar.
8. Blog is the educational communication layer: reader pathway `social post → Blog → class`; formal scholarly notes belong in Publications.
9. Contact identity is personal and canonical: `qselmers@gmail.com` and the full LinkedIn profile URL. Legacy institutional contact metadata is not propagated.
10. Homepage ORCID/OpenAlex metrics are displayed as reported and are never manually inflated.
11. Legacy Jekyll files are removed only after content, URL, build, and deployment parity are demonstrated.

## Migration phases

- [x] Phase 1 — isolated migration branch.
- [x] Phase 2 — Quarto architecture and principal routes.
- [x] Phase 3 — automated Quarto rendering.
- [x] Phase 4 — content migration and homepage integration.
  - [x] 4.1 Projects
  - [x] 4.2 Publications
  - [x] 4.3 Software
  - [x] 4.4 Teaching
  - [x] 4.5 Conferences
  - [x] 4.6 External Data Sources
  - [x] 4.7 Blog teaching funnel
  - [x] 4.8 CV
  - [x] 4.9 Contact
  - [x] 4.10 Final homepage
- [x] Phase 5 — metadata and automation consolidation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt.
- [ ] Phase 7 — certify URLs, redirects, accessibility, metadata, external links, and responsive layout.
- [ ] Phase 8 — production deployment and default-branch standardization.

## Phase 4 outcome

The Quarto information architecture now has independent sections for Research, Projects, Publications, Conferences, Software, Teaching, External Data Sources, Blog, CV, and Contact.

The homepage provides the personal academic identity:

> **Quantitative Marine Ecology & Fisheries Science**

with the signature line:

> **Measure change. Model uncertainty. Inform fisheries decisions.**

Research metrics are generated from the synchronized ORCID/OpenAlex public metric record rather than edited manually.

## Phase 5 outcome

Metadata and automation now have explicit ownership boundaries.

### Canonical external sources

- `qselmer/qselmer/assets/data/publications.json`
- `qselmer/qselmer/assets/data/research-metrics.json`
- `qselmer/qselmer/assets/data/repository-catalog.json`

`config/site.json` records those sources plus canonical identity, local registries, generated artefacts, and synchronization permissions.

The repository catalogue is downloaded once into a temporary directory during `sync_profile.py`; it is **not mirrored into the public website**. Software and Teaching receive only their curated public subsets.

### Consolidated automation

The weekly profile workflow is now `.github/workflows/sync-academic-profile.yml`; the obsolete filename `sync-publications.yml` is retired.

The workflow delegates orchestration to:

- `scripts/sync_profile.py` for synchronization and derivation;
- `scripts/validate_site.py source` for source-state certification;
- `scripts/validate_site.py rendered` for post-render certification.

`quarto-preview.yml` therefore contains only the CI sequence rather than duplicated catalogue and identity checks.

The rendered validator now checks all internal `href` and `src` targets automatically. Zero missing internal links/resources is therefore a CI property rather than a manual checkpoint.

The legacy Jekyll deployment remains available only for production `master` during the migration and no longer runs as a redundant pull-request validator.

## Remaining work

### Phase 6
Remove Jekyll-only collections, layouts, includes, Sass, generator/template residue, legacy metadata mirrors, obsolete talk-map infrastructure, Gem/Bundler dependencies, and other technical debt after a final parity inventory.

### Phase 7
Run full certification for route preservation/redirects, metadata/SEO, accessibility, external links, responsive layouts, and deployment artefact quality.

### Phase 8
Replace the production deployment with Quarto, merge only after final approval, and standardize the default branch if the repository settings permit it.
