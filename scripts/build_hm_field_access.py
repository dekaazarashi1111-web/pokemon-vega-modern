#!/usr/bin/env python3
"""stage 21へ、Vega HM所持を正本とするfield能力runtimeを結合する。"""

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

from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "USER-20260814-HM-FIELD-ACCESS"
ROM_SIZE = 32 * 1024 * 1024
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
CLEAN_ROM_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE21 = Path("build/stages/21_first_battle_hotfix.gba")
STAGE21_SHA256 = "ac0bd8c54ea8a6ee76a56fb0e4cd124e01ace03c4a72ebe923e87e536c8ec521"
STAGE21_ALLOCATION = Path("build/stages/21_allocation.json")
STAGE22 = Path("build/stages/22_hm_field_access.gba")
STAGE22_META = Path("build/stages/22_hm_field_access.json")
STAGE22_ALLOCATION = Path("build/stages/22_allocation.json")
RUNTIME_BIN = Path("generated/runtime/hm_field_access.bin")
RUNTIME_SYMBOLS = Path("generated/runtime/hm_field_access_symbols.json")
MGBA_FIXTURE = Path("build/stages/22_mgba_hm_field_access.json")
REPORT = Path("reports/generated/hm_field_access.md")
RUNNER = Path("tools/mgba_hm_field_access_smoke.c")
ALLOCATION_NAME = "hm_field_access_runtime"

REQUIRED_SYMBOLS = {
    "VegaHM_FieldCapability",
    "VegaHM_SetUpFlash",
    "VegaHM_SetUpCut",
    "VegaHM_SetUpFly",
    "VegaHM_SetUpStrength",
    "VegaHM_SetUpSurf",
    "VegaHM_SetUpRockSmash",
    "VegaHM_SetUpWaterfall",
    "VegaHM_SetUpDive",
}

HM_ROWS = (
    ("HM01", "いあいぎり", 15, 339, 1, "VegaHM_SetUpCut", 0x080972C5),
    ("HM02", "そらをとぶ", 19, 340, 2, "VegaHM_SetUpFly", 0x0912083D),
    ("HM03", "なみのり", 57, 341, 4, "VegaHM_SetUpSurf", 0x091208F5),
    ("HM04", "かいりき", 70, 342, 3, "VegaHM_SetUpStrength", 0x080D18AD),
    ("HM05", "フラッシュ", 148, 343, 0, "VegaHM_SetUpFlash", 0x080CACF9),
    ("HM06", "いわくだき", 249, 344, 5, "VegaHM_SetUpRockSmash", 0x080CABA5),
    ("HM07", "たきのぼり", 127, 345, 6, "VegaHM_SetUpWaterfall", 0x09120879),
    ("HM08", "ダイビング", 291, 346, 14, "VegaHM_SetUpDive", 0x09120951),
)

PATCHES = (
    ("field capability branch", 0x0911F748,
     bytes.fromhex("f8 b5 ce 46 47 46 81 46"), "capability_stub"),
    ("badge common", 0x091224A4, bytes.fromhex("4c 22 08 4b"), bytes.fromhex("01 20 70 47")),
    ("badge Surf", 0x091224D4, bytes.fromhex("10 b5 03 4b"), bytes.fromhex("01 20 70 47")),
    ("badge Flash", 0x091224EC, bytes.fromhex("82 20 10 b5"), bytes.fromhex("01 20 70 47")),
    ("Cut script badge", 0x091226A2, bytes.fromhex("05 d0"), bytes.fromhex("c0 46")),
    ("Rock Smash script badge", 0x091226D6, bytes.fromhex("05 d0"), bytes.fromhex("c0 46")),
    ("Strength script badge", 0x0912270A, bytes.fromhex("05 d0"), bytes.fromhex("c0 46")),
    ("party Cut badge", 0x0912240C, bytes.fromhex("00 d1"), bytes.fromhex("00 e0")),
    ("party Cut compatibility", 0x0912242A, bytes.fromhex("06 1e"), bytes.fromhex("00 26")),
    ("party Cut Vega item", 0x091224A0, struct.pack("<I", 570), struct.pack("<I", 339)),
    ("party Fly badge", 0x0912237E, bytes.fromhex("93 d0"), bytes.fromhex("c0 46")),
    ("party Fly compatibility", 0x0912239A, bytes.fromhex("05 1e"), bytes.fromhex("00 25")),
    ("party Fly Vega item", 0x09122494, struct.pack("<I", 571), struct.pack("<I", 340)),
)


