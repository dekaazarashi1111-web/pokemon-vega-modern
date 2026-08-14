#!/usr/bin/env python3
"""T07: Vega IDを固定し、DPE Speciesをcanonical tableとROM stageへ統合する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.engine.extract_vega_id_spaces import _decode_terminated, _read_charmap  # noqa: E402
from tools.engine.extract_vega_species import (  # noqa: E402
    VegaSpeciesExtractionError,
    extract_vega_species,
)
from scripts.fast_stage_reuse import trusted_stage_sha  # noqa: E402


ROM_BASE = 0x08000000
TASK_ID = "T07"
CONFIG_PATH = Path("config/species_port.json")
GENERATED_ROOT = Path("generated/engine/species")
REPORT_PATH = Path("reports/generated/species_port.md")
MANIFEST_PATH = Path("manifests/species_ids.csv")
SCHEMA_VERSION = 1


def _expected_stage06_sha(root: Path, inputs: Mapping[str, Any]) -> str:
    return trusted_stage_sha(
        root,
        Path(str(inputs["stage06_path"])),
        Path(str(inputs["stage06_metadata_path"])),
        "T06",
        str(inputs["stage06_sha256"]),
    )

MANIFEST_HEADER = (
    "species_key", "id", "vega_id", "dpe_id", "dpe_symbol", "classification",
    "display_name", "form_key", "is_official", "canonical_national_dex",
    "review_state", "status", "notes",
)

ARTIFACT_PATHS = (
    "generated/engine/species/species_port.json",
    "generated/engine/species/species_generated.h",
    "generated/engine/species/base_stats.bin",
    "generated/engine/species/species_names.bin",
    "generated/engine/species/national_dex.bin",
    "generated/engine/species/dpe_aliases.json",
    "generated/engine/species/reference_validation.json",
    "generated/engine/species/official_species_count.c",
    "manifests/species_ids.csv",
    "reports/generated/species_port.md",
)

FINGERPRINT_FILES = (
    "config/species_port.json", "scripts/build_species_port.py",
    "tools/engine/extract_vega_species.py", "tools/mgba_species_smoke.c",
    "scripts/validate_manifests.py", "manifests/id_ranges.csv",
    "tests/test_extract_vega_species.py", "tests/test_build_species_port.py",
    "generated/engine/ids/id_spaces.json", "reports/generated/id_inventory.json",
    "build/stages/06_battle_core.json", "vendor/upstream/DPE-JP/include/species.h",
    "vendor/upstream/DPE-JP/strings/Pokemon_Name_Table.string",
    "state/source-lock.json", "infra/toolchain_manifest.json",
)


class SpeciesPortError(RuntimeError):
    """固定入力、mapping、runtime table、reference、またはsmokeの違反。"""


def _fail(message: str) -> NoReturn:
    raise SpeciesPortError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: object, *, pretty: bool = True) -> bytes:
    separators = None if pretty else (",", ":")
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None,
                       separators=separators) + "\n").encode("utf-8")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"cannot read {label}: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} root must be an object")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label} must be an integer")
    return value


def _normal(name: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", name) if not c.isspace())


def _symbol_key(symbol: str) -> str:
    return "SPECIES_KEY_" + symbol.removeprefix("SPECIES_")


def _logical(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        _fail(f"{label} must be a relative path")
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        _fail(f"{label} escapes repository root")
    return path


def _fixed_bytes(root: Path, path_value: object, expected: object, label: str) -> bytes:
    path = _logical(root, path_value, label)
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"cannot read {label}: {error}")
    if _sha256(raw) != expected:
        _fail(f"{label} SHA-256 mismatch")
    return raw


def _parse_dpe_symbols(root: Path, count: int) -> tuple[dict[int, str], list[dict[str, Any]], set[int]]:
    path = root / "vendor/upstream/DPE-JP/include/species.h"
    text = path.read_text(encoding="utf-8")
    by_id: dict[int, list[str]] = defaultdict(list)
    for match in re.finditer(
        r"^#define\s+(SPECIES_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*$", text, re.M
    ):
        value = int(match.group(2), 0)
        if 0 <= value < count:
            by_id[value].append(match.group(1))
    defined_ids = set(by_id)
    primary: dict[int, str] = {}
    aliases: list[dict[str, Any]] = []
    for species_id in range(count):
        if species_id not in by_id:
            primary[species_id] = f"SPECIES_DPE_RESERVED_{species_id:04d}"
            continue
        symbols = by_id[species_id]
        chosen = symbols[-1] if species_id == 83 else symbols[0]
        primary[species_id] = chosen
        aliases.extend(
            {"source_id": species_id, "source_symbol": symbol, "primary": symbol == chosen}
            for symbol in symbols
        )
    return primary, aliases, defined_ids


def extract_dpe_species(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    policy = config.get("dpe")
    charmap_policy = config.get("charmap")
    if not isinstance(policy, Mapping) or not isinstance(charmap_policy, Mapping):
        _fail("dpe/charmap policy is missing")
    rom = _fixed_bytes(root, policy.get("rom_path"), policy.get("rom_sha256"), "DPE ROM")
    offsets = _fixed_bytes(root, policy.get("offsets_path"), policy.get("offsets_sha256"), "DPE offsets")
    offsets_text = offsets.decode("utf-8")
    count = _integer(policy.get("species_count"), "dpe.species_count")
    name_address = _integer(policy.get("name_address"), "dpe.name_address")
    stats_address = _integer(policy.get("base_stats_address"), "dpe.base_stats_address")
    dex_address = _integer(policy.get("national_dex_address"), "dpe.national_dex_address")
    name_stride = _integer(policy.get("name_stride"), "dpe.name_stride")
    stats_stride = _integer(policy.get("base_stats_stride"), "dpe.base_stats_stride")
    dex_count = _integer(policy.get("national_dex_count"), "dpe.national_dex_count")
    if (count, name_stride, stats_stride, dex_count) != (1440, 8, 32, 1439):
        _fail("DPE Species count/table ABI changed")
    for symbol, address in (
        ("gSpeciesNames", name_address), ("gBaseStats", stats_address),
        ("gSpeciesToNationalPokedexNum", dex_address),
    ):
        pattern = rf"^{symbol}:\s+{address:08X}\s*$"
        if not re.search(pattern, offsets_text, re.M):
            _fail(f"DPE offsets root changed for {symbol}")

    def table(address: int, size: int, expected: object, label: str) -> bytes:
        offset = address - ROM_BASE
        raw = rom[offset:offset + size]
        if len(raw) != size or _sha256(raw) != expected:
            _fail(f"DPE {label} table SHA-256/size mismatch")
        return raw

    names = table(name_address, count * name_stride, policy.get("name_table_sha256"), "name")
    stats = table(stats_address, count * stats_stride, policy.get("base_stats_sha256"), "BaseStats")
    dex = table(dex_address, dex_count * 2, policy.get("national_dex_sha256"), "national dex")
    charmap, charmap_meta = _read_charmap(
        root, {"logical_path": charmap_policy.get("path"), "sha256": charmap_policy.get("sha256")}
    )
    symbols, symbol_aliases, defined_ids = _parse_dpe_symbols(root, count)
    rows: list[dict[str, Any]] = []
    for source_id in range(count):
        raw_name = names[source_id * name_stride:(source_id + 1) * name_stride]
        display_name, encoded_length = _decode_terminated(raw_name, charmap, f"DPE Species {source_id} name")
        national = 0 if source_id == 0 else int.from_bytes(dex[(source_id - 1) * 2:source_id * 2], "little")
        rows.append({
            "source_id": source_id, "symbol": symbols[source_id],
            "is_defined": source_id in defined_ids,
            "display_name": display_name, "name_encoded_length": encoded_length,
            "canonical_national_dex": national,
            "base_stats_raw_hex": stats[source_id * stats_stride:(source_id + 1) * stats_stride].hex(),
        })
    return {
        "schema_version": 1, "source": "DPE_FIXED_BUILD", "count": count,
        "rows": rows, "symbol_aliases": symbol_aliases,
        "defined_ids": sorted(defined_ids), "defined_count": len(defined_ids),
        "provenance": {
            "commit": policy.get("commit"), "rom_sha256": policy.get("rom_sha256"),
            "offsets_sha256": policy.get("offsets_sha256"), "charmap": charmap_meta,
        },
    }


def _source_alias_map(id_model: Mapping[str, Any], domain: str) -> dict[int, int]:
    key = domain + "_aliases"
    rows = id_model.get(key)
    if not isinstance(rows, list):
        _fail(f"T05 {key} is missing")
    result: dict[int, int] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            _fail(f"T05 {key} row is invalid")
        source_id = _integer(row.get("source_id"), f"{key}.source_id")
        canonical_id = _integer(row.get("canonical_id"), f"{key}.canonical_id")
        previous = result.setdefault(source_id, canonical_id)
        if previous != canonical_id:
            _fail(f"T05 {domain} source ID maps to multiple canonical IDs: {source_id}")
    return result


def _translate_dpe_stats(raw: bytes, abilities: Mapping[int, int], items: Mapping[int, int]) -> bytes:
    if len(raw) != 32:
        _fail("DPE BaseStats row size changed")
    output = bytearray(raw)
    for offset in (12, 14):
        source = int.from_bytes(raw[offset:offset + 2], "little")
        if source not in items:
            _fail(f"unresolved DPE held-item source ID {source}")
        output[offset:offset + 2] = struct.pack("<H", items[source])
    for offset in (22, 26, 28):
        source = int.from_bytes(raw[offset:offset + 2], "little")
        if source not in abilities:
            _fail(f"unresolved DPE ability source ID {source}")
        output[offset:offset + 2] = struct.pack("<H", abilities[source])
    return bytes(output)


def _collect_species_values(value: object, *, key: str = "") -> list[int]:
    result: list[int] = []
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            name = str(child_key)
            if name in {"species", "target_species", "species_id"} and isinstance(child, int):
                result.append(child)
            else:
                result.extend(_collect_species_values(child, key=name))
    elif isinstance(value, list):
        for child in value:
            result.extend(_collect_species_values(child, key=key))
    return result


def validate_existing_references(
    inventory: Mapping[str, Any], stage06: bytes, stage06_meta: Mapping[str, Any]
) -> dict[str, Any]:
    sources: dict[str, list[int]] = {}
    trainer = inventory.get("trainer_contract")
    if isinstance(trainer, Mapping):
        refs = trainer.get("referenced_ids")
        if isinstance(refs, Mapping) and isinstance(refs.get("species"), list):
            sources["trainer_parties"] = [int(value) for value in refs["species"]]
    encounter = inventory.get("encounter_details")
    sources["wild_tables"] = _collect_species_values(encounter)
    scripts = inventory.get("script_references")
    if isinstance(scripts, list):
        species_rows = [row for row in scripts if isinstance(row, Mapping) and row.get("category") == "species"]
        sources["scripts_and_gifts"] = [int(row["value"]) for row in species_rows if isinstance(row.get("value"), int)]

    runtime = stage06_meta.get("runtime_tables")
    if not isinstance(runtime, Mapping) or not isinstance(runtime.get("evolutions"), Mapping):
        _fail("T06 evolution runtime metadata is missing")
    evo = runtime["evolutions"]
    address = _integer(evo.get("address"), "T06 evolution address") - ROM_BASE
    count = _integer(evo.get("count"), "T06 evolution count")
    stride = _integer(evo.get("stride"), "T06 evolution stride")
    evolution_targets: list[int] = []
    for species in range(412):
        for row_index in range(16):
            method, _param, target, _unknown = struct.unpack_from(
                "<HHHH", stage06, address + species * stride + row_index * 8
            )
            if method:
                evolution_targets.append(target)
    sources["evolutions"] = evolution_targets
    summary: dict[str, Any] = {}
    for label, values in sources.items():
        unique = sorted(set(values))
        invalid = [value for value in unique if not 0 <= value < 412]
        if invalid:
            _fail(f"existing {label} contains unresolved Species IDs: {invalid[:8]}")
        summary[label] = {"reference_count": len(values), "unique_ids": unique, "status": "PASS"}
    return {"status": "PASS", "frozen_range": [0, 411], "sources": summary}


def build_species_model(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if config.get("schema_version") != 1 or config.get("task") != TASK_ID:
        _fail("species config schema/task mismatch")
    policy = config.get("mapping_policy")
    inputs = config.get("inputs")
    if not isinstance(policy, Mapping) or not isinstance(inputs, Mapping):
        _fail("mapping/input policy missing")
    if policy.get("automatic_identity") != "UNIQUE_NFKC_DISPLAY_NAME_TO_PRIMARY_NATIONAL_FORM":
        _fail("automatic Species identity policy changed")
    if policy.get("reuse_frozen_holes") is not False or policy.get("append_start") != 412:
        _fail("Vega frozen Species range policy changed")

    vega = extract_vega_species(root, config)
    dpe = extract_dpe_species(root, config)
    stage06 = _fixed_bytes(
        root, inputs.get("stage06_path"),
        _expected_stage06_sha(root, inputs), "T06 stage",
    )
    stage06_meta = _read_json(_logical(root, inputs.get("stage06_metadata_path"), "T06 metadata"), "T06 metadata")
    id_model = _read_json(_logical(root, inputs.get("id_spaces_path"), "T05 model"), "T05 model")
    inventory = _read_json(_logical(root, inputs.get("id_inventory_path"), "T02 inventory"), "T02 inventory")
    abilities = _source_alias_map(id_model, "ability")
    items = _source_alias_map(id_model, "item")

    runtime = stage06_meta.get("runtime_tables")
    if not isinstance(runtime, Mapping) or not isinstance(runtime.get("base_stats"), Mapping):
        _fail("T06 BaseStats metadata missing")
    old = runtime["base_stats"]
    old_address = _integer(old.get("address"), "T06 BaseStats address")
    if old_address != config["runtime"]["old_base_stats_address"] or old.get("count") != 412 or old.get("stride") != 32:
        _fail("T06 frozen BaseStats ABI changed")
    frozen_stats = stage06[old_address - ROM_BASE:old_address - ROM_BASE + 412 * 32]
    if len(frozen_stats) != 412 * 32 or _sha256(frozen_stats) != old.get("sha256"):
        _fail("T06 frozen BaseStats bytes differ")

    dpe_rows = list(dpe["rows"])
    primary_by_national: dict[int, int] = {}
    for row in dpe_rows:
        if not row["is_defined"]:
            continue
        national = row["canonical_national_dex"]
        if national > 0:
            primary_by_national.setdefault(national, row["source_id"])
    primary_name_to_sources: dict[str, list[int]] = defaultdict(list)
    for row in dpe_rows:
        if not row["is_defined"]:
            continue
        source_id = row["source_id"]
        national = row["canonical_national_dex"]
        if national > 0 and primary_by_national[national] == source_id:
            primary_name_to_sources[_normal(row["display_name"])].append(source_id)

    source_to_canonical: dict[int, int] = {0: 0}
    matched_source_by_vega: dict[int, int] = {0: 0}
    for row in vega["rows"]:
        vega_id = row["id"]
        if vega_id == 0:
            continue
        candidates = primary_name_to_sources.get(_normal(row["display_name"]), [])
        if len(candidates) == 1 and candidates[0] not in source_to_canonical:
            source_id = candidates[0]
            source_to_canonical[source_id] = vega_id
            matched_source_by_vega[vega_id] = source_id

    canonical_rows: list[dict[str, Any]] = []
    stats_rows: list[bytes] = []
    name_rows: list[bytes] = []
    national_rows: list[int] = []
    dpe_rom = _fixed_bytes(root, config["dpe"]["rom_path"], config["dpe"]["rom_sha256"], "DPE ROM")
    vega_rom = _fixed_bytes(root, config["vega"]["rom_path"], config["vega"]["rom_sha256"], "Vega ROM")
    name_root = config["dpe"]["name_address"] - ROM_BASE
    name_stride = config["dpe"]["name_stride"]
    vega_name_root = config["vega"]["name_pointer"] - ROM_BASE

    for vega_row in vega["rows"]:
        canonical_id = vega_row["id"]
        source_id = matched_source_by_vega.get(canonical_id)
        source = dpe_rows[source_id] if source_id is not None else None
        national = source["canonical_national_dex"] if source else 0
        symbol = source["symbol"] if source else f"SPECIES_VEGA_{canonical_id:03d}"
        is_official = bool(national)
        canonical_rows.append({
            "id": canonical_id, "species_key": _symbol_key(symbol), "vega_id": canonical_id,
            "dpe_id": source_id, "dpe_symbols": [source["symbol"]] if source else [],
            "classification": "VEGA_DPE_CANONICAL" if source else "VEGA_ORIGINAL",
            "display_name": vega_row["display_name"], "form_key": "",
            "is_official": is_official, "canonical_national_dex": national,
            "review_state": "AUTO_REVIEWED_UNIQUE_NAME" if source else "REVIEWED_VEGA_ORIGINAL",
            "status": "FROZEN",
        })
        stats_rows.append(frozen_stats[canonical_id * 32:(canonical_id + 1) * 32])
        raw6 = vega_rom[vega_name_root + canonical_id * 6:vega_name_root + (canonical_id + 1) * 6]
        terminator = raw6.index(0xFF)
        name_rows.append(raw6[:terminator + 1].ljust(11, b"\xFF"))
        national_rows.append(national)

    next_id = 412
    for source in dpe_rows:
        source_id = source["source_id"]
        if source_id in source_to_canonical or not source["is_defined"]:
            continue
        canonical_id = next_id
        next_id += 1
        source_to_canonical[source_id] = canonical_id
        national = source["canonical_national_dex"]
        is_form = national > 0 and primary_by_national[national] != source_id
        is_official = 1 <= national <= int(policy["official_national_dex_max"])
        form_key = f"FORM_KEY_{source['symbol'].removeprefix('SPECIES_')}" if is_form else ""
        canonical_rows.append({
            "id": canonical_id, "species_key": _symbol_key(source["symbol"]), "vega_id": None,
            "dpe_id": source_id, "dpe_symbols": [source["symbol"]],
            "classification": "DPE_FORM_APPEND" if is_form else "DPE_SPECIES_APPEND",
            "display_name": source["display_name"], "form_key": form_key,
            "is_official": is_official, "canonical_national_dex": national if is_official else 0,
            "review_state": "REVIEWED_FORM_NATIONAL_DEX" if is_form else "REVIEWED_DPE_APPEND",
            "status": "APPENDED",
        })
        stats_rows.append(_translate_dpe_stats(bytes.fromhex(source["base_stats_raw_hex"]), abilities, items))
        raw8 = dpe_rom[name_root + source_id * name_stride:name_root + (source_id + 1) * name_stride]
        terminator = raw8.index(0xFF)
        name_rows.append(raw8[:terminator + 1].ljust(11, b"\xFF"))
        national_rows.append(national if is_official else 0)

    if [row["id"] for row in canonical_rows] != list(range(len(canonical_rows))):
        _fail("canonical Species IDs are not contiguous")
    if [row["vega_id"] for row in canonical_rows[:412]] != list(range(412)):
        _fail("Vega Species prefix changed")
    for source_id, canonical_id in source_to_canonical.items():
        if not 0 <= source_id < 1440 or not 0 <= canonical_id < len(canonical_rows):
            _fail("DPE alias is outside canonical range")
    if set(source_to_canonical) != set(dpe["defined_ids"]):
        _fail("not every DPE source Species resolves")

    official_numbers = {row["canonical_national_dex"] for row in canonical_rows if row["is_official"]}
    if 0 in official_numbers or len(official_numbers) != 1025:
        _fail("official canonical National Dex coverage changed")
    form_groups: dict[int, int] = defaultdict(int)
    for row in canonical_rows:
        if row["is_official"]:
            form_groups[row["canonical_national_dex"]] += 1
    duplicate_groups = {key: value for key, value in form_groups.items() if value > 1}
    for row in canonical_rows:
        if row["is_official"] and form_groups[row["canonical_national_dex"]] > 1:
            if not row["vega_id"] and not row["form_key"] and row["classification"] == "DPE_FORM_APPEND":
                _fail("official duplicate lacks explicit form marker")

    reference_validation = validate_existing_references(inventory, stage06, stage06_meta)
    source_symbols_by_id: dict[int, list[str]] = defaultdict(list)
    for alias in dpe["symbol_aliases"]:
        source_symbols_by_id[alias["source_id"]].append(alias["source_symbol"])
    aliases: list[dict[str, Any]] = []
    for source_id in dpe["defined_ids"]:
        canonical_id = source_to_canonical[source_id]
        canonical_rows[canonical_id]["dpe_symbols"] = source_symbols_by_id[source_id]
        for symbol in source_symbols_by_id[source_id]:
            aliases.append({
                "source_id": source_id, "source_symbol": symbol,
                "canonical_id": canonical_id,
                "species_key": canonical_rows[canonical_id]["species_key"],
            })

    first_appended = next(
        row for row, stats in zip(canonical_rows[412:], stats_rows[412:])
        if row["is_official"] and stats[0] > 0
    )
    return {
        "schema_version": SCHEMA_VERSION, "task": TASK_ID,
        "species": canonical_rows, "aliases": aliases,
        "base_stats_hex": b"".join(stats_rows).hex(),
        "species_names_hex": b"".join(name_rows).hex(),
        "national_dex": national_rows,
        "reference_validation": reference_validation,
        "first_appended_fixture": {
            "canonical_id": first_appended["id"], "dpe_id": first_appended["dpe_id"],
            "dpe_symbol": first_appended["dpe_symbols"][0],
            "display_name": first_appended["display_name"],
        },
        "summary": {
            "vega_frozen_count": 412, "dpe_table_count": 1440,
            "dpe_source_count": dpe["defined_count"],
            "canonical_count": len(canonical_rows),
            "dpe_alias_to_vega_count": len(matched_source_by_vega),
            "dpe_appended_count": len(canonical_rows) - 412,
            "official_national_count": len(official_numbers),
            "official_form_duplicate_group_count": len(duplicate_groups),
            "official_form_row_count": sum(value for value in duplicate_groups.values()),
            "unofficial_vega_count": sum(not row["is_official"] for row in canonical_rows[:412]),
        },
        "provenance": {"vega": vega["provenance"], "dpe": dpe["provenance"]},
    }


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=MANIFEST_HEADER, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in MANIFEST_HEADER})
    return stream.getvalue().encode("utf-8")


def render_artifacts(model: Mapping[str, Any], smoke: Mapping[str, Any] | None = None) -> dict[str, bytes]:
    public = {key: value for key, value in model.items() if not key.endswith("_hex")}
    species = model["species"]
    aliases = model["aliases"]
    base_stats = bytes.fromhex(str(model["base_stats_hex"]))
    names = bytes.fromhex(str(model["species_names_hex"]))
    national = b"".join(struct.pack("<H", int(value)) for value in model["national_dex"])
    header_lines = [
        "#pragma once", "/* Generated by T07; do not edit. */",
        f"#define VEGA_FROZEN_SPECIES_COUNT 412u",
        f"#define CANONICAL_SPECIES_COUNT {len(species)}u",
        f"#define CANONICAL_OFFICIAL_NATIONAL_COUNT {model['summary']['official_national_count']}u",
        "",
    ]
    for row in species:
        header_lines.append(f"#define {row['species_key']} {row['id']}u")
    header_lines += ["", "/* DPE source symbols resolve through the canonical manifest. */"]
    for row in aliases:
        header_lines.append(f"#define {row['source_symbol']} {row['canonical_id']}u")
    header = ("\n".join(header_lines) + "\n").encode("ascii")
    alias_public = {"schema_version": 1, "source_count": len(aliases), "rows": aliases}
    official_c = f'''/* Generated by T07; form rows share one canonical National Dex number. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

bool VegaOfficialDexThresholdMet(const uint8_t *caught, size_t caught_size, unsigned threshold)
{{
    unsigned count = 0;
    for (unsigned national = 1; national <= 1025; ++national) {{
        unsigned bit = national - 1;
        if (bit / 8 < caught_size && (caught[bit / 8] & (1u << (bit & 7)))) ++count;
    }}
    return count >= threshold;
}}
'''.encode("ascii")
    manifest_rows = []
    for row in species:
        manifest_rows.append({
            "species_key": row["species_key"], "id": row["id"],
            "vega_id": "" if row["vega_id"] is None else row["vega_id"],
            "dpe_id": "" if row["dpe_id"] is None else row["dpe_id"],
            "dpe_symbol": "|".join(row["dpe_symbols"]),
            "classification": row["classification"], "display_name": row["display_name"],
            "form_key": row["form_key"], "is_official": str(row["is_official"]).lower(),
            "canonical_national_dex": row["canonical_national_dex"],
            "review_state": row["review_state"], "status": row["status"], "notes": "",
        })
    smoke_status = smoke.get("status") if isinstance(smoke, Mapping) else "PENDING"
    smoke_species = smoke.get("species") if isinstance(smoke, Mapping) else model["first_appended_fixture"]["canonical_id"]
    summary = model["summary"]
    report = f"""# T07 Species port

