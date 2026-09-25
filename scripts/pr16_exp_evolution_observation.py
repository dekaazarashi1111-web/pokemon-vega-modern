#!/usr/bin/env python3
"""未受入3caseの観測契約修復。変更したvalidatorだけを再検証する。"""
from __future__ import annotations
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_evolution_sync as s
e=s.e
SELF='scripts/pr16_exp_evolution_observation.py'
TEST='tests/test_pr16_exp_evolution_observation.py'
SYNC_TESTS=(
 'test_three_native_contracts_accept_complete_raw_data',
 'test_raw_species_exp_move_pp_and_bonus_are_independently_checked',
 'test_missing_or_duplicate_fight_evidence_rejected',
 'test_unbounded_or_unordered_fight_key_rejected',
 'test_observation_is_read_only_and_all_three_barriers_remain',
 'test_fight_wait_is_bounded_neutral_then_ordinary_key',
)

def validate(out,err,case,rows,pp):
    result=s.validate(out,err,case,rows,pp)
    e.need(b'ESHARE_SLOT_MISMATCH ' not in err,'no oracle mismatch may be accepted')
    ready=re.findall(rb'^ESHARE_FIELD_READY frame=(\d+) stable=(\d+)$',err,re.M)
    e.need(len(ready)==err.count(b'ESHARE_FIELD_READY '),'complete neutral readiness evidence')
    if case['mode']==2:
        e.need(len(ready)==1 and 0<int(ready[0][0])<result['boundary'] and int(ready[0][1])==120,'neutral shared fixture readiness')
    else:e.need(not ready,'no phantom shared fixture readiness')
    result['evolution_begin_observed']=bool(result['evolution_begin'])
    result['shared_fixture_neutral_frames']=120 if ready else 0
    return result


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        # expected()/callback契約とCが変わったため旧24unitを同一入力と偽って再利用しない。
        # 旧native受入、初回失敗原本、保存済み成功caseは再実行しない。
        e.write(e.PROOF/'validation-impact.json',{
            'prior_failed_runs':[36075652959,36076513362],
            'changed_contracts':['evolved_current_level_rows','frame_observed_callback','neutral_shared_fixture_readiness'],
            'revalidation_reason_ja':'validator/C変更に直結する24+6既存unitと新規unitのみ。旧nativeは再実行0。',
            'accepted_native_reruns':0,'old_unit_reuse_claimed':False})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_evolution_share',
                 *('tests.test_pr16_exp_evolution_sync.SyncTests.'+name for name in SYNC_TESTS),
                 'tests.test_pr16_exp_evolution_observation','-v']
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,s.SELF,s.TEST,s.C))
    e.SELF,e.TEST,e.C=SELF,TEST,s.C
    e.configure();e.x.m.run=scoped_run;e.x.validate=validate


if __name__=='__main__':
    configure()
    actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
