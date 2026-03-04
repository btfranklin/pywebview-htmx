from __future__ import annotations

import pytest

import pywebview_htmx.runtime as runtime_module

TESTED_BEHAVIOR_IDS = set(range(31, 43))
SCRIPT_TAG = '<script data-pywebview-htmx="true">'


def _noop() -> None:
    return None


def test_create_window_passes_title(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    runtime_module.create_window("my-title", "<html><body>x</body></html>")
    assert captured["args"][0] == "my-title"


def test_create_window_passes_injected_html(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    runtime_module.create_window("title", "<html><body>x</body></html>")
    assert SCRIPT_TAG in captured["kwargs"]["html"]


def test_create_window_passes_js_api(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    api = object()

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    runtime_module.create_window("title", "<html><body>x</body></html>", js_api=api)
    assert captured["kwargs"]["js_api"] is api


def test_create_window_forwards_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    runtime_module.create_window(
        "title",
        "<html><body>x</body></html>",
        width=900,
        height=600,
        frameless=True,
    )
    assert captured["kwargs"]["width"] == 900
    assert captured["kwargs"]["height"] == 600
    assert captured["kwargs"]["frameless"] is True


def test_create_window_returns_webview_result(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()
    monkeypatch.setattr(
        runtime_module.webview,
        "create_window",
        lambda *a, **k: sentinel,
    )
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    result = runtime_module.create_window("title", "<html><body>x</body></html>")
    assert result is sentinel


def test_create_window_default_starts_webview_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"start": 0}

    def fake_create_window(*args, **kwargs):
        return object()

    def fake_start():
        calls["start"] += 1

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", fake_start)
    runtime_module.create_window("title", "<html><body>x</body></html>")
    assert calls["start"] == 1


def test_create_window_start_false_skips_webview_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"start": 0, "create_window": 0}

    def fake_create_window(*args, **kwargs):
        calls["create_window"] += 1
        return object()

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    def fake_start():
        calls["start"] += 1

    monkeypatch.setattr(runtime_module.webview, "start", fake_start)
    runtime_module.create_window("title", "<html><body>x</body></html>", start=False)
    assert calls["create_window"] == 1
    assert calls["start"] == 0


def test_create_window_create_failure_does_not_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"start": 0}

    def fake_create_window(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    def fake_start():
        calls["start"] += 1

    monkeypatch.setattr(runtime_module.webview, "start", fake_start)
    with pytest.raises(RuntimeError, match="boom"):
        runtime_module.create_window("title", "<html><body>x</body></html>")
    assert calls["start"] == 0


def test_create_window_start_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"create_window": 0}

    def fake_create_window(*args, **kwargs):
        calls["create_window"] += 1
        return object()

    def fake_start():
        raise RuntimeError("start-failed")

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", fake_start)
    with pytest.raises(RuntimeError, match="start-failed"):
        runtime_module.create_window("title", "<html><body>x</body></html>")
    assert calls["create_window"] == 1


def test_create_window_passes_single_marker_to_webview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(runtime_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(runtime_module.webview, "start", _noop)
    runtime_module.create_window(
        "title",
        "<html><body>x</body></html>",
        start=False,
        confirm_close=True,
    )
    assert captured["kwargs"]["html"].count(SCRIPT_TAG) == 1
    assert captured["kwargs"]["confirm_close"] is True
