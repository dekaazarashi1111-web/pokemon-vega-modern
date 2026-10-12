#!/usr/bin/env python3
"""resource帰還を遮る3calleeと8要素switch表だけを有限採取。旧8calleeは再採取しない。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_resource_frontier as prior

BASE='1d461b1dd2d3de04bff61e61861d51bbe3df6470'
SLUG='pr16-ring-resource-tail'
TASK='PR-P08-7-RING-RESOURCE-TAIL'
TITLE='resourceの未読3calleeと8要素分岐表を有限結合'
SELF='scripts/pr16_ring_resource_tail.py'
TEST='tests/test_pr16_ring_resource_tail.py'
WORKFLOW='.github/workflows/pr16-ring-resource-tail.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_resource_tail.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
CALLEES=(0x08000ead,0x0800105d,0x080014dd)
TABLE,COUNT=0x08001224,8
NO_REPEAT=('resource追加3callee/8要素32byte表と表先の有限採取は保存結果を再利用する。'
    '既読2850命令・先の8callee・VarGet/旧external ABI/BP/nativeを単独再実行しない。'
    '保存table targetを実callback選択・実allocation・Ring通常取得の証明へ昇格しない。')
need=prior.need
identity=prior.identity


def plan(analysis):
    expected={'pending_direct_callees':list(CALLEES),'pending_continuations':[],
        'saved_node_count':2850,'cached_node_count':2457,'new_node_count':393,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False}
    need(type(analysis)is dict,'analysis形式')
    for key,value in expected.items():
        need(type(analysis.get(key))is type(value)and analysis[key]==value,'pending/scope差分 '+key)
    nodes={n['address']:n for n in analysis['new_nodes']}
    n=nodes[0x08001212]
    need(n['literal_value']==TABLE and n['literal_address']==0x08001220,'分岐表pointer差分')
    need(nodes[0x08001218]['hex']=='8746' and nodes[0x08001218]['kind']=='indirect'
        and nodes[0x0800120c]['hex']=='0728','MOV PC/8要素範囲差分')
    return list(CALLEES)


def parse_table(raw):
    need(type(raw)is bytes and len(raw)==COUNT*4,'分岐表32byte')
    targets=[int.from_bytes(raw[i:i+4],'little')for i in range(0,len(raw),4)]
    need(all(0x08000000<=v<0x0a000000 and not v&1 for v in targets),'Thumb内分岐表target境界')
    need(all(not TABLE<=v<TABLE+COUNT*4 for v in targets),'分岐先data重複')
    return {'start':TABLE,'length':len(raw),'hex':raw.hex(),'targets':targets,
        'identity':identity(raw),'semantics':'MOV_PC_THUMB_BRANCH_NOT_BX_OR_RUNTIME_CALLBACK_PROOF'}


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,tables=prior.saved_inputs();report=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,report['source_bindings'])
    windows.add_windows(memory,report['analysis']['new_windows'])
    nodes=[*nodes,*report['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    need(len(nodes)==2850,'保存2850命令差分')
    return nodes,memory,tables


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    roots=plan(previous['analysis']);nodes,memory,tables=saved_inputs()
    forbidden=prior.data_bytes([(t['start'],t['length'])for t in tables]+
        [(f.TABLE,f.TABLE_COUNT*4),(TABLE,COUNT*4)])
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'saved_nodes':len(nodes),
        'prior_run':previous['run_id'],'data_ranges':[{'start':TABLE,'length':COUNT*4}],
        'source_bindings':{p:identity((s.ROOT/p).read_bytes())for p in (SELF,TEST,WORKFLOW,PRIOR,*SOURCES)}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    table=parse_table(raw[TABLE-0x08000000:TABLE-0x08000000+COUNT*4])
    roots=sorted(set((*roots,*(v|1 for v in table['targets']))))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier)
    new=result['new_nodes'];points=set(result.pop('points'))|set(range(TABLE,TABLE+COUNT*4))
    prior.validate_new(new,nodes,forbidden)
    windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_RESOURCE_DELEGATES_AND_SWITCH_TABLE_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':[*tables,table],'resource_switch_table':table,
        'new_windows':windows,'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'saved_node_count':len(nodes)+len(new),
        'data_bytes_bound':COUNT*4,'literal_references':[n for n in new if 'literal_address'in n],
        'unbound_runtime_data':copy.deepcopy(previous['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,prior.SELF,'scripts/pr16_ring_dispatch_contracts.py','scripts/pr16_ring_gate_contracts.py',
        'scripts/pr16_ring_caller_contracts.py','scripts/pr16_ring_string_machine.py',
        'scripts/pr16_ring_contract_machine.py','scripts/pr16_ring_saved_contracts.py',
        'scripts/pr16_ring_owner_context.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'resourceの未読3calleeと8要素32byte分岐表を有限結合。新規{result["new_node_count"]}命令/'
        f'{result["new_window_bytes"]}byte、保存命令{result["saved_node_count"]}件。既読再解読/native0。',
        '次は保存命令だけでresource getter/転送/bitmapと12byte record callerの条件付き帰還・書込範囲を結合。'
        '実callback table/32byte出力slot/通常・拡張変数領域のallocationは実証拠と区別する。'
        '今回3callee/32byte表・先の8callee/VarGet/旧external ABI/BP/nativeは単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
