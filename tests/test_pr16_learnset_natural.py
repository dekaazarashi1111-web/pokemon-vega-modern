"""自然初期技のraw4行境界と実測証拠validatorの新規限定試験。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_learnset_natural as n


class InitialTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(n.initial([],1),[0,0,0,0])
    def test_below(self):self.assertEqual(n.initial([(33,2)],1),[0,0,0,0])
    def test_exact(self):self.assertEqual(n.initial([(33,1),(81,2)],2),[33,81,0,0])
    def test_last_four_raw(self):self.assertEqual(n.initial([(33,1),(81,1),(45,2),(45,2),(85,3)],3),[81,45,85,0])
    def test_duplicates_do_not_pull_fifth(self):self.assertEqual(n.initial([(33,1),(45,2),(45,2),(45,2),(45,2)],2),[45,0,0,0])
    def test_future_excluded(self):self.assertEqual(n.initial([(33,1),(45,3)],2),[33,0,0,0])
    def test_original_order_retained(self):self.assertEqual(n.initial([(85,1),(33,1),(45,1)],1),[85,33,45,0])
    def test_unsorted(self):
        with self.assertRaises(ValueError):n.initial([(33,2),(45,1)],3)
    def test_invalid_rows(self):
        for row in [(0,1),(1063,1),(True,1),(33,False),(33,0),(33,101),(33,),('33',1)]:
            with self.subTest(row=row),self.assertRaises(ValueError):n.initial([row],1)
    def test_invalid_levels(self):
        for level in [0,101,True,1.0,'1']:
            with self.subTest(level=level),self.assertRaises(ValueError):n.initial([],level)
    def test_row_limit(self):
        with self.assertRaises(ValueError):n.initial([(33,1)]*129,1)
    def test_butterfree_source(self):self.assertEqual(n.initial(n.p.LEVELS[414],44),[375,554,537,497])


class EvidenceTests(unittest.TestCase):
    def fixture(self):
        pp=[0]+[15]*1062;rows={838:[(71,1),(310,1)]}
        r=dict(schema_version=1,status='PASS',case=n.CASE,candidate_sha256=n.CANDIDATE['sha256'],
               enemy_species=838,enemy_level=1,enemy_moves=[71,310,0,0],enemy_pp=[15,15,0,0],moves_after=[53,89,497,0],pp_after=[14,15,15,0],
               xp_before=999,xp_threshold=1000,xp_after=1100,level_before=43,level_after=44,boundary=100,encounter=200,pp_spent=300,level_frame=400,returned=500,
               turns=1,walking_steps=48,enemy_hp_before=100,enemy_hp_min=0,outcome=1,guarded_phases=3,denied_host_write_apis=7,fresh_cores=2,
               save_counters=[2,3,3],party_preserved_bytes=100,initial_party_exp_stats_progress_are_fixtures=True,all_owners_accepted=False,issue19_complete=False,release_ready=False,warnings_errors=0)
        parts=[bytes(100),bytes(8)+b'\x01'*92]
        err='original core destroyed; new core normal Continue\n'
        for stage,count,value in [('fixture',2,parts[0]),('returned',2,parts[1]),('saved',3,parts[1]),('continued',3,parts[1])]:
            err+=f'NATURAL_PARTY stage={stage} counter={count} hex={value.hex()}\n'
        for i,mid in enumerate(r['enemy_moves']):err+=f'NATURAL_INITIAL slot={i} move={mid} pp={pp[mid]} expected={mid} expected_pp={pp[mid]}\n'
        return r,err.encode(),rows,pp
    def test_valid_scoped_evidence(self):
        r,err,rows,pp=self.fixture();self.assertEqual(n.validate(json.dumps(r),err,rows,pp)['original_rows'],rows[838])
    def test_schema(self):
        r,err,rows,pp=self.fixture();r['new']=1
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_boolean_counter(self):
        r,err,rows,pp=self.fixture();r['turns']=True
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_no_level_frame(self):
        r,err,rows,pp=self.fixture();r['level_frame']=0
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_no_exp_reward(self):
        r,err,rows,pp=self.fixture();r['xp_after']=999
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_wrong_wild_move(self):
        r,err,rows,pp=self.fixture();r['enemy_moves'][0]=33
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_original_observation_missing(self):
        r,err,rows,pp=self.fixture();err=err.replace(b'NATURAL_INITIAL',b'OTHER')
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_no_new_core(self):
        r,err,rows,pp=self.fixture();r['fresh_cores']=1
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_scope_escalation(self):
        for key in ['all_owners_accepted','issue19_complete','release_ready']:
            r,err,rows,pp=self.fixture();r[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_missing_write_barrier(self):
        r,err,rows,pp=self.fixture();r['guarded_phases']=2
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_no_saved_counter(self):
        r,err,rows,pp=self.fixture();err=err.replace(b'continued counter=3',b'continued counter=2')
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err,rows,pp)
    def test_warning(self):
        r,err,rows,pp=self.fixture()
        with self.assertRaises(ValueError):n.validate(json.dumps(r),err+b'mGBA[WARN]',rows,pp)
    def test_duplicate_json(self):
        r,err,rows,pp=self.fixture();out=json.dumps(r).replace('"schema_version": 1','"schema_version": 1, "schema_version": 1')
        with self.assertRaises(ValueError):n.validate(out,err,rows,pp)


if __name__=='__main__':unittest.main(verbosity=2)
