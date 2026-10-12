#!/usr/bin/env python3
"""3callee・非null中継先・placeholder/nibble/fallbackの133byteだけを保存する。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import pr16_ring_string_frontier as previous
import pr16_ring_string_contracts as contracts

BASE='fa2fdb4861142228bb2c1f49390c4e9b88b91fcd'
SLUG='pr16-ring-reference-frontier'
TASK='PR-P08-7-RING-REFERENCE-FRONTIER'
TITLE='残る3callee・非null中継先・placeholder等133byteを有限保存'
SELF='scripts/pr16_ring_reference_frontier.py'
TEST='tests/test_pr16_ring_reference_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-reference-frontier.yml'
PRIOR=contracts.REPORT
REPORT='content/modernization/pr16_ring_reference_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
CALLEES=(0x0806dd5d,0x08076d41,0x081c7ac9)
EFFECTIVE=(0x09378a31,)
TABLES=contracts.PENDING_DATA
SOURCES=(contracts.SELF,previous.SELF,previous.REPORT,*contracts.SOURCES)
NO_REPEAT=('3callee/非null中継先/placeholder等133byteと表候補先の有限採取は今回保存原本を再利用。'
    '同じ採取・旧716契約・FC/memset/BP/nativeを単独再実行しない。'
    '表word候補と保存命令の結合を実callbackの帰還/SPやRing正規取得の証明にしない。')
need=previous.need
identity=previous.identity


def data_plan(analysis):
    need(analysis.get('pending_direct_callees')==list(CALLEES),'3callee差分')
    need(analysis.get('pending_effective_targets')==list(EFFECTIVE),'実中継先差分')
    need(analysis.get('pending_data_ranges')==list(TABLES),'133byte範囲差分')
    need(analysis.get('pending_continuations')==[] and analysis.get('saved_node_count')==1752,'保存継続差分')
    need(analysis.get('ring_acquisition_accepted') is False and analysis.get('release_ready') is False,'受入差分')
    return copy.deepcopy(list(TABLES))


def validate_tables(tables,nodes,other_ranges=()):
    need(type(tables)is list and len(tables)==3,'table件数')
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    for start,length in other_ranges:
        need(type(start)is int and type(length)is int and length>0,'保存table範囲')
        occupied.update(range(start,start+length))
    points=set()
    for expected,row in zip(TABLES,tables):
        need(type(row)is dict and all(type(row.get(k))is type(v) and row[k]==v for k,v in expected.items()),'table descriptor')
        need(type(row.get('hex'))is str,'table hex形式')
        raw=bytes.fromhex(row['hex']);need(len(raw)==row['length'] and row.get('identity')==identity(raw),'table identity')
        span=set(range(row['start'],row['start']+row['length']))
        need(not span&(points|occupied),'code/data重複');points.update(span)
    return points


def callback_candidates(tables,nodes,other_ranges=()):
    forbidden=validate_tables(tables,nodes,other_ranges)
    for start,length in other_ranges:forbidden.update(range(start,start+length))
    known={n['address']for n in nodes}
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    literals={p for n in nodes if 'literal_address'in n for p in range(n['literal_address'],n['literal_address']+4)}
    raw=bytes.fromhex(tables[0]['hex']);rows=[]
    for index in range(14):
        word=int.from_bytes(raw[index*4:index*4+4],'little');at=word&~1
        eligible=bool(word&1) and previous.ROM_BASE<=at<previous.ROM_END
        if eligible:
            need(at not in forbidden and at+1 not in forbidden and at not in literals,'callback data境界')
            need(at not in occupied or at in known,'callback operand境界')
        rows.append({'index':index,'table_address':TABLES[0]['start']+index*4,'stored_word':word,
            'eligible_thumb_candidate':eligible,'effective_thumb_entry':word if eligible else None,
            'binding':'TABLE_WORD_CANDIDATE_NOT_CALLSITE_ABI_OR_NATIVE_REACHABILITY'})
    return rows


def collect_tables(raw,nodes,other_ranges=()):
    need(type(raw)is bytes and 0<len(raw)<=previous.ROM_END-previous.ROM_BASE,'ROM byte入力')
    tables=[]
    for desc in TABLES:
        at=desc['start']-previous.ROM_BASE;need(0<=at<=at+desc['length']<=len(raw),'table ROM範囲')
        data=raw[at:at+desc['length']];tables.append(dict(desc,hex=data.hex(),identity=identity(data)))
    validate_tables(tables,nodes,other_ranges);return tables


def saved_inputs():
    import pr16_ring_followup_v2 as s
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
    data_plan(prior['analysis']);nodes,memory,tables=saved_inputs();need(len(nodes)==1752,'保存node差分')
    ranges=[(t['start'],t['length'])for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)]
    bindings={p:s.identity((s.ROOT/p).read_bytes())for p in (SELF,TEST,WORKFLOW,PRIOR,*SOURCES)}
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':bindings,'callees':CALLEES,
        'effective_targets':EFFECTIVE,'data_ranges':TABLES,'prior_run':prior['run_id'],'saved_nodes':len(nodes)}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    fresh=collect_tables(raw,nodes,ranges);callbacks=callback_candidates(fresh,nodes,ranges)
    points=validate_tables(fresh,nodes,ranges);forbidden=set(points)
    for start,length in ranges:forbidden.update(range(start,start+length))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data decode禁止')
        return decoder.thumb_instruction(data,at)
    roots=sorted(set((*CALLEES,*EFFECTIVE,*(r['effective_thumb_entry']for r in callbacks if r['eligible_thumb_candidate']))))
    result=walk.bounded_walk(raw,roots,old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier)
    new=result['new_nodes'];validate_tables(fresh,[*nodes,*new],ranges)
    points.update(result.pop('points'));windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_PLACEHOLDER_REFERENCES_AND_CALLEES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':[*tables,*fresh],'callback_bindings':callbacks,
        'new_windows':windows,'new_node_count':len(new),'new_window_bytes':sum(w['end']-w['start']for w in windows),
        'saved_bytes_reused':reused,'cached_node_count':len(nodes),'data_bytes_bound':133,
        'literal_references':[n for n in new if 'literal_address'in n],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new],'analysis':result}))
    paths=(SELF,TEST,contracts.SELF,contracts.model.SELF,contracts.model.prior.SELF,contracts.vm.SELF,
        contracts.vm.flow.SELF,contracts.c.SELF)
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in paths}))
    return result


def summaries(result):
    return (f'残る3callee/非null中継先とplaceholder等133byteを{len(result["waves"])}waveで有限結合。'
        f'新規{result["new_node_count"]}命令/{result["new_window_bytes"]}byte。既読再解読・native0。',
        '保存したplaceholder table/getter・nibble実表・fallback先頭・非null中継先を有限合成契約として結合する。'
        '新たなcallee/実データ/間接辺とcaller frameは保存pendingで絞り、推測して通過しない。'
        '同じ採取/旧716契約/FC/memset/BPは単独再実行しない。Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((*SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
