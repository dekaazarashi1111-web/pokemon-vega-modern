#!/usr/bin/env python3
"""Circus cold-load tail保護bridgeを2独立linkし、影響する中断復旧を検証。"""
from pathlib import Path
import hashlib
import inspect
import json
import os
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_coldboot.py'
TEST='tests/test_pr16_circus_coldboot.py'
FIXTURE='tests/fixtures/circus_cold_load_fixture.c'
SOURCE='overlays/circus_streak/circus_streak_cold_load.c'
CONTROLLER='tools/mgba_pr16_circus_coldboot.c'
PROBE='scripts/pr16_circus_coldboot_probe.py'
WORKFLOW='.github/workflows/pr16-circus-coldboot.yml'
REPORT='content/modernization/pr16_circus_coldboot.json'
TASK='USER-20260919-CIRCUS-COLD-LOAD'
FILES=(SELF,TEST,FIXTURE,SOURCE,CONTROLLER,PROBE,WORKFLOW)
OUT=ROOT/'.local/pr16-circus-coldboot'
NATIVE=OUT/'native'
OWNER='overlays/circus_streak/circus_streak.c'
OWNER_H='overlays/circus_streak/circus_streak.h'
RUNTIME='pr16_circus_cold_load_bridge'
PARENT=dict(size=33554432,sha256='3b5f919958bf72bad9aa5b466215f33311f9c8c19e1f7f409303416eab952d5d')
AUTOSAVE_SOURCE='overlays/factory_high_modes_v2/factory_high_modes_v2.c'
SAVE_SOURCE='overlays/qol_production/qol_production.c'
SAVE_LOAD_LITERAL=0xDB4E8
BASE=0x08000000
RESERVE=2048


def need(value,message):
    if not value:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def configure():
    import pr16_circus_three_win as b
    b.SELF=SELF;b.TEST=TEST;b.WORKFLOW=WORKFLOW;b.HEADER=CONTROLLER;b.rec.TASK=TASK
    b.OUT.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    return b


def autosave_contract(text):
    # 正常自動Save2回は既存codeの仕様。旧probeが予想した0回へ処理を書換えない。
    start=text.index('static u16 restore_original(u8 reset_streak)\n{')
    end=text.index('\nstatic void repair_shiny_journal',start)
    body=text[start:end]
    need(body.count('if (!persist_current())')==2,'Factory restore no longer has two commits')
    need(body.index('VEGA_FACTORY_RESTORE_PENDING')<body.index('if (!persist_current())')
        <body.index('copy_bytes(G_PLAYER_PARTY')<body.index('G_LEDGER->factory.snapshot_valid = 0u;')
        <body.rindex('if (!persist_current())'),'Factory two-phase recovery order differs')
    return dict(source=AUTOSAVE_SOURCE,function='restore_original',automatic_recovery_saves=2,
        source_identity=identity(text.encode()),function_identity=identity(body.encode()),
        scope_ja='復旧前markerのcommitと、原party復元/snapshot消去後commit。通常Save1回と別に数える。')


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value))
    loss['cold_boot_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    r.SELF=SELF;r.TEST=TEST;r.HEADER=CONTROLLER;r.WORKFLOW=WORKFLOW;r.TASK=TASK
    r.checkpoint(state,loss,stop,
        'cold-load bridgeの実1勝→第2戦中断→ABORT一度/best1→通常Save/別coreを原本で確認。未完の実3勝/9BPと真正30連勝は別ゲートのまま。',
        [REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+('。2独立ARM linkと全ROM rollbackの構築原本を保存。' if value.get('build') else '。host契約を検証。ARM linkとnativeは未実行。')+'既存Factoryの自動Save2回は変更せず、未完戦を加算しない64byteを検証。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'cold-load attempt already recorded; inspect original before changing')
    old=resume.load(ROOT,'content/modernization/pr16_circus_interruption.json')
    need(old['recording_run']==35420622910 and old['classification']=='CIRCUS_INTERRUPTION_DIAGNOSTIC_OPEN','interruption predecessor differs')
    run=r.api('actions/runs/35420622910')
    need(run['status']=='completed' and run['conclusion']=='failure','interruption Actions not a completed failure')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'old raw changed')
    import pr16_circus_drain as drain
    path='evidence/pr16_circus_interruption/35420622910/circus-interrupt-second-battle.stderr'
    diagnosis=drain.recovery_diagnosis((ROOT/path).read_bytes())
    value=dict(schema_version=1,classification='CIRCUS_COLD_LOAD_BRIDGE_PREPARED_NATIVE_OPEN',
        parent=PARENT,original_trace=diagnosis,original_trace_identity=identity((ROOT/path).read_bytes()),
        automatic_save_contract=autosave_contract((ROOT/AUTOSAVE_SOURCE).read_text()),
        host_tests=r.tests([Path(TEST).name]),
        old_failed_probe_preserved=True,old_failed_run=35420622910,
        save_count_contract_ja='実既存codeは中断復旧で2回の自動Saveを行う。旧probeの全Save0回という予測だけを訂正し、自動2/通常1を区別。旧原本のbest0は新probeでも失敗。CRC64/実勝利/ABORT一度/原party600は弱めない。',
        changed_rom_scope_ja='新規Thumb bridgeと既存save-load literalの4byteのみ。旧loadへ一度委譲し、CRC-validなCircus tail64を委譲前に復元。旧Factory/cold field復旧/乱数/能力/party/戦闘scriptは不変。',
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    checkpoint(value,'PREPARED','ロード中の既存Factory自動Save2回でCircus tail64が消える原本を固定。CRC-validなtailを委譲前に保護するbridgeと、512bit破損/256返値/別ID/二重ABORTのhost検証を追加。')


def compile_bridge(folder,address,previous):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'circus_cold_load_addresses.h').write_text(f'#define CIRCUS_COLD_PREVIOUS_LOAD 0x{previous:08X}u\n')
    linker=folder/'bridge.ld'
    linker.write_text(f'ENTRY(CircusStreakColdLoad)\nSECTIONS {{ . = 0x{address:08X}; .text : {{ KEEP(*(.text.CircusStreakColdLoad)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }} }}\n')
    elf=folder/'bridge.elf';binary=folder/'bridge.bin'
    args=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
        '-Wall','-Wextra','-Werror','-fstack-usage','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
        '-T',str(linker),'-I',str(folder),'-I',str(ROOT/'overlays/circus_streak'),str(ROOT/SOURCE),str(ROOT/OWNER),'-o',str(elf)]
    result=subprocess.run(args,cwd=folder,capture_output=True,text=True)
    (folder/'compile.stdout').write_text(result.stdout);(folder/'compile.stderr').write_text(result.stderr)
    need(result.returncode==0,'cold-load ARM compile failed: '+result.stderr[-3000:])
    need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)])==b'','cold-load unresolved ARM symbol')
    symbols=subprocess.check_output(['arm-none-eabi-nm','-n','--defined-only',str(elf)],text=True)
    lines=[l.split() for l in symbols.splitlines() if len(l.split())==3]
    need(not any(r[1] in 'bBdD' for r in lines),'cold-load writable static state prohibited')
    entry=[int(r[0],16)|1 for r in lines if r[2]=='CircusStreakColdLoad']
    need(len(entry)==1 and entry[0]==address|1,'cold-load entry placement differs')
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    raw=binary.read_bytes();need(64<len(raw)<=RESERVE,'cold-load payload bound')
    (folder/'symbols.txt').write_text(symbols)
    (folder/'disassembly.txt').write_text(subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True).replace(str(elf),'cold-load.elf'))
    usage='\n'.join(p.read_text() for p in folder.glob('*.su'))
    (folder/'stack-usage.txt').write_text(usage)
    sizes=[int(line.split('\t')[1]) for line in usage.splitlines() if 'CircusStreakColdLoad' in line]
    need(sizes and max(sizes)<=128,'cold-load stack bound')
    return raw,entry[0]


