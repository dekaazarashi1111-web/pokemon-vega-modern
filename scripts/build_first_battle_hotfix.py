#!/usr/bin/env python3
"""stage 20へ初戦の不正な行動順indicator防御を決定的に適用する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import BpsError, apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402
from scripts.fast_stage_reuse import trusted_stage_sha  # noqa: E402

TASK = "USER-20260814-FIRST-BATTLE-LOOP"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE20 = Path("build/stages/20_facility_runtime.gba")
STAGE20_SHA256 = "d82f280c4d9c6ca6b5268c287c9534c0e556bc9ba2ad2075d027af6a7580d4cd"
STAGE20_META = Path("build/stages/20_facility_runtime.json")
STAGE20_ALLOCATION = Path("build/stages/20_allocation.json")
STAGE06_META = Path("build/stages/06_battle_core.json")
STAGE21 = Path("build/stages/21_first_battle_hotfix.gba")
STAGE21_META = Path("build/stages/21_first_battle_hotfix.json")
STAGE21_ALLOCATION = Path("build/stages/21_allocation.json")
MGBA_FIXTURE = Path("build/stages/21_mgba_first_battle_loop.json")
REPORT = Path("reports/generated/first_battle_loop_fix.md")
RUNNER = Path("tools/mgba_first_battle_loop_smoke.c")
RUNTIME_SOURCE = Path("overlays/first_battle_hotfix/first_battle_hotfix.c")
RUNTIME_HEADER = Path("overlays/first_battle_hotfix/first_battle_hotfix.h")
RUNTIME_BIN = Path("generated/runtime/first_battle_hotfix.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/first_battle_hotfix_symbols.json")
ALLOCATION_NAME = "first_battle_priority_guard"

ITEM_PATCH_ADDRESS = 0x090CEAFC
ITEM_PATCH_OFFSET = ITEM_PATCH_ADDRESS - GBA_ROM_BASE
EXPECTED = bytes.fromhex("60 28 04 d1 01 3c 24 06 24 0e 02 2c 2a d9")
REPLACEMENT = bytes.fromhex("1a 28 04 d0 60 28 c6 d1 01 3c 02 2c 2a d9")
SOURCE_GUARD_ADDRESS = 0x090CEAFC
SOURCE_GUARD_OFFSET = SOURCE_GUARD_ADDRESS - GBA_ROM_BASE
SOURCE_GUARD = bytes.fromhex(
    "02 00 1a 3a 51 1e 8a 41 01 00 60 39 4d 1e a9 41 11 42 bf d1"
)
RUN_TURN_PROLOGUE = bytes.fromhex("f0 b5 57 46 de 46 4e 46")
REQUIRED_RUNTIME_SYMBOLS = {
    "VegaFirstBattle_ClearInvalidQuickDrawIndicators",
    "VegaFirstBattle_RunTurnActionsFunctions",
}


class FirstBattleHotfixError(ValueError):
    """stage入力、命令契約、または実ROM回帰が不正。"""


def _fail(message: str) -> NoReturn:
    raise FirstBattleHotfixError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-4000:]}")
    return completed.stdout.strip()


def _allocation_contract(root: Path) -> dict[str, Any]:
    value = json.loads((root / STAGE20_ALLOCATION).read_bytes())
    if not isinstance(value, dict):
        _fail("stage20 allocation report must be an object")
    summaries = value.get("summaries")
    if not isinstance(summaries, dict) or summaries.get("overlap_count") != 0:
        _fail("stage20 allocator overlap contract failed")
    return value


def _allocation(root: Path, size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    previous = _allocation_contract(root)
    requests = [{
        "name": row["name"],
        "region": row["region"],
        "size": row["size"],
        "alignment": row["alignment"],
        "owner": row["owner"],
        "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in previous["allocations"]]
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 4,
        "owner": TASK,
        "purpose": "Quick Draw indicatorと実特性を照合するturn scheduler wrapper",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(
        row for row in report["allocations"] if row["name"] == ALLOCATION_NAME
    )
    return allocation, report


def _compile_runtime(
    root: Path, load_address: int, continuation_address: int
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("first-battle hotfix requires the ARM GNU toolchain")
    source = root / RUNTIME_SOURCE
    header = root / RUNTIME_HEADER
    if not source.is_file() or not header.is_file():
        _fail("first-battle runtime source is missing")

    with tempfile.TemporaryDirectory(prefix="vega-first-battle-runtime-") as raw:
        temporary = Path(raw)
        linker = temporary / "linker.ld"
        elf = temporary / "first_battle_hotfix.elf"
        binary = temporary / "first_battle_hotfix.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaFirstBattle_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            f"-DVEGA_FIRST_BATTLE_ORIGINAL_CONTINUE=0x{continuation_address:08X}",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaFirstBattle_RunTurnActionsFunctions",
            f"-Wl,-T,{linker}", f"-I{source.parent}", str(source),
            "-o", str(elf),
        ], "first-battle ARM runtime link", cwd=root)
        undefined = _run([nm, "-u", str(elf)], "first-battle undefined symbols")
        if undefined:
            _fail("first-battle runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "first-battle runtime objcopy")
        symbols: dict[str, int] = {}
        for line in _run(
            [nm, "-n", "--defined-only", str(elf)], "first-battle runtime nm"
        ).splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("VegaFirstBattle_"):
                symbols[fields[2]] = int(fields[0], 16)
        if set(symbols) != REQUIRED_RUNTIME_SYMBOLS:
            _fail(f"first-battle runtime symbol set differs: {sorted(symbols)}")
        runtime = binary.read_bytes()
        if not runtime or len(runtime) > 1024:
            _fail(f"first-battle runtime size differs: {len(runtime)}")
        return runtime, symbols


def _t06_symbol_addresses(root: Path) -> dict[str, int]:
    metadata = json.loads((root / STAGE06_META).read_text(encoding="utf-8"))
    fingerprint = metadata.get("fingerprint")
    runs = metadata.get("upstream_runs")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        _fail("T06 fingerprint is invalid")
    if not isinstance(runs, list) or len(runs) != 2:
        _fail("T06 repeatability contract is missing")
    required = ("RunTurnActionsFunctions", "GetBankItemEffect")
    resolved_runs: list[dict[str, int]] = []
    for index, run in enumerate(runs, 1):
        if not isinstance(run, dict) or not isinstance(run.get("offsets"), dict):
            _fail(f"T06 offsets contract is invalid: run {index}")
        path = root / "build/battle-core" / fingerprint / f"run-{index}/offsets.ini"
        raw = path.read_bytes()
        if _sha(raw) != run["offsets"].get("sha256"):
            _fail(f"T06 offsets digest differs: run {index}")
        symbols: dict[str, int] = {}
        for line in raw.decode("utf-8").splitlines():
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            if value.strip():
                symbols[name.strip()] = int(value.strip(), 16)
        if len(symbols) != run["offsets"].get("symbol_count"):
            _fail(f"T06 offsets symbol count differs: run {index}")
        resolved: dict[str, int] = {}
        for name in required:
            address = symbols.get(name)
            if address is None or address & 1:
                _fail(f"T06 symbol is missing/unaligned: {name} (run {index})")
            resolved[name] = address
        resolved_runs.append(resolved)
    if resolved_runs[0] != resolved_runs[1]:
        _fail("T06 first-battle symbols differ between repeatability runs")
    return resolved_runs[0]


def build_hotfix_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    source = (root / STAGE20).read_bytes()
    expected_stage20 = trusted_stage_sha(
        root, STAGE20, STAGE20_META, "USER-20260814-FACILITY-RUNTIME",
        STAGE20_SHA256,
    )
    if len(source) != ROM_SIZE or _sha(source) != expected_stage20:
        _fail("stage20 size/hash contract failed")
    actual = source[ITEM_PATCH_OFFSET:ITEM_PATCH_OFFSET + len(EXPECTED)]
    source_guard = source[
        SOURCE_GUARD_OFFSET:SOURCE_GUARD_OFFSET + len(SOURCE_GUARD)
    ]
    if actual == EXPECTED:
        integration_mode = "stage21_instruction_patch"
    elif source_guard == SOURCE_GUARD:
        integration_mode = "t06_source_integrated"
    else:
        _fail(
            "RunTurnActionsFunctions guard bytes drift: "
            f"legacy_expected={EXPECTED.hex()} source_expected={SOURCE_GUARD.hex()} "
            f"actual={source_guard.hex()}"
        )

    output = bytearray(source)
    if integration_mode == "stage21_instruction_patch":
        output[ITEM_PATCH_OFFSET:ITEM_PATCH_OFFSET + len(REPLACEMENT)] = REPLACEMENT
    legacy_changed = (
        [
            ITEM_PATCH_OFFSET + index
            for index, (before, after) in enumerate(zip(EXPECTED, REPLACEMENT))
            if before != after
        ]
        if integration_mode == "stage21_instruction_patch"
        else []
    )

    t06_symbols = _t06_symbol_addresses(root)
    t06_metadata = json.loads((root / STAGE06_META).read_text(encoding="utf-8"))
    base_stats = t06_metadata.get("runtime_tables", {}).get("base_stats", {})
    base_stats_address = base_stats.get("address")
    if not isinstance(base_stats_address, int):
        _fail("T06 BaseStats address is missing")
    actashi_row = base_stats_address - GBA_ROM_BASE + 7 * 32
    actashi_abilities = [
        int.from_bytes(source[actashi_row + 0x16:actashi_row + 0x18], "little"),
        int.from_bytes(source[actashi_row + 0x1A:actashi_row + 0x1C], "little"),
    ]
    if actashi_abilities != [67, 64]:
        _fail(f"Actashi primary/secondary ability contract differs: {actashi_abilities}")
    run_turn = t06_symbols["RunTurnActionsFunctions"]
    run_turn_offset = run_turn - GBA_ROM_BASE
    if source[run_turn_offset:run_turn_offset + len(RUN_TURN_PROLOGUE)] \
            != RUN_TURN_PROLOGUE:
        _fail("RunTurnActionsFunctions entry prologue drifted")

    provisional, _ = _allocation(root, 1024, "0" * 64)
    payload_offset = int(provisional["start"])
    runtime, runtime_symbols = _compile_runtime(
        root, GBA_ROM_BASE + payload_offset, (run_turn + 8) | 1,
    )
    allocation, allocation_report = _allocation(root, len(runtime), _sha(runtime))
    if int(allocation["start"]) != payload_offset:
        _fail("first-battle runtime allocation moved after final link")
    payload_end = int(allocation["end_exclusive"])
    if source[payload_offset:payload_end] != bytes([0xFF]) * len(runtime):
        _fail("first-battle runtime destination is not erased FF")
    output[payload_offset:payload_end] = runtime

    wrapper = runtime_symbols["VegaFirstBattle_RunTurnActionsFunctions"] | 1
    entry_stub = bytes.fromhex("00 4b 18 47") + struct.pack("<I", wrapper)
    output[run_turn_offset:run_turn_offset + len(entry_stub)] = entry_stub
    output_raw = bytes(output)

    allowed = set(range(payload_offset, payload_end))
    allowed.update(range(run_turn_offset, run_turn_offset + len(entry_stub)))
    allowed.update(legacy_changed)
    changed = {
        index for index, (before, after) in enumerate(zip(source, output_raw))
        if before != after
    }
    if not changed <= allowed:
        _fail("hotfix changed bytes outside the runtime/entry patch contract")
    if output_raw[run_turn_offset:run_turn_offset + 8] != entry_stub:
        _fail("RunTurnActionsFunctions wrapper hook differs")

    allocation_raw = _stable(allocation_report)
    runtime_symbol_payload = {
        "schema_version": 1,
        "task": TASK,
        "load_address": GBA_ROM_BASE + payload_offset,
        "symbols": {
            name: address | 1 for name, address in sorted(runtime_symbols.items())
        },
        "original": {
            "RunTurnActionsFunctions": run_turn | 1,
            "continuation": (run_turn + 8) | 1,
        },
    }
    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity mismatch")
    release_patch = create_bps(
        clean, output_raw,
        metadata=f"{TASK}:{_sha(output_raw)}".encode("ascii"),
    )
    if apply_bps(clean, release_patch) != output_raw:
        _fail("stage21 release BPS round-trip differs from exact ROM")
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": STAGE20.as_posix(),
            "size": len(source),
            "sha256": _sha(source),
        },
        "output": {
            "path": STAGE21.as_posix(),
            "size": len(output_raw),
            "sha256": _sha(output_raw),
        },
        "patch": {
            "item_guard_integration_mode": integration_mode,
            "function": "RunTurnActionsFunctions",
            "site_address": f"0x{run_turn:08X}",
            "site_offset": run_turn_offset,
            "span_size": len(entry_stub),
            "expected_hex": RUN_TURN_PROLOGUE.hex(),
            "replacement_hex": entry_stub.hex(),
            "changed_byte_count": len(changed),
            "wrapper_address": f"0x{wrapper:08X}",
            "source_guard_address": f"0x{SOURCE_GUARD_ADDRESS:08X}",
            "source_guard_hex": SOURCE_GUARD.hex(),
            "semantics": [
                "Quick Draw indicatorを各bankの実特性と照合",
                "ABILITY_QUICKDRAW以外のbankはindicatorを通知前に破棄",
                "正規Quick Drawと既存Quick Claw/Custap経路は維持",
            ],
        },
        "runtime": {
            "allocation_name": ALLOCATION_NAME,
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(runtime),
            "sha256": _sha(runtime),
            "symbols": runtime_symbol_payload["symbols"],
        },
        "actashi_ability_contract": {
            "species_id": 7,
            "primary": actashi_abilities[0],
            "secondary": actashi_abilities[1],
            "base_stats_address": base_stats_address,
        },
        "source_generation": {
            "path": "scripts/build_battle_core.py",
            "guards": [
                "invalid Quick Claw/Custap indicator guard",
            ],
            "quick_draw_owner": "stage21 runtime wrapper",
        },
        "allocation": {
            "input_path": STAGE20_ALLOCATION.as_posix(),
            "output_path": STAGE21_ALLOCATION.as_posix(),
            "new_allocation_count": 1,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "sha256": _sha(allocation_raw),
        },
        "release_patch_round_trip": {
            "format": "BPS1",
            "source_sha256": _sha(clean),
            "target_sha256": _sha(output_raw),
            "patch_size": len(release_patch),
            "patch_sha256": _sha(release_patch),
            "exact": True,
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "input_hash_pinned": _sha(source) == expected_stage20,
            "source_guard_or_patch_valid": integration_mode in {
                "stage21_instruction_patch", "t06_source_integrated"
            },
            "wrapper_hook_exact": output_raw[
                run_turn_offset:run_turn_offset + len(entry_stub)
            ] == entry_stub,
            "declared_changes_only": changed <= allowed,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("first-battle hotfix invariant failed")
    return {
        STAGE21.as_posix(): output_raw,
        STAGE21_META.as_posix(): _stable(metadata),
        STAGE21_ALLOCATION.as_posix(): allocation_raw,
        RUNTIME_BIN.as_posix(): runtime,
        RUNTIME_SYMBOLS.as_posix(): _stable(runtime_symbol_payload),
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vega-first-battle-hotfix-") as raw:
        temporary = Path(raw)
        rom = temporary / STAGE21.name
        executable = temporary / "mgba-first-battle-loop-smoke"
        rom.write_bytes(stage)
        compiler = os.environ.get("CC", "cc")
        _run(
            [
                compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                str(RUNNER), "-o", str(executable), "-lmgba",
            ],
            "first-battle libmGBA runner compile",
            cwd=root,
        )
        symbols = _t06_symbol_addresses(root)
        args = [
            executable.as_posix(), rom.as_posix(), metadata["output"]["sha256"],
            hex(symbols["RunTurnActionsFunctions"]),
            hex(symbols["GetBankItemEffect"]),
        ]
        first = json.loads(_run(args, "first-battle exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "first-battle exact-ROM run 2", cwd=root))
        if first != second or first.get("status") != "PASS":
            _fail("first-battle exact-ROM fixture is not deterministic PASS")
        branches = first.get("branches")
        natural = first.get("natural_actashi_route")
        faults = first.get("invalid_indicator_fault_injections")
        legitimate = first.get("legitimate_priority_effects")
        if not isinstance(branches, list) or len(branches) != 3:
            _fail("first-battle fixture did not cover all three starter branches")
        if (
            not isinstance(natural, dict)
            or not natural.get("selected_actashi")
            or not natural.get("trainer_327_started")
            or not natural.get("pointer_stable")
            or not natural.get("pending_shadow_stable")
            or natural.get("observation", {}).get("player_ability") != 67
            or natural.get("observation", {}).get("opponent_ability") != 65
            or natural.get("observation", {}).get("quick_claw_script_entries") != 0
            or natural.get("observation", {}).get("quick_draw_script_entries") != 0
            or natural.get("observation", {}).get("placeholder_item_entries") != 0
            or not natural.get("observation", {}).get("pp_spent_once")
            or not natural.get("observation", {}).get("hp_changed")
        ):
            _fail("natural Actashi first-battle route contract drifted")
        if not isinstance(faults, list) or len(faults) != 2:
            _fail("first-battle fixture did not cover both invalid indicators")
        expected_faults = {
            "QUICK_CLAW": (1, 65),
            "QUICK_DRAW_ACTASHI_ABILITY_64": (0, 64),
        }
        if {row.get("indicator") for row in faults} != set(expected_faults):
            _fail("first-battle invalid indicator set drifted")
        for row in faults:
            expected_bank, expected_ability = expected_faults[row["indicator"]]
            observation = row.get("observation", {})
            if (
                row.get("bank") != expected_bank
                or row.get("ability") != expected_ability
                or not observation.get("invalid_indicator_injected")
                or not observation.get("invalid_indicator_rejected")
                or observation.get("quick_claw_script_entries") != 0
                or observation.get("quick_draw_script_entries") != 0
                or observation.get("placeholder_item_entries") != 0
                or not observation.get("pp_spent_once")
                or not observation.get("hp_changed")
            ):
                _fail(f"invalid indicator guard failed: {row.get('indicator')}")
        if not isinstance(legitimate, list) or len(legitimate) != 3:
            _fail("first-battle fixture did not cover all priority effects")
        expected_effects = {"QUICK_CLAW", "CUSTAP_BERRY", "QUICK_DRAW"}
        if {row.get("effect") for row in legitimate} != expected_effects:
            _fail("first-battle priority effect coverage drifted")
        quick_draw = next(
            row for row in legitimate if row.get("effect") == "QUICK_DRAW"
        )
        if (
            not quick_draw.get("ability_name_valid")
            or quick_draw.get("popup_ability") != 260
        ):
            _fail("legitimate Quick Draw popup ability name is invalid")
        first["process_runs"] = 2
        first["rom_sha256"] = metadata["output"]["sha256"]
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    faults = mgba["invalid_indicator_fault_injections"]
    natural = mgba["natural_actashi_route"]
    natural_observation = natural["observation"]
    branch_lines = "\n".join(
        f"- {row['branch']} / Trainer {row['trainer_id']}: "
        f"PP {row['pp_before']}→{row['pp_after']}、HP更新={row['hp_changed']}、"
        f"不正通知={row['placeholder_item_entries']}"
        for row in mgba["branches"]
    )
    priority_lines = "\n".join(
        f"- {row['effect']}: indicator={row['indicator_seen']}、"
        f"先頭bank={row['first_bank']}、通知={row['notification_seen']}、"
        f"特性名有効={row['ability_name_valid']}、"
        f"PP {row['observation']['pp_before']}→{row['observation']['pp_after']}"
        for row in mgba["legitimate_priority_effects"]
    )
    fault_lines = "\n".join(
        f"- fault {row['indicator']}: bank={row['bank']}、ability={row['ability']}、"
        f"破棄={row['observation']['invalid_indicator_rejected']}、"
        f"Quick Draw通知={row['observation']['quick_draw_script_entries']}、"
        f"PP {row['observation']['pp_before']}→{row['observation']['pp_after']}"
        for row in faults
    )
    text = f"""# 初戦の行動順通知ループ修正

