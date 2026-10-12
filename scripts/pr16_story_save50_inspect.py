#!/usr/bin/env python3
"""Save49から先の505経路に必要な未読地形と東側ownerだけ。native0。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save49_accept as a
from pr16_story_after_maori import need,identity,unpack,write
h=a.m.h
BASE='2b6c88be3bf78efabe1624335d22cb790c0c5f8c'
OUT=ROOT/'.local/pr16-story-save50-inspect'
CODE={'scripts/pr16_story_save50_inspect.py','.github/workflows/pr16-story-save50-inspect.yml'}
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'未読505範囲の初回採取だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    need(state['story_save49']['story_fast_save']==a.OUTPUT,'正式Save49からだけ')
    OUT.mkdir(parents=True);old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    need(identity(raw)==a.shared.plan.CANDIDATE,'同一固定ROM')
    source=ROOT/'content/modernization/pr16_story_save44_evidence/inspection.json'
    view=json.loads(source.read_bytes())['static_south_map'];need(view['map']==[3,23],'保存済505mapのみ')
    width,height,_,blocks,primary,secondary=unpack(raw,view['layout'],'IIIIII');need((width,height)==(48,40),'保存済寸法')
    cells=[]
    for y in range(height):
        for x in range(26,width):
            if (x,y)==(33,0) or view['collision_grid'][y][x]not in('.','O'):continue
            v,=unpack(raw,blocks+2*(y*width+x),'H');tile=v&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
            behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')
            cells.append(dict(xy=[x,y],elevation=v>>12,collision=(v>>10)&3,behavior=behavior&511))
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,COMMAND_LENGTHS,_trainerbattle_size,_decode_map_scripts
    rom=RomImage('save49-route505-new-owners',raw)
    roots,refs,rows=_decode_map_scripts(rom,view['scripts'],'route505')
    events,=unpack(raw,view['header']+4,'I');no,nw,nc,nb=unpack(raw,events,'BBBB');need(nc<=64,'有限座標event')
    objectptr,warpptr,coordptr,bgptr=unpack(raw,events+4,'IIII');coords=[]
    for i in range(nc):
        q=coordptr+16*i;x,y,elev=unpack(raw,q,'hhB');var,value=unpack(raw,q+6,'HH');script,=unpack(raw,q+12,'I')
        coords.append(dict(index=i,xy=[x,y],elevation=elev,trigger_var=var,trigger_value=value,script=script))
        if x>=26 and script:roots.append(ScriptRoot(script,'east_coord_'+str(i),'coord'))
    for obj in view['objects']:
        if obj['xy'][0]>=26 and obj['script']:roots.append(ScriptRoot(obj['script'],'east_npc_'+str(obj['local_id']),'object'))
    walker=ScriptWalker(rom)
    for root in roots:walker.add_root(root)
    graph=walker.walk();need(not graph['diagnostics'] and len(graph['nodes'])<=128,'新505owner有限graph診断0')
    instructions=[]
    for node in graph['nodes']:
        pc=node['address']
        for _ in range(node['instruction_count']):
            op=rom.u8(pc);size=_trainerbattle_size(rom.u8(pc+1))if op==0x5c else COMMAND_LENGTHS[op];need(0<size<=32,'有界script命令')
            data=raw[pc-0x08000000:pc-0x08000000+size];instructions.append(dict(address=pc,opcode=op,size=size,hex=data.hex(),node=node['address']));pc+=size
    need(sum(i['size']for i in instructions)<=65536,'有限新script')
    done=a.m.inherited.terminal(37142517526,'76ba6c8ff45c9f1f0943a7e2741bef643d279f81',111259715046,['success']*11)
    result=dict(status='STATIC_ROUTE505_TERRAIN_OWNERS_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,
        inherited_view=view,inherited_preparation=identity(source.read_bytes()),new_terrain_cells=len(cells),allcells=cells,map_script_rows=rows,map_script_references=refs,coords=coords,graph=graph,instructions=instructions,
        new_map_views=0,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,prior_record=done)
    need(h.d.bindings(protected)==protected,'全既受入正本不変');write(OUT/'inspection.json',result)
    print(json.dumps(dict(status=result['status'],cells=len(cells),new_nodes=len(graph['nodes']),new_instructions=len(instructions)),ensure_ascii=False))
if __name__=='__main__':main()
