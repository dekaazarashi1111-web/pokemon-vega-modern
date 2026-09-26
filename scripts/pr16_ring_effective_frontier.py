#!/usr/bin/env python3
"""実callsiteで絞った未読callee/継続/計算ジャンプ表だけを有限採取する。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='611b4efc114a0c8c9a5b886ae000ad9002e3a838'
SLUG='pr16-ring-effective-frontier'
TASK='PR-P08-7-RING-EFFECTIVE-FRONTIER'
TITLE='実callsiteの新規7入口と5要素jump表を保存境界へ接続'
SELF='scripts/pr16_ring_effective_frontier.py'
TEST='tests/test_pr16_ring_effective_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-effective-frontier.yml'
PRIOR='content/modernization/pr16_ring_saved_contracts.json'
REPORT='content/modernization/pr16_ring_effective_frontier.json'
OLD='content/modernization/pr16_ring_owner_frontier.json'
CONTEXT='content/modernization/pr16_ring_owner_context.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=28
EXTRA_CODE=()
OWNERS='content/modernization/pr16_ring_selector_owners.json'
CALLERS='content/modernization/pr16_ring_record_callers.json'
FRONTIER='content/modernization/pr16_ring_branch_frontier.json'
UNREAD='content/modernization/pr16_ring_unread_frontier.json'
PATCH='content/modernization/pr16_ring_patch_owner.json'
TRANSITIVE='content/modernization/pr16_ring_transitive_owner.json'
SAMPLES=tuple('content/modernization/pr16_ring_'+name+'.json' for name in
              ('flagset_continuation','callee_bytes','helper_bytes','nonzero_bytes','zero_bytes'))
REPORTS=(OWNERS,CALLERS,FRONTIER,UNREAD,PATCH,TRANSITIVE,*SAMPLES,OLD,CONTEXT)
SOURCES=(*REPORTS,'scripts/pr16_ring_owner_frontier.py','scripts/pr16_ring_transitive_owner.py',
    'scripts/pr16_ring_compiled_owner.py','scripts/pr16_ring_record_callers.py',
    'scripts/pr16_ring_branch_frontier.py','scripts/pr16_ring_selector_followup.py',
    'scripts/pr16_ring_zero_bytes.py','.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT=('実callsiteからの新規7入口・5要素jump表と合流先を再利用。今回保存したnodeを再採取/再解読しない。'
    '定数targetや分岐表をnative到達・全callee ABI・Ring受入に読み替えず、未知/窓外/共有境界を残す。')
ROM_BASE,ROM_END=0x08000000,0x0a000000
TABLE,TABLE_COUNT=0x08113810,5
FIXED=(0x08068d89,0x0806916d,0x081c2a55,0x092d12e1,0x092d28d9,0x092d2979,0x093bda29)
PREFIX=((0x081137f4,'00b5'),(0x081137f6,'0448'),(0x081137f8,'0078'),
        (0x081137fa,'0428'),(0x081137fc,'12d8'),(0x081137fe,'8000'),
        (0x08113800,'0249'),(0x08113802,'4018'),(0x08113804,'0068'),(0x08113806,'8746'))


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def put(memory,at,raw):
    need(type(at)is int and type(raw)is bytes and ROM_BASE<=at<=at+len(raw)<=ROM_END,'保存byte境界')
    for offset,value in enumerate(raw):
        pos=at+offset;need(pos not in memory or memory[pos]==value,'保存byte矛盾');memory[pos]=value


def bind_table_prefix(nodes):
    """既存decode済nodeと正確な5要素index制限を結合。codeを再decodeしない。"""
    by={n['address']:n for n in nodes}
    need(len(by)==len(nodes),'保存node重複')
    for at,hex_ in PREFIX:
        need(at in by and by[at]['size']==2 and by[at]['hex']==hex_,'jump prefix差分')
    need(by[0x081137f6].get('literal_address')==0x08113808
         and by[0x081137f6].get('literal_value')==0x03005ed8,'mode byte pointer差分')
    need(by[0x081137fc]['kind']=='conditional' and by[0x081137fc].get('target')==0x08113824,'上限branch差分')
    need(by[0x08113800].get('literal_address')==0x0811380c
         and by[0x08113800].get('literal_value')==TABLE,'table pointer差分')
    need(by[0x08113806]['kind']=='indirect' and by[0x08113806].get('register')==0,'MOV pc,r0差分')
    return {'entry':0x081137f5,'mode_byte_pointer':0x03005ed8,'mode_range':[0,4],
        'out_of_range_target':0x08113825,'table':TABLE,'table_count':TABLE_COUNT,
        'site':0x08113806,'saved_prefix_reused':True,'native_reachability_proven':False}


def table_entries(raw,occupied):
    need(type(raw)is bytes and len(raw)==TABLE_COUNT*4,'table長')
    need(type(occupied)is set,'命令占有集合')
    rows=[]
    for i in range(TABLE_COUNT):
        at=TABLE+i*4;value=int.from_bytes(raw[i*4:i*4+4],'little')
        need(not any(pos in occupied for pos in range(at,at+4)),'table/命令重複')
        need(ROM_BASE<=value<ROM_END and not value&1,'MOV-PC tableの偶数Thumb命令境界')
        need(not TABLE<=value<TABLE+TABLE_COUNT*4,'table自身へ分岐')
        rows.append({'index':i,'address':at,'raw_target':value,'thumb_entry':value|1})
    return rows


def requested_roots(prior,context,entries):
    remaining=prior['next_unread_boundaries']
    need(remaining['direct_callees']==[0x08068d89,0x0806916d]
         and remaining['computed_jump_site']==0x08113806
         and remaining['validator_window_end']==0x093bda28,'未読境界差分')
    linked=context['resolved_trampoline_targets']
    need(linked==[0x0806dec5,0x081c2a55,0x092d12e1,0x092d28d9,0x092d2979],'実callsite宛先差分')
    roots=set(remaining['direct_callees']+[remaining['validator_window_end']|1]+linked[1:])
    need(tuple(sorted(roots))==FIXED,'新規7入口差分')
    need(len(entries)==TABLE_COUNT and [r['index'] for r in entries]==list(range(TABLE_COUNT)),'jump要素欠落')
    roots.update(r['thumb_entry'] for r in entries)
    need(len(roots)<=len(FIXED)+TABLE_COUNT,'root予算')
    return sorted(roots)


def nodes_to_memory(memory,nodes):
    occupied=set()
    for n in nodes:
        at,size=n['address'],n['size'];raw=bytes.fromhex(n['hex'])
        need(type(at)is int and not at&1 and size in (2,4) and len(raw)==size,'node境界')
        need(not occupied.intersection(range(at,at+size)),'命令重複')
        occupied.update(range(at,at+size));put(memory,at,raw)
        if 'literal_address' in n:
            loc,value=n['literal_address'],n['literal_value']
            need(type(loc)is int and not loc&3 and type(value)is int and 0<=value<=0xffffffff,'literal境界')
            put(memory,loc,value.to_bytes(4,'little'))
    return occupied


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_owner_frontier as old
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    reports={p:s.load(p) for p in REPORTS}
    for value in reports.values():saved.bindings_fresh(s.ROOT,value['source_bindings'])
    memory=previous.saved_memory(reports[OWNERS])
    for path in (CALLERS,FRONTIER,UNREAD,OLD):frontier.add_windows(memory,reports[path]['analysis']['new_windows'])
    graphs=[*reports[PATCH]['frontier']['graphs'],*reports[TRANSITIVE]['native_owners'].values(),
        *(reports[p]['analysis']['graph'] for p in SAMPLES),{'nodes':reports[OLD]['analysis']['new_nodes']}]
    cached=old.cache_nodes(graphs)
    occupied=nodes_to_memory(memory,list(cached.values()))
    table=bind_table_prefix(reports[OLD]['analysis']['new_nodes'])
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes())
        for p in (SELF,PRIOR,*SOURCES)},'fixed_targets':list(FIXED),'table':table,
        'window':old.WINDOW,'node_limit_per_root':old.LIMIT,'max_sampled_bytes':old.MAX_BYTES}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    data=raw[TABLE-ROM_BASE:TABLE-ROM_BASE+TABLE_COUNT*4]
    entries=table_entries(data,occupied)
    table_new,table_reused=old.new_windows(raw,list(range(TABLE,TABLE+len(data))),memory)
    put(memory,TABLE,data)
    roots=requested_roots(prior['analysis'],reports[CONTEXT]['analysis'],entries)
    def decode(candidate_bytes,at):
        need(not TABLE<=at<TABLE+len(data),'declared jump-table data boundary')
        return decoder.thumb_instruction(candidate_bytes,at)
    result=old.inspect_frontier(raw,roots,cached,decode)
    windows,reused=old.new_windows(raw,result.pop('points'),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    counts={}
    for row in result['roots']:
        for edge in row['boundaries']:counts[edge['kind']]=counts.get(edge['kind'],0)+1
    result.update({'classification':'EFFECTIVE_CALLSITE_AND_BOUNDED_JUMP_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'fixed_targets':list(FIXED),'table_binding':table,
        'table_entries':entries,'table_identity':identity(data),'new_table_windows':table_new,
        'table_bytes_reused':table_reused,'new_windows':windows,
        'new_node_count':len(result['new_nodes']),'boundary_counts':counts,
        'new_window_bytes':sum(w['end']-w['start'] for w in windows+table_new),'saved_bytes_reused':reused,
        'cached_node_count':len(cached),'saved_root_reuse':[t for t in roots if t&~1 in cached],
        'memory_write_sites':[n['address'] for n in result['new_nodes'] if n['memory_write']],
        'all_callers_resolved':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0,'candidate_reconstructions':1,
        'full_rom_scans':0,'prior_graph_decoders_replayed':0})
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'実callsiteの新規7入口と保存済計算jumpの5要素表から、未読{result["new_node_count"]}命令/'
        f'{result["new_window_bytes"]}byteだけを保存。既存{result["cached_node_count"]}nodeへは再decodeせず停止。'
        '候補復元1、ROM変更/native再実行0。',
        '今回の保存callee・validator継続・jump各caseを実callsite/frame/書込へ結合し、'
        '残る未読辺だけを進める。7入口/5要素表や既読copy/checksum/BPを再採取・単独再実行しない。'
        '全caller/initializer LIMIT・Ring正規story取得/装備実戦/保存とpolicy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
