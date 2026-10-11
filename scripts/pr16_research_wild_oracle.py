#!/usr/bin/env python3
"""釣り/生態の実稼得原本を独立に検証。native/ARM/旧suiteは起動しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'content/modernization/pr16_research_wild_local_evidence'
CANDIDATE = {'size': 33554432, 'sha256': '26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da'}
METHODS = ('fishing', 'ecology')
FIXTURE = {'size': 131072, 'sha256': '434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'}
STAGES = ('fixture', 'escaped', 'earned', 'continued')
SCREEN_STAGES = ('fixture', 'encounter', 'ball-pocket', 'earned', 'continued')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def integer(value, low, high):
    need(type(value) is int and low <= value <= high, 'bounded integer, not boolean')
    return value


def exact(got, want):
    if type(got) is not type(want):
        return False
    if isinstance(want, dict):
        return got.keys() == want.keys() and all(exact(got[k], v) for k, v in want.items())
    if isinstance(want, list):
        return len(got) == len(want) and all(exact(a, b) for a, b in zip(got, want))
    return got == want


def strict_load(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: need(False, 'non-finite JSON'))


def hex_bytes(value, length):
    need(type(value) is str and re.fullmatch('[0-9a-f]{'+str(2*length)+'}', value) is not None, 'complete canonical hex')
    return bytes.fromhex(value)


def seal(ledger):
    need(len(ledger) == 2048, 'complete ledger')
    value = 2166136261
    for index, byte in enumerate(ledger):
        value = ((value ^ (0 if 8 <= index < 12 else byte)) * 16777619) & 0xffffffff
    out = bytearray(ledger)
    struct.pack_into('<I', out, 8, value)
    return bytes(out)


def expected_owner(method, paid, minute):
    need(method in METHODS and type(paid) is bool, 'closed modeled scope')
    integer(minute, 1, 2)
    out = bytearray(64)
    out[0], out[1], out[6], out[7], out[36] = 1, 64, 1, minute, 1 + int(paid)
    if paid:
        points = 4 if method == 'fishing' else 10
        struct.pack_into('<H', out, 4, points)
        struct.pack_into('<I', out, 10, points)
        struct.pack_into('<H', out, 14 + 2 * METHODS.index(method), points)
    return bytes(out)


def expected_ledger(method, paid, minute):
    # Independently authored model of the fixture, not a copy of measured RAM.
    # Progression was a declared fixture: travel/visited/HOF/league-II/certs;
    # hatch/EXP-share were already 1 in the bound seed. No unknown bytes masked.
    out = bytearray(2048)
    out[:8] = b'VGS1\x02\0\0\x08'
    for offset in (0x10, 0x11, 0x12, 0x15, 0x1d, 0x1e, 0x1f):
        out[offset] = 1
    out[0x18] = 15
    out[0x73f:0x77f] = expected_owner(method, paid, minute)
    if paid:
        # RewardEncountersV2.credit_activity precedes ResearchEconomy in chain.
        struct.pack_into('<I', out, 0xc, 1)
        struct.pack_into('<I', out, 0x3fc, 1)
        struct.pack_into('<H', out, 0x684 + 2 * (0 if method == 'fishing' else 3), 1)
    return seal(out)


def closing(method, enemy):
    return dict(kind='summary', status='PASS', method=method, candidate_sha256=CANDIDATE['sha256'],
                initial_rp=0, earned_rp=4 if method == 'fishing' else 10,
                transaction_saves=2, typed_credit_saves=1, total_automatic_saves=3,
                manual_saves=0, fresh_cores=2, attempts=2, encounters=2,
                species=enemy['species'], pid=enemy['pid'], physical_escape_verified=True,
                host_write_barriers=7, guarded_host_writes=0, rng_injected=False,
                target_injected=False, accepted_case_reruns=0, all_activities_accepted=False,
                natural_arrival_accepted=False, warnings_errors=0)


def validate(raw: bytes, method: str, reviewed_screens: dict) -> dict:
    need(method in METHODS and type(raw) is bytes and 0 < len(raw) < 24000 and raw.endswith(b'\n'), 'complete bounded native transcript')
    rows = [strict_load(line) for line in raw.splitlines()]
    order = ['snapshot', 'screen']
    if method == 'ecology':
        order += ['radar_menu']
    order += ['enemy', 'snapshot']
    if method == 'ecology':
        order += ['radar_menu']
    order += ['enemy', 'screen', 'screen', 'snapshot', 'screen', 'snapshot', 'screen', 'summary']
    need(len(rows) == len(order) and all(type(r) is dict and r.get('kind') == kind for r, kind in zip(rows, order)), 'closed ordered transcript')
    frame = 0
    for row in rows[:-1]:
        new = integer(row.get('frame'), frame, 24000)
        frame = new
    snapshots = [r for r in rows if r['kind'] == 'snapshot']
    need([r.get('stage') for r in snapshots] == list(STAGES), 'all four persistence boundaries')
    first = snapshots[0]
    fields = set(('kind stage frame counter party_count balls map ledger_sha256 unrelated_ledger_sha256 party_sha256 flash_sha256 inventory_sha256 other_inventory_sha256 checksum_valid owner wild_armed result generation factory_transaction credit_kind typed_credit').split())
    for index, row in enumerate(snapshots):
        need(row.keys() == fields, 'closed snapshot schema')
        paid = index >= 2
        for key in ('ledger_sha256', 'unrelated_ledger_sha256', 'party_sha256', 'flash_sha256', 'inventory_sha256', 'other_inventory_sha256'):
            hex_bytes(row[key], 32)
        owner = hex_bytes(row['owner'], 64)
        need(owner == expected_owner(method, paid, owner[7]), 'every owner byte, including claims and pending')
        ledger = expected_ledger(method, paid, owner[7])
        other = bytearray(ledger)
        other[4:6] = bytes(2); other[8:12] = bytes(4); other[0x73f:0x77f] = bytes(64)
        need(row['ledger_sha256'] == identity(ledger)['sha256'] and row['unrelated_ledger_sha256'] == identity(other)['sha256'], 'independent whole-ledger and other-owner reconstruction')
        scalars = dict(counter=5 if paid else 2, party_count=2 if paid else 1, balls=19 if paid else 20,
                       checksum_valid=True, wild_armed=0, result=0, generation=int(paid),
                       factory_transaction=int(paid), credit_kind=0 if method == 'fishing' else 3,
                       typed_credit=int(paid), map=[3, 38, 94, 10] if method == 'fishing' else [3, 63, 14, 11])
        need(exact({k: row[k] for k in scalars}, scalars), 'closed map/party/Bag/three-save ownership')
        need(row['other_inventory_sha256'] == first['other_inventory_sha256'], 'unrelated inventory unchanged')
    invariant = fields - {'stage', 'frame'}
    need(exact({k: snapshots[1][k] for k in invariant}, {k: first[k] for k in invariant}), 'physical escape does not award/save/change party/Bag/ledger/Flash')
    need(exact({k: snapshots[3][k] for k in invariant}, {k: snapshots[2][k] for k in invariant}), 'fresh core Continue keeps full transaction state without manual Save')
    need(first['flash_sha256'] == FIXTURE['sha256'], 'unchanged initial disk image')
    for key in ('party_sha256', 'inventory_sha256', 'flash_sha256'):
        need(first[key] != snapshots[2][key], 'real capture change: ' + key)
    enemies = [r for r in rows if r['kind'] == 'enemy']
    for index, row in enumerate(enemies):
        need(row.keys() == {'kind','attempt','frame','species','pid','pre_caught','activity','party'}, 'closed enemy schema')
        integer(row['species'], 1, 1670); integer(row['pid'], 1, 0xffffffff)
        mon = hex_bytes(row['party'], 100)
        need(int.from_bytes(mon[:4], 'little') == row['pid'] and int.from_bytes(mon[32:34], 'little') == row['species'], 'natural enemy individual identity')
        need(exact([row['attempt'], row['pre_caught'], row['activity']], [index + 1, 0, METHODS.index(method)]), 'newly uncaught/armed provenance and real attempts')
    if method == 'ecology':
        menus = [r for r in rows if r['kind'] == 'radar_menu']
        for index, row in enumerate(menus):
            want = dict(kind='radar_menu', from_mode=4 if index else 0,
                        down_presses=0 if index else 4, selected_mode=4, frame=row['frame'])
            need(exact(row, want), 'retained stock radar cursor, not injected mode')
    screens = [r for r in rows if r['kind'] == 'screen']
    expected_names = ['research-' + method + '-' + s + '.ppm' for s in SCREEN_STAGES]
    need(set(reviewed_screens) == set(expected_names), 'exact reviewed screenshot set')
    for row, stage, name in zip(screens, SCREEN_STAGES, expected_names):
        hex_bytes(reviewed_screens[name], 32)
        need(exact(row, dict(kind='screen', stage=stage, name=name, sha256=reviewed_screens[name], frame=row['frame'])), 'reviewed real screen, ordered and hash-bound')
    need(exact(rows[-1], closing(method, enemies[-1])), 'closed success scope; no release/whole-game promotion')
    return dict(status='PASS', method=method, raw=identity(raw), rp=rows[-1]['earned_rp'],
                ledger_reconstructions=4, native_processes=0, observations=snapshots,
                all_activities_accepted=False, natural_arrival_accepted=False)
