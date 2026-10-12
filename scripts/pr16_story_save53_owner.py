#!/usr/bin/env python3
"""Save52のミルシティ回復候補のownerと必要地形を限定読取。native0。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save52_accept as a
from pr16_story_after_maori import need,identity,unpack,write,map_view
h=a.m.h
BASE='cb5100a3a7b88b017b49908779e2a87344911c3a'
OUT=ROOT/'.local/pr16-story-save53-owner'
CODE={'scripts/pr16_story_save53_owner.py','.github/workflows/pr16-story-save53-owner.yml','content/modernization/pr16_story_save53_preparation.json'}
def inspect(raw,view):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,COMMAND_LENGTHS,_trainerbattle_size,_decode_map_scripts,MAP_GROUPS_POINTER_SITE
    need(view['map']==[3,2],'保存済townだけ')
    groups,=unpack(raw,MAP_GROUPS_POINTER_SITE,'I')
    # 最初のwarpを候補とするだけ。採用はscript graphのheal owner照合後。
    w=view['warps'][5];need(w['target_map']==[6,5]and w['xy']==[38,15],'固定候補warp')
    inside=map_view(raw,groups,*w['target_map'])
    rom=RomImage('save52-miru-healing-candidate',raw);roots=[];allrows=[];allrefs=[];coords=[]
    for v in(inside,):
        rr,refs,rows=_decode_map_scripts(rom,v['scripts'],'map_'+str(v['map']));roots+=rr;allrows+=rows;allrefs+=refs
        events,=unpack(raw,v['header']+4,'I');no,nw,nc,nb=unpack(raw,events,'BBBB');op,wp,cp,bp=unpack(raw,events+4,'IIII');need(nc<=64,'有限座標event')
        for i in range(nc):
            q=cp+16*i;x,y,elev=unpack(raw,q,'hhB');var,value=unpack(raw,q+6,'HH');script,=unpack(raw,q+12,'I')
            row=dict(map=v['map'],index=i,xy=[x,y],elevation=elev,trigger_var=var,trigger_value=value,script=script);coords.append(row)
            if script:roots.append(ScriptRoot(script,'coord_'+str(v['map'])+'_'+str(i),'coord'))
        if v is inside:
            for o in v['objects']:
                if o['script']:roots.append(ScriptRoot(o['script'],'candidate_npc_'+str(o['local_id']),'object'))
    walker=ScriptWalker(rom)
    for root in roots:walker.add_root(root)
    graph=walker.walk();need(not graph['diagnostics']and len(graph['nodes'])<=512,'必要なtown/候補ownerの有界graph')
    instructions=[]
    for node in graph['nodes']:
        pc=node['address']
        for _ in range(node['instruction_count']):
            op=rom.u8(pc);size=_trainerbattle_size(rom.u8(pc+1))if op==0x5c else COMMAND_LENGTHS[op];need(0<size<=32,'有界命令')
            data=raw[pc-0x08000000:pc-0x08000000+size];instructions.append(dict(address=pc,opcode=op,size=size,hex=data.hex(),node=node['address']));pc+=size
    terrain=[]
    width,height,_,blocks,primary,secondary=unpack(raw,view['layout'],'IIIIII')
    for x,y in [(35,16),(36,16),(37,16),(38,16),(38,15)]:
        v,=unpack(raw,blocks+2*(y*width+x),'H');tile=v&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
        behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I');terrain.append(dict(xy=[x,y],elevation=v>>12,collision=(v>>10)&3,behavior=behavior&511))
    return dict(inherited_view=view,candidate_interior=inside,map_script_rows=allrows,map_script_references=allrefs,coords=coords,graph=graph,instructions=instructions,terrain=terrain,new_terrain_cells=len(terrain),new_map_views=1,new_script_nodes=len(graph['nodes']),facility_owner_accepted=False,native_route_accepted=False)
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'初回限定採取')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE);need(state['story_save52']['story_fast_save']==a.OUTPUT,'Save52正式親')
    OUT.mkdir(parents=True);old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    need(identity(raw)==a.shared.plan.CANDIDATE,'同じ候補ROM')
    source=ROOT/'content/modernization/pr16_story_save53_preparation.json';prior=json.loads(source.read_bytes());view=prior['inherited_view'];result=inspect(raw,view)
    result['prior_read_only_inspection']=identity(source.read_bytes());result['rejected_candidate_6_0_reason_ja']='map6/0 ownerに回復specialなし。50円の受付/見学scriptだけであり回復施設と断定しない。'
    result['previous_terrain']=prior['terrain'];result['previous_coords']=prior['coords'];result['town_script_graph']=prior['graph']
    done=a.m.inherited.terminal(37147254753,'9e4b701087c609141774a6a746b96bdc1aeede66',111273645819,['success']*11)
    result.update(status='STATIC_MIRU_HEALING_OWNER_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,inherited_preparation=identity(source.read_bytes()),native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,prior_record=done)
    need(h.d.bindings(protected)==protected,'旧受入不変');write(OUT/'inspection.json',result)
    print(json.dumps(dict(status=result['status'],cells=result['new_terrain_cells'],nodes=result['new_script_nodes']),ensure_ascii=False))
if __name__=='__main__':main()
