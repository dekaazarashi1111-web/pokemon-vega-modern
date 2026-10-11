#!/usr/bin/env python3
"""未解決外部callee0x08113889の1根だけ採取。他calleeは追跡しない。"""
from __future__ import annotations
import copy
import json
import os
import subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
BASE='4c5b275e9abfc34f5d94d90b255c188f3db85e34'
SLUG='pr16-ring-external1-bytes'
TASK='PR-P08-7-RING-EXTERNAL1-BYTES'
TITLE='最初の未解決外部callee1根を限定採取し次のABI境界を記録'
SELF='scripts/pr16_ring_external1_bytes.py'
TEST='tests/test_pr16_ring_external1_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-external1-bytes.yml'
PRIOR='content/modernization/pr16_ring_high_branch_abi.json'
REPORT='content/modernization/pr16_ring_external1_bytes.json'
KEY='ring_external1_bytes'
TARGET=0x08113889
EXTRA_SAMPLES=('content/modernization/pr16_ring_epilogue_bytes.json',
               'content/modernization/pr16_ring_high_branch_bytes.json')
KNOWN_SAMPLES=(sampler.SAMPLE,*EXTRA_SAMPLES,
    *('content/modernization/pr16_ring_'+name+'_bytes.json' for name in ('zero','nonzero','helper','callee')))
COMPLETED=(
    ('content/modernization/pr16_ring_epilogue_bytes.json','6f6a8678aea8089e184d3f667a5602bb540b7e18'),
    ('content/modernization/pr16_ring_epilogue_abi.json','cc8e3bb00db195df3498668371669aa62123ce84'),
    ('content/modernization/pr16_ring_high_branch_bytes.json','dec0a27ac693547ef1df06e66d5e97f5f22dde26'),
    ('content/modernization/pr16_ring_high_branch_abi.json','4c5b275e9abfc34f5d94d90b255c188f3db85e34'))
SOURCES=(sampler.SELF,sampler.s.SELF,*sampler.SOURCES,*KNOWN_SAMPLES,*(p for p,_ in COMPLETED))
MIN_TESTS=9
EXTRA_CODE=()
NO_REPEAT='外部callee0x08113889の限定byteは保存済み。同一candidateから再採取せず保存graphのABIを検証する。他callee/旧18targetを解決済みへ変えない。'


def validate_prior(prior):
    s.need(prior['task']=='PR-P08-7-RING-HIGH-BRANCH-ABI','先行task不一致')
    a=prior['analysis']
    s.need(a['candidate']==s.CANDIDATE and a['priority_unread_targets'][0]==TARGET,'candidate/次根不一致')
    s.need(TARGET in a['remaining_unread_targets'] and len(set(a['old_unread_targets']))==18,'残辺不一致')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False,'過大受入')
    return a


def frontier(a,graph,known):
    external={e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    remaining=(set(a['remaining_unread_targets'])-{TARGET})|(external-known)
    return {'remaining_unread_targets':sorted(remaining),
            'known_sampled_boundary_targets':sorted(external&known),
            'new_unread_targets':sorted(external-known-set(a['remaining_unread_targets'])),
            'unresolved_indirect_edges':[copy.deepcopy(e) for e in graph['external_edges'] if e.get('target') is None]}


def aggregate(analyses):
    s.need(len(analyses)==5,'工程数不一致')
    totals={key:sum(a.get(key,0) for a in analyses) for key in
            ('rom_changes','new_emulator_processes','accepted_native_cases_replayed','candidate_reconstructions','new_graph_decodes')}
    s.need(totals=={'rom_changes':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
                   'candidate_reconstructions':3,'new_graph_decodes':3},'実行総計不一致')
    s.need(all(a['ring_acquisition_accepted'] is False for a in analyses),'受入昇格禁止')
    return totals


def session_record(current,out):
    records=[];analyses=[]
    for i,(path,commit) in enumerate(COMPLETED):
        raw=(s.ROOT/path).read_bytes();r=json.loads(raw);analyses.append(r['analysis'])
        s.need(subprocess.check_output(['git','show',commit+':'+path],cwd=s.ROOT)==raw,'先行記録byte差分')
        observed=s.api('actions/runs/'+str(r['run_id']))
        expected='failure' if i==0 else 'success'
        s.need(observed['head_sha']==r['source_head'] and observed['status']=='completed'
               and observed['conclusion']==expected,'先行run原結論不一致')
        if i==1:
            recovery=r['prior_actions_verified_without_replay'][0]['scoped_recovery']
            s.need(recovery['record_verified'] and recovery['commit']==COMPLETED[0][1],'採取記録の独立回復なし')
        s.need(r['focused_tests']['successful'] and r['focused_tests']['tests_run']==(18,16,8,14)[i],'先行tests不一致')
        records.append({'task':r['task'],'path':path,'commit':commit,'source_head':r['source_head'],
                        'run_id':r['run_id'],'original_run_conclusion':expected,'focused_tests':r['focused_tests']})
    tests=json.loads((out/'tests.json').read_bytes())
    records.append({'task':TASK,'path':REPORT,'source_head':os.environ['GITHUB_SHA'],
                    'run_id':int(os.environ['GITHUB_RUN_ID']),'run_status_at_record':'in_progress',
                    'record_commit_semantics':'remote ref and recorded-result.json after guarded nonforce push','focused_tests':tests})
    return {'session_five_tasks':records,'session_totals':aggregate([*analyses,current]),
            'session_focused_tests':sum(r['focused_tests']['tests_run'] for r in records)}


def analyze(prior,out):
    a=validate_prior(prior)
    deferred=tuple(sorted(set(a['remaining_unread_targets'])-{TARGET}))
    graph,ranges=sampler.collect(TARGET,deferred,EXTRA_SAMPLES,out)
    known={n['address']|1 for p in KNOWN_SAMPLES for n in s.load(p)['analysis']['graph']['nodes']}
    s.need(graph['entry']==TARGET and graph['saved_instruction_bytes_redecoded']==0
           and graph['deferred_roots_decoded']==0,'採取scope不一致')
    known.update(n['address']|1 for n in graph['nodes'])
    result={'classification':'EXTERNAL1_PREFIX_BYTES_NOT_ABI_OR_OWNER_PROOF','candidate':copy.deepcopy(s.CANDIDATE),
        'target':TARGET,'graph':graph,'sampled_ranges':ranges,
        'sampled_instruction_bytes':sum(n['size'] for n in graph['nodes']),
        'old_unread_targets':a['old_unread_targets'],'old_frontier_removed':False,
        **frontier(a,graph,known), 'next_saved_abi_target':TARGET,
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
        'new_emulator_processes':0,'candidate_reconstructions':1,'new_graph_decodes':1,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}
    result.update(session_record(result,out))
    return result


def summaries(a):
    return (f'未解決外部callee0x08113889の1根だけ{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byteを採取保存。'
        '他root/保存済み命令のdecodeは0。外部辺・間接辺・未読境界を保持し、calleeのABI/副作用/owner除外は未受入。'
        '本セッション5工程は採取3件/保存ABI2件、ROM変更0・受入済みnative再実行0。',
        '次は保存済みpr16_ring_external1_bytes.jsonだけで0x08113889の局所ABI・副作用・呼出境界を検証する。'
        '今回5工程のbyte再採取/ABI単独再実行は禁止。0x0806DD1D/0x081138F9と旧18owner、採取で現れた未解決辺は保持。'
        'Ring通常story取得、policy/Circus、最終候補/releaseは未完のまま。')

if __name__=='__main__':s.run(sys.modules[__name__])
