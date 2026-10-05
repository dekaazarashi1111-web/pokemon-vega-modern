#!/usr/bin/env python3
"""親deltaを全文固定し、残参照の新根だけ測定・記録する。"""
import collections,datetime,hashlib,io,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_song_actions as song_actions
import pr16_dex_hof_reference_gaps as data
import pr16_dex_hof_reference_gaps_song as song
import pr16_dex_hof_reference_chain as delta
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='688ea79ac2fee2672249d3e377ac7200b9d5c860'
WF='.github/workflows/pr16-dex-hof-reference-gaps.yml';SELF='scripts/pr16_dex_hof_reference_gaps_actions.py';GUIDE='docs/PR16_DEX_HOF_REFERENCE_GAPS_JA.md'
CODE={WF,SELF,GUIDE,data.REVIEW,song.REVIEW,song.SOURCES}
CODE|={'scripts/pr16_dex_hof_reference_'+name+'.py'for name in('gaps','gaps_song','chain')}
CODE|={'tests/test_pr16_dex_hof_reference_'+name+'.py'for name in('gaps','gaps_song','chain','gaps_actions')}
OLDCP='content/modernization/pr16_dex_hof_reference_checkpoint.json'
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_reference_gaps_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_reference_gaps_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-reference-gaps';PUBLIC=ROOT/'public-dex-hof-reference-gaps';ARTIFACT='pr16-dex-hof-reference-gaps-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','reference-gaps-tests.txt','reference-chain.json','unknown-frontier.json'}
MAX_FILE=4000000;MAX_TOTAL=12000000


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all inherited originals and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']==data.CANDIDATE and cp['classified']==644 and cp['unclassified']==230,'exact inherited recovered typed frontier')
 need(cp['baseline_identity']==delta.BASELINE_ID and cp['delta_identity']==delta.PARENT_ID,'whole inherited 874 inventory and644 parent');delta.parent((ROOT/delta.BASELINE).read_bytes(),(ROOT/delta.PARENT).read_bytes())



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


def run():
 import pr16_dex_hof_song_extended as extended
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_reference_gaps as data_tests
 import test_pr16_dex_hof_reference_gaps_song as song_tests
 import test_pr16_dex_hof_reference_chain as delta_tests
 import test_pr16_dex_hof_reference_gaps_actions as action_tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh reference scope');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in(data_tests,song_tests,delta_tests,action_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'reference-gaps-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new fail-closed reference suites')
  song_actions.OUT=OUT;song_actions.SOURCES=song.SOURCES;sources,bindings=song_actions.public_sources()
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==latest['candidate']==data.CANDIDATE,'whole exact current candidate reconstruction')
  owners=data.d.bind_owners(current,latest);need(len(owners)==115,'all current actual owner bindings')
  inherited=delta.parent((ROOT/delta.BASELINE).read_bytes(),(ROOT/delta.PARENT).read_bytes())
  for hit in inherited['hits']:need(identity(data.chunk(current,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'every retained hit actual bytes')
  r1,p1=data.regions(current,latest,inherited,sources)
  engine=extended.bind_engine(current,json.loads((ROOT/song_actions.ENGINE).read_bytes()),json.loads((ROOT/'content/modernization/pr16_dex_hof_song_extended_engine_review.json').read_bytes()))
  r3,p3=song.song_regions(current,inherited,engine,sources,r1)
  need(all(not(r.start<s.end and s.start<r.end)for r in r1 for s in r3),'data/code and song roles disjoint')
  evidence=delta.build(inherited,r1+r3,dict(data=p1,song=p3,public_source_bindings=bindings))
  full=delta.materialize(inherited,evidence)
  need(data.d.compare_inventory(full['hits'],inherited)['same_inventory']and all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'all874 identities and retained644/remainingunknown rows exact')
  need(evidence['newly_classified']==17 and evidence['classified']==661 and evidence['unclassified']==213,'exact new11 data/3 instruction/3 song frontier')
  write(PUBLIC/'reference-chain.json',evidence)
  frontier=unknown_frontier(full,owners);owner_unknown=frontier['owner_unknown'];write(PUBLIC/'unknown-frontier.json',frontier)
  m=dict(status='PASS_CURRENT_PARENT_BOUND_REFERENCE_GAPS',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
   classified=evidence['classified'],unclassified=evidence['unclassified'],newly_classified=evidence['newly_classified'],new_data=11,new_code=3,new_song=3,old_inventory_candidates=874,previous_classified=644,previous_unknown=230,owner_unknown=owner_unknown,unowned_unknown=frontier['unowned_unknown'],
   all_prior_accepted_retained=True,remaining_unknown_rows_retained=True,old_full_rom_inventory_reused=True,delta_identity=identity((PUBLIC/'reference-chain.json').read_bytes()),baseline_identity=delta.BASELINE_ID,parent_identity=delta.PARENT_ID,unknown_identity=identity((PUBLIC/'unknown-frontier.json').read_bytes()),
   source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({OLDCP,delta.BASELINE,delta.PARENT,LATEST,'state/source-lock.json','content/modernization/pr16_story_route_adapter_checkpoint.json'}),
   current_owner_count=len(owners),current_rom_reconstructions=reconstructed,old_full_rom_scan_runs=0,native_processes=0,accepted_heap_reruns=0,
   combined_song_models=p3['combined_song_count'],old_models_reused_for_new_cross_song_role_safety=True,tutor_upper_word_remains_unknown=True,
   donor_leased=False,donor_eligible=False,indirect_reference_completeness_claimed=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False)
  write(PUBLIC/'measurement.json',m);bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()})
 except Exception as exc:
  # 下位compiler/decoderの詳細には私有byte/pathがあり得る。公開失敗証拠へ転記しない。
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc())
  write(OUT/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,error_code='REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED',native_processes=0,current_rom_reconstructions=reconstructed))
  raise RuntimeError('REFERENCE_SCOPE_FAILED_PRIVATE_DETAIL_RETAINED') from None


