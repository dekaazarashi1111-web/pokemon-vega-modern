#!/usr/bin/env python3
"""未受入のHM05/Save20新区間だけを初回測定。旧accepted native/testsを実行しない。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_hm05_accept as m
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
import pr16_story_gym_record as log_gate
OUT=ROOT/'.local/pr16-story-hm05'
ART=OUT/'artifact'
WF='.github/workflows/pr16-story-hm05.yml'
CODE={WF,'scripts/pr16_story_hm05_accept.py','scripts/pr16_story_hm05_measure.py',
      'tests/test_pr16_story_hm05_accept.py',m.DEV+'/expected.json',m.DEV+'/local-validation.json'}
PARENT=dict(size=18664867,sha256='d93e36abb202788962f1ddd866189d1a72443efa51102a4b66a197ec0549156a')


def invoke(runtime,lane,seed,command):
    m.commands(command)
    folder=ART/lane;folder.mkdir()
    save=folder/'story.srm';save.write_bytes(seed);(folder/'commands.txt').write_bytes(command)
    argv=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
          str(ART/'candidate.gba'),str(save),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        try:
            p=subprocess.run(argv,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
        except subprocess.TimeoutExpired:
            h.d.write(folder/'execution.json',dict(status='TIMEOUT_NOT_ACCEPTED',initial_save=m.identity(seed),
                current_save=m.identity(save.read_bytes()),native_processes=1,automatic_retry=False))
            raise
    h.d.write(folder/'execution.json',dict(returncode=p.returncode,initial_save=m.identity(seed),
        final_save=m.identity(save.read_bytes()),native_processes=1,automatic_retry=False))
    m.need(p.returncode==0 and not (folder/'stderr.txt').read_bytes(),'native失敗は保全し停止。自動再走なし')
    return save.read_bytes()


def measure():
    os.chdir(ROOT);h.d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists() and not OUT.exists(),'未受入の初回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    parent=h.d.read(ROOT/m.gym.CP)
    m.need(parent['actions_completion_confirmed'] is True and parent['save19_accepted'] is True and
           parent['verification']['output_save']==m.INPUT_SAVE,'完了済みSave19親のみ')
    plan=m.load((ROOT/m.DEV/'expected.json').read_bytes());cmds=m.decode_plan(plan)
    local=h.d.read(ROOT/m.DEV/'local-validation.json')
    m.need(h.d.bindings(local['source_bindings'])==local['source_bindings'],'ローカル検証source全byte')
    m.need(m.identity(json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==
           local['plan_value_binding'],'入力計画のJSON値全体')
    m.need(local['new_tests']==60 and local['development_native_processes']==2 and
           local['development_native_failures']==0 and local['accepted_case_reruns']==0,'実行会計')
    bindings=h.d.bindings(CODE);ART.mkdir(parents=True)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests',
        '-p','test_pr16_story_hm05_accept.py','-v'],capture_output=True,timeout=120)
    (ART/'unit.stdout.txt').write_bytes(unit.stdout);(ART/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0,'新60試験の終了値');log_gate.unit_original(unit.stdout,unit.stderr,60)
    meta,z=transport.archive(11028517527,36559147649,PARENT,'e9c9a55c59705490cd49f834fb8586c41bb1861b')
    with z:
        manifest=m.load(z.read('manifest.json'))
        m.need(len(manifest)==264 and set(z.namelist())==set(manifest)|{'manifest.json'},'正式Save19全264member')
        for name,binding in manifest.items():m.need(m.identity(z.read(name))==binding,'親全member '+name)
        for name,target,binding in (('story-fast.srm','input.srm',m.INPUT_SAVE),
            ('candidate.gba','candidate.gba',m.CANDIDATE),('runner','runner',m.RUNNER)):
            value=z.read(name);m.need(m.identity(value)==binding,'固定親 '+name)
            (ART/target).write_bytes(value);(ART/target).chmod(0o555 if name=='runner' else 0o444)
    h.d.write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=transport.archive(10898620034,36218655601,dict(size=102586759,
        sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                path=runtime/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,
        sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA runtime')
    saved=invoke(runtime,'progress',(ART/'input.srm').read_bytes(),cmds['progress'])
    (ART/'story-fast.srm').write_bytes(saved);m.need(m.identity(saved)==m.OUTPUT_SAVE,'自然Save20完了後だけcold開始')
    cold=invoke(runtime,'continue',saved,cmds['continue']);(ART/'cold.srm').write_bytes(cold)
    result,ledger=m.verify(ART)
    h.d.write(ART/'verification.json',result);h.d.write(ART/'save-byte-ledger.json',ledger)
    # 開発cold終端は未受入menu。正式coldでは原本prefixの後だけfield閉じを追加。
    for lane in ('progress','continue'):
        raw=m.inflate(plan[lane]['development_stdout_zlib_b85'])
        command=m.inflate(plan[lane]['development_commands_zlib_b85'],40000)
        m.need(m.identity(raw)==plan[lane]['development_stdout'] and
               m.identity(command)==plan[lane]['development_commands'],'開発text原本も保全')
        (ART/(lane+'-development.stdout.txt')).write_bytes(raw)
        (ART/(lane+'-development.commands.txt')).write_bytes(command)
    m.need(h.d.bindings(protected)==protected and h.d.bindings(CODE)==bindings,'旧受入と新区間source不変')
    for name,binding in (('input.srm',m.INPUT_SAVE),('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
        m.need(m.identity((ART/name).read_bytes())==binding,'原本不変 '+name)
    h.d.write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings,result=result,new_tests=60,development_native_processes=2,development_native_failures=0,
        formal_native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,
        development_cold_prefix_preserved=True,development_cold_menu_end_accepted=False,
        save_byte_ledger=m.identity((ART/'save-byte-ledger.json').read_bytes())))
    h.d.write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS Save20: 通常HM05/2勝/野生2離脱/PC回復/保存/cold全131088bytes; 248+59入力; 全82画面; 新60試験; 旧再走0')


if __name__=='__main__':measure()
