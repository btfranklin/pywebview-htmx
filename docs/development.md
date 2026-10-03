# Development

## Setup And Validation

- Install dependencies: `pdm install`
- Install the Chromium test browser: `pdm run install-browser`
- Lint: `pdm run lint`
- Test: `pdm run test`
- Native bridge smoke test: `pdm run test-native`
- Run the manual demo: `pdm run python app.py`

Use PDM for dependency and environment management. Do not use pip to add,
remove, or manage project packages. GitHub Actions installs PDM with its
official setup action and caches dependencies using `pdm.lock`.

The runtime behavior suite uses real headless Chromium through Playwright.
Browser tests fail rather than skip when Chromium is unavailable, so run the
browser-install command after initial setup and whenever Playwright reports a
missing executable.

The native smoke test needs a local desktop session and a supported PyWebview
renderer. It creates a hidden window, calls a real Python handler, checks the
returned HTML, and checks that a Python exception reaches `py:error`. The
window closes after the check. A failed check exits with an error.
The test deliberately raises a Python exception to check error delivery. Its
expected traceback can appear in the logs.

Run it after changes to window setup or bridge interactions. It is separate
from the headless test suite because CI does not provide a desktop session.

## Package Policy

- Before adding a package, verify the latest version available.
- Use `>=` dependency bounds by default.
- Do not pin to an exact version unless the package requires it for correct
  functionality or reproducible release behavior.

## Release And CI

- Pull requests and pushes to `main` run lint and tests through
  [../.github/workflows/python-package.yml](../.github/workflows/python-package.yml).
- Release preparation and publishing order are documented in
  [releasing.md](releasing.md). Push the version tag first so
  `release-notes-scribe` can draft the GitHub Release notes.
- Published GitHub Releases build and upload the package through
  [../.github/workflows/python-publish.yml](../.github/workflows/python-publish.yml).
- Versioning is SCM-derived through PDM configuration in
  [../pyproject.toml](../pyproject.toml).

## Local Tooling

Use available CLI tools when they make work more direct:

- `gh` for GitHub issue, PR, release, and workflow inspection.
- `pipx` for isolated command-line Python tools.
- Homebrew-installed commands for local diagnostics.
