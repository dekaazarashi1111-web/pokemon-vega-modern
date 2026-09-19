#!/usr/bin/env python3
"""Build the scoped PR16 party-retention successor over the exact 7f32 parent."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_bp_party_retention_successor.py"
SOURCE = "overlays/facility_party_retention/facility_party_retention.c"
HEADER = "overlays/save_migration/save_migration.h"
OUT = ROOT / ".local/pr16-bp-party-retention-successor"
REGIONS = "config/rom_regions.csv"
BASE = 0x08000000
SIZE = 33_554_432
PARENT_SHA = "7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd"
CALLSITE = 0x090DD51C
CALLSITE_OFFSET = CALLSITE - BASE
CALLSITE_BEFORE = bytes.fromhex("24f032f9")
ORIGINAL_PREDICATE = 0x09101784
TRAMPOLINE_OFFSET = 0x012CFF28
TRAMPOLINE_ADDRESS = BASE + TRAMPOLINE_OFFSET
RUNTIME_REGION = "future_tail"
RUNTIME_RESERVATION = 2048
ALLOCATION_OWNER = "USER-20260914-BP-PARTY-RETENTION"


class RetentionBuildError(ValueError):
    """The pinned candidate, ABI, allocation, or bounded edit differs."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RetentionBuildError(message)


def identity(raw: bytes) -> dict[str, int | str]:
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def patch_bytes(raw: bytes, offset: int, before: bytes, after: bytes) -> bytes:
    need(type(raw) is bytes and type(offset) is int, "immutable bytes/integer required")
    need(type(before) is bytes and type(after) is bytes, "byte patches required")
    need(len(before) == len(after) > 0, "fixed-size nonempty edit required")
    need(0 <= offset <= len(raw) - len(before), "patch outside candidate")
    need(raw[offset : offset + len(before)] == before, "patch preimage differs")
    need(before != after, "empty edit rejected")
    return raw[:offset] + after + raw[offset + len(before) :]


def decode_thumb_bl(address: int, raw: bytes) -> int:
    need(len(raw) == 4 and address % 2 == 0, "aligned four-byte Thumb BL required")
    first, second = struct.unpack("<HH", raw)
    need(first & 0xF800 == 0xF000, "Thumb BL first halfword differs")
    need(second & 0xF800 == 0xF800, "Thumb BL second halfword differs")
    displacement = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if displacement & (1 << 22):
        displacement -= 1 << 23
    return address + 4 + displacement


def encode_thumb_bl(address: int, target: int) -> bytes:
    need(address % 2 == 0 and target % 2 == 0, "Thumb BL addresses must be aligned")
    displacement = target - (address + 4)
    need(displacement % 2 == 0, "Thumb BL displacement must be halfword aligned")
    need(-(1 << 22) <= displacement <= (1 << 22) - 2, "Thumb BL target out of range")
    encoded = displacement & ((1 << 23) - 1)
    raw = struct.pack(
        "<HH",
        0xF000 | ((encoded >> 12) & 0x07FF),
        0xF800 | ((encoded >> 1) & 0x07FF),
    )
    need(decode_thumb_bl(address, raw) == target, "Thumb BL round-trip differs")
    return raw


def make_trampoline(runtime_entry: int) -> bytes:
    """Return an 8-byte Thumb absolute tail jump that preserves caller LR."""
    need(runtime_entry & 1 == 1, "Thumb runtime entry required")
    # ldr r3, [pc, #0]; bx r3; .word runtime_entry
    return struct.pack("<HHI", 0x4B00, 0x4718, runtime_entry)


def existing_requests(original: dict[str, object]) -> list[dict[str, object]]:
    from tools.rom_allocator import REQUEST_FIELDS

    summaries = original.get("summaries")
    rows = original.get("allocations")
    need(isinstance(summaries, dict) and summaries.get("overlap_count") == 0, "parent allocation overlap")
    need(isinstance(rows, list), "parent allocations absent")
    requests: list[dict[str, object]] = []
    for index, raw_row in enumerate(rows):
        need(isinstance(raw_row, dict), "parent allocation row differs")
        row = dict(raw_row)
        start = row.get("start")
        end = row.get("end_exclusive")
        size = row.get("size")
        need(
            row.get("sequence") == index
            and type(start) is int
            and type(end) is int
            and type(size) is int
            and 0 <= start < end <= SIZE
            and end - start == size,
            "parent allocation bounds/order differ",
        )
        request = {key: value for key, value in row.items() if key in REQUEST_FIELDS}
        if row.get("placement") == "FIRST_FIT":
            request.pop("start", None)
        requests.append(request)
    return requests


