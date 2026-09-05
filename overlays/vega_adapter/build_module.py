#!/usr/bin/python3
"""Build the deterministic T03 no-op Vega adapter with pinned ARM tools."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
ROM_BASE = 0x08000000
AUDITED_CFRU_END = 0x09185F88
INTEGRATION_START = 0x09200000
INTEGRATION_END = 0x09600000
DEFAULT_ROM_ORIGIN = 0x09200000
MARKER = b"PVADAPTER_V1\0\0\0\0"
ABI_VERSION = 1
HEADER_SIZE = 32
EXPECTED_TEXT_SIZE = 2
TOOL_KEYS = (
    "python",
    "arm_none_eabi_as",
    "arm_none_eabi_ld",
    "arm_none_eabi_objcopy",
    "arm_none_eabi_nm",
)
ARTIFACT_NAMES = (
    "vega_adapter.bin",
    "vega_adapter.elf",
    "vega_adapter.map",
)
SYMBOL_NAMES = frozenset(
    {
        "__vega_adapter_start",
        "__vega_adapter_header_end",
        "__vega_adapter_text_start",
        "__vega_adapter_text_end",
        "__vega_adapter_end",
        "__vega_adapter_size",
        "__vega_adapter_hook_count",
        "gVegaAdapterModuleHeader",
        "vega_adapter_entry",
    }
)


class AdapterBuildError(RuntimeError):
    """The build input, toolchain, or produced module violated its contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdapterBuildError(f"cannot read {label}: {path}") from error
    if not isinstance(value, Mapping):
        raise AdapterBuildError(f"{label} must be a JSON object")
    return value


def _parse_origin(value: str) -> int:
    try:
        origin = int(value, 0)
    except ValueError as error:
        raise AdapterBuildError(f"ROM_ORIGIN is not an integer: {value!r}") from error
    if origin < INTEGRATION_START or origin >= INTEGRATION_END:
        raise AdapterBuildError(
            "ROM_ORIGIN must be inside integration_modules "
            f"[{INTEGRATION_START:#010x}, {INTEGRATION_END:#010x})"
        )
    if origin & 3:
        raise AdapterBuildError("ROM_ORIGIN must be 4-byte aligned")
    return origin


def _tool_environment() -> dict[str, str]:
    return {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "SOURCE_DATE_EPOCH": "0",
        "TZ": "UTC",
    }


