---
name: use-pywebview-htmx
description: Build or modify PyWebview desktop UIs with pywebview-htmx. Use when a task involves pywebview_htmx, create_window(), py-call/py-trigger/py-target/py-swap/py-wait/py-policy attributes, Python handlers exposed through js_api, form submit serialization, dynamic fragment processing, or bundled theme helpers.
---

# Use Pywebview Htmx

Treat `pywebview-htmx` as an in-process HTML fragment runtime, not an HTTP framework.
Bind HTML elements with `py-*` attributes, expose matching Python methods through
`js_api`, return escaped HTML strings, and let the runtime swap the returned
fragment into the DOM.

If the current workspace is this library repository, read `README.md`, `app.py`,
and `src/pywebview_htmx/static/runtime.js` before making non-trivial changes.
Use the bundled references in this skill for quick recall; open the repo files
when you need the exact current implementation.

## Workflow

### 1. Map the interaction contract

Inspect the HTML/template and the Python `js_api` object together.

- Match every `py-call` to a real Python method.
- Confirm the method returns an HTML string fragment, not a dict or other object.
- Choose the swap target and swap strategy before changing markup.
- Prefer `create_window()` for normal app usage so runtime and theme injection stay automatic.

For the exact contract, read `references/contract.md`.

### 2. Build the binding correctly

Use the smallest declarative binding that fits the interaction.

- Use `py-call` for the Python method name.
- Use `py-trigger` only when the event is not the default `click`.
- Use `py-target` when the triggering element should not be updated in place.
- Use `py-swap="outerHTML"` only when you are returning a full replacement component.
- Preserve the same outer selector or `id` on `outerHTML` replacements if later interactions still target that component.
- Use `py-wait` to move loading state onto a dedicated indicator.
- Use `py-policy` when a triggering control needs different request acceptance
  behavior than the global runtime config. If controls share a `py-target`, they
  also share request state.

### 3. Shape params safely

Use `data-py-params` for explicit JSON payloads on ordinary elements.

- When Python generates `data-py-params`, call `encode_params_attr(...)` instead of hand-rolling JSON escaping.
- For `<form py-trigger="submit">`, give the inputs `name` attributes. The runtime now serializes named fields automatically and merges them over any static `data-py-params`.
- Add custom JavaScript only when you need payload shaping beyond standard form serialization.

For examples, read `references/patterns.md`.

### 4. Render fragments defensively

Treat returned fragments as privileged HTML insertion.

- Escape untrusted values before interpolating them into markup.
- Return a single coherent fragment that matches the chosen swap style.
- For `append`, return only the row/item snippet to append.
- For `outerHTML`, return the entire replacement node.

### 5. Re-process and debug intentionally

The runtime automatically binds newly swapped descendants, but manual DOM edits still
need explicit processing.

- Call `window.pywebviewHtmx.process(root)` after inserting interactive nodes outside a normal pywebview-htmx swap.
- Listen for `py:error`, `py:ignored`, `py:beforeSwap`, and `py:afterSwap` when debugging.
- Adjust global timing or request behavior through `window.pywebviewHtmx.config`.
- Use `py-policy` when a specific trigger should use `drop`; remember that
  controls sharing a resolved `py-target` coordinate against the same in-flight
  state.

For failure cases and checks, read `references/troubleshooting.md`.

## Practical Rules

- Do not manually include the runtime script when using `create_window()`.
- Do not assume HTMX-style automatic form serialization on non-form elements.
- Do not return structured data from Python handlers unless you convert it to HTML before returning.
- Do not forget `name` attributes on form inputs you expect to serialize.
- Do not mutate the DOM manually and assume the runtime will discover new `py-call` elements by itself.

## References

- `references/contract.md`: concise API and runtime contract
- `references/patterns.md`: copyable interaction patterns and implementation choices
- `references/troubleshooting.md`: common mistakes and debugging checklist
