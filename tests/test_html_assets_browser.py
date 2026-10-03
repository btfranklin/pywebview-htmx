from __future__ import annotations

import pytest
from playwright.sync_api import Page

from pywebview_htmx import inject_runtime, inject_theme


@pytest.mark.parametrize(
    "inactive_markup",
    [
        '<!-- <script data-pywebview-htmx="true"></script> -->',
        '<template><script data-pywebview-htmx="true"></script></template>',
        '<textarea><script data-pywebview-htmx="true"></script></textarea>',
        '<!-- <style data-pywebview-theme="paper">example</style> -->',
        '<template><style data-pywebview-theme="paper">example</style></template>',
    ],
)
def test_injected_assets_work_with_unicode_and_inactive_markup(
    page: Page, inactive_markup: str,
) -> None:
    html = (
        "<html>\n<head><title>İstanbul</title></head>\n<body>"
        f"{inactive_markup}"
        '<button id="load" py-call="load" py-target="#result">İstanbul</button>'
        '<div id="result"></div></body></html><!-- </body> </head> -->'
    )
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(inject_runtime(inject_theme(html)))
    page.evaluate(
        """() => {
          window.pywebview = {api: {load: () => '<p>İstanbul loaded</p>'}};
        }"""
    )

    page.locator("#load").click()
    page.locator("#result").get_by_text("İstanbul loaded").wait_for()
    assert page.title() == "İstanbul"
    assert page.locator('body > script[data-pywebview-htmx="true"]').count() == 1
    assert page.locator('head > style[data-pywebview-theme="aurora"]').count() == 1
    assert not page_errors
