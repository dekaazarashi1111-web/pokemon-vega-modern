from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.stage61_save_fixture import build_stage61_save


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_stage61_event_lifecycle_e2e.py"
SOURCE_PATH = ROOT / "tools/mgba_stage61_event_lifecycle_e2e.c"
SPEC = importlib.util.spec_from_file_location("stage61_event_lifecycle", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class Stage61EventLifecycleE2eTests(unittest.TestCase):
    @staticmethod
    def _roots() -> dict[str, object]:
        ferry = []
        groups = ((31, 6), (32, 4), (33, 4), (35, 5),
                  (36, 2), (37, 2), (38, 0))
        for index, (group, number) in enumerate(groups):
            ferry.append({"owner_id": f"OBJECT:{group:03d}/{number:03d}:001",
                          "map": f"{group:03d}/{number:03d}",
                          "root": f"0x{0x08180000 + index * 0x100:08X}"})
        result = {
            "ferry": ferry,
            "vermilion_trash": [{"id": index, "root": f"0x{0x09430000 + index * 11:08X}"}
                                 for index in range(1, 16)],
            "route16_snorlax": {"root": "0x094283A0"},
            "route12_snorlax": {"root": "0x09428344"},
            "flute_giver": {"root": "0x087700B1"},
        }
        return result

    @staticmethod
    def _write_artifact(directory: Path, name: str, size: int) -> None:
        if size == RUNNER.PPM_SIZE:
            pattern = name.encode("ascii")
            rgb_size = 240 * 160 * 3
            rgb = (pattern * ((rgb_size + len(pattern) - 1) // len(pattern)))[
                :rgb_size
            ]
            raw = b"P6\n240 160\n255\n" + rgb
        else:
            raw = bytes(size)
        (directory / name).write_bytes(raw)

    @staticmethod
    def _framebuffer_fields(directory: Path, case: str) -> dict[str, object]:
        roles = RUNNER._CASE_FRAMEBUFFER_ROLES[case]
        hashes = {
            name: RUNNER._ppm_rgb_fnv1a64(
                (directory / name).read_bytes(), f"unit {name}",
            )
            for name in roles
        }
        return {
            "framebuffer_artifact_fnv1a64": hashes,
            "framebuffer_artifact_roles": dict(roles),
        }

    @classmethod
    def _ferry(cls, directory: Path) -> dict[str, object]:
        roots = cls._roots()["ferry"]
        owners = []
        stems = ("ferry-seven", "ferry-one", "ferry-two", "ferry-four",
                 "ferry-five", "ferry-six", "ferry-three")
        for root, stem in zip(roots, stems, strict=True):
            srm = f"{stem}.srm"
            ppm = f"{stem}.ppm"
            cls._write_artifact(directory, srm, RUNNER.SAVE_SIZE)
            cls._write_artifact(directory, ppm, RUNNER.PPM_SIZE)
            owners.append({
                "owner_id": root["owner_id"],
                "map": "/".join(str(int(value))
                                for value in root["map"].split("/")),
                "owner_root": root["root"], "actual_walk_steps": 1,
                "direction_plus_a": True, "choice_cancel_via_b": True,
                "cancel_result": 127, "post_cancel_result": 0,
                "cancel_owner_pc_hits": 1,
                "pre_board_engine_var_readback": {"0x4076": 0, "0x4071": 4},
                "choice_zero_via_a": True, "boarding": True,
                "owner_pc_hits": 1, "special_pc": "0x08147468",
                "special_pc_hits": 1,
                "first_nonfield_callback": "0x0814765D",
                "first_task_function": "0x0807951D", "task_observed": True,
                "arrival": "3/5@23,32", "save_via_start_menu": True,
                "fresh_core_continue": True, "field_input_recovered": True,
                "srm": srm, "ppm": ppm,
            })
        result = {"schema_version": 1, "status": "PASS",
                  "case": "ferry_all_owner_lifecycle",
                  "preparation_teleport_and_engine_var_fixture": True,
                  "preparation_engine_var_writes": [
                      {"var": "0x4076", "value": 0},
                      {"var": "0x4071", "value": 4},
                  ],
                  "preparation_engine_api_calls_only": True,
                  "host_direct_memory_writes": 0,
                  "direct_owner_or_script_calls": 0,
                  "direct_special_calls": 0, "owners": owners,
                  "owner_count": 7, "cancel_count": 7,
                  "boarding_count": 7, "arrival_count": 7,
                  "normal_save_count": 7, "fresh_continue_count": 7,
                  "failed": 0, "untested": 0, "warnings": 0}
        result.update(cls._framebuffer_fields(directory, "ferry"))
        return result

    @classmethod
    def _vermilion(cls, directory: Path) -> dict[str, object]:
        for name in ("vermilion-baseline.ppm", "vermilion-open.ppm",
                     "vermilion-reentry.ppm"):
            cls._write_artifact(directory, name, RUNNER.PPM_SIZE)
        cls._write_artifact(directory, "event-lifecycle-vermilion.srm",
                            RUNNER.SAVE_SIZE)
        result = {"schema_version": 1, "status": "PASS",
                  "case": "vermilion_gym_lifecycle",
                  "preparation_teleport_only": True,
                  "direct_owner_or_script_calls": 0, "map": "98/40",
                  "persistent_flag": "0x1871", "temp_flag": "0x0001",
                  "switches_initial": [1, 2], "wrong_switch": 3,
                  "switches_retry": [4, 5], "actual_walk_steps": 8,
                  "direction_plus_a": True, "owner_pc_hits": 4,
                  "failure_reset": True, "success_persisted": True,
                  "fresh_core_continue": True, "reentry_temp_reset": True,
                  "field_input_recovered": True,
                  "metatile_hashes": {"baseline": "0000000000000001",
                                      "half": "0000000000000002",
                                      "reset": "0000000000000001",
                                      "open": "0000000000000003",
                                      "reentry": "0000000000000003"},
                  "srm": "event-lifecycle-vermilion.srm",
                  "ppms": ["vermilion-baseline.ppm", "vermilion-open.ppm",
                            "vermilion-reentry.ppm"],
                  "failed": 0, "untested": 0, "warnings": 0}
        result.update(cls._framebuffer_fields(directory, "vermilion"))
        return result

    @classmethod
    def _snorlax(cls, directory: Path) -> dict[str, object]:
        srms = ["route16-snorlax-ran.srm", "route16-snorlax-caught.srm",
                "route12-snorlax-caught.srm"]
        ppms = ["route16-snorlax-ran.ppm", "route16-snorlax-caught.ppm",
                "route12-snorlax-caught.ppm"]
        for name in srms[:2]:
            (directory / name).write_bytes(build_stage61_save(
                map_group=96, map_number=27, x=30, y=13,
                flags={0x119E: True, 0x149F: True},
            ))
        (directory / srms[2]).write_bytes(build_stage61_save(
            map_group=96, map_number=23, x=12, y=70,
            flags={0x119E: True, 0x149E: True},
        ))
        for name in ppms:
            cls._write_artifact(directory, name, RUNNER.PPM_SIZE)
        result = {"schema_version": 1, "status": "PASS",
                "case": "route16_snorlax_lifecycle",
                "owner_id": "OBJECT:096/027:005", "owner_root": "0x094283A0",
                "producer_owner_id": "OBJECT:001/045:008",
                "producer_owner_root": "0x087700B1",
                "producer_owner_pc_hits": 3, "producer_message_count": 3,
                "preparation_teleport_and_declared_capture_fixture": True,
                "direct_owner_or_script_calls": 0,
                "natural_flute_producer": True, "actual_walk_steps": 7,
                "direction_plus_a": True, "choice_no_preserved": True,
                "choice_no_result": 0, "choice_yes_battle": True,
                "species": 491, "owner_pc_hits": 3,
                "capture_preparation": {
                    "matches_established_last_ball_fixture": True,
                    "master_ball_added_via_rom_call": True,
                    "host_writes_limited_to_inventory_party_menu_preparation": True,
                    "party_slots_1_through_5_zeroed_by_host": True,
                    "party_count_set_to_one_by_host": True,
                    "bag_ball_pocket_cursor_prepared_by_host": True,
                    "direct_memory_writes_outside_declared_fixture": 0,
                    "battle_struct_host_writes": 0,
                    "battle_result_host_writes": 0,
                    "battle_action_cursor_host_writes": 0,
                    "fresh_continue_before_battle": True,
                    "unused_party_slots_zero": True,
                },
                "outcomes": [{
                    "name": "RAN", "value": 4,
                    "battle_result_via_keys": True, "species": 491,
                    "party_count_before": 6, "party_count_after": 6,
                    "battle_runtime_initialized": True,
                    "battle_runtime_cleaned": True, "field_returned": True,
                    "first_battle_callback": "0x08012345",
                    "battle_input_pulses": 2, "owner_pc_hits": 2,
                    "producer_owner_pc_hits": 1,
                }, {
                    "name": "CAUGHT", "value": 7,
                    "battle_result_via_keys": True,
                    "bag_direction_a": True, "species": 491,
                    "party_count_before": 1, "party_count_after": 2,
                    "captured_species": 491,
                    "capture_preparation_valid": True,
                    "battle_runtime_initialized": True,
                    "battle_runtime_cleaned": True, "field_returned": True,
                    "master_ball_consumed": True,
                    "first_battle_callback": "0x08012345",
                    "battle_input_pulses": 4, "owner_pc_hits": 1,
                    "producer_owner_pc_hits": 1,
                }],
                "route12_capture_control": {
                    "owner_id": "OBJECT:096/023:014",
                    "owner_root": "0x09428344", "map": "96/23",
                    "physical_start": [11, 70], "approach_key": "RIGHT",
                    "approach_steps": 1, "owner_position": [13, 70],
                    "species": 491, "outcome_name": "CAUGHT",
                    "outcome_value": 7, "natural_flute_producer": True,
                    "producer_owner_pc_hits": 1, "owner_pc_hits": 1,
                    "actual_walk_steps": 2, "direction_plus_a": True,
                    "choice_yes_battle": True, "bag_direction_a": True,
                    "party_count_before": 1, "party_count_after": 2,
                    "captured_species": 491,
                    "capture_preparation_valid": True,
                    "battle_runtime_initialized": True,
                    "battle_runtime_cleaned": True, "field_returned": True,
                    "master_ball_consumed": True,
                    "first_battle_callback": "0x08012345",
                    "battle_input_pulses": 4,
                    "save_via_start_menu": True,
                    "fresh_core_continue": True, "reentry_hidden": True,
                    "field_input_recovered": True,
                    "srm": srms[2], "ppm": ppms[2],
                },
                "hidden_after_each_terminal": True,
                "normal_save_count": 3, "fresh_continue_count": 3,
                "reentry_hidden_count": 3, "field_input_recovered": True,
                "srms": srms, "ppms": ppms,
                  "failed": 0, "untested": 0, "warnings": 0}
        result.update(cls._framebuffer_fields(directory, "snorlax"))
        return result

    @classmethod
    def _fly(cls, directory: Path) -> dict[str, object]:
        for name in ("fly_normal_menu-town-map.ppm",
                     "fly_normal_menu-final.ppm"):
            cls._write_artifact(directory, name, RUNNER.PPM_SIZE)
        result = {
            "schema_version": 3, "status": "PASS", "case": "fly_normal_menu",
            "preparation_only_host_writes": True,
            "direct_owner_or_script_calls": 0,
            "start_party_town_map_via_keys": True, "town_map_visible": True,
            "context_down_steps": 1, "sequence_steps": 5,
            "origin": "96/23", "destination": "96/4", "landing": [6, 6],
            "landing_overworld": True, "landing_script_released": True,
            "landing_controls_unlocked": True, "start_pressed": True,
            "start_menu_opened": True, "back_pressed": True,
            "field_input_recovered": True,
            "field_framebuffer_fnv1a64": "0000000000000001",
            "town_map_framebuffer_fnv1a64": "0000000000000002",
            "capture": {
                "message_state_address": "0x02000000",
                "string_address": "0x02000004",
                "printer_entry": "0x08000001",
                "printer_entry_preimage_hex": "00",
                "template_printer_entry": "0x08000003",
                "template_printer_entry_preimage_hex": "00",
                "execution": {"invalid_control_flow": False,
                              "first_invalid_pc": None, "cpsr": None, "lr": None},
                "active_frames": 0, "state_counts": [1, 0, 0, 0],
                "var_result": {},
                "framebuffer": {
                    "first_fnv1a64": "0000000000000001",
                    "last_fnv1a64": "0000000000000002",
                    "changed_frames": 2,
                    "maximum_baseline_pixel_difference": 100,
                },
                "messages": [], "printer_calls": [],
            },
            "failed": 0, "untested": 0, "warnings": 0,
        }
        result.update(cls._framebuffer_fields(directory, "fly"))
        artifact_hashes = result["framebuffer_artifact_fnv1a64"]
        result["framebuffer_stage_rgb_fnv1a64"] = {
            "origin": RUNNER._fnv1a64(b"unit-fly-origin-framebuffer"),
            "town_map": artifact_hashes["fly_normal_menu-town-map.ppm"],
            "landing": artifact_hashes["fly_normal_menu-final.ppm"],
        }
        return result

    def test_c_contains_continuous_real_input_lifecycles(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for token in ("el_interact_trash", "s61_walk_approach",
                      "el_cancel_ferry", "menu_cancel_seen",
                      "WORLD_KEY_B", "S61_CHOICE_YES",
                      "EL_FERRY_SPECIAL", "s61_throw_master_ball_with_keys",
                      "preparation_teleport_and_engine_var_fixture\\\":true",
                      "host_direct_memory_writes\\\":0",
                      "s61_normal_input_save(core)", "s61_open_fresh",
                      "s61_enter_party_menu", "route12-snorlax-caught",
                      "96U, 23U, 11U, 70U, WORLD_KEY_RIGHT, 1U, 15U",
                      "battle_struct_host_writes\\\":0",
                      "framebuffer_artifact_fnv1a64",
                      "framebuffer_stage_rgb_fnv1a64",
                      "captured_species", "battle_runtime_cleaned",
                      "direct_owner_or_script_calls\\\":0",
                      "\\\"failed\\\":0,\\\"untested\\\":0,\\\"warnings\\\":0"):
            self.assertIn(token, source)
        self.assertNotIn("write16(core, WORLD_SPECIAL_RESULT", source)

    def test_embedded_harness_only_renames_outer_main(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "embedded.c"
            identity = RUNNER._build_embedded(destination)
            transformed = destination.read_text(encoding="utf-8")
        original = (ROOT / RUNNER.EMBEDDED).read_text(encoding="utf-8")
        self.assertTrue(identity["outer_main_renamed"])
        self.assertEqual(transformed.replace(RUNNER._RENAMED, RUNNER._MAIN, 1),
                         original)

    def test_strict_compile_only_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = RUNNER.compile_runner(Path(temporary) / "runner")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["stdout_empty"])
        self.assertTrue(result["stderr_empty"])

    def test_vermilion_validator_rejects_self_report_and_mutated_ppm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._vermilion(directory)
            self.assertEqual(RUNNER.validate_vermilion(
                value, directory, self._roots())["status"], "PASS")
            bad = deepcopy(value)
            bad["untested"] = 1
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "zero PASS"):
                RUNNER.validate_vermilion(bad, directory, self._roots())
            (directory / "vermilion-open.ppm").write_bytes(b"P6\n")
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "size不一致"):
                RUNNER.validate_vermilion(value, directory, self._roots())

    def test_ferry_validator_requires_all_seven_owner_pc_and_full_srm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._ferry(directory)
            self.assertEqual(RUNNER.validate_ferry(
                value, directory, self._roots())["status"], "PASS")
            missing = deepcopy(value)
            missing["owners"] = missing["owners"][:-1]
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "件数"):
                RUNNER.validate_ferry(missing, directory, self._roots())
            no_pc = deepcopy(value)
            no_pc["owners"][0]["owner_pc_hits"] = 0
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "root/callback"):
                RUNNER.validate_ferry(no_pc, directory, self._roots())
            direct_write = deepcopy(value)
            direct_write["host_direct_memory_writes"] = 1
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "aggregate"):
                RUNNER.validate_ferry(direct_write, directory, self._roots())
            bad_readback = deepcopy(value)
            bad_readback["owners"][0]["pre_board_engine_var_readback"][
                "0x4071"] = 3
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "root/callback"):
                RUNNER.validate_ferry(bad_readback, directory, self._roots())
            (directory / value["owners"][0]["srm"]).write_bytes(
                bytes(RUNNER.SAVE_SIZE - 1))
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "size不一致"):
                RUNNER.validate_ferry(value, directory, self._roots())

    def test_ppm_gradient_substitution_is_rejected_by_c_result_join(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._fly(directory)
            name = "fly_normal_menu-town-map.ppm"
            gradient = bytes(index & 0xFF for index in range(240 * 160 * 3))
            (directory / name).write_bytes(b"P6\n240 160\n255\n" + gradient)
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "saved RGB FNV-1a64/C result"):
                RUNNER.validate_fly(value, directory)

    def test_snorlax_validator_requires_both_key_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._snorlax(directory)
            self.assertEqual(RUNNER.validate_snorlax(
                value, directory, self._roots())["status"], "PASS")
            bad = deepcopy(value)
            bad["outcomes"][1]["bag_direction_a"] = False
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "bag_direction_a"):
                RUNNER.validate_snorlax(bad, directory, self._roots())
            bad_species = deepcopy(value)
            bad_species["route12_capture_control"]["captured_species"] = 10
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "Route12 species491"):
                RUNNER.validate_snorlax(
                    bad_species, directory, self._roots(),
                )
            stale_coordinate = deepcopy(value)
            stale_coordinate["route12_capture_control"]["physical_start"] = [14, 72]
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "Route12 species491"):
                RUNNER.validate_snorlax(
                    stale_coordinate, directory, self._roots(),
                )
            host_write = deepcopy(value)
            host_write["capture_preparation"]["battle_struct_host_writes"] = 1
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "host直書き"):
                RUNNER.validate_snorlax(
                    host_write, directory, self._roots(),
                )

    def test_process_evidence_is_atomic_exact_and_semantically_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            names = RUNNER._evidence_names("snorlax")
            for name in names:
                (directory / name).write_bytes(b"stale")
            RUNNER._preclear_exact(directory, names, "unit evidence")
            self.assertTrue(all(not (directory / name).exists()
                                for name in names))
            result = {"schema_version": 1, "status": "PASS"}
            stdout = (json.dumps(result, separators=(",", ":")) + "\n").encode()
            evidence = RUNNER._retain_process_evidence(
                directory, "snorlax", stdout=stdout, stderr=b"", result=result,
            )
            self.assertTrue(evidence["stdout_result_matches_canonical"])
            self.assertTrue(evidence["stderr_empty"])
            roles = {row["role"] for row in evidence["artifacts"].values()}
            self.assertEqual(roles, {
                "raw_process_stdout", "raw_process_stderr",
                "canonical_case_result",
            })
            for row in evidence["artifacts"].values():
                self.assertTrue(row["stale_precleared"])
                self.assertTrue(row["atomic_retained"])
                self.assertEqual(Path(row["path"]).stat().st_size, row["size"])
            self.assertEqual((directory / names[1]).read_bytes(), b"")
            self.assertFalse(any(directory.glob(".*.retain.tmp")))

    def test_fly_validator_rejects_invalid_control_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self._fly(directory)
            self.assertEqual(RUNNER.validate_fly(value, directory)["status"],
                             "PASS")
            bad = deepcopy(value)
            bad["capture"]["execution"] = {
                "invalid_control_flow": True,
                "first_invalid_pc": "0x02000000",
                "cpsr": "0x0000003F", "lr": "0x02000001",
            }
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "engine Fly"):
                RUNNER.validate_fly(bad, directory)

    def test_process_evidence_rejects_stdout_canonical_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "stdout result/canonical"):
                RUNNER._retain_process_evidence(
                    directory, "fly", stdout=b'{"status":"PASS"}\n',
                    stderr=b"", result={"status": "FAIL"},
                )

    def test_runs_is_exactly_two(self) -> None:
        RUNNER._require_exact_runs(2)
        for value in (0, 1, 3, True):
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "exact 2"):
                RUNNER._require_exact_runs(value)

    def test_orchestrator_runs_each_case_in_two_independent_directories(self) -> None:
        process_calls: list[tuple[str, Path]] = []

        def fake_process(command: list[str], **_kwargs: object) -> SimpleNamespace:
            case = command[3]
            directory = Path(command[2])
            process_calls.append((case, directory))
            for name in RUNNER._CASE_PRODUCT_ARTIFACTS[case]:
                self._write_artifact(
                    directory, name,
                    RUNNER.SAVE_SIZE if name.endswith(".srm")
                    else RUNNER.PPM_SIZE,
                )
            result = {"case": case, "schema_version": 1, "status": "PASS"}
            stdout = (json.dumps(result, separators=(",", ":")) + "\n").encode()
            return SimpleNamespace(returncode=0, stdout=stdout, stderr=b"")

        def fake_validate(case: str, value: object, directory: Path,
                          _roots: object) -> dict[str, object]:
            artifacts = {}
            for name in RUNNER._CASE_PRODUCT_ARTIFACTS[case]:
                is_srm = name.endswith(".srm")
                expected_rgb = None if is_srm else RUNNER._ppm_rgb_fnv1a64(
                    (directory / name).read_bytes(), "mock product",
                )
                artifacts[name] = RUNNER._artifact(
                    directory, name,
                    RUNNER.SAVE_SIZE if is_srm else RUNNER.PPM_SIZE,
                    "mock product",
                    role="external_srm_full_readback" if is_srm
                    else "framebuffer_ppm",
                    case=case,
                    expected_rgb_fnv1a64=expected_rgb,
                    framebuffer_role=None if is_srm
                    else RUNNER._CASE_FRAMEBUFFER_ROLES[case][name],
                )
            ppms = [name for name in artifacts if name.endswith(".ppm")]
            return {
                "status": "PASS", "result": value,
                "artifacts": artifacts,
                "external_srm_semantic_readback": [],
                "framebuffer_artifact_rgb_readback":
                    RUNNER._framebuffer_readback(artifacts, ppms, "mock"),
            }

        identity = {"rom": "/fake/stage61.gba", "root_exact": {}}
        with tempfile.TemporaryDirectory() as temporary, \
                mock.patch.object(RUNNER, "read_identity", return_value=identity), \
                mock.patch.object(RUNNER, "compile_runner",
                                  return_value={"status": "PASS"}), \
                mock.patch.object(RUNNER, "_environment", return_value={}), \
                mock.patch.object(RUNNER, "validate_result",
                                  side_effect=fake_validate), \
                mock.patch.object(RUNNER.subprocess, "run",
                                  side_effect=fake_process):
            report = RUNNER.run(
                Path("unused.gba"), Path("unused.json"), None,
                Path(temporary) / "work", runs=2,
            )
        self.assertEqual(len(process_calls), 8)
        self.assertEqual(len({directory for _case, directory in process_calls}), 8)
        self.assertEqual(report["runs_per_case"], 2)
        self.assertEqual(report["independent_process_count"], 8)
        self.assertEqual(report["coverage"]["retained_artifact_count"], 76)
        self.assertEqual(report["coverage"]["full_srm_sha256_count"], 22)
        self.assertEqual(report["coverage"]["ppm_sha256_count"], 30)
        self.assertEqual(report["coverage"]["ppm_rgb_fnv1a64_join_count"], 30)
        self.assertTrue(all(case["normalized_hashes_match"]
                            for case in report["cases"].values()))

    def test_work_directory_must_be_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "stale").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(RUNNER.Stage61EventLifecycleError,
                                        "空または未作成"):
                RUNNER._prepare_work(directory)


if __name__ == "__main__":
    unittest.main()
