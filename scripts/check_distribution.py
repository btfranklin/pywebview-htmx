"""Install release artifacts with PDM and check them outside the checkout."""

from __future__ import annotations

import argparse
from email.parser import BytesParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def artifact_version(artifact: Path) -> str:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            names = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            if len(names) != 1:
                raise ValueError(f"Expected one wheel metadata file: {artifact}")
            metadata = archive.read(names[0])
    else:
        with tarfile.open(artifact) as archive:
            names = [
                n for n in archive.getmembers()
                if n.name.endswith('/PKG-INFO') and n.name.count('/') == 1
            ]
            if len(names) != 1:
                raise ValueError(f"Expected one source metadata file: {artifact}")
            stream = archive.extractfile(names[0])
            if stream is None:
                raise ValueError(f"Cannot read source metadata: {artifact}")
            metadata = stream.read()
    parsed = BytesParser().parsebytes(metadata)
    if parsed['Name'] != 'pywebview-htmx' or not parsed['Version']:
        raise ValueError(f"Unexpected package metadata: {artifact}")
    return str(parsed['Version'])


def check(artifact: Path, native: bool) -> None:
    expected_version = artifact_version(artifact)
    with TemporaryDirectory(prefix="pywebview-htmx-release-") as directory:
        project = Path(directory)
        dependencies = [f"pywebview-htmx @ {artifact.as_uri()}"]
        if native and sys.platform.startswith("linux"):
            dependencies.append("pywebview[pyside6]>=6.2.1")
        (project / "pyproject.toml").write_text(
            '[project]\nname = "release-check"\nversion = "0.0.0"\n'
            'requires-python = ">=3.14"\ndependencies = '
            + json.dumps(dependencies)
            + '\n[tool.pdm]\ndistribution = false\n',
            encoding="utf-8",
        )
        environment = os.environ.copy()
        for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PDM_PROJECT"):
            environment.pop(name, None)
        environment.update({
            "PDM_IGNORE_ACTIVE_VENV": "1",
            "PDM_VENV_IN_PROJECT": "1",
            "PDM_CHECK_UPDATE": "false",
        })
        pdm = shutil.which("pdm")
        if pdm is None:
            raise RuntimeError("Install PDM before checking release artifacts")

        def run(*arguments: str, timeout: int = 600) -> None:
            subprocess.run(
                [pdm, *arguments], cwd=project,
                env=environment, check=True, timeout=timeout,
            )

        run("use", "--first", sys._base_executable)
        platform = {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")
        run(
            "lock", "--python",
            f"=={sys.version_info.major}.{sys.version_info.minor}.*",
            "--platform", platform, "--implementation", sys.implementation.name,
        )
        run("sync", "--no-self")
        shutil.copy2(
            ROOT / "scripts/check_installed.py", project / "check_installed.py",
        )
        run("run", "python", "-I", "check_installed.py", expected_version)
        if native:
            shutil.copy2(ROOT / "tests/native_smoke.py", project / "native_smoke.py")
            if sys.platform.startswith("linux"):
                environment["PYWEBVIEW_GUI"] = "qt"
                environment["QT_API"] = "pyside6"
            run("run", "python", "-I", "native_smoke.py", timeout=180)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--native", action="store_true",
        help="Check the installed wheel in a desktop session",
    )
    args = parser.parse_args()
    directory = args.directory.resolve()
    wheels = sorted(directory.glob("*.whl"))
    sources = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        parser.error("Supply exactly one wheel and one source archive")
    if artifact_version(wheels[0]) != artifact_version(sources[0]):
        parser.error("Wheel and source archive versions differ")
    for artifact in wheels if args.native else wheels + sources:
        check(artifact, args.native)


if __name__ == "__main__":
    main()
