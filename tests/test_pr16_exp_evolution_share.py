"""戦闘EXP進化/控え共有の新しい境界のみ。旧native/suiteは実行しない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_evolution_share as e

PP=[0]+[20]*1062
for mid,points in {53:15,89:10,106:30,16:35,497:10}.items():PP[mid]=points
ROWS=e.x.n.p.LEVELS[414]


def example(mode):
    case=e.vectors(PP)[mode];count=2 if mode==2 else 1;sid=414 if mode==2 else 413;level=44 if mode==2 else 15
    moves,points,_=e.expected(case,level,PP,1,ROWS)
    rm,rp=([0]*4,[0]*4) if mode!=2 else e.expected(case,level,PP,0,ROWS,True)[:2]
    r=dict(schema_version=1,status='PASS',case=case['name'],candidate_sha256=e.x.CANDIDATE['sha256'],enemy_species=838,enemy_level=76,
           moves_after=moves,pp_after=points,reserve_moves_after=rm,reserve_pp_after=rp,species_before=sid,species_after=414 if mode==0 else sid,
           party_count=count,xp_before=(case['level']+1)**3-1,xp_after=level**3+1,level_before=case['level'],level_after=level,
           reserve_level_after=level if mode==2 else 0,reserve_xp_after=level**3+1 if mode==2 else 0,
           boundary=10,encounter=20,pp_spent=30,level_frame=40,reserve_level_frame=50 if mode==2 else 0,returned=100,
           turns=1,walking_steps=40,enemy_hp_before=193,enemy_hp_min=0,outcome=1,evolution_begin=50 if mode!=2 else 0,
           evolution_update=60 if mode!=2 else 0,evolution_input_pulses=1 if mode!=2 else 0,active_party_index_samples=100,reserve_battle_entries=0,
           guarded_phases=3,denied_host_write_apis=7,fresh_cores=2,save_counters=[2,3,3],party_preserved_bytes=100*count,
           initial_party_exp_stats_progress_share_are_fixtures=True,all_owners_accepted=False,issue19_complete=False,release_ready=False,warnings_errors=0)
    lines=[]
    for stage,counter in zip(e.STAGES,(2,2,3,3)):
        first=stage=='fixture';data=bytearray(100*count)
        for i in range(count):
            at=100*i;data[at:at+8]=bytes(range(8));data[at+84]=case['level'] if first else level
            struct.pack_into('<HH',data,at+86,20 if first else 30,20 if first else 30)
        lines.append(f'ESHARE_PARTY stage={stage} count={count} counter={counter} hex={data.hex()}')
        for i in range(count):
            owner=sid if first or i else r['species_after'];xp=r['xp_before'] if first else r['xp_after'];lv=case['level'] if first else level
            mm=case['moves'] if first else rm if i else moves;ps=case['points'] if first else rp if i else points;hp=20 if first else 30
            lines.append(f'ESHARE_MON stage={stage} index={i} species={owner} level={lv} xp={xp} hp={hp} maxhp={hp} held=0 bonus=0 moves='+','.join(map(str,mm))+' pp='+','.join(map(str,ps)))
    if mode!=2:
        lines+=['ESHARE_EVOLUTION phase=begin frame=50 callback=080cee71','ESHARE_EVOLUTION phase=update frame=60 callback=080cf869',f'ESHARE_EVOLUTION_INPUT frame=70 key={2 if mode else 1}']
    lines+=['original core destroyed; new core normal Continue']
    return r,('\n'.join(lines)+'\n').encode(),case


class EvolutionShareTests(unittest.TestCase):
    def accept(self,mode,mutate=None,stderr=None):
        r,err,case=example(mode)
        if mutate:mutate(r)
        if stderr:err=stderr(err)
        return e.validate(json.dumps(r).encode(),err,case,ROWS,PP)
    def test_evolution_accept_learns_original_gust(self):
        r=self.accept(0);self.assertEqual(r['species_after'],414);self.assertEqual(r['eligible_original_moves'],[16]);self.assertEqual(r['moves_after'],[53,106,16,0])
    def test_evolution_cancel_retains_metapod(self):
        r=self.accept(1);self.assertEqual(r['species_after'],413);self.assertEqual(r['eligible_original_moves'],[])
    def test_shared_nonparticipant_learns_and_persists_200bytes(self):
        r=self.accept(2);self.assertEqual(r['persisted_party']['size'],200);self.assertEqual(r['reserve_eligible_original_moves'],[497]);self.assertEqual(r['reserve_pp_after'][:2],[15,8])
    def test_evolution_not_same_as_regular_metapod_levelup(self):
        c=e.vectors(PP)[0];mm,_,eligible=e.expected(c,20,PP,1,ROWS);self.assertEqual(eligible,[16]);self.assertNotIn(77,mm)
    def test_phantom_reserve_is_rejected(self):
        with self.assertRaises(ValueError):self.accept(0,lambda r:r.update(reserve_level_after=10))
    def test_wrong_cancel_key_is_rejected(self):
        with self.assertRaises(ValueError):self.accept(1,stderr=lambda b:b.replace(b'frame=70 key=2',b'frame=70 key=1'))
    def test_wrong_japanese_callback_is_rejected(self):
        with self.assertRaises(ValueError):self.accept(0,stderr=lambda b:b.replace(b'080cee71',b'080cee70'))
    def test_cancel_cannot_claim_evolved_species(self):
        with self.assertRaises(ValueError):self.accept(1,lambda r:r.update(species_after=414))
    def test_reserve_must_never_enter_battle(self):
        with self.assertRaises(ValueError):self.accept(2,lambda r:r.update(reserve_battle_entries=1))
    def test_participation_samples_required(self):
        with self.assertRaises(ValueError):self.accept(2,lambda r:r.update(active_party_index_samples=0))
    def test_reserve_pp_may_not_be_spent(self):
        with self.assertRaises(ValueError):self.accept(2,lambda r:r['reserve_pp_after'].__setitem__(0,14))
    def test_all_party_bytes_required(self):
        with self.assertRaises(ValueError):self.accept(2,stderr=lambda b:b.replace(b'count=2',b'count=1'))
    def test_reserve_getter_cannot_be_missing(self):
        with self.assertRaises(ValueError):self.accept(2,stderr=lambda b:b.replace(b'ESHARE_MON stage=saved index=1',b'OTHER stage=saved index=1'))
    def test_hp_over_maximum_rejected(self):
        with self.assertRaises(ValueError):self.accept(0,stderr=lambda b:b.replace(b'hp=30 maxhp=30',b'hp=999 maxhp=30'))
    def test_fake_save_counter_rejected(self):
        with self.assertRaises(ValueError):self.accept(2,stderr=lambda b:b.replace(b'continued count=2 counter=3',b'continued count=2 counter=4'))
    def test_strict_schema_and_scope_reject_bool_or_extra(self):
        for k,v in [('fresh_cores',True),('issue19_complete',True),('release_ready',True),('warnings_errors',1),('unknown',0)]:
            with self.subTest(k=k),self.assertRaises(ValueError):self.accept(0,lambda r:r.update({k:v}))
    def test_duplicate_json_key_rejected(self):
        r,err,case=example(0);out=json.dumps(r).encode();out=out[:-1]+b',"status":"PASS"}'
        with self.assertRaises(ValueError):e.validate(out,err,case,ROWS,PP)
    def test_duplicate_mon_phase_rejected(self):
        with self.assertRaises(ValueError):self.accept(2,stderr=lambda b:b.replace(b'stage=saved index=1',b'stage=saved index=0'))
    def test_summary_and_host_write_evidence_rejected(self):
        for marker in (b'BOUNDARY_SELECTION',b'FORBIDDEN'):
            with self.subTest(marker=marker),self.assertRaises(ValueError):self.accept(0,stderr=lambda b:b+marker)
    def test_fresh_core_required(self):
        with self.assertRaises(ValueError):self.accept(2,stderr=lambda b:b.replace(b'original core destroyed; new core normal Continue\n',b''))
    def test_unknown_vector_rejected(self):
        r,err,case=example(2);case['moves'][1]=33
        with self.assertRaises(ValueError):e.validate(json.dumps(r).encode(),err,case,ROWS,PP)
    def test_pending_keeps_saved_success_without_native_replay(self):
        r=self.accept(0);vv=e.vectors(PP);accepted={r['case']:{'result':r}}
        self.assertEqual([c['name'] for c in e.x.pending(vv,accepted)],[c['name'] for c in vv[1:]])
    def test_native_barriers_never_dispatch_or_write(self):
        text=(e.ROOT/e.C).read_text();main=text.split('int main(int argc,char **argv)')[1]
        for block in main.split('a_guard(c);')[1:]:
            guarded=block.split('a_restore(c,&saved)')[0]
            for token in ('write8(','write16(','write32(','set_mon_data','p02s_set_data','call_preserving(','qol_get_party_data(','create_mon('):self.assertNotIn(token,guarded)
        self.assertEqual(main.count('a_guard(c);'),3);self.assertIn('offset=90;offset<=98',main);self.assertIn('100*e_count',main)
        self.assertNotIn('boundary_old_',main);self.assertIn('c->runFrame=e_frame',main)
    def test_source_oracle_reads_saved_original_not_rom(self):
        source=(e.ROOT/e.SELF).read_text().split('def original_sources(folder):')[1].split('\ndef expected(')[0]
        self.assertIn("cp['summary']['files']['evolution.bin']",source);self.assertIn('x.n.p.EVOLUTIONS[sid]',source);self.assertNotIn('candidate.gba',source)


if __name__=='__main__':unittest.main()
