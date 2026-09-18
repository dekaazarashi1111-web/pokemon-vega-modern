#!/usr/bin/env python3
"""固定Circus候補のplayer predicateだけを包む。原本ROM、旧Factory runtimeを不変にする。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from pr16_circus_identity import need,identity,stable,strict
SELF='scripts/pr16_circus_retention.py'
SOURCE='overlays/circus_retention/circus_retention.c'
TEST='tests/test_pr16_circus_retention.py'
WORKFLOW='.github/workflows/pr16-circus-retention.yml'
TASK='USER-20260919-CIRCUS-RETENTION'
OUT=ROOT/'.local/pr16-circus-retention-build'
PARENT=dict(size=33554432,sha256='99cc09484a9c6bd787fb4b0631970396b4ae5ec2abc902ea8fdec932130b6c0b')
BASE=0x08000000
LITERAL=0x012CFF2C
CONTINUATIONS=(0x09FF4D16,0x09FF4D77,0x09FF4DD8)
NAME='pr16_circus_party_retention_runtime'
RESERVATION=1024


def continuation_contract(recipe):
    rows=recipe['launch_sites']
    need(type(rows) is list and len(rows)==3,'three Circus launch sites required')
    need(all(type(r['new']) is int and r['size']==43 for r in rows),'launch size contract')
    result=tuple(r['new']+r['size'] for r in rows)
    need(result==CONTINUATIONS,'Circus continuations changed')
    return result


def bounded_patch(raw,literal,offset,payload,previous,entry):
    need(type(raw) is bytes and type(payload) is bytes and 32<=len(payload)<=RESERVATION,'immutable bounded runtime required')
    need(type(literal) is int and type(offset) is int and literal%4==offset%4==0,'aligned patch required')
    need(0<=literal<=len(raw)-4 and literal+4<=offset<=len(raw)-len(payload),'patch spans overlap/outside')
    need(type(previous) is int and type(entry) is int and previous&1 and entry&1 and previous!=entry,'distinct Thumb targets required')
    need(raw[literal:literal+4]==struct.pack('<I',previous),'trampoline preimage differs')
    need(raw[offset:offset+len(payload)]==b'\xff'*len(payload),'allocated runtime is not erased')
    out=bytearray(raw);out[literal:literal+4]=struct.pack('<I',entry);out[offset:offset+len(payload)]=payload
    need(out[:literal]==raw[:literal] and out[literal+4:offset]==raw[literal+4:offset] and out[offset+len(payload):]==raw[offset+len(payload):],'undeclared ROM change')
    rollback=bytearray(out);rollback[literal:literal+4]=raw[literal:literal+4];rollback[offset:offset+len(payload)]=b'\xff'*len(payload)
    need(bytes(rollback)==raw,'whole-ROM rollback mismatch')
    return bytes(out)


def compile_runtime(folder,offset,previous,scripts):
    need(not any(p.is_symlink() for p in (folder,*folder.parents)),'unsafe compile output')
    folder.mkdir(parents=True,exist_ok=True);address=BASE+offset
    linker=folder/'runtime.ld'
    linker.write_text('ENTRY(VegaCircusRandomPlayerParty)\n'+f'SECTIONS {{ . = 0x{address:08x}; .text : {{ KEEP(*(.text.entry)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }} }}\n')
    elf=folder/'runtime.elf';binary=folder/'runtime.bin'
    defines=[f'-DCIRCUS_PREVIOUS_PREDICATE=0x{previous:08x}u']
    defines.extend(f'-DCIRCUS_SCRIPT_{name}=0x{value:08x}u' for name,value in zip(('FIRST','SECOND','THIRD'),scripts))
    command=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
        '-Wall','-Wextra','-Werror','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none','-T',str(linker),*defines,str(ROOT/SOURCE),'-o',str(elf)]
    subprocess.run(command,check=True,capture_output=True)
    symbols=subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True)
    entries=[int(line.split()[0],16) for line in symbols.splitlines() if line.split()[-1:]==['VegaCircusRandomPlayerParty']]
    need(len(entries)==1 and entries[0]&~1==address,'entry/link placement differs')
    need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)])==b'','unresolved runtime symbol')
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes();need(32<=len(payload)<=RESERVATION,'runtime size bound')
    disasm=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True).replace(str(elf),'circus-retention.elf')
    (folder/'symbols.txt').write_text(symbols);(folder/'disassembly.txt').write_text(disasm)
    return payload


def run():
    import pr16_circus_entry as parent
    import pr16_bp_party_retention_successor as old
    import pr16_ring_npc_successor as gift
    from tools.rom_allocator import build_allocation_report_from_csv
    from pr16_circus_thumb_record import validate_build
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe build output');OUT.mkdir(parents=True,exist_ok=True)
    raw=(parent.OUT/'candidate.gba').read_bytes();recipe=strict((parent.OUT/'report.json').read_bytes())
    need(identity(raw)==PARENT and recipe['candidate']==PARENT,'fixed parent differs')
    thumb=strict((ROOT/'content/modernization/pr16_circus_thumb_checkpoint.json').read_bytes());validate_build(recipe,thumb['proof'])
    for name in ('scripts/pr16_circus_entry.py','scripts/pr16_circus_thumb.py'):
        need(identity((ROOT/name).read_bytes())==thumb['source_bindings'][name],'saved parent source changed')
    scripts=continuation_contract(recipe)
    for script in scripts:need(raw[script-BASE-1]==0x5d,'native battle opcode changed')
    need(old.decode_thumb_bl(old.CALLSITE,raw[old.CALLSITE_OFFSET:old.CALLSITE_OFFSET+4])==old.TRAMPOLINE_ADDRESS,'existing predicate callsite changed')
    rows=recipe['allocation']['allocations'];previous_rows=[r for r in rows if r['name']=='pr16_factory_party_retention_runtime']
    need(len(previous_rows)==1,'old Factory runtime allocation absent')
    previous=struct.unpack_from('<I',raw,LITERAL)[0]
    need(previous==(previous_rows[0]['gba_start']|1) and raw[LITERAL-4:LITERAL]==bytes.fromhex('004b1847'),'old Thumb tail jump differs')
    requests=old.existing_requests(recipe['allocation'])
    req=dict(name=NAME,region='future_tail',size=RESERVATION,alignment=4,owner=TASK,
        purpose='Circus-only read-only party predicate; previous Factory predicate retained',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req])
    offset=next(r['start'] for r in preview['allocations'] if r['name']==NAME)
    payloads=[compile_runtime(OUT/f'compile-{i}',offset,previous,scripts) for i in (1,2)]
    need(payloads[0]==payloads[1],'independent ARM links differ');payload=payloads[0];entry=BASE+offset+1
    left=bounded_patch(raw,LITERAL,offset,payload,previous,entry);right=bounded_patch(raw,LITERAL,offset,payloads[1],previous,entry)
    need(left==right,'independent bounded builds differ')
    changed=[]
    for row,request in zip(rows,requests):
        a,b=row['start'],row['end_exclusive'];need(identity(raw[a:b])['sha256']==row['content_sha256'],'parent allocation hash differs')
        if raw[a:b]!=left[a:b]:
            need(row['name']=='pr16_factory_party_retention_trampoline' and a<=LITERAL and LITERAL+4<=b,'unexpected existing owner changed')
            request['content_sha256']=identity(left[a:b])['sha256'];changed.append(row['name'])
    need(changed==['pr16_factory_party_retention_trampoline'],'exactly one literal owner required')
    req.update(start=offset,size=len(payload),content_sha256=identity(payload)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req]);need(allocation['summaries']['overlap_count']==0,'allocation overlap')
    for row in allocation['allocations']:need(identity(left[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'output allocation hash differs')
    proof=dict(parent=PARENT,literal_offset=LITERAL,previous_entry=previous,new_entry=entry,payload_offset=offset,payload=identity(payload),
        declared_spans=[[LITERAL,LITERAL+4],[offset,offset+len(payload)]],whole_rom_rollback_matches_parent=True,
        previous_factory_runtime_unchanged=True,previous_predicate_called_once=True,non_circus_original_return_preserved=True,
        host_ram_writes=0,script_continuations=list(scripts),newly_overridden_cases='Circus number3/valid active rental/three exact script-pending pairs only',
        inherited_prefix_cases=['circus-cancel-save-continue','factory-fallback-cancel'],accepted_native_cases_replayed=0)
    sources=(SELF,SOURCE,TEST,WORKFLOW,old.SELF,parent.SELF,'overlays/save_migration/save_migration.h',gift.REGIONS)
    report=dict(schema_version=1,status='BUILT_CIRCUS_RETENTION_NATIVE_OPEN',task=TASK,source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ.get('GITHUB_RUN_ID','0')),parent=PARENT,candidate=identity(left),parent_recipe=recipe,
        entries=recipe['entries'],launch_sites=recipe['launch_sites'],allocation=allocation,proof=proof,
        independent_new_runtime_links=2,independent_bounded_builds=2,sources={n:identity((ROOT/n).read_bytes()) for n in sources},
        new_emulator_processes=0,accepted_native_cases_replayed=0,rental_identity_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    (OUT/'candidate.gba').write_bytes(left);(OUT/'report.json').write_bytes(stable(report))
    need((parent.OUT/'candidate.gba').read_bytes()==raw,'parent candidate mutated')
    print(json.dumps({k:report[k] for k in ('status','candidate','proof')},ensure_ascii=False));return report

if __name__=='__main__':run()
