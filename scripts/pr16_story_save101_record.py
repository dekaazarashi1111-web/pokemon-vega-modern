#!/usr/bin/env python3
"""Save101独立受入とmilestone方針/次施設を固定引継ぎ・両ログへ同期。native0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT),str(ROOT/'tests')]
import pr16_story_save101_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-STORY-MILESTONES';OUT=ROOT/'.local/pr16-story-save101-record'
CODE={'scripts/pr16_story_save101_accept.py','scripts/pr16_story_save101_record.py','tests/test_pr16_story_save101_accept.py',a.VISUAL,'content/modernization/pr16_story_save101_next_milestone.json','.github/workflows/pr16-story-save101-record.yml','content/modernization/pr16_story_save101_pre_dispatch.json'}
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
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode();lines=[v.split('Z ',1)[-1]for v in log.splitlines()if' ... 'in v and('test_pr16_story_save101_measure.'in v or'test_pr16_story_milestones.'in v)]
    need(len(lines)==63 and all(v.endswith(' ... ok')for v in lines)and'Ran 63 tests'in log,'63新controller成功原本を再読/再走0')
    return dict(executions=63,passed_executions=63,unchanged_success_reruns=0,test_lines=lines)
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入不変')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37199540423,'4730763b5ba68e4e5c77b2c3b4226acf8b590d25',111428199096,['success']*11)
    controller=controller_receipt()
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==69 and set(z.namelist())==set(mf)|{'manifest.json'},'親Save100全69member')
        for n,b in mf.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a;_,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save100/不変ROM')
    original=OUT/'original';meta,manifest=unpack_verified(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE,original,50)
    visual=h.d.read(ROOT/a.VISUAL);need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==35 and visual['reviewed_screens']==dict(progress=list(range(33)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全35原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'原画 '+n)
    result=a.verify(original,before,rom);assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE101_ORIGINAL=str(original),PR16_SAVE100_INPUT=str(assets/'input.srm'),PR16_SAVE101_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save101_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==47 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 47 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'47新独立受入と正確な終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for p in sorted(original.rglob('*')):
        if not p.is_file()or p.suffix not in{'.json','.txt'}:continue
        dest=evidence/p.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    write(evidence/'verification.json',result);write(evidence/'measurement-terminal.json',done);write(evidence/'save100-record-terminal.json',prior_done);write(evidence/'controller-receipt.json',controller);write(evidence/'next-milestone.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save101 artifact11303305200のstory-fast.srm（131088bytes/SHA256 '+a.OUTPUT['sha256']+'）だけから再開。506番道路3/24・53,13西。解放後の町から通常西接続、5歩/1旋回/新戦闘0、通常Save101/独立Continueを地域milestoneとして受入。HP277/294・PP3,9,8,2、全party600byte/Bag/23114円/2badge/4072=3/4352・4380・4382・4383保持。4021=98/4022=3、friendship周期まで30歩。次の意味ある到達点は506→519→シオウシティのPokecenter7/3で通常回復/Save/fresh Continue。相互connection3/24→3/37→3/3、町door22,19→7/3 warp0、nurse7,2/counter7,3/対面候補7,4北を固定ROMから照合。全tile経路・trainer視線・野生/資源observer・counter会話ownerは実行前に解決。西出口登録だけで通行可としない。対応済通常戦はcompact ledgerへ記録して宣言済milestoneへ継続、全雑魚戦ごとのSaveを作らない。未知callback/event/warp/owner/UI/観測差/資源不足は診断停止し、milestone達成とは呼ばない。下流はシオウジム11/3・キリtrainer418・badge2084のmajor milestone。正常4072=9→10/研究所special367/var11の全国図鑑、その後の別progression自然EXP/進化/LuckyEgg/12境界/Lv100soakは未完。Save25〜100証拠、RAM53/42/Save100差/2056未解明を保持。汎用継続host検査を連戦native受入にしない。58+cold13入力35画面/新63controller/47受入/native2/記録native0/旧成功再走0。一般CI既知QOL source不一致やfinalHEAD action_requiredを全成功としない。ROM/runtime再公開/flag注入/進化回避/新balance/merge/release/baseline切替0。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save101_accepted=True,west_connection_accepted=True,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=63,new_acceptance_tests=47,successful_native_processes=2,record_native_processes=0,prior_accepted_evidence_unchanged=True,milestone_policy='docs/PR16_STORY_MILESTONE_CONTRACT_JA.md',next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# 解放後の西地域接続・Save101限定受入

`{result['status']}`。Save100からミルシティの西端へ4歩、通常西connectionで506番道路3/24(53,13)西へ。解放後の地域接続という宣言済milestoneで保存/独立Continue。5歩/1旋回、戦闘・会話・warp0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。50member/35画面/58+cold13入力。新63controller/47独立受入、成功native2/記録native0/旧成功再走0。

## 原本と保存境界

0北→1西旋回、2〜5西4歩、6道路field。7〜11menu0→4、12/13保存確認、14〜27保存中、27counter101でも途中hash、28保存成功hash/文言、32clearfield。counterや瞬間hashだけで完了としない。全SaveRTC131088byteはcold不変。progress32=cold1全pixel一致、cold0との588pixelは11花tile。全party600byte/Bag/23114円/2badge/4072=3/S61E/PC/旧Save100bank保持。差分7128byte/1807範囲、42sector checksums。5歩で4021=93→98、4022=3→3。

今回のprogress/cold RAMは全観測同一。過去Save100の異なるRAMhash、Save53/42、physical2056等のowner未解明を解決済みにはしない。

## 方針の修正

所有者計画は『全雑魚戦ごとのcheckpointは作らない』。Save25〜100は歴史的受入として保持し、そこで生成された停止手順を以後の一般方針へ継承しない。新規milestone契約は通常戦episodeを台帳化して継続する。対応済type/正規outcome/field復帰/実HP・PP/ownerを要求し、未知callback・event・warp・UI・story effect・観測差・資源不足を診断停止に分離する。

今回は非草地西接続なのでnative戦闘0。任意の戦闘後HP/PPを既存partyhashだけから解決するadapterは未実装であり、複数戦host検査をnative連戦受入へ昇格しない。

## 次の実在する施設

固定ROMのmap接続を追い、506番道路→519番道路→シオウシティ、町の22,19入口→Pokecenter7/3を確認。nurseは7,2、7,3は衝突1/behavior128のcounterなので7,4北からの会話ownerを確認する。店7/6はボードショップで回復施設ではない。506北門18/0の出口は3/42なので短絡経路と推測しない。全tile経路と障害/戦闘owner/資源を解決後、通常回復と保存再開を次milestoneにする。次のmajor badgeはキリtrainer418/map11/3/flag2084。

{a.next_route()['next_goal_ja']}

## 残件

{goal}
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本不変')
    state['story_save100']['record_completion']=prior_done
    state['story_save101']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,24],xy=[53,13],facing=3,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':3},lead_hp=[277,294],lead_pp=[3,9,8,2],record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_milestone='content/modernization/pr16_story_save101_next_milestone.json',next_goal_ja=goal)
    state['story_milestone_policy']=dict(owner_plan='docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md',contract='docs/PR16_STORY_MILESTONE_CONTRACT_JA.md',ordinary_battle_checkpoint=False,diagnostic_stop_is_milestone=False,accepted_save25_to100_retained=True,native_multi_battle_continuation_accepted=False,observer_adapter_pending=True)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='解放後西region接続Save101とmilestone方針。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='Save101/506番道路53,13西。通常西connection5歩/1旋回/58+cold13入力/35画面/全party・資源保持。次シオウPokecenter。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MILESTONE_SHIOU_CENTER_FROM_SAVE101',goal_ja=goal,read_paths=['docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md','docs/PR16_STORY_MILESTONE_CONTRACT_JA.md',a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_milestones.py','scripts/pr16_story_save101_accept.py','content/modernization/pr16_story_save101_next_milestone.json'],stop_rule_ja='通常戦ごとの保存を廃止し宣言済milestoneまで継続。未知owner/callback/event/warp/UI、観測不一致、資源不足は診断停止。診断frontierを完了扱いしない。実行前に全tile/戦闘observer/回復counterを解決。')
    state['do_not_repeat'].append('Save101の58/cold13入力35画面50member/63controller/47受入/native2を無影響再走しない。Save25〜100証拠は保持し、当時のfirst-battle stopを一般方針にしない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='Save101/506番道路53,13西。解放後の地域接続milestone受入。次は506→519→シオウPokecenter通常回復。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'''
## {stamp}
- Version: PR16-STORY-SAVE101-MILESTONES
- Timestamp: {stamp}
- Task: {TASK} / 意味ある到達点までの継続契約と解放後西地域接続
- Status: DONE（西接続Save101限定、全story/連戦nativeは未完）
- Summary: 町から通常西connection→506の53,13西。5歩/1旋回、新戦闘0、通常Save/fresh Continue。所有者計画を正本とし、通常戦ごと保存ではなくcompact episode ledger→milestone継続/診断停止に分離。
- Files changed: milestone制御/契約/Save101計測/独立受入/visual/checkpoint/text証拠/次施設owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、63新controller、47新受入。58+cold13入力/35画面/50member/native2/記録native0/旧成功再走0。7128byte1807範囲/42checksum/全SaveRTC/party600/PC/S61E/旧bank保持。
- Owner: 接続offset4/逆-4/両端behavior0。4021=93→98/4022=3→3、次friendship周期30歩。progress32=cold1全pixel一致、cold0との588pixelは11花tile。古いRAM差/2056不明は維持。
- Next facility: 固定ROM506→519→シオウのPokecenter7/3、入口22,19、nurse7,2/counter7,3/会話候補7,4北。次badgeはキリtrainer418/2084。全tile到達/戦闘後resource observerは未実装/未受入。
- Terminal sync: Save100記録run37199540423/job111428199096全11step成功。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。同branch非forcepush/全text読戻し。
- Network: 同repoGitHub/Actions、読取用文字decode照合 https://raw.githubusercontent.com/pret/pokefirered/master/charmap.txt 。ROM/runtime非再配布/ROM変更/host補充/merge/release/baseline切替0。一般CI既知QOL不一致/finalHEAD action_requiredを緑にしない。
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

