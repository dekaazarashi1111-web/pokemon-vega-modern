#!/usr/bin/env python3
"""保存済みSave26の限定受入と同branch記録。native再走/私有原本再配布0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save26_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-SOUTH-SAVE26'
OUT=ROOT/'.local/pr16-story-save26-record'
CODE={'scripts/pr16_story_save26_accept.py','scripts/pr16_story_save26_record.py','tests/test_pr16_story_save26_accept.py',
      a.VISUAL,'.github/workflows/pr16-story-save26-record.yml'}

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'初回新規記録だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    OUT.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37113873113,'dbb50b3c13ce33d7a8576d9a24178af9e056a49a',111176793864,['success']*10)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save26_measure.' in v]
    need(len(tests)==15 and any('Ran 15 tests in ' in v for v in log) and any(v.endswith(' OK')for v in log),'15成功controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save25全原本')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.a.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'親Save25/同一ROM固定')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==51 and len(z.namelist())==52 and set(z.namelist())==set(manifest)|{'manifest.json'},'全51原本member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..' not in n.split('/') for n in z.namelist()),'新公開save/画面/textだけ')
        need(not any(n.endswith('.gba') or n=='runner' or n.startswith(('runtime/','private-inputs/')) for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==37 and
         visual['reviewed_screens']==dict(progress=list(range(35)),**{'continue':[0,1]}) and visual['save_success_wording_observed'] is True,'全37画面目視')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視全byte '+n)
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全37画面anchor完全')
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    os.environ.update(PR16_SAVE26_ORIGINAL=str(original),PR16_SAVE25_INPUT=str(assets/'input.srm'),PR16_SAVE26_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save26_accept.py','-v'],capture_output=True,timeout=120)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==20 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新20受入/拒否試験のみ')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save25-record-terminal.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
                 'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0' not in raw,'tracked textのみ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job_id=a.JOB,passed_tests=15,replayed_tests=0,test_lines=tests))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save26 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
          'map1/73・32,15西・party4/RP0・12712円・badge1・story4071=6/4072=1。野生ディグダLv6の通常1勝、Save26/独立Continueは完了。'
          '次は32,15から西へ23,15、岩階段23,14→23,13、19,13→19,14の正規coord teleportを通常入力で確認する。'
          'trainer352（30,13）/353（21,17）は未対戦、残り経路は静的候補だけ。ミュウツーPP[1,14,1,5]/HP324、オノノクスPP[15,10,15,20]/HP294。'
          '残PPを実技UIで扱い、host回復/flag/var解禁は禁止。既存候補ROM/runnerはSave24 artifact11263343138、runtimeは11263910704をhash固定してActions入力のみ再利用。'
          '新公開artifactは新save/画面/textだけ。84/cold13入力・15controller/新20受入試験・Save1〜25は無影響再走しない。'
          'teleport/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
        record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save26_accepted=True,teleport_accepted=False,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
        prior_controller_tests=15,new_acceptance_tests=20,record_native_processes=0,next_goal_ja=goal,
        release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟南通路・Save26 限定受入

`{result['status']}`。31,7南から東南を迂回し32,15西へ通常進行。野生ディグダ♀Lv6を火炎放射1回で倒し、通常Save26/独立Continueを受入。trainer352/353やteleportは未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / 212283bytes / SHA256 `{a.ARCHIVE['sha256']}`。全51member、84/cold13入力、37画面を照合。遭遇遷移16、戦闘17〜25、勝利/解錠26、保存成功文言33、安定field34。warmのfield:false残留はcallback/lockで区別し、cold0/1ではtrue。追加勝利には数えない。

Save26 `{a.OUTPUT['sha256']}` / 131088bytes。party600byte差分は火炎放射PP2→1のみ。HP/EXP/種族/4技/道具/OT、全Bag/HM05、所持金12712、全trainer/story flags保持。補助var4021だけ40→53、runtime ownerは未解決。旧Save25bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6906byte/1743範囲差分。

15controller試験成功原本を再利用し、新20受入/拒否試験だけを実行。record native0、旧受入再走0、ROM変更/compile/fixture0。新artifactは新save/画面/textだけ。一般CI全成功やreleaseは主張しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save25']['record_completion']=prior_done
    state['story_save26']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
        story_fast_save=a.OUTPUT,map=[1,73],xy=[32,15],facing=3,rp=0,money=12712,badge_count=1,story_vars={'4071':6,'4072':1},
        hm05_owned=True,hm05_taught_or_used=False,teleport_accepted=False,cave_crossing_complete=False,
        record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],
        reason_ja='洞窟東南の野生1勝とSave26/独立Continueを限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='洞窟南通路/野生1勝/Save26測定source。全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_SOUTH_FROM_SAVE26',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save26_measure.py','content/modernization/pr16_story_save25_preparation.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],
        stop_rule_ja='Save26の32,15西から先だけ。野生1勝/保存済み入力を再走しない。未到達trainer/teleportを受入へ昇格しない。host解禁禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='洞窟南通路32,15西で野生ディグダLv6を通常1勝、Save26/独立Continue受入。12712円/party4/RP0/badge1。残PP[1,14,1,5]。trainer352/353/teleport/洞窟走破は未完。'
    state['do_not_repeat'].append('Save26の84/cold13入力・15controller/新20受入試験を無影響再走しない。37画面/全51memberを保持。野生1勝をtrainer勝利や自然成長へ昇格しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟南通路とSave26
- Version: story-cave-south-save26-v1
- Status: DONE（新区間野生1勝/保存限定。洞窟走破/全story未完）
- Summary: 31,7から東南を迂回し32,15西。野生ディグダLv6に火炎放射1回で勝利、通常Save26と独立Continue。新artifactはsave/画面/textだけ。
- Files changed: Save26専用controller/20受入試験/record workflow、checkpointとtext証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、84/cold13入力・37画面・全51member。party差分PP1byte、旧bank/Bag/PC/S61E/全国図鑑/全flags保持、42checksum。15controller試験原本再利用、新20受入試験だけ。record native0/ROM変更0/既受入再走0。
- Commit: WIP3fde7851、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push、全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save25はActions入力だけ。一般CI旧capacity source不一致は保持、merge/release/baseline変更0。
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
