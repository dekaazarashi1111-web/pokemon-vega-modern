#!/usr/bin/env python3
"""未成功の自然初期技だけ命令観測。25境界試験は保存原本から継承する。"""
from pathlib import Path
import json
import os
import re
import subprocess
import pr16_learnset_natural as n
m=n.m
TRACE=r'''
static unsigned nt_steps,nt_calls;
static bool lb_action(struct mCore *c);
static void nt_frame(struct mCore *c) {
    unsigned sb=read32(c,QOL_SAVE_BLOCK1_SLOT);
    if(!p02s_ewram_pointer(sb) || read8(c,sb+4)!=96 || read8(c,sb+5)!=17 || lb_action(c)){c->runFrame(c);return;}
    unsigned frame=c->frameCounter(c),steps=0;
    while(c->frameCounter(c)==frame) {
        unsigned pc=(unsigned)read_register(c,"pc");
        unsigned entries[]={0x0803D1C0,0x0803E14C,0x091145F0,read32(c,0x0803E150)&~1U,0x0803E01C,0x0803FBC4,ROM_SET_MON_DATA&~1U};
        for(unsigned i=0;i<sizeof(entries)/sizeof(*entries);++i)if(pc==entries[i]+4 || pc==entries[i]+2) {
            unsigned r0=(unsigned)read_register(c,"r0"),r1=(unsigned)read_register(c,"r1"),r2=(unsigned)read_register(c,"r2"),lr=(unsigned)read_register(c,"lr");
            if(i<5 || (r0>=ADDR_ENEMY_PARTY && r0<ADDR_ENEMY_PARTY+600 && r1>=11 && r1<=25)) {
                unsigned value=p02s_ewram_pointer(r2)?read32(c,r2):0;
                fprintf(stderr,"NATURAL_TRACE frame=%u pc=%08x entry=%08x lr=%08x r0=%08x r1=%08x r2=%08x value=%08x\n",lb_frames,pc,entries[i],lr,r0,r1,r2,value);++nt_calls;
            }
        }
        c->step(c);a_require(++steps<=2000000 && ++nt_steps<=120000000,"bounded passive initial trace");
    }
}
'''

