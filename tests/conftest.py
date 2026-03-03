from __future__ import annotations

import re

import pytest

from pyhtmx import get_pyhtmx_script


@pytest.fixture(scope="session")
def js_source() -> str:
    return get_pyhtmx_script()


@pytest.fixture(scope="session")
def js_compact(js_source: str) -> str:
    return re.sub(r"\s+", " ", js_source).strip()
