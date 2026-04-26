from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "AGENTS.md",
    "docs/index.md",
    "docs/architecture.md",
    "docs/development.md",
]
AGENT_REQUIRED_ROUTES = [
    "README.md",
    "docs/index.md",
    "src/pywebview_htmx/runtime.py",
    "src/pywebview_htmx/static/runtime.js",
    "app.py",
    "pyproject.toml",
    "tests/",
    "skills/use-pywebview-htmx/",
]
LOCAL_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _read_repo_file(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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


def test_required_agent_legibility_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOCS if not (REPO_ROOT / path).exists()]
    assert not missing, f"Missing agent-legibility docs: {missing}"


def test_new_docs_have_resolvable_local_markdown_links() -> None:
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


def test_agents_md_routes_to_core_repo_surfaces() -> None:
    agents_md = _read_repo_file("AGENTS.md")
    missing_routes = [
        route for route in AGENT_REQUIRED_ROUTES if route not in agents_md
    ]
    assert not missing_routes, f"AGENTS.md is missing route(s): {missing_routes}"


def test_development_guidance_captures_package_policy() -> None:
    combined_guidance = "\n".join(
        _read_repo_file(path) for path in ("AGENTS.md", "docs/development.md")
    ).lower()

    required_fragments = [
        "pdm install",
        "pdm run lint",
        "pdm run test",
        "pdm run python app.py",
        "do not use pip to add",
        ">=",
        "latest version",
    ]
    missing_fragments = [
        fragment for fragment in required_fragments if fragment not in combined_guidance
    ]
    assert not missing_fragments, (
        "Development guidance is missing durable instruction(s): "
        f"{missing_fragments}"
    )
