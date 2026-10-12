#!/usr/bin/env python3
"""保存byteのrecord初期化契約。呼出元の割当と実到達・同時実行は証明しない。"""
from __future__ import annotations
import copy
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '5a3a79347acd235250cd389a6d79b650902f93f6'
SLUG = 'pr16-ring-record-init'
TASK = 'PR-P08-7-RING-RECORD-INIT'
TITLE = '保存byteのrecord初期化・容量差と制御域alias候補を検証'
SELF = 'scripts/pr16_ring_record_init.py'
TEST = 'tests/test_pr16_ring_record_init.py'
WORKFLOW = '.github/workflows/pr16-ring-record-init.yml'
PRIOR = 'content/modernization/pr16_ring_selector_owners.json'
REPORT = 'content/modernization/pr16_ring_record_init.json'
KEY = 'ring_record_init'
MIN_TESTS = 20
EXTRA_CODE = ()
SOURCES = ()
NO_REPEAT = ('保存0x08113984初期化の局所Thumb契約・容量差・別callsiteの制御域alias候補は検証済み。'
             '候補再復元/同一初期化ABI/BP/nativeを再実行せず、実callerのpointer/size/limitと'
             '0x09126CB4/0x09127060/0x09099E16の実作用・実到達条件を次に照合する。')
ENTRY, END = 0x08113984, 0x081139DC
CODE = bytes.fromhex('30b500061204030eff2424060019000e012805d90149002008701ae0d85e00030d4d29600d49900c08800d4900200880022b0ed100220b4c2088824209da0a4803682968900040180360013220888242f7db30bc01bc00472c2000033020000396af0302dc5e00033c6b4108')
SELECTOR, RECORD, CAPACITY, INDEX, LIMIT = 0x03005ED8, 0x0300202C, 0x03002030, 0x0203AF96, 0x03005EDC
TEMPLATE = 0x08416B3C
SP, LR = 0x03007000, 0x08012345
MASK = 0xffffffff


def uint(value, bits=32):
    s.need(type(value) is int and 0 <= value < 1 << bits, '整数の型/範囲')
    return value


def overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def contract(state, size, limit):
    """独立した仕様側。zero-fillでなく未採取template wordの反復である。"""
    state, size, limit = uint(state) & 255, uint(size) & 65535, uint(limit, 16)
    valid = state in (1, 2)
    return {'normalized_state': state, 'normalized_size': size, 'valid': valid,
            'registered_capacity': size // 4 if valid else None,
            'initialized_words': limit if state == 2 else 0,
            'required_initialization_bytes': 4 * limit if state == 2 else 0,
            'initialization_exceeds_declared_size': state == 2 and 4*limit > size,
            'selector_written': 0 if not valid else None,
            'allocates_storage': False, 'frame_bytes': 12}


class Memory:
    """既知・供給済みbyteだけ。実GBA mapping/未整列アクセスはモデル化しない。"""
    def __init__(self):
        self.data, self.writes = {}, []
    def seed(self, at, data):
        for n, byte in enumerate(data): self.data[at+n] = byte
    def read(self, at, width):
        s.need(at % width == 0 and all(at+i in self.data for i in range(width)), '未供給/未整列read')
        return sum(self.data[at+i] << (8*i) for i in range(width))
    def write(self, at, width, value):
        s.need(at % width == 0 and all(at+i in self.data for i in range(width)), '割当外/未整列write')
        value &= (1 << (width*8))-1
        self.writes.append({'address': at, 'width': width, 'value': value})
        self.seed(at, value.to_bytes(width, 'little'))


