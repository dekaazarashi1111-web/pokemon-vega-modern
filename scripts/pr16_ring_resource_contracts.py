#!/usr/bin/env python3
"""保存2970命令のresource/queue/bitmapと12byte callerを結合。実描画やRing受入ではない。"""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import pr16_ring_dispatch_contracts as prior

BASE='56bffb9a6a7f7ba2d5d2c02063cfdc189f8afba4'
SLUG='pr16-ring-resource-contracts'
TASK='PR-P08-7-RING-RESOURCE-CONTRACTS'
TITLE='resourceの予約queue・bitmap・12byte callerの帰還と部分書込を結合'
SELF='scripts/pr16_ring_resource_contracts.py'
TEST='tests/test_pr16_ring_resource_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-resource-contracts.yml'
PRIOR='content/modernization/pr16_ring_resource_tail.json'
REPORT='content/modernization/pr16_ring_resource_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=59
EXTRA_CODE=()
SOURCES=()
need=prior.need
vm=prior.vm
caller=prior.prior.caller
RESOURCE,GETTER,QUEUE,TRANSFER,BITMAP=0x08003eed,0x080011e5,0x08000ead,0x08001299,0x080014f1
FLAGS,CONTEXT,MASK,BITS,ENABLE=0x030008d0,0x030008e8,0x03000928,0x03000938,0x03003dcc
QBASE,LOCK,HEAD=0x030000c8,0x030008c8,0x030008c9
TABLE,RECORDS=0x08001224,0x02020430
NO_REPEAT=('保存2970命令のresource属性/queue/転送/bitmap/12byte caller帰還と不足時部分書込は今回原本を再利用する。'
    '同じbyte採取/旧VarGet/旧external ABI/BP/nativeを単独再実行しない。queue予約をDMA実行・描画・Ring通常取得と同一視しない。'
    'cursor>=128の配列外初回参照、size0再利用、bitmap検索count0/1拒否、実allocation未証明を保持する。')


class Machine(prior.Machine):
    def __init__(self,nodes,segments,args=()):
        super().__init__(nodes,segments,args);self.reads=[]
    def read(self,at,size):
        self.reads.append((at,size,getattr(self,'last_pc',None)))
        return super().read(at,size)


def uint(value,bits,label):
    need(type(value)is int and 0<=value<1<<bits,label+' unsigned');return value


def attribute(channel,selector,flags):
    channel=uint(channel,32,'channel')&255;selector=uint(selector,32,'selector')&255
    need(type(flags)is bytes and len(flags)==2,'属性2byte')
    a,b=flags
    if channel>3 or not a&1:return 255
    values=(a&1,b&3,(b>>2)&31,(a>>2)&3,b>>7,(a>>4)&3,(a>>6)&1,a>>7)
    return values[selector-1]if 1<=selector<=8 else 255


def size_for_copy(channel,flags,display):
    channel=uint(channel,32,'channel')&255;display=uint(display,8,'display')&7
    shape=attribute(channel,4,flags)
    kind=(0 if display in (0,1)else 65535)if channel<2 else (
        (0 if display==0 else 1 if display in (1,2)else 65535)if channel==2 else
        (0 if display==0 else 1 if display==2 else 65535))
    if kind==0:return (1,2,2,4)[shape]*2048 if shape<4 else 0
    if kind==1:return (1,4,16,64)[shape]*256 if shape<4 else 0
    return 0


