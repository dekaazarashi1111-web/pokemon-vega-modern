#!/usr/bin/env python3
"""こころのやかた1/59の未読ownerと像探索に必要な地形だけを採取。既読graphを再利用。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save55_accept as a
from pr16_story_after_maori import need,identity,unpack,write,map_view
h=a.m.h
BASE='0a13f73595b58afc5d61ea1092bdc9385d2bd23a'
OUT=ROOT/'.local/pr16-story-save56-inspect'
CODE={'scripts/pr16_story_save56_inspect.py','.github/workflows/pr16-story-save56-inspect.yml'}
def inspect(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,COMMAND_LENGTHS,_trainerbattle_size,_decode_map_scripts,MAP_GROUPS_POINTER_SITE
    source=ROOT/'content/modernization/pr16_story_save55_preparation.json';p=json.loads(source.read_bytes());v=p['town']
    need(identity(raw)==a.shared.plan.CANDIDATE and v['map']==[3,2],'同一ROM/既読town')
    need(next(w for w in v['warps']if w['xy']==[15,19])['target_map']==[1,59],'必須やかた入口')
    rom=RomImage('save55-heart-mansion',raw);groups,=unpack(raw,MAP_GROUPS_POINTER_SITE,'I');interior=map_view(raw,groups,1,59)
    walker=ScriptWalker(rom);inherited=[]
    for n in p['graph']['nodes']:
        node={k:n[k]for k in('address','end_reason','instruction_count','edges')};node['references']=[{k:r[k]for k in r if k not in('script_address','roots')}for r in p['graph']['references']if r['script_address']==n['address']]
        walker.nodes[n['address']]=node;inherited.append(n['address'])
    roots,refs,rows=_decode_map_scripts(rom,interior['scripts'],'mansion');coords=[];bgs=[]
    for root in roots:walker.add_root(root)
    for o in interior['objects']:
        if o['script']:walker.add_root(ScriptRoot(o['script'],'mansion_npc_'+str(o['local_id']),'object'))
    events,=unpack(raw,interior['header']+4,'I');no,nw,nc,nb=unpack(raw,events,'BBBB');op,wp,cp,bp=unpack(raw,events+4,'IIII');need(nc<=64 and nb<=64,'有限室内event')
    for i in range(nc):
        q=cp+16*i;x,y,elev=unpack(raw,q,'hhB');var,val=unpack(raw,q+6,'HH');script,=unpack(raw,q+12,'I');coords.append(dict(map=interior['map'],index=i,xy=[x,y],elevation=elev,trigger_var=var,trigger_value=val,script=script))
        if script:walker.add_root(ScriptRoot(script,'mansion_coord_'+str(i),'coord'))
    for i in range(nb):
        q=bp+12*i;x,y,elev,kind=unpack(raw,q,'hhBB');value,=unpack(raw,q+8,'I');row=dict(map=interior['map'],index=i,xy=[x,y],elevation=elev,kind=kind,value=value);bgs.append(row)
        if kind not in(7,8) and value:walker.add_root(ScriptRoot(value,'mansion_bg_'+str(i),'bg'))
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
    terrain=[]
    width,height,_,blocks,primary,secondary=unpack(raw,interior['layout'],'IIIIII')
    need(width*height<=2048,'像の周囲を含む室内だけ')
    for y in range(height):
        for x in range(width):
            value,=unpack(raw,blocks+2*(y*width+x),'H');tile=value&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
            behavior,=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I');terrain.append(dict(map=interior['map'],xy=[x,y],tile=tile,elevation=value>>12,collision=(value>>10)&3,behavior=behavior&511))
    return dict(inherited_owner=identity(source.read_bytes()),town=v,interior=interior,coords=coords,bgs=bgs,map_scripts=rows,map_references=refs,graph=graph,instructions=instructions,texts=texts,terrain=terrain,inherited_script_nodes=sorted(set(inherited)),new_script_nodes=len(graph['nodes'])-len(set(inherited)),new_terrain_cells=len(terrain),new_map_views=1,native_route_accepted=False)

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'初回限定採取')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE);need(state['story_save55']['story_fast_save']==a.OUTPUT,'正式Save55親')
    old=a.m.m.a;_,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    result=inspect(raw);result.update(status='STATIC_SAVE56_MANSION_OWNER_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0)
    need(h.d.bindings(protected)==protected,'旧受入不変');write(OUT/'inspection.json',result);print(json.dumps(dict(status=result['status'],cells=result['new_terrain_cells'],nodes=result['new_script_nodes']),ensure_ascii=False))
if __name__=='__main__':main()
