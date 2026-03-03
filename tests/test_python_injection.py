from __future__ import annotations

import pytest

from pyhtmx import get_pyhtmx_script, inject_pyhtmx

TESTED_BEHAVIOR_IDS = set(range(10, 31))
MARKER = 'data-pyhtmx="true"'
SCRIPT_MARKER = '<script data-pyhtmx="true">'


@pytest.mark.parametrize(
    ("html", "closing_tag"),
    [
        ("<html><body><div>x</div></body></html>", "</body>"),
        ("<html><body><div>x</div></BODY></html>", "</BODY>"),
        ("<html><body><div>x</div></BoDy></html>", "</BoDy>"),
    ],
)
def test_injects_before_closing_body_variants(html: str, closing_tag: str) -> None:
    result = inject_pyhtmx(html)
    assert MARKER in result
    assert result.index(MARKER) < result.index(closing_tag)


def test_appends_when_body_tag_is_missing() -> None:
    html = "<html><div>content</div></html>"
    result = inject_pyhtmx(html)
    assert result.startswith(html)
    assert result.endswith("</script>")


def test_preserves_prefix_content() -> None:
    html = "PREFIX<html><body>content</body></html>"
    result = inject_pyhtmx(html)
    assert result.startswith("PREFIX<html><body>content")


def test_preserves_suffix_after_closing_body() -> None:
    html = "<html><body>content</body></html>SUFFIX"
    result = inject_pyhtmx(html)
    assert result.endswith("</html>SUFFIX")


def test_uses_last_closing_body_when_multiple_present() -> None:
    html = "<body>first</body><div>middle</div></body>"
    result = inject_pyhtmx(html)
    assert result.index(MARKER) > result.lower().find("</body>")
    assert result.index(MARKER) < result.lower().rfind("</body>")


def test_first_injection_has_single_marker() -> None:
    html = "<html><body>content</body></html>"
    result = inject_pyhtmx(html)
    assert result.count(MARKER) == 1


def test_injection_is_idempotent() -> None:
    html = "<html><body>content</body></html>"
    once = inject_pyhtmx(html)
    twice = inject_pyhtmx(once)
    assert twice == once


def test_second_injection_does_not_add_duplicate_marker() -> None:
    html = "<html><body>content</body></html>"
    result = inject_pyhtmx(inject_pyhtmx(html))
    assert result.count(MARKER) == 1


@pytest.mark.parametrize(
    "html",
    [
        '<html><body><script data-pyhtmx="true"></script></body></html>',
        '<html><body><SCRIPT DATA-PYHTMX="true"></SCRIPT></body></html>',
        (
            '<html><body><script type="text/javascript" '
            'data-pyhtmx="true"></script></body></html>'
        ),
    ],
)
def test_skips_if_marked_script_already_present(html: str) -> None:
    assert inject_pyhtmx(html) == html


def test_non_script_data_pyhtmx_does_not_block_injection() -> None:
    html = '<html><body><div data-pyhtmx="true"></div></body></html>'
    result = inject_pyhtmx(html)
    assert result != html
    assert result.count(SCRIPT_MARKER) == 1


def test_empty_html_input_gets_injected_script() -> None:
    result = inject_pyhtmx("")
    assert MARKER in result


def test_inject_always_returns_string() -> None:
    assert isinstance(inject_pyhtmx("<div>x</div>"), str)


def test_no_body_with_existing_marker_is_unchanged() -> None:
    html = '<script data-pyhtmx="true"></script>'
    assert inject_pyhtmx(html) == html


def test_injection_contains_full_script_content() -> None:
    result = inject_pyhtmx("<html><body>x</body></html>")
    assert get_pyhtmx_script() in result


def test_injection_handles_surrounding_whitespace() -> None:
    html = "  <html><body>x</body></html>  "
    result = inject_pyhtmx(html)
    assert result.startswith("  <html><body>x")
    assert result.endswith("</html>  ")


def test_injection_preserves_unrelated_script_tags() -> None:
    html = "<html><body><script>var x = 1;</script>content</body></html>"
    result = inject_pyhtmx(html)
    assert "<script>var x = 1;</script>" in result
    assert result.count("<script>var x = 1;</script>") == 1
