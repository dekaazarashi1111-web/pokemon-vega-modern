#!/usr/bin/env python3
"""受入済みNPC候補へ通常戦闘Ring bridgeを限定追加。native受入とは分離する。"""
from __future__ import annotations
import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_ring_policy_successor.py'
SOURCE='overlays/ring_policy/ring_policy.c'
HEADER='overlays/ring_policy/ring_policy.h'
OUT=ROOT/'.local/pr16-ring-policy-successor'
PARENT_SHA='72fbca91cd6ee1082198678ccaed76bcb76dfd19ce9f6f3c26309745b2f09ac0'
BASE,SIZE=0x08000000,33554432
BEGIN,END=0x091266F4,0x09126960
BEGIN_SHA='7c823c35f5273a25ba97b51752b6216671f1a074f64e4384a88acf08d7f234b7'
PROLOGUE=bytes.fromhex('f0b545464e46de46')
TASK='USER-20260918-RING-POLICY'
ALLOCATION='pr16_ring_ordinary_policy_runtime'
RESERVATION=1024
# run35341496620: 固定親の実BLとcallee先頭を原本から照合済み。
OWNERS={
 'VEGA_RING_STATE_GETTER':(0x09126702,0x0910E990,'034b1868ab23db009c4660447047c046b0df0302'),
 'VEGA_RING_SELECT_MECHANIC':(0x091268CA,0x0910EFA4,'b12230b5104c2368d2009a5c83b0002a17d00e4d'),
 'VEGA_RING_END_BATTLE':(0x091267CA,0x0910F36C,'b12370b52e4e05003068db00c35c002b02d00024'),
}


def need(ok,message):
    if not ok: raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def jump(address):
    need(type(address) is int and BASE<=address<BASE+SIZE and address&1,'invalid Thumb jump target')
    return struct.pack('<HHI',0x4B00,0x4718,address)


def trampoline(raw):
    need(type(raw) is bytes and len(raw)==8 and raw==PROLOGUE,'unapproved displaced prologue')
    # 4つのPC非依存命令のみ移設。r3は元のvoid関数でも読取前に定義される。
    # r4-r7/LRとr8/r9/fpの保存順、元のstack alignmentを変えない。
    return raw+jump((BEGIN+8)|1)


def decode_bl(address,raw):
    need(len(raw)==4,'invalid BL size')
    a,b=struct.unpack('<HH',raw)
    need(a&0xF800==0xF000 and b&0xF800==0xF800,'not a Thumb BL')
    value=((a&0x7FF)<<12)|((b&0x7FF)<<1)
    if value&0x400000:value-=0x800000
    return address+4+value


def verify_owners(raw):
    need(identity(raw)==dict(size=SIZE,sha256=PARENT_SHA),'accepted NPC parent differs')
    need(identity(raw[BEGIN-BASE:END-BASE])['sha256']==BEGIN_SHA,'ordinary begin changed')
    need(raw[BEGIN-BASE:BEGIN-BASE+8]==PROLOGUE,'ordinary entry ABI changed')
    for name,(call,target,prefix) in OWNERS.items():
        need(decode_bl(call,raw[call-BASE:call-BASE+4])==target,'owner call differs: '+name)
        bound=bytes.fromhex(prefix)
        need(raw[target-BASE:target-BASE+len(bound)]==bound,'owner bytes differ: '+name)
    return {name:target|1 for name,(_,target,_) in OWNERS.items()}


def reserved_owner(regions,allocation):
    rows=[r for r in regions if r['name']=='cfru_payload']
    need(len(rows)==1,'reserved CFRU owner missing or duplicated')
    row=rows[0]
    need(row['kind']=='reserved' and row['owner']=='CFRU-JP'
         and int(row['start'],0)==0x01000000 and int(row['end_exclusive'],0)==0x01200000,
         'reserved CFRU envelope differs')
    need(int(row['start'],0)<=BEGIN-BASE<END-BASE<=int(row['end_exclusive'],0),
         'original policy is outside reserved CFRU envelope')
    need(all(r['end_exclusive']<=BEGIN-BASE or r['start']>=END-BASE
             for r in allocation['allocations']),'allocator overlaps reserved policy owner')
    return dict(region=row['name'],owner=row['owner'],kind=row['kind'],
                patch_start=BEGIN-BASE,patch_size=8)


