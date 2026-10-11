#!/usr/bin/env python3
"""封書badge gate・新ミルジム入口Save76原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save76_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-LETTER-GATE-GYM-ENTRY-SAVE76'
OUT=ROOT/'.local/pr16-story-save76-record'

CODE={'scripts/pr16_story_save76_accept.py','scripts/pr16_story_save76_record.py','tests/test_pr16_story_save76_accept.py',a.VISUAL,'content/modernization/pr16_story_save76_gym_route.json','.github/workflows/pr16-story-save76-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE76_JA.md' and a.CP=='content/modernization/pr16_story_save76_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save76_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37170311449,'ed3fe324e74ef4d769fc1afed1157b748fd1c617',111341779688,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save76_measure.',28)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==51 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save75全51member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save75/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==58 and len(z.namelist())==59 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save76member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==43 and visual['reviewed_screens']==dict(progress=list(range(41)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save76画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save76画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE76_ORIGINAL=str(original),PR16_SAVE75_INPUT=str(assets/'input.srm'),PR16_SAVE76_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save76_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==50 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 50 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'50成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save75-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save76 artifact11291861689のstory-fast.srm（131088bytes/SHA256 10c7d4b96e2b36db13158ba3a8d8929caabac28275e98e01a93c586b0315d836）だけから再開。紙274のconsumerは博物館2階map6/1・local2/4,9、badge0x823確認後check/removeitem274→flag4382。現badge1/0x823未setで引渡し未解禁。先にナギナタのミルジム10/16へ新通常入場、6,18北でSave76/独立Continueを受入。次は保存済gym-owner/routeから初ディグダlocal5/6,14の初期4372〜4378と台詞/配置変更を照合し、6,15まで新北3歩＋通常A。最初の新event/battleで通常保存。紙1個/flag4383・全party600byte/HP288/294・PP9,10,15,2/Bag19416円/PC/S61E/全RAM台帳保持。28新controller/50新受入、77+cold13入力43画面58member/native2。34最終hash先行counter75→35counter76/別一時hashでも保存中→36成功→40field。全SaveRTC/ジムfield全pixel一致。physical2056:0→1/aux4021:71→85/4022:3→2/404d:44→33のruntime owner未解明。ジム攻略後に博物館研究者へ紙引渡し→505道路レンジャー。紙引渡し/ジム攻略/全story/全国図鑑/自然成長・進化/LuckyEgg/研究施設自然到達未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save76_accepted=True,gym_entered=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=28,controller_executions=28,unchanged_controller_cases_replayed=0,new_acceptance_tests=50,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 封書のbadge gate・新ミルジム入口Save76限定受入

`{result['status']}`。町15,20南から東5歩/北9歩/北扉への通常入力でミルジムmap10/16・6,18北へ到着。旋回2回。自動北1歩はなし。初入場で通常Save76/独立Continue、新戦闘0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。58member/43画面/77+cold13入力。新controller28/新受入50。native2/record0/旧成功再走0/ROM変更0。

## 封書の正規consumerと前提

[保存済みconsumer](../content/modernization/pr16_story_save76_preparation.json)。博物館2階map6/1・local2/4,9、root0x08e1c302。badge0x823がなければ「ミルジムのナギナタさんを倒せないようでは」と断る。badge確認後のcheckitem274→removeitem274→flag4382。flag4383は像からの取得側。引渡し後の案内は505番道路のポケモンレンジャー。現badge1/0x823未set、引渡しは未実行。

受取人不明のため、既読graph116nodeと町直結ownerを再利用しても見つからず、原425mapのROM-rooted参照indexを読取専用で採取した。旧43group pointerは現relocation先と同一。9decoder診断/不正rootを保持し、全graph完全性は主張しない。今回の陽性consumer/leader151命令と11文字列だけを同一ROMで固定し、native検査時に全命令byteを照合。全ROMのbyte pattern searchなし。今後は保存済みownerを使用し全域再採取しない。

## 実入力・保存

1東旋回/7北旋回、17北扉中→18ジム6,18北。19〜23menu0→4、24確認/25上書き。26〜35保存中、34最終hash先行/counter75、35counter76でも別一時hash/未完、36〜39成功、40field。全SaveRTCとprogress40/cold0/cold1全pixel一致。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/flag4383/PC/S61E/全RAM台帳保持。physical2056:0→1、aux4021:71→85/4022:3→2/404d:44→33。runtime owner未解明。42checksum/6985byte1743範囲、旧Save75bank57344byte保持。

## 次

[初ディグダownerと北3歩](../content/modernization/pr16_story_save76_gym_route.json)。実到着6,18から先だけ。旧館内/町歩行/ジム入場を再走しない。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save75']['record_completion']=prior_done
    state['story_save76']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[6,18],facing=2,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_entered=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='封書badge gateと新ジム入口Save76。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='紙consumerを博物館2階local2/required badge0x823へ同定。未取得のため新ミルジム入場Save76/6,18北。全party/紙保持。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_FIRST_DIGLETT_FROM_SAVE76',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save76_accept.py','scripts/pr16_story_save76_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save76_preparation.json','content/modernization/pr16_story_save76_gym_route.json'],stop_rule_ja='Save76/ジム6,18北だけから開始。初ディグダlocal5のownerと保存flagsを照合して北3歩＋A。最初の新境界で通常保存。badge/紙引渡しを捏造せず、旧入場/館/町区間を再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='紙のconsumer/badge gateを同定。新ミルジム入場でSave76/6,18北。全party/HP/PP/紙保持、次は初ディグダ。'
    state['do_not_repeat'].append('Save76の77/cold13入力43画面58member/28controller/50受入を無影響再走しない。封書consumer博物館2階local2/required badge0x823、現1badgeで未解禁。新ジム6,18北/紙/全party/全RAM保持。34最終hash先行→35counter76別hashも保存中→36成功→40field。全SaveRTC/全pixel一致。次は北3歩/初ディグダ。ROM-rooted紙consumer参照indexと選択ownerは再採取不要。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 封書badge gate・新ミルジム入口Save76
- Version: story-letter-gate-gym-entry-save76-v1
- Status: DONE（consumer陽性同定/新ジム入場/保存/独立Continue限定）
- Summary: 封書274の消費者は博物館2階local2、required badge0x823。現1badgeで未解禁なのでミルジム10/16へ通常入場し6,18北でSave76。全party600byte/HP288/PP9,10,15,2/Bag19416円/紙/PC/S61E/全RAM台帳保持。
- Files changed: Save76 preparation/measure/28controller/50受入/record/checkpoint/text証拠/初ディグダowner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。77+cold13入力43画面58member。新controller28原log継承/新受入50。record native0/compile0/旧成功再走0。
- Evidence: 34最終hash先行counter75→35counter76/一時別hash/未完→36成功→40field。全SaveRTC/field全pixel一致。42checksum/6985byte1743範囲。2056 set/aux3変数owner未解明。封書引渡し/ジム攻略は未受入。
- Discovery: 原425mapをrooted参照indexで照合し陽性consumerを同定。9decoder診断/不正rootを保持、全域の完全性は未主張。今後は選択consumer/ジムownerを再利用し全域採取を再走しない。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repo GitHub/Actionsだけ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredを全成功にしない。merge/release/baseline変更0。
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




