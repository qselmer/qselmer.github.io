# Project logo mirrors

Project cards must use the canonical logo maintained by the source repository. Do not design substitute marks in this website repository.

## Source convention

Preferred source paths in each project repository:

```text
assets/images/logo.svg
assets/images/logo.png
```

Mirror the selected logo into this directory using a stable project slug, for example:

```text
images/projects/stock-assessment-misspecification/logo.png
images/projects/season-benchmarking/logo.svg
images/projects/pelagic-fishery-reorganization/logo.png
images/projects/fishcore/logo.svg
```

Then add the matching `<div class="qs-project-visual"><img class="qs-project-logo" ...></div>` block to `projects/index.qmd`.

The repository logo remains the source of truth; this directory stores only the web-safe mirror used by the public personal website.
