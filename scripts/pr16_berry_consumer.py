#!/usr/bin/env python3
"""保存済みBerry近傍を現Taskのownerと条件付きCPU fetchへ結ぶ境界定義。"""
from __future__ import annotations
import json
import re
import struct
import pr16_berry_origin as b

BASE = '4ed0e9e96aa8e5e1b8755225cc6565fd3e6d8e7f'
TASK = 'USER-20261011-BERRY-CONSUMER'
RAM_NAMES = {'gTasks', 'gMultibootStart', 'gMultibootStatus', 'gMultibootSize', 'gMultibootParam'}
HEADERS = {'include/task.h': '2f9f1c0d8755572d5ccc5c4190339ffaca2d4bbf',
           'include/gba/multiboot.h': 'a8bc8fddfd820eda38ba8fba4fd1db917bccc1ae'}
LIBRARY = {'size': 1968536, 'sha256': '0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'}


def strict(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            b.need(key not in out, 'JSON重複key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('非有限JSON')))


def ram_symbols(raw):
    found = {}
    for number, line in enumerate(raw.decode().splitlines(), 1):
        cells = line.split('\t')
        if len(cells) != 8 or cells[4] not in RAM_NAMES:
            continue
        b.need(cells[4] not in found and re.fullmatch(r'(?:0x)?[0-9A-Fa-f]{8}', cells[1]), 'RAM必要名重複/住所')
        address = int(cells[1], 16)
        b.need(0x02000000 <= address < 0x02040000 or 0x03000000 <= address < 0x03008000, '通常RAM内')
        b.need(address % 4 == 0, 'RAM整列')
        found[cells[4]] = {'address': address, 'line': number, 'row_sha256': b.identity(line.encode())['sha256']}
    b.need(found.keys() == RAM_NAMES, 'RAM必要名欠落')
    ranges = sorted((v['address'], v['address'] + (640 if k == 'gTasks' else 76 if k == 'gMultibootParam' else 4)) for k, v in found.items())
    b.need(all(end <= nxt for (_, end), (nxt, _) in zip(ranges, ranges[1:])), 'RAM owner重複')
    b.need(all((start >> 24) == ((end-1) >> 24) and end <= (0x02040000 if start < 0x03000000 else 0x03008000) for start,end in ranges), 'RAM終端越え')
    return found


def master_model(length, color, speed, probe=0, clients=2, wait=0):
    b.need(all(type(n) is int for n in (length,color,speed,probe,clients,wait)), '型付き整数')
    b.need(-16 <= length <= 0x40020 and 0 <= color <= 7 and -4 <= speed <= 4, '有限fixture値')
    early = bool(probe or not clients or wait)
    rounded = (length + 15) & ~15
    valid = not early and 0x100 <= rounded <= 0x40000
    i = ((color << 3) | (3-speed)) if speed < 0 else (0x38 | color) if speed == 0 else ((color << 3) | (speed-1))
    return {'accepted': valid, 'early_reset': early, 'source_pointer_written': not early,
            'rounded_length': rounded, 'palette_if_accepted': ((i & 0x3F) << 1) | 0x81 if valid else None,
            'probe_count_after': 0xD0 if valid else 0, 'check_wait_after': wait if valid else 15}


def decode_following(word):
    b.need(type(word) is int and 0 <= word <= 0xFFFF, '完全Thumb半語')
    # メモリload/storeや未定義/例外は単純な命令型分類へ昇格しない。
    if word & 0xE000 == 0x0000: return 'SHIFT_ADD_SUB'
    if word & 0xE000 == 0x2000: return 'IMMEDIATE_ALU'
    if word & 0xFC00 == 0x4000: return 'REGISTER_ALU'
    return None


def instruction_contract(raw):
    origin = b.HIT - b.START
    b.need(b.identity(raw) == {'size': 13452, 'sha256': '06acf5c00490ccbaaf8bf57a4d53d36d7df80495f894576f2acd3b9f1e9da052'}, '保存bundle全identity')
    start = (origin & ~1)
    hi, lo, following = struct.unpack_from('<HHH', raw, start)
    shapes = b.thumb_shapes(raw, b.START, b.HIT)
    b.need(len(shapes) == 1 and shapes[0]['address'] == b.HIT-1 and shapes[0]['hit_overlap_size'] == 3,
           '保存BL位置と3byte被覆')
    return {'mapped_base': 0x02000000, 'entry': 0x02000000,
            'halfword_addresses': [0x02000000+start+i for i in (0,2,4)],
            'instruction_identities': [b.identity(raw[start+i:start+i+2]) for i in (0,2,4)],
            'relative_bl_target': shapes[0]['conditional_target_if_executed_at_rom_address']-b.START,
            'following_class': decode_following(following), 'full_origin_size': 4,
            'actual_fetch_proven': False, 'natural_multiboot_transfer_proven': False}


def classify(native, contract):
    b.need(type(native) is dict and native.get('host_owner_verified') is True and
           native.get('host_init_cases') == 3 and type(native.get('host_init_cases')) is int and
           native.get('host_master_cases') == 13 and type(native.get('host_master_cases')) is int and
           native.get('nonowned_host_ram_unchanged') is True, '現owner実行の完全性')
    b.need(native.get('rom_writes') == 0 and type(native.get('rom_writes')) is int and
           native.get('real_saves') == 0 and type(native.get('real_saves')) is int, 'ROM/save不変')
    children = native.get('children')
    b.need(type(children) is list and len(children) == 2, '有限child fixture集合')
    accepted = []
    for case, row in enumerate(children):
        b.need(type(row) is dict and row.get('case') == case and type(row.get('case')) is int,
               'child case集合/重複')
        b.need(type(row.get('fetch_mask')) is int and 0 <= row['fetch_mask'] <= 7 and
               type(row.get('steps')) is int and 0 < row['steps'] <= 1500000 and
               row.get('mapped_original_bytes_unchanged_at_fetch') is True and
               row.get('entry_was_bundle_header') is True, 'child読取/identity/有限入口')
        if row['fetch_mask'] == 7 and row.get('bl_target_and_link_verified') is True and row.get('escaped_fixture_scope') is False and contract.get('following_class') is not None:
            accepted.append(case)
    return {'status': 'CONDITIONAL_MULTIBOOT_THUMB_ORIGIN_MEASURED' if accepted else 'CURRENT_MULTIBOOT_OWNER_BOUND_CHILD_FETCH_PENDING',
            'current_asset_owner_proven': True, 'actual_instruction_fetch_proven': bool(accepted),
            'accepted_child_cases': accepted, 'classification_eligible_after_completed_run_receipt': bool(accepted),
            'natural_entry_reachability_proven': False, 'natural_multiboot_transfer_proven': False,
            'all_aliases_or_indirect_readers_proven': False, 'donor_safe_bytes': 0}
