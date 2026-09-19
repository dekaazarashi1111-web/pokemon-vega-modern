#!/usr/bin/env python3
"""保存byteだけでdelegateの限定契約を検証。hardware/story/native受入とは区別。"""
from __future__ import annotations
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = 'd059ce8696dce5f220790721eb495c7ae38de8cf'
SLUG = 'pr16-ring-delegate-contracts'
TASK = 'PR-P08-7-RING-DELEGATE-CONTRACTS'
TITLE = '保存7delegateの書込範囲・帰還・未読境界を検証'
SELF = 'scripts/pr16_ring_delegate_contracts.py'
TEST = 'tests/test_pr16_ring_delegate_contracts.py'
WORKFLOW = '.github/workflows/pr16-ring-delegate-contracts.yml'
PRIOR = 'content/modernization/pr16_ring_branch_frontier.json'
REPORT = 'content/modernization/pr16_ring_delegate_contracts.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 36
EXTRA_CODE = ()
SOURCES = ('content/modernization/pr16_ring_record_callers.json',
           'content/modernization/pr16_ring_selector_owners.json',
           'scripts/pr16_ring_record_callers.py', 'scripts/pr16_ring_branch_frontier.py')
NO_REPEAT = ('branch-frontier採取と7delegateの局所契約は保存原本を再利用。'
             'memsetの限定ベクトル、reset、I/O readerの供給bit列モデル、gate、date validatorを通常story/hardware受入へ昇格しない。'
             '0x0912C4A8/0x0912C554/0x09099E04とmonth table/間接callerが次の未読境界。')
MASK = 0xFFFFFFFF
SP, LR, BUFFER = 0x03007000, 0x08012345, 0x02010000
BUSY, DATA, DIRECTION, CONTROL = 0x0203DFD1, 0x080000C4, 0x080000C6, 0x080000C8
FILL, RESET, GATE, READER, TIME_READER, STATUS, VALIDATOR = (0x081C9DF8, 0x0912C5FC, 0x0912C630, 0x0912C664, 0x0912C728, 0x0912C7EC, 0x09126EFC)
# function命令境界をliteral poolと分離する。全byteをanalyzeで保存原本へ照合。
CODE_RANGES = ((FILL,0x081C9E4A), (RESET,0x0912C60A), (GATE,0x0912C644),
               (READER,0x0912C71A), (TIME_READER,0x0912C7E0), (STATUS,0x0912C85E), (VALIDATOR,0x0912705C))
CODES = {
    0x081C9DF8: bytes.fromhex('30b5051c0c1c2b1c032a1cd903202840002818d1291cff20044023022343180403430f2a09d908c108c108c108c1103a0f2af8d801e008c1043a032afbd80b1c01e01c700133101c013a0028f9d1281c30bd'),
    0x0912C5FC: bytes.fromhex('0122034b1a800022024b1a707047c046c8000008d1df0302'),
    0x0912C630: bytes.fromhex('10b5044b1b78012b02d0fff735ff10bd0020fce7d1df0302'),
    0x0912C664: bytes.fromhex('f0b5ce46474680b52b4b98461b788146012b4ed0012307216527012604250524264a138004331380254b19803b000b4133405b0018002343284300041b04000c1b0c10801080108013800139eed205221b4b1a8007234b444f469c4604240526164a0825002314801480148014801480168011884908c9015b080b43013d1b0629061b0e0d0e0029edd13b700137bc45e7d14b4619797f230b4049460b71012313801380434601201d70c0bcb946b046f0bd0020f9e7c046d1df0302c4000008c6000008'),
    0x0912C728: bytes.fromhex('f0b5ce46474680b52b4b9c461b788146012b4fd0012307216727012604250524264a138004331380254b19803b000b4133405b0018002343284300041b04000c1b0c10801080108013800139eed205221b4b1a804b461f1d07234b44984604240526164a0825002314801480148014801480168011884908c9015b080b43013d1b0629061b0e0d0e0029edd13b700137b845e7d14b4619797f230b4049460b71012313801380634601201d70c0bcb946b046f0bd0020f9e7d1df0302c4000008c6000008'),
    0x0912C7EC: bytes.fromhex('30b51c4d2b7885b0012b12d001a8fff755fe00280dd06b46db7a5b060cd42b78012b06d04020fff79ffe002801d0012403e0002005b030bd002401a8fff77eff6b469b7a7f2b05d80123200118430006000eefe72b78012b08d04020fff784fe002803d001342406240eede72007000ee0e7c046d1df0302'),
    0x09126EFC: bytes.fromhex('f8b5c379da09050052015b0601d410231a432b789f2b00d992e00f211940092900d98de01b099e00f618760076186b78af789f2b4ed80f21194009294ad81b099800c3185b005b18181e45d00c2b43dc14009f2f44d98022520022431204ff27140c022847d03e4a013b9b009b58bb4250db2b799f2b55d80f211940092951d81b099a00d3185b005b18182b4adc6b799f2b4fd80f21194009294bd81b099a00d3185b005b183c2b44dcab799f2b0ad80f211940092906d81b099a00d3185b005b183c2b04dd80231b0123431b041c0c2000f8bdff20ff23802414439f2f33d80f2139400929b6d83a099700bf187f007f180228b7d11c21b30709d13000483172f702ff73425e414b1e994131431c318f42aedd80235b0023431b041c0c2b799f2ba9d980239b0023431b041c0c6b799f2bafd98023db0023431b041c0cb4e74023ff261a4372e7c024ff2764001443013b034a9b009b58bb4200db89e7d9e730951609'),
}


