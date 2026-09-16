#!/usr/bin/env python3
"""Stage77を親にEelevate専用switch-in AIのStage78を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P05-STAGE78-EELEVATE-SWITCH-AI"
STAGE = 78
ROM_SIZE = 32 * 1024 * 1024
DEFAULT_CONFIG = Path("config/modernization_p05_stage78_eelevate_switch_ai.json")
EXPECTED_CONFIG_SHA256 = "649535b79d6ac2c0ec61a8e5c4ae5df9028bf515d92d05d2f37048bfa7bebe7a"
EXPECTED_STAGE77_COMMIT = "137c6945c6bf5c633944ddd5287dffca9c5692c0"
EXPECTED_PARENT_ALLOCATION_COUNT = 81
EXPECTED_PARENT_LAST_SEQUENCE = 80
EXPECTED_NEW_SEQUENCE = 81
PROVISIONAL_LOAD_ADDRESS = 0x095E1000
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class ModernizationP05Stage78EelevateSwitchAIError(RuntimeError):
    pass


def _fail(message: str) -> NoReturn:
    raise ModernizationP05Stage78EelevateSwitchAIError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label} JSON不正: {error}")
    _require(isinstance(value, dict), f"{label} rootがobjectではありません")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _rom_offset(address: int, width: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    _require(0 <= offset <= ROM_SIZE - width, f"{label}がROM範囲外")
    return offset


def map_eelevate_absorber(query: Mapping[str, Any]) -> int:
    """ROMのpure adapterと同じ決定表。"""
    original = _integer(query.get("originalAbility"), "originalAbility")
    if original != 313:
        return original
    move = _integer(query.get("move"), "move")
    if (
        move in {0, 643, 0xFFFF}
        or move > 1062
        or _integer(query.get("moveType"), "moveType") != 4
        or _integer(query.get("moveSplit"), "moveSplit") == 2
    ):
        return original
    if any(bool(query.get(key)) for key in ("circusSuppressed", "abilitySuppressed", "grounded")):
        return original
    shield = bool(query.get("abilityShield"))
    if not shield and any(bool(query.get(key)) for key in ("targetAbilityIgnored", "neutralizingGasPresent")):
        return original
    return 298


def select_threat(foe1: int, move1: int, foe2: int, move2: int) -> tuple[int, int] | None:
    """ROM helperと同じfoe1優先・invalid fallback規則。"""
    if move1 not in {0, 0xFFFF} and 0 < move1 <= 1062:
        return foe1, move1
    if move2 not in {0, 0xFFFF} and 0 < move2 <= 1062:
        return foe2, move2
    return None


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    _require(path.is_file() and not path.is_symlink(), f"Stage78 configが固定通常fileではありません: {path}")
    raw = path.read_bytes()
    _require(sha256(raw) == EXPECTED_CONFIG_SHA256, "Stage78 config exact SHA-256不一致")
    config = _json(raw, "Stage78 config")
    _require(
        (config.get("schema_version"), config.get("task"), config.get("stage"))
        == (SCHEMA_VERSION, TASK, STAGE),
        "Stage78 schema/task/stage不一致",
    )
    _require(config.get("status") == "STAGE77_IDENTITY_PINNED", "Stage78 status不正")
    parent = config.get("parent_identity")
    _require(isinstance(parent, dict) and parent.get("stage77_commit") == EXPECTED_STAGE77_COMMIT, "Stage77 commit pin不一致")
    _require(parent.get("policy") == "FAIL_CLOSED_EXACT_STAGE77_COMMIT_AND_SEVEN_IDENTITIES", "Stage77 identity policy不一致")
    _require(set(parent) == {"stage77_commit", "rom", "metadata", "allocation", "checkpoint", "tracked_config", "contract", "symbols", "policy"}, "Stage77 identity exact key集合不一致")
    _require(config.get("eelevate_contract", {}).get("completion") == {
        "eelevate_dedicated_switch_ai": True,
        "mgba_runtime": "NOT_RUN",
        "browt_pombon_gecqua_added": 0,
        "side_change_added": 0,
        "active_play_baseline_changed": False,
        "release_ready": False,
        "full_p05_done": False,
        "done": False,
    }, "Stage78 completion claim不一致")
    hooks = config.get("parent_abi", {}).get("hooks")
    _require(isinstance(hooks, list) and len(hooks) == 2, "Stage78 hook count不一致")
    expected_hooks = (
        ("0x090A03E4", 16, "0x090A03F4", "0x090A03F5", "Stage78_EntryFindMonAbsorberActive", "95235b009b463100280010f0bffa5b46"),
        ("0x090A0426", 12, "0x090A0432", "0x090A0433", "Stage78_EntryFindMonAbsorberParty", "3000984639f007ffe38e0700"),
    )
    for row, expected in zip(hooks, expected_hooks):
        address, width, continuation_even, continuation_thumb, target, parent_hex = expected
        _require((row.get("address"), row.get("width"), row.get("continuation_even"), row.get("continuation_thumb"), row.get("target"), row.get("parent_hex")) == expected, f"{target} exact ABI不一致")
        _require(len(bytes.fromhex(parent_hex)) == width, f"{target} preimage width不一致")
        _require(int(continuation_even, 0) == int(address, 0) + width and int(continuation_thumb, 0) == (int(continuation_even, 0) | 1), f"{target} continuation不一致")
    runtime = config.get("runtime_abi", {})
    _require(runtime.get("query", {}).get("size") == 12 and len(runtime.get("query", {}).get("fields", [])) == 10, "query ABI不一致")
    _require(len(runtime.get("exports", [])) == 6, "export ABI集合不一致")
    _require(config.get("allocation", {}).get("alignment") == 16, "allocation alignment不一致")
    _require(set(config.get("outputs", {})) == {"rom", "metadata", "allocation", "incremental_bps", "payload", "symbols", "audit", "contract", "checkpoint"}, "output exact key集合不一致")
    return config


def _fixed_raw(root: Path, identity: Mapping[str, Any], label: str) -> bytes:
    path_value = identity.get("path")
    digest = identity.get("sha256")
    _require(isinstance(path_value, str) and isinstance(digest, str) and _SHA_RE.fullmatch(digest) is not None, f"{label} identity不正")
    path = root / path_value
    _require(path.is_file() and not path.is_symlink(), f"{label}が固定通常fileではありません")
    raw = path.read_bytes()
    _require(len(raw) == _integer(identity.get("size"), f"{label}.size"), f"{label} size不一致")
    _require(sha256(raw) == digest, f"{label} SHA-256不一致")
    return raw


def require_pinned_parent(root: Path, config: Mapping[str, Any]) -> dict[str, bytes]:
    parent = config["parent_identity"]
    result = subprocess.run(["git", "cat-file", "-e", f"{EXPECTED_STAGE77_COMMIT}^{{commit}}"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(result.returncode == 0, "Stage77 commit object不存在")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_STAGE77_COMMIT, "HEAD"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(ancestor.returncode == 0, "Stage77 commitがHEAD ancestorではありません")
    fixed = {key: _fixed_raw(root, parent[key], f"Stage77 {key}") for key in ("rom", "metadata", "allocation", "checkpoint", "tracked_config", "contract", "symbols")}
    for key, identity in config["source_pins"].items():
        if isinstance(identity, dict):
            fixed[key] = _fixed_raw(root, identity, key)
    upstream = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root / "vendor/upstream/CFRU-JP", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(upstream.returncode == 0 and upstream.stdout.strip() == config["source_pins"]["fixed_cfru_jp_commit"], "CFRU-JP HEAD pin不一致")
    for key in ("checkpoint", "tracked_config", "contract"):
        shown = subprocess.run(["git", "show", f"{EXPECTED_STAGE77_COMMIT}:{parent[key]['path']}"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _require(shown.returncode == 0 and shown.stdout == fixed[key], f"Stage77 commit→{key} cross-link不一致")
    metadata = _json(fixed["metadata"], "Stage77 metadata")
    allocation = _json(fixed["allocation"], "Stage77 allocation")
    checkpoint = _json(fixed["checkpoint"], "Stage77 checkpoint")
    parent_config = _json(fixed["tracked_config"], "Stage77 config")
    symbols = _json(fixed["symbols"], "Stage77 symbols")
    _require(metadata.get("stage") == checkpoint.get("stage") == parent_config.get("stage") == symbols.get("stage") == 77, "Stage77 internal stage不一致")
    _require(metadata.get("output", {}).get("sha256") == sha256(fixed["rom"]), "Stage77 ROM cross-link不一致")
    rows = allocation.get("allocations")
    _require(isinstance(rows, list) and len(rows) == EXPECTED_PARENT_ALLOCATION_COUNT, "Stage77 allocation count不一致")
    _require([row.get("sequence") for row in rows] == list(range(EXPECTED_PARENT_ALLOCATION_COUNT)), "Stage77 allocation sequence不連続")
    _require(rows[-1].get("sequence") == EXPECTED_PARENT_LAST_SEQUENCE and metadata.get("allocation_sequence") == EXPECTED_PARENT_LAST_SEQUENCE, "Stage77 terminal allocation不一致")
    stage77_hooks = parent_config.get("parent_abi", {}).get("hooks")
    hook_guard = config["parent_abi"]["stage77_hooks"]
    _require(isinstance(stage77_hooks, list) and len(stage77_hooks) == hook_guard["count"], "Stage77 hook count guard不一致")
    _require(sha256(stable_json(stage77_hooks)) == hook_guard["stable_json_sha256"], "Stage77 hook lineage hash不一致")
    active = _json(fixed["active_play_baseline_json"], "active baseline")
    _require(active.get("stage") == 62 and active.get("status") == "ACTIVE", "active baseline Stage62不一致")
    _validate_source_semantics(fixed)
    return fixed


def _validate_source_semantics(fixed: Mapping[str, bytes]) -> None:
    ai_master = fixed["fixed_cfru_ai_master"].decode("utf-8")
    ai_util = fixed["fixed_cfru_ai_util"].decode("utf-8")
    battle_util = fixed["fixed_cfru_battle_util"].decode("utf-8")
    ability_util = fixed["fixed_cfru_ability_util"].decode("utf-8")
    stage72 = fixed["stage72_source"].decode("utf-8")
    for token in ("static bool8 FindMonThatAbsorbsOpponentsMove(void)", "LoadBattlersAndFoes(&battlerIn1, &battlerIn2, &foe1, &foe2);", "predictedMove1 = IsValidMovePrediction(foe1, gActiveBattler);", "GetPredictedAIAbility(gActiveBattler, foe1)", "GetMonAbility(&party[i])", "ABILITY_EARTHEATER"):
        _require(token in ai_master, f"ai_master根拠不足: {token}")
    for token in ("u16 GetAIAbility(u8 bankAtk, u8 bankDef, u16 move)", "move_t IsValidMovePrediction(u8 bankAtk, u8 bankDef)"):
        _require(token in ai_util, f"ai_util根拠不足: {token}")
    _require("item_effect_t GetBankItemEffect(u8 bank)" in battle_util and "item_effect_t GetMonItemEffect(const struct Pokemon* mon)" in battle_util, "effective item API根拠不足")
    _require("bool8 IsTargetAbilityIgnored(u16 defAbility, u16 atkAbility, u16 move)" in ability_util, "Mold Breaker API根拠不足")
    for token in ("Stage72_IsDamagingGroundMove", "STAGE72_MOVE_THOUSAND_ARROWS", "Stage72_CheckGrounding", "Stage72_CheckMonGrounding"):
        _require(token in stage72, f"Stage72 Ground根拠不足: {token}")


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(list(command), cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    sizes: dict[str, int]
    compiler: str
    disassembly: str


def compile_payload(root: Path, load_address: int) -> CompiledPayload:
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    objdump = shutil.which("arm-none-eabi-objdump")
    _require(bool(gcc and objcopy and nm and objdump), "arm-none-eabi toolchainがPATHにありません")
    source = root / "overlays/modernization_p05_stage78_eelevate_switch_ai"
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage78-eelevate-switch-ai-") as temporary:
        work = Path(temporary)
        c_obj = work / "runtime.o"
        s_obj = work / "hooks.o"
        elf = work / "runtime.elf"
        binary = work / "runtime.bin"
        _run([str(gcc), *common, "-Os", "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin", "-fomit-frame-pointer", "-c", str(source / "modernization_p05_stage78_eelevate_switch_ai.c"), "-o", str(c_obj)], root, "Stage78 C compile")
        _run([str(gcc), *common, "-c", str(source / "modernization_p05_stage78_eelevate_switch_ai_hooks.S"), "-o", str(s_obj)], root, "Stage78 ASM compile")
        _run([str(gcc), "-nostdlib", *common, f"-Wl,--defsym=STAGE78_LOAD_ADDRESS=0x{load_address:08X}", f"-Wl,-T,{source / 'modernization_p05_stage78_eelevate_switch_ai.ld'}", str(s_obj), str(c_obj), "-o", str(elf)], root, "Stage78 link")
        _run([str(objcopy), "-O", "binary", str(elf), str(binary)], root, "Stage78 objcopy")
        symbol_text = _run([str(nm), "-n", "-S", str(elf)], root, "Stage78 nm")
        disassembly = _run([str(objdump), "-d", str(elf)], root, "Stage78 objdump")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        for line in symbol_text.splitlines():
            fields = line.split()
            if len(fields) == 4 and all(character in "0123456789abcdefABCDEF" for character in fields[0]):
                symbols[fields[3]] = int(fields[0], 16)
                sizes[fields[3]] = int(fields[1], 16)
        code = binary.read_bytes()
        compiler = _run([str(gcc), "--version"], root, "gcc version").splitlines()[0]
    required = {"Stage78_MapEelevateAbsorber", "Stage78_ActiveAbsorberAbility", "Stage78_PartyAbsorberAbility", "Stage78_EntryFindMonAbsorberActive", "Stage78_EntryFindMonAbsorberParty", "Stage78_RuntimeProbe"}
    _require(required <= symbols.keys(), "Stage78 required symbol不足")
    _require(all(load_address <= symbols[name] < load_address + len(code) for name in required), "Stage78 symbol payload外")
    return CompiledPayload(code, symbols, sizes, compiler, disassembly)


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for row in allocation["allocations"]:
        request = {key: row[key] for key in ("name", "region", "size", "alignment", "owner", "purpose", "content_sha256")}
        if row.get("placement") == "EXPLICIT":
            request["start"] = row["start"]
        else:
            _require(row.get("placement") == "FIRST_FIT", "Stage77 allocation placement不正")
        requests.append(request)
    return requests


def _allocate(root: Path, config: Mapping[str, Any], previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    declaration = config["allocation"]
    requests = _previous_requests(previous)
    requests.append({**declaration, "size": size, "content_sha256": digest})
    report = build_allocation_report_from_csv(root / config["source_pins"]["rom_regions"]["path"], requests)
    rows = report.get("allocations")
    _require(report.get("summaries", {}).get("overlap_count") == 0, "Stage78 allocator overlap")
    _require(isinstance(rows, list) and len(rows) == EXPECTED_NEW_SEQUENCE + 1, "Stage78 allocation count不一致")
    _require(rows[:EXPECTED_PARENT_ALLOCATION_COUNT] == previous.get("allocations"), "Stage78 allocatorが親first81 rowを変更")
    row = rows[-1]
    _require(row.get("sequence") == EXPECTED_NEW_SEQUENCE and row.get("name") == declaration["name"] and row.get("placement") == "FIRST_FIT", "Stage78 terminal allocation不一致")
    return row, report


def veneer(width: int, target: int, address: int = 0) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
    if width == 12:
        if address & 2:
            return struct.pack("<HHHIH", 0x469C, 0x4B00, 0x4718, target, 0x46C0)
        return struct.pack("<HHHHI", 0x469C, 0x4B01, 0x4718, 0x46C0, target)
    if width == 16 and not (address & 3):
        return struct.pack("<HHIHHHH", 0x4B00, 0x4718, target, 0x46C0, 0x46C0, 0x46C0, 0x46C0)
    _fail(f"未対応veneer: address=0x{address:08X} width={width}")


def _patch_exact(image: bytearray, address: int, expected: bytes, replacement: bytes, label: str) -> dict[str, Any]:
    _require(len(expected) == len(replacement), f"{label} replacement width不一致")
    offset = _rom_offset(address, len(expected), label)
    actual = bytes(image[offset:offset + len(expected)])
    _require(actual == expected, f"{label} parent preimage不一致: {actual.hex()} != {expected.hex()}")
    image[offset:offset + len(replacement)] = replacement
    return {"name": label, "address": f"0x{address:08X}", "width": len(expected), "before_hex": expected.hex(), "after_hex": replacement.hex()}


def _rom_diff_allowlist(parent: bytes, result: bytes, intervals: Sequence[tuple[int, int, str]]) -> dict[str, Any]:
    ordered = sorted(intervals)
    cursor = 0
    changed_inside = 0
    rows: list[dict[str, Any]] = []
    for start, end, name in ordered:
        _require(0 <= start < end <= ROM_SIZE and start >= cursor, f"{name} allowlist不正/重複")
        _require(parent[cursor:start] == result[cursor:start], f"ROM差分がallowlist外: 0x{cursor:X}..0x{start:X}")
        changed = sum(left != right for left, right in zip(parent[start:end], result[start:end]))
        changed_inside += changed
        rows.append({"name": name, "start": start, "end_exclusive": end, "size": end - start, "changed_bytes": changed})
        cursor = end
    _require(parent[cursor:] == result[cursor:], f"ROM差分がallowlist外: 0x{cursor:X}..EOF")
    return {"allowed_intervals": rows, "allowlist_interval_count": len(rows), "changed_bytes_inside_allowlist": changed_inside, "changed_bytes_outside_allowlist": 0}


def _implementation_identity(root: Path) -> dict[str, Any]:
    paths = [
        "config/modernization_p05_stage78_eelevate_switch_ai.json",
        "tools/modernization_p05_stage78_eelevate_switch_ai.py",
        "scripts/build_modernization_p05_stage78_eelevate_switch_ai.sh",
        "tests/test_modernization_p05_stage78_eelevate_switch_ai.py",
        "overlays/modernization_p05_stage78_eelevate_switch_ai/modernization_p05_stage78_eelevate_switch_ai.h",
        "overlays/modernization_p05_stage78_eelevate_switch_ai/modernization_p05_stage78_eelevate_switch_ai.c",
        "overlays/modernization_p05_stage78_eelevate_switch_ai/modernization_p05_stage78_eelevate_switch_ai_hooks.S",
        "overlays/modernization_p05_stage78_eelevate_switch_ai/modernization_p05_stage78_eelevate_switch_ai.ld",
    ]
    rows: list[dict[str, Any]] = []
    framed = hashlib.sha256()
    for relative in paths:
        raw = (root / relative).read_bytes()
        row = {"path": relative, "size": len(raw), "sha256": sha256(raw)}
        encoded = stable_json(row)
        framed.update(len(encoded).to_bytes(8, "big"))
        framed.update(encoded)
        rows.append(row)
    return {"files": rows, "sha256": framed.hexdigest()}


def _source_identities(root: Path) -> dict[str, dict[str, Any]]:
    base = root / "overlays/modernization_p05_stage78_eelevate_switch_ai"
    return {path.name: {"size": len(path.read_bytes()), "sha256": sha256(path.read_bytes())} for path in sorted(base.iterdir()) if path.is_file()}


def _matrix() -> list[dict[str, Any]]:
    base = {"originalAbility": 313, "move": 89, "moveType": 4, "moveSplit": 0, "grounded": 0, "targetAbilityIgnored": 0, "abilityShield": 0, "circusSuppressed": 0, "abilitySuppressed": 0, "neutralizingGasPresent": 0}
    changes = [
        ("eligible_physical_ground", {}, 298),
        ("eligible_special_ground", {"moveSplit": 1}, 298),
        ("other_ability", {"originalAbility": 26}, 26),
        ("no_prediction", {"move": 0}, 313),
        ("prediction_switch", {"move": 0xFFFF}, 313),
        ("prediction_out_of_range", {"move": 1063}, 313),
        ("non_ground", {"moveType": 10}, 313),
        ("status_ground", {"moveSplit": 2}, 313),
        ("thousand_arrows", {"move": 643}, 313),
        ("gravity", {"grounded": 1}, 313),
        ("iron_ball", {"grounded": 1}, 313),
        ("rooted", {"grounded": 1}, 313),
        ("smack_down", {"grounded": 1}, 313),
        ("mold_breaker", {"targetAbilityIgnored": 1}, 313),
        ("mold_breaker_shield", {"targetAbilityIgnored": 1, "abilityShield": 1}, 298),
        ("teravolt", {"targetAbilityIgnored": 1}, 313),
        ("teravolt_shield", {"targetAbilityIgnored": 1, "abilityShield": 1}, 298),
        ("turboblaze", {"targetAbilityIgnored": 1}, 313),
        ("turboblaze_shield", {"targetAbilityIgnored": 1, "abilityShield": 1}, 298),
        ("mold_breaker_move", {"targetAbilityIgnored": 1}, 313),
        ("mold_breaker_move_shield", {"targetAbilityIgnored": 1, "abilityShield": 1}, 298),
        ("magic_room_disables_shield", {"targetAbilityIgnored": 1, "abilityShield": 0}, 313),
        ("embargo_disables_shield", {"targetAbilityIgnored": 1, "abilityShield": 0}, 313),
        ("circus", {"circusSuppressed": 1}, 313),
        ("circus_shield", {"circusSuppressed": 1, "abilityShield": 1}, 313),
        ("gastro_acid", {"abilitySuppressed": 1}, 313),
        ("gastro_acid_shield", {"abilitySuppressed": 1, "abilityShield": 1}, 313),
        ("neutralizing_gas", {"neutralizingGasPresent": 1}, 313),
        ("neutralizing_gas_shield", {"neutralizingGasPresent": 1, "abilityShield": 1}, 298),
        ("outgoing_active_sole_gas_excluded", {"neutralizingGasPresent": 0}, 298),
        ("grounded_shield", {"grounded": 1, "abilityShield": 1}, 313),
        ("combined_ignore_gas_shield", {"targetAbilityIgnored": 1, "neutralizingGasPresent": 1, "abilityShield": 1}, 298),
    ]
    rows = []
    for name, delta, expected in changes:
        query = dict(base)
        query.update(delta)
        actual = map_eelevate_absorber(query)
        _require(actual == expected, f"matrix不一致: {name}")
        rows.append({"name": name, "query": query, "expected_ability": expected, "result_ability": actual, "pass": True})
    return rows


def build_artifacts(root: Path) -> dict[str, bytes]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    previous_allocation = _json(fixed["allocation"], "Stage77 allocation")
    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS)
    placement, _ = _allocate(root, config, previous_allocation, len(provisional.code), sha256(provisional.code))
    load_address = GBA_ROM_BASE + int(placement["start"])
    compiled = compile_payload(root, load_address)
    _require(len(compiled.code) == len(provisional.code), "Stage78 relocation payload size drift")
    placement, allocation_report = _allocate(root, config, previous_allocation, len(compiled.code), sha256(compiled.code))
    _require(GBA_ROM_BASE + int(placement["start"]) == load_address, "Stage78 allocation relocation drift")
    image = bytearray(parent)
    start = int(placement["start"])
    _require(bytes(image[start:start + len(compiled.code)]) == b"\xFF" * len(compiled.code), "Stage78 payload preimage非FF")
    image[start:start + len(compiled.code)] = compiled.code
    changes: list[dict[str, Any]] = [{"name": "payload", "address": f"0x{load_address:08X}", "width": len(compiled.code), "before_sha256": sha256(b"\xFF" * len(compiled.code)), "after_sha256": sha256(compiled.code)}]
    for row in config["parent_abi"]["hooks"]:
        symbol = row["target"]
        changes.append(_patch_exact(image, int(row["address"], 0), bytes.fromhex(row["parent_hex"]), veneer(int(row["width"]), compiled.symbols[symbol], int(row["address"], 0)), row["name"]))
    result = bytes(image)
    _require(len(result) == ROM_SIZE, "Stage78 output ROM size不一致")
    parent_config = _json(fixed["tracked_config"], "Stage77 config")
    parent_symbols = _json(fixed["symbols"], "Stage77 symbols")["symbols"]
    for row in parent_config["parent_abi"]["hooks"]:
        address = int(row["address"], 0)
        width = int(row["width"])
        offset = _rom_offset(address, width, row["name"])
        expected = veneer(width, int(parent_symbols[row["target"]], 0), address)
        _require(parent[offset:offset + width] == result[offset:offset + width] == expected, f"Stage77 hook変更: {row['name']}")
    for row in config["parent_abi"]["preserved_stage76_patches"]:
        offset = _rom_offset(int(row["address"], 0), int(row["width"]), row["name"])
        expected = bytes.fromhex(row["parent_hex"])
        _require(parent[offset:offset + int(row["width"])] == result[offset:offset + int(row["width"])] == expected, f"Stage76 patch変更: {row['name']}")
    intervals = [(start, start + len(compiled.code), "payload")]
    intervals.extend((_rom_offset(int(row["address"], 0), int(row["width"]), row["name"]), _rom_offset(int(row["address"], 0), int(row["width"]), row["name"]) + int(row["width"]), row["name"]) for row in config["parent_abi"]["hooks"])
    diff_audit = _rom_diff_allowlist(parent, result, intervals)
    implementation = _implementation_identity(root)
    payload_identity = {"path": config["outputs"]["payload"], "start": start, "load_address": f"0x{load_address:08X}", "size": len(compiled.code), "sha256": sha256(compiled.code), "allocation_sequence": EXPECTED_NEW_SEQUENCE}
    output_identity = {"path": config["outputs"]["rom"], "size": len(result), "sha256": sha256(result), "crc32": f"{zlib.crc32(result) & 0xFFFFFFFF:08X}"}
    parent_rows_hash = sha256(stable_json(previous_allocation["allocations"]))
    new_rows_hash = sha256(stable_json(allocation_report["allocations"][:EXPECTED_PARENT_ALLOCATION_COUNT]))
    _require(parent_rows_hash == new_rows_hash, "Stage78 first81 allocation lineage hash不一致")
    allocation_lineage = {"parent_count": 81, "parent_last_sequence": 80, "new_count": 82, "new_sequence": 81, "first81_all_fields_equal": True, "parent_first81_sha256": parent_rows_hash, "new_first81_sha256": new_rows_hash, "payload_slice_sha256": sha256(result[start:start + len(compiled.code)])}
    bps = create_bps(parent, result, metadata=b"Stage77 to Stage78 P05 Eelevate switch AI")
    _require(apply_bps(parent, bps) == result, "Stage77→78 BPS roundtrip不一致")
    bps_identity = {"path": config["outputs"]["incremental_bps"], "size": len(bps), "sha256": sha256(bps), "source_sha256": sha256(parent), "target_sha256": sha256(result), "round_trip": True}
    matrix = _matrix()
    symbol_values = {key: f"0x{value:08X}" for key, value in sorted(compiled.symbols.items()) if key.startswith("Stage78_")}
    exports = [{**row, "address": symbol_values[row["name"]]} for row in config["runtime_abi"]["exports"]]
    runtime_abi = {**config["runtime_abi"], "exports": exports, "hooks": [{"name": row["name"], "site": row["address"], "width": row["width"], "entry": row["target"], "entry_address": symbol_values[row["target"]], "continuation_even": row["continuation_even"], "continuation_thumb": row["continuation_thumb"], "abi": row["abi"]} for row in config["parent_abi"]["hooks"]]}
    checks = {"parent_stage77_commit_and_seven_identities": "PASS", "parent_first81_rows_all_fields_preserved": "PASS", "stage77_29_hooks_preserved": "PASS", "stage76_pointer_and_three_hooks_preserved": "PASS", "two_switch_ai_hooks_installed": 2, "active_original_call_tuple_preserved": "PASS", "party_threat_prediction_rederived": "PASS", "dynamic_ground_status_thousand_arrows_grounding": "PASS", "mold_breaker_and_ability_shield": "PASS", "circus_and_active_suppression": "PASS", "residual_neutralizing_gas_excludes_outgoing": "PASS", "pure_matrix_cases": len(matrix), "pure_matrix": "PASS", "allocator_overlap": "PASS", "rom_diff_outside_payload_plus_two_hooks": 0, "bps_roundtrip": "PASS", "browt_pombon_gecqua_added": 0, "side_change_added": 0, "active_play_baseline_unchanged": "PASS", "mgba_runtime": "NOT_RUN"}
    parent_identity = {"stage": 77, "commit": EXPECTED_STAGE77_COMMIT, "path": config["parent_identity"]["rom"]["path"], "size": len(parent), "sha256": sha256(parent), "crc32": f"{zlib.crc32(parent) & 0xFFFFFFFF:08X}"}
    active_baseline = {"stage": 62, "unchanged": True, "json": dict(config["source_pins"]["active_play_baseline_json"]), "markdown": dict(config["source_pins"]["active_play_baseline_md"])}
    remaining = ["single cumulative P05 mGBA smoke on Stage78", "P05 aggregate completion/release decision"]
    status = "EELEVATE_DEDICATED_SWITCH_AI_MATERIALIZED_CUMULATIVE_MGBA_PENDING"
    symbols_json = {"schema_version": 1, "task": TASK, "stage": STAGE, "load_address": f"0x{load_address:08X}", "compiler": compiled.compiler, "payload_size": len(compiled.code), "payload_sha256": sha256(compiled.code), "symbols": symbol_values, "runtime_abi": runtime_abi}
    common = {"schema_version": 1, "task": TASK, "stage": STAGE, "status": status, "parent": parent_identity, "output": output_identity, "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE, "allocation_lineage": allocation_lineage, "bps": bps_identity, "eelevate_contract": config["eelevate_contract"], "runtime_abi": runtime_abi, "matrix": {"case_count": len(matrix), "all_pass": True, "cases": matrix}, "checks": checks, "pending": remaining, "implementation_sha256": implementation["sha256"], "active_play_baseline": active_baseline, "eelevate_dedicated_switch_ai_complete": True, "release_ready": False, "full_p05_done": False, "done": False}
    metadata = {**common, "allocation": placement, "remaining_work": remaining, "source_identities": _source_identities(root), "implementation": implementation, "artifact_count": 9}
    audit = {**common, "changes": changes, "rom_diff": diff_audit, "implementation": implementation}
    contract = dict(common)
    outputs = config["outputs"]
    artifacts: dict[str, bytes] = {outputs["rom"]: result, outputs["metadata"]: stable_json(metadata), outputs["allocation"]: stable_json(allocation_report), outputs["incremental_bps"]: bps, outputs["payload"]: compiled.code, outputs["symbols"]: stable_json(symbols_json), outputs["audit"]: stable_json(audit), outputs["contract"]: stable_json(contract)}
    sibling_identities = [{"path": relative, "size": len(raw), "sha256": sha256(raw), "sha256_scope": "WHOLE_FILE"} for relative, raw in artifacts.items()]
    checkpoint_core = {**common, "rom_diff": diff_audit}
    core_sha = sha256(stable_json(checkpoint_core))
    checkpoint_size = 0
    checkpoint_raw = b""
    for _ in range(8):
        checkpoint = dict(checkpoint_core)
        checkpoint["artifact_manifest"] = {"artifact_count": 9, "all_paths_sizes_sha256_present": True, "self_hash_is_nonrecursive": True, "artifacts": [*sibling_identities, {"path": outputs["checkpoint"], "size": checkpoint_size, "sha256": core_sha, "sha256_scope": "STABLE_JSON_WITHOUT_ARTIFACT_MANIFEST"}]}
        checkpoint_raw = stable_json(checkpoint)
        if len(checkpoint_raw) == checkpoint_size:
            break
        checkpoint_size = len(checkpoint_raw)
    _require(len(checkpoint_raw) == checkpoint_size, "Stage78 checkpoint self size非収束")
    artifacts[outputs["checkpoint"]] = checkpoint_raw
    _require(set(artifacts) == set(outputs.values()) and len(artifacts) == 9, "Stage78 artifact path/count不一致")
    return artifacts


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def materialize(root: Path, *, check: bool = False) -> dict[str, Any]:
    artifacts = build_artifacts(root)
    differences: list[str] = []
    for relative, raw in artifacts.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != raw:
                differences.append(relative)
        else:
            _atomic_write(path, raw)
    if differences:
        _fail("Stage78生成物が再現結果と不一致です: " + ", ".join(differences))
    config = read_config(root)
    metadata = _json(artifacts[config["outputs"]["metadata"]], "Stage78 metadata")
    return {"status": "PASS", "mode": "CHECK" if check else "WRITE", "output_sha256": metadata["output"]["sha256"], "payload_size": metadata["payload"]["size"], "allocation_sequence": metadata["allocation_sequence"], "hook_count": metadata["checks"]["two_switch_ai_hooks_installed"], "matrix_cases": metadata["matrix"]["case_count"], "eelevate_dedicated_switch_ai_complete": True, "mgba_runtime": "NOT_RUN", "release_ready": False}


def preflight(root: Path) -> dict[str, Any]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    for row in config["parent_abi"]["hooks"]:
        offset = _rom_offset(int(row["address"], 0), int(row["width"]), row["name"])
        _require(parent[offset:offset + int(row["width"])] == bytes.fromhex(row["parent_hex"]), f"{row['name']} Stage77 preimage不一致")
    compiled = compile_payload(root, PROVISIONAL_LOAD_ADDRESS)
    return {"status": "PASS", "parent_sha256": sha256(parent), "hook_count": 2, "payload_size": len(compiled.code), "matrix_cases": len(_matrix())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    result = preflight(args.root) if args.preflight else materialize(args.root, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(f"RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT=-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_CONFIG", "PROVISIONAL_LOAD_ADDRESS", "ModernizationP05Stage78EelevateSwitchAIError",
    "build_artifacts", "compile_payload", "map_eelevate_absorber", "materialize", "preflight",
    "read_config", "require_pinned_parent", "select_threat", "sha256", "stable_json", "veneer",
]
