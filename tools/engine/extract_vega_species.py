#!/usr/bin/env python3
"""固定Vega ROMからSpecies 0..411の名前とBaseStats ABIを抽出する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.engine.extract_vega_id_spaces import _read_charmap


ROM_BASE = 0x08000000


class VegaSpeciesExtractionError(ValueError):
    """固定ROM、table root、hash、またはSpecies ABIの不一致。"""


def _fail(message: str) -> NoReturn:
    raise VegaSpeciesExtractionError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{label} must be an integer")
    return value


def _slice(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(rom):
        _fail(f"{label} is outside ROM")
    return rom[offset:offset + size]


def _decode_fixed(raw: bytes, charmap: Mapping[int, str], label: str) -> tuple[str, int]:
    end = raw.find(b"\xFF")
    if end < 0:
        end = len(raw)
    decoded: list[str] = []
    for index, byte in enumerate(raw[:end]):
        if byte not in charmap:
            decoded.append(f"[{byte:02X}]")
        else:
            decoded.append(charmap[byte])
    return "".join(decoded), end


def extract_vega_species(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    policy = config.get("vega")
    charmap_policy = config.get("charmap")
    if not isinstance(policy, Mapping) or not isinstance(charmap_policy, Mapping):
        _fail("vega/charmap policy is missing")
    path = root / str(policy.get("rom_path", ""))
    try:
        rom = path.read_bytes()
    except OSError as error:
        _fail(f"cannot read fixed Vega ROM: {error}")
    expected_rom = str(policy.get("rom_sha256", ""))
    if _sha256(rom) != expected_rom:
        _fail("fixed Vega ROM SHA-256 mismatch")

    count = _integer(policy.get("species_count"), "vega.species_count")
    name_site = _integer(policy.get("name_pointer_site"), "vega.name_pointer_site")
    name_pointer = _integer(policy.get("name_pointer"), "vega.name_pointer")
    name_stride = _integer(policy.get("name_stride"), "vega.name_stride")
    stats_site = _integer(policy.get("base_stats_pointer_site"), "vega.base_stats_pointer_site")
    stats_pointer = _integer(policy.get("base_stats_pointer"), "vega.base_stats_pointer")
    stats_stride = _integer(policy.get("base_stats_stride"), "vega.base_stats_stride")
    if (count, name_stride, stats_stride) != (412, 6, 28):
        _fail("Vega Species count/ABI changed")
    if int.from_bytes(rom[name_site:name_site + 4], "little") != name_pointer:
        _fail("Vega Species-name root changed")
    if int.from_bytes(rom[stats_site:stats_site + 4], "little") != stats_pointer:
        _fail("Vega BaseStats root changed")

    name_raw = _slice(rom, name_pointer, count * name_stride, "Vega Species names")
    stats_raw = _slice(rom, stats_pointer, count * stats_stride, "Vega BaseStats")
    if _sha256(name_raw) != policy.get("name_table_sha256"):
        _fail("Vega Species-name table SHA-256 mismatch")
    if _sha256(stats_raw) != policy.get("base_stats_sha256"):
        _fail("Vega BaseStats table SHA-256 mismatch")
    charmap, charmap_meta = _read_charmap(
        root,
        {"logical_path": charmap_policy.get("path"), "sha256": charmap_policy.get("sha256")},
    )

    rows: list[dict[str, Any]] = []
    for species_id in range(count):
        raw_name = name_raw[species_id * name_stride:(species_id + 1) * name_stride]
        name, encoded_length = _decode_fixed(raw_name, charmap, f"Vega Species {species_id} name")
        raw = stats_raw[species_id * stats_stride:(species_id + 1) * stats_stride]
        ev = int.from_bytes(raw[10:12], "little")
        rows.append(
            {
                "id": species_id,
                "display_name": name,
                "name_encoded_length": encoded_length,
                "base_stats": {
                    "hp": raw[0], "attack": raw[1], "defense": raw[2],
                    "speed": raw[3], "sp_attack": raw[4], "sp_defense": raw[5],
                    "type1": raw[6], "type2": raw[7], "catch_rate": raw[8],
                    "exp_yield": raw[9],
                    "ev_yield": [(ev >> shift) & 3 for shift in (0, 2, 4, 6, 8, 10)],
                    "item1": int.from_bytes(raw[12:14], "little"),
                    "item2": int.from_bytes(raw[14:16], "little"),
                    "gender_ratio": raw[16], "egg_cycles": raw[17],
                    "friendship": raw[18], "growth_rate": raw[19],
                    "egg_group1": raw[20], "egg_group2": raw[21],
                    "ability1": raw[22], "ability2": raw[23],
                    "safari_flee_rate": raw[24], "body_color_no_flip": raw[25],
                },
                "raw_hex": raw.hex(),
            }
        )
    return {
        "schema_version": 1,
        "source": "VEGA_FIXED_ROM",
        "count": count,
        "ids": list(range(count)),
        "rows": rows,
        "provenance": {
            "rom_path": str(policy["rom_path"]), "rom_sha256": expected_rom,
            "name_table_sha256": _sha256(name_raw),
            "base_stats_sha256": _sha256(stats_raw), "charmap": charmap_meta,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path, default=Path("config/species_port.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config if args.config.is_absolute() else root / args.config
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        print(json.dumps(extract_vega_species(root, config), ensure_ascii=False, sort_keys=True, indent=2))
    except (OSError, UnicodeError, json.JSONDecodeError, VegaSpeciesExtractionError) as error:
        print(f"extract_vega_species: ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
