#!/usr/bin/env python3
"""親deltaを全文固定し、残参照の新根だけ測定・記録する。"""
import collections,datetime,hashlib,io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_field_consumer_batch as data
import pr16_dex_hof_consumer_song as song
import pr16_dex_hof_field_consumer_batch_capacity as space
import pr16_dex_hof_field_consumer_batch_chain as delta
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='5c55881d8ffdec73db319b219b4d73c9b56743be'
WF='.github/workflows/pr16-dex-hof-field-consumer-batch.yml';SELF='scripts/pr16_dex_hof_field_consumer_batch_actions.py';GUIDE='docs/PR16_DEX_HOF_FIELD_CONSUMER_BATCH_JA.md'
DEVELOPMENT='content/modernization/pr16_dex_hof_field_consumer_batch_development_validation.json'
CODE={WF,SELF,GUIDE,data.SOURCES,DEVELOPMENT,*data.REVIEWS}
CODE|={'scripts/pr16_dex_hof_'+name+'.py' for name in('field_consumer_batch','bag_sort_roots','fishing_roots','field_move_roots','event_text_roots','battle_script_roots','field_consumer_batch_chain','field_consumer_batch_capacity')}
CODE|={'tests/test_pr16_dex_hof_'+name+'.py' for name in('field_consumer_batch','bag_sort_roots','fishing_roots','field_move_roots','event_text_roots','battle_script_roots','field_consumer_batch_chain','field_consumer_batch_capacity','field_consumer_batch_actions')}
OLDCP=delta.PARENT_CHECKPOINT
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_field_consumer_batch_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_field_consumer_batch_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-field-consumer-batch';PUBLIC=ROOT/'public-dex-hof-field-consumer-batch';ARTIFACT='pr16-dex-hof-field-consumer-batch-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','field-consumer-batch-tests.txt','reference-chain.json','unknown-frontier.json','partial-space.json'}
MAX_FILE=4000000;MAX_TOTAL=12000000
EXPECTED=data.EXPECTED
CATEGORIES=data.EXPECTED_CATEGORIES


def validate_development(development):
 need(development.get('status')=='PASS_NEW_SOURCE_ONLY_FIELD_CONSUMER_BATCH_REVIEW' and
      development.get('review_scope')=='new_field_consumer_batch_sources_only' and
      development.get('old_independent_final_review_retried')is False and
      type(development.get('open_findings'))is list and development['open_findings']==[],
      'exact new-only source review without retrying refused old review')
 bindings=development.get('source_bindings',{})
 need(type(bindings)is dict and set(bindings)==CODE-{DEVELOPMENT},
      'complete exact reviewed source set; no self-attestation or omissions')
 need(prior.bindings(bindings)==bindings,'all reviewed whole source bytes unchanged')


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 development=json.loads((ROOT/DEVELOPMENT).read_bytes());validate_development(development)
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[] and prior.bindings(state['source_bindings'])==state['source_bindings'],'all earlier originals and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']==data.CANDIDATE and cp['classified']==746 and cp['unclassified']==128,'exact inherited746 typed frontier')
 need(cp['baseline_identity']==delta.BASELINE_ID and cp['delta_identity']==delta.PARENT_ID,'whole inherited874 inventory and746 parent');delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS])




def bounded_files(files):
 need(files and sum(len(raw)for raw in files.values())<MAX_TOTAL,'nonempty bounded total publication')
 for name,raw in files.items():
  need(0<len(raw)<MAX_FILE and raw.endswith(b'\n')and b'\0'not in raw and b'\r'not in raw,'complete bounded text '+name);raw.decode('utf8')
  if name.endswith('.json'):json.loads(raw)
 need('reference-chain.json'not in files or len(files['reference-chain.json'])<=delta.MAX_DELTA_BYTES,'bounded shared delta')
 return {name:identity(raw)for name,raw in files.items()}


