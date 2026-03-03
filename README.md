# pyhtmx

`pyhtmx` provides HTMX-style declarative attributes for PyWebview apps.

## Install

```bash
pdm install
```

## Run demo

```bash
pdm run python app.py
```

## Attributes

- `py-call`: Python API method to invoke through `window.pywebview.api`.
- `py-trigger`: Event name to bind (defaults to `click`).
- `data-py-params`: JSON payload sent to the Python API method.
- `py-target`: CSS selector of element to update with returned HTML.
- `py-swap`: Swap style (`innerHTML`, `outerHTML`, `append`).
- `py-wait`: CSS selector for element that receives `.py-waiting` while request is in flight.

## Runtime config

- `window.pyhtmx.config.requestPolicy`: `latest-wins` (default) or `drop`.
- `window.pyhtmx.config.swapDelay`: Delay before swapping.
- `window.pyhtmx.config.settleDelay`: Delay after swapping.

## Theme system

pyHTMX ships reusable component styling and multiple built-in themes.

```python
from pyhtmx import create_window, list_pyhtmx_themes

print(list_pyhtmx_themes())  # ['aurora', 'cybermind', 'paper']
create_window("My App", html, js_api=api, theme="paper")
```

API:
- `list_pyhtmx_themes()`: available bundled theme names.
- `get_pyhtmx_theme_css(theme)`: resolved CSS (base + theme overrides).
- `inject_pyhtmx_theme(html, theme)`: inject or replace theme CSS in raw HTML.
- `create_window(..., theme="aurora")`: injects selected theme + pyHTMX script.

Set `theme=None` in `create_window()` to disable automatic theme CSS injection.

Bundled component classes include:
- Layout: `.pyh-shell`, `.pyh-hero`, `.pyh-grid`, `.pyh-card`
- Controls: `.pyh-btn`, `.pyh-btn-primary`, `.pyh-btn-secondary`, `.pyh-btn-ghost`, `.pyh-btn-danger`
- Content: `.pyh-result`, `.pyh-note`, `.pyh-code`, `.pyh-chip`, `.pyh-muted`
- Lists/logs: `.pyh-activity-list`, `.pyh-event-log`
- Utilities: `.pyh-row`, `.pyh-full-width`, `.pyh-inline-config`

## Window lifecycle

`create_window()` starts PyWebview by default. Pass `start=False` to create the
window without starting the global event loop yet:

```python
window = create_window("My App", html, js_api=api, theme="aurora", start=False)
```
