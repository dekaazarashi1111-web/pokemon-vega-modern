"""現行Stage61のcompiler・payload・patch生成元を使う状態namespace専用fixture。"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence


SCOPE = 'STATE_NAMESPACE_UNIT_FIXTURE_ONLY'


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def covered(spans: Sequence[Mapping[str, int]], declarations: Sequence[Mapping[str, Any]]) -> bool:
    """隣接宣言の和集合で全変更byteを覆い、未宣言領域を許可しない。"""
    intervals: list[list[int]] = []
    for row in sorted(declarations, key=lambda item: int(item['start'])):
        start, end = int(row['start']), int(row['end_exclusive'])
        if start < 0 or end <= start:
            raise ValueError('invalid declared interval')
        if intervals and start <= intervals[-1][1]:
            intervals[-1][1] = max(intervals[-1][1], end)
        else:
            intervals.append([start, end])
    return all(any(start <= int(span['start']) < int(span['end_exclusive']) <= end
                   for start, end in intervals) for span in spans)


def build_artifacts(*, root: Path, config: Mapping[str, Any], stage60: bytes,
                    output_raw: bytes, payload_offset: int, payload_size: int,
                    data_address: int, data_size: int, code_offset: int, code: bytes,
                    symbols: Mapping[str, int], nm_text: str,
                    runtime_toolchain: Mapping[str, Any], declared: Sequence[Mapping[str, Any]],
                    semantic_report: Mapping[str, Any], namespace_report: Mapping[str, Any],
                    blob_meta: Mapping[str, Any], map_section_consumer_proof: Mapping[str, Any]) -> dict[str, bytes]:
    from scripts import build_stage61_display_npc_event_audit as builder
    from tools import stage61_state_namespace_collision_audit as validator
    expected = config['inputs']['stage60_rom']
    if len(stage60) != expected['size'] or _sha(stage60) != expected['sha256'] \
            or len(output_raw) != len(stage60):
        raise ValueError('state fixture input identity differs')
    start = payload_offset + code_offset
    payload = output_raw[payload_offset:payload_offset + payload_size]
    if len(payload) != payload_size or output_raw[start:start + len(code)] != code:
        raise ValueError('compiled code is not installed at its linked ROM address')
    source_raw = (root / config['runtime_source']).read_bytes()
    source_contract = validator.validate_stage61_normal_save_cow_source(source_raw.decode('utf-8'))
    object_contract = validator._stage61_normal_save_cow_object_contract(
        output_raw, symbols, builder.GBA_BASE + start, len(code))
    spans = builder._changed_spans(stage60, output_raw)
    if not covered(spans, declared):
        raise ValueError('state fixture changes bytes outside declared regions')
    state_contract = builder._persistent_state_compatibility_metadata()
    validator._validate_stage61_normal_save_cow_metadata(state_contract['normal_save_copy_on_write'])
    runtime = {
        'source': config['runtime_source'], 'source_sha256': _sha(source_raw),
        'code_sha256': _sha(code), 'code_size': len(code), 'symbols': dict(symbols),
        'toolchain_manifest_sha256': runtime_toolchain['manifest_sha256'],
        'toolchain': deepcopy(dict(runtime_toolchain)),
    }
    semantics = deepcopy(dict(semantic_report))
    semantics.update({
        'status_scope': SCOPE, 'stage61_namespace_policy': deepcopy(dict(namespace_report)),
        'stage61_bill_sevii_scope_guard': deepcopy(blob_meta['bill_sevii_scope_guard']),
    })
    audit = {
        'schema_version': config['schema_version'], 'task': config['task'], 'stage': config['stage'],
        'status': 'PASS', 'status_scope': SCOPE, 'release_profile': 'STATE_NAMESPACE_FIXTURE',
        'strict_audit_status': 'NOT_RUN_IN_UNIT_FIXTURE', 'gameplay_release': False,
        'input_sha256': _sha(stage60), 'rom_sha256': _sha(output_raw), 'runtime': runtime,
        'namespace_policy': deepcopy(dict(namespace_report)),
        'bill_sevii_scope_guard': deepcopy(blob_meta['bill_sevii_scope_guard']),
        'persistent_state_compatibility': state_contract,
        'normal_save_source_proof': source_contract,
        'normal_save_object_proof': object_contract,
        'map_section_consumer_policy': {
            **deepcopy(dict(map_section_consumer_proof)),
            'selected_site_ids': list(builder.MAP_SECTION_POLICY_SELECTED_SITE_IDS),
            'quest_log_project_crosswalk': deepcopy(blob_meta['quest_log_project_crosswalk']),
            'raid_flag_range': {
                'start': '0x15C0', 'end_inclusive': '0x162C', 'count': 109,
                'legacy_collision_range': '0x1800..0x186C',
                'binary_base_patch_count': len(builder.CFRU_RAID_FLAG_BASE_PATCHES),
                'binary_end_patch_count': len(builder.CFRU_RAID_FLAG_END_PATCHES),
                'api_adapter_literal_count': len(builder.CFRU_RAID_FLAG_API_LITERALS),
            },
        },
        'change_audit': {
            'changed_span_count': len(spans), 'outside_declared_span_count': 0,
            'declared_patch_count': len(declared), 'spans': spans,
            'declarations': deepcopy(list(declared)),
        },
    }
    outputs = config['outputs']
    metadata = {
        'schema_version': config['schema_version'], 'task': config['task'], 'stage': config['stage'],
        'status': 'PASS', 'status_scope': SCOPE, 'release_profile': 'STATE_NAMESPACE_FIXTURE',
        'strict_audit_status': 'NOT_RUN_IN_UNIT_FIXTURE', 'gameplay_release': False,
        'input': {'path': expected['path'], 'sha256': _sha(stage60), 'size': len(stage60)},
        'output': {'path': outputs['rom'], 'sha256': _sha(output_raw), 'size': len(output_raw)},
        'payload': {
            'address': builder.GBA_BASE + payload_offset, 'offset': payload_offset,
            'size': len(payload), 'sha256': _sha(payload), 'data_address': data_address,
            'data_size': data_size, 'code_address': builder.GBA_BASE + start, 'code_size': len(code),
        },
        'runtime': runtime, 'audit': audit,
    }
    return {
        outputs['rom']: output_raw, outputs['metadata']: builder._stable(metadata),
        outputs['audit']: builder._stable(audit),
        str(validator.STAGE61_EVENT_SEMANTIC_RELATIVE): builder._stable(semantics),
        outputs['symbols']: builder._stable({'symbols': dict(symbols), 'nm': nm_text,
                                           'toolchain_manifest_sha256': runtime_toolchain['manifest_sha256']}),
    }