def execute():
    base=n.ROOT/n.EVIDENCE/'36039653256'
    prior=n.load(base/'verification.json')
    n.need(prior['run_id']==36039653256 and prior['status']=='FAIL' and prior['new_unit_tests']==25 and prior['native_processes']==1,'saved first failure')
    for path in (n.SELF,n.TEST,n.C):n.need(n.identity((n.ROOT/path).read_bytes())==prior['source_bindings'][path],'unchanged failed source')
    old_run=m.run
    def run(args,name,timeout=240):
        if name=='unit':
            out=(base/'unit.stdout.txt').read_bytes();err=(base/'unit.stderr.txt').read_bytes()
            n.need(n.identity(out)==prior['proof_bindings']['unit.stdout.txt'] and n.identity(err)==prior['proof_bindings']['unit.stderr.txt'] and b'Ran 25 tests' in err and b'\nOK\n' in err,'inherited 25 unit result')
            n.write(n.PROOF/'inherited-unit.json',{'source_run':prior['run_id'],'source_head':prior['source_head'],'new_unit_tests':0,'inherited_unit_tests':25,'tests':n.identity((n.ROOT/n.TEST).read_bytes()),'stdout':n.identity(out),'stderr':n.identity(err)})
            return out,err
        if name=='compile':
            walking=n.WORK/'pr16_natural_walking.h';text=walking.read_text()
            anchor='static void lb_frame(struct mCore *c,unsigned key) {'
            n.need(text.count(anchor)==1 and text.count('c->setKeys(c,key);c->runFrame(c);++lb_frames;')==1,'exact passive trace transform')
            text=text.replace(anchor,TRACE+'\n'+anchor).replace('c->setKeys(c,key);c->runFrame(c);++lb_frames;','c->setKeys(c,key);nt_frame(c);++lb_frames;')
            (n.PROOF/'pr16_natural_trace_walking.h').write_text(text)
            derivative=(n.ROOT/n.C).read_text().replace('#include "pr16_natural_walking.h"','#include "pr16_natural_trace_walking.h"')
            compiled=n.PROOF/'diagnostic-runner.c';compiled.write_text(derivative)
            args=[str(compiled) if x==n.C else x for x in args];args.insert(1,'-I'+str(n.PROOF))
            raw=(n.WORK/'candidate.gba').read_bytes();ranges=[]
            meta=n.load(n.ROOT/'content/modernization/pr16_candidate_wiki_saved_link_sources.json')
            for key,row in meta['symbols'].items():
                if key not in ('GiveBoxMonInitialMoveset','GiveMoveToBoxMon','CreateBoxMon','CreateMon','CreateWildMon','SetMonData','SetBoxMonData'):continue
                if 'address' not in row or 'size' not in row:
                    ranges.append({'name':key,'saved':row,'code_range_available':False});continue
                at=row['address']-0x08000000;size=row['size']
                if 0<=at<at+size<=len(raw) and 0<size<=8192:ranges.append({'name':key,'saved':row,'current_bytes':raw[at:at+size].hex(),'current_identity':n.identity(raw[at:at+size])})
            for at,size in [(0x3D1C0,1024),(0x3E14C,32),(0x1114000,2048),(0x15F9800,1024)]:
                ranges.append({'address':0x08000000+at,'size':size,'bytes':raw[at:at+size].hex()})
            n.write(n.PROOF/'candidate-code-ranges.json',ranges)
            return old_run(args,name,timeout)
        return old_run(args,name,timeout)
    m.run=run
    try:n.execute()
    except Exception:pass
    finally:m.run=old_run
    v=n.load(n.PROOF/'verification.json')
    v.update(new_unit_tests=0,inherited_unit_tests=25,diagnostic_only=True,diagnostic_source=n.identity(Path(__file__).read_bytes()))
    if (n.PROOF/'pr16_natural_trace_walking.h').exists():
        v['actual_compiled_walking']=n.identity((n.PROOF/'pr16_natural_trace_walking.h').read_bytes())
    v['historical_count_correction']={'run_id':36040259713,'new_unit_tests':0,'inherited_unit_tests':25,'native_processes':0,'reason':'KeyError before compile; inherited-unit.json is authoritative for execution counts'}
    v['proof_bindings']={x.name:n.identity(x.read_bytes()) for x in n.PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
    n.write(n.PROOF/'verification.json',v)
    text=(n.PROOF/(n.CASE+'.stderr.txt')).read_text()
    n.need(v['status']=='FAIL' and 'NATURAL_TRACE ' in text and 'natural initial moves differ from locked original' in text,'expected diagnosed failure only')
    # Export only declared text source, never ROM/save files.
    for source in ('src/modernization/pr16_learnset_progress_game.c','state/source-lock.json'):
        path=n.ROOT/source
        if path.is_file():(n.PROOF/('source-'+path.name)).write_text(path.read_text())
    result=subprocess.run(['git','grep','-n','-E','CreateWildMon|GiveBoxMonInitialMoveset|SetWildMon|wild.*moves','--','scripts','src','overlays'],cwd=n.ROOT,capture_output=True)
    n.need(result.returncode in (0,1) and len(result.stdout)<1500000,'bounded source search')
    (n.PROOF/'source-caller-search.txt').write_bytes(result.stdout)
    v['fresh_cores']=1;v['trace_calls']=len(re.findall(r'^NATURAL_TRACE ',text,re.M))
    v['proof_bindings']={x.name:n.identity(x.read_bytes()) for x in n.PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
    n.write(n.PROOF/'verification.json',v)
    print('PASS_DIAGNOSIS_ONLY; native result remains FAIL; new unit tests 0')

if __name__=='__main__':execute()
