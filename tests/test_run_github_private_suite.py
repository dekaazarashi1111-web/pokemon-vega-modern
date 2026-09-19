from __future__ import annotations

import unittest
from pathlib import Path

from scripts.run_github_private_suite import command_plan

ROOT = Path(__file__).resolve().parents[1]


class GitHubPrivateSuiteTests(unittest.TestCase):
    def test_each_declared_suite_has_a_plan(self) -> None:
        for suite in (
            "battle-cli-offline", "stage62-check", "stage62-mgba",
            "modernization-p01",
            "modernization-p02",
            "modernization-contracts",
            "modernization-p04-assets",
            "modernization-p04-capacity",
            "modernization-p03-stage65",
            "modernization-p03-stage66",
            "full-unit", "all",
        ):
            with self.subTest(suite=suite):
                self.assertTrue(command_plan(suite, python="python3"))

    def test_modernization_p01_is_focused_and_rebuilds_before_check(self) -> None:
        plan = command_plan("modernization-p01", python="python3")
        self.assertIn(["make", "modernization-p01-focused-test"], plan)
        build = ["python3", "scripts/build_modernization_p01.py", "build"]
        check = ["python3", "scripts/build_modernization_p01.py", "check"]
        self.assertLess(plan.index(build), plan.index(check))
        self.assertNotIn(["make", "test"], plan)

    def test_modernization_p02_rebuilds_before_exact_rom_gate(self) -> None:
        plan = command_plan("modernization-p02", python="python3")
        parent = ["python3", "scripts/build_modernization_p01.py", "build"]
        build = ["python3", "scripts/build_modernization_p02_stage64.py", "build"]
        run = ["python3", "scripts/run_modernization_p02_mgba.py", "run"]
        runtime_check = ["python3", "scripts/run_modernization_p02_mgba.py", "check"]
        check = ["python3", "scripts/build_modernization_p02_stage64.py", "check"]
        drift = [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p02_stage64_checkpoint.json",
            "content/modernization/p02_stage64_mgba_runtime_gate.json",
        ]
        self.assertLess(plan.index(parent), plan.index(run))
        self.assertLess(plan.index(run), plan.index(runtime_check))
        self.assertLess(plan.index(runtime_check), plan.index(build))
        self.assertLess(plan.index(build), plan.index(check))
        self.assertLess(plan.index(check), plan.index(drift))
        self.assertIn(["make", "modernization-p02-focused-test"], plan)
        self.assertNotIn(["make", "test"], plan)

    def test_modernization_contracts_are_focused_and_read_only(self) -> None:
        plan = command_plan("modernization-contracts", python="python3")
        self.assertEqual(
            [
                ["python3", "scripts/build_modernization_p03.py", "--check"],
                ["python3", "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
                ["python3", "scripts/build_modernization_p05.py", "--check"],
                ["python3", "scripts/build_modernization_p06.py", "--compact"],
                ["python3", "scripts/build_modernization_p07.py", "--check"],
                ["make", "modernization-contracts-focused-test"],
            ],
            plan,
        )
        self.assertNotIn(["make", "test"], plan)

    def test_full_unit_bootstraps_ignored_modernization_artifacts(self) -> None:
        plan = command_plan("full-unit", python="python3")
        required_order = [
            ["python3", "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"],
            ["python3", "scripts/build_modernization_p04_assets.py", "--write", "--compact"],
            ["git", "diff", "--exit-code", "--", "content/modernization/p04_asset_import_manifest.json"],
            ["python3", "scripts/build_modernization_p01.py", "build"],
            ["python3", "scripts/build_modernization_p02_stage64.py", "build"],
            [
                "git", "diff", "--exit-code", "--",
                "content/modernization/p02_stage64_checkpoint.json",
            ],
            ["python3", "scripts/build_modernization_p03_stage65.py", "build"],
            [
                "git", "diff", "--exit-code", "--",
                "content/modernization/p03_stage65_checkpoint.json",
            ],
            ["python3", "scripts/build_modernization_p03_stage66.py", "build"],
            [
                "git", "diff", "--exit-code", "--",
                "content/modernization/p03_stage66_bulk_route_audit.json",
                "content/modernization/p03_stage66_change_audit.json",
                "content/modernization/p03_stage66_checkpoint.json",
            ],
            ["make", "test"],
        ]
        self.assertEqual(required_order, plan)

    def test_modernization_p04_assets_are_rebuilt_from_pinned_source(self) -> None:
        plan = command_plan("modernization-p04-assets", python="python3")
        fetch = ["python3", "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"]
        write = ["python3", "scripts/build_modernization_p04_assets.py", "--write", "--compact"]
        diff = ["git", "diff", "--exit-code", "--", "content/modernization/p04_asset_import_manifest.json"]
        check = ["python3", "scripts/build_modernization_p04_assets.py", "--check", "--compact"]
        self.assertLess(plan.index(fetch), plan.index(write))
        self.assertLess(plan.index(write), plan.index(diff))
        self.assertLess(plan.index(diff), plan.index(check))
        self.assertIn(["make", "modernization-p04-assets-focused-test"], plan)
        self.assertNotIn(["make", "test"], plan)

    def test_modernization_p04_capacity_rebuilds_required_private_inputs(self) -> None:
        plan = command_plan("modernization-p04-capacity", python="python3")
        fetch = ["python3", "scripts/build_modernization_p04_sources.py", "--fetch", "--compact"]
        assets = ["python3", "scripts/build_modernization_p04_assets.py", "--write", "--compact"]
        p01 = ["python3", "scripts/build_modernization_p01.py", "build"]
        p02 = ["python3", "scripts/build_modernization_p02_stage64.py", "build"]
        p03 = ["python3", "scripts/build_modernization_p03_stage65.py", "build"]
        p05 = ["python3", "scripts/build_modernization_p05.py", "--check"]
        capacity = [
            "python3", "scripts/build_modernization_p04_capacity.py", "--check", "--compact",
        ]
        self.assertLess(plan.index(fetch), plan.index(assets))
        self.assertLess(plan.index(assets), plan.index(p01))
        self.assertLess(plan.index(p01), plan.index(p02))
        self.assertLess(plan.index(p02), plan.index(p03))
        self.assertLess(plan.index(p03), plan.index(p05))
        self.assertLess(plan.index(p05), plan.index(capacity))
        self.assertIn(["make", "modernization-p04-capacity-focused-test"], plan)
        self.assertNotIn(["make", "test"], plan)

    def test_modernization_p03_stage65_rebuilds_the_full_parent_chain(self) -> None:
        plan = command_plan("modernization-p03-stage65", python="python3")
        p01 = ["python3", "scripts/build_modernization_p01.py", "build"]
        p02 = ["python3", "scripts/build_modernization_p02_stage64.py", "build"]
        p03 = ["python3", "scripts/build_modernization_p03_stage65.py", "build"]
        run = ["python3", "scripts/run_modernization_p03_stage65_mgba.py", "run"]
        check = ["python3", "scripts/build_modernization_p03_stage65.py", "check"]
        drift = [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage65_checkpoint.json",
            "content/modernization/p03_stage65_mgba_runtime_gate.json",
        ]
        self.assertLess(plan.index(p01), plan.index(p02))
        self.assertLess(plan.index(p02), plan.index(run))
        self.assertLess(plan.index(run), plan.index(p03))
        self.assertLess(plan.index(p03), plan.index(check))
        self.assertLess(plan.index(check), plan.index(drift))
        self.assertIn(["make", "modernization-p03-stage65-focused-test"], plan)
        self.assertNotIn(
            ["python3", "scripts/build_modernization_p08.py", "--check"], plan,
        )
        self.assertNotIn(["make", "modernization-p08-focused-test"], plan)
        self.assertNotIn(["make", "test"], plan)

    def test_modernization_p03_stage66_rebuilds_and_verifies_bulk_checkpoint(self) -> None:
        plan = command_plan("modernization-p03-stage66", python="python3")
        p01 = ["python3", "scripts/build_modernization_p01.py", "build"]
        p02 = ["python3", "scripts/build_modernization_p02_stage64.py", "build"]
        p03_stage65 = ["python3", "scripts/build_modernization_p03_stage65.py", "build"]
        run = ["python3", "scripts/run_modernization_p03_stage66_mgba.py", "run"]
        build = ["python3", "scripts/build_modernization_p03_stage66.py", "build"]
        runtime_check = ["python3", "scripts/run_modernization_p03_stage66_mgba.py", "check"]
        check = ["python3", "scripts/build_modernization_p03_stage66.py", "check"]
        drift = [
            "git", "diff", "--exit-code", "--",
            "content/modernization/p03_stage66_bulk_route_audit.json",
            "content/modernization/p03_stage66_change_audit.json",
            "content/modernization/p03_stage66_checkpoint.json",
            "content/modernization/p03_stage66_mgba_runtime_gate.json",
        ]
        self.assertLess(plan.index(p01), plan.index(p02))
        self.assertLess(plan.index(p02), plan.index(p03_stage65))
        self.assertLess(plan.index(p03_stage65), plan.index(run))
        self.assertLess(plan.index(run), plan.index(build))
        self.assertLess(plan.index(build), plan.index(runtime_check))
        self.assertLess(plan.index(runtime_check), plan.index(check))
        self.assertLess(plan.index(check), plan.index(drift))
        self.assertIn(["make", "modernization-p03-stage66-focused-test"], plan)
        self.assertIn(["python3", "scripts/build_modernization_p08.py", "--check"], plan)
        self.assertNotIn(["make", "test"], plan)

    def test_all_does_not_repeat_focused_battle_unit(self) -> None:
        plan = command_plan("all", python="python3")
        flattened = [" ".join(command) for command in plan]
        self.assertIn("make test", flattened)
        self.assertFalse(any("test_codex_battle_runtime" in row for row in flattened))
        self.assertTrue(any("stage62_npc_placement" in row for row in flattened))
        self.assertTrue(any("run_modernization_p01_mgba.py" in row for row in flattened))
        self.assertTrue(any("run_modernization_p02_mgba.py run" in row for row in flattened))
        self.assertTrue(
            any("run_modernization_p03_stage65_mgba.py run" in row for row in flattened)
        )
        self.assertTrue(
            any("run_modernization_p03_stage66_mgba.py run" in row for row in flattened)
        )
        self.assertEqual(
            1,
            flattened.count("python3 scripts/build_modernization_p03_stage66.py build"),
        )
        self.assertTrue(any("build_modernization_p08.py --check" in row for row in flattened))
        self.assertTrue(any("catalog species search" in row for row in flattened))

    def test_private_release_downloads_require_private_repository_gate(self) -> None:
        for relative, expected_count in (
            (".github/workflows/private-runtime.yml", 1),
            (".github/workflows/chatgpt-comment-control.yml", 2),
        ):
            with self.subTest(workflow=relative):
                workflow = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(expected_count, workflow.count("gh release download"))
                self.assertEqual(
                    expected_count,
                    workflow.count(
                        'private=$(gh api "repos/${GITHUB_REPOSITORY}" --jq \'.private\')'
                    ),
                )
                self.assertEqual(
                    expected_count,
                    workflow.count('test "$private" = true'),
                )
                segments_before_download = workflow.split("gh release download")[:-1]
                self.assertEqual(expected_count, len(segments_before_download))
                for segment in segments_before_download:
                    self.assertIn(
                        'private=$(gh api "repos/${GITHUB_REPOSITORY}" --jq \'.private\')',
                        segment,
                    )
                    self.assertLess(
                        segment.rfind(
                            'private=$(gh api "repos/${GITHUB_REPOSITORY}" --jq \'.private\')'
                        ),
                        segment.rfind('test "$private" = true'),
                    )

    def test_comment_full_suites_use_the_bootstrapping_private_runner(self) -> None:
        workflow = (
            ROOT / ".github/workflows/chatgpt-comment-control.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "full-unit)\n              python3 scripts/run_github_private_suite.py full-unit",
            workflow,
        )
        self.assertIn(
            "all)\n              python3 scripts/run_github_private_suite.py all",
            workflow,
        )
        self.assertNotIn("full-unit)\n              make test", workflow)

    def test_unknown_suite_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            command_plan("shell", python="python3")


if __name__ == "__main__":
    unittest.main()
