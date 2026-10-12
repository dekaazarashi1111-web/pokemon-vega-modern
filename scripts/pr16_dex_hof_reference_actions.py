#!/usr/bin/env python3
"""残参照の新型根と共有deltaを一度測定し、原本保持で記録する。"""
import collections,datetime,io,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_song_actions as song_actions
import pr16_dex_hof_reference_data as data
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_song as song
import pr16_dex_hof_reference_delta as delta
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='f81f21024a1f2a78466e65fc2aac3bf54e6bb1b9'
WF='.github/workflows/pr16-dex-hof-references.yml';SELF='scripts/pr16_dex_hof_reference_actions.py';GUIDE='docs/PR16_DEX_HOF_REFERENCES_JA.md'
CODE={WF,SELF,GUIDE,data.REVIEW,code.REVIEW,song.REVIEW,song.SOURCES}
CODE|={'scripts/pr16_dex_hof_reference_'+name+'.py'for name in('data','code','song','delta')}
CODE|={'tests/test_pr16_dex_hof_reference_'+name+'.py'for name in('data','code','song','delta','actions')}
OLDCP='content/modernization/pr16_dex_hof_typed_recovery_checkpoint.json'
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_reference_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_reference_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-references';PUBLIC=ROOT/'public-dex-hof-references';ARTIFACT='pr16-dex-hof-references-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','reference-tests.txt','reference-delta.json'}
MAX_FILE=4000000;MAX_TOTAL=12000000


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all inherited originals and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']==data.CANDIDATE and cp['classified']==619 and cp['unclassified']==255,'exact inherited recovered typed frontier')
 need(cp['evidence_bindings'][delta.BASELINE]==delta.BASELINE_ID==identity((ROOT/delta.BASELINE).read_bytes()),'whole inherited 874 inventory')


def bound_sources(sources):
 root=OUT/'bound-data-sources';root.mkdir()
 review=json.loads((ROOT/data.REVIEW).read_bytes())
 for path in [data.REVIEW,*review['source_bindings']]:
  raw=sources['cfru-trainer-battle.h']if path=='vendor/upstream/CFRU-JP/include/battle.h'else(ROOT/path).read_bytes()
  target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 data.source_proof(root);code.source_proof(ROOT)
 return root


def bounded_files(files):
 need(files and sum(len(raw)for raw in files.values())<MAX_TOTAL,'nonempty bounded total publication')
 for name,raw in files.items():
  need(0<len(raw)<MAX_FILE and raw.endswith(b'\n')and b'\0'not in raw,'complete bounded text '+name);raw.decode('utf8')
  if name.endswith('.json'):json.loads(raw)
 need('reference-delta.json'not in files or len(files['reference-delta.json'])<=delta.MAX_DELTA_BYTES,'bounded shared delta')
 return {name:identity(raw)for name,raw in files.items()}


