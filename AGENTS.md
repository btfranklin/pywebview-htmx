# Agent Map

Use this file as the fast route into the repository. Keep durable details in
`docs/` and keep this file short.

## Start Here

- User-facing overview and API examples: [README.md](README.md)
- Maintainer and agent docs index: [docs/index.md](docs/index.md)
- Python package helpers: [src/pywebview_htmx/runtime.py](src/pywebview_htmx/runtime.py)
- JavaScript runtime: [src/pywebview_htmx/static/runtime.js](src/pywebview_htmx/static/runtime.js)
- Manual runtime showcase: [app.py](app.py)
- Test suite: [tests/](tests/)
- Package and tool config: [pyproject.toml](pyproject.toml)
- Installable coding-agent skill: [skills/use-pywebview-htmx/](skills/use-pywebview-htmx/)

## Development Rules

- Use PDM for dependency and environment management. Do not use pip to add,
  remove, or manage project packages.
- When adding dependencies, verify the latest available package version first
  and use a `>=` bound unless a strict pin is technically required.
- Useful local tools may include `gh`, `pipx`, and Homebrew-installed commands.
  Prefer them when they make inspection or release work more direct.
- Preserve existing worktree changes. Do not revert unrelated edits.

## Validation

- Install dependencies: `pdm install`
- Lint: `pdm run lint`
- Test: `pdm run test`
- Run the demo: `pdm run python app.py`

## Collaboration

Be direct and concrete. Match the surrounding communication style, explain
tradeoffs when they matter, and keep repo-facing changes public-friendly.
