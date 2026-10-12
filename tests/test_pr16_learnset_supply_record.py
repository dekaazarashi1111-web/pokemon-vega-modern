"""PLA1記録専用の拒否試験。既受入C/圧縮/nativeは実行しない。"""
from __future__ import annotations
import copy
import json
import unittest
from scripts import pr16_learnset_supply_record as r


class SupplyRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=r.inputs()
        cls.files={name:(r.ROOT/r.EVIDENCE/name).read_bytes() for name in cls.config['proof_files']}

    def reject(self, change, member='verification.json'):
        config=copy.deepcopy(self.config);files=dict(self.files)
        value=json.loads(files[member]);change(value);files[member]=r.encode(value)
        if member!='verification.json':
            v=json.loads(files['verification.json']);v['proof_files'][member]=r.identity(files[member])
            files['verification.json']=r.encode(v)
        config['proof_files']={name:r.identity(raw) for name,raw in files.items()}
        with self.assertRaises(ValueError):r.validate(files,config)

    def test_original_success(self):
        self.assertEqual(r.validate(self.files,self.config)['receipt']['image'],r.IMAGE)
    def test_missing_file(self):
        files=dict(self.files);files.pop('unit.txt')
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_extra_file(self):
        with self.assertRaises(ValueError):r.validate(dict(self.files,extra=b'{}'),self.config)
    def test_tampered_file(self):
        files=dict(self.files);files['unit.txt']+=b' '
        with self.assertRaises(ValueError):r.validate(files,self.config)
    def test_no_scope_promotion(self):
        self.reject(lambda v:v.update(scope='GAMEPLAY_ACCEPTED'))
    def test_all_pending_flags_stay_false(self):
        for name in r.FALSE_FLAGS:
            with self.subTest(name=name):self.reject(lambda v:v.update({name:True}))
    def test_all_zero_counts_stay_integer_zero(self):
        for name in r.ZERO_COUNTS:
            for value in (1,False):
                with self.subTest(name=name,value=value):self.reject(lambda v:v.update({name:value}))
    def test_source_identity(self):
        self.reject(lambda v:v.update(source_head='0'*40))
    def test_parent_candidate(self):
        self.reject(lambda v:v['parent_candidate'].update(sha256='0'*64))
    def test_test_counts(self):
        self.reject(lambda v:v.update(new_tests=31))
        self.reject(lambda v:v.update(new_host_queries=145877))
    def test_no_physical_supply_from_receipt(self):
        self.reject(lambda v:v['receipt'].update(physical_supply_verified=True))
    def test_archive_order_preserved(self):
        self.reject(lambda v:v['receipt'].update(all_rows_order_equal=False))
    def test_gate_and_raw_page_evidence(self):
        self.reject(lambda v:v.update(hall_of_fame_gate_checked=False),'host-audit.json')
        self.reject(lambda v:v.update(raw_pages_before_known_filter=False),'host-audit.json')
    def test_no_rom_writes_in_allocation_plan(self):
        self.reject(lambda v:v.update(rom_written=True),'allocation-plan.json')
    def test_fixed_entry_and_binary_not_owned(self):
        self.assertNotIn('CHATGPT_RESUME.md',r.owned())
        self.assertTrue(all(not name.endswith(('.bin','.gba','.zip','.sav','.srm')) for name in r.owned()))
        self.assertTrue({r.STATE,r.DOC,r.CP,'design/run_log.md','design/version_log.md'}<=r.owned())


if __name__=='__main__':unittest.main()
