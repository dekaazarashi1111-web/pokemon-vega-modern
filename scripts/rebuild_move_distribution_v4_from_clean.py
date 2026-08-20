#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT22 Stage39をBPS chainで厳密再構築する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps  # noqa: E402


TASK = "T22"
CONFIG = Path("config/move_distribution_v4.json")
BUILDER = Path("scripts/build_move_distribution_v4.py")
STAGE38_DIRECT = Path("build/patches/firered-jpn-rev0-to-mirage-production-stage38.bps")
STAGE38_DIRECT_SHA256 = "71e4655c7bf9b88a1639a833ac38b56075e3b5a5850a36d0ab3ed44d6301c058"
EVIDENCE = Path("build/stages/39_clean_rebuild.json")
REPORT = Path("reports/generated/move_distribution_v4_clean_rebuild.md")


class MoveDistributionV4CleanRebuildError(RuntimeError):
    """clean、Stage38、Stage39 BPS chainまたはmGBA証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise MoveDistributionV4CleanRebuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path) -> bytes:
    try:
        return (ROOT / path).read_bytes()
    except OSError as exc:
        _fail(f"required artifact unavailable: {path}: {exc}")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _run(command: Sequence[str], label: str) -> None:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")


def _atomic_write(path: Path, raw: bytes) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, target)


def _validate() -> tuple[dict[str, Any], bytes]:
    config = _json(CONFIG)
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean_path = Path(inputs["clean_rom"]["path"])
    stage38_path = Path(inputs["stage38_rom"]["path"])
    stage39_path = Path(outputs["rom"])
    incremental_path = Path(outputs["incremental_bps"])
    direct_path = Path(outputs["clean_bps"])
    clean = _read(clean_path)
    stage38 = _read(stage38_path)
    stage39 = _read(stage39_path)
    if len(clean) != int(inputs["clean_rom"]["size"]) or _sha(clean) != inputs["clean_rom"]["sha256"]:
        _fail("clean FireRed identity differs")
    if len(stage38) != int(inputs["stage38_rom"]["size"]) or _sha(stage38) != inputs["stage38_rom"]["sha256"]:
        _fail("Stage38 identity differs")
    stage38_direct = _read(STAGE38_DIRECT)
    if _sha(stage38_direct) != STAGE38_DIRECT_SHA256 or apply_bps(clean, stage38_direct) != stage38:
        _fail("clean->Stage38 fixed BPS differs")

    metadata = _json(Path(outputs["metadata"]))
    allocation = _json(Path(outputs["allocation"]))
    incremental = _read(incremental_path)
    direct = _read(direct_path)
    if (
        metadata.get("status") != "PASS"
        or metadata.get("output", {}).get("sha256") != _sha(stage39)
        or metadata.get("input", {}).get("sha256") != _sha(stage38)
        or metadata.get("mgba", {}).get("status") != "PASS"
        or metadata.get("mgba", {}).get("process_count") != 2
        or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
        or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
        or allocation.get("summaries", {}).get("overlap_count") != 0
    ):
        _fail("Stage39 metadata/allocation contract differs")
    chained = apply_bps(apply_bps(clean, stage38_direct), incremental)
    direct_result = apply_bps(clean, direct)
    if chained != stage39 or direct_result != stage39 or chained != direct_result:
        _fail("clean->Stage38->Stage39/direct Stage39 identity differs")
    if (
        metadata["patches"]["incremental"]["sha256"] != _sha(incremental)
        or metadata["patches"]["clean_direct"]["sha256"] != _sha(direct)
        or metadata["patches"]["incremental"]["exact"] is not True
        or metadata["patches"]["clean_direct"]["exact"] is not True
    ):
        _fail("Stage39 BPS metadata differs")

    quick = _json(Path(outputs["mgba_quick"]))
    full = _json(Path(outputs["mgba_full"]))
    for mode, document in (("quick", quick), ("full", full)):
        if (
            document.get("status") != "PASS" or document.get("mode") != mode
            or document.get("rom_sha256") != _sha(stage39)
            or document.get("warnings_errors") != 0
            or document.get("process_runs") != 1
            or any(value is not True for value in document.get("checks", {}).values())
            or any(value is not True for value in document.get("acceptance_checks", {}).values())
        ):
            _fail(f"Stage39 mGBA {mode} evidence differs")
    for key in ("result_identity", "runner_sha256", "symbols_sha256", "cases_sha256"):
        if quick.get(key) != full.get(key):
            _fail(f"Stage39 mGBA quick/full {key} differs")

    evidence = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE38_BPS_PLUS_STAGE39_SERIALIZER_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage38_sha256": _sha(stage38),
            "stage39_sha256": _sha(stage39),
            "stage39_metadata_sha256": _sha(_read(Path(outputs["metadata"]))),
            "stage39_allocation_sha256": _sha(_read(Path(outputs["allocation"]))),
        },
        "chain": [
            {"artifact": clean_path.as_posix(), "sha256": _sha(clean), "size": len(clean)},
            {"artifact": STAGE38_DIRECT.as_posix(), "sha256": _sha(stage38_direct), "size": len(stage38_direct)},
            {"artifact": stage38_path.as_posix(), "sha256": _sha(stage38), "size": len(stage38)},
            {"artifact": BUILDER.as_posix(), "sha256": _sha(_read(BUILDER))},
            {"artifact": incremental_path.as_posix(), "sha256": _sha(incremental), "size": len(incremental)},
            {"artifact": stage39_path.as_posix(), "sha256": _sha(stage39), "size": len(stage39)},
        ],
        "bps": {
            "stage38_incremental": {"sha256": _sha(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct), "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": {
            "changed_byte_count": metadata["change_audit"]["changed_byte_count"],
            "outside_declared_span_count": 0, "declared_span_overlap_count": 0,
        },
        "allocator_overlap_count": 0,
        "mgba": {
            "process_count": 2, "result_identity": quick["result_identity"],
            "quick_artifact_sha256": _sha(_read(Path(outputs["mgba_quick"]))),
            "full_artifact_sha256": _sha(_read(Path(outputs["mgba_full"]))),
            "warnings_errors": 0,
        },
    }
    report = f"""# T22 Move Distribution V4 clean rebuild

- clean FireRed日本版Rev.0→Stage38→Stage39 chainとclean→Stage39直接BPSが同一ROMになった。
- Stage38→39 incremental BPS、clean直接BPSを完全往復した。
- allocator/declared-span overlap 0、declared span外変更0。
- mGBA quick/full独立2 processはwarnings/errors 0、result identity一致。

- Stage38 SHA-256: `{evidence['input_output']['stage38_sha256']}`
- Stage39 SHA-256: `{evidence['input_output']['stage39_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage39 serializer/mGBA {mode}")
    evidence, report = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(EVIDENCE, expected)
        _atomic_write(REPORT, report)
    else:
        if _read(EVIDENCE) != expected or _read(REPORT) != report:
            _fail("Stage39 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, MoveDistributionV4CleanRebuildError) as error:
        print(f"Move Distribution V4 clean rebuild {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "Move Distribution V4 clean rebuild %s: PASS stage39=%s processes=2"
        % (args.mode, evidence["input_output"]["stage39_sha256"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
