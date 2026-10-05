#!/usr/bin/env python3
"""退役表の型分類と実heap admissionを検証。donor/本番leaseは証明前に有効化しない。"""
import datetime,io,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests'),str(ROOT)]
import pr16_dex_hof_generation_writer_actions as parent
import pr16_dex_hof_storage_actions as prior
import pr16_dex_publication as publication
need,identity,write,git=prior.need,prior.identity,prior.write,prior.git
BASE='561e4c74db9c87699c7d2032183e8e8cbfa9aece'
WF='.github/workflows/pr16-dex-hof-capacity.yml';SELF='scripts/pr16_dex_hof_capacity_actions.py';GUIDE='docs/PR16_DEX_HOF_CAPACITY_JA.md'
CODE={WF,SELF,GUIDE,'scripts/pr16_dex_hof_donor.py','tests/test_pr16_dex_hof_donor.py','overlays/hof_journal/hof_heap.c','overlays/hof_journal/hof_heap.h','tests/test_pr16_hof_heap.c','tools/mgba_pr16_hof_heap.c'}
OLDCP='content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
CP='content/modernization/pr16_dex_hof_capacity_checkpoint.json';EVIDENCE='content/modernization/pr16_dex_hof_capacity_evidence'
STATE=prior.STATE;DOC=prior.DOC;LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-dex-hof-capacity';PUBLIC=ROOT/'public-dex-hof-capacity';ARTIFACT='pr16-dex-hof-capacity-text-only'
SNAPSHOTS=[('fixed-state.json',STATE),('fixed-resume.md',DOC),('fixed-checkpoint.json',CP),('fixed-run-log.md',LOGS[0]),('fixed-version-log.md',LOGS[1])]
PROOF={'measurement.json','heap-host.json','donor-tests.txt','heap-native.json','heap-arm.json','egg-typed-audit.json','heap-binding.json','attempts.json'}

def source_guard():
 import pr16_learnset_runtime_record as g
 prior.current();publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF);g.START=BASE;g.CODE=CODE;g.OWNED=set();g.guard()
 state=json.loads((ROOT/STATE).read_bytes());need(state['pending_runs']==[]and prior.bindings(state['source_bindings'])==state['source_bindings'],'prior bound original text and terminal state retained')
 cp=json.loads((ROOT/OLDCP).read_bytes());need(cp['candidate']['sha256']=='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583','exact latest candidate')

def command(args):
 r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);need(r.returncode==0 and not r.stderr,'strict command '+Path(args[0]).name+': '+r.stderr[-2400:]);return r.stdout

def reconstruct():
 import pr16_dex_hof_main_cow_actions as main
 import pr16_dex_hof_successor as successor
 main.OUT=OUT/'parent';main.OUT.mkdir();_,_,before,_,_=main.reconstruct()
 patches,linked=successor.link(OUT/'old-link');current,placed=successor.apply(before,patches,linked)
 controller=json.loads((ROOT/parent.CP).read_bytes());need(identity(current)==controller['candidate']and linked==controller['link'],'entire controller predecessor reconstruction')
 patches,linked=parent.link(OUT/'current-link');old=successor.checkpoint;latest=dict(candidate=controller['candidate'],isolated=dict(placement=controller['placement'],link=dict(sections=controller['placement']['preserved_hof_sections'])))
 try:successor.checkpoint=lambda:latest;current,placed=successor.apply(current,patches,linked)
 finally:successor.checkpoint=old
 cp=json.loads((ROOT/OLDCP).read_bytes());need(identity(current)==cp['candidate']and linked==cp['link']and placed==cp['placement'],'exact latest0641 allbytes/link/owner placement reconstruction')
 return current,cp

