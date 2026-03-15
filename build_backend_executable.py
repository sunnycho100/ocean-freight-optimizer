"""
Build a frozen backend executable for desktop packaging.

Output:
  backend_bin/api_server.exe
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENTRYPOINT = ROOT / "api_server.py"
DIST_DIR = ROOT / "backend_bin"
WORK_DIR = ROOT / "build" / "pyinstaller_work"
SPEC_DIR = ROOT / "build" / "pyinstaller_spec"

COLLECT_ALL_PACKAGES = [
    "pandas",
    "openpyxl",
    "selenium",
    "webdriver_manager",
]

COLLECT_SUBMODULES = [
    "quick_download_package",
    "url_checker_package",
    "hapag_module",
    "chatbot",
]

OPTIONAL_HIDDEN_IMPORTS = [
    "openai",
    "google.generativeai",
]

LOCAL_HIDDEN_IMPORTS = [
    "url_checker_refactored",
    "quick_download_refactored",
    "ONE_processor",
    "hapag_checker",
    "one_pipeline",
    "hapag_pipeline",
]


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> int:
    if not ENTRYPOINT.exists():
        print(f"[build-backend] Missing entrypoint: {ENTRYPOINT}")
        return 1

    if not _has_module("PyInstaller"):
        print("[build-backend] PyInstaller is not installed.")
        print("[build-backend] Install it with:")
        print(f'  "{sys.executable}" -m pip install pyinstaller')
        return 1

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        "api_server",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(WORK_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--paths",
        str(ROOT),
    ]

    for package_name in COLLECT_ALL_PACKAGES:
        cmd.extend(["--collect-all", package_name])

    for package_name in COLLECT_SUBMODULES:
        cmd.extend(["--collect-submodules", package_name])

    for module_name in OPTIONAL_HIDDEN_IMPORTS:
        if _has_module(module_name):
            cmd.extend(["--hidden-import", module_name])

    for module_name in LOCAL_HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module_name])

    cmd.append(str(ENTRYPOINT))

    print("[build-backend] Building backend executable with PyInstaller...")
    print("[build-backend] Command:")
    print("  " + " ".join(cmd))

    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"[build-backend] Build failed with exit code {result.returncode}")
        return result.returncode

    output_file = DIST_DIR / "api_server.exe"
    if not output_file.exists():
        print(f"[build-backend] Build finished but output not found: {output_file}")
        return 1

    print(f"[build-backend] Success: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
