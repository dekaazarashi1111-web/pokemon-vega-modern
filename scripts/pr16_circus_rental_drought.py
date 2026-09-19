#!/usr/bin/env python3
"""READY/6体レンタル→fieldのDrought空loaderだけを修復し、22戦目以降を継続。"""
from copy import deepcopy
from pathlib import Path
import inspect
import json
import os
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_rental_boundary as prior
need,identity,stable=prior.need,prior.identity,prior.stable
SELF='scripts/pr16_circus_rental_drought.py'
TEST='tests/test_pr16_circus_rental_drought.py'
HEADER='overlays/circus_streak/circus_drought_rental.h'
FIXTURE='tests/fixtures/circus_drought_rental_fixture.c'
WATCH='tools/mgba_pr16_circus_rental_drought.h'
WORKFLOW='.github/workflows/pr16-circus-rental-drought.yml'
REPORT='content/modernization/pr16_circus_rental_drought.json'
SOURCE='overlays/circus_streak/circus_drought.c'
OLD=prior.REPORT
RAW='evidence/pr16_circus_rental_boundary/35452739116/native/circus-continuous-30-save.stderr'
BASE='1e8650300a7512636cc533f701f96e6956b6160b'
RUN=35452739116
JOB=105922614423
OUT=ROOT/'.local/pr16-circus-rental-drought'
NEW=(SELF,TEST,HEADER,FIXTURE,WATCH,WORKFLOW)
RUNTIME='pr16_circus_rental_drought'
RESERVE=8192
NEXT='READY/6体レンタル→fieldのDrought修復候補で22戦目以降の実勝敗・元party600/owner64・通常Save/fresh Continueを確認する。真正30勝未達なら新原本の最初の停止だけを修復し、達成後に正規特性抑制へ進む。旧21勝prefixは同一continuation内の不可避部分以外に再実行しない。'


def repair(source):
    edits=[
        ('#include "circus_drought_selection.h"','#include "circus_drought_rental.h"\n#include "circus_streak.h"'),
        ('#define NATIVE(a) ((void (*)(void))(uintptr_t)(a))',
         '#define NATIVE(a) ((void (*)(void))(uintptr_t)(a))\n#define OWNER ((const CircusStreakOwner *)(uintptr_t)CIRCUS_STREAK_ADDRESS)'),
        ('__attribute__((noinline)) static void DroughtStep(void) { NATIVE(0x0807AD39u)(); }',
'''__attribute__((noinline)) static void DroughtStep(void) { NATIVE(0x0807AD39u)(); }
static uint32_t DroughtSaveIdentity(void)
{
    const volatile uint8_t *save2 = *(const volatile uint8_t * volatile *)(uintptr_t)0x0300504Cu;
    if ((uintptr_t)save2 < 0x02000000u || (uintptr_t)save2 > 0x0203F000u)
        return 0u;
    return (uint32_t)save2[10] | ((uint32_t)save2[11] << 8)
        | ((uint32_t)save2[12] << 16) | ((uint32_t)save2[13] << 24);
}
static uint8_t DroughtOwnerReady(void)
{
    return (uint8_t)(CircusStreakValid(OWNER)
        && OWNER->save_identity == DroughtSaveIdentity() && OWNER->phase == CIRCUS_READY);
}'''),
        ('CircusDroughtInitializeSelection(&c, READ8(0x02023F89u), w, DroughtOriginal, DroughtInitVars, DroughtStep);',
         'CircusDroughtInitializeRentalBoundary(&c, DroughtOwnerReady(), READ8(0x02023F89u), w, DroughtOriginal, DroughtInitVars, DroughtStep);')]
    for old,new in edits:
        need(source.count(old)==1,'rental Drought source preimage differs: '+old)
        source=source.replace(old,new)
    return source


