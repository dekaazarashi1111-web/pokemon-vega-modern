#!/usr/bin/env python3
"""保存2330命令のVarGet全u16分類・帰還とcallback/resource停止境界。nativeなし。"""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import pr16_ring_gate_contracts as prior

BASE='ed8d6e9e8a0284a747d1d6769185d230e0d10222'
SLUG='pr16-ring-dispatch-contracts'
TASK='PR-P08-7-RING-DISPATCH-CONTRACTS'
TITLE='VarGet全65536値と実継続・callback/resource境界の保存契約を検証'
SELF='scripts/pr16_ring_dispatch_contracts.py'
TEST='tests/test_pr16_ring_dispatch_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-dispatch-contracts.yml'
PRIOR='content/modernization/pr16_ring_dispatch_frontier.json'
REPORT='content/modernization/pr16_ring_dispatch_contracts.json'
KEY='latest_ring_diagnostic'
SOURCES=()
EXTRA_CODE=()
MIN_TESTS=38
HELPER,POP_SITE=0x09128221,0x090970f6
SELECTOR,VAR_BASE,SPECIAL=0x03005ed8,0x020312e8,0x08163014
PENDING=(0x080011e5,0x08001299,0x080014f1,0x0800273d,0x080027ad,0x08002899,
    0x080028ed,0x08002901,0x0806dd1d,0x08113889,0x081138f9)
NO_REPEAT=('VarGet helper全65536値・保存caller帰還・明示slot不足拒否・callback/resource停止契約を再利用。'
    '同じ候補復元/採取/既読2330命令/81要素/非null帰還/265caller/11文字列/BP/nativeを単独再実行しない。'
    'special pointer表と拡張/通常変数領域の合成allocationを実callerの有効範囲やRing取得へ昇格しない。')
need=prior.need
vm=prior.vm


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


class Machine(prior.Machine):
    def pop_return(self,pc,error):
        n=self.nodes[pc]
        need(pc==POP_SITE and n['hex']=='70bd' and n['size']==2 and n['kind']=='return','POP継続allowlist差分')
        need(error=='未対応間接命令','POP継続例外境界')
        at=self.r[13];need(vm.STACK_LO<=at<=vm.STACK_HI-16,'POP継続stack範囲')
        values=[self.read(at+i*4,4)for i in range(4)]
        self.r[4:7]=values[:3];self.r[15]=values[3];self.r[13]+=16
        # Thumb POP PCはbit0を無視。BXのARM/Thumb切替と混同しない。
        return values[3]&~1

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None)
                if pc!=POP_SITE or str(exc)!='未対応間接命令':raise
                entry=self.pop_return(pc,str(exc))|1


def helper_result(value):
    need(type(value)is int and 0<=value<=65535,'helper u16引数')
    if 0x5000<=value<=0x51ff:return VAR_BASE+2*value
    return int(0x4100<=value<=0x7fff)


def route(value):
    need(type(value)is int and 0<=value<=0xffffffff,'VarGet u32引数')
    v=value&65535
    if 0x5000<=v<=0x51ff:return {'kind':'extended','address':VAR_BASE+2*v,'value':v}
    if 0x4000<=v<=0x40ff:return {'kind':'saveblock','offset':2*v-0x7000,'value':v}
    if v>=0x8000:return {'kind':'special','table_slot':SPECIAL+4*(v-0x8000),'value':v}
    return {'kind':'immediate','value':v}


def check_input(nodes,analysis):
    need(type(nodes)is list and len(nodes)==2330,'保存node数')
    need(analysis['cached_node_count']==2107 and analysis['new_node_count']==223,'保存wave差分')
    need(analysis['pending_direct_callees']==list(PENDING) and analysis['pending_continuations']==[],'未読境界差分')
    for k in ('ring_acquisition_accepted','release_ready','all_dispatch_returns_proven','all_live_slot_bounds_proven'):
        need(analysis[k]is False,'未受入境界 '+k)


def helper_exhaustive(nodes):
    """無書込leafのmemoryを再利用。register/flags/traceは各vectorで初期化する。"""
    m=Machine(nodes,[]);digest=hashlib.sha256();counts={'zero':0,'one':0,'pointer':0};sites=set()
    for value in range(65536):
        m.r=list(m.original);m.r[0]=value;m.flags=tuple(bool(value&(1<<i))for i in range(4))
        m.steps=0;m.low_sp=vm.SP;m.calls.clear();m.call_arguments.clear();m.executed_sites.clear()
        m.run(HELPER);expected=helper_result(value)
        need(m.r[0]==expected and not m.writes and not m.calls and m.low_sp==vm.SP,'helper全u16契約')
        digest.update(value.to_bytes(2,'little')+expected.to_bytes(4,'little'))
        counts['pointer'if expected>1 else 'one'if expected else 'zero']+=1;sites.update(m.executed_sites)
    return {'cases':65536,'result_sha256':digest.hexdigest(),'counts':counts,'executed_sites':sorted(sites),
        'memory_writes':0,'stack_bytes':0,'return_sp_callee_saved_proven':True,
        'input_domain':'u16 supplied by saved VarGet caller; high-bit direct helper arguments not claimed'}


