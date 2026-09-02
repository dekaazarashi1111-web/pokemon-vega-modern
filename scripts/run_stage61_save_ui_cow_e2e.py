#!/usr/bin/env python3
"""Stage61の通常SAVE UI障害・SaveFailed再試行・fresh Continueを実走する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
REPORT_SCHEMA_VERSION = 3
RESULT_SCHEMA_VERSION = 3
REQUIRED_RUNS = 2
CASE = "save_ui_cow_fault_retry_continue"
SOURCE = Path("tools/mgba_stage61_save_ui_cow_e2e.c")
EMBEDDED_SOURCE = Path("tools/mgba_stage61_display_npc_event_e2e.c")
RFU_SOURCE = Path("tools/mgba_stage61_rfu_peripheral.c")
RFU_HEADER = Path("tools/mgba_stage61_rfu_peripheral.h")
ORCHESTRATOR_SOURCE = Path("scripts/run_stage61_save_ui_cow_e2e.py")
DEFAULT_ROM = Path("build/stages/61_display_npc_event_audit.gba")
DEFAULT_METADATA = Path("build/stages/61_display_npc_event_audit.json")
SAVE_SIZE = 131072
PPM_HEADER = b"P6\n240 160\n255\n"
PPM_PIXEL_SIZE = 240 * 160 * 3
FRAMEBUFFER_BYTES_PER_PIXEL = 4
FRAMEBUFFER_BYTE_SIZE = 240 * 160 * FRAMEBUFFER_BYTES_PER_PIXEL
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HEX64 = re.compile(r"[0-9a-f]{16}")
_ADDRESS = re.compile(r"0x[0-9A-Fa-f]{8}")
_EMBEDDED_MAIN = "\nint main(int argc, char **argv)\n{"
_RENAMED_MAIN = (
    "\nint s61_embedded_display_npc_event_main(int argc, char **argv)\n{"
)
_PRODUCT_ARTIFACTS = (
    "save-ui-cow-before.srm",
    "save-ui-cow-fault.srm",
    "save-ui-cow-after.srm",
    "save-ui-cow-retained.srm",
    "save-ui-cow-save-failed.rgba",
    "save-ui-cow-save-failed.ppm",
    "save-ui-cow-hard-continue.rgba",
    "save-ui-cow-hard-continue.ppm",
)
_PROCESS_ARTIFACTS = (
    "save-ui-cow.stdout",
    "save-ui-cow.stderr",
    "save-ui-cow.result.json",
)
_RUN_ARTIFACTS = (*_PRODUCT_ARTIFACTS, *_PROCESS_ARTIFACTS)
_PRODUCT_ROLES = {
    "save-ui-cow-before.srm": "before_save_srm",
    "save-ui-cow-fault.srm": "fault_partial_flash_srm",
    "save-ui-cow-after.srm": "explicit_retry_after_srm",
    "save-ui-cow-retained.srm": "fresh_continue_input_srm",
    "save-ui-cow-save-failed.rgba": "save_failed_raw_framebuffer",
    "save-ui-cow-save-failed.ppm": "save_failed_framebuffer_ppm",
    "save-ui-cow-hard-continue.rgba": "fresh_continue_raw_framebuffer",
    "save-ui-cow-hard-continue.ppm": "fresh_continue_framebuffer_ppm",
}
_PROCESS_ROLES = {
    "save-ui-cow.stdout": "raw_process_stdout",
    "save-ui-cow.stderr": "raw_process_stderr",
    "save-ui-cow.result.json": "canonical_case_result",
}
_ARTIFACT_BASE_KEYS = {
    "path", "size", "sha256", "role", "case",
    "stale_precleared", "atomic_retained",
}
_FRESH_CANARIES = (
    {
        "canary_id": "expanded_flag_18B4",
        "region": "expanded_flags",
        "identifier": 0x18B4,
        "address": "0x0203B2DE",
        "expected_value": 1,
    },
    {
        "canary_id": "expanded_var_5170",
        "region": "expanded_vars",
        "identifier": 0x5170,
        "address": "0x0203B5C8",
        "expected_value": 0x61A5,
    },
    {
        "canary_id": "last_used_ball",
        "region": "last_used_ball",
        "identifier": None,
        "address": "0x0203B6EC",
        "expected_value": 3,
    },
    {
        "canary_id": "player_coins",
        "region": "player_coins",
        "identifier": None,
        "address": "0x0203B78C",
        "expected_value": 0x00054321,
    },
)


class Stage61SaveUiCowError(RuntimeError):
    """検証入力またはmGBA実走契約が一致しない。"""


def _fail(message: str) -> NoReturn:
    raise Stage61SaveUiCowError(message)


def _stable(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, indent=2, sort_keys=True,
    ) + "\n"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fnv64(data: bytes) -> str:
    value = 0x14650FB0739D0383
    for byte in data:
        value ^= byte
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def _framebuffer_fnv64(data: bytes) -> str:
    value = 0xCBF29CE484222325
    for byte in data:
        value ^= byte
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def _path(value: Path) -> Path:
    return value if value.is_absolute() else ROOT / value


def _atomic_write_bytes(destination: Path, raw: bytes) -> None:
    temporary_path: Path | None = None
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=destination.name + ".", suffix=".tmp",
            dir=destination.parent, delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(raw)
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _remove_exact_file(path: Path, label: str) -> bool:
    if path.is_symlink():
        _fail(f"{label}はsymlinkです")
    if path.is_file():
        path.unlink()
        return True
    if path.exists():
        _fail(f"{label}は通常fileではありません")
    return False


def _artifact_descriptor(
    path: Path, *, role: str, stale_precleared: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        _fail(f"retained artifactが通常fileではありません: {path.name}")
    raw = path.read_bytes()
    descriptor: dict[str, Any] = {
        "path": str(path.resolve()),
        "size": len(raw),
        "sha256": _sha256(raw),
        "role": role,
        "case": CASE,
        "stale_precleared": stale_precleared,
        "atomic_retained": True,
    }
    if extra is not None:
        if set(extra) & set(descriptor):
            _fail("retained artifact extra keyがbase identityと衝突")
        descriptor.update(extra)
    return descriptor


def _atomic_retain_bytes(
    work: Path, name: str, raw: bytes, *, role: str,
    stale_precleared: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if Path(name).name != name or name in {"", ".", ".."}:
        _fail("retained artifact name不正")
    destination = work / name
    if destination.is_symlink():
        _fail(f"retained artifactはsymlinkです: {name}")
    _atomic_write_bytes(destination, raw)
    descriptor = _artifact_descriptor(
        destination, role=role, stale_precleared=stale_precleared,
        extra=extra,
    )
    if destination.read_bytes() != raw:
        _fail(f"retained artifact atomic再読不一致: {name}")
    return descriptor


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"{label}を読めません: {error}")
    if not isinstance(value, Mapping):
        _fail(f"{label} rootはobjectではありません")
    return value


def _build_embedded_harness(destination: Path) -> dict[str, Any]:
    source = ROOT / EMBEDDED_SOURCE
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"embedded harnessを読めません: {error}")
    if text.count(_EMBEDDED_MAIN) != 1:
        _fail("embedded harnessのmain定義が一意ではありません")
    transformed = text.replace(_EMBEDDED_MAIN, _RENAMED_MAIN, 1)
    destination.write_text(transformed, encoding="utf-8", newline="\n")
    return {
        "source": str(EMBEDDED_SOURCE),
        "source_sha256": _sha256(text.encode("utf-8")),
        "transformed_sha256": _sha256(transformed.encode("utf-8")),
        "main_renamed": True,
        "other_bytes_unchanged": True,
    }


def _compile(executable: Path) -> dict[str, Any]:
    compiler = shutil.which("cc")
    source = ROOT / SOURCE
    rfu_source = ROOT / RFU_SOURCE
    rfu_header = ROOT / RFU_HEADER
    missing = [
        str(path) for path in (source, rfu_source, rfu_header)
        if not path.is_file()
    ]
    if compiler is None or missing:
        _fail(f"mGBA compile前提不足: cc={compiler}, missing={missing}")
    executable.parent.mkdir(parents=True, exist_ok=True)
    embedded = executable.parent / "stage61-embedded-harness.c"
    embedded_identity = _build_embedded_harness(embedded)
    define = f'-DS61_SAVE_UI_EMBEDDED_HARNESS="{embedded}"'
    command = [
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-pedantic", f"-I{ROOT / 'tools'}", define, str(source),
        str(rfu_source), "-o", str(executable), "-lmgba",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=120, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        detail = completed.stderr or completed.stdout or str(completed.returncode)
        _fail("Stage61 save UI COW runner compile失敗: " + detail[-6000:])
    return {
        "status": "PASS",
        "source": str(SOURCE),
        "source_sha256": _sha256(source.read_bytes()),
        "rfu_source": str(RFU_SOURCE),
        "rfu_source_sha256": _sha256(rfu_source.read_bytes()),
        "rfu_header": str(RFU_HEADER),
        "rfu_header_sha256": _sha256(rfu_header.read_bytes()),
        "embedded_harness": embedded_identity,
        "command": (
            "cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic "
            "-I<tools> -DS61_SAVE_UI_EMBEDDED_HARNESS=<generated> "
            "<source> -o <runner> -lmgba"
        ),
        "stdout_empty": True,
        "stderr_empty": True,
    }


def read_identity(
    rom_path: Path, metadata_path: Path,
    expected_rom_sha256: str | None = None,
) -> dict[str, Any]:
    rom = _path(rom_path)
    metadata_file = _path(metadata_path)
    try:
        raw = rom.read_bytes()
    except OSError as error:
        _fail(f"Stage61 ROMを読めません: {error}")
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage61 ROM size不一致: {len(raw)}")
    digest = _sha256(raw)
    if expected_rom_sha256 is not None:
        if _SHA256.fullmatch(expected_rom_sha256) is None:
            _fail("--expected-rom-sha256はlowercase SHA-256ではありません")
        if digest != expected_rom_sha256:
            _fail("Stage61 ROM hashが明示pinと一致しません")

    metadata = _read_json(metadata_file, "Stage61 metadata")
    if metadata.get("schema_version") != 1 \
            or metadata.get("stage") != STAGE \
            or metadata.get("task") != TASK \
            or metadata.get("status") != "PASS":
        _fail("Stage61 metadata identity不一致")
    output = metadata.get("output")
    if not isinstance(output, Mapping) \
            or output.get("size") != len(raw) \
            or output.get("sha256") != digest:
        _fail("Stage61 metadata output identity不一致")
    output_path = output.get("path")
    if not isinstance(output_path, str) \
            or _path(Path(output_path)).resolve() != rom.resolve():
        _fail("Stage61 metadata output path不一致")

    audit = metadata.get("audit")
    persistent = audit.get("persistent_state_compatibility") \
        if isinstance(audit, Mapping) else None
    normal = persistent.get("normal_save_copy_on_write") \
        if isinstance(persistent, Mapping) else None
    link = persistent.get("link_save_record_commit") \
        if isinstance(persistent, Mapping) else None
    transaction = link.get("record_only_transaction") \
        if isinstance(link, Mapping) else None
    if not isinstance(link, Mapping) \
            or link.get("save_type") != "SAVE_LINK_ONLY_1" \
            or link.get("stock_damaged_side_channel_normalized_to_error") \
                is not True \
            or link.get("runtime_symbol") != "Stage61State_HandleSavingData" \
            or not isinstance(transaction, Mapping) \
            or transaction.get("invariant") \
                != "AT_LEAST_ONE_COMPLETE_GENERATION_ALWAYS":
        _fail("Stage61 metadata COW/SaveFailed前提不一致")
    if not isinstance(normal, Mapping) \
            or normal.get("save_type") != "SAVE_NORMAL_ONLY_0" \
            or normal.get("runtime_symbol") \
                != "Stage61State_HandleSavingData" \
            or normal.get("stock_handle_saving_data_delegated") is not False \
            or normal.get("stock_try_write_sector_used") is not False \
            or normal.get("protected_bank_flash_policy") \
                != "READ_ONLY_BYTE_EXACT" \
            or normal.get("preinvalidation_callback_failure_is_not_ignored") \
                is not True \
            or normal.get("save_failed_screen_wipe_retry_mgba_required") \
                is not True \
            or normal.get("natural_start_menu_second_retry_mgba_required") \
                is not True \
            or normal.get("fresh_core_continue_mgba_required") is not True:
        _fail("Stage61 metadata SAVE_NORMAL COW契約不一致")
    direct_callers = link.get("direct_callers")
    if not isinstance(direct_callers, list) or not any(
        isinstance(item, Mapping) and item.get("address") == "0x080F64C4"
        for item in direct_callers
    ):
        _fail("Stage61 metadata SaveFailed retry caller不一致")
    runtime = metadata.get("runtime")
    symbols = runtime.get("symbols") if isinstance(runtime, Mapping) else None
    handle_saving_data = symbols.get("Stage61State_HandleSavingData") \
        if isinstance(symbols, Mapping) else None
    if isinstance(handle_saving_data, bool) \
            or not isinstance(handle_saving_data, int) \
            or not 0x09000000 <= handle_saving_data < 0x0A000000:
        _fail("Stage61 metadata HandleSavingData symbol不一致")
    return {
        "rom": str(rom.resolve()),
        "rom_size": len(raw),
        "rom_sha256": digest,
        "metadata": str(metadata_file.resolve()),
        "metadata_sha256": _sha256(metadata_file.read_bytes()),
        "cow_runtime_symbol": link["runtime_symbol"],
        "normal_save_copy_on_write": True,
        "handle_saving_data": handle_saving_data,
        "save_failed_retry_caller": "0x080F64C4",
    }


def _require_keys(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(f"mGBA result {label} keys不一致")
    return value


def _require_true(value: Mapping[str, Any], keys: Sequence[str], label: str) -> None:
    for key in keys:
        if value.get(key) is not True:
            _fail(f"mGBA result {label}.{key}はtrueではありません")


def _snapshot(work_dir: Path, name: Any, label: str) -> tuple[Path, bytes]:
    if not isinstance(name, str) or Path(name).name != name \
            or name in {"", ".", ".."}:
        _fail(f"mGBA result {label} path不正")
    path = work_dir / name
    if path.is_symlink():
        _fail(f"mGBA result {label}はsymlinkです")
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"mGBA result {label}を読めません: {error}")
    if len(raw) != SAVE_SIZE:
        _fail(f"mGBA result {label} size不一致: {len(raw)}")
    return path.resolve(), raw


def _screen_snapshot(
    work_dir: Path, ppm_name: Any, framebuffer_name: Any,
) -> dict[str, Any]:
    for name, label in (
        (ppm_name, "PPM artifact"),
        (framebuffer_name, "raw framebuffer"),
    ):
        if not isinstance(name, str) or Path(name).name != name \
                or name in {"", ".", ".."}:
            _fail(f"mGBA result SaveFailed {label} path不正")
    path = work_dir / ppm_name
    framebuffer_path = work_dir / framebuffer_name
    if path.is_symlink() or framebuffer_path.is_symlink():
        _fail("mGBA result SaveFailed screen artifactはsymlinkです")
    try:
        raw = path.read_bytes()
        framebuffer = framebuffer_path.read_bytes()
    except OSError as error:
        _fail(f"mGBA result SaveFailed screen artifactを読めません: {error}")
    if len(raw) != len(PPM_HEADER) + PPM_PIXEL_SIZE \
            or not raw.startswith(PPM_HEADER):
        _fail("mGBA result SaveFailed artifact PPM shape不一致")
    if len(framebuffer) != FRAMEBUFFER_BYTE_SIZE:
        _fail("mGBA result SaveFailed raw framebuffer size不一致")
    pixels = raw[len(PPM_HEADER):]
    expected_pixels = b"".join(
        framebuffer[index:index + 3]
        for index in range(0, len(framebuffer), FRAMEBUFFER_BYTES_PER_PIXEL)
    )
    if pixels != expected_pixels:
        _fail("mGBA result SaveFailed PPM/raw framebuffer変換不一致")
    return {
        "ppm": {
            "path": str(path.resolve()),
            "size": len(raw),
            "sha256": _sha256(raw),
        },
        "raw_framebuffer": {
            "path": str(framebuffer_path.resolve()),
            "size": len(framebuffer),
            "sha256": _sha256(framebuffer),
            "fnv64": _framebuffer_fnv64(framebuffer),
            "width": 240,
            "height": 160,
            "bytes_per_pixel": FRAMEBUFFER_BYTES_PER_PIXEL,
            "byte_order": "little",
        },
        "pixel_fnv64": _fnv64(pixels),
        "ppm_exact_from_raw_framebuffer": True,
    }


def _ppm_snapshot(work_dir: Path, name: Any, label: str) -> dict[str, Any]:
    if not isinstance(name, str) or Path(name).name != name \
            or name in {"", ".", ".."}:
        _fail(f"mGBA result {label} path不正")
    path = work_dir / name
    if path.is_symlink():
        _fail(f"mGBA result {label}はsymlinkです")
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"mGBA result {label}を読めません: {error}")
    if len(raw) != len(PPM_HEADER) + PPM_PIXEL_SIZE \
            or not raw.startswith(PPM_HEADER):
        _fail(f"mGBA result {label} PPM shape不一致")
    pixels = raw[len(PPM_HEADER):]
    if len(set(pixels)) < 2:
        _fail(f"mGBA result {label}は一様画面です")
    return {
        "path": str(path.resolve()),
        "size": len(raw),
        "sha256": _sha256(raw),
        "pixel_fnv64": _fnv64(pixels),
        "width": 240,
        "height": 160,
    }


def validate_c_result(value: Any, work_dir: Path) -> dict[str, Any]:
    root = _require_keys(value, {
        "schema_version", "status", "case", "natural_input",
        "engine_trace", "fault", "save_failed_screen", "explicit_retry",
        "hard_restart", "srm", "preparation_only_host_writes",
        "direct_owner_or_script_calls", "failed", "untested", "warnings",
    }, "root")
    if root["schema_version"] != RESULT_SCHEMA_VERSION \
            or root["status"] != "PASS" \
            or root["case"] != CASE \
            or root["preparation_only_host_writes"] is not True \
            or root["direct_owner_or_script_calls"] != 0 \
            or root["failed"] != 0 \
            or root["untested"] != 0 \
            or root["warnings"] != 0:
        _fail("mGBA result root status不一致")

    natural = _require_keys(root["natural_input"], {
        "start_pressed", "save_action_selected", "confirmation_pulses",
        "host_direct_save_callback",
    }, "natural_input")
    _require_true(natural, ("start_pressed", "save_action_selected"),
                  "natural_input")
    if natural["host_direct_save_callback"] is not False \
            or not isinstance(natural["confirmation_pulses"], int) \
            or isinstance(natural["confirmation_pulses"], bool) \
            or not 1 <= natural["confirmation_pulses"] <= 32:
        _fail("mGBA result natural input/direct-call契約不一致")

    engine = _require_keys(root["engine_trace"], {
        "save_serialized_game", "save_serialized_game_hits_before_fault",
        "update_save_addresses", "update_save_addresses_hits_before_fault",
        "handle_saving_data_hits_before_fault", "save_data_buffer",
        "save_data_buffer_stable",
    }, "engine_trace")
    _require_true(engine, ("save_data_buffer_stable",), "engine_trace")
    buffer_pointer = engine.get("save_data_buffer")
    if engine["save_serialized_game"] != "0x0804BAB8" \
            or engine["save_serialized_game_hits_before_fault"] != 1 \
            or engine["update_save_addresses"] != "0x080DB1BC" \
            or engine["update_save_addresses_hits_before_fault"] != 1 \
            or engine["handle_saving_data_hits_before_fault"] != 1 \
            or not isinstance(buffer_pointer, str) \
            or _ADDRESS.fullmatch(buffer_pointer) is None \
            or not 0x02000000 <= int(buffer_pointer, 16) < 0x02040000:
        _fail("mGBA result serialization/buffer owner trace不一致")

    fault = _require_keys(root["fault"], {
        "callback", "real_flash_callback_executed",
        "status_injected_at_real_return", "fault_callback_hits",
        "partial_flash_side_effect", "changed_bytes", "phase",
        "normal_save_type", "physical_sector", "damaged_mask_before_wipe",
        "protected_slot", "protected_counter",
        "protected_generation_exact", "damaged_generation_incomplete",
    }, "fault")
    _require_true(fault, (
        "real_flash_callback_executed", "status_injected_at_real_return",
        "partial_flash_side_effect", "protected_generation_exact",
        "damaged_generation_incomplete",
    ), "fault")
    if fault["callback"] != "0x081C2E90" \
            or fault["fault_callback_hits"] != 1 \
            or fault["phase"] not in {"NORMAL_COW", "STOCK"} \
            or fault["normal_save_type"] != 0 \
            or not isinstance(fault["physical_sector"], int) \
            or isinstance(fault["physical_sector"], bool) \
            or not 0 <= fault["physical_sector"] < 32 \
            or not isinstance(fault["changed_bytes"], int) \
            or isinstance(fault["changed_bytes"], bool) \
            or not 1 <= fault["changed_bytes"] <= SAVE_SIZE \
            or not isinstance(fault["damaged_mask_before_wipe"], int) \
            or isinstance(fault["damaged_mask_before_wipe"], bool) \
            or not 1 <= fault["damaged_mask_before_wipe"] <= 0xFFFFFFFF \
            or fault["protected_slot"] not in (0, 1) \
            or not isinstance(fault["protected_counter"], int) \
            or isinstance(fault["protected_counter"], bool) \
            or not 0 <= fault["protected_counter"] <= 0xFFFFFFFF:
        _fail("mGBA result flash fault契約不一致")

    screen = _require_keys(root["save_failed_screen"], {
        "real_owner_observed", "state5_observed", "framebuffer_hash",
        "framebuffer_raw_path", "artifact_path", "artifact_pixel_fnv64",
        "owner_state_trace",
        "damaged_generation_wiped", "retry_completed", "attempt_status",
        "state6_success_observed", "retry_acknowledged_with_a",
        "field_input_recovered",
    }, "save_failed_screen")
    _require_true(screen, (
        "real_owner_observed", "state5_observed",
        "damaged_generation_wiped", "retry_completed",
        "state6_success_observed", "retry_acknowledged_with_a",
        "field_input_recovered",
    ), "save_failed_screen")
    if screen["attempt_status"] != 1 \
            or not isinstance(screen["framebuffer_hash"], str) \
            or _HEX64.fullmatch(screen["framebuffer_hash"]) is None \
            or not isinstance(screen["artifact_pixel_fnv64"], str) \
            or _HEX64.fullmatch(screen["artifact_pixel_fnv64"]) is None:
        _fail("mGBA result SaveFailed screen結果不一致")
    trace = screen["owner_state_trace"]
    if not isinstance(trace, list) or len(trace) != 2:
        _fail("mGBA result SaveFailed owner state trace件数不一致")
    for sequence, expected_state in enumerate((5, 6)):
        observation = _require_keys(trace[sequence], {
            "sequence", "pc", "state_address", "state",
            "active_address", "active",
        }, f"save_failed_screen.owner_state_trace[{sequence}]")
        pc = observation["pc"]
        if observation["sequence"] != sequence \
                or observation["state_address"] != "0x0203AAC8" \
                or observation["state"] != expected_state \
                or observation["active_address"] != "0x03005480" \
                or not isinstance(observation["active"], int) \
                or isinstance(observation["active"], bool) \
                or observation["active"] == 0 \
                or not isinstance(pc, str) \
                or _ADDRESS.fullmatch(pc) is None \
                or not 0x080F6160 <= int(pc, 16) < 0x080F6500:
            _fail("mGBA result SaveFailed owner state trace不一致")
    screen_artifact = _screen_snapshot(
        work_dir.resolve(), screen["artifact_path"],
        screen["framebuffer_raw_path"],
    )
    if Path(screen_artifact["ppm"]["path"]).parent != work_dir.resolve() \
            or Path(screen_artifact["raw_framebuffer"]["path"]).parent \
                != work_dir.resolve() \
            or screen_artifact["pixel_fnv64"] \
                != screen["artifact_pixel_fnv64"] \
            or screen_artifact["raw_framebuffer"]["fnv64"] \
                != screen["framebuffer_hash"]:
        _fail("mGBA result SaveFailed artifact readback不一致")

    explicit = _require_keys(root["explicit_retry"], {
        "start_menu_save_with_keys", "counter_before", "counter_after",
        "full_generation_complete",
    }, "explicit_retry")
    _require_true(explicit, (
        "start_menu_save_with_keys", "full_generation_complete",
    ), "explicit_retry")
    for key in ("counter_before", "counter_after"):
        if not isinstance(explicit[key], int) \
                or isinstance(explicit[key], bool) \
                or not 0 <= explicit[key] <= 0xFFFFFFFF:
            _fail(f"mGBA result explicit_retry.{key}不正")
    if explicit["counter_before"] \
            != (fault["protected_counter"] + 1) & 0xFFFFFFFF \
            or explicit["counter_after"] \
            != (explicit["counter_before"] + 1) & 0xFFFFFFFF:
        _fail("mGBA result retry counter chain不一致")

    restart = _require_keys(root["hard_restart"], {
        "old_core_closed", "fresh_core_opened", "title_continue", "counter",
        "field_input_recovered", "canaries_restored", "canary_count",
        "canaries", "location", "input_liveness", "framebuffer_hash",
        "framebuffer_raw_path", "artifact_path", "artifact_pixel_fnv64",
    }, "hard_restart")
    _require_true(restart, (
        "old_core_closed", "fresh_core_opened", "title_continue",
        "field_input_recovered", "canaries_restored",
    ), "hard_restart")
    if restart["counter"] != explicit["counter_after"]:
        _fail("mGBA result hard restart counter不一致")
    location = _require_keys(restart["location"], {
        "map_group", "map_number", "x", "y", "warp_id",
    }, "hard_restart.location")
    if location["map_group"] != 96 or location["map_number"] != 5 \
            or location["x"] != 20 or location["y"] != 20 \
            or isinstance(location["warp_id"], bool) \
            or not isinstance(location["warp_id"], int) \
            or not 0 <= location["warp_id"] <= 0xFF:
        _fail("mGBA result hard restart map/position不一致")
    input_liveness = _require_keys(restart["input_liveness"], {
        "start_pressed", "start_menu_opened", "menu_callback_observed",
        "back_pressed", "callback_ordered", "map_preserved",
        "position_preserved", "field_terminal", "field_input_recovered",
        "location_before", "location_after",
    }, "hard_restart.input_liveness")
    _require_true(input_liveness, (
        "start_pressed", "start_menu_opened", "back_pressed",
        "callback_ordered", "map_preserved", "position_preserved",
        "field_terminal", "field_input_recovered",
    ), "hard_restart.input_liveness")
    if input_liveness["menu_callback_observed"] != "0x0806EA75" \
            or restart["field_input_recovered"] \
                is not input_liveness["field_input_recovered"]:
        _fail("mGBA result hard restart実入力callback契約不一致")
    for phase in ("location_before", "location_after"):
        observed_location = _require_keys(input_liveness[phase], {
            "map_group", "map_number", "x", "y", "warp_id",
        }, f"hard_restart.input_liveness.{phase}")
        if dict(observed_location) != dict(location):
            _fail(
                "mGBA result hard restart実入力前後のmap/position不一致"
            )
    continue_artifact = _screen_snapshot(
        work_dir.resolve(), restart["artifact_path"],
        restart["framebuffer_raw_path"],
    )
    if not isinstance(restart["framebuffer_hash"], str) \
            or _HEX64.fullmatch(restart["framebuffer_hash"]) is None \
            or not isinstance(restart["artifact_pixel_fnv64"], str) \
            or _HEX64.fullmatch(restart["artifact_pixel_fnv64"]) is None \
            or continue_artifact["pixel_fnv64"] \
                != restart["artifact_pixel_fnv64"] \
            or continue_artifact["raw_framebuffer"]["fnv64"] \
                != restart["framebuffer_hash"]:
        _fail("mGBA result hard Continue framebuffer readback不一致")
    canaries = restart["canaries"]
    if restart["canary_count"] != len(_FRESH_CANARIES) \
            or not isinstance(canaries, list) \
            or len(canaries) != len(_FRESH_CANARIES):
        _fail("mGBA result hard restart canary件数不一致")
    normalized_canaries: list[dict[str, Any]] = []
    for index, expected in enumerate(_FRESH_CANARIES):
        canary = _require_keys(canaries[index], {
            "canary_id", "region", "identifier", "address",
            "expected_value", "observed_value",
        }, f"hard_restart.canaries[{index}]")
        for key, expected_value in expected.items():
            if canary[key] != expected_value:
                _fail(f"mGBA result hard restart canary {key}不一致")
        if not isinstance(canary["expected_value"], int) \
                or isinstance(canary["expected_value"], bool) \
                or not isinstance(canary["observed_value"], int) \
                or isinstance(canary["observed_value"], bool) \
                or canary["observed_value"] != expected["expected_value"]:
            _fail("mGBA result hard restart canary observed/expected不一致")
        normalized_canaries.append(dict(canary))

    srm = _require_keys(root["srm"], {
        "size", "before_path", "fault_path", "after_path", "retained_path",
        "before_fnv64", "fault_fnv64", "after_fnv64",
    }, "srm")
    if srm["size"] != SAVE_SIZE:
        _fail("mGBA result SRM declared size不一致")
    resolved_work = work_dir.resolve()
    before_path, before = _snapshot(resolved_work, srm["before_path"],
                                    "srm.before")
    fault_path, fault_bytes = _snapshot(
        resolved_work, srm["fault_path"], "srm.fault",
    )
    after_path, after = _snapshot(resolved_work, srm["after_path"],
                                  "srm.after")
    retained_path, retained = _snapshot(
        resolved_work, srm["retained_path"], "srm.retained",
    )
    if before_path.parent != resolved_work \
            or fault_path.parent != resolved_work \
            or after_path.parent != resolved_work \
            or retained_path.parent != resolved_work:
        _fail("mGBA result SRM pathがwork directory外です")
    if not isinstance(srm["before_fnv64"], str) \
            or not isinstance(srm["fault_fnv64"], str) \
            or not isinstance(srm["after_fnv64"], str) \
            or _HEX64.fullmatch(srm["before_fnv64"]) is None \
            or _HEX64.fullmatch(srm["fault_fnv64"]) is None \
            or _HEX64.fullmatch(srm["after_fnv64"]) is None \
            or srm["before_fnv64"] != _fnv64(before) \
            or srm["fault_fnv64"] != _fnv64(fault_bytes) \
            or srm["after_fnv64"] != _fnv64(after):
        _fail("mGBA result SRM FNV readback不一致")
    external_changed_bytes = sum(
        left != right for left, right in zip(before, fault_bytes)
    )
    if external_changed_bytes != fault["changed_bytes"]:
        _fail("mGBA result fault SRM changed-byte readback不一致")
    if before == after:
        _fail("mGBA result before/after SRMが同一です")
    if after != retained:
        _fail("mGBA result retained SRMがafter snapshotと異なります")

    normalized = deepcopy(dict(root))
    normalized["save_failed_screen"] = deepcopy(dict(screen))
    normalized["save_failed_screen"]["artifact"] = screen_artifact
    del normalized["save_failed_screen"]["artifact_path"]
    del normalized["save_failed_screen"]["framebuffer_raw_path"]
    del normalized["save_failed_screen"]["artifact_pixel_fnv64"]
    normalized["hard_restart"] = deepcopy(dict(restart))
    normalized["hard_restart"]["canaries"] = normalized_canaries
    normalized["hard_restart"]["framebuffer_artifact"] = continue_artifact
    del normalized["hard_restart"]["framebuffer_hash"]
    del normalized["hard_restart"]["framebuffer_raw_path"]
    del normalized["hard_restart"]["artifact_path"]
    del normalized["hard_restart"]["artifact_pixel_fnv64"]
    normalized["srm"] = {
        "size": SAVE_SIZE,
        "before": {
            "path": str(before_path), "size": len(before),
            "sha256": _sha256(before), "fnv64": _fnv64(before),
        },
        "fault": {
            "path": str(fault_path), "size": len(fault_bytes),
            "sha256": _sha256(fault_bytes), "fnv64": _fnv64(fault_bytes),
            "changed_bytes_from_before": external_changed_bytes,
        },
        "after": {
            "path": str(after_path), "size": len(after),
            "sha256": _sha256(after), "fnv64": _fnv64(after),
        },
        "retained": {
            "path": str(retained_path), "size": len(retained),
            "sha256": _sha256(retained), "fnv64": _fnv64(retained),
        },
        "before_after_different": True,
        "after_retained_exact": True,
    }
    return normalized


def _parse_process_stdout(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail(f"{label} stdout UTF-8不正: {error}")
    if not text.endswith("\n") or text.count("\n") != 1 or not text[:-1]:
        _fail(f"{label} stdoutはexact 1行JSONではありません")
    try:
        value = json.loads(text[:-1])
    except json.JSONDecodeError as error:
        _fail(f"{label} stdout JSON不正: {error}")
    if not isinstance(value, Mapping):
        _fail(f"{label} stdout JSON rootはobjectではありません")
    return value


def _retain_process_evidence(
    work: Path, *, stdout: bytes, stderr: bytes, result: Mapping[str, Any],
) -> dict[str, Any]:
    records = {
        _PROCESS_ARTIFACTS[0]: _atomic_retain_bytes(
            work, _PROCESS_ARTIFACTS[0], stdout,
            role="raw_process_stdout",
        ),
        _PROCESS_ARTIFACTS[1]: _atomic_retain_bytes(
            work, _PROCESS_ARTIFACTS[1], stderr,
            role="raw_process_stderr",
        ),
    }
    parsed = _parse_process_stdout(stdout, CASE)
    try:
        stderr.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail(f"{CASE} stderr UTF-8不正: {error}")
    if stderr:
        _fail("Stage61 save UI COW mGBA stderr非空")
    canonical = _stable(dict(result)).encode("utf-8")
    if parsed != result or json.loads(canonical) != result:
        _fail("save UI COW stdout result/canonical result不一致")
    records[_PROCESS_ARTIFACTS[2]] = _atomic_retain_bytes(
        work, _PROCESS_ARTIFACTS[2], canonical,
        role="canonical_case_result",
    )
    return {
        "stdout_result_matches_canonical": True,
        "stderr_empty": True,
        "raw_stdout": _PROCESS_ARTIFACTS[0],
        "raw_stderr": _PROCESS_ARTIFACTS[1],
        "canonical_case_result": _PROCESS_ARTIFACTS[2],
        "raw_stdout_sha256": records[_PROCESS_ARTIFACTS[0]]["sha256"],
        "canonical_result_sha256": records[_PROCESS_ARTIFACTS[2]]["sha256"],
        "artifacts": records,
    }


def _prepare_work(path: Path) -> Path:
    work = _path(path)
    if work.is_symlink() or (work.exists() and not work.is_dir()):
        _fail("work directoryは実directoryである必要があります")
    work.mkdir(parents=True, exist_ok=True)
    allowed = {f"run-{index}" for index in range(1, REQUIRED_RUNS + 1)}
    unknown = sorted(entry.name for entry in work.iterdir()
                     if entry.name not in allowed)
    if unknown:
        _fail(f"work directoryに未知の既存entryがあります: {unknown}")
    return work.resolve()


def _prepare_run_work(work: Path, run_index: int) -> tuple[Path, int]:
    if run_index not in range(1, REQUIRED_RUNS + 1):
        _fail("save UI COW run index不正")
    parent = work / f"run-{run_index}"
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        _fail("save UI COW run parentは実directoryではありません")
    parent.mkdir(parents=True, exist_ok=True)
    unknown_parent = sorted(
        entry.name for entry in parent.iterdir() if entry.name != CASE
    )
    if unknown_parent:
        _fail(f"save UI COW run parentに未知entryがあります: {unknown_parent}")
    directory = parent / CASE
    if directory.is_symlink() \
            or (directory.exists() and not directory.is_dir()):
        _fail("save UI COW run workは実directoryではありません")
    directory.mkdir(parents=True, exist_ok=True)
    unknown = sorted(entry.name for entry in directory.iterdir()
                     if entry.name not in set(_RUN_ARTIFACTS))
    if unknown:
        _fail(f"save UI COW run workに未知entryがあります: {unknown}")
    removed = sum(
        _remove_exact_file(directory / name, f"stale artifact {name}")
        for name in _RUN_ARTIFACTS
    )
    if any(directory.iterdir()):
        _fail("save UI COW run workをprocess前に空にできません")
    return directory.resolve(), removed


def _product_artifacts(work: Path) -> dict[str, dict[str, Any]]:
    artifacts: dict[str, dict[str, Any]] = {}
    for name in _PRODUCT_ARTIFACTS:
        path = work / name
        if path.is_symlink() or not path.is_file():
            _fail(f"save UI COW product artifact欠落: {name}")
        raw = path.read_bytes()
        extra: dict[str, Any]
        if name.endswith(".srm"):
            if len(raw) != SAVE_SIZE:
                _fail(f"save UI COW SRM size不一致: {name}")
            extra = {"fnv64": _fnv64(raw)}
        elif name.endswith(".rgba"):
            if len(raw) != FRAMEBUFFER_BYTE_SIZE:
                _fail("save UI COW raw framebuffer size不一致")
            extra = {
                "framebuffer_fnv1a64": _framebuffer_fnv64(raw),
                "framebuffer_role": (
                    "save_failed_state5" if "save-failed" in name
                    else "fresh_continue_field"
                ),
            }
        else:
            if len(raw) != len(PPM_HEADER) + PPM_PIXEL_SIZE \
                    or not raw.startswith(PPM_HEADER):
                _fail(f"save UI COW PPM shape不一致: {name}")
            pixels = raw[len(PPM_HEADER):]
            extra = {
                "rgb_fnv1a64": _fnv64(pixels),
                "framebuffer_role": (
                    "save_failed_state5" if "save-failed" in name
                    else "fresh_continue_field"
                ),
            }
        artifacts[name] = _atomic_retain_bytes(
            work, name, raw, role=_PRODUCT_ROLES[name], extra=extra,
        )
    return artifacts


def _validate_run_artifact_closure(
    work: Path, artifacts: Mapping[str, Mapping[str, Any]],
) -> None:
    expected_names = set(_RUN_ARTIFACTS)
    actual_names = {path.name for path in work.iterdir()}
    if set(artifacts) != expected_names or actual_names != expected_names \
            or len(artifacts) != 11:
        _fail("save UI COW retained artifact closureはexact 11件ではありません")
    resolved_paths: set[Path] = set()
    for name in _RUN_ARTIFACTS:
        descriptor = artifacts[name]
        extra_keys: set[str] = set()
        if name.endswith(".srm"):
            extra_keys = {"fnv64"}
        elif name.endswith(".ppm"):
            extra_keys = {"rgb_fnv1a64", "framebuffer_role"}
        elif name.endswith(".rgba"):
            extra_keys = {"framebuffer_fnv1a64", "framebuffer_role"}
        expected_keys = _ARTIFACT_BASE_KEYS | extra_keys
        if not isinstance(descriptor, Mapping) \
                or set(descriptor) != expected_keys:
            _fail(f"save UI COW artifact leaf schema不一致: {name}")
        expected_role = (
            _PRODUCT_ROLES[name] if name in _PRODUCT_ROLES
            else _PROCESS_ROLES[name]
        )
        declared_path = descriptor.get("path")
        if not isinstance(declared_path, str):
            _fail(f"save UI COW artifact path不正: {name}")
        path = Path(declared_path)
        try:
            resolved = path.resolve(strict=True)
            raw = resolved.read_bytes()
        except OSError as error:
            _fail(f"save UI COW artifact再読失敗 {name}: {error}")
        if not path.is_absolute() or path.is_symlink() \
                or resolved != (work / name).resolve() \
                or descriptor.get("size") != len(raw) \
                or descriptor.get("sha256") != _sha256(raw) \
                or descriptor.get("role") != expected_role \
                or descriptor.get("case") != CASE \
                or descriptor.get("stale_precleared") is not True \
                or descriptor.get("atomic_retained") is not True:
            _fail(f"save UI COW artifact identity/readback不一致: {name}")
        if name.endswith(".srm") \
                and descriptor.get("fnv64") != _fnv64(raw):
            _fail(f"save UI COW SRM FNV不一致: {name}")
        if name.endswith(".ppm"):
            if not raw.startswith(PPM_HEADER) \
                    or descriptor.get("rgb_fnv1a64") \
                        != _fnv64(raw[len(PPM_HEADER):]) \
                    or descriptor.get("framebuffer_role") not in {
                        "save_failed_state5", "fresh_continue_field",
                    }:
                _fail(f"save UI COW PPM RGB role/FNV不一致: {name}")
        if name.endswith(".rgba") \
                and (descriptor.get("framebuffer_fnv1a64")
                     != _framebuffer_fnv64(raw)
                     or descriptor.get("framebuffer_role") not in {
                         "save_failed_state5", "fresh_continue_field",
                     }):
            _fail(f"save UI COW RGBA role/FNV不一致: {name}")
        resolved_paths.add(resolved)
    if len(resolved_paths) != len(_RUN_ARTIFACTS):
        _fail("save UI COW artifact pathが一意ではありません")


def _normalized_run_payload(
    result: Mapping[str, Any], artifacts: Mapping[str, Mapping[str, Any]],
    process_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_artifacts: dict[str, Any] = {}
    for name, descriptor in sorted(artifacts.items()):
        if not isinstance(name, str) or not isinstance(descriptor, Mapping):
            _fail("normalized save UI COW artifact entry不正")
        normalized_artifacts[name] = {
            key: value for key, value in descriptor.items() if key != "path"
        }
    return {
        "result": dict(result),
        "process_evidence": {
            key: value for key, value in process_evidence.items()
            if key != "artifacts"
        },
        "artifacts": normalized_artifacts,
    }


def _verify_inputs_unchanged(
    identity: Mapping[str, Any], compile_result: Mapping[str, Any],
    orchestrator: Mapping[str, Any],
) -> None:
    checks = (
        (Path(str(identity["rom"])), identity["rom_sha256"], "ROM"),
        (Path(str(identity["metadata"])), identity["metadata_sha256"],
         "metadata"),
        (ROOT / SOURCE, compile_result["source_sha256"], "runner C source"),
        (ROOT / RFU_SOURCE, compile_result["rfu_source_sha256"],
         "RFU C source"),
        (ROOT / RFU_HEADER, compile_result["rfu_header_sha256"],
         "RFU header source"),
        (ROOT / EMBEDDED_SOURCE,
         compile_result["embedded_harness"]["source_sha256"],
         "embedded harness source"),
        (ROOT / ORCHESTRATOR_SOURCE, orchestrator["source_sha256"],
         "orchestrator source"),
    )
    for path, expected, label in checks:
        try:
            actual = _sha256(path.read_bytes())
        except OSError as error:
            _fail(f"{label}再読失敗: {error}")
        if actual != expected:
            _fail(f"{label}が実走中に変更されました")


def _run_once(
    executable: Path, identity: Mapping[str, Any], run_work: Path,
    run_index: int, stale_precleared: int, timeout_seconds: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    environment = os.environ.copy()
    environment["S61_HANDLE_SAVING_DATA_SYMBOL"] = str(
        identity["handle_saving_data"],
    )
    completed = subprocess.run(
        [str(executable), str(identity["rom"]), str(run_work)],
        cwd=ROOT, text=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=timeout_seconds, check=False,
        env=environment,
    )
    if completed.returncode != 0:
        _atomic_retain_bytes(
            run_work, _PROCESS_ARTIFACTS[0], completed.stdout,
            role="raw_process_stdout",
        )
        _atomic_retain_bytes(
            run_work, _PROCESS_ARTIFACTS[1], completed.stderr,
            role="raw_process_stderr",
        )
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace",
        )
        _fail(
            f"Stage61 save UI COW mGBA run{run_index}失敗 "
            f"exit={completed.returncode}: " + detail[-12000:]
        )
    raw_result = _parse_process_stdout(
        completed.stdout, f"save UI COW run{run_index}",
    )
    process_evidence = _retain_process_evidence(
        run_work, stdout=completed.stdout, stderr=completed.stderr,
        result=raw_result,
    )
    validate_c_result(raw_result, run_work)
    artifacts = _product_artifacts(run_work)
    artifacts.update(process_evidence["artifacts"])
    _validate_run_artifact_closure(run_work, artifacts)
    normalized = _normalized_run_payload(
        raw_result, artifacts, process_evidence,
    )
    normalized_sha256 = _sha256(_stable(normalized).encode("utf-8"))
    record = {
        "schema_version": 1,
        "status": "PASS",
        "run_index": run_index,
        "independent_os_process": True,
        "empty_case_directory_at_start": True,
        "stale_artifacts_precleared": stale_precleared,
        "work_directory": str(run_work),
        "normalized_sha256": normalized_sha256,
        "result": dict(raw_result),
        "artifacts": artifacts,
        "process_evidence": {
            key: value for key, value in process_evidence.items()
            if key != "artifacts"
        },
        "failed": 0,
        "untested": 0,
        "warnings": 0,
    }
    return record, normalized


def _require_exact_runs(runs: int) -> None:
    if isinstance(runs, bool) or runs != REQUIRED_RUNS:
        _fail(f"--runsはexact {REQUIRED_RUNS}である必要があります")


def _require_replay_match(
    records: Sequence[Mapping[str, Any]],
    normalized: Sequence[Mapping[str, Any]],
) -> str:
    if len(records) != REQUIRED_RUNS or len(normalized) != REQUIRED_RUNS:
        _fail("save UI COW independent OS run数がexact 2ではありません")
    hashes = [record.get("normalized_sha256") for record in records]
    if len(set(hashes)) != 1 or normalized[0] != normalized[1]:
        _fail("save UI COW 2 independent OS run normalized hash不一致")
    return str(hashes[0])


def run_validation(
    rom_path: Path, metadata_path: Path, work_dir: Path,
    timeout_seconds: int = 3600,
    expected_rom_sha256: str | None = None,
    runs: int = REQUIRED_RUNS,
) -> dict[str, Any]:
    _require_exact_runs(runs)
    if not 60 <= timeout_seconds <= 21600:
        _fail("--timeout-secondsは60..21600です")
    identity = read_identity(
        rom_path, metadata_path, expected_rom_sha256=expected_rom_sha256,
    )
    work = _prepare_work(work_dir)
    orchestrator = {
        "source": str(ORCHESTRATOR_SOURCE),
        "source_sha256": _sha256((ROOT / ORCHESTRATOR_SOURCE).read_bytes()),
    }
    run_records: list[dict[str, Any]] = []
    normalized_runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(
        prefix="stage61-save-ui-cow-compile-",
    ) as temporary:
        executable = Path(temporary) / "stage61-save-ui-cow-runner"
        compile_result = _compile(executable)
        for run_index in range(1, runs + 1):
            run_work, stale_precleared = _prepare_run_work(work, run_index)
            _verify_inputs_unchanged(identity, compile_result, orchestrator)
            record, normalized = _run_once(
                executable, identity, run_work, run_index,
                stale_precleared, timeout_seconds,
            )
            run_records.append(record)
            normalized_runs.append(normalized)
    _verify_inputs_unchanged(identity, compile_result, orchestrator)
    normalized_sha256 = _require_replay_match(
        run_records, normalized_runs,
    )
    artifacts: dict[str, Any] = {}
    for record in run_records:
        for name, descriptor in record["artifacts"].items():
            logical = f"run-{record['run_index']}/{CASE}/{name}"
            if logical in artifacts:
                _fail(f"save UI COW artifact logical path衝突: {logical}")
            artifacts[logical] = descriptor
    artifact_paths = {
        Path(str(descriptor.get("path"))).resolve()
        for descriptor in artifacts.values()
    }
    if len(artifact_paths) != len(artifacts):
        _fail("save UI COW cross-run artifact pathが一意ではありません")
    role_counts = {
        role: sum(1 for descriptor in artifacts.values()
                  if descriptor.get("role") == role)
        for role in (
            "before_save_srm", "fault_partial_flash_srm",
            "explicit_retry_after_srm", "fresh_continue_input_srm",
            "save_failed_raw_framebuffer", "save_failed_framebuffer_ppm",
            "fresh_continue_raw_framebuffer",
            "fresh_continue_framebuffer_ppm", "raw_process_stdout",
            "raw_process_stderr", "canonical_case_result",
        )
    }
    if any(count != REQUIRED_RUNS for count in role_counts.values()) \
            or len(artifacts) != 22:
        _fail("save UI COW retained artifact role/count不一致")
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "case": "stage61_save_ui_cow_e2e",
        "orchestrator": orchestrator,
        "identity": identity,
        "compile": compile_result,
        "runs_per_case": runs,
        "independent_process_count": runs,
        "normalized_sha256": normalized_sha256,
        "normalized_hashes_match": True,
        "runs": run_records,
        "coverage": {
            "start_to_save_real_keys": True,
            "host_direct_save_callback_cannot_pass": True,
            "real_flash_callback_fault": True,
            "real_save_failed_screen": True,
            "save_failed_ppm_raw_framebuffer_join": True,
            "damaged_generation_wipe_and_retry": True,
            "explicit_start_menu_retry": True,
            "hard_fresh_continue": True,
            "hard_fresh_continue_location": "96/5@20,20",
            "retained_srm_exact": True,
            "each_case_two_independent_os_processes": True,
            "normalized_hash_match_per_case": True,
            "full_srm_sha256_count": 8,
            "ppm_sha256_count": 4,
            "raw_framebuffer_sha256_count": 4,
            "raw_stdout_count": 2,
            "raw_stderr_count": 2,
            "canonical_case_result_count": 2,
            "retained_artifact_count": 22,
            "direct_owner_or_script_calls": 0,
        },
        "artifacts": artifacts,
        "failed": 0,
        "untested": 0,
        "warnings": 0,
    }
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-rom-sha256")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--runs", type=int, default=REQUIRED_RUNS)
    parser.add_argument(
        "--compile-only", action="store_true",
        help="ROMを開かずstrict C compileだけを実行する",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _require_exact_runs(args.runs)
    if args.compile_only:
        if args.work_dir is not None or args.expected_rom_sha256 is not None:
            _fail("--compile-onlyは--work-dir/--expected-rom-sha256と併用不可です")
        with tempfile.TemporaryDirectory(
            prefix="stage61-save-ui-cow-compile-only-",
        ) as temporary:
            compile_result = _compile(
                Path(temporary) / "stage61-save-ui-cow-runner",
            )
        document = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "task": TASK,
            "stage": STAGE,
            "status": "PASS",
            "mode": "compile-only",
            "orchestrator": {
                "source": str(ORCHESTRATOR_SOURCE),
                "source_sha256": _sha256(
                    (ROOT / ORCHESTRATOR_SOURCE).read_bytes(),
                ),
            },
            "compile": compile_result,
        }
    else:
        if args.work_dir is None:
            _fail("runtime modeには--work-dirが必要です")
        document = run_validation(
            rom_path=args.rom,
            metadata_path=args.metadata,
            work_dir=args.work_dir,
            timeout_seconds=args.timeout_seconds,
            expected_rom_sha256=args.expected_rom_sha256,
            runs=args.runs,
        )
    if args.output is not None:
        output = _path(args.output)
        protected = {
            _path(args.rom).resolve(strict=False),
            _path(args.metadata).resolve(strict=False),
            (ROOT / SOURCE).resolve(),
            (ROOT / EMBEDDED_SOURCE).resolve(),
            (ROOT / ORCHESTRATOR_SOURCE).resolve(),
        }
        destination = output.resolve(strict=False)
        if destination in protected:
            _fail("report outputがROM/metadata/sourceと同一pathです")
        if args.work_dir is not None:
            work = _path(args.work_dir).resolve(strict=False)
            if destination == work or work in destination.parents:
                _fail("report outputをruntime work directory内には置けません")
        if output.is_symlink() or (output.exists() and not output.is_file()):
            _fail("report outputは通常fileである必要があります")
        output.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_bytes(output, _stable(document).encode("utf-8"))
    print(_stable(document), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stage61SaveUiCowError as error:
        print(f"stage61-save-ui-cow-e2e: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
