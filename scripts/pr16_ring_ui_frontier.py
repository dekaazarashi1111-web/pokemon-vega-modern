#!/usr/bin/env python3
"""固定JPの7入口だけを有限採取し、保存2970命令へ結合する。"""
from __future__ import annotations
import copy
import hashlib
import sys

BASE='6f5bbffc51c90b66b1cbe5c227fb81511391cbb9'
SLUG='pr16-ring-ui-frontier'
TASK='PR-P08-7-RING-UI-FRONTIER'
TITLE='JP text/windowの7入口を未読命令だけで初期化・callback境界へ結合'
SELF='scripts/pr16_ring_ui_frontier.py'
TEST='tests/test_pr16_ring_ui_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-ui-frontier.yml'
PRIOR='content/modernization/pr16_ring_ui_owners.json'
REPORT='content/modernization/pr16_ring_ui_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
ROOTS={'AddTextPrinterParameterized':0x08002c45,'DeactivateAllTextPrinters':0x08002c29,
       'RunTextPrinters':0x08002dd1,'InitWindows':0x08003af1,'AddWindow':0x08003cb1,
       'RemoveWindow':0x08003e09,'FreeAllWindowBuffers':0x08003e99}
SOURCES=('scripts/pr16_ring_ui_owners.py','scripts/pr16_ring_resource_tail.py',
    'content/modernization/pr16_ring_resource_tail.json','scripts/pr16_ring_resource_frontier.py',
    'scripts/pr16_ring_remaining_frontier.py','scripts/pr16_ring_owner_frontier.py',
    'scripts/pr16_ring_effective_frontier.py','scripts/pr16_ring_branch_frontier.py',
    'scripts/pr16_ring_zero_bytes.py','scripts/pr16_ring_transitive_owner.py',
    'scripts/pr16_ring_flagset_continuation.py','.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT=('JP text/windowの7入口の有限採取は今回保存nodeを再利用。旧2970命令/1752resource契約/固定JPsource取得/BP/nativeは再実行しない。'
    '保存initializerの存在を通常入場・実allocation成功・callback実行と同一視しない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def plan(a):
    need(type(a)is dict and a.get('saved_node_count')==2970,'保存node数')
    rows=a.get('next_named_roots');need(type(rows)is list and len(rows)==len(ROOTS),'root集合')
    need(all(type(r)is dict and type(r.get('entry'))is int and r.get('already_saved')is False for r in rows),
         'root形式/既読root')
    need({r.get('symbol'):r['entry']for r in rows}==ROOTS,'JP root差分')
    for key in ('actual_callback_table_observed','all_live_slot_bounds_proven','ring_acquisition_accepted','release_ready'):
        need(a.get(key)is False,'scope差分 '+key)
    need(a.get('header_abi',{}).get('header_stride_matches_candidate')is False,'ヘッダstride境界')
    return sorted(ROOTS.values())


def validate_graph(nodes,cached,data_ranges):
    need(type(nodes)is list and 0<len(nodes)<=1800,'新規node予算')
    occupied=set()
    for n in cached:
        occupied.update(range(n['address'],n['address']+n['size']))
    forbidden=set()
    for start,length in data_ranges:
        need(type(start)is int and type(length)is int and 0<length<=65536
             and 0x08000000<=start<start+length<=0x0a000000,'data範囲')
        forbidden.update(range(start,start+length))
    fresh=set()
    for n in nodes:
        at,size=n['address'],n['size']
        need(type(at)is int and at%2==0 and type(size)is int and size in (2,4),'命令整列/幅')
        need(0x08000000<=at<at+size<=0x0a000000,'ROM範囲')
        need(len(bytes.fromhex(n['hex']))==size,'命令byte幅')
        points=set(range(at,at+size));need(not points&(occupied|forbidden|fresh),'既読/code/data重複')
        fresh|=points
    return len(fresh)


def saved_inputs():
    import pr16_ring_resource_tail as tail
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,_=tail.saved_inputs();r=s.load(tail.REPORT)
    saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows'])
    nodes=[*nodes,*r['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    need(len(nodes)==2970 and len({n['address']for n in nodes})==2970,'保存2970命令')
    return nodes,memory,copy.deepcopy(r['analysis']['tables'])


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    roots=plan(previous['analysis']);nodes,memory,tables=saved_inputs()
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)]
    forbidden={p for start,length in ranges for p in range(start,start+length)}
    need(not set(r&~1 for r in roots)&{n['address']for n in nodes},'root再採取')
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    (out/'preflight.json').write_bytes(s.stable({'roots':roots,'saved_nodes':len(nodes),
        'prior_run':previous['run_id'],'source_bindings':{p:identity((s.ROOT/p).read_bytes())for p in paths}}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
                             max_nodes=1800,max_bytes=8192)
    new=result['new_nodes'];points=result.pop('points');validate_graph(new,nodes,ranges)
    windows,reused=old.new_windows(raw,points,memory)
    need(identity(candidate.read_bytes())==identity(raw),'candidate変更')
    known={n['address']for n in nodes}
    result.update({'classification':'FINITE_JP_UI_INITIALIZER_AND_CALLBACK_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'named_roots':dict(ROOTS),'tables':tables,
        'new_windows':windows,'saved_bytes_reused':reused,'new_node_count':len(new),
        'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'cached_node_count':len(nodes),'saved_node_count':len(nodes)+len(new),
        'literal_references':[n for n in new if 'literal_address'in n],
        'calls_into_saved_graph':[n for n in new if n['kind']=='call'and n['target']&~1 in known],
        'unbound_runtime_data':copy.deepcopy(previous['analysis']['unbound_runtime_data']),
        'header_abi':copy.deepcopy(previous['analysis']['header_abi']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'caller_pointer_size_limit_proven':False,'actual_callback_table_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'upstream_fetches_this_run':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    export=(SELF,TEST,'scripts/pr16_ring_resource_contracts.py','scripts/pr16_ring_dispatch_contracts.py',
        'scripts/pr16_ring_gate_contracts.py','scripts/pr16_ring_caller_contracts.py',
        'scripts/pr16_ring_string_machine.py','scripts/pr16_ring_contract_machine.py',
        'scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py',
        'scripts/pr16_ring_remaining_frontier.py','scripts/pr16_ring_owner_frontier.py',
        'scripts/pr16_ring_transitive_owner.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in export}))
    return result


def summaries(r):
    return (f'固定JPのtext/window7入口を有限結合。新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byte、'
        f'保存総数{r["saved_node_count"]}。旧2970命令再解読0、ROM変更/native0。',
        '次は今回の保存initializer/RunTextPrintersを32byte text pool・12byte window poolの'
        'ループ上限/allocator失敗/解放/間接callbackへ結合。未読callee/実gFonts tableはpendingを正とする。'
        '今回7入口採取・旧resource契約・BP/nativeを単独再実行しない。'
        'Ring正規取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
