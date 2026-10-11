"""特殊野生2callsite修復の新境界だけ。旧13unit/nativeは起動しない。"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('sw_repair',Path(__file__).resolve().parents[1]/'scripts/pr16_special_wild_repair.py')
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)


def party(last=92):
    raw=bytearray(100);struct.pack_into('<I',raw,0,123);struct.pack_into('<H',raw,32,451);raw[84]=25
    struct.pack_into('<4H',raw,44,10,39,33,last);raw[52:56]=bytes([35,30,35,10]);return raw.hex()


def fixture(method='fishing',patched=False,special=True):
    f=dict(map=[3,27],seed_start=123,limit=64,profile=int(special),mode=1 if patched else 2 if special else 0)
    a={'qol_start':0x09320000,'qol_end':0x09330000}
    entries=[0x08082750,0x093BEA68,0x09392714] if method=='fishing' else [0x09220198,0x093BEA98,0x0939273C]
    rows=[dict(event='fixture',method=method,dispatch_status=0,transitions=1,normal_unlock_claimed=False,**f),dict(event='call',attempt=1,seed=123,entry=entries[0]+1,map=f['map'])]
    rows += [dict(event='entry',attempt=1,step=i+1,pc=pc,lr=1) for i,pc in enumerate(entries)]
    if special:rows.append(dict(event='special_setter',attempt=1,step=10,pc=0x09114698,lr=0x09320001,move=92,slot=3))
    rows.append(dict(event='before_post',attempt=1,step=20,party=party()))
    if not patched:rows.append(dict(event='before_apply',attempt=1,step=22,party=party()))
    rows += [dict(event='after_return',attempt=1,step=30,party=party(45) if special and not patched else party()),dict(event='result',attempt=1,returned=1,species=451,special_setters=int(special),apply_calls=0 if patched else 1,post_calls=1),dict(event='summary',status='OBSERVED',method=method,calls=1,host_write_violations=0,direct_call_fixture=True,gameplay_accepted=False,save_continue_accepted=False)]
    return rows,a,f


def pack(rows):return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()


def synthetic_rom():
    rom=bytearray(0x1392800)
    for off,pre in s.PREIMAGES.items():rom[off:off+12]=pre+bytes.fromhex('200010bc02bc0847')
    return bytes(rom)


class Boundary(unittest.TestCase):
    def test_both_special_paths_old_and_fixed(self):
        for method in ('fishing','hidden'):
            for repaired in (False,True):
                r,a,f=fixture(method,repaired);out=s.native_result(pack(r),method,a,f,repaired,True)
                self.assertEqual(out['classification'],'SPECIAL_SLOT_PRESERVED' if repaired else 'SPECIAL_SLOT_OVERWRITTEN')
                self.assertFalse(out['gameplay_accepted']);self.assertFalse(out['save_continue_accepted'])
    def test_normal_controls(self):
        for repaired in (False,True):
            r,a,f=fixture('hidden',repaired,False);self.assertEqual(s.native_result(pack(r),'hidden',a,f,repaired,False)['classification'],'NO_SPECIAL_UNCHANGED')
    def test_patched_cannot_call_reset(self):
        r,a,f=fixture(patched=True);r[-2]['apply_calls']=1
        with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,True,True)
    def test_patched_requires_full_100_byte_preservation(self):
        for offset in (0,40,52,85):
            r,a,f=fixture(patched=True);raw=bytearray.fromhex(r[-3]['party']);raw[offset]^=1;r[-3]['party']=raw.hex()
            with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,True,True)
    def test_old_must_really_erase_special(self):
        r,a,f=fixture();r[-3]['party']=party()
        with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_qol_setter_range_and_order(self):
        for key,val in (('lr',0x09100000),('step',25),('pc',0x093925F4),('slot',2),('move',99)):
            r,a,f=fixture();r[5][key]=val
            with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_missing_or_duplicate_callsite(self):
        for duplicate in (False,True):
            r,a,f=fixture()
            if duplicate:r.insert(6,copy.deepcopy(r[6]))
            else:r.pop(6)
            with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_refuse_fixture_drift(self):
        for key,val in (('map',[11,3]),('profile',0),('limit',65),('seed_start',999)):
            r,a,f=fixture();r[0][key]=val
            with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_refuse_seed_count_and_write_or_scope_promotion(self):
        for key,val in (('host_write_violations',1),('gameplay_accepted',True),('save_continue_accepted',True),('calls',True),('calls',65)):
            r,a,f=fixture();r[-1][key]=val
            with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
        r,a,f=fixture();r[1]['seed']+=1
        with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_refuse_wrong_delegate(self):
        r,a,f=fixture();r[3]['pc']=0x094141BD
        with self.assertRaises(ValueError):s.native_result(pack(r),'fishing',a,f,False,True)
    def test_exact_two_site_patch_rollback_and_reapply_rejected(self):
        rom=synthetic_rom()
        with patch.object(s.old,'CANDIDATE',s.identity(rom)):
            fixed,recipe=s.patch_candidate(rom)
            self.assertEqual(recipe['changed_bytes'],8);self.assertTrue(recipe['rollback_verified'])
            for off in s.PREIMAGES:self.assertEqual(fixed[off:off+4],s.NOP);self.assertEqual(fixed[off+4:off+12],rom[off+4:off+12])
            with self.assertRaises(ValueError):s.patch_candidate(fixed)
    def test_reject_bad_preimage_and_bad_return_window(self):
        for offset in (0x1392722,0x139274A,0x1392726,0x139274E):
            rom=bytearray(synthetic_rom());rom[offset]^=1;rom=bytes(rom)
            with patch.object(s.old,'CANDIDATE',s.identity(rom)):
                with self.assertRaises(ValueError):s.patch_candidate(rom)
    def test_refuse_any_unbound_rom(self):
        with self.assertRaises(ValueError):s.patch_candidate(b'not a candidate')
    def test_generated_probe_keeps_seven_guards_and_no_old_main_call(self):
        source=s.generated_source()
        self.assertEqual(source.count('int main(int argc,char**argv)'),1)
        self.assertEqual(source.count('int saved_probe_main('),1)
        self.assertIn('sw_post_calls',source);self.assertIn('limit>64U',source)
        for token in ('c->busWrite8=deny8','c->busWrite16=deny16','c->busWrite32=deny32','c->rawWrite8=raw8','c->rawWrite16=raw16','c->rawWrite32=raw32','c->writeRegister=denyreg'):self.assertIn(token,source)
    def test_research_source_exact_domain(self):
        declared=s.research_rows();self.assertEqual(len(declared),846)
        self.assertFalse(any(r['fields'][:2]==[11,3] for r in declared))
        self.assertTrue(any(r['fields'][:2]==[3,63] for r in declared))
    def test_fixture_intersection_and_mismatched_table_rejected(self):
        decl=[dict(research_key='a',region='TOHOKU',fields=[3,27,451,20,30,2,5,5,2,3,1]),dict(research_key='b',region='TOHOKU',fields=[3,63,471,42,55,2,5,5,2,5,1])]
        table=b''.join(struct.pack('<BBH8B',*r['fields']) for r in decl)
        rom=bytearray(0x90000);rom[0x1000:0x1000+len(table)]=table
        struct.pack_into('<I',rom,0x8257C,0x08004000)
        rom[0x4000:0x4002]=bytes([3,27]);struct.pack_into('<I',rom,0x4010,0x08005000);rom[0x4014:0x4016]=b'\xff\xff'
        struct.pack_into('<I',rom,0x5004,0x08006000);a={'qol_start':0x08001000,'qol_end':0x08002000}
        f=s.select_fixture(rom,a,decl);self.assertEqual(f['fishing']['map'],[3,27]);self.assertEqual(f['hidden']['map'],[3,63])
        rom[0x1000]^=1
        with self.assertRaises(ValueError):s.select_fixture(rom,a,decl)
    def test_no_fishing_intersection_cannot_start_native(self):
        decl=[dict(research_key='a',region='TOHOKU',fields=[3,63,471,42,55,2,5,5,2,5,1])]
        table=struct.pack('<BBH8B',*decl[0]['fields']);rom=bytearray(0x90000);rom[0x1000:0x1000+len(table)]=table
        struct.pack_into('<I',rom,0x8257C,0x08004000);rom[0x4000:0x4002]=b'\xff\xff'
        with self.assertRaises(ValueError):s.select_fixture(rom,{'qol_start':0x08001000,'qol_end':0x08002000},decl)


if __name__=='__main__':unittest.main()
