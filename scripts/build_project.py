#!/usr/bin/env python3
"""T03: clean ROMから再構築可能なVega no-op module harnessを生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.common import (  # noqa: E402
    input_expectations,
    load_toml,
    output_expectations,
    resolved_input_paths,
    sha256_file,
    stable_digest,
    verified_hashes,
    write_json,
)
from tools.rom_allocator import (  # noqa: E402
    GBA_ROM_BASE,
    ROM_SIZE,
    build_allocation_report_from_csv,
    load_regions_csv,
)


SCHEMA_VERSION = 1
TASK_ID = "T03"
STAGE_ROM = Path("build/stages/03_harness.gba")
STAGE_METADATA = Path("build/stages/03_harness.json")
ALLOCATION_REPORT = Path("build/stages/03_allocation.json")
MODULE_OUTPUT = Path("build/modules/vega_adapter")
SMOKE_REPORT = Path("reports/generated/harness_smoke.md")
MODULE_ARTIFACTS = (
    "vega_adapter.bin",
    "vega_adapter.elf",
    "vega_adapter.map",
    "metadata.json",
)
FINGERPRINT_FILES = (
    "Makefile",
    "config/project.toml",
    "config/rom_regions.csv",
    "config/harness_smoke.json",
    "infra/toolchain_manifest.json",
    "scripts/build_project.py",
    "scripts/common.py",
    "tools/rom_allocator.py",
    "tools/mgba_harness_smoke.c",
    "overlays/vega_adapter/Makefile",
    "overlays/vega_adapter/README.md",
    "overlays/vega_adapter/build_module.py",
    "overlays/vega_adapter/linker.ld",
    "overlays/vega_adapter/module.S",
)


class HarnessBuildError(RuntimeError):
    """T03 build contract違反。"""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _byte_hashes(data: bytes) -> dict[str, str | int]:
    return {
        "size": len(data),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": _sha256_bytes(data),
    }


def _require_hashes(
    actual: Mapping[str, str | int],
    expected: Mapping[str, str | int],
    label: str,
) -> None:
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if key == "size":
            matches = actual_value == int(expected_value)
        else:
            matches = str(actual_value).lower() == str(expected_value).lower()
        if not matches:
            mismatches.append(f"{key}: expected {expected_value}, got {actual_value}")
    if mismatches:
        raise HarnessBuildError(f"{label} hash mismatch ({'; '.join(mismatches)})")


def apply_ips(source: bytes, patch: bytes) -> bytes:
    """IPSをmemory上のcopyへ適用する。入力bytesは変更しない。"""

    if not patch.startswith(b"PATCH"):
        raise HarnessBuildError("IPS header is missing")
    output = bytearray(source)
    cursor = 5
    saw_eof = False
    while cursor + 3 <= len(patch):
        if patch[cursor : cursor + 3] == b"EOF":
            cursor += 3
            saw_eof = True
            break
        if cursor + 5 > len(patch):
            raise HarnessBuildError("IPS record header is truncated")
        offset = int.from_bytes(patch[cursor : cursor + 3], "big")
        size = int.from_bytes(patch[cursor + 3 : cursor + 5], "big")
        cursor += 5
        if size:
            end = cursor + size
            if end > len(patch):
                raise HarnessBuildError("IPS literal record is truncated")
            payload = patch[cursor:end]
            cursor = end
        else:
            if cursor + 3 > len(patch):
                raise HarnessBuildError("IPS RLE record is truncated")
            run = int.from_bytes(patch[cursor : cursor + 2], "big")
            if run == 0:
                raise HarnessBuildError("IPS RLE record has zero length")
            payload = patch[cursor + 2 : cursor + 3] * run
            cursor += 3
        end_offset = offset + len(payload)
        if end_offset > len(output):
            output.extend(b"\x00" * (end_offset - len(output)))
        output[offset:end_offset] = payload
    if not saw_eof:
        raise HarnessBuildError("IPS EOF marker is missing")
    remaining = len(patch) - cursor
    if remaining == 3:
        truncate_size = int.from_bytes(patch[cursor : cursor + 3], "big")
        if truncate_size > len(output):
            output.extend(b"\x00" * (truncate_size - len(output)))
        else:
            del output[truncate_size:]
    elif remaining:
        raise HarnessBuildError("IPS has trailing bytes after EOF")
    return bytes(output)


def expand_rom_ff(source: bytes, target_size: int = ROM_SIZE) -> bytes:
    if isinstance(target_size, bool) or not isinstance(target_size, int):
        raise HarnessBuildError("ROM target size must be an integer")
    if target_size < len(source):
        raise HarnessBuildError("ROM expansion target is smaller than source")
    return source + b"\xFF" * (target_size - len(source))


def gba_header_checksum(rom: bytes) -> int:
    if len(rom) < 0xBE:
        raise HarnessBuildError("ROM is too short for a GBA header")
    return (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF


def validate_gba_header(
    rom: bytes, *, expected_title: str, expected_game_code: str
) -> dict[str, Any]:
    try:
        title = rom[0xA0:0xAC].decode("ascii")
        game_code = rom[0xAC:0xB0].decode("ascii")
    except UnicodeDecodeError as error:
        raise HarnessBuildError("GBA header title/code is not ASCII") from error
    stored = rom[0xBD]
    computed = gba_header_checksum(rom)
    if title != expected_title or game_code != expected_game_code:
        raise HarnessBuildError(
            f"GBA header identity mismatch: title={title!r}, code={game_code!r}"
        )
    if stored != computed:
        raise HarnessBuildError(
            f"GBA header checksum mismatch: stored={stored:#04x}, computed={computed:#04x}"
        )
    return {
        "title_ascii": title,
        "game_code_ascii": game_code,
        "stored_checksum": stored,
        "computed_checksum": computed,
        "checksum_fix_applied": False,
    }


def expected_byte_assertions(
    rom: bytes,
    symbols: Mapping[str, object],
    expected: Mapping[str, object],
) -> list[dict[str, Any]]:
    if set(expected) - set(symbols):
        raise HarnessBuildError("expected entry bytes reference an unknown symbol")
    rows: list[dict[str, Any]] = []
    for name in sorted(expected):
        address = int(str(symbols[name]), 0)
        if not GBA_ROM_BASE <= (address & ~1) < GBA_ROM_BASE + len(rom):
            raise HarnessBuildError(f"expected-byte symbol is outside ROM: {name}")
        try:
            wanted = bytes.fromhex(str(expected[name]))
        except ValueError as error:
            raise HarnessBuildError(f"expected bytes are invalid hex: {name}") from error
        if not wanted:
            raise HarnessBuildError(f"expected bytes are empty: {name}")
        offset = (address & ~1) - GBA_ROM_BASE
        actual = rom[offset : offset + len(wanted)]
        if actual != wanted:
            raise HarnessBuildError(
                f"expected-byte assertion failed at {name}: "
                f"expected {wanted.hex()}, got {actual.hex()}"
            )
        rows.append(
            {
                "name": name,
                "gba_address": f"0x{address:08X}",
                "rom_offset": f"0x{offset:08X}",
                "size": len(wanted),
                "expected_hex": wanted.hex(),
                "actual_hex": actual.hex(),
                "status": "PASS",
            }
        )
    return rows


def insert_declared_module(
    expanded: bytes,
    module: bytes,
    *,
    start: int,
    expected_fill: int,
) -> tuple[bytes, dict[str, Any]]:
    if not 0 <= expected_fill <= 0xFF:
        raise HarnessBuildError("module destination expected byte is outside u8")
    end = start + len(module)
    if not module or not 0 <= start < end <= len(expanded):
        raise HarnessBuildError("module allocation is empty or outside ROM")
    destination = expanded[start:end]
    if destination != bytes([expected_fill]) * len(module):
        raise HarnessBuildError("module destination expected-byte assertion failed")
    candidate = bytearray(expanded)
    candidate[start:end] = module
    result = bytes(candidate)
    if result[:start] != expanded[:start] or result[end:] != expanded[end:]:
        raise HarnessBuildError("module insertion changed bytes outside its allocation")
    return result, {
        "name": "vega_adapter_module_destination",
        "rom_offset": f"0x{start:08X}",
        "gba_address": f"0x{GBA_ROM_BASE + start:08X}",
        "end_exclusive": f"0x{end:08X}",
        "size": len(module),
        "expected_byte": expected_fill,
        "status": "PASS",
    }


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HarnessBuildError(f"cannot read {label}") from error
    if not isinstance(value, dict):
        raise HarnessBuildError(f"{label} must be a JSON object")
    return value


def _tool_environment() -> dict[str, str]:
    return {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "SOURCE_DATE_EPOCH": "0",
        "TZ": "UTC",
        "XDG_CONFIG_HOME": "/nonexistent",
        "XDG_DATA_HOME": "/nonexistent",
    }


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    require_empty_stderr: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=_tool_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.decode("utf-8", "replace")[-2000:]
        if not message:
            message = completed.stdout.decode("utf-8", "replace")[-2000:]
        raise HarnessBuildError(
            f"command failed ({completed.returncode}): {Path(command[0]).name}: {message}"
        )
    if require_empty_stderr and completed.stderr:
        raise HarnessBuildError(
            "command emitted stderr: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    return completed


def _verify_file_sha(path_value: object, digest_value: object, label: str) -> Path:
    path = Path(str(path_value))
    digest = str(digest_value)
    if not path.is_absolute() or not path.is_file():
        raise HarnessBuildError(f"pinned {label} is not an absolute file")
    actual = sha256_file(path)
    if actual != digest:
        raise HarnessBuildError(f"pinned {label} SHA-256 mismatch: {actual}")
    return path


def _verify_smoke_toolchain(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise HarnessBuildError("toolchain manifest schema_version must be integer 1")
    tools = manifest.get("tools")
    if not isinstance(tools, Mapping):
        raise HarnessBuildError("toolchain manifest tools are missing")
    host_cc = tools.get("host_cc")
    mgba = tools.get("mgba")
    if not isinstance(host_cc, Mapping) or not isinstance(mgba, Mapping):
        raise HarnessBuildError("host_cc/mgba tool contracts are missing")
    compiler = _verify_file_sha(host_cc.get("path"), host_cc.get("sha256"), "host_cc")
    runtime_files = mgba.get("runtime_files")
    if not isinstance(runtime_files, list) or not runtime_files:
        raise HarnessBuildError("mGBA runtime file contracts are missing")
    checked: list[dict[str, str]] = []
    for index, entry in enumerate(runtime_files):
        if not isinstance(entry, Mapping):
            raise HarnessBuildError("invalid mGBA runtime file contract")
        path = _verify_file_sha(
            entry.get("path"), entry.get("sha256"), f"mgba.runtime_files[{index}]"
        )
        checked.append({"name": path.name, "sha256": str(entry["sha256"])})
    return {
        "host_cc": {
            "name": compiler.name,
            "version": str(host_cc.get("version", "")),
            "sha256": str(host_cc["sha256"]),
        },
        "mgba": {
            "version": str(mgba.get("version", "")),
            "sha256": str(mgba.get("sha256", "")),
            "runtime_files": checked,
        },
    }


def _fingerprint_inputs(
    root: Path,
    input_records: Mapping[str, Mapping[str, str | int]],
) -> dict[str, Any]:
    files: dict[str, str] = {}
    for logical in FINGERPRINT_FILES:
        path = root / logical
        if path.is_symlink() or not path.is_file():
            raise HarnessBuildError(f"fingerprint input is missing/non-regular: {logical}")
        files[logical] = sha256_file(path)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_ID,
        "inputs": {
            key: dict(value) for key, value in sorted(input_records.items())
        },
        "files": files,
        "repeat_count": 2,
        "rom_size": ROM_SIZE,
    }


def _build_adapter(root: Path, out_dir: Path, origin: int) -> dict[str, Any]:
    command = [
        "/usr/bin/make",
        "-C",
        str(root / "overlays/vega_adapter"),
        f"OUT_DIR={out_dir}",
        f"ROM_ORIGIN=0x{origin:08X}",
        f"TOOLCHAIN_MANIFEST={root / 'infra/toolchain_manifest.json'}",
    ]
    _run(command, cwd=root, timeout=60)
    metadata = _read_json_object(out_dir / "metadata.json", "adapter metadata")
    if metadata.get("schema_version") != 1:
        raise HarnessBuildError("adapter metadata schema mismatch")
    module = metadata.get("module")
    if not isinstance(module, Mapping):
        raise HarnessBuildError("adapter module metadata is missing")
    if module.get("hook_count") != 0 or module.get("vega_owned_writes") != []:
        raise HarnessBuildError("T03 adapter is not a zero-hook no-op")
    return metadata


def _build_once(
    root: Path,
    directory: Path,
    vega: bytes,
    smoke_config: Mapping[str, Any],
) -> dict[str, Any]:
    regions = load_regions_csv(root / "config/rom_regions.csv")
    integration = next(
        (region for region in regions if region.name == "integration_modules"), None
    )
    if integration is None or integration.kind != "allocatable":
        raise HarnessBuildError("integration_modules allocatable region is missing")
    origin = GBA_ROM_BASE + integration.start
    adapter_dir = directory / "adapter"
    adapter_dir.mkdir(parents=True)
    adapter_metadata = _build_adapter(root, adapter_dir, origin)
    module = (adapter_dir / "vega_adapter.bin").read_bytes()
    request = adapter_metadata.get("allocator_request")
    if not isinstance(request, Mapping):
        raise HarnessBuildError("adapter allocator request is missing")
    allocation = build_allocation_report_from_csv(
        root / "config/rom_regions.csv", [request]
    )
    if allocation["summaries"]["overlap_count"] != 0:
        raise HarnessBuildError("allocator reported an overlap")
    allocation_row = allocation["allocations"][0]
    if allocation_row["start"] != integration.start:
        raise HarnessBuildError("adapter was not placed at integration_modules start")
    if allocation_row["content_sha256"] != _sha256_bytes(module):
        raise HarnessBuildError("allocator content hash does not match adapter")

    expanded = expand_rom_ff(vega, ROM_SIZE)
    candidate, destination_assertion = insert_declared_module(
        expanded,
        module,
        start=allocation_row["start"],
        expected_fill=int(smoke_config["module_destination_expected_byte"]),
    )
    if candidate[: len(vega)] != vega:
        raise HarnessBuildError("no-op module changed Vega-owned bytes")
    rom_path = directory / "03_harness.gba"
    rom_path.write_bytes(candidate)
    rom_path.chmod(0o600)
    return {
        "rom": rom_path,
        "adapter_dir": adapter_dir,
        "adapter_metadata": adapter_metadata,
        "allocation": allocation,
        "destination_assertion": destination_assertion,
        "module_start": allocation_row["start"],
        "module_end": allocation_row["end_exclusive"],
    }


def _compare_builds(first: Mapping[str, Any], second: Mapping[str, Any]) -> None:
    if Path(first["rom"]).read_bytes() != Path(second["rom"]).read_bytes():
        raise HarnessBuildError("two consecutive harness ROM builds differ")
    for name in MODULE_ARTIFACTS:
        left = Path(first["adapter_dir"]) / name
        right = Path(second["adapter_dir"]) / name
        if left.read_bytes() != right.read_bytes():
            raise HarnessBuildError(f"two consecutive adapter artifacts differ: {name}")
    if first["allocation"] != second["allocation"]:
        raise HarnessBuildError("two consecutive allocation reports differ")


def _compile_smoke_runner(
    root: Path, out_path: Path, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    toolchain = _verify_smoke_toolchain(manifest)
    compiler = str(manifest["tools"]["host_cc"]["path"])
    source = root / "tools/mgba_harness_smoke.c"
    _run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(source),
            "-o",
            str(out_path),
            "-lmgba",
        ],
        cwd=root,
        timeout=60,
        require_empty_stderr=True,
    )
    out_path.chmod(0o700)
    toolchain["runner"] = {
        "source_sha256": sha256_file(source),
        "binary_sha256": sha256_file(out_path),
        "compiler_flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"],
    }
    return toolchain


def _run_smoke(
    root: Path,
    runner: Path,
    reference: Path,
    candidate: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    symbols = config.get("symbols")
    if not isinstance(symbols, Mapping):
        raise HarnessBuildError("smoke symbols are missing")
    if config.get("fixed_rtc_unix") != 946684800:
        raise HarnessBuildError("smoke fixed RTC contract mismatch")
    if config.get("saveblock1") != {"position_offset": 0, "location_offset": 4}:
        raise HarnessBuildError("smoke SaveBlock1 layout contract mismatch")
    movement_keys = config.get("movement_keys")
    if not isinstance(movement_keys, list) or not movement_keys:
        raise HarnessBuildError("smoke movement key list is missing")
    command = [
        str(runner),
        str(reference),
        str(candidate),
        str(symbols["TrySavingData"]),
        str(symbols["Save_LoadGameData"]),
        str(symbols["gSaveBlock1"]),
        str(config["title_frames"]),
        str(config["trace_segments"]),
        str(config["settle_frames"]),
        str(config["movement_frames"]),
        str(config["save_status_ok"]),
        ",".join(str(value) for value in movement_keys),
        str(config["expected_title_framebuffer_fnv1a64"]),
    ]
    completed = _run(
        command,
        cwd=root,
        timeout=120,
        require_empty_stderr=True,
    )
    try:
        result = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HarnessBuildError("smoke runner stdout is not one JSON document") from error
    validate_smoke_result(result, config)
    return result


def validate_smoke_result(result: object, config: Mapping[str, Any]) -> None:
    """保存済み／fresh実行のsmoke JSONを同じ契約で検証する。"""

    if (
        not isinstance(result, dict)
        or result.get("schema_version") != 1
        or result.get("status") != "PASS"
        or result.get("measurement") != "libmGBA_reference_candidate_behavior"
        or result.get("artifacts_written") != []
    ):
        raise HarnessBuildError("smoke runner did not return PASS")
    required_checks = {
        "title",
        "new_game",
        "basic_map_movement",
        "save",
        "load",
        "observable_equivalence",
    }
    checks = result.get("checks")
    if not isinstance(checks, Mapping) or any(checks.get(key) is not True for key in required_checks):
        raise HarnessBuildError("smoke runner required checks are incomplete")
    if result.get("reference") != result.get("candidate"):
        raise HarnessBuildError("smoke reference/candidate observations differ")
    observation = result.get("candidate")
    if not isinstance(observation, Mapping):
        raise HarnessBuildError("smoke candidate observation is missing")
    if observation.get("title_framebuffer_fnv1a64") != config.get(
        "expected_title_framebuffer_fnv1a64"
    ):
        raise HarnessBuildError("smoke title checkpoint hash mismatch")
    transitions = observation.get("title_pixel_transitions")
    new_game = observation.get("new_game")
    movement = observation.get("movement")
    load = observation.get("load")
    save = observation.get("save")
    if (
        not isinstance(transitions, int)
        or transitions < 100
        or not isinstance(new_game, Mapping)
        or not isinstance(movement, Mapping)
        or dict(new_game) != config.get("expected_new_game")
        or dict(movement) != config.get("expected_movement")
        or new_game.get("map_group", -1) < 0
        or new_game.get("map_number", -1) < 0
        or (new_game.get("x"), new_game.get("y"))
        == (movement.get("x"), movement.get("y"))
        or movement.get("key") not in config.get("movement_keys", [])
        or not isinstance(load, Mapping)
        or load.get("fresh_core") is not True
        or load.get("restored") is not True
        or load.get("status") != config.get("save_status_ok")
        or not isinstance(save, Mapping)
        or save.get("size") != 0x20000
        or save.get("status") != config.get("save_status_ok")
    ):
        raise HarnessBuildError("smoke fresh-core save/load contract failed")


def _atomic_write_bytes(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _render_report(metadata: Mapping[str, Any]) -> str:
    smoke = metadata["smoke"]["candidate"]
    allocation = metadata["allocation"]["allocations"][0]
    assertions = metadata["expected_byte_assertions"]
    rows = "\n".join(
        "| {name} | {gba_address} | {expected_hex} | {status} |".format(**row)
        for row in assertions
    )
    return f"""# T03 Vega module harness smoke

