#!/usr/bin/env python3
"""未受入のSave19新区間だけを一度測定。旧区間/旧試験/compileは実行しない。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_gym_accept as m
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
OUT=ROOT/'.local/pr16-story-gym'
ART=OUT/'artifact'
WF='.github/workflows/pr16-story-gym.yml'
CODE={WF,'scripts/pr16_story_gym_accept.py','scripts/pr16_story_gym_measure.py',
      'tests/test_pr16_story_gym_accept.py',m.DEV+'/expected.json',m.DEV+'/local-validation.json'}
PARENT=dict(size=18101058,sha256='4e7a2e5d25dbf01284fdd992327971b7a0d84df2e86022ea6cefc685b2dd064b')


def invoke(runtime,lane,seed,command):
    m.commands(command)
    folder=ART/lane;folder.mkdir()
    save=folder/'story.srm';save.write_bytes(seed)
    (folder/'commands.txt').write_bytes(command)
    argv=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
          str(ART/'candidate.gba'),str(save),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        try:
            p=subprocess.run(argv,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
        except subprocess.TimeoutExpired:
            h.d.write(folder/'execution.json',dict(status='TIMEOUT_NOT_ACCEPTED',initial_save=m.identity(seed),
                current_save=m.identity(save.read_bytes()),automatic_retry=False))
            raise
    h.d.write(folder/'execution.json',dict(returncode=p.returncode,initial_save=m.identity(seed),
        final_save=m.identity(save.read_bytes()),native_processes=1,automatic_retry=False))
    m.need(p.returncode == 0 and not (folder/'stderr.txt').read_bytes(), 'native失敗は保全して停止。自動再走しない')
    return save.read_bytes()


def measure():
    os.chdir(ROOT);h.d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/m.CP).exists() and not OUT.exists(),
           '未受入新区間の初回・新規artifactだけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    plan=json.loads((ROOT/m.DEV/'expected.json').read_text())
    local=json.loads((ROOT/m.DEV/'local-validation.json').read_text())
    m.need(h.d.bindings(local['source_bindings']) == local['source_bindings'], 'ローカル検証済みsourceの全byte')
    m.need(m.identity(json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()) ==
           local['plan_value_binding'], '整形だけの差を許し、入力計画の内容を固定')
    m.need(local['new_tests'] == 73 and local['development_native_processes'] == 2 and
           local['development_native_failures'] == 0 and local['accepted_case_reruns'] == 0, '開発実行会計')
    cmds=m.decode_plan(plan);bindings=h.d.bindings(CODE);ART.mkdir(parents=True)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests',
        '-p','test_pr16_story_gym_accept.py','-v'],capture_output=True,timeout=120)
    (ART/'unit.stdout.txt').write_bytes(unit.stdout);(ART/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode == 0 and not unit.stdout and unit.stderr.count(b' ... ok\n') == 73 and
           b'\nOK\n' in unit.stderr and b'FAILED' not in unit.stderr and b'skipped' not in unit.stderr, '新区間専用73試験')
    meta,z=transport.archive(11012768108,36522150353,PARENT,'2577d253823bdca94bf3dfac0a67dea9776a6d8a')
    with z:
        manifest=json.loads(z.read('manifest.json'))
        m.need(len(manifest) == 170 and set(z.namelist()) == set(manifest)|{'manifest.json'}, '正式Save18全170member')
        for name,binding in manifest.items():m.need(m.identity(z.read(name)) == binding, '親member全byte: '+name)
        for name,target,binding in (('story-fast.srm','input.srm',m.INPUT_SAVE),
            ('candidate.gba','candidate.gba',m.source.CANDIDATE),('runner','runner',m.shared.RUNNER)):
            data=z.read(name);m.need(m.identity(data) == binding, '固定入力: '+name)
            (ART/target).write_bytes(data);(ART/target).chmod(0o555 if name == 'runner' else 0o444)
    h.d.write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=transport.archive(10898620034,36218655601,dict(size=102586759,
        sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name == 'ld.so' or name.startswith('lib/'):
                path=runtime/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes()) == dict(size=1968536,
        sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'), '固定mGBA runtime')
    saved=invoke(runtime,'progress',(ART/'input.srm').read_bytes(),cmds['progress'])
    (ART/'story-fast.srm').write_bytes(saved)
    m.need(m.identity(saved) == m.OUTPUT_SAVE, '書込み完了Save19を確認してからcold起動')
    cold=invoke(runtime,'continue',saved,cmds['continue']);(ART/'cold.srm').write_bytes(cold)
    result,ledger=m.verify(ART)
    h.d.write(ART/'verification.json',result);h.d.write(ART/'save-byte-ledger.json',ledger)
    # 先行checkpointの実入力prefixも失わない。旧hash-only WIPは成功昇格しない。
    recovery=json.loads((ROOT/m.DEV/'recovery-wip.json').read_text())
    prefix=(ART/'progress/commands.txt').read_bytes()[:recovery['commands']['size']]
    stdout=(ART/'progress/stdout.txt').read_bytes()[:recovery['stdout_prefix']['size']]
    m.need(m.identity(prefix) == recovery['commands'] and m.identity(stdout) == recovery['stdout_prefix'], '保存済み回収prefixの全byte保持')
    m.need(h.d.bindings(protected) == protected and h.d.bindings(CODE) == bindings, '既存受入/新区間source不変')
    for name,binding in (('input.srm',m.INPUT_SAVE),('candidate.gba',m.source.CANDIDATE),('runner',m.shared.RUNNER)):
        m.need(m.identity((ART/name).read_bytes()) == binding, '原本不変: '+name)
    h.d.write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings,result=result,new_tests=73,development_native_processes=2,development_native_failures=0,
        prior_unaccepted_lost_wip_native_processes=1,formal_native_processes=2,accepted_case_reruns=0,
        accepted_test_reruns=0,compiles=0,recovery_prefix_verified=True,prior_hash_only_wip_accepted=False,
        save_byte_ledger=m.identity((ART/'save-byte-ledger.json').read_bytes())))
    h.d.write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS Save19: 通常2勝/badge1/報酬/PC回復/保存/cold全131088bytes; 入力464+34; 全243画面; 新73試験; 旧再走0')


if __name__=='__main__':measure()
