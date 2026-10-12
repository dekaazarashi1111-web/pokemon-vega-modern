#!/usr/bin/env python3
"""完了済み子機LZ読出しから単一originの正式型差分を追加する。ROM不要。"""
from __future__ import annotations
import copy
import pr16_berry_child_lz as lz

need, identity, encode = lz.need, lz.identity, lz.encode
HIT = 0x086C51BF
HIT_ID = {'size': 4, 'sha256': '169f39595db6c1ad1cf83234441b8a0ec54dc2a94afab2cc05d80713fb0a0a41'}
CLASSIFICATION = 'FALSE_POSITIVE_TYPED_REFERENCE_LZ77_MULTIBOOT_SOURCE_TOKEN'
PARENT = 'content/modernization/pr16_sound_origin_reader_evidence'
OUTPUT = 'content/modernization/pr16_berry_lz_type_evidence'
PROOF_PATH = 'content/modernization/pr16_berry_child_lz_evidence/lz-reader.json'
RANGE = {'start': 0x09FED0C4, 'end_exclusive': 0x09FEEA44, 'size': 6528}


def validate_evidence(proof, measurement, receipt, accepted):
    need(accepted.get('status') == 'completed' and accepted.get('conclusion') == 'success' and
         accepted.get('id') == measurement.get('actions_run_id') == receipt.get('measurement_run_id') and
         accepted.get('source_head') == measurement.get('source_head') == receipt.get('measurement_source_head'),
         '外部完了run/測定/受領HEAD一致')
    need(receipt.get('measurement_completion_confirmed') is True and
         receipt.get('status') == 'LZ_READER_COMPLETION_BOUND_FORMAL_DELTA_PENDING', '正式型差分の受領gate')
    need(proof.get('status') == 'CONDITIONAL_LZ_READER_OBSERVED' and
         proof.get('classification_candidate') == 'CONDITIONAL_LZ77_SOURCE_TOKEN' and
         proof.get('candidate') == measurement.get('candidate') == lz.CANDIDATE and
         proof.get('mapped_image') == lz.IMAGE and proof.get('formal_classification_changes') == 0 and
         proof.get('donor_safe_bytes') == 0, '保存全候補/配置とreader gate')
    parsed, native = proof['reader'], proof['native']
    lz.validate_native(native, parsed)
    need(native.get('native_diagnostics') is not None and
         all(type(native['native_diagnostics'].get(k)) is int and native['native_diagnostics'][k] == 0
             for k in ('fatal','error','warn','stub','game_error')), 'native警告/error/stubゼロ')
    need(parsed['source_start'] == lz.STREAM and parsed['source_end_exclusive'] == lz.STREAM + parsed['consumed_bytes'] and
         lz.STREAM <= lz.TARGET < lz.TARGET + 4 <= parsed['source_end_exclusive'] <= lz.CHILD + lz.SIZE,
         '実消費区間内の対象4byte')
    covered = []
    for role in parsed['target_roles']:
        at, size = role['source_address'], role['size']
        need(role['kind'] in ('flags','literal','backreference') and type(at) is int and type(size) is int and
             size == (2 if role['kind'] == 'backreference' else 1) and
             lz.STREAM <= at < at + size <= parsed['source_end_exclusive'], '圧縮token幅/型/範囲')
        need(role['rom_address'] == lz.START + at - lz.CHILD and
             role['target_byte_indexes'] == [i for i in range(4) if at <= lz.TARGET+i < at+size], '各byteのROM/子機対応')
        need(type(role['sha256']) is str and len(role['sha256']) == 64 and
             all(c in '0123456789abcdef' for c in role['sha256']), 'token hash')
        covered.extend(role['target_byte_indexes'])
    need(sorted(covered) == [0,1,2,3], '対象全4byte・重複なし')
    return True