def execute(state, pointer, size, limit, *, allocated_bytes=0, selector=7,
            template=0xA1B2C3D4, max_steps=700000):
    """限定Thumb v4T実行。与えた非alias領域での条件付き結果でありnativeではない。"""
    for value in (state,pointer,size,template): uint(value)
    uint(limit,16); uint(selector,8); uint(allocated_bytes)
    s.need(allocated_bytes <= 262140 and 0 < max_steps <= 700000, '実行資源上限')
    s.need(pointer % 4 == 0, 'buffer整列')
    if allocated_bytes:
        region = (pointer, pointer+allocated_bytes)
        s.need(any(lo <= region[0] <= region[1] <= hi for lo,hi in
                   ((0x02000000,0x02040000),(0x03000000,0x03008000))), 'canonical RAM範囲')
        controls = [(SELECTOR,SELECTOR+1),(RECORD,RECORD+4),(CAPACITY,CAPACITY+2),
                    (INDEX,INDEX+2),(LIMIT,LIMIT+2),(SP-12,SP)]
        s.need(not any(overlap(region,c) for c in controls), '供給領域と制御域/frameがalias')
    mem = Memory();mem.seed(ENTRY,CODE)
    for at,width,val in ((SELECTOR,1,selector),(RECORD,4,0x02008000),
                         (CAPACITY,2,123),(INDEX,2,17),(LIMIT,2,limit),(TEMPLATE,4,template)):
        mem.seed(at,val.to_bytes(width,'little'))
    mem.seed(SP-12,b'\x00'*12);mem.seed(pointer,b'\xCC'*allocated_bytes)
    regs=[0]*16;regs[:3]=[state,pointer,size];regs[4:6]=[0x12345678,0x89abcdef]
    regs[13:15]=[SP,LR];pc=ENTRY; steps=0; visited=set(); flags=(False,False,False,False)
    def cmp(a,b):
        result=(a-b)&MASK
        return bool(result&0x80000000),result==0,a>=b,bool(((a^b)&(a^result))&0x80000000)
    while steps < max_steps:
        s.need(ENTRY <= pc < END and pc not in (0x081139A0,0x081139A2), 'code外/文字列poolへの分岐')
        visited.add(pc); half=mem.read(pc,2);steps+=1; nxt=pc+2
        if half & 0xfe00 == 0xb400:
            ids=[i for i in range(8) if half & (1<<i)] + ([14] if half&256 else [])
            regs[13]-=4*len(ids)
            for i,reg in enumerate(ids):mem.write(regs[13]+4*i,4,regs[reg])
        elif half & 0xfe00 == 0xbc00:
            s.need(not half&256, 'POP pcは範囲外')
            ids=[i for i in range(8) if half&(1<<i)]
            for i,reg in enumerate(ids):regs[reg]=mem.read(regs[13]+4*i,4)
            regs[13]+=4*len(ids)
        elif half & 0xff87 == 0x4700:
            target=regs[(half>>3)&15]
            s.need(target==LR, '保存LRの帰還不一致')
            break
        elif half & 0xf800 in (0x0000,0x0800):
            dest,src,shift=half&7,(half>>3)&7,(half>>6)&31
            regs[dest]=(regs[src]<<shift)&MASK if half&0xf800==0 else regs[src]>>(shift or 32)
        elif half & 0xf800 == 0x1800:
            s.need(not half&0x0600, '対象外加減算')
            regs[half&7]=(regs[(half>>3)&7]+regs[(half>>6)&7])&MASK
        elif half & 0xf800 == 0x2000:
            regs[(half>>8)&7]=half&255
        elif half & 0xf800 == 0x2800:
            flags=cmp(regs[(half>>8)&7],half&255)
        elif half & 0xf800 == 0x3000:
            reg=(half>>8)&7;regs[reg]=(regs[reg]+(half&255))&MASK
        elif half & 0xffc0 == 0x4280:
            flags=cmp(regs[half&7],regs[(half>>3)&7])
        elif half & 0xf800 == 0x4800:
            regs[(half>>8)&7]=mem.read(((pc+4)&~3)+4*(half&255),4)
        elif half & 0xf800 in (0x6000,0x6800,0x7000,0x8000,0x8800):
            op=half&0xf800;width=1 if op==0x7000 else (2 if op in (0x8000,0x8800) else 4)
            reg=half&7;at=(regs[(half>>3)&7]+((half>>6)&31)*width)&MASK
            if op in (0x6800,0x8800):regs[reg]=mem.read(at,width)
            else:mem.write(at,width,regs[reg])
        elif half & 0xf000 == 0xd000:
            cond=(half>>8)&15;n,z,c,v=flags
            choices={1:not z,9:not c or z,10:n==v,11:n!=v}
            s.need(cond in choices, '対象外条件分岐')
            if choices[cond]:nxt=pc+4+2*((half&255)- (256 if half&128 else 0))
        elif half & 0xf800 == 0xe000:
            delta=half&2047;nxt=pc+4+2*(delta-(2048 if delta&1024 else 0))
        else:
            raise ValueError('対象外Thumb opcode')
        pc=nxt
    else:raise ValueError('step上限')
    s.need(regs[13]==SP and regs[4:6]==[0x12345678,0x89abcdef], '局所保存register不一致')
    return {'r0':regs[0], 'sp':regs[13], 'steps':steps,'visited':sorted(visited),
            'selector':mem.read(SELECTOR,1),'record_base':mem.read(RECORD,4),
            'capacity':mem.read(CAPACITY,2),'index':mem.read(INDEX,2),
            'limit':mem.read(LIMIT,2),'writes':mem.writes,
            'buffer_hex':bytes(mem.data[pointer+i] for i in range(allocated_bytes)).hex()}


def saved_bytes(prior, start, end):
    memory={}
    for w in prior['analysis']['new_windows']:
        raw=bytes.fromhex(w['hex']);s.need(len(raw)==w['end']-w['start'] and s.identity(raw)==w['identity'], 'window identity不一致')
        for at,byte in enumerate(raw,w['start']):
            s.need(at not in memory or memory[at]==byte, 'window矛盾')
            memory[at]=byte
    s.need(all(i in memory for i in range(start,end)), '未採取byte')
    return bytes(memory[i] for i in range(start,end))


