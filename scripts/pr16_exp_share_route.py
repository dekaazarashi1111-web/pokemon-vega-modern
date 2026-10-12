#!/usr/bin/env python3
"""保存済み進化2caseは再実行せず、共有fixtureを自然遭遇の手前へ分離する。"""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_evolution_observation as o
e=o.e
SELF='scripts/pr16_exp_share_route.py'
TEST='tests/test_pr16_exp_share_route.py'
INHERITED_RUN=36078747595
TOWN='lb_path(c,5,lb_town_path,sizeof(lb_town_path)/sizeof(*lb_town_path),false);lb_step(c,QOL_KEY_UP);lb_position(c,96,17,11,39);'


def derived_source(source):
    """固定templateから共有専用runnerを派生。ROM/受入済みrunnerを改変しない。"""
    replacements=[
        ('    e_count=v->mode==2?2:1;e_sid=v->mode==2?414:413;',
         '    a_require(v->mode==2,"shared-only runner rejects accepted evolution cases");\n    e_count=2;e_sid=414;'),
        ('write8(c,QOL_PLAYER_PARTY_COUNT,e_count);','write8(c,QOL_PLAYER_PARTY_COUNT,1);'),
        ('    e_slots(c,0,e_sid,v->level,v->moves,v->points);\n    if(e_count==2){',
         '    e_slots(c,0,e_sid,v->level,v->moves,v->points);\n'
         '    /* 町の歩行はfixture準備。共有観測境界より前、1体のまま通常入力で移動。 */\n'
         '    '+TOWN+'\n'
         '    fprintf(stderr,"ESHARE_FIXTURE_ROUTE frame=%u count=1 group=96 map=17 x=11 y=39\\n",lb_frames);\n'
         '    if(e_count==2){'),
        ('        (void)call_preserving(c,QOL_FLAG_SET,QOL_FLAG_EXP_SHARE,0,0,0);',
         '        write8(c,QOL_PLAYER_PARTY_COUNT,e_count);\n'
         '        (void)call_preserving(c,QOL_FLAG_SET,QOL_FLAG_EXP_SHARE,0,0,0);'),
        ('e_party(c,"fixture",before);lb_position(c,96,5,20,20);',
         'e_party(c,"fixture",before);lb_position(c,96,17,11,39);'),
        ('    '+TOWN+'unsigned boundary=lb_frames;',
         '    lb_frame(c,0);unsigned boundary=lb_frames; /* 共有fixtureの後、guard下で観測開始。 */'),
    ]
    for old,new in replacements:
        e.need(source.count(old)==1,'shared route template anchor mismatch: '+old[:70])
        source=source.replace(old,new)
    return source


def validate(out,err,case,rows,pp):
    e.need(case['mode']==2,'saved evolution cases must not use this runner')
    result=o.validate(out,err,case,rows,pp)
    route=re.findall(rb'^ESHARE_FIXTURE_ROUTE frame=(\d+) count=1 group=96 map=17 x=11 y=39$',err,re.M)
    ready=re.findall(rb'^ESHARE_FIELD_READY frame=(\d+) stable=120$',err,re.M)
    e.need(len(route)==1 and err.count(b'ESHARE_FIXTURE_ROUTE ')==1,'one exact pre-observation route witness')
    e.need(0<int(route[0])<int(ready[0])<result['boundary'],'fixture preparation precedes guarded encounter')
    e.need(err.index(b'ESHARE_FIXTURE_ROUTE ')<err.index(b'ESHARE_FIELD_READY ')<err.index(b'ESHARE_PARTY stage=fixture '),'fixture phase raw order')
    result['pre_observation_route']={'frame':int(route[0]),'party_count':1,'map':[96,17],'position':[11,39],'town_shared_flag_path_accepted':False}
    return result


def reuse_unit():
    folder=e.ROOT/e.EVIDENCE/str(INHERITED_RUN);v=e.load(folder/'verification.json')
    e.need(v['run_id']==INHERITED_RUN and v['new_unit_tests']==42 and len(v['accepted'])==2 and v['native_processes']==3,'prior partial run identity')
    e.need(set(v['accepted'])=={'metapod-exp-evolve','metapod-exp-cancel'},'prior accepted case set')
    for path,binding in v['source_bindings'].items():
        if path!=e.WF:e.need(e.identity((e.ROOT/path).read_bytes())==binding,'inherited unit source changed: '+path)
    files={}
    for name in ('unit.process.json','unit.stderr.txt','unit.stdout.txt'):
        files[name]=(folder/name).read_bytes();e.need(e.identity(files[name])==v['proof_bindings'][name],'inherited unit proof changed: '+name)
    e.need(e.load(folder/'unit.process.json')=={'returncode':0,'timed_out':False} and files['unit.stderr.txt'].count(b' ... ok\n')==42 and b'\nOK\n' in files['unit.stderr.txt'],'42 successful unit originals')
    return files,v


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        files,prior=reuse_unit()
        for suffix in ('stderr.txt','stdout.txt'):(e.PROOF/('inherited-unit.'+suffix)).write_bytes(files['unit.'+suffix])
        e.write(e.PROOF/'inherited-unit.json',{'source_run':INHERITED_RUN,'original_run_conclusion':'failure','inherited_unit_tests':42,'inherited_unit_tests_rerun':0,'accepted_native_reruns':0,'proof_bindings':{n:e.identity(raw) for n,raw in files.items()},'inherited_sources_unchanged':True,'new_scope':'SHARED_FIXTURE_ROUTE_AND_REUSE_ONLY'})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_share_route','-v']
    if name=='compile':
        base=(e.ROOT/o.s.C).read_text();derived=derived_source(base)
        target=e.WORK/'shared-route.c';target.write_text(derived)
        (e.PROOF/'shared-route.c').write_text(derived)
        original=str(e.ROOT/o.s.C);e.need(command.count(original)==1,'exact compile source replacement')
        command=[str(target) if token==original else token for token in command]
        e.write(e.PROOF/'shared-route-source.json',{'template':o.s.C,'template_identity':e.identity(base.encode()),'derived_identity':e.identity(derived.encode()),'generator':SELF,'generator_identity':e.identity((e.ROOT/SELF).read_bytes()),'old_accepted_template_unchanged':True,'host_writes_after_guard_added':0,'town_shared_flag_path_accepted':False,'rom_changes':0})
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,o.SELF,o.TEST,o.s.SELF,o.s.TEST,o.s.C))
    e.SELF,e.TEST,e.C=SELF,TEST,o.s.C
    e.configure();e.x.m.run=scoped_run;e.x.validate=validate


if __name__=='__main__':
    configure()
    actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths')
    actions[sys.argv[1]]()
