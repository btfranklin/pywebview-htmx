# Development

## Setup And Validation

- Install dependencies: `pdm install`
- Lint: `pdm run lint`
- Test: `pdm run test`
- Run the manual demo: `pdm run python app.py`

Use PDM for dependency and environment management. Do not use pip to add,
remove, or manage project packages. The GitHub Actions bootstrap may install PDM
into a runner, but project dependencies belong in `pyproject.toml` and
`pdm.lock`.

## Package Policy

- Before adding a package, verify the latest version available.
- Use `>=` dependency bounds by default.
- Do not pin to an exact version unless the package requires it for correct
  functionality or reproducible release behavior.

## Release And CI

- Pull requests and pushes to `main` run lint and tests through
  [../.github/workflows/python-package.yml](../.github/workflows/python-package.yml).
- Published GitHub releases build and upload the package through
  [../.github/workflows/python-publish.yml](../.github/workflows/python-publish.yml).
- Versioning is SCM-derived through PDM configuration in
  [../pyproject.toml](../pyproject.toml).

## Local Tooling

Use available CLI tools when they make work more direct:

- `gh` for GitHub issue, PR, release, and workflow inspection.
- `pipx` for isolated command-line Python tools.
- Homebrew-installed commands for local diagnostics.
