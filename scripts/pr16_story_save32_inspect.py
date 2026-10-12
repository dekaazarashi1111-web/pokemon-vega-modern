#!/usr/bin/env python3
"""Save31南側以降に必要な未読地形/隣接map/story ownerだけを採取。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save31_accept as a
from pr16_story_after_maori import need,identity,unpack,map_view,write
h=a.m.h
BASE='baace8a83125bda71e931a9d44891fd37e52f99f'
OUT=ROOT/'.local/pr16-story-save32-inspect'
CODE={'scripts/pr16_story_save32_inspect.py','.github/workflows/pr16-story-save32-inspect.yml'}
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'初回の未読範囲だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    need(state['story_save31']['story_fast_save']==a.OUTPUT,'Save31受入後だけ')
    OUT.mkdir(parents=True)
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    need(identity(raw)==a.shared.plan.CANDIDATE,'固定candidateだけ')
    previous={}
    def reuse(v):
        if isinstance(v,dict):
            if all(k in v for k in ('xy','elevation','collision','behavior')):
                xy=tuple(v['xy']);cell={k:v[k]for k in ('xy','elevation','collision','behavior')}
                need(xy not in previous or previous[xy]==cell,'既存採取原本一致');previous[xy]=cell
            for x in v.values():reuse(x)
        elif isinstance(v,list):
            for x in v:reuse(x)
    for n in range(24,32):
        p=ROOT/f'content/modernization/pr16_story_save{n}_evidence/inspection.json'
        if p.exists():reuse(json.loads(p.read_bytes()))
    view=json.loads((ROOT/'content/modernization/pr16_story_save23_evidence/inspection.json').read_bytes())['maps'][1]
    width,height,_,blocks,primary,secondary=unpack(raw,view['layout'],'IIIIII')
    need((width,height)==(40,23),'既存map寸法')
    fresh=[];allcells=[]
    for y in range(height):
        for x in range(width):
            if (x,y)in previous:cell=previous[x,y]
            else:
                v,=unpack(raw,blocks+2*(y*width+x),'H');tile=v&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
                behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')
                cell=dict(xy=[x,y],elevation=v>>12,collision=(v>>10)&3,behavior=behavior&511);fresh.append(cell)
            allcells.append(cell)
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE
    groups,=unpack(raw,MAP_GROUPS_POINTER_SITE,'I')
    adjacent=[map_view(raw,groups,1,n)for n in (37,38,72)]
    w=ScriptWalker(RomImage('save31-new-coordinate',raw));w.add_root(ScriptRoot(0x082146f1,'coord_7_5','coord'));graph=w.walk()
    need(not graph['diagnostics'],'新owner診断0')
    done=a.m.inherited.terminal(37120967764,'c0327a3c9f0cf9940a7cb2b11c508c4ce87dd985',111196833683,['success']*11)
    result=dict(status='STATIC_NEW_TERRAIN_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,
        inherited_cells=len(previous),new_cells=len(fresh),allcells=allcells,new_terrain=fresh,previous_view=view,adjacent_maps=adjacent,coord7_5_graph=graph,
        coord7_5_bytes=raw[0x2146f1:0x2147dd].hex(),native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,prior_record=done)
    need(len(allcells)==920 and len(previous)+len(fresh)==920,'全地形の非重複分割')
    need(h.d.bindings(protected)==protected,'既受入原本保持')
    write(OUT/'inspection.json',result)
    print(json.dumps(dict(status=result['status'],inherited_cells=len(previous),new_cells=len(fresh),graph_nodes=len(graph['nodes'])),ensure_ascii=False))
if __name__=='__main__':main()