def run():
 import pr16_dex_hof_donor as donor
 import test_pr16_dex_hof_donor as tests
 prior.current();need(not OUT.exists()and not PUBLIC.exists(),'one fresh capacity scope');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
 try:
  stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests));(PUBLIC/'donor-tests.txt').write_text(stream.getvalue());need(test.wasSuccessful(),'new donor negative unit cases')
  host=OUT/'heap-host';command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(ROOT/'tests/test_pr16_hof_heap.c'),str(ROOT/'overlays/hof_journal/hof_heap.c'),'-o',str(host)]);host_result=json.loads(command([str(host)]));write(PUBLIC/'heap-host.json',host_result)
  obj=OUT/'heap.o';command(['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-mthumb-interwork','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'overlays/hof_journal/hof_heap.c'),'-o',str(obj)]);need(not command(['arm-none-eabi-nm','-u',str(obj)]),'admission no unresolved ARM library dependency')
  size=command(['arm-none-eabi-size',str(obj)]).splitlines()[-1].split();stack=[]
  for line in (OUT/'heap.su').read_text().splitlines():
   row=line.split('\t');stack.append(dict(function=row[0].split(':')[-1],bytes=int(row[1]),kind=row[2]))
  ld=OUT/'heap.ld';ld.write_text('SECTIONS { . = 0x02030000; .text : { *(.text*) *(.rodata*) *(.glue_7*) *(.v4_bx) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) } }\n')
  elf=OUT/'heap.elf';binary=OUT/'heap.bin';command(['arm-none-eabi-gcc','-mthumb','-mcpu=arm7tdmi','-nostdlib','-Wl,--build-id=none','-Wl,-e,HH_Admit','-Wl,-T,'+str(ld),str(obj),'-o',str(elf)]);command(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)])
  symbols={line.split()[-1]:int(line.split()[0],16) for line in command(['arm-none-eabi-nm','--defined-only',str(elf)]).splitlines() if len(line.split())==3};entry=symbols['HH_Admit']|1
  arm=dict(text=int(size[0]),data=int(size[1]),bss=int(size[2]),stack=stack,rom_placed=False,isolated_ram_entry=entry,image=identity(binary.read_bytes()));need(arm['data']==arm['bss']==0 and len(binary.read_bytes())<8192,'no mutable static ARM owner');write(PUBLIC/'heap-arm.json',arm)
  current,cp=reconstruct();typed=donor.audit(current,cp);need(typed['candidate']==cp['candidate']and typed['donor_leased']is False,'current candidate typed audit without lease');write(PUBLIC/'egg-typed-audit.json',typed)
  heap=parent.audit_heap_bindings(current);write(PUBLIC/'heap-binding.json',heap)
  candidate=OUT/'candidate.gba';candidate.write_bytes(current)
  need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'exact accepted mGBA runtime')
  native=OUT/'native';command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(ROOT/'tools/mgba_pr16_hof_heap.c'),str(ROOT/'overlays/hof_journal/hof_heap.c'),'-DHH_ADMIT_ARM_ENTRY='+str(entry)+'u','-lmgba','-lm','-o',str(native)])
  attempts.append('new-actual-heap-admission-and-relocation-prefix');write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts));r=subprocess.run([str(native),str(candidate),str(binary)],capture_output=True,text=True,timeout=300)
  if r.stderr:(PUBLIC/'heap-native-stderr.txt').write_text(r.stderr)
  need(r.returncode==0 and not r.stderr,'actual heap native '+str(r.returncode)+' '+r.stderr[-1800:]);n=json.loads(r.stdout);write(PUBLIC/'heap-native.json',n)
  need(n['cases']==15 and n['allocator_calls']==17 and n['calls']==74 and n['arm_admission_calls']==28 and n['native_processes']==1 and n['game_boots']==n['real_saves']==0 and not n['runtime_lease_enabled']and not n['all_save_entries_heap_ready']and not n['formal_save_changed'],'complete exact bounded native scope')
  need(n['status']=='PASS_ACTUAL_ROM_HEAP_ADMISSION_AND_RELOCATION_HAZARD'and n['preflight_rejections_without_alloc']==3 and n['arena_overwritten_before_heap_reset']==13352 and n['relocation_overwrite_bytes']==53300,'all scoped actual allocator and unsafe-lifetime conditions');need(candidate.read_bytes()==current,'whole current candidate unchanged')
  write(PUBLIC/'measurement.json',dict(status='PASS_TYPED_DONOR_FRONTIER_AND_ACTUAL_HEAP_ADMISSION',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(current),candidate_changed=False,donor_unit_tests=test.testsRun,heap_host=host_result,heap_arm=arm,native=n,typed_audit=typed,native_processes=len(attempts),unaffected_native_reruns=0,donor_leased=False,controller_runtime_wired=False,workspace_runtime_owned=False,all_save_entries_heap_ready=False,synchronous_lifetime_integrated=False,formal_rom_changed=False,formal_save_changed=False,source_bindings=prior.bindings(CODE)))
 except Exception as e:write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e).replace(str(ROOT),'.'),native_processes=len(attempts)));raise

