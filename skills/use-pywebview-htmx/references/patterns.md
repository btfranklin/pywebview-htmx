# Pywebview Htmx Patterns

Use this file when implementing or refactoring app code.

## Basic button to result panel

Use this for the common “click button, replace result area” pattern.

```html
<button
  py-call="fetch_profile"
  py-target="#result"
  data-py-params='{"user_id": 42}'>
  Load profile
</button>
<div id="result"></div>
```

Python:

```python
from html import escape


class API:
    def fetch_profile(self, params: dict) -> str:
        user_id = escape(str(params.get("user_id", "unknown")))
        return f"<p>User: {user_id}</p>"
```

## Safe dynamic params from Python

Use this when HTML is generated in Python and `data-py-params` must be embedded safely.

```python
from pywebview_htmx import encode_params_attr

payload = encode_params_attr({"user_id": 42, "mode": "full"})
button = f'''
<button py-call="fetch_profile" py-target="#result" data-py-params="{payload}">
  Load profile
</button>
'''
```

## Submit form without manual sync JavaScript

Give each input a `name`. The runtime serializes the form automatically.

```html
<form py-call="save_message" py-trigger="submit" py-target="#result">
  <input name="message" type="text">
  <select name="mood">
    <option value="focused">focused</option>
    <option value="curious">curious</option>
  </select>
  <button type="submit">Save</button>
</form>
<div id="result"></div>
```

Use `data-py-params` only for extra static values that should be merged in.

## Append activity rows

Use `append` only when the handler returns the row/item snippet, not the full list.

```html
<button
  py-call="add_activity"
  py-target="#activity-list"
  py-swap="append"
  data-py-params='{"source": "toolbar"}'>
  Add
</button>
<ul id="activity-list"></ul>
```

## Replace a full component

Use `outerHTML` for full-card refreshes or self-replacing controls.

Rules:

- Return the full replacement node.
- Preserve the same outer selector or `id` if future bindings still target it.
- Keep follow-up interactive descendants inside the replacement markup.

## Per-element concurrency

Use global config for broad behavior changes:

```js
window.pywebviewHtmx.config.requestPolicy = "drop";
```

Use `py-policy` when one trigger needs different behavior. If multiple triggers
share a resolved `py-target`, they also share request state:

```html
<button
  py-call="long_task"
  py-target="#result"
  py-policy="drop">
  Run once
</button>
```

## Dynamic fragment insertion

When Python returns new markup containing fresh `py-call` elements, normal swaps
bind them automatically.

When external JavaScript inserts the markup manually, follow it with:

```js
window.pywebviewHtmx.process(root);
```

## Theme switching

For Python-driven theme changes:

- Expose a Python method such as `switch_theme`.
- Return a fragment containing `<style data-pywebview-theme="theme-name">...</style>`.
- Replace the themed section with `py-swap="outerHTML"`.
