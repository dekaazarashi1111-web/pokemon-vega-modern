from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_modernization_p03_fullslots_guarded_e2e as runner
from tools import modernization_p03_native_pp_repair as boundary


def observation(mode="replace-0", rom_sha=boundary.CANDIDATE_SHA):
    before, pp, after, after_pp = runner.expected_slots(mode, rom_sha)
    full = mode.startswith("replace-")
    selection = full or mode == "cancel-selection"
    refusal = mode in ("refuse", "cancel-selection")
    return {
        "schema_version": 1, "status": "OBSERVED", "scope": runner.SCOPE, "mode": mode,
        "rom_sha256": rom_sha, "private_save_initial_sha256": runner.PRIVATE_SHA,
        "species": 649, "initial_level": 7 if mode.endswith("below-level") else 8,
        "final_level": 8 if mode.endswith("below-level") else 9, "canonical_move_pp": 20,
        "before_moves": before, "before_pp": pp, "after_moves": after, "after_pp": after_pp,
        "reloaded_moves": after.copy(), "reloaded_pp": after_pp.copy(),
        "host_write_guard": True, "host_write_guard_phase": "LEARNING_SCENE",
        "normal_bag_party_input": True, "normal_save_menu": True, "fresh_core_normal_continue": True,
        "breeding_e2e": False, "full_p03_acceptance": False, "release_ready": False, "warnings_errors": 0,
        "trace": {"frames": 1500, "down_presses": int(mode[-1]) if full else 0,
                  "selection_presses": 1 if selection else 0, "evolution_b_presses": 5,
                  "ask_frame": 100 if full or refusal else 0, "summary_frame": 200 if selection else 0,
                  "stop_frame": 300 if refusal else 0, "replaced_frame": 300 if full else 0,
                  "begin_frame": 400, "update_frame": 500, "field_frame": 1500},
    }


def encoded(value):
    return json.dumps(value).encode()


