# qselmer.github.io

Personal scientific website for Elmer Quispe-Salazar, developed with Jekyll and GitHub Pages.

## Site structure

The website separates stable research themes, concrete projects, formal publications, software and data resources, scientific engagement, curriculum vitae, and contact information.

```text
Research
Projects
Publications
Software & Data
Engagement
CV
Contact
```

## Content collections

- `_projects/`: research programmes with scientific questions, data, methods, status, and expected outputs.
- `_software/`: scientific software and analytical frameworks with explicit development status.
- `_publications/`: curated scholarly outputs.
- `_talks/`: conference presentations, posters, and seminars.
- `_teaching/`: teaching and training activities.
- `_posts/`: research notes and technical articles.

## JavaScript workflow

Install dependencies and run the reproducible build:

```bash
npm ci
npm test
```

`npm test` validates the JavaScript source and regenerates `assets/js/main.min.js`.

## Local Jekyll development

After installing the Ruby dependencies:

```bash
bundle install
bundle exec jekyll serve
```

Changes to `_config.yml` require restarting the Jekyll process.

## Content standards

Project and software records should state their status accurately. Public software releases should include version, source repository, documentation, tests, license, citation metadata, and archived releases where appropriate. Restricted fisheries or institutional data must not be redistributed without authorization.