#!/usr/bin/env python3
"""Extend exact real capture with native switch, a turn and a third cold core.

The old source and raw acceptance are immutable. This generates a NEW explicitly
scoped controller and retains its exact bytes, not a relabelled old run.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_natural_capture as capture
import pr16_natural_capture_checkpoint as retained
need=capture.need;r=capture.r;common=capture.common;shop=capture.shop
SELF='scripts/pr16_captured_battle.py';SOURCE='tools/mgba_pr16_captured_battle.h';TEST='tests/test_pr16_captured_battle.py';WORKFLOW='.github/workflows/pr16-captured-battle.yml'
OUT=ROOT/'.local/pr16-captured-battle';SCOPE='PR16_NATURAL_CAPTURE_SWITCH_TURN_TWO_SAVES_THREE_CORES'
PROOF=re.compile(rb'^CAPTURED_BATTLE_PROOF (\{[^\n]+\})$',re.M)
TRACE=('encounter','menu','switched','spent','field','saved','reloaded')
EXTRA=r'''g_shot("reloaded");
 unsigned old_steps=n_steps,old_outcome=n_outcome;struct NBProof follow=nb_run(c,v);n_steps=old_steps;n_outcome=old_outcome;
 a_require(read32(c,P03_SAVE_COUNTER)==counter+2U,"second ordinary save counter differs");
 b_copy(c,QOL_PLAYER_PARTY,party,200U);g_inventory(c,now);a_require(!memcmp(now,expected,sizeof(now)),"captured battle changed inventory");
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);a_require(b_continue(c),"third core Continue failed");follow.reloaded=b_frames;
 b_copy(c,QOL_PLAYER_PARTY,reloaded,200U);g_inventory(c,now);a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U && !memcmp(party,reloaded,200U) && !memcmp(now,expected,sizeof(now)) && read32(c,P03_SAVE_COUNTER)==counter+2U,"third core changed captured battle/save state");g_shot("captured-battle-reloaded");
 fprintf(stderr,"CAPTURED_BATTLE_PROOF {\"encounter\":%u,\"menu\":%u,\"switched\":%u,\"spent\":%u,\"field\":%u,\"saved\":%u,\"reloaded\":%u,\"steps\":%u,\"enemy_species\":%u,\"enemy_level\":%u,\"ability\":%u,\"move\":%u,\"pp_before\":%u,\"pp_after\":%u,\"outcome\":%u,\"captured_personality\":%u,\"party_slot\":1,\"party_and_inventory_persisted\":true,\"manual_saves\":2,\"fresh_cores\":3,\"gear_acquisition_accepted\":false,\"full_p05_acceptance\":false,\"release_ready\":false}\n",follow.encounter,follow.menu,follow.switched,follow.spent,follow.field,follow.saved,follow.reloaded,follow.steps,follow.species,follow.level,follow.ability,follow.move,follow.pp_before,follow.pp_after,follow.outcome,n_pid);
'''


def controller():
    text=(ROOT/capture.SOURCE).read_text()
    for old,new in [('int main(int argc,char**argv){','#include "mgba_pr16_captured_battle.h"\nint main(int argc,char**argv){'),(capture.SCOPE,SCOPE),('g_shot("reloaded");',EXTRA),('\\"manual_saves\\":1,\\"fresh_cores\\":2','\\"manual_saves\\":2,\\"fresh_cores\\":3'),('\\"battle_connection_accepted\\":false','\\"battle_connection_accepted\\":true')]:
        need(text.count(old)==1,'captured-battle projection preimage differs: '+old);text=text.replace(old,new,1)
    return text


def validate(raw,stderr,name,code,audit):
    actual=common.strict_json(raw);need(type(actual) is dict,'captured-battle result required')
    for k,v in dict(scope=SCOPE,manual_saves=2,fresh_cores=3,battle_connection_accepted=True).items():need(common.same_typed(actual.get(k),v),'captured battle scope differs: '+k)
    # COPY used only to delegate unchanged initial-capture structural checks.
    normalized=dict(actual,scope=capture.SCOPE,manual_saves=1,fresh_cores=2,battle_connection_accepted=False)
    capture.validate(json.dumps(normalized).encode(),stderr,name,code,audit)
    matches=PROOF.findall(stderr);need(len(matches)==1,'captured-battle raw proof missing/duplicated');proof=common.strict_json(matches[0])
    fixed=dict(ability=26,captured_personality=actual['personality'],party_slot=1,party_and_inventory_persisted=True,manual_saves=2,fresh_cores=3,gear_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False)
    dynamic={'steps','enemy_species','enemy_level','move','pp_before','pp_after','outcome',*TRACE}
    need(set(proof)==set(fixed)|dynamic,'captured-battle proof schema differs')
    for k,v in fixed.items():need(common.same_typed(proof[k],v),'captured-battle proof differs: '+k)
    need(all(type(proof[k]) is int for k in dynamic),'captured-battle counters must be integers')
    need(actual['witness']['reloaded']<proof['encounter'] and proof['reloaded']==actual['total_frames'],'follow-on battle/reload not ordered after capture')
    need(all(proof[a]<proof[b] for a,b in zip(TRACE,TRACE[1:])),'captured-battle action/save order differs')
    need(1<=proof['steps']<=1024 and 1<=proof['move']<=2048 and 1<=proof['pp_before']<=64 and 0<=proof['pp_after']<proof['pp_before'] and proof['pp_before']-proof['pp_after']<=2 and proof['outcome'] in (1,4),'captured-battle turn values invalid')
    need(any(s['species']==proof['enemy_species'] and s['min']<=proof['enemy_level']<=s['max'] for s in audit['cases'][name]['table']['slots']),'follow-on enemy not from native table')
    return dict(capture_and_battle=actual,battle=proof)


def run():
    m=shop.base.load();out=m.prepare_output(OUT);recipe=capture.repair.run();candidate=capture.repair.OUTPUT/'candidate.gba';raw=r.layer.source.checked(candidate,capture.SHA);seed=ROOT/m.SEED;r.layer.source.checked(seed,m.SEED_SHA)
    audit=capture.oracle(raw);source=controller();(out/'controller.c').write_text(source);(out/'oracle.json').write_bytes(r.stable(audit));(out/'candidate.json').write_bytes(r.stable(recipe))
    receipt=retained.build();prior_files=retained.display.archive((ROOT/retained.DIRECTORY/str(retained.RECORDS['capture'][0])/'original.zip').read_bytes());old=common.strict_json(prior_files['pr16-natural-capture/result.json'])
    paths=set(old['sources'])|{SELF,SOURCE,TEST,WORKFLOW};bindings={p:common.identity(ROOT/p) for p in sorted(paths)};protected={str(p):common.identity(p) for p in (seed,candidate)};results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-captured-battle-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):(work/target).write_text(m.embed((ROOT/src).read_text(),'captured_battle_embedded_'+str(i)))
            (work/'pr16_shop_breeding_helpers.c').write_text(m.embed((ROOT/shop.base.PARENT_C).read_text(),'captured_battle_breeding'))
            (work/'pr16_capture_shop_helpers.c').write_text(m.embed((ROOT/shop.SOURCE).read_text(),'captured_battle_shop'))
            binary=work/'runner';_,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(out/'controller.c'),'-lmgba','-o',str(binary)],out/'compile',120);need(common.require_exited(process)==0,'captured-battle compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10);m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(name):
                private=work/(name+'.srm');shutil.copyfile(seed,private);stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),capture.SHA,m.SEED_SHA,name,str(out/name)],out/name,900)
                try:return dict(name=name,result=validate(stdout,stderr,name,common.require_exited(process),audit),process=process),None
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:return None,dict(name=name,error=str(exc),process=process)
            with ThreadPoolExecutor(max_workers=2) as pool:
                for value,error in pool.map(one,capture.CASES):
                    if value:results.append(value)
                    if error:failures.append(error)
    finally:
        need(protected=={p:common.identity(Path(p)) for p in protected},'captured-battle inputs changed');need(bindings=={p:common.identity(ROOT/p) for p in bindings},'captured-battle sources changed')
    report=dict(schema_version=1,status='FAIL' if failures else 'PASS',scope=SCOPE,candidate=r.identity(raw),sources=bindings,controller=r.identity(source.encode()),oracle=audit,
                results=results,failures=failures,guard_checks=guards,new_native_processes=2,successful_fresh_cores=sum(row['result']['battle']['fresh_cores'] for row in results),
                captured_to_native_battle_accepted=not failures,gear_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0)
    (out/'result.json').write_bytes(r.stable(report));need(not failures,'captured-battle native failure; inspect originals');return report
if __name__=='__main__':
    try:print(json.dumps(run()))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
