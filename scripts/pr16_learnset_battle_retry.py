#!/usr/bin/env python3
"""compile前停止の16試験を継承し、不足LEFT定数だけを補って未実行戦闘へ。"""
from __future__ import annotations
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pr16_learnset_battle as b
m=b.m
RUN=35832603358
HEAD='ea7cf90458ee011719c7aafd137c740a97320c05'
ARTIFACT={'id':10737707124,'name':'pr16-learnset-battle-proof','size_in_bytes':7410,
          'digest':'sha256:c7fc0a367ef44755c23a48022cf83ce166caea4b7bd0e13d4a16cb8af283c260'}
EXTRA={'scripts/pr16_learnset_battle_retry.py','tests/test_pr16_learnset_battle_retry.py'}
ORIGINAL_RUN=m.run


def once(text,old,new):
    m.need(text.count(old)==1,'exact compiler repair anchor');return text.replace(old,new)


def repair_c(text):
    return once(text,'#include "pr16_learnset_battle_fixture.h"',
        '#include "pr16_learnset_battle_fixture.h"\n/* GBA keypad left, matching the existing field drivers. */\n#define QOL_KEY_LEFT 0x0020U')


def repair_runner(text):
    return once(text,"m.need(not (ROOT/CP).exists(),'battle checkpoint already exists: inspect before retry')",
        "m.need(not (ROOT/CP).exists() or m.load(ROOT/CP)['status']=='FAIL','accepted battle rerun refused')")


def install():
    for name,transform in ((b.C,repair_c),(b.SELF,repair_runner)):
        p=b.ROOT/name;old=subprocess.check_output(['git','show',HEAD+':'+name],cwd=b.ROOT).decode();new=transform(old)
        m.need(p.read_text() in (old,new),'unexpected battle source during compiler-only repair')
        if p.read_text()==old:p.write_text(new)
    importlib.reload(b);b.CODE|=EXTRA


def inherit():
    prior=m.load(b.ROOT/b.CP)
    m.need(prior['source_head']==HEAD and prior['run_id']==RUN and prior['status']=='FAIL'
           and prior['native_processes']==0 and prior['new_unit_tests']==16,'prior compile-only checkpoint')
    run=b.fetch('actions/runs/'+str(RUN));meta=b.fetch('actions/artifacts/'+str(ARTIFACT['id']))
    m.need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure','prior failed run')
    m.need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired'] and meta['workflow_run']['head_sha']==HEAD,'prior artifact')
    raw=b.fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
    m.need(m.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'prior archive hash')
    data=b.zip_members(raw);v=json.loads(data['verification.json'])
    m.need(v['status']=='FAIL' and v['native_processes']==0 and v['new_unit_tests']==16 and v['error']=='command failure: compile','prior result')
    for name,ident in v['proof_bindings'].items():m.need(m.identity(data[name])==ident,'prior proof hash')
    unit=data['unit.stderr.txt'];err=data['compile.stderr.txt']
    m.need(unit.count(b' ... ok\n')==16 and b'Ran 16 tests' in unit and unit.rstrip().endswith(b'OK'),'inherited16tests')
    m.need(err.count(b'error:')==3 and err.count('‘QOL_KEY_LEFT’ undeclared'.encode())==3,'compiler failure cause')
    for name in (b.TEST,):m.need(m.identity((b.ROOT/name).read_bytes())==v['source_bindings'][name],'inherited contract source')
    for name in ('verification.json','unit.stderr.txt','unit.stdout.txt','compile.stderr.txt','compile.process.json'):
        (b.PROOF/('compile-prior-'+name)).write_bytes(data[name])
    b.write(b.PROOF/'inherited-unit.json',{'run_id':RUN,'source_head':HEAD,'artifact':ARTIFACT,'unit_tests':16,
        'tests_rerun':0,'native_processes':0,'prior_conclusion':'failure','repair':'define missing GBA LEFT=0x20 only; no ROM/battle behavior edits'})


def command(args,name,timeout=240):
    if name=='unit':
        inherit();m.need(args[1:]==['-B','-m','unittest','tests.test_pr16_learnset_battle','-v'],'inherited suite request')
        args=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_battle_retry','-v']
    return ORIGINAL_RUN(args,name,timeout)


def execute():
    m.run=command
    try:b.execute()
    finally:
        p=b.PROOF/'verification.json'
        if p.exists():
            v=m.load(p);v.update(inherited_unit_tests=16,previous_failed_run=RUN,compiler_repair='missing host LEFT constant 0x20; native previously not started')
            b.write(p,v)


if __name__=='__main__':
    install()
    actions={'execute':execute,'record':b.record,'guard':b.guard,'paths':lambda:print('\n'.join(sorted(b.owned()|b.CODE)))}
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