## 結論

- stage 20のTrainer 327（アクタシ選択、相手リープン）を含む初戦3分岐は、固定入力では通常進行した。
- Delta/VBA-M stateと同じアクタシ第2特性64を確認し、不正なQuick Draw indicatorを命令単位で注入した。
- stage 21はturn scheduler入口でindicatorと実特性を照合し、Quick Draw以外なら通知前に破棄して同じターンを継続する。
- 正規Quick Drawは通知を1回表示し、popup ability ID 260が設定される。Quick Draw防御の正本はstage 21 runtime wrapperとする。

## ROM差分

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Patch: `{metadata['patch']['site_address']}` / {metadata['patch']['span_size']} bytes / 実変更 {metadata['patch']['changed_byte_count']} bytes
- Runtime: `{metadata['runtime']['address']:#010x}` / {metadata['runtime']['size']} bytes / `{metadata['runtime']['sha256']}`
- New allocation: {metadata['allocation']['new_allocation_count']} / allocator overlap: {metadata['allocation']['overlap_count']}
- clean FireRed Rev.0→stage 21 BPS往復: {metadata['release_patch_round_trip']['exact']} / `{metadata['release_patch_round_trip']['patch_sha256']}`

## libmGBA実ROM回帰

- 自然new-game経路: アクタシ選択={natural['selected_actashi']}、Trainer 327開始={natural['trainer_327_started']}、A入力={natural['a_presses']}回
- 自然初戦: ability {natural_observation['player_ability']}/{natural_observation['opponent_ability']}、PP {natural_observation['pp_before']}→{natural_observation['pp_after']}、HP更新={natural_observation['hp_changed']}、不正通知={natural_observation['placeholder_item_entries']}
- gNewBS / pending shadow安定: {natural['pointer_stable']} / {natural['pending_shadow_stable']}
{branch_lines}
{fault_lines}
{priority_lines}
- warnings/errors: {mgba['warnings_errors']}
- deterministic process runs: {mgba['process_runs']}

既存stage 20を再利用し、全stageの重い再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs = build_hotfix_outputs(root)
    repeated = build_hotfix_outputs(root)
    if outputs != repeated:
        _fail("first-battle hotfix build is not byte deterministic")
    metadata = json.loads(outputs[STAGE21_META.as_posix()])
    mgba = _mgba_fixture(root, outputs[STAGE21.as_posix()], metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT)
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(
                f"First-battle hotfix build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE21.as_posix()])})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file()
                or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(
                f"First-battle hotfix check: PASS "
                f"({len(outputs)} artifacts, side effects NONE)"
            )
    except (
        FirstBattleHotfixError, OSError, KeyError, TypeError, ValueError,
        subprocess.SubprocessError, BpsError,
    ) as error:
        print(f"First-battle hotfix {args.mode}: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
