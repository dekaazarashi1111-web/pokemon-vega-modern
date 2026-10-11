#!/usr/bin/env python3
"""共有研究saveの16境界を、再実行せず原本・全owner・Bag差分から判定する。"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import zipfile
import pr16_research_save_delegate as repair
import pr16_research_bag_delegate as bag

need, identity = repair.need, repair.identity
ROOT = Path(__file__).resolve().parents[1]
SOURCE = '625987cd510dcf379be575b3702d3bb9a80816cf'
ITEM_SOURCE = '9cb7ca0a7699fd49f1e217cf8204fea682d5dbb8'
ITEM_WF = '.github/workflows/pr16-research-bag-native-20260926.yml'
C = 'tools/mgba_pr16_research_save_impact.c'
WF = '.github/workflows/pr16-research-save-impact-native-20260926.yml'
CONFIG = repair.CONFIG
SEED = {'size':131072,'sha256':'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'}
OPS = ('existing-earn','simple-earn','spend','rank')
CASES = tuple(f'{op}-{phase}' for op in OPS for phase in range(4))
GUARDS = ('bus8','bus16','bus32','raw8','raw16','raw32','register')
SOURCES = {C,WF,CONFIG,'scripts/pr16_research_save_delegate.py',
           'overlays/research_economy_v1/research_economy_v1.c',
           'overlays/research_economy_v1/research_economy_v1.h',
           'tools/mgba_qol_production_smoke.c','tools/mgba_battle_core_smoke.c',
           'tools/mgba_ai_fixture_runner.c'}
MEMBERS = {'repair.json','inputs.json','compile.json','compile.stdout.txt','compile.stderr.txt','guards.json','measurement.json'}
MEMBERS |= {f'guard-{g}.{s}.txt' for g in GUARDS for s in ('stdout','stderr')}
MEMBERS |= {f'{c}.{s}' for c in CASES for s in ('stdout.txt','stderr.txt','process.json')}
ITEM_CASES = tuple(f'{op}-{phase}' for op in ('spend','rank') for phase in range(5))
ITEM_SOURCES = (SOURCES-{WF})|{ITEM_WF,'scripts/pr16_research_bag_actions.py','scripts/pr16_research_bag_delegate.py'}
ITEM_MEMBERS = (MEMBERS-{f'{c}.{suffix}' for c in CASES for suffix in ('stdout.txt','stderr.txt','process.json')}) | {'invocation.json','bag-repair.json','generated-items.c'}
ITEM_MEMBERS |= {f'{c}.{suffix}' for c in ITEM_CASES for suffix in ('stdout.txt','stderr.txt','process.json')}
ARTIFACT_INPUTS = [
    {'binding':{'size':102586759,'sha256':'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'},'id':10898620034,'name':'pr16-special-wild-gameplay-runtime','source_head':'8660fe70f4354333cf7647186663cacafa04451b'},
    {'binding':{'size':17366330,'sha256':'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed'},'id':10898510128,'name':'pr16-special-wild-gameplay-data','source_head':'8660fe70f4354333cf7647186663cacafa04451b'}]
EVENTS = ('fixture','returned_or_cut','continued','continued_again')
STDERR = b'initial validate=0 magic=31534756 version=2 size=2048 owner=1/64\n'
DENIED = b'research-save-impact: host write after observation barrier\n'


def pairs(values):
    out = {}
    for key, value in values:
        need(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def load(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: need(False,'nonfinite JSON'))


def integer(value, low, high, why):
    need(type(value) is int and low <= value <= high, why)


def digest(value):
    need(isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value), 'SHA-256 syntax')


def unpack(raw, items=False):
    members=ITEM_MEMBERS if items else MEMBERS
    need(len(raw) <= 2000000,'public archive size')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist())==members and len(z.infolist())==len(members),'exact public members')
        result = {}
        for e in z.infolist():
            p=PurePosixPath(e.filename)
            need(not p.is_absolute() and len(p.parts)==1 and e.external_attr>>28!=10 and e.file_size<=200000,'public regular text')
            b=z.read(e);b.decode('utf-8');need(b'\0' not in b,'no binary public evidence')
            result[e.filename]=b
    return result


def u16(b, n): return struct.unpack_from('<H',b,n)[0]
def u32(b, n): return struct.unpack_from('<I',b,n)[0]
def w16(b, n, value): struct.pack_into('<H',b,n,value)
def w32(b, n, value): struct.pack_into('<I',b,n,value)


def expected_owner(before, kind, phase, stage):
    """Independent byte-level transaction oracle; never supplies runtime state."""
    b=bytearray(before)
    if stage=='fixture' or phase in (1,4): return b
    w32(b,36,2)
    if stage=='returned_or_cut' and phase==2:
        key,aux,amount=((2,0,3),(4,2,10),(14,1,100),(0,5,4))[kind-1]
        w32(b,44,0x52450001 if kind==1 else 1)
        b[48:52]=bytes((kind,1,key,aux));w16(b,52,amount);w16(b,54,500)
        return b
    apply=phase==0 or stage=='returned_or_cut' or kind==1
    if apply:
        delta={1:3,2:10,3:-100,4:0}[kind];w16(b,4,500+delta)
        if kind in (1,2):
            w32(b,10,delta);w16(b,14+2*(2 if kind==1 else 4),delta)
        if kind==1:w32(b,40,0x52450001)
        if kind==2:b[27]=2
        if kind==3:b[28]=1
        if kind==4:b[26]=1
    return b


def native_result(raw, op, phase, candidate=None):
    candidate=repair.CANDIDATE if candidate is None else candidate
    need(op in OPS and type(phase) is int and phase in range(5) and (phase!=4 or (op in ('spend','rank') and candidate==bag.CANDIDATE)),'case identity')
    lines=raw.decode('utf-8').splitlines();need(len(lines)==5,'four observations plus one result')
    rows=[load(line) for line in lines];events=rows[:4];v=rows[4];kind=OPS.index(op)+1
    expected={'status':'PASS','scope':'RESEARCH_SHARED_SAVE_SCHEDULED_FLASH_RECOVERY',
              'candidate_sha256':candidate['sha256'],'operation':op,'phase':phase,
              'result':0 if phase==0 else 0xFFFFFFFF if phase==3 else 15 if phase==4 else 13,
              'transaction_calls':1,'delegate_saves':2 if phase==0 else 0 if phase in (1,4) else 1,
              'delegate_loads':0,'phase1':0 if phase==4 else 1,'phase2':0 if phase in (1,4) else 1,
              'fresh_cores':3,'host_write_barriers':7,'recovery_saves':1 if phase in (2,3) else 0,
              'test_mode':False,'normal_transaction_ui_accepted':False,
              'second_continue_idempotent':True,'warnings_errors':0}
    need(set(v)==set(expected)|{'steps'},'exact result fields')
    for k,x in expected.items():need(type(v[k]) is type(x) and v[k]==x,'result '+k)
    integer(v['steps'],1,490000000,'bounded CPU execution')
    base=bytearray(64);base[0]=1;base[1]=64;base[6]=1;w16(base,4,500);w32(base,36,1)
    first=events[0];need(first['item_quantity']==(999 if phase==4 else 0),'absent target or native full-stack fixture');expected_fields={'event','counter','item_quantity','inventory_sha256','other_inventory_sha256','party_sha256','party_count','owner'}
    for i,(stage,e) in enumerate(zip(EVENTS,events)):
        need(set(e)==expected_fields and e['event']==stage,'event fields/order')
        integer(e['counter'],1,100,'native save counter');integer(e['item_quantity'],0,999,'Bag item quantity');integer(e['party_count'],1,6,'party count')
        for field in ('inventory_sha256','other_inventory_sha256','party_sha256'):digest(e[field])
        need(isinstance(e['owner'],str) and re.fullmatch('[0-9a-f]{128}',e['owner']),'64 byte synthetic owner')
        owner=bytearray.fromhex(e['owner']);integer(owner[7],0,2,'bounded ordinary minute tick')
        target=expected_owner(base,kind,phase,stage);owner[7]=target[7]=0
        need(owner==target,'all owner bytes '+stage)
        need(e['other_inventory_sha256']==first['other_inventory_sha256'],'unrelated Bag items preserved')
        need((e['party_sha256'],e['party_count'])==(first['party_sha256'],first['party_count']),'all party bytes preserved')
        applied=(stage!='fixture' and phase not in (1,4) and (phase==0 or (stage=='returned_or_cut' and phase==3) or (stage.startswith('continued') and kind==1)))
        added=(1 if kind==3 else 5 if kind==4 else 0) if applied else 0
        need(e['item_quantity']==first['item_quantity']+added,'exact Bag delta '+stage)
        need((e['inventory_sha256']==first['inventory_sha256'])==(added==0),'full Bag digest delta '+stage)
        count=first['counter']+(v['delegate_saves'] if i else 0)+(v['recovery_saves'] if i>=2 else 0)
        need(e['counter']==count,'real save/recovery count '+stage)
    need({k:x for k,x in events[2].items() if k!='event'}=={k:x for k,x in events[3].items() if k!='event'},'second independent Continue idempotence')
    return dict(v,observations=events)


def validate_bundle(files, source, run_id, read_source, items=False):
    cases=ITEM_CASES if items else CASES;members=ITEM_MEMBERS if items else MEMBERS
    sources=ITEM_SOURCES if items else SOURCES;candidate=bag.CANDIDATE if items else repair.CANDIDATE
    need(set(files)==members,'no missing/extra evidence')
    inputs=load(files['inputs.json']);measurement=load(files['measurement.json']);comp=load(files['compile.json'])
    need(inputs['source_head']==source==(ITEM_SOURCE if items else SOURCE) and inputs['run_id']==run_id,'measurement source/run')
    need(run_id==(36229762846 if items else 36229142708) and inputs['artifacts']==ARTIFACT_INPUTS,'fixed runtime/data/run provenance')
    need(inputs['candidate']==candidate and inputs['seed']==SEED,'measurement candidate/seed')
    need(set(inputs['source_bindings'])==sources,'closed source set')
    for path,binding in inputs['source_bindings'].items():need(identity(read_source(path))==binding,'measured source changed: '+path)
    need(comp['source_bindings']==inputs['source_bindings'] and type(comp['returncode']) is int and comp['returncode']==0,'successful bound host compile')
    need(not files['compile.stderr.txt'] and not files['compile.stdout.txt'],'clean host compile')
    digest(comp['executable']['sha256']);integer(comp['executable']['size'],10000,2000000,'host executable')
    need(comp['command'][0]=='cc' and '-lmgba' in comp['command'] and '-Werror' in comp['command'],'actual strict host compiler command')
    need(any(x.endswith('/generated-items.c') if items else x==C for x in comp['command']),'measured C compiler input')
    need(measurement['source_head']==source and measurement['run_id']==run_id,'measurement boundary')
    failed=set() if items else {c for c in CASES if c.startswith(('spend-','rank-'))}
    need(set(measurement['failures'])==failed,'retain exact historical failed cases')
    for k,n in {'native_processes':len(cases),'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0}.items():
        need(type(measurement[k]) is int and measurement[k]==n,'measurement count '+k)
    need(measurement['normal_transaction_ui_accepted'] is False and measurement['status']=='MEASURED_NOT_YET_ACCEPTED','not inherited UI acceptance')
    need(set(measurement['cases'])==set(cases),'exact case matrix')
    guards=load(files['guards.json']);need(set(guards)==set(GUARDS),'seven host APIs')
    for method,g in guards.items():
        out,err=files[f'guard-{method}.stdout.txt'],files[f'guard-{method}.stderr.txt']
        need(type(g['returncode']) is int and g['returncode']==1 and not out and err==DENIED and g['stdout']==identity(out) and g['stderr']==identity(err),'negative write guard '+method)
    results={};failures={}
    for case in cases:
        op,phase=case.rsplit('-',1);phase=int(phase);p=load(files[case+'.process.json']);out,err=files[case+'.stdout.txt'],files[case+'.stderr.txt']
        need(p==measurement['cases'][case] and type(p['returncode']) is int and p['returncode']==int(case in failed) and p['timeout'] is False,'process exit '+case)
        need(p['source_head']==source and p['seed']==SEED and p['stdout']==identity(out) and p['stderr']==identity(err),'process provenance '+case)
        need(p['private_final_save']['size']==131088,'private Flash plus RTC size');digest(p['private_final_save']['sha256'])
        if case in failed:
            need(p==measurement['failures'][case] and err==STDERR+b'research-save-impact: transaction result\n','original item failure preserved')
            need(len(out.splitlines())==1 and load(out)==results['existing-earn-0']['observations'][0],'failed before returned observation, fixture preserved')
            failures[case]={'returncode':1,'timeout':False,'accepted':False,'stdout':identity(out),'stderr':identity(err)}
            continue
        v=native_result(out,op,phase,candidate)
        expected_stderr=STDERR
        if items:expected_stderr+=f"item boundary result={v['result']} saves={v['delegate_saves']} loads=0 phases=0/{v['phase1']}/{v['phase2']}\n".encode()
        need(err==expected_stderr,'unexpected native stderr '+case)
        results[case]=v
    r=load(files['repair.json'])
    need(r['parent']==repair.PARENT and r['candidate']==repair.CANDIDATE and r['changed_bytes']==1 and r['rollback_verified'] is True and r['arm_compiles']==0,'fixed save restoration recipe')
    if items:
        need(files['generated-items.c']==bag.item_runner(read_source(C)),'exact generated item runner')
        need(inputs['generated_harness']==identity(files['generated-items.c']) and inputs['canonical_source_after']==bag.SOURCE_AFTER,'canonical source / generated harness binding')
        invocation=load(files['invocation.json']);need(invocation['source_head']==source and invocation['run_id']==run_id,'invocation identity')
        b=load(files['bag-repair.json']);need(b['parent']==bag.PARENT and b['candidate']==bag.CANDIDATE and b['changed_bytes']==2 and b['rollback_verified'] is True and b['outside_declared_changes']==0 and b['source_before']==bag.SOURCE_BEFORE and b['source_after']==bag.SOURCE_AFTER,'two-byte Bag repair provenance')
    else:
        prior=inputs['prior_terminal'];need(prior=={'id':36221094800,'head_sha':'e6135fb6cd22abbd9a25d3712a7a7b389d71042a','status':'completed','conclusion':'success'},'existing wild terminal identity')
    return {'status':'PASS_ITEM_SAVE_CAPACITY_SCOPED' if items else 'EARN_SCOPED_PASS_WITH_ITEM_FAILURES_RETAINED','candidate':candidate,'source_head':source,'run_id':run_id,'results':results,'failures':failures,
            'native_processes':len(cases),'accepted_cases':len(results),'accepted_fresh_cores':len(results)*3,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,
            'normal_transaction_ui_accepted':False,'source_bindings':inputs['source_bindings'],
            'public_evidence_bindings':{p:identity(b) for p,b in files.items()}}


def thumb_bl(raw, address):
    a,b=struct.unpack_from('<HH',raw,address-0x08000000)
    need(a&0xF800==0xF000 and b&0xF800==0xF800,'Thumb-1 BL pair')
    offset=((a&0x7FF)<<12)|((b&0x7FF)<<1)
    if offset&0x400000:offset-=0x800000
    return address+4+offset


def audit(rom, config_raw, source_raw, candidate=None):
    """Root fixed machine functions in physical field scripts and ROM literals."""
    need(identity(rom)==(candidate or repair.CANDIDATE),'current candidate identity')
    config=load(config_raw);need(config['delegates']['qol_save']=='0x09377661','canonical production save delegate')
    def word(addr):return struct.unpack_from('<I',rom,addr-0x08000000)[0]
    links={0x093BE9DC:0x093BE15C,0x093BE9EE:0x093BE15C,0x093BE88E:0x093BE374,0x093BE92C:0x093BE5A0,0x093BDFA2:0x093BF6A8}
    for address,target in links.items():need(thumb_bl(rom,address)==target,'rooted transaction/recovery BL')
    need(word(0x093BF67C)==0x09377661 and word(0x093BE580)==0x093BF9EC and word(0x093BE710)==0x093BFC94,'production delegate/catalog literals')
    need(struct.unpack_from('<HHHBBBBBB',rom,0x13BF9EC+14*16)==(991,100,1,7,1,0,2,255,0),'daily-limited catalog index14')
    need(struct.unpack_from('<IHHB',rom,0x13BFC94)==(0,4,5,1),'rank1 reward')
    need(rom.count(b'VEGARE40')==1 and rom.find(b'VEGARE40')==0x13BD870,'research payload identity')
    roots={}
    expected={
        'BINDING_KEY_RESEARCH_RANK':(0x093C0408,0x093BE929,0x80),
        'BINDING_KEY_ACTIVITY_MINING':(0x093C050C,0x093BE9D5,0xD8),
        'BINDING_KEY_ACTIVITY_PHOTO':(0x093C05E4,0x093BE9E7,0xDC),
        'BINDING_KEY_RESEARCH_SHOP':(0x093C0328,0x093BE869,0xE0)}
    for row in config['physical_bindings']:
        if row['binding_key'] not in expected:continue
        script,native,size=expected[row['binding_key']];events=word(int(row['event_pointer_site'],16));obj=row['append_kind']=='OBJECT'
        observed=word(word(events+(4 if obj else 16))+row['append_index']*(24 if obj else 12)+(16 if obj else 8))
        need(observed==script,'root physical script')
        body=rom[script-0x08000000:script-0x08000000+size]
        needle=b'\x23'+struct.pack('<I',native);need(body.count(needle)==1,'script callnative root')
        roots[row['binding_key']]={'script':hex(script),'native':hex(native),'callnative_offset':body.index(needle),'window':identity(body)}
    need(set(roots)==set(expected),'all physical roots required')
    text=source_raw.decode();need('return (u8)(FN_QOL_SAVE(0u) == 1u);' in text,'production persist service')
    calls=[{'line':i,'source':line.strip()} for i,line in enumerate(text.splitlines(),1) if 'persist_phase(' in line]
    need(len(calls)==15,'closed shared persist callsite inventory')
    return {'schema_version':1,'candidate':identity(rom),'config':identity(config_raw),'runtime_source':identity(source_raw),
            'physical_roots':roots,'thumb_bl':{hex(k):hex(v) for k,v in links.items()},'persist_callsites':calls,
            'coverage_ja':'4 pending種別×成功/phase1失敗/phase2失敗/phase2前中断、およびspend/rankの実容量拒否2件。復旧phase0をfresh Continueで観測。通常取引UI・全catalog・新規/V1移行・phase0自体の失敗注入は未受入。',
            'rom_changes':0,'arm_compiles':0,'new_native_processes':0}


def guard_scope(allowed, actual, mandatory):
    need(mandatory <= actual, 'required staged records missing')
    need(actual <= allowed, 'unexpected staged changes')
    return actual & allowed


def terminal(run, jobs, source, workflow, name):
    need(run['head_sha']==source and run['head_branch']=='codex/modernization-followup-20260908','terminal source/branch')
    need(run['repository']['full_name']=='dekaazarashi1111-web/pokemon-vega-modern' and run['event']=='push' and run['path']==workflow,'terminal repository/event/workflow')
    need(run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'terminal success, no inferred/rerun acceptance')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one unpaged terminal job')
    job=jobs['jobs'][0]
    need(job['run_id']==run['id'] and job['head_sha']==source and job['name']==name and job['status']=='completed' and job['conclusion']=='success','terminal job')
    need(job['steps'] and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'all terminal steps')
    need(any(s['name']=='Run actions/upload-artifact@v4' for s in job['steps']),'uploaded evidence')
    return job['id']


def historical_terminal(run, jobs):
    need(run['id']==36229142708 and run['head_sha']==SOURCE and run['head_branch']=='codex/modernization-followup-20260908','original failed run identity')
    need(run['repository']['full_name']=='dekaazarashi1111-web/pokemon-vega-modern' and run['event']=='push' and run['path']==WF,'original workflow identity')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'historical failure not relabelled success')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one historical job')
    j=jobs['jobs'][0];need(j['run_id']==run['id'] and j['head_sha']==SOURCE and j['name']=='native' and j['status']=='completed' and j['conclusion']=='failure','historical native job')
    need(all(x['status']=='completed' and x['conclusion']==('failure' if x['number']==3 else 'success') for x in j['steps']),'only measurement step fails')
    need(any(x['number']==4 and x['name']=='Run actions/upload-artifact@v4' for x in j['steps']),'original partial proof uploaded')
    return j['id']
