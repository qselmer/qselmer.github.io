# Automation architecture

The website uses canonical scholarly sources, curated public registries, and deterministic builders. Phase 7 adds a **Unified Scholarly Graph** that connects the public research ecosystem without turning the website into a second source of truth.

## Data flow

```text
qselmer/qselmer
│
├── publications.json ────────────────→ assets/data/publications.json
│                                         ├── publications/_generated.md
│                                         └── conferences + talks/_generated.md
│
├── research-metrics.json ────────────→ assets/data/research-metrics.json
│                                         └── includes/profile-sidebar.html
│
└── repository-catalog.json ──────────→ temporary runtime file only
                                          ├── software/registry.json
                                          │      ↓
                                          │  assets/data/software.json
                                          │      ↓
                                          │  software/_generated.md
                                          │
                                          └── teaching/registry.json
                                                 ↓
                                             assets/data/teaching.json
                                                 ↓
                                             teaching/_generated.md

Public mirrors + curated registries
│
├── projects/registry.json
├── graph/registry.json
├── assets/data/publications.json
├── assets/data/conferences.json
├── assets/data/software.json
├── assets/data/teaching.json
├── blog/registry.json
└── assets/data/research-metrics.json
          ↓
 scripts/build_scholarly_graph.py
          ↓
 assets/data/scholarly-graph.json
          ├── research-graph/_generated.md → /research-graph/
          └── includes/about-selected.html → About / Selected research
```

The repository catalogue is **not committed as a website mirror** because the canonical catalogue can contain private-repository metadata. `scripts/sync_profile.py` downloads it once into a temporary directory and exposes only curated public subsets.

## Unified Scholarly Graph

`assets/data/scholarly-graph.json` is the Phase 7 public relationship layer. It does not replace the domain catalogues. Instead, it gives public entities stable IDs and connects them through typed relations.

Current public node classes include:

- Person;
- Theme;
- Project;
- Repository;
- Publication;
- Talk and Poster;
- Software;
- Teaching;
- Post.

Examples of typed relations include `part_of_theme`, `contributes_to_theme`, `repository_for`, `implemented_in`, and `created_by`. Explicit project-output relations can be added to `graph/registry.json` when a relationship is supported by the underlying records; the builder does not invent unsupported links.

### Stable identifiers and provenance

The graph uses deterministic IDs such as:

```text
person:elmer-quispe-salazar
project:stock-assessment-misspecification
publication:doi:10.3989/scimar.05636.117
software:github:qselmer/oceancube
talk:2026-05-06:<normalized-title>
post:statistical-distributions-fisheries-marine-ecology
```

Every public node also records its canonical URL and provenance source. DOI duplication, dangling edges, invalid canonical URLs, missing featured nodes, and unsupported relation types are rejected by Phase 7 validation.

## Public/private firewall

`graph/registry.json` contains an explicit `public_repositories` allowlist. Repository identifiers and repository nodes can enter `assets/data/scholarly-graph.json` only when they are on this list.

This provides two independent privacy boundaries:

1. the raw canonical repository catalogue is handled only as a temporary runtime file and is never serialized to the website; and
2. the public graph accepts repository metadata only from explicitly approved public repositories.

Private project repositories may still back a public project description, but their repository name or GitHub URL is not serialized into the public graph. If a private/non-approved repository would be exposed directly by a project URL, the graph build fails.

## Canonical configuration

`config/site.json` centralizes:

- public identity fields;
- canonical profile repository and source paths;
- forbidden legacy identity values;
- website mirrors and registries;
- derived JSON artefacts;
- generated fragments;
- files that the synchronization workflow is allowed to commit.

`scripts/site_config.py` is the shared accessor used by synchronization and validation code.

## Orchestrators

### `scripts/sync_profile.py`

Runs the complete profile-derived update:

1. synchronize publications;
2. synchronize research metrics;
3. fetch the canonical repository catalogue once to a temporary file;
4. derive the curated public Software and Teaching subsets;
5. synchronize canonical public visual assets;
6. rebuild all domain catalogues;
7. build the thematic Research layer;
8. build the Unified Scholarly Graph;
9. rebuild Research and About from the resulting relationship layers;
10. run source and Phase 7 graph validation.

Individual sync/build scripts remain executable for debugging and targeted maintenance.

### `scripts/validate_site.py`

Two validation modes are supported.

```bash
python scripts/validate_site.py source
python scripts/validate_site.py rendered
```

`source` validates canonical identity consistency, JSON catalogues and registries, ORCID consistency, deterministic generated fragments, the canonical CV resource, and absence of known legacy identity values.

`rendered` validates homepage identity and metrics, CV and compatibility routes, canonical Contact identity, rendered CV integrity, metadata/accessibility rules, and every internal HTML `href` and `src` target.

### `scripts/validate_phase7.py`

Phase 7 adds an explicit graph certification layer:

```bash
python scripts/validate_phase7.py source
python scripts/validate_phase7.py rendered
```

The source check certifies stable unique node IDs, DOI uniqueness, absolute canonical URLs, valid typed edges, the repository allowlist, the public/private firewall, graph statistics, and the generated Research Graph fragment. The rendered check certifies both `/research-graph/` and the machine-readable `/assets/data/scholarly-graph.json` resource.

## GitHub Actions

### `sync-academic-profile.yml`

Runs weekly after the profile repository refresh and can also be dispatched manually. It calls `python scripts/sync_profile.py`. The list of files that the bot may commit comes from `config/site.json` via `python scripts/site_config.py tracked`.

### `quarto-preview.yml`

For pull requests to production:

```text
rebuild domain catalogues
      ↓
build Unified Scholarly Graph
      ↓
source + Phase 7 validation
      ↓
Quarto render
      ↓
rendered-site + Phase 7 validation
      ↓
external-link validation
      ↓
preview artifact
```

### `quarto-pages.yml`

For pushes to production `master`, the same validation chain is followed by upload and deployment to GitHub Pages.

## Public outputs

Phase 7 publishes two complementary interfaces:

- `/research-graph/` — human-readable navigation through themes, projects, repositories, and outputs;
- `/assets/data/scholarly-graph.json` — machine-readable public graph for future derived pages, search, visualizations, feeds, and other academic products.

About / `Selected research` is now selected by stable graph IDs rather than by independent catalogue heuristics.

## Legacy preservation

The retired Academic Pages/Jekyll implementation is preserved only in branch `legacy/jekyll-v0.9`; it does not participate in current validation or deployment.
