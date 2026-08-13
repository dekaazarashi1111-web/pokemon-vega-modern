#!/usr/bin/env python3
"""固定CFRU/DPE sourceとT01 compiled baselineからID空間を抽出する。

このmoduleは成果物を書き込まない。公開入口は ``default_policy`` と
``extract_cfru_id_spaces`` で、返り値はそのままJSON化できる。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
EXPECTED_COUNTS = {"types": 25, "abilities": 311, "items": 774}
ROM_BASE = 0x08000000
ROM_LIMIT = 0x0A000000

_CFRU_SOURCE_FILES = (
    "charmap.tbl",
    "include/battle.h",
    "include/constants/abilities.h",
    "include/constants/items.h",
    "include/constants/pokemon.h",
    "include/constants/tmshms.h",
    "include/new/item.h",
    "src/Tables/item_tables.c",
    "src/Tables/type_tables.h",
    "src/ability_battle_effects.c",
    "src/terastal.c",
    "strings/ability_name_table.string",
    "strings/ability_descriptions.string",
    "strings/item_descriptions.string",
    "strings/type_names.string",
    "assembly/data/ability_description_table.s",
    "assembly/data/type_tables.s",
)

_DPE_SOURCE_FILES = (
    "charmap.tbl",
    "include/abilities.h",
    "include/items.h",
    "include/base_stats.h",
)

_BASELINE_SYMBOLS = (
    "gAbilityNames",
    "gAbilityDescriptions",
    "gItemData",
    "gItemGraphicsTable",
    "gTypeEffectiveness",
    "gTypeNames",
)

_ITEM_FIELDS = (
    "name",
    "itemId",
    "price",
    "holdEffect",
    "holdEffectParam",
    "description",
    "importance",
    "unk19",
    "pocket",
    "type",
    "fieldUseFunc",
    "battleUsage",
    "battleUseFunc",
    "secondaryId",
)


class CFRUIdSpaceInventoryError(ValueError):
    """固定入力から完全で一意なID inventoryを作れない。"""


def default_policy() -> dict[str, Any]:
    """T01の固定成果物を参照する既定policyを返す。"""

    return {
        "cfru_source": "vendor/upstream/CFRU-JP",
        "dpe_source": "vendor/upstream/DPE-JP",
        "source_lock": "state/source-lock.json",
        "t01_report": "reports/generated/upstream_repro.json",
        "baseline": {"engine": "cfru", "profile": "baseline", "run": 1},
        "expected_counts": dict(EXPECTED_COUNTS),
        "expected_commits": {
            "cfru": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
            "dpe": "10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e",
        },
        "expected_source_bundle_sha256": {
            "cfru": "34b3f2bb10780da2108e2c52d3d33faf9ed23cde642ca0f66f48b3bb4a9d3a61",
            "dpe": "d5b7a64d7595a801c713828f6c5c4e4bcda12395b5565a3829cefcccd72c06a0",
        },
        "expected_baseline_sha256": (
            "140aa67a38046bcbf3d211550d900929039a4e7c41e55572f9503b6f27d71922"
        ),
        "expected_offsets_sha256": (
            "05cef90bc63c04cd93a1a327ddfef1aa07d4910e42d80c3f43ae8db800f2b0fd"
        ),
        "expected_charmap_sha256": (
            "35c1b978f7004129679751a79cf4b40d7edd2fcd678bc81a29483b64b75b7ed5"
        ),
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256(encoded)


def _merge_mapping(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _merge_mapping(dict(result[key]), value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _resolved_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    if policy is None:
        return default_policy()
    if not isinstance(policy, Mapping):
        raise CFRUIdSpaceInventoryError("policy must be a mapping")
    # build scriptのconfig全体と、そのcfru section単体の双方を受け入れる。
    outer = policy
    selected = policy.get("cfru", policy)
    if not isinstance(selected, Mapping):
        raise CFRUIdSpaceInventoryError("policy.cfru must be a mapping")
    flat_keys = {
        "source_path",
        "commit",
        "baseline_rom_path",
        "baseline_rom_sha256",
        "offsets_path",
        "offsets_sha256",
        "type_count",
        "ability_count",
        "item_count",
    }
    if set(selected) & flat_keys:
        unknown = set(selected) - flat_keys
        if unknown:
            raise CFRUIdSpaceInventoryError(
                f"unknown flat policy.cfru keys: {sorted(unknown)}"
            )
        missing = flat_keys - set(selected)
        if missing:
            raise CFRUIdSpaceInventoryError(
                f"missing flat policy.cfru keys: {sorted(missing)}"
            )
        adapted: dict[str, Any] = {
            "cfru_source": selected["source_path"],
            "baseline": {
                "engine": "cfru",
                "profile": "baseline",
                "run": 1,
                "rom": selected["baseline_rom_path"],
                "offsets": selected["offsets_path"],
            },
            "expected_baseline_sha256": selected["baseline_rom_sha256"],
            "expected_offsets_sha256": selected["offsets_sha256"],
            "expected_counts": {
                "types": selected["type_count"],
                "abilities": selected["ability_count"],
                "items": selected["item_count"],
            },
            "expected_commits": {"cfru": selected["commit"]},
        }
        dpe = outer.get("dpe") if "cfru" in outer else None
        if dpe is not None:
            if not isinstance(dpe, Mapping) or set(dpe) != {"source_path", "commit"}:
                raise CFRUIdSpaceInventoryError(
                    "flat policy.dpe must contain exactly source_path and commit"
                )
            adapted["dpe_source"] = dpe["source_path"]
            adapted["expected_commits"]["dpe"] = dpe["commit"]
        charmap = outer.get("charmap") if "cfru" in outer else None
        if charmap is not None:
            if not isinstance(charmap, Mapping) or set(charmap) != {"path", "sha256"}:
                raise CFRUIdSpaceInventoryError(
                    "flat policy.charmap must contain exactly path and sha256"
                )
            expected_charmap = f"{str(selected['source_path']).rstrip('/')}/charmap.tbl"
            if charmap["path"] != expected_charmap:
                raise CFRUIdSpaceInventoryError(
                    f"policy.charmap.path differs from CFRU source: {charmap['path']}"
                )
            adapted["expected_charmap_sha256"] = charmap["sha256"]
        return _merge_mapping(default_policy(), adapted)
    return _merge_mapping(default_policy(), selected)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _source_ref(path: str, text: str, offset: int, symbol: str) -> dict[str, Any]:
    return {
        "path": path,
        "line": _line_number(text, offset),
        "symbol": symbol,
    }


def _root_path(root: Path, value: object, label: str) -> tuple[Path, str]:
    if not isinstance(value, str) or not value:
        raise CFRUIdSpaceInventoryError(f"{label} must be a non-empty path string")
    path = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as error:
        raise CFRUIdSpaceInventoryError(f"{label} must be inside root") from error
    return path, relative


def _read_text(path: Path, logical_path: str) -> tuple[str, bytes]:
    if path.is_symlink() or not path.is_file():
        raise CFRUIdSpaceInventoryError(
            f"required source is missing/non-regular: {logical_path}"
        )
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig"), raw
    except UnicodeDecodeError as error:
        raise CFRUIdSpaceInventoryError(f"source is not UTF-8: {logical_path}") from error


def _load_json(path: Path, logical_path: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise CFRUIdSpaceInventoryError(f"required JSON is missing: {logical_path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CFRUIdSpaceInventoryError(f"invalid JSON: {logical_path}") from error
    if not isinstance(value, dict):
        raise CFRUIdSpaceInventoryError(f"JSON root must be an object: {logical_path}")
    return value, raw


def _git_head(source_root: Path) -> str | None:
    git = source_root / ".git"
    if not git.is_dir():
        return None
    head_path = git / "HEAD"
    if not head_path.is_file():
        raise CFRUIdSpaceInventoryError(f"invalid git metadata: {source_root.name}")
    head = head_path.read_text(encoding="ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", head):
        return head
    if not head.startswith("ref: "):
        raise CFRUIdSpaceInventoryError(f"invalid git HEAD: {source_root.name}")
    ref = head[5:]
    loose = git / ref
    if loose.is_file():
        commit = loose.read_text(encoding="ascii").strip()
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    packed = git / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii").splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1] == ref and re.fullmatch(r"[0-9a-f]{40}", fields[0]):
                return fields[0]
    raise CFRUIdSpaceInventoryError(f"cannot resolve git HEAD: {source_root.name}")


def _locked_source(
    lock: Mapping[str, Any], name: str, logical_root: str
) -> Mapping[str, Any]:
    matches = [
        row
        for row in lock.get("sources", [])
        if isinstance(row, Mapping)
        and row.get("name") == name
        and row.get("path") == logical_root
    ]
    if len(matches) != 1:
        raise CFRUIdSpaceInventoryError(
            f"source-lock must contain exactly one {name} source at {logical_root}"
        )
    return matches[0]


def _source_identity(
    *,
    name: str,
    source_root: Path,
    logical_root: str,
    lock: Mapping[str, Any],
    expected_commit: object,
    report_sources: Mapping[str, Any],
) -> tuple[str, str | None]:
    row = _locked_source(lock, name, logical_root)
    commit = row.get("resolved_commit") or row.get("actual_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise CFRUIdSpaceInventoryError(f"invalid locked {name} commit")
    if expected_commit is not None and commit != expected_commit:
        raise CFRUIdSpaceInventoryError(
            f"{name} locked commit differs from policy: {commit} != {expected_commit}"
        )
    head = _git_head(source_root)
    if head is None or head != commit:
        raise CFRUIdSpaceInventoryError(
            f"{name} git HEAD differs from source-lock: {head} != {commit}"
        )
    report_row = report_sources.get(name)
    if not isinstance(report_row, Mapping) or report_row.get("commit") != commit:
        raise CFRUIdSpaceInventoryError(f"T01 report {name} commit differs from source-lock")
    tree = report_row.get("tree")
    if tree is not None and (
        not isinstance(tree, str) or not re.fullmatch(r"[0-9a-f]{40}", tree)
    ):
        raise CFRUIdSpaceInventoryError(f"invalid T01 {name} tree hash")
    return commit, tree


def _strip_c_comments(text: str) -> str:
    """位置と改行を保ったままC/asm commentを空白化する。"""

    pattern = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)

    def blank(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group(0))

    return pattern.sub(blank, text)


def _without_unbound(text: str) -> str:
    """固定buildで未定義のUNBOUND branchだけを行位置を保って除外する。"""

    output: list[str] = []
    stack: list[tuple[bool, bool]] = []
    active = True
    for line in text.splitlines(keepends=True):
        match = re.match(r"\s*#\s*(ifdef|ifndef)\s+([A-Za-z_]\w*)", line)
        if match:
            condition = match.group(2) != "UNBOUND"
            if match.group(1) == "ifndef":
                condition = not condition
            stack.append((active, condition))
            active = active and condition
            output.append("\n" if line.endswith("\n") else "")
            continue
        if re.match(r"\s*#\s*else\b", line):
            if not stack:
                raise CFRUIdSpaceInventoryError("unmatched #else")
            parent, condition = stack[-1]
            active = parent and not condition
            output.append("\n" if line.endswith("\n") else "")
            continue
        if re.match(r"\s*#\s*endif\b", line):
            if not stack:
                raise CFRUIdSpaceInventoryError("unmatched #endif")
            parent, _ = stack.pop()
            active = parent
            output.append("\n" if line.endswith("\n") else "")
            continue
        output.append(line if active else ("\n" if line.endswith("\n") else ""))
    if stack:
        raise CFRUIdSpaceInventoryError("unterminated preprocessor conditional")
    return "".join(output)


def _eval_constant(expression: str, values: Mapping[str, int]) -> int:
    expression = expression.strip()
    while expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()
    match = re.fullmatch(
        r"(0x[0-9A-Fa-f]+|[0-9]+|[A-Za-z_]\w*)(?:\s*([+-])\s*(0x[0-9A-Fa-f]+|[0-9]+))?",
        expression,
    )
    if match is None:
        raise CFRUIdSpaceInventoryError(f"unsupported constant expression: {expression}")
    token = match.group(1)
    try:
        value = int(token, 0)
    except ValueError:
        if token not in values:
            raise CFRUIdSpaceInventoryError(f"unresolved constant: {token}")
        value = values[token]
    if match.group(2):
        delta = int(match.group(3), 0)
        value = value + delta if match.group(2) == "+" else value - delta
    return value


def _parse_constants(
    text: str, path: str, prefix: str
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    active = _without_unbound(text)
    clean = _strip_c_comments(active)
    events: list[tuple[int, str, str, str]] = []
    for match in re.finditer(
        rf"^\s*#define\s+({re.escape(prefix)}[A-Z0-9_]+)\s+([^\n]+)$",
        clean,
        re.MULTILINE,
    ):
        expression = match.group(2).strip()
        # function-like macroはnamespace IDではない。
        if expression.startswith("(") and ")" in match.group(1):
            continue
        events.append((match.start(), "define", match.group(1), expression))
    for enum_match in re.finditer(r"\benum(?:\s+[A-Za-z_]\w*)?\s*\{(.*?)\}\s*;", clean, re.DOTALL):
        body = enum_match.group(1)
        cursor = enum_match.start(1)
        for part in body.split(","):
            stripped = part.strip()
            if not stripped:
                cursor += len(part) + 1
                continue
            match = re.fullmatch(
                rf"({re.escape(prefix)}[A-Z0-9_]+)(?:\s*=\s*(.+))?", stripped, re.DOTALL
            )
            if match:
                position = clean.find(match.group(1), cursor, cursor + len(part) + 1)
                events.append(
                    (
                        position if position >= 0 else cursor,
                        "enum",
                        match.group(1),
                        (match.group(2) or "").strip(),
                    )
                )
            cursor += len(part) + 1
    events.sort(key=lambda row: row[0])

    values: dict[str, int] = {}
    rows: dict[str, dict[str, Any]] = {}
    aliases: list[dict[str, Any]] = []
    enum_next: int | None = None
    for offset, kind, symbol, expression in events:
        if symbol in rows:
            raise CFRUIdSpaceInventoryError(f"duplicate constant symbol: {symbol}")
        if kind == "enum" and not expression:
            if enum_next is None:
                raise CFRUIdSpaceInventoryError(f"enum has no initial value: {symbol}")
            value = enum_next
        else:
            value = _eval_constant(expression, values)
        if kind == "enum":
            enum_next = value + 1
        values[symbol] = value
        row = {
            "value": value,
            "expression": expression or str(value),
            "kind": kind,
            "source_ref": _source_ref(path, text, offset, symbol),
        }
        rows[symbol] = row
        target_match = re.fullmatch(rf"{re.escape(prefix)}[A-Z0-9_]+", expression)
        if kind == "define" and target_match and expression != symbol:
            aliases.append(
                {
                    "symbol": symbol,
                    "target_symbol": expression,
                    "id": value,
                    "source_ref": row["source_ref"],
                }
            )
    if not rows:
        raise CFRUIdSpaceInventoryError(f"no {prefix} constants found in {path}")
    return rows, aliases


def _initializer_bounds(text: str, marker: str) -> tuple[int, int]:
    clean = _strip_c_comments(text)
    marker_offset = clean.find(marker)
    if marker_offset < 0:
        raise CFRUIdSpaceInventoryError(f"initializer marker not found: {marker}")
    start = clean.find("{", marker_offset + len(marker))
    if start < 0:
        raise CFRUIdSpaceInventoryError(f"initializer has no opening brace: {marker}")
    depth = 0
    for offset in range(start, len(clean)):
        char = clean[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, offset
    raise CFRUIdSpaceInventoryError(f"unterminated initializer: {marker}")


def _initializer_entries(text: str, marker: str) -> list[tuple[str, int]]:
    clean = _strip_c_comments(text)
    start, end = _initializer_bounds(text, marker)
    depth = 0
    entry_start: int | None = None
    entries: list[tuple[str, int]] = []
    for offset in range(start + 1, end):
        char = clean[offset]
        if char == "{":
            if depth == 0:
                entry_start = offset
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise CFRUIdSpaceInventoryError(f"invalid brace depth: {marker}")
            if depth == 0 and entry_start is not None:
                entries.append((text[entry_start : offset + 1], entry_start))
                entry_start = None
    if depth or entry_start is not None:
        raise CFRUIdSpaceInventoryError(f"invalid entries: {marker}")
    return entries


def _designated_fields(block: str) -> dict[str, str]:
    matches = list(re.finditer(r"\.([A-Za-z_]\w*)\s*=", block))
    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block) - 1
        value = block[match.end() : end].strip().rstrip(",").strip()
        if match.group(1) in fields:
            raise CFRUIdSpaceInventoryError(f"duplicate designated field: {match.group(1)}")
        fields[match.group(1)] = re.sub(r"\s+", " ", value)
    return fields


def _parse_item_records(text: str, path: str) -> list[dict[str, Any]]:
    entries = _initializer_entries(text, "const struct Item gItemData[]")
    rows: list[dict[str, Any]] = []
    for index, (block, offset) in enumerate(entries):
        fields = _designated_fields(block)
        missing = [field for field in _ITEM_FIELDS if field not in fields]
        extra = sorted(set(fields) - set(_ITEM_FIELDS))
        if missing or extra:
            raise CFRUIdSpaceInventoryError(
                f"item record {index} fields differ: missing={missing}, extra={extra}"
            )
        raw_name = fields["name"]
        name_bytes = bytes(int(token, 16) for token in re.findall(r"0x([0-9A-Fa-f]{2})", raw_name))
        if not name_bytes or name_bytes[-1] != 0xFF:
            raise CFRUIdSpaceInventoryError(f"item record {index} name is not terminated")
        rows.append(
            {
                "fields": fields,
                "name_bytes": name_bytes,
                "source_ref": _source_ref(path, text, offset, fields["itemId"]),
            }
        )
    return rows


def _split_pair(block: str) -> tuple[str, str]:
    body = block.strip()[1:-1]
    parts = [part.strip() for part in body.split(",") if part.strip()]
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z_]\w*", part) for part in parts):
        raise CFRUIdSpaceInventoryError(f"unsupported icon initializer: {block}")
    return parts[0], parts[1]


def _parse_item_icons(text: str, path: str) -> list[dict[str, Any]]:
    entries = _initializer_entries(text, "const struct ItemIconTemplate gItemGraphicsTable[]")
    rows: list[dict[str, Any]] = []
    for block, offset in entries:
        icon, palette = _split_pair(block)
        rows.append(
            {
                "icon_symbol": icon,
                "palette_symbol": palette,
                "source_ref": _source_ref(path, text, offset, icon),
            }
        )
    return rows


def _parse_item_types(
    *,
    enum_text: str,
    enum_path: str,
    table_text: str,
    table_path: str,
    item_constants: Mapping[str, Mapping[str, Any]],
    expected_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """固定ItemType enumとgItemsByTypeのdesignated表を完全に結合する。"""

    enum_clean = _strip_c_comments(enum_text)
    enum_start, enum_end = _initializer_bounds(enum_clean, "enum ItemType")
    enum_body = enum_clean[enum_start + 1 : enum_end]
    type_rows: list[dict[str, Any]] = []
    cursor = enum_start + 1
    for part in enum_body.split(","):
        stripped = part.strip()
        if not stripped:
            cursor += len(part) + 1
            continue
        match = re.fullmatch(r"(ITEM_TYPE_[A-Z0-9_]+)(?:\s*=\s*([0-9]+|0x[0-9A-Fa-f]+))?", stripped)
        if match is None:
            raise CFRUIdSpaceInventoryError(
                f"unsupported ItemType enum entry: {stripped!r}"
            )
        symbol = match.group(1)
        expected_value = len(type_rows)
        value = expected_value if match.group(2) is None else int(match.group(2), 0)
        if value != expected_value:
            raise CFRUIdSpaceInventoryError(
                f"ItemType enum is not contiguous at {symbol}: {value} != {expected_value}"
            )
        offset = enum_clean.find(symbol, cursor, cursor + len(part) + 1)
        if offset < 0:
            raise CFRUIdSpaceInventoryError(f"cannot locate ItemType source: {symbol}")
        type_rows.append(
            {
                "id": value,
                "symbol": symbol,
                "source_ref": _source_ref(enum_path, enum_text, offset, symbol),
            }
        )
        cursor += len(part) + 1
    if len(type_rows) != 63:
        raise CFRUIdSpaceInventoryError(
            f"ItemType enum count changed: {len(type_rows)} != 63"
        )
    type_by_symbol = {row["symbol"]: row for row in type_rows}

    table_clean = _strip_c_comments(table_text)
    start, end = _initializer_bounds(table_clean, "const u16 gItemsByType[ITEMS_COUNT]")
    fragment = table_clean[start + 1 : end]
    pattern = re.compile(
        r"\[\s*(ITEM_[A-Z0-9_]+)\s*\]\s*=\s*(ITEM_TYPE_[A-Z0-9_]+)\s*,"
    )
    matches = list(pattern.finditer(fragment))
    if len(matches) != 465:
        raise CFRUIdSpaceInventoryError(
            f"gItemsByType explicit count changed: {len(matches)} != 465"
        )
    if pattern.sub("", fragment).strip():
        raise CFRUIdSpaceInventoryError("gItemsByType contains unsupported initializer syntax")
    table_ref = _source_ref(table_path, table_text, start, "gItemsByType")
    assignments: dict[int, dict[str, Any]] = {}
    for match in matches:
        item_symbol, type_symbol = match.groups()
        item = item_constants.get(item_symbol)
        item_type = type_by_symbol.get(type_symbol)
        if item is None or item_type is None:
            raise CFRUIdSpaceInventoryError(
                f"gItemsByType has unresolved symbols: {item_symbol}={type_symbol}"
            )
        item_id = int(item["value"])
        if not 0 <= item_id < expected_count:
            raise CFRUIdSpaceInventoryError(
                f"gItemsByType item ID outside range: {item_symbol}={item_id}"
            )
        if item_id in assignments:
            raise CFRUIdSpaceInventoryError(
                f"gItemsByType assigns item ID {item_id} more than once"
            )
        absolute_offset = start + 1 + match.start()
        assignments[item_id] = {
            "item_type_id": int(item_type["id"]),
            "item_type_key": type_symbol,
            "item_type_explicit": True,
            "item_type_source_ref": _source_ref(
                table_path, table_text, absolute_offset, item_symbol
            ),
            "is_evolution_stone": type_symbol == "ITEM_TYPE_EVOLUTION_STONE",
            "is_evolution_item": type_symbol == "ITEM_TYPE_EVOLUTION_ITEM",
        }
    rows = [
        assignments.get(
            item_id,
            {
                "item_type_id": 0,
                "item_type_key": "ITEM_TYPE_DEFAULT_0",
                "item_type_explicit": False,
                "item_type_source_ref": table_ref,
                "is_evolution_stone": False,
                "is_evolution_item": False,
            },
        )
        for item_id in range(expected_count)
    ]
    if sum(row["is_evolution_stone"] for row in rows) != 12:
        raise CFRUIdSpaceInventoryError("evolution-stone item set changed")
    if sum(row["is_evolution_item"] for row in rows) != 40:
        raise CFRUIdSpaceInventoryError("evolution-item set changed")
    return rows, type_rows


def _parse_tera_type_colors(
    text: str, path: str, expected_count: int
) -> list[dict[str, Any]]:
    """sTeraTypeColorのRGB(5-bit) positional tableを厳密に読む。"""

    marker = "static const u16 sTeraTypeColor[NUMBER_OF_MON_TYPES]"
    start, end = _initializer_bounds(text, marker)
    clean = _strip_c_comments(text)
    fragment = clean[start + 1 : end]
    pattern = re.compile(
        r"RGB\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)"
    )
    matches = list(pattern.finditer(fragment))
    cursor = 0
    for index, match in enumerate(matches):
        separator = fragment[cursor : match.start()].strip()
        expected_separator = "" if index == 0 else ","
        if separator != expected_separator:
            raise CFRUIdSpaceInventoryError(
                f"unsupported separator before sTeraTypeColor entry {index}: {separator!r}"
            )
        cursor = match.end()
    trailing = fragment[cursor:].strip()
    if trailing not in ("", ","):
        raise CFRUIdSpaceInventoryError(
            f"unsupported trailing token in sTeraTypeColor: {trailing!r}"
        )
    if len(matches) != expected_count:
        raise CFRUIdSpaceInventoryError(
            f"sTeraTypeColor count changed: {len(matches)} != {expected_count}"
        )
    rows: list[dict[str, Any]] = []
    for type_id, match in enumerate(matches):
        red, green, blue = (int(match.group(index)) for index in (1, 2, 3))
        if not all(0 <= component <= 31 for component in (red, green, blue)):
            raise CFRUIdSpaceInventoryError(
                f"sTeraTypeColor entry {type_id} is outside RGB5 range: "
                f"({red}, {green}, {blue})"
            )
        absolute = start + 1 + match.start()
        rows.append(
            {
                "r": red,
                "g": green,
                "b": blue,
                "bgr555": red | (green << 5) | (blue << 10),
                "source_ref": _source_ref(path, text, absolute, f"sTeraTypeColor[{type_id}]"),
            }
        )
    return rows


def _parse_org_sequence(text: str, path: str, table_symbol: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"^#org\s+@([A-Za-z0-9_]+)\s*$", text, re.MULTILINE))
    table_index = next(
        (index for index, match in enumerate(matches) if match.group(1) == table_symbol), None
    )
    if table_index is None:
        raise CFRUIdSpaceInventoryError(f"#org @{table_symbol} not found")
    rows: list[dict[str, Any]] = []
    for index in range(table_index + 1, len(matches)):
        match = matches[index]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content_lines = []
        for line in text[match.end() : end].splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ".")):
                continue
            content_lines.append(stripped)
        if not content_lines:
            raise CFRUIdSpaceInventoryError(f"empty string block: {match.group(1)}")
        rows.append(
            {
                "symbol": match.group(1),
                "text": "\n".join(content_lines),
                "source_ref": _source_ref(path, text, match.start(), match.group(1)),
            }
        )
    return rows


def _parse_word_rows(text: str, path: str, label: str) -> list[dict[str, Any]]:
    label_match = re.search(rf"^{re.escape(label)}:\s*$", text, re.MULTILINE)
    if label_match is None:
        raise CFRUIdSpaceInventoryError(f"word table not found: {label}")
    rows: list[dict[str, Any]] = []
    for match in re.finditer(r"^\s*\.word\s+([^@;\n]+)", text[label_match.end() :], re.MULTILINE):
        expression = match.group(1).strip()
        absolute = label_match.end() + match.start()
        if not re.fullmatch(r"0x[0-9A-Fa-f]+|[A-Za-z_]\w*", expression):
            raise CFRUIdSpaceInventoryError(f"unsupported .word expression: {expression}")
        rows.append(
            {
                "expression": expression,
                "source_ref": _source_ref(path, text, absolute, expression),
            }
        )
    return rows


def _parse_ability_ratings(
    text: str, path: str, constants: Mapping[str, Mapping[str, Any]], count: int
) -> tuple[list[int], dict[str, dict[str, Any]]]:
    start, end = _initializer_bounds(text, "const s8 gAbilityRatings[ABILITIES_COUNT]")
    fragment = text[start + 1 : end]
    ratings = [0] * count
    refs: dict[str, dict[str, Any]] = {}
    for match in re.finditer(
        r"\[(ABILITY_[A-Z0-9_]+)\]\s*=\s*(-?[0-9]+)\s*,", fragment
    ):
        symbol = match.group(1)
        if symbol not in constants:
            raise CFRUIdSpaceInventoryError(f"rating uses unknown ability: {symbol}")
        ability_id = int(constants[symbol]["value"])
        if symbol in refs:
            raise CFRUIdSpaceInventoryError(f"duplicate ability rating: {symbol}")
        ratings[ability_id] = int(match.group(2))
        refs[symbol] = _source_ref(path, text, start + 1 + match.start(), symbol)
    return ratings, refs


def _parse_charmap(text: str) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([0-9A-Fa-f]{2})=(.*)$", line)
        if match:
            mapping[int(match.group(1), 16)] = match.group(2)
    if len(mapping) < 200 or 0xFF not in mapping:
        raise CFRUIdSpaceInventoryError("charmap is incomplete")
    return mapping


def _decode_text(data: bytes, charmap: Mapping[int, str], *, require_terminator: bool = True) -> str:
    output: list[str] = []
    terminated = False
    for value in data:
        if value == 0xFF:
            terminated = True
            break
        token = charmap.get(value)
        if token is None:
            raise CFRUIdSpaceInventoryError(f"unmapped game text byte: 0x{value:02X}")
        if token in (r"\n", r"\l"):
            output.append("\n")
        elif token == r"\p":
            output.append("\n\n")
        else:
            output.append(token)
    if require_terminator and not terminated:
        raise CFRUIdSpaceInventoryError("game text lacks 0xFF terminator")
    return "".join(output)


def _parse_offsets(path: Path, logical_path: str) -> dict[str, int]:
    if path.is_symlink() or not path.is_file():
        raise CFRUIdSpaceInventoryError(f"baseline offsets missing: {logical_path}")
    text = path.read_text(encoding="utf-8")
    values: dict[str, int] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([^:]+):\s*([0-9A-Fa-f]{8})\s*", line)
        if match:
            values[match.group(1).strip()] = int(match.group(2), 16)
    missing = [symbol for symbol in _BASELINE_SYMBOLS if symbol not in values]
    if missing:
        raise CFRUIdSpaceInventoryError(f"baseline offsets lack symbols: {missing}")
    return values


def _rom_offset(address: int, rom_size: int, size: int, label: str) -> int:
    if not ROM_BASE <= address < ROM_LIMIT:
        raise CFRUIdSpaceInventoryError(f"{label} is not a ROM address: 0x{address:08X}")
    offset = address - ROM_BASE
    if offset + size > rom_size:
        raise CFRUIdSpaceInventoryError(f"{label} exceeds baseline ROM")
    return offset


def _rom_text(rom: bytes, address: int, charmap: Mapping[int, str], label: str) -> str:
    offset = _rom_offset(address, len(rom), 1, label)
    end = rom.find(b"\xff", offset, min(len(rom), offset + 2048))
    if end < 0:
        raise CFRUIdSpaceInventoryError(f"unterminated ROM text: {label}")
    return _decode_text(rom[offset : end + 1], charmap)


def _hex_address(value: int) -> str | None:
    return None if value == 0 else f"0x{value:08X}"


def _numeric_literal(expression: str, label: str) -> int:
    expression = expression.strip()
    try:
        return int(expression, 0)
    except ValueError as error:
        raise CFRUIdSpaceInventoryError(f"{label} must be numeric: {expression}") from error


def _baseline_from_report(
    root: Path, policy: Mapping[str, Any], report: Mapping[str, Any]
) -> tuple[Path, str, Path, str, Mapping[str, Any]]:
    baseline = policy.get("baseline")
    if not isinstance(baseline, Mapping):
        raise CFRUIdSpaceInventoryError("policy.baseline must be a mapping")
    direct_rom = baseline.get("rom") or policy.get("baseline_rom")
    direct_offsets = baseline.get("offsets") or policy.get("baseline_offsets")
    if direct_rom is not None:
        rom_path, rom_logical = _root_path(root, direct_rom, "baseline ROM")
        offsets_value = direct_offsets or str(Path(rom_logical).with_name("offsets.ini"))
        offsets_path, offsets_logical = _root_path(root, offsets_value, "baseline offsets")
        build_row: Mapping[str, Any] = {}
        return rom_path, rom_logical, offsets_path, offsets_logical, build_row

    engine = baseline.get("engine", "cfru")
    profile = baseline.get("profile", "baseline")
    run = baseline.get("run", 1)
    matches = [
        row
        for row in report.get("builds", [])
        if isinstance(row, Mapping)
        and row.get("engine") == engine
        and row.get("profile") == profile
        and row.get("run") == run
    ]
    if len(matches) != 1:
        raise CFRUIdSpaceInventoryError(
            f"T01 report must contain one baseline build: {engine}/{profile}/run-{run}"
        )
    build_row = matches[0]
    artifact_dir = build_row.get("artifact_dir")
    if not isinstance(artifact_dir, str):
        raise CFRUIdSpaceInventoryError("T01 baseline artifact_dir is invalid")
    rom_path, rom_logical = _root_path(root, f"{artifact_dir}/test.gba", "baseline ROM")
    offsets_path, offsets_logical = _root_path(
        root, f"{artifact_dir}/offsets.ini", "baseline offsets"
    )
    return rom_path, rom_logical, offsets_path, offsets_logical, build_row


def _canonical_rows(
    constants: Mapping[str, Mapping[str, Any]], count: int, prefix: str
) -> list[dict[str, Any]]:
    by_id: dict[int, list[tuple[str, Mapping[str, Any]]]] = {}
    for symbol, row in constants.items():
        value = int(row["value"])
        if 0 <= value < count:
            by_id.setdefault(value, []).append((symbol, row))
    missing = [value for value in range(count) if value not in by_id]
    if missing:
        raise CFRUIdSpaceInventoryError(f"{prefix} constants have ID gaps: {missing[:12]}")
    result = []
    for value in range(count):
        candidates = by_id[value]
        # 数値定義をaliasより優先する。ENIGMA_BERRY_OLDが固定表の実体になる。
        candidates.sort(
            key=lambda pair: (
                bool(re.fullmatch(rf"{re.escape(prefix)}[A-Z0-9_]+", pair[1]["expression"])),
                pair[1]["source_ref"]["line"],
                pair[0],
            )
        )
        symbol, row = candidates[0]
        result.append({"id": value, "symbol": symbol, "constant": row})
    return result


def _build_types(
    *,
    constants: Mapping[str, Mapping[str, Any]],
    dpe_constants: Mapping[str, Mapping[str, Any]],
    names: Sequence[Mapping[str, Any]],
    display_colors: Sequence[Mapping[str, Any]],
    type_asm: str,
    type_asm_path: str,
    type_table_text: str,
    type_table_path: str,
    rom: bytes,
    offsets: Mapping[str, int],
    expected_count: int,
) -> list[dict[str, Any]]:
    if expected_count != 25:
        raise CFRUIdSpaceInventoryError("only the fixed 25-entry type space is supported")
    type_by_id = {
        int(row["value"]): (symbol, row)
        for symbol, row in constants.items()
        if symbol.startswith("TYPE_")
        and symbol != "TYPE_NAME_LENGTH"
        and 0 <= int(row["value"]) < expected_count
    }
    if set(type_by_id) != {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 23, 24}:
        raise CFRUIdSpaceInventoryError("fixed CFRU type constants changed")
    for type_id, (symbol, _) in type_by_id.items():
        dpe = dpe_constants.get(symbol)
        if dpe is None or int(dpe["value"]) != type_id:
            raise CFRUIdSpaceInventoryError(f"DPE type mismatch: {symbol}")
    if len(names) != 24:
        raise CFRUIdSpaceInventoryError(f"CFRU type name count changed: {len(names)} != 24")
    if len(display_colors) != expected_count:
        raise CFRUIdSpaceInventoryError(
            f"CFRU type display color count changed: {len(display_colors)} != {expected_count}"
        )

    icon_matches = list(
        re.finditer(
            r"^\s*typeicon\s+([0-9]+)\s*,\s*([0-9]+)\s*,\s*(0x[0-9A-Fa-f]+|[0-9]+)",
            type_asm,
            re.MULTILINE,
        )
    )
    if len(icon_matches) < expected_count + 1:
        raise CFRUIdSpaceInventoryError("gMoveMenuInfoIcons lacks type entries")

    matrix_address = offsets["gTypeEffectiveness"]
    matrix_offset = _rom_offset(
        matrix_address, len(rom), expected_count * expected_count * 2, "gTypeEffectiveness"
    )
    flat = struct.unpack_from(f"<{expected_count * expected_count}H", rom, matrix_offset)
    allowed = {0, 1, 500, 1000, 2000}
    if not set(flat) <= allowed:
        raise CFRUIdSpaceInventoryError("compiled type matrix contains unsupported multipliers")

    table_start = type_table_text.find("gTypeEffectiveness")
    table_ref = _source_ref(type_table_path, type_table_text, table_start, "gTypeEffectiveness")
    rows: list[dict[str, Any]] = []
    for type_id in range(expected_count):
        if type_id in type_by_id:
            symbol, constant = type_by_id[type_id]
            constant_ref = constant["source_ref"]
        else:
            symbol = f"TYPE_RESERVED_{type_id}"
            constant_ref = None
        name = names[type_id] if type_id < len(names) else None
        display_color = display_colors[type_id]
        icon_match = icon_matches[type_id + 1]  # entry 0 is an unused menu glyph
        raw_row = list(flat[type_id * expected_count : (type_id + 1) * expected_count])
        logical_row = [1000 if value == 0 else value for value in raw_row]
        if type_id in (18, 19, 20, 21, 22):
            status = "ALIGNMENT_RESERVED"
        elif name is None:
            status = "MISSING_UPSTREAM_NAME"
        else:
            status = "ACTIVE"
        row_match = re.search(
            rf"\[{re.escape(symbol)}\]\s*=", type_table_text
        ) if type_id in type_by_id else None
        rows.append(
            {
                "id": type_id,
                "symbol": symbol,
                "canonical_key": f"TYPE_KEY_{symbol.removeprefix('TYPE_')}",
                "name_ja": name["text"] if name is not None else None,
                "status": status,
                "move_menu_icon": {
                    "width": int(icon_match.group(1)),
                    "height": int(icon_match.group(2)),
                    "tile_offset": int(icon_match.group(3), 0),
                },
                "display_color": {
                    "r": int(display_color["r"]),
                    "g": int(display_color["g"]),
                    "b": int(display_color["b"]),
                    "bgr555": int(display_color["bgr555"]),
                },
                "effectiveness": logical_row,
                "effectiveness_raw": raw_row,
                "source_refs": {
                    "constant": constant_ref,
                    "name": name["source_ref"] if name is not None else None,
                    "matrix": (
                        _source_ref(type_table_path, type_table_text, row_match.start(), symbol)
                        if row_match is not None
                        else table_ref
                    ),
                    "move_menu_icon": _source_ref(
                        type_asm_path, type_asm, icon_match.start(), symbol
                    ),
                    "display_color": display_color["source_ref"],
                },
            }
        )
    return rows


def _build_abilities(
    *,
    constants: Mapping[str, Mapping[str, Any]],
    dpe_constants: Mapping[str, Mapping[str, Any]],
    names: Sequence[Mapping[str, Any]],
    description_words: Sequence[Mapping[str, Any]],
    ratings: Sequence[int],
    rating_refs: Mapping[str, Mapping[str, Any]],
    rom: bytes,
    offsets: Mapping[str, int],
    charmap: Mapping[int, str],
    expected_count: int,
) -> list[dict[str, Any]]:
    canonical = _canonical_rows(constants, expected_count, "ABILITY_")
    if len(names) != expected_count or len(description_words) != expected_count:
        raise CFRUIdSpaceInventoryError(
            "ability name/description pointer count differs from constants"
        )
    name_offset = _rom_offset(
        offsets["gAbilityNames"], len(rom), expected_count * 17, "gAbilityNames"
    )
    description_offset = _rom_offset(
        offsets["gAbilityDescriptions"],
        len(rom),
        expected_count * 4,
        "gAbilityDescriptions",
    )
    rows: list[dict[str, Any]] = []
    for entry in canonical:
        ability_id = entry["id"]
        symbol = entry["symbol"]
        dpe = dpe_constants.get(symbol)
        if dpe is None or int(dpe["value"]) != ability_id:
            raise CFRUIdSpaceInventoryError(f"DPE ability mismatch: {symbol}")
        compiled_name = _decode_text(
            rom[name_offset + ability_id * 17 : name_offset + (ability_id + 1) * 17],
            charmap,
        )
        if compiled_name != names[ability_id]["text"]:
            raise CFRUIdSpaceInventoryError(
                f"compiled/source ability name mismatch at {ability_id}: "
                f"{compiled_name!r} != {names[ability_id]['text']!r}"
            )
        pointer = struct.unpack_from("<I", rom, description_offset + ability_id * 4)[0]
        description = _rom_text(rom, pointer, charmap, f"ability {ability_id} description")
        word = description_words[ability_id]
        rows.append(
            {
                "id": ability_id,
                "symbol": symbol,
                "canonical_key": f"ABILITY_KEY_{symbol.removeprefix('ABILITY_')}",
                "name_ja": compiled_name,
                "description_ja": description,
                "rating": int(ratings[ability_id]),
                "description_symbol": word["expression"],
                "description_rom_address": _hex_address(pointer),
                "source_refs": {
                    "constant": entry["constant"]["source_ref"],
                    "name": names[ability_id]["source_ref"],
                    "description_pointer": word["source_ref"],
                    "rating": rating_refs.get(symbol),
                },
            }
        )
    return rows


def _build_items(
    *,
    constants: Mapping[str, Mapping[str, Any]],
    dpe_constants: Mapping[str, Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
    icons: Sequence[Mapping[str, Any]],
    item_types: Sequence[Mapping[str, Any]],
    rom: bytes,
    offsets: Mapping[str, int],
    charmap: Mapping[int, str],
    expected_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    canonical = _canonical_rows(constants, expected_count, "ITEM_")
    if (
        len(records) != expected_count
        or len(icons) != expected_count
        or len(item_types) != expected_count
    ):
        raise CFRUIdSpaceInventoryError(
            "item table/icon/type count changed: "
            f"{len(records)}/{len(icons)}/{len(item_types)} != {expected_count}"
        )
    data_offset = _rom_offset(
        offsets["gItemData"], len(rom), expected_count * 40, "gItemData"
    )
    graphics_offset = _rom_offset(
        offsets["gItemGraphicsTable"],
        len(rom),
        expected_count * 8,
        "gItemGraphicsTable",
    )
    rows: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for entry in canonical:
        item_id = entry["id"]
        symbol = entry["symbol"]
        dpe = dpe_constants.get(symbol)
        if dpe is None or int(dpe["value"]) != item_id:
            raise CFRUIdSpaceInventoryError(f"DPE item mismatch: {symbol}")
        record = records[item_id]
        fields = record["fields"]
        compiled = rom[data_offset + item_id * 40 : data_offset + (item_id + 1) * 40]
        (
            compiled_id,
            price,
            hold_effect,
            hold_effect_param,
            description_pointer,
            importance,
            mystery,
            pocket,
            use_type,
            field_callback,
            battle_usage,
            battle_callback,
            secondary_id,
        ) = (
            struct.unpack_from("<H", compiled, 10)[0],
            struct.unpack_from("<H", compiled, 12)[0],
            compiled[14],
            compiled[15],
            struct.unpack_from("<I", compiled, 16)[0],
            compiled[20],
            compiled[21],
            compiled[22],
            compiled[23],
            struct.unpack_from("<I", compiled, 24)[0],
            compiled[28],
            struct.unpack_from("<I", compiled, 32)[0],
            compiled[36],
        )
        compiled_name = _decode_text(compiled[:10], charmap)
        source_name = _decode_text(record["name_bytes"], charmap)
        if compiled_name != source_name:
            raise CFRUIdSpaceInventoryError(
                f"compiled/source item name mismatch at {item_id}: {compiled_name!r} != {source_name!r}"
            )
        literal_checks = {
            "price": price,
            "holdEffectParam": hold_effect_param,
            "importance": importance,
            "unk19": mystery,
            "battleUsage": battle_usage,
            "secondaryId": secondary_id,
        }
        for field, actual in literal_checks.items():
            expression = fields[field]
            if re.fullmatch(r"0x[0-9A-Fa-f]+|[0-9]+", expression):
                expected = _numeric_literal(expression, f"item {item_id} {field}")
                if actual != expected:
                    raise CFRUIdSpaceInventoryError(
                        f"compiled/source item field mismatch at {item_id}.{field}: {actual} != {expected}"
                    )
        icon_pointer, palette_pointer = struct.unpack_from(
            "<II", rom, graphics_offset + item_id * 8
        )
        table_constant = constants.get(fields["itemId"])
        table_id = int(table_constant["value"]) if table_constant is not None else None
        if compiled_id != item_id or table_id != item_id:
            anomaly = {
                "kind": "ITEM_TABLE_IDENTITY_MISMATCH",
                "id": item_id,
                "canonical_symbol": symbol,
                "table_symbol": fields["itemId"],
                "compiled_item_id": compiled_id,
            }
            anomalies.append(anomaly)
        rows.append(
            {
                "id": item_id,
                "symbol": symbol,
                "canonical_key": f"ITEM_KEY_{symbol.removeprefix('ITEM_')}",
                "name_ja": compiled_name,
                "description_ja": _rom_text(
                    rom, description_pointer, charmap, f"item {item_id} description"
                ),
                "table_item_symbol": fields["itemId"],
                "compiled_item_id": compiled_id,
                "price": price,
                "hold_effect": hold_effect,
                "hold_effect_symbol": fields["holdEffect"],
                "hold_effect_param": hold_effect_param,
                "description_symbol": fields["description"],
                "description_rom_address": _hex_address(description_pointer),
                "importance": importance,
                "mystery": mystery,
                "pocket": pocket,
                "pocket_symbol": fields["pocket"],
                "use_type": use_type,
                "use_type_symbol": fields["type"],
                "field_callback_symbol": fields["fieldUseFunc"],
                "field_callback_address": _hex_address(field_callback),
                "battle_usage": battle_usage,
                "battle_callback_symbol": fields["battleUseFunc"],
                "battle_callback_address": _hex_address(battle_callback),
                "secondary_id": secondary_id,
                "icon_symbol": icons[item_id]["icon_symbol"],
                "palette_symbol": icons[item_id]["palette_symbol"],
                "icon_rom_address": _hex_address(icon_pointer),
                "palette_rom_address": _hex_address(palette_pointer),
                **dict(item_types[item_id]),
                "source_refs": {
                    "constant": entry["constant"]["source_ref"],
                    "item_record": record["source_ref"],
                    "icon": icons[item_id]["source_ref"],
                    "item_type": item_types[item_id]["item_type_source_ref"],
                },
            }
        )
    return rows, anomalies


def extract_cfru_id_spaces(
    root: Path, policy: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """固定source/baselineからtype・ability・item inventoryを返す。

    ``policy`` は ``default_policy()`` と同じ形、またはその内容を ``cfru``
    keyに格納したconfig全体を受け取れる。戻り値には絶対path、timestamp、非JSON型を
    含めない。
    """

    root = Path(root).resolve()
    if not root.is_dir():
        raise CFRUIdSpaceInventoryError("root is not a directory")
    resolved = _resolved_policy(policy)
    cfru_root, cfru_logical = _root_path(root, resolved["cfru_source"], "CFRU source")
    dpe_root, dpe_logical = _root_path(root, resolved["dpe_source"], "DPE source")
    lock_path, lock_logical = _root_path(root, resolved["source_lock"], "source-lock")
    report_path, report_logical = _root_path(root, resolved["t01_report"], "T01 report")
    if not cfru_root.is_dir() or not dpe_root.is_dir():
        raise CFRUIdSpaceInventoryError("fixed CFRU/DPE source directory is missing")

    lock, lock_raw = _load_json(lock_path, lock_logical)
    report, report_raw = _load_json(report_path, report_logical)
    report_sources = report.get("sources")
    if not isinstance(report_sources, Mapping):
        raise CFRUIdSpaceInventoryError("T01 report sources are invalid")
    expected_commits = resolved.get("expected_commits")
    if not isinstance(expected_commits, Mapping):
        raise CFRUIdSpaceInventoryError("policy.expected_commits must be a mapping")
    cfru_commit, cfru_tree = _source_identity(
        name="cfru",
        source_root=cfru_root,
        logical_root=cfru_logical,
        lock=lock,
        expected_commit=expected_commits.get("cfru"),
        report_sources=report_sources,
    )
    dpe_commit, dpe_tree = _source_identity(
        name="dpe",
        source_root=dpe_root,
        logical_root=dpe_logical,
        lock=lock,
        expected_commit=expected_commits.get("dpe"),
        report_sources=report_sources,
    )

    cfru_texts: dict[str, str] = {}
    cfru_raws: dict[str, bytes] = {}
    for relative in _CFRU_SOURCE_FILES:
        cfru_texts[relative], cfru_raws[relative] = _read_text(
            cfru_root / relative, f"{cfru_logical}/{relative}"
        )
    dpe_texts: dict[str, str] = {}
    dpe_raws: dict[str, bytes] = {}
    for relative in _DPE_SOURCE_FILES:
        dpe_texts[relative], dpe_raws[relative] = _read_text(
            dpe_root / relative, f"{dpe_logical}/{relative}"
        )

    rom_path, rom_logical, offsets_path, offsets_logical, build_row = _baseline_from_report(
        root, resolved, report
    )
    if rom_path.is_symlink() or not rom_path.is_file():
        raise CFRUIdSpaceInventoryError(f"baseline ROM missing/non-regular: {rom_logical}")
    rom = rom_path.read_bytes()
    if len(rom) != 32 * 1024 * 1024:
        raise CFRUIdSpaceInventoryError(f"baseline ROM size changed: {len(rom)}")
    rom_sha256 = _sha256(rom)
    expected_rom_sha256 = resolved.get("expected_baseline_sha256")
    if expected_rom_sha256 is not None and rom_sha256 != expected_rom_sha256:
        raise CFRUIdSpaceInventoryError(
            f"baseline ROM hash differs from policy: {rom_sha256} != {expected_rom_sha256}"
        )
    reported_rom_sha256 = build_row.get("output_sha256") if build_row else None
    if reported_rom_sha256 is not None and reported_rom_sha256 != rom_sha256:
        raise CFRUIdSpaceInventoryError("baseline ROM hash differs from T01 report")
    offsets_sha256 = _sha256_file(offsets_path)
    expected_offsets_sha256 = resolved.get("expected_offsets_sha256")
    if expected_offsets_sha256 is not None and offsets_sha256 != expected_offsets_sha256:
        raise CFRUIdSpaceInventoryError(
            "baseline offsets hash differs from policy: "
            f"{offsets_sha256} != {expected_offsets_sha256}"
        )
    reported_offsets_sha256 = build_row.get("offsets_sha256") if build_row else None
    if reported_offsets_sha256 is not None and reported_offsets_sha256 != offsets_sha256:
        raise CFRUIdSpaceInventoryError("baseline offsets hash differs from T01 report")
    offsets = _parse_offsets(offsets_path, offsets_logical)

    expected_counts = resolved.get("expected_counts")
    if not isinstance(expected_counts, Mapping):
        raise CFRUIdSpaceInventoryError("policy.expected_counts must be a mapping")
    counts: dict[str, int] = {}
    for key, fixed in EXPECTED_COUNTS.items():
        value = expected_counts.get(key)
        if not isinstance(value, int) or value != fixed:
            raise CFRUIdSpaceInventoryError(
                f"fixed {key} count policy changed: {value} != {fixed}"
            )
        counts[key] = value

    ability_constants, ability_aliases = _parse_constants(
        cfru_texts["include/constants/abilities.h"],
        "include/constants/abilities.h",
        "ABILITY_",
    )
    item_constants, item_aliases = _parse_constants(
        cfru_texts["include/constants/items.h"],
        "include/constants/items.h",
        "ITEM_",
    )
    tmhm_constants, _ = _parse_constants(
        cfru_texts["include/constants/tmshms.h"],
        "include/constants/tmshms.h",
        "ITEM_",
    )
    if len(tmhm_constants) != 58:
        raise CFRUIdSpaceInventoryError(
            f"TM/HM item alias count changed: {len(tmhm_constants)} != 58"
        )
    canonical_by_id: dict[int, str] = {}
    for symbol, row in item_constants.items():
        item_id = int(row["value"])
        if 0 <= item_id < counts["items"] and item_id not in canonical_by_id:
            canonical_by_id[item_id] = symbol
    tmhm_aliases: list[dict[str, Any]] = []
    for symbol, row in tmhm_constants.items():
        item_id = int(row["value"])
        target_symbol = canonical_by_id.get(item_id)
        if target_symbol is None or not 289 <= item_id <= 346:
            raise CFRUIdSpaceInventoryError(
                f"TM/HM item alias has invalid source ID: {symbol}={item_id}"
            )
        if symbol == target_symbol:
            continue
        tmhm_aliases.append(
            {
                "symbol": symbol,
                "target_symbol": target_symbol,
                "id": item_id,
                "source_ref": row["source_ref"],
            }
        )
    item_aliases.extend(tmhm_aliases)
    type_constants, type_aliases = _parse_constants(
        cfru_texts["include/constants/pokemon.h"],
        "include/constants/pokemon.h",
        "TYPE_",
    )
    dpe_ability_constants, _ = _parse_constants(
        dpe_texts["include/abilities.h"], "include/abilities.h", "ABILITY_"
    )
    dpe_item_constants, _ = _parse_constants(
        dpe_texts["include/items.h"], "include/items.h", "ITEM_"
    )
    dpe_type_constants, _ = _parse_constants(
        dpe_texts["include/base_stats.h"], "include/base_stats.h", "TYPE_"
    )

    ability_names = _parse_org_sequence(
        cfru_texts["strings/ability_name_table.string"],
        "strings/ability_name_table.string",
        "gAbilityNames",
    )
    type_names = _parse_org_sequence(
        cfru_texts["strings/type_names.string"],
        "strings/type_names.string",
        "gTypeNames",
    )
    ability_description_words = _parse_word_rows(
        cfru_texts["assembly/data/ability_description_table.s"],
        "assembly/data/ability_description_table.s",
        "gAbilityDescriptions",
    )
    ratings, rating_refs = _parse_ability_ratings(
        cfru_texts["src/ability_battle_effects.c"],
        "src/ability_battle_effects.c",
        ability_constants,
        counts["abilities"],
    )
    item_records = _parse_item_records(
        cfru_texts["src/Tables/item_tables.c"], "src/Tables/item_tables.c"
    )
    item_icons = _parse_item_icons(
        cfru_texts["src/Tables/item_tables.c"], "src/Tables/item_tables.c"
    )
    item_types, item_type_definitions = _parse_item_types(
        enum_text=cfru_texts["include/new/item.h"],
        enum_path="include/new/item.h",
        table_text=cfru_texts["src/Tables/item_tables.c"],
        table_path="src/Tables/item_tables.c",
        item_constants=item_constants,
        expected_count=counts["items"],
    )
    tera_type_colors = _parse_tera_type_colors(
        cfru_texts["src/terastal.c"], "src/terastal.c", counts["types"]
    )
    charmap_sha256 = _sha256(cfru_raws["charmap.tbl"])
    expected_charmap_sha256 = resolved.get("expected_charmap_sha256")
    if expected_charmap_sha256 is not None and charmap_sha256 != expected_charmap_sha256:
        raise CFRUIdSpaceInventoryError(
            "CFRU charmap hash differs from policy: "
            f"{charmap_sha256} != {expected_charmap_sha256}"
        )
    charmap = _parse_charmap(cfru_texts["charmap.tbl"])

    types = _build_types(
        constants=type_constants,
        dpe_constants=dpe_type_constants,
        names=type_names,
        display_colors=tera_type_colors,
        type_asm=cfru_texts["assembly/data/type_tables.s"],
        type_asm_path="assembly/data/type_tables.s",
        type_table_text=cfru_texts["src/Tables/type_tables.h"],
        type_table_path="src/Tables/type_tables.h",
        rom=rom,
        offsets=offsets,
        expected_count=counts["types"],
    )
    abilities = _build_abilities(
        constants=ability_constants,
        dpe_constants=dpe_ability_constants,
        names=ability_names,
        description_words=ability_description_words,
        ratings=ratings,
        rating_refs=rating_refs,
        rom=rom,
        offsets=offsets,
        charmap=charmap,
        expected_count=counts["abilities"],
    )
    items, item_anomalies = _build_items(
        constants=item_constants,
        dpe_constants=dpe_item_constants,
        records=item_records,
        icons=item_icons,
        item_types=item_types,
        rom=rom,
        offsets=offsets,
        charmap=charmap,
        expected_count=counts["items"],
    )
    aliases = [
        {"space": space, **row}
        for space, rows in (
            ("type", type_aliases),
            ("ability", ability_aliases),
            ("item", item_aliases),
        )
        for row in rows
    ]

    cfru_file_hashes = {
        relative: _sha256(cfru_raws[relative]) for relative in sorted(cfru_raws)
    }
    dpe_file_hashes = {
        relative: _sha256(dpe_raws[relative]) for relative in sorted(dpe_raws)
    }
    source_bundle_hashes = {
        "cfru": _stable_sha256(cfru_file_hashes),
        "dpe": _stable_sha256(dpe_file_hashes),
    }
    expected_source_hashes = resolved.get("expected_source_bundle_sha256")
    if not isinstance(expected_source_hashes, Mapping):
        raise CFRUIdSpaceInventoryError(
            "policy.expected_source_bundle_sha256 must be a mapping"
        )
    for source_name, actual_hash in source_bundle_hashes.items():
        if expected_source_hashes.get(source_name) != actual_hash:
            raise CFRUIdSpaceInventoryError(
                f"{source_name} source bundle hash differs from policy: "
                f"{actual_hash} != {expected_source_hashes.get(source_name)}"
            )
    fingerprint = report.get("fingerprint")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise CFRUIdSpaceInventoryError("T01 fingerprint is invalid")
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine": "CFRU-JP",
        "counts": counts,
        "item_type_contract": {
            "definition_count": len(item_type_definitions),
            "explicit_item_count": sum(row["item_type_explicit"] for row in item_types),
            "evolution_stone_count": sum(row["is_evolution_stone"] for row in item_types),
            "evolution_item_count": sum(row["is_evolution_item"] for row in item_types),
            "definitions": item_type_definitions,
        },
        "sources": {
            "cfru": {
                "path": cfru_logical,
                "commit": cfru_commit,
                "tree": cfru_tree,
                "source_bundle_sha256": source_bundle_hashes["cfru"],
                "files": cfru_file_hashes,
            },
            "dpe": {
                "path": dpe_logical,
                "commit": dpe_commit,
                "tree": dpe_tree,
                "source_bundle_sha256": source_bundle_hashes["dpe"],
                "files": dpe_file_hashes,
            },
        },
        "source_lock": {"path": lock_logical, "sha256": _sha256(lock_raw)},
        "t01_baseline": {
            "report_path": report_logical,
            "report_sha256": _sha256(report_raw),
            "fingerprint": fingerprint,
            "profile": resolved["baseline"].get("profile", "baseline"),
            "run": resolved["baseline"].get("run", 1),
            "rom_path": rom_logical,
            "rom_size": len(rom),
            "rom_sha256": rom_sha256,
            "offsets_path": offsets_logical,
            "offsets_sha256": offsets_sha256,
            "symbols": {symbol: _hex_address(offsets[symbol]) for symbol in _BASELINE_SYMBOLS},
        },
        "type_effectiveness_scale": {
            "no_effect": 1,
            "not_effective": 500,
            "normal": 1000,
            "super_effective": 2000,
            "compiled_no_data": 0,
            "logical_no_data_normalized_to": 1000,
        },
        "anomalies": item_anomalies,
    }
    result: dict[str, Any] = {
        "metadata": metadata,
        "types": types,
        "abilities": abilities,
        "items": items,
        "aliases": aliases,
    }
    metadata["inventory_sha256"] = _stable_sha256(
        {
            "metadata": {key: value for key, value in metadata.items() if key != "inventory_sha256"},
            "types": types,
            "abilities": abilities,
            "items": items,
            "aliases": aliases,
        }
    )
    # JSON互換性を最後に明示検査する。default=strで欠陥を隠さない。
    json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--policy", type=Path, help="policy JSON（cfru section形式も可）")
    parser.add_argument("--pretty", action="store_true", help="indent付きJSONを表示")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    policy: Mapping[str, Any] | None = None
    try:
        if args.policy is not None:
            loaded = json.loads(args.policy.read_text(encoding="utf-8"))
            if not isinstance(loaded, Mapping):
                raise CFRUIdSpaceInventoryError("policy JSON root must be an object")
            policy = loaded
        result = extract_cfru_id_spaces(args.root, policy)
    except (CFRUIdSpaceInventoryError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
