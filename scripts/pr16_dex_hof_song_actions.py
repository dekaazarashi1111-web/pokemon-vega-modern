#!/usr/bin/env python3
"""現在候補の新song型consumerを検証・記録。旧native/inventoryの再走はしない。"""
import datetime,io,json,os,sys,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_actions as prior
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='47d4624f92fb32cdbce0e878eccc111aa2cd93d4'
WF='.github/workflows/pr16-dex-hof-song.yml';SELF='scripts/pr16_dex_hof_song_actions.py';GUIDE='docs/PR16_DEX_HOF_SONG_JA.md'
SOURCES='content/modernization/pr16_dex_hof_song_sources.json';ENGINE='content/modernization/pr16_dex_hof_song_engine_review.json'
CODE={WF,SELF,GUIDE,SOURCES,ENGINE,'scripts/pr16_dex_hof_song.py','tests/test_pr16_dex_hof_song.py'}
OLDCP='content/modernization/pr16_dex_hof_numeric_checkpoint.json';INVENTORY='content/modernization/pr16_dex_hof_numeric_evidence/egg-typed-audit.json'
LATEST='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_song_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_song_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-song';PUBLIC=ROOT/'public-dex-hof-song';ARTIFACT='pr16-dex-hof-song-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','song-tests.txt','egg-typed-audit.json'}


def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'all inherited sources and terminal state')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']['sha256']=='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'and cp['classified']==455 and cp['unclassified']==419,'exact numeric frontier')
 need(cp['evidence_bindings'][INVENTORY]==identity((ROOT/INVENTORY).read_bytes()),'whole inherited typed inventory original')


def public_sources():
 import pr16_dex_hof_song as song
 directory=OUT/'pinned-public-sources';directory.mkdir();manifest=json.loads((ROOT/SOURCES).read_bytes())
 for row in manifest:
  path=directory/row['local'];repo=row['repository'];commit=row['commit'];source=row['source']
  need(repo in('kapibarasan000/CFRU-JP','pret/pokefirered')and len(commit)==40 and '..'not in source and '/'not in row['local'],'closed official source paths')
  existing=ROOT/'vendor/upstream/CFRU-JP'/source
  if repo=='kapibarasan000/CFRU-JP'and existing.is_file()and identity(existing.read_bytes())=={k:row[k]for k in('size','sha256')}:raw=existing.read_bytes()
  else:
   url=f'https://raw.githubusercontent.com/{repo}/{commit}/{source}'
   with urllib.request.urlopen(url,timeout=90)as response:raw=response.read(row['size']+1)
  need(identity(raw)=={k:row[k]for k in('size','sha256')},'fixed public source download '+row['local']);path.write_bytes(raw)
 return song.verify_sources(directory,manifest,json.loads((ROOT/'state/source-lock.json').read_bytes()))


def run():
 import pr16_dex_hof_song as song
 import pr16_dex_hof_capacity_actions as reconstruction
 import test_pr16_dex_hof_song as tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh song observation');OUT.mkdir(parents=True);PUBLIC.mkdir();reconstructed=0
 try:
  stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));(PUBLIC/'song-tests.txt').write_text(stream.getvalue());need(result.wasSuccessful(),'new fail-closed song suites')
  sources,bindings=public_sources()
  # Earlier private candidates were intentionally not published. Reconstruct once only
  # to read the new engine/song scope; do not run prior inventory or native functions.
  reconstruction.OUT=OUT/'current';reconstruction.OUT.mkdir();current,latest=reconstruction.reconstruct();reconstructed=1
  need(identity(current)==song.CANDIDATE==latest['candidate'],'whole current candidate reconstruction')
  owners=song.prior.bind_owners(current,latest);need(len(owners)==115,'all actual latest owner afterSHA bindings')
  engine=song.bind_engine(current,json.loads((ROOT/ENGINE).read_bytes()))
  inherited=json.loads((ROOT/INVENTORY).read_bytes());audit=song.extend(current,inherited,engine,sources,bindings)
  extension=audit['song_extension'];need(extension['newly_classified']>0 and audit['classified']+audit['unclassified']==874,'positive bounded typed frontier change')
  write(PUBLIC/'egg-typed-audit.json',audit)
  m=dict(status='PASS_CURRENT_ROOTED_SONG_TYPED_CLASSIFICATION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,unit_tests=result.testsRun,
    classified=audit['classified'],unclassified=audit['unclassified'],newly_classified=extension['newly_classified'],explicit_source_ids=extension['explicit_source_ids'],complete_modeled_songs=extension['accepted_complete_songs'],sample_witnesses=len(extension['asset_witnesses']),footsteps=extension['footsteps'],
    old_inventory_candidates=874,all_prior_accepted_retained=True,old_full_rom_inventory_reused=True,typed_audit_identity=identity((PUBLIC/'egg-typed-audit.json').read_bytes()),source_bindings=prior.bindings(CODE),inherited_bindings=prior.bindings({OLDCP,INVENTORY,LATEST,'state/source-lock.json'}),
    public_source_bindings=bindings,engine_review_binding=identity((ROOT/ENGINE).read_bytes()),current_owner_count=len(owners),current_rom_reconstructions=reconstructed,
    accepted_link_reconstruction_for_new_read_only_scope=True,unaffected_native_reruns=0,native_processes=0,old_full_rom_scan_runs=0,donor_leased=False,donor_eligible=False,complete_runtime_audio_read_footprint_claimed=False,indirect_reference_completeness_claimed=False,
    controller_runtime_wired=False,formal_rom_changed=False,formal_save_changed=False)
  write(PUBLIC/'measurement.json',m)
 except Exception as exc:
  write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(exc).__name__,message=str(exc).replace(str(ROOT),'.'),native_processes=0,current_rom_reconstructions=reconstructed));raise


