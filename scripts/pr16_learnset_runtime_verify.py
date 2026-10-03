#!/usr/bin/env python3
"""新2入口だけの配置・全owner C・ARM/mGBA検証。旧受入工程は再実行しない。"""
from __future__ import annotations
import ctypes as c
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from tools import pr16_learnset_runtime as r
from tools import pr16_learnset_successor as s
from pr16_learnset_floette_verify import download, identities, snapshot
from pr16_learnset_payload_verify import current_pr
import pr16_learnset_runtime_link as linker
from tests.test_pr16_learnset_runtime import View, library

WORK = ROOT/'.local/pr16-learnset-runtime'
EXPECTED_IMAGE = {'size':108008, 'sha256':'5ebbc35c546370bc1c87d48d5d147dc93a6aba2739d9ab9d0825bbf8f307450c'}
CODE = ('tools/pr16_learnset_runtime.py', 'src/modernization/pr16_learnset_runtime.h',
        'src/modernization/pr16_learnset_runtime.c', 'src/modernization/pr16_learnset_game.c',
        'src/modernization/pr16_learnset_owner.h', 'src/modernization/pr16_learnset_owner.c',
        'tests/test_pr16_learnset_runtime.py', 'scripts/pr16_learnset_runtime_link.py',
        'scripts/pr16_learnset_runtime_verify.py', 'tools/mgba_pr16_learnset_runtime.c',
        'tools/mgba_battle_core_smoke.c', 'tools/mgba_ai_fixture_runner.c',
        '.github/workflows/pr16-learnset-runtime.yml',
        'tools/pr16_learnset_successor.py', 'scripts/pr16_learnset_floette_verify.py',
        'scripts/pr16_learnset_payload_verify.py', 'scripts/pr16_wiki_reconcile.py',
        'scripts/pr16_saved_recipe.py', r.PARENT, r.FLOETTE, r.ALLOCATION, linker.NORMAL)
need = r.need


def oracle(parent: Path, floette: Path) -> list[dict]:
    """新image/packing関数を参照せず、固定binaryの元spanを読み取る。"""
    entries = {(x['species_id'], x['consumer']):x for x in s.rows(floette/'consumer-index.jsonl')}
    policies = (floette/'owner-policies.bin').read_bytes()
    pools = {False:{p.name:p.read_bytes() for p in parent.glob('*.bin')},
             True:{p.name:p.read_bytes() for p in floette.glob('*.bin')}}
    result = []
    for sid, policy in enumerate(policies):
        owner = {'species_id':sid, 'policy':policy, 'species_key':entries[sid,'level_up']['species_key'],
                 'level_bytes':'', 'level_pairs':[], 'machine_bytes':bytes(16).hex()}
        if policy == 1:
            for consumer in ('level_up','machine'):
                span = entries[sid,consumer]['payload']
                raw = pools[sid==1029][span['file']][span['offset']:span['offset']+span['size']]
                if consumer == 'level_up':
                    need(raw[-3:]==b'\0\0\xff', '元level終端不一致')
                    owner['level_bytes'] = raw[:-3].hex()
                    owner['level_pairs'] = [list(pair) for pair in struct.iter_unpack('<HB', raw[:-3])]
                else:
                    need(len(raw)==16, '元machine stride不一致')
                    owner['machine_bytes'] = raw.hex()
        result.append(owner)
    return result


