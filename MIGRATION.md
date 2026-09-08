# Website migration: Jekyll → Quarto

This branch contains the controlled migration of `qselmer.github.io` from the legacy Academic Pages/Jekyll implementation to Quarto.

## Rules

1. `master` remains the production site until Quarto passes validation.
2. Legacy Jekyll source is retained temporarily in this branch as a migration reference.
3. Quarto renders only explicitly listed `.qmd` files during the transition.
4. Repository-specific scientific content is not duplicated into the website.
5. GitHub repositories remain the source of truth; the website is the discovery and presentation layer.
6. The authoritative publication catalogue is `qselmer/qselmer/assets/data/publications.json`; the website stores only a synchronized mirror and generated presentation fragment.
7. The authoritative repository inventory is `qselmer/qselmer/assets/data/repository-catalog.json`; Software uses a small editorial registry to decide which public repositories are mature enough to expose as scientific software.
8. Teaching materials will remain in dedicated `type-training` repositories and may publish their own Quarto/Jupyter documentation.
9. Legacy template files are removed only after URL, content, and build parity are verified.

## Migration phases

- [x] Phase 1 — create isolated migration branch.
- [x] Phase 2 — add minimal Quarto architecture and principal section routes.
- [x] Phase 3 — validate automated Quarto rendering.
- [ ] Phase 4 — migrate project, publication, software, conference, teaching, data, blog, CV, and contact content.
  - [x] Phase 4.1 — migrate and classify all six project records while preserving project URLs.
  - [x] Phase 4.2 — consolidate publications around the profile catalogue and generate the Quarto publication list automatically.
  - [x] Phase 4.3 — audit scientific software, curate mature public tools, preserve legacy software URLs, and automate the software catalogue.
  - [ ] Phase 4.4 — teaching.
  - [ ] Phase 4.5 — conferences.
  - [ ] Phase 4.6 — data.
  - [ ] Phase 4.7 — blog / research notes.
  - [ ] Phase 4.8 — CV.
  - [ ] Phase 4.9 — contact.
  - [ ] Phase 4.10 — final homepage integration.
- [ ] Phase 5 — consolidate remaining metadata and automation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt, including legacy collection records after final parity checks.
- [ ] Phase 7 — validate URLs, accessibility, links, metadata, and mobile layout.
- [ ] Phase 8 — merge to production and standardize the default branch.

## Validation checkpoint

Quarto rendering is validated through GitHub Actions. Project migration retains the established `/projects/<slug>/` routes while separating programme-level records from manuscript-oriented projects.

Publication migration uses `qselmer/qselmer/assets/data/publications.json` as the single authoritative scholarly catalogue. The website mirror at `assets/data/publications.json` is synchronized weekly, and `publications/_generated.md` is a derived presentation artifact checked by CI. Conference outputs remain in the same canonical dataset but are intentionally rendered under the Conferences section rather than duplicated as formal publications.

Software migration uses the profile repository catalogue as the authoritative repository inventory and a website editorial registry only for maturity and inclusion decisions. The primary Software catalogue currently exposes `oceancube` as a stable-source R package and Humboldt Ocean Watch as an experimental application. `seasignals` remains incubating; Pelagytics remains concept-stage; `FisheryClose`, `postHub`, and `fish-byte` are not promoted until their repository-level documentation supports the claim. The established `/software/oceancube/`, `/software/seasignals/`, and `/software/pelagytics/` routes are preserved, and `/software/humboldt-ocean-watch/` is added.

The weekly website synchronization now updates publications and curated software together after the canonical `qselmer/qselmer` profile refresh.
