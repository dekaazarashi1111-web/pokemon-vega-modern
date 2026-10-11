import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_berry_consumer as m


class ConsumerBoundary(unittest.TestCase):
    def good(self):
        row={'case':0,'fetch_mask':7,'steps':100,'mapped_original_bytes_unchanged_at_fetch':True,
             'entry_was_bundle_header':True,'bl_target_and_link_verified':True,'escaped_fixture_scope':False}
        return {'host_owner_verified':True,'host_init_cases':3,'host_master_cases':13,
                'nonowned_host_ram_unchanged':True,'rom_writes':0,'real_saves':0,
                'children':[row,{**row,'case':1}]}
    def test_payload_rounding(self):
        self.assertEqual(m.master_model(13260,4,1)['rounded_length'],13264)
    def test_lower_boundary(self):
        self.assertFalse(m.master_model(240,4,1)['accepted']);self.assertTrue(m.master_model(241,4,1)['accepted'])
    def test_upper_boundary(self):
        self.assertTrue(m.master_model(262144,4,1)['accepted']);self.assertFalse(m.master_model(262145,4,1)['accepted'])
    def test_nonpositive(self):
        for n in (-16,-1,0):self.assertFalse(m.master_model(n,4,1)['accepted'])
    def test_early_guards(self):
        for probe,clients,wait in ((1,2,0),(0,0,0),(0,2,1)):
            row=m.master_model(13260,4,1,probe,clients,wait)
            self.assertTrue(row['early_reset']);self.assertFalse(row['source_pointer_written'])
    def test_late_reset_preserves_source_write(self):
        row=m.master_model(0,4,1);self.assertTrue(row['source_pointer_written']);self.assertEqual(row['check_wait_after'],15)
    def test_palette_modes(self):
        self.assertEqual([m.master_model(256,4,s)['palette_if_accepted'] for s in (-4,-1,0,1,4)],[207,201,249,193,199])
    def test_types_and_fixture_limit(self):
        for args in ((True,4,1),(256,True,1),(256,4,False),(999999,4,1),(256,8,1),(256,4,5)):
            with self.assertRaises(ValueError):m.master_model(*args)
    def test_required_ram_symbols(self):
        raw='\n'.join('\t'.join(['x',f'{0x02000000+i*1024:08x}','x','x',n,'x','x','x']) for i,n in enumerate(sorted(m.RAM_NAMES))).encode()
        self.assertEqual(m.ram_symbols(raw).keys(),m.RAM_NAMES)
        with self.assertRaises(ValueError):m.ram_symbols(raw+b'\n'+raw.splitlines()[0])
    def test_missing_and_outside_ram(self):
        with self.assertRaises(ValueError):m.ram_symbols(b'')
        raw='\t'.join(['x','08000000','x','x','gTasks','x','x','x']).encode()
        with self.assertRaises(ValueError):m.ram_symbols(raw)
    def test_overlapping_ram(self):
        raw='\n'.join('\t'.join(['x','02000000','x','x',n,'x','x','x']) for n in m.RAM_NAMES).encode()
        with self.assertRaises(ValueError):m.ram_symbols(raw)
    def test_thumb_kind_rejects_memory_and_exception(self):
        self.assertEqual(m.decode_following(0x2009),'IMMEDIATE_ALU')
        self.assertEqual(m.decode_following(0x1C09),'SHIFT_ADD_SUB')
        self.assertEqual(m.decode_following(0x4009),'REGISTER_ALU')
        for n in (0x6809,0xDF00,0x4700,0xFFFF):self.assertIsNone(m.decode_following(n))
    def test_strict_json(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}'):
            with self.assertRaises(ValueError):m.strict(raw)
        self.assertEqual(m.strict('{"x":1}'),{'x':1})
    def test_full_measurement_not_final_acceptance(self):
        v=m.classify(self.good(),{'following_class':'IMMEDIATE_ALU'})
        self.assertTrue(v['classification_eligible_after_completed_run_receipt']);self.assertEqual(v['donor_safe_bytes'],0)
        self.assertFalse(v['natural_multiboot_transfer_proven']);self.assertFalse(v['all_aliases_or_indirect_readers_proven'])
    def test_partial_coverage_never_accepted(self):
        for mask in (0,1,3,5,6):
            v=self.good()
            for row in v['children']:row['fetch_mask']=mask
            self.assertFalse(m.classify(v,{'following_class':'IMMEDIATE_ALU'})['actual_instruction_fetch_proven'])
    def test_unknown_following_kind_never_accepted(self):
        self.assertFalse(m.classify(self.good(),{'following_class':None})['actual_instruction_fetch_proven'])
    def test_link_not_verified_never_accepted(self):
        v=self.good()
        for row in v['children']:row['bl_target_and_link_verified']=False
        self.assertFalse(m.classify(v,{'following_class':'IMMEDIATE_ALU'})['actual_instruction_fetch_proven'])
        v=self.good()
        for row in v['children']:row['escaped_fixture_scope']=True
        self.assertFalse(m.classify(v,{'following_class':'IMMEDIATE_ALU'})['actual_instruction_fetch_proven'])
    def test_host_owner_and_write_guards(self):
        for key,value in [('host_owner_verified',False),('host_init_cases',True),('host_master_cases',12),('rom_writes',False),('real_saves',1),('nonowned_host_ram_unchanged',False)]:
            v=self.good();v[key]=value
            with self.assertRaises(ValueError):m.classify(v,{'following_class':'IMMEDIATE_ALU'})
    def test_child_bounds_duplicate_and_identity(self):
        for key,value in [('case',1),('fetch_mask',True),('fetch_mask',8),('steps',0),('steps',1500001),('mapped_original_bytes_unchanged_at_fetch',False),('entry_was_bundle_header',False)]:
            v=self.good();v['children'][0][key]=value
            with self.assertRaises(ValueError):m.classify(v,{'following_class':'IMMEDIATE_ALU'})
    def test_projection_read_only_and_wrong_bundle(self):
        v=self.good();before=copy.deepcopy(v);m.classify(v,{'following_class':'IMMEDIATE_ALU'});self.assertEqual(v,before)
        with self.assertRaises(ValueError):m.instruction_contract(b'\0'*13452)

if __name__=='__main__':unittest.main()