def diagnose(raw):
    import pr16_circus_continuous_probe as p
    accepted=prior.accepted_prefix(raw);events=p.parse(raw)
    prefix=b'CIRCUS_RENTAL_BOUNDARY ';rows=[p.strict(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]
    need(len(rows)==21 and [r['elapsed'] for r in rows]==[1,*range(30,601,30)],'rental Drought samples')
    last=events[-1];owner=p.owner(bytes.fromhex(last['owner']))
    need(last['label']=='selected' and last['battle']==21 and last['count']==6 and last['script']==0x09FF4CB5,'selected boundary event')
    need(owner['current']==owner['best']==owner['prepared']==owner['settled']==21 and owner['phase']==1 and owner['session']==8,'READY owner boundary')
    for row in rows:
        weather=bytes.fromhex(row['weather_raw']);base=0x6B8
        need(row['current']==21 and row['phase']==1 and row['count']==6 and row['saved_count']==1
             and row['marker']==row['snapshot']==1 and row['script']==0x09FF4CB5 and row['outcome']==1
             and row['callback2']==0x08055E75 and not row['newbs'],'field boundary drift')
        need((weather[0x6CC-base],weather[0x6D2-base],weather[0x74D-base],weather[0x74E-base])==(2,0,1,1),'empty loader boundary drift')
        need((weather[0x6D0-base],weather[0x6D1-base],weather[0x6C8-base],weather[0x6C6-base])==(12,12,1,1),'Drought readiness drift')
    return dict(classification='CIRCUS_RENTAL_DROUGHT_READY6_DIAGNOSED',source_run=RUN,events=100,wins=accepted['actual_wins'],bp=accepted['bp'],
        owner_phase=1,owner_session=8,current=21,active_party_count=6,saved_party_count=1,marker=1,snapshot=1,
        script=0x09FF4CB5,outcome=1,weather=12,weather_state=2,complete=0,cursor=[1,1],elapsed_frames=600,
        cause_ja='既存guardはARMED/3体/marker2またはWIN復帰だけを許可する。新原本はCRC/identity有効なREADY owner、元party保存1体、レンタル6体、marker1、script09ff4cb5であり、別の正規field復帰境界なのに旧initAllへ落ちて空loader cursor1で停止した。')


def task_id():
    return 'USER-20260920-CIRCUS-RENTAL-DROUGHT-RUN'+os.environ.get('GITHUB_RUN_ID','0')


def configure():
    for key,value in dict(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,OUT=OUT,NEXT=NEXT,NEW=NEW).items():
        setattr(prior,key,value)
    d,b=prior.configure()
    d.FILES=tuple(dict.fromkeys((*d.FILES,*NEW,SOURCE,OLD,RAW)))
    d.c.FILES=d.FILES
    return d,b


def record(value,phase,stop,next_step):
    import pr16_resume as resume
    d,b=configure();task=task_id();r=b.rec;state=resume.load(ROOT,resume.STATE);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value));ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_rental_drought_followup']=loss['rental_drought_followup']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30)
    state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35452739116/job105922614423は新candidate7a5676f9の実21勝/63BP/元party600復元後、READY/6体/script09ff4cb5/Drought state2 cursor1で600frame停止したreadonly原本。旧21勝受入単体・旧ARM link・同じ境界診断は再実行せず後継だけを検証する。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER;r.TASK=task
    extra=list(dict.fromkeys((REPORT,*d.FILES,*value.get('text_evidence',{}))))
    r.checkpoint(state,loss,stop,next_step,extra,phase,
        value['classification']+'。CRC/save identity有効READY ownerと6体/script09ff4cb5だけを別guardで許可。既存ARMED/3体/WIN/LOSS predicate不変。新tail payload独立2link、旧allocation/owner/party/BP不変、同一continuation内prefix21戦のみ不可避。')


