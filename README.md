# qselmer.github.io

Personal academic website of Elmer Quispe-Salazar, built with Jekyll and deployed through GitHub Pages.

## Scientific information architecture

The site separates stable research themes from concrete projects and scholarly outputs:

- `Research`: long-term scientific questions and methodological themes.
- `Projects`: active and completed research programmes.
- `Publications`: verified peer-reviewed, conference, and technical outputs.
- `Software & Data`: software under development, reproducible workflows, and curated data resources.
- `Engagement`: talks, teaching, and research notes.
- `CV` and `Contact`: professional record and collaboration channels.

## Collections

- `_projects/`: project records with questions, data, methods, status, and outputs.
- `_publications/`: verified scholarly records only.
- `_software/`: software records with transparent development status.
- `_talks/`: presentations and posters.
- `_teaching/`: teaching and training activities.

## Publication policy

Publication pages are included only when authorship, title, year, output type, and citation status can be verified. DOI, PDF, code, data, and presentation links are added only when stable public locations exist. Works in preparation are not represented as publications.

## Software and data policy

Software records must distinguish clearly among concept, prototype, active development, internal use, and public release. Repository, version, DOI, citation, and license fields are added only after they exist.

Restricted fisheries, biological, or institutional datasets are never published through this repository. Public pages may describe metadata, analytical structure, derived products, or synthetic examples without exposing protected information.

## Local JavaScript build

The JavaScript bundle is generated from the source files in `assets/js/`. Plotly and Mermaid are loaded only on pages that contain those visualizations.

```bash
npm ci
npm test
```

`npm test` checks JavaScript syntax and rebuilds `assets/js/main.min.js`.

## Local Jekyll preview

```bash
bundle install
bundle exec jekyll serve
```

Changes to `_config.yml` require restarting the Jekyll server.