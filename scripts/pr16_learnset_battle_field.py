#!/usr/bin/env python3
"""通常非link戦闘のIS_MASTER bitを正しく検査し、実測前提を記録する。"""
from __future__ import annotations
import json
import subprocess
import sys
import pr16_learnset_battle as b
import pr16_learnset_battle_retry as r
m=b.m
RUN=35833129256
HEAD='120b1b365d8242e5bc840328c5c90ca129d99ae5'
REFLECTED='8ae7d2180a0e29ba83f277415ea4cc3e486dc8e5'
ARTIFACT={'id':10737588489,'name':'pr16-learnset-battle-proof','size_in_bytes':19413,
          'digest':'sha256:861cee5ee038de44013ce63cee14248d92cecb738165c4911a218bf153ef925b'}
EXTRA={'scripts/pr16_learnset_battle_field.py','tests/test_pr16_learnset_battle_field.py'}
ORIGINAL_RUN=m.run


def render(text):
    text=r.once(text,'read32(c,ADDR_BATTLE_TYPE_FLAGS)==0','read32(c,ADDR_BATTLE_TYPE_FLAGS)==4U')
    text=r.once(text,'a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==4U',
        'fprintf(stderr,"LEARNED_ENCOUNTER frame=%u flags=%08x party=%u species=%u battle_pid=%08x party_pid=%08x\\n",lb_frames,read32(c,ADDR_BATTLE_TYPE_FLAGS),read16(c,ADDR_BATTLER_PARTY_INDEXES),read16(c,ADDR_BATTLE_MONS),read32(c,ADDR_BATTLE_MONS+0x48),read32(c,QOL_PLAYER_PARTY));\n'
        '    g_shot("encounter-boundary");\n'
        '    /* BATTLE_TYPE_IS_MASTER=4 is always set for non-link battles. */\n'
        '    a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==4U')
    text=r.once(text,'c->setKeys(c,key);c->runFrame(c);++lb_frames;',
        'c->setKeys(c,key);c->runFrame(c);++lb_frames;\n'
        '    if(read8(c,BATTLE_CORE_BATTLE_OUTCOME))lb_outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);')
    return text


def install():
    p=b.ROOT/b.C;old=subprocess.check_output(['git','show',REFLECTED+':'+b.C],cwd=b.ROOT).decode();new=render(old)
    m.need(p.read_text() in (old,new),'unexpected native source before field repair')
    if p.read_text()==old:p.write_text(new)
    b.CODE|=r.EXTRA|EXTRA


def inherit():
    prior=m.load(b.ROOT/b.CP)
    m.need(prior['source_head']==HEAD and prior['run_id']==RUN and prior['status']=='FAIL'
        and prior['native_processes']==1 and prior['new_unit_tests']==6 and prior['inherited_unit_tests']==16,'prior battle boundary')
    run=b.fetch('actions/runs/'+str(RUN));meta=b.fetch('actions/artifacts/'+str(ARTIFACT['id']))
    m.need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==HEAD,'prior run')
    m.need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired'] and meta['workflow_run']['head_sha']==HEAD,'prior artifact')
    raw=b.fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
    m.need(m.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'prior archive')
    data=b.zip_members(raw);v=json.loads(data['verification.json'])
    m.need(v['status']=='FAIL' and v['native_processes']==1 and v['host_compiles']==1 and v['error']=='command failure: battle','prior native result')
    for name,ident in v['proof_bindings'].items():m.need(m.identity(data[name])==ident,'prior proof hash')
    m.need(data['battle.stderr.txt'].endswith(b'P03 archive: natural nonfacility learned battler\n') and not data['battle.stdout.txt'],'prior stop')
    for name in (b.SELF,b.TEST,'scripts/pr16_learnset_battle_retry.py','tests/test_pr16_learnset_battle_retry.py'):
        m.need(m.identity((b.ROOT/name).read_bytes())==v['source_bindings'][name],'inherited source '+name)
    for name,count in (('unit.stderr.txt',6),('compile-prior-unit.stderr.txt',16)):
        raw=data[name];m.need(raw.count(b' ... ok\n')==count and raw.rstrip().endswith(b'OK'),'inherited unit outcome')
    for name in ('verification.json','unit.stderr.txt','compile-prior-unit.stderr.txt','battle.stderr.txt','battle.process.json'):
        (b.PROOF/('field-prior-'+name)).write_bytes(data[name])
    b.write(b.PROOF/'inherited-unit.json',{'run_id':RUN,'source_head':HEAD,'artifact':ARTIFACT,'unit_tests':22,'tests_rerun':0,
        'prior_native_accepted':False,'prior_conclusion':'failure','repair':'require exact IS_MASTER=4 for natural non-link single battle; no effect/PP/identity weakening'})


def command(args,name,timeout=240):
    if name=='unit':
        inherit();m.need(args[1:]==['-B','-m','unittest','tests.test_pr16_learnset_battle','-v'],'old suite invocation')
        args=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_battle_field','-v']
    return ORIGINAL_RUN(args,name,timeout)


def execute():
    m.run=command
    try:b.execute()
    finally:
        p=b.PROOF/'verification.json'
        if p.exists():
            v=m.load(p);v.update(inherited_unit_tests=22,previous_failed_run=RUN,field_repair='exact IS_MASTER=4 and readonly encounter/outcome witness',
                primary_constant_source={'path':'content/modernization/pr16_p08_ring_representative.json',
                    'identity':m.identity((b.ROOT/'content/modernization/pr16_p08_ring_representative.json').read_bytes())})
            b.write(p,v)


if __name__=='__main__':
    install()
    actions={'execute':execute,'record':b.record,'guard':b.guard,'paths':lambda:print('\n'.join(sorted(b.owned()|b.CODE)))}
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