def bitmap_search(data,bank,count):
    need(type(data)is bytes and len(data)==256,'bitmap256byte')
    uint(bank,8,'bank');uint(count,32,'count')
    if count<2:return 0xffffffff  # 保存命令は最初のfree bitで一致比較しない。
    first=bank*512;limit=min(first+1024,2048);run=0;start=0
    for bit in range(first,limit):
        if data[bit//8]&(1<<(bit%8)):run=0
        else:
            if run==0:start=bit-first
            run+=1
            if run==count:return start
    return 0xffffffff


def queue_image(occupied=()):
    need(type(occupied)in (tuple,list,range,set)and all(type(i)is int and 0<=i<128 for i in occupied),'queue index')
    data=bytearray(b'\xcc'*2048)
    for i in range(128):data[16*i+8:16*i+10]=(1 if i in occupied else 0).to_bytes(2,'little')
    return bytes(data)


def fixture(table,*,channel=0,flags=b'\x01\x00',display=0,head=0,occupied=(),enabled=0,
            slot=0,dims=(1,1),offset=0,context_base=0,pointer=0x02001800,source=0x02001000,bitmap=None):
    for name,value,bits in (('channel',channel,8),('display',display,8),('head',head,8),('slot',slot,8),
                           ('offset',offset,16),('base',context_base,16),('pointer',pointer,32),('source',source,32),('enabled',enabled,32)):
        uint(value,bits,name)
    need(type(flags)is bytes and len(flags)==2,'属性2byte')
    need(type(table)is bytes and len(table)==32,'保存分岐表32byte')
    need(type(dims)in (tuple,list)and len(dims)==2,'dims')
    for d in dims:uint(d,8,'dimension')
    if bitmap is None:bitmap=bytes(256)
    need(type(bitmap)is bytes and len(bitmap)==256,'bitmap256byte')
    flagbytes=bytearray(17)
    for i in range(4):flagbytes[i*4:i*4+2]=flags
    flagbytes[16]=display
    ctx=bytearray(64)
    for i in range(4):ctx[i*16:i*16+2]=context_base.to_bytes(2,'little');ctx[i*16+4:i*16+8]=pointer.to_bytes(4,'little')
    record=bytes([channel,0,0,*dims,0])+offset.to_bytes(2,'little')+source.to_bytes(4,'little')
    return {'channel':channel,'slot':slot,'segments':[(TABLE,table,False),(FLAGS,bytes(flagbytes),False),
        (CONTEXT,bytes(ctx),False),(QBASE,queue_image(occupied),True),(LOCK,b'\x77',True),(HEAD,bytes([head]),False),
        (MASK,bytes(16),True),(BITS,bitmap,True),(ENABLE,enabled.to_bytes(4,'little'),False),
        (RECORDS+slot*12,record,False)]}


class Expected:
    """保存Thumbと独立した有界RAMモデル。queue予約のみ、src/dstをコピーしない。"""
    def __init__(self,segments):
        self.mem={};self.writes=[];self.reservations=[]
        for at,data,_ in segments:
            for i,b in enumerate(data):need(at+i not in self.mem,'expected alias');self.mem[at+i]=b
    def read(self,at,size):
        need(all(at+i in self.mem for i in range(size)),'expected missing')
        return sum(self.mem[at+i]<<(8*i)for i in range(size))
    def write(self,at,size,value):
        need(all(at+i in self.mem for i in range(size)),'expected write bounds')
        value&=(1<<(8*size))-1
        for i in range(size):self.mem[at+i]=(value>>(8*i))&255
        self.writes.append((at,size,value))
    def attr(self,channel,selector):
        c=channel&255
        return attribute(c,selector,bytes(self.mem[FLAGS+c*4+i]for i in range(2)))if c<=3 else 255
    def queue(self,source,dest,length,mode):
        self.write(LOCK,1,1);index=self.read(HEAD,1)
        for _ in range(128):
            at=QBASE+16*index
            if self.read(at+8,2)==0:
                for p,n,v in ((at,4,source),(at+4,4,dest),(at+8,2,length),(at+10,2,1 if mode&255==1 else 3)):
                    self.write(p,n,v)
                self.write(LOCK,1,0)
                self.reservations.append({'index':index,'source':source,'destination':dest,'length':length&65535})
                return index
            index=0 if index>=127 else index+1
        self.write(LOCK,1,0);return 0xffffffff
    def transfer(self,channel,source,length,offset,mode):
        c=channel&255;mode&=255
        if c>3 or self.attr(c,1)!=1 or mode not in (1,2):return 255
        base=self.attr(c,2)*16384 if mode==1 else self.attr(c,3)*2048
        return self.queue(source,0x06000000+((base+(offset&65535))&65535),length&65535,0)&255
    def bitmap(self,channel,offset,count,mode):
        if mode not in (0,1,2):return 0
        bank=self.attr(channel,2)
        if mode==0:return bitmap_search(bytes(self.mem[BITS+i]for i in range(256)),bank,count)
        first=bank*512+offset
        need(0<=first<=first+count<=2048,'expected bitmap allocation')
        for bit in range(first,first+count):
            at=BITS+bit//8;mask=1<<(bit%8);value=self.read(at,1)
            self.write(at,1,value|mask if mode==1 else value&~mask)
        return 0
    def copy_graphics(self,channel):
        c=channel&255
        if c>3:return
        pointer=self.read(CONTEXT+c*16+4,4)
        if pointer==0 or pointer>0x03008000:return
        flags=bytes(self.mem[FLAGS+c*4+i]for i in range(2))
        self.transfer(c,pointer,size_for_copy(c,flags,self.read(FLAGS+16,1)),0,2)
    def tiles(self,channel,source,length,offset):
        c=channel&255
        base=self.read(CONTEXT+c*16,2)&1023
        scaled=((base+(offset&65535))<<(5 if self.attr(c,5)==0 else 6))&65535
        result=self.transfer(c,source,length,scaled,1)
        if result==255:return 65535
        at=MASK+4*(result//32);self.write(at,4,self.read(at,4)|(1<<(result%32)))
        if self.read(ENABLE,4)==1:self.bitmap(c,scaled//32,(length&65535)//32,1)
        return result
    def resource(self,slot,mode):
        at=RECORDS+(slot&255)*12;c=self.read(at,1)
        length=(self.read(at+3,1)*self.read(at+4,1)*32)&65535
        if mode&255 in (2,3):self.tiles(c,self.read(at+8,4),length,self.read(at+6,2))
        if mode&255 in (1,3):self.copy_graphics(c)
        return vm.RETURN  # 外側pop r0は返却値ではなく保存LRを復元する。


def execute(nodes,case,entry,args,model,*,fifth=None):
    expected=Expected(case['segments']);value=getattr(expected,model)(*args,*(()if fifth is None else(fifth,)))
    machine=Machine(nodes,case['segments'],args)
    if fifth is not None:
        for i,b in enumerate(fifth.to_bytes(4,'little')):machine.mem[vm.SP+i]=b
    machine.run(entry)
    need(machine.r[0]==value and machine.nonstack_writes()==expected.writes,'resource戻値/正確順序書込')
    need(all(machine.mem[p]==b for p,b in expected.mem.items()),'resource最終object差分')
    objects=[(at,len(data))for at,data,w in case['segments']if w]
    need(not caller.outside_writes(machine,objects),'resource object/frame外書込')
    need(all(not 0x06000000<=p<0x07000000 for p,_,_ in machine.nonstack_writes()),'queue予約を実VRAM書込に昇格')
    return machine,expected


def verify(nodes,analysis):
    need(len(nodes)==analysis['saved_node_count']==2970 and analysis['cached_node_count']==2850,'保存2970命令差分')
    need(analysis['pending_direct_callees']==[]and analysis['pending_continuations']==[],'未読callee差分')
    table=bytes.fromhex(analysis['resource_switch_table']['hex']);need(len(table)==32,'保存table幅')
    rows=[];stops=[];digest=hashlib.sha256();counts={};sites=set()
    def record(machine,expected,label,group,full=False):
        counts[group]=counts.get(group,0)+1;sites.update(machine.executed_sites)
        digest.update(json.dumps([label,machine.r[0],expected.writes],separators=(',',':')).encode())
        if full:rows.append({'case':label,'steps':machine.steps,'return_r0':machine.r[0],
            'maximum_stack_bytes':vm.SP-machine.low_sp,'writes':machine.nonstack_writes(),
            'call_arguments':machine.call_arguments,'reservations':expected.reservations,
            'return_sp_callee_saved_proven':True,'allocation_scope':'EXPLICIT_SYNTHETIC_DISJOINT_RAM_ONLY'})
    flags=[bytes([a,b])for a,b in ((0,0),(1,0),(255,255),(0x55,0xaa),(0xab,0x55),
        (5,1),(9,2),(13,3),(17,4),(33,8),(65,16),(129,32),(1,64),(1,128))]
    for c in (0,1,2,3,4,255,0x100):
        for fs in flags:
            for selector in (0,1,2,3,4,5,6,7,8,9,0x101):
                case=fixture(table,flags=fs);m=Machine(nodes,case['segments'],(c,selector)).run(GETTER)
                need(m.r[0]==attribute(c,selector,fs) and not m.nonstack_writes(),'getter有限全分岐')
                e=Expected(case['segments']);record(m,e,f'getter-{c}-{fs.hex()}-{selector}','attribute')
    for head in (0,1,31,32,126,127):
        patterns=((),(head,),tuple(range(128)),tuple(i for i in range(128)if i!=(head-1)%128))
        for p,occupied in enumerate(patterns):
            for length in (0,1,32,65535):
                for mode in (0,1,255):
                    case=fixture(table,head=head,occupied=occupied)
                    m,e=execute(nodes,case,QUEUE,(0x02001801,0x06000002,length,mode),'queue')
                    record(m,e,f'queue-{head}-{p}-{length}-{mode}','queue',head==127 and length in (0,32)and mode==0)
    for c in range(4):
        for fs in (b'\x01\x00',b'\xff\xff',b'\x00\x00'):
            for mode in (0,1,2,255,0x101):
                for offset in (0,65535):
                    case=fixture(table,channel=c,flags=fs)
                    m,e=execute(nodes,case,TRANSFER,(c,0xffffffff,0x10021,offset),'transfer',fifth=mode)
                    record(m,e,f'transfer-{c}-{fs.hex()}-{mode}-{offset}','transfer')
    for bank in range(4):
        for data in (bytes(256),b'\xff'*256,b'\xaa'*256,bytes([255])*10+bytes(246)):
            for count in (0,1,2,7,512,1024,1025):
                case=fixture(table,flags=bytes([1,bank]),bitmap=data)
                m,e=execute(nodes,case,BITMAP,(0,123,count,0),'bitmap')
                record(m,e,f'search-{bank}-{hashlib.sha256(data).hexdigest()[:8]}-{count}','bitmap-search')
        for mode in (1,2):
            for offset,count in ((0,0),(0,1),(7,9),(127,33),(511,1)):
                case=fixture(table,flags=bytes([1,bank]),bitmap=b'\xaa'*256)
                m,e=execute(nodes,case,BITMAP,(0,offset,count,mode),'bitmap')
                record(m,e,f'bitmap-{bank}-{offset}-{count}-{mode}','bitmap-write',offset==7)
    for c in range(4):
        for shape in range(4):
            for mode in (1,2,3):
                for enabled in (0,1):
                    case=fixture(table,channel=c,flags=bytes([1|shape<<2,0x80 if shape&1 else 0]),
                        display=c%3,enabled=enabled,head=127,occupied=(127,),slot=31,dims=(3,2),offset=7,context_base=8)
                    m,e=execute(nodes,case,RESOURCE,(31,mode),'resource')
                    record(m,e,f'record-{c}-{shape}-{mode}-{enabled}','record-caller',True)
    for mode in (1,2,3):
        for dims in ((0,0),(255,255)):
            for occupied in ((),tuple(range(128))):
                case=fixture(table,slot=255,dims=dims,occupied=occupied,flags=b'\x01\x03')
                m,e=execute(nodes,case,RESOURCE,(255,mode),'resource')
                record(m,e,f'edge-{mode}-{dims}-{bool(occupied)}','record-edge',True)
    for pointer in (0,1,0x02000001,0x03008000,0x03008001,0xffffffff):
        case=fixture(table,pointer=pointer,display=7)
        m,e=execute(nodes,case,RESOURCE,(0,1),'resource');record(m,e,f'pointer-{pointer:08x}','pointer-limit',True)
    normal=fixture(table,slot=0,enabled=1,dims=(2,2));_,expected=execute(nodes,normal,RESOURCE,(0,3),'resource')
    for address in (TABLE,FLAGS,CONTEXT,QBASE,LOCK,HEAD,MASK,BITS,ENABLE,RECORDS):
        for damage in ('missing','short','readonly'):
            segment=next(s for s in normal['segments']if s[0]==address)
            if damage=='readonly'and not segment[2]:continue
            case=copy.deepcopy(normal);changed=[]
            for at,data,w in case['segments']:
                if at==address:
                    if damage=='missing':continue
                    if damage=='short':data=data[:(11 if at==RECORDS else 0)]
                    if damage=='readonly':w=False
                changed.append((at,data,w))
            m=Machine(nodes,changed,(0,3))
            try:m.run(RESOURCE)
            except ValueError as exc:need(str(exc)in ('未map read','未許可 write'),'不足停止種別')
            else:raise ValueError('不足を成功へ昇格')
            need(m.nonstack_writes()==expected.writes[:len(m.nonstack_writes())],'不足前部分書込')
            stops.append({'case':f'{address:08x}-{damage}','site':m.last_pc,'read_fault':m.read_fault,
                'writes':m.nonstack_writes(),'call_arguments':m.call_arguments,'return_proven':False,'rollback_claimed':False})
    cursor_diagnostics=[]
    for head in (128,255):
        case=fixture(table,head=head);m=Machine(nodes,case['segments'],(0x02001800,0x06000000,32,0))
        try:m.run(QUEUE)
        except ValueError as exc:
            need(head==255 and str(exc)=='未map read','cursor配列外停止')
            need(m.nonstack_writes()==[(LOCK,1,1)],'cursor配列外時lock保持')
            stops.append({'case':f'cursor-{head}','site':m.last_pc,'read_fault':m.read_fault,'writes':m.nonstack_writes(),
                'call_arguments':m.call_arguments,'return_proven':False,'rollback_claimed':False})
        else:
            need(head==128 and m.r[0]==0,'cursor128は隣接flagsをoccupied扱いしてwrap')
        first=next((at,width)for at,width,site in m.reads if site==0x08000eda)
        need(first==(QBASE+16*head+8,2),'cursor初回probe差分')
        cursor_diagnostics.append({'cursor':head,'first_probe':first,'outside_nominal_queue':True,
            'synthetic_return_observed':head==128,'queue_bound_proven':False})
    return {'classification':'SAVED_RESOURCE_QUEUE_BITMAP_CALLER_CONTRACTS_NOT_DMA_OR_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':sum(counts.values()),'case_counts':counts,
        'case_digest_sha256':digest.hexdigest(),'executed_sites':sorted(sites),'contracts':rows,'limited_stops':stops,
        'resource_caller_conditional_returns_proven':True,'queue_write_order_proven':True,
        'queue_capacity':128,'queue_entry_bytes':16,'bitmap_search_count_0_or_1_returns':4294967295,
        'zero_length_reservation_consumes_slot':False,'cursor_range_checked_by_code':False,
        'cursor_diagnostics':cursor_diagnostics,'reservation_is_dma_completion':False,'source_destination_buffers_read_or_written':False,
        'unbound_runtime_data':copy.deepcopy(analysis['unbound_runtime_data']),
        'pending_direct_callees':[],'pending_effective_targets':[],'pending_continuations':[],'pending_data_ranges':[],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'all_dispatch_returns_proven':False,'all_live_slot_bounds_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['明示同期RAM/有界非alias/初期cursor0..127。実allocator/callback選択/割込み状態の証明ではない。',
            '予約時にsrc/dstは非参照。null/奇数/未map pointerを予約できても転送時の安全性は未証明。',
            'length0予約はsize0のままで後続予約が同じslotを上書き可能。count0/1 bitmap検索は失敗を返す。',
            'cursor128は配列外の隣接flagsを読むがreturnする合成例がある。255の未map初回probeではlock1が残る。帰還と配列境界を混同しない。']}


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_resource_tail as frontier
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*previous['analysis']['new_nodes']]
    result=verify(nodes,previous['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    result,raw=prior.prior.archive_effects(result);(out/'raw-effects.json').write_bytes(raw)
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return (f'保存2970命令でresource属性/queue/転送/bitmap/12byte callerの{result["synthetic_contract_cases"]}合成契約と'
        f'{len(result["limited_stops"])}不足停止を結合。128slot予約・部分書込・外側帰還を固定。実DMA/通常取得とは別。',
        '次は実callback table/12byte resource/32byte出力slotのallocation・callback到達と残るownerを照合。'
        'queue予約は実DMA完了でなく、source/destinationの有効性を証明しない。'
        'cursor>=128初回配列外・size0再利用・bitmap検索0/1拒否を保存証拠として保持。'
        '今回resource契約/2970命令/3calleeと表/先の8callee/VarGet/旧external ABI/BP/nativeを単独再実行しない。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    import pr16_ring_resource_tail as frontier
    SOURCES=tuple(dict.fromkeys((frontier.SELF,*frontier.SOURCES,prior.SELF,prior.prior.SELF,
        caller.SELF,caller.prior.SELF,caller.prior.prior.SELF,vm.SELF,vm.flow.SELF)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
