#!/usr/bin/env python3
"""Drought空loaderの未完cursorだけをnativeで修復し、実17勝後の復帰と保存を検証。"""
from pathlib import Path
import inspect
import json
import os
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_taunt as previous
c,probe=previous.c,previous.probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_drought.py'
TEST='tests/test_pr16_circus_drought.py'
SOURCE='overlays/circus_streak/circus_drought.c'
HEADER='overlays/circus_streak/circus_drought.h'
FIXTURE='tests/fixtures/circus_drought_fixture.c'
WATCH='tools/mgba_pr16_circus_drought_watch.h'
WORKFLOW='.github/workflows/pr16-circus-drought.yml'
REPORT='content/modernization/pr16_circus_drought.json'
CPU='content/modernization/pr16_circus_win_return_cpu.json'
ROWS='evidence/pr16_circus_win_return_cpu/35433308048/cpu-rows.json'
RAW='evidence/pr16_circus_taunt/35430246002/native/'+probe.CASE+'.stderr'
TASK='USER-20260919-CIRCUS-DROUGHT'
OUT=ROOT/'.local/pr16-circus-drought'
FILES=tuple(dict.fromkeys((SELF,TEST,SOURCE,HEADER,FIXTURE,WATCH,WORKFLOW,CPU,ROWS,RAW,*previous.FILES)))
PARENT=dict(size=33554432,sha256='3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')
RESERVE=8192
RUNTIME='pr16_circus_drought_empty_loader'
TABLE=0x389A0C
NEXT='新候補の実17勝後復帰とnative完了cursor/集計/原party600/owner64/通常Save/fresh Continueを画像込みで確認。真正30勝/90BPが未達なら最初の新敗北から入力だけを改善し、達成後に正規特性抑制を別検証する。旧診断/受入単体/旧2linkを再実行しない。'


def diagnosis(rows):
    need(len(rows)==21 and [r['elapsed'] for r in rows]==[1,*range(30,601,30)],'CPU original sample endpoints')
    need(all(r['weather_id']==12 and r['weather_init']==0x0807AD09 for r in rows),'weather12 initializer original')
    tail=rows[1:]
    need(all(bytes.fromhex(r['weather'])[0x14:0x16]==b'\x02\x00' and bytes.fromhex(r['weather'])[0x1a]==0 for r in tail),'state2 incomplete original')
    need(sum(0x0807A374<=r['pc']<=0x0807A3BC or 0x0807AD1E<=r['pc']<=0x0807AE20 for r in tail)>=16,'native busy loop original')
    return dict(weather=12,init_all=0x0807AD09,step=0x0807AD39,empty_loader=0x0807A351,
        state=2,observed_frames=600,observed_points=21,ready_zero_hypothesis_rejected=True,
        cause_ja='Drought initAllはstate2のpalette loaderをbusy-loop。FRLG由来loaderは空実装でcursor1が32へ進まず、weather完了もtask再開も来ない。',
        upstream_reference=dict(repository='pret/pokefirered',path='src/field_weather.c',blob_sha='56cf6505bd381fde0aaa9a704cc4e997b5f934d2',
            symbols=['LoadDroughtWeatherPalette','ResetDroughtWeatherPaletteLoading','LoadDroughtWeatherPalettes'],
            note_ja='上流は空loaderと本来のterminal32をコメントで明示。実候補のBX LR preimageと呼出し/初期化命令もbuild前に照合し、上流同名だけではpatchしない。'))


def verify_prefix(events,raw):
    previous.verify_prefix(events,raw)
    old=probe.parse((ROOT/RAW).read_bytes())
    need(len(old)==80 and old[78]['label']=='outcome' and old[78]['outcome']==1,'real seventeenth WIN original')
    need(events[:79]==old[:79],'seventeen real battle prefix changed before repaired return')


def policy_text(base,headers):return previous.policy_text(base,headers)+'\n'+(ROOT/WATCH).read_text()

