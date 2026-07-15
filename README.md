# qselmer.github.io

Personal academic website of Elmer Quispe-Salazar, built with Jekyll and deployed through GitHub Pages.

## Local JavaScript build

The JavaScript bundle is generated from the source files in `assets/js/`. Plotly and Mermaid are loaded only on pages that contain those visualizations.

```bash
npm ci
npm test
```

`npm test` checks the JavaScript syntax and rebuilds `assets/js/main.min.js`.

## Local Jekyll preview

```bash
bundle install
bundle exec jekyll serve
```
