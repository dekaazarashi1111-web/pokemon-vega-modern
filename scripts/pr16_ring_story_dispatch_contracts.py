#!/usr/bin/env python3
"""保存candidate命令のscript/field dispatch契約。未mapを成功stubで埋めない。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_dispatch_frontier as prior
import pr16_ring_story_caller_frontier as archive
import pr16_ring_explicit_text_machine as vm
import pr16_ring_followup_v2 as s

BASE='16e8dbf2cd4183469ae3c9acb6462cfb4a539498'
SLUG='pr16-ring-story-dispatch-contracts'
TASK='PR-P08-7-RING-STORY-DISPATCH-CONTRACTS'
TITLE='保存script状態と実命令slotの部分書込・待機・field table不足を条件付き結合'
SELF='scripts/pr16_ring_story_dispatch_contracts.py'
TEST='tests/test_pr16_ring_story_dispatch_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-story-dispatch-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_dispatch_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=(prior.SELF,archive.SELF,vm.SELF,'scripts/pr16_ring_ui_contracts.py',
    'scripts/pr16_ring_resource_contracts.py','scripts/pr16_ring_dispatch_contracts.py',
    'scripts/pr16_ring_gate_contracts.py','scripts/pr16_ring_caller_contracts.py',
    'scripts/pr16_ring_string_machine.py','scripts/pr16_ring_contract_machine.py',
    'scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py',
    'scripts/pr16_ring_message_task_frontier.py','scripts/pr16_ring_text_export_recovery.py')
NETWORK='既存run35316606613のhash固定exportのみ。外部source追加、候補復元、ROM/native実行0。'
NO_REPEAT='保存script/field dispatch全u8境界、実66/67slot、初期化とglobal statusの条件付き契約は原本再利用。synthetic RAM/任意callbackの帰還を通常story供給と同一視しない。次は080565B0の5slotと08068DDD待機callbackの未読byteだけ。旧text/bootstrap/BP/native再実行禁止。'
ARTIFACT=10534848462
ZIP_SHA='78e78513d635a708be0c35711bae3a3a8b948cfbc6a6f86b6eeb69ff1708b573'
C,STATE,LOCK,SCRIPT,TABLE,END=0x03000eb0,0x03000ea8,0x03000f9c,0x02001800,0x08162cc4,0x08163010
NULL_PTR=0x0836b2a4
BUSY=0x02036fd0
WAIT=0x08068ddd
FIELD_TABLE,FIELD_STATE=0x080565b0,0x03003568
GROUPS=('setup','mode','opcode','callback','global','field')
SCOPES=((0x0806906c,0x080693d8),(0x0806b0cc,0x0806b148),(0x08068cfc,0x08068d24),
        (0x081c7ac8,0x081c7ad0),(0x08056598,0x08056604),(0x080560c8,0x080560e2))
need=s.need
word=vm.b.word


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-dispatch.zip') as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            value=json.loads(raw);need(value['file']==name and value['index']==index and value['count']==len(row['parts']),'chunk sequence')
            parts.append(value['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity')
        return json.loads(raw)


def context(mode=0,script=0,native=0):
    need(type(mode)is int and 0<=mode<256,'mode u8')
    b=bytearray(b'\xcc'*116);b[1]=mode
    for offset,value in ((4,native),(8,script),(0x5c,TABLE),(0x60,END)):b[offset:offset+4]=word(value)
    return bytes(b)


def initial_writes():
    return [(C+1,1,0),(C+8,4,0),(C,1,0),(C+4,4,0),(C+0x5c,4,TABLE),(C+0x60,4,END)]+[(C+i,4,0)for i in range(0x70,0x60,-4)]+[(C+i,4,0)for i in range(0x58,8,-4)]


def segments(mode=0,script=0,native=0,*,status=0):
    return [(C,context(mode,script,native),True),(STATE,bytes([status]),True),(LOCK,b'\x77',True)]


def slot_segments(slots):
    need(type(slots)is list and len(slots)==2,'slot count')
    rows=[]
    for row,op,target in zip(slots,(0x66,0x67),(0x0806b139,0x0806b0cd)):
        need(row=={'opcode':op,'address':TABLE+4*op,'hex':word(target).hex(),'target':target},'実slot結合')
        rows.append((row['address'],bytes.fromhex(row['hex']),False))
    return rows


def contracts(nodes,slots,group):
    need(group in GROUPS,'契約group')
    selected=[n for n in nodes if any(lo<=n['address']<hi for lo,hi in SCOPES)]
    cases=vm.Cases(selected);run=cases.run
    mapped_slots=slot_segments(slots)
    if group=='setup':
        run('init-context',0x0806906d,segments(),(C,TABLE,END),initial_writes())
        run('global-init',0x08069341,segments(),writes=initial_writes()+[(STATE,1,2)])
        for pointer in (0,SCRIPT):
            extra=[(0x03000f9d,b'\x55\x55',True),(0x03000fa0,b'\x55',True)]
            writes=[(0x03000f9e,1,0),(0x03000f9d,1,0),(0x03000fa0,1,0)]+initial_writes()+[(C+8,4,pointer),(C+1,1,1),(LOCK,1,1),(STATE,1,0)]
            run('setup-'+str(pointer),0x080693a5,segments()+extra,(pointer,),writes)
    elif group=='mode':
        for mode in range(256):
            writes=[(C+1,1,0)]if mode==1 else [(C+1,1,1),(C+1,1,0)]if mode==2 else []
            run('mode-'+str(mode),0x080690c5,segments(mode),(C,),writes,value=int(mode>2))
    elif group=='opcode':
        for op in range(256):
            # 67はbusy=1でmessage表示を拒否して次の範囲外opcodeへ進む条件。
            data=bytes([op])+word(0x02003000)+b'\xff'if op==0x67 else bytes([op])
            seg=segments(1,SCRIPT)+[(SCRIPT,data,False),(NULL_PTR,word(0),False),*mapped_slots]
            writes=[(C+8,4,SCRIPT+1)];stop=None;fault=None;value=None
            if op>=211:writes+=[(C+1,1,0)];value=0
            elif op==0x66:writes+=[(C+1,1,2),(C+4,4,WAIT)];value=1
            elif op==0x67:
                seg.append((BUSY,b'\x01',False))
                writes += [(C+8,4,SCRIPT+i)for i in range(2,6)]+[(C+8,4,SCRIPT+6),(C+1,1,0)];value=0
            else:
                stop=('未map read',0x0806912a);fault={'address':TABLE+4*op,'size':4,'site':0x0806912a}
            run('opcode-'+str(op),0x080690c5,seg,(C,),writes,value,stop,fault)
        run('null-script-sentinel',0x080690c5,segments(1,SCRIPT)+[(NULL_PTR,word(SCRIPT),False)],(C,),
            stop=('保存node境界で停止',0x08069110))
    elif group=='callback':
        for flag in (0,1,2,255):
            # 保存済みbool getterへの合成nativePtr。実waitmessage callbackの代替受入ではない。
            run('conditional-saved-getter-'+str(flag),0x080690c5,segments(2,SCRIPT,0x080692f9)+[(0x03000fa1,bytes([flag]),False)],
                (C,),[(C+1,1,1)]if flag==1 else [],value=1)
        run('real-wait-callback-unread',0x080690c5,segments(2,SCRIPT,WAIT),(C,),stop=('保存node境界で停止',WAIT&~1))
        run('native-arm-pointer-rejected',0x080690c5,segments(2,SCRIPT,WAIT&~1),(C,),stop=('ARM state未対応',0x081c7ac8))
    elif group=='global':
        for status in range(256):
            writes=[]if status in (1,2)else [(LOCK,1,1),(STATE,1,2),(LOCK,1,0)]
            run('global-status-'+str(status),0x08069369,segments(status=status),writes=writes,value=0)
        run('global-active-unknown-mode',0x08069369,segments(3),writes=[(LOCK,1,1)],value=1)
        run('global-real-wait',0x08069369,segments(1,SCRIPT)+[(SCRIPT,b'\x66',False),(NULL_PTR,word(0),False),*mapped_slots],
            writes=[(LOCK,1,1),(C+8,4,SCRIPT+1),(C+1,1,2),(C+4,4,WAIT)],value=1)
    elif group=='field':
        for state in range(256):
            stop=('未map read',0x080565a8)if state<5 else None
            fault={'address':FIELD_TABLE+4*state,'size':4,'site':0x080565a8}if state<5 else None
            run('field-state-'+str(state),0x080560c9,[(FIELD_STATE,bytes([state]),False)],stop=stop,fault=fault)
    return cases


@functools.lru_cache(maxsize=1)
def verified_groups():
    c=payload('saved-context.json')
    return {g:contracts(c['nodes'],c['story_dispatch_frontier']['command_slots'],g)for g in GROUPS}


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis']
    need(c['story_dispatch_frontier']=={k:v for k,v in a.items()if k!='export_manifest'},'保存解析原本')
    need(len(c['nodes'])==8821 and a['candidate']==s.CANDIDATE and a['ring_acquisition_accepted']is False,'保存境界')
    rows=[];sites=set()
    for group in GROUPS:
        cases=verified_groups()[group];rows+=cases.rows;sites|=cases.sites
    result={'classification':'SAVED_STORY_DISPATCH_CONDITIONAL_CONTRACTS_NOT_NORMAL_ACQUISITION',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'cases':rows,'executed_saved_sites':sorted(sites),
        'saved_node_count':len(c['nodes']),'actual_context':C,'actual_status':STATE,'actual_lock':LOCK,
        'actual_command_table':{'table':TABLE,'end':END,'count':211,'slots':a['command_slots']},
        'pending_field_table':{'address':FIELD_TABLE,'slots':5,'dispatch_site':0x080565aa,'entry':0x08056599},
        'pending_wait_callback':WAIT,'null_script_swi_boundary':0x08069110,
        'unmapped_command_slots_not_proven_absent':True,'synthetic_getter_is_wait_callback':False,
        'normal_story_observed':False,'initializer_runtime_observed':False,
        'candidate_reconstructions':0,'rom_changes':0,'new_node_count':0,'new_window_bytes':0,
        'new_emulator_processes':0,'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'明示合成RAMのscript/field状態全u8と実66/67slotだけ。busy時67は表示しない。未読callback/5slot、font/window供給と通常story到達は未証明。'}
    files=exporter.source_export((SELF,TEST,*SOURCES))
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-dispatch.zip') as z:
        manifest=json.loads(z.read('export/manifest.json'))
        need(s.identity(z.read('export/manifest.json'))==a['export_manifest'],'export manifest binding')
        for p,raw in files.items():
            if p in manifest['files']:need(s.identity(raw)==manifest['files'][p]['identity'],'保存model source差分 '+p)
    result['executed_source_bindings']={p:s.identity(raw)for p,raw in files.items()}
    files['saved-context.json']=s.stable(dict(c,story_dispatch_contracts=result))
    for name in ('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'保存script/field dispatchの{r["contract_cases"]}条件を結合。実66待機/67busy拒否、全u8 mode/status/opcode/field、cursor部分書込、setup/global初期化を検証。候補復元/native0。',
        '未読080565B0の5slotと実wait callback08068DDDだけを採取し、field state0の初期化calleeを既存font/window/bootstrapへ結合する。未mapは不存在ではない。通常story取得/装備/Saveは未受入。今回条件と旧text/BP/nativeを単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_dispatch_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
