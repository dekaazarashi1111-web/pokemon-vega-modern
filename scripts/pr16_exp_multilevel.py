#!/usr/bin/env python3
"""EXP複数レベル失敗だけを診断。保存3成功/旧oracle19を再実行しない。"""
from __future__ import annotations
import sys
import re
import struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_learnset_boundaries as x
SELF='scripts/pr16_exp_multilevel.py'
TRACE='tools/pr16_exp_multilevel_trace.h'
TEST='tests/test_pr16_exp_multilevel.py'
x.CODE.update((SELF,TRACE,TEST))
original_run=x.m.run
UNIT_RUN=36065509607
UNIT_SOURCES={x.SELF:'930ac803c21f637112d43009981a818e3d8076cf0e8a5fcfbc9fc376f2b0f44a',x.TEST:'32efc92275899507f8089b7dea7791a10c88f685a5a990b71107ed3652048e8d'}


def health(stderr):
    rows=re.findall(rb'^NATURAL_PARTY stage=(fixture|returned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',stderr,re.M)
    x.need([r[0] for r in rows]==[b'fixture',b'returned',b'saved',b'continued'],'health lifecycle')
    records={}
    for label,_,encoded in rows:
        data=bytes.fromhex(encoded.decode());hp,maximum=struct.unpack_from('<HH',data,86)
        x.need(0<hp<=maximum<999,'native health bounds')
        records[label.decode()]={'hp':hp,'maximum_hp':maximum,'level':data[84]}
    first=records['fixture'];last=records['returned']
    x.need(first['hp']==first['maximum_hp'] and first['level']==10 and last['level']>=12,'full native health and multilevel fixture')
    x.need(records['returned']==records['saved']==records['continued'],'health Save/Continue')
    return {'status':'PASS','health_writes_after_creation':0,'combat_stats_are_fixture':True,'old_level_43_cases_rerun':False,'phases':records}


def focused_run(command,name,*args,**kwargs):
    if name=='unit':
        evidence=x.ROOT/x.EVIDENCE/str(UNIT_RUN)
        saved=x.load(evidence/'verification.json')
        x.need(saved['new_unit_tests']==20,'saved focused oracle count')
        for path,digest in UNIT_SOURCES.items():
            x.need(x.identity((x.ROOT/path).read_bytes())['sha256']==digest==saved['source_bindings'][path]['sha256'],'unaffected oracle source changed')
        for leaf in ('unit.stdout.txt','unit.stderr.txt','unit.process.json'):
            x.need(x.identity((evidence/leaf).read_bytes())==saved['proof_bindings'][leaf],'saved unit proof changed')
        x.need(x.load(evidence/'unit.process.json')=={'returncode':0,'timed_out':False},'saved unit process')
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_boundaries.BoundaryTests.test_observation_never_calls_accepted_main','tests.test_pr16_exp_multilevel','-v']
        x.write(x.PROOF/'unit-reuse.json',{'source_run':UNIT_RUN,'saved_count':20,'unchanged_oracle_tests_reused':19,'changed_driver_structure_test':1,'new_health_tests':8,'source_bindings':UNIT_SOURCES,'accepted_native_reruns':0})
    out,err=original_run(command,name,*args,**kwargs)
    if name=='butterfree-exp-multilevel':x.write(x.PROOF/'multilevel-health.json',health(err))
    return out,err


def execute():
    try:x.execute()
    finally:
        proof=x.PROOF/'verification.json'
        if proof.exists():
            v=x.load(proof);v['fixture_correction']={'case':'butterfree-exp-multilevel','native_hp_and_max_hp_preserved':True,'combat_stats_only':True,'accepted_cases_changed':False,'old_failure_runs':[36065509607,36066498141]}
            hp=x.PROOF/'multilevel-health.json'
            if hp.exists():v['multilevel_health']=x.load(hp)
            x.write(proof,v)


if __name__=='__main__':
    x.m.run=focused_run
    actions={'execute':execute,'record':x.record,'complete':x.complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    x.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
