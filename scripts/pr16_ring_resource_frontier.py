#!/usr/bin/env python3
"""未読resource 8calleeだけを有限採取。保存2457命令/VarGet/BPは再実行しない。"""
from __future__ import annotations
import copy
import hashlib
import sys

BASE='d966a41f8856e8d940ad1c5f6ef0a97e462de9c5'
SLUG='pr16-ring-resource-frontier'
TASK='PR-P08-7-RING-RESOURCE-FRONTIER'
TITLE='未読resource 8calleeを保存2457命令へ有限結合'
SELF='scripts/pr16_ring_resource_frontier.py'
TEST='tests/test_pr16_ring_resource_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-resource-frontier.yml'
PRIOR='content/modernization/pr16_ring_varget_join.json'
REPORT='content/modernization/pr16_ring_resource_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=40
EXTRA_CODE=()
CALLEES=(0x080011e5,0x08001299,0x080014f1,0x0800273d,0x080027ad,0x08002899,0x080028ed,0x08002901)
SOURCES=('scripts/pr16_ring_dispatch_frontier.py','scripts/pr16_ring_remaining_frontier.py',
    'scripts/pr16_ring_owner_frontier.py','scripts/pr16_ring_effective_frontier.py',
    'scripts/pr16_ring_branch_frontier.py','scripts/pr16_ring_zero_bytes.py',
    'scripts/pr16_ring_transitive_owner.py','scripts/pr16_ring_flagset_continuation.py',
    'scripts/pr16_ring_selector_reuse.py','content/modernization/pr16_ring_selector_reuse.json',
    'content/modernization/pr16_ring_dispatch_frontier.json')
NO_REPEAT=('未読resource 8calleeの有限採取は保存原本を再利用する。既読2457命令/VarGet selector縦結合/旧external ABI/BP/nativeを単独再実行しない。'
    '新規calleeや間接辺はstubで補わず、保存命令からresource/callback/出力slotの条件付き帰還とallocationを結合する。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def plan(analysis):
    expected={'pending_direct_callees':list(CALLEES),'pending_effective_targets':[],
        'pending_data_ranges':[],'pending_continuations':[],
        'known_callees_awaiting_caller_contracts':[],'saved_node_count':2457,
        'synthetic_selector_returns_proven':True,'selector_callee_arguments_bound':True,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False}
    need(type(analysis)is dict,'analysis形式')
    for key,value in expected.items():
        need(type(analysis.get(key))is type(value) and analysis[key]==value,'pending/scope差分 '+key)
    return list(CALLEES)


def data_bytes(ranges):
    need(type(ranges)in (tuple,list),'data範囲形式');points=set()
    for start,length in ranges:
        need(type(start)is int and type(length)is int and length>0 and
            0x08000000<=start<start+length<=0x0a000000,'data範囲境界')
        need(length<=65536 and len(points)+length<=262144,'data範囲上限')
        points.update(range(start,start+length))
    return points


def validate_new(nodes,cached,forbidden):
    occupied={p for n in cached for p in range(n['address'],n['address']+n['size'])}
    fresh=set()
    for n in nodes:
        at,size=n['address'],n['size']
        need(type(at)is int and at%2==0 and type(size)is int and size in (2,4),'新node整列/幅')
        need(0x08000000<=at<at+size<=0x0a000000 and len(bytes.fromhex(n['hex']))==size,'新node byte境界')
        points=set(range(at,at+size))
        need(not points&(occupied|fresh|forbidden),'新code/data/保存operand重複')
        fresh.update(points)
    return len(fresh)


def preflight(root,paths,analysis,run):
    roots=plan(analysis)
    need(type(paths)in (tuple,list) and paths,'source一覧')
    need(type(run)is int and run>0,'先行run形式')
    return {'source_bindings':{p:identity((root/p).read_bytes())for p in paths},
        'roots':roots,'prior_run':run,'saved_nodes':2457,'data_ranges':[]}


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_dispatch_frontier as previous
    import pr16_ring_selector_reuse as reuse
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,tables=previous.saved_inputs()
    report=s.load(previous.REPORT);external=s.load(reuse.REPORT)
    for value in (report,external):saved.bindings_fresh(s.ROOT,value['source_bindings'])
    windows.add_windows(memory,report['analysis']['new_windows'])
    nodes=[*nodes,*report['analysis']['new_nodes'],*external['analysis']['reused_external_nodes']]
    need(len(nodes)==2457 and len({n['address']for n in nodes})==2457,'保存node数/重複')
    f.nodes_to_memory(memory,nodes)
    return nodes,memory,copy.deepcopy(report['analysis']['tables'])


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    roots=plan(prior['analysis']);nodes,memory,tables=saved_inputs()
    forbidden=data_bytes([(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)])
    (out/'preflight.json').write_bytes(s.stable(preflight(s.ROOT,
        tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES))),prior['analysis'],prior['run_id'])))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier)
    new=result['new_nodes'];points=result.pop('points')
    validate_new(new,nodes,forbidden)
    windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_RESOURCE_EIGHT_CALLEES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':tables,'new_windows':windows,
        'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'saved_node_count':len(nodes)+len(new),
        'data_bytes_bound':0,'literal_references':[n for n in new if 'literal_address'in n],
        'unbound_runtime_data':copy.deepcopy(prior['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,'scripts/pr16_ring_dispatch_contracts.py','scripts/pr16_ring_gate_contracts.py',
        'scripts/pr16_ring_caller_contracts.py','scripts/pr16_ring_string_machine.py',
        'scripts/pr16_ring_contract_machine.py','scripts/pr16_ring_saved_contracts.py',
        'scripts/pr16_ring_owner_context.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'未読resource 8calleeを保存2457命令へ有限結合。新規{result["new_node_count"]}命令/'
        f'{result["new_window_bytes"]}byte、既読再解読/全ROM走査/native0。',
        '次は保存したresource 8calleeを実callback table/12byte resource/32byte出力slotの引数・帰還・書込範囲へ結合する。'
        '未知callee/間接辺はstub化せず残す。実allocation/通常・拡張変数領域との結合、Ring正規story取得・装備実戦・保存は未受入。'
        '同じ8callee採取・保存2457命令・VarGet selector1/2・旧external ABI/7graph・BP/nativeを単独再実行しない。'
        'policy/Circus/P08へscopeを拡大しない。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
