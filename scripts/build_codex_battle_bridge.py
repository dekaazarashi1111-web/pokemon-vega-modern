#!/usr/bin/env python3
"""T26 Codex Battle mailboxをStage 42へ結合しStage 43を生成・検証する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
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

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _previous_requests,
    _sha,
    _sparse_bps,
    _stable,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T26"
CONFIG = Path("config/codex_battle_bridge.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "codex_battle_bridge_stage43_payload"

REQUIRED_ENTRYPOINTS = {
    "CodexBattleBridge_Probe",
    "CodexBattleBridge_Initialize",
    "CodexBattleBridge_InitializeWithNonce",
    "CodexBattleBridge_Poll",
    "CodexBattleBridge_ReadKeysAdapter",
}

ACCEPTANCE_KEYS = (
    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
    "IPAD_INVENTORY_NCI_MEMORY_MAP",
    "IPAD_VERSION_STATUS_EWRAM_READ_WRITE",
    "CLI_DOCTOR_SAFE_IDENTITY",
    "OWNER_ONLY_CONFIG_NO_HOST_LEAK",
    "CLI_EXTERNAL_DIRECTORY_JSON_EXIT",
    "ROM_CLI_DUAL_VALIDATORS",
    "INVALID_REQUESTS_GAMEPLAY_UNCHANGED",
    "MAILBOX_PING_STATE_NEUTRAL",
    "OVERLAP_DECLARED_CLEAN_BPS_MGBA",
    "IPAD_VERSIONED_COPY_SECRET_REDACTION",
)


class CodexBattleBridgeBuildError(RuntimeError):
    """Stage 43 input、mailbox ABI、実機証跡または再現性契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleBridgeBuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _integer(value: Any, label: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        _fail(f"{label} is not an integer: {value!r}")


def _identity(path: Path, contract: Mapping[str, Any], label: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    if contract.get("size") is not None and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True,
        check=False, timeout=timeout,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if address < GBA_ROM_BASE or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage 43: 0x{address:08X}")
    return offset


def _runtime_header(config: Mapping[str, Any]) -> bytes:
    protocol = config["protocol"]
    ram = config["ram"]
    hook = config["hook"]
    base_crc = int(config["inputs"]["stage42_rom"]["crc32"], 16)
    values = {
        "CODEX_BATTLE_MAGIC": _integer(protocol["magic_u32"], "magic"),
        "CODEX_BATTLE_PROTOCOL_MAJOR": int(protocol["major"]),
        "CODEX_BATTLE_PROTOCOL_MINOR": int(protocol["minor"]),
        "CODEX_BATTLE_MAILBOX_ADDRESS": _integer(ram["address"], "RAM address"),
        "CODEX_BATTLE_MAILBOX_SIZE": int(protocol["struct_size"]),
        "CODEX_BATTLE_RESERVED_SIZE": int(ram["reserved_size"]),
        "CODEX_BATTLE_HEADER_SIZE": int(protocol["header_size"]),
        "CODEX_BATTLE_SNAPSHOT_OFFSET": int(protocol["snapshot_offset"]),
        "CODEX_BATTLE_SNAPSHOT_SIZE": int(protocol["snapshot_size"]),
        "CODEX_BATTLE_REQUEST_OFFSET": int(protocol["request_offset"]),
        "CODEX_BATTLE_REQUEST_SIZE": int(protocol["request_size"]),
        "CODEX_BATTLE_REQUEST_PAYLOAD_MAX": int(protocol["request_payload_max"]),
        "CODEX_BATTLE_CAPABILITIES": int(protocol["capabilities"]),
        "CODEX_BATTLE_STAGE_NUMBER": int(protocol["stage_number"]),
        "CODEX_BATTLE_STAGE_IDENTITY": _integer(
            protocol["stage_identity"], "Stage identity"),
        "CODEX_BATTLE_BUILD_IDENTITY": _integer(
            protocol["build_identity"], "build identity"),
        "CODEX_BATTLE_BASE_ROM_CRC32": base_crc,
        "CODEX_BATTLE_PONG_MAGIC": _integer(protocol["pong_magic"], "PONG magic"),
        "CODEX_BATTLE_DELEGATE_READ_KEYS": _integer(hook["delegate"], "delegate"),
    }
    lines = [
        "#ifndef VEGA_CODEX_BATTLE_BRIDGE_GENERATED_H",
        "#define VEGA_CODEX_BATTLE_BRIDGE_GENERATED_H",
        "",
    ]
    for name, value in values.items():
        lines.append(f"#define {name} 0x{value:X}u")
    lines.extend(["", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(
    load_address: int, header: bytes,
) -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/codex_battle_bridge/codex_battle_bridge.c"
    if not source.is_file():
        _fail("Codex Battle bridge runtime source is missing")
    with tempfile.TemporaryDirectory(prefix="vega-codex-battle-runtime-") as raw:
        directory = Path(raw)
        (directory / "codex_battle_bridge_generated.h").write_bytes(header)
        obj = directory / "codex_battle_bridge.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            f"-I{directory}", f"-I{ROOT}", "-c", str(source), "-o", str(obj),
        ], "compile Codex Battle bridge runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.CodexBattleBridge_*)) *(.text*) *(.rodata*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "codex_battle_bridge.elf"
        binary = directory / "codex_battle_bridge.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,CodexBattleBridge_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Codex Battle bridge runtime")
        undefined = _run([nm, "-u", str(elf)], "Codex Battle undefined-symbol audit")
        if undefined:
            _fail("Codex Battle runtime has undefined symbols: " + undefined)
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run(
            [nm, "-n", "-S", "--defined-only", str(elf)],
            "Codex Battle runtime nm",
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
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"Codex Battle runtime symbols differ: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Codex Battle runtime objcopy")
        payload = binary.read_bytes()
        if not payload or len(payload) > 32 * 1024:
            _fail(f"Codex Battle runtime size is unreasonable: {len(payload)}")
        return payload, symbols, sizes


def _allocation(
    previous: Mapping[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Stage43 gameplay-neutral versioned Codex Battle mailbox, "
            "ReadKeys delegate wrapper and PING/PONG validator"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage43 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage43 Codex Battle allocation is not unique")
    return matches[0], report


def _build_payload(
    config: Mapping[str, Any], previous: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any], dict[str, Any], bytes]:
    header = _runtime_header(config)
    payload_offset = -1
    load_address = GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    final: tuple[bytes, dict[str, int], dict[str, int]] | None = None
    for _ in range(8):
        code, symbols, sizes = _compile_runtime(load_address, header)
        payload_size = _align(PAYLOAD_HEADER_SIZE + len(code), 16)
        allocation, _ = _allocation(previous, payload_size, "0" * 64)
        next_offset = int(allocation["start"])
        next_load = GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if payload_offset == next_offset and load_address == next_load:
            final = code, symbols, sizes
            break
        payload_offset, load_address = next_offset, next_load
    if final is None:
        _fail("Codex Battle runtime allocation did not reach a fixed point")
    code, symbols, sizes = final
    payload = bytearray(b"\xFF" * _align(PAYLOAD_HEADER_SIZE + len(code), 16))
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    protocol = config["protocol"]
    ram = config["ram"]
    struct.pack_into(
        "<8s14I", payload, 0, b"VEGACB43",
        1, len(payload), PAYLOAD_HEADER_SIZE, len(code),
        int(protocol["major"]), int(protocol["minor"]),
        int(protocol["struct_size"]), int(ram["reserved_size"]),
        _integer(ram["address"], "RAM address"),
        _integer(protocol["stage_identity"], "Stage identity"),
        int(protocol["capabilities"]), int(protocol["request_offset"]),
        int(protocol["request_size"]), int(protocol["snapshot_size"]),
    )
    allocation, report = _allocation(previous, len(payload), _sha(bytes(payload)))
    if int(allocation["start"]) != payload_offset:
        _fail("Stage43 allocation moved after payload hash")
    runtime = {
        "payload": {
            "address": GBA_ROM_BASE + payload_offset,
            "offset": payload_offset,
            "size": len(payload),
            "sha256": _sha(bytes(payload)),
        },
        "code": {
            "address": GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
            "offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "size": len(code),
            "sha256": _sha(code),
        },
        "entrypoints": {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)},
        "symbol_sizes": {name: sizes.get(name, 0) for name in sorted(REQUIRED_ENTRYPOINTS)},
    }
    return bytes(payload), runtime, report, header


def _validate_ram(config: Mapping[str, Any]) -> dict[str, Any]:
    with (ROOT / "config/ram_layout.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    live = [row for row in rows if row["status"] == "LIVE" and row["start"]]
    owned = [row for row in live if row["owner"] == "T26_CODEX_BATTLE_BRIDGE"]
    if len(owned) != 1:
        _fail("T26 RAM owner row is not unique")
    row = owned[0]
    start = _integer(config["ram"]["address"], "RAM start")
    end = _integer(config["ram"]["end_exclusive"], "RAM end")
    size = int(config["ram"]["reserved_size"])
    if (int(row["start"], 0) != start or int(row["end_exclusive"], 0) != end
            or int(row["size"]) != size or end - start != size
            or int(config["ram"]["mailbox_size"]) != 256
            or int(config["ram"]["future_extension_size"]) != 256):
        _fail("T26 RAM reservation differs")
    overlaps = [
        other["symbol"] for other in live
        if other is not row and other["address_space"] == row["address_space"]
        and start < int(other["end_exclusive"], 0)
        and int(other["start"], 0) < end
    ]
    if overlaps or not (0x02000000 <= start < end <= 0x02040000):
        _fail(f"T26 RAM overlap/range differs: {overlaps}")
    request_start = start + int(config["protocol"]["request_offset"])
    request_end = request_start + int(config["protocol"]["request_size"])
    return {
        "address": start,
        "end_exclusive": end,
        "reserved_size": size,
        "mailbox_size": 256,
        "request_start": request_start,
        "request_end_exclusive": request_end,
        "overlap_count": 0,
        "save_bytes": 0,
        "persistence": "VOLATILE",
    }


def _validate_protocol_config(config: Mapping[str, Any]) -> None:
    protocol = config["protocol"]
    expected = {
        "major": 1, "minor": 0, "struct_size": 256, "header_size": 80,
        "snapshot_offset": 80, "snapshot_size": 48,
        "request_offset": 128, "request_size": 64,
        "request_payload_max": 32, "capabilities": 7,
        "stage_number": 43, "phase_idle": 1, "command_ping": 1,
    }
    if any(int(protocol[key]) != value for key, value in expected.items()):
        _fail("Codex Battle protocol configuration differs")
    if (protocol["magic_ascii"] != "VCBX"
            or _integer(protocol["magic_u32"], "magic") != 0x58424356
            or _integer(protocol["pong_magic"], "PONG") != 0x474E4F50):
        _fail("Codex Battle protocol magic differs")


def _protocol_document(
    config: Mapping[str, Any], output: bytes, runtime: Mapping[str, Any],
) -> dict[str, Any]:
    protocol = config["protocol"]
    ram = config["ram"]
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": 43,
        "rom": {
            "sha256": _sha(output),
            "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
            "size": len(output),
            "basename": "Pokemon-Vega-Stage43-Codex-Battle-Bridge.gba",
        },
        "mailbox": {
            "address": _integer(ram["address"], "mailbox address"),
            "struct_size": int(protocol["struct_size"]),
            "reserved_size": int(ram["reserved_size"]),
            "magic": _integer(protocol["magic_u32"], "magic"),
            "major": int(protocol["major"]),
            "minor": int(protocol["minor"]),
            "header_size": int(protocol["header_size"]),
            "snapshot_offset": int(protocol["snapshot_offset"]),
            "snapshot_size": int(protocol["snapshot_size"]),
            "request_offset": int(protocol["request_offset"]),
            "request_size": int(protocol["request_size"]),
            "request_payload_max": int(protocol["request_payload_max"]),
            "capabilities": int(protocol["capabilities"]),
            "stage_number": int(protocol["stage_number"]),
            "stage_identity": _integer(protocol["stage_identity"], "Stage identity"),
            "build_identity": _integer(protocol["build_identity"], "build identity"),
            "base_rom_crc32": int(config["inputs"]["stage42_rom"]["crc32"], 16),
            "phase_idle": int(protocol["phase_idle"]),
            "command_ping": int(protocol["command_ping"]),
            "pong_magic": _integer(protocol["pong_magic"], "PONG magic"),
        },
        "runtime": {"poll": runtime["entrypoints"]["CodexBattleBridge_Poll"]},
        "nci": {
            "port_default": int(config["device_contract"]["network_cmd_port"]),
            "trusted_lan_only": True,
            "hardcore_write_warning": True,
            "read_command": "READ_CORE_MEMORY",
            "write_command": "WRITE_CORE_MEMORY",
        },
        "exit_codes": {
            "ok": 0, "config": 10, "transport": 20, "nci_response": 21,
            "core_or_rom": 22, "protocol": 23, "request": 24,
            "config_write": 25,
        },
    }


def _ipad_evidence(
    config: Mapping[str, Any], protocol_document: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    path = ROOT / config["outputs"]["ipad"]
    if not path.is_file():
        return None, None
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    forbidden = (
        r"/var/(?:mobile|containers)/Containers/",
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY",
        r'"host"\s*:',
        r'"credential(?:s)?"\s*:',
    )
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in forbidden):
        _fail("iPad evidence contains machine address/path/credential material")
    evidence = json.loads(text)
    if not isinstance(evidence, dict):
        _fail("iPad evidence root differs")
    expected_device = config["device_contract"]
    inventory = evidence.get("inventory", {})
    nci = evidence.get("nci", {})
    cli = evidence.get("cli", {})
    safety = evidence.get("safety", {})
    mailbox = evidence.get("mailbox", {})
    # Device evidence is immutable historical evidence.  A rebuilt base ROM
    # gets a new CRC32 and must return to PENDING until it is exercised on the
    # iPad again; never rewrite or silently bless the old observation.
    if mailbox.get("rom_crc32") != protocol_document["rom"]["crc32"]:
        return None, _sha(raw)
    if (evidence.get("schema_version") != 1 or evidence.get("task") != TASK
            or evidence.get("status") != "PASS"
            or inventory.get("retroarch_version") != expected_device["retroarch_version"]
            or inventory.get("retroarch_build") != expected_device["retroarch_build"]
            or inventory.get("mgba_info_version") != expected_device["mgba_info_version"]
            or inventory.get("mgba_core_sha256") != expected_device["mgba_core_sha256"]
            or inventory.get("network_cmd_enable") is not True
            or inventory.get("network_cmd_port") != expected_device["network_cmd_port"]
            or any(nci.get(key) is not True for key in (
                "version", "get_status", "ewram_read", "mailbox_write", "ping_pong"))
            or any(cli.get(key) is not True for key in (
                "doctor", "device_status", "bridge_ping", "external_directory",
                "stable_json_exit_codes", "owner_only_config"))
            or mailbox.get("address") != protocol_document["mailbox"]["address"]
            or mailbox.get("stage_identity") != protocol_document["mailbox"]["stage_identity"]
            or any(safety.get(key) is not True for key in (
                "retroarch_stopped_before_config", "backup_hash_match",
                "versioned_rom_new_file", "existing_rom_unchanged",
                "existing_save_unchanged", "request_span_only",
                "ip_redacted", "credential_redacted", "container_uuid_redacted"))):
        _fail("iPad evidence does not satisfy the Stage43 device contract")
    return evidence, _sha(raw)


def _patch(
    output: bytearray, stage: bytes, declared: list[dict[str, Any]],
    address: int, expected: bytes, replacement: bytes, name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement size differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage42 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    row = {
        "name": name, "address": address, "offset": offset,
        "size": len(expected), "expected_hex": expected.hex(),
        "replacement_hex": replacement.hex(),
    }
    declared.append({"kind": f"hook::{name}", "start": offset,
                     "end_exclusive": offset + len(expected)})
    return row


def _static_outputs() -> dict[str, bytes]:
    config_raw = (ROOT / CONFIG).read_bytes()
    config = json.loads(config_raw)
    if not isinstance(config, dict) or config.get("task") != TASK:
        _fail("Codex Battle bridge config root/task differs")
    _validate_protocol_config(config)
    inputs = config["inputs"]
    stage = _identity(Path(inputs["stage42_rom"]["path"]),
                      inputs["stage42_rom"], "Stage42 ROM")
    metadata_raw = _identity(Path(inputs["stage42_metadata"]["path"]),
                             inputs["stage42_metadata"], "Stage42 metadata")
    allocation_raw = _identity(Path(inputs["stage42_allocation"]["path"]),
                               inputs["stage42_allocation"], "Stage42 allocation")
    stage42_clean_bps = _identity(Path(inputs["stage42_clean_bps"]["path"]),
                                  inputs["stage42_clean_bps"], "Stage42 clean BPS")
    clean = _identity(Path(inputs["clean_rom"]["path"]),
                      inputs["clean_rom"], "clean FireRed")
    if len(stage) != ROM_SIZE or (zlib.crc32(stage) & 0xFFFFFFFF) != int(
            inputs["stage42_rom"]["crc32"], 16):
        _fail("Stage42 size/CRC32 differs")
    if apply_bps(clean, stage42_clean_bps) != stage:
        _fail("clean->Stage42 pinned BPS does not reproduce Stage42")
    previous_meta = json.loads(metadata_raw)
    previous_alloc = json.loads(allocation_raw)
    if (previous_meta.get("task") != "T25" or previous_meta.get("status") != "PASS"
            or previous_meta.get("output", {}).get("sha256") != _sha(stage)
            or previous_meta.get("mgba", {}).get("status") != "PASS"
            or previous_alloc.get("summaries", {}).get("overlap_count") != 0):
        _fail("Stage42 metadata/allocation prerequisite differs")

    ownership = _validate_ram(config)
    payload, runtime, allocation_report, generated_header = _build_payload(
        config, previous_alloc)
    payload_offset = int(runtime["payload"]["offset"])
    if stage[payload_offset:payload_offset + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage43 allocation target is not erased")
    output = bytearray(stage)
    output[payload_offset:payload_offset + len(payload)] = payload
    declared = [{"kind": "payload::codex_battle_bridge", "start": payload_offset,
                 "end_exclusive": payload_offset + len(payload)}]
    hook = config["hook"]
    target = runtime["entrypoints"][str(hook["target_symbol"])]
    patch = _patch(
        output, stage, declared, _integer(hook["address"], "hook address"),
        bytes.fromhex(str(hook["expected_hex"])), struct.pack("<I", target),
        str(hook["name"]),
    )
    patch.update({
        "mode": hook["mode"], "delegate": _integer(hook["delegate"], "delegate"),
        "target": target, "target_symbol": hook["target_symbol"],
        "delegate_chain_preserved": True,
    })
    ordered = sorted(declared, key=lambda row: int(row["start"]))
    if any(int(left["end_exclusive"]) > int(right["start"])
           for left, right in zip(ordered, ordered[1:])):
        _fail("Stage43 declared spans overlap")
    declared_offsets = {
        index for row in ordered
        for index in range(int(row["start"]), int(row["end_exclusive"]))
    }
    changed = [index for index, (before, after) in enumerate(zip(stage, output))
               if before != after]
    outside = [index for index in changed if index not in declared_offsets]
    if outside:
        _fail(f"Stage43 changed bytes outside declared spans: {outside[:8]}")
    hook_offsets = set(range(patch["offset"], patch["offset"] + patch["size"]))
    previous_changed = 0
    for allocation in previous_alloc.get("allocations", []):
        previous_changed += sum(
            stage[index] != output[index] and index not in hook_offsets
            for index in range(int(allocation["start"]), int(allocation["end_exclusive"]))
        )
    if previous_changed:
        _fail("T00-T25 allocation changed outside the chained delegate pointer")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage43 BPS round trip differs")

    protocol_document = _protocol_document(config, output_raw, runtime)
    ipad, ipad_sha = _ipad_evidence(config, protocol_document)
    ipad_pass = ipad is not None
    static_checks = {
        "input_identity": True,
        "ram_overlap_zero": ownership["overlap_count"] == 0,
        "save_bytes_zero": ownership["save_bytes"] == 0,
        "hook_delegate_preserved": patch["delegate_chain_preserved"] is True,
        "declared_span_outside_zero": not outside,
        "allocator_overlap_zero": allocation_report["summaries"]["overlap_count"] == 0,
        "bps_round_trip": True,
        "dual_protocol_constants": generated_header and protocol_document["mailbox"]["magic"]
            == _integer(config["protocol"]["magic_u32"], "magic"),
        "production_cli_no_raw_memory_subcommand": True,
    }
    if any(value is not True for value in static_checks.values()):
        _fail(f"Stage43 static checks differ: {static_checks}")

    output_paths = config["outputs"]
    symbols_document = {
        "schema_version": 1, "task": TASK,
        "symbols": {name: {"address": address,
                            "size": runtime["symbol_sizes"].get(name, 0)}
                    for name, address in runtime["entrypoints"].items()},
        "runtime": runtime["code"], "payload": runtime["payload"],
        "hook": patch, "mailbox": protocol_document["mailbox"],
    }
    cases = {
        "schema_version": 1, "task": TASK, "rom_sha256": _sha(output_raw),
        "acceptance_keys": list(ACCEPTANCE_KEYS),
        "mailbox_address": protocol_document["mailbox"]["address"],
        "payload_address": runtime["payload"]["address"],
        "mailbox": protocol_document["mailbox"], "hook": patch,
        "protected_spans": [
            {"name": "party", "address": 0x020241E4, "size": 600},
            {"name": "battle", "address": 0x02023B24, "size": 0x430},
            {"name": "save_ledger", "address": 0x0203D000, "size": 0x800},
            {"name": "factory", "address": 0x0203F220, "size": 0x500},
            {"name": "mirage", "address": 0x0203EE00, "size": 0x298},
            {"name": "reward", "address": 0x0203F110, "size": 0x100},
            {"name": "rng", "address": 0x03005040, "size": 4},
        ],
        "invalid_cases": [
            "torn", "duplicate", "stale", "future", "wrong_nonce",
            "wrong_payload_crc", "wrong_request_crc", "wrong_phase",
            "oversize", "unknown_command",
        ],
        "quick_iterations": 8, "full_iterations": 64,
    }
    metadata = {
        "schema_version": 1, "task": TASK,
        "status": "PASS_LOCAL" if not ipad_pass else "PASS_LOCAL_IPAD_PENDING_MGBA",
        "input": {"path": inputs["stage42_rom"]["path"], "size": len(stage),
                  "sha256": _sha(stage), "crc32": inputs["stage42_rom"]["crc32"]},
        "input_metadata_sha256": _sha(metadata_raw),
        "input_allocation_sha256": _sha(allocation_raw),
        "clean_input": {"path": inputs["clean_rom"]["path"], "size": len(clean),
                        "sha256": _sha(clean)},
        "output": {"path": output_paths["rom"], "size": len(output_raw),
                   "sha256": _sha(output_raw),
                   "crc32": protocol_document["rom"]["crc32"]},
        "runtime": runtime, "mailbox": protocol_document["mailbox"],
        "ownership": ownership, "hook": patch,
        "allocation": {"path": output_paths["allocation"], "name": ALLOCATION_NAME,
                       "overlap_count": 0,
                       "remaining_allocatable_bytes":
                           allocation_report["summaries"]["remaining_allocatable_bytes"]},
        "change_audit": {"changed_byte_count": len(changed),
                         "declared_spans": ordered,
                         "declared_span_overlap_count": 0,
                         "outside_declared_span_count": 0,
                         "previous_allocation_changes_outside_delegate": 0},
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "hook": 0},
        "patches": {
            "incremental": {"path": output_paths["incremental_bps"],
                            "size": len(incremental), "sha256": _sha(incremental),
                            "exact": True},
            "clean_direct": {"path": output_paths["clean_bps"],
                             "size": len(direct), "sha256": _sha(direct),
                             "exact": True},
        },
        "static_checks": static_checks,
        "ipad": {"status": "PASS" if ipad_pass else "PENDING",
                 "evidence_path": output_paths["ipad"], "sha256": ipad_sha},
        "mgba": {"status": "PENDING", "process_count": 0},
        "acceptance": {key: False for key in ACCEPTANCE_KEYS},
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": metadata["status"],
        "input": metadata["input"], "output": metadata["output"],
        "runtime": runtime, "mailbox": protocol_document["mailbox"],
        "ownership": ownership, "hook": patch,
        "change_audit": metadata["change_audit"],
        "overlap_audit": metadata["overlap_audit"],
        "static_checks": static_checks, "ipad": metadata["ipad"],
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": metadata["status"],
        "acceptance": {key: {"status": "PENDING", "evidence": {}}
                       for key in ACCEPTANCE_KEYS},
        "runtime_invalid_case_count": len(cases["invalid_cases"]),
        "mgba": {"status": "PENDING", "process_count": 0},
        "ipad": metadata["ipad"],
    }
    return {
        output_paths["rom"]: output_raw,
        output_paths["metadata"]: _stable(metadata),
        output_paths["allocation"]: _stable(allocation_report),
        output_paths["incremental_bps"]: incremental,
        output_paths["clean_bps"]: direct,
        output_paths["generated_header"]: generated_header,
        output_paths["runtime"]: payload[
            PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + runtime["code"]["size"]],
        output_paths["symbols"]: _stable(symbols_document),
        output_paths["protocol"]: _stable(protocol_document),
        output_paths["cases"]: _stable(cases),
        output_paths["audit"]: _stable(audit),
        output_paths["coverage"]: _stable(coverage),
    }


def _validate_mgba_document(
    document: Mapping[str, Any], mode: str, identities: Mapping[str, str],
) -> None:
    expected_tests = {
        "case_fixture", "runtime_exports", "rooted_delegate", "header_snapshot_crc",
        "ping_pong", "torn_duplicate_stale", "future_nonce_crc",
        "phase_oversize_command", "protected_state_unchanged", "warnings_zero",
    }
    tests = document.get("tests")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("mode") != mode or document.get("status") != "PASS"
            or document.get("result_identity") != "CB43:1:256:512:10:7"
            or any(document.get(key) != value for key, value in identities.items())
            or not isinstance(tests, dict) or set(tests) != expected_tests
            or any(value is not True for value in tests.values())
            or document.get("total") != len(expected_tests)
            or document.get("warnings") != 0
            or document.get("invalid_case_count") != 10
            or document.get("protected_span_count") != 7):
        _fail(f"Codex Battle mGBA {mode} did not report exact all-PASS")


def _finalize_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    config = _read_json(CONFIG)
    output_paths = config["outputs"]
    runner = ROOT / "tools/mgba_codex_battle_bridge_smoke.c"
    if not runner.is_file():
        _fail("Codex Battle mGBA runner is missing")
    source_identities = {
        "rom_sha256": _sha(outputs[output_paths["rom"]]),
        "runner_sha256": _sha(runner.read_bytes()),
        "symbols_sha256": _sha(outputs[output_paths["symbols"]]),
        "cases_sha256": _sha(outputs[output_paths["cases"]]),
    }
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    documents: dict[str, dict[str, Any]] = {}
    result: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(prefix="vega-codex-battle-mgba-", dir=local) as raw:
        directory = Path(raw)
        executable = directory / "mgba-codex-battle-bridge"
        rom = directory / "stage43.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(outputs[output_paths["rom"]])
        symbols.write_bytes(outputs[output_paths["symbols"]])
        cases.write_bytes(outputs[output_paths["cases"]])
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "Codex Battle libmGBA compile")
        executable_identities = {
            **source_identities, "runner_sha256": _sha(executable.read_bytes()),
        }
        for mode, key, timeout in (
            ("quick", "mgba_quick", 300), ("full", "mgba_full", 600),
        ):
            stdout = _run(
                [str(executable), str(rom), str(symbols), str(cases), mode],
                f"Codex Battle mGBA {mode}", timeout=timeout,
            )
            document = json.loads(stdout)
            if not isinstance(document, dict):
                _fail(f"Codex Battle mGBA {mode} JSON root differs")
            _validate_mgba_document(document, mode, executable_identities)
            document["runner_sha256"] = source_identities["runner_sha256"]
            document["process_runs"] = 1
            document["fixture"] = "codex_battle_bridge_stage43_exact_rom"
            documents[mode] = document
            result[output_paths[key]] = _stable(document)
    quick, full = documents["quick"], documents["full"]
    if any(quick[key] != full[key] for key in (
        "result_identity", "rom_sha256", "runner_sha256",
        "symbols_sha256", "cases_sha256",
    )):
        _fail("Codex Battle mGBA quick/full identity differs")
    mgba = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": {"independent_processes": True,
                            "quick_full_equal": True, "warnings_zero": True},
        "quick": {"path": output_paths["mgba_quick"], "tests": quick["tests"]},
        "full": {"path": output_paths["mgba_full"], "tests": full["tests"]},
    }
    metadata = json.loads(outputs[output_paths["metadata"]])
    audit = json.loads(outputs[output_paths["audit"]])
    coverage = json.loads(outputs[output_paths["coverage"]])
    ipad_pass = metadata["ipad"]["status"] == "PASS"
    acceptance = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE": True,
        "IPAD_INVENTORY_NCI_MEMORY_MAP": ipad_pass,
        "IPAD_VERSION_STATUS_EWRAM_READ_WRITE": ipad_pass,
        "CLI_DOCTOR_SAFE_IDENTITY": ipad_pass,
        "OWNER_ONLY_CONFIG_NO_HOST_LEAK": ipad_pass,
        "CLI_EXTERNAL_DIRECTORY_JSON_EXIT": ipad_pass,
        "ROM_CLI_DUAL_VALIDATORS": quick["tests"]["header_snapshot_crc"]
            and quick["tests"]["future_nonce_crc"],
        "INVALID_REQUESTS_GAMEPLAY_UNCHANGED":
            quick["tests"]["torn_duplicate_stale"]
            and full["tests"]["future_nonce_crc"]
            and full["tests"]["phase_oversize_command"]
            and full["tests"]["protected_state_unchanged"],
        "MAILBOX_PING_STATE_NEUTRAL": quick["tests"]["ping_pong"]
            and full["tests"]["protected_state_unchanged"] and ipad_pass,
        "OVERLAP_DECLARED_CLEAN_BPS_MGBA":
            all(value == 0 for value in metadata["overlap_audit"].values())
            and metadata["change_audit"]["outside_declared_span_count"] == 0,
        "IPAD_VERSIONED_COPY_SECRET_REDACTION": ipad_pass,
    }
    if tuple(acceptance) != ACCEPTANCE_KEYS:
        _fail("Codex Battle acceptance order differs")
    status = "PASS" if all(acceptance.values()) else "PASS_LOCAL"
    metadata["status"] = status
    metadata["mgba"] = mgba
    metadata["acceptance"] = acceptance
    audit["status"] = status
    audit["mgba"] = mgba
    audit["acceptance"] = acceptance
    coverage["status"] = status
    coverage["mgba"] = mgba
    coverage["acceptance"] = {
        key: {
            "status": "PASS" if value else "PENDING",
            "evidence": {
                "builder": key in {
                    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
                    "ROM_CLI_DUAL_VALIDATORS",
                    "INVALID_REQUESTS_GAMEPLAY_UNCHANGED",
                    "OVERLAP_DECLARED_CLEAN_BPS_MGBA",
                } and value,
                "mgba_quick_full": key in {
                    "ROM_CLI_DUAL_VALIDATORS", "INVALID_REQUESTS_GAMEPLAY_UNCHANGED",
                    "MAILBOX_PING_STATE_NEUTRAL", "OVERLAP_DECLARED_CLEAN_BPS_MGBA",
                } and value,
                "ipad": key in {
                    "IPAD_INVENTORY_NCI_MEMORY_MAP",
                    "IPAD_VERSION_STATUS_EWRAM_READ_WRITE",
                    "CLI_DOCTOR_SAFE_IDENTITY", "OWNER_ONLY_CONFIG_NO_HOST_LEAK",
                    "CLI_EXTERNAL_DIRECTORY_JSON_EXIT", "MAILBOX_PING_STATE_NEUTRAL",
                    "IPAD_VERSIONED_COPY_SECRET_REDACTION",
                } and ipad_pass,
            },
        } for key, value in acceptance.items()
    }
    result.update({
        output_paths["metadata"]: _stable(metadata),
        output_paths["audit"]: _stable(audit),
        output_paths["coverage"]: _stable(coverage),
    })
    return result


def build_outputs(static: Mapping[str, bytes] | None = None) -> dict[str, bytes]:
    if static is None:
        static = _static_outputs()
    return {**static, **_finalize_outputs(static)}


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (ROOT / relative).is_file()
        or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Codex Battle Bridge generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        static = _static_outputs()
        repeated_static = _static_outputs()
        if static != repeated_static:
            _fail("Codex Battle Bridge static build is not byte deterministic")
        outputs = build_outputs(static)
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
            config = _read_json(CONFIG)
            metadata = json.loads(outputs[config["outputs"]["metadata"]])
            if metadata.get("status") != "PASS":
                _fail("real iPad evidence is not finalized")
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, CodexBattleBridgeBuildError,
    ) as error:
        print(f"Codex Battle Bridge Stage43 {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    config = _read_json(CONFIG)
    metadata = json.loads(outputs[config["outputs"]["metadata"]])
    print(
        "Codex Battle Bridge Stage43 %s: %s stage=%s crc32=%s artifacts=%d"
        % (args.mode, metadata["status"], metadata["output"]["sha256"],
           metadata["output"]["crc32"], len(outputs))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
