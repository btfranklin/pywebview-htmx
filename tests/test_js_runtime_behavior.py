from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS = REPO_ROOT / "tests/js_runtime_behavior_harness.mjs"
RUNTIME = REPO_ROOT / "src/pywebview_htmx/static/runtime.js"


def test_runtime_behaviors_execute_in_dom_harness() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for JavaScript runtime behavior tests")

    result = subprocess.run(
        [node, str(HARNESS), str(RUNTIME)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
