#!/usr/bin/env python3
"""Build/check the global Stage60 ChangeKit ownership repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import _arm_tool, _sparse_bps  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402

TASK = "USER-20260829-STAGE59-WILD-SPECIES-ROOT-REPAIR"
GBA_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
HEADER_SIZE = 0x100
ALLOCATION_NAME = "wild_species_root_repair_stage60_payload"
CONFIG = Path("config/stage60_wild_species_root_repair.json")
REQUIRED = {
    "Stage60WildSpeciesRootRepair_BuildTrainerPartySetup",
    "Stage60WildSpeciesRootRepair_ConfigureTrainerBattle",
    "Stage60WildSpeciesRootRepair_PolicyEnd",
    "Stage60WildSpeciesRootRepair_Probe",
}


class BuildError(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def run(command: Sequence[str], label: str) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise BuildError(f"{label}: {detail[-6000:]}")
    return completed.stdout.strip()


def identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    raw = path.read_bytes()
    if len(raw) != int(contract.get("size", len(raw))) \
            or sha(raw) != str(contract["sha256"]):
        raise BuildError(f"{label} identity differs")
    return raw


def compile_runtime(source: Path, address: int) \
        -> tuple[bytes, dict[str, int], str]:
    gcc = _arm_tool(ROOT, "arm-none-eabi-gcc")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage60-wild-root-", dir=ROOT / ".local") as tmp:
        directory = Path(tmp)
        obj, elf, binary = (directory / "runtime.o", directory / "runtime.elf",
                            directory / "runtime.bin")
        linker = directory / "linker.ld"
        run([
            gcc, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common", "-c",
            str(ROOT / source), "-o", str(obj),
        ], "runtime compile")
        linker.write_text(
            "SECTIONS\n{\n" f"  . = 0x{address:08X};\n"
            "  .text : { KEEP(*(.text.Stage60WildSpeciesRootRepair_*)) "
            "*(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n}\n", encoding="ascii",
        )
        run([
            gcc, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,Stage60WildSpeciesRootRepair_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "runtime link")
        if run([nm, "-u", str(elf)], "undefined audit"):
            raise BuildError("runtime has undefined symbols")
        nm_text = run([nm, "-n", "-S", "--defined-only", str(elf)], "nm")
        symbols: dict[str, int] = {}
        mutable: list[str] = []
        for line in nm_text.splitlines():
            fields = line.split()
            if len(fields) >= 4:
                symbols[fields[3]] = int(fields[0], 16)
                if fields[2] in {"B", "b", "C", "c", "D", "d", "G", "g"}:
                    mutable.append(fields[3])
        if REQUIRED - set(symbols) or mutable:
            raise BuildError(f"symbol audit differs missing={REQUIRED-set(symbols)} mutable={mutable}")
        run([objcopy, "-O", "binary", str(elf), str(binary)], "objcopy")
        return binary.read_bytes(), symbols, nm_text


def previous_requests(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    if report["summaries"]["overlap_count"]:
        raise BuildError("input allocation overlaps")
    keys = ("name", "region", "size", "alignment", "owner", "purpose",
            "content_sha256")
    return [{key: row[key] for key in keys} for row in report["allocations"]]


def allocate(previous: Mapping[str, Any], size: int, digest: str) \
        -> tuple[dict[str, Any], dict[str, Any]]:
    requests = previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules", "size": size,
        "alignment": 16, "owner": TASK,
        "purpose": "global BuildTrainerParty ChangeKit ownership gate",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    rows = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(rows) != 1 or report["summaries"]["overlap_count"]:
        raise BuildError("output allocation invalid")
    return rows[0], report


def payload(code: bytes) -> bytes:
    size = (HEADER_SIZE + len(code) + 15) & ~15
    raw = bytearray(b"\xFF" * size)
    raw[HEADER_SIZE:HEADER_SIZE + len(code)] = code
    struct.pack_into("<8s5I", raw, 0, b"VEGAWS60", 1, size, HEADER_SIZE,
                     len(code), 1)
    return bytes(raw)


def jump_stub(target: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target | 1)


def thumb_bl(site: int, target: int) -> bytes:
    delta = (target & ~1) - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        raise BuildError("Thumb BL target out of range")
    return struct.pack("<HH", 0xF000 | ((delta >> 12) & 0x7FF),
                       0xF800 | ((delta >> 1) & 0x7FF))


def changed_spans(before: bytes, after: bytes) -> list[dict[str, int]]:
    spans, index = [], 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        spans.append({"start": start, "end_exclusive": index, "size": index-start})
    return spans


def build(config_path: Path = CONFIG) -> dict[str, Any]:
    config = json.loads((ROOT / config_path).read_text(encoding="utf-8"))
    inputs, outputs = config["inputs"], config["outputs"]
    stage59 = identity(inputs["stage59_rom"], "Stage59 ROM")
    metadata59_raw = identity(inputs["stage59_metadata"], "Stage59 metadata")
    previous = json.loads(identity(inputs["stage59_allocation"], "Stage59 allocation"))
    clean = identity(inputs["clean_rom"], "clean ROM")
    if len(stage59) != ROM_SIZE or len(clean) * 2 != ROM_SIZE:
        raise BuildError("ROM size differs")
    metadata59 = json.loads(metadata59_raw)
    if metadata59["output"]["sha256"] != sha(stage59):
        raise BuildError("Stage59 metadata does not own input ROM")

    provisional_code, _, _ = compile_runtime(Path(config["runtime_source"]), 0x09E00100)
    provisional_payload = payload(provisional_code)
    row, _ = allocate(previous, len(provisional_payload), "0" * 64)
    offset = int(row["start"])
    code, symbols, nm_text = compile_runtime(
        Path(config["runtime_source"]), GBA_BASE + offset + HEADER_SIZE)
    built_payload = payload(code)
    if len(code) != len(provisional_code) or len(built_payload) != len(provisional_payload):
        raise BuildError("placement changed runtime size")
    row, allocation_report = allocate(previous, len(built_payload), sha(built_payload))
    if int(row["start"]) != offset or stage59[offset:offset+len(built_payload)] \
            != b"\xFF" * len(built_payload):
        raise BuildError("allocated bytes are not free")

    output = bytearray(stage59)
    output[offset:offset+len(built_payload)] = built_payload
    hook_rows: list[dict[str, Any]] = []
    for hook in config["hooks"]:
        hook_address = int(hook["address"], 16)
        hook_offset = hook_address - GBA_BASE
        expected = bytes.fromhex(hook["expected"])
        target = symbols[hook["symbol"]]
        kind = hook.get("kind")
        if kind == "thumb_bl":
            replacement = thumb_bl(hook_address, target)
        elif kind == "thumb_pointer":
            replacement = struct.pack("<I", target | 1)
        else:
            replacement = jump_stub(target)
        if stage59[hook_offset:hook_offset+len(expected)] != expected:
            raise BuildError(f"hook expected bytes differ: {hook['name']}")
        if len(replacement) != len(expected):
            raise BuildError(f"hook length differs: {hook['name']}")
        output[hook_offset:hook_offset+len(replacement)] = replacement
        hook_rows.append({
            "name": hook["name"], "address": hook_address,
            "start": hook_offset,
            "end_exclusive": hook_offset + len(replacement),
            "expected_hex": expected.hex(),
            "replacement_hex": replacement.hex(), "runtime_entry": target | 1,
        })
    output_raw = bytes(output)

    declared = [
        {"name": "payload", "start": offset,
         "end_exclusive": offset+len(built_payload)},
        *hook_rows,
    ]
    spans = changed_spans(stage59, output_raw)
    outside = [span for span in spans if not any(
        row["start"] <= span["start"] and span["end_exclusive"] <= row["end_exclusive"]
        for row in declared)]
    if outside:
        raise BuildError(f"changes outside declared spans: {outside[:3]}")

    incremental = _sparse_bps(stage59, output_raw)
    clean_bps = create_bps(clean, output_raw, metadata=b"firered-jpn-rev0-to-stage60")
    if apply_bps(stage59, incremental) != output_raw or apply_bps(clean, clean_bps) != output_raw:
        raise BuildError("BPS round trip failed")
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input_sha256": sha(stage59), "rom_sha256": sha(output_raw),
        "root_cause": {
            "first_corrupting_function": "TrainerChangeKitFinalRuntime_BuildTrainerPartySetup",
            "first_corrupting_instruction": "0x093033E0 strb r2, [r1, #31]",
            "observed_transition": "intended wild Species 10 -> stale prior trainer Species",
            "stale_owner": "gTrainerBattleOpponent_A",
        },
        "repair": {
            "scope": "global shared BuildTrainerPartySetup entrance",
            "map_or_species_hardcode": False,
            "hooks": hook_rows,
            "stock_delegate": 0x09302D61, "changekit_delegate": 0x09303395,
            "configure_delegate": 0x09417631,
            "ownership_predicates": ["fresh configure token", "storage magic",
                                     "PENDING/ACTIVE phase",
                                     "current_gimmick != NULL", "trainer_id equality"],
        },
        "allocation": row,
        "change_audit": {"changed_span_count": len(spans),
                         "outside_declared_span_count": 0, "spans": spans},
        "bps": {"incremental_round_trip": "PASS", "clean_round_trip": "PASS"},
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": 60, "status": "PASS",
        "input": {"path": inputs["stage59_rom"]["path"], "sha256": sha(stage59),
                  "size": len(stage59)},
        "output": {"path": outputs["rom"], "sha256": sha(output_raw),
                   "size": len(output_raw)},
        "runtime": {"source": config["runtime_source"], "address": GBA_BASE+offset,
                    "size": len(built_payload), "code_size": len(code),
                    "symbols": symbols},
        "audit": audit,
    }
    report = (
        "# Stage60 wild Species root repair\n\n"
        "- 原因: ChangeKit trainer sidecarが共有party生成入口で、前戦のtrainer IDをwild所有権と誤認。\n"
        "- 最初の破壊: `0x093033E0 strb r2, [r1, #31]`。\n"
        "- 修正: 有効ChangeKit contextとlive trainer IDが一致する時だけsidecar wrapperへ委譲。\n"
        "- Route/Species固有分岐なし。stock builderは全入口で維持。\n"
    ).encode("utf-8")

    artifacts = {
        outputs["rom"]: output_raw, outputs["metadata"]: stable(metadata),
        outputs["allocation"]: stable(allocation_report),
        outputs["incremental_bps"]: incremental, outputs["clean_bps"]: clean_bps,
        outputs["runtime"]: code,
        outputs["symbols"]: stable({"symbols": symbols, "nm": nm_text}),
        outputs["audit"]: stable(audit), outputs["report"]: report,
    }
    for name, raw in artifacts.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return metadata


def check(config_path: Path = CONFIG) -> dict[str, Any]:
    config = json.loads((ROOT / config_path).read_text(encoding="utf-8"))
    metadata = json.loads((ROOT / config["outputs"]["metadata"]).read_text())
    rom = (ROOT / config["outputs"]["rom"]).read_bytes()
    if metadata["output"]["sha256"] != sha(rom):
        raise BuildError("built ROM differs from metadata")
    if json.loads((ROOT / config["outputs"]["audit"]).read_text())["status"] != "PASS":
        raise BuildError("audit is not PASS")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    result = build(args.config) if args.action == "build" else check(args.config)
    print(json.dumps({"status": "PASS", "output": result["output"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
