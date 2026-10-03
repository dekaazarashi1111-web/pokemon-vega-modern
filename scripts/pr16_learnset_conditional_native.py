#!/usr/bin/env python3
"""保存PLC1/PLR1を継承し、新4入口だけを配置・ARM/native検証する。"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_runtime as r
import pr16_learnset_conditional_host as h
from pr16_learnset_floette_verify import download,snapshot
from pr16_learnset_payload_verify import current_pr
from pr16_wiki_reconcile import fetch
WORK=ROOT/'.local/pr16-learnset-conditional-native'
LOCK='content/modernization/pr16_learnset_conditional_host_inputs.json'
TASK='USER-20260922-LEARNSET-CONDITIONAL'
CODE=(LOCK,'src/modernization/pr16_learnset_conditional_game.h',
      'src/modernization/pr16_learnset_conditional_game.c',
      'tests/fixtures/pr16_learnset_conditional_bindings.h',
      'tests/fixtures/pr16_learnset_conditional_fixture.c',
      'tests/test_pr16_learnset_conditional_game.py',
      'scripts/pr16_learnset_conditional_native.py',
      'tools/mgba_pr16_learnset_conditional.c',
      '.github/workflows/pr16-learnset-conditional-native.yml')
SELECTED=((13,50),(128,50),(129,50),(140,50),(390,50),(355,100),
          (649,9),(1029,50),(1670,48),(887,10),(1621,10),(918,10),(0,10),(1268,10),(257,10))
need=r.need
identity=h.old.saved.identity
BASE=0x08000000

def write(path,value):path.write_bytes(s.encode(value))

def command(args,log,env=None):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240,env=env)
    log.write_bytes(p.stdout+p.stderr)
    need(p.returncode==0,'工程失敗 '+str(args[:3])+'\n'+p.stderr.decode(errors='replace')[-2200:])
    return p.stdout

def inherit():
    lock=s.read_json(ROOT/LOCK)
    run=fetch('actions/runs/'+str(lock['run_id']))
    jobs=fetch('actions/runs/'+str(lock['run_id'])+'/jobs?per_page=100')['jobs']
    need(run['head_sha']==lock['source_head'] and run['head_branch']=='codex/modernization-followup-20260908'
         and run['status']=='completed' and run['conclusion']=='success'
         and run['path']=='.github/workflows/pr16-learnset-conditional.yml','受入host run不一致')
    need(len(jobs)==2 and {j['name'] for j in jobs}=={'conditional-host','conditional-context'}
         and all(j['conclusion']=='success' and all(x['conclusion']=='success' for x in j['steps']) for j in jobs),'受入host jobs不一致')
    for kind in ('proof','data'):
        download(lock['artifacts']['pr16-learnset-conditional-host-'+kind],lock['source_head'],WORK/('host-'+kind),lock[kind+'_files'])
    cp=s.read_json(WORK/'host-proof/host-checkpoint.json')
    need(cp['focused_tests']==41 and cp['host_audit']['total_queries']==622669,'継承件数不一致')
    for name,binding in cp['code_bindings'].items():s.bound(ROOT/name,binding)
    write(WORK/'proof/inherited-host.json',{'run_id':lock['run_id'],'source_head':lock['source_head'],
          'tests':41,'queries':622669,'executed_again':0,'code_bindings_unchanged':True})
    return cp

def bindings(prior):
    dis=(ROOT/'content/modernization/pr16_learnset_runtime_evidence/disassembly.txt').read_text()
    match=re.search(r'^([0-9a-f]+) <Pr16ResolveLearnsetOwner>:',dis,re.M)
    need(match is not None,'保存owner symbol欠落')
    owner=int(match[1],16)
    need(prior['code_start']<=owner<prior['code_end'] and owner%2==0,'保存owner範囲不一致')
    accepted=(WORK/'restore/progress/pr16_learnset_progress_bindings.h').read_text()
    return '#ifndef PR16_CONDITIONAL_BINDINGS_H\n#define PR16_CONDITIONAL_BINDINGS_H\n'+accepted+f'''
extern const uint8_t Pr16ConditionalImage[];
#define PR16_CONDITIONAL_IMAGE Pr16ConditionalImage
#define PR16_CONDITIONAL_IMAGE_SIZE 115282u
#define PR16_READ_CONDITIONAL Pr16ReadLearnsetConditional
#define PR16_OWNER_GATE ((uint8_t (*)(const uint8_t *,uint16_t,uint16_t,uint8_t,uint16_t *)){hex(owner|1)}u)
#define PR16_MEMORY_MODE ((volatile uint8_t *)0x0203EC00u)
#define PR16_PARENT_ARCHIVE_MOVES ((uint8_t (*)(void *,uint16_t *))0x0954B281u)
#endif
'''

def link(folder):
    folder.mkdir()
    parent=(WORK/'restore/parent.gba').read_bytes()
    prior=s.read_json(WORK/'restore/progress/link.json')
    need(identity(parent)==prior['candidate'],'新配置親不一致')
    image=(WORK/'host-data/conditional-image.bin').read_bytes()
    s.bound(WORK/'host-data/conditional-image.bin',s.read_json(ROOT/LOCK)['data_files']['conditional-image.bin'])
    start,region=r.free_span(prior['allocation'],((len(image)+3)&~3)+8192)
    base=BASE+start;rel=folder.relative_to(ROOT).as_posix()
    header=folder/'pr16_learnset_conditional_bindings.h'
    header.write_text(bindings(s.read_json(WORK/'restore/runtime/link.json')))
    (folder/'image.S').write_text('.section .rodata.plc1,"a",%progbits\n.balign 4\n.global Pr16ConditionalImage\nPr16ConditionalImage:\n.incbin "'+str(WORK/'host-data/conditional-image.bin')+'"\n')
    (folder/'conditional.ld').write_text('SECTIONS { . = '+hex(base)+'; .image : { *(.rodata.plc1) } . = ALIGN(4); .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } ASSERT(SIZEOF(.data)==0,"data forbidden") ASSERT(SIZEOF(.bss)==0,"BSS forbidden") }\n')
    flags=['-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin',
           '-fno-common','-fno-pic','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
           '-Wall','-Wextra','-Werror','-Isrc/modernization','-I'+rel]
    objects=[]
    for name in ('pr16_learnset_conditional','pr16_learnset_conditional_game'):
        obj=rel+'/'+name+'.o';objects.append(obj)
        h.old.command(['arm-none-eabi-gcc',*flags,'-include',str(header),'-c','src/modernization/'+name+'.c','-o',obj])
    h.old.command(['arm-none-eabi-gcc',*flags,'-c',rel+'/image.S','-o',rel+'/image.o'])
    elf=rel+'/conditional.elf'
    h.old.command(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-T,'+rel+'/conditional.ld',*objects,rel+'/image.o','-o',elf])
    need(not h.old.command(['arm-none-eabi-nm','-u',elf]).strip(),'未解決symbol')
    h.old.command(['arm-none-eabi-objcopy','-O','binary',elf,rel+'/conditional.bin'])
    (folder/'disassembly.txt').write_bytes(h.old.command(['arm-none-eabi-objdump','-d',elf]))
    symbols={}
    for line in h.old.command(['arm-none-eabi-nm','-n',elf]).decode().splitlines():
        parts=line.split()
        if len(parts)==3:symbols[parts[2]]=int(parts[0],16)
    blob=(folder/'conditional.bin').read_bytes();code_start=base+((len(image)+3)&~3)
    need(blob[:len(image)]==image and len(image)<len(blob)<=len(image)+8196 and parent[start:start+len(blob)]==b'\xff'*len(blob),'配置/容量/保存PLC1違反')
    hooks=(('Pr16_GameAfterEvolution',0x1114120,'8446f8b562465423'),
           ('Pr16_GameGetConditionalRelearnerMoves',0x11141D4,'004b184781b25409'),
           ('Pr16_GameGetEggMoves',0x451EC,'004b1847adb15409'),
           ('Pr16_GameGetAllEggMoves',0x10EB970,'004b1847e5485309'))
    import pr16_evolution_learning_repair as evo
    need(parent[evo.START:evo.START+len(evo.DISPATCH)]==evo.DISPATCH,'P03 dispatcher不一致')
    out=bytearray(parent);out[start:start+len(blob)]=blob;patches=[]
    for name,at,expected in hooks:
        need(parent[at:at+8].hex()==expected,'固定4入口preimage不一致: '+hex(at)+' '+parent[at:at+8].hex())
        target=symbols[name];need(at%4==0 and code_start<=target<base+len(blob) and target%2==0,'Thumb関数/alignment不一致')
        after=b'\x00\x4b\x18\x47'+struct.pack('<I',target|1)
        out[at:at+8]=after;patches.append({'symbol':name,'offset':at,'before':expected,'after':after.hex(),'target':target|1})
    rollback=bytearray(out);rollback[start:start+len(blob)]=b'\xff'*len(blob)
    for p in patches:rollback[p['offset']:p['offset']+8]=bytes.fromhex(p['before'])
    need(bytes(rollback)==parent,'宣言外ROM変更')
    for phase,binary in (('runtime','runtime-bundle.bin'),('progress','progress.bin')):
        old=s.read_json(WORK/'restore'/phase/'link.json');at=old['start'];size=old['bundle']['size']
        need(out[at:at+size]==parent[at:at+size],'受入PLR1/通常level-up変更')
    for at in prior['protected_root_offsets']:need(out[at:at+4]==parent[at:at+4],'共有root変更')
    need(out[evo.START:evo.START+len(evo.DISPATCH)]==parent[evo.START:evo.START+len(evo.DISPATCH)] and out[evo.ENTRY:evo.ENTRY+8]==parent[evo.ENTRY:evo.ENTRY+8],'進化振分け変更')
    plan=copy.deepcopy(prior['allocation']);touched=[]
    for row in plan['allocations']:
        if any(row['start']<=p['offset']<row['end_exclusive'] for p in patches):
            row['content_sha256']=hashlib.sha256(out[row['start']:row['end_exclusive']]).hexdigest();touched.append(row['name'])
    plan['allocations'].append({'name':'pr16_conditional_four_consumers','region':region,'start':start,
        'end_exclusive':start+len(blob),'size':len(blob),'alignment':4,'placement':'FIRST_FIT','owner':TASK,
        'purpose':'PLC1 evolution/reminder/egg/shared conditional entrypoints','content_sha256':hashlib.sha256(blob).hexdigest(),
        'sequence':len(plan['allocations']),'gba_start':base,'gba_end_exclusive':base+len(blob)})
    summary=plan['summaries'];summary['allocation_count']+=1;summary['allocated_bytes']+=len(blob);summary['remaining_allocatable_bytes']-=len(blob)
    for usage in summary['region_usage']:
        if usage['region']==region:usage['allocation_count']+=1;usage['allocated_bytes']+=len(blob);usage['remaining_bytes']-=len(blob)
    report={'status':'LINKED_FOUR_CONDITIONAL_ENTRYPOINTS','parent':identity(parent),'candidate':identity(bytes(out)),
        'candidate_crc32':f'{zlib.crc32(out)&0xffffffff:08X}','bundle':identity(blob),'image':identity(image),
        'start':start,'code_start':code_start,'code_end':base+len(blob),'hooks':patches,
        'symbols':{k:v for k,v in symbols.items() if k.startswith('Pr16')},'allocation':plan,
        'protected_root_offsets':prior['protected_root_offsets'],'prior_image_unchanged':True,'outside_declared_ranges':0,
        'p03_evolution_dispatch_unchanged':True,'updated_allocation_hashes':touched,
        'old_arm_compiles':0,'game_tutor_connected':False,'archive_rebound':False,
        'gameplay_e2e_accepted':False,'release_ready':False}
    (folder/'candidate.gba').write_bytes(out);write(folder/'link.json',report)
    return report

def samples(report):
    parent,floette=WORK/'restore/parent',WORK/'restore/floette'
    index={(x['species_id'],x['consumer']):x for x in s.rows(floette/'consumer-index.jsonl')}
    pools={False:{p.name:p.read_bytes() for p in parent.glob('*.bin')},True:{p.name:p.read_bytes() for p in floette.glob('*.bin')}}
    policies=(floette/'owner-policies.bin').read_bytes()
    def raw(sid,family):
        p=index[sid,family]['payload']
        return pools[sid==1029][p['file']][p['offset']:p['offset']+p['size']] if p else b''
    def u16(data):return [v[0] for v in struct.iter_unpack('<H',data)]
    def lists(sid,level):
        if policies[sid]!=1:return [[],[],[],[]]
        egg=raw(sid,'egg')[2:]
        if egg.endswith(b'\xff\xff'):egg=egg[:-2]
        egg=u16(egg);evo=u16(raw(sid,'evolution'));rem=u16(raw(sid,'reminder'))
        levels=list(struct.iter_unpack('<HB',raw(sid,'level_up')[:-3]));shared=u16(raw(sid,'shared_egg'))
        return [list(dict.fromkeys(egg)),list(dict.fromkeys(egg+shared)),
                list(dict.fromkeys(evo+[m for m,l in levels if l<=level]+rem)),evo+[m for m,l in levels if l==level]]
    max_shared=0
    for sid in range(1671):
        row=lists(sid,100);max_shared=max(max_shared,len(row[1]));need(len(row[1])<=40,'共有候補容量超過')
    lines=['#include <stdint.h>',f'#define PR16_CODE_START {hex(report["code_start"])}u',
           f'#define PR16_CODE_END {hex(report["code_end"])}u',
           'struct ConditionalSample { uint16_t species; uint8_t level,policy; uint8_t count[4]; uint16_t moves[4][50]; };',
           'static const struct ConditionalSample conditional_samples[]={']
    for sid,level in SELECTED:
        rows=lists(sid,level)
        need(all(not 1000<=m<=1003 for row in rows for m in row),'native known fixture collision')
        arrays=','.join('{'+','.join(map(str,row or [0]))+'}' for row in rows)
        lines.append('{'+','.join(map(str,(sid,level,policies[sid])))+',{'+','.join(map(str,map(len,rows)))+'},{'+arrays+'}},')
    lines.append('};');(WORK/'proof/pr16_conditional_samples.h').write_text('\n'.join(lines)+'\n')
    write(WORK/'proof/shared-capacity.json',{'owners':1671,'maximum_union':max_shared,'capacity':40,'status':'PASS'})

def verify():
    current_pr(os.environ['GITHUB_SHA']);WORK.mkdir(parents=True);(WORK/'proof').mkdir()
    inherit();h.WORK=WORK/'restore';h.WORK.mkdir();h.restore_progress();h.payloads()
    protected=[ROOT/n for n in (*CODE,*h.CODE)]+[p for p in WORK.glob('host-*/*') if p.is_file()]+[WORK/'restore/parent.gba']
    before=snapshot(protected)
    unit=command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_conditional_game','-v'],WORK/'proof/game-unit.txt')
    need(re.search(rb'Ran 18 tests', (WORK/'proof/game-unit.txt').read_bytes()),'新規試験数不一致')
    for seed in (11,29):command([sys.executable,'-B',__file__,'link',str(WORK/f'build{seed}')],WORK/f'proof/build{seed}.txt',dict(os.environ,PYTHONHASHSEED=str(seed)))
    first=s.read_json(WORK/'build11/link.json');second=s.read_json(WORK/'build29/link.json')
    need(first==second and (WORK/'build11/conditional.bin').read_bytes()==(WORK/'build29/conditional.bin').read_bytes(),'独立候補hash不一致')
    data=WORK/'data';data.mkdir()
    for name in ('link.json','conditional.bin','pr16_learnset_conditional_bindings.h','disassembly.txt'):shutil.copyfile(WORK/'build11'/name,data/name)
    samples(first)
    binary=WORK/'native'
    command(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK/'proof'),
             'tools/mgba_pr16_learnset_conditional.c','-lmgba','-o',str(binary)],WORK/'proof/native-compile.txt')
    results=[]
    for seed in (11,29):
        result=json.loads(command([str(binary),str(WORK/f'build{seed}/candidate.gba'),first['candidate']['sha256']],WORK/f'proof/native{seed}.txt',dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')))
        need(result['status']=='PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS' and result['samples']==len(SELECTED),'native scope不一致')
        write(WORK/f'proof/native{seed}.json',result);results.append(result)
    need(before==snapshot(protected),'入力byte/mtime変更')
    command([sys.executable,'-B','scripts/pr16_resume.py','check'],WORK/'proof/resume.json')
    command([sys.executable,'-B','scripts/validate_task_graph.py'],WORK/'proof/task-graph.txt')
    command(['git','diff','--exit-code'],WORK/'proof/tracked-diff.txt')
    report={'status':'PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS','scope':'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E',
        'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'task':TASK,
        'candidate':first['candidate'],'candidate_crc32':first['candidate_crc32'],'focused_tests':18,
        'inherited_host_run':35715106357,'inherited_tests':41,'inherited_queries':622669,'accepted_tests_rerun':0,
        'native_results':results,'native_processes':2,'new_arm_compiles':4,'new_arm_links':2,'independent_candidate_hashes_match':True,
        'four_conditional_entrypoints_connected':True,'p03_evolution_dispatch_unchanged':True,
        'game_tutor_connected':False,'archive_rebound':False,'gameplay_e2e_accepted':False,'release_ready':False,
        'active_baseline_changed':False,'issue19_complete':False,'accepted_native_reruns':0,
        'accepted_payload_regenerations':0,'accepted_source_regenerations':0,'old_arm_compiles':0,
        'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,
        'code_bindings':{n:s.identity(ROOT/n) for n in (*CODE,*h.CODE)},
        'data_files':{p.name:s.identity(p) for p in data.iterdir()},'proof_files':{p.name:s.identity(p) for p in (WORK/'proof').iterdir()}}
    write(WORK/'proof/verification.json',report);print(json.dumps({'status':report['status'],'candidate':report['candidate']}))

if __name__=='__main__':
    if sys.argv[1:]==['verify']:
        try:verify()
        except Exception as exc:
            (WORK/'proof').mkdir(parents=True,exist_ok=True)
            write(WORK/'proof/failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),'error':str(exc).replace(str(ROOT),'$REPO')})
            raise
    elif len(sys.argv)==3 and sys.argv[1]=='link':print(json.dumps(link(Path(sys.argv[2]))['candidate']))
    else:raise SystemExit('usage: pr16_learnset_conditional_native.py verify|link FOLDER')
