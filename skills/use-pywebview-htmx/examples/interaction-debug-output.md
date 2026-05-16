# Pywebview Htmx Interaction Output Example

Use this shape when implementing or debugging a pywebview-htmx interaction. Keep
the actual response tied to the user's app and files.

## Contract Check

- `py-call`: Python method exists on the exposed `js_api` object.
- Handler return: HTML string fragment, with untrusted values escaped.
- Params: valid `data-py-params` or named form fields for submit serialization.

## Binding Changes

- Trigger: default `click` or explicit `py-trigger`.
- Target: resolved `py-target`, or the triggering element when omitted.
- Swap: `innerHTML`, `outerHTML`, or `append`, with the returned fragment shaped to match.
- Wait state: `py-wait` target or fallback behavior.
- Request policy: global config or per-trigger `py-policy`, noting any shared target state.

## Handler Changes

- Python method signature and expected `params`.
- Escaping/sanitization used before returning markup.
- Fragment shape and preserved selectors or IDs for follow-up interactions.

## Dynamic Content

- Normal pywebview-htmx swaps re-process returned fragments automatically.
- Manual DOM insertion calls `window.pywebviewHtmx.process(root)`.

## Validation Steps

1. Open the local app through the project run command.
2. Trigger the interaction and inspect the swapped DOM.
3. Check console events such as `py:error`, `py:ignored`, `py:beforeSwap`, and `py:afterSwap`.
4. Confirm loading and concurrency behavior for repeated clicks or shared targets.
