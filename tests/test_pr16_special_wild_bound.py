"""実表全byteと既知差分のみ。旧17unit/nativeは実行しない。"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('sw_bound',Path(__file__).resolve().parents[1]/'scripts/pr16_special_wild_bound.py')
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)


class TableBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declared=s.s.research_rows();cls.audit=s.load(s.ROOT/s.AUDIT)
        rows=copy.deepcopy(cls.declared)
        for d in cls.audit['candidates'][0]['differences']:rows[d['index']]['fields']=d['actual']
        cls.raw=b''.join(struct.pack('<BBH8B',*r['fields']) for r in rows)
        rom=bytearray(s.TABLE_OFFSET+s.TABLE_SIZE+256)
        rom[s.TABLE_OFFSET:s.TABLE_OFFSET+s.TABLE_SIZE]=cls.raw
        struct.pack_into('<I',rom,0x137B31C,0x08000000+s.TABLE_OFFSET)
        struct.pack_into('<I',rom,0x8257C,0x08004000)
        rom[0x4000:0x4002]=bytes([3,27]);struct.pack_into('<I',rom,0x4010,0x08005000)
        rom[0x4014:0x4016]=b'\xff\xff';struct.pack_into('<I',rom,0x5004,0x08006000)
        cls.rom=bytes(rom);cls.candidate=s.identity(cls.rom)
        cls.anchors={'qol_start':0x08000000+0x137B000,'qol_end':0x08000000+len(rom)}
    def setUp(self):
        self.audit=copy.deepcopy(self.__class__.audit);self.audit['candidate']=self.candidate
        self.override=patch.object(s.old,'CANDIDATE',self.candidate);self.override.start();self.addCleanup(self.override.stop)
    def bind(self,rom=None,anchors=None,declared=None):
        return s.bound_rows(self.rom if rom is None else rom,self.anchors if anchors is None else anchors,self.declared if declared is None else declared,self.audit)
    def test_exact_table_all_rows_and_no_rom_change(self):
        before=s.identity(self.rom);rows,report=self.bind()
        self.assertEqual(report['rows'],846);self.assertEqual(report['unchanged_rows'],716)
        self.assertEqual(report['map_only_differences'],130)
        self.assertEqual(b''.join(struct.pack('<BBH8B',*r['fields']) for r in rows),self.raw)
        self.assertEqual(s.identity(self.rom),before);self.assertFalse(report['original_disable_provenance_accepted'])
    def test_excluded_map_cannot_become_fixture(self):
        rows,_=self.bind();f=s.s.select_fixture(self.rom,self.anchors,rows)
        self.assertEqual(f['fishing']['map'],[3,27]);self.assertEqual(f['hidden']['map'],[3,63])
        self.assertEqual(sum(r['fields'][:2]==[3,19] for r in rows),8)
        self.assertNotEqual(f['fishing']['map'],[3,19])
    def test_wrong_parent_candidate_fails(self):
        with self.assertRaises(ValueError):self.bind(rom=b'unknown')
    def test_changed_audit_identity_or_promotion_fails(self):
        for key,value in [('run_id',0),('source_head','x'),('parent_run',0),('parent_conclusion','success'),('rom_changes',1),('runtime_accepted',True),('whole_rom_exact_matches',[s.TABLE_OFFSET])]:
            with self.subTest(key=key):
                original=self.audit[key];self.audit[key]=value
                with self.assertRaises(ValueError):self.bind()
                self.audit[key]=original
    def test_missing_or_multiple_tables_fails(self):
        for tables in ([],self.audit['candidates']*2):
            self.audit['candidates']=tables
            with self.assertRaises(ValueError):self.bind()
    def test_wrong_table_offset_or_identity_fails(self):
        table=self.audit['candidates'][0]
        for key,value in [('offset',s.TABLE_OFFSET+2),('identity',dict(size=10152,sha256='0'*64))]:
            original=table[key];table[key]=value
            with self.assertRaises(ValueError):self.bind()
            table[key]=original
    def test_mutated_actual_byte_fails_even_with_bound_parent(self):
        rom=bytearray(self.rom);rom[s.TABLE_OFFSET+2]^=1;rom=bytes(rom)
        self.audit['candidate']=s.identity(rom)
        with patch.object(s.old,'CANDIDATE',s.identity(rom)):
            with self.assertRaises(ValueError):self.bind(rom=rom)
    def test_wrong_qol_range_fails(self):
        for a in (dict(self.anchors,qol_start=0x08000000+s.TABLE_OFFSET+2),dict(self.anchors,qol_end=0x08000000+s.TABLE_OFFSET+s.TABLE_SIZE-1)):
            with self.assertRaises(ValueError):self.bind(anchors=a)
    def test_changed_literal_pointer_fails(self):
        rom=bytearray(self.rom);rom[0x137B31C]^=1;rom=bytes(rom);self.audit['candidate']=s.identity(rom)
        with patch.object(s.old,'CANDIDATE',s.identity(rom)):
            with self.assertRaises(ValueError):self.bind(rom=rom)
    def test_extra_literal_reference_fails(self):
        rom=bytearray(self.rom);struct.pack_into('<I',rom,0x137B010,s.TABLE_OFFSET+0x08000000);rom=bytes(rom);self.audit['candidate']=s.identity(rom)
        with patch.object(s.old,'CANDIDATE',s.identity(rom)):
            with self.assertRaises(ValueError):self.bind(rom=rom)
    def test_duplicate_or_missing_declared_row_fails(self):
        for rows in (self.declared[:-1],self.declared[:-1]+[self.declared[0]]):
            with self.assertRaises(ValueError):self.bind(declared=rows)
    def test_changed_source_fields_fail(self):
        rows=copy.deepcopy(self.declared);rows[0]['fields'][2]+=1
        with self.assertRaises(ValueError):self.bind(declared=rows)
    def test_known_difference_order_and_completeness_required(self):
        table=self.audit['candidates'][0];original=copy.deepcopy(table['differences'])
        for diffs in (original[:-1],list(reversed(original)),original+original[:1]):
            table['differences']=diffs
            with self.assertRaises(ValueError):self.bind()
    def test_no_arbitrary_field_exception(self):
        rows=copy.deepcopy(self.declared);i=self.audit['candidates'][0]['differences'][0]['index'];rows[i]['fields'][2]+=1
        self.audit['expected']=s.identity(b''.join(struct.pack('<BBH8B',*r['fields']) for r in rows))
        with self.assertRaisesRegex(ValueError,'未知map'):self.bind(declared=rows)
    def test_no_arbitrary_map_exception(self):
        rows=copy.deepcopy(self.declared);i=self.audit['candidates'][0]['differences'][0]['index'];rows[i]['fields'][:2]=[3,20]
        self.audit['expected']=s.identity(b''.join(struct.pack('<BBH8B',*r['fields']) for r in rows))
        with self.assertRaisesRegex(ValueError,'未知map'):self.bind(declared=rows)
    def test_saved_audit_is_hash_bound(self):
        self.assertEqual(s.identity((s.ROOT/s.AUDIT).read_bytes()),s.AUDIT_HASH)


class SavedSuccess(unittest.TestCase):
    def test_absent_case_is_pending_without_cpu_call(self):
        self.assertIsNone(s.reuse_result(None,'a',{},False,True,{}))
        self.assertIsNone(s.reuse_result({'results':{}},'a',{},False,True,{}))
    def test_saved_fixture_drift_is_not_silently_reexecuted(self):
        prior={'results':{'a':{'fixture':{'map':[3,27]},'patched':False}}}
        with self.assertRaises(ValueError):s.reuse_result(prior,'a',{'map':[3,19]},False,True,{})
    def test_saved_raw_revalidated_without_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);raw=b'saved-native-output\n';(folder/'a.stdout.txt').write_bytes(raw)
            (folder/'a.process.json').write_text(json.dumps({'returncode':0,'timed_out':False}))
            result={'fixture':{},'patched':False,'method':'hidden'}
            prior={'results':{'a':result},'evidence_path':tmp,'public_evidence_bindings':{'a.stdout.txt':s.identity(raw)}}
            with patch.object(s.s,'native_result',return_value=result) as validator:
                self.assertEqual(s.reuse_result(prior,'a',{},False,True,{}),result)
                validator.assert_called_once_with(raw,'hidden',{}, {},False,True)
            (folder/'a.stdout.txt').write_bytes(b'changed')
            with self.assertRaises(ValueError):s.reuse_result(prior,'a',{},False,True,{})


if __name__=='__main__':unittest.main()
