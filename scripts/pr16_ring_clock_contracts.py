#!/usr/bin/env python3
"""保存byteのGPIO2関数・月表境界・外部中継だけを検証。ROM/nativeは再実行しない。"""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_delegate_contracts as old

BASE = 'e0ecbcda36b6cbd27af9ae04dd4a20162ba44285'
SLUG = 'pr16-ring-clock-contracts'
TASK = 'PR-P08-7-RING-CLOCK-CONTRACTS'
TITLE = 'GPIO2delegate・月表境界・外部中継の保存byte契約を確定'
SELF = 'scripts/pr16_ring_clock_contracts.py'
TEST = 'tests/test_pr16_ring_clock_contracts.py'
WORKFLOW = '.github/workflows/pr16-ring-clock-contracts.yml'
PRIOR = 'content/modernization/pr16_ring_unread_frontier.json'
REPORT = 'content/modernization/pr16_ring_clock_contracts.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 36
EXTRA_CODE = ()
FRONTIER = 'content/modernization/pr16_ring_branch_frontier.json'
CONTRACTS = 'content/modernization/pr16_ring_delegate_contracts.json'
SOURCES = (FRONTIER, CONTRACTS, 'scripts/pr16_ring_delegate_contracts.py',
    'scripts/pr16_ring_record_callers.py', 'scripts/pr16_ring_branch_frontier.py',
    'content/modernization/pr16_ring_selector_owners.json',
    'content/modernization/pr16_ring_record_callers.json')
NO_REPEAT = ('GPIO2関数/月表11か月/無効monthの表範囲超過/09099E04中継は保存結果を再利用。'
    '同じbyte採取、mirrored探索、旧7delegate/BP/nativeを再実行しない。'
    '081C85A5の戻値・ABIと閏年suffix、実caller/pointer/size/LIMITは未証明。')
READ, WRITE, THUNK, TABLE = 0x0912C4A8, 0x0912C554, 0x09099E04, 0x09169530
BIC_SITE, BIC_OPCODE = 0x0912C52C, 0x43A0
MONTHS = (31,28,31,30,31,30,31,31,30,31,30,31)
GPIO_CODES = {
    READ: bytes.fromhex('01230721f0b584466327012604250524234a138004331380224b19803b000b4133405b0018002343284300041b04000c1b0c10801080108013800139eed20522184b08261a80042400230525144a14801480148014801480158011884908c9015b080b43013e1b0631061b0e0e0e0029edd1dc100431214002249d102c40180021433f24a04301245b10014323400b436146cb71044b1480012014801e70f0bdc4000008c6000008d1df0302'),
    WRITE: bytes.fromhex('012320222549f0b500060b8004330b8043151a400223c41523401a430823801503401a43402307201a431d4b188005236227012604259c46120612163b00034133405b001c002c432404240c0c800c800c80644623431b041b0c0b800138edd200240125042705260c48130023412b405b0019003343394309041b04090c1b0c01340180018001800380082cedd10022044b0580058001201a70f0bdc4000008c6000008d1df0302')}
THUNK_CODE = bytes.fromhex('00b500f002f8011c00bd134b1847')
THUNK_LITERAL = bytes.fromhex('a5851c08')
GPIO_RANGES = ((READ,0x0912C548),(WRITE,0x0912C5F0))
ARCHIVE = {'id':10443871750,'size':5484,'sha256':'b2a7fa32c327583ef9fdc066a9a679764bc1578fb3c19b5d959c646437f9a71c'}


def need(ok, text):
    if not ok:
        raise ValueError(text)


def uint(value, bits=32):
    need(type(value) is int and 0 <= value < 1 << bits, '整数範囲')
    return value


class BicBoundary(Exception):
    """旧VMにない1命令を、byteを書き換えず命令fetch境界で処理する。"""


class MissingRead(Exception):
    def __init__(self, at, width):
        self.at, self.width = at, width
        super().__init__('未供給read境界')


