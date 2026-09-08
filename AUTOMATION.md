# Automation architecture

The website uses a deliberately small automation surface. Canonical academic metadata is maintained in the profile repository; the website stores only safe public mirrors, curated derivatives, and deterministic presentation fragments.

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
```

The repository catalogue is **not committed as a website mirror** because the canonical catalogue can contain private-repository metadata. `scripts/sync_profile.py` downloads it once into a temporary directory and exposes only curated public subsets.

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
4. derive the public software subset;
5. derive the public teaching subset;
6. rebuild Publications, Conferences, Software, Teaching, and the global profile sidebar;
7. run source validation.

Individual sync/build scripts remain executable for debugging and targeted maintenance.

### `scripts/validate_site.py`

Two validation modes are supported.

```bash
python scripts/validate_site.py source
python scripts/validate_site.py rendered
```

`source` validates canonical identity consistency, JSON catalogues and registries, ORCID consistency, deterministic generated fragments, the canonical CV resource, and absence of known legacy identity values.

`rendered` validates homepage identity and metrics, CV and `/resume/` compatibility, canonical Contact identity, rendered CV integrity, metadata/accessibility rules, and every internal HTML `href` and `src` target.

## GitHub Actions

### `sync-academic-profile.yml`

Runs weekly after the profile repository refresh and can also be dispatched manually. It calls `python scripts/sync_profile.py`. The list of files that the bot may commit comes from `config/site.json` via `python scripts/site_config.py tracked`.

### `quarto-preview.yml`

For pull requests to production:

```text
source validation
      ↓
Quarto render
      ↓
rendered-site validation
      ↓
external-link validation
      ↓
preview artifact
```

### `quarto-pages.yml`

For pushes to production `master`, the same validation chain is followed by upload and deployment to GitHub Pages.

## Legacy preservation

The retired Academic Pages/Jekyll implementation is preserved only in branch `legacy/jekyll-v0.9`; it does not participate in current validation or deployment.
