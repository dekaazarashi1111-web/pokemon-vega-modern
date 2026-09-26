"""Observer/contract/process unit tests; none is product-ROM acceptance evidence."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p05_scheduler_runner", ROOT / "scripts/run_modernization_p05_controller_witness.py")
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


def synthetic_result(case: str = "dragonize_ghost") -> dict:
    ability, target_type, hit = runner.CASES[case]
    initial = {"frame": 0, "battle_flags": 4, "pp": [35, 40], "hp": [1000, 1000],
               "abilities": [ability, 0], "types": [[11, 11], [target_type, target_type]]}
    final = copy.deepcopy(initial)
    final.update(frame=9, pp=[34, 39], hp=[1000, 980 if hit else 1000])
    return {
        "schema_version": 1, "status": "PASS", "scope": runner.SCOPE, "case": case,
        "rom_sha256": runner.ROM_ID["sha256"], "normal_controller_input": True,
        "passive_after_fixture": True, "fixture_battle_ram_overrides": True,
        "native_battle_setup": True, "representative_scheduler_e2e": True,
        "full_p05_acceptance": False, "species_ability_assignment_e2e": False,
        "save_reload_e2e": False, "release_ready": False, "warnings_errors": 0,
        "initial": initial, "final": final,
        "events": {"action": 1, "move": 2, "player_pp_spent": 4,
                   "enemy_pp_spent": 6, "returned": 8,
                   "hit": 5 if hit else 0, "immune": 0 if hit else 5}, "frames": 9,
    }


class ResultContractTests(unittest.TestCase):
    def reject(self, value: dict, case: str = "dragonize_ghost") -> None:
        with self.assertRaises((ValueError, TypeError)):
            runner.validate_result(json.dumps(value).encode(), case, 0)

    def test_four_synthetic_contract_examples(self):
        for case in runner.CASES:
            with self.subTest(case=case):
                sample = synthetic_result(case)
                self.assertEqual(runner.validate_result(json.dumps(sample).encode(), case, 0), sample)

    def test_nonzero_exit_overrides_pass_json(self):
        for code in (1, -signal.SIGTERM, True):
            with self.subTest(code=code), self.assertRaises(ValueError):
                runner.validate_result(json.dumps(synthetic_result()).encode(), "dragonize_ghost", code)

    def test_exact_bool_types(self):
        for field in ("normal_controller_input", "passive_after_fixture", "release_ready"):
            value = synthetic_result(); value[field] = int(value[field]); self.reject(value)

    def test_numeric_bool_rejected(self):
        value = synthetic_result(); value["events"]["action"] = True; self.reject(value)

    def test_no_full_acceptance_promotion(self):
        for field in ("full_p05_acceptance", "species_ability_assignment_e2e", "save_reload_e2e", "release_ready"):
            value = synthetic_result(); value[field] = True; self.reject(value)

    def test_requires_explicit_fixture_scope(self):
        value = synthetic_result(); value["fixture_battle_ram_overrides"] = False; self.reject(value)

    def test_missing_and_extra_keys(self):
        value = synthetic_result(); del value["events"]; self.reject(value)
        value = synthetic_result(); value["scheduler_e2e"] = True; self.reject(value)

    def test_one_turn_not_two_or_zero(self):
        for pp in ([35, 40], [34, 40], [33, 39], [34, 38]):
            value = synthetic_result(); value["final"]["pp"] = pp; self.reject(value)

    def test_selection_must_precede_execution(self):
        for field in ("action", "move", "player_pp_spent", "enemy_pp_spent", "returned"):
            value = synthetic_result(); value["events"][field] = 0; self.reject(value)
        value = synthetic_result(); value["events"]["move"] = 6; self.reject(value)

    def test_stable_return_required(self):
        value = synthetic_result(); value["events"]["returned"] = 9; self.reject(value)

    def test_damage_attribution_required(self):
        value = synthetic_result(); value["events"]["hit"] = 1; self.reject(value)
        value = synthetic_result(); value["events"]["hit"] = 0; self.reject(value)

    def test_ghost_control_requires_immunity_not_just_unchanged_hp(self):
        value = synthetic_result("no_ability_ghost"); value["events"]["immune"] = 0
        self.reject(value, "no_ability_ghost")

    def test_wrong_hp_outcome(self):
        value = synthetic_result(); value["final"]["hp"][1] = 1000; self.reject(value)
        value = synthetic_result(); value["final"]["hp"][0] = 999; self.reject(value)
        value = synthetic_result(); value["final"]["hp"][1] = 0; self.reject(value)

    def test_wrong_rom_case_ability_type(self):
        for field, replacement in (("case", "no_ability_ghost"), ("rom_sha256", "0" * 64)):
            value = synthetic_result(); value[field] = replacement; self.reject(value)
        value = synthetic_result(); value["final"]["abilities"][0] = 0; self.reject(value)
        value = synthetic_result(); value["final"]["types"][1][0] = 0; self.reject(value)

    def test_malformed_json_and_duplicate_keys(self):
        for data in (b"{}{}", b"PASS", b"[]", b'\xff', b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.subTest(data=data), self.assertRaises((ValueError, UnicodeError)):
                runner.validate_result(data, "dragonize_ghost", 0)

    def test_regular_wild_bookkeeping_only(self):
        for flags in (0, 4):
            value = synthetic_result()
            value["initial"]["battle_flags"] = value["final"]["battle_flags"] = flags
            self.assertEqual(runner.validate_result(json.dumps(value).encode(), "dragonize_ghost", 0), value)
        for flags in (True, 1, 2, 8, 0x80, 0x100, 0x40000000, 0xFFFFFFFF):
            value = synthetic_result()
            value["initial"]["battle_flags"] = value["final"]["battle_flags"] = flags
            self.reject(value)
        value = synthetic_result(); value["final"]["battle_flags"] = 0; self.reject(value)

    def test_warning_rejected(self):
        value = synthetic_result(); value["warnings_errors"] = 1; self.reject(value)


class ProcessAndFilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = runner.prepare_output(self.root / ".local/p05", self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_partial_invalid_utf8_logs_survive_timeout(self):
        command = [sys.executable, "-S", "-c", "import os,time;os.write(1,b'partial\\xff');os.write(2,b'err\\xfe');time.sleep(10)"]
        with self.assertRaises(subprocess.TimeoutExpired):
            runner.run_logged(command, self.root, self.output, "dragonize_ghost", 1.0)
        self.assertEqual((self.output / "dragonize_ghost.stdout").read_bytes(), b"partial\xff")
        self.assertEqual((self.output / "dragonize_ghost.stderr").read_bytes(), b"err\xfe")
        self.assertTrue(json.loads((self.output / "dragonize_ghost.process.json").read_text())["timed_out"])

    def test_real_sigterm_after_pass_is_failure(self):
        raw = json.dumps(synthetic_result())
        command = [sys.executable, "-c", f"import os,signal;os.write(1,{raw.encode()!r});os.kill(os.getpid(),signal.SIGTERM)"]
        code = runner.run_logged(command, self.root, self.output, "dragonize_ghost", 10)
        self.assertEqual(code, -signal.SIGTERM)
        with self.assertRaises(ValueError):
            runner.validate_result((self.output / "dragonize_ghost.stdout").read_bytes(), "dragonize_ghost", code)

    def test_launch_failure_recorded(self):
        with self.assertRaises(FileNotFoundError):
            runner.run_logged([str(self.root / "absent")], self.root, self.output, "compile", 5)
        record = json.loads((self.output / "compile.process.json").read_text())
        self.assertIsNone(record["returncode"])
        self.assertIn("launch_error", record)

    def test_compile_failure_logs_preserved(self):
        code = runner.run_logged([sys.executable, "-c", "import sys;sys.stderr.write('compile error');sys.exit(2)"], self.root, self.output, "compile", 5)
        self.assertEqual(code, 2)
        self.assertEqual((self.output / "compile.stderr").read_text(), "compile error")

    def test_old_pass_and_owned_logs_invalidated(self):
        (self.output / "result.json").write_text('{"status":"PASS"}')
        (self.output / "compile.stderr").write_text("old")
        (self.output / "tested-head.txt").write_text("retain")
        runner.prepare_output(self.output, self.root)
        self.assertFalse((self.output / "result.json").exists())
        self.assertFalse((self.output / "compile.stderr").exists())
        self.assertEqual((self.output / "tested-head.txt").read_text(), "retain")

    def test_symlink_ancestor_rejected(self):
        outside = self.root / "outside"; outside.mkdir()
        (self.root / ".local/alias").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.prepare_output(self.root / ".local/alias/test", self.root)
        self.assertFalse((outside / "test").exists())

    def test_parent_escape_and_local_root_rejected(self):
        for path in (self.root / "not-local", self.root / ".local", self.root / ".local/../outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.prepare_output(path, self.root)

    def test_changed_or_missing_input_is_failure(self):
        input_file = self.root / "rom.gba"; input_file.write_bytes(b"original")
        binding = {input_file: runner.identity(input_file)}
        runner.verify_unchanged(binding)
        input_file.write_bytes(b"changed")
        with self.assertRaises(ValueError): runner.verify_unchanged(binding)
        input_file.unlink()
        with self.assertRaises(ValueError): runner.verify_unchanged(binding)

    def test_input_symlink_rejected(self):
        real = self.root / "real"; real.write_bytes(b"source")
        alias = self.root / "alias"; alias.symlink_to(real)
        with self.assertRaises(ValueError): runner.identity(alias)


class SourceBoundaryTests(unittest.TestCase):
    def test_live_turn_contains_no_host_rom_calls_or_ram_writes(self):
        source = (ROOT / runner.SOURCE).read_text()
        body = source.split("static struct P05TurnObserver p05_observe_turn(", 1)[1].split("static void p05_print_sample", 1)[0]
        for forbidden in ("write8(", "write16(", "write32", "rawWrite", "call_bounded(", "call_preserving(", "restore_snapshot(", "p05_fixture(", "set_mon_data"):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, body)
        self.assertIn("core->setKeys(core, keys)", body)
        self.assertIn("core->runFrame(core)", body)
        self.assertIn("frame - last_press >= 30U", body)

    def test_pass_printed_after_teardown_and_rom_check(self):
        source = (ROOT / runner.SOURCE).read_text()
        tail = source.split("int main(int argc, char **argv)", 1)[1]
        self.assertLess(tail.index("core->deinit(core)"), tail.index('\\"status\\":\\"PASS\\"'))
        self.assertLess(tail.index("sha256_file(argv[1], after)"), tail.index('\\"status\\":\\"PASS\\"'))
        self.assertNotIn("free(core)", tail)

    def test_workflow_uses_discovery_and_always_collects_logs(self):
        source = (ROOT / ".github/workflows/p05-controller-witness.yml").read_text()
        self.assertIn("unittest discover -s tests", source)
        self.assertIn("if: always()", source)
        self.assertNotIn("continue-on-error", source)
        self.assertIn("contents: read", source)


OBSERVER_CASES = (
    "valid_hit", "valid_immune", "brief_return", "invalid_initial", "warning",
    "battle_exit", "battler_count", "absent", "wrong_species", "wrong_move",
    "wrong_ability", "wrong_type", "pp_refill", "two_player_turns", "two_enemy_turns",
    "faint", "healing", "player_damaged", "no_action_selection", "no_move_selection",
    "no_chosen_move", "wrong_chosen_action", "damage_before_move", "unattributed_damage",
    "missing_damage", "unexpected_immunity", "missing_immunity", "unexpected_damage",
    "enemy_never_moved", "no_return", "timeout", "nonmonotonic", "contradictory_controller",
    "valid_master", "initial_trainer", "live_link", "live_double", "live_route_change",
)


class NativeObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.executable = Path(cls.temporary.name) / "observer"
        command = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic", "-Itools",
                   "tests/modernization_p05_turn_observer_fixture.c", "-o", str(cls.executable)]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        if completed.returncode:
            cls.temporary.cleanup()
            raise AssertionError(completed.stdout + completed.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()


def native_test(case):
    def test(self):
        completed = subprocess.run([str(self.executable), case], capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("observer-fixture " + case + ": OK", completed.stdout)
    return test


for _case in OBSERVER_CASES:
    setattr(NativeObserverTests, "test_" + _case, native_test(_case))

if __name__ == "__main__":
    unittest.main()
