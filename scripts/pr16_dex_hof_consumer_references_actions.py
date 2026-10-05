#!/usr/bin/env python3
"""親deltaを全文固定し、残参照の新根だけ測定・記録する。"""
import collections,datetime,hashlib,io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_song_actions as song_actions
import pr16_dex_hof_consumer_references as data
import pr16_dex_hof_consumer_song as song
import pr16_dex_hof_consumer_chain as delta
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='ab334cc56e302793ea53575695f769675e474161'
WF='.github/workflows/pr16-dex-hof-consumer-references.yml';SELF='scripts/pr16_dex_hof_consumer_references_actions.py';GUIDE='docs/PR16_DEX_HOF_CONSUMER_REFERENCES_JA.md'
CODE={WF,SELF,GUIDE,data.SOURCES,*data.REVIEWS,data.HISTORY_CP,'content/modernization/pr16_dex_hof_consumer_audio_negative.json'}
CODE|={data.HISTORY+'/'+n for n in('historical.json','host-tests.txt','receipt.json')}
CODE|={'scripts/pr16_dex_hof_'+name+'.py'for name in('consumer_references','consumer_song','consumer_chain','consumer_palette','consumer_engine','battle_continuation')}
CODE|={'tests/test_pr16_dex_hof_'+name+'.py'for name in('consumer_references','consumer_song','consumer_chain','consumer_palette','consumer_engine','battle_continuation','consumer_references_actions')}
HISTORY_WF='.github/workflows/pr16-dex-hof-tutor-history.yml'
CODE|={HISTORY_WF,'scripts/pr16_dex_hof_tutor_history_actions.py','scripts/pr16_dex_hof_consumer_tutor.py','tests/test_pr16_dex_hof_consumer_tutor.py','docs/PR16_DEX_HOF_TUTOR_HISTORY_JA.md'}
OLDCP=delta.PARENT_CHECKPOINT
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_consumer_references_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_consumer_references_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-consumer-references';PUBLIC=ROOT/'public-dex-hof-consumer-references';ARTIFACT='pr16-dex-hof-consumer-references-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','consumer-references-tests.txt','reference-chain.json','unknown-frontier.json'}
MAX_FILE=4000000;MAX_TOTAL=12000000
EXPECTED=dict(new_data=2,new_code=1,new_song=0,newly_classified=3,classified=726,unclassified=148,owner_unknown=0,unowned_unknown=148,combined_song_models=133)
CATEGORIES={'FALSE_POSITIVE_TYPED_REFERENCE_HISTORICAL_DPE_PALETTE_POINTER_TAG_CROSS_FIELD':1,'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_THUMB_INSTRUCTION_STREAM':1,'FALSE_POSITIVE_TYPED_REFERENCE_HISTORICAL_T09_TUTOR_NUMERIC_MASK':1}


def history_terminal():
 import pr16_story_live_probe as t
 cp=json.loads((ROOT/data.HISTORY_CP).read_bytes());proof=data.historical_proof();receipt=json.loads((ROOT/data.HISTORY/'receipt.json').read_bytes())
 run=t.api('actions/runs/'+str(cp['run_id']));job=t.api('actions/jobs/'+str(cp['job_id']));asset=t.api('actions/artifacts/'+str(cp['artifact']['id']))
 need(run['head_sha']==cp['source_head']==BASE and run['status']=='completed'and run['conclusion']=='success'and run['run_attempt']==1 and job['run_id']==cp['run_id']and len(job['steps'])==8 and all(x['conclusion']=='success'for x in job['steps']),'all8 exact independent historical input steps terminal')
 publication.consumer(asset,cp['artifact']['name'],cp['run_id']);need(asset['size_in_bytes']==cp['artifact']['size']and asset['digest']=='sha256:'+cp['artifact']['sha256'],'exact whole historical public archive identity')
 for path,binding in receipt['source_bindings'].items():
  original=git('show',BASE+':'+path);need(identity(original)==binding,'whole originally measured historical source')
  if path==HISTORY_WF:
   trigger=('  push:\n    branches: [codex/modernization-followup-20260908]\n    paths: ['+HISTORY_WF+']\n').encode()
   need(original.count(trigger)==1 and(ROOT/path).read_bytes()==original.replace(trigger,b'  workflow_dispatch:\n'),'retire only completed history trigger')
  else:need((ROOT/path).read_bytes()==original,'unchanged measured historical code and tests')
 return cp