def run():
 import pr16_dex_hof_song_extended as extended
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_reference_data as data_tests
 import test_pr16_dex_hof_reference_code as code_tests
 import test_pr16_dex_hof_reference_song as song_tests
 import test_pr16_dex_hof_reference_delta as delta_tests
 import test_pr16_dex_hof_reference_actions as action_tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh reference scope');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in(data_tests,code_tests,song_tests,delta_tests,action_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'reference-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new fail-closed reference suites')
  song_actions.OUT=OUT;song_actions.SOURCES=song.SOURCES;sources,bindings=song_actions.public_sources();source_root=bound_sources(sources)
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==latest['candidate']==data.CANDIDATE,'whole exact current candidate reconstruction')
  owners=data.d.bind_owners(current,latest);need(len(owners)==115,'all current actual owner bindings')
  inherited=delta.baseline((ROOT/delta.BASELINE).read_bytes())
  for hit in inherited['hits']:need(identity(data.chunk(current,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'every retained hit actual bytes')
  r1,p1=data.data_regions(current,latest,inherited,source_root);r2,p2=code.code_regions(current,latest,inherited)
  engine=extended.bind_engine(current,json.loads((ROOT/song_actions.ENGINE).read_bytes()),json.loads((ROOT/'content/modernization/pr16_dex_hof_song_extended_engine_review.json').read_bytes()))
  r3,p3=song.song_regions(current,inherited,engine,sources,r1+r2)
  need(all(not(r.start<s.end and s.start<r.end)for r in r1+r2 for s in r3),'data/code and song roles disjoint')
  evidence=delta.build(inherited,r1+r2+r3,dict(data=p1,code=p2,song=p3,public_source_bindings=bindings))
  full=delta.materialize(inherited,evidence)
  need(data.d.compare_inventory(full['hits'],inherited)['same_inventory']and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all874 identities and retained619/remainingunknown rows exact')
  need(evidence['newly_classified']==25 and evidence['classified']==644 and evidence['unclassified']==230,'exact new17 data/1 instruction/7 song frontier')
  write(PUBLIC/'reference-delta.json',evidence)
  m=dict(status='PASS_CURRENT_FINITE_REFERENCE_DELTA',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
   classified=evidence['classified'],unclassified=evidence['unclassified'],newly_classified=evidence['newly_classified'],new_data=17,new_code=1,new_song=7,old_inventory_candidates=874,previous_classified=619,previous_unknown=255,
   all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,delta_identity=identity((PUBLIC/'reference-delta.json').read_bytes()),baseline_identity=delta.BASELINE_ID,
   source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({OLDCP,delta.BASELINE,LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json'}),
   current_owner_count=len(owners),current_rom_reconstructions=reconstructed,old_full_rom_scan_runs=0,native_processes=0,accepted_heap_reruns=0,
   combined_song_models=p3['combined_song_count'],old_models_reused_for_new_cross_song_role_safety=True,tutor_upper_word_remains_unknown=True,
   donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False)
  write(PUBLIC/'measurement.json',m);bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()})
 except Exception as exc:
  # 下位compiler/decoderの詳細には私有byte/pathがあり得る。公開失敗証拠へ転記しない。
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc())
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,error_code='REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',native_processes=0,current_rom_reconstructions=reconstructed))
  raise RuntimeError('REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED') from None


