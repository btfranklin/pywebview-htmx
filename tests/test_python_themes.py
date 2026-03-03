from __future__ import annotations

import pytest

import pyhtmx.pyhtmx as pyhtmx_module
from pyhtmx import (
    DEFAULT_THEME,
    get_pyhtmx_theme_css,
    inject_pyhtmx_theme,
    list_pyhtmx_themes,
)


def test_list_pyhtmx_themes_has_expected_names() -> None:
    themes = list_pyhtmx_themes()
    assert themes == sorted(themes)
    assert "aurora" in themes
    assert "cybermind" in themes
    assert "paper" in themes
    assert "base" not in themes


def test_get_pyhtmx_theme_css_includes_base_and_theme_content() -> None:
    css = get_pyhtmx_theme_css("aurora")
    assert ".pyh-shell" in css
    assert "--pyh-background" in css
    assert "--pyh-btn-primary-bg" in css


def test_get_pyhtmx_theme_css_unknown_theme_raises() -> None:
    with pytest.raises(ValueError, match="Unknown pyhtmx theme"):
        get_pyhtmx_theme_css("nonexistent")


def test_inject_pyhtmx_theme_inserts_before_head_close() -> None:
    html = "<html><head><title>x</title></head><body>ok</body></html>"
    result = inject_pyhtmx_theme(html, theme="aurora")
    assert 'data-pyhtmx-theme="aurora"' in result
    assert result.index('data-pyhtmx-theme="aurora"') < result.lower().index("</head>")


def test_inject_pyhtmx_theme_inserts_before_body_if_no_head() -> None:
    html = "<html><body>ok</body></html>"
    result = inject_pyhtmx_theme(html, theme="aurora")
    assert result.index('data-pyhtmx-theme="aurora"') < result.lower().index("</body>")


def test_inject_pyhtmx_theme_prepends_without_head_or_body() -> None:
    html = "<div>content</div>"
    result = inject_pyhtmx_theme(html, theme="aurora")
    assert result.startswith('<style data-pyhtmx-theme="aurora">')
    assert result.endswith(html)


def test_inject_pyhtmx_theme_idempotent_same_theme() -> None:
    html = "<html><head></head><body>ok</body></html>"
    once = inject_pyhtmx_theme(html, theme="aurora")
    twice = inject_pyhtmx_theme(once, theme="aurora")
    assert once == twice
    assert twice.count('data-pyhtmx-theme="aurora"') == 1


def test_inject_pyhtmx_theme_replaces_existing_theme() -> None:
    html = (
        '<html><head><style data-pyhtmx-theme="paper">x</style></head>'
        "<body>ok</body></html>"
    )
    result = inject_pyhtmx_theme(html, theme="aurora")
    assert 'data-pyhtmx-theme="aurora"' in result
    assert 'data-pyhtmx-theme="paper"' not in result


def test_create_window_default_theme_is_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(pyhtmx_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(pyhtmx_module.webview, "start", lambda: None)
    pyhtmx_module.create_window("title", "<html><body>ok</body></html>", start=False)

    assert f'data-pyhtmx-theme="{DEFAULT_THEME}"' in captured["kwargs"]["html"]


def test_create_window_theme_none_skips_theme_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_window(*args, **kwargs):
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(pyhtmx_module.webview, "create_window", fake_create_window)
    monkeypatch.setattr(pyhtmx_module.webview, "start", lambda: None)
    pyhtmx_module.create_window(
        "title",
        "<html><body>ok</body></html>",
        theme=None,
        start=False,
    )

    assert "data-pyhtmx-theme" not in captured["kwargs"]["html"]
    assert 'data-pyhtmx="true"' in captured["kwargs"]["html"]
