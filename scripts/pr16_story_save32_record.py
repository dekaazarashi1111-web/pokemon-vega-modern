#!/usr/bin/env python3
"""Save32原本の独立受入・固定引継ぎ・同branch記録。native再走なし。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save32_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-SOUTH-TRAINER-SAVE32'
OUT=ROOT/'.local/pr16-story-save32-record'
PREPARATION_CODE={'scripts/pr16_story_save32_inspect.py','.github/workflows/pr16-story-save32-inspect.yml'}
CODE={'scripts/pr16_story_save32_accept.py','scripts/pr16_story_save32_record.py','tests/test_pr16_story_save32_accept.py',a.VISUAL,'.github/workflows/pr16-story-save32-record.yml'}

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE32_JA.md' and a.CP=='content/modernization/pr16_story_save32_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save32_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    preparation_done=inherited.terminal(37121423789,'e8b5e13b4775188258420edbb5754ed919823458',111198130088,['success']*8)
    prior_done=inherited.terminal(37120967764,'c0327a3c9f0cf9940a7cb2b11c508c4ce87dd985',111196833683,['success']*11)
    failedrun=h.d.inputs.api('actions/runs/37122292424');failedjob=h.d.inputs.api('actions/jobs/111200634955')
    need(failedrun['head_sha']=='730146ee64b35f6e7feac264680cedf4d46a6033' and failedrun['status']=='completed' and failedrun['conclusion']=='failure' and failedjob['steps'][2]['conclusion']=='failure' and failedjob['steps'][3]['conclusion']=='skipped','初回record sourceguard失敗終端')
    failed=dict(run=h.d.run_summary(failedrun),job=failedjob,native_processes=0,tests_executed=0,artifact_count=0,reason_ja='strict guardのCODEへ比較base以前に追加済みの採取器2pathを含め、変更集合不一致で停止。CODEは実差分5pathへ限定し、採取器の保全bindingは別PREPARATION_CODEへ分離。入力/ROM/測定/旧試験を再走しない。')
    failed2run=h.d.inputs.api('actions/runs/37122423332');failed2job=h.d.inputs.api('actions/jobs/111201015523')
    need(failed2run['head_sha']=='67dd53f092e82ea5836bdbd2aec64fee2b8accdf' and failed2run['status']=='completed' and failed2run['conclusion']=='failure' and failed2job['steps'][2]['conclusion']=='success' and failed2job['steps'][3]['conclusion']=='failure','第2record bytes型失敗終端')
    failed2=dict(run=h.d.run_summary(failed2run),job=failed2job,native_processes=0,tests_executed=0,artifact_count=0,reason_ja='中間party独立モデルはbytearray。既存identity関数がexact bytesを要求するため受入unit起動前に停止。モデルをbytesへ凍結する1箇所だけ修正。ゲーム測定/既受入試験再走0。')
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save32_measure.' in v]
    need(len(tests)==12 and any('Ran 12 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更12controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==37 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save31全37member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save31/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==79 and len(z.namelist())==80 and set(z.namelist())==set(manifest)|{'manifest.json'},'全79member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==64 and visual['reviewed_screens']==dict(progress=list(range(62)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全64画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全64画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE32_ORIGINAL=str(original),PR16_SAVE31_INPUT=str(assets/'input.srm'),PR16_SAVE32_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save32_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==24 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新24受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save31-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'failed-record-terminal.json',failed);write(evidence/'failed-record-bytes-terminal.json',failed2);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'preparation-terminal.json',preparation_done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=12,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save32 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・21,19東・party4/RP0・13128円・badge1・story4071=7/4072=1。南段差14,15の通常通過とtrainer353通常1勝/416円/Save32/独立Continueを受入。'
      'ミュウツーHP322/354・PP[1,14,0,0]、他party/Bag/S61Eは不変。以降はれいとうビームと火炎放射を選ばず、通常UIの別技/必要時通常回復だけ。host回復/PP/flag/var注入は禁止。'
      '保存された全920マス（既存164+未読756）の静的原本から、21,19→22,19→23,19→23,14東岩階段→23,13→21,13→21,14→19,14へ向かう。'
      'flag4367=1の正規teleport先8,10は未到達。7,5のcoordはvar4071=7でtrainer360を含む6node/var4071=8へ続くが未発火。静的壁だけで西側出口が不可能とは判断せずmap-load動的地形ownerも必要時だけ照合する。'
      '物理出口4,19はmap1/38へ、その隣接warp4,6はmap3/21へ接続する静的表。通常到達/洞窟走破/全国図鑑は未完。'
      '138/cold13入力・64画面・新12controller/24受入試験、Save1〜31を無影響再走しない。補助var4021=103/4022=0のruntime ownerは未解決。'
      'trainer352/360、東階段、解禁後teleport、洞窟出口、HM05原因、全国図鑑、自然成長進化、全storyは未完。既存ROM/runner/runtimeはActions入力だけ、新公開artifactは新save/画面/textだけ。')

    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save32_accepted=True,trainer353_accepted=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|PREPARATION_CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=12,new_acceptance_tests=24,record_native_processes=0,failed_record_run=37122292424,failed_record_runs=[37122292424,37122423332],failed_record_tests_executed=0,next_goal_ja=goal,
      release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 南回廊・trainer353・Save32 限定受入

`{result['status']}`。Save31の14,14から南段差14,15を通過し、21,19でlocal7の視線戦に入った。D・H団したっぱ/trainer353を通常UIで1勝、報酬416円、通常Save32と独立Continueを受入。東岩階段/teleport/洞窟出口は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / 323646bytes / SHA256 `{a.ARCHIVE['sha256']}`。全79member、138/cold13入力、64画面。接触14、battle17、勝利outcome50、field復帰53、保存成功文言60、安定field61。通常Save中の3部分writeとcounter32を区別。独立Continue0/1ではbattle残留値0。

ダンゴロLv10の頑丈/オレンのみで2回、ブロロンLv13とドガースLv12に各1回のれいとうビーム。交代質問は2回とも拒否。HP324→322、PP4→0。全600byte party差分はoffset55の4→0とoffset86の68→66だけ。保存親から5中間partyを独立再構成し画面/RAM hashと一致。Bag/HM05/全PC/S61E payload不変、12712→13128円、legacy flag1633=1280+353だけ0→1。正規NPC root0x093709A0を独立decodeしてtrainer353へ結合。story4071=7/4072=1・flag4367=1・badge1保持。補助var4021=93→103/4022=2→0のruntime ownerは未解決。42sector checksum/S61E CRC・旧Save31bank57344byte・全Save/RTC cold同一、6973byte/1782範囲差分。

未読地形採取run37121423789/job111198130088は全8step成功、native0。既存164マスを再利用して未読756マスだけ追加し、全920マスを固定。3隣接map/7,5 coordの6nodeは静的だけ。新12controller原logを保持して再走0、新24受入/拒否試験を1回実行して全stderr保存。初回record37122292424はstrict sourceguardの変更集合不一致で停止、受入試験0/native0。比較base以前の採取器2pathをCODEから保全専用bindingへ分離し、失敗log/APIを保持。第2record37122423332は中間party bytearrayをstrict bytes identityへ渡してunit前停止。bytes化1箇所だけ修正、受入unit0/native0。旧failure原本保持、ROM変更0/compile0/fixture0/既受入再走0。Save31記録run37120967764の全11step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save31']['record_completion']=prior_done
    state['story_save32_preparation']=dict(run_id=37121423789,job_id=111198130088,artifact_id=11273700621,status='completed',conclusion='success',native_processes=0,inherited_cells=164,new_cells=756,source_head='e8b5e13b4775188258420edbb5754ed919823458',checkpoint=a.m.PREP)
    state['story_save32']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[21,19],facing=4,rp=0,money=13128,badge_count=1,story_vars={'4071':7,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,trainer353_accepted=True,story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='南回廊/trainer353通常勝利/Save32を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='南回廊/trainer353/Save32測定source。東階段/teleport/洞窟出口/全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_EAST_STAIRS_FROM_SAVE32',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save32_measure.py',a.m.PREP,'content/modernization/pr16_story_cave_route_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save32の21,19東から先だけ。PP[1,14,0,0]、既受入trainer353を再戦しない。通常技選択のみ、host回復/解禁禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='南回廊→21,19東でtrainer353通常1勝/416円。Save32/独立Continue受入。13128円/party4/RP0/badge1、HP322/PP[1,14,0,0]。東階段/teleport/洞窟出口は未完。'
    state['do_not_repeat'].append('Save32の138/cold13入力・64画面・新12controller/24受入試験を無影響再走しない。全79memberと既存失敗原本を保持。trainer353勝利を東階段/teleport/洞窟走破へ昇格しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|PREPARATION_CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 南回廊とtrainer353通常勝利Save32
- Version: story-cave-south-trainer-save32-v1
- Status: DONE（trainer353/保存限定。東階段/teleport/洞窟出口/全国図鑑未完）
- Summary: Save31の14,14から南段差を通過し、21,19でtrainer353を通常UIで1勝。報酬416円/HP324→322/れいとうビームPP4→0、通常Save32/独立Continueを受入。頑丈/オレンのみのダンゴロLv10、ブロロンLv13、ドガースLv12、交代拒否2回。
- Files changed: 未読地形採取器、Save32 controller/12変更試験/24受入試験/record workflow、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: 地形run37121423789全8step成功、既存164+新756マス/7,5の6node静的。測定run{a.RUN}/job{a.JOB}全8step成功、138/cold13入力・64画面・全79member。party差分2byte、5中間partyを独立再構成、legacy flag1633だけ/正規trainer353 root、Bag/PC/S61E/全国図鑑保持、補助var4021は93→103/4022は2→0（runtime owner未解決）。42checksum/6973byte差分/全SaveRTC保持。新12controller原本再利用、新24受入だけ実行して全stderr保存。record native0/ROM変更0/旧ゲーム再走0。
- Failure: 初回record37122292424/job111200634955はsourceguard変更集合不一致。採取器2pathは比較base以前のためCODEから分離し保全binding維持。受入試験0/native0/artifact0、失敗Actions原logを保持。
- Failure: 第2record37122423332/job111201015523は中間partyのbytearray型をidentityが拒否してunit起動前停止。bytes化だけ修正、受入unit0/native0/artifact0。失敗Actions原logを保持。
- History: Save31記録run37120967764全11step終端を反映。旧native/record失敗原本を保持。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本だけ。既存ROM/runtime/input Save31再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
