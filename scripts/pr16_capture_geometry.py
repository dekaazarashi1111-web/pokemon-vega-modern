#!/usr/bin/env python3
"""Read exact candidate walking geometry for the two rooted Eelektross tables.

This supplies input coordinates, never a generated Pokemon or encounter proof.
Collision, behavior and event exclusions are retained for runtime review.
"""
from pathlib import Path
import json
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_repaired_acceptance as repaired
from tools.trainer_final.kanto_events import _stage_map_state
need=repaired.need


def geometry(raw,group,number):
    def data(pointer,size):
        at=pointer-0x08000000
        need(0<=at<=len(raw)-size,'geometry pointer outside ROM')
        return raw[at:at+size]
    def u32(pointer):return struct.unpack('<I',data(pointer,4))[0]
    state=_stage_map_state(raw,group,number)
    layout=u32(state['map_header_address']);width,height=struct.unpack('<II',data(layout,8))
    need(0<width<=1024 and 0<height<=1024 and width*height<=0x100000,'geometry dimensions invalid')
    blocks=struct.unpack('<'+str(width*height)+'H',data(u32(layout+12),width*height*2))
    attributes=[u32(u32(layout+offset)+20) for offset in (16,20)]
    events=set()
    for obj in state['objects']:events.add(struct.unpack_from('<HH',obj,4))
    for name,stride in (('warps_hex',8),('coords_hex',16)):
        values=bytes.fromhex(state[name])
        for at in range(0,len(values),stride):events.add(struct.unpack_from('<HH',values,at))
    cells=[]
    for i,block in enumerate(blocks):
        tile=block&0x3ff;behavior=u32(attributes[tile>=640]+4*(tile if tile<640 else tile-640))&0x1ff
        cells.append(dict(x=i%width,y=i//width,collision=(block>>10)&3,elevation=block>>12,behavior=behavior,event=(i%width,i//width) in events))
    pairs=[]
    for c in cells:
        if c['collision'] or c['event']:continue
        for dx,dy in ((1,0),(0,1)):
            x,y=c['x']+dx,c['y']+dy
            if x>=width or y>=height:continue
            d=cells[y*width+x]
            if not d['collision'] and not d['event'] and d['elevation']==c['elevation'] and c['behavior']==d['behavior']:
                pairs.append(dict(start=[c['x'],c['y']],end=[x,y],behavior=c['behavior'],elevation=c['elevation']))
    need(pairs,'no candidate walking pair')
    return dict(group=group,map=number,width=width,height=height,layout=hex(layout),
                objects=[o.hex() for o in state['objects']],warps_hex=state['warps_hex'],coords_hex=state['coords_hex'],
                behavior_counts={str(b):sum(c['behavior']==b for c in cells) for b in sorted({c['behavior'] for c in cells})},
                walkable_pairs=pairs,native_encounter_accepted=False)


def run():
    raw=repaired.layer.source.checked(ROOT/repaired.ROM,repaired.ROM_SHA)
    value=dict(status='STATIC_GEOMETRY_NOT_NATIVE_CAPTURE',candidate=repaired.identity(raw),
               maps=[geometry(raw,1,n) for n in (113,118)],new_emulator_runs=0,release_ready=False)
    out=ROOT/'.local/pr16-capture-geometry';out.mkdir(parents=True,exist_ok=True)
    (out/'geometry.json').write_bytes(repaired.stable(value))
    print(json.dumps(dict(status=value['status'],maps=[dict(map=m['map'],pairs=len(m['walkable_pairs']),behaviors=m['behavior_counts']) for m in value['maps']],new_emulator_runs=0)))

if __name__=='__main__':run()
