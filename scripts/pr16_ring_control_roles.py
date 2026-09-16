#!/usr/bin/env python3
"""保存済みBCD変換・I/O wrapper・tail veneerの局所契約。通常story到達ではない。"""
from __future__ import annotations
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_record_callers as capture

BASE = '781fd40d23c75bcc11f9d51320d90f5ebcee7e0f'
SLUG = 'pr16-ring-control-roles'
TASK = 'PR-P08-7-RING-CONTROL-ROLES'
TITLE = '保存BCD変換とI/O wrapper・外部veneerの契約を区別'
SELF = 'scripts/pr16_ring_control_roles.py'
TEST = 'tests/test_pr16_ring_control_roles.py'
WORKFLOW = '.github/workflows/pr16-ring-control-roles.yml'
PRIOR = 'content/modernization/pr16_ring_record_callers.json'
REPORT = 'content/modernization/pr16_ring_control_roles.json'
KEY = 'ring_control_roles'
MIN_TESTS = 24
EXTRA_CODE = ()
SOURCES = (capture.SELF, capture.OWNERS)
NO_REPEAT = ('保存BCD変換2048vector・I/O wrapper条件モデル・tick/init prefix・veneerは完了。'
             '0x09099E16は0x081C9DF9へのtail veneerで、memset効果/帰還保存を証明していない。'
             '同じ局所ABI/byte採取を繰り返さず、保存された未読delegateと実到達だけを進める。')
SELECTOR, LIMIT, CONVERTED = 0x03005ED8, 0x03005EDC, 0x03005EF0
HOUR_FLAG, COUNTER = 0x0203DFC8, 0x03005EF9
STATUS, SAVED_IO, RAW_STATUS, IO = 0x0203DFD2, 0x0203DFD4, 0x0203DFD6, 0x04000208
SP, LR, MASK = 0x03007000, 0x08012345, 0xffffffff
BCD, READER, TICK, INIT, VENEER = 0x09126CB4, 0x09127060, 0x091270E4, 0x09127148, 0x09099E16
EXTERNALS = (0x0912C5FC, 0x0912C7EC, 0x0912C630, 0x0912C664, 0x09126EFC)
# 原candidateの限定保存byte。analyzeで入力原本と全byte照合する。
CODES = {
    0x09126CB4: bytes.fromhex('454a137870b59f2b00d983e00f201840092800d97ee01b099900c918fa23db009c464900091861443c4b198050789f2800d96de00f240440092c69d8000981000918490009190906090ed97090789f285cd80f240440092c58d8000981000918490009190906090e1971d0789f284bd80f240440092c47d8000981000918490009190906090e597111799f2939d80f240c40092c35d8090988004018400000190406240e9c7155799f2d28d80f262e40092e24d82d09a9004919490089190906090ed97191799f2917d80f250d40092d13d809098a005218520052191206120e1a720f4a1278002a03d00b2802d90c3c9c7170bd0c349c71fbe7ff22f0e7ff21dfe7ff24ff20cde7ff21bce7ff21abe7ff219ae7034987e7d85e0003f05e0003c8df0302cf080000'),
    0x09127060: bytes.fromhex('f0b5c64600261a4f00b51a4c3e801a4d23882b80268005f0c1fa05f0b7fb174b18702b8823800f2319000122014001291ad183429b415b425b003b8023882b800f4b98461800268005f0c2fa2b882380238840462b80268005f0d4fa2b8840462380fff71bff02003a8080bcb846f0bdd2df030208020004d4df0302d6df0302d85e0003'),
    0x091270E4: bytes.fromhex('70b5124c2378002b08d03b2b04d801331b061b0e237070bd0023fbe7fff7aeff0b4b1a88ff231b011a420ad0'),
    0x09127130: bytes.fromhex('f95e0003d2df0302d85e0003'),
    0x09127148: bytes.fromhex('002370b50d4c2370fff786ff'),
    0x09127184: bytes.fromhex('f95e0003'),
    0x09099E16: bytes.fromhex('134b1847'),
    0x09099E64: bytes.fromhex('f99d1c08'),
}


def need_uint(value, bits=32):
    s.need(type(value) is int and 0 <= value < 1 << bits, '整数型/範囲')
    return value


