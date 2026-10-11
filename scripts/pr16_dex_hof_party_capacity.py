"""733親の全証拠と独立141frontierへ束縛する容量照合。旧lease規則は不変。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pr16_dex_hof_party_chain as chain
import pr16_dex_hof_partial_space as base_capacity
import pr16_dex_hof_boundary_capacity as prior
from pr16_dex_hof_donor import identity, need
from pr16_dex_hof_space_intervals import Span, plan_materialized_successor

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = 'content/modernization/pr16_dex_hof_boundary_references_evidence/unknown-frontier.json'
CHECKPOINT = chain.PARENT_CHECKPOINT
INPUTS = {
    FRONTIER: {'size': 61763, 'sha256': 'ef91033ce77034dffa6b1155011bbe7df86f26df79c5ea8f630288cae8462a1f'},
    CHECKPOINT: chain.PARENT_CHECKPOINT_ID,
}
PARENT_AUDIT_ID = chain.PARENT_AUDIT_ID


def all_input_bindings():
    """全歴史的容量原本のidentityを正規化し、重複が同一の場合だけ統合する。"""
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
        need(identity(raw) == expected and raw.endswith(b'\n'), 'entire independent733 capacity input')
        values[path] = json.loads(raw)
    frontier, checkpoint = values[FRONTIER], values[CHECKPOINT]
    need(checkpoint['unknown_identity'] == INPUTS[FRONTIER] and
         checkpoint['candidate'] == frontier['candidate'], 'measured parent unknown envelope')
    need((checkpoint['classified'], checkpoint['unclassified'], frontier['total'],
          frontier['owner_unknown']) == (733, 141, 141, 0), 'exact parent capacity frontier')
    return frontier, checkpoint


def current_report(full, root=ROOT, *, parent_audit, boundary_parent, runtime_parent, lifetime_parent,
                   callback_parent, baseline_audit):
    """chain.parent_audits(*19入力)を**展開して受け取る。旧容量validatorを再利用する。"""
    frontier, checkpoint = read_inputs(root)
    need(identity(chain.canonical(parent_audit)) == PARENT_AUDIT_ID,
         'all733 parent fields and ten complete proof families remain exact')
    need(all(a[k] is False for a in (parent_audit, full) for k in chain.FLAGS),
         'capacity-only inputs cannot claim lease or indirect retirement')
    need((parent_audit['classified'], parent_audit['unclassified']) == (733, 141) and
         parent_audit['candidate'] == frontier['candidate'], 'whole733 parent candidate')
    need([h for h in parent_audit['hits'] if not h['accepted']] ==
         [r['hit'] for r in frontier['rows']], 'every immediate-parent unknown field exact')
    need(all(full.get(name) == parent_audit[name] for name in chain.INHERITED_NAMES),
         'every inherited proof namespace remains completely unchanged')
    # 既受入規則とsource-bound容量式を一切変更せず、歴史的726根から計算する。
    result = prior.current_report(full, root, parent_audit=boundary_parent, runtime_parent=runtime_parent,
                                  lifetime_parent=lifetime_parent,
                                  callback_parent=callback_parent, baseline_audit=baseline_audit)
    _, _, placement, _ = base_capacity.read_inputs(root)
    donor = result['donor']
    plan = plan_materialized_successor(
        parent_audit, full, placement, Span(donor['address'], donor['address'] + donor['size']),
        result['controller']['total_allocated_bytes'], 4)
    plan['parent_frontier_identity'] = copy.deepcopy(INPUTS[FRONTIER])
    need(plan['total_unprotected_bytes'] == 0 and plan['lease_eligible'] is False and
         plan['lease_authorized'] is False, 'unbounded unknowns never create a lease')
    need(result['controller']['total_allocated_bytes'] == 6528 and
         result['other_known_capacity']['sum_upper_bound_bytes'] == 1315 and
         plan['owner_count'] == 115 and donor['size'] == 15118,
         'unchanged measured controller known-capacity and entire donor-owner bounds')
    result['fixed732_boundary_parent_successor_plan'] = result['successor_plan']
    result['successor_plan'] = plan
    result['immediate_parent_input_bindings'] = copy.deepcopy(INPUTS)
    result['immediate_parent_checkpoint'] = CHECKPOINT
    return result
