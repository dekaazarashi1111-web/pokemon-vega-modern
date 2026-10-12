#!/usr/bin/env python3
"""初回の保存済み測定をbyte不変で受領。ROM復元・音声測定・32試験は再走しない。"""
from __future__ import annotations
import datetime as dt
import io
import json
import os
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_selected_sound_roots_actions as first
from pr16_selected_asset_actions import runs
m, old, a, publication = first.m, first.old, first.a, first.publication
ROOT, STATE, GUIDE, BRANCH, LOGS = first.ROOT, first.STATE, first.GUIDE, first.BRANCH, first.LOGS
read, load, write, snapshot = first.read, first.load, first.write, first.snapshot
TASK, REPORT, EVIDENCE = first.TASK, first.REPORT, first.EVIDENCE
MEASURE_HEAD='6ced361784848e2df562251b43276b6aab9f51b7'
RUN_ID=38193578259
ARTIFACT_ID=11722642450
CODE=first.CODE|{'scripts/pr16_selected_sound_roots_recover.py','tests/test_pr16_selected_sound_roots_serialization.py'}
WORK=ROOT/'.local/pr16-selected-sound-roots-recovery'
PUBLIC=WORK/'public'
PHASE='preflight'


def public(name,value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def receive():
    run=a.fetch('actions/runs/'+str(RUN_ID))
    m.need(run['head_sha']==MEASURE_HEAD and run['head_branch']==BRANCH and
        run['status']=='completed' and run['conclusion']=='failure','初回失敗run identity')
    jobs=a.fetch('actions/runs/'+str(RUN_ID)+'/jobs?filter=latest&per_page=100')
    m.need(jobs['total_count']==len(jobs['jobs'])==1,'初回全job')
    job=jobs['jobs'][0];steps={s['name']:s for s in job['steps']}
    m.need(job['id']==114631314717 and job['conclusion']=='failure' and
        steps['有限音声rootの宣言境界を検証して記録']['conclusion']=='failure' and
        steps['Run actions/upload-artifact@v4']['conclusion']=='success','初回保存照合失敗/アップロード成功')
    art=a.fetch('actions/artifacts/'+str(ARTIFACT_ID))
    m.need(art['workflow_run']['id']==RUN_ID and art['workflow_run']['head_sha']==MEASURE_HEAD and
        art['name']=='pr16-selected-sound-roots-public-text' and not art['expired'] and
        art['size_in_bytes']==94857 and art['digest']=='sha256:08b33fb7e5b2d5eb70fd1bc22718f328747c6227d075b8201a5de99b2deb808a','保存artifact identity')
    raw=a.fetch('actions/artifacts/'+str(ARTIFACT_ID)+'/zip',binary=True)
    m.need(m.identity(raw)==dict(size=94857,sha256=art['digest'][7:]),'保存ZIP全hash')
    members=old.zip_members(raw)
    m.need(set(members)=={'attempt.json','failure.json','parent-actions-completion.json','sound-roots.json','sound-tests.txt'},'保存全5member')
    failure=json.loads(members['failure.json']);proof=json.loads(members['sound-roots.json'])
    m.need(m.identity(members['failure.json'])==dict(size=679,sha256='a646d821eeb3f7e79e4d4b4525667f6fafcad6fb5bcacd9f9fec8d60821964bc'),'失敗原本hash')
    m.need(failure['status']=='NOT_ACCEPTED' and failure['phase']=='bounded-sound-root-declared-extents' and
        failure['frames'][-2]==dict(path='scripts/pr16_selected_sound_roots_actions.py',line=120) and
        failure['rom_reconstructions']==failure['new_sound_root_measurements']==1,'保存後照合失敗箇所')
    m.need(m.identity(members['sound-tests.txt'])==dict(size=3243,sha256='e11fff77487a832ceed4d038ca6bf3fa2aaade118049ecfaa0c64c0f9d7632ff') and
        b'Ran 32 tests' in members['sound-tests.txt'] and members['sound-tests.txt'].endswith(b'\nOK\n'),'前回32試験成功原本')
    m.need(m.identity(members['sound-roots.json'])==dict(size=824912,sha256='4c364e81daaf4d08bbafec305b0a9c4561f92fa9c18250ee6646327a6d247702'),'測定原本hash')
    m.need(proof['candidate']==m.CANDIDATE and proof['parent_identity']==m.identity(read(first.prior.EVIDENCE+'/record-candidates.json')) and
        proof['match_count']==len(proof['inspection']['matches'])==0 and
        proof['inspection']['counts']==dict(banks=73,nested_links=174,rejected_or_unsupported_records=12147,tone_records=13194,valid_pcm_records=873) and
        proof['inspection']['unique_valid_pcm_samples']==88,'保存測定の範囲/0件')
    m.need(not proof['actual_asset_reader_proven'] and proof['formal_classification_changes']==0 and
        [proof[k] for k in ('formal_classified','formal_unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'正式型/容量不変')
    previous=a.git('show',MEASURE_HEAD+':scripts/pr16_selected_sound_roots.py')
    m.need(read('scripts/pr16_selected_sound_roots.py')==previous.replace(
        b'queue.append(dict(base=x.canonical(target),indices=values,',
        b'queue.append(dict(base=x.canonical(target),indices=list(values),') and previous!=read('scripts/pr16_selected_sound_roots.py'),'修正はnested indexのJSON lossless化だけ')
    m.need(m.encode(proof)==members['sound-roots.json'],'測定JSONのcanonical byte保持')
    receipt=dict(schema_version=1,source_head=MEASURE_HEAD,run_id=RUN_ID,run_status='completed',run_conclusion='failure',
        failure_not_rewritten=True,measurement_replayed=False,old_32_tests_replayed=False,
        job_id=job['id'],steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']],
        artifact={k:art[k] for k in ('id','name','size_in_bytes','digest')},members={n:m.identity(v) for n,v in members.items()},
        original_measurement_sources={n:m.identity(a.git('show',MEASURE_HEAD+':'+n)) for n in sorted(first.CODE)},
        diagnosis_ja='nested ToneData rootのindicesがtupleのため、JSON復元listとの直接比較で停止。測定は保存済み。list化の6境界試験後、測定JSONを改作せず受領する。')
    return members,proof,receipt


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回限定')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists(),'重複受領禁止')
    PUBLIC.mkdir(parents=True);head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'] and not a.git('status','--porcelain','--untracked-files=no').strip(),'event HEAD/clean')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',m.BASE_HEAD,head).decode().splitlines())==CODE,'許可sourceだけ')
    m.need(not a.git('ls-files','--',*[p+'/AGENTS.md' for p in ('scripts','tests','docs','design','content','content/modernization','.github','.github/workflows')]).strip(),'追加AGENTS確認')
    state,parent=load(STATE),load(first.prior.REPORT);lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_ASSET_RECORD_READER' and [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')]==[789,85,6,0],'現在地')
    owner=m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected={first.prior.REPORT}
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name,want in parent[key].items():m.need(m.identity(read(name))==want,'保存親hash');protected.add(name)
    before=snapshot(protected)
    PHASE='receive-saved-measurement-without-replay';members,proof,receipt=receive()
    PHASE='new-serialization-tests';stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_sound_roots_serialization.py'))
    public('serialization-tests.txt',stream.getvalue().encode())
    m.need(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'新6保存境界試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    receipt.update(new_serialization_tests=6,read_only_recovery_passed=True,observed_at=dt.datetime.now(dt.timezone.utc).isoformat())
    evidence={EVIDENCE+'/'+n:d for n,d in members.items()}
    evidence.update({EVIDENCE+'/measurement-recovery.json':m.encode(receipt),EVIDENCE+'/serialization-tests.txt':stream.getvalue().encode(),EVIDENCE+'/starting-head-checks.json':m.encode(runs(MEASURE_HEAD))})
    for name,data in evidence.items():write(name,data)
    stable=snapshot(evidence)
    m.need(load(EVIDENCE+'/sound-roots.json')==proof and stable==snapshot(evidence) and before==snapshot(protected),'保存後read-only/全旧原本保持')
    goal=('有限音声root73群・13194音色recordのうち非圧縮PCM宣言範囲への一致0件を保存。実asset/reader未特定。'
        '0x0880FA64と0x095FE848/0x09673660の元ROM・Vega IPS・現代化ownerの配置元を束縛し、実asset境界/consumerへ進む。'
        '圧縮/未対応音色・有限root外は未証明。0件を不存在や正式型と扱わない。'
        '保存した32試験/音声測定/今回6保存試験と旧record/base/逆参照/map/ARM/LZ/Wikiは無変更再走しない。'
        '正式789/85・選定残6・安全容量0。窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。')
    status='SELECTED_SOUND_ROOT_ZERO_MATCH_SAVED_READER_PENDING'
    counts=dict(rom_reconstructions=0,native_processes=0,accepted_test_reruns=0,new_sound_root_measurements=0,
        old_xref_or_base_search_reruns=0,old_lz_or_map_reruns=0,task_total_rom_reconstructions=1,task_total_sound_measurements=1)
    report=dict(schema_version=1,task=TASK,status=status,source_head=head,measurement_source_head=MEASURE_HEAD,
        measurement_actions_run_id=RUN_ID,measurement_actions_conclusion='failure',measurement_recovery=EVIDENCE+'/measurement-recovery.json',
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,match_count=0,
        new_unit_tests=6,reused_successful_unit_tests=32,actual_asset_reader_proven=False,read_only_check_passed=True,task_graph_passed=True,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},
        preserved_inputs={n:v[0] for n,v in before.items()},observed_head_checks=observed,next_ja=goal,**counts)
    write(REPORT,report);lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_ASSET_OWNER_PROVENANCE',goal_ja=goal,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/sound-roots.json',EVIDENCE+'/measurement-recovery.json',first.prior.REPORT],
        done_ja='実asset境界と全4byteの実readerを束縛し、完了証拠の受領後だけ正式型差分へ進む。')
    state['observed_head_checks']=observed
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,new_unit_tests=6,reused_successful_unit_tests=32,read_only_check_passed=True,task_graph_passed=True,**counts)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_sound_roots_checkpoint=REPORT)
    text=read('CHATGPT_RESUME.md').decode();left,rest=text.split('## 次の未完作業\n',1);_,right=rest.split('\n所有者が閲覧版で',1)
    text=left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_SELECTED_ASSET_OWNER_PROVENANCE。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode());state['bindings']['CHATGPT_RESUME.md']=dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner==m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}),'Wiki/所有者判断/安全方針保持');write(STATE,state)
    summary=('有限音声root73群・13194record・非圧縮PCM88sampleを照合し、対象3範囲との一致0件。'
        '初回run38193578259は新32試験と測定後、tuple/list保存照合で失敗。失敗原本は保持し、6保存境界試験とbyte不変受領で復旧。'
        '復旧時のROM再構成/測定/旧32試験再走0、task全体では候補復元1・音声測定1。実reader・保存統合は未完。')
    guide=read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide+='\n## 有限音声rootの0件測定と保存境界の復旧\n\n'+summary+'\n\n[checkpoint](../'+REPORT+') / [改作なしの測定JSON](../'+EVIDENCE+'/sound-roots.json) / [失敗原本と復旧根拠](../'+EVIDENCE+'/measurement-recovery.json)。\n\n## 次の未完作業\n\n'+goal+'\n';write(GUIDE,guide.encode())
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 有限音声rootと保存境界の復旧\n'
        '- Version: selected-sound-roots-v2\n- Status: DONE（限定検査と保存を完了、実reader/保存容量は未完）\n'
        f'- Summary: {summary}\n- Files changed: 新音声検査器/32試験/6保存試験/復旧runner/Actions、checkpoint/text証拠、固定MD/JSON、両ログ。\n'
        '- Verify: 新6保存試験、既存32成功原本のhash受領、初回失敗run/ZIP94857byte全hash/全5member、byte/mtime不変、task graph、最終index新規private違反0。全体guardと一般CIは別記録。\n'
        f'- Next: {goal}\n- Commit: この記録を含む単親通常commit。実SHAはActions result/Git履歴。\n'
        '- Network: 同repo PR/ref/Actions/artifactと同branch非force push。初回測定のみ固定JP symbol/pret公開header/sound.cと既存private入力復元。ROM/save/生byte列は非公開のまま。\n')
    for name in LOGS:
        original=read(name);m.need(('- Task: '+TASK+' /').encode() not in original,'同task二重追記禁止');write(name,original+block.encode())
    PHASE='final-index-and-nonforce-push';allowed=CODE|set(evidence)|LOGS|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(m.BASE_HEAD,allowed,REPORT);m.need(before==snapshot(protected),'旧原本保持')
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前HEAD')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 音声root0件と保存境界復旧を再測定なしで記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip();m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'公開blob一致')
    for name in set(evidence)|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-LOGS):z.writestr(name,read(name))
    public('result.json',dict(status=status,source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),**counts))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('recovery-failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,rom_reconstructions=0,new_sound_root_measurements=0))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
