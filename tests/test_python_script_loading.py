from __future__ import annotations

from pywebview_htmx import get_runtime_script

TESTED_BEHAVIOR_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_returns_string() -> None:
    assert isinstance(get_runtime_script(), str)


def test_returns_non_empty_content() -> None:
    assert get_runtime_script().strip()


def test_contains_window_runtime_export() -> None:
    assert "window.pywebviewHtmx" in get_runtime_script()


def test_contains_public_process_export() -> None:
    assert "process: processPyWebviewHtmxNodes" in get_runtime_script()


def test_contains_public_swap_export() -> None:
    assert "swap: pySwap" in get_runtime_script()


def test_contains_public_trigger_export() -> None:
    assert "trigger: triggerEvent" in get_runtime_script()


def test_contains_request_policy_configuration() -> None:
    assert 'requestPolicy: "latest-wins"' in get_runtime_script()


def test_contains_py_error_event_path() -> None:
    assert '"py:error"' in get_runtime_script()


def test_script_is_stable_across_calls() -> None:
    assert get_runtime_script() == get_runtime_script()
