#!/usr/bin/env python3
"""共有専用runnerの遭遇前イベント待ちに通常A入力を追加。状態/結果注入なし。"""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_share_saved as s
e=s.e
SELF='scripts/pr16_exp_share_input.py'
TEST='tests/test_pr16_exp_share_input.py'
C='tools/mgba_pr16_exp_share_input.c'
RUN=36079548406
ANCHOR='static void e_frame(struct mCore *c){\n    e_original_frame(c);x_trace(c);'
PATCH='''static unsigned e_field_keys;
static bool e_field_encounter;
static void e_field_input(struct mCore *c){
    if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER))e_field_encounter=true;
    if(!e_field_encounter && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD
       && read8(c,P02S_FIELD_LOCK)==1 && lb_frames%30==0){
        a_require(e_field_keys<120,"bounded ordinary field event input");
        ++e_field_keys;c->setKeys(c,QOL_KEY_A);
        fprintf(stderr,"ESHARE_FIELD_KEY frame=%u key=1 callback=08055e75 lock=1\\n",lb_frames);
    }
}
static void e_frame(struct mCore *c){
    e_field_input(c);
    e_original_frame(c);x_trace(c);'''


def derived_source():
    raw=(e.ROOT/s.C).read_text();e.need(raw.count(ANCHOR)==1,'exact saved C input anchor')
    return raw.replace(ANCHOR,PATCH)


def original_units():
    s.bound_saved()
    folder=e.ROOT/e.EVIDENCE/str(RUN);v=e.load(folder/'verification.json')
    e.need(v['source_head']=='023604d280177ad971bac96649b2b15f7c8e42e7' and v['new_unit_tests']==4 and v['native_processes']==1,'saved direct compile scope')
    for path,binding in v['source_bindings'].items():
        if path!=e.WF:e.need(e.identity((e.ROOT/path).read_bytes())==binding,'inherited source changed: '+path)
    for name in ('unit.process.json','unit.stderr.txt','unit.stdout.txt','compile.process.json','compile.stderr.txt'):
        raw=(folder/name).read_bytes();e.need(e.identity(raw)==v['proof_bindings'][name],'inherited original changed: '+name)
    e.need(e.load(folder/'unit.process.json')==e.load(folder/'compile.process.json')=={'returncode':0,'timed_out':False},'original unit/compiler processes')
    e.need((folder/'unit.stderr.txt').read_bytes().count(b' ... ok\n')==4 and not (folder/'compile.stderr.txt').read_bytes(),'original successful unit/compile evidence')
    return v


def validate(out,err,case,rows,pp):
    result=s.r.validate(out,err,case,rows,pp)
    keys=re.findall(rb'^ESHARE_FIELD_KEY frame=(\d+) key=1 callback=08055e75 lock=1$',err,re.M)
    e.need(0<len(keys)<=120 and len(keys)==err.count(b'ESHARE_FIELD_KEY '),'bounded exact ordinary field inputs')
    frames=[int(x) for x in keys]
    e.need(frames==sorted(set(frames)) and all(f%30==0 for f in frames),'field input frame cadence')
    e.need(result['boundary']<=frames[0]<=frames[-1]<result['encounter'],'field inputs only before native encounter')
    result['ordinary_field_event_pulses']=len(keys)
    return result


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        original_units();e.need((e.ROOT/C).read_text()==derived_source(),'exact derived tracked C')
        e.write(e.PROOF/'field-input-impact.json',{'inherited_unit_tests':55,'inherited_unit_reruns':0,'accepted_native_reruns':0,'prior_run':RUN,'prior_run_conclusion':'failure','template':s.C,'template_identity':e.identity((e.ROOT/s.C).read_bytes()),'derived_source':C,'derived_identity':e.identity((e.ROOT/C).read_bytes()),'change':'PRE_ENCOUNTER_LOCKED_FIELD_ORDINARY_A_KEYS_ONLY','maximum_input_pulses':120,'state_injection':False,'rom_changes':0})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_share_input','-v']
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,C,s.SELF,s.TEST,s.C,s.r.SELF,s.r.TEST,s.r.o.SELF,s.r.o.TEST,s.r.o.s.SELF,s.r.o.s.TEST,s.r.o.s.C))
    e.SELF,e.TEST,e.C=SELF,TEST,C
    e.configure();e.x.m.run=scoped_run;e.x.validate=validate


if __name__=='__main__':
    configure()
    actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