class ClockVM(old.VM):
    """旧VMは無変更。固定BIC siteだけを追加し、全segment共通のfetch上限を課す。"""
    def __init__(self, codes, code_ranges):
        self.executing = False
        self.fetches = self.bic_count = 0
        super().__init__(codes, code_ranges)

    def read(self, at, width):
        need(at % width == 0, '未整列read')
        if not all(at+i in self.mem for i in range(width)):
            raise MissingRead(at, width)
        value = super().read(at, width)
        if self.executing and width == 2 and at in self.code:
            self.fetches += 1
            need(self.fetches <= self.fetch_limit, '全segment共通fetch上限')
            if at == BIC_SITE:
                need(value == BIC_OPCODE, '固定BIC opcode差分')
                raise BicBoundary()
        return value

    def run(self, entry, max_steps=20000):
        uint(entry)
        need(not entry & 1 and type(max_steps) is int and 0 < max_steps <= 20000, '実行範囲')
        need(not self.executing, '入れ子実行禁止')
        self.fetches = self.bic_count = 0
        self.fetch_limit = max_steps
        self.executing = True
        pc = entry
        try:
            while True:
                try:
                    result = super().run(pc, max_steps=20000)
                    last_segment_steps = result.pop('steps')
                    return {**result, 'last_segment_steps':last_segment_steps,
                        'instruction_halfword_fetches':self.fetches, 'bic_count':self.bic_count}
                except BicBoundary:
                    # Thumb BIC r0,r4: N/Zだけ更新。C/V、他registerとROMは保持。
                    self.r[0] &= (~self.r[4]) & old.MASK
                    self.nz(self.r[0])
                    self.bic_count += 1
                    pc = BIC_SITE + 2
        finally:
            self.executing = False


def io_vm(busy):
    uint(busy,8)
    vm = ClockVM(GPIO_CODES, GPIO_RANGES)
    vm.seed(old.BUSY,bytes([busy])); vm.seed(old.DATA,bytes(6))
    return vm


def send_byte(value, order):
    result = []
    for bit in order:
        part = ((value >> bit) & 1) * 2
        result += [(old.DATA,2,4|part)]*3 + [(old.DATA,2,5|part)]
    return result


def read_value(raw):
    uint(raw,8)
    return (raw & 0xC0) | ((raw >> 3) & 4) | ((raw >> 2) & 2) | ((raw >> 1) & 1)


def write_value(raw):
    uint(raw)
    return 0x40 | ((raw & 4) << 3) | ((raw & 2) << 2) | ((raw & 1) << 1)


def finish(vm, entry):
    before = vm.r[4:12].copy()
    result = vm.run(entry)
    need(result['returned'] and vm.r[4:12] == before and vm.r[13] == old.SP, '帰還/保存register差分')
    need(vm.r[0] == 1 and vm.mem[old.BUSY] == 0, '戻値/BUSY差分')
    need(not any(a == old.BUSY for a,_,_ in vm.reads), 'delegateがBUSYを読む')
    return [w for w in vm.writes if not old.SP-64 <= w[0] < old.SP]


def read_case(raw, busy=0, alignment=0):
    uint(raw,8); uint(alignment,2)
    vm = io_vm(busy)
    vm.seed(old.BUFFER,bytes([0xCC])*16); vm.r[0] = old.BUFFER + alignment
    vm.io_bits = [((raw >> bit) & 1)*2 for bit in range(8)]
    writes = finish(vm, READ)
    expected = [(old.DATA,2,1),(old.DATA,2,5),(old.DIRECTION,2,7)] + send_byte(0x63,range(7,-1,-1))
    expected += [(old.DIRECTION,2,5)] + ([(old.DATA,2,4)]*5+[(old.DATA,2,5)])*8
    expected += [(old.BUFFER+alignment+7,1,read_value(raw)),(old.DATA,2,1),(old.DATA,2,1),(old.BUSY,1,0)]
    need(writes == expected and vm.io_index == 8 and vm.bic_count == 1, 'read GPIO/buffer列')
    buffer = bytearray([0xCC]*16); buffer[alignment+7] = read_value(raw)
    need(bytes(vm.mem[old.BUFFER+i] for i in range(16)) == buffer, 'read buffer範囲')
    return {'result_byte':read_value(raw),'io_reads':8,'nonstack_writes':len(writes)}


def write_case(raw, busy=0):
    uint(raw)
    vm = io_vm(busy); vm.r[0] = raw
    writes = finish(vm, WRITE)
    expected = [(old.DATA,2,1),(old.DATA,2,5),(old.DIRECTION,2,7)] + send_byte(0x62,range(7,-1,-1))
    expected += send_byte(write_value(raw),range(8)) + [(old.DATA,2,1),(old.DATA,2,1),(old.BUSY,1,0)]
    need(writes == expected and vm.io_index == 0 and vm.bic_count == 0, 'write GPIO列')
    return {'serialized_byte':write_value(raw),'io_reads':0,'nonstack_writes':len(writes)}


def bcd(raw):
    return 10*(raw >> 4)+(raw & 15) if raw <= 0x99 and raw & 15 <= 9 else None


