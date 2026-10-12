"""746親の全証拠・128frontier・保存容量planへ束縛する。旧lease規則は不変。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pr16_dex_hof_field_consumer_batch_chain as chain
import pr16_dex_hof_partial_space as base_capacity
import pr16_dex_hof_root_batch_capacity as prior
from pr16_dex_hof_donor import identity, need
from pr16_dex_hof_space_intervals import Span, aligned, complement, plan_materialized_successor

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = 'content/modernization/pr16_dex_hof_root_batch_evidence/unknown-frontier.json'
CHECKPOINT = chain.PARENT_CHECKPOINT
PARENT_PLAN = 'content/modernization/pr16_dex_hof_root_batch_evidence/partial-space.json'
INPUTS = {
    FRONTIER: {'size': 56095, 'sha256': '8e463394c3ff6160d15f4d89d8b97153766e7c1b5af13d51d323abdb1ad5e2c0'},
    CHECKPOINT: chain.PARENT_CHECKPOINT_ID,
    PARENT_PLAN: {'size': 22817, 'sha256': '895250c668b17b8063c23fd87871c4e6a464f0885fe559eb37d9cf581e4184df'},
}
PARENT_AUDIT_ID = chain.PARENT_AUDIT_ID
CURRENT_OWNER_AUDIT_ID = {'size': 282800, 'sha256': '753f0046c1d01f7f12bed94cf2a85e2b8efe96a97e312bd248726e2fc051ed1d'}


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
             'entire independent746 capacity input in LF')
        values[path] = json.loads(raw)
    frontier, checkpoint, recorded = (values[p] for p in (FRONTIER, CHECKPOINT, PARENT_PLAN))
    need(checkpoint['unknown_identity'] == INPUTS[FRONTIER] and
         checkpoint['capacity_identity'] == INPUTS[PARENT_PLAN] and
         checkpoint['candidate'] == frontier['candidate'] == recorded['candidate'],
         'measured parent unknown and capacity envelopes')
    need((checkpoint['classified'], checkpoint['unclassified'], frontier['total'],
          frontier['owner_unknown']) == (746, 128, 128, 0), 'exact parent capacity frontier')
    plan = recorded['successor_plan']
    need(plan['candidate'] == checkpoint['candidate'] and
         (plan['parent_unknown_count'], plan['current_unknown_count'],
          plan['newly_classified_count'], plan['full_inventory_count']) == (131, 128, 3, 874),
         'saved current746 successor plan, not historical148 current_plan')
    return frontier, checkpoint, recorded


def current_report(full, root=ROOT, *, parent_audit, root_batch_parent, help_batch_parent, remaining_consumers_parent, summary_parent, party_parent,
                   boundary_parent, runtime_parent, lifetime_parent, callback_parent, baseline_audit):
    """chain.parent_audits(*29入力)を**展開し、旧容量validatorと計算を再利用する。"""
    frontier, checkpoint, recorded = read_inputs(root)
    chain.validate_materialized(parent_audit, full)
    need(identity(chain.canonical(parent_audit)) == PARENT_AUDIT_ID,
         'all746 parent fields and fifteen complete proof families remain exact')
    need(all(a[k] is False for a in (parent_audit, full) for k in chain.FLAGS),
         'capacity-only inputs cannot claim lease or indirect retirement')
    need((parent_audit['classified'], parent_audit['unclassified']) == (746, 128) and
         parent_audit['candidate'] == frontier['candidate'], 'whole746 parent candidate')
    need([h for h in parent_audit['hits'] if not h['accepted']] ==
         [r['hit'] for r in frontier['rows']], 'every immediate-parent unknown field exact')
    need(all(full.get(name) == parent_audit[name] for name in chain.INHERITED_NAMES),
         'every inherited proof namespace remains completely unchanged')
    # 旧Root validatorには746親だけを渡す。新field consumer deltaを旧証拠として解釈しない。
    # 容量原本とsource-bound式は変更しない。保存済み128親planも別identityから照合する。
    result = prior.current_report(parent_audit, root, parent_audit=root_batch_parent, help_batch_parent=help_batch_parent,
                                  remaining_consumers_parent=remaining_consumers_parent, summary_parent=summary_parent,
                                  party_parent=party_parent,
                                  boundary_parent=boundary_parent, runtime_parent=runtime_parent,
                                  lifetime_parent=lifetime_parent, callback_parent=callback_parent,
                                  baseline_audit=baseline_audit)
    _, _, placement, _ = base_capacity.read_inputs(root)
    donor = result['donor']
    domain = Span(donor['address'], donor['address'] + donor['size'])
    request_bytes = result['controller']['total_allocated_bytes']
    recorded_plan = plan_materialized_successor(root_batch_parent, parent_audit, placement,
                                                domain, request_bytes, 4)
    recorded_plan['parent_frontier_identity'] = copy.deepcopy(prior.INPUTS[prior.FRONTIER])
    need(recorded_plan == recorded['successor_plan'], 'entire saved current746 plan reproduced exactly')
    for key in ('candidate', 'donor', 'controller', 'current_plan', 'other_known_capacity', 'execution',
                'current_owner_binding', 'root_batch_runtime_boundary'):
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
    result['fixed746_root_batch_successor_plan'] = result['successor_plan']
    result['successor_plan'] = plan
    result['fixed746_root_batch_point_only_projection'] = result['successor_point_only_projection']
    targets = sorted({row['target'] for row in full['hits'] if not row['accepted']})
    gaps = complement(domain, tuple(Span(target, target + 1) for target in targets))
    usable = aligned(gaps, 4)
    result['successor_point_only_projection'] = dict(
        unique_targets=len(targets), total_gap_bytes=sum(gap.size for gap in gaps),
        largest_gap_bytes=max((gap.size for gap in gaps), default=0),
        largest_aligned_gap_bytes=max((gap.size for gap in usable), default=0),
        current_unknown_targets_retained_assumption=True, safe_to_lease=False,
        indirect_or_owner_protection_omitted_for_projection_only=True)
    result['field_consumer_batch_runtime_boundary'] = runtime_boundary()
    result['current_owner_binding'] = current_owner_binding(placement)
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
        'indirect_reference_completeness_proven': False,
        'target_retirement_proven': False,
        'explicit_owner_transfer_proven': False,
        'natural_play_universal_reachability_claimed': False,
        'donor_safe_bytes': 0,
        'donor_leased': False,
        'formal_rom_changed': False,
        'formal_save_changed': False,
    }


def current_owner_binding(placement):
    """最新generation_writerの実owner全fieldを束縛し、旧owner hashを代用しない。"""
    need(identity(chain.canonical(placement)) == CURRENT_OWNER_AUDIT_ID,
         'all fields of latest generation writer owner checkpoint')
    path = 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
    owner_rows = placement['placement']['owner_byte_audit']
    preserved = placement['placement']['preserved_hof_sections']
    save_count = len(placement['link']['sections']) + len(preserved)
    need(len(owner_rows) == 115 and save_count == 52 and placement['link']['free_bytes'] == 804,
         'latest115 actual owners and52 save owners with804 free bytes')
    return dict(path=path, checkpoint_identity=dict(zip(('size', 'sha256'), base_capacity.INPUTS[path])),
                actual_owner_rows_identity=identity(chain.canonical(owner_rows)),
                actual_owner_count=115, save_owner_count=save_count, save_free_bytes=804,
                donor_lease_or_owner_transfer_performed=False)