def uint(value, bits=32):
    s.need(type(value) is int and 0 <= value < 1 << bits, '整数型/範囲')
    return value


def signed(value):
    return value-(1 << 32) if value & (1 << 31) else value


class VM:
    """当該Thumb-1だけ。未知命令・未供給read・literal実行・外部callを黙認しない。"""
    def __init__(self, codes=None, code_ranges=CODE_RANGES):
        self.mem = {at+i:b for at,raw in (CODES if codes is None else codes).items() for i,b in enumerate(raw)}
        self.code = frozenset(at for lo,hi in code_ranges for at in range(lo,hi))
        self.writable, self.writes, self.reads, self.io_bits = set(), [], [], []
        self.io_index = 0
        self.r = [0x12340000+i for i in range(16)]
        self.r[13:15] = [SP, LR]
        self.flags = (False, False, False, False)
        self.seed(SP-64,bytes(64))
    def seed(self, at, raw):
        s.need(type(raw) is bytes and all(at+i not in self.mem or at+i in self.writable for i in range(len(raw))), 'ROM/fixture上書き')
        for i,b in enumerate(raw): self.mem[at+i]=b; self.writable.add(at+i)
    def read(self, at, width):
        s.need(at % width == 0 and all(at+i in self.mem for i in range(width)), f'未供給/未整列read: {at:08X}/{width}')
        if at == DATA and width == 2:
            s.need(self.io_index < len(self.io_bits), '供給I/O bit不足')
            value = self.io_bits[self.io_index]; self.io_index += 1
        else:
            value = sum(self.mem[at+i] << (8*i) for i in range(width))
        self.reads.append((at,width,value))
        return value
    def write(self, at, width, value):
        s.need(at % width == 0 and all(at+i in self.writable for i in range(width)), '領域外/未整列write')
        value &= (1 << (width*8))-1
        self.writes.append((at,width,value))
        for i in range(width): self.mem[at+i] = (value >> (i*8)) & 255
    def nz(self, value):
        self.flags=(bool(value & (1 << 31)),value==0,self.flags[2],self.flags[3])
    def arithmetic(self, a, b, sub=False, carry=0):
        full = a-b-carry if sub else a+b+carry
        value = full & MASK
        overflow = bool(((a^b) if sub else ~(a^b)) & (a^value) & (1 << 31))
        self.flags=(bool(value & (1 << 31)),value==0,full>=0 if sub else full>MASK,overflow)
        return value
    def shift(self, value, amount, kind):
        c=self.flags[2]
        if amount == 0: result=value
        elif kind == 0:
            result=(value << amount)&MASK if amount < 32 else 0
            c=bool(value & (1 << (32-amount))) if amount <= 32 else False
        elif kind == 1:
            result=value >> amount if amount < 32 else 0
            c=bool(value & (1 << (amount-1))) if amount <= 32 else False
        else:
            result=(signed(value) >> min(amount,32)) & MASK
            c=bool(value & (1 << (min(amount,32)-1)))
        self.flags=(bool(result & (1 << 31)),result==0,c,self.flags[3])
        return result
    def run(self, entry, max_steps=20000):
        uint(entry); s.need(entry % 2 == 0, 'entry整列')
        s.need(type(max_steps) is int and 0 < max_steps <= 20000, 'step上限')
        pc=entry
        for steps in range(1,max_steps+1):
            s.need(pc in self.code and pc+1 in self.code, 'code範囲外/literal実行')
            h=self.read(pc,2); nxt=pc+2
            if h & 0xFE00 in (0xB400,0xBC00):
                push=h & 0xFE00 == 0xB400
                ids=[i for i in range(8) if h & (1 << i)]+([14 if push else 15] if h & 256 else [])
                s.need(ids,'空stack命令')
                if push:
                    self.r[13]-=4*len(ids)
                    for i,reg in enumerate(ids): self.write(self.r[13]+4*i,4,self.r[reg])
                else:
                    for i,reg in enumerate(ids): self.r[reg]=self.read(self.r[13]+4*i,4)
                    self.r[13]+=4*len(ids)
                    if 15 in ids:
                        s.need(self.r[15]==LR,'未知帰還')
                        return {'steps':steps,'returned':True}
            elif h & 0xF800 == 0x4800:
                self.r[(h >> 8)&7]=self.read(((pc+4)&~3)+4*(h&255),4)
            elif h & 0xE000 == 0 and h & 0x1800 != 0x1800:
                kind,amount=(h >> 11)&3,(h >> 6)&31
                self.r[h&7]=self.shift(self.r[(h >> 3)&7],amount or (32 if kind else 0),kind)
            elif h & 0xF800 == 0x1800:
                operand=(h >> 6)&7
                b=operand if h & 0x400 else self.r[operand]
                self.r[h&7]=self.arithmetic(self.r[(h >> 3)&7],b,bool(h&0x200))
            elif h & 0xE000 == 0x2000:
                op,d,imm=(h >> 11)&3,(h >> 8)&7,h&255
                if op==0: self.r[d]=imm; self.nz(imm)
                elif op==1: self.arithmetic(self.r[d],imm,True)
                else: self.r[d]=self.arithmetic(self.r[d],imm,op==3)
            elif h & 0xFC00 == 0x4000:
                op,d,b=(h >> 6)&15,h&7,self.r[(h >> 3)&7]
                if op==0: self.r[d]&=b; self.nz(self.r[d])
                elif op==12: self.r[d]|=b; self.nz(self.r[d])
                elif op in (2,3,4): self.r[d]=self.shift(self.r[d],b&255,op-2)
                elif op==5: self.r[d]=self.arithmetic(self.r[d],b,carry=int(self.flags[2]))
                elif op==6: self.r[d]=self.arithmetic(self.r[d],b,True,int(not self.flags[2]))
                elif op==8: self.nz(self.r[d]&b)
                elif op==9: self.r[d]=self.arithmetic(0,b,True)
                elif op==10: self.arithmetic(self.r[d],b,True)
                else: raise ValueError('対象外ALU')
            elif h & 0xFC00 == 0x4400:
                op,d,reg=(h >> 8)&3,(h&7)|((h >> 4)&8),(h >> 3)&15
                s.need(d!=15 and reg!=15,'対象外PC操作')
                if op==3:
                    s.need(h&0x87==0 and self.r[reg]==LR,'未知BX/BLX')
                    return {'steps':steps,'returned':True}
                if op==0: self.r[d]=(self.r[d]+self.r[reg])&MASK
                elif op==1: self.arithmetic(self.r[d],self.r[reg],True)
                else: self.r[d]=self.r[reg]
            elif h & 0xF800 in (0x6000,0x6800,0x7000,0x7800,0x8000,0x8800):
                op=h&0xF800; width=1 if op in (0x7000,0x7800) else (2 if op in (0x8000,0x8800) else 4)
                d,at=h&7,(self.r[(h >> 3)&7]+((h >> 6)&31)*width)&MASK
                if op&0x800: self.r[d]=self.read(at,width)
                else: self.write(at,width,self.r[d])
            elif h & 0xFE00 == 0x5800:
                self.r[h&7]=self.read((self.r[(h >> 3)&7]+self.r[(h >> 6)&7])&MASK,4)
            elif h & 0xF800 == 0xC000:
                base=(h >> 8)&7; ids=[i for i in range(8) if h&(1 << i)]
                s.need(ids and base not in ids,'対象外STM')
                for i,reg in enumerate(ids): self.write(self.r[base]+4*i,4,self.r[reg])
                self.r[base]+=4*len(ids)
            elif h & 0xFF00 == 0xB000:
                self.r[13]+=(h&127)*(-4 if h&128 else 4)
            elif h & 0xF800 == 0xA800:
                self.r[(h >> 8)&7]=(self.r[13]+4*(h&255))&MASK
            elif h & 0xF000 == 0xD000:
                n,z,c,v=self.flags; cond=(h >> 8)&15
                conditions=(z,not z,c,not c,n,not n,v,not v,c and not z,not c or z,n==v,n!=v,not z and n==v,z or n!=v)
                s.need(cond<14,'SWI/undefined')
                if conditions[cond]: nxt=pc+4+2*((h&255)-(256 if h&128 else 0))
            elif h & 0xF800 == 0xE000:
                nxt=pc+4+2*((h&2047)-(2048 if h&1024 else 0))
            elif h & 0xF800 == 0xF000:
                s.need(pc+2 in self.code and pc+3 in self.code,'BL境界')
                low=self.read(pc+2,2); s.need(low&0xF800==0xF800,'BLX/不正BL')
                delta=((h&2047) << 12)|((low&2047) << 1)
                if h&1024: delta-=1 << 23
                return {'steps':steps,'returned':False,'unread_call':(pc+4+delta)&MASK,'site':pc,'args':self.r[:4]}
            else: raise ValueError(f'対象外Thumb: {pc:08X}/{h:04X}')
            pc=nxt
        raise ValueError('step上限')


