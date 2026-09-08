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
- [ ] Phase 3 — validate automated Quarto rendering.
- [ ] Phase 4 — migrate project, publication, software, conference, teaching, data, blog, CV, and contact content.
- [ ] Phase 5 — consolidate metadata and automation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt.
- [ ] Phase 7 — validate URLs, accessibility, links, metadata, and mobile layout.
- [ ] Phase 8 — merge to production and standardize the default branch.
