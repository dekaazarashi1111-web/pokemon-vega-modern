#!/usr/bin/env python3
"""Add one Ring giver over the exact accepted BP candidate, without replaying BP.

This is a bounded successor, not P08 integration or native acceptance. Existing
NPCs/scripts/warps/coordinates remain byte-identical. Only the map's event root
and one allocator-owned new payload change.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_ring_npc_successor.py'
SOURCE = 'overlays/ring_npc/ring_npc.c'
HEADER = 'overlays/ring_npc/ring_npc.h'
OUT = ROOT/'.local/pr16-ring-npc-successor'
TASK = 'USER-20260918-RING-NPC'
PARENT_SHA = 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b'
BASE, SIZE = 0x08000000, 33554432
REGIONS = 'config/rom_regions.csv'
RESERVATION = 4096
ALLOCATION = 'pr16_ring_npc_runtime'
MAP = (96, 17)
TEMPLATE_MAP = (96, 5)
NPC_XY, FRONT_XY = (26, 19), (26, 20)  # synthetic-test defaults only
FINAL_FLAG, RING = 0x13FF, 580


class RingBuildError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise RingBuildError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode('utf-8')


def span(raw, address, size):
    need(type(address) is int and type(size) is int and size > 0, 'invalid ROM span')
    offset = address - BASE
    need(0 <= offset <= len(raw)-size, 'ROM span outside candidate')
    return raw[offset:offset+size]


def u32(raw, address):
    return struct.unpack('<I', span(raw, address, 4))[0]


def map_view(raw, map_key=MAP):
    groups = u32(raw, BASE+0x54B0C)
    header = u32(raw, u32(raw, groups+map_key[0]*4)+map_key[1]*4)
    header_bytes = span(raw, header, 0x1C)
    events = u32(raw, header+4)
    event_bytes = span(raw, events, 20)
    count = event_bytes[0]
    # Keep this new site below the conservative fifteen-template boundary.
    need(0 <= count <= 15, 'invalid live object count')
    objects = u32(raw, events+4)
    raw_objects = span(raw, objects, count*24) if count else b''
    rows = [raw_objects[i:i+24] for i in range(0, len(raw_objects), 24)]
    ids = [row[0] for row in rows]
    need(all(ids) and len(ids)==len(set(ids)), 'invalid/duplicate existing local IDs')
    return dict(header=header, header_hex=header_bytes.hex(), events=events,
                event_bytes=event_bytes, objects=objects, raw_objects=raw_objects,
                count=count, ids=ids)


def extend_objects(event_bytes, old_objects, script_address, objects_address, xy=NPC_XY, template=None):
    """Use the established map-object append ABI; do not repurpose a live script."""
    need(type(event_bytes) is bytes and len(event_bytes)==20, 'event header size differs')
    count = event_bytes[0]
    need(0 <= count <= 14 and type(old_objects) is bytes and len(old_objects)==24*count,
         'object count/table size differs')
    rows = [old_objects[i:i+24] for i in range(0,len(old_objects),24)]
    ids = [row[0] for row in rows]
    need(all(ids) and len(ids)==len(set(ids)), 'invalid/duplicate existing IDs')
    need(type(xy) is tuple and len(xy)==2 and all(type(v) is int and 0<=v<1024 for v in xy), 'invalid NPC coordinates')
    need(xy not in [struct.unpack_from('<HH',row,4) for row in rows], 'NPC cell already occupied')
    for address in (script_address, objects_address):
        need(type(address) is int and BASE<=address<BASE+SIZE, 'new pointer outside ROM')
    need(objects_address%4==0, 'unaligned object table')
    if template is None:
        templates = [row for row in rows if row[0]==2]
        need(len(templates)==1, 'accepted stationary reception template missing')
        template = templates[0]
    need(type(template) is bytes and len(template)==24 and template[0]==2, 'unsafe source template')
    need(struct.unpack_from('<HH',template,4)==(20,19), 'reception template position differs')
    new = bytearray(template)
    new_id = next(i for i in range(1,256) if i not in ids)
    new[0] = new_id
    struct.pack_into('<HH',new,4,*xy)
    new[10] = 0  # movement range; the accepted reception movement type is retained
    struct.pack_into('<HH',new,12,0,0)  # not a trainer or a berry tree
    struct.pack_into('<I',new,16,script_address)
    struct.pack_into('<H',new,20,0)  # always visible; progress is checked by the gift
    events = bytearray(event_bytes)
    events[0] += 1
    struct.pack_into('<I',events,4,objects_address)
    result = old_objects+bytes(new)
    need(result[:len(old_objects)]==old_objects, 'existing object mutation')
    need(events[1:4]==event_bytes[1:4] and events[8:]==event_bytes[8:], 'non-object event mutation')
    return bytes(events), result, dict(local_id=new_id,x=xy[0],y=xy[1],
        graphics_id=new[1],movement_type=new[9],elevation=new[8],
        cloned_from_local_id=2,script=script_address,flag=0,trainer_type=0)


def verify_manifests():
    with (ROOT/'manifests/flags.csv').open(encoding='utf-8',newline='') as f:
        flags=list(csv.DictReader(f))
    rows=[r for r in flags if r['flag_key']=='STATE_KEY_EVENT_MAIN_FINAL_LEAGUE_CLEARED_DONE']
    need(len(rows)==1 and int(rows[0]['id'],0)==FINAL_FLAG and rows[0]['owner']=='T20', 'final-league owner drift')
    with (ROOT/'manifests/item_ids.csv').open(encoding='utf-8',newline='') as f:
        items=list(csv.DictReader(f))
    rows=[r for r in items if r['item_key']=='ITEM_KEY_MEGA_RING']
    need(len(rows)==1 and int(rows[0]['id'],0)==RING and 'POCKET_KEY_ITEMS' in rows[0].values(), 'Ring item/key-pocket owner drift')


def compile_runtime(out, load):
    out.mkdir(parents=True,exist_ok=True)
    linker=out/'ring.ld'
    linker.write_text('ENTRY(VegaRingNpcInteract)\nSECTIONS { . = '+hex(load)+'; '
        '.text : { KEEP(*(.text.VegaRingNpcInteract)) *(.text*) *(.rodata*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n',encoding='utf-8')
    elf=out/'ring.elf'
    command=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi',
        '-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections',
        '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror',
        '-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none','-T',str(linker),str(ROOT/SOURCE),'-o',str(elf)]
    proc=subprocess.run(command,capture_output=True)
    (out/'compiler.stdout').write_bytes(proc.stdout);(out/'compiler.stderr').write_bytes(proc.stderr)
    need(proc.returncode==0,'Ring ARM compile failed; see compiler.stderr')
    symbols=subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True)
    (out/'symbols.txt').write_text(symbols,encoding='utf-8')
    entry=[int(line.split()[0],16) for line in symbols.splitlines() if line.split()[-1:]==['VegaRingNpcInteract']]
    need(len(entry)==1 and entry[0]&~1==load,'Ring entry placement differs')
    binary=out/'ring.bin'
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes()
    need(32<=len(payload)<=1024,'gift runtime outside bounded size')
    disassembly=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True)
    (out/'disassembly.txt').write_text(disassembly.replace(str(elf),'ring-npc.elf'),encoding='utf-8')
    return payload, entry[0]|1


def add_dialogue(blob, root, runtime_entry):
    from scripts.build_bp_shop_runtime import _Script, _add_script
    from tools.regression.rom_runtime import _charmap, _encode_text
    mapping,tokens=_charmap(root)
    messages={
        'ok':'メガリングを うけとった！\\nメガストーンを もたせて たたかおう！',
        'owned':'メガリングは もう もっているね。',
        'locked':'さいしゅうの リーグを クリアしたら\\nまた きてね。',
        'full':'バッグに あきを つくって\\nまた きてね。',
        'failed':'うけとれなかった。\\nもういちど はなしかけてね。',
    }
    for key,text in messages.items():
        blob.add('ring_text_'+key,_encode_text(text,mapping,tokens),1)
    start=_Script();start.emit(0x6A,0x5A)
    # callnative is a script operation, never an emulator host call.
    start.emit(0x23);start.data.extend(struct.pack('<I',runtime_entry))
    for value,key in ((1,'ok'),(2,'owned'),(3,'locked'),(4,'full')):
        start.compare_result(value);start.if_equal('ring_script_'+key)
    start.goto('ring_script_failed')
    _add_script(blob,'ring_script_npc',start)
    for key in messages:
        script=_Script();script.msgbox('ring_text_'+key);script.emit(0x6C,0x02)
        _add_script(blob,'ring_script_'+key,script)
    return messages


def choose_offset(allocation):
    from scripts.pr16_bp_party_retention_successor import existing_requests
    from tools.rom_allocator import build_allocation_report_from_csv
    requests=existing_requests(allocation)
    requests.append(dict(name=ALLOCATION,region='future_tail',size=RESERVATION,alignment=4,
        owner=TASK,purpose='Ring giver payload preview',content_sha256='0'*64))
    preview=build_allocation_report_from_csv(ROOT/REGIONS,requests)
    rows=[r for r in preview['allocations'] if r['name']==ALLOCATION]
    need(len(rows)==1,'Ring allocation absent')
    return rows[0]['start']


def make_payload(raw, offset, code, entry, xy, template):
    from tools.regression.rom_runtime import _Blob
    view=map_view(raw)
    blob=_Blob();blob.reserve('ring_header',64,4)
    need(blob.add('ring_code',code,4)==64 and entry==BASE+offset+65,'gift code/entry offset drift')
    messages=add_dialogue(blob,ROOT,entry)
    object_offset=(len(blob.data)+3)&~3
    # Scripts already have stable relative labels; pointer fixups are finalized below.
    script=BASE+offset+blob.labels['ring_script_npc']
    events,objects,npc=extend_objects(view['event_bytes'],view['raw_objects'],script,BASE+offset+object_offset,xy,template)
    need(blob.add('ring_objects',objects,4)==object_offset,'object placement differs')
    event_offset=blob.add('ring_events',events,4)
    struct.pack_into('<8sIIIIIIII',blob.data,0,b'VEGAR18N',1,len(blob.data),entry,script,
        BASE+offset+event_offset,MAP[0],MAP[1],npc['local_id'])
    payload=blob.finish(offset)
    need(len(payload)<=RESERVATION,'Ring payload exceeded reservation')
    return payload,dict(header=view['header'],old_events=view['events'],
        new_events=BASE+offset+event_offset,old_event_header=view['event_bytes'].hex(),
        old_objects=identity(view['raw_objects']),old_object_count=view['count'],
        new_object_count=view['count']+1,npc=npc,front=[xy[0],xy[1]+1],template_map=list(TEMPLATE_MAP),
        messages=messages,native_entry=entry,script_address=script,
        existing_objects_preserved=True,non_object_events_preserved=True,
        map_scripts_preserved=True)


def apply(raw, allocation, offset, payload, details):
    from scripts.pr16_bp_party_retention_successor import existing_requests, patch_bytes
    from tools.rom_allocator import build_allocation_report_from_csv
    need(identity(raw)==dict(size=SIZE,sha256=PARENT_SHA),'parent candidate identity differs')
    need(offset%4==0 and 0<len(payload)<=RESERVATION,'payload bounds differ')
    pointer_offset=details['header']+4-BASE
    edits=sorted([(pointer_offset,pointer_offset+4),(offset,offset+len(payload))])
    need(edits[0][1]<=edits[1][0],'Ring edits overlap')
    new=patch_bytes(raw,pointer_offset,struct.pack('<I',details['old_events']),struct.pack('<I',details['new_events']))
    new=patch_bytes(new,offset,b'\xff'*len(payload),payload)
    cursor=0
    for start,end in edits:
        need(new[cursor:start]==raw[cursor:start],'undeclared candidate edit')
        cursor=end
    need(new[cursor:]==raw[cursor:],'undeclared candidate suffix edit')
    requests=existing_requests(allocation)
    changed=[]
    for row,request in zip(allocation['allocations'],requests):
        start,end=row['start'],row['end_exclusive']
        need(identity(raw[start:end])['sha256']==row['content_sha256'],'parent allocation hash differs')
        if new[start:end]!=raw[start:end]:
            need(start<=pointer_offset and pointer_offset+4<=end,'unexpected existing allocation mutation')
            request['content_sha256']=identity(new[start:end])['sha256'];changed.append(row['name'])
    need(len(changed)<=1,'more than one map-root allocation changed')
    requests.append(dict(name=ALLOCATION,region='future_tail',start=offset,size=len(payload),alignment=4,
        owner=TASK,purpose='Safe Ring NPC; regular Bag grant; no policy or save-layout write',
        content_sha256=identity(payload)['sha256']))
    result=build_allocation_report_from_csv(ROOT/REGIONS,requests)
    need(result['summaries']['overlap_count']==0,'Ring allocation overlap')
    for row in result['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'output allocation hash differs')
    return new,result,changed


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    from scripts import pr16_bp_party_retention_successor as parent
    from scripts import pr16_capture_geometry as geometry
    from scripts.pr16_purchased_gear import path as walk_path
    import zlib
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe output path')
    OUT.mkdir(parents=True,exist_ok=True)
    verify_manifests()
    recipe=parent.run();raw=(parent.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==dict(size=SIZE,sha256=PARENT_SHA) and recipe['candidate']==identity(raw),'accepted parent differs')
    model=geometry.geometry(raw,*MAP)
    (OUT/'geometry-before.json').write_bytes(stable(model))
    # The town has fifteen existing templates. Add on its connected north
    # route instead, with no old conversation replacement or slot-limit change.
    candidates=[p for p in model['walkable_pairs'] if p['behavior']==0
        and p['end']==[p['start'][0],p['start'][1]+1]
        and model['height']-8 <= p['start'][1] <= model['height']-2
        and abs(p['start'][0]-model['width']//2)<=6]
    need(candidates,'no clear normal-ground giver/front pair on north route')
    candidates.sort(key=lambda p:(abs(p['start'][0]-13)+abs(p['start'][1]-38),p['start']))
    pair=candidates[0];xy=tuple(pair['start']);front=tuple(pair['end'])
    view=map_view(raw)
    template_view=map_view(raw,TEMPLATE_MAP)
    template=template_view['raw_objects'][template_view['ids'].index(2)*24:][:24]
    need(template[8] in (0,pair['elevation']),'reception/giver elevation mismatch')
    offset=choose_offset(recipe['allocation'])
    compilations=[compile_runtime(OUT/f'compile-{i}',BASE+offset+64) for i in (1,2)]
    need(compilations[0]==compilations[1],'independent gift compilations differ')
    code,entry=compilations[0]
    payload,details=make_payload(raw,offset,code,entry,xy,template)
    new,allocation,changed=apply(raw,recipe['allocation'],offset,payload,details)
    after=geometry.geometry(new,*MAP)
    # Keep the old shop/reception approach and north connection route available.
    paths=dict(to_south_connection=walk_path(after,front,(11,39)),
        to_grass=walk_path(after,front,(14,30)))
    need(map_view(new)['raw_objects'][:len(view['raw_objects'])]==view['raw_objects'],'old NPC bytes changed')
    candidate=identity(new)
    report=dict(schema_version=1,status='BUILT_RING_NPC_NOT_NATIVE_ACCEPTED',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ.get('GITHUB_RUN_ID','0')),parent=identity(raw),candidate=candidate,
        crc32=f'{zlib.crc32(new)&0xffffffff:08X}',allocation=allocation,payload_offset=offset,
        payload=identity(payload),map=details,map_key=list(MAP),paths=paths,existing_allocations_rehashed=changed,
        new_allocations=1,independent_gift_compiles=2,undeclared_changed_bytes=0,
        map_layout_changes=0,existing_object_changes=0,save_layout_changes=0,
        battle_policy_changes=0,accepted_native_cases_replayed=0,new_emulator_processes=0,
        ring_acquisition_accepted=False,ordinary_policy_accepted=False,release_ready=False,
        sources={p:identity((ROOT/p).read_bytes()) for p in (SELF,SOURCE,HEADER,REGIONS,
            'manifests/flags.csv','manifests/item_ids.csv',parent.SELF)})
    (OUT/'candidate.gba').write_bytes(new)
    (OUT/'candidate.json').write_bytes(stable(report))
    need((parent.OUT/'candidate.gba').read_bytes()==raw,'accepted parent mutated')
    print(json.dumps({k:report[k] for k in ('status','candidate','crc32','payload_offset','map','new_emulator_processes')},ensure_ascii=False))
    return report


if __name__=='__main__':
    run()
