"""737親の全証拠・137frontier・保存容量planへ束縛する。旧lease規則は不変。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pr16_dex_hof_remaining_consumers_chain as chain
import pr16_dex_hof_partial_space as base_capacity
import pr16_dex_hof_summary_capacity as prior
from pr16_dex_hof_donor import identity, need
from pr16_dex_hof_space_intervals import Span, plan_materialized_successor

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = 'content/modernization/pr16_dex_hof_summary_references_evidence/unknown-frontier.json'
CHECKPOINT = chain.PARENT_CHECKPOINT
PARENT_PLAN = 'content/modernization/pr16_dex_hof_summary_references_evidence/partial-space.json'
INPUTS = {
    FRONTIER: {'size': 60019, 'sha256': '8e9a910b72b855ae7115a28b279abeddf82612f8f975e6085b6bb17fafd1093d'},
    CHECKPOINT: chain.PARENT_CHECKPOINT_ID,
    PARENT_PLAN: {'size': 15194, 'sha256': '0c02f86656a4bfc4f16a73e09c9eff9ae0f382989b89deeed99bfcc81f6c2da7'},
}
PARENT_AUDIT_ID = chain.PARENT_AUDIT_ID


def all_input_bindings():
    """全歴史的容量原本の独立identityを、重複が一致する場合だけ統合する。"""
    merged = copy.deepcopy(INPUTS)
    module, visited = prior, set()
    while module is not None:
        need(module not in visited, 'acyclic fixed capacity lineage')
        visited.add(module)
        for path, expected in module.INPUTS.items():
            value = dict(zip(('size', 'sha256'), expected)) if type(expected) is tuple else dict(expected)
            need(set(value) == {'size', 'sha256'}, 'closed independent capacity binding')
            need(path not in merged or merged[path] == value, 'duplicate capacity input identity agrees')
            merged[path] = value
        module = getattr(module, 'prior', None)
    return {path: merged[path] for path in sorted(merged)}


def read_inputs(root=ROOT):
    values = {}
    for path, expected in INPUTS.items():
        file = root / path
        need(file.is_file() and not file.is_symlink(), 'regular independent parent capacity input')
        raw = file.read_bytes()
        need(identity(raw) == expected and raw.endswith(b'\n') and b'\r' not in raw,
             'entire independent737 capacity input in LF')
        values[path] = json.loads(raw)
    frontier, checkpoint, recorded = (values[p] for p in (FRONTIER, CHECKPOINT, PARENT_PLAN))
    need(checkpoint['unknown_identity'] == INPUTS[FRONTIER] and
         checkpoint['capacity_identity'] == INPUTS[PARENT_PLAN] and
         checkpoint['candidate'] == frontier['candidate'] == recorded['candidate'],
         'measured parent unknown and capacity envelopes')
    need((checkpoint['classified'], checkpoint['unclassified'], frontier['total'],
          frontier['owner_unknown']) == (737, 137, 137, 0), 'exact parent capacity frontier')
    plan = recorded['successor_plan']
    need(plan['candidate'] == checkpoint['candidate'] and
         (plan['parent_unknown_count'], plan['current_unknown_count'],
          plan['newly_classified_count'], plan['full_inventory_count']) == (139, 137, 2, 874),
         'saved current737 successor plan, not historical148 current_plan')
    return frontier, checkpoint, recorded


def current_report(full, root=ROOT, *, parent_audit, summary_parent, party_parent,
                   boundary_parent, runtime_parent, lifetime_parent, callback_parent, baseline_audit):
    """chain.parent_audits(*23入力)を**展開し、旧容量validatorと計算を再利用する。"""
    frontier, checkpoint, recorded = read_inputs(root)
    need(identity(chain.canonical(parent_audit)) == PARENT_AUDIT_ID,
         'all737 parent fields and twelve complete proof families remain exact')
    need(all(a[k] is False for a in (parent_audit, full) for k in chain.FLAGS),
         'capacity-only inputs cannot claim lease or indirect retirement')
    need((parent_audit['classified'], parent_audit['unclassified']) == (737, 137) and
         parent_audit['candidate'] == frontier['candidate'], 'whole737 parent candidate')
    need([h for h in parent_audit['hits'] if not h['accepted']] ==
         [r['hit'] for r in frontier['rows']], 'every immediate-parent unknown field exact')
    need(all(full.get(name) == parent_audit[name] for name in chain.INHERITED_NAMES),
         'every inherited proof namespace remains completely unchanged')
    # 容量原本とsource-bound式は変更しない。保存済み137親planも別identityから照合する。
    result = prior.current_report(full, root, parent_audit=summary_parent, party_parent=party_parent,
                                  boundary_parent=boundary_parent, runtime_parent=runtime_parent,
                                  lifetime_parent=lifetime_parent, callback_parent=callback_parent,
                                  baseline_audit=baseline_audit)
    _, _, placement, _ = base_capacity.read_inputs(root)
    donor = result['donor']
    domain = Span(donor['address'], donor['address'] + donor['size'])
    request_bytes = result['controller']['total_allocated_bytes']
    recorded_plan = plan_materialized_successor(summary_parent, parent_audit, placement,
                                                domain, request_bytes, 4)
    recorded_plan['parent_frontier_identity'] = copy.deepcopy(prior.INPUTS[prior.FRONTIER])
    need(recorded_plan == recorded['successor_plan'], 'entire saved current737 plan reproduced exactly')
    for key in ('candidate', 'donor', 'controller', 'current_plan', 'other_known_capacity', 'execution'):
        need(result[key] == recorded[key], 'all fixed capacity quantities and source identities retained')
    plan = plan_materialized_successor(parent_audit, full, placement, domain, request_bytes, 4)
    plan['parent_frontier_identity'] = copy.deepcopy(INPUTS[FRONTIER])
    need(plan['protected'] == [{'address': donor['address'], 'size': 15118}] and
         plan['total_unprotected_bytes'] == plan['largest_aligned_gap_bytes'] == 0 and
         plan['lease_eligible'] is False and plan['lease_authorized'] is False and
         plan['rom_mutation_performed'] is False, 'entire donor stays protected without any lease')
    need(request_bytes == 6528 and result['other_known_capacity']['sum_upper_bound_bytes'] == 1315 and
         plan['owner_count'] == 115 and donor['size'] == 15118,
         'unchanged measured controller known-capacity and entire donor-owner bounds')
    result['fixed735_summary_parent_successor_plan'] = result['successor_plan']
    result['successor_plan'] = plan
    result['immediate_parent_input_bindings'] = copy.deepcopy(INPUTS)
    result['immediate_parent_checkpoint'] = CHECKPOINT
    result['immediate_parent_capacity_identity'] = copy.deepcopy(INPUTS[PARENT_PLAN])
    result['immediate_parent_recorded_successor_plan'] = copy.deepcopy(recorded_plan)
    return result
