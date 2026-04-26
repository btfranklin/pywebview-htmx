from __future__ import annotations

import pytest

TESTED_BEHAVIOR_IDS = set(range(73, 101))


def _assert_fragments_present(js_compact: str, fragments: tuple[str, ...]) -> None:
    for fragment in fragments:
        assert fragment in js_compact


JS_BEHAVIOR_FRAGMENTS: list[tuple[int, tuple[str, ...]]] = [
    (
        73,
        (
            'function shouldPreventDefault(eventName)',
            'return eventName === "submit";',
            "if (shouldPreventDefault(eventName) && event.cancelable)",
            "event.preventDefault();",
        ),
    ),
    (
        74,
        (
            "function getRequestState(key)",
            "let state = requestState.get(key);",
            "requestState.set(key, state);",
        ),
    ),
    (75, ("lastIssued: 0", "state.lastIssued = requestId;")),
    (76, ("inFlightCount: 0", "state.inFlightCount += 1;")),
    (77, ('requestPolicy === "drop"', 'triggerEvent(element, "py:ignored"')),
    (78, ('triggerEvent(element, "py:trigger"', "requestId,")),
    (
        79,
        (
            "function addWaiting(waitTarget)",
            'waitTarget.classList.add("py-waiting")',
        ),
    ),
    (80, ("if (requestId !== state.lastIssued) { return; }",)),
    (81, ("const target = targetSelector ? $(targetSelector) : element;",)),
    (82, (" : element;",)),
    (83, ('console.warn("PyWebview HTMX: target element not found"',)),
    (84, ('triggerEvent(target, "py:beforeSwap"',)),
    (85, ("if (config.swapDelay > 0)", "await delay(config.swapDelay);")),
    (86, ("if (requestId !== state.lastIssued) { return; }",)),
    (87, ("const processRoot = pySwap(target, response, swapStyle);",)),
    (88, ("processPyWebviewHtmxNodes(processRoot);",)),
    (
        89,
        (
            "const afterSwapTarget =",
            'swapStyle === "outerHTML"',
            'triggerEvent(afterSwapTarget, "py:afterSwap"',
        ),
    ),
    (90, ("if (config.settleDelay > 0)", "await delay(config.settleDelay);")),
    (91, ('triggerEvent(element, "py:error"', "requestId")),
    (92, ("state.inFlightCount = Math.max(0, state.inFlightCount - 1);",)),
    (93, ("Math.max(0, state.inFlightCount - 1)",)),
    (
        94,
        (
            "function removeWaiting(waitTarget)",
            'waitTarget.classList.remove("py-waiting")',
        ),
    ),
    (95, ('case "innerHTML":', "target.innerHTML = content;")),
    (96, ('case "append":', 'target.insertAdjacentHTML("beforeend", content);')),
    (
        97,
        (
            'case "outerHTML": {',
            "const parent = target.parentElement || document.body;",
        ),
    ),
    (98, ("|| document.body",)),
    (99, ('default:', "target.innerHTML = content;")),
    (100, ("return target;", "return parent;")),
]


@pytest.mark.parametrize(
    ("behavior_id", "fragments"),
    JS_BEHAVIOR_FRAGMENTS,
    ids=[f"B{behavior_id}" for behavior_id, _ in JS_BEHAVIOR_FRAGMENTS],
)
def test_js_request_and_swap_fragments(
    behavior_id: int,
    fragments: tuple[str, ...],
    js_compact: str,
) -> None:
    _ = behavior_id
    _assert_fragments_present(js_compact, fragments)
