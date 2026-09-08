# Website migration: Jekyll -> Quarto

This branch contains the controlled migration of `qselmer.github.io` from Academic Pages/Jekyll to Quarto.

## Governing rules

1. `master` remains the production site until final deployment validation.
2. GitHub repositories remain the scientific source of truth; the website is the discovery and presentation layer.
3. Repository-specific code, analyses, manuscripts, and full teaching content are not duplicated into the website.
4. Publications and research metrics use canonical public metadata from `qselmer/qselmer`.
5. The canonical repository catalogue is used to curate Software and Teaching, but the complete catalogue is never persisted in the public website because it may contain private-repository metadata.
6. Conference records retain ORCID-derived bibliographic identity with website-specific presentation metadata in `talks/registry.json`; legitimate legacy-only conference records are explicitly labelled as historical.
7. Data Sources are external resources for students and collaborators, not datasets owned or produced by Elmer Quispe-Salazar.
8. Blog is the educational communication layer: reader pathway `social post -> Blog -> class`; formal scholarly notes belong in Publications.
9. Contact identity is personal and canonical: `qselmers@gmail.com` and the full LinkedIn profile URL. Legacy institutional contact metadata is not propagated.
10. Homepage ORCID/OpenAlex metrics are displayed as reported and are never manually inflated.
11. Legacy public content is preserved or mapped before its Jekyll source is removed.
12. The pre-migration implementation remains recoverable from `legacy/jekyll-v0.9`.

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
- [x] Phase 6 - remove Academic Pages/Jekyll technical debt.
- [x] Phase 7 - certify URLs, redirects, accessibility, metadata, external links, and responsive layout.
- [ ] Phase 8 - production deployment and default-branch standardization.

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

The final pre-migration Jekyll production state is preserved in branch `legacy/jekyll-v0.9` at commit `f84307690cc573b7b2e83a548d2d56102a05218d` before technical-debt removal.

A final parity inventory identified meaningful residual routes before cleanup. Quarto equivalents were created for `/engagement/`, `/resources/`, `/services/`, `/follow/`, `/terms/`, and the 404 page. A 2022 anchoveta biomass conference contribution that existed only in the legacy `_publications` collection was retained as an explicitly historical Conferences record at `/talks/2022-09-01-anchoveta-biomass-variability/`; no unverified proceedings URL was invented.

`config/legacy-routes.json` separates preserved routes from routes requiring redirects. Phase 7 now generates and certifies those redirects deterministically.

The migration branch no longer contains the Academic Pages/Jekyll runtime or template machinery, including:

- Jekyll `_config*`, `_data`, `_drafts`, `_includes`, `_layouts`, `_pages`, `_posts`, `_projects`, `_publications`, `_sass`, `_software`, and `_talks`;
- Ruby/Bundler and Jekyll Docker development files;
- Academic Pages JavaScript/Node build assets and `package.json`;
- `markdown_generator` template-generation notebooks/scripts;
- the geocoded talk-map notebook, generated map, and workflow;
- obsolete Academic Pages CV conversion utilities and upstream issue/contribution templates.

The retained source is Quarto plus the Python metadata/build pipeline, curated JSON registries/mirrors, site content, images, and CV resources. Source CI rejects reintroduction of the retired legacy paths.

## Phase 7 outcome

Preproduction certification is complete.

- Required legacy redirects are generated deterministically from `config/legacy-routes.json` and validated against the rendered site.
- Current same-site URLs are validated directly against `_site`; historical website routes and project microsites are distinguished from true external URLs.
- Canonical URLs, Open Graph metadata, Twitter cards, `sitemap.xml`, `robots.txt`, and a `noindex` 404 page are present.
- Accessibility checks enforce visible page titles, exactly one `h1` per page, a keyboard skip link, visible focus states, reduced-motion support, image alternative text, iframe titles, and responsive viewport metadata.
- External-link validation blocks confirmed `404`/`410` failures while separately reporting authentication, rate-limit, anti-bot, gateway, TLS, and timeout responses that cannot be conclusively validated from GitHub Actions.
- The certified workflow run rendered successfully and passed source, rendered-site, redirect, SEO/accessibility, internal-link, and external-link checks.
- Independent artefact inspection found **42 HTML pages**, **1,141 internal `href`/`src` references**, **0 missing internal references**, and **0 canonical/H1 semantic anomalies**.
- Secondary layout rendering at **1440 x 900** and **390 x 844** for Home, Data Sources, CV, Contact, and a long Blog page found no obvious content overflow or clipping. The available Chromium runtime was blocked from local navigation by the execution environment, so JavaScript navbar behaviour is not represented as Chrome-certified.

## Remaining work

### Phase 8

Add/verify the production Quarto Pages deployment, merge only after explicit final approval, and standardize the default branch if repository settings permit it. Production `master` remains unchanged until that cutover.
