#!/usr/bin/env python3
"""回復後ミルシティの未読NPC/ジム入口ownerだけを採取。既読map/graphを再利用。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save54_accept as a
from pr16_story_after_maori import need,identity,unpack,write,map_view
h=a.m.h
BASE='170a3a49bcc802bc028723776424ebc7f805139d'
OUT=ROOT/'.local/pr16-story-save55-inspect'
CODE={'scripts/pr16_story_save55_inspect.py','.github/workflows/pr16-story-save55-inspect.yml'}
def inspect(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,COMMAND_LENGTHS,_trainerbattle_size,_decode_map_scripts,MAP_GROUPS_POINTER_SITE
    source=ROOT/'content/modernization/pr16_story_save53_owner.json';p=json.loads(source.read_bytes());v=p['inherited_view'];interior=p['candidate_interior']
    need(identity(raw)==a.shared.plan.CANDIDATE and v['map']==[3,2]and interior['map']==[6,5],'既読town/回復施設')
    rom=RomImage('save54-miru-next-story',raw);groups,=unpack(raw,MAP_GROUPS_POINTER_SITE,'I');gym=map_view(raw,groups,39,0)
    walker=ScriptWalker(rom);inherited=[]
    # 各graphの保存nodeとreferencesから復元し、既読scriptを再decodeしない。
    for graph in[p['graph'],p['town_script_graph']]:
        for n in graph['nodes']:
            node={k:n[k]for k in('address','end_reason','instruction_count','edges')};node['references']=[{k:r[k]for k in r if k not in('script_address','roots')}for r in graph['references']if r['script_address']==n['address']]
            walker.nodes[n['address']]=node;inherited.append(n['address'])
    for o in v['objects']:
        if o['script']:walker.add_root(ScriptRoot(o['script'],'town_npc_'+str(o['local_id']),'object'))
    roots,refs,rows=_decode_map_scripts(rom,gym['scripts'],'gym');coords=[]
    for root in roots:walker.add_root(root)
    for o in gym['objects']:
        if o['script']:walker.add_root(ScriptRoot(o['script'],'gym_npc_'+str(o['local_id']),'object'))
    events,=unpack(raw,gym['header']+4,'I');no,nw,nc,nb=unpack(raw,events,'BBBB');op,wp,cp,bp=unpack(raw,events+4,'IIII');need(nc<=64,'有限gym座標event')
    for i in range(nc):
        q=cp+16*i;x,y,elev=unpack(raw,q,'hhB');var,val=unpack(raw,q+6,'HH');script,=unpack(raw,q+12,'I');coords.append(dict(map=gym['map'],index=i,xy=[x,y],elevation=elev,trigger_var=var,trigger_value=val,script=script))
        if script:walker.add_root(ScriptRoot(script,'gym_coord_'+str(i),'coord'))
    graph=walker.walk();need(not graph['diagnostics']and len(graph['nodes'])<512,'必要ownerの有界graph')
    instructions=[];texts={}
    for node in graph['nodes']:
        if node['address']in inherited:continue
        pc=node['address']
        for _ in range(node['instruction_count']):
            op=rom.u8(pc);size=_trainerbattle_size(rom.u8(pc+1))if op==0x5c else COMMAND_LENGTHS[op];need(0<size<=32,'有限命令')
            data=rom.raw(pc,size);instructions.append(dict(address=pc,opcode=op,size=size,hex=data.hex(),node=node['address']))
            # loadpointer/messageの文字列だけ上限512byte。命令やROM全体は転載しない。
            ptrs=[]
            if op==0x0f:ptrs=[int.from_bytes(data[2:6],'little')]
            elif op==0x67:ptrs=[int.from_bytes(data[1:5],'little')]
            elif op==0x5c:ptrs=[int.from_bytes(data[j:j+4],'little')for j in(6,10)if j+4<=len(data)]
            for ptr in ptrs:
                if ptr in texts or not rom.contains(ptr):continue
                chunk=rom.raw(ptr,min(512,rom.end-ptr));end=chunk.find(b'\xff')
                if end>=0:texts[ptr]=chunk[:end+1].hex()
            pc+=size
    oldcells={tuple(t['xy']):t for t in p['previous_terrain']+p['terrain']};terrain=[]
    for view,points in[(interior,[(7,8)]),(v,[(x,y)for y in range(8,17)for x in range(8,13)])]:
        width,height,_,blocks,primary,secondary=unpack(raw,view['layout'],'IIIIII')
        for x,y in points:
            if view is v and (x,y)in oldcells:continue
            value,=unpack(raw,blocks+2*(y*width+x),'H');tile=value&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
            behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I');terrain.append(dict(map=view['map'],xy=[x,y],elevation=value>>12,collision=(value>>10)&3,behavior=behavior&511))
    return dict(inherited_owner=identity(source.read_bytes()),town=v,interior=interior,gym=gym,gym_coords=coords,gym_map_scripts=rows,gym_map_references=refs,graph=graph,instructions=instructions,texts=texts,new_terrain=terrain,inherited_script_nodes=sorted(set(inherited)),new_script_nodes=len(graph['nodes'])-len(set(inherited)),new_terrain_cells=len(terrain),new_map_views=1,native_route_accepted=False)
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'初回限定採取')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE);need(state['story_save54']['story_fast_save']==a.OUTPUT,'正式Save54親')
    old=a.m.m.a;_,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    result=inspect(raw);result.update(status='STATIC_SAVE55_MIRU_OWNER_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0)
    need(h.d.bindings(protected)==protected,'旧受入不変');write(OUT/'inspection.json',result);print(json.dumps(dict(status=result['status'],cells=result['new_terrain_cells'],nodes=result['new_script_nodes']),ensure_ascii=False))
if __name__=='__main__':main()
