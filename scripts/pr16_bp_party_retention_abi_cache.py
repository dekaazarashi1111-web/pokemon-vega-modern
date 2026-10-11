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
    unique = {
        (int(row["address"]), int(row["size"]), str(row["name"]))
        for row in frontier
    }
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


def _halfword(rom: bytes, address: int) -> int:
    offset = address - base.ROM_BASE
    need(address % 2 == 0, "Thumb instruction address is not aligned")
    need(0 <= offset and offset + 2 <= len(rom), "Thumb instruction outside candidate ROM")
    return struct.unpack_from("<H", rom, offset)[0]


def _decode_thumb_b16(address: int, instruction: int) -> int:
    if instruction & 0xF800 == 0xE000:
        displacement = instruction & 0x07FF
        if displacement & 0x0400:
            displacement -= 0x0800
        return address + 4 + (displacement << 1)
    if instruction & 0xF000 == 0xD000:
        condition = (instruction >> 8) & 0xF
        need(condition < 0xE, "Thumb conditional branch condition differs")
        displacement = instruction & 0x00FF
        if displacement & 0x0080:
            displacement -= 0x0100
        return address + 4 + (displacement << 1)
    fail("Thumb 16-bit branch opcode differs")


def _player_true_block_contract(
    rom: bytes,
    build_address: int,
    build_size: int,
    target: dict[str, int | str],
    frontier_variants: list[dict[str, int | str]],
) -> dict[str, Any]:
    """Resolve the source ``if (predicate())`` by its compiled basic blocks.

    GCC is free to place unrelated frontier-build blocks between the two
    predicate calls in linear address order.  The accepted candidate emits a
    BNE to the player-build block and an unconditional branch for the false
    path; both paths then rejoin.  Following those edges avoids treating code
    layout as source control flow.
    """

    build_end = build_address + build_size
    predicate_call = int(target["address"])
    search_end = min(predicate_call + 16, build_end)
    compares = [
        address
        for address in range(predicate_call + 4, search_end, 2)
        if _halfword(rom, address) == 0x2800  # cmp r0, #0
    ]
    need(
        len(compares) == 1,
        "target predicate r0 comparison missing/ambiguous",
    )
    compare_address = compares[0]
    branch_address = compare_address + 2
    branch = _halfword(rom, branch_address)
    need(
        branch & 0xFF00 == 0xD100,
        "target predicate true edge is not direct BNE",
    )
    false_branch_address = branch_address + 2
    false_branch = _halfword(rom, false_branch_address)
    need(
        false_branch & 0xF800 == 0xE000,
        "target predicate false edge is not direct unconditional branch",
    )
    true_block_start = _decode_thumb_b16(branch_address, branch)
    false_continuation = _decode_thumb_b16(false_branch_address, false_branch)
    need(
        build_address <= true_block_start < build_end,
        "target predicate true block outside build function",
    )
    need(
        build_address <= false_continuation < build_end,
        "target predicate false continuation outside build function",
    )

    variants_by_target: dict[int, list[dict[str, int | str]]] = {}
    for variant in frontier_variants:
        variants_by_target.setdefault(int(variant["address"]), []).append(variant)

    direct_calls: list[dict[str, int | str]] = []
    block_end_address: int | None = None
    block_exit_target: int | None = None
    address = true_block_start
    for _ in range(64):
        need(
            build_address <= address < build_end,
            "target predicate true block escaped build function",
        )
        first = _halfword(rom, address)
        if address + 4 <= build_end:
            second = _halfword(rom, address + 2)
            if first & 0xF800 == 0xF000 and second & 0xF800 == 0xF800:
                raw = struct.pack("<HH", first, second)
                call_target = base.decode_thumb_bl(address, raw)
                direct_calls.append(
                    {
                        "address": address,
                        "bytes": raw.hex(),
                        "target": call_target,
                    }
                )
                address += 4
                continue
        if first & 0xF800 == 0xE000:
            block_end_address = address
            block_exit_target = _decode_thumb_b16(address, first)
            break
        need(
            not (first & 0xF000 == 0xD000 and ((first >> 8) & 0xF) < 0xE),
            "target predicate true block contains nested conditional branch",
        )
        need(first & 0xFF87 != 0x4700, "target predicate true block returns via BX")
        need(first & 0xFF00 != 0xBD00, "target predicate true block returns via POP")
        address += 2
    need(block_end_address is not None, "target predicate true block has no direct exit")
    need(
        block_exit_target == false_continuation,
        "target predicate true/false paths do not rejoin",
    )
    need(
        len(direct_calls) == 1,
        "target predicate true block direct call count differs",
    )
    player_call = direct_calls[0]
    variants = variants_by_target.get(int(player_call["target"]), [])
    need(
        len(variants) == 1,
        "target predicate true block call is not one frontier variant",
    )
    variant = variants[0]
    player_call = {
        **player_call,
        "symbol": str(variant["name"]),
        "symbol_size": int(variant["size"]),
    }
    return {
        "compare_address": compare_address,
        "compare": "cmp r0, #0",
        "condition_branch_address": branch_address,
        "condition": "BNE/nonzero bool8",
        "true_block_start": true_block_start,
        "false_branch_address": false_branch_address,
        "false_continuation": false_continuation,
        "true_block_exit_address": block_end_address,
        "true_block_exit_target": block_exit_target,
        "paths_rejoin": True,
        "true_block_direct_call_count": len(direct_calls),
        "player_build_callsite": player_call,
    }


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
    guard = _player_true_block_contract(
        rom,
        build_address,
        build_size,
        target,
        symbols["BuildFrontierParty_variants"],
    )
    player_call = guard["player_build_callsite"]
    need(
        any(int(row["address"]) == int(player_call["address"]) for row in frontier_calls),
        "target player call missing from complete frontier call inventory",
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
        "target_predicate_guard": guard,
        "target_player_build_callsite": player_call,
        "next_predicate_callsite": next_predicate,
        "target_predicate_ordinal_zero_based": base.TARGET_PREDICATE_ORDINAL,
        "candidate_branch_targets_verified": True,
        "candidate_control_flow_verified": True,
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
        "schema_version": 4,
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
        "schema_version": 4,
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
        "audit_implementation": "HASH_BOUND_STATIC_CFG_FINAL_CANDIDATE_SELECTION",
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
