#!/usr/bin/env python3
"""保存済み22画面の視認・終端を限定受入へ結合。ROM/native/旧試験は実行しない。"""
from __future__ import annotations
import datetime
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
BASE = 'content/modernization/'
START = 'd8437a43808f457b6abafed8e24be434ddfe896b'
HEAD = '164028f28c9fa753afa1525907e2824b17a16698'
RUN, JOB, ART = 36312254126, 108600336124, 10929142898
CANDIDATE = {'size': 33554432, 'sha256': '59ac6688576238f00dac88cccec1a42415f6f0e4f3f07d60411f6d3059bf61e6'}
CP = BASE+'pr16_research_standard_list_ui_checkpoint.json'
EVIDENCE = BASE+'pr16_research_standard_list_ui_evidence/'+str(RUN)
REVIEW = BASE+'pr16_research_standard_list_visual_review.json'
ACCEPT = BASE+'pr16_research_standard_list_acceptance.json'
GUIDE = 'docs/PR16_RESEARCH_STANDARD_LIST_JA.md'
SELF = 'scripts/pr16_research_standard_list_accept.py'
WF = '.github/workflows/pr16-research-standard-list-accept.yml'
TEST = 'tests/test_pr16_research_standard_list_accept.py'
CODE = {SELF, WF, TEST, REVIEW}
OUT = ROOT/'.local/pr16-standard-list-accept'
TASK = 'USER-20260927-RESEARCH-STANDARD-LIST'
SCREENS = set(('door_entered counter_approach counter_intro menu_first balance_selected menu_after_balance guide_cursor guide_one guide_two menu_after_guide b_cancel_message b_cancel_closed revisit_intro menu_revisit exit_cursor exit_message exit_closed third_intro menu_third third_cancel_message third_closed end').split())
SCREENS = {x+'.ppm' for x in SCREENS}
FALSE = ('natural_story_progress_accepted', 'naturally_earned_spending_accepted', 'release_ready')

def need(value, reason):
    if not value:
        raise ValueError(reason)

def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}

def read(path):
    return json.loads(Path(path).read_bytes())

def validate(measured, oracle, unit, review, terminal):
    """原本・独立視認・GitHub終端を混同せず結合する純粋検証。"""
    run, job = terminal['run'], terminal['job']
    need(run['id']==RUN and run['head_sha']==HEAD and run['run_attempt']==1
         and run['head_branch']=='codex/modernization-followup-20260908'
         and run['path']=='.github/workflows/pr16-research-standard-list.yml'
         and run['status']=='completed' and run['conclusion']=='success', 'run終端/source')
    need(job['id']==JOB and job['run_id']==RUN and job['head_sha']==HEAD
         and job['status']=='completed' and job['conclusion']=='success', 'job終端/source')
    need(measured['source_head']==HEAD and measured['run_id']==RUN and measured['candidate']==CANDIDATE
         and oracle['candidate']==CANDIDATE, '実測identity')
    need(measured['returncode']==0 and measured['timeout'] is False
         and measured['stderr']==identity(b'') and measured['flash_prefix_unchanged'] is True, 'native終了/Flash')
    need(measured['counts']==dict(accepted_case_reruns=0,arm_compiles=0,guard_processes=7,host_compiles=1,native_processes=1), '実測計数')
    need(oracle['status']=='PASS_STANDARD_LIST_NATIVE_OBSERVATIONS'
         and oracle['standard_list_accepted'] is False and oracle['visual_review_completed'] is False,
         '原本の未受入フラグを改作しない')
    need(oracle['all_owner_ledger_bag_party_flash_counter_unchanged'] is True
         and oracle['single_task_and_window_lifecycle'] is True, '資源・保存・window所有')
    for name, expected in dict(visits=3, functional_rows_selected=2, b_cancels=2,
                               exit_row_selections=1, native_processes=1, accepted_case_reruns=0).items():
        need(type(oracle[name]) is int and oracle[name]==expected, 'oracle計数 '+name)
    need(oracle['stdout']==measured['stdout'] and oracle['commands']==measured['commands'], '入出力binding')
    need(set(measured['screens'])==SCREENS and oracle['screens']==measured['screens'], '22画面の閉集合')
    need(unit['expected']==unit['passed']==27 and unit['returncode']==0
         and unit['stdout']==identity(b''), '旧oracle27件原本')
    need(review['source_head']==HEAD and review['run_id']==RUN and review['candidate']==CANDIDATE
         and review['reviewed_screen_count']==22 and review['screens']==measured['screens']
         and review['completed'] is True and review['method']=='ASSISTANT_VISUAL_REVIEW_NO_OCR', '独立視認binding')
    need(set(review['findings'])==SCREENS and all(isinstance(x,str) and x for x in review['findings'].values()), '画面別所見')
    for name in FALSE:
        need(oracle[name] is False and review[name] is False, '未受入範囲 '+name)
    need(review['whole_game_visual_quality_accepted'] is False, '全体品質へ昇格禁止')
    return dict(status='PASS_STANDARD_LIST_SELECTION_CANCEL_REVISIT_SCOPED', standard_list_accepted=True,
                visual_review_completed=True, actions_completion_confirmed=True, candidate=CANDIDATE,
                measurement_run=RUN, measurement_source_head=HEAD, screens=22, visits=3,
                functional_rows_selected=2,b_cancels=2,exit_row_selections=1,
                new_native_processes=0,new_arm_compiles=0,new_host_compiles=0,new_guard_processes=0,
                accepted_case_reruns=0,old_test_executions=0,**{k:False for k in FALSE})

