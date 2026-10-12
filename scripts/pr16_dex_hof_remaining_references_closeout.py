#!/usr/bin/env python3
"""有限参照deltaの終端確認。分類・ROM・host・nativeを再実行しない。"""
import datetime,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_remaining_references_actions as w
import pr16_story_live_probe as t
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
current,bindings=w.prior.current,w.prior.bindings
BASE='6d08fcbaa12c5bdd8399b3cce44f6ff8932cf098';SOURCE='3bf77f041db9f4a840c22451ca1dd33342682d99';RUN=37323654514;JOB=111808776979
ARCHIVE=(11350699749,RUN,1365469,'7827b01a03e9ef4502c4b1ad8af033ba2ea14635ff5d59aa0334bcbec934c82b')
EXPECTED=dict(unit_tests=161,classified=694,unclassified=180,newly_classified=33,new_data=26,new_code=7,new_song=0,combined_song_models=132,owner_unknown=1,unowned_unknown=179,retained_sample_witnesses=49)
WF='.github/workflows/pr16-dex-hof-remaining-references-closeout.yml';SELF='scripts/pr16_dex_hof_remaining_references_closeout.py'
CODE={w.WF,WF,SELF,'tests/test_pr16_dex_hof_remaining_references_closeout.py'};OUT=ROOT/'.local/pr16-dex-hof-remaining-references-closeout';PUBLIC=ROOT/'public-dex-hof-remaining-references-closeout';ARTIFACT='pr16-dex-hof-remaining-references-closeout-text-only'


def source_guard():
 import pr16_learnset_runtime_record as g
 current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()