def date_expected(raw):
    """新しい11か月だけの独立oracle。無効monthは表外read先で停止し、戻値を捏造しない。"""
    need(type(raw) is bytes and len(raw)==8 and raw[1] != 2, '新規non-February範囲だけ')
    year,month,day,weekday,hour,minute,second,status = raw
    m = bcd(month)
    if m is None or not 1 <= m <= 12:
        return {'returned':False,'table_read_address':(TABLE+4*((255 if m is None else m)-1)) & old.MASK}
    value = ((status >> 7)&1)*32 + (0 if status & 64 else 16)
    if bcd(year) is None: value |= 64
    for field,limit,bit in ((day,MONTHS[m-1],256),(hour,24,512),(minute,60,1024),(second,60,2048)):
        v = bcd(field)
        if v is None or v > limit: value |= bit
    return {'returned':True,'value':value}


def date_case(raw):
    expected = date_expected(raw)
    codes = {old.VALIDATOR:old.CODES[old.VALIDATOR],TABLE:struct.pack('<12I',*MONTHS)}
    vm = ClockVM(codes,((old.VALIDATOR,0x0912705C),))
    vm.seed(old.BUFFER,raw); vm.r[0] = old.BUFFER; before = vm.r[4:12].copy()
    try:
        actual = vm.run(old.VALIDATOR)
    except MissingRead as edge:
        need(expected['returned'] is False and edge.width == 4 and edge.at == expected['table_read_address'], '予想外read境界')
        need(not TABLE <= edge.at < TABLE+48, '月表内readを未読扱い')
        actual = {'returned':False,'table_read_address':edge.at,'stop':'outside_declared_month_table'}
    if actual['returned']:
        need(expected['returned'] and vm.r[0] == expected['value'] and vm.r[4:12] == before and vm.r[13] == old.SP, 'date戻値/ABI差分')
        actual = {'returned':True,'value':vm.r[0]}
    else:
        need(actual.get('stop') == 'outside_declared_month_table', '未読callを戻値へ昇格')
    need(all(old.SP-64 <= at < old.SP for at,_,_ in vm.writes), 'date非stack書込')
    need(bytes(vm.mem[old.BUFFER+i] for i in range(8)) == raw, 'date入力変更')
    return actual


def thunk_contract(code=THUNK_CODE, literal=THUNK_LITERAL):
    need(type(code) is bytes and code == THUNK_CODE and type(literal) is bytes and len(literal) == 4, '中継opcode/size差分')
    words = struct.unpack('<7H',code)
    delta = ((words[1]&2047) << 12) | ((words[2]&2047) << 1)
    if words[1]&1024: delta -= 1 << 23
    call_target = THUNK+2+4+delta
    pool = ((THUNK+10+4)&~3)+(words[5]&255)*4
    target = int.from_bytes(literal,'little')
    need(call_target == THUNK+10 and pool == 0x09099E5C and target & 1 and 0x08000000 <= target < 0x0A000000, '中継target/literal差分')
    return {'entry':THUNK,'bl_site':THUNK+2,'local_target':call_target,'literal_address':pool,
        'unread_tail_target':target,'saved_lr_bytes':4,'callee_entry_sp_mod8_delta':4,
        'conditional_suffix_ja':'外部calleeがSPと保存LRを保持して戻る場合だけ、r1=r0の後に保存LRへ帰還。',
        'external_return_or_abi_proven':False,'remainder_semantics_proven':False,'leap_year_suffix_proven':False}


