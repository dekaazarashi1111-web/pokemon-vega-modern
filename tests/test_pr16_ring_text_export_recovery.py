"""実行済みRingは起動せず、text exportと保存receiptの失敗閉鎖を検査。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_text_export_recovery as t


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'bundle'
        self.files = {'scripts/a.py': '日本語😀\n'.encode() * 100, 'data.json': b'{"x":1}\n'}
    def make(self):
        with patch.object(t, 'CHARS', 60): return t.bundle(self.files, self.path)
    def mutate(self, fn):
        m = self.make(); fn(m)
        (self.path / 'manifest.json').write_bytes(t.stable(m))
        with self.assertRaises((ValueError, KeyError)): t.unbundle(self.path)
    def test_roundtrip(self): self.make(); self.assertEqual(t.unbundle(self.path), self.files)
    def test_unicode_shards(self):
        m = self.make(); self.assertGreater(len(m['files']['scripts/a.py']['parts']), 1)
    def test_empty_text(self):
        t.bundle({'empty.txt': b''}, self.path); self.assertEqual(t.unbundle(self.path), {'empty.txt': b''})
    def test_empty_map_rejected(self):
        with self.assertRaises(ValueError): t.bundle({}, self.path)
    def test_null_rejected(self):
        with self.assertRaises(ValueError): t.bundle({'a.txt': b'x\0y'}, self.path)
    def test_nonutf8_rejected(self):
        with self.assertRaises(UnicodeError): t.bundle({'a.txt': b'\xff'}, self.path)
    def test_secret_rejected_before_split(self):
        with patch.object(t, 'CHARS', 8):
            with self.assertRaises(ValueError): t.bundle({'a.txt': b'ghp_' + b'a' * 36}, self.path)
    def test_private_key_rejected(self):
        with self.assertRaises(ValueError): t.bundle({'a.txt': b'-----BEGIN RSA ' + b'PRIVATE KEY-----'}, self.path)
    def test_traversal_rejected(self):
        with self.assertRaises(ValueError): t.bundle({'../a.txt': b''}, self.path)
    def test_absolute_rejected(self):
        with self.assertRaises(ValueError): t.bundle({'/a.txt': b''}, self.path)
    def test_binary_suffix_rejected(self):
        with self.assertRaises(ValueError): t.bundle({'a.gba': b'rom'}, self.path)
    def test_no_overwrite(self):
        self.make()
        with self.assertRaises(ValueError): t.bundle(self.files, self.path)
    def test_logical_size(self):
        with patch.object(t, 'MAX_LOGICAL', 2):
            with self.assertRaises(ValueError): t.bundle(self.files, self.path)
    def test_total_size(self):
        with patch.object(t, 'MAX_TOTAL', 2):
            with self.assertRaises(ValueError): t.bundle(self.files, self.path)
    def test_member_size(self):
        with patch.object(t, 'MAX_MEMBER', 30):
            with self.assertRaises(ValueError): self.make()
    def test_extra_member(self):
        self.make(); (self.path / 'extra.json').write_text('{}')
        with self.assertRaises(ValueError): t.unbundle(self.path)
    def test_symlink(self):
        self.make(); (self.path / 'extra.json').symlink_to(self.path / 'manifest.json')
        with self.assertRaises(ValueError): t.unbundle(self.path)
    def test_hash_mutation(self): self.mutate(lambda m: m['files']['data.json']['identity'].update(size=1))
    def test_part_hash_mutation(self): self.mutate(lambda m: m['files']['data.json']['parts'][0]['identity'].update(size=1))
    def test_part_missing(self): self.mutate(lambda m: m['files']['data.json']['parts'][0].update(path='file-9999-part-9999.json'))
    def test_part_duplicate(self): self.mutate(lambda m: m['files']['scripts/a.py']['parts'].append(m['files']['data.json']['parts'][0]))
    def test_part_traversal(self): self.mutate(lambda m: m['files']['data.json']['parts'][0].update(path='../a.json'))
    def test_schema(self): self.mutate(lambda m: m.update(schema_version=2))
    def test_above_original_limit_roundtrip(self):
        raw = b'x' * (t.MAX_MEMBER + 1)
        m = t.bundle({'large.txt': raw}, self.path)
        self.assertEqual(t.unbundle(self.path)['large.txt'], raw)
        self.assertTrue(all(p.stat().st_size <= t.MAX_MEMBER for p in self.path.iterdir()))


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tests = dict(tests_run=49, failures=0, errors=0, skips=0, successful=True)
        self.prior = {'source_head': t.SOURCE, 'run_id': t.RUN, 'focused_tests': self.tests,
                      'analysis': dict(contract_cases=333, conditional_return_cases=303, pending_stop_cases=30,
                                       ring_acquisition_accepted=False, release_ready=False, rom_changes=0, new_emulator_processes=0)}
        self.run = dict(id=t.RUN, head_sha=t.SOURCE, status='completed', conclusion='failure')
        self.jobs = [dict(id=t.JOB, conclusion='failure', steps=[dict(number=n, conclusion=c) for n,c in ((3,'success'),(4,'failure'),(5,'skipped'))])]
        receipt = dict(status='PASS_RECORDED_NONFORCE_PUSHED', commit=t.BASE, source_head=t.SOURCE, run_id=t.RUN,
                       tests=self.tests, new_emulator_processes=0, ring_acquisition_accepted=False, release_ready=False)
        self.log = ('RESULT=DONE TASK=PR-P08-7-RING-TEXT-AUDIO-SEQUENCE VERIFY=PASS COMMIT=' + t.BASE + '\n'
                    + json.dumps(receipt) + '\nFile "<stdin>", line 7\nAssertionError')
    def verify(self): return t.verify_receipt(self.prior,self.run,self.jobs,self.log)
    def test_original_failure_preserved(self):
        r=self.verify(); self.assertEqual(r['original_conclusion'],'failure'); self.assertFalse(r['original_failure_reclassified_as_success'])
    def test_no_replay(self): self.assertEqual(self.verify()['accepted_cases_replayed'],0)
    def test_run_sha(self):
        self.run['head_sha']='0'*40
        with self.assertRaises(ValueError):self.verify()
    def test_conclusion_not_rewritten(self):
        self.run['conclusion']='success'
        with self.assertRaises(ValueError):self.verify()
    def test_failed_verification_not_recovered(self):
        self.jobs[0]['steps'][0]['conclusion']='failure'
        with self.assertRaises(ValueError):self.verify()
    def test_wrong_count(self):
        self.prior['analysis']['contract_cases']=334
        with self.assertRaises(ValueError):self.verify()
    def test_missing_receipt(self):
        self.log='AssertionError'
        with self.assertRaises(ValueError):self.verify()
    def test_duplicate_receipt(self):
        self.log += '\n'+self.log
        with self.assertRaises(ValueError):self.verify()
    def test_scope_promotion_rejected(self):
        self.prior['analysis']['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):self.verify()
    def test_inputs_immutable(self):
        old=copy.deepcopy((self.prior,self.run,self.jobs));self.verify();self.assertEqual(old,(self.prior,self.run,self.jobs))

if __name__ == '__main__': unittest.main()
