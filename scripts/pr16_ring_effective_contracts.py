#!/usr/bin/env python3
"""新規calleeを保存済frame/validator/5要素分岐と結合。実機到達とは分ける。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import pr16_ring_saved_contracts as vm
import pr16_ring_effective_frontier as frontier

BASE='10090d4ffb5c50f0fb09014f65c263e9c8748d0a'
SLUG='pr16-ring-effective-contracts'
TASK='PR-P08-7-RING-EFFECTIVE-CONTRACTS'
TITLE='新規pop/mode/veneerとvalidatorエラー継続を保存証拠へ結合'
SELF='scripts/pr16_ring_effective_contracts.py'
TEST='tests/test_pr16_ring_effective_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-effective-contracts.yml'
PRIOR=frontier.REPORT
REPORT='content/modernization/pr16_ring_effective_contracts.json'
KEY='latest_ring_diagnostic'
SOURCES=(vm.SELF,vm.flow.SELF,frontier.SELF,frontier.OLD,frontier.CONTEXT,vm.PATCH,
         frontier.TRANSITIVE,vm.REPORT,'scripts/pr16_ring_flagset_continuation.py')
EXTRA_CODE=()
MIN_TESTS=32
NO_REPEAT=('保存pop+cursor復帰、mode全256値、中継先2件、validator version/size/hash/reservedの'
    '合成契約を再利用。10090d4以後の新規境界以外を採取せず、既読ABI/BPを単独再実行しない。'
    '低level成否とRing通常取得・装備実戦・保存の受入は別。')
need=vm.need
POP,RETURN_SCRIPT=0x0806916d,0x080691a9
MODE,CTX=0x081137f5,0x02001000
VENEERS=((0x092d12e1,0x093bd9a9),(0x092d2979,0x093bde81))


def joined_nodes(old,patch,new,extra=()):
    nodes=vm.saved_nodes(old,patch)
    return list(vm.flow.node_map([*nodes,*new['new_nodes'],*extra]).values())


def selector_results(new,old):
    """正確な既存prefix+新規表+caseの構造を結合し、全mode byteを網羅する。"""
    prefix=frontier.bind_table_prefix(old['new_nodes'])
    nodes=vm.flow.node_map([*old['new_nodes'],*new['new_nodes']])
    entries=new['table_entries']
    need(len(entries)==5 and [r['index'] for r in entries]==list(range(5)),'table順序')
    for i,row in enumerate(entries):
        need(row['address']==frontier.TABLE+4*i and row['thumb_entry']==row['raw_target']|1,'table結合')
    need(nodes[0x0811382e]['hex']=='02bc' and nodes[0x08113830]['hex']=='0847','保存LR復元差分')
    results=[]
    for mode in range(256):
        at=entries[mode]['raw_target'] if mode<=4 else prefix['out_of_range_target']&~1
        trace=[];returned=None
        while at!=0x0811382e:
            need(at in nodes and len(trace)<4 and at not in trace,'case境界/loop')
            n=nodes[at];need(n['size']==2,'case長');h=int.from_bytes(bytes.fromhex(n['hex']),'little');trace.append(at)
            if n['kind']=='ordinary' and h&0xff00==0x2000:
                returned=h&255;at+=2
            elif n['kind']=='jump' and h&0xf800==0xe000:
                d=h&0x7ff;d=d-0x800 if d&0x400 else d
                need(n['target']==at+4+2*d,'case branch差分');at=n['target']
            else:raise ValueError('mode caseの未対応効果')
        expected=1 if mode in (1,3) else 2 if mode in (2,4) else 0
        need(returned==expected,'mode戻り値差分')
        results.append({'mode':mode,'return_r0':returned,'case_trace':trace,
                        'nonstack_writes':0,'sp_and_r4_r11_restored_by_exact_prefix_suffix':True})
    return results


def veneer_links(nodes):
    by=vm.flow.node_map(nodes);rows=[]
    for entry,expected in VENEERS:
        lo=entry&~1;load,branch=by[lo],by[lo+2]
        need(load['hex']=='004b' and load['literal_address']==lo+4
             and branch['hex']=='1847' and branch['kind']=='indirect','veneer形式')
        target=load['literal_value'];need(target==expected and target&1,'veneer target差分')
        rows.append({'entry':entry,'target':target,'branch_register':3,
            'preserves_registers':['r0','r1','r2','r4-r11','SP','LR'],
            'preservation_scope':'TWO_INSTRUCTION_VENEER_ONLY_NOT_CALLEE',
            'callee_saved_nodes_present':target&~1 in by,
            'callee_return_proven':False,'native_reachability_proven':False})
    return rows


def pop_case(nodes,depth,composed=False):
    need(type(depth)is int and 0<=depth<=255,'stack depth byte')
    data=bytearray(12+4*max(depth,1));data[0]=depth
    for i in range(depth):data[12+4*i:16+4*i]=(0x08002001+4*i).to_bytes(4,'little')
    data[8:12]=(0x08000001).to_bytes(4,'little')
    machine=vm.Machine(nodes,[(CTX,bytes(data),True)],(CTX,)).run(RETURN_SCRIPT if composed else POP)
    expected=0 if depth==0 else 0x08002001+4*(depth-1)
    writes=[] if depth==0 else [(CTX,1,depth-1)]
    if composed:writes.append((CTX+8,4,expected))
    need(machine.nonstack_writes()==writes,'pop書込差分')
    need(machine.r[0]==(vm.RETURN if composed else expected),'pop帰還値差分')
    need(machine.data(CTX,1)==bytes([max(depth-1,0)]),'pop depth差分')
    return {'depth':depth,'composed_script_return':composed,'selected_script_pointer':expected,
        'writes':[list(w) for w in writes],'maximum_stack_bytes':vm.SP-machine.low_sp,
        'sp_and_r4_r11_restored':True,'caller_capacity_proven':False}


def validator_buffer(version=1,size=2048,*,good_hash=True,reserved_offset=None):
    need(type(version)is int and 0<=version<=65535 and type(size)is int and 0<=size<=65535,'header整数')
    data=bytearray(2048);data[:4]=(0x31534756).to_bytes(4,'little')
    data[4:6]=version.to_bytes(2,'little');data[6:8]=size.to_bytes(2,'little')
    if reserved_offset is not None:
        need(type(reserved_offset)is int and 0<=reserved_offset<2048,'reserved offset');data[reserved_offset]=1
    value=vm.checksum(bytes(data))
    data[8:12]=(value if good_hash else value^1).to_bytes(4,'little')
    return bytes(data)


def validator_case(nodes,data,expected):
    machine=vm.Machine(nodes,[(CTX,data,False)],(CTX,2048)).run(vm.VALIDATE)
    need(machine.r[0]==expected and not machine.nonstack_writes(),'validator error/readonly差分')
    return {'return_code':expected,'header_version':int.from_bytes(data[4:6],'little'),
        'declared_size':int.from_bytes(data[6:8],'little'),'nonstack_writes':0,
        'maximum_stack_bytes':vm.SP-machine.low_sp,'steps':machine.steps,'sp_and_r4_r11_restored':True}


def boundary_links(new,nodes,covered_indirect=None):
    known={n['address'] for n in nodes};resolved=[];pending=[];seen=set()
    covered_indirect=covered_indirect or {}
    for root in new['roots']:
        for b in root['boundaries']:
            target=b.get('target');key=(root['entry'],b['site'],b['kind'],target)
            if key in seen:continue
            seen.add(key)
            row=dict(root=root['entry'],**b)
            if b['kind']=='indirect_boundary' and b['site'] in covered_indirect:
                row['binding']=covered_indirect[b['site']];resolved.append(row)
            elif target is not None and target&~1 in known:
                row['binding']='SAVED_NODE_ONLY_NOT_CALLEE_OR_LIVE_FRAME_PROOF';resolved.append(row)
            elif b['kind'] not in ('revisited_node_boundary','saved_node_boundary'):
                pending.append(row)
    return {'saved_boundary_links':resolved,'pending_boundaries':pending,
            'pending_direct_callees':sorted({r['target'] for r in pending if r['kind']=='unread_call'}),
            'pending_continuations':sorted({r['target'] for r in pending
                if r['kind'] in ('window_boundary','outside_branch') and r.get('target') is not None})}


def analyze(prior,out):
    import pr16_ring_followup_v2 as support
    import pr16_ring_flagset_continuation as saved
    reports={p:support.load(p) for p in (frontier.OLD,vm.PATCH,frontier.TRANSITIVE,vm.REPORT)}
    for r in reports.values():saved.bindings_fresh(support.ROOT,r['source_bindings'])
    old=reports[frontier.OLD]['analysis'];patch=reports[vm.PATCH];new=prior['analysis']
    extra=[n for g in reports[frontier.TRANSITIVE]['native_owners'].values() for n in g['nodes']]
    nodes=joined_nodes(old,patch,new,extra)
    modes=selector_results(new,old)
    pops=[pop_case(nodes,depth,composed) for depth in range(256) for composed in (False,True)]
    validators=[]
    for version in (0,3,255,256,65535):validators.append(validator_case(nodes,validator_buffer(version),3))
    for size in (0,1,2047,2049,32768,65535):validators.append(validator_case(nodes,validator_buffer(size=size),4))
    for version in (1,2):
        validators.append(validator_case(nodes,validator_buffer(version,good_hash=False),5))
        for offset in (65,66,67):validators.append(validator_case(nodes,validator_buffer(version,reserved_offset=offset),15))
    limits=[]
    for version in (1,2):
        machine=vm.Machine(nodes,[(CTX,validator_buffer(version),False)],(CTX,2048))
        try:machine.run(vm.VALIDATE)
        except ValueError as error:
            need(str(error)=='保存node境界で停止' and machine.last_pc=={1:0x093bdaa8,2:0x093bdb3e}[version],'未読停止差分')
            limits.append({'version':version,'stopped_at':machine.last_pc,'accepted':False})
        else:raise ValueError('validator成功継続を未証明のまま受入')
    veneers=veneer_links(nodes)
    covered={0x0806918c:'SYNTHETIC_POP_RETURN_NOT_LIVE_FRAME',
             0x092d12e2:'RESOLVED_VENEER_ONLY_CALLEE_ABI_UNPROVEN',
             0x092d297a:'RESOLVED_VENEER_ONLY_CALLEE_ABI_UNPROVEN'}
    links=boundary_links(new,nodes,covered)
    result={'classification':'SAVED_EFFECTIVE_CALLEE_AND_BRANCH_CONTRACTS_NOT_RING_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(support.CANDIDATE),'veneer_links':veneers,
        'pending_effective_targets':[r['target'] for r in veneers if not r['callee_saved_nodes_present']],
        'mode_contract':{'input_byte_cases':256,'outputs':[r['return_r0'] for r in modes],
            'nonstack_writes':0,'frame_bytes':4,'sp_and_r4_r11_restored_by_exact_prefix_suffix':True},
        'pop_contract':{'synthetic_cases':len(pops),'depth_range':[0,255],
            'required_context_bytes':'12 + 4 * depth (empty case: at least 12 bytes)',
            'empty_returns_null':True,'nonempty_reads_last_pointer_and_decrements_depth':True,
            'composed_return_updates_context_cursor':True,'max_frame_bytes':max(r['maximum_stack_bytes'] for r in pops),
            'caller_capacity_proven':False},
        'validator_error_cases':validators,'validator_success_stops':limits,
        'development_findings':['version2はversion1と同じ境界ではなく0x093BDB3Eへ分岐する。初回の同一停止点仮定を棄却し、各versionの保存branchに一致する回帰へ修正。'],
        'synthetic_contract_cases':len(pops)+len(modes)+len(validators),
        'validator_success_continuation_proven':False,'all_live_frames_proven':False,
        **links,'all_callers_resolved':False,'caller_pointer_size_limit_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_byte_samples':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0}
    (out/'analysis.json').write_bytes(support.stable(result));return result


def summaries(result):
    return (f'新規calleeを結合し、mode全256値、pop/ScriptReturn512ケース、validatorエラー19ケースを検証。'
        '中継2件を既知validator/0x093BDE81へ接続。Ring受入・live全frameとは別。ROM/native再実行0。',
        '保存結合を再利用し、残るdirect callee '+','.join(f'0x{x:08X}' for x in result['pending_direct_callees'])+
        ' と未読中継先 '+','.join(f'0x{x:08X}' for x in result['pending_effective_targets'])+
        '・窓外継続のみを進める。正常header継続はversion1=0x093BDAA8、version2=0x093BDB3Eで停止する。'
        '新規7入口/表/既読契約/BPは単独再実行せず、Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
