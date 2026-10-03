#!/usr/bin/env python3
"""保存field初期化の停止点とcallback終了契約。通常callback登録を仮定しない。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_initializer_frontier as prior
import pr16_ring_story_wait_lifecycle as life
import pr16_ring_story_dispatch_contracts as d
import pr16_ring_story_caller_frontier as archive
import pr16_ring_explicit_text_machine as vm
import pr16_ring_followup_v2 as s

BASE='c6e4bbaac07fa1343a0428aa0095ea8d2e8757a2'
SLUG='pr16-ring-story-initializer-contracts'
TASK='PR-P08-7-RING-STORY-INITIALIZER-CONTRACTS'
TITLE='field callbackの待機・消去・部分書込と初期化資源の停止境界を条件付き検証'
SELF='scripts/pr16_ring_story_initializer_contracts.py'
TEST='tests/test_pr16_ring_story_initializer_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-story-initializer-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_initializer_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
SOURCES=(prior.SELF,life.SELF,d.SELF,archive.SELF,vm.SELF,'scripts/pr16_ring_message_task_frontier.py')
NETWORK='成功run35321072525のhash固定exportと保存candidate命令のみ。外部source追加/候補復元/ROM変更/native0。'
NO_REPEAT='flash全u8、field callbackの優先順位/false待機/true消去/拒否時部分書込、state3→4連続RAM、初期化資源停止の540条件は原本を再利用。callbackに渡した保存getterは合成初期条件で通常登録の証拠ではない。次はheap reset0804B85DとBG供給/default callbackの未解決owner。旧byte/1037+786+540条件/BP/native単独再実行禁止。'
ARTIFACT=10537685396
ZIP_SHA='09b74455005e36593a38879c7131f70d4178e8db31f04c024cfbe237d2b4f225'
CB1,CB2,FLASH,SAVE_PTR,SAVE=0x03005060,0x03005064,0x080555f1,0x03005048,0x02010000
CALLBACK=0x08055ead
UNKNOWN=0x08000111
GROUPS=('flash','callback2','callback1','boundaries','resources','field')
need=s.need
word=d.word


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-initializer.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence');parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def flash(flag):
    need(type(flag)is int and 0<=flag<256,'flash u8')
    return [(SAVE_PTR,word(SAVE),False),(SAVE+0x30,bytes([flag]),False)]


def callbacks(cb2,cb1=UNKNOWN):return [(CB2,word(cb2),True),(CB1,word(cb1),True)]


def contracts(c,group):
    need(group in GROUPS,'group境界')
    cases=vm.Cases(c['nodes']);run=cases.run
    if group=='flash':
        for flag in range(256):run('flash-'+str(flag),FLASH,flash(flag),value=flag)
    elif group=='callback2':
        # 実保存getterを合成callbackへ指定する条件。通常storyでの登録は証明しない。
        for flag in range(256):
            writes=[(CB2,4,0),(CB1,4,0)]if flag else[]
            run('callback2-'+str(flag),CALLBACK,callbacks(FLASH)+flash(flag),writes=writes,value=int(flag!=0))
    elif group=='callback1':
        for flag in (0,1,2,255):
            run('callback1-'+str(flag),CALLBACK,callbacks(0,FLASH)+flash(flag),writes=[(CB1,4,0)],value=1)
    elif group=='boundaries':
        run('default-callback-unread',CALLBACK,callbacks(0,0),stop=('保存node境界で停止',0x0807d694))
        for label,cb2,cb1 in (('unknown2',UNKNOWN,0),('unknown1',0,UNKNOWN),('arm2',FLASH&~1,0),('arm1',0,FLASH&~1)):
            stop=('ARM state未対応',0x081c7ac8)if label.startswith('arm')else('保存node境界で停止',UNKNOWN&~1)
            run(label,CALLBACK,callbacks(cb2,cb1),stop=stop)
        run('priority-false-no-cb1-read',CALLBACK,[(CB2,word(FLASH),True)]+flash(0),value=0)
        run('partial-clear-before-cb1-denied',CALLBACK,[(CB2,word(FLASH),True)]+flash(1),writes=[(CB2,4,0)],stop=('未許可 write',0x08055ece))
        run('readonly-cb2-clear-denied',CALLBACK,[(CB2,word(FLASH),False),(CB1,word(0),True)]+flash(1),stop=('未許可 write',0x08055eca))
        run('missing-cb2-object',CALLBACK,[],stop=('未map read',0x08055eb0),fault={'address':CB2,'size':4,'site':0x08055eb0})
        run('missing-save-pointer',FLASH,[],stop=('未map read',0x080555f2),fault={'address':SAVE_PTR,'size':4,'site':0x080555f2})
    elif group=='resources':
        run('initializer-heap-reset-unread',0x08055b71,[],stop=('保存node境界で停止',0x0804b85c))
        run('screen-gpu-register-unread',0x08056741,[],stop=('保存node境界で停止',0x08000a38))
        run('windows-bg-supplier-unmapped',0x080f7cc5,[],stop=('未map read',0x08001200),fault={'address':0x030008d0,'size':1,'site':0x08001200})
        run('printer-bg-x-unread',0x080f7cf1,[],stop=('保存node境界で停止',0x08001b90))
    elif group=='field':
        table=life.field_data(c['story_field_frontier']['field_slots'])
        def state_segments(state):return [(d.FIELD_STATE,bytes([state]),True),(d.FIELD_TABLE,table,False)]
        run('field0-heap-boundary',0x08056599,state_segments(0),(d.FIELD_STATE,),stop=('保存node境界で停止',0x0804b85c))
        for flag in (0,1,255):
            run('field2-flash-'+str(flag),0x08056599,state_segments(2)+flash(flag),(d.FIELD_STATE,),stop=('保存node境界で停止',0x0807e7a4 if flag else 0x080f77e8))
        for flag in (0,1,255):
            seg=state_segments(3)+callbacks(FLASH)+flash(flag);previous=None
            for tick in range(2):
                incoming=vm.b.Expected(seg).image()
                if previous is not None:need(previous==incoming,'field連続RAM不一致')
                writes=[(CB2,4,0),(CB1,4,0),(d.FIELD_STATE,1,4)]if flag and tick==0 else[]
                m=run(f'field3-sequence-{flag}-{tick}',0x08056599,seg,(d.FIELD_STATE,),writes,int(bool(flag)and tick==1))
                row=cases.rows[-1];row.update(incoming_object_sha256=incoming,previous_final_object_sha256=previous,host_memory_writes_between_ticks=0)
                previous=row['final_object_sha256'];seg=life.carry_segments(seg,m)
    return cases


@functools.lru_cache(maxsize=1)
def verified_groups():
    c=payload('saved-context.json');return {g:contracts(c,g)for g in GROUPS}


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis']
    need(c['story_initializer_frontier']=={k:v for k,v in a.items()if k!='export_manifest'},'保存initializer原本')
    need(len(c['nodes'])==9186 and a['candidate']==s.CANDIDATE and a['new_node_count']==174,'保存candidate/node境界')
    rows=[];sites=set()
    for group in GROUPS:
        cases=verified_groups()[group];rows+=cases.rows;sites|=cases.sites
    need(len(rows)==540,'限定case数')
    r={'classification':'SAVED_INITIALIZER_CALLBACK_CONDITIONS_NOT_NORMAL_REGISTRATION_OR_RING_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'contract_cases':len(rows),'cases':rows,'executed_saved_sites':sorted(sites),
        'flash_getter':FLASH,'save_block1_pointer':SAVE_PTR,'field_callback':CALLBACK,'field_callback_globals':[CB1,CB2],
        'synthetic_callback_pointers_are_explicit_premises':True,'normal_field_callback_registration_proven':False,
        'host_memory_writes_between_ticks':0,
        'first_initializer_unread_callee':0x0804b85d,'first_window_resource':{'address':0x030008d0,'size':1,'site':0x08001200},
        'default_field_callback_unread':0x0807d695,'printer_prefix_unread_callee':0x08001b91,
        'field2_unread_callees':[0x080f77e9,0x0807e7a5],
        'inherited_field0_initializer_may_paths':a['field0_initializer_may_paths'],
        'prior_static_graph_replayed':False,'heap_io_window_font_supply_proven':False,
        'candidate_reconstructions':0,'rom_changes':0,'new_emulator_processes':0,'new_node_count':0,'new_window_bytes':0,
        'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,'normal_story_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'保存getterを明示合成callbackとした全u8/field3→4条件。通常callback登録・heap/IO/BG/font/window供給は未証明。first-stopの部分writeを保持し成功stubを入れない。'}
    files=exporter.source_export((SELF,TEST,*SOURCES))
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-initializer.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));need(s.identity(z.read('export/manifest.json'))==a['export_manifest'],'export manifest binding')
        for p,raw in files.items():
            if p in manifest['files']:need(s.identity(raw)==manifest['files'][p]['identity'],'保存model source差分 '+p)
    r['executed_source_bindings']={p:s.identity(raw)for p,raw in files.items()}
    files['saved-context.json']=s.stable(dict(c,story_initializer_contracts=r))
    for name in('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'field初期化の未読停止・実callbackの待機/消去/部分書込・state3→4を{r["contract_cases"]}条件で結合。callback pointerは明示初期条件、tick間RAM書換0。候補復元/native0。',
        'state0の最初の未読0804B85D（heap/save reset）から限定し、実BG供給030008D0・InitWindows・font pointer登録へ結合する。default callback0807D695とfield2境界080F77E9/0807E7A5は別の未解決ownerとして保持。今回540条件/旧1037+786条件/採取済byte/BP/nativeは単独再実行しない。Ring通常story取得/装備/保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_initializer_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
