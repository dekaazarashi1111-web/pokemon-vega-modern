#!/usr/bin/env python3
"""自然野生EXP共有だけを観測。2体での町/イベント横断を受入範囲にしない。"""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_share_input as i
e=i.e
SELF='scripts/pr16_exp_share_grass.py'
TEST='tests/test_pr16_exp_share_grass.py'
C='tools/mgba_pr16_exp_share_grass.c'
RUN=36079930352
OLD='    fprintf(stderr,"ESHARE_FIXTURE_ROUTE frame=%u count=1 group=96 map=17 x=11 y=39\\n",lb_frames);'
NEW='''    /* 草むら最後の手前まで1体で通常移動。2体でのevent横断は今回のscope外。 */
    unsigned approach=sizeof(lb_grass_path)/sizeof(*lb_grass_path);
    a_require(approach>1,"bounded grass approach");
    lb_path(c,17,lb_grass_path,approach-1,false);
    lb_position(c,96,17,13,30);
    fprintf(stderr,"ESHARE_GRASS_FIXTURE_ROUTE frame=%u count=1 group=96 map=17 x=13 y=30\\n",lb_frames);'''


def derived_source():
    source=(e.ROOT/i.s.C).read_text()
    changes=[(OLD,NEW),('e_party(c,"fixture",before);lb_position(c,96,17,11,39);','e_party(c,"fixture",before);lb_position(c,96,17,13,30);'),('    lb_path(c,17,lb_grass_path,sizeof(lb_grass_path)/sizeof(*lb_grass_path),true);','    lb_path(c,17,lb_grass_path+approach-1,1,true);')]
    for old,new in changes:
        e.need(source.count(old)==1,'exact grass fixture anchor '+old[:70]);source=source.replace(old,new)
    return source


def original_units():
    i.original_units();folder=e.ROOT/e.EVIDENCE/str(RUN);v=e.load(folder/'verification.json')
    e.need(v['source_head']=='d951b8cc7600c5412b9db7c30172e57cf0cb454e' and v['new_unit_tests']==6 and v['native_processes']==1,'field input prior run identity')
    for path,binding in v['source_bindings'].items():
        if path!=e.WF:e.need(e.identity((e.ROOT/path).read_bytes())==binding,'previous source changed '+path)
    for name in ('unit.process.json','unit.stdout.txt','unit.stderr.txt','compile.process.json','compile.stderr.txt'):
        e.need(e.identity((folder/name).read_bytes())==v['proof_bindings'][name],'previous original changed '+name)
    e.need(e.load(folder/'unit.process.json')==e.load(folder/'compile.process.json')=={'returncode':0,'timed_out':False},'previous successful units and compile')
    e.need((folder/'unit.stderr.txt').read_bytes().count(b' ... ok\n')==6 and not (folder/'compile.stderr.txt').read_bytes(),'6 original unit successes')
    return v


def validate(out,err,case,rows,pp):
    e.need(case['mode']==2,'shared-only grass fixture')
    result=i.s.r.o.validate(out,err,case,rows,pp)
    route=re.findall(rb'^ESHARE_GRASS_FIXTURE_ROUTE frame=(\d+) count=1 group=96 map=17 x=13 y=30$',err,re.M)
    ready=re.findall(rb'^ESHARE_FIELD_READY frame=(\d+) stable=120$',err,re.M)
    e.need(len(route)==err.count(b'ESHARE_GRASS_FIXTURE_ROUTE ')==1,'one exact last dry tile witness')
    e.need(b'ESHARE_FIXTURE_ROUTE ' not in err and b'ESHARE_FIELD_KEY ' not in err,'no earlier route or event-input scope contamination')
    e.need(0<int(route[0])<int(ready[0])<result['boundary'],'shared creation after dry approach before encounter boundary')
    e.need(err.index(b'ESHARE_GRASS_FIXTURE_ROUTE ')<err.index(b'ESHARE_FIELD_READY ')<err.index(b'ESHARE_PARTY stage=fixture '),'original preparation order')
    result['pre_observation_route']={'frame':int(route[0]),'party_count':1,'map':[96,17],'position':[13,30],'two_party_overworld_events_accepted':False}
    return result


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        original_units();e.need((e.ROOT/C).read_text()==derived_source(),'exact grass fixture tracked source')
        e.write(e.PROOF/'grass-fixture-impact.json',{'inherited_unit_tests':61,'inherited_unit_reruns':0,'accepted_native_reruns':0,'prior_run':RUN,'prior_run_conclusion':'failure','prior_stop':'ordinary action entry; not promoted to wild acceptance','template':i.s.C,'template_identity':e.identity((e.ROOT/i.s.C).read_bytes()),'derived':C,'derived_identity':e.identity((e.ROOT/C).read_bytes()),'shared_fixture_position':[96,17,13,30],'two_party_overworld_events_accepted':False,'event_input_scheduler_used':False,'rom_changes':0})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_share_grass','-v']
    return e.BASE_RUN(command,name,*args,**kwargs)


def configure():
    e.CODE.update((SELF,TEST,C,i.SELF,i.TEST,i.C,i.s.SELF,i.s.TEST,i.s.C,i.s.r.SELF,i.s.r.TEST,i.s.r.o.SELF,i.s.r.o.TEST,i.s.r.o.s.SELF,i.s.r.o.s.TEST,i.s.r.o.s.C))
    e.SELF,e.TEST,e.C=SELF,TEST,C;e.configure();e.x.m.run=scoped_run;e.x.validate=validate


if __name__=='__main__':
    configure();actions={'execute':e.execute,'record':e.x.record,'complete':e.complete,'guard':e.x.guard,'paths':lambda:print('\n'.join(sorted(e.x.owned())))}
    e.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
