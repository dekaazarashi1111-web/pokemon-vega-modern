#!/usr/bin/env python3
"""保存済み3命令の局所帰還ABI。全callee/実帰還/非aliasの証明ではない。"""
from __future__ import annotations
import copy
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE = '6f6a8678aea8089e184d3f667a5602bb540b7e18'
SLUG = 'pr16-ring-epilogue-abi'
TASK = 'PR-P08-7-RING-EPILOGUE-ABI'
TITLE = '保存末尾3命令の条件付き帰還ABIとpush読戻しを検証'
SELF = 'scripts/pr16_ring_epilogue_abi.py'
TEST = 'tests/test_pr16_ring_epilogue_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-epilogue-abi.yml'
PRIOR = 'content/modernization/pr16_ring_epilogue_bytes.json'
REPORT = 'content/modernization/pr16_ring_epilogue_abi.json'
KEY = 'ring_epilogue_abi'
MIN_TESTS = 16
EXTRA_CODE = (s.SELF,)
TAIL = 'content/modernization/pr16_ring_common_tail_abi.json'
CALLEE = 'content/modernization/pr16_ring_callee_abi.json'
SOURCES = (TAIL, CALLEE)
NO_REPEAT = '保存末尾0x0806DE63の3命令は条件付き局所ABI検証済み。再採取・単独再実行しない。全callee帰還/保存slot不変/非aliasは未証明。'
EXPECTED = ((0x0806DE62,'70bc'), (0x0806DE64,'02bc'), (0x0806DE66,'0847'))


def u32(n):
    s.need(type(n) is int and 0 <= n <= 0xffffffff, 'u32範囲外')
    return n


def validate_sample(prior):
    s.need(prior['task']=='PR-P08-7-RING-EPILOGUE-BYTES' and prior['run_id']==35011425946
           and prior['source_head']=='632e502f19f1caf6fcb7f48d1b58277fd02ef357', '採取identity不一致')
    a=prior['analysis']; g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and a['classification']=='EPILOGUE_BYTES_NOT_RETURN_PROOF', '採取scope不一致')
    s.need(g['entry']==0x0806DE63 and g['window']==18 and g['window_identity']=={
        'size':18,'sha256':'5a1c430318dadd0495fdcfaad3229ae022e3a91055f71dbf1b106fcbaebb9b82'}, '窓不一致')
    nodes=[]
    for at,h in EXPECTED:
        n={'address':at,'size':2,'hex':h,'kind':'indirect' if at==0x0806DE66 else 'ordinary',
           'memory_write':False,'successors':[] if at==0x0806DE66 else [at+2]}
        if at==0x0806DE66: n['register']=1
        nodes.append(n)
    s.need(g['nodes']==nodes and g['memory_write_sites']==[], '命令/辺/注釈不一致')
    s.need(g['external_edges']==[{'site':0x0806DE66,'kind':'indirect','register':1,'target':None}], 'BX辺不一致')
    s.need(a['sampled_ranges']==[dict(address=at,hex=h,**s.identity(bytes.fromhex(h))) for at,h in EXPECTED], '保存hash不一致')
    s.need(a['sampled_instruction_bytes']==6 and len(set(a['old_unread_targets']))==18, '保存scope不一致')
    for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[k] is False, '採取原本の過大主張')
    return a


def execute(code, registers, memory):
    """整列・非wrap・副作用なしRAM4wordの有限モデル。BX先は実行しない。"""
    s.need(tuple(code)==EXPECTED, '保存3命令以外は実行不可')
    s.need(len(registers)==16, 'register数不一致')
    r=[u32(x) for x in registers]; sp=r[13]
    s.need(sp%4==0 and sp<=0xffffffec, 'stack整列/wrap不正')
    before=copy.deepcopy(memory); reads=[]
    for at,h in code:
        ins=int.from_bytes(bytes.fromhex(h),'little')
        if ins & 0xff00 == 0xbc00:
            regs=[i for i in range(8) if ins & (1<<i)]
            s.need(regs, '空POP')
            for reg in regs:
                addr=r[13]
                s.need(addr in memory, '未提供stack word')
                r[reg]=u32(memory[addr]); reads.append(addr); r[13]+=4
        elif ins & 0xff87 == 0x4700:
            reg=(ins>>3)&15; dest=r[reg]
            s.need(dest&1 or dest%4==0, '未整列ARM境界は範囲外')
            return {'registers':r, 'sp_delta':r[13]-sp, 'reads':reads,
                    'target_thumb':bool(dest&1),'target_raw':dest,'target_address':dest&~1,
                    'memory_unchanged':memory==before,'destination_executed':False}
        else: raise ValueError('未知命令')
    raise ValueError('BXなし')


