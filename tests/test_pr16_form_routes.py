"""Fail-closed synthetic metadata tests, not native form acceptance."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_form_routes as m
class FormRouteTests(unittest.TestCase):
    def sample(self,name):
        out=m.expected(name);out['total_frames']=24000;out['traces']=[]
        index=m.CASES.index(name)
        for n in range(out['rounds']):
            trace={k:(n+1)*1000+(j+1)*100 for j,k in enumerate(m.TRACE)}
            if index==7:trace['service']=0
            if index in (7,8):trace['party']=0
            if index in (7,8,9):trace['selection']=0
            out['traces'].append(trace)
        return out
    def test_all_ten_scoped_cases_and_twenty_five_fresh_cores(self):
        self.assertEqual(sum(m.expected(n)['fresh_cores'] for n in m.CASES),25)
        for name in m.CASES:
            value=self.sample(name);self.assertEqual(m.validate(json.dumps(value).encode(),name,0),value)
            self.assertFalse(value['release_ready']);self.assertTrue(value['starting_progress_individual_map_are_fixtures'])
    def test_every_required_witness_and_round_order(self):
        for name in m.CASES:
            value=self.sample(name)
            for i,t in enumerate(value['traces']):
                for key,v in t.items():
                    bad=self.sample(name);bad['traces'][i][key]=0 if v else 100
                    with self.subTest(name=name,key=key),self.assertRaises(ValueError):m.validate(json.dumps(bad).encode(),name,0)
        bad=self.sample(m.CASES[0]);bad['traces'].reverse()
        with self.assertRaises(ValueError):m.validate(json.dumps(bad).encode(),m.CASES[0],0)
    def test_full_denial_and_compaction_preserve_pp_and_pp_ups(self):
        denied=self.sample('full-denied');removed=self.sample('compact-removal')
        self.assertEqual(denied['moves'],[84,109,86,33]);self.assertEqual(denied['pp_bonuses'],229)
        self.assertEqual(removed['moves'],[84,109,86,0]);self.assertEqual(removed['pp_bonuses'],57)
        for key,value in [('moves',[84,109,86,315]),('pp',[7,8,9,5]),('pp_bonuses',37),('automatic_saves',1),('result',0)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(json.dumps(denied|{key:value}).encode(),'full-denied',0)
    def test_wrong_identity_testmode_saves_party_and_scope_are_rejected(self):
        good=self.sample(m.CASES[0])
        for key,value in [('rom_sha256','0'*64),('fresh_cores',1),('manual_saves',1),('automatic_saves',0),
                          ('selected_party_slot',0),('host_index',10),('test_mode',True),('nonselected_preserved',False),
                          ('party_byte_preserved_on_reload',False),('physical_host',[1,36,0,0]),('release_ready',True),
                          ('warnings_errors',1),('host_write_barriers',6),('species',894),('rounds',1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(json.dumps(good|{key:value}).encode(),m.CASES[0],0)
    def test_noninteger_exit_and_counter_duplicate_json_and_extra_keys_rejected(self):
        name=m.CASES[0];good=self.sample(name)
        for code in (1,None,False,0.0):
            with self.assertRaises(ValueError):m.validate(json.dumps(good).encode(),name,code)
        for raw in (b'{}',b'{"a":1,"a":2}',json.dumps(good|{'total_frames':True}).encode(),json.dumps(good|{'extra':1}).encode()):
            with self.assertRaises(ValueError):m.validate(raw,name,0)
    def test_cancel_cannot_be_relabelled_as_success(self):
        for name in m.CASES[-3:]:
            good=self.sample(name)
            self.assertEqual(good['automatic_saves'],0)
            with self.assertRaises(ValueError):m.validate(json.dumps(good|{'result':0}).encode(),name,0)
    def test_new_controller_keeps_real_interaction_and_save_barriers(self):
        text=(ROOT/m.SOURCE).read_text()
        self.assertIn('b_position(c,1,36,6,4)',text);self.assertIn('b_frame(c,QOL_KEY_UP)',text)
        self.assertIn('m_waitmenu(c,0,prefix,round)',text);self.assertIn('m_waitmenu(c,2,prefix,round)',text)
        self.assertIn('read8(c,M_PARTY_SLOT)==1U',text);self.assertIn('a_guard(c);a_require(b_save(c)',text)
        self.assertIn('b_continue(c)',text);self.assertIn('!memcmp(party,restored,200U)',text)
        guarded=text.split('/* After this barrier, only GBA input and read-only observations. */',1)[1]
        for forbidden in ('write8(', 'write16(', 'write32(', 'set_mon_data_u32(', 'call_preserving('):self.assertNotIn(forbidden,guarded)
if __name__=='__main__':unittest.main()