def checked_return(vm, entry, before):
    result=vm.run(entry)
    s.need(result.get('returned') and vm.r[4:12]==before and vm.r[13]==SP,'callee保存/帰還差分')
    return result


def fill_case(alignment, count, value):
    uint(alignment,2); uint(count,8); uint(value)
    vm=VM(); vm.seed(BUFFER,b'\xcc'*(count+8)); vm.r[:3]=[BUFFER+alignment,value,count]
    before=vm.r[4:12].copy(); checked_return(vm,FILL,before)
    expected=bytearray(b'\xcc'*(count+8)); expected[alignment:alignment+count]=bytes([value&255])*count
    s.need(bytes(vm.mem[BUFFER+i] for i in range(count+8))==expected and vm.r[0]==BUFFER+alignment,'fill内容/戻値')
    writes=[w for w in vm.writes if not SP-64<=w[0]<SP]
    s.need(sum(w[1] for w in writes)==count and all(BUFFER+alignment<=a and a+n<=BUFFER+alignment+count for a,n,_ in writes),'fill範囲')
    return len(writes)


def base_io(busy):
    uint(busy,8)
    vm=VM(); vm.seed(BUSY,bytes([busy])); vm.seed(DATA,bytes(6)); return vm


def reader_case(entry, busy, payload):
    size=7 if entry==READER else 3
    s.need(entry in (READER,TIME_READER) and type(payload) is bytes and len(payload)==size,'reader入力')
    vm=base_io(busy); vm.seed(BUFFER,b'\xcc'*9); vm.r[0]=BUFFER
    vm.io_bits=[((b >> bit)&1)*2 for b in payload for bit in range(8)]
    checked_return(vm,entry,vm.r[4:12].copy())
    expected=bytearray(b'\xcc'*9)
    if busy!=1:
        offset=0 if entry==READER else 4
        expected[offset:offset+size]=payload; expected[4]&=127
    s.need(bytes(vm.mem[BUFFER+i] for i in range(9))==expected,'reader buffer差分')
    s.need(vm.r[0]==int(busy!=1) and vm.io_index==(8*size if busy!=1 else 0),'reader結果/bit数')
    writes=[w for w in vm.writes if not SP-64<=w[0]<SP]
    if busy==1: s.need(not writes,'busy時書込')
    else:
        command=0x65 if entry==READER else 0x67
        expected_io=[(DATA,2,1),(DATA,2,5),(DIRECTION,2,7)]
        for bit in range(7,-1,-1):
            bitvalue=((command >> bit)&1)*2
            expected_io += [(DATA,2,4|bitvalue)]*3+[(DATA,2,5|bitvalue)]
        expected_io += [(DIRECTION,2,5)]
        expected_io += ([(DATA,2,4)]*5+[(DATA,2,5)])*(size*8)
        expected_io += [(DATA,2,1)]*2
        s.need([w for w in writes if w[0] in (DATA,DIRECTION)]==expected_io,'GPIO write列')
        s.need(vm.mem[BUSY]==0 and all(a in (DATA,DIRECTION,BUSY) or BUFFER<=a<BUFFER+7 for a,_,_ in writes),'reader書込範囲')
    return {'io_reads':vm.io_index,'gpio_writes':sum(a in (DATA,DIRECTION) for a,_,_ in writes)}


