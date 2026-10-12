#!/usr/bin/env python3
"""message状態0/1のselector0一word・palette・r8 thunkだけを追加保存する。"""
from __future__ import annotations
import functools
import sys
import pr16_ring_followup_v2 as s
import pr16_ring_message_task_contracts as prior
import pr16_ring_text_export_recovery as export

BASE='5dba0681032c255ef52a36b6e0fb65165d8ab740'
SLUG='pr16-ring-message-window-frontier'
TASK='PR-P08-7-RING-MESSAGE-WINDOW-FRONTIER'
TITLE='状態0/1のwindow属性0・palette・frame中継の未読境界を保存'
SELF='scripts/pr16_ring_message_window_frontier.py'
TEST='tests/test_pr16_ring_message_window_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-message-window-frontier.yml'
PRIOR='content/modernization/pr16_ring_message_task_checkpoint.json'
REPORT='content/modernization/pr16_ring_message_window_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.REPORT,prior.PRIOR,*prior.SOURCES)))
TABLE=0x08004938
DIRECT=(0x0806fb91,0x081c7ae9)
CALLS=((0x080f8820,0x0806fb91),(0x08004872,0x081c7ae9))
FALSE=('task_state01_complete_proven','task_state_transitions_proven','task_runtime_observed',
       'task_scheduler_execution_observed','normal_story_observed','initializer_runtime_observed',
       'actual_callback_table_observed','dma_execution_observed','ring_acquisition_accepted','release_ready')
NO_REPEAT=('window属性selector0の一word/選択body・palette0806FB91・frame thunk081C7AE9は保存原本を再利用。'
    '次は状態0/1の条件付き効果/帰還/不足を保存命令で検証。今回採取・旧1231条件/391条件/BP/nativeは単独再実行しない。')
need=s.need


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    c=prior.saved_inputs();r=s.load(prior.REPORT);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    a={k:v for k,v in r['analysis'].items() if k not in ('cases','state2_sequences','executed_sites')}
    return dict(c,task_contracts=a)


def plan(c):
    prior.validate_inputs(c);a=c['task_contracts'];by={n['address']:n for n in c['nodes']}
    need(a['candidate']==s.CANDIDATE and a['contract_cases']==1231 and a['conditional_return_cases']==914
         and a['pending_stop_cases']==317 and a['same_ram_state2_sequences']==96,'保存成功集合')
    need(a['pending_window_attribute']==dict(entry=0x0800491d,table=TABLE,needed_selector=0,table_word_observed=False),'属性0未読')
    need(a['pending_palette_entry']==DIRECT[0] and a['pending_frame_thunk']==DIRECT[1]
         and a['saved_frame_callback']==0x080f8185,'指定callee/保存callback')
    for key in FALSE:need(a[key] is False,'未受入境界 '+key)
    need(a['task_full_boundary']['busy_after']==2 and a['task_full_boundary']['liveness_proven'] is False,'満杯境界保持')
    exact={0x08004926:'0728',0x0800492a:'8000',0x0800492c:'0149',0x0800492e:'4018',
           0x08004930:'0068',0x08004932:'8746',0x08153068:'0021',0x08004840:'8846'}
    for at,raw in exact.items():need(by[at]['hex']==raw,'属性/callback命令 '+hex(at))
    need(by[0x0800492c]['literal_value']==TABLE,'属性表出自')
    for at,target in CALLS:
        need(by[at]['kind']=='call' and by[at]['target']==target&~1,'callee出自')
    need(all(t&~1 not in by for t in DIRECT),'callee再採取禁止')
    return {'direct_roots':list(DIRECT),'selector':0,'table_word_address':TABLE,'table_word_bytes':4,
            'forbidden_table_range':[TABLE,TABLE+32],'max_nodes':1024,'max_bytes':4096,
            'expand_direct_calls':False,'saved_nodes_redecoded':0,'accepted_contract_cases_replayed':0}


def table_target(raw):
    need(type(raw)is bytes and len(raw)==4,'selector0 word長')
    target=int.from_bytes(raw,'little')
    need(0x08000000<=target<0x0a000000 and not target&1 and not TABLE<=target<TABLE+32,'MOV-PC target範囲')
    return target