def validate_measurement(m):
 need(m['status']=='PASS_CURRENT_FINITE_REFERENCE_DELTA'and m['source_head']==os.environ['GITHUB_SHA']and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact successful source/run measurement')
 expected=dict(current_owner_count=115,current_rom_reconstructions=1,new_data=17,new_code=1,new_song=7,newly_classified=25,old_inventory_candidates=874,previous_classified=619,previous_unknown=255,classified=644,unclassified=230,combined_song_models=130)
 need(all(type(m[k])is int and m[k]==v for k,v in expected.items()),'exact bound measurement counters')
 need(type(m['unit_tests'])is int and m['unit_tests']>0 and all(m[k]is True for k in('all_prior_accepted_retained','remaining_unknown_rows_retained','old_full_rom_inventory_reused','old_models_reused_for_new_cross_song_role_safety','tutor_upper_word_remains_unknown')),'measured retention contracts')


def validate_record(m,raw,inherited):
 evidence=delta.read_measured(raw,m['delta_identity'],inherited)
 validate_measurement(m)
 categories=collections.Counter(row['classification']for row in evidence['changes'])
 need(categories=={'FALSE_POSITIVE_TYPED_REFERENCE_TRAINER_NAME_ITEM_CROSS_FIELD':15,'FALSE_POSITIVE_TYPED_REFERENCE_ZLIB_SERIALIZED_ARCHIVE':2,'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_THUMB_INSTRUCTION_CROSSING':1,'FALSE_POSITIVE_TYPED_REFERENCE_PCM8':7},'exact independently measured delta category counts')
 full=delta.materialize(inherited,evidence)
 need(m['candidate']==evidence['candidate']==inherited['candidate']==data.CANDIDATE,'record same whole candidate')
 for key in('classified','unclassified','newly_classified'):need(m[key]==evidence[key],'record exact additive counters')
 need(m['new_data']+m['new_code']+m['new_song']==m['newly_classified']==25 and m['combined_song_models']==130,'exact typed subset counters')
 need(not any(m[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns')),'no unproved runtime/lease promotion')
 need(all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'record keeps prior accepted and remaining unknown exact')
 return evidence


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'all earlier originals and unique new checkpoint')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());evidence=validate_record(m,(PUBLIC/'reference-delta.json').read_bytes(),delta.baseline((ROOT/delta.BASELINE).read_bytes()))
 need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'all measured source and predecessor bindings')
 bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()});paths=set()
 for name in sorted(PROOF):
  target=ROOT/EVIDENCE/name;need(not target.exists(),'immutable reference evidence');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((PUBLIC/name).read_bytes());paths.add(target.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),previous_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),reference_baseline=delta.BASELINE))
 summary=f'現0641の旧egg874参照にtrainer15/archive2/命令跨ぎ1/有限JP音声7の25件を追加し、644分類/230未知。新{m["unit_tests"]}試験と新旧130曲の役割競合を検証。T09上位wordは別PLC2consumerとの混同を拒否し未知保持。原本4.1MBは再複製せず共有delta {m["delta_identity"]["size"]}byteへ。全旧619受入不変、donor/正式ROM/Save101不変。'
 goal='残230の未分類（T09上位word、残code/data/audio根）を閉じ、間接参照・旧egg退役完全性を証明する。未知0と退役ゲート後だけ必要容量を明示donor移管し、Ccontroller実owner配置、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、保存入口heap-ready/同期非再入/全出口Freeを閉じる。その後正式候補切替、trainer131後半から最終シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_references']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=644,unclassified=230,delta_identity=m['delta_identity'],tutor_upper_word_remains_unknown=True,donor_leased=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_REMAINING_ROOTED_REFERENCE_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,delta.BASELINE,'scripts/pr16_dex_hof_reference_delta.py',data.REVIEW,code.REVIEW,song.REVIEW])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='不変原本＋共有deltaによる根付き参照分類source。旧sampleと新songの役割競合を含むread-only scope。donor/本番配線未受入。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'旧型分類/heap/nativeは変更影響なしに再実行しない。次回はbaseline＋deltaをmaterializeして継承する。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],reference_unit_tests=m['unit_tests'],classified=644,unclassified=230,native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-REFERENCES / 有限型根と共有参照delta\n- Version: hof-reference-delta-v1\n- Status: STOPPED（新25分類・記録済、donor/本番controllerは未完）\n- Summary: {summary}\n- Files changed: 新classifier/拒否tests/source review/Actions/guide/CP/minimal text evidence、固定MDJSON、両append-onlyログ。\n- Verify: unit={m["unit_tests"]}; 全candidate/115 actual owner/全874hit SHA、tracker source全blob、JP trainer C ABI/serializer/全TOC22stream、rooted Thumb12byteとliteral分離。音声は有限root4曲追加に伴う新旧130曲の全role競合確認。旧619と残unknown全field不変、旧全ROMscan/native/heap0。\n- Boundary: 旧formalは事前意味reviewのみ、現0641で再束縛。T09上位wordは現wrapperが別PLC2を読むため未知保持。codeのELF節名/owner名だけの分類なし。donor0、正式ROM/Save101不変、heap13352の保存退避53300跨ぎ禁止、HOF32sector実controller未配線。\n- Publication: 原本4.1MBは参照継承。新delta {m["delta_identity"]["size"]}byte、独立measurement全SHAとclosed schemas/typed geometry/2MB上限を検査。producer/guard/uploadと全snapshot総量をpush前に機械検査。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputs/固定公開source。公開はsource/最小address-size-SHA/textのみ。ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'earlier originals preserved')
 # 同じ実snapshot bytesをcommit前に上限検査。upload直前の初回発見を避ける。
 planned={name:(PUBLIC/name).read_bytes()for name in PROOF};planned.update({name:(ROOT/path).read_bytes()for name,path in SNAPSHOTS});bounded_files(planned)
 receipt=dict(status='PASS_RECORDED_REFERENCE_DELTA',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0,precommit_publication_files=bounded_files(planned))
 # commit SHA長だけ先取りし、最終receipt自体も含む全量を保守的に予算へ入れる。
 projected=dict(receipt,final_head='0'*40,final_blobs={path:dict(**identity(planned[name]),git_blob_sha='0'*40,trailing_newline=True)for name,path in SNAPSHOTS})
 bounded_files(dict(planned,**{'record.json':(json.dumps(projected,ensure_ascii=False,indent=2)+'\n').encode()}))
 owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',receipt)


def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed reference bytes')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed snapshot/LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only old log bytes')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-REFERENCES VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC)
 files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in PROOF|{'failure.json','record.json',*(n for n,_ in SNAPSHOTS)},'closed regular nonhidden text publication')
  files[path.name]=path.read_bytes()
 bounded_files(files)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed reference workflow');globals()[sys.argv[1]]()
