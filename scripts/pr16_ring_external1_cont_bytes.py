#!/usr/bin/env python3
"""external1未読継続1根だけ採取。prefix/末尾/他calleeはdecodeしない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
import pr16_ring_external1_bytes as previous
BASE='fb7dc4ce41c06f15b4c781d3aea84d0b31caaae3'
SLUG='pr16-ring-external1-cont-bytes'
TASK='PR-P08-7-RING-EXTERNAL1-CONT-BYTES'
TITLE='external1未読継続1根を採取し16byte継承frameと未読末尾を保存'
SELF='scripts/pr16_ring_external1_cont_bytes.py'
TEST='tests/test_pr16_ring_external1_cont_bytes.py'
WORKFLOW='.github/workflows/pr16-ring-external1-cont-bytes.yml'
PRIOR='content/modernization/pr16_ring_external1_abi.json'
REPORT='content/modernization/pr16_ring_external1_cont_bytes.json'
KEY='ring_external1_cont_bytes'
TARGET=0x081138C9
EXTRA_SAMPLES=(*previous.EXTRA_SAMPLES,previous.REPORT)
KNOWN_SAMPLES=tuple(dict.fromkeys((*previous.KNOWN_SAMPLES,previous.REPORT)))
SOURCES=(previous.SELF,*previous.SOURCES,previous.REPORT)
MIN_TESTS=10
EXTRA_CODE=()
NO_REPEAT='0x081138C9の1根継続byteは保存済み。prefix/継続を再採取せず保存継続ABIへ。0x081138F1末尾、他callee、旧18ownerの未証明範囲を保持する。'


def validate_prior(prior):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL1-ABI','先行task差分')
    a=prior['analysis']
    s.need(a['candidate']==s.CANDIDATE and a['priority_unread_targets'][0]==TARGET,'次根/candidate差分')
    c=a['boundary_contracts']['continuation']
    s.need(c['target']==TARGET and c['frame_bytes_live']==16 and c['r0']==0x0300202C
           and a['local_sp_delta']==-16,'継承ABI差分')
    s.need(TARGET in a['remaining_unread_targets'] and 0x081138F1 in a['remaining_unread_targets']
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
    return {'classification':'EXTERNAL1_CONTINUATION_BYTES_NOT_ABI_OR_RETURN_PROOF',
        'candidate':copy.deepcopy(s.CANDIDATE),'target':TARGET,'graph':graph,'sampled_ranges':ranges,
        'sampled_instruction_bytes':sum(n['size'] for n in graph['nodes']),
        'inherited_prefix_boundary':copy.deepcopy(a['boundary_contracts']['continuation']),
        'old_unread_targets':a['old_unread_targets'],'old_frontier_removed':False,**frontier(a,graph,known),
        'next_saved_abi_target':TARGET,'callee_return_proven':False,'callee_return_observed':False,
        'saved_slot_preservation_proven':False,'return_pointer_non_alias_proven':False,
        'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':1,'new_graph_decodes':1,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return (f'external1未読継続0x081138C9だけ{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byteを採取保存。'
        '16byte継承frameと末尾0x081138F1を保持し、既読命令/他rootのdecodeは0。採取を帰還/副作用除外/Ring取得受入へ昇格しない。',
        '次は保存済みpr16_ring_external1_cont_bytes.jsonだけで継続のABI・副作用・未解決辺を検証する。'
        'prefix再実行/byte再採取は禁止。続いて0x081138F1末尾採取/ABI。0x0806DD1D/0x081138F9・旧18owner・Ring通常取得は未完を保持。')

if __name__=='__main__':s.run(sys.modules[__name__])
