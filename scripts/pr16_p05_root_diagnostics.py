#!/usr/bin/env python3
"""Read reachable P05 candidates despite unrelated invalid roots, with limits.

This is not native admission/acquisition acceptance. Invalid roots, map records
and encounter tables remain explicit; no resynchronization or hidden fallback.
"""
from pathlib import Path
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'));sys.path.insert(0, str(ROOT))
import pr16_receiver_audit as audit
from tools.t02.rom_inventory import RomImage, MAP_GROUPS_POINTER_SITE
need = audit.repaired.need
TARGETS = {503, 411, 957, 497, 787, 1526}
ITEMS = {580, 1016, 1012, 1031, 1029, 1014, 1035}


def map_entry(rom, group, number):
    table = rom.u32(MAP_GROUPS_POINTER_SITE)
    group_table = rom.u32(table + group*4)
    header = rom.u32(group_table + number*4)
    layout = rom.u32(header)
    events = rom.u32(header+4)
    out = {'group': group, 'map': number, 'header': header, 'layout': layout,
           'width': rom.s32(layout), 'height': rom.s32(layout+4), 'events': events,
           'objects': [], 'warps': [], 'coords': [], 'bgs': []}
    if not events or rom.raw(events,4) == b'\xff'*4:
        return out
    counts = list(rom.raw(events,4)); pointers = [rom.u32(events+4+4*i) for i in range(4)]
    for i in range(counts[0]):
        at = pointers[0]+24*i
        out['objects'].append({'index': i, 'local_id': rom.u8(at), 'graphics_id': rom.u8(at+1),
          'kind': rom.u8(at+2), 'x': rom.s16(at+4), 'y': rom.s16(at+6),
          'movement': rom.u8(at+9), 'script': rom.u32(at+16), 'flag': rom.u16(at+20)})
    for i in range(counts[1]):
        at = pointers[1]+8*i
        out['warps'].append({'index':i,'x':rom.s16(at),'y':rom.s16(at+2),'elevation':rom.u8(at+4),
                            'target_warp':rom.u8(at+5),'target_map':rom.u8(at+6),'target_group':rom.u8(at+7)})
    for i in range(counts[2]):
        at = pointers[2]+16*i
        out['coords'].append({'index':i,'x':rom.u16(at),'y':rom.u16(at+2),'variable':rom.u16(at+6),
                             'value':rom.u16(at+8),'script':rom.u32(at+12)})
    for i in range(counts[3]):
        at = pointers[3]+12*i
        out['bgs'].append({'index':i,'x':rom.u16(at),'y':rom.u16(at+2),'kind':rom.u8(at+5),'script_or_item':rom.u32(at+8)})
    return out


def rooted_graph(rom, roots):
    walker = audit.ReceiverWalker(rom); invalid = []
    for root in roots:
        if not rom.contains(root.address):
            invalid.append({'address':root.address,'label':root.label,'kind':root.kind})
        else:
            walker.add_root(root)
    graph = walker.walk()
    graph['invalid_roots'] = invalid
    graph['all_roots_decoded'] = not invalid and not graph['diagnostics']
    return graph


def rooted_receivers(raw):
    rom = RomImage('fixed repaired candidate',raw)
    roots, counts = audit._collect_contactable_roots(rom)
    graph = rooted_graph(rom,roots)
    selected = [r for r in graph['references'] if
      r['category']=='var' and r['value']==0x403A or
      r['category']=='special' and r['value']==0x72 or
      r['category']=='native' or r['category']=='item' and r['value'] in ITEMS]
    labels = sorted({label for r in selected for label in r['roots']})
    maps = sorted({tuple(map(int,label.split(':')[1:3])) for label in labels})
    metadata = []
    for group, number in maps:
        try:
            metadata.append(map_entry(rom, group, number))
        except ValueError as error:
            metadata.append({'group':group,'map':number,'error':str(error)})
    addresses = {r['script_address'] for r in selected}
    return {'status':'ROOTED_CANDIDATES_NOT_NATIVE_ACCEPTANCE','root_counts':dict(counts),
       'supplied_roots':len(roots),'decoded_roots':graph['root_count'],'visited_scripts':graph['visited_script_count'],
       'invalid_roots':graph['invalid_roots'],'diagnostics':graph['diagnostics'],
       'all_roots_decoded':graph['all_roots_decoded'],'references':selected,'maps':metadata,
       'nodes':[n for n in graph['nodes'] if n['address'] in addresses],
       'no_match_proves_absence':False,'physical_admission_accepted':False}


