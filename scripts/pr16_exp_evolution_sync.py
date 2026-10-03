#!/usr/bin/env python3
"""新3caseの読取/入力同期修復。初回24unitは原本を照合し再実行しない。"""
from __future__ import annotations
import json
from pathlib import Path
import re
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_evolution_share as e
SELF='scripts/pr16_exp_evolution_sync.py'
TEST='tests/test_pr16_exp_evolution_sync.py'
C='tools/mgba_pr16_exp_evolution_sync.c'
PRIOR=36075652959
BASE_SELF=e.SELF;BASE_TEST=e.TEST;BASE_C=e.C


def decode(raw):
    e.need(len(raw)==100,'whole mon')
    return {'species':struct.unpack_from('<H',raw,32)[0],'held':struct.unpack_from('<H',raw,34)[0],
            'xp':struct.unpack_from('<I',raw,36)[0],'bonus':raw[40],'moves':list(struct.unpack_from('<4H',raw,44)),
            'pp':list(raw[52:56]),'level':raw[84],'hp':struct.unpack_from('<H',raw,86)[0],'maxhp':struct.unpack_from('<H',raw,88)[0]}


def reuse(v,reader,source):
    e.need(v['run_id']==PRIOR and v['source_head']=='6b69b8d48644d255962d218dcce81ff01c4904a7' and v['new_unit_tests']==24 and not v['accepted'],'first failure identity')
    for leaf in ('unit.stdout.txt','unit.stderr.txt','unit.process.json'):
        e.need(e.identity(reader(leaf))==v['proof_bindings'][leaf],'unit proof '+leaf)
    e.need(json.loads(reader('unit.process.json'))=={'returncode':0,'timed_out':False} and reader('unit.stderr.txt').count(b' ... ok\n')==24 and b'\nOK\n' in reader('unit.stderr.txt'),'24 successful unit originals')
    for path in (BASE_SELF,BASE_TEST,BASE_C,e.x.SELF,e.x.n.p.__file__.replace(str(e.ROOT)+'/', '')):
        e.need(e.identity(source(path))==v['source_bindings'][path],'unchanged base source '+path)
    observations=0
    for name,_,_,_,_,_ in e.CASES:
        leaf=name+'.stderr.txt';err=reader(leaf);e.need(e.identity(err)==v['proof_bindings'][leaf],'native failure original')
        party=re.findall(rb'^ESHARE_PARTY stage=fixture count=(\d+) counter=2 hex=([0-9a-f]+)$',err,re.M)
        rows=re.findall(rb'^ESHARE_MON stage=fixture index=(\d+) species=(\d+) level=(\d+) xp=(\d+) hp=(\d+) maxhp=(\d+) held=(\d+) bonus=(\d+) moves=(\d+,\d+,\d+,\d+) pp=(\d+,\d+,\d+,\d+)$',err,re.M)
        e.need(len(party)==1 and len(rows)==int(party[0][0]),'native fixture getter coverage')
        raw=bytes.fromhex(party[0][1].decode());e.need(len(raw)==100*len(rows),'native fixture whole party')
        for i,row in enumerate(rows):
            e.need(int(row[0])==i,'native getter order')
            expected=dict(zip(('species','level','xp','hp','maxhp','held','bonus'),map(int,row[1:8])))
            expected.update(moves=list(map(int,row[8].split(b','))),pp=list(map(int,row[9].split(b','))))
            e.need(decode(raw[100*i:100*(i+1)])==expected,'read-only layout/native GetMonData mismatch');observations+=1
    e.need(observations==4,'native layout samples')
    return {'unchanged_unit_tests_reused':24,'native_layout_samples':observations,'source_run':PRIOR,'accepted_native_reruns':0,
            'prior_native_failures_preserved':3,'new_native_scope':'only previous failed evolution/share three cases',
            'repair':'read-only raw mon observations; neutral stable action readiness and bounded ordinary Fight key retry; read-only walking trace'}


def validate(out,err,case,rows,pp):
    result=e.validate(out,err,case,rows,pp);data,observed=e.party_evidence(err,result['party_count'])
    for stage,raw in zip(e.STAGES,data):
        for i in range(result['party_count']):e.need(decode(raw[100*i:100*(i+1)])==observed[stage,i],'all raw mon fields/observations agree')
    pulses=re.findall(rb'^ESHARE_FIGHT frame=(\d+) pulses=(\d+)$',err,re.M)
    e.need(len(pulses)==err.count(b'ESHARE_FIGHT ')==result['turns'],'Fight turn evidence')
    frames=[int(f) for f,_ in pulses]
    e.need(frames==sorted(set(frames)) and all(result['encounter']<f<result['returned'] for f in frames),'Fight chronology')
    e.need(all(1<=int(n)<=30 for _,n in pulses),'bounded physical Fight keys')
    result['read_only_party_layout_verified']=True;return result


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        folder=e.ROOT/e.EVIDENCE/str(PRIOR);v=e.load(folder/'verification.json')
        report=reuse(v,lambda leaf:(folder/leaf).read_bytes(),lambda path:(e.ROOT/path).read_bytes())
        e.write(e.PROOF/'unit-and-layout-reuse.json',report)
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_evolution_sync','-v']
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,C));e.SELF,e.TEST,e.C=SELF,TEST,C
    e.configure();e.x.m.run=scoped_run;e.x.validate=validate


if __name__=='__main__':
    configure();actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
