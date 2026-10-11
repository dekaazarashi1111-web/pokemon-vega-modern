#!/usr/bin/env python3
"""隔離ARMと通常ゲームの完了原本だけを記録。再compile/native再走無し。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
import pr16_dex_lifecycle_actions as isolated
import pr16_dex_gameplay_actions as gameplay
import pr16_dex_visual_probe as visual
need,identity,write=isolated.need,isolated.identity,isolated.write
BASE='310f7bbd3e1aed518bc9c10d373874e34864d964';SOURCE='d7052a19a0c2991c48de3826278dc9a5c665da5f'
RUN=37231996230;JOB=111523526200;ARCHIVE=(11313698590,RUN,41838,'1a6cb98a5d90431aa1355f27682b4b58974a174f82b83be6d7e7705c79987283')
ISOLATED_SOURCE='60fdfd27d08db121387becfd615a594d7a75729b';ISOLATED_RUN=37230810454;ISOLATED_JOB=111519848850
ISOLATED_ARCHIVE=(11313494497,ISOLATED_RUN,17359,'1c8c7a615a613c2887f2054d66d0c9f6a1ba2546fb9ae12e22abc8174c067944')
CP='content/modernization/pr16_dex_lifecycle_checkpoint.json';GUIDE='docs/PR16_DEX_LIFECYCLE_JA.md';EVIDENCE='content/modernization/pr16_dex_lifecycle_evidence'
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md';LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_dex_lifecycle_record.py','.github/workflows/pr16-dex-lifecycle-record.yml',GUIDE}
VISUAL=(11314431596,37232287450,14560,'ffc2f108a07ee6b4d69852cd82ba1e23e590bea052569c4cda37dfdd26f238c4')
OUT=ROOT/'.local/pr16-dex-lifecycle-record';PUBLIC=ROOT/'public-dex-lifecycle-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized record branch')
 pr=transport.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def terminal(run,source,job):
 r=transport.api('actions/runs/'+str(run));j=transport.api('actions/jobs/'+str(job))
 need(r['head_sha']==source and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'exact terminal successful run')
 need(j['run_id']==run and j['conclusion']=='success'and len(j['steps'])==10 and all(x['conclusion']=='success'for x in j['steps']),'all10 steps success')
def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not(ROOT/CP).exists(),'one immutable record');OUT.mkdir(parents=True);PUBLIC.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(bindings(protected)==protected and state['pending_runs']==[],'previous sources exact and records terminal')
 terminal(ISOLATED_RUN,ISOLATED_SOURCE,ISOLATED_JOB);terminal(RUN,SOURCE,JOB)
 iz,_=transport.archive(ISOLATED_ARCHIVE)
 with iz:
  need(set(iz.namelist())=={'build.json','native.json','native-attempt.json','host-tests.txt'},'isolated original member set');original={n:iz.read(n)for n in iz.namelist()}
 ir=json.loads(original['build.json']);need(ir['native']['cases']==52 and ir['native']['calls']==52 and ir['native']['steps']==756378 and ir['native']['ordinary_game_boots']==0,'isolated accounting')
 need(ir['link']['payload']['size']==188 and ir['placement']['allocation']['summaries']['allocation_count']==109 and ir['placement']['allocation']['summaries']['overlap_count']==0,'bounded actual placement')
 z,_=transport.archive(ARCHIVE)
 with z:
  need('measurement.json'in z.namelist()and 'failure.json'not in z.namelist(),'complete game original without failure');measured={n:z.read(n)for n in z.namelist()}
 report=json.loads(measured['measurement.json']);need(report['status']=='PASS_CANDIDATE_ORDINARY_DEX_SAVE_CONTINUE_NEWGAME'and report['source_head']==SOURCE and report['run_id']==RUN and report['candidate']==ir['candidate'],'exact ordinary measurement')
 need(report['native_processes']==1 and report['reused_native_processes']==3 and report['accepted_native_processes']==4 and report['ordinary_saves']==2 and report['newgame_introductions']==1 and report['all_consumers_wired']is False and report['formal_save_changed']is False,'bounded game acceptance')
 # 完走済み3processは失敗run内の原本から引き継ぐ。run全体のfailureは保持。
 for spec,source,job,cases in ((gameplay.REUSE,gameplay.REUSE_SOURCE,111521087457,['save101-save','save101-cold']),(gameplay.NEWGAME,gameplay.NEWGAME_SOURCE,111522290907,['newgame-save'])):
  prior=transport.api('actions/runs/'+str(spec[1]));need(prior['head_sha']==source and prior['status']=='completed'and prior['conclusion']=='failure','original diagnostic run remains failure')
  pj=transport.api('actions/jobs/'+str(job));need(pj['run_id']==spec[1]and pj['conclusion']=='failure','original diagnostic job')
  rz,_=transport.archive(spec)
  with rz:
   for n in rz.namelist():
    if any(n.startswith(case+'/')for case in cases):need(measured[n]==rz.read(n),'reused native full original bytes '+n)
 for src,paths in ((ISOLATED_SOURCE,ir['source_bindings']),(SOURCE,report['source_bindings'])):
  for path,b in paths.items():need(identity((ROOT/path).read_bytes())==b and identity(git('show',src+':'+path))==b,'measured source exact '+path)
 screens_reviewed=[]
 for name,row in report['cases'].items():
  need(row['fresh_processes']==2 and row['ordinary_saves']==1 and len(row['processes'])==2,'one Save independent cold each')
  output=measured[name+'-candidate-only.srm'];need(identity(output)==row['processes'][0]['output']==row['processes'][1]['input']==row['processes'][1]['output'],'all saved/continued bytes exact')
  physical=gameplay.game.physical(output,row['counter_after']);need(identity(physical['mdx'])['sha256']==row['processes'][1]['trace']['mdx'][0]['live_sha256'],'physical MDX same bank proof')
  for process in row['processes']:
   case=process['case'];text=measured[case+'/stdout.txt'];need(not measured[case+'/stderr.txt'],'clean process original')
   rows=[json.loads(v)for v in text.splitlines()];need(rows[-1]==process['trace']['end'],'native end original exact')
   for screen in process['trace']['screens']:
    image=measured[case+'/screen-'+str(screen['screen']).zfill(4)+'.ppm'];need(identity(image)['sha256']==screen['sha256'],'whole actual screenshot original')
    pixels=image[15:];colors=len(set(pixels[i:i+3]for i in range(0,len(pixels),3)));nonblack=sum(pixels[i:i+3]!=b'\0\0\0'for i in range(0,len(pixels),3))
    need(colors>1 and nonblack>1000,'nonblank actual original screen');screens_reviewed.append(dict(case=case,index=screen['screen'],sha256=screen['sha256'],colors=colors,nonblack_pixels=nonblack))
 terminal(VISUAL[1],BASE,111524369801)
 vz,_=transport.archive(VISUAL)
 with vz:visual_files={n:vz.read(n)for n in vz.namelist()}
 vr=json.loads(visual_files['measurement.json']);need(vr['native_processes']==1 and vr['ordinary_saves']==0 and len(vr['display'])==4 and all(d['nonblack_pixels']==19108 for d in vr['display']),'extra read-only visual result')
 for i in range(4):need(identity(visual_files['screen-'+str(i).zfill(4)+'.ppm'])['sha256']=='c735c4070e9cf842661e600b45924f4f58ae3409d28ba8418db7986741d0ded6','whole normal house screen same as original')
 e=ROOT/EVIDENCE;e.mkdir()
 for folder,files in (('isolated',original),('gameplay',measured),('visual',visual_files)):
  for name,raw in files.items():
   if Path(name).suffix not in{'.json','.txt'}:continue
   dest=e/folder/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 write(e/'visual-review.json',dict(status='PASS_ORIGINAL_NONBLANK_AND_MANUAL_SCENE_REVIEW',original_screens=screens_reviewed,newgame_three_screens_byte_identical=True,extra_probe_run=VISUAL[1],extra_native_processes=1,extra_saves=0,room_visible=True,road_visible=True,reason_ja='画像表示時の疑義を原本全byte/非黒pixel/色数と個別画像で解消。元3室内画像は同じSHAで正常。追加無入力4画面も同じ室内。描画不具合を観測したという主張は撤回。'))
 evidence={p.relative_to(ROOT).as_posix()for p in e.rglob('*')if p.is_file()}
 cp=dict(schema_version=1,status=report['status'],candidate=ir['candidate'],isolated=dict(source=ISOLATED_SOURCE,run=ISOLATED_RUN,job=ISOLATED_JOB,artifact=ISOLATED_ARCHIVE[0],archive_size=ISOLATED_ARCHIVE[2],archive_sha256=ISOLATED_ARCHIVE[3],native=ir['native'],link=ir['link'],placement=ir['placement']),gameplay=dict(source=SOURCE,run=RUN,job=JOB,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],measurement=report),outer_load_guard_wired=True,newgame_wired=True,ordinary_save_continue_accepted=True,all_consumers_wired=False,all_save_modes_accepted=False,formal_rom_changed=False,formal_save_changed=False,formal_save=101,release_ready=False,source_bindings=bindings(CODE|isolated.CODE|gameplay.CODE|visual.CODE),evidence_bindings=bindings(evidence),record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA'],record_native_processes=0,record_arm_compiles=0,visual_review=dict(run=VISUAL[1],job=111524369801,artifact=VISUAL[0],archive_size=VISUAL[2],archive_sha256=VISUAL[3],source=BASE,extra_native_processes=1,ordinary_saves=0,original_nonblank_screens=6))
 write(ROOT/CP,cp)
 goal=('正式ROM/Save101は保持。PR16_DEX_LIFECYCLE_JA.mdとpr16_dex_lifecycle_checkpoint.jsonから再開。候補限定でpost-QOL load gateとCFRU wipe後InitNew、正常fallback保持/MDX無効時global2、Save101のlegacy移行→通常Save→独立coldContinue、新規ゲーム→初回Save→独立coldContinueまで受入。'
       '次はSID喪失前の全consumerを新ownerへ接続する。battle entry/switch、active捕獲/授受/孵化/進化、UI/native count、CFRU Bag誤読count、reward clear、Factory memorial/Codex seen rollback、DexNavをinventory順に対象scopeへ分ける。'
       'authority不明invalid-liveの非破壊的保存失敗伝播、HOF/overwrite等全save mode固有副作用と実失敗画面も未受入。旧stock mirrorを大量拡張せず新namespace APIを使う。影響native後だけ正式ROM基準とstory再開を判断。最終はシオウPokecenter通常回復/Save/coldContinue、雑魚戦ごとのSaveなし。')
 state['story_dex_owner']['runtime_integration']['load_newgame']=dict(checkpoint=CP,guide=GUIDE,status=report['status'],candidate=ir['candidate'],isolated_run=ISOLATED_RUN,gameplay_run=RUN,outer_load_guard_wired=True,newgame_wired=True,ordinary_save_continue_accepted=True,all_consumers_wired=False,formal_save_changed=False,record_run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']='正式ROM/Save101保持。図鑑候補のload/newgame接続と通常Save/独立coldContinueを受入。全consumer、全save mode/失敗UI、正式進行復帰は未完。';state['bp']['next_step']=goal
 state['next_action'].update(id='WIRE_DEX_TYPED_CONSUMERS_AND_SAVE_FAILURES',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_CONSUMERS_JA.md','content/modernization/pr16_dex_load_status_audit.json'])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='候補限定の図鑑load/newgameと通常Save/独立Continueを記録したsource。正式ROM/Save101保持。記録native0。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(bindings(CODE|isolated.CODE|gameplay.CODE|visual.CODE|evidence|{CP}));state['do_not_repeat'].append(f'図鑑load/newgame隔離run{ISOLATED_RUN}の52caseと通常lifecycle run{RUN}の4process/2保存をsource/候補不変で再実行しない。候補内のSave102/新規Save1を正式Save101へ昇格せず、全consumer/全mode/失敗UIの未完を保持。')
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-LIFECYCLE / 図鑑load/newgameと通常保存\n- Version: dex-lifecycle-v1\n- Status: DONE（候補lifecycle限定。全consumer等は次工程）\n- Summary: MDXのstale-valid排除、正常fallback保持、無効時global2でContinue遮断。CFRU wipe後InitNew tail188byteを追加し、既存108ownerと元schedulerを保持。\n- Files changed: lifecycle/gameplay source、候補接続/status監査、専用workflow/試験、checkpoint/evidence、固定MDJSON、両ログ。\n- Verify: isolated run{ISOLATED_RUN}/job{ISOLATED_JOB}全10step、6generator/50host、52隔離ARM、EWRAM/IWRAM全非owner。gameplay run{RUN}/job{JOB}全10step、6host/受入4process（原本3再利用＋新cold1）/2通常Save/2独立cold、全SaveRTC不変のcold。既受入native再走0。画像表示の疑義を原本6画面と追加無入力probe1process/4画面で解消。\n- Boundary: 正式ROM/Save101不変。初回STARTのflag83E/1bitのみsource/ROM窓で同定し、保存原本から逆変換で全進行hashを復元。NewGame初回はtype4、Save101はtype0。全consumer、高ownerの自然登録、全save mode、authorityなし保存失敗UIは未受入。初回run37230632321はcompile診断/native0、run37231227293と37231607258はNewGame差分診断failureのまま保持。\n- Commit: record source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoGitHub/Actions/既存入力と公式Ubuntu toolchain。公開はsource/最小address-size-SHA/text/screens/承認済の新候補saveのみ。入力save/ROM/runtime/runner非公開。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 need(bindings(protected)==protected,'all previously accepted sources retained')
 owned={STATE,DOC,CP,*LOGS}|evidence;write(OUT/'owned.json',sorted(owned));write(PUBLIC/'lifecycle-record.json',cp);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed readback')
 print('RESULT=DONE TASK=USER-20261004-DEX-LIFECYCLE VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
 if not PUBLIC.exists():return
 need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated record directory')
 for p in PUBLIC.iterdir():
  need(p.name=='lifecycle-record.json'and p.is_file()and not p.is_symlink(),'explicit receipt only');raw=p.read_bytes();need(0<len(raw)<250000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded JSON');json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','record','guard','snapshot','export'),'bounded record action');globals()[sys.argv[1]]()
