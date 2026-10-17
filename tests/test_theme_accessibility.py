from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page

from pywebview_htmx import inject_theme, list_themes


THEMES = list_themes()
BUTTONS = {
    "default": ".pyh-btn:not([class*='pyh-btn-'])",
    "primary": ".pyh-btn-primary",
    "secondary": ".pyh-btn-secondary",
    "ghost": ".pyh-btn-ghost",
    "danger": ".pyh-btn-danger",
}
MARKUP = """<!doctype html>
<html><head></head><body><main class="pyh-shell"><section class="pyh-card">
<button class="pyh-btn">Default</button>
<button class="pyh-btn pyh-btn-primary">Primary</button>
<button class="pyh-btn pyh-btn-secondary">Secondary</button>
<button class="pyh-btn pyh-btn-ghost">Ghost</button>
<button class="pyh-btn pyh-btn-danger">Danger</button>
<div class="pyh-fields">
  <input id="input" value="Input">
  <select id="select"><option>Option</option></select>
  <textarea id="textarea">Text</textarea>
</div>
<details open><summary id="summary">Details</summary></details>
<span class="pyh-wait-target py-waiting">
  <span class="pyh-busy-pill"></span>Waiting
</span>
<div id="unrelated-motion"
  style="animation: external-motion 3s linear infinite; transition: opacity 2s">
  External motion sample
</div>
</section></main></body></html>"""


def _rgb(color: str) -> tuple[int, int, int]:
    match = re.fullmatch(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)",
        color,
    )
    assert match, f"Expected a browser RGB color, got {color!r}"
    return tuple(int(channel) for channel in match.groups())


def _luminance(color: tuple[int, int, int]) -> float:
    channels = [channel / 255 for channel in color]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("theme", THEMES)
def test_theme_buttons_have_readable_text_in_each_state(page: Page, theme: str) -> None:
    page.set_content(inject_theme(MARKUP, theme))
    assert page.locator(f'head style[data-pywebview-theme="{theme}"]').count() == 1

    for variant, selector in BUTTONS.items():
        button = page.locator(selector)
        button.evaluate("element => element.classList.add('py-waiting')")
        try:
            for state in ("normal", "hover", "active"):
                if state == "normal":
                    page.mouse.move(0, 0)
                    page.mouse.up()
                else:
                    button.hover()
                if state == "active":
                    page.mouse.down()
                else:
                    page.mouse.up()
                colors = button.evaluate(
                    """element => {
                      const style = getComputedStyle(element);
                      return {
                        foreground: style.color,
                        opacity: style.opacity,
                        backgrounds: style.backgroundImage === 'none'
                          ? [style.backgroundColor]
                          : [...style.backgroundImage.matchAll(/rgba?\\([^)]*\\)/g)]
                              .map(match => match[0]),
                        filter: style.filter
                      };
                    }"""
                )
                foreground = _rgb(colors["foreground"])
                backgrounds = [_rgb(color) for color in colors["backgrounds"]]
                assert backgrounds, f"{theme} {variant} has no sampled background stops"
                assert colors["opacity"] == "1", (
                    f"{theme} {variant} waiting state changes text contrast"
                )
                assert colors["filter"] == "none", (
                    f"{theme} {variant} changes contrast on {state}"
                )
                for background in backgrounds:
                    ratio = _contrast(foreground, background)
                    assert ratio >= 4.5, (
                        f"{theme} {variant} text contrast is {ratio:.2f}:1 "
                        f"on {state} background {background}"
                    )
        finally:
            page.mouse.up()
            button.evaluate("element => element.classList.remove('py-waiting')")

    expected_scheme = "light" if theme == "paper" else "dark"
    color_scheme = page.locator("html").evaluate(
        "element => getComputedStyle(element).colorScheme"
    )
    assert color_scheme == expected_scheme


@pytest.mark.parametrize("theme", THEMES)
def test_theme_controls_have_visible_keyboard_focus(page: Page, theme: str) -> None:
    page.set_content(inject_theme(MARKUP, theme))

    page.keyboard.press("Tab")
    for selector in (
        ".pyh-btn",
        "#input",
        "#select",
        "#textarea",
        "#summary",
    ):
        control = page.locator(selector).first
        control.focus()
        assert control.evaluate("element => element.matches(':focus-visible')")
        focus = control.evaluate(
            """element => {
              const style = getComputedStyle(element);
              return {
                focusVisible: element.matches(":focus-visible"),
                width: style.outlineWidth,
                style: style.outlineStyle,
                color: style.outlineColor
              };
            }"""
        )
        assert focus["focusVisible"]
        assert float(focus["width"].removesuffix("px")) >= 3
        assert focus["style"] == "solid"
        assert _rgb(focus["color"])


@pytest.mark.parametrize("theme", THEMES)
def test_reduced_motion_keeps_busy_marker_visible(page: Page, theme: str) -> None:
    page.emulate_media(reduced_motion="reduce")
    page.set_content(inject_theme(MARKUP, theme))

    button = page.locator(".pyh-btn").first
    button.hover()
    reduced = button.evaluate(
        """element => ({
          transform: getComputedStyle(element).transform,
          transitionDuration: getComputedStyle(element).transitionDuration
        })"""
    )
    assert reduced["transform"] == "none"
    durations = reduced["transitionDuration"].split(", ")
    assert all(float(value.removesuffix("s")) <= 0.00001 for value in durations)
    unrelated = page.locator("#unrelated-motion").evaluate(
        """element => {
          const style = getComputedStyle(element);
          return {animation: style.animationName, duration: style.animationDuration,
            transition: style.transitionDuration};
        }"""
    )
    assert unrelated == {
        "animation": "external-motion",
        "duration": "3s",
        "transition": "2s",
    }

    marker = page.locator(".pyh-busy-pill")
    marker_style = marker.evaluate(
        """element => {
          const style = getComputedStyle(element);
          return {
            visibility: style.visibility,
            animation: style.animationName,
            border: style.borderTopColor
          };
        }"""
    )
    assert marker_style["visibility"] == "visible"
    assert marker_style["animation"] == "none"
    assert _rgb(marker_style["border"])
