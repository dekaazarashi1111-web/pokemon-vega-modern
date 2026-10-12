#!/usr/bin/env python3
"""Save53回復施設の未読5cellsだけ。既存owner/mapを再採取しない。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save53_accept as a
from pr16_story_after_maori import need,identity,unpack,write
h=a.m.h
BASE='e55598a4c32f45491cb8b62dfca6320ee3f69f2f'
OUT=ROOT/'.local/pr16-story-save54-inspect'
CODE={'scripts/pr16_story_save54_inspect.py','.github/workflows/pr16-story-save54-inspect.yml'}
def inspect(raw):
    source=ROOT/'content/modernization/pr16_story_save53_owner.json';p=json.loads(source.read_bytes());v=p['candidate_interior']
    need(identity(raw)==a.shared.plan.CANDIDATE and v['map']==[6,5]and v['layout']==136944192,'同一候補と既読室内だけ')
    width,height,_,blocks,primary,secondary=unpack(raw,v['layout'],'IIIIII');need((width,height)==(15,10),'既読layout')
    terrain=[]
    for x,y in[(7,7),(7,6),(7,5),(7,4),(7,3)]:
        value,=unpack(raw,blocks+2*(y*width+x),'H');tile=value&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
        behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I');terrain.append(dict(xy=[x,y],elevation=value>>12,collision=(value>>10)&3,behavior=behavior&511))
    return dict(inherited_owner=identity(source.read_bytes()),interior=v,terrain=terrain,new_terrain_cells=5,new_map_views=0,new_script_nodes=0,new_object_attribute_bytes=0,route=[[7,y]for y in range(8,3,-1)],healer=p['graph']['references'],native_route_accepted=False)
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'初回限定採取')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE);need(state['story_save53']['story_fast_save']==a.OUTPUT,'Save53正式親')
    old=a.m.m.a;_,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    result=inspect(raw);result.update(status='STATIC_SAVE54_INTERIOR_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0)
    need(h.d.bindings(protected)==protected,'旧受入不変');write(OUT/'inspection.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
