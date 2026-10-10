"""保存原本と新receiptだけ。旧32/184試験、ROM再構成、CPUモデルを呼ばない。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_weather_bubble_receipt as r


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {n:r.regular(ROOT,r.EVIDENCE+'/'+n) for n in r.FILES}
        # この新試験プロセスで保存親を1度だけ復元。測定/旧suiteではない。
        cls.parent = r.parent(ROOT)
        cls.delta = r.build(cls.parent,cls.files)
        cls.full = r.materialize(cls.parent,cls.delta,cls.files)

    def test_exact_originals(self):
        values = r.verify_files(self.files)
        self.assertEqual(values['tests.json']['tests_run'],32)
        self.assertFalse(values['measurement.json']['formal_classification_accepted'])

    def test_current_source_bindings(self):
        r.verify_sources(r.verify_files(self.files),ROOT)

    def test_singleton_only_and_all_873_rows_retained(self):
        self.assertEqual((self.full['classified'],self.full['unclassified'],len(self.full['hits'])),(784,90,874))
        changes = [(a,b) for a,b in zip(self.parent['hits'],self.full['hits']) if not r.exact(a,b)]
        self.assertEqual(len(changes),1)
        self.assertEqual(changes[0][0]['address'],0x0838B32F)
        self.assertEqual(r.identity(r.previous.canonical(self.parent)),r.previous.PARENT_AUDIT_ID)

    def test_all_old_namespaces_and_safety_claims(self):
        self.assertEqual(len(r.previous.INHERITED_NAMES),30)
        for name in r.previous.INHERITED_NAMES:
            self.assertTrue(r.exact(self.parent[name],self.full[name]))
        self.assertNotIn(r.previous.NAMESPACE,self.full)
        for name in ('donor_eligible','donor_leased','indirect_reference_completeness_claimed'):
            self.assertIs(self.full[name],False)

    def test_frontier_retains_remaining_full_rows_and_order(self):
        frontier = r.frontier(self.full)
        expected = [h for h in self.parent['hits'] if not h['accepted'] and h['address'] != r.model.HIT]
        self.assertTrue(r.exact([row['hit'] for row in frontier['rows']],expected))
        self.assertEqual(frontier['total'],90)
        self.assertIn(0x083D6B61,[h['address'] for h in expected])

    def test_repeated_application_rejected(self):
        with self.assertRaises(ValueError): r.build(self.full,self.files)

    def test_diagnostic_namespace_contamination_rejected(self):
        bad = dict(self.parent,blastoise_reference_chain={})
        with self.assertRaises(ValueError): r.build(bad,self.files)

    def test_parent_counter_tampering_rejected(self):
        with self.assertRaises(ValueError): r.build(dict(self.parent,classified=784),self.files)

    def test_missing_extra_and_renamed_originals(self):
        for name in r.FILES:
            bad = dict(self.files); del bad[name]
            with self.assertRaises(ValueError): r.verify_files(bad)
        with self.assertRaises(ValueError): r.verify_files(dict(self.files,extra=b'{}'))

    def test_zip_rejects_unpinned_and_appended_envelopes(self):
        for raw in (b'',b'PK',b'{}',r.canonical(self.delta)):
            with self.assertRaises(ValueError): r.unpack(raw)

    def test_json_rejects_ambiguous_values(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1.0}',b'\x00',b'\xff',b'{} {}'):
            with self.assertRaises((ValueError,UnicodeError)): r.read(raw)

    def test_deep_type_strictness(self):
        for a,b in ((False,0),(True,1),([1],(1,)),({'a':False},{'a':0}),(0,0.0)):
            self.assertFalse(r.exact(a,b))

    def test_regular_file_rejects_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'ok.json').write_bytes(b'{}')
            (root/'alias.json').symlink_to(root/'ok.json')
            self.assertEqual(r.regular(root,'ok.json'),b'{}')
            for name in ('../ok.json','/ok.json','./ok.json','alias.json','missing.json'):
                with self.assertRaises(ValueError): r.regular(root,name)

    def test_no_measurement_or_old_test_execution(self):
        with patch.object(r.model,'measure',side_effect=AssertionError('remeasure')),patch.object(r.model,'compose',side_effect=AssertionError('reader replay')):
            self.assertTrue(r.exact(r.build(self.parent,self.files),self.delta))

    def test_log_hashes_and_order(self):
        first = dict(status='PASS_CURRENT_BUBBLE_BEFORE_PUBLICATION',files=r.FILES,
                     context=dict(source_head=r.HEAD,run_id=r.RUN),formal_acceptance=False)
        second = dict(status='PASS_CLOSED_FOUR_BUBBLE_JSON',files=r.FILES)
        a,b = json.dumps(first).encode()+b'\n',json.dumps(second).encode()+b'\n'
        self.assertEqual(r.verify_log(a+b)['published_file_identities'],r.FILES)
        for bad in (a,b,b+a,a+a+b):
            with self.assertRaises(ValueError): r.verify_log(bad)
        changed = copy.deepcopy(second); changed['files']['measurement.json']['size'] += 1
        with self.assertRaises(ValueError): r.verify_log(a+json.dumps(changed).encode())

    def test_delta_extra_and_missing_fields(self):
        with self.assertRaises(ValueError): r.materialize(self.parent,dict(self.delta,unknown=True),self.files)
        bad = dict(self.delta); del bad['claims']
        with self.assertRaises(ValueError): r.materialize(self.parent,bad,self.files)

    def test_target_geometry_and_witness_identity(self):
        for field in ('address','size','id'):
            bad = copy.deepcopy(self.delta); bad['witnesses'][0][field] += 1
            with self.assertRaises(ValueError): r.materialize(self.parent,bad,self.files)
        bad = copy.deepcopy(self.delta); bad['changes'][0]['witness_ids'] = [True]
        with self.assertRaises(ValueError): r.materialize(self.parent,bad,self.files)


def add_original_test(name):
    def test(self):
        changed = dict(self.files); changed[name] += b' '
        with self.assertRaises(ValueError): r.verify_files(changed)
    setattr(ReceiptTests,'test_original_bytes_'+name.replace('.','_'),test)


def add_delta_test(key):
    def test(self):
        changed = copy.deepcopy(self.delta); changed[key] += 1
        with self.assertRaises(ValueError): r.materialize(self.parent,changed,self.files)
        changed[key] = False
        with self.assertRaises(ValueError): r.materialize(self.parent,changed,self.files)
    setattr(ReceiptTests,'test_counter_'+key,test)


def add_claim_test(key):
    def test(self):
        changed = copy.deepcopy(self.delta); changed['claims'][key] = not changed['claims'][key]
        with self.assertRaises(ValueError): r.materialize(self.parent,changed,self.files)
    setattr(ReceiptTests,'test_claim_'+key,test)


for name in r.FILES: add_original_test(name)
for key in ('classified','unclassified','newly_classified','donor_safe_bytes','native_processes','old_full_rom_scan_runs','old_scope_test_reruns','measurement_replays'):
    add_delta_test(key)
for key in r.model.CLAIMS: add_claim_test(key)


if __name__ == '__main__': unittest.main()
