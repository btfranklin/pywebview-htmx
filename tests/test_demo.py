from __future__ import annotations

import pytest
from playwright.sync_api import Page
from runpy import run_path
from pathlib import Path

from pywebview_htmx import inject_runtime, inject_theme

demo = run_path(str(Path(__file__).resolve().parents[1] / "app.py"))
api = demo["api"]
html_content = demo["html_content"]


@pytest.fixture
def demo_page(page: Page) -> Page:
    page.set_content(inject_theme(inject_runtime(html_content)))
    page.evaluate(
        """() => {
          window.bridgeCalls = [];
          window.pywebview = {api: new Proxy({}, {
            get(_target, method) {
              return async params => {
                window.bridgeCalls.push({method, params});
                if (method === 'switch_theme') {
                  return window.themeMarkup;
                }
                if (method === 'show_params') {
                  return '<pre class="pyh-code">' + JSON.stringify(params) + '</pre>';
                }
                return '<article class="pyh-result">Completed.</article>';
              };
            }
          })};
        }"""
    )
    return page


def test_demo_starts_with_examples_and_compact_theme_picker(demo_page: Page) -> None:
    page = demo_page
    assert page.locator(".pyh-hero h1").inner_text() == "PyWebview HTMX"
    assert page.locator("#theme-picker h2").inner_text() == "Theme"
    assert page.locator("main > .pyh-grid").count() == 1
    assert page.locator("#runtime-diagnostics").evaluate(
        "element => element.open"
    ) is False
    assert page.locator("#runtime-diagnostics").evaluate(
        """element => element.compareDocumentPosition(
          document.querySelector('.pyh-grid')
        )"""
    ) & 2
    assert page.locator(".demo-example").count() == 9
    assert page.locator("#runtime-diagnostics").locator("summary").inner_text() == (
        "Runtime diagnostics"
    )


def test_first_example_fits_initial_desktop_viewport(
    demo_page: Page,
    tmp_path,
) -> None:
    page = demo_page
    page.set_viewport_size({"width": 1280, "height": 900})
    first_example = page.locator(".demo-example").first.bounding_box()
    assert first_example is not None
    assert first_example["y"] + first_example["height"] <= 900
    page.screenshot(path=str(tmp_path / "demo-desktop.png"))


@pytest.mark.parametrize("width", [320, 375])
def test_demo_fits_narrow_viewports_without_horizontal_scroll(
    demo_page: Page,
    width: int,
    tmp_path,
) -> None:
    page = demo_page
    page.set_viewport_size({"width": width, "height": 900})
    page.wait_for_timeout(50)
    assert page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth"
    )
    assert page.locator("#echo-message").is_visible()
    assert page.locator("#run-timeout-button").is_visible()
    page.screenshot(path=str(tmp_path / f"demo-{width}px.png"))


def test_theme_picker_uses_state_and_stable_focus_ids(
    demo_page: Page,
) -> None:
    page = demo_page
    next_picker = api.switch_theme({"theme": "paper"})
    page.evaluate("markup => { window.themeMarkup = markup; }", next_picker)
    page.locator("#theme-paper").click()
    selected = page.locator("#theme-paper")
    selected.wait_for()
    assert selected.get_attribute("aria-pressed") == "true"
    assert page.locator("#theme-aurora").get_attribute("aria-pressed") == "false"
    assert page.locator("#theme-picker style").get_attribute(
        "data-pywebview-theme"
    ) == "paper"
    assert page.locator("#replace-panel-button").count() == 1
    assert page.locator("#morph-button").count() == 1


def test_invalid_parameters_show_error_near_source_without_calling_python(
    demo_page: Page,
) -> None:
    page = demo_page
    page.locator("#show-invalid-params-button").click()
    status = page.locator("#params-status")
    assert "Request failed:" in status.inner_text()
    assert page.evaluate("window.bridgeCalls") == []


def test_timeout_and_stale_errors_update_status_safely(demo_page: Page) -> None:
    page = demo_page
    source = page.locator("#run-timeout-button")
    page.evaluate(
        """element => {
          element.dispatchEvent(new CustomEvent('py:error', {
            bubbles: true,
            detail: {
              element,
              error: {name: 'TimeoutError', message: 'The request timed out.'},
              phase: 'timeout',
              stale: false
            }
          }));
        }""",
        source.element_handle(),
    )
    status = page.locator("#race-demo-status")
    assert status.inner_text() == (
        "Request timed out. Python may still be working; no retry was sent."
    )
    assert page.evaluate("window.bridgeCalls") == []

    page.evaluate(
        """element => {
          element.dispatchEvent(new CustomEvent('py:error', {
            bubbles: true,
            detail: {
              element,
              error: {name: 'Error', message: 'Old request failed.'},
              requestId: 1,
              stale: true
            }
          }));
        }""",
        source.element_handle(),
    )
    assert status.inner_text() == (
        "Request timed out. Python may still be working; no retry was sent."
    )


def test_native_details_open_with_keyboard(demo_page: Page) -> None:
    page = demo_page
    summary = page.locator(".demo-example details summary").first
    summary.focus()
    page.keyboard.press("Enter")
    assert page.locator(".demo-example details").first.evaluate(
        "element => element.open"
    )
    page.keyboard.press("Enter")
    assert not page.locator(".demo-example details").first.evaluate(
        "element => element.open"
    )
