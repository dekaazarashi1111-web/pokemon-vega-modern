#!/usr/bin/env python3
"""未読callee 0x0806DD1Dを1根だけ採取。既読ABI/nativeは実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_epilogue_bytes as sampler
import pr16_ring_external1_exit_bytes as previous

BASE = 'f27c4f1a4c0e34e11fb0cd704b61780e342ebd2a'
SLUG = 'pr16-ring-external2-bytes'
TASK = 'PR-P08-7-RING-EXTERNAL2-BYTES'
TITLE = '未読外部callee0x0806DD1Dの限定採取と未証明境界の保存'
SELF = 'scripts/pr16_ring_external2_bytes.py'
TEST = 'tests/test_pr16_ring_external2_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-external2-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_external1_exit_abi.json'
REPORT = 'content/modernization/pr16_ring_external2_bytes.json'
KEY = 'ring_external2_bytes'
TARGET = 0x0806DD1D
EXTRA_SAMPLES = (*previous.EXTRA_SAMPLES, previous.REPORT)
KNOWN_SAMPLES = tuple(dict.fromkeys((*previous.KNOWN_SAMPLES, previous.REPORT)))
SOURCES = (previous.SELF, *previous.SOURCES, previous.REPORT)
MIN_TESTS = 14
EXTRA_CODE = ()
NO_REPEAT = '外部callee0x0806DD1Dの限定byte採取は完了。保存graphだけでABIと副作用を検証し、同一candidateから再採取しない。external1の5工程・BPを再実行せず、0x081138F9・旧18owner・保存slot/返却pointer非alias・Ring通常取得は未証明のまま保持する。'


def validate_prior(prior):
    s.need(prior['task'] == 'PR-P08-7-RING-EXTERNAL1-EXIT-ABI', '先行task差分')
    a = prior['analysis']
    s.need(a['candidate'] == s.CANDIDATE and a['priority_unread_targets'][0] == TARGET, 'candidate/次根差分')
    old, remaining = set(a['old_unread_targets']), set(a['remaining_unread_targets'])
    s.need(len(old) == 18 and old <= remaining and TARGET not in old
           and {TARGET, 0x081138F9} <= remaining, '未読境界欠落')
    s.need(a['composition']['saved_results_reused_not_executed'] is True
           and a['composition']['unconditional_external1_return_proven'] is False
           and a['hypothetical_counter_corrupts_saved_lr']['observed'] is False, '先行条件付き境界差分')
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
    result = {'classification': 'EXTERNAL2_BYTES_NOT_ABI_RETURN_OR_SIDE_EFFECT_PROOF',
        'candidate': copy.deepcopy(s.CANDIDATE), 'target': TARGET, 'graph': graph, 'sampled_ranges': ranges,
        'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
        'old_unread_targets': a['old_unread_targets'], 'old_frontier_removed': False,
        **frontier(a, graph, known), 'next_saved_abi_target': TARGET,
        'prior_external1_indirect_edges_preserved': copy.deepcopy(a['unresolved_indirect_edges']),
        'callee_return_proven': False, 'callee_return_observed': False, 'saved_slot_preservation_proven': False,
        'return_pointer_non_alias_proven': False, 'side_effects_excluded': False,
        'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 1, 'new_graph_decodes': 1,
        'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0}
    s.need(set(a['old_unread_targets']) <= set(result['remaining_unread_targets']), '旧owner消失')
    return result


def summaries(a):
    return (f'未読外部callee0x0806DD1Dの1根だけ{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byteを採取保存。'
        'external1の5工程と既読rootのdecode/ABI/BP再実行0。先行run35049978307の成功を原Actionsで照合。副作用・帰還・保存slot/返却pointer非aliasは未証明。',
        '次は保存済みpr16_ring_external2_bytes.jsonの命令だけで0x0806DD1DのABI・副作用を検証する。'
        '同一候補から再採取せず、未読継続が出れば保存frontierに従う。0x081138F9・旧18owner・Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__ == '__main__':
    s.run(sys.modules[__name__])