def record():
 from pr16_learnset_compact_record import publish_resume
 import pr16_resume
 prior.current();state=json.loads((ROOT/STATE).read_bytes());protected=dict(state['source_bindings']);need(prior.bindings(protected)==protected and not(ROOT/CP).exists(),'unchanged originals and unique capacity record')
 m=json.loads((PUBLIC/'measurement.json').read_bytes());need(m['source_bindings']==prior.bindings(CODE),'exact measured new source');paths=set()
 for name in sorted(PROOF):
  raw=(PUBLIC/name).read_bytes();dest=ROOT/EVIDENCE/name;need(not dest.exists(),'new immutable text evidence');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);paths.add(dest.relative_to(ROOT).as_posix())
 write(ROOT/CP,dict(schema_version=1,**m,guide=GUIDE,evidence_bindings=prior.bindings(paths),record_run=int(os.environ['GITHUB_RUN_ID']),record_source=os.environ['GITHUB_SHA']))
 typed=m['typed_audit'];remaining=typed['unclassified'];classified=typed['classified'];candidate=m['candidate']['sha256']
 summary=f'現候補{candidate}の旧egg見かけ参照をtyped asset/consumerへ機械分類し、{classified}件分類・{remaining}件未知を保持。実heap全chain事前admissionをC実装し、新isolated ARMでfirst-fit/split/整列/解放とOOM前拒否を検証。保存退避入口の実3コピーがarena13352byteをMallocInit前に破壊することも確認。donor/本番arenaは未使用、正式ROM/Save101不変。'
 goal='残る旧egg参照をtyped code/audio/graphics/numeric consumerで分類し、間接参照不在と明示donor移管を証明する。Ccontroller必要容量を確保し、全保存入口のheap-ready・同期非再入・admission→Alloc→全出口Freeを0804B85C入口前に閉じる。controllerと実S61E/MDXを全writer/loader/Link exact-source/no-main/INITIALへ接続。全mode/早期31/species9bit/残typedを受入後に正式候補切替、trainer131後半から最終シオウ通常回復/保存/coldContinue。雑魚毎Saveなし。'
 state['story_dex_owner']['runtime_integration']['hof_capacity']=dict(checkpoint=CP,guide=GUIDE,status=m['status'],candidate=m['candidate'],classified=classified,unclassified=remaining,donor_leased=False,heap_admission_c_implemented=True,isolated_heap_native=m['native'],heap_runtime_lease_enabled=False,controller_runtime_wired=False,source=os.environ['GITHUB_SHA'],run=int(os.environ['GITHUB_RUN_ID']))
 state['bp']['current_stop']=summary;state['bp']['next_step']=goal;state['next_action'].update(id='FINISH_TYPED_DONOR_AND_SYNCHRONOUS_HEAP_LIFETIME',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_HOF_GENERATION_WRITER_JA.md',OLDCP])
 state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='現ROM donor型分類と実allocator隔離検証。全保存入口のheap所有/配線受入ではない。';state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
 state['source_bindings'].update(prior.bindings(CODE|paths|{CP}));state['do_not_repeat'].append('HOF容量/heap専用checkpointの型分類と新isolated allocator試験をsource/候補不変なら再走しない。donor0/本番lease0。heap退避は0804B85C入口から既に危険で、MallocInit直前解放では遅い。全入口heap-ready/非再入/全出口Free未完。')
 state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],donor_unit_tests=m['donor_unit_tests'],heap_host=m['heap_host'],new_native_processes=1,native=m['native'],current_candidate=m['candidate'],donor_leased=False,heap_runtime_lease_enabled=False,general_ci_known_source_mismatch_not_resolved=True,stage79_cached_not_new_native=True,reason_ja=summary)
 publish_resume(state);pr16_resume.validate(ROOT);stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: USER-20261005-DEX-HOF-CAPACITY / typed donor監査と実heap事前admission\n- Version: hof-capacity-v1\n- Status: STOPPED（限定実装・検証完了。donor/保存runtime配線は未完）\n- Summary: {summary}\n- Files changed: 新classifier/C admission/host/native/Actions/guide/CP/text evidence、固定MDJSON、両ログ。\n- Verify: donor unit{m["donor_unit_tests"]}; heap host={json.dumps(m["heap_host"],sort_keys=True)}; native={json.dumps(m["native"],sort_keys=True)}; ARM={json.dumps(m["heap_arm"],sort_keys=True)}。旧native再走0、現ROM全SHA/115owner配置再構成一致。\n- Boundary: 874見かけ参照を親12abでなく現候補へ再束縛。未分類のdata仮定除外なし。Alloc OOM assert前に全chain拒否。root.prev=self、raw13359/round13360/align8、Freeはraw。保存前53300byte退避の開始からarena禁止。全入口heap-ready・同期排他・lifetime・本番controllerは未完。正式ROM/Save101/50HOF履歴/1936suffix/baseline/release不変。\n- Next: {goal}\n- Commit: source={os.environ["GITHUB_SHA"]}; samebranch非force。\n- Network: 同repoActions/既存private inputs。公開はsource/minimal address-size-SHA/text、ROM断片/rawhex/ROM/save/runtime/runner/credentials追加公開0。\n'
 for path in LOGS:
  with(ROOT/path).open('a')as out:out.write(entry)
 need(prior.bindings(protected)==protected,'every earlier source byte retained');owned={STATE,DOC,CP,*LOGS}|paths;write(OUT/'owned.json',sorted(owned));git('add','--',*sorted(owned));write(PUBLIC/'record.json',dict(status='PASS_RECORDED_HOF_CAPACITY_FRONTIER',source_head=os.environ['GITHUB_SHA'],record_run=int(os.environ['GITHUB_RUN_ID']),native_processes=1))

