#!/usr/bin/env python3
"""保存2457命令でVarGet selector1/2を縦結合。旧ABI単独・ROM/nativeは実行しない。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_dispatch_contracts as prior

BASE='f0539c0bfd3bf85b2a1b0aea1829aa39b108fa22'
SLUG='pr16-ring-varget-join'
TASK='PR-P08-7-RING-VARGET-JOIN'
TITLE='VarGet selector1/2の全通常256変数と条件付きrecord書込・帰還を結合'
SELF='scripts/pr16_ring_varget_join.py'
TEST='tests/test_pr16_ring_varget_join.py'
WORKFLOW='.github/workflows/pr16-ring-varget-join.yml'
PRIOR='content/modernization/pr16_ring_selector_reuse.json'
REPORT='content/modernization/pr16_ring_varget_join.json'
KEY='latest_ring_diagnostic'
SOURCES=()
EXTRA_CODE=()
MIN_TESTS=34
COUNT,LIMIT,COUNTER,CAPACITY,BASE_PTR,PENDING=0x0203af10,0x03005edc,0x0203af96,0x03002030,0x0300202c,0x030050bc
EXTERNAL=(0x0806dd1d,0x08113889,0x081138f9)
RESOURCE=(0x080011e5,0x08001299,0x080014f1,0x0800273d,0x080027ad,0x08002899,0x080028ed,0x08002901)
NO_REPEAT=('VarGet selector1/2の全通常256変数・record key/mode・count/limit/capacity境界と外側帰還の新規結合は保存結果を再利用する。'
    '旧external ABI/7graph・旧VarGet65536/1337・既読2457命令・81要素/265caller/11文字列・BP/nativeを単独再実行しない。'
    '明示合成allocationの帰還を実caller/Ring通常取得へ昇格しない。')
need=prior.need
vm=prior.vm
caller=prior.prior.caller
Machine=prior.Machine


def u16(value,label):
    need(type(value)is int and 0<=value<=65535,label+' u16');return value


def eligible(value):
    u16(value,'id');need(0x4000<=value<=0x40ff,'通常256変数')
    return 0x4030<=value<=0x404f or 0x40b4<=value<=0x40ff


def fixture(value,selector,*,count=1,limit=2,index=0,capacity=1,record_key=None,record_mode=0,
            record_value=0x4321,save_value=0x1234):
    need(type(value)is int and 0<=value<=0xffffffff,'caller u32');v=value&65535
    need(0x4000<=v<=0x40ff and type(selector)is int and selector in (1,2),'selector/通常変数')
    for label,x in (('count',count),('limit',limit),('index',index),('capacity',capacity),('record_value',record_value),('save_value',save_value)):u16(x,label)
    key=v if record_key is None else u16(record_key,'key')
    need(key<=0x7fff and type(record_mode)is int and record_mode in (0,1),'record key/mode')
    base=0x02010000 if index<16384 else 0x02000000;record=base+4*index
    need(0x02000000<=record<=0x0203fffc,'record EWRAM条件')
    save=caller.SB1+prior.route(v)['offset'];word=(record_value<<16)|(record_mode<<15)|key
    regions=[(prior.SELECTOR,1),(caller.GLOBAL1,4),(save,2),(COUNT,2),(LIMIT,2),(COUNTER,2),
        (CAPACITY,2),(BASE_PTR,4),(PENDING,2),(record,4)]
    need(all(a+n<=b or b+m<=a for i,(a,n)in enumerate(regions)for b,m in regions[i+1:]),'合成object alias')
    segs=[(prior.SELECTOR,bytes([selector]),False),(caller.GLOBAL1,caller.SB1.to_bytes(4,'little'),False),
        (save,save_value.to_bytes(2,'little'),True),(COUNT,count.to_bytes(2,'little'),False),
        (LIMIT,limit.to_bytes(2,'little'),False),(COUNTER,index.to_bytes(2,'little'),True),
        (CAPACITY,capacity.to_bytes(2,'little'),False),(BASE_PTR,base.to_bytes(4,'little'),False),
        (PENDING,b'\xaa\xaa',True),(record,word.to_bytes(4,'little'),True)]
    gate=count>0 and count<limit and index<capacity
    writes=[];expected_save=save_value;expected_record=word;expected_index=index;pending=0xaaaa
    if selector==1:
        take=gate and key==v and record_mode==0
        if take:
            expected_save=record_value;expected_index=index+1;writes=[(COUNTER,2,expected_index),(save,2,expected_save)]
        calls=[(0x08113889,[0,v])];peak=40
    else:
        take=eligible(v);calls=[(0x0806dd1d,[v-0x4000,1])];peak=28
        if take:
            pending=v-0x4000;writes=[(PENDING,2,pending)];calls.append((0x081138f9,[0,v,save_value]));peak=44
            if gate:
                expected_index=index+1;expected_record=v|(save_value<<16)
                writes.extend(((record,2,(word&0x8000)|v),(record+1,1,v>>8),(record+2,2,save_value),(COUNTER,2,expected_index)))
    return {'value':value,'v':v,'selector':selector,'segments':segs,'record':record,'save':save,'gate':gate,
        'record_initial':word,'save_initial':save_value,'index_initial':index,'expected_save':expected_save,
        'expected_record':expected_record,'expected_index':expected_index,'expected_pending':pending,
        'writes':writes,'calls':calls,'peak':peak,'objects':[(COUNTER,2),(PENDING,2),(record,4),(save,2)]}


def execute(nodes,case,label):
    m=Machine(nodes,case['segments'],(case['value'],)).run(caller.VARGET)
    need(m.r[0]==case['expected_save'] and m.read(case['save'],2)==case['expected_save'],'保存caller戻値 '+label)
    need(m.read(case['record'],4)==case['expected_record'] and m.read(COUNTER,2)==case['expected_index']
        and m.read(PENDING,2)==case['expected_pending'],'record/counter/pending結果 '+label)
    need(m.nonstack_writes()==case['writes'] and not caller.outside_writes(m,case['objects']),'順序付き正確書込 '+label)
    calls=[(r['target'],r['args'][:2 if r['target']!=0x081138f9 else 3])for r in m.call_arguments if r['target']in EXTERNAL]
    need(calls==case['calls'] and vm.SP-m.low_sp==case['peak'],'実call引数/frame結合 '+label)
    return {'case':label,'steps':m.steps,'return_r0':m.r[0],'maximum_stack_bytes':case['peak'],
        'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,'return_sp_callee_saved_proven':True,
        'allocation_proof_scope':'EXPLICIT_SYNTHETIC_DISJOINT_OBJECTS_ONLY'}


def damaged(case,address,kind):
    value=copy.deepcopy(case);found=False;segs=[]
    need(kind in ('missing','short','readonly'),'損傷mode')
    for at,data,writable in value['segments']:
        if at==address:
            found=True
            if kind=='missing':continue
            if kind=='short':data=data[:-1]
            if kind=='readonly':writable=False
        segs.append((at,data,writable))
    need(found,'損傷objectなし');value['segments']=segs;return value


def verify(nodes,analysis):
    need(len(nodes)==analysis['saved_node_count']==2457 and analysis['reused_external_node_count']==127,'保存2457命令差分')
    need(analysis['known_callees_awaiting_caller_contracts']==list(EXTERNAL)
        and analysis['pending_direct_callees']==list(RESOURCE),'保存callee境界差分')
    rows=[];stops=[]
    for selector in (1,2):
        for v in range(0x4000,0x4100):rows.append(execute(nodes,fixture(v,selector),f'all-{selector}-{v:04x}'))
    boundaries=(0x4000,0x402f,0x4030,0x404f,0x4050,0x40b3,0x40b4,0x40ff)
    gates=({'count':0},{'count':2},{'count':65535,'limit':65535},{'capacity':0},
        {'index':1,'capacity':1},{'index':65535,'capacity':65535})
    for selector in (1,2):
        for v in boundaries:
            for i,gate in enumerate(gates):rows.append(execute(nodes,fixture(v,selector,**gate),f'gate-{selector}-{v:04x}-{i}'))
            for index in (1,255,65534):
                for mode in (0,1):
                    rows.append(execute(nodes,fixture(v,selector,index=index,capacity=index+1,record_mode=mode,
                        record_value=0xffff,save_value=0),f'slot-{selector}-{v:04x}-{index}-{mode}'))
            for high in (0x10000,0xffff0000):
                rows.append(execute(nodes,fixture(high|v,selector),f'high-{selector}-{high|v:08x}'))
    for v in boundaries:
        rows.append(execute(nodes,fixture(v,1,record_key=v^1),f'key-miss-{v:04x}'))
        rows.append(execute(nodes,fixture(v,1,record_mode=1),f'mode-miss-{v:04x}'))
    for selector in (1,2):
        v=0x4030;case=fixture(v,selector)
        for address in (COUNT,LIMIT,COUNTER,CAPACITY,BASE_PTR,case['record'],case['save']):
            for kind in ('missing','short'):
                c=damaged(case,address,kind);m=Machine(nodes,c['segments'],(v,))
                try:m.run(caller.VARGET)
                except ValueError as exc:need(str(exc)in ('未map read','未許可 write'),'不足停止種別')
                else:raise ValueError('不足objectを成功に昇格')
                need(m.nonstack_writes()==case['writes'][:len(m.nonstack_writes())],'不足前部分書込の順序')
                stops.append({'case':f'bound-{selector}-{address:08x}-{kind}','site':m.last_pc,
                    'read_fault':m.read_fault,'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,
                    'return_proven':False,'rollback_claimed':False})
        for address in (COUNTER,case['save']) if selector==1 else (PENDING,case['record'],COUNTER):
            c=damaged(case,address,'readonly');m=Machine(nodes,c['segments'],(v,))
            try:m.run(caller.VARGET)
            except ValueError as exc:need(str(exc)=='未許可 write','非許可書込停止種別')
            else:raise ValueError('readonly書込を成功に昇格')
            need(m.nonstack_writes()==case['writes'][:len(m.nonstack_writes())],'拒否前部分書込の順序')
            stops.append({'case':f'readonly-{selector}-{address:08x}','site':m.last_pc,'read_fault':m.read_fault,
                'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,'return_proven':False,'rollback_claimed':False})
    return {'classification':'SAVED_VARGET_SELECTOR_CALLER_RETURNS_AND_ORDERED_EFFECTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':len(rows),'contracts':rows,'limited_stops':stops,
        'ordinary_variable_count':256,'selector2_external3_id_ranges':[[0x4030,0x404f],[0x40b4,0x40ff]],
        'selector2_external3_id_count':108,'maximum_conditional_frame_bytes':44,
        'selector_callee_arguments_bound':True,'synthetic_selector_returns_proven':True,
        'known_callees_awaiting_caller_contracts':[],'pending_direct_callees':list(RESOURCE),
        'pending_effective_targets':[],'pending_continuations':[],'pending_data_ranges':[],
        'unbound_runtime_data':copy.deepcopy(analysis['unbound_runtime_data']),
        'session_stages_verified_without_replay':copy.deepcopy(analysis['session_stages_verified_without_replay']),
        'historical_failed_attempt':copy.deepcopy(analysis['historical_failed_attempt']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['合成通常RAM・明示非alias・整列済みobject・同期実行での保存命令による帰還。実allocation/割込み状態の証明ではない。',
            'selector1はrecord key/mode一致時にcounter更新後save値を書込。selector2は108変数でpendingを書き、条件成立時にrecord/counterを更新。',
            '不足/readonly診断は失敗前の部分書込も保存する。巻戻し/原子性を主張しない。',
            '既存helper全u16やselector0/3/255の1337帰還、外部ABI単独の分類は再実行しない。']}


def analyze(prior_report,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_dispatch_frontier as frontier
    nodes,_,_=frontier.saved_inputs();r=s.load(frontier.REPORT)
    nodes=[*nodes,*r['analysis']['new_nodes'],*prior_report['analysis']['reused_external_nodes']]
    result=verify(nodes,prior_report['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    result,raw=prior.prior.archive_effects(result);(out/'raw-effects.json').write_bytes(raw)
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'保存2457命令でVarGet selector1/2の通常256変数を含む{result["synthetic_contract_cases"]}帰還、'
        f'{len(result["limited_stops"])}不足/readonly停止を結合。selector2の108変数・最大44byte frame・順序付き部分書込を固定。',
        '次はresource未読8callee 0x080011E5/0x08001299/0x080014F1/0x0800273D/0x080027AD/0x08002899/0x080028ED/0x08002901だけを有限採取し、'
        '実callback table/12byte resource/32byte出力slotと通常・拡張変数領域のallocation条件を結合する。'
        '保存2457命令・VarGet全u16/1337帰還・selector1/2縦結合・旧external ABI/7graph・BP/nativeを単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_selector_reuse as reused
    import pr16_ring_dispatch_frontier as frontier
    SOURCES=tuple(dict.fromkeys((prior.SELF,reused.SELF,frontier.SELF,frontier.REPORT,
        *support.load(reused.REPORT)['source_bindings'])))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
