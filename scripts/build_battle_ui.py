#!/usr/bin/env python3
"""stage 23へ固定CFRU由来の技タイプ・有効度UI adapterを結合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
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

from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402
from scripts.fast_stage_reuse import (  # noqa: E402
    generated_input_may_follow_stage,
    trusted_stage_sha,
    trusted_t06_fingerprint,
)


TASK = "USER-20260814-BATTLE-UI"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
CONFIG = Path("config/battle_ui.json")
STAGE06_META = Path("build/stages/06_battle_core.json")
STAGE06 = Path("build/stages/06_battle_core.gba")
STAGE17 = Path("build/stages/17_regression.gba")
STAGE17_META = Path("build/stages/17_regression.json")
STAGE23 = Path("build/stages/23_battle_rules.gba")
STAGE23_META = Path("build/stages/23_battle_rules.json")
STAGE23_ALLOCATION = Path("build/stages/23_allocation.json")
STAGE24 = Path("build/stages/24_battle_ui.gba")
STAGE24_META = Path("build/stages/24_battle_ui.json")
STAGE24_ALLOCATION = Path("build/stages/24_allocation.json")
RUNTIME_BIN = Path("generated/runtime/battle_ui.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/battle_ui_symbols.json")
MGBA_FIXTURE = Path("build/stages/24_mgba_battle_ui.json")
POLICY_FIXTURE = Path("build/stages/24_mgba_battle_policy.json")
REPORT = Path("reports/generated/battle_ui.md")
RUNNER = Path("tools/mgba_battle_ui_smoke.c")
POLICY_RUNNER = Path("tools/mgba_battle_policy_smoke.c")
EMBEDDED_RUNNER_SOURCES = (
    Path("tools/mgba_battle_core_smoke.c"),
    Path("tools/mgba_ai_fixture_runner.c"),
)
ALLOCATION_NAME = "battle_ui_runtime"
EXPECTED_STAGE23_SHA256 = "54a36507d0ca5e85408c5c2f4f8984feb2a396e15d67d5cc75b8af621bd7dc97"
EXPECTED_CFRU_COMMIT = "e24a16fe39e27ae162faf5b78596d1f3df18489d"
EXPECTED_CFRU_TREE = "f4424af017abd01afe2d2deb833fb67275f03804"
EXPECTED_T06_FINGERPRINT = "0a4c04b64ee012db93c6b6bda92aa0e277fc79f63aa0e133f47f3f2cd0b17b03"


def _expected_stage23(root: Path) -> str:
    return trusted_stage_sha(
        root, STAGE23, STAGE23_META, "USER-20260814-BATTLE-RULES",
        EXPECTED_STAGE23_SHA256,
    )


def _expected_t06_fingerprint(root: Path) -> str:
    return trusted_t06_fingerprint(
        root, STAGE06_META, EXPECTED_T06_FINGERPRINT,
    )

REQUIRED_SYMBOLS = {
    "VegaBattleUI_ClassifyResult",
    "VegaBattleUI_GetSelectedMoveType",
    "VegaBattleUI_DisplayMoveType",
    "VegaBattleUI_DisplayMoveEffectiveness",
    "VegaBattleUI_InitMoveSelection",
    "VegaBattleUI_HandleInputChooseMove",
    "VegaBattleUI_GuardHelpOpen",
}

UPSTREAM_SYMBOLS = {
    "InitMoveSelectionsVarsAndStrings": (0x09116310, 0x2C8),
    "HandleInputChooseMove": (0x09116E40, 0x119C),
    "MoveSelectionDisplayMoveType": (0x0911570C, 0xB8),
    "MoveSelectionDisplayMoveEffectiveness": (0x09116DF0, 0x50),
    "HandleInputChooseTarget": (0x09115CEC, 0x624),
    "CountAliveMonsInBattle": (0x090E8120, 0x138),
    "TeraTypeActive": (0x09130528, 0x2C),
    "CheckTableForMoveEffect": (0x09130E14, 0x30),
    "gUserInterfaceGfx_TypeHighlightingPal": (0x091B66A0, 0x20),
    "PSSIconsTiles": (0x091B5348, 0x240),
    "sText_StabMoveInterfaceType": (0x091683DC, 0x09),
    "gTypeEffectiveness": (0x09164A8C, 0x4E2),
}

UPSTREAM_ADDRESS_ONLY = {
    "gText_BattleUI_SuperEffective": 0x091430E3,
    "gText_BattleUI_NotVeryEffective": 0x091430E6,
    "gText_BattleUI_NoEffect": 0x091430E9,
    "gText_BattleUI_STAB": 0x091430EB,
    "gText_Acc": 0x09143100,
    "StringNull": 0x09001CB5,
    "gMoveEffectsThatIgnoreWeaknessResistance": 0x0903FE65,
}

SOURCE_ANCHORS = (
    ("emit_real_type", "src/move_menu.c", "tempMoveStruct->moveTypes[i] = GetMoveTypeSpecial"),
    ("emit_visual_result", "src/move_menu.c", "u8 moveResult = VisualTypeCalc(move, gActiveBattler, j);"),
    ("real_type_gate", "src/move_menu.c", "#ifdef DISPLAY_REAL_MOVE_TYPE_ON_MENU"),
    ("effectiveness_gate", "src/move_menu.c", "#ifdef DISPLAY_EFFECTIVENESS_ON_MENU"),
    ("effect_no_effect_first", "src/move_menu.c", "if (moveResult & MOVE_RESULT_NO_EFFECT)"),
    ("effect_super", "src/move_menu.c", "else if (moveResult & MOVE_RESULT_SUPER_EFFECTIVE)"),
    ("effect_resisted", "src/move_menu.c", "else if (moveResult & MOVE_RESULT_NOT_VERY_EFFECTIVE)"),
    ("visual_type_calc", "src/damage_calc.c", "u8 VisualTypeCalc(u16 move, u8 bankAtk, u8 bankDef)"),
    ("stellar_rule", "src/damage_calc.c", "if (moveType == TYPE_STELLAR && IsTerastal(bankDef))"),
)

AUDIT_SURFACES = {
    "EmitChooseMoveHook",
    "MoveSelectionDisplayMoveType",
    "MoveSelectionDisplayMoveEffectiveness",
    "HandleInputChooseMove",
    "InitMoveSelectionsVarsAndStrings",
}

RESERVED_ITEM_PLACEHOLDERS = {
    0, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 72, 82, 87, 88,
    89, 90, 91, 92, 99, 100, 101, 102, 105, 112, 113, 114, 115, 116,
    117, 118, 119, 120, 176, 177, 178, 226, 227, 228, 229, 230, 231,
    232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244,
    245, 246, 247, 248, 249, 250, 251, 252, 253, 267, 347,
}
RUNTIME_ITEM_OVERRIDES = {348}
RESERVED_SPECIES_PLACEHOLDERS = {0, *range(263, 277)}


class BattleUIError(ValueError):
    """battle UI source、owner、runtime、または実ROM fixtureが不正。"""


def _fail(message: str) -> NoReturn:
    raise BattleUIError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed.stdout.strip()


def _address(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"0x[0-9A-Fa-f]+", value):
        return int(value, 16)
    _fail(f"invalid address: {value!r}")


def _rom_slice(rom: bytes, address: int, size: int) -> bytes:
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > len(rom):
        _fail(f"ROM range outside image: 0x{address:08X}+{size}")
    return rom[offset:offset + size]


def _battle_core_contract(metadata: dict[str, Any]) -> dict[str, Any]:
    """UIが実際に依存するT06の決定的な契約だけを取り出す。"""
    runs = metadata.get("upstream_runs")
    if not isinstance(runs, list) or not runs or not isinstance(runs[-1], dict):
        _fail("T06 upstream run evidence missing")
    run = runs[-1]
    return {
        "fingerprint": metadata.get("fingerprint"),
        "rom_sha256": metadata.get("output", {}).get("sha256"),
        "offsets_sha256": run.get("offsets", {}).get("sha256"),
        "linked_object_sha256": run.get("linked_object", {}).get("sha256"),
    }


def _config(root: Path) -> dict[str, Any]:
    config = _read_json(root / CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("battle UI config identity differs")
    if config.get("source") != {
        "path": "vendor/upstream/CFRU-JP",
        "commit": EXPECTED_CFRU_COMMIT,
        "tree": EXPECTED_CFRU_TREE,
    }:
        _fail("battle UI pinned source differs")
    for name, row in config["inputs"].items():
        path = root / row["path"]
        if not path.is_file():
            _fail(f"battle UI pinned input differs: {row['path']}")
        if generated_input_may_follow_stage(str(row["path"])):
            continue
        if name == "battle_core_metadata":
            observed = _battle_core_contract(_read_json(path))
            expected = {key: row.get(key) for key in observed}
            if observed != expected:
                _fail(f"battle UI pinned input differs: {row['path']}")
        elif _sha(path.read_bytes()) != row["sha256"]:
            _fail(f"battle UI pinned input differs: {row['path']}")
    if (
        not generated_input_may_follow_stage(
            str(config["inputs"]["stage_rom"]["path"])
        )
        and config["inputs"]["stage_rom"]["sha256"]
            != EXPECTED_STAGE23_SHA256
    ):
        _fail("battle UI stage23 config hash differs")
    return config


def _find_anchor(path: Path, anchor: str) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    line = next((index for index, value in enumerate(lines, 1) if anchor in value), None)
    if line is None:
        _fail(f"pinned CFRU source anchor missing: {path}: {anchor}")
    return line


def _offset_symbols(path: Path) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([^:]+):\s+([0-9A-Fa-f]{8})", line)
        if match:
            symbols[match.group(1).strip()] = int(match.group(2), 16)
    return symbols


def _nm_sizes(path: Path) -> dict[str, tuple[int, int]]:
    rows: dict[str, tuple[int, int]] = {}
    output = _run(
        ["arm-none-eabi-nm", "-S", "--defined-only", str(path)],
        "T06 linked object symbol audit",
    )
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 4:
            rows[fields[3]] = (int(fields[0], 16), int(fields[1], 16))
    return rows


def audit_source(root: Path = ROOT, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or _config(root)
    source_root = root / config["source"]["path"]
    commit = _run(["git", "rev-parse", "HEAD"], "CFRU source commit", cwd=source_root)
    tree = _run(["git", "rev-parse", "HEAD^{tree}"], "CFRU source tree", cwd=source_root)
    dirty = _run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        "CFRU source status", cwd=source_root,
    )
    if commit != EXPECTED_CFRU_COMMIT or tree != EXPECTED_CFRU_TREE or dirty:
        _fail("fixed CFRU checkout identity/cleanliness differs")

    lock = _read_json(root / "state/source-lock.json")
    rows = [
        row for row in lock.get("sources", [])
        if isinstance(row, dict) and row.get("name") == "cfru"
    ]
    if len(rows) != 1 or any(
        rows[0].get(key) != EXPECTED_CFRU_COMMIT
        for key in ("configured_commit", "actual_commit", "resolved_commit")
    ):
        _fail("state/source-lock.json CFRU pin differs")

    profile = root / "config/cfru_vega_minimal.h"
    profile_text = profile.read_text(encoding="utf-8")
    macro_states = {
        name: bool(re.search(rf"^\s*#\s*define\s+{name}\b", profile_text, re.MULTILINE))
        for name in ("DISPLAY_REAL_MOVE_TYPE_ON_MENU", "DISPLAY_EFFECTIVENESS_ON_MENU")
    }
    if any(macro_states.values()) or any(
        not re.search(rf"^\s*#\s*undef\s+{name}\b", profile_text, re.MULTILINE)
        for name in macro_states
    ):
        _fail("minimal CFRU UI macro state differs")

    evidence: dict[str, dict[str, Any]] = {}
    source_files: dict[str, dict[str, Any]] = {}
    for key, relative, anchor in SOURCE_ANCHORS:
        path = source_root / relative
        raw = path.read_bytes()
        evidence[key] = {
            "path": f"{config['source']['path']}/{relative}",
            "line": _find_anchor(path, anchor),
            "anchor": anchor,
            "file_sha256": _sha(raw),
        }
        source_files[relative] = {"size": len(raw), "sha256": _sha(raw)}

    t06 = _read_json(root / STAGE06_META)
    t06_fingerprint = _expected_t06_fingerprint(root)
    if t06.get("fingerprint") != t06_fingerprint or t06.get("status") != "PASS":
        _fail("T06 battle-core identity differs")
    run = t06.get("upstream_runs", [{}])[-1]
    build_root = root / "build/battle-core" / t06_fingerprint / "run-1"
    offsets_path = build_root / "offsets.ini"
    linked_path = build_root / "linked.o"
    if (
        _sha(offsets_path.read_bytes()) != run.get("offsets", {}).get("sha256")
        or _sha(linked_path.read_bytes()) != run.get("linked_object", {}).get("sha256")
    ):
        _fail("T06 linked evidence differs")
    offsets = _offset_symbols(offsets_path)
    sizes = _nm_sizes(linked_path)
    symbols: dict[str, dict[str, Any]] = {}
    for name, (address, size) in UPSTREAM_SYMBOLS.items():
        if offsets.get(name) != address or sizes.get(name) != (address, size):
            _fail(f"T06 UI symbol ABI differs: {name}")
        symbols[name] = {"address": address, "size": size}
    for name, address in UPSTREAM_ADDRESS_ONLY.items():
        if offsets.get(name) != address:
            _fail(f"T06 UI data symbol differs: {name}")
        symbols[name] = {"address": address}

    return {
        "status": "PASS",
        "commit": commit,
        "tree": tree,
        "source_lock_verified": True,
        "source_checkout_clean": True,
        "profile": profile.relative_to(root).as_posix(),
        "profile_sha256": _sha(profile.read_bytes()),
        "profile_ui_macros_active": macro_states,
        "adapter_reason": "T06の固定payloadを再構築せず、無効だったsource UI分岐とinline済みcursor経路を同じABIで接続",
        "files": source_files,
        "evidence": evidence,
        "linked_symbols": symbols,
        "offsets_sha256": _sha(offsets_path.read_bytes()),
        "linked_object_sha256": _sha(linked_path.read_bytes()),
    }


def _hook_target(rom: bytes, address: int) -> int:
    stub = _rom_slice(rom, address, 8)
    register = stub[1] & 7
    if (
        stub[0] != 0 or stub[1] != 0x48 | register
        or stub[2] != register * 8 or stub[3] != 0x47
    ):
        _fail(f"Thumb absolute hook shape differs: 0x{address:08X}")
    target = struct.unpack_from("<I", stub, 4)[0]
    if not target & 1:
        _fail(f"Thumb target is not odd: 0x{address:08X}")
    return target


def _audit_address_csv(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / config["inputs"]["address_audit"]["path"]
    matches: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if (
                row.get("engine") == "cfru"
                and row.get("profile") in {"baseline", "factory-like", "minimal"}
                and row.get("symbol") in AUDIT_SURFACES
            ):
                matches.append(row)
    expected = len(AUDIT_SURFACES) * 3
    if len(matches) != expected or any(row["classification"] != "CFRU" for row in matches):
        _fail("address audit does not prove all battle UI surfaces are CFRU-owned")
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha(path.read_bytes()),
        "rows": len(matches),
        "profiles": sorted({row["profile"] for row in matches}),
        "symbols": sorted({row["symbol"] for row in matches}),
        "classifications": {"CFRU": len(matches)},
    }


def audit_owner(root: Path = ROOT, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or _config(root)
    rom = (root / STAGE23).read_bytes()
    if len(rom) != ROM_SIZE or _sha(rom) != _expected_stage23(root):
        _fail("stage23 owner input differs")
    owners = config["owners"]
    observed: dict[str, dict[str, Any]] = {}
    for key in ("emit_choose_move",):
        row = owners[key]
        site = _address(row["hook"])
        target = _hook_target(rom, site)
        if target != _address(row["target"]):
            _fail(f"battle UI owner target differs: {key}")
        observed[key] = {"hook": site, "target": target}
    for key in (
        "display_move_type", "display_effectiveness",
        "handle_input_choose_move", "init_move_selection",
    ):
        row = owners[key]
        site = _address(row["hook"])
        entry = _address(row["entry"])
        target = _hook_target(rom, site)
        expected = bytes.fromhex(row["expected_hex"])
        if target != _address(row["target"]) or _rom_slice(rom, entry, len(expected)) != expected:
            _fail(f"battle UI patch entry differs: {key}")
        observed[key] = {
            "hook": site, "target": target, "entry": entry,
            "entry_sha256": _sha(expected),
        }
    return {
        "status": "PASS",
        "pre_owner": "CFRU_FIXED_PAYLOAD",
        "post_owner": "CFRU_FIXED_PAYLOAD_WITH_SOURCE_EQUIVALENT_UI_ADAPTER",
        "global_owner_shared_by_normal_factory_raid": True,
        "stock_hooks": observed,
        "address_audit": _audit_address_csv(root, config),
    }


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = _read_json(root / STAGE23_ALLOCATION)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage23 allocator overlap contract failed")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in report["allocations"]]


def _allocation(root: Path, size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 4,
        "owner": TASK,
        "purpose": "固定CFRU move type/effectiveness/STAB表示adapter",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(row for row in report["allocations"] if row["name"] == ALLOCATION_NAME)
    return allocation, report


def _compile_runtime(
    root: Path, load_address: int, linked_symbols: dict[str, dict[str, Any]]
) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for battle UI runtime")
    source = root / "overlays/battle_ui/battle_ui.c"
    assembly = root / "overlays/battle_ui/battle_ui_trampoline.S"
    header = root / "overlays/battle_ui/battle_ui.h"
    if not source.is_file() or not assembly.is_file() or not header.is_file():
        _fail("battle UI adapter source is missing")
    with tempfile.TemporaryDirectory(prefix="vega-battle-ui-") as raw:
        directory = Path(raw)
        linker = directory / "linker.ld"
        elf = directory / "battle_ui.elf"
        binary = directory / "battle_ui.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaBattleUI_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-DVEGA_BATTLE_UI_LINKED_ABI=1",
            f"-DVEGA_UI_TYPE_HIGHLIGHT_PALETTE_ADDRESS=0x{linked_symbols['gUserInterfaceGfx_TypeHighlightingPal']['address']:08X}u",
            f"-DVEGA_UI_PSS_ICONS_ADDRESS=0x{linked_symbols['PSSIconsTiles']['address']:08X}u",
            f"-DVEGA_UI_TEXT_SUPER_ADDRESS=0x{linked_symbols['gText_BattleUI_SuperEffective']['address']:08X}u",
            f"-DVEGA_UI_TEXT_RESISTED_ADDRESS=0x{linked_symbols['gText_BattleUI_NotVeryEffective']['address']:08X}u",
            f"-DVEGA_UI_TEXT_NONE_ADDRESS=0x{linked_symbols['gText_BattleUI_NoEffect']['address']:08X}u",
            f"-DVEGA_UI_TEXT_STAB_ADDRESS=0x{linked_symbols['gText_BattleUI_STAB']['address']:08X}u",
            f"-DVEGA_UI_TEXT_STAB_PREFIX_ADDRESS=0x{linked_symbols['sText_StabMoveInterfaceType']['address']:08X}u",
            f"-DVEGA_UI_COUNT_ALIVE_MONS_ADDRESS=0x{linked_symbols['CountAliveMonsInBattle']['address'] | 1:08X}u",
            f"-DVEGA_UI_TERA_TYPE_ACTIVE_ADDRESS=0x{linked_symbols['TeraTypeActive']['address'] | 1:08X}u",
            f"-DVEGA_UI_CHECK_MOVE_EFFECT_TABLE_ADDRESS=0x{linked_symbols['CheckTableForMoveEffect']['address'] | 1:08X}u",
            f"-DVEGA_UI_HANDLE_CHOOSE_TARGET_ADDRESS=0x{linked_symbols['HandleInputChooseTarget']['address'] | 1:08X}u",
            f"-DVEGA_UI_HANDLE_CHOOSE_MOVE_HOOK_ADDRESS=0x{_address(_config(root)['owners']['handle_input_choose_move']['hook']) | 1:08X}u",
            f"-DVEGA_UI_INIT_MOVE_SELECTION_CONTINUE_ADDRESS=0x{linked_symbols['InitMoveSelectionsVarsAndStrings']['address'] + 8 | 1:08X}",
            f"-DVEGA_UI_HANDLE_CHOOSE_MOVE_CONTINUE_ADDRESS=0x{linked_symbols['HandleInputChooseMove']['address'] + 8 | 1:08X}",
            f"-DVEGA_UI_HELP_OPEN_CONTINUE_ADDRESS=0x{_address(_config(root)['owners']['help_open_guard']['entry']) + 8 | 1:08X}",
            "-DVEGA_UI_HELP_OPEN_SUPPRESS_ADDRESS=0x0813C0C5",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaBattleUI_DisplayMoveType", f"-Wl,-T,{linker}",
            f"-I{source.parent}", str(source), str(assembly), "-o", str(elf),
        ], "battle UI ARM link", cwd=root)
        undefined = _run([nm, "-u", str(elf)], "battle UI undefined-symbol check")
        if undefined:
            _fail("battle UI image has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "battle UI objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "battle UI nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("VegaBattleUI_"):
                symbols[fields[2]] = int(fields[0], 16)
        if set(symbols) != REQUIRED_SYMBOLS:
            _fail(f"battle UI entrypoint set differs: {sorted(symbols)}")
        runtime = binary.read_bytes()
        if not runtime or len(runtime) > 4096:
            _fail(f"unexpected battle UI runtime size: {len(runtime)}")
        return runtime, symbols


def _patch(output: bytearray, address: int, expected: bytes, replacement: bytes, label: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{label}: patch size differs")
    offset = address - GBA_ROM_BASE
    actual = bytes(output[offset:offset + len(expected)])
    if actual != expected:
        _fail(f"{label}: expected={expected.hex()} actual={actual.hex()}")
    output[offset:offset + len(expected)] = replacement
    return {
        "label": label, "address": address, "offset": offset, "size": len(expected),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _has_placeholder(text: object) -> bool:
    return isinstance(text, str) and ("?" in text or "？" in text)


def audit_strings(root: Path, source: bytes, output: bytes, config: dict[str, Any]) -> dict[str, Any]:
    move_model = _read_json(root / config["inputs"]["move_model"]["path"])
    id_model = _read_json(root / config["inputs"]["id_model"]["path"])
    species_model = _read_json(root / config["inputs"]["species_model"]["path"])
    moves = move_model.get("moves", [])
    abilities = id_model.get("abilities", [])
    items = id_model.get("items", [])
    species = species_model.get("species", [])
    if (len(moves), len(abilities), len(items), len(species)) != (1063, 312, 999, 1621):
        _fail("canonical name model counts differ")
    move_unresolved = {row["id"] for row in moves if _has_placeholder(row.get("display_name"))}
    ability_unresolved = {row["id"] for row in abilities if _has_placeholder(row.get("display_name"))}
    item_unresolved = {row["id"] for row in items if _has_placeholder(row.get("display_name"))}
    species_unresolved = {row["id"] for row in species if _has_placeholder(row.get("display_name"))}
    if move_unresolved or ability_unresolved:
        _fail("live move/ability name placeholder remains")
    if item_unresolved != RESERVED_ITEM_PLACEHOLDERS | RUNTIME_ITEM_OVERRIDES:
        _fail("reserved item placeholder set differs")
    inert_items = {
        row["id"] for row in items
        if row["id"] in RESERVED_ITEM_PLACEHOLDERS
        and row.get("price") == 0
        and row.get("importance") == 0
        and row.get("battle_usage") == 0
        and row.get("hold_effect_key") == "NONE"
        and row.get("battle_effect_key") == "NONE"
        and row.get("status") == "FROZEN"
    }
    if inert_items != RESERVED_ITEM_PLACEHOLDERS:
        _fail("placeholder item is reachable through a live battle effect")
    if species_unresolved != RESERVED_SPECIES_PLACEHOLDERS or any(
        row.get("canonical_national_dex") != 0
        for row in species if row["id"] in species_unresolved
    ):
        _fail("reserved Species placeholder set differs")

    t06 = _read_json(root / STAGE06_META)
    stage06 = (root / STAGE06).read_bytes()
    stage17 = (root / STAGE17).read_bytes()
    stage17_meta = _read_json(root / STAGE17_META)
    if (
        len(stage06) != ROM_SIZE
        or len(stage17) != ROM_SIZE
        or _sha(stage06) != t06.get("output", {}).get("sha256")
        or _sha(stage17) != stage17_meta.get("output", {}).get("sha256")
    ):
        _fail("stage06/stage17 runtime-table provenance differs")
    radar = stage17_meta.get("wild", {}).get("tohoku_overlay", {}).get(
        "ecology_radar", {}
    )
    if radar.get("item_id") != 348:
        _fail("stage17 ecology radar metadata differs")
    tables: dict[str, dict[str, Any]] = {}
    for name in ("move_names", "ability_names", "item_data"):
        row = t06["runtime_tables"][name]
        start = int(row["address"]) - GBA_ROM_BASE
        size = int(row["size"])
        before = source[start:start + size]
        after = output[start:start + size]
        if before != after:
            _fail(f"canonical runtime table changed: {name}")
        canonicalized = bytearray(after)
        runtime_overrides: list[int] = []
        if name == "item_data":
            stride = int(row["stride"])
            relative = 348 * stride
            if relative + stride > size:
                _fail("ecology radar item row is outside canonical item table")
            expected_override = stage17[start + relative:start + relative + stride]
            if (
                radar.get("item_address") != GBA_ROM_BASE + start + relative
                or struct.unpack_from("<H", expected_override, 10)[0] != 348
                or struct.unpack_from("<I", expected_override, 16)[0]
                    != radar.get("description_address")
                or struct.unpack_from("<I", expected_override, 24)[0]
                    != radar.get("field_callback")
            ):
                _fail("ecology radar item ABI differs from stage17 metadata")
            if after[relative:relative + stride] != expected_override:
                _fail("ecology radar item row differs from validated stage17")
            canonicalized[relative:relative + stride] = stage06[
                start + relative:start + relative + stride
            ]
            runtime_overrides.append(348)
        if _sha(bytes(canonicalized)) != row["sha256"]:
            _fail(f"canonical runtime table changed outside overrides: {name}")
        tables[name] = {
            "address": row["address"], "count": row["count"],
            "stride": row["stride"], "sha256": row["sha256"],
            "effective_sha256": _sha(after),
            "runtime_override_item_ids": runtime_overrides,
            "unchanged": True,
        }
    species_names = root / config["inputs"]["species_names"]["path"]
    species_raw = species_names.read_bytes()
    if len(species_raw) != 1621 * 11 or _sha(species_raw) != config["inputs"]["species_names"]["sha256"]:
        _fail("canonical Species name artifact differs")
    first = _read_json(root / config["inputs"]["first_battle_fixture"]["path"])
    fault_observations = [
        row.get("observation", {})
        for row in first.get("invalid_indicator_fault_injections", [])
        if isinstance(row, dict)
    ]
    placeholder_observations = [
        row.get("placeholder_item_entries")
        for row in [*first.get("branches", []), *fault_observations]
    ]
    if not placeholder_observations or any(value != 0 for value in placeholder_observations):
        _fail("first-battle item notification exposed a placeholder")
    return {
        "status": "PASS",
        "counts": {"moves": 1063, "abilities": 312, "items": 999, "species": 1621},
        "live_unresolved": {"moves": [], "abilities": [], "items": [], "species": []},
        "reserved_inert_item_ids": sorted(inert_items),
        "runtime_item_overrides": sorted(RUNTIME_ITEM_OVERRIDES),
        "reserved_non_dex_species_ids": sorted(species_unresolved),
        "runtime_tables": tables,
        "species_names": {"path": species_names.relative_to(root).as_posix(), "sha256": _sha(species_raw)},
        "first_battle_placeholder_item_entries": placeholder_observations,
    }


def _build_stage(root: Path = ROOT) -> tuple[dict[str, bytes], dict[str, Any]]:
    config = _config(root)
    source_audit = audit_source(root, config)
    owner_audit = audit_owner(root, config)
    source = (root / STAGE23).read_bytes()
    expected_stage23 = _expected_stage23(root)
    if len(source) != ROM_SIZE or _sha(source) != expected_stage23:
        _fail("stage23 size/hash contract failed")
    stage23_meta = _read_json(root / STAGE23_META)
    if stage23_meta.get("status") != "PASS" or stage23_meta.get("output", {}).get("sha256") != _sha(source):
        _fail("stage23 metadata contract failed")

    provisional, _ = _allocation(root, 4096, "0" * 64)
    payload_offset = int(provisional["start"])
    runtime, symbols = _compile_runtime(
        root, GBA_ROM_BASE + payload_offset, source_audit["linked_symbols"]
    )
    allocation, allocation_report = _allocation(root, len(runtime), _sha(runtime))
    if int(allocation["start"]) != payload_offset:
        _fail("battle UI allocation moved after final link")
    payload_end = int(allocation["end_exclusive"])
    if source[payload_offset:payload_end] != bytes([0xFF]) * len(runtime):
        _fail("battle UI allocation destination is not erased FF")

    output = bytearray(source)
    output[payload_offset:payload_end] = runtime
    patches: list[dict[str, Any]] = []
    patch_contract = (
        ("display_move_type", "VegaBattleUI_DisplayMoveType"),
        ("display_effectiveness", "VegaBattleUI_DisplayMoveEffectiveness"),
        ("handle_input_choose_move", "VegaBattleUI_HandleInputChooseMove"),
        ("init_move_selection", "VegaBattleUI_InitMoveSelection"),
        ("help_open_guard", "VegaBattleUI_GuardHelpOpen"),
    )
    for owner_key, symbol in patch_contract:
        row = config["owners"][owner_key]
        target = symbols[symbol] | 1
        replacement = bytes.fromhex("00 4b 18 47") + struct.pack("<I", target)
        patches.append(_patch(
            output, _address(row["entry"]), bytes.fromhex(row["expected_hex"]),
            replacement, f"{owner_key} source-equivalent adapter",
        ))
    output_raw = bytes(output)
    allowed = set(range(payload_offset, payload_end))
    for row in patches:
        allowed.update(range(row["offset"], row["offset"] + row["size"]))
    changed = {index for index, pair in enumerate(zip(source, output_raw)) if pair[0] != pair[1]}
    if not changed <= allowed:
        _fail("battle UI build changed bytes outside allocation/entry stubs")
    if (
        _hook_target(output_raw, _address(config["owners"]["display_move_type"]["entry"]))
        != symbols["VegaBattleUI_DisplayMoveType"] | 1
        or _hook_target(output_raw, _address(config["owners"]["display_effectiveness"]["entry"]))
        != symbols["VegaBattleUI_DisplayMoveEffectiveness"] | 1
        or _hook_target(output_raw, _address(config["owners"]["handle_input_choose_move"]["entry"]))
        != symbols["VegaBattleUI_HandleInputChooseMove"] | 1
        or _hook_target(output_raw, _address(config["owners"]["init_move_selection"]["entry"]))
        != symbols["VegaBattleUI_InitMoveSelection"] | 1
        or _hook_target(output_raw, _address(config["owners"]["help_open_guard"]["entry"]))
        != symbols["VegaBattleUI_GuardHelpOpen"] | 1
    ):
        _fail("battle UI post-patch ownership chain differs")

    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity differs")
    release_patch = create_bps(
        clean, output_raw, metadata=f"{TASK}:{_sha(output_raw)}".encode("ascii"))
    if apply_bps(clean, release_patch) != output_raw:
        _fail("clean ROM to stage24 BPS round-trip differs")

    strings = audit_strings(root, source, output_raw, config)
    symbol_payload = {
        "schema_version": 1,
        "task": TASK,
        "load_address": GBA_ROM_BASE + payload_offset,
        "symbols": {name: address | 1 for name, address in sorted(symbols.items())},
    }
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {"path": STAGE23.as_posix(), "size": len(source), "sha256": _sha(source)},
        "output": {"path": STAGE24.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        "source_audit": source_audit,
        "owner_audit": owner_audit,
        "runtime": {
            "allocation_name": ALLOCATION_NAME,
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(runtime),
            "sha256": _sha(runtime),
            "symbols": symbol_payload["symbols"],
        },
        "patches": patches,
        "string_audit": strings,
        "allocation": {
            "path": STAGE24_ALLOCATION.as_posix(),
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patch_round_trip": {
            "format": "BPS1", "source_sha256": _sha(clean),
            "target_sha256": _sha(output_raw), "patch_sha256": _sha(release_patch),
            "patch_size": len(release_patch), "exact": True,
        },
        "invariants": {
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "stage23_hash_pinned": _sha(source) == expected_stage23,
            "source_lock_verified": source_audit["source_lock_verified"],
            "fixed_cfru_ui_abi_verified": len(source_audit["linked_symbols"]) == 19,
            "normal_factory_raid_share_owner": owner_audit["global_owner_shared_by_normal_factory_raid"],
            "five_owner_entry_stubs_only": len(patches) == 5,
            "declared_changes_only": changed <= allowed,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "canonical_live_strings_resolved": all(not values for values in strings["live_unresolved"].values()),
            "release_patch_exact": True,
        },
    }
    failed = [name for name, passed in metadata["invariants"].items() if not passed]
    if failed:
        _fail("battle UI invariant failed: " + ", ".join(failed))
    return ({
        STAGE24.as_posix(): output_raw,
        STAGE24_ALLOCATION.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): runtime,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbol_payload),
    }, metadata)


def _tool_identity(root: Path) -> dict[str, str]:
    cc = shutil.which(os.environ.get("CC", "cc"))
    if not cc:
        _fail("C compiler missing")
    version = _run([cc, "--version"], "C compiler version").splitlines()[0]
    pkg = shutil.which("pkg-config")
    mgba = "linker:-lmgba"
    if pkg:
        probe = subprocess.run(
            [pkg, "--modversion", "mgba"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            mgba = probe.stdout.strip()
    return {"cc": cc, "cc_version": version, "libmgba": mgba}


def _runner_cache_key(root: Path, sources: Sequence[Path], rom_sha256: str, extra: object) -> tuple[str, dict[str, Any]]:
    payload = {
        "schema_version": 1,
        "rom_sha256": rom_sha256,
        "sources": {path.as_posix(): _sha((root / path).read_bytes()) for path in sources},
        "toolchain": _tool_identity(root),
        "extra": extra,
    }
    return _sha(_stable(payload)), payload


def _validate_ui_fixture(value: dict[str, Any], rom_sha256: str) -> None:
    expected_cases = {
        "NORMAL_1X": 0,
        "SUPER_2X_OR_MORE": 1,
        "RESISTED_HALF_OR_LESS": 2,
        "NO_EFFECT_0X": 3,
        "SUPER_AND_STAB": 1,
    }
    cases = value.get("effect_cases", [])
    observed = {row.get("name"): row.get("class") for row in cases}
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "cfru_move_menu_effectiveness_v5"
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or not value.get("read_only")
        or observed != expected_cases
        or any(row.get("palette_group") != row.get("class") for row in cases)
        or any(not row.get("effect_label") or not row.get("entry_completed") for row in cases)
        or not next(row for row in cases if row["name"] == "SUPER_AND_STAB").get("stab")
        or value.get("type_cases") != {"stellar": 24, "tera_blast_selected": 24, "tera_blast_clear": 10}
        or value.get("matrix_multipliers") != [500, 2000, 4000, 250, 0]
        or not value.get("double_target_specific")
        or not value.get("actual_menu_path")
        or value.get("actual_menu_super") != {
            "type_entry_seen": True,
            "effect_entry_seen": True,
            "super_label_seen": True,
            "cursor_before": 0,
            "cursor_after": 1,
            "palette_group": 1,
            "controller_stable": True,
        }
        or not value.get("field_help_forwarded")
        or value.get("default_help_guard") != {
            "details_opened": True, "accuracy_label": True,
            "closed": True, "pointer_stable": True,
            "help_state_idle": True, "controller_stable": True,
            "button_mode": 0,
        }
        or value.get("l_move_details") != {
            "opened": True, "accuracy_label": True,
            "closed": True, "pointer_stable": True, "button_mode": 1,
        }
        or not value.get("input_return")
        or not value.get("routes", {}).get("wild", {}).get("pp_spent")
        or not value.get("routes", {}).get("trainer", {}).get("pp_spent")
        or not value.get("routes", {}).get("double", {}).get("both_opponents_hit")
    ):
        _fail("battle UI exact-ROM fixture differs")


def _ui_fixture(root: Path, rom: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    symbols = metadata["runtime"]["symbols"]
    linked = metadata["source_audit"]["linked_symbols"]
    owners = metadata["owner_audit"]["stock_hooks"]
    selected = {
        name: symbols[name] for name in (
            "VegaBattleUI_DisplayMoveType",
            "VegaBattleUI_DisplayMoveEffectiveness",
            "VegaBattleUI_ClassifyResult",
            "VegaBattleUI_GetSelectedMoveType",
            "VegaBattleUI_GuardHelpOpen",
        )
    }
    selected.update({
        "type_entry": owners["display_move_type"]["entry"],
        "effect_entry": owners["display_effectiveness"]["entry"],
        "type_palette": linked["gUserInterfaceGfx_TypeHighlightingPal"]["address"],
        "text_super": linked["gText_BattleUI_SuperEffective"]["address"],
        "text_resisted": linked["gText_BattleUI_NotVeryEffective"]["address"],
        "text_none": linked["gText_BattleUI_NoEffect"]["address"],
        "text_stab": linked["gText_BattleUI_STAB"]["address"],
        "text_accuracy": linked["gText_Acc"]["address"],
        "type_matrix": linked["gTypeEffectiveness"]["address"],
        "handle_choose_move": _address(
            _config(root)["owners"]["handle_input_choose_move"]["hook"]
        ) | 1,
        "handle_choose_target": linked["HandleInputChooseTarget"]["address"] | 1,
    })
    sources = (RUNNER, *EMBEDDED_RUNNER_SOURCES)
    key, provenance = _runner_cache_key(root, sources, _sha(rom), selected)
    cache = root / MGBA_FIXTURE
    if cache.is_file():
        value = _read_json(cache)
        if value.get("cache", {}).get("key") == key:
            _validate_ui_fixture(value, _sha(rom))
            return value
    with tempfile.TemporaryDirectory(prefix="vega-battle-ui-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE24.name
        executable = directory / "mgba-battle-ui-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / RUNNER), "-o", str(executable), "-lmgba",
        ], "battle UI libmGBA runner compile", cwd=root)
        args = [
            str(executable), str(rom_path), _sha(rom),
            str(selected["VegaBattleUI_DisplayMoveType"]),
            str(selected["VegaBattleUI_DisplayMoveEffectiveness"]),
            str(selected["VegaBattleUI_ClassifyResult"]),
            str(selected["VegaBattleUI_GetSelectedMoveType"]),
            str(selected["type_entry"]),
            str(selected["effect_entry"]),
            str(selected["type_palette"]),
            str(selected["text_super"]),
            str(selected["text_resisted"]),
            str(selected["text_none"]),
            str(selected["text_stab"]),
            str(selected["text_accuracy"]),
            str(selected["type_matrix"]),
            str(selected["handle_choose_move"]),
            str(selected["handle_choose_target"]),
            str(selected["VegaBattleUI_GuardHelpOpen"]),
        ]
        first = json.loads(_run(args, "battle UI exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "battle UI exact-ROM run 2", cwd=root))
        if first != second:
            _fail("battle UI exact-ROM fixture is not process deterministic")
        first["process_runs"] = 2
        first["cache"] = {"key": key, "provenance": provenance}
        _validate_ui_fixture(first, _sha(rom))
        return first


def _policy_symbol_names(source: str) -> list[str]:
    from scripts.build_battle_core import POLICY_SMOKE_SYMBOLS

    start = source.find("#define POLICY_SYMBOL_LIST")
    end = source.find("struct PolicySymbols", start)
    if start < 0 or end < 0:
        _fail("policy runner symbol list missing")
    names = re.findall(r'X\([^,]+,\s*"([^"]+)"\)', source[start:end])
    if tuple(names) != POLICY_SMOKE_SYMBOLS or len(names) != len(set(names)):
        _fail("policy runner symbol contract differs")
    return names


def _validate_policy_fixture(value: dict[str, Any], rom_sha256: str) -> None:
    facility = value.get("facility", {})
    raid = value.get("raid", {})
    if (
        value.get("status") != "PASS"
        or value.get("fixture") != "t06_battle_policy_integration_v1"
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or value.get("unreached_routes") != []
        or facility.get("matrix_cases") != 24
        or not facility.get("scheduler_faint_end")
        or not facility.get("runtime_cleaned")
        or raid.get("initial_shields") != 5
        or raid.get("shield_breaks") != 5
        or not raid.get("raid_state_completion_scheduler_e2e")
        or not raid.get("turn_limit_scheduler_end")
        or not raid.get("normal_wild_no_leak")
        or not raid.get("normal_trainer_no_leak")
        or not raid.get("runtime_cleaned")
    ):
        _fail("stage24 Factory/Raid policy regression differs")


def _policy_fixture(root: Path, rom: bytes) -> dict[str, Any]:
    t06 = _read_json(root / STAGE06_META)
    symbols = t06.get("upstream_runs", [{}])[-1].get("integration_symbols", {})
    source_text = (root / POLICY_RUNNER).read_text(encoding="utf-8")
    names = _policy_symbol_names(source_text)
    if any(name not in symbols for name in names):
        _fail("policy integration symbol missing from T06 evidence")
    selected = {name: symbols[name] for name in names}
    sources = (POLICY_RUNNER, *EMBEDDED_RUNNER_SOURCES)
    key, provenance = _runner_cache_key(root, sources, _sha(rom), selected)
    cache = root / POLICY_FIXTURE
    if cache.is_file():
        value = _read_json(cache)
        if value.get("cache", {}).get("key") == key:
            _validate_policy_fixture(value, _sha(rom))
            return value
    with tempfile.TemporaryDirectory(prefix="vega-battle-ui-policy-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE24.name
        executable = directory / "mgba-battle-policy-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / POLICY_RUNNER), "-o", str(executable), "-lmgba",
        ], "battle UI policy runner compile", cwd=root)
        args = [str(executable), str(rom_path), _sha(rom)]
        args.extend(f"{name}={selected[name]}" for name in names)
        value = json.loads(_run(args, "stage24 Factory/Raid exact-ROM run", cwd=root))
        value["process_runs"] = 1
        source_hash = _sha((root / POLICY_RUNNER).read_bytes())
        value["determinism_reuse"] = {
            "t06_process_runs": t06["battle_policy_smoke"]["process_runs"],
            "t06_source_sha256": t06["battle_policy_smoke"]["source_sha256"],
            "same_runner_source": t06["battle_policy_smoke"]["source_sha256"] == source_hash,
        }
        if value["determinism_reuse"] != {
            "t06_process_runs": 2,
            "t06_source_sha256": source_hash,
            "same_runner_source": True,
        }:
            _fail("T06 policy determinism evidence cannot be reused")
        value["cache"] = {"key": key, "provenance": provenance}
        _validate_policy_fixture(value, _sha(rom))
        return value


def _report(metadata: dict[str, Any], ui: dict[str, Any], policy: dict[str, Any]) -> bytes:
    effect_lines = "\n".join(
        f"- {row['name']}: class={row['class']} / palette={row['palette_group']} / "
        f"effect={row['effect_label']} / STAB={row['stab']}"
        for row in ui["effect_cases"]
    )
    strings = metadata["string_audit"]
    actual_menu_super = json.dumps(
        ui["actual_menu_super"], ensure_ascii=False, sort_keys=True,
    )
    move_details = json.dumps(
        ui["l_move_details"], ensure_ascii=False, sort_keys=True,
    )
    default_help_guard = json.dumps(
        ui["default_help_guard"], ensure_ascii=False, sort_keys=True,
    )
    text = f"""# 戦闘時の技タイプ・有効度UI

