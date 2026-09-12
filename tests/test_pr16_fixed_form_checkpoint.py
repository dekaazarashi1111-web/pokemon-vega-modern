"""Offline evidence integrity tests; no mGBA, network, or acceptance promotion."""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_fixed_form_checkpoint as keep

PIN = dict(run_id=34697100492, job_id=103562346678, artifact_id=10299570880,
           head='c38d5dae3ac1c73d65b891e5b2f525267caa7b2d', size=978963,
           sha256='8d2e0461baec89b8082ce8af7715efd38e7c4c07525931f4d26381e06100d2a6',
           cases=list(keep.fixed.CASES)[:2], conclusion='failure')


class FixedFormCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / keep.originals.BASE / str(PIN['run_id']) / 'original.zip').read_bytes()

    def test_retained_failed_native_run_is_not_a_pass(self):
        result, receipt = keep.validate(self.raw, PIN)
        self.assertEqual(result['actual_new_processes'], 2)
        self.assertEqual(len(result['failures']), 2)
        self.assertEqual(result['results'], [])
        self.assertFalse(receipt['p03_fixed_form_gap_closed'])

    def test_successful_crowned_original_remains_valid_without_reexecution(self):
        pin = keep.originals.PINS[-1]
        binding = dict(run_id=pin[0], job_id=pin[1], artifact_id=pin[2], head=pin[3],
                       size=pin[4], sha256=pin[5], cases=list(keep.fixed.CASES)[-2:], conclusion='success')
        raw = (ROOT / keep.originals.BASE / str(pin[0]) / 'original.zip').read_bytes()
        result, receipt = keep.validate(raw, binding)
        self.assertEqual(len(result['results']), 2)
        self.assertFalse(receipt['p03_fixed_form_gap_closed'])

    def test_pin_strict_types_and_finite_case_set(self):
        for key, value in (('run_id', True), ('size', 0), ('size', 32000001),
                           ('head', 'main'), ('sha256', 'A' * 64),
                           ('cases', []), ('cases', PIN['cases'] * 2),
                           ('cases', PIN['cases'][::-1]), ('conclusion', 'queued')):
            pin = copy.deepcopy(PIN)
            pin[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                keep.pin_check(pin)
        for key in PIN:
            pin = copy.deepcopy(PIN)
            del pin[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                keep.pin_check(pin)

    def test_strict_json_rejects_duplicate_nested_keys_and_nonfinite(self):
        for raw in (b'{"a":1,"a":2}', b'{"x":{"a":1,"a":2}}', b'{"n":NaN}', b'{"n":Infinity}'):
            with self.assertRaises(ValueError):
                keep.strict(raw)

    def test_process_receipt_is_not_python_truthiness(self):
        row = dict(schema_version=1, returncode=0, spawn_error=None, timed_out=False)
        self.assertEqual(keep.process(keep.fixed.stable(row), 0), row)
        for key, value in (('returncode', False), ('returncode', 0.0),
                           ('timed_out', 0), ('schema_version', True),
                           ('spawn_error', ''), ('returncode', 1)):
            bad = dict(row, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                keep.process(keep.fixed.stable(bad), 0)

    def test_raw_original_identity_is_mandatory(self):
        for raw in (self.raw + b'padding', self.raw[:-1], b''):
            with self.assertRaises(ValueError):
                keep.validate(raw, PIN)

    def test_commit_source_must_equal_archived_source(self):
        with self.assertRaisesRegex(ValueError, 'tested commit source differs'):
            keep.validate(self.raw, PIN, source_reader=lambda head, path: b'forged source')

    def forge_report(self, mutate):
        with zipfile.ZipFile(io.BytesIO(self.raw)) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        path = keep.PREFIX + 'result.json'
        report = json.loads(members[path])
        mutate(report)
        members[path] = keep.fixed.stable(report)
        receipt_path = keep.PREFIX + 'receipt.json'
        receipt = json.loads(members[receipt_path])
        receipt['members']['result.json'] = keep.identity(members[path])
        members[receipt_path] = keep.fixed.stable(receipt)
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)
        raw = data.getvalue()
        return raw, dict(PIN, **keep.identity(raw))

    def test_rehashed_envelope_cannot_inflate_or_omit_native_cases(self):
        mutations = (
            lambda r: r.update(p03_fixed_form_gap_closed=True),
            lambda r: r.update(release_ready=True),
            lambda r: r.update(actual_new_processes=0),
            lambda r: r.update(old_runs_relabelled=1),
            lambda r: r.update(guard_checks=r['guard_checks'][:-1]),
            lambda r: r.update(requested_cases=r['requested_cases'][:-1]),
            lambda r: r.update(failures=r['failures'][:-1]),
            lambda r: r.update(status='PASS_SCOPED_PENDING_FIVE_CASES'),
        )
        for mutate in mutations:
            raw, pin = self.forge_report(mutate)
            with self.assertRaises(ValueError):
                keep.validate(raw, pin)


if __name__ == '__main__':
    unittest.main()
