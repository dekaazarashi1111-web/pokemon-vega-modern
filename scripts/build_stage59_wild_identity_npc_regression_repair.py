#!/usr/bin/env python3
"""Build/check Stage59 wild-identity guard and regression repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _arm_tool, _sparse_bps  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.stage57_debug_suite import quick_audit  # noqa: E402

TASK = "USER-20260829-STAGE59-WILD-IDENTITY-NPC-REGRESSION-REPAIR"
STAGE = 59
GBA_ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "wild_identity_npc_regression_repair_stage59_payload"
DEFAULT_CONFIG = Path("config/stage59_wild_identity_npc_regression_repair.json")
REQUIRED_SYMBOLS = {
    "Stage59Repair_NormalizeEnemyPartyIdentity",
    "Stage59Repair_TryGenerateWildMonAdapter",
    "Stage59Repair_GenerateFishingEncounterAdapter",
    "Stage59Repair_TryHiddenEncounterAdapter",
    "Stage59Repair_Probe",
}


class Stage59BuildError(RuntimeError):
    """Stage59 input, allocation, patch, or reproducibility contract failure."""


def _fail(message: str) -> NoReturn:
    raise Stage59BuildError(message)


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
        _fail("config root is not an object")
    if (value.get("schema_version"), value.get("task"), value.get("stage")) \
            != (1, TASK, STAGE):
        _fail("config schema/task/stage differs")
    if len(value.get("hooks", [])) != 3:
        _fail("exactly three wild entry hooks are required")
    return value


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _compile_runtime(source: Path, load_address: int) \
        -> tuple[bytes, dict[str, int], dict[str, int], str]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage59-identity-runtime-", dir=local) as raw:
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
            "-c", str(ROOT / source), "-o", str(obj),
        ], "Stage59 runtime compile")
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.Stage59Repair_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,Stage59Repair_Probe", f"-Wl,-T,{linker}", str(obj),
            "-lgcc", "-o", str(elf),
        ], "Stage59 runtime link")
        undefined = _run([nm, "-u", str(elf)], "Stage59 undefined audit")
        if undefined:
            _fail(f"Stage59 undefined symbols: {undefined}")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        nm_text = _run(
            [nm, "-n", "-S", "--defined-only", str(elf)], "Stage59 nm",
        )
        for line in nm_text.splitlines():
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
            _fail(f"Stage59 symbol audit differs: missing={missing} mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Stage59 objcopy")
        code = binary.read_bytes()
        if not code or len(code) > 16 * 1024:
            _fail(f"Stage59 runtime size is invalid: {len(code)}")
        return code, symbols, sizes, nm_text


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _build_payload(code: bytes) -> bytes:
    size = _align(PAYLOAD_HEADER_SIZE + len(code), 16)
    payload = bytearray(b"\xFF" * size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    struct.pack_into(
        "<8s6I", payload, 0, b"VEGAID59", 1, size,
        PAYLOAD_HEADER_SIZE, len(code), 3, 1621,
    )
    return bytes(payload)


def _previous_requests(previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage58 allocation report contains overlap")
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
        "purpose": "all wild-entry canonical-name guard and regression repair",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage59 allocator overlap")
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1:
        _fail("Stage59 payload allocation is not unique")
    return rows[0], report


def _jump_stub(target: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target | 1)


def _patch(output: bytearray, baseline: bytes, declared: list[dict[str, Any]],
           address: int, expected: bytes, replacement: bytes,
           kind: str, name: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"patch length differs: {name}")
    start = address - GBA_ROM_BASE
    if start < 0 or start + len(expected) > len(baseline):
        _fail(f"patch range is invalid: {name}")
    if baseline[start:start + len(expected)] != expected \
            or output[start:start + len(expected)] != expected:
        _fail(f"expected bytes differ: {name}@0x{address:08X}")
    output[start:start + len(replacement)] = replacement
    row = {
        "kind": kind, "name": name, "address": address,
        "start": start, "end_exclusive": start + len(replacement),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }
    declared.append(row)
    return row


def _changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    if len(before) != len(after):
        _fail("change audit size differs")
    spans: list[dict[str, int]] = []
    index = 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        spans.append({"start": start, "end_exclusive": index, "size": index - start})
    return spans


def _change_audit(before: bytes, after: bytes,
                  declared: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spans = _changed_spans(before, after)
    ranges = sorted((int(row["start"]), int(row["end_exclusive"])) for row in declared)
    overlaps = sum(1 for left, right in zip(ranges, ranges[1:]) if left[1] > right[0])
    outside = [row for row in spans if not any(
        start <= row["start"] and row["end_exclusive"] <= end
        for start, end in ranges
    )]
    if overlaps or outside:
        _fail(f"Stage59 declared-span audit failed overlap={overlaps} outside={outside[:4]}")
    return {
        "changed_byte_count": sum(row["size"] for row in spans),
        "changed_span_count": len(spans),
        "declared_span_count": len(declared),
        "outside_declared_span_count": len(outside),
        "overlap_count": overlaps,
        "spans": spans,
    }


def _inherited_debug_contract(stage58: bytes) -> dict[str, Any]:
    result = quick_audit(stage58, metadata=None)
    if result.get("status") != "PASS":
        _fail("Stage58 inherited debug quick audit did not pass")
    checks = result["checks"]
    return {
        "status": "PASS",
        "rom_sha256": result["rom_sha256"],
        "menu_callsites": int(checks["menu_callsites"]),
        "npc_pointer_repairs": int(checks["npc_pointer_repairs"]),
        "control_flow_repairs": int(checks["control_flow_repairs"]),
        "research_rules": int(checks["research_rules"]),
        "field_pc_maps": int(checks["field_pc_maps"]),
        "story_trainers_status": checks["story_trainers"]["status"],
    }


def _markdown(audit: Mapping[str, Any]) -> bytes:
    output = audit["output"]
    guard = audit["wild_identity_guard"]
    inherited = audit["inherited_debug"]
    lines = [
        "# Pokémon Vega Stage59 wild identity / NPC regression repair", "",
        "## 変更", "",
        "- 地上・水上、釣り、隠し／スキャナー遭遇の3入口を共通のcanonical名同期へ接続。",
        "- 地上側の既存Stage57初期技同期は維持。釣り・隠し側は特殊技構成を保持するため名前だけを同期。",
        "- Collection Supply内の3か所のSpecies書換えは、Stage57の原子的Species＋default nicknameラッパー接続を継承確認。",
        "- 自然遭遇と全方式回帰テストへcanonical nickname判定を追加。", "",
        "## 静的検証", "",
        f"- Stage59 ROM SHA-256: `{output['sha256']}`",
        f"- 3入口hook: {guard['hook_count']}/3",
        f"- Collection atomic Species callsite: {guard['atomic_species_call_count']}/3",
        f"- declared外変更: {audit['change_audit']['outside_declared_span_count']}",
        f"- allocation overlap: {audit['allocator']['overlap_count']}",
        f"- incremental / clean BPS round-trip: {audit['bps']['incremental']['round_trip']} / {audit['bps']['clean']['round_trip']}",
        f"- Stage58継承 menu/NPC/control-flow: {inherited['menu_callsites']} / {inherited['npc_pointer_repairs']} / {inherited['control_flow_repairs']}", "",
        "## 動的検証", "",
        "`make stage59-mgba-all` が全1620 Species名、地上・釣り・隠し193生成、Route505自然歩行・逃走、fresh/QA-saveメニュー回帰を実行します。自然遭遇数はrunner引数で1〜66へ変更できます。",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_static(config_path: Path) -> dict[str, bytes]:
    config = _read_config(config_path)
    inputs = config["inputs"]
    stage58 = _identity(inputs["stage58_rom"], "Stage58 ROM")
    metadata58_raw = _identity(inputs["stage58_metadata"], "Stage58 metadata")
    metadata58 = json.loads(metadata58_raw)
    previous = json.loads(_identity(inputs["stage58_allocation"], "Stage58 allocation"))
    clean = _identity(inputs["clean_rom"], "clean FireRed JPN Rev0")
    if len(stage58) != ROM_SIZE or len(clean) != ROM_SIZE // 2:
        _fail("Stage58/clean ROM size differs")
    if metadata58.get("output", {}).get("sha256") != _sha(stage58):
        _fail("Stage58 metadata output identity differs")
    inherited = _inherited_debug_contract(stage58)

    source = Path(str(config["runtime_source"]))
    provisional_code, _, _, _ = _compile_runtime(source, 0x09E00000)
    provisional_payload = _build_payload(provisional_code)
    allocation, _ = _allocation(previous, len(provisional_payload), "0" * 64)
    payload_offset = int(allocation["start"])
    load_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols, symbol_sizes, nm_text = _compile_runtime(source, load_address)
    payload = _build_payload(code)
    if len(code) != len(provisional_code) or len(payload) != len(provisional_payload):
        _fail("runtime size changed with placement address")
    allocation, allocation_report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload allocation moved after content hash resolution")
    payload_end = payload_offset + len(payload)
    if stage58[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage59 payload destination is not erased FF")

    output = bytearray(stage58)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "kind": "payload", "name": ALLOCATION_NAME,
        "address": GBA_ROM_BASE + payload_offset,
        "start": payload_offset, "end_exclusive": payload_end,
    }]
    hook_rows: list[dict[str, Any]] = []
    for row in config["hooks"]:
        symbol = str(row["symbol"])
        if symbol not in symbols:
            _fail(f"hook symbol missing: {symbol}")
        hook_rows.append(_patch(
            output, stage58, declared, int(str(row["address"]), 0),
            bytes.fromhex(str(row["expected"])), _jump_stub(symbols[symbol]),
            "wild_identity_hook", str(row["name"]),
        ))

    atomic_rows: list[dict[str, Any]] = []
    for row in config["atomic_species_calls"]:
        address = int(str(row["address"]), 0)
        expected = bytes.fromhex(str(row["expected"]))
        start = address - GBA_ROM_BASE
        actual = bytes(output[start:start + len(expected)])
        if actual != expected:
            _fail(f"inherited atomic Species call differs: {row['name']}")
        atomic_rows.append({
            "name": row["name"], "address": address,
            "bytes": actual.hex(), "status": "PASS",
        })

    output_raw = bytes(output)
    change = _change_audit(stage58, output_raw, declared)
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    incremental = _sparse_bps(stage58, output_raw)
    direct = create_bps(
        clean, output_raw,
        metadata=b"Clean FireRed JPN Rev0 to Stage59 Wild Identity NPC Regression Repair",
    )
    if apply_bps(stage58, incremental) != output_raw:
        _fail("Stage59 incremental BPS round-trip differs")
    if apply_bps(clean, direct) != output_raw:
        _fail("Stage59 clean BPS round-trip differs")
    bps = {
        "incremental": {
            "path": config["outputs"]["incremental_bps"],
            "size": len(incremental), "sha256": _sha(incremental),
            "round_trip": True,
        },
        "clean": {
            "path": config["outputs"]["clean_bps"],
            "size": len(direct), "sha256": _sha(direct),
            "round_trip": True,
        },
    }
    runtime = {
        "source": str(source),
        "load_address": load_address,
        "code_size": len(code),
        "payload_address": GBA_ROM_BASE + payload_offset,
        "payload_size": len(payload),
        "payload_sha256": _sha(payload),
        "symbols": symbols,
        "symbol_sizes": symbol_sizes,
        "nm_sha256": _sha((nm_text + "\n").encode()),
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "input": {
            "stage58_rom_sha256": _sha(stage58),
            "stage58_metadata_sha256": _sha(metadata58_raw),
            "clean_rom_sha256": _sha(clean),
        },
        "output": output_identity,
        "root_cause": {
            "wild_identity": (
                "Collection post-generation Species replacement was guarded only at "
                "the land/water outer hook, while fishing and hidden entrypoints had no "
                "shared canonical-name postcondition."
            ),
            "test_gap": (
                "Natural Route505 assertions checked Species and level but did not "
                "compare party/battle nickname with the canonical Species name."
            ),
            "npc_diagnostic": (
                "The lightweight bundle inspected an erased Stage56 save and failed to "
                "resolve script labels, so its 1588 unresolved-label result is not a "
                "valid runtime defect count."
            ),
        },
        "wild_identity_guard": {
            "hook_count": len(hook_rows), "hooks": hook_rows,
            "atomic_species_call_count": len(atomic_rows),
            "atomic_species_calls": atomic_rows,
            "move_policy": {
                "land_water": "existing Stage57 canonical name + initial moves, then name guard",
                "fishing": "canonical name only; preserve authored research-profile moves",
                "hidden": "canonical name only; preserve authored research-profile moves",
            },
        },
        "runtime": runtime,
        "inherited_debug": inherited,
        "change_audit": change,
        "allocator": {
            "allocation": allocation,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "bps": bps,
        "dynamic_gate": {
            "report": config["outputs"]["mgba"],
            "required_domains": [
                "identity_guard_1620_species", "all_wild_methods",
                "route505_natural_identity", "menu_fresh_save", "menu_qa_save",
            ],
        },
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "input": audit["input"], "output": output_identity,
        "payload": runtime, "patches": hook_rows,
        "inherited_debug": inherited, "change_audit": change,
        "allocator": audit["allocator"], "bps": bps,
        "dynamic_gate": audit["dynamic_gate"],
    }
    outputs = config["outputs"]
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["runtime"]: payload,
        outputs["symbols"]: _stable({
            "schema_version": 1, "task": TASK, "stage": STAGE,
            "runtime": runtime,
        }),
        outputs["audit"]: _stable(audit),
        outputs["report"]: _markdown(audit),
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
    drift = [relative for relative, raw in outputs.items()
             if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw]
    if drift:
        _fail("Stage59 generated artifact drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        first = _build_static(args.config)
        second = _build_static(args.config)
        if first != second:
            _fail("Stage59 build is not byte deterministic")
        config = _read_config(args.config)
        metadata = json.loads(first[config["outputs"]["metadata"]])
        if args.mode == "build":
            _write_outputs(first)
        else:
            _check_outputs(first)
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, Stage59BuildError) as error:
        print(f"Stage59 wild identity/NPC regression {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    print(
        "Stage59 wild identity/NPC regression %s: %s sha256=%s crc32=%s artifacts=%d"
        % (args.mode, metadata["status"], metadata["output"]["sha256"],
           metadata["output"]["crc32"], len(first))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
