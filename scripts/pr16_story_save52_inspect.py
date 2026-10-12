#!/usr/bin/env python3
"""Save51の先のダブルtrainer視界回避に必要な未読object属性16byteだけ。native0。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save51_accept as a
from pr16_story_after_maori import need,identity,unpack,write
h=a.m.h
BASE='09e892da2e0c864b09c9698ee2e5ec54dbf603b1'
OUT=ROOT/'.local/pr16-story-save52-inspect'
CODE={'scripts/pr16_story_save52_inspect.py','.github/workflows/pr16-story-save52-inspect.yml'}
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'未読object属性の初回採取だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    need(state['story_save51']['story_fast_save']==a.OUTPUT,'正式Save51だけ')
    OUT.mkdir(parents=True);old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    need(identity(raw)==a.shared.plan.CANDIDATE,'同一固定ROM')
    source=ROOT/'content/modernization/pr16_story_save50_preparation.json';prior=json.loads(source.read_bytes());view=prior['inherited_view'];need(view['map']==[3,23],'保存済505')
    events,=unpack(raw,view['header']+4,'I');no,nw,nc,nb=unpack(raw,events,'BBBB');ptr,=unpack(raw,events+4,'I');need(no==len(view['objects'])==9,'保存済object9')
    result=[]
    for obj in view['objects']:
        if obj['local_id']not in(3,8):continue
        base=ptr+24*(obj['local_id']-1);local,=unpack(raw,base,'B');x,y=unpack(raw,base+4,'hh');script,=unpack(raw,base+16,'I')
        need(local==obj['local_id']and[x,y]==obj['xy']and script==obj['script']==154590315,'既読double owner identity')
        elevation,movement,radius,padding,trainer,range_=unpack(raw,base+8,'BBBBHH')
        result.append(dict(local_id=local,xy=[x,y],elevation=elevation,movement_type=movement,movement_range_x=radius&15,movement_range_y=radius>>4,padding_byte11=padding,trainer_type=trainer,trainer_range=range_,script=script))
    need(len(result)==2,'必要な2体だけ')
    done=a.m.inherited.terminal(37146098901,'5803a1894ce67270c32e923ececf539d589ee653',111270247423,['success']*11)
    report=dict(status='STATIC_ROUTE505_PAIR_ATTRIBUTES_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,inherited_preparation=identity(source.read_bytes()),objects=result,new_object_attribute_bytes=16,new_terrain_cells=0,new_map_views=0,new_script_nodes=0,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,prior_record=done)
    need(h.d.bindings(protected)==protected,'旧受入正本不変');write(OUT/'inspection.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
