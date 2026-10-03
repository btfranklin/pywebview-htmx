from __future__ import annotations

from importlib.resources import files
import json
from html import escape as html_escape
from html.parser import HTMLParser
from typing import Any

import webview

_THEME_BASE_NAME = "base"
DEFAULT_THEME = "aurora"


class _AssetTags(HTMLParser):
    """Find active asset tags and closing tags in the original HTML."""

    CDATA_CONTENT_ELEMENTS = (
        *HTMLParser.CDATA_CONTENT_ELEMENTS, "title", "textarea", "noscript",
    )

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self._html = html
        self._line_starts = [0] + [
            index + 1 for index, char in enumerate(html) if char == "\n"
        ]
        self._template_depth = 0
        self._theme_start: tuple[int, str] | None = None
        self.runtime_present = False
        self.theme: tuple[int, int, str] | None = None
        self.closing_tags: dict[str, int] = {}
        self.feed(html)
        self.close()

    def _offset(self) -> int:
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag == "template":
            self._template_depth += 1
        if self._template_depth:
            return

        attributes: dict[str, str | None] = {}
        for name, value in attrs:
            attributes.setdefault(name, value)
        marker = attributes.get("data-pywebview-htmx")
        if tag == "script" and marker is not None and marker.lower() == "true":
            self.runtime_present = True
        if tag == "style" and self.theme is None:
            theme = attributes.get("data-pywebview-theme")
            if theme is not None:
                self._theme_start = (self._offset(), theme)

    def handle_endtag(self, tag: str) -> None:
        if tag == "template" and self._template_depth:
            self._template_depth -= 1
            return
        if self._template_depth:
            return

        offset = self._offset()
        if tag in {"head", "body"}:
            self.closing_tags[tag] = offset
        if tag == "style" and self._theme_start is not None:
            start, theme = self._theme_start
            end = self._html.index(">", offset) + 1
            self.theme = (start, end, theme)
            self._theme_start = None


def list_themes() -> list[str]:
    """Return all bundled selectable theme names."""
    themes_dir = files("pywebview_htmx").joinpath("static/themes")
    names = sorted(
        path.name[:-4]
        for path in themes_dir.iterdir()
        if path.is_file() and path.name.endswith(".css")
    )
    return [name for name in names if name != _THEME_BASE_NAME]


def get_theme_css(theme: str = DEFAULT_THEME) -> str:
    """Return bundled CSS for ``theme``, composed of base + theme overrides."""
    normalized_theme = theme.strip().lower()
    available = list_themes()
    if normalized_theme not in available:
        options = ", ".join(available)
        raise ValueError(
            f"Unknown theme '{theme}'. Available themes: {options}",
        )

    themes_dir = files("pywebview_htmx").joinpath("static/themes")
    base_css = themes_dir.joinpath(f"{_THEME_BASE_NAME}.css").read_text(
        encoding="utf-8",
    )
    theme_css = themes_dir.joinpath(f"{normalized_theme}.css").read_text(
        encoding="utf-8",
    )
    return f"{base_css}\n\n{theme_css}"


def get_runtime_script() -> str:
    """Read the bundled JavaScript runtime from package resources."""
    return files("pywebview_htmx").joinpath("static/runtime.js").read_text(
        encoding="utf-8",
    )


def encode_params_attr(params: Any) -> str:
    """Encode a payload for safe embedding in ``data-py-params``."""
    return html_escape(
        json.dumps(params, sort_keys=True, allow_nan=False),
        quote=True,
    )


def inject_runtime(html: str) -> str:
    """Inject the runtime script into an HTML string before ``</body>`` when present."""
    tags = _AssetTags(html)
    if tags.runtime_present:
        return html

    script_content = get_runtime_script()
    injection = f'<script data-pywebview-htmx="true">{script_content}</script>'

    body_close_idx = tags.closing_tags.get("body", len(html))
    return f"{html[:body_close_idx]}{injection}{html[body_close_idx:]}"


def inject_theme(html: str, theme: str = DEFAULT_THEME) -> str:
    """Inject or replace the bundled theme CSS in HTML."""
    normalized_theme = theme.strip().lower()
    css = get_theme_css(normalized_theme)
    injection = f'<style data-pywebview-theme="{normalized_theme}">{css}</style>'

    tags = _AssetTags(html)
    if tags.theme is not None:
        start, end, current_theme = tags.theme
        current_theme = current_theme.strip().lower()
        if current_theme == normalized_theme:
            return html
        return f"{html[:start]}{injection}{html[end:]}"

    insertion_idx = tags.closing_tags.get(
        "head", tags.closing_tags.get("body", 0),
    )
    return f"{html[:insertion_idx]}{injection}{html[insertion_idx:]}"


def create_window(
    title: str,
    html: str,
    js_api: Any = None,
    theme: str | None = DEFAULT_THEME,
    start: bool = True,
    **kwargs: Any,
) -> webview.Window:
    """
    Create and start a PyWebview window with runtime assets auto-injected.

    Args:
        title: Window title.
        html: HTML content for the window.
        js_api: Python API object exposed to JavaScript as ``window.pywebview.api``.
        theme: Bundled theme name to inject. Use ``None`` to disable theme injection.
        start: Whether to call ``webview.start()`` after creating the window.
        **kwargs: Additional keyword args forwarded to ``webview.create_window``.
    """
    html_with_runtime = html
    if theme is not None:
        html_with_runtime = inject_theme(html_with_runtime, theme)
    html_with_runtime = inject_runtime(html_with_runtime)
    window = webview.create_window(
        title,
        html=html_with_runtime,
        js_api=js_api,
        **kwargs,
    )
    if start:
        webview.start()
    return window