class VM:
    """対象で使うThumb-1のみ。未知命令/未供給read/領域外writeは停止。"""
    def __init__(self):
        self.mem, self.writable, self.writes, self.calls = {}, set(), [], []
        for at, raw in CODES.items():
            for i, b in enumerate(raw): self.mem[at+i] = b
        self.code = frozenset(self.mem)
        self.r = [0x12340000+i for i in range(16)]
        self.r[13:15] = [SP, LR]
        self.flags = (False, False, False, False)
        self.seed(SP-64, bytes(64))
    def seed(self, at, raw):
        s.need(type(raw) is bytes and not any(at+i in self.mem and at+i not in self.writable for i in range(len(raw))), 'ROM上書き')
        for i,b in enumerate(raw): self.mem[at+i] = b; self.writable.add(at+i)
    def read(self, at, width):
        s.need(at % width == 0 and all(at+i in self.mem for i in range(width)), '未供給/未整列read')
        return sum(self.mem[at+i] << (i*8) for i in range(width))
    def write(self, at, width, value):
        s.need(at % width == 0 and all(at+i in self.writable for i in range(width)), '領域外/未整列write')
        value &= (1 << (width*8))-1
        self.writes.append({'address': at, 'width': width, 'value': value})
        for i in range(width): self.mem[at+i] = (value >> (i*8)) & 255
    def nz(self, value):
        self.flags = (bool(value & 0x80000000), value == 0, self.flags[2], self.flags[3])
    def arithmetic(self, a, b, sub=False, borrow=0):
        full = a-b-borrow if sub else a+b
        value = full & MASK
        carry = full >= 0 if sub else full > MASK
        overflow = bool(((a^b) if sub else ~(a^b)) & (a^value) & 0x80000000)
        self.flags = (bool(value & 0x80000000), value == 0, carry, overflow)
        return value
    def run(self, entry, *, returns=None, stop_call=False, max_steps=500):
        s.need(type(max_steps) is int and 0 < max_steps <= 500, 'step上限の型/範囲')
        need_uint(entry)
        pc = entry
        for steps in range(1, max_steps+1):
            s.need(pc in self.code and pc+1 in self.code, 'code範囲外への分岐')
            h = self.read(pc, 2); nxt = pc+2
            if h & 0xfe00 in (0xb400, 0xbc00):
                push = h & 0xfe00 == 0xb400
                ids = [i for i in range(8) if h & (1 << i)] + ([14 if push else 15] if h & 256 else [])
                s.need(ids, '空stack命令')
                if push:
                    self.r[13] -= 4*len(ids)
                    for i, reg in enumerate(ids): self.write(self.r[13]+4*i, 4, self.r[reg])
                else:
                    for i, reg in enumerate(ids): self.r[reg] = self.read(self.r[13]+4*i, 4)
                    self.r[13] += 4*len(ids)
                    if 15 in ids:
                        s.need(self.r[15] == LR, '未知帰還')
                        return {'steps': steps, 'return': LR}
            elif h & 0xf800 == 0x4800:
                self.r[(h>>8)&7] = self.read(((pc+4)&~3)+4*(h&255), 4)
            elif h & 0xf800 in (0, 0x0800):
                d, a, sh = h&7, self.r[(h>>3)&7], (h>>6)&31
                if h & 0xf800 == 0:
                    val = (a << sh) & MASK; c = bool(a & (1 << (32-sh))) if sh else self.flags[2]
                else:
                    sh = sh or 32; val = a >> sh; c = bool(a & (1 << (sh-1)))
                self.flags = (bool(val & 0x80000000), val == 0, c, self.flags[3]); self.r[d] = val
            elif h & 0xf800 == 0x1800:
                operand = (h>>6)&7
                b = operand if h & 0x400 else self.r[operand]
                self.r[h&7] = self.arithmetic(self.r[(h>>3)&7], b, bool(h & 0x200))
            elif h & 0xe000 == 0x2000:
                op, d, imm = (h>>11)&3, (h>>8)&7, h&255
                if op == 0: self.r[d] = imm; self.nz(imm)
                elif op == 1: self.arithmetic(self.r[d], imm, True)
                else: self.r[d] = self.arithmetic(self.r[d], imm, op == 3)
            elif h & 0xfc00 == 0x4000:
                op, d, b = (h>>6)&15, h&7, self.r[(h>>3)&7]
                if op == 0: self.r[d] &= b; self.nz(self.r[d])
                elif op == 6: self.r[d] = self.arithmetic(self.r[d], b, True, 0 if self.flags[2] else 1)
                elif op == 8: self.nz(self.r[d] & b)
                elif op == 9: self.r[d] = self.arithmetic(0, b, True)
                elif op == 10: self.arithmetic(self.r[d], b, True)
                else: raise ValueError('対象外ALU命令')
            elif h & 0xfc00 == 0x4400:
                op, d, reg = (h>>8)&3, (h&7)|((h>>4)&8), (h>>3)&15
                if op == 3:
                    s.need(h & 0x87 == 0, 'BLX/reserved BX')
                    return {'steps': steps, 'tail_target': self.r[reg]}
                s.need(d != 15 and op in (0, 2), '対象外high register命令')
                self.r[d] = self.r[reg] if op == 2 else (self.r[d]+self.r[reg]) & MASK
            elif h & 0xf800 in (0x6000,0x6800,0x7000,0x7800,0x8000,0x8800):
                op = h & 0xf800; width = 1 if op in (0x7000,0x7800) else (2 if op in (0x8000,0x8800) else 4)
                d, at = h&7, (self.r[(h>>3)&7]+((h>>6)&31)*width)&MASK
                if op & 0x0800: self.r[d] = self.read(at,width)
                else: self.write(at,width,self.r[d])
            elif h & 0xf000 == 0xd000:
                n,z,c,v = self.flags
                choices = {0:z, 1:not z, 2:c, 3:not c, 8:c and not z, 9:not c or z}
                s.need((h>>8)&15 in choices, '対象外condition')
                if choices[(h>>8)&15]: nxt = pc+4+2*((h&255)-(256 if h&128 else 0))
            elif h & 0xf800 == 0xe000:
                nxt = pc+4+2*((h&2047)-(2048 if h&1024 else 0))
            elif h & 0xf800 == 0xf000:
                target = capture.bl_target(pc,h,self.read(pc+2,2))
                s.need(target is not None, '不正BL')
                self.calls.append({'site':pc, 'target':target, 'args':self.r[:4],
                    'io_at_call':self.read(IO,2) if IO in self.mem else None,
                    'status_at_call':self.read(STATUS,2) if STATUS in self.mem else None})
                if stop_call: return {'steps':steps, 'stopped_before_external_call':target}
                s.need(returns is not None and target in returns, '未証明外部callee')
                # 明示mock契約: 外部は帰還・r4-r11/供給RAMを保持。実calleeの証明ではない。
                self.r[0] = need_uint(returns[target])
                self.r[1:4] = [0xdead0001,0xdead0002,0xdead0003]
                self.r[12] = 0xdead000c; self.r[14] = (pc+4)|1
                self.flags = (False,False,False,False); nxt = pc+4
            else: raise ValueError('対象外Thumb命令')
            pc = nxt
        raise ValueError('step上限')