def configure():
    previous.configure()
    for k,v in dict(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,OUT=OUT,
        FILES=FILES,policy_text=policy_text,verify_prefix=verify_prefix,probe=probe).items():setattr(c,k,v)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value))
    state['circus_drought_followup']=loss['drought_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35433308048/job105871614193はCPU21点/600frameの読取診断SUCCESS。native受入ではない。weather12のinitAll0807ad09/state2/空loader0807a350に停止を特定。同候補の17戦診断は再実行せず、後継ROMの新検証だけを行う。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    failure_note='run35434401185/job105874514732はCPU JSON arrayをobject専用readerへ渡してprepare停止。ARM link0/native0。array reader修復後の未実行build/nativeだけを進め、旧failureは保持。'
    if failure_note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,failure_note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。変更はweather12 initAll table4byteと新規tail payloadだけ。旧全allocation不変/rollback/独立2linkを確認し、旧LOSS/BP/Ring/Save ownerは変更しない。新候補の未完continuationだけ実行。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT);need(not (ROOT/REPORT).exists(),'Drought attempt exists; inspect original, do not replay')
    cpu=resume.load(ROOT,CPU);run=r.api('actions/runs/35433308048')
    need(run['status']=='completed' and run['conclusion']=='success' and cpu['classification']=='CIRCUS_WIN_CPU_READONLY_COMPLETE','CPU original incomplete')
    for p,bound in cpu['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'CPU raw changed: '+p)
    actions=[{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    for p in resume.load(ROOT,resume.STATE)['pending_runs']:
        if p['run_id']!=run['id']:
            a=r.api('actions/runs/'+str(p['run_id']));actions.append({k:a[k] for k in ('id','head_sha','status','conclusion')})
    failed=r.api('actions/runs/35434401185')
    need(failed['status']=='completed' and failed['conclusion']=='failure' and failed['head_sha']=='c7c28f4cd20d16dfe3ec90b492798a0e34b35323','array-reader failure differs')
    actions.append({k:failed[k] for k in ('id','head_sha','status','conclusion')})
    value=dict(schema_version=1,classification='CIRCUS_DROUGHT_NATIVE_REPAIR_PREPARED',parent=PARENT,
        preparation_failures=[dict(run_id=35434401185,job_id=105874514732,original_conclusion='failure',native_processes=0,arm_links=0,reason_ja='CPU原本はarrayだがobject専用resume.loadを呼びprepare停止。listのままJSON decodeし、prepare経路を回帰検査。')],
        diagnosis=diagnosis(json.loads((ROOT/ROWS).read_bytes())),actions_reconciled=actions,host_tests=r.tests([Path(TEST).name]),
        accepted_native_cases_replayed=0,independent_old_arm_links_replayed=0,unavoidable_prefix_battles=17,
        genuine_30_wins_verified=False,win_return_native_verified=False,visual_review_completed=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    checkpoint(value,'PREPARED','実17勝後は未実装Drought palette loaderのcursorが進まずstate2で無限待機。CircusWIN/有効ownerとledger/正規script/weather12だけをguardし、空loader cursor2byte以外はnative初期化へ委譲する修正を準備。')


def verify_preimage(raw):
    need(identity(raw)==PARENT,'fixed Drought parent identity')
    checks={0x7A350:bytes.fromhex('70470000'),TABLE:struct.pack('<I',0x0807AD09),
        0x389940:struct.pack('<I',0x02037E68),0x7AD08:bytes.fromhex('10b5fff7e3ff'),
        0x7AD90:bytes.fromhex('fff7e0fa')}
    for at,before in checks.items():need(raw[at:at+len(before)]==before,'Drought preimage differs at '+hex(at))
    return {hex(at):identity(before) for at,before in checks.items()}


def compile_bridge(folder,address,armed):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'circus_drought_addresses.h').write_text(f'#define CIRCUS_DROUGHT_ARMED 0x{armed:08X}u\n')
    ld=folder/'bridge.ld';ld.write_text(f'ENTRY(CircusDroughtInitAll)\nSECTIONS {{ . = 0x{address:08X}; .text : {{ KEEP(*(.text.CircusDroughtInitAll)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }} }}\n')
    elf=folder/'bridge.elf';binary=folder/'bridge.bin'
    args=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
        '-Wall','-Wextra','-Werror','-fstack-usage','-DVEGA_SAVE_ROM_RUNTIME=1','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
        '-T',str(ld),'-I',str(folder),'-I',str(ROOT/'overlays/circus_streak'),str(ROOT/SOURCE),str(ROOT/'overlays/save_migration/save_migration.c'),'-o',str(elf)]
    result=subprocess.run(args,cwd=folder,capture_output=True,text=True)
    (folder/'compile.stdout').write_text(result.stdout);(folder/'compile.stderr').write_text(result.stderr)
    need(result.returncode==0,'Drought ARM compile: '+result.stderr[-3000:])
    need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)])==b'','unresolved ARM symbol')
    syms=subprocess.check_output(['arm-none-eabi-nm','-n','--defined-only',str(elf)],text=True)
    rows=[l.split() for l in syms.splitlines() if len(l.split())==3]
    need(not any(r[1] in 'bBdD' for r in rows),'writable static state prohibited')
    entry=[int(r[0],16)|1 for r in rows if r[2]=='CircusDroughtInitAll'];need(entry==[address|1],'entry placement')
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes();need(64<len(payload)<=RESERVE,'payload bound')
    (folder/'symbols.txt').write_text(syms)
    (folder/'disassembly.txt').write_text(subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True).replace(str(elf),'drought.elf'))
    usage='\n'.join(p.read_text() for p in folder.glob('*.su'));(folder/'stack-usage.txt').write_text(usage)
    sizes=[int(l.split('\t')[1]) for l in usage.splitlines() if 'CircusDroughtInitAll' in l]
    need(sizes and max(sizes)<=128,'Drought stack bound')
    return payload,entry[0]


