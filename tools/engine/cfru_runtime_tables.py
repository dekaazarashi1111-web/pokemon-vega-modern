#!/usr/bin/env python3
"""T04/T05 の意味モデルを CFRU runtime ABI 用の資産へ描画する。

このモジュールはファイルを書き込まない。``build_runtime_assets`` は、固定長表、
可変長文字列 blob、pointer relocation、CFRU source table からの row-copy recipe を
返す。SOURCE_SYMBOL の値は link 前には確定しないため、``offsets=None`` では明示的な
relocation として残し、``resolve_runtime_assets``（または ``offsets`` 付き build）で
全 relocation を fail-closed に解決する。
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


MOVE_COUNT = 1063
MOVE_STRIDE = 12
MOVE_NAME_STRIDE = 16
ABILITY_COUNT = 312
ABILITY_NAME_STRIDE = 17
ITEM_COUNT = 999
ITEM_STRIDE = 40
ITEM_ICON_STRIDE = 8

_MOVE_FIELDS = (
    "effect",
    "power",
    "type",
    "accuracy",
    "pp",
    "secondary",
    "target",
    "priority",
    "flags",
    "z_move_power",
    "split",
    "z_move_effect",
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_ROM_MIN = 0x08000000
_ROM_MAX = 0x09FFFFFF


class CFRURuntimeTableError(ValueError):
    """runtime table の入力契約または ABI が一致しない。"""


def _fail(message: str) -> NoReturn:
    raise CFRURuntimeTableError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _stable_digest(value: object) -> str:
    return _sha256(_stable_bytes(value))


def _public_value(value: object) -> object:
    """build-time private bytes/charmap を除外して入力モデルを安定hash化する。"""

    if isinstance(value, Mapping):
        return {
            str(key): _public_value(child)
            for key, child in value.items()
            if not str(key).startswith("_")
        }
    if isinstance(value, (list, tuple)):
        return [_public_value(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    _fail(f"model contains a non-JSON value: {type(value).__name__}")


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be an object")
    return value


def _rows(value: object, label: str, count: int) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, (list, tuple)) or len(value) != count:
        _fail(f"{label} must contain exactly {count} rows")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            _fail(f"{label}[{index}] must be an object")
        rows.append(row)
    return rows


def _integer(value: object, label: str, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
        _fail(f"{label} must be an integer in {lower}..{upper}")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be a non-empty string")
    return value


def _hex_bytes(value: object, label: str) -> bytes:
    if not isinstance(value, str) or len(value) % 2:
        _fail(f"{label} must be an even-length hex string")
    try:
        return bytes.fromhex(value)
    except ValueError:
        _fail(f"{label} must be an even-length hex string")


def _trim_terminated(raw: bytes, label: str) -> bytes:
    try:
        end = raw.index(0xFF)
    except ValueError:
        _fail(f"{label} lacks the 0xFF game-text terminator")
    return raw[: end + 1]


def _safe_relative(root: Path, logical: object, label: str) -> Path:
    if not isinstance(logical, str) or not logical or Path(logical).is_absolute():
        _fail(f"{label} must be a non-empty relative path")
    resolved_root = root.resolve()
    path = (resolved_root / logical).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        _fail(f"{label} escapes repository root")
    if path.is_symlink() or not path.is_file():
        _fail(f"{label} is missing/non-regular: {logical}")
    return path


def _file_with_hash(root: Path, logical: object, expected: object, label: str) -> bytes:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        _fail(f"{label} SHA-256 is invalid")
    raw = _safe_relative(root, logical, label).read_bytes()
    actual = _sha256(raw)
    if actual != expected:
        _fail(f"{label} SHA-256 mismatch: {actual} != {expected}")
    return raw


def _read_charmap(
    root: Path, id_model: Mapping[str, Any]
) -> tuple[dict[str, int], dict[int, str], list[str], str]:
    sources = _mapping(id_model.get("sources"), "T05.sources")
    vega = _mapping(sources.get("vega"), "T05.sources.vega")
    provenance = _mapping(vega.get("charmap"), "T05.sources.vega.charmap")
    raw = _file_with_hash(
        root,
        provenance.get("logical_path"),
        provenance.get("sha256"),
        "fixed CFRU-JP charmap",
    )
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        _fail(f"fixed charmap is not UTF-8: {error}")
    encode: dict[str, int] = {}
    decode: dict[int, str] = {}
    for number, line in enumerate(lines, 1):
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            byte = int(line[:2], 16)
        except ValueError:
            _fail(f"fixed charmap has an invalid byte on line {number}")
        token = line[3:]
        # CFRU-JP は一部byteにASCII記号と和文記号のaliasを持つ。encoderでは
        # 両方を受理し、decoderの表示名は上流と同じく後勝ちにする。
        decode[byte] = token
        if token != "$":
            encode.setdefault(token, byte)
    if decode.get(0xFF) != "$" or decode.get(0xFE) != r"\n":
        _fail("fixed charmap terminator/newline ABI mismatch")
    tokens = sorted((token for token in encode if token), key=lambda token: (-len(token), token))
    return encode, decode, tokens, _sha256(raw)


def _game_text_input(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\n")


def _encode_game_text(text: object, mapping: Mapping[str, int], tokens: Sequence[str], label: str) -> bytes:
    if not isinstance(text, str):
        _fail(f"{label} must be text")
    normalized = _game_text_input(text)
    output = bytearray()
    index = 0
    while index < len(normalized):
        for token in tokens:
            if normalized.startswith(token, index):
                output.append(mapping[token])
                index += len(token)
                break
        else:
            _fail(f"{label} is not encodable at {normalized[index:]!r}")
    return bytes(output)


def _decode_game_text(raw: bytes, reverse: Mapping[int, str], label: str) -> str:
    output: list[str] = []
    for byte in _trim_terminated(raw, label)[:-1]:
        token = reverse.get(byte)
        if token is None or token == "$":
            _fail(f"{label} contains unmapped byte 0x{byte:02X}")
        output.append(token)
    return "".join(output)


def _fixed_game_name(
    text: object,
    stride: int,
    mapping: Mapping[str, int],
    reverse: Mapping[int, str],
    tokens: Sequence[str],
    label: str,
) -> bytes:
    encoded = _encode_game_text(text, mapping, tokens, label)
    if len(encoded) > stride - 1:
        _fail(f"{label} exceeds {stride - 1} encoded bytes")
    raw = encoded + bytes([0xFF]) * (stride - len(encoded))
    if _decode_game_text(raw, reverse, label) != _game_text_input(str(text)):
        _fail(f"{label} failed charmap round-trip")
    return raw


def _validate_inputs(
    root: Path, move_model: Mapping[str, Any], id_model: Mapping[str, Any]
) -> tuple[
    Sequence[Mapping[str, Any]],
    Sequence[Mapping[str, Any]],
    Sequence[Mapping[str, Any]],
]:
    if not isinstance(root, Path) or not root.resolve().is_dir():
        _fail("root must be an existing repository Path")
    if not isinstance(move_model, Mapping) or not isinstance(id_model, Mapping):
        _fail("move_model and id_model must be mappings")

    if move_model.get("schema_version") != 1 or move_model.get("task") != "T04":
        _fail("T04 move model schema/task mismatch")
    moves = _rows(move_model.get("moves"), "T04.moves", MOVE_COUNT)
    if [row.get("id") for row in moves] != list(range(MOVE_COUNT)):
        _fail("T04 canonical move IDs must be contiguous 0..1062")
    summary = _mapping(move_model.get("summary"), "T04.summary")
    if (
        summary.get("move_count") != MOVE_COUNT
        or summary.get("frozen_count") != 512
        or summary.get("appended_count") != 551
        or summary.get("cfru_alias_count") != 992
        or [row.get("vega_id") for row in moves[:512]] != list(range(512))
        or any(row.get("vega_id") is not None for row in moves[512:])
    ):
        _fail("T04 move range/count contract changed")
    move_keys = [row.get("move_key") for row in moves]
    if (
        len(set(move_keys)) != MOVE_COUNT
        or any(not isinstance(key, str) or not key.startswith("MOVE_KEY_") for key in move_keys)
        or sum(row.get("classification") == "CFRU_APPEND" for row in moves) != 551
        or sum(row.get("classification") == "VEGA_EXCLUSIVE_V3" for row in moves) != 70
        or sum(row.get("classification") == "VEGA_COMPAT_DUPLICATE" for row in moves) != 1
    ):
        _fail("T04 move key/classification contract changed")
    move_aliases = _rows(move_model.get("aliases"), "T04.aliases", 992)
    if (
        [row.get("cfru_source_id") for row in move_aliases] != list(range(992))
        or len({row.get("cfru_symbol") for row in move_aliases}) != 992
        or any(
            not isinstance(row.get("canonical_id"), int)
            or not 0 <= row["canonical_id"] < MOVE_COUNT
            or move_keys[row["canonical_id"]] != row.get("canonical_key")
            for row in move_aliases
        )
    ):
        _fail("T04 CFRU move alias contract changed")

    if id_model.get("schema_version") != 1 or id_model.get("task") != "T05":
        _fail("T05 ID model schema/task mismatch")
    if id_model.get("activation_task") != "T06":
        _fail("T05 activation task must remain T06")
    abilities = _rows(id_model.get("abilities"), "T05.abilities", ABILITY_COUNT)
    items = _rows(id_model.get("items"), "T05.items", ITEM_COUNT)
    if [row.get("id") for row in abilities] != list(range(ABILITY_COUNT)):
        _fail("T05 canonical ability IDs must be contiguous 0..311")
    if [row.get("id") for row in items] != list(range(ITEM_COUNT)):
        _fail("T05 canonical item IDs must be contiguous 0..998")
    id_summary = _mapping(id_model.get("summary"), "T05.summary")
    if (
        id_summary.get("ability_count") != ABILITY_COUNT
        or id_summary.get("item_count") != ITEM_COUNT
        or id_summary.get("frozen_ability_count") != 78
        or id_summary.get("frozen_item_count") != 375
        or id_summary.get("cfru_appended_item_count") != 613
        or id_summary.get("qol_appended_item_count") != 11
    ):
        _fail("T05 ability/item range contract changed")

    fingerprint_inputs = _mapping(id_model.get("fingerprint_inputs"), "T05.fingerprint_inputs")
    if id_model.get("fingerprint") != _stable_digest(fingerprint_inputs):
        _fail("T05 fingerprint is not self-consistent")
    handoff = _mapping(id_model.get("runtime_handoff"), "T05.runtime_handoff")
    rebuilds = handoff.get("canonical_rebuilds")
    expected_rebuilds = {
        ("ITEM_DATA", 774, ITEM_COUNT, "struct Item"),
        ("ITEM_GRAPHICS", 774, ITEM_COUNT, "struct ItemIconTemplate"),
        ("ABILITY_NAMES", 311, ABILITY_COUNT, "game_charmap_strings"),
        ("ABILITY_DESCRIPTIONS", 311, ABILITY_COUNT, "game_charmap_strings"),
    }
    observed_rebuilds = {
        (
            row.get("table_key"),
            row.get("source_rows"),
            row.get("canonical_rows"),
            row.get("runtime_abi"),
        )
        for row in rebuilds
        if isinstance(rebuilds, (list, tuple)) and isinstance(row, Mapping)
    } if isinstance(rebuilds, (list, tuple)) else set()
    expected_gates = {
        "REBUILD_CANONICAL_POSITIONAL_TABLES",
        "REPOINT_ALL_RUNTIME_CONSUMERS",
        "ROUND_TRIP_ALL_CANONICAL_ROWS",
        "REJECT_SOURCE_ID_DIRECT_INDEXING",
        "KEEP_ITEM_OBTAINED_FLAGS_DISABLED_UNTIL_T08_RESIZE_OR_TRANSLATION",
    }
    if (
        handoff.get("task") != "T06"
        or handoff.get("semantic_tables_are_runtime_abi") is not False
        or observed_rebuilds != expected_rebuilds
        or set(handoff.get("hard_gates", [])) != expected_gates
    ):
        _fail("T05 positional runtime handoff contract changed")

    if any(row.get("vega_id") != index or row.get("vega_raw") is None for index, row in enumerate(items[:375])):
        _fail("T05 item rows 0..374 must be Vega raw rows")
    if any(
        not isinstance(row.get("cfru_id"), int)
        or row.get("cfru_source") is None
        or row.get("vega_raw") is not None
        for row in items[375:988]
    ):
        _fail("T05 item rows 375..987 must be CFRU source rows")
    if any(
        row.get("classification") != "QOL_APPEND"
        or row.get("cfru_id") is not None
        or row.get("vega_id") is not None
        for row in items[988:]
    ):
        _fail("T05 item rows 988..998 must be QOL rows")
    if any(row.get("vega_id") != index or row.get("vega_raw") is None for index, row in enumerate(abilities[:78])):
        _fail("T05 ability rows 0..77 must be Vega frozen rows")
    if any(
        row.get("classification") != "CFRU_APPEND"
        or not isinstance(row.get("cfru_id"), int)
        or row.get("vega_raw") is not None
        for row in abilities[78:]
    ):
        _fail("T05 ability rows 78..311 must be CFRU source rows")
    ability_aliases = _rows(
        id_model.get("ability_aliases"), "T05.ability_aliases", 311
    )
    if [row.get("source_id") for row in ability_aliases] != list(range(311)):
        _fail("T05 ability aliases must be source-ID ordered")
    for alias in ability_aliases:
        canonical_id = alias.get("canonical_id")
        if (
            not isinstance(canonical_id, int)
            or not 0 <= canonical_id < ABILITY_COUNT
            or abilities[canonical_id].get("ability_key") != alias.get("ability_key")
            or abilities[canonical_id].get("cfru_id") != alias.get("source_id")
            or abilities[canonical_id].get("cfru_symbol") != alias.get("source_symbol")
        ):
            _fail("T05 ability alias points outside the canonical mapping")
    item_aliases = _rows(id_model.get("item_aliases"), "T05.item_aliases", 827)
    source_ids = {row.get("source_id") for row in item_aliases}
    if source_ids != set(range(774)) or len({row.get("source_symbol") for row in item_aliases}) != 827:
        _fail("T05 item alias source coverage changed")
    for alias in item_aliases:
        canonical_id = alias.get("canonical_id")
        if (
            not isinstance(canonical_id, int)
            or not 0 <= canonical_id < ITEM_COUNT
            or items[canonical_id].get("item_key") != alias.get("item_key")
            or items[canonical_id].get("cfru_id") != alias.get("source_id")
        ):
            _fail("T05 item alias points outside the canonical mapping")

    sources = _mapping(id_model.get("sources"), "T05.sources")
    cfru_dpe = _mapping(sources.get("cfru_dpe"), "T05.sources.cfru_dpe")
    source_lock = _mapping(cfru_dpe.get("source_lock"), "T05 CFRU source_lock")
    _file_with_hash(
        root,
        source_lock.get("path"),
        source_lock.get("sha256"),
        "fixed source-lock",
    )
    source_sets = _mapping(cfru_dpe.get("sources"), "T05 CFRU source sets")
    cfru = _mapping(source_sets.get("cfru"), "T05 CFRU source")
    cfru_path = _string(cfru.get("path"), "T05 CFRU source.path")
    files = _mapping(cfru.get("files"), "T05 CFRU source.files")
    for logical, expected_hash in sorted(files.items()):
        if not isinstance(logical, str):
            _fail("T05 CFRU source file key must be text")
        _file_with_hash(root, f"{cfru_path.rstrip('/')}/{logical}", expected_hash, f"fixed CFRU source {logical}")

    move_provenance = _mapping(move_model.get("provenance"), "T04.provenance")
    vega_meta = _mapping(sources.get("vega"), "T05.sources.vega")
    vega_rom = _mapping(vega_meta.get("rom"), "T05.sources.vega.rom")
    if move_provenance.get("vega_rom_sha256") != vega_rom.get("sha256"):
        _fail("T04/T05 Vega ROM provenance differs")
    if move_provenance.get("cfru_commit") != cfru.get("commit"):
        _fail("T04/T05 CFRU commit provenance differs")
    return moves, abilities, items


def _pack_move_rows(moves: Sequence[Mapping[str, Any]]) -> bytes:
    output = bytearray()
    for index, row in enumerate(moves):
        battle = _mapping(row.get("battle"), f"move {index}.battle")
        if set(battle) != set(_MOVE_FIELDS):
            _fail(f"move {index}.battle schema differs")
        values = [
            _integer(battle[field], f"move {index}.{field}", -128 if field == "priority" else 0, 127 if field == "priority" else 255)
            for field in _MOVE_FIELDS
        ]
        packed = struct.pack("<7Bb4B", *values)
        decoded = struct.unpack("<7Bb4B", packed)
        if tuple(values) != decoded:
            _fail(f"move {index} failed 12-byte ABI round-trip")
        output.extend(packed)
    if len(output) != MOVE_COUNT * MOVE_STRIDE:
        _fail("gBattleMoves size mismatch")
    return bytes(output)


def _pack_names(
    rows: Sequence[Mapping[str, Any]],
    field: str,
    stride: int,
    mapping: Mapping[str, int],
    reverse: Mapping[int, str],
    tokens: Sequence[str],
    label: str,
) -> bytes:
    output = bytearray()
    for index, row in enumerate(rows):
        fixed = _fixed_game_name(
            row.get(field), stride, mapping, reverse, tokens, f"{label} {index}"
        )
        if label == "ability name" and index < 78:
            vega = _mapping(row.get("vega_raw"), f"ability {index}.vega_raw")
            frozen = _trim_terminated(
                _hex_bytes(vega.get("name_raw"), f"ability {index}.vega_raw.name_raw"),
                f"ability {index} frozen name",
            )
            if frozen != _trim_terminated(fixed, f"ability {index} canonical name"):
                _fail(f"ability {index} frozen name bytes changed")
        output.extend(fixed)
    if len(output) != len(rows) * stride:
        _fail(f"{label} table size mismatch")
    return bytes(output)


def _description_assets(
    rows: Sequence[Mapping[str, Any]],
    *,
    text_getter: Any,
    raw_getter: Any,
    mapping: Mapping[str, int],
    reverse: Mapping[int, str],
    tokens: Sequence[str],
    label: str,
) -> tuple[bytes, bytes, list[int]]:
    blob = bytearray()
    offsets: list[int] = []
    for index, row in enumerate(rows):
        offsets.append(len(blob))
        text = text_getter(row)
        raw_value = raw_getter(row)
        if raw_value is None:
            raw = _encode_game_text(text, mapping, tokens, f"{label} {index}") + b"\xFF"
        else:
            raw = _trim_terminated(_hex_bytes(raw_value, f"{label} {index} raw"), f"{label} {index}")
        expected = _encode_game_text(text, mapping, tokens, f"{label} {index}") + b"\xFF"
        if raw != expected:
            _fail(f"{label} {index} text/raw bytes differ")
        if _decode_game_text(raw, reverse, f"{label} {index}") != _game_text_input(str(text)):
            _fail(f"{label} {index} failed charmap round-trip")
        blob.extend(raw)
    offsets_bytes = b"".join(struct.pack("<I", offset) for offset in offsets)
    for index, offset in enumerate(offsets):
        end = offsets[index + 1] if index + 1 < len(offsets) else len(blob)
        if offset >= end or blob[end - 1] != 0xFF:
            _fail(f"{label} {index} blob boundary mismatch")
    return bytes(blob), offsets_bytes, offsets


def _rom_pointer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not _ROM_MIN <= value <= _ROM_MAX:
        _fail(f"{label} must be a GBA ROM pointer")
    return value


def _animation_assets(
    moves: Sequence[Mapping[str, Any]], relocations: list[dict[str, Any]]
) -> tuple[bytes, list[dict[str, Any]], list[tuple[int | None, str | None, int]]]:
    table = bytearray(MOVE_COUNT * 4)
    recipes: list[dict[str, Any]] = []
    assembly_rows: list[tuple[int | None, str | None, int]] = []
    for index, row in enumerate(moves):
        animation = _mapping(row.get("animation"), f"move {index}.animation")
        kind = animation.get("mapping_kind")
        symbol = animation.get("symbol")
        vega_pointer = animation.get("vega_pointer")
        if kind == "VEGA_ROM_POINTER":
            pointer = _rom_pointer(vega_pointer, f"move {index} Vega animation")
            if symbol is not None:
                _fail(f"move {index} Vega animation unexpectedly has a symbol")
            struct.pack_into("<I", table, index * 4, pointer)
            recipe = {"id": index, "kind": "VEGA_RAW_POINTER", "value": pointer}
            assembly_rows.append((pointer, None, 0))
        elif kind == "EXTERNAL_ROM_POINTER":
            if vega_pointer != 0 or not isinstance(symbol, str):
                _fail(f"move {index} external animation recipe is invalid")
            try:
                pointer = int(symbol, 0)
            except ValueError:
                _fail(f"move {index} external animation is not a raw pointer")
            pointer = _rom_pointer(pointer, f"move {index} external animation")
            struct.pack_into("<I", table, index * 4, pointer)
            recipe = {"id": index, "kind": "RAW_POINTER", "value": pointer}
            assembly_rows.append((pointer, None, 0))
        elif kind == "SOURCE_SYMBOL":
            if vega_pointer != 0 or not isinstance(symbol, str) or not _IDENTIFIER.fullmatch(symbol):
                _fail(f"move {index} source animation symbol is invalid")
            relocation = {
                "table": "gMoveAnimations",
                "offset": index * 4,
                "width": 4,
                "kind": "ABS32",
                "symbol": symbol,
                "addend": 0,
                "domain": "MOVE_ANIMATION",
                "row": index,
            }
            relocations.append(relocation)
            recipe = {"id": index, "kind": "SOURCE_SYMBOL", "symbol": symbol}
            assembly_rows.append((None, symbol, 0))
        else:
            _fail(f"move {index} has unknown animation mapping kind: {kind!r}")
        recipes.append(recipe)
    return bytes(table), recipes, assembly_rows


def _pointer_placeholder(
    table_name: str,
    blob_symbol: str,
    offsets: Sequence[int],
    domain: str,
    relocations: list[dict[str, Any]],
) -> tuple[bytes, list[tuple[int | None, str | None, int]]]:
    rows: list[tuple[int | None, str | None, int]] = []
    for index, addend in enumerate(offsets):
        relocations.append(
            {
                "table": table_name,
                "offset": index * 4,
                "width": 4,
                "kind": "ABS32",
                "symbol": blob_symbol,
                "addend": addend,
                "domain": domain,
                "row": index,
            }
        )
        rows.append((None, blob_symbol, addend))
    return bytes(len(offsets) * 4), rows


_POCKET_VALUES = {
    "POCKET_ITEMS": 1,
    "POCKET_KEY_ITEMS": 2,
    "POCKET_POKE_BALLS": 3,
    "POCKET_TM_CASE": 4,
    "POCKET_BERRIES": 5,
}
_USE_TYPE_VALUES = {
    "ITEM_USE_MAIL": 0,
    "ITEM_USE_PARTY_MENU": 1,
    "ITEM_USE_FIELD": 2,
    "ITEM_USE_PBLOCK_CASE": 3,
    "ITEM_USE_BAG_MENU": 4,
    "ITEM_USE_PARTY_MENU_MOVES": 5,
}


def _qol_item_row(
    row: Mapping[str, Any],
    mapping: Mapping[str, int],
    reverse: Mapping[int, str],
    tokens: Sequence[str],
) -> bytes:
    item_id = _integer(row.get("id"), "QOL item id", 988, 998)
    name = _fixed_game_name(
        row.get("display_name"), 10, mapping, reverse, tokens, f"QOL item {item_id} name"
    )
    if row.get("hold_effect_key") != "NONE" or str(row.get("hold_effect_param")) != "0":
        _fail(f"QOL item {item_id} has an unresolved hold effect")
    pocket_symbol = row.get("pocket")
    use_symbol = row.get("source_use_type")
    if pocket_symbol not in _POCKET_VALUES or use_symbol not in _USE_TYPE_VALUES:
        _fail(f"QOL item {item_id} pocket/use type is unresolved")
    price = _integer(row.get("price"), f"QOL item {item_id}.price", 0, 0xFFFF)
    importance = _integer(row.get("importance"), f"QOL item {item_id}.importance", 0, 0xFF)
    mystery = _integer(row.get("source_mystery"), f"QOL item {item_id}.source_mystery", 0, 0xFF)
    battle_usage = _integer(row.get("battle_usage"), f"QOL item {item_id}.battle_usage", 0, 0xFF)
    secondary = _integer(row.get("secondary_id"), f"QOL item {item_id}.secondary_id", 0, 0xFF)
    packed = struct.pack(
        "<10sHHBBIBBBBIB3xIB3x",
        name,
        item_id,
        price,
        0,
        0,
        0,
        importance,
        mystery,
        _POCKET_VALUES[str(pocket_symbol)],
        _USE_TYPE_VALUES[str(use_symbol)],
        0,
        battle_usage,
        0,
        secondary,
    )
    if len(packed) != ITEM_STRIDE or struct.unpack_from("<H", packed, 10)[0] != item_id:
        _fail(f"QOL item {item_id} failed struct Item round-trip")
    if packed[29:32] != b"\0\0\0" or packed[37:40] != b"\0\0\0":
        _fail(f"QOL item {item_id} ABI padding differs")
    return packed


def _item_assets(
    items: Sequence[Mapping[str, Any]],
    mapping: Mapping[str, int],
    reverse: Mapping[int, str],
    tokens: Sequence[str],
    relocations: list[dict[str, Any]],
) -> tuple[bytes, bytes, bytes, bytes, list[dict[str, Any]], list[dict[str, Any]]]:
    item_table = bytearray(ITEM_COUNT * ITEM_STRIDE)
    icon_table = bytearray(ITEM_COUNT * ITEM_ICON_STRIDE)
    item_recipes: list[dict[str, Any]] = []
    icon_recipes: list[dict[str, Any]] = []
    qol_blob = bytearray()
    qol_offsets: list[int] = []
    cfru_icon_pairs: dict[tuple[str, str], set[int]] = {}
    for source_row in items:
        source_value = source_row.get("cfru_source")
        if not isinstance(source_value, Mapping):
            continue
        icon_symbol = source_value.get("icon_symbol")
        palette_symbol = source_value.get("palette_symbol")
        source_id = source_value.get("id")
        if (
            isinstance(icon_symbol, str)
            and isinstance(palette_symbol, str)
            and isinstance(source_id, int)
            and not isinstance(source_id, bool)
        ):
            cfru_icon_pairs.setdefault((icon_symbol, palette_symbol), set()).add(source_id)

    for index, row in enumerate(items):
        destination = index * ITEM_STRIDE
        icon_destination = index * ITEM_ICON_STRIDE
        if index < 375:
            vega = _mapping(row.get("vega_raw"), f"item {index}.vega_raw")
            raw = _hex_bytes(vega.get("raw_hex"), f"item {index}.vega_raw.raw_hex")
            icon = _hex_bytes(
                vega.get("icon_entry_raw"), f"item {index}.vega_raw.icon_entry_raw"
            )
            if len(raw) != ITEM_STRIDE or len(icon) != ITEM_ICON_STRIDE:
                _fail(f"item {index} frozen ABI size differs")
            embedded_id = struct.unpack_from("<H", raw, 10)[0]
            if embedded_id not in (0, index):
                _fail(f"item {index} frozen row has unexpected itemId {embedded_id}")
            if raw[29:32] != b"\0\0\0" or raw[37:40] != b"\0\0\0":
                _fail(f"item {index} frozen ABI padding differs")
            item_table[destination : destination + ITEM_STRIDE] = raw
            icon_table[icon_destination : icon_destination + ITEM_ICON_STRIDE] = icon
            item_recipes.append(
                {
                    "id": index,
                    "kind": "VEGA_RAW_ROW",
                    "destination_offset": destination,
                    "raw_sha256": _sha256(raw),
                }
            )
            icon_recipes.append(
                {
                    "id": index,
                    "kind": "VEGA_RAW_ROW",
                    "destination_offset": icon_destination,
                    "raw_sha256": _sha256(icon),
                }
            )
        elif index < 988:
            source_id = _integer(row.get("cfru_id"), f"item {index}.cfru_id", 0, 773)
            source = _mapping(row.get("cfru_source"), f"item {index}.cfru_source")
            if source.get("id") != source_id:
                _fail(f"item {index} CFRU source row/index differs")
            reserved = row.get("classification") == "CFRU_RESERVED"
            item_recipes.append(
                {
                    "id": index,
                    "kind": "CFRU_SOURCE_ROW_COPY",
                    "destination_offset": destination,
                    "source_table_key": "CFRU_ITEM_DATA",
                    "source_index": source_id,
                    "source_stride": ITEM_STRIDE,
                    "copy_size": ITEM_STRIDE,
                    "post_copy_patches": [
                        {
                            "offset": 10,
                            "width": 2,
                            "kind": "U16_LE",
                            "value": 0 if reserved else index,
                        }
                    ],
                    "source_semantic_sha256": _stable_digest(source),
                    "reserved": reserved,
                }
            )
            icon_recipes.append(
                {
                    "id": index,
                    "kind": "CFRU_SOURCE_ROW_COPY",
                    "destination_offset": icon_destination,
                    "source_table_key": "CFRU_ITEM_GRAPHICS",
                    "source_index": source_id,
                    "source_stride": ITEM_ICON_STRIDE,
                    "copy_size": ITEM_ICON_STRIDE,
                    "source_semantic_sha256": _stable_digest(
                        {
                            "icon_symbol": source.get("icon_symbol"),
                            "palette_symbol": source.get("palette_symbol"),
                            "icon_rom_address": source.get("icon_rom_address"),
                            "palette_rom_address": source.get("palette_rom_address"),
                        }
                    ),
                }
            )
        else:
            packed = _qol_item_row(row, mapping, reverse, tokens)
            item_table[destination : destination + ITEM_STRIDE] = packed
            description_offset = len(qol_blob)
            description = _encode_game_text(
                row.get("description"), mapping, tokens, f"QOL item {index} description"
            ) + b"\xFF"
            if _decode_game_text(description, reverse, f"QOL item {index} description") != _game_text_input(str(row.get("description"))):
                _fail(f"QOL item {index} description failed round-trip")
            qol_offsets.append(description_offset)
            qol_blob.extend(description)
            relocations.append(
                {
                    "table": "gItemData",
                    "offset": destination + 16,
                    "width": 4,
                    "kind": "ABS32",
                    "symbol": "gQolItemDescriptionBlob",
                    "addend": description_offset,
                    "domain": "QOL_ITEM_DESCRIPTION",
                    "row": index,
                }
            )
            field_callback = row.get("field_use_callback_key")
            battle_callback = row.get("battle_use_callback_key")
            for field_offset, symbol, domain in (
                (24, field_callback, "QOL_ITEM_FIELD_CALLBACK"),
                (32, battle_callback, "QOL_ITEM_BATTLE_CALLBACK"),
            ):
                if symbol != "NONE":
                    if not isinstance(symbol, str) or not _IDENTIFIER.fullmatch(symbol):
                        _fail(f"QOL item {index} has invalid callback symbol {symbol!r}")
                    relocations.append(
                        {
                            "table": "gItemData",
                            "offset": destination + field_offset,
                            "width": 4,
                            "kind": "THUMB32",
                            "symbol": symbol,
                            "addend": 0,
                            "domain": domain,
                            "row": index,
                        }
                    )
            icon_symbol = row.get("icon_key")
            palette_symbol = row.get("palette_key")
            if not isinstance(icon_symbol, str) or not _IDENTIFIER.fullmatch(icon_symbol):
                _fail(f"QOL item {index} has invalid icon symbol {icon_symbol!r}")
            if not isinstance(palette_symbol, str) or not _IDENTIFIER.fullmatch(palette_symbol):
                _fail(f"QOL item {index} has invalid palette symbol {palette_symbol!r}")
            icon_sources = cfru_icon_pairs.get((icon_symbol, palette_symbol), set())
            if len(icon_sources) != 1:
                _fail(f"QOL item {index} icon/palette pair is not one CFRU source row")
            icon_source_id = next(iter(icon_sources))
            item_recipes.append(
                {
                    "id": index,
                    "kind": "QOL_GENERATED_ROW",
                    "destination_offset": destination,
                    "description_offset": description_offset,
                    "raw_sha256_before_relocation": _sha256(packed),
                }
            )
            icon_recipes.append(
                {
                    "id": index,
                    "kind": "CFRU_SOURCE_ROW_COPY",
                    "destination_offset": icon_destination,
                    "source_table_key": "CFRU_ITEM_GRAPHICS",
                    "source_index": icon_source_id,
                    "source_stride": ITEM_ICON_STRIDE,
                    "copy_size": ITEM_ICON_STRIDE,
                    "icon_symbol": icon_symbol,
                    "palette_symbol": palette_symbol,
                }
            )

    if [row["id"] for row in item_recipes] != list(range(ITEM_COUNT)):
        _fail("item row recipe coverage differs")
    if [row["id"] for row in icon_recipes] != list(range(ITEM_COUNT)):
        _fail("item icon recipe coverage differs")
    if [row["kind"] for row in item_recipes].count("VEGA_RAW_ROW") != 375:
        _fail("item Vega raw recipe count differs")
    if [row["kind"] for row in item_recipes].count("CFRU_SOURCE_ROW_COPY") != 613:
        _fail("item CFRU source recipe count differs")
    if [row["kind"] for row in item_recipes].count("QOL_GENERATED_ROW") != 11:
        _fail("item QOL recipe count differs")
    qol_offsets_bytes = b"".join(struct.pack("<I", value) for value in qol_offsets)
    return (
        bytes(item_table),
        bytes(icon_table),
        bytes(qol_blob),
        qol_offsets_bytes,
        item_recipes,
        icon_recipes,
    )


def _pointer_assembly(
    pointer_tables: Mapping[str, Sequence[tuple[int | None, str | None, int]]]
) -> bytes:
    lines = [
        ".section .rodata.cfru_runtime_pointers, \"a\", %progbits",
        ".balign 4",
        "/* Generated recipe source: data/blob symbols are supplied by the parent linker. */",
    ]
    for table_name, rows in pointer_tables.items():
        lines.extend((f".global {table_name}", f"{table_name}:"))
        for value, symbol, addend in rows:
            if value is not None:
                expression = f"0x{value:08X}"
            elif symbol is not None:
                expression = symbol if addend == 0 else f"{symbol} + {addend}"
            else:
                _fail(f"assembly pointer recipe for {table_name} is incomplete")
            lines.append(f"    .word {expression}")
        lines.append(".balign 4")
    lines.append("")
    return "\n".join(lines).encode("ascii")


def _header_source() -> bytes:
    return (
        "#ifndef CFRU_RUNTIME_TABLES_GENERATED_H\n"
        "#define CFRU_RUNTIME_TABLES_GENERATED_H\n"
        f"#define CFRU_RUNTIME_MOVE_COUNT {MOVE_COUNT}\n"
        f"#define CFRU_RUNTIME_MOVE_STRIDE {MOVE_STRIDE}\n"
        f"#define CFRU_RUNTIME_MOVE_NAME_STRIDE {MOVE_NAME_STRIDE}\n"
        f"#define CFRU_RUNTIME_ABILITY_COUNT {ABILITY_COUNT}\n"
        f"#define CFRU_RUNTIME_ABILITY_NAME_STRIDE {ABILITY_NAME_STRIDE}\n"
        f"#define CFRU_RUNTIME_ITEM_COUNT {ITEM_COUNT}\n"
        f"#define CFRU_RUNTIME_ITEM_STRIDE {ITEM_STRIDE}\n"
        f"#define CFRU_RUNTIME_ITEM_ICON_STRIDE {ITEM_ICON_STRIDE}\n"
        "#endif\n"
    ).encode("ascii")


def _table_layout(tables: Mapping[str, bytes]) -> dict[str, dict[str, Any]]:
    fixed = {
        "gBattleMoves": (MOVE_COUNT, MOVE_STRIDE),
        "gMoveNames": (MOVE_COUNT, MOVE_NAME_STRIDE),
        "gMoveDescriptionOffsets": (MOVE_COUNT, 4),
        "gMoveDescriptions": (MOVE_COUNT, 4),
        "gMoveAnimations": (MOVE_COUNT, 4),
        "gAbilityNames": (ABILITY_COUNT, ABILITY_NAME_STRIDE),
        "gAbilityDescriptionOffsets": (ABILITY_COUNT, 4),
        "gAbilityDescriptions": (ABILITY_COUNT, 4),
        "gItemData": (ITEM_COUNT, ITEM_STRIDE),
        "gItemGraphicsTable": (ITEM_COUNT, ITEM_ICON_STRIDE),
        "gQolItemDescriptionOffsets": (11, 4),
    }
    layout: dict[str, dict[str, Any]] = {}
    for symbol, raw in tables.items():
        count, stride = fixed.get(symbol, (None, None))
        if count is not None and len(raw) != count * stride:
            _fail(f"{symbol} byte size differs from count/stride")
        layout[symbol] = {
            "size": len(raw),
            "count": count,
            "stride": stride,
            "sha256": _sha256(raw),
        }
    return layout


def _refresh_manifest(result: dict[str, Any]) -> None:
    tables = _mapping(result.get("tables"), "runtime assets.tables")
    if any(not isinstance(value, bytes) for value in tables.values()):
        _fail("runtime tables must contain bytes only")
    metadata = dict(_mapping(result.get("metadata"), "runtime assets.metadata"))
    metadata["tables"] = _table_layout(tables)  # type: ignore[arg-type]
    metadata["manifest_sha256"] = _stable_digest(
        {
            "tables": metadata["tables"],
            "recipes_sha256": _stable_digest(result.get("recipes")),
            "patches_sha256": _stable_digest(result.get("patches")),
            "relocations_sha256": _stable_digest(result.get("relocations")),
        }
    )
    result["metadata"] = metadata


def build_runtime_assets(
    root: Path,
    move_model: Mapping,
    id_model: Mapping,
    offsets: Mapping[str, int] | None = None,
) -> dict[str, bytes | object]:
    """T04/T05 model から副作用なしで canonical runtime assets を返す。

    ``offsets`` を省略すると pointer field は zero placeholder と relocation の組で
    返る。指定時は既知link symbolを適用し、生成blob/QOL handlerなど次link待ちの
    symbolを ``metadata.unresolved_symbols`` と relocation に明示して残す。
    CFRU item/icon source row の複製は link 後 patch 用 ``patches`` として常に残る。
    """

    moves, abilities, items = _validate_inputs(root, move_model, id_model)
    encode, decode, tokens, charmap_sha256 = _read_charmap(root, id_model)
    relocations: list[dict[str, Any]] = []

    move_data = _pack_move_rows(moves)
    move_names = _pack_names(
        moves, "display_name", MOVE_NAME_STRIDE, encode, decode, tokens, "move name"
    )
    move_desc_blob, move_desc_offsets_raw, move_desc_offsets = _description_assets(
        moves,
        text_getter=lambda row: _mapping(row.get("description"), "move.description").get("text"),
        raw_getter=lambda row: _mapping(row.get("description"), "move.description").get("raw_hex"),
        mapping=encode,
        reverse=decode,
        tokens=tokens,
        label="move description",
    )
    move_desc_ptrs, move_desc_asm = _pointer_placeholder(
        "gMoveDescriptions",
        "gMoveDescriptionBlob",
        move_desc_offsets,
        "MOVE_DESCRIPTION",
        relocations,
    )
    move_animations, animation_recipes, animation_asm = _animation_assets(moves, relocations)

    ability_names = _pack_names(
        abilities,
        "display_name",
        ABILITY_NAME_STRIDE,
        encode,
        decode,
        tokens,
        "ability name",
    )
    ability_desc_blob, ability_desc_offsets_raw, ability_desc_offsets = _description_assets(
        abilities,
        text_getter=lambda row: row.get("description"),
        raw_getter=lambda row: row.get("description_raw"),
        mapping=encode,
        reverse=decode,
        tokens=tokens,
        label="ability description",
    )
    ability_desc_ptrs, ability_desc_asm = _pointer_placeholder(
        "gAbilityDescriptions",
        "gAbilityDescriptionBlob",
        ability_desc_offsets,
        "ABILITY_DESCRIPTION",
        relocations,
    )

    (
        item_data,
        item_graphics,
        qol_desc_blob,
        qol_desc_offsets,
        item_recipes,
        icon_recipes,
    ) = _item_assets(items, encode, decode, tokens, relocations)

    tables: dict[str, bytes] = {
        "gBattleMoves": move_data,
        "gMoveNames": move_names,
        "gMoveDescriptionBlob": move_desc_blob,
        "gMoveDescriptionOffsets": move_desc_offsets_raw,
        "gMoveDescriptions": move_desc_ptrs,
        "gMoveAnimations": move_animations,
        "gAbilityNames": ability_names,
        "gAbilityDescriptionBlob": ability_desc_blob,
        "gAbilityDescriptionOffsets": ability_desc_offsets_raw,
        "gAbilityDescriptions": ability_desc_ptrs,
        "gItemData": item_data,
        "gItemGraphicsTable": item_graphics,
        "gQolItemDescriptionBlob": qol_desc_blob,
        "gQolItemDescriptionOffsets": qol_desc_offsets,
    }
    pointer_tables = {
        "gMoveDescriptions": move_desc_asm,
        "gMoveAnimations": animation_asm,
        "gAbilityDescriptions": ability_desc_asm,
    }
    recipes: dict[str, object] = {
        "move_descriptions": {
            "blob_symbol": "gMoveDescriptionBlob",
            "offset_symbol": "gMoveDescriptionOffsets",
            "pointer_symbol": "gMoveDescriptions",
            "offsets": move_desc_offsets,
        },
        "move_animations": animation_recipes,
        "ability_descriptions": {
            "blob_symbol": "gAbilityDescriptionBlob",
            "offset_symbol": "gAbilityDescriptionOffsets",
            "pointer_symbol": "gAbilityDescriptions",
            "offsets": ability_desc_offsets,
        },
        "qol_item_descriptions": {
            "blob_symbol": "gQolItemDescriptionBlob",
            "offset_symbol": "gQolItemDescriptionOffsets",
            "row_ids": list(range(988, 999)),
        },
    }
    patches: dict[str, object] = {
        "source_tables": {
            "CFRU_ITEM_DATA": {
                "original_symbol": "gItemData",
                "source_symbol": "gCfruSourceItemData",
                "rows": 774,
                "stride": ITEM_STRIDE,
                "canonical_item_ids": [
                    next(
                        alias["canonical_id"]
                        for alias in id_model["item_aliases"]
                        if alias["source_id"] == source_id
                    )
                    for source_id in range(774)
                ],
                "dummy_embedded_item_ids": {"375": 0},
            },
            "CFRU_ITEM_GRAPHICS": {
                "original_symbol": "gItemGraphicsTable",
                "source_symbol": "gCfruSourceItemGraphicsTable",
                "rows": 774,
                "stride": ITEM_ICON_STRIDE,
            },
        },
        "item_rows": item_recipes,
        "item_icons": icon_recipes,
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "T06",
        "tables": tables,
        "recipes": recipes,
        "patches": patches,
        "relocations": relocations,
        "sources": {
            "runtime_pointer_tables.s": _pointer_assembly(pointer_tables),
            "runtime_tables_generated.h": _header_source(),
        },
        "metadata": {
            "input": {
                "move_model_sha256": _stable_digest(_public_value(move_model)),
                "id_model_sha256": _stable_digest(_public_value(id_model)),
                "id_fingerprint": id_model.get("fingerprint"),
                "charmap_sha256": charmap_sha256,
            },
            "domains": {
                "moves": {"count": MOVE_COUNT, "data_stride": MOVE_STRIDE, "name_stride": MOVE_NAME_STRIDE},
                "abilities": {"count": ABILITY_COUNT, "name_stride": ABILITY_NAME_STRIDE},
                "items": {"count": ITEM_COUNT, "data_stride": ITEM_STRIDE, "icon_stride": ITEM_ICON_STRIDE},
            },
            "gates": {
                "move_data_all_rows_round_trip": True,
                "move_names_all_rows_charmap_round_trip": True,
                "move_descriptions_all_rows_charmap_round_trip": True,
                "ability_names_all_rows_charmap_round_trip": True,
                "ability_descriptions_all_rows_charmap_round_trip": True,
                "item_recipe_all_rows_covered": True,
                "icon_recipe_all_rows_covered": True,
            },
            "relocation_status": "PENDING",
            "source_copy_status": "PENDING",
        },
    }
    _refresh_manifest(result)
    if offsets is not None:
        source_tables = result["patches"]["source_tables"]
        unresolved_source_tables: list[str] = []
        for source in source_tables.values():
            source_symbol = source["source_symbol"]
            value = offsets.get(source_symbol)
            if value is not None:
                source["source_address"] = _integer(
                    value, f"offsets[{source_symbol}]", _ROM_MIN, _ROM_MAX
                )
            else:
                unresolved_source_tables.append(source_symbol)
        result["metadata"]["source_copy_status"] = (
            "RESOLVED" if not unresolved_source_tables else "PENDING"
        )
        result["metadata"]["unresolved_source_tables"] = unresolved_source_tables
        return _apply_runtime_offsets(result, offsets, strict=False)
    return result


def _apply_runtime_offsets(
    assets: Mapping[str, Any], offsets: Mapping[str, int], *, strict: bool
) -> dict[str, bytes | object]:

    if not isinstance(assets, Mapping) or assets.get("schema_version") != 1 or assets.get("task") != "T06":
        _fail("runtime assets schema/task mismatch")
    if not isinstance(offsets, Mapping):
        _fail("offsets must be a symbol -> integer mapping")
    result = copy.deepcopy(dict(assets))
    tables_obj = _mapping(result.get("tables"), "runtime assets.tables")
    tables: dict[str, bytearray] = {}
    for symbol, raw in tables_obj.items():
        if not isinstance(symbol, str) or not isinstance(raw, bytes):
            _fail("runtime assets table entries must be symbol -> bytes")
        tables[symbol] = bytearray(raw)
    relocation_rows = result.get("relocations")
    if not isinstance(relocation_rows, list):
        _fail("runtime assets.relocations must be a list")
    required_symbols = {
        row.get("symbol")
        for row in relocation_rows
        if isinstance(row, Mapping) and isinstance(row.get("symbol"), str)
    }
    normalized: dict[str, int] = {}
    # offsets.ini には ``.local`` などrendererと無関係なlabelも含まれる。
    # 必須symbolだけを型検査し、それ以外は読まない。
    for symbol in required_symbols:
        if symbol in offsets:
            normalized[symbol] = _integer(
                offsets[symbol], f"offsets[{symbol}]", _ROM_MIN, _ROM_MAX
            )
    previously_resolved = {
        row.get("symbol")
        for row in relocation_rows
        if isinstance(row, Mapping)
        and isinstance(row.get("symbol"), str)
        and isinstance(row.get("resolved_value"), int)
        and not isinstance(row.get("resolved_value"), bool)
    }
    missing = sorted(
        {
            row.get("symbol")
            for row in relocation_rows
            if isinstance(row, Mapping)
            and isinstance(row.get("symbol"), str)
            and row.get("symbol") not in normalized
            and row.get("symbol") not in previously_resolved
        }
    )
    if strict and missing:
        preview = ", ".join(missing[:8])
        suffix = " ..." if len(missing) > 8 else ""
        _fail(f"unresolved relocation symbols ({len(missing)}): {preview}{suffix}")
    for index, relocation in enumerate(relocation_rows):
        if not isinstance(relocation, dict):
            _fail(f"relocation {index} must be an object")
        kind = relocation.get("kind")
        if kind not in {"ABS32", "THUMB32"} or relocation.get("width") != 4:
            _fail(f"relocation {index} has unsupported kind/width")
        table_name = relocation.get("table")
        symbol = relocation.get("symbol")
        if table_name not in tables or not isinstance(symbol, str):
            _fail(f"relocation {index} target/symbol is invalid")
        if symbol not in normalized:
            continue
        offset = _integer(relocation.get("offset"), f"relocation {index}.offset", 0, len(tables[table_name]) - 4)
        addend = _integer(relocation.get("addend"), f"relocation {index}.addend", 0, 0xFFFFFFFF)
        base_value = normalized[symbol]
        value = (base_value | 1) + addend if kind == "THUMB32" else base_value + addend
        if not _ROM_MIN <= value <= _ROM_MAX:
            _fail(f"relocation {index} resolves outside GBA ROM")
        if kind == "THUMB32" and value & 1 == 0:
            _fail(f"relocation {index} does not resolve to a Thumb pointer")
        previous_value = relocation.get("resolved_value")
        if previous_value is not None and previous_value != value:
            _fail(f"relocation {index} symbol address changed between resolution stages")
        struct.pack_into("<I", tables[table_name], offset, value)
        relocation["resolved_value"] = value
    result["tables"] = {symbol: bytes(raw) for symbol, raw in tables.items()}
    metadata = dict(_mapping(result.get("metadata"), "runtime assets.metadata"))
    metadata["relocation_status"] = (
        "RESOLVED"
        if not missing
        else "PARTIAL"
        if normalized or previously_resolved
        else "PENDING"
    )
    metadata["resolved_symbol_count"] = len(set(normalized) | previously_resolved)
    metadata["unresolved_symbol_count"] = len(missing)
    metadata["unresolved_symbols"] = missing
    result["metadata"] = metadata
    _refresh_manifest(result)
    return result


def apply_source_table_patches(
    assets: Mapping[str, Any], source_tables: Mapping[str, bytes]
) -> dict[str, bytes | object]:
    """CFRU source Item/Icon rowsをcanonical placeholderへcopyする。

    ``source_tables`` は ``CFRU_ITEM_DATA`` (774*40 bytes) と
    ``CFRU_ITEM_GRAPHICS`` (774*8 bytes) を受け取る。入力bytesもassetsも変更せず、
    canonical ``itemId`` post-patchを適用した新しいasset dictを返す。
    """

    if (
        not isinstance(assets, Mapping)
        or assets.get("schema_version") != 1
        or assets.get("task") != "T06"
    ):
        _fail("runtime assets schema/task mismatch")
    if not isinstance(source_tables, Mapping):
        _fail("source_tables must be a table-key -> bytes mapping")
    expected = {
        "CFRU_ITEM_DATA": (774, ITEM_STRIDE),
        "CFRU_ITEM_GRAPHICS": (774, ITEM_ICON_STRIDE),
    }
    if set(source_tables) != set(expected):
        _fail("source_tables must contain exactly CFRU_ITEM_DATA and CFRU_ITEM_GRAPHICS")
    checked_sources: dict[str, bytes] = {}
    for key, (count, stride) in expected.items():
        raw = source_tables[key]
        if not isinstance(raw, bytes) or len(raw) != count * stride:
            _fail(f"{key} must be exactly {count * stride} bytes")
        checked_sources[key] = raw

    patch_root_input = _mapping(assets.get("patches"), "runtime assets.patches")
    source_specs = _mapping(
        patch_root_input.get("source_tables"), "runtime assets.patches.source_tables"
    )
    item_source_spec = _mapping(
        source_specs.get("CFRU_ITEM_DATA"), "CFRU_ITEM_DATA source spec"
    )
    canonical_item_ids = item_source_spec.get("canonical_item_ids")
    if (
        not isinstance(canonical_item_ids, list)
        or len(canonical_item_ids) != 774
        or any(
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < ITEM_COUNT
            for value in canonical_item_ids
        )
    ):
        _fail("CFRU_ITEM_DATA canonical item-ID expectations differ")
    dummy_values = _mapping(
        item_source_spec.get("dummy_embedded_item_ids"),
        "CFRU_ITEM_DATA dummy embedded item IDs",
    )
    if dummy_values != {"375": 0}:
        _fail("CFRU_ITEM_DATA dummy embedded item-ID contract differs")

    # Upstream raw buildはsource ID、canonical aliasをincludeしたprototype buildは
    # canonical IDを埋め込む。両者だけを許し、既知dummy row 375は0も許す。
    source_items = checked_sources["CFRU_ITEM_DATA"]
    for source_id in range(774):
        row = source_items[source_id * ITEM_STRIDE : (source_id + 1) * ITEM_STRIDE]
        embedded_id = struct.unpack_from("<H", row, 10)[0]
        allowed_ids = (
            {dummy_values[str(source_id)]}
            if str(source_id) in dummy_values
            else {source_id, canonical_item_ids[source_id]}
        )
        if embedded_id not in allowed_ids:
            _fail(
                f"CFRU_ITEM_DATA row {source_id} carries itemId {embedded_id}, "
                f"expected one of {sorted(allowed_ids)}"
            )
        if row[29:32] != b"\0\0\0" or row[37:40] != b"\0\0\0":
            _fail(f"CFRU_ITEM_DATA row {source_id} ABI padding differs")

    result = copy.deepcopy(dict(assets))
    table_values = _mapping(result.get("tables"), "runtime assets.tables")
    tables: dict[str, bytearray] = {}
    for symbol, raw in table_values.items():
        if not isinstance(symbol, str) or not isinstance(raw, bytes):
            _fail("runtime assets table entries must be symbol -> bytes")
        tables[symbol] = bytearray(raw)
    patch_root = _mapping(result.get("patches"), "runtime assets.patches")
    groups = (
        ("item_rows", "gItemData"),
        ("item_icons", "gItemGraphicsTable"),
    )
    applied = 0
    for group_name, target_symbol in groups:
        recipes = patch_root.get(group_name)
        if not isinstance(recipes, list) or len(recipes) != ITEM_COUNT:
            _fail(f"runtime assets.patches.{group_name} must contain {ITEM_COUNT} rows")
        if target_symbol not in tables:
            _fail(f"runtime assets lacks target table {target_symbol}")
        target = tables[target_symbol]
        for recipe_index, recipe in enumerate(recipes):
            if not isinstance(recipe, Mapping) or recipe.get("id") != recipe_index:
                _fail(f"{group_name} recipe ordering differs at row {recipe_index}")
            if recipe.get("kind") != "CFRU_SOURCE_ROW_COPY":
                continue
            source_key = recipe.get("source_table_key")
            if source_key not in checked_sources:
                _fail(f"{group_name} row {recipe_index} source table is unknown")
            source_stride = _integer(
                recipe.get("source_stride"),
                f"{group_name} row {recipe_index}.source_stride",
                1,
                ITEM_STRIDE,
            )
            if source_stride != expected[source_key][1]:
                _fail(f"{group_name} row {recipe_index} source stride differs")
            copy_size = _integer(
                recipe.get("copy_size"),
                f"{group_name} row {recipe_index}.copy_size",
                1,
                source_stride,
            )
            if copy_size != source_stride:
                _fail(f"{group_name} row {recipe_index} partial row copy is forbidden")
            source_index = _integer(
                recipe.get("source_index"),
                f"{group_name} row {recipe_index}.source_index",
                0,
                expected[source_key][0] - 1,
            )
            destination = _integer(
                recipe.get("destination_offset"),
                f"{group_name} row {recipe_index}.destination_offset",
                0,
                len(target) - copy_size,
            )
            if destination != recipe_index * copy_size:
                _fail(f"{group_name} row {recipe_index} destination is noncanonical")
            source_offset = source_index * source_stride
            target[destination : destination + copy_size] = checked_sources[source_key][
                source_offset : source_offset + copy_size
            ]
            post_patches = recipe.get("post_copy_patches", [])
            if not isinstance(post_patches, list):
                _fail(f"{group_name} row {recipe_index} post patches must be a list")
            for patch_index, patch in enumerate(post_patches):
                if (
                    not isinstance(patch, Mapping)
                    or patch.get("kind") != "U16_LE"
                    or patch.get("width") != 2
                ):
                    _fail(
                        f"{group_name} row {recipe_index} post patch {patch_index} "
                        "is unsupported"
                    )
                relative = _integer(
                    patch.get("offset"),
                    f"{group_name} row {recipe_index} post patch offset",
                    0,
                    copy_size - 2,
                )
                value = _integer(
                    patch.get("value"),
                    f"{group_name} row {recipe_index} post patch value",
                    0,
                    0xFFFF,
                )
                struct.pack_into("<H", target, destination + relative, value)
            applied += 1

    # 613 CFRU Item rows + (613 CFRU + 11 reused QOL) icon rows。
    if applied != 1237:
        _fail(f"source row copy count differs: {applied} != 1237")
    result["tables"] = {symbol: bytes(raw) for symbol, raw in tables.items()}
    metadata = dict(_mapping(result.get("metadata"), "runtime assets.metadata"))
    metadata["source_copy_status"] = "APPLIED"
    metadata["source_table_sha256"] = {
        key: _sha256(raw) for key, raw in checked_sources.items()
    }
    metadata["source_row_copy_count"] = applied
    result["metadata"] = metadata
    _refresh_manifest(result)
    return result


def resolve_runtime_assets(
    assets: Mapping[str, Any], offsets: Mapping[str, int]
) -> dict[str, bytes | object]:
    """全 ABS32 relocation を symbol address で解決した資産のcopyを返す。

    ``build_runtime_assets(..., offsets=prototype_offsets)`` は既知link symbolだけを
    適用し、生成blob/QOL handlerなど次linkで確定するsymbolを明示的に残す。
    本関数は最終gate用であり、残存symbolを1件も許容しない。
    """

    return _apply_runtime_offsets(assets, offsets, strict=True)


__all__ = [
    "ABILITY_COUNT",
    "ABILITY_NAME_STRIDE",
    "CFRURuntimeTableError",
    "ITEM_COUNT",
    "ITEM_ICON_STRIDE",
    "ITEM_STRIDE",
    "MOVE_COUNT",
    "MOVE_NAME_STRIDE",
    "MOVE_STRIDE",
    "apply_source_table_patches",
    "build_runtime_assets",
    "resolve_runtime_assets",
]
