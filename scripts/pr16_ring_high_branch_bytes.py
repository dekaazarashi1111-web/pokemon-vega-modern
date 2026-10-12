#!/usr/bin/env python3
"""未読0x0806DE51の採取。保存済み共通末尾と帰還末尾へ入らない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
BASE = 'cc8e3bb00db195df3498668371669aa62123ce84'
SLUG='pr16-ring-high-branch-bytes'
TASK='PR-P08-7-RING-HIGH-BRANCH-BYTES'
TITLE='未読高域分岐1根を採取し保存済み末尾との境界を記録'
SELF='scripts/pr16_ring_high_branch_bytes.py'
TEST='tests/test_pr16_ring_high_branch_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-high-branch-bytes.yml'
PRIOR='content/modernization/pr16_ring_epilogue_abi.json'
REPORT='content/modernization/pr16_ring_high_branch_bytes.json'
KEY='ring_high_branch_bytes'
TARGET=0x0806DE51
DEFERRED=(0x08113889,0x0806DD1D,0x081138F9)
EXTRA_SAMPLE='content/modernization/pr16_ring_epilogue_bytes.json'
MIN_TESTS=8
EXTRA_CODE=()
SOURCES=(sampler.SELF,sampler.s.SELF,EXTRA_SAMPLE,*sampler.SOURCES)
NO_REPEAT='0x0806DE51高域分岐は採取済み。同一candidateの再採取をせず保存byteのABIへ進む。保存共通末尾/帰還末尾/既受入BPは再実行しない。'


def validate_prior(prior):
    s.need(prior['task']=='PR-P08-7-RING-EPILOGUE-ABI', '先行task不一致')
    a=prior['analysis']
    s.need(a['candidate']==s.CANDIDATE and a['priority_unread_targets']==[TARGET], 'candidate/次根不一致')
    s.need(len(set(a['old_unread_targets']))==18 and len(a['old_unread_targets'])==18, '旧18target不一致')
    for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[k] is False, '受入境界不一致')
    return a


def analyze(prior,out):
    a=validate_prior(prior)
    graph,ranges=sampler.collect(TARGET,DEFERRED,(EXTRA_SAMPLE,),out)
    known={n['address']|1 for p in (sampler.SAMPLE,EXTRA_SAMPLE)
           for n in s.load(p)['analysis']['graph']['nodes']}
    external={e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    s.need(graph['entry']==TARGET and not {n['address']|1 for n in graph['nodes']} & known, '既読命令の再採取')
    return {'classification':'HIGH_BRANCH_BYTES_NOT_ABI_PROOF','candidate':copy.deepcopy(s.CANDIDATE),
        'target':TARGET,'graph':graph,'sampled_ranges':ranges,
        'sampled_instruction_bytes':sum(n['size'] for n in graph['nodes']),
        'old_unread_targets':a['old_unread_targets'],'old_frontier_removed':False,
        'known_sampled_boundary_targets':sorted(external&known),
        'remaining_unread_targets':sorted(set(a['old_unread_targets'])|set(DEFERRED)|(external-known)),
        'priority_unread_targets':list(DEFERRED),'callee_return_proven':False,'callee_return_observed':False,
        'saved_slot_preservation_proven':False,'return_pointer_non_alias_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,
        'new_graph_decodes':1,'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return (f'未読高域分岐0x0806DE51だけを{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byte採取保存。'
        '保存済み末尾へはdecodeせず辺で停止。旧18targetと外部call3本を保持、全callee帰還/非alias/Ring取得は未証明。',
        '次は保存済みpr16_ring_high_branch_bytes.jsonだけで高域分岐のABIを検証する。既読末尾/zero/helper/BPを再実行しない。'
        'その後に未解決外部call0x08113889、0x0806DD1D、0x081138F9を各1根の範囲で進める。')

if __name__=='__main__':s.run(sys.modules[__name__])
