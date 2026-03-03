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

## Window lifecycle

`create_window()` starts PyWebview by default. Pass `start=False` to create the
window without starting the global event loop yet:

```python
window = create_window("My App", html, js_api=api, start=False)
```
