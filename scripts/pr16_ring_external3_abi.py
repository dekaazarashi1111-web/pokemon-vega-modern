#!/usr/bin/env python3
"""保存external3前半の条件分岐・引数・frame契約だけを検証。未読境界で停止する。"""
from __future__ import annotations
import copy
from functools import lru_cache
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '53190a228b3b61fc809d118c685fe84503a460ea'
SLUG = 'pr16-ring-external3-abi'
TASK = 'PR-P08-7-RING-EXTERNAL3-ABI'
TITLE = 'external3保存前半の3条件・引数・20byte frameとalias境界を検証'
SELF = 'scripts/pr16_ring_external3_abi.py'
TEST = 'tests/test_pr16_ring_external3_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-external3-abi.yml'
PRIOR = 'content/modernization/pr16_ring_external3_bytes.json'
REPORT = 'content/modernization/pr16_ring_external3_abi.json'
KEY = 'ring_external3_abi'
SOURCES = ()
EXTRA_CODE = ()
MIN_TESTS = 22
START = 0x081138F8
CONT, TAIL = START + 65, START + 105
COUNT, LIMIT, COUNTER, CAPACITY, BASE_PTR = 0x0203AF10, 0x03005EDC, 0x0203AF96, 0x03002030, 0x0300202C
MASK = 0xffffffff
CODE = ('f0b5','0006','070e','0904','0b0c','1204','120c','9446','1748','0188','0029','27d0',
        '1648','0088','8142','23d2','154e','1649','3088','0988','8842','1dd2','021c','144d',
        '2c68','9200','1219','1349','1940','1388','1248','1840')
LITERALS = dict(zip(range(START + 112, START + 140, 4), (COUNT,LIMIT,COUNTER,CAPACITY,BASE_PTR,32767,0xffff8000)))
NO_REPEAT = 'external3保存前半32命令/64byteのABIは完了。3条件・正規化引数・20byte frameを保存契約として再利用し、再採取/単独ABI再実行しない。次は未読継続0x08113939だけ。末尾0x08113961・旧18owner・外側帰還/非alias・Ring通常取得は未受入。'


def expected_nodes():
    nodes = []
    for i, hx in enumerate(CODE):
        at = START + 2*i; h = int.from_bytes(bytes.fromhex(hx), 'little')
        n = dict(address=at,size=2,hex=hx,kind='ordinary',memory_write=(i==0),successors=[at+2] if i<31 else [])
        if h & 0xf800 == 0x4800:
            address = ((at+4)&~3)+(h&255)*4
            n.update(literal_address=address,literal_value=LITERALS[address])
        elif h & 0xf000 == 0xd000:
            n.update(kind='conditional',target=TAIL&~1)
        nodes.append(n)
    return nodes


def expected_edges():
    edges = [dict(site=START+offset,kind='conditional',target=TAIL,resolved_to_code_address_only=True,
                  stop_reason='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED') for offset in (22,30,42)]
    edges.append(dict(site=START+62,kind='window_fallthrough',target=CONT,resolved_to_code_address_only=True,
                      stop_reason='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED'))
    return edges


def program(prior):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL3-BYTES','先行task差分')
    a=prior['analysis'];g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and a['target']==a['next_saved_abi_target']==START|1,'candidate/target差分')
    s.need(g['entry']==START|1 and g['window']==64 and g['window_identity']==
           {'size':64,'sha256':'4f890b71406471287629badfd597f75fe0bf9be686df2e321e03501cb6317496'},'window差分')
    s.need(g['nodes']==expected_nodes() and g['external_edges']==expected_edges() and g['memory_write_sites']==[START],'命令/辺/副作用差分')
    raw={START+2*i:bytes.fromhex(hx) for i,hx in enumerate(CODE)}
    raw.update({address:value.to_bytes(4,'little') for address,value in LITERALS.items()})
    ranges=[dict(address=address,hex=value.hex(),**s.identity(value)) for address,value in sorted(raw.items())]
    s.need(a['sampled_ranges']==ranges and a['sampled_instruction_bytes']==64,'保存byte/hash差分')
    s.need(g['saved_instruction_bytes_redecoded']==g['deferred_roots_decoded']==0,'再decode')
    old=set(a['old_unread_targets'])
    s.need(len(old)==18 and set(a['remaining_unread_targets'])==old|{CONT,TAIL}
           and set(a['new_unread_targets'])=={CONT,TAIL},'frontier差分')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False,'過大受入')
    return a


