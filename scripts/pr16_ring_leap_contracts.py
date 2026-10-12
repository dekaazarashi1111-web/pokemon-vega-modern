#!/usr/bin/env python3
"""保存した剰余calleeと二月suffixの限定命令契約。ROM/nativeは再実行しない。"""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_delegate_contracts as old

BASE = 'c561b1c065d262d1ddaab338a8eb796119082acd'
SLUG = 'pr16-ring-leap-contracts'
TASK = 'PR-P08-7-RING-LEAP-CONTRACTS'
TITLE = '保存剰余callee・中継ABI・二月閏年suffixを検証'
SELF = 'scripts/pr16_ring_leap_contracts.py'
TEST = 'tests/test_pr16_ring_leap_contracts.py'
WORKFLOW = '.github/workflows/pr16-ring-leap-contracts.yml'
PRIOR = 'content/modernization/pr16_ring_divmod_frontier.json'
REPORT = 'content/modernization/pr16_ring_leap_contracts.json'
CLOCK = 'content/modernization/pr16_ring_clock_contracts.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 37
EXTRA_CODE = ()
SOURCES = (CLOCK,'scripts/pr16_ring_delegate_contracts.py','scripts/pr16_ring_clock_contracts.py')
NO_REPEAT = ('保存081C85A5の非0除数剰余・中継ABI・二月suffixを再利用。'
    '除数0の未読helperや実年offset、caller/pointer/size/LIMITの証明へ昇格しない。'
    '同じbyte採取/候補復元/GPIO/月表/BPを単独再実行しない。')
TARGET, END, THUNK, POOL = 0x081C85A4, 0x081C8664, 0x09099E04, 0x09099E5C
CODE = bytes.fromhex('002958d00123884200d2f74610b401242407a14204d2814202d209011b01f8e7e400a14204d2814202d249005b00f8e70022884200d3401a4c08a04205d3001b9c460124e3411a4363468c08a04205d3001b9c460224e3411a436346cc08a04205d3001b9c460324e3411a4363469c46002803d01b0901d00909d9e70e242407224001d110bcf74663460324e3411a4201d0cc08001963460224e3411a4201d08c08001963460124e3411a4201d04c08001910bcf74600b5fff7b6fc002000bd')
THUNK_CODE = bytes.fromhex('00b500f002f8011c00bd134b1847')
LITERAL = bytes.fromhex('a5851c08')
ARCHIVE = {'id':10446593639,'size':3810,'sha256':'5568aad8e4ccb6abe1d09830de51176969e1b5644d5b1302470e70882a339ee4'}


def need(ok,text):
    if not ok:raise ValueError(text)


class FlowBoundary(Exception):
    def __init__(self,pc,opcode):
        self.pc,self.opcode=pc,opcode
        super().__init__('保存命令の連結境界')


class LinkedVM(old.VM):
    """旧VMを変えずBL/POP/BX/MOV-pcと当該RORだけ接続。未知targetは停止。"""
    def __init__(self,codes,ranges):
        self.executing=False
        super().__init__(codes,ranges)
    def read(self,at,width):
        value=super().read(at,width)
        if self.executing and width==2 and at in self.code:
            self.fetches+=1
            need(self.fetches<=self.budget,'連結全体fetch上限')
            if value in (0x46F7,0x4718,0x41E3) or value&0xFE00==0xBC00 and value&256:
                raise FlowBoundary(at,value)
        return value
    def run_linked(self,entry,budget=2000):
        old.uint(entry)
        need(not entry&1 and type(budget)is int and 0<budget<=20000,'実行範囲')
        need(not self.executing,'入れ子実行')
        self.executing=True;self.fetches=0;self.budget=budget
        self.calls=[];self.edges=[];self.ror_count=0
        pc=entry
        try:
            while True:
                try:
                    result=super().run(pc)
                    if result['returned']:
                        return {'returned':True,'fetches':self.fetches}
                    self.r[14]=(result['site']+4)|1
                    self.calls.append({'site':result['site'],'target':result['unread_call'],'args':result['args']})
                    pc=result['unread_call']
                    if pc not in self.code:
                        return {**result,'fetches':self.fetches}
                    continue
                except FlowBoundary as flow:
                    h,pc=flow.opcode,flow.pc
                    if h==0x41E3:
                        amount=self.r[4]&255
                        need(amount in (1,2,3),'当該RORのshift範囲')
                        value=self.r[3]
                        self.r[3]=((value>>amount)|(value<<(32-amount)))&old.MASK
                        self.flags=(bool(self.r[3]&(1<<31)),self.r[3]==0,bool(self.r[3]&(1<<31)),self.flags[3])
                        self.ror_count+=1;pc+=2;continue
                    if h&0xFE00==0xBC00:
                        ids=[i for i in range(8) if h&(1<<i)]+[15]
                        for i,reg in enumerate(ids):self.r[reg]=self.read(self.r[13]+4*i,4)
                        self.r[13]+=4*len(ids);target=self.r[15]
                    elif h==0x4718:
                        target=self.r[3]
                        need(target&1,'ARM切替は未実装境界')
                    else:
                        target=self.r[14]
                        need(target&1,'保存calleeのThumb帰還契約外')
                    self.edges.append({'site':pc,'target':target,'opcode':h})
                    if target==old.LR:
                        return {'returned':True,'fetches':self.fetches}
                    pc=target&~1
                    need(pc in self.code,'未供給間接target')
        finally:self.executing=False


