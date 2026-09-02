from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_stage61_display_npc_event_audit as builder
from tests.stage61_save_fixture import build_stage61_save


ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "build/stages/61_display_npc_event_audit.gba"
METADATA_PATH = ROOT / "build/stages/61_display_npc_event_audit.json"
PPM_HEADER = b"P6\n240 160\n255\n"


class Stage61ProgressionBuilderGateTests(unittest.TestCase):
    @staticmethod
    def _positions(mode: str) -> dict[str, dict[str, dict[str, int]]]:
        stems = (
            ("league_full_chain", "league_blackout_retry")
            if mode == "league" else
            ("seafoam_active_current", "seafoam_stopped_current")
        )
        return {
            stem: {
                "save_before": {
                    "x": 10 + index, "y": 20 + index, "warp_id": index,
                },
                "cold_continue": {
                    "x": 10 + index, "y": 20 + index, "warp_id": index,
                },
            }
            for index, stem in enumerate(stems, start=1)
        }

    @classmethod
    def _league(cls) -> dict[str, object]:
        return {
            "schema_version": 3, "status": "PASS",
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
            "trainer_battle_wins": 6, "trainer_battle_losses": 1,
            "blackout_exercised": True, "last_heal_match": True,
            "blackout_field_recovered": True,
            "blackout_scene_high_water_preserved": True,
            "completion_absent_after_loss": True,
            "actual_reentry_after_blackout": True,
            "retry_win_committed": True,
            "physical_room_warp_transitions": 6,
            "actual_walk_steps": 123, "face_a_battle_cases": 7,
            "owner_pc_cases": 7, "owner_pc_hits": 70,
            "battle_resume_instruction_trace_cases": 6,
            "elite_completion_adapter_cases": 5,
            "champion_no_geometry_negative_control": True,
            "field_recovery_cases": 6,
            "hall_of_fame_tag3_field_terminal": True,
            "checkpoint_positions": cls._positions("league"),
            "start_save_cases": 2, "fresh_continue_cases": 2,
            "bootstrap_stock_warp_calls": 3,
            "direct_owner_or_script_calls": 0,
            "failed": 0, "untested": 0, "warnings": 0,
        }

    @classmethod
    def _seafoam(cls) -> dict[str, object]:
        return {
            "schema_version": 3, "status": "PASS",
            "case": "seafoam_progression_lifecycle_complete",
            "static_maps_83_through_87": 5, "runtime_maps_b3_b4": 2,
            "flag_state_variants": 2, "runtime_maps_1f_through_b4": 5,
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
            "fall_owner_pc_cases": 9, "fall_owner_pc_hits": 19,
            "push_owner_pc_cases": 9, "push_owner_pc_hits": 20,
            "strength_owner_pc_cases": 9, "strength_owner_pc_hits": 21,
            "surf_observed_cases": 4, "active_current_motion_cases": 3,
            "active_current_motion_observed": True,
            "b3_current_stop_observed": True,
            "b4_current_stop_observed": True,
            "stopped_current_flag_observed": True,
            "non_producer_obstacle_controls": 2,
            "topology_direct_flag_writes": 0,
            "active_stopped_layouts_distinct": True,
            "physical_exit_reentry_cases": 2,
            "checkpoint_positions": cls._positions("seafoam"),
            "start_save_cases": 2, "fresh_continue_cases": 2,
            "field_callback_chain_cases": 2,
            "actual_walk_steps": 180, "bootstrap_stock_warp_calls": 5,
            "direct_owner_or_script_calls": 0,
            "failed": 0, "untested": 0, "warnings": 0,
        }

    @staticmethod
    def _descriptor(
        path: Path, raw: bytes, *, role: str,
        format_name: str, case_id: str,
    ) -> dict[str, object]:
        path.write_bytes(raw)
        return {
            "path": str(path.resolve()), "name": path.name, "role": role,
            "format": format_name, "case_id": case_id, "size": len(raw),
            "sha256": builder._sha(raw), "raw_re_read": True,
            "atomic_retain": True,
        }

    @classmethod
    def _fixture(
        cls, directory: Path, mode: str,
    ) -> tuple[dict[str, object], dict[str, object]]:
        rom_raw = ROM_PATH.read_bytes()
        metadata_raw = METADATA_PATH.read_bytes()
        result = cls._league() if mode == "league" else cls._seafoam()
        stems = (
            ("league_full_chain", "league_blackout_retry")
            if mode == "league" else
            ("seafoam_active_current", "seafoam_stopped_current")
        )
        pixels_by_stem = {
            stem: bytes(
                (index + stem_index * 17) & 0xFF
                for index in range(240 * 160 * 3)
            )
            for stem_index, stem in enumerate(stems, start=1)
        }
        result["checkpoint_framebuffer_fnv1a64"] = {
            stem: builder._mgba_effect_fnv1a64(pixels)
            for stem, pixels in pixels_by_stem.items()
        }
        save_specs: dict[str, dict[str, object]] = {
            "league_full_chain": {
                "map_group": 97, "map_number": 80,
                "flags": {
                    identifier: True for identifier in range(0x1407, 0x140D)
                },
                "variables": {0x516C: 5},
            },
            "league_blackout_retry": {
                "map_group": 97, "map_number": 76,
                "flags": {
                    0x1407: True, 0x1408: True, 0x1409: False,
                    0x140A: False, 0x140B: False, 0x140C: False,
                },
                "variables": {0x516C: 2},
            },
            "seafoam_active_current": {
                "map_group": 97, "map_number": 87,
                "flags": {
                    0x0805: False, 0x162D: False, 0x162E: False,
                    **{value: True for value in range(0x162F, 0x1635)},
                    0x1635: True, 0x1636: False, 0x1637: False,
                    0x1638: False, 0x1639: False, 0x163A: True,
                    0x163D: False, 0x163E: False,
                },
                "variables": {0x5167: 0},
            },
            "seafoam_stopped_current": {
                "map_group": 97, "map_number": 87,
                "flags": {
                    0x0805: False,
                    **{value: True for value in range(0x162D, 0x1633)},
                    0x1633: False, 0x1634: False, 0x1635: True,
                    0x1636: False, 0x1637: True, 0x1638: False,
                    0x1639: False, 0x163A: False,
                    0x163D: True, 0x163E: True,
                },
                "variables": {0x5167: 0},
            },
        }

        embedded_path = ROOT / builder.MGBA_RUNNER_SOURCE
        embedded_raw = embedded_path.read_bytes()
        embedded_text = embedded_raw.decode("utf-8")
        transformed = builder._sha(embedded_text.replace(
            "\nint main(int argc, char **argv)\n{",
            "\nint s61_embedded_progression_main(int argc, char **argv)\n{",
            1,
        ).encode("utf-8"))
        runner_path = ROOT / builder.MGBA_PROGRESSION_LIFECYCLE_RUNNER_SOURCE
        orchestrator_path = (
            ROOT / builder.MGBA_PROGRESSION_LIFECYCLE_ORCHESTRATOR_SOURCE
        )

        def map_row(
            group: int, number: int, tags: list[int],
        ) -> dict[str, object]:
            header = builder._map_header_offset(rom_raw, group, number)
            table = builder._u32(rom_raw, header + 8, "test map script")
            return {
                "map": f"{group:03d}/{number:03d}",
                "header": f"0x{builder.GBA_BASE + header:08X}",
                "script_table": f"0x{table:08X}", "tags": tags,
            }

        roots = {
            "map_groups_pointer": "0x08054B0C",
            "league": [map_row(97, number, tags) for number, tags in (
                (75, [5, 1, 4, 2]), (76, [5, 1, 4, 2]),
                (77, [5, 1, 4, 2]), (78, [5, 1, 4, 2]),
                (79, [4, 2]), (80, [3]),
            )],
            "seafoam": [map_row(97, number, tags) for number, tags in (
                (83, []), (84, []), (85, []),
                (86, [3, 2]), (87, [3, 1, 4, 2]),
            )],
        }
        checkpoint_expectations = {
            stem: {
                "map": {
                    "group": save_specs[stem]["map_group"],
                    "number": save_specs[stem]["map_number"],
                },
                "flags": {
                    f"0x{identifier:04X}": state
                    for identifier, state in sorted(
                        save_specs[stem]["flags"].items()
                    )
                },
                "vars": {
                    f"0x{identifier:04X}": value
                    for identifier, value in sorted(
                        save_specs[stem].get("variables", {}).items()
                    )
                },
            }
            for stem in stems
        }
        canonical = (
            json.dumps(
                result, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ) + "\n"
        ).encode("utf-8")
        normalized_sha = builder._sha(canonical)
        run_records = []
        for run_index in (1, 2):
            run_dir = directory / f"run-{run_index:02d}"
            run_dir.mkdir()
            artifacts = {
                "process_stdout": cls._descriptor(
                    run_dir / "process.stdout.raw", canonical,
                    role="mGBA_process_stdout",
                    format_name="raw-utf8-json-line", case_id=mode,
                ),
                "process_stderr": cls._descriptor(
                    run_dir / "process.stderr.raw", b"",
                    role="mGBA_process_stderr", format_name="raw-bytes",
                    case_id=mode,
                ),
                "canonical_case_result": cls._descriptor(
                    run_dir / "case-result.canonical.json", canonical,
                    role="canonical_case_result",
                    format_name="canonical-json", case_id=mode,
                ),
            }
            for stem_index, stem in enumerate(stems, start=1):
                position = result["checkpoint_positions"][stem][
                    "cold_continue"
                ]
                save = build_stage61_save(
                    **save_specs[stem], x=position["x"], y=position["y"],
                    warp_id=position["warp_id"],
                    marker=stem_index,
                )
                pixels = pixels_by_stem[stem]
                artifacts[f"{stem}_srm"] = cls._descriptor(
                    run_dir / f"{stem}.srm", save,
                    role="cold_continue_srm", format_name="flash1m-srm",
                    case_id=stem,
                )
                artifacts[f"{stem}_framebuffer"] = cls._descriptor(
                    run_dir / f"{stem}.ppm", PPM_HEADER + pixels,
                    role="cold_continue_framebuffer",
                    format_name="ppm-p6-240x160", case_id=stem,
                )
            run_records.append({
                "run_index": run_index,
                "directory": str(run_dir.resolve()),
                "directory_empty_before_launch": True,
                "stale_artifacts_precleared": 0,
                "process": {
                    "command": [
                        str((directory / "stage61-progression-lifecycle").resolve()),
                        str(ROM_PATH.resolve()), str(run_dir.resolve()), mode,
                    ],
                    "returncode": 0,
                    "stdout_case_result_exact_match": True,
                    "stderr_empty": True,
                    "normalized_result_sha256": normalized_sha,
                },
                "artifacts": artifacts,
            })

        report: dict[str, object] = {
            "schema_version": 3, "status": "PASS",
            "case": "stage61_progression_lifecycle_e2e", "mode": mode,
            "runs": 2, "failed": 0, "untested": 0, "warnings": 0,
            "identity": {
                "rom": str(ROM_PATH.resolve()),
                "rom_sha256": builder._sha(rom_raw),
                "metadata": str(METADATA_PATH.resolve()),
                "metadata_sha256": builder._sha(metadata_raw),
                "roots": roots,
            },
            "compile": {
                "status": "PASS",
                "embedded": {
                    "source": str(builder.MGBA_RUNNER_SOURCE),
                    "source_sha256": builder._sha(embedded_raw),
                    "transformed_sha256": transformed,
                    "main_renamed": True,
                },
                "sources": {
                    "runner_c": {
                        "path": str(runner_path.resolve()),
                        "sha256": builder._sha(runner_path.read_bytes()),
                    },
                    "orchestrator": {
                        "path": str(orchestrator_path.resolve()),
                        "sha256": builder._sha(orchestrator_path.read_bytes()),
                    },
                },
                "command": (
                    "cc -std=c11 -O2 -Wall -Wextra -Werror "
                    "-pedantic ... -lmgba"
                ),
            },
            "execution": {
                "backend": "libmGBA", "os_subprocess_runs": 2,
                "distinct_mcore_instances_per_run": 6,
                "cold_boot_continue_instances_per_run": 2,
                "real_gba_key_input": True,
                "host_direct_owner_or_script_calls": 0,
                "stale_runtime_artifacts_precleared": True,
                "run_directories_empty_before_launch": True,
                "retained_artifacts_per_run": 7,
                "retained_artifacts_total": 14,
                "all_retained_artifacts_atomic": True,
                "stdout_case_result_exact_match": True,
                "independent_run_normalized_result_sha256_equal": True,
                "normalized_result_sha256": normalized_sha,
                "work_directory": str(directory.resolve()),
                "run_directories": [
                    record["directory"] for record in run_records
                ],
                "stderr_empty": True,
            },
            "validation": {
                "mode": mode, "result": result,
                "artifact_sha_re_read_by_orchestrator": True,
                "natural_input_owner_and_callback_validated": True,
                "distinct_mcore_cold_continue_validated": True,
                "checkpoint_expectations": checkpoint_expectations,
                "complete": True, "remaining": None,
                "independent_os_subprocess_replay_validated": True,
            },
            "run_records": run_records,
        }
        report_path = directory / f"{mode}.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        context = {
            "mode": mode, "report_path": report_path,
            "rom_path": ROM_PATH, "metadata_path": METADATA_PATH,
            "rom_raw": rom_raw, "metadata_raw": metadata_raw,
        }
        return report, context

    @staticmethod
    def _rewrite(
        report: dict[str, object], context: dict[str, object],
    ) -> None:
        Path(context["report_path"]).write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_both_modes_re_read_two_runs_and_decode_each_save(self) -> None:
        (ROOT / ".local").mkdir(exist_ok=True)
        for mode in ("league", "seafoam"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                dir=ROOT / ".local",
            ) as temporary:
                _, context = self._fixture(Path(temporary), mode)
                result = builder._validate_mgba_progression_lifecycle_evidence(
                    **context,
                )
                self.assertEqual(result["mode"], mode)
                self.assertEqual(result["artifact_count"], 14)
                self.assertEqual(len(result["decoded_save_contracts"]), 4)

    def test_rejects_source_metric_and_raw_stdout_tamper(self) -> None:
        (ROOT / ".local").mkdir(exist_ok=True)
        mutations = {
            "source": lambda report: report["compile"]["sources"][
                "runner_c"
            ].__setitem__("sha256", "0" * 64),
            "metric": lambda report: report["validation"][
                "result"
            ].__setitem__("elite_completion_adapter_cases", 4),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                dir=ROOT / ".local",
            ) as temporary:
                report, context = self._fixture(Path(temporary), "league")
                mutate(report)
                self._rewrite(report, context)
                with self.assertRaises(builder.Stage61BuildError):
                    builder._validate_mgba_progression_lifecycle_evidence(
                        **context,
                    )

        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as temporary:
            report, context = self._fixture(Path(temporary), "league")
            artifact = report["run_records"][0]["artifacts"][
                "process_stdout"
            ]
            forged = (
                b'{"schema_version":3,"status":"PASS",'
                b'"case":"forged"}\n'
            )
            Path(artifact["path"]).write_bytes(forged)
            artifact["size"] = len(forged)
            artifact["sha256"] = builder._sha(forged)
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "stdout/canonical/stderr",
            ):
                builder._validate_mgba_progression_lifecycle_evidence(
                    **context,
                )

    def test_rejects_fake_flash_and_checkpoint_position_lie(self) -> None:
        (ROOT / ".local").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as temporary:
            report, context = self._fixture(Path(temporary), "league")
            artifact = report["run_records"][0]["artifacts"][
                "league_full_chain_srm"
            ]
            fake = bytes([0x25]) + bytes(128 * 1024 - 2) + bytes([0x61])
            Path(artifact["path"]).write_bytes(fake)
            artifact["sha256"] = builder._sha(fake)
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "complete save generation",
            ):
                builder._validate_mgba_progression_lifecycle_evidence(
                    **context,
                )

        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as temporary:
            report, context = self._fixture(Path(temporary), "seafoam")
            report["validation"]["result"]["checkpoint_positions"][
                "seafoam_active_current"
            ]["cold_continue"]["x"] += 1
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "SAVE直前/cold Continue",
            ):
                builder._validate_mgba_progression_lifecycle_evidence(
                    **context,
                )


if __name__ == "__main__":
    unittest.main()
