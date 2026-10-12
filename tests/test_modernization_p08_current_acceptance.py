"""P08の現在残件を原本証跡から再検証する回帰テスト。"""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import check_modernization_p08_current_acceptance as audit
from tools import modernization_p08_stage79_evidence as evidence


class CurrentAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 実checkoutのROM・runner・生ログ・Actions原本を検証。mGBA再実行ではない。
        cls.actual = audit.build_report()
        cls.extension = json.loads((audit.ROOT / audit.DOCUMENTS[0]).read_text())['current_cumulative_runtime']
        cls.originals = {path: (audit.ROOT / path).read_bytes() for path in cls.actual['source_bindings']}

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for path, raw in self.originals.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        self.current = deepcopy(self.extension)
        # Unitの改変注入用。実checkout検証はsetUpClassで省略せず一度実行する。
        self.validator = patch.object(evidence, 'build_extension', return_value=self.current)
        self.representative_validator = patch.object(audit.representative, 'build_extension',
            return_value=deepcopy(self.actual['representative_e2e']))
        self.native_validator = patch.object(audit.native, 'build_extension',
            return_value=deepcopy(self.actual.get('native_pp_acceptance')))
        self.native_validator.start()
        self.addCleanup(self.native_validator.stop)
        self.representative_validator.start()
        self.addCleanup(self.representative_validator.stop)
        self.validator.start()
        self.addCleanup(self.validator.stop)

    def edit(self, path, transform):
        target = self.root / path
        document = json.loads(target.read_bytes())
        transform(document)
        target.write_bytes(evidence.stable(document))

    def build(self):
        return audit.build_report(self.root)

    def rejects(self):
        with self.assertRaises((evidence.EvidenceError, KeyError, TypeError, ValueError, OSError)):
            self.build()

    def test_actual_evidence_is_seven_domains_but_release_is_blocked(self):
        self.assertEqual(self.actual['satisfied_runtime_domains'], list(evidence.DOMAINS))
        self.assertEqual(self.actual['validation_status'], 'PASS')
        self.assertEqual(self.actual['acceptance_status'], 'BLOCKED')
        self.assertIs(self.actual['release_ready'], False)
        self.assertIs(self.actual['heavy_execution_performed'], False)
        self.assertEqual(self.actual['candidate_stage'], 81 if (audit.ROOT / audit.native.CONFIG).exists() else 80)
        self.assertEqual(self.actual['active_baseline_stage'], 62)

    def test_p03_and_p05_false_flags_stay_blocking(self):
        ids = {b['id'] for b in self.actual['current_blockers']}
        for key in ['P03_SCHEDULER_E2E_PENDING', 'P03_BREEDING_E2E_PENDING',
                    'P03_SAVE_RELOAD_E2E_PENDING', 'P03_FULL_ACCEPTANCE_PENDING',
                    'P05_SCHEDULER_E2E_PENDING', 'P05_FULL_ACCEPTANCE_PENDING']:
            self.assertIn(key, ids)

    def test_history_is_preserved_but_is_not_the_current_blocker_list(self):
        report = self.build()
        historical = json.loads(self.originals[audit.DOCUMENTS[0]])['release_blockers']
        self.assertEqual(report['historical_stage77']['release_blockers'], historical)
        ids = {b['id'] for b in report['current_blockers']}
        self.assertFalse(ids.intersection(historical))
        self.assertFalse(any(b['phase'] in ('P02', 'P04') for b in report['current_blockers']))
        self.assertIs(report['eelevate_switch_ai_done'], True)

    def test_empty_adoption_is_not_approval(self):
        report = self.build()
        self.assertEqual(report['p06_adoption'], {'review_record_count': 194, 'adopted_delta_count': 0})
        self.assertEqual(report['p07_adoption']['normal_species_to_vega_move_adopted'], 0)
        self.assertEqual(report['p07_adoption']['vega_species_to_normal_move_adopted'], 0)
        ids = {b['id'] for b in report['current_blockers']}
        self.assertIn('P06_SPECIES_ADJUSTMENT_NOT_ADOPTED', ids)
        self.assertIn('P07_CROSS_DISTRIBUTION_NOT_ADOPTED', ids)

    def test_build_is_deterministic_and_read_only(self):
        before = {p: ((self.root / p).read_bytes(), (self.root / p).stat().st_mtime_ns)
                  for p in self.originals}
        self.assertEqual(self.build(), self.build())
        self.assertEqual(before, {p: ((self.root / p).read_bytes(), (self.root / p).stat().st_mtime_ns)
                                 for p in self.originals})

    def test_source_bindings_cover_every_current_blocker(self):
        report = self.build()
        for blocker in report['current_blockers']:
            self.assertIn(blocker['source_path'], report['source_bindings'])
            self.assertTrue(blocker['source_pointer'].startswith('/'))

    def test_declared_unclaimed_coverage_is_not_fabricated_as_done(self):
        self.assertEqual(self.actual['unclaimed_coverage'],
                         {'link_runtime_e2e': False, 'physical_all_menu_paths_e2e': False})
        self.assertIs(self.actual['phase_completion_promoted'], False)

    def test_missing_registered_runtime_is_not_ignored(self):
        with patch.object(evidence, 'build_extension', side_effect=evidence.EvidenceError('missing')):
            self.rejects()

    def test_stale_extension_in_each_p08_document_is_rejected(self):
        for path in audit.DOCUMENTS:
            with self.subTest(path=path):
                self.edit(path, lambda d: d['current_cumulative_runtime'].update(candidate_stage=78))
                self.rejects()
                (self.root / path).write_bytes(self.originals[path])

    def test_release_promotion_is_rejected_in_each_handoff(self):
        for path in audit.DOCUMENTS:
            with self.subTest(path=path):
                self.edit(path, lambda d: d.update(release_ready=True))
                self.rejects()
                (self.root / path).write_bytes(self.originals[path])

    def test_tampered_historical_blockers_are_rejected(self):
        self.edit(audit.DOCUMENTS[0], lambda d: d.update(release_blockers=[]))
        self.rejects()

    def test_tampered_binding_is_rejected(self):
        self.edit(audit.DOCUMENTS[1], lambda d: d['cumulative_evidence_binding'].update(sha256='0' * 64))
        self.rejects()

    def test_missing_historical_scope_is_rejected(self):
        self.edit(audit.DOCUMENTS[2], lambda d: d.pop('historical_checkpoint_scope'))
        self.rejects()

    def test_p03_false_cannot_be_relabelled_as_true(self):
        path = next(r['result_path'] for r in self.current['domains'] if r['id'] == 'p03')
        self.edit(path, lambda d: d['runner_result'].update(save_reload_e2e=True))
        self.rejects()

    def test_p05_false_cannot_be_relabelled_as_true(self):
        path = next(r['result_path'] for r in self.current['domains'] if r['id'] == 'p05')
        self.edit(path, lambda d: d['runner_result'].update(full_p05_acceptance=True))
        self.rejects()

    def test_missing_and_symlink_evidence_are_rejected(self):
        path = self.current['domains'][0]['result_path']
        target = self.root / path
        target.unlink()
        self.rejects()
        target.symlink_to(audit.ROOT / path)
        self.rejects()

    def test_p06_count_cannot_replace_actual_adopted_rows(self):
        self.edit(audit.P06, lambda d: d['adoption'].update(adopted_delta_count=194))
        self.rejects()

    def test_p06_review_cannot_authorize_runtime(self):
        self.edit(audit.P06, lambda d: d['adoption'].update(runtime_patch_authorized=True))
        self.rejects()

    def test_p06_new_adoption_requires_new_acceptance_policy(self):
        self.edit(audit.P06, lambda d: d['adoption'].update(adopted_delta_count=1,
                  adopted_delta_records=[{'species_key': 'example'}],
                  explicit_species_adjustment_spec_received=True, runtime_patch_authorized=True))
        self.rejects()

    def test_p06_projection_tampering_is_rejected(self):
        path = json.loads(self.originals[audit.P06])['review_partition']['projection_path']
        self.edit(path, lambda d: d['records'].pop())
        self.rejects()

    def test_p07_contract_and_handoff_must_agree(self):
        self.edit(audit.P07_HANDOFF, lambda d: d['summary'].update(runtime_implemented=True))
        self.rejects()

    def test_p07_rows_cannot_hide_behind_zero_counts(self):
        self.edit(audit.P07, lambda d: d['adopted_delta']['normal_species_to_vega_move'].append({'move': 1}))
        self.rejects()

    def test_p07_invented_rows_are_rejected(self):
        self.edit(audit.P07, lambda d: d['adopted_delta']['invented_rows'].append({'move': 1}))
        self.rejects()

    def test_economy_cannot_be_finalized_without_policy_update(self):
        self.edit(audit.ECONOMY, lambda d: d['runtime']['economy'].update(status='FINAL'))
        self.rejects()

    def test_boolean_values_are_strict(self):
        for value in [None, 0, 1, 'false', 'true', [], {}]:
            with self.subTest(value=value), self.assertRaises(evidence.EvidenceError):
                audit.boolean({'flag': value}, 'flag')
        self.assertIs(audit.boolean({'flag': False}, 'flag'), False)
        self.assertIs(audit.boolean({'flag': True}, 'flag'), True)

    def test_counts_are_nonnegative_integers_not_booleans(self):
        for value in [None, False, True, -1, '0', 0.0]:
            with self.subTest(value=value), self.assertRaises(evidence.EvidenceError):
                audit.count({'count': value}, 'count')

    def cli(self, args):
        stdout = SimpleNamespace(buffer=io.BytesIO())
        with patch.object(audit, 'ROOT', self.root), patch.object(audit, 'build_report', return_value=self.actual), \
             patch.object(audit.sys, 'stdout', stdout), patch.object(audit.sys, 'stderr', io.StringIO()):
            code = audit.main(args)
        return code, stdout.buffer.getvalue()

    def test_check_is_read_only_and_rejects_stale_snapshot(self):
        target = self.root / audit.OUTPUT
        target.write_bytes(evidence.stable(self.actual))
        stamp = target.stat().st_mtime_ns
        self.assertEqual(self.cli(['--check'])[0], 0)
        self.assertEqual(target.stat().st_mtime_ns, stamp)
        target.write_text('{"release_ready":true}\n')
        self.assertEqual(self.cli(['--check'])[0], 2)
        self.assertEqual(target.read_text(), '{"release_ready":true}\n')

    def test_check_missing_snapshot_does_not_create_one(self):
        self.assertEqual(self.cli(['--check'])[0], 2)
        self.assertFalse((self.root / audit.OUTPUT).exists())

    def test_write_is_explicit_and_roundtrips(self):
        self.assertEqual(self.cli([])[0], 0)
        self.assertFalse((self.root / audit.OUTPUT).exists())
        self.assertEqual(self.cli(['--write'])[0], 0)
        self.assertEqual((self.root / audit.OUTPUT).read_bytes(), evidence.stable(self.actual))
        self.assertEqual(self.cli(['--check'])[0], 0)

    def test_release_gate_fails_even_when_consistency_check_passes(self):
        (self.root / audit.OUTPUT).write_bytes(evidence.stable(self.actual))
        code, output = self.cli(['--check', '--require-release-ready'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)['validation_status'], 'PASS')
        self.assertIs(json.loads(output)['release_ready'], False)

    def test_write_refuses_symlink_snapshot(self):
        external = self.root / 'external.json'
        external.write_text('keep')
        (self.root / audit.OUTPUT).symlink_to(external)
        self.assertEqual(self.cli(['--write'])[0], 2)
        self.assertEqual(external.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