def _run(command: Sequence[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=_tool_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    output = completed.stdout.decode("utf-8", "replace")
    if completed.returncode:
        raise AdapterBuildError(
            f"command failed ({completed.returncode}): {command[0]}\n{output[-2000:]}"
        )
    return output


def _verify_toolchain(manifest_path: Path) -> dict[str, dict[str, str]]:
    manifest = _load_object(manifest_path, "toolchain manifest")
    schema = manifest.get("schema_version")
    if isinstance(schema, bool) or schema != SCHEMA_VERSION:
        raise AdapterBuildError("toolchain manifest schema_version must be integer 1")
    tools = manifest.get("tools")
    if not isinstance(tools, Mapping):
        raise AdapterBuildError("toolchain manifest tools must be an object")

    identities: dict[str, dict[str, str]] = {}
    for key in TOOL_KEYS:
        raw = tools.get(key)
        if not isinstance(raw, Mapping):
            raise AdapterBuildError(f"toolchain manifest is missing {key}")
        path = Path(str(raw.get("path", "")))
        digest = str(raw.get("sha256", ""))
        version = str(raw.get("version", ""))
        version_contains = str(raw.get("version_contains", ""))
        version_command = raw.get("version_command")
        if (
            not path.is_absolute()
            or not path.is_file()
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not version
            or not version_contains
            or not isinstance(version_command, list)
            or not version_command
            or str(version_command[0]) != str(path)
            or not all(isinstance(item, str) and item for item in version_command)
        ):
            raise AdapterBuildError(f"invalid pinned tool contract: {key}")
        observed_digest = _sha256_file(path)
        if key == "python" and raw.get("identity_policy") == "UBUNTU_CPYTHON_PACKAGE_ABI_V1":
            # This script is launched by the module Makefile with an isolated PATH.
            root = Path(__file__).resolve().parents[2]
            sys.path.insert(0, str(root))
            from scripts.portable_python_identity import PythonIdentityError, verify
            try:
                identities[key] = verify(path, digest, version)
            except PythonIdentityError as error:
                raise AdapterBuildError(str(error)) from error
            if Path(sys.executable).resolve() != path.resolve():
                raise AdapterBuildError("builder must run with the pinned /usr/bin/python3")
            continue
        if observed_digest != digest:
            raise AdapterBuildError(
                f"pinned tool SHA-256 mismatch for {key}: {observed_digest}"
            )
        output = _run(version_command, cwd=manifest_path.parent)
        if version_contains not in output:
            raise AdapterBuildError(f"pinned tool version mismatch for {key}")
        if key == "python" and Path(sys.executable).resolve() != path.resolve():
            raise AdapterBuildError("builder must run with the pinned /usr/bin/python3")
        identities[key] = {
            "path": str(path),
            "version": version,
            "sha256": digest,
        }
    return identities


def _parse_symbols(nm_output: str) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in nm_output.splitlines():
        match = re.fullmatch(r"([0-9A-Fa-f]+)\s+\S\s+(\S+)", line.strip())
        if not match or match.group(2) not in SYMBOL_NAMES:
            continue
        name = match.group(2)
        if name in symbols:
            raise AdapterBuildError(f"duplicate ELF symbol: {name}")
        symbols[name] = int(match.group(1), 16)
    missing = sorted(SYMBOL_NAMES - set(symbols))
    if missing:
        raise AdapterBuildError(f"ELF is missing required symbols: {missing}")
    return symbols


def _artifact(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
        raise AdapterBuildError(f"missing/invalid build artifact: {path.name}")
    return {
        "path": path.name,
        "size": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _section(
    name: str, start: int, end: int, origin: int, binary: bytes
) -> dict[str, Any]:
    if start < origin or end <= start or end - origin > len(binary):
        raise AdapterBuildError(f"invalid output section: {name}")
    content = binary[start - origin : end - origin]
    return {
        "name": name,
        "start": f"0x{start:08X}",
        "end_exclusive": f"0x{end:08X}",
        "size": len(content),
        "sha256": _sha256_bytes(content),
    }


def _build_metadata(
    *,
    origin: int,
    source: Path,
    linker: Path,
    builder: Path,
    makefile: Path,
    build_dir: Path,
    tools: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    binary_path = build_dir / "vega_adapter.bin"
    elf_path = build_dir / "vega_adapter.elf"
    map_path = build_dir / "vega_adapter.map"
    binary = binary_path.read_bytes()
    nm = Path(tools["arm_none_eabi_nm"]["path"])
    symbols = _parse_symbols(
        _run([str(nm), "-n", "--defined-only", elf_path.name], cwd=build_dir)
    )

    start = symbols["__vega_adapter_start"]
    header_end = symbols["__vega_adapter_header_end"]
    text_start = symbols["__vega_adapter_text_start"]
    text_end = symbols["__vega_adapter_text_end"]
    end = symbols["__vega_adapter_end"]
    # GNU nm displays the code address with the ELF Thumb bit normalized away.
    # The external ABI and embedded function pointer explicitly include it.
    code_entry = symbols["vega_adapter_entry"]
    entry = code_entry | 1
    if start != origin or header_end != text_start or text_end != end:
        raise AdapterBuildError("module sections are not contiguous at ROM_ORIGIN")
    if symbols["__vega_adapter_size"] != end - start or end - start != len(binary):
        raise AdapterBuildError("module size symbol/binary span mismatch")
    if symbols["__vega_adapter_hook_count"] != 0:
        raise AdapterBuildError("T03 adapter unexpectedly declares hooks")
    if code_entry & 1 or entry & 1 != 1 or code_entry != text_start:
        raise AdapterBuildError("entry symbol is not a Thumb address at text start")
    if end > INTEGRATION_END:
        raise AdapterBuildError("module exceeds integration_modules region")
    if len(binary) != HEADER_SIZE + EXPECTED_TEXT_SIZE:
        raise AdapterBuildError("no-op module binary size changed")

    marker = binary[: len(MARKER)]
    if marker != MARKER:
        raise AdapterBuildError("module marker mismatch")
    abi, embedded_size, embedded_entry, hook_count = struct.unpack_from(
        "<IIII", binary, len(MARKER)
    )
    if (
        abi != ABI_VERSION
        or embedded_size != len(binary)
        or embedded_entry != entry
        or hook_count != 0
    ):
        raise AdapterBuildError("embedded module ABI header mismatch")
    if binary[text_start - origin : text_end - origin] != b"\x70\x47":
        raise AdapterBuildError("T03 entry is not the expected Thumb 'bx lr'")

    sections = [
        _section(".vega_adapter.header", start, header_end, origin, binary),
        _section(".vega_adapter.text", text_start, text_end, origin, binary),
    ]
    artifacts = {
        path.name: _artifact(path)
        for path in (binary_path, elf_path, map_path)
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "module": {
            "name": "vega_adapter",
            "purpose": "T03_DETERMINISTIC_NO_OP_HARNESS",
            "abi_version": ABI_VERSION,
            "marker_ascii": "PVADAPTER_V1",
            "marker_hex": MARKER.hex(),
            "entry_symbol": "vega_adapter_entry",
            "entry_isa": "Thumb",
            "entry_address": f"0x{entry:08X}",
            "entry_code_address": f"0x{code_entry:08X}",
            "hook_count": 0,
            "hooks": [],
            "vega_owned_writes": [],
            "side_effects": "NONE_UNREFERENCED_BX_LR",
        },
        "allocation": {
            "section": "vega_adapter_module",
            "rom_origin": f"0x{origin:08X}",
            "rom_end_exclusive": f"0x{end:08X}",
            "rom_offset": f"0x{origin - ROM_BASE:08X}",
            "size": len(binary),
            "allowed_region_start": f"0x{INTEGRATION_START:08X}",
            "allowed_region_end_exclusive": f"0x{INTEGRATION_END:08X}",
            "audited_cfru_payload_end": f"0x{AUDITED_CFRU_END:08X}",
        },
        "allocator_request": {
            "name": "vega_adapter_module",
            "region": "integration_modules",
            "size": len(binary),
            "alignment": 4,
            "start": f"0x{origin - ROM_BASE:08X}",
            "owner": "vega_adapter",
            "purpose": "T03 deterministic no-op harness module",
            "content_sha256": artifacts["vega_adapter.bin"]["sha256"],
        },
        "sections": sections,
        "inputs": {
            "overlays/vega_adapter/module.S": _sha256_file(source),
            "overlays/vega_adapter/linker.ld": _sha256_file(linker),
            "overlays/vega_adapter/build_module.py": _sha256_file(builder),
            "overlays/vega_adapter/Makefile": _sha256_file(makefile),
        },
        "toolchain": {key: dict(tools[key]) for key in TOOL_KEYS},
        "build": {
            "assembler_flags": ["-mcpu=arm7tdmi", "--fatal-warnings"],
            "linker_flags": [
                "--build-id=none",
                "--fatal-warnings",
                "--no-undefined",
                "--gc-sections",
            ],
            "binary_sections": [".vega_adapter.header", ".vega_adapter.text"],
        },
        "artifacts": artifacts,
    }


def build(
    *, manifest_path: Path, out_dir: Path, rom_origin: str
) -> dict[str, Any]:
    origin = _parse_origin(rom_origin)
    module_dir = Path(__file__).resolve().parent
    source = module_dir / "module.S"
    linker = module_dir / "linker.ld"
    builder = module_dir / "build_module.py"
    makefile = module_dir / "Makefile"
    for path in (source, linker, builder, makefile, manifest_path):
        if path.is_symlink() or not path.is_file():
            raise AdapterBuildError(f"build input must be a regular non-symlink file: {path}")
    tools = _verify_toolchain(manifest_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    if out_dir.is_symlink() or not out_dir.is_dir():
        raise AdapterBuildError("OUT_DIR must be a non-symlink directory")
    for name in (*ARTIFACT_NAMES, "metadata.json"):
        destination = out_dir / name
        if destination.is_symlink():
            raise AdapterBuildError(f"refusing to replace symlink artifact: {name}")

    assembler = tools["arm_none_eabi_as"]["path"]
    linker_tool = tools["arm_none_eabi_ld"]["path"]
    objcopy = tools["arm_none_eabi_objcopy"]["path"]
    with tempfile.TemporaryDirectory(prefix=".vega-adapter-build-", dir=out_dir) as raw:
        work = Path(raw)
        _run(
            [
                assembler,
                "-mcpu=arm7tdmi",
                "--fatal-warnings",
                "-o",
                "vega_adapter.o",
                str(source),
            ],
            cwd=work,
        )
        _run(
            [
                linker_tool,
                "--build-id=none",
                "--fatal-warnings",
                "--no-undefined",
                "--gc-sections",
                f"--defsym=__vega_adapter_rom_origin={origin:#x}",
                "-T",
                str(linker),
                "-Map=vega_adapter.map",
                "-o",
                "vega_adapter.elf",
                "vega_adapter.o",
            ],
            cwd=work,
        )
        _run(
            [
                objcopy,
                "-O",
                "binary",
                "--only-section=.vega_adapter.header",
                "--only-section=.vega_adapter.text",
                "vega_adapter.elf",
                "vega_adapter.bin",
            ],
            cwd=work,
        )
        metadata = _build_metadata(
            origin=origin,
            source=source,
            linker=linker,
            builder=builder,
            makefile=makefile,
            build_dir=work,
            tools=tools,
        )
        for name in ARTIFACT_NAMES:
            (work / name).chmod(0o644)
        metadata_path = work / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        # Publish metadata last so its presence means all sibling artifacts
        # were validated and atomically replaced.
        (out_dir / "metadata.json").unlink(missing_ok=True)
        for name in ARTIFACT_NAMES:
            os.replace(work / name, out_dir / name)
        os.replace(metadata_path, out_dir / "metadata.json")
    return metadata


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--manifest", required=True, type=Path)
    command.add_argument("--out-dir", required=True, type=Path)
    command.add_argument("--rom-origin", default=f"0x{DEFAULT_ROM_ORIGIN:08X}")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        metadata = build(
            manifest_path=args.manifest.resolve(),
            out_dir=Path(os.path.abspath(args.out_dir)),
            rom_origin=args.rom_origin,
        )
    except (AdapterBuildError, OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "module_sha256": metadata["artifacts"]["vega_adapter.bin"][
                    "sha256"
                ],
                "entry_address": metadata["module"]["entry_address"],
                "hook_count": metadata["module"]["hook_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