- Status: `PASS`
- Fingerprint: `{metadata['fingerprint']}`
- Output ROM SHA-256: `{metadata['outputs']['rom']['sha256']}`
- 連続2 build: byte-identical

## Stage

1. 固定clean ROMへ固定Vega IPSをmemory上で適用し、既知Vega SHA-256と照合。
2. 16 MiBから32 MiBへ `0xFF` で拡張。
3. no-op Thumb moduleをfile offset `{allocation['start']:#010x}` / GBA `{allocation['gba_start']:#010x}` へ配置。
4. Vega-owned 16 MiBはbyte-identical、宣言allocation外の変更は0 byte。

Allocator overlap: `{metadata['allocation']['summaries']['overlap_count']}`。module hook/repoint count: `0`。
GBA header checksumは入力時点で正しく、修正していない。

## Expected-byte assertions

| Site | GBA address | Expected | Status |
|---|---:|---|---|
{rows}

module destination `{metadata['module_destination_assertion']['gba_address']}` から
`{metadata['module_destination_assertion']['size']}` bytesは、挿入前にすべて
`0x{metadata['module_destination_assertion']['expected_byte']:02X}` であることを確認した。

## libmGBA smoke

- title: fixed frame `{metadata['smoke_contract']['title_frames']}`、framebuffer FNV-1a64 `{smoke['title_framebuffer_fnv1a64']}`
- new game: 通常入力traceで map `{smoke['new_game']['map_group']}/{smoke['new_game']['map_number']}`、座標 `{smoke['new_game']['x']},{smoke['new_game']['y']}`
- movement: key `{smoke['movement']['key']}` で `{smoke['movement']['x']},{smoke['movement']['y']}` へ移動
- save: Vega `TrySavingData` status `{smoke['save']['status']}`、128 KiB flashへ書込み
- load: 新しいmGBA coreへsaveを再attach・reset後、Vega `Save_LoadGameData` status `{smoke['load']['status']}` で座標/map復元
- reference Vega / candidate harness observable-equivalence: `PASS`

