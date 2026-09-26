#!/usr/bin/env python3
"""旧18targetの未読命令だけを有限採取。到達・ABI・副作用不存在は証明しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='67958790201608adc840959b146c9bc9cafc7597'
SLUG='pr16-ring-owner-frontier'
TASK='PR-P08-7-RING-OWNER-FRONTIER'
TITLE='旧18targetの未読命令と保存済み境界を重複なしで固定'
SELF='scripts/pr16_ring_owner_frontier.py'
TEST='tests/test_pr16_ring_owner_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-owner-frontier.yml'
PRIOR='content/modernization/pr16_ring_leap_contracts.json'
REPORT='content/modernization/pr16_ring_owner_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
OWNERS='content/modernization/pr16_ring_selector_owners.json'
CALLERS='content/modernization/pr16_ring_record_callers.json'
FRONTIER='content/modernization/pr16_ring_branch_frontier.json'
UNREAD='content/modernization/pr16_ring_unread_frontier.json'
PATCH='content/modernization/pr16_ring_patch_owner.json'
TRANSITIVE='content/modernization/pr16_ring_transitive_owner.json'
SAMPLES=tuple('content/modernization/pr16_ring_'+name+'.json' for name in
    ('flagset_continuation','callee_bytes','helper_bytes','nonzero_bytes','zero_bytes'))
SOURCES=(OWNERS,CALLERS,FRONTIER,UNREAD,PATCH,TRANSITIVE,*SAMPLES,
    'scripts/pr16_ring_transitive_owner.py','scripts/pr16_ring_compiled_owner.py',
    'scripts/pr16_ring_record_callers.py','scripts/pr16_ring_branch_frontier.py',
    'scripts/pr16_ring_selector_followup.py','scripts/pr16_ring_zero_bytes.py',
    '.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT=('旧18targetの今回保存命令/境界を再利用。保存nodeへ合流した先や未読calleeを再帰探索しない。'
    'cohort内共有node・operand/literal/未知命令/資源上限は受入に昇格しない。BP/GPIO/閏年/候補の同一採取は再実行しない。')
ROM_BASE,ROM_SIZE=0x08000000,0x02000000
WINDOW,LIMIT,MAX_BYTES=128,64,16384
TARGETS=(0x08068CFD,0x080690B5,0x080691A9,0x080691D1,0x081137F5,0x09097105,
    0x09302F0D,0x09303859,0x09378B95,0x09378E2D,0x09378E2F,0x09378E31,
    0x09379B89,0x09379B8B,0x093BD971,0x093BD9A9,0x093BEDE1,0x093BEE4D)
KINDS={'ordinary','call','jump','conditional','indirect','return'}


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):
    return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def cache_nodes(graphs):
    """既存nodeのbyte境界だけ再利用。旧graphを走査/再解読しない。"""
    found={}
    for graph in graphs:
        for node in graph['nodes']:
            at,size=node['address'],node['size']
            need(type(at)is int and not at&1 and size in (2,4) and node['kind'] in KINDS,'保存node境界')
            need(len(bytes.fromhex(node['hex']))==size,'保存node byte長')
            if at in found:need(found[at]['hex']==node['hex'] and found[at]['size']==size,'保存node矛盾')
            found[at]=node
    occupied={}
    for at,node in found.items():
        for pos in range(at,at+node['size']):
            need(pos not in occupied or occupied[pos]==at,'保存命令重複')
            occupied[pos]=at
    return found


def inspect_frontier(raw,roots,cached,decode,window=WINDOW,limit=LIMIT):
    """callは再帰せず、既知nodeと当工程共有nodeを境界として停止。"""
    need(type(raw)is bytes and 0<len(raw)<=ROM_SIZE,'ROM byte入力')
    need(type(window)is int and 2<=window<=WINDOW and not window&1,'窓上限')
    need(type(limit)is int and 1<=limit<=LIMIT,'node上限')
    need(type(roots)in (tuple,list) and roots and len(roots)==len(set(roots)),'target空/重複')
    need(all(type(t)is int and t&1 and ROM_BASE<=t&~1<ROM_BASE+len(raw) for t in roots),'target範囲')
    known=cache_nodes([{'nodes':list(cached.values())}])
    nodes={};occupied={};literals=set();points=set();rows=[]
    def verify_span(at,data):
        need(ROM_BASE<=at<=at+len(data)<=ROM_BASE+len(raw),'保存byte範囲')
        need(raw[at-ROM_BASE:at-ROM_BASE+len(data)]==data,'候補と保存byte差分')
    for at,node in known.items():
        verify_span(at,bytes.fromhex(node['hex']))
        for pos in range(at,at+node['size']):occupied[pos]=at
        if 'literal_address' in node:
            at=node['literal_address'];value=node['literal_value']
            verify_span(at,value.to_bytes(4,'little'));literals.update(range(at,at+4))
    for pointer in sorted(roots):
        root=pointer&~1;end=min(root+window,ROM_BASE+len(raw))
        pending=[root];seen=set();local=[];edges=[]
        def edge(at,kind,**more):edges.append({'site':at,'kind':kind,**more})
        while pending:
            at=pending.pop()
            if at in seen:
                edge(at,'revisited_node_boundary',target=at|1);continue
            seen.add(at)
            if not root<=at<end:
                edge(at,'window_boundary',target=at|1);continue
            if at in known:
                edge(at,'saved_node_boundary',target=at|1);continue
            if at in nodes:
                edge(at,'cohort_node_boundary',target=at|1);continue
            if at in occupied:
                edge(at,'instruction_operand_boundary',instruction_start=occupied[at]);continue
            if at in literals:
                edge(at,'literal_data_boundary');continue
            if len(local)>=limit:
                edge(at,'node_limit_boundary');continue
            if at+2>end:
                edge(at,'truncated_instruction_boundary');continue
            half=int.from_bytes(raw[at-ROM_BASE:at-ROM_BASE+2],'little')
            size=4 if half&0xF800==0xF000 else 2
            if at+size>end:
                edge(at,'truncated_instruction_boundary');continue
            points.update(range(at,at+size))
            if any(pos in occupied or pos in literals for pos in range(at,at+size)):
                edge(at,'overlapping_instruction_boundary');continue
            try:node=decode(raw,at)
            except ValueError as error:
                edge(at,'decoder_rejection',encoded=raw[at-ROM_BASE:at-ROM_BASE+size].hex(),reason=str(error)[:240]);continue
            need(node['address']==at and node['size']==size and node['kind'] in KINDS,'decoder node境界差分')
            verify_span(at,bytes.fromhex(node['hex']))
            need(len(bytes.fromhex(node['hex']))==size,'decoder byte長差分')
            if 'literal_address' in node:
                pool=node['literal_address']
                need(type(pool)is int and not pool&3,'literal整列')
                verify_span(pool,node['literal_value'].to_bytes(4,'little'))
                need(not any(pos in occupied for pos in range(pool,pool+4)),'literalと命令重複')
                literals.update(range(pool,pool+4));points.update(range(pool,pool+4))
            nodes[at]=copy.deepcopy(node);local.append(at)
            for pos in range(at,at+size):occupied[pos]=at
            kind=node['kind']
            if kind in ('call','jump','conditional'):
                target=node['target'];need(type(target)is int and not target&1,'分岐target整列')
                if kind=='call':edge(at,'unread_call',target=target|1)
                elif root<=target<end:pending.append(target)
                else:edge(at,'outside_branch',target=target|1)
            if kind=='indirect':edge(at,'indirect_boundary',register=node['register'])
            if kind=='return':edge(at,'return_opcode_not_abi_proof')
            if kind not in ('return','indirect','jump'):pending.append(at+size)
        rows.append({'entry':pointer,'window':[root,end],'new_node_addresses':sorted(local),
            'boundaries':sorted(edges,key=lambda r:(r['site'],r['kind'])),
            'candidate_control_flow_only':True,'runtime_reachable':False,'side_effects_excluded':False})
    need(len(points)<=MAX_BYTES,'採取byte総上限')
    return {'roots':rows,'new_nodes':[nodes[k] for k in sorted(nodes)],'points':sorted(points)}


def new_windows(raw,points,memory):
    """保存済byteは一致確認だけ。不足byteのみ連続窓へまとめる。"""
    need(type(raw)is bytes and type(memory)is dict,'byte/memory型')
    need(len(points)<=MAX_BYTES and len(points)==len(set(points)),'point上限/重複')
    windows=[];reused=0
    for at in sorted(points):
        need(type(at)is int and ROM_BASE<=at<ROM_BASE+len(raw),'point範囲')
        value=raw[at-ROM_BASE]
        if at in memory:
            need(type(memory[at])is int and memory[at]==value,'保存byte矛盾');reused+=1;continue
        if windows and windows[-1][1]==at:windows[-1][1]+=1
        else:windows.append([at,at+1])
    return ([{'start':lo,'end':hi,'hex':raw[lo-ROM_BASE:hi-ROM_BASE].hex(),
              'identity':identity(raw[lo-ROM_BASE:hi-ROM_BASE])} for lo,hi in windows],reused)


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    need(prior['analysis']['old_unread_targets']==list(TARGETS),'旧18target差分')
    reports={p:s.load(p) for p in (OWNERS,CALLERS,FRONTIER,UNREAD,PATCH,TRANSITIVE,*SAMPLES)}
    for report in reports.values():saved.bindings_fresh(s.ROOT,report['source_bindings'])
    memory=previous.saved_memory(reports[OWNERS])
    for path in (CALLERS,FRONTIER,UNREAD):frontier.add_windows(memory,reports[path]['analysis']['new_windows'])
    graphs=[*reports[PATCH]['frontier']['graphs'],*reports[TRANSITIVE]['native_owners'].values(),
            *(reports[p]['analysis']['graph'] for p in SAMPLES)]
    cached=cache_nodes(graphs)
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':{p:s.identity((s.ROOT/p).read_bytes()) for p in (SELF,PRIOR,*SOURCES)},
        'only_targets':list(TARGETS),'window':WINDOW,'node_limit_per_root':LIMIT,'max_sampled_bytes':MAX_BYTES}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    result=inspect_frontier(raw,TARGETS,cached,decoder.thumb_instruction)
    windows,reused=new_windows(raw,result.pop('points'),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    origins={str(t):[{'owner':g['entry'],**e} for g in graphs for e in g['external_edges'] if e.get('target')==t] for t in TARGETS}
    counts={}
    for row in result['roots']:
        for edge in row['boundaries']:counts[edge['kind']]=counts.get(edge['kind'],0)+1
    result.update({'classification':'OLD_OWNER_FRONTIER_UNREAD_NODES_NOT_ABI_OR_ACQUISITION_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'old_unread_targets':list(TARGETS),'saved_origins':origins,
        'origin_missing_targets':[t for t in TARGETS if not origins[str(t)]],
        'cached_node_count':len(cached),'new_node_count':len(result['new_nodes']),'boundary_counts':counts,
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start'] for w in windows),'saved_bytes_reused':reused,
        'memory_write_sites':[n['address'] for n in result['new_nodes'] if n['memory_write']],
        'old_frontier_removed':False,'all_callers_resolved':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'candidate_reconstructions':1,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'旧18targetを有限追跡し、新規{result["new_node_count"]}命令/{result["new_window_bytes"]}byteと保存済み合流境界を記録。'
        f'保存{result["saved_bytes_reused"]}byteを再利用。未知/operand/literal/資源上限は停止。候補復元1、ROM変更/native再実行0。',
        '保存した旧18targetのcall/return・書込・共有nodeを実callsiteの引数/保存frameと結合してownerを絞る。'
        '今回nodeの再採取/再解読と既読GPIO/剰余/閏年/BPの単独再実行は不要。'
        'initializerの実caller/pointer/size/LIMIT、Ring正規取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
