#!/usr/bin/env python3
"""PR16 target callsite/ABI audit from hash-bound T06 build-cache evidence.

The final candidate and the two cached linked objects are authoritative.  This
script intentionally accepts compiler-local ``BuildFrontierParty`` variants
(e.g. ``.isra``/``.constprop``), while keeping the externally used predicate
ABI exact.  It never starts an emulator and never claims runtime retention
acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
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
FRONTIER_NAME = re.compile(r"^BuildFrontierParty(?:[.$].*)?$")


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


def parse_linked_symbols(text: str) -> dict[str, Any]:
    exact: dict[str, list[dict[str, int | str]]] = {
        "BuildTrainerPartySetup": [],
        "IsRandomBattleTowerBattle": [],
    }
    frontier: list[dict[str, int | str]] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 4:
            continue
        name = fields[3]
        if name not in exact and FRONTIER_NAME.fullmatch(name) is None:
            continue
        try:
            address = int(fields[0], 16)
            size = int(fields[1], 16)
        except ValueError:
            fail(f"invalid nm row: {line}")
        row: dict[str, int | str] = {
            "name": name,
            "address": address,
            "size": size,
            "type": fields[2],
        }
        need(row["type"] in {"t", "T"}, f"linked symbol is not text: {name}")
        need(size > 0 and address % 2 == 0, f"linked symbol bound/alignment differs: {name}")
        if name in exact:
            exact[name].append(row)
        else:
            frontier.append(row)
    result: dict[str, Any] = {}
    for name, rows in exact.items():
        need(len(rows) == 1, f"linked symbol missing/ambiguous: {name}")
        result[name] = rows[0]
    need(frontier, "linked static frontier variants missing")
    unique = {(int(row["address"]), int(row["size"]), str(row["name"])) for row in frontier}
    need(len(unique) == len(frontier), "linked static frontier variant duplicate")
    result["BuildFrontierParty_variants"] = sorted(
        frontier, key=lambda row: (int(row["address"]), str(row["name"]))
    )
    return result


def all_thumb_bl_calls(rom: bytes, start: int, size: int) -> list[dict[str, int | str]]:
    offset = start - base.ROM_BASE
    need(0 <= offset and offset + size <= len(rom), "function outside candidate ROM")
    function = rom[offset : offset + size]
    calls: list[dict[str, int | str]] = []
    for relative in range(0, max(0, len(function) - 3), 2):
        chunk = function[relative : relative + 4]
        first, second = struct.unpack("<HH", chunk)
        if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
            continue
        address = start + relative
        calls.append(
            {
                "address": address,
                "bytes": chunk.hex(),
                "target": base.decode_thumb_bl(address, chunk),
            }
        )
    return calls


def disassemble_function(rom: bytes, start: int, size: int) -> str:
    offset = start - base.ROM_BASE
    need(0 <= offset and offset + size <= len(rom), "function outside candidate ROM")
    with tempfile.TemporaryDirectory(prefix="pr16-retention-disasm-") as raw_dir:
        raw_path = Path(raw_dir) / "function.bin"
        raw_path.write_bytes(rom[offset : offset + size])
        result = subprocess.run(
            [
                "arm-none-eabi-objdump",
                "-D",
                "-b",
                "binary",
                "-marm",
                "-Mforce-thumb",
                f"--adjust-vma=0x{start:08x}",
                str(raw_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False,
        )
    need(result.returncode == 0, "candidate function objdump failed")
    need(not result.stderr.strip(), "candidate function objdump produced stderr")
    return result.stdout


def target_callsite_contract(
    rom: bytes, symbols: dict[str, Any]
) -> dict[str, Any]:
    build = symbols["BuildTrainerPartySetup"]
    predicate = symbols["IsRandomBattleTowerBattle"]
    build_address = int(build["address"])
    build_size = int(build["size"])
    predicate_address = int(predicate["address"])
    predicate_calls = base._branch_calls(
        rom, build_address, build_size, predicate_address
    )
    need(
        len(predicate_calls) == base.EXPECTED_PREDICATE_CALLS,
        "candidate predicate call count differs",
    )
    frontier_calls: list[dict[str, int | str]] = []
    for variant in symbols["BuildFrontierParty_variants"]:
        for row in base._branch_calls(
            rom, build_address, build_size, int(variant["address"])
        ):
            frontier_calls.append(
                {
                    **row,
                    "symbol": str(variant["name"]),
                    "symbol_size": int(variant["size"]),
                }
            )
    frontier_calls.sort(key=lambda row: int(row["address"]))
    need(
        len({int(row["address"]) for row in frontier_calls})
        == len(frontier_calls),
        "candidate frontier callsites overlap",
    )
    need(
        len(frontier_calls) == base.EXPECTED_FRONTIER_CALLS,
        "candidate BuildFrontierParty variant call count differs",
    )
    target = predicate_calls[base.TARGET_PREDICATE_ORDINAL]
    next_predicate = predicate_calls[base.TARGET_PREDICATE_ORDINAL + 1]
    guarded = [
        row
        for row in frontier_calls
        if int(target["address"]) < int(row["address"]) < int(next_predicate["address"])
    ]
    need(
        len(guarded) == 1,
        "compiled player target interval does not contain exactly one frontier call",
    )
    return {
        "build_function": {
            "address": build_address,
            "size": build_size,
            "entry_thumb": build_address | 1,
        },
        "predicate_symbol": {
            "address": predicate_address,
            "size": int(predicate["size"]),
            "entry_thumb": predicate_address | 1,
            "name": str(predicate["name"]),
        },
        "frontier_variants": symbols["BuildFrontierParty_variants"],
        "predicate_calls": predicate_calls,
        "frontier_calls": frontier_calls,
        "frontier_call_count": len(frontier_calls),
        "target_predicate_callsite": target,
        "target_player_build_callsite": guarded[0],
        "next_predicate_callsite": next_predicate,
        "target_predicate_ordinal_zero_based": base.TARGET_PREDICATE_ORDINAL,
        "candidate_branch_targets_verified": True,
    }


def source_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    sources: dict[str, str] = {}
    identities: dict[str, dict[str, int | str]] = {}
    with zipfile.ZipFile(base.STATE_ARCHIVE) as archive:
        for path in base.SOURCE_PATHS.values():
            need(path in archive.namelist(), f"pinned source missing: {path}")
            raw = archive.read(path)
            sources[path] = raw.decode("utf-8")
            identities[path] = base.identity(raw)
    builder_raw = sources[base.SOURCE_PATHS["builder"]].encode("utf-8")
    need(
        base.git_blob_sha1(builder_raw) == base.SOURCE_BLOB_SHA1,
        "pinned build_pokemon.c blob differs",
    )
    return base.source_contract(sources), identities


def select_cache(rom: bytes) -> dict[str, Any]:
    accepted: dict[str, list[dict[str, Any]]] = {}
    diagnostics: list[dict[str, Any]] = []
    with zipfile.ZipFile(CACHE) as archive, tempfile.TemporaryDirectory(
        prefix="pr16-retention-cache-"
    ) as raw_dir:
        complete = discover(archive.namelist())
        for fingerprint, runs in sorted(complete.items()):
            row: dict[str, Any] = {"fingerprint": fingerprint, "runs": []}
            try:
                linked: list[bytes] = []
                outcomes: list[dict[str, Any]] = []
                symbol_runs: list[dict[str, Any]] = []
                for run in (1, 2):
                    outcome = json.loads(archive.read(runs[run]["outcome.json"]))
                    need(
                        isinstance(outcome, dict) and outcome.get("run") == run,
                        f"cache run differs: run {run}",
                    )
                    raw = archive.read(runs[run]["linked.o"])
                    published = outcome.get("linked_object")
                    need(
                        isinstance(published, dict)
                        and base.identity(raw)
                        == {
                            "size": published.get("size"),
                            "sha256": published.get("sha256"),
                        },
                        f"linked object identity differs: run {run}",
                    )
                    path = Path(raw_dir) / f"{fingerprint}-{run}.o"
                    path.write_bytes(raw)
                    nm_text = base._run_nm(path)
                    symbol_lines = [
                        line
                        for line in nm_text.splitlines()
                        if "BuildTrainerPartySetup" in line
                        or "IsRandomBattleTowerBattle" in line
                        or "BuildFrontierParty" in line
                    ]
                    run_row = {
                        "run": run,
                        "linked_object": base.identity(raw),
                        "outcome_keys": sorted(outcome),
                        "symbol_lines": symbol_lines,
                    }
                    row["runs"].append(run_row)
                    symbols = parse_linked_symbols(nm_text)
                    linked.append(raw)
                    outcomes.append(outcome)
                    symbol_runs.append(symbols)
                need(symbol_runs[0] == symbol_runs[1], "linked symbol runs differ")
                build = symbol_runs[0]["BuildTrainerPartySetup"]
                build_address = int(build["address"])
                build_size = int(build["size"])
                row["candidate_all_bl_calls"] = all_thumb_bl_calls(
                    rom, build_address, build_size
                )
                row["candidate_disassembly"] = disassemble_function(
                    rom, build_address, build_size
                )
                target = target_callsite_contract(rom, symbol_runs[0])
                identity_key = json.dumps(
                    {
                        "linked_objects": [base.identity(raw) for raw in linked],
                        "symbols": symbol_runs[0],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                item = {
                    "fingerprint": fingerprint,
                    "linked": linked,
                    "outcomes": outcomes,
                    "symbol_runs": symbol_runs,
                    "target": target,
                }
                accepted.setdefault(identity_key, []).append(item)
                row.update(
                    status="ACCEPTED_FINAL_CANDIDATE_CALLSITE",
                    symbols=symbol_runs[0],
                    target=target,
                )
            except (
                CacheAuditError,
                base.AbiAuditError,
                KeyError,
                json.JSONDecodeError,
            ) as error:
                row["status"] = "REJECTED"
                row["reason"] = str(error)[:1000]
            diagnostics.append(row)
    inventory = {
        "schema_version": 3,
        "cache": {"name": CACHE_NAME, **file_identity(CACHE)},
        "candidate": base.identity(rom),
        "complete_fingerprint_count": len(diagnostics),
        "accepted_identity_count": len(accepted),
        "fingerprints": diagnostics,
    }
    base.OUT.mkdir(parents=True, exist_ok=True)
    inventory_path = base.OUT / "cache-discovery.json"
    inventory_path.write_bytes(base.stable(inventory))
    need(
        len(accepted) == 1,
        "accepted linked cache identity missing/ambiguous: "
        f"accepted={len(accepted)} complete={len(diagnostics)}; "
        "see cache-discovery.json",
    )
    aliases = next(iter(accepted.values()))
    aliases.sort(key=lambda item: str(item["fingerprint"]))
    chosen = aliases[0]
    need(
        all(
            item["linked"] == chosen["linked"]
            and item["symbol_runs"] == chosen["symbol_runs"]
            for item in aliases
        ),
        "accepted cache aliases differ",
    )
    return {
        "fingerprint": chosen["fingerprint"],
        "fingerprint_aliases": [item["fingerprint"] for item in aliases],
        "linked_objects": [base.identity(raw) for raw in chosen["linked"]],
        "linked_objects_byte_identical": chosen["linked"][0]
        == chosen["linked"][1],
        "outcome_linked_objects": [
            row["linked_object"] for row in chosen["outcomes"]
        ],
        "target_symbol_runs": chosen["symbol_runs"],
        "target": chosen["target"],
        "inventory": base.identity(inventory_path.read_bytes()),
    }


def run() -> dict[str, Any]:
    state_binding = binding(base.STATE_ARCHIVE, base.STATE_ARCHIVE_NAME)
    cache_binding = binding(CACHE, CACHE_NAME)
    recipe = base.parent.run()
    rom = (base.parent.OUT / "candidate.gba").read_bytes()
    need(
        base.identity(rom)
        == {"size": base.CANDIDATE_SIZE, "sha256": base.CANDIDATE_SHA256},
        "candidate identity differs",
    )
    need(recipe.get("candidate") == base.identity(rom), "candidate recipe differs")
    source_report, source_identities = source_contract()
    selected = select_cache(rom)
    symbols = selected["target_symbol_runs"][0]
    target = selected["target"]
    report = {
        "schema_version": 3,
        "status": base.STATUS,
        "task": "USER-20260914-BP-RETENTION-ABI",
        "candidate": base.identity(rom),
        "candidate_changed": False,
        "state_archive": {
            "name": base.STATE_ARCHIVE_NAME,
            "size": state_binding["size"],
            "sha256": state_binding["sha256"],
        },
        "build_cache": {
            "binding": {
                "name": CACHE_NAME,
                "size": cache_binding["size"],
                "sha256": cache_binding["sha256"],
            },
            "selection": selected,
        },
        "source_commit": base.SOURCE_COMMIT,
        "source_build_pokemon_blob_sha1": base.SOURCE_BLOB_SHA1,
        "source_identities": source_identities,
        "source_contract": source_report,
        "symbols": symbols,
        "target": target,
        "target_callsite_verified": True,
        "target_abi_verified": True,
        "runtime_connected": False,
        "native_retention_verified": False,
        "native_bp_earning_accepted": False,
        "new_emulator_processes": 0,
        "accepted_native_cases_replayed": 0,
        "release_ready": False,
        "audit_implementation": "HASH_BOUND_STATIC_VARIANT_FINAL_CANDIDATE_SELECTION",
        "next_step": (
            "Connect the existing retention wrapper only at the verified player "
            "predicate callsite, then run repaired native retention verification."
        ),
    }
    (base.OUT / "abi.json").write_bytes(base.stable(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "fingerprint": selected["fingerprint"],
                "fingerprint_aliases": selected["fingerprint_aliases"],
                "build_address": hex(
                    int(symbols["BuildTrainerPartySetup"]["address"])
                ),
                "predicate_callsite": hex(
                    int(target["target_predicate_callsite"]["address"])
                ),
                "player_build_callsite": hex(
                    int(target["target_player_build_callsite"]["address"])
                ),
                "frontier_variant": target["target_player_build_callsite"][
                    "symbol"
                ],
                "target_callsite_verified": True,
                "target_abi_verified": True,
                "runtime_connected": False,
                "new_emulator_processes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return report


if __name__ == "__main__":
    run()
