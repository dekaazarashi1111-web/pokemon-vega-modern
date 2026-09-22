"""保存証拠の拒否試験だけを実行。native/ARM/codec試験は呼ばない。"""
from __future__ import annotations
import copy
import json
import unittest
from scripts import pr16_learnset_compact_record as r


class RecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=r.inputs()
        cls.files={name:(r.ROOT/r.EVIDENCE/name).read_bytes() for name in cls.config['proof_files']}

    def altered(self,name,change):
        files=dict(self.files);config=copy.deepcopy(self.config)
        value=json.loads(files[name]);change(value);files[name]=r.encode(value)
        if name!='verification.json':
            outer=json.loads(files['verification.json'])
            outer['proof_files'][name]=r.identity(files[name])
            files['verification.json']=r.encode(outer)
        config['proof_files']={p:r.identity(b) for p,b in files.items()}
        return files,config

    def reject(self,name,change):
        with self.assertRaises(ValueError):r.validate(*self.altered(name,change))

    def test_exact_proof(self):
        self.assertEqual(r.validate(self.files,self.config)['candidate'],self.config['candidate'])
    def test_missing_member(self):
        files=dict(self.files);files.pop('link.json')
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_extra_member(self):
        with self.assertRaises(ValueError):r.validate(dict(self.files,unexpected=b'{}'),self.config)
    def test_hash_tamper(self):
        files=dict(self.files);files['link.json']+=b' '
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_no_gameplay_promotion(self):
        self.reject('verification.json',lambda x:x.update(gameplay_e2e_accepted=True))
    def test_no_archive_promotion(self):
        self.reject('verification.json',lambda x:x.update(archive_rebound=True))
    def test_no_tutor_promotion(self):
        self.reject('verification.json',lambda x:x.update(game_tutor_connected=True))
    def test_no_accepted_native_repeat(self):
        self.reject('verification.json',lambda x:x.update(accepted_native_reruns=1))
    def test_no_accepted_host_repeat(self):
        self.reject('verification.json',lambda x:x.update(accepted_tests_rerun=1))
    def test_native_process_count(self):
        self.reject('verification.json',lambda x:x.update(native_processes=1))
    def test_source_binding(self):
        self.reject('verification.json',lambda x:x.update(source_head='0'*40))
    def test_wrong_hook(self):
        self.reject('link.json',lambda x:x['hooks'][0].update(offset=0))
    def test_wrong_p07_delegate(self):
        self.reject('link.json',lambda x:x.update(p07_archive_delegate=0x0954B281))
    def test_extra_segment(self):
        self.reject('link.json',lambda x:x['segments'].append(x['segments'][0]))
    def test_allocation_overlap(self):
        def change(x):
            x['allocation']['allocations'][1]['start']=x['allocation']['allocations'][0]['start']
        self.reject('link.json',change)
    def test_native_pp_evidence(self):
        self.reject('native11.json',lambda x:x.update(stored_four_moves_and_pp_preserved=False))
    def test_false_semantic_equivalence(self):
        self.reject('compact-audit.json',lambda x:x.update(owner_order_count_payload_actions_equal=False))
    def test_failure_history_preserved(self):
        self.reject('inherited-compact.json',lambda x:x.update(run_conclusion='success'))


if __name__=='__main__':unittest.main()
