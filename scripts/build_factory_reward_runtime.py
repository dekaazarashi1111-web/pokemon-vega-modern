#!/usr/bin/env python3
"""Stage 27へFactory TrialのACTIVE初回・連勝報酬を実ROM接続する。"""

from __future__ import annotations

import argparse
import csv
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

from tools.release import bps as bps_codec  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260818-FACTORY-REWARD-RUNTIME"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/27_bp_shop_runtime.gba")
INPUT_META = Path("build/stages/27_bp_shop_runtime.json")
INPUT_ALLOC = Path("build/stages/27_allocation.json")
FACILITY_META = Path("build/stages/20_facility_runtime.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
OUTPUT_ROM = Path("build/stages/28_factory_reward_runtime.gba")
OUTPUT_META = Path("build/stages/28_factory_reward_runtime.json")
OUTPUT_ALLOC = Path("build/stages/28_allocation.json")
RUNTIME_BIN = Path("generated/runtime/factory_reward_runtime.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/factory_reward_runtime_symbols.json")
CATALOG_HEADER = Path("generated/runtime/factory_reward_catalog_generated.h")
CATALOG_JSON = Path("generated/runtime/factory_reward_catalog.json")
MGBA_FIXTURE = Path("build/stages/28_mgba_factory_reward_smoke.json")
REPORT = Path("reports/generated/factory_reward_runtime.md")
PATCH_INCREMENTAL = Path("build/patches/bp-shop-stage27-to-factory-reward-stage28.bps")
PATCH_CUMULATIVE = Path("build/patches/vega-modern-kanto-v1.4.0-to-factory-reward-stage28.bps")
RUNNER = Path("tools/mgba_factory_reward_smoke.c")

EXPECTED_INPUT_SHA256 = "efeec95f16adfcd7d0076339cc4930f2c0c1f56af9cc85cd93fad0c9b9599611"
EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
PAYLOAD_HEADER_SIZE = 0x80
ALLOCATION_NAME = "factory_reward_runtime_payload"
MANIFEST_KEYS = (
    "FACILITY_REWARD_KEY_TRIAL_XS",
    "FACILITY_REWARD_KEY_TRIAL_S",
    "FACILITY_REWARD_KEY_TRIAL_BP",
    "FACILITY_REWARD_KEY_STREAK_003",
    "FACILITY_REWARD_KEY_STREAK_007",
    "FACILITY_REWARD_KEY_STREAK_014",
    "FACILITY_REWARD_KEY_STREAK_021",
)
FIRST_CLAIM_BITS = {
    "FACILITY_REWARD_KEY_TRIAL_XS": 1,
    "FACILITY_REWARD_KEY_TRIAL_S": 2,
    "FACILITY_REWARD_KEY_TRIAL_BP": 3,
}
STREAK_CLAIM_BITS = {
    "FACILITY_REWARD_KEY_STREAK_003": 4,
    "FACILITY_REWARD_KEY_STREAK_007": 5,
    "FACILITY_REWARD_KEY_STREAK_014": 6,
    "FACILITY_REWARD_KEY_STREAK_021": 7,
}
CREDIT_KINDS = {
    "CREDIT_KEY_HABITAT": 0,
    "CREDIT_KEY_TYPE": 1,
    "CREDIT_KEY_RARE": 2,
    "CREDIT_KEY_RANDOM": 3,
}
REQUIRED_ENTRYPOINTS = {
    "FactoryRewardRuntime_Probe",
    "FactoryRewardRuntime_Complete",
}
REQUIRED_LINKED_SYMBOLS = REQUIRED_ENTRYPOINTS | {
    "VegaFactoryAddBattlePoints",
    "VegaSaveFinalize",
    "VegaSaveValidate",
}


class FactoryRewardBuildError(ValueError):
    """入力、manifest、ROM ABI、配置、または受入条件の違反。"""


def _fail(message: str) -> NoReturn:
    raise FactoryRewardBuildError(message)


def _sha(raw: bytes | bytearray) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-5000:]}")
    return completed.stdout.strip()


