#!/usr/bin/env python3
"""保存失敗の候補限定受入と不受入原本を、native再走なしで固定する。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as t
import pr16_dex_save_failure_actions as initial
import pr16_dex_save_failure_delta as delta
import pr16_dex_save_failure_ui as ui
need,identity,write=initial.need,initial.identity,initial.write
BASE='29d97ec41b7739cd5204ba2476569bee082c9178'
ISOLATED=dict(source='2ea7577c8d4d02e88e91253dab9855bbc8d3eb3c',run=37234821383,job=111531715874,archive=(11315426394,37234821383,17512,'3f5dda8b3f7b70f1de4361ecb52efe55ce90018281e212ae19b1fbe3f508927d'),file='build.json')
UPDATED=dict(source='82912f7db7b805ffb8af04785c0ae397a8df6bbf',run=37235903199,job=111534818475,archive=(11315776017,37235903199,17586,'210866095da2dabe37cfa41fa50ba790298ca0690f8bcb0a2aaaafbefe44c0f7'),file='measurement.json')
UI=dict(source=BASE,run=37236898977,job=111537718388,archive=(11315717277,37236898977,27759,'b62a6e0c81a5713ce989ae551afb8b9aed49ddfb95b75828c029be89f805202e'),file='measurement.json')
DIAGNOSTICS=[
 dict(source='dc7141524db4a44aa6194fc402cc2ea30e3cb57c',run=37236495419,archive=(11316150777,37236495419,44466,'b8d6df9e7c02d3a6903263a593adec3299c02b416864cd3d90652a5fda9f0972'),reason='通常エラー第一頁の入力待ち改ページを画面・callbackで同定。driver待ち条件を修正。'),
 dict(source='8c4a84f285f6d30064bd9d8d3c74f21ae10e710a',run=37235253135,archive=(11314584834,37235253135,9409,'380f399807ebcfe422be7cc16ec0b494fbc996f7d4e3551628ed847376b74309'),reason='専用SaveFailed前半でMDX破壊。最初の不一致で停止。'),
 dict(source='4d55bf6856448eaebfec3bae93150f0bc8433c17',run=37235631389,archive=(11315436753,37235631389,9909,'ba3a9523f503bec3a78898a457a04745a7a2344d5e8e9a5198b5883a32df90b1'),reason='DMA store observerがMDX先頭への2byte破壊を検出。'),
 dict(source='7650f1f29de794859efd17c4ee97271c8da9ad07',run=37236225285,archive=(11316170257,37236225285,39041,'cdd0249315aa8b0ffa0d010b477efea80fe28511bb6d16d31a91a180ce2b398b'),reason='修正版ROMの専用SaveFailed回避は保持。通常エラーUI driver待ち条件の診断timeout。'),
]
GUIDE='docs/PR16_DEX_SAVE_FAILURE_JA.md';CODE={GUIDE,'scripts/pr16_dex_save_failure_record.py','.github/workflows/pr16-dex-save-failure-record.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';CP='content/modernization/pr16_dex_save_failure_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_save_failure_evidence';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-save-failure-record';PUBLIC=ROOT/'public-dex-save-failure-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return{p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized record branch')
 p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def read_success(spec):
 r=t.api('actions/runs/'+str(spec['run']));j=t.api('actions/jobs/'+str(spec['job']));need(r['head_sha']==spec['source']and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact successful run')
 need(j['run_id']==spec['run']and j['conclusion']=='success'and len(j['steps'])==10 and all(s['conclusion']=='success'for s in j['steps']),'all10 native workflow steps success')
 z,_=t.archive(spec['archive'])
 with z:files={n:z.read(n)for n in z.namelist()}
 need(spec['file']in files and 'failure.json'not in files,'complete accepted measurement')
 report=json.loads(files[spec['file']]);need(report['source_head']==spec['source']and report['run_id']==spec['run'],'exact measurement source/run')
 for path,b in report['source_bindings'].items():need(identity(git('show',spec['source']+':'+path))==b,'original source full bytes')
 return files,report

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable failure record');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected,'prior accepted sources exact')
 need(state['pending_runs']==[dict(run_id=37234348310,tested_head='51506e34ea552cd55a52ac311b92f47218f008fd',status='in_progress')],'only completed battle record pending')
 old=t.api('actions/jobs/111530381334');need(old['run_id']==37234348310 and old['conclusion']=='success'and len(old['steps'])==12 and all(s['conclusion']=='success'for s in old['steps']),'battle record12steps terminal')
 z,_=t.archive((11315196473,37234348310,18170,'e4b4a476af39b2ba319017092b3db5c660112b4166780bd9b9b57888ca5f5129'))
 with z:need(z.read('battle-record.json')==(ROOT/initial.f.CP).read_bytes(),'battle receipt equals committed checkpoint all bytes')
 originals={};reports={}
 for label,spec in [('isolated-original',ISOLATED),('updated-gates',UPDATED),('ordinary-error-ui',UI)]:originals[label],reports[label]=read_success(spec)
 first,new,screen=reports.values();need(json.loads(originals['ordinary-error-ui']['runtime-identity.json'])==new['runtime'],'same exact package and library hash for ARM and UI');need(first['native']['cases']==152 and new['native']['cases']==108 and new['native']['new_result_gate_cases']==48 and new['native']['old152_cases_rerun']==0,'exact isolated case accounting')
 need(new['link']['base']==0x095FFEF0 and new['link']['payload']['size']==160 and new['placement']['all110_old_owners_byte_identical']and new['placement']['allocation']['summaries']['allocation_count']==111 and new['placement']['allocation']['summaries']['overlap_count']==0,'new gate allocator and previous owners unchanged')
 need(screen['candidate']==new['candidate']and screen['source_save']==screen['output_save']==t.SEED and screen['native_processes']==1 and screen['save_attempts']==1 and screen['save_commits']==0 and screen['authority_present']and not screen['authorityless_real_ui_accepted'],'bounded real negative UI and full original SaveRTC')
 folder=OUT/'ui';folder.mkdir()
 for name,raw in originals['ordinary-error-ui'].items():
  need(Path(name).name==name,'simple UI member');(folder/name).write_bytes(raw)
 need(ui.validate((folder/'stdout.txt').read_bytes(),folder,new['candidate']['sha256'])==screen['trace'],'independent current strict transcript and screen replay without native')
 need(screen['trace']['end']['destructive_save_failed_entered']is False and len(screen['trace']['screens'])==4,'unsafe screen never entered, normal error two pages and field verified')
 rejected=[]
 for spec in DIAGNOSTICS:
  r=t.api('actions/runs/'+str(spec['run']));need(r['status']=='completed'and r['conclusion']=='failure'and r['head_sha']==spec['source'],'original diagnostic failure retained')
  z,_=t.archive(spec['archive'])
  with z:files={n:z.read(n)for n in z.namelist()}
  fail=json.loads(files['failure.json']);need(fail['status']=='DIAGNOSTIC_NOT_ACCEPTED'and fail['native_processes']==1,'exact diagnostic original');originals['diagnostic-'+str(spec['run'])]=files
  rejected.append(dict(**spec,failure=fail,candidate_accepted=False))
 dma=[json.loads(x)for x in originals['diagnostic-37235631389']['stdout.txt'].splitlines()if b'mdx_native_writer'in x];need(len(dma)==1 and dma[0]['dma']==7 and dma[0]['destination']==0x0203DB40 and dma[0]['width']==2 and dma[0]['state']==2 and dma[0]['writer_pc_proven']is False,'DMA clobber original, CPU PC attribution not overclaimed')
 page=originals['diagnostic-37236495419'];page_rows=[json.loads(x)for x in page['stdout.txt'].splitlines()];page_stages=[r for r in page_rows if 'failure_ui_stage'in r]
 need(page_rows[0]['candidate_sha256']==new['candidate']['sha256']and page_stages[-1]['callback']==0x0806F1F5 and page_stages[-1]['attempt']==255 and page_stages[-1]['active']==0 and page_stages[-1]['counter']==101,'same-candidate stable first-page diagnostic state')
 need(identity(page['screen-0001.ppm'])['sha256']=='980d52f89730c01ef202a722bb4a9c7ab3713b47090da18ff20d9828f2d50937','whole retained first-page visual original')
 visual=dict(first_page_run=37236495419,first_page_artifact=11316150777,first_page_image='screen-0001.ppm',first_page_sha256='980d52f89730c01ef202a722bb4a9c7ab3713b47090da18ff20d9828f2d50937',final_page_run=UI['run'],final_page_image='screen-0002.ppm',field_image='screen-0003.ppm',manual_review_ja='同候補の第一頁は先行診断原本で「レポートがかけませんでした」を目視。成功runの最終頁とfieldも目視。成功runのframe1923画像はtext更新前だったため第一頁の文面証拠に使わず、同候補/同callback/attempt255の既存原本を再利用。追加native0。',extra_native_processes=0)
 evidence=ROOT/EVIDENCE;evidence.mkdir()
 for label,files in originals.items():
  for name,raw in files.items():
   need(Path(name).name==name,'simple evidence name')
   if Path(name).suffix not in{'.json','.txt'}:continue
   dest=evidence/label/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 evidence_paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
 code=CODE|initial.CODE|delta.CODE|ui.CODE
 cp=dict(schema_version=1,status='PASS_CANDIDATE_INVALID_LIVE_NONDESTRUCTIVE_SAVE_ERROR',candidate=new['candidate'],isolated_original=dict(spec=ISOLATED,measurement=first),updated_gates=dict(spec=UPDATED,measurement=new),ordinary_error_ui=dict(spec=UI,measurement=screen),diagnostics=rejected,visual_review=visual,dma_owner_collision=dma[0],source_bindings=bindings(code),evidence_bindings=bindings(evidence_paths),invalid_live_save_error_accepted=True,authorityless_real_ui_accepted=False,valid_live_save_failed_owner_collision_unresolved=True,valid_wipe_success_retry_accepted=False,all_consumers_wired=False,all_save_modes_accepted=False,formal_rom_changed=False,formal_save_changed=False,formal_save=101,record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0)
 write(ROOT/CP,cp)
 goal=('正式ROM/Save101は保持。候補d3dcb55aではbattle seen5窓/公式count、invalid-live保存拒否の非破壊通常エラーUIを限定受入。元110ownerとscheduler/codec保持。'
 '次はvalid-liveの実保存失敗で旧SaveFailedのtiles16KiB＋video-stateが拡張ownerを破壊する経路を安全化し、HOF/overwrite/default等全save mode固有副作用/実retry/cold fallbackを区別して受入する。'
 '続いてactive capture/SetMonPokedexFlags、native授受/孵化/進化、UI/native count、acquisition/research/reward、reward clear、Factory memorial/Codex rollback、DexNavの残consumerをSID喪失前に接続する。'
 'authorityなし隔離writer拒否と、authorityありCRC1byte fixtureの実UIを混同しない。全consumerと必要な影響native前に正式ROM切替やtrainer131後半へ進めない。最終はシオウPokecenter通常回復/Save/coldContinue、雑魚毎のSaveなし。')
 state['story_dex_owner']['runtime_integration']['save_failure']=dict(checkpoint=CP,guide=GUIDE,status=cp['status'],candidate=cp['candidate'],updated_run=UPDATED['run'],ui_run=UI['run'],record_run=int(os.environ['GITHUB_RUN_ID']),all_save_modes_accepted=False,valid_live_owner_collision_unresolved=True,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['battle_consumers']['recording']=dict(run=37234348310,job=111530381334,all12_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['bp']['current_stop']='正式ROM/Save101保持。battle seen/公式countとinvalid-liveの非破壊通常エラーを候補限定受入。valid保存失敗owner衝突、全mode、残consumerは未完。';state['bp']['next_step']=goal
 state['next_action'].update(id='CLOSE_VALID_SAVE_FAILURE_OWNERS_AND_REMAINING_DEX_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_BATTLE_CONSUMERS_JA.md','docs/PR16_DEX_CONSUMERS_JA.md'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='candidate-only invalid-live非破壊保存エラーとconsumer部分接続の記録source。正式ROM/Save101不変。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(code|evidence_paths|{CP}));state['do_not_repeat'].append(f'保存失敗: old152case run37234821383、新gate48＋追加oracle60 run{UPDATED["run"]}、実通常エラーUI run{UI["run"]}の原本を使用。候補/源不変でnative再走しない。DMA破壊とUI driver診断failureを保持。valid-live専用SaveFailedのowner衝突/全mode/全consumerへ受入拡張禁止。')
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-SAVE-FAILURE / invalid-live非破壊保存エラー\n- Version: dex-save-failure-v2\n- Status: DONE（invalid-live限定。valid失敗/全mode/残consumerは未完）\n- Summary: stockの返値255→mask0誤成功とQOL sector31後処理を遮断。invalid-liveでは衝突する専用SaveFailedへ入らず通常エラー第一頁→改ページA→最終頁→復帰A→fieldへ返す。TryWipeもinvalidを非破壊拒否。新160byte/111owner、元110owner全byte保持。\n- Files changed: failure gate/source/署名窓/native/negative UI、guide/CP/evidence、固定MDJSON、両ログ。\n- Verify: isolated152case原本、変更gate48＋追加oracle60=108case/1656480instructions、actual error UI run{UI["run"]}、CRC1byte例外/7barrier/4画面/改ページAと復帰A/MDX522不変/保存commit0/FlashRTC131088全byte不変。全3受入workflow10step成功。記録native0。\n- Correction: SaveFailedの16KiB tiles DMAがMDX/QOL/CFRU owner、video-stateがResearchへ重なる。run37235631389でDMA7/2byte/MDX先頭を検出、rawPCをDMA要求元にしない。失敗原本とUI driver timeoutを保持。\n- Boundary: 実UIはSave101 authorityありの明示CRC fixture。authorityなしは隔離全writer/mode拒否だけ。valid wipe成功retry、valid-live専用画面owner衝突、HOF/overwrite固有副作用、全consumer/正式進行は未受入。正式ROM/Save101不変。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存入力/固定一次source/公式Ubuntu compiler。公開はsource/address-size-SHA/text/screensのみ、ROM/入力save/runtime/runner/credential非公開。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 need(bindings(protected)==protected,'all previous accepted sources retained')
 owned={STATE,DOC,CP,*LOGS}|evidence_paths;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'save-failure-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed readback')
 print('RESULT=DONE TASK=USER-20261004-DEX-SAVE-FAILURE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated receipt directory')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name=='save-failure-record.json','one explicit receipt');r=p.read_bytes();need(0<len(r)<500000 and r.endswith(b'\n')and b'\0'not in r,'bounded complete JSON');json.loads(r)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'closed action');globals()[sys.argv[1]]()
