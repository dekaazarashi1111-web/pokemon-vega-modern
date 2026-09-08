"""baseline証跡の流用はexact source/ROM/run契約が成立する時だけ。"""
import unittest
from scripts.reuse_p01_baseline import PIN_RUN, PIN_HEAD, eligible, valid_run


class EvidenceReuseTests(unittest.TestCase):
    def test_same_source_and_explicit_non_baseline_changes_allowed(self):
        self.assertTrue(eligible([]))
        self.assertTrue(eligible(["design/run_log.md", "scripts/build_p01_rom.py"]))

    def test_runtime_implementation_change_forces_real_retest(self):
        for path in ("scripts/build_stage62_npc_placement_integrity_repair.py", "tools/stage61_interaction_oracle.py", "overlays/save_migration/save_migration.c", "manifests/species_ids.csv"):
            self.assertFalse(eligible([path]))

    def test_baseline_and_input_identity_changes_force_retest(self):
        for path in ("config/active_play_baseline.json", "config/github_private_environment.json", "infra/toolchain_manifest.json", "scripts/run_p01_baseline_gate.py", "scripts/restore_p01_environment.py"):
            self.assertFalse(eligible([path]))

    def test_exact_successful_run_required(self):
        run = {"id": PIN_RUN, "head_sha": PIN_HEAD, "status": "completed", "conclusion": "success", "name": "p01-runtime-validation", "event": "pull_request"}
        self.assertTrue(valid_run(run))
        for key, value in (("id", PIN_RUN + 1), ("head_sha", "0" * 40), ("status", "in_progress"), ("conclusion", "skipped"), ("conclusion", "failure"), ("name", "other"), ("event", "push")):
            self.assertFalse(valid_run(dict(run, **{key: value})))

    def test_unknown_paths_and_traversal_never_authorize_reuse(self):
        for path in ("scripts/new_runtime.py", "../scripts/build_p01_rom.py", "config/modernization_new_unreviewed.json"):
            self.assertFalse(eligible([path]))


if __name__ == "__main__":
    unittest.main()
