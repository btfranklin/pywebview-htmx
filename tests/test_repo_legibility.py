from __future__ import annotations

import re
import subprocess
import tomllib
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "AGENTS.md",
    "docs/index.md",
    "docs/architecture.md",
    "docs/development.md",
    "docs/releasing.md",
]
AGENT_REQUIRED_LINK_TARGETS = {
    "README.md",
    "docs/index.md",
    "src/pywebview_htmx/runtime.py",
    "src/pywebview_htmx/static/runtime.js",
    "app.py",
    "pyproject.toml",
    "docs/releasing.md",
    "tests",
    "skills/use-pywebview-htmx",
}
REQUIRED_WHEEL_FILES = {
    "pywebview_htmx/__init__.py",
    "pywebview_htmx/py.typed",
    "pywebview_htmx/runtime.py",
    "pywebview_htmx/static/runtime.js",
    "pywebview_htmx/static/themes/aurora.css",
    "pywebview_htmx/static/themes/base.css",
    "pywebview_htmx/static/themes/cybermind.css",
    "pywebview_htmx/static/themes/paper.css",
}
LOCAL_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _iter_local_links(markdown_path: Path) -> list[str]:
    links: list[str] = []
    for raw_link in LOCAL_MARKDOWN_LINK_RE.findall(
        markdown_path.read_text(encoding="utf-8"),
    ):
        target = raw_link.split("#", 1)[0].strip()
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
            continue
        links.append(target)
    return links


def _repo_relative_link_targets(markdown_path: Path) -> set[str]:
    targets: set[str] = set()
    for target in _iter_local_links(markdown_path):
        resolved = (markdown_path.parent / target).resolve()
        try:
            relative_target = resolved.relative_to(REPO_ROOT)
        except ValueError:
            continue
        targets.add(relative_target.as_posix())
    return targets


def _load_pyproject() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def test_required_agent_legibility_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOCS if not (REPO_ROOT / path).exists()]
    assert not missing, f"Missing agent-legibility docs: {missing}"


def test_required_docs_have_resolvable_local_markdown_links() -> None:
    checked_paths = [REPO_ROOT / path for path in REQUIRED_DOCS]
    broken_links: list[str] = []

    for markdown_path in checked_paths:
        for target in _iter_local_links(markdown_path):
            resolved = (markdown_path.parent / target).resolve()
            link_description = f"{markdown_path.relative_to(REPO_ROOT)} -> {target}"
            try:
                resolved.relative_to(REPO_ROOT)
            except ValueError:
                broken_links.append(link_description)
                continue
            if not resolved.exists():
                broken_links.append(link_description)

    assert not broken_links, f"Broken local Markdown links: {broken_links}"


def test_agents_md_links_to_core_repo_surfaces() -> None:
    link_targets = _repo_relative_link_targets(REPO_ROOT / "AGENTS.md")
    missing_targets = sorted(AGENT_REQUIRED_LINK_TARGETS - link_targets)
    assert not missing_targets, (
        f"AGENTS.md is missing link target(s): {missing_targets}"
    )


def test_parsed_project_metadata_declares_pep_561_typing() -> None:
    project_metadata = _load_pyproject()["project"]
    assert project_metadata["name"] == "pywebview-htmx"
    assert "Typing :: Typed" in project_metadata["classifiers"]
    assert (REPO_ROOT / "src/pywebview_htmx/py.typed").is_file()


def test_wheel_contains_runtime_assets_and_typing_marker(tmp_path: Path) -> None:
    subprocess.run(
        ["pdm", "build", "--dest", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, f"Expected one wheel, found: {wheels}"

    with zipfile.ZipFile(wheels[0]) as wheel:
        wheel_files = set(wheel.namelist())

    missing_files = sorted(REQUIRED_WHEEL_FILES - wheel_files)
    assert not missing_files, f"Wheel is missing package file(s): {missing_files}"
