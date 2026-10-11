"""741親の全証拠・133frontier・保存容量planへ束縛する。旧lease規則は不変。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pr16_dex_hof_help_batch_chain as chain
import pr16_dex_hof_partial_space as base_capacity
import pr16_dex_hof_remaining_consumers_capacity as prior
from pr16_dex_hof_donor import identity, need
from pr16_dex_hof_space_intervals import Span, plan_materialized_successor

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = 'content/modernization/pr16_dex_hof_remaining_consumers_evidence/unknown-frontier.json'
CHECKPOINT = chain.PARENT_CHECKPOINT
PARENT_PLAN = 'content/modernization/pr16_dex_hof_remaining_consumers_evidence/partial-space.json'
INPUTS = {
    FRONTIER: {'size': 58275, 'sha256': '55bee1d2fbe5f830cd23acb58ec0f09d56ac0e4d2fe7af9ea798894a14c13adf'},
    CHECKPOINT: chain.PARENT_CHECKPOINT_ID,
    PARENT_PLAN: {'size': 17993, 'sha256': 'dea8c62dfb5e9b608ead9ade52bf1a907e29920d946990146f15ba4e58094115'},
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
             'entire independent741 capacity input in LF')
        values[path] = json.loads(raw)
    frontier, checkpoint, recorded = (values[p] for p in (FRONTIER, CHECKPOINT, PARENT_PLAN))
    need(checkpoint['unknown_identity'] == INPUTS[FRONTIER] and
         checkpoint['capacity_identity'] == INPUTS[PARENT_PLAN] and
         checkpoint['candidate'] == frontier['candidate'] == recorded['candidate'],
         'measured parent unknown and capacity envelopes')
    need((checkpoint['classified'], checkpoint['unclassified'], frontier['total'],
          frontier['owner_unknown']) == (741, 133, 133, 0), 'exact parent capacity frontier')
    plan = recorded['successor_plan']
    need(plan['candidate'] == checkpoint['candidate'] and
         (plan['parent_unknown_count'], plan['current_unknown_count'],
          plan['newly_classified_count'], plan['full_inventory_count']) == (137, 133, 4, 874),
         'saved current741 successor plan, not historical148 current_plan')
    return frontier, checkpoint, recorded


def current_report(full, root=ROOT, *, parent_audit, remaining_consumers_parent, summary_parent, party_parent,
                   boundary_parent, runtime_parent, lifetime_parent, callback_parent, baseline_audit):
    """chain.parent_audits(*25入力)を**展開し、旧容量validatorと計算を再利用する。"""
    frontier, checkpoint, recorded = read_inputs(root)
    chain.validate_materialized(parent_audit, full)
    need(identity(chain.canonical(parent_audit)) == PARENT_AUDIT_ID,
         'all741 parent fields and thirteen complete proof families remain exact')
    need(all(a[k] is False for a in (parent_audit, full) for k in chain.FLAGS),
         'capacity-only inputs cannot claim lease or indirect retirement')
    need((parent_audit['classified'], parent_audit['unclassified']) == (741, 133) and
         parent_audit['candidate'] == frontier['candidate'], 'whole741 parent candidate')
    need([h for h in parent_audit['hits'] if not h['accepted']] ==
         [r['hit'] for r in frontier['rows']], 'every immediate-parent unknown field exact')
    need(all(full.get(name) == parent_audit[name] for name in chain.INHERITED_NAMES),
         'every inherited proof namespace remains completely unchanged')
    # 容量原本とsource-bound式は変更しない。保存済み133親planも別identityから照合する。
    result = prior.current_report(full, root, parent_audit=remaining_consumers_parent, summary_parent=summary_parent,
                                  party_parent=party_parent,
                                  boundary_parent=boundary_parent, runtime_parent=runtime_parent,
                                  lifetime_parent=lifetime_parent, callback_parent=callback_parent,
                                  baseline_audit=baseline_audit)
    _, _, placement, _ = base_capacity.read_inputs(root)
    donor = result['donor']
    domain = Span(donor['address'], donor['address'] + donor['size'])
    request_bytes = result['controller']['total_allocated_bytes']
    recorded_plan = plan_materialized_successor(remaining_consumers_parent, parent_audit, placement,
                                                domain, request_bytes, 4)
    recorded_plan['parent_frontier_identity'] = copy.deepcopy(prior.INPUTS[prior.FRONTIER])
    need(recorded_plan == recorded['successor_plan'], 'entire saved current741 plan reproduced exactly')
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
    result['fixed737_remaining_consumers_parent_successor_plan'] = result['successor_plan']
    result['successor_plan'] = plan
    result['help_batch_runtime_boundary'] = runtime_boundary()
    result['immediate_parent_input_bindings'] = copy.deepcopy(INPUTS)
    result['immediate_parent_checkpoint'] = CHECKPOINT
    result['immediate_parent_capacity_identity'] = copy.deepcopy(INPUTS[PARENT_PLAN])
    result['immediate_parent_recorded_successor_plan'] = copy.deepcopy(recorded_plan)
    return result


def runtime_boundary():
    """保存済み容量の再測定ではなく、未接続runtimeの禁止境界を明示する。"""
    return {
        'status': 'UNPROVEN_RUNTIME_BOUNDARY_NO_ALLOCATION_OR_WIRING',
        'controller_measured_bytes': 6528,
        'controller_runtime_wired': False,
        'heap_scratch_bytes': 13352,
        'heap_lifetime_proven': False,
        'universal_irq_or_heap_lifetime_claimed': False,
        'stock_save_backup_bytes': 53300,
        'release_before_stock_save_entry': 0x0804B85C,
        'stock_save_boundary_crossing_allowed': False,
        'all_save_entry_heap_ready_proven': False,
        'synchronous_nonreentrant_use_proven': False,
        'donor_safe_bytes': 0,
        'donor_leased': False,
        'formal_rom_changed': False,
        'formal_save_changed': False,
    }
