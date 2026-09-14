#!/usr/bin/env python3
"""PR16 target ABI audit using the hash-bound T06 build-cache archive.

This is a source/binary audit only.  It reuses the existing candidate builder,
does not start an emulator, and does not claim runtime retention acceptance.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, NoReturn
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import pr16_bp_party_retention_abi as base  # noqa: E402

CACHE = (
    ROOT
    / ".local/pr16-bp-trial-native-inputs"
    / "pokemon-vega-private-env-v1-build-cache.zip"
)
CACHE_NAME = CACHE.name
MEMBER = re.compile(
    r"^build/battle-core/([0-9a-f]{64})/run-([12])/(linked\.o|outcome\.json)$"
)


class CacheAuditError(ValueError):
    pass


def fail(message: str) -> NoReturn:
    raise CacheAuditError(message)


def need(value: bool, message: str) -> None:
    if not value:
        fail(message)


def file_identity(path: Path) -> dict[str, int | str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return {"size": size, "sha256": digest.hexdigest()}


def binding(path: Path, name: str) -> dict[str, Any]:
    cfg = json.loads((ROOT / "config/github_private_environment.json").read_bytes())
    rows = [row for row in cfg["archives"] if row.get("name") == name]
    need(len(rows) == 1, f"archive binding missing/ambiguous: {name}")
    need(path.is_file() and not path.is_symlink(), f"archive missing/nonregular: {name}")
    expected = rows[0]
    need(
        file_identity(path)
        == {"size": expected["size"], "sha256": expected["sha256"]},
        f"archive identity differs: {name}",
    )
    return expected


def discover(names: list[str]) -> dict[str, dict[int, dict[str, str]]]:
    groups: dict[str, dict[int, dict[str, str]]] = {}
    seen: set[tuple[str, int, str]] = set()
    for name in names:
        match = MEMBER.fullmatch(name)
        if match is None:
            continue
        fingerprint, raw_run, filename = match.groups()
        run = int(raw_run)
        key = (fingerprint, run, filename)
        need(key not in seen, f"duplicate cache member: {name}")
        seen.add(key)
        groups.setdefault(fingerprint, {}).setdefault(run, {})[filename] = name
    complete = {
        fingerprint: runs
        for fingerprint, runs in groups.items()
        if set(runs) == {1, 2}
        and all(set(runs[run]) == {"linked.o", "outcome.json"} for run in (1, 2))
    }
    need(bool(complete), "complete battle-core linked cache missing")
    return complete


def composite() -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    state_binding = binding(base.STATE_ARCHIVE, base.STATE_ARCHIVE_NAME)
    cache_binding = binding(CACHE, CACHE_NAME)
    candidates: list[tuple[str, list[bytes], list[dict[str, Any]], list[dict[str, Any]]]] = []
    rejected: list[dict[str, str]] = []
    with zipfile.ZipFile(CACHE) as archive, tempfile.TemporaryDirectory(
        prefix="pr16-retention-cache-"
    ) as raw_dir:
        for fingerprint, runs in sorted(discover(archive.namelist()).items()):
            try:
                linked: list[bytes] = []
                outcomes: list[dict[str, Any]] = []
                symbols: list[dict[str, Any]] = []
                for run in (1, 2):
                    outcome_raw = archive.read(runs[run]["outcome.json"])
                    outcome = json.loads(outcome_raw)
                    need(isinstance(outcome, dict) and outcome.get("run") == run, "cache run differs")
                    raw = archive.read(runs[run]["linked.o"])
                    published = outcome.get("linked_object")
                    need(
                        isinstance(published, dict)
                        and base.identity(raw)
                        == {"size": published.get("size"), "sha256": published.get("sha256")},
                        f"linked object identity differs: run {run}",
                    )
                    path = Path(raw_dir) / f"{fingerprint}-{run}.o"
                    path.write_bytes(raw)
                    parsed = base.parse_nm_symbols(base._run_nm(path))
                    linked.append(raw)
                    outcomes.append(outcome)
                    symbols.append(parsed)
                need(symbols[0] == symbols[1], "linked symbol runs differ")
                need(
                    int(symbols[0]["BuildTrainerPartySetup"]["address"])
                    == base.EXPECTED_BUILD_SETUP_ADDRESS,
                    "BuildTrainerPartySetup address differs",
                )
                candidates.append((fingerprint, linked, outcomes, symbols))
            except (CacheAuditError, base.AbiAuditError, KeyError, json.JSONDecodeError) as error:
                rejected.append({"fingerprint": fingerprint, "reason": str(error)[:500]})
    need(len(candidates) == 1, "accepted linked cache missing/ambiguous")
    fingerprint, linked, outcomes, symbols = candidates[0]
    metadata = {
        "fingerprint": fingerprint,
        "upstream_runs": [
            {"linked_object": base.identity(linked[0])},
            {"linked_object": base.identity(linked[1])},
        ],
    }
    output = io.BytesIO()
    with zipfile.ZipFile(base.STATE_ARCHIVE) as state, zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_STORED
    ) as merged:
        for source in base.SOURCE_PATHS.values():
            merged.writestr(source, state.read(source))
        merged.writestr(base.BATTLE_METADATA, base.stable(metadata))
        for index, raw in enumerate(linked, start=1):
            merged.writestr(
                f"build/battle-core/{fingerprint}/run-{index}/linked.o", raw
            )
    report = {
        "cache": {"name": CACHE_NAME, **file_identity(CACHE)},
        "fingerprint": fingerprint,
        "linked_objects": [base.identity(raw) for raw in linked],
        "linked_objects_byte_identical": linked[0] == linked[1],
        "outcome_linked_objects": [row["linked_object"] for row in outcomes],
        "target_symbol_runs": symbols,
        "rejected_candidates": rejected,
    }
    return output.getvalue(), state_binding, {"binding": cache_binding, "selection": report}


def run() -> dict[str, Any]:
    merged, state_binding, cache_report = composite()
    original = base._state_binding
    base._state_binding = lambda: (merged, state_binding)
    try:
        report = base.run()
    finally:
        base._state_binding = original
    report["build_cache"] = cache_report
    report["audit_implementation"] = "HASH_BOUND_BUILD_CACHE_SUCCESSOR"
    report["accepted_native_cases_replayed"] = 0
    report["new_emulator_processes"] = 0
    report["runtime_connected"] = False
    report["native_retention_verified"] = False
    report["release_ready"] = False
    (base.OUT / "abi.json").write_bytes(base.stable(report))
    print(json.dumps({
        "status": report["status"],
        "fingerprint": cache_report["selection"]["fingerprint"],
        "target_callsite_verified": report["target_callsite_verified"],
        "target_abi_verified": report["target_abi_verified"],
        "runtime_connected": False,
        "new_emulator_processes": 0,
    }, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    run()
