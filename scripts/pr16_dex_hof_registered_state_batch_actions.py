#!/usr/bin/env python3
"""親deltaを全文固定し、残参照の新根だけ測定・記録する。"""
import collections,datetime,hashlib,io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_registered_state_batch as data
import pr16_dex_hof_consumer_song as song
import pr16_dex_hof_registered_state_batch_capacity as space
import pr16_dex_hof_registered_state_batch_chain as delta
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='b9be8c6c231df0aac1c5eb163b154a4ec8ff5787'
WF='.github/workflows/pr16-dex-hof-registered-state-batch.yml';SELF='scripts/pr16_dex_hof_registered_state_batch_actions.py';GUIDE='docs/PR16_DEX_HOF_REGISTERED_STATE_BATCH_JA.md'
DEVELOPMENT='content/modernization/pr16_dex_hof_registered_state_batch_development_validation.json'
CODE={WF,SELF,GUIDE,data.SOURCES,data.CONTRACT,DEVELOPMENT,*data.REVIEWS}
CODE|={'scripts/pr16_dex_hof_'+name+'.py' for name in('registered_state_batch','dancer_roots','money_reward_roots','registered_state_batch_chain','registered_state_batch_capacity')}
CODE|={'tests/test_pr16_dex_hof_'+name+'.py' for name in('registered_state_batch','dancer_roots','money_reward_roots','registered_state_batch_chain','registered_state_batch_capacity','registered_state_batch_actions')}
OLDCP=delta.PARENT_CHECKPOINT
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_registered_state_batch_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_registered_state_batch_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-registered-state-batch';PUBLIC=ROOT/'public-dex-hof-registered-state-batch';ARTIFACT='pr16-dex-hof-registered-state-batch-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','registered-state-batch-tests.txt','reference-chain.json','unknown-frontier.json','partial-space.json'}
MAX_FILE=4000000;MAX_TOTAL=12000000
EXPECTED=data.EXPECTED
CATEGORIES=data.EXPECTED_CATEGORIES


