"""孵化2件/旧20試験を再実行せず、配布counter契約の変更影響だけを検査。"""
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_natural_gift_save as g
s=g.s

class GiftSaveTests(unittest.TestCase):
    def fixture(self):
        pp={204:20,235:5,382:10,738:5};mon=bytearray(100)
        struct.pack_into('<H',mon,32,1029);mon[84]=50;struct.pack_into('<4H',mon,44,204,235,382,738);mon[52:56]=bytes(pp.values());struct.pack_into('<HH',mon,86,149,149)
        raw=bytes(100)+mon
        r={'schema_version':1,'status':'PASS','case':s.GIFT,'candidate_sha256':s.CANDIDATE['sha256'],'species':1029,'level':50,'moves':[204,235,382,738],'pp':list(pp.values()),'fresh_cores':2,'denied_host_write_apis':7,'guarded_phases':3,'party_preserved_bytes':200,'initial_party_map_ring_flag_are_fixtures':True,'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,'gift_counter_steps':2,'boundary':10,'claimed':20,'returned':40,'saved':50,'continued':60,'repeat':70,'npc_script':0x09463300,'save_counters':[2,4,5,5,5]}
        err=''.join(f'SUPPLY_PARTY stage={n} counter={c} hex={b.hex()}\n' for n,c,b in zip(('fixture','claimed','saved','continued','repeat'),r['save_counters'],[bytes(100),raw,raw,raw,raw]))
        err+='SUPPLY_GIFT_SAVE frame=25 before=2 after=3 lock=1 count=2 pc=080db240\nSUPPLY_GIFT_SAVE frame=30 before=3 after=4 lock=1 count=2 pc=080db240\noriginal core destroyed; new core boot and normal Continue\n'
        return r,err.encode(),pp
    def test_exact_two_raw_transitions(self):
        r,err,pp=self.fixture();v=g.validate(json.dumps(r),err,pp);self.assertEqual(len(v['gift_counter_witnesses']),2)
    def test_old_one_increment_assumption_rejected(self):
        r,err,pp=self.fixture();r['save_counters']=[2,3,4,4,4]
        with self.assertRaises(ValueError):g.validate(json.dumps(r),err,pp)
    def test_missing_transition(self):
        r,err,pp=self.fixture()
        with self.assertRaises(ValueError):g.validate(json.dumps(r),err.replace(b'SUPPLY_GIFT_SAVE frame=25',b'MISSING frame=25'),pp)
    def test_extra_transition(self):
        r,err,pp=self.fixture()
        with self.assertRaises(ValueError):g.validate(json.dumps(r),err+b'SUPPLY_GIFT_SAVE frame=35 before=4 after=5 lock=1 count=2 pc=080db240\n',pp)
    def test_mutated_transitions(self):
        for old,new in [(b'frame=25',b'frame=19'),(b'after=3',b'after=4'),(b'lock=1',b'lock=0'),(b'count=2',b'count=1'),(b'pc=080db240',b'pc=02000000')]:
            r,err,pp=self.fixture()
            with self.assertRaises(ValueError,msg=str(new)):g.validate(json.dumps(r),err.replace(old,new,1),pp)
    def test_repeat_or_continue_changed(self):
        for counters in ([2,4,5,5,6],[2,4,5,6,6]):
            r,err,pp=self.fixture();r['save_counters']=counters
            with self.assertRaises(ValueError):g.validate(json.dumps(r),err,pp)
    def test_saved_bytes_changed(self):
        r,err,pp=self.fixture()
        with self.assertRaises(ValueError):g.validate(json.dumps(r),err.replace(b'stage=continued counter=5 hex=00',b'stage=continued counter=5 hex=01'),pp)
    def test_pp_and_move_order(self):
        for key,value in [('moves',[235,204,382,738]),('pp',[20,5,20,5]),('gift_counter_steps',True),('release_ready',True)]:
            r,err,pp=self.fixture();r[key]=value
            with self.assertRaises(ValueError):g.validate(json.dumps(r),err,pp)
    def test_warning_and_lifecycle(self):
        for mutation in (lambda b:b+b'mGBA[error]',lambda b:b.replace(b'original core destroyed;',b'missing;')):
            r,err,pp=self.fixture()
            with self.assertRaises(ValueError):g.validate(json.dumps(r),mutation(err),pp)
    def test_duplicate_json(self):
        r,err,pp=self.fixture()
        with self.assertRaises(ValueError):g.validate('{"status":"FAIL",'+json.dumps(r)[1:],err,pp)
    def test_gift_only_pending(self):
        contracts={n:{} for n in s.NAMES};accepted={n:{'contract':{},'result':{'status':'PASS'}} for n in s.HATCH}
        self.assertEqual(s.pending(accepted,contracts),[s.GIFT])
    def test_only_input_observation_after_boundary(self):
        text=(s.ROOT/s.C).read_text();section=text.split('/* Fixture終端。',1)[1]
        self.assertNotIn('write8(',section);self.assertNotIn('write32(',section)
        self.assertNotIn('call_preserving(c,0x080DB34',section)
        self.assertIn('SUPPLY_GIFT_SAVE frame=',text);self.assertIn('gift_counter_steps==2',text)

if __name__=='__main__':unittest.main()
