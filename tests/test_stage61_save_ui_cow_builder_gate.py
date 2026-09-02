from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from scripts import build_stage61_display_npc_event_audit as builder
from scripts import run_stage61_save_ui_cow_e2e as producer
from tests.stage61_save_fixture import build_stage61_save


ROOT = Path(__file__).resolve().parents[1]
CASE = producer.CASE
_SAVE_FAILED_RGBA = bytes(range(256)) * (
    producer.FRAMEBUFFER_BYTE_SIZE // 256
)
_HARD_CONTINUE_RGBA = bytes(reversed(range(256))) * (
    producer.FRAMEBUFFER_BYTE_SIZE // 256
)


class Stage61SaveUiCowBuilderGateTests(unittest.TestCase):
    """Final builder must distrust the producer's PASS and re-read bytes.

    The fixture deliberately has the same shape as the runtime report emitted
    by ``run_stage61_save_ui_cow_e2e.py``: two independent OS-process records,
    eleven retained leaves per run, and a raw C schema-v2 result.  Several
    negative cases remain internally consistent enough to pass the producer's
    result validator; only independent Flash/position/COW reconstruction in
    the final builder can reject them.
    """

    SAVE_SIZE = producer.SAVE_SIZE
    SECTOR_SIZE = 0x1000
    SLOT_SECTORS = 14
    PROTECTED_SLOT = 0
    PROTECTED_COUNTER = 10
    BACKUP_COUNTER = 9
    RETRY_COUNTER = 11
    FINAL_COUNTER = 12
    FAULT_PHYSICAL_SECTOR = 17
    EXPECTED_LOCATION = {
        "map_group": 96,
        "map_number": 5,
        "x": 20,
        "y": 20,
        "warp_id": 0xFF,
    }
    FINAL_FLAGS = {0x18B4: True}
    FINAL_VARS = {0x5170: 0x61A5}
    FINAL_LAST_BALL = 3
    FINAL_COINS = 0x00054321

    @staticmethod
    def _ppm_from_rgba(framebuffer: bytes) -> bytes:
        pixels = b"".join(
            framebuffer[index:index + 3]
            for index in range(0, len(framebuffer), 4)
        )
        return producer.PPM_HEADER + pixels

    @classmethod
    def _generation(
        cls, *, counter: int, first_sector: int,
        x: int = 20, y: int = 20, warp_id: int = 0xFF,
        canaries: bool,
    ) -> bytes:
        return build_stage61_save(
            map_group=96,
            map_number=5,
            x=x,
            y=y,
            warp_id=warp_id,
            flags=cls.FINAL_FLAGS if canaries else {},
            variables=cls.FINAL_VARS if canaries else {},
            counter=counter,
            first_sector=first_sector,
            marker=counter,
            last_used_ball=cls.FINAL_LAST_BALL if canaries else 0,
            coins=cls.FINAL_COINS if canaries else 0,
        )

    @classmethod
    def _merge_generations(cls, even: bytes, odd: bytes) -> bytes:
        if len(even) != cls.SAVE_SIZE or len(odd) != cls.SAVE_SIZE:
            raise AssertionError("synthetic Flash size drift")
        split = cls.SLOT_SECTORS * cls.SECTOR_SIZE
        merged = bytearray(b"\xFF" * cls.SAVE_SIZE)
        merged[:split] = even[:split]
        merged[split:2 * split] = odd[split:2 * split]
        return bytes(merged)

    @classmethod
    def _save_images(
        cls, *, x: int = 20, y: int = 20, warp_id: int = 0xFF,
        final_canaries: bool = True,
    ) -> dict[str, bytes]:
        before = cls._merge_generations(
            cls._generation(
                counter=cls.PROTECTED_COUNTER, first_sector=3,
                canaries=False,
            ),
            cls._generation(
                counter=cls.BACKUP_COUNTER, first_sector=4,
                canaries=False,
            ),
        )
        fault = bytearray(before)
        fault_offset = cls.FAULT_PHYSICAL_SECTOR * cls.SECTOR_SIZE
        # One real target-bank payload byte changed without its checksum.  The
        # protected complete generation remains byte exact while the target
        # generation becomes incomplete, matching the COW fault invariant.
        fault[fault_offset] ^= 0x5A
        after = cls._merge_generations(
            cls._generation(
                counter=cls.FINAL_COUNTER, first_sector=5,
                x=x, y=y, warp_id=warp_id, canaries=final_canaries,
            ),
            cls._generation(
                counter=cls.RETRY_COUNTER, first_sector=6,
                x=x, y=y, warp_id=warp_id, canaries=final_canaries,
            ),
        )
        return {
            "save-ui-cow-before.srm": before,
            "save-ui-cow-fault.srm": bytes(fault),
            "save-ui-cow-after.srm": after,
            "save-ui-cow-retained.srm": after,
        }

    @classmethod
    def _raw_result(cls, images: Mapping[str, bytes]) -> dict[str, Any]:
        before = images["save-ui-cow-before.srm"]
        fault = images["save-ui-cow-fault.srm"]
        after = images["save-ui-cow-after.srm"]
        changed = sum(
            left != right
            for left, right in zip(before, fault, strict=True)
        )
        failed_pixels = cls._ppm_from_rgba(
            _SAVE_FAILED_RGBA,
        )[len(producer.PPM_HEADER):]
        continue_pixels = cls._ppm_from_rgba(
            _HARD_CONTINUE_RGBA,
        )[len(producer.PPM_HEADER):]
        return {
            "schema_version": producer.RESULT_SCHEMA_VERSION,
            "status": "PASS",
            "case": CASE,
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
                "partial_flash_side_effect": True,
                "changed_bytes": changed,
                "phase": "NORMAL_COW",
                "normal_save_type": 0,
                "physical_sector": cls.FAULT_PHYSICAL_SECTOR,
                "damaged_mask_before_wipe": (
                    1 << cls.FAULT_PHYSICAL_SECTOR
                ),
                "protected_slot": cls.PROTECTED_SLOT,
                "protected_counter": cls.PROTECTED_COUNTER,
                "protected_generation_exact": True,
                "damaged_generation_incomplete": True,
            },
            "save_failed_screen": {
                "real_owner_observed": True,
                "state5_observed": True,
                "framebuffer_hash": producer._framebuffer_fnv64(
                    _SAVE_FAILED_RGBA,
                ),
                "framebuffer_raw_path": (
                    "save-ui-cow-save-failed.rgba"
                ),
                "artifact_path": "save-ui-cow-save-failed.ppm",
                "artifact_pixel_fnv64": producer._fnv64(failed_pixels),
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
                "counter_before": cls.RETRY_COUNTER,
                "counter_after": cls.FINAL_COUNTER,
                "full_generation_complete": True,
            },
            "hard_restart": {
                "old_core_closed": True,
                "fresh_core_opened": True,
                "title_continue": True,
                "counter": cls.FINAL_COUNTER,
                "field_input_recovered": True,
                "canaries_restored": True,
                "canary_count": len(producer._FRESH_CANARIES),
                "canaries": [
                    {**row, "observed_value": row["expected_value"]}
                    for row in producer._FRESH_CANARIES
                ],
                "location": dict(cls.EXPECTED_LOCATION),
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
                    "location_before": dict(cls.EXPECTED_LOCATION),
                    "location_after": dict(cls.EXPECTED_LOCATION),
                },
                "framebuffer_hash": producer._framebuffer_fnv64(
                    _HARD_CONTINUE_RGBA,
                ),
                "framebuffer_raw_path": (
                    "save-ui-cow-hard-continue.rgba"
                ),
                "artifact_path": "save-ui-cow-hard-continue.ppm",
                "artifact_pixel_fnv64": producer._fnv64(
                    continue_pixels,
                ),
            },
            "srm": {
                "size": cls.SAVE_SIZE,
                "before_path": "save-ui-cow-before.srm",
                "fault_path": "save-ui-cow-fault.srm",
                "after_path": "save-ui-cow-after.srm",
                "retained_path": "save-ui-cow-retained.srm",
                "before_fnv64": producer._fnv64(before),
                "fault_fnv64": producer._fnv64(fault),
                "after_fnv64": producer._fnv64(after),
            },
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    @classmethod
    def _write_product_artifacts(
        cls, work: Path, images: Mapping[str, bytes],
    ) -> None:
        for name, raw in images.items():
            (work / name).write_bytes(raw)
        (work / "save-ui-cow-save-failed.rgba").write_bytes(
            _SAVE_FAILED_RGBA,
        )
        (work / "save-ui-cow-save-failed.ppm").write_bytes(
            cls._ppm_from_rgba(_SAVE_FAILED_RGBA),
        )
        (work / "save-ui-cow-hard-continue.rgba").write_bytes(
            _HARD_CONTINUE_RGBA,
        )
        (work / "save-ui-cow-hard-continue.ppm").write_bytes(
            cls._ppm_from_rgba(_HARD_CONTINUE_RGBA),
        )

    @classmethod
    def _run_record(
        cls, work: Path, run_index: int, images: Mapping[str, bytes],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        work.mkdir(parents=True)
        cls._write_product_artifacts(work, images)
        result = cls._raw_result(images)
        # The fixture is producer-valid before it is handed to the independent
        # final builder.  This keeps test failures about the consumer gate.
        producer.validate_c_result(result, work)
        stdout = (
            json.dumps(
                result, ensure_ascii=False, separators=(",", ":"),
            ) + "\n"
        ).encode("utf-8")
        process = producer._retain_process_evidence(
            work, stdout=stdout, stderr=b"", result=result,
        )
        artifacts = producer._product_artifacts(work)
        artifacts.update(process["artifacts"])
        producer._validate_run_artifact_closure(work, artifacts)
        process_row = {
            key: value for key, value in process.items()
            if key != "artifacts"
        }
        normalized = producer._normalized_run_payload(
            result, artifacts, process_row,
        )
        normalized_sha256 = producer._sha256(
            producer._stable(normalized).encode("utf-8"),
        )
        return {
            "schema_version": 1,
            "status": "PASS",
            "run_index": run_index,
            "independent_os_process": True,
            "empty_case_directory_at_start": True,
            "stale_artifacts_precleared": 0,
            "work_directory": str(work.resolve()),
            "normalized_sha256": normalized_sha256,
            "result": result,
            "artifacts": artifacts,
            "process_evidence": process_row,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }, normalized

    @staticmethod
    def _compile_identity() -> dict[str, Any]:
        runner_raw = (
            ROOT / builder.MGBA_SAVE_UI_COW_RUNNER_SOURCE
        ).read_bytes()
        embedded_raw = (ROOT / builder.MGBA_RUNNER_SOURCE).read_bytes()
        embedded_text = embedded_raw.decode("utf-8")
        original_main = "\nint main(int argc, char **argv)\n{"
        renamed_main = (
            "\nint s61_embedded_display_npc_event_main"
            "(int argc, char **argv)\n{"
        )
        return {
            "status": "PASS",
            "source": str(builder.MGBA_SAVE_UI_COW_RUNNER_SOURCE),
            "source_sha256": builder._sha(runner_raw),
            "embedded_harness": {
                "source": str(builder.MGBA_RUNNER_SOURCE),
                "source_sha256": builder._sha(embedded_raw),
                "transformed_sha256": builder._sha(
                    embedded_text.replace(
                        original_main, renamed_main, 1,
                    ).encode("utf-8")
                ),
                "main_renamed": True,
                "other_bytes_unchanged": True,
            },
            "command": (
                "cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic "
                "-I<tools> -DS61_SAVE_UI_EMBEDDED_HARNESS=<generated> "
                "<source> -o <runner> -lmgba"
            ),
            "stdout_empty": True,
            "stderr_empty": True,
        }

    @classmethod
    def _fixture(
        cls, root: Path,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        images = cls._save_images()
        work = root / "runtime"
        runs: list[dict[str, Any]] = []
        normalized: list[dict[str, Any]] = []
        for run_index in (1, 2):
            record, normalized_row = cls._run_record(
                work / f"run-{run_index}" / CASE,
                run_index,
                images,
            )
            runs.append(record)
            normalized.append(normalized_row)
        if normalized[0] != normalized[1]:
            raise AssertionError("save UI COW fixture replay drift")

        rom_path = root / "stage61.gba"
        with rom_path.open("wb") as handle:
            handle.truncate(builder.ROM_SIZE)
        rom_raw = rom_path.read_bytes()
        metadata_path = root / "stage61.json"
        metadata_raw = b'{"schema_version":1,"stage":61}\n'
        metadata_path.write_bytes(metadata_raw)
        rom_sha256 = builder._sha(rom_raw)
        metadata_sha256 = builder._sha(metadata_raw)
        orchestrator_raw = (
            ROOT / builder.MGBA_SAVE_UI_COW_ORCHESTRATOR_SOURCE
        ).read_bytes()

        root_artifacts: dict[str, Any] = {}
        for run in runs:
            for name, descriptor in run["artifacts"].items():
                root_artifacts[
                    f"run-{run['run_index']}/{CASE}/{name}"
                ] = deepcopy(descriptor)
        document: dict[str, Any] = {
            "schema_version": producer.REPORT_SCHEMA_VERSION,
            "task": builder.TASK,
            "stage": builder.STAGE,
            "status": "PASS",
            "case": "stage61_save_ui_cow_e2e",
            "orchestrator": {
                "source": str(
                    builder.MGBA_SAVE_UI_COW_ORCHESTRATOR_SOURCE
                ),
                "source_sha256": builder._sha(orchestrator_raw),
            },
            "identity": {
                "rom": str(rom_path.resolve()),
                "rom_size": len(rom_raw),
                "rom_sha256": rom_sha256,
                "metadata": str(metadata_path.resolve()),
                "metadata_sha256": metadata_sha256,
                "cow_runtime_symbol": "Stage61State_HandleSavingData",
                "normal_save_copy_on_write": True,
                "handle_saving_data": 0x09001001,
                "save_failed_retry_caller": "0x080F64C4",
            },
            "compile": cls._compile_identity(),
            "runs_per_case": 2,
            "independent_process_count": 2,
            "normalized_sha256": runs[0]["normalized_sha256"],
            "normalized_hashes_match": True,
            "runs": runs,
            "coverage": {
                "start_to_save_real_keys": True,
                "host_direct_save_callback_cannot_pass": True,
                "real_flash_callback_fault": True,
                "real_save_failed_screen": True,
                "save_failed_ppm_raw_framebuffer_join": True,
                "damaged_generation_wipe_and_retry": True,
                "explicit_start_menu_retry": True,
                "hard_fresh_continue": True,
                "hard_fresh_continue_location": "96/5@20,20",
                "retained_srm_exact": True,
                "each_case_two_independent_os_processes": True,
                "normalized_hash_match_per_case": True,
                "full_srm_sha256_count": 8,
                "ppm_sha256_count": 4,
                "raw_framebuffer_sha256_count": 4,
                "raw_stdout_count": 2,
                "raw_stderr_count": 2,
                "canonical_case_result_count": 2,
                "retained_artifact_count": 22,
                "direct_owner_or_script_calls": 0,
            },
            "artifacts": root_artifacts,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }
        context = {
            "report_path": root / "report.json",
            "rom_path": rom_path,
            "metadata_path": metadata_path,
            "rom_sha256": rom_sha256,
            "metadata_sha256": metadata_sha256,
            "handle_saving_data": 0x09001001,
            "workspace_root": ROOT,
        }
        return document, context

    @staticmethod
    def _validate(
        document: dict[str, Any], context: dict[str, Any],
    ) -> dict[str, Any]:
        context["report_path"].write_bytes(builder._stable(document))
        return builder._validate_mgba_save_ui_cow_evidence(**context)

    @staticmethod
    def _sync_root_artifacts(document: dict[str, Any]) -> None:
        document["artifacts"] = {
            f"run-{run['run_index']}/{CASE}/{name}": deepcopy(descriptor)
            for run in document["runs"]
            for name, descriptor in run["artifacts"].items()
        }

    @classmethod
    def _rewrite_leaf(
        cls, document: dict[str, Any], run_index: int,
        name: str, raw: bytes,
    ) -> None:
        run = document["runs"][run_index - 1]
        descriptor = run["artifacts"][name]
        Path(descriptor["path"]).write_bytes(raw)
        descriptor["size"] = len(raw)
        descriptor["sha256"] = builder._sha(raw)
        if name.endswith(".srm"):
            descriptor["fnv64"] = producer._fnv64(raw)
        elif name.endswith(".ppm"):
            descriptor["rgb_fnv1a64"] = producer._fnv64(
                raw[len(producer.PPM_HEADER):],
            )
        elif name.endswith(".rgba"):
            descriptor["framebuffer_fnv1a64"] = (
                producer._framebuffer_fnv64(raw)
            )

    @classmethod
    def _rewrite_process_join(
        cls, document: dict[str, Any], run_index: int,
    ) -> None:
        run = document["runs"][run_index - 1]
        result = run["result"]
        stdout = (
            json.dumps(
                result, ensure_ascii=False, separators=(",", ":"),
            ) + "\n"
        ).encode("utf-8")
        canonical = producer._stable(result).encode("utf-8")
        cls._rewrite_leaf(
            document, run_index, "save-ui-cow.stdout", stdout,
        )
        cls._rewrite_leaf(
            document, run_index, "save-ui-cow.result.json", canonical,
        )
        process = run["process_evidence"]
        process["raw_stdout_sha256"] = builder._sha(stdout)
        process["canonical_result_sha256"] = builder._sha(canonical)

    @classmethod
    def _recompute_normalized(
        cls, document: dict[str, Any], *, rewrite_process: bool = True,
    ) -> None:
        for run_index, run in enumerate(document["runs"], start=1):
            if rewrite_process:
                cls._rewrite_process_join(document, run_index)
            normalized = producer._normalized_run_payload(
                run["result"], run["artifacts"],
                run["process_evidence"],
            )
            run["normalized_sha256"] = producer._sha256(
                producer._stable(normalized).encode("utf-8"),
            )
        document["normalized_sha256"] = document["runs"][0][
            "normalized_sha256"
        ]
        document["normalized_hashes_match"] = len({
            run["normalized_sha256"] for run in document["runs"]
        }) == 1
        cls._sync_root_artifacts(document)

    @classmethod
    def _replace_final_images(
        cls, document: dict[str, Any], after: bytes,
    ) -> None:
        for run_index, run in enumerate(document["runs"], start=1):
            cls._rewrite_leaf(
                document, run_index, "save-ui-cow-after.srm", after,
            )
            cls._rewrite_leaf(
                document, run_index, "save-ui-cow-retained.srm", after,
            )
            run["result"]["srm"]["after_fnv64"] = producer._fnv64(
                after,
            )
        cls._recompute_normalized(document)

    @classmethod
    def _assert_runs_pass_producer(cls, document: Mapping[str, Any]) -> None:
        for run in document["runs"]:
            producer.validate_c_result(
                run["result"], Path(run["work_directory"]),
            )

    def test_fixture_each_raw_result_passes_producer_validator(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, _ = self._fixture(Path(temporary))
            self._assert_runs_pass_producer(document)
        self.assertEqual(document["schema_version"], 3)
        self.assertEqual(len(document["runs"]), 2)
        self.assertEqual(len(document["artifacts"]), 22)
        self.assertTrue(document["normalized_hashes_match"])

    def test_valid_v3_re_reads_two_runs_and_all_22_leaves(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            result = self._validate(document, context)
        self.assertEqual(
            result["kind"], "STAGE61_MGBA_SAVE_UI_COW_VALIDATION",
        )
        self.assertTrue(result["protected_generation_byte_exact"])
        self.assertTrue(result["fault_generation_incomplete"])
        self.assertTrue(result["fresh_continue"])
        self.assertTrue(result["all_external_artifacts_re_read"])

    def test_rejects_old_schema_or_missing_second_independent_run(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        mutations = (
            lambda document: document.__setitem__("schema_version", 1),
            lambda document: document["runs"].pop(),
            lambda document: document["runs"][1].__setitem__(
                "independent_os_process", False,
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate), tempfile.TemporaryDirectory(
                dir=local,
            ) as temporary:
                document, context = self._fixture(Path(temporary))
                mutate(document)
                with self.assertRaises(builder.Stage61BuildError):
                    self._validate(document, context)

    def test_rejects_non_exact_eleven_leaf_run_and_cross_run_alias(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            del document["runs"][0]["artifacts"][
                "save-ui-cow-before.srm"
            ]
            self._sync_root_artifacts(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            document["runs"][1]["artifacts"][
                "save-ui-cow-before.srm"
            ]["path"] = document["runs"][0]["artifacts"][
                "save-ui-cow-before.srm"
            ]["path"]
            self._sync_root_artifacts(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_key_deleted_from_result_stdout_and_canonical(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run in document["runs"]:
                del run["result"]["hard_restart"]["location"]
            # The three representations still agree.  A mere equality join
            # cannot catch the missing mandatory C-result field.
            self._recompute_normalized(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_nonempty_stderr_and_noncanonical_result_bytes(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            self._rewrite_leaf(
                document, 1, "save-ui-cow.stderr", b"mGBA warning\n",
            )
            self._recompute_normalized(document, rewrite_process=False)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run_index, run in enumerate(document["runs"], start=1):
                compact = (
                    json.dumps(
                        run["result"], ensure_ascii=False,
                        separators=(",", ":"), sort_keys=True,
                    ) + "\n"
                ).encode("utf-8")
                self._rewrite_leaf(
                    document, run_index,
                    "save-ui-cow.result.json", compact,
                )
                run["process_evidence"][
                    "canonical_result_sha256"
                ] = builder._sha(compact)
            self._recompute_normalized(document, rewrite_process=False)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_ppm_rgba_join_or_leaf_fnv_role_tamper(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run_index, run in enumerate(document["runs"], start=1):
                descriptor = run["artifacts"][
                    "save-ui-cow-save-failed.ppm"
                ]
                raw = bytearray(Path(descriptor["path"]).read_bytes())
                raw[-1] ^= 0xFF
                self._rewrite_leaf(
                    document, run_index,
                    "save-ui-cow-save-failed.ppm", bytes(raw),
                )
                run["result"]["save_failed_screen"][
                    "artifact_pixel_fnv64"
                ] = producer._fnv64(bytes(raw)[len(producer.PPM_HEADER):])
            self._recompute_normalized(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run in document["runs"]:
                descriptor = run["artifacts"][
                    "save-ui-cow-hard-continue.rgba"
                ]
                descriptor["framebuffer_fnv1a64"] = "0" * 16
                descriptor["framebuffer_role"] = "save_failed_state5"
            self._recompute_normalized(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_protected_bank_mutation_that_producer_accepts(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run_index, run in enumerate(document["runs"], start=1):
                before_path = Path(run["artifacts"][
                    "save-ui-cow-before.srm"
                ]["path"])
                fault_descriptor = run["artifacts"][
                    "save-ui-cow-fault.srm"
                ]
                fault = bytearray(Path(fault_descriptor["path"]).read_bytes())
                # Physical sector 0 contains logical section 11 when first=3.
                # Mutate it and repair its stock checksum, so the protected
                # generation remains structurally complete but is no longer
                # byte exact relative to before.
                fault[0x20] ^= 0x01
                sector = bytes(fault[:self.SECTOR_SIZE])
                checksum = builder._mgba_save_checksum(sector, 11)
                fault[0xFF6:0xFF8] = checksum.to_bytes(2, "little")
                fault_raw = bytes(fault)
                self._rewrite_leaf(
                    document, run_index, "save-ui-cow-fault.srm",
                    fault_raw,
                )
                before = before_path.read_bytes()
                result = run["result"]
                result["fault"]["changed_bytes"] = sum(
                    left != right
                    for left, right in zip(before, fault_raw, strict=True)
                )
                result["srm"]["fault_fnv64"] = producer._fnv64(
                    fault_raw,
                )
            self._recompute_normalized(document)
            self._assert_runs_pass_producer(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_complete_fault_target_that_producer_accepts(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            complete_target = self._generation(
                counter=self.RETRY_COUNTER,
                first_sector=6,
                canaries=True,
            )
            split = self.SLOT_SECTORS * self.SECTOR_SIZE
            for run_index, run in enumerate(document["runs"], start=1):
                before = Path(run["artifacts"][
                    "save-ui-cow-before.srm"
                ]["path"]).read_bytes()
                fault = bytearray(before)
                fault[split:2 * split] = complete_target[split:2 * split]
                fault_raw = bytes(fault)
                self._rewrite_leaf(
                    document, run_index, "save-ui-cow-fault.srm",
                    fault_raw,
                )
                run["result"]["fault"]["changed_bytes"] = sum(
                    left != right
                    for left, right in zip(before, fault_raw, strict=True)
                )
                run["result"]["srm"]["fault_fnv64"] = (
                    producer._fnv64(fault_raw)
                )
            self._recompute_normalized(document)
            self._assert_runs_pass_producer(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_valid_final_save_with_wrong_position_and_warp(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            substituted = self._save_images(
                x=21, y=19, warp_id=7, final_canaries=True,
            )["save-ui-cow-after.srm"]
            self._replace_final_images(document, substituted)
            self._assert_runs_pass_producer(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_valid_final_save_without_declared_canaries(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            substituted = self._save_images(
                final_canaries=False,
            )["save-ui-cow-after.srm"]
            self._replace_final_images(document, substituted)
            self._assert_runs_pass_producer(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_hard_continue_input_liveness_false_after_rehash(
        self,
    ) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run in document["runs"]:
                run["result"]["hard_restart"]["input_liveness"][
                    "start_menu_opened"
                ] = False
            self._recompute_normalized(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_hard_continue_input_position_drift_after_rehash(
        self,
    ) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            for run in document["runs"]:
                run["result"]["hard_restart"]["input_liveness"][
                    "location_after"
                ]["x"] = 21
            self._recompute_normalized(document)
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)

    def test_rejects_cross_run_semantic_drift_after_hash_recompute(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            document, context = self._fixture(Path(temporary))
            document["runs"][1]["result"]["natural_input"][
                "confirmation_pulses"
            ] = 3
            self._recompute_normalized(document)
            producer.validate_c_result(
                document["runs"][1]["result"],
                Path(document["runs"][1]["work_directory"]),
            )
            with self.assertRaises(builder.Stage61BuildError):
                self._validate(document, context)


if __name__ == "__main__":
    unittest.main()
