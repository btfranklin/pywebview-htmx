# pywebview-htmx

![pywebview-htmx banner](https://raw.githubusercontent.com/btfranklin/pywebview-htmx/main/.github/social%20preview/pywebview_htmx_social_preview.jpg "pywebview-htmx")

`pywebview-htmx` (import as `pywebview_htmx`) brings HTMX-style declarative interactions to PyWebview apps.

You write mostly normal HTML, annotate interactive elements with `py-*` attributes,
and `pywebview-htmx` wires those elements to Python methods exposed through
`window.pywebview.api`.

## What You Get

- Declarative Python calls from HTML (`py-call`, `py-trigger`, `data-py-params`)
- Declarative target updates (`py-target`, `py-swap`)
- Built-in loading state support (`py-wait` + `.py-waiting`)
- Event hooks for lifecycle instrumentation (`py:trigger`, `py:beforeSwap`, etc.)
- Concurrency control (`latest-wins` or `drop`) without custom plumbing
- Automatic processing of newly swapped HTML fragments
- Built-in theme system (multiple shipped themes + reusable component CSS)

## Mental Model

`pywebview-htmx` is a tiny runtime that does four core jobs:

1. Find elements with `py-call`.
2. Bind an event listener (default: `click`, override with `py-trigger`).
3. Call your Python API method through `window.pywebview.api[method](params)`.
4. Swap returned HTML into the DOM according to `py-target` + `py-swap`.

In other words: your Python methods are your "server handlers", and returned HTML
is your "response body".

## Installation

### In this repository

```bash
pdm install
```

### In another PDM project

```bash
pdm add pywebview-htmx
```

## Agent Skill

This repository includes an installable coding-agent skill at
`skills/use-pywebview-htmx/`.

The folder in this repository is the source for a skill that tools such as
[`npx skills`](https://skills.sh/) can discover and install from GitHub.

List the available skill from this repository:

```bash
npx skills add btfranklin/pywebview-htmx --list --full-depth
```

Install just this skill:

```bash
npx skills add btfranklin/pywebview-htmx --skill use-pywebview-htmx
```

Other skill installers can consume the same skill folder from this repository.
The skill includes:

- the core usage workflow
- a concise contract reference
- implementation patterns
- troubleshooting guidance

## Quick Start

```python
from pywebview_htmx import create_window


class API:
    def greeting(self, params: dict) -> str:
        name = params.get("name", "world")
        return f"<p>Hello, {name}!</p>"


html = """
<!doctype html>
<html>
  <body>
    <button
      py-call="greeting"
      py-target="#result"
      data-py-params='{"name": "pywebview-htmx"}'>
      Say hello
    </button>
    <div id="result"></div>
  </body>
</html>
"""

create_window("Quickstart", html, js_api=API())
```

You do **not** manually include `runtime.js` when using `create_window()`;
it is injected automatically.

## Important Differences From HTMX

- There is no HTTP request layer. `pywebview-htmx` calls a Python method on
  `window.pywebview.api` directly.
- Python handlers should return an HTML string fragment. Returning objects or
  other data types is treated as an error.
- For ordinary buttons/links, params still come from `data-py-params`.
- For `<form py-trigger="submit">`, named fields are serialized automatically
  and merged over `data-py-params`.
- Returned HTML is inserted directly into the DOM, so escape untrusted values
  before returning markup.

## API Reference (Python)

### `create_window(title, html, js_api=None, theme="aurora", start=True, **kwargs)`

Creates a PyWebview window with injected theme CSS (optional) and injected
`pywebview-htmx` runtime script.

- `title`: window title
- `html`: HTML document string
- `js_api`: Python object exposed as `window.pywebview.api`
- `theme`: bundled theme name (`"aurora"`, `"paper"`, `"cybermind"`) or `None`
- `start`: whether to call `webview.start()` automatically
- `**kwargs`: forwarded to `webview.create_window()`

When to set `start=False`:
- You need to create multiple windows before starting
- You want to manage PyWebview startup/lifecycle yourself

### `get_runtime_script()`

Returns the bundled JavaScript runtime as a string.

### `inject_runtime(html)`

Injects the runtime script tag into an HTML string (idempotent).

### `encode_params_attr(params)`

Returns HTML-escaped JSON that is safe to place in a `data-py-params`
attribute.

```python
from pywebview_htmx import encode_params_attr

payload = encode_params_attr({"user_id": 42, "mode": "full"})
button = f'<button data-py-params="{payload}">Load user</button>'
```

### Theme helpers

- `list_themes()` -> sorted list of available themes
- `get_theme_css(theme)` -> base CSS + selected theme CSS
- `inject_theme(html, theme)` -> inject or replace theme `<style>` block

### Constants

- `DEFAULT_THEME` (currently `"aurora"`)

## Declarative Attribute Reference

### `py-call` (required)

Python API method name to invoke.

```html
<button py-call="fetch_user">...</button>
```

### `py-trigger` (optional)

DOM event name to bind. Default is `click`.

```html
<form py-call="submit_form" py-trigger="submit">...</form>
<div py-call="show_tip" py-trigger="mouseenter">...</div>
```

### `data-py-params` (optional)

JSON payload passed to Python method.

```html
<button data-py-params='{"user_id": 42, "mode": "full"}'>...</button>
```

Notes:
- If missing, params default to `{}`.
- Invalid JSON logs an error and falls back to `{}`.
- For submit-triggered forms, named form fields are serialized automatically and
  merged over this payload.

### `py-target` (optional)

CSS selector of the element to update. If omitted, the triggering element is updated.

### `py-swap` (optional)

How returned HTML is applied:

- `innerHTML` (default)
- `outerHTML`
- `append`

Unknown value falls back to `innerHTML`.

### `py-wait` (optional)

CSS selector of element receiving `.py-waiting` while request is in flight.
If missing/empty/unresolvable, the triggering element is used.

### `py-policy` (optional)

Per-element concurrency override. If omitted, the global
`window.pywebviewHtmx.config.requestPolicy` value is used.

- `latest-wins`
- `drop`

## Runtime Config (JavaScript)

`window.pywebviewHtmx.config` includes:

- `defaultSwapStyle` (default: `"innerHTML"`)
- `swapDelay` (ms, default: `0`)
- `settleDelay` (ms, default: `20`)
- `requestPolicy` (`"latest-wins"` default, or `"drop"`)

Example:

```js
window.pywebviewHtmx.config.requestPolicy = "drop";
window.pywebviewHtmx.config.swapDelay = 150;
window.pywebviewHtmx.config.settleDelay = 50;
```

## Lifecycle Events

`pywebview-htmx` dispatches custom events you can observe for telemetry, debugging, and UX:

- `py:trigger`
- `py:beforeSwap`
- `py:afterSwap`
- `py:ignored` (when `requestPolicy="drop"` and request is in flight)
- `py:error`

Example:

```js
document.body.addEventListener("py:error", (event) => {
  console.error("pywebview-htmx error", event.detail.error);
});
```

## Concurrency Behavior

Per trigger element, `pywebview-htmx` tracks request state.

### `latest-wins` (default)

Multiple rapid requests are allowed; stale responses are ignored.
Only latest request updates the DOM.

### `drop`

If a request is already in flight for that element, new triggers are ignored and
`py:ignored` is emitted.

## Dynamic Content Re-processing

After a swap, `pywebview-htmx` automatically scans swapped content for new `py-call`
elements and binds them. This enables chained interactions in returned fragments
without manual re-init code.

## Theme System

`pywebview-htmx` ships a reusable component styling system plus multiple themes.

```python
from pywebview_htmx import create_window, list_themes

print(list_themes())
# ['aurora', 'cybermind', 'paper']

create_window("My App", html, js_api=api, theme="cybermind")
```

Set `theme=None` to disable automatic theme injection.

### Built-in Component Classes

The bundled CSS supports both `pyh-*` classes and compatibility aliases used by
the demo (`.hero`, `.demo-card`, `.btn`, etc.).

Recommended canonical classes:

- Layout: `.pyh-shell`, `.pyh-hero`, `.pyh-grid`, `.pyh-card`
- Controls: `.pyh-btn`, `.pyh-btn-primary`, `.pyh-btn-secondary`, `.pyh-btn-ghost`, `.pyh-btn-danger`
- Content: `.pyh-result`, `.pyh-note`, `.pyh-code`, `.pyh-chip`, `.pyh-muted`
- Logs/lists: `.pyh-activity-list`, `.pyh-event-log`
- Utilities: `.pyh-row`, `.pyh-full-width`, `.pyh-inline-config`

### Shipping Your Own Theme

Use the same token pattern as bundled themes (`--pyh-*` variables) and inject your
custom CSS before runtime initialization. If you want PyWebview HTMX-style replacement
behavior, add your own `<style data-pywebview-theme="my-theme">...</style>` block.

## Practical Patterns

### Pattern 1: Form submit to Python

- Use `py-trigger="submit"` on `<form>`
- Give fields `name` attributes so they can be serialized
- Use `data-py-params` only for extra static values you want merged in
- `py-target` a result card/summary region

### Pattern 2: Append activity/log rows

- Use `py-swap="append"` to add `<li>` rows
- Return a single row snippet from Python

### Pattern 3: Replace full component

- Use `py-swap="outerHTML"`
- Return full replacement markup with the same outer id/selector if future
  interactions should keep targeting that component

### Pattern 4: Theme switch from Python

- Expose a `switch_theme` Python method
- Return HTML containing `<style data-pywebview-theme="...">...</style>`
- Swap a wrapper section with `py-swap="outerHTML"`

## Security Notes

- Returned HTML is inserted directly into the DOM.
- Escape/sanitize untrusted data before returning markup.
- Treat Python API methods as privileged application logic.

## Troubleshooting

### "Nothing happens when I click"

Check:
- `py-call` matches an existing method on `window.pywebview.api`
- method returns a string of HTML
- no JSON parse error in `data-py-params`
- `py-target` selector exists
- for forms, fields have `name` attributes

### "New buttons in swapped HTML do not work"

This should work by default via post-swap processing. If you perform manual DOM
changes outside of pywebview-htmx swaps, call:

```js
window.pywebviewHtmx.process(document.body);
```

### "Loading state looks wrong"

Style `.py-waiting` globally and/or point `py-wait` at a dedicated element.

### "I got a Python API return type error"

`pywebview-htmx` expects handlers to return an HTML string fragment. Convert
structured data into markup before returning it.

## Common Mistakes

- Returning dicts/lists instead of HTML strings
- Forgetting to escape untrusted values before interpolating into markup
- Omitting `name` attributes on form fields and expecting them to serialize
- Using `py-swap="outerHTML"` but not preserving the target component's
  selector/id
- Manually mutating the DOM outside of `pywebview-htmx` swaps without calling
  `window.pywebviewHtmx.process(...)`

## Demo

Run the full feature showcase:

```bash
pdm run python app.py
```

The demo includes:
- Runtime config controls
- Live event feed
- All swap modes
- Multiple trigger types
- Concurrency policy behavior
- Dynamic fragment processing
- Python-driven live theme switching

## License

MIT (see [LICENSE](LICENSE)).