def date_case(raw):
    s.need(type(raw) is bytes and len(raw)==8,'date入力')
    vm=VM(); vm.seed(BUFFER,raw); vm.r[0]=BUFFER; before=vm.r[4:12].copy()
    result=vm.run(VALIDATOR)
    s.need(all(SP-64<=a<SP for a,_,_ in vm.writes),'date入力書換')
    if result.get('returned'):
        s.need(vm.r[4:12]==before and vm.r[13]==SP,'date ABI差分')
        result['value']=vm.r[0]
    return result


def expected_february(raw):
    # 非閏年の二月に限定。実コードのday=0/hour=24/minute=60/second=60許容を隠さない。
    def bcd(b): return 10*(b >> 4)+(b&15) if b<=0x99 and b&15<=9 else None
    y,month,day,weekday,hour,minute,second,status=raw
    year=bcd(y); s.need(month==2 and (year is None or year%4!=0),'非閏年二月のみ')
    value=((status >> 7)&1)*32+(0 if status&64 else 16)
    if year is None: value|=64
    if bcd(day) is None or bcd(day)>28: value|=256
    for field,limit,bit in ((hour,24,512),(minute,60,1024),(second,60,2048)):
        if bcd(field) is None or bcd(field)>limit: value|=bit
    return value


def check_contracts():
    fill_count=0
    for alignment in range(4):
        for count in range(65):
            for value in (0,1,127,128,255,0x123456AB):
                fill_case(alignment,count,value); fill_count+=1
    for value in range(256):
        for alignment in range(4):
            fill_case(alignment,17,value); fill_count+=1
    reset_count=gate_count=reader_count=status_count=date_count=0
    for busy in range(256):
        vm=base_io(busy); before=vm.r[:12].copy(); checked_return(vm,RESET,vm.r[4:12].copy())
        s.need(vm.writes==[(CONTROL,2,1),(BUSY,1,0)] and vm.r[:2]==before[:2],'reset契約')
        reset_count+=1
        for entry in (GATE,STATUS):
            vm=base_io(busy); vm.r[0]=BUFFER; r=vm.run(entry)
            s.need(all(SP-64<=a<SP for a,_,_ in vm.writes),'gate/status外部前書込')
            if busy==1:
                s.need(r.get('returned') and vm.r[0]==0 and vm.r[13]==SP,'gate/status busy帰還')
            else:
                s.need(r.get('unread_call')==0x0912C4A8,'gate/status外部境界')
                s.need(r['args'][0]==(BUFFER if entry==GATE else SP-28),'外部引数')
            if entry==GATE: gate_count+=1
            else: status_count+=1
        for entry,n in ((READER,7),(TIME_READER,3)):
            reader_case(entry,busy,bytes(range(n))); reader_count+=1
    for entry,n in ((READER,7),(TIME_READER,3)):
        for pos in range(n):
            for value in range(256):
                payload=bytearray(n); payload[pos]=value
                reader_case(entry,0,bytes(payload)); reader_count+=1
    for pos in (0,2,3,4,5,6,7):
        for value in range(256):
            raw=bytearray([1,2,15,3,12,30,30,64]); raw[pos]=value
            if pos==0 and value<=0x99 and value&15<=9 and (10*(value >> 4)+(value&15))%4==0:
                continue
            r=date_case(bytes(raw))
            s.need(r.get('returned') and r['value']==expected_february(raw),'date限定モデル差分')
            date_count+=1
    leap=date_case(bytes([4,2,0x29,0,0,0,0,64]))
    s.need(leap.get('unread_call')==0x09099E04 and leap['args'][:2]==[4,100],'閏年外部境界')
    try: date_case(bytes([1,1,1,0,0,0,0,64]))
    except ValueError as error: s.need('09169530/4' in str(error),'month table境界差分')
    else: raise ValueError('未読month tableを黙認')
    return {'fill_vectors':fill_count,'reset_vectors':reset_count,'gate_vectors':gate_count,
            'status_prefix_vectors':status_count,'reader_vectors':reader_count,'date_vectors':date_count,
            'leap_year_external':leap}


