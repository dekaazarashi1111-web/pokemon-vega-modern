#!/usr/bin/env python3
"""保存済み型分類の冗長領域証拠だけ圧縮。旧分類/ROM/nativeを再実行しない。"""
import copy,datetime,io,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_typed_actions as w
import pr16_dex_publication as publication
need,identity,write,git=w.need,w.identity,w.write,w.git
prior=w.prior
BASE='908289942a276fa4f552d96aae4d985f7c6a5156';ORIGINAL_SOURCE='920cbc492bb8c65ee0364f9420d3a152f1f72e5f';ORIGINAL_RUN=37300879978;ORIGINAL_JOB=111733040155
ORIGINAL_AUDIT=dict(size=18862653,sha256='679b632bb92d98e67b532a74bf3b9a2c0f288c3bd892ec584c7763a99cba7354')
WF='.github/workflows/pr16-dex-hof-typed-recovery.yml';SELF='scripts/pr16_dex_hof_typed_recovery.py';GUIDE='docs/PR16_DEX_HOF_TYPED_RECOVERY_JA.md'
CODE={w.WF,WF,SELF,GUIDE,'tests/test_pr16_dex_hof_typed_recovery.py'}
CP='content/modernization/pr16_dex_hof_typed_recovery_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_typed_recovery_evidence'
STATE=w.STATE;DOC=w.DOC;LOGS=w.LOGS
OUT=ROOT/'.local/pr16-dex-hof-typed-recovery';PUBLIC=ROOT/'public-dex-hof-typed-recovery';ARTIFACT='pr16-dex-hof-typed-recovery-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','typed-tests.txt','egg-typed-audit.json','recovery-tests.txt','recovery.json'}


def original_run():
 import pr16_story_live_probe as t
 run=t.api('actions/runs/'+str(ORIGINAL_RUN));job=t.api('actions/jobs/'+str(ORIGINAL_JOB))
 need(run['head_sha']==ORIGINAL_SOURCE and run['status']=='completed'and run['conclusion']=='failure'and run['run_attempt']==1 and job['run_id']==ORIGINAL_RUN,'exact terminal original publication failure')
 steps=job['steps'];need(len(steps)==14,'all original terminal steps')
 need(all(s['status']=='completed'for s in steps),'no original step running')
 need([s['conclusion']for s in steps]==['success']*10+['failure','skipped','success','success'],'measurement/record/push/readback passed; publication guard failed and upload skipped')
 return dict(run=ORIGINAL_RUN,job=ORIGINAL_JOB,source=ORIGINAL_SOURCE,conclusion='failure',measurement_record_push_readback_success=True,publication_guard='failure',artifact_upload='skipped',steps=[dict(name=s['name'],conclusion=s['conclusion'])for s in steps])


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());protected=state['source_bindings']
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'unchanged inherited source '+path)
 old=git('show',BASE+':'+w.WF);trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+w.WF+']\n').encode()
 need(identity(old)==protected[w.WF]and old.count(trigger)==1 and(ROOT/w.WF).read_bytes()==old.replace(trigger,b'  workflow_dispatch:\n'),'retire only measured workflow trigger')
 need(state['pending_runs']==[dict(run_id=ORIGINAL_RUN,tested_head=ORIGINAL_SOURCE,status='in_progress')],'one recorded original pending run')
 original_run()


