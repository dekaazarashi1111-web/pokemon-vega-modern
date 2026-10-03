#!/usr/bin/env python3
"""保存caller合成: CreateTaskのindex域・実文字列容量・非null prefixを限定検証。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import pr16_ring_string_machine as prior
import pr16_ring_saved_contracts as vm

BASE='ec9f3611fe1de52f39b801159f673adc51e78400'
SLUG='pr16-ring-caller-contracts'
TASK='PR-P08-7-RING-CALLER-CONTRACTS'
TITLE='CreateTask実caller・11実文字列容量・非null転送prefixの保存契約を結合'
SELF='scripts/pr16_ring_caller_contracts.py'
TEST='tests/test_pr16_ring_caller_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-caller-contracts.yml'
PRIOR='content/modernization/pr16_ring_text_frontier.json'
REPORT='content/modernization/pr16_ring_caller_contracts.json'
KEY='latest_ring_diagnostic'
EXTRA_CODE=()
SOURCES=()
MIN_TESTS=44
CREATE,INSERT,STRING,GATE,VARGET=0x08076bb5,0x08076c09,0x08008b49,0x08002cf1,0x0806dd5d
TASKS,COUNT,STRIDE=0x030050d0,16,40
CTX,SRC,GATE_CONTEXT=0x02001000,0x02001800,0x02020010
SB1,SB2,GLOBAL1,GLOBAL2,GATE_WORD=0x02004000,0x02003000,0x03005048,0x0300504c,0x03003dd0
TRANSFERS={0x08002d30:'8cc8',0x08002d32:'8cc1',0x08002d64:'1cc8',0x08002d66:'1cc1',
    0x08002d68:'8cc8',0x08002d6a:'8cc1',0x08002d6c:'90c8',0x08002d6e:'90c1'}
NO_REPEAT=('CreateTask保存callerの0..15探索・正常task列/満杯と11実文字列の容量境界・非nullコピーprefixを再利用。'
    '特定callerの範囲証明を全live caller/割込み状態やRing正規取得へ昇格しない。'
    '同じ採取・旧795/716・task挿入/memset/BP/native単独試験を再実行しない。')
need=vm.need


def identity(data):return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


class CallNodes(dict):
    """既存step解釈を変えず、保存call命令の直前引数だけを観測する。"""
    def __init__(self,values,owner):super().__init__(values);self.owner=owner
    def __getitem__(self,key):
        n=super().__getitem__(key)
        if n['kind']=='call':
            self.owner.call_arguments.append({'site':key,'target':n['target']|1,
                'args':self.owner.r[:4].copy(),'sp':self.owner.r[13]})
        return n


class Machine(prior.Machine):
    def __init__(self,nodes,segments,args=()):
        super().__init__(nodes,segments,args);self.call_arguments=[]
        self.nodes=CallNodes(self.nodes,self)

    def transfer(self,pc,error):
        n=self.nodes[pc]
        need(pc in TRANSFERS and n['hex']==TRANSFERS[pc] and n['size']==2 and n['kind']=='ordinary',
             '転送allowlist差分')
        need(error==f'未対応保存命令 {pc:08X}','転送例外境界')
        h=int.from_bytes(bytes.fromhex(n['hex']),'little');base=(h>>8)&7
        regs=[r for r in range(8)if h&(1<<r)]
        need(regs and base not in regs,'転送base/writeback未対応')
        address=self.r[base];need(address%4==0 and address+4*len(regs)<=0x100000000,'転送範囲')
        if h&0x0800:
            for i,r in enumerate(regs):self.r[r]=self.read(address+4*i,4)
        else:
            for i,r in enumerate(regs):self.write(address+4*i,4,self.r[r])
        self.r[base]=address+4*len(regs)
        return pc+2

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None)
                if pc not in TRANSFERS or str(exc)!=f'未対応保存命令 {pc:08X}':raise
                entry=self.transfer(pc,str(exc))|1


def task_chain(data):
    """640byte snapshotの整合性前提を検査。未観測live状態を補完しない。"""
    need(type(data)is bytes and len(data)==COUNT*STRIDE,'task領域長')
    active=[i for i in range(COUNT)if data[i*STRIDE+4]==1]
    need(all(data[i*STRIDE+4]in (0,1)for i in range(COUNT)),'active値')
    if not active:return []
    heads=[i for i in active if data[i*STRIDE+5]==254]
    need(len(heads)==1,'head数')
    chain=[];prev=254;at=heads[0];last_priority=-1
    while at!=255:
        need(0<=at<COUNT and at in active and at not in chain,'task境界/循環')
        base=at*STRIDE;priority=data[base+7]
        need(data[base+5]==prev and priority>=last_priority,'逆link/priority')
        chain.append(at);prev=at;at=data[base+6];last_priority=priority
    need(set(chain)==set(active),'到達不能active')
    return chain


def task_fixture(chain,priorities):
    need(len(chain)==len(priorities) and len(set(chain))==len(chain)
        and all(type(i)is int and 0<=i<COUNT for i in chain),'fixture列')
    need(all(type(p)is int and 0<=p<256 for p in priorities)and list(priorities)==sorted(priorities),'fixture priority')
    data=bytearray(b'\xcc'*(COUNT*STRIDE))
    for i in range(COUNT):data[i*STRIDE+4:i*STRIDE+8]=bytes([0,255,255,0])
    for k,i in enumerate(chain):
        data[i*STRIDE+4:i*STRIDE+8]=bytes([1,chain[k-1]if k else 254,chain[k+1]if k+1<len(chain)else 255,priorities[k]])
    task_chain(bytes(data));return bytes(data)


def created(data,callback,priority):
    chain=task_chain(data)
    need(type(callback)is int and 0<=callback<0x100000000 and type(priority)is int and 0<=priority<0x100000000,'CreateTask引数')
    target=next((i for i in range(COUNT)if data[i*STRIDE+4]==0),None)
    if target is None:return data,0,[],chain
    p=priority&255;at=next((k for k,i in enumerate(chain)if p<data[i*STRIDE+7]),len(chain))
    left=chain[at-1]if at else 254;right=chain[at]if at<len(chain)else 255
    base=TASKS+target*STRIDE
    writes=[(base,4,callback),(base+7,1,p),(base+5,1,left),(base+6,1,right)]
    if left!=254:writes.append((TASKS+left*STRIDE+6,1,target))
    if right!=255:writes.append((TASKS+right*STRIDE+5,1,target))
    writes.extend((base+8+i*4,4,0)for i in range(8));writes.append((base+4,1,1))
    out=bytearray(data)
    for address,size,value in writes:out[address-TASKS:address-TASKS+size]=value.to_bytes(size,'little')
    order=[*chain[:at],target,*chain[at:]];need(task_chain(bytes(out))==order,'expected task列')
    return bytes(out),target,writes,order


def outside_writes(machine,objects):
    allowed=set(range(machine.low_sp,vm.SP));stack=set(range(vm.STACK_LO,vm.STACK_HI))
    for start,length in objects:
        need(type(start)is int and type(length)is int and 0<=start<start+length<=0x100000000,'object範囲')
        span=set(range(start,start+length));need(not span&stack,'object/stack alias');allowed.update(span)
    return [list(w)for w in machine.writes if not all(w[0]+i in allowed for i in range(w[1]))]


def text_body(raw):
    need(type(raw)is bytes and 255 in raw,'有限FF')
    body=raw[:raw.index(255)+1]
    need(not any(c in (252,253)for c in body[:-1]),'再帰/制御textは別契約')
    return body


def fd_expected(dest,names):
    need(type(dest)is int and 0<=dest<0x100000000 and names,'FD引数')
    output=bytearray([80]);writes=[(dest,1,80)];cursor=1
    for name in names:
        body=text_body(name)
        for i,b in enumerate(body):writes.append((dest+cursor+i,1,b))
        output.extend(body[:-1]);cursor+=len(body)-1
        writes.append((dest+cursor,1,96));output.append(96);cursor+=1
    writes.append((dest+cursor,1,255));output.append(255)
    need(dest+len(output)<=0x100000000,'FD上限')
    return bytes(output),writes


def verify(nodes,analysis):
    need(len(nodes)==1935 and analysis['cached_node_count']==1859 and analysis['new_node_count']==76,'保存node数')
    need(analysis['pending_direct_callees']==[0x08002e4d,0x08002e79,0x08003eed]and analysis['pending_continuations']==[],'pending callee集合')
    import pr16_ring_text_frontier as frontier
    tables=analysis['tables'];frontier.validate_texts(tables[7:],nodes,[(t['start'],t['length'])for t in tables[:7]])
    segments=[(t['start'],bytes.fromhex(t['hex']),False)for t in tables]
    text={t['start']:text_body(bytes.fromhex(t['hex']))for t in tables[7:]}
    rows=[];stops=[]
    def returned(machine,label,objects):
        need(not outside_writes(machine,objects),'object/owned frame外write '+label)
        rows.append({'case':label,'steps':machine.steps,'return_r0':machine.r[0],
            'maximum_stack_bytes':vm.SP-machine.low_sp,'writes':machine.nonstack_writes(),
            'call_arguments':machine.call_arguments,'return_sp_callee_saved_proven':True})
    def stopped(machine,entry,label,error,site):
        try:machine.run(entry)
        except ValueError as exc:need(str(exc)==error and machine.last_pc==site,'停止地点差分 '+label)
        else:raise ValueError('未証明境界を通過 '+label)
        stops.append({'case':label,'error':error,'site':site,'read_fault':machine.read_fault,
            'writes':machine.nonstack_writes(),'call_arguments':machine.call_arguments,'return_proven':False})
    # 既存callee単独試験ではなく、実CreateTask本体・挿入・data消去・active化の縦結合。
    create_cases=[]
    for first in range(17):
        chain=list(range(first));priorities=[i*13 for i in range(first)]
        for p in (0,13,127,195,255,0x12340032):
            create_cases.append((chain,priorities,0x08012345,p))
    for missing in range(16):
        chain=[(i*7+3)%16 for i in range(16)if (i*7+3)%16!=missing]
        for p in (0,50,51,255):create_cases.append((chain,[50]*15,0x09378a31,p))
    for i,(chain,priorities,cb,p)in enumerate(create_cases):
        data=task_fixture(chain,priorities);expected,target,writes,order=created(data,cb,p)
        machine=Machine(nodes,[(TASKS,data,True)],(cb,p)).run(CREATE)
        need(machine.data(TASKS,len(data))==expected and machine.r[0]==target,'CreateTask出力')
        need(machine.nonstack_writes()==writes,'CreateTask順序/32byte data消去/active化')
        calls=[c for c in machine.call_arguments if c['site']==0x08076bd4]
        need(len(calls)==(1 if writes else 0)and all(0<=c['args'][0]<COUNT and c['args'][0]==target for c in calls),'実caller index域')
        need(task_chain(machine.data(TASKS,len(data)))==order,'新task列不変条件')
        returned(machine,'create-'+str(i),[(TASKS,len(data))])
    # exact保存命令によるindex loop、遷移・上限を独立に固定する。全callerを証明するものではない。
    known={n['address']:n for n in nodes}
    loop={0x08076bbc:'0026',0x08076bc0:'b000',0x08076bc2:'8019',0x08076bc4:'c500',
        0x08076bd2:'301c',0x08076bf4:'701c',0x08076bf6:'0006',0x08076bf8:'060e',
        0x08076bfa:'0f2e',0x08076bfc:'e0d9',0x08076bfe:'0020'}
    need(all(known[p]['hex']==h for p,h in loop.items()),'caller loop保存byte')
    need(known[0x08076bfc]['target']==0x08076bc0 and known[0x08076bd4]['target']==INSERT-1,'caller loop edge')
    # 実ROM文字列を参照するFD全11組、gender2値、single/繰返し、終端ぴったり/不足。
    refs=[(5,0,0x083dd1dd),(5,1,0x083dd1e0),(6,0,0x083dd210),(6,1,0x083dd20c),
        (7,0,0x083dd1ea),(8,0,0x083dd1f2),(9,0,0x083dd1ee),(10,0,0x083dd1fb),
        (11,0,0x083dd1f6),(12,0,0x083dd206),(13,0,0x083dd200)]
    for index,gender,pointer in refs:
        for repetitions in (1,2,8):
            name=text[pointer];expected,writes=fd_expected(CTX,[name]*repetitions)
            data=bytes([80])+bytes([253,index,96])*repetitions+b'\xff'
            globals_=[(GLOBAL1,SB1.to_bytes(4,'little'),False),(GLOBAL2,SB2.to_bytes(4,'little'),False),
                (SB2,bytes([32,33,255,0,0,0,0,0,gender]),False),(SB1+0x3a4c,b'\xff',False)]
            for padding in (0,1,16):
                machine=Machine(nodes,[(CTX,b'\xcc'*(len(expected)+padding),True),(SRC,data,False),*globals_,*segments],(CTX,SRC)).run(STRING)
                need(machine.data(CTX,len(expected)+padding)==expected+b'\xcc'*padding and machine.r[0]==CTX+len(expected)-1,'実text容量')
                need(machine.nonstack_writes()==writes,'実text正確write')
                returned(machine,f'text-{index}-{gender}-{repetitions}-{padding}',[(CTX,len(expected)+padding)])
            machine=Machine(nodes,[(CTX,b'\xcc'*(len(expected)-1),True),(SRC,data,False),*globals_,*segments],(CTX,SRC))
            stopped(machine,STRING,f'text-short-{index}-{gender}-{repetitions}','未許可 write',0x08008c2a)
            need(machine.nonstack_writes()==writes[:-1] and not outside_writes(machine,[(CTX,len(expected)-1)]),'不足buffer停止')
    # 非nullは保存32byte書込/16byte転送とnibble引数まで。未読calleeをstub成功にしない。
    for value in (0,1,127,255,0x17f):
        for nibble in (0,1,0x7f,0x80,255):
            src=bytearray(range(16));src[12]=nibble;src[13]=255-nibble
            machine=Machine(nodes,[(GATE_WORD,(1).to_bytes(4,'little'),False),
                (GATE_CONTEXT,b'\xcc'*32,True),(SRC,bytes(src),False)],(SRC,value,0x08012345))
            stopped(machine,GATE,f'nonnull-{value}-{nibble}','保存node境界で停止',0x08002e78)
            effective=1 if value&255==127 else value&255
            expected=bytes(src)+(0x08012345).to_bytes(4,'little')+bytes(7)+bytes([1,0,effective,0,0])
            need(machine.data(GATE_CONTEXT,32)==expected,'非null context32byte')
            call=machine.call_arguments[-1]
            need(call['site']==0x08002d48 and call['args'][:3]==[nibble>>4,(255-nibble)&15,(255-nibble)>>4],'非null nibble引数')
            need(not outside_writes(machine,[(GATE_CONTEXT,32)])and machine.r[13]==vm.SP-20,'非null frame限定')
    for value in (0,0x3fff,0x4000,0x4010,0x410f,0xffff,0x14010):
        machine=Machine(nodes,[],(value,));stopped(machine,VARGET,'var-veneer-'+str(value),'保存node境界で停止',0x090970dc)
        need(machine.r[0]==value&65535 and machine.r[4]==value&65535 and not machine.nonstack_writes(),'VarGet中継引数')
    return {'classification':'SAVED_CREATE_CALLER_TEXT_CAPACITY_AND_NONNULL_PREFIX_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':len(rows),'contracts':rows,'limited_prefix_stops':stops,
        'create_task_caller_cases':len(create_cases),'actual_rom_text_count':len(text),'string_capacity_success_cases':99,
        'specific_create_caller_index_lt16_proven':True,'full_create_returns_zero_ambiguous_with_slot0':True,
        'specific_caller_proof_sites':loop,'valid_task_chain_required':True,'all_live_task_lists_acyclic_proven':False,
        'all_live_string_buffers_large_enough_proven':False,'all_callers_resolved':False,'all_live_frames_proven':False,
        'caller_pointer_size_limit_proven':False,'all_runtime_owners_excluded':False,
        'pending_direct_callees':[0x08002e4d,0x08002e79,0x08003eed],'pending_effective_targets':[0x090970dd],
        'pending_data_ranges':[],'pending_continuations':[],
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'preconditions':['CreateTask保存bodyはindex0..15を走査。全slot非空では0を返しslot0成功と値だけでは区別不可。',
            'task合成は逆link・単一head・非循環・priority順序を満たす640byte入力前提。割込み/同時更新/live snapshotは未観測。',
            'ROM11文字列は実byte。選択globalは合成fixtureで、出力容量はFFを含めた明示mapping。live caller allocationは未証明。',
            '非null転送は16byte入力と32byte contextの非alias/整列前提。未読callee帰還やstory/Ring取得に昇格しない。']}


def analyze(prior_report,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_text_frontier as frontier
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*prior_report['analysis']['new_nodes']]
    result=verify(nodes,prior_report['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'summary.json').write_bytes(s.stable({k:result[k]for k in ('classification','synthetic_contract_cases','create_task_caller_cases',
        'actual_rom_text_count','pending_direct_callees','pending_effective_targets')}))
    return result


def summaries(result):
    return (f'保存1935命令でCreateTask実caller{result["create_task_caller_cases"]}件・11実文字列の容量99件を合成。'
        '当該callerのindex0..15・満杯0返却、非null32byte初期化と16byte転送を限定検証。live allocation/Ring未証明。',
        '次は未読3callee0x08002E4D/0x08002E79/0x08003EEDとVarGet実中継先0x090970DDだけを有限採取する。'
        '保存CreateTask caller/11文字列/非nullprefixを再利用し、live task列/文字列allocationとstory到達は別証拠で結合する。'
        '満杯0返却をslot0成功へ、合成prefixをcallee帰還へ読み替えない。旧採取/795/716/BP/nativeを単独再実行しない。Ring/policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_text_frontier as frontier
    import pr16_ring_reference_contracts as previous
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((frontier.SELF,previous.SELF,prior.SELF,prior.prior.SELF,vm.SELF,vm.flow.SELF,*previous.SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
