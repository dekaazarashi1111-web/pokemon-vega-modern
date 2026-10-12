#!/usr/bin/env python3
"""実測ABIに束縛し、成功90試験を継承して未完nativeへ進む。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_compact_reuse as reuse
m,n,s,h=reuse.m,reuse.n,reuse.s,reuse.h
WORK,need,write,command=reuse.WORK,reuse.need,reuse.write,reuse.command
CODE=(m.ABI_INPUTS,'scripts/pr16_learnset_compact_bound.py',
      'tests/test_pr16_learnset_compact_bound.py','.github/workflows/pr16-learnset-compact-bound.yml',
      'scripts/pr16_learnset_conditional_abi.py','.github/workflows/pr16-learnset-conditional-abi.yml',
      'overlays/modernization_p07_preserved_layer/runtime.c')


def inherit_abi():
    lock=s.read_json(ROOT/m.ABI_INPUTS)
    for prefix,head,runid,path,conclusion in (
        ('abi',lock['abi']['source_head'],lock['abi']['run_id'],'.github/workflows/pr16-learnset-conditional-abi.yml','success'),
        ('compiler',lock['compiler_head'],lock['compiler_run'],'.github/workflows/pr16-learnset-compact-reuse.yml','failure')):
        run=n.fetch(f'actions/runs/{runid}')
        need(run['status']=='completed' and run['conclusion']==conclusion and run['head_sha']==head
             and run['path']==path and run['head_branch']=='codex/modernization-followup-20260908','固定ABI/compiler run不一致')
        n.download(lock[prefix+'_artifact'],head,WORK/(prefix+'-saved'),lock[prefix+'_files'])
    need(s.read_json(WORK/'abi-saved/abi.json')==lock['abi'],'ABI記録不一致')
    for name in ('scripts/pr16_learnset_compact_reuse.py','tests/test_pr16_learnset_compact_reuse.py',
                 'overlays/modernization_p07_preserved_layer/runtime.c'):
        prior=n.fetch('contents/'+name+'?ref='+lock['compiler_head'])
        raw=(ROOT/name).read_bytes()
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==prior['sha'],'継承compiler/P07 source変更')
    text=(WORK/'compiler-saved/reuse-unit.txt').read_bytes()
    need(text.count(b' ... ok\n')==6 and re.search(rb'Ran 6 tests',text) and b'\nOK\n' in text,'6試験原本不一致')
    for old,new in (('reuse-unit.txt','inherited-compiler-unit.txt'),('failure.json','previous-preimage-failure.json')):
        shutil.copyfile(WORK/'compiler-saved'/old,WORK/'proof'/new)
    shutil.copyfile(WORK/'abi-saved/abi.json',WORK/'proof/abi.json')
    write(WORK/'proof/inherited-compiler.json',{'run_id':lock['compiler_run'],'source_head':lock['compiler_head'],
        'run_conclusion':'failure','tests':6,'executed_again':0,'prior_arm_compiles':3,'prior_arm_links':1,
        'prior_native_processes':0,'failure_stage':'preimage_guard_after_first_link'})
    return lock


def verify():
    n.current_pr(os.environ['GITHUB_SHA'])
    WORK.mkdir(parents=True);(WORK/'proof').mkdir()
    n.inherit();m.inherit_game();cp=reuse.inherit_compact();inherit_abi()
    names=tuple(dict.fromkeys((*CODE,*reuse.CODE,*m.CODE,*n.CODE,*h.CODE)))
    protected=[ROOT/name for name in names];before=n.snapshot(protected)
    command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_compact_bound','-v'],WORK/'proof/bound-unit.txt')
    need(re.search(rb'Ran 6 tests',(WORK/'proof/bound-unit.txt').read_bytes()),'新規ABI試験数不一致')
    h.WORK=WORK/'restore';h.WORK.mkdir();h.restore_progress();h.payloads()
    parent_before=n.snapshot([WORK/'restore/parent.gba'])
    for seed in (11,29):
        command([sys.executable,'-B',__file__,'link',str(WORK/f'build{seed}')],WORK/f'proof/build{seed}.txt',dict(os.environ,PYTHONHASHSEED=str(seed)))
    first=s.read_json(WORK/'build11/link.json');second=s.read_json(WORK/'build29/link.json')
    need(first==second and first['compact_receipt']==cp['receipt'],'独立配置/継承PLC2不一致')
    for name in ('conditional.bin','compact-image.bin'):
        need((WORK/'build11'/name).read_bytes()==(WORK/'build29'/name).read_bytes(),'独立byte不一致')
    data=WORK/'data';data.mkdir()
    for name in ('link.json','conditional.bin','compact-image.bin','compact-receipt.json','pr16_learnset_conditional_bindings.h','disassembly.txt'):
        shutil.copyfile(WORK/'build11'/name,data/name)
    shutil.copyfile(data/'link.json',WORK/'proof/link.json')
    n.samples(first)
    write(WORK/'proof/link-checkpoint.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'independent_candidate_hashes_match':True,'new_arm_compiles':6,'new_arm_links':2,
        'candidate':first['candidate'],'data_files':{p.name:s.identity(p) for p in data.iterdir()},
        'code_bindings':{name:s.identity(ROOT/name) for name in names}})
    binary=WORK/'native'
    command(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK/'proof'),
        'tools/mgba_pr16_learnset_conditional.c','-lmgba','-o',str(binary)],WORK/'proof/native-compile.txt')
    results=[]
    for seed in (11,29):
        result=json.loads(command([str(binary),str(WORK/f'build{seed}/candidate.gba'),first['candidate']['sha256']],
            WORK/f'proof/native{seed}.txt',dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')))
        need(result['status']=='PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS' and result['samples']==len(n.SELECTED),'native scope不一致')
        write(WORK/f'proof/native{seed}.json',result);results.append(result)
    need(before==n.snapshot(protected) and parent_before==n.snapshot([WORK/'restore/parent.gba']),'入力byte/mtime変更')
    command([sys.executable,'-B','scripts/pr16_resume.py','check'],WORK/'proof/resume.json')
    command([sys.executable,'-B','scripts/validate_task_graph.py'],WORK/'proof/task-graph.txt')
    command(['git','diff','--exit-code'],WORK/'proof/tracked-diff.txt')
    report={'status':'PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS','scope':'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E',
        'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'task':m.TASK,
        'candidate':first['candidate'],'candidate_crc32':first['candidate_crc32'],'focused_tests':6,
        'compact_audit':cp['audit'],'compact_receipt':cp['receipt'],
        'inherited_compact_run':cp['run_id'],'inherited_compact_tests':25,'inherited_compact_queries':15039,
        'inherited_host_run':35715106357,'inherited_host_tests':41,'inherited_host_queries':622669,
        'inherited_game_run':m.FAIL_RUN,'inherited_game_tests':18,'accepted_tests_rerun':0,
        'inherited_compiler_run':35720416968,'inherited_compiler_tests':6,
        'native_results':results,'native_processes':2,'new_arm_compiles':6,'new_arm_links':2,
        'independent_candidate_hashes_match':True,'four_conditional_entrypoints_connected':True,
        'p03_evolution_dispatch_unchanged':True,'p07_archive_wrapper_preserved':True,
        'game_tutor_connected':False,'archive_rebound':False,'gameplay_e2e_accepted':False,
        'release_ready':False,'active_baseline_changed':False,'issue19_complete':False,
        'accepted_native_reruns':0,'accepted_payload_regenerations':0,'accepted_source_regenerations':0,
        'old_arm_compiles':0,'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,
        'code_bindings':{name:s.identity(ROOT/name) for name in names},
        'data_files':{p.name:s.identity(p) for p in data.iterdir()},
        'proof_files':{p.name:s.identity(p) for p in (WORK/'proof').iterdir()}}
    write(WORK/'proof/verification.json',report)
    print(json.dumps({'status':report['status'],'candidate':report['candidate']}))


if __name__=='__main__':
    if sys.argv[1:]==['verify']:
        try:verify()
        except Exception as exc:
            (WORK/'proof').mkdir(parents=True,exist_ok=True)
            write(WORK/'proof/failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                'error':str(exc).replace(str(ROOT),'$REPO')})
            raise
    elif len(sys.argv)==3 and sys.argv[1]=='link':print(json.dumps(reuse.link(Path(sys.argv[2]))['candidate']))
    else:raise SystemExit('usage: pr16_learnset_compact_bound.py verify|link FOLDER')