raw ROM、save、framebuffer、RAM dumpはreportへ出力していない。
"""


def _publish(
    root: Path,
    first: Mapping[str, Any],
    metadata: dict[str, Any],
) -> None:
    stage_rom = root / STAGE_ROM
    module_output = root / MODULE_OUTPUT
    _atomic_write_bytes(stage_rom, Path(first["rom"]).read_bytes(), 0o600)
    module_output.mkdir(parents=True, exist_ok=True)
    for name in MODULE_ARTIFACTS:
        source = Path(first["adapter_dir"]) / name
        _atomic_write_bytes(module_output / name, source.read_bytes(), 0o644)
    write_json(root / ALLOCATION_REPORT, metadata["allocation"])
    (root / ALLOCATION_REPORT).chmod(0o644)
    write_json(root / STAGE_METADATA, metadata)
    (root / STAGE_METADATA).chmod(0o644)
    report = _render_report(metadata)
    _atomic_write_bytes(root / SMOKE_REPORT, report.encode("utf-8"), 0o644)


def _input_records(
    root: Path, config: Mapping[str, Any]
) -> tuple[dict[str, dict[str, str | int]], dict[str, Path]]:
    paths = resolved_input_paths(root, dict(config))
    expected = config["expected"]
    clean = verified_hashes(
        paths["clean_rom"], input_expectations(expected, "clean_rom"), "clean_rom"
    )
    ips = verified_hashes(
        paths["vega_ips"], input_expectations(expected, "vega_ips"), "vega_ips"
    )
    return {"clean_rom": clean, "vega_ips": ips}, paths


def build_harness(root: Path, config_path: Path) -> dict[str, Any]:
    config = load_toml(config_path)
    input_records, paths = _input_records(root, config)
    clean = paths["clean_rom"].read_bytes()
    vega = apply_ips(clean, paths["vega_ips"].read_bytes())
    vega_hashes = _byte_hashes(vega)
    _require_hashes(vega_hashes, output_expectations(config["expected"], "vega"), "vega")
    smoke_config = _read_json_object(root / "config/harness_smoke.json", "smoke config")
    if smoke_config.get("schema_version") != SCHEMA_VERSION:
        raise HarnessBuildError("smoke config schema_version must be 1")
    header = validate_gba_header(
        vega,
        expected_title=str(smoke_config["expected_game_title_ascii"]),
        expected_game_code=str(smoke_config["expected_game_code_ascii"]),
    )
    assertions = expected_byte_assertions(
        vega,
        smoke_config["symbols"],
        smoke_config["expected_entry_bytes"],
    )
    manifest = _read_json_object(
        root / "infra/toolchain_manifest.json", "toolchain manifest"
    )
    fingerprint_inputs = _fingerprint_inputs(root, input_records)
    fingerprint = stable_digest(fingerprint_inputs)

    build_root = root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".t03-harness-", dir=build_root) as raw:
        work = Path(raw)
        reference = work / "vega.gba"
        reference.write_bytes(vega)
        reference.chmod(0o600)
        first = _build_once(root, work / "run-1", vega, smoke_config)
        second = _build_once(root, work / "run-2", vega, smoke_config)
        _compare_builds(first, second)
        candidate_bytes = Path(first["rom"]).read_bytes()
        candidate_header = validate_gba_header(
            candidate_bytes,
            expected_title=str(smoke_config["expected_game_title_ascii"]),
            expected_game_code=str(smoke_config["expected_game_code_ascii"]),
        )
        if candidate_header != header:
            raise HarnessBuildError("harness unexpectedly changed the GBA header")
        runner = work / "mgba_harness_smoke"
        toolchain = _compile_smoke_runner(root, runner, manifest)
        smoke = _run_smoke(
            root, runner, reference, Path(first["rom"]), smoke_config
        )
        rom_record = _byte_hashes(candidate_bytes)
        module_metadata = first["adapter_metadata"]
        metadata: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "task": TASK_ID,
            "fingerprint": fingerprint,
            "fingerprint_inputs": fingerprint_inputs,
            "inputs": {
                "clean_rom": input_records["clean_rom"],
                "vega_ips": input_records["vega_ips"],
                "vega_reference": vega_hashes,
            },
            "outputs": {
                "rom": rom_record,
                "module": module_metadata["artifacts"]["vega_adapter.bin"],
            },
            "repeatability": {
                "runs": 2,
                "rom_byte_identical": True,
                "adapter_artifacts_byte_identical": True,
                "allocation_report_identical": True,
            },
            "layout": {
                "rom_size": ROM_SIZE,
                "vega_owned_start": 0,
                "vega_owned_end_exclusive": len(vega),
                "vega_owned_changed_bytes": 0,
                "declared_write_count": 1,
                "declared_write_start": first["module_start"],
                "declared_write_end_exclusive": first["module_end"],
                "bytes_changed_outside_declared_writes": 0,
            },
            "header": header,
            "expected_byte_assertions": assertions,
            "module_destination_assertion": first["destination_assertion"],
            "module_metadata": module_metadata,
            "allocation": first["allocation"],
            "smoke_contract": smoke_config,
            "smoke": smoke,
            "toolchain": toolchain,
            "artifacts_written": [
                STAGE_ROM.as_posix(),
                STAGE_METADATA.as_posix(),
                ALLOCATION_REPORT.as_posix(),
                *(f"{MODULE_OUTPUT.as_posix()}/{name}" for name in MODULE_ARTIFACTS),
                SMOKE_REPORT.as_posix(),
            ],
        }
        _publish(root, first, metadata)
    return metadata


def check_harness(root: Path, config_path: Path) -> dict[str, Any]:
    metadata = _read_json_object(root / STAGE_METADATA, "published harness metadata")
    if metadata.get("schema_version") != 1 or metadata.get("status") != "PASS":
        raise HarnessBuildError("published harness metadata is not PASS schema 1")
    config = load_toml(config_path)
    input_records, paths = _input_records(root, config)
    current_inputs = _fingerprint_inputs(root, input_records)
    current_fingerprint = stable_digest(current_inputs)
    if metadata.get("fingerprint_inputs") != current_inputs:
        raise HarnessBuildError("published harness fingerprint inputs are stale")
    if metadata.get("fingerprint") != current_fingerprint:
        raise HarnessBuildError("published harness fingerprint is stale")

    rom_path = root / STAGE_ROM
    if rom_path.is_symlink() or not rom_path.is_file():
        raise HarnessBuildError("published harness ROM is missing/non-regular")
    rom = rom_path.read_bytes()
    _require_hashes(_byte_hashes(rom), metadata["outputs"]["rom"], "published ROM")
    clean = paths["clean_rom"].read_bytes()
    vega = apply_ips(clean, paths["vega_ips"].read_bytes())
    vega_hashes = _byte_hashes(vega)
    if metadata.get("inputs") != {
        "clean_rom": input_records["clean_rom"],
        "vega_ips": input_records["vega_ips"],
        "vega_reference": vega_hashes,
    }:
        raise HarnessBuildError("published input provenance is stale")
    smoke_config = _read_json_object(root / "config/harness_smoke.json", "smoke config")
    if metadata.get("smoke_contract") != smoke_config:
        raise HarnessBuildError("published smoke contract is stale")
    header = validate_gba_header(
        rom,
        expected_title=str(smoke_config["expected_game_title_ascii"]),
        expected_game_code=str(smoke_config["expected_game_code_ascii"]),
    )
    if metadata.get("header") != header:
        raise HarnessBuildError("published GBA header contract is stale")
    validate_smoke_result(metadata.get("smoke"), smoke_config)
    assertions = expected_byte_assertions(
        vega, smoke_config["symbols"], smoke_config["expected_entry_bytes"]
    )
    if metadata.get("expected_byte_assertions") != assertions:
        raise HarnessBuildError("published expected-byte assertions are stale")
    if rom[: len(vega)] != vega:
        raise HarnessBuildError("published harness changed Vega-owned bytes")
    layout = metadata["layout"]
    start = int(layout["declared_write_start"])
    end = int(layout["declared_write_end_exclusive"])
    if metadata.get("repeatability") != {
        "runs": 2,
        "rom_byte_identical": True,
        "adapter_artifacts_byte_identical": True,
        "allocation_report_identical": True,
    }:
        raise HarnessBuildError("published repeatability contract is stale")
    if layout != {
        "rom_size": ROM_SIZE,
        "vega_owned_start": 0,
        "vega_owned_end_exclusive": len(vega),
        "vega_owned_changed_bytes": 0,
        "declared_write_count": 1,
        "declared_write_start": start,
        "declared_write_end_exclusive": end,
        "bytes_changed_outside_declared_writes": 0,
    }:
        raise HarnessBuildError("published ROM layout contract is stale")
    expanded = expand_rom_ff(vega, ROM_SIZE)
    module_path = root / MODULE_OUTPUT / "vega_adapter.bin"
    module_bytes = module_path.read_bytes()
    rebuilt, destination_assertion = insert_declared_module(
        expanded,
        module_bytes,
        start=start,
        expected_fill=int(smoke_config["module_destination_expected_byte"]),
    )
    if rom != rebuilt:
        raise HarnessBuildError("published harness differs outside declared module insertion")
    if metadata.get("module_destination_assertion") != destination_assertion:
        raise HarnessBuildError("published module destination assertion is stale")

    module_metadata = _read_json_object(
        root / MODULE_OUTPUT / "metadata.json", "published module metadata"
    )
    if metadata.get("module_metadata") != module_metadata:
        raise HarnessBuildError("published stage/module metadata cross-link is stale")
    if metadata.get("outputs", {}).get("module") != module_metadata.get(
        "artifacts", {}
    ).get("vega_adapter.bin"):
        raise HarnessBuildError("published module output identity is stale")
    module_contract = module_metadata.get("module")
    if (
        not isinstance(module_contract, Mapping)
        or module_contract.get("hook_count") != 0
        or module_contract.get("hooks") != []
        or module_contract.get("vega_owned_writes") != []
        or module_contract.get("side_effects") != "NONE_UNREFERENCED_BX_LR"
    ):
        raise HarnessBuildError("published module is not the T03 zero-hook no-op")
    allocation = build_allocation_report_from_csv(
        root / "config/rom_regions.csv", [module_metadata["allocator_request"]]
    )
    if allocation != metadata.get("allocation"):
        raise HarnessBuildError("published allocation report is stale")
    if _read_json_object(root / ALLOCATION_REPORT, "published allocation file") != allocation:
        raise HarnessBuildError("published allocation file is stale")
    allocation_row = allocation["allocations"][0]
    if (
        allocation_row["start"] != start
        or allocation_row["end_exclusive"] != end
        or allocation_row["content_sha256"] != _sha256_bytes(module_bytes)
    ):
        raise HarnessBuildError("published layout/allocation/module cross-link is stale")
    for name in MODULE_ARTIFACTS[:3]:
        artifact = module_metadata["artifacts"][name]
        path = root / MODULE_OUTPUT / name
        if path.stat().st_size != artifact["size"] or sha256_file(path) != artifact["sha256"]:
            raise HarnessBuildError(f"published adapter artifact is stale: {name}")
    report_path = root / SMOKE_REPORT
    if not report_path.is_file():
        raise HarnessBuildError("harness smoke report is missing")
    report = report_path.read_text(encoding="utf-8")
    if report != _render_report(metadata):
        raise HarnessBuildError("harness smoke report is stale")
    return {
        "status": "PASS",
        "fingerprint": current_fingerprint,
        "rom_sha256": metadata["outputs"]["rom"]["sha256"],
        "allocation_overlap_count": allocation["summaries"]["overlap_count"],
        "smoke_status": metadata["smoke"]["status"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("harness", "check-harness"):
        command = subparsers.add_parser(name)
        command.add_argument(
            "--config", type=Path, default=ROOT / "config/project.toml"
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config_path = args.config
        if not config_path.is_absolute():
            config_path = ROOT / config_path
        if args.command == "harness":
            result = build_harness(ROOT, config_path)
            summary = {
                "status": result["status"],
                "fingerprint": result["fingerprint"],
                "rom_sha256": result["outputs"]["rom"]["sha256"],
                "allocation_overlap_count": result["allocation"]["summaries"][
                    "overlap_count"
                ],
                "smoke_status": result["smoke"]["status"],
            }
        else:
            summary = check_harness(ROOT, config_path)
    except (HarnessBuildError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