def expected_bcd(raw, hour_flag=0):
    s.need(type(raw) is bytes and len(raw) == 7, 'BCD入力')
    need_uint(hour_flag,8)
    values = [10*(b>>4)+(b&15) if b <= 0x99 and b&15 <= 9 else 255 for b in raw]
    if hour_flag:
        values[4] = (values[4] + (12 if values[4] <= 11 else -12)) & 255
    # byte +2は書込対象外。年不正は2000+255=2255であり65535ではない。
    return [(CONVERTED,2,2000+values[0])] + [(CONVERTED+i+2,1,values[i]) for i in range(1,7)]


def bcd_case(raw, hour_flag=0):
    expected = expected_bcd(raw,hour_flag)
    vm=VM(); vm.seed(SELECTOR,raw); vm.seed(CONVERTED,b'\xcc'*9);vm.seed(HOUR_FLAG,bytes([hour_flag]))
    preserved=vm.r[4:7]; result=vm.run(BCD)
    actual=[(w['address'],w['width'],w['value']) for w in vm.writes if CONVERTED <= w['address'] < CONVERTED+9]
    # hour補正だけ同一addressへの追加store。最終値と書込範囲を独立照合。
    s.need(all(vm.read(at,width)==value for at,width,value in expected), 'BCD仕様差分')
    s.need({(a,w) for a,w,v in actual} == {(a,w) for a,w,v in expected}, 'BCD書込先差分')
    s.need(vm.read(CONVERTED+2,1)==0xcc and bytes(vm.mem[SELECTOR+i] for i in range(7))==raw, 'BCD入力/padding変更')
    s.need(all(CONVERTED <= w['address'] < CONVERTED+9 or SP-16 <= w['address'] < SP for w in vm.writes), 'BCD局所以外へのwrite')
    s.need(vm.r[13]==SP and vm.r[4:7]==preserved and not vm.calls, 'BCD帰還/保存差分')
    return vm,result


