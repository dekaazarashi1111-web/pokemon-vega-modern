#!/usr/bin/env python3
"""Save100の動的Ranger会話と町解放を独立受入し固定引継ぎ/両ログ同期。native0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT),str(ROOT/'tests')]
import pr16_story_save100_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-RANGER-SAVE100';OUT=ROOT/'.local/pr16-story-save100-record'
CODE={'scripts/pr16_story_save100_accept.py','scripts/pr16_story_save100_record.py','tests/test_pr16_story_save100_accept.py',a.VISUAL,'content/modernization/pr16_story_save100_next_route.json','.github/workflows/pr16-story-save100-record.yml','content/modernization/pr16_story_save100_pre_dispatch.json'}
def unpack_verified(artifact,run,archive,source,target,count):
    meta,z=a.transport.archive(artifact,run,archive,source);target.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==count and set(z.namelist())==set(manifest)|{'manifest.json'},'全manifest member')
        need(all(Path(n).suffix in{'.srm','.ppm','.txt','.json'}and not n.startswith('/')and'..'not in n.split('/')for n in z.namelist()),'新save/画面/textのみ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'全member '+n)
        z.extractall(target)
    return meta,manifest

def controller_receipt():
    receipts=[]
    for job,count in [(111425480014,38),(a.JOB,1)]:
        raw=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode();log=raw.splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save100_measure.'in v]
        need(len(lines)==count and all(v.endswith(' ... ok')for v in lines)and any('Ran '+str(count)+' test'in v for v in log),'新38+訂正1成功行の原本再読だけ')
        receipts.append(dict(job=job,executions=count,test_lines=lines))
    import test_pr16_story_save100_measure as tests
    need(unittest.defaultTestLoader.loadTestsFromModule(tests).countTestCases()==39,'39case loadだけ/再走0')
    need(h.d.git('show','aa8b788fd93ee5c3481ec8298ec3ecc6ea8221e3:scripts/pr16_story_save100_measure.py')==(ROOT/'scripts/pr16_story_save100_measure.py').read_bytes(),'測定controllerは不変')
    name='tests/test_pr16_story_save100_measure.py';prior=ast.parse(h.d.git('show','aa8b788fd93ee5c3481ec8298ec3ecc6ea8221e3:'+name));current=ast.parse((ROOT/name).read_bytes())
    for cls in current.body:
        if isinstance(cls,ast.ClassDef):cls.body=[f for f in cls.body if not(isinstance(f,ast.FunctionDef)and f.name=='test_parent_binding_exact')]
    need(ast.dump(prior)==ast.dump(current),'旧38caseのAST不変、新規親binding検査だけ追加')
    return dict(final_cases=39,executions=39,passed_executions=39,failed_executions=0,unchanged_success_reruns=0,receipts=receipts)

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新記録1回だけ')
    need(a.GUIDE=='docs/PR16_STORY_SAVE100_JA.md'and a.CP=='content/modernization/pr16_story_save100_checkpoint.json','今回専用宛先')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入は不変')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37197809471,'8d12d98794bb91673597b074e2ea2be11665f5ae',111423190429,['success']*11)
    controller=controller_receipt()
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==119 and set(z.namelist())==set(mf)|{'manifest.json'},'親Save99全119member')
        for n,b in mf.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save99/不変ROM')
    original=OUT/'original';meta,manifest=unpack_verified(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE,original,69)
    failed=OUT/'failed-preflight-original';failed_meta,failed_mf=unpack_verified(11302405444,37198607755,dict(size=1636,sha256='d0a587c415309941fb2d27aebb6fa1d2eed16a680e7bdac914afe8a8ec973d44'),'aa8b788fd93ee5c3481ec8298ec3ecc6ea8221e3',failed,2)
    failure=h.d.read(failed/'failure.json');need(failure==dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type='ValueError',message='親dynamic計画exact binding',native_processes=0,source_head='aa8b788fd93ee5c3481ec8298ec3ecc6ea8221e3',run_id=37198607755),'旧失敗原本/native0を保持')
    failure_run=h.d.inputs.api('actions/runs/37198607755');need(failure_run['head_sha']=='aa8b788fd93ee5c3481ec8298ec3ecc6ea8221e3'and failure_run['conclusion']=='failure'and failure_run['status']=='completed','旧run failureのまま')
    failed_receipt=dict(artifact_id=11302405444,archive=dict(size=1636,sha256='d0a587c415309941fb2d27aebb6fa1d2eed16a680e7bdac914afe8a8ec973d44'),failure=failure,normalization_used=False,parent_fixture_unchanged=True,reason_ja='正本末尾改行込みのbyteは10384byte。ローカル転送写しだけに末尾改行1個が加わり10385byteとなった。正本や検査を緩和せず期待bindingを正本へ訂正。38成功controllerは再走せず、新規exact binding1検査のみ。')
    pre=h.d.read(ROOT/'content/modernization/pr16_story_save100_pre_dispatch.json');need(pre['parent_fixture_binding']==identity((ROOT/'content/modernization/pr16_story_save99_next_route.json').read_bytes()),'pre-dispatchの正本byte照合')
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==54 and visual['reviewed_screens']==dict(progress=list(range(52)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全54原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'原画 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE100_ORIGINAL=str(original),PR16_SAVE99_INPUT=str(assets/'input.srm'),PR16_SAVE100_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save100_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==62 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for p in sorted(original.rglob('*')):
        if not p.is_file()or p.suffix not in{'.json','.txt'}:continue
        raw=p.read_bytes();raw.decode();need(b'\0'not in raw,'tracked textのみ');dest=evidence/p.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'controller-test-receipt.json',controller);write(evidence/'next-route.json',a.next_route());write(evidence/'save99-record-terminal.json',prior_done)
    for p in failed.rglob('*'):
        if p.is_file():
            dest=evidence/'failed-preflight-original'/p.relative_to(failed);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    write(evidence/'failed-preflight-receipt.json',failed_receipt)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}

    rule=a.next_route()['transition_preflight_rule_ja'];byte_rule=a.next_route()['byte_binding_pre_dispatch_rule_ja']
    goal='Save100 artifact11302156714のstory-fast.srm（131088bytes/SHA256 9a4185c74f4906eb05de0167f082fa70de166caf42c5aa6bf7a9fe85bfee77ff）だけから再開。ミルシティ3/2・4,17北。実Ranger20,29の正面20,28南から通常会話、warp5,16→自動2歩→ダグトリオ解放→最初fieldでSave100/Continueを限定受入。4072=3/4380set、4352最終set、4382/4383/紙0/4061=1/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。回復分岐なし/新戦闘0/プレイヤー捕獲0。次は西へ4歩、通常西connection3/24・53,13候補を固定床behavior0/offset4/逆offset-4/実画面で確認し、最初の新fieldでSave101/独立Continue。Ranger/解放scene/博物館/接近61歩を再走しない。4021=93/4022=3、通常2歩だけ加算でscript自動2歩は加算なし、次friendship周期35歩。progress RAM454211fdとcold1a34e64cは別hash、owner未解明。過去RAM53/42/2056も保持。95+cold13入力/54画面、45最終Flash一致でもcounter99/保存中、46counter100で別途中hash、47安定hash/成功、51clearfield。cold全SaveRTC保持、pixel差564/408/588は花animation11tileだけ。39controller=初回38成功＋訂正1、新62受入、native成功2/失敗0/事前失敗1/記録native0/旧成功再走0。初回run37198607755は正本写しの末尾改行hash差でnative0停止し原本不変。'+byte_rule+' Save99記録run37197809471全11step終端同期。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。全国図鑑/自然成長進化/全story/release未受入。一般CI既知qol_production.c不一致を全成功としない。'+rule
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save100_accepted=True,ranger_interaction_accepted=True,dugtrio_road_block_removed=True,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=39,controller_executions=39,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=1,record_native_processes=0,failed_preflight=failed_receipt,next_goal_ja=goal,transition_preflight_rule_ja=rule,byte_binding_pre_dispatch_rule_ja=byte_rule,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# 動的Ranger会話・ダグトリオ解放・Save100限定受入

`{result['status']}`。Save99から通常2歩/2旋回で、実画面のRanger20,29の正面20,28南へ。連続2frameの位置を確認してA1回。町へのwarpと自動イベントを完了し、最初の操作可能field4,17北でSave100/独立Continue。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。69member/54画面/95+cold13入力。39controller（38+訂正1）/62新受入。成功native2/失敗0/事前失敗1/記録native0/旧成功再走0。

## 会話・町の連続script

観測0/1はRanger20,28、2から20,29へ移動。主人公は18,28→19,28→20,28、4/5で南向き正面を連続確認。6〜9で手紙到達を受けた台詞、10fade、11町5,16、12自動移動4,17。12〜19のキャプチャ/リリース台詞、20/21で3頭移動、23で障害消失、24別れ、25最初の操作可能field。NPCsceneのキャプチャをプレイヤーの捕獲/戦闘受入にしない。

固定会話は4382set/4380false→4072=2/4352clear/町warp。町の4072=2条件scriptが自動開始し、4380set/4352set/4072=3で終了。回復処理は別分岐なのでHP277/294とPP3,9,8,2保持。全party600byte/全Bag/23114円/紙0/4061=1/バッジ2保持。

通常2歩の4021=91→93/4022=1→3。scriptによる2歩は今回歩数counterへ加算されない。次friendship周期まで35歩。S61E payload差はbyte259の224→240、expanded4380だけ新set。CRC・全42sector checksum・PC・旧Save99 bank57344byte・全coldSaveRTC一致。全7145byte/1790範囲。

## 保存の中間状態・冷起動

26〜30通常menu0→4、31/32確認、33〜46保存中。45は最終Flashhashと同じでもcounter99、46はcounter100だが別途中hash、47で安定hash/保存成功文言、51でclearfield。瞬間hash/counterだけで完了扱いしない。

progress RAM454211fdからcold1a34e64cへ変化するがcold2観測は一致。全SaveRTC131088byte不変とは別の観測でありowner未解明。過去RAM53/42/physical2056の未解明も維持。progress/cold差564/408px、cold間588pxは目視確認した11tileの花animationだけで、主人公/通路は保持。全pixel一致とは主張しない。

## 事前失敗とbyte binding

run37198607755/job111425480014は親計画のhash不一致でnative0停止。artifact11302405444原本のfailure/manifestをそのまま保持。正本10384byteに対し転送写し10385byteだった。正本を改変せず、期待hashを正本の最終改行込みbyteへ訂正。初回38成功testを再走せず、新exact binding1caseのみ実行。{byte_rule}

## 次

{goal}
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本不変')
    state['story_save99']['record_completion']=prior_done
    state['story_save100']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[4,17],facing=2,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':3},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],ranger_interaction_accepted=True,dugtrio_road_block_removed=True,flag4380=True,flag4352=True,museum_admission_var4061=1,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_route=a.EVIDENCE+'/next-route.json',next_goal_ja=goal,transition_preflight_rule_ja=rule,byte_binding_pre_dispatch_rule_ja=byte_rule)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='動的Ranger正面会話と町のダグトリオ解放をSave100で保存。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='Save100/ミルシティ4,17北。動的Ranger20,29へ実正面A→町の解放scene→4072=3/4380set。全party600byte/HP277/PP3,9,8,2/23114円保持。95+cold13入力/54画面。通常2歩+自動2歩、歩数93/3。cold RAM差owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stop='Save100の4,17北から西connectionへ。最初の新fieldでSave101/独立Continue。解放済Ranger/町scene/61歩接近を再走しない。'+rule+' '+byte_rule
    state['next_action'].update(id='STORY_TOWN_WEST_CONNECTION_FROM_SAVE100',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save100_accept.py','scripts/pr16_story_save100_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save100_next_route.json','content/modernization/pr16_story_save100_pre_dispatch.json'],stop_rule_ja=stop)
    state['do_not_repeat'].append('Save100の95/cold13入力54画面69member、動的Ranger正面A/町解放/通常2歩/自動2歩、39controller/62新受入を無影響再走しない。初回binding失敗原本はnative0。'+byte_rule)
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='Save100/ミルシティ4,17北。Ranger実正面会話/ダグトリオ解放完了、4072=3/4380set/全party保持。次は西connection候補へ。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'''
## {stamp}
- Version: PR16-STORY-SAVE100
- Timestamp: {stamp}
- Task: {TASK} / 動的Ranger会話・町解放とSave100
- Status: DONE（会話/解放scene/保存/Continue限定。全国図鑑/自然進化/全story未完）
- Summary: 実画面のRanger20,29に20,28南から通常A。町warp5,16→自動2歩→ダグトリオ解放→最初field4,17北でSave100/Continue。4072=3/4380set。回復分岐なし。
- Files changed: Save100 measure/controller/preparation/独立受入62/visual/record/checkpoint/text証拠/次west plan/pre-dispatch契約、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、39controller（38+訂正1）/62新受入。95+cold13入力/54画面/69member/native2/失敗0/事前失敗1/記録native0/旧成功再走0。7145byte1790範囲/42checksum/全SaveRTC/PC/S61E/旧bank保持。
- Evidence: 45最終Flashhash一致でもcounter99/保存中、46counter100/別途中hash、47安定hash/成功文言、51clearfield。progress/cold564/408px、cold間588pxは花animation11tileだけ。RAMprogress/cold差owner未解明。
- Owner: 通常2歩の4021=91→93/4022=1→3、script自動2歩は加算なし。固定町4072=2条件script→4380set/4072=3。次friendship周期35歩。過去RAM53/42/2056等の未解明を維持。
- Failure: run37198607755/job111425480014は親計画写しの末尾改行追加でhash不一致/native0。正本byte不変のまま期待binding訂正、38成功検査再走0/新1検査。artifact11302405444を原本のまま保存。
- Terminal sync: Save99記録run37197809471/job111423190429全11step成功を同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。一般CI既知不一致を全成功にしない。
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

