"""自動受付という新しい影響scopeだけ。初回38成功ケース再走0。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save93_admission_measure as m
class Admission(unittest.TestCase):
    def fake(self,mode=None):
        class S:
            def __init__(s):s.last=dict(map=[6,0],xy=[14,9],live_xy=[21,16],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=92,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER);s.observations=[s.last];s.inputs=[];s.i=0
            def step(s,*keys):
                s.inputs.extend(keys);s.i+=1;xy=[14,9-s.i]if s.i<=4 else[14,5];lock=int(s.i>=4 and s.i<7);face=2 if s.i<4 else 4
                s.last=dict(s.last,xy=xy,live_xy=[x+7 for x in xy],facing=face,lock=lock)
                if mode=='warp'and s.i==4:s.last['map']=[6,1]
                if mode=='battle'and s.i==4:s.last['callback2']=m.m.BATTLE
                if mode=='early'and s.i==3:s.last['lock']=1
                if mode=='absent'and s.i==4:s.last['lock']=0
                if mode=='long'and s.i>=4:s.last['lock']=1
                if mode=='party'and s.i==5:s.last['party_sha256']='0'*64
                if mode=='save'and s.i==5:s.last['save_counter']=93
                if mode=='outside'and s.i==5:s.last['xy']=[4,9];s.last['live_xy']=[11,16]
                s.observations.append(s.last);return s.last
        return S()
    def run_case(self,s):
        with patch.object(m.m,'screen',return_value=b'P6\n240 160\n255\n'):return m.progress(s,{})
    def test_admission_boundary_only(self):
        s=self.fake();r,ep,f,w=self.run_case(s);self.assertEqual(r,[[14,9],[14,8],[14,7],[14,6],[14,5]]);self.assertEqual(f['kind'],'new_museum_admission');self.assertEqual(f['dialogue_observations'],[4,5,6]);self.assertEqual(f['observation'],7);self.assertIsNone(ep);self.assertEqual(w,[])
    def test_exact_fee_inputs(self):s=self.fake();self.run_case(s);self.assertEqual(s.inputs,[(64,8),(0,48)]*4+[(1,2),(0,180)]*3)
    def test_stops_at_first_unlock(self):s=self.fake();self.run_case(s);self.assertEqual(len(s.inputs),14);self.assertEqual(s.last['xy'],[14,5])
    def test_scripted_move_allowlist(self):self.assertEqual(m.ROUTE[-1],[14,5]);self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_bound_rejects_endless_dialogue(self):
        s=self.fake('long')
        with self.assertRaises(ValueError):self.run_case(s)
        self.assertEqual(len(s.inputs),32)
    def test_native_fee_owner(self):
        p=json.loads((ROOT/m.PREP).read_bytes());d={x['address']:x['hex']for x in p['instructions']};self.assertEqual(d[0x817f2b3],'913200000000');self.assertEqual(d[0x817f2c6],'1661400100');self.assertEqual(p['coord']['variable'],0x4061)
    def test_expected_fee_not_paper(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual((p['expected']['money_before'],p['expected']['money_after']),(23164,23114));self.assertFalse(p['expected']['museum_second_floor_accepted']);self.assertFalse(any(x['opcode']==0x45 for x in p['instructions']))
    def test_bad_screen_rejected(self):
        with patch.object(m.m,'screen',return_value=b'not-a-screen'):
            with self.assertRaises(ValueError):m.progress(self.fake(),{})
def negative(mode):
    def test(self):
        with self.assertRaises(ValueError):self.run_case(self.fake(mode))
    return test
for mode in ['warp','battle','early','absent','party','save','outside']:setattr(Admission,'test_reject_'+mode,negative(mode))
if __name__=='__main__':unittest.main()
