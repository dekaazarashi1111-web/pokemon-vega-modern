#!/usr/bin/env python3
"""EXP複数レベル失敗だけを診断。保存3成功/旧oracle19を再実行しない。"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_learnset_boundaries as x
SELF='scripts/pr16_exp_multilevel.py'
TRACE='tools/pr16_exp_multilevel_trace.h'
x.CODE.update((SELF,TRACE))
original_run=x.m.run
UNIT_RUN=36065509607
UNIT_SOURCES={x.SELF:'930ac803c21f637112d43009981a818e3d8076cf0e8a5fcfbc9fc376f2b0f44a',x.TEST:'32efc92275899507f8089b7dea7791a10c88f685a5a990b71107ed3652048e8d'}


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
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_boundaries.BoundaryTests.test_observation_never_calls_accepted_main','-v']
        x.write(x.PROOF/'unit-reuse.json',{'source_run':UNIT_RUN,'saved_count':20,'unchanged_oracle_tests_reused':19,'changed_driver_structure_test':1,'source_bindings':UNIT_SOURCES,'accepted_native_reruns':0})
    return original_run(command,name,*args,**kwargs)


if __name__=='__main__':
    x.m.run=focused_run
    actions={'execute':x.execute,'record':x.record,'complete':x.complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    x.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