- Status: PASS
- Vega frozen IDs: `0..411` ({summary['vega_frozen_count']} rows)
- DPE source Species: {summary['dpe_source_count']}
- Canonical Species: {summary['canonical_count']} (append {summary['dpe_appended_count']})
- DPE→Vega identity aliases: {summary['dpe_alias_to_vega_count']}
- Official canonical National Dex count: {summary['official_national_count']}
- Official multi-form groups: {summary['official_form_duplicate_group_count']} ({summary['official_form_row_count']} rows)
- Vega original/unofficial rows: {summary['unofficial_vega_count']}
- Existing trainer/wild/script/gift/evolution references: PASS
- Appended party-memory fixture: Species `{smoke_species}` / {smoke_status}

## Mapping contract

Vega `0..411` is a lossless frozen prefix. DPE primary forms are aliased only when a unique NFKC display-name identity exists; every other DPE Species/form is appended. Every row carries `is_official`, `canonical_national_dex`, `review_state`, and an explicit `form_key` for appended forms.

The Oval Charm threshold counts distinct official National Dex numbers, so multiple forms never increase the 100-species count.
""".encode("utf-8")
    return {
        "generated/engine/species/species_port.json": _stable_json(public),
        "generated/engine/species/species_generated.h": header,
        "generated/engine/species/base_stats.bin": base_stats,
        "generated/engine/species/species_names.bin": names,
        "generated/engine/species/national_dex.bin": national,
        "generated/engine/species/dpe_aliases.json": _stable_json(alias_public),
        "generated/engine/species/reference_validation.json": _stable_json(model["reference_validation"]),
        "generated/engine/species/official_species_count.c": official_c,
        "manifests/species_ids.csv": _csv_bytes(manifest_rows),
        "reports/generated/species_port.md": report,
    }


def build_stage(root: Path, config: Mapping[str, Any], model: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    inputs = config["inputs"]
    runtime = config["runtime"]
    stage06 = _fixed_bytes(
        root, inputs["stage06_path"],
        _expected_stage06_sha(root, inputs), "T06 stage",
    )
    table = bytes.fromhex(str(model["base_stats_hex"]))
    offset = _integer(runtime.get("new_base_stats_offset"), "new BaseStats offset")
    address = _integer(runtime.get("new_base_stats_address"), "new BaseStats address")
    old_address = _integer(runtime.get("old_base_stats_address"), "old BaseStats address")
    expected_count = _integer(runtime.get("old_base_stats_pointer_count"), "old pointer count")
    if address != ROM_BASE + offset or offset < 0x01600000 or offset + len(table) > 0x01F50000:
        _fail("T07 BaseStats allocation is outside DPE payload partition")
    output = bytearray(stage06)
    if set(output[offset:offset + len(table)]) != {0xFF}:
        _fail("T07 BaseStats allocation is not erased")
    before = struct.pack("<I", old_address)
    after = struct.pack("<I", address)
    sites = [index for index in range(0, len(stage06) - 3, 4) if stage06[index:index + 4] == before]
    if len(sites) != expected_count:
        _fail(f"T06 canonical BaseStats pointer universe changed: {len(sites)}")
    output[offset:offset + len(table)] = table
    for site in sites:
        output[site:site + 4] = after
    if any(output[index:index + 4] == before for index in range(0, len(output) - 3, 4)):
        _fail("legacy T06 BaseStats root remains")
    metadata = {
        "schema_version": 1, "task": TASK_ID, "status": "PASS",
        "input": {"path": inputs["stage06_path"], "sha256": _sha256(stage06)},
        "output": {"path": runtime["output_rom_path"], "sha256": _sha256(output), "size": len(output)},
        "base_stats": {
            "address": address, "offset": offset, "count": len(model["species"]),
            "stride": 32, "size": len(table), "sha256": _sha256(table),
            "repoint_count": len(sites), "repoint_sites": sites,
        },
        "first_appended_fixture": model["first_appended_fixture"],
    }
    return bytes(output), metadata


def run_smoke(root: Path, rom: bytes, species_id: int) -> dict[str, Any]:
    source = root / "tools/mgba_species_smoke.c"
    rom_sha = _sha256(rom)
    with tempfile.TemporaryDirectory(prefix=".t07-mgba-", dir=root / "build") as raw:
        work = Path(raw)
        rom_path = work / "candidate.gba"
        executable = work / "species_smoke"
        rom_path.write_bytes(rom)
        compiled = subprocess.run(
            ["/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(source), "-o", str(executable), "-lmgba"],
            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=60, check=False,
        )
        if compiled.returncode or compiled.stdout or compiled.stderr:
            _fail("mGBA Species runner compile failed/noisy: " + (compiled.stdout + compiled.stderr)[-2000:])
        environment = {"HOME": str(work), "LC_ALL": "C", "LANG": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"}
        payloads: list[dict[str, Any]] = []
        outputs: list[str] = []
        for _run in range(2):
            result = subprocess.run(
                [str(executable), str(rom_path), rom_sha, str(species_id)], cwd=work,
                env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=180, check=False,
            )
            if result.returncode or result.stderr:
                _fail("mGBA appended Species smoke failed: " + (result.stdout + result.stderr)[-2000:])
            output = result.stdout.strip()
            try:
                payload = json.loads(output)
            except json.JSONDecodeError as error:
                _fail(f"mGBA Species smoke returned invalid JSON: {error}")
            if payload.get("status") != "PASS" or payload.get("species") != species_id:
                _fail("mGBA Species smoke contract failed")
            outputs.append(output)
            payloads.append(payload)
        if outputs[0] != outputs[1]:
            _fail("mGBA Species smoke is not repeatable")
        return {**payloads[0], "process_runs": 2, "runner_sha256": _sha256_file(source)}


def _fingerprint(root: Path) -> dict[str, Any]:
    rows = []
    for logical in FINGERPRINT_FILES:
        path = root / logical
        if not path.is_file() or path.is_symlink():
            _fail(f"fingerprint input missing/nonregular: {logical}")
        rows.append({"path": logical, "sha256": _sha256_file(path), "size": path.stat().st_size})
    digest = _sha256(_stable_json(rows, pretty=False).rstrip(b"\n"))
    return {"sha256": digest, "inputs": rows}


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-t07")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _compile_probe(root: Path, artifacts: Mapping[str, bytes]) -> None:
    with tempfile.TemporaryDirectory(prefix=".t07-compile-", dir=root / "build") as raw:
        work = Path(raw)
        (work / "species_generated.h").write_bytes(
            artifacts["generated/engine/species/species_generated.h"]
        )
        (work / "official_species_count.c").write_bytes(
            artifacts["generated/engine/species/official_species_count.c"]
        )
        probe = work / "probe.c"
        probe.write_text(
            '#include "species_generated.h"\n'
            '#include "official_species_count.c"\n'
            '_Static_assert(VEGA_FROZEN_SPECIES_COUNT == 412u, "frozen");\n'
            '_Static_assert(CANONICAL_SPECIES_COUNT == 1621u, "count");\n'
            'int main(void) { unsigned char caught[129] = {0}; '
            'return VegaOfficialDexThresholdMet(caught, sizeof(caught), 100u); }\n',
            encoding="ascii",
        )
        result = subprocess.run(
            ["/usr/bin/cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(probe), "-o", str(work / "probe")],
            cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=60, check=False,
        )
        if result.returncode or result.stdout or result.stderr:
            _fail("generated Species C compile probe failed/noisy: " + (result.stdout + result.stderr)[-2000:])


def build(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    config = _read_json(root / CONFIG_PATH, "T07 config")
    fingerprint = _fingerprint(root)
    first = build_species_model(root, config)
    second = build_species_model(root, config)
    if _stable_json(first) != _stable_json(second):
        _fail("two Species model builds differ")
    stage_first, metadata_first = build_stage(root, config, first)
    stage_second, metadata_second = build_stage(root, config, second)
    if stage_first != stage_second or metadata_first != metadata_second:
        _fail("two T07 ROM builds differ")
    fixture_id = first["first_appended_fixture"]["canonical_id"]
    smoke = run_smoke(root, stage_first, fixture_id)
    artifacts = render_artifacts(first, smoke)
    _compile_probe(root, artifacts)
    metadata_first.update({
        "fingerprint": fingerprint["sha256"], "fingerprint_inputs": fingerprint["inputs"],
        "smoke": smoke,
        "published_artifacts": {path: _sha256(data) for path, data in sorted(artifacts.items())},
    })
    _atomic_write(root / config["runtime"]["output_rom_path"], stage_first)
    _atomic_write(root / config["runtime"]["output_metadata_path"], _stable_json(metadata_first))
    for logical, data in artifacts.items():
        _atomic_write(root / logical, data)
    return {
        "status": "PASS", "species": len(first["species"]),
        "appended": first["summary"]["dpe_appended_count"],
        "official": first["summary"]["official_national_count"],
        "rom_sha256": _sha256(stage_first), "fingerprint": fingerprint["sha256"],
    }


def check(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    config = _read_json(root / CONFIG_PATH, "T07 config")
    metadata = _read_json(root / config["runtime"]["output_metadata_path"], "T07 metadata")
    fingerprint = _fingerprint(root)
    if metadata.get("fingerprint") != fingerprint["sha256"] or metadata.get("fingerprint_inputs") != fingerprint["inputs"]:
        _fail("published T07 fingerprint differs")
    model = build_species_model(root, config)
    stage, expected_meta = build_stage(root, config, model)
    published_stage = (root / config["runtime"]["output_rom_path"]).read_bytes()
    if stage != published_stage or metadata.get("output") != expected_meta.get("output") or metadata.get("base_stats") != expected_meta.get("base_stats"):
        _fail("published T07 stage differs from rebuilt stage")
    smoke = metadata.get("smoke")
    if not isinstance(smoke, Mapping) or smoke.get("status") != "PASS" or smoke.get("process_runs") != 2:
        _fail("published T07 smoke evidence is invalid")
    artifacts = render_artifacts(model, smoke)
    _compile_probe(root, artifacts)
    expected_hashes = {path: _sha256(data) for path, data in sorted(artifacts.items())}
    if metadata.get("published_artifacts") != expected_hashes:
        _fail("published T07 artifact hash map differs")
    for logical, data in artifacts.items():
        path = root / logical
        if not path.is_file() or path.read_bytes() != data:
            _fail(f"published T07 artifact differs: {logical}")
    return {
        "status": "PASS", "species": len(model["species"]),
        "appended": model["summary"]["dpe_appended_count"],
        "official": model["summary"]["official_national_count"],
        "rom_sha256": _sha256(stage), "fingerprint": fingerprint["sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = build(args.root) if args.command == "build" else check(args.root)
    except (SpeciesPortError, VegaSpeciesExtractionError, OSError, UnicodeError) as error:
        print(f"build_species_port: ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
