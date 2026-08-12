#!/usr/bin/env python3
"""T04 move-port統合generatorの焦点テスト。"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_move_port import (
    MANIFEST_HEADER,
    MovePortError,
    build_move_model,
    render_artifacts,
    validate_move_model,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/move_port.json"
ROM_PATH = ROOT / "build/reference/vega.gba"


@unittest.skipUnless(CONFIG_PATH.is_file() and ROM_PATH.is_file(), "T04 fixed inputs are unavailable")
class MovePortBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.model = build_move_model(ROOT, cls.config)
        cls.artifacts = render_artifacts(cls.model)

    def test_exact_frozen_append_and_alias_contract(self) -> None:
        summary = self.model["summary"]
        self.assertEqual(summary["frozen_count"], 512)
        self.assertEqual(summary["mapped_cfru_count"], 441)
        self.assertEqual(summary["appended_count"], 551)
        self.assertEqual((summary["move_count"], summary["last_id"]), (1063, 1062))
        self.assertEqual([row["id"] for row in self.model["moves"]], list(range(1063)))
        self.assertEqual(
            [row["vega_id"] for row in self.model["moves"][:512]], list(range(512))
        )
        self.assertEqual(len(self.model["aliases"]), 992)
        self.assertEqual(
            [row["cfru_source_id"] for row in self.model["aliases"]], list(range(992))
        )

    def test_v3_precedence_and_distinct_name_collision_resolution(self) -> None:
        moves = self.model["moves"]
        self.assertEqual(
            (moves[470]["move_key"], moves[470]["display_name"], moves[470]["classification"]),
            ("MOVE_KEY_SOUL_BITE", "ソウルバイト", "VEGA_EXCLUSIVE_V3"),
        )
        self.assertEqual(
            (moves[509]["move_key"], moves[509]["display_name"], moves[509]["classification"]),
            ("MOVE_KEY_DARK_SNIPE", "ダークスナイプ", "VEGA_EXCLUSIVE_V3"),
        )
        aliases = {row["cfru_symbol"]: row for row in self.model["aliases"]}
        self.assertGreaterEqual(aliases["MOVE_JAWLOCK"]["canonical_id"], 512)
        self.assertGreaterEqual(aliases["MOVE_SNIPESHOT"]["canonical_id"], 512)
        self.assertEqual(aliases["MOVE_POUND"]["canonical_id"], 1)
        self.assertEqual(moves[511]["classification"], "VEGA_COMPAT_DUPLICATE")

    def test_all_v3_rows_join_and_numeric_triples_reach_battle_and_bridge(self) -> None:
        self.assertEqual(self.model["v3"]["modern_effects"]["count"], 61)
        self.assertEqual(self.model["v3"]["vega_exclusive"]["count"], 70)
        self.assertEqual(self.model["summary"]["v3_numeric_override_count"], 101)
        fly = next(
            row
            for row in self.model["v3"]["modern_effects"]["joins"]
            if row["move_name"] == "そらをとぶ"
        )
        self.assertEqual(fly["numeric_triple"], [90, 95, 15])
        battle = self.model["moves"][fly["vega_id"]]["battle"]
        self.assertEqual((battle["power"], battle["accuracy"], battle["pp"]), (90, 95, 15))
        offset = self.model["bridge"]["tables"]["battle"]["offset"] + fly["vega_id"] * 12
        raw = self.model["_bridge_bytes"][offset : offset + 12]
        self.assertEqual((raw[1], raw[3], raw[4]), (90, 95, 15))
        self.assertEqual(self.model["moves"][445]["battle"]["accuracy"], 85)
        self.assertEqual(
            (
                self.model["moves"][479]["battle"]["power"],
                self.model["moves"][479]["battle"]["accuracy"],
                self.model["moves"][479]["battle"]["pp"],
            ),
            (50, 0, 15),
        )
        self.assertEqual(self.model["moves"][448]["battle"]["secondary"], 20)

    def test_all_exclusive_effects_have_compiled_adapter_plans(self) -> None:
        adapters = [row for row in self.model["moves"] if row["effect_adapter"] is not None]
        self.assertEqual(len(adapters), 70)
        self.assertEqual(len({row["effect_adapter"]["handler_symbol"] for row in adapters}), 70)
        source = self.artifacts[
            "generated/engine/moves/move_effect_adapters.c"
        ].decode("ascii")
        for row in adapters:
            adapter = row["effect_adapter"]
            self.assertEqual(adapter["kind"], "GENERATED_ADAPTER")
            self.assertEqual(adapter["cfru_effect_id"], 0)
            self.assertEqual(row["battle"]["effect"], 0)
            self.assertTrue(adapter["effect_plan"]["operations"])
            definition = f" {adapter['handler_symbol']}(struct MovePortEffectRuntime *runtime)"
            self.assertEqual(source.count(definition), 1)
        self.assertEqual(self.model["summary"]["effect_adapter_count"], 70)

    def test_generated_effect_handlers_execute_every_adapter_plan(self) -> None:
        if shutil.which("cc") is None:
            self.skipTest("host C compiler is unavailable")
        with tempfile.TemporaryDirectory(prefix="t04-adapter-run-") as raw:
            directory = Path(raw)
            (directory / "moves_merged.h").write_bytes(
                self.artifacts["generated/engine/moves/moves_merged.h"]
            )
            (directory / "move_effect_adapters.c").write_bytes(
                self.artifacts["generated/engine/moves/move_effect_adapters.c"]
            )
            (directory / "probe.c").write_text(
                """#include "moves_merged.h"
