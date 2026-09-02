from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts import build_stage61_display_npc_event_audit as builder
from tests.stage61_save_fixture import build_stage61_save
from tests.test_stage61_event_lifecycle_e2e import (
    Stage61EventLifecycleE2eTests as ResultFixture,
)


ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "build/stages/61_display_npc_event_audit.gba"
METADATA_PATH = ROOT / "build/stages/61_display_npc_event_audit.json"
RUNNER_PATH = ROOT / builder.MGBA_EVENT_LIFECYCLE_ORCHESTRATOR_SOURCE
SPEC = importlib.util.spec_from_file_location(
    "stage61_event_lifecycle_builder_fixture", RUNNER_PATH,
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class Stage61EventLifecycleBuilderGateTests(unittest.TestCase):
    @staticmethod
    def _sources() -> dict[str, Any]:
        event_python = ROOT / builder.MGBA_EVENT_LIFECYCLE_ORCHESTRATOR_SOURCE
        event_c = ROOT / builder.MGBA_EVENT_LIFECYCLE_RUNNER_SOURCE
        display_c = ROOT / builder.MGBA_RUNNER_SOURCE
        main_python = ROOT / builder.MGBA_ORCHESTRATOR_SOURCE
        display_raw = display_c.read_bytes()
        original = "\nint main(int argc, char **argv)\n{"
        renamed = (
            "\nint s61_embedded_event_lifecycle_main(int argc, char **argv)\n{"
        )
        return {
            "status": "PASS",
            "command": (
                "cc -std=c11 -O2 -Wall -Wextra -Werror "
                "-pedantic embedded.c event.c -lmgba"
            ),
            "runner": {
                "path": str(event_python.resolve()),
                "sha256": builder._sha(event_python.read_bytes()),
            },
            "c_harness": {
                "path": str(event_c.resolve()),
                "sha256": builder._sha(event_c.read_bytes()),
            },
            "embedded_display_harness": {
                "path": str(display_c.resolve()),
                "sha256": builder._sha(display_raw),
                "transformed_sha256": builder._sha(
                    display_raw.decode("utf-8").replace(
                        original, renamed, 1,
                    ).encode("utf-8")
                ),
                "outer_main_renamed": True,
                "other_bytes_unchanged": True,
            },
            "current_orchestrator": {
                "path": str(main_python.resolve()),
                "sha256": builder._sha(main_python.read_bytes()),
            },
            "stdout_empty": True,
            "stderr_empty": True,
        }

    @staticmethod
    def _identity(rom_raw: bytes, metadata_raw: bytes,
                  roots: dict[str, Any]) -> dict[str, Any]:
        config_path = (ROOT / builder.DEFAULT_CONFIG).resolve()
        return {
            "schema_version": 1,
            "status": "PASS",
            "rom": str(ROM_PATH.resolve()),
            "rom_size": len(rom_raw),
            "rom_sha256": builder._sha(rom_raw),
            "metadata": str(METADATA_PATH.resolve()),
            "metadata_sha256": builder._sha(metadata_raw),
            "config": str(config_path),
            "config_sha256": builder._sha(config_path.read_bytes()),
            "root_exact": roots,
            "contracts": {
                "normal_save_copy_on_write": True,
                "ferry_four_choice_rows": 4,
                "ferry_owner_count": 7,
                "vermilion_persistent_flag": "0x1871",
                "route16_hidden_flag": "0x149F",
                "route12_hidden_flag": "0x149E",
                "canonical_snorlax_species": 491,
            },
        }

    @classmethod
    def _result(cls, case: str, work: Path,
                roots: dict[str, Any]) -> dict[str, Any]:
        if case == "vermilion":
            result = ResultFixture._vermilion(work)
            switch = result["switches_retry"][1]
            (work / result["srm"]).write_bytes(build_stage61_save(
                map_group=98,
                map_number=40,
                x=1 + ((switch - 1) % 5) * 2,
                y=11 + ((switch - 1) // 5) * 2,
                flags={0x1871: True, 0x0001: False},
            ))
            return result
        if case == "ferry":
            result = ResultFixture._ferry(work)
            for owner, root in zip(
                result["owners"], roots["ferry"], strict=True,
            ):
                owner["owner_root"] = root["root"]
                (work / owner["srm"]).write_bytes(build_stage61_save(
                    map_group=3, map_number=5, x=23, y=32,
                ))
            return result
        if case == "snorlax":
            result = ResultFixture._snorlax(work)
            result["owner_root"] = roots["route16_snorlax"]["root"]
            result["producer_owner_root"] = roots["flute_giver"]["root"]
            result["route12_capture_control"]["owner_root"] = (
                roots["route12_snorlax"]["root"]
            )
            return result
        if case == "fly":
            return ResultFixture._fly(work)
        raise AssertionError(case)

    @classmethod
    def _fixture(
        cls, directory: Path,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        rom_raw = ROM_PATH.read_bytes()
        metadata_raw = METADATA_PATH.read_bytes()
        roots = builder._mgba_event_v2_root_exact(rom_raw)
        cases: dict[str, Any] = {}
        root_artifacts: dict[str, Any] = {}
        for case in ("vermilion", "ferry", "snorlax", "fly"):
            runs: list[dict[str, Any]] = []
            hashes: list[str] = []
            for run_index in (1, 2):
                work = directory / f"run-{run_index}" / case
                work.mkdir(parents=True)
                result = cls._result(case, work, roots)
                raw_stdout = (
                    json.dumps(
                        result, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"),
                    ) + "\n"
                ).encode("utf-8")
                process = RUNNER._retain_process_evidence(
                    work, case, stdout=raw_stdout, stderr=b"", result=result,
                )
                validated = RUNNER.validate_result(case, result, work, roots)
                validated["process_evidence"] = {
                    key: value for key, value in process.items()
                    if key != "artifacts"
                }
                validated["artifacts"].update(process["artifacts"])
                normalized = RUNNER._normalized_run_payload(validated)
                normalized_sha = builder._sha(builder._stable(normalized))
                hashes.append(normalized_sha)
                run = {
                    "schema_version": 1,
                    "status": "PASS",
                    "run_index": run_index,
                    "independent_os_process": True,
                    "empty_case_directory_at_start": True,
                    "work_directory": str(work.resolve()),
                    "normalized_sha256": normalized_sha,
                    **validated,
                    "failed": 0,
                    "untested": 0,
                    "warnings": 0,
                }
                runs.append(run)
                for name, descriptor in validated["artifacts"].items():
                    root_artifacts[
                        f"run-{run_index}/{case}/{name}"
                    ] = descriptor
            if len(set(hashes)) != 1:
                raise AssertionError(f"{case} fixture normalized drift")
            cases[case] = {
                "schema_version": 1,
                "status": "PASS",
                "run_count": 2,
                "independent_os_processes": True,
                "normalized_sha256": hashes[0],
                "normalized_hashes_match": True,
                "runs": runs,
                "failed": 0,
                "untested": 0,
                "warnings": 0,
            }

        report = {
            "schema_version": 1,
            "stage": builder.STAGE,
            "task": builder.TASK,
            "status": "PASS",
            "identity": cls._identity(rom_raw, metadata_raw, roots),
            "sources": cls._sources(),
            "runs_per_case": 2,
            "independent_process_count": 8,
            "cases": cases,
            "coverage": {
                "vermilion_switch_failure_success_reentry": True,
                "ferry_all_seven_cancel_board_arrive_save_continue": True,
                "route16_natural_producer_no_run_caught_reentry": True,
                "route12_species491_real_bag_caught_party_field_reentry": True,
                "route12_route16_external_srm_semantic_readback": True,
                "engine_teleport_real_producer_choice": True,
                "each_case_two_independent_os_processes": True,
                "normalized_hash_match_per_case": True,
                "owner_roots_resolved_from_rom": 25,
                "full_srm_sha256_count": 22,
                "ppm_sha256_count": 30,
                "ppm_rgb_fnv1a64_join_count": 30,
                "raw_stdout_count": 8,
                "raw_stderr_count": 8,
                "canonical_case_result_count": 8,
                "retained_artifact_count": 76,
                "direct_owner_or_script_calls": 0,
            },
            "artifacts": root_artifacts,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }
        report_path = directory / "event-report.json"
        report_path.write_bytes(builder._stable(report))
        context = {
            "report_path": report_path,
            "rom_path": ROM_PATH,
            "metadata_path": METADATA_PATH,
            "rom_raw": rom_raw,
            "metadata_raw": metadata_raw,
        }
        return report, context

    @staticmethod
    def _rewrite(report: dict[str, Any], context: dict[str, Any]) -> None:
        Path(context["report_path"]).write_bytes(builder._stable(report))

    @staticmethod
    def _refresh_artifact(report: dict[str, Any], case: str,
                          run_index: int, name: str) -> None:
        run = report["cases"][case]["runs"][run_index - 1]
        descriptor = run["artifacts"][name]
        raw = Path(descriptor["path"]).read_bytes()
        descriptor["size"] = len(raw)
        descriptor["sha256"] = builder._sha(raw)
        report["artifacts"][f"run-{run_index}/{case}/{name}"] = copy.deepcopy(
            descriptor
        )

    def test_valid_v2_report_re_reads_all_76_leaves(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            _, context = self._fixture(Path(temporary))
            result = builder._validate_mgba_event_lifecycle_evidence(**context)
        self.assertEqual(result["physical_lifecycle_cases"], 4)
        self.assertEqual(result["independent_os_processes"], 8)
        self.assertEqual(result["resolved_owner_roots"], 25)
        self.assertEqual(result["retained_artifacts_re_read"], 76)
        self.assertEqual(result["decoded_external_srm_count"], 22)
        self.assertEqual(result["ppm_rgb_fnv1a64_join_count"], 30)

    def test_rejects_source_result_and_missing_second_process(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        mutations = {
            "source": lambda report: report["sources"]["c_harness"].__setitem__(
                "sha256", "0" * 64,
            ),
            "physical_result": lambda report: report["cases"]["ferry"][
                "runs"
            ][0]["result"]["owners"][0].__setitem__("owner_pc_hits", 0),
            "one_run": lambda report: report["cases"]["fly"]["runs"].pop(),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                dir=local,
            ) as temporary:
                report, context = self._fixture(Path(temporary))
                mutate(report)
                self._rewrite(report, context)
                with self.assertRaises(builder.Stage61BuildError):
                    builder._validate_mgba_event_lifecycle_evidence(**context)

    def test_rejects_same_size_ppm_substitution_after_sha_refresh(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            report, context = self._fixture(Path(temporary))
            name = "vermilion-open.ppm"
            descriptor = report["cases"]["vermilion"]["runs"][0][
                "artifacts"
            ][name]
            rgb = bytes(index & 0xFF for index in range(240 * 160 * 3))
            Path(descriptor["path"]).write_bytes(b"P6\n240 160\n255\n" + rgb)
            self._refresh_artifact(report, "vermilion", 1, name)
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "PPM RGB join",
            ):
                builder._validate_mgba_event_lifecycle_evidence(**context)

    def test_rejects_checksum_valid_srm_semantic_substitution(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            report, context = self._fixture(Path(temporary))
            name = "event-lifecycle-vermilion.srm"
            descriptor = report["cases"]["vermilion"]["runs"][0][
                "artifacts"
            ][name]
            Path(descriptor["path"]).write_bytes(build_stage61_save(
                map_group=98, map_number=40, x=1, y=1,
                flags={0x1871: True, 0x0001: False},
            ))
            self._refresh_artifact(report, "vermilion", 1, name)
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "座標不一致",
            ):
                builder._validate_mgba_event_lifecycle_evidence(**context)

    def test_rejects_raw_stdout_canonical_result_divergence(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=local) as temporary:
            report, context = self._fixture(Path(temporary))
            case = "fly"
            run = report["cases"][case]["runs"][0]
            name = f"case-{case}.stdout"
            descriptor = run["artifacts"][name]
            forged = copy.deepcopy(run["result"])
            forged["actual_walk_steps"] = 999
            Path(descriptor["path"]).write_bytes(
                (json.dumps(forged, separators=(",", ":")) + "\n").encode()
            )
            self._refresh_artifact(report, case, 1, name)
            run["process_evidence"]["raw_stdout_sha256"] = (
                run["artifacts"][name]["sha256"]
            )
            self._rewrite(report, context)
            with self.assertRaisesRegex(
                builder.Stage61BuildError, "raw/canonical/result join",
            ):
                builder._validate_mgba_event_lifecycle_evidence(**context)


if __name__ == "__main__":
    unittest.main()