def promote(chain, frontier, window, proof, measurement, receipt, accepted):
    """既存874候補を再scanせず、保存された未知集合から1件だけ除外する。"""
    validate_evidence(proof, measurement, receipt, accepted)
    need(chain['candidate'] == frontier['candidate'] == proof['candidate'] == lz.CANDIDATE, '全候補identity')
    need(chain['classified'] == 788 and chain['unclassified'] == frontier['total'] == 86 and
         len(frontier['rows']) == 86 and window['remaining_count'] == len(window['remaining_rows']) == 7 and
         window['formal_classified'] == 788 and window['formal_unclassified'] == 86 and
         window['selected_range'] == RANGE and window['donor_safe_bytes'] == 0, '正式親788/86/窓7')
    addresses = [r['hit']['address'] for r in frontier['rows']]
    selected = [r['address'] for r in window['remaining_rows']]
    need(len(set(addresses)) == 86 and len(set(selected)) == 7 and selected == sorted(selected) and
         set(selected) <= set(addresses), '未知一意/選定集合整列')
    need(addresses.count(HIT) == selected.count(HIT) == 1, '単一未分類origin')
    hit = next(r['hit'] for r in frontier['rows'] if r['hit']['address'] == HIT)
    other = next(r for r in window['remaining_rows'] if r['address'] == HIT)
    need(all(hit[k] == other[k] for k in ('address','target','size','sha256','classification','accepted','kind')) and
         hit['classification'] == 'UNCLASSIFIED' and hit['accepted'] is False and
         {k: hit[k] for k in ('size','sha256')} == HIT_ID, '保存hit全identity')
    accepted_hit = copy.deepcopy(hit)
    accepted_hit.update(accepted=True, classification=CLASSIFICATION,
        reason='actual_child_arm_swi11_hle_reads_all_four_lz_source_token_bytes',
        evidence=[{'berry_lz_type_reference_chain_witness': 0}])
    claims = dict(formal_classification_accepted=True, conditional_finite_reader_only=True,
        actual_runtime_execution_observed=True, natural_entry_reachability_proven=False,
        natural_link_transfer_proven=False, original_bios_cpu_execution_claimed=False,
        all_alternative_readers_excluded=False, indirect_reference_completeness_claimed=False,
        donor_eligible=False, donor_leased=False, donor_safe_bytes=0, formal_rom_changed=False,
        formal_save_changed=False, accepted_measurement_replays=0, accepted_test_reruns=0)
    new_chain = dict(schema_version=1, namespace='berry_lz_type_reference_chain', candidate=lz.CANDIDATE,
        inherited_candidates=874, inherited_classified=788, inherited_unclassified=86, newly_classified=1,
        classified=789, unclassified=85, donor_safe_bytes=0, changes=[accepted_hit], claims=claims,
        parent_chain_path=PARENT+'/reference-chain.json', parent_chain_identity=identity(encode(chain)),
        parent_frontier_path=PARENT+'/unknown-frontier.json', parent_frontier_identity=identity(encode(frontier)),
        parent_window_path=PARENT+'/window-progress.json', parent_window_identity=identity(encode(window)),
        proof_path=PROOF_PATH, proof_identity=identity(encode(proof)), accepted_measurement=copy.deepcopy(accepted),
        status='ACCEPTED_SINGLE_LZ77_ORIGIN_CONDITIONAL_READER',
        witnesses=[{'origin':HIT, 'origin_identity':HIT_ID, 'target_roles':copy.deepcopy(proof['reader']['target_roles']),
            'native_identity':identity(encode(proof['native'])), 'mapped_image':lz.IMAGE,
            'conditional_sio_reads':32, 'original_bios_cpu_execution_claimed':False, 'donor_safe_bytes':0}])
    new_front = copy.deepcopy(frontier)
    new_front['rows'] = [r for r in new_front['rows'] if r['hit']['address'] != HIT]
    new_front.update(total=85, owner_unknown=sum(bool(r['owners']) for r in new_front['rows']),
                     unowned_unknown=sum(not r['owners'] for r in new_front['rows']))
    new_window = copy.deepcopy(window)
    new_window['remaining_rows'] = [r for r in new_window['remaining_rows'] if r['address'] != HIT]
    new_window.update(remaining_count=6, next_address=new_window['remaining_rows'][0]['address'],
        formal_classified=789, formal_unclassified=85, donor_safe_bytes=0,
        newly_classified_addresses=window['newly_classified_addresses']+[HIT],
        newly_classified_in_this_receipt=[HIT], status='SIX_SELECTED_ORIGINS_REMAIN_AFTER_BERRY_LZ',
        parent_window_identity=identity(encode(window)))
    return new_chain, new_front, new_window
