# Architecture

`pywebview-htmx` is an in-process HTML fragment runtime for PyWebview apps. It
borrows HTMX-style markup, but there is no HTTP layer: elements call Python
methods through `window.pywebview.api`, and those methods return HTML fragments.

## Boundaries

- Python package helpers live in [../src/pywebview_htmx/runtime.py](../src/pywebview_htmx/runtime.py).
  They load packaged assets, inject runtime/theme markup, encode params, and
  create PyWebview windows.
- The JavaScript runtime lives in
  [../src/pywebview_htmx/static/runtime.js](../src/pywebview_htmx/static/runtime.js).
  It binds `py-call` elements, builds params, invokes Python methods, swaps
  returned fragments, emits lifecycle events, and re-processes dynamic content.
- Theme CSS lives under `src/pywebview_htmx/static/themes/`. `base.css` defines
  shared component tokens and each selectable theme adds overrides.
- The demo app in [../app.py](../app.py) is a manual runtime showcase, not a
  second framework surface. Keep it useful for inspecting interaction behavior.
- Tests in [../tests/](../tests/) guard Python helpers, runtime contract
  fragments, theme behavior, and repository legibility.
- The installable skill in
  [../skills/use-pywebview-htmx/](../skills/use-pywebview-htmx/) is the
  agent-facing usage workflow.

## Contract Sources

- Source code is authoritative for implementation behavior.
- [../README.md](../README.md) is the public, user-facing contract summary.
- Skill references are the compact agent-facing contract:
  [contract.md](../skills/use-pywebview-htmx/references/contract.md),
  [patterns.md](../skills/use-pywebview-htmx/references/patterns.md), and
  [troubleshooting.md](../skills/use-pywebview-htmx/references/troubleshooting.md).

When behavior changes, update source, tests, README, and skill references in the
same pass when each surface is affected.

## Invariants

- Normal app usage should go through `create_window()` so runtime and theme
  injection stay automatic.
- Python API handlers exposed through `js_api` must return HTML strings.
- Returned fragments are inserted directly into the DOM. Escape or sanitize
  untrusted data before interpolating it into markup.
- `data-py-params` is JSON for ordinary elements. Submit-triggered forms merge
  named field values over static params.
- `py-target` selects the swap target. If omitted, the triggering element is
  updated.
- Request state is scoped to the resolved `py-target` when present, and to the
  triggering element otherwise. Shared wait targets keep a separate in-flight
  count for `.py-waiting`.
- `py-swap="outerHTML"` replacements must preserve any selector or `id` that
  future interactions still target.
- Swapped content is re-processed automatically. Manual DOM insertion still
  needs `window.pywebviewHtmx.process(root)`.