def close():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 current();need(not OUT.exists()and not PUBLIC.exists(),'one terminal reference closeout');OUT.mkdir(parents=True);PUBLIC.mkdir();state=json.loads((ROOT/w.STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every earlier bound original '+path)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'only completed measurement trigger retired')
 run=t.api('actions/runs/'+str(RUN));job=t.api('actions/jobs/'+str(JOB))
 need(run['head_sha']==SOURCE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==RUN and len(job['steps'])==14 and all(s['conclusion']=='success'for s in job['steps']),'all fourteen reference measurement steps successful')
 publication.consumer(t.api('actions/artifacts/'+str(ARCHIVE[0])),w.ARTIFACT,RUN);archive,_=t.archive(ARCHIVE)
 with archive:
  names=set(w.PROOF)|{'record.json',*(name for name,_ in w.SNAPSHOTS)}
  need(set(archive.namelist())==names and len(archive.infolist())==len(names)and all(not i.is_dir()and i.external_attr>>28!=10 for i in archive.infolist()),'complete closed nonsymlink measured text archive')
  receipt=json.loads(archive.read('record.json'));measure=json.loads(archive.read('measurement.json'))
  need(receipt['final_head']==BASE and receipt['source_head']==SOURCE and receipt['record_run']==RUN and measure['source_head']==SOURCE and measure['run_id']==RUN,'exact measured source/record lineage')
  for name,path in w.SNAPSHOTS:
   raw=archive.read(name);need(raw==(ROOT/path).read_bytes()==git('show',BASE+':'+path)and raw.endswith(b'\n'),'all committed original snapshot bytes and LF')
   binding=receipt['final_blobs'][path];need(identity(raw)=={k:binding[k]for k in('size','sha256')}and git('rev-parse',BASE+':'+path).decode().strip()==binding['git_blob_sha'],'whole exact original Git blob')
  for name in w.PROOF:need(archive.read(name)==(ROOT/w.EVIDENCE/name).read_bytes(),'all original reference measurements retained')
 cp=json.loads((ROOT/w.CP).read_bytes())
 need(all(cp[k]==v and measure[k]==v for k,v in EXPECTED.items())and cp['candidate']==measure['candidate']==w.data.CANDIDATE,'exact source and candidate counters')
 need(cp['source_bindings']==measure['source_bindings']and cp['inherited_bindings']==measure['inherited_bindings'],'exact measured source identities')
 need(cp['delta_identity']==measure['delta_identity']and cp['reference_baseline']==w.delta.BASELINE,'one immutable baseline/delta identity')
 inherited=w.delta.parent((ROOT/w.delta.BASELINE).read_bytes(),(ROOT/w.delta.EARLIER).read_bytes(),(ROOT/w.delta.PARENT).read_bytes());delta=w.delta.read_measured((ROOT/w.EVIDENCE/'reference-chain.json').read_bytes(),cp['delta_identity'],inherited);full=w.delta.materialize(inherited,delta)
 need(len(full['hits'])==874 and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all prior661 and remainingunknowns exactly retained')
 need(full['reference_delta']==inherited['reference_delta']and full['reference_chain']==inherited['reference_chain'],'both full original delta families and witnesses retained')
 need(cp['current_owner_count']==115 and cp['current_rom_reconstructions']==1 and cp['tutor_upper_word_remains_unknown']is True and not any(cp[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns')),'no unproved runtime or donor promotion')
 need(state['pending_runs']==[dict(run_id=RUN,tested_head=SOURCE,status='in_progress')],'only exact original measurement pending');state['pending_runs']=[]
 tests=(ROOT/'.local/pr16-remaining-references-closeout-tests.txt').read_bytes();need(tests.count(b' ... ok\n')==9 and b'\nOK\n'in tests,'nine new synthetic final-publication guards')
 result=dict(status='PASS_TERMINAL_EXACT_REMAINING_REFERENCE_CHAIN_RECORD',source_head=SOURCE,record_head=BASE,run=RUN,job=JOB,all14_steps_success=True,archive=ARCHIVE,all5_snapshots_full_bytes_and_lf_verified=True,checkpoint=w.CP,checkpoint_identity=identity((ROOT/w.CP).read_bytes()),**EXPECTED,delta_identity=cp['delta_identity'],baseline_identity=w.delta.BASELINE_ID,parent_identity=w.delta.PARENT_ID,earlier_identity=w.delta.EARLIER_ID,old661_accepted_and_all874_identities_retained=True,both_old_delta_families_preserved=True,closeout_source=os.environ['GITHUB_SHA'],closeout_run=int(os.environ['GITHUB_RUN_ID']),tests_rerun=0,new_export_guard_tests=9,export_guard_test_log=identity(tests),arm_compiles=0,native_processes=0,current_rom_reconstructions=0,candidate_changed=False,donor_leased=False,formal_save_changed=False)
 state['story_dex_owner']['runtime_integration']['hof_remaining_references']['recording']=result;state['observed_head_checks'].update(record_run=RUN,record_job=JOB,all14_steps_success=True,whole_receipt_equals_checkpoint=True)
 state['source_bindings'].update(bindings(CODE));publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-REMAINING-REFERENCES / 追加33参照chainの終端\n- Version: hof-remaining-references-closeout\n- Status: STOPPED（33件の分類・記録を受入。donor/本番controllerは未完）\n- Summary: run{RUN}/job{JOB}全14step成功。artifact{ARCHIVE[0]}の全10text原本、固定MDJSON/CP/両ログの全byte・LF・Git blobを照合しpending解除。measurement起動条件だけmanual-onlyへ。\n- Files changed: closeout source/workflow、measurement起動条件、固定MDJSON、両append-onlyログ。\n- Verify: 原本161tests、owner4/engine6/text22/LZ1の33追加、694分類/180未知（owner内1/外179）を再利用。旧661全行・644delta25行/22witness・661chain17行/16witness・残unknown全field不変。既存132曲/49sample/finite-root rolesと全親証拠継承を確認。新公開guard9tests PASS。旧分類/host/ARM/ROM/native再走0。\n- Publication: 619原本4.1MB＋644delta149772byte＋661chain95619byteは参照保持。child {cp["delta_identity"]["size"]}byte、独立measurement全SHA・closed schema・typed geometry・全量上限。公開metadataは必要なsource identity/address-size-SHAへ縮小、private archive名/member path/不要relocation情報を除去。\n- Boundary: 現候補0641/115owner/52saveowner/804byte/正式ROM/Save101不変。donor0、実controller/heap lifetimeは未完、heap13352の保存退避53300跨ぎ禁止。静的有限根を自然story到達/描画/再生へ昇格しない。T09/currentPLC2混同を拒否。一般CI既知QOL不一致/action_required job0/Stage79cacheを別扱い。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: closeout source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/text原本のみ。ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n'

 for path in w.LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 write(PUBLIC/'closeout.json',result)
 for name,path in w.SNAPSHOTS:(PUBLIC/name).write_bytes((ROOT/path).read_bytes())
 # 最終snapshot receiptを含む保守的な上限をpush前に検査。
 projected=dict(result,final_head='0'*40,final_blobs={path:dict(**identity((PUBLIC/name).read_bytes()),git_blob_sha='0'*40,trailing_newline=True)for name,path in w.SNAPSHOTS})
 planned={name:(PUBLIC/name).read_bytes()for name,_ in w.SNAPSHOTS};planned['closeout.json']=(json.dumps(projected,ensure_ascii=False,indent=2)+'\n').encode();w.bounded_files(planned)
 owned={w.STATE,*w.LOGS}
 if(ROOT/w.DOC).read_bytes()!=git('show','HEAD:'+w.DOC):owned.add(w.DOC)
 write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned))


def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'closeout.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'all committed closeout bytes')
 for name,path in w.SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(PUBLIC/name).read_bytes()and raw.endswith(b'\n'),'whole committed snapshot LF');receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in w.LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'old logs are exact prefixes')
 write(PUBLIC/'closeout.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-REMAINING-REFERENCES VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected={'closeout.json',*(name for name,_ in w.SNAPSHOTS)}
 need(set(files)==expected,'complete six-file terminal artifact, never a partial success')
 w.bounded_files(files);receipt=json.loads(files['closeout.json'])
 need(receipt.get('final_head')==head and len(head)==40 and receipt.get('status')=='PASS_TERMINAL_EXACT_REMAINING_REFERENCE_CHAIN_RECORD','completed snapshot receipt and current commit')
 proofs=receipt.get('final_blobs',{});need(set(proofs)=={path for _,path in w.SNAPSHOTS},'all final snapshot receipts')
 for name,path in w.SNAPSHOTS:
  raw=files[name];binding=proofs[path]
  need(binding.get('trailing_newline')is True and raw.endswith(b'\n')and identity(raw)=={k:binding[k]for k in('size','sha256')},'complete committed final snapshot identity')
  import hashlib
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'exact final Git blob content')
 return True

def export():
 publication.output(PUBLIC,success='closeout.json',failure=None);files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in{'closeout.json',*(n for n,_ in w.SNAPSHOTS)},'closed terminal flat text set');files[path.name]=path.read_bytes()
 validate_export(files,git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','close','guard','snapshot','export'),'closed terminal reference modes');globals()[sys.argv[1]]()