def reconstruct():
    b=configure();old=b.reconstruct()
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    from pr16_bp_party_retention_successor import existing_requests
    import pr16_ring_npc_successor as gift
    from tools.rom_allocator import build_allocation_report_from_csv
    raw=(n.INPUT/'candidate.gba').read_bytes();need(identity(raw)==PARENT,'fixed 3b parent differs')
    (OUT/'parent-recipe.json').write_bytes(stable(old));(OUT/'parent.gba').write_bytes(raw)
    previous=struct.unpack_from('<I',raw,SAVE_LOAD_LITERAL)[0]
    need(previous==old['entries']['CircusStreakRuntimeSaveLoad'] and raw[SAVE_LOAD_LITERAL-4:SAVE_LOAD_LITERAL]==bytes.fromhex('004b1847'),'fixed load trampoline changed')
    requests=existing_requests(old['allocation']);need(not any(r['name']==RUNTIME for r in requests),'cold-load allocation already exists')
    req=dict(name=RUNTIME,region='future_tail',size=RESERVE,alignment=4,owner=TASK,
        purpose='CRC-valid Circus64 prime before legacy automatic recovery Saves',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req])
    offset=next(r['start'] for r in preview['allocations'] if r['name']==RUNTIME)
    builds=[compile_bridge(OUT/('compile-'+str(i)),BASE+offset,previous) for i in (1,2)]
    need(builds[0]==builds[1],'cold-load independent ARM links differ')
    payload,entry=builds[0]
    need(raw[offset:offset+len(payload)]==b'\xff'*len(payload),'cold-load allocated bytes not erased')
    patches=[dict(name='cold-load-bridge',offset=offset,before=raw[offset:offset+len(payload)].hex(),after=payload.hex()),
        dict(name='cold-load-delegate',offset=SAVE_LOAD_LITERAL,before=raw[SAVE_LOAD_LITERAL:SAVE_LOAD_LITERAL+4].hex(),after=struct.pack('<I',entry).hex())]
    new=bounded_patch(raw,patches)
    req.update(start=offset,size=len(payload),content_sha256=identity(payload)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[req])
    need(allocation['summaries']['overlap_count']==0,'cold-load allocation overlap')
    for row in allocation['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'other allocated owner changed: '+row['name'])
    recipe=dict(old,parent=PARENT,candidate=identity(new),patches=patches,allocation=allocation,
        entries=dict(old['entries'],CircusStreakColdLoad=entry),cold_load_delegate=previous,
        cold_load_payload=dict(offset=offset,**identity(payload)),independent_arm_links=2,
        whole_rom_rollback_matches_parent=True,changed_existing_allocations=[],
        parent_patch_recipe=identity(stable(old)),status='BUILT_CIRCUS_COLD_LOAD_NATIVE_OPEN',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),run_id=int(os.environ['GITHUB_RUN_ID']))
    recipe['source_bindings']={**old['source_bindings'],**{p:identity((ROOT/p).read_bytes()) for p in (*FILES,AUTOSAVE_SOURCE,SAVE_SOURCE)}}
    (OUT/'build.json').write_bytes(stable(recipe));(OUT/'candidate.gba').write_bytes(new)
    (n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))
    need((OUT/'parent.gba').read_bytes()==raw,'cold-load parent mutated')
    print(json.dumps(dict(candidate=recipe['candidate'],payload=recipe['cold_load_payload'],independent_ARM_links=2,rollback=True)))
    return recipe


