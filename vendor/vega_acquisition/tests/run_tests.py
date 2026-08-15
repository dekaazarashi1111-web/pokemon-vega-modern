#!/usr/bin/env python3
"""Run static validation, reproducibility, host-C runtime, and negative tests."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    if completed.stdout:
        print(completed.stdout, end="")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        run([sys.executable, str(root / "scripts/validate_acquisition_content.py"), "--package", str(root)], root)
        run([sys.executable, str(root / "scripts/build_acquisition_content.py"), "--package", str(root), "--check"], root)
        run([sys.executable, str(root / "tests/run_negative_tests.py")], root)
        run([sys.executable, str(root / "tests/test_wild_sanitizer.py")], root)
        cc = shutil.which(os.environ.get("CC", "cc"))
        if not cc:
            raise RuntimeError("native C compiler not found")
        with tempfile.TemporaryDirectory() as temp_text:
            binary = Path(temp_text) / "test_acquisition_runtime"
            sources = [
                root / "tests/test_acquisition_runtime.c",
                root / "overlays/acquisition_runtime/acquisition_runtime.c",
                root / "overlays/acquisition_runtime/acquisition_save_migration.c",
                root / "generated/acquisition_event_defs.c",
                root / "generated/acquisition_collection_defs.c",
                root / "generated/acquisition_host_defs.c",
            ]
            run([cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-I", str(root), *map(str, sources), "-o", str(binary)], root)
            run([str(binary)], root)
        print("all acquisition package tests: PASS")
    except (OSError, RuntimeError) as error:
        print(f"acquisition package tests failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
