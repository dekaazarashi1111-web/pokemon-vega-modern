#!/usr/bin/env python3
"""mode3 mainの限定受入と全原本を固定再開点へ記録。追加ARM/native0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_hof_main_ui as work
import pr16_dex_hof_main_cow_actions as isolated_work
need,identity,write=work.need,work.identity,work.write
BASE='5092c4848f445c6ef13a8768cce8e22bc19fb999';RUN=37266381005;JOB=111623997889
ARCHIVE=(11326468711,RUN,108832,'24ea644eef9492cbf0cd5ceee2184446d531c5e132481915a8c7164ea0550baf')
WF=work.WF;VISUAL='content/modernization/pr16_dex_hof_main_visual_review.json';CODE={WF,VISUAL,'scripts/pr16_dex_hof_main_record.py','.github/workflows/pr16-dex-hof-main-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_hof_main_checkpoint.json';GUIDE=isolated_work.GUIDE;EVIDENCE='content/modernization/pr16_dex_hof_main_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-hof-main-record';PUBLIC=ROOT/'public-dex-hof-main-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized current mode3 record');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
def source_guard():
 import pr16_learnset_runtime_record as g,pr16_dex_publication as publication
 current();publication.contract(ROOT,'.github/workflows/pr16-dex-hof-main-record.yml',PUBLIC,'pr16-dex-hof-main-record-receipts','scripts/pr16_dex_hof_main_record.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def archive(spec,label,module):
 import pr16_dex_publication as publication
 publication.consumer(t.api('actions/artifacts/'+str(spec[0])),module.ARTIFACT,spec[1]);z,_=t.archive(spec)
 with z:
  names=z.namelist();need(len(names)==len(set(names)),'unique artifact members');files={n:z.read(n)for n in names};need(all(i.external_attr>>28!=10 for i in z.infolist()),'no archived symlink')
 folder=OUT/label;folder.mkdir()
 for n,b in files.items():
  p=Path(n);need(not p.is_absolute()and'..'not in p.parts and not any(v.startswith('.')for v in p.parts)and len(p.parts)<=3,'bounded original artifact path');dest=folder/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 old=module.PUBLIC
 try:module.PUBLIC=folder;module.export()
 finally:module.PUBLIC=old
 return files,folder

def remaining_subspans(link):
 free=isolated_work.f.free_spans();used=sorted((x['address'],x['address']+x['size'])for x in link['sections']);out=[]
 for lo,hi in free:
  cursor=lo
  for a,z in used:
   if lo<=a<hi:
    need(cursor<=a<z<=hi,'new helper inside one actual donor window')
    if cursor<a:out.append(dict(address=cursor,size=a-cursor))
    cursor=z
  if cursor<hi:out.append(dict(address=cursor,size=hi-cursor))
 need(sum(x['size']for x in out)==186,'current remaining scheduler capacity is186 not366');return out

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume,pr16_dex_start_fault_ui as cold
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one new mode3 record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'every prior source retained and no prior pending run')
 for run,job,head in[(work.RUN,work.JOB,work.BASE),(RUN,JOB,BASE)]:
  r=t.api('actions/runs/'+str(run));j=t.api('actions/jobs/'+str(job));need(r['head_sha']==head and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==run and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'source run all10step success')
 iso,ifolder=archive(work.ARCHIVE,'isolated',isolated_work);ui,ufolder=archive(ARCHIVE,'ui',work);i=json.loads(iso['measurement.json']);m=json.loads(ui['measurement.json']);need('failure.json'not in iso and'failure.json'not in ui,'successful originals only')
 need(i['status']=='PASS_ISOLATED_MODE3_MAIN_COW_SOURCE_AUTHORITY'and i['isolated']['cases']==554 and i['isolated']['mode3_cases']==42 and i['isolated']['dispatch_cases']==512 and json.loads(iso['isolated-stdout.txt'])==i['isolated']and not iso['isolated-stderr.txt'],'all554 ARM conditions and complete stdout')
 need(i['candidate']==m['candidate']==dict(size=33554432,sha256='88be88116bd452bd70cffaf2a820d5c6c6b6b7410fa603a9a0228b694725d5de')and i['parent_candidate']==isolated_work.f.checkpoint()['candidate'],'exact current parent and accepted candidate')
 pl=i['placement'];need(i['link']['payload_bytes']==180 and len(i['link']['sections'])==5 and i['link']['existing_scheduler_relinks']==0 and pl['new_rom_tail_bytes']==0,'five current-gap180byte helpers with no old scheduler relink/tail expansion');need(len(pl['owner_byte_audit'])==115 and sum(r['unchanged']for r in pl['owner_byte_audit'])==114 and pl['modified_owners']==['display_npc_event_audit_stage61_payload']and pl['allocation']['summaries']['allocation_count']==115 and pl['allocation']['summaries']['overlap_count']==0 and pl['whole_rom_rollback_exact'],'whole115owner retention and inverse')
 need(m['status']=='PASS_MODE3_COW_UI_ONLY_FAILURE_SUCCESS_AND_COLD'and m['source_head']==BASE and m['native_processes']==10 and m['ram_fixture_bytes_per_ui_process']==9 and m['host_tests']==4,'five changed UI and five independent cold processes')
 need([(c['mode'],c['name'])for c in m['cases']]==[(3,'hof28-fault'),(4,'hof29-fault'),(1,'main-fault'),(2,'outer-fault'),(0,'healthy')],'all five exact outcomes')
 for case in m['cases']:
  folder=ufolder/case['name'];need(work.validate_trace((folder/'stdout.txt').read_bytes(),folder,m['candidate'],case['mode'])==case['trace']and not(folder/'stderr.txt').read_bytes(),'whole UI trace revalidated without native');cd=case['cold'];cf=ufolder/(case['name']+'-cold')/('cold-'+str(cd['counter']));rows=[json.loads(x)for x in(cf/'stdout.txt').read_bytes().splitlines()];need(not(cf/'stderr.txt').read_bytes()and rows[-1]==cd['end']and cold.screens(rows,cf)==cd['screens'],'whole cold trace and actual pixels identity');need([x for x in rows if'hof_cold_metadata'in x]==[cd['hof_metadata']]and cd['hof_metadata']['stat10']==case['physical_stat10']and cd['hof_metadata']['ledger_sha256']==cd['observation']['ledger_sha256']=='1a34e64cfee8f3793ea60b1736daa6df07d122390dcb69aacacf45cbffd0a229','all five selected counter/stat and full physical QOL ledger')
 visual=json.loads((ROOT/VISUAL).read_bytes());images={n:identity(b)for n,b in ui.items()if n.endswith('.ppm')};need(visual['run']==RUN and visual['source_head']==BASE and tuple(visual['archive'])==ARCHIVE and visual['actual_pixels_reviewed']and visual['screens']==25 and visual['images']==images,'all25 screenshots individually reviewed and bound')
 paths=set()
 for label,files in [('isolated',iso),('ui',ui)]:
  for n,b in files.items():
   if Path(n).suffix not in{'.json','.txt'}:continue
   p=EVIDENCE+'/'+label+'/'+n;need(not(ROOT/p).exists(),'new immutable text evidence');dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(p)
 summary='初回HOF mode3の主保存を既存copy-on-writeへ接続し、主保存故障時の旧authority全14sectorを保護。HOF28失敗は29/mainを書かず、29失敗もmainを書かない。stat10は生RAMで一度だけ、coldは選択mainの0/1に一致。5条件の既存HOFエラー/正常表示と各cold、全QOL2048byteを限定受入。候補88be8811、既存scheduler内5窓180byte、115owner中114全byte不変。HOFとmainの世代結合・跨領域原子性は未完。'
 with(ROOT/GUIDE).open('a')as out:out.write('\n## 候補限定受入\n\n'+summary+'\n\n隔離run'+str(work.RUN)+'は554条件（mode3変更42＋全u8 dispatch512）。新host7suiteを原本再利用しobserver影響1suiteだけ追試、UI専用4suite。UI run'+str(RUN)+'はHOF28/29/主保存/outer末尾/正常の5条件と各cold、計10process/25画面。9byte入口fixtureであり自然殿堂入りではない。次の配置はこのcheckpointのcurrent_scheduler_subownersを優先し、旧scheduler残366byteではなく実残186byteを使う。新ROM末尾の消費0。\n')
 scheduler=json.loads((ROOT/isolated_work.f.SCHED).read_bytes());current_sections=[*scheduler['link']['sections'],*i['link']['sections']]
 cp=dict(schema_version=1,status='PASS_SCOPED_MODE3_MAIN_COW_AND_HOF_FAILURE_SHORT_CIRCUIT',candidate=m['candidate'],parent_candidate=i['parent_candidate'],isolated=i,ui=m,isolated_run=work.RUN,isolated_job=work.JOB,isolated_archive=work.ARCHIVE,ui_run=RUN,ui_job=JOB,ui_archive=ARCHIVE,visual_review=visual,current_build=dict(link=i['link'],placement=pl),current_scheduler_subowners=current_sections,current_scheduler_free_subspans=remaining_subspans(i['link']),current_scheduler_free_bytes=186,old_scheduler_free366_is_historical=True,all_previous_owners=115,unchanged_previous_owners=114,new_allocations=0,new_subowner_bytes=180,accepted_raw_native_processes=11,diagnostic_native_processes=0,fixture_setup_mode0_calls=3,initial_hof_atomicity=False,hof_main_generation_binding=False,all_save_modes=False,common_failure_all_callers=False,sector31_atomicity=False,all_cold_owners_preserved=False,all_typed_consumers=False,formal_rom_changed=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0,record_arm_compiles=0,source_bindings=bindings(isolated_work.CODE|work.CODE|CODE|{GUIDE}),evidence_bindings=bindings(paths));write(ROOT/CP,cp)
 goal='正式ROM/Save101を保持。最新88be8811/115owner/current_scheduler_subownersを基準に、HOF28/29とmain保存世代の結合・跨領域原子性を次に閉じる。mode3 mainの旧authority保護とHOF失敗短絡は受入済みだが、main失敗時にHOFが先行更新される境界は未完。全mode4/5/default/LinkFull、未対応caller共通SaveFailed・stale authority wipe、早期sector31故障/単bank原子性、残typedconsumer、全cold ownerも未完。正式切替とtrainer131後半は必要検証不足で保留（承認不足ではない）。最終はシオウ通常回復/Save/独立cold Continue、雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_main_cow']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=cp['candidate'],parent_candidate=cp['parent_candidate'],owners=115,unchanged_previous_owners=114,new_subowner_bytes=180,current_scheduler_free_bytes=186,isolated_run=work.RUN,ui_run=RUN,record_run=int(os.environ['GITHUB_RUN_ID']),initial_hof_atomicity=False,formal_rom_changed=False,formal_save_changed=False)
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='CLOSE_HOF_GENERATION_AND_REMAINING_SAVE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_FALLBACK_QOL_JA.md','docs/PR16_DEX_HOF_FAILURE_JA.md','docs/PR16_DEX_OUTER_QOL_JA.md','docs/PR16_DEX_CONSUMERS_JA.md']);state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='mode3主保存authority保護とHOF失敗短絡だけの限定受入記録source。HOF/main原子性・正式切替は未完。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(isolated_work.CODE|work.CODE|CODE|paths|{CP,GUIDE}));state['do_not_repeat'].append('88be8811のmode3 main COWは隔離554条件とUI5条件＋各cold10process/25画像を原本再利用。main0の3callはsynthetic入力bank生成で通常Save再受入ではない。既存115owner中114保持、新180byteはStage61内5窓。次は実subownerを差引いた186byteを優先し、旧366byteや古いsuffixを空き扱いしない。HOF/main世代結合は未完。')
 state['observed_head_checks']=dict(scope_head=BASE,isolated_run=work.RUN,isolated_job=work.JOB,ui_run=RUN,ui_job=JOB,both_all10_steps_success=True,accepted_raw_native_processes=11,diagnostic_native_processes=0,screens=25,all_cold_owners_preserved=False,initial_hof_atomicity=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary);publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-MAIN-COW / 初回mode3主保存authority保護\n- Version: dex-hof-main-cow-v1\n- Status: DONE（候補mode3 main保護とHOF失敗短絡の限定受入）\n- Summary: {summary}\n- Files changed: mode3 ARM/generator/bindings/isolated/UI/tests/workflows、専用CP/全text evidence、固定MDJSONと両ログ。\n- Verify: 隔離run{work.RUN}/job{work.JOB}全10step、実ARM554条件（42変更故障・境界＋512dispatch）。host7suite＋影響1suite、UI4suite。UI run{RUN}/job{JOB}全10step、5UI＋各cold10process25画像を全原本/全SHA/pixelで検査。\n- Allocation: 新180byteを旧schedulerの実空き5窓へ。全115owner中114全byte保持、Stage61のみ更新、row3だけ4byte変更、overlap0、全ROM逆変換。元scheduler再link0、新ROM末尾0、実残186byte、旧366byteは履歴。\n- Native: 受入raw11（隔離1＋UI/cold10）、診断0。隔離入力bankのmode0生成3callはfixtureであり旧通常Save再受入ではない。記録host0/ARM0/native0。正式ROM06c5e85c/Save101全4copy814a8e31不変。\n- Boundary: stat10は生RAM0→1を一度、HOF失敗でrollback0/main0。主保存故障も旧14sector・cold101を保持。正常/outer末尾はcold102。QOL2048byteは5coldで物理全byte一致。HOF28/29はmainより先行するため全体原子性・世代bindingはfalse。\n- Next: {goal}\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repo Actions原本/既存入力のみ。公開source/最小address-size-SHA/text/screens、ROM断片/rawhex/ROM/runtime/入力save/runner/credential追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'all prior protected bytes retained');owned={STATE,DOC,CP,GUIDE,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'hof-main-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed record including newline')
 print('RESULT=DONE TASK=USER-20261005-DEX-HOF-MAIN-COW VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC,success='hof-main-record.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='hof-main-record.json','one regular receipt');b=p.read_bytes();need(0<len(b)<2000000 and b.endswith(b'\n')and b'\0'not in b,'bounded complete JSON');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed mode3 record');globals()[sys.argv[1]]()
