from __future__ import annotations

import pytest

TESTED_BEHAVIOR_IDS = set(range(101, 114))


def _assert_fragments_present(js_compact: str, fragments: tuple[str, ...]) -> None:
    for fragment in fragments:
        assert fragment in js_compact


JS_BEHAVIOR_FRAGMENTS: list[tuple[int, tuple[str, ...]]] = [
    (
        101,
        (
            "function mergeParamValue(target, key, value)",
            "if (Object.prototype.hasOwnProperty.call(target, key))",
        ),
    ),
    (
        102,
        (
            "function serializeForm(form, event)",
            "const formData = new FormData(form);",
        ),
    ),
    (
        103,
        (
            'const submitter = event && "submitter" in event ? event.submitter : null;',
            "submitter.name",
        ),
    ),
    (
        104,
        (
            "value instanceof File",
            (
                'console.warn("PyWebview HTMX: file inputs are not supported '
                'in data-py-params"'
            ),
        ),
    ),
    (
        105,
        (
            "function buildRequestParams(element, eventName, event)",
            'if (element.tagName !== "FORM" || eventName !== "submit")',
            "return { ...params, ...serializeForm(element, event) };",
        ),
    ),
    (
        106,
        (
            "const elements = [];",
            'if (root.matches && root.matches("[py-call]"))',
            "elements.push(root);",
            'elements.push(...root.querySelectorAll("[py-call]"));',
        ),
    ),
    (
        107,
        (
            "function getRequestPolicy(element)",
            'const policy = element.getAttribute("py-policy") || config.requestPolicy;',
        ),
    ),
    (
        108,
        (
            'policy === "drop" || policy === "latest-wins"',
            "return config.requestPolicy;",
        ),
    ),
    (
        109,
        (
            "const requestPolicy = getRequestPolicy(element);",
            'if (requestPolicy === "drop" && state.inFlightCount > 0)',
        ),
    ),
    (
        110,
        (
            "const params = buildRequestParams(element, eventName, event);",
        ),
    ),
    (
        111,
        (
            'if (typeof response !== "string") {',
            (
                'throw new Error("PyWebview HTMX: Python API methods must return '
                'an HTML string")'
            ),
        ),
    ),
    (
        112,
        (
            'triggerEvent(element, "py:error", { error, requestId });',
        ),
    ),
    (
        113,
        (
            'element.getAttribute("py-policy")',
        ),
    ),
]


@pytest.mark.parametrize(
    ("behavior_id", "fragments"),
    JS_BEHAVIOR_FRAGMENTS,
    ids=[f"B{behavior_id}" for behavior_id, _ in JS_BEHAVIOR_FRAGMENTS],
)
def test_js_ergonomic_contract_fragments(
    behavior_id: int,
    fragments: tuple[str, ...],
    js_compact: str,
) -> None:
    _ = behavior_id
    _assert_fragments_present(js_compact, fragments)