def compact_audit(original):
 """全hit/consumer証拠保持。新numeric hitに無関係な重複region列挙だけ落とす。"""
 result=copy.deepcopy(original);extension=result['typed_numeric_extension'];regions=extension['regions'];hits=result['hits']
 targets={r['address']for r in extension['changed_hits']}
 need(len(targets)==extension['newly_classified'],'unique changed numeric/palette origins')
 active=[r for r in hits if r['address']in targets]
 need(len(active)==len(targets)and all(r['accepted']for r in active),'all changed numeric/palette hits present and accepted')
 kept=[]
 for region in regions:
  address,size=region['address'],region['size'];need(type(address)is int and type(size)is int and size>0,'positive typed region')
  matches=[h for h in active if address<=h['address']and h['address']+h['size']<=address+size]
  if not matches:continue
  need(all(region['evidence']in h['evidence']for h in matches),'every retained region already in exact hit evidence')
  kept.append(region)
 for hit in active:
  need(any(r['address']<=hit['address']and hit['address']+hit['size']<=r['address']+r['size']and r['evidence']in hit['evidence']for r in kept),'all changed hit witnesses retained')
 need(kept and len(kept)<len(regions),'only genuine redundant region list reduced')
 extension['regions']=kept
 extension['region_list_compaction']=dict(original_region_count=len(regions),retained_region_count=len(kept),removed_unreferenced_region_count=len(regions)-len(kept),hit_rows_changed=0,all_hit_evidence_retained=True,all_pool_partition_and_source_proof_retained=True)
 need(result['hits']==original['hits'],'all 874 hit rows including witnesses exact')
 for key in original:
  if key!='typed_numeric_extension':need(result[key]==original[key],'all unrelated audit fields exact')
 for key in original['typed_numeric_extension']:
  if key!='regions':need(extension[key]==original['typed_numeric_extension'][key],'all other numeric proof fields exact')
 return result


