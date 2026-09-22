#!/usr/bin/env python3
"""新規初期技/自然level-upだけを配置・検証。受入済みPLR1を再生成しない。"""
from __future__ import annotations
import copy
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_runtime as r
import pr16_learnset_runtime_link as old
from pr16_learnset_floette_verify import download, snapshot
from pr16_learnset_payload_verify import completed_run, current_pr

TASK = 'USER-20260922-LEARNSET-PROGRESS'
WORK = ROOT/'.local/pr16-learnset-progress'
CP = 'content/modernization/pr16_learnset_runtime_checkpoint.json'
EVIDENCE = ROOT/'content/modernization/pr16_learnset_runtime_evidence'
CODE = ('src/modernization/pr16_learnset_progress.h', 'src/modernization/pr16_learnset_progress.c',
        'src/modernization/pr16_learnset_progress_game.c', 'tests/fixtures/pr16_learnset_progress_bindings.h',
        'tests/fixtures/pr16_learnset_progress_fixture.c', 'tests/test_pr16_learnset_progress.py',
        'scripts/pr16_learnset_progress_verify.py', 'tools/mgba_pr16_learnset_progress.c',
        '.github/workflows/pr16-learnset-progress.yml')
SELECTED = ((1,50),(10,13),(649,9),(1029,50),(1670,48),(887,10),(1621,10),(1029,1),(649,1))
BASE = 0x08000000
need = r.need
identity = old.saved.identity


def write(path, value):
    path.write_bytes(s.encode(value))


def execute(args, output, env=None):
    process = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=240, env=env)
    output.write_bytes(process.stdout+process.stderr)
    need(process.returncode == 0, '工程失敗: '+str(args[:3])+'\n'+process.stderr.decode(errors='replace')[-3000:])
    return process.stdout


