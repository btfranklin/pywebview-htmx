# pywebview-htmx Contract

Use this file for quick recall after checking the consuming application's
declared and installed `pywebview-htmx` versions. If this reference differs from
the installed package, follow the installed package's public API and runtime.
Do not infer a feature history from version numbers; inspect version-matched
artifacts before making compatibility claims. When declared, locked, and active
versions disagree, resolve which environment runs the app before applying this
contract. Cite the inspected artifact for version-sensitive conclusions; without
one, limit the response to uncertainty and diagnostic steps.

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
- `py-timeout`: optional Python response deadline in milliseconds
- `py-debounce`: optional delay after the last event, in milliseconds

If `py-target` is omitted, the triggering element is the target.
If `py-wait` is missing, empty, invalid, or unresolved, the triggering element
receives `.py-waiting`.

When handling native link navigation, form submission, or a form-associated
submit/reset control, the runtime prevents that destructive default action. It
preserves the normal behavior of checkboxes, radio buttons, labels, and
ordinary buttons.
A label that contains its control calls Python once per activation.

## Params contract

- Missing `data-py-params` becomes `{}`.
- Invalid JSON or a value that is not an object emits `py:error`. Python is not called.
- Forms with `submit`, `input`, or `change` triggers serialize named fields automatically.
- Form values merge over any static `data-py-params`.
- Repeated form field names accumulate into arrays.
- File inputs are skipped with a warning.

Use `encode_params_attr(...)` when Python emits `data-py-params` into HTML.
Non-finite numbers raise `ValueError` because JSON does not support them.

## Runtime config

Available on `window.pywebviewHtmx.config`:

- `defaultSwapStyle`
- `swapDelay`
- `settleDelay`
- `requestPolicy`
- `requestTimeout`

Global config is the default. `py-policy` overrides request behavior for a
single element. Runtime defaults and `py-wait` are resolved for each accepted
request. An explicit `py-swap` overrides `defaultSwapStyle`; otherwise a config
change applies to the element's next request even if it is already bound.

Request state is scoped to the normalized selector string for a nonempty
`py-target`, and to the triggering element otherwise. Controls using the same
selector coordinate `latest-wins` and `drop` behavior across replacement of the
matching DOM node. Selector state is retained only while requests are in
flight. Loading state is counted separately per wait element resolved for each
accepted request.
Bundled loading styles do not block pointer input. Request policy controls
whether another trigger is accepted.

`latest-wins` does not cancel Python work. PyWebview runs exposed handlers in
separate threads. Protect shared mutable data with a lock or a database
transaction when needed. `drop` does not act as a global lock across scopes.

Wait for `window`'s `pywebviewready` event before programmatic calls at startup.
Calls made before the bridge is available emit `py:error` and are not queued.

## Events

- `py:trigger`
- `py:beforeSwap`
- `py:afterSwap`
- `py:ignored`
- `py:error`

Use these for telemetry, debugging, and UX hooks. They are observational and
non-cancelable. Every `py:error` includes a required boolean `detail.stale`;
stale failures remain observable even though stale successful responses do not
swap.

`detail.element` identifies the original control. If that control is detached,
the error is dispatched on `document.body`, or the document if no body exists.

## Component CSS

Bundled component styling uses only canonical `.pyh-*` classes. Demo-style
aliases such as `.btn` and `.demo-card` are not part of the public surface.

## Dynamic content

- Swapped fragments are automatically re-processed.
- Manual DOM insertion still requires `window.pywebviewHtmx.process(root)`.
- `process(root)` includes `root` itself if it has `py-call`.

## Safety

- Returned HTML is inserted directly into the DOM.
- Escape or sanitize untrusted content before returning markup.
- Treat Python API methods as privileged application logic.

## Request deadlines

Set `py-timeout="2000"` for a two-second Python response deadline. The global
`requestTimeout` default is `0` (no deadline). Values are milliseconds from
0 to 2147483647. A timeout emits `py:error` with `detail.phase="timeout"` and
`error.name="TimeoutError"`. The loading indicator stops, and a late response
cannot change the page. A late Python failure still emits `py:error` with
`detail.expired=true`.

A deadline does not cancel Python work or retry the call. Under `drop`, the
scope stays locked until Python finishes. Show the timeout message and let the
application check the operation's result before another attempt. If Python
never returns, the lock remains until the page is reloaded; reloading does not
prove that the operation was cancelled. Use `latest-wins` for independent read
operations that can safely run again.

## Delay rapid input calls

Use `py-debounce="200"` on a read operation to wait until input stops for 200 ms.
Each event replaces the pending call for that control. Only the final event's
parameter snapshot is sent. Forms with `py-trigger="input"` or `change`
serialize their named fields, as submit forms do. Input during text composition
is not sent; the final input event supplies the completed text.

```html
<form py-call="search" py-trigger="input" py-debounce="200" py-target="#results">
  <label for="query">Search</label>
  <input id="query" name="query" type="search">
</form>
<div id="results"></div>
```

The delay defaults to zero. Clicks and submissions remain immediate unless a
control explicitly sets `py-debounce`. A removed control cannot send its pending
call while detached. Waiting state and request policy start when the call is
sent, not while its timer is pending. `drop` can still reject that call if
another operation is running; use `latest-wins` for live read results. The delay
does not cancel Python work that has already started.

## Focus after replacement

Give controls stable, unique IDs. When a destructive swap removes the focused
control, the runtime focuses the inserted control with the same ID without
scrolling the page. Text inputs and textareas also retain their selection,
limited to the replacement value's length.

Focus is read immediately before the swap. Moving to a control outside the
updated region during a request is respected. A lifecycle listener that sets
focus after the swap also takes precedence. Append operations do not change
focus. If no matching control is inserted, the runtime does not guess a new
focus target.
