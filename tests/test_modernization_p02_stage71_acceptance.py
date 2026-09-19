import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_modernization_p02_stage71_acceptance.py"
CONFIG = ROOT / "config" / "modernization_p02_stage71_acceptance_gate.json"


def load_gate():
    spec = importlib.util.spec_from_file_location("p02_stage71_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModernizationP02Stage71AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.validated_config, cls.preflight = cls.gate.build_preflight(CONFIG)

    def valid_runtime_result(self):
        return {
            "schema_version": 1,
            "status": "PASS",
            "classification": "STAGE71_EXACT_ROM_NORMAL_INPUT_AND_FRESH_CORE",
            "rom_sha256": self.config["inputs"]["stage71_rom"]["sha256"],
            "known_good_seed_sha256":
                self.config["inputs"]["known_good_continue_save"]["sha256"],
            "boot_route": "NORMAL_TITLE_CONTINUE_PINNED_SAVE",
            "initial_normal_continue_field": True,
            "fixture_replacement_after_field": True,
            "warnings_errors": 0,
            "temporary_save_only": True,
            "direct_conditions": {
                "level": True,
                "friendship": True,
                "known_move": True,
                "trade": True,
                "night_form": True,
                "level_held_item_six": {
                    "species_count": 6,
                    "conditional_selected": 6,
                    "conditional_item_consumed": 6,
                    "below_level_rejected": 6,
                    "wrong_or_missing_item_regular": 12,
                    "hidden_ability_preserved": 24,
                    "payload_pc_seen": True,
                },
            },
            "normal_evolution_cancel": {
                "normal_bag_party_input": True,
                "scene_callbacks_seen": True,
                "physical_b_cancel": True,
                "source_retained": True,
                "four_moves_retained": True,
                "ability_slot_retained": True,
            },
            "normal_evolution_success": {
                "normal_bag_party_input": True,
                "scene_callbacks_seen": True,
                "target_applied": True,
                "four_moves_retained": True,
                "ability_slot_retained": True,
                "ability_matches_slot": True,
            },
            "conditional_form_success": {
                "normal_bag_party_input": True,
                "scene_callbacks_seen": True,
                "exact_form_applied": True,
                "condition_item_consumed": True,
                "four_moves_retained": True,
                "hidden_ability_preserved": True,
                "ability_matches_hidden": True,
            },
            "bag_item_use": {
                "normal_start_bag_party_input": True,
                "scene_callbacks_seen": True,
                "target_applied": True,
                "bag_item_consumed": True,
                "four_moves_retained": True,
            },
            "bag_item_missing": {
                "normal_start_bag_input_attempted": True,
                "item_absent": True,
                "party_not_opened_for_item": True,
                "species_unchanged": True,
            },
            "save_reload": {
                "stock_save_twice": True,
                "original_core_destroyed": True,
                "fresh_core_created": True,
                "stock_load_succeeded": True,
                "normal_continue_load_succeeded": True,
                "exact_form_reloaded": True,
                "four_moves_reloaded": True,
                "condition_item_still_consumed": True,
                "hidden_ability_reloaded": True,
                "ability_matches_hidden": True,
            },
        }

    def test_final_stage71_identity_and_acceptance_routes_are_pinned(self):
        self.gate._validate_config(self.config)
        self.assertEqual(
            self.config["inputs"]["stage71_rom"]["sha256"],
            "dbcc1194511f234c7d34c196082d59bfc0cb6aca6bb3b9c0f911bc8add4230bb",
        )
        self.assertEqual(self.config["runtime"]["process_runs"], 2)
        self.assertEqual(len(self.config["acceptance"]["required_routes"]), 11)
        self.assertEqual(
            self.config["inputs"]["known_good_continue_save"],
            {
                "path": ".local/60_wild_species_root_repair.srm",
                "size": 131072,
                "sha256":
                    "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb",
            },
        )
        boot = self.config["runtime"]["boot_fixture"]
        self.assertEqual(
            boot["policy"],
            "PINNED_KNOWN_GOOD_SAVE_NORMAL_TITLE_CONTINUE_THEN_RAM_FIXTURE_REPLACEMENT",
        )
        self.assertTrue(boot["source_save_never_mutated"])
        self.assertEqual(
            (boot["map_group"], boot["map_num"], boot["x"], boot["y"]),
            (96, 5, 20, 20),
        )

    def test_static_stage71_identity_symbols_and_repaired_rows(self):
        rom = self.gate._fixed(
            self.config["inputs"]["stage71_rom"], "Stage71 ROM"
        )
        metadata = self.gate._fixed(
            self.config["inputs"]["stage71_metadata"], "Stage71 metadata"
        )
        allocation = self.gate._fixed(
            self.config["inputs"]["stage71_allocation"], "Stage71 allocation"
        )
        identity = self.gate._validate_stage71_inputs(
            self.config, rom, metadata, allocation
        )
        self.assertTrue(identity["stage71_target_allocation_content_hash_verified"])
        self.assertEqual(identity["allocation_row_count_structural"], 74)
        self.assertEqual(
            len(self.gate._validate_symbols(rom, self.config)), 8
        )
        rows = self.gate._validate_repair_rows(rom, self.config)
        self.assertEqual(rows["species_count"], 6)
        self.assertEqual(
            rows["representative_rows"]["SPECIES_KEY_TOGETIC"],
            [7, 93, 20, 0],
        )

    def test_harness_compiles_without_running_mgba(self):
        self.assertEqual(
            self.validated_config["status"], "STAGE71_FINAL_IDENTITY_PINNED"
        )
        self.assertEqual(self.preflight["compilation"]["status"], "PASS")
        self.assertEqual(self.preflight["repaired_rows"]["species_count"], 6)
        self.assertTrue(
            self.preflight["known_good_continue_save"]["identity_verified"]
        )

    def test_runtime_schema_rejects_every_required_false_claim(self):
        valid = self.valid_runtime_result()
        self.gate._validate_runtime_result(valid, self.config)
        mutations = [
            ("direct_conditions", "night_form"),
            ("normal_evolution_cancel", "physical_b_cancel"),
            ("normal_evolution_success", "ability_matches_slot"),
            ("conditional_form_success", "hidden_ability_preserved"),
            ("bag_item_use", "bag_item_consumed"),
            ("bag_item_missing", "party_not_opened_for_item"),
            ("save_reload", "fresh_core_created"),
        ]
        for section, key in mutations:
            with self.subTest(section=section, key=key):
                broken = copy.deepcopy(valid)
                broken[section][key] = False
                with self.assertRaises(
                    self.gate.ModernizationP02Stage71AcceptanceError
                ):
                    self.gate._validate_runtime_result(broken, self.config)

    def test_c_harness_uses_normal_input_and_never_calls_begin_scene_directly(self):
        source = (ROOT / self.config["runtime"]["runner_source"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("p02s_enter_bag_physical", source)
        self.assertIn("p02s_enter_item_party", source)
        self.assertIn("p02s_continue_to_field", source)
        self.assertIn("p02s_install_field_fixture", source)
        self.assertIn("p02-stage-diagnostic stage=", source)
        main = source[source.index("int main(") :]
        self.assertNotIn("qol_run_field_trace(core)", main)
        self.assertNotIn("QOL_B_RETURN_WARP", main)
        self.assertNotIn("p02s_run_field_trace", source)
        self.assertNotIn("qol_initialize_save(argv[2])", source)
        self.assertIn("QOL_KEY_B", source)
        self.assertIn("QOL_TRY_SAVING_DATA", source)
        self.assertIn("qol_close(core);\n    core = NULL;", source)
        self.assertNotIn("QOL_LOAD_GAME_DATA", source)
        self.assertIn('p02s_continue_to_field(core, "fresh_core_normal_continue")', source)
        self.assertNotIn("0x080CEF01U", source)
        runner = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("shutil.copyfile(seed_save_path, save)", runner)
        self.assertIn("expected_seed_sha", runner)

    def test_checkpoint_records_two_failed_attempts(self):
        runner = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"failed_predecessor_attempt_sets": 2', runner)
        self.assertIn(
            '"HARNESS_SYNTHETIC_POST_TRACE_WARP_SOFT_RESET"', runner
        )
        self.assertIn('"HARNESS_NORMAL_BAG_PARTY_ENTRY_FAILED"', runner)

    def test_published_stopped_checkpoint_is_fail_closed(self):
        evidence = json.loads(
            (ROOT / self.config["output"]).read_text(encoding="utf-8")
        )
        self.gate._validate_stopped(
            evidence, self.validated_config, self.preflight
        )
        self.assertEqual(evidence["status"], "STOPPED_EXACT_UI_PENDING")
        self.assertEqual(
            evidence["execution"]["p02_production_runtime_judgment"],
            "UNJUDGED",
        )
        self.assertFalse(evidence["claims"]["full_evolution_acceptance"])
        self.assertNotIn("runtime_result", evidence)


if __name__ == "__main__":
    unittest.main()