def run():
 import test_pr16_dex_hof_typed_recovery as tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one new text-only recovery');OUT.mkdir(parents=True);PUBLIC.mkdir();terminal=original_run()
 cp=json.loads((ROOT/w.CP).read_bytes());m=json.loads((ROOT/w.EVIDENCE/'measurement.json').read_bytes());raw=(ROOT/w.EVIDENCE/'egg-typed-audit.json').read_bytes()
 need(identity(raw)==ORIGINAL_AUDIT==m['typed_audit_identity']and cp['typed_audit_identity']==ORIGINAL_AUDIT,'whole immutable original audit')
 need(cp['source_head']==m['source_head']==ORIGINAL_SOURCE and cp['record_run']==m['run_id']==ORIGINAL_RUN,'original measurement lineage')
 for path,binding in cp['evidence_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'each original measured artifact byte')
 old=json.loads(raw);inherited=json.loads((ROOT/w.INVENTORY).read_bytes());w.validate_record_audit(old,m,inherited)
 stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));(PUBLIC/'recovery-tests.txt').write_text(stream.getvalue());need(test.wasSuccessful(),'new representation-only negative tests')
 compact=compact_audit(old);w.validate_record_audit(compact,m,inherited);write(PUBLIC/'egg-typed-audit.json',compact)
 compact_identity=identity((PUBLIC/'egg-typed-audit.json').read_bytes());need(compact_identity['size']<8000000,'compact complete evidence under bounded upload limit')
 measure=copy.deepcopy(m);measure['typed_audit_identity']=compact_identity;measure['representation_recovery']=dict(status='COMPACTED_FROM_COMMITTED_MEASUREMENT_NO_RECLASSIFICATION',original_checkpoint=w.CP,original_checkpoint_identity=identity((ROOT/w.CP).read_bytes()),original_audit=ORIGINAL_AUDIT,original_measurement=identity((ROOT/w.EVIDENCE/'measurement.json').read_bytes()),original_run=terminal,new_classifications=0,rom_reconstructions=0,native_processes=0)
 write(PUBLIC/'measurement.json',measure);(PUBLIC/'typed-tests.txt').write_bytes((ROOT/w.EVIDENCE/'typed-tests.txt').read_bytes())
 receipt=dict(status='PASS_COMMITTED_TYPED_EVIDENCE_COMPACTION_ONLY',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),original_record_head=BASE,original_source=ORIGINAL_SOURCE,original_run=terminal,original_audit=ORIGINAL_AUDIT,compact_audit=compact_identity,compaction=compact['typed_numeric_extension']['region_list_compaction'],recovery_unit_tests=test.testsRun,measurement_unit_tests=168,classified=619,unclassified=255,new_classifications=0,rom_reconstructions=0,arm_compiles=0,native_processes=0,donor_leased=False,candidate_changed=False,formal_save_changed=False,source_bindings=prior.bindings(CODE))
 need((m['unit_tests'],m['classified'],m['unclassified'],m['newly_classified'],m['new_numeric'],m['new_palette'],m['new_song'])==(168,619,255,59,39,6,14),'exact measured frontier, no fabricated recovery counters')
 write(PUBLIC/'recovery.json',receipt)


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings'])
 for path,binding in protected.items():
  if path!=w.WF:need(identity((ROOT/path).read_bytes())==binding,'every original except retired trigger retained')
 need(not(ROOT/CP).exists(),'unique recovery checkpoint')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());r=json.loads((PUBLIC/'recovery.json').read_bytes());need(identity((PUBLIC/'egg-typed-audit.json').read_bytes())==m['typed_audit_identity']==r['compact_audit'],'whole compacted audit identity');need(r['source_bindings']==prior.bindings(CODE),'exact recovery source');w.validate_record_audit(json.loads((PUBLIC/'egg-typed-audit.json').read_bytes()),m,json.loads((ROOT/w.INVENTORY).read_bytes()))
 paths=set()
 for name in sorted(PROOF):
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'new immutable recovery evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((PUBLIC/name).read_bytes());paths.add(dest.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),prior_checkpoint=w.CP,recovery=r,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID'])))
 summary='現候補0641の残参照59件（level39/palette6/song14）を追加し619分類/255未知、168tests PASS。全874行と旧560受入保持。原runは記録push成功後に冗長18.9MB証拠が公開上限で拒否されfailure。保存済みGit原本を保持し、hit非参照の重複regionだけ除いた後継証拠へ回復。分類/ROM/native再実行0、donor/正式ROM/Save101不変。'
 state['story_dex_owner']['runtime_integration']['hof_typed'].update(checkpoint=CP,guide=GUIDE,representation_recovery=r)
 state['bp']['current_stop']=summary;state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='測定済み型分類の公開表現だけを回復したsource。元Actions failureをsuccessへ改称せず原本保持。'
 state['next_action']['read_paths']=[GUIDE,CP,w.GUIDE,w.CP,'scripts/pr16_dex_hof_typed_numeric.py','scripts/pr16_dex_hof_song_extended.py']
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary);state['observed_head_checks'].update(representation_recovery=r,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-TYPED / 保存済み証拠の公開表現回復\n- Version: hof-typed-recovery\n- Status: STOPPED（分類受入619/255、公開表現を回復。donor/本番配線は未完）\n- Summary: {summary}\n- Files changed: compact recovery source/新境界tests/workflow/guide/後継CP/text証拠、固定MDJSON、両append-onlyログ。元18.9MB原本と失敗runは不変。\n- Verify: 元168tests/115owner/candidate全SHA/全874byteを原本再利用。新表現tests={r["recovery_unit_tests"]}。圧縮={json.dumps(r["compaction"],sort_keys=True)}。旧分類/168tests/ARM/ROM再構築/native再走0。\n- Boundary: 全hit/evidence/全pool partition/source proof不変、参照されないregion列挙だけ削減。元run{ORIGINAL_RUN}/job{ORIGINAL_JOB}は前10step成功・guard failure・upload skippedのまま。未知255/tutor1/間接参照/実controller/heap lifetimeは未完。\n- Next: {state["next_action"]["goal_ja"]}\n- Commit: recovery source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoの保存済みtextのみ。ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_RECORDED_TYPED_REPRESENTATION_RECOVERY',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),original_source=ORIGINAL_SOURCE,original_record_head=BASE,native_processes=0))


def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed recovery text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed recovery text with LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only entire old logs retained')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-TYPED VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC,success='recovery.json',failure=None)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in PROOF|{'record.json',*(n for n,_ in SNAPSHOTS)},'closed nonsymlink flat recovery text');raw=p.read_bytes();need(0<len(raw)<8000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty recovery text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed recovery workflow');globals()[sys.argv[1]]()
