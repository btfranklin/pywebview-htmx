from __future__ import annotations

from importlib.resources import files
import re
from typing import Any

import webview

_PYHTMX_SCRIPT_TAG_RE = re.compile(r"<script[^>]*\bdata-pyhtmx\b", re.IGNORECASE)


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


def create_window(
    title: str,
    html: str,
    js_api: Any = None,
    start: bool = True,
    **kwargs: Any,
) -> webview.Window:
    """
    Create and start a PyWebview window with pyHTMX auto-injected into the page.

    Args:
        title: Window title.
        html: HTML content for the window.
        js_api: Python API object exposed to JavaScript as ``window.pywebview.api``.
        start: Whether to call ``webview.start()`` after creating the window.
        **kwargs: Additional keyword args forwarded to ``webview.create_window``.
    """
    html_with_pyhtmx = inject_pyhtmx(html)
    window = webview.create_window(
        title,
        html=html_with_pyhtmx,
        js_api=js_api,
        **kwargs,
    )
    if start:
        webview.start()
    return window