def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all earlier originals and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']==data.CANDIDATE and cp['classified']==723 and cp['unclassified']==151,'exact inherited723 typed frontier')
 need(cp['baseline_identity']==delta.BASELINE_ID and cp['delta_identity']==delta.PARENT_ID,'whole inherited874 inventory and723 parent');delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]);history_terminal()



def bounded_files(files):
 need(files and sum(len(raw)for raw in files.values())<MAX_TOTAL,'nonempty bounded total publication')
 for name,raw in files.items():
  need(0<len(raw)<MAX_FILE and raw.endswith(b'\n')and b'\0'not in raw,'complete bounded text '+name);raw.decode('utf8')
  if name.endswith('.json'):json.loads(raw)
 need('reference-chain.json'not in files or len(files['reference-chain.json'])<=delta.MAX_DELTA_BYTES,'bounded shared delta')
 return {name:identity(raw)for name,raw in files.items()}


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
   need(commit=='afa090a1d28aa3776bc1f7c9875051cbbaa16439','one independently read project source ref');f=ROOT/path;need(f.is_file()and not f.is_symlink(),'regular project source');raw=f.read_bytes()
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
 import test_pr16_dex_hof_consumer_references as data_tests
 import test_pr16_dex_hof_consumer_song as song_tests
 import test_pr16_dex_hof_consumer_chain as delta_tests
 import test_pr16_dex_hof_consumer_references_actions as action_tests
 import test_pr16_dex_hof_consumer_palette as palette_tests
 import test_pr16_dex_hof_consumer_engine as engine_tests
 import test_pr16_dex_hof_battle_continuation as battle_tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh consumer scope');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  sources,bindings=public_sources()
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==latest['candidate']==data.CANDIDATE,'whole exact current candidate reconstruction')
  owners=data.d.bind_owners(current,latest);need(len(owners)==115,'all115 current actual owner bindings')
  inherited=delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS])
  for hit in inherited['hits']:need(identity(data.d.chunk(current,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'all874 retained hit bytes')
  data_tests.FIXTURE=(current,latest,inherited,sources)
  palette_tests.FIXTURE=(current,latest,inherited,data.read_review(data.PALETTE),ROOT,sources)
  engine_tests.FIXTURE=(current,inherited,data.read_review(data.ENGINE),sources)
  battle_tests.FIXTURE=(current,{p:sources[n]for p,n in[('src/general_bs_commands.c','battle-src--general_bs_commands.c'),('src/attackcanceler.c','battle-continuation-attackcanceler.c'),('BPRJ.ld','battle-BPRJ.ld')]})
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in(data_tests,song_tests,delta_tests,action_tests,palette_tests,engine_tests,battle_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'consumer-references-tests.txt').write_text(stream.getvalue())
  if not result.wasSuccessful():print(json.dumps(dict(error_code='NEW_REFERENCE_TEST_FAILURE',tests=[t.id()for t,_ in result.failures+result.errors])))
  need(result.wasSuccessful()and not result.skipped,'all new finite-consumer cases without skipped current tests')
  r1,p1=data.regions(current,latest,inherited,sources)
  r3,p3=song.regions(current,inherited,r1,data.protected_windows());need(not r3,'no repeated discovery from unchanged133 song IDs')
  evidence=delta.build(inherited,r1,dict(data=p1,song=p3,public_source_bindings=bindings));full=delta.materialize(inherited,evidence)
  need(data.d.compare_inventory(full['hits'],inherited)['same_inventory']and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all874 identities and retained723/remainingunknown rows exact')
  need(all(evidence[k]==EXPECTED[k]for k in('newly_classified','classified','unclassified')),'exact three new rooted references')
  write(PUBLIC/'reference-chain.json',evidence);frontier=unknown_frontier(full,owners);write(PUBLIC/'unknown-frontier.json',frontier)
  m=dict(status='PASS_CURRENT_723_PARENT_BOUND_CONSUMER_REFERENCES',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
   classified=evidence['classified'],unclassified=evidence['unclassified'],newly_classified=evidence['newly_classified'],new_data=2,new_code=1,new_song=0,old_inventory_candidates=874,previous_classified=723,previous_unknown=151,owner_unknown=frontier['owner_unknown'],unowned_unknown=frontier['unowned_unknown'],
   all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,delta_identity=identity((PUBLIC/'reference-chain.json').read_bytes()),baseline_identity=delta.BASELINE_ID,parent_identity=delta.PARENT_ID,earlier_identity=delta.EARLIER_ID,unknown_identity=identity((PUBLIC/'unknown-frontier.json').read_bytes()),
   source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({*delta.PARENT_INPUTS,LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json'}),
   current_owner_count=len(owners),current_rom_reconstructions=reconstructed,historical_rom_reconstructions=0,historical_input_run=37338921508,historical_input_tests_reused=16,old_full_rom_scan_runs=0,native_processes=0,accepted_heap_reruns=0,independent_final_source_review_completed=False,validation_scope='新scope専用unit、独立歴史入力と現候補全SHA/115actual owner/874hit/有限consumerの機械検証。旧最終song/battle/Surfの独立再レビュー未実施を保持。',
   combined_song_models=p3['combined_song_models'],retained_sample_witnesses=p3['retained_sample_witnesses'],old_models_reused_for_new_cross_song_role_safety=True,tutor_upper_word_remains_unknown=False,battle_unknown_count=10,battle_partial_models=16,
   donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False)
  write(PUBLIC/'measurement.json',m);bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()})
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc());frames=[dict(source=Path(t.filename).name,function=t.name,line=t.lineno)for t in traceback.extract_tb(exc.__traceback__)if Path(t.filename).parent==ROOT/'scripts']
  print(json.dumps(dict(error_code='REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',type=type(exc).__name__,source_frames=frames)))
  write(OUT/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,error_code='REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',native_processes=0,current_rom_reconstructions=reconstructed))
  raise RuntimeError('REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED')from None


def validate_measurement(m):
 need(m['status']=='PASS_CURRENT_723_PARENT_BOUND_CONSUMER_REFERENCES'and m['source_head']==os.environ['GITHUB_SHA']and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact successful source/run measurement')
 expected=dict(current_owner_count=115,current_rom_reconstructions=1,old_inventory_candidates=874,previous_classified=723,previous_unknown=151,**EXPECTED)
 need(all(type(m[k])is int and m[k]==v for k,v in expected.items()),'exact bound measurement counters')
 need(m['retained_sample_witnesses']==50,'all original and immediate-parent50 sample witnesses preserved')
 need(m['tutor_upper_word_remains_unknown']is False and m['historical_input_run']==37338921508 and m['historical_input_tests_reused']==16 and m['historical_rom_reconstructions']==0 and m['battle_unknown_count']==10 and m['battle_partial_models']==16,'historical reuse and partial battle boundary exact')
 need(type(m['unit_tests'])is int and m['unit_tests']>0 and all(m[k]is True for k in('all_prior_accepted_retained','remaining_unknown_rows_retained','old_full_rom_inventory_reused','old_models_reused_for_new_cross_song_role_safety')),'measured retention contracts')


def validate_record(m,raw,inherited):
 evidence=delta.read_measured(raw,m['delta_identity'],inherited)
 validate_measurement(m)
 categories=collections.Counter(row['classification']for row in evidence['changes'])
 need(categories==CATEGORIES,'exact independently measured rooted category counts')
 full=delta.materialize(inherited,evidence)
 need(m['candidate']==evidence['candidate']==inherited['candidate']==data.CANDIDATE,'record same whole candidate')
 for key in('classified','unclassified','newly_classified'):need(m[key]==evidence[key],'record exact additive counters')
 need(all(full[k]==inherited[k]for k in('reference_delta','reference_chain','remaining_reference_chain','script_reference_chain')),'all four old delta families and witnesses exactly retained')
 need(not any(m[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns')),'no unproved runtime/lease promotion')
 need(all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'record keeps prior accepted and remaining unknown exact')
 return evidence


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'all earlier originals and unique new checkpoint')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());evidence=validate_record(m,(PUBLIC/'reference-chain.json').read_bytes(),delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]))
 frontier_raw=(PUBLIC/'unknown-frontier.json').read_bytes();owners={o['name']:o for o in json.loads((ROOT/LATEST).read_bytes())['placement']['owner_byte_audit']}
 need(identity(frontier_raw)==m['unknown_identity']and json.loads(frontier_raw)==unknown_frontier(delta.materialize(delta.parent(*[(ROOT/path).read_bytes()for path in delta.PARENT_INPUTS]),evidence),owners),'complete exact remaining unknown inventory and actual owner join')
 need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'all measured source and predecessor bindings')
 bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()});paths=set()
 for name in sorted(PROOF):
  target=ROOT/EVIDENCE/name;need(not target.exists(),'immutable reference evidence');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((PUBLIC/name).read_bytes());paths.add(target.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),previous_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),reference_baseline=delta.BASELINE,reference_parent=delta.PARENT))
 summary=f'現0641の旧egg874参照へ実root/consumerから新{m["newly_classified"]}件を分類し、{m["classified"]}分類/{m["unclassified"]}未知（owner内{m["owner_unknown"]}/外{m["unowned_unknown"]}）。新{m["unit_tests"]}試験、全115actual owner/874hit、旧723全行・旧25/17/33/29 changesと22/16/33/23 witnessesを保持。donor/正式ROM/Save101不変。'
 goal=f'残{m["unclassified"]}件の実root/consumerを閉じる。owner内未知0でもdonor不可。全unknown0だけではdonor不可。間接参照・旧egg退役完全性を証明して明示移管し、Ccontroller実配置、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、heap-ready/同期非再入/全出口Freeを閉じる。その後正式候補切替→trainer131後半→シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_consumer_references']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=m['classified'],unclassified=m['unclassified'],delta_identity=m['delta_identity'],parent_identity=delta.PARENT_ID,earlier_identity=delta.EARLIER_ID,owner_unknown=m['owner_unknown'],unowned_unknown=m['unowned_unknown'],donor_leased=False,controller_runtime_wired=False,historical_input_checkpoint=data.HISTORY_CP,historical_run=37338921508,battle_partial_models=16,battle_unknown_count=10,retained_song_models=133,retained_sample_witnesses=50,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_UNOWNED_REFERENCE_AND_RETIREMENT_PROOF',goal_ja=goal,read_paths=[GUIDE,CP,*delta.PARENT_INPUTS,'scripts/pr16_dex_hof_consumer_chain.py',data.HISTORY_CP,data.ENGINE,data.BATTLE])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='619原本・644delta・661chain・694chain・723chainを保持する追加root/consumer分類source。実root/consumerから有限窓のみ型付けし、donor/本番配線は未受入。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'原本4.1MB/旧delta/旧chainを複製・改変しない。全親をidentity照合してmaterializeし、旧104追加を落とさない。影響なしheap/native再走禁止。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],reference_unit_tests=m['unit_tests'],classified=m['classified'],unclassified=m['unclassified'],native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-CONSUMER-REFERENCES / 723親保持とT09実歴史根\n- Version: hof-consumer-reference-chain-v1\n- Status: STOPPED（新3分類・owner内未知0、donor/本番controller未完）\n- Summary: {summary}\n- Files changed: 新classifier/拒否tests/source review/Actions/guide/CP/minimal chain、独立歴史入力証拠、固定MDJSON、両append-onlyログ。\n- Verify: 新unit={m["unit_tests"]}（別run歴史16を再利用）、全candidate/115actual owner/874hit全SHA、固定source全blob。旧723と残unknown全field、旧25+17+33+29変化と22+16+33+23witness全byteを保持。音声{m["combined_song_models"]}曲のroleと50過去sample witnessを新typed窓に照合。旧全ROMscan/native/heap0。旧最終song/battle/Surfの独立再レビューは未実施を継承、通常unitと現候補の機械検査に受入範囲を限定。\n- Boundary: 旧formalは事前reviewのみ。現0641で全owner/窓再束縛。有限型分類をstory到達/実音声再生/退役不在へ昇格しない。\n- Publication: 619原本4.1MB/644delta149772byte/661chain95619byte/694chain71138byte/723chain134951byteは不変参照。新chain {m["delta_identity"]["size"]}byteを独立measurement全SHAとclosed schemaで検査。producer/guard/upload/record path一致・非空・完全10text/receipt必須、hidden/symlink/未知file拒否。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputs/固定公開source。歴史run37338921508全8step/16testsを参照継承し、旧Stage38再取得・再生成0。source・最小address-size-SHA・textのみ。ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。正式ROM/Save101/owner115/saveowner52/残804byte不変、heap13352の保存退避53300跨ぎ禁止。\n'
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
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-CONSUMER-REFERENCES VERIFY=PASS COMMIT='+receipt['final_head'])
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
 measure=json.loads(files['measurement.json']);need(measure['delta_identity']==identity(files['reference-chain.json']),'independent measured complete chain envelope')
 need(measure['source_head']==receipt['source_head']and measure['run_id']==receipt['record_run'],'same source and run measurement')
 return True

def export():
 publication.output(PUBLIC,success='record.json',failure=None)
 files={}
 for path in PUBLIC.iterdir():
  need(path.is_file()and not path.is_symlink()and not path.name.startswith('.')and path.name in PROOF|{'record.json',*(n for n,_ in SNAPSHOTS)},'closed regular nonhidden success text publication')
  files[path.name]=path.read_bytes()
 validate_export(files,git('rev-parse','HEAD').decode().strip())

if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed reference workflow');globals()[sys.argv[1]]()