def machine(include_date=False):
    codes={TARGET:CODE,THUNK:THUNK_CODE,POOL:LITERAL}
    ranges=[(TARGET,END),(THUNK,THUNK+len(THUNK_CODE))]
    if include_date:
        codes[old.VALIDATOR]=old.CODES[old.VALIDATOR]
        ranges.append((old.VALIDATOR,0x0912705C))
    return LinkedVM(codes,ranges)


def remainder_case(dividend,divisor,linked=False):
    old.uint(dividend);old.uint(divisor);need(divisor!=0,'非0除数だけ')
    vm=machine();vm.r[:2]=[dividend,divisor];before=vm.r[4:12].copy()
    result=vm.run_linked(THUNK if linked else TARGET)
    need(result['returned'] and vm.r[0]==dividend%divisor,'剰余差分')
    need(not linked or vm.r[1]==vm.r[0],'中継r1差分')
    need(vm.r[4:12]==before and vm.r[13]==old.SP,'callee保存/帰還差分')
    need(all(old.SP-64<=at<old.SP for at,_,_ in vm.writes),'非stack書込')
    return {'remainder':vm.r[0],'fetches':vm.fetches,'ror_count':vm.ror_count,
        'stack_bytes':max([old.SP-at for at,_,_ in vm.writes]+[0])}


def bcd(raw):
    return 10*(raw>>4)+(raw&15) if raw<=0x99 and raw&15<=9 else None


def date_probe(raw):
    need(type(raw)is bytes and len(raw)==8 and raw[1]==2,'二月8byteだけ')
    year=bcd(raw[0]);need(year is not None and year%4==0,'新規year suffixだけ')
    vm=machine(True);vm.seed(old.BUFFER,raw);vm.r[0]=old.BUFFER;before=vm.r[4:12].copy()
    result=vm.run_linked(old.VALIDATOR)
    need(result['returned'] and vm.r[4:12]==before and vm.r[13]==old.SP,'二月ABI差分')
    need(bytes(vm.mem[old.BUFFER+i] for i in range(8))==raw,'date入力書込')
    need(all(old.SP-64<=at<old.SP for at,_,_ in vm.writes),'date非stack書込')
    return vm


def date_case(raw):
    # この新規domainでは有効BCD yearの4倍数25値すべてが29日を許す。暦のepochは仮定しない。
    vm=date_probe(raw)
    expected=((raw[7]>>7)&1)*32+(0 if raw[7]&64 else 16)
    for field,limit,bit in ((raw[2],29,256),(raw[4],24,512),(raw[5],60,1024),(raw[6],60,2048)):
        value=bcd(field)
        if value is None or value>limit:expected|=bit
    need(vm.r[0]==expected,'独立二月oracle差分')
    need([call['target'] for call in vm.calls]==[THUNK,THUNK+10],'二月call連鎖差分')
    for call in vm.calls:
        if call['target']==THUNK:
            need(call['args'][:2]==[bcd(raw[0]),100],'calendar BL引数差分')
    return {'value':vm.r[0],'calls':len(vm.calls),'fetches':vm.fetches,
        'stack_bytes':max([old.SP-at for at,_,_ in vm.writes]+[0])}


