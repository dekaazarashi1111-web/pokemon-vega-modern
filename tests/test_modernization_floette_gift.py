from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools import modernization_floette_gift as gift
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]


class ModernizationFloetteGiftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / gift.CONFIG).read_text(encoding="utf-8"))
        cls.outputs = gift.build_outputs(ROOT)
        cls.metadata = json.loads(cls.outputs[cls.config["outputs"]["metadata"]])
        cls.contract = json.loads(cls.outputs[cls.config["outputs"]["contract"]])
        cls.checkpoint = json.loads(cls.outputs[cls.config["outputs"]["checkpoint"]])

    def test_host_transaction_matrix(self) -> None:
        host = self.metadata["validation"]["host"]
        self.assertEqual(host["status"], "PASS")
        self.assertEqual(host["scenario_count"], 13)
        self.assertTrue(host["party_delivery"])
        self.assertTrue(host["pc_delivery"])
        self.assertTrue(host["party_pc_full_unclaimed"])
        self.assertTrue(host["standard_save_rollback"])
        self.assertTrue(host["sector_save_rollback"])
        self.assertTrue(host["rollback_failure_surfaced"])

    def test_stage67_species_1029_full_surface_exact(self) -> None:
        runtime = self.contract["species_runtime"]
        self.assertEqual(runtime["status"], "PASS_STAGE67_PROVEN_AND_STAGE68_BYTE_IDENTICAL")
        self.assertEqual(runtime["required_role_count"], 11)
        self.assertEqual(runtime["missing_role_count"], 0)
        evidence = runtime["stage67"]["evidence"]
        self.assertEqual(evidence["base_stats"]["stats"], [74, 65, 67, 92, 125, 128])
        self.assertEqual(evidence["base_stats"]["types"], [23, 23])
        self.assertEqual(evidence["base_stats"]["abilities"], [167, 0, 181])
        for key in ("front_sprite", "back_sprite", "normal_palette", "shiny_palette"):
            self.assertTrue(evidence[key]["pointer_non_null"])
            self.assertTrue(evidence[key]["pointer_in_rom"])
            self.assertGreater(evidence[key]["decoded_nonzero_bytes"], 0)
        self.assertEqual(evidence["front_sprite"]["decoded_size"], 2048)
        self.assertEqual(evidence["back_sprite"]["decoded_size"], 2048)
        self.assertEqual(evidence["normal_palette"]["decoded_size"], 32)
        self.assertEqual(evidence["shiny_palette"]["decoded_size"], 32)
        self.assertEqual(evidence["icon"]["decoded_size"], 1024)
        self.assertEqual(evidence["name"]["decoded"], "フラエッテ")
        self.assertEqual(evidence["level_up"]["rows"][-1], {"move_id": 0, "level": 255})
        self.assertGreater(evidence["tm_compatibility"]["nonzero_bytes"], 0)
        self.assertGreater(evidence["tutor_compatibility"]["nonzero_bytes"], 0)

    def test_identity_override_and_safe_national_670_owner(self) -> None:
        identity = self.contract["identity"]
        self.assertEqual(identity["species_id"], 1029)
        self.assertEqual(identity["base_species_id"], 959)
        self.assertEqual(identity["canonical_national_dex"], 670)
        legacy = self.contract["legacy_collection_override"]
        self.assertEqual(
            legacy["legacy_model"]["row"]["status"],
            "UNOBTAINABLE_EVENT_FORM_EXCLUDED",
        )
        self.assertEqual(legacy["stage69_override"]["status"], "OBTAINABLE_ONE_TIME_GIFT")
        registration = legacy["national_dex_registration"]
        self.assertEqual(registration["collection_bit"], 850)
        self.assertFalse(registration["legacy_52_byte_pokedex_bitmaps_indexed"])

    def test_flag_namespace_is_dedicated_and_collision_free(self) -> None:
        flags = self.contract["claim_flag_namespace"]
        self.assertEqual(flags["claim_flag"], 0x14CD)
        self.assertEqual(flags["stage68_reserved"], {"first": 0x14A0, "last": 0x14CC, "count": 45})
        self.assertEqual(flags["collision_count"], 0)
        self.assertFalse(flags["global_manifest"]["claim_row_present"])
        self.assertFalse(flags["global_manifest"]["mutated"])
        self.assertTrue(flags["below_next_owner_boundary"])

    def test_physical_npc_and_script_graph(self) -> None:
        rom = self.outputs[self.config["outputs"]["rom"]]
        map_meta = self.metadata["map"]
        self.assertEqual(map_meta["object_count_before"], 14)
        self.assertEqual(map_meta["object_count_after"], 15)
        self.assertEqual(map_meta["gift_object"]["local_id"], 15)
        self.assertEqual((map_meta["gift_object"]["x"], map_meta["gift_object"]["y"]), (25, 19))
        self.assertTrue(map_meta["stage68_shop_local14_preserved"])
        self.assertEqual(map_meta["cell_audit"]["collision"], 0)
        events = map_meta["events_after_address"] - gift.GBA_ROM_BASE
        objects = struct.unpack_from("<I", rom, events + 4)[0] - gift.GBA_ROM_BASE
        self.assertEqual(rom[events], 15)
        npc = objects + 14 * 0x18
        self.assertEqual(rom[npc], 15)
        self.assertEqual(struct.unpack_from("<HH", rom, npc + 4), (25, 19))
        script = struct.unpack_from("<I", rom, npc + 0x10)[0]
        self.assertEqual(script, map_meta["gift_script_address"])
        script_offset = script - gift.GBA_ROM_BASE
        self.assertEqual(rom[script_offset:script_offset + 3], bytes((0x6A, 0x5A, 0x23)))
        claim = int.from_bytes(rom[script_offset + 3:script_offset + 7], "little")
        self.assertEqual(claim, self.metadata["entrypoints"]["FloetteGift_Claim"])

    def test_incremental_bps_and_declared_span(self) -> None:
        parent = (ROOT / self.config["inputs"]["parent_rom"]["path"]).read_bytes()
        rom = self.outputs[self.config["outputs"]["rom"]]
        patch = self.outputs[self.config["outputs"]["bps"]]
        self.assertEqual(apply_bps(parent, patch), rom)
        payload = self.metadata["payload"]
        map_site = self.metadata["map"]["header_offset"] + 4
        changed = [index for index, pair in enumerate(zip(parent, rom)) if pair[0] != pair[1]]
        self.assertTrue(changed)
        self.assertTrue(all(
            payload["offset"] <= index < payload["offset"] + payload["size"]
            or map_site <= index < map_site + 4
            for index in changed
        ))

    def test_generated_outputs_are_exact(self) -> None:
        for relative, raw in self.outputs.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(path.read_bytes(), raw, relative)
        rom = self.outputs[self.config["outputs"]["rom"]]
        self.assertEqual(hashlib.sha256(rom).hexdigest(), self.metadata["output"]["sha256"])
        self.assertTrue(all(self.metadata["invariants"].values()))

    def test_exact_runtime_checkpoint_is_partial_and_honest(self) -> None:
        self.assertEqual(
            self.metadata["status"],
            "PASS_HOST_AND_EXACT_PARTIAL_RUNTIME_FULL_RELOAD_PENDING",
        )
        validation = self.metadata["validation"]
        self.assertEqual(
            validation["exact_rom_runtime_smoke"],
            "PARTIAL_PASS_FULL_AND_RELOAD_PENDING",
        )
        self.assertEqual(validation["heavy_test_runs"], 3)
        gate = validation["runtime_gate"]
        self.assertEqual(gate["attempt_count"], 3)
        self.assertEqual(gate["retry_count"], 2)
        self.assertTrue(all(gate["exact_rom_confirmed"].values()))
        self.assertTrue(all(gate["host_confirmed_pending_exact_rom"].values()))
        self.assertEqual(
            set(gate["not_yet_executed_exact_rom"].values()), {"PENDING"},
        )
        self.assertEqual(
            gate["corrected_runner"]["status"],
            "COMPILE_PASS_NOT_EXECUTED_PER_THREE_ATTEMPT_LIMIT",
        )
        self.assertFalse(any(row["rom_transaction_failure"] for row in gate["attempts"]))

    def test_corrected_runner_uses_linked_dpe_box_abi(self) -> None:
        abi = self.contract["acquisition_abi"]["entrypoints"]
        self.assertEqual(abi["GetBoxedMonPtr"]["thumb_entrypoint"], 0x09123AE1)
        self.assertEqual(abi["GetBoxMonDataAt"]["thumb_entrypoint"], 0x09123BE5)
        self.assertEqual(abi["ZeroBoxMonAt"]["thumb_entrypoint"], 0x091239C9)
        runner = (
            ROOT
            / "overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c"
        ).read_text(encoding="utf-8")
        self.assertIn("fg_get_boxed_mon_ptr", runner)
        self.assertNotIn("FG_SET_BOX_MON", runner)

    def test_builder_is_byte_deterministic(self) -> None:
        self.assertEqual(self.outputs, gift.build_outputs(ROOT))


if __name__ == "__main__":
    unittest.main()
