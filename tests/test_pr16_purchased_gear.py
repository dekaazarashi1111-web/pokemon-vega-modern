import copy
import json
import unittest
from scripts import pr16_purchased_gear as p

class PurchasedGearValidationTests(unittest.TestCase):
    def setUp(self):
        self.name='eelektross-active'
        self.audit={'paths':{'town':[[0,0]]*25},'table':{'slots':[{'species':627,'min':75,'max':80}]}}
        witness={key:(i+1)*10 for i,key in enumerate(p.TRACE)}
        witness.update(toggle=92,mega=95)
        self.row=p.expected(self.name)|dict(personality=123,enemy_species=627,enemy_level=76,move=9,pp_before=15,pp_after=14,outcome=4,walking_steps=45,total_frames=130,witness=witness)
        self.stderr=b'GEAR_ENCOUNTER species=627 level=76 flags=00000000 frame=80\n'
    def validate(self,row=None,stderr=None,code=0,name=None):
        return p.validate(json.dumps(self.row if row is None else row).encode(),self.stderr if stderr is None else stderr,self.name if name is None else name,code,self.audit)
    def test_active_and_controls(self):
        self.assertEqual(self.validate(),self.row)
        for name,toggles in p.CASES.items():
            row=copy.deepcopy(self.row);row.update(p.expected(name));row['witness']['toggle']=92 if toggles else 0;row['witness']['mega']=95 if toggles==1 else 0
            self.assertEqual(self.validate(row,name=name),row)
    def test_reject_scope_inflation(self):
        for key in ('full_p05_acceptance','release_ready','ring_bp_natural_acquisition_accepted'):
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(self.row|{key:True})
    def test_reject_fixture_concealment(self):
        with self.assertRaises(ValueError):self.validate(self.row|{'initial_map_party_ring_bp_policy_are_fixtures':False})
    def test_reject_missing_or_extra_fields(self):
        row=copy.deepcopy(self.row);del row['fresh_cores']
        with self.assertRaises(ValueError):self.validate(row)
        with self.assertRaises(ValueError):self.validate(self.row|{'extra':0})
    def test_reject_typed_exit_and_counters(self):
        for code in (1,-1,False,None):
            with self.subTest(code=code),self.assertRaises(ValueError):self.validate(code=code)
        for key in ('walking_steps','fresh_cores','personality','toggles'):
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(self.row|{key:True})
    def test_reject_wrong_candidate_or_old_scope(self):
        for delta in ({'rom_sha256':p.parent.r.ROM_SHA},{'scope':p.parent.SCOPE},{'fresh_cores':2}):
            with self.subTest(delta=delta),self.assertRaises(ValueError):self.validate(self.row|delta)
    def test_reject_broken_sequence(self):
        for key in p.TRACE:
            row=copy.deepcopy(self.row);row['witness'][key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(row)
    def test_reject_injected_or_missing_physical_give(self):
        for key in ('physical_give','physical_map_transition','held_stone_not_consumed','party_inventory_bp_persisted'):
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(self.row|{key:False})
    def test_reject_mega_after_move_or_without_input(self):
        for key,value in (('mega',0),('mega',100),('toggle',0),('toggle',101)):
            row=copy.deepcopy(self.row);row['witness'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.validate(row)
    def test_reject_activated_negative_control(self):
        row=copy.deepcopy(self.row);name='eelektross-cancel-toggle';row.update(p.expected(name))
        with self.assertRaises(ValueError):self.validate(row,name=name)
    def test_reject_wrong_species_item_ability_or_bp(self):
        for key in ('species','item','mega_species','ability','bp_after'):
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(self.row|{key:self.row[key]+1})
    def test_reject_invalid_pp_and_outcome(self):
        for delta in ({'pp_after':15},{'pp_after':-1},{'pp_after':0},{'outcome':2},{'walking_steps':1}):
            with self.subTest(delta=delta),self.assertRaises(ValueError):self.validate(self.row|delta)
    def test_reject_missing_duplicate_or_wrong_encounter(self):
        for err in (b'',self.stderr*2,self.stderr.replace(b'species=627',b'species=411'),self.stderr.replace(b'level=76',b'level=74'),self.stderr.replace(b'frame=80',b'frame=81'),self.stderr.replace(b'flags=00000000',b'flags=00000008')):
            with self.subTest(err=err),self.assertRaises(ValueError):self.validate(stderr=err)
    def test_reject_warning_and_duplicate_json_key(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr+b'mGBA[warn]')
        raw=json.dumps(self.row).encode().replace(b'"status": "PASS"',b'"status": "FAIL", "status": "PASS"')
        with self.assertRaises(ValueError):p.validate(raw,self.stderr,self.name,0,self.audit)
    def test_geometry_rejects_unreachable_and_inconsistent_cells(self):
        model={'walkable_pairs':[dict(start=[0,0],end=[1,0],elevation=3,behavior=0),dict(start=[1,1],end=[2,1],elevation=3,behavior=2)]}
        self.assertEqual(p.path(model,[0,0],[2,1]),[[1,0],[1,1],[2,1]])
        with self.assertRaises(ValueError):p.path(model,[0,0],[3,1])
        model['walkable_pairs'].append(dict(start=[0,0],end=[1,0],elevation=4,behavior=0))
        with self.assertRaises(ValueError):p.path(model,[0,0],[1,0])

if __name__=='__main__':unittest.main()
