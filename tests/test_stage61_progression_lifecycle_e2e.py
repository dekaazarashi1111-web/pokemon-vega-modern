from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_stage61_progression_lifecycle_e2e.py"
SOURCE_PATH = ROOT / "tools/mgba_stage61_progression_lifecycle_e2e.c"
SPEC = importlib.util.spec_from_file_location(
    "stage61_progression_lifecycle", RUNNER_PATH
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
FIXTURE_PPM_FNV1A64 = f"{RUNNER._fnv1a64(bytes(
    index & 0xFF for index in range(RUNNER.PPM_PIXEL_SIZE)
)):016X}"


class Stage61ProgressionLifecycleE2eTests(unittest.TestCase):
    @staticmethod
    def _league() -> dict[str, object]:
        return {
            "schema_version": RUNNER.RESULT_SCHEMA_VERSION,
            "status": "PASS",
            "case": "league_progression_lifecycle_complete",
            "room_order": [
                "097/075", "097/076", "097/077", "097/078",
                "097/079", "097/080",
            ],
            "scene_var": "0x516C",
            "scene_sequence_exact": [1, 2, 3, 4, 5, 5],
            "completion_sequence_exact": [
                "0x1408", "0x1409", "0x140A", "0x140B", "0x140C",
            ],
            "trainer_battle_wins": 6,
            "trainer_battle_losses": 1,
            "blackout_exercised": True,
            "last_heal_match": True,
            "blackout_field_recovered": True,
            "blackout_scene_high_water_preserved": True,
            "completion_absent_after_loss": True,
            "actual_reentry_after_blackout": True,
            "retry_win_committed": True,
            "physical_room_warp_transitions": 6,
            "actual_walk_steps": 123,
            "face_a_battle_cases": 7,
            "owner_pc_cases": 7,
            "owner_pc_hits": 70,
            "battle_resume_instruction_trace_cases": 6,
            "elite_completion_adapter_cases": 5,
            "champion_no_geometry_negative_control": True,
            "field_recovery_cases": 6,
            "hall_of_fame_tag3_field_terminal": True,
            "checkpoint_positions": {
                "league_full_chain": {
                    "save_before": {"x": 5, "y": 11, "warp_id": 0},
                    "cold_continue": {"x": 5, "y": 11, "warp_id": 0},
                },
                "league_blackout_retry": {
                    "save_before": {"x": 6, "y": 11, "warp_id": 0},
                    "cold_continue": {"x": 6, "y": 11, "warp_id": 0},
                },
            },
            "checkpoint_framebuffer_fnv1a64": {
                "league_full_chain": FIXTURE_PPM_FNV1A64,
                "league_blackout_retry": FIXTURE_PPM_FNV1A64,
            },
            "start_save_cases": 2,
            "fresh_continue_cases": 2,
            "bootstrap_stock_warp_calls": 3,
            "direct_owner_or_script_calls": 0,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    @staticmethod
    def _seafoam() -> dict[str, object]:
        return {
            "schema_version": RUNNER.RESULT_SCHEMA_VERSION,
            "status": "PASS",
            "case": "seafoam_progression_lifecycle_complete",
            "static_maps_83_through_87": 5,
            "runtime_maps_b3_b4": 2,
            "flag_state_variants": 2,
            "runtime_maps_1f_through_b4": 5,
            "route20_reset_owner_cases": 2,
            "route20_reset_owner_pc_hits": 10,
            "upper_b3_physical_chain_cases": 2,
            "distinct_b3_b4_physical_chain_cases": 2,
            "active_current_control_chain_cases": 1,
            "actual_strength_prompt_cases": 9,
            "strength_zero_to_one_transition_cases": 9,
            "native_strength_clear_after_fall_cases": 9,
            "actual_boulder_push_cases": 9,
            "actual_boulder_push_steps": 23,
            "actual_hole_fall_cases": 9,
            "topology_hide_arrival_transition_cases": 9,
            "fall_owner_pc_cases": 9,
            "fall_owner_pc_hits": 9,
            "push_owner_pc_cases": 9,
            "push_owner_pc_hits": 9,
            "strength_owner_pc_cases": 9,
            "strength_owner_pc_hits": 20,
            "surf_observed_cases": 4,
            "active_current_motion_cases": 3,
            "active_current_motion_observed": True,
            "b3_current_stop_observed": True,
            "b4_current_stop_observed": True,
            "stopped_current_flag_observed": True,
            "non_producer_obstacle_controls": 2,
            "topology_direct_flag_writes": 0,
            "active_stopped_layouts_distinct": True,
            "physical_exit_reentry_cases": 2,
            "checkpoint_positions": {
                "seafoam_active_current": {
                    "save_before": {"x": 15, "y": 10, "warp_id": 1},
                    "cold_continue": {"x": 15, "y": 10, "warp_id": 1},
                },
                "seafoam_stopped_current": {
                    "save_before": {"x": 9, "y": 19, "warp_id": 3},
                    "cold_continue": {"x": 9, "y": 19, "warp_id": 3},
                },
            },
            "checkpoint_framebuffer_fnv1a64": {
                "seafoam_active_current": FIXTURE_PPM_FNV1A64,
                "seafoam_stopped_current": FIXTURE_PPM_FNV1A64,
            },
            "start_save_cases": 2,
            "fresh_continue_cases": 2,
            "field_callback_chain_cases": 2,
            "actual_walk_steps": 80,
            "bootstrap_stock_warp_calls": 5,
            "direct_owner_or_script_calls": 0,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    @staticmethod
    def _artifacts(directory: Path, names: tuple[str, ...]) -> None:
        save = bytearray(RUNNER.SAVE_SIZE)
        save[0] = 0x25
        save[-1] = 0x61
        pixels = bytes(index & 0xFF for index in range(RUNNER.PPM_PIXEL_SIZE))
        for name in names:
            (directory / f"{name}.srm").write_bytes(save)
            (directory / f"{name}.ppm").write_bytes(RUNNER.PPM_HEADER + pixels)

    def test_c_closes_real_input_owner_battle_blackout_and_fall_lifecycles(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for token in (
            "s61_drive_interaction", "world_finish_battle",
            "WORLD_BATTLE_OUTCOME_LOST", "pl_complete_league_win",
            "PL_LEAGUE_PROXY_GOTO", "PL_LEAGUE_TAG5_ROOT",
            "pl_actual_warp", "pl_actual_fall", "PL_FALL_WARP_EFFECT_7",
            "PL_FALL_WARP_BEHAVIOR", "s61_normal_input_save(core)",
            "s61_open_fresh", "s61_field_roundtrip_exact",
            "PL_UPPER_FIRST", "PL_UPPER_SECOND",
            "PL_B3_FIRST_STAGE", "PL_B3_SECOND_STAGE",
            "pl_route20_topology_reset", "pl_snapshot_b3_obstacles",
            "route20_owner_hits", "route20_reset_owner_pc_hits",
            "pl_assert_seafoam_checkpoint_state", "PL_B4_SCENE_VAR",
            "pl_framebuffer_rgb_fnv1a64",
            "checkpoint_framebuffer_fnv1a64",
            "pl_artifact_prefix(ppm_prefix, sizeof(ppm_prefix), directory, stem)",
            "\"upper-first-1f\", &PL_SEAFOAM_1F, 2U",
            "\"upper-first-b1\", &PL_SEAFOAM_B1, 3U",
            "\"upper-first-b2\", &PL_SEAFOAM_B2, 2U",
            "\"upper-second-1f\", &PL_SEAFOAM_1F, 3U",
            "\"upper-second-b1\", &PL_SEAFOAM_B1, 4U",
            "\"upper-second-b2\", &PL_SEAFOAM_B2, 3U",
            "\"b3-second-to-b4\", &PL_B3, 5U, {12U, 16U}, {9U, 18U}",
            "{3U, 13, 16, PL_B3_OBSTACLE_2_HIDE}",
            "{4U, 9, 16, PL_B3_OBSTACLE_1_HIDE}",
            "{WORLD_KEY_DOWN, 2U}, {WORLD_KEY_LEFT, 3U}",
            "strength.lifecycle_flag_set_observed",
            "strength.watched_instruction_pc = WORLD_FLAG_SET & ~1U",
            "direct_owner_or_script_calls\\\":0",
            "\\\"failed\\\":0,\\\"untested\\\":0,\\\"warnings\\\":0",
        ):
            self.assertIn(token, source)
        self.assertNotIn("battle_win_loss_exercised\\\":false", source)
        self.assertNotIn("boulder_push_exercised\\\":false", source)
        self.assertNotIn(
            "{WORLD_KEY_LEFT, 2U}, {WORLD_KEY_DOWN, 2U}", source
        )
        self.assertNotIn(
            'pl_path(ppm, sizeof(ppm), directory, stem, "ppm")', source
        )

    def test_embedded_harness_only_renames_outer_main(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "embedded.c"
            identity = RUNNER._build_embedded(output)
            transformed = output.read_text(encoding="utf-8")
        original = (ROOT / RUNNER.EMBEDDED).read_text(encoding="utf-8")
        self.assertTrue(identity["main_renamed"])
        self.assertEqual(
            transformed.replace(RUNNER._RENAMED, RUNNER._MAIN, 1), original
        )

    def test_strict_compile_and_source_hash_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = RUNNER.compile_runner(Path(temporary) / "runner")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            set(report["sources"]),
            {"runner_c", "orchestrator", "rfu_source", "rfu_header"},
        )
        self.assertRegex(report["sources"]["runner_c"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(report["sources"]["orchestrator"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(report["sources"]["rfu_source"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(report["sources"]["rfu_header"]["sha256"], r"^[0-9a-f]{64}$")

    def test_stale_outputs_are_removed_and_report_write_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            identity = {
                "rom": str(directory / "input.gba"),
                "metadata": str(directory / "input.json"),
            }
            report = directory / "report.json"
            report.write_text("stale", encoding="utf-8")
            self.assertEqual(RUNNER._prepare_output(report, identity), report)
            self.assertFalse(report.exists())
            work = directory / "work"
            work.mkdir()
            for stem in RUNNER.ARTIFACT_STEMS["league"]:
                for extension in ("srm", "ppm"):
                    (work / f"{stem}.{extension}").write_text(
                        "stale", encoding="utf-8"
                    )
            for name in RUNNER.PROCESS_ARTIFACT_NAMES.values():
                (work / name).write_text("stale", encoding="utf-8")
            RUNNER._prepare_runtime_artifacts(work, "league")
            self.assertEqual(list(work.iterdir()), [])
            value = {"schema_version": 2, "status": "PASS"}
            RUNNER._write_json_atomic(report, value)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8")), value)
            self.assertEqual(list(directory.glob("report.json.*.tmp")), [])

    def test_run_directory_rejects_unknown_entries_and_runs_are_exact_two(self) -> None:
        for runs in (0, 1, 3, True):
            with self.subTest(runs=runs), self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "exact 2"
            ):
                RUNNER._require_runs(runs)
        RUNNER._require_runs(2)
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run-01"
            run_dir.mkdir()
            (run_dir / "foreign-user-file").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "未知"
            ):
                RUNNER._prepare_run_directory(run_dir, "league")
            self.assertTrue((run_dir / "foreign-user-file").is_file())

    def test_process_artifacts_are_atomic_and_canonical_result_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._league()
            stdout = json.dumps(value, separators=(",", ":")).encode() + b"\n"
            parsed = RUNNER._parse_process_stdout(stdout)
            self.assertEqual(parsed, value)
            stdout_descriptor = RUNNER._retain_bytes(
                directory / "process.stdout.raw", stdout,
                role="mGBA_process_stdout", format_name="raw-utf8-json-line",
                case_id="league",
            )
            canonical = RUNNER._canonical_result_bytes(parsed)
            result_descriptor = RUNNER._retain_bytes(
                directory / "case-result.canonical.json", canonical,
                role="canonical_case_result", format_name="canonical-json",
                case_id="league",
            )
            self.assertTrue(stdout_descriptor["atomic_retain"])
            self.assertEqual(result_descriptor["sha256"], RUNNER._sha(canonical))
            self.assertEqual(
                json.loads((directory / "case-result.canonical.json")
                           .read_text(encoding="utf-8")),
                value,
            )
            for invalid in (b"", stdout + b"\n", b"[]\n", b"\xff\n"):
                with self.subTest(invalid=invalid), self.assertRaises(
                    RUNNER.ProgressionLifecycleError
                ):
                    RUNNER._parse_process_stdout(invalid)

    def test_independent_run_result_hash_and_normalized_payload_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            records, validations = self._two_run_records(directory)
            digest = records[0]["process"]["normalized_result_sha256"]
            self.assertEqual(
                RUNNER._require_replay_match(records, validations), digest
            )
            changed = copy.deepcopy(records)
            changed[1]["process"]["normalized_result_sha256"] = "b" * 64
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "normalized result"
            ):
                RUNNER._require_replay_match(changed, validations)
            changed_validations = copy.deepcopy(validations)
            changed_validations[1]["result"]["actual_walk_steps"] += 1
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "normalized result"
            ):
                RUNNER._require_replay_match(records, changed_validations)
            changed_role = copy.deepcopy(records)
            changed_role[1]["artifacts"]["league_full_chain_srm"][
                "role"
            ] = "forged_semantic_role"
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "artifact descriptor"
            ):
                RUNNER._require_replay_match(changed_role, validations)

    def _two_run_records(
            self, directory: Path,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        records: list[dict[str, object]] = []
        validations: list[dict[str, object]] = []
        value = self._league()
        stdout = json.dumps(value, separators=(",", ":")).encode() + b"\n"
        for index in (1, 2):
            run_dir = directory / f"run-{index:02d}"
            precleared = RUNNER._prepare_run_directory(run_dir, "league")

            def fake_run(command: list[str], **_: object) -> object:
                self._artifacts(
                    run_dir, ("league_full_chain", "league_blackout_retry")
                )
                return RUNNER.subprocess.CompletedProcess(
                    command, 0, stdout=stdout, stderr=b""
                )

            with mock.patch.object(
                RUNNER.subprocess, "run", side_effect=fake_run
            ):
                record, normalized = RUNNER._run_once(
                    "league", Path("/fixture/runner"), "/fixture/rom.gba",
                    run_dir, index, precleared,
                )
            records.append(record)
            validations.append(normalized)
        return records, validations

    @staticmethod
    def _resign_artifact(
            record: dict[str, object], key: str, raw: bytes,
    ) -> None:
        artifacts = record["artifacts"]
        assert isinstance(artifacts, dict)
        descriptor = artifacts[key]
        assert isinstance(descriptor, dict)
        path = Path(descriptor["path"])
        path.write_bytes(raw)
        descriptor["size"] = len(raw)
        descriptor["sha256"] = RUNNER._sha(raw)

    def test_second_run_resigned_srm_and_ppm_substitutions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            records, validations = self._two_run_records(Path(temporary))
            second = records[1]

            srm_key = "league_full_chain_srm"
            srm_descriptor = second["artifacts"][srm_key]
            srm = bytearray(Path(srm_descriptor["path"]).read_bytes())
            srm[1] ^= 0x7F
            self._resign_artifact(second, srm_key, bytes(srm))

            ppm_key = "league_full_chain_framebuffer"
            ppm_descriptor = second["artifacts"][ppm_key]
            ppm = bytearray(Path(ppm_descriptor["path"]).read_bytes())
            ppm[len(RUNNER.PPM_HEADER) + 17] ^= 0x5A
            self._resign_artifact(second, ppm_key, bytes(ppm))

            second_result = validations[1]["result"]
            second_result["checkpoint_framebuffer_fnv1a64"][
                "league_full_chain"
            ] = f"{RUNNER._fnv1a64(bytes(ppm[len(RUNNER.PPM_HEADER):])):016X}"
            stdout = (
                json.dumps(second_result, separators=(",", ":")) + "\n"
            ).encode()
            canonical = RUNNER._canonical_result_bytes(second_result)
            self._resign_artifact(second, "process_stdout", stdout)
            self._resign_artifact(second, "canonical_case_result", canonical)
            second["process"]["normalized_result_sha256"] = RUNNER._sha(
                canonical
            )

            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "artifact descriptor"
            ):
                RUNNER._require_replay_match(records, validations)

    def test_one_os_run_retains_exact_seven_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run-01"
            precleared = RUNNER._prepare_run_directory(run_dir, "league")
            value = self._league()
            stdout = json.dumps(value, separators=(",", ":")).encode() + b"\n"

            def fake_run(command: list[str], **_: object) -> object:
                self._artifacts(
                    run_dir, ("league_full_chain", "league_blackout_retry")
                )
                return RUNNER.subprocess.CompletedProcess(
                    command, 0, stdout=stdout, stderr=b""
                )

            with mock.patch.object(
                RUNNER.subprocess, "run", side_effect=fake_run
            ):
                record, normalized = RUNNER._run_once(
                    "league", Path("/fixture/runner"), "/fixture/rom.gba",
                    run_dir, 1, precleared,
                )
            self.assertEqual(len(record["artifacts"]), 7)
            self.assertEqual(
                set(record["artifacts"]),
                {
                    "process_stdout", "process_stderr",
                    "canonical_case_result", "league_full_chain_srm",
                    "league_full_chain_framebuffer",
                    "league_blackout_retry_srm",
                    "league_blackout_retry_framebuffer",
                },
            )
            self.assertTrue(record["process"]["stderr_empty"])
            self.assertEqual(normalized["result"], value)
            self.assertEqual(
                {path.name for path in run_dir.iterdir()},
                RUNNER._runtime_artifact_names("league"),
            )

    def test_report_output_cannot_alias_inputs_or_be_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            rom = directory / "input.gba"
            metadata = directory / "input.json"
            identity = {"rom": str(rom), "metadata": str(metadata)}
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "同一path"
            ):
                RUNNER._prepare_output(rom, identity)
            output_directory = directory / "report.json"
            output_directory.mkdir()
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "通常file"
            ):
                RUNNER._prepare_output(output_directory, identity)

    def test_complete_league_and_seafoam_results_re_read_all_raw_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._artifacts(
                directory, ("league_full_chain", "league_blackout_retry")
            )
            league = RUNNER.validate_result(self._league(), directory, "league")
            self._artifacts(
                directory, ("seafoam_active_current", "seafoam_stopped_current")
            )
            seafoam = RUNNER.validate_result(self._seafoam(), directory, "seafoam")
            self.assertTrue(league["complete"])
            self.assertTrue(seafoam["complete"])
            self.assertTrue(league["artifact_sha_re_read_by_orchestrator"])
            self.assertTrue(seafoam["distinct_mcore_cold_continue_validated"])
            for report in (league, seafoam):
                self.assertEqual(len(report["artifacts"]), 4)
                for artifact in report["artifacts"].values():
                    self.assertTrue(artifact["raw_re_read"])
                    self.assertTrue(artifact["atomic_retain"])
                    self.assertTrue(Path(artifact["path"]).is_absolute())

    def test_result_negative_mutations_are_rejected(self) -> None:
        mutations = (
            ("direct_owner_or_script_calls", 1, "direct_owner"),
            ("untested", 1, "untested"),
            ("owner_pc_hits", 6, "owner PC"),
            ("blackout_exercised", False, "blackout"),
            ("battle_resume_instruction_trace_cases", 5, "instruction"),
            ("elite_completion_adapter_cases", 4, "adapter"),
            ("champion_no_geometry_negative_control", False, "negative"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._artifacts(
                directory, ("league_full_chain", "league_blackout_retry")
            )
            for key, replacement, message in mutations:
                with self.subTest(key=key):
                    value = copy.deepcopy(self._league())
                    value[key] = replacement
                    with self.assertRaisesRegex(
                        RUNNER.ProgressionLifecycleError, message
                    ):
                        RUNNER.validate_result(value, directory, "league")
            value = self._league()
            value["unexpected"] = 1
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "keys不一致"
            ):
                RUNNER.validate_result(value, directory, "league")

    def test_owner_counter_negative_mutations_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._artifacts(
                directory, ("seafoam_active_current", "seafoam_stopped_current")
            )
            for key in (
                "fall_owner_pc_hits", "push_owner_pc_hits",
                "strength_owner_pc_hits",
            ):
                value = self._seafoam()
                value[key] = 1
                with self.subTest(key=key), self.assertRaisesRegex(
                    RUNNER.ProgressionLifecycleError, "owner PC"
                ):
                    RUNNER.validate_result(value, directory, "seafoam")
            value = self._seafoam()
            value["strength_zero_to_one_transition_cases"] = 1
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "zero_to_one"
            ):
                RUNNER.validate_result(value, directory, "seafoam")
            value = self._seafoam()
            value["route20_reset_owner_pc_hits"] = 1
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "Route20 reset owner PC"
            ):
                RUNNER.validate_result(value, directory, "seafoam")
            mutations = (
                ("route20_reset_owner_cases", 1),
                ("upper_b3_physical_chain_cases", 1),
                ("distinct_b3_b4_physical_chain_cases", 1),
                ("actual_boulder_push_cases", 8),
                ("actual_boulder_push_steps", 22),
                ("native_strength_clear_after_fall_cases", 8),
                ("topology_hide_arrival_transition_cases", 8),
                ("non_producer_obstacle_controls", 1),
                ("topology_direct_flag_writes", 1),
                ("b3_current_stop_observed", False),
                ("b4_current_stop_observed", False),
            )
            for key, replacement in mutations:
                value = self._seafoam()
                value[key] = replacement
                with self.subTest(key=key), self.assertRaisesRegex(
                    RUNNER.ProgressionLifecycleError, key
                ):
                    RUNNER.validate_result(value, directory, "seafoam")

    def test_checkpoint_position_schema_and_cold_continue_match_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._artifacts(
                directory, ("league_full_chain", "league_blackout_retry")
            )
            value = self._league()
            value["checkpoint_positions"]["league_full_chain"][
                "cold_continue"
            ]["x"] += 1
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "位置が不一致"
            ):
                RUNNER.validate_result(value, directory, "league")
            value = self._league()
            value["checkpoint_positions"]["league_full_chain"][
                "save_before"
            ]["warp_id"] = 256
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "u8"
            ):
                RUNNER.validate_result(value, directory, "league")
            value = self._league()
            value["checkpoint_framebuffer_fnv1a64"][
                "league_full_chain"
            ] = "0000000000000000"
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "FNV-1a64不一致"
            ):
                RUNNER.validate_result(value, directory, "league")
            value = self._league()
            value["checkpoint_framebuffer_fnv1a64"][
                "league_full_chain"
            ] = "abcdef0123456789"
            with self.assertRaisesRegex(
                RUNNER.ProgressionLifecycleError, "形式"
            ):
                RUNNER.validate_result(value, directory, "league")

    def test_srm_size_content_and_symlink_mutations_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            names = ("league_full_chain", "league_blackout_retry")
            self._artifacts(directory, names)
            target = directory / "league_full_chain.srm"
            target.write_bytes(bytes(RUNNER.SAVE_SIZE - 1))
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "size"):
                RUNNER.validate_result(self._league(), directory, "league")
            self._artifacts(directory, names)
            target.write_bytes(bytes(RUNNER.SAVE_SIZE))
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "一様"):
                RUNNER.validate_result(self._league(), directory, "league")
            self._artifacts(directory, names)
            backing = directory / "backing.srm"
            target.rename(backing)
            target.symlink_to(backing)
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "通常file"):
                RUNNER.validate_result(self._league(), directory, "league")

    def test_framebuffer_header_size_content_and_symlink_mutations_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            names = ("seafoam_active_current", "seafoam_stopped_current")
            self._artifacts(directory, names)
            target = directory / "seafoam_active_current.ppm"
            target.write_bytes(b"P6\n1 1\n255\n\x00\x00\x00")
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "形式/size"):
                RUNNER.validate_result(self._seafoam(), directory, "seafoam")
            self._artifacts(directory, names)
            target.write_bytes(RUNNER.PPM_HEADER + bytes(RUNNER.PPM_PIXEL_SIZE))
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "一様"):
                RUNNER.validate_result(self._seafoam(), directory, "seafoam")
            self._artifacts(directory, names)
            backing = directory / "backing.ppm"
            target.rename(backing)
            target.symlink_to(backing)
            with self.assertRaisesRegex(RUNNER.ProgressionLifecycleError, "通常file"):
                RUNNER.validate_result(self._seafoam(), directory, "seafoam")


if __name__ == "__main__":
    unittest.main()
