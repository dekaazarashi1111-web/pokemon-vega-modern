#!/usr/bin/env python3
"""明示許可されたBubble closeoutだけ。成功原本を受領し、新検証後にtextを非force反映。"""
from __future__ import annotations
import collections
import copy
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo
import pr16_weather_bubble_receipt as r
import pr16_resume as resume

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20261010-WEATHER-BUBBLE'
INITIAL = r.HEAD
SELF = 'scripts/pr16_weather_bubble_closeout.py'
RECEIPT = 'scripts/pr16_weather_bubble_receipt.py'
TEST = 'tests/test_pr16_weather_bubble_receipt.py'
WORKFLOW = '.github/workflows/pr16-weather-bubble-closeout.yml'
STEP_NAMES = ['Set up job','Run actions/checkout@v4','Closed first scope and unchanged saved resume',
    'Official compiler and independent PNG checker','New bubble source, ARM ABI, 32 tests and finite reader only',
    'Closed successful text publication guard','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
STEP_NUMBERS = [1,2,3,4,5,6,7,14,15]
NEXT = ('正式784分類/90未知の保存親から次は08397492の1件。pr16_weather_bubble_receipt.restore_parentで62旧原本と今回4原本/差分を復元し、'
        '独立公開source・全asset・実table/literal/readerへ結ぶ。近傍名/参考size/距離だけで型へ昇格しない。'
        'Bubble成功32試験/実reader/ROM再構成は再走しない。Blastoise083D6B61の既知未消費tail診断も反復しない。'
        '保存入口ready/退避53300前Free/同期非再入/controller6528本番配線、正式切替後trainer131後半→シオウ回復保存coldContinueは別gate。')


def git(*args, env=None):
    return subprocess.check_output(['git',*args],cwd=ROOT,env=env).decode().strip()


def api(path, binary=False):
    command = ['gh','api','repos/'+r.REPO+'/'+path]
    if binary and path == 'actions/jobs/'+str(r.JOB)+'/logs':
        # 固定jobの原logをPIPEへ取得。端末へ出さず、承認済みJSON二行だけを検証する。
        command.append('--allow-escape-sequences')
    raw = subprocess.check_output(command,cwd=ROOT)
    return raw if binary else json.loads(raw)


def save(name, value):
    path = ROOT/name
    r.need(not path.is_symlink(), '出力symlinkを拒否')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if type(value) is bytes else r.canonical(value))


def index_guard(base, allowed):
    import guard_private_files as guard
    names = git('diff','--cached','--name-only',base).splitlines()
    r.need(set(names) <= allowed and names, '明示許可された今回textだけをstage')
    for name in names:
        path = ROOT/name
        r.need(path.is_file() and not path.is_symlink() and path.suffix in ('.md','.json','.py','.yml'), 'textのみ')
        after = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
        before = subprocess.run(['git','show',base+':'+name],cwd=ROOT,capture_output=True).stdout
        after.decode('utf-8'); r.need(b'\0' not in after, 'NUL禁止')
        r.need(path.suffix.lower() not in guard.BLOCKED_SUFFIXES and
               not any(name == p or name.startswith(p+'/') for p in guard.BLOCKED_PARTS), 'private path禁止')
        def bad(raw):
            lines = raw.decode('utf-8',errors='replace').splitlines()
            return collections.Counter(lines[n-1] for n in guard.document_user_path_lines(raw))
        r.need(not (bad(after)-bad(before)), '新private user path禁止: '+name)
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'baseline.index'))
        git('read-tree',base,env=env)
        command = [sys.executable,str(ROOT/'scripts/guard_private_files.py')]
        before = subprocess.run(command,cwd=ROOT,env=env,capture_output=True)
        after = subprocess.run(command,cwd=ROOT,capture_output=True)
    r.need(before.returncode in (0,1) and after.returncode in (0,1), 'guard実行異常を拒否')
    r.need(before.returncode != 0 or after.returncode == 0, 'full guard悪化を拒否')
    return dict(base=base,changed_paths=names,new_changed_path_violations=0,
        full_index_guard_before_returncode=before.returncode,full_index_guard_after_returncode=after.returncode,
        full_guard_pass_claimed=after.returncode == 0)