def terminal_fixture():
    """検証器の単体試験専用。実受入ではGitHub応答以外に使わない。"""
    return dict(run=dict(id=RUN,head_sha=HEAD,head_branch='codex/modernization-followup-20260908',run_attempt=1,
                         path='.github/workflows/pr16-research-standard-list.yml',status='completed',conclusion='success'),
                job=dict(id=JOB,run_id=RUN,head_sha=HEAD,status='completed',conclusion='success'))

def record():
    sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_research_lifecycle_actions as d
    import pr16_research_counter_accept as archive
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT); d.current(); need(not (ROOT/ACCEPT).exists(),'受入の重複禁止')
    OUT.mkdir(parents=True,exist_ok=True)
    cp=read(ROOT/CP)
    need(cp['status']=='MEASURED_STANDARD_LIST_PENDING_VISUAL_AND_TERMINAL_REVIEW'
         and cp['standard_list_accepted'] is False and cp['run_id']==RUN, '現在checkpoint')
    for label in ('source_bindings','protected_bindings'):
        need(d.bindings(set(cp[label]))==cp[label], '不変 '+label)
    manifest=read(ROOT/cp['evidence_manifest'])
    need(d.bindings(set(manifest))==manifest,'保存済み全原本hash')
    run=d.inputs.api('actions/runs/'+str(RUN)); job=d.inputs.api('actions/jobs/'+str(JOB))
    terminal=dict(run={k:run[k] for k in terminal_fixture()['run']},job={k:job[k] for k in terminal_fixture()['job']})
    rows,meta=archive.archive(ART,154943,'cd0dbfa95122b53b234a0431c5beb6e60e13f93578ce5b15fe193d0946c8c57b',71,2728412,RUN)
    prefix='.local/pr16-standard-list-ui-native/public/'
    need(set(rows)=={CP}|{p for p in rows if p.startswith(prefix)},'artifact用途の閉集合')
    need(meta['workflow_run']['head_sha']==HEAD,'artifact source')
    old={p[len(prefix):]:v for p,v in rows.items() if p.startswith(prefix)}
    need(json.loads(rows[CP])==cp,'tracked checkpointと元artifact')
    for name in ('measurement.json','oracle.json','oracle-unit.json','stdout.txt','stderr.txt','commands.txt','guards.json'):
        need(old[name]==(ROOT/EVIDENCE/name).read_bytes(),'保存原本byte '+name)
    measured,oracle,unit=[json.loads(old[n+'.json']) for n in ('measurement','oracle','oracle-unit')]
    review=read(ROOT/REVIEW); result=validate(measured,oracle,unit,review,terminal)
    for name,binding in measured['screens'].items():
        raw=old[name]
        need(identity(raw)==binding and raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'実画面 '+name)
    for name in ('stdout','stderr','commands'):
        need(identity(old[name+'.txt'])==measured[name],'実測入出力 '+name)
    need(identity(old['oracle-unit.stderr.txt'])==unit['stderr']
         and old['oracle-unit.stderr.txt'].count(b' ... ok\n')==27
         and b'\nOK\n' in old['oracle-unit.stderr.txt'],'旧27件を再実行せず再利用')
    guards=json.loads(old['guards.json'])
    need(set(guards)=={'bus8','bus16','bus32','raw8','raw16','raw32','register'},'7 barrier')
    for name,value in guards.items():
        err=old[name+'.stderr.txt']; out=old[name+'.stdout.txt']
        need(err==b'research-save-impact: host write after observation barrier\n' and out==b''
             and value==dict(returncode=1,stderr=identity(err),stdout=identity(out)),'保存済み書込み拒否')
    tests=subprocess.run([sys.executable,'-B','-m','unittest',TEST.replace('/','.')[:-3],'-v'],capture_output=True,timeout=90)
    for stream in ('stdout','stderr'):(OUT/('unit.'+stream+'.txt')).write_bytes(getattr(tests,stream))
    count=tests.stderr.count(b' ... ok\n')
    need(tests.returncode==0 and count==25 and b'\nOK\n' in tests.stderr and not tests.stdout,'新規25検証PASS')
    runs=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=10')['workflow_runs']
    result.update(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
                  measured_checkpoint=identity(rows[CP]),original_terminal=terminal,artifact=meta,
                  evidence_manifest=identity((ROOT/cp['evidence_manifest']).read_bytes()),
                  review=identity((ROOT/REVIEW).read_bytes()),new_validation_tests=count,
                  validation_stderr=identity(tests.stderr),validation_stdout=identity(tests.stdout),
                  old_oracle_tests_reused=27,old_host_tests_reused=18,old_thumb_tests_reused=8,old_event_tests_reused=14,
                  old_native_failures_preserved=cp['failed_original_native_runs'],
                  latest_actions=[d.run_summary(r) for r in runs],active_baseline_changed=False,issue19_complete=False)
    d.write(ROOT/ACCEPT,result)
    cp.update(status=result['status'],standard_list_accepted=True,visual_review_completed=True,actions_completion_confirmed=True,
              acceptance=ACCEPT,visual_review=REVIEW,acceptance_run=result['run_id'],original_measurement_unchanged=True)
    d.write(ROOT/CP,cp)
    goal='標準リストは22画面/3訪問で限定受入済み。次は自然稼得RP→ショップ支出の未完境界。既存canonical shopの入力関数とwindow/frame所有を先に確認し、影響部分だけ修正・実測する。通常ストーリー進行は別の未完境界。数値2境界/旧4入口/旧稼得/BP/P08を再実行しない。'
    text=(ROOT/GUIDE).read_text(encoding='utf-8')
    text+='\n## 2026-09-27 独立限定受入\n\n'+goal+'\n\n原本run36312254126/job108600336124はcompleted/success。固定artifactの22 PPMを本会話で視認し、全メニュー行・会話窓・枠・選択・取消・終了・再訪を確認。所見は `'+REVIEW+'`、独立受入は `'+ACCEPT+'`。原本oracleの未受入フラグは改作せず、後継判定として記録する。今回のnative/guard/host/ARM生成と旧試験再実行は0、新しい記録検証25件のみ。受付0RP/rank1は起動前fixtureであり自然稼得・自然到達の証拠ではない。一般CIのaction_requiredや歴史的failureをsuccessに読み替えない。\n'
    # 冒頭の現在地のみ最新化し、旧実装/失敗履歴は保持する。
    text=text.replace('`MEASURED_STANDARD_LIST_PENDING_VISUAL_AND_TERMINAL_REVIEW`。source', '`'+result['status']+'`。実測source',1)
    text=text.replace('自己run終端と22実画面の視認前に正式受入へ昇格しない。','独立受入でrun終端と22実画面を確認済み。自然稼得支出/通常進行は未受入。',1)
    (ROOT/GUIDE).write_text(text,encoding='utf-8')
    state=d.read(d.STATE)
    state['research_standard_list']=dict(path=CP,status=result['status'],candidate=CANDIDATE,acceptance=ACCEPT,
        measurement_run=RUN,run_id=result['run_id'],source_head=result['source_head'],standard_list_accepted=True)
    state['bp']['current_stop']=result['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_NATURALLY_EARNED_SPENDING_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,ACCEPT,'overlays/research_economy_v1/research_economy_v1.c',
                    'scripts/pr16_research_lifecycle_actions.py','content/modernization/pr16_research_photo_checkpoint.json'],
        stop_rule_ja='標準リスト/数値/旧稼得を無変更再実行しない。自然RP支出と通常進行を別scopeで受入。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'STANDARD_LIST run36312254126/59ac6688の22画面/3訪問/選択2/B取消2/終了1を限定受入。独立受入によるnative/ARM/host/guard/旧試験の再実行0。原本27oracle、18host/8ELF/14eventを再利用。自然RP支出/通常進行へ昇格しない。')
    state['observed_head']=result['source_head'];state['observed_head_semantics']='標準リストの独立受入記録source。実測run36312254126は終端success確認済み。自己記録runの終端は次のAPI読取で照合する。'
    state['observed_head_checks']=dict(scope_head=result['source_head'],runs=[r for r in result['latest_actions'] if r['head_sha']==result['source_head']],reason_ja='最新Actionsを照合。action_required/failureは保持し、一般CI全成功を主張しない。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs if r['status'] in ('queued','in_progress')]
    state['logs_synchronized']=True
    for p in CODE|{CP,ACCEPT,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 標準リスト22画面・終端の独立受入\n- Version: research-standard-list-accepted-v1\n- Status: DONE（選択/取消/再訪限定。自然RP支出・通常進行は未完）\n- Summary: 59ac6688で3訪問/2機能/2取消/終了1、22実画面の窓・枠・表示を視認。原本run36312254126のsuccessと保存済みoracleを結合。旧failureと未受入フラグは原本に保持。\n- Files changed: 独立受入検証器/25試験/視認記録/Actions、checkpoint/受入JSON/専用MD、固定引継ぎMD/JSON、両ログ。\n- Verify: 新規25検証PASS、元artifact SHA/全22画面/全保存manifest/source/protected一致。新規native/ARM/host/guard/旧試験再実行0。task graph/resume/final-index guard後のみcommit。一般CI全成功や全体historical guard PASSは主張しない。\n- Commit: source={result["source_head"]}; acceptance run={result["run_id"]}; 同branchへの非force commit。自己SHAはremote/git logで確認。\n- Network: GitHub run/job/artifact/PRのみ。ROM/save/私有入力変更0、merge/release/baseline変更0。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as stream:stream.write(log)
    owned={CP,ACCEPT,GUIDE,d.STATE,d.DOC}|set(d.LOGS)
    need(d.bindings(set(cp['protected_bindings']))==cp['protected_bindings'],'protected最終一致')
    d.write(OUT/'owned.json',sorted(owned));print(json.dumps(result,ensure_ascii=False))

def guard():
    sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_research_lifecycle_actions as d
    import pr16_learnset_runtime_record as g
    import pr16_resume
    os.chdir(ROOT);d.current();pr16_resume.validate(ROOT)
    g.START=START;g.CODE=CODE;g.OWNED=set(read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

def snapshot():
    """次の独立境界のtracked textだけ取得。入力ROM/saveは含めない。"""
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    patterns=['scripts/pr16_research*.py','tests/test_pr16_research*.py','tools/pr16_research*.c',
              'content/modernization/pr16_research*checkpoint.json','content/modernization/pr16_research*recipe.json',
              'docs/PR16_RESEARCH*.md','overlays/research_economy_v1/*','config/research_economy_v1.json']
    exact={'AGENTS.md','CHATGPT_RESUME.md',BASE+'p08_remaining_work.json',BASE+'pr16_bp_chooser_checkpoint.json',
           BASE+'pr16_native_supply_resume_20260913.json','docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md',
           'scripts/pr16_resume.py','scripts/pr16_learnset_compact_record.py','scripts/pr16_learnset_runtime_record.py',
           'content/research_economy_v1/canonical_model.json'}
    files=[p for p in paths if p and (p in exact or any(fnmatch.fnmatch(p,q) for q in patterns))]
    manifest=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),files={})
    with zipfile.ZipFile(OUT/'context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            raw=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT);raw.decode('utf-8');need(b'\0' not in raw,'text限定')
            z.writestr(p,raw);manifest['files'][p]=identity(raw)
        z.writestr('context-manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(read(OUT/'owned.json')))
    elif sys.argv[1:]==['snapshot']:snapshot()
    else:raise SystemExit('record|guard|paths|snapshot')
