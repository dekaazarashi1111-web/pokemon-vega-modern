#!/usr/bin/env python3
"""館内の新野生1勝Save59原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save59_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-NORTHWEST-HALL-SAVE59'
OUT=ROOT/'.local/pr16-story-save59-record'

CODE={'scripts/pr16_story_save59_accept.py','scripts/pr16_story_save59_record.py','tests/test_pr16_story_save59_accept.py',a.VISUAL,'.github/workflows/pr16-story-save59-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE59_JA.md' and a.CP=='content/modernization/pr16_story_save59_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save59_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37156581269,'bae4395664cdfe99ff80a2efd7e8011b76e8077b',111301091588,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save59_measure.',26)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==69 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save58全69member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save58/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==69 and len(z.namelist())==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save59member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==54 and visual['reviewed_screens']==dict(progress=list(range(52)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save59画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save59画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE59_ORIGINAL=str(original),PR16_SAVE58_INPUT=str(assets/'input.srm'),PR16_SAVE59_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save59_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==51 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 51 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'51成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save58-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save59 artifact11286447464のstory-fast.srm（131088bytes/SHA256 b1acf753876e54805a82c8f23aeacd0e9d69824da50c5f0d504720227f0f4552）だけから再開。map1/59・5,7北。未通過接尾辞14歩と新野生オタクン♂Lv9へ1勝、つばめがえし1回/PP12→11、HP288/294・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1保持、Save59/独立Continueを限定受入。上階/有効階段/像の紙は未到達。次は保存済pr16_story_save59_measure.ROUTEの5,7からの接尾辞30歩、北5,6→東28,6→南28,10→東30,10のbehavior108階段warp5→map1/60warp2へ通常入力。最初の新event/戦闘/未通過境界で保存。到着候補32,10/33,10は未測定。旧20,24warp8は床behavior8上の着地点で不発、未保存失敗16入力3画面/native1のSave57原本を保持し同じ北歩行を繰り返さない。紙ownerはmap1/60背景16,28/script149012422・item274/flag4383と静的照合済みだが未取得。26新controller/51新受入、95+cold13入力54画面69member/native2を無影響再走0。RAMledgerは保存menu開始観測27でfd17077e18b3f159f176b300578a7a563adeb077729226917b9d0b2ac9a238c8へ変化しowner未解明、全coldSaveRTC/全暗所field画面同一。46counter59でも部分write、47成功→51field。旧RAM/offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save59_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=26,controller_executions=26,unchanged_controller_cases_replayed=0,new_acceptance_tests=51,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館の北西廊下14歩・新野生1勝・Save59限定受入

`{result['status']}`。Save58の7,13南から南3/西2/北9の通常14歩。5,7で新オタクン♂Lv9に遭遇し、つばめがえし1回で通常撃破。Save59と独立Continue。HP288/294・PP[15,10,15,11]。上階/有効階段/像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。69member/54画面/95+cold13入力。新controller26case、51新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 通常入力と保存

0〜15暗所14歩と南→西→北の向き、16野生遷移/17暗転/18battle。19オタクン♂Lv9、20オノノクスLv100。22slot0/23slot2/24slot3の実技UIでつばめがえしPP12、25撃破/実PP11、26field。battle_flags4/outcome1とwire field:falseの残留を未復帰や追加勝利にしない。

27〜31通常menu0→4、32確認/33上書き、34〜46保存中。46counter59でも部分write、47〜50成功文言/安定Flash、51field。progress26/51とcold0/1は人物と床・右壁の暗所field全byte一致、全SaveRTCも一致。

## 限定差分と未完

全party600bytesの差分はslot3 PP12→11の1byteだけ。全HP/EXP/held item/残party・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save58bank57344byte保持。42checksum、6966byte/1717範囲。aux4021=52→66のruntime owner未解明。RAMledgerは保存menu開始観測27でfd17077e...へ変化しcoldまで同一、owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明も保持。

有効階段30,10への接尾辞30歩が残る。旧20,24着地点warpの不発原本はSave57に保持。紙16,28/item274/flag4383の静的ownerも既読原本を継承し再採取0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save58']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37156581115');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='bae4395664cdfe99ff80a2efd7e8011b76e8077b','旧Stage79終端')
    state['story_save58']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save59']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[5,7],facing=2,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,11],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='保存済経路の未通過接尾辞14歩/新野生1勝/Save59。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館の北西廊下14歩/新野生1勝/Save59。5,7北。次は有効階段30,10への残り30歩。上階/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_EFFECTIVE_STAIRS_FROM_SAVE59',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save59_accept.py','scripts/pr16_story_save59_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save59の5,7以降の接尾辞30歩だけ。新野生1勝/旧14歩を再走しない。次の新event/戦闘/未通過境界で保存。20,24着地点を発火warpとしない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかた北西廊下14歩/新野生1勝でSave59。5,7北。次は有効階段30,10へ残り30歩。上階/像の紙未到達。'
    state['do_not_repeat'].append('Save59の95/cold13入力54画面69member/26controller/51受入を無影響再走しない。新14歩/オタクン♂Lv9へ1勝/PP12→11、46counter部分write→47成功→51field。上階/紙未到達、RAM台帳保存menu観測27/aux4021owner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 館の北西廊下14歩と新野生1勝Save59
- Version: story-mansion-northwest-hall-save59-v1
- Status: DONE（新14歩/野生1勝/保存/独立Continue限定）
- Summary: Save58接尾辞14歩、オタクン♂Lv9へ1勝。HP288/294・つばめがえしPP12→11、他party/Bag/17904円/RP0保持。5,7北で保存、上階/有効階段/紙未到達。
- Files changed: Save59 measure/26controller/51受入/record、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。95+cold13入力54画面69member。新26controller原log継承/51新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: party599byte/HP/EXP/持物/全Bag/legacy flags/PC/S61E保持、PP1消費だけ。46counter部分write→47成功→51field、全SaveRTC/暗所4画面一致。RAMledger保存menu観測27とaux4021owner未解明。旧bank57344byte/42checksum/6966byte1717範囲。
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



