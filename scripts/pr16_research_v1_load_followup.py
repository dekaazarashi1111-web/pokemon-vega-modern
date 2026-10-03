#!/usr/bin/env python3
"""起動先行callと通常loadを分離。旧26試験/fixture/oracleは変更しない。"""
from __future__ import annotations
import json
import struct
from pathlib import Path
import pr16_research_v1_load as prior
need=prior.need
identity=prior.identity
FIRST_RETURN=0x080ED736
LOAD_RETURN=0x080789FE
ROOT=0x080DB4E4
BEFORE='if(vl_root&&!vl_root_done&&pc==vl_root_lr&&sp==vl_root_sp){vl_root_done=1;vl_root_result=r0;}'
AFTER='if(vl_root&&!vl_root_done&&pc==vl_root_lr&&sp==vl_root_sp){\n vl_root_done=1;vl_root_result=r0;\n printf("{\\"diagnostic_root\\":true,\\"result\\":%u,\\"type\\":%u,\\"counter\\":%u,\\"version\\":%u,\\"last\\":%u,\\"research\\":%u,\\"mirage\\":%u,\\"qol\\":%u,\\"root_lr\\":%u}\\n",r0,vl_type,read32(c,SI_COUNTER),si_read16(c,LC_LEDGER+4),si_read16(c,SI_VOL+16),vl_research,vl_mirage,vl_qol,vl_root_lr);fflush(stdout);\n if(read32(c,SI_COUNTER)==0){vl_root=vl_research=vl_mirage=vl_qol=vl_root_done=vl_research_done=0;}\n}'

def instrument(source):
    need(source.count(BEFORE)==1,'one original root-return boundary')
    return source.replace(BEFORE,AFTER)


def generate(seed):
    import pr16_research_lifecycle_v2 as base
    text=base.generate().read_text();token='int main(int argc,char**argv){'
    need(text.count(token)==1,'one original lifecycle main')
    header='#define VL_ROM "'+prior.CANDIDATE['sha256']+'"\nstatic const char* const VL_FIXTURES[]={'+','.join('"'+prior.fixture(seed,c)[1]['fixture']['sha256']+'"' for c in prior.CASES)+'};\n'
    return (header+text.replace(token,'int prior_lifecycle_main(int argc,char**argv){')+'\n'+instrument(Path('tools/mgba_pr16_research_v1_load.c').read_text())).encode()


def caller_bindings(candidate):
    need(identity(candidate)==prior.CANDIDATE,'unchanged exact candidate')
    rows=[]
    for ret in (FIRST_RETURN,LOAD_RETURN):
        a,b=struct.unpack_from('<HH',candidate,ret-4-0x08000000)
        need(a&0xF800==0xF000 and b&0xF800==0xF800,'Thumb BL caller')
        offset=((a&2047)<<12)|((b&2047)<<1)
        if offset&(1<<22):offset-=1<<23
        need(ret+offset==ROOT,'both callers reach same root')
        rows.append({'return_pc':ret,'call_pc':ret-4,'target':ret+offset})
    return rows


def root_expectations(case):
    need(case in prior.CASES,'closed case')
    valid=case==prior.CASES[0]
    common={'diagnostic_root':True,'type':0,'research':1,'mirage':1,'qol':1}
    return [dict(common,result=2,counter=0,version=0,last=65535,root_lr=FIRST_RETURN),
            dict(common,result=int(valid),counter=3 if valid else 2,version=2 if valid else 1,last=0 if valid else 7,root_lr=LOAD_RETURN)]


def validate(raw,case,save,baseline):
    need(0<len(raw)<=24000,'bounded root observations')
    lines=raw.decode('utf-8').splitlines()
    need(len(lines)==(11 if case==prior.CASES[0] else 5),'exact two root calls plus prior observations')
    roots=[prior.old.load(x) for x in lines[:2]]
    for got,want in zip(roots,root_expectations(case)):
        need(set(got)==set(want),'closed root observation schema')
        for key,value in want.items():
            need(type(got[key]) is type(value) and got[key]==value,'root '+key)
    legacy=('\n'.join(lines[2:])+'\n').encode()
    result=prior.validate(legacy,case,save,baseline)
    return dict(result,root_observations=roots,ordinary_root_calls=2,stdout=identity(raw),legacy_observations=identity(legacy))
