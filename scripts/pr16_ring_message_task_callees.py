#!/usr/bin/env python3
"""保存taskの七つの未読calleeだけを一回の候補復元で保存する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_message_task_frontier as prior
import pr16_ring_followup_v2 as s
import pr16_ring_text_export_recovery as export

BASE = '726e026d46d1b5aca67a34354bb35638396fdf45'
SLUG = 'pr16-ring-message-task-callees'
TASK = 'PR-P08-7-RING-MESSAGE-TASK-CALLEES'
TITLE = 'message taskの待機・終了・window分岐の七calleeを限定保存'
SELF = 'scripts/pr16_ring_message_task_callees.py'
TEST = 'tests/test_pr16_ring_message_task_callees.py'
WORKFLOW = '.github/workflows/pr16-ring-message-task-callees.yml'
PRIOR = prior.REPORT
REPORT = 'content/modernization/pr16_ring_message_task_callees.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 24
EXTRA_CODE = ()
SOURCES = tuple(dict.fromkeys((prior.SELF, prior.PRIOR, *prior.SOURCES)))
NO_REPEAT = ('保存task08068C31の七callee採取は原本を再利用。新規callは再帰採取せず未読境界を保持。'
    '次は保存命令で待機/終了/task削除/window分岐/不足を結合。今回採取/前回62命令/旧391条件/BP/nativeは単独再実行しない。')
CALLS = ((0x08068c76,0x0815305d), (0x08068c84,0x080692f9),
    (0x08068c8e,0x080f7efd), (0x08068c94,0x080f8a05),
    (0x08068c9e,0x080f7f45), (0x08068caa,0x080f7d15), (0x08068cbe,0x08076ca1))
ROOTS = tuple(sorted(target for _,target in CALLS))
need = s.need


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,a,inherited,owner = prior.prior.saved_inputs()
    report = s.load(PRIOR); saved.bindings_fresh(s.ROOT,report['source_bindings'])
    return {'nodes': [*nodes,*report['analysis']['new_nodes']], 'analysis': a,
        'inherited_analysis': inherited, 'owner_analysis': owner,
        'message_summary': s.load(prior.PRIOR)['analysis'], 'task_frontier': report['analysis']}


def plan(context):
    nodes = context['nodes']; a = context['task_frontier']; by = {r['address']:r for r in nodes}
    need(len(by)==len(nodes)==7371,'保存7371命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==62 and a['new_window_bytes']==154,'先行identity')
    need(a['pending_direct_callees']==list(ROOTS) and not a['pending_continuations'],'未読七callee集合')
    need(all(target&~1 not in by for target in ROOTS),'既読callee再採取禁止')
    for site,target in CALLS:
        n=by.get(site,{})
        need(n.get('kind')=='call' and n.get('size')==4 and n.get('target')==target&~1,'保存task BL '+hex(site))
    for key in ('task_state_transitions_proven','task_runtime_observed','initializer_runtime_observed',
                'actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
        need(a[key] is False,'未受入境界 '+key)
    return {'roots':list(ROOTS),'saved_callsite_bindings':[dict(site=p,target=t) for p,t in CALLS],
        'max_nodes':1024,'max_bytes':4096,'max_roots':64,'max_rounds':8,
        'expand_direct_calls':False,'redecode_saved_nodes':False,'normal_story_observed':False}


def validate_result(result,known):
    need(result['initial_roots']==list(ROOTS) and not result['saved_roots_reused'],'七根のみ')
    need(result['saved_nodes_redecoded']==result['direct_calls_recursively_expanded']==0,'既読/再帰禁止')
    nodes=result['new_nodes']; starts=[r['address'] for r in nodes]
    need(0<len(nodes)<=1024 and starts==sorted(set(starts)),'新規命令集合')
    occupied=set()
    for n in nodes:
        at,size=n['address'],n['size']
        need(type(at)is int and at%2==0 and size in (2,4) and 0x08000000<=at<at+size<=0x0a000000,'命令範囲')
        need(n['kind'] in ('ordinary','call','jump','conditional','indirect','return'),'命令分類')
        span=set(range(at,at+size));need(not span&(occupied|known),'既読/新規重複');occupied|=span
        need(len(bytes.fromhex(n['hex']))==size,'命令byte長')
        if 'literal_address'in n:
            p=n['literal_address'];need(type(p)is int and p%4==0 and 0x08000000<=p<=0x09fffffc,'literal範囲')
    return occupied


def analyze(previous,out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    context=saved_inputs(); nodes=context['nodes']; bound=plan(context)
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'plan':bound,
        'source_bindings':{p:s.identity((s.ROOT/p).read_bytes()) for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    result=walk.bounded_walk(raw,list(ROOTS),old.cache_nodes([{'nodes':nodes}]),
        decoder.thumb_instruction,old.inspect_frontier,max_nodes=1024,max_bytes=4096,max_roots=64,max_rounds=8)
    known={at for n in nodes for at in range(n['address'],n['address']+n['size'])}
    validate_result(result,known)
    # 保存済み命令/literalと前工程の保存窓だけを再利用し、新規byteだけ記録する。
    _,memory,_,_=prior.prior.prior.saved_inputs();memory=dict(memory)
    for n in nodes:
        for i,v in enumerate(bytes.fromhex(n['hex'])):memory[n['address']+i]=v
        if 'literal_address'in n:
            for i,v in enumerate(n['literal_value'].to_bytes(4,'little')):memory[n['literal_address']+i]=v
    windows,reused=old.new_windows(raw,result.pop('points'),memory)
    need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate変更')
    result.update({'classification':'MESSAGE_TASK_SEVEN_CALLEE_BYTES_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'plan':bound,'new_windows':windows,'new_node_count':len(result['new_nodes']),
        'saved_node_count':len(nodes)+len(result['new_nodes']),
        'new_window_bytes':sum(w['end']-w['start'] for w in windows),'saved_bytes_reused':reused,
        'candidate_reconstructions':1,'rom_changes':0,'new_emulator_processes':0,'full_rom_scans':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'task_state_transitions_proven':False,'task_runtime_observed':False,'normal_story_observed':False,
        'initializer_runtime_observed':False,'actual_callback_table_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'保存七calleeのbyteのみ。新規未読BL/間接辺/継続上限は未証明。状態遷移と効果は次工程。'})
    updated=dict(context,nodes=[*nodes,*result['new_nodes']],task_callees=result)
    files=prior.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    files['saved-context.json']=s.stable(updated)
    manifest=export.bundle(files,out/'export')
    result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    result['export_logical_files']=len(manifest['files'])
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'message taskの待機/終了/削除/window分岐七calleeを新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteで保存。旧7371命令の再解読/native0。',
        '次は保存taskと七calleeの状態遷移・待機/終了・削除・不足時の部分writeを結合検証。'
        '新規未読callee/間接辺は成功stubなしで停止し、上流busy/通常story/live window初期化を混同しない。今回採取/旧391条件/BP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12)
    s.run(sys.modules[__name__])
