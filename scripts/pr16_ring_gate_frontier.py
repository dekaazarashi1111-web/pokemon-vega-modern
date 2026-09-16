#!/usr/bin/env python3
"""保存pendingの3callee/VarGet中継先だけを追加採取。既読解読・data再採取なし。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='12caaea180b12e0ed44c3a3e434af8c0c5a126df'
SLUG='pr16-ring-gate-frontier'
TASK='PR-P08-7-RING-GATE-FRONTIER'
TITLE='3calleeとVarGet実中継先を既読1935命令へ有限結合'
SELF='scripts/pr16_ring_gate_frontier.py'
TEST='tests/test_pr16_ring_gate_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-gate-frontier.yml'
PRIOR='content/modernization/pr16_ring_caller_contracts.json'
REPORT='content/modernization/pr16_ring_gate_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=18
EXTRA_CODE=()
SOURCES=()
CALLEES=(0x08002e4d,0x08002e79,0x08003eed)
EFFECTIVE=(0x090970dd,)
NO_REPEAT=('3callee/VarGet中継先の有限採取を保存原本から再利用する。'
    '同じ候補復元、1935既読命令、11文字列、CreateTask caller265契約、旧795/716/BPを単独再実行しない。'
    '新callee・table・callbackは未証明境界を明記し、全live frameやRing取得へ昇格しない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def plan(analysis):
    expected={'pending_direct_callees':list(CALLEES),'pending_effective_targets':list(EFFECTIVE),
        'pending_data_ranges':[],'pending_continuations':[],'saved_node_count':1935,
        'specific_create_caller_index_lt16_proven':True,'all_live_task_lists_acyclic_proven':False,
        'all_live_string_buffers_large_enough_proven':False,'ring_acquisition_accepted':False,'release_ready':False}
    for k,v in expected.items():need(type(analysis.get(k))is type(v) and analysis[k]==v,'pending/scope差分 '+k)
    return sorted((*CALLEES,*EFFECTIVE))


def preflight(root,paths,analysis,run):
    roots=plan(analysis);need(type(paths)in (list,tuple)and paths,'source一覧')
    return {'source_bindings':{p:identity((root/p).read_bytes())for p in paths},
        'roots':roots,'prior_run':run,'saved_nodes':1935,'data_ranges':[]}


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_text_frontier as previous
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
    roots=plan(prior['analysis']);nodes,memory,tables=saved_inputs();need(len(nodes)==1935,'保存node数')
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
    result.update({'classification':'FINITE_GATE_CALLEES_AND_VAR_IMPLEMENTATION_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':tables,'new_windows':windows,
        'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'data_bytes_bound':0,
        'literal_references':[n for n in new if 'literal_address'in n],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,'scripts/pr16_ring_caller_contracts.py','scripts/pr16_ring_text_frontier.py',
        'scripts/pr16_ring_string_machine.py','scripts/pr16_ring_contract_machine.py',
        'scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'3callee/VarGet実中継先を既読1935命令へ有限結合。新規{result["new_node_count"]}命令/'
        f'{result["new_window_bytes"]}byte、data再採取0、既読再解読/native0。',
        '保存したVarGet実装と3calleeをcallerの引数・戻り値・書込範囲へ結合し、未読table/callbackは推測せずpendingで限定する。'
        'CreateTask/11文字列/非nullprefixの受入済み合成契約は単独再実行しない。'
        '実story Ring取得・装備実戦・保存とpolicy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_caller_contracts as previous
    import pr16_ring_text_frontier as text
    import pr16_ring_reference_contracts as older
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((previous.SELF,text.SELF,older.SELF,previous.prior.SELF,
        previous.prior.prior.SELF,previous.vm.SELF,previous.vm.flow.SELF,*older.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