def choose_runtime_offset(original: dict[str, object]) -> int:
    from tools.rom_allocator import build_allocation_report_from_csv

    requests = existing_requests(original)
    requests.append(
        {
            "name": "pr16_factory_party_retention_runtime_preview",
            "region": RUNTIME_REGION,
            "size": RUNTIME_RESERVATION,
            "alignment": 4,
            "owner": ALLOCATION_OWNER,
            "purpose": "preview only",
            "content_sha256": "0" * 64,
        }
    )
    preview = build_allocation_report_from_csv(ROOT / REGIONS, requests)
    rows = [
        row
        for row in preview["allocations"]
        if row["name"] == "pr16_factory_party_retention_runtime_preview"
    ]
    need(len(rows) == 1, "runtime preview allocation missing")
    start = rows[0]["start"]
    need(type(start) is int and start % 4 == 0, "runtime preview alignment differs")
    return start


def compile_runtime(out: Path, runtime_offset: int) -> bytes:
    need(not any(path.is_symlink() for path in (out, *out.parents)), "unsafe compile output")
    out.mkdir(parents=True, exist_ok=True)
    runtime_address = BASE + runtime_offset
    linker = out / "runtime.ld"
    linker.write_text(
        "ENTRY(VegaFacilityRandomPlayerParty)\n"
        f"SECTIONS {{ . = 0x{runtime_address:08x}; "
        ".text : { KEEP(*(.text.entry)) *(.text*) *(.rodata*) } "
        "/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n"
    )
    elf = out / "runtime.elf"
    binary = out / "runtime.bin"
    command = [
        "arm-none-eabi-gcc",
        "-std=c11",
        "-Os",
        "-mthumb",
        "-mcpu=arm7tdmi",
        "-ffreestanding",
        "-fno-builtin",
        "-ffunction-sections",
        "-fdata-sections",
        "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-nostdlib",
        "-Wl,--gc-sections",
        "-Wl,--build-id=none",
        "-T",
        str(linker),
        f"-DVEGA_ORIGINAL_RANDOM_PREDICATE=0x{ORIGINAL_PREDICATE | 1:08x}u",
        str(ROOT / SOURCE),
        "-o",
        str(elf),
    ]
    subprocess.run(command, check=True, capture_output=True)
    symbols = subprocess.check_output(["arm-none-eabi-nm", "-n", str(elf)], text=True)
    entries = [
        int(line.split()[0], 16)
        for line in symbols.splitlines()
        if line.split()[-1:] == ["VegaFacilityRandomPlayerParty"]
    ]
    need(len(entries) == 1 and entries[0] & ~1 == runtime_address, "runtime entry placement differs")
    subprocess.run(
        ["arm-none-eabi-objcopy", "-O", "binary", str(elf), str(binary)],
        check=True,
        capture_output=True,
    )
    payload = binary.read_bytes()
    need(32 <= len(payload) <= RUNTIME_RESERVATION, "bounded runtime size differs")
    disassembly = subprocess.check_output(
        ["arm-none-eabi-objdump", "-d", str(elf)], text=True
    ).replace(str(elf), "party-retention-runtime.elf")
    (out / "runtime-disassembly.txt").write_text(disassembly)
    (out / "runtime-symbols.txt").write_text(symbols)
    return payload


def allocation(
    parent: bytes,
    original: dict[str, object],
    runtime_offset: int,
    payload: bytes,
    trampoline: bytes,
) -> dict[str, object]:
    from tools.rom_allocator import build_allocation_report_from_csv

    requests = existing_requests(original)
    for row in original["allocations"]:
        start, end = row["start"], row["end_exclusive"]
        need(identity(parent[start:end])["sha256"] == row["content_sha256"], "parent allocation identity differs")
    requests.extend(
        [
            {
                "name": "pr16_factory_party_retention_trampoline",
                "region": "integration_modules",
                "start": TRAMPOLINE_OFFSET,
                "size": len(trampoline),
                "alignment": 4,
                "owner": ALLOCATION_OWNER,
                "purpose": "Near Thumb tail jump for the verified player predicate callsite",
                "content_sha256": identity(trampoline)["sha256"],
            },
            {
                "name": "pr16_factory_party_retention_runtime",
                "region": RUNTIME_REGION,
                "start": runtime_offset,
                "size": len(payload),
                "alignment": 4,
                "owner": ALLOCATION_OWNER,
                "purpose": "Read-only exchange-party retention predicate wrapper",
                "content_sha256": identity(payload)["sha256"],
            },
        ]
    )
    result = build_allocation_report_from_csv(ROOT / REGIONS, requests)
    need(result["summaries"]["overlap_count"] == 0, "successor allocation overlap")
    return result


