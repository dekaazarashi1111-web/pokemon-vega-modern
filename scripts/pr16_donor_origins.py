#!/usr/bin/env python3
"""選定済み10参照originと固定公開symbolの近傍を束縛。owner/leaseは推測しない。"""
from __future__ import annotations
from bisect import bisect_right
import hashlib
import json
import re

BASE, END = 0x08000000, 0x0A000000
WINDOW = (0x09FED0C4, 0x09FEEA44)
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
PLAN_ID = dict(size=9687, sha256='100dd710037fd958db20191a4bffa8590fb0414a2e252705f1111d75e15e9d2c')
CLAIMS = dict(donor_safe_bytes=0, donor_eligible=False, donor_leased=False,
    formal_classification_changes=0, actual_consumer_proven=False,
    symbol_neighborhood_is_owner=False, retirement_or_transfer_complete=False,
    indirect_reference_completeness_claimed=False, outside_target_excludes_access=False,
    intra_donor_origins_covered=False, rom_reconstructions=0, native_processes=0,
    accepted_test_reruns=0, old_full_rom_scan_runs=0, rom_writes=0, save_writes=0)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    need(type(raw) is bytes, 'bytesのみ')
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def parse_symbols(raw, expected):
    """固定8列TSVのみ。隣接labelをextentや現在ROMのownerに昇格しない。"""
    need(type(expected) is dict and type(expected.get('size')) is int, 'symbol identity型')
    need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')}, 'symbol全identity')
    need(blob(raw) == expected['git_blob'], 'symbol Git blob')
    lines = raw.decode('utf-8').splitlines()
    need(0 < len(lines) <= 200000, 'symbol有限行数')
    groups, seen = {}, set()
    for number, line in enumerate(lines, 1):
        row = line.split('\t')
        if len(row) != 8:
            continue
        if not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{8}', row[1]):
            continue
        address = int(row[1], 16)
        if not BASE <= address < END:
            continue
        need(bool(re.fullmatch(r'[A-Za-z_.$][A-Za-z0-9_.$]*', row[4])), 'symbol名の型')
        need((address,row[4]) not in seen, 'symbol重複')
        seen.add((address,row[4]))
        groups.setdefault(address, []).append(dict(name=row[4], line=number, row_sha256=identity(line.encode())['sha256']))
    need(bool(groups), 'ROM symbolなし')
    return [dict(address=address, labels=sorted(labels, key=lambda x:x['name']))
            for address,labels in sorted(groups.items())]


def validate_rows(rows):
    need(type(rows) is list and 0 < len(rows) <= 10000, '有限origin list')
    seen = set()
    for row in rows:
        need(type(row) is dict, 'origin object')
        address,target,size = (row.get(k) for k in ('address','target','size'))
        need(all(type(x) is int for x in (address,target,size)) and size==4,
             'origin整数/4byte')
        need(BASE <= address <= END-size and WINDOW[0] <= target < WINDOW[1], 'origin/target範囲')
        need(row.get('accepted') is False and row.get('classification')=='UNCLASSIFIED', '未知のみ')
        need(row.get('kind')=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS', '保存origin型')
        need(type(row.get('sha256')) is str and bool(re.fullmatch('[0-9a-f]{64}',row['sha256'])), 'origin hash')
        need(address not in seen, 'origin重複')
        seen.add(address)


def locate(rows, symbols):
    validate_rows(rows)
    need(type(symbols) is list and bool(symbols), 'symbol list')
    addresses=[s['address'] for s in symbols]
    need(all(type(x) is int and BASE<=x<END for x in addresses)
         and addresses==sorted(set(addresses)), 'symbol整列/一意')
    out=[]
    for row in sorted(rows,key=lambda x:x['address']):
        pos=bisect_right(addresses,row['address'])-1
        previous=symbols[pos] if pos>=0 else None
        following=symbols[pos+1] if pos+1<len(symbols) else None
        covered=[s for s in symbols[max(pos+1,0):] if s['address'] < row['address']+row['size']]
        out.append(dict(hit=dict(row), preceding_label=previous, following_label=following,
            labels_starting_inside_hit=covered,
            offset_from_preceding=None if previous is None else row['address']-previous['address'],
            status='PUBLIC_SYMBOL_NEIGHBORHOOD_ONLY_CURRENT_OWNER_UNPROVEN',
            current_candidate_bytes_bound=False, actual_consumer_proven=False))
    return out


def analyze(plan_raw, symbol_raw, source):
    need(identity(plan_raw)==PLAN_ID,'保存窓plan全identity')
    plan=json.loads(plan_raw)
    need(plan['candidate']==CANDIDATE and plan['selected']['start']==WINDOW[0]
         and plan['selected']['end_exclusive']==WINDOW[1] and plan['selected']['size']==6528,'保存候補/窓')
    rows=plan['selected']['unclassified_target_rows']
    need(len(rows)==10 and plan['inherited']==dict(total=874,classified=785,unclassified=89),'正式785/89と選定10行')
    symbols=parse_symbols(symbol_raw,source)
    return dict(schema_version=1, status='TEN_ORIGIN_SYMBOL_FRONTIER_BOUND_NOT_OWNER_PROOF',
        candidate=dict(CANDIDATE), plan_identity=dict(PLAN_ID), public_symbol_source=dict(source),
        selected_window=dict(start=WINDOW[0],end_exclusive=WINDOW[1],size=6528),
        origins=locate(rows,symbols), claims=dict(CLAIMS),
        limitations_ja=['公開JP symbolの隣接labelは現候補のowner/asset extent/実consumer証明ではない。',
                       '高位ROM originに近傍labelがない場合も未確認。最終labelの範囲をROM末尾まで延長しない。',
                       '窓外からの跨りread・旧owner内部origin・計算/間接参照は残る。正式785/89、安全容量0。'])
