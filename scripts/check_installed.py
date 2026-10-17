"""Check an installed distribution without the source checkout on sys.path."""

from __future__ import annotations

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
import sys

import pywebview_htmx
from pywebview_htmx import (
    encode_params_attr,
    get_runtime_script,
    get_theme_css,
    inject_runtime,
    inject_theme,
    list_themes,
)


def main() -> None:
    installed = Path(pywebview_htmx.__file__).resolve()
    assert installed.is_relative_to(Path(sys.prefix).resolve()), installed
    assert version("pywebview-htmx") == sys.argv[1]
    assert files("pywebview_htmx").joinpath("py.typed").is_file()
    script = get_runtime_script()
    assert "window.pywebviewHtmx" in script
    source = '<!doctype html><html><head></head><body>İstanbul</body></html>'
    runtime = inject_runtime(source)
    assert script in runtime
    assert inject_runtime(runtime) == runtime
    assert list_themes() == ["aurora", "cybermind", "paper"]
    for theme in list_themes():
        css = get_theme_css(theme)
        assert ".pyh-btn" in css
        themed = inject_theme(runtime, theme)
        assert css in themed
        assert f'data-pywebview-theme="{theme}"' in themed
        assert inject_theme(themed, theme) == themed
        assert "İstanbul" in themed
    assert "&quot;" in encode_params_attr({"name": 'a "quoted" name'})
    print(f"Installed distribution passed: {version('pywebview-htmx')} at {installed}")


if __name__ == "__main__":
    main()
