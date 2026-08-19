#!/usr/bin/env python3
"""AUTHORING_KITとTask01--06を非破壊working copyで最終検証する。

REF_1012の既知の形式矛盾だけを、exact-ROM監査に基づいてDOUBLEのArchive
consumerとして正規化する。受領ディレクトリとDownloadsのZIPは変更しない。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION"
AUTHORING_NAME = "Pokemon-Vega_Trainer-AUTHORING-KIT_STAGE34_20260819"
TASK_NAMES = (
    "VEGA_TRAINER_CHANGEKIT_TASK01_GLOBAL",
    "VEGA_TRAINER_CHANGEKIT_TASK02_TOHOKU_EARLY",
    "VEGA_TRAINER_CHANGEKIT_TASK03_TOHOKU_MID",
    "VEGA_TRAINER_CHANGEKIT_TASK04_TOHOKU_LATE",
    "VEGA_TRAINER_CHANGEKIT_TASK05_LEAGUE_POSTGAME",
    "VEGA_TRAINER_CHANGEKIT_TASK06_KANTO",
)
OUTPUT_DIR = Path("build/validated_inputs")
AUTHORING_ZIP = OUTPUT_DIR / f"{AUTHORING_NAME}_AUTOFIXED.zip"
TASK05_ZIP = OUTPUT_DIR / f"{TASK_NAMES[4]}_AUTOFIXED.zip"
EVIDENCE = Path("reports/generated/trainer_changekit_input_validation.json")
REPORT = Path("reports/generated/trainer_changekit_input_validation.md")
REF1012 = "ENC_TOHOKU_REF_1012"


class InputValidationError(RuntimeError):
    """入力discovery、working correction、validator、packageの契約違反。"""


def _fail(message: str) -> NoReturn:
    raise InputValidationError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _input_root() -> Path:
    candidates = (
        ROOT.parent / "integration_inputs",
        ROOT.parent.parent / "integration_inputs",
        ROOT / "userfile/imports/trainer_changekit_final/integration_inputs",
    )
    for candidate in candidates:
        if (candidate / AUTHORING_NAME / "TASK_SEQUENCE.json").is_file() and all(
            (candidate / name / "KIT_MANIFEST.json").is_file() for name in TASK_NAMES
        ):
            return candidate.resolve()
    _fail("validated integration input root cannot be discovered")


def _atomic_write(path: Path, raw: bytes) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, target)


def _update_encounter_format(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    if not fields or "encounter_key" not in fields or "battle_type" not in fields:
        _fail(f"encounter CSV schema differs: {path}")
    matches = [row for row in rows if row["encounter_key"] == REF1012]
    if len(matches) != 1:
        _fail(f"REF_1012 row is not unique: {path}")
    before = matches[0]["battle_type"]
    if before not in {"UNKNOWN", "DOUBLE"}:
        _fail(f"REF_1012 unexpected source format: {before}")
    matches[0]["battle_type"] = "DOUBLE"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return {"before": before, "after": "DOUBLE"}


def _run(
    command: Sequence[str],
    label: str,
    *,
    allow_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        list(command), cwd=ROOT, env=environment,
        text=True, capture_output=True, check=False,
    )
    if completed.returncode and not allow_failure:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed


def _validation(
    validator: Path,
    authoring: Path,
    change: Path | None,
    global_kit: Path | None,
    output: Path,
    *,
    allow_failure: bool = False,
) -> dict[str, Any]:
    if change is None:
        command = [
            sys.executable, str(validator), "--authoring-kit", str(authoring),
            "--json-out", str(output),
        ]
    else:
        command = [
            sys.executable, str(validator), "--authoring-kit", str(authoring),
            "--change-kit", str(change), "--json-out", str(output),
        ]
        if global_kit is not None:
            command.extend(("--global-kit", str(global_kit)))
    completed = _run(command, f"validator {output.stem}", allow_failure=allow_failure)
    try:
        value = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"validator result is invalid: {output}: {exc}")
    if not isinstance(value, dict):
        _fail(f"validator result root differs: {output}")
    if not allow_failure and (completed.returncode or value.get("status") != "PASS"):
        _fail(f"validator did not report PASS: {output}: {value.get('errors')}")
    return value


def _package(
    script: Path,
    authoring: Path,
    output: Path,
    *,
    change: Path | None = None,
    global_kit: Path | None = None,
) -> bytes:
    command = [sys.executable, str(script), "--authoring-kit", str(authoring)]
    if change is not None:
        command.extend(("--change-kit", str(change)))
    if global_kit is not None:
        command.extend(("--global-kit", str(global_kit)))
    command.extend(("--output", str(output)))
    _run(command, f"package {output.name}")
    raw = output.read_bytes()
    if not raw.startswith(b"PK\x03\x04"):
        _fail(f"packaged ZIP signature differs: {output}")
    return raw


def _build_working_copy(input_root: Path) -> tuple[dict[str, Any], bytes, bytes]:
    with tempfile.TemporaryDirectory(prefix="vega-trainer-input-validation-") as temporary:
        temp = Path(temporary)
        authoring = temp / AUTHORING_NAME
        shutil.copytree(input_root / AUTHORING_NAME, authoring)
        # Running the received validators may have left interpreter caches in
        # the editable extraction.  They are never design input and the kit
        # contract explicitly prohibits binary content.
        for cache in sorted(authoring.rglob("__pycache__"), reverse=True):
            if cache.is_dir():
                shutil.rmtree(cache)
        tasks = []
        for name in TASK_NAMES:
            destination = temp / name
            shutil.copytree(input_root / name, destination)
            tasks.append(destination)

        authoring_source = authoring / "source/v5/data/trainer_encounters.csv"
        task05_source = tasks[4] / "data/trainer_encounters.csv"
        authoring_correction = _update_encounter_format(authoring_source)
        task05_correction = _update_encounter_format(task05_source)

        tools = authoring / "tools"
        _run(
            [sys.executable, str(tools / "build_partitions.py"),
             "--authoring-kit", str(authoring)],
            "rebuild corrected partitions",
        )
        authoring_package_path = temp / AUTHORING_ZIP.name
        authoring_zip = _package(
            tools / "package_authoring_kit.py", authoring, authoring_package_path
        )

        task05_package_path = temp / TASK05_ZIP.name
        task05_zip = _package(
            tools / "package_change_kit.py", authoring, task05_package_path,
            change=tasks[4], global_kit=tasks[0],
        )

        results: dict[str, Any] = {}
        authoring_result_path = temp / "authoring_validation.json"
        results["authoring"] = _validation(
            tools / "validate_authoring_kit.py", authoring, None, None,
            authoring_result_path,
        )
        for index, task in enumerate(tasks, start=1):
            result_path = temp / f"task{index:02d}_validation.json"
            results[f"task{index:02d}"] = _validation(
                tools / "validate_change_kit.py", authoring, task,
                None if index == 1 else tasks[0], result_path,
            )
        if not all(row.get("status") == "PASS" for row in results.values()):
            _fail("one or more corrected working validators did not PASS")

        source_partition = None
        with (authoring / "partitions/encounter_partition.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            for row in csv.DictReader(stream):
                if row["encounter_key"] == REF1012:
                    source_partition = row
                    break
        if source_partition is None or source_partition["battle_format"] != "DOUBLE":
            _fail("corrected REF_1012 partition is not DOUBLE")

        evidence = {
            "schema_version": 1,
            "task": TASK,
            "status": "PASS",
            "input_root": "integration_inputs (Downloads ZIPs remain untouched)",
            "baseline": json.loads((authoring / "BASELINE.json").read_text(encoding="utf-8")),
            "correction": {
                "encounter_key": REF1012,
                "authoring_battle_type": authoring_correction,
                "task05_battle_type": task05_correction,
                "partition_battle_format": source_partition["battle_format"],
                "physical_fact": {
                    "cited_address": "0x0885B0C0",
                    "cited_opcode": "0x62 cleartrainerflag (not trainerbattle)",
                    "canonical_owner": "ENC_TOHOKU_REF_1013",
                    "canonical_command": "0x08890AFB",
                    "canonical_kind": 8,
                },
                "runtime_resolution": "unique DOUBLE ARCHIVE consumer; false flag reference is never patched",
            },
            "packages": {
                "authoring": {"path": AUTHORING_ZIP.as_posix(),
                              "sha256": _sha(authoring_zip), "size": len(authoring_zip)},
                "task05": {"path": TASK05_ZIP.as_posix(),
                           "sha256": _sha(task05_zip), "size": len(task05_zip)},
            },
            "validators": results,
            "original_inputs_mutated": False,
        }
        return evidence, authoring_zip, task05_zip


def _report(evidence: Mapping[str, Any]) -> bytes:
    validators = evidence["validators"]
    statuses = ", ".join(f"{name}={row['status']}" for name, row in validators.items())
    return f"""# Trainer ChangeKit input validation

