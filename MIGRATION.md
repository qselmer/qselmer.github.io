# Website migration: Jekyll → Quarto

This branch contains the controlled migration of `qselmer.github.io` from the legacy Academic Pages/Jekyll implementation to Quarto.

## Rules

1. `master` remains the production site until Quarto passes validation.
2. Legacy Jekyll source is retained temporarily in this branch as a migration reference.
3. Quarto renders only explicitly listed `.qmd` files during the transition.
4. Repository-specific scientific content is not duplicated into the website.
5. GitHub repositories remain the source of truth; the website is the discovery and presentation layer.
6. Publications will be consolidated into one authoritative metadata source.
7. Teaching materials will remain in dedicated `type-training` repositories and may publish their own Quarto/Jupyter documentation.
8. Legacy template files are removed only after URL, content, and build parity are verified.

## Migration phases

- [x] Phase 1 — create isolated migration branch.
- [x] Phase 2 — add minimal Quarto architecture and principal section routes.
- [x] Phase 3 — validate automated Quarto rendering.
- [ ] Phase 4 — migrate project, publication, software, conference, teaching, data, blog, CV, and contact content.
  - [x] Phase 4.1 — migrate and classify all six project records while preserving project URLs.
  - [ ] Phase 4.2 — publications.
  - [ ] Phase 4.3 — software.
  - [ ] Phase 4.4 — teaching.
  - [ ] Phase 4.5 — conferences.
  - [ ] Phase 4.6 — data.
  - [ ] Phase 4.7 — blog / research notes.
  - [ ] Phase 4.8 — CV.
  - [ ] Phase 4.9 — contact.
  - [ ] Phase 4.10 — final homepage integration.
- [ ] Phase 5 — consolidate metadata and automation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt.
- [ ] Phase 7 — validate URLs, accessibility, links, metadata, and mobile layout.
- [ ] Phase 8 — merge to production and standardize the default branch.

## Validation checkpoint

Quarto rendering has been validated successfully through GitHub Actions. The generated preview contains all explicitly rendered pages and passed the current internal-link target check with no missing internal targets. Project migration retains the established `/projects/<slug>/` routes while separating programme-level records from manuscript-oriented projects.
