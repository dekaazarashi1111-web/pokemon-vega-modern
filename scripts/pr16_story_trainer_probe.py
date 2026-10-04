#!/usr/bin/env python3
"""Save101から未保存のtrainer境界だけを延長する。旧受入ソースは凍結。"""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_route_probe as retained
import pr16_story_trainer_adapter as trainer
import pr16_story_trainer_session as trainer_reader
from pr16_story_after_maori import need,identity,write
from pr16_story_milestones import DiagnosticStop
BASE='06726eca808ac62ac26a18e9abb0cec154520268'
CODE={'scripts/pr16_story_trainer_session.py','content/modernization/pr16_story_trainer_owners.json','scripts/pr16_story_trainer_adapter.py','scripts/pr16_story_trainer_probe.py','tests/test_pr16_story_trainer_adapter.py','content/modernization/pr16_story_trainer_unit.json','.github/workflows/pr16-story-trainer-adapter.yml'}

def guard():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized single-attempt trainer continuation')
    p=retained.retained.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole live draft head')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only declared trainer paths')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
    for path,binding in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'accepted source frozen '+path)
    unit=json.loads((ROOT/'content/modernization/pr16_story_trainer_unit.json').read_bytes())
    need(unit['tests']==unit['passed'] and unit['passed']>0 and unit['stderr'].count(' ... ok\n')==unit['passed'] and '\nOK\n' in unit['stderr'],'focused host tests')
    for path,binding in unit['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'new exact unit source '+path)

def walk(session,route):
    rows=[];battles=[]
    for index,(before,target)in enumerate(zip(route,route[1:])):
        if before[:2]!=target[:2]:raise DiagnosticStop('connection_adapter_pending',dict(index=index,target=target))
        need(session.last['map']+session.last['xy']==before,'current exact route tile')
        for attempt in range(3):
            prior=session.live;o=session.step((retained.direction(before,target),8),(0,48))
            if o['callback2']!=0x08055E75 or o['lock']!=0:
                if index==39 and target==[3,24,32,10]:
                    evidence=retained.clock.walking_evidence(prior,session.live,target[2:],observed_transition=True)
                    rows.append(dict(index=index,attempt=attempt,observation=o['observe'],**evidence));write(retained.ART/'walking-ledger.json',rows)
                    transition=session.live;session.step((0,600));entry=retained.battle.entry_evidence(transition,session.live);write(retained.ART/'battle-entry.json',entry)
                    battles.append(retained.battle.play(session));write(retained.ART/'battle-ledger.json',battles);break
                if index==49 and target==[3,24,38,6]:
                    row=trainer.sight(prior,session.live);write(retained.ART/'trainer-sight.json',dict(index=index,observation=o['observe'],**row))
                    trainer.observe_approach(session)
                raise DiagnosticStop('new_route_event_observation',dict(index=index,target=target,observation=o,ui=session.live['ui'],trainer=session.live['route']['trainer_id']))
            evidence=retained.clock.walking_evidence(prior,session.live,target[2:]);rows.append(dict(index=index,attempt=attempt,observation=o['observe'],**evidence));write(retained.ART/'walking-ledger.json',rows)
            if o['xy']==target[2:]:break
        else:raise DiagnosticStop('unpassed_route_tile',dict(index=index,target=target))
    raise DiagnosticStop('facility_adapter_pending')

def inspect(rom):
    original=original_inspect(rom)
    data=json.loads((ROOT/'content/modernization/pr16_story_trainer_owners.json').read_bytes())
    need(identity(rom)==data['candidate'],'trainer fixed ROM identity')
    for row in data['bindings']:
        need(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'exact trainer owner '+row['meaning'])
    write(retained.ART/'trainer-owners.json',data)
    return original
original_inspect=retained.owners.inspect

def main():
    retained.reader=trainer_reader;retained.owners.inspect=inspect
    retained.OUT=ROOT/'.local/pr16-story-trainer-adapter';retained.ART=retained.OUT/'artifact';retained.guard=guard;retained.walk=walk;retained.main()
if __name__=='__main__':main()
