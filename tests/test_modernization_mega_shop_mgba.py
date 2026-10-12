from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import run_modernization_mega_shop_mgba as gate  # noqa: E402


class ModernizationMegaShopMgbaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence_path = ROOT / gate.OUTPUT
        cls.evidence = json.loads(cls.evidence_path.read_text(encoding="utf-8"))

    def test_final_stage68_rom_and_metadata_are_exactly_pinned(self) -> None:
        inputs = self.evidence["inputs"]
        for key, relative in (
            ("rom", gate.ROM),
            ("metadata", gate.METADATA),
            ("symbols", gate.SYMBOLS),
            ("checkpoint", gate.CHECKPOINT),
        ):
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(inputs[key]["path"], relative.as_posix())
            self.assertEqual(inputs[key]["size"], len(raw))
            self.assertEqual(inputs[key]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(
            self.evidence["stage68_metadata_validation_state_at_run"],
            "PENDING",
        )

    def test_exact_rom_runtime_covers_required_stateful_routes(self) -> None:
        result = self.evidence["runtime_result"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["warnings_errors"], 0)
        self.assertEqual(result["representative_indices"], [0, 22, 44])
        self.assertEqual(result["representative_item_ids"], [999, 1021, 1043])
        self.assertEqual(result["representative_claim_flags"], [5280, 5302, 5324])
        self.assertEqual(result["accepted_item_boundary_ids"], [999, 1023, 1024, 1043])
        self.assertEqual(result["first_rejected_item_id"], 1044)
        self.assertEqual(result["hold_effect"], 73)
        self.assertEqual(result["price_bp"], 16)
        self.assertEqual(result["initial_bp"], 100)
        self.assertEqual(result["final_bp"], 52)
        self.assertEqual(set(result["checks"]), gate.EXPECTED_CHECKS)
        self.assertTrue(all(result["checks"].values()))

    def test_fresh_core_and_claim_boundaries_are_not_overclaimed(self) -> None:
        runtime = self.evidence["runtime"]
        claims = self.evidence["claims"]
        self.assertEqual(runtime["process_runs"], 1)
        self.assertEqual(runtime["core_instances"], 2)
        self.assertTrue(runtime["fresh_core"])
        self.assertFalse(runtime["host_test_overlay"])
        self.assertTrue(claims["normal_save_fresh_core_once_rejection"])
        self.assertFalse(claims["all_45_runtime_purchases"])
        self.assertFalse(claims["physical_menu_input_e2e"])
        self.assertEqual(self.evidence["diagnostic_history"], gate.DIAGNOSTIC_HISTORY)
        self.assertFalse(self.evidence["diagnostic_history"]["rom_defect"])

    def test_runner_uses_production_rom_functions_and_physical_graph(self) -> None:
        source = (ROOT / gate.RUNNER).read_text(encoding="utf-8")
        self.assertNotIn("#define MODERNIZATION_MEGA_SHOP_HOST_TEST", source)
        self.assertIn("MEGA_FACTORY_ADD_BP", source)
        self.assertIn("MEGA_ADD_BAG", source)
        self.assertIn("MEGA_SAVE_LOAD", source)
        self.assertIn("MEGA_SET_SAVE_BLOCK_POINTERS", source)
        self.assertIn("MEGA_SET_BAG_POCKETS", source)
        self.assertIn("MEGA_CFRU_SANITIZE_ITEM", source)
        self.assertIn("MEGA_ITEM_GET_NAME", source)
        self.assertIn("MEGA_ITEM_GET_HOLD_EFFECT", source)
        self.assertIn("MEGA_IS_MEGA_STONE", source)
        self.assertIn("mega_verify_map", source)
        self.assertIn("mega_read_u32_unaligned(core, npc_script + 3U)", source)
        self.assertEqual(source.count("mega_open_core("), 3)
        self.assertEqual(source.count("mega_close_core("), 3)

    def test_result_validator_fails_closed_on_price_or_warning_drift(self) -> None:
        tampered = copy.deepcopy(self.evidence["runtime_result"])
        tampered["price_bp"] = 15
        with self.assertRaisesRegex(
            gate.ModernizationMegaShopMgbaError,
            "runner result",
        ):
            gate._validate_runner_result(tampered)
        tampered = copy.deepcopy(self.evidence["runtime_result"])
        tampered["warnings_errors"] = 1
        with self.assertRaisesRegex(
            gate.ModernizationMegaShopMgbaError,
            "runner result",
        ):
            gate._validate_runner_result(tampered)

    def test_check_is_fingerprint_bound_and_read_only(self) -> None:
        before = self.evidence_path.read_bytes()
        before_state = (
            self.evidence_path.stat().st_mtime_ns,
            hashlib.sha256(before).hexdigest(),
        )
        completed = subprocess.run(
            ["python3", "scripts/run_modernization_mega_shop_mgba.py", "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("MODERNIZATION_MEGA_SHOP_MGBA_CHECK=PASS", completed.stdout)
        after_state = (
            self.evidence_path.stat().st_mtime_ns,
            hashlib.sha256(self.evidence_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(before_state, after_state)


if __name__ == "__main__":
    unittest.main()
