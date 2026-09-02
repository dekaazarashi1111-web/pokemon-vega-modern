from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_stage61_save_ui_cow_e2e.py"
SOURCE_PATH = ROOT / "tools/mgba_stage61_save_ui_cow_e2e.c"

SPEC = importlib.util.spec_from_file_location(
    "stage61_save_ui_cow_e2e", RUNNER_PATH,
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

_FRAMEBUFFER = bytes(range(256)) * (RUNNER.FRAMEBUFFER_BYTE_SIZE // 256)
_PPM_PIXELS = b"".join(
    _FRAMEBUFFER[index:index + 3]
    for index in range(0, len(_FRAMEBUFFER), 4)
)


class Stage61SaveUiCowE2eTests(unittest.TestCase):
    FRAMEBUFFER = _FRAMEBUFFER
    PPM_PIXELS = _PPM_PIXELS
    FAULT_CHANGED_BYTES = 4097

    @staticmethod
    def _fault(before: bytes) -> bytes:
        fault = bytearray(before)
        for index in range(Stage61SaveUiCowE2eTests.FAULT_CHANGED_BYTES):
            fault[index] ^= 0x5A
        return bytes(fault)

    @staticmethod
    def _result(before: bytes, after: bytes) -> dict[str, object]:
        fault = Stage61SaveUiCowE2eTests._fault(before)
        return {
            "schema_version": RUNNER.RESULT_SCHEMA_VERSION,
            "status": "PASS",
            "case": "save_ui_cow_fault_retry_continue",
            "preparation_only_host_writes": True,
            "direct_owner_or_script_calls": 0,
            "natural_input": {
                "start_pressed": True,
                "save_action_selected": True,
                "confirmation_pulses": 2,
                "host_direct_save_callback": False,
            },
            "engine_trace": {
                "save_serialized_game": "0x0804BAB8",
                "save_serialized_game_hits_before_fault": 1,
                "update_save_addresses": "0x080DB1BC",
                "update_save_addresses_hits_before_fault": 1,
                "handle_saving_data_hits_before_fault": 1,
                "save_data_buffer": "0x020399B0",
                "save_data_buffer_stable": True,
            },
            "fault": {
                "callback": "0x081C2E90",
                "real_flash_callback_executed": True,
                "status_injected_at_real_return": True,
                "fault_callback_hits": 1,
                "phase": "STOCK",
                "normal_save_type": 0,
                "physical_sector": 17,
                "partial_flash_side_effect": True,
                "changed_bytes": Stage61SaveUiCowE2eTests.FAULT_CHANGED_BYTES,
                "damaged_mask_before_wipe": 1,
                "protected_slot": 0,
                "protected_counter": 10,
                "protected_generation_exact": True,
                "damaged_generation_incomplete": True,
            },
            "save_failed_screen": {
                "real_owner_observed": True,
                "state5_observed": True,
                "framebuffer_hash": RUNNER._framebuffer_fnv64(
                    Stage61SaveUiCowE2eTests.FRAMEBUFFER,
                ),
                "framebuffer_raw_path": "save-ui-cow-save-failed.rgba",
                "artifact_path": "save-ui-cow-save-failed.ppm",
                "artifact_pixel_fnv64": RUNNER._fnv64(
                    Stage61SaveUiCowE2eTests.PPM_PIXELS,
                ),
                "owner_state_trace": [
                    {
                        "sequence": 0,
                        "pc": "0x080F6280",
                        "state_address": "0x0203AAC8",
                        "state": 5,
                        "active_address": "0x03005480",
                        "active": 0x020399A0,
                    },
                    {
                        "sequence": 1,
                        "pc": "0x080F62B0",
                        "state_address": "0x0203AAC8",
                        "state": 6,
                        "active_address": "0x03005480",
                        "active": 0x020399A0,
                    },
                ],
                "damaged_generation_wiped": True,
                "retry_completed": True,
                "attempt_status": 1,
                "state6_success_observed": True,
                "retry_acknowledged_with_a": True,
                "field_input_recovered": True,
            },
            "explicit_retry": {
                "start_menu_save_with_keys": True,
                "counter_before": 11,
                "counter_after": 12,
                "full_generation_complete": True,
            },
            "hard_restart": {
                "old_core_closed": True,
                "fresh_core_opened": True,
                "title_continue": True,
                "counter": 12,
                "field_input_recovered": True,
                "location": {
                    "map_group": 96,
                    "map_number": 5,
                    "x": 20,
                    "y": 20,
                    "warp_id": 0xFF,
                },
                "input_liveness": {
                    "start_pressed": True,
                    "start_menu_opened": True,
                    "menu_callback_observed": "0x0806EA75",
                    "back_pressed": True,
                    "callback_ordered": True,
                    "map_preserved": True,
                    "position_preserved": True,
                    "field_terminal": True,
                    "field_input_recovered": True,
                    "location_before": {
                        "map_group": 96,
                        "map_number": 5,
                        "x": 20,
                        "y": 20,
                        "warp_id": 0xFF,
                    },
                    "location_after": {
                        "map_group": 96,
                        "map_number": 5,
                        "x": 20,
                        "y": 20,
                        "warp_id": 0xFF,
                    },
                },
                "framebuffer_hash": RUNNER._framebuffer_fnv64(
                    Stage61SaveUiCowE2eTests.FRAMEBUFFER,
                ),
                "framebuffer_raw_path": (
                    "save-ui-cow-hard-continue.rgba"
                ),
                "artifact_path": "save-ui-cow-hard-continue.ppm",
                "artifact_pixel_fnv64": RUNNER._fnv64(
                    Stage61SaveUiCowE2eTests.PPM_PIXELS,
                ),
                "canaries_restored": True,
                "canary_count": len(RUNNER._FRESH_CANARIES),
                "canaries": [
                    {**item, "observed_value": item["expected_value"]}
                    for item in RUNNER._FRESH_CANARIES
                ],
            },
            "srm": {
                "size": RUNNER.SAVE_SIZE,
                "before_path": "save-ui-cow-before.srm",
                "fault_path": "save-ui-cow-fault.srm",
                "after_path": "save-ui-cow-after.srm",
                "retained_path": "save-ui-cow-retained.srm",
                "before_fnv64": RUNNER._fnv64(before),
                "fault_fnv64": RUNNER._fnv64(fault),
                "after_fnv64": RUNNER._fnv64(after),
            },
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    @staticmethod
    def _write_snapshots(directory: Path, before: bytes, after: bytes) -> None:
        (directory / "save-ui-cow-before.srm").write_bytes(before)
        (directory / "save-ui-cow-fault.srm").write_bytes(
            Stage61SaveUiCowE2eTests._fault(before),
        )
        (directory / "save-ui-cow-after.srm").write_bytes(after)
        (directory / "save-ui-cow-retained.srm").write_bytes(after)
        (directory / "save-ui-cow-save-failed.ppm").write_bytes(
            RUNNER.PPM_HEADER + Stage61SaveUiCowE2eTests.PPM_PIXELS,
        )
        (directory / "save-ui-cow-save-failed.rgba").write_bytes(
            Stage61SaveUiCowE2eTests.FRAMEBUFFER,
        )
        (directory / "save-ui-cow-hard-continue.ppm").write_bytes(
            RUNNER.PPM_HEADER + Stage61SaveUiCowE2eTests.PPM_PIXELS,
        )
        (directory / "save-ui-cow-hard-continue.rgba").write_bytes(
            Stage61SaveUiCowE2eTests.FRAMEBUFFER,
        )

    def test_c_source_requires_real_keys_owner_states_and_fresh_core(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for token in (
            "WORLD_KEY_START", "WORLD_START_MENU_SAVE_ACTION",
            "sui_step_frames_to_fault_callback",
            "SUI_STOCK_ERASE_FLASH_SECTOR",
            "S61_HANDLE_SAVING_DATA_SYMBOL",
            "s61_inject_status_at_callback_return",
            "SUI_SAVE_FAILED_STATE = 0x0203AAC8U",
            "SUI_SAVE_FAILED_ACTIVE = 0x03005480U",
            "SUI_SAVE_FAILED_WIPE_STATE = 5U",
            "sui_capture_save_failed_owner",
            "save-ui-cow-save-failed.rgba",
            "\\\"owner_state_trace\\\"",
            "\\\"canary_count\\\":4",
            "SUI_SAVE_SERIALIZED_GAME = 0x0804BAB8U",
            "SUI_UPDATE_SAVE_ADDRESSES = 0x080DB1BCU",
            "s61_normal_input_save(core)",
            "bootstrap_close_core(core)",
            "s61_open_fresh(\n        rom_path, retained_path, &fixture)",
            "\\\"host_direct_save_callback\\\":false",
            "sui_prove_fresh_input_liveness(fresh, &fixture)",
            "s61_field_roundtrip(",
            "\\\"input_liveness\\\"",
        ):
            self.assertIn(token, source)

    def test_generated_embedded_harness_renames_only_outer_main(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "embedded.c"
            identity = RUNNER._build_embedded_harness(destination)
            transformed = destination.read_text(encoding="utf-8")
        original = (ROOT / RUNNER.EMBEDDED_SOURCE).read_text(encoding="utf-8")
        self.assertTrue(identity["main_renamed"])
        self.assertNotIn(RUNNER._EMBEDDED_MAIN, transformed)
        self.assertIn(RUNNER._RENAMED_MAIN, transformed)
        self.assertEqual(
            transformed.replace(RUNNER._RENAMED_MAIN, RUNNER._EMBEDDED_MAIN, 1),
            original,
        )

    def test_strict_compile_only_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = RUNNER._compile(Path(temporary) / "runner")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["stdout_empty"])
        self.assertTrue(result["stderr_empty"])

    def test_validator_re_reads_all_131072_byte_snapshots_and_hashes(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([0xA5]) * RUNNER.SAVE_SIZE
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            normalized = RUNNER.validate_c_result(
                self._result(before, after), work,
            )
        self.assertEqual(
            normalized["srm"]["before"]["sha256"], RUNNER._sha256(before),
        )
        self.assertEqual(
            normalized["srm"]["fault"]["changed_bytes_from_before"],
            self.FAULT_CHANGED_BYTES,
        )
        self.assertEqual(
            normalized["srm"]["after"]["sha256"], RUNNER._sha256(after),
        )
        self.assertEqual(
            normalized["srm"]["retained"]["sha256"], RUNNER._sha256(after),
        )
        self.assertTrue(normalized["srm"]["before_after_different"])
        self.assertTrue(normalized["srm"]["after_retained_exact"])

    def test_validator_rejects_host_direct_callback_claim(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        result["natural_input"]["host_direct_save_callback"] = True
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "direct-call",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_self_report_when_retained_bytes_differ(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = deepcopy(self._result(before, after))
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            (work / "save-ui-cow-retained.srm").write_bytes(
                bytes([2]) * RUNNER.SAVE_SIZE,
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "retained SRM",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_missing_real_save_failed_observation(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        result["save_failed_screen"]["state5_observed"] = False
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "state5_observed",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_save_failed_artifact_mismatch(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            artifact = work / "save-ui-cow-save-failed.ppm"
            raw = bytearray(artifact.read_bytes())
            raw[-1] ^= 0xFF
            artifact.write_bytes(raw)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "PPM/raw framebuffer",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_arbitrary_ppm_with_recomputed_hash(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        arbitrary_pixels = bytes([0xA5]) * RUNNER.PPM_PIXEL_SIZE
        result["save_failed_screen"]["artifact_pixel_fnv64"] = \
            RUNNER._fnv64(arbitrary_pixels)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            (work / "save-ui-cow-save-failed.ppm").write_bytes(
                RUNNER.PPM_HEADER + arbitrary_pixels,
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "PPM/raw framebuffer",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_framebuffer_hash_tamper(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        result["save_failed_screen"]["framebuffer_hash"] = \
            "0000000000000000"
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "artifact readback",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_canary_observed_and_expected_tamper(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        for field in ("observed_value", "expected_value"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() \
                    as temporary:
                result = self._result(before, after)
                result["hard_restart"]["canaries"][0][field] = 0
                work = Path(temporary)
                self._write_snapshots(work, before, after)
                with self.assertRaisesRegex(
                    RUNNER.Stage61SaveUiCowError, "canary",
                ):
                    RUNNER.validate_c_result(result, work)

    def test_validator_rejects_canary_deletion(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        del result["hard_restart"]["canaries"][-1]
        result["hard_restart"]["canary_count"] -= 1
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "canary件数",
            ):
                RUNNER.validate_c_result(result, work)

    def test_validator_rejects_false_hard_continue_input_liveness(self) \
            -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        fields = (
            "start_pressed", "start_menu_opened", "back_pressed",
            "callback_ordered", "map_preserved", "position_preserved",
            "field_terminal", "field_input_recovered",
        )
        for field in fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() \
                    as temporary:
                result = self._result(before, after)
                result["hard_restart"]["input_liveness"][field] = False
                work = Path(temporary)
                self._write_snapshots(work, before, after)
                with self.assertRaisesRegex(
                    RUNNER.Stage61SaveUiCowError,
                    rf"input_liveness\.{field}",
                ):
                    RUNNER.validate_c_result(result, work)

    def test_validator_rejects_hard_continue_input_location_drift(self) \
            -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        for phase, key in (
            ("location_before", "map_number"),
            ("location_after", "x"),
        ):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() \
                    as temporary:
                result = self._result(before, after)
                result["hard_restart"]["input_liveness"][phase][key] += 1
                work = Path(temporary)
                self._write_snapshots(work, before, after)
                with self.assertRaisesRegex(
                    RUNNER.Stage61SaveUiCowError,
                    "実入力前後のmap/position",
                ):
                    RUNNER.validate_c_result(result, work)

    def test_validator_rejects_input_liveness_schema_or_callback_tamper(
        self,
    ) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        mutations = (
            lambda result: result["hard_restart"]["input_liveness"].__setitem__(
                "unexpected", True,
            ),
            lambda result: result["hard_restart"]["input_liveness"].__setitem__(
                "menu_callback_observed", "0x08000001",
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() \
                    as temporary:
                result = self._result(before, after)
                mutate(result)
                work = Path(temporary)
                self._write_snapshots(work, before, after)
                with self.assertRaises(RUNNER.Stage61SaveUiCowError):
                    RUNNER.validate_c_result(result, work)

    def test_process_evidence_rejects_stdout_result_substitution(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        actual = self._result(before, after)
        substituted = deepcopy(actual)
        substituted["direct_owner_or_script_calls"] = 1
        stdout = (json.dumps(actual, separators=(",", ":")) + "\n").encode()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "stdout result/canonical",
            ):
                RUNNER._retain_process_evidence(
                    Path(temporary), stdout=stdout, stderr=b"",
                    result=substituted,
                )

    def test_minimal_stdout_cannot_satisfy_exact_c_schema(self) -> None:
        minimal = {
            "schema_version": RUNNER.RESULT_SCHEMA_VERSION,
            "status": "PASS",
            "case": RUNNER.CASE,
        }
        stdout = (json.dumps(minimal, separators=(",", ":")) + "\n").encode()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            evidence = RUNNER._retain_process_evidence(
                work, stdout=stdout, stderr=b"", result=minimal,
            )
            self.assertTrue(evidence["stdout_result_matches_canonical"])
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "root keys不一致",
            ):
                RUNNER.validate_c_result(minimal, work)

    def test_stale_exact_artifacts_are_precleared_before_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root / "run-1" / RUNNER.CASE
            case.mkdir(parents=True)
            stale = case / RUNNER._PROCESS_ARTIFACTS[0]
            stale.write_bytes(b"stale")
            work = RUNNER._prepare_work(root)
            run_work, removed = RUNNER._prepare_run_work(work, 1)
            self.assertEqual(removed, 1)
            self.assertEqual(list(run_work.iterdir()), [])

    def test_unknown_stale_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root / "run-1" / RUNNER.CASE
            case.mkdir(parents=True)
            (case / "unexpected.bin").write_bytes(b"stale")
            work = RUNNER._prepare_work(root)
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "未知entry",
            ):
                RUNNER._prepare_run_work(work, 1)

    def test_replay_gate_rejects_semantic_difference_even_with_same_hash(self) -> None:
        records = [
            {"normalized_sha256": "a" * 64},
            {"normalized_sha256": "a" * 64},
        ]
        with self.assertRaisesRegex(
            RUNNER.Stage61SaveUiCowError, "normalized hash不一致",
        ):
            RUNNER._require_replay_match(records, [{"run": 1}, {"run": 2}])

    def test_hard_continue_ppm_self_report_cannot_replace_raw_framebuffer(
        self,
    ) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        arbitrary_pixels = bytes(
            index & 0xFF for index in range(RUNNER.PPM_PIXEL_SIZE)
        )
        result["hard_restart"]["artifact_pixel_fnv64"] = RUNNER._fnv64(
            arbitrary_pixels,
        )
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            (work / "save-ui-cow-hard-continue.ppm").write_bytes(
                RUNNER.PPM_HEADER + arbitrary_pixels,
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "PPM/raw framebuffer",
            ):
                RUNNER.validate_c_result(result, work)

    def test_product_artifact_set_and_hashes_are_exact(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            artifacts = RUNNER._product_artifacts(work)
        self.assertEqual(set(artifacts), set(RUNNER._PRODUCT_ARTIFACTS))
        self.assertEqual(len(artifacts), 8)
        for descriptor in artifacts.values():
            self.assertRegex(descriptor["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(descriptor["atomic_retained"])

    def test_artifact_leaf_closure_rejects_extra_self_report(self) -> None:
        before = bytes(RUNNER.SAVE_SIZE)
        after = bytes([1]) * RUNNER.SAVE_SIZE
        result = self._result(before, after)
        stdout = (json.dumps(result, separators=(",", ":")) + "\n").encode()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self._write_snapshots(work, before, after)
            artifacts = RUNNER._product_artifacts(work)
            evidence = RUNNER._retain_process_evidence(
                work, stdout=stdout, stderr=b"", result=result,
            )
            artifacts.update(evidence["artifacts"])
            RUNNER._validate_run_artifact_closure(work, artifacts)
            artifacts[RUNNER._PRODUCT_ARTIFACTS[0]]["self_report"] = True
            with self.assertRaisesRegex(
                RUNNER.Stage61SaveUiCowError, "leaf schema",
            ):
                RUNNER._validate_run_artifact_closure(work, artifacts)


if __name__ == "__main__":
    unittest.main()
