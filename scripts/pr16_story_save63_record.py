#!/usr/bin/env python3
"""館内の新8歩・北東階段による上階初到達Save63原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save63_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-UPPER-STAIR-SAVE63'
OUT=ROOT/'.local/pr16-story-save63-record'

CODE={'scripts/pr16_story_save63_accept.py','scripts/pr16_story_save63_record.py','tests/test_pr16_story_save63_accept.py',a.VISUAL,'.github/workflows/pr16-story-save63-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE63_JA.md' and a.CP=='content/modernization/pr16_story_save63_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save63_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37160527253,'f89219a5eb6fe1562c592892447ffc376e3c4bb8',111312845996,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save63_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==71 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save62全71member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save62/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==56 and len(z.namelist())==57 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save63member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==41 and visual['reviewed_screens']==dict(progress=list(range(39)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save63画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save63画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE63_ORIGINAL=str(original),PR16_SAVE62_INPUT=str(assets/'input.srm'),PR16_SAVE63_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save63_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==50 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 50 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'50成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save62-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save63 artifact11287229492のstory-fast.srm（131088bytes/SHA256 76dacf781f2e6cf3f44521223cf0c9228e9ca7e04ce26fadeabceba4c1777c87）だけから再開。初上階map1/60・32,10東。新8歩/方向転換2/北東階段30,10→warp2を限定受入し、通常Save63・独立Continue済み。HP288/294・PP15,10,15,6、全party600byte/Bag/18744円/RP0/badge1/story4071=9/4072=1/PC保持。次は保存済route-planの上階32,10→33,10→34,10から31,21の穴へ40歩の未通過接尾辞。最初の新event/戦闘/不通境界で保存。上階北部と紙側は静的非連結で、穴31,21→入口31,22→南東階段30,29→上階33,29→紙背面16,27が未検証候補。紙/穴作動/南東階段は未到達。27新controller/50新受入、69+cold13入力41画面56member/native2。32一時最終Flash、33counter63部分write、34成功→38field。最終field全画面/coldSaveRTC一致。physical2056解除とaux4021:89→97/4022:0→3、RAM台帳は36変化、runtime owner未解明。旧offset41/aux404d/40ac保持。Flash未使用/がくしゅうそうち未装備。受入済み通路/戦闘/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save63_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,inert_warp8_activation=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=50,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館の北東階段・初上階Save63限定受入

`{result['status']}`。Save62から新8歩・方向転換2で入口階30,10の階段へ。map1/60・32,10東に初到達、通常保存・独立Continue。戦闘0。像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。56member/41画面/69+cold13入力。新controller27case、50新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 実階段と保存

0開始、1〜10の間に新8歩・南/東へ転換2。10で30,10階段、11でmap1/60・32,10へ通常warp1回。到着11は「こころのやかた」banner付き。12〜16menu0→4、17確認/18上書き。19〜33保存中、32のFlashは一時的に最終hashと一致、33counter63でも部分write、34〜37成功文言、38field。終端38/cold0/cold1の全画面byte一致、全SaveRTC一致。map名bannerのある11を終端画像と同一扱いしない。

## 保存差分と未完

party全600byte/HP288/294/PP15,10,15,6・ミュウツー全HP/PP・EXP/持物・全Bag/18744円/RP0・PC/S61E全payload・旧Save62bank57344byte保持。physical2056の1→0、aux4021の89→97/4022の0→3だけをlegacy差分として固定。runtime ownerは未解明でstory成功へ昇格しない。RAM台帳は36の保存成功文言中に変化。42checksum/6890byte1674範囲。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。

紙までの候補は[Save62時点の静的経路](../content/modernization/pr16_story_save62_evidence/route-plan.json)を再利用。今回だけ北東階段の1接続を実測受入した。上階北部40歩/穴31,21/入口南東階段/紙側の接続は未実測。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save62']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37160527066');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='f89219a5eb6fe1562c592892447ffc376e3c4bb8','旧Stage79終端')
    state['story_save62']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save63']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[32,10],facing=4,rp=0,money=18744,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,6],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,inert_warp8_activation=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan='content/modernization/pr16_story_save62_evidence/route-plan.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新8歩/北東階段/初上階Save63。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館の新8歩/北東階段から初上階map1/60・32,10東/Save63。全party保持・戦闘0。紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_UPPER_NORTH_SUFFIX_FROM_SAVE63',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save63_accept.py','scripts/pr16_story_save63_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save63上階32,10東から穴31,21への未通過40歩候補。最初の新event/戦闘/不通境界で保存。旧北東階段/旧戦闘/旧保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかた北東階段から上階に初到達しSave63。map1/60・32,10東、全party/HP/PP保持。紙への上階北部40歩は未通過。'
    state['do_not_repeat'].append('Save63の69/cold13入力41画面56member/27controller/50受入を無影響再走しない。新8歩/転換2/北東階段warp1/戦闘0。32一時最終Flash→33counter63部分write→34成功→38field、全SaveRTC/最終field画面一致。RAM台帳36変化owner未解明。穴/紙の接続をnative受入にしない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 北東階段から上階初到達Save63
- Version: story-mansion-upper-stair-save63-v1
- Status: DONE（新8歩/通常階段1/保存/独立Continue限定）
- Summary: Save62の26,6から新8歩で階段30,10、初上階map1/60・32,10東。全party600byte/HP288/294/PP15,10,15,6/Bag/18744円/RP0保持。戦闘0・紙未到達。
- Files changed: Save63 measure/27controller/50受入/record、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。69+cold13入力41画面56member。新27controller原log継承/50新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: 32一時最終Flash→33counter63部分write→34成功→38field。全SaveRTC/最終field画面一致。RAM台帳36変化owner未解明。physical2056解除/aux4021:89→97・4022:0→3。旧bank57344byte/42checksum/6890byte1674範囲。上階北部40歩/穴31,21/南東階段/紙は未実測。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredは全成功にしない。merge/release/baseline変更0。
- Next: {goal}
"""
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



