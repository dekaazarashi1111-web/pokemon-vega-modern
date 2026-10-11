#!/usr/bin/env python3
"""解禁後西側teleportのSave33原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save33_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-CAVE-EAST-TELEPORT-SAVE33'
OUT=ROOT/'.local/pr16-story-save33-record'
CODE={'scripts/pr16_story_save33_accept.py','scripts/pr16_story_save33_record.py','tests/test_pr16_story_save33_accept.py',a.VISUAL,'.github/workflows/pr16-story-save33-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE33_JA.md' and a.CP=='content/modernization/pr16_story_save33_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save33_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37122527387,'8d97e9de625f4b28b9c1b6bc7a30e5582812eba6',111201313311,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save33_measure.' in v]
    need(len(tests)==15 and any('Ran 15 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更15controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==79 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save32全79member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save32/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==46 and len(z.namelist())==47 and set(z.namelist())==set(manifest)|{'manifest.json'},'全46member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==31 and visual['reviewed_screens']==dict(progress=list(range(29)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全31画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全31画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE33_ORIGINAL=str(original),PR16_SAVE32_INPUT=str(assets/'input.srm'),PR16_SAVE33_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save33_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==24 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新24受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save32-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=15,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save33 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・8,10西・party4/RP0・13128円・badge1・story4071=7/4072=1。東岩階段23,14とflag4367=1の正規19,14→8,10teleport、Save33/独立Continueを受入。'
      'ミュウツーHP322/354・PP[1,14,0,0]、party/Bag/PC/S61E/所持金は不変。れいとうビーム/火炎放射を選ばず通常UIの残存技/必要時通常回復だけ。host回復/PP/flag/var注入は禁止。'
      '保存済全920マスと7,5のcoord6nodeから西側区間を調べ、var4071=7でtrainer360を含む次の正規eventへ向かう。8,10から踏み直し転送で東へ戻らない経路を選ぶ。静的壁だけで出口不可と決めず必要ならmap-load動的地形ownerだけ照合。'
      '物理出口4,19はmap1/38へ、隣接warp4,6はmap3/21へ接続する静的表。通常到達/洞窟走破/全国図鑑は未完。'
      '69/cold13入力・31画面・新15controller/24受入試験、Save1〜32を無影響再走しない。補助var4021=115/4022=2のruntime ownerは未解決。'
      'trainer352/360、洞窟出口、HM05原因、全国図鑑、自然成長進化、全storyは未完。既存ROM/runner/runtimeはActions入力だけ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save33_accepted=True,east_stair_accepted=True,west8_10_teleport_accepted=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=15,new_acceptance_tests=24,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 東岩階段・解禁後teleport・Save33 限定受入

`{result['status']}`。Save32の21,19から東岩階段23,14/上段23,13を通過し、flag4367=1の正規19,14→8,10転送と通常Save33/独立Continueを受入。戦闘0。洞窟出口/次event/trainer360は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全46member、69/cold13入力、31画面。階段8/上段9、trigger17、着地18/解錠19、書込中23〜26、保存文言27/field28。counter33先行の26を保存完了へ昇格せず、全Flash完成27を区別。

party全600byte/HP322/PP[1,14,0,0]、Bag/HM05/所持金13128/PC/S61E全payload不変。legacy flags不変、story4071=7/4072=1・flag4367=1・badge1保持。補助var4021=103→115/4022=0→2のruntime ownerは未解決。42sector checksum/S61E CRC・旧Save32bank57344byte・全Save/RTC cold同一、6970byte/1779範囲差分。候補内のcheckflag/goto_ifと両warp実30byteを独立照合。

15controller試験は測定原logを保持して再走0。新24受入/拒否試験だけ実行。地形採取/旧受入試験/native再走/ROM変更/compile/fixture0。Save32記録run37122527387全11step終端を固定JSONに反映し、旧失敗原本は変更しない。一般CI全成功/releaseは主張しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save32']['record_completion']=prior_done
    state['story_save33']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[8,10],facing=3,rp=0,money=13128,badge_count=1,story_vars={'4071':7,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,east_stair_accepted=True,west8_10_teleport_accepted=True,story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='東岩階段/解禁後転送/Save33を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='東岩階段/解禁後19,14→8,10/Save33測定source。洞窟出口/全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_WEST_EVENT_FROM_SAVE33',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save33_measure.py',a.m.PREP,'content/modernization/pr16_story_cave_route_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save33の8,10西から先だけ。PP[1,14,0,0]、正規UIだけで西側eventへ。既受入東階段/転送を再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='東岩階段と解禁後19,14→8,10転送、Save33/独立Continue受入。戦闘0、13128円/party4/RP0/badge1・HP322/PP[1,14,0,0]。西側event/洞窟出口未完。'
    state['do_not_repeat'].append('Save33の69/cold13入力・31画面・新15controller/24受入試験を無影響再走しない。全46memberを保持。解禁後teleportを次event/洞窟走破へ昇格しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 東岩階段と解禁後西側転送Save33
- Version: story-cave-unlocked-teleport-save33-v1
- Status: DONE（階段/転送/保存限定。西側event/洞窟出口/全国図鑑未完）
- Summary: Save32から東岩階段を通過しflag4367=1の正規19,14→8,10転送、通常Save33/独立Continueを受入。戦闘0、party全600byte/HP322/PP[1,14,0,0]・Bag・所持金13128・PC/S61E不変。
- Files changed: Save33 controller/15変更試験/24受入試験/record workflow、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、69/cold13入力・31画面・全46member。階段8/上段9、trigger17/着地18/解錠19、部分write4状態23〜26/counter33先行26、保存文言27/field28。42checksum/6970byte差分/全SaveRTC不変。legacy flags/story維持、補助var4021=103→115/4022=0→2（runtime owner未解決）。実warp30byte独立照合。15controller原本再利用、新24受入/拒否試験だけ実行してstderr保存。record native0/ROM変更0/旧ゲーム再走0。
- History: Save32記録run37122527387全11step終端を反映。旧失敗原本は変更しない。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本だけ。既存ROM/runtime/input Save32再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with(ROOT/name).open('a',encoding='utf-8')as f:f.write(entry)
    write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for n in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+n)==(ROOT/n).read_bytes(),'全text読戻し '+n)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'record|guard|snapshot');actions[sys.argv[1]]()
