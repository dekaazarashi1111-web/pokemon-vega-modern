#!/usr/bin/env python3
"""external1未読帰還末尾1根だけ採取。保存prefix/継続/他calleeは追跡しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
import pr16_ring_external1_cont_bytes as previous
BASE='4d1350cbb717da7ce6a2b35683ebf36ec939dd46'
SLUG='pr16-ring-external1-exit-bytes'
TASK='PR-P08-7-RING-EXTERNAL1-EXIT-BYTES'
TITLE='external1帰還末尾1根だけ採取し継承frameと間接帰還境界を保存'
SELF='scripts/pr16_ring_external1_exit_bytes.py'
TEST='tests/test_pr16_ring_external1_exit_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-external1-exit-bytes.yml'
PRIOR='content/modernization/pr16_ring_external1_cont_abi.json'
REPORT='content/modernization/pr16_ring_external1_exit_bytes.json'
KEY='ring_external1_exit_bytes'
TARGET=0x081138F1
EXTRA_SAMPLES=(*previous.EXTRA_SAMPLES,previous.REPORT)
KNOWN_SAMPLES=tuple(dict.fromkeys((*previous.KNOWN_SAMPLES,previous.REPORT)))
SOURCES=(previous.SELF,*previous.SOURCES,previous.REPORT)
MIN_TESTS=10
EXTRA_CODE=()
NO_REPEAT='external1帰還末尾0x081138F1のbyteは採取保存済み。再採取せず保存末尾ABIだけを検証し、prefix/継続は保存結果を再利用する。全帰還/保存slot非alias/owner除外は未受入。'


def validate_prior(prior):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL1-CONT-ABI','先行task差分')
    a=prior['analysis']
    s.need(a['candidate']==s.CANDIDATE and a['priority_unread_targets'][0]==TARGET
           and a['next_unread_return_target']==TARGET,'candidate/次根差分')
    s.need(a['inherited_frame_bytes_live']==16 and a['local_sp_delta']==0,'継承frame差分')
    s.need(a['counter_write']=={'site':0x081138E4,'address':0x0203AF96,'size':2,
           'value':'(inherited_u16_index + 1) mod 2^16','only_on_match':True},'副作用契約差分')
    s.need(TARGET in a['remaining_unread_targets'] and 0x081138F9 in a['remaining_unread_targets']
           and len(set(a['old_unread_targets']))==18,'未読境界欠落')
    for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[k] is False,'過大受入')
    return a


def frontier(a,graph,known):
    external={e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    return {'remaining_unread_targets':sorted((set(a['remaining_unread_targets'])-{TARGET})|(external-known)),
            'known_sampled_boundary_targets':sorted(external&known),
            'new_unread_targets':sorted(external-known-set(a['remaining_unread_targets'])),
            'unresolved_indirect_edges':[copy.deepcopy(e) for e in graph['external_edges'] if e.get('target') is None]}


def analyze(prior,out):
    a=validate_prior(prior)
    deferred=tuple(sorted(set(a['remaining_unread_targets'])-{TARGET}))
    graph,ranges=sampler.collect(TARGET,deferred,EXTRA_SAMPLES,out)
    s.need(graph['entry']==TARGET and graph['saved_instruction_bytes_redecoded']==0
           and graph['deferred_roots_decoded']==0,'採取scope差分')
    known={n['address']|1 for p in KNOWN_SAMPLES for n in s.load(p)['analysis']['graph']['nodes']}
    known.update(n['address']|1 for n in graph['nodes'])
    return {'classification':'EXTERNAL1_EXIT_BYTES_NOT_RETURN_OR_STACK_INTEGRITY_PROOF',
        'candidate':copy.deepcopy(s.CANDIDATE),'target':TARGET,'graph':graph,'sampled_ranges':ranges,
        'sampled_instruction_bytes':sum(n['size'] for n in graph['nodes']),
        'inherited_frame_bytes_live':16,'continuation_counter_write':copy.deepcopy(a['counter_write']),
        'old_unread_targets':a['old_unread_targets'],'old_frontier_removed':False,**frontier(a,graph,known),
        'next_saved_abi_target':TARGET,'callee_return_proven':False,'callee_return_observed':False,
        'saved_slot_preservation_proven':False,'return_pointer_non_alias_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'new_graph_decodes':1,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return (f'external1未読帰還末尾0x081138F1だけ{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byteを採取保存。'
        '保存済みprefix/継続と別rootのdecodeは0。16byte継承frame・条件付きcounter書込を保持し、間接帰還/非aliasは未受入。',
        '次は保存済みpr16_ring_external1_exit_bytes.jsonの末尾ABIを検証し、prefix/継続は保存結果だけで条件付き結合する。'
        '本セッション4工程を再実行せず5工程目の記録へ。0x0806DD1D/0x081138F9・旧18owner・Ring通常取得は未完を保持。')

if __name__=='__main__':s.run(sys.modules[__name__])