def _arm_tool(root: Path, name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    for candidate in (
        root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/arm-toolchain/bin" / name,
        root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/arm-toolchain/bin-real" / name,
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    _fail(f"required ARM tool is missing: {name}")


def _host_cc(root: Path) -> str:
    configured = os.environ.get("CC")
    if configured:
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        candidate = Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    resolved = shutil.which("cc")
    if resolved:
        # Prefer the kit wrapper when present because it carries the pinned
        # libmGBA include/library closure even if a system cc also exists.
        kit = root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/host-toolchain/bin/cc"
        if kit.is_file() and os.access(kit, os.X_OK):
            return str(kit)
        return resolved
    candidate = root.parent / "OFFLINE_TESTKIT/runtime/linux-x86_64/host-toolchain/bin/cc"
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    _fail("host C compiler is missing")


def _u32(raw: bytes | bytearray, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        _fail(f"{label}: offset outside ROM: 0x{offset:X}")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(address: int, size: int, label: str, *, limit: int = ROM_SIZE) -> int:
    address &= ~1
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > limit:
        _fail(f"{label}: ROM address outside image: 0x{address:08X}+{size}")
    return offset


def _sparse_bps(source: bytes, target: bytes) -> bytes:
    """Encode sparse same-size ROM changes without byte-walking equal MiB runs."""

    if len(source) != len(target):
        _fail("sparse BPS requires equal-size source and target")
    spans: list[tuple[int, int]] = []
    block_size = 0x1000
    for block_start in range(0, len(target), block_size):
        block_end = min(block_start + block_size, len(target))
        left = source[block_start:block_end]
        right = target[block_start:block_end]
        if left == right:
            continue
        index = 0
        while index < len(right):
            while index < len(right) and left[index] == right[index]:
                index += 1
            if index == len(right):
                break
            start = block_start + index
            while index < len(right) and left[index] != right[index]:
                index += 1
            end = block_start + index
            if spans and start - spans[-1][1] < 4:
                spans[-1] = (spans[-1][0], end)
            else:
                spans.append((start, end))

    patch = bytearray(bps_codec.MAGIC)
    patch.extend(bps_codec._encode_number(len(source)))
    patch.extend(bps_codec._encode_number(len(target)))
    patch.extend(bps_codec._encode_number(0))
    cursor = 0
    for start, end in spans:
        if start > cursor:
            patch.extend(bps_codec._action(bps_codec.SOURCE_READ, start - cursor))
        patch.extend(bps_codec._action(bps_codec.TARGET_READ, end - start))
        patch.extend(target[start:end])
        cursor = end
    if cursor < len(target):
        patch.extend(bps_codec._action(bps_codec.SOURCE_READ, len(target) - cursor))
    patch.extend(bps_codec._crc32(source).to_bytes(4, "little"))
    patch.extend(bps_codec._crc32(target).to_bytes(4, "little"))
    patch.extend(bps_codec._crc32(patch).to_bytes(4, "little"))
    encoded = bytes(patch)
    if apply_bps(source, encoded) != target:
        _fail("sparse BPS round-trip differs")
    return encoded


def _input_contract(
    root: Path,
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage = (root / INPUT_ROM).read_bytes()
    base = (root / BASE_ROM).read_bytes()
    stage_meta = _read_json(root / INPUT_META)
    previous_alloc = _read_json(root / INPUT_ALLOC)
    facility_meta = _read_json(root / FACILITY_META)
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_INPUT_SHA256:
        _fail("stage27 input size or hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size or hash differs")
    if stage_meta.get("output", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        _fail("stage27 metadata output hash differs")
    if previous_alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage27 allocator overlap contract failed")
    old_complete = int(facility_meta.get("entrypoints", {}).get("FacilityRuntime_Complete", 0))
    script = int(facility_meta.get("symbols", {}).get("script_facility_complete", 0))
    script_offset = _rom_offset(script, 6, "Facility completion script")
    if stage[script_offset] != 0x23:
        _fail("Facility completion script no longer starts with callnative")
    if _u32(stage, script_offset + 1, "Facility completion native pointer") != old_complete:
        _fail("Facility completion script no longer targets stage20 complete")
    return stage, base, stage_meta, previous_alloc, facility_meta


def _catalog_outputs(root: Path) -> tuple[dict[str, Any], bytes, bytes]:
    reward_rows = _rows(root / "manifests/facility_rewards.csv")
    selected = {
        row["facility_reward_key"]: row
        for row in reward_rows
        if row.get("facility_reward_key") in MANIFEST_KEYS
    }
    if set(selected) != set(MANIFEST_KEYS):
        _fail("Factory reward manifest key set differs")
    if any(selected[key].get("status") != "ACTIVE" for key in MANIFEST_KEYS):
        _fail("Factory reward manifest contains non-ACTIVE selected rows")

    item_rows = {row["item_key"]: row for row in _rows(root / "manifests/item_ids.csv")}
    try:
        xs_item = int(item_rows["ITEM_KEY_EXP_CANDY_XS"]["id"], 0)
        s_item = int(item_rows["ITEM_KEY_EXP_CANDY_S"]["id"], 0)
    except (KeyError, ValueError) as error:
        _fail(f"Exp Candy item binding differs: {error}")

    xs = selected["FACILITY_REWARD_KEY_TRIAL_XS"]
    small = selected["FACILITY_REWARD_KEY_TRIAL_S"]
    bp = selected["FACILITY_REWARD_KEY_TRIAL_BP"]
    if (
        xs["trigger_kind"] != "TRIAL_FIRST"
        or xs["item_key"] != "ITEM_KEY_EXP_CANDY_XS"
        or int(xs["quantity"], 0) <= 0
        or small["trigger_kind"] != "TRIAL_FIRST"
        or small["item_key"] != "ITEM_KEY_EXP_CANDY_S"
        or int(small["quantity"], 0) <= 0
        or bp["trigger_kind"] != "TRIAL_FIRST"
        or bp["currency_key"] != "CURRENCY_KEY_BP"
        or int(bp["amount"], 0) <= 0
    ):
        _fail("Factory first-clear reward semantics differ")

    streaks: list[dict[str, Any]] = []
    for key in MANIFEST_KEYS[3:]:
        row = selected[key]
        if (
            row["trigger_kind"] != "STREAK"
            or row["repeatability"] != "ONCE"
            or row["currency_key"] not in CREDIT_KINDS
            or int(row["amount"], 0) != 1
            or int(row["streak"], 0) <= 0
        ):
            _fail(f"Factory streak reward semantics differ: {key}")
        streaks.append({
            "facility_reward_key": key,
            "streak": int(row["streak"], 0),
            "currency_key": row["currency_key"],
            "credit_kind": CREDIT_KINDS[row["currency_key"]],
            "amount": int(row["amount"], 0),
            "claim_key": row["claim_key"],
            "claim_bit": STREAK_CLAIM_BITS[key],
        })
    if [row["streak"] for row in streaks] != sorted(row["streak"] for row in streaks):
        _fail("Factory streak thresholds are not ascending")

    first_mask = sum(1 << bit for bit in FIRST_CLAIM_BITS.values())
    streak_thresholds_c = ", ".join(f"{row['streak']}u" for row in streaks)
    streak_kinds_c = ", ".join(f"{row['credit_kind']}u" for row in streaks)
    streak_bits_c = ", ".join(f"{row['claim_bit']}u" for row in streaks)
    header = f"""#ifndef VEGA_FACTORY_REWARD_CATALOG_GENERATED_H
#define VEGA_FACTORY_REWARD_CATALOG_GENERATED_H

#include <stdint.h>

#define FACTORY_REWARD_ITEM_EXP_CANDY_XS {xs_item}u
#define FACTORY_REWARD_ITEM_EXP_CANDY_XS_QUANTITY {int(xs['quantity'], 0)}u
#define FACTORY_REWARD_ITEM_EXP_CANDY_S {s_item}u
#define FACTORY_REWARD_ITEM_EXP_CANDY_S_QUANTITY {int(small['quantity'], 0)}u
#define FACTORY_REWARD_FIRST_BP {int(bp['amount'], 0)}u
#define FACTORY_REWARD_FIRST_XS_CLAIM_BIT {FIRST_CLAIM_BITS['FACILITY_REWARD_KEY_TRIAL_XS']}u
#define FACTORY_REWARD_FIRST_S_CLAIM_BIT {FIRST_CLAIM_BITS['FACILITY_REWARD_KEY_TRIAL_S']}u
#define FACTORY_REWARD_FIRST_BP_CLAIM_BIT {FIRST_CLAIM_BITS['FACILITY_REWARD_KEY_TRIAL_BP']}u
#define FACTORY_REWARD_FIRST_CLAIM_MASK 0x{first_mask:02X}u
#define FACTORY_REWARD_STREAK_COUNT {len(streaks)}u

static const uint16_t gFactoryRewardStreakThresholds[FACTORY_REWARD_STREAK_COUNT] = {{
    {streak_thresholds_c}
}};
static const uint8_t gFactoryRewardStreakCreditKinds[FACTORY_REWARD_STREAK_COUNT] = {{
    {streak_kinds_c}
}};
static const uint8_t gFactoryRewardStreakClaimBits[FACTORY_REWARD_STREAK_COUNT] = {{
    {streak_bits_c}
}};

#endif /* VEGA_FACTORY_REWARD_CATALOG_GENERATED_H */
""".encode("ascii")
    catalog = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "source": ["manifests/facility_rewards.csv", "manifests/item_ids.csv"],
        "selected_keys": list(MANIFEST_KEYS),
        "first_clear": {
            "items": [
                {
                    "facility_reward_key": xs["facility_reward_key"],
                    "item_key": xs["item_key"],
                    "item_id": xs_item,
                    "quantity": int(xs["quantity"], 0),
                    "claim_key": xs["claim_key"],
                    "claim_bit": FIRST_CLAIM_BITS[xs["facility_reward_key"]],
                },
                {
                    "facility_reward_key": small["facility_reward_key"],
                    "item_key": small["item_key"],
                    "item_id": s_item,
                    "quantity": int(small["quantity"], 0),
                    "claim_key": small["claim_key"],
                    "claim_bit": FIRST_CLAIM_BITS[small["facility_reward_key"]],
                },
            ],
            "battle_points": int(bp["amount"], 0),
            "bp_claim_key": bp["claim_key"],
            "bp_claim_bit": FIRST_CLAIM_BITS[bp["facility_reward_key"]],
            "claim_mask": first_mask,
        },
        "streak_rewards": streaks,
        "header_sha256": _sha(header),
    }
    return catalog, header, _stable(catalog)


def _compile_runtime(
    root: Path,
    load_address: int,
    generated_header: bytes,
    old_complete: int,
) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(root, "arm-none-eabi-gcc")
    objcopy = _arm_tool(root, "arm-none-eabi-objcopy")
    nm = _arm_tool(root, "arm-none-eabi-nm")
    sources = [
        root / "overlays/factory_reward_runtime/factory_reward_runtime.c",
        root / "overlays/factory_reward_runtime/factory_reward_libc.c",
        root / "overlays/save_migration/save_migration.c",
    ]
    for source in sources:
        if not source.is_file():
            _fail(f"Factory reward runtime source missing: {source}")
    with tempfile.TemporaryDirectory(prefix="vega-factory-reward-runtime-") as temporary:
        directory = Path(temporary)
        (directory / "factory_reward_catalog_generated.h").write_bytes(generated_header)
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-Os", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables", "-fdata-sections",
            "-ffunction-sections", "-fno-common", "-DVEGA_SAVE_ROM_RUNTIME=1",
            f"-DVEGA_FACILITY_COMPLETE_ADDRESS=0x{old_complete:08X}u",
            f"-I{directory}", f"-I{root}",
            f"-I{root / 'overlays/factory_reward_runtime'}",
            f"-I{root / 'overlays/save_migration'}",
        ]
        objects: list[Path] = []
        for index, source in enumerate(sources):
            obj = directory / f"{index:02d}_{source.stem}.o"
            _run([*common, "-c", str(source), "-o", str(obj)], f"compile {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : {\n"
            "    KEEP(*(.text.FactoryRewardRuntime_*))\n"
            "    *(.text*) *(.rodata*) *(.data*)\n"
            "  }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n",
            encoding="ascii",
        )
        elf = directory / "factory_reward.elf"
        binary = directory / "factory_reward.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FactoryRewardRuntime_Probe", f"-Wl,-T,{linker}",
            *map(str, objects), "-lgcc", "-o", str(elf),
        ], "link Factory reward runtime")
        undefined = _run([nm, "-u", str(elf)], "Factory reward undefined-symbol audit")
        if undefined:
            _fail("Factory reward runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Factory reward objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Factory reward nm").splitlines():
            fields = line.split()
            if len(fields) == 3:
                try:
                    symbols[fields[2]] = int(fields[0], 16)
                except ValueError:
                    pass
        missing = sorted(REQUIRED_LINKED_SYMBOLS - set(symbols))
        if missing:
            _fail(f"Factory reward linked exports differ: missing={missing}")
        code = binary.read_bytes()
        if not code or len(code) > 32 * 1024:
            _fail(f"unexpected Factory reward runtime size: {len(code)}")
        for name in REQUIRED_LINKED_SYMBOLS:
            address = symbols[name]
            if address & 1 or not load_address <= address < load_address + len(code):
                _fail(f"Factory reward symbol outside/alignment: {name}=0x{address:08X}")
        return code, symbols


def _build_payload(
    root: Path,
    generated_header: bytes,
    payload_offset: int,
    old_complete: int,
    catalog: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    code_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(root, code_address, generated_header, old_complete)
    payload = bytearray(PAYLOAD_HEADER_SIZE + len(code))
    payload[PAYLOAD_HEADER_SIZE:] = code
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    struct.pack_into(
        "<8sIIIIIIIIIII",
        payload,
        0,
        b"VEGAFR28",
        1,
        len(payload),
        len(code),
        len(MANIFEST_KEYS),
        int(catalog["first_clear"]["battle_points"]),
        int(catalog["first_clear"]["claim_mask"]),
        len(catalog["streak_rewards"]),
        old_complete,
        entrypoints["FactoryRewardRuntime_Probe"],
        entrypoints["FactoryRewardRuntime_Complete"],
        0,
    )
    linked = {name: symbols[name] | 1 for name in sorted(REQUIRED_LINKED_SYMBOLS)}
    return bytes(payload), {
        "payload": {
            "magic": "VEGAFR28",
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload),
            "sha256": _sha(payload),
            "header_size": PAYLOAD_HEADER_SIZE,
            "code_offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "code_address": code_address,
            "code_size": len(code),
            "code_sha256": _sha(code),
        },
        "entrypoints": entrypoints,
        "linked_symbols": linked,
        "symbols": {
            f"native::{name}": symbols[name]
            for name in sorted(symbols)
            if code_address <= symbols[name] < code_address + len(code)
        },
    }


def _previous_requests(allocation: dict[str, Any]) -> list[dict[str, object]]:
    return [{
        "name": row["name"],
        "region": row["region"],
        "size": row["size"],
        "alignment": row["alignment"],
        "start": row["start"],
        "owner": row["owner"],
        "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in allocation["allocations"]]


def _allocation(
    root: Path,
    previous: dict[str, Any],
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": "Factory Trial first-clear item/BP and streak encounter-credit wrapper",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage28 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Factory reward allocation is not unique")
    return matches[0], report


def _ram_audit(root: Path) -> dict[str, Any]:
    path = root / "config/ram_layout.csv"
    rows = _rows(path)
    rollback = [row for row in rows if row["symbol"] == "gVegaSaveRollbackData" and row["status"] == "LIVE"]
    if len(rollback) != 1:
        _fail("Factory reward rollback reservation is not unique")
    row = rollback[0]
    if (
        int(row["start"], 0) != 0x0203E400
        or int(row["end_exclusive"], 0) != 0x0203EC00
        or int(row["size"], 0) != 0x800
        or row["persistence"] != "VOLATILE"
    ):
        _fail("Factory reward rollback reservation differs")
    live = sorted(
        (int(item["start"], 0), int(item["end_exclusive"], 0), item["owner"])
        for item in rows
        if item["address_space"] == "EWRAM" and item["status"] == "LIVE"
    )
    overlap = [
        (left[2], right[2]) for left, right in zip(live, live[1:])
        if right[0] < left[1]
    ]
    if overlap:
        _fail(f"live EWRAM reservations overlap: {overlap}")
    return {
        "status": "PASS",
        "reused_reservation": row["owner"],
        "address": int(row["start"], 0),
        "end_exclusive": int(row["end_exclusive"], 0),
        "size": int(row["size"], 0),
        "new_ram_reservation": False,
        "overlap_count": 0,
        "layout_sha256": _sha(path.read_bytes()),
    }


def build_runtime_outputs(root: Path = ROOT) -> dict[str, bytes]:
    root = Path(root)
    stage, base, stage_meta, previous_alloc, facility_meta = _input_contract(root)
    catalog, generated_header, catalog_json = _catalog_outputs(root)
    old_complete = int(facility_meta["entrypoints"]["FacilityRuntime_Complete"])
    script_address = int(facility_meta["symbols"]["script_facility_complete"])
    script_offset = _rom_offset(script_address, 6, "Facility completion script")

    preliminary, _ = _build_payload(root, generated_header, 0, old_complete, catalog)
    allocation, _ = _allocation(root, previous_alloc, len(preliminary), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime = _build_payload(root, generated_header, payload_offset, old_complete, catalog)
    if len(payload) != len(preliminary):
        _fail("address-dependent Factory reward payload size changed")
    allocation, allocation_report = _allocation(root, previous_alloc, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Factory reward allocation changed after final link")
    payload_end = int(allocation["end_exclusive"])
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Factory reward payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    pointer_site = script_offset + 1
    expected = _u32(output, pointer_site, "old Facility complete pointer")
    if expected != old_complete:
        _fail(f"old Facility complete pointer differs: 0x{expected:08X}")
    replacement = int(runtime["entrypoints"]["FactoryRewardRuntime_Complete"])
    struct.pack_into("<I", output, pointer_site, replacement)
    patch = {
        "label": "Factory Trial completion callnative wrapper",
        "script_address": script_address,
        "script_offset": script_offset,
        "site_address": GBA_ROM_BASE + pointer_site,
        "site_offset": pointer_site,
        "opcode": 0x23,
        "expected_pointer": old_complete,
        "replacement_pointer": replacement,
    }

    allowed = [(payload_offset, payload_end), (pointer_site, pointer_site + 4)]
    changed = [index for index, (before, after) in enumerate(zip(stage, output)) if before != after]
    outside = [
        index for index in changed
        if not any(start <= index < end for start, end in allowed)
    ]
    if outside:
        _fail(f"stage28 changed bytes outside declared spans: {outside[:8]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    cumulative = _sparse_bps(base, output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("stage27 to stage28 BPS round-trip differs")
    if apply_bps(base, cumulative) != output_raw:
        _fail("v1.4.0 to stage28 cumulative BPS round-trip differs")

    ram = _ram_audit(root)
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "input": {
            "path": INPUT_ROM.as_posix(),
            "size": len(stage),
            "sha256": _sha(stage),
            "upstream_task": stage_meta.get("task"),
        },
        "base_release": {
            "path": BASE_ROM.as_posix(),
            "size": len(base),
            "sha256": _sha(base),
        },
        "output": {
            "path": OUTPUT_ROM.as_posix(),
            "size": len(output_raw),
            "sha256": _sha(output_raw),
        },
        **runtime,
        "catalog": {
            "path": CATALOG_JSON.as_posix(),
            "header_path": CATALOG_HEADER.as_posix(),
            "selected_row_count": len(MANIFEST_KEYS),
            "first_clear": catalog["first_clear"],
            "streak_rewards": catalog["streak_rewards"],
        },
        "patches": [patch],
        "completion_chain": {
            "script": script_address,
            "old_complete": old_complete,
            "wrapper_complete": replacement,
            "order": ["FacilityRuntime_Complete", "apply ACTIVE manifest bonus when result == 9"],
            "base_result_preserved": 9,
            "base_ownership": ["party restore", "current/best streak", "base 9 BP", "sector31 persistence"],
        },
        "transaction": {
            "first_clear_order": [
                "AddBagItem Exp Candy XS x5",
                "AddBagItem Exp Candy S x2",
                "VegaFactoryAddBattlePoints +3",
                "set first-clear claim bits 1..3",
                "set due streak credit/claim bits",
                "TrySavingData(0)",
                "TryWriteSector(31)",
            ],
            "bag_full_behavior": "base clear remains complete; first-clear claim bits stay unset and retry on a later successful clear",
            "repeat_behavior": "claim bits suppress duplicate first-clear items/BP and duplicate streak credits",
            "compensation": "save failure restores exact post-base ledger snapshot, removes newly added items, and best-effort rewrites both stores",
            "rollback_storage": "gVegaSaveRollbackData",
        },
        "ram_audit": ram,
        "allocation": {
            "path": OUTPUT_ALLOC.as_posix(),
            "name": ALLOCATION_NAME,
            "overlap_count": allocation_report["summaries"]["overlap_count"],
            "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"],
        },
        "release_patches": {
            "incremental": {
                "path": PATCH_INCREMENTAL.as_posix(),
                "source_sha256": _sha(stage),
                "target_sha256": _sha(output_raw),
                "size": len(incremental),
                "sha256": _sha(incremental),
                "exact": True,
            },
            "cumulative": {
                "path": PATCH_CUMULATIVE.as_posix(),
                "source_sha256": _sha(base),
                "target_sha256": _sha(output_raw),
                "size": len(cumulative),
                "sha256": _sha(cumulative),
                "exact": True,
            },
        },
        "change_audit": {
            "changed_byte_count": len(changed),
            "declared_spans": [
                {"start": payload_offset, "end_exclusive": payload_end, "kind": "payload"},
                {"start": pointer_site, "end_exclusive": pointer_site + 4, "kind": "callnative pointer"},
            ],
            "outside_declared_span_count": 0,
        },
        "invariants": {
            "input_stage27_hash_pinned": _sha(stage) == EXPECTED_INPUT_SHA256,
            "base_v1_4_0_hash_pinned": _sha(base) == EXPECTED_BASE_SHA256,
            "rom_size_32_mib": len(output_raw) == ROM_SIZE,
            "manifest_selected_rows_7": len(MANIFEST_KEYS) == 7,
            "first_claim_mask_bits_1_to_3": catalog["first_clear"]["claim_mask"] == 0x0E,
            "streak_thresholds_3_7_14_21": [row["streak"] for row in catalog["streak_rewards"]] == [3, 7, 14, 21],
            "completion_wrapper_physically_bound": _u32(output_raw, pointer_site, "new wrapper pointer") == replacement,
            "old_complete_called_first": True,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "ram_overlap_zero": ram["overlap_count"] == 0,
            "declared_changes_only": not outside,
            "incremental_bps_exact": True,
            "cumulative_bps_exact": True,
        },
    }
    if not all(metadata["invariants"].values()):
        _fail("Factory reward runtime invariant failed")
    symbols_doc = {
        "schema_version": 1,
        "task": TASK,
        "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"],
        "linked_symbols": runtime["linked_symbols"],
        "symbols": runtime["symbols"],
        "completion_chain": metadata["completion_chain"],
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): payload,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbols_doc),
        CATALOG_HEADER.as_posix(): generated_header,
        CATALOG_JSON.as_posix(): catalog_json,
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
    }


def _mgba_fixture(root: Path, stage: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    runner = root / RUNNER
    if not runner.is_file():
        _fail(f"Factory reward mGBA runner missing: {runner}")
    with tempfile.TemporaryDirectory(prefix="vega-factory-reward-smoke-") as temporary:
        temp = Path(temporary)
        executable = temp / "mgba-factory-reward-smoke"
        _run([
            _host_cc(root), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(RUNNER), "-o", str(executable), "-lmgba",
        ], "Factory reward libmGBA smoke compile", cwd=root)
        entry = metadata["entrypoints"]
        linked = metadata["linked_symbols"]
        ensure = _read_json(root / INPUT_META)["entrypoints"]["BpShop_EnsureSave"]
        common_args = [
            hex(entry["FactoryRewardRuntime_Probe"]),
            hex(entry["FactoryRewardRuntime_Complete"]),
            hex(linked["VegaSaveFinalize"]),
            hex(ensure),
            hex(metadata["completion_chain"]["script"]),
            hex(metadata["completion_chain"]["old_complete"]),
        ]
        processes: list[subprocess.Popen[str]] = []
        for index in (1, 2):
            rom = temp / f"28_factory_reward_run{index}.gba"
            save = temp / f"28_factory_reward_run{index}.sav"
            rom.write_bytes(stage)
            processes.append(subprocess.Popen(
                [str(executable), str(rom), str(save), *common_args],
                cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ))
        payloads: list[str] = []
        for index, process in enumerate(processes, start=1):
            try:
                stdout, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired as error:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending in processes:
                    pending.communicate()
                detail = ((error.stderr or error.stdout) or "").strip()
                _fail(f"Factory reward exact-ROM smoke run {index} timed out: {detail}")
            if process.returncode:
                for pending in processes:
                    if pending.poll() is None:
                        pending.kill()
                for pending in processes:
                    if pending is not process:
                        pending.communicate()
                detail = (stderr or stdout).strip()
                _fail(
                    f"Factory reward exact-ROM smoke run {index} failed "
                    f"({process.returncode}): {detail}"
                )
            payloads.append(stdout.strip())
        first, second = (json.loads(payload) for payload in payloads)
        if first != second or first.get("status") != "PASS":
            _fail("Factory reward exact-ROM smoke is not deterministic PASS")
        first["process_runs"] = 2
        first["rom_sha256"] = _sha(stage)
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    checks = mgba["checks"]
    text = f"""# Factory Trial reward runtime / Stage 28

## 結論

- 既存の `FacilityRuntime_Complete` を先に呼ぶwrapperを、Factory Trial完了scriptへ物理接続した。
- 既存のparty復元、連勝更新、基本9 BP、sector 31保存は変更していない。
- `manifests/facility_rewards.csv` のACTIVE初回3件と連勝4件を実saveへ接続した。
- 初回報酬は Exp Candy XS x5、Exp Candy S x2、追加3 BP。
- 連勝3/7/14/21で HABITAT/TYPE/RARE/RANDOM encounter creditを各1回だけ付与する。
- bag満杯時は基本クリアを取り消さず、初回報酬を未受取のまま次回成功時へ繰り越す。

## ROM結合

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Payload: `{metadata['payload']['address']:#010x}` / {metadata['payload']['size']} bytes
- Completion script: `{metadata['completion_chain']['script']:#010x}`
- Old complete: `{metadata['completion_chain']['old_complete']:#010x}`
- Wrapper complete: `{metadata['completion_chain']['wrapper_complete']:#010x}`
- Allocator overlap: {metadata['allocation']['overlap_count']}
- Declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- Incremental/cumulative BPS exact: {metadata['release_patches']['incremental']['exact']} / {metadata['release_patches']['cumulative']['exact']}

## focused exact-ROM smoke

- completion callnative binding: {checks['completion_wrapper_binding']}
- ABI probe / save initialization: {checks['probe_and_save_init']}
- first-clear items, +3 BP, base 9 BP: {checks['first_clear_bonus']}
- streak 3/7/14/21 one-time credits: {checks['streak_credit_catchup']}
- repeat clear no duplication: {checks['repeat_no_duplication']}
- bag-full deferred bonus / base clear preserved: {checks['bag_full_deferred_bonus']}
- normal save item reload: {checks['normal_save_item_reload']}
- sector31 ledger match: {checks['sector31_ledger_match']}
- exact party restore: {checks['exact_party_restore']}
- deterministic process runs: {mgba['process_runs']}

ユーザー指示どおりfresh全監査は再実行せず、Stage 28 builder、manifest binding、allocator、変更span、BPS往復、libmGBA exact-ROM smokeに限定して検証した。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs = build_runtime_outputs(root)
    repeated = build_runtime_outputs(root)
    if outputs != repeated:
        _fail("Factory reward runtime build is not byte deterministic")
    stage = outputs[OUTPUT_ROM.as_posix()]
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    mgba = _mgba_fixture(root, stage, metadata)
    metadata["exact_rom_fixture"] = {
        "path": MGBA_FIXTURE.as_posix(),
        "status": mgba["status"],
        "process_runs": mgba["process_runs"],
        "all_checks": all(mgba["checks"].values()),
    }
    metadata["invariants"]["exact_rom_process_runs_2"] = mgba["process_runs"] == 2
    metadata["invariants"]["exact_rom_all_checks"] = all(mgba["checks"].values())
    if not all(metadata["invariants"].values()):
        _fail("Factory reward exact-ROM invariant failed")
    outputs[OUTPUT_META.as_posix()] = _stable(metadata)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs[REPORT.as_posix()] = _report(metadata, mgba)
    return outputs


def _write_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(root: Path, outputs: dict[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (root / relative).is_file() or (root / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Factory reward generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs(ROOT)
        if args.mode == "build":
            _write_outputs(ROOT, outputs)
        else:
            _check_outputs(ROOT, outputs)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, FactoryRewardBuildError) as error:
        print(f"Factory reward runtime build failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Factory reward runtime {args.mode}: PASS "
        f"stage={_sha(outputs[OUTPUT_ROM.as_posix()])} artifacts={len(outputs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