## 結論

- AUTHORING_KITとTask 01〜06を非破壊working copyで検証し、全validatorがPASSした。
- REF_1012は`0x0885B0C0`のflag命令を戦闘と誤認した入力矛盾だったため、元命令を変更せず、REF_1013のkind 8に対応する固有DOUBLE Archive consumerへ正規化した。
- corrected AUTHORING_KITとTask05は決定的ZIPへ再梱包し、CRC・SHA256SUMS・再展開validatorを通した。
- Downloadsの受領ZIPと展開済み入力は変更していない。

## Validator

{statuses}

## Corrected packages

- AUTHORING: `{evidence['packages']['authoring']['sha256']}`
- Task05: `{evidence['packages']['task05']['sha256']}`
""".encode("utf-8")


def build(*, write: bool) -> dict[str, Any]:
    evidence, authoring_zip, task05_zip = _build_working_copy(_input_root())
    report = _report(evidence)
    if write:
        _atomic_write(AUTHORING_ZIP, authoring_zip)
        _atomic_write(TASK05_ZIP, task05_zip)
        _atomic_write(EVIDENCE, _stable(evidence))
        _atomic_write(REPORT, report)
    else:
        expected = {
            AUTHORING_ZIP: authoring_zip,
            TASK05_ZIP: task05_zip,
            EVIDENCE: _stable(evidence),
            REPORT: report,
        }
        differences = [
            path.as_posix() for path, raw in expected.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != raw
        ]
        if differences:
            _fail("published validator artifacts differ: " + ", ".join(differences))
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = build(write=args.mode == "build")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, InputValidationError) as exc:
        print(f"Trainer ChangeKit input validation {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"Trainer ChangeKit input validation {args.mode}: PASS "
        f"validators={len(evidence['validators'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
