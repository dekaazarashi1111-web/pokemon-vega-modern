#!/usr/bin/env python3
"""成功25試験/15039照合を再利用し、freestanding ARMリンクから継続。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_learnset_compact_native as m
n, s, h = m.n, m.s, m.h
WORK, need, write, command = m.WORK, m.need, m.write, m.command
LOCK = 'content/modernization/pr16_learnset_compact_host_inputs.json'
CODE = (LOCK, 'scripts/pr16_learnset_compact_reuse.py',
        'tests/test_pr16_learnset_compact_reuse.py', '.github/workflows/pr16-learnset-compact-reuse.yml')


def compile_args(args):
    result = list(args)
    if result and result[0] == 'arm-none-eabi-gcc' and '-c' in result and '-fno-jump-tables' not in result:
        result.append('-fno-jump-tables')
    return result


def link(folder):
    """既存配置検査を維持し、C compileだけjump-table補助関数を禁止。"""
    original = h.old.command
    h.old.command = lambda args: original(compile_args(args))
    try:
        report = m.link(folder)
    finally:
        h.old.command = original
    report['compiler_options_added'] = ['-fno-jump-tables']
    write(folder/'link.json',report)
    return report


def inherit_compact():
    lock = s.read_json(ROOT/LOCK)
    run = n.fetch(f"actions/runs/{lock['run_id']}")
    need(run['status'] == 'completed' and run['conclusion'] == 'failure'
         and run['head_sha'] == lock['source_head']
         and run['path'] == '.github/workflows/pr16-learnset-compact-native.yml', 'PLC2先行run不一致')
    n.download(lock['artifact'],lock['source_head'],WORK/'compact-host-proof',lock['proof_files'])
    cp = s.read_json(WORK/'compact-host-proof/compact-host-checkpoint.json')
    need(cp['source_head'] == lock['source_head'] and cp['run_id'] == lock['run_id']
         and cp['focused_tests'] == 25 and cp['audit']['queries'] == 15039
         and cp['audit']['status'] == 'PASS', 'PLC2成功原本不一致')
    for name,binding in cp['code_bindings'].items(): s.bound(ROOT/name,binding)
    for name,binding in cp['proof_files'].items():
        s.bound(WORK/'compact-host-proof'/name,binding)
        shutil.copyfile(WORK/'compact-host-proof'/name,WORK/'proof'/name)
    text = (WORK/'proof/compact-unit.txt').read_bytes()
    need(text.count(b' ... ok\n') == 25 and re.search(rb'Ran 25 tests',text) and b'\nOK\n' in text, '25試験の成功不一致')
    failure = s.read_json(WORK/'compact-host-proof/failure.json')
    need('__gnu_thumb1_case_uqi' in failure['error'], '先行リンク失敗不一致')
    shutil.copyfile(WORK/'compact-host-proof/failure.json',WORK/'proof/previous-compact-failure.json')
    shutil.copyfile(WORK/'compact-host-proof/compact-host-checkpoint.json',WORK/'proof/compact-host-checkpoint.json')
    record = {'run_id':lock['run_id'],'source_head':lock['source_head'],'run_conclusion':'failure',
              'focused_tests':25,'host_queries':15039,'focused_tests_executed':0,'host_queries_executed':0,
              'prior_arm_compiles':3,'prior_arm_link_attempts':1,'prior_arm_links_succeeded':0,
              'prior_native_processes':0,'code_bindings_unchanged':True}
    write(WORK/'proof/inherited-compact.json',record)
    return cp


def verify():
    n.current_pr(os.environ['GITHUB_SHA'])
    WORK.mkdir(parents=True); (WORK/'proof').mkdir()
    n.inherit(); m.inherit_game(); cp = inherit_compact()
    names = tuple(dict.fromkeys((*CODE,*m.CODE,*n.CODE,*h.CODE)))
    protected = [ROOT/name for name in names]
    before = n.snapshot(protected)
    command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_compact_reuse','-v'],WORK/'proof/reuse-unit.txt')
    need(re.search(rb'Ran 6 tests',(WORK/'proof/reuse-unit.txt').read_bytes()), '新規compiler-option試験数不一致')
    h.WORK = WORK/'restore'; h.WORK.mkdir(); h.restore_progress(); h.payloads()
    parent_before = n.snapshot([WORK/'restore/parent.gba'])
    for seed in (11,29):
        command([sys.executable,'-B',__file__,'link',str(WORK/f'build{seed}')],WORK/f'proof/build{seed}.txt',dict(os.environ,PYTHONHASHSEED=str(seed)))
    first = s.read_json(WORK/'build11/link.json'); second = s.read_json(WORK/'build29/link.json')
    need(first == second and first['compact_receipt'] == cp['receipt'], '独立配置/継承PLC2不一致')
    for name in ('conditional.bin','compact-image.bin'):
        need((WORK/'build11'/name).read_bytes() == (WORK/'build29'/name).read_bytes(), '独立byte不一致')
    data = WORK/'data'; data.mkdir()
    for name in ('link.json','conditional.bin','compact-image.bin','compact-receipt.json','pr16_learnset_conditional_bindings.h','disassembly.txt'):
        shutil.copyfile(WORK/'build11'/name,data/name)
    shutil.copyfile(data/'link.json',WORK/'proof/link.json')
    n.samples(first)
    binary = WORK/'native'
    command(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK/'proof'),
             'tools/mgba_pr16_learnset_conditional.c','-lmgba','-o',str(binary)],WORK/'proof/native-compile.txt')
    results = []
    for seed in (11,29):
        result = json.loads(command([str(binary),str(WORK/f'build{seed}/candidate.gba'),first['candidate']['sha256']],
            WORK/f'proof/native{seed}.txt',dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')))
        need(result['status'] == 'PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS' and result['samples'] == len(n.SELECTED), 'native scope不一致')
        write(WORK/f'proof/native{seed}.json',result); results.append(result)
    need(before == n.snapshot(protected) and parent_before == n.snapshot([WORK/'restore/parent.gba']), '入力byte/mtime変更')
    command([sys.executable,'-B','scripts/pr16_resume.py','check'],WORK/'proof/resume.json')
    command([sys.executable,'-B','scripts/validate_task_graph.py'],WORK/'proof/task-graph.txt')
    command(['git','diff','--exit-code'],WORK/'proof/tracked-diff.txt')
    report = {'status':'PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS','scope':'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E',
        'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'task':m.TASK,
        'candidate':first['candidate'],'candidate_crc32':first['candidate_crc32'],'focused_tests':6,
        'compact_audit':cp['audit'],'compact_receipt':cp['receipt'],
        'inherited_compact_run':cp['run_id'],'inherited_compact_tests':25,'inherited_compact_queries':15039,
        'inherited_host_run':35715106357,'inherited_host_tests':41,'inherited_host_queries':622669,
        'inherited_game_run':m.FAIL_RUN,'inherited_game_tests':18,'accepted_tests_rerun':0,
        'native_results':results,'native_processes':2,'new_arm_compiles':6,'new_arm_links':2,
        'independent_candidate_hashes_match':True,'four_conditional_entrypoints_connected':True,
        'p03_evolution_dispatch_unchanged':True,'game_tutor_connected':False,'archive_rebound':False,
        'gameplay_e2e_accepted':False,'release_ready':False,'active_baseline_changed':False,'issue19_complete':False,
        'accepted_native_reruns':0,'accepted_payload_regenerations':0,'accepted_source_regenerations':0,
        'old_arm_compiles':0,'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,
        'code_bindings':{name:s.identity(ROOT/name) for name in names},
        'data_files':{p.name:s.identity(p) for p in data.iterdir()},
        'proof_files':{p.name:s.identity(p) for p in (WORK/'proof').iterdir()}}
    write(WORK/'proof/verification.json',report)
    print(json.dumps({'status':report['status'],'candidate':report['candidate']}))


if __name__ == '__main__':
    if sys.argv[1:] == ['verify']:
        try: verify()
        except Exception as exc:
            (WORK/'proof').mkdir(parents=True,exist_ok=True)
            write(WORK/'proof/failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                'error':str(exc).replace(str(ROOT),'$REPO')})
            raise
    elif len(sys.argv) == 3 and sys.argv[1] == 'link': print(json.dumps(link(Path(sys.argv[2]))['candidate']))
    else: raise SystemExit('usage: pr16_learnset_compact_reuse.py verify|link FOLDER')
