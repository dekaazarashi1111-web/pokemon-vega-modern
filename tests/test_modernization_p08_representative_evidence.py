"""Original archive, provenance, process and P08-layer regression tests.

Negative fixtures are not emulator executions. Positive tests revalidate the
originals actually committed by the authenticated evidence-import workflow.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import modernization_p08_representative_evidence as e


class RepresentativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = e.build_extension()
        cls.payloads = {}
        cls.actions = {}
        for suite, pin in e.SUITES.items():
            directory = e.ROOT / e.DIRECTORY / suite / str(pin['run_id'])
            cls.payloads[suite] = e.unpack((directory / 'source.zip').read_bytes(), suite)
            cls.actions[suite] = json.loads((directory / 'actions.json').read_bytes())

    def payload_change(self, suite, transform):
        files = dict(self.payloads[suite])
        report = e.witness.strict_json(files['result.json'])
        transform(report)
        files['result.json'] = files['job.stdout.json'] = e.base.stable(report)
        return files

    def reject_payload(self, files, suite):
        with self.assertRaises((e.base.EvidenceError, ValueError, TypeError, KeyError, UnicodeError)):
            e.validate_payload(files, suite)

    def test_three_original_suites_are_bound_to_one_candidate(self):
        self.assertEqual([row['id'] for row in self.actual['suites']], list(e.SUITES))
        self.assertEqual(self.actual['candidate_rom']['sha256'], e.witness.ROM_ID['sha256'])
        for suite in e.SUITES:
            self.assertEqual(e.validate_payload(self.payloads[suite], suite)['status'], 'PASS')

    def test_retained_thirty_are_not_new_runs(self):
        self.assertEqual(self.actual['retained_original_fresh_process_runs'], 30)
        self.assertEqual(self.actual['fresh_process_runs_this_validation'], 0)
        self.assertIs(self.actual['heavy_execution_performed'], False)
        self.assertEqual([r['retained_original_fresh_process_runs'] for r in self.actual['suites']], [2, 24, 4])

    def test_full_acceptance_and_natural_routes_remain_unclaimed(self):
        self.assertTrue(all(value is False for value in self.actual['unclaimed_coverage'].values()))
        self.assertIs(self.actual['phase_completion_promoted'], False)
        self.assertIs(self.actual['active_baseline_changed'], False)

    def test_source_bindings_include_rom_seed_workflows_and_original_members(self):
        bindings = self.actual['source_bindings']
        for path in [e.ROM, e.SEED, e.CONFIG, *e.TOOLCHAIN]:
            self.assertIn(path, bindings)
        for suite, pin in e.SUITES.items():
            self.assertIn(e.workflow_path(suite), bindings)
            for name in e.archive_members(suite) | {'source.zip', 'actions.json'}:
                self.assertIn(f'{e.DIRECTORY}/{suite}/{pin["run_id"]}/{name}', bindings)

    def test_archive_digest_rejects_even_one_appended_byte(self):
        for suite, pin in e.SUITES.items():
            path = e.ROOT / e.DIRECTORY / suite / str(pin['run_id']) / 'source.zip'
            with self.subTest(suite=suite), self.assertRaises(e.base.EvidenceError):
                e.unpack(path.read_bytes() + b'x', suite)

    def test_archive_cannot_be_substituted_by_another_success(self):
        pin = e.SUITES['p03_learning']
        raw = (e.ROOT / e.DIRECTORY / 'p03_learning' / str(pin['run_id']) / 'source.zip').read_bytes()
        with self.assertRaises(e.base.EvidenceError):
            e.unpack(raw, 'p05_controller')

    def test_job_json_must_equal_accepted_json(self):
        for suite in e.SUITES:
            files = dict(self.payloads[suite]); files['job.stdout.json'] = b'{}'
            self.reject_payload(files, suite)

    def test_original_raw_streams_cannot_be_silently_rewritten(self):
        for suite in e.SUITES:
            files = dict(self.payloads[suite]); label = e.labels(suite)[0]
            files[label + '.stderr'] += b'new warning'
            self.reject_payload(files, suite)

    def test_missing_and_extra_members_fail_closed(self):
        for suite in e.SUITES:
            files = dict(self.payloads[suite]); files.pop('compile.stderr')
            self.reject_payload(files, suite)
            files = dict(self.payloads[suite]); files['failure.json'] = b'{}'
            self.reject_payload(files, suite)

    def test_duplicate_and_non_utf8_stdout_rejected(self):
        for suite in e.SUITES:
            for bad in (b'{"status":"PASS","status":"PASS"}', b'\xff', b'{"x":NaN}'):
                files = dict(self.payloads[suite]); files[e.labels(suite)[0] + '.stdout'] = bad
                self.reject_payload(files, suite)

    def test_controller_actual_process_must_exit_zero(self):
        suite = 'p05_controller'; files = dict(self.payloads[suite])
        name = e.labels(suite)[0] + '.process.json'
        process = e.witness.strict_json(files[name]); process['returncode'] = -11
        files[name] = e.base.stable(process)
        self.reject_payload(files, suite)

    def test_controller_timeout_cannot_hide_behind_pass_stdout(self):
        files = dict(self.payloads['p05_controller']); name = 'dragonize_ghost.process.json'
        process = e.witness.strict_json(files[name]); process['timed_out'] = True
        files[name] = e.base.stable(process)
        self.reject_payload(files, 'p05_controller')

    def test_compile_failure_timeout_or_flag_change_rejected(self):
        for field, value in [('returncode', 1), ('timed_out', True), ('command', ['cc', '-o', 'fake'])]:
            files = dict(self.payloads['p05_controller']); process = e.witness.strict_json(files['compile.process.json'])
            process[field] = value; files['compile.process.json'] = e.base.stable(process)
            self.reject_payload(files, 'p05_controller')

    def test_controller_wrong_case_command_rejected(self):
        files = dict(self.payloads['p05_controller']); name = 'dragonize_ghost.process.json'
        process = e.witness.strict_json(files[name]); process['command'][-1] = 'no_ability_ghost'
        files[name] = e.base.stable(process)
        self.reject_payload(files, 'p05_controller')

    def test_negative_guards_are_not_successful_runtime_cases(self):
        files = dict(self.payloads['p05_scheduler']); files['guard-bus8.stderr'] = b''
        self.reject_payload(files, 'p05_scheduler')
        self.assertEqual(len(self.payloads['p05_scheduler']), 68)

    def test_required_steps_must_succeed_not_skip(self):
        for suite in e.SUITES:
            actions = deepcopy(self.actions[suite]); actions['required_steps'][0]['conclusion'] = 'skipped'
            with self.assertRaises(e.base.EvidenceError): e.validate_actions(actions, suite)

    def test_required_steps_must_be_unique_complete_and_ordered(self):
        for transform in (lambda rows: rows.pop(), lambda rows: rows.append(rows[0]), lambda rows: rows.reverse()):
            actions = deepcopy(self.actions['p05_controller']); transform(actions['required_steps'])
            with self.assertRaises(e.base.EvidenceError): e.validate_actions(actions, 'p05_controller')

    def test_execution_sources_must_include_workflow_and_toolchain(self):
        actions = deepcopy(self.actions['p03_learning']); actions['verified_execution_sources'].pop(e.TOOLCHAIN[0])
        with self.assertRaises(e.base.EvidenceError): e.validate_actions(actions, 'p03_learning')

    def test_changed_registered_source_is_rejected(self):
        regular = e.base.regular
        for target in [e.ROM, e.SEED, 'tools/mgba_modernization_p05_controller_witness.c',
                       'tools/mgba_modernization_p03_learning_e2e.c', e.TOOLCHAIN[0]]:
            def changed(root, path):
                raw = regular(root, path)
                return raw + b'x' if path == target else raw
            with self.subTest(path=target), patch.object(e.base, 'regular', side_effect=changed):
                with self.assertRaises(e.base.EvidenceError): e.build_extension()

    def test_p08_attachment_is_idempotent_and_preserves_stage79_layer(self):
        path = 'content/modernization/p08_runtime_handoff.json'
        document = json.loads((e.ROOT / path).read_bytes())
        original = {k: v for k, v in document.items() if k not in e.KEYS}
        outputs = e.attach_outputs({path: e.base.stable(original)})
        self.assertEqual(outputs, e.attach_outputs(outputs))
        attached = json.loads(outputs[path]); e.validate_document(attached, self.actual)
        self.assertEqual({k: v for k, v in attached.items() if k not in e.KEYS}, original)

    def test_stale_layer_or_binding_is_rejected(self):
        path = 'content/modernization/p08_runtime_handoff.json'
        original = json.loads((e.ROOT / path).read_bytes())
        for key in e.KEYS:
            altered = deepcopy(original); altered.pop(key)
            with self.assertRaises(e.base.EvidenceError): e.validate_document(altered, self.actual)

    def test_no_registration_is_only_allowed_for_historical_builder_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = {'historical.json': b'{}'}
            self.assertEqual(e.attach_outputs(raw, root), raw)
            with self.assertRaises(e.base.EvidenceError): e.build_extension(root)

    def test_false_and_zero_are_not_interchangeable(self):
        with self.assertRaises(e.base.EvidenceError): e.exact(False, 0, 'boolean contract')
        with self.assertRaises(e.base.EvidenceError): e.exact({'flag': False}, {'flag': 0}, 'nested boolean')


def _payload_test(suite, mutation):
    def test(self): self.reject_payload(self.payload_change(suite, mutation), suite)
    return test


for _suite in e.SUITES:
    for _name, _mutation in {
        'release_promotion': lambda r: r.update(release_ready=True),
        'cached_pass': lambda r: r.update(cached_results_reused=1),
        'wrong_count': lambda r: r.update(fresh_process_runs=999),
        'bool_count': lambda r: r.update(fresh_process_runs=True),
        'missing_case': lambda r: r['cases'].pop(),
        'duplicate_case': lambda r: r['cases'].append(r['cases'][0]),
        'nonzero_exit': lambda r: r['cases'][0].update(returncode=-11),
        'bool_exit': lambda r: r['cases'][0].update(returncode=False),
        'wrong_rom': lambda r: r['rom'].update(sha256='0' * 64),
        'baseline_promotion': lambda r: r.update(active_baseline_changed=True),
    }.items():
        setattr(RepresentativeEvidenceTests, f'test_{_suite}_{_name}', _payload_test(_suite, _mutation))


def _actions_test(field):
    def test(self):
        for suite in e.SUITES:
            actions = deepcopy(self.actions[suite]); actions[field] = 'wrong'
            with self.assertRaises(e.base.EvidenceError): e.validate_actions(actions, suite)
    return test


for _field in ('repository', 'head_branch', 'head_sha', 'run_id', 'run_attempt', 'status',
               'conclusion', 'workflow_path', 'artifact_id', 'artifact_digest',
               'artifact_run_id', 'artifact_head_sha', 'job_id', 'job_conclusion'):
    setattr(RepresentativeEvidenceTests, 'test_provenance_' + _field, _actions_test(_field))


if __name__ == '__main__':
    unittest.main()