def verify_original(prior):
    """今回先行runの原ZIP/保存commitだけを照合。探索/検証本体は再実行しない。"""
    import pr16_ring_followup_v2 as s
    raw = subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(ARCHIVE['id'])+'/zip'],cwd=s.ROOT)
    need(s.identity(raw) == {k:ARCHIVE[k] for k in ('size','sha256')}, '先行原artifact差分')
    expected = {'analysis.json','preflight.json','guard.json','recorded-result.json','tests.json','tests.txt'}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        info = archive.infolist()
        need(len(info)==6 and {r.filename for r in info} == expected and all(r.file_size <= 200000 and not r.is_dir() for r in info), 'artifact member境界')
        payload = {r.filename:archive.read(r).decode('utf-8') for r in info}
    receipt = json.loads(payload['recorded-result.json'])
    need(json.loads(payload['analysis.json']) == prior['analysis'] and json.loads(payload['tests.json']) == prior['focused_tests'], '先行保存report差分')
    need(receipt['commit']==BASE and receipt['run_id']==35090180714 and receipt['source_head']==prior['source_head']
         and receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED', '先行receipt差分')
    need(subprocess.check_output(['git','show',BASE+':'+PRIOR],cwd=s.ROOT)==(s.ROOT/PRIOR).read_bytes(), '先行commit byte差分')
    failed = s.api('actions/runs/35090013920')
    need(failed['status']=='completed' and failed['conclusion']=='failure' and failed['head_sha']=='2aebb6d75cad48cc26b83645b675121b6a31c8fd','初回failure原結論差分')
    preflight = json.loads(payload['preflight.json'])
    need(preflight['original_failed_run']==failed['id'] and preflight['failure_stage']=='missing_preflight_before_candidate_restore','failure記録差分')
    return {'archive':ARCHIVE,'receipt':receipt,'guard':json.loads(payload['guard.json']),
        'original_failure':{k:failed[k] for k in ('id','head_sha','status','conclusion')},
        'failure_stage':preflight['failure_stage']}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    reports = {p:s.load(p) for p in (FRONTIER,CONTRACTS,frontier.OWNERS,frontier.CALLERS)}
    for report in reports.values(): saved.bindings_fresh(s.ROOT,report['source_bindings'])
    memory = previous.saved_memory(reports[frontier.OWNERS])
    for report in (reports[frontier.CALLERS],reports[FRONTIER],prior):
        frontier.add_windows(memory,report['analysis']['new_windows'])
    expected = {**GPIO_CODES,THUNK:THUNK_CODE,0x09099E5C:THUNK_LITERAL,
        TABLE:struct.pack('<12I',*MONTHS),old.VALIDATOR:old.CODES[old.VALIDATOR]}
    for at,data in expected.items():
        need(bytes(memory[at+i] for i in range(len(data))) == data,'保存byteと契約差分')
    source_original = verify_original(prior)
    counts = {'read_vectors':0,'write_vectors':0,'valid_month_day_vectors':0,'month_extent_vectors':0}
    for value in range(256):
        for busy in (0,1,2,255):
            read_case(value,busy,value%4); counts['read_vectors']+=1
            write_case(value,busy); counts['write_vectors']+=1
    for high in (0x100,0x12340000,0xFFFFFF00):
        for value in range(256):
            write_case(high|value); counts['write_vectors']+=1
    for month in (1,3,4,5,6,7,8,9,0x10,0x11,0x12):
        for day in range(256):
            date_case(bytes([1,month,day,0,0x12,0x30,0x45,64]));counts['valid_month_day_vectors']+=1
    outside = {}
    for month in range(256):
        if month == 2: continue
        for day in (0,0x31,255):
            result = date_case(bytes([1,month,day,0,0x12,0x30,0x45,64]));counts['month_extent_vectors']+=1
            if not result['returned']:
                outside[f'0x{month:02X}'] = result['table_read_address']
    result = {'classification':'SAVED_GPIO_MONTH_TABLE_AND_THUNK_CONTRACTS_NOT_HARDWARE_OR_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'prior_original_verified':source_original,'counts':counts,
        'byte_bindings':{f'0x{at:08X}':s.identity(data) for at,data in expected.items()},
        'gpio_read':{'entry':READ,'command':0x63,'serial_bit_order':'LSB_FIRST','buffer_written_offset':7,
            'result_bits':'input bits 7,6 retained; input bits 5,3,1 become output bits 2,1,0',
            'returns':1,'busy_read':False,'busy_after':0,'buffer_0_to_6_preserved':True,'supplied_io_stream_only':True},
        'gpio_write':{'entry':WRITE,'command':0x62,'payload_forced_bit':0x40,
            'payload_bits':'input bits 2,1,0 become payload bits 5,3,1; all other input bits ignored',
            'command_order':'MSB_FIRST','payload_order':'LSB_FIRST','returns':1,'busy_read':False,'busy_after':0},
        'date':{'month_table':list(MONTHS),'valid_months_tested':[1,3,4,5,6,7,8,9,10,11,12],
            'day_bytes_per_month':256,'day_zero_accepted':True,'february_prefix_replayed':False,
            'invalid_month_values':len(outside),'invalid_month_outside_table_reads':outside,
            'outside_stop_is_model_boundary_not_hardware_fault':True,'out_of_table_values_or_runtime_outcomes_proven':False},
        'thunk':thunk_contract(),'unread_external_targets':[0x081C85A5],
        'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_callers_resolved':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'physical_hardware_behavior_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0,'candidate_reconstructions':0}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('保存byteだけでGPIO2関数のread1024/write1792vectorと月表11か月2816dayを検証。'
        'month境界765vectorでは無効244値が表外readへ進むことを記録し、実機faultとは断定しない。'
        '09099E04は081C85A5への中継で剰余/閏年契約は未証明。先行42tests成功原本と初回failureを保持。候補復元/ROM変更/native再実行0。',
        '保存中継から0x081C85A5の未読契約と閏年suffixを追う。無効monthの表外値を正常拒否と仮定しない。'
        'initializer08113984のcomputed/RAM caller・pointer/size/LIMITと旧18ownerは未完。'
        'GPIO/月表/byte採取/mirrored探索/BPを再実行しない。Ring正規取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可'); support.run(sys.modules[__name__])
