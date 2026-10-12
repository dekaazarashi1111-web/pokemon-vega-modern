"""Save89/9,11南から移動0歩・4375true第11switchだけの新規controller検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save90_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[9,11],live_xy=[16,18],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=89,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11295599506,'981089324f749ae85d82a42e41743fc529edf45c95ac510f3aef53fd1e0412b2'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'25e14aa8952190dae350858541a406b7ddcb2a9539af79800a82581ac0819b8d');self.assertEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[9,11]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):self.assertEqual(self.prep()['interaction'],{'local_id': 8, 'target': [9, 12], 'script': 141220512, 'visibility_flag': 4374, 'button': 'A', 'from_xy': [9, 11], 'facing': 1, 'object_address': 155169756, 'object_hex': '0881000009000c000308110000000000a0da6a0816110000'})
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{'4372': 0, '4373': 0, '4374': 0, '4375': 1, '4376': 0, '4377': 0, '4378': 1})
    def test_expected_flags(self):self.assertEqual(self.prep()['expected_flag_changes'],[[4372, 0, 1], [4374, 0, 1], [4375, 1, 0]])
    def test_expected_objects(self):self.assertEqual(self.prep()['expected_object_changes'],[{'local_id': 5, 'operation': 'removeobject'}, {'local_id': 8, 'operation': 'removeobject'}, {'local_id': 9, 'operation': 'addobject'}])
    def test_branch_owner(self):
        p=self.prep();self.assertEqual(len(p['instructions']),43);self.assertEqual({x['node']for x in p['instructions']},{141220512, 141219331, 141220680, 136400176, 141219312, 141219670});self.assertEqual([x['hex']for x in p['instructions']if x['node']==141219670],['291411','530500','291611','530800','2a1711','550900','03'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400648','136400673'});self.assertIn('はいちが',p['texts']['136400673']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_no_warp_or_battle_requested(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]));self.assertNotIn(92,[x['opcode']for x in self.prep()['instructions']])
    def fake(self,no_lock=False,bad_xy=False,battle=False):
        class Interaction:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.event=False
            def step(s,*keys):
                s.inputs.extend(keys);lock=int(not s.event and not no_lock);s.event=True
                s.last=dict(s.last,lock=lock,xy=[9,12]if bad_xy else[9,11],callback2=m.m.BATTLE if battle else m.m.FIELD);s.observations.append(s.last);return s.last
        return Interaction()
    def test_normal_interaction_once(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE+[[9,11]],None,[]));self.assertEqual((f['kind'],f['local_id'],f['trigger'],f['observation']),('eleventh_diglett_event',8,[9,12],2));self.assertEqual(s.inputs,[(1,2),(0,60),(1,2),(0,180)])
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
    def test_unexpected_movement_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(bad_xy=True),{})
    def test_unexpected_battle_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(battle=True),{})
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[3,9,8,2])
    def test_no_directional_inputs(self):
        s=self.fake();m.progress(s,{});self.assertTrue(all(k in(0,1)for k,_ in s.inputs))
    def test_badge_and_money_bound_to_winning_parent(self):
        p=self.prep();self.assertTrue(p['required_badge_present']);self.assertFalse(p['paper_delivered']);self.assertEqual(p['input_save'],m.a.OUTPUT)
    def test_distinct_parent_flags(self):self.assertNotEqual(self.prep()['initial_flags'],{str(f):int(f in(4376,4378))for f in range(4372,4379)})
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',88),('outside_map','map',[3,2]),('old_xy','xy',[6,7]),('bad_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',2),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
