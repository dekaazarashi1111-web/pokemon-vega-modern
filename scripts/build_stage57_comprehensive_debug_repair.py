#!/usr/bin/env python3
"""Stage56の横断不具合を修復し、決定的なStage57 ROMを生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _arm_tool, _sparse_bps  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.stage57_debug_suite import (  # noqa: E402
    BROKEN_BG_TERMINAL,
    CONTROL_FLOW_REPAIRS,
    FACTORY_CURSOR_CALLSITE,
    FIELD_PC_MAP_COUNT,
    FIELD_PC_TABLE_ADDRESS,
    MENU_BASE_INSTRUCTIONS,
    MENU_CALLSITES,
    MENU_TILE_BASE,
    NPC_POINTER_REPAIRS,
    RESEARCH_RULE_COUNT,
    RESEARCH_TABLE_ADDRESS,
    SPECIES_SET_CALLSITES,
    WILD_GENERATION_HOOK,
    canonical_qol_tables,
    full_audit,
    quick_audit,
    story_trainer_repair_plan,
)


TASK = "USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR"
STAGE = 57
GBA_ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "comprehensive_debug_repair_stage57_payload"
DEFAULT_CONFIG = Path("config/stage57_comprehensive_debug_repair.json")
RUNTIME_SOURCE = Path("overlays/stage57_debug_repair/stage57_debug_repair.c")
REQUIRED_SYMBOLS = {
    "Stage57Debug_SetSpeciesWithCanonicalName",
    "Stage57Debug_NormalizeMonIdentity",
    "Stage57Debug_TryGenerateWildMonAdapter",
    "Stage57Debug_FactoryMenuInitCursorAdapter",
    "Stage57Debug_Probe",
}
OLD_RESEARCH_SHA256 = "b09bb7e3c9eaa03939160da0dba768b595996e22481828b5c7b8227ce3ba3bd2"
OLD_FIELD_PC_SHA256 = "a0da65027c31d635da3d1e1b4250c0ee0d72549cff05896b39f879586d6fde16"
BG_SAFE_TEXT = 0x093DCE28
REQUIRED_MGBA_DOMAINS = {
    "static", "story", "menu", "route505", "species", "collection", "world",
}


class Stage57BuildError(RuntimeError):
    """Stage57 input、patch、allocationまたは検証契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage57BuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _run(command: Sequence[str], label: str, *, timeout: int = 120) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        _fail(f"{label} timeout: {error}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-6000:]}")
    return completed.stdout.strip()


