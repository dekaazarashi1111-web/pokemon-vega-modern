#!/usr/bin/env python3
"""保存hostを継承し、PLC2分割配置と未実行の4入口だけを検証する。"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_learnset_conditional_native as n
from tools import pr16_learnset_compact as compact
from tests.test_pr16_learnset_compact import audit_library, load_library
s, r, h = n.s, n.r, n.h
need, write, command, identity = n.need, n.write, n.command, n.identity
WORK = ROOT/'.local/pr16-learnset-compact-native'
n.WORK = WORK
TASK = 'USER-20260922-LEARNSET-COMPACT'
BASE = 0x08000000
ABI_INPUTS = 'content/modernization/pr16_learnset_conditional_bound_inputs.json'
CODE = ('tools/pr16_learnset_compact.py', 'src/modernization/pr16_learnset_compact.h',
        'src/modernization/pr16_learnset_compact.c', 'tests/test_pr16_learnset_compact.py',
        'scripts/pr16_learnset_compact_native.py', '.github/workflows/pr16-learnset-compact-native.yml')
FAIL_HEAD = 'd61d54443d5ac8d47c9807a8a042c1e4402073dd'
FAIL_RUN = 35716683381
FAIL_ARTIFACT = {'id':10690456075, 'name':'pr16-learnset-conditional-native-proof',
    'size_in_bytes':2023, 'digest':'sha256:238193c280c6db58b2b2a3d63d5a48947ed2f47de7afc6fde975e88496bc6df3'}
FAIL_FILES = {
    'build11.txt':{'size':905,'sha256':'6d4a3e579086c5f3c48601c847290949913b78e37a44056f3fca956eac512b1e'},
    'failure.json':{'size':980,'sha256':'ef855fdb1f64b857ab117a797116fa33ebd7e1a748f1bb0a815c1114e28dab15'},
    'game-unit.txt':{'size':2495,'sha256':'c968fa29627fbcbf69faffaa9d110d4d950b338d45ab28006c5223bc0357190a'},
    'inherited-host.json':{'size':158,'sha256':'16c1d69026f963d8053da73b03bf3555007e5273dc6db56c95c1950082a96634'}}


def inherit_game():
    """失敗runの成功18試験のみ継承。run全体のfailureは変更しない。"""
    run = n.fetch(f'actions/runs/{FAIL_RUN}')
    need(run['head_sha'] == FAIL_HEAD and run['status'] == 'completed'
         and run['conclusion'] == 'failure'
         and run['head_branch'] == 'codex/modernization-followup-20260908'
         and run['path'] == '.github/workflows/pr16-learnset-conditional-native.yml', '旧failure結合不一致')
    n.download(FAIL_ARTIFACT, FAIL_HEAD, WORK/'failed-proof', FAIL_FILES)
    files = [x for x in n.CODE if x.startswith(('src/', 'tests/'))]
    bindings = {}
    for name in files:
        old = n.fetch('contents/'+name+'?ref='+FAIL_HEAD)
        raw = (ROOT/name).read_bytes()
        sha = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        need(sha == old['sha'], '18試験のsource変更: '+name)
        bindings[name] = identity(raw)
    text = (WORK/'failed-proof/game-unit.txt').read_bytes()
    need(text.count(b' ... ok\n') == 18 and re.search(rb'Ran 18 tests\b', text)
         and b'\nOK\n' in text and b'FAILED (' not in text, '18試験原本不一致')
    failure = s.read_json(WORK/'failed-proof/failure.json')
    need(failure['source_head'] == FAIL_HEAD and '連続空間が不足' in failure['error'], '配置失敗原本不一致')
    record = {'run_id':FAIL_RUN, 'source_head':FAIL_HEAD, 'run_conclusion':'failure',
              'inherited_game_tests':18, 'game_tests_executed_again':0,
              'failure_stage':'allocation_before_arm_compile', 'prior_arm_compiles':0,
              'prior_native_processes':0, 'code_bindings':bindings,
              'artifact':FAIL_ARTIFACT, 'proof_files':FAIL_FILES}
    write(WORK/'proof/inherited-game.json', record)
    shutil.copyfile(WORK/'failed-proof/game-unit.txt', WORK/'proof/inherited-game-unit.txt')
    shutil.copyfile(WORK/'failed-proof/failure.json', WORK/'proof/previous-failure.json')
    return record


def allocation_row(name, region, start, blob, sequence):
    return {'name':name, 'region':region, 'start':start,
        'end_exclusive':start+len(blob), 'size':len(blob), 'alignment':4,
        'placement':'FIRST_FIT', 'owner':TASK, 'purpose':'PLC2四条件consumerの分割配置',
        'content_sha256':hashlib.sha256(blob).hexdigest(), 'sequence':sequence,
        'gba_start':BASE+start, 'gba_end_exclusive':BASE+start+len(blob)}


def validate_abi(parent, abi):
    need(identity(parent) == abi['candidate'], 'ABI固定親候補不一致')
    for entry in abi['entries'].values():
        at = entry['offset']; expected = bytes.fromhex(entry['preimage'])
        need(entry['address'] == BASE + at and len(expected) == 32
             and parent[at:at+32] == expected, 'ABI入口32bytes不一致')
        if 'thumb_veneer_target' in entry:
            target = entry['thumb_veneer_target']; pos = (target & ~1) - BASE
            need(target & 1 and parent[at:at+4] == bytes.fromhex('004b1847')
                 and struct.unpack_from('<I',parent,at+4)[0] == target
                 and parent[pos:pos+64].hex() == entry['target_preimage'], 'ABI委譲先不一致')
    need(parent[0x10EB970:0x10EB97C].hex() == '9c46014b1847c04685db5d09', '共有入口12byte veneer不一致')
    need(abi['entries']['reminder']['thumb_veneer_target'] == 0x095DDBE9, 'P07保全delegate不一致')
    return abi['entries']


def link(folder: Path):
    folder.mkdir()
    parent = (WORK/'restore/parent.gba').read_bytes()
    prior = s.read_json(WORK/'restore/progress/link.json')
    need(identity(parent) == prior['candidate'], '固定親候補不一致')
    abi = s.read_json(ROOT/ABI_INPUTS)['abi']
    entries = validate_abi(parent, abi)
    source = (WORK/'host-data/conditional-image.bin').read_bytes()
    need(identity(source) == s.read_json(ROOT/n.LOCK)['data_files']['conditional-image.bin'], '固定PLC1不一致')
    image, receipt = compact.compact(source)
    plan = copy.deepcopy(prior['allocation'])
    data_start, data_region = r.free_span(plan, len(image))
    plan['allocations'].append(allocation_row('pr16_conditional_plc2', data_region, data_start,
                                             image, len(plan['allocations'])))
    start, region = r.free_span(plan, 8192)
    base = BASE+start
    rel = folder.relative_to(ROOT).as_posix()
    header = folder/'pr16_learnset_conditional_bindings.h'
    text = n.bindings(s.read_json(WORK/'restore/runtime/link.json'))
    need(text.count('115282u') == 1 and text.count('#define PR16_READ_CONDITIONAL Pr16ReadLearnsetConditional') == 1, '親binding形状変更')
    text = text.replace('115282u',str(len(image))+'u').replace(
        '#define PR16_READ_CONDITIONAL Pr16ReadLearnsetConditional',
        '#include "pr16_learnset_compact.h"\n#define PR16_READ_CONDITIONAL Pr16ReadCompactConditional')
    need(text.count('0x0954B281u') == 1, 'archive binding形状変更')
    text = text.replace('0x0954B281u', hex(entries['reminder']['thumb_veneer_target'])+'u')
    header.write_text(text)
    (folder/'conditional.ld').write_text('Pr16ConditionalImage = '+hex(BASE+data_start)+';\nSECTIONS { . = '+hex(base)
        +'; .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } '
        +'/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } '
        +'ASSERT(SIZEOF(.data)==0,"data forbidden") ASSERT(SIZEOF(.bss)==0,"BSS forbidden") }\n')
    flags = ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin',
             '-fno-common','-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
             '-Wall','-Wextra','-Werror','-Isrc/modernization','-I'+rel]
    objects = []
    for name in ('pr16_learnset_conditional','pr16_learnset_compact','pr16_learnset_conditional_game'):
        obj = rel+'/'+name+'.o'; objects.append(obj)
        h.old.command(['arm-none-eabi-gcc',*flags,'-include',str(header),'-c','src/modernization/'+name+'.c','-o',obj])
    elf = rel+'/conditional.elf'
    h.old.command(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/conditional.ld',*objects,'-o',elf])
    need(not h.old.command(['arm-none-eabi-nm','-u',elf]).strip(), '未解決symbol')
    h.old.command(['arm-none-eabi-objcopy','-O','binary',elf,rel+'/conditional.bin'])
    (folder/'disassembly.txt').write_bytes(h.old.command(['arm-none-eabi-objdump','-d',elf]))
    symbols = {}
    for line in h.old.command(['arm-none-eabi-nm','-n',elf]).decode().splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0],16)
    blob = (folder/'conditional.bin').read_bytes()
    need(0 < len(blob) <= 8192 and symbols['Pr16ConditionalImage'] == BASE+data_start, 'code/data配置不一致')
    segments = ((start,blob,region,'conditional.bin'), (data_start,image,data_region,'compact-image.bin'))
    out = bytearray(parent)
    for at, raw, _, name in segments:
        need(parent[at:at+len(raw)] == b'\xff'*len(raw), '分割配置preimage違反: '+name)
        out[at:at+len(raw)] = raw
    hooks = (('Pr16_GameAfterEvolution',0x1114120,'8446f8b562465423'),
             ('Pr16_GameGetConditionalRelearnerMoves',0x11141D4,'004b1847e9db5d09'),
             ('Pr16_GameGetEggMoves',0x451EC,'004b1847adb15409'),
             ('Pr16_GameGetAllEggMoves',0x10EB970,'9c46014b1847c046'))
    import pr16_evolution_learning_repair as evo
    need(parent[evo.START:evo.START+len(evo.DISPATCH)] == evo.DISPATCH, 'P03 dispatcher不一致')
    patches = []
    for name, at, expected in hooks:
        need(parent[at:at+8].hex() == expected, '固定4入口preimage不一致: '+hex(at))
        target = symbols[name]
        need(at%4 == 0 and base <= target < base+len(blob) and target%2 == 0, 'Thumb/alignment不一致')
        after = b'\x00\x4b\x18\x47'+struct.pack('<I',target|1)
        out[at:at+8] = after
        patches.append({'symbol':name,'offset':at,'before':expected,'after':after.hex(),'target':target|1})
    rollback = bytearray(out)
    for at, raw, _, _ in segments: rollback[at:at+len(raw)] = b'\xff'*len(raw)
    for p in patches: rollback[p['offset']:p['offset']+8] = bytes.fromhex(p['before'])
    need(bytes(rollback) == parent, '宣言外ROM変更')
    for phase in ('runtime','progress'):
        old = s.read_json(WORK/'restore'/phase/'link.json'); at=old['start']; size=old['bundle']['size']
        need(out[at:at+size] == parent[at:at+size], '受入PLR1/通常level-up変更')
    for at in prior['protected_root_offsets']: need(out[at:at+4] == parent[at:at+4], '共有root変更')
    need(out[evo.START:evo.START+len(evo.DISPATCH)] == parent[evo.START:evo.START+len(evo.DISPATCH)]
         and out[evo.ENTRY:evo.ENTRY+8] == parent[evo.ENTRY:evo.ENTRY+8], '進化振分け変更')
    touched = []
    for row in plan['allocations'][:-1]:
        if any(row['start'] <= p['offset'] < row['end_exclusive'] for p in patches):
            row['content_sha256'] = hashlib.sha256(out[row['start']:row['end_exclusive']]).hexdigest()
            touched.append(row['name'])
    plan['allocations'].append(allocation_row('pr16_conditional_plc2_code',region,start,blob,len(plan['allocations'])))
    for row in plan['allocations'][-2:]:
        summary = plan['summaries']; summary['allocation_count'] += 1
        summary['allocated_bytes'] += row['size']; summary['remaining_allocatable_bytes'] -= row['size']
        for usage in summary['region_usage']:
            if usage['region'] == row['region']:
                usage['allocation_count'] += 1; usage['allocated_bytes'] += row['size']; usage['remaining_bytes'] -= row['size']
    ordered = sorted(plan['allocations'],key=lambda row:row['start'])
    need(all(a['end_exclusive'] <= b['start'] for a,b in zip(ordered,ordered[1:])), 'allocation重複')
    report = {'status':'LINKED_FOUR_CONDITIONAL_ENTRYPOINTS', 'format':'PLC2',
        'parent':identity(parent), 'candidate':identity(bytes(out)), 'candidate_crc32':f'{zlib.crc32(out)&0xffffffff:08X}',
        'bundle':identity(blob), 'image':identity(image), 'compact_receipt':receipt,
        'start':start, 'code_start':base, 'code_end':base+len(blob), 'hooks':patches,
        'segments':[{'file':name,'start':at,'region':reg,**identity(raw)} for at,raw,reg,name in segments],
        'symbols':{k:v for k,v in symbols.items() if k.startswith('Pr16')}, 'allocation':plan,
        'protected_root_offsets':prior['protected_root_offsets'], 'prior_image_unchanged':True,
        'outside_declared_ranges':0, 'p03_evolution_dispatch_unchanged':True,
        'updated_allocation_hashes':touched, 'old_arm_compiles':0,
        'abi_run':abi['run_id'], 'p07_archive_delegate':entries['reminder']['thumb_veneer_target'],
        'p07_archive_wrapper_preserved':True,
        'game_tutor_connected':False, 'archive_rebound':False, 'gameplay_e2e_accepted':False, 'release_ready':False}
    (folder/'candidate.gba').write_bytes(out); (folder/'compact-image.bin').write_bytes(image)
    write(folder/'compact-receipt.json',receipt); write(folder/'link.json',report)
    return report


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'link':
        print(json.dumps(link(Path(sys.argv[2]))['candidate']))
    else:
        raise SystemExit('Use pr16_learnset_compact_bound.py verify; accepted host tests must not be repeated')
