import copy
import json
import unittest
from scripts import pr16_captured_battle as m

class CapturedBattleTests(unittest.TestCase):
    def setUp(self):
        self.name='cave-113';self.value=m.capture.expected(self.name)|dict(scope=m.SCOPE,manual_saves=2,fresh_cores=3,battle_connection_accepted=True,level=80,personality=123,walking_steps=5,encounters=1,escaped=0,total_frames=200,witness=dict(walking=1,encounter=20,bag=30,caught=40,saved=50,reloaded=60))
        self.proof=dict(encounter=70,menu=80,switched=90,spent=100,field=110,saved=120,reloaded=200,steps=5,enemy_species=411,enemy_level=80,ability=26,move=85,pp_before=15,pp_after=14,outcome=4,captured_personality=123,party_slot=1,party_and_inventory_persisted=True,manual_saves=2,fresh_cores=3,gear_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False)
        self.audit={'cases':{self.name:{'table':{'slots':[{'species':411,'min':70,'max':80}]}}}}
    def validate(self,value=None,proof=None):
        raw=json.dumps(self.value if value is None else value).encode();p=self.proof if proof is None else proof
        stderr=b'NATURAL_ENCOUNTER number=1 step=5 species=411 level=80 flags=00000004 frame=20\nCAPTURED_BATTLE_PROOF '+json.dumps(p).encode()+b'\n'
        return m.validate(raw,stderr,self.name,0,self.audit)
    def test_scoped_new_capture_battle(self):self.assertEqual(self.validate()['battle'],self.proof)
    def test_reject_prior_two_core_capture_as_new(self):
        with self.assertRaises(ValueError):self.validate(self.value|{'fresh_cores':2})
    def test_reject_no_new_battle(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'encounter':50})
    def test_reject_reordered_save(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'saved':95})
    def test_reject_no_native_pp_use(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'pp_after':15})
    def test_reject_different_captured_identity(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'captured_personality':124})
    def test_reject_injected_or_unlisted_enemy(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'enemy_species':10})
    def test_reject_scope_inflation(self):
        for key in ('gear_acquisition_accepted','full_p05_acceptance','release_ready'):
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(proof=self.proof|{key:True})
    def test_reject_boolean_counter(self):
        with self.assertRaises(ValueError):self.validate(proof=self.proof|{'steps':True})
    def test_generated_controller_retains_guard_and_new_scope(self):
        text=m.controller();self.assertIn(m.SCOPE,text);self.assertIn('struct NBProof follow=nb_run(c,v)',text);self.assertIn('third core Continue failed',text)
        self.assertNotIn(m.capture.SCOPE,text);self.assertEqual(text.count('a_guard(c)'),3)

if __name__=='__main__':unittest.main()