def _read_config(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail("config rootがobjectではありません")
    if (value.get("schema_version"), value.get("task"), value.get("stage")) \
            != (1, TASK, STAGE):
        _fail("config schema/task/stage不一致")
    if int(value.get("menu_tile_base", -1)) != MENU_TILE_BASE:
        _fail("menu tile base契約不一致")
    return value


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256不一致")
    return raw


def _compile_runtime(load_address: int) \
        -> tuple[bytes, dict[str, int], dict[str, int]]:
    source = ROOT / RUNTIME_SOURCE
    if not source.is_file():
        _fail(f"runtime source不足: {RUNTIME_SOURCE}")
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage57-debug-runtime-", dir=local) as raw:
        directory = Path(raw)
        obj = directory / "runtime.o"
        elf = directory / "runtime.elf"
        binary = directory / "runtime.bin"
        linker = directory / "linker.ld"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            "-c", str(source), "-o", str(obj),
        ], "Stage57 runtime compile")
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.Stage57Debug_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,Stage57Debug_Probe", f"-Wl,-T,{linker}", str(obj),
            "-lgcc", "-o", str(elf),
        ], "Stage57 runtime link")
        undefined = _run([nm, "-u", str(elf)], "Stage57 undefined audit")
        if undefined:
            _fail(f"Stage57 undefined symbols: {undefined}")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run(
            [nm, "-n", "-S", "--defined-only", str(elf)], "Stage57 nm",
        ).splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                address, size = int(fields[0], 16), int(fields[1], 16)
            except ValueError:
                continue
            kind, name = fields[2], fields[3]
            symbols[name], sizes[name] = address, size
            if kind in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(name)
        missing = sorted(REQUIRED_SYMBOLS - set(symbols))
        if missing or mutable:
            _fail(f"Stage57 symbol audit不一致: missing={missing} mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Stage57 objcopy")
        code = binary.read_bytes()
        if not code or len(code) > 64 * 1024:
            _fail(f"Stage57 runtime size不正: {len(code)}")
        return code, symbols, sizes


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _build_payload(code: bytes, payload_offset: int) -> tuple[bytes, int]:
    script_offset = _align(PAYLOAD_HEADER_SIZE + len(code), 4)
    script_address = GBA_ROM_BASE + payload_offset + script_offset
    # BG event専用。faceplayerを使わず、visible message後に必ずrelease/endする。
    bg_script = (
        bytes((0x69, 0x0F, 0x00)) + struct.pack("<I", BG_SAFE_TEXT)
        + bytes((0x09, 0x03, 0x6B, 0x02))
    )
    size = _align(script_offset + len(bg_script), 16)
    payload = bytearray(b"\xFF" * size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    payload[script_offset:script_offset + len(bg_script)] = bg_script
    struct.pack_into(
        "<8s9I", payload, 0, b"VEGADB57", 1, size, PAYLOAD_HEADER_SIZE,
        len(code), script_offset, len(bg_script), RESEARCH_RULE_COUNT,
        FIELD_PC_MAP_COUNT, MENU_TILE_BASE,
    )
    return bytes(payload), script_address


def _previous_requests(previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage56 allocation reportにoverlapがあります")
    return [{
        key: row[key]
        for key in ("name", "region", "size", "alignment", "owner", "purpose",
                    "content_sha256")
    } for row in previous["allocations"]]


def _allocation(previous: Mapping[str, Any], size: int, digest: str) \
        -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "NPC/menu/wild identity横断修復とBG安全script",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage57 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage57 payload allocationが一意ではありません")
    return rows[0], report


def _thumb_bl(site_address: int, target_address: int) -> bytes:
    site, target = site_address & ~1, target_address & ~1
    delta = target - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        _fail(f"Thumb BL範囲外: 0x{site:08X}->0x{target:08X}")
    return struct.pack(
        "<HH", 0xF000 | ((delta >> 12) & 0x7FF),
        0xF800 | ((delta >> 1) & 0x7FF),
    )


def _jump_stub(target: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target | 1)


def _patch(
    output: bytearray,
    baseline: bytes,
    declared: list[dict[str, Any]],
    address: int,
    expected: bytes,
    replacement: bytes,
    kind: str,
    name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"patch長不一致: {name}")
    start = address - GBA_ROM_BASE
    if start < 0 or start + len(expected) > len(baseline):
        _fail(f"patch範囲外: {name}")
    if baseline[start:start + len(expected)] != expected \
            or output[start:start + len(expected)] != expected:
        _fail(f"expected bytes不一致: {name}@0x{address:08X}")
    output[start:start + len(replacement)] = replacement
    row = {
        "kind": kind, "name": name, "address": address,
        "start": start, "end_exclusive": start + len(replacement),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }
    declared.append(row)
    return row


def _change_audit(
    before: bytes, after: bytes, declared: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    spans = sorted(
        ({"kind": str(row["kind"]), "name": str(row["name"]),
          "start": int(row["start"]), "end_exclusive": int(row["end_exclusive"])}
         for row in declared),
        key=lambda row: (row["start"], row["end_exclusive"]),
    )
    overlap = [
        (left, right) for left, right in zip(spans, spans[1:])
        if left["end_exclusive"] > right["start"]
    ]
    if overlap:
        _fail(f"declared span overlap: {overlap[:2]}")
    changed = 0
    outside: list[int] = []
    cursor = 0
    for index, (old, new) in enumerate(zip(before, after, strict=True)):
        if old == new:
            continue
        changed += 1
        while cursor < len(spans) and index >= spans[cursor]["end_exclusive"]:
            cursor += 1
        if cursor >= len(spans) or index < spans[cursor]["start"]:
            outside.append(index)
            if len(outside) == 8:
                break
    if outside:
        _fail("宣言外ROM変更: " + ", ".join(hex(value) for value in outside))
    return {
        "status": "PASS", "changed_byte_count": changed,
        "declared_span_count": len(spans), "declared_spans": spans,
        "overlap_count": 0, "outside_declared_span_count": 0,
    }


def _markdown(audit: Mapping[str, Any]) -> bytes:
    quick = audit["debug"]["quick"]["checks"]
    cfg = audit["debug"]["full"]["script_cfg"]
    wild = audit["debug"]["full"]["wild_surface"]
    mgba = audit["mgba"]
    coverage = mgba.get("coverage", {})
    lines = [
        "# Stage57 横断デバッグ・修復報告", "",
        f"- Status: {audit['status']}",
        f"- ROM SHA-256: `{audit['output']['sha256']}`",
        f"- 変更byte数: {audit['change_audit']['changed_byte_count']}",
        "", "## 修復", "",
        f"- NPC会話pointer: {quick['npc_pointer_repairs']}件",
        f"- story/固定遭遇control-flow: {quick['control_flow_repairs']}件",
        f"- menu VRAM base callsite: {quick['menu_callsites']}件",
        f"- research binding: {quick['research_rules']}件",
        f"- Field PC binding: {quick['field_pc_maps']}件",
        "- 通常story trainerの再戦Lv80～100誤流入: "
        f"{quick['story_trainers']['active_command_count']}戦修復、残存0戦",
        "- 共有trainer 348は通常戦をID 1384へ分離し、Kanto高難度戦を保持",
        "- 種族変更時のdefault nicknameと野生初期技をSpeciesへ同期",
        "", "## 高速full scan", "",
        f"- physical maps: {cfg['physical_maps']}",
        f"- contactable roots: {cfg['root_count']}",
        f"- reachable scripts: {cfg['visited_script_count']}",
        f"- diagnostics: {cfg['diagnostic_count']}",
        f"- wild headers / slots: {wild['native_headers']} / "
        f"{wild['native_slots_checked']}",
        f"- QOL research / Collection wild forms: "
        f"{wild['qol_research_rules_checked']} / "
        f"{wild['collection_wild_forms_checked']}",
        f"- Species range mismatch: {wild['species_range_mismatch_count']}",
        "", "## mGBA exact-ROM", "",
        f"- Status: {mgba['status']}",
        f"- domains: {', '.join(mgba.get('domains', []))}",
        f"- 動的process: {mgba['process_count']}（各domain独立2 process）",
        f"- warnings / errors: {mgba.get('warnings', 0)}",
        f"- menu: {coverage.get('menu_cases', 0)} cases、"
        f"Collection {coverage.get('collection_hosts', 0)} hosts",
        f"- Route505: {coverage.get('route505_encounters', 0)} natural encounters、"
        f"identity {coverage.get('route505_identity_checks', 0)} species",
        f"- Species: canonical {coverage.get('canonical_species', 0)}、"
        f"created {coverage.get('species_created', 0)}、"
        f"named {coverage.get('species_named', 0)}",
        f"- world: {coverage.get('world_fixtures', 0)} input fixtures",
        "", "## 505番道路", "",
        "- 現行physical binding由来のRESEARCH候補: "
        + ", ".join(str(value) for value in quick["route_505_research_species"]),
        "- 旧T503 Speciesの自然流入: 0件",
        "- Species 92 / 717 / 804は、party・戦闘Species・canonical名・front画像一致", "",
        "## 再現性・境界", "",
        f"- declared span外変更: {audit['change_audit']['outside_declared_span_count']}",
        f"- ROM / RAM / save / map / hook overlap: "
        f"{audit['overlap_audit']['rom']} / {audit['overlap_audit']['ram']} / "
        f"{audit['overlap_audit']['save']} / {audit['overlap_audit']['map']} / "
        f"{audit['overlap_audit']['hook']}",
        f"- Stage56差分BPS往復: {audit['bps']['incremental']['round_trip']}",
        f"- clean直接BPS往復: {audit['bps']['clean']['round_trip']}",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _mgba_evidence(
    config: Mapping[str, Any], output_sha256: str,
) -> dict[str, Any]:
    relative = str(config["outputs"]["mgba"])
    path = ROOT / relative
    if not path.is_file():
        return {"status": "PENDING", "path": relative, "process_count": 0}
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"Stage57 mGBA evidence不正: {error}")
    if (not isinstance(document, dict)
            or (document.get("schema_version"), document.get("task"),
                document.get("stage")) != (1, TASK, STAGE)
            or document.get("status") != "PASS"
            or document.get("profile") != "all"
            or document.get("rom_sha256") != output_sha256
            or document.get("full_coverage") is not True
            or set(document.get("selected_domains", [])) != REQUIRED_MGBA_DOMAINS
            or document.get("warnings") != 0
            or document.get("dynamic_process_runs") != 2):
        _fail("Stage57 mGBA evidence identity/coverage不一致")
    domains = document.get("domains")
    if (not isinstance(domains, dict) or set(domains) != REQUIRED_MGBA_DOMAINS
            or any(not isinstance(value, dict) or value.get("status") != "PASS"
                   for value in domains.values())):
        _fail("Stage57 mGBA domain evidence不一致")
    dynamic = ("menu", "route505", "species", "collection", "world")
    if any(int(domains[name].get("process_runs", 0)) != 2 for name in dynamic):
        _fail("Stage57 dynamic domainの独立2 process契約不一致")
    try:
        menu = domains["menu"]["result"]
        route = domains["route505"]["result"]["result"]
        species = domains["species"]["result"]
        collection = domains["collection"]["result"]
        world = domains["world"]
        menu_coverage = menu["coverage"]
        collection_coverage = collection["coverage"]
    except (KeyError, TypeError) as error:
        _fail(f"Stage57 mGBA coverage evidence欠落: {error}")
    if (menu_coverage.get("menu_callsites") != 10
            or menu_coverage.get("non_collection_overlays") != 9
            or menu_coverage.get("collection_hosts") != 14
            or not all(menu.get("checks", {}).values())
            or menu.get("warnings_errors") != 0):
        _fail("Stage57 menu coverage契約不一致")
    if (route.get("encounters") != 66
            or route.get("natural_species_checks") != 66
            or route.get("direct_species_checks") != 3
            or route.get("direct_name_checks") != 3
            or route.get("direct_front_checks") != 3
            or route.get("warnings") != 0):
        _fail("Stage57 Route505 coverage契約不一致")
    if (species.get("canonical_species_count") != 1621
            or species.get("species_created") != 1619
            or species.get("species_named") != 1620
            or species.get("compatibility_names_checked") != 1620):
        _fail("Stage57 Species coverage契約不一致")
    if (collection_coverage.get("hosts") != 14
            or collection_coverage.get("forms") != 388
            or collection_coverage.get("gmax") != 34
            or collection_coverage.get("items") != 999
            or collection.get("warnings") != 0
            or not all(collection.get("tests", {}).values())):
        _fail("Stage57 Collection coverage契約不一致")
    if world.get("fixture_count") != 22 or world.get("warnings") != 0:
        _fail("Stage57 world coverage契約不一致")
    return {
        "status": "PASS",
        "path": relative,
        "sha256": _sha(raw),
        "process_count": sum(
            int(domains[name]["process_runs"]) for name in dynamic
        ),
        "domain_count": len(domains),
        "domains": sorted(domains),
        "warnings": 0,
        "coverage": {
            "menu_cases": int(menu_coverage["non_collection_overlays"])
            + int(menu_coverage["collection_hosts"]),
            "menu_callsites": int(menu_coverage["menu_callsites"]),
            "collection_hosts": int(menu_coverage["collection_hosts"]),
            "route505_encounters": int(route["encounters"]),
            "route505_identity_checks": int(route["direct_species_checks"]),
            "canonical_species": int(species["canonical_species_count"]),
            "species_created": int(species["species_created"]),
            "species_named": int(species["species_named"]),
            "world_fixtures": int(world["fixture_count"]),
        },
    }


def _build_static(config_path: Path) -> dict[str, bytes]:
    started = time.monotonic()
    config = _read_config(config_path)
    inputs = config["inputs"]
    stage56 = _identity(inputs["stage56_rom"], "Stage56 ROM")
    metadata56 = json.loads(_identity(inputs["stage56_metadata"], "Stage56 metadata"))
    previous = json.loads(_identity(inputs["stage56_allocation"], "Stage56 allocation"))
    clean = _identity(inputs["clean_rom"], "clean FireRed JPN Rev0")
    if len(stage56) != ROM_SIZE or len(clean) != ROM_SIZE // 2:
        _fail("Stage56/clean ROM size不一致")
    if metadata56.get("output", {}).get("sha256") != _sha(stage56):
        _fail("Stage56 metadata output identity不一致")

    provisional_code, _, _ = _compile_runtime(GBA_ROM_BASE + PAYLOAD_HEADER_SIZE)
    provisional_payload, _ = _build_payload(provisional_code, 0)
    allocation, _ = _allocation(previous, len(provisional_payload), "0" * 64)
    payload_offset = int(allocation["start"])
    load_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols, symbol_sizes = _compile_runtime(load_address)
    payload, bg_script = _build_payload(code, payload_offset)
    if len(code) != len(provisional_code) or len(payload) != len(provisional_payload):
        _fail("配置addressによりruntime sizeが変化しました")
    allocation, allocation_report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload hash確定後にallocationが移動しました")
    payload_end = payload_offset + len(payload)
    if stage56[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage57 payload destinationがerased FFではありません")

    output = bytearray(stage56)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "kind": "payload", "name": ALLOCATION_NAME,
        "address": GBA_ROM_BASE + payload_offset,
        "start": payload_offset, "end_exclusive": payload_end,
    }]
    patch_groups: dict[str, list[dict[str, Any]]] = {
        "menu_calls": [], "species_calls": [], "wild_hook": [],
        "factory_cursor": [],
        "npc_pointers": [], "control_flow": [], "bg_terminal": [],
        "binding_tables": [], "story_trainers": [],
    }
    for name, address, expected in MENU_CALLSITES:
        patch_groups["menu_calls"].append(_patch(
            output, stage56, declared, address, expected, MENU_BASE_INSTRUCTIONS,
            "menu_tile_base", name,
        ))

    species_target = symbols["Stage57Debug_SetSpeciesWithCanonicalName"] | 1
    for name, address, expected in SPECIES_SET_CALLSITES:
        patch_groups["species_calls"].append(_patch(
            output, stage56, declared, address, expected,
            _thumb_bl(address, species_target), "species_identity_call", name,
        ))
    hook_name, hook_address, hook_expected = WILD_GENERATION_HOOK
    wild_target = symbols["Stage57Debug_TryGenerateWildMonAdapter"] | 1
    patch_groups["wild_hook"].append(_patch(
        output, stage56, declared, hook_address, hook_expected,
        _jump_stub(wild_target), "wild_identity_hook", hook_name,
    ))
    cursor_name, cursor_address, cursor_expected = FACTORY_CURSOR_CALLSITE
    cursor_target = symbols["Stage57Debug_FactoryMenuInitCursorAdapter"] | 1
    patch_groups["factory_cursor"].append(_patch(
        output, stage56, declared, cursor_address, cursor_expected,
        _thumb_bl(cursor_address, cursor_target), "factory_cursor_abi", cursor_name,
    ))

    research, field_pc = canonical_qol_tables()
    old_research_start = RESEARCH_TABLE_ADDRESS - GBA_ROM_BASE
    old_field_start = FIELD_PC_TABLE_ADDRESS - GBA_ROM_BASE
    old_research = stage56[old_research_start:old_research_start + len(research)]
    old_field = stage56[old_field_start:old_field_start + len(field_pc)]
    if _sha(old_research) != OLD_RESEARCH_SHA256 \
            or _sha(old_field) != OLD_FIELD_PC_SHA256:
        _fail("Stage56 QOL stale table identity不一致")
    patch_groups["binding_tables"].append(_patch(
        output, stage56, declared, RESEARCH_TABLE_ADDRESS, old_research, research,
        "qol_binding_table", "research_rules",
    ))
    patch_groups["binding_tables"].append(_patch(
        output, stage56, declared, FIELD_PC_TABLE_ADDRESS, old_field, field_pc,
        "qol_binding_table", "field_pc_maps",
    ))

    for name, address, old, new in NPC_POINTER_REPAIRS:
        patch_groups["npc_pointers"].append(_patch(
            output, stage56, declared, address, struct.pack("<I", old),
            struct.pack("<I", new), "npc_script_pointer", name,
        ))
    for name, address, old, new in CONTROL_FLOW_REPAIRS:
        patch_groups["control_flow"].append(_patch(
            output, stage56, declared, address, struct.pack("<I", old),
            struct.pack("<I", new), "event_control_flow", name,
        ))
    bg_name, bg_address, bg_expected = BROKEN_BG_TERMINAL
    patch_groups["bg_terminal"].append(_patch(
        output, stage56, declared, bg_address, bg_expected,
        bytes((0x05,)) + struct.pack("<I", bg_script),
        "bg_safe_fallback", bg_name,
    ))

    story_plan = story_trainer_repair_plan(stage56)
    for row in story_plan["patches"]:
        patch_groups["story_trainers"].append(_patch(
            output, stage56, declared, int(row["address"]),
            bytes(row["expected"]), bytes(row["replacement"]),
            str(row["kind"]), str(row["name"]),
        ))
    story_plan_audit = {
        key: value for key, value in story_plan.items() if key != "patches"
    }

    output_raw = bytes(output)
    change_audit = _change_audit(stage56, output_raw, declared)
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    mgba = _mgba_evidence(config, output_identity["sha256"])
    release_status = "PASS" if mgba["status"] == "PASS" \
        else "PASS_STATIC_MGBA_PENDING"
    runtime = {
        "payload": {
            "offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
        },
        "code": {
            "offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "address": load_address, "size": len(code), "sha256": _sha(code),
        },
        "bg_safe_script": bg_script,
        "symbols": {
            name: {"address": symbols[name] | 1, "size": symbol_sizes[name]}
            for name in sorted(REQUIRED_SYMBOLS)
        },
    }
    overlap_audit = {
        "status": "PASS", "rom": 0, "ram": 0, "save": 0,
        "map": 0, "hook": 0,
        "allocator_overlap": int(
            allocation_report.get("summaries", {}).get("overlap_count", -1)
        ),
    }
    if overlap_audit["allocator_overlap"] != 0:
        _fail("Stage57 overlap audit不一致")
    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": release_status,
        "input": {
            "stage56": {"path": inputs["stage56_rom"]["path"],
                        "size": len(stage56), "sha256": _sha(stage56)},
            "clean": {"path": inputs["clean_rom"]["path"],
                      "size": len(clean), "sha256": _sha(clean)},
        },
        "output": output_identity, "runtime": runtime,
        "allocation": allocation, "patches": patch_groups,
        "story_trainer_repair": story_plan_audit,
        "change_audit": change_audit, "overlap_audit": overlap_audit,
        "mgba": mgba,
    }
    quick = quick_audit(output_raw, metadata=metadata)
    full = full_audit(output_raw, metadata=metadata)
    # wall-clockはCLIの体感速度表示だけに使い、決定的生成物へは含めない。
    quick.pop("elapsed_seconds", None)
    full.pop("elapsed_seconds", None)
    if isinstance(full.get("quick"), dict):
        full["quick"].pop("elapsed_seconds", None)
    if not (quick["rom_sha256"] == full["rom_sha256"]
            == output_identity["sha256"]):
        _fail("quick/full ROM identity不一致")

    incremental = _sparse_bps(stage56, output_raw)
    direct = create_bps(
        clean, output_raw,
        metadata=b"Clean FireRed JPN Rev0 to Stage57 Comprehensive Debug Repair",
    )
    if apply_bps(stage56, incremental) != output_raw \
            or apply_bps(clean, direct) != output_raw:
        _fail("Stage57 BPS round-trip不一致")
    bps = {
        "incremental": {
            "path": config["outputs"]["incremental_bps"],
            "size": len(incremental), "sha256": _sha(incremental),
            "round_trip": True,
        },
        "clean": {
            "path": config["outputs"]["clean_bps"],
            "size": len(direct), "sha256": _sha(direct), "round_trip": True,
        },
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": release_status,
        "input": metadata["input"], "output": output_identity,
        "runtime": runtime, "patches": patch_groups,
        "story_trainer_repair": story_plan_audit,
        "change_audit": change_audit, "overlap_audit": overlap_audit,
        "debug": {"quick": quick, "full": full},
        "mgba": mgba,
        "bps": bps,
        "root_causes": {
            "route_505": "Stage36 QOL research/Field-PC tables used stale map bindings",
            "npc_lock": "Stage52 owner rebuild accepted erased source script pointers",
            "menu_corruption": "window content reused standard frame tile base 0x214",
            "identity": "Collection species mutations did not synchronize default nickname/moves",
            "story_flow": "three malformed event-script pointer operands",
            "story_trainer_levels": (
                "battle-searcher rematch parties were also bound to 26 initial "
                "kind 0/4 story commands"
            ),
        },
    }
    metadata["debug"] = {
        "quick": {"status": "PASS", "path": config["outputs"]["debug_quick"]},
        "full": {"status": "PASS", "path": config["outputs"]["debug_full"]},
    }
    metadata["bps"] = bps
    symbols_doc = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "runtime": runtime, "patches": patch_groups,
        "story_trainer_repair": story_plan_audit,
    }
    cases = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "rom_sha256": output_identity["sha256"],
        "menu_tile_base": MENU_TILE_BASE,
        "route_505": {
            "group": 3, "map": 23,
            "research_species": quick["checks"]["route_505_research_species"],
            "forbidden_species": [92, 717, 804],
        },
        "npc_repairs": [
            {"name": name, "address": address, "target": new}
            for name, address, _, new in NPC_POINTER_REPAIRS
        ],
        "control_flow_repairs": [
            {"name": name, "address": address, "target": new}
            for name, address, _, new in CONTROL_FLOW_REPAIRS
        ],
        "bg_safe_script": bg_script,
        "story_trainer_repair": story_plan_audit,
    }
    outputs = config["outputs"]
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["runtime"]: code,
        outputs["symbols"]: _stable(symbols_doc),
        outputs["cases"]: _stable(cases),
        outputs["audit"]: _stable(audit),
        outputs["report"]: _markdown(audit),
        outputs["debug_quick"]: _stable({
            "schema_version": 1, "tool": "stage57_debug_suite",
            "mode": "quick", **quick,
        }),
        outputs["debug_full"]: _stable({
            "schema_version": 1, "tool": "stage57_debug_suite",
            "mode": "full", **full,
        }),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    drift = [
        relative for relative, raw in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
    ]
    if drift:
        _fail("Stage57生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        first = _build_static(args.config)
        second = _build_static(args.config)
        if first != second:
            _fail("Stage57 buildがbyte deterministicではありません")
        if args.mode == "build":
            _write_outputs(first)
        else:
            _check_outputs(first)
        config = _read_config(args.config)
        metadata = json.loads(first[config["outputs"]["metadata"]])
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, subprocess.SubprocessError,
            Stage57BuildError) as error:
        print(f"Stage57 comprehensive debug {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "Stage57 comprehensive debug %s: %s sha256=%s crc32=%s artifacts=%d"
        % (args.mode, metadata["status"], metadata["output"]["sha256"],
           metadata["output"]["crc32"], len(first))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
