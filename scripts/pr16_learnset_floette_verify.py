#!/usr/bin/env python3
"""Eternal差分/owner Cだけを検証。既受入表はartifactの同一byteを再利用する。"""
from __future__ import annotations
from collections import Counter
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_floette as f
from pr16_wiki_reconcile import fetch
from pr16_learnset_payload_verify import completed_run

WORK = ROOT/'.local/pr16-learnset-floette'
INPUTS = s.BASE+'pr16_learnset_floette_inputs.json'
CODE = ('tools/pr16_learnset_floette.py','tests/test_pr16_learnset_floette.py',
        'src/modernization/pr16_learnset_owner.c','src/modernization/pr16_learnset_owner.h',
        'scripts/pr16_learnset_floette_source.py','scripts/pr16_learnset_floette_verify.py',
        'scripts/pr16_learnset_floette_record.py',
        '.github/workflows/pr16-learnset-floette-source.yml',
        '.github/workflows/pr16-learnset-floette.yml',
        '.github/workflows/pr16-learnset-floette-record.yml',f.DECISION,INPUTS)
CONSUMERS = ('egg','evolution','form_change','level_up','machine',
             'pre_evolution_carry','reminder','shared_egg','tutor')


def need(ok,message):
    if not ok: raise ValueError(message)