def prepare():
    import pr16_resume as resume
    d,b=configure();task=task_id();r=b.rec;head=r.scope();state=resume.validate(ROOT)
    need(int(r.command('git','rev-list','--count',BASE+'..'+head)) in (1,6) and set(r.command('git','diff','--name-only',BASE,head).splitlines())==set(NEW),'rental Drought WIP source scope')
    need(not (ROOT/REPORT).exists(),'rental Drought attempt already exists')
    old=resume.load(ROOT,OLD);need(old['recording_run']==RUN and old['classification']=='CIRCUS_RENTAL_BOUNDARY_READONLY_COMPLETE' and old['diagnostic_complete'],'readonly predecessor differs')
    need(identity((ROOT/RAW).read_bytes())==old['text_evidence'][RAW],'readonly raw identity differs')
    run=r.api('actions/runs/'+str(RUN));job=r.api('actions/jobs/'+str(JOB))
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']=='9f663a0bde45deb01958ecbf8c0bfc1541508857','predecessor run differs')
    need(job['status']=='completed' and job['conclusion']=='success' and job['run_id']==RUN,'predecessor job differs')
    actions=[{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    for run_id in (35453175182,35453175149):
        a=r.api('actions/runs/'+str(run_id));need(a['head_sha']==BASE and a['status']=='completed' and a['conclusion']=='action_required','HEAD no-job run differs')
        actions.append({k:a[k] for k in ('id','head_sha','status','conclusion')})
    diagnosis=diagnose((ROOT/RAW).read_bytes())
    before=(ROOT/SOURCE).read_bytes();need(identity(before)==state['source_bindings'][SOURCE],'Drought source binding drift')
    (ROOT/SOURCE).write_text(repair(before.decode()))
    value=dict(schema_version=1,classification='CIRCUS_RENTAL_DROUGHT_REPAIR_PREPARED',diagnosis=diagnosis,
        actions_reconciled=actions,source_change=dict(path=SOURCE,before=identity(before),after=identity((ROOT/SOURCE).read_bytes())),
        host_tests=r.tests([Path(TEST).name,'test_pr16_circus_selection.py','test_pr16_circus_drought.py','test_pr16_circus_rental_boundary.py']),
        accepted_prefix_wins=21,accepted_prefix_reexecuted_only_inside_continuation=True,accepted_native_cases_replayed=0,
        independent_old_arm_links_replayed=0,native_lifecycle_accepted=False,standard_save_fresh_continue=False,
        genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    record(value,'PREPARED','実21勝受入後の最初の新停止をREADY/6体レンタルfield復帰のDrought空loaderと確定。狭いowner/ledger/party/script/weather guardを準備し、旧phase2/3体とWIN経路は委譲して変更しない。',NEXT)


def compile_bridge(folder,address,armed):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'circus_drought_addresses.h').write_text(f'#define CIRCUS_DROUGHT_ARMED 0x{armed:08X}u\n')
    ld=folder/'bridge.ld';ld.write_text(f'ENTRY(CircusDroughtInitAll)\nSECTIONS {{ . = 0x{address:08X}; .text : {{ KEEP(*(.text.CircusDroughtInitAll)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }} }}\n')
    elf=folder/'bridge.elf';binary=folder/'bridge.bin'
    args=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-fstack-usage',
        '-DVEGA_SAVE_ROM_RUNTIME=1','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none','-T',str(ld),'-I',str(folder),
        '-I',str(ROOT/'overlays/circus_streak'),str(ROOT/SOURCE),str(ROOT/'overlays/circus_streak/circus_streak.c'),
        str(ROOT/'overlays/save_migration/save_migration.c'),'-o',str(elf)]
    result=subprocess.run(args,cwd=folder,capture_output=True,text=True)
    (folder/'compile.stdout').write_text(result.stdout);(folder/'compile.stderr').write_text(result.stderr)
    need(result.returncode==0,'rental Drought ARM compile: '+result.stderr[-3000:])
    need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)])==b'','unresolved rental Drought ARM symbol')
    syms=subprocess.check_output(['arm-none-eabi-nm','-n','--defined-only',str(elf)],text=True)
    rows=[line.split() for line in syms.splitlines() if len(line.split())==3]
    need(not any(row[1] in 'bBdD' for row in rows),'writable static state prohibited')
    entry=[int(row[0],16)|1 for row in rows if row[2]=='CircusDroughtInitAll'];need(entry==[address|1],'rental Drought entry placement')
    need(any(row[2]=='CircusStreakValid' for row in rows),'owner CRC validator absent from payload')
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    payload=binary.read_bytes();need(64<len(payload)<=RESERVE,'rental Drought payload bound')
    (folder/'symbols.txt').write_text(syms)
    dis=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True).replace(str(elf),'rental-drought.elf')
    (folder/'disassembly.txt').write_text(dis)
    usage='\n'.join(p.read_text() for p in folder.glob('*.su'));(folder/'stack-usage.txt').write_text(usage)
    sizes=[int(line.split('\t')[1]) for line in usage.splitlines() if 'CircusDroughtInitAll' in line]
    need(sizes and max(sizes)<=160,'rental Drought stack bound')
    return payload,entry[0]


