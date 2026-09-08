# Website migration: Jekyll → Quarto

This branch contains the controlled migration of `qselmer.github.io` from the legacy Academic Pages/Jekyll implementation to Quarto.

## Rules

1. `master` remains the production site until Quarto passes validation.
2. Legacy Jekyll source is retained temporarily in this branch as a migration reference.
3. Quarto renders only explicitly listed `.qmd` files during the transition.
4. Repository-specific scientific content is not duplicated into the website.
5. GitHub repositories remain the source of truth; the website is the discovery and presentation layer.
6. The authoritative publication catalogue is `qselmer/qselmer/assets/data/publications.json`; the website stores only a synchronized mirror and generated presentation fragment.
7. The authoritative repository inventory is `qselmer/qselmer/assets/data/repository-catalog.json`; website registries curate which software and teaching resources are mature enough to present.
8. Teaching content remains in dedicated repositories. Actual activities use `type-training`; the reusable teaching scaffold uses `type-template`.
9. Legacy template files are removed only after URL, content, and build parity are verified.

## Migration phases

- [x] Phase 1 — create isolated migration branch.
- [x] Phase 2 — add minimal Quarto architecture and principal section routes.
- [x] Phase 3 — validate automated Quarto rendering.
- [ ] Phase 4 — migrate project, publication, software, conference, teaching, data, blog, CV, and contact content.
  - [x] Phase 4.1 — migrate and classify all six project records while preserving project URLs.
  - [x] Phase 4.2 — consolidate publications around the profile catalogue and generate the Quarto publication list automatically.
  - [x] Phase 4.3 — curate scientific software from the canonical repository inventory and preserve software maturity boundaries.
  - [x] Phase 4.4 — curate structured teaching activities and teaching infrastructure without duplicating course content into the website.
  - [ ] Phase 4.5 — conferences.
  - [ ] Phase 4.6 — data.
  - [ ] Phase 4.7 — blog / research notes.
  - [ ] Phase 4.8 — CV.
  - [ ] Phase 4.9 — contact.
  - [ ] Phase 4.10 — final homepage integration.
- [ ] Phase 5 — consolidate metadata and automation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt, including the legacy `_publications/` collection and `_data/publications.json` mirror after final parity checks.
- [ ] Phase 7 — validate URLs, accessibility, links, metadata, and mobile layout.
- [ ] Phase 8 — merge to production and standardize the default branch.

## Validation checkpoint

Quarto rendering has been validated successfully through GitHub Actions. The generated preview contains all explicitly rendered pages and passed the current internal-link target check with no missing internal targets. Project migration retains the established `/projects/<slug>/` routes while separating programme-level records from manuscript-oriented projects.

Publication migration uses `qselmer/qselmer/assets/data/publications.json` as the single authoritative catalogue. The website mirror at `assets/data/publications.json` is synchronized weekly, and `publications/_generated.md` is a derived presentation artifact checked by CI. Conference outputs remain in the same canonical dataset but are intentionally rendered under the Conferences section rather than duplicated as formal publications.

Software migration uses the canonical repository inventory plus `software/registry.json` for website-level maturity decisions. Only repositories with defensible public documentation are promoted as scientific software; incubating and concept-stage records remain clearly separated.

Teaching migration follows the same architecture. `teaching/registry.json` currently promotes `git-github-training` as the structured teaching activity and `.template-training` as teaching infrastructure. Practice repositories and clones are not promoted automatically. `bioacoustic-monitoring` is intentionally held for adaptation because its current public README identifies the Climate Change AI tutorial and original authors; it must become a distinct, explicitly attributed class before website promotion.