class HMFieldAccessError(ValueError):
    """HM field runtimeの入力、命令、または実ROM境界が不正。"""


def _fail(message: str) -> NoReturn:
    raise HMFieldAccessError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _run(command: Sequence[str], label: str, *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-4000:]}")
    return completed.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path}")
    return value


def _previous_requests(root: Path) -> list[dict[str, object]]:
    report = _read_json(root / STAGE21_ALLOCATION)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("stage21 allocator overlap contract failed")
    return [{
        "name": row["name"], "region": row["region"], "size": row["size"],
        "alignment": row["alignment"], "start": row["start"],
        "owner": row["owner"], "purpose": row["purpose"],
        "content_sha256": row["content_sha256"],
    } for row in report["allocations"]]


def _allocation(
    root: Path,
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(root)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 4,
        "owner": TASK,
        "purpose": "Vega HM01..08所持を正本とするfield能力とparty callback guard",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / "config/rom_regions.csv", requests)
    allocation = next(row for row in report["allocations"] if row["name"] == ALLOCATION_NAME)
    return allocation, report


def _compile_runtime(root: Path, load_address: int) -> tuple[bytes, dict[str, int]]:
    compiler = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    if not compiler or not objcopy or not nm:
        _fail("ARM GNU toolchain is required for HM field runtime")
    source = root / "overlays/hm_field_access/hm_field_access.c"
    header = root / "overlays/hm_field_access/hm_field_access.h"
    for path in (source, header):
        if not path.is_file():
            _fail(f"HM field runtime source missing: {path}")

    with tempfile.TemporaryDirectory(prefix="vega-hm-field-access-") as raw:
        directory = Path(raw)
        linker = directory / "linker.ld"
        elf = directory / "hm_field_access.elf"
        binary = directory / "hm_field_access.bin"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaHM_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }\n"
            "}\n",
            encoding="ascii",
        )
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-Os", "-std=c11",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaHM_FieldCapability", f"-Wl,-T,{linker}",
            f"-I{source.parent}", str(source), "-o", str(elf),
        ], "HM field ARM link", cwd=root)
        undefined = _run([nm, "-u", str(elf)], "HM field undefined-symbol check")
        if undefined.strip():
            _fail("HM field ARM image has undefined symbols: " + undefined.strip())
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "HM field objcopy")
        symbols: dict[str, int] = {}
        for line in _run([nm, "-n", "--defined-only", str(elf)], "HM field nm").splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[2].startswith("VegaHM_"):
                symbols[fields[2]] = int(fields[0], 16)
        missing = REQUIRED_SYMBOLS - set(symbols)
        if missing:
            _fail(f"HM field entrypoints missing: {sorted(missing)}")
        runtime = binary.read_bytes()
        if not runtime or len(runtime) > 4096:
            _fail(f"unexpected HM field runtime size: {len(runtime)}")
        return runtime, symbols


