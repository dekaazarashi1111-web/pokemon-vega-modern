#!/usr/bin/env python3
"""保存Thumb nodeの合成契約。合成bufferだけで検証し、ROM/nativeを起動しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import pr16_ring_owner_context as flow

BASE='b4bb860473dd7c3070f44f76cdeae4e907807328'
SLUG='pr16-ring-saved-contracts'
TASK='PR-P08-7-RING-SAVED-CONTRACTS'
TITLE='保存copy/checksum/cursor/metadata初期化の書込とframeを結合検証'
SELF='scripts/pr16_ring_saved_contracts.py'
TEST='tests/test_pr16_ring_saved_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-saved-contracts.yml'
PRIOR=flow.REPORT
FRONTIER=flow.PRIOR
PATCH=flow.PATCH
REPORT='content/modernization/pr16_ring_saved_contracts.json'
KEY='latest_ring_diagnostic'
SOURCES=(FRONTIER,PATCH,flow.SELF,'scripts/pr16_ring_flagset_continuation.py')
EXTRA_CODE=()
MIN_TESTS=32
NO_REPEAT=('保存callback/cursor/copy2048/checksum/LE32/runtime metadata初期化とvalidator prefixの合成契約を再利用。'
           'synthetic frameをlive frame・Ring取得と同一視しない。新規byte採取0、既読ABI/nativeを単独再実行しない。')
need=flow.need
MASK=0xffffffff
STACK_LO,STACK_HI,SP,RETURN=0x03007000,0x03008000,0x03007f00,0x08000101
COPY,HASH,WRITE,CURSOR,CALLBACK,INIT,ENSURE,VALIDATE=0x09378b95,0x093bd971,0x093bede1,0x080691d1,0x080690b5,0x093bee4d,0x093bee79,0x093bd9a9
META,BUFFER,BACKUP=0x0203f0a0,0x0203d000,0x02039a14


class Machine:
    """保存命令限定の小さな実行モデル。未読命令/未map/整列違反はfail closed。"""
    def __init__(self,nodes,segments,args=()):
        self.nodes=flow.node_map(nodes);self.mem={};self.writable=set();self.writes=[];self.calls=[]
        for lo,data,writable in [*segments,(STACK_LO,bytes(STACK_HI-STACK_LO),True)]:
            need(type(lo)is int and type(data)is bytes and 0<=lo<=lo+len(data)<=0x100000000,'segment境界')
            for offset,value in enumerate(data):
                at=lo+offset;need(at not in self.mem,'segment重複');self.mem[at]=value
                if writable:self.writable.add(at)
        self.r=[0xA0000000+i*0x101 for i in range(16)]
        self.r[:len(args)]=args;self.r[13]=SP;self.r[14]=RETURN
        need(all(type(v)is int and 0<=v<=MASK for v in self.r),'register範囲')
        self.original=tuple(self.r);self.flags=(False,False,False,False);self.low_sp=SP;self.steps=0
    def read(self,at,size):
        need(type(at)is int and at>=0 and at+size<=0x100000000,'read範囲')
        need(size in (1,2,4) and at%size==0,'read整列')
        need(all(at+i in self.mem for i in range(size)),'未map read')
        return sum(self.mem[at+i]<<(8*i) for i in range(size))
    def write(self,at,size,value):
        need(type(at)is int and at>=0 and at+size<=0x100000000,'write範囲')
        need(size in (1,2,4) and at%size==0,'write整列')
        need(all(at+i in self.writable for i in range(size)),'未許可 write')
        for i in range(size):self.mem[at+i]=(value>>(8*i))&255
        self.writes.append((at,size,value&((1<<(size*8))-1)))
    def arithmetic(self,a,b,sub=False,carry=0):
        total=a-b if sub else a+b+carry;v=total&MASK
        c=a>=b if sub else total>MASK
        overflow=bool(((a^b)&(a^v)&0x80000000) if sub else (~(a^b)&(a^v)&0x80000000))
        self.flags=(bool(v&0x80000000),v==0,c,overflow);return v
    def branch(self,condition):
        n,z,c,v=self.flags
        return (z,not z,c,not c,n,not n,v,not v,c and not z,(not c)or z,n==v,n!=v,(not z)and(n==v),z or(n!=v))[condition]
    def run(self,entry,max_steps=100000):
        need(type(entry)is int and entry&1,'Thumb entry')
        need(type(max_steps)is int and 1<=max_steps<=100000,'step上限')
        pc=entry&~1
        while pc!=(RETURN&~1):
            need(self.steps<max_steps,'step上限到達');self.steps+=1
            self.last_pc=pc;need(pc in self.nodes,'保存node境界で停止')
            n=self.nodes[pc];raw=bytes.fromhex(n['hex']);h=int.from_bytes(raw[:2],'little');nextpc=pc+len(raw)
            rd=h&7;rs=(h>>3)&7
            if n['kind']=='call':
                need(len(raw)==4 and h&0xf800==0xf000,'call上位')
                lo=int.from_bytes(raw[2:],'little');need(lo&0xf800==0xf800,'call下位')
                hi=h&0x7ff;hi=hi-0x800 if hi&0x400 else hi
                target=pc+4+(hi<<12)+((lo&0x7ff)<<1);need(target==n['target'],'call結合')
                self.r[14]=pc+5;self.calls.append((pc,target|1));nextpc=target
            elif n['kind'] in ('indirect','return'):
                need(h&0xff87==0x4700,'BX以外の間接は未対応')
                target=self.r[(h>>3)&15];need(target&1,'ARM state未対応');nextpc=target&~1
            elif n['kind'] in ('jump','conditional'):
                if n['kind']=='jump':
                    need(h&0xf800==0xe000,'jump形式');d=h&0x7ff;d=d-0x800 if d&0x400 else d;take=True
                else:
                    condition=(h>>8)&15;need(h&0xf000==0xd000 and condition<14,'条件形式')
                    d=h&255;d=d-256 if d&128 else d;take=self.branch(condition)
                target=pc+4+2*d;need(target==n['target'],'branch結合')
                if take:nextpc=target
            elif h&0xf600==0xb400:
                indices=[i for i in range(8) if h&(1<<i)]
                if h&0x100:indices.append(15 if h&0x800 else 14)
                if h&0x800:
                    for i in indices:self.r[i]=self.read(self.r[13],4);self.r[13]+=4
                    if 15 in indices:need(self.r[15]&1,'POP PC state');nextpc=self.r[15]&~1
                else:
                    self.r[13]-=len(indices)*4
                    need(STACK_LO<=self.r[13]<=SP,'stack下限')
                    for j,i in enumerate(indices):self.write(self.r[13]+j*4,4,self.r[i])
                self.low_sp=min(self.low_sp,self.r[13])
            elif h&0xf000==0x5000:
                op=(h>>9)&7;at=(self.r[rs]+self.r[(h>>6)&7])&MASK
                if op<3:self.write(at,(4,2,1)[op],self.r[rd])
                else:
                    width=(1,4,2,1,2)[op-3];value=self.read(at,width)
                    if op in (3,7) and value&(1<<(width*8-1)):value-=1<<(width*8)
                    self.r[rd]=value&MASK
            elif h&0xe000==0x6000 or h&0xf000==0x8000:
                width=2 if h&0xf000==0x8000 else (1 if h&0x1000 else 4)
                at=(self.r[rs]+((h>>6)&31)*width)&MASK
                if h&0x800:self.r[rd]=self.read(at,width)
                else:self.write(at,width,self.r[rd])
            elif h&0xf800==0x2800:self.arithmetic(self.r[(h>>8)&7],h&255,True)
            elif h&0xfc00==0x4000 and (h>>6)&15 in (5,6,9,10,11):
                op=(h>>6)&15;a,b=self.r[rd],self.r[rs];carry=int(self.flags[2])
                if op==5:self.r[rd]=self.arithmetic(a,b,carry=carry)
                elif op==6:self.r[rd]=self.arithmetic(a,b+1-carry,True)
                elif op==9:self.r[rd]=self.arithmetic(0,b,True)
                elif op==10:self.arithmetic(a,b,True)
                else:self.arithmetic(a,b)
            elif h&0xf800==0x1800:
                x=(h>>6)&7;b=x if h&0x400 else self.r[x]
                self.r[rd]=self.arithmetic(self.r[rs],b,bool(h&0x200))
            elif h&0xf800 in (0x3000,0x3800):
                reg=(h>>8)&7;self.r[reg]=self.arithmetic(self.r[reg],h&255,bool(h&0x800))
            else:
                after=flow.transfer(n,tuple(self.r));need(all(type(v)is int for v in after),'未具体化register')
                self.r=list(after)
            pc=nextpc
        need(self.r[13]==SP and self.r[4:12]==list(self.original[4:12]),'return/SP/callee-saved差分')
        return self
    def data(self,at,size):return bytes(self.mem[at+i] for i in range(size))
    def nonstack_writes(self):return [w for w in self.writes if not STACK_LO<=w[0]<STACK_HI]


def saved_nodes(frontier,patch):
    return list(flow.node_map([*frontier['new_nodes'],*(n for g in patch['frontier']['graphs'] for n in g['nodes'])]).values())


def checksum(data):
    need(type(data)is bytes and len(data)==2048,'checksum入力長')
    result=0x811c9dc5
    for i,b in enumerate(data):result=((result^(0 if 8<=i<12 else b))*0x01000193)&MASK
    return result


def metadata_expected():
    data=bytearray(96);data[:4]=(0x31564552).to_bytes(4,'little')
    for offset in (16,18,20):data[offset:offset+2]=b'\xff\xff'
    data[32]=255;return bytes(data)


def verify_contracts(nodes,context):
    cases=[]
    def record(label,vm,expected_writes=None):
        writes=vm.nonstack_writes()
        points=sorted({at+i for at,width,_ in writes for i in range(width)});ranges=[]
        for at in points:
            if ranges and ranges[-1][1]==at:ranges[-1][1]+=1
            else:ranges.append([at,at+1])
        if expected_writes is not None:need(writes==expected_writes,'書込列差分 '+label)
        cases.append({'case':label,'return_r0':vm.r[0],'instruction_steps':vm.steps,
                      'maximum_stack_bytes':SP-vm.low_sp,'nonstack_write_count':len(writes),
                      'sp_and_r4_r11_restored':True,'nonstack_write_ranges':ranges})
    for callback in (0x08068ddd,0x0806b159):
        vm=Machine(nodes,[(0x02001000,bytes([0xcc])*64,True)],(0x02001000,callback)).run(CALLBACK)
        record('script-callback-'+hex(callback),vm,[(0x02001001,1,2),(0x02001004,4,callback)])
    for word in (0,1,0x80000000,0xffffffff,0x04030201):
        ctx=bytearray(64);ctx[8:12]=(0x02002000).to_bytes(4,'little')
        vm=Machine(nodes,[(0x02001000,bytes(ctx),True),(0x02002000,word.to_bytes(4,'little'),False)],(0x02001000,)).run(CURSOR)
        need(vm.r[0]==word and vm.read(0x02001008,4)==0x02002004,'cursor/LE32差分')
        record('cursor-'+hex(word),vm,[(0x02001008,4,0x02002000+i) for i in range(1,5)])
    copy_row=next(r for r in context['rows'] if r['entry']==COPY)['callsite_bindings'][0]
    need(copy_row['arguments']['r0']=='0x0203D000' and copy_row['arguments']['r1']=='0x02039A14'
         and copy_row['arguments']['r2']=='0x00000800','実copy callsite不一致')
    for seed in (0,1,17,255):
        data=bytes((i*73+seed)&255 for i in range(2048))
        vm=Machine(nodes,[(BACKUP,data,False),(BUFFER,bytes(2048),True)],(BUFFER,BACKUP,2048)).run(COPY)
        need(vm.data(BUFFER,2048)==data,'2048byte copy差分')
        record('copy2048-'+str(seed),vm,[(BUFFER+i,1,b) for i,b in enumerate(data)])
        vm=Machine(nodes,[(BUFFER,data,False)],(BUFFER,)).run(HASH)
        need(vm.r[0]==checksum(data),'checksum差分');record('checksum-'+str(seed),vm,[])
        out=Machine(nodes,[(BUFFER,bytes(16),True)],(BUFFER+8,vm.r[0])).run(WRITE)
        need(out.data(BUFFER+8,4)==checksum(data).to_bytes(4,'little'),'checksum slot LE32差分')
        record('checksum-write-'+str(seed),out,[(BUFFER+8+i,1,b) for i,b in enumerate(checksum(data).to_bytes(4,'little'))])
    for initial in (bytes(96),bytes([255])*96):
        vm=Machine(nodes,[(META,initial,True)]).run(INIT)
        need(vm.data(META,96)==metadata_expected(),'metadata初期化差分');record('metadata-init-'+str(initial[0]),vm)
        need(len(vm.nonstack_writes())==101,'metadata write件数')
    initial=metadata_expected();vm=Machine(nodes,[(META,initial,True)]).run(ENSURE)
    need(vm.data(META,96)==initial,'metadata維持差分');record('metadata-ensure-valid',vm,[])
    vm=Machine(nodes,[(META,bytes(96),True)]).run(ENSURE)
    need(vm.data(META,96)==metadata_expected(),'metadata合成差分');record('metadata-ensure-invalid',vm)
    for pointer,size,fill,expected in ((0,0,0,6),(0x02001000,2047,1,4),(0x02001000,2048,0,1),
                                     (0x02001000,2048,255,1),(0x02001000,2048,1,2)):
        segments=[] if pointer==0 else [(pointer,bytes([fill])*2048,True)]
        vm=Machine(nodes,segments,(pointer,size)).run(VALIDATE)
        need(vm.r[0]==expected,'validator prefix return差分');record(f'validator-{pointer}-{size}-{fill}',vm,[])
    return {'cases':cases,'synthetic_contract_case_count':len(cases),
            'copy_actual_callsite':copy.deepcopy(copy_row),
            'copy_range':{'source':[BACKUP,BACKUP+2048],'destination':[BUFFER,BUFFER+2048],'length':2048},
            'checksum_contract':{'input_bytes':2048,'zeroed_hash_offsets':[8,9,10,11],
                                 'seed':0x811c9dc5,'multiplier':0x01000193,'output_slot_offset':8},
            'metadata_range':[META,META+96], 'metadata_marker':0x31564552,
            'validator_prefix_return_codes':[6,4,1,2],'validator_success_continuation_proven':False,
            'return_contract_preconditions':['この合成modelの非alias buffer/stackと整列した実引数',
                'copy/zero fillの長さは正・範囲は非wrap・読み書き可能',
                '実callerの到達・全callee帰還・live SP/frameとは別の限定契約'],
            'all_live_frames_proven':False,'all_callers_resolved':False,'caller_pointer_size_limit_proven':False,
            'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
            'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_byte_samples':0,
            'accepted_native_cases_replayed':0,'prior_graph_decoders_replayed':0}


def analyze(prior,out):
    import pr16_ring_followup_v2 as support
    import pr16_ring_flagset_continuation as saved
    frontier,patch=support.load(FRONTIER),support.load(PATCH)
    for report in (frontier,patch):saved.bindings_fresh(support.ROOT,report['source_bindings'])
    nodes=saved_nodes(frontier['analysis'],patch)
    result=verify_contracts(nodes,prior['analysis']);result['candidate']=copy.deepcopy(support.CANDIDATE)
    result['classification']='SAVED_SYNTHETIC_MEMORY_AND_FRAME_CONTRACTS_NOT_NATIVE_ACQUISITION'
    result['next_unread_boundaries']={'direct_callees':[0x08068d89,0x0806916d],
        'computed_jump_site':0x08113806,'validator_window_end':0x093bda28,
        'resolved_trampoline_targets_without_global_abi_proof':prior['analysis']['resolved_trampoline_targets']}
    (out/'analysis.json').write_bytes(support.stable(result));return result


def summaries(result):
    return (f'保存nodeの{result["synthetic_contract_case_count"]}合成ケースでcallback/cursor/copy2048/checksum/LE32/runtime metadata初期化とvalidator早期returnを検証。'
            '書込範囲と合成SP/r4-r11復元を確認。live frame/全callerは未証明。候補復元/ROM/native再実行0。',
            '未読direct callee2件、computed jump表、validator窓外継続と中継先の未読実体だけを進める。'
            '保存済FlagGet/FlagSet・GPIO・剰余/閏年・今回copy/checksum契約の単独再実行は不要。'
            '元initializerの実caller/pointer/size/LIMIT、Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
