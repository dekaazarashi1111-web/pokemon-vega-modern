#!/usr/bin/env python3
"""32sector HOF storage記録の終端。追加host/ARM/nativeなし。"""
import datetime,json,os,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_storage_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
BASE='b2cec1850846b0246f3eb962b835fce2a2679d30';SOURCE='42d8d57a914bc3febede56ec21dec7e8be150e05';RUN=37271761754;JOB=111640066211
ARCHIVE=(11328289516,RUN,1309503,'ac960bb3ea49d34be621cbf5442aa2fb37a6cf42af7b6107611401128f824e09')
WF='.github/workflows/pr16-dex-hof-storage-closeout.yml'
CODE={w.WF,WF,'scripts/pr16_dex_hof_storage_closeout.py'}
OUT=ROOT/'.local/pr16-dex-hof-storage-closeout';PUBLIC=ROOT/'public-dex-hof-storage-closeout'
ARTIFACT='pr16-dex-hof-storage-closeout-receipts'

def source_guard():
 import pr16_learnset_runtime_record as g
 w.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,'scripts/pr16_dex_hof_storage_closeout.py');g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()

def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 w.current();need(not OUT.exists()and not PUBLIC.exists(),'one terminal closeout');OUT.mkdir(parents=True);PUBLIC.mkdir()
 state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for p,b in protected.items():
  if p!=w.WF:need(identity((ROOT/p).read_bytes())==b,'every previous bound byte '+p)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'completed host workflow retired without other edits')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB))
 need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and len(job['steps'])==14 and all(s['conclusion']=='success'for s in job['steps']),'record all14steps terminal success')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);z,_=t.archive(ARCHIVE)
 with z:
  names=z.namelist();need(len(names)==len(set(names))==14 and all(i.external_attr>>28!=10 for i in z.infolist()),'fourteen unique nonsymlink original texts')
  receipt=json.loads(z.read('record.json'));measurement=json.loads(z.read('measurement.json'))
  need(receipt['final_head']==BASE and receipt['source_head']==SOURCE,'exact record lineage')
  for name,path in w.SNAPSHOTS:
   raw=z.read(name);need(raw==(ROOT/path).read_bytes()==git('show',BASE+':'+path)and raw.endswith(b'\n'),'all six original artifact/source bytes '+path)
   b=receipt['final_blobs'][path];need(identity(raw)=={k:b[k]for k in('size','sha256')}and git('rev-parse',BASE+':'+path).decode().strip()==b['git_blob_sha'],'all six exact git identities')
  need(z.read('fixed-checkpoint.json')==(ROOT/w.CP).read_bytes(),'whole checkpoint equals record original')
  for name in ('measurement.json','host-tests.txt','host-metrics.json','codec-arm.json','abi-windows.json','abi-stdout.txt','attempts.json'):need(z.read(name)==(ROOT/w.EVIDENCE/name).read_bytes(),'all raw host originals unchanged')
 cp=json.loads((ROOT/w.CP).read_bytes());need(cp['host_tests']==16 and cp['native_processes']==1 and cp['native_abi']['cases']==228 and cp['codec_arm']['arm_compiles']==1,'16host/228new ABI/one codec compile')
 need(not any(cp[k]for k in('runtime_generation_binding','runtime_cross_store_atomicity','candidate_changed','formal_rom_changed','formal_save_changed','runtime_integration_accepted','all_species_accepted','initial_migration_wired')),'limited scope not promoted')
 need(cp['flash_sectors']==32 and cp['journal_bytes']==256 and cp['hof_history_teams']==50 and cp['hof_opaque_suffix_retained']==1936,'bounded actualgeometry ownership')
 need(cp['source_bindings']==measurement['source_bindings']and cp['candidate']==measurement['candidate'],'whole code/candidate identities')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only one record pending');state['pending_runs']=[]
 result=dict(status='PASS_TERMINAL_32SECTOR_HOF_STORAGE_RECORD',record_run=RUN,record_job=JOB,record_source=SOURCE,record_completion=BASE,all14_record_steps_success=True,record_archive=ARCHIVE,all6_original_snapshots_byte_equal=True,checkpoint=w.CP,checkpoint_identity=identity((ROOT/w.CP).read_bytes()),closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),host_tests_rerun=0,arm_compiles=0,native_processes=0,candidate_changed=False,runtime_generation_binding=False,runtime_cross_store_atomicity=False,formal_rom_changed=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['hof_storage']['recording']=result
 state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_record_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['source_bindings'].update(w.bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-STORAGE / 32sector HOF journal記録の終端\n- Version: dex-hof-storage-closeout\n- Status: STOPPED（容量方式/codec/実HOF ABI完了、稼働ROM配線は未完）\n- Summary: run{RUN}/job{JOB}全14stepとartifact{ARCHIVE[0]}原本14text、正本6fileの全byte/改行/Git blobを照合しpending解除。成功workflowはmanual-onlyへ。\n- Files changed: closeout source/workflow、前workflow起動条件、固定MDJSONと両ログ。\n- Verify: 16host、新228ABI、Ccodec ARM objectの原本再利用。追加host/ARM/native0。erase未確認退役の欠陥を修正済み。一般CIの既知QOL source不一致・action_required/job0・Stage79cacheは別扱い。\n- Boundary: 32sector/128KiB、50履歴・1936suffix・sector30/31保持。logical4の256byte journal、非選択logical8/9一時scratch、最後logical13。現ROM保存writer/loadへ未接続。species9bit・初回absence移行・code配置未完。正式ROM/Save101・現88be8811・115owner/43subowner/186byte不変。\n- Next: 現ownerから新codec/scheduler配置と全writer/normal/clone/readback/selector/HOF-only load接続。共通SaveFailed/早期31/cold owner/typedconsumerを閉じてから正式候補切替、trainer131後半、最終シオウ通常回復・保存・独立cold Continue。雑魚毎Saveなし。\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force push。\n- Network: 同repoActions/既存text原本のみ。ROM断片/rawhex/ROM/入力save/runtime/runner/credential追加公開0。\n'

 for p in w.LOGS:
  with(ROOT/p).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',result)
 for name,p in w.SNAPSHOTS:(PUBLIC/name).write_bytes((ROOT/p).read_bytes())
 owned={w.STATE,*w.LOGS}
 if(ROOT/w.DOC).read_bytes()!=git('show','HEAD:'+w.DOC):owned.add(w.DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 w.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')

def snapshot():
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'whole committed closeout text')
 for name,p in w.SNAPSHOTS:
  raw=git('show','HEAD:'+p);need(raw==(PUBLIC/name).read_bytes()and raw.endswith(b'\n'),'all six committed complete snapshots');receipt['final_blobs'][p]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+p).decode().strip(),trailing_newline=True)
 for p in w.LOGS:need(git('show','HEAD:'+p).startswith(git('show',BASE+':'+p)),'entire old log prefix retained')
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-STORAGE VERIFY=PASS COMMIT='+receipt['final_head'])

def export():
 publication.output(PUBLIC,success='closeout.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and p.name in{'closeout.json',*(n for n,_ in w.SNAPSHOTS)},'only explicit complete text snapshots')
  raw=p.read_bytes();need(0<len(raw)<3500000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete UTF8');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed host closeout');globals()[sys.argv[1]]()
