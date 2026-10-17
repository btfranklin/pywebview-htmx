# Development

## Setup And Validation

- Install dependencies: `pdm install`
- Install Chromium and WebKit: `pdm run install-browser`
- All checks: `pdm run check`
- Offline documentation check: `pdm run check-docs` (requires the native `perfect-doc` executable)
- Lint: `pdm run lint`
- Test: `pdm run test`
- Native bridge smoke test: `pdm run test-native`
- Run the manual demo: `pdm run python app.py`

Use PDM for dependency and environment management. Do not use pip to add,
remove, or manage project packages. GitHub Actions installs PDM with its
official setup action and caches dependencies using `pdm.lock`.

The runtime behavior suite uses real headless Chromium and WebKit through
Playwright. Browser tests fail rather than skip when an engine is unavailable. Run the
browser-install command after initial setup and whenever Playwright reports a
missing executable.

The native smoke test needs a local desktop session and a supported PyWebview
renderer. It creates a hidden window and checks real Python calls, form parameters,
request ordering, dynamic controls, themes, busy state, and exception delivery. The
window closes after the check. A failed check exits with an error.
The test deliberately raises a Python exception to check error delivery. Its
expected traceback can appear in the logs.

Run it after changes to window setup or bridge interactions. It is separate
from the headless suite. CI runs it against the built wheel in macOS WKWebView,
Windows WebView2, and Linux Qt under Xvfb. Browser-engine tests do not replace
these native bridge checks.

## Package Policy

- Before adding a package, verify the latest version available.
- Use `>=` dependency bounds by default.
- Do not pin to an exact version unless the package requires it for correct
  functionality or reproducible release behavior.

## Release And CI

- Pull requests and pushes to `main` run lint, both browser engines, offline
  documentation checks, installed-distribution checks, and native bridge checks through
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

## Installed Distribution Checks

Run `pdm build`, then `pdm run check-dist dist`. The directory must contain one
wheel and one source archive with the same package version. Each artifact is
installed with PDM in a temporary project outside this checkout. The check
reads every bundled theme, the runtime, and the typing marker, then exercises
HTML injection and parameter encoding. The temporary projects are removed.

Run `pdm run check-dist dist --native` in a desktop session to check the installed
wheel through a real bridge. On Linux this command installs the existing
PyWebview dependency's `pyside6` extra in the temporary project. It needs Qt
system libraries and a display; CI supplies Xvfb. It does not add GUI packages
to the main project environment.

`pdm run check` includes the offline Perfect Doc check. Install the native
[Perfect Doc executable](https://github.com/btfranklin/perfect-doc/releases)
on your PATH first. CI uses a checksum-verified Linux release. The repository's
`perfect-doc.toml` keeps GitHub Markdown anchors and local file links.