INHERITED={*delta.PARENT_INPUTS,LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json',*space.all_input_bindings()}
MEASUREMENT_FIELDS=frozenset(('accepted_heap_reruns', 'all_prior_accepted_retained', 'baseline_identity', 'candidate', 'candidate_changed', 'capacity_identity', 'classified', 'combined_song_models', 'controller_runtime_wired', 'current_owner_count', 'current_rom_reconstructions', 'delta_identity', 'development_validation', 'donor_eligible', 'donor_leased', 'earlier_identity', 'formal_rom_changed', 'formal_save_changed', 'historical_rom_reconstructions', 'independent_final_source_review_completed', 'indirect_reference_completeness_claimed', 'inherited_bindings', 'native_processes', 'new_boundary', 'new_code', 'new_data', 'new_registered_state_batch_source_review_completed', 'new_song', 'newly_classified', 'old_full_rom_inventory_reused', 'old_full_rom_scan_runs', 'old_inventory_candidates', 'old_models_reused_for_new_cross_song_role_safety', 'owner_unknown', 'parent_identity', 'previous_classified', 'previous_unknown', 'registered_state_batch_diagnostics', 'remaining_unknown_rows_retained', 'retained_sample_witnesses', 'run_id', 'source_bindings', 'source_head', 'status', 'unclassified', 'unit_tests', 'unknown_identity', 'unowned_unknown', 'validation_scope'))
def validate_binding_map(value, expected_paths):
 need(type(value)is dict and set(value)==set(expected_paths) and bool(value),
      'complete independent exact source binding set')
 need(all(delta.valid_identity(binding)and binding['size']>0 for binding in value.values()),
      'all source identities have closed positive integer size and exact SHA')
 return True

def validate_registry():
 data.require_contract()
 expected={c['kind']:c['module']for c in data.CONSUMER_SPECS}
 need(type(delta.NEW_KIND_MODULES)is dict and data.canonical(delta.NEW_KIND_MODULES)==data.canonical(expected),'entire exact dedicated chain registry matches frozen contract')
 return True

def validate_development(development):
 need(type(development)is dict,'closed development mapping')
 need(development.get('status')=='PASS_NEW_SOURCE_ONLY_REGISTERED_STATE_BATCH_REVIEW' and
      development.get('review_scope')=='new_registered_state_batch_sources_only' and
      development.get('old_independent_final_review_retried')is False and
      type(development.get('open_findings'))is list and development['open_findings']==[],
      'exact new-only source review without retrying refused old review')
 bindings=development.get('source_bindings',{})
 need(type(bindings)is dict and set(bindings)==CODE-{DEVELOPMENT},
      'complete exact reviewed source set; no self-attestation or omissions')
 validate_binding_map(bindings,CODE-{DEVELOPMENT})
 need(data.canonical(prior.bindings(CODE-{DEVELOPMENT}))==data.canonical(bindings),'all reviewed whole source bytes unchanged')


def validate_source_manifest(manifest,lock):
 import re
 keys={'repository','commit','source','local','size','sha256','git_blob_sha','url'}
 expected={}
 for module,_ in data.ALL_MODULES:
  need(type(module.SOURCE_IDS)is dict and bool(module.SOURCE_IDS),'nonempty independent consumer source IDs')
  for key,row in module.SOURCE_IDS.items():
   need(type(row)is dict and row.get('local')==key,'exact consumer source local key')
   need(key not in expected or expected[key]==row,'shared consumer source whole metadata agrees')
   expected[key]=row
 need(type(manifest)is list and bool(manifest),'nonempty complete public source manifest')
 allowed={r['repository'].removeprefix('https://github.com/').removesuffix('.git'):r['resolved_commit'] for r in lock['sources']}
 found={}
 for row in manifest:
  need(type(row)is dict and set(row)==keys,'closed source manifest schema; no undeclared aliases')
  need(all(type(row[k])is str and row[k]for k in keys-{'size'}),'nonempty source identity strings')
  need(type(row['size'])is int and row['size']>0,'positive exact source byte count')
  need(re.fullmatch('[0-9a-f]{40}',row['commit'])is not None and re.fullmatch('[0-9a-f]{40}',row['git_blob_sha'])is not None and re.fullmatch('[0-9a-f]{64}',row['sha256'])is not None,'exact source hashes')
  repo,commit,path,key=(row[k]for k in ('repository','commit','source','local'))
  need('..'not in path and not path.startswith('/')and '/'not in key and not key.startswith('.')and key not in found,'closed unique public source paths')
  if repo=='dekaazarashi1111-web/pokemon-vega-modern':need(commit in data.PROJECT_SOURCE_REFS,'fixed independently read project source')
  else:need(repo in allowed and commit==allowed[repo],'fixed source-lock public upstream')
  need(row['url']==f'https://github.com/{repo}/blob/{commit}/{path}','exact public source URL')
  found[key]=row
 need(found==expected,'all and only independently bound consumer source metadata')
 return True


def validate_source_inputs():
 validate_registry()
 # ROM再構成の前に未完review/manifestを拒否。外部取得は行わない。
 for _,path in data.ALL_MODULES:data.read_review(path)
 path=ROOT/data.SOURCES
 need(path.is_file()and not path.is_symlink(),'regular independently fixed source manifest')
 raw=path.read_bytes();need(raw and raw.endswith(b'\n')and b'\r'not in raw and b'\0'not in raw,'complete source manifest LF bytes')
 manifest=json.loads(raw)
 validate_source_manifest(manifest,json.loads((ROOT/'state/source-lock.json').read_bytes()))
 return manifest


def source_guard():
 validate_registry()
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 development=json.loads((ROOT/DEVELOPMENT).read_bytes());validate_development(development);validate_source_inputs()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[] and prior.bindings(state['source_bindings'])==state['source_bindings'],'all earlier originals and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']==data.CANDIDATE and cp['classified']==774 and cp['unclassified']==100,'exact inherited774 typed frontier')
 need(cp['baseline_identity']==delta.BASELINE_ID and cp['delta_identity']==delta.PARENT_ID,'whole inherited874 inventory and774 parent');delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS])




