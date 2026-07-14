# Worked Example: Repairing a Search Form

The `inventory-desktop` application submitted its search form through the
browser instead of calling Python. When the handler was invoked manually, it
returned a dictionary that the runtime could not swap into `#search-results`.

## Contract Verification

- `pyproject.toml` declared `pywebview-htmx>=0.3.1`.
- `pdm.lock` and the active environment both resolved `0.3.1`.
- The installed runtime supported submit serialization, `py-wait`, and HTML
  fragment swaps.
- No dependency change was needed.

## Diagnosis

In `templates/search.html`, the form omitted `py-trigger="submit"`, and the
query input had no `name`. In `inventory/api.py`, `search_inventory()` returned
structured data rather than an HTML string. Those three contract mismatches
accounted for the browser submission, empty params, and `py:error` event.

## Application Changes

`templates/search.html`:

```html
<form
  py-call="search_inventory"
  py-trigger="submit"
  py-target="#search-results"
  py-wait="#search-status">
  <label>
    Search inventory
    <input name="query" type="search" required>
  </label>
  <button type="submit">Search</button>
</form>
<p id="search-status" aria-live="polite">Ready</p>
<section id="search-results" aria-live="polite"></section>
```

`inventory/api.py`:

```python
from html import escape


class InventoryAPI:
    def search_inventory(self, params: dict[str, object]) -> str:
        query = str(params.get("query", "")).strip()
        if not query:
            return '<p class="error">Enter a search term.</p>'

        matches = self.inventory.search(query)
        rows = "".join(
            f"<li>{escape(item.name)} — {item.quantity}</li>"
            for item in matches
        )
        if not rows:
            return f"<p>No inventory matched <strong>{escape(query)}</strong>.</p>"
        return f"<ul>{rows}</ul>"
```

The handler now accepts the runtime's params dictionary, escapes application
data before interpolation, and returns a fragment shaped for the default
`innerHTML` swap.

## Validation

- `pdm run test`: 42 tests passed.
- `pdm run python app.py`: the form called `search_inventory` without browser
  navigation and replaced `#search-results`.
- The handler test for an empty query returned the validation fragment; a manual
  query containing `<` rendered as text rather than markup.
- Repeated submissions cleared the waiting state correctly, and the console
  emitted no `py:error` events.