## 結論

- 固定CFRU-JP `{EXPECTED_CFRU_COMMIT}` の技選択UI ownerを維持し、無効だった実タイプ・有効度分岐をstage 24 adapterで接続した。
- 判定は独自相性表ではなく、`EmitChooseMove` が実damage側 `VisualTypeCalc` から作る `moveTypes/moveResults` をそのまま表示する。
- 等倍・タイプ不一致は元CFRUどおり空欄。抜群・いまひとつ・無効・タイプ一致は既存CFRU記号とpaletteで判別できる。Factory ROM byteは使用していない。

## exact-ROM結果

{effect_lines}
- Stellar / Tera Blast selected / clear: {ui['type_cases']['stellar']} / {ui['type_cases']['tera_blast_selected']} / {ui['type_cases']['tera_blast_clear']}
- type matrix: {ui['matrix_multipliers']} (1000=1×)
- wild/trainer/double input return: {ui['input_return']} / double target-specific: {ui['double_target_specific']}
- actual action-to-move menu indicator: {ui['actual_menu_path']}
- actual cursor super-effective render: {actual_menu_super}
- default HELP設定での戦闘中L詳細guard: {default_help_guard}
- field HELP passthrough: {ui['field_help_forwarded']}
- L技詳細（威力・命中）open/close: {move_details}
- Factory: {policy['facility']['matrix_cases']} cases / Raid shields: {policy['raid']['shield_breaks']}/{policy['raid']['initial_shields']} / cleanup: {policy['raid']['runtime_cleaned']}
- process runs: UI {ui['process_runs']} / policy {policy['process_runs']} / warnings-errors: {ui['warnings_errors']}+{policy['warnings_errors']}