def aliases(prior):
    """callee効果を仮定せず、literal/BL引数と後続storeの条件付きaliasだけを抽出。"""
    output=[]
    for start,literal,expected in (
        (0x09127110,0x09127138,'094d0a220021280072f77dfe01236b70ab700f332b71'),
        (0x09127160,0x0912718C,'0a4d0a220021280072f755fe01236b70ab700f332b71')):
        raw=saved_bytes(prior,start,start+22)
        s.need(raw.hex()==expected, 'alias候補byte差分')
        value=struct.unpack('<I',saved_bytes(prior,literal,literal+4))[0]
        half=struct.unpack_from('<H',raw)[0]
        s.need(half&0xf800==0x4800 and ((start+4)&~3)+4*(half&255)==literal and value==SELECTOR,'literal候補差分')
        hi,lo=struct.unpack_from('<HH',raw,8)
        s.need(hi&0xf800==0xf000 and lo&0xf800==0xf800,'Thumb BL不一致')
        displacement=(hi&2047)*4096+(lo&2047)*2
        if hi&1024:displacement-=1<<23
        callee=start+8+4+displacement
        s.need(callee==0x09099E16,'callee差分')
        output.append({'start':start,'hex':raw.hex(),'literal_address':literal,'pointer':value,
            'external_callee':callee,'arguments_before_call':{'r0':value,'r1':0,'r2':10},
            'callee_effect_proven':False,'r5_preservation_proven':False,
            'post_call_stores_if_r5_preserved':[{'address':value+1,'width':1,'value':1},
                {'address':value+2,'width':1,'value':1},{'address':value+4,'width':1,'value':16}],
            'conditional_limit_low_byte_alias':True,'runtime_reachable':False})
    return output


def analyze(prior,out):
    a=prior['analysis'];s.need(a['candidate']==s.CANDIDATE and a['new_emulator_processes']==0,'前工程identity')
    s.need(saved_bytes(prior,ENTRY,ENTRY+len(CODE))==CODE,'初期化保存byte不一致')
    cases=[]
    for state,size,limit in ((0,12,3),(1,12,3),(2,12,3),(2,4,3),(2,12,0)):
        c=contract(state,size,limit);r=execute(state,0x02010000,size,limit,allocated_bytes=max(size,4*limit))
        if c['valid']:
            s.need((r['capacity'],r['index'],r['record_base'])==(size//4,0,0x02010000),'登録契約差分')
        s.need(r['r0']==LR,'return値差分')
        cases.append({'inputs':{'state':state,'size':size,'limit':limit},'contract':c,'execution':r,
                      'classification':'HOST_MODEL_ONLY_NOT_NATIVE'})
    result={'classification':'SAVED_LOCAL_INITIALIZER_CONTRACT_NOT_ALLOCATION_OR_NATIVE',
        'candidate':copy.deepcopy(s.CANDIDATE),'entry':ENTRY,'end':END,'saved_code':s.identity(CODE),
        'abi':{'state':'r0 low8','records':'r1 unchanged pointer','size':'r2 low16',
               'capacity':'floor((r2 & 65535)/4)','frame_bytes':12,'r4_r5_preserved_conditionally':True,
               'r0_at_return':'saved LR, not allocation pointer','external_calls_in_local_initializer':0},
        'cases':cases,'independent_extent_condition_ja':'state2はcapacityでなくLIMITのword数を初期化する。'
            'caller実所有範囲はmax(4*capacity,4*LIMIT)を別途確認し、制御域/stackとの非aliasを確認する。'
            'bufferの割当/解放はこの関数にない。mode1/2有効時にselectorを直接設定しない。',
        'unread_template_address':TEMPLATE,'template_value_observed':False,
        'foreign_control_alias_candidates':aliases(prior),
        'old_unread_targets':copy.deepcopy(a['old_unread_targets']),
        'old_frontier_removed':False,'allocated_storage_extent_proven':False,
        'selector1_runtime_observed':False,'selector2_runtime_observed':False,
        'active_record_prefix_observed':False,'normal_mapping_proven':False,'synchrony_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'candidate_reconstructions':0}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    stop=('保存0x08113984の局所初期化を命令実行で検証。caller pointerを登録しcapacity=floor(u16 size/4)、'
          'mode2の初期化word数は別global LIMIT。局所frame12byte、allocatorなし。'
          '0x09127110/7160は同じselector領域を外部calleeへ渡し、r5保存条件下でLIMIT下位byteへ16を書込む候補。'
          '実到達/外部callee作用/割当所有は未証明。候補復元0/native0/旧ABI・受入BP再実行0。')
    next_step=('保存initializerとalias候補を再検証せず、0x08113984実callerのpointer/size/LIMITと'
               '0x09126CB4/0x09127060/0x09099E16の役割・実到達を絞る。'
               '有効初期化はselectorを設定しないため通常story経路のselector1/2を別に追う。'
               '同一アドレスだけでRTC衝突/既存コードの不存在と断定しない。旧18owner、Ring取得・装備実戦・保存、'
               'policy/Circus/P08は未完。')
    return stop,next_step

if __name__=='__main__':
    s.need(sys.argv[1:]==['run'],'runだけを許可');s.run(sys.modules[__name__])
