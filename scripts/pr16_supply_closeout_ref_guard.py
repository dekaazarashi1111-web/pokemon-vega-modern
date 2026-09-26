#!/usr/bin/env python3
"""PR head表示の遅延を実branch refと有界祖先で区別。保存12試験は再実行しない。"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_supply_native_closeout as c
OLD='700011a644e3d5504781ea3cf50a7ca3549f56b8'
REPO='dekaazarashi1111-web/pokemon-vega-modern'
BRANCH='codex/modernization-followup-20260908'
ART={'id':10703799253,'name':'pr16-supply-native-closeout-proof','size_in_bytes':856,
     'digest':'sha256:3c461c7c4bf3499081bd27d82969baaa6047f68ee32a72497fe435634ed5f147'}
EXTRA={'scripts/pr16_supply_closeout_ref_guard.py','tests/test_pr16_supply_closeout_ref_guard.py'}


def check_remote(pr,ref,head,allowed):
    c.need(pr['state']=='open' and pr['draft'] is True and pr['merged'] is False,'PR scope')
    c.need(pr['head']['ref']==BRANCH and pr['head']['repo']['full_name']==REPO
           and pr['base']['ref']=='main' and pr['base']['repo']['full_name']==REPO,'PR repository/branch')
    c.need(ref['ref']=='refs/heads/'+BRANCH and ref['object']['type']=='commit' and ref['object']['sha']==head,'live branch conflict')
    c.need(head in allowed and pr['head']['sha'] in allowed,'PR head outside verified ancestor range')
    return {'live_branch_head':head,'observed_pr_head':pr['head']['sha'],'pr_head_display_lag':pr['head']['sha']!=head,
            'branch_ref_exact':True,'pr_head_in_verified_record_only_ancestry':True}


def inherit():
    from pr16_wiki_reconcile import fetch
    run=fetch('actions/runs/35749269393')
    c.need(run['head_sha']==OLD and run['status']=='completed' and run['conclusion']=='failure','prior closeout identity')
    files=c.bundle(ART,OLD,35749269393,text=True)
    c.need(set(files)=={'record.txt','unit.txt'} and files['unit.txt'].count(b' ... ok\n')==12
           and b'Ran 12 tests' in files['unit.txt'] and files['unit.txt'].rstrip().endswith(b'OK')
           and b'ValueError: PR/remote HEAD' in files['record.txt'],'prior closeout boundary')
    for name in ('scripts/pr16_supply_native_closeout.py','tests/test_pr16_supply_native_closeout.py'):
        c.need((ROOT/name).read_bytes()==subprocess.check_output(['git','show',OLD+':'+name],cwd=ROOT),'inherited test source changed')
    c.WORK.mkdir(parents=True,exist_ok=True)
    (c.WORK/'unit.txt').write_bytes(files['unit.txt'])
    proof={'run_id':35749269393,'source_head':OLD,'artifact':ART,'whole_run_conclusion':'failure',
           'scoped_tests_passed':12,'tests_rerun':0,'record_files_written':False,
           'members':{n:c.identity(raw) for n,raw in files.items()}}
    c.write(c.WORK/'inherited-tests.json',proof)
    return proof


def record():
    import pr16_learnset_payload_verify as payload
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_compact_record import publish_resume
    inherited=inherit();observed={}
    def preflight(head):
        subprocess.run(['git','merge-base','--is-ancestor',c.START,head],cwd=ROOT,check=True)
        changed=set(subprocess.check_output(['git','diff','--name-only',c.START,head],cwd=ROOT,text=True).splitlines())
        c.need(changed==c.CODE,'unexpected changes before record-only closeout')
        allowed=set(subprocess.check_output(['git','rev-list',c.START+'..'+head],cwd=ROOT,text=True).splitlines())|{c.START}
        c.need(1<=len(allowed)<=8,'record-only ancestry bound')
        observed.update(check_remote(fetch('pulls/16'),fetch('git/ref/heads/'+BRANCH),head,allowed))
    payload.current_pr=preflight
    c.record()
    report=c.load(ROOT/c.REPORT)
    report.update(remote_ref_guard=observed,inherited_closeout=inherited,new_closeout_tests=6,
                  inherited_closeout_tests=12,accepted_tests_rerun=0)
    c.write(ROOT/c.REPORT,report)
    state=c.load(ROOT/c.STATE)
    state['observed_head_checks']['record_remote_ref_guard']=observed
    state['do_not_repeat'].append('closeoutの12証拠拒否試験はrun35749269393でPASSを継承し再実行0。このrunは新しい実branch ref/PR同一repo・branch・祖先境界6試験だけ。PR head表示遅延をlive branch ref完全一致とb464a4d以降の記録専用祖先で照合。')
    publish_resume(state)
    old='新closeout12試験・resume check・task graph・限定final index/private差分guardを通過してからcommit。'
    new='保存run35749269393のcloseout12試験を継承（再実行0）、新ref境界6試験・resume check・task graph・限定final index/private差分guardを通過してからcommit。PR表示headとlive branch refは別記し、repo/branch/未merge/有界祖先とlive完全一致を検査。'
    for name in ('design/run_log.md','design/version_log.md'):
        p=ROOT/name;text=p.read_text(encoding='utf-8');c.need(text.count(old)==1,'closeout log segment')
        p.write_text(text.replace(old,new),encoding='utf-8')
    print(json.dumps({'remote_ref_guard':observed,'inherited_tests':12,'new_ref_tests':6,'native_rerun':0}))


if __name__=='__main__':
    c.CODE|=EXTRA
    actions={'record':record,'guard':c.guard,'paths':lambda:print('\n'.join(sorted(c.OWNED)))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_closeout_ref_guard.py record|guard|paths')
    actions[sys.argv[1]]()
