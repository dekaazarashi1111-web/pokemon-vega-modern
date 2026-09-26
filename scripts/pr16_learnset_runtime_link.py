#!/usr/bin/env python3
"""受入済み親を保存byteから復元し、新2入口だけをThumb veneerで接続する。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from tools import pr16_learnset_runtime as r
from tools import pr16_learnset_successor as s
import pr16_saved_recipe as saved

TASK = 'USER-20260922-LEARNSET-RUNTIME'
PARENT = {'size':33554432, 'sha256':'46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38'}
ANCHOR = {'size':33554432, 'sha256':'6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3'}
NORMAL = 'content/modernization/pr16_saved_reconstruction_recipes.json'
HOOKS = {'Pr16_GameGetLevelUpMovesBySpecies':0x011142A0,
         'Pr16_GameCanMonLearnTMHM':0x01110184}
need = r.need


def materialize() -> bytes:
    """入力復元のみ。旧監査/ARM/nativeは実行しない。"""
    normal = s.read_json(ROOT/NORMAL)
    raw = (ROOT/'build/stages/80_modernization_runtime_boundary_repair.gba').read_bytes()
    need(saved.identity(raw) == ANCHOR, '固定anchor不一致')
    for recipe in [*normal['recipes'], s.read_json(ROOT/r.ALLOCATION)['build']]:
        need(saved.identity(raw) == recipe['parent'], '保存recipe親不一致')
        raw = saved.patch(raw, recipe['patches'])
        need(saved.identity(raw) == recipe['candidate'], '保存recipe復元不一致')
    need(saved.identity(raw) == PARENT, '受入親ROM不一致')
    return raw


def command(args: list[str], output: Path | None = None) -> bytes:
    run = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=180)
    if output is not None:
        output.write_bytes(run.stdout + run.stderr)
    need(run.returncode == 0, '新ARM工程失敗: ' + ' '.join(args[:2]) + '\n' + run.stderr.decode())
    return run.stdout


def link(folder: Path, parent: bytes) -> dict:
    image = (folder/'runtime-image.bin').read_bytes()
    receipt = s.read_json(folder/'receipt.json')
    need(saved.identity(parent) == PARENT and saved.identity(image) == receipt['image'], 'link入力不一致')
    start = receipt['planned_rom_offset']; address = 0x08000000 + start
    rel = folder.relative_to(ROOT).as_posix()
    (folder/'pr16_learnset_runtime_generated.h').write_text('#define PR16_IMAGE_SIZE '+str(len(image))+'u\n')
    (folder/'image.S').write_text('.section .learnsets,"a",%progbits\n.balign 4\n.global Pr16LearnsetImage\nPr16LearnsetImage:\n.incbin "'+rel+'/runtime-image.bin"\n')
    (folder/'runtime.ld').write_text('SECTIONS { . = '+hex(address)+'; .learnsets : { KEEP(*(.learnsets)) } . = ALIGN(4); .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } ASSERT(SIZEOF(.data) == 0, "writable data forbidden") ASSERT(SIZEOF(.bss) == 0, "BSS forbidden") }\n')
    cc = 'arm-none-eabi-gcc'
    flags = ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin',
             '-fno-common','-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
             '-Wall','-Wextra','-Werror','-I'+rel]
    objects = []
    for source in ('src/modernization/pr16_learnset_owner.c', 'src/modernization/pr16_learnset_runtime.c',
                   'src/modernization/pr16_learnset_game.c', rel+'/image.S'):
        obj = rel+'/'+Path(source).stem+'.o'; objects.append(obj)
        command([cc,*flags,'-c',source,'-o',obj])
    elf = rel+'/runtime.elf'
    command([cc,*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/runtime.ld',*objects,'-o',elf])
    need(command(['arm-none-eabi-nm','-u',elf]).strip() == b'', '未解決ARM symbol')
    command(['arm-none-eabi-objcopy','-O','binary',elf,rel+'/runtime-bundle.bin'])
    disassembly = command(['arm-none-eabi-objdump','-d',elf])
    (folder/'disassembly.txt').write_bytes(disassembly)
    symbols = {}
    for line in command(['arm-none-eabi-nm','-n',elf]).decode().splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0],16)
    bundle = (folder/'runtime-bundle.bin').read_bytes()
    need(symbols['Pr16LearnsetImage'] == address and bundle[:len(image)] == image, '配置image先頭不一致')
    need(0 < len(bundle)-len(image) <= receipt['code_reserve'], '新ARM code容量超過')
    need(parent[start:start+len(bundle)] == b'\xff'*len(bundle), '空間の実ROM preimageがFFではない')
    plan = s.read_json(ROOT/r.ALLOCATION)['build']['allocation']
    need(r.free_span(plan, r.aligned(len(image))+receipt['code_reserve'])[0] == start, '配置計画不一致')
    patches = []
    output = bytearray(parent)
    output[start:start+len(bundle)] = bundle
    for name, offset in HOOKS.items():
        target = symbols[name]
        need(address+len(image) <= target < address+len(bundle) and target % 2 == 0 and offset % 4 == 0, 'Thumb target範囲/alignment')
        after = b'\x00\x4b\x18\x47' + struct.pack('<I', target|1)
        patches.append({'symbol':name,'offset':offset,'before':parent[offset:offset+8].hex(),
                        'after':after.hex(),'target':target|1})
        output[offset:offset+8] = after
    # 全ROM差分は新領域と宣言した2入口のみに限定。旧表rootや保存hookを変更しない。
    allowed = [(start,start+len(bundle)), *[(p['offset'],p['offset']+8) for p in patches]]
    changed = 0
    for at,(before,after) in enumerate(zip(parent,output)):
        if before != after:
            changed += 1
            need(any(a <= at < b for a,b in allowed), '宣言外ROM差分')
    for offset in (0x4346C,0x432B4,0x1263D8,0x1FDA1F8,0x5EC,0xDB4E8):
        need(output[offset:offset+4] == parent[offset:offset+4], '共有root/save hook変更')
    # 入力とは別の候補だけを.localへ保存。ROMをtracked/artifactへ追加しない。
    (folder/'candidate.gba').write_bytes(output)
    allocation = copy.deepcopy(plan)
    allocation['allocations'].append({'name':'pr16_learnset_runtime_two_entrypoints',
        'region':receipt['planned_region'],'start':start,'end_exclusive':start+len(bundle),'size':len(bundle),
        'alignment':4,'placement':'FIRST_FIT','owner':TASK,'purpose':'PLR1 owner-gated level listing and existing machine slots',
        'content_sha256':hashlib.sha256(bundle).hexdigest(),'sequence':len(plan['allocations']),
        'gba_start':address,'gba_end_exclusive':address+len(bundle)})
    summary = allocation['summaries']
    summary['allocation_count'] += 1; summary['allocated_bytes'] += len(bundle); summary['remaining_allocatable_bytes'] -= len(bundle)
    for usage in summary['region_usage']:
        if usage['region'] == receipt['planned_region']:
            usage['allocation_count'] += 1; usage['allocated_bytes'] += len(bundle); usage['remaining_bytes'] -= len(bundle)
    report = {'schema_version':1,'status':'LINKED_TWO_ENTRYPOINTS_NOT_GAMEPLAY_ACCEPTANCE','parent':PARENT,
        'candidate':saved.identity(bytes(output)),'candidate_crc32':f'{zlib.crc32(output)&0xffffffff:08X}',
        'image':saved.identity(image),'bundle':saved.identity(bundle),'start':start,
        'code_start':address+len(image),'code_end':address+len(bundle),'symbols':{k:symbols[k] for k in HOOKS},
        'hooks':patches,'changed_bytes':changed,'outside_declared_ranges':0,
        'protected_root_offsets':[0x4346C,0x432B4,0x1263D8,0x1FDA1F8,0x5EC,0xDB4E8],
        'allocation':allocation,'new_arm_compiles':4,'new_arm_links':1,'old_arm_compiles':0,
        'old_native_replays':0,'global_table_roots_changed':False,'release_ready':False}
    (folder/'link.json').write_bytes(s.encode(report))
    return report
