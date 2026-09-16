#!/usr/bin/env python3
"""未読2入口と11文字列83byteの有限採取。既読命令とnativeは再実行しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='0ee0588da2832d627bfaf4e8876aa5aa275fafc2'
SLUG='pr16-ring-text-frontier'
TASK='PR-P08-7-RING-TEXT-FRONTIER'
TITLE='未読VarGet callee・非null継続と11文字列83byteを有限保存'
SELF='scripts/pr16_ring_text_frontier.py'
TEST='tests/test_pr16_ring_text_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-text-frontier.yml'
PRIOR='content/modernization/pr16_ring_reference_contracts.json'
REPORT='content/modernization/pr16_ring_text_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=()
ROM_BASE,ROM_END=0x08000000,0x0a000000
CALLEES=(0x0806dc49,)
EFFECTIVE=(0x08002d15,)
TEXT_POINTERS=(0x083dd1dd,0x083dd1e0,0x083dd1ea,0x083dd1ee,0x083dd1f2,
               0x083dd1f6,0x083dd1fb,0x083dd200,0x083dd206,0x083dd20c,0x083dd210)
NO_REPEAT=('未読2入口と11文字列83byteの有限採取は保存原本を再利用する。'
    '同じcandidate復元・既読命令再解読・旧795/716契約・BP/nativeを単独再実行しない。'
    '保存文字列終端とcallee候補を実callerのbuffer/task境界やRing正規取得へ昇格しない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(data):
    return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def text_plan():
    return [{'label':'placeholder_text_'+hex(p),'start':p,
        'length':min(32,TEXT_POINTERS[i+1]-p)if i+1<len(TEXT_POINTERS)else 32,
        'max_terminator_scan':32}for i,p in enumerate(TEXT_POINTERS)]


def data_plan(analysis):
    expected={'pending_direct_callees':list(CALLEES),'pending_effective_targets':list(EFFECTIVE),
        'pending_data_ranges':text_plan(),'pending_continuations':[],'saved_node_count':1859,
        'ring_acquisition_accepted':False,'release_ready':False}
    for k,v in expected.items():
        need(type(analysis.get(k))is type(v) and analysis[k]==v,'保存pending不一致: '+k)
    return copy.deepcopy(expected['pending_data_ranges'])


def validate_texts(rows,nodes,other_ranges=()):
    need(type(rows)is list and len(rows)==11,'文字列件数')
    occupied=set()
    for n in nodes:
        occupied.update(range(n['address'],n['address']+n['size']))
        if 'literal_address'in n:occupied.update(range(n['literal_address'],n['literal_address']+4))
    for start,length in other_ranges:
        need(type(start)is int and type(length)is int and length>0,'既存data範囲')
        occupied.update(range(start,start+length))
    points=set()
    for expected,row in zip(text_plan(),rows):
        need(type(row)is dict and all(type(row.get(k))is type(v) and row[k]==v for k,v in expected.items()),'文字列descriptor')
        need(type(row.get('hex'))is str,'文字列hex形式')
        raw=bytes.fromhex(row['hex'])
        need(len(raw)==row['length'] and row.get('identity')==identity(raw),'文字列identity')
        span=set(range(row['start'],row['start']+row['length']))
        need(not span&(points|occupied),'文字列/code/data重複');points.update(span)
    need(len(points)==83,'文字列83byte範囲')
    return points


def collect_texts(raw,nodes,other_ranges=()):
    need(type(raw)is bytes and 0<len(raw)<=ROM_END-ROM_BASE,'ROM入力')
    rows=[]
    for desc in text_plan():
        at=desc['start']-ROM_BASE
        need(0<=at<=at+desc['length']<=len(raw),'文字列ROM範囲')
        data=raw[at:at+desc['length']]
        rows.append(dict(desc,hex=data.hex(),identity=identity(data)))
    validate_texts(rows,nodes,other_ranges);return rows


def terminators(rows,nodes=(),other_ranges=()):
    validate_texts(rows,nodes,other_ranges)
    result=[]
    for row in rows:
        raw=bytes.fromhex(row['hex']);offset=raw.find(b'\xff')
        result.append({'start':row['start'],'window_bytes':len(raw),
            'first_ff_offset':offset if offset>=0 else None,
            'bounded_prefix_hex':raw[:offset+1].hex()if offset>=0 else None,
            'all_runtime_buffer_bounds_proven':False})
    return result


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_reference_frontier as previous
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
    data_plan(prior['analysis']);nodes,memory,tables=saved_inputs()
    need(len(nodes)==1859,'保存node差分')
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)]
    (out/'preflight.json').write_bytes(s.stable({'prior_run':prior['run_id'],'roots':[*CALLEES,*EFFECTIVE],
        'saved_nodes':len(nodes),'text_plan':text_plan(),'data_bytes':83}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    texts=collect_texts(raw,nodes,ranges);points=validate_texts(texts,nodes,ranges)
    forbidden=set(points)
    for start,length in ranges:forbidden.update(range(start,start+length))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    result=walk.bounded_walk(raw,sorted((*CALLEES,*EFFECTIVE)),old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier)
    new=result['new_nodes'];validate_texts(texts,[*nodes,*new],ranges)
    points.update(result.pop('points'));windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_TEXT_AND_VAR_GATE_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':[*tables,*texts],'text_windows':texts,
        'text_terminators':terminators(texts,[*nodes,*new],ranges),
        'new_windows':windows,'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'data_bytes_bound':83,
        'literal_references':[n for n in new if 'literal_address'in n],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,'scripts/pr16_ring_reference_contracts.py','scripts/pr16_ring_string_machine.py',
        'scripts/pr16_ring_contract_machine.py','scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py')
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'未読2入口と11文字列83byteを有限採取。新規{result["new_node_count"]}命令、'
        f'{sum(t["first_ff_offset"]is not None for t in result["text_terminators"])}文字列で窓内FFを保存。ROM変更/native0。',
        '保存したVarGet callee・非null継続と11文字列を実byteの合成契約へ結合する。'
        'task index<16/非循環列・文字列buffer境界は実caller証拠と分離し、未読callee/間接辺は保存pendingで絞る。'
        '同じ採取・旧795/716契約・FC/memset/BPを単独再実行しない。Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_reference_contracts as previous
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((previous.SELF,*previous.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
