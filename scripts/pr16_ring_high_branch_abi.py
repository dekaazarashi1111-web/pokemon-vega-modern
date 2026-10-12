#!/usr/bin/env python3
"""高域分岐の保存8命令だけの算術ABI。ROM/既読末尾/nativeは実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE='dec0a27ac693547ef1df06e66d5e97f5f22dde26'
SLUG='pr16-ring-high-branch-abi'
TASK='PR-P08-7-RING-HIGH-BRANCH-ABI'
TITLE='保存高域8命令の符号付き除算と条件付きpointer ABIを検証'
SELF='scripts/pr16_ring_high_branch_abi.py'
TEST='tests/test_pr16_ring_high_branch_abi.py'
WORKFLOW='.github/workflows/pr16-ring-high-branch-abi.yml'
PRIOR='content/modernization/pr16_ring_high_branch_bytes.json'
REPORT='content/modernization/pr16_ring_high_branch_abi.json'
KEY='ring_high_branch_abi'
MIN_TESTS=14
EXTRA_CODE=()
ZERO='content/modernization/pr16_ring_zero_abi.json'
TAIL='content/modernization/pr16_ring_common_tail_abi.json'
EPILOGUE='content/modernization/pr16_ring_epilogue_abi.json'
SOURCES=(ZERO,TAIL,EPILOGUE)
NO_REPEAT='高域0x0806DE51の保存8命令は算術ABI検証済み。再採取・既読ABIの単独再実行をせず、次は外部callee0x08113889を1根だけ進める。'
START,END=0x0806DE50,0x0806DE60
HEX=('0549','7018','0028','01da','044a','b018','c010','0449')
LITERALS={0x0806DE68:0xffffc000,0x0806DE6C:0xffffc007,0x0806DE70:0x02037014}
MASK=0xffffffff


def program(a):
    g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and g['entry']==START|1 and g['window']==16,'採取scope不一致')
    s.need(g['window_identity']==s.identity(bytes.fromhex(''.join(HEX))),'window hash不一致')
    nodes=[]
    for i,h in enumerate(HEX):
        at=START+2*i; n={'address':at,'size':2,'hex':h,'kind':'conditional' if i==3 else 'ordinary',
            'memory_write':False,'successors':([START+8,START+12] if i==3 else [at+2]) if at+2<END else []}
        if i==3:n['target']=START+12
        if i in (0,4,7):
            ins=int.from_bytes(bytes.fromhex(h),'little'); addr=((at+4)&~3)+(ins&255)*4
            n.update(literal_address=addr,literal_value=LITERALS[addr])
        nodes.append(n)
    s.need(g['nodes']==nodes and g['memory_write_sites']==[],'命令/辺/literal不一致')
    s.need(len(g['external_edges'])==1 and g['external_edges'][0]['site']==END-2
           and g['external_edges'][0]['target']==END|1,'末尾境界不一致')
    ranges=[dict(address=START+2*i,hex=h,**s.identity(bytes.fromhex(h))) for i,h in enumerate(HEX)]
    ranges += [dict(address=at,hex=value.to_bytes(4,'little').hex(),**s.identity(value.to_bytes(4,'little'))) for at,value in LITERALS.items()]
    s.need(a['sampled_ranges']==ranges and a['sampled_instruction_bytes']==16,'sample hash/幅不一致')
    return nodes


def signed(value):
    return value if value < 0x80000000 else value-(1<<32)


def execute(entry_r6, code=HEX, literals=None):
    """Thumbの8命令内だけ有限解釈。出力境界DE60の保存ADDは実行しない。"""
    s.need(type(entry_r6) is int and 0<=entry_r6<=MASK,'r6不正')
    s.need(tuple(code)==HEX,'保存code以外を拒否')
    lit=LITERALS if literals is None else literals
    s.need(lit==LITERALS,'literal差分')
    r=[0]*16; r[6]=entry_r6; r[13]=0x03007000
    pc=START; seen=[]; data_reads=0; cmp_negative=None
    while pc<END:
        s.need(pc in range(START,END,2) and pc not in seen,'CFG逸脱/loop')
        seen.append(pc); h=int.from_bytes(bytes.fromhex(code[(pc-START)//2]),'little'); after=pc+2
        if h&0xf800==0x4800:
            r[(h>>8)&7]=lit[((pc+4)&~3)+(h&255)*4]
        elif h&0xfe00==0x1800:
            r[h&7]=(r[(h>>3)&7]+r[(h>>6)&7])&MASK
        elif h&0xf800==0x2800:
            s.need(h==0x2800,'CMP0以外は範囲外');cmp_negative=signed(r[0])<0
        elif h==0xda01:
            s.need(cmp_negative is not None,'比較なし分岐')
            if not cmp_negative:after=pc+4+2*(h&255)
        elif h&0xf800==0x1000:
            shift=(h>>6)&31 or 32;r[h&7]=(signed(r[(h>>3)&7])>>shift)&MASK
        else:raise ValueError('未知命令')
        pc=after
    s.need(pc==END,'出力境界逸脱')
    return {'boundary_r0':r[0],'boundary_r1':r[1], 'entry_r6_preserved':r[6]==entry_r6,
            'local_sp_delta':r[13]-0x03007000,'data_ram_reads':data_reads,'stores':0,
            'negative_correction':cmp_negative,'instructions_visited':seen,'prior_tail_executed':False}


def analyze(prior,out):
    s.need(prior['task']=='PR-P08-7-RING-HIGH-BRANCH-BYTES','先行task不一致')
    a=prior['analysis'];nodes=program(a)
    zero=s.load(ZERO)['analysis'];tail=s.load(TAIL)['analysis'];ep=s.load(EPILOGUE)['analysis']
    s.need(zero['high_input_to_special_path']=={'input_first':0x4000,'input_last':0xffff,'boundary':START|1,'r0':0x3fff},'高域入口証拠不一致')
    s.need(any(n['address']==END and n['operation']==['adds',0,0,1] for n in tail['decoded_operations']),'保存join不一致')
    s.need(ep['r0_preserved'] is True and ep['local_sp_delta']==16,'保存epilogue不一致')
    covered=set(); count=0
    for value in range(0x4000,0x10000):
        result=execute(value);covered.update(result['instructions_visited']);count+=1
        s.need(result['boundary_r0']==(value-0x4000)//8 and result['boundary_r1']==0x02037014
               and not result['negative_correction'] and result['local_sp_delta']==0,'高域算術不一致')
    diagnostics=(0,1,0x3ff0,0x3ff7,0x3ff8,0x3ff9,0x3ffa,0x3ffb,0x3ffc,0x3ffd,0x3ffe,0x3fff,0xffffffff)
    for value in diagnostics:
        result=execute(value);covered.update(result['instructions_visited'])
        delta=signed((value-0x4000)&MASK);q=(abs(delta)//8)*(-1 if delta<0 else 1)
        s.need(result['boundary_r0']==q&MASK,'負側切捨て不一致')
    s.need(covered==set(range(START,END,2)),'未検査命令')
    return {'classification':'HIGH_BRANCH_SIGNED_DIVISION_POINTER_UNDER_ENTRY_ASSUMPTIONS',
        'candidate':copy.deepcopy(s.CANDIDATE),'instructions_verified':8,'instruction_bytes_verified':16,
        'literal_bytes_verified':12,'high_input_cases':count,'out_of_route_diagnostic_cases':len(diagnostics),
        'high_input_bounds':[0x4000,0xffff],'boundary_thumb':END|1,
        'boundary_expression':'r0 = trunc(signed32(entry_r6 - 0x4000) / 8); r1 = 0x02037014',
        'conditional_pointer_expression':'0x02037014 + ((id - 0x4000) >> 3), when entry_r6=id in [0x4000,0xffff]',
        'computed_pointer_bounds_under_high_entry_assumption':[0x02037014,0x02038813],
        'allocated_storage_extent_proven':False,'local_sp_delta':0,'local_data_ram_reads':0,'local_stores':0,
        'prior_tail_and_epilogue_results_reused_not_executed':True,
        'proof_assumptions_ja':['未読高域入口へentry_r6=idで到達する。ID経路は先行保存dispatchを再利用し再実行しない。',
            '保存joinのADDと保存epilogueのr0保持を条件付きで結合。到達/stack slot保持/全callee帰還は証明しない。'],
        'hypothetical_inherited_slot_alias':{'id':0x4000,'pointer':0x02037014,'flagset_entry_sp':0x0203701C,'saved_slot_offset':-8,'observed':False},
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[0x08113889,0x0806DD1D,0x081138F9],
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
        'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0}


def summaries(a):
    return ('保存高域8命令/16byteとliteral12byteを照合。高域ID49152件、到達を主張しない負側診断13件で全8命令を検査。'
        'entry_r6=idならpointer式0x02037014+((id-0x4000)>>3)。RAM読取/store/stack操作0。'
        '保存join/epilogueは結果を再利用し実行0。格納域の実サイズ・保存slot非alias・全callee帰還は未証明。',
        '次は未解決外部callee0x08113889の1根だけを限定採取する。0x0806DD1D/0x081138F9と旧18targetを保持。'
        '保存高域/共通末尾/帰還末尾/zero/helper/受入済みBPを再実行しない。Ring通常取得受入へ昇格しない。')

if __name__=='__main__':s.run(sys.modules[__name__])
