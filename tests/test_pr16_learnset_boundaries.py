"""新EXP境界のoracle/偽証拠拒否/成功再選択防止。旧unitを再実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_learnset_boundaries as x
PP=[0]+[20]*1062
PP[53]=15;PP[89]=10
ROWS=x.n.p.LEVELS[414]


def sample(index=0):
    case=x.vectors(PP)[index];level=14 if index==1 else 44
    moves,points,prompts,_=x.expected(case,level,PP,1,ROWS)
    r=dict(schema_version=1,status='PASS',case=case['name'],candidate_sha256=x.CANDIDATE['sha256'],
           enemy_species=838,enemy_level=76,moves_after=moves,pp_after=points,
           xp_before=(case['level']+1)**3-1,xp_threshold=(case['level']+1)**3,xp_after=level**3+1,
           level_before=case['level'],level_after=level,boundary=800,encounter=1900,pp_spent=2000,
           level_frame=2400,returned=4000,turns=1,walking_steps=48,enemy_hp_before=193,enemy_hp_min=0,outcome=1,
           summaries=prompts,selections=prompts,summary_frame=2600 if prompts else 0,selection_frame=2800 if prompts else 0,
           guarded_phases=3,denied_host_write_apis=7,fresh_cores=2,save_counters=[2,3,3],party_preserved_bytes=100,
           initial_party_exp_stats_progress_are_fixtures=True,all_owners_accepted=False,issue19_complete=False,release_ready=False,warnings_errors=0)
    before=b'\x11'*100;after=before[:8]+b'\x22'*92
    err=b''.join(b'NATURAL_PARTY stage='+stage+b' counter='+str(count).encode()+b' hex='+data.hex().encode()+b'\n'
                 for stage,count,data in [(b'fixture',2,before),(b'returned',2,after),(b'saved',3,after),(b'continued',3,after)])
    for _ in range(prompts):err+=f"BOUNDARY_SELECTION frame=2800 cursor={case['slot']} key={2 if case['mode'] else 1} mode={case['mode']}\n".encode()
    err+=b'original core destroyed; new core normal Continue\n'
    return r,err,case


class BoundaryTests(unittest.TestCase):
    def check(self,r,err,case):return x.validate(json.dumps(r).encode(),err,case,ROWS,PP)
    def test_four_new_cases_only(self):
        cases=x.vectors(PP);self.assertEqual(len(cases),4)
        self.assertNotIn(x.n.CASE,[c['name'] for c in cases]);self.assertEqual(len({c['name'] for c in cases}),4)
    def test_known_pp_not_reset(self):
        r,err,c=sample();v=self.check(r,err,c);self.assertEqual(v['pp_after'][2],9);self.assertEqual(v['summaries'],0)
    def test_multiple_levels_same_level_three_moves(self):
        r,err,c=sample(1);v=self.check(r,err,c);self.assertEqual(v['moves_after'],[53,77,78,79]);self.assertGreater(v['level_after']-v['level_before'],1)
    def test_replacement(self):
        r,err,c=sample(2);v=self.check(r,err,c);self.assertEqual(v['moves_after'],[53,497,33,45]);self.assertEqual(v['selections'],1)
    def test_summary_refusal_preserves_four(self):
        r,err,c=sample(3);v=self.check(r,err,c);self.assertEqual(v['moves_after'],c['moves']);self.assertEqual(v['pp_after'][1:],c['points'][1:])
    def test_no_repeat_success(self):
        r,err,c=sample();a={c['name']:{'result':self.check(r,err,c)}}
        self.assertEqual(len(x.pending(x.vectors(PP),a)),3)
        self.assertNotIn(c,x.pending(x.vectors(PP),a))
    def test_unknown_saved_case_rejected(self):
        with self.assertRaises(ValueError):x.pending(x.vectors(PP),{'other':{}})
    def test_changed_saved_fixture_rejected(self):
        r,err,c=sample();v=self.check(r,err,c);v['fixture']=dict(c,level=42)
        with self.assertRaises(ValueError):x.pending(x.vectors(PP),{c['name']:{'result':v}})
    def test_changed_saved_candidate_rejected(self):
        r,err,c=sample();v=self.check(r,err,c);v['candidate_sha256']='0'*64
        with self.assertRaises(ValueError):x.pending(x.vectors(PP),{c['name']:{'result':v}})
    def test_bad_scope_and_types(self):
        r,e,c=sample()
        for k,val in [('status','FAIL'),('case','old'),('candidate_sha256','0'*64),('issue19_complete',True),('fresh_cores',1),('guarded_phases',2),('initial_party_exp_stats_progress_are_fixtures',False),('xp_after',True),('warnings_errors',False)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:val}),e,c)
    def test_duplicate_json_key_rejected(self):
        r,e,c=sample();s=json.dumps(r)[:-1]+',"status":"PASS"}'
        with self.assertRaises(ValueError):x.validate(s.encode(),e,c,ROWS,PP)
    def test_extra_missing_key_rejected(self):
        r,e,c=sample()
        for v in [dict(r,unexpected=0),{k:v for k,v in r.items() if k!='outcome'}]:
            with self.assertRaises(ValueError):self.check(v,e,c)
    def test_wrong_moves_pp_rejected(self):
        r,e,c=sample(2)
        for k,seq in [('moves_after',[53,89,33,45]),('pp_after',[14,19,9,10]),('moves_after',[53,497,True,45])]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:seq}),e,c)
    def test_bad_native_chronology(self):
        r,e,c=sample()
        for k,val in [('encounter',800),('pp_spent',1900),('level_frame',1000),('returned',2400),('outcome',4),('enemy_hp_min',1),('turns',0)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:val}),e,c)
    def test_bad_growth_curve(self):
        r,e,c=sample()
        for k,val in [('xp_before',0),('xp_threshold',0),('xp_after',44**3-1),('xp_after',45**3),('level_after',43)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:val}),e,c)
    def test_multilevel_not_single_level(self):
        c=x.vectors(PP)[1]
        with self.assertRaises(ValueError):x.expected(c,11,PP,1,ROWS)
    def test_summary_evidence_required(self):
        r,e,c=sample(2)
        for changed in [e.replace(b'BOUNDARY_SELECTION',b'NOT_A_SELECTION'),e.replace(b'key=1',b'key=2')]:
            with self.assertRaises(ValueError):self.check(r,changed,c)
    def test_saved_lifecycle_required(self):
        r,e,c=sample()
        for changed in [e.replace(b'counter=3',b'counter=2'),e.replace(b'stage=continued',b'stage=missing'),e.replace(b'new core normal Continue',b'same core'),e+b'FORBIDDEN\n']:
            with self.assertRaises(ValueError):self.check(r,changed,c)
    def test_persisted_bytes_must_match(self):
        r,e,c=sample();lines=e.splitlines();lines[3]=lines[3][:-2]+b'33'
        with self.assertRaises(ValueError):self.check(r,b'\n'.join(lines)+b'\n',c)
    def test_observation_never_calls_accepted_main(self):
        text=(x.ROOT/x.C).read_text();self.assertIn('pr16_boundaries_helpers.h',text)
        self.assertEqual(text.count('int main('),1);self.assertEqual(text.count('a_guard(c)'),3)
        guarded=text[text.index('struct mCore saved=*c;a_guard(c)'):text.index('a_restore(c,&saved);unsigned xp')]
        for token in ('write8(','write16(','write32(','p02s_set_data(','call_preserving(','create_mon('):self.assertNotIn(token,guarded)


if __name__=='__main__':unittest.main()
