"""最初の質問のnative証拠契約。合成unit fixtureはnative受入にしない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_learnset_first_refuse as f
PP=[0]+[20]*1062
PP[53]=15;PP[89]=10
ROWS=f.x.n.p.LEVELS[414]


def sample():
    case=f.vectors(PP)[0]
    r=dict(schema_version=1,status='PASS',case=case['name'],candidate_sha256=f.x.CANDIDATE['sha256'],
           enemy_species=838,enemy_level=76,moves_after=case['moves'][:],pp_after=[14,8,9,10],
           xp_before=44**3-1,xp_threshold=44**3,xp_after=44**3+20,level_before=43,level_after=44,
           boundary=800,encounter=1900,pp_spent=2000,level_frame=2400,returned=4000,turns=1,
           walking_steps=48,enemy_hp_before=193,enemy_hp_min=0,outcome=1,summaries=0,selections=0,
           summary_frame=0,selection_frame=0,guarded_phases=3,denied_host_write_apis=7,fresh_cores=2,
           save_counters=[2,3,3],party_preserved_bytes=100,initial_party_exp_stats_progress_are_fixtures=True,
           all_owners_accepted=False,issue19_complete=False,release_ready=False,warnings_errors=0,
           first_refusal_pulses=1,stop_confirmation_pulses=1,first_refusal_frame=2700,stop_confirmation_frame=3000,
           summary_never_opened=True,refusal_opcode=90,stop_opcode=91)
    before=bytearray(b'\x11'*100);before[84]=43;struct.pack_into('<HH',before,86,104,104)
    after=bytearray(before);after[8]=0x22;after[84]=44;struct.pack_into('<HH',after,86,106,106)
    err=b''.join(b'NATURAL_PARTY stage='+label+b' counter='+str(counter).encode()+b' hex='+data.hex().encode()+b'\n'
                 for label,counter,data in [(b'fixture',2,before),(b'returned',2,after),(b'saved',3,after),(b'continued',3,after)])
    err+=b'FIRST_REFUSAL frame=2700 script=08123450 opcode=90 key=2 pending=497\n'
    err+=b'FIRST_REFUSAL frame=3000 script=08123480 opcode=91 key=1 pending=497\n'
    err+=b'original core destroyed; new core normal Continue\n'
    return r,err,case


class FirstRefusalTests(unittest.TestCase):
    def check(self,r,e,c):return f.validate(json.dumps(r).encode(),e,c,ROWS,PP)
    def test_first_question_preserves_four_and_unused_pp(self):
        r,e,c=sample();v=self.check(r,e,c)
        self.assertEqual(v['moves_after'],c['moves']);self.assertEqual(v['pp_after'][1:],c['points'][1:])
        self.assertEqual(v['native_health']['status'],'PASS');self.assertEqual(v['eligible_original_moves'],[497])
    def test_one_new_case_not_old_summary_refusal(self):
        self.assertEqual(len(f.CASES),1)
        old=f.load(f.ROOT/f.OLD_CP)['accepted'];self.assertNotIn(f.CASES[0][0],old)
    def test_accepted_case_not_rescheduled(self):
        r,e,c=sample();self.assertEqual(f.x.pending([c],{c['name']:{'result':self.check(r,e,c)}}),[])
    def test_changed_accepted_fixture_rejected(self):
        r,e,c=sample();v=self.check(r,e,c);v['fixture']=dict(c,level=42)
        with self.assertRaises(ValueError):f.x.pending([c],{c['name']:{'result':v}})
    def test_wrong_scope_types_rejected(self):
        r,e,c=sample()
        for k,value in [('status','FAIL'),('issue19_complete',True),('release_ready',True),('all_owners_accepted',True),('fresh_cores',1),('guarded_phases',2),('warnings_errors',False),('first_refusal_pulses',True),('level_after',True),('summary_never_opened',1)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:value}),e,c)
    def test_summary_refusal_cannot_substitute(self):
        r,e,c=sample()
        for k,value in [('summaries',1),('selections',1),('summary_frame',2600),('summary_never_opened',False)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:value}),e,c)
        with self.assertRaises(ValueError):self.check(r,e+b'BOUNDARY_SELECTION frame=2800\n',c)
    def test_no_missing_or_unknown_result_fields(self):
        r,e,c=sample()
        for changed in (dict(r,extra=0),{k:v for k,v in r.items() if k!='stop_opcode'}):
            with self.assertRaises(ValueError):self.check(changed,e,c)
    def test_duplicate_result_key_rejected(self):
        r,e,c=sample()
        with self.assertRaises(ValueError):f.validate((json.dumps(r)[:-1]+',"status":"PASS"}').encode(),e,c,ROWS,PP)
    def test_wrong_or_missing_first_key_rejected(self):
        r,e,c=sample()
        for changed in (e.replace(b'key=2',b'key=1'),e.replace(b'key=2',b'key=0'),e.replace(b'opcode=90',b'opcode=91')):
            with self.assertRaises(ValueError):self.check(r,changed,c)
    def test_wrong_stop_key_rejected(self):
        r,e,c=sample()
        with self.assertRaises(ValueError):self.check(r,e.replace(b'opcode=91 key=1',b'opcode=91 key=2'),c)
    def test_pending_move_and_rom_pointer_required(self):
        r,e,c=sample()
        for changed in (e.replace(b'pending=497',b'pending=53'),e.replace(b'script=08123450',b'script=02123450'),e.replace(b'script=08123480',b'script=08123450')):
            with self.assertRaises(ValueError):self.check(r,changed,c)
    def test_first_then_stop_raw_order_required(self):
        r,e,c=sample();lines=e.splitlines();lines[4],lines[5]=lines[5],lines[4]
        with self.assertRaises(ValueError):self.check(r,b'\n'.join(lines)+b'\n',c)
    def test_question_pulses_are_bounded(self):
        r,e,c=sample()
        for k,value in [('first_refusal_pulses',0),('first_refusal_pulses',9),('stop_confirmation_pulses',2)]:
            with self.assertRaises(ValueError):self.check(dict(r,**{k:value}),e,c)
    def test_raw_frame_binding_and_chronology(self):
        r,e,c=sample()
        for k,value in [('encounter',800),('first_refusal_frame',2400),('first_refusal_frame',2701),('stop_confirmation_frame',2700),('returned',3000),('pp_spent',1900),('turns',0),('outcome',4)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:value}),e,c)
    def test_malformed_raw_event_rejected(self):
        r,e,c=sample()
        for changed in (e.replace(b'key=2',b'key=not-a-number'),e.replace(b'frame=2700',b'frame=-1'),e+b'FIRST_REFUSAL ignored\n'):
            with self.assertRaises(ValueError):self.check(r,changed,c)
    def test_moves_pp_and_exp_cannot_be_forged(self):
        r,e,c=sample()
        for k,value in [('moves_after',[53,497,33,45]),('pp_after',[14,10,9,10]),('pp_after',[15,8,9,10]),('pp_after',[True,8,9,10]),('xp_before',0),('xp_after',45**3)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(dict(r,**{k:value}),e,c)
    def test_health_overflow_rejected(self):
        r,e,c=sample();rows=e.splitlines()
        for i in (1,2,3):
            head,raw=rows[i].split(b' hex=');p=bytearray.fromhex(raw.decode());struct.pack_into('<H',p,86,999);rows[i]=head+b' hex='+p.hex().encode()
        with self.assertRaises(ValueError):self.check(r,b'\n'.join(rows)+b'\n',c)
    def test_save_continue_requires_exact_individual(self):
        r,e,c=sample()
        for changed in (e.replace(b'counter=3',b'counter=2'),e.replace(b'stage=continued',b'stage=missing'),e.replace(b'new core normal Continue',b'same core'),e+b'FORBIDDEN\n'):
            with self.assertRaises(ValueError):self.check(r,changed,c)
        lines=e.splitlines();lines[3]=lines[3][:-2]+b'33'
        with self.assertRaises(ValueError):self.check(r,b'\n'.join(lines)+b'\n',c)
    def test_native_never_dispatches_or_writes_during_observation(self):
        source=(f.ROOT/f.C).read_text();self.assertEqual(source.count('int main('),1);self.assertEqual(source.count('a_guard(c)'),3)
        guard=source[source.index('struct mCore saved=*c;a_guard(c)'):source.index('a_restore(c,&saved);unsigned xp')]
        for token in ('write8(','write16(','write32(','p02s_set_data(','call_preserving(','create_mon(','run_function('):self.assertNotIn(token,guard)
        self.assertIn('cb!=P03F_SUMMARY_CB',guard);self.assertIn('opcode==0x5AU?QOL_KEY_B:QOL_KEY_A',guard)
    def test_only_new_units_are_selected(self):
        seen=[];old=f.BASE_RUN
        try:
            f.BASE_RUN=lambda command,*args,**kw:seen.append(command)
            f.scoped_run(['old-suite'],'unit')
        finally:f.BASE_RUN=old
        self.assertEqual(seen,[[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_first_refuse','-v']])
    def test_old_sources_unchanged(self):
        old=f.load(f.ROOT/f.OLD_CP)
        for path in (f.x.SELF,f.OLD_C,f.health_policy.SELF,f.health_policy.g.SELF,f.health_policy.g.TRACE):
            self.assertEqual(f.identity((f.ROOT/path).read_bytes()),old['source_bindings'].get(path,old.get('compiled_sources',{}).get(path)),path)


if __name__=='__main__':unittest.main()