def capacity_report(full,inherited):
 parents=delta.parent_audits(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]);need(parents['parent_audit']==inherited,'exact common independent parent')
 return space.current_report(full,ROOT,**parents)


def unknown_frontier(full,owners):
 remaining=[dict(hit=h,owners=[o['name']for o in owners.values()if data.d.contains(o['address'],o['address']+o['size'],h['address'],h['size'])])for h in full['hits']if not h['accepted']]
 count=sum(bool(r['owners'])for r in remaining)
 return dict(candidate=data.CANDIDATE,total=len(remaining),owner_unknown=count,unowned_unknown=len(remaining)-count,rows=remaining,donor_eligible=False,indirect_reference_completeness_claimed=False)


def public_sources():
 directory=OUT/'pinned-public-sources';directory.mkdir()
 manifest=json.loads((ROOT/data.SOURCES).read_bytes());lock=json.loads((ROOT/'state/source-lock.json').read_bytes());allowed={r['repository'].removeprefix('https://github.com/').removesuffix('.git'):r for r in lock['sources']}
 need(len({r['local']for r in manifest})==len(manifest),'unique finite public source identities')
 sources={};bindings={};cache={}
 for row in manifest:
  repo,commit,path,name=(row[k]for k in('repository','commit','source','local'));key=repo,commit,path
  need('..'not in path and not path.startswith('/')and '/'not in name and not name.startswith('.'),'closed source path')
  if key in cache:raw=cache[key]
  elif repo=='dekaazarashi1111-web/pokemon-vega-modern':
   need(commit in data.PROJECT_SOURCE_REFS,'one independently read project source ref');f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular project source');raw=f.read_bytes()
  else:
   need(repo in allowed and commit==allowed[repo]['resolved_commit'],'same fixed source-lock upstream')
   existing=ROOT/allowed[repo]['path']/path
   if existing.is_file()and not existing.is_symlink()and identity(existing.read_bytes())=={k:row[k]for k in('size','sha256')}:raw=existing.read_bytes()
   else:
    with urllib.request.urlopen(f'https://raw.githubusercontent.com/{repo}/{commit}/{path}',timeout=90)as response:raw=response.read(row['size']+1)
  need(identity(raw)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha'],'entire fixed public source and Git blob')
  cache[key]=raw;(directory/name).write_bytes(raw);sources[name]=raw
  if 'canonical'in row:sources[row['canonical']]=raw
  bindings[name]={k:row[k]for k in('repository','commit','source','size','sha256','git_blob_sha')}
 return sources,bindings


def run():
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_field_consumer_batch as data_tests
 import test_pr16_dex_hof_event_text_roots as event_tests
 import test_pr16_dex_hof_battle_script_roots as battle_tests
 import test_pr16_dex_hof_bag_sort_roots as bag_tests
 import test_pr16_dex_hof_fishing_roots as fishing_tests
 import test_pr16_dex_hof_field_move_roots as field_tests
 import test_pr16_dex_hof_field_consumer_batch_chain as delta_tests
 import test_pr16_dex_hof_field_consumer_batch_capacity as space_tests
 import test_pr16_dex_hof_field_consumer_batch_actions as action_tests
 prior.current();need(not OUT.exists() and not PUBLIC.exists(),'one fresh field-consumer-batch scope');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  sources,bindings=public_sources()
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==latest['candidate']==data.CANDIDATE,'whole exact current candidate reconstruction')
  owners=data.d.bind_owners(current,latest);need(len(owners)==115,'all115 current actual owner bindings')
  inherited=delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS])
  for hit in inherited['hits']:need(identity(data.d.chunk(current,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'all874 retained hit bytes')
  data_tests.FIXTURE=(current,latest,inherited,sources)
  data.install_fixtures(current,latest,inherited,sources,event_tests,battle_tests,bag_tests,fishing_tests,field_tests)
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in(data_tests,event_tests,battle_tests,bag_tests,fishing_tests,field_tests,delta_tests,space_tests,action_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'field-consumer-batch-tests.txt').write_text(stream.getvalue())
  if not result.wasSuccessful():print(json.dumps(dict(error_code='NEW_SPACE_TEST_FAILURE',tests=[t.id()for t,_ in result.failures+result.errors])))
  need(result.wasSuccessful() and not result.skipped,'all new field-consumer and capacity cases without skipped current tests')
  r1,p1=data.regions(current,latest,inherited,sources)
  r3,p3=song.measured_regions(current,inherited,r1,data.protected_windows());need(not r3,'no repeated discovery from unchanged133 song IDs')
  evidence=delta.build(inherited,r1,dict(data=p1,song=p3,public_source_bindings=bindings));full=delta.materialize(inherited,evidence)
  need(data.d.compare_inventory(full['hits'],inherited)['same_inventory'] and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all874 identities and retained746/remainingunknown rows exact')
  need(all(evidence[k]==EXPECTED[k]for k in('newly_classified','classified','unclassified')),'exact new rooted references')
  write(PUBLIC/'reference-chain.json',evidence);frontier=unknown_frontier(full,owners);write(PUBLIC/'unknown-frontier.json',frontier)
  capacity=capacity_report(full,inherited);write(PUBLIC/'partial-space.json',capacity)
  m=dict(status='PASS_CURRENT_746_PARENT_FIELD_CONSUMER_BATCH_AND_PARTIAL_SPACE_REFUSAL',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
   classified=evidence['classified'],unclassified=evidence['unclassified'],newly_classified=evidence['newly_classified'],new_data=EXPECTED['new_data'],new_code=EXPECTED['new_code'],new_boundary=EXPECTED['new_boundary'],new_song=0,old_inventory_candidates=874,previous_classified=746,previous_unknown=128,owner_unknown=frontier['owner_unknown'],unowned_unknown=frontier['unowned_unknown'],
   all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,delta_identity=identity((PUBLIC/'reference-chain.json').read_bytes()),baseline_identity=delta.BASELINE_ID,parent_identity=delta.PARENT_ID,earlier_identity=delta.EARLIER_ID,unknown_identity=identity((PUBLIC/'unknown-frontier.json').read_bytes()),capacity_identity=identity((PUBLIC/'partial-space.json').read_bytes()),
   source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({*delta.PARENT_INPUTS,LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json',*space.all_input_bindings()}),
   current_owner_count=len(owners),current_rom_reconstructions=reconstructed,historical_rom_reconstructions=0,old_full_rom_scan_runs=0,native_processes=0,accepted_heap_reruns=0,independent_final_source_review_completed=False,new_field_consumer_batch_source_review_completed=True,development_validation=identity((ROOT/DEVELOPMENT).read_bytes()),validation_scope='新scope専用unit、現候補全SHA/115actual owner/874hit/新登録event/battle consumer最小型・field未結合guard・保存容量原本の機械検証。旧最終song/battle/Surf独立再レビュー未実施を保持。',
   combined_song_models=p3['combined_song_models'],retained_sample_witnesses=p3['retained_sample_witnesses'],old_models_reused_for_new_cross_song_role_safety=True,
   donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False,field_consumer_batch_diagnostics=p1)
  write(PUBLIC/'measurement.json',m);bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()})
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc());frames=[dict(source=Path(t.filename).name,function=t.name,line=t.lineno)for t in traceback.extract_tb(exc.__traceback__)if Path(t.filename).parent==ROOT/'scripts']
  print(json.dumps(dict(error_code='FIELD_CONSUMER_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',type=type(exc).__name__,source_frames=frames)))
  write(OUT/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,error_code='FIELD_CONSUMER_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',native_processes=0,current_rom_reconstructions=reconstructed))
  raise RuntimeError('FIELD_CONSUMER_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')from None


def validate_measurement(m):
 need(m['status']=='PASS_CURRENT_746_PARENT_FIELD_CONSUMER_BATCH_AND_PARTIAL_SPACE_REFUSAL' and m['source_head']==os.environ['GITHUB_SHA'] and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact successful source/run measurement')
 expected=dict(current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=746,previous_unknown=128,**EXPECTED)
 need(all(type(m[k])is int and m[k]==v for k,v in expected.items()),'exact bound measurement counters')
 need(m['retained_sample_witnesses']==50,'all original and immediate-parent50 sample witnesses preserved')
 need(m.get('independent_final_source_review_completed')is False and m.get('new_field_consumer_batch_source_review_completed')is True,'exact new-only review and independently unreviewed historical scope')
 need(m.get('development_validation')==identity((ROOT/DEVELOPMENT).read_bytes()),'entire current independently reviewed development envelope')
 need(type(m['unit_tests'])is int and m['unit_tests']>0 and all(m[k]is True for k in('all_prior_accepted_retained','remaining_unknown_rows_retained','old_full_rom_inventory_reused','old_models_reused_for_new_cross_song_role_safety')),'measured retention contracts')


def validate_closed_boundaries(m):
 false_fields=('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed')
 zero_fields=('native_processes','old_full_rom_scan_runs','accepted_heap_reruns','historical_rom_reconstructions')
 need(all(m.get(k)is False for k in false_fields),'all unproved runtime/lease claims are explicit boolean false')
 need(all(type(m.get(k))is int and m[k]==0 for k in zero_fields),'all unperformed execution counters are integer zero')
 return True


def validate_record(m,raw,inherited):
 evidence=delta.read_measured(raw,m['delta_identity'],inherited);validate_measurement(m)
 need(collections.Counter(row['classification']for row in evidence['changes'])==CATEGORIES,'exact independently measured rooted category counts')
 full=delta.materialize(inherited,evidence)
 need(m['field_consumer_batch_diagnostics']==evidence['proof']['data'],'same complete measured finite consumer diagnostics')
 need(m['candidate']==evidence['candidate']==inherited['candidate']==data.CANDIDATE,'record same whole candidate')
 for key in('classified','unclassified','newly_classified'):need(m[key]==evidence[key],'record exact additive counters')
 need(all(full[k]==inherited[k]for k in delta.INHERITED_NAMES),'all fifteen old delta families and witnesses exactly retained')
 validate_closed_boundaries(m)
 need(all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'record keeps prior accepted and remaining unknown exact')
 return evidence


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'all earlier originals and unique new checkpoint')
 inherited=delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]);m=json.loads((PUBLIC/'measurement.json').read_bytes());evidence=validate_record(m,(PUBLIC/'reference-chain.json').read_bytes(),inherited);full=delta.materialize(inherited,evidence)
 owners={o['name']:o for o in json.loads((ROOT/LATEST).read_bytes())['placement']['owner_byte_audit']}
 frontier_raw=(PUBLIC/'unknown-frontier.json').read_bytes();capacity_raw=(PUBLIC/'partial-space.json').read_bytes()
 need(identity(frontier_raw)==m['unknown_identity'] and json.loads(frontier_raw)==unknown_frontier(full,owners),'complete remaining unknown inventory and actual owner join')
 need(identity(capacity_raw)==m['capacity_identity'] and json.loads(capacity_raw)==capacity_report(full,inherited),'whole source-bound partial-space contract')
 need(m['source_bindings']==prior.bindings(CODE) and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'whole measured source and inherited artifacts unchanged')
 paths=set()
 for name in sorted(PROOF):
  p=EVIDENCE+'/'+name;need(not(ROOT/p).exists(),'one immutable new text evidence');(ROOT/p).parent.mkdir(parents=True,exist_ok=True);(ROOT/p).write_bytes((PUBLIC/name).read_bytes());paths.add(p)
 cp=dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),previous_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),reference_baseline=delta.BASELINE,reference_parent=delta.PARENT)
 write(ROOT/CP,cp)
 summary=f'現0641のBag数量順2件・Fishing timeout・追加field-move説明の計4hitに新producer guardを実装。同4hitは実producerから未到達またはconsumer未接続のため未知維持。別の現map登録event text1件とeffect231登録battle script2件の最小4byteを各分類し、新分類{m["newly_classified"]}、{m["classified"]}分類/未知{m["unclassified"]}を保持。新{m["unit_tests"]}試験、全115actual ownerと全15親deltaを照合。有限producerだけの否定証拠であり全caller/全writerの不在や普遍未到達は主張しない。全egg15118byte保護/安全容量0、正式ROM/Save101/donor不変。'
 goal=f'残{m["unclassified"]}件を実consumer根から調べる。Bag数量順ID14/15は実生成配列から除外、Fishingは実state6→9でstate7 timeout producerへ進まず、追加Defog/Dive説明は実stock consumerが旧表のまま。各4hitは未知維持し、別の実caller/非zero writerまたはconsumer結合の独立証拠が出た時だけ再開。Credits4paddingの日本語layout、GPU外側root、wireless非zero writerも未証明。次は残未調査の実UI/script/asset登録根を限定調査する。既測定Bag/ShockWave/Seagallop/Help/RFU/Fame/Credits/Summary/party/Mystery/本event/battle最小型/field guard/旧suite/nativeは無影響再走しない。未知最大access/間接参照/退役/owner移管未証明なら旧egg15118全域保護/安全0。単一controller6528byte容量確保後、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL/全mode/早期31/species9bit、全保存入口heap-ready/同期非再入/0804B85C退避前Freeへ接続。正式切替後trainer131後半→シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_field_consumer_batch']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']),classified=m['classified'],unclassified=m['unclassified'],unit_tests=m['unit_tests'],consumer_diagnostics=dict(path=EVIDENCE+'/measurement.json',proof_identity=identity(data.canonical(m['field_consumer_batch_diagnostics'])),complete_diagnostics_retained=True),donor_safe_bytes=0,known_capacity_upper_bound=1315,controller_measured_bytes=6528,donor_leased=False,controller_runtime_wired=False)
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_ROOTS_AND_BOUND_PARTIAL_DONOR_SPACE',goal_ja=goal,read_paths=[GUIDE,CP,*delta.PARENT_INPUTS,'scripts/pr16_dex_hof_callback_capacity.py','scripts/pr16_dex_hof_partial_space.py',LATEST,*data.REVIEWS])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='全746親証拠保持、新登録event/battle最小型とfield未結合guard測定source。残root/donor/本番配線未受入。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'新scopeの有限producer guardを全caller/全writer未到達と分離。普遍runtime寿命保証や自然到達を未完のまま保持。全親changes25/17/33/29/3/2/1/0/3/1/2/2/4/2/3、witness22/16/33/23/3/2/1/0/3/1/2/2/4/2/3、133曲/50assetを保持。未知word size4を参照先のread幅へ誤用しない。無影響heap/native再走禁止。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],reference_unit_tests=m['unit_tests'],classified=m['classified'],unclassified=m['unclassified'],native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261006-DEX-HOF-FIELD-CONSUMER-BATCH / 登録field consumer最小型・未結合guard・容量保持\n- Version: hof-field-consumer-batch-v1\n- Status: STOPPED（新3type/4hit誤採用防止guard、残root/donor/実controller未完）\n- Summary: {summary}\n- Files changed: 新consumer verifier/chain/capacity/拒否unit/Actions/guide/checkpoint/最小証拠、固定MDJSON、両ログ。\n- Verify: 新unit{m["unit_tests"]}、現candidate全SHA・115actual owner・874hit、全15親delta/全127changes/全117witness/旧746と残unknown全field保持、133全song model/50assetと新typed窓の役割交差。旧全ROMscan/native/heap/歴史再生成0。\n- Capacity: 未知参照はアクセス幅未証明なら全donor保護。点target楽観空隙を安全容量へ昇格しない。global余白511とsave内部804は既存owner/subownerを保持した上限で、新leaseなし。Ccontroller既測定単一text6528/align4と比較。間接参照/対象退役完全性も別必須gate。\n- Publication: 619原本と全親chainは参照保持、複製なし。独立measurementと全text size/SHA/LF、closed success artifact、hidden/symlink/未知file拒否。旧独立最終song/battle/Surfレビュー未実施を継承し、拒否操作の別経路再実行なし。\n- Boundary: 現0641/115owner/52saveowner/残804、正式ROM/Save101不変。heap13352を保存退避53300入口へ跨いで保持しない。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存入力/固定source。公開source・最小address-size-SHA・textのみ、ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'earlier originals preserved')
 # 同じ実snapshot bytesをcommit前に上限検査。upload直前の初回発見を避ける。
 planned={name:(PUBLIC/name).read_bytes()for name in PROOF};planned.update({name:(ROOT/path).read_bytes()for name,path in SNAPSHOTS});bounded_files(planned)
 receipt=dict(status='PASS_RECORDED_REFERENCE_CHAIN',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0,precommit_publication_files=bounded_files(planned))
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
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261006-DEX-HOF-FIELD-CONSUMER-BATCH VERIFY=PASS COMMIT='+receipt['final_head'])
def validate_export(files,head):
 expected=PROOF|{'record.json',*(name for name,_ in SNAPSHOTS)}
 need(set(files)==expected,'complete success artifact, never partial measurement or snapshot')
 bounded_files(files);receipt=json.loads(files['record.json'])
 need(receipt.get('final_head')==head and len(head)==40 and receipt.get('status')=='PASS_RECORDED_REFERENCE_CHAIN','completed chain snapshot receipt and current commit')
 planned=receipt['precommit_publication_files'];need(set(planned)==expected-{'record.json'},'all proof and snapshot files bound before commit')
 for name,binding in planned.items():need(identity(files[name])==binding,'complete exact recorded file '+name)
 proofs=receipt.get('final_blobs',{});need(set(proofs)=={path for _,path in SNAPSHOTS},'all final snapshot receipts')
 for name,path in SNAPSHOTS:
  raw=files[name];binding=proofs[path]
  need(binding.get('trailing_newline')is True and raw.endswith(b'\n')and identity(raw)=={k:binding[k]for k in('size','sha256')},'complete committed final snapshot identity')
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'exact final Git blob content')
 measure=json.loads(files['measurement.json']);need(measure['delta_identity']==identity(files['reference-chain.json']) and measure['capacity_identity']==identity(files['partial-space.json']),'independent measured complete chain envelope')
 need(measure['source_head']==receipt['source_head']and measure['run_id']==receipt['record_run'],'same source and run measurement')
 return True

def export():
 publication.output(PUBLIC,success='record.json',failure=None)
 files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in PROOF|{'record.json',*(n for n,_ in SNAPSHOTS)},'closed regular nonhidden success text publication')
  files[path.name]=path.read_bytes()
 head=git('rev-parse','HEAD').decode().strip()
 validate_export(files,head)
 receipt=json.loads(files['record.json'])
 for name,path in SNAPSHOTS:
  need(git('show',head+':'+path)==files[name],'upload snapshot equals independent committed blob')
  need(git('rev-parse',head+':'+path).decode().strip()==receipt['final_blobs'][path]['git_blob_sha'],'upload snapshot exact committed Git identity')
 for name in PROOF:
  need(git('show',head+':'+EVIDENCE+'/'+name)==files[name],'upload proof equals immutable committed measurement')

if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed reference workflow');globals()[sys.argv[1]]()
