from __future__ import annotations

import re
from pathlib import Path

from test_js_contract_config_and_binding import TESTED_BEHAVIOR_IDS as JS_BINDING_IDS
from test_js_contract_request_and_swap import TESTED_BEHAVIOR_IDS as JS_REQUEST_IDS
from test_python_create_window import TESTED_BEHAVIOR_IDS as WINDOW_IDS
from test_python_injection import TESTED_BEHAVIOR_IDS as INJECTION_IDS
from test_python_script_loading import TESTED_BEHAVIOR_IDS as SCRIPT_IDS


def _catalog_ids() -> set[int]:
    catalog_path = Path(__file__).with_name("BEHAVIOR_CATALOG.md")
    content = catalog_path.read_text(encoding="utf-8")
    return {int(match) for match in re.findall(r"(?m)^(\d+)\.\s", content)}


def test_behavior_catalog_ids_are_1_to_100() -> None:
    assert _catalog_ids() == set(range(1, 101))


def test_every_catalog_behavior_is_claimed_by_a_test_domain() -> None:
    covered = SCRIPT_IDS | INJECTION_IDS | WINDOW_IDS | JS_BINDING_IDS | JS_REQUEST_IDS
    assert covered == _catalog_ids()