def bcd_vectors():
    count=0
    for field in range(7):
        for value in range(256):
            raw=bytearray(b'\x26\x09\x16\x03\x12\x34\x56');raw[field]=value
            bcd_case(bytes(raw));count+=1
    for value in range(256):
        raw=bytearray(b'\x26\x09\x16\x03\x00\x34\x56');raw[4]=value
        bcd_case(bytes(raw),1);count+=1
    return count


def reader_case(status, validation):
    need_uint(status);need_uint(validation)
    vm=VM()
    for at,width,value in ((IO,2,0x81),(STATUS,2,0x9999),(SAVED_IO,2,0),(RAW_STATUS,1,0)):
        vm.seed(at,value.to_bytes(width,'little'))
    preserved=vm.r[4:9]
    returns=dict.fromkeys(EXTERNALS,0);returns[EXTERNALS[1]]=status;returns[EXTERNALS[-1]]=validation
    vm.run(READER,returns=returns)
    targets=[c['target'] for c in vm.calls]
    wanted=list(EXTERNALS) if status&15==1 else list(EXTERNALS[:2])
    s.need(targets==wanted and vm.r[13]==SP and vm.r[4:9]==preserved,'reader条件付き経路/保存差分')
    s.need(vm.read(IO,2)==0x81 and vm.read(RAW_STATUS,1)==status&255,'reader IO/status差分')
    s.need(vm.read(STATUS,2)==(validation&65535 if status&15==1 else 1),'reader返却status差分')
    s.need(all(c['io_at_call']==0 for c in vm.calls[:-1]) if len(vm.calls)==5 else all(c['io_at_call']==0 for c in vm.calls),'reader IO呼出境界')
    if len(vm.calls)==5:
        s.need(vm.calls[-1]['io_at_call']==0x81 and all(c['args'][0]==SELECTOR for c in vm.calls[2:]), 'reader pointer引数差分')
    return vm


def prefix(counter, entry=TICK):
    need_uint(counter,8);s.need(entry in (TICK,INIT),'prefix entry')
    vm=VM();vm.seed(COUNTER,bytes([counter]));result=vm.run(entry,stop_call=True)
    expected_call = entry==INIT or counter==0
    s.need(bool(vm.calls)==expected_call,'prefix call条件差分')
    if expected_call:
        s.need(result.get('stopped_before_external_call')==READER,'prefix外部境界')
        if entry==INIT:s.need(vm.read(COUNTER,1)==0,'init counter')
    else:
        s.need(vm.read(COUNTER,1)==(counter+1 if counter<=59 else 0) and vm.r[13]==SP,'tick counter')
    return vm,result