def wild_catalogue(raw, count=265):
    """Stage57 native-header catalogue count is a bound, not silent termination."""
    rom = RomImage('fixed candidate',raw); root = rom.u32(0x0808257C)&~1
    rows=[];diagnostics=[];matches=[];owners=set()
    for i in range(count):
        at=root+20*i
        if not rom.contains(at,20):
            diagnostics.append({'header':i,'error':'header outside ROM'});break
        group,number=rom.u8(at),rom.u8(at+1)
        row={'header':i,'group':group,'map':number,'tables':{},'first_coordinate_owner':(group,number) not in owners}
        owners.add((group,number))
        for j,(method,slots_count) in enumerate((('land',12),('water',5),('rock',5),('fishing',10))):
            info=rom.u32(at+4+4*j)&~1
            if not info:continue
            try:
                need(rom.contains(info,8),'info pointer outside ROM')
                slots=rom.u32(info+4)&~1;need(rom.contains(slots,4*slots_count),'slots pointer outside ROM')
                rate=rom.u8(info);need(1<=rate<=100,'invalid rate')
                values=[]
                for k in range(slots_count):
                    low,high,species=struct.unpack('<BBH',rom.raw(slots+4*k,4))
                    need(1<=low<=high<=100 and 1<=species<=1670,'invalid level/species slot')
                    values.append({'min':low,'max':high,'species':species})
                row['tables'][method]={'rate':rate,'slots':values}
                for k,slot in enumerate(values):
                    if slot['species'] in TARGETS:
                        matches.append({'header':i,'group':group,'map':number,'method':method,'slot':k,**slot,
                                        'first_coordinate_owner':row['first_coordinate_owner']})
            except ValueError as error:
                detail={'header':i,'group':group,'map':number,'method':method,'info':info,'error':str(error)}
                diagnostics.append(detail);row['tables'][method]={'status':'INVALID','error':str(error)}
        rows.append(row)
    return {'root':root,'expected_legacy_header_count':count,'inspected_headers':len(rows),
            'complete_valid_catalogue':len(rows)==count and not diagnostics,'diagnostics':diagnostics,
            'headers':rows,'target_candidates':matches,'natural_acquisition_accepted':False}


def inherited_sites(raw):
    rom=RomImage('provenance',raw);root=rom.u32(0x0808257C)&~1
    maps=[]
    for group,number in ((12,7),):
        try:maps.append(map_entry(rom,group,number))
        except ValueError as error:maps.append({'group':group,'map':number,'error':str(error)})
    return {'wild_root':root,'wild_header_139':list(struct.unpack('<BBH4I',rom.raw(root+139*20,20))),
            'wild_header_region_265':audit.repaired.identity(rom.raw(root,265*20)),
            'map_records':maps}


def provenance(raw):
    from tools import modernization_p03_native_pp_repair as stage80
    import modernization_final_integration as stage84
    baseline=json.loads((ROOT/'config/active_play_baseline.json').read_bytes())['rom']
    rows={}
    for label,path,sha in (('stage62',baseline['path'],baseline['sha256']),
                          ('stage80',stage80.PARENT_PATH,stage80.PARENT_SHA),
                          ('stage84',stage84.ROM,stage84.SHA)):
        try:
            parent=audit.repaired.layer.source.checked(ROOT/path,sha)
            rows[label]={'identity':audit.repaired.identity(parent),'sites':inherited_sites(parent)}
        except (OSError,ValueError) as error:
            rows[label]={'status':'UNAVAILABLE','error':str(error)}
    rows['candidate']={'identity':audit.repaired.identity(raw),'sites':inherited_sites(raw)}
    return rows


def run():
    out=ROOT/'.local/pr16-receiver-audit';out.mkdir(parents=True,exist_ok=True)
    raw=audit.repaired.layer.source.checked(ROOT/audit.repaired.ROM,audit.repaired.ROM_SHA)
    inputs=audit.restore_map_inputs()
    value={'status':'STATIC_PARTIAL_DIAGNOSTICS_NOT_NATIVE_ACCEPTANCE','candidate':audit.repaired.identity(raw),
           'catalogue_archive':inputs['archive'],'roots':rooted_receivers(raw),'wild':wild_catalogue(raw),
           'pointer_provenance':provenance(raw),'rom_changed':False,'new_emulator_runs':0,'release_ready':False}
    (out/'p05-roots.json').write_bytes(audit.repaired.stable(value))
    audit.repaired.layer.source.checked(ROOT/audit.repaired.ROM,audit.repaired.ROM_SHA)
    print(json.dumps({'status':value['status'],'roots':value['roots']['decoded_roots'],
        'invalid_roots':len(value['roots']['invalid_roots']),'graph_diagnostics':len(value['roots']['diagnostics']),
        'wild_diagnostics':len(value['wild']['diagnostics']),'new_emulator_runs':0,'release_ready':False}))

if __name__=='__main__':run()
