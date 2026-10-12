#!/usr/bin/env python3
"""Save24後の東通路trainer/残PP/階段候補を固定ROMで限定照合。入力0。"""
from __future__ import annotations
import json, os, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save24_accept as a
from pr16_story_after_maori import need,identity,write,unpack
from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,_decode_trainer_party
BASE='35d93c421ea266455f23eba7ee6fd10599b3dae2'
OUT=ROOT/'.local/pr16-story-save25-prepare'
CODE={'scripts/pr16_story_save25_prepare.py','tests/test_pr16_story_save25_prepare.py','.github/workflows/pr16-story-save25-prepare.yml'}
TARGETS=[(5,[33,7],351,0x09370968),(6,[30,13],352,0x09370984),(7,[21,17],353,0x093709a0)]
ROUTE=[[31,y] for y in range(4,13)]+[[x,12] for x in range(32,35)]+[[34,13],[34,14],[34,15]]+[[x,15] for x in range(33,22,-1)]+[[23,14],[23,13],[22,13],[21,13],[20,13],[19,13],[19,14]]
def party(saved):
    table,_=a.d.m.prior.parent.sectors.bank(saved,0,24,a.d.m.prior.parent.sectors.LAYOUT)
    rows=[]
    for i in range(4):
        p=table[1]+56+i*100
        rows.append(dict(slot=i,species=struct.unpack_from('<H',saved,p+32)[0],moves=list(struct.unpack_from('<4H',saved,p+44)),
                         pp=list(saved[p+52:p+56]),hp=list(struct.unpack_from('<HH',saved,p+86))))
    need(rows[0]==dict(slot=0,species=150,moves=[600,366,53,58],pp=[1,14,5,5],hp=[324,354]),'Save24主力PP/HPを保存原本で照合')
    return rows
def inspect(raw,saved):
    need(identity(raw)==a.d.m.shared.plan.CANDIDATE and identity(saved)==a.OUTPUT,'唯一の候補/Save24')
    r=RomImage('save24-east-trainers',raw)
    events=r.u32(137444032+4);objects=r.u32(events+4)
    rows=[]
    for local,xy,tid,address in TARGETS:
        record=objects+24*(local-1)
        need(r.u8(record)==local and [r.s16(record+4),r.s16(record+6)]==xy and r.u32(record+16)==address,'実NPC owner')
        w=ScriptWalker(r);w.add_root(ScriptRoot(address,'cave-east-'+str(local),'object'));g=w.walk()
        refs=[v for v in g['references'] if v.get('category')=='trainer' and v.get('instruction_address')==address]
        need(not g['diagnostics'] and len(refs)==1 and refs[0]['value']==tid and refs[0]['battle_type']==0,'通常trainerのroot')
        rows.append(dict(local_id=local,xy=xy,script=address,trainer_id=tid,graph=g))
    width,height,_,blocks,primary,secondary=unpack(raw,137190172,'IIIIII')
    cells=unpack(raw,blocks,'H'*(width*height));terrain=[]
    for x,y in ROUTE:
        cell=cells[y*width+x];tile=cell&1023
        base,index=(primary,tile) if tile<0x280 else (secondary,tile-0x280)
        behavior=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')[0]&511
        terrain.append(dict(xy=[x,y],elevation=cell>>12,collision=(cell>>10)&3,behavior=behavior))
    need(all(v['collision']==0 for v in terrain),'静的経路はcollision0のみ')
    need(terrain[-7]['xy']==[23,14] and terrain[-7]['elevation']==0 and terrain[-7]['behavior']==42,'高さ0の岩階段')
    return dict(status='PASS_EAST_TRAINER_OWNERS_PP_TERRAIN_STATIC_ONLY',trainers=rows,party=party(saved),route=ROUTE,terrain=terrain,
                native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,rom_changes=0,save_changes=0,
                trainer_victories_accepted=0,teleport_accepted=False,cave_crossing_complete=False,release_ready=False)
def main():
    h=a.d.m.h;h.d.current();state=h.source_check()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'初回限定')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    OUT.mkdir()
    meta,z=a.d.m.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        raw=z.read('candidate.gba');saved=z.read('story-fast.srm')
    result=inspect(raw,saved);write(OUT/'inspection.json',result)
    record=a.d.m.h.d.inputs.api('actions/runs/37094105840')
    need(record['status']=='completed' and record['conclusion']=='success','Save24記録終端')
    # 保存済み固定runtimeを転送可能な大きさへ分割。実行・compile・ROM生成をしない。
    _,z=a.d.m.transport.archive(10898620034,36218655601,dict(size=102586759,sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                dest=OUT/'runtime'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    need(identity((OUT/'runtime/lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA')
    write(OUT/'runtime/manifest.json',{p.relative_to(OUT/'runtime').as_posix():identity(p.read_bytes()) for p in (OUT/'runtime').rglob('*') if p.is_file()})
    need(h.d.bindings(protected)==protected,'全受入source不変')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
