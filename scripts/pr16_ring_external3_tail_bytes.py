#!/usr/bin/env python3
"""未読末尾0x08113961を1根だけ採取。prefix/bodyの保存ABIは再実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
import pr16_ring_external3_body_bytes as previous

BASE = '63291360cbf53546e52853ab358c33f5552747b2'
SLUG = 'pr16-ring-external3-tail-bytes'
TASK = 'PR-P08-7-RING-EXTERNAL3-TAIL-BYTES'
TITLE = 'external3未読末尾0x08113961の1根採取と間接帰還境界保存'
SELF = 'scripts/pr16_ring_external3_tail_bytes.py'
TEST = 'tests/test_pr16_ring_external3_tail_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-external3-tail-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_external3_body_abi.json'
REPORT = 'content/modernization/pr16_ring_external3_tail_bytes.json'
KEY = 'ring_external3_tail_bytes'
TARGET = 0x08113961
EXTRA_SAMPLES = (*previous.EXTRA_SAMPLES, previous.REPORT)
KNOWN_SAMPLES = tuple(dict.fromkeys((*previous.KNOWN_SAMPLES, previous.REPORT)))
SOURCES = (previous.SELF, *previous.SOURCES, previous.REPORT)
MIN_TESTS = 14
EXTRA_CODE = ()
NO_REPEAT = 'external3末尾0x08113961の1根byte採取は完了。同一candidateで再採取せず保存byteの帰還ABIを検証する。prefix/bodyは保存契約だけで合成し、既読ABI/BPを再実行しない。旧18owner・帰還先/保存frame非alias・Ring通常取得は未証明。'


def validate_prior(prior):
    s.need(prior['task'] == 'PR-P08-7-RING-EXTERNAL3-BODY-ABI', '先行task差分')
    a = prior['analysis']
    s.need(a['candidate'] == s.CANDIDATE and a['priority_unread_targets'] == [TARGET], 'candidate/次根差分')
    old, remaining = set(a['old_unread_targets']), set(a['remaining_unread_targets'])
    s.need(len(old) == 18 and TARGET not in old and remaining == old | {TARGET}, '未読境界欠落')
    s.need(a['inherited_frame_bytes_live'] == 20 and a['local_sp_delta'] == 0
           and a['next_unread_return_target'] == TARGET and a['saved_prefix_reused_not_executed'] is True
           and a['ordered_store_widths'] == [2,1,2,2]
           and a['non_alias_formula']['valid_without_alias_preconditions'] is False, '保存ABI契約差分')
    s.need(a['alias_diagnostics']['native_observation'] is False
           and all(a['alias_diagnostics'][k]['observed'] is False for k in
                   ('record_aliases_counter','record_aliases_base_pointer','value_aliases_counter')), '診断/観測混同')
    for key in ('callee_return_proven', 'callee_return_observed', 'saved_slot_preservation_proven',
                'return_pointer_non_alias_proven', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
        s.need(a[key] is False, '過大受入')
    return a


def frontier(a, graph, known):
    external = {e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    return {'remaining_unread_targets': sorted((set(a['remaining_unread_targets']) - {TARGET}) | (external - known)),
            'known_sampled_boundary_targets': sorted(external & known),
            'new_unread_targets': sorted(external - known - set(a['remaining_unread_targets'])),
            'unresolved_indirect_edges': [copy.deepcopy(e) for e in graph['external_edges'] if e.get('target') is None]}


def analyze(prior, out):
    a = validate_prior(prior)
    deferred = tuple(sorted(set(a['remaining_unread_targets']) - {TARGET}))
    graph, ranges = sampler.collect(TARGET, deferred, EXTRA_SAMPLES, out)
    s.need(graph['entry'] == TARGET and graph['saved_instruction_bytes_redecoded'] == 0
           and graph['deferred_roots_decoded'] == 0, '採取scope差分')
    known = {n['address'] | 1 for p in KNOWN_SAMPLES for n in s.load(p)['analysis']['graph']['nodes']}
    known.update(n['address'] | 1 for n in graph['nodes'])
    result = {'classification': 'EXTERNAL3_TAIL_BYTES_NOT_ABI_RETURN_OR_SIDE_EFFECT_PROOF',
        'candidate': copy.deepcopy(s.CANDIDATE), 'target': TARGET, 'graph': graph, 'sampled_ranges': ranges,
        'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
        'old_unread_targets': a['old_unread_targets'], 'old_frontier_removed': False,
        **frontier(a, graph, known), 'next_saved_abi_target': TARGET,
        'prior_external_indirect_edges_preserved': copy.deepcopy(a['prior_external_indirect_edges_preserved'] + a['unresolved_indirect_edges']),
        'callee_return_proven': False, 'callee_return_observed': False, 'saved_slot_preservation_proven': False,
        'return_pointer_non_alias_proven': False, 'side_effects_excluded': False,
        'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 1, 'new_graph_decodes': 1,
        'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0}
    s.need(set(a['old_unread_targets']) <= set(result['remaining_unread_targets']), '旧owner消失')
    return result


def summaries(a):
    return (f'external3未読末尾0x08113961の1根だけ{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byteを採取保存。'
        'external1/2・external3前半/継続の保存ABIとBPは再実行0。',
        '次は保存済みpr16_ring_external3_tail_bytes.jsonだけで末尾ABIと保存prefix/bodyの条件付き合成を検証する。'
        '末尾を再採取せず、既読ABI/BPを再実行しない。旧18owner・保存frame/record/global非alias・Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__ == '__main__':
    s.run(sys.modules[__name__])
