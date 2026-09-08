# Website migration: Jekyll -> Quarto

This document records the controlled migration of `qselmer.github.io` from Academic Pages/Jekyll to Quarto and the production cutover completed on 8 September 2026.

## Governing rules

1. GitHub repositories remain the scientific source of truth; the website is the discovery and presentation layer.
2. Repository-specific code, analyses, manuscripts, and full teaching content are not duplicated into the website.
3. Publications and research metrics use canonical public metadata from `qselmer/qselmer`.
4. The canonical repository catalogue is used to curate Software and Teaching, but the complete catalogue is never persisted in the public website because it may contain private-repository metadata.
5. Conference records retain ORCID-derived bibliographic identity with website-specific presentation metadata in `talks/registry.json`; legitimate legacy-only conference records are explicitly labelled as historical.
6. Data Sources are external resources for students and collaborators, not datasets owned or produced by Elmer Quispe-Salazar.
7. Blog is the educational communication layer: reader pathway `social post -> Blog -> class`; formal scholarly notes belong in Publications.
8. Contact identity is personal and canonical: `qselmers@gmail.com` and the full LinkedIn profile URL. Legacy institutional contact metadata is not propagated.
9. Homepage ORCID/OpenAlex metrics are displayed as reported and are never manually inflated.
10. Legacy public content is preserved or mapped before its Jekyll source is removed.
11. The pre-migration implementation remains recoverable from `legacy/jekyll-v0.9`.

## Migration phases

- [x] Phase 1 - isolated migration branch.
- [x] Phase 2 - Quarto architecture and principal routes.
- [x] Phase 3 - automated Quarto rendering.
- [x] Phase 4 - content migration and homepage integration.
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
- [x] Phase 5 - metadata and automation consolidation.
- [x] Phase 6 - Academic Pages/Jekyll technical-debt retirement.
- [x] Phase 7 - URLs, redirects, accessibility, metadata, external links, and responsive-layout certification.
- [x] Phase 8 - production cutover to Quarto on GitHub Pages.

## Phase 4 outcome

The Quarto information architecture has independent sections for Research, Projects, Publications, Conferences, Software, Teaching, External Data Sources, Blog, CV, and Contact.

The homepage identity is **Quantitative Marine Ecology & Fisheries Science** with the signature **Measure change. Model uncertainty. Inform fisheries decisions.** Research metrics are generated from synchronized ORCID/OpenAlex public metadata rather than edited manually.

## Phase 5 outcome

Metadata and automation have explicit ownership boundaries. Canonical sources are:

- `qselmer/qselmer/assets/data/publications.json`
- `qselmer/qselmer/assets/data/research-metrics.json`
- `qselmer/qselmer/assets/data/repository-catalog.json`

`config/site.json` records sources, canonical identity, local registries, generated artefacts, and synchronization permissions. The repository catalogue is downloaded transiently and is not mirrored into the public website.

The weekly profile workflow is `.github/workflows/sync-academic-profile.yml`. `scripts/sync_profile.py` orchestrates synchronization and derivation; `scripts/validate_site.py` certifies source and rendered states. Internal `href` and `src` validation is a permanent CI check.

## Phase 6 outcome

The final pre-migration Jekyll production state is preserved in branch `legacy/jekyll-v0.9` at commit `f84307690cc573b7b2e83a548d2d56102a05218d`.

A final parity inventory identified meaningful residual routes before cleanup. Quarto equivalents were created for `/engagement/`, `/resources/`, `/services/`, `/follow/`, `/terms/`, and the 404 page. A 2022 anchoveta biomass conference contribution that existed only in the legacy `_publications` collection was retained as an explicitly historical Conferences record at `/talks/2022-09-01-anchoveta-biomass-variability/`; no unverified proceedings URL was invented.

`config/legacy-routes.json` separates preserved routes from routes requiring redirects.

The production source no longer contains the Academic Pages/Jekyll runtime or template machinery, including Jekyll collections/configuration, layouts/includes/Sass, Ruby/Bundler, Docker legacy, Academic Pages JavaScript/Node assets, `markdown_generator`, legacy CV utilities, and talk-map machinery. Source CI rejects reintroduction of retired legacy paths.

## Phase 7 outcome

Phase 7 was certified on commit `323a338507ac741b9314df00e2ad38ce0dcf8fa1`.

Certification covers deterministic legacy redirects, current and historical route handling, canonical URLs, Open Graph/Twitter metadata, sitemap/robots, 404 `noindex`, one visible `h1` per page, keyboard skip link/focus states, reduced motion, image alternative text, iframe titles, responsive viewport structure, internal-link validation, and external-link auditing with confirmed GET `404`/`410` treated as blocking failures.

Final Phase 7 workflow run `34272945869` completed successfully. The independent preproduction artifact audit found 42 HTML pages, 1,141 internal `href/src` references, 0 missing internal references, and 0 canonical/H1 anomalies.

## Phase 8 outcome

The user explicitly authorized the production cutover. PR #26 was merged with exact head-SHA protection into `master`.

Production merge commit:

```text
0cf243eb7f68e67fe322bb1036e7ac10e97d4f33
```

The Jekyll deployment workflow was replaced by `.github/workflows/quarto-pages.yml`. The production workflow validates source state, renders Quarto, validates the rendered site and external links, uploads `_site` as the GitHub Pages artifact, and deploys with `actions/deploy-pages`.

First Quarto production deployment:

```text
GitHub Actions run: 34276777663
Result: SUCCESS
Pages URL: https://qselmer.github.io/
Pages artifact: 10076025275
Artifact digest: sha256:b2298c715ace67b1e2af381defe67aaddb9b89bd3256ca1a0ed25102cfce4b25
```

The GitHub Pages deployment log reports success for build version `0cf243eb7f68e67fe322bb1036e7ac10e97d4f33` and evaluates the environment URL as `https://qselmer.github.io/`.

The exact deployed artifact was independently audited: 42 HTML pages and 1,140 internal `href/src` references with 0 missing. The home page, Data Sources, Contact, sitemap, robots file, and representative legacy redirects are present in the deployed artifact.

Direct HTTP retrieval of the public domain could not be independently repeated from the execution sandbox because its DNS/network policy did not resolve `qselmer.github.io`; therefore no browser/network verification is claimed beyond GitHub Pages' successful deployment status and inspection of the exact deployed artifact.

### Branch state after cutover

- `master` - active Quarto production/default branch.
- `legacy/jekyll-v0.9` - immutable pre-migration Jekyll rollback snapshot.
- `migration/quarto-v1` - retained migration history/candidate branch.

The repository currently uses `master` as its default branch. Standardizing the branch name to `main` is an optional administrative follow-up and is deliberately not simulated by creating a parallel branch: the available GitHub connector can read `default_branch` but does not expose the repository-settings mutation required to change it safely.

## Migration status

**COMPLETE.** The website source, validation pipeline, and GitHub Pages production deployment are now Quarto-based. The preserved legacy branch provides a rollback/reference snapshot without participating in deployment.
