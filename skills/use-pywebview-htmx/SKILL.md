---
name: use-pywebview-htmx
description: >-
  Use when implementing, reviewing, explaining, or debugging a desktop app that consumes pywebview-htmx through declarative `py-*` bindings and Python `js_api` handlers. Verify guidance against the app's declared and installed library version. Do not use for developing or releasing pywebview-htmx itself, generic PyWebview apps, HTTP or Django HTMX, or unrelated frontend work. Return consumer-app code, a diagnosis, review findings, an explanation, or a validated implementation plan.
---

# Use pywebview-htmx

Treat `pywebview-htmx` as an in-process HTML fragment runtime, not an HTTP
framework. Bind application HTML with `py-*` attributes, expose matching Python
methods through `js_api`, and return safe HTML fragments for DOM swaps.

## Workflow

### 1. Verify the consumer's contract

Inspect the consuming application's dependency declaration, lockfile, and active
environment before relying on a library feature.

- Record the declared and installed `pywebview-htmx` versions for non-trivial
  diagnoses, reviews, and plans.
- Treat the installed package as the source of truth when it differs from this
  skill's bundled guidance. Inspect its public API or bundled runtime when exact
  behavior matters.
- Never infer feature support from a version number alone. If the relevant
  installed package or version-matched documentation is unavailable, state the
  uncertainty and avoid version-specific claims until it can be inspected.
- Support every version-sensitive claim with an inspected, version-matched
  artifact such as the installed runtime path or packaged documentation. Do not
  project this skill's current contract backward onto older versions.
- If declaration, lock, and environment versions disagree, stop before making
  feature-specific diagnoses or proposing compatibility code. Establish which
  environment runs the app and inspect that runtime first.
- If that inspection is unavailable, return only the confirmed mismatch,
  version-neutral observations, and the next diagnostic steps. Do not present a
  cross-version fix as safe.
- Report version mismatches. Do not sync the environment or change the
  dependency version unless the user authorizes it.
- Do not edit the library's source or substitute an upstream development
  checkout for the application's installed dependency.

Use the [contract reference](references/contract.md) for quick recall after this
version check.

### 2. Map the interaction

Inspect the HTML/template and the Python `js_api` object together.

- Match every `py-call` to a real Python method.
- Confirm the method returns an HTML string fragment, not a dict or other object.
- Choose the swap target and swap strategy before changing markup.
- Prefer `create_window()` when the installed version supports it so runtime and
  theme injection stay automatic.

### 3. Build the binding

Use the smallest declarative binding that fits the interaction.

- Match `py-call` to the Python method name and use an explicit `py-trigger`
  when the event is not the default click.
- Choose `py-target`, `py-swap`, `py-wait`, and `py-policy` only after confirming
  the installed version supports the intended behavior.
- Use `py-swap="outerHTML"` only for a full replacement component.
- Preserve the same outer selector or `id` on `outerHTML` replacements if later interactions still target that component.

Read [interaction patterns](references/patterns.md) only when implementation
examples are useful.

### 4. Shape params and fragments safely

Use `data-py-params` for explicit JSON payloads on ordinary elements.

- When Python generates `data-py-params`, call `encode_params_attr(...)` instead of hand-rolling JSON escaping.
- For supported `<form py-trigger="submit">` serialization, give every included
  control a `name` attribute.
- Add custom JavaScript only when you need payload shaping beyond standard form serialization.
- Escape untrusted values before interpolating them into markup.
- Return a single coherent fragment that matches the chosen swap style.
- For `append`, return only the row/item snippet to append.
- For `outerHTML`, return the entire replacement node.

### 5. Debug and validate the application

The runtime automatically binds newly swapped descendants, but manual DOM edits still
need explicit processing.

- When supported, call `window.pywebviewHtmx.process(root)` after inserting
  interactive nodes outside a normal pywebview-htmx swap.
- Listen for `py:error`, `py:ignored`, `py:beforeSwap`, and `py:afterSwap` when debugging.
- Run the consuming project's standard automated checks.
- Launch the application and exercise the changed interaction, including
  repeated triggers, loading state, swap results, and follow-up controls when
  relevant.

Read [troubleshooting guidance](references/troubleshooting.md) for failure cases.

## Practical Rules

- Do not manually include the runtime script when using `create_window()`.
- Do not assume HTMX-style automatic form serialization on non-form elements.
- Do not return structured data from Python handlers unless you convert it to HTML before returning.
- Do not forget `name` attributes on form inputs you expect to serialize.
- Do not mutate the DOM manually and assume the runtime will discover new `py-call` elements by itself.

## References

- [Contract](references/contract.md): concise API and runtime behavior
- [Patterns](references/patterns.md): copyable consumer-app interactions
- [Troubleshooting](references/troubleshooting.md): common failures and checks
- [Worked example](examples/interaction-debug-output.md): completed consumer-app diagnosis and fix