def audit(folder: Path, expected: list[dict]) -> dict:
    """配置imageを実Cへ渡し、全species/全128slotと元spanを照合する。"""
    raw = (folder/'runtime-image.bin').read_bytes()
    buffer = (c.c_uint8*len(raw)).from_buffer_copy(raw)
    copies = s.read_json(folder/'receipt.json')['copies']
    for entry in copies:
        parent = WORK/('floette' if entry['arena']=='FLOETTE_DELTA' else 'parent')
        original = (parent/entry['file']).read_bytes(); at = entry['image_offset']
        need(raw[at:at+len(original)]==original, '元poolの全byteコピー不一致')
    with tempfile.TemporaryDirectory(dir=WORK) as destination:
        dll = library(destination)
        for owner in expected:
            sid = owner['species_id']; policy = owner['policy']
            action = 1 if policy==1 else 2 if policy<5 else 3
            for consumer in (3,4):
                view = View()
                need(dll.Pr16ReadLearnsetRuntime(buffer,len(raw),sid,consumer,c.byref(view))==action
                     and view.owner==sid, '配置後C owner/action不一致')
                if action==1:
                    want = bytes.fromhex(owner['level_bytes' if consumer==3 else 'machine_bytes'])
                    count = len(owner['level_pairs']) if consumer==3 else 128
                    need(view.count==count and c.string_at(view.bytes,len(want))==want, '配置後C span/level順序不一致')
                else:
                    need(not view.bytes and view.count==0, '188保全ownerへspan漏洩')
            out = (c.c_uint16*42)(*([0xDEAD]*42))
            moves = [pair[0] for pair in owner['level_pairs']]
            need(dll.Pr16RuntimeLevelMoves(buffer,len(raw),sid,out,40)==len(moves)
                 and list(out)==moves+[0xDEAD]*(42-len(moves)), '全species copy/canary不一致')
            bits = int.from_bytes(bytes.fromhex(owner['machine_bytes']),'little')
            for slot in range(128):
                need(dll.Pr16RuntimeMachineAllowed(buffer,len(raw),sid,slot)==((bits>>slot)&1), '全species/slot不一致')
        need(bytes(buffer)==raw, 'C呼出しによる入力書換え')
    return {'status':'PASS_PLACED_C_AGAINST_ACCEPTED_SPANS', 'owners':len(expected),
            'span_queries':len(expected)*2, 'level_copy_queries':len(expected),
            'machine_bit_queries':len(expected)*128, 'copied_pools':len(copies),
            'learning_owners':sum(x['policy']==1 for x in expected), 'identity_only_preserved':188,
            'all_input_bytes_unchanged':True, 'all_output_canaries_unchanged':True,
            'archive_moves_granted':0, 'old_acceptance_tests_rerun':0}


def samples(folder: Path, expected: list[dict], report: dict) -> list[int]:
    selected = {1,10,649,1029,1670,412}
    selected.add(max(expected,key=lambda x:len(x['level_pairs']))['species_id'])
    for policy in range(2,8):
        selected.add(next(x['species_id'] for x in expected if x['policy']==policy))
    lines = ['#include <stdint.h>', '#define PR16_CODE_START '+hex(report['code_start'])+'U',
             '#define PR16_CODE_END '+hex(report['code_end'])+'U',
             'struct Pr16Sample { uint16_t species; uint8_t count; uint16_t moves[40]; uint8_t bits[16]; };',
             'static const struct Pr16Sample pr16_samples[] = {']
    for sid in sorted(selected):
        row = expected[sid]; moves = [x[0] for x in row['level_pairs']]
        lines.append('{'+str(sid)+','+str(len(moves))+',{'+','.join(map(str,moves or [0]))+'},{'+
                     ','.join(str(x) for x in bytes.fromhex(row['machine_bytes']))+'}},')
    lines.append('};\n')
    (folder/'pr16_learnset_samples.h').write_text('\n'.join(lines))
    return sorted(selected)


def execute(args: list[str], log: Path, *, env: dict|None=None) -> bytes:
    result = subprocess.run(args,cwd=ROOT,capture_output=True,env=env,timeout=240)
    log.write_bytes(result.stdout+result.stderr)
    need(result.returncode==0, '新検証工程失敗: '+log.name+'\n'+(result.stdout+result.stderr).decode())
    return result.stdout


