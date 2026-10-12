#!/usr/bin/env python3
"""保存済み90未知から08397492を固定する。symbol近傍は候補であり型/容量ではない。"""
from __future__ import annotations
import copy
import hashlib
import json
import re

TARGET = 0x08397492
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
HIT = {'accepted': False, 'address': TARGET, 'classification': 'UNCLASSIFIED',
       'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS', 'owner_candidates': [],
       'reason': 'no_complete_typed_asset_consumer_witness',
       'sha256': '596fb6d08572fb73f6c9f5d1dc6d33fa1dd8b3226e1b235ca564bee8d87d5a43',
       'size': 4, 'target': 167707392}
SYMBOL_SOURCE = {'repository': 'ComplexRobot/frlg-sym',
    'commit': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
    'path': 'diagnostics/pokefirered_jp.sym.audit.tsv', 'size': 4147002,
    'sha256': 'fc1e4b579b21a592b8e09fa3c36f242833837190401128cd6866c945eff2f44e',
    'git_blob': '53316c0d61da2c6cc22acf3d79f68c61c64c65be'}
CLAIMS = {'formal_classification_accepted': False, 'donor_eligible': False,
    'donor_leased': False, 'donor_safe_bytes': 0, 'newly_classified': 0,
    'rom_reconstructions': 0, 'native_processes': 0, 'accepted_test_reruns': 0,
    'accepted_reader_replays': 0, 'neighbor_distance_is_asset_size': False,
    'actual_asset_or_reader_measured': False, 'full_story_pass_claimed': False}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def identity(raw):
    need(type(raw) is bytes, 'byte入力のみ')
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(type(k) is str and exact(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return type(a) in (str, int, bool, type(None)) and a == b


def select_target(frontier):
    """一意な保存hitだけを選択し、入力を変更しない。正式親の復元/hashは呼出側で束縛する。"""
    need(type(frontier) is dict and exact(frontier.get('candidate'), CANDIDATE), '容量候補SHA/size不一致')
    for key, value in {'total': 90, 'owner_unknown': 0, 'unowned_unknown': 90,
                       'donor_eligible': False, 'indirect_reference_completeness_claimed': False}.items():
        need(exact(frontier.get(key), value), 'frontier境界: ' + key)
    rows = frontier.get('rows')
    need(type(rows) is list and len(rows) == 90, '残90行を維持')
    addresses = []
    for row in rows:
        need(type(row) is dict and set(row) == {'hit', 'owners'} and exact(row['owners'], []), '未所有行のみ')
        hit = row['hit']
        need(type(hit) is dict and set(hit) == set(HIT), 'hit閉schema')
        for key in ('accepted', 'classification', 'kind', 'owner_candidates', 'reason', 'size'):
            need(exact(hit[key], HIT[key]), '未知の意味を変えない: ' + key)
        need(type(hit['address']) is int and 0x08000000 <= hit['address'] <= 0x09FFFFFC, 'hit address')
        need(type(hit['target']) is int and 0 <= hit['target'] < 2**32, 'hit target')
        need(type(hit['sha256']) is str and re.fullmatch('[0-9a-f]{64}', hit['sha256']), 'hit hash')
        addresses.append(hit['address'])
    need(len(set(addresses)) == 90 and addresses == sorted(addresses), '重複/順序変更を拒否')
    selected = [r for r in rows if r['hit']['address'] == TARGET]
    need(len(selected) == 1 and exact(selected[0]['hit'], HIT), '固定08397492原本不一致')
    need(identity(HIT['target'].to_bytes(4, 'little'))['sha256'] == HIT['sha256'], '保存word/hash整合')
    return copy.deepcopy(selected[0])


def symbol_neighbors(raw, target=TARGET):
    """認証済み公開TSVの前後labelを抽出。距離/参考sizeをasset境界に昇格しない。"""
    need(type(raw) is bytes and b'\0' not in raw, 'TSV textのみ')
    need(type(target) is int and target == TARGET, '有限targetのみ')
    lines = raw.decode('utf-8').splitlines()
    need(lines and len(lines[0]) < 4096, 'TSV header')
    rows = []
    for number, line in enumerate(lines, 1):
        fields = line.split('\t')
        if len(fields) > 1 and re.fullmatch('(?:0x)?[0-9a-fA-F]{8}', fields[1]):
            address = int(fields[1], 16)
            if 0x08000000 <= address < 0x0A000000:
                need(len(line) <= 4096, 'symbol行上限')
                rows.append({'line': number, 'address': address, 'fields': fields})
    need(rows, 'address列1の公開symbolを取得できない')
    addresses = sorted({r['address'] for r in rows})
    left, right = [a for a in addresses if a <= target], [a for a in addresses if a > target]
    need(left and right, '前後symbol欠落')
    selected_addresses = set(left[-2:] + right[:2])
    result = [r for r in rows if r['address'] in selected_addresses]
    need(4 <= len(result) <= 32, 'alias行の有限範囲')
    return {'header': lines[0], 'rows': result, 'target': target,
            'nearest_preceding_label': left[-1], 'nearest_following_label': right[0],
            'scope': 'SYMBOL_HINTS_ONLY_NOT_ASSET_EXTENT_OR_CONSUMER_PROOF',
            'neighbor_distance_is_asset_size': False}


def bind_symbols(raw):
    expected = {k: SYMBOL_SOURCE[k] for k in ('size', 'sha256')}
    need(exact(identity(raw), expected), '固定公開TSV全体SHA/size')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    need(blob == SYMBOL_SOURCE['git_blob'], '固定公開Git blob')
    return symbol_neighbors(raw)


def binding_state(state):
    """現行nested schemaだけを更新。R0/他lane/未完gateを保全してcopyを返す。"""
    need(type(state) is dict, '状態JSON object')
    owner = state.get('owner_execution_plan')
    need(type(owner) is dict and 'save_capacity' not in owner, 'flatな旧/推測schemaを拒否')
    need(type(owner.get('wiki')) is dict and owner['wiki'].get('review_ready') is True, 'R0提示受領が先')
    lanes = owner.get('technical_lanes')
    need(type(lanes) is dict and type(lanes.get('save_capacity')) is dict, 'technical_lanes.save_capacity必須')
    need(lanes['save_capacity'].get('status') == 'READY_TO_RESUME_FROM_PRESERVED_FRONTIER', '記録済みscope再走を拒否')
    need(type(state.get('next_action')) is dict and state['next_action'].get('id') == 'SAVE_CAPACITY_FROM_PRESERVED_08397492_FRONTIER', '現在nextだけを進める')
    result = copy.deepcopy(state)
    lane = result['owner_execution_plan']['technical_lanes']['save_capacity']
    lane['status'] = 'FRONTIER_BOUND_ASSET_READER_PROOF_PENDING'
    lane['checkpoint_path'] = 'content/modernization/pr16_capacity_08397492_checkpoint.json'
    return result
