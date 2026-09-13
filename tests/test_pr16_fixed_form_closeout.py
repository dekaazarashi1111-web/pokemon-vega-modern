"""Source-only revalidation of retained originals; never starts mGBA."""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_fixed_form_closeout as close


class FixedFormCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archives = {p[0]: (ROOT / close.BASE / str(p[0]) / 'original.zip').read_bytes() for p in close.PINS}

    def edited(self, edit, pin=None):
        pin = pin or close.PINS[-1]
        with zipfile.ZipFile(io.BytesIO(self.archives[pin[0]])) as z:
            members = {n: z.read(n) for n in z.namelist()}
        edit(members)
        prefix = 'pr16-fixed-form-acceptance/'
        rec = close.load(members[prefix + 'receipt.json'])
        for name in rec['members']:
            if prefix + name in members:
                rec['members'][name] = close.identity(members[prefix + name])
        members[prefix + 'receipt.json'] = close.stable(rec)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, raw in members.items():
                z.writestr(name, raw)
        raw = stream.getvalue()
        custom = list(pin)
        custom[4:6] = [len(raw), close.identity(raw)['sha256']]
        return raw, tuple(custom)

    def reject_edit(self, edit):
        raw, pin = self.edited(edit)
        with self.assertRaises((ValueError, KeyError, zipfile.BadZipFile)):
            close.archive_valid(raw, pin)

    def test_all_five_real_original_cases_without_rerun(self):
        rows, records = [], []
        for pin in close.PINS:
            accepted, record = close.archive_valid(self.archives[pin[0]], pin)
            rows.extend(accepted)
            records.append(record)
        self.assertEqual({r['name'] for r in rows}, set(close.fixed.CASES))
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(r['result']['fresh_cores'] for r in rows), 11)
        self.assertEqual(records[0]['actions_conclusion'], 'failure')
        self.assertEqual(records[0]['failures_in_original_run'], 4)
        self.assertEqual(sum(r['actual_processes_in_original_run'] for r in records), 9)
        self.assertTrue(all(r['result']['aggregate_gap_closed'] is False for r in rows))

    def test_outer_archive_identity(self):
        for pin in close.PINS:
            with self.subTest(run=pin[0]), self.assertRaises(ValueError):
                close.archive_valid(self.archives[pin[0]] + b'x', pin)

    def test_exact_tested_head(self):
        pin = list(close.PINS[-1]); pin[3] = '0' * 40
        with self.assertRaises(ValueError):
            close.archive_valid(self.archives[pin[0]], tuple(pin))

    def test_guard_must_actually_reject_host_write(self):
        prefix = 'pr16-fixed-form-acceptance/'
        for key, data in [('guard-bus8.stderr', b''), ('guard-register.stdout', b'PASS'),
                          ('guard-raw32.process.json', close.stable(dict(schema_version=1, returncode=0, timed_out=False, spawn_error=None)))]:
            with self.subTest(member=key):
                self.reject_edit(lambda m, k=key, d=data: m.__setitem__(prefix+k, d))

    def test_stdout_not_just_plausible_report(self):
        def edit(members):
            name = 'pr16-fixed-form-acceptance/result.json'
            report = close.load(members[name])
            report['results'][0]['result']['four_slot_boundary'] = False
            members[name] = close.stable(report)
        self.reject_edit(edit)

    def test_raw_partial_claims_are_immutable(self):
        def edit(members):
            name = 'pr16-fixed-form-acceptance/result.json'
            report = close.load(members[name])
            report['p03_fixed_form_gap_closed'] = True
            members[name] = close.stable(report)
        self.reject_edit(edit)

    def test_process_boolean_timeout_and_skip_rejected(self):
        good = dict(schema_version=1, returncode=0, timed_out=False, spawn_error=None)
        close.process(good, 0)
        for key, value in [('schema_version', True), ('returncode', False), ('returncode', 77), ('timed_out', True), ('spawn_error', 'failed')]:
            bad = dict(good, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                close.process(bad, 0)

    def test_duplicate_nonfinite_metadata(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                close.load(raw)

    def test_receipt_missing_member(self):
        self.reject_edit(lambda m: m.pop('pr16-fixed-form-acceptance/compile.process.json'))

    def test_source_snapshot_members_not_just_zip_hash(self):
        def edit(members):
            source = io.BytesIO()
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('invented.py', 'pass\n')
            members['pr16-fixed-form-acceptance/sources.zip'] = source.getvalue()
        self.reject_edit(edit)

    def test_forbidden_or_traversal_archive_members(self):
        for name in ('evil.gba', '../escape.txt', 'user/save.sav'):
            with self.subTest(member=name):
                self.reject_edit(lambda m, n=name: m.__setitem__(n, b'not allowed'))

    def test_actions_bound_to_one_run_job_artifact(self):
        p = close.PINS[-1]
        data = dict(run=dict(id=p[0], head_sha=p[3], head_branch=close.BRANCH, status='completed', conclusion=p[6], run_attempt=1),
                    jobs=dict(jobs=[dict(id=p[1], run_id=p[0], status='completed', conclusion=p[6])]),
                    artifact=dict(id=p[2], size_in_bytes=p[4], digest='sha256:'+p[5], workflow_run=dict(id=p[0], head_sha=p[3])))
        close.actions_valid(data, p)
        for keys, value in [(('run', 'head_sha'), '0'*40), (('run', 'run_attempt'), 2),
                            (('artifact', 'id'), 1), (('artifact', 'digest'), 'sha256:'+'0'*64)]:
            bad = copy.deepcopy(data); bad[keys[0]][keys[1]] = value
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                close.actions_valid(bad, p)

    def test_p08_closes_only_fixed_form_and_is_idempotent(self):
        data = close.load((ROOT / close.P08).read_bytes())
        before = copy.deepcopy(data)
        updated = close.update_p08(data)
        p03 = next(r for r in updated['remaining_conditions'] if r['id'] == 'EVOLUTION_FORM_OTHER_EGG')
        self.assertEqual(p03['remaining_physical_gap_ids'], [])
        self.assertIn('P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL', p03['accepted_physical_gap_ids'])
        self.assertIn(close.GAP, p03['accepted_physical_gap_ids'])
        self.assertEqual([r for r in updated['remaining_conditions'] if r['id'] != p03['id']],
                         [r for r in before['remaining_conditions'] if r['id'] != p03['id']])
        for key in ('final_candidate', 'latest_scoped_candidate', 'full_p03_acceptance', 'full_p07_acceptance', 'release_ready', 'active_baseline_changed'):
            self.assertEqual(updated[key], before[key])
        self.assertEqual(close.update_p08(copy.deepcopy(updated)), updated)

    def test_p08_refuses_changed_scope_or_lost_generic_success(self):
        for key, value in [('remaining_physical_gap_ids', ['UNEXPECTED']), ('accepted_physical_gap_ids', [])]:
            data = close.load((ROOT / close.P08).read_bytes())
            row = next(r for r in data['remaining_conditions'] if r['id'] == 'EVOLUTION_FORM_OTHER_EGG')
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                close.update_p08(data)


if __name__ == '__main__':
    unittest.main()