def snapshot(count=1,limit=2,index=0,capacity=2,base=0x02010000,record=0x8000):
    """診断用の明示的なbyte snapshot。native観測ではない。"""
    mem={}
    for value in (count,limit,index,capacity,record):s.need(type(value)is int and 0<=value<=65535,'u16範囲')
    s.need(type(base)is int and 0<=base<=MASK and base%4==0,'base範囲/整列')
    for at,width,value in ((COUNT,2,count),(LIMIT,2,limit),(COUNTER,2,index),(CAPACITY,2,capacity),
                           (BASE_PTR,4,base),((base+4*index)&MASK,2,record)):
        for off,byte in enumerate(value.to_bytes(width,'little')):
            s.need(at+off<=MASK and (at+off not in mem or mem[at+off]==byte),'snapshot不一致')
            mem[at+off]=byte
    return mem


def execute(mode,key,value,memory,sp=0x03007F00,lr=0x08100001,preserved=(4,5,6,7)):
    """保存命令だけを解釈。PUSHをbyte snapshotへ反映してからRAMを読む。"""
    s.need(all(type(x)is int and 0<=x<=MASK for x in (mode,key,value,lr)),'引数範囲')
    s.need(type(sp)is int and 20<=sp<=MASK and sp%4==0,'stack範囲/整列')
    s.need(len(preserved)==4 and all(type(x)is int and 0<=x<=MASK for x in preserved),'保存register範囲')
    mem=dict(memory)
    s.need(all(type(at)is int and 0<=at<=MASK and type(b)is int and 0<=b<=255 for at,b in mem.items()),'snapshot byte範囲')
    r=[0]*16;r[:3]=[mode,key,value];r[4:8]=preserved;r[13]=sp;r[14]=lr
    pc=START;compare=None;coverage=[];branches=[];reads=[];writes=[]
    while START<=pc<START+64:
        s.need(pc not in coverage,'循環');coverage.append(pc)
        at=pc;h=int.from_bytes(bytes.fromhex(CODE[(pc-START)//2]),'little');pc+=2
        if h==0xb5f0:
            r[13]-=20
            for i,k in enumerate((4,5,6,7,14)):
                addr=r[13]+4*i;raw=r[k].to_bytes(4,'little')
                mem.update({addr+j:byte for j,byte in enumerate(raw)})
                writes.append(dict(site=at,address=addr,size=4,register=k,value=r[k]))
        elif h & 0xf800 in (0x0000,0x0800):
            shift=(h>>6)&31;v=r[(h>>3)&7]
            r[h&7]=(v<<shift)&MASK if h&0xf800==0 else v>>(shift or 32);compare=None
        elif h & 0xff00==0x4600:
            r[(h&7)|((h>>4)&8)]=r[(h>>3)&15]
        elif h & 0xf800==0x4800:
            r[(h>>8)&7]=LITERALS[((at+4)&~3)+(h&255)*4]
        elif h & 0xf800 in (0x8800,0x6800):
            width=2 if h&0xf800==0x8800 else 4
            addr=(r[(h>>3)&7]+((h>>6)&31)*width)&MASK
            s.need(addr%width==0 and addr+width-1<=MASK and all(addr+j in mem for j in range(width)),'未提供/非整列RAM読取')
            v=int.from_bytes(bytes(mem[addr+j] for j in range(width)),'little');r[h&7]=v
            reads.append(dict(site=at,address=addr,size=width,value=v))
        elif h & 0xf800==0x2800:compare=(r[(h>>8)&7],h&255)
        elif h & 0xffc0==0x4280:compare=(r[h&7],r[(h>>3)&7])
        elif h & 0xf000==0xd000:
            s.need(compare is not None,'比較flags不明');left,right=compare;cond=(h>>8)&15
            s.need(cond in (0,2),'未知条件');taken=left==right if cond==0 else left>=right
            branches.append((at,taken))
            offset=h&255;dest=at+4+2*(offset-256 if offset&128 else offset)
            s.need(dest==TAIL&~1,'branch差分')
            if taken:pc=dest
        elif h & 0xf800==0x1800:
            s.need(h&0x200==0,'未対応SUB');rhs=(h>>6)&7 if h&0x400 else r[(h>>6)&7]
            r[h&7]=(r[(h>>3)&7]+rhs)&MASK;compare=None
        elif h & 0xffc0==0x4000:r[h&7]&=r[(h>>3)&7];compare=None
        else:raise ValueError('未知命令')
    return {'boundary':pc|1,'registers':r,'local_sp_delta':r[13]-sp,'coverage':coverage,
            'branches':branches,'reads':reads,'writes':writes,'memory':mem,'boundary_executed':False}


@lru_cache(maxsize=1)
def sweep():
    values=(0,1,2,32767,32768,65534,65535);coverage=set();branches=set();cases=0
    for count,limit,index,capacity in product(values,repeat=4):
        r=execute(0,0,0,snapshot(count,limit,index,capacity));expected=CONT if 0<count<limit and index<capacity else TAIL
        s.need(r['boundary']==expected and r['local_sp_delta']==-20 and len(r['writes'])==5,'gate/frame差分')
        cases+=1;coverage.update(r['coverage']);branches.update(r['branches'])
    for key in range(65536):
        mode=(key%256)|0xffffff00;value=(65535-key)|0xffff0000
        r=execute(mode,key|0xffff0000,value,snapshot(record=key));regs=r['registers']
        s.need(r['boundary']==CONT and regs[0]==key&0x8000 and regs[1]==key&0x7fff
               and regs[2]==0x02010000 and regs[3]==key and regs[7]==key%256 and regs[12]==65535-key,'正規化/継続契約差分')
    s.need(coverage==set(range(START,START+64,2)) and branches=={(START+o,t) for o in (22,30,42) for t in (False,True)},'CFG未被覆')
    return {'gate_boundary_cases':cases,'normalization_cases':65536,'covered_instruction_count':len(coverage),
            'conditional_outcomes':len(branches),'new_emulator_processes':0}


def alias_diagnostic():
    mem=snapshot(index=0,capacity=2)
    baseline=execute(0,1,2,mem);alias=execute(0,1,2,mem,sp=COUNTER+2,lr=0x08101235)
    s.need(baseline['boundary']==CONT and alias['boundary']==TAIL,'alias反例差分')
    return {'entry_sp':COUNTER+2,'saved_lr_address':COUNTER-2,'original_index':0,'index_after_push':0x0810,
        'baseline_boundary':CONT,'alias_boundary':TAIL,'observed':False,'stack_and_global_non_alias_required':True}


def analyze(prior,out):
    a=program(prior)
    return {'classification':'EXTERNAL3_PREFIX_GATES_AND_CONTINUATION_ABI_NOT_FULL_RETURN',
        'candidate':copy.deepcopy(s.CANDIDATE),'instructions_verified':32,'instruction_bytes_verified':64,
        'diagnostic_cases':copy.deepcopy(sweep()),'local_sp_delta':-20,'frame_bytes_live':20,
        'saved_register_order':[4,5,6,7,14],'local_explicit_nonstack_stores':0,'external_calls':0,
        'continuation_condition':'0 < loaded_u16_count < loaded_u16_limit and loaded_u16_index < loaded_u16_capacity',
        'continuation_contract':{'target':CONT,'r0':'loaded_record_halfword & 0x8000','r1':'input_r1 & 0x7fff',
            'r2':'(loaded_base_word + 4 * loaded_u16_index) mod 2^32','r3':'loaded_record_halfword',
            'r4':'loaded_base_word','r5':BASE_PTR,'r6':COUNTER,'r7':'input_r0 & 0xff','r12':'input_r2 & 0xffff',
            'frame_bytes_live':20},
        'early_exit_target':TAIL,'early_exit_is_return_proven':False,'return_value_proven':False,
        'hypothetical_stack_overwrites_counter':alias_diagnostic(),
        'proof_assumptions_ja':['読取りsnapshotのRAM範囲/整列が有効で通常memoryとして振る舞う。',
            '継続式のloaded値はPUSH後の読取結果。entry時と同値を主張するにはstack/入力領域非aliasが必要。',
            '継続/末尾は未読。引数の意味や全体帰還・副作用を推測しない。'],
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[CONT,TAIL],'unresolved_indirect_edges':a['unresolved_indirect_edges'],
        'prior_external_indirect_edges_preserved':a['prior_external_indirect_edges_preserved'],
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_graph_decodes':0,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return ('external3保存前半32命令/64byteの3gate・正規化引数・20byte PUSH frameを検証。'
        '2401境界組合せと65536正規化入力で全命令/分岐両側を被覆。stackがcounterへaliasすると分岐が変わる仮想反例を保存。'
        '未読継続/末尾は未実行、ROM復元/native/既読ABI再実行0。',
        '次は未読継続0x08113939の1根だけを限定採取し、保存前半の境界契約を再利用する。'
        '未読末尾0x08113961・旧18owner・外側帰還/非alias・Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__=='__main__':
    sys.modules.setdefault('pr16_ring_external3_abi',sys.modules[__name__])
    s.run(sys.modules[__name__])
