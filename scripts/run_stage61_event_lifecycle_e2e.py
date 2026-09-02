#!/usr/bin/env python3
"""Stage61の複合event lifecycleを実キー入力とfresh mGBA coreで検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
SOURCE = Path("tools/mgba_stage61_event_lifecycle_e2e.c")
EMBEDDED = Path("tools/mgba_stage61_display_npc_event_e2e.c")
RFU_SOURCE = Path("tools/mgba_stage61_rfu_peripheral.c")
RFU_HEADER = Path("tools/mgba_stage61_rfu_peripheral.h")
ORCHESTRATOR = Path("scripts/run_stage61_mgba_validation.py")
CONFIG = Path("config/stage61_display_npc_event_audit.json")
DEFAULT_ROM = Path("build/stages/61_display_npc_event_audit.gba")
DEFAULT_METADATA = Path("build/stages/61_display_npc_event_audit.json")
DEFAULT_OUTPUT = Path("reports/generated/stage61_event_lifecycle_e2e.json")
DEFAULT_WORK = Path(".local/stage61-event-lifecycle-final")
SAVE_SIZE = 131072
ROM_SIZE = 32 * 1024 * 1024
PPM_SIZE = len(b"P6\n240 160\n255\n") + 240 * 160 * 3
REQUIRED_RUNS = 2
_CASE_PRODUCT_ARTIFACTS = {
    "vermilion": (
        "event-lifecycle-vermilion.srm", "vermilion-baseline.ppm",
        "vermilion-open.ppm", "vermilion-reentry.ppm",
    ),
    "ferry": tuple(
        name
        for stem in ("ferry-seven", "ferry-one", "ferry-two", "ferry-four",
                     "ferry-five", "ferry-six", "ferry-three")
        for name in (f"{stem}.srm", f"{stem}.ppm")
    ),
    "snorlax": (
        "route16-snorlax-ran.srm", "route16-snorlax-caught.srm",
        "route12-snorlax-caught.srm", "route16-snorlax-ran.ppm",
        "route16-snorlax-caught.ppm", "route12-snorlax-caught.ppm",
    ),
    "fly": ("fly_normal_menu-town-map.ppm", "fly_normal_menu-final.ppm"),
}
_CASE_FRAMEBUFFER_ROLES = {
    "vermilion": {
        "vermilion-baseline.ppm": "pre_switch_baseline",
        "vermilion-open.ppm": "success_open",
        "vermilion-reentry.ppm": "fresh_continue_reentry",
    },
    "ferry": {
        f"{stem}.ppm": "arrival_after_boarding"
        for stem in ("ferry-seven", "ferry-one", "ferry-two", "ferry-four",
                     "ferry-five", "ferry-six", "ferry-three")
    },
    "snorlax": {
        "route16-snorlax-ran.ppm": "route16_ran_field",
        "route16-snorlax-caught.ppm": "route16_caught_field",
        "route12-snorlax-caught.ppm": "route12_caught_field",
    },
    "fly": {
        "fly_normal_menu-town-map.ppm": "town_map",
        "fly_normal_menu-final.ppm": "landing",
    },
}
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ADDRESS = re.compile(r"0x[0-9A-F]{8}")
_FNV1A64 = re.compile(r"[0-9A-F]{16}")
_MAIN = "\nint main(int argc, char **argv)\n{"
_RENAMED = "\nint s61_embedded_event_lifecycle_main(int argc, char **argv)\n{"


class Stage61EventLifecycleError(RuntimeError):
    """入力identity、mGBA観測、または成果物が厳密契約と一致しない。"""


def _fail(message: str) -> NoReturn:
    raise Stage61EventLifecycleError(message)


def _path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fnv1a64(raw: bytes) -> str:
    value = 14695981039346656037
    for byte in raw:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016X}"


def _ppm_rgb_fnv1a64(raw: bytes, label: str) -> str:
    header = b"P6\n240 160\n255\n"
    if len(raw) != PPM_SIZE or not raw.startswith(header):
        _fail(f"{label} PPM RGB framing不一致")
    rgb = raw[len(header):]
    if len(rgb) != 240 * 160 * 3:
        _fail(f"{label} PPM RGB byte数不一致")
    return _fnv1a64(rgb)


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"{label}を読めません: {error}")
    if not isinstance(value, Mapping):
        _fail(f"{label} rootはobjectではありません")
    return value


def _u32(raw: bytes, offset: int, label: str) -> int:
    if isinstance(offset, bool) or not 0 <= offset <= len(raw) - 4:
        _fail(f"{label} offsetがROM範囲外です: {offset:#x}")
    return int.from_bytes(raw[offset:offset + 4], "little")


def _rom_offset(pointer: int, label: str) -> int:
    if not 0x08000000 <= pointer < 0x0A000000:
        _fail(f"{label} pointerがROM範囲外です: {pointer:#x}")
    return pointer - 0x08000000


def _map_event_roots(raw: bytes, group: int, number: int) -> dict[str, Any]:
    groups = _rom_offset(_u32(raw, 0x54B0C, "gMapGroups"), "gMapGroups")
    group_table = _rom_offset(
        _u32(raw, groups + group * 4, "map group table"), "map group table",
    )
    header_pointer = _u32(raw, group_table + number * 4, "map header")
    header = _rom_offset(header_pointer, "map header")
    events_pointer = _u32(raw, header + 4, "map events")
    events = _rom_offset(events_pointer, "map events")
    object_count = raw[events]
    bg_count = raw[events + 3]
    objects_pointer = _u32(raw, events + 4, "object templates") if object_count else 0
    bgs_pointer = _u32(raw, events + 16, "BG events") if bg_count else 0
    objects = _rom_offset(objects_pointer, "object templates") if object_count else 0
    bgs = _rom_offset(bgs_pointer, "BG events") if bg_count else 0
    object_rows = []
    for index in range(object_count):
        row = objects + index * 24
        object_rows.append({
            "index": index,
            "local_id": raw[row],
            "x": int.from_bytes(raw[row + 4:row + 6], "little"),
            "y": int.from_bytes(raw[row + 6:row + 8], "little"),
            "root": _u32(raw, row + 16, "object root"),
        })
    bg_rows = []
    for index in range(bg_count):
        row = bgs + index * 12
        bg_rows.append({
            "index": index,
            "x": int.from_bytes(raw[row:row + 2], "little"),
            "y": int.from_bytes(raw[row + 2:row + 4], "little"),
            "kind": raw[row + 5],
            "root": _u32(raw, row + 8, "BG root"),
        })
    return {
        "map": f"{group:03d}/{number:03d}",
        "header": f"0x{header_pointer:08X}",
        "events": f"0x{events_pointer:08X}",
        "objects": object_rows,
        "bgs": bg_rows,
    }


def resolve_root_exact(raw: bytes) -> dict[str, Any]:
    ferry_specs = (
        ("OBJECT:031/006:001", 31, 6, 1),
        ("OBJECT:032/004:001", 32, 4, 1),
        ("OBJECT:033/004:001", 33, 4, 1),
        ("OBJECT:035/005:001", 35, 5, 1),
        ("OBJECT:036/002:001", 36, 2, 1),
        ("OBJECT:037/002:001", 37, 2, 1),
        ("OBJECT:038/000:001", 38, 0, 1),
    )
    ferries: list[dict[str, Any]] = []
    for owner_id, group, number, index in ferry_specs:
        table = _map_event_roots(raw, group, number)
        if len(table["objects"]) <= index:
            _fail(f"{owner_id} object indexがありません")
        row = table["objects"][index]
        if (row["local_id"], row["x"], row["y"]) != (2, 8, 4):
            _fail(f"{owner_id} local-id/座標がROM上で不一致です")
        _rom_offset(row["root"], owner_id + " root")
        ferries.append({
            "owner_id": owner_id, "map": table["map"],
            "index": index, "local_id": 2, "position": [8, 4],
            "root": f"0x{row['root']:08X}",
        })

    gym = _map_event_roots(raw, 98, 40)
    if len(gym["bgs"]) < 17:
        _fail("Vermilion Gymのtrash BG 15件がROMにありません")
    trash = []
    for trash_id, index in enumerate(range(2, 17), start=1):
        row = gym["bgs"][index]
        expected = (1 + ((trash_id - 1) % 5) * 2,
                    10 + ((trash_id - 1) // 5) * 2)
        if (row["x"], row["y"], row["kind"]) != (*expected, 0):
            _fail(f"Vermilion trash {trash_id} ROM record不一致")
        _rom_offset(row["root"], f"trash {trash_id} root")
        trash.append({"id": trash_id, "index": index,
                      "position": list(expected),
                      "root": f"0x{row['root']:08X}"})
    roots = [int(row["root"], 16) for row in trash]
    if any(right - left != 11 for left, right in zip(roots, roots[1:])):
        _fail("Vermilion trash relocated roots are not exact 11-byte rows")

    route16 = _map_event_roots(raw, 96, 27)
    if len(route16["objects"]) <= 5:
        _fail("Route16 Snorlax object indexがありません")
    snorlax = route16["objects"][5]
    if (snorlax["local_id"], snorlax["x"], snorlax["y"]) != (6, 31, 13):
        _fail("Route16 Snorlax local-id/座標がROM上で不一致です")
    _rom_offset(snorlax["root"], "Route16 Snorlax root")

    route12 = _map_event_roots(raw, 96, 23)
    if len(route12["objects"]) <= 14:
        _fail("Route12 Snorlax object indexがありません")
    route12_snorlax = route12["objects"][14]
    if (route12_snorlax["local_id"], route12_snorlax["x"],
            route12_snorlax["y"]) != (15, 13, 70):
        _fail("Route12 Snorlax local-id/座標がROM上で不一致です")
    _rom_offset(route12_snorlax["root"], "Route12 Snorlax root")

    giver_map = _map_event_roots(raw, 1, 45)
    if len(giver_map["objects"]) <= 8:
        _fail("Flute giver object indexがありません")
    giver = giver_map["objects"][8]
    if (giver["local_id"], giver["x"], giver["y"]) != (9, 22, 24):
        _fail("Flute giver local-id/座標がROM上で不一致です")
    _rom_offset(giver["root"], "Flute giver root")
    owner_roots = ([int(row["root"], 16) for row in ferries]
                   + [int(row["root"], 16) for row in trash]
                   + [snorlax["root"], route12_snorlax["root"], giver["root"]])
    if len(owner_roots) != 25 or len(set(owner_roots)) != 25:
        _fail("event lifecycle 25 owner rootsがROM上で一意ではありません")
    return {
        "schema_version": 1,
        "status": "PASS",
        "resolver": "gMapGroups->MapHeader->MapEvents->record",
        "ferry": ferries,
        "vermilion_trash": trash,
        "route16_snorlax": {
            "owner_id": "OBJECT:096/027:005", "map": "096/027",
            "index": 5, "local_id": 6, "position": [31, 13],
            "root": f"0x{snorlax['root']:08X}",
        },
        "route12_snorlax": {
            "owner_id": "OBJECT:096/023:014", "map": "096/023",
            "index": 14, "local_id": 15, "position": [13, 70],
            "root": f"0x{route12_snorlax['root']:08X}",
        },
        "flute_giver": {
            "owner_id": "OBJECT:001/045:008", "map": "001/045",
            "index": 8, "local_id": 9, "position": [22, 24],
            "root": f"0x{giver['root']:08X}",
        },
    }


def _require_normal_save_contract(audit: Mapping[str, Any]) -> None:
    persistent = audit.get("persistent_state_compatibility")
    normal = persistent.get("normal_save_copy_on_write") \
        if isinstance(persistent, Mapping) else None
    if not isinstance(normal, Mapping) \
            or normal.get("save_type") != "SAVE_NORMAL_ONLY_0" \
            or normal.get("stock_handle_saving_data_delegated") is not False \
            or normal.get("stock_try_write_sector_used") is not False \
            or normal.get("protected_bank_flash_policy") != "READ_ONLY_BYTE_EXACT" \
            or normal.get("fresh_core_continue_mgba_required") is not True:
        _fail("metadataの通常SAVE COW契約がevent lifecycle前提と不一致です")


def read_identity(rom_path: Path, metadata_path: Path,
                  expected_rom_sha256: str | None = None) -> dict[str, Any]:
    rom = _path(rom_path)
    metadata_file = _path(metadata_path)
    try:
        raw = rom.read_bytes()
    except OSError as error:
        _fail(f"Stage61 ROMを読めません: {error}")
    if len(raw) != ROM_SIZE:
        _fail(f"Stage61 ROM size不一致: {len(raw)}")
    digest = _sha256(raw)
    if expected_rom_sha256 is not None:
        if _SHA256.fullmatch(expected_rom_sha256) is None:
            _fail("--expected-rom-sha256はlowercase SHA-256ではありません")
        if digest != expected_rom_sha256:
            _fail("Stage61 ROM hashが明示pinと一致しません")
    metadata = _read_json(metadata_file, "Stage61 metadata")
    output = metadata.get("output")
    if metadata.get("schema_version") != 1 \
            or metadata.get("stage") != STAGE \
            or metadata.get("task") != TASK \
            or metadata.get("status") != "PASS" \
            or not isinstance(output, Mapping) \
            or output.get("size") != len(raw) \
            or output.get("sha256") != digest:
        _fail("Stage61 ROM/metadata identity不一致")
    audit = metadata.get("audit")
    if not isinstance(audit, Mapping) or audit.get("status") != "PASS":
        _fail("Stage61 audit metadata不一致")
    ferry = audit.get("sevii_ferry_multichoice_namespace")
    assertions = ferry.get("assertions") if isinstance(ferry, Mapping) else None
    if not isinstance(ferry, Mapping) or ferry.get("status") != "PASS" \
            or ferry.get("runtime_owner_count") != 7 \
            or not isinstance(assertions, Mapping) \
            or any(assertions.get(key) is not True for key in (
                "all_four_clean_rows_have_exact_four_choices",
                "all_seven_ferry_owners_use_dedicated_rows",
                "cancel_result_0x7f_is_preserved",
                "visible_results_are_bounded_to_0_through_3",
            )):
        _fail("metadataのSevii ferry multichoice契約不一致")
    namespace = audit.get("namespace_policy")
    state = namespace.get("state_namespace") \
        if isinstance(namespace, Mapping) else None
    flag_mapping = state.get("flag_mapping") if isinstance(state, Mapping) else None
    if not isinstance(flag_mapping, Mapping) \
            or flag_mapping.get("0x0264") != "0x1871":
        _fail("Vermilion persistent flag relocation不一致")
    _require_normal_save_contract(audit)

    config_path = ROOT / CONFIG
    config = _read_json(config_path, "Stage61 builder config")
    story = config.get("story")
    required_story = {
        "tohoku_flute_flag": "0x119E", "route12_hidden_flag": "0x149E",
        "route16_hidden_flag": "0x149F",
        "flute_item": 350, "canonical_snorlax_species": 491,
    }
    if not isinstance(story, Mapping) \
            or any(story.get(key) != value for key, value in required_story.items()):
        _fail("Stage61 Route16 story config不一致")
    roots = resolve_root_exact(raw)
    return {
        "schema_version": 1, "status": "PASS",
        "rom": str(rom.resolve()), "rom_size": len(raw),
        "rom_sha256": digest,
        "metadata": str(metadata_file.resolve()),
        "metadata_sha256": _sha256(metadata_file.read_bytes()),
        "config": str(config_path.resolve()),
        "config_sha256": _sha256(config_path.read_bytes()),
        "root_exact": roots,
        "contracts": {
            "normal_save_copy_on_write": True,
            "ferry_four_choice_rows": 4,
            "ferry_owner_count": 7,
            "vermilion_persistent_flag": "0x1871",
            "route16_hidden_flag": "0x149F",
            "route12_hidden_flag": "0x149E",
            "canonical_snorlax_species": 491,
        },
    }


def _build_embedded(destination: Path) -> dict[str, Any]:
    source = ROOT / EMBEDDED
    text = source.read_text(encoding="utf-8")
    if text.count(_MAIN) != 1:
        _fail("embedded display harnessのouter mainが一意ではありません")
    transformed = text.replace(_MAIN, _RENAMED, 1)
    destination.write_text(transformed, encoding="utf-8", newline="\n")
    return {
        "path": str(source.resolve()), "sha256": _sha256(source.read_bytes()),
        "transformed_sha256": _sha256(transformed.encode()),
        "outer_main_renamed": True, "other_bytes_unchanged": True,
    }


def compile_runner(executable: Path) -> dict[str, Any]:
    compiler = shutil.which("cc")
    source = ROOT / SOURCE
    rfu_source = ROOT / RFU_SOURCE
    rfu_header = ROOT / RFU_HEADER
    missing = [
        str(path) for path in (source, rfu_source, rfu_header)
        if not path.is_file()
    ]
    if compiler is None or missing:
        _fail(f"compile前提不足: cc={compiler}, missing={missing}")
    executable.parent.mkdir(parents=True, exist_ok=True)
    embedded_path = executable.parent / "stage61-event-lifecycle-embedded.c"
    embedded = _build_embedded(embedded_path)
    command = [
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-pedantic", f"-I{ROOT / 'tools'}",
        f'-DS61_EVENT_LIFECYCLE_EMBEDDED_HARNESS="{embedded_path}"',
        str(source), str(rfu_source), "-o", str(executable), "-lmgba",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=180, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        detail = completed.stderr or completed.stdout or str(completed.returncode)
        _fail("event lifecycle strict C compile失敗: " + detail[-8000:])
    orchestrator = ROOT / ORCHESTRATOR
    return {
        "status": "PASS",
        "command": "cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic ... -lmgba",
        "runner": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256(Path(__file__).read_bytes()),
        },
        "c_harness": {
            "path": str(source.resolve()), "sha256": _sha256(source.read_bytes()),
        },
        "rfu_source": {
            "path": str(rfu_source.resolve()),
            "sha256": _sha256(rfu_source.read_bytes()),
        },
        "rfu_header": {
            "path": str(rfu_header.resolve()),
            "sha256": _sha256(rfu_header.read_bytes()),
        },
        "embedded_display_harness": embedded,
        "current_orchestrator": {
            "path": str(orchestrator.resolve()),
            "sha256": _sha256(orchestrator.read_bytes()),
        },
        "stdout_empty": True, "stderr_empty": True,
    }


def _require_map(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(f"{label} keys不一致")
    return value


def _require_true(value: Mapping[str, Any], keys: Sequence[str], label: str) -> None:
    for key in keys:
        if value.get(key) is not True:
            _fail(f"{label}.{key}はtrueではありません")


def _require_zero_terminal(value: Mapping[str, Any], label: str) -> None:
    if value.get("status") != "PASS" or value.get("failed") != 0 \
            or value.get("untested") != 0 or value.get("warnings") != 0:
        _fail(f"{label} failed/untested/warningsがzero PASSではありません")


def _artifact_name(name: Any, label: str) -> str:
    if not isinstance(name, str) or not name or Path(name).name != name:
        _fail(f"{label} artifact basename不正")
    return name


def _unlink_exact(path: Path, label: str) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        _fail(f"{label}は通常fileではありません: {path.name}")


def _preclear_exact(work: Path, names: Sequence[str], label: str) -> None:
    for raw_name in names:
        name = _artifact_name(raw_name, label)
        _unlink_exact(work / name, label)
        _unlink_exact(work / f".{name}.retain.tmp", label + " temporary")


def _atomic_retain_bytes(work: Path, name: Any, raw: bytes, *,
                         role: str, case: str,
                         stale_precleared: bool) -> dict[str, Any]:
    basename = _artifact_name(name, role)
    if not isinstance(raw, bytes):
        _fail(f"{role} retain payloadはbytesではありません")
    destination = work / basename
    temporary = work / f".{basename}.retain.tmp"
    _unlink_exact(temporary, role + " temporary")
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        directory_fd = os.open(work, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as error:
        _unlink_exact(temporary, role + " temporary")
        _fail(f"{role} atomic retain失敗: {error}")
    retained = destination.read_bytes()
    if retained != raw:
        _fail(f"{role} atomic retain readback不一致: {basename}")
    return {
        "path": str(destination.resolve()), "size": len(retained),
        "sha256": _sha256(retained), "role": role, "case": case,
        "stale_precleared": stale_precleared, "atomic_retained": True,
    }


def _artifact(work: Path, name: Any, size: int, label: str, *,
              role: str, case: str,
              expected_rgb_fnv1a64: str | None = None,
              framebuffer_role: str | None = None) -> dict[str, Any]:
    basename = _artifact_name(name, label)
    path = work / basename
    if path.is_symlink() or not path.is_file():
        _fail(f"{label} artifactがありません: {basename}")
    raw = path.read_bytes()
    if len(raw) != size:
        _fail(f"{label} artifact size不一致: {basename}={len(raw)}")
    rgb_fnv1a64 = None
    if size == PPM_SIZE:
        rgb_fnv1a64 = _ppm_rgb_fnv1a64(raw, label)
        if _FNV1A64.fullmatch(str(expected_rgb_fnv1a64)) is None \
                or rgb_fnv1a64 != expected_rgb_fnv1a64:
            _fail(f"{label} saved RGB FNV-1a64/C result不一致: {basename}")
        if not isinstance(framebuffer_role, str) or not framebuffer_role:
            _fail(f"{label} framebuffer role不正: {basename}")
    elif expected_rgb_fnv1a64 is not None or framebuffer_role is not None:
        _fail(f"{label} non-PPMへframebuffer契約が指定されました")
    retained = _atomic_retain_bytes(
        work, basename, raw, role=role, case=case,
        stale_precleared=True,
    )
    if rgb_fnv1a64 is not None:
        retained["rgb_fnv1a64"] = rgb_fnv1a64
        retained["framebuffer_role"] = framebuffer_role
    return retained


def _framebuffer_contract(value: Mapping[str, Any], case: str,
                          label: str) -> tuple[Mapping[str, str],
                                               Mapping[str, str]]:
    expected_roles = _CASE_FRAMEBUFFER_ROLES.get(case)
    if expected_roles is None:
        _fail(f"{label} framebuffer case不正")
    expected_names = set(expected_roles)
    hashes = _require_map(
        value.get("framebuffer_artifact_fnv1a64"), expected_names,
        label + " framebuffer artifact FNV",
    )
    roles = _require_map(
        value.get("framebuffer_artifact_roles"), expected_names,
        label + " framebuffer artifact roles",
    )
    if roles != expected_roles:
        _fail(f"{label} framebuffer artifact role/name対応不一致")
    if any(not isinstance(item, str) or _FNV1A64.fullmatch(item) is None
           for item in hashes.values()):
        _fail(f"{label} framebuffer artifact RGB FNV形式不一致")
    return hashes, roles


def _framebuffer_readback(
        artifacts: Mapping[str, Mapping[str, Any]],
        names: Sequence[str], label: str) -> dict[str, str]:
    readback: dict[str, str] = {}
    for name in names:
        artifact = artifacts.get(name)
        if not isinstance(artifact, Mapping) \
                or _FNV1A64.fullmatch(str(artifact.get("rgb_fnv1a64"))) is None:
            _fail(f"{label} framebuffer RGB readback join不一致: {name}")
        readback[name] = str(artifact["rgb_fnv1a64"])
    return readback


_SAVE_SECTOR_SIZE = 0x1000
_SAVE_SECTION_COUNT = 14
_SAVE_SIGNATURE = 0x08012025
_SAVE_SECTION_SIZES = (
    0xF24, 0xF80, 0xF80, 0xF80, 0xEC0,
    0xF80, 0xF80, 0xF80, 0xF80, 0xF80, 0xF80, 0xF80, 0xF80,
    0x7D0,
)


def _save_checksum(section: bytes, identifier: int) -> int:
    if len(section) != _SAVE_SECTOR_SIZE \
            or not 0 <= identifier < _SAVE_SECTION_COUNT:
        _fail("event SRM checksum入力不正")
    total = sum(
        int.from_bytes(section[offset:offset + 4], "little")
        for offset in range(0, _SAVE_SECTION_SIZES[identifier], 4)
    ) & 0xFFFFFFFF
    return ((total >> 16) + (total & 0xFFFF)) & 0xFFFF


def _counter_newer(left: int, right: int) -> bool:
    delta = (right - left) & 0xFFFFFFFF
    return delta != 0 and delta < 0x80000000


def _decode_event_srm(raw: bytes, label: str) -> dict[str, Any]:
    if len(raw) != SAVE_SIZE:
        _fail(f"{label} SRM size不一致")
    generations: dict[int, dict[int, bytes]] = {}
    physical_by_counter: dict[int, dict[int, int]] = {}
    for physical in range(28):
        start = physical * _SAVE_SECTOR_SIZE
        section = raw[start:start + _SAVE_SECTOR_SIZE]
        identifier = int.from_bytes(section[0xFF4:0xFF6], "little")
        checksum = int.from_bytes(section[0xFF6:0xFF8], "little")
        signature = int.from_bytes(section[0xFF8:0xFFC], "little")
        counter = int.from_bytes(section[0xFFC:0x1000], "little")
        if signature != _SAVE_SIGNATURE or identifier >= _SAVE_SECTION_COUNT \
                or checksum != _save_checksum(section, identifier):
            continue
        rows = generations.setdefault(counter, {})
        physical_rows = physical_by_counter.setdefault(counter, {})
        if identifier in rows:
            rows.clear()
            physical_rows.clear()
            continue
        rows[identifier] = section
        physical_rows[identifier] = physical
    complete = {
        counter: rows for counter, rows in generations.items()
        if set(rows) == set(range(_SAVE_SECTION_COUNT))
    }
    if not complete:
        _fail(f"{label} SRMに完全な14-sector generationがありません")
    selected = next(iter(complete))
    for counter in complete:
        if _counter_newer(selected, counter):
            selected = counter
    sections = complete[selected]
    physical_rows = physical_by_counter[selected]
    if len({physical // 14 for physical in physical_rows.values()}) != 1:
        _fail(f"{label} SRM generationがbankを跨いでいます")
    save1 = b"".join(
        sections[identifier][:_SAVE_SECTION_SIZES[identifier]]
        for identifier in range(1, 5)
    )
    if len(save1) != 0x3D40:
        _fail(f"{label} SRM SaveBlock1再構築不一致")
    record = sections[13][0x7D0:0x7D0 + 0x616]
    if len(record) != 0x616 \
            or int.from_bytes(record[0:4], "little") != 0x45313653 \
            or int.from_bytes(record[4:6], "little") != 1 \
            or int.from_bytes(record[6:8], "little") != 0x606:
        _fail(f"{label} SRM S61E header不一致")
    payload = record[16:]
    crc = int.from_bytes(record[8:12], "little")
    if zlib.crc32(payload) & 0xFFFFFFFF != crc \
            or int.from_bytes(record[12:16], "little") != (~crc & 0xFFFFFFFF):
        _fail(f"{label} SRM S61E CRC不一致")
    return {
        "counter": selected,
        "bank": next(iter(physical_rows.values())) // 14,
        "map_group": save1[4], "map_number": save1[5],
        "x": int.from_bytes(save1[0:2], "little"),
        "y": int.from_bytes(save1[2:4], "little"),
        "saveblock1": save1, "expanded_flags": payload[:0x200],
        "record_crc32": crc, "valid_generation_count": len(complete),
    }


def _decoded_flag(decoded: Mapping[str, Any], identifier: int) -> bool:
    if 0 <= identifier < 0x0900:
        backing = decoded.get("saveblock1")
        offset = 0x0EE0 + (identifier >> 3)
    elif 0x0900 <= identifier <= 0x18FF:
        backing = decoded.get("expanded_flags")
        offset = (identifier - 0x0900) >> 3
    else:
        _fail(f"event SRM flag ID範囲外: 0x{identifier:04X}")
    if not isinstance(backing, bytes) or offset >= len(backing):
        _fail(f"event SRM flag backing不正: 0x{identifier:04X}")
    return bool(backing[offset] & (1 << (identifier & 7)))


def _snorlax_srm_readback(work: Path, name: str, *, group: int, map_: int,
                           x: int, y: int, hidden_flag: int) -> dict[str, Any]:
    path = work / _artifact_name(name, "Snorlax semantic SRM")
    raw = path.read_bytes()
    decoded = _decode_event_srm(raw, name)
    flute = _decoded_flag(decoded, 0x119E)
    hidden = _decoded_flag(decoded, hidden_flag)
    if decoded["map_group"] != group or decoded["map_number"] != map_ \
            or decoded["x"] != x or decoded["y"] != y \
            or not flute or not hidden:
        _fail(f"{name} external map/xy/flute/hidden semantic readback不一致")
    return {
        "path": str(path.resolve()), "size": len(raw), "sha256": _sha256(raw),
        "selected_counter": decoded["counter"], "selected_bank": decoded["bank"],
        "valid_generation_count": decoded["valid_generation_count"],
        "map": f"{decoded['map_group']}/{decoded['map_number']}",
        "position": [decoded["x"], decoded["y"]],
        "flute_flag": "0x119E", "flute_flag_set": flute,
        "hidden_flag": f"0x{hidden_flag:04X}", "hidden_flag_set": hidden,
        "expanded_record_crc32": f"0x{decoded['record_crc32']:08X}",
        "external_byte_decode": True,
    }


def validate_vermilion(value: Any, work: Path,
                        roots: Mapping[str, Any]) -> dict[str, Any]:
    keys = {"schema_version", "status", "case", "preparation_teleport_only",
            "direct_owner_or_script_calls", "map", "persistent_flag", "temp_flag",
            "switches_initial", "wrong_switch", "switches_retry",
            "actual_walk_steps", "direction_plus_a", "owner_pc_hits",
            "failure_reset", "success_persisted", "fresh_core_continue",
            "reentry_temp_reset", "field_input_recovered", "metatile_hashes",
            "srm", "ppms", "framebuffer_artifact_fnv1a64",
            "framebuffer_artifact_roles", "failed", "untested", "warnings"}
    row = _require_map(value, keys, "vermilion")
    _require_zero_terminal(row, "vermilion")
    _require_true(row, ("preparation_teleport_only", "direction_plus_a",
                        "failure_reset", "success_persisted", "fresh_core_continue",
                        "reentry_temp_reset", "field_input_recovered"), "vermilion")
    if row.get("schema_version") != 1 or row.get("case") != "vermilion_gym_lifecycle" \
            or row.get("map") != "98/40" \
            or row.get("persistent_flag") != "0x1871" \
            or row.get("temp_flag") != "0x0001" \
            or row.get("direct_owner_or_script_calls") != 0 \
            or not isinstance(row.get("actual_walk_steps"), int) \
            or isinstance(row["actual_walk_steps"], bool) \
            or row["actual_walk_steps"] < 4 \
            or not isinstance(row.get("owner_pc_hits"), int) \
            or isinstance(row["owner_pc_hits"], bool) or row["owner_pc_hits"] < 4:
        _fail("Vermilion実入力/owner/state契約不一致")
    for name in ("switches_initial", "switches_retry"):
        pair = row.get(name)
        if not isinstance(pair, list) or len(pair) != 2 \
                or any(isinstance(item, bool) or not isinstance(item, int)
                       or not 1 <= item <= 15 for item in pair) \
                or pair[0] == pair[1]:
            _fail(f"Vermilion {name}不一致")
        left_row, left_column = divmod(pair[0] - 1, 5)
        right_row, right_column = divmod(pair[1] - 1, 5)
        if abs(left_row - right_row) + abs(left_column - right_column) != 1:
            _fail(f"Vermilion {name}は5x3上で隣接していません")
    if not isinstance(row.get("wrong_switch"), int) \
            or isinstance(row["wrong_switch"], bool) \
            or not 1 <= row["wrong_switch"] <= 15 \
            or row["wrong_switch"] in row["switches_initial"]:
        _fail("Vermilion wrong switch不一致")
    hashes = _require_map(row.get("metatile_hashes"),
                          {"baseline", "half", "reset", "open", "reentry"},
                          "vermilion metatile hashes")
    if any(not isinstance(item, str) or re.fullmatch(r"[0-9A-F]{16}", item) is None
           for item in hashes.values()) \
            or hashes["baseline"] != hashes["reset"] \
            or hashes["open"] != hashes["reentry"] \
            or len({hashes["baseline"], hashes["half"], hashes["open"]}) != 3:
        _fail("Vermilion metatile lifecycle hash不一致")
    ppms = row.get("ppms")
    if ppms != ["vermilion-baseline.ppm", "vermilion-open.ppm",
                "vermilion-reentry.ppm"]:
        _fail("Vermilion PPM列不一致")
    framebuffer_hashes, framebuffer_roles = _framebuffer_contract(
        row, "vermilion", "Vermilion",
    )
    artifacts = {row["srm"]: _artifact(
        work, row["srm"], SAVE_SIZE, "Vermilion SRM",
        role="external_srm_full_readback", case="vermilion",
    )}
    artifacts.update({name: _artifact(
        work, name, PPM_SIZE, "Vermilion PPM",
        role="framebuffer_ppm", case="vermilion",
        expected_rgb_fnv1a64=framebuffer_hashes[name],
        framebuffer_role=framebuffer_roles[name],
    )
                      for name in ppms})
    if len(roots.get("vermilion_trash", [])) != 15:
        _fail("Vermilion ROM root exact件数不一致")
    return {
        "status": "PASS", "result": dict(row), "artifacts": artifacts,
        "external_srm_semantic_readback": [],
        "framebuffer_artifact_rgb_readback": _framebuffer_readback(
            artifacts, ppms, "Vermilion",
        ),
    }


def validate_ferry(value: Any, work: Path,
                   roots: Mapping[str, Any]) -> dict[str, Any]:
    keys = {"schema_version", "status", "case",
            "preparation_teleport_and_engine_var_fixture",
            "preparation_engine_var_writes", "preparation_engine_api_calls_only",
            "host_direct_memory_writes", "direct_owner_or_script_calls",
            "direct_special_calls", "owners", "owner_count", "cancel_count",
            "boarding_count", "arrival_count", "normal_save_count",
            "fresh_continue_count", "framebuffer_artifact_fnv1a64",
            "framebuffer_artifact_roles", "failed", "untested", "warnings"}
    row = _require_map(value, keys, "ferry")
    _require_zero_terminal(row, "ferry")
    if row.get("schema_version") != 1 or row.get("case") != "ferry_all_owner_lifecycle" \
            or row.get("preparation_teleport_and_engine_var_fixture") is not True \
            or row.get("preparation_engine_var_writes") != [
                {"var": "0x4076", "value": 0},
                {"var": "0x4071", "value": 4},
            ] \
            or row.get("preparation_engine_api_calls_only") is not True \
            or row.get("host_direct_memory_writes") != 0 \
            or row.get("direct_owner_or_script_calls") != 0 \
            or row.get("direct_special_calls") != 0 \
            or any(row.get(key) != 7 for key in (
                "owner_count", "cancel_count", "boarding_count", "arrival_count",
                "normal_save_count", "fresh_continue_count")):
        _fail("ferry aggregate契約不一致")
    owners = row.get("owners")
    root_rows = roots.get("ferry")
    if not isinstance(owners, list) or len(owners) != 7 \
            or not isinstance(root_rows, list) or len(root_rows) != 7:
        _fail("ferry owner/root件数不一致")
    expected_roots = {item["owner_id"]: item for item in root_rows}
    framebuffer_hashes, framebuffer_roles = _framebuffer_contract(
        row, "ferry", "ferry",
    )
    artifacts: dict[str, Any] = {}
    seen: set[str] = set()
    owner_keys = {"owner_id", "map", "owner_root", "actual_walk_steps",
                  "direction_plus_a", "choice_cancel_via_b", "cancel_result",
                  "post_cancel_result",
                  "cancel_owner_pc_hits", "pre_board_engine_var_readback",
                  "choice_zero_via_a", "boarding",
                  "owner_pc_hits", "special_pc", "special_pc_hits",
                  "first_nonfield_callback", "first_task_function", "task_observed",
                  "arrival", "save_via_start_menu", "fresh_core_continue",
                  "field_input_recovered", "srm", "ppm"}
    for index, value_owner in enumerate(owners):
        owner = _require_map(value_owner, owner_keys, f"ferry owner {index}")
        owner_id = owner.get("owner_id")
        root_row = expected_roots.get(owner_id)
        expected_map = None
        source_map = root_row.get("map") if isinstance(root_row, Mapping) else None
        if isinstance(source_map, str) \
                and re.fullmatch(r"[0-9]{3}/[0-9]{3}", source_map):
            expected_map = "/".join(str(int(part)) for part in source_map.split("/"))
        if not isinstance(root_row, Mapping) or owner_id in seen \
                or owner.get("owner_root") != root_row.get("root") \
                or owner.get("map") != expected_map \
                or owner.get("cancel_result") != 127 \
                or owner.get("post_cancel_result") != 0 \
                or owner.get("pre_board_engine_var_readback") \
                    != {"0x4076": 0, "0x4071": 4} \
                or not isinstance(owner.get("actual_walk_steps"), int) \
                or isinstance(owner["actual_walk_steps"], bool) \
                or owner["actual_walk_steps"] < 1 \
                or not isinstance(owner.get("cancel_owner_pc_hits"), int) \
                or owner["cancel_owner_pc_hits"] < 1 \
                or not isinstance(owner.get("owner_pc_hits"), int) \
                or owner["owner_pc_hits"] < 1 \
                or not isinstance(owner.get("special_pc_hits"), int) \
                or owner["special_pc_hits"] < 1 \
                or owner.get("special_pc") != "0x08147468" \
                or owner.get("first_nonfield_callback") != "0x0814765D" \
                or owner.get("first_task_function") != "0x0807951D" \
                or owner.get("arrival") != "3/5@23,32":
            _fail(f"ferry owner実入力/root/callback契約不一致: {owner_id}")
        _require_true(owner, ("direction_plus_a", "choice_cancel_via_b",
                              "choice_zero_via_a", "boarding", "task_observed",
                              "save_via_start_menu", "fresh_core_continue",
                              "field_input_recovered"), f"ferry {owner_id}")
        seen.add(owner_id)
        artifacts[owner["srm"]] = _artifact(
            work, owner["srm"], SAVE_SIZE, f"ferry {owner_id} SRM",
            role="external_srm_full_readback", case="ferry",
        )
        artifacts[owner["ppm"]] = _artifact(
            work, owner["ppm"], PPM_SIZE, f"ferry {owner_id} PPM",
            role="framebuffer_ppm", case="ferry",
            expected_rgb_fnv1a64=framebuffer_hashes[owner["ppm"]],
            framebuffer_role=framebuffer_roles[owner["ppm"]],
        )
    if seen != set(expected_roots):
        _fail("ferry全7 owner集合不一致")
    return {
        "status": "PASS", "result": dict(row), "artifacts": artifacts,
        "external_srm_semantic_readback": [],
        "framebuffer_artifact_rgb_readback": _framebuffer_readback(
            artifacts, list(framebuffer_roles), "ferry",
        ),
    }


def validate_snorlax(value: Any, work: Path,
                     roots: Mapping[str, Any]) -> dict[str, Any]:
    keys = {
        "schema_version", "status", "case", "owner_id", "owner_root",
        "producer_owner_id", "producer_owner_root", "producer_owner_pc_hits",
        "producer_message_count",
        "preparation_teleport_and_declared_capture_fixture",
        "direct_owner_or_script_calls", "natural_flute_producer",
        "actual_walk_steps", "direction_plus_a", "choice_no_preserved",
        "choice_no_result", "choice_yes_battle", "species", "owner_pc_hits",
        "capture_preparation", "outcomes", "route12_capture_control",
        "hidden_after_each_terminal", "normal_save_count",
        "fresh_continue_count", "reentry_hidden_count", "field_input_recovered",
        "srms", "ppms", "framebuffer_artifact_fnv1a64",
        "framebuffer_artifact_roles", "failed", "untested", "warnings",
    }
    row = _require_map(value, keys, "snorlax")
    _require_zero_terminal(row, "snorlax")
    root = roots.get("route16_snorlax")
    route12_root = roots.get("route12_snorlax")
    producer_root = roots.get("flute_giver")
    if not isinstance(root, Mapping) \
            or not isinstance(route12_root, Mapping) \
            or not isinstance(producer_root, Mapping) \
            or row.get("owner_id") != "OBJECT:096/027:005" \
            or row.get("owner_root") != root.get("root") \
            or row.get("producer_owner_id") != "OBJECT:001/045:008" \
            or row.get("producer_owner_root") != producer_root.get("root") \
            or row.get("case") != "route16_snorlax_lifecycle" \
            or row.get("direct_owner_or_script_calls") != 0 \
            or row.get("species") != 491 \
            or any(row.get(key) != 3 for key in (
                "normal_save_count", "fresh_continue_count", "reentry_hidden_count")) \
            or not isinstance(row.get("actual_walk_steps"), int) \
            or isinstance(row["actual_walk_steps"], bool) \
            or row["actual_walk_steps"] < 6 \
            or not isinstance(row.get("owner_pc_hits"), int) \
            or isinstance(row["owner_pc_hits"], bool) \
            or row["owner_pc_hits"] < 3 \
            or not isinstance(row.get("producer_owner_pc_hits"), int) \
            or isinstance(row["producer_owner_pc_hits"], bool) \
            or row["producer_owner_pc_hits"] < 3 \
            or not isinstance(row.get("producer_message_count"), int) \
            or isinstance(row["producer_message_count"], bool) \
            or row["producer_message_count"] < 3:
        _fail("Route12/16 Snorlax owner/producer/state契約不一致")
    _require_true(row, ("preparation_teleport_and_declared_capture_fixture",
                        "natural_flute_producer",
                        "direction_plus_a", "choice_no_preserved",
                        "choice_yes_battle", "hidden_after_each_terminal",
                        "field_input_recovered"), "snorlax")

    preparation = _require_map(
        row.get("capture_preparation"), {
            "matches_established_last_ball_fixture",
            "master_ball_added_via_rom_call",
            "host_writes_limited_to_inventory_party_menu_preparation",
            "party_slots_1_through_5_zeroed_by_host",
            "party_count_set_to_one_by_host",
            "bag_ball_pocket_cursor_prepared_by_host",
            "direct_memory_writes_outside_declared_fixture",
            "battle_struct_host_writes", "battle_result_host_writes",
            "battle_action_cursor_host_writes",
            "fresh_continue_before_battle", "unused_party_slots_zero",
        }, "snorlax capture preparation",
    )
    _require_true(preparation, (
        "matches_established_last_ball_fixture",
        "master_ball_added_via_rom_call",
        "host_writes_limited_to_inventory_party_menu_preparation",
        "party_slots_1_through_5_zeroed_by_host",
        "party_count_set_to_one_by_host",
        "bag_ball_pocket_cursor_prepared_by_host",
        "fresh_continue_before_battle", "unused_party_slots_zero",
    ), "snorlax capture preparation")
    if preparation.get("direct_memory_writes_outside_declared_fixture") != 0 \
            or preparation.get("battle_struct_host_writes") != 0 \
            or preparation.get("battle_result_host_writes") != 0 \
            or preparation.get("battle_action_cursor_host_writes") != 0:
        _fail("Snorlax battle runtime/resultへhost直書きがあります")

    outcomes = row.get("outcomes")
    run_keys = {
        "name", "value", "battle_result_via_keys", "species",
        "party_count_before", "party_count_after",
        "battle_runtime_initialized", "battle_runtime_cleaned",
        "field_returned", "first_battle_callback", "battle_input_pulses",
        "owner_pc_hits", "producer_owner_pc_hits",
    }
    caught_keys = run_keys | {
        "bag_direction_a", "captured_species", "capture_preparation_valid",
        "master_ball_consumed",
    }
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        _fail("Route16 Snorlax複数battle終端件数不一致")
    ran = _require_map(outcomes[0], run_keys, "Route16 RAN")
    caught = _require_map(outcomes[1], caught_keys, "Route16 CAUGHT")
    _require_true(ran, (
        "battle_result_via_keys", "battle_runtime_initialized",
        "battle_runtime_cleaned", "field_returned",
    ), "Route16 RAN")
    _require_true(caught, (
        "battle_result_via_keys", "bag_direction_a",
        "capture_preparation_valid", "battle_runtime_initialized",
        "battle_runtime_cleaned", "field_returned", "master_ball_consumed",
    ), "Route16 CAUGHT")
    if ran.get("name") != "RAN" or ran.get("value") != 4 \
            or ran.get("species") != 491 \
            or not isinstance(ran.get("party_count_before"), int) \
            or isinstance(ran["party_count_before"], bool) \
            or not 1 <= ran["party_count_before"] <= 6 \
            or ran.get("party_count_after") != ran["party_count_before"] \
            or caught.get("name") != "CAUGHT" or caught.get("value") != 7 \
            or caught.get("species") != 491 \
            or caught.get("party_count_before") != 1 \
            or caught.get("party_count_after") != 2 \
            or caught.get("captured_species") != 491:
        _fail("Route16 Snorlax Run/Caught party終端不一致")
    for label, outcome in (("Route16 RAN", ran),
                           ("Route16 CAUGHT", caught)):
        if _ADDRESS.fullmatch(str(outcome.get("first_battle_callback"))) is None \
                or not isinstance(outcome.get("battle_input_pulses"), int) \
                or isinstance(outcome["battle_input_pulses"], bool) \
                or outcome["battle_input_pulses"] < 1 \
                or not isinstance(outcome.get("owner_pc_hits"), int) \
                or outcome["owner_pc_hits"] < 1 \
                or not isinstance(outcome.get("producer_owner_pc_hits"), int) \
                or outcome["producer_owner_pc_hits"] < 1:
            _fail(f"{label} callback/input/owner観測不一致")

    route12_keys = {
        "owner_id", "owner_root", "map", "physical_start", "approach_key",
        "approach_steps", "owner_position", "species", "outcome_name",
        "outcome_value", "natural_flute_producer", "producer_owner_pc_hits",
        "owner_pc_hits", "actual_walk_steps", "direction_plus_a",
        "choice_yes_battle", "bag_direction_a", "party_count_before",
        "party_count_after", "captured_species", "capture_preparation_valid",
        "battle_runtime_initialized", "battle_runtime_cleaned", "field_returned",
        "master_ball_consumed", "first_battle_callback", "battle_input_pulses",
        "save_via_start_menu", "fresh_core_continue", "reentry_hidden",
        "field_input_recovered", "srm", "ppm",
    }
    route12 = _require_map(
        row.get("route12_capture_control"), route12_keys,
        "Route12 capture control",
    )
    _require_true(route12, (
        "natural_flute_producer", "direction_plus_a", "choice_yes_battle",
        "bag_direction_a", "capture_preparation_valid",
        "battle_runtime_initialized", "battle_runtime_cleaned", "field_returned",
        "master_ball_consumed", "save_via_start_menu", "fresh_core_continue",
        "reentry_hidden", "field_input_recovered",
    ), "Route12 capture control")
    if route12.get("owner_id") != "OBJECT:096/023:014" \
            or route12.get("owner_root") != route12_root.get("root") \
            or route12.get("map") != "96/23" \
            or route12.get("physical_start") != [11, 70] \
            or route12.get("approach_key") != "RIGHT" \
            or route12.get("approach_steps") != 1 \
            or route12.get("owner_position") != [13, 70] \
            or route12.get("species") != 491 \
            or route12.get("outcome_name") != "CAUGHT" \
            or route12.get("outcome_value") != 7 \
            or route12.get("party_count_before") != 1 \
            or route12.get("party_count_after") != 2 \
            or route12.get("captured_species") != 491 \
            or not isinstance(route12.get("actual_walk_steps"), int) \
            or route12["actual_walk_steps"] < 2 \
            or not isinstance(route12.get("owner_pc_hits"), int) \
            or route12["owner_pc_hits"] < 1 \
            or not isinstance(route12.get("producer_owner_pc_hits"), int) \
            or route12["producer_owner_pc_hits"] < 1 \
            or not isinstance(route12.get("battle_input_pulses"), int) \
            or route12["battle_input_pulses"] < 1 \
            or _ADDRESS.fullmatch(
                str(route12.get("first_battle_callback"))) is None:
        _fail("Route12 species491実Bag捕獲/party/field終端不一致")
    if row["owner_pc_hits"] != ran["owner_pc_hits"] + caught["owner_pc_hits"] \
            or row["producer_owner_pc_hits"] != (
                ran["producer_owner_pc_hits"]
                + caught["producer_owner_pc_hits"]
                + route12["producer_owner_pc_hits"]):
        _fail("Snorlax aggregate owner PC hit数不一致")

    expected_srms = ["route16-snorlax-ran.srm",
                     "route16-snorlax-caught.srm",
                     "route12-snorlax-caught.srm"]
    expected_ppms = ["route16-snorlax-ran.ppm",
                     "route16-snorlax-caught.ppm",
                     "route12-snorlax-caught.ppm"]
    if row.get("srms") != expected_srms or row.get("ppms") != expected_ppms \
            or route12.get("srm") != expected_srms[2] \
            or route12.get("ppm") != expected_ppms[2]:
        _fail("Route12/16 Snorlax成果物列不一致")
    framebuffer_hashes, framebuffer_roles = _framebuffer_contract(
        row, "snorlax", "Route12/16 Snorlax",
    )
    artifacts = {name: _artifact(
        work, name, SAVE_SIZE, "Snorlax SRM",
        role="external_srm_full_readback", case="snorlax",
    )
                 for name in row["srms"]}
    artifacts.update({name: _artifact(
        work, name, PPM_SIZE, "Snorlax PPM",
        role="framebuffer_ppm", case="snorlax",
        expected_rgb_fnv1a64=framebuffer_hashes[name],
        framebuffer_role=framebuffer_roles[name],
    )
                      for name in row["ppms"]})
    semantic = [
        _snorlax_srm_readback(
            work, "route16-snorlax-ran.srm",
            group=96, map_=27, x=30, y=13, hidden_flag=0x149F,
        ),
        _snorlax_srm_readback(
            work, "route16-snorlax-caught.srm",
            group=96, map_=27, x=30, y=13, hidden_flag=0x149F,
        ),
        _snorlax_srm_readback(
            work, "route12-snorlax-caught.srm",
            group=96, map_=23, x=12, y=70, hidden_flag=0x149E,
        ),
    ]
    return {
        "status": "PASS", "result": dict(row), "artifacts": artifacts,
        "external_srm_semantic_readback": semantic,
        "framebuffer_artifact_rgb_readback": _framebuffer_readback(
            artifacts, expected_ppms, "Route12/16 Snorlax",
        ),
    }


def validate_fly(value: Any, work: Path) -> dict[str, Any]:
    keys = {
        "schema_version", "status", "case", "preparation_only_host_writes",
        "direct_owner_or_script_calls",
        "start_party_town_map_via_keys", "town_map_visible",
        "context_down_steps", "sequence_steps", "origin", "destination",
        "landing", "landing_overworld", "landing_script_released",
        "landing_controls_unlocked", "start_pressed", "start_menu_opened",
        "back_pressed", "field_input_recovered", "field_framebuffer_fnv1a64",
        "town_map_framebuffer_fnv1a64", "framebuffer_artifact_fnv1a64",
        "framebuffer_artifact_roles", "framebuffer_stage_rgb_fnv1a64",
        "capture", "failed", "untested", "warnings",
    }
    row = _require_map(value, keys, "fly")
    _require_zero_terminal(row, "fly")
    capture = _require_map(row.get("capture"), {
        "message_state_address", "string_address", "printer_entry",
        "printer_entry_preimage_hex", "template_printer_entry",
        "template_printer_entry_preimage_hex", "execution", "active_frames",
        "state_counts", "var_result", "framebuffer", "messages",
        "printer_calls",
    }, "fly capture")
    execution = _require_map(
        capture.get("execution"), {"invalid_control_flow", "first_invalid_pc",
                                   "cpsr", "lr"}, "fly capture execution",
    )
    framebuffer = _require_map(
        capture.get("framebuffer"), {
            "first_fnv1a64", "last_fnv1a64", "changed_frames",
            "maximum_baseline_pixel_difference",
        }, "fly capture framebuffer",
    )
    if row.get("schema_version") != 3 \
            or value.get("status") != "PASS" \
            or value.get("case") != "fly_normal_menu" \
            or value.get("preparation_only_host_writes") is not True \
            or value.get("direct_owner_or_script_calls") != 0 \
            or value.get("start_party_town_map_via_keys") is not True \
            or value.get("town_map_visible") is not True \
            or value.get("origin") != "96/23" \
            or value.get("destination") != "96/4" \
            or value.get("landing") != [6, 6] \
            or value.get("landing_overworld") is not True \
            or value.get("landing_script_released") is not True \
            or value.get("landing_controls_unlocked") is not True \
            or value.get("start_pressed") is not True \
            or value.get("start_menu_opened") is not True \
            or value.get("back_pressed") is not True \
            or value.get("field_input_recovered") is not True \
            or not isinstance(value.get("context_down_steps"), int) \
            or isinstance(value["context_down_steps"], bool) \
            or value["context_down_steps"] < 1 \
            or not isinstance(value.get("sequence_steps"), int) \
            or isinstance(value["sequence_steps"], bool) \
            or value["sequence_steps"] < 1 \
            or any(not isinstance(value.get(key), str)
                   or re.fullmatch(r"[0-9A-F]{16}", value[key]) is None
                   for key in ("field_framebuffer_fnv1a64",
                               "town_map_framebuffer_fnv1a64")) \
            or value["field_framebuffer_fnv1a64"] \
                == value["town_map_framebuffer_fnv1a64"] \
            or execution != {"invalid_control_flow": False,
                              "first_invalid_pc": None,
                              "cpsr": None, "lr": None} \
            or not isinstance(framebuffer.get("changed_frames"), int) \
            or framebuffer["changed_frames"] < 1 \
            or not isinstance(
                framebuffer.get("maximum_baseline_pixel_difference"), int) \
            or framebuffer["maximum_baseline_pixel_difference"] < 1 \
            or value.get("warnings") != 0:
        _fail("engine Fly producer/choice/landing契約不一致")
    framebuffer_hashes, framebuffer_roles = _framebuffer_contract(
        row, "fly", "Fly",
    )
    stage_hashes = _require_map(
        row.get("framebuffer_stage_rgb_fnv1a64"),
        {"origin", "town_map", "landing"}, "Fly framebuffer stage RGB FNV",
    )
    if any(not isinstance(item, str) or _FNV1A64.fullmatch(item) is None
           for item in stage_hashes.values()) \
            or stage_hashes["town_map"] \
                != framebuffer_hashes["fly_normal_menu-town-map.ppm"] \
            or stage_hashes["landing"] \
                != framebuffer_hashes["fly_normal_menu-final.ppm"] \
            or len(set(stage_hashes.values())) != 3:
        _fail("Fly origin/town-map/landing RGB role結合不一致")
    artifacts = {}
    for name in ("fly_normal_menu-town-map.ppm", "fly_normal_menu-final.ppm"):
        artifacts[name] = _artifact(
            work, name, PPM_SIZE, "Fly PPM",
            role="framebuffer_ppm", case="fly",
            expected_rgb_fnv1a64=framebuffer_hashes[name],
            framebuffer_role=framebuffer_roles[name],
        )
    return {
        "status": "PASS", "result": dict(row), "artifacts": artifacts,
        "external_srm_semantic_readback": [],
        "framebuffer_artifact_rgb_readback": _framebuffer_readback(
            artifacts, list(framebuffer_roles), "Fly",
        ),
    }


def validate_result(case: str, value: Any, work: Path,
                    roots: Mapping[str, Any]) -> dict[str, Any]:
    if case == "vermilion":
        return validate_vermilion(value, work, roots)
    if case == "ferry":
        return validate_ferry(value, work, roots)
    if case == "snorlax":
        return validate_snorlax(value, work, roots)
    if case == "fly":
        return validate_fly(value, work)
    _fail(f"unknown case: {case}")


def _environment(identity: Mapping[str, Any]) -> dict[str, str]:
    roots = identity["root_exact"]
    trash = roots["vermilion_trash"]
    snorlax = roots["route16_snorlax"]
    route12_snorlax = roots["route12_snorlax"]
    flute_giver = roots["flute_giver"]
    env = dict(os.environ)
    env.update({
        "EL_GYM_PERSISTENT_FLAG": str(int(identity["contracts"]["vermilion_persistent_flag"], 16)),
        "EL_GYM_TRASH_ROOT_BASE": str(int(trash[0]["root"], 16)),
        "EL_ROUTE16_SNORLAX_ROOT": str(int(snorlax["root"], 16)),
        "EL_ROUTE12_SNORLAX_ROOT": str(int(route12_snorlax["root"], 16)),
        "EL_FLUTE_GIVER_ROOT": str(int(flute_giver["root"], 16)),
        "S61_GIVER_GROUP": "1", "S61_GIVER_MAP": "45",
        "S61_GIVER_START_X": "20", "S61_GIVER_START_Y": "24",
        "S61_GIVER_ACTION_KEY": "16", "S61_GIVER_APPROACH_STEPS": "1",
        "S61_GIVER_LOCAL_ID": "9",
        "S61_SNORLAX_GROUP": "96", "S61_SNORLAX_MAP": "27",
        "S61_SNORLAX_START_X": "29", "S61_SNORLAX_START_Y": "13",
        "S61_SNORLAX_ACTION_KEY": "16", "S61_SNORLAX_APPROACH_STEPS": "1",
        "S61_SNORLAX_LOCAL_ID": "6",
        "S61_FLUTE_FLAG": str(0x119E), "S61_FLUTE_ITEM": "350",
        "S61_SNORLAX_HIDDEN_FLAG": str(0x149F),
        "S61_SNORLAX_SPECIES": "491", "S61_SNORLAX_HIDES_AFTER_FLEE": "true",
        "S61_FLY_ORIGIN_GROUP": "96", "S61_FLY_ORIGIN_MAP": "23",
        "S61_FLY_ORIGIN_X": "14", "S61_FLY_ORIGIN_Y": "72",
        "S61_FLY_CONTEXT_DOWN": "1", "S61_FLY_VISITED_FLAG": str(0x18E4),
        "S61_FLY_DESTINATION_GROUP": "96", "S61_FLY_DESTINATION_MAP": "4",
        "S61_FLY_DESTINATION_X": "6", "S61_FLY_DESTINATION_Y": "6",
        "S61_FLY_MAP_SEQUENCE": (
            "UP:2:60,UP:2:60,UP:2:60,A:2:600,A:2:600"
        ),
    })
    return env


def _parse_single_json(stdout: str, label: str) -> Any:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        _fail(f"{label} JSON stdoutが一意ではありません: {len(lines)} lines")
    try:
        return json.loads(lines[0])
    except json.JSONDecodeError as error:
        _fail(f"{label} JSON不正: {error}")


def _evidence_names(case: str) -> tuple[str, str, str]:
    if case not in _CASE_PRODUCT_ARTIFACTS:
        _fail(f"unknown evidence case: {case}")
    return (f"case-{case}.stdout", f"case-{case}.stderr",
            f"case-{case}.result.json")


def _retain_process_evidence(work: Path, case: str, *, stdout: bytes,
                             stderr: bytes, result: Any) -> dict[str, Any]:
    try:
        stdout_text = stdout.decode("utf-8")
        stderr.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail(f"{case} process stream UTF-8不正: {error}")
    parsed_stdout = _parse_single_json(stdout_text, case)
    canonical = _stable(result).encode("utf-8")
    try:
        parsed_canonical = json.loads(canonical)
    except json.JSONDecodeError as error:  # pragma: no cover - serializer invariant
        _fail(f"{case} canonical result JSON不正: {error}")
    if parsed_stdout != result or parsed_canonical != result:
        _fail(f"{case} stdout result/canonical case-result不一致")
    stdout_name, stderr_name, result_name = _evidence_names(case)
    records = {
        stdout_name: _atomic_retain_bytes(
            work, stdout_name, stdout, role="raw_process_stdout", case=case,
            stale_precleared=True,
        ),
        stderr_name: _atomic_retain_bytes(
            work, stderr_name, stderr, role="raw_process_stderr", case=case,
            stale_precleared=True,
        ),
        result_name: _atomic_retain_bytes(
            work, result_name, canonical, role="canonical_case_result",
            case=case, stale_precleared=True,
        ),
    }
    if stderr:
        _fail(f"{case} raw stderrは空ではありません")
    return {
        "stdout_result_matches_canonical": True, "stderr_empty": True,
        "raw_stdout": stdout_name, "raw_stderr": stderr_name,
        "canonical_case_result": result_name,
        "raw_stdout_sha256": records[stdout_name]["sha256"],
        "canonical_result_sha256": records[result_name]["sha256"],
        "artifacts": records,
    }


def _prepare_work(path: Path) -> Path:
    work = _path(path)
    if work.exists():
        if work.is_symlink() or not work.is_dir():
            _fail("--work-dirは実directoryである必要があります")
        if any(work.iterdir()):
            _fail("--work-dirは空または未作成である必要があります")
    else:
        work.mkdir(parents=True)
    return work


def _prepare_case_work(work: Path, run_index: int, case: str) -> Path:
    if run_index not in (1, 2) or case not in _CASE_PRODUCT_ARTIFACTS:
        _fail("case process work identity不正")
    directory = work / f"run-{run_index}" / case
    if directory.exists():
        if directory.is_symlink() or not directory.is_dir():
            _fail("case process workは実directoryではありません")
        if any(directory.iterdir()):
            _fail("各case process workは開始時に空である必要があります")
    else:
        directory.mkdir(parents=True)
    _preclear_exact(
        directory,
        (*_CASE_PRODUCT_ARTIFACTS[case], *_evidence_names(case)),
        f"{case} run{run_index} stale preclear",
    )
    return directory


def _normalized_run_payload(validated: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = validated.get("artifacts")
    if not isinstance(artifacts, Mapping):
        _fail("normalized run artifacts不正")
    normalized_artifacts: dict[str, Any] = {}
    for name, artifact in sorted(artifacts.items()):
        if not isinstance(name, str) or not isinstance(artifact, Mapping):
            _fail("normalized run artifact entry不正")
        normalized_artifacts[name] = {
            key: artifact.get(key)
            for key in ("size", "sha256", "role", "case",
                        "stale_precleared", "atomic_retained",
                        "rgb_fnv1a64", "framebuffer_role")
        }
    semantic = []
    for row in validated.get("external_srm_semantic_readback", []):
        if not isinstance(row, Mapping):
            _fail("normalized external SRM semantic row不正")
        semantic.append({key: value for key, value in row.items() if key != "path"})
    evidence = validated.get("process_evidence")
    if not isinstance(evidence, Mapping):
        _fail("normalized process evidence不正")
    return {
        "result": validated.get("result"),
        "external_srm_semantic_readback": semantic,
        "framebuffer_artifact_rgb_readback": validated.get(
            "framebuffer_artifact_rgb_readback"
        ),
        "process_evidence": {
            key: value for key, value in evidence.items() if key != "artifacts"
        },
        "artifacts": normalized_artifacts,
    }


def _require_exact_runs(runs: int) -> None:
    if isinstance(runs, bool) or runs != REQUIRED_RUNS:
        _fail(f"--runsはexact {REQUIRED_RUNS}である必要があります")


def run(rom: Path, metadata: Path, output: Path | None, work_dir: Path,
        expected_rom_sha256: str | None = None,
        runs: int = REQUIRED_RUNS) -> dict[str, Any]:
    _require_exact_runs(runs)
    identity = read_identity(rom, metadata, expected_rom_sha256)
    work = _prepare_work(work_dir)
    executable = work / "toolchain" / "stage61-event-lifecycle"
    compile_info = compile_runner(executable)
    environment = _environment(identity)
    cases: dict[str, Any] = {}
    for case in ("vermilion", "ferry", "snorlax", "fly"):
        case_runs: list[dict[str, Any]] = []
        normalized_hashes: list[str] = []
        for run_index in range(1, runs + 1):
            case_work = _prepare_case_work(work, run_index, case)
            completed = subprocess.run(
                [str(executable), identity["rom"], str(case_work), case],
                cwd=ROOT, env=environment, text=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=3600, check=False,
            )
            if completed.returncode:
                _atomic_retain_bytes(
                    case_work, f"case-{case}.stdout", completed.stdout,
                    role="raw_process_stdout", case=case,
                    stale_precleared=True,
                )
                _atomic_retain_bytes(
                    case_work, f"case-{case}.stderr", completed.stderr,
                    role="raw_process_stderr", case=case,
                    stale_precleared=True,
                )
                detail = (completed.stderr or completed.stdout).decode(
                    "utf-8", errors="replace",
                )
                _fail(
                    f"mGBA event lifecycle {case} run{run_index}失敗 "
                    f"exit={completed.returncode}: " + detail[-12000:]
                )
            try:
                stdout_text = completed.stdout.decode("utf-8")
            except UnicodeDecodeError as error:
                _fail(f"{case} run{run_index} stdout UTF-8不正: {error}")
            raw = _parse_single_json(stdout_text, f"{case} run{run_index}")
            process_evidence = _retain_process_evidence(
                case_work, case, stdout=completed.stdout,
                stderr=completed.stderr, result=raw,
            )
            validated = validate_result(
                case, raw, case_work, identity["root_exact"],
            )
            validated["process_evidence"] = {
                key: value for key, value in process_evidence.items()
                if key != "artifacts"
            }
            validated["artifacts"].update(process_evidence["artifacts"])
            normalized_payload = _normalized_run_payload(validated)
            normalized_sha256 = _sha256(
                _stable(normalized_payload).encode("utf-8")
            )
            normalized_hashes.append(normalized_sha256)
            case_runs.append({
                "schema_version": 1, "status": "PASS",
                "run_index": run_index, "independent_os_process": True,
                "empty_case_directory_at_start": True,
                "work_directory": str(case_work.resolve()),
                "normalized_sha256": normalized_sha256,
                **validated,
                "failed": 0, "untested": 0, "warnings": 0,
            })
        if len(set(normalized_hashes)) != 1:
            _fail(f"{case} independent run normalized hash不一致")
        cases[case] = {
            "schema_version": 1, "status": "PASS", "run_count": runs,
            "independent_os_processes": True,
            "normalized_sha256": normalized_hashes[0],
            "normalized_hashes_match": True, "runs": case_runs,
            "failed": 0, "untested": 0, "warnings": 0,
        }
    artifacts: dict[str, Any] = {}
    for case_name, case in cases.items():
        for case_run in case["runs"]:
            for name, artifact in case_run["artifacts"].items():
                logical = f"run-{case_run['run_index']}/{case_name}/{name}"
                if logical in artifacts:
                    _fail(f"artifact logical path衝突: {logical}")
                artifacts[logical] = artifact
    role_counts = {
        role: sum(1 for artifact in artifacts.values()
                  if artifact.get("role") == role)
        for role in (
            "external_srm_full_readback", "framebuffer_ppm",
            "raw_process_stdout", "raw_process_stderr",
            "canonical_case_result",
        )
    }
    expected_role_counts = {
        "external_srm_full_readback": 22,
        "framebuffer_ppm": 30,
        "raw_process_stdout": 8,
        "raw_process_stderr": 8,
        "canonical_case_result": 8,
    }
    if role_counts != expected_role_counts or len(artifacts) != 76:
        _fail("event lifecycle retained artifact role/count不一致")
    ppm_rgb_join_count = sum(
        1 for artifact in artifacts.values()
        if artifact.get("role") == "framebuffer_ppm"
        and _FNV1A64.fullmatch(str(artifact.get("rgb_fnv1a64"))) is not None
        and isinstance(artifact.get("framebuffer_role"), str)
        and bool(artifact["framebuffer_role"])
    )
    if ppm_rgb_join_count != 30:
        _fail("event lifecycle PPM RGB FNV/role join件数不一致")
    report = {
        "schema_version": 1, "stage": STAGE, "task": TASK,
        "status": "PASS", "identity": identity, "sources": compile_info,
        "runs_per_case": runs, "independent_process_count": runs * len(cases),
        "cases": cases,
        "coverage": {
            "vermilion_switch_failure_success_reentry": True,
            "ferry_all_seven_cancel_board_arrive_save_continue": True,
            "route16_natural_producer_no_run_caught_reentry": True,
            "route12_species491_real_bag_caught_party_field_reentry": True,
            "route12_route16_external_srm_semantic_readback": True,
            "engine_teleport_real_producer_choice": True,
            "each_case_two_independent_os_processes": True,
            "normalized_hash_match_per_case": True,
            "owner_roots_resolved_from_rom": 25,
            "full_srm_sha256_count": role_counts["external_srm_full_readback"],
            "ppm_sha256_count": role_counts["framebuffer_ppm"],
            "ppm_rgb_fnv1a64_join_count": ppm_rgb_join_count,
            "raw_stdout_count": role_counts["raw_process_stdout"],
            "raw_stderr_count": role_counts["raw_process_stderr"],
            "canonical_case_result_count": role_counts["canonical_case_result"],
            "retained_artifact_count": len(artifacts),
            "direct_owner_or_script_calls": 0,
        },
        "artifacts": artifacts,
        "failed": 0, "untested": 0, "warnings": 0,
    }
    if output is not None:
        destination = _path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_retain_bytes(
            destination.parent, destination.name,
            _stable(report).encode("utf-8"), role="final_report",
            case="orchestrator", stale_precleared=False,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--expected-rom-sha256")
    parser.add_argument("--runs", type=int, default=REQUIRED_RUNS)
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()
    try:
        _require_exact_runs(args.runs)
    except Stage61EventLifecycleError as error:
        print(f"ERROR: {error}", file=os.sys.stderr)
        return 1
    if args.compile_only:
        with tempfile.TemporaryDirectory(prefix="stage61-event-lifecycle-compile-") as tmp:
            value = compile_runner(Path(tmp) / "runner")
        print(_stable({"schema_version": 1, "status": "PASS",
                       "compile": value}), end="")
        return 0
    try:
        report = run(args.rom, args.metadata, args.output, args.work_dir,
                     args.expected_rom_sha256, args.runs)
    except Stage61EventLifecycleError as error:
        print(f"ERROR: {error}", file=os.sys.stderr)
        return 1
    print(_stable(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
