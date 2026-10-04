#!/usr/bin/env python3
"""compact容量/lease記録の完了を閉じる。host/ARM/nativeの再実行なし。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
BASE='c004de44d7a1ab8ecbbef79521397b3bc3afc144'
SOURCE='3073f0e038c2659491889ac41521fbaf10205adb'
RUN=37220657694;JOB=111490144652
ARCHIVE=(11310395589,RUN,2531,'54583d349005fab1130a2b04a772b972220f4635206d6c65ea31e595ccf5344b')
CODE={'scripts/pr16_dex_capacity_closeout.py','.github/workflows/pr16-dex-capacity-closeout.yml'}
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_dex_capacity_checkpoint.json';LOGS={'design/run_log.md','design/version_log.md'}
OUT=ROOT/'.local/pr16-dex-capacity-closeout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','one authorized terminal recording')
 p=transport.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole exact draft HEAD')
def source_guard():
 import pr16_learnset_runtime_record as g
 current();g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists(),'one terminal closeout');OUT.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'all accepted source bindings')
 r=transport.api('actions/runs/'+str(RUN));j=transport.api('actions/jobs/'+str(JOB))
 need(r['head_sha']==SOURCE and r['status']=='completed'and r['conclusion']=='success'and r['run_attempt']==1,'terminal exact capacity record run')
 need(j['run_id']==RUN and j['conclusion']=='success'and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'all12 record steps')
 z,_=transport.archive(ARCHIVE)
 with z:
  need(z.namelist()==['capacity-record.json'],'only expected public receipt')
  need(z.read('capacity-record.json')==(ROOT/CP).read_bytes(),'whole immutable checkpoint receipt')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'one exact finished record pending')
 state['pending_runs']=[]
 receipt=dict(run=RUN,job=JOB,source=SOURCE,completion=BASE,all12_steps_success=True,artifact=ARCHIVE[0],archive_size=ARCHIVE[2],archive_sha256=ARCHIVE[3],receipt_whole_bytes_verified=True,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,rom_changed=False,save_changed=False)
 state['story_dex_owner']['runtime_integration']['capacity']['recording']=receipt
 state['observed_head_checks']=dict(scope_head=SOURCE,capacity_measurement_run=37219630045,capacity_record_run=RUN,all12_steps_success=True,compact_tests=51,lease_tests=25,c_mapping_comparisons=262144,measurement_arm_translation_units=4,record_arm_compiles=0,record_native_processes=0,runtime_wired=False,general_ci_known_source_mismatch_not_resolved=True,reason_ja='図鑑compact ARM4638byteとStage39退役owner6484byteのhash-bound契約を専用記録run全12step成功で固定。receipt全byte一致。allocator実移管/実配置/Stage61保存と全consumer/native保存は未完。正式Save101保持。Stage79 cacheを新nativeに数えず、一般CI QOL source不一致も未解決。')
 state['source_bindings'].update({p:identity((ROOT/p).read_bytes())for p in CODE});publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-CAPACITY / compact ARM容量と退役owner契約の記録終端\n- Version: dex-capacity-v1-closeout\n- Status: DONE（容量工程の記録終端。ROM接続/native受入は未完）\n- Summary: run{RUN}/job{JOB}全12step成功、記録commit{BASE}、artifact{ARCHIVE[0]}の外側SHAとcheckpoint receipt全byteを照合してpendingを解除。\n- Files changed: 専用closeout、固定MD/JSON、両ログ。\n- Verify: terminal/source bindings/resume/task graph/index guard PASS。再host0/ARM0/native0/ROM・Save変更0。51compact＋25lease試験、ARM4compile/1linkの原本を保持。\n- Next: 署名付きowner移譲と実配置relink、Stage61既存owner内置換と全save/consumer接続、保存ABI限定native後にシオウ回復へ。未割当FF借用や正式ROM基準切替をしない。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions終端と検査済text receiptのみ。既知一般CI QOL source不一致、Stage79 cache、旧9月18日queueは別扱い。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 need(all(identity((ROOT/p).read_bytes())==b for p,b in protected.items()),'all previous evidence frozen')
 owned={STATE,DOC,*LOGS};write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/closeout.json',receipt);git('add','--',*sorted(owned))
def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def export():
 if(OUT/'receipts').exists():publication.export_evidence(OUT/'receipts',ROOT/'public-dex-capacity-closeout')
def snapshot():
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole closeout committed text')
 print('RESULT=STOPPED TASK=USER-20261004-DEX-CAPACITY VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','export','snapshot'),'bounded closeout action');globals()[sys.argv[1]]()
