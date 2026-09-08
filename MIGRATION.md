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
9. Conference outputs retain ORCID-derived bibliographic identity; `talks/registry.json` adds only presentation-level metadata and stable routes.
10. The Data section is an external-source directory for students and collaborators. `data/registry.json` contains discovery metadata only; no listed dataset is presented as owned or produced by Elmer Quispe-Salazar.
11. The Blog is a teaching-communication layer: the audience pathway is social post → Blog → class, while content production should normally proceed class/theme → Blog → social post. New Blog articles require an explicit link to a published class; migrated legacy articles may be retained as documented exceptions until the class exists.
12. Formal scholarly outputs and citable scientific notes belong in Publications, not in the Blog.
13. Contact identity follows the currently maintained public `qselmer/qselmer` profile: `qselmers@gmail.com` is the personal collaboration address and the full LinkedIn profile slug is canonical. Legacy institutional email and obsolete LinkedIn metadata are not propagated into the Quarto site.
14. Legacy template files are removed only after URL, content, and build parity are verified.

## Migration phases

- [x] Phase 1 — create isolated migration branch.
- [x] Phase 2 — add minimal Quarto architecture and principal section routes.
- [x] Phase 3 — validate automated Quarto rendering.
- [ ] Phase 4 — migrate project, publication, software, conference, teaching, data, blog, CV, and contact content.
  - [x] Phase 4.1 — migrate and classify all six project records while preserving project URLs.
  - [x] Phase 4.2 — consolidate publications around the profile catalogue and generate the Quarto publication list automatically.
  - [x] Phase 4.3 — curate scientific software from the canonical repository inventory and preserve software maturity boundaries.
  - [x] Phase 4.4 — curate structured teaching activities and teaching infrastructure without duplicating course content into the website.
  - [x] Phase 4.5 — reconcile all conference outputs with ORCID and preserve conference routes.
  - [x] Phase 4.6 — replace the ambiguous data-product concept with a curated external data-source directory for students and collaborators.
  - [x] Phase 4.7 — define Blog as the social → extended article → class pathway, migrate the legacy statistical-distributions article, and enforce class linkage for new posts.
  - [x] Phase 4.8 — retain the detailed PDF as the canonical CV while converting `/cv/` into a navigable professional landing page and preserving `/resume/`.
  - [x] Phase 4.9 — consolidate personal contact identity, collaboration scope, and verified academic/professional profiles without using a third-party contact form.
  - [ ] Phase 4.10 — final homepage integration.
- [ ] Phase 5 — consolidate metadata and automation.
- [ ] Phase 6 — remove Academic Pages/Jekyll technical debt, including legacy `_publications/`, `_talks/`, `_posts/`, `_data/publications.json`, `_data/data_resources.yml`, and obsolete Jekyll contact configuration after final parity checks.
- [ ] Phase 7 — validate URLs, accessibility, links, metadata, and mobile layout.
- [ ] Phase 8 — merge to production and standardize the default branch.

## Validation checkpoint

Quarto rendering has been validated successfully through GitHub Actions. The generated preview contains all explicitly rendered pages and passed the current internal-link target check with no missing internal targets. Project migration retains the established `/projects/<slug>/` routes while separating programme-level records from manuscript-oriented projects.

Publication migration uses `qselmer/qselmer/assets/data/publications.json` as the single authoritative catalogue. The website mirror at `assets/data/publications.json` is synchronized weekly, and `publications/_generated.md` is a derived presentation artifact checked by CI. Conference outputs remain in the same canonical dataset but are intentionally rendered under the Conferences section rather than duplicated as formal publications.

Software migration uses the canonical repository inventory plus `software/registry.json` for website-level maturity decisions. Only repositories with defensible public documentation are promoted as scientific software; incubating and concept-stage records remain clearly separated.

Teaching migration follows the same architecture. `teaching/registry.json` currently promotes `git-github-training` as the structured teaching activity and `.template-training` as teaching infrastructure. Practice repositories and clones are not promoted automatically. `bioacoustic-monitoring` is intentionally held for adaptation because its current public README identifies the Climate Change AI tutorial and original authors; it must become a distinct, explicitly attributed class before website promotion.

Conference migration reconciles every `Conference outputs` record in the synchronized publication catalogue against `talks/registry.json`. The two SPF-2026 legacy records preserve their established routes and presentation metadata; the 2024 VI SIBECORP contribution receives a stable route. `assets/data/conferences.json` and `talks/_generated.md` are deterministic derivatives checked by CI, so new ORCID conference outputs cannot silently disappear from the website catalogue.

Data migration now defines `/data/` exclusively as a curated directory of external sources for students and collaborators. `data/registry.json` contains 29 reviewed resources across fisheries, biodiversity, oceanography, satellite/reanalysis/climate, bathymetry/geospatial, Peru-specific public data, and licensed/commercial sources. The site does not mirror or claim ownership of these datasets. `data/_generated.md` is deterministic and checked by CI.

Blog migration now separates communication from scholarship. `blog/registry.json` records extended articles and their class relationship; `scripts/build_blog.py` rejects new non-legacy posts that are not linked to a published class. The established `/blog/statistical-distributions-fisheries-marine-ecology/` route is preserved as a `legacy-adapted` exception because no structured class for that topic is currently published. Social-media posts remain distribution entry points rather than website publication records, and formal scientific notes remain under Publications.

CV migration keeps `files/CV.pdf` as the authoritative detailed curriculum vitae while `/cv/` acts as a professional discovery page linked to the site catalogues. `/resume/` is preserved as a compatibility route, and CI verifies both routes plus the rendered PDF resource.

Contact migration uses the maintained public profile as the identity source for personal collaboration contact. The Quarto Contact page exposes `qselmers@gmail.com`, ORCID, Google Scholar, Web of Science, ResearchGate, GitHub, LinkedIn, and X; it clearly states that the website is personal rather than an institutional communication channel. The unused FormSubmit configuration remains only as legacy Jekyll material until Phase 6 and is not rendered or used by Quarto.