def validate_new(r,c,target):
    roots=sorted((*DIRECT,target|1));known={p for n in c['nodes'] for p in range(n['address'],n['address']+n['size'])}
    need(r['initial_roots']==roots and not r['saved_roots_reused'],'指定3根のみ')
    need(r['saved_nodes_redecoded']==r['direct_calls_recursively_expanded']==0,'既読/再帰禁止')
    starts=[n['address'] for n in r['new_nodes']]
    need(0<len(starts)<=1024 and starts==sorted(set(starts)),'新規node予算/重複')
    for n in r['new_nodes']:
        at,size=n['address'],n['size'];span=set(range(at,at+size))
        need(type(at)is int and not at%2 and size in (2,4) and 0x08000000<=at<at+size<=0x0a000000,'命令範囲')
        need(not span&known and not span&set(range(TABLE,TABLE+32)),'既読/data解読禁止')
        need(len(bytes.fromhex(n['hex']))==size,'命令byte長');known|=span
    return known


def analyze(previous,out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_message_owner_frontier as memory_source
    import pr16_ring_message_task_frontier as exporter
    c=saved_inputs();bound=plan(c);nodes=c['nodes']
    need(previous['analysis']['reused_contract_cases']==1231,'checkpoint照合')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':bound,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes()) for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    word=raw[TABLE-0x08000000:TABLE-0x08000000+4];target=table_target(word)
    forbidden=set(range(TABLE,TABLE+32))
    for n in nodes:
        if 'literal_address'in n:forbidden.update(range(n['literal_address'],n['literal_address']+4))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'保存dataを命令解読しない')
        return decoder.thumb_instruction(data,at)
    r=walk.bounded_walk(raw,sorted((*DIRECT,target|1)),old.cache_nodes([{'nodes':nodes}]),decode,
        old.inspect_frontier,max_nodes=1024,max_bytes=4096,max_roots=64,max_rounds=8)
    validate_new(r,c,target)
    _,memory,_,_=memory_source.saved_inputs();memory=dict(memory)
    for n in nodes:
        for i,v in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=v
        if 'literal_address'in n:
            for i,v in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=v
    windows,reused=old.new_windows(raw,r.pop('points'),memory)
    data,reused_data=old.new_windows(raw,list(range(TABLE,TABLE+4)),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate変更')
    r.update({k:False for k in FALSE})
    r.update({'classification':'WINDOW_SELECTOR0_PALETTE_FRAME_BYTES_NOT_NATIVE_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'plan':bound,'selector0':{'table':TABLE,'selector':0,'hex':word.hex(),'target':target,**s.identity(word)},
        'new_windows':windows,'new_data_windows':data,'new_node_count':len(r['new_nodes']),
        'saved_node_count':len(nodes)+len(r['new_nodes']),'saved_bytes_reused':reused+reused_data,
        'new_window_bytes':sum(w['end']-w['start'] for w in [*windows,*data]),'candidate_reconstructions':1,
        'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,'successful_callee_stubs':0,
        'boundary_ja':'属性0だけ。selector1..7・新BL・palette実DMA・r8 live-frame・通常storyは未証明。'})
    files=exporter.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    files['saved-context.json']=s.stable(dict(c,nodes=[*nodes,*r['new_nodes']],window_frontier=r))
    manifest=export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    r['export_logical_files']=len(manifest['files']);(out/'analysis.json').write_bytes(s.stable(r))
    return r


def summaries(r):
    return (f'window属性0の一word/選択body、palette、frame thunkを新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteで保存。旧8251命令再解読/1231条件再実行/native0。',
        '次は保存命令でmessage task状態0/1のwindow属性・paletteコピー・r8 frame callbackを条件付き結合検証。'
        '新BL/資源不足は成功stubなしで停止。今回採取/旧1231条件/391条件/BP/nativeを単独再実行しない。'
        '通常story/Ring取得・live初期化・task満杯busy2は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