def main():
    head = os.environ['GITHUB_SHA']
    r.need(os.environ['GITHUB_REPOSITORY'] == r.REPO and os.environ['GITHUB_REF_NAME'] == r.BRANCH and
           os.environ['GITHUB_RUN_ATTEMPT'] == '1' and git('rev-parse','HEAD') == head, '指定branch初回HEADだけ')
    r.need(not git('status','--porcelain'), 'clean checkout')
    pr = api('pulls/16')
    r.need(pr['state'] == 'open' and pr['draft'] is True and pr['merged'] is False and pr['head']['sha'] == head, '現HEAD draft/open')
    resume.validate(ROOT)
    r.need(not (ROOT/r.CHECKPOINT).exists() and not (ROOT/r.EVIDENCE).exists(), '受入済みcloseoutの二重適用禁止')
    run = api('actions/runs/'+str(r.RUN))
    job = api('actions/jobs/'+str(r.JOB))
    artifact = api('actions/artifacts/'+str(r.ARTIFACT))
    meta = r.metadata(run,job,artifact)
    r.need(r.exact([s['name'] for s in job['steps']],STEP_NAMES) and
           r.exact([s['number'] for s in job['steps']],STEP_NUMBERS), '取得した全9stepの厳密name/number/順序')
    files = r.unpack(api('actions/artifacts/'+str(r.ARTIFACT)+'/zip',binary=True))
    log = r.verify_log(api('actions/jobs/'+str(r.JOB)+'/logs',binary=True))
    values = r.verify_files(files)
    r.verify_sources(values,ROOT)
    audit = r.parent(ROOT)
    delta = r.build(audit,files)
    full = r.materialize(audit,delta,files)
    frontier = r.frontier(full)
    # 受領した4原本は再シリアライズせず全byte保存。
    for name,raw in files.items(): save(r.EVIDENCE+'/'+name,raw)
    save(r.EVIDENCE+'/reference-chain.json',delta)
    save(r.EVIDENCE+'/unknown-frontier.json',frontier)
    cp = dict(schema_version=1,status=delta['status'],task=TASK,**meta,**log,
        candidate=copy.deepcopy(r.model.CANDIDATE),classified=784,unclassified=90,newly_classified=1,
        inherited_classified=783,inherited_unclassified=91,inherited_saved_inputs=62,
        inherited_reference_stages=30,inherited_changes=164,inherited_witnesses=154,
        reference_stages=31,total_changes=165,total_witnesses=155,
        delta_identity=r.identity(r.canonical(delta)),unknown_identity=r.identity(r.canonical(frontier)),
        full_audit_identity=r.identity(r.previous.canonical(full)),evidence_bindings=delta['evidence_bindings'],
        guide=r.GUIDE,previous_checkpoint=r.previous.PARENT_CHECKPOINT,next_ja=NEXT,
        claims=copy.deepcopy(r.model.CLAIMS),donor_safe_bytes=0,native_processes=0,measurement_replays=0,
        old_scope_test_reruns=0,current_session_rom_reconstructions=0,
        historical_success_reconstructions=1,historical_task_reconstructions_including_failed_run=2,
        failed_previous_run=values['provenance.json']['failed_previous_run'],
        measurement_tests_inherited=32,measurement_source_files_frozen=6,dependency_files_frozen=len(values['provenance.json']['dependency_bindings']),
        closeout_source_head=head,closeout_run_id=int(os.environ['GITHUB_RUN_ID']),
        closeout_recovery=dict(failed_run_id=38042005576,failed_job_id=114183945767,reason='gh refused ANSI in saved log; fixed job PIPE-only --allow-escape-sequences',tests_executed=0,rom_reconstructions=0,commits_created=0),
        general_ci=dict(all_general_ci_success=False,preexisting_run_id=38040440825,preexisting_job_id=114179438028,
            source_mismatch='overlays/qol_production/qol_production.c',capacity_step=14,secondary_missing_upload_step=17,
            unrelated_sources_unchanged=True),release_ready=False,active_baseline_changed=False,merge_performed=False)
    save(r.CHECKPOINT,cp)
    sys.path.insert(0,str(ROOT/'tests'))
    import test_pr16_weather_bubble_receipt as tests
    class Recording(unittest.TextTestResult):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs); self.names=[]
        def startTest(self,test):
            self.names.append(test.id()); super().startTest(test)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Recording).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    print(stream.getvalue(),flush=True)
    r.need(result.wasSuccessful() and not result.skipped and result.testsRun >= 40, '新receipt全試験成功')
    cp['receipt_tests'] = dict(tests_run=result.testsRun,tests=result.names,failures=0,errors=0,skipped=0,
                               old_scope_test_reruns=0,rom_reconstructions=0,native_processes=0)
    cp['closeout_code_bindings'] = {p:r.identity((ROOT/p).read_bytes()) for p in (SELF,RECEIPT,TEST,WORKFLOW)}
    save(r.CHECKPOINT,cp)
    restored = r.restore_parent(ROOT)
    r.need(r.exact(r.identity(r.previous.canonical(restored)),cp['full_audit_identity']), '保存後の受入親784/90完全復元')
    summary = ('Weather Bubble成功run38040440848/job114179438484の全9step/32試験を原本継承。'
        'ZIPと4JSON、生成・検証済み/公開済みの各4hash、6測定source/143依存source/62親原本を照合。'
        '独立8x16 indexed4画像の全64byte一致、実sheet/reader38命令・64byte消費・実12byte stack帰還を条件付き最小4byte型へ受入。'
        '0838B32Fだけ追加し784分類/90未知/全874hit、旧30段164変更154witness不変。'
        f'新receipt{result.testsRun}試験PASS。今回ROM再構成/旧scope再走/native各0、donor安全容量0、正式ROM/Save101不変。')
    guide = ('# PR16 Weather Bubble 最小型受入\n\n'+summary+'\n\n'
        '## 根拠と境界\n\n'
        '測定source HEAD: `'+r.HEAD+'`。成功artifact11665870186のZIP SHA-256: `'+r.ZIP_ID['sha256']+'`。'
        '公開sourceはpret/pokefireredの固定c75f352304d529f6ba92d4f74b9cf8b5c3810788。'
        'gWeatherBubbleTiles0838B304〜0838B344、対象0838B32F〜0838B333（offset43から4byte）、'
        'sWeatherBubbleSpriteSheet0838D5F4のsize64/tag1205、Bubbles_InitVars0807D034→LoadSpriteSheet08008258→CpuSet081C7A88。'
        '全32半word消費/出力SHA一致とallocation失敗/created済みの両未消費controlを保持する。\n\n'
        '受入は誤検出pointerの条件付きデータ型1件のみ。Fog/allocator/registryの同期正常ABIと同一資源epochを条件にする。'
        'BIOS本体CPU、描画、自然story到達、IRQ/全heap寿命、donor適格性/leaseは未証明。'
        '安全容量は0、正式ROMとSave101、BP/P08受入、release=falseを変更しない。\n\n'
        '## 再開と再検証\n\n'+NEXT+'\n\n'
        '`python3 scripts/pr16_weather_bubble_receipt.py` は保存原本と現在sourceだけを照合する。'
        '正式旧親はblastoise_chain.parentの62原本。診断31番目Blastoise namespaceを混ぜない。'
        '新31番目Bubble差分で165変更/155witness。原本4JSONのformal_classification_accepted=falseは測定時事実のまま保持し、受入は別checkpointで記録する。\n\n'
        '## Actionsと会計\n\n'
        '既知失敗38039867181から実call frame束縛へ修正した成功だけを受領。過去task再構成は失敗込み2、成功runは1、本closeoutは0。'
        'closeout失敗38042005576は保存logのANSIに対するgh出力拒否。試験・受入・commit前に停止し、固定job原logのPIPE取得だけを修正した。'
        'source-validationの既存38040440825/job114179438028はstep14 capacity証拠のqol_production.c source不一致（2error）、'
        'step17未生成artifact uploadも失敗。これらのsourceと受入条件を変更せず、全CI greenとは記録しない。\n')
    save(r.GUIDE,guide.encode())
    state = resume.load(ROOT,resume.STATE)
    old_checks = copy.deepcopy(state['observed_head_checks'])
    state['weather_bubble_closeout'] = dict(checkpoint=r.CHECKPOINT,guide=r.GUIDE,source_head=r.HEAD,run_id=r.RUN,
        classified=784,unclassified=90,donor_safe_bytes=0,previous_observed_checks=old_checks)
    state['observed_head'] = r.HEAD
    state['observed_date_jst'] = datetime.datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    state['observed_head_semantics'] = '成功測定のsource HEAD。記録workflow HEAD/runはWeather Bubble checkpointへ別記し、測定HEADに偽装しない。'
    state['bp']['current_stop'] = summary
    state['bp']['next_step'] = NEXT
    state['next_action']['id'] = 'BIND_NEXT_08397492_ASSET_FRONTIER'
    state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [r.GUIDE,r.CHECKPOINT,RECEIPT,r.EVIDENCE+'/unknown-frontier.json','scripts/pr16_weather_bubble_sources.py']
    state['observed_head_checks'] = dict(run_id=r.RUN,job_id=r.JOB,scope_head=r.HEAD,all9_steps_success=True,
        artifact_id=r.ARTIFACT,classified=784,unclassified=90,newly_classified=1,scope_tests=32,receipt_tests=result.testsRun,
        all_general_ci_success=False,general_ci_capacity_step14_failure=True,general_ci_secondary_missing_upload_step17=True,
        general_ci_runs=[38040440825,38040446702],reason_ja=summary+'一般CI既存capacity source不一致は継続。全CI greenではない。')
    state['session_execution_summary'] = summary
    state['pending_runs'] = []
    freeze = 'Weather Bubble成功38040440848の6source/4原本/32試験と実readerを無変更再走しない。今回受領はROM/native0。型1件をdonor安全容量や本番表示へ昇格しない。'
    if freeze not in state['do_not_repeat']: state['do_not_repeat'].append(freeze)
    new_paths = [r.CHECKPOINT,r.GUIDE,SELF,RECEIPT,TEST,WORKFLOW,*[r.EVIDENCE+'/'+n for n in (*r.FILES,'reference-chain.json','unknown-frontier.json')]]
    for name in new_paths:
        r.need(name not in state['source_bindings'], '既存source pinを無断で更新しない')
        state['source_bindings'][name] = r.identity((ROOT/name).read_bytes())
    state['logs_synchronized'] = True
    resume.dump(ROOT/resume.STATE,state)
    subprocess.run([sys.executable,'scripts/pr16_resume.py','render'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'scripts/pr16_resume.py','check'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    now = datetime.datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds')
    verification = f'新receipt {result.testsRun} tests PASS; 保存784親再読完全一致; resume render/check PASS; task graph PASS; 最終index差分guard新規違反0（既存full guard失敗は別計上）; 旧32/184試験・ROM/native再走0'
    entries = {
        'design/run_log.md': f'\n## {now} {TASK} closeout\n\n- Timestamp: {now}\n- Task: {TASK}\n- Status: DONE\n- Summary: {summary}\n- Files changed: receipt/closeout/tests, bubble evidence/checkpoint/guide, 固定resume MD/JSON, 両log\n- Verify: {verification}\n- Commit: この記録を含むcommit（親 {head}、非force同branch）\n- Network: GitHub固定成功run/job/artifact/logの受領のみ。新ROM/private runtimeなし。\n',
        'design/version_log.md': f'\n## {now} PR16-WEATHER-BUBBLE-784-90\n\n- Timestamp: {now}\n- Version: PR16-WEATHER-BUBBLE-784-90\n- Commit: この記録を含むcommit（親 {head}、非force同branch）\n- Task: {TASK}\n- Summary: {summary}\n- Verify: {verification}\n'}
    for name,entry in entries.items():
        before = (ROOT/name).read_bytes()
        r.need((TASK+' closeout').encode() not in before if name.endswith('run_log.md') else b'PR16-WEATHER-BUBBLE-784-90' not in before, '同記録の重複禁止')
        (ROOT/name).write_bytes(before+entry.encode())
    stage = [r.CHECKPOINT,r.GUIDE,resume.STATE,resume.DOC,*entries,*[r.EVIDENCE+'/'+n for n in (*r.FILES,'reference-chain.json','unknown-frontier.json')]]
    git('add','--',*stage)
    allowed = set(stage) | {SELF,RECEIPT,TEST,WORKFLOW}
    guard = index_guard(INITIAL,allowed)
    git('diff','--cached','--check')
    r.need(api('pulls/16')['head']['sha'] == head, 'push直前HEAD競合を拒否')
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('commit','-m',TASK+': 成功原本を無再測定受領しBubble最小型1件784/90と引継ぎを確定')
    committed = git('rev-parse','HEAD')
    git('push','origin','HEAD:refs/heads/'+r.BRANCH)
    r.need(api('git/ref/heads/'+r.BRANCH)['object']['sha'] == committed, '非force push後のremote HEAD一致')
    output = dict(status='DONE_BUBBLE_SAVED_EVIDENCE_CLOSEOUT',commit=committed,parent=head,
        measurement_source_head=r.HEAD,measurement_run_id=r.RUN,closeout_run_id=int(os.environ['GITHUB_RUN_ID']),
        classified=784,unclassified=90,receipt_tests=result.testsRun,donor_safe_bytes=0,native_processes=0,
        measurement_replays=0,current_session_rom_reconstructions=0,old_scope_test_reruns=0,guard=guard,
        all_general_ci_success=False,release_ready=False)
    destination = Path('/tmp/bubble-closeout-result'); destination.mkdir()
    (destination/'result.json').write_bytes(r.canonical(output))
    print(json.dumps(output,ensure_ascii=False,sort_keys=True))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS_SCOPED COMMIT='+committed)


if __name__ == '__main__': main()
