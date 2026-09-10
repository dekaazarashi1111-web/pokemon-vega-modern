"""Synthetic validator mutations only; these are not emulator acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_modernization_p06_phase_e2e as m

class PhaseValidation(unittest.TestCase):
    def fixture(self,index):
        s=373 if index==2 or index>=8 else 220;a=1 if index in (1,4,5,6) else 0
        x={k:0 for k in m.INTS};x.update({k:False for k in m.FLAGS})
        x.update(schema_version=1,status='OBSERVED',scope=m.SCOPE,rom_sha256=m.base.recipe.PARENT_SHA if index==8 else m.base.FINAL_SHA,case=m.CASES[index],host_write_guard=True,fixture_boundary='BEFORE_FIRST_OBSERVED_FRAME',full_p06_acceptance=False,release_ready=False,warnings_errors=0,ability_name_hex='01'+'ff'*8,ability_description_hex='02'+'ff'*22,species=s,slot=a,ability=m.base.ABILITIES_AFTER[s][a],personality=0,frames=2000,key_presses=4,menu_frame=1000,ended=True)
        x['party_attack']=m.base.stats(s,48,index!=8,0,[0]*6,[0]*6)[1]
        if index<3:x.update(summary_equal=True,mon_equal=True,summary_page=1)
        else:
            x.update(battle_attack=x['party_attack'],player_hp=100,enemy_hp=100,enemy_initial_hp=100,player_pp=20,enemy_pp=20)
            if index==3:x.update(disabled_move=44,disable_timer=3,event_frame=1500,turns=1)
            if index==4:x.update(turns=4,enemy_pp=16)
            if index==5:x.update(reveal_item=13,event_frame=500)
            if index>=8:x.update(turns=1,player_pp=19,enemy_pp=19,enemy_hp=60 if index==8 else 75)
        return x
    def validate(self,x,index,code=0):return m.validate(json.dumps(x).encode(),index,code)
    def test_all_expected_observation_shapes(self):
        for i in range(10):
            with self.subTest(case=i):self.validate(self.fixture(i),i)
    def test_failed_process_and_boolean_zero_rejected(self):
        for code in (False,1,-9):
            with self.subTest(code=code),self.assertRaises(ValueError):self.validate(self.fixture(0),0,code)
    def test_unobserved_endpoint_rejected(self):
        for i in range(10):
            x=self.fixture(i);x['ended']=False
            with self.subTest(case=i),self.assertRaises(ValueError):self.validate(x,i)
    def test_honest_scope_and_rom_required(self):
        for key,value in [('full_p06_acceptance',True),('release_ready',True),('rom_sha256',m.base.recipe.PARENT_SHA),('host_write_guard',False),('warnings_errors',1)]:
            x=self.fixture(0);x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(x,0)
    def test_wrong_ability_and_fake_integer_rejected(self):
        for key,value in [('ability',25),('slot',True),('frames',True),('party_attack',1)]:
            x=self.fixture(0);x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(x,0)
    def test_summary_text_and_mon_integrity_required(self):
        for key,value in [('summary_equal',False),('mon_equal',False),('summary_page',0),('ability_name_hex','ff'*9)]:
            x=self.fixture(0);x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(x,0)
    def test_disable_wrong_move_or_no_timer_rejected(self):
        for key,value in [('disabled_move',33),('disable_timer',0),('event_frame',0)]:
            x=self.fixture(3);x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(x,3)
    def test_control_must_execute_four_incoming_moves(self):
        x=self.fixture(4);x['enemy_pp']=20
        with self.assertRaises(ValueError):self.validate(x,4)
    def test_frisk_requires_actual_item_before_first_input(self):
        for key,value in [('reveal_item',0),('event_frame',1500)]:
            x=self.fixture(5);x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(x,5)
        x=self.fixture(6);x['reveal_item']=13
        with self.assertRaises(ValueError):self.validate(x,6)
    def test_attack_control_and_effect(self):
        a=self.fixture(8);b=self.fixture(9);m.validate_attack_pair(a,b)
        for key,value in [('personality',1),('enemy_hp',50),('party_attack',a['party_attack'])]:
            c=copy.deepcopy(b);c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_attack_pair(a,c)
    def test_duplicate_json_key_rejected(self):
        raw=json.dumps(self.fixture(0))[:-1]+',"frames":2000}'
        with self.assertRaises(ValueError):m.validate(raw.encode(),0,0)

if __name__=='__main__':unittest.main()