def build(
    parent: bytes,
    original: dict[str, object],
    runtime_offset: int,
    payload: bytes,
) -> tuple[bytes, dict[str, object]]:
    need(identity(parent) == {"size": SIZE, "sha256": PARENT_SHA}, "exact 7f32 parent required")
    need(parent[CALLSITE_OFFSET : CALLSITE_OFFSET + 4] == CALLSITE_BEFORE, "verified predicate callsite differs")
    need(decode_thumb_bl(CALLSITE, CALLSITE_BEFORE) == ORIGINAL_PREDICATE, "original predicate target differs")
    need(0 <= runtime_offset <= SIZE - len(payload), "runtime outside candidate")
    runtime_entry = BASE + runtime_offset + 1
    trampoline = make_trampoline(runtime_entry)
    need(parent[TRAMPOLINE_OFFSET : TRAMPOLINE_OFFSET + len(trampoline)] == b"\xff" * len(trampoline), "trampoline gap is not erased")
    need(parent[runtime_offset : runtime_offset + len(payload)] == b"\xff" * len(payload), "runtime allocation is not erased")
    callsite_after = encode_thumb_bl(CALLSITE, TRAMPOLINE_ADDRESS)
    candidate = patch_bytes(parent, CALLSITE_OFFSET, CALLSITE_BEFORE, callsite_after)
    candidate = patch_bytes(candidate, TRAMPOLINE_OFFSET, b"\xff" * len(trampoline), trampoline)
    candidate = patch_bytes(candidate, runtime_offset, b"\xff" * len(payload), payload)
    spans = sorted(
        [
            (CALLSITE_OFFSET, CALLSITE_OFFSET + 4),
            (TRAMPOLINE_OFFSET, TRAMPOLINE_OFFSET + len(trampoline)),
            (runtime_offset, runtime_offset + len(payload)),
        ]
    )
    need(all(left[1] <= right[0] for left, right in zip(spans, spans[1:])), "declared edits overlap")
    cursor = 0
    for start, end in spans:
        need(candidate[cursor:start] == parent[cursor:start], "undeclared candidate prefix change")
        cursor = end
    need(candidate[cursor:] == parent[cursor:], "undeclared candidate suffix change")
    plan = allocation(parent, original, runtime_offset, payload, trampoline)
    for row in plan["allocations"]:
        start, end = row["start"], row["end_exclusive"]
        need(identity(candidate[start:end])["sha256"] == row["content_sha256"], "output allocation identity differs")
    changed = sum(left != right for left, right in zip(parent, candidate))
    report: dict[str, object] = {
        "schema_version": 1,
        "status": "BUILT_SCOPED_PARTY_RETENTION_NOT_NATIVE_ACCEPTED",
        "parent": identity(parent),
        "candidate": identity(candidate),
        "crc32": f"{zlib.crc32(candidate) & 0xFFFFFFFF:08X}",
        "allocation": plan,
        "binding": {
            "callsite": CALLSITE,
            "callsite_before": CALLSITE_BEFORE.hex(),
            "original_predicate": ORIGINAL_PREDICATE,
            "trampoline": TRAMPOLINE_ADDRESS,
            "runtime_entry": runtime_entry,
            "player_true_path_only": True,
            "second_predicate_callsite_changed": False,
        },
        "runtime": identity(payload),
        "runtime_offset": runtime_offset,
        "runtime_entry": runtime_entry,
        "trampoline": {"offset": TRAMPOLINE_OFFSET, **identity(trampoline)},
        "changes": [
            {"offset": CALLSITE_OFFSET, "size": 4, "before": CALLSITE_BEFORE.hex(), "after": callsite_after.hex()},
            {"offset": TRAMPOLINE_OFFSET, "size": len(trampoline), "before": (b"\xff" * len(trampoline)).hex(), "after": trampoline.hex()},
            {"offset": runtime_offset, "size": len(payload), "before": (b"\xff" * len(payload)).hex(), "after": payload.hex()},
        ],
        "actual_changed_bytes": changed,
        "undeclared_changed_bytes": 0,
        "new_allocations": 2,
        "save_layout_changes": 0,
        "global_special_table_changes": 0,
        "accepted_native_cases_replayed": 0,
        "new_emulator_processes": 0,
        "runtime_connected": True,
        "native_party_retention_accepted": False,
        "native_bp_earning_accepted": False,
        "p05_native_bp_gap_closed": False,
        "release_ready": False,
        "active_baseline_changed": False,
    }
    return candidate, report


def run() -> dict[str, object]:
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
    import pr16_bp_exchange_successor as previous

    need(not any(path.is_symlink() for path in (OUT, *OUT.parents)), "unsafe successor output")
    OUT.mkdir(parents=True, exist_ok=True)
    parent_report = previous.run()
    parent = (previous.OUT / "candidate.gba").read_bytes()
    need(parent_report["candidate"] == identity(parent), "parent report/candidate differ")
    runtime_offset = choose_runtime_offset(parent_report["allocation"])
    payloads = [compile_runtime(OUT / f"compile-{index}", runtime_offset) for index in (1, 2)]
    need(payloads[0] == payloads[1], "independent native compilations differ")
    left, report = build(parent, parent_report["allocation"], runtime_offset, payloads[0])
    right, again = build(parent, parent_report["allocation"], runtime_offset, payloads[1])
    need(left == right and report == again, "independent bounded successors differ")
    (OUT / "candidate.gba").write_bytes(left)
    report.update(
        independent_native_compiles=2,
        independent_bounded_builds=2,
        sources={
            path: identity((ROOT / path).read_bytes())
            for path in (SELF, SOURCE, HEADER, REGIONS, previous.SELF)
        },
    )
    (OUT / "candidate.json").write_bytes(stable(report))
    need((previous.OUT / "candidate.gba").read_bytes() == parent, "parent mutated")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
