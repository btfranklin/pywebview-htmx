from __future__ import annotations

from pywebview_htmx import encode_params_attr


def test_encode_params_attr_returns_json_string() -> None:
    encoded = encode_params_attr({"count": 3, "enabled": True})
    assert encoded == "{&quot;count&quot;: 3, &quot;enabled&quot;: true}"


def test_encode_params_attr_escapes_quotes_and_tags() -> None:
    encoded = encode_params_attr({"message": '"hi" <b>unsafe</b>'})
    assert "\\&quot;hi\\&quot;" in encoded
    assert "&lt;b&gt;unsafe&lt;/b&gt;" in encoded


def test_encode_params_attr_is_exported_from_package() -> None:
    encoded = encode_params_attr({"name": "pywebview-htmx"})
    assert isinstance(encoded, str)
