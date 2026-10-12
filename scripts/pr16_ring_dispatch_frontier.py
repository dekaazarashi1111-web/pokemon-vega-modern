#!/usr/bin/env python3
"""未読4callee/VarGetの2継続だけを有限採取。既読2107命令は再解読しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='5e8d6025997a964805bd26893ef3fef3686e2b96'
SLUG='pr16-ring-dispatch-frontier'
TASK='PR-P08-7-RING-DISPATCH-FRONTIER'
TITLE='4calleeとVarGetの2継続を保存2107命令へ有限結合'
SELF='scripts/pr16_ring_dispatch_frontier.py'
TEST='tests/test_pr16_ring_dispatch_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-dispatch-frontier.yml'
PRIOR='content/modernization/pr16_ring_gate_contracts.json'
REPORT='content/modernization/pr16_ring_dispatch_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=23
EXTRA_CODE=()
SOURCES=()
CALLEES=(0x080017d1,0x080020bd,0x081c7acd,0x09128221)
EFFECTIVE=(0x0806dc51,0x0806dc57)
NO_REPEAT=('4calleeとVarGetの2継続の有限採取は保存原本を再利用する。'
    '既読2107命令・81要素展開・非null帰還・265caller・11文字列・BP/nativeの単独再実行は禁止。'
    '未読callee/間接callbackと実allocation条件は未証明のまま、次は保存byteの契約結合へ進む。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def plan(analysis):
    expected={'pending_direct_callees':list(CALLEES),'pending_effective_targets':list(EFFECTIVE),
        'pending_data_ranges':[],'pending_continuations':[],'saved_node_count':2107,
        'specific_nonnull_return_proven':True,'slot_safety_requires_caller_allocation':True,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False}
    need(type(analysis)is dict,'analysis形式')
    for k,v in expected.items():need(type(analysis.get(k))is type(v) and analysis[k]==v,'pending/scope差分 '+k)
    return sorted((*CALLEES,*EFFECTIVE))


def preflight(root,paths,analysis,run):
    roots=plan(analysis);need(type(paths)in (list,tuple)and paths,'source一覧')
    need(type(run)is int and run>0,'先行run形式')
    return {'source_bindings':{p:identity((root/p).read_bytes())for p in paths},
        'roots':roots,'prior_run':run,'saved_nodes':2107,'data_ranges':[]}


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_gate_frontier as previous
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,_=previous.saved_inputs();report=s.load(previous.REPORT)
    saved.bindings_fresh(s.ROOT,report['source_bindings'])
    windows.add_windows(memory,report['analysis']['new_windows'])
    nodes=[*nodes,*report['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    return nodes,memory,copy.deepcopy(report['analysis']['tables'])


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    roots=plan(prior['analysis']);nodes,memory,tables=saved_inputs();need(len(nodes)==2107,'保存node数')
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
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
    need(not any(set(range(n['address'],n['address']+n['size']))&forbidden for n in new),'新code/data重複')
    windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_DISPATCH_CALLEES_AND_VAR_CONTINUATIONS_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':tables,'new_windows':windows,
        'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'data_bytes_bound':0,
        'literal_references':[n for n in new if 'literal_address'in n],
        'unbound_runtime_data':copy.deepcopy(prior['analysis']['unbound_runtime_data']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,'scripts/pr16_ring_gate_contracts.py','scripts/pr16_ring_caller_contracts.py',
        'scripts/pr16_ring_string_machine.py','scripts/pr16_ring_contract_machine.py',
        'scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'4callee/VarGetの2継続を既読2107命令へ有限結合。新規{result["new_node_count"]}命令/'
        f'{result["new_window_bytes"]}byte、data再採取0、既読再解読/native0。',
        '保存したresource callee・callback trampoline・VarGet helper/継続を実caller引数と帰還/SP/書込範囲へ結合する。'
        '未読先はstubで補わずpendingを保持。callback table/12byte resource records/32byte出力slotの実allocationは別証拠。'
        '既読2107命令/81要素/非null帰還/265caller/11文字列/BP/nativeを単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_gate_contracts as contracts
    import pr16_ring_gate_frontier as previous
    import pr16_ring_caller_contracts as caller
    import pr16_ring_reference_contracts as older
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((contracts.SELF,previous.SELF,caller.SELF,older.SELF,
        caller.prior.SELF,caller.prior.prior.SELF,caller.vm.SELF,caller.vm.flow.SELF,
        previous.PRIOR,previous.REPORT,*older.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
