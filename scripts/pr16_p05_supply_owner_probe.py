#!/usr/bin/env python3
"""Bounded exact-ROM supply-owner audit, never native acceptance.

Unlike the old item-only inventory, retain work-variable item operands (native
`giveitem` macros use those), native/std calls, event-header bytes and unknown
opcode predecessors. Do not change the shared decoder or resynchronize it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SHA = 'e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'
OUT = ROOT / '.local/pr16-p05-supply-owner'
SELF = 'scripts/pr16_p05_supply_owner_probe.py'
TOKENS = re.compile(r'MEGA_?RING|BATTLE_?CIRCUS|CircusFlags|ScriptCmdTable|ScrCmd_[A-Za-z]*(?:battle|item)|VegaConfigureNext(?:BattlePolicy|Facility)|0x0203DFBC', re.I)
UPSTREAM_SUFFIXES = {'.c', '.h', '.s', '.inc', '.asm', '.ld', '.tbl'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def ring_reference(row):
    """Candidate only: work-variable assignment alone does not prove a giver."""
    if row['category'] == 'item' and row['value'] == 580:
        return True
    return (row['category'] == 'var' and row.get('operand') == 580
            and row['opcode'] in (0x16, 0x19, 0x1A, 0x21))


def header_record(rom, group, number):
    from tools.t02.rom_inventory import MAP_GROUPS_POINTER_SITE
    table = rom.u32(MAP_GROUPS_POINTER_SITE)
    header = rom.u32(rom.u32(table + 4*group) + 4*number)
    layout, events = rom.u32(header), rom.u32(header+4)
    record = dict(group=group, map=number, header=header, layout=layout,
                  dimensions=[rom.s32(layout), rom.s32(layout+4)], events=events,
                  header_hex=rom.raw(header, 28).hex(), arrays=[], diagnostics=[])
    if not events:
        record['empty_events'] = True
        return record
    data = rom.raw(events, 20)
    record['events_hex'] = data.hex()
    counts = list(data[:4]); pointers = list(struct.unpack('<4I', data[4:]))
    record['counts'] = counts; record['pointers'] = pointers
    for kind, count, pointer, stride in zip(('objects','warps','coords','bgs'), counts, pointers, (24,8,16,12)):
        row = dict(kind=kind, count=count, pointer=pointer, stride=stride, entries=[])
        row['full_region_in_rom'] = count == 0 or rom.contains(pointer, count*stride)
        if count and not row['full_region_in_rom']:
            record['diagnostics'].append(dict(kind=kind, reason='array_outside_rom'))
        elif count:
            shown = min(count, 12)
            row['entries'] = [rom.raw(pointer+i*stride, stride).hex() for i in range(shown)]
            row['entries_omitted'] = count-shown
            row['region_identity'] = identity(rom.raw(pointer, count*stride))
        record['arrays'].append(row)
    record['physical_entrance_identified'] = False
    return record


def collect_sources(archive, output):
    config = json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    bound = next(r for r in config['archives'] if r['name'] == 'pokemon-vega-private-env-v1-state.zip')
    need(identity(archive.read_bytes()) == {k:bound[k] for k in ('size','sha256')}, 'state archive identity differs')
    payload, rows = {}, []
    with zipfile.ZipFile(archive) as z:
        need(len(z.namelist()) == len(set(z.namelist())), 'duplicate state archive members')
        for info in z.infolist():
            name = info.filename; path = PurePosixPath(name)
            if not name.startswith('vendor/upstream/CFRU-JP/') or path.suffix.lower() not in UPSTREAM_SUFFIXES:
                continue
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in name, 'unsafe source path')
            need(not stat.S_ISLNK(info.external_attr >> 16) and info.file_size <= 4_000_000, 'unsafe source member')
            raw = z.read(info); text = raw.decode('utf-8-sig')
            need(b'\0' not in raw, 'nontext source')
            hits = [dict(line=i, text=line) for i,line in enumerate(text.splitlines(),1) if TOKENS.search(line)]
            if not hits:
                continue
            payload[name] = raw
            rows.append(dict(path=name, origin='PINNED_STATE_SOURCE', **identity(raw), matches=hits))
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    selected = {
        SELF, 'tests/test_pr16_p05_supply_owner_probe.py', '.github/workflows/pr16-p05-supply-owner.yml',
        'scripts/pr16_receiver_audit.py', 'scripts/pr16_p05_root_diagnostics.py',
        'tools/t02/rom_inventory.py', 'tools/stage57_debug_suite.py',
        'content/collection_supply_v1/canonical_model.json', 'config/github_private_environment.json',
        'config/modernization_p05_stage77_suppression.json', 'config/modernization_p05_stage78_suppression.json',
        'content/modernization/p08_remaining_work.json', 'config/active_play_baseline.json',
        'scripts/build_facility_runtime.py','scripts/build_factory_reward_runtime.py',
        'scripts/build_factory_repeat_reward_runtime.py','scripts/build_bp_shop_runtime.py',
        'scripts/build_collection_supply_v1.py','scripts/pr16_apply_gear_policy_boundary.py',
        'overlays/cfru/rom_bridge.c', 'overlays/cfru/cfru_integration.c',
    }
    prefixes = ('overlays/facility_runtime/', 'overlays/factory_reward_runtime/', 'overlays/factory_repeat_reward_runtime/',
                'overlays/trainer_changekit_final_runtime/', 'overlays/collection_supply_v1/', 'overlays/bp_shop_runtime/')
    for name in tracked:
        path = ROOT/name
        if name not in selected and not name.startswith(prefixes):
            continue
        if path.suffix.lower() not in UPSTREAM_SUFFIXES | {'.py','.json','.yml'}:
            continue
        raw = path.read_bytes(); text = raw.decode('utf-8')
        need(not path.is_symlink() and len(raw)<4_000_000 and b'\0' not in raw, 'unsafe tracked source')
        payload[name] = raw
        rows.append(dict(path=name, origin='TRACKED_CHECKOUT', **identity(raw), matches=[dict(line=i,text=line) for i,line in enumerate(text.splitlines(),1) if TOKENS.search(line)]))
    need(len(payload)<=160 and sum(map(len,payload.values()))<=24_000_000, 'source snapshot exceeds bound')
    with zipfile.ZipFile(output/'owner-sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(payload.items()):
            z.writestr(name,raw)
    return dict(archive={k:bound[k] for k in ('name','size','sha256')}, sources=rows,
                source_zip=identity((output/'owner-sources.zip').read_bytes()))


def inspect(raw):
    need(identity(raw)==dict(size=33554432,sha256=SHA),'exact current shop successor required')
    sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
    import pr16_receiver_audit as audit
    from tools.t02.rom_inventory import COMMAND_LENGTHS, RomImage, _trainerbattle_size
    from tools.stage57_debug_suite import _collect_contactable_roots
    rom=RomImage('P05 ordinary supply owner exact candidate',raw)
    roots,counts=_collect_contactable_roots(rom); walker=audit.ReceiverWalker(rom)
    invalid=[]
    for root in roots:
        if rom.contains(root.address):walker.add_root(root)
        else:invalid.append(dict(address=root.address,label=root.label,kind=root.kind))
    graph=walker.walk()
    ring=[r for r in graph['references'] if ring_reference(r)]
    # Include known real service and original Ring-removal roots, not only
    # diagnostic helper scripts that happen to mention ITEM_MEGA_RING.
    wanted={'map:96:5:object:1','map:98:69:object:1'}
    wanted.update(label for r in ring for label in r['roots'])
    interesting={n['address'] for n in graph['nodes'] if set(n['roots'])&wanted}
    interesting.update(r['script_address'] for r in ring)
    for d in graph['diagnostics']:
        candidates=[n['address'] for n in graph['nodes'] if n['end_reason']=='unknown_opcode' and n['address']<=d.get('address',0)]
        if candidates:interesting.add(max(candidates))
    nodes=[]
    for n in graph['nodes']:
        if n['address'] not in interesting:continue
        pc=n['address']; trace=[]
        need(n['instruction_count']<=walker.MAX_INSTRUCTIONS_PER_NODE,'instruction bound changed')
        for _ in range(n['instruction_count']):
            op=rom.u8(pc);size=_trainerbattle_size(rom.u8(pc+1)) if op==0x5C else COMMAND_LENGTHS[op]
            trace.append(dict(address=pc,opcode=op,size=size,bytes=rom.raw(pc,size).hex()))
            pc+=size
        nodes.append(dict(n,instructions=trace,stopped_at=pc,stop_window=rom.raw(pc,min(24,rom.end-pc)).hex()))
    need(len(nodes)<=400 and sum(len(n['instructions']) for n in nodes)<=12000,'selected graph exceeds diagnostic bound')
    coords={(12,6),(12,7),(96,5),(98,69)}
    coords.update(tuple(map(int,label.split(':')[1:3])) for label in wanted)
    maps=[]
    for group,number in sorted(coords):
        try:maps.append(header_record(rom,group,number))
        except ValueError as error:maps.append(dict(group=group,map=number,error=str(error)))
    # Report readonly predicate and script links. These are NOT runtime writes.
    return dict(schema_version=1,status='STATIC_SUPPLY_OWNER_CANDIDATES_NOT_NATIVE_ACCEPTANCE',candidate=identity(raw),
        root_counts=dict(counts),supplied_roots=len(roots),decoded_roots=graph['root_count'],visited_scripts=graph['visited_script_count'],
        invalid_roots=invalid,diagnostics=graph['diagnostics'],ring_operand_candidates=ring,
        selected_roots=sorted(wanted),selected_script_nodes=nodes,map_headers=maps,
        references=[r for r in graph['references'] if r['script_address'] in interesting],
        circus_suppression_predicate=dict(battle_type_flags_address=0x02022AAC,battle_type_required=0x04000000,
            circus_flags_address=0x0203DFBC,circus_required=0x80000000,source='config/modernization_p05_stage77_suppression.json'),
        no_match_proves_absence=False,decoder_changed=False,new_emulator_runs=0,rom_changes=0,
        physical_ring_accepted=False,physical_bp_accepted=False,physical_policy_accepted=False,physical_circus_admission_accepted=False,
        release_ready=False)


def run(archive, output):
    archive=archive.absolute();output=output.absolute()
    need(output.is_relative_to(ROOT/'.local') and output!=ROOT/'.local','output not dedicated local directory')
    need(not any(p.is_symlink() for p in (archive,*archive.parents,output,*output.parents)),'symlink input/output')
    output.mkdir(parents=True,exist_ok=True)
    source=collect_sources(archive,output)
    source['tested_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (output/'owner-index.json').write_bytes(stable(source))
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_receiver_audit as audit
    import pr16_shop_display_repair as repair
    inputs=audit.restore_map_inputs()
    recipe=repair.run()
    raw=(repair.OUTPUT/'candidate.gba').read_bytes()
    report=inspect(raw)
    report['tested_head']=source['tested_head'];report['map_catalogue_archive']=inputs['archive']
    (output/'supply-owner.json').write_bytes(stable(report))
    (output/'candidate.json').write_bytes(stable(recipe))
    need(identity((repair.OUTPUT/'candidate.gba').read_bytes())==report['candidate'],'candidate changed during audit')
    print(json.dumps(dict(status=report['status'],ring_candidates=len(report['ring_operand_candidates']),
          invalid_roots=len(report['invalid_roots']),diagnostics=len(report['diagnostics']),new_emulator_runs=0,release_ready=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();run(args.archive,args.output)
