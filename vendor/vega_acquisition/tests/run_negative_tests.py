#!/usr/bin/env python3
"""Apply each negative fixture to an isolated package copy and require validation failure."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def mutate_csv(path: Path, selector: dict[str, str], updates: dict[str, str]) -> None:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    matches = [row for row in rows if all(row.get(key) == value for key, value in selector.items())]
    if len(matches) != 1:
        raise ValueError(f"selector matches {len(matches)} rows in {path}: {selector}")
    matches[0].update(updates)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    package = Path(__file__).resolve().parents[1]
    fixtures = json.loads((package / "tests/fixtures/negative_cases.json").read_text(encoding="utf-8"))["fixtures"]
    for fixture in fixtures:
        with tempfile.TemporaryDirectory() as temp_text:
            temp = Path(temp_text) / "package"
            shutil.copytree(package, temp)
            mutate_csv(temp / fixture["file"], fixture["selector"], fixture["updates"])
            completed = subprocess.run(
                [sys.executable, str(temp / "scripts/validate_acquisition_content.py"), "--package", str(temp)],
                text=True, capture_output=True, check=False,
            )
            detail = (completed.stderr or completed.stdout)
            if completed.returncode == 0 or fixture["expected_error_contains"] not in detail:
                print(f"negative fixture did not fail as expected: {fixture['fixture_key']}\n{detail}", file=sys.stderr)
                return 1
            print(f"{fixture['fixture_key']}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