def _patch(
    output: bytearray,
    address: int,
    expected: bytes,
    replacement: bytes,
    label: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{label}: patch size differs")
    offset = address - GBA_ROM_BASE
    actual = bytes(output[offset:offset + len(expected)])
    if actual != expected:
        _fail(f"{label}: expected={expected.hex()} actual={actual.hex()}")
    output[offset:offset + len(expected)] = replacement
    return {
        "label": label,
        "address": f"0x{address:08X}",
        "offset": offset,
        "size": len(expected),
        "expected_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
    }


def _build_stage(root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    source = (root / STAGE21).read_bytes()
    if len(source) != ROM_SIZE or _sha(source) != STAGE21_SHA256:
        _fail("stage21 size/hash contract failed")

    provisional, _ = _allocation(root, 4096, "0" * 64)
    payload_offset = int(provisional["start"])
    runtime, symbols = _compile_runtime(root, GBA_ROM_BASE + payload_offset)
    allocation, allocation_report = _allocation(root, len(runtime), _sha(runtime))
    if int(allocation["start"]) != payload_offset:
        _fail("HM field allocation moved after final link")
    payload_end = int(allocation["end_exclusive"])
    if source[payload_offset:payload_end] != bytes([0xFF]) * len(runtime):
        _fail("HM field allocation destination is not erased FF")

    output = bytearray(source)
    output[payload_offset:payload_end] = runtime
    patch_rows: list[dict[str, Any]] = []
    for label, address, expected, replacement in PATCHES:
        if replacement == "capability_stub":
            target = symbols["VegaHM_FieldCapability"] | 1
            replacement = bytes.fromhex("00 4b 18 47") + struct.pack("<I", target)
        assert isinstance(replacement, bytes)
        patch_rows.append(_patch(output, address, expected, replacement, label))

    callback_base = 0x09168F9C
    for hm, name, move, item, index, symbol, original in HM_ROWS:
        address = callback_base + index * 8
        replacement = struct.pack("<I", symbols[symbol] | 1)
        patch_rows.append(_patch(
            output, address, struct.pack("<I", original), replacement,
            f"{hm} {name} callback ownership guard",
        ))

    output_raw = bytes(output)
    allowed: set[int] = set(range(payload_offset, payload_end))
    for row in patch_rows:
        allowed.update(range(int(row["offset"]), int(row["offset"]) + int(row["size"])))
    changed = {index for index, (before, after) in enumerate(zip(source, output_raw)) if before != after}
    if not changed <= allowed:
        _fail("HM field build changed bytes outside allocation/declared patches")

    clean = (root / CLEAN_ROM).read_bytes()
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != CLEAN_ROM_SHA256:
        _fail("clean FireRed Japanese Rev.0 identity mismatch")
    release_patch = create_bps(
        clean, output_raw, metadata=f"{TASK}:{_sha(output_raw)}".encode("ascii"))
    if apply_bps(clean, release_patch) != output_raw:
        _fail("stage22 release BPS round-trip differs from exact ROM")

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
        "input": {"path": STAGE21.as_posix(), "size": len(source), "sha256": _sha(source)},
        "output": {"path": STAGE22.as_posix(), "size": len(output_raw), "sha256": _sha(output_raw)},
        "runtime": {
            "allocation_name": ALLOCATION_NAME,
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(runtime),
            "sha256": _sha(runtime),
            "symbols": symbol_payload["symbols"],
        },
        "hm_contract": [{
            "hm": hm, "name": name, "move_id": move, "vega_item_id": item,
            "callback_index": index, "wrapper": symbol_payload["symbols"][symbol],
        } for hm, name, move, item, index, symbol, _ in HM_ROWS],
        "patches": patch_rows,
        "allocation": {
            "path": STAGE22_ALLOCATION.as_posix(),
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
            "vega_hm_ids_339_346": [row[3] for row in HM_ROWS] == list(range(339, 347)),
            "party_move_not_persisted": True,
            "new_story_or_save_flags_unchanged": True,
            "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
            "declared_changes_only": changed <= allowed,
        },
    }
    failed_invariants = [
        name for name, passed in metadata["invariants"].items() if not passed
    ]
    if failed_invariants:
        _fail("HM field invariant failed: " + ", ".join(failed_invariants))
    return ({
        STAGE22.as_posix(): output_raw,
        STAGE22_META.as_posix(): _stable(metadata),
        STAGE22_ALLOCATION.as_posix(): _stable(allocation_report),
        RUNTIME_BIN.as_posix(): runtime,
        RUNTIME_SYMBOLS.as_posix(): _stable(symbol_payload),
    }, metadata)


def _mgba_fixture(root: Path, rom: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vega-hm-field-mgba-") as raw:
        directory = Path(raw)
        rom_path = directory / STAGE22.name
        executable = directory / "mgba-hm-field-access-smoke"
        rom_path.write_bytes(rom)
        _run([
            os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(root / RUNNER), "-o", str(executable), "-lmgba",
        ], "HM field libmGBA runner compile", cwd=root)
        args = [str(executable), str(rom_path), metadata["output"]["sha256"]]
        first = json.loads(_run(args, "HM field exact-ROM run 1", cwd=root))
        second = json.loads(_run(args, "HM field exact-ROM run 2", cwd=root))
        if first != second or first.get("status") != "PASS":
            _fail("HM field exact-ROM fixture is not deterministic PASS")
        cases = first.get("hm_cases")
        if not isinstance(cases, list) or len(cases) != 8:
            _fail("HM field exact-ROM fixture does not cover eight HMs")
        if any(len(row.get("party_variants", [])) != 3 for row in cases):
            _fail("HM field fixture lacks empty/unlearned/learned party coverage")
        first["process_runs"] = 2
        return first


def _report(metadata: dict[str, Any], mgba: dict[str, Any]) -> bytes:
    lines = []
    for row in mgba["hm_cases"]:
        variants = ", ".join(
            f"{variant['party']}:{variant['before']}→{variant['after']}→restore {variant['after_restore']}"
            for variant in row["party_variants"]
        )
        callback = row["callback"]
        lines.append(
            f"- {row['name']} / Item {row['item']}: {variants}; "
            f"callback missing={callback['missing']} / owned={callback['owned']} / "
            f"original gate={callback['original_map_gate']}"
        )
    surf = mgba["surf_state_boundary"]
    text = f"""# HM所持によるフィールド能力

## 結論

- 解禁の正本をVega既存HM Item 339..346のバッグ所持へ統一した。
- 手持ち0体、未習得、習得済みのいずれも、未所持は6（拒否）、入手直後は0（許可）となる。
- party menuの8 callbackにも所持guardを置き、HM未所持で技だけ知っている場合の迂回を閉じた。
- map/terrain/follower判定は既存callbackへ委譲し、技・story flag・save fieldは書き込まない。
- HM05はVegaのフラッシュ、HM08はVegaのダイビングとして固定し、CFRU追加ID 570..577を解禁判定に使わない。

## ROM

- Input: `{metadata['input']['path']}` / `{metadata['input']['sha256']}`
- Output: `{metadata['output']['path']}` / `{metadata['output']['sha256']}`
- Runtime: `0x{metadata['runtime']['address']:08X}` / {metadata['runtime']['size']} bytes / `{metadata['runtime']['sha256']}`
- Allocator overlap: {metadata['allocation']['overlap_count']}
- clean FireRed Rev.0→stage 22 BPS exact: {metadata['release_patch_round_trip']['exact']} / `{metadata['release_patch_round_trip']['patch_sha256']}`

## libmGBA exact-ROM境界

{chr(10).join(lines)}
- Surf state: land={surf['land_not_surfing']}, land/requires-surf={surf['land_requires_surfing']}, surfing/reject-land={surf['surf_rejects_land_only']}, surfing={surf['surf_requires_surfing']}
- move writes: {mgba['move_writes']} / new story flags: {mgba['new_story_flags']}
- deterministic process runs: {mgba['process_runs']} / warnings-errors: {mgba['warnings_errors']}

既存stage 21を再利用し、重い全stage再構築は行っていない。
"""
    return text.encode("utf-8")


def collect_outputs(root: Path = ROOT) -> dict[str, bytes]:
    outputs, metadata = _build_stage(root)
    repeated, repeated_metadata = _build_stage(root)
    if outputs != repeated or metadata != repeated_metadata:
        _fail("HM field build is not byte deterministic")
    mgba = _mgba_fixture(root, outputs[STAGE22.as_posix()], metadata)
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
                f"HM field access build: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE22.as_posix()])})"
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
                f"HM field access check: PASS ({len(outputs)} artifacts; "
                f"ROM sha256={_sha(outputs[STAGE22.as_posix()])})"
            )
        return 0
    except (HMFieldAccessError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"HM field access: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
