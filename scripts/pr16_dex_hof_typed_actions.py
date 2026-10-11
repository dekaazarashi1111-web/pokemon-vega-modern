#!/usr/bin/env python3
"""現候補の残参照を根付きnumeric/XCMD consumerへ接続。donor権限は発行しない。"""
import collections,copy,datetime,hashlib,io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_hof_song_actions as song_actions
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='79c55005f37a752fe1aedae7606e2beee380705f'
WF='.github/workflows/pr16-dex-hof-typed.yml';SELF='scripts/pr16_dex_hof_typed_actions.py';GUIDE='docs/PR16_DEX_HOF_TYPED_JA.md'
ENGINE='content/modernization/pr16_dex_hof_song_extended_engine_review.json'
SONG_SOURCES='content/modernization/pr16_dex_hof_typed_song_sources.json'
CODE={WF,SELF,GUIDE,ENGINE,SONG_SOURCES,'content/modernization/pr16_dex_hof_typed_numeric_review.json','scripts/pr16_dex_hof_typed_numeric.py','tests/test_pr16_dex_hof_typed_numeric.py','scripts/pr16_dex_hof_song_extended.py','tests/test_pr16_dex_hof_song_extended.py','tests/test_pr16_dex_hof_typed_actions.py','scripts/pr16_dex_hof_typed_palette.py','tests/test_pr16_dex_hof_typed_palette.py','content/modernization/pr16_dex_hof_typed_palette_review.json'}
OLDCP='content/modernization/pr16_dex_hof_song_checkpoint.json';INVENTORY='content/modernization/pr16_dex_hof_song_evidence/egg-typed-audit.json'
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_typed_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_typed_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-typed';PUBLIC=ROOT/'public-dex-hof-typed';ARTIFACT='pr16-dex-hof-typed-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','typed-tests.txt','egg-typed-audit.json'}


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all inherited sources and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']['sha256']=='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'and cp['classified']==560 and cp['unclassified']==314,'exact retained song frontier')
 need(cp['evidence_bindings'][INVENTORY]==identity((ROOT/INVENTORY).read_bytes()),'whole inherited 874 typed inventory original')


def typed_sources():
 import pr16_dex_hof_typed_numeric as numeric
 import pr16_dex_hof_typed_palette as palette
 source_root=OUT/'bound-typed-sources';source_root.mkdir()
 review=json.loads((ROOT/palette.REVIEW).read_bytes())
 paths=set(numeric.SOURCE_GIT_BLOB)|{numeric.RECEIPT,palette.REVIEW}|set(review['source_bindings'])
 if getattr(numeric,'REVIEW',None):paths.add(numeric.REVIEW)
 lock=json.loads((ROOT/'state/source-lock.json').read_bytes());upstreams={r['path']:r for r in lock['sources']}
 for path in sorted(paths):
  need('..'not in Path(path).parts and not Path(path).is_absolute(),'closed source-only relative path')
  if path.startswith('vendor/upstream/CFRU-JP/'):
   upstream=upstreams['vendor/upstream/CFRU-JP'];commit=upstream['resolved_commit']
   need(commit=='e24a16fe39e27ae162faf5b78596d1f3df18489d'and upstream['repository']=='https://github.com/kapibarasan000/CFRU-JP.git','exact numeric upstream source lock')
   source=path[len('vendor/upstream/CFRU-JP/'):]
   need(source in('src/learn_move.c','include/pokemon.h','src/item.c','src/config.h'),'closed numeric external source set')
   with urllib.request.urlopen('https://raw.githubusercontent.com/kapibarasan000/CFRU-JP/'+commit+'/'+source,timeout=90)as response:raw=response.read(1000001)
   need(0<len(raw)<=1000000 and b'\0'not in raw,'bounded complete source text');raw.decode('utf8')
   need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==numeric.SOURCE_GIT_BLOB[path],'whole downloaded numeric Git blob')
  else:
   file=ROOT/path;need(file.is_file()and not file.is_symlink(),'regular tracked typed source');raw=file.read_bytes()
  destination=source_root/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
 numeric.source_proof(source_root);palette.source_proof(source_root)
 return source_root