def download(artifact:dict, head:str, destination:Path, members:dict) -> None:
    """固定受入artifactのみ。ZIP traversal/symlink/重複/size改変を拒否する。"""
    need(not destination.exists(),'受入入力を重複復元しない')
    meta=fetch(f"actions/artifacts/{artifact['id']}")
    need(all(meta[k]==artifact[k] for k in ('id','name','digest','size_in_bytes'))
         and not meta['expired'] and meta['workflow_run']['head_sha']==head
         and meta['workflow_run']['head_branch']=='codex/modernization-followup-20260908','artifact identity不一致')
    raw=fetch(f"actions/artifacts/{artifact['id']}/zip",binary=True)
    need(len(raw)==meta['size_in_bytes'] and hashlib.sha256(raw).hexdigest()==meta['digest'].removeprefix('sha256:'),'artifact ZIP hash不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(set(archive.namelist())==set(members) and len(archive.infolist())==len(members),'artifact member集合/重複不一致')
        destination.mkdir(parents=True)
        for info in archive.infolist():
            name=info.filename
            need(Path(name).name==name and not info.is_dir() and info.external_attr>>28!=0xA
                 and info.file_size==members[name]['size'] and info.file_size<80000000,'artifact path/size/symlink不正')
            data=archive.read(name)
            need(hashlib.sha256(data).hexdigest()==members[name]['sha256'],'artifact member hash不一致')
            (destination/name).write_bytes(data)


def identities(folder:Path) -> dict:
    return {p.name:s.identity(p) for p in sorted(folder.iterdir())}


def snapshot(paths) -> dict:
    return {str(p):(s.identity(p),p.stat().st_mtime_ns) for p in paths}


def independent_audit(source:Path,parent:Path,output:Path) -> dict:
    """生成器のpacking/owner関数を使わず、原本から差分の全byteを照合する。"""
    reference=s.read_json(source/'reference.json'); routes=list(s.rows(output/'floette-routes.jsonl'))
    need(len(routes)==len(reference['routes'])==37,'reference/差分行数不一致')
    mapping={'level_up':'level_up','evolution':'evolution','tm':'machine'}
    for i,(original,row) in enumerate(zip(reference['routes'],routes)):
        need(row['provenance']['source_route']==original and row['source_order']==i
             and row['species_id']==1029 and row['species_key']=='SPECIES_KEY_FLOETTE_ETERNAL'
             and row['consumer']==mapping[original['method']] and row['move_id']==original['project_move_id']
             and row['source_id']=='official-reference:legendsza:0670.05:'+original['route_id']
             and row['layer']=='official_baseline' and not row['runtime_applied']
             and row['rewrite_existing_moves'] is False,'原本経路の意味/owner不一致')
    original=reference['routes']
    level=[r for r in original if r['method']=='level_up']
    evolution=[r for r in original if r['method']=='evolution']
    machine=[r['project_move_id'] for r in original if r['method']=='tm']
    expected={'floette.level_up.bin':b''.join(r['project_move_id'].to_bytes(2,'little')+bytes([r['target_learning_level']]) for r in level)+b'\0\0\xff',
        'floette.evolution.bin':b''.join(r['project_move_id'].to_bytes(2,'little') for r in evolution),
        'floette.egg.bin':(21029).to_bytes(2,'little')+b'\xff\xff',
        'floette.reminder.bin':b'','floette.shared_egg.bin':b'',
        'floette.tutor.bin':bytes(16),'floette.tutor_archive.bin':b''}
    catalog=s.read_json(parent/'catalogs.json')['machine']['slots']
    bits=sum(1<<r['bit_index'] for r in catalog if r['move_id'] in machine)
    expected['floette.machine.bin']=bits.to_bytes(16,'little')
    missing=[mid for mid in machine if mid not in {r['move_id'] for r in catalog}]
    need(len(missing)==12 and len(machine)==23 and len(level)==13 and len(evolution)==1,'固定参考内訳不一致')
    expected['floette.machine_archive.bin']=b''.join(mid.to_bytes(2,'little') for mid in missing)
    for name,raw in expected.items(): need((output/name).read_bytes()==raw,'差分payload byte不一致: '+name)
    parent_lines=(parent/'consumer-index.jsonl').read_bytes().splitlines(keepends=True)
    output_lines=(output/'consumer-index.jsonl').read_bytes().splitlines(keepends=True)
    need(len(parent_lines)==len(output_lines)==15039,'全index行数不一致')
    policies={}; changed=[]; kept=0
    policy_ids={'INTERNAL_IDENTITY_ONLY':2,'EXCLUDED_REMAKE_FORM_IDENTITY_ONLY':3,
        'NON_BATTLING_FORM_IDENTITY_ONLY':4,'BATTLE_COPY_CARRY_ONLY':5,
        'BATTLE_FORM_CARRY_ONLY':6,'P04_MEGA_CARRY_ONLY':7}
    for a,c in zip(parent_lines,output_lines):
        before,after=json.loads(a),json.loads(c); sid=before['species_id']
        need((after['species_id'],after['species_key'],after['consumer'])==
             (sid,before['species_key'],before['consumer']),'index identity/order不一致')
        if sid==1029:
            need(before['status']=='BLOCKED_SOURCE_ADOPTION' and after['status']=='PAYLOAD_PREPARED_NOT_INSTALLED','裁定枠不一致')
            changed.append(after['consumer'])
        else:
            need(a==c,'既存owner index byte改変'); kept+=1
        policy=policy_ids[before['identity']['policy']] if before['status']=='IDENTITY_ONLY_NO_REPLACEMENT' else 1
        need(policies.get(sid,policy)==policy,'consumer間policy矛盾');policies[sid]=policy
    need(sorted(changed)==sorted(CONSUMERS) and kept==15030,'差分は1029の9枠だけ')
    policy_bytes=bytes(policies[sid] for sid in range(1671))
    need((output/'owner-policies.bin').read_bytes()==policy_bytes,'C policy indexと親identity不一致')
    with tempfile.TemporaryDirectory(dir=WORK) as temp:
        library=Path(temp)/'owner.so'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(ROOT/'src/modernization/pr16_learnset_owner.c'),'-o',str(library)],check=True)
        dll=ctypes.CDLL(str(library));call=dll.Pr16ResolveLearnsetOwner
        call.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_uint16,ctypes.c_uint16,ctypes.c_uint8,ctypes.POINTER(ctypes.c_uint16)]
        call.restype=ctypes.c_uint8
        vector=(ctypes.c_uint8*1671).from_buffer_copy(policy_bytes)
        for sid,policy in enumerate(policy_bytes):
            for consumer in range(9):
                expected_action=3 if policy>=5 else 2 if policy>=2 else 4 if consumer in (2,5) else 1
                owner=ctypes.c_uint16(65535)
                need(call(vector,1671,sid,consumer,ctypes.byref(owner))==expected_action and owner.value==sid,'実owner C query不一致')
        need(bytes(vector)==policy_bytes,'C queryがpolicy入力を書換え')
    need(s.read_json(output/'owner_approved_overlay.json')=={'rows':[]},'未承認overlay')
    return {'status':'PASS_INDEPENDENT_DELTA_BYTES_AND_ACTUAL_C_OWNERS','source_routes':37,
        'unchanged_parent_index_rows':kept,'changed_index_rows':9,'actual_c_queries':15039,
        'identity_only_species':188,'battle_carry_species':157,'non_battle_identity_species':31,
        'machine_routes_bound_to_catalog':11,'machine_routes_requiring_archive_supply':12,
        'conditional_game_callsite_connected':False,'rom_changes':0,'native_runs':0}


