#!/usr/bin/env python3
"""Exact saved PLR1 data extends the retained typed inventory; no ROM/native reconstruction."""
import datetime,io,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_publication as publication
import pr16_story_live_probe as transport
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='94c3be28fea74f663ef4be6aa9611fbd8d825826'
WF='.github/workflows/pr16-dex-hof-numeric.yml';SELF='scripts/pr16_dex_hof_numeric_actions.py';GUIDE='docs/PR16_DEX_HOF_NUMERIC_JA.md'
CODE={WF,SELF,GUIDE,'scripts/pr16_dex_hof_numeric.py','tests/test_pr16_dex_hof_numeric.py'}
OLDCP='content/modernization/pr16_dex_hof_capacity_checkpoint.json'
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_numeric_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_numeric_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-numeric';PUBLIC=ROOT/'public-dex-hof-numeric';ARTIFACT='pr16-dex-hof-numeric-text-only'
ORIGINAL=(10683907559,35704908254,120487,'d7f66cae03f6d228e49dd6dbb3caea8760063e9a771ace0d13e009cfef402c9e')
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','numeric-tests.txt','egg-typed-audit.json'}

def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all inherited sources and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']['sha256']=='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'and cp['typed_audit']['classified']==443 and cp['typed_audit']['unclassified']==431,'exact retained frontier')

def run():
 import pr16_dex_hof_numeric as numeric
 import test_pr16_dex_hof_numeric as tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh numeric observation');OUT.mkdir(parents=True);PUBLIC.mkdir()
 try:
  stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));(PUBLIC/'numeric-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new fail-closed numeric suites')
  receipt,link,sources=numeric.source_proof();meta=transport.api('actions/artifacts/'+str(ORIGINAL[0]));publication.consumer(meta,'pr16-learnset-runtime-data',ORIGINAL[1]);archive,_=transport.archive(ORIGINAL)
  with archive:
   need(set(archive.namelist())=={'runtime-bundle.bin','runtime-image.bin','receipt.json','link.json'},'closed saved PLR1 data original')
   need(archive.read('receipt.json')==(ROOT/numeric.EVIDENCE/'receipt.json').read_bytes()and archive.read('link.json')==(ROOT/numeric.EVIDENCE/'link.json').read_bytes(),'all original source receipts')
   bundle=archive.read('runtime-bundle.bin');need(identity(bundle)==link['bundle']and archive.read('runtime-image.bin')==bundle[:receipt['size']],'whole original accepted bundle/image')
  old=json.loads((ROOT/OLDCP).read_bytes());inherited,latest=numeric.load_inherited();need(inherited==old['typed_audit'],'whole immutable inherited inventory');audit=numeric.extend(inherited,latest,bundle)
  need(audit['candidate']==old['candidate']and audit['candidates']==874 and audit['classified']==455 and audit['unclassified']==419 and audit['numeric_extension']['newly_classified']==12,'exact twelve PLR1 changes only')
  need(all(a==b for a,b in zip(old['typed_audit']['hits'],audit['hits'])if a['accepted']),'all443 prior accepted rows retained')
  need(not audit['donor_leased']and not audit['donor_eligible']and not audit['indirect_reference_completeness_claimed'],'no unproven owner transfer')
  write(PUBLIC/'egg-typed-audit.json',audit)
  write(PUBLIC/'measurement.json',dict(status='PASS_PLR1_EXACT_NUMERIC_CONSUMER_CLASSIFICATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=old['candidate'],candidate_changed=False,unit_tests=result.testsRun,classified=455,unclassified=419,newly_classified=12,old_inventory_candidates=874,all_prior_accepted_retained=True,old_full_rom_inventory_reused=True,original_artifact=ORIGINAL,plr1_bundle=link['bundle'],plr1_image=link['image'],typed_audit_identity=identity((PUBLIC/'egg-typed-audit.json').read_bytes()),source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({OLDCP,LATEST}|set(sources)),native_processes=0,arm_compiles=0,current_rom_reconstructions=0,accepted_source_regenerations=0,donor_leased=False,controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False))
 except Exception as exc:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,message=str(exc).replace(str(ROOT),'.'),native_processes=0));raise

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'unchanged originals and unique numeric CP')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'all measured source bytes');paths=set()
 for name in sorted(PROOF):
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'immutable numeric evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((PUBLIC/name).read_bytes());paths.add(dest.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),prior_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID'])))
 summary='現候補0641af70の旧egg全874見かけ参照を継承し、PLR1の12件を固定compose/receipt/linked C consumerと全1483ownerの数値spanへ結合。455件分類・419件未知。12件すべての行境界跨ぎも両側の型で証明。既存bundle再利用、ROM再構成/ARM/native0、donor0、正式ROM/Save101不変。'
 goal='残419件をtyped song/track VOICE/ToneData/WaveData、他numeric、code consumerへ結合し、間接参照・退役consumer完全性を証明して必要分だけ明示donor移管する。その後Ccontrollerと実S61E/MDXの全writer/loader/Link/INITIAL配線、同期heap所有、全mode/早期31/species9bit/残typedを受入し、正式候補切替からtrainer131後半・最終シオウ通常回復/保存/独立coldContinueへ。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_numeric']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=455,unclassified=419,newly_classified=12,donor_leased=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_TYPED_SONG_AND_REMAINING_DONOR_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,'scripts/pr16_dex_hof_numeric.py','docs/PR16_DEX_HOF_CAPACITY_JA.md',OLDCP])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='PLR1の固定数値generator/consumer分類source。容量移管・本番controller接続の受入ではない。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append('PLR1数値分類12件は原本bundle・image・poolを独立署名し、全1483ownerと行境界を検査。現source/candidate不変なら旧874全ROM走査・heap/native・習得原本生成を再走しない。455分類/419未知、donor0。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],numeric_unit_tests=m['unit_tests'],classified=455,unclassified=419,native_processes=0,arm_compiles=0,current_rom_reconstructions=0,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-NUMERIC / PLR1 exact numeric consumer\n- Version: hof-numeric-v1\n- Status: STOPPED（12件追加分類・実装検証。donor/実保存配線は未完）\n- Summary: {summary}\n- Files changed: numeric classifier/negative suites/Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: new unit={m["unit_tests"]}; bundle108904/image108008/parent pool69165; full1671 policies,1483 owner spans, all-byte/mirror/Thumb exact bundle inventory; old443 accepted rows unchanged. Whole current owner afterSHA equals original linked bundle. ROM/native/ARM0.\n- Boundary: 12件は全件species行境界を跨ぐ。全数値spanの隙間/重複を拒否し両側の証跡を保持。padding1byte/code/machine/headerは除外。unknown419と間接参照完全性は未完、donorは使用しない。正式ROM/Save101/50HOF/opaque1936/baseline/release不変。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; same branch nonforce。\n- Network: fixed existing PLR1 artifact{ORIGINAL[0]} SHA verified。新公開source/minimal address-size-SHA/textのみ、ROM断片/rawhex/ROM/save/runtime/runner/credential0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'all inherited originals retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_RECORDED_PLR1_NUMERIC_FRONTIER',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed numeric text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text with LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only entire old logs retained')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-NUMERIC VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in PROOF|{'failure.json','record.json',*(n for n,_ in SNAPSHOTS)},'closed nonsymlink flat text set');raw=p.read_bytes();need(0<len(raw)<4000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed numeric workflow');globals()[sys.argv[1]]()
