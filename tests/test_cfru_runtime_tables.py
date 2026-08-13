from __future__ import annotations

import copy
import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.engine.cfru_runtime_tables import (
    CFRURuntimeTableError,
    apply_source_table_patches,
    build_runtime_assets,
    resolve_runtime_assets,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_json(logical: str) -> dict:
    return json.loads((ROOT / logical).read_text(encoding="utf-8"))


def _encoder() -> tuple[dict[str, int], list[str]]:
    mapping: dict[str, int] = {}
    for line in (ROOT / "vendor/upstream/CFRU-JP/charmap.tbl").read_text(
        encoding="utf-8-sig"
    ).splitlines():
        if len(line) < 3 or line[2] != "=":
            continue
        try:
            byte = int(line[:2], 16)
        except ValueError:
            continue
        token = line[3:]
        if token != "$":
            mapping.setdefault(token, byte)
    return mapping, sorted(mapping, key=lambda token: (-len(token), token))


def _encode(text: str, mapping: dict[str, int], tokens: list[str]) -> bytes:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\n")
    output = bytearray()
    index = 0
    while index < len(text):
        for token in tokens:
            if text.startswith(token, index):
                output.append(mapping[token])
                index += len(token)
                break
        else:
            raise AssertionError(f"unencodable test text at {text[index:]!r}")
    return bytes(output)


class CFRURuntimeTablesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.move_model = _load_json("generated/engine/moves/move_port.json")
        cls.id_model = _load_json("generated/engine/ids/id_spaces.json")
        cls.assets = build_runtime_assets(ROOT, cls.move_model, cls.id_model)
        cls.mapping, cls.tokens = _encoder()

    def test_exact_counts_strides_and_hashes(self) -> None:
        tables = self.assets["tables"]
        expected_sizes = {
            "gBattleMoves": 1063 * 12,
            "gMoveNames": 1063 * 16,
            "gMoveDescriptionBlob": 48358,
            "gMoveDescriptionOffsets": 1063 * 4,
            "gMoveDescriptions": 1063 * 4,
            "gMoveAnimations": 1063 * 4,
            "gAbilityNames": 312 * 17,
            "gAbilityDescriptionBlob": 5871,
            "gAbilityDescriptionOffsets": 312 * 4,
            "gAbilityDescriptions": 312 * 4,
            "gItemData": 999 * 40,
            "gItemGraphicsTable": 999 * 8,
            "gQolItemDescriptionBlob": 295,
            "gQolItemDescriptionOffsets": 11 * 4,
        }
        self.assertEqual({key: len(value) for key, value in tables.items()}, expected_sizes)
        expected_hashes = {
            "gBattleMoves": "b1962f8ce90bd675300691258e551f67015391e02ff670071bf5f51e4d18b32c",
            "gMoveNames": "6d501c03ba9a18995d7bb29cedcdca742c4fc4fbb3d4e4d42d4971a7ba89edfa",
            "gMoveDescriptionBlob": "590b9e3330778c32af3c954e72c9b1024f22118b67191808d31045601f84f59c",
            "gMoveDescriptionOffsets": "29061ee38faa2ba0646c077d49c44409bd35443611ba889e0861a7b3dd114029",
            "gMoveAnimations": "70c9d7b8fcef0d37ce9fd9649390bb337e266a05124b5f3764a388879308f953",
            "gAbilityNames": "7738c43dcf08260ccee2590624cd6db41b1d012e1413bb771398596b73e18655",
            "gAbilityDescriptionBlob": "0474d7db6950f4cd4c148cfbe235adb1389dc685c213d4799fafdccb64edcbf1",
            "gAbilityDescriptionOffsets": "c645c911a44c146b840768911a11a86f041fc979dcd3e3c6bd25e5e14c564246",
            "gItemData": "8778ce26702c16f82978fe89ba645ff544425a9d4a87672568a3fb5a715febc7",
            "gItemGraphicsTable": "725119e79c8b3bdbeffd3d9d49db514a82ce1c26dd43aa8510a37697ade9b1a8",
        }
        for symbol, expected in expected_hashes.items():
            actual = hashlib.sha256(tables[symbol]).hexdigest()
            self.assertEqual(actual, expected, symbol)
            self.assertEqual(self.assets["metadata"]["tables"][symbol]["sha256"], expected)
        self.assertTrue(all(self.assets["metadata"]["gates"].values()))
        self.assertEqual(self.assets["metadata"]["relocation_status"], "PENDING")
        self.assertIn(b"CFRU_RUNTIME_MOVE_COUNT 1063", self.assets["sources"]["runtime_tables_generated.h"])

    def test_all_move_and_ability_rows_round_trip(self) -> None:
        tables = self.assets["tables"]
        decoded_moves = list(struct.iter_unpack("<7Bb4B", tables["gBattleMoves"]))
        self.assertEqual(len(decoded_moves), 1063)
        fields = (
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
        for index, (packed, row) in enumerate(zip(decoded_moves, self.move_model["moves"])):
            self.assertEqual(packed, tuple(row["battle"][field] for field in fields), index)

        for symbol, rows, stride in (
            ("gMoveNames", self.move_model["moves"], 16),
            ("gAbilityNames", self.id_model["abilities"], 17),
        ):
            raw = tables[symbol]
            for index, row in enumerate(rows):
                encoded = _encode(row["display_name"], self.mapping, self.tokens)
                fixed = raw[index * stride : (index + 1) * stride]
                self.assertEqual(fixed, encoded + b"\xFF" * (stride - len(encoded)), (symbol, index))

        move_offsets = struct.unpack("<1063I", tables["gMoveDescriptionOffsets"])
        move_blob = tables["gMoveDescriptionBlob"]
        for index, (offset, row) in enumerate(zip(move_offsets, self.move_model["moves"])):
            end = move_offsets[index + 1] if index + 1 < len(move_offsets) else len(move_blob)
            self.assertEqual(
                move_blob[offset:end],
                bytes.fromhex(row["description"]["raw_hex"]),
                index,
            )

        ability_offsets = struct.unpack("<312I", tables["gAbilityDescriptionOffsets"])
        ability_blob = tables["gAbilityDescriptionBlob"]
        for index, (offset, row) in enumerate(zip(ability_offsets, self.id_model["abilities"])):
            end = ability_offsets[index + 1] if index + 1 < len(ability_offsets) else len(ability_blob)
            expected = _encode(row["description"], self.mapping, self.tokens) + b"\xFF"
            self.assertEqual(ability_blob[offset:end], expected, index)

    def test_animation_and_item_recipes_cover_every_canonical_row(self) -> None:
        animations = self.assets["recipes"]["move_animations"]
        self.assertEqual([row["id"] for row in animations], list(range(1063)))
        self.assertEqual(
            {kind: sum(row["kind"] == kind for row in animations) for kind in {row["kind"] for row in animations}},
            {"VEGA_RAW_POINTER": 71, "RAW_POINTER": 330, "SOURCE_SYMBOL": 662},
        )
        animation_table = self.assets["tables"]["gMoveAnimations"]
        animation_relocations = {
            row["row"]: row
            for row in self.assets["relocations"]
            if row["domain"] == "MOVE_ANIMATION"
        }
        for row in animations:
            value = struct.unpack_from("<I", animation_table, row["id"] * 4)[0]
            if row["kind"] == "SOURCE_SYMBOL":
                self.assertEqual(value, 0)
                self.assertEqual(animation_relocations[row["id"]]["symbol"], row["symbol"])
            else:
                self.assertEqual(value, row["value"])
        self.assertIn(
            b".word ANIM_PSYCHICNOISE",
            self.assets["sources"]["runtime_pointer_tables.s"],
        )

        item_rows = self.assets["patches"]["item_rows"]
        item_icons = self.assets["patches"]["item_icons"]
        self.assertEqual([row["id"] for row in item_rows], list(range(999)))
        self.assertEqual([row["id"] for row in item_icons], list(range(999)))
        self.assertEqual(
            [item_rows[index]["kind"] for index in (0, 374, 375, 987, 988, 998)],
            [
                "VEGA_RAW_ROW",
                "VEGA_RAW_ROW",
                "CFRU_SOURCE_ROW_COPY",
                "CFRU_SOURCE_ROW_COPY",
                "QOL_GENERATED_ROW",
                "QOL_GENERATED_ROW",
            ],
        )
        self.assertEqual(item_rows[375]["source_index"], 40)
        self.assertEqual(item_rows[375]["post_copy_patches"][0]["value"], 375)
        self.assertEqual(item_rows[589]["source_index"], 375)
        self.assertTrue(item_rows[589]["reserved"])
        self.assertEqual(item_rows[589]["post_copy_patches"][0]["value"], 0)
        self.assertEqual(item_rows[987]["source_index"], 773)

        item_table = self.assets["tables"]["gItemData"]
        icon_table = self.assets["tables"]["gItemGraphicsTable"]
        for index in range(375):
            self.assertEqual(
                item_table[index * 40 : (index + 1) * 40],
                bytes.fromhex(self.id_model["items"][index]["vega_raw"]["raw_hex"]),
                index,
            )
            self.assertEqual(
                icon_table[index * 8 : (index + 1) * 8],
                bytes.fromhex(self.id_model["items"][index]["vega_raw"]["icon_entry_raw"]),
                index,
            )
        self.assertEqual(item_table[375 * 40 : 988 * 40], bytes((988 - 375) * 40))
        self.assertEqual(icon_table[375 * 8 : 988 * 8], bytes((988 - 375) * 8))
        for index in range(988, 999):
            self.assertEqual(struct.unpack_from("<H", item_table, index * 40 + 10)[0], index)

    def test_two_stage_relocation_resolution_is_strict(self) -> None:
        symbols = sorted({row["symbol"] for row in self.assets["relocations"]})
        self.assertEqual(len(symbols), 596)
        offsets = {symbol: 0x08800000 + index * 0x1000 for index, symbol in enumerate(symbols)}
        resolved = resolve_runtime_assets(self.assets, offsets)
        self.assertEqual(resolved["metadata"]["relocation_status"], "RESOLVED")
        self.assertNotEqual(
            resolved["metadata"]["manifest_sha256"],
            self.assets["metadata"]["manifest_sha256"],
        )
        for relocation in resolved["relocations"]:
            expected = (
                offsets[relocation["symbol"]] | 1
                if relocation["kind"] == "THUMB32"
                else offsets[relocation["symbol"]]
            ) + relocation["addend"]
            actual = struct.unpack_from(
                "<I", resolved["tables"][relocation["table"]], relocation["offset"]
            )[0]
            self.assertEqual(actual, expected)
            self.assertEqual(relocation["resolved_value"], expected)
        # 入力assetは不変で、部分的なsymbol mapを暗黙採用しない。
        self.assertEqual(self.assets["metadata"]["relocation_status"], "PENDING")
        with self.assertRaisesRegex(CFRURuntimeTableError, "unresolved relocation symbols"):
            resolve_runtime_assets(self.assets, {symbols[0]: offsets[symbols[0]]})

        first_symbols = set(symbols[:-5])
        partial = build_runtime_assets(
            ROOT,
            self.move_model,
            self.id_model,
            {symbol: offsets[symbol] for symbol in first_symbols},
        )
        self.assertEqual(partial["metadata"]["relocation_status"], "PARTIAL")
        final = resolve_runtime_assets(
            partial, {symbol: offsets[symbol] for symbol in symbols if symbol not in first_symbols}
        )
        self.assertEqual(final["metadata"]["relocation_status"], "RESOLVED")

    def test_source_table_copy_helper_applies_all_recipes(self) -> None:
        source_items = bytearray(774 * 40)
        for source_id in range(774):
            struct.pack_into(
                "<H", source_items, source_id * 40 + 10, 0 if source_id == 375 else source_id
            )
            struct.pack_into("<H", source_items, source_id * 40 + 12, source_id * 3 & 0xFFFF)
        source_icons = b"".join(
            struct.pack("<II", 0x08100000 + source_id * 8, 0x08200000 + source_id * 8)
            for source_id in range(774)
        )
        applied = apply_source_table_patches(
            self.assets,
            {
                "CFRU_ITEM_DATA": bytes(source_items),
                "CFRU_ITEM_GRAPHICS": source_icons,
            },
        )
        self.assertEqual(applied["metadata"]["source_copy_status"], "APPLIED")
        self.assertEqual(applied["metadata"]["source_row_copy_count"], 1237)
        canonical_items = applied["tables"]["gItemData"]
        canonical_icons = applied["tables"]["gItemGraphicsTable"]
        for canonical_id, source_id, expected_item_id in (
            (375, 40, 375),
            (589, 375, 0),
            (987, 773, 987),
        ):
            row = canonical_items[canonical_id * 40 : (canonical_id + 1) * 40]
            expected = bytearray(source_items[source_id * 40 : (source_id + 1) * 40])
            struct.pack_into("<H", expected, 10, expected_item_id)
            self.assertEqual(row, expected)
        self.assertEqual(
            canonical_icons[988 * 8 : 989 * 8], source_icons[68 * 8 : 69 * 8]
        )
        self.assertEqual(self.assets["metadata"]["source_copy_status"], "PENDING")

    def test_model_validation_fails_closed(self) -> None:
        broken_move = dict(self.move_model)
        broken_moves = list(self.move_model["moves"])
        broken_moves[512] = dict(broken_moves[512], id=9999)
        broken_move["moves"] = broken_moves
        with self.assertRaisesRegex(CFRURuntimeTableError, "contiguous"):
            build_runtime_assets(ROOT, broken_move, self.id_model)

        broken_id = dict(self.id_model)
        broken_id["fingerprint"] = "0" * 64
        with self.assertRaisesRegex(CFRURuntimeTableError, "fingerprint"):
            build_runtime_assets(ROOT, self.move_model, broken_id)

        broken_id = dict(self.id_model)
        broken_items = list(self.id_model["items"])
        broken_items[375] = dict(broken_items[375], cfru_source=None)
        broken_id["items"] = broken_items
        with self.assertRaisesRegex(CFRURuntimeTableError, "CFRU source rows"):
            build_runtime_assets(ROOT, self.move_model, broken_id)


if __name__ == "__main__":
    unittest.main()