def native():
    import pr16_circus_interruption as ip
    import pr16_circus_coldboot_probe as probe
    import pr16_streak_native as n
    recipe=json.loads((OUT/'build.json').read_bytes())
    need(recipe==json.loads((n.INPUT/'report.json').read_bytes()) and identity((n.INPUT/'candidate.gba').read_bytes())==recipe['candidate'],'cold-load recipe differs')
    probe.SHA=recipe['candidate']['sha256'];n.EXTRA=n.EXTRA|set(FILES)|{AUTOSAVE_SOURCE,SAVE_SOURCE}
    code=inspect.getsource(ip.native)
    old='    import pr16_circus_interruption_probe as probe'
    need(code.count(old)==1,'interruption native import boundary differs')
    code=code.replace(old,'    import pr16_circus_coldboot_probe as probe')
    ns=dict(ip.__dict__);ns.update(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,SOURCE=CONTROLLER,PROBE=PROBE,OUT=NATIVE,configure=configure)
    exec(compile(code,SELF+':native','exec'),ns);ns['native']()


def finish():
    b=configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_COLD_LOAD_DIAGNOSTIC_OPEN'
    build=OUT/'build.json';report=NATIVE/'report.json'
    if build.exists():value['build']=json.loads(build.read_bytes())
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['classification']='CIRCUS_COLD_LOAD_INTERRUPTION_BEST1_SAVE_CONTINUE_VERIFIED'
            value['scoped_result']=json.loads((NATIVE/'streak.json').read_bytes())
    import pr16_circus_coldboot_probe as probe
    value['text_evidence']={};prefix='evidence/pr16_circus_coldboot/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in (build,report,NATIVE/(probe.CASE+'.stdout'),NATIVE/(probe.CASE+'.stderr'),NATIVE/(probe.CASE+'.process.json'),NATIVE/'streak.json'):
        if not p.exists():continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext cold-load evidence')
        name=prefix+p.name;target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False
    passed=value['classification'].endswith('_VERIFIED')
    checkpoint(value,'RECORDED','実1勝後の第2戦中断でcurrent0/best1/ABORT一度を保持。既存自動Save2回と通常Save1回を区別し、3つ目のcoreでもowner64/原party600/Factory104不変/BP0を検証。'
        if passed else 'cold-load bridgeの2独立ARM link/rollbackと中断原本を保存。実復旧の未達条件を成功扱いにせず最初の不一致から継続する。')


def pack():
    import pr16_resume as resume
    target=ROOT/'.local/pr16-circus-coldboot-evidence';members={}
    def add(name,raw):
        need(len(raw)<4*1024*1024,'oversize evidence')
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);members[name]=identity(raw)
    for p in OUT.rglob('*'):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stdout','.stderr','.c','.h','.su','.ppm'}:continue
        need(not p.is_symlink(),'unsafe evidence link');add('coldboot/'+p.relative_to(OUT).as_posix(),p.read_bytes())
    for name in (*FILES,OWNER,OWNER_H,AUTOSAVE_SOURCE,SAVE_SOURCE,REPORT,resume.STATE,resume.DOC,
        'scripts/pr16_circus_interruption.py','scripts/pr16_circus_interruption_probe.py','scripts/pr16_streak_native.py',
        'tools/mgba_pr16_streak_native.c','tools/mgba_pr16_circus_sustain.h','design/run_log.md','design/version_log.md'):
        add('source/'+name,(ROOT/name).read_bytes())
    (target/'members.json').write_bytes(stable(members))


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action in {'prepare','reconstruct','native','finish','pack'}:globals()[action]()
    else:raise SystemExit('unknown command')