def reconstruct():
    configure();c.f.reconstruct()
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    from pr16_bp_party_retention_successor import existing_requests
    import pr16_ring_npc_successor as gift
    from tools.rom_allocator import build_allocation_report_from_csv
    raw=(n.INPUT/'candidate.gba').read_bytes();old=json.loads((n.INPUT/'report.json').read_bytes());checks=verify_preimage(raw)
    (OUT/'parent.gba').write_bytes(raw);(OUT/'parent-recipe.json').write_bytes(stable(old))
    for at,size in ((0x0807A330,160),(0x0807ACD4,352),(0x08389A04,16)):
        text=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma=0x08000000',
            '--start-address='+hex(at),'--stop-address='+hex(at+size),str(n.INPUT/'candidate.gba')],text=True,cwd=ROOT)
        (OUT/('parent-'+hex(at)+'.txt')).write_text(text.replace(str(ROOT)+'/',''))
    requests=existing_requests(old['allocation']);need(not any(r['name']==RUNTIME for r in requests),'allocation exists')
    req=dict(name=RUNTIME,region='future_tail',size=RESERVE,alignment=4,owner=TASK,purpose='Circus WIN only native empty Drought loader termination',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req]);off=next(r['start'] for r in preview['allocations'] if r['name']==RUNTIME)
    builds=[compile_bridge(OUT/('compile-'+str(i)),0x08000000+off,old['entries']['CircusStreakRuntimeArmed']) for i in (1,2)]
    need(builds[0]==builds[1],'independent Drought ARM links differ');payload,entry=builds[0]
    need(raw[off:off+len(payload)]==b'\xff'*len(payload),'new tail must be erased')
    patches=[dict(name='drought-empty-loader',offset=off,before=raw[off:off+len(payload)].hex(),after=payload.hex()),
        dict(name='drought-init-all-table',offset=TABLE,before=raw[TABLE:TABLE+4].hex(),after=struct.pack('<I',entry).hex())]
    new=bounded_patch(raw,patches);req.update(start=off,size=len(payload),content_sha256=identity(payload)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req]);need(allocation['summaries']['overlap_count']==0,'allocation overlap')
    for row in allocation['allocations']:need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'existing allocation changed: '+row['name'])
    recipe=dict(old,parent=PARENT,candidate=identity(new),patches=patches,allocation=allocation,
        entries=dict(old['entries'],CircusDroughtInitAll=entry),independent_arm_links=2,independent_old_arm_links_replayed=0,
        whole_rom_rollback_matches_parent=True,changed_existing_allocations=[],parent_patch_recipe=identity(stable(old)),
        payload=dict(offset=off,**identity(payload)),preimage_checks=checks,status='BUILT_CIRCUS_DROUGHT_NATIVE_OPEN',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),run_id=int(os.environ['GITHUB_RUN_ID']))
    recipe['source_bindings']={**old['source_bindings'],**{p:identity((ROOT/p).read_bytes()) for p in FILES}}
    recipe['change_impact']=dict(rom_ranges=[dict(offset=p['offset'],size=len(bytes.fromhex(p['before'])),purpose=p['name']) for p in patches],
        old_allocations_unchanged=True,old_loss_guard_unchanged=True,save_owners_unchanged=True,
        native_write_scope=['weather.loadDroughtPalsIndex','weather.loadDroughtPalsOffset'],
        native_write_scope_excludes=['weather.initState','weather.weatherGfxLoaded','streak','BP','party','outcome','task','script','PC','RNG'],
        required_new_case='17 real wins unchanged prefix, repaired field return, remaining real continuation, original600/owner64/Save/fresh Continue',
        excluded_replays=['BP standalone','Ring standalone','cold-load abort standalone','three-win standalone','old ARM links'])
    (OUT/'build.json').write_bytes(stable(recipe));(OUT/'candidate.gba').write_bytes(new)
    (n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))
    need(identity((OUT/'parent.gba').read_bytes())==PARENT,'parent changed')
    print(json.dumps(dict(candidate=recipe['candidate'],payload=recipe['payload'],independent_ARM_links=2,rollback=True)))


