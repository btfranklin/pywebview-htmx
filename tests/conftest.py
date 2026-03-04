from __future__ import annotations

import re

import pytest

from pywebview_htmx import get_runtime_script


@pytest.fixture(scope="session")
def js_source() -> str:
    return get_runtime_script()


@pytest.fixture(scope="session")
def js_compact(js_source: str) -> str:
    return re.sub(r"\s+", " ", js_source).strip()
