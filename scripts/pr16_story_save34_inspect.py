#!/usr/bin/env python3
"""Save33西側経路に必要な未読map-load scriptだけ。既存920地形/coord原本は再採取しない。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save33_accept as a
from pr16_story_after_maori import need,identity,unpack,write
h=a.m.h
BASE='d04da36893482bddd2405e2230b2690f5aa2e739'
OUT=ROOT/'.local/pr16-story-save34-inspect'
CODE={'scripts/pr16_story_save34_inspect.py','.github/workflows/pr16-story-save34-inspect.yml'}
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'初回の未読map-loadだけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    need(state['story_save33']['story_fast_save']==a.OUTPUT,'Save33受入後だけ')
    OUT.mkdir(parents=True);old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:raw=z.read('candidate.gba')
    need(identity(raw)==a.shared.plan.CANDIDATE,'固定candidateだけ')
    prep=json.loads((ROOT/a.m.PREP).read_bytes());view=prep['previous_view']
    need(view['map']==[1,73] and view['header']==137444032 and view['scripts']==135697300 and len(prep['allcells'])==920,'保存済map/全地形原本')
    need(unpack(raw,view['header']+8,'I')[0]==view['scripts'],'固定map-load pointer')
    from tools.t02.rom_inventory import RomImage,ScriptWalker,COMMAND_LENGTHS,_trainerbattle_size,_decode_map_scripts
    rom=RomImage('save33-cave-map-load',raw);roots,refs,rows=_decode_map_scripts(rom,view['scripts'],'cave_map1_73')
    need(roots and len(roots)<=32 and not any(x.get('status')for x in rows),'有限map-load table')
    w=ScriptWalker(rom)
    for root in roots:w.add_root(root)
    graph=w.walk();need(not graph['diagnostics'] and len(graph['nodes'])<=128,'有限新map-load graph診断0')
    instructions=[]
    for node in graph['nodes']:
        pc=node['address']
        for _ in range(node['instruction_count']):
            op=rom.u8(pc);size=_trainerbattle_size(rom.u8(pc+1))if op==0x5c else COMMAND_LENGTHS[op]
            need(0<size<=32,'有界script命令')
            data=raw[pc-0x08000000:pc-0x08000000+size]
            instructions.append(dict(address=pc,opcode=op,size=size,hex=data.hex(),node=node['address']))
            pc+=size
    need(sum(x['size']for x in instructions)<=65536,'全新script採取上限')
    done=a.m.inherited.terminal(37123210891,'6910abb080a36796bd570455eb7858828a5d3b51',111203247521,['success']*11)
    result=dict(status='STATIC_CAVE_MAP_LOAD_ONLY_NOT_NATIVE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=a.shared.plan.CANDIDATE,input_save=a.OUTPUT,
        map=[1,73],map_scripts=view['scripts'],map_script_rows=rows,map_script_references=refs,graph=graph,instructions=instructions,
        inherited_preparation=identity((ROOT/a.m.PREP).read_bytes()),inherited_cells=920,new_terrain_cells=0,native_processes=0,rom_changes=0,save_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,prior_record=done)
    need(h.d.bindings(protected)==protected,'既受入原本保持');write(OUT/'inspection.json',result)
    print(json.dumps(dict(status=result['status'],new_nodes=len(graph['nodes']),new_instructions=len(instructions),map_script_rows=rows),ensure_ascii=False))
if __name__=='__main__':main()
