#!/usr/bin/env python3
"""既受入の固定候補へCircus専用連勝ownerを結合。元Factoryとscript位置は不変。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
OUT = ROOT / '.local/pr16-circus-streak-build'
TASK = 'USER-20260919-CIRCUS-STREAK'
PARENT = dict(size=33554432, sha256='3554dc42923bf426332f25c5776d4e213ab0d89a9d2ad6d3861be8d93b9e2cc1')
SELF = 'scripts/pr16_circus_streak.py'
WORKFLOW = '.github/workflows/pr16-circus-streak-build.yml'
TEST = 'tests/test_pr16_circus_streak_build.py'
PREFIX = 'overlays/circus_streak/'
SOURCES = [PREFIX+n for n in ('circus_streak.c','circus_streak.h','circus_streak_io.c','circus_streak_io.h',
    'circus_streak_runtime.c','circus_streak_runtime.h','circus_facility_policy.c')]
OLD_SOURCE = 'overlays/facility_runtime/facility_runtime.c'
OLD_HEADER = 'overlays/facility_runtime/facility_runtime.h'
RUNTIME = 'pr16_circus_streak_runtime'
VENEER = 'pr16_circus_streak_get_veneer'
RESERVATION = 24000
GET_CALL = 0x09103380
GETTER = 0x091025EC
READ_KEYS_LITERAL = 0x5EC
SAVE_LOAD_LITERAL = 0xDB4E8


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def function_span(source, name):
    matches = list(re.finditer(r'(?m)^(?:static |FACILITY_EXPORT )?(?:void|uint8_t|uint16_t) '+re.escape(name)+r'\([^;]*?\)\s*\{', source))
    need(len(matches)==1, 'function boundary differs: '+name)
    start = matches[0].start(); at = matches[0].end(); depth = 1
    # この固定C sourceの関数内にbraceを持つ文字列/commentを導入したら拒否する。
    while depth and at < len(source):
        depth += (source[at]=='{') - (source[at]=='}'); at += 1
    need(depth==0, 'unterminated function: '+name)
    return start, at


def replace_function(source, name, new):
    start, end = function_span(source, name)
    return source[:start]+new+source[end:]


def isolated_source(source, policy):
    source = source.replace('FacilityRuntime_', 'CircusRuntime_')
    source = source.replace('#include "facility_runtime.h"', '#include "circus_facility.h"\n#include "circus_streak_runtime.h"')
    source = source.replace('#include "../save_migration/save_migration.h"', '#include "save_migration.h"')
    for name in ('restore_original','CircusRuntime_AfterBattle','CircusRuntime_Complete'):
        a,b = function_span(policy,name)
        source = replace_function(source,name,policy[a:b])
    source = replace_function(source,'initialize_ledger_if_needed','')
    before = '    initialize_ledger_if_needed();'
    need(source.count(before)==1,'initialization source differs')
    source = source.replace(before,'    if (!ledger_valid()) { set_result(0u); return; }')
    before = '    original_count = FACILITY_CALCULATE_PARTY_COUNT();'
    need(source.count(before)==1,'entry source differs')
    source = source.replace(before,'    if (!CircusStreakRuntimeBegin()) { set_result(0u); return; }\n'+before)
    a,b = function_span(source,'CircusRuntime_PrepareBattle'); body = source[a:b]
    before = '    persist_current();\n    set_result(1u);'
    need(body.count(before)==1,'prepare source differs')
    source = source[:a]+body.replace(before,'    if (!CircusStreakRuntimeArm()) { set_result(0u); return; }\n    set_result(1u);')+source[b:]
    source = replace_function(source,'CircusRuntime_Recover', '''FACILITY_EXPORT void CircusRuntime_Recover(void)
{
    if (!CircusStreakRuntimeRecover()) { set_result(0u); return; }
    if (ledger_valid() && gVegaModernSaveData->factory.snapshot_valid) {
        set_result(restore_original(1u));
        return;
    }
    set_result(1u);
}''')
    source = replace_function(source,'CircusRuntime_Abort', '''FACILITY_EXPORT void CircusRuntime_Abort(void)
{
    set_result(restore_original(1u));
}''')
    for forbidden in ('factory.current_streak','factory.best_streak','factory.reward_claim_bits','VegaFactoryClaimReward','VegaSaveInitNew'):
        need(forbidden not in source,'Factory state alias: '+forbidden)
    return source


def bounded_patch(raw, patches):
    need(type(raw) is bytes and patches,'immutable input/patches required')
    ordered = sorted(patches,key=lambda r:r['offset'])
    out = bytearray(raw); cursor = 0
    for row in ordered:
        at = row['offset']; before = bytes.fromhex(row['before']); after = bytes.fromhex(row['after'])
        need(type(at) is int and len(before)==len(after)>0 and cursor<=at<=len(raw)-len(before),'overlap or bounds')
        need(raw[at:at+len(before)]==before,'patch preimage differs: '+row['name'])
        out[at:at+len(after)]=after
        need(bytes(out[cursor:at])==raw[cursor:at],'undeclared patch')
        cursor=at+len(after)
    need(bytes(out[cursor:])==raw[cursor:],'undeclared suffix')
    rollback=bytearray(out)
    for row in ordered:
        at=row['offset']; before=bytes.fromhex(row['before']); rollback[at:at+len(before)]=before
    need(bytes(rollback)==raw,'whole-ROM rollback differs')
    return bytes(out)


def compile_runtime(folder, address, policy, delegates):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'circus_facility.c').write_text(isolated_source((ROOT/OLD_SOURCE).read_text(),(ROOT/(PREFIX+'circus_facility_policy.c')).read_text()))
    (folder/'circus_facility.h').write_text((ROOT/OLD_HEADER).read_text().replace('FacilityRuntime_', 'CircusRuntime_'))
    (folder/'circus_streak_addresses.h').write_text('\n'.join(f'#define {name} 0x{value:08X}u' for name,value in delegates.items())+'\n')
    linker=folder/'runtime.ld'
    linker.write_text(f'ENTRY(CircusRuntime_Probe)\nSECTIONS {{ . = 0x{address:08X}; .text : {{ KEEP(*(.text.CircusRuntime_*)) KEEP(*(.text.CircusStreakRuntime*)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }} }}\n')
    elf=folder/'runtime.elf'; binary=folder/'runtime.bin'
    defines=[f'-DVEGA_FACILITY_{label}_ADDRESS=0x{policy[key]:08X}u' for label,key in
        (('CONFIGURE_POLICY','configure_facility'),('GENERATE_RENTALS','generate_rentals'),('GENERATE_TRAINER','generate_trainer'))]
    command=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
        '-Wall','-Wextra','-Werror','-fstack-usage','-DVEGA_SAVE_ROM_RUNTIME=1','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
        '-T',str(linker),'-I',str(folder),'-I',str(ROOT/PREFIX),'-I',str(ROOT/'overlays/save_migration'),*defines,
        str(folder/'circus_facility.c'),str(ROOT/'overlays/save_migration/save_migration.c'),
        *[str(ROOT/(PREFIX+n)) for n in ('circus_streak.c','circus_streak_io.c','circus_streak_runtime.c')],'-o',str(elf)]
    result=subprocess.run(command,text=True,capture_output=True,cwd=folder)
    (folder/'compile.stdout').write_text(result.stdout);(folder/'compile.stderr').write_text(result.stderr)
    need(result.returncode==0,'ARM compile failed: '+result.stderr[-3000:])
    need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)])==b'','unresolved ARM symbol')
    syms=subprocess.check_output(['arm-none-eabi-nm','-n','--defined-only',str(elf)],text=True)
    need(not any(len(line.split())==3 and line.split()[1] in 'bBdD' for line in syms.splitlines()),'unexpected writable static state')
    entries={r[2]:int(r[0],16)|1 for line in syms.splitlines() if len(r:=line.split())==3 and r[2].startswith(('CircusRuntime_','CircusStreakRuntime'))}
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes();need(64<len(payload)<=RESERVATION,'payload exceeds reservation')
    (folder/'symbols.txt').write_text(syms)
    (folder/'disassembly.txt').write_text(subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True).replace(str(elf),'circus-streak.elf'))
    return payload,entries


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_circus_retention as parent
    import pr16_circus_entry as admission
    import pr16_bp_party_retention_successor as old
    import pr16_ring_npc_successor as gift
    from scripts.pr16_bp_trial_route import graph
    from tools.rom_allocator import build_allocation_report_from_csv
    OUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe output path')
    raw=(parent.OUT/'candidate.gba').read_bytes(); recipe=json.loads((parent.OUT/'report.json').read_bytes())
    need(identity(raw)==PARENT and recipe['candidate']==PARENT,'accepted retention parent differs')
    requests=old.existing_requests(recipe['allocation'])
    req=dict(name=RUNTIME,region='future_tail',size=RESERVATION,alignment=16,owner=TASK,purpose='Circus-owned streak/save and isolated reception runtime',content_sha256='0'*64)
    veneer=dict(name=VENEER,region='integration_modules',size=8,alignment=4,owner=TASK,purpose='sp072 read-only Circus streak getter long-call veneer',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req,veneer])
    off=next(r['start'] for r in preview['allocations'] if r['name']==RUNTIME)
    near=next(r['start'] for r in preview['allocations'] if r['name']==VENEER)
    need(raw[SAVE_LOAD_LITERAL-4:SAVE_LOAD_LITERAL]==bytes.fromhex('004b1847'),'save-load trampoline changed')
    delegates=dict(CIRCUS_PREVIOUS_READ_KEYS=struct.unpack_from('<I',raw,READ_KEYS_LITERAL)[0],
        CIRCUS_PREVIOUS_SAVE_LOAD=struct.unpack_from('<I',raw,SAVE_LOAD_LITERAL)[0],CIRCUS_PREVIOUS_SELECTOR=recipe['entries']['selector'])
    need(all(v&1 and BASE<=v<BASE+len(raw) for v in delegates.values()),'delegate must be bound Thumb ROM')
    cfg=json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    archive=ROOT/'.local/pr16-bp-trial-native-inputs/pokemon-vega-private-env-v1-state.zip'
    bound=next(r for r in cfg['archives'] if r['name']==archive.name)
    need(identity(archive.read_bytes())=={k:bound[k] for k in ('size','sha256')},'fixed source archive differs')
    with zipfile.ZipFile(archive) as z:
        meta=json.loads(z.read('build/stages/20_facility_runtime.json'))
        global_header=z.read('vendor/upstream/CFRU-JP/include/global.h')
    policy=meta['contract']['battle_policy_addresses']
    match=re.search(rb'/\*0x00A\*/[^\n]*playerTrainerId[^\n]*',global_header)
    need(match is not None,'trainer identity ABI no longer +0xA')
    builds=[compile_runtime(OUT/f'compile-{n}',BASE+off,policy,delegates) for n in (1,2)]
    need(builds[0]==builds[1],'independent ARM links differ')
    payload,entries=builds[0]; patches=[]
    def patch(name,offset,after):
        patches.append(dict(name=name,offset=offset,before=raw[offset:offset+len(after)].hex(),after=after.hex()))
    need(raw[off:off+len(payload)]==b'\xff'*len(payload) and raw[near:near+8]==b'\xff'*8,'new allocation not erased')
    patch('new-runtime',off,payload)
    jump=bytes.fromhex('004b1847')+struct.pack('<I',entries['CircusStreakRuntimeGet'])
    patch('sp072-get-veneer',near,jump)
    need(old.decode_thumb_bl(GET_CALL,raw[GET_CALL-BASE:GET_CALL-BASE+4])==GETTER,'sp072 getter preimage differs')
    patch('sp072-getter-call',GET_CALL-BASE,old.encode_thumb_bl(GET_CALL,BASE+near))
    patch('read-keys-delegate',READ_KEYS_LITERAL,struct.pack('<I',entries['CircusStreakRuntimeReadKeys']))
    patch('save-load-delegate',SAVE_LOAD_LITERAL,struct.pack('<I',entries['CircusStreakRuntimeSaveLoad']))
    natives=json.loads((admission.OUT/'facility-symbols.json').read_bytes())['entrypoints']
    remap={value:entries[name.replace('FacilityRuntime_','CircusRuntime_')] for name,value in natives.items()}
    remap[recipe['entries']['selector']]=entries['CircusStreakRuntimeSelect']
    nodes=graph(raw,[recipe['entries']['circus']]);seen=set();calls=[]
    need(len(nodes)<=128,'bounded Circus graph exceeded')
    owner=next(r for r in recipe['allocation']['allocations'] if r['name']==admission.ALLOCATION)
    for node in nodes:
        for row in node['instructions']:
            address=row['address']
            need(owner['gba_start']<=address<owner['gba_end_exclusive'],'Circus edge escaped clone')
            if address in seen:continue
            seen.add(address)
            if row['opcode']==0x23 and row['native'] in remap:
                new=remap[row['native']];patch('circus-native-call',address-BASE+1,struct.pack('<I',new))
                calls.append(dict(address=address,before=row['native'],after=new))
    need(sum(r['before']==recipe['entries']['selector'] for r in calls)==3,'three selector edges required')
    for suffix in ('Enter','PrepareBattle','AfterBattle','Complete','Abort'):
        need(any(r['before']==natives['FacilityRuntime_'+suffix] for r in calls),'missing production edge '+suffix)
    left=bounded_patch(raw,patches);need(left==bounded_patch(raw,patches),'independent patches differ')
    changed=[]
    for row,request in zip(recipe['allocation']['allocations'],requests):
        a,b=row['start'],row['end_exclusive'];need(identity(raw[a:b])['sha256']==row['content_sha256'],'parent owner hash differs')
        if raw[a:b]!=left[a:b]:
            need(row['name']==admission.ALLOCATION,'non-Circus prior allocation changed: '+row['name'])
            request['content_sha256']=identity(left[a:b])['sha256'];changed.append(row['name'])
    req.update(start=off,size=len(payload),content_sha256=identity(payload)['sha256'])
    veneer.update(start=near,content_sha256=identity(jump)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req,veneer])
    need(allocation['summaries']['overlap_count']==0,'allocator overlap')
    for row in allocation['allocations']:
        need(identity(left[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'candidate owner hash differs')
    need(all(left[c-BASE-1]==0x5D for c in parent.CONTINUATIONS),'accepted script continuations changed')
    sources=[SELF,TEST,WORKFLOW,OLD_SOURCE,OLD_HEADER,*SOURCES,'config/ram_layout.csv','config/save_layout.csv',
        'tests/test_pr16_circus_streak.py','tests/fixtures/circus_streak_fixture.c','tests/fixtures/circus_streak_io_fixture.c',
        'overlays/save_migration/save_migration.c','overlays/save_migration/save_migration.h']
    report=dict(schema_version=1,status='BUILT_CIRCUS_STREAK_NATIVE_OPEN',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),run_id=int(os.environ.get('GITHUB_RUN_ID','0')),
        parent=PARENT,candidate=identity(left),payload=identity(payload),payload_offset=off,entries=entries,
        reception=recipe['entries'],launch_sites=recipe['launch_sites'],delegates=delegates,patches=patches,calls=calls,
        allocation=allocation,changed_existing_allocations=changed,independent_arm_links=2,whole_rom_rollback_matches_parent=True,
        original_factory_runtime_unchanged=True,original_factory_streak_and_claim_not_aliased=True,
        accepted_script_continuations=list(parent.CONTINUATIONS),trainer_id_abi=match[0].decode(),
        source_bindings={n:identity((ROOT/n).read_bytes()) for n in sources},new_emulator_processes=0,
        accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    (OUT/'candidate.gba').write_bytes(left);(OUT/'report.json').write_bytes(stable(report))
    (OUT/'circus-graph.json').write_bytes(stable(nodes))
    need((parent.OUT/'candidate.gba').read_bytes()==raw,'accepted parent mutated')
    print(json.dumps({k:report[k] for k in ('status','candidate','payload','entries','original_factory_runtime_unchanged')},ensure_ascii=False))
    return report

if __name__=='__main__':
    run()