def reconstruct():
    d,b=configure();task=task_id();d.c.f.reconstruct()
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    from pr16_bp_party_retention_successor import existing_requests
    import pr16_ring_npc_successor as gift
    from tools.rom_allocator import build_allocation_report_from_csv
    old=json.loads((ROOT/OLD).read_bytes())['build'];raw=(n.INPUT/'candidate.gba').read_bytes()
    need(identity(raw)==old['parent'],'rental Drought base parent reconstruction')
    for path,bound in old['source_bindings'].items():
        actual=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT) if path==SOURCE else (ROOT/path).read_bytes()
        need(identity(actual)==bound,'saved predecessor source drift: '+path)
    parent=bounded_patch(raw,old['patches']);need(identity(parent)==old['candidate'],'saved predecessor candidate reconstruction')
    for row in old['allocation']['allocations']:
        need(identity(parent[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'predecessor allocation changed: '+row['name'])
    requests=existing_requests(old['allocation']);need(not any(row['name']==RUNTIME for row in requests),'rental Drought allocation exists')
    request=dict(name=RUNTIME,region='future_tail',size=RESERVE,alignment=4,owner=task,
        purpose='Circus READY six-rental field return empty Drought loader termination',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[request])
    off=next(row['start'] for row in preview['allocations'] if row['name']==RUNTIME)
    builds=[compile_bridge(OUT/('compile-'+str(i)),0x08000000+off,old['entries']['CircusStreakRuntimeArmed']) for i in (1,2)]
    need(builds[0]==builds[1],'independent rental Drought ARM links differ');payload,entry=builds[0]
    need(parent[off:off+len(payload)]==b'\xff'*len(payload),'rental Drought tail not erased')
    table=d.TABLE
    need(parent[table:table+4]==struct.pack('<I',old['entries']['CircusDroughtInitAll']),'Drought table predecessor entry')
    patches=[dict(name='rental-drought-ready6',offset=off,before=parent[off:off+len(payload)].hex(),after=payload.hex()),
        dict(name='rental-drought-init-table',offset=table,before=parent[table:table+4].hex(),after=struct.pack('<I',entry).hex())]
    candidate=bounded_patch(parent,patches)
    request.update(start=off,size=len(payload),content_sha256=identity(payload)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/gift.REGIONS,requests+[request]);need(allocation['summaries']['overlap_count']==0,'rental Drought allocation overlap')
    for row in allocation['allocations']:
        need(identity(candidate[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'candidate allocation changed: '+row['name'])
    changed=[i for i,(a,z) in enumerate(zip(parent,candidate)) if a!=z]
    need(changed and all(off<=i<off+len(payload) or table<=i<table+4 for i in changed),'rental Drought delta escaped payload/table')
    need(struct.pack('<I',0x0203DB00) in payload and struct.pack('<I',0x02023F89) in payload and struct.pack('<I',0x09FF4CB5) in payload,'generated READY6 guard literals absent')
    recipe=dict(schema_version=1,status='BUILT_CIRCUS_RENTAL_DROUGHT_NATIVE_OPEN',task=task,source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ['GITHUB_RUN_ID']),old=old,parent=old['candidate'],candidate=identity(candidate),patches=patches,allocation=allocation,
        entries=dict(old['entries'],CircusDroughtInitAll=entry),payload=dict(offset=off,**identity(payload)),independent_arm_links=2,
        independent_old_arm_links_replayed=0,whole_rom_rollback_matches_parent=True,changed_existing_allocations=[],
        supersedes=dict(candidate=old['candidate'],changed_bytes=len(changed),old_arm_links_replayed=0),
        source_bindings={**old['source_bindings'],**{path:identity((ROOT/path).read_bytes()) for path in d.FILES}},
        change_impact=dict(rom_ranges=[dict(offset=p['offset'],size=len(bytes.fromhex(p['before'])),purpose=p['name']) for p in patches],
            old_allocations_unchanged=True,old_runtime_payload_unchanged=True,save_owners_unchanged=True,
            native_read_scope=['CircusStreakOwner64 CRC/save_identity/phase','factory ledger','active party count','field callback/script/weather'],
            native_write_scope=['weather.loadDroughtPalsIndex','weather.loadDroughtPalsOffset'],
            native_write_scope_excludes=['Circus owner','factory ledger','party','BP','outcome','task','script','PC','RNG'],
            required_new_case='unchanged 21-win prefix then READY six-rental Drought return and battle22 continuation',
            excluded_replays=['accepted standalone cases','old boundary diagnostic','old ARM links']))
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'parent.gba').write_bytes(parent);(OUT/'candidate.gba').write_bytes(candidate);(OUT/'build.json').write_bytes(stable(recipe))
    (n.INPUT/'candidate.gba').write_bytes(candidate);(n.INPUT/'report.json').write_bytes(stable(recipe))
    print(json.dumps(dict(candidate=recipe['candidate'],payload=recipe['payload'],independent_ARM_links=2,rollback=True)))


def witness(raw):
    import pr16_circus_continuous_probe as p
    prefix=b'CIRCUS_RENTAL_DROUGHT ';rows=[p.strict(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]
    direct=[row for row in rows if row['label']=='event-crossed-direct']
    if direct:
        need(len(rows)==len(direct)==1 and direct[0]['events']>100 and direct[0]['elapsed']==1,'direct rental Drought crossing schema')
        return dict(entered=None,direct=True,transition=[],crossed=True,final=direct[0])
    need(rows and rows[0]['label']=='entered' and rows[0]['events']==100,'rental Drought entry witness absent')
    entered=rows[0]
    for key,value in dict(current=21,phase=1,count=6,saved_count=1,marker=1,snapshot=1,callback2=0x08055E75,script=0x09FF4CB5,newbs=0,state=2,complete=0,index=1,offset=1).items():
        need(type(entered[key]) is int and entered[key]==value,'rental Drought entry '+key)
    crossed=[row for row in rows if row['label']=='event-crossed']
    bounded=[row for row in rows if row['label']=='bounded-stop']
    need(not (crossed and bounded),'rental Drought witness conflict')
    if crossed:
        need(len(crossed)==1 and crossed[0]['events']>100 and crossed[0]['elapsed']<=600,'rental Drought crossing schema')
    else:
        need(len(bounded)==1 and bounded[0]['elapsed']==600,'bounded rental Drought failure absent')
    return dict(entered=entered,direct=False,transition=[row for row in rows if row['label']=='weather-returned'],crossed=bool(crossed),final=(crossed or bounded)[0])


def native():
    d,b=configure();task=task_id();recipe=json.loads((OUT/'build.json').read_bytes());d.probe.SHA=recipe['candidate']['sha256']
    import pr16_circus_win_return_trace as trace
    def rental_drought_watch(text):
        return prior.s.boundary.compose_boundary_watch(text,(ROOT/'tools/mgba_pr16_circus_selection_context.h').read_text(),trace.chained_watch)+'\n'+(ROOT/WATCH).read_text()
    source=inspect.getsource(d.c.native);anchor='(ROOT/b.fade.WATCH).read_text()';need(source.count(anchor)==1,'continuous watcher source boundary')
    ns=dict(d.c.__dict__);ns['rental_drought_watch']=rental_drought_watch
    exec(compile(source.replace(anchor,'rental_drought_watch('+anchor+')'),SELF+':native','exec'),ns)
    failure=None
    try:ns['native']()
    except ValueError as error:
        need(str(error) in {'continuous lifecycle failed; inspect original','genuine 30-win target remains open'},'unexpected rental Drought native failure: '+str(error))
        failure=str(error)
    import pr16_circus_continuous_probe as p
    folder=OUT/'native';raw=(folder/(d.probe.CASE+'.stderr')).read_bytes();events=p.parse(raw);old=p.parse((ROOT/RAW).read_bytes())
    need(len(old)==100 and len(events)>=100,'continuous prefix event count')
    need(all(prior.s.boundary.same_without_frame(a,z) for a,z in zip(events[:100],old)),'accepted 100-event semantics changed')
    observed=witness(raw);repaired=len(events)>100 and observed['crossed']
    if repaired:
        first=events[100];owner=p.owner(bytes.fromhex(first['owner']))
        need(first['label']=='confirmation' and first['battle']==21 and first['count']==3 and first['marker']==2 and first['snapshot']==1
             and first['script']==0x09FF4CEB and not first['newbs'] and first['outcome']==0,'battle22 confirmation boundary')
        need(owner['current']==owner['best']==21 and owner['phase']==2 and owner['prepared']==22 and owner['settled']==21 and owner['session']==8,'battle22 armed owner')
    report=json.loads((folder/'report.json').read_bytes()) if (folder/'report.json').exists() else {}
    summary=json.loads((folder/'streak.json').read_bytes()) if (folder/'streak.json').exists() else {}
    save_continue=bool(repaired and report.get('status')=='PASS_CIRCUS_SCOPED_NATIVE' and len(events)>=2 and [e['label'] for e in events[-2:]]==['saved','reloaded'])
    genuine=bool(summary.get('genuine_30_wins_verified',False))
    actual_wins=max([p.owner(bytes.fromhex(e['owner']))['current'] for e in events if 'owner' in e] or [21])
    if genuine:classification='CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE_VERIFIED'
    elif save_continue:classification='CIRCUS_RENTAL_DROUGHT_RETURN_SAVE_CONTINUE_SCOPED_VERIFIED'
    elif repaired:classification='CIRCUS_RENTAL_DROUGHT_BOUNDARY_REPAIRED_NEXT_STOP_OPEN'
    else:classification='CIRCUS_RENTAL_DROUGHT_REPAIR_NOT_CROSSED'
    result=dict(classification=classification,repaired_boundary=repaired,witness=observed,events=len(events),actual_wins=actual_wins,
        standard_save_fresh_continue=save_continue,genuine_30_wins_verified=genuine,native_report_status=report.get('status'),
        process_failure=failure,accepted_prefix_events_semantically_identical=100,accepted_prefix_wins_reexecuted_for_continuation=21,
        accepted_native_cases_replayed=0,old_arm_links_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    if repaired:result['battle22_confirmation']={k:events[100][k] for k in ('frame','battle','count','marker','snapshot','script','newbs','outcome')}
    if events:result['last_event']={k:events[-1].get(k) for k in ('label','frame','battle','count','bp','marker','snapshot','script','newbs','outcome')}
    (OUT/'rental-drought-result.json').write_bytes(stable(result));print(json.dumps(result,ensure_ascii=False))


def finish():
    d,b=configure();task=task_id();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_RENTAL_DROUGHT_NATIVE_OPEN'
    for path,key in [('build.json','build'),('native/report.json','native'),('native/streak.json','scoped_result'),('rental-drought-result.json','rental_drought_result')]:
        p=OUT/path
        if p.exists():value[key]=json.loads(prior.s.launch.inherited.relative_text(p.read_bytes(),ROOT))
    if 'build' in value:value['candidate']=value['build']['candidate']
    result=value.get('rental_drought_result')
    if result:
        value['classification']=result['classification'];value['native_lifecycle_accepted']=result['standard_save_fresh_continue']
        value['standard_save_fresh_continue']=result['standard_save_fresh_continue'];value['genuine_30_wins_verified']=result['genuine_30_wins_verified']
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={};value['evidence_transformations']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        name='evidence/pr16_circus_rental_drought/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=prior.s.launch.inherited.export(name,p.read_bytes(),value['text_evidence'])
    if not result:
        stop='READY/6体Drought後継のbuild/native原本が未完。受入状態を進めず、同runの最初の失敗から再開。';next_step=NEXT
    elif result['genuine_30_wins_verified']:
        stop='READY/6体境界を修復し、同一processで真正30勝・90BP・元party600/owner64・通常Save/fresh Continueまで到達。正規特性抑制/P08/releaseは未完。'
        next_step='真正30勝候補を固定し、Battle Circus正規経路の特性抑制を独立nativeで検証する。続いてP08最終受入とrelease判断を別ゲートで行う。'
    elif result['standard_save_fresh_continue']:
        stop='READY/6体境界を修復し22戦目以降と通常Save/fresh Continueを確認。今回の実勝数='+str(result['actual_wins'])+'、真正30勝は未達。'
        next_step='保存済み後継原本の最初の実敗北/停止から入力だけを改善し、真正30勝・90BPを同一processで達成する。旧21勝prefixの独立再実行は禁止。'
    elif result['repaired_boundary']:
        stop='READY/6体Drought境界を越え22戦目confirmationを確認。通常Save/fresh Continue前の新停止を原本保存し、30勝受入には昇格しない。'
        next_step='22戦目confirmation以降の新原本から最初の停止だけを修復する。READY/6体修復・旧21勝prefixは固定し、旧ARM link/旧境界/受入単体を再実行しない。'
    else:
        stop='READY/6体Drought後継は600frame境界を越えず、修復未受入の原本を保存。旧21勝受入は維持。';next_step='新payloadのowner READY predicate/生成ARMと境界witnessを照合し、同じ停止に対する最小修正だけを行う。'
    record(value,'RECORDED',stop,next_step)


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure()[1].pipeline()
    elif action=='pack':configure()[0].c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
