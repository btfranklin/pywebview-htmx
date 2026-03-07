# Pywebview Htmx Troubleshooting

Use this file when the markup looks plausible but the interaction still fails.

## Nothing happens on click or submit

Check these first:

- `py-call` matches a real method on `window.pywebview.api`
- the Python method returns an HTML string
- `py-target` resolves to a real element
- `data-py-params` contains valid JSON
- form inputs that should serialize have `name` attributes

## I got `py:error`

Inspect the browser console and listen for the event:

```js
document.body.addEventListener("py:error", (event) => {
  console.error(event.detail.error);
});
```

Common causes:

- Python handler returned a non-string value
- `window.pywebview.api` was unavailable
- `py-call` referenced a missing method

## Form payload is missing fields

- Confirm the element is a real `<form>`
- Confirm `py-trigger="submit"`
- Add `name` to each field that should serialize
- Remember that unnamed fields are ignored

If you need custom payload shaping, add JavaScript intentionally instead of
assuming the runtime will infer it.

## New buttons in inserted HTML do not work

Normal pywebview-htmx swaps re-process fragments automatically.

If you inserted DOM manually, call:

```js
window.pywebviewHtmx.process(root);
```

The runtime now processes `root` itself if it has `py-call`, not only its descendants.

## `outerHTML` replacement broke later interactions

The replacement likely dropped the old target selector or `id`.

When a later control still targets `#some-card`, the replacement fragment must
still render `id="some-card"` on its outer node.

## Concurrency behavior is wrong

Check both levels:

- global `window.pywebviewHtmx.config.requestPolicy`
- per-element `py-policy`

Remember:

- `latest-wins` lets requests race but ignores stale responses
- `drop` ignores new triggers while the current request is in flight

## Loading state looks wrong

- `py-wait` points loading state at another element
- missing or empty `py-wait` means the triggering element gets `.py-waiting`
- if the wait target selector is wrong, the trigger element is used as fallback
