#!/usr/bin/env python3
"""HOF局所候補の原本と限界を固定正本へ記録。追加native0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_hof_ui as work
import pr16_dex_hof_failure_actions as isolated_work
need,identity,write=work.need,work.identity,work.write
BASE='6d75cf77c77f89a6d2541114f796e67ff06efd85';RUN=37255103782;JOB=111590380492;ARCHIVE=(11322322595,RUN,68085,'ebe197a5d3e935ac631c4d5d883b44b6b8b0277fa5e96c7ac38b95218e5eff95')
DIAGNOSTICS=[(11322212855,37254213792,23771,'f7bc3341f4d6a6e076b60bc6a55cebfed68a27211f86695bee2446dba599d8f4'),(11321363562,37254589135,24274,'0d198bc543b49506497a9fb5a7bd6cfccfcd3a764acca286f72b8b28eb70548a')]
WF=work.WF;VISUAL='content/modernization/pr16_dex_hof_ui_visual_review.json';CODE={WF,VISUAL,'scripts/pr16_dex_hof_record.py','.github/workflows/pr16-dex-hof-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_hof_checkpoint.json';GUIDE=isolated_work.GUIDE;EVIDENCE='content/modernization/pr16_dex_hof_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-hof-record';PUBLIC=ROOT/'public-dex-hof-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized HOF record');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft')
def source_guard():
 import pr16_learnset_runtime_record as g,pr16_dex_publication as publication
 current();publication.contract(ROOT,'.github/workflows/pr16-dex-hof-record.yml',PUBLIC,'pr16-dex-hof-record-receipts','scripts/pr16_dex_hof_record.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def archive(spec,kind,ui=False):
 import pr16_dex_publication as publication
 publication.consumer(t.api('actions/artifacts/'+str(spec[0])),work.ARTIFACT if ui else isolated_work.ARTIFACT,spec[1]);z,_=t.archive(spec)
 with z:files={n:z.read(n)for n in z.namelist()}
 folder=OUT/kind;folder.mkdir()
 for n,b in files.items():
  p=Path(n);need(not p.is_absolute()and'..'not in p.parts and len(p.parts)<=3,'bounded original path');dest=folder/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 module=work if ui else isolated_work;old=module.PUBLIC
 try:module.PUBLIC=folder;module.export()
 finally:module.PUBLIC=old
 return files,folder

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume,pr16_dex_start_fault_ui as cold
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one new HOF record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'all original sources and terminal state retained')
 for run,job,head in[(work.RUN,work.JOB,work.BASE),(RUN,JOB,BASE)]:
  r=t.api('actions/runs/'+str(run));j=t.api('actions/jobs/'+str(job));need(r['head_sha']==head and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==run and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'both source runs all10success')
 original,of=archive(work.ARCHIVE,'isolated');ui,uf=archive(ARCHIVE,'ui',True);i=json.loads(original['measurement.json']);m=json.loads(ui['measurement.json']);need('failure.json'not in original and'failure.json'not in ui,'complete successful originals');need(i['status']=='PASS_ISOLATED_HOF_FAILURE_NOTIFICATION'and i['source_head']==work.BASE and i['native_processes']==1 and i['isolated']['cases']==2880,'HOF2880 isolated conditions');need(json.loads(original['isolated-stdout.txt'])==i['isolated']and not original['isolated-stderr.txt'],'full isolated trace exact')
 need(i['candidate']==m['candidate']==dict(size=33554432,sha256='40ad82373b1e0f49283f59dce1e68a009b3e548d8f3ff080b72a134a228b0ac2')and i['link']['payload']['size']==260,'same exact candidate and new260byte');pl=i['placement'];need(pl['unchanged_owners']==113 and len(pl['owner_byte_audit'])==113 and all(r['unchanged']for r in pl['owner_byte_audit'])and pl['allocation']['summaries']['allocation_count']==114 and pl['allocation']['summaries']['overlap_count']==0 and pl['whole_rom_rollback_exact'],'all113 owners exact and new114th owner nonoverlap');need(pl['tail_reference_audit']['literal_candidates']==22 and pl['tail_reference_audit']['thumb_bl_candidates']==3 and pl['tail_reference_audit']['unclassified_candidates']==0,'all apparent references typed')
 need(m['status']=='PASS_HOF_UI_ONLY_FAILURE_SUCCESS_AND_COLD'and m['source_head']==BASE and m['native_processes']==6 and m['ram_fixture_bytes_per_ui_process']==9,'only HOF UI/cold6 processes')
 for case in m['cases']:
  folder=uf/case['name'];need(work.validate_trace((folder/'stdout.txt').read_bytes(),folder,m['candidate'],case['mode'])==case['trace']and not(folder/'stderr.txt').read_bytes(),'whole UI trace revalidated without native');cd=case['cold'];cf=uf/(case['name']+'-cold')/('cold-'+str(cd['counter']));rows=[json.loads(x)for x in(cf/'stdout.txt').read_bytes().splitlines()];need(not(cf/'stderr.txt').read_bytes()and rows[-1]==cd['end']and cold.screens(rows,cf)==cd['screens'],'cold full trace and pixels identity');need([x for x in rows if'hof_cold_metadata'in x]==[cd['hof_metadata']]and cd['hof_metadata']['stat10']==case['physical_stat10'],'cold physical/live stat coherence')
 previous=json.loads((ROOT/'content/modernization/pr16_dex_union_checkpoint.json').read_bytes());previous_cases={c['name']:c for c in previous['ui']['cases']};ledger_boundary=[]
 for case in m['cases']:
  old=previous_cases[case['name']]['cold'];got=case['cold'];need(got['hof_metadata']['ledger_sha256']==got['observation']['ledger_sha256']==old['observation']['ledger_sha256']and got['mdx']['save_file_status']==old['mdx']['save_file_status'],'cold QOL behavior exactly matches preserved predecessor by case');ledger_boundary.append(dict(case=case['name'],ledger_sha256=got['hof_metadata']['ledger_sha256'],save_file_status=got['mdx']['save_file_status'],same_as_predecessor=True,all_cold_owners_preserved_claimed=False))
 need(ledger_boundary[0]['ledger_sha256']!=ledger_boundary[1]['ledger_sha256']==ledger_boundary[2]['ledger_sha256'],'main-fault fallback difference explicitly retained, not full QOL restoration acceptance')
 need([(c['name'],c['mode'])for c in m['cases']]==[('main-fault',1),('outer-fault',2),('healthy',0)],'exact three cases in original order')
 for case in m['cases']:
  cd=case['cold'];rows=[json.loads(x)for x in ui[case['name']+'-cold/cold-'+str(cd['counter'])+'/stdout.txt'].splitlines()];need([r for r in rows if'observe'in r]==[cd['observation']]and[r for r in rows if'mdx'in r]==[cd['mdx']]and cd['input']==cd['output']==case['save'],'whole cold observation and FlashRTC identities')
 visual=json.loads((ROOT/VISUAL).read_bytes());images={n:identity(b)for n,b in ui.items()if n.endswith('.ppm')};need(visual['run']==RUN and visual['source_head']==BASE and tuple(visual['archive'])==ARCHIVE and visual['actual_pixels_reviewed']and visual['screens']==15 and visual['images']==images,'explicit actual15pixel review bound to every original SHA')
 paths=set();diagnostics=[]
 for label,files in [('isolated',original),('ui',ui)]:
  for n,b in files.items():
   if Path(n).suffix not in{'.json','.txt'}:continue
   p=EVIDENCE+'/'+label+'/'+n;need(not(ROOT/p).exists(),'immutable new evidence');dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(p)
 for spec in DIAGNOSTICS:
  files,folder=archive(spec,'diagnostic-'+str(spec[1]));failure=json.loads(files['failure.json']);need(failure['status']=='DIAGNOSTIC_NOT_ACCEPTED','failure stays diagnostic');diagnostics.append(dict(run=spec[1],archive=spec,failure=failure))
  for n,b in files.items():
   p=EVIDENCE+'/diagnostic-'+str(spec[1])+'/'+n;dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(p)
 failed_record=dict(run=37255522627,job=111591624002,source='4a9fb9681221c2a36a0e7fa76d23904a5b127362',archive=[11322422260,37255522627,31412,'2c3115b214fae76f740d208101a35ef115f36627fea5460063d62d612203fdbe'],native_processes=0,commit_push_performed=False,reason_ja='原本再検査後、text-only最終index guardがPPMのGit取込を拒否。既存guardは保持し、画像はActions原本＋全SHA束縛、Git証拠はJSON/TXTへ限定。')
 r=t.api('actions/runs/37255522627');j=t.api('actions/jobs/111591624002');need(r['head_sha']==failed_record['source']and r['status']=='completed'and r['conclusion']=='failure'and j['run_id']==failed_record['run']and next(x for x in j['steps']if x['number']==5)['conclusion']=='failure'and next(x for x in j['steps']if x['number']==7)['conclusion']=='skipped','prior guard stopped before commit')
 z,_=t.archive(tuple(failed_record['archive']))
 with z:need(z.namelist()==['hof-record.json'],'one retained rejected-index receipt');failed_raw=z.read('hof-record.json')
 p=EVIDENCE+'/record-index-diagnostic.json';write(ROOT/p,dict(**failed_record,receipt_identity=identity(failed_raw)));paths.add(p)
 cp=dict(schema_version=1,status='PASS_HOF_NOTIFICATION_UI_ONLY_NO_RETRY',candidate=m['candidate'],isolated=i,ui=m,isolated_run=work.RUN,isolated_job=work.JOB,isolated_archive=work.ARCHIVE,ui_run=RUN,ui_job=JOB,ui_archive=ARCHIVE,diagnostics=diagnostics,record_preflight_diagnostics=[failed_record],visual_review=visual,cold_ledger_boundary=ledger_boundary,all_cold_owners_preserved=False,extension_snapshot_phase="FIRST_FLASH_PROGRAM",hof_fixture_bytes=9,cold_input_fixture_derived=True,hof_failure_notification_accepted=True,hof_old_failure_screen_avoided=True,hof_initial_stat_increment_preserved=True,hof_automatic_retry=False,hof_initial_save_atomicity_accepted=False,common_failure_all_callers_accepted=False,all_save_modes_accepted=False,all_consumers_wired=False,early_sector31_fault_accepted=False,sector31_atomicity_accepted=False,natural_entry_accepted=False,full_hof_species_abi_accepted=False,formal_rom_changed=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0,source_bindings=bindings(isolated_work.CODE|work.CODE|CODE),evidence_bindings=bindings(paths));write(ROOT/CP,cp)
 summary='HOF実callerの誤成功音を抑止し、既存窓のエラー→新規A→元演出を候補限定受入。旧SaveFailed/wipe/自動再保存0。同sessionのstat10は0→1を一度だけ保持（主故障coldは0、外側故障/正常coldは1）。payload8192byteは演出遷移まで、初回Flash program時点以降の拡張20248byteは全保持。9byte UI-only入口/主保存故障・sector31末尾故障・正常/各cold。初回mode3原子性と全caller共通SaveFailed、全mode/残consumerは未完。主故障cold101のQOL ledger差は前Union/Mysteryと同一の既存fallback差で、全cold owner復元を受入しない。'
 with(ROOT/GUIDE).open('a')as out:out.write('\n## 候補限定受入\n\n'+summary+'\n\n隔離run'+str(work.RUN)+'は2880条件/1process。UI run'+str(RUN)+'は6process/15画像を原本SHAと実pixelで確認。新114owner/overlap0/既存113owner全byte保持・全ROM逆変換。2つの初期診断は実行ファイル名とbyte比較observerの不具合であり、受入へ改称しない。\n')
 cp['source_bindings'][GUIDE]=identity((ROOT/GUIDE).read_bytes());write(ROOT/CP,cp)
 goal='正式ROM/Save101を保持。HOFの局所通知/旧SaveFailed回避を9byte UI-onlyと各coldで限定受入。次は初回mode3 stock委譲の保存世代/28・29とmainの整合、mode4/5 erase・default/LinkFull等全mode、未対応caller共通SaveFailedとstale selector authority wipeを安全契約へ分離。主保存故障cold時のQOL ledger差も既存fallback契約として解明。早期sector31故障/単bank原子性、残typedconsumerも未完。必要証拠が揃うまで正式切替とtrainer131後半を保留し、owner承認不足と誤認しない。最終はシオウPokecenter通常回復/Save/独立coldContinue、雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_failure']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=m['candidate'],isolated_run=work.RUN,ui_run=RUN,record_run=int(os.environ['GITHUB_RUN_ID']),fixture_bytes=9,cold_input_fixture_derived=True,hof_initial_save_atomicity_accepted=False,common_failure_all_callers_accepted=False,formal_rom_changed=False,formal_save_changed=False)
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='CLOSE_INITIAL_HOF_AND_REMAINING_SAVE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_UNION_FAILURE_JA.md','docs/PR16_DEX_OUTER_QOL_JA.md','docs/PR16_DEX_CONSUMERS_JA.md']);state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='HOF局所通知/9byte入口とcoldの候補受入記録source。正式ROM/Save101不変。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(isolated_work.CODE|work.CODE|CODE|paths|{CP,GUIDE}));state['do_not_repeat'].append('HOF40ad8237候補の局所通知は隔離2880条件＋UI-only9byte/3条件/各cold6process15画像。旧SaveFailed回避と初回stat10一度・payload保全まで。初回mode3原子性/全mode/自然殿堂入りへ広げず、同じnativeを影響なしに再走しない。')
 state['observed_head_checks']=dict(scope_head=BASE,isolated_run=work.RUN,isolated_job=work.JOB,ui_run=RUN,ui_job=JOB,both_all10_steps_success=True,accepted_raw_native_processes=7,diagnostic_native_processes=sum(d['failure']['native_processes']for d in diagnostics),fixture_bytes=9,screens=15,all_save_modes_accepted=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary);publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-FAILURE / HOF保存失敗の局所通知と非破壊待機\n- Version: dex-hof-v1\n- Status: DONE（候補限定受入。全mode/共通残callerは未完）\n- Summary: {summary}\n- Files changed: HOF ASM/generator/typed lease/isolated/UI/host/workflows、専用CP/evidence、固定MDJSONと両ログ。\n- Verify: isolated run{work.RUN}/2880case/1process、UI run{RUN}/6process15画像、原本全文・全SHA・実pixel確認。260byte/候補40ad8237、新114owner/overlap0/旧113全byte保持、22literal＋3BL/17root/未分類0、全ROM逆変換。記録ARM0/native0。\n- Diagnostics: 初回はhost executableとARM link dir衝突/native0、次はmGBA word配列をbyteとして比較し隔離case0停止/native1。どちらも保存/画面受入へ改称せず原本保持。record初回はPPMのGit取込をtext-only guardが拒否しcommit前停止。画像は既存Actions原本に保持しSHAで束縛、trackedはtextだけに限定してguard無変更。\n- Fixture: UI入口callback/state9byte以外の全RAM不変を無frameで検査。自然殿堂入り、story gate、初回mode3原子性、HOF全種族ABIの受入ではない。正式原本4copy不変。\n- Next: {goal}\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存入力。公開source/address-size-SHA/text/screensだけ。ROM断片/rawhex/runtime/入力save/runner/credentials追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'every original bound source retained');owned={STATE,DOC,CP,GUIDE,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'hof-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed record including newline')
 print('RESULT=DONE TASK=USER-20261005-DEX-HOF-FAILURE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC,success='hof-record.json',failure=None);need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated receipt only')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='hof-record.json','one receipt');b=p.read_bytes();need(0<len(b)<1500000 and b.endswith(b'\n')and b'\0'not in b,'bounded JSON');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed HOF record');globals()[sys.argv[1]]()