def restore():
    cp = s.read_json(ROOT/CP)
    completed_run(cp['run_id'], cp['source_head'], '.github/workflows/pr16-learnset-runtime.yml', 'runtime-boundary')
    for name, expected in cp['verification']['code_bindings'].items():
        s.bound(ROOT/name, expected)
    for name, expected in cp['proof_bindings'].items():
        s.bound(EVIDENCE/name, expected)
    download(cp['artifacts']['pr16-learnset-runtime-data'], cp['source_head'], WORK/'accepted', cp['verification']['data_files'])
    parent = old.materialize()
    report = s.read_json(WORK/'accepted/link.json')
    bundle = (WORK/'accepted/runtime-bundle.bin').read_bytes()
    start = report['start']; output = bytearray(parent)
    need(identity(bundle) == report['bundle'] and parent[start:start+len(bundle)] == b'\xff'*len(bundle), '旧bundle/preimage不一致')
    output[start:start+len(bundle)] = bundle
    for patch in report['hooks']:
        at = patch['offset']; before = bytes.fromhex(patch['before']); after = bytes.fromhex(patch['after'])
        need(parent[at:at+8] == before and len(before) == len(after) == 8, '旧hook不一致')
        output[at:at+8] = after
    raw = bytes(output)
    need(identity(raw) == cp['candidate'] == report['candidate'], '親aabd52a0復元失敗')
    (WORK/'parent.gba').write_bytes(raw)
    # Bind the source ABI to the fixed JP linker script, not misleading US comments.
    upstream = 'e24a16fe39e27ae162faf5b78596d1f3df18489d'
    with urllib.request.urlopen('https://raw.githubusercontent.com/kapibarasan000/CFRU-JP/'+upstream+'/BPRJ.ld',timeout=60) as response:
        ld = response.read()
    need(hashlib.sha1(b'blob '+str(len(ld)).encode()+b'\0'+ld).hexdigest() == 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51', 'JP ABI固定blob不一致')
    expected = {'GetMonData':0x0803F355,'GetBoxMonData':0x0803F4B1,
                'GetLevelFromBoxMonExp':0x0803DF9D,'GiveMoveToMon':0x0803E009,
                'GiveMoveToBoxMon':0x0803E01D,'gMoveToLearn':0x02023F82}
    for name, address in expected.items():
        match = re.search(r'^'+name+r'\s*=\s*(0x[0-9A-Fa-f]+)(\s*\|\s*1)?\s*;',ld.decode(),re.M)
        need(match and (int(match[1],16) | bool(match[2])) == address, 'JP ABIアドレス不一致: '+name)
    config = s.read_json(ROOT/'content/modernization/pr16_candidate_wiki_creation_sources.json')
    need(config['upstream_config_sha256'] == '49ea2d82bbd5e0040e39b83e044ff3e4e21e09222bcc0a6879a786cc99da4f6e', '受入CFRU設定のbinding不一致')
    # Accepted source receipt records this exact config. Fetch only fixed ABI config,
    # never the 182-page/1299-species original learnset collectors.
    with urllib.request.urlopen('https://raw.githubusercontent.com/kapibarasan000/CFRU-JP/'+upstream+'/src/config.h',timeout=60) as response:
        cfg = response.read()
    need(hashlib.sha256(cfg).hexdigest() == '49ea2d82bbd5e0040e39b83e044ff3e4e21e09222bcc0a6879a786cc99da4f6e', '固定CFRU設定不一致')
    need(not re.search(rb'^\s*#\s*define\s+FLAG_POKEMON_LEARNSET_RANDOMIZER\b',cfg,re.M), '有効randomizerを消さない')
    (WORK/'proof/abi.json').write_bytes(s.encode({'upstream_head':upstream,'linker_blob':'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
        'linker_identity':identity(ld),'config_identity':identity(cfg),'learnset_randomizer_enabled':False,
        'functions':expected,'cursor':0x02023F88,'cursor_source':'kapibarasan000/CFRU-JP@'+upstream+':src/learn_move.c#sLearningMoveTableID'}))
    return report


def binding_header(report):
    dis = (EVIDENCE/'disassembly.txt').read_text()
    match = re.search(r'^([0-9a-f]+) <Pr16ReadLearnsetRuntime>:',dis,re.M)
    need(match is not None, '受入reader symbol欠落')
    reader = int(match[1],16)
    need(report['code_start'] <= reader < report['code_end'] and reader%2 == 0, 'reader範囲違反')
    return f'''#include "pr16_learnset_runtime.h"
#define PR16_IMAGE ((const uint8_t *){hex(BASE+report['start'])}u)
#define PR16_IMAGE_SIZE 108008u
#define PR16_READ_VIEW ((uint8_t (*)(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *)){hex(reader|1)}u)
#define PR16_GET_MON_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F355u)
#define PR16_GET_BOX_DATA ((uint32_t (*)(const void *,int,uint8_t *))0x0803F4B1u)
#define PR16_GET_BOX_LEVEL ((uint8_t (*)(const void *))0x0803DF9Du)
#define PR16_GIVE_MON_MOVE ((uint16_t (*)(void *,uint16_t))0x0803E009u)
#define PR16_GIVE_BOX_MOVE ((uint16_t (*)(void *,uint16_t))0x0803E01Du)
#define PR16_LEARNING_CURSOR ((volatile uint8_t *)0x02023F88u)
#define PR16_PENDING_MOVE ((volatile uint16_t *)0x02023F82u)
'''


def link(folder):
    folder.mkdir()
    prior = s.read_json(WORK/'accepted/link.json'); parent = (WORK/'parent.gba').read_bytes()
    need(identity(parent) == prior['candidate'], '新link親不一致')
    start, region = r.free_span(prior['allocation'], 4096)
    address = BASE+start
    (folder/'pr16_learnset_progress_bindings.h').write_text(binding_header(prior))
    rel = folder.relative_to(ROOT).as_posix()
    (folder/'progress.ld').write_text('SECTIONS { . = '+hex(address)+'; .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } ASSERT(SIZEOF(.data)==0,"data forbidden") ASSERT(SIZEOF(.bss)==0,"BSS forbidden") }\n')
    flags = ['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin','-fno-common',
             '-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
             '-Wall','-Wextra','-Werror','-Isrc/modernization','-I'+rel]
    objects = []
    for name in ('pr16_learnset_progress','pr16_learnset_progress_game'):
        obj = rel+'/'+name+'.o'; objects.append(obj)
        old.command(['arm-none-eabi-gcc',*flags,'-c','src/modernization/'+name+'.c','-o',obj])
    elf = rel+'/progress.elf'
    old.command(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/progress.ld',*objects,'-o',elf])
    need(not old.command(['arm-none-eabi-nm','-u',elf]).strip(), '未解決symbol')
    old.command(['arm-none-eabi-objcopy','-O','binary',elf,rel+'/progress.bin'])
    (folder/'disassembly.txt').write_bytes(old.command(['arm-none-eabi-objdump','-d',elf]))
    symbols = {}
    for line in old.command(['arm-none-eabi-nm','-n',elf]).decode().splitlines():
        fields=line.split()
        if len(fields)==3: symbols[fields[2]]=int(fields[0],16)
    binary = (folder/'progress.bin').read_bytes()
    need(0<len(binary)<=4096 and parent[start:start+len(binary)] == b'\xff'*len(binary), '新code容量/preimage違反')
    # Both pre-CFRU and direct CFRU calls must see the new owner, not old tables.
    legacy = 0x3E1F4
    need(parent[legacy:legacy+4] == b'\x00\x4a\x10\x47', 'natural入口veneer不一致')
    natural = struct.unpack_from('<I', parent, legacy+4)[0]
    need(natural & 1 and 0x09110000 <= natural < 0x09120000, 'natural実symbol範囲違反')
    natural_off = (natural & ~1)-BASE
    initial_off = 0x11145F0
    need(hashlib.sha256(parent[initial_off:initial_off+168]).hexdigest() == 'ce09526af6b37397bd031705203a53c7109fe8e0a19d3809e964677313379c3e', '固定initial本体不一致')
    hooks = [('Pr16_GameGiveBoxMonInitialMoveset',0x3E174),('Pr16_GameGiveBoxMonInitialMoveset',initial_off),
             ('Pr16_GameMonTryLearningNewMove',legacy),('Pr16_GameMonTryLearningNewMove',natural_off)]
    need(len({at for _,at in hooks})==4, '入口重複')
    output = bytearray(parent);output[start:start+len(binary)] = binary; patches=[]
    for name, at in hooks:
        target=symbols[name]
        need(at%4==0 and address<=target<address+len(binary) and target%2==0, 'Thumb範囲/alignment違反')
        after=b'\x00\x4b\x18\x47'+struct.pack('<I',target|1)
        patches.append({'symbol':name,'offset':at,'before':parent[at:at+8].hex(),'after':after.hex(),'target':target|1})
        output[at:at+8]=after
    # Byte-complete rollback, including the untouched prior hooks/image and save roots.
    rollback=bytearray(output);rollback[start:start+len(binary)]=b'\xff'*len(binary)
    for patch in patches: rollback[patch['offset']:patch['offset']+8]=bytes.fromhex(patch['before'])
    need(bytes(rollback)==parent, '宣言外ROM差分')
    for at in prior['protected_root_offsets']:
        need(output[at:at+4]==parent[at:at+4], '共有root/save変更')
    old_start=prior['start'];need(output[old_start:old_start+prior['bundle']['size']]==parent[old_start:old_start+prior['bundle']['size']], '受入PLR1変更')
    plan=copy.deepcopy(prior['allocation'])
    plan['allocations'].append({'name':'pr16_learnset_initial_and_natural','region':region,'start':start,'end_exclusive':start+len(binary),
        'size':len(binary),'alignment':4,'placement':'FIRST_FIT','owner':TASK,'purpose':'owner-gated initial and natural learning',
        'content_sha256':hashlib.sha256(binary).hexdigest(),'sequence':len(plan['allocations']),'gba_start':address,'gba_end_exclusive':address+len(binary)})
    summary=plan['summaries'];summary['allocation_count']+=1;summary['allocated_bytes']+=len(binary);summary['remaining_allocatable_bytes']-=len(binary)
    for usage in summary['region_usage']:
        if usage['region']==region: usage['allocation_count']+=1;usage['allocated_bytes']+=len(binary);usage['remaining_bytes']-=len(binary)
    report={'status':'LINKED_INITIAL_AND_NATURAL_GAME_ENTRYPOINTS','parent':identity(parent),'candidate':identity(bytes(output)),
        'candidate_crc32':f'{zlib.crc32(output)&0xffffffff:08X}','bundle':identity(binary),'start':start,'code_start':address,'code_end':address+len(binary),
        'hooks':patches,'symbols':{k:v for k,v in symbols.items() if k.startswith('Pr16')},'allocation':plan,
        'protected_root_offsets':prior['protected_root_offsets'],'prior_image_unchanged':True,'outside_declared_ranges':0,
        'new_arm_compiles':2,'new_arm_links':1,'old_arm_compiles':0,'gameplay_e2e_accepted':False,'release_ready':False}
    (folder/'candidate.gba').write_bytes(output);write(folder/'link.json',report)
    return report


def host_audit():
    import importlib.util
    spec=importlib.util.spec_from_file_location('progress_vectors',ROOT/'tests/test_pr16_learnset_progress.py')
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
    raw=(WORK/'accepted/runtime-image.bin').read_bytes()
    image=(c.c_uint8*len(raw)).from_buffer_copy(raw)
    oracle=list(s.rows(EVIDENCE/'entrypoints.jsonl'))
    need(len(oracle)==1671, 'owner oracle件数')
    queries=0
    with tempfile.TemporaryDirectory(dir=WORK) as tmp:
        dll=t.library(tmp)
        for row in oracle:
            sid=row['species_id'];pairs=row['level_pairs'];policy=raw[32+sid]
            at,count,_=struct.unpack_from('<IHH',raw,1704+sid*8)
            if policy!=1:
                need(not pairs and at==0xffffffff, '保全枠にlevel span')
                continue
            need(list(struct.iter_unpack('<HB',raw[at:at+count*3]))==[tuple(x) for x in pairs], '受入span/oracle不一致')
            view=t.View(c.cast(c.byref(image,at),t.U8P),count,sid)
            for level in range(1,101):
                expected=[m for m,lv in pairs if lv<=level][-4:]
                out=(c.c_uint16*6)(*([0xDEAD]*6))
                n=dll.Pr16ProgressInitial(c.byref(view),level,out,4);queries+=1
                need(n==len(expected) and list(out)==expected+[0xDEAD]*(6-n), '初期全owner/level不一致')
                expected=[m for m,lv in pairs if lv==level]
                cursor=c.c_uint8(255);actual=[]
                for i in range(len(expected)+1):
                    actual.append(dll.Pr16ProgressNext(c.byref(view),level,i==0,c.byref(cursor)));queries+=1
                need(actual==expected+[0] and cursor.value==255, '自然全owner/level不一致')
    report={'status':'PASS_ALL_LEARNING_OWNERS_100_LEVELS','owners':1483,'levels':100,'queries':queries,
            'identity_only_excluded':188,'input_image_unchanged':bytes(image)==raw,'old_machine_queries':0,'accepted_tests_rerun':0}
    write(WORK/'proof/host-audit.json',report)
    return report


def samples(report):
    oracle={row['species_id']:row for row in s.rows(EVIDENCE/'entrypoints.jsonl')}
    lines=['#include <stdint.h>','#define PR16_CODE_START '+hex(report['code_start'])+'u',
           '#define PR16_CODE_END '+hex(report['code_end'])+'u',
           '#define PR16_INITIAL_DIRECT '+hex(report['hooks'][1]['offset']+BASE+1)+'u',
           '#define PR16_NATURAL_DIRECT '+hex(report['hooks'][3]['offset']+BASE+1)+'u',
           'struct ProgressSample { uint16_t species; uint8_t level,policy,count,next_count; uint16_t moves[4],next[40]; };',
           'static const struct ProgressSample progress_samples[]={']
    for sid,level in SELECTED:
        row=oracle[sid];pairs=row['level_pairs']
        initial=[]
        for mid in [m for m,lv in pairs if lv<=level][-4:]:
            if mid not in initial: initial.append(mid)
        nxt=[m for m,lv in pairs if lv==level]
        lines.append('{'+','.join(map(str,(sid,level,row['policy'],len(initial),len(nxt))))+',{'+','.join(map(str,initial or [0]))+'},{'+','.join(map(str,nxt or [0]))+'}},')
    lines.append('};')
    text='\n'.join(lines)+'\n';(WORK/'proof/pr16_progress_samples.h').write_text(text)
    return text


def verify():
    current_pr(os.environ['GITHUB_SHA']);WORK.mkdir(parents=True,exist_ok=True)
    (WORK/'proof').mkdir();restore()
    protected=[ROOT/p for p in CODE]+list((WORK/'accepted').iterdir())+list(EVIDENCE.iterdir())+[WORK/'parent.gba']
    before=snapshot(protected)
    unit=execute([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_progress','-v'],WORK/'proof/unit.txt')
    text=(WORK/'proof/unit.txt').read_text();need(re.findall(r'^Ran (\d+) tests? in ',text,re.M)==['30'] and re.search(r'\nOK\s*$',text),'新30試験不一致')
    host=host_audit()
    for seed in (11,29):
        execute([sys.executable,'-B',__file__,'link',str(WORK/f'build{seed}')],WORK/f'proof/build{seed}.txt',dict(os.environ,PYTHONHASHSEED=str(seed)))
    first=s.read_json(WORK/'build11/link.json');second=s.read_json(WORK/'build29/link.json')
    need(first==second and (WORK/'build11/progress.bin').read_bytes()==(WORK/'build29/progress.bin').read_bytes(),'独立配置hash不一致')
    data=WORK/'data';data.mkdir()
    for name in ('link.json','progress.bin','pr16_learnset_progress_bindings.h','disassembly.txt'):
        shutil.copyfile(WORK/'build11'/name,data/name)
    write(data/'checkpoint.json',{'status':'NEW_HOST_AND_ARM_PASS_NATIVE_PENDING','source_head':os.environ['GITHUB_SHA'],
          'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':first['candidate'],'files':{p.name:s.identity(p) for p in data.iterdir()},
          'code_bindings':{name:s.identity(ROOT/name) for name in CODE}})
    samples(first)
    binary=WORK/'native'
    execute(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror',
             '-Itools','-I'+str(WORK/'proof'),'tools/mgba_pr16_learnset_progress.c','-lmgba','-o',str(binary)],WORK/'proof/native-compile.txt')
    results=[]
    for seed in (11,29):
        raw=execute([str(binary),str(WORK/f'build{seed}/candidate.gba'),first['candidate']['sha256']],WORK/f'proof/native{seed}.txt',dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
        value=json.loads(raw);need(value['status']=='PASS_INITIAL_AND_NATURAL_ROM_PROBES' and value['samples']==9 and value['candidate_sha256']==first['candidate']['sha256'], 'native出力scope不一致')
        write(WORK/f'proof/native{seed}.json',value);results.append(value)
    need(before==snapshot(protected),'固定入力byte/mtime変更')
    execute([sys.executable,'-B','scripts/pr16_resume.py','check'],WORK/'proof/resume.json')
    execute([sys.executable,'-B','scripts/validate_task_graph.py'],WORK/'proof/task-graph.txt')
    execute(['git','diff','--exit-code'],WORK/'proof/tracked-diff.txt')
    shutil.copyfile(data/'link.json',WORK/'proof/link.json')
    shutil.copyfile(data/'disassembly.txt',WORK/'proof/disassembly.txt')
    report={'status':'PASS_INITIAL_AND_NATURAL_ROM_PROBES','scope':'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E',
        'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'task':TASK,
        'candidate':first['candidate'],'candidate_crc32':first['candidate_crc32'],'focused_tests':30,'host_audit':host,
        'native_results':results,'native_processes':2,'new_arm_compiles':4,'new_arm_links':2,'independent_candidate_hashes_match':True,
        'initial_and_natural_connected':True,'prior_two_entrypoints_unchanged':True,'conditional_consumers_connected':False,
        'gameplay_e2e_accepted':False,'release_ready':False,'active_baseline_changed':False,'issue19_complete':False,
        'accepted_native_reruns':0,'accepted_payload_regenerations':0,'accepted_source_regenerations':0,'old_arm_compiles':0,
        'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,
        'code_bindings':{name:s.identity(ROOT/name) for name in CODE},
        'data_files':{p.name:s.identity(p) for p in data.iterdir()},'proof_files':{p.name:s.identity(p) for p in (WORK/'proof').iterdir()}}
    write(WORK/'proof/verification.json',report);print(json.dumps({'status':report['status'],'candidate':report['candidate']}))


if __name__=='__main__':
    if sys.argv[1:]==['verify']:verify()
    elif len(sys.argv)==3 and sys.argv[1]=='link':print(json.dumps(link(Path(sys.argv[2]))['candidate']))
    else:raise SystemExit('usage: pr16_learnset_progress_verify.py verify|link FOLDER')
