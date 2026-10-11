import copy
import json
import unittest
from scripts import pr16_natural_capture as n

class NaturalCaptureValidationTests(unittest.TestCase):
    def setUp(self):
        self.name='cave-113'
        self.row=n.expected(self.name)|dict(level=45,personality=123,walking_steps=5,encounters=2,escaped=1,total_frames=100,
            witness=dict(walking=1,encounter=20,bag=30,caught=40,saved=50,reloaded=60))
        self.audit={'cases':{self.name:{'table':{'slots':[{'species':411,'min':40,'max':50},{'species':10,'min':1,'max':20}]}}}}
        self.stderr=b'NATURAL_ENCOUNTER number=1 step=2 species=10 level=5 flags=00000000 frame=10\nNATURAL_ENCOUNTER number=2 step=5 species=411 level=45 flags=00000000 frame=20\n'
    def validate(self,row=None,stderr=None,code=0):
        return n.validate(json.dumps(self.row if row is None else row).encode(),self.stderr if stderr is None else stderr,self.name,code,self.audit)
    def test_valid_scoped_capture(self):self.assertEqual(self.validate(),self.row)
    def test_reject_scope_inflation(self):
        for key in ('full_p05_acceptance','release_ready','gear_acquisition_accepted','battle_connection_accepted','target_and_rng_injected'):
            row=copy.deepcopy(self.row);row[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(row)
    def test_reject_missing_or_extra_key(self):
        row=copy.deepcopy(self.row);del row['fresh_cores']
        with self.assertRaises(ValueError):self.validate(row)
        row=self.row|{'extra':True}
        with self.assertRaises(ValueError):self.validate(row)
    def test_reject_boolean_counters_and_exit(self):
        for key in ('level','walking_steps','personality','fresh_cores'):
            row=self.row|{key:True}
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(row)
        with self.assertRaises(ValueError):self.validate(code=False)
    def test_reject_unordered_save_trace(self):
        row=copy.deepcopy(self.row);row['witness']['reloaded']=40
        with self.assertRaises(ValueError):self.validate(row)
    def test_reject_missing_encounter_original(self):
        with self.assertRaises(ValueError):self.validate(stderr=b'')
    def test_reject_unaudited_species(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr.replace(b'species=10 ',b'species=11 '))
    def test_reject_unaudited_level(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr.replace(b'level=45 ',b'level=60 '))
    def test_reject_trainer_battle(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr.replace(b'flags=00000000',b'flags=00000008'))
    def test_reject_skipped_target(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr.replace(b'species=10 level=5',b'species=411 level=45'))
    def test_reject_warning(self):
        with self.assertRaises(ValueError):self.validate(stderr=self.stderr+b'mGBA[warn]')
    def test_reject_wrong_candidate(self):
        with self.assertRaises(ValueError):self.validate(self.row|{'rom_sha256':n.r.ROM_SHA})
    def test_reject_duplicate_json_key(self):
        raw=json.dumps(self.row).encode().replace(b'"status": "PASS"',b'"status": "FAIL", "status": "PASS"')
        with self.assertRaises(ValueError):n.validate(raw,self.stderr,self.name,0,self.audit)

if __name__=='__main__':unittest.main()
