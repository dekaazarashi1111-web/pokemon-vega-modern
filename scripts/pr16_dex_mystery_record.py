#!/usr/bin/env python3
"""Mystery Gift候補の成功原本を記録。native/ARM/host再走0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_mystery_failure_actions as isolated_work
import pr16_dex_mystery_ui as work
need,identity,write=work.need,work.identity,work.write
BASE='fd268ac336d3886ba1efb1768d5979e2e18bfdc1';RUN=37244619223;JOB=111559928588;ARCHIVE=(11318148921,RUN,65938,'deefb7e7b2f71346d87f45983b67a82064393065d12d738760246b1ece9ab23d')
DIAGNOSTICS=[(11317964596,37244205003,6735,'33336ac9cb25e65ab9eef000939a2b8e233de57c17da743081b6f7c1b6a489e3')]
WF=work.WF;CODE={WF,'scripts/pr16_dex_mystery_record.py','.github/workflows/pr16-dex-mystery-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_mystery_checkpoint.json';GUIDE=isolated_work.GUIDE;EVIDENCE='content/modernization/pr16_dex_mystery_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-mystery-record';PUBLIC=ROOT/'public-dex-mystery-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized record');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def archive(spec,kind):
 z,_=t.archive(spec)
 with z:files={n:z.read(n)for n in z.namelist()}
 folder=OUT/kind;folder.mkdir()
 for n,b in files.items():
  p=Path(n);need(not p.is_absolute()and'..'not in p.parts and len(p.parts)<=3,'bounded artifact paths');d=folder/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
 module=isolated_work if kind=='isolated'else work;old=module.PUBLIC
 try:module.PUBLIC=folder;module.export()
 finally:module.PUBLIC=old
 return files,folder

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable candidate record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'prior accepted source and terminal state')
 for run,job,head in [(work.RUN,work.JOB,work.BASE),(RUN,JOB,BASE)]:
  r=t.api('actions/runs/'+str(run));j=t.api('actions/jobs/'+str(job));need(r['head_sha']==head and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==run and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'both original all10steps terminal')
 original,of=archive(work.ARCHIVE,'isolated');ui,uf=archive(ARCHIVE,'ui');i=json.loads(original['measurement.json']);m=json.loads(ui['measurement.json']);need('failure.json'not in original and'failure.json'not in ui,'complete successful originals')
 need(i['status']=='PASS_ISOLATED_MYSTERY_SAVE_FAILURE_NOTIFICATION'and i['source_head']==work.BASE and i['isolated']['cases']==816 and i['isolated']['menu_cases']==96 and i['isolated']['scope_cases']==720 and i['native_processes']==1,'isolated menu and scope original')
 need(json.loads(original['isolated-stdout.txt'])==i['isolated']and not original['isolated-stderr.txt'],'whole native isolation raw receipt')
 need(i['candidate']==m['candidate']==dict(size=33554432,sha256='3bb4c51bd8d0155b83ec46b46ea9e5f7440e71860c2f0bb740e7b33ec8fb6d56')and i['link']['payload']['size']==128 and i['placement']['retained_codec_bytes']==5022 and i['placement']['unchanged_owners']==111 and i['placement']['whole_rom_rollback_exact'],'same bounded candidate without ROM reconstruction')
 need(m['status']=='PASS_MYSTERY_GIFT_UI_ONLY_FAILURE_SUCCESS_AND_COLD'and m['run_id']==RUN and m['source_head']==BASE and m['native_processes']==6 and m['ram_fixture_bytes_per_ui_process']==11 and m['register_writes']==0,'three new UI/three cold processes')
 for record,head,exceptions in [(i,work.BASE,{work.OLDWF}),(m,BASE,{WF})]:
  for p,b in record['source_bindings'].items():need(identity(git('show',head+':'+p))==b and(p in exceptions or identity((ROOT/p).read_bytes())==b),'all original source full bytes '+p)
 old=git('show',BASE+':'+WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+WF+']\n').encode();need(old.count(trigger)==1 and(ROOT/WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'successful native workflow manual only')
 import pr16_dex_start_fault_ui as cold
 for case in m['cases']:
  n=case['name'];mode=case['mode'];need(work.validate_trace(ui[n+'/stdout.txt'],uf/n,m['candidate'],mode)==case['trace'],'all pixels and UI events revalidated without native');c=case['cold'];prefix=n+'-cold/cold-'+str(c['counter']);rows=[json.loads(x)for x in ui[prefix+'/stdout.txt'].splitlines()]
  need([x for x in rows if 'observe'in x]==[c['observation']]and[x for x in rows if 'mdx'in x]==[c['mdx']]and rows[-1]==c['end']and c['input']==c['output']==case['save'],'cold whole trace, unchanged full FlashRTC')
  need(cold.screens(rows,uf/prefix)==c['screens'],'cold original full pixels')
 need([x['name']for x in m['cases']]==['main-fault','outer-fault','healthy']and not any(m[k]for k in('natural_entry_accepted','all_nonstart_notifications_accepted','gift_transaction_accepted','formal_rom_changed','formal_save_changed')),'no broad acceptance')
 paths=set();evidence=ROOT/EVIDENCE;evidence.mkdir()
 def retain(files,kind):
  for n,b in files.items():
   if Path(n).suffix not in{'.json','.txt'}:continue
   d=evidence/kind/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b);paths.add(d.relative_to(ROOT).as_posix())
 retain(original,'isolated');retain(ui,'ui');diagnostics=[]
 for spec in DIAGNOSTICS:
  files,folder=archive(spec,'diagnostic-'+str(spec[1]));failure=json.loads(files['failure.json']);need(failure['status']=='DIAGNOSTIC_NOT_ACCEPTED','failure not promoted');retain(files,'diagnostic-'+str(spec[1]));diagnostics.append(dict(run=spec[1],artifact=spec[0],failure=failure))
 with(ROOT/GUIDE).open('a')as out:
  out.write('\n## 受入原本\n\n隔離run'+str(work.RUN)+'は元menu/QOL/inner連鎖96条件＋限定gate720条件、1296実ARM callを受入。UI run'+str(RUN)+'はmain故障・outer末尾故障・正常保存の各既存window表示→通常A待ち→menu帰還、各独立coldを計6process/15画像で確認。候補3bb4c51b、128byte、他111owner/codec5022byte/既存gate保持。main故障ではcounter101維持、outer故障はmain102確定を隠さず失敗表示、正常は102成功表示。\n\nUI entryはcallback/state9byteと、constructor直後のMG task parent17/text0の2byteだけを明示fixture。全EWRAMと他IWRAM byte不変をCPU/frame停止中に照合し、以後はゲーム内処理と通常キーだけ。通常通信/受信/削除/自然入場/field復帰を受け入れない。field windowの一時heap漏れの可能性をこの隔離processに閉じ、正規transitionの検証へ昇格しない。MG setupが自動割当するwindow baseBlock2byteは固定template値と区別し、先頭6byte/template、bitmap所有、範囲/非重複と実heap extentを確認。旧run37244205003は誤った8byte template比較でsetup後/native1・保存0停止、failure原本として保持。menu待機state1への未実行oracle訂正も記録。\n')
 cp=dict(schema_version=1,status='PASS_CANDIDATE_MYSTERY_FAILURE_NOTIFICATION_UI_ONLY',candidate=m['candidate'],isolated=i,ui=m,isolated_run=work.RUN,isolated_job=work.JOB,isolated_archive=work.ARCHIVE,ui_run=RUN,ui_job=JOB,ui_archive=ARCHIVE,diagnostics=diagnostics,visual_review=dict(run=RUN,screens=15,review_ja='同runの全15画面を目視・SHA照合。失敗2例の既存window内2行エラー、正常例の完了文、A後menu、cold fieldを確認。追加native0。'),source_bindings=bindings(isolated_work.CODE|work.CODE|CODE),evidence_bindings=bindings(paths),mystery_failure_notification_accepted=True,mystery_ui_fixture_only=True,natural_entry_accepted=False,gift_transaction_accepted=False,all_nonstart_notifications_accepted=False,hof_save_failed_repair_accepted=False,all_save_modes_accepted=False,all_consumers_wired=False,early_sector31_fault_accepted=False,sector31_atomicity_accepted=False,formal_rom_changed=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0)
 write(ROOT/CP,cp)
 goal=('正式ROM/Save101保持。Mystery Giftだけはreturn無視callerの誤成功を修復。state2のattempt1専用success/非1既存2行error、署名済stack連鎖だけ非破壊failureを受入。isolated816とUI-only main故障/outer末尾故障/正常→入力待ち→menu帰還/各coldを保持。'
 '次はUnionRoomChatの無条件完了文/SE_SAVEと、HOF/共通SaveFailedのtiles16KiB/video/decompression scratch衝突、回数増分とmode4/5 eraseの重複retry、stale selector authority wipeを安全契約に分離修復する。sector31早期故障/原子性、全mode、残typed consumerも未完。全必要影響native前に正式ROM切替・trainer131後半へ進まない。最終はシオウPokecenter通常回復/Save/独立coldContinue、雑魚毎Saveなし。')
 state['story_dex_owner']['runtime_integration']['mystery_failure']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=m['candidate'],isolated_run=work.RUN,ui_run=RUN,record_run=int(os.environ['GITHUB_RUN_ID']),mystery_failure_notification_accepted=True,mystery_ui_fixture_only=True,all_nonstart_notifications_accepted=False,formal_rom_changed=False,formal_save_changed=False)
 state['bp']['current_stop']='正式ROM/Save101保持。Mystery Giftの非START誤成功通知だけ候補修復、既存windowエラー/正常/A待ち/menu帰還/各coldをUI限定受入。HOF/UnionRoomChat/全mode/残consumerは未完。';state['bp']['next_step']=goal;state['next_action'].update(id='CLOSE_REMAINING_NONSTART_FAILURE_AND_SAVE_MODE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_OUTER_QOL_JA.md','docs/PR16_DEX_SAVE_FAILURE_JA.md','docs/PR16_DEX_CONSUMERS_JA.md']);state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='Mystery Gift通知限定候補記録source。正式ROM/Save101不変。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(bindings(isolated_work.CODE|work.CODE|CODE|paths|{CP}));state['do_not_repeat'].append(f'Mystery Gift隔離run{work.RUN} menu96/gate720、UI run{RUN} main故障/outer末尾故障/正常と各coldの6process15画像を無変更再走しない。11byte UI fixtureであり通信/受信/削除/自然入場やHOF/全非STARTへ昇格しない。旧37244205003のnative1/setup後template誤oracle停止はfailure保持。')
 state['observed_head_checks']=dict(scope_head=BASE,isolated_run=work.RUN,ui_run=RUN,ui_job=JOB,both_all10_steps_success=True,new_accepted_native_processes=7,isolated_cases=816,ui_fixture_bytes_per_process=11,all_nonstart_notifications_accepted=False,all_save_modes_accepted=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=state['bp']['current_stop']);publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-MYSTERY-FAILURE / Mystery Gift保存の正しい成否通知\n- Version: dex-mystery-v1\n- Status: DONE（Mystery Gift通知とUI-only縦切り。全非START未完）\n- Summary: state2表示8byteとresult入口8byteを128byteのimmutable suffixへ接続。attempt1だけ成功、非1は元window内2行error。署名済inner/outer stack callerだけ旧SaveFailed回避、bit31はouter実結果まで保持。\n- Files changed: mystery ASM/bindings/generator/native/host/workflow、guide/CP/evidence、固定MDJSON、両ログ。\n- Verify: isolated{work.RUN}全10step/816case1296call、UI{RUN}全10step/6process15画像。UI fixtureは9+2byte限定、register0、7barrier、全他RAM保持。main故障101/outer故障102/正常102、MDX522/party/Bag/故障後20248owner/各coldを照合。112owner/overlap0、codec5022/他111owner/全未宣言ROM保持/逆変換。記録ARM0/native0。\n- Correction: UI診断37244205003はInitWindowsの動的baseBlockを固定template8byteと誤比較しsetup後native1/save0で停止。2byte動的欄だけ正規bitmap/範囲/非重複を検証する後継へ。未実行menu待機oracleもstate2→1へ訂正。失敗原本不変。\n- Boundary: 11byte UI-only入口/parent17であり自然通信/受信/削除/正規transition/heap無漏洩/field帰還は未受入。UnionRoomChat/HOF/全mode/残consumer/早期sector31原子性未完。正式ROM/Save101不変、trainer131後半0。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存入力/固定pret source/公式Ubuntu。公開source/address-size-SHA/text/screensのみ。ROM断片/rawhex/runtime/入力save/runner/credentials追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'prior bound sources all retained');owned={STATE,DOC,CP,GUIDE,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'mystery-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed record readback')
 print('RESULT=DONE TASK=USER-20261004-DEX-MYSTERY-FAILURE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated receipt only')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='mystery-record.json','only exact receipt');b=p.read_bytes();need(0<len(b)<1000000 and b.endswith(b'\n')and b'\0'not in b,'complete bounded JSON');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed record');globals()[sys.argv[1]]()