def extend_numeric(raw,base,latest,source_root):
 import pr16_dex_hof_donor as donor
 import pr16_dex_hof_typed_numeric as numeric
 regions,proof=numeric.numeric_regions(raw,latest,source_root)
 import pr16_dex_hof_typed_palette as palette
 palette_regions,palette_proof=palette.palette_regions(raw,latest,source_root)
 regions=list(regions)+list(palette_regions);proof=dict(numeric=proof,palette=palette_proof)
 for witness in base['song_extended_extension']['asset_witnesses']:
  need(not any(r.start<witness['end_exclusive']and witness['start']<r.end for r in regions),'new numeric/palette and song payload roles do not overlap')
 result=copy.deepcopy(base);changed=[];category_counts=collections.Counter()
 for i,hit in enumerate(result['hits']):
  if hit['accepted']:continue
  row=copy.deepcopy(donor.classify_hits([hit],regions,latest['placement']['owner_byte_audit'])[0])
  if not row['accepted']:continue
  row.pop('reason',None);row.pop('owner_candidates',None)
  need(identity(donor.chunk(raw,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'retained numeric hit bytes')
  result['hits'][i]=row;category_counts[row['classification']]+=1;changed.append({k:hit[k]for k in('address','target','kind','size','sha256')})
 result['classified']=sum(r['accepted']for r in result['hits']);result['unclassified']=len(result['hits'])-result['classified'];result['classifications']=dict(collections.Counter(r['classification']for r in result['hits']))
 result['typed_numeric_extension']=dict(status='PASS_ROOTED_NUMERIC_AND_PALETTE_CONSUMERS',newly_classified=len(changed),new_numeric=len(changed)-category_counts['FALSE_POSITIVE_TYPED_PALETTE_CROSS_FIELD'],new_classifications=dict(category_counts),new_palette=category_counts['FALSE_POSITIVE_TYPED_PALETTE_CROSS_FIELD'],changed_hits=changed,proof=proof,
  regions=[dict(address=r.start,size=r.end-r.start,kind=r.kind,evidence=r.evidence)for r in regions],old_full_rom_inventory_reused=True,donor_leased=False,indirect_reference_completeness_claimed=False)
 return result


def run():
 import pr16_dex_hof_song as song
 import pr16_dex_hof_song_extended as extended
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_typed_numeric as numeric_tests
 import test_pr16_dex_hof_song_extended as song_tests
 import test_pr16_dex_hof_typed_palette as palette_tests
 import test_pr16_dex_hof_typed_actions as record_tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh typed observation');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in(numeric_tests,song_tests,palette_tests,record_tests));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(PUBLIC/'typed-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new fail-closed typed suites')
  song_actions.OUT=OUT;song_actions.SOURCES=SONG_SOURCES;sources,bindings=song_actions.public_sources();source_root=typed_sources()
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==song.CANDIDATE==latest['candidate'],'whole current candidate reconstruction')
  owners=song.prior.bind_owners(current,latest);need(len(owners)==115,'all actual latest owner afterSHA bindings')
  engine=extended.bind_engine(current,json.loads((ROOT/song_actions.ENGINE).read_bytes()),json.loads((ROOT/ENGINE).read_bytes()))
  inherited=json.loads((ROOT/INVENTORY).read_bytes());song_audit=extended.extend(current,inherited,engine,sources,bindings)
  audit=extend_numeric(current,song_audit,latest,source_root)
  need(song.prior.compare_inventory(audit['hits'],inherited)['same_inventory']and len(audit['hits'])==874,'exact full original inventory retained')
  need(all(a==b for a,b in zip(inherited['hits'],audit['hits'])if a['accepted']),'all 560 previous accepted rows retained exactly')
  need(not audit['donor_leased']and not audit['donor_eligible']and not audit['indirect_reference_completeness_claimed'],'no lease or completeness promotion')
  need(audit['classified']>560 and audit['classified']+audit['unclassified']==874,'positive bounded typed frontier change')
  write(PUBLIC/'egg-typed-audit.json',audit)
  songproof=audit['song_extended_extension'];numericproof=audit['typed_numeric_extension']
  m=dict(status='PASS_CURRENT_ROOTED_REMAINING_TYPED_CLASSIFICATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
    classified=audit['classified'],unclassified=audit['unclassified'],newly_classified=audit['classified']-560,new_numeric=numericproof['new_numeric'],new_palette=numericproof['new_palette'],new_song=songproof['newly_classified'],
    old_inventory_candidates=874,all_prior_accepted_retained=True,old_full_rom_inventory_reused=True,typed_audit_identity=identity((PUBLIC/'egg-typed-audit.json').read_bytes()),source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({OLDCP,INVENTORY,LATEST,'state/source-lock.json'}),
    selected_song_id_count=songproof['selected_song_id_count'],rooted_jp_fanfare_rows=songproof['rooted_jp_fanfare_rows'],complete_modeled_songs=songproof['accepted_complete_songs'],new_sample_witnesses=len(songproof['asset_witnesses']),jp_song_table_extent_claimed=False,typed_source_bindings={p:{k:b[k]for k in('size','sha256')}for group in(numericproof['proof']['numeric']['bindings'],numericproof['proof']['palette']['source_bindings'])for p,b in group.items()},public_source_bindings=bindings,engine_review_binding=identity((ROOT/ENGINE).read_bytes()),current_owner_count=len(owners),current_rom_reconstructions=reconstructed,
    accepted_link_reconstruction_for_new_read_only_scope=True,unaffected_native_reruns=0,native_processes=0,old_full_rom_scan_runs=0,donor_leased=False,donor_eligible=False,complete_runtime_audio_read_footprint_claimed=False,indirect_reference_completeness_claimed=False,
    controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False)
  write(PUBLIC/'measurement.json',m)
 except Exception as exc:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,message=str(exc).replace(str(ROOT),'.'),native_processes=0,current_rom_reconstructions=reconstructed));raise


