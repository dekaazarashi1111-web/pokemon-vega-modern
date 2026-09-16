from __future__ import annotations

import copy
import json
import struct
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESTORATION_ZIP = ROOT / (
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)
PUBLISHED = ROOT / "content/modernization/p02_evolution_contract.json"

from tools.modernization_evolution import (  # noqa: E402
    ModernizationEvolutionError,
    build_evolution_contract,
    normalize_evolution_rows,
    parse_evolution_binary,
    parse_runtime_method_enum,
    stable_json,
)
from tools.modernization_identity import load_manifests  # noqa: E402


class ModernizationP02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifests = load_manifests(ROOT)
        cls.contract = build_evolution_contract(ROOT, RESTORATION_ZIP)
        cls.rows = cls.contract["current_table"]["rows"]
        cls.by_key = {row["row_key"]: row for row in cls.rows}

    def test_all_runtime_rows_have_stable_species_and_form_identity(self) -> None:
        summary = self.contract["current_table"]["summary"]
        self.assertEqual(summary["rows"], 850)
        self.assertEqual(summary["families"], {
            "BATTLE_TRANSFORM": 172,
            "PERSISTENT": 678,
        })
        self.assertEqual(summary["vega_prefix_rows"], 202)
        self.assertEqual(summary["dpe_append_rows"], 648)
        self.assertEqual(len(self.by_key), len(self.rows))
        for row in self.rows:
            self.assertTrue(row["row_key"].startswith("SPECIES_KEY_"))
            self.assertTrue(row["source"]["species_key"].startswith("SPECIES_KEY_"))
            self.assertTrue(row["target"]["species_key"].startswith("SPECIES_KEY_"))
            self.assertEqual(
                row["source"]["form_key"],
                self.manifests["species"].by_key[row["source"]["species_key"]]["form_key"],
            )
            self.assertEqual(
                row["target"]["form_key"],
                self.manifests["species"].by_key[row["target"]["species_key"]]["form_key"],
            )

        caterpie = self.by_key["SPECIES_KEY_CATERPIE#SLOT_00"]
        self.assertEqual(caterpie["source"]["canonical_id"], 649)
        self.assertEqual(caterpie["target"]["species_key"], "SPECIES_KEY_METAPOD")
        self.assertEqual(caterpie["condition"]["parameter"]["value"], 7)
        self.assertNotIn("SPECIES_KEY_EGG#SLOT_00", self.by_key)

    def test_adopted_vega_unique_and_review_only_are_disjoint(self) -> None:
        adopted = self.contract["adopted_specifications"]["vega_unique_preservation"]
        review = self.contract["review_only"]
        self.assertEqual(len(adopted), 26)
        self.assertEqual(len({row["row_key"] for row in adopted}), 26)
        self.assertTrue(all(row["policy"] == "ADOPTED_PRESERVE_EXACT" for row in adopted))
        self.assertTrue(all(
            self.by_key[row["row_key"]]["baseline_policy"]
            == "ADOPT_AND_PRESERVE_VEGA_UNIQUE"
            for row in adopted
        ))
        self.assertEqual(review["summary"], {
            "zip05_rows": 128,
            "zip05_exact_current": 119,
            "zip05_not_current": 9,
            "description_mismatch_candidates": 15,
            "public_vega_difference_candidates": 10,
            "missing_official_branch_families": 3,
        })
        self.assertTrue(all(
            row["policy"] == "REVIEW_ONLY_NOT_ADOPTED"
            for section in (
                review["description_mismatch_candidates"],
                review["public_vega_difference_candidates"],
            )
            for row in section
        ))

    def test_runtime_method_semantics_are_bound_to_actual_cfru_sources(self) -> None:
        runtime = self.contract["runtime_contract"]
        self.assertEqual(runtime["method_abi"]["EVO_MOVE"], 26)
        self.assertEqual(runtime["method_abi"]["EVO_DUDUNSPARCE_TWO"], 42)
        self.assertEqual(runtime["method_abi"]["EVO_DUDUNSPARCE_THREE"], 43)
        self.assertEqual(runtime["method_abi"]["EVO_TERASTAL"], 252)
        self.assertEqual(runtime["method_abi"]["EVO_MEGA"], 254)
        self.assertEqual(runtime["friendship_threshold"], 220)
        self.assertTrue(runtime["time_enabled"])
        self.assertTrue(runtime["hold_item_removal_enabled"])
        self.assertEqual(runtime["unsupported_methods"], ["EVO_DAMAGE_LOCATION"])
        self.assertEqual(
            runtime["table"]["evo_none_parameter_residues"]["count"], 24,
        )
        self.assertEqual(
            runtime["table"]["evo_none_parameter_residues"]["classification"],
            "IGNORED_PADDING_NOT_EVOLUTION_ROWS",
        )

        header = (ROOT / "vendor/upstream/CFRU-JP/include/pokemon.h").read_bytes()
        self.assertEqual(parse_runtime_method_enum(header), runtime["method_abi"])

    def test_parameter_namespaces_and_battle_transform_family_are_explicit(self) -> None:
        rayquaza = self.by_key["SPECIES_KEY_RAYQUAZA#SLOT_00"]
        self.assertEqual(rayquaza["method"]["family"], "BATTLE_TRANSFORM")
        self.assertEqual(rayquaza["condition"]["parameter"]["role"], "MOVE")
        self.assertEqual(rayquaza["condition"]["extra"]["variant"], "WISH_MOVE")

        hold_item = next(row for row in self.rows if row["method"]["id"] == 35)
        self.assertEqual(hold_item["condition"]["parameter"]["role"], "LEVEL")
        self.assertEqual(hold_item["condition"]["extra"]["role"], "ITEM")
        persistent = next(row for row in self.rows if row["method"]["id"] == 4)
        self.assertEqual(persistent["method"]["family"], "PERSISTENT")

    def test_known_generator_errors_are_interpreted_and_located(self) -> None:
        findings = {
            row["finding_key"]: row for row in self.contract["findings"]["rows"]
        }
        self.assertEqual(self.contract["static_gate"], "PASS")
        self.assertEqual(
            self.contract["release_gate"],
            "BLOCKED_BY_REQUIRED_FIXES_AND_DEFERRED_RUNTIME_ACCEPTANCE",
        )
        self.assertEqual(self.contract["findings"]["required_fix_count"], 1)
        rayquaza = findings["P02-EVO-RAYQUAZA-MOVE-NAMESPACE"]
        self.assertEqual(rayquaza["current"]["parameter_key"], "MOVE_KEY_OVERDRIVE")
        self.assertEqual(rayquaza["current"]["parameter_id"], 773)
        self.assertEqual(
            rayquaza["classification"],
            "CONFIRMED_HISTORICAL_ARTIFACT_NAMESPACE_ERROR",
        )
        self.assertEqual(rayquaza["required"], {
            "parameter_key": "MOVE_KEY_DRAGONASCENT",
            "parameter_id": 630,
            "producer_handles_wish_as_move": True,
        })
        self.assertEqual(rayquaza["producer_cause"]["function"], "merge_evolutions")
        self.assertTrue(rayquaza["producer_cause"]["root_fix_applied"])
        namespace = self.contract["runtime_contract"]["producer"]["parameter_namespace_policy"]
        self.assertEqual(namespace["status"], "PASS")
        self.assertTrue(namespace["historical_default_output_preserved"])
        self.assertEqual(namespace["legacy_resolved_parameter_id"], 773)
        self.assertEqual(namespace["modernization_resolved_parameter_id"], 630)
        table = self.contract["runtime_contract"]["table"]
        expected_file_offset = (
            table["rom_file_offset"] + 645 * 128 + 2
        )
        self.assertEqual(rayquaza["current"]["rom_file_offset"], expected_file_offset)
        self.assertEqual(rayquaza["current"]["rom_file_offset_hex"], "0x01F8E1BA")

        charizard = findings["P02-EVO-LEGACY-MEGA-PARAM"]
        self.assertEqual(charizard["current_parameter"]["reference"]["key"], "ITEM_KEY_TM15")
        self.assertEqual(charizard["disposition"], "REVIEW_ONLY_NO_AUTOMATIC_REWRITE")

    def test_missing_branches_preserve_vega_and_gate_move_routes_on_p03(self) -> None:
        missing = self.contract["review_only"]["missing_official_branch_candidates"]
        by_source = {row["source"]["species_key"]: row for row in missing}
        self.assertEqual(set(by_source), {
            "SPECIES_KEY_GIRAFARIG", "SPECIES_KEY_SCYTHER", "SPECIES_KEY_DUNSPARCE",
        })
        self.assertEqual(
            by_source["SPECIES_KEY_GIRAFARIG"]["existing_vega_target"]["species_key"],
            "SPECIES_KEY_VEGA_055",
        )
        self.assertEqual(
            by_source["SPECIES_KEY_DUNSPARCE"]["existing_vega_target"]["species_key"],
            "SPECIES_KEY_VEGA_342",
        )
        self.assertFalse(by_source["SPECIES_KEY_SCYTHER"]["existing_vega_edge_present"])
        self.assertTrue(all(row["policy"] == "REVIEW_ONLY_PRESERVE_VEGA_BRANCH" for row in missing))
        kleavor = by_source["SPECIES_KEY_SCYTHER"]["proposed_official_branches"][0]
        self.assertEqual(kleavor["requirement"]["key"], "ITEM_KEY_BLACK_AUGURITE")
        self.assertEqual(kleavor["requirement"]["canonical_id"], 946)
        self.assertEqual(kleavor["requirement"]["consume_policy"], "ON_EFFECT")
        self.assertEqual(kleavor["upstream_dpe_source"]["line"], 136)

        dependencies = self.contract["p03_dependencies"]["dependencies"]
        self.assertEqual(len(dependencies), 3)
        self.assertEqual(len({row["dependency_key"] for row in dependencies}), 3)
        self.assertEqual({row["required_move_key"] for row in dependencies}, {
            "MOVE_KEY_TWINBEAM", "MOVE_KEY_HYPERDRILL",
        })
        self.assertTrue(all(not row["satisfied_by_current_level_up_table"] for row in dependencies))
        self.assertFalse(self.contract["p03_dependencies"]["all_satisfied_by_current_level_up_table"])
        self.assertEqual(self.contract["acquisition_contract"]["item_count"], 75)
        self.assertTrue(self.contract["deferred_runtime_acceptance"]["must_not_be_reported_as_passed"])

    def test_binary_parser_rejects_size_hidden_rows_and_ambiguous_none_payload(self) -> None:
        with self.assertRaisesRegex(ModernizationEvolutionError, "size不一致"):
            parse_evolution_binary(b"\0" * 127, species_count=1)

        hidden = bytearray(128)
        struct.pack_into("<HHHH", hidden, 8, 4, 7, 1, 0)
        with self.assertRaisesRegex(ModernizationEvolutionError, "EVO_NONE後"):
            parse_evolution_binary(bytes(hidden), species_count=1)

        payload = bytearray(128)
        struct.pack_into("<HHHH", payload, 0, 0, 22, 1, 0)
        with self.assertRaisesRegex(ModernizationEvolutionError, "target/extra payload"):
            parse_evolution_binary(bytes(payload), species_count=1)

        harmless_prefix_residue = bytearray(128)
        struct.pack_into("<HHHH", harmless_prefix_residue, 0, 0, 22, 0, 0)
        self.assertEqual(parse_evolution_binary(bytes(harmless_prefix_residue), species_count=1), [])

    def test_unknown_method_and_out_of_range_target_fail_closed(self) -> None:
        fixture = [{
            "source_id": 1,
            "slot": 0,
            "method_id": 999,
            "parameter": 1,
            "target_id": 2,
            "extra": 0,
            "table_offset": 128,
        }]
        with self.assertRaisesRegex(ModernizationEvolutionError, "未定義Evolution method"):
            normalize_evolution_rows(fixture, self.manifests, runtime_address=0x09F79F38)

        invalid_target = copy.deepcopy(fixture)
        invalid_target[0].update({"method_id": 4, "target_id": 1621})
        with self.assertRaisesRegex(ModernizationEvolutionError, "範囲外"):
            normalize_evolution_rows(invalid_target, self.manifests, runtime_address=0x09F79F38)

    def test_published_contract_is_deterministic_and_check_is_read_only(self) -> None:
        self.assertEqual(PUBLISHED.read_bytes(), stable_json(self.contract))
        before = PUBLISHED.read_bytes()
        before_mtime = PUBLISHED.stat().st_mtime_ns
        completed = subprocess.run(
            ["python3", "scripts/build_modernization_p02.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("MODERNIZATION_P02_CHECK=PASS", completed.stdout)
        self.assertEqual(PUBLISHED.read_bytes(), before)
        self.assertEqual(PUBLISHED.stat().st_mtime_ns, before_mtime)


if __name__ == "__main__":
    unittest.main()
