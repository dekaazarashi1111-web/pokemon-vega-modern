"""自然供給の新契約だけを検査。旧native/旧unitを呼ばない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_natural_supply as s

class NaturalSupplyTests(unittest.TestCase):
    def test_distinct_unaccepted_cases(self):
        self.assertEqual(len(set(s.NAMES)),3)
        self.assertFalse(set(s.NAMES)&set(s.egg.BY_NAME))
    def test_hatch_baseline(self):
        cases=s.hatch_cases({1:20,649:15})
        self.assertEqual([c[-1] for c in cases],[(33,81,0,0),(10,39,0,0)])
        self.assertTrue(all(c[4]==c[3]==0 and c[5]==c[6] for c in cases))
    def test_bad_cycles(self):
        for value in ({1:0,649:15},{1:20,649:41},{1:True,649:15},{1:20}):
            with self.assertRaises(ValueError):s.hatch_cases(value)
    def test_scoped_globals_restored(self):
        old=s.egg.CASES,s.egg.SCOPE,s.m.CANDIDATE
        with self.assertRaises(RuntimeError):
            with s.egg_contract(s.hatch_cases({1:20,649:15})):raise RuntimeError()
        self.assertEqual(old,(s.egg.CASES,s.egg.SCOPE,s.m.CANDIDATE))
    def test_exact_controller_derivation(self):
        text=s.hatch_source(s.hatch_cases({1:20,649:15}))
        parent=(s.ROOT/s.egg.PARENT).read_text()
        self.assertEqual(text.count('a_guard(c);'),parent.count('a_guard(c);'))
        self.assertIn('b_create(c,QOL_PLAYER_PARTY,v->mother_species',text)
        self.assertNotIn('"lightball-father"',text)
        self.assertIn(s.CANDIDATE['sha256'],text)
    def test_floette_raw_window(self):
        self.assertEqual(s.boundary.n.initial(s.FLOETTE_ROWS,50),[204,235,382,738])
        self.assertEqual(s.boundary.n.initial([(1,1),(2,1),(3,1),(4,1),(4,1)],1),[2,3,4,0])
    def test_source_order_rejected(self):
        with self.assertRaises(ValueError):s.boundary.n.initial(s.FLOETTE_ROWS[::-1],50)
    def test_skip_saved_success(self):
        contracts={name:{'sha':name} for name in s.NAMES}
        saved={s.NAMES[0]:{'contract':contracts[s.NAMES[0]],'result':{'status':'PASS'}}}
        self.assertEqual(s.pending(saved,contracts),list(s.NAMES[1:]))
    def test_changed_saved_contract_rejected(self):
        with self.assertRaises(ValueError):s.pending({s.NAMES[0]:{'contract':0,'result':{'status':'PASS'}}},{name:1 for name in s.NAMES})
    def test_unknown_saved_case_rejected(self):
        with self.assertRaises(ValueError):s.pending({'extra':{}},{name:{} for name in s.NAMES})
    def test_no_repeat_all_accepted(self):
        contracts={name:{} for name in s.NAMES};saved={name:{'contract':{},'result':{'status':'PASS'}} for name in s.NAMES}
        self.assertEqual(s.pending(saved,contracts),[])
    def test_gift_readonly_source_boundary(self):
        text=(s.ROOT/s.C).read_text().split('/* Fixture終端。',1)[1]
        self.assertNotIn('write8(',text);self.assertNotIn('create_mon(',text)
        self.assertIn('c=b_restart(',text);self.assertIn('gift_dialog(c,false)',text)
        self.assertNotIn('FloetteGift_Claim',text)
    def gift(self):
        pp={204:20,235:5,382:20,738:5};mon=bytearray(100)
        struct.pack_into('<H',mon,32,1029);mon[84]=50
        struct.pack_into('<4H',mon,44,204,235,382,738);mon[52:56]=bytes(pp.values())
        raw=bytes(100)+mon
        r={'schema_version':1,'status':'PASS','case':s.GIFT,'candidate_sha256':s.CANDIDATE['sha256'],'species':1029,'level':50,'moves':[204,235,382,738],'pp':list(pp.values()),'fresh_cores':2,'denied_host_write_apis':7,'guarded_phases':3,'party_preserved_bytes':200,'initial_party_map_ring_flag_are_fixtures':True,'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,'boundary':10,'claimed':20,'returned':30,'saved':40,'continued':50,'repeat':60,'npc_script':0x09500000,'save_counters':[2,3,4,4,4]}
        err=''.join(f'SUPPLY_PARTY stage={name} counter={c} hex={data.hex()}\n' for name,c,data in zip(('fixture','claimed','saved','continued','repeat'),r['save_counters'],[bytes(100),raw,raw,raw,raw]))
        err+='original core destroyed; new core boot and normal Continue\n'
        return r,err.encode(),pp
    def test_full_raw_gift_validation(self):
        r,err,pp=self.gift();self.assertEqual(s.gift_validate(json.dumps(r),err,pp)['status'],'PASS')
    def test_gift_scope_mutations(self):
        for key,value in [('issue19_complete',True),('fresh_cores',1),('guarded_phases',0),('species',959),('claimed',31),('moves',[235,204,382,738]),('save_counters',[2,3,4,4,5]),('boundary',True)]:
            r,err,pp=self.gift();r[key]=value
            with self.assertRaises(ValueError,msg=key):s.gift_validate(json.dumps(r),err,pp)
    def test_raw_counter_mismatch(self):
        r,err,pp=self.gift()
        with self.assertRaises(ValueError):s.gift_validate(json.dumps(r),err.replace(b'counter=4',b'counter=5',1),pp)
    def test_raw_party_corruption(self):
        r,err,pp=self.gift()
        with self.assertRaises(ValueError):s.gift_validate(json.dumps(r),err.replace(b'stage=repeat counter=4 hex=00',b'stage=repeat counter=4 hex=01'),pp)
    def test_native_warning_rejected(self):
        r,err,pp=self.gift()
        with self.assertRaises(ValueError):s.gift_validate(json.dumps(r),err+b'mGBA[error]',pp)
    def test_duplicate_json_rejected(self):
        r,err,pp=self.gift()
        with self.assertRaises(ValueError):s.gift_validate('{"status":"FAIL",'+json.dumps(r)[1:],err,pp)
    def test_missing_raw_stage_rejected(self):
        r,err,pp=self.gift()
        with self.assertRaises(ValueError):s.gift_validate(json.dumps(r),err.replace(b'SUPPLY_PARTY stage=saved',b'MISSING stage=saved'),pp)
    def test_geometry_out_of_bounds(self):
        with self.assertRaises(ValueError):s.gift_geometry(bytes(100))

if __name__=='__main__':unittest.main()