def bounded_files(files):
 need(type(files)is dict,'closed publication mapping')
 allowed=PROOF|{'record.json','closeout.json',*(name for name,_ in SNAPSHOTS)}
 need(all(type(name)is str and name in allowed and '/'not in name and not name.startswith('.')and name.endswith(('.json','.txt','.md'))and type(raw)is bytes for name,raw in files.items()),'only declared flat text names and exact bytes')
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
 validate_registry();validate_development(json.loads((ROOT/DEVELOPMENT).read_bytes()));validate_source_inputs()
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_registered_state_batch as data_tests
 import test_pr16_dex_hof_dancer_roots as consumer_test_0
 import test_pr16_dex_hof_money_reward_roots as consumer_test_1
 import test_pr16_dex_hof_registered_state_batch_chain as delta_tests
 import test_pr16_dex_hof_registered_state_batch_capacity as space_tests
 import test_pr16_dex_hof_registered_state_batch_actions as action_tests
 prior.current();need(not OUT.exists() and not PUBLIC.exists(),'one fresh registered-state-batch scope');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  sources,bindings=public_sources()
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==latest['candidate']==data.CANDIDATE,'whole exact current candidate reconstruction')
  owners=data.d.bind_owners(current,latest);need(len(owners)==115,'all115 current actual owner bindings')
  inherited=delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS])
  for hit in inherited['hits']:need(identity(data.d.chunk(current,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'all874 retained hit bytes')
  data_tests.FIXTURE=(current,latest,inherited,sources)
  data.install_fixtures(current,latest,inherited,sources,consumer_test_0,consumer_test_1)
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in(data_tests,consumer_test_0,consumer_test_1,delta_tests,space_tests,action_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'registered-state-batch-tests.txt').write_text(stream.getvalue())
  if not result.wasSuccessful():print(json.dumps(dict(error_code='NEW_SPACE_TEST_FAILURE',tests=[t.id()for t,_ in result.failures+result.errors])))
  need(result.wasSuccessful() and not result.skipped,'all new registered state consumer and capacity cases without skipped current tests')
  r1,p1=data.regions(current,latest,inherited,sources)
  r3,p3=song.measured_regions(current,inherited,r1,data.protected_windows());need(not r3,'no repeated discovery from unchanged133 song IDs')
  evidence=delta.build(inherited,r1,dict(data=p1,song=p3,public_source_bindings=bindings));full=delta.materialize(inherited,evidence)
  need(data.d.compare_inventory(full['hits'],inherited)['same_inventory'] and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all874 identities and retained774/remainingunknown rows exact')
  need(all(evidence[k]==EXPECTED[k]for k in('newly_classified','classified','unclassified')),'exact new rooted references')
  write(PUBLIC/'reference-chain.json',evidence);frontier=unknown_frontier(full,owners);write(PUBLIC/'unknown-frontier.json',frontier)
  capacity=capacity_report(full,inherited);write(PUBLIC/'partial-space.json',capacity)
  m=dict(status='PASS_CURRENT_774_PARENT_REGISTERED_STATE_BATCH_AND_PARTIAL_SPACE_REFUSAL',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
   classified=evidence['classified'],unclassified=evidence['unclassified'],newly_classified=evidence['newly_classified'],new_data=EXPECTED['new_data'],new_code=EXPECTED['new_code'],new_boundary=EXPECTED['new_boundary'],new_song=0,old_inventory_candidates=874,previous_classified=774,previous_unknown=100,owner_unknown=frontier['owner_unknown'],unowned_unknown=frontier['unowned_unknown'],
   all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,delta_identity=identity((PUBLIC/'reference-chain.json').read_bytes()),baseline_identity=delta.BASELINE_ID,parent_identity=delta.PARENT_ID,earlier_identity=delta.EARLIER_ID,unknown_identity=identity((PUBLIC/'unknown-frontier.json').read_bytes()),capacity_identity=identity((PUBLIC/'partial-space.json').read_bytes()),
   source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings(INHERITED),
   current_owner_count=len(owners),current_rom_reconstructions=reconstructed,historical_rom_reconstructions=0,old_full_rom_scan_runs=0,native_processes=0,accepted_heap_reruns=0,independent_final_source_review_completed=False,new_registered_state_batch_source_review_completed=True,development_validation=identity((ROOT/DEVELOPMENT).read_bytes()),validation_scope='新scope専用unit、現候補全SHA/115actual owner/874hit/新consumerの独立source symbol/struct・実登録caller/state dispatch・完全prologue・2path実fetch和とopaque ABI/future-live/epoch条件の最小Thumb型・保存容量原本の機械検証。旧最終song/battle/Surf独立再レビュー未実施を保持。',
   combined_song_models=p3['combined_song_models'],retained_sample_witnesses=p3['retained_sample_witnesses'],old_models_reused_for_new_cross_song_role_safety=True,
   donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False,registered_state_batch_diagnostics=p1)
  write(PUBLIC/'measurement.json',m);bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()})
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc());frames=[dict(source=Path(t.filename).name,function=t.name,line=t.lineno)for t in traceback.extract_tb(exc.__traceback__)if Path(t.filename).parent==ROOT/'scripts']
  print(json.dumps(dict(error_code='REGISTERED_STATE_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',type=type(exc).__name__,source_frames=frames)))
  write(OUT/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,error_code='REGISTERED_STATE_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',native_processes=0,current_rom_reconstructions=reconstructed))
  raise RuntimeError('REGISTERED_STATE_BATCH_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')from None


