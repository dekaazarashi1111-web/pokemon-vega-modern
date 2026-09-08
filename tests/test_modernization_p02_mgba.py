from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import run_modernization_p02_mgba as gate  # noqa: E402


class ModernizationP02MgbaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / gate.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        cls.evidence_path = ROOT / cls.config["output"]
        cls.evidence = json.loads(cls.evidence_path.read_text(encoding="utf-8"))

    def test_exact_rom_direct_call_has_positive_and_negative_cases(self) -> None:
        result = self.evidence["runtime_result"]
        self.assertEqual(result["get_mega_species_symbol"], "0x09114CF0")
        self.assertEqual(result["get_mega_species_thumb"], "0x09114CF1")
        self.assertEqual(result["species_id"], 645)
        self.assertEqual(result["target_species_id"], 1092)
        self.assertEqual(result["item_id"], 0)
        self.assertEqual(result["cases"]["dragon_ascent"]["moves"], [630, 0, 0, 0])
        self.assertEqual(result["cases"]["dragon_ascent"]["result"], 1092)
        self.assertEqual(result["cases"]["historical_773"]["moves"], [773, 0, 0, 0])
        self.assertEqual(result["cases"]["historical_773"]["result"], 0)
        self.assertIsNone(result["cases"]["null_moves"]["moves"])
        self.assertEqual(result["cases"]["null_moves"]["result"], 0)
        self.assertTrue(result["payload_pc_seen"])
        self.assertEqual(result["warnings_errors"], 0)

    def test_two_independent_processes_are_bound_without_e2e_overclaim(self) -> None:
        execution = self.evidence["execution"]
        self.assertEqual(execution["process_runs"], 2)
        self.assertTrue(execution["independent_processes"])
        self.assertTrue(execution["identical_results"])
        self.assertEqual(
            self.evidence["classification"],
            "DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E",
        )
        self.assertFalse(self.evidence["claims"]["scheduler_e2e"])
        self.assertFalse(self.evidence["claims"]["full_evolution_acceptance"])
        self.assertTrue(
            self.evidence["claims"]["dragon_ascent_630_selects_mega_rayquaza_1092"],
        )
        self.assertTrue(
            self.evidence["claims"]["historical_773_does_not_select_wish_mega"],
        )
        self.assertTrue(
            self.evidence["claims"]["null_moves_does_not_select_wish_mega"],
        )

    def test_stage63_preimage_and_stage64_two_byte_patch_are_bound(self) -> None:
        inputs = self.evidence["inputs"]
        self.assertEqual(inputs["stage63"]["rayquaza_entry"], [254, 773, 1092, 2])
        self.assertEqual(inputs["stage64"]["rayquaza_entry"], [254, 630, 1092, 2])
        self.assertEqual(inputs["changed_rom_offsets"], [0x01F8E1BA, 0x01F8E1BB])
        self.assertEqual(
            inputs["battle_core_fingerprint"],
            "9215826454ee6023888d2f53d33b662d21a340af868c92637aae2c5c191c5717",
        )
        self.assertEqual(
            {row["get_mega_species"] for row in inputs["offsets"]},
            {"0x09114CF0"},
        )

    def test_runner_is_read_only_bounded_and_uses_isolated_stack(self) -> None:
        source = (ROOT / self.config["runtime"]["runner_source"]).read_text(
            encoding="utf-8",
        )
        self.assertIn("BATTLE_CORE_ISOLATE_HOST_CALL_STACK", source)
        self.assertIn("P02_GET_MEGA_SPECIES_SYMBOL = 0x09114CF0U", source)
        self.assertIn("call_bounded(", source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn("mCoreLoadSaveFile", source)
        self.assertIn(r'\"read_only\":true', source)
        self.assertIn(r'\"artifacts_written\":[]', source)

    def test_result_validator_fails_closed_on_old_wrong_id_acceptance(self) -> None:
        tampered = copy.deepcopy(self.evidence["runtime_result"])
        tampered["cases"]["historical_773"]["result"] = 1092
        with self.assertRaisesRegex(
            gate.ModernizationP02MgbaError, "historical_773",
        ):
            gate._validate_runner_result(tampered, self.config)

    def test_check_is_fingerprint_bound_and_read_only(self) -> None:
        before = self.evidence_path.read_bytes()
        before_state = (
            self.evidence_path.stat().st_mtime_ns,
            hashlib.sha256(before).hexdigest(),
        )
        completed = subprocess.run(
            ["python3", "scripts/run_modernization_p02_mgba.py", "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("MODERNIZATION_P02_MGBA_CHECK=PASS", completed.stdout)
        after_state = (
            self.evidence_path.stat().st_mtime_ns,
            hashlib.sha256(self.evidence_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(before_state, after_state)


if __name__ == "__main__":
    unittest.main()