def validate_measurement(m):
 need(m['status']=='PASS_CURRENT_PARENT_BOUND_REFERENCE_GAPS'and m['source_head']==os.environ['GITHUB_SHA']and m['run_id']==int(os.environ['GITHUB_RUN_ID']),'exact successful source/run measurement')
 expected=dict(current_owner_count=115,current_rom_reconstructions=1,new_data=11,new_code=3,new_song=3,newly_classified=17,old_inventory_candidates=874,previous_classified=644,previous_unknown=230,owner_unknown=5,unowned_unknown=208,classified=661,unclassified=213,combined_song_models=132)
 need(all(type(m[k])is int and m[k]==v for k,v in expected.items()),'exact bound measurement counters')
 need(type(m['unit_tests'])is int and m['unit_tests']>0 and all(m[k]is True for k in('all_prior_accepted_retained','remaining_unknown_rows_retained','old_full_rom_inventory_reused','old_models_reused_for_new_cross_song_role_safety','tutor_upper_word_remains_unknown')),'measured retention contracts')


def validate_record(m,raw,inherited):
 evidence=delta.read_measured(raw,m['delta_identity'],inherited)
 validate_measurement(m)
 categories=collections.Counter(row['classification']for row in evidence['changes'])
 need(categories=={'FALSE_POSITIVE_TYPED_REFERENCE_TRAINER_NAME_ITEM_CROSS_FIELD':2,'FALSE_POSITIVE_TYPED_REFERENCE_ADJACENT_JP_TEXT_CROSSING':3,'FALSE_POSITIVE_TYPED_REFERENCE_PACKED_U16_CROSS_ROW':1,'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_THUMB_INSTRUCTION_STREAM':3,'FALSE_POSITIVE_TYPED_REFERENCE_INDEXED_U16_PAIR':1,'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_TILESET_LZ77':3,'FALSE_POSITIVE_TYPED_REFERENCE_ROOTED_SPRITE_4BPP_FRAME':1,'FALSE_POSITIVE_TYPED_REFERENCE_PCM8':3},'exact independently measured rooted category counts')
 full=delta.materialize(inherited,evidence)
 need(m['candidate']==evidence['candidate']==inherited['candidate']==data.CANDIDATE,'record same whole candidate')
 for key in('classified','unclassified','newly_classified'):need(m[key]==evidence[key],'record exact additive counters')
 need(m['new_data']+m['new_code']+m['new_song']==m['newly_classified']==17 and m['combined_song_models']==132,'exact typed subset counters')
 need(not any(m[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs','accepted_heap_reruns')),'no unproved runtime/lease promotion')
 need(all(old==new for old,new in zip(inherited['hits'],full['hits'])if old['accepted']or not new['accepted']),'record keeps prior accepted and remaining unknown exact')
 return evidence


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'all earlier originals and unique new checkpoint')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());evidence=validate_record(m,(PUBLIC/'reference-chain.json').read_bytes(),delta.parent((ROOT/delta.BASELINE).read_bytes(),(ROOT/delta.PARENT).read_bytes()))
 frontier_raw=(PUBLIC/'unknown-frontier.json').read_bytes();owners={o['name']:o for o in json.loads((ROOT/LATEST).read_bytes())['placement']['owner_byte_audit']}
 need(identity(frontier_raw)==m['unknown_identity']and json.loads(frontier_raw)==unknown_frontier(delta.materialize(delta.parent((ROOT/delta.BASELINE).read_bytes(),(ROOT/delta.PARENT).read_bytes()),evidence),owners),'complete exact remaining unknown inventory and actual owner join')
 need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'all measured source and predecessor bindings')
 bounded_files({p.name:p.read_bytes()for p in PUBLIC.iterdir()});paths=set()
 for name in sorted(PROOF):
  target=ROOT/EVIDENCE/name;need(not target.exists(),'immutable reference evidence');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((PUBLIC/name).read_bytes());paths.add(target.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),previous_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),reference_baseline=delta.BASELINE,reference_parent=delta.PARENT))
 summary=f'現0641の旧egg874参照について、regression trainer2/tilesetLZ3、Stage61 TEXT3/sprite1、flagmap1/SharedIndex1、命令3、有限JP音声3の新17件を分類し、661分類/213未知（owner内5/外208）。新{m["unit_tests"]}試験と新旧132曲/旧47sample保持を検証。644親delta全25行/22witnessを固定chainで継承し、原本4.1MBと旧149772byteを複製しない。donor/正式ROM/Save101不変。'
 goal='残213（owner内5/外208）のrooted参照を閉じる。T09上位wordのPLC2混同を避け、Stage36/38/55/70と未根付きJP音声306等を最新actual ownerへ束縛する。全unknown0だけではdonor不可で、間接参照・旧egg退役完全性を証明して明示移管する。その後Ccontroller実配置、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、heap-ready/同期非再入/全出口Freeを閉じ、正式候補切替→trainer131後半→最終シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'

 state['story_dex_owner']['runtime_integration']['hof_reference_gaps']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=661,unclassified=213,delta_identity=m['delta_identity'],parent_identity=delta.PARENT_ID,owner_unknown=5,unowned_unknown=208,tutor_upper_word_remains_unknown=True,donor_leased=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_REMAINING_ROOTED_REFERENCE_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,delta.BASELINE,delta.PARENT,'scripts/pr16_dex_hof_reference_chain.py',data.REVIEW,song.REVIEW])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='不変619原本＋644親deltaを継承する追加17根分類source。新旧132曲/47sampleとfinite-rootのrole競合を検査。donor/本番配線未受入。'
 state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'旧型分類/heap/nativeは変更影響なしに再実行しない。次回は619baseline＋644parent delta＋本chainを各全identityでmaterializeし、旧25行を落とさない。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],reference_unit_tests=m['unit_tests'],classified=661,unclassified=213,native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-REFERENCE-GAPS / 644親保持と追加17参照根\n- Version: hof-reference-chain-v1\n- Status: STOPPED（新17分類・記録済、donor/本番controller未完）\n- Summary: {summary}\n- Files changed: 新classifier/拒否tests/source review/Actions/guide/CP/minimal chain、固定MDJSON、両append-onlyログ。\n- Verify: 新unit={m["unit_tests"]}、全candidate/115 actual owner/874hit全SHA、固定source全blob。regression5/Stage614は命令でなくtrainer/LZ/text/sprite型。旧644と残unknown全field、旧25witness全byte保持。新旧132曲のrole＋finite-root conflict、旧47sample identityを確認。旧全ROMscan/native/heap0。\n- Boundary: 旧formalは事前reviewだけ。現0641で全owner/窓再束縛。SharedIndexはhistorical typingのみ、live到達や退役不在の受入なし。Shinyは明示r3 literal delegateだけ解決。song86はtask初回zero/data9更新とsprite全64slot使用時callback無し分岐の有限静的根、実到達/再生非主張。T09 PLC2混同拒否を保持。\n- Publication: 619原本4.1MBと644親delta149772byteは不変参照。追加chain {m["delta_identity"]["size"]}byteを独立measurement全SHAとclosed schemaで検査。producer/guard/upload/record path一致・非空・complete10text/receipt必須、hidden/symlink/未知fileを拒否。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputs/固定公開source。公開はsource・最小address-size-SHA・textのみ。ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。正式ROM/Save101/owner115/saveowner52/残804byte不変、heap13352の保存退避53300跨ぎ禁止。\n'

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
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-REFERENCE-GAPS VERIFY=PASS COMMIT='+receipt['final_head'])
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
