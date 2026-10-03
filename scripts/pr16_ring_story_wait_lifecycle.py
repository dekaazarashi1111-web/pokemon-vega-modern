#!/usr/bin/env python3
"""実wait callbackとfield状態を保存byteへ結合。tick間RAMは出力だけ継承。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_field_frontier as prior
import pr16_ring_story_dispatch_contracts as d
import pr16_ring_story_caller_frontier as archive
import pr16_ring_explicit_text_machine as vm
import pr16_ring_followup_v2 as s

BASE='9abda77b40446747a2df2b4cad45d276627393d1'
SLUG='pr16-ring-story-wait-lifecycle'
TASK='PR-P08-7-RING-STORY-WAIT-LIFECYCLE'
TITLE='実wait callbackからscript終了への連続tickとfield状態境界を保存byteで結合'
SELF='scripts/pr16_ring_story_wait_lifecycle.py'
TEST='tests/test_pr16_ring_story_wait_lifecycle.py'
WORKFLOW='.github/workflows/pr16-ring-story-wait-lifecycle.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_wait_lifecycle.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=28
EXTRA_CODE=()
SOURCES=(prior.SELF,d.SELF,archive.SELF,vm.SELF,'scripts/pr16_ring_message_task_frontier.py')
NETWORK='成功run35319665678のhash固定exportのみ。候補復元・再採取・native実行0。'
NO_REPEAT='実wait全u8/連続3tick・field1/4とstate0/2/3停止境界は保存原本を再利用。待機解除byteのhost書込0だがbusy=0/非0は明示初期条件。通常message表示/取得を受入にしない。次は08055B71/08055EAD/080555F1の未読calleeだけ。旧1037条件/今回786条件/BP/native単独再実行禁止。'
ARTIFACT=10536507721
ZIP_SHA='ea0196a0366877ee116ca576c204b21b3884c9bf8ebd417d08360f0496b1531b'
GROUPS=('wait','dispatch','global','field','sequence')
SCOPES=((0x08055000,0x08057f00),(0x08068ddc,0x08068df8),(0x080690b4,0x080693a4),(0x0806b138,0x0806b148),(0x081c7ac8,0x081c7ad0))
FIELD_TARGETS=(0x080565c4,0x080565f0,0x080565dc,0x080565e6,0x080565f8)
UNREAD={0:0x08055b71,2:0x080555f1,3:0x08055ead}
need=s.need


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-field.zip') as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence')
            parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def field_data(rows):
    need(type(rows)is list and len(rows)==5,'field slot数')
    for i,(r,target)in enumerate(zip(rows,FIELD_TARGETS)):
        need(r=={'state':i,'address':d.FIELD_TABLE+4*i,'hex':d.word(target).hex(),'target':target,'decode_root':target|1},'candidate field slot差分')
    return b''.join(bytes.fromhex(r['hex'])for r in rows)


def carry_segments(segments,machine):
    """毎tickのRAMを前tickの結果から写す。状態/PC/LRのpatchや成功stubはしない。"""
    return [(at,bytes(machine.mem[at+i]for i in range(len(data))),writable)for at,data,writable in segments]


def contracts(c,group):
    need(group in GROUPS,'group境界')
    nodes=[n for n in c['nodes']if any(lo<=n['address']<hi for lo,hi in SCOPES)]
    cases=vm.Cases(nodes);run=cases.run
    slots=d.slot_segments(c['story_dispatch_frontier']['command_slots'])
    if group in ('wait','dispatch','global'):
        for flag in range(256):
            seg=[(d.BUSY,bytes([flag]),False)];writes=[]
            if group=='wait':entry=d.WAIT;args=();value=int(flag==0)
            else:
                seg=d.segments(2,d.SCRIPT,d.WAIT)+seg
                entry,args=(0x080690c5,(d.C,))if group=='dispatch'else(0x08069369,())
                writes=([(d.LOCK,1,1)]if group=='global'else[])+([(d.C+1,1,1)]if flag==0 else[]);value=1
            run(group+'-'+str(flag),entry,seg,args,writes,value)
    elif group=='field':
        data=field_data(c['story_field_frontier']['field_slots'])
        for state in range(5):
            seg=[(d.FIELD_STATE,bytes([state]),True),(d.FIELD_TABLE,data,False)]
            stop=('保存node境界で停止',UNREAD[state]&~1)if state in UNREAD else None
            writes=[(d.FIELD_STATE,1,2)]if state==1 else[]
            run('field-'+str(state),0x08056599,seg,(d.FIELD_STATE,),writes,int(state==4),stop)
        run('field-wrapper-one',0x080560c9,[(d.FIELD_STATE,b'\x01',True),(d.FIELD_TABLE,data,False)],writes=[(d.FIELD_STATE,1,2)])
    elif group=='sequence':
        for flag in (0,1,2,255):
            seg=d.segments(1,d.SCRIPT)+[(d.SCRIPT,b'\x66\xff',False),(d.NULL_PTR,d.word(0),False),(d.BUSY,bytes([flag]),False),*slots]
            expected=[[(d.LOCK,1,1),(d.C+8,4,d.SCRIPT+1),(d.C+1,1,2),(d.C+4,4,d.WAIT)],
                [(d.LOCK,1,1)]+([(d.C+1,1,1)]if flag==0 else[]),
                [(d.LOCK,1,1)]+([(d.C+8,4,d.SCRIPT+2),(d.C+1,1,0),(d.STATE,1,2),(d.LOCK,1,0)]if flag==0 else[])]
            previous=None
            for tick,writes in enumerate(expected):
                incoming=vm.b.Expected(seg).image()
                if previous is not None:need(incoming==previous,'連続tick RAM非連続')
                m=run(f'sequence-{flag}-{tick}',0x08069369,seg,writes=writes,value=0 if flag==0 and tick==2 else 1)
                row=cases.rows[-1];row['incoming_object_sha256']=incoming;row['previous_final_object_sha256']=previous
                row['host_memory_writes_between_ticks']=0;previous=row['final_object_sha256']
                seg=carry_segments(seg,m)
    return cases


@functools.lru_cache(maxsize=1)
def verified_groups():
    c=payload('saved-context.json');return {g:contracts(c,g)for g in GROUPS}


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis']
    need(c['story_field_frontier']=={k:v for k,v in a.items()if k!='export_manifest'},'保存field原本')
    need(len(c['nodes'])==9012 and a['candidate']==s.CANDIDATE and a['new_node_count']==191,'保存candidate/node境界')
    rows=[];sites=set()
    for g in GROUPS:
        cases=verified_groups()[g];rows+=cases.rows;sites|=cases.sites
    r={'classification':'SAVED_REAL_WAIT_SCRIPT_TICKS_AND_FIELD_CONDITIONS_NOT_NORMAL_STORY',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'cases':rows,'executed_saved_sites':sorted(sites),
        'actual_wait_callback':d.WAIT,'actual_message_state':d.BUSY,'field_state_targets':list(FIELD_TARGETS),
        'field_unread_callees':{str(k):v for k,v in UNREAD.items()},
        'completed_ticks_from_initial_hidden':3,'host_memory_writes_between_ticks':0,
        'actual_message_display_observed':False,'initial_message_state_is_explicit_premise':True,
        'candidate_reconstructions':0,'rom_changes':0,'new_emulator_processes':0,'new_node_count':0,'new_window_bytes':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'実66→wait→終了のRAM連続3tick。hidden初期条件だけ完了しbusyは待機を保持。field0/2/3は未読calleeで停止。通常story初期化やRing取得の証明ではない。'}
    files=exporter.source_export((SELF,TEST,*SOURCES))
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-field.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));need(s.identity(z.read('export/manifest.json'))==a['export_manifest'],'export manifest binding')
        for p,raw in files.items():
            if p in manifest['files']:need(s.identity(raw)==manifest['files'][p]['identity'],'保存model source差分 '+p)
    r['executed_source_bindings']={p:s.identity(raw)for p,raw in files.items()}
    files['saved-context.json']=s.stable(dict(c,story_wait_lifecycle=r))
    for name in('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'実wait callbackの全u8とscript連続3tick、field状態を{r["contract_cases"]}条件で結合。hiddenなら66→待機解除→終了/lock解除、busyなら待機継続。tick間host書込0、候補復元/native0。',
        'field0初期化08055B71、field3callback08055EAD、field2flash080555F1の未読calleeを限定し、window/font供給と通常story到達へ結合する。旧byte/1037条件/今回786条件/BP/nativeは単独再実行しない。Ring通常取得/装備/保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_wait_lifecycle']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