class ResultContractTests(unittest.TestCase):
    def validate(self, result, mode="replace-0", sha=boundary.CANDIDATE_SHA, rc=0):
        return runner.validate_result(encoded(result), mode, sha, rc)

    def test_all_nine_candidate_cases(self):
        for mode in runner.MODES:
            with self.subTest(mode=mode):
                self.assertEqual(self.validate(observation(mode), mode), observation(mode))

    def test_parent_controls_are_explicit_defects_not_candidate_pass(self):
        for mode in runner.CONTROLS:
            result = observation(mode, boundary.PARENT_SHA)
            self.validate(result, mode, boundary.PARENT_SHA)
            with self.assertRaises(ValueError):
                self.validate(result, mode, boundary.CANDIDATE_SHA)

    def test_legacy_pp45_is_rejected_on_repaired_candidate(self):
        result = observation()
        result["after_pp"][0] = result["reloaded_pp"][0] = 45
        with self.assertRaises(ValueError):
            self.validate(result)

    def test_canonical_pp_cannot_be_redefined_to_hide_defect(self):
        result = observation()
        result["canonical_move_pp"] = 45
        with self.assertRaises(ValueError):
            self.validate(result)

    def test_wrong_replacement_slot_is_rejected(self):
        result = observation()
        result["after_moves"] = [33, 535, 45, 52]
        with self.assertRaises(ValueError):
            self.validate(result)

    def test_all_retained_moves_pp_and_reloaded_slots_are_checked(self):
        for field in ("before_moves", "before_pp", "after_moves", "after_pp", "reloaded_moves", "reloaded_pp"):
            for index in range(4):
                result = observation()
                result[field][index] += 1
                with self.subTest(field=field, index=index), self.assertRaises(ValueError):
                    self.validate(result)

    def test_refusal_must_not_learn(self):
        for mode in ("refuse", "cancel-selection", "below-level", "empty-below-level"):
            result = observation(mode)
            result["after_moves"][0] = 535
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.validate(result, mode)

    def test_missing_extra_and_duplicate_json_fields_rejected(self):
        result = observation()
        result.pop("normal_save_menu")
        with self.assertRaises(ValueError):
            self.validate(result)
        result = observation()
        result["invented_acceptance"] = True
        with self.assertRaises(ValueError):
            self.validate(result)
        raw = encoded(observation()).replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1')
        with self.assertRaises(ValueError):
            runner.validate_result(raw, "replace-0", boundary.CANDIDATE_SHA, 0)

    def test_bool_int_confusion_rejected_at_every_depth(self):
        for field in ("schema_version", "warnings_errors", "canonical_move_pp"):
            result = observation()
            result[field] = bool(result[field])
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(result)
        result = observation()
        result["trace"]["down_presses"] = False
        with self.assertRaises(ValueError):
            self.validate(result)
        result = observation("empty-learn")
        result["before_pp"][3] = False
        with self.assertRaises(ValueError):
            self.validate(result, "empty-learn")
        with self.assertRaises(ValueError):
            self.validate(observation(), rc=False)

    def test_completion_and_guard_claims_cannot_be_changed(self):
        for field in ("host_write_guard", "normal_save_menu", "fresh_core_normal_continue",
                      "full_p03_acceptance", "release_ready", "breeding_e2e"):
            result = observation()
            result[field] = not result[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(result)

    def test_native_route_evidence_required(self):
        for field in ("ask_frame", "summary_frame", "replaced_frame", "begin_frame", "update_frame", "field_frame"):
            result = observation()
            result["trace"][field] = 0
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(result)

    def test_event_order_and_exact_physical_down_presses(self):
        for mode in runner.MODES:
            result = observation(mode)
            result["trace"]["down_presses"] += 1
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.validate(result, mode)
        result = observation()
        result["trace"]["ask_frame"] = 999
        with self.assertRaises(ValueError):
            self.validate(result)

    def test_nonzero_return_code_unknown_mode_and_rom_rejected(self):
        for rc in (-11, 1, 2, 139):
            with self.subTest(rc=rc), self.assertRaises(ValueError):
                self.validate(observation(), rc=rc)
        for mode, sha in (("other", boundary.CANDIDATE_SHA), ("replace-0", "0" * 64), ("refuse", boundary.PARENT_SHA)):
            with self.subTest(mode=mode, sha=sha), self.assertRaises(ValueError):
                self.validate(observation(), mode=mode, sha=sha)

    def test_guard_exit_and_exact_diagnostic_required(self):
        good = subprocess.CompletedProcess([], 1, b"", b"P03 fullslots: host write after learning barrier\n")
        runner.validate_guard(good)
        for rc, out, err in ((0, good.stdout, good.stderr), (2, good.stdout, good.stderr),
                             (-11, good.stdout, good.stderr), (True, good.stdout, good.stderr),
                             (1, b"PASS", good.stderr), (1, b"", b"different failure")):
            with self.subTest(rc=rc, out=out, err=err), self.assertRaises(ValueError):
                runner.validate_guard(subprocess.CompletedProcess([], rc, out, err))

    def test_entrypoints_are_unique_and_originals_unmodified(self):
        entry = "int main(int argc, char **argv)"
        self.assertEqual(runner.embed_learning(entry), "int p03f_previous_learning_main(int argc, char **argv)")
        for source in ("", entry + entry):
            with self.assertRaises(ValueError):
                runner.embed_learning(source)

    def test_output_escape_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            runner.run(runner.ROOT / "outside-local")
        with self.assertRaises(ValueError):
            runner.run(runner.ROOT / ".local/../outside-local")
        with self.assertRaises(ValueError):
            runner.run(runner.ROOT / ".local")
        with tempfile.TemporaryDirectory(dir=runner.ROOT / ".local") as temp:
            link = Path(temp) / "link"
            link.symlink_to(Path(temp), target_is_directory=True)
            with self.assertRaises(ValueError):
                runner.run(link / "output")

    def test_failed_run_removes_stale_pass(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / ".local") as temp:
            output = Path(temp)
            (output / "result.json").write_text('{"status":"PASS"}')
            with patch.object(runner, "source_bindings", side_effect=ValueError("source mismatch")):
                with self.assertRaises(ValueError):
                    runner.run(output)
            self.assertFalse((output / "result.json").exists())


class BoundaryAndFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = (runner.ROOT / boundary.PARENT_PATH).read_bytes()
        cls.seed = runner.ROOT / runner.SEED_PATH

    def test_existing_recipe_is_exactly_five_classified_literals(self):
        fixed, report = boundary.build(self.parent)
        changed = {i for i, (a, b) in enumerate(zip(self.parent, fixed)) if a != b}
        expected = {offset + i for offset, *_ in boundary.SITES for i in range(4)}
        self.assertEqual(changed, expected)
        self.assertEqual(hashlib.sha256(fixed).hexdigest(), boundary.CANDIDATE_SHA)
        self.assertFalse(report["current_stage79_candidate_changed"])
        self.assertFalse(report["active_baseline_changed"])
        self.assertFalse(report["release_ready"])
        self.assertEqual(len(report["patches"]), 5)
        self.assertEqual(report["modified_bytes"], 20)

    def test_wrong_parent_and_already_repaired_parent_rejected(self):
        fixed, _ = boundary.build(self.parent)
        for data in (b"", self.parent[:-1], b"\xff" + self.parent[1:], fixed):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                boundary.build(data)

    def test_instruction_guards_and_canonical_table_not_modified(self):
        fixed, _ = boundary.build(self.parent)
        for _, offset, code_hex, role in boundary.SITES:
            code = bytes.fromhex(code_hex)
            with self.subTest(role=role):
                self.assertEqual(fixed[offset:offset + len(code)], code)
        start = boundary.CANONICAL_MOVES - 0x08000000
        self.assertEqual(fixed[start:start + 12 * 1024], self.parent[start:start + 12 * 1024])

    def test_private_rtc_fixture_preserves_every_game_save_byte(self):
        before = self.seed.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "private.srm"
            report = runner.prepare_private_save(self.seed, dest)
            self.assertEqual(dest.read_bytes()[:131072], before)
            self.assertEqual(dest.read_bytes()[131072:], bytes(7) + b"\x40" + bytes(8))
            self.assertEqual(runner.identity(dest), {"size": 131088, "sha256": runner.PRIVATE_SHA})
            self.assertEqual(report["game_save_bytes_changed_before_boot"], 0)
            self.assertEqual(self.seed.read_bytes(), before)

    def test_seed_overwrite_double_initialization_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            runner.prepare_private_save(self.seed, self.seed)
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "private.srm"
            runner.prepare_private_save(self.seed, dest)
            before = dest.read_bytes()
            with self.assertRaises(ValueError):
                runner.prepare_private_save(self.seed, dest)
            self.assertEqual(dest.read_bytes(), before)
            link = Path(temp) / "link.srm"
            link.symlink_to(self.seed)
            with self.assertRaises(ValueError):
                runner.prepare_private_save(self.seed, link)
            with self.assertRaises(ValueError):
                runner.prepare_private_save(link, Path(temp) / "other.srm")

    def test_candidate_cannot_overwrite_parent_or_existing_file(self):
        parent = runner.ROOT / boundary.PARENT_PATH
        with self.assertRaises(ValueError):
            runner.write_candidate(parent, parent)
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "candidate.gba"
            dest.write_bytes(b"sentinel")
            with self.assertRaises(ValueError):
                runner.write_candidate(parent, dest)
            self.assertEqual(dest.read_bytes(), b"sentinel")

    def test_observation_has_no_getter_call_or_host_write(self):
        source = (runner.ROOT / runner.SOURCE).read_text()
        observation_source = source.split("static struct P03FTrace p03f_scene(", 1)[1].split("static void p03f_read_slots", 1)[0]
        for forbidden in ("call_preserving(", "call_bounded(", "p02s_data(", "write8(", "write16(",
                          "write32(", "set_mon_data", "loadState(", "restore_snapshot("):
            self.assertNotIn(forbidden, observation_source)
        for api in ("busWrite8", "busWrite16", "busWrite32", "rawWrite8", "rawWrite16", "rawWrite32", "writeRegister"):
            self.assertIn("c->" + api + "=p03f_deny", source)


if __name__ == "__main__":
    unittest.main()
