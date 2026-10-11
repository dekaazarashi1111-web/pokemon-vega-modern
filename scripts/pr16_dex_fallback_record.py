#!/usr/bin/env python3
"""限定idle fallback受入を原本全文から固定正本へ記録。追加native/ARM0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_fallback_cold as work
import pr16_dex_fallback_qol_actions as isolated_work
need,identity,write=work.need,work.identity,work.write
BASE='8b11cbc5575954c445d8599d60a857bb797f815c'
RUN=37261066891;JOB=111608210701;ARCHIVE=(11324487407,RUN,17437,'9d51cfca557286da23687b37764285591fecc453c69db9fbb6ba6d2f3af9e110')
WF=work.WF;VISUAL='content/modernization/pr16_dex_fallback_visual_review.json'
CODE={WF,VISUAL,'scripts/pr16_dex_fallback_record.py','.github/workflows/pr16-dex-fallback-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_fallback_checkpoint.json';GUIDE=isolated_work.GUIDE;EVIDENCE='content/modernization/pr16_dex_fallback_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-fallback-record';PUBLIC=ROOT/'public-dex-fallback-record'
DIAGNOSTICS=[(11323735857,37257779364,482,'5b79ce7faa12cb7c7d481dbb64a1c2ee388d134af87be8494c0dec08c3fe43da'),(11323448524,37259333246,14254,'2bf44c77c4c0a14d885ef2f931d9aa4787d3a1780270289d4641346ce229a42a')]
BOOT_ONLY=(11323469046,37259756434,21217,'483f4a0c370e231a30fbd80da188f34b0a405b0d2021a4611f5a5b345538d416')
TITLE_ONLY=(11324495487,37260278584,24815,'7c885d73d9f940d1c2b775b9a3d4b7c9fcdff1a85e3dcfc59e896ae105be4365')
MENU_DIAGNOSTIC=(11323504728,37260564499,15235,'2d1c8e996ba288065477173baeb6e97b58e83fc8ca77a3bd55a138281bf17b0d')
COMPACT=(11323204071,37258072804,1271,'a4b23b7a023244b6893a6158a8d390df985952dc6e0b5814eeeda938feaa8319')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized fallback record');p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft')
def source_guard():
 import pr16_learnset_runtime_record as g,pr16_dex_publication as publication
 current();publication.contract(ROOT,'.github/workflows/pr16-dex-fallback-record.yml',PUBLIC,'pr16-dex-fallback-record-receipts','scripts/pr16_dex_fallback_record.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def archive(spec,label,module):
 import pr16_dex_publication as publication
 publication.consumer(t.api('actions/artifacts/'+str(spec[0])),module.ARTIFACT,spec[1]);z,_=t.archive(spec)
 with z:files={n:z.read(n)for n in z.namelist()}
 folder=OUT/label;folder.mkdir()
 for n,b in files.items():
  p=Path(n);need(not p.is_absolute()and'..'not in p.parts and len(p.parts)<=2,'bounded original path');dest=folder/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 old=module.PUBLIC
 try:module.PUBLIC=folder;module.export()
 finally:module.PUBLIC=old
 return files,folder

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one new fallback record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'all prior accepted sources and terminal state')
 for run,job,head in[(work.RUN,work.JOB,work.BASE),(RUN,JOB,BASE)]:
  r=t.api('actions/runs/'+str(run));j=t.api('actions/jobs/'+str(job));need(r['head_sha']==head and r['status']=='completed'and r['conclusion']=='success'and j['run_id']==run and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'all source-run10 steps success')
 iso,ifolder=archive(work.ARCHIVE,'isolated',isolated_work);cold,cfolder=archive(ARCHIVE,'cold',work);i=json.loads(iso['measurement.json']);m=json.loads(cold['measurement.json']);need('failure.json'not in iso and'failure.json'not in cold,'successful originals complete')
 need(i['status']=='PASS_ISOLATED_FALLBACK_IDLE_QOL_LEDGER'and i['isolated']['cases']==508 and i['host_cases']==327907 and i['native_processes']==1 and json.loads(iso['isolated-stdout.txt'])==i['isolated']and not iso['isolated-stderr.txt'],'all scoped isolated raw evidence exact')
 need(i['candidate']==m['candidate']==dict(size=33554432,sha256='d773a1232c31fcb5629785278c2ad6e6d46208dbc62a55d66167fba7a2a38670')and i['parent_candidate']==dict(size=33554432,sha256='40ad82373b1e0f49283f59dce1e68a009b3e548d8f3ff080b72a134a228b0ac2')and i['link']['payload']['size']==296,'latest HOF lineage and exact candidate')
 pl=i['placement'];need(len(pl['owner_byte_audit'])==114 and sum(r['unchanged']for r in pl['owner_byte_audit'])==113 and pl['modified_owners']==['mirage_production_stage38_payload']and pl['allocation']['summaries']['allocation_count']==115 and pl['allocation']['summaries']['overlap_count']==0 and pl['whole_rom_rollback_exact'],'all114 old owners inherited:113 unchanged,one4byte pointer;new115 total')
 need(sorted(p['size']for p in pl['patches'])==[4,296]and pl['tail_reference_audit']['literal_candidates']==30 and pl['tail_reference_audit']['thumb_bl_candidates']==2 and pl['tail_reference_audit']['root_count']==26 and pl['tail_reference_audit']['unclassified_candidates']==0,'closed two patches and all typed references')
 need(m['status']=='PASS_FALLBACK_IDLE_LEDGER_COLD_AND_INVALID_BLOCK'and m['source_head']==BASE and m['native_processes']==1 and m['reused_native_processes']==2 and m['prior_diagnostic_native_processes']==1 and m['old_native_reruns']==0,'two positive originals retained and only unfinished negative rerun')
 z,_=t.archive(t.SAVE101)
 with z:seed=z.read('story-fast.srm')
 need(identity(seed)==t.SEED==m['formal_seed']and identity(seed[0x1F064:0x1F864])==m['physical_ledger']==dict(size=2048,sha256='1a34e64cfee8f3793ea60b1736daa6df07d122390dcb69aacacf45cbffd0a229'),'formal physical durable ledger binding')
 need([c['name']for c in m['cases']]==['healthy','fallback','corrupt-ledger'],'three exact cold cases');recovered,rfolder=archive(work.RECOVER_ARCHIVE,'cold-first',work)
 for case in m['cases']:
  name=case['name'];data,declared=work.fixture(seed,name);folder=cfolder/name;need(declared==case['fixture']and case['save']==case['output']==identity(data),'exact private copy metadata and unchanged output assertion')
  need(work.trace((folder/'stdout.txt').read_text(),folder,m['candidate'],data,int(name=='corrupt-ledger'))==case['trace']and not(folder/'stderr.txt').read_bytes(),'complete whole cold trace revalidated')
  if name!='corrupt-ledger':
   need(case['reused_raw']and case['source_run']==work.RECOVER_RUN,'earlier complete positive source kept')
   for p in('stdout.txt','stderr.txt','screen-0000.ppm'):need(cold[name+'/'+p]==recovered[name+'/'+p],'positive original complete bytes retained, no native rerun')
  else:need(not case['reused_raw']and case['source_run']==RUN,'only changed negative observer run')
 need([c['trace']['metadata']['status']for c in m['cases']]==[1,255,2]and [c['trace']['metadata']['counter']for c in m['cases']]==[101,101,101],'successful fallback255 and rejected selected101/global2 remain distinct')
 need(m['cases'][0]['trace']['metadata']['ledger_sha256']==m['cases'][1]['trace']['metadata']['ledger_sha256']==m['physical_ledger']['sha256'],'full2048 durable ledger restored in both valid cold cases')
 visual=json.loads((ROOT/VISUAL).read_bytes());images={n:identity(b)for n,b in cold.items()if n.endswith('.ppm')};need(visual['negative_ui']==dict(kind='SAVE_DATA_MISSING_MESSAGE',callback2=134266037,frame=2584,start_presses=2,A_presses=0,counter=101,status=2,field=False),'exact rejected save message, never intro/title-only');need(visual['run']==RUN and visual['source_head']==BASE and tuple(visual['archive'])==ARCHIVE and visual['actual_pixels_reviewed']and visual['screens']==3 and visual['images']==images,'all three actual pixels and complete image SHA')
 boot,bfolder=archive(BOOT_ONLY,'boot-only',work);boot_report=json.loads(boot['measurement.json']);need(boot_report['native_processes']==1 and boot_report['cases'][-1]['trace']['metadata']['frame']==780 and boot_report['cases'][-1]['trace']['metadata']['status']==2,'earlier successful internal rejection was only intro-frame evidence')
 title,tfolder=archive(TITLE_ONLY,'title-only',work);title_report=json.loads(title['measurement.json']);need(title_report['native_processes']==1 and title_report['cases'][-1]['trace']['metadata']['frame']==1982 and title_report['cases'][-1]['trace']['metadata']['status']==2,'title-only intermediate remains distinct from error menu')
 menu,mfolder=archive(MENU_DIAGNOSTIC,'menu-parser-diagnostic',work);menu_failure=json.loads(menu['failure.json']);need(menu_failure['native_processes']==1 and menu_failure['message']=='full coherent cold metadata'and json.loads(menu['corrupt-ledger/stdout.txt'].splitlines()[-1])['end']=='PASS_FALLBACK_QOL_COLD','menu raw succeeded but strict parser stopped before after-close file assertion')
 paths=set();diagnostics=[]
 for label,files in [('isolated',iso),('cold',cold),('cold-first-diagnostic',recovered),('boot-only',boot),('title-only',title),('menu-parser-diagnostic',menu)]:
  for n,b in files.items():
   if Path(n).suffix not in{'.json','.txt'}:continue
   p=EVIDENCE+'/'+label+'/'+n;need(not(ROOT/p).exists(),'immutable new evidence');dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(p)
 for spec,label in[(DIAGNOSTICS[0],'compile-first'),(COMPACT,'compile-compact')]:
  files,folder=archive(spec,label,isolated_work)
  for n,b in files.items():
   p=EVIDENCE+'/'+label+'/'+n;dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);paths.add(p)
  diagnostics.append(dict(run=spec[1],archive=spec,report=json.loads(files['failure.json']if'failure.json'in files else files['measurement.json'])))
 need(diagnostics[0]['report']['native_processes']==0 and diagnostics[1]['report']['status']=='COMPILED_FALLBACK_NOT_PLACED_NOT_ACCEPTED'and diagnostics[1]['report']['link']['payload']['size']==300,'capacity rejection and300byte compile-only are not acceptance')
 summary='選択済み片bank fallback255でQOL台帳が全zeroとなる不具合を、v2/idle durable2048byteの非破壊復元で修正。正常cold1と故障コピーcold255が物理1a34…の全byteへ一致し、同地点・party・Bag、追加Save0。破損台帳はglobal2/MDX無効でfield遮断し、エラーUI到達後も選択counter101を保持（intro/title中間のcounter0と区別）。候補d773a123、296byte、新115owner、旧114中113全byte保持＋Mirage参照4byteのみ。全cold owner・世代結合/sector31原子性は未完。'
 guide_text=(ROOT/GUIDE).read_text();old_stage='現時点は新host契約とARM容量のcompile-only段階。配置、native、cold復元は未受入。';need(guide_text.count(old_stage)==1,'one historical initial-stage paragraph');(ROOT/GUIDE).write_text(guide_text.replace(old_stage,'当初は新host契約とARM容量のcompile-only段階で、配置、native、cold復元は未受入だった。現在の限定受入は末尾を参照。'))
 with(ROOT/GUIDE).open('a')as out:out.write('\n## 候補限定受入\n\n'+summary+'\n\n隔離run'+str(work.RUN)+'は508条件/1process、host327907条件。cold初回run'+str(work.RECOVER_RUN)+'の成功2processは全trace/pixel原本を保持し、破損エラー画面にfield inventory observerを適用した1processだけ診断。中間run37259756434/37260278584はintro/title中の内部拒否だけを確認し、後継run'+str(RUN)+'はStart後の画面まで1processだけを追加。自然HOF/実Flash故障生成の再走はしていない。\n')
 cp=dict(schema_version=1,status='PASS_SCOPED_IDLE_FALLBACK_QOL_COLD',candidate=m['candidate'],parent_candidate=i['parent_candidate'],isolated=i,cold=m,isolated_run=work.RUN,isolated_job=work.JOB,isolated_archive=work.ARCHIVE,cold_run=RUN,cold_job=JOB,cold_archive=ARCHIVE,diagnostics=diagnostics,intermediate_ui=[dict(run=BOOT_ONLY[1],archive=BOOT_ONLY,status='INTERNAL_REJECTION_DURING_INTRO_NOT_FINAL_UI',native_processes=1),dict(run=TITLE_ONLY[1],archive=TITLE_ONLY,status='TITLE_ONLY_NOT_ERROR_MENU',native_processes=1)],menu_parser_diagnostic=dict(run=MENU_DIAGNOSTIC[1],archive=MENU_DIAGNOSTIC,failure=menu_failure,scope='raw menu complete; after-close file check was not reached'),cold_first_diagnostic=dict(run=work.RECOVER_RUN,archive=work.RECOVER_ARCHIVE,failure=json.loads(recovered['failure.json']),completed_positive_cases_reused=2),visual_review=visual,current_build=dict(link=i['link'],placement=pl),all_previous_owners=114,unchanged_previous_owners=113,modified_existing_owner_4byte='mirage_production_stage38_payload',all_cold_owners_preserved=False,sector31_generation_binding=False,sector31_atomicity=False,initial_hof_atomicity=False,all_save_modes=False,common_failure_all_callers=False,all_typed_consumers=False,formal_rom_changed=False,formal_save_changed=False,accepted_raw_native_processes=4,diagnostic_native_processes=2,intermediate_boot_title_native_processes=2,total_native_processes=8,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0,record_arm_compiles=0,source_bindings=bindings(isolated_work.CODE|work.CODE|CODE|{GUIDE}),evidence_bindings=bindings(paths));write(ROOT/CP,cp)
 goal='正式ROM/Save101を保持。最新d773a123/115ownerを基準に、初回mode3のHOF sector28/29とmain保存世代の整合を次に実装・検証する。全mode4/5/default/LinkFull、未対応caller共通SaveFailedとstale authority wipe、早期sector31故障/単bank原子性、残typedconsumerは未完。fallback255はQOL v2 idle台帳のみ限定復元で、Collection/Codex/Circus等の全cold owner復元と世代結合を受入していない。正式切替とtrainer131後半は検証未完で保留（承認不足ではない）。最終はシオウ通常回復/Save/独立cold Continue、雑魚ごとのSaveなし。'
 state['story_dex_owner']['runtime_integration']['fallback_qol']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=m['candidate'],parent_candidate=i['parent_candidate'],owners=115,previous_owners=114,unchanged_previous_owners=113,isolated_run=work.RUN,cold_run=RUN,record_run=int(os.environ['GITHUB_RUN_ID']),all_cold_owners_preserved=False,formal_rom_changed=False,formal_save_changed=False)
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='CLOSE_INITIAL_HOF_AND_REMAINING_SAVE_CONTRACTS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_HOF_FAILURE_JA.md','docs/PR16_DEX_OUTER_QOL_JA.md','docs/PR16_DEX_CONSUMERS_JA.md']);state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='idle fallback QOLのみの限定受入記録source。正式ROM/Save101は不変。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(isolated_work.CODE|work.CODE|CODE|paths|{CP,GUIDE}));state['do_not_repeat'].append('d773a123のfallback QOLはhost327907/ARM508と正常・片bank故障・破損cold計3成功caseで限定受入。初回coldの成功2原本を再利用し観測器だけの陰性1を修正。変更影響なしに再走せず、全cold owner/初回HOF原子性へ拡大しない。')
 state['observed_head_checks']=dict(scope_head=BASE,isolated_run=work.RUN,isolated_job=work.JOB,cold_run=RUN,cold_job=JOB,both_all10_steps_success=True,accepted_raw_native_processes=4,diagnostic_native_processes=2,intermediate_boot_title_native_processes=2,total_native_processes=8,fixture_physical_copy_bytes=[0,1,2],screens=3,all_cold_owners_preserved=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary);publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-FALLBACK-QOL / 選択済みfallbackのidle台帳復元\n- Version: dex-fallback-qol-v1\n- Status: DONE（idle QOL台帳の候補限定受入）\n- Summary: {summary}\n- Files changed: fallback C契約/ARM/generator/typed lease/isolated/cold/tests/workflows、専用CP/evidence、固定MDJSONと両ログ。\n- Verify: host327907条件、実ARM508条件/1process/run{work.RUN}、正常/片bank故障/破損cold3caseの原本全文と3pixel全SHA。新296byte、旧114ownerを全部継承して113全byte不変/1owner参照4byteのみ、新115owner/overlap0/全ROM逆変換。30literal＋2BL/26root/未分類0。\n- Native: 受入raw4（隔離1＋cold3）、診断2（field用Bag観測の不適合、collectorの旧counter0期待）＋intro/title中の内部拒否のみの中間2、総8。初回C容量guardは配置前/native0、300byteはcompile-only。再記録ARM0/native0。正常2coldは原本再利用し再走0。\n- Fixture: 正式Save101の作業コピーだけに旧bank署名1byte、不正台帳試験はさらにCRC1byte。作業コピーの選択bank101全byte（party/保存MDXを含む）は不変。RAMfixture0/register0/7barrier、FlashRTC/ROM不変、追加Save0。正式原本4copy不変。\n- Boundary: 255は1へ変えない。列挙済みの未完journalは入口で拒否。v1/empty/CRC不正はInitNewせずglobal2/MDX無効化。破損終端も選択counter101だがエラーUI/global2/field不可。intro/title中間counter0と混同しない。QOL世代はmain世代と非結合、全cold owner/early31/HOF原子性/全mode未完。\n- Next: {goal}\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repo Actions/既存入力だけ。公開source/address-size-SHA/text/screens、ROM断片/rawhex/ROM/runtime/入力save/runner/credentials追加公開0。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'every old protected source preserved');owned={STATE,DOC,CP,GUIDE,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'fallback-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed record including newline')
 print('RESULT=DONE TASK=USER-20261005-DEX-FALLBACK-QOL VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 import pr16_dex_publication as publication
 publication.output(PUBLIC,success='fallback-record.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='fallback-record.json','one receipt');b=p.read_bytes();need(0<len(b)<1500000 and b.endswith(b'\n')and b'\0'not in b,'bounded complete JSON');json.loads(b)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed fallback record');globals()[sys.argv[1]]()