def recover_prior(prior, run):
    """失敗runをsuccessへ改作せず、既にpushされた限定成果だけ独立読戻し。"""
    s.need(run['id']==35011425946 and run['conclusion']=='failure'
           and prior['source_head']=='632e502f19f1caf6fcb7f48d1b58277fd02ef357', '回復対象不一致')
    validate_sample(prior)
    meta=s.api('git/commits/'+BASE)
    s.need([p['sha'] for p in meta['parents']]==[prior['source_head']], '保存commit親不一致')
    outputs=(PRIOR,s.STATE,s.DOC,s.BACKLOG,*s.LOGS)
    changed=s.cmd('git','diff','--name-only',prior['source_head'],BASE).splitlines()
    s.need(set(changed)==set(outputs), '保存commitの変更scope不一致')
    for p in outputs:
        s.need(subprocess.check_output(['git','show',BASE+':'+p],cwd=s.ROOT)==(s.ROOT/p).read_bytes(), '保存成果読戻し不一致')
    job=s.api('actions/jobs/104524066362')
    s.need(job['run_id']==run['id'] and job['head_sha']==prior['source_head'] and job['conclusion']=='failure', '原job不一致')
    log=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/jobs/104524066362/logs'],cwd=s.ROOT)
    text=log.decode('utf-8-sig')
    for token in ('632e502..6f6a867', 'assert_remote(commit)', 'ValueError: PR境界不一致',
                  '"new_violations": 0', '"exact_output_match": true', '"full_guard_pass_claimed": false'):
        s.need(token in text, '原ログの停止位置/guard不一致')
    s.need(prior['focused_tests']['successful'] and prior['focused_tests']['tests_run']==18, '採取tests不一致')
    return {'record_verified':True,'original_conclusion':'failure','failure_after_nonforce_push':True,
            'committed_outputs_byte_verified':list(outputs),'commit':BASE,'job_id':job['id'],
            'original_job_log_identity':s.identity(log),'new_graph_decodes':0,'candidate_reconstructions':0}


def analyze(prior,out):
    a=validate_sample(prior); c=s.load(CALLEE)['analysis']; tail=s.load(TAIL)['analysis']
    slots=c['prefix']['saved_register_slots']
    s.need([x['register'] for x in slots]==[4,5,6,14]
           and [x['flagset_entry_sp_offset'] for x in slots]==[-24,-20,-16,-12], '先行frame不一致')
    s.need(tail['continuation_thumb']==0x0806DE63 and tail['flagset_entry_sp_offset_at_boundary_under_saved_assumptions']==-24, '入口境界不一致')
    cases=0
    for sp in (0x02000100,0x03007000):
        for word in (0,0xffffffff,*[1<<i for i in range(32)]):
            regs=[word]*16; regs[13]=sp
            mem={sp:word,sp+4:word^0xffffffff,sp+8:word,sp+12:0x0806DE81}
            r=execute(EXPECTED,regs,mem)
            s.need(r['sp_delta']==16 and r['registers'][4:7]==[mem[sp],mem[sp+4],mem[sp+8]]
                   and r['registers'][0]==word and r['target_raw']==0x0806DE81 and r['memory_unchanged'], '局所ABI不一致')
            cases+=1
    return {'classification':'CONDITIONAL_EPILOGUE_RETURN_NOT_WHOLE_CALLEE_PROOF','candidate':copy.deepcopy(s.CANDIDATE),
        'instructions_verified':3,'instruction_bytes_verified':6,'local_sp_delta':16,
        'popped_registers':[4,5,6,1],'return_slot_register':1,'r0_preserved':True,
        'conditional_return_target':c['prefix']['callee_entry_lr_value'],
        'flagset_entry_sp_offset_after_epilogue_under_saved_assumptions':-8,
        'inherited_flagset_slots_unconsumed':[-8,-4], 'verification_cases':cases,
        'proof_assumptions_ja':['末尾へSP=FlagSet入口SP-24で到達し、整列・非volatile・非wrapの4wordを読む。',
            '先行の外部call/storeが保存r4/r5/r6/LRを書換えていない場合に限ってcaller値へ復元する。'],
        'corrupted_saved_lr_counterexample':{'intended':0x0806DE81,'actual_saved_word':0x08001001,'actual_bx_target':0x08001001},
        'return_pointer_alias_counterexamples':tail['return_pointer_alias_counterexamples'],
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[0x0806DE51], 'callee_return_proven':False,'callee_return_observed':False,
        'saved_slot_preservation_proven':False,'return_pointer_non_alias_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0}


def summaries(a):
    return ('保存末尾3命令/6byteの条件付き局所帰還ABIを検証。SP+16、r4/r5/r6を3wordから復元し4word目をr1経由BX、r0不変。'
        '保存slot保持と到達を仮定した帰還先0x0806DE81・FlagSet frame残8byteを結合。全callee帰還/非aliasは未証明。'
        '採取run35011425946はpush後PR照合でfailureのまま保持し、commit6f6a8678の6成果を独立読戻し。再採取0。',
        '次は未読0x0806DE51だけを限定採取し、もう一方のpointer経路を確認する。外部call3本/旧18targetは保持。'
        '保存末尾/共通末尾/zero/helper/既受入BPを再採取・単独再実行しない。Ring通常取得へ昇格しない。')

if __name__=='__main__': s.run(sys.modules[__name__])