def validate_record_audit(audit,m,inherited):
 import pr16_dex_hof_donor as donor
 import pr16_dex_hof_song as song
 need(audit['candidate']==m['candidate']==inherited['candidate']==song.CANDIDATE,'record whole candidate identity')
 need(len(audit['hits'])==audit['candidates']==inherited['candidates']==len(inherited['hits'])==874,'record all original inventory rows')
 need(donor.compare_inventory(audit['hits'],inherited)['same_inventory'],'record original inventory identity set')
 fields=('address','target','kind','size','sha256');changed=[]
 for old,new in zip(inherited['hits'],audit['hits']):
  need(all(old[k]==new[k]for k in fields),'record inventory ordering and identities')
  need(type(new['accepted']) is bool,'record boolean classification')
  if old['accepted'] or not new['accepted']:need(old==new,'record existing accepted and remaining unknown rows exactly retained')
  else:changed.append(new)
 need(sum(h['accepted']for h in inherited['hits'])==inherited['classified']==560 and inherited['unclassified']==314,'record exact predecessor frontier')
 classified=sum(h['accepted']for h in audit['hits'])
 need(classified==audit['classified']==m['classified'] and 874-classified==audit['unclassified']==m['unclassified'],'record exact current counters')
 need(audit['classifications']==dict(collections.Counter(h['classification']for h in audit['hits'])),'record classification histogram')
 need(len(changed)==m['newly_classified']==m['new_numeric']+m['new_palette']+m['new_song'] and len(changed)>0,'record positive disjoint extension count')
 need(audit['typed_numeric_extension']['newly_classified']==m['new_numeric']+m['new_palette']and audit['typed_numeric_extension']['new_numeric']==m['new_numeric']and audit['typed_numeric_extension']['new_palette']==m['new_palette']and audit['song_extended_extension']['newly_classified']==m['new_song'],'record exact extension counters')
 need(not any(audit[k]for k in('donor_leased','donor_eligible','indirect_reference_completeness_claimed')),'record no donor or completeness grant')
 need(not any(m[k]for k in('candidate_changed','donor_leased','donor_eligible','indirect_reference_completeness_claimed','controller_runtime_wired','formal_rom_changed','formal_save_changed','native_processes','old_full_rom_scan_runs')),'record no unchecked promotion')
 return len(changed)


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'unchanged originals and unique typed CP')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());need(identity((PUBLIC/'egg-typed-audit.json').read_bytes())==m['typed_audit_identity'],'record exact measured audit bytes');validate_record_audit(json.loads((PUBLIC/'egg-typed-audit.json').read_bytes()),m,json.loads((ROOT/INVENTORY).read_bytes()));need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings'])and m['typed_source_bindings']=={p:identity((OUT/'bound-typed-sources'/p).read_bytes())for p in m['typed_source_bindings']},'all measured source bytes');paths=set()
 for name in sorted(PROOF):
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'immutable typed evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((PUBLIC/name).read_bytes());paths.add(dest.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),prior_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID'])))
 summary=f'現候補0641af70の旧egg874参照に根付きnumericと拡張JP song consumer分類を追加。新numeric{m["new_numeric"]}/palette{m["new_palette"]}/song{m["new_song"]}、{m["classified"]}分類/{m["unclassified"]}未知。旧560受入と全874inventoryを保持。新{m["unit_tests"]}tests、現候補の新read用再構成1回、旧inventory/native0。donor/正式ROM/Save101不変。'
 goal=f'残{m["unclassified"]}件を根付きconsumerへ結び、間接参照・旧egg退役完全性を証明する。未知0と退役ゲート後だけ必要分を明示donor移管し、Ccontroller実owner配置・全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL・同期heap lifetime・全mode/早期31/species9bitを閉じる。その後正式候補切替、trainer131後半から最終シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_typed']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=m['classified'],unclassified=m['unclassified'],newly_classified=m['newly_classified'],donor_leased=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_REMAINING_TYPED_DONOR_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,'scripts/pr16_dex_hof_typed_numeric.py','scripts/pr16_dex_hof_song_extended.py',OLDCP])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='根付きnumeric/拡張JP songの型分類source。donor移管・本番controller配線・実演奏は未受入。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'候補/source不変で旧全ROM走査/heap/native/習得原本生成を再走しない。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],typed_unit_tests=m['unit_tests'],classified=m['classified'],unclassified=m['unclassified'],native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-TYPED / 残numeric・拡張song consumer分類\n- Version: hof-typed-v1\n- Status: STOPPED（新型分類を実装検証。donor/本番保存配線は未完）\n- Summary: {summary}\n- Files changed: classifier/negative suites/engine semantic review/Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: unit={m["unit_tests"]}; 現candidate全SHA/115owner afterSHA、固定serializer/C ABI/receipts、追加JP engine窓とmutable tone command状態を束縛。旧560accepted不変、全874hit bytes照合、旧全ROMscan/native0。\n- Boundary: 未知参照をowner名だけで除外しない。失敗track構造/cross-song競合/PCM-DPCM区別を保持。footstep250/251の固定MIDIと現song不一致を維持。donor0、正式ROM/Save101/50HOF/opaque1936/baseline/release不変。heap13352は保存退避53300跨ぎ禁止、全保存入口lifetimeと32sectorcontroller本番配線未完。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputs、固定公開source blob。公開source/最小address-size-SHA/textのみ、ROM断片/rawhex/ROM/inputsave/runtime/runner/credentials追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'all inherited originals retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_RECORDED_ROOTED_TYPED_FRONTIER',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0))


def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed typed text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text with LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only entire old logs retained')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-TYPED VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in PROOF|{'failure.json','record.json',*(n for n,_ in SNAPSHOTS)},'closed nonsymlink flat text set');raw=p.read_bytes();need(0<len(raw)<16000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed typed workflow');globals()[sys.argv[1]]()