def return_witness(raw):
    rows=[json.loads(l[len(b'CIRCUS_DROUGHT_RETURN '):]) for l in raw.splitlines() if l.startswith(b'CIRCUS_DROUGHT_RETURN ')]
    need(len(rows)==1,'native Drought return witness absent/duplicate');r=rows[0]
    for k,v in dict(state=5,complete=1,index=32,offset=32,current=16,outcome=1).items():need(type(r[k]) is int and r[k]==v,'Drought native return '+k)
    need(type(r['brightness']) is int and 0<=r['brightness']<=6,'native brightness range')
    need(r['script']==0x09FF4D77,'native return script');return r


def native():
    configure();import pr16_streak_native as n
    import pr16_circus_win_return_trace as trace
    recipe=json.loads((OUT/'build.json').read_bytes());probe.SHA=recipe['candidate']['sha256']
    ns=dict(c.__dict__);ns['chained_watch']=trace.chained_watch
    exec(compile(trace.chained_native_source(),SELF+':return-watch','exec'),ns)
    target_failure=None
    try:ns['native']()
    except ValueError as error:
        need(str(error)=='genuine 30-win target remains open','Drought native failed: '+str(error));target_failure=str(error)
    report=json.loads((OUT/'native/report.json').read_bytes());summary=json.loads((OUT/'native/streak.json').read_bytes())
    raw=(OUT/'native'/(probe.CASE+'.stderr')).read_bytes();events=probe.parse(raw);verify_prefix(events,(ROOT/c.PREFIX).read_bytes())
    witness=return_witness(raw)
    need(report['status']=='PASS_CIRCUS_SCOPED_NATIVE' and summary['wins']>=17 and [r['label'] for r in events[-2:]]==['saved','reloaded'],'native continuation/save missing')
    need(events[79]['label']=='settled' and events[79]['battle']==16 and probe.owner(bytes.fromhex(events[79]['owner']))['current']==17,'seventeenth real settlement missing')
    result=dict(classification='CIRCUS_DROUGHT_RETURN_SAVE_CONTINUE_NATIVE_VERIFIED',witness=witness,
        actual_wins=summary['wins'],actual_losses=summary['losses'],genuine_30_wins_verified=summary['genuine_30_wins_verified'],
        target_check_failure=target_failure,native_prefix_events_identical=79,old_accepted_cases_replayed=0,
        standard_save_fresh_continue=True,owner_bytes_verified=64,original_party_bytes_verified=600)
    (OUT/'return-result.json').write_bytes(stable(result));print(json.dumps(result,ensure_ascii=False))


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_DROUGHT_NATIVE_OPEN'
    if (OUT/'build.json').exists():value['build']=json.loads((OUT/'build.json').read_bytes());value['candidate']=value['build']['candidate']
    if (OUT/'native/report.json').exists():value['native']=json.loads((OUT/'native/report.json').read_bytes())
    if (OUT/'return-result.json').exists():
        value['return_result']=json.loads((OUT/'return-result.json').read_bytes());value['classification']=value['return_result']['classification']
        value['win_return_native_verified']=True;value['genuine_30_wins_verified']=value['return_result']['genuine_30_wins_verified']
        value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'text evidence only')
        name='evidence/pr16_circus_drought/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        q=ROOT/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    checkpoint(value,'RECORDED','Drought空loader修正の独立2link/全ROM rollback/原本を記録。native17勝後復帰='+str(value['win_return_native_verified'])+'、真正30勝='+str(value['genuine_30_wins_verified'])+'。画像レビュー/正規特性抑制/P08/releaseは別ゲート。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