def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'unchanged originals and unique song CP')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());need(m['source_bindings']==prior.bindings(CODE)and m['inherited_bindings']==prior.bindings(m['inherited_bindings']),'all measured source bytes');paths=set()
 for name in sorted(PROOF):
  dest=ROOT/EVIDENCE/name;need(not dest.exists(),'immutable song evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((PUBLIC/name).read_bytes());paths.add(dest.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),prior_checkpoint=OLDCP,current_owner_checkpoint=LATEST,record_source=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID'])))
 summary=f'現候補0641af70の旧egg874参照に根付きJP song interpreterを実装。{m["explicit_source_ids"]}個の明示ID、{m["complete_modeled_songs"]}曲の完全モデル、{m["sample_witnesses"]}sample witnessから{m["newly_classified"]}件を追加し、{m["classified"]}分類/{m["unclassified"]}未知。footstep MIDIと現Song250/251の不一致も保持。新{m["unit_tests"]}tests、現候補の新read用再構成1回、旧inventory/native0。donor/正式ROM/Save101不変。'
 goal=f'残{m["unclassified"]}件の未対応song/audio/numeric/codeを根付きconsumerへ結び、間接参照・退役完全性を証明する。今回のsample prefix分類をDPCM全read footprintや実演奏受入と混同しない。未知0と退役ゲート後のみ必要分を明示donor移管し、Ccontroller実owner配置・全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL・同期heap lifetime・全mode/早期31/species9bitを閉じる。その後正式候補切替、trainer131後半から最終シオウ通常回復/保存/独立coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_song']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=m['classified'],unclassified=m['unclassified'],newly_classified=m['newly_classified'],donor_leased=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_REMAINING_TYPED_DONOR_CONSUMERS',goal_ja=goal,read_paths=[GUIDE,CP,'scripts/pr16_dex_hof_song.py','docs/PR16_DEX_HOF_NUMERIC_JA.md',OLDCP])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='JP engine窓に再束縛したsong型consumer分類source。実演奏・donor移管・本番controller配線は未受入。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append(summary+'候補/source不変なら旧全ROM走査/heap/native/習得原本生成を再走しない。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],song_unit_tests=m['unit_tests'],classified=m['classified'],unclassified=m['unclassified'],native_processes=0,current_rom_reconstructions=1,current_candidate=m['candidate'],donor_leased=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-SONG / 根付きJP song consumer分類\n- Version: hof-song-v1\n- Status: STOPPED（新song分類を実装検証。donor/本番保存配線は未完）\n- Summary: {summary}\n- Files changed: classifier/negative suites/source pins/engine semantic review/Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: unit={m["unit_tests"]}; 現candidate全SHA/115owner afterSHA、JP全engine窓/effective36slot/4player容量/114source IDs、全命令/VOICE/1段split/rhythm/Wave chain。全旧455accepted不変、全874hit bytes再照合、旧全ROMscan/native0。\n- Boundary: 全song横断の構造/command/sample競合拒否、失敗track/VOICE-only読取も保護。MEMACC/XCMD/PORT/tempo0/non-yield/budgetは拒否。source MIDIと現Songの不一致を成功へ読み替えない。最小DPCM prefixと全実read footprintを分離。donor0、正式ROM/Save101/50HOF/opaque1936/baseline/release不変。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force。\n- Network: 同repoActions/既存private inputs、固定CFRU/pret19source blob。公開source/minimal address-size-SHA/textのみ、ROM断片/rawhex/ROM/save/MIDI/WAV/runtime/runner/credential追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'all inherited originals retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_RECORDED_ROOTED_SONG_FRONTIER',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=0))


def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed song text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text with LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only entire old logs retained')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-SONG VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in PROOF|{'failure.json','record.json',*(n for n,_ in SNAPSHOTS)},'closed nonsymlink flat text set');raw=p.read_bytes();need(0<len(raw)<8000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed song workflow');globals()[sys.argv[1]]()