def compile_runtime(out,load,original,owners):
    out.mkdir(parents=True,exist_ok=True)
    linker=out/'policy.ld'
    linker.write_text('ENTRY(VegaRingPolicyBegin)\nSECTIONS { . = '+hex(load)+'; '
        '.text : { KEEP(*(.text.VegaRingPolicyBegin)) *(.text*) *(.rodata*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n')
    elf=out/'policy.elf'
    defines=dict(owners,VEGA_RING_ORIGINAL_BEGIN=original|1)
    command=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi',
        '-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections',
        '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror',
        '-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
        *['-D'+key+'='+hex(value)+'u' for key,value in sorted(defines.items())],
        '-T',str(linker),str(ROOT/SOURCE),'-o',str(elf)]
    proc=subprocess.run(command,capture_output=True)
    (out/'compiler.stdout').write_bytes(proc.stdout);(out/'compiler.stderr').write_bytes(proc.stderr)
    need(proc.returncode==0,'Ring policy ARM compilation failed')
    symbols=subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True)
    (out/'symbols.txt').write_text(symbols)
    entries=[int(line.split()[0],16) for line in symbols.splitlines() if line.split()[-1:]==['VegaRingPolicyBegin']]
    need(len(entries)==1 and entries[0]&~1==load,'policy entry placement differs')
    binary=out/'policy.bin'
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes();need(32<=len(payload)<=768,'policy code size outside contract')
    dis=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True)
    (out/'disassembly.txt').write_text(dis.replace(str(elf),'ring-policy.elf'))
    return payload,entries[0]|1


