# Pywebview Htmx Contract

Use this file when you need the exact interaction model without reopening the full
library sources.

## Mental model

- `pywebview-htmx` finds elements with `py-call`.
- It binds an event listener. Default trigger is `click`.
- It calls `window.pywebview.api[method](params)`.
- It expects the Python method to return an HTML string fragment.
- It swaps that fragment into the DOM.

This is HTMX-like in markup style, but it is not an HTTP request/response system.

## Python surface

- `create_window(title, html, js_api=None, theme="aurora", start=True, **kwargs)`
- `get_runtime_script()`
- `inject_runtime(html)`
- `encode_params_attr(params)`
- `list_themes()`
- `get_theme_css(theme)`
- `inject_theme(html, theme)`
- `DEFAULT_THEME`

Normal app usage should go through `create_window()`.

## Declarative attributes

- `py-call`: required method name
- `py-trigger`: optional event name; default `click`
- `data-py-params`: optional JSON payload
- `py-target`: optional CSS selector for the swap target
- `py-swap`: `innerHTML`, `outerHTML`, or `append`
- `py-wait`: optional selector for the loading-state target
- `py-policy`: optional per-element request policy override, `latest-wins` or `drop`

If `py-target` is omitted, the triggering element is the target.
If `py-wait` is missing, empty, invalid, or unresolved, the triggering element
receives `.py-waiting`.

## Params contract

- Missing `data-py-params` becomes `{}`.
- Invalid JSON logs an error and becomes `{}`.
- `<form py-trigger="submit">` serializes named fields automatically.
- Form values merge over any static `data-py-params`.
- Repeated form field names accumulate into arrays.
- File inputs are skipped with a warning.

Use `encode_params_attr(...)` when Python emits `data-py-params` into HTML.

## Runtime config

Available on `window.pywebviewHtmx.config`:

- `defaultSwapStyle`
- `swapDelay`
- `settleDelay`
- `requestPolicy`

Global config is the default. `py-policy` overrides request behavior for a single
element.

Request state is scoped to the resolved `py-target` when present, and to the
triggering element otherwise. Controls that target the same element coordinate
`latest-wins` and `drop` behavior. Loading state is counted separately per
resolved `py-wait` target.

## Events

- `py:trigger`
- `py:beforeSwap`
- `py:afterSwap`
- `py:ignored`
- `py:error`

Use these for telemetry, debugging, and UX hooks.

## Dynamic content

- Swapped fragments are automatically re-processed.
- Manual DOM insertion still requires `window.pywebviewHtmx.process(root)`.
- `process(root)` includes `root` itself if it has `py-call`.

## Safety

- Returned HTML is inserted directly into the DOM.
- Escape or sanitize untrusted content before returning markup.
- Treat Python API methods as privileged application logic.