static int32_t apply(void *context, enum MovePortAdapterOperation operation) {
    (void) operation; ++*(uint32_t *)context; return 0;
}
int main(void) {
    uint32_t calls = 0; struct MovePortEffectRuntime runtime = { &calls, apply };
    if (gMovePortEffectAdapterCount != 70) return 1;
    for (uint32_t i = 0; i < gMovePortEffectAdapterCount; ++i)
        if (gMovePortEffectAdapters[i].handler(&runtime) != 0) return 2;
    return calls >= 70 ? 0 : 3;
}
""",
                encoding="ascii",
            )
            binary = directory / "probe"
            completed = subprocess.run(
                [
                    "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                    str(directory / "move_effect_adapters.c"), str(directory / "probe.c"),
                    "-I", str(directory), "-o", str(binary),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(subprocess.run([str(binary)], check=False).returncode, 0)

    def test_game_encoding_aliases_and_descriptions_are_resolved(self) -> None:
        header = self.artifacts["generated/engine/moves/moves_merged.h"].decode("ascii")
        self.assertIn("#define MOVE_POUND MOVE_KEY_POUND", header)
        alias_lines = [
            line
            for line in header.splitlines()
            if line.startswith("#define MOVE_") and not line.startswith("#define MOVE_PORT_")
        ]
        self.assertEqual(len(alias_lines), 992)
        names = self.artifacts["generated/engine/moves/move_names.c"].decode("ascii")
        self.assertIn("sMoveName_1[] = { 0x1A, 0x10, 0x08, 0xFF }", names)
        self.assertNotIn("0xE3, 0x81", names)
        descriptions = self.artifacts[
            "generated/engine/moves/move_descriptions.c"
        ].decode("ascii")
        self.assertIn("sMoveDescription_1[]", descriptions)
        self.assertTrue(all(not row["description"]["text"].startswith("@") for row in self.model["moves"]))
        self.assertTrue(
            all(bytes.fromhex(row["description"]["raw_hex"])[-1] == 0xFF for row in self.model["moves"])
        )

    def test_bridge_is_exact_five_table_layout_with_overridden_names(self) -> None:
        bridge = self.model["bridge"]
        blob = self.artifacts["generated/engine/moves/vega_bridge.bin"]
        self.assertEqual(len(blob), 44032)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), bridge["sha256"])
        self.assertEqual(
            {name: row["offset"] for name, row in bridge["tables"].items()},
            {"names": 0, "battle": 4096, "descriptions": 10240, "animations": 40960, "effects": 43008},
        )
        self.assertEqual(sum(row["reference_count"] for row in bridge["tables"].values()), 178)
        names_offset = bridge["tables"]["names"]["offset"]
        self.assertEqual(blob[names_offset + 470 * 8 : names_offset + 471 * 8].hex(), "5f5379965264ffff")
        self.assertEqual(blob[names_offset + 509 * 8 : names_offset + 510 * 8].hex(), "91ae585d65529dff")

    def test_artifact_set_manifest_and_render_are_deterministic(self) -> None:
        expected = {
            "generated/engine/moves/move_port.json",
            "generated/engine/moves/moves_merged.h",
            "generated/engine/moves/battle_moves.c",
            "generated/engine/moves/move_names.c",
            "generated/engine/moves/move_descriptions.c",
            "generated/engine/moves/move_effect_map.c",
            "generated/engine/moves/move_animation_map.c",
            "generated/engine/moves/move_effect_adapters.c",
            "generated/engine/moves/vega_bridge.bin",
            "generated/engine/moves/layout.json",
            "manifests/move_ids.csv",
        }
        self.assertEqual(set(self.artifacts), expected)
        self.assertEqual(self.artifacts, render_artifacts(self.model))
        manifest = list(
            csv.DictReader(
                io.StringIO(self.artifacts["manifests/move_ids.csv"].decode("utf-8")),
            )
        )
        self.assertEqual(tuple(manifest[0]), MANIFEST_HEADER)
        self.assertEqual(len(manifest), 1063)
        public = json.loads(
            self.artifacts["generated/engine/moves/move_port.json"].decode("utf-8")
        )
        self.assertNotIn("_bridge_bytes", public)
        self.assertEqual(public["summary"], self.model["summary"])

    def test_model_and_input_fail_closed(self) -> None:
        broken = copy.deepcopy(self.model)
        broken["moves"][512]["id"] = 9999
        with self.assertRaisesRegex(MovePortError, "contiguous"):
            validate_move_model(broken)
        bad_config = copy.deepcopy(self.config)
        bad_config["vega"]["rom_sha256"] = "00" * 32
        with self.assertRaisesRegex(MovePortError, "rom_sha256"):
            build_move_model(ROOT, bad_config)
        bad_duplicate = copy.deepcopy(self.config)
        bad_duplicate["mapping_policy"]["duplicate_name_resolution"]["1"]["canonical_vega_id"] = 511
        with self.assertRaisesRegex(MovePortError, "MOVE_POUND"):
            build_move_model(ROOT, bad_duplicate)
        bad_adapter = copy.deepcopy(self.model)
        bad_adapter["moves"][470]["effect_adapter"]["handler_symbol"] = ""
        with self.assertRaisesRegex(MovePortError, "adapter"):
            validate_move_model(bad_adapter)


if __name__ == "__main__":
    unittest.main()
