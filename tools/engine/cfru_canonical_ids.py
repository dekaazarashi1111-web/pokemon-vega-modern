"""固定CFRUのSpecies/Ability名前空間をVega canonical IDへ接続する。"""

from __future__ import annotations

import csv
import hashlib
import re
import struct
from pathlib import Path
from typing import Any, Mapping


ROM_BASE = 0x08000000
PAYLOAD_BASE = 0x09000000
PAYLOAD_CAPACITY = 0x200000
CANONICAL_SPECIES_COUNT = 1621
CANONICAL_ABILITY_COUNT = 312

_DEFINE_RE = re.compile(
    r"^#define\s+((?:SPECIES|ABILITY)_[A-Z0-9_]+)\s+"
    r"(0x[0-9A-Fa-f]+|\d+)\s*$",
    re.MULTILINE,
)
_EQU_RE = re.compile(
    r"^\s*\.equ\s+((?:SPECIES|ABILITY)_[A-Z0-9_]+)\s*,\s*"
    r"(0x[0-9A-Fa-f]+|\d+)\s*$",
    re.MULTILINE,
)
_TOKEN_RE = re.compile(r"\b(?:SPECIES|ABILITY)_[A-Z0-9_]+\b")
_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\r\n]*", re.DOTALL)
_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')

_SPECIAL_TOKENS = {
    "SPECIES_TABLES_TERMIN",
    "ABILITY_TABLES_TERMIN",
    # Non-ID macros/resources whose historical names share the ID prefixes.
    "ABILITY_NAME_LENGTH",
    "ABILITY_ON_FIELD",
    "ABILITY_ON_OPPOSING_FIELD",
    "ABILITY_POP_UP_IMG",
    "ABILITY_POP_UP_PAL",
    "ABILITY_POP_UP_POS_X_DIFF",
    "ABILITY_POP_UP_POS_X_SLIDE",
    "ABILITY_PRESENT",
    "ABILITY_PREVENTING_ESCAPE",
}
_SOURCE_INDEXED_TABLE = "src/Tables/music_tables.c"


class CanonicalIdCompatibilityError(ValueError):
    """manifest、vendor定数、consumer、またはlinked tableが契約外である。"""


def _fail(message: str) -> None:
    raise CanonicalIdCompatibilityError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_manifest(
    path: Path,
    *,
    source_column: str,
    expected_count: int,
) -> tuple[list[dict[str, str]], dict[int, int]]:
    if path.is_symlink() or not path.is_file():
        _fail(f"canonical ID manifest is missing/nonregular: {path}")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != expected_count:
        _fail(
            f"canonical ID manifest row count differs: {path}: "
            f"{len(rows)} != {expected_count}"
        )
    canonical = [int(row["id"]) for row in rows]
    if canonical != list(range(expected_count)):
        _fail(f"canonical IDs are not contiguous/ordered: {path}")
    source_to_canonical: dict[int, int] = {}
    for row in rows:
        raw = row.get(source_column, "")
        if not raw or not raw.isdigit():
            continue
        source_id = int(raw)
        canonical_id = int(row["id"])
        previous = source_to_canonical.setdefault(source_id, canonical_id)
        if previous != canonical_id:
            _fail(
                f"source ID maps to multiple canonical IDs: "
                f"{source_column}={source_id}"
            )
    return rows, source_to_canonical


def _read_vendor_constants(path: Path, prefix: str) -> dict[str, int]:
    if path.is_symlink() or not path.is_file():
        _fail(f"vendor constant header is missing/nonregular: {path}")
    result = {
        name: int(raw, 0)
        for name, raw in _DEFINE_RE.findall(path.read_text(encoding="utf-8"))
        if name.startswith(prefix + "_")
    }
    if not result:
        _fail(f"vendor constant header yielded no {prefix} definitions: {path}")
    return result


def _read_assembly_constants(path: Path, prefix: str) -> dict[str, int]:
    if path.is_symlink() or not path.is_file():
        _fail(f"vendor assembly definitions are missing/nonregular: {path}")
    return {
        name: int(raw, 0)
        for name, raw in _EQU_RE.findall(path.read_text(encoding="utf-8"))
        if name.startswith(prefix + "_")
    }