def verify() -> None:
    decision=s.read_json(ROOT/f.DECISION); parent_cp=s.read_json(ROOT/decision['parent_checkpoint'])
    expected=s.read_json(ROOT/INPUTS)
    source_done=completed_run(decision['source_run']['id'],decision['source_run']['head_sha'],'.github/workflows/pr16-learnset-floette-source.yml','fixed-reference')
    members=dict(decision['source_files'],**{'receipt.json':decision['source_receipt']})
    download(decision['source_artifact'],decision['source_run']['head_sha'],WORK/'source',members)
    members=dict(parent_cp['summary']['files'],**{'receipt.json':parent_cp['proof_bindings']['receipt.json']})
    download(parent_cp['payload_artifact'],parent_cp['source_head'],WORK/'parent',members)
    proof=WORK/'proof';proof.mkdir()
    inputs=[*sorted((WORK/'source').iterdir()),*sorted((WORK/'parent').iterdir()),
            *(ROOT/name for name in decision['repository_sources']),*(ROOT/name for name in CODE)]
    before=snapshot(inputs)
    command=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_floette','-v']
    unit=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    log=unit.stdout+unit.stderr;(proof/'unit.txt').write_text(log);print(log)
    need(unit.returncode==0 and re.findall(r'^Ran (\d+) tests? in ',log,re.M)==['44']
         and re.search(r'\nOK\s*$',log),'新44試験が全成功ではない')
    for seed in (11,29):
        env=dict(os.environ,PYTHONHASHSEED=str(seed))
        subprocess.run([sys.executable,'-B',__file__,'build',str(WORK/f'build{seed}')],cwd=ROOT,env=env,check=True)
    first=identities(WORK/'build11');second=identities(WORK/'build29')
    need(first==second==expected['expected_outputs'],'独立2プロセス/ローカルActions hash差分')
    audit=independent_audit(WORK/'source',WORK/'parent',WORK/'build11')
    need(before==snapshot(inputs),'入力byte/mtimeが変化')
    subprocess.run([sys.executable,'-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--exit-code'],cwd=ROOT,check=True)
    need(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT),'tracked変更')
    for name in ('receipt.json','floette-index.jsonl','floette-routes.jsonl','owner_approved_overlay.json'):
        shutil.copyfile(WORK/'build11'/name,proof/name)
    (proof/'audit.json').write_bytes(s.encode(audit))
    report={'status':'PASS_FLOETTE_AND_OWNER_SCOPE','source_head':os.environ['GITHUB_SHA'],
        'run_id':int(os.environ['GITHUB_RUN_ID']),'focused_tests':44,'actual_c_queries':15039,
        'independent_processes':2,'local_actions_output_hashes_match':True,
        'input_byte_mtime_unchanged':True,'tracked_tree_unchanged':True,
        'accepted_payload_regenerations':0,'accepted_source_regenerations':0,'accepted_native_reruns':0,
        'source_completion':source_done,'inputs_lock':s.identity(ROOT/INPUTS),
        'code_bindings':{name:s.identity(ROOT/name) for name in CODE},'payload_files':first,
        'proof_files':identities(proof),'runtime_applied':False,'rom_changes':0,'native_runs':0,
        'issue19_complete':False,'release_ready':False}
    (proof/'verification.json').write_bytes(s.encode(report))
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    if sys.argv[1:]==['verify']: verify()
    elif len(sys.argv)==3 and sys.argv[1]=='build':
        f.build(ROOT,WORK/'source',WORK/'parent',Path(sys.argv[2]))
    else: raise SystemExit('usage: pr16_learnset_floette_verify.py verify | build DEST')
