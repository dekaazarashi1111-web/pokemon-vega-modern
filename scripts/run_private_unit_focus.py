#!/usr/bin/env python3
"""修復対象だけを実行し、任意の例外本文を含めない実測結果を保存する。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TARGETS = (
    "tests.test_prepare_trainer_unit_inputs",
    "tests.test_build_id_spaces",
    "tests.test_cfru_id_space_inventory",
    "tests.test_trainer_changekit_content",
    "tests.test_trainer_changekit_final_builder",
    "tests.test_trainer_final_kanto_events",
    'tests.test_audit_private_unit_log',
    'tests.test_run_private_unit_focus',
    'tests.test_run_full_unit',
    'tests.test_portable_python_identity',
    'tests.test_prepare_private_unit_source_blobs',
    'tests.test_vega_adapter',
    'tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_control_abi_registry_all_domains_and_internal_trace_fail_closed',
    'tests.test_build_upstream.SandboxPathTests',
    'tests.test_event_authoring_packet',
    'tests.test_extract_vega_moves.FixedVegaMoveExtractionTests.test_cli_reads_only_fixed_config_and_reference_and_emits_json',
    'tests.test_population_evidence_boundary',
    'tests.test_validate_manifests',
    'tests.test_release.BpsTests',
    'tests.test_release.ReleaseContractTests.test_release_identity_is_v1_4_0_acquisition_package',
    'tests.test_stage61_catalog_state_matrix.Stage61CatalogStateMatrixUnitTests.test_runtime_toolchain_manifest_is_complete_and_abi_closed',
    'tests.test_stage61_factory_prepare_error_adapter',
    'tests.test_stage61_normal_save_cow_contract.Stage61NormalSaveCowMetadataContractTest',
    'tests.test_stage61_seafoam_engine_canonicalization.Stage61SeafoamEngineCanonicalizationTest.test_arm7tdmi_wrapper_compile_and_object_code',
    'tests.test_stage61_stateful_menu_mgba_contract',
    'tests.test_stage61_wiki',
    'tests.test_stage61_state_namespace_collision_audit',
    'tests.test_private_unit_fixtures',
)


def digest(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


class Result(unittest.TestResult):
    def __init__(self, tracked: set[str]):
        super().__init__()
        self.tracked = tracked
        self.details = []
        self.skip_details = []

    def _error(self, test, err, kind):
        # subtest値やerror.args、traceback本文は診断へ含めない。
        parent = getattr(test, 'test_case', test)
        identity = parent.id()
        fixture = re.fullmatch(r'(setUpClass|tearDownClass|setUpModule|tearDownModule) \(([A-Za-z_][A-Za-z_0-9.]*)\)', identity)
        if fixture:
            identity = fixture[2] + '.' + fixture[1]
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+', identity):
            identity = 'unittest.class_fixture'
        frames = []
        for frame, number in traceback.walk_tb(err[2]):
            try:
                relative = Path(frame.f_code.co_filename).resolve().relative_to(ROOT).as_posix()
            except ValueError:
                continue
            if relative in self.tracked:
                frames.append({'path': relative, 'line': number})
        kind_name = err[0].__name__
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', kind_name):
            kind_name = 'Exception'
        self.details.append({'outcome': kind, 'test': identity,
                             'exception_type': kind_name, 'frames': frames})
        (self.failures if kind == 'FAIL' else self.errors).append((test, kind_name))

    def addError(self, test, err):
        self._error(test, err, 'ERROR')

    def addFailure(self, test, err):
        self._error(test, err, 'FAIL')

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._error(test, err, 'FAIL' if issubclass(err[0], test.failureException) else 'ERROR')

    def addSkip(self, test, reason):
        super().addSkip(test, 'reason redacted')
        self.skip_details.append({'test': test.id(), 'reason_sha256': hashlib.sha256(reason.encode()).hexdigest()})


def main() -> int:
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z', '--', '*.py'], cwd=ROOT).decode().split('\0'))
    rom = ROOT / 'build/stages/62_npc_placement_integrity_repair.gba'
    before = digest(rom)
    from scripts.run_full_unit import PrivateResult
    result = PrivateResult(tracked)
    suite = unittest.defaultTestLoader.loadTestsFromNames(TARGETS)
    suite.run(result)
    after = digest(rom)
    report = {
        'head_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'expected_failures': len(result.expectedFailures),
        'unexpected_successes': len(result.unexpectedSuccesses),
        'details': result.details, 'skip_records': result.skip_details,
        'stage62_rom_unchanged': before == after, 'stage62_rom_sha256': after,
    }
    path = ROOT / 'build/private-unit-focus/result.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
