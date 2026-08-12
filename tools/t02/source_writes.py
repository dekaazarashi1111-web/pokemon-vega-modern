#!/usr/bin/env python3
"""固定DPE/CFRU source writeを、上流insert.pyと同じ順序で再生する。

このモジュールが公開するモデルにはROM byteそのものを含めない。書込み値と
clean/Vega/Factory観測値は長さとSHA-256だけを記録する。実byteは再生中の
memory内にだけ保持し、最終T01 ROMとの完全一致を必須ゲートにする。
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Iterable, Mapping, Sequence


ROM_BASE = 0x08000000
ROM_SIZE = 0x02000000
REPOINT_SCAN_END = 0x01000000
IGNORED_REPOINT_OFFSETS = {
    "cfru": frozenset({0x35C748, 0x35C774, 0xCABDF0}),
    "dpe": frozenset({0x3986C0, 0x3986EC, 0xDABDF0}),
}
SCHEMA_VERSION = 1
CONTROL_FILES: tuple[tuple[str, str], ...] = (
    ("byte_replacement", "bytereplacement"),
    ("hook", "hooks"),
    ("repoint", "repoints"),
    ("repointall", "repointall"),
    ("routine_pointer", "routinepointers"),
    ("function_rewrite", "functionrewrites"),
)
PROFILE_OVERLAYS = {
    "factory-like": "config/cfru_factory_like.h",
    "minimal": "config/cfru_minimal.h",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(encoded)


def _file_bytes(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise ValueError(f"{label}が存在しません: {path}")
    return path.read_bytes()


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label}をJSONとして読めません: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label}のtop-levelはobjectでなければなりません")
    return value


def _root_path(root: Path, value: str | Path, label: str) -> Path:
    root = root.resolve()
    path = Path(value)
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label}はworkspace外を指せません: {value}") from error
    return resolved


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        # 明示variantのsourceがroot外でも、private pathをmodelへ露出しない。
        return f"external/{path.name}"


def _require_sha(data: bytes, expected: Any, label: str) -> str:
    actual = _sha256(data)
    if expected is not None and actual != str(expected):
        raise ValueError(f"{label} SHA-256不一致: {actual} != {expected}")
    return actual


def _source_identity(
    source_root: Path,
    expected_commit: Any,
    expected_tree: Any,
) -> dict[str, str]:
    """vendor sourceが固定commit/treeかつcleanであることを読取専用検証する。"""

    if expected_commit is None and expected_tree is None:
        return {}
    commands = (
        ("commit", ["git", "rev-parse", "HEAD"]),
        ("tree", ["git", "rev-parse", "HEAD^{tree}"]),
        ("status", ["git", "status", "--porcelain=v1", "--untracked-files=all"]),
    )
    observed: dict[str, str] = {}
    for label, command in commands:
        completed = subprocess.run(
            command,
            cwd=source_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
        text = completed.stdout.decode("utf-8", "replace").strip()
        if completed.returncode:
            raise RuntimeError(f"source {label}検証失敗: {source_root.name}: {text[-800:]}")
        observed[label] = text
    if observed["status"]:
        raise ValueError(f"固定sourceがcleanではありません: {source_root.name}")
    if expected_commit is not None and observed["commit"] != str(expected_commit):
        raise ValueError(
            f"固定source commit不一致: {source_root.name}: "
            f"{observed['commit']} != {expected_commit}"
        )
    if expected_tree is not None and observed["tree"] != str(expected_tree):
        raise ValueError(
            f"固定source tree不一致: {source_root.name}: "
            f"{observed['tree']} != {expected_tree}"
        )
    return {"commit": observed["commit"], "tree": observed["tree"], "status": "clean"}


def _parse_integer(token: Any, label: str) -> int:
    if isinstance(token, bool):
        raise ValueError(f"{label}は整数でなければなりません")
    if isinstance(token, int):
        return token
    if isinstance(token, str):
        try:
            return int(token, 0)
        except ValueError:
            try:
                return int(token, 16)
            except ValueError as error:
                raise ValueError(f"{label}が整数ではありません: {token!r}") from error
    raise ValueError(f"{label}は整数でなければなりません")


def _rom_offset(address: str | int, label: str) -> int:
    # upstream control filesのaddress fieldは0x prefixなしでも常にhex。
    if isinstance(address, str):
        try:
            value = int(address, 16)
        except ValueError as error:
            raise ValueError(f"{label}がhex addressではありません: {address!r}") from error
    else:
        value = _parse_integer(address, label)
    return value - ROM_BASE if value >= ROM_BASE else value


def _slice_ff(data: bytes, start: int, end: int) -> bytes:
    if start < 0 or end < start:
        raise ValueError(f"不正なhalf-open spanです: [{start:#x}, {end:#x})")
    if start >= len(data):
        return b"\xff" * (end - start)
    prefix = data[start : min(end, len(data))]
    return prefix + b"\xff" * (end - start - len(prefix))


def _digest_field(data: bytes) -> dict[str, Any]:
    return {"length": len(data), "sha256": _sha256(data)}


@dataclass(frozen=True)
class ControlRecord:
    source_kind: str
    source_path: str
    line: int
    tokens: tuple[str, ...]
    active_condition: str


@dataclass
class _WriteEvent:
    engine: str
    profile: str
    source_kind: str
    source_path: str
    line: int
    start: int
    data: bytes
    intended_symbol: str
    active_condition: str
    evidence: list[str]
    followup: str | None = None
    before: bytes = b""
    overlap_ids: list[str] = field(default_factory=list)

    @property
    def end(self) -> int:
        return self.start + len(self.data)


def _scan_defines(text: str, defines: dict[str, Any]) -> None:
    """T01でpatchされたupstream include処理と同じdefine/undef効果を適用する。"""

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("#define "):
            parts = stripped.split()
            if len(parts) < 2:
                continue
            if len(parts) == 2 or parts[2].startswith(("//", "/*")):
                value: Any = True
            else:
                value = parts[2]
            defines[parts[1]] = value
        elif stripped.startswith("#undef "):
            parts = stripped.split()
            if len(parts) > 1:
                defines.pop(parts[1], None)


def effective_defines(
    source_root: Path,
    include_paths: Iterable[str],
    *,
    virtual_files: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """上流control fileがincludeから取得する最終macro辞書を返す。"""

    source_root = source_root.resolve()
    virtual = dict(virtual_files or {})
    defines: dict[str, Any] = {}
    for include in include_paths:
        normalized = Path(include).as_posix()
        if normalized in virtual:
            text = virtual[normalized]
        else:
            path = (source_root / normalized).resolve(strict=False)
            try:
                path.relative_to(source_root)
            except ValueError as error:
                raise ValueError(f"includeがsource root外です: {include}") from error
            if not path.is_file():
                raise ValueError(f"include fileがありません: {include}")
            text = path.read_text(encoding="utf-8")
        _scan_defines(text, defines)
    return defines


def parse_control_file(
    source_root: Path,
    filename: str,
    source_kind: str,
    *,
    profile: str,
    virtual_files: Mapping[str, str] | None = None,
) -> tuple[list[ControlRecord], int]:
    """include/config条件を評価し、active recordとinactive件数を返す。"""

    source_root = source_root.resolve()
    path = (source_root / filename).resolve(strict=False)
    try:
        path.relative_to(source_root)
    except ValueError as error:
        raise ValueError(f"control fileがsource root外です: {filename}") from error
    if not path.exists():
        return [], 0
    if not path.is_file():
        raise ValueError(f"control pathはfileでなければなりません: {filename}")

    defines: dict[str, Any] = {}
    stack: list[tuple[str, bool]] = []
    records: list[ControlRecord] = []
    inactive = 0
    virtual = dict(virtual_files or {})
    relative_source = filename.replace(os.sep, "/")

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        # upstreamはincludeだけcolumn 0を要求する。
        if raw.startswith('#include "'):
            match = re.match(r'^#include\s+"([^"]+)"', raw)
            if not match:
                raise ValueError(f"include構文が不正です: {relative_source}:{line_number}")
            included = match.group(1)
            _scan_defines(
                virtual.get(included)
                if included in virtual
                else (source_root / included).read_text(encoding="utf-8"),
                defines,
            )
            continue

        stripped = raw.strip()
        upper = stripped.upper()
        parts = stripped.split()
        if upper.startswith("#IFDEF ") and len(parts) > 1:
            stack.insert(0, (parts[1], True))
            continue
        if upper.startswith("#IFNDEF ") and len(parts) > 1:
            stack.insert(0, (parts[1], False))
            continue
        if upper == "#ELSE":
            if not stack:
                raise ValueError(f"孤立した#elseです: {relative_source}:{line_number}")
            name, required = stack.pop(0)
            stack.insert(0, (name, not required))
            continue
        if upper == "#ENDIF":
            if not stack:
                raise ValueError(f"孤立した#endifです: {relative_source}:{line_number}")
            stack.pop(0)
            continue
        if not stripped or stripped.startswith("#"):
            continue

        active = all((name in defines) == required for name, required in stack)
        clauses = [f"profile == {profile}"]
        clauses.extend(
            f"{'defined' if required else '!defined'}({name})"
            for name, required in reversed(stack)
        )
        if not active:
            inactive += 1
            continue
        records.append(
            ControlRecord(
                source_kind=source_kind,
                source_path=relative_source,
                line=line_number,
                tokens=tuple(stripped.split()),
                active_condition=" && ".join(clauses),
            )
        )
    if stack:
        raise ValueError(f"閉じていないconditionalがあります: {relative_source}")
    return records, inactive


def parse_offsets_ini(data: str) -> dict[str, int]:
    """T01 offsets.iniをsymbol -> ROM offsetへ変換する。"""

    symbols: dict[str, int] = {}
    for line_number, raw in enumerate(data.splitlines(), 1):
        if not raw.strip():
            continue
        match = re.fullmatch(r"\s*(.+?):\s+([0-9A-Fa-f]{8})\s*", raw)
        if not match:
            raise ValueError(f"offsets.ini構文が不正です: line {line_number}")
        symbol = match.group(1)
        address = int(match.group(2), 16)
        if address < ROM_BASE:
            raise ValueError(f"ROM symbol addressではありません: {symbol}={address:#x}")
        offset = address - ROM_BASE
        previous = symbols.setdefault(symbol, offset)
        if previous != offset:
            raise ValueError(f"symbolが異なる値で重複しています: {symbol}")
    if not symbols:
        raise ValueError("offsets.iniにsymbolがありません")
    return symbols


def hook_bytes(symbol_offset: int, hook_offset: int, register: int) -> tuple[int, bytes]:
    """upstream Hook()が書くaligned startとexact bytesを返す。"""

    if hook_offset & 1:
        hook_offset -= 1
    register &= 7
    if hook_offset % 4:
        data = bytes((0x01, 0x48 | register, register << 3, 0x47, 0, 0))
    else:
        data = bytes((0x00, 0x48 | register, register << 3, 0x47))
    pointer = symbol_offset + ROM_BASE + 1
    if not 0 <= pointer <= 0xFFFFFFFF:
        raise ValueError("hook pointerが32-bit ROM address外です")
    return hook_offset, data + pointer.to_bytes(4, "little")


def repoint_bytes(symbol_offset: int, slide: int = 0) -> bytes:
    pointer = symbol_offset + ROM_BASE + slide
    if not 0 <= pointer <= 0xFFFFFFFF:
        raise ValueError("repoint pointerが32-bit address外です")
    return pointer.to_bytes(4, "little")


def function_wrapper_bytes(
    symbol_offset: int, hook_offset: int, num_params: int, is_returning: int
) -> tuple[int, bytes]:
    """upstream FunctionWrap()の可変長wrapperをbyte単位で再現する。"""

    if hook_offset & 1:
        hook_offset -= 1
    num_params -= 1
    if num_params < 0:
        raise ValueError("function rewrite numParamsは1以上でなければなりません")
    if is_returning not in (0, 1):
        raise ValueError("function rewrite isReturningは0/1でなければなりません")
    if num_params < 4:
        data = bytes(
            (
                0x10, 0xB5, 0x03, 0x4C, 0x00, 0xF0, 0x03, 0xF8,
                0x10, 0xBC, is_returning + 1, 0xBC,
                is_returning << 3, 0x47, 0x20, 0x47,
            )
        )
    else:
        k = num_params - 3
        values = bytearray((0x10, 0xB5, 0x82, 0xB0))
        for index in range(k + 2):
            values.extend((index + 2, 0x9C, index, 0x94))
        values.extend(
            (
                0x00, 0x9C, num_params - 1, 0x94,
                0x01, 0x9C, num_params, 0x94,
                0x02, 0xB0, k + 8, 0x4C,
                0x00, 0xF0, (k << 1) + 13, 0xF8,
                0x82, 0xB0, num_params, 0x9C,
                0x01, 0x94, num_params - 1, 0x9C, 0x00, 0x94,
            )
        )
        for index in reversed(range(k + 2)):
            values.extend((index, 0x9C, index + 2, 0x94))
        values.extend(
            (
                0x02, 0xB0, 0x10, 0xBC, is_returning + 1, 0xBC,
                is_returning << 3, 0x47, 0x20, 0x47,
            )
        )
        if any(value > 0xFF for value in values):
            raise ValueError("function rewrite operandが1 byteを超えました")
        data = bytes(values)
    return hook_offset, data + repoint_bytes(symbol_offset, 1)


def _org_sites(source_text: str) -> list[tuple[int, int]]:
    sites: list[tuple[int, int]] = []
    for line_number, raw in enumerate(source_text.splitlines(), 1):
        match = re.match(r"^\s*\.org\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*(?:,|$)", raw)
        if match:
            sites.append((int(match.group(1), 0), line_number))
    sites.sort()
    if len({offset for offset, _ in sites}) != len(sites):
        raise ValueError("special_inserts.asmに重複.orgがあります")
    return sites


def derive_special_insert_spans(
    source_text: str, assembled_binary: bytes
) -> list[tuple[int, int, int, bytes]]:
    """upstream special insert scannerと同じexact half-open spansを返す。

    戻り値は ``(start, end, source_line, bytes)``。assembler/object由来の
    binaryを必須とし、sourceだけから命令長を推測しない。
    """

    sites = _org_sites(source_text)
    if sites and not assembled_binary:
        raise ValueError("special insert spanにはassembler出力が必要です")
    spans: list[tuple[int, int, int, bytes]] = []
    for index, (start, line) in enumerate(sites):
        if start >= len(assembled_binary):
            raise ValueError(f".orgがassembler出力外です: {start:#x}")
        if index == len(sites) - 1:
            end = len(assembled_binary)
        else:
            next_start = sites[index + 1][0]
            cursor = start
            while cursor < next_start:
                if assembled_binary[cursor : cursor + 4] == b"\xff\xff\xff\xff":
                    break
                cursor += 1
            end = cursor
        # upstream parserはC block comment内の行頭.orgもoffset listへ拾うが、
        # assembler側は何もemitせず先頭がfill(FF)になる。この場合ReplaceBytes
        # もzero-token writeとなるため、fixed write rowは作らない。
        if end == start:
            continue
        if end < start:
            raise ValueError(f"special insert spanが逆転しています: {start:#x}")
        spans.append((start, end, line, assembled_binary[start:end]))
    return spans


def _assemble_special_inserts(
    source_root: Path, variant: Mapping[str, Any]
) -> tuple[bytes, dict[str, str]]:
    explicit = variant.get("special_inserts_bin")
    if explicit is not None:
        path = Path(str(explicit))
        if not path.is_absolute():
            path = source_root / path
        data = _file_bytes(path, "special inserts binary")
        _require_sha(data, variant.get("special_inserts_sha256"), "special inserts binary")
        return data, {"method": "provided_binary", "sha256": _sha256(data)}

    assembler = str(variant.get("assembler") or shutil.which("arm-none-eabi-as") or "")
    objcopy = str(variant.get("objcopy") or shutil.which("arm-none-eabi-objcopy") or "")
    if not assembler or not objcopy:
        raise RuntimeError("special insertsのexact spanにassembler/objcopyが必要です")
    assembler_sha = _require_sha(
        _file_bytes(Path(assembler), "assembler"),
        variant.get("assembler_sha256"),
        "assembler",
    )
    objcopy_sha = _require_sha(
        _file_bytes(Path(objcopy), "objcopy"),
        variant.get("objcopy_sha256"),
        "objcopy",
    )
    with tempfile.TemporaryDirectory(prefix="t02-special-") as temporary:
        temporary_path = Path(temporary)
        obj = temporary_path / "special_inserts.o"
        binary = temporary_path / "special_inserts.bin"
        commands = (
            [assembler, "-mthumb", "-I", "assembly", "-c", "special_inserts.asm", "-o", str(obj)],
            [objcopy, "-O", "binary", str(obj), str(binary)],
        )
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=source_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
            if completed.returncode:
                excerpt = completed.stdout.decode("utf-8", "replace")[-1200:]
                raise RuntimeError(f"special inserts assembly失敗: {excerpt}")
        data = _file_bytes(binary, "assembled special inserts")
    return data, {
        "method": "assembler_object",
        "sha256": _sha256(data),
        "assembler_sha256": assembler_sha,
        "objcopy_sha256": objcopy_sha,
    }


def _symbol(symbols: Mapping[str, int], name: str, record: ControlRecord) -> int:
    try:
        return symbols[name]
    except KeyError as error:
        raise ValueError(
            f"active symbolがoffsets.iniにありません: {name} "
            f"({record.source_path}:{record.line})"
        ) from error


def _replacement_bytes(token_text: Sequence[str], defines: Mapping[str, Any]) -> bytes:
    if not token_text:
        raise ValueError("byte replacementが空です")
    try:
        values = [int(token, 16) for token in token_text]
    except ValueError:
        if len(token_text) != 1 or token_text[0] not in defines:
            raise ValueError(f"未知のbyte replacement値です: {' '.join(token_text)}") from None
        raw = defines[token_text[0]]
        try:
            number = int(raw)
        except (TypeError, ValueError):
            try:
                number = int(str(raw), 16)
            except ValueError as error:
                raise ValueError(f"macroが数値ではありません: {token_text[0]}={raw}") from error
        # upstream: hex(number)の0x後を単一byte tokenとしてReplaceBytesへ渡す。
        values = [int(hex(number)[2:], 16)]
    if any(value < 0 or value > 0xFF for value in values):
        raise ValueError(f"byte replacement値が1 byte外です: {token_text}")
    return bytes(values)


def _apply_event(memory: bytearray, event: _WriteEvent, events: list[_WriteEvent]) -> None:
    if not event.data:
        raise ValueError(f"zero-length writeは禁止です: {event.source_path}:{event.line}")
    if event.start < 0 or event.end > len(memory):
        raise ValueError(
            f"write spanがROM外です: [{event.start:#x}, {event.end:#x}) / {len(memory):#x}"
        )
    event.before = bytes(memory[event.start : event.end])
    memory[event.start : event.end] = event.data
    events.append(event)


def simulate_repointall(
    memory: bytearray,
    controls: Sequence[tuple[int, int, str, ControlRecord]],
    *,
    engine: str,
    profile: str,
    scan_end: int = REPOINT_SCAN_END,
) -> list[_WriteEvent]:
    """上流RealRepointを再現し、全match（同値writeを含む）を返す。"""

    if scan_end < 0 or scan_end > len(memory):
        raise ValueError("repointall scan_endがROM外です")
    scan_end -= scan_end % 4
    pointer_order: list[int] = []
    pointer_targets: dict[int, tuple[int, str, ControlRecord]] = {}
    for control_offset, symbol_offset, symbol, record in controls:
        if control_offset < 0 or control_offset + 4 > len(memory):
            raise ValueError(f"repointall control addressがROM外です: {control_offset:#x}")
        old_pointer = int.from_bytes(memory[control_offset : control_offset + 4], "little")
        pointer_order.append(old_pointer)
        pointer_targets[old_pointer] = (symbol_offset, symbol, record)

    events: list[_WriteEvent] = []
    if engine not in IGNORED_REPOINT_OFFSETS:
        raise ValueError(f"repointall engineが不正です: {engine}")
    ignored_offsets = IGNORED_REPOINT_OFFSETS[engine]
    for offset in range(0, scan_end, 4):
        if offset in ignored_offsets:
            continue
        word = int.from_bytes(memory[offset : offset + 4], "little")
        for old_pointer in pointer_order:
            if word != old_pointer:
                continue
            symbol_offset, symbol, record = pointer_targets[old_pointer]
            data = repoint_bytes(symbol_offset)
            event = _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="repointall",
                source_path=record.source_path,
                line=record.line,
                start=offset,
                data=data,
                intended_symbol=symbol,
                active_condition=record.active_condition,
                evidence=[
                    f"{record.source_path}:{record.line}",
                    "upstream RealRepoint 4-byte aligned scan",
                    f"matched_pointer_sha256={_sha256(old_pointer.to_bytes(4, 'little'))}",
                ],
            )
            _apply_event(memory, event, events)
            break
    return events


def _song_events(
    source_root: Path,
    memory: bytearray,
    symbols: Mapping[str, int],
    *,
    engine: str,
    profile: str,
) -> list[_WriteEvent]:
    path = source_root / "songs"
    if not path.exists():
        return []
    records, _ = parse_control_file(
        source_root, "songs", "song_pointer", profile=profile
    )
    if not records:
        return []
    if len(memory) < 0x1C10DC:
        raise ValueError("song table pointer位置がROM外です")
    song_table = int.from_bytes(memory[0x1C10D8 : 0x1C10DC], "little") - ROM_BASE
    events: list[_WriteEvent] = []
    for record in records:
        if len(record.tokens) != 2:
            raise ValueError(f"songs recordが不正です: {record.source_path}:{record.line}")
        song_id = _parse_integer(record.tokens[0], "song id")
        symbol = record.tokens[1]
        try:
            symbol_offset = symbols[symbol]
        except KeyError:
            symbol_offset = _parse_integer(symbol, "song symbol/address")
        event = _WriteEvent(
            engine=engine,
            profile=profile,
            source_kind="song_pointer",
            source_path="songs",
            line=record.line,
            start=song_table + song_id * 8,
            data=repoint_bytes(symbol_offset),
            intended_symbol=symbol,
            active_condition=record.active_condition,
            evidence=[f"songs:{record.line}", "upstream song table simulation"],
        )
        _apply_event(memory, event, events)
    return events


def _classify(
    event: _WriteEvent,
    clean: bytes,
    vega: bytes,
    factory: bytes,
) -> tuple[str, str | None, str]:
    start, end = event.start, event.end
    vega_bytes = _slice_ff(vega, start, end)
    clean_bytes = _slice_ff(clean, start, end)
    factory_bytes = _slice_ff(factory, start, end)
    if event.data == vega_bytes:
        return "SAME_TARGET", None, "written digest equals Vega digest"
    if event.source_kind == "linker":
        return "RELOCATE", None, "primary linked payload requires integration-region relocation"
    if vega_bytes == clean_bytes:
        classification = "CFRU" if event.engine == "cfru" else "PORT"
        factory_note = " and equals Factory" if event.data == factory_bytes else ""
        return (
            classification,
            None,
            f"Vega digest equals clean digest; active {event.engine.upper()} write{factory_note}",
        )
    # upstream writeとVega変更が競合するため、統合wrapper/再実装の対象。
    factory_note = (
        "written digest equals Factory digest"
        if event.data == factory_bytes
        else "written digest differs from Factory digest"
    )
    return "PORT", None, f"Vega differs from clean and written differs from Vega; {factory_note}"


def _events_to_rows(
    events: list[_WriteEvent], clean: bytes, vega: bytes, factory: bytes
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, event in enumerate(events, 1):
        write_id = f"{event.engine}/{event.profile}/{index:06d}"
        classification, followup, classification_evidence = _classify(
            event, clean, vega, factory
        )
        start, end = event.start, event.end
        clean_bytes = _slice_ff(clean, start, end)
        vega_bytes = _slice_ff(vega, start, end)
        factory_bytes = _slice_ff(factory, start, end)
        rows.append(
            {
                "write_id": write_id,
                "sequence": index,
                "engine": event.engine,
                "profile": event.profile,
                "source_kind": event.source_kind,
                "source": {"path": event.source_path, "line": event.line},
                "start": ROM_BASE + start,
                "end": ROM_BASE + end,
                "rom_offset_start": start,
                "rom_offset_end": end,
                "length": len(event.data),
                "intended_symbol": event.intended_symbol,
                "active_condition": event.active_condition,
                "written": _digest_field(event.data),
                "pre_write": _digest_field(event.before),
                "clean": _digest_field(clean_bytes),
                "vega": _digest_field(vega_bytes),
                "factory": _digest_field(factory_bytes),
                "same_value_write": event.before == event.data,
                "classification_candidate": classification,
                "classification_evidence": classification_evidence,
                "evidence": list(event.evidence),
                "followup": followup,
                "overlaps": [],
            }
        )

    # Address sweepでwrite順序とは独立にoverlapを注記する。
    ordered = sorted(range(len(rows)), key=lambda i: (rows[i]["rom_offset_start"], rows[i]["rom_offset_end"], i))
    active: list[int] = []
    for current_index in ordered:
        current = rows[current_index]
        start = int(current["rom_offset_start"])
        active = [i for i in active if int(rows[i]["rom_offset_end"]) > start]
        for other_index in active:
            other = rows[other_index]
            if int(other["rom_offset_end"]) <= start:
                continue
            current["overlaps"].append(other["write_id"])
            other["overlaps"].append(current["write_id"])
        active.append(current_index)
    for row in rows:
        row["overlaps"].sort()
    return rows


def _annotate_cross_engine_overlaps(rows: list[dict[str, Any]]) -> None:
    """同時統合されるDPE↔CFRU writesのaddress overlapを注記する。

    CFRU profiles同士は相互排他的なbuild variantなので比較しない。variant内
    overlapは ``_events_to_rows`` が既に注記済みで、ここではengineを跨ぐ
    pairだけを追加する。
    """

    ordered = sorted(
        range(len(rows)),
        key=lambda index: (
            int(rows[index]["rom_offset_start"]),
            int(rows[index]["rom_offset_end"]),
            str(rows[index]["write_id"]),
        ),
    )
    active: list[int] = []
    for current_index in ordered:
        current = rows[current_index]
        start = int(current["rom_offset_start"])
        active = [
            index for index in active if int(rows[index]["rom_offset_end"]) > start
        ]
        for other_index in active:
            other = rows[other_index]
            if other["engine"] == current["engine"]:
                continue
            current_id = str(current["write_id"])
            other_id = str(other["write_id"])
            if other_id not in current["overlaps"]:
                current["overlaps"].append(other_id)
            if current_id not in other["overlaps"]:
                other["overlaps"].append(current_id)
        active.append(current_index)
    for row in rows:
        row["overlaps"].sort()


CODE_CONTEXT_KINDS = frozenset({"hook", "function_rewrite", "routine_pointer"})


def _annotate_code_contexts(
    rows: list[dict[str, Any]], references: Mapping[str, bytes], radius: int = 16
) -> None:
    """code hook/pointer siteへprivate-byte-freeなbounded context観測を付ける。"""

    if radius < 2 or radius > 64:
        raise ValueError("code context radiusは2..64でなければなりません")
    for row in rows:
        if row["source_kind"] not in CODE_CONTEXT_KINDS:
            row["code_context"] = None
            continue
        site_start = int(row["rom_offset_start"])
        site_end = int(row["rom_offset_end"])
        context_start = max(0, site_start - radius) & ~1
        context_end = min(ROM_SIZE, site_end + radius)
        context_end -= context_end % 2
        if context_end <= context_start:
            raise ValueError(f"code context spanが空です: {row['write_id']}")
        contexts = {
            name: _slice_ff(data, context_start, context_end)
            for name, data in references.items()
        }
        clean = contexts["clean"]
        vega = contexts["vega"]
        factory = contexts["factory"]
        if row["source_kind"] in {"hook", "function_rewrite"}:
            site_semantics = "thumb_code_hook"
            containing_status = (
                "VEGA_CHANGED_IN_BOUNDED_CONTEXT"
                if vega != clean
                else "NO_VEGA_CHANGE_IN_BOUNDED_CONTEXT"
            )
        else:
            site_semantics = "routine_pointer_table"
            containing_status = "NOT_A_CODE_CONTAINER_POINTER_TABLE"
        row["code_context"] = {
            "architecture": "ARMv4T/Thumb",
            "site_semantics": site_semantics,
            "start": ROM_BASE + context_start,
            "end": ROM_BASE + context_end,
            "rom_offset_start": context_start,
            "rom_offset_end": context_end,
            "clean": _digest_field(clean),
            "vega": _digest_field(vega),
            "factory": _digest_field(factory),
            "vega_changed_from_clean": vega != clean,
            "factory_changed_from_clean": factory != clean,
            "containing_function_status": containing_status,
            "raw_bytes_in_model": False,
        }


def _disassemble_thumb_context(
    data: bytes, start: int, objdump: Path
) -> list[dict[str, Any]]:
    """opcode表示を無効化し、bounded Thumb instructionだけを返す。"""

    with tempfile.NamedTemporaryFile(prefix="t02-disasm-", suffix=".bin") as handle:
        handle.write(data)
        handle.flush()
        completed = subprocess.run(
            [
                str(objdump),
                "-D",
                "-b",
                "binary",
                "-marm",
                "-Mforce-thumb",
                f"--adjust-vma={ROM_BASE + start:#x}",
                "--no-show-raw-insn",
                handle.name,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
    if completed.returncode:
        raise RuntimeError("bounded Thumb disassemblyに失敗しました")
    instructions: list[dict[str, Any]] = []
    for raw in completed.stdout.decode("utf-8", "replace").splitlines():
        match = re.match(r"^\s*([0-9A-Fa-f]+):\s+(.+?)\s*$", raw)
        if not match:
            continue
        text = re.sub(r"\s+", " ", match.group(2)).strip()
        # undecodable data directiveはliteral opcodeを含むので公開しない。
        if re.match(r"^\.(?:byte|short|hword|word|inst)\b", text):
            text = "undecodable"
        instructions.append({"address": int(match.group(1), 16), "instruction": text})
    if not instructions:
        raise RuntimeError("bounded Thumb disassemblyが空です")
    return instructions


def _representative_code_disassembly(
    rows: Sequence[Mapping[str, Any]],
    references: Mapping[str, bytes],
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    path = Path(str(contract.get("path") or shutil.which("arm-none-eabi-objdump") or ""))
    if not path.is_file():
        raise RuntimeError("bounded code contextにarm-none-eabi-objdumpが必要です")
    digest = _require_sha(
        _file_bytes(path, "arm-none-eabi-objdump"),
        contract.get("sha256"),
        "arm-none-eabi-objdump",
    )
    candidates: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for row in rows:
        if row["source_kind"] not in {"hook", "function_rewrite"}:
            continue
        key = (str(row["engine"]), str(row["profile"]), str(row["source_kind"]))
        current = candidates.get(key)
        # Vega変更があるrowを優先し、その中でwrite_id最小を代表にする。
        if current is None or (
            bool(row["code_context"]["vega_changed_from_clean"])
            and not bool(current["code_context"]["vega_changed_from_clean"])
        ):
            candidates[key] = row
    output: list[dict[str, Any]] = []
    for key in sorted(candidates):
        row = candidates[key]
        context = row["code_context"]
        start = int(context["rom_offset_start"])
        end = int(context["rom_offset_end"])
        output.append(
            {
                "write_id": row["write_id"],
                "source_kind": row["source_kind"],
                "context_start": ROM_BASE + start,
                "context_end": ROM_BASE + end,
                "selection": "prefer Vega-changed bounded context; then first write_id",
                "clean": _disassemble_thumb_context(
                    _slice_ff(references["clean"], start, end), start, path
                ),
                "vega": _disassemble_thumb_context(
                    _slice_ff(references["vega"], start, end), start, path
                ),
                "factory": _disassemble_thumb_context(
                    _slice_ff(references["factory"], start, end), start, path
                ),
                "raw_opcode_bytes_in_model": False,
            }
        )
    return output, {"path": str(path), "sha256": digest}


def validate_write_overlaps(
    writes: Sequence[Mapping[str, Any]],
    *,
    allowed_pairs: Iterable[Sequence[str]] = (),
) -> None:
    """未許可overlapを拒否する。pair順序は問わない。"""

    allowed_list = [tuple(sorted(map(str, pair))) for pair in allowed_pairs]
    if any(len(pair) != 2 or not pair[0] or pair[0] == pair[1] for pair in allowed_list):
        raise ValueError("allowed overlap pairは異なる2 write_idでなければなりません")
    allowed = set(allowed_list)
    if len(allowed) != len(allowed_list):
        raise ValueError("allowed overlap pairが重複しています")
    seen: set[tuple[str, str]] = set()
    for row in writes:
        write_id = str(row.get("write_id", ""))
        for other in row.get("overlaps", []):
            pair = tuple(sorted((write_id, str(other))))
            if pair in seen:
                continue
            seen.add(pair)
            if pair not in allowed:
                raise ValueError(f"未分類のfixed-write overlapです: {pair[0]} <-> {pair[1]}")
    stale = sorted(allowed - seen)
    if stale:
        raise ValueError(f"存在しないallowed overlapです: {stale[0][0]} <-> {stale[0][1]}")


def expand_cross_engine_overlap_template(value: Any) -> list[list[str]]:
    """policyの圧縮cross-engine allowlistを決定的write_id pairへ展開する。"""

    if not isinstance(value, Mapping):
        raise ValueError("allowed_cross_engine_overlap_templateはobjectでなければなりません")
    required = {"left_engine", "left_profiles", "right_variant", "write_number_pairs"}
    unknown = sorted(set(value) - required)
    missing = sorted(required - set(value))
    if unknown or missing:
        raise ValueError(f"cross-engine overlap template key不正: missing={missing}, unknown={unknown}")
    left_engine = value["left_engine"]
    right_variant = value["right_variant"]
    profiles = value["left_profiles"]
    number_pairs = value["write_number_pairs"]
    if left_engine not in {"dpe", "cfru"} or not isinstance(right_variant, str):
        raise ValueError("cross-engine overlap template variantが不正です")
    if not re.fullmatch(r"(?:dpe|cfru)/[A-Za-z0-9-]+", right_variant):
        raise ValueError("cross-engine overlap template right_variantが不正です")
    if right_variant.split("/", 1)[0] == left_engine:
        raise ValueError("cross-engine overlap templateは異なるengine間に限ります")
    if not isinstance(profiles, list) or not all(
        isinstance(profile, str) and re.fullmatch(r"[A-Za-z0-9-]+", profile)
        for profile in profiles
    ):
        raise ValueError("cross-engine overlap template profilesが不正です")
    if len(set(profiles)) != len(profiles):
        raise ValueError("cross-engine overlap template profileが重複しています")
    if not isinstance(number_pairs, list):
        raise ValueError("cross-engine overlap template write_number_pairsが不正です")
    if bool(profiles) != bool(number_pairs):
        raise ValueError("cross-engine overlap template profiles/pairsは共に空か共に非空です")
    normalized_numbers: list[tuple[int, int]] = []
    for pair in number_pairs:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in pair)
        ):
            raise ValueError("cross-engine write number pairは正整数2個でなければなりません")
        normalized_numbers.append((pair[0], pair[1]))
    if len(set(normalized_numbers)) != len(normalized_numbers):
        raise ValueError("cross-engine write number pairが重複しています")
    return [
        [f"{left_engine}/{profile}/{left:06d}", f"{right_variant}/{right:06d}"]
        for profile in profiles
        for left, right in normalized_numbers
    ]


def validate_write_rows(
    rows: Sequence[Mapping[str, Any]],
    classifications: set[str],
    unknown_contract: Mapping[str, Any],
) -> None:
    required = {
        "write_id", "engine", "profile", "source_kind", "start", "end",
        "intended_symbol", "active_condition", "written", "clean", "vega",
        "factory", "classification_candidate", "evidence", "followup",
        "classification_evidence",
    }
    ids: set[str] = set()
    for row in rows:
        missing = sorted(required - row.keys())
        if missing:
            raise ValueError(f"write row必須field欠落: {missing}")
        write_id = str(row["write_id"])
        if not write_id or write_id in ids:
            raise ValueError(f"write_id重複/空です: {write_id!r}")
        ids.add(write_id)
        if int(row["end"]) <= int(row["start"]):
            raise ValueError(f"write spanが空です: {write_id}")
        classification = str(row["classification_candidate"])
        if classification not in classifications:
            raise ValueError(f"許可されないclassificationです: {classification}")
        if not isinstance(row["classification_evidence"], str) or not row[
            "classification_evidence"
        ].strip():
            raise ValueError(f"classification evidenceが空です: {write_id}")
        evidence = row["evidence"]
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            raise ValueError(f"write evidenceが空/不正です: {write_id}")
        if classification == "UNKNOWN":
            if unknown_contract.get("requires_nonempty_evidence") is not True:
                raise ValueError("unknown contractはnonempty evidenceを必須にしてください")
            if unknown_contract.get("requires_followup_task") is not True:
                raise ValueError("unknown contractはfollowup taskを必須にしてください")
            followup = row["followup"]
            allowed = unknown_contract.get("allowed_followups")
            if not isinstance(allowed, list) or not all(
                isinstance(item, str) and item for item in allowed
            ):
                raise ValueError("unknown contract allowed_followupsが不正です")
            if not isinstance(followup, str) or followup not in allowed:
                raise ValueError(f"UNKNOWN followupが未割当/許可外です: {write_id}")


def _source_virtual_files(
    root: Path, source_root: Path, profile: str, variant: Mapping[str, Any]
) -> tuple[dict[str, str], dict[str, str] | None]:
    config_path = source_root / "src/config.h"
    if not config_path.exists():
        return {}, None
    config_text = config_path.read_text(encoding="utf-8")
    profile_provenance: dict[str, str] | None = None
    overlay_value = variant.get("profile_overlay")
    if overlay_value is None and profile in PROFILE_OVERLAYS:
        overlay_value = PROFILE_OVERLAYS[profile]
    if overlay_value is not None:
        overlay_path = _root_path(root, str(overlay_value), "profile overlay")
        overlay_data = _file_bytes(overlay_path, "profile overlay")
        overlay_sha = _require_sha(
            overlay_data, variant.get("profile_overlay_sha256"), "profile overlay"
        )
        config_text += "\n" + overlay_data.decode("utf-8")
        profile_provenance = {
            "path": _relative(root, overlay_path),
            "sha256": overlay_sha,
        }
    return {"src/config.h": config_text}, profile_provenance


def _variant_events(
    root: Path,
    variant: Mapping[str, Any],
    references: Mapping[str, bytes],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    engine = str(variant.get("engine", "")).lower()
    profile = str(variant.get("profile", ""))
    if engine not in {"dpe", "cfru"} or not profile:
        raise ValueError("variant engine/profileが不正です")
    source_root = _root_path(root, str(variant["source_root"]), "source root")
    if not source_root.is_dir():
        raise ValueError(f"source rootがdirectoryではありません: {source_root}")
    source_identity = _source_identity(
        source_root,
        variant.get("source_commit"),
        variant.get("source_tree"),
    )
    artifact_root = _root_path(root, str(variant["artifact_root"]), "artifact root")

    input_path = _root_path(root, str(variant["input_rom"]), "variant input ROM")
    output_path = artifact_root / str(variant.get("output_rom", "test.gba"))
    output_bin_path = artifact_root / str(variant.get("output_bin", "output.bin"))
    offsets_path = artifact_root / str(variant.get("offsets", "offsets.ini"))
    output = _file_bytes(output_path, "T01 output ROM")
    if len(output) > ROM_SIZE:
        raise ValueError(f"T01 output ROMが32 MiBを超えます: {len(output)}")
    raw_input = _file_bytes(input_path, "variant input ROM")
    target_size = _parse_integer(variant.get("target_size", len(output)), "target_size")
    if target_size != len(output):
        raise ValueError("target_sizeとT01 output ROM sizeが一致しません")
    if len(raw_input) > target_size:
        raise ValueError("variant input ROMがtarget_sizeを超えます")
    input_data = raw_input + b"\xff" * (target_size - len(raw_input))
    output_bin = _file_bytes(output_bin_path, "T01 output.bin")
    offsets_data = _file_bytes(offsets_path, "T01 offsets.ini")
    symbols = parse_offsets_ini(offsets_data.decode("utf-8"))
    insertion_offset = _parse_integer(variant["insertion_offset"], "insertion_offset")
    if insertion_offset < 0 or insertion_offset + len(output_bin) > target_size:
        raise ValueError("linker payload spanがROM外です")

    expected = variant.get("expected", {})
    if not isinstance(expected, Mapping):
        raise ValueError("variant expectedはobjectでなければなりません")
    input_hash = _require_sha(input_data, expected.get("input_sha256"), "variant input")
    output_hash = _require_sha(output, expected.get("output_sha256"), "T01 output")
    output_bin_hash = _require_sha(
        output_bin, expected.get("output_bin_sha256"), "T01 output.bin"
    )
    offsets_hash = _require_sha(offsets_data, expected.get("offsets_sha256"), "T01 offsets.ini")

    memory = bytearray(input_data)
    events: list[_WriteEvent] = []
    source_prefix = _relative(root, source_root)
    # linker.ld:4はmake.py EditLinker()がbuild直前に書き換える生成入力。
    # tracked vendor linkerの旧ORIGINを証拠にせず、固定offsetの正本と書換え処理を指す。
    linker_line = 12
    linker_source = f"{source_prefix}/scripts/make.py"
    _apply_event(
        memory,
        _WriteEvent(
            engine=engine,
            profile=profile,
            source_kind="linker",
            source_path=linker_source,
            line=linker_line,
            start=insertion_offset,
            data=output_bin,
            intended_symbol=".text payload",
            active_condition=f"profile == {profile}",
            evidence=[
                f"{linker_source}:{linker_line}",
                f"{source_prefix}/scripts/make.py:67-68 (EditLinker)",
                f"effective linker.ld:4 ORIGIN={ROM_BASE + insertion_offset:#010x}",
                f"T01 output.bin sha256={output_bin_hash}",
                "T01 fixed insertion_offset",
            ],
        ),
        events,
    )

    virtual_files, profile_overlay = _source_virtual_files(
        root, source_root, profile, variant
    )
    parsed: dict[str, list[ControlRecord]] = {}
    inactive_count = 0
    for source_kind, filename in CONTROL_FILES:
        records, inactive = parse_control_file(
            source_root,
            filename,
            source_kind,
            profile=profile,
            virtual_files=virtual_files,
        )
        parsed[source_kind] = records
        inactive_count += inactive

    # defines are reset per upstream control file; bytereplacement includes all needed headers.
    includes: list[str] = []
    byte_file = source_root / "bytereplacement"
    if byte_file.exists():
        for raw in byte_file.read_text(encoding="utf-8").splitlines():
            match = re.match(r'^#include\s+"([^"]+)"', raw)
            if match:
                includes.append(match.group(1))
    byte_defines = effective_defines(
        source_root, includes, virtual_files=virtual_files
    )

    for record in parsed["byte_replacement"]:
        if len(record.tokens) < 2:
            raise ValueError(f"byte replacement recordが不正です: {record.source_path}:{record.line}")
        start = _rom_offset(record.tokens[0], "byte replacement address")
        data = _replacement_bytes(record.tokens[1:], byte_defines)
        _apply_event(
            memory,
            _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="byte_replacement",
                source_path=f"{source_prefix}/{record.source_path}",
                line=record.line,
                start=start,
                data=data,
                intended_symbol="literal bytes",
                active_condition=record.active_condition,
                evidence=[
                    f"{source_prefix}/{record.source_path}:{record.line}",
                    "upstream ReplaceBytes token simulation",
                ],
            ),
            events,
        )

    special_source = source_root / "special_inserts.asm"
    special_provenance: dict[str, str] | None = None
    if special_source.exists():
        special_binary, special_provenance = _assemble_special_inserts(source_root, variant)
        special_text = special_source.read_text(encoding="utf-8")
        for start, end, line, data in derive_special_insert_spans(
            special_text, special_binary
        ):
            _apply_event(
                memory,
                _WriteEvent(
                    engine=engine,
                    profile=profile,
                    source_kind="special_insert",
                    source_path=f"{source_prefix}/special_inserts.asm",
                    line=line,
                    start=start,
                    data=data,
                    intended_symbol=".org emitted payload",
                    active_condition=f"profile == {profile}",
                    evidence=[
                        f"{source_prefix}/special_inserts.asm:{line}",
                        f"assembler binary sha256={special_provenance['sha256']}",
                        "upstream sentinel/next-.org extraction simulation",
                    ],
                ),
                events,
            )

    for record in parsed["hook"]:
        if len(record.tokens) != 3:
            raise ValueError(f"hook recordが不正です: {record.source_path}:{record.line}")
        symbol, address, register = record.tokens
        start, data = hook_bytes(
            _symbol(symbols, symbol, record),
            _rom_offset(address, "hook address"),
            _parse_integer(register, "hook register"),
        )
        _apply_event(
            memory,
            _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="hook",
                source_path=f"{source_prefix}/{record.source_path}",
                line=record.line,
                start=start,
                data=data,
                intended_symbol=symbol,
                active_condition=record.active_condition,
                evidence=[f"{source_prefix}/{record.source_path}:{record.line}", "upstream Hook byte simulation"],
            ),
            events,
        )

    for record in parsed["repoint"]:
        if len(record.tokens) not in (2, 3):
            raise ValueError(f"repoint recordが不正です: {record.source_path}:{record.line}")
        symbol, address = record.tokens[:2]
        slide = _parse_integer(record.tokens[2], "repoint slide") if len(record.tokens) == 3 else 0
        _apply_event(
            memory,
            _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="repoint",
                source_path=f"{source_prefix}/{record.source_path}",
                line=record.line,
                start=_rom_offset(address, "repoint address"),
                data=repoint_bytes(_symbol(symbols, symbol, record), slide),
                intended_symbol=symbol,
                active_condition=record.active_condition,
                evidence=[f"{source_prefix}/{record.source_path}:{record.line}", "upstream Repoint simulation"],
            ),
            events,
        )

    repointall_controls: list[tuple[int, int, str, ControlRecord]] = []
    for record in parsed["repointall"]:
        if len(record.tokens) != 2:
            raise ValueError(f"repointall recordが不正です: {record.source_path}:{record.line}")
        symbol, address = record.tokens
        # evidence path is public source-relative in serialized rows.
        public_record = ControlRecord(
            record.source_kind,
            f"{source_prefix}/{record.source_path}",
            record.line,
            record.tokens,
            record.active_condition,
        )
        repointall_controls.append(
            (
                _rom_offset(address, "repointall double-pointer address"),
                _symbol(symbols, symbol, record),
                symbol,
                public_record,
            )
        )
    repoint_scan_end = _parse_integer(
        variant.get("repoint_scan_end", min(REPOINT_SCAN_END, len(memory))),
        "repoint_scan_end",
    )
    events.extend(
        simulate_repointall(
            memory,
            repointall_controls,
            engine=engine,
            profile=profile,
            scan_end=repoint_scan_end,
        )
    )

    for record in parsed["routine_pointer"]:
        if len(record.tokens) != 2:
            raise ValueError(f"routine pointer recordが不正です: {record.source_path}:{record.line}")
        symbol, address = record.tokens
        _apply_event(
            memory,
            _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="routine_pointer",
                source_path=f"{source_prefix}/{record.source_path}",
                line=record.line,
                start=_rom_offset(address, "routine pointer address"),
                data=repoint_bytes(_symbol(symbols, symbol, record), 1),
                intended_symbol=symbol,
                active_condition=record.active_condition,
                evidence=[f"{source_prefix}/{record.source_path}:{record.line}", "upstream thumb Repoint simulation"],
            ),
            events,
        )

    for record in parsed["function_rewrite"]:
        if len(record.tokens) != 4:
            raise ValueError(f"function rewrite recordが不正です: {record.source_path}:{record.line}")
        symbol, address, num_params, is_returning = record.tokens
        start, data = function_wrapper_bytes(
            _symbol(symbols, symbol, record),
            _rom_offset(address, "function rewrite address"),
            _parse_integer(num_params, "function rewrite numParams"),
            _parse_integer(is_returning, "function rewrite isReturning"),
        )
        _apply_event(
            memory,
            _WriteEvent(
                engine=engine,
                profile=profile,
                source_kind="function_rewrite",
                source_path=f"{source_prefix}/{record.source_path}",
                line=record.line,
                start=start,
                data=data,
                intended_symbol=symbol,
                active_condition=record.active_condition,
                evidence=[f"{source_prefix}/{record.source_path}:{record.line}", "upstream variable-length FunctionWrap simulation"],
            ),
            events,
        )

    # Current pinned eventscripts is empty. Refuse future nonempty input rather than guessing map state.
    event_scripts = source_root / "eventscripts"
    if event_scripts.exists() and any(
        line.strip() and not line.strip().startswith("#")
        for line in event_scripts.read_text(encoding="utf-8").splitlines()
    ):
        raise RuntimeError("nonempty eventscriptsにはexact map-state simulationが必要です")
    events.extend(
        _song_events(
            source_root, memory, symbols, engine=engine, profile=profile
        )
    )

    replay_hash = _sha256(bytes(memory))
    if bytes(memory) != output:
        mismatch = next(
            (index for index, (actual, wanted) in enumerate(zip(memory, output)) if actual != wanted),
            min(len(memory), len(output)),
        )
        raise RuntimeError(
            f"fixed-write replayがT01 outputと一致しません: {engine}/{profile}; "
            f"first_mismatch={mismatch:#x}; replay_sha256={replay_hash}; "
            f"expected_sha256={output_hash}"
        )

    rows = _events_to_rows(events, references["clean"], references["vega"], references["factory"])
    kinds = Counter(row["source_kind"] for row in rows)
    classifications = Counter(row["classification_candidate"] for row in rows)
    return rows, {
        "engine": engine,
        "profile": profile,
        "write_count": len(rows),
        "inactive_record_count": inactive_count,
        "same_value_write_count": sum(bool(row["same_value_write"]) for row in rows),
        "overlap_row_count": sum(bool(row["overlaps"]) for row in rows),
        "source_kind_counts": dict(sorted(kinds.items())),
        "classification_counts": dict(sorted(classifications.items())),
        "input_sha256": input_hash,
        "output_sha256": output_hash,
        "output_bin_sha256": output_bin_hash,
        "offsets_sha256": offsets_hash,
        "replay_sha256": replay_hash,
        "special_inserts": special_provenance,
        "source_identity": source_identity,
        "profile_overlay": profile_overlay,
    }


def _standard_variants(
    root: Path, policy: Mapping[str, Any], result: Mapping[str, Any]
) -> list[dict[str, Any]]:
    builds = result.get("builds")
    if not isinstance(builds, list):
        raise ValueError("T01 result.buildsがlistではありません")
    selected: dict[tuple[str, str], Mapping[str, Any]] = {}
    for build in builds:
        if not isinstance(build, Mapping) or int(build.get("run", 0)) != 1:
            continue
        key = (str(build.get("engine", "")), str(build.get("profile", "")))
        if key in selected:
            raise ValueError(f"T01 run-1 variantが重複しています: {key}")
        selected[key] = build
    order = (("dpe", "base"), ("cfru", "baseline"), ("cfru", "factory-like"), ("cfru", "minimal"))
    missing = [key for key in order if key not in selected]
    if missing:
        raise ValueError(f"T01 resultにvariantがありません: {missing}")

    source_lock = policy.get("source_lock")
    if not isinstance(source_lock, Mapping) or not isinstance(source_lock.get("commits"), Mapping):
        raise ValueError("policy.source_lock.commitsがありません")
    locked_commits = source_lock["commits"]
    artifact_contract = policy.get("t01_artifact")
    if not isinstance(artifact_contract, Mapping) or not isinstance(
        artifact_contract.get("outputs"), Mapping
    ):
        raise ValueError("policy.t01_artifact.outputsがありません")
    locked_outputs = artifact_contract["outputs"]
    fingerprint = str(artifact_contract.get("fingerprint", ""))
    fingerprint_inputs = result.get("fingerprint_inputs")
    if not isinstance(fingerprint_inputs, Mapping) or not isinstance(
        fingerprint_inputs.get("profiles"), Mapping
    ):
        raise ValueError("T01 result fingerprint_inputs.profilesがありません")
    locked_profiles = fingerprint_inputs["profiles"]
    address_space = policy.get("address_space")
    if not isinstance(address_space, Mapping):
        raise ValueError("policy.address_spaceがありません")
    locked_insertions = {
        "dpe": _rom_offset(address_space["dpe_insert_start"], "DPE insertion start"),
        "cfru": _rom_offset(address_space["cfru_insert_start"], "CFRU insertion start"),
    }
    try:
        tool_contracts = result["toolcheck"]["tools"]["tools"]
        assembler_contract = tool_contracts["arm_none_eabi_as"]
        objcopy_contract = tool_contracts["arm_none_eabi_objcopy"]
    except (KeyError, TypeError) as error:
        raise ValueError("T01 resultにassembler/objcopy identityがありません") from error
    for name, contract in (("assembler", assembler_contract), ("objcopy", objcopy_contract)):
        if not isinstance(contract, Mapping) or not re.fullmatch(
            r"[0-9a-f]{64}", str(contract.get("sha256", ""))
        ):
            raise ValueError(f"T01 {name} identityが不正です")
    clean_path = str(policy["inputs"]["clean"]["path"])
    dpe_build = selected[("dpe", "base")]
    dpe_artifact = str(dpe_build["artifact_dir"])
    variants: list[dict[str, Any]] = []
    for engine, profile in order:
        build = selected[(engine, profile)]
        source_name = "DPE-JP" if engine == "dpe" else "CFRU-JP"
        locked_commit = str(locked_commits.get(engine, ""))
        if not re.fullmatch(r"[0-9a-f]{40}", locked_commit):
            raise ValueError(f"source lock commitが不正です: {engine}")
        if str(build.get("source_commit", "")) != locked_commit:
            raise ValueError(f"T01 build/source-lock commit不一致です: {engine}/{profile}")
        variant_name = f"{engine}/{profile}"
        if str(build.get("output_sha256", "")) != str(locked_outputs.get(variant_name, "")):
            raise ValueError(f"T01 build/policy output hash不一致です: {variant_name}")
        expected_artifact = Path(
            "build", "upstream-cache", fingerprint, engine, profile, "run-1"
        ).as_posix()
        if Path(str(build.get("artifact_dir", ""))).as_posix() != expected_artifact:
            raise ValueError(f"T01 artifact path不一致です: {variant_name}")
        if int(build.get("insertion_offset", -1)) != locked_insertions[engine]:
            raise ValueError(f"T01 insertion offset不一致です: {variant_name}")
        variant: dict[str, Any] = {
            "engine": engine,
            "profile": profile,
            "source_root": f"vendor/upstream/{source_name}",
            "artifact_root": str(build["artifact_dir"]),
            "input_rom": clean_path if engine == "dpe" else f"{dpe_artifact}/test.gba",
            "insertion_offset": int(build["insertion_offset"]),
            "target_size": ROM_SIZE,
            "source_commit": locked_commit,
            "source_tree": str(build["source_tree"]),
            "assembler": str(assembler_contract["path"]),
            "assembler_sha256": str(assembler_contract["sha256"]),
            "objcopy": str(objcopy_contract["path"]),
            "objcopy_sha256": str(objcopy_contract["sha256"]),
            "expected": {
                "input_sha256": build["input_sha256"],
                "output_sha256": build["output_sha256"],
                "output_bin_sha256": build["output_bin_sha256"],
                "offsets_sha256": build["offsets_sha256"],
            },
        }
        if profile in PROFILE_OVERLAYS:
            variant["profile_overlay"] = PROFILE_OVERLAYS[profile]
            profile_sha = str(locked_profiles.get(profile, ""))
            if not re.fullmatch(r"[0-9a-f]{64}", profile_sha):
                raise ValueError(f"T01 profile hashが不正です: {profile}")
            variant["profile_overlay_sha256"] = profile_sha
        variants.append(variant)
    return variants


def _reference_inputs(root: Path, policy: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    inputs = policy.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("policy.inputsがobjectではありません")
    data: dict[str, bytes] = {}
    provenance: dict[str, Any] = {}
    for name in ("clean", "vega", "factory"):
        entry = inputs.get(name)
        if not isinstance(entry, Mapping):
            raise ValueError(f"policy.inputs.{name}がありません")
        path = _root_path(root, str(entry["path"]), f"{name} reference")
        raw = _file_bytes(path, f"{name} reference")
        digest = _require_sha(raw, entry.get("sha256"), f"{name} reference")
        if entry.get("size") is not None and len(raw) != int(entry["size"]):
            raise ValueError(f"{name} reference size不一致")
        data[name] = raw
        provenance[name] = {"size": len(raw), "sha256": digest}
    return data, provenance


def _build_source_write_model(root: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    """固定source/T01 artifactから決定的なfixed-write modelを構築する。

    明示variantは ``policy['source_writes']['variants']`` で渡せる。省略時は
    T02 policyのT01 resultからDPE baseとCFRU 3 profileのrun-1を解決する。
    """

    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"rootがdirectoryではありません: {root}")
    if not isinstance(policy, Mapping):
        raise ValueError("policyはmappingでなければなりません")
    source_lock_provenance: dict[str, Any] | None = None
    source_lock = policy.get("source_lock")
    if source_lock is not None:
        if not isinstance(source_lock, Mapping):
            raise ValueError("policy.source_lockはobjectでなければなりません")
        lock_path = _root_path(root, str(source_lock["path"]), "source lock")
        lock_data = _file_bytes(lock_path, "source lock")
        lock_sha = _require_sha(lock_data, source_lock.get("sha256"), "source lock")
        lock_json = _read_json(lock_path, "source lock")
        lock_sources = lock_json.get("sources")
        if not isinstance(lock_sources, list):
            raise ValueError("source lock.sourcesがlistではありません")
        observed_commits = {
            str(entry.get("name")): str(entry.get("resolved_commit"))
            for entry in lock_sources
            if isinstance(entry, Mapping)
        }
        configured_commits = source_lock.get("commits")
        if not isinstance(configured_commits, Mapping):
            raise ValueError("policy.source_lock.commitsがobjectではありません")
        for name, commit in configured_commits.items():
            if observed_commits.get(str(name)) != str(commit):
                raise ValueError(f"policy/source-lock commit不一致です: {name}")
        source_lock_provenance = {"sha256": lock_sha, "commits": dict(configured_commits)}
    references, reference_provenance = _reference_inputs(root, policy)

    source_writes = policy.get("source_writes", {})
    if not isinstance(source_writes, Mapping):
        raise ValueError("policy.source_writesはobjectでなければなりません")
    explicit_variants = source_writes.get("variants")
    result: Mapping[str, Any] | None = None
    disassembler_contract: Mapping[str, Any]
    if explicit_variants is None:
        artifact = policy.get("t01_artifact")
        if not isinstance(artifact, Mapping):
            raise ValueError("policy.t01_artifactがありません")
        result_path = _root_path(root, str(artifact["result"]), "T01 result")
        result = _read_json(result_path, "T01 result")
        fingerprint = str(artifact.get("fingerprint", ""))
        if result.get("fingerprint") != fingerprint or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise ValueError("T01 fingerprint/result identity不一致")
        variants = _standard_variants(root, policy, result)
        try:
            disassembler_contract = result["toolcheck"]["tools"]["tools"][
                "arm_none_eabi_objdump"
            ]
        except (KeyError, TypeError) as error:
            raise ValueError("T01 resultにobjdump tool identityがありません") from error
    else:
        if not isinstance(explicit_variants, list) or not explicit_variants:
            raise ValueError("policy.source_writes.variantsは非空listでなければなりません")
        if not all(isinstance(item, Mapping) for item in explicit_variants):
            raise ValueError("source write variantはobjectでなければなりません")
        variants = [dict(item) for item in explicit_variants]
        configured_disassembler = source_writes.get("disassembler", {})
        if not isinstance(configured_disassembler, Mapping):
            raise ValueError("source_writes.disassemblerはobjectでなければなりません")
        disassembler_contract = configured_disassembler

    all_rows: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    for variant in variants:
        rows, summary = _variant_events(root, variant, references)
        # write_id/sequenceはvariant内で生成済み。variant key重複をここで拒否する。
        if any(
            item["engine"] == summary["engine"] and item["profile"] == summary["profile"]
            for item in variant_summaries
        ):
            raise ValueError(f"variant重複です: {summary['engine']}/{summary['profile']}")
        all_rows.extend(rows)
        variant_summaries.append(summary)

    _annotate_cross_engine_overlaps(all_rows)
    _annotate_code_contexts(all_rows, references)
    representative_disassembly, disassembler_provenance = (
        _representative_code_disassembly(
            all_rows, references, disassembler_contract
        )
    )

    classifications = set(map(str, policy.get("classifications", ())))
    if not classifications:
        classifications = {"VEGA", "CFRU", "PORT", "RELOCATE", "SAME_TARGET", "UNKNOWN"}
    unknown_contract = policy.get("unknown_contract", {})
    if not isinstance(unknown_contract, Mapping):
        raise ValueError("policy.unknown_contractはobjectでなければなりません")
    validate_write_rows(all_rows, classifications, unknown_contract)
    if "allowed_overlaps" not in source_writes:
        raise ValueError("policy.source_writes.allowed_overlapsがありません")
    allowed_overlaps = source_writes["allowed_overlaps"]
    if not isinstance(allowed_overlaps, list):
        raise ValueError("allowed_overlapsはlistでなければなりません")
    if "allowed_cross_engine_overlap_template" not in source_writes:
        raise ValueError(
            "policy.source_writes.allowed_cross_engine_overlap_templateがありません"
        )
    cross_engine_overlaps = expand_cross_engine_overlap_template(
        source_writes["allowed_cross_engine_overlap_template"]
    )
    direct = {tuple(sorted(map(str, pair))) for pair in allowed_overlaps}
    expanded = {tuple(sorted(pair)) for pair in cross_engine_overlaps}
    duplicate = sorted(direct & expanded)
    if duplicate:
        raise ValueError(
            f"direct/template overlap allowlistが重複しています: "
            f"{duplicate[0][0]} <-> {duplicate[0][1]}"
        )
    validate_write_overlaps(
        all_rows, allowed_pairs=[*allowed_overlaps, *cross_engine_overlaps]
    )

    kinds = Counter(str(row["source_kind"]) for row in all_rows)
    classes = Counter(str(row["classification_candidate"]) for row in all_rows)
    model: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "provenance": {
            "policy_id": str(policy.get("policy_id", "explicit")),
            "policy_digest": _stable_digest(policy),
            "t01_fingerprint": (
                str(policy.get("t01_artifact", {}).get("fingerprint", ""))
                if isinstance(policy.get("t01_artifact", {}), Mapping)
                else ""
            ),
            "references": reference_provenance,
            "source_lock": source_lock_provenance,
            "disassembler": disassembler_provenance,
            "privacy": "ROM observations are SHA-256 digests only",
            "variant_replays": [
                {
                    key: value
                    for key, value in summary.items()
                    if key
                    in {
                        "engine", "profile", "input_sha256", "output_sha256",
                        "output_bin_sha256", "offsets_sha256", "replay_sha256",
                        "special_inserts", "source_identity", "profile_overlay",
                    }
                }
                for summary in variant_summaries
            ],
        },
        "writes": all_rows,
        "summaries": {
            "write_count": len(all_rows),
            "same_value_write_count": sum(bool(row["same_value_write"]) for row in all_rows),
            "overlap_row_count": sum(bool(row["overlaps"]) for row in all_rows),
            "overlap_pair_count": sum(len(row["overlaps"]) for row in all_rows) // 2,
            "allowed_overlap_pair_count": len(allowed_overlaps),
            "allowed_cross_engine_overlap_pair_count": len(cross_engine_overlaps),
            "source_kind_counts": dict(sorted(kinds.items())),
            "classification_counts": dict(sorted(classes.items())),
            "variants": variant_summaries,
            "representative_code_disassembly": representative_disassembly,
        },
    }
    # Serializationそのものを行い、bytesや非決定型が漏れていないことを完了前に確認。
    json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return model


def build_source_write_model(root: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    """公開API。入力/環境起因の失敗をValueError/RuntimeErrorへ正規化する。"""

    try:
        return _build_source_write_model(root, policy)
    except (ValueError, RuntimeError):
        raise
    except Exception as error:
        raise ValueError(f"source write model入力/構造が不正です: {error}") from error


def _write_model(path: Path, model: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T02 exact fixed-source write model generator")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    policy_path = args.policy if args.policy.is_absolute() else root / args.policy
    output_path = args.output if args.output.is_absolute() else root / args.output
    policy = _read_json(policy_path, "T02 policy")
    model = build_source_write_model(root, policy)
    _write_model(output_path, model)
    # stdoutは件数とmodel digestだけ。ROM path/byte/digestすら表示しない。
    print(
        json.dumps(
            {
                "status": "PASS",
                "write_count": model["summaries"]["write_count"],
                "model_sha256": _stable_digest(model),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
