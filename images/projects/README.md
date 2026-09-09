# Project logo mirrors

Project cards use only the canonical logo maintained by each source repository. This website does not design, infer, or substitute project marks.

## Source convention

The synchronization checks the source paths declared in `projects/registry.json`. The standard candidates are:

```text
assets/images/logo.svg
assets/images/logo.png
```

The first canonical file found is mirrored verbatim into a stable project directory:

```text
images/projects/<project-slug>/logo.svg
images/projects/<project-slug>/logo.png
```

Only one mirrored logo is retained for a project. If the accessible source repository no longer contains a canonical logo, the mirror is removed and the project card returns to an empty visual slot.

## Automation

`scripts/sync_project_logos.py` performs the cross-repository mirror and `scripts/build_projects.py` regenerates `projects/_generated.md`. The weekly academic-profile workflow runs both tasks.

Private source repositories require a GitHub token with read access to those repositories. The synchronizer checks `PROJECT_REPO_TOKEN`, then `PROFILE_REPO_TOKEN`, then `GITHUB_TOKEN`. The website repository's normal `GITHUB_TOKEN` can write synchronized files here but does not, by itself, grant read access to other private repositories.

The repository logo remains the source of truth; this directory contains only the web mirror used by the public project cards.