def analyze(prior,out):
    import pr16_ring_record_callers as capture
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    owners=s.load(capture.OWNERS); callers=s.load(frontier.CALLERS)
    for report in (owners,callers): saved.bindings_fresh(s.ROOT,report['source_bindings'])
    memory=capture.saved_memory(owners)
    frontier.add_windows(memory,callers['analysis']['new_windows'])
    frontier.add_windows(memory,prior['analysis']['new_windows'])
    for at,raw in CODES.items():
        s.need(all(memory.get(at+i)==b for i,b in enumerate(raw)),'delegate fixture/保存byte差分')
    counts=check_contracts()
    result={'classification':'SAVED_DELEGATE_BOUNDED_CONTRACTS_NOT_HARDWARE_OR_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'counts':counts,
        'code_ranges':[list(r) for r in CODE_RANGES],
        'byte_bindings':{f'0x{at:08X}':s.identity(raw) for at,raw in CODES.items()},
        'fill':{'entry':FILL,'tested_lengths':[0,64],'additional_length':17,'alignments':[0,1,2,3],
                'effect':'r0 buffer gets r2 copies of low byte of r1; r0 returns original pointer',
                'r4_r11_sp_preserved_for_tested_vectors':True,'all_uint32_lengths_exhausted':False,
                'actual_initializer_pointer_size_limit_proven':False},
        'reset':{'entry':RESET,'writes':[[CONTROL,2,1],[BUSY,1,0]],'r0_r1_preserved':True},
        'readers':{'entries':[READER,TIME_READER],'commands':[101,103],'buffer_byte_ranges':[[0,7],[4,7]],
                   'hour_bit7_cleared':True,'buffer_byte7_written':False,'busy_one_no_io_or_buffer_write':True,
                   'supplied_io_stream_only':True,'physical_hardware_behavior_proven':False},
        'gated_wrappers':{'entries':[GATE,STATUS],'busy_one_returns_zero':True,
                         'first_unread_delegate':0x0912C4A8,'status_other_paths_proven':False},
        'date_validator':{'entry':VALIDATOR,'scope':'February one-field sweeps; 25 valid year bytes divisible by four excluded before execution',
                          'day_zero_accepted_by_local_code':True,'hour24_minute60_second60_accepted_by_local_code':True,
                          'weekday_byte_unchecked':True,'input_bytes_written':0,
                          'month_table':0x09169530,'month_table_extent_required':[0x09169530,0x09169560],
                          'all_months_or_leap_years_proven':False},
        'unread_external_targets':[0x0912C4A9,0x0912C555,0x09099E05],
        'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_callers_resolved':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'selector1_runtime_observed':False,'selector2_runtime_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0,
        'boundary_ja':'限定Thumbモデルと供給I/O bit列。実hardware・caller到達・通常story受入ではない。旧18ownerも残る。'}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    c=result['counts']
    return (f'保存7delegateを限定検証: fill{c["fill_vectors"]}、reset/gate/status各256、reader{c["reader_vectors"]}、'
            f'date{c["date_vectors"]}ベクトル。GPIO書込/buffer範囲を固定。day0/hour24/minute60/second60許容は実装事実として保持。'
            'ROM復元/変更/native/BP再実行0。通常Ring取得は未受入。',
            '未読0x0912C4A9/0x0912C555/0x09099E05とmonth table0x09169530..0x09169560を保存byte優先で検証する。'
            'initializerのcomputed/RAM/mirrored-PC callerとpointer/size/LIMIT、旧18owner、Ring通常取得/装備実戦/保存は未完。'
            '既読7delegate・前回分岐走査・BP受入を再実行しない。')


if __name__=='__main__':
    s.need(sys.argv[1:]==['run'],'runだけを許可')
    s.run(sys.modules[__name__])