def verify() -> None:
    current_pr(os.environ['GITHUB_SHA'])
    proof = WORK/'proof'; proof.mkdir(parents=True)
    for cp_name, target in ((r.PARENT,'parent'),(r.FLOETTE,'floette')):
        cp = s.read_json(ROOT/cp_name)
        members = dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
        download(cp['payload_artifact'],cp['source_head'],WORK/target,members)
    paths = [*(ROOT/name for name in CODE), *sorted((WORK/'parent').iterdir()), *sorted((WORK/'floette').iterdir()),
             ROOT/'build/stages/80_modernization_runtime_boundary_repair.gba']
    before = snapshot(paths)
    unitlog = proof/'unit.txt'
    execute([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_runtime','-v'],unitlog)
    text = unitlog.read_text()
    need(re.findall(r'^Ran (\d+) tests? in ',text,re.M)==['19'] and re.search(r'\nOK\s*$',text), '新19試験数/結果不一致')
    parent = linker.materialize()
    (WORK/'accepted-parent.gba').write_bytes(parent)
    for seed in (11,29):
        execute([sys.executable,'-B',__file__,'build',str(WORK/f'build{seed}')],proof/f'build{seed}.txt',
                env=dict(os.environ,PYTHONHASHSEED=str(seed)))
    first, second = WORK/'build11', WORK/'build29'
    for name in ('runtime-image.bin','runtime-bundle.bin','candidate.gba','receipt.json','link.json'):
        need(s.identity(first/name)==s.identity(second/name), '独立2プロセス差分: '+name)
    need(s.identity(first/'runtime-image.bin')==EXPECTED_IMAGE, 'ローカル/Actions image差分')
    expected = oracle(WORK/'parent',WORK/'floette')
    result = audit(first,expected); (proof/'host-audit.json').write_bytes(s.encode(result))
    link_report = s.read_json(first/'link.json')
    selected = samples(first,expected,link_report)
    harness = WORK/'entrypoint-probe'
    execute(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(first),
             'tools/mgba_pr16_learnset_runtime.c','-lmgba','-o',str(harness)],proof/'native-compile.txt')
    native = []
    for seed in (11,29):
        stdout = execute([str(harness),str(WORK/f'build{seed}'/'candidate.gba'),link_report['candidate']['sha256']],proof/f'native{seed}.txt')
        row = json.loads(stdout)
        need(row['status']=='PASS_TWO_LINKED_ROM_ENTRYPOINTS' and row['candidate_sha256']==link_report['candidate']['sha256']
             and row['samples']==len(selected) and row['calls']==len(selected)*130+1
             and all(row[k] is True for k in ('new_code_pc_seen_for_every_call','existing_mon_bytes_unchanged','output_canaries_unchanged')),
             '新2入口ROM試験が全成功ではない')
        (proof/f'native{seed}.json').write_bytes(s.encode(row)); native.append(row)
    need(before==snapshot(paths), '受入入力/source byteまたはmtime変更')
    execute([sys.executable,'-B','scripts/validate_task_graph.py'],proof/'task-graph.txt')
    execute(['git','diff','--exit-code'],proof/'tracked-diff.txt')
    need(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT), 'tracked変更')
    for name in ('receipt.json','link.json','disassembly.txt','pr16_learnset_samples.h'):
        shutil.copyfile(first/name,proof/name)
    (proof/'entrypoints.jsonl').write_bytes(b''.join(s.encode(row) for row in expected))
    data = WORK/'data'; data.mkdir()
    for name in ('runtime-image.bin','runtime-bundle.bin','receipt.json','link.json'):
        shutil.copyfile(first/name,data/name)
    report = {'status':'PASS_TWO_GAME_ENTRYPOINTS_ARM_LINK_AND_DIRECT_ROM_PROBES',
        'task':linker.TASK,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'focused_tests':19,'host_audit':result,'native_probe_processes':2,'native_probe_calls':sum(x['calls'] for x in native),
        'sample_species':selected,'new_arm_compiles':8,'new_arm_links':2,'independent_processes':2,
        'independent_candidate_hashes_match':True,'local_actions_image_hash_matches':True,
        'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,'code_bindings':{name:s.identity(ROOT/name) for name in CODE},
        'proof_files':identities(proof),'data_files':identities(data),'parent_candidate':linker.PARENT,
        'candidate':link_report['candidate'],'scope':'TWO_ENTRYPOINT_DIRECT_CALL_NOT_GAMEPLAY_E2E',
        'rom_hook_count':2,'natural_level_up_connected':False,'initial_moves_connected':False,
        'conditional_consumers_connected':False,'physical_archive_supply_verified':False,
        'global_table_roots_changed':False,'saved_four_moves_rewritten':False,
        'accepted_source_regenerations':0,'accepted_payload_regenerations':0,'accepted_native_reruns':0,
        'old_arm_compiles':0,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False}
    (proof/'verification.json').write_bytes(s.encode(report))
    print(json.dumps({k:report[k] for k in ('status','candidate','focused_tests','native_probe_calls')},ensure_ascii=False))


if __name__=='__main__':
    if sys.argv[1:]==['verify']:
        verify()
    elif len(sys.argv)==3 and sys.argv[1]=='build':
        folder = Path(sys.argv[2])
        r.build(ROOT,WORK/'parent',WORK/'floette',folder)
        linker.link(folder,(WORK/'accepted-parent.gba').read_bytes())
    else:
        raise SystemExit('usage: pr16_learnset_runtime_verify.py verify | build DEST')