## ROM・文字列境界

- Input: `{metadata['input']['sha256']}`
- Output: `{metadata['output']['sha256']}`
- Runtime: `0x{metadata['runtime']['address']:08X}` / {metadata['runtime']['size']} bytes / `{metadata['runtime']['sha256']}`
- live unresolved names: `{strings['live_unresolved']}`
- reserved inert items: {len(strings['reserved_inert_item_ids'])}; reserved non-Dex Species: {len(strings['reserved_non_dex_species_ids'])}
- clean FireRed Rev.0→stage 24 BPS exact: {metadata['release_patch_round_trip']['exact']}

検証済みstage 23を再利用し、全stage再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs, metadata = _build_stage(root)
    repeated, repeated_metadata = _build_stage(root)
    if outputs != repeated or metadata != repeated_metadata:
        _fail("battle UI build is not byte deterministic")
    rom = outputs[STAGE24.as_posix()]
    ui = _ui_fixture(root, rom, metadata)
    policy = _policy_fixture(root, rom)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(), "status": ui["status"],
        "process_runs": ui["process_runs"], "cache_key": ui["cache"]["key"],
    }
    metadata["policy_regression"] = {
        "path": POLICY_FIXTURE.as_posix(), "status": policy["status"],
        "facility_matrix_cases": policy["facility"]["matrix_cases"],
        "raid_shield_breaks": policy["raid"]["shield_breaks"],
        "cache_key": policy["cache"]["key"],
    }
    metadata["acceptance"] = {
        "normal_and_factory_same_owner": True,
        "effectiveness_and_stellar_match_damage_contract": ui["status"] == "PASS",
        "actual_menu_path_rendered": ui["actual_menu_path"],
        "actual_cursor_effectiveness_rendered": all(
            ui["actual_menu_super"][key]
            for key in (
                "type_entry_seen", "effect_entry_seen", "super_label_seen",
                "controller_stable",
            )
        ) and ui["actual_menu_super"]["palette_group"] == 1,
        "l_move_details_rendered": (
            all(ui["l_move_details"][key] for key in (
                "opened", "accuracy_label", "closed", "pointer_stable"
            ))
            and ui["l_move_details"]["button_mode"] == 1
        ),
        "default_help_guarded_in_battle": (
            all(ui["default_help_guard"][key] for key in (
                "details_opened", "accuracy_label", "closed",
                "pointer_stable", "help_state_idle", "controller_stable",
            ))
            and ui["default_help_guard"]["button_mode"] == 0
            and ui["field_help_forwarded"]
        ),
        "canonical_live_names_resolved": all(
            not values for values in metadata["string_audit"]["live_unresolved"].values()
        ),
        "single_double_trainer_wild_factory_raid_input_return": (
            ui["input_return"] and policy["status"] == "PASS"
        ),
    }
    if not all(metadata["acceptance"].values()):
        _fail("battle UI acceptance failed")
    outputs[STAGE24_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(ui)
    outputs[POLICY_FIXTURE.as_posix()] = _stable(policy)
    outputs[REPORT.as_posix()] = _report(metadata, ui, policy)
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
                f"battle UI build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE24.as_posix()])})"
            )
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                _fail("artifact drift: " + ", ".join(drift))
            print(
                f"battle UI check: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE24.as_posix()])})"
            )
        return 0
    except (
        BattleUIError, OSError, ValueError, KeyError, IndexError,
        StopIteration, subprocess.SubprocessError,
    ) as error:
        print(f"battle UI: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
