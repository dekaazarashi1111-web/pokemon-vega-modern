from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts import build_stage61_display_npc_event_audit as BUILDER
from scripts import run_stage61_mgba_validation as RUNNER


ROOT = Path(__file__).resolve().parents[1]


class Stage61BuilderRetentionV2Tests(unittest.TestCase):
    def test_builder_resolves_framebuffer_role_independently(self) -> None:
        document = {
            "schema_version": 1,
            "status": "PASS",
            "case": "map_popup",
            "framebuffer_artifacts": [{
                "path": "map-popup-peak.ppm",
                "rgb_fnv1a64": "0123456789ABCDEF",
                "framebuffer_role": "INTERACTION_PEAK_FRAME",
            }],
        }
        stripped, rows = (
            BUILDER._mgba_retention_v3_split_c_framebuffer_artifacts(
                document, case_id="map_popup",
            )
        )
        self.assertNotIn("framebuffer_artifacts", stripped)
        self.assertEqual(
            rows[0]["framebuffer_role"], "INTERACTION_PEAK_FRAME",
        )
        for key, value in (
            ("framebuffer_role", "DIALOGUE_MESSAGE_FRAME"),
            ("path", "unknown-frame.ppm"),
        ):
            forged = deepcopy(document)
            forged["framebuffer_artifacts"][0][key] = value
            with self.assertRaises(BUILDER.Stage61BuildError):
                BUILDER._mgba_retention_v3_split_c_framebuffer_artifacts(
                    forged, case_id="map_popup",
                )

    def _frame_descriptor(
        self, case_id: str, path: str, raw: bytes,
    ) -> dict[str, object]:
        header = b"P6\n240 160\n255\n"
        self.assertTrue(raw.startswith(header))
        return {
            "path": path,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "rgb_fnv1a64": RUNNER._fnv1a64(raw[len(header):]),
            "framebuffer_role": RUNNER._framebuffer_role(case_id, path),
        }

    def _wrapper(
        self, case_id: str, result: dict[str, object], *, runs: int,
        shards: int,
    ) -> dict[str, object]:
        result_sha = hashlib.sha256(
            RUNNER._stable(result).encode("utf-8")
        ).hexdigest()
        shard_hashes = [result_sha] * shards
        return {
            "status": "PASS",
            "process_runs": runs,
            "process_shards": shards,
            "same_shard_boundaries_across_runs": True,
            "per_shard_identical_results": True,
            "per_shard_result_sha256": shard_hashes,
            "per_run_merged_result_sha256": [result_sha] * runs,
            "per_run_per_shard_result_sha256": [
                list(shard_hashes) for _ in range(runs)
            ],
            "identical_results": True,
            "result": result,
        }

    def _source_tree(
        self, root: Path, case_id: str, *, runs: int, shards: int,
        frames: dict[int, tuple[str, bytes]],
        stdout_document: dict[str, object],
    ) -> Path:
        source = root / "source"
        for run_index in range(1, runs + 1):
            for shard_index in range(1, shards + 1):
                work = source / (
                    f"{case_id}-run-{run_index}-shard-{shard_index}"
                )
                work.mkdir(parents=True)
                relative, raw = frames[shard_index]
                raw_document = deepcopy(stdout_document)
                raw_document.setdefault("framebuffer_artifacts", [{
                    "path": relative,
                    "rgb_fnv1a64": RUNNER._fnv1a64(
                        raw[len(b"P6\n240 160\n255\n"):]
                    ),
                    "framebuffer_role": RUNNER._framebuffer_role(
                        case_id, relative,
                    ),
                }])
                (work / f"observer-{case_id}-stdout.json").write_text(
                    json.dumps(raw_document, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                (work / f"observer-{case_id}-stderr.log").write_bytes(b"")
                frame = work / relative
                frame.parent.mkdir(parents=True, exist_ok=True)
                frame.write_bytes(raw)
        return source

    def test_runner_producer_and_independent_builder_validator_agree(
        self,
    ) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            root = Path(temporary)
            case_id = "map_popup"
            frames = {
                1: (
                    "map-popup-peak.ppm",
                    b"P6\n240 160\n255\n" + bytes(
                        (index + 19) & 0xFF
                        for index in range(240 * 160 * 3)
                    ),
                )
            }
            rom = root / "stage61.gba"
            rom.write_bytes(b"stage61-retention-v2-rom")
            rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
            result = {
                "schema_version": 1,
                "status": "PASS",
                "case": case_id,
                "artifacts": [
                    self._frame_descriptor(
                        case_id,
                        (
                            f"shard-{shard}/{relative}"
                            if len(frames) > 1 else relative
                        ),
                        raw,
                    )
                    for shard, (relative, raw) in frames.items()
                ],
            }
            source = self._source_tree(
                root, case_id, runs=2, shards=1, frames=frames,
                stdout_document=result,
            )
            results = {
                case_id: self._wrapper(
                    case_id, result, runs=2, shards=1,
                )
            }
            report = root / "report.json"
            retention = RUNNER._build_artifact_retention(
                root / "retained", temp=source, rom_path=rom,
                rom_sha256=rom_sha, results=results, report_path=report,
                effects=False,
            )
            validated = BUILDER._validate_mgba_retained_artifact_manifest_v3(
                retention, report_path=report, rom_sha256=rom_sha,
                results=results, effects=False, expected_case_ids=(case_id,),
            )
            self.assertEqual(validated["schema_version"], 3)
            self.assertEqual(
                validated["kind"],
                "STAGE61_MGBA_RETAINED_ARTIFACT_VALIDATION_V3",
            )
            self.assertTrue(validated["run_shard_phase_exact"])

            legacy_root = deepcopy(retention)
            legacy_root["schema_version"] = 2
            legacy_root["kind"] = "STAGE61_MGBA_ARTIFACT_RETENTION_V2"
            with self.assertRaisesRegex(
                BUILDER.Stage61BuildError, "report schema",
            ):
                BUILDER._validate_mgba_retained_artifact_manifest_v3(
                    legacy_root, report_path=report,
                    rom_sha256=rom_sha, results=results,
                    effects=False, expected_case_ids=(case_id,),
                )

            manifest_path = root / "retained" / "manifest.json"
            original_manifest_raw = manifest_path.read_bytes()
            original_retention = deepcopy(retention)
            forged = json.loads(original_manifest_raw.decode("utf-8"))
            stream = next(
                row for row in forged["entries"]
                if row["role"] == "PROCESS_STDOUT"
            )
            stream["phase"] = "FORGED_PHASE"
            body = {key: value for key, value in stream.items()
                    if key != "entry_id"}
            stream["entry_id"] = (
                "artifact-entry-" + RUNNER._retention_binding_sha256(body)
            )
            forged["tree_sha256"] = RUNNER._retention_binding_sha256(
                forged["entries"]
            )
            forged["source_registry"] = [
                {
                    key: row[key] for key in (
                        "entry_id", "case_id", "role", "run_index",
                        "shard_index", "phase", "source_relative_path",
                        "size", "sha256", "source_result_sha256",
                    )
                }
                for row in forged["entries"]
                if row["case_id"] is not None
                and row["role"] != "CASE_RESULT_JSON"
            ]
            forged["source_registry"].sort(key=lambda row: (
                row["case_id"], row["run_index"], row["shard_index"],
                row["source_relative_path"], row["role"], row["phase"],
            ))
            forged["source_registry_sha256"] = (
                RUNNER._retention_binding_sha256(
                    forged["source_registry"]
                )
            )
            unsigned = deepcopy(forged)
            unsigned.pop("manifest_sha256")
            forged["manifest_sha256"] = (
                RUNNER._retention_binding_sha256(unsigned)
            )
            forged_raw = RUNNER._stable(forged).encode("utf-8")
            manifest_path.write_bytes(forged_raw)
            retention["manifest_size"] = len(forged_raw)
            retention["manifest_file_sha256"] = hashlib.sha256(
                forged_raw
            ).hexdigest()
            retention["tree_sha256"] = forged["tree_sha256"]
            retention["source_registry_sha256"] = forged[
                "source_registry_sha256"
            ]
            retention["entry_ids"] = [
                row["entry_id"] for row in forged["entries"]
            ]
            with self.assertRaisesRegex(
                BUILDER.Stage61BuildError, "process stream partition",
            ):
                BUILDER._validate_mgba_retained_artifact_manifest_v3(
                    retention, report_path=report, rom_sha256=rom_sha,
                    results=results, effects=False,
                    expected_case_ids=(case_id,),
                )
            manifest_path.write_bytes(original_manifest_raw)
            retention = original_retention

            frame_entry = next(
                row for row in json.loads(
                    manifest_path.read_text(
                        encoding="utf-8"
                    )
                )["entries"]
                if row["role"] == "FRAMEBUFFER_PPM"
            )
            leaf = root / "retained" / frame_entry["relative_path"]
            leaf.write_bytes(leaf.read_bytes() + b"forged")
            with self.assertRaisesRegex(
                BUILDER.Stage61BuildError, "leaf size/SHA",
            ):
                BUILDER._validate_mgba_retained_artifact_manifest_v3(
                    retention, report_path=report, rom_sha256=rom_sha,
                    results=results, effects=False,
                    expected_case_ids=(case_id,),
                )

    def test_rejects_unjoined_streams_and_structurally_fake_ppm(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        mutations = {
            "stdout": (
                lambda work, frame: (
                    work / "observer-map_popup-stdout.json"
                ).write_text(
                    '{"schema_version":1,"status":"PASS",'
                    '"case":"unrelated"}\n', encoding="utf-8",
                ),
                "stdout .*\u4e0d\u4e00\u81f4|framebuffer artifact registry\u6b20\u843d",
            ),
            "stderr": (
                lambda work, frame: (
                    work / "observer-map_popup-stderr.log"
                ).write_bytes(b"forged diagnostic\n"),
                "stderr非空",
            ),
            "truncated_ppm": (
                lambda work, frame: frame.write_bytes(
                    b"P6\n240 160\n255\n" + b"\x01\x02"
                ),
                "framebuffer PPM構造不正",
            ),
            "uniform_ppm": (
                lambda work, frame: frame.write_bytes(
                    b"P6\n240 160\n255\n" + b"\x7F" * (240 * 160 * 3)
                ),
                "framebuffer PPM構造不正",
            ),
        }
        for name, (mutate, message) in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                dir=local,
            ) as temporary:
                root = Path(temporary)
                case_id = "map_popup"
                initial = (
                    b"P6\n240 160\n255\n" + bytes(
                        index & 0xFF for index in range(240 * 160 * 3)
                    )
                )
                frames = {1: ("map-popup-peak.ppm", initial)}
                result = {
                    "schema_version": 1,
                    "status": "PASS",
                    "case": case_id,
                    "artifacts": [self._frame_descriptor(
                        case_id, "map-popup-peak.ppm", initial,
                    )],
                }
                source = self._source_tree(
                    root, case_id, runs=1, shards=1, frames=frames,
                    stdout_document=result,
                )
                work = source / f"{case_id}-run-1-shard-1"
                frame = work / "map-popup-peak.ppm"
                mutate(work, frame)
                actual_frame = frame.read_bytes()
                result["artifacts"][0]["size"] = len(actual_frame)
                result["artifacts"][0]["sha256"] = hashlib.sha256(
                    actual_frame
                ).hexdigest()
                result["artifacts"][0]["rgb_fnv1a64"] = RUNNER._fnv1a64(
                    actual_frame[len(b"P6\n240 160\n255\n"):]
                )
                if name in {"truncated_ppm", "uniform_ppm"}:
                    (work / "observer-map_popup-stdout.json").write_text(
                        json.dumps(result, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                results = {
                    case_id: self._wrapper(
                        case_id, result, runs=1, shards=1,
                    )
                }
                rom = root / "stage61.gba"
                rom.write_bytes(b"stage61-retention-v2-rom")
                rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
                report = root / "report.json"
                with self.assertRaisesRegex(
                    (RUNNER.Stage61MgbaError, BUILDER.Stage61BuildError),
                    message,
                ):
                    retention = RUNNER._build_artifact_retention(
                        root / "retained", temp=source, rom_path=rom,
                        rom_sha256=rom_sha, results=results,
                        report_path=report, effects=False,
                    )
                    BUILDER._validate_mgba_retained_artifact_manifest_v3(
                        retention, report_path=report, rom_sha256=rom_sha,
                        results=results, effects=False,
                        expected_case_ids=(case_id,),
                    )

    def test_sharded_stdout_requires_exact_disjoint_union(self) -> None:
        from tests.test_stage61_mgba_validation import (
            Stage61MgbaValidationTests,
        )

        base = Stage61MgbaValidationTests()._calibration_document()
        for path in base["results"][0]["successful_paths"]:
            capture = path["capture"]
            for row in [
                *capture["messages"], *capture["printer_calls"],
            ]:
                row["raw_sha256"] = hashlib.sha256(
                    bytes.fromhex(row["raw_hex"])
                ).hexdigest()
        first = deepcopy(base)
        second = deepcopy(base)
        second_row = second["results"][0]
        second_row["case_id"] = "cal-003-002-008"
        second_row["owner_key"] = "OBJECT:003/002:008"
        second_row["local_id"] = 9
        for document in (first, second):
            document["fixture_count"] = 1
            document["resolved"] = 1
            document["unresolved"] = 0
        expected = RUNNER._merge_calibration_shards([first, second])
        expected = RUNNER.validate_final_mgba_case_result(
            "catalog_calibrate", expected,
        )
        RUNNER._retention_join_shards(
            "catalog_calibrate", [first, second], expected,
        )
        BUILDER._mgba_retention_v3_join_shards(
            "catalog_calibrate", [first, second], expected,
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "\u91cd\u8907",
        ):
            RUNNER._retention_join_shards(
                "catalog_calibrate", [first, first], expected,
            )
        with self.assertRaisesRegex(
            BUILDER.Stage61BuildError, "\u91cd\u8907",
        ):
            BUILDER._mgba_retention_v3_join_shards(
                "catalog_calibrate", [first, first], expected,
            )

    def test_final_persistence_selection_is_exact_three_expanded_states(
        self,
    ) -> None:
        matrix = json.loads((
            ROOT / "reports/generated/stage61_npc_state_matrix.json"
        ).read_text(encoding="utf-8"))
        selected = BUILDER._validate_required_mgba_persistence_matrix_cases(
            matrix["cases"]
        )
        self.assertEqual(
            list(selected),
            [
                case_id for case_id, _
                in BUILDER.MGBA_REQUIRED_STATE_PERSISTENCE_CASES
            ],
        )
        for label, mutate in (
            ("missing", lambda rows: rows.__delitem__(next(
                index for index, row in enumerate(rows)
                if row["case_id"]
                == "matrix-096-001-010-default-006"
            ))),
            ("flag", lambda rows: next(
                row for row in rows if row["case_id"]
                == "matrix-096-001-010-default-001"
            )["state"]["flags"][0].__setitem__("value", False)),
            ("var", lambda rows: next(
                row for row in rows if row["case_id"]
                == "matrix-096-001-010-default-007"
            )["state"]["vars"][0].__setitem__("value", 2)),
        ):
            with self.subTest(label=label):
                rows = deepcopy(matrix["cases"])
                mutate(rows)
                with self.assertRaises(BUILDER.Stage61BuildError):
                    BUILDER._validate_required_mgba_persistence_matrix_cases(
                        rows
                    )

    def test_final_persistence_report_requires_both_modes_and_exact_ids(
        self,
    ) -> None:
        case_ids = [
            case_id for case_id, _
            in BUILDER.MGBA_REQUIRED_STATE_PERSISTENCE_CASES
        ]
        document = {
            "state_persistence": {
                "selected_case_count": 3,
                "case_ids": case_ids,
                "modes": [
                    "catalog_state_legacy_persistence",
                    "catalog_state_persistence",
                ],
                "normal_rom_save": True,
                "save_via_start_menu_input": True,
                "separate_writer_reader_processes": True,
                "fresh_title_continue": True,
                "legacy_saveblock1_var_canaries": [
                    0x4000, 0x4040, 0x40FF,
                ],
                "legacy_source": {"sha256": "0" * 64},
                "failed": 0,
                "untested": 0,
            }
        }

        def payload(mode: str) -> dict[str, object]:
            rows = []
            for case_id in case_ids:
                common = {
                    "case_id": case_id,
                    "fresh_title_continue": True,
                    "expanded_flag_readback": True,
                    "expanded_var_readback": True,
                }
                rows.append({
                    "case_id": case_id,
                    "base_case_id": "cal-096-001-010",
                    "writer": {
                        **common, "phase": "WRITE",
                        "normal_save_generations": 2,
                        "save_via_start_menu_input": True,
                    },
                    "reader": {
                        **common, "phase": "READ",
                        "normal_save_generations": 0,
                        "save_via_start_menu_input": False,
                    },
                    "reader_save_image_unchanged": True,
                })
            return {"case": mode, "fixture_count": 3, "results": rows}

        payloads = {
            mode: payload(mode) for mode in (
                "catalog_state_persistence",
                "catalog_state_legacy_persistence",
            )
        }
        BUILDER._validate_required_mgba_persistence_report(
            document, payloads,
        )
        for label, mutate in (
            ("mode", lambda value: value["state_persistence"].__setitem__(
                "modes", ["catalog_state_persistence"],
            )),
            ("id", lambda value: value["state_persistence"]["case_ids"]
             .__setitem__(1, case_ids[0])),
        ):
            with self.subTest(label=label):
                forged = deepcopy(document)
                mutate(forged)
                with self.assertRaises(BUILDER.Stage61BuildError):
                    BUILDER._validate_required_mgba_persistence_report(
                        forged, payloads,
                    )

    def test_real_c_stdout_projection_is_revalidated_before_enrichment(
        self,
    ) -> None:
        """Raw C stdout lacks Python-added artifacts but cannot omit fields."""

        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        case_id = "snorlax_flag_visibility_matrix"
        raw_result = {
            "schema_version": 2,
            "status": "PASS",
            "case": case_id,
            "supplementary_direct_state_setup": True,
            "not_primary_producer_consumer_test": True,
            "clear_visible": True,
            "set_hidden_after_save_load": True,
            "warnings": 0,
        }
        ppm = (
            b"P6\n240 160\n255\n"
            + bytes((index * 29 + 7) & 0xFF
                    for index in range(240 * 160 * 3))
        )
        final_result = {
            **raw_result,
            "artifacts": [self._frame_descriptor(
                case_id, "snorlax-direct-peak.ppm", ppm,
            )],
        }
        context = {
            "fixtures": RUNNER.validate_fixture_document(
                deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
            ),
            "charmap": RUNNER._read_charmap(),
            "catalog_expected": {},
            "event_expected": {},
            "calibration_expected": {},
            "stateful_expected": {},
        }

        for label, stdout_document, passes in (
            ("complete", raw_result, True),
            ("minimal-anchor", {
                "schema_version": 2,
                "status": "PASS",
                "case": case_id,
            }, False),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                dir=local,
            ) as temporary:
                root = Path(temporary)
                frames = {1: ("snorlax-direct-peak.ppm", ppm)}
                source = self._source_tree(
                    root, case_id, runs=2, shards=1, frames=frames,
                    stdout_document=stdout_document,
                )
                rom = root / "stage61.gba"
                rom.write_bytes(b"stage61-real-c-stdout-projection")
                rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
                results = {
                    case_id: self._wrapper(
                        case_id, final_result, runs=2, shards=1,
                    )
                }
                report = root / "report.json"
                retention = RUNNER._build_artifact_retention(
                    root / "retained", temp=source, rom_path=rom,
                    rom_sha256=rom_sha, results=results,
                    report_path=report, effects=False,
                )
                validate = lambda: (
                    BUILDER._validate_mgba_retained_artifact_manifest_v3(
                        retention, report_path=report, rom_sha256=rom_sha,
                        results=results, effects=False,
                        expected_case_ids=(case_id,),
                        raw_case_context=context,
                    )
                )
                if passes:
                    self.assertTrue(validate()["run_shard_phase_exact"])
                    missing_stateful_context = deepcopy(context)
                    missing_stateful_context.pop("stateful_expected")
                    with self.assertRaisesRegex(
                        BUILDER.Stage61BuildError,
                        "raw normalization context\u4e0d\u6b63",
                    ):
                        BUILDER._validate_mgba_retained_artifact_manifest_v3(
                            retention, report_path=report,
                            rom_sha256=rom_sha, results=results,
                            effects=False, expected_case_ids=(case_id,),
                            raw_case_context=missing_stateful_context,
                        )
                else:
                    with self.assertRaisesRegex(
                        BUILDER.Stage61BuildError,
                        "raw stdout\u518d\u691c\u8a3c\u5931\u6557",
                    ):
                        validate()


if __name__ == "__main__":
    unittest.main()
