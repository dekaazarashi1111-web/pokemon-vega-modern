#!/usr/bin/env python3
"""残る6callee/3data表だけを有限採取。旧445命令/280契約/nativeは再実行しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import pr16_ring_remaining_contracts as contracts
import pr16_ring_remaining_frontier as frontier
import pr16_ring_owner_frontier as old

BASE='5261da3e622b0d0297d0cdcad3bceef81b000fea'
SLUG='pr16-ring-dependency-frontier'
TASK='PR-P08-7-RING-DEPENDENCY-FRONTIER'
TITLE='残る6calleeとstring/v2有限data表を保存結合'
SELF='scripts/pr16_ring_dependency_frontier.py'
TEST='tests/test_pr16_ring_dependency_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-dependency-frontier.yml'
PRIOR=contracts.REPORT
REPORT='content/modernization/pr16_ring_dependency_frontier.json'
KEY='latest_ring_diagnostic'
EXTRA_CODE=()
MIN_TESTS=22
SOURCES=tuple(dict.fromkeys((contracts.SELF,frontier.SELF,frontier.REPORT,*contracts.SOURCES)))
CALLEES=(0x08076bb5,0x080ccf91,0x080f7d29,0x080f8909,0x081c7ad5,0x093bee0b)
TABLES=contracts.TABLES
ROM_BASE,ROM_END=frontier.ROM_BASE,frontier.ROM_END
NO_REPEAT=('残る6callee/3data表とtable先の有限採取は今回保存原本を再利用。'
    '次はv2正常/実buffer copy/string分岐を合成契約として結合。'
    '旧445命令・280単独契約・BP/nativeは再実行しない。')
need=frontier.need


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def data_plan(prior):
    need(prior['pending_direct_callees']==list(CALLEES),'6callee差分')
    need(prior['pending_data_ranges']==list(TABLES),'3data範囲差分')
    need(prior['pending_continuations']==[],'前工程継続差分')
    need(prior['ring_acquisition_accepted'] is False and prior['release_ready'] is False,'受入差分')
    return copy.deepcopy(TABLES)


def validate_tables(tables,nodes):
    need(type(tables)is list and len(tables)==3,'表件数')
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    seen=set()
    for expected,row in zip(TABLES,tables):
        need(all(row.get(k)==v for k,v in expected.items()),'表descriptor差分')
        raw=bytes.fromhex(row['hex']);need(len(raw)==row['length'],'表長')
        need(row['identity']==identity(raw),'表identity差分')
        points=set(range(row['start'],row['start']+row['length']))
        need(not points&occupied,'data表と保存命令重複')
        need(not points&seen,'data表重複');seen.update(points)
    return seen


def dispatch_targets(tables,nodes):
    forbidden=validate_tables(tables,nodes)
    raw=bytes.fromhex(tables[0]['hex']);known={n['address'] for n in nodes}
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    literals={p for n in nodes if 'literal_address' in n for p in range(n['literal_address'],n['literal_address']+4)}
    rows=[]
    for i in range(6):
        word=int.from_bytes(raw[i*4:i*4+4],'little');target=word&~1
        need(ROM_BASE<=target<ROM_END,'dispatch ROM範囲')
        need(target not in forbidden and target not in literals,'dispatch data境界')
        need(target not in occupied or target in known,'dispatch operand境界')
        rows.append({'control_byte':250+i,'table_address':TABLES[0]['start']+i*4,
            'stored_word':word,'effective_thumb_entry':target|1,
            'binding':'MOV_PC_IN_THUMB_STATE_NOT_NATIVE_REACHABILITY'})
    return rows


def collect_tables(raw,nodes):
    need(type(raw)is bytes and 0<len(raw)<=ROM_END-ROM_BASE,'ROM入力')
    tables=[]
    for desc in TABLES:
        at=desc['start']-ROM_BASE;length=desc['length']
        need(0<=at<=at+length<=len(raw),'table ROM範囲')
        payload=raw[at:at+length]
        tables.append(dict(desc,hex=payload.hex(),identity=identity(payload)))
    validate_tables(tables,nodes);return tables


def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_effective_frontier as f
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as windows
    import pr16_ring_flagset_continuation as saved
    reports={p:s.load(p) for p in (*f.REPORTS,f.REPORT,frontier.REPORT)}
    for report in reports.values():saved.bindings_fresh(s.ROOT,report['source_bindings'])
    memory=previous.saved_memory(reports[f.OWNERS])
    for p in (f.CALLERS,f.FRONTIER,f.UNREAD,f.OLD,f.REPORT,frontier.REPORT):
        windows.add_windows(memory,reports[p]['analysis']['new_windows'])
    windows.add_windows(memory,reports[f.REPORT]['analysis']['new_table_windows'])
    nodes=contracts.saved_nodes(reports[frontier.REPORT]);f.nodes_to_memory(memory,nodes)
    return nodes,memory


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    data_plan(prior['analysis']);nodes,memory=saved_inputs();cached=old.cache_nodes([{'nodes':nodes}])
    bindings={p:s.identity((s.ROOT/p).read_bytes()) for p in (SELF,TEST,WORKFLOW,PRIOR,*SOURCES)}
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':bindings,'callees':CALLEES,
        'data_ranges':TABLES,'previous_contract_run':prior['run_id'],'saved_nodes':len(nodes)}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    tables=collect_tables(raw,nodes);dispatch=dispatch_targets(tables,nodes)
    points=validate_tables(tables,nodes)
    forbidden=points|set(range(f.TABLE,f.TABLE+f.TABLE_COUNT*4))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data表decode禁止')
        return decoder.thumb_instruction(data,at)
    roots=sorted(set((*CALLEES,*(r['effective_thumb_entry'] for r in dispatch))))
    result=frontier.bounded_walk(raw,roots,cached,decode,old.inspect_frontier)
    new_nodes=result['new_nodes'];validate_tables(tables,[*nodes,*new_nodes])
    points.update(result.pop('points'))
    windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_DEPENDENCIES_AND_TABLES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':tables,'dispatch_table_bindings':dispatch,
        'new_windows':windows,'saved_bytes_reused':reused,'new_node_count':len(new_nodes),
        'new_window_bytes':sum(w['end']-w['start'] for w in windows),'data_bytes_bound':len(validate_tables(tables,nodes)),
        'cached_node_count':len(nodes),'all_callers_resolved':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':1,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new_nodes],'analysis':result}))
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')
        for p in (SELF,TEST,contracts.SELF,contracts.model.SELF)}))
    return result


def summaries(result):
    return (f'残る6calleeと3表440byteを有限結合。{len(result["waves"])}waveで'
        f'新規{result["new_node_count"]}命令/{result["new_window_bytes"]}byte。旧命令再解読・native0。',
        '今回保存したcopy/string分岐とv2表を使い、v2正常return・実buffer形のcopy・文字列分岐を合成検証する。'
        '未読callee/間接辺を推測せず保存pendingを次の境界とする。'
        '同じ採取/旧280契約/BPは再実行しない。Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