def patch(raw,offset,payload,entry):
    need(len(raw)==SIZE and offset%4==0 and 0<len(payload)<=RESERVATION,'invalid policy patch bounds')
    need(0<=offset<=SIZE-len(payload) and offset>END-BASE,'policy payload overlaps existing begin')
    need(raw[offset:offset+len(payload)]==b'\xff'*len(payload),'policy allocation is not empty')
    need(raw[BEGIN-BASE:BEGIN-BASE+8]==PROLOGUE,'entry already changed')
    need(BASE+offset<=entry&~1<BASE+offset+len(payload),'entry outside payload')
    new=bytearray(raw);new[BEGIN-BASE:BEGIN-BASE+8]=jump(entry);new[offset:offset+len(payload)]=payload
    cursor=0
    for start,end in ((BEGIN-BASE,BEGIN-BASE+8),(offset,offset+len(payload))):
        need(new[cursor:start]==raw[cursor:start],'undeclared policy edit')
        cursor=end
    need(new[cursor:]==raw[cursor:],'undeclared policy suffix edit')
    return bytes(new)


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_ring_npc_successor as gift
    from scripts.pr16_bp_party_retention_successor import existing_requests
    from tools.rom_allocator import build_allocation_report_from_csv
    OUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe policy output')
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_ring_policy_build.py','-v'],cwd=ROOT,capture_output=True)
    (OUT/'builder-tests.stdout').write_bytes(test.stdout);(OUT/'builder-tests.stderr').write_bytes(test.stderr)
    need(test.returncode==0,'policy builder contracts failed')
    prior=json.loads((ROOT/'content/modernization/pr16_ring_npc_gift_checkpoint_20260918.json').read_bytes())
    for source in (gift.SELF,gift.SOURCE,gift.HEADER,'tools/mgba_pr16_ring_npc.c'):
        need(identity((ROOT/source).read_bytes())==prior['source_bindings'][source],'accepted gift owner changed')
    recipe=gift.run();raw=(gift.OUT/'candidate.gba').read_bytes();owners=verify_owners(raw)
    need(recipe['candidate']==identity(raw),'gift recipe differs')
    with (ROOT/gift.REGIONS).open(encoding='utf-8',newline='') as f:
        region=reserved_owner(list(csv.DictReader(f)),recipe['allocation'])
    requests=existing_requests(recipe['allocation'])
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[dict(name=ALLOCATION,
        region='future_tail',size=RESERVATION,alignment=4,owner=TASK,purpose='ordinary Ring policy preview',content_sha256='0'*64)])
    rows=[row for row in preview['allocations'] if row['name']==ALLOCATION]
    need(len(rows)==1,'policy allocation missing')
    offset=rows[0]['start'];original=BASE+offset+32;load=BASE+offset+48
    first,entry=compile_runtime(OUT/'compile-1',load,original,owners)
    second,entry2=compile_runtime(OUT/'compile-2',load,original,owners)
    need(first==second and entry==entry2,'independent policy ARM builds differ')
    payload=struct.pack('<8sIIIIII',b'VEGAR18P',1,48+len(first),BEGIN,original|1,entry,0)
    payload+=trampoline(raw[BEGIN-BASE:BEGIN-BASE+8])+first
    new=patch(raw,offset,payload,entry);changed=[]
    for row,request in zip(recipe['allocation']['allocations'],requests):
        start,end=row['start'],row['end_exclusive']
        need(identity(raw[start:end])['sha256']==row['content_sha256'],'parent allocation digest differs')
        if raw[start:end]!=new[start:end]:
            need(start<=BEGIN-BASE and BEGIN-BASE+8<=end,'unexpected existing allocation change')
            request['content_sha256']=identity(new[start:end])['sha256'];changed.append(row['name'])
    need(changed==[],'reserved CFRU entry must not change allocator-owned payloads')
    requests.append(dict(name=ALLOCATION,region='future_tail',start=offset,size=len(payload),alignment=4,
        owner=TASK,purpose='Ring ordinary begin bridge; no NPC/save/UI replacement',content_sha256=identity(payload)['sha256']))
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests)
    need(allocation['summaries']['overlap_count']==0,'policy allocation overlap')
    for row in allocation['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'candidate allocation digest differs')
    sources=(SELF,SOURCE,HEADER,'overlays/cfru/rom_bridge.c','overlays/cfru/integration.c',
             'overlays/cfru/integration.h','overlays/cfru/runtime.h','scripts/build_battle_core.py')
    report=dict(schema_version=2,status='BUILT_RING_POLICY_NOT_NATIVE_ACCEPTED',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ.get('GITHUB_RUN_ID','0')),parent=identity(raw),candidate=identity(new),
        crc32=f'{zlib.crc32(new)&0xffffffff:08X}',allocation=allocation,payload_offset=offset,payload=identity(payload),
        entry=entry,trampoline=original|1,original_begin=BEGIN,original_begin_identity=dict(size=END-BEGIN,sha256=BEGIN_SHA),
        original_owner_run=35341496620,owners=owners,displaced_prologue_hex=PROLOGUE.hex(),
        original_resume=(BEGIN+8)|1,independent_policy_compiles=2,existing_allocations_rehashed=changed,
        reserved_entry_owner=region,original_entry_changed_bytes=8,undeclared_changed_bytes=0,npc_payload_changed=False,save_layout_changes=0,
        sources={p:identity((ROOT/p).read_bytes()) for p in sources},
        new_emulator_processes=0,accepted_native_cases_replayed=0,ordinary_battle_accepted=False,
        ring_full_acceptance=False,release_ready=False)
    (OUT/'candidate.gba').write_bytes(new);(OUT/'candidate.json').write_bytes(stable(report))
    # 再開時に巨大sourceを再検索せず、検証した実装と必要helperを直接読めるよう保持。
    for name in (*sources,'tools/mgba_pr16_purchased_gear.c','tools/mgba_pr16_natural_capture.c',
                 'scripts/pr16_resume.py','scripts/pr16_ring_followup_v2.py',
                 'scripts/pr16_ring_compiled_record.py','scripts/pr16_ring_npc_workbench.py'):
        target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    need((gift.OUT/'candidate.gba').read_bytes()==raw,'accepted gift parent mutated')
    print(json.dumps({k:v for k,v in report.items() if k not in ('allocation','sources')},ensure_ascii=False))
    return report


if __name__=='__main__':run()
