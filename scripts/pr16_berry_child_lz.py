#!/usr/bin/env python3
"""子機停止点の後続LZ入力を検証。発行命令と圧縮tokenを混同しない。"""
from __future__ import annotations
import hashlib
import json

CHILD, START, SIZE = 0x02000000, 0x086C48AC, 13456
STREAM, DEST, TARGET = CHILD + 0x2F0, CHILD + 0x10000, CHILD + 0x913
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
IMAGE = {'size': 13456, 'sha256': '1b23d91f9b5ca8759a7608516ed9bf986488bc002d14ddaa3add469bb0afb20f'}
LIBRARY = {'size': 1968536, 'sha256': '0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def decode_lz(raw, source=STREAM, target=TARGET, max_output=0x20000):
    """GBA LZ10を独立展開。境界越え/無効参照は切り詰めず拒否する。"""
    need(type(raw) is bytes and len(raw) >= 4 and raw[0] == 0x10, 'LZ10 header')
    size = int.from_bytes(raw[1:4], 'little')
    need(0 < size <= max_output, '有限出力長')
    out, pos, roles = bytearray(), 4, []
    counts = {'flags': 0, 'literal': 0, 'backreference': 0}
    def token(start, width, kind, before, after):
        hit = [i for i in range(4) if source + start <= target + i < source + start + width]
        if hit:
            roles.append({'source_address': source + start, 'size': width, 'kind': kind,
                          'target_byte_indexes': hit, 'output_start': before, 'output_end': after,
                          'sha256': identity(raw[start:start + width])['sha256']})
    token(0, 4, 'header', 0, 0)
    while len(out) < size:
        need(pos < len(raw), '欠落flags')
        flags = raw[pos]; token(pos, 1, 'flags', len(out), len(out)); pos += 1
        counts['flags'] += 1
        for bit in range(7, -1, -1):
            if len(out) == size:
                break
            before, begin = len(out), pos
            if flags & (1 << bit):
                need(pos + 2 <= len(raw), '欠落参照token')
                word = int.from_bytes(raw[pos:pos + 2], 'big'); pos += 2
                length, distance = (word >> 12) + 3, (word & 4095) + 1
                need(distance <= len(out), '未生成領域への参照')
                need(len(out) + length <= size, '出力末尾を越える参照')
                for _ in range(length):
                    out.append(out[-distance])
                kind = 'backreference'
            else:
                need(pos < len(raw), '欠落literal')
                out.append(raw[pos]); pos += 1; kind = 'literal'
            counts[kind] += 1
            token(begin, pos - begin, kind, before, len(out))
    covered = sorted(i for row in roles for i in row['target_byte_indexes'])
    return bytes(out), {'source_start': source, 'source_end_exclusive': source + pos,
        'consumed_bytes': pos, 'output': identity(out), 'token_counts': counts,
        'target_roles': roles, 'target_byte_indexes': covered,
        'target_bytes_consumed': len(covered), 'input': identity(raw),
        'consumed_input': identity(raw[:pos]), 'trailing_bytes': len(raw) - pos}


def validate_native(n, parsed):
    fixed = {'schema_version': 1, 'native_processes': 1, 'child_header_boots': 0,
        'entry': CHILD + 0x120, 'stop_pc': CHILD + 0x1D8, 'swi11_count': 1,
        'sio_fixture_transactions': 8, 'sio_fixture_reads': 32, 'host_write_guards': 7,
        'host_writes_after_entry': 0, 'target_read_mask': 15, 'mapped_bytes': SIZE,
        'payload_read_first': STREAM, 'payload_read_end_exclusive': parsed['source_end_exclusive'],
        'payload_read_bytes': parsed['consumed_bytes'], 'payload_read_unique': parsed['consumed_bytes'],
        'payload_read_max_count': 1, 'output_write_bytes': parsed['output']['size'],
        'output_size': parsed['output']['size']}
    need(type(n) is dict, 'native object')
    need(all(type(n.get(k)) is int and n[k] == v for k, v in fixed.items()), 'native会計/全source read/出力境界')
    need(n.get('status') == 'CONDITIONAL_LZ_READER_OBSERVED', '実reader status')
    need(n.get('stop_reason') == 'RETURNED_FROM_SWI11', '実SWI帰還')
    for key in ('natural_link_transfer_proven', 'original_bios_cpu_execution_claimed',
                'formal_rom_changed', 'formal_save_changed', 'full_emulator_checkpoint_restored'):
        need(n.get(key) is False, '未証明の成功を主張しない: ' + key)
    for key in ('sio_reads_are_fixture', 'all_issued_code_equal_source', 'all_payload_reads_equal_source',
                'output_writes_sequential'):
        need(n.get(key) is True, '来歴/fixtureの明示: ' + key)
    need(type(n.get('steps')) is int and 0 < n['steps'] <= 500000, '有限native step')
    need(parsed['target_byte_indexes'] == [0, 1, 2, 3], '全4byte tokenを独立集計')
    seen = set()
    for row in n.get('issued_spans', []):
        need(set(row) == {'address', 'visits'} and type(row['address']) is int and
             type(row['visits']) is int and 0 < row['visits'] < 128, '発行span schema')
        at = row['address']
        need(CHILD + 0x120 <= at <= CHILD + 0x1D4 and at % 4 == 0 and at not in seen, '後続ARM範囲/重複')
        seen.add(at)
    need({CHILD + x for x in (0x120, 0x144, 0x1CC, 0x1D0, 0x1D4)} <= seen, '実callerからSWIまで')
    return True


def bind(raw, native, child, expanded):
    need(identity(raw) == CANDIDATE, '全候補SHA')
    body = raw[START - 0x08000000:START - 0x08000000 + SIZE]
    need(identity(body) == IMAGE == child['conditional_mapped_image'], '保存imageの来歴')
    old = child['native']
    need(old['stop_pc'] == CHILD + 0x120 and old['target_byte_mask'] == 0 and
         old['stop_reason'] == 'REPEATED_PC_BUDGET', '保存停止点')
    need(old['final_registers'] == {'r0': 0x04000120, 'r1': 0, 'r2': 0, 'r3': 0,
        'sp': 0x03007F00, 'lr': CHILD + 0x154, 'cpsr': 0x400000DF}, '保存live-in register')
    need(body[0x1D4:0x1D8] == bytes.fromhex('000011ef'), '実SWI11')
    need(int.from_bytes(body[0x1E8:0x1EC], 'little') == STREAM and
         int.from_bytes(body[0x1EC:0x1F0], 'little') == DEST, '実source/destination literal')
    out, parsed = decode_lz(body[STREAM - CHILD:])
    need(out == expanded, '独立parserとnative全出力byte一致')
    validate_native(native, parsed)
    for row in parsed['target_roles']:
        row['rom_address'] = START + row['source_address'] - CHILD
    return {'schema_version': 1, 'status': native['status'], 'candidate': CANDIDATE,
        'mapped_image': IMAGE, 'reader': parsed, 'native': native,
        'code_bindings': [{'child_address': row['address'], **identity(body[row['address'] - CHILD:row['address'] - CHILD + 4])}
                          for row in native['issued_spans']],
        'classification_candidate': 'CONDITIONAL_LZ77_SOURCE_TOKEN',
        'formal_classification_changes': 0, 'formal_classified': 788, 'formal_unclassified': 86,
        'selected_unknown_origins': 7, 'donor_safe_bytes': 0,
        'conditions_ja': ['保存PC/registerをlive-inとする新fixture。全core状態の復元ではない。',
            'SIOCNT/dataの32回の読出しは成功通信を模した明示入力。物理リンク/実BIOS転送の受入ではない。',
            'mGBA 0.10.2の実SWI11 HLE読出し/書込を透過計測。元BIOSのCPU実行ではない。',
            '対象は展開元token。0x02000913を未発行命令とした旧仮説を型証明へ使わない。',
            '正式台帳/安全容量は完了runの別受領と単独型差分まで増やさない。']}
