#!/usr/bin/env python3
"""実NPC配布3件の既存成功を再実行せず原本検証し、固定再開点と両ログへ記録。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='f5a480bd4c591650221caf657cf17789d5458a02'
TESTED='dd432122b22d6bdaf1858c03b40a351da67c56bf'
RUN,JOB,ARTIFACT=35339382576,105581553850,10543834367
ZIP_SHA='2fa3a6957224048e87efa1e91b6b51fce8c717252c8ec2eeb4865c12c79f1e50'
CANDIDATE='72fbca91cd6ee1082198678ccaed76bcb76dfd19ce9f6f3c26309745b2f09ac0'
TASK='USER-20260918-RING-NPC-GIFT'
SELF='scripts/pr16_ring_npc_gift_record.py'
TEST='tests/test_pr16_ring_npc_gift_record.py'
WORKFLOW='.github/workflows/pr16-ring-npc-gift-record.yml'
REPORT='content/modernization/pr16_ring_npc_gift_checkpoint_20260918.json'
OUT=ROOT/'.local/pr16-ring-npc-gift-record'
IMPLEMENTATION=(
    '.github/workflows/pr16-ring-npc-workbench.yml','scripts/pr16_ring_npc_workbench.py',
    '.github/workflows/pr16-ring-npc.yml','overlays/ring_npc/ring_npc.c',
    'overlays/ring_npc/ring_npc.h','tests/ring_npc_host.c','tests/test_pr16_ring_npc.py',
    'scripts/pr16_ring_npc_successor.py','tests/test_pr16_ring_npc_successor.py',
    'scripts/pr16_ring_npc_native.py','tools/mgba_pr16_ring_npc.c','tests/test_pr16_ring_npc_native.py',
)
STOP=('NPC正規配布の最初の動作区切りを完了。run35339382576/job105581553850 SUCCESS、'
      '新candidate72fbca91のmap96/17 local4 (12,38)でRing0→1の実会話、二重受取防止、'
      '最終リーグ未達/バッグ満杯の不成立、通常Save2→3/fresh Continue/再訪を3process・6coresで確認。'
      '11+18+10=39 source tests、ARM二重生成、既存NPC/非object event/レイアウト不変、7画面目視。'
      'BP正本ceddbe91は変更しない。通常戦闘へのリング所持再判定は次の未完作業であり、'
      'Ring/policyのformal IDは閉じない。')
NEXT=('新NPC候補72fbca91を親に、通常戦闘開始時にリング所持を毎回再判定する最小bridgeを実装する。'
      '明示pending設定、施設/raid/link制限、対応石/使用回数/他ギミック排他を維持し、'
      'NPC受取→対応石を装備→通常Save/fresh Continue→既存技選択UIのメガ選択/不選択/取消・技使用・'
      '戦闘後復帰を実観測する。新しい戦闘前選択UIやNPC受取時の揮発NEXT設定で代用しない。'
      '保存済みNPC3件は配布/配置/saveコードに変更影響がなければ再実行せず原本を継承する。')
VISUAL={
    'gift-save-revisit-first-dialogue':'eeba86af22b55d341dcfd2a5329346a765b610bf9427e944ad2e87167025dfdb',
    'gift-save-revisit-repeat-dialogue':'4db9467561aca28324aecc56489d4f73a4896c06368f4ef3298f3c2b5f676b8c',
    'gift-save-revisit-reloaded-dialogue':'4db9467561aca28324aecc56489d4f73a4896c06368f4ef3298f3c2b5f676b8c',
    'locked-save-revisit-first-dialogue':'5d1ed24198e9fbf7ce6381d4a5939f3ee63884038b302d36f57b7a40b6ca0877',
    'locked-save-revisit-reloaded-dialogue':'5d1ed24198e9fbf7ce6381d4a5939f3ee63884038b302d36f57b7a40b6ca0877',
    'full-save-revisit-first-dialogue':'ea8436d433624570c77561e317df22664373c86233efea7ce1bb89022c370541',
    'full-save-revisit-reloaded-dialogue':'ea8436d433624570c77561e317df22664373c86233efea7ce1bb89022c370541',
}


def need(ok,message):
    if not ok: raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def unpack(raw):
    need(identity(raw)==dict(size=235010,sha256=ZIP_SHA),'native artifact identity differs')
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())<300,'artifact too many members')
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                 and info.filename not in files and not info.is_dir(),'unsafe/duplicate artifact member')
            need(info.file_size<2000000 and (info.external_attr>>16)&0o170000 != 0o120000,'unsafe artifact type/size')
            files[info.filename]=z.read(info)
    manifest=json.loads(files['members.json'])
    need(set(files)==set(manifest)|{'members.json'},'artifact manifest member set differs')
    for name,metadata in manifest.items():
        need(identity(files[name])=={k:metadata[k] for k in ('size','sha256')},'artifact member digest differs: '+name)
    return files,manifest


def validate_evidence(files,manifest,root=ROOT):
    import pr16_ring_npc_native as native
    n=json.loads(files['pr16-ring-npc-native/result.json'])
    b=json.loads(files['pr16-ring-npc-successor/candidate.json'])
    need(n['status']=='PASS_NPC_GIFT_SAVE_ONLY' and n['failures']==[],'native overall failure')
    need(n['actual_new_processes']==3 and n['successful_fresh_cores']==6
         and n['accepted_native_cases_replayed']==0 and len(n['guard_checks'])==7
         and len(set(n['guard_checks']))==7,'native accounting differs')
    need(n['candidate']==b['candidate']==dict(size=33554432,sha256=CANDIDATE),'gift candidate differs')
    need(b['source_head']==TESTED and b['run_id']==RUN and b['crc32']=='62F3C583','builder provenance differs')
    need(n['physical_host']==[96,17,4,12,38] and b['map']['old_object_count']==3
         and b['map']['new_object_count']==4,'physical NPC owner differs')
    for k in ('ring_full_acceptance','ordinary_battle_accepted','release_ready'):
        need(n[k] is False,'unobserved acceptance promoted')
    need(b['independent_gift_compiles']==2 and b['existing_object_changes']==0
         and b['map_layout_changes']==0 and b['undeclared_changed_bytes']==0
         and b['save_layout_changes']==0 and b['battle_policy_changes']==0,'build scope differs')
    for source,metadata in n['sources'].items():
        need(identity((root/source).read_bytes())==metadata,'native source changed: '+source)
    for source,metadata in b['sources'].items():
        need(identity((root/source).read_bytes())==metadata,'builder source changed: '+source)
    need(len(n['results'])==3 and {x['case'] for x in n['results']}==set(native.CASES),'case set differs')
    for name in n['guard_checks']:
        prefix='pr16-ring-npc-native/guard-'+name
        need(files[prefix+'.stdout']==b'' and files[prefix+'.stderr']==b'P03 archive: host write after observation barrier\n', 'guard output differs')
        need(json.loads(files[prefix+'.process.json'])==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'guard rejection differs')
    originals={}
    for item in n['results']:
        name=item['case'];prefix='pr16-ring-npc-native/'+name
        proc=json.loads(files[prefix+'.process.json'])
        need(proc==item['process'] and type(proc['returncode']) is int and proc['returncode']==0
             and proc['timed_out'] is False and proc['spawn_error'] is None,'native process differs')
        raw=files[prefix+'.stdout'];row=json.loads(raw)
        need(row==item['native_result'],'raw native result differs')
        native.validate(row,name,CANDIDATE,n['physical_host'])
        need(b'mGBA[' not in files[prefix+'.stderr'],'native warning')
        originals[name]={suffix:{'identity':identity(files[prefix+'.'+suffix]),
            'utf8':files[prefix+'.'+suffix].decode('utf-8')} for suffix in ('stdout','stderr','process.json')}
    tests={}
    for name,count in (('gift',11),('map',18),('oracle',10)):
        raw=files['pr16-ring-npc-run/'+name+'.stderr']
        need(re.search(rb'Ran '+str(count).encode()+rb' tests in [^\n]+\n\nOK\n$',raw) is not None,
             'focused source test result differs: '+name)
        tests[name]={'count':count,'raw':raw.decode('utf-8'),'identity':identity(raw)}
    for label,digest in VISUAL.items():
        need(hashlib.sha256(files['pr16-ring-npc-native/'+label+'.png']).hexdigest()==digest,'reviewed screenshot changed')
    return dict(schema_version=1,task=TASK,classification='SCOPED_NPC_GIFT_SAVE_ONLY',
        tested_head=TESTED,run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,
        artifact_identity=dict(size=235010,sha256=ZIP_SHA),candidate=b['candidate'],crc32=b['crc32'],
        native=n,builder=b,originals=originals,source_tests=tests,
        visual_review=dict(completed=True,reviewed_sha256=VISUAL,
            method_ja='ChatGPTがartifactの原寸PNGを直接目視。成功/重複/条件不足/満杯と保存後会話の7画面。文字とNPC表示の崩れなし。'),
        npc_gift_save_scoped_accepted=True,ring_full_acceptance=False,ordinary_battle_accepted=False,
        release_ready=False,accepted_native_cases_replayed=0,
        record_new_emulator_processes=0,member_manifest=manifest)


def run():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'environment boundary')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout boundary');ops.assert_remote(head,attempts=12)
    need(not (ROOT/REPORT).exists(),'gift checkpoint already recorded; do not replay')
    need(set(ops.cmd('git','diff','--name-only',TESTED,head).splitlines())=={SELF,TEST,WORKFLOW},'unrelated work changed')
    OUT.mkdir(parents=True,exist_ok=True)
    state=resume.validate(ROOT);before=copy.deepcopy(state)
    checkpoint=(ROOT/resume.CHECKPOINT).read_bytes();backlog=resume.load(ROOT,resume.BACKLOG);ledger_before=copy.deepcopy(backlog)
    r=ops.api('actions/runs/'+str(RUN));jobs=ops.api('actions/runs/'+str(RUN)+'/jobs')['jobs']
    need(r['status']=='completed' and r['conclusion']=='success' and r['head_sha']==TESTED,'native run is not success')
    need(len(jobs)==1 and jobs[0]['id']==JOB and jobs[0]['conclusion']=='success','native job differs')
    artifact=ops.api('actions/artifacts/'+str(ARTIFACT))
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ZIP_SHA
         and not artifact['expired'],'native artifact metadata differs')
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    files,manifest=unpack(raw);report=validate_evidence(files,manifest)
    failed=ops.api('actions/runs/35338073483')
    need(failed['conclusion']=='failure' and failed['head_sha']=='a2b4bac74a53f6985b9c9009c455959e21c9a183','initial rejected build history differs')
    report['previous_rejected_build']=dict(run_id=failed['id'],conclusion='failure',native_processes=0,
        reason_ja='町96/5が15templateのためappend上限で前処理拒否。上限/既存NPCを変更せず北ルート96/17へ追加。')
    report['record_source_head']=head;report['record_run_id']=int(os.environ['GITHUB_RUN_ID'])
    report['source_bindings']={p:identity((ROOT/p).read_bytes()) for p in (*IMPLEMENTATION,SELF,TEST,WORKFLOW)}
    (ROOT/REPORT).write_bytes(stable(report))
    state['ring_npc_implementation']={'path':REPORT,'status':report['classification'],'tested_head':TESTED,
        'run_id':RUN,'candidate':dict(report['candidate'],crc32=report['crc32']),
        'npc_gift_save_scoped_accepted':True,'ring_full_acceptance':False,'ordinary_battle_accepted':False}
    state['bp']['current_stop']=state['source_change_review_ja']=STOP
    state['bp']['next_step']=state['next_action']['goal_ja']=NEXT
    state['next_action']['read_paths']=[REPORT,'scripts/pr16_ring_npc_successor.py','scripts/pr16_ring_npc_native.py',
        'overlays/cfru/rom_bridge.c','overlays/cfru/integration.c','scripts/build_battle_core.py']
    state['observed_head']=head
    state['observed_head_semantics']='NPC配布成功を原本から記録したsource HEAD。正式BP受入は既存欄を維持。記録commitはremote refで確認。'
    state['observed_head_checks']['reason_ja']=('NPC build/native run35339382576 SUCCESSを確認。39 testsと3新規processの結果は独立checkpoint参照。'
        '開始HEADのsource-validation action_requiredと初回NPCビルドfailureはそのまま保持。全CI greenとは主張しない。')
    state['session_execution_summary']={'new_emulator_processes':0,'record_scope_new_emulator_processes':0,
        'recorded_native_processes':3,'recorded_fresh_cores':6,'rom_changes':0,
        'recorded_candidate_changes':1,'accepted_standalone_replays':0,'scope_ja':STOP}
    state['do_not_repeat'].insert(0,'NPC配布3件は'+REPORT+'のrun35339382576で成功。配布/配置/saveに変更影響がなければ原本を継承し、次は通常戦闘のリング再判定と既存UI。')
    state['logs_synchronized']=True
    # Native sources are bound inside the immutable milestone receipt. Do not
    # add actively edited future implementation files to the old BP validator.
    state['source_bindings'][REPORT]=identity((ROOT/REPORT).read_bytes())
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='NATURAL_CAPTURE_GEAR')
    row['ring_npc_gift_checkpoint']=REPORT
    for key in ('candidate','status','last_accepted_native_run','latest_native_run','latest_native_job','remaining_physical_gap_ids','remaining_p08_gate_ids','release_ready'):
        need(state[key]==before[key],'formal acceptance changed: '+key)
    check=copy.deepcopy(backlog);next(x for x in check['remaining_conditions'] if x['id']=='NATURAL_CAPTURE_GEAR').pop('ring_npc_gift_checkpoint')
    need(check==ledger_before,'formal backlog changed')
    (ROOT/resume.STATE).write_bytes(stable(state));(ROOT/resume.BACKLOG).write_bytes(stable(backlog))
    (ROOT/resume.DOC).write_text(resume.render(state),encoding='utf-8');resume.validate(ROOT)
    results=[]
    for pattern in ('test_pr16_ring_npc_gift_record.py','test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w',encoding='utf-8') as stream:
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(result.wasSuccessful() and result.testsRun>0 and not result.skipped,'record/resume focused tests failed')
        results.append({'pattern':pattern,'count':result.testsRun,'success':True})
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    need((ROOT/resume.CHECKPOINT).read_bytes()==checkpoint,'BP checkpoint changed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    outputs=(REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS)
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 正規NPC配布と保存再開の最初の動作区切り\n'
        '- Status: DONE / NPC配布と保存再開のみ。Ring全体/通常戦闘/最終統合は未完。\n- Version: pr16-ring-npc-gift-20260918\n'
        '- Summary: '+STOP+'\n- Files changed: '+', '.join((*IMPLEMENTATION,SELF,TEST,WORKFLOW,*outputs))+'\n'
        '- Verify: production C11/map18/native oracle10の39tests PASS。ARM二重生成一致、allocator overlap0、宣言外ROM差分0。新native3cases/6cores、各Save2→3、Ring0→1又は不成立、全Bag/party/BP保持。\n'
        '- Visual: 成功/重複/未達/満杯とcold再訪7画面を原PNGで確認。\n'
        '- Record verification: 原ZIPと全member digest、case raw stdout/stderr/process、candidate/source/Actionsを照合。記録/resume focused testsとtask graph PASS。最終index guardとdiff checkはcommit前必須。\n'
        '- History: 初回run35338073483は町のNPC枠境界で停止、native0。新run35339382576で北ルートへ修正成功。旧失敗は成功に読み替えない。\n'
        f'- Evidence: tested={TESTED}; run={RUN}; job={JOB}; artifact={ARTIFACT}; SHA256={ZIP_SHA}。\n'
        '- Preserved: 受入済みBP/P03/P06/P07のnative再実行0。最初のhost用globは既存plan14testsも含んだため後続でexact test名へ修正。正式BP候補・checkpoint・physical3/P08 gates2は無変更。\n'
        f'- Commit: この記録を含むcommit。record source={head}、record run={os.environ["GITHUB_RUN_ID"]}。同branchへ非force反映、完了SHAはremote ref確認。\n'
        '- Network: GitHub connector/Actions・固定private環境の復元のみ。ROM/save/private ZIP/elfをGitや証拠artifactへ公開しない。\n'
        '- Boundary: 全体private guardの既存違反前後一致と追加違反0を検査。全体guard PASS、全CI green、merge/release/baseline変更は主張しない。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        path=ROOT/name;need(TASK not in path.read_text(encoding='utf-8'),'duplicate completion log')
        with path.open('a',encoding='utf-8') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPLEMENTATION,SELF,TEST,WORKFLOW,*outputs))
    guard.guard();subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    ops.assert_remote(head)
    for key,value in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):
        subprocess.run(['git','config',key,value],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 正規NPC配布3件と保存再開の実測を記録'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in outputs:
        need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed bytes differ')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'tracked changes remain')
    receipt=dict(status='PASS_RECORDED_NONFORCE_PUSHED',task=TASK,commit=commit,source_head=head,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),native_run_id=RUN,tests=results,new_emulator_processes=0,
        npc_gift_save_scoped_accepted=True,ring_full_acceptance=False,ordinary_battle_accepted=False,release_ready=False)
    (OUT/'recorded-result.json').write_bytes(stable(receipt));print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':run()
