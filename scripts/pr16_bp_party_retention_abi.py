#!/usr/bin/env python3
"""PR16: exchange-party retention target callsite/ABI audit.

This is a read-only static target audit.  It rebuilds the already-bound
candidate, resolves the exact CFRU linked object from the pinned state archive,
and proves that the final candidate still contains the specific player-party
random-rebuild call in ``BuildTrainerPartySetup``.  It does not connect the
retention wrapper, run an emulator, or claim native retention/BP acceptance.
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
from typing import Any, Mapping, NoReturn
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import pr16_bp_exchange_successor as parent  # noqa: E402

OUT = ROOT / ".local/pr16-bp-retention-abi-run"
STATE_ARCHIVE = (
    ROOT
    / ".local/pr16-bp-trial-native-inputs"
    / "pokemon-vega-private-env-v1-state.zip"
)
STATE_ARCHIVE_NAME = STATE_ARCHIVE.name
BATTLE_METADATA = "build/stages/06_battle_core.json"
SOURCE_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
SOURCE_BLOB_SHA1 = "99f58ab79046546230e5ce6fc769dcfb7d5a0e29"
CANDIDATE_SHA256 = "7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd"
CANDIDATE_SIZE = 33_554_432
ROM_BASE = 0x08000000
EXPECTED_BUILD_SETUP_ADDRESS = 0x090DD2A4
TARGET_PREDICATE_ORDINAL = 0
EXPECTED_PREDICATE_CALLS = 2
EXPECTED_FRONTIER_CALLS = 7
SOURCE_PATHS = {
    "builder": "vendor/upstream/CFRU-JP/src/build_pokemon.c",
    "predicate": "vendor/upstream/CFRU-JP/src/frontier.c",
    "header": "vendor/upstream/CFRU-JP/include/new/frontier.h",
}
SYMBOL_NAMES = (
    "BuildTrainerPartySetup",
    "IsRandomBattleTowerBattle",
    "BuildFrontierParty",
)
STATUS = "PASS_TARGET_CALLSITE_ABI_NOT_RUNTIME_CONNECTION_NOT_NATIVE_ACCEPTANCE"


class AbiAuditError(ValueError):
    """Pinned source, linked symbol, or final-candidate callsite differs."""


def fail(message: str) -> NoReturn:
    raise AbiAuditError(message)


def need(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def identity(raw: bytes) -> dict[str, int | str]:
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def _extract_function(text: str, signature_pattern: str, label: str) -> str:
    matches = list(re.finditer(signature_pattern, text, re.MULTILINE))
    need(len(matches) == 1, f"{label} signature missing/ambiguous")
    brace = text.find("{", matches[0].end())
    need(brace >= 0, f"{label} body opening brace missing")
    depth = 0
    for index in range(brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[matches[0].start() : index + 1]
    fail(f"{label} body is unterminated")


def source_contract(sources: Mapping[str, str]) -> dict[str, Any]:
    try:
        builder = sources[SOURCE_PATHS["builder"]]
        predicate = sources[SOURCE_PATHS["predicate"]]
        header = sources[SOURCE_PATHS["header"]]
    except KeyError as error:
        fail(f"required source missing: {error.args[0]}")

    function = _extract_function(
        builder,
        r"^void\s+BuildTrainerPartySetup\s*\(\s*void\s*\)\s*$",
        "BuildTrainerPartySetup",
    )
    predicate_calls = list(
        re.finditer(r"\bIsRandomBattleTowerBattle\s*\(\s*\)", function)
    )
    frontier_calls = list(re.finditer(r"\bBuildFrontierParty\s*\(", function))
    need(
        len(predicate_calls) == EXPECTED_PREDICATE_CALLS,
        "source predicate call count differs",
    )
    need(
        len(frontier_calls) == EXPECTED_FRONTIER_CALLS,
        "source BuildFrontierParty call count differs",
    )

    target = predicate_calls[TARGET_PREDICATE_ORDINAL]
    next_predicate = predicate_calls[TARGET_PREDICATE_ORDINAL + 1]
    between = function[target.end() : next_predicate.start()]
    expected_player_call = re.compile(
        r"BuildFrontierParty\s*\(\s*gPlayerParty\s*,\s*0\s*,\s*"
        r"towerTier\s*,\s*TRUE\s*,\s*TRUE\s*\+\s*1\s*,\s*"
        r"B_SIDE_PLAYER\s*\)\s*;",
        re.MULTILINE,
    )
    player_matches = list(expected_player_call.finditer(between))
    need(
        len(player_matches) == 1,
        "source player random-rebuild target missing/ambiguous",
    )
    need(
        len(re.findall(r"\bBuildFrontierParty\s*\(", between)) == 1,
        "source target interval contains another frontier build",
    )
    guard_prefix = function[max(0, target.start() - 16) : target.start()]
    need(re.search(r"\bif\s*\(\s*$", guard_prefix), "target predicate is not direct if guard")

    definitions = list(
        re.finditer(
            r"^bool8\s+IsRandomBattleTowerBattle\s*\(\s*\)\s*$",
            predicate,
            re.MULTILINE,
        )
    )
    declarations = list(
        re.finditer(
            r"^bool8\s+IsRandomBattleTowerBattle\s*\(\s*\)\s*;\s*$",
            header,
            re.MULTILINE,
        )
    )
    need(len(definitions) == 1, "predicate definition ABI differs")
    need(len(declarations) == 1, "predicate declaration ABI differs")

    return {
        "builder_signature": "void BuildTrainerPartySetup(void)",
        "predicate_definition": "bool8 IsRandomBattleTowerBattle()",
        "predicate_declaration": "bool8 IsRandomBattleTowerBattle();",
        "predicate_argument_count": 0,
        "predicate_return_abi": "bool8/u8 in r0",
        "predicate_call_count": len(predicate_calls),
        "frontier_call_count": len(frontier_calls),
        "target_predicate_ordinal_zero_based": TARGET_PREDICATE_ORDINAL,
        "target_player_call": (
            "BuildFrontierParty(gPlayerParty, 0, towerTier, TRUE, "
            "TRUE + 1, B_SIDE_PLAYER)"
        ),
        "second_predicate_role": "multi-partner fallback",
    }


def parse_nm_symbols(text: str) -> dict[str, dict[str, int | str]]:
    wanted: dict[str, list[dict[str, int | str]]] = {name: [] for name in SYMBOL_NAMES}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 4 or fields[3] not in wanted:
            continue
        try:
            address = int(fields[0], 16)
            size = int(fields[1], 16)
        except ValueError:
            fail(f"invalid nm row: {line}")
        wanted[fields[3]].append(
            {"address": address, "size": size, "type": fields[2]}
        )
    result: dict[str, dict[str, int | str]] = {}
    for name, rows in wanted.items():
        need(len(rows) == 1, f"linked symbol missing/ambiguous: {name}")
        row = rows[0]
        need(row["type"] in {"t", "T"}, f"linked symbol is not text: {name}")
        need(int(row["size"]) > 0, f"linked symbol is unbounded: {name}")
        need(int(row["address"]) % 2 == 0, f"linked symbol is not aligned: {name}")
        result[name] = row
    return result


def decode_thumb_bl(address: int, raw: bytes) -> int:
    need(len(raw) == 4, "Thumb BL requires four bytes")
    first, second = struct.unpack("<HH", raw)
    need(first & 0xF800 == 0xF000, "Thumb BL first halfword differs")
    need(second & 0xF800 == 0xF800, "Thumb BL second halfword differs")
    displacement = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return address + 4 + displacement


def _branch_calls(
    rom: bytes, start: int, size: int, target: int
) -> list[dict[str, int | str]]:
    offset = start - ROM_BASE
    need(0 <= offset and offset + size <= len(rom), "function outside candidate ROM")
    calls: list[dict[str, int | str]] = []
    function = rom[offset : offset + size]
    for relative in range(0, max(0, len(function) - 3), 2):
        chunk = function[relative : relative + 4]
        first, second = struct.unpack("<HH", chunk)
        if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
            continue
        address = start + relative
        if decode_thumb_bl(address, chunk) == target:
            calls.append({"address": address, "bytes": chunk.hex(), "target": target})
    return calls


def target_callsite_contract(
    rom: bytes, symbols: Mapping[str, Mapping[str, int | str]]
) -> dict[str, Any]:
    build = symbols["BuildTrainerPartySetup"]
    predicate = symbols["IsRandomBattleTowerBattle"]
    frontier = symbols["BuildFrontierParty"]
    build_address = int(build["address"])
    build_size = int(build["size"])
    predicate_address = int(predicate["address"])
    frontier_address = int(frontier["address"])

    need(
        build_address == EXPECTED_BUILD_SETUP_ADDRESS,
        "BuildTrainerPartySetup moved from accepted wrapper hook ABI",
    )
    predicate_calls = _branch_calls(
        rom, build_address, build_size, predicate_address
    )
    frontier_calls = _branch_calls(rom, build_address, build_size, frontier_address)
    need(
        len(predicate_calls) == EXPECTED_PREDICATE_CALLS,
        "candidate predicate call count differs",
    )
    need(
        len(frontier_calls) == EXPECTED_FRONTIER_CALLS,
        "candidate BuildFrontierParty call count differs",
    )
    target = predicate_calls[TARGET_PREDICATE_ORDINAL]
    next_predicate = predicate_calls[TARGET_PREDICATE_ORDINAL + 1]
    guarded_frontier = [
        row
        for row in frontier_calls
        if int(target["address"]) < int(row["address"]) < int(next_predicate["address"])
    ]
    need(
        len(guarded_frontier) == 1,
        "compiled target interval does not contain exactly one frontier build",
    )
    player_call = guarded_frontier[0]
    need(
        int(player_call["address"]) > int(target["address"]),
        "compiled player build does not follow predicate",
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
        },
        "frontier_symbol": {
            "address": frontier_address,
            "size": int(frontier["size"]),
            "entry_thumb": frontier_address | 1,
        },
        "predicate_calls": predicate_calls,
        "frontier_call_count": len(frontier_calls),
        "target_predicate_callsite": target,
        "target_player_build_callsite": player_call,
        "next_predicate_callsite": next_predicate,
        "target_predicate_ordinal_zero_based": TARGET_PREDICATE_ORDINAL,
        "candidate_branch_targets_verified": True,
    }


def _run_nm(linked_object: Path) -> str:
    result = subprocess.run(
        [
            "arm-none-eabi-nm",
            "-S",
            "--defined-only",
            str(linked_object),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        check=False,
    )
    need(result.returncode == 0, "linked-object nm failed")
    need(not result.stderr.strip(), "linked-object nm produced stderr")
    return result.stdout


def _state_binding() -> tuple[bytes, dict[str, Any]]:
    cfg = json.loads((ROOT / "config/github_private_environment.json").read_bytes())
    matches = [
        row for row in cfg["archives"] if row.get("name") == STATE_ARCHIVE_NAME
    ]
    need(len(matches) == 1, "state archive binding missing/ambiguous")
    raw = STATE_ARCHIVE.read_bytes()
    expected = matches[0]
    need(
        identity(raw)
        == {"size": expected["size"], "sha256": expected["sha256"]},
        "state archive identity differs",
    )
    return raw, expected


def _linked_object_contract(
    archive_raw: bytes,
) -> tuple[list[bytes], dict[str, Any], dict[str, str]]:
    with tempfile.TemporaryDirectory(prefix="pr16-retention-abi-archive-") as raw_dir:
        archive_path = Path(raw_dir) / STATE_ARCHIVE_NAME
        archive_path.write_bytes(archive_raw)
        with zipfile.ZipFile(archive_path) as archive:
            need(BATTLE_METADATA in archive.namelist(), "battle-core metadata missing")
            metadata_raw = archive.read(BATTLE_METADATA)
            metadata = json.loads(metadata_raw)
            fingerprint = metadata.get("fingerprint")
            need(
                isinstance(fingerprint, str)
                and re.fullmatch(r"[0-9a-f]{64}", fingerprint) is not None,
                "battle-core fingerprint differs",
            )
            runs = metadata.get("upstream_runs")
            need(isinstance(runs, list) and len(runs) == 2, "battle-core runs differ")
            linked_rows: list[dict[str, Any]] = []
            linked_bytes: list[bytes] = []
            for index, run in enumerate(runs, start=1):
                need(isinstance(run, dict), "battle-core run row differs")
                member = f"build/battle-core/{fingerprint}/run-{index}/linked.o"
                need(member in archive.namelist(), f"linked object missing: run {index}")
                raw = archive.read(member)
                published = run.get("linked_object")
                need(
                    isinstance(published, dict)
                    and identity(raw)
                    == {
                        "size": published.get("size"),
                        "sha256": published.get("sha256"),
                    },
                    f"linked object identity differs: run {index}",
                )
                linked_bytes.append(raw)
                linked_rows.append(
                    {"run": index, "member": member, **identity(raw)}
                )

            sources: dict[str, str] = {}
            source_identities: dict[str, dict[str, int | str]] = {}
            for path in SOURCE_PATHS.values():
                need(path in archive.namelist(), f"pinned source missing: {path}")
                raw = archive.read(path)
                sources[path] = raw.decode("utf-8")
                source_identities[path] = identity(raw)
            builder_raw = sources[SOURCE_PATHS["builder"]].encode("utf-8")
            need(
                git_blob_sha1(builder_raw) == SOURCE_BLOB_SHA1,
                "pinned build_pokemon.c blob differs",
            )

        return linked_bytes, {
            "metadata_member": BATTLE_METADATA,
            "metadata": identity(metadata_raw),
            "fingerprint": fingerprint,
            "source_commit": SOURCE_COMMIT,
            "linked_objects": linked_rows,
            "linked_objects_byte_identical": linked_bytes[0] == linked_bytes[1],
            "source_identities": source_identities,
        }, sources


def run() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    archive_raw, archive_binding = _state_binding()
    linked_raws, linked_report, sources = _linked_object_contract(archive_raw)
    source_report = source_contract(sources)

    recipe = parent.run()
    rom = (parent.OUT / "candidate.gba").read_bytes()
    need(
        identity(rom)
        == {"size": CANDIDATE_SIZE, "sha256": CANDIDATE_SHA256},
        "candidate identity differs",
    )
    need(
        recipe.get("candidate") == identity(rom),
        "successor recipe/candidate identity differs",
    )

    linked_symbol_runs: list[dict[str, dict[str, int | str]]] = []
    with tempfile.TemporaryDirectory(prefix="pr16-retention-abi-linked-") as raw_dir:
        for index, linked_raw in enumerate(linked_raws, start=1):
            linked_path = Path(raw_dir) / f"linked-{index}.o"
            linked_path.write_bytes(linked_raw)
            linked_symbol_runs.append(parse_nm_symbols(_run_nm(linked_path)))
    need(
        linked_symbol_runs[0] == linked_symbol_runs[1],
        "two linked-object target symbol contracts differ",
    )
    symbols = linked_symbol_runs[0]
    linked_report["target_symbol_runs"] = linked_symbol_runs
    target = target_callsite_contract(rom, symbols)

    report = {
        "schema_version": 1,
        "status": STATUS,
        "task": "USER-20260914-BP-RETENTION-ABI",
        "candidate": identity(rom),
        "candidate_changed": False,
        "state_archive": {
            "name": STATE_ARCHIVE_NAME,
            "size": archive_binding["size"],
            "sha256": archive_binding["sha256"],
        },
        "linked": linked_report,
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
        "next_step": (
            "Connect the existing retention wrapper only at the verified player "
            "predicate callsite, then run repaired native retention verification."
        ),
    }
    (OUT / "abi.json").write_bytes(stable(report))
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate": report["candidate"],
                "predicate_callsite": hex(
                    int(report["target"]["target_predicate_callsite"]["address"])
                ),
                "player_build_callsite": hex(
                    int(report["target"]["target_player_build_callsite"]["address"])
                ),
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