def guard():
 import pr16_resume,pr16_learnset_runtime_record as g
 prior.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
 receipt=json.loads((PUBLIC/'record.json').read_bytes());receipt['final_head']=git('rev-parse','HEAD').decode().strip();receipt['final_blobs']={}
 for path in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+path)==(ROOT/path).read_bytes(),'whole committed owned text')
 for name,path in SNAPSHOTS:
  raw=git('show','HEAD:'+path);need(raw==(ROOT/path).read_bytes()and raw.endswith(b'\n'),'whole committed text with LF');(PUBLIC/name).write_bytes(raw);receipt['final_blobs'][path]=dict(**identity(raw),git_blob_sha=git('rev-parse','HEAD:'+path).decode().strip(),trailing_newline=True)
 for path in LOGS:need(git('show','HEAD:'+path).startswith(git('show',BASE+':'+path)),'append-only entire old logs retained')
 write(PUBLIC/'record.json',receipt);print('RESULT=STOPPED TASK=USER-20261005-DEX-HOF-CAPACITY VERIFY=PASS COMMIT='+receipt['final_head'])
def export():
 publication.output(PUBLIC)
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink()and not p.name.startswith('.')and p.name in PROOF|{'failure.json','record.json','heap-native-stderr.txt',*(n for n,_ in SNAPSHOTS)},'closed nonsymlink flat text set');raw=p.read_bytes();need(0<len(raw)<4000000 and raw.endswith(b'\n')and b'\0'not in raw,'bounded complete nonempty text');raw.decode('utf8')
  if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('source_guard','run','record','guard','snapshot','export'),'closed capacity workflow');globals()[sys.argv[1]]()