def validate_measurement(m):
 need(type(m)is dict and set(m)==MEASUREMENT_FIELDS,'complete closed independently declared measurement fields')
 need(type(m['run_id'])is int and m['run_id']>0 and type(m['source_head'])is str and len(m['source_head'])==40 and all(c in '0123456789abcdef'for c in m['source_head']),'strict positive run and full source SHA')
 need(type(m['retained_sample_witnesses'])is int and m['retained_sample_witnesses']==50,'strict retained sample witness count')
 for key in('candidate','delta_identity','baseline_identity','parent_identity','earlier_identity','unknown_identity','capacity_identity','development_validation'):
  need(delta.valid_identity(m[key])and m[key]['size']>0,'strict complete nonempty measurement identity '+key)
 validate_binding_map(m['source_bindings'],CODE);validate_binding_map(m['inherited_bindings'],INHERITED)
 need(data.canonical(m['candidate'])==data.canonical(data.CANDIDATE)and data.canonical(m['baseline_identity'])==data.canonical(delta.BASELINE_ID)and data.canonical(m['parent_identity'])==data.canonical(delta.PARENT_ID)and data.canonical(m['earlier_identity'])==data.canonical(delta.EARLIER_ID),'exact independent candidate and lineage identities')
 need(type(m['validation_scope'])is str and bool(m['validation_scope'])and type(m['registered_state_batch_diagnostics'])is dict and bool(m['registered_state_batch_diagnostics']),'complete diagnostic and scope mappings')
 validate_closed_boundaries(m)
 need(m['status']=='PASS_CURRENT_774_PARENT_REGISTERED_STATE_BATCH_AND_PARTIAL_SPACE_REFUSAL' and m['source_head']==os.environ['GITHUB_SHA'] and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact successful source/run measurement')
 expected=dict(current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=774,previous_unknown=100,**EXPECTED)
 need(all(type(m[k])is int and m[k]==v for k,v in expected.items()),'exact bound measurement counters')
 need(m['retained_sample_witnesses']==50,'all original and immediate-parent50 sample witnesses preserved')
 need(m.get('independent_final_source_review_completed')is False and m.get('new_registered_state_batch_source_review_completed')is True,'exact new-only review and independently unreviewed historical scope')
 need(data.canonical(m.get('development_validation'))==data.canonical(identity((ROOT/DEVELOPMENT).read_bytes())),'entire current independently reviewed development envelope')
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
 need(data.canonical(m['registered_state_batch_diagnostics'])==data.canonical(evidence['proof']['data']),'same complete measured finite consumer diagnostics')
 need(data.canonical(m['candidate'])==data.canonical(evidence['candidate'])==data.canonical(inherited['candidate'])==data.canonical(data.CANDIDATE),'record same whole candidate')
 for key in('classified','unclassified','newly_classified'):need(m[key]==evidence[key],'record exact additive counters')
 need(all(full[k]==inherited[k]for k in delta.INHERITED_NAMES),'all twenty-four old delta families and witnesses exactly retained')
 validate_closed_boundaries(m)
 need(all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'record keeps prior accepted and remaining unknown exact')
 return evidence


def record():
 data.require_contract()
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'all earlier originals and unique new checkpoint')
 inherited=delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]);m=json.loads((PUBLIC/'measurement.json').read_bytes());evidence=validate_record(m,(PUBLIC/'reference-chain.json').read_bytes(),inherited);full=delta.materialize(inherited,evidence)
 owners={o['name']:o for o in json.loads((ROOT/LATEST).read_bytes())['placement']['owner_byte_audit']}
 frontier_raw=(PUBLIC/'unknown-frontier.json').read_bytes();capacity_raw=(PUBLIC/'partial-space.json').read_bytes()
 need(identity(frontier_raw)==m['unknown_identity'] and data.canonical(json.loads(frontier_raw))==data.canonical(unknown_frontier(full,owners)),'complete remaining unknown inventory and actual owner join')
 need(identity(capacity_raw)==m['capacity_identity'] and data.canonical(json.loads(capacity_raw))==data.canonical(capacity_report(full,inherited)),'whole source-bound partial-space contract')
 validate_binding_map(m['source_bindings'],CODE);validate_binding_map(m['inherited_bindings'],INHERITED)
 need(data.canonical(m['source_bindings'])==data.canonical(prior.bindings(CODE)) and data.canonical(m['inherited_bindings'])==data.canonical(prior.bindings(INHERITED)),'whole independent measured source and inherited artifacts unchanged')
 paths=set()
 for name in sorted(PROOF):
  p=EVIDENCE+'/'+name;need(not(ROOT/p).exists(),'one immutable new text evidence');(ROOT/p).parent.mkdir(parents=True,exist_ok=True);(ROOT/p).write_bytes((PUBLIC/name).read_bytes());paths.add(p)
 cp=dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),previous_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),reference_baseline=delta.BASELINE,reference_parent=delta.PARENT)
 write(ROOT/CP,cp)
 summary=f'{data.ACCEPTANCE_SUMMARY} 新{m["newly_classified"]}件・最小計{data.MINIMUM_BYTES}byte。{m["classified"]}分類/未知{m["unclassified"]}。全774親・47入力・24namespace155changes145witnessと133曲50assetを保持。新scopeの最小型と自然全play/IRQ/heap/間接完全性/退役/owner移管を分離し、egg15118保護・安全0・正式ROM/Save101不変。' 
 goal=data.NEXT_GOAL
 state['story_dex_owner']['runtime_integration']['hof_registered_state_batch']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']),classified=m['classified'],unclassified=m['unclassified'],unit_tests=m['unit_tests'],consumer_diagnostics=dict(path=EVIDENCE+'/measurement.json',proof_identity=identity(data.canonical(m['registered_state_batch_diagnostics'])),complete_diagnostics_retained=True),donor_safe_bytes=0,known_capacity_upper_bound=1315,controller_measured_bytes=6528,donor_leased=False,controller_runtime_wired=False)
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_ROOTS_AND_BOUND_PARTIAL_DONOR_SPACE',goal_ja=goal,read_paths=[GUIDE,CP,*delta.PARENT_INPUTS,'scripts/pr16_dex_hof_callback_capacity.py','scripts/pr16_dex_hof_partial_space.py',LATEST,*data.REVIEWS])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='全774親証拠保持、新登録state consumer最小型測定source。残root/donor/本番配線未受入。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'新scopeの必要最小型と自然play全到達を分離。既guardの単一producer不達を全caller/全writer不達へ一般化しない。普遍runtime寿命保証や自然到達を未完のまま保持。全親changes25/17/33/29/3/2/1/0/3/1/2/2/4/2/3/3/2/2/3/5/2/3/5/3、witness22/16/33/23/3/2/1/0/3/1/2/2/4/2/3/3/2/2/3/5/2/3/5/3、133曲/50assetを保持。未知word size4を参照先のread幅へ誤用しない。無影響heap/native再走禁止。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],reference_unit_tests=m['unit_tests'],classified=m['classified'],unclassified=m['unclassified'],native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261006-DEX-HOF-REGISTERED-STATE-BATCH / 登録state consumer最小型・容量保持\n- Version: hof-registered-state-batch-v1\n- Status: STOPPED（新登録state consumer必要最小型、既event1hitと旧field4hit未知保持、残root/donor/実controller未完）\n- Summary: {summary}\n- Files changed: 新consumer verifier/chain/capacity/拒否unit/Actions/guide/checkpoint/最小証拠、固定MDJSON、両ログ。\n- Verify: 新unit{m["unit_tests"]}、現candidate全SHA・115actual owner・874hit、全24親delta/全155changes/全145witness/旧774と残unknown全field保持、133全song model/50assetと新typed窓の役割交差。旧全ROMscan/native/heap/歴史再生成0。\n- Capacity: 未知参照はアクセス幅未証明なら全donor保護。点target楽観空隙を安全容量へ昇格しない。global余白511とsave内部804は既存owner/subownerを保持した上限で、新leaseなし。Ccontroller既測定単一text6528/align4と比較。間接参照/対象退役完全性も別必須gate。\n- Publication: 保存済み全原本と全親chainは参照保持、複製なし。独立measurementと全text size/SHA/LF、closed success artifact、hidden/symlink/未知file拒否。旧独立最終song/battle/Surfレビュー未実施を継承し、拒否操作の別経路再実行なし。\n- Boundary: 現0641/115owner/52saveowner/残804、正式ROM/Save101不変。heap13352を保存退避53300入口へ跨いで保持しない。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存入力/固定source。公開source・最小address-size-SHA・textのみ、ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。\n'
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
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261006-DEX-HOF-REGISTERED-STATE-BATCH VERIFY=PASS COMMIT='+receipt['final_head'])
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
 # 全receipt本文をcommitted measurement/proof/snapshotから独立再構築する。
 expected_receipt=dict(status='PASS_RECORDED_REFERENCE_CHAIN',source_head=measure['source_head'],
  record_run=measure['run_id'],native_processes=0,
  precommit_publication_files={name:identity(files[name])for name in expected-{'record.json'}},
  final_head=head,final_blobs={path:dict(**identity(files[name]),
   git_blob_sha=hashlib.sha1(b'blob '+str(len(files[name])).encode()+b'\0'+files[name]).hexdigest(),
   trailing_newline=True)for name,path in SNAPSHOTS})
 need(data.canonical(receipt)==data.canonical(expected_receipt),
      'entire closed receipt equals independently bound committed measurement and snapshots')
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