def var_segments(value,selector=0,*,present=True,pointer=None,short=False):
    r=route(value);v=r['value'];payload=((v*73)^0xa55a)&65535;segments=[]
    if r['kind']=='immediate':return segments,v,None
    if r['kind']=='extended':target=r['address']
    elif r['kind']=='saveblock':
        target=prior.caller.SB1+r['offset']
        segments=[(SELECTOR,bytes([selector]),False),(prior.caller.GLOBAL1,prior.caller.SB1.to_bytes(4,'little'),False)]
    else:
        target=prior.caller.CTX if pointer is None else pointer
        segments=[(r['table_slot'],target.to_bytes(4,'little'),False)]
        if target==0:return segments,v,None
    if present:segments.append((target,payload.to_bytes(2,'little')[:1 if short else 2],False))
    return segments,payload,target


def verify(nodes,analysis,*,exhaustive=True):
    check_input(nodes,analysis);rows=[];stops=[]
    helper=helper_exhaustive(nodes)if exhaustive else None
    def returned(m,label,expected):
        need(m.r[0]==expected and not m.nonstack_writes(),'VarGet戻値/無書込 '+label)
        rows.append({'case':label,'steps':m.steps,'return_r0':m.r[0],'maximum_stack_bytes':vm.SP-m.low_sp,
            'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,'return_sp_callee_saved_proven':True})
    def stopped(m,entry,label,error,site,objects=()):
        try:m.run(entry)
        except ValueError as exc:need(str(exc)==error and m.last_pc==site,'停止境界 '+label)
        else:raise ValueError('未証明境界を通過 '+label)
        need(not prior.caller.outside_writes(m,objects),'停止前object外write '+label)
        stops.append({'case':label,'site':site,'error':error,'read_fault':m.read_fault,'return_proven':False,
            'maximum_stack_bytes':vm.SP-m.low_sp,'writes':m.nonstack_writes(),'call_arguments':m.call_arguments})
    values=sorted(set(range(0x4000,0x4100))|set(range(0x5000,0x5200))|
        {0,1,0x3ffe,0x3fff,0x4100,0x4101,0x4ffe,0x4fff,0x5200,0x5201,0x7ffe,0x7fff,
         0x8000,0x8001,0x801f,0x80ff,0xfffe,0xffff})
    for v in values:
        selectors=(0,3,255)if route(v)['kind']=='saveblock'else(0,)
        for selector in selectors:
            segments,expected,_=var_segments(v,selector)
            m=Machine(nodes,segments,(v,)).run(prior.caller.VARGET)
            returned(m,f'var-{v:04x}-selector-{selector}',expected)
    for v in (0,0x3fff,0x4000,0x40ff,0x4100,0x4fff,0x5000,0x51ff,0x5200,0x7fff,0x8000,0xffff):
        for high in (0x10000,0x12340000,0xffff0000):
            value=high|v;segments,expected,_=var_segments(value)
            returned(Machine(nodes,segments,(value,)).run(prior.caller.VARGET),f'var-high-{value:08x}',expected)
    for v in (0x8000,0x8001,0xffff):
        segments,expected,_=var_segments(v,pointer=0)
        returned(Machine(nodes,segments,(v,)).run(prior.caller.VARGET),f'null-special-{v:04x}',expected)
    for v in (0x4000,0x40ff,0x5000,0x51ff,0x8000,0xffff):
        for short in (False,True):
            segments,_,target=var_segments(v,present=short,short=short)
            m=Machine(nodes,segments,(v,))
            stopped(m,prior.caller.VARGET,f'unmapped-halfword-{v:04x}-{short}','未map read',0x0806dd6c)
            need(m.read_fault=={'address':target,'size':2,'site':0x0806dd6c},'halfword幅停止')
    for v in (0x8000,0x8001,0xffff):
        m=Machine(nodes,[],(v,));stopped(m,prior.caller.VARGET,f'unmapped-special-{v:04x}','未map read',0x0806dd0a)
        need(m.read_fault['address']==route(v)['table_slot'] and m.read_fault['size']==4,'special表幅')
    for selector in (1,2):
        for v in (0x4000,0x4001,0x40ff):
            segments,_,_=var_segments(v,selector);m=Machine(nodes,segments,(v,))
            endpoint=0x08113888 if selector==1 else 0x0806dd1c
            stopped(m,prior.caller.VARGET,f'var-selector-{selector}-{v:04x}','保存node境界で停止',endpoint)
            need(m.call_arguments[-1]['args'][:2]==([0,v]if selector==1 else[v-0x4000,1]),'selector callee引数')
    for mode in (0,255):
        for index in (0,1,254,255):
            for callback in (0x08012345,0x08012344,0):
                src=bytearray(range(16));src[5]=index;target=prior.TABLE+index*12
                segments=[(prior.caller.GATE_WORD,prior.TABLE.to_bytes(4,'little'),False),(target,callback.to_bytes(4,'little'),False),
                    (prior.caller.GATE_CONTEXT,b'\xcc'*32,True),(prior.caller.SRC,bytes(src),False),
                    (prior.COMBINATIONS,b'\xcc'*168,True)]
                m=Machine(nodes,segments,(prior.caller.SRC,mode,0x08012345))
                error,site=('保存node境界で停止',callback&~1)if callback&1 else('ARM state未対応',0x081c7acc)
                stopped(m,prior.caller.GATE,f'callback-{mode}-{index}-{callback:08x}',error,site,
                    [(prior.caller.GATE_CONTEXT,32),(prior.COMBINATIONS,168)])
                need(m.r[:2]==[prior.caller.GATE_CONTEXT,callback],'BX r1引数結合')
    for slot in (0,1,31,255):
        for dims in ((0,0),(1,1),(7,9),(255,255)):
            raw=bytes([5,0,0,*dims,0,0x34,0x12,0,0x70,0,2]);at=prior.RECORDS+slot*12
            for mode in (1,2,3):
                m=Machine(nodes,[(at,raw,False)],(slot,mode));endpoint=0x080028ec if mode==1 else 0x080011e4
                stopped(m,prior.RESOURCE,f'resource-{slot}-{dims}-{mode}','保存node境界で停止',endpoint)
                need(m.call_arguments[-1]['args'][:(1 if mode==1 else 2)]==([5]if mode==1 else[5,5]),'resource次callee引数')
    return {'classification':'SAVED_VARGET_U16_RETURN_AND_DISPATCH_RESOURCE_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'helper_exhaustive':helper,'synthetic_contract_cases':len(rows),
        'contracts':rows,'limited_stops':stops,'specific_varget_returns_proven':True,
        'varget_u16_classes':{'immediate':'0..3FFF,4100..4FFF,5200..7FFF','saveblock':'4000..40FF',
            'extended':'5000..51FF -> 020312E8 + 2*var','special':'8000..FFFF -> [08163014 + 4*(var-8000)]'},
        'unbound_runtime_data':copy.deepcopy(analysis['unbound_runtime_data'])+
            [{'kind':'special pointer table','base':SPECIAL,'read_bytes':4,'actual_entry_count_proven':False},
             {'kind':'extended variable storage','base':0x0203b2e8,'size':1024,'actual_allocation_proven':False},
             {'kind':'saveblock1 ordinary variables','offset':0x1000,'size':512,'actual_allocation_proven':False}],
        'pending_direct_callees':list(PENDING),'pending_effective_targets':[],'pending_data_ranges':[],
        'pending_continuations':[],'all_callers_resolved':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['全65536値は保存helperのu16入力。callerが上位16bitを切り捨てることも別の帰還契約で検証。',
            '通常/拡張変数halfwordとspecial表1wordは明示合成map。実allocation・表の実entry数は未証明。',
            'selector1/2の未結合calleeを成功stubで補わない。既存external1/2/3原本の再利用を次に照合する。',
            'callbackのodd未map/even/nullは停止診断。実callback選択・帰還やRing story取得とは別。']}


def analyze(prior_report,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_dispatch_frontier as frontier
    import io,unittest
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*prior_report['analysis']['new_nodes']]
    result=verify(nodes,prior_report['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    stream=io.StringIO();suite=unittest.TestLoader().discover(str(s.ROOT/'tests'),pattern='test_pr16_resume.py')
    tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    need(tested.wasSuccessful()and not tested.skipped and tested.testsRun>0,'再開MD/JSON回帰')
    raw=stream.getvalue().encode();(out/'resume-tests.txt').write_bytes(raw)
    result['resume_generator_regression']={'tests_run':tested.testsRun,'successful':True,'log_identity':identity(raw)}
    result,raw=prior.archive_effects(result);(out/'raw-effects.json').write_bytes(raw)
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'保存2330命令でVarGet helper全65536値とcaller帰還{result["synthetic_contract_cases"]}件、'
        f'未map/selector/callback/resource停止{len(result["limited_stops"])}件を検証。通常256変数・拡張512変数・special表参照の区分を結合。',
        '次はselector1/2の0x08113889/0x0806DD1D/0x081138F9を既存external1/2/3保存原本から再利用結合し、'
        '残るresource8calleeと実callback table/変数領域のallocationを有限検証する。'
        '採取済み2330命令・VarGet全u16/帰還・81要素/非null帰還・265caller・11文字列・BP/nativeを単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_dispatch_frontier as frontier
    import pr16_ring_reference_contracts as older
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((frontier.SELF,prior.SELF,prior.caller.SELF,prior.caller.prior.SELF,
        prior.caller.prior.prior.SELF,vm.SELF,vm.flow.SELF,'tests/test_pr16_resume.py',
        frontier.PRIOR,'content/modernization/pr16_ring_gate_frontier.json',*older.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
