#!/usr/bin/env python3
"""現在のBerry imageを子機配置fixtureへ結び、実PCの全4byte発行だけを証拠化する。"""
from __future__ import annotations
import pr16_berry_transfer as parent

need, identity, encode = parent.need, parent.identity, parent.encode
CHILD, LABEL_SIZE, COPY_SIZE, TARGET = 0x02000000, 13452, 13456, 0x02000913
LIBRARY = {'size': 1968536, 'sha256': '0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'}
FALSE_KEYS = ('formal_rom_changed', 'formal_save_changed', 'natural_link_transfer_proven',
              'original_bios_cpu_execution_claimed')
REASONS = {'BUILTIN_BIOS_BUDGET', 'UNBOUND_CODE_ENTRY', 'REPEATED_PC_BUDGET',
           'CHILD_CODE_CHANGED', 'TARGET_FOUR_BYTES_ISSUED', 'FINITE_STEP_BUDGET'}


def validate_native(value):
    need(type(value) is dict, 'native object')
    need(all(value.get(k) is False for k in FALSE_KEYS), '未観測の成功/変更を主張しない')
    need(value.get('all_issued_child_bytes_equal_source') is True, '発行byteのROM来歴')
    expected = {'schema_version': 1, 'native_processes': 1, 'child_boot_fixtures': 1,
                'host_writes_after_entry': 0, 'host_write_guards': 7, 'mapped_bytes': COPY_SIZE,
                'parent_game_boots': 0}
    need(all(type(value.get(k)) is int and value[k] == v for k, v in expected.items()), 'native固定会計')
    need(type(value.get('steps')) is int and 0 < value['steps'] <= 1000000, '有限step数')
    need(type(value.get('target_byte_mask')) is int and 0 <= value['target_byte_mask'] <= 15, '4byte mask')
    need(value.get('stop_reason') in REASONS, '既知の停止境界')
    need(type(value.get('issued_spans')) is list and 0 < len(value['issued_spans']) <= LABEL_SIZE // 2, '発行span有限集合')
    seen, mask, spans = set(), 0, []
    for row in value['issued_spans']:
        need(type(row) is dict and set(row) == {'address', 'width_mask', 'visits'}, 'span閉schema')
        at, widths, visits = (row[k] for k in ('address', 'width_mask', 'visits'))
        need(all(type(x) is int for x in (at, widths, visits)) and widths in (2, 4, 6) and
             0 < visits <= 131073 and at not in seen, 'span型/重複/visit予算')
        seen.add(at)
        for width in (2, 4):
            if not widths & width:
                continue
            need(CHILD <= at and at + width <= CHILD + LABEL_SIZE and at % width == 0, '整列した完全発行幅')
            for index in range(4):
                if at <= TARGET + index < at + width:
                    mask |= 1 << index
            spans.append({'child_address': at, 'rom_address': parent.START + at - CHILD, 'size': width})
    need(mask == value['target_byte_mask'], '全4byteを実発行spanから独立集計')
    accepted = mask == 15
    need(value.get('status') == ('CONDITIONAL_CHILD_READER_OBSERVED' if accepted else 'BOUNDED_CHILD_FRONTIER'), '実観測とstatus一致')
    need((value['stop_reason'] == 'TARGET_FOUR_BYTES_ISSUED') == accepted, '未発行を成功にしない')
    return {'target_bytes_issued': mask.bit_count(), 'all_four_bytes_issued': accepted,
            'issued_spans': spans, 'formal_classification_changes': 0,
            'donor_safe_bytes': 0, 'natural_transfer_proven': False, 'root_mapping_is_fixture': True}


def bind(raw, native, transfer):
    need(identity(raw) == parent.parent.CANDIDATE, '現候補全SHA')
    span = transfer['transfer_interval']
    need(span == parent.interval(parent.START, parent.END) and transfer['profile_count'] == 13 and
         transfer['current_task_payload_binding_proven'] is True, '保存転送境界。再解釈しない')
    body = parent.parent.section(raw, parent.BASE, parent.START, COPY_SIZE)
    need(parent.parent.arm_header(body)['relative_entry_if_arm'] == 256, '現在のARM root入口')
    origin = parent.parent.section(raw, parent.BASE, parent.HIT, 4)
    need(identity(origin) == parent.parent.HIT_ID, '対象全4byte来歴')
    result = validate_native(native)
    for row in result['issued_spans']:
        row.update(identity(parent.parent.section(raw, parent.BASE, row['rom_address'], row['size'])))
    return {'schema_version': 1, 'status': native['status'], 'candidate': parent.parent.CANDIDATE,
        'origin': {'address': parent.HIT, **identity(origin)}, 'child_origin': TARGET,
        'label_image': identity(body[:LABEL_SIZE]), 'conditional_mapped_image': identity(body),
        'tail_outside_label': identity(body[LABEL_SIZE:]), 'mapping': {'rom_start': parent.START,
        'child_start': CHILD, 'size': COPY_SIZE, 'entry': CHILD, 'initial_cpsr': 0xDF,
        'initial_sp': 0x03007F00, 'initial_r0_r12': 0, 'cartridge_model': 'unchanged current candidate'},
        'reader': result, 'native': native, 'formal_classified': 788, 'formal_unclassified': 86,
        'selected_unknown_origins': 7, 'donor_safe_bytes': 0,
        'conditions_ja': ['成功した実転送ではなく、現Taskが渡すimageを子機RAMへ事前配置した条件付きfixture。',
            '現候補ROMは子機側cartモデルとして読取専用。Ruby/Sapphire実カートリッジを再現していない。',
            'ARM header entryから同一image byteをmGBAで発行。entry後のhost bus/raw/register書込7APIを拒否。',
            '既存mGBA builtin BIOSを使用。元BIOS CPU/実リンク/IRQ全寿命/実画面/ゲーム保存の受入ではない。',
            '観測済み発行spanと単なるbyte形を区別する。未発行なら型不明を維持し、外部run受領前に正式台帳を増やさない。']}