def bound_window(prior):
    import hashlib
    rows=prior['analysis']['new_windows']
    need(len(rows)==1 and rows[0]['start']==TARGET and rows[0]['end']==TARGET+512,'保存窓境界')
    raw=bytes.fromhex(rows[0]['hex'])
    need(len(raw)==512 and rows[0]['identity']=={'size':512,'sha256':hashlib.sha256(raw).hexdigest()},'保存窓identity')
    need(len(CODE)==END-TARGET and raw[:len(CODE)]==CODE,'剰余命令差分')
    return raw


def verify_original(prior):
    import pr16_ring_followup_v2 as s
    raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(ARCHIVE['id'])+'/zip'],cwd=s.ROOT)
    need(s.identity(raw)=={k:ARCHIVE[k] for k in ('size','sha256')},'先行artifact identity')
    names={'analysis.json','preflight.json','guard.json','recorded-result.json','tests.json','tests.txt'}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info=z.infolist()
        need(len(info)==6 and {r.filename for r in info}==names
             and all(not r.is_dir() and r.file_size<=200000 for r in info),'先行artifact member境界')
        values={r.filename:z.read(r).decode('utf-8') for r in info}
    receipt=json.loads(values['recorded-result.json']);guard=json.loads(values['guard.json'])
    need(json.loads(values['analysis.json'])==prior['analysis']
         and json.loads(values['tests.json'])==prior['focused_tests'],'先行保存report差分')
    need(receipt['commit']==BASE and receipt['run_id']==prior['run_id']
         and receipt['source_head']==prior['source_head']
         and receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED','先行完了receipt差分')
    need(guard['new_violations']==0 and guard['exact_output_match'] is True
         and guard['full_guard_pass_claimed'] is False,'guard境界差分')
    need(subprocess.check_output(['git','show',BASE+':'+PRIOR],cwd=s.ROOT)==(s.ROOT/PRIOR).read_bytes(),'先行commit読戻し差分')
    return {'archive':ARCHIVE,'receipt':receipt,'guard':guard}


def vectors():
    divisors=(1,2,3,4,7,8,15,16,31,32,63,64,100,127,255,256,0x7FFFFFFF,0x80000000,0xFFFFFFFF)
    pairs={(a,b) for a in range(256) for b in divisors}
    for bit in range(32):
        for delta in (-1,0,1):
            a=(1<<bit)+delta
            if 0<=a<=old.MASK:pairs.update((a,b) for b in divisors)
    seed=0x16202609
    for _ in range(1024):
        seed=(1664525*seed+1013904223)&old.MASK;a=seed
        seed=(1664525*seed+1013904223)&old.MASK;pairs.add((a,seed or 1))
    pairs.update((old.MASK,b) for b in divisors)
    return sorted(pairs)


def calendar_vectors():
    rows=set()
    for year in range(0,100,4):
        encoded=(year//10)*16+year%10
        for day in range(256):rows.add(bytes([encoded,2,day,0,0x12,0x30,0x45,64]))
        for status in (0,64,128,192):
            for time in ((0x12,0x30,0x45),(0x24,0x60,0x60),(0xFF,0xFF,0xFF)):
                rows.add(bytes([encoded,2,0x29,0,*time,status]))
    for encoded in (0,0x96):
        for weekday in range(256):rows.add(bytes([encoded,2,0x29,weekday,0x12,0x30,0x45,64]))
    return sorted(rows)


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    clock=s.load(CLOCK);saved.bindings_fresh(s.ROOT,clock['source_bindings'])
    bound_window(prior)
    for at,data in ((THUNK,THUNK_CODE),(POOL,LITERAL),(old.VALIDATOR,old.CODES[old.VALIDATOR])):
        need(s.identity(data)==clock['analysis']['byte_bindings'][f'0x{at:08X}'],'中継/validator保存byte差分')
    original=verify_original(prior)
    pairs=vectors();max_fetches=0;ror_vectors=0
    for dividend,divisor in pairs:
        r=remainder_case(dividend,divisor)
        max_fetches=max(max_fetches,r['fetches']);ror_vectors+=int(r['ror_count']>0)
    # 実date call引数を含む0..99 / 100を中継全体で網羅。大きい入力は別に代表だけ。
    linked_pairs=[(a,100) for a in range(100)]+[(old.MASK,b) for b in (1,3,100,0x80000000,old.MASK)]
    for dividend,divisor in linked_pairs:remainder_case(dividend,divisor,True)
    dates=calendar_vectors();call_rows=0;max_stack=0;flags=set()
    for date in dates:
        r=date_case(date);call_rows+=int(r['calls']>0);flags.add(r['value']);max_stack=max(max_stack,r['stack_bytes'])
    zero=machine();zero.r[:2]=[7,0];zero_result=zero.run_linked(TARGET)
    need(not zero_result['returned'] and zero_result['unread_call']==0x081C7FCC,'除数0境界差分')
    result={'classification':'SAVED_REMAINDER_THUNK_AND_FEBRUARY_SUFFIX_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'prior_original_verified':original,
        'counts':{'nonzero_u32_remainder_vectors':len(pairs),'ror_exercised_vectors':ror_vectors,
            'linked_thunk_vectors':len(linked_pairs),'february_vectors':len(dates),'february_call_vectors':call_rows,
            'maximum_division_halfword_fetches':max_fetches,'maximum_calendar_stack_bytes':max_stack},
        'byte_bindings':{f'0x{at:08X}':s.identity(data) for at,data in
            ((TARGET,CODE),(THUNK,THUNK_CODE),(POOL,LITERAL),(old.VALIDATOR,old.CODES[old.VALIDATOR]))},
        'remainder':{'entry':TARGET,'code_end':END,'nonzero_divisor_vectors_match_python_unsigned_modulo':True,
            'full_u32_domain_formally_proven':False,'calendar_divisor':100,'calendar_dividends_exhausted':list(range(100)),
            'r4_to_r11_and_sp_preserved_for_tested_vectors':True,'nonstack_writes':0},
        'thunk':{'entry':THUNK,'tail_target':TARGET|1,'r0_and_r1_equal_remainder_for_tested_vectors':True,
            'calendar_call_domain_exhausted':True,'saved_stack_bytes_short_path':4,'saved_stack_bytes_full_path':8},
        'february':{'decoded_years':list(range(0,100,4)),'day_bytes_per_year':256,'day_limit':29,
            'day_zero_accepted':True,'year_zero_day29_accepted':True,'weekday_control_bytes':256,
            'year_epoch_or_general_century_semantics_proven':False,'input_readonly':True,
            'hour24_minute60_second60_accepted':True,'result_flags_observed':sorted(flags),
            'unchanged_nonleap_and_other_month_prefixes_replayed':False},
        'zero_divisor':{'returned':False,'unread_call':zero_result['unread_call'],'site':zero_result['site'],
            'not_reachable_from_checked_calendar_call_domain':True,'helper_return_or_effects_proven':False},
        'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_callers_resolved':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'physical_hardware_behavior_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'candidate_reconstructions':0,'new_bytes_sampled':0}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    counts=result['counts']
    return (f'保存192byteの非0除数剰余{counts["nonzero_u32_remainder_vectors"]}vector・中継{counts["linked_thunk_vectors"]}vector・'
        f'二月{counts["february_vectors"]}vectorを検証。BCD year4倍数25値はday29許容、r4-r11/SP・入力不変。'
        '除数0だけ081C7FCCへ未読call。暦epoch/汎用世紀判定は未証明。候補復元/新規byte採取/ROM変更/native再実行0。',
        'GPIO/月表/剰余/閏年suffixの保存契約を再利用し、initializer08113984のcomputed/RAM caller・実pointer/size/LIMIT、'
        'または旧18未読ownerの未観測辺へ進む。除数0の081C7FCCは実callerで必要性が出るまで再採取しない。'
        'Ring正規取得・装備実戦・保存、policy/Circus/P08は未受入。BPと既読契約は単独再実行しない。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
