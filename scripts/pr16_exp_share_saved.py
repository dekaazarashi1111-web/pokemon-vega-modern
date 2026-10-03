#!/usr/bin/env python3
"""保存済み・9unit検査済みの共有Cを直接compileする。旧生成器と原本は不変。"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_share_route as r
e=r.e
SELF='scripts/pr16_exp_share_saved.py'
TEST='tests/test_pr16_exp_share_saved.py'
RUN=36079225466
C=e.EVIDENCE+'/'+str(RUN)+'/shared-route.c'


def bound_saved():
    folder=e.ROOT/e.EVIDENCE/str(RUN);v=e.load(folder/'verification.json')
    e.need(v['source_head']=='6942bfc0e1ceac900a4a925d19e12c1892ffc24a' and v['run_id']==RUN and v['new_unit_tests']==9 and v['native_processes']==0,'saved route run identity')
    e.need(v['error']=='exact compile source replacement' and v['status']=='FAIL','retain pre-compile failure')
    for path,binding in v['source_bindings'].items():
        if path!=e.WF:e.need(e.identity((e.ROOT/path).read_bytes())==binding,'saved source changed: '+path)
    files={name:(folder/name).read_bytes() for name in ('unit.stdout.txt','unit.stderr.txt','unit.process.json','shared-route.c')}
    for name,raw in files.items():e.need(e.identity(raw)==v['proof_bindings'][name],'saved proof changed: '+name)
    e.need(e.load(folder/'unit.process.json')=={'returncode':0,'timed_out':False} and files['unit.stderr.txt'].count(b' ... ok\n')==9 and b'\nOK\n' in files['unit.stderr.txt'],'9 passing original units')
    r.reuse_unit() # 42unitの全source/原本もhash照合するが、旧試験は実行しない。
    return files,v


def compile_command(command):
    e.need(command.count(C)==1 and command[0]=='cc' and '-MMD' in command,'exact tracked source compile')
    e.need(str(e.ROOT/r.o.s.C) not in command and r.o.s.C not in command,'accepted evolution source is not recompiled')
    return command


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        files,v=bound_saved()
        for suffix in ('stdout.txt','stderr.txt'):(e.PROOF/('inherited-route-unit.'+suffix)).write_bytes(files['unit.'+suffix])
        e.write(e.PROOF/'inherited-route.json',{'source_run':RUN,'source_head':v['source_head'],'prior_run_conclusion':'failure','original_error':v['error'],'compiler_invocations_in_prior_run':0,'prior_host_compiles_counter_was_attempted':1,'prior_native_processes':0,'inherited_unit_tests':51,'accepted_unit_reruns':0,'accepted_native_reruns':0,'source':C,'source_identity':e.identity(files['shared-route.c']),'scope':'DIRECT_COMPILATION_OF_SAVED_SHARED_RUNNER'})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_share_saved','-v']
    elif name=='compile':command=compile_command(command)
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,C,r.SELF,r.TEST,r.o.SELF,r.o.TEST,r.o.s.SELF,r.o.s.TEST,r.o.s.C))
    e.SELF,e.TEST,e.C=SELF,TEST,C
    e.configure();e.x.m.run=scoped_run;e.x.validate=r.validate


if __name__=='__main__':
    configure()
    actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
