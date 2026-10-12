"""Apply explicit owner decisions to the current view, never to historical evidence."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

DECISION = 'content/modernization/p08_owner_approved_policy.json'
CONFIG = 'config/modernization_p03_stage74_supply.json'
CONFIG_SHA = 'aa3cdd33683be5799a30184dfa03485012f03fa5928d0c341028ff88722708fc'
DECISION_ID = 'OWNER-20260910-131832-ARCHIVE-PUBLIC'
COMMENT_ID = 5619397125
ARCHIVE = {
    'status': 'ADOPTED', 'scope': 'ADDITIONAL_MACHINE_TUTOR_ARCHIVE_ONLY',
    'entry': 'BAG_MOVE_MEMORY_ITEM_ONLY', 'required_flag': '0x082C',
    'required_flag_name': 'HALL_OF_FAME', 'price': 0,
    'early_game_archive_available': False, 'existing_other_memory_modes_unchanged': True,
    'runtime_change_required': False,
}
PUBLIC = {
    'visibility': 'public', 'owner_selected': True,
    'existing_tracked_originals_preserved': True, 'private_conversion_required': False,
    'existing_public_state_blocks_completion': False,
    'guard_disabled': False, 'guard_failure_relabelled_pass': False,
    'credentials_and_unintended_new_inputs_still_protected': True,
    'original_deletion_authorized': False, 'history_rewrite_authorized': False,
    'merge_authorized': False, 'active_baseline_switch_authorized': False,
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def same(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(root, name):
    path = root / name
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink input')
    return path.read_bytes()


def validate(policy, config):
    need(policy.get('decision_id') == DECISION_ID, 'unrecognized owner decision')
    need(policy.get('source_message_at_utc') == '2026-09-10T13:18:32Z', 'decision provenance differs')
    need(type(policy.get('pr_comment_id')) is int and policy['pr_comment_id'] == COMMENT_ID, 'approval comment differs')
    need(same(policy.get('archive_economy'), ARCHIVE), 'archive approval differs')
    need(same(policy.get('repository_policy'), PUBLIC), 'public policy differs')
    need(policy.get('p07_new_rows_adopted_by_this_decision') is False, 'no blanket P07 adoption')
    runtime = config['runtime']
    want_unlock = {key: ARCHIVE[key] for key in ('entry', 'required_flag', 'required_flag_name', 'early_game_archive_available')}
    need(same(runtime['unlock'], want_unlock), 'approved unlock differs from existing implementation')
    need(type(runtime['economy']['price']) is int and runtime['economy']['price'] == 0, 'approved fee differs')
    need(runtime['economy']['status'] == 'PROVISIONAL_REPLACEABLE', 'historical config was rewritten')


def load(root):
    decision = read(root, DECISION)
    historical = read(root, CONFIG)
    need(identity(historical)['sha256'] == CONFIG_SHA, 'historical Stage74 input changed')
    policy = decode(decision)
    validate(policy, decode(historical))
    return policy, {DECISION: identity(decision), CONFIG: identity(historical)}


def project_values(current, policy, bindings):
    """Monotonic, idempotent policy projection; no ROM or acceptance promotion."""
    result = copy.deepcopy(current)
    closures = {
        'ARCHIVE_ECONOMY': ('P03', '殿堂入り後・Bagのわざメモリー・無料を所有者が正式採用。通常思い出し等の条件は変更しない。'),
        'REPOSITORY_GUARD': ('P08', 'publicと既存追跡は所有者の意図した状態。非公開化・原本移動を完成条件にしない。過去guardの実測失敗は保持し、秘密情報等の検査は無効化しない。'),
    }
    pending = result['remaining_conditions']
    need(type(pending) is list and all(type(row) is dict and type(row.get('id')) is str for row in pending), 'invalid pending rows')
    need(len({row['id'] for row in pending}) == len(pending), 'duplicate pending IDs')
    # Existing decisions/evidence are retained; duplicate calls must not grow the view.
    closed = result.setdefault('closed_conditions', [])
    closed_ids = {row['id'] for row in closed}
    findings = result.setdefault('nonblocking_findings', [])
    finding_ids = {row['id'] for row in findings}
    for key, (phase, reason) in closures.items():
        if key not in closed_ids:
            closed.append({'id': key, 'phase': phase, 'closure_type': 'EXPLICIT_OWNER_POLICY_DECISION',
                           'decision_id': policy['decision_id'], 'success_evidence': DECISION, 'reason_ja': reason})
        if key == 'REPOSITORY_GUARD' and 'HISTORICAL_FULL_INDEX_GUARD' not in finding_ids:
            findings.append({'id': 'HISTORICAL_FULL_INDEX_GUARD', 'source_condition': key,
                             'result_relabelled': False, 'guard_disabled': False,
                             'reason_ja': '過去のguard結果は原本・protection記録どおり。意図した公開状態だけを理由に停止しない。新規の未承認混入は対象外。'})
    result['remaining_conditions'] = [row for row in pending if row['id'] not in closures]
    result['archive_economy'] = {**copy.deepcopy(policy['archive_economy']), 'decision_source': DECISION}
    result['repository_policy'] = {**copy.deepcopy(policy['repository_policy']), 'decision_source': DECISION}
    result.setdefault('source_bindings', {}).update(copy.deepcopy(bindings))
    return result


def project(current, root):
    policy, bindings = load(Path(root))
    return project_values(current, policy, bindings)
