#!/usr/bin/env python3
"""新Save25原本をGitへ記録。native/既受入試験/ROM再配布は行わない。"""
from __future__ import annotations
import ast,datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save25_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-TRAINER351-SAVE25'
PREP='content/modernization/pr16_story_save25_preparation.json'
OUT=ROOT/'.local/pr16-story-save25-record'
CODE={'scripts/pr16_story_save25_accept.py','scripts/pr16_story_save25_record.py','tests/test_pr16_story_save25_accept.py',
      a.VISUAL,PREP,'.github/workflows/pr16-story-save25-record.yml'}
def unit_receipt(job_id,count):
    raw=h.d.inputs.api('actions/jobs/'+str(job_id)+'/logs',True)
    lines=raw.decode().splitlines();tests=[v.split('Z ',1)[-1]for v in lines if ' ... ok' in v and 'test_pr16_story_save25_' in v]
    need(len(tests)==count and any('Ran '+str(count)+' tests in ' in v for v in lines) and any(v.endswith(' OK')for v in lines),'既成功試験原本')
    return dict(job_id=job_id,passed_tests=count,replayed_tests=0,test_lines=tests)
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    OUT.mkdir()
    for name in a.m.CODE:
        need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定sources不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37094105840,'1a842ee45ca361522fd4e6f6cee766df6534428e',111120376656,['success']*11)
    prep_done=inherited.terminal(37094769974,'1c7b23e4a6a5708cebdb2713c97f553b47ac616b',111122336477,['success']*8)
    failure_done=inherited.terminal(37112433649,'25049912ce5828ba55f9cda5a60c494ae1cabb45',111172794747,
        ['success','success','success','success','failure','skipped','success','success','success'])
    _,z=a.m.a.d.m.transport.archive(11270435233,37112433649,dict(size=554,sha256='2b4ae1c3bab16aedbe38c9de3b445bb861fc7646d80320cf738d5ebba64d9288'),'25049912ce5828ba55f9cda5a60c494ae1cabb45')
    with z:
        failure=json.loads(z.read('failure.json'));need(failure['native_processes']==0 and failure['type']=='HTTPError' and failure['message']=='HTTP Error 404: Not Found','runtime消失前処理のみ')
    # controller16試験は成功原本を利用。変更したのは入力runtime復元経路だけ。
    def functions(raw):return {n.name:ast.get_source_segment(raw,n) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
    old=functions(h.d.git('show','25049912ce5828ba55f9cda5a60c494ae1cabb45:scripts/pr16_story_save25_measure.py').decode())
    new=functions((ROOT/'scripts/pr16_story_save25_measure.py').read_text())
    need(all(old[n]==new[n]for n in ('pixels','crop','digest','classify','navigation','idle','screen','battle','progress','save')),'16controller試験の対象全関数不変')
    receipts=[unit_receipt(111172794747,16),unit_receipt(a.JOB,7)]
    prep=h.d.read(ROOT/PREP)
    raw=h.d.inputs.api('actions/jobs/111122336477/logs',True).decode()
    cleaned='\n'.join(v.split('Z ',1)[-1]for v in raw.splitlines())
    index=cleaned.index('{\n  "status": "PASS_EAST_TRAINER')
    logged,_=json.JSONDecoder().raw_decode(cleaned[index:])
    need(logged==prep and prep['native_processes']==0 and [r['trainer_id']for r in prep['trainers']]==[351,352,353],'静的3root/6nodeと保存PP原本')
    _,z=a.m.a.d.m.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:before=z.read('story-fast.srm');rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.m.a.d.m.shared.plan.CANDIDATE,'読取専用親入力')
    meta,z=a.m.a.d.m.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'全55新原本member')
        need(not any(n.endswith('.gba') or n=='runner' or n.startswith(('runtime/','private-inputs/')) for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'全member '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==42 and
         visual['reviewed_screens']==dict(progress=list(range(40)),**{'continue':[0,1]}) and visual['save_success_wording_observed'] is True,'42画面目視/成功文言')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視全byte '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    os.environ.update(PR16_SAVE25_ORIGINAL=str(original),PR16_SAVE24_INPUT=str(assets/'input.srm'),PR16_SAVE25_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save25_accept.py','-v'],capture_output=True,timeout=120)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==18 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新18受入/拒否試験のみ')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
                 'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0' not in raw,'tracked textのみ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'prepared-terminal.json',prep_done)
    write(evidence/'preflight-failure.json',dict(terminal=failure_done,failure=failure,controller_tests=16,native_processes=0,
        recovery_ja='消失したartifact10898620034を保持済みartifact11263910704の同一runtime hashでActions内再利用。既存ROM/runtime/入力Save24は新artifact外。'))
    write(evidence/'controller-test-receipts.json',receipts)
    paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()}
    goal=(f'Save25 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
          'map1/73・31,7南・party4/RP0・12712円・badge1・story4071=6/4072=1。'
          'trainer351の通常勝利/416円/Save25/独立Continueは完了。次は東通路の31,8以南から進み、'
          'trainer352（30,13）/353（21,17）と岩階段23,14経由の正規teleportを通常入力で確認する。'
          '3root/6node・33点地形は静的候補だけで実通行受入ではない。ミュウツーPP[1,14,2,5]/HP324、'
          'オノノクスPP[15,10,15,20]/HP294。通常UIで残PPを扱い、host回復/flag/var解禁は禁止。'
          '既存候補ROM/runnerはSave24 artifact11263343138からActions内で読取専用再利用。'
          '旧runtime artifact10898620034は404で消失、保持済み11263910704のruntime/manifest.json全member/hashを照合して利用。'
          '新公開artifactには新save/画面/textだけを入れ、既存ROM/runner/runtime/入力Saveは再配布しない。'
          '94/cold13入力、16+7/新18試験、Save1〜24を無影響再走しない。teleport/洞窟走破/HM05原因/全国図鑑/自然進化/全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
        record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save25_accepted=True,teleport_accepted=False,
        visual_review=a.VISUAL,preparation=PREP,source_bindings=h.d.bindings(CODE|a.m.CODE),
        evidence_bindings=h.d.bindings(paths),prior_controller_tests=[16,7],new_acceptance_tests=18,record_native_processes=0,
        next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟trainer351・Save25 限定受入

`{result['status']}`。東通路31,4から31,7へ通常進行し、D・だんしたっぱの3体に火炎放射3回、交代提案B取消2回で勝利。416円を得て通常Save25/独立Continueを受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` は全8step成功。artifact `{a.ARTIFACT}` / 223647bytes / SHA256 `{a.ARCHIVE['sha256']}`。全55member、94/cold13入力、42画面を照合。保存成功文言はprogress38、安定field39。敗北/逃走/捕獲0、trainer1勝をoutcome残留で多重計上しない。

Save25 `{a.OUTPUT['sha256']}` / 131088bytes。party600byteの差分は火炎放射PP5→2だけ、全HP/EXP/種族/4技/道具/OTを保持。Bag/HM05不変、所持金12296→12712、trainer351のphysical bit1631だけ0→1。補助vars4021:38→40/4022:3→0、runtime ownerは未解決。旧Save24bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1を確認。全Save/RTCはcoldと同一、6928byte/1746範囲差分。

準備run37094769974の6静的契約/3root6node/33点地形は再利用。run37112433649はruntime原本404・native0のfailureを保持し、成功16controller試験は再走せず保持済みruntime入力へ接続した新7path試験だけを実行。当記録は新18受入/拒否試験・native0。新artifactは新save/画面/textだけで既存ROM/runner/runtime/入力Save24を含まない。

## 次の未完工程

{goal}

record source `{os.environ['GITHUB_SHA']}` / run `{os.environ['GITHUB_RUN_ID']}` 自身のpush/post終端は外部APIで確認する。merge/release/active baseline変更なし。
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'旧受入source/基準を保全')
    state['story_save24']['record_completion']=prior_done
    state['story_save25']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
        story_fast_save=a.OUTPUT,map=[1,73],xy=[31,7],facing=1,money=12712,badge_count=1,rp=0,story_vars={'4071':6,'4072':1},
        hm05_owned=True,hm05_taught_or_used=False,teleport_accepted=False,cave_crossing_complete=False,record_native_processes=0,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['story_save25_preparation']=dict(status=prep['status'],path=PREP,run_id=37094769974,terminal=prep_done,native_processes=0)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],
        reason_ja='新trainer351勝利とSave25/独立Continueを限定受入。前処理404失敗は保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='trainer351/Save25測定source。全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_EAST_FROM_SAVE25',goal_ja=goal,read_paths=[a.GUIDE,a.CP,PREP,a.VISUAL,'scripts/pr16_story_save25_measure.py','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],
        stop_rule_ja='Save25以南だけ。trainer351勝利・旧入力は再走しない。静的経路を実到達に昇格せず、全国図鑑/story flag注入禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='洞窟trainer351の通常勝利/416円と31,7南のSave25・独立Continue受入。party4/RP0・12712円・badge1。teleport/洞窟走破/全国図鑑/自然成長/全story未完。'
    state['do_not_repeat'].append('Save25の94/cold13入力・16+7/新18試験を無影響再走しない。準備3root6node/33点は静的だけ。runtime404のnative0 failureを成功へ改作しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟東通路trainer351とSave25
- Version: story-cave-trainer351-save25-v1
- Status: DONE（trainer1勝/保存限定。洞窟走破/全story未完）
- Summary: 31,7の通常trainer351を火炎放射3回・交代取消2回で勝利、416円。通常Save25と独立Continueの全byte保持。新artifactはsave/画面/textだけ。
- Files changed: 専用controller/18受入試験/record workflow、Save25正本とtext証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、94/cold13入力、42画面、party差分PP1byte、旧bank/Bag/PC/S61E/全国図鑑保持、42checksum。準備6静的/16controller/7path試験原本再利用、新18受入試験だけ。record native0/ROM変更0/既受入再走0。run37112433649はruntime原本404/native0 failureのまま保存。
- Commit: WIP1c7b23e4/25049912/61d71820、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後、同branch非force pushと全text読戻し。
- Network: 同repoのGitHub/Actions原本のみ。既存ROM/runtimeはActions入力として読取り、新規再配布0。一般CI旧capacity source不一致を成功とせず、merge/release/baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8')as f:f.write(entry)
    write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for n in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+n)==(ROOT/n).read_bytes(),'全text読戻し '+n)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'record|guard|snapshot');actions[sys.argv[1]]()
