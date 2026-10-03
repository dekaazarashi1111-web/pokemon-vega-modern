#!/usr/bin/env python3
"""taskの未読8calleeと保存literal由来frame callback一根を限定保存する。"""
from __future__ import annotations
import functools
import sys
import pr16_ring_message_task_callees as prior
import pr16_ring_followup_v2 as s
import pr16_ring_text_export_recovery as export

BASE='faa627a7dad154e66ddebab881fe4122cef50b53'
SLUG='pr16-ring-message-window-bytes'
TASK='PR-P08-7-RING-MESSAGE-WINDOW-BYTES'
TITLE='task終了判定・window資源と保存frame callbackの未読境界を結合'
SELF='scripts/pr16_ring_message_window_bytes.py'
TEST='tests/test_pr16_ring_message_window_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-message-window-bytes.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_message_window_bytes.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.PRIOR,*prior.SOURCES)))
CALLS=((0x080f7d1c,0x08002e3d),(0x080f7f62,0x08003f6d),(0x080f7f54,0x08004839),
    (0x0815306a,0x0800491d),(0x080f7f24,0x080f8819),(0x080f7f30,0x08152f71),
    (0x080f8a12,0x08152fb1),(0x080f7f3c,0x081530e1))
DIRECT=tuple(sorted(t for _,t in CALLS))
FRAME=0x080f8185
ROOTS=tuple(sorted((*DIRECT,FRAME)))
NO_REPEAT=('task終了判定/未読window8calleeとliteral由来frame callbackの採取は保存原本を再利用。'
    '次は保存命令だけで上流script/busy・task待機/終了/削除/window不足を結合。今回/旧採取/旧391条件/BP/nativeは単独再実行しない。')
need=s.need


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    c=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    return dict(c,nodes=[*c['nodes'],*r['analysis']['new_nodes']],task_callees=r['analysis'])


def plan(c):
    by={n['address']:n for n in c['nodes']};a=c['task_callees']
    need(len(by)==len(c['nodes'])==7525,'保存7525命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==154 and a['new_window_bytes']==352,'先行identity')
    need(a['pending_direct_callees']==list(DIRECT) and not a['pending_continuations'],'未読8callee')
    for p,t in CALLS:
        n=by.get(p,{})
        need(n.get('kind')=='call' and n.get('target')==t&~1 and n.get('size')==4,'保存callee出自')
    n=by[0x080f7f50]
    need(n['hex']=='0949' and n['literal_value']==FRAME and n['literal_address']==0x080f7f78,'frame literal出自')
    need(by[0x080f7f52]['hex']=='281c','window id供給')
    need(all(t&~1 not in by for t in ROOTS),'新規9根の再採取禁止')
    for k in ('task_runtime_observed','task_state_transitions_proven','normal_story_observed',
              'initializer_runtime_observed','actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a[k] is False,'未受入境界 '+k)
    return {'roots':list(ROOTS),'direct_callers':[dict(site=p,target=t) for p,t in CALLS],
        'frame_callback':{'pointer':FRAME,'literal_site':0x080f7f50,'callee_callsite':0x080f7f54,
                          'callback_execution_proven':False},
        'max_nodes':1024,'max_bytes':4096,'max_roots':64,'max_rounds':8}


def validate_new(r,known):
    need(r['initial_roots']==list(ROOTS) and not r['saved_roots_reused'],'新規9根')
    need(r['saved_nodes_redecoded']==r['direct_calls_recursively_expanded']==0,'既読/再帰禁止')
    nodes=r['new_nodes'];starts=[n['address'] for n in nodes]
    need(0<len(nodes)<=1024 and starts==sorted(set(starts)),'新規node順序/予算')
    occupied=set()
    for n in nodes:
        at,size=n['address'],n['size'];span=set(range(at,at+size))
        need(type(at)is int and at%2==0 and size in (2,4) and 0x08000000<=at<at+size<=0x0a000000,'命令範囲')
        need(not span&(known|occupied) and len(bytes.fromhex(n['hex']))==size,'重複/byte長');occupied|=span
    return occupied


def analyze(previous,out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    c=saved_inputs();bound=plan(c);nodes=c['nodes']
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':bound,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes()) for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    r=walk.bounded_walk(raw,list(ROOTS),old.cache_nodes([{'nodes':nodes}]),decoder.thumb_instruction,
        old.inspect_frontier,max_nodes=1024,max_bytes=4096,max_roots=64,max_rounds=8)
    known={p for n in nodes for p in range(n['address'],n['address']+n['size'])};validate_new(r,known)
    _,memory,_,_=prior.prior.prior.prior.saved_inputs();memory=dict(memory)
    for n in nodes:
        for i,v in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=v
        if 'literal_address'in n:
            for i,v in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=v
    windows,reused=old.new_windows(raw,r.pop('points'),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate変更')
    r.update({'classification':'MESSAGE_TASK_WINDOW_BYTES_NOT_NATIVE_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'plan':bound,'new_windows':windows,'new_node_count':len(r['new_nodes']),
        'saved_node_count':len(nodes)+len(r['new_nodes']),'new_window_bytes':sum(w['end']-w['start'] for w in windows),
        'saved_bytes_reused':reused,'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'normal_story_observed':False,'task_runtime_observed':False,'initializer_runtime_observed':False,
        'actual_callback_table_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'終了判定とwindow/frameの保存byteのみ。未読BL・資源data・frame ABIと通常storyは未受入。'})
    files=prior.prior.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    files['saved-context.json']=s.stable(dict(c,nodes=[*nodes,*r['new_nodes']],window_bytes=r))
    manifest=export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    r['export_logical_files']=len(manifest['files']);(out/'analysis.json').write_bytes(s.stable(r))
    return r


def summaries(r):
    return (f'task終了判定/8calleeとframe callbackを新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteで保存。旧7525命令再解読/native0。',
        '次は採取を繰り返さず、保存命令で上流script/busy・task待機/終了/削除・window初期化不足を結合検証。'
        '資源data/未読calleeは成功stubなしで停止し、正常story/live gFonts/画面観測へ昇格しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
