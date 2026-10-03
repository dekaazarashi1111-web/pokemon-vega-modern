#!/usr/bin/env python3
"""保存末尾3命令の条件付き復元ABIと5工程集約。先行ABI/nativeは実行しない。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE='763941a8200051ba5463addc2f5826defaa0f24e'
SLUG='pr16-ring-external1-exit-abi'
TASK='PR-P08-7-RING-EXTERNAL1-EXIT-ABI'
TITLE='保存末尾の条件付き復元帰還ABIと5工程の原Actions・commitを集約'
SELF='scripts/pr16_ring_external1_exit_abi.py'
TEST='tests/test_pr16_ring_external1_exit_abi.py'
WORKFLOW='.github/workflows/pr16-ring-external1-exit-abi.yml'
PRIOR='content/modernization/pr16_ring_external1_exit_bytes.json'
REPORT='content/modernization/pr16_ring_external1_exit_abi.json'
PREFIX='content/modernization/pr16_ring_external1_abi.json'
BODY='content/modernization/pr16_ring_external1_cont_abi.json'
KEY='ring_external1_exit_abi'
MIN_TESTS=24
EXTRA_CODE=()
COMPLETED=(
    (PREFIX,'fb7dc4ce41c06f15b4c781d3aea84d0b31caaae3',18),
    ('content/modernization/pr16_ring_external1_cont_bytes.json','b2685c0e9117989177b8ced6314ca6f780730aee',10),
    (BODY,'4d1350cbb717da7ce6a2b35683ebf36ec939dd46',20),
    (PRIOR,BASE,10))
SOURCES=tuple(path for path,_,_ in COMPLETED)
NO_REPEAT='本セッションのexternal1 prefix ABI/継続採取・ABI/末尾採取・ABIの5工程は完了。保存証拠と原Actions/commitを再利用し単独再実行しない。次は0x0806DD1Dの1根。全callee帰還・counter/返却pointer非alias・Ring通常取得は未受入。'
START=0x081138F0
CODE=('70bc','02bc','0847')
MASK=(1<<32)-1
EDGES=[{'site':START+4,'kind':'indirect','register':1,'target':None}]


def expected_nodes():
    return [dict(address=START+2*i,size=2,hex=h,kind='ordinary',memory_write=False,successors=[START+2*i+2])
            if i<2 else dict(address=START+4,size=2,hex=h,kind='indirect',register=1,memory_write=False,successors=[])
            for i,h in enumerate(CODE)]


def program(a):
    g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and a['target']==START|1 and a['next_saved_abi_target']==START|1,'candidate/target差分')
    s.need(g['entry']==START|1 and g['window']==64 and g['window_identity']==
           {'size':64,'sha256':'fb1ba4e1aa1ffca56c5afeb35034230da65dfa84c91ad56bcd664b953fd7cee6'},'window差分')
    s.need(g['nodes']==expected_nodes() and g['memory_write_sites']==[] and g['external_edges']==EDGES,'命令/間接辺差分')
    ranges=[dict(address=START+2*i,hex=h,**s.identity(bytes.fromhex(h))) for i,h in enumerate(CODE)]
    s.need(a['sampled_ranges']==ranges and a['sampled_instruction_bytes']==6,'sample hash差分')
    s.need(a['inherited_frame_bytes_live']==16 and a['unresolved_indirect_edges']==EDGES,'継承frame/帰還辺差分')
    s.need(g['saved_instruction_bytes_redecoded']==0 and g['deferred_roots_decoded']==0,'重複decode')
    s.need(len(set(a['old_unread_targets']))==18 and set(a['old_unread_targets'])<=set(a['remaining_unread_targets'])
           and {0x0806DD1D,0x081138F9}<=set(a['remaining_unread_targets']),'旧owner/別callee欠落')
    for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[k] is False,'過大受入')
    return g['nodes']


def execute(r0,sp,frame,code=CODE):
    """16byte読取snapshotのPOP/POP/BXのみ。branch先へは踏み込まない。"""
    s.need(tuple(code)==CODE,'保存code以外')
    s.need(type(r0) is int and 0<=r0<=MASK,'r0範囲')
    s.need(type(sp) is int and 0<=sp<=MASK-16 and sp%4==0,'sp範囲/整列')
    s.need(type(frame) is bytes and len(frame)==16,'frame幅')
    r=[0]*16;r[0]=r0;r[13]=sp;reads=[];branch=None
    for i,hx in enumerate(code):
        h=int.from_bytes(bytes.fromhex(hx),'little')
        if h&0xff00==0xbc00:
            for k in range(8):
                if h&(1<<k):
                    offset=r[13]-sp;r[k]=int.from_bytes(frame[offset:offset+4],'little')
                    reads.append({'site':START+2*i,'address':r[13],'register':k,'value':r[k]});r[13]+=4
        elif h==0x4708:branch=r[(h>>3)&15]
        else:raise ValueError('未知命令')
    s.need(r[13]-sp==16 and len(reads)==4 and branch is not None,'末尾契約差分')
    return {'r0':r[0],'restored_r4_r5_r6':r[4:7],'branch_operand':branch,
        'selected_isa':'THUMB' if branch&1 else 'ARM','branch_target_executed':False,
        'local_sp_delta':r[13]-sp,'exit_sp':r[13],'stack_reads':reads,'local_memory_writes':0,
        'prior_code_executed':False}


def join(prefix,body):
    """保存結果を条件付きに結合するだけ。先行interpreterは呼ばない。"""
    s.need(prefix['candidate']==body['candidate']==s.CANDIDATE,'結合candidate差分')
    s.need(prefix['local_sp_delta']==-16 and prefix['saved_register_order']==[4,5,6,14],'保存PUSH契約差分')
    early=prefix['boundary_contracts']['early_exit'];cont=prefix['boundary_contracts']['continuation']
    s.need(early=={'target':START|1,'r0':0,'frame_bytes_live':16}
           and cont['target']==0x081138C9 and cont['frame_bytes_live']==16,'prefix境界差分')
    s.need(body['local_sp_delta']==0 and body['inherited_frame_bytes_live']==16
           and body['next_unread_return_target']==START|1,'継続境界差分')
    s.need(body['counter_write']=={'site':0x081138E4,'address':0x0203AF96,'size':2,
           'value':'(inherited_u16_index + 1) mod 2^16','only_on_match':True},'保存副作用差分')
    for a in (prefix,body):
        s.need(a['callee_return_proven'] is False and a['saved_slot_preservation_proven'] is False
               and a['return_pointer_non_alias_proven'] is False,'非条件付き昇格')
    return {'net_sp_delta_under_composition':0,'r0_from_saved_prefix_or_continuation_preserved':True,
        'saved_results_reused_not_executed':True,
        'early_result':0,'continuation_pointer_formula':body['pointer_formula'],
        'continuation_match_formula':body['match_formula'],'counter_write':copy.deepcopy(body['counter_write']),
        'proof_assumptions_ja':['16byteのframe読取が有効で末尾3命令中のsnapshotが安定している。',
            'frameの4wordが保存したr4/r5/r6/LRに等しく、counter STRH等がそれらを破壊していない。',
            '保存LRが正しい継続先とISAを指す。bufferの有効範囲/整列/返却pointer非aliasは別途必要。'],
        'unconditional_external1_return_proven':False}


def alias_diagnostic():
    """保存継続counterの仮想aliasを末尾入力snapshotに反映。先行ABIは実行しない。"""
    entry_sp=0x0203AF98;sp=entry_sp-16;words=(0x44444444,0x55555555,0x66666666,0x08101235)
    original=b''.join(x.to_bytes(4,'little') for x in words);changed=bytearray(original)
    offset=0x0203AF96-sp;changed[offset:offset+2]=(1).to_bytes(2,'little')
    before=execute(0x02010002,sp,original);after=execute(0x02010002,sp,bytes(changed))
    s.need(before['branch_operand']==words[3] and after['branch_operand']==0x00011235
           and after['r0']==before['r0'],'alias反例差分')
    return {'external1_entry_sp':entry_sp,'saved_lr_word_address':entry_sp-4,
        'counter_strh_address':0x0203AF96,'counter_value':1,'before_branch_operand':before['branch_operand'],
        'after_branch_operand':after['branch_operand'],'observed':False,'original_lr_preservation_disproved_without_non_alias_assumption':True}


def aggregate(analyses):
    s.need(len(analyses)==5,'5工程の記録が必要')
    keys=('rom_changes','new_emulator_processes','accepted_native_cases_replayed',
          'candidate_reconstructions','new_graph_decodes','prior_abi_classifications_replayed')
    totals={k:sum(a.get(k,0) for a in analyses) for k in keys}
    s.need(totals==dict(zip(keys,(0,0,0,2,2,0))),'実行総数の差分')
    s.need(all(a['candidate']==s.CANDIDATE and a['ring_acquisition_accepted'] is False
               and a['release_ready'] is False for a in analyses),'candidate/受入境界の差分')
    s.need(all(set(a['old_unread_targets'])==set(analyses[0]['old_unread_targets']) for a in analyses),'旧owner欠落')
    totals['sampled_instruction_bytes']=sum(a.get('sampled_instruction_bytes',0) for a in analyses)
    totals['verified_instruction_bytes']=sum(a.get('instruction_bytes_verified',0) for a in analyses)
    s.need(totals['sampled_instruction_bytes']==42 and totals['verified_instruction_bytes']==88,'命令byte総数差分')
    return totals


def session_record(current,out):
    records=[];analyses=[]
    for path,commit,count in COMPLETED:
        raw=(s.ROOT/path).read_bytes();r=json.loads(raw);analyses.append(r['analysis'])
        s.need(subprocess.check_output(['git','show',commit+':'+path],cwd=s.ROOT)==raw,'先行完了commitからのbyte差分')
        run=s.api('actions/runs/'+str(r['run_id']))
        s.need(run['head_sha']==r['source_head'] and run['status']=='completed' and run['conclusion']=='success','先行原Actions差分')
        tests=r['focused_tests']
        s.need(tests=={'tests_run':count,'failures':0,'errors':0,'skips':0,'successful':True},'先行test件数差分')
        jobs=s.api('actions/runs/'+str(r['run_id'])+'/jobs')['jobs']
        s.need(len(jobs)==1 and jobs[0]['status']=='completed' and jobs[0]['conclusion']=='success','記録job未完')
        records.append({'task':r['task'],'path':path,'commit':commit,'source_head':r['source_head'],
                        'run_id':r['run_id'],'job_id':jobs[0]['id'],'original_run_conclusion':'success',
                        'focused_tests':tests,'report_identity':s.identity(raw)})
    tests=json.loads((out/'tests.json').read_bytes())
    records.append({'task':TASK,'path':REPORT,'source_head':os.environ['GITHUB_SHA'],
        'run_id':int(os.environ['GITHUB_RUN_ID']),'run_status_at_record':'in_progress',
        'record_commit_semantics':'guarded nonforce push後のremote ref/recorded-result.jsonで照合','focused_tests':tests})
    return {'session_five_tasks':records,'session_totals':aggregate([*analyses,current]),
            'session_focused_tests':sum(r['focused_tests']['tests_run'] for r in records)}


def analyze(prior,out):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL1-EXIT-BYTES','先行task差分');a=prior['analysis'];program(a)
    composition=join(s.load(PREFIX)['analysis'],s.load(BODY)['analysis'])
    values=[0,MASK,0x02010002,0x03006FF2,*[1<<i for i in range(32)]]
    for value in values:
        words=(value,value^MASK,(value+1)&MASK,0x08101235);frame=b''.join(x.to_bytes(4,'little') for x in words)
        r=execute(value,0x03006FF0,frame)
        s.need(r['r0']==value and r['restored_r4_r5_r6']==list(words[:3])
               and r['branch_operand']==words[3] and r['exit_sp']==0x03007000,'POP/BX契約差分')
    result={'classification':'EXTERNAL1_LOCAL_EXIT_ABI_AND_CONDITIONAL_FRAME_COMPOSITION',
        'candidate':copy.deepcopy(s.CANDIDATE),'instructions_verified':3,'instruction_bytes_verified':6,
        'tail_snapshot_diagnostic_cases':len(values),'local_sp_delta':16,'local_memory_writes':0,
        'restored_registers':[4,5,6],'branch_register':1,'branch_word_offset_from_tail_sp':12,
        'r0_preserved':True,'local_return_structure_verified':True,'composition':composition,
        'hypothetical_counter_corrupts_saved_lr':alias_diagnostic(),
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[0x0806DD1D,0x081138F9],
        'unresolved_indirect_edges':a['unresolved_indirect_edges'],
        'indirect_edge_classification':'frame_word_3_to_BX_r1_not_observed_return_target',
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_graph_decodes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0}
    result.update(session_record(result,out));return result


def summaries(a):
    return (f'保存末尾3命令/6byteはr4/r5/r6復元・SP+16・r0保持・保存wordからBX r1を検証。'
        f'本セッション5工程の限定{a["session_focused_tests"]}testsと原Actions/commitを集約。新規採取42byte、ABI照合88byte、候補復元2回、ROM変更/native/受入再実行0。'
        '保存LR破壊の仮想counter aliasを保持し、条件付き帰還を全callee帰還やRing通常取得へ昇格しない。',
        '次は未解決外部callee0x0806DD1Dの1根だけ限定採取し、保存byteのABI・副作用を調べる。'
        'external1の本5工程は再採取/単独ABI再実行禁止。0x081138F9と旧18owner、保存slot/返却pointer非alias、Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__=='__main__':s.run(sys.modules[__name__])
