from __future__ import annotations

import pytest

TESTED_BEHAVIOR_IDS = set(range(43, 73))


def _assert_fragments_present(js_compact: str, fragments: tuple[str, ...]) -> None:
    for fragment in fragments:
        assert fragment in js_compact


JS_BEHAVIOR_FRAGMENTS: list[tuple[int, tuple[str, ...]]] = [
    (43, ('defaultSwapStyle: "innerHTML"',)),
    (44, ("swapDelay: 0",)),
    (45, ("settleDelay: 20",)),
    (46, ('requestPolicy: "latest-wins"',)),
    (47, ("const requestState = new WeakMap();",)),
    (48, ("window.pyhtmx = {",)),
    (49, ("config,",)),
    (50, ("process: processPyHTMXNodes",)),
    (51, ("swap: pySwap",)),
    (52, ("trigger: triggerEvent",)),
    (
        53,
        (
            'document.addEventListener("DOMContentLoaded"',
            "processPyHTMXNodes(document.body)",
        ),
    ),
    (54, ("function processPyHTMXNodes(root = document)",)),
    (55, ('if (!root || typeof root.querySelectorAll !== "function")',)),
    (56, ('root.querySelectorAll("[py-call]")',)),
    (57, ('element.getAttribute("data-pyhtmx-bound") === "true"',)),
    (58, ('element.setAttribute("data-pyhtmx-bound", "true")',)),
    (59, ('element.getAttribute("py-trigger") || "click"',)),
    (60, ('element.getAttribute("py-call")',)),
    (61, ('console.warn("pyHTMX: py-call is empty"',)),
    (62, ('element.getAttribute("py-target")',)),
    (63, ('element.getAttribute("py-swap") || config.defaultSwapStyle',)),
    (64, ('element.getAttribute("data-py-params")',)),
    (65, ('if (!raw) return {};',)),
    (66, ('console.error("pyHTMX: invalid JSON in data-py-params"', "return {};")),
    (67, ('if (!element.hasAttribute("py-wait"))', "return element;")),
    (
        68,
        (
            'const waitSelector = element.getAttribute("py-wait")',
            "if (!waitSelector) { return element; }",
        ),
    ),
    (69, ("return $(waitSelector) || element;",)),
    (70, ("const bridge = window.pywebview && window.pywebview.api;",)),
    (71, ('throw new Error("window.pywebview.api is not available")',)),
    (72, ("Python API method", "was not found")),
]


@pytest.mark.parametrize(
    ("behavior_id", "fragments"),
    JS_BEHAVIOR_FRAGMENTS,
    ids=[f"B{behavior_id}" for behavior_id, _ in JS_BEHAVIOR_FRAGMENTS],
)
def test_js_contract_fragments(
    behavior_id: int,
    fragments: tuple[str, ...],
    js_compact: str,
) -> None:
    _ = behavior_id
    _assert_fragments_present(js_compact, fragments)
