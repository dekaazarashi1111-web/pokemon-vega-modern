#!/usr/bin/env python3
"""compact容量/lease記録の完了を閉じる。host/ARM/nativeの再実行なし。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as transport
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
BASE='d95b455d2f66675ffbcd4532bef3828dfa1f7eae'
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
 current();need(set(git('diff','--name-only',BASE,'HEAD').decode().splitlines())==CODE,'only receipt-path correction source')
 state=json.loads((ROOT/STATE).read_bytes())
 for p,b in state['source_bindings'].items():
  need(identity(git('show',BASE+':'+p) if p in CODE else (ROOT/p).read_bytes())==b,'exact preserved source or explicit prior correction preimage '+p)
def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists(),'one receipt path recovery');OUT.mkdir()
 state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 need(state['pending_runs']==[],'capacity record already closed')
 r=transport.api('actions/runs/37220882395');j=transport.api('actions/jobs/111490799117')
 need(r['head_sha']=='89ca1ca6fdb8d0c38949d9bea74227c3bc09082c'and r['status']=='completed'and r['conclusion']=='success','previous closeout terminal')
 need(j['run_id']==37220882395 and len(j['steps'])==12 and all(x['conclusion']=='success'for x in j['steps']),'previous all12 steps, upload warned missing path')
 receipt=state['story_dex_owner']['runtime_integration']['capacity']['recording']
 need(receipt['run']==RUN and receipt['source']==SOURCE and receipt['receipt_whole_bytes_verified']is True,'existing exact record receipt')
 # 既存closeoutはexport先とupload pathだけ不一致。受入・pending・checkpointは変更しない。
 write(OUT/'receipts/closeout.json',receipt)
 state['story_dex_owner']['runtime_integration']['capacity']['receipt_path_recovery']=dict(previous_closeout_run=37220882395,previous_closeout_job=111490799117,reason_ja='export先とupload pathの不一致だけを修正し既存receiptを再公開。旧試験/nativeは再実行しない。',recovery_source=os.environ['GITHUB_SHA'],recovery_run=int(os.environ['GITHUB_RUN_ID']),host_tests=0,arm_compiles=0,native_processes=0)
 for p in CODE:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
 publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261004-DEX-CAPACITY / closeout receipt公開pathの訂正\n- Version: dex-capacity-v1-receipt-path\n- Status: DONE（記録receiptのみ。実ROM接続は未完）\n- Summary: 先行closeoutの全12step・固定MD/JSONは成功していたがupload pathがexport先と不一致でartifact0件だった。pathを訂正し、同じ既存receiptを検査済directoryから公開する。\n- Files changed: closeout script/workflow、固定MD/JSONのsource binding、両ログ。\n- Verify: 先行終端/既存receipt/訂正前sourceを照合。新host0/ARM0/native0/ROM・Save変更0。pendingは空のまま。\n- Commit: recovery source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/公開receiptのみ。\n'
 for p in LOGS:
  with(ROOT/p).open('a')as f:f.write(entry)
 for p,b in protected.items():
  if p not in CODE:need(identity((ROOT/p).read_bytes())==b,'all unaffected accepted source unchanged '+p)
 owned={STATE,DOC,*LOGS};write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))
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
