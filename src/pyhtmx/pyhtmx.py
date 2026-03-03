from __future__ import annotations

from importlib.resources import files
import re
from typing import Any

import webview

_PYHTMX_SCRIPT_TAG_RE = re.compile(r"<script[^>]*\bdata-pyhtmx\b", re.IGNORECASE)
_PYHTMX_THEME_TAG_RE = re.compile(
    r"<style[^>]*\bdata-pyhtmx-theme\s*=\s*[\"'](?P<name>[^\"']+)[\"'][^>]*>.*?</style>",
    re.IGNORECASE | re.DOTALL,
)
_THEME_BASE_NAME = "base"
DEFAULT_THEME = "aurora"


def list_pyhtmx_themes() -> list[str]:
    """Return all bundled selectable theme names."""
    themes_dir = files("pyhtmx").joinpath("static/themes")
    names = sorted(
        path.name[:-4]
        for path in themes_dir.iterdir()
        if path.is_file() and path.name.endswith(".css")
    )
    return [name for name in names if name != _THEME_BASE_NAME]


def get_pyhtmx_theme_css(theme: str = DEFAULT_THEME) -> str:
    """Return bundled CSS for ``theme``, composed of base + theme overrides."""
    normalized_theme = theme.strip().lower()
    available = list_pyhtmx_themes()
    if normalized_theme not in available:
        options = ", ".join(available)
        raise ValueError(
            f"Unknown pyhtmx theme '{theme}'. Available themes: {options}",
        )

    themes_dir = files("pyhtmx").joinpath("static/themes")
    base_css = themes_dir.joinpath(f"{_THEME_BASE_NAME}.css").read_text(
        encoding="utf-8",
    )
    theme_css = themes_dir.joinpath(f"{normalized_theme}.css").read_text(
        encoding="utf-8",
    )
    return f"{base_css}\n\n{theme_css}"


def get_pyhtmx_script() -> str:
    """Read the bundled pyHTMX JavaScript from package resources."""
    return files("pyhtmx").joinpath("static/pyhtmx.js").read_text(encoding="utf-8")


def inject_pyhtmx(html: str) -> str:
    """Inject the pyHTMX script into an HTML string before ``</body>`` when present."""
    if _PYHTMX_SCRIPT_TAG_RE.search(html):
        return html

    script_content = get_pyhtmx_script()
    injection = f'<script data-pyhtmx="true">{script_content}</script>'

    lower_html = html.lower()
    body_close_idx = lower_html.rfind("</body>")
    if body_close_idx == -1:
        return f"{html}{injection}"

    return f"{html[:body_close_idx]}{injection}{html[body_close_idx:]}"


def inject_pyhtmx_theme(html: str, theme: str = DEFAULT_THEME) -> str:
    """Inject or replace the bundled pyHTMX theme CSS in HTML."""
    normalized_theme = theme.strip().lower()
    css = get_pyhtmx_theme_css(normalized_theme)
    injection = f'<style data-pyhtmx-theme="{normalized_theme}">{css}</style>'

    match = _PYHTMX_THEME_TAG_RE.search(html)
    if match:
        current_theme = match.group("name").strip().lower()
        if current_theme == normalized_theme:
            return html
        start, end = match.span()
        return f"{html[:start]}{injection}{html[end:]}"

    lower_html = html.lower()
    head_close_idx = lower_html.rfind("</head>")
    if head_close_idx != -1:
        return f"{html[:head_close_idx]}{injection}{html[head_close_idx:]}"

    body_close_idx = lower_html.rfind("</body>")
    if body_close_idx != -1:
        return f"{html[:body_close_idx]}{injection}{html[body_close_idx:]}"

    return f"{injection}{html}"


def create_window(
    title: str,
    html: str,
    js_api: Any = None,
    theme: str | None = DEFAULT_THEME,
    start: bool = True,
    **kwargs: Any,
) -> webview.Window:
    """
    Create and start a PyWebview window with pyHTMX auto-injected into the page.

    Args:
        title: Window title.
        html: HTML content for the window.
        js_api: Python API object exposed to JavaScript as ``window.pywebview.api``.
        theme: Bundled theme name to inject. Use ``None`` to disable theme injection.
        start: Whether to call ``webview.start()`` after creating the window.
        **kwargs: Additional keyword args forwarded to ``webview.create_window``.
    """
    html_with_pyhtmx = html
    if theme is not None:
        html_with_pyhtmx = inject_pyhtmx_theme(html_with_pyhtmx, theme)
    html_with_pyhtmx = inject_pyhtmx(html_with_pyhtmx)
    window = webview.create_window(
        title,
        html=html_with_pyhtmx,
        js_api=js_api,
        **kwargs,
    )
    if start:
        webview.start()
    return window
