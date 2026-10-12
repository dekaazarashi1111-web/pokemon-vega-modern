#!/usr/bin/env python3
"""未読6calleeとstring252の84byte表だけを採取し、保存命令へ結合する。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE='53c04c70d2ac8959bc00100e77b7f16046d9ce4a'
SLUG='pr16-ring-string-frontier'
TASK='PR-P08-7-RING-STRING-FRONTIER'
TITLE='未読6calleeとstring252の21要素表を有限採取・保存結合'
SELF='scripts/pr16_ring_string_frontier.py'
TEST='tests/test_pr16_ring_string_frontier.py'
WORKFLOW='.github/workflows/pr16-ring-string-frontier.yml'
PRIOR='content/modernization/pr16_ring_dependency_contracts.json'
DEPENDENCY='content/modernization/pr16_ring_dependency_frontier.json'
REPORT='content/modernization/pr16_ring_string_frontier.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
SOURCES=('scripts/pr16_ring_dependency_contracts.py','scripts/pr16_ring_dependency_frontier.py',DEPENDENCY)
CALLEES=(0x08002cf1,0x08008d5d,0x0806dd99,0x08076c09,0x0813d469,0x081c9df9)
TABLE={'label':'string_extended_subtypes','start':0x08008bb4,'length':84,
       'count':21,'stride':4,'site':0x08008bac,'index':'subtype - 4; unsigned 0..20'}
ROM_BASE,ROM_END=0x08000000,0x0a000000
NO_REPEAT=('未読6callee/string252の21要素84byte表とその有限継続は今回保存原本を再利用。'
    '同一採取・既存94契約・BP/nativeを再実行せず、保存nodeでstring253/252とcallee境界を結合する。'
    '表の分岐先同定は帰還/SP/実callerやRing正規取得の証明ではない。')


def need(ok,text):
    if not ok:raise ValueError(text)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def data_plan(prior):
    need(prior.get('pending_direct_callees')==list(CALLEES),'未読6callee差分')
    need(prior.get('pending_data_ranges')==[TABLE],'未読84byte表差分')
    need(prior.get('pending_continuations')==[],'継続差分')
    need(prior.get('saved_node_count')==1576,'保存node件数差分')
    need(prior.get('ring_acquisition_accepted') is False and prior.get('release_ready') is False,'受入差分')
    return copy.deepcopy(TABLE)


def validate_table(row,nodes,other_ranges=()):
    need(type(row)is dict and all(type(row.get(k))is type(v) and row[k]==v for k,v in TABLE.items()),'表descriptor差分')
    need(type(row.get('hex'))is str,'表hex形式')
    raw=bytes.fromhex(row['hex']);need(len(raw)==84,'表長')
    need(row.get('identity')==identity(raw),'表identity差分')
    points=set(range(TABLE['start'],TABLE['start']+84))
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    need(not points&occupied,'表と命令重複')
    for start,length in other_ranges:
        need(type(start)is int and type(length)is int and length>0,'他data範囲')
        need(not points&set(range(start,start+length)),'表と他data重複')
    return points


def dispatch_targets(row,nodes,other_ranges=()):
    forbidden=validate_table(row,nodes,other_ranges)
    for start,length in other_ranges:forbidden.update(range(start,start+length))
    known={n['address'] for n in nodes}
    occupied={p for n in nodes for p in range(n['address'],n['address']+n['size'])}
    literals={p for n in nodes if 'literal_address' in n for p in range(n['literal_address'],n['literal_address']+4)}
    raw=bytes.fromhex(row['hex']);rows=[]
    for i in range(21):
        word=int.from_bytes(raw[i*4:i*4+4],'little');target=word&~1
        need(ROM_BASE<=target<ROM_END,'dispatch ROM範囲')
        need(target not in forbidden and target+1 not in forbidden and target not in literals,'dispatch data境界')
        need(target not in occupied or target in known,'dispatch operand境界')
        rows.append({'subtype':i+4,'table_address':TABLE['start']+i*4,'stored_word':word,
            'effective_thumb_entry':target|1,'binding':'MOV_PC_IN_THUMB_STATE_NOT_NATIVE_REACHABILITY'})
    return rows


def collect_table(raw,nodes,other_ranges=()):
    need(type(raw)is bytes and 0<len(raw)<=ROM_END-ROM_BASE,'ROM byte入力')
    at=TABLE['start']-ROM_BASE;need(at+84<=len(raw),'table ROM範囲')
    data=raw[at:at+84];row=dict(TABLE,hex=data.hex(),identity=identity(data))
    validate_table(row,nodes,other_ranges);return row


def saved_inputs():
    import pr16_ring_dependency_frontier as dependency
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory=dependency.saved_inputs();report=s.load(DEPENDENCY)
    saved.bindings_fresh(s.ROOT,report['source_bindings'])
    windows.add_windows(memory,report['analysis']['new_windows'])
    nodes=[*nodes,*report['analysis']['new_nodes']];f.nodes_to_memory(memory,nodes)
    return nodes,memory,copy.deepcopy(report['analysis']['tables'])


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_dependency_frontier as dependency
    import pr16_ring_remaining_frontier as frontier
    import pr16_ring_owner_frontier as old
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_effective_frontier as f
    import pr16_ring_contract_machine as model
    data_plan(prior['analysis']);nodes,memory,tables=saved_inputs()
    need(len(nodes)==prior['analysis']['saved_node_count'],'保存node不一致')
    ranges=[(t['start'],t['length']) for t in tables]+[(f.TABLE,f.TABLE_COUNT*4)]
    cached=old.cache_nodes([{'nodes':nodes}])
    bindings={p:s.identity((s.ROOT/p).read_bytes()) for p in (SELF,TEST,WORKFLOW,PRIOR,*SOURCES)}
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':bindings,'callees':CALLEES,
        'data_ranges':[TABLE],'previous_contract_run':prior['run_id'],'saved_nodes':len(nodes)}))
    restore.OUT=out;restore.restore()
    candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw=candidate.read_bytes();saved.candidate_identity(raw)
    table=collect_table(raw,nodes,ranges);dispatch=dispatch_targets(table,nodes,ranges)
    points=validate_table(table,nodes,ranges);forbidden=set(points)
    for start,length in ranges:forbidden.update(range(start,start+length))
    def decode(data,at):
        need(at not in forbidden and at+1 not in forbidden,'data表decode禁止')
        return decoder.thumb_instruction(data,at)
    roots=sorted(set((*CALLEES,*(r['effective_thumb_entry'] for r in dispatch))))
    result=frontier.bounded_walk(raw,roots,cached,decode,old.inspect_frontier)
    new_nodes=result['new_nodes'];validate_table(table,[*nodes,*new_nodes],ranges)
    points.update(result.pop('points'));windows,reused=old.new_windows(raw,sorted(points),memory)
    need(identity(candidate.read_bytes())==identity(raw),'候補変更')
    result.update({'classification':'FINITE_STRING_SUBTYPES_AND_CALLEES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'tables':[*tables,table],'dispatch_table_bindings':dispatch,
        'new_windows':windows,'saved_bytes_reused':reused,'new_node_count':len(new_nodes),
        'new_window_bytes':sum(w['end']-w['start'] for w in windows),'data_bytes_bound':84,
        'cached_node_count':len(nodes),'literal_references':[n for n in new_nodes if 'literal_address' in n],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':[*nodes,*new_nodes],'analysis':result}))
    paths=(SELF,TEST,model.SELF,model.base.SELF,model.base.flow.SELF,
        'scripts/pr16_ring_remaining_contracts.py',frontier.SELF,old.SELF)
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8') for p in paths}))
    return result


def summaries(result):
    return (f'未読6calleeとstring252の21要素84byte表を{len(result["waves"])}waveで保存結合。'
        f'新規{result["new_node_count"]}命令/{result["new_window_bytes"]}byte。既読再解読・native0。',
        '今回保存したstring252全subtype分岐とstring253参照選択、scheduler/callback/wait等を有限合成契約で結合する。'
        '未読callee/実data/ライブcaller frameは保存pendingから次へ絞る。'
        '同じ採取/旧94契約/BPを単独再実行しない。Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    import pr16_ring_dependency_contracts as contracts
    SOURCES=tuple(dict.fromkeys((*SOURCES,*contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
