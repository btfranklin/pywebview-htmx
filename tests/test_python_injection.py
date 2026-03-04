from __future__ import annotations

import pytest

from pywebview_htmx import get_runtime_script, inject_runtime

TESTED_BEHAVIOR_IDS = set(range(10, 31))
MARKER = 'data-pywebview-htmx="true"'
SCRIPT_MARKER = '<script data-pywebview-htmx="true">'


@pytest.mark.parametrize(
    ("html", "closing_tag"),
    [
        ("<html><body><div>x</div></body></html>", "</body>"),
        ("<html><body><div>x</div></BODY></html>", "</BODY>"),
        ("<html><body><div>x</div></BoDy></html>", "</BoDy>"),
    ],
)
def test_injects_before_closing_body_variants(html: str, closing_tag: str) -> None:
    result = inject_runtime(html)
    assert MARKER in result
    assert result.index(MARKER) < result.index(closing_tag)


def test_appends_when_body_tag_is_missing() -> None:
    html = "<html><div>content</div></html>"
    result = inject_runtime(html)
    assert result.startswith(html)
    assert result.endswith("</script>")


def test_preserves_prefix_content() -> None:
    html = "PREFIX<html><body>content</body></html>"
    result = inject_runtime(html)
    assert result.startswith("PREFIX<html><body>content")


def test_preserves_suffix_after_closing_body() -> None:
    html = "<html><body>content</body></html>SUFFIX"
    result = inject_runtime(html)
    assert result.endswith("</html>SUFFIX")


def test_uses_last_closing_body_when_multiple_present() -> None:
    html = "<body>first</body><div>middle</div></body>"
    result = inject_runtime(html)
    assert result.index(MARKER) > result.lower().find("</body>")
    assert result.index(MARKER) < result.lower().rfind("</body>")


def test_first_injection_has_single_marker() -> None:
    html = "<html><body>content</body></html>"
    result = inject_runtime(html)
    assert result.count(MARKER) == 1


def test_injection_is_idempotent() -> None:
    html = "<html><body>content</body></html>"
    once = inject_runtime(html)
    twice = inject_runtime(once)
    assert twice == once


def test_second_injection_does_not_add_duplicate_marker() -> None:
    html = "<html><body>content</body></html>"
    result = inject_runtime(inject_runtime(html))
    assert result.count(MARKER) == 1


@pytest.mark.parametrize(
    "html",
    [
        '<html><body><script data-pywebview-htmx="true"></script></body></html>',
        '<html><body><SCRIPT DATA-PYWEBVIEW-HTMX="true"></SCRIPT></body></html>',
        (
            '<html><body><script type="text/javascript" '
            'data-pywebview-htmx="true"></script></body></html>'
        ),
    ],
)
def test_skips_if_marked_script_already_present(html: str) -> None:
    assert inject_runtime(html) == html


def test_non_script_data_marker_does_not_block_injection() -> None:
    html = '<html><body><div data-pywebview-htmx="true"></div></body></html>'
    result = inject_runtime(html)
    assert result != html
    assert result.count(SCRIPT_MARKER) == 1


def test_empty_html_input_gets_injected_script() -> None:
    result = inject_runtime("")
    assert MARKER in result


def test_inject_always_returns_string() -> None:
    assert isinstance(inject_runtime("<div>x</div>"), str)


def test_no_body_with_existing_marker_is_unchanged() -> None:
    html = '<script data-pywebview-htmx="true"></script>'
    assert inject_runtime(html) == html


def test_injection_contains_full_script_content() -> None:
    result = inject_runtime("<html><body>x</body></html>")
    assert get_runtime_script() in result


def test_injection_handles_surrounding_whitespace() -> None:
    html = "  <html><body>x</body></html>  "
    result = inject_runtime(html)
    assert result.startswith("  <html><body>x")
    assert result.endswith("</html>  ")


def test_injection_preserves_unrelated_script_tags() -> None:
    html = "<html><body><script>var x = 1;</script>content</body></html>"
    result = inject_runtime(html)
    assert "<script>var x = 1;</script>" in result
    assert result.count("<script>var x = 1;</script>") == 1