def _merge_constants(*groups: Mapping[str, int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for group in groups:
        for name, value in group.items():
            previous = result.setdefault(name, value)
            if previous != value:
                _fail(f"vendor constant differs between C/assembly: {name}")
    return result


def _constant_aliases(
    constants: Mapping[str, int],
    source_to_canonical: Mapping[int, int],
    label: str,
) -> dict[str, int]:
    missing = sorted(
        (name, source_id)
        for name, source_id in constants.items()
        if source_id not in source_to_canonical
    )
    if missing:
        _fail(f"{label} vendor constants lack manifest mappings: {missing[:8]}")
    aliases = {
        name: source_to_canonical[source_id]
        for name, source_id in constants.items()
    }
    return aliases


def _render_species_alias_header(aliases: Mapping[str, int]) -> str:
    lines = [
        "#ifndef POKEMON_VEGA_T06_SPECIES_ALIASES_H",
        "#define POKEMON_VEGA_T06_SPECIES_ALIASES_H",
        "",
        "/* manifest generated: source Species namespace -> Vega canonical */",
        "#ifndef VEGA_KEEP_SOURCE_SPECIES_IDS",
    ]
    for name, value in sorted(aliases.items(), key=lambda item: (item[1], item[0])):
        lines.extend(
            (
                f"#ifdef {name}",
                f"#undef {name}",
                "#endif",
                f"#define {name} {value}u",
            )
        )
    lines.extend(
        (
            "#ifdef NUM_SPECIES",
            "#undef NUM_SPECIES",
            "#endif",
            f"#define NUM_SPECIES {CANONICAL_SPECIES_COUNT}u",
            "#endif /* VEGA_KEEP_SOURCE_SPECIES_IDS */",
            "",
            "#endif /* POKEMON_VEGA_T06_SPECIES_ALIASES_H */",
            "",
        )
    )
    return "\n".join(lines)


def _tokens(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="strict")
    text = _COMMENT_RE.sub("", text)
    text = _STRING_RE.sub("", text)
    return _TOKEN_RE.findall(text)


def _consumer_inventory(
    tree: Path,
    species_constants: Mapping[str, int],
    ability_constants: Mapping[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = list((tree / "src").rglob("*.c"))
    paths.extend((tree / "src").rglob("*.h"))
    paths.extend((tree / "assembly").rglob("*.s"))
    paths.extend(tree / name for name in ("asm_defines.s", "xse_defines.s", "special_inserts.asm"))
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink():
            _fail(f"CFRU consumer is missing/nonregular: {path}")
        tokens = _tokens(path)
        if not tokens:
            continue
        species = sorted({token for token in tokens if token.startswith("SPECIES_")})
        abilities = sorted({token for token in tokens if token.startswith("ABILITY_")})
        unknown = sorted(
            token
            for token in set(tokens)
            if token not in species_constants
            and token not in ability_constants
            and token not in _SPECIAL_TOKENS
        )
        if unknown:
            logical = path.relative_to(tree).as_posix()
            _fail(f"unmapped CFRU Species/Ability consumer: {logical}: {unknown}")
        logical = path.relative_to(tree).as_posix()
        if logical == _SOURCE_INDEXED_TABLE:
            classification = "SOURCE_INDEXED_POSTLINK_CANONICALIZED"
        elif logical.startswith("assembly/") or logical.endswith(".asm") or logical in {
            "asm_defines.s",
            "xse_defines.s",
        }:
            classification = "ASSEMBLY_EQU_CANONICAL"
        else:
            classification = "C_PREPROCESSOR_CANONICAL"
        rows.append(
            {
                "path": logical,
                "classification": classification,
                "species_occurrences": sum(token.startswith("SPECIES_") for token in tokens),
                "species_symbols": len(species),
                "ability_occurrences": sum(token.startswith("ABILITY_") for token in tokens),
                "ability_symbols": len(abilities),
            }
        )
    if not rows:
        _fail("CFRU Species/Ability consumer inventory is empty")
    return rows


def install_canonical_id_compatibility(
    root: Path,
    tree: Path,
    generated_aliases: Mapping[str, int],
) -> tuple[dict[str, int], dict[str, Any]]:
    """sandbox sourceへSpecies aliasesを導入し、Ability aliasesも全件監査する。"""

    species_rows, species_by_source = _read_manifest(
        root / "manifests/species_ids.csv",
        source_column="dpe_id",
        expected_count=CANONICAL_SPECIES_COUNT,
    )
    ability_rows, ability_by_source = _read_manifest(
        root / "manifests/ability_ids.csv",
        source_column="cfru_id",
        expected_count=CANONICAL_ABILITY_COUNT,
    )
    species_header = tree / "include/constants/species.h"
    ability_header = tree / "include/constants/abilities.h"
    species_header_constants = _read_vendor_constants(species_header, "SPECIES")
    ability_header_constants = _read_vendor_constants(ability_header, "ABILITY")
    species_constants = _merge_constants(
        species_header_constants,
        _read_assembly_constants(tree / "asm_defines.s", "SPECIES"),
        _read_assembly_constants(tree / "xse_defines.s", "SPECIES"),
    )
    ability_constants = _merge_constants(
        ability_header_constants,
        _read_assembly_constants(tree / "asm_defines.s", "ABILITY"),
        _read_assembly_constants(tree / "xse_defines.s", "ABILITY"),
    )
    species_aliases = _constant_aliases(
        species_constants, species_by_source, "Species"
    )
    ability_aliases = _constant_aliases(
        ability_constants, ability_by_source, "Ability"
    )
    supplied_ability_aliases = {
        name: int(generated_aliases[name])
        for name in ability_header_constants
        if name in generated_aliases
    }
    expected_generated_ability_aliases = {
        name: ability_aliases[name] for name in ability_header_constants
    }
    if supplied_ability_aliases != expected_generated_ability_aliases:
        missing = sorted(
            set(expected_generated_ability_aliases) - set(supplied_ability_aliases)
        )
        differing = sorted(
            name
            for name in set(expected_generated_ability_aliases)
            & set(supplied_ability_aliases)
            if supplied_ability_aliases[name]
            != expected_generated_ability_aliases[name]
        )
        _fail(
            "generated Ability aliases do not cover the fixed CFRU header: "
            f"missing={missing[:8]} differing={differing[:8]}"
        )

    inventory = _consumer_inventory(tree, species_constants, ability_constants)
    integration = tree / "integration"
    integration.mkdir(exist_ok=True)
    rendered = _render_species_alias_header(species_aliases)
    (integration / "species_aliases.h").write_text(
        rendered, encoding="utf-8", newline="\n"
    )
    with species_header.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write('\n#include "../../integration/species_aliases.h"\n')

    # This one active table is Species-indexed and must retain its linked size
    # so all established CFRU symbols stay stable.  Its rows are rebuilt and
    # repointed after link by canonicalize_linked_species_tables().
    music = tree / _SOURCE_INDEXED_TABLE
    music.write_text(
        "#define VEGA_KEEP_SOURCE_SPECIES_IDS 1\n"
        + music.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )

    species_mismatches = sum(
        source_id != species_by_source[source_id]
        for source_id in species_by_source
    )
    ability_mismatches = sum(
        source_id != ability_by_source[source_id]
        for source_id in ability_by_source
    )
    report = {
        "schema_version": 1,
        "status": "PREPARED",
        "species": {
            "canonical_rows": len(species_rows),
            "source_constants": len(species_constants),
            "source_header_constants": len(species_header_constants),
            "source_ids_mapped": len(species_by_source),
            "numeric_mismatches": species_mismatches,
            "alias_header_sha256": _sha256(rendered.encode("utf-8")),
            "canonical_count": CANONICAL_SPECIES_COUNT,
        },
        "abilities": {
            "canonical_rows": len(ability_rows),
            "source_constants": len(ability_constants),
            "source_header_constants": len(ability_header_constants),
            "source_ids_mapped": len(ability_by_source),
            "numeric_mismatches": ability_mismatches,
            "generated_aliases_verified": len(supplied_ability_aliases),
            "canonical_count": CANONICAL_ABILITY_COUNT,
        },
        "consumers": {
            "files": len(inventory),
            "species_occurrences": sum(row["species_occurrences"] for row in inventory),
            "ability_occurrences": sum(row["ability_occurrences"] for row in inventory),
            "unmapped": 0,
            "rows": inventory,
        },
        "source_indexed_tables": [_SOURCE_INDEXED_TABLE],
    }
    return {**species_aliases, **ability_aliases}, report


def _find_all(raw: bytes | bytearray, needle: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        offset = raw.find(needle, start)
        if offset < 0:
            return result
        result.append(offset)
        start = offset + 1


def canonicalize_linked_species_tables(
    root: Path,
    rom: bytes,
    payload: bytes,
    offsets: Mapping[str, int],
) -> tuple[bytes, bytes, dict[str, Any]]:
    """既存symbol配置を変えずactive Species-indexed tableをcanonical化する。"""

    _, species_by_source = _read_manifest(
        root / "manifests/species_ids.csv",
        source_column="dpe_id",
        expected_count=CANONICAL_SPECIES_COUNT,
    )
    table_symbol = "gWildSpeciesBasedBattleBGM"
    length_symbol = "gWildSpeciesBasedBattleBGMLength"
    if table_symbol not in offsets or length_symbol not in offsets:
        _fail("linked Species-indexed music symbols are missing")
    old_address = int(offsets[table_symbol])
    length_address = int(offsets[length_symbol])
    old_offset = old_address - ROM_BASE
    length_offset = length_address - ROM_BASE
    if old_offset < 0 or length_offset < 0 or max(old_offset, length_offset) >= len(rom):
        _fail("linked Species-indexed music symbols are outside ROM")
    source_count = struct.unpack_from("<H", rom, length_offset)[0]
    if source_count <= 0 or source_count > max(species_by_source) + 1:
        _fail(f"linked Species-indexed music length is invalid: {source_count}")
    source = struct.unpack_from(f"<{source_count}H", rom, old_offset)
    canonical = [0] * CANONICAL_SPECIES_COUNT
    nonzero = 0
    for source_id, song in enumerate(source):
        if song == 0:
            continue
        canonical_id = species_by_source.get(source_id)
        if canonical_id is None:
            _fail(
                "nonzero Species-indexed music row lacks manifest mapping: "
                f"source={source_id} song={song}"
            )
        if canonical[canonical_id] not in (0, song):
            _fail(f"canonical Species-indexed music row collides: {canonical_id}")
        canonical[canonical_id] = song
        nonzero += 1
    canonical_raw = struct.pack(f"<{len(canonical)}H", *canonical)
    payload_out = bytearray(payload)
    alignment = (-len(payload_out)) & 3
    payload_out.extend(b"\0" * alignment)
    new_payload_offset = len(payload_out)
    new_address = PAYLOAD_BASE + new_payload_offset
    payload_out.extend(canonical_raw)
    if len(payload_out) > PAYLOAD_CAPACITY:
        _fail(
            f"canonical Species-indexed music table overflows payload: "
            f"{len(payload_out):#x} > {PAYLOAD_CAPACITY:#x}"
        )
    pointer_sites = _find_all(payload_out[:new_payload_offset], struct.pack("<I", old_address))
    if not pointer_sites:
        _fail("linked Species-indexed music table has no pointer consumers")
    for site in pointer_sites:
        struct.pack_into("<I", payload_out, site, new_address)
    length_payload_offset = length_address - PAYLOAD_BASE
    if length_payload_offset < 0 or length_payload_offset + 2 > new_payload_offset:
        _fail("Species-indexed music length is outside CFRU payload")
    struct.pack_into("<H", payload_out, length_payload_offset, CANONICAL_SPECIES_COUNT)

    rom_out = bytearray(rom)
    rom_payload_offset = PAYLOAD_BASE - ROM_BASE
    if rom_payload_offset + len(payload_out) > len(rom_out):
        _fail("canonical Species-indexed music payload exceeds ROM")
    rom_out[rom_payload_offset : rom_payload_offset + len(payload_out)] = payload_out
    report = {
        "status": "CANONICAL",
        "table": table_symbol,
        "source_address": old_address,
        "source_count": source_count,
        "canonical_address": new_address,
        "canonical_count": CANONICAL_SPECIES_COUNT,
        "canonical_sha256": _sha256(canonical_raw),
        "nonzero_rows": nonzero,
        "pointer_sites": [PAYLOAD_BASE + site for site in pointer_sites],
        "payload_alignment": alignment,
        "payload_size_before": len(payload),
        "payload_size_after": len(payload_out),
    }
    return bytes(rom_out), bytes(payload_out), report
