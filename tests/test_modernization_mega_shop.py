from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.modernization_mega_shop import (
    ITEM_SANITIZER_REPLACEMENT,
    _all_offsets,
    _run_host_harness,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/modernization_mega_shop.json").read_text())
META = json.loads((ROOT / "build/stages/68_modernization_mega_shop.json").read_text())
CATALOG = json.loads((ROOT / "content/modernization/mega_shop_catalog.json").read_text())
ALLOWLIST = json.loads(
    (ROOT / "config/modernization_mega_shop_pointer_sites.json").read_text()
)
PARENT = (ROOT / CONFIG["inputs"]["rom"]["path"]).read_bytes()
ROM = (ROOT / CONFIG["outputs"]["rom"]).read_bytes()
GBA = 0x08000000


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rom_offset(address: int | str) -> int:
    if isinstance(address, str):
        address = int(address, 0)
    return (address & ~1) - GBA


def decompress_lz77(rom: bytes, address: int, expected_size: int) -> bytes:
    cursor = rom_offset(address)
    assert rom[cursor] == 0x10
    declared = int.from_bytes(rom[cursor + 1:cursor + 4], "little")
    assert declared == expected_size
    cursor += 4
    output = bytearray()
    while len(output) < declared:
        flags = rom[cursor]
        cursor += 1
        for bit in range(7, -1, -1):
            if len(output) >= declared:
                break
            if flags & (1 << bit):
                high, low = rom[cursor:cursor + 2]
                cursor += 2
                length = (high >> 4) + 3
                distance = ((high & 15) << 8 | low) + 1
                assert distance <= len(output)
                for _ in range(length):
                    if len(output) < declared:
                        output.append(output[-distance])
            else:
                output.append(rom[cursor])
                cursor += 1
    return bytes(output)


def test_contract_and_dedicated_flag_namespace() -> None:
    assert len(ROM) == 32 * 1024 * 1024
    assert sha(ROM) == META["output"]["sha256"]
    assert [row["item_id"] for row in CATALOG["entries"]] == list(range(999, 1044))
    assert [row["claim_flag"] for row in CATALOG["entries"]] == list(
        range(0x14A0, 0x14CD)
    )
    assert {row["price_bp"] for row in CATALOG["entries"]} == {16}
    assert (CATALOG["page_size"], CATALOG["page_count"]) == (5, 9)
    assert META["flag_namespace"]["status"] == "PASS_DEDICATED_STAGE68_ALLOCATION"
    assert META["flag_namespace"]["collision_count"] == 0
    assert META["flag_namespace"]["global_manifest_rows_present"] == 0
    assert META["flag_namespace"]["flags_manifest_mutated"] is False


def test_real_transaction_code_host_failure_injection() -> None:
    header = (ROOT / CONFIG["outputs"]["catalog_header"]).read_bytes()
    result = _run_host_harness(ROOT, header)
    assert result["status"] == "PASS"
    assert result["assertions"] >= 244
    assert result["failures"] == 0
    assert result["catalog_entries"] == 45
    assert result["failure_injection_cases"] == 2
    recorded = META["validation"]["host_harness"]
    assert recorded["status"] == "PASS"
    assert recorded["assertions"] == result["assertions"]


def test_pointer_repoints_are_exact_semantic_allowlist_only() -> None:
    groups = {row["table_key"]: row for row in ALLOWLIST["tables"]}
    patches = {row["table_key"]: row for row in META["pointer_repoints"]}
    assert set(groups) == set(patches) == {
        "item_data",
        "item_graphics",
        "item_effect_pointer2",
        "item_fling",
        "item_type_by_id",
    }
    assert sum(row["site_count"] for row in groups.values()) == 57
    for key, group in groups.items():
        patch = patches[key]
        old = int(group["old_address"], 0)
        new = patch["new_address"]
        sites = [row["site_offset"] for row in group["sites"]]
        assert sites == patch["site_offsets"]
        assert _all_offsets(PARENT, struct.pack("<I", old)) == sites
        assert not _all_offsets(ROM, struct.pack("<I", old))
        for row in group["sites"]:
            context = bytes.fromhex(row["expected_context_hex"])
            assert row["semantic_owner"] != "UNCLASSIFIED"
            assert row["semantic_evidence"]
            assert sha(context) == row["expected_context_sha256"]
            start = row["context_offset"]
            assert PARENT[start:start + len(context)] == context
            assert struct.unpack_from("<I", ROM, row["site_offset"])[0] == new
        assert patch["all_literal_matches_allowlisted"] is True
        assert patch["all_contexts_exact"] is True


def test_item_tables_have_1044_valid_rows_and_assets() -> None:
    tables = META["item_materialization"]["tables"]
    parent_template = PARENT[
        rom_offset(CONFIG["item_tables"]["item_data"]["address"])
        + 747 * 40:
        rom_offset(CONFIG["item_tables"]["item_data"]["address"])
        + 748 * 40
    ]
    data = rom_offset(tables["item_data"]["new_address"])
    graphics = rom_offset(tables["item_graphics"]["new_address"])
    types = rom_offset(tables["item_type_by_id"]["new_address"])
    effects = rom_offset(tables["item_effect_pointer2"]["new_address"])
    fling = rom_offset(tables["item_fling"]["new_address"])
    asset_root = ROOT / CONFIG["inputs"]["asset_root"]
    description_pointers: set[int] = set()
    for index, catalog_row in enumerate(CATALOG["entries"]):
        item_id = 999 + index
        row = ROM[data + item_id * 40:data + (item_id + 1) * 40]
        assert row[:10].hex() == catalog_row["display_name_hex"]
        assert struct.unpack_from("<H", row, 10)[0] == item_id
        assert struct.unpack_from("<H", row, 12)[0] == 0
        assert row[14:16] == parent_template[14:16]
        assert row[20:40] == parent_template[20:40]
        description = struct.unpack_from("<I", row, 16)[0]
        assert GBA <= description < GBA + len(ROM)
        description_pointers.add(description)
        assert struct.unpack_from("<H", ROM, types + item_id * 2)[0] == 50
        assert ROM[effects + item_id * 4:effects + (item_id + 1) * 4] == PARENT[
            rom_offset(CONFIG["item_tables"]["item_effect_pointer2"]["address"])
            + 747 * 4:
            rom_offset(CONFIG["item_tables"]["item_effect_pointer2"]["address"])
            + 748 * 4
        ]
        assert ROM[fling + item_id * 2:fling + (item_id + 1) * 2] == PARENT[
            rom_offset(CONFIG["item_tables"]["item_fling"]["address"])
            + 747 * 2:
            rom_offset(CONFIG["item_tables"]["item_fling"]["address"])
            + 748 * 2
        ]
        icon_pointer, palette_pointer = struct.unpack_from(
            "<II", ROM, graphics + item_id * 8,
        )
        icon = decompress_lz77(ROM, icon_pointer, 288)
        palette = decompress_lz77(ROM, palette_pointer, 32)
        assert icon == (asset_root / catalog_row["icon_relative_path"]).read_bytes()
        assert palette == (asset_root / catalog_row["palette_relative_path"]).read_bytes()
    assert len(description_pointers) == 1
    description_offset = rom_offset(description_pointers.pop())
    assert 0xFF in ROM[description_offset:description_offset + 64]
    assert all(table["new_count"] == 1044 for table in tables.values())


def test_original_999_rows_are_byte_exact() -> None:
    for key, spec in CONFIG["item_tables"].items():
        if key in {"template_item_id", "mega_stone_item_type"}:
            continue
        old_address = int(spec["address"], 0)
        new_address = META["item_materialization"]["tables"][key]["new_address"]
        size = spec["old_count"] * spec["stride"]
        assert ROM[rom_offset(new_address):rom_offset(new_address) + size] == PARENT[
            rom_offset(old_address):rom_offset(old_address) + size
        ]


def test_sanitizer_and_physical_factory_npc_graph() -> None:
    sanitizer = META["item_sanitizer"]
    assert ROM[sanitizer["site_offset"]:sanitizer["site_offset"] + 24] \
        == ITEM_SANITIZER_REPLACEMENT
    bounds = json.loads(
        (ROOT / "config/modernization_mega_shop_item_bounds.json").read_text()
    )
    bound_meta = META["cfru_item_bounds"]
    assert bound_meta["old_max_inclusive"] == 998
    assert bound_meta["new_max_inclusive"] == 1043
    assert bound_meta["first_rejected"] == 1044
    assert bound_meta["site_count"] == len(bounds["sites"]) == 12
    for row in bounds["sites"]:
        context = bytes.fromhex(row["expected_context_hex"])
        assert sha(context) == row["expected_context_sha256"]
        assert PARENT[row["context_offset"]:row["context_offset"] + 20] == context
        assert struct.unpack_from("<I", ROM, row["site_offset"])[0] == 1043
    for item_id in (999, 1023, 1024, 1043):
        assert item_id <= bound_meta["new_max_inclusive"]
    assert 1044 == bound_meta["first_rejected"]
    map_meta = META["map"]
    header = map_meta["header_offset"]
    assert struct.unpack_from("<I", ROM, header + 4)[0] \
        == map_meta["events_after_address"]
    assert struct.unpack_from("<I", ROM, header + 8)[0] \
        == map_meta["old_scripts_pointer"]
    events = rom_offset(map_meta["events_after_address"])
    assert tuple(ROM[events:events + 4]) == (14, 10, 0, 7)
    objects_pointer = struct.unpack_from("<I", ROM, events + 4)[0]
    assert objects_pointer == map_meta["objects_after_address"]
    objects = rom_offset(objects_pointer)
    assert sha(ROM[objects:objects + 13 * 24]) == map_meta["old_objects_sha256"]
    shop = ROM[objects + 13 * 24:objects + 14 * 24]
    assert shop[0] == 14
    assert struct.unpack_from("<HH", shop, 4) == (24, 19)
    assert struct.unpack_from("<I", shop, 16)[0] == map_meta["shop_script_address"]
    labels = META["labels"]
    script = rom_offset(labels["script_mega_shop_npc"])
    assert ROM[script:script + 3] == bytes((0x6A, 0x5A, 0x23))
    assert struct.unpack_from("<I", ROM, script + 3)[0] \
        == META["entrypoints"]["MegaShop_Open"]
    assert ROM[script + 7] == 0x21
    assert ROM[script + 12:script + 14] == bytes((0x06, 0x01))
    assert struct.unpack_from("<I", ROM, script + 14)[0] \
        == labels["script_mega_shop_wait"]


def test_narrow_consumers_explicitly_exclude_new_ids() -> None:
    codex_config = json.loads(
        (ROOT / "config/codex_battle_runtime.json").read_text()
    )
    codex_source = (
        ROOT / "overlays/codex_battle_runtime/codex_battle_runtime.c"
    ).read_text()
    assert codex_config["battle"]["item_max"] == 998
    assert "if (item > CODEX_RUNTIME_ITEM_MAX)" in codex_source
    assert META["runtime_boundaries"]["codex"]["new_item_ids_admitted"] == 0
    mirage = json.loads(
        (ROOT / "generated/runtime/mirage_production_serialized.json").read_text()
    )
    item_ids = [row["item_id"] for row in mirage["rentals"]]
    item_ids.extend(row["item_id"] for row in mirage["rewards"])
    assert max(item_ids) <= 998
    assert META["runtime_boundaries"]["mirage"]["new_item_ids_admitted"] == 0


def test_source_provenance_is_complete_and_exact() -> None:
    bindings = META["source_bindings"]
    assert bindings["file_count"] == len(bindings["files"])
    for binding in bindings["files"]:
        raw = (ROOT / binding["path"]).read_bytes()
        assert len(raw) == binding["size"]
        assert sha(raw) == binding["sha256"]
    assert bindings["p04_asset_payload"]["file_count"] == 90
    assert bindings["arm_toolchain"]["executables"]["compiler"]["version"]
    header = (ROOT / CONFIG["outputs"]["catalog_header"]).read_bytes()
    assert sha(header) == bindings["generated_catalog_header"]["sha256"]
    assert len(header) == bindings["generated_catalog_header"]["size"]


class ModernizationMegaShopTest(unittest.TestCase):
    def test_contract(self) -> None:
        test_contract_and_dedicated_flag_namespace()

    def test_host_transaction(self) -> None:
        test_real_transaction_code_host_failure_injection()

    def test_pointer_allowlist(self) -> None:
        test_pointer_repoints_are_exact_semantic_allowlist_only()

    def test_item_materialization(self) -> None:
        test_item_tables_have_1044_valid_rows_and_assets()

    def test_old_rows(self) -> None:
        test_original_999_rows_are_byte_exact()

    def test_map_and_sanitizer(self) -> None:
        test_sanitizer_and_physical_factory_npc_graph()

    def test_narrow_boundaries(self) -> None:
        test_narrow_consumers_explicitly_exclude_new_ids()

    def test_source_provenance(self) -> None:
        test_source_provenance_is_complete_and_exact()


if __name__ == "__main__":
    unittest.main()