def analyze(prior,out):
    owners=s.load(capture.OWNERS);memory=capture.saved_memory(owners)
    for w in prior['analysis']['new_windows']:
        data=bytes.fromhex(w['hex']);s.need(s.identity(data)==w['identity'] and len(data)==w['end']-w['start'],'新規保存byte identity')
        capture.merge_bytes(memory,w['start'],data)
    for at,data in CODES.items():
        s.need(bytes(memory[i] for i in range(at,at+len(data)))==data,'役割code差分')
    vectors=bcd_vectors()
    readers=[]
    for status in (0,1,0x11,0xff,0x10001):
        for validation in (0,0xff0):
            vm=reader_case(status,validation)
            readers.append({'input_status':status,'mock_validation':validation,'calls':vm.calls,
                'status_after':vm.read(STATUS,2),'classification':'CONDITIONAL_EXTERNAL_MOCK_NOT_NATIVE'})
    for count in range(256):prefix(count)
    prefix(17,INIT)
    veneer=VM();before=veneer.r.copy();tail=veneer.run(VENEER)
    s.need(tail['tail_target']==0x081C9DF9 and not veneer.writes and veneer.r[:3]==before[:3]
           and veneer.r[4:]==before[4:], 'tail veneer差分')
    refs=prior['analysis']['references']
    initial=[r for r in refs if r['target']==0x08113984]
    s.need(not initial,'initializer新規参照あり: caller引数の分析が必要')
    result={'classification':'SAVED_CONTROL_ROLE_CONTRACTS_NOT_STORY_REACHABILITY',
        'candidate':copy.deepcopy(s.CANDIDATE),'bcd_vectors_checked':vectors,
        'bcd_converter':{'entry':BCD,'raw_address':SELECTOR,'converted_address':CONVERTED,
            'input_fields':7,'year_bias':2000,'invalid_year':2255,'invalid_other_field':255,
            'hour_adjust_flag':HOUR_FLAG,'validity':'BCD digits only; not calendar field bounds',
            'raw_bytes_written':0,'frame_bytes':16,'external_calls':0,
            'scope_ja':'selectorと同じbyteをBCD年として読む実装。実到達/同時利用は未観測。'},
        'reader_wrapper':{'entry':READER,'frame_bytes':24,'io_address':IO,
            'external_targets':list(EXTERNALS),'gated_predicate':'external status & 15 == 1',
            'output_pointer':SELECTOR,'cases':readers,
            'external_return_and_preservation_proven':False,'external_buffer_writes_proven':False},
        'entry_prefix':{'tick':TICK,'init':INIT,'counter_address':COUNTER,
            'tick_inputs_checked':256,'tick_reader_condition':'counter == 0',
            'nonzero_counter_update':'1..59 increment; 60..255 reset to zero and return',
            'init_resets_counter_before_reader':True,
            'reused_reference_sites':[r for r in refs if r['target'] in (TICK,INIT)]},
        'external_veneer':{'entry':VENEER,'instructions':2,'tail_target':0x081C9DF9,
            'r0_r1_r2_r4_r11_sp_lr_preserved_until_tail':True,
            'delegate_return_preservation_proven':False,'memset_effect_proven':False},
        'initializer_caller_boundary':{'target':0x08113984,'direct_bl_and_aligned_pointer_candidates':0,
            'all_callers_absent_proven':False,'caller_pointer_size_limit_proven':False,
            'unsearched_forms':['Thumb short/tail branches','ARM B/BL','computed/indirect/mirrored targets']},
        'unread_delegates':[0x081C9DF9,*[x|1 for x in EXTERNALS]],
        'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_runtime_owners_excluded':False,
        'selector1_runtime_observed':False,'selector2_runtime_observed':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
        'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'candidate_reconstructions':0}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('保存byteから0x09126CB4の7field BCD変換を2048vectorで検証。0x09127060は外部5calleeを持つ'
            'I/O wrapper、0x09099E16は未読0x081C9DF9への2命令tail veneer。tick/init入口条件257件を限定検証。'
            'initializer直接BL/pointer参照0は不存在証明ではない。候補復元/native/既読ABI/BP再実行0。',
            '保存caller/制御役割証拠を再利用し、initializerへの未検索Thumb tail/ARM/間接参照と、'
            '0x081C9DF9およびI/O wrapperの未読5delegateを必要範囲だけ結合する。'
            'selector1/2とrecord pointer/size/LIMITの通常story実到達を観測するまでRing受入にしない。'
            'BCDとselectorの同一byteは確認済みだがRTC同時衝突/全owner不存在を断定しない。旧18ownerは維持。')


if __name__=='__main__':
    s.need(sys.argv[1:]==['run'],'runだけを許可');s.run(sys.modules[__name__])
