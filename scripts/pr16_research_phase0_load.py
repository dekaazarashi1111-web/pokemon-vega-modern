#!/usr/bin/env python3
"""通常loadのphase0保存不可・cold Continue回復を限定検証する。"""
from __future__ import annotations
import hashlib
import struct
from pathlib import Path
import pr16_research_v1_corrupt_load as parent
old = parent.root.prior
need, identity = old.need, old.identity
CANDIDATE = parent.CANDIDATE
CASES = ('load-v1-phase0-unavailable', 'load-pending-phase0-unavailable')
SCOPE = 'ORDINARY_LOAD_PHASE0_AVAILABILITY_FIXTURE_AND_COLD_RECOVERY'
C = 'tools/mgba_pr16_research_phase0_load.c'
SOURCE = 'overlays/research_economy_v1/research_economy_v1.c'
OFFSET, OWNER, AVAILABLE, PHASE0 = old.OFFSET, 0x73F, 0x03005044, 0x093BF630


def fixture(seed: bytes, case: str):
    need(identity(seed) == old.old.SEED and case in CASES, 'exact private seed/closed case')
    if case == CASES[0]:
        raw, _ = old.fixture(seed, old.CASES[0])
    else:
        ledger = bytearray(seed[OFFSET:OFFSET + 2048])
        need(ledger[:8] == b'VGS1\x02\0\0\x08' and old.checksum(ledger) == int.from_bytes(ledger[8:12], 'little'), 'valid V2 seed')
        # prepared existing-earn/fishing: 5 points, next transaction 2.
        owner = bytearray(64)
        owner[0], owner[1], owner[6] = 1, 64, 1
        struct.pack_into('<I', owner, 36, 2)
        struct.pack_into('<I', owner, 44, 1)
        owner[48], owner[49] = 1, 1
        struct.pack_into('<H', owner, 52, 5)
        ledger[OWNER:OWNER + 64] = owner
        ledger = old.seal(ledger)
        raw = seed[:OFFSET] + ledger + seed[OFFSET + 2048:]
    ledger = raw[OFFSET:OFFSET + 2048]
    need(len(raw) == 131072 and raw[:OFFSET] == seed[:OFFSET] and raw[OFFSET + 2048:] == seed[OFFSET + 2048:], 'private ledger fixture only')
    return raw, {'case': case, 'seed': identity(seed), 'fixture': identity(raw), 'ledger': identity(ledger),
                 'recovered_ledger': identity(recovered(ledger, case)), 'offset': OFFSET, 'size': 2048,
                 'outside_ledger_changes': 0, 'historical_user_save_claimed': False}


def recovered(ledger: bytes, case: str) -> bytes:
    need(len(ledger) == 2048 and case in CASES, 'full input/closed recovery case')
    need(old.checksum(ledger) == int.from_bytes(ledger[8:12], 'little'), 'valid input checksum')
    if case == CASES[0]:
        return old.migrated(ledger)
    owner = ledger[OWNER:OWNER + 64]
    expected = bytearray(64)
    expected[0], expected[1], expected[6] = 1, 64, 1
    struct.pack_into('<I', expected, 36, 2)
    struct.pack_into('<I', expected, 44, 1)
    expected[48], expected[49] = 1, 1
    struct.pack_into('<H', expected, 52, 5)
    need(ledger[:8] == b'VGS1\x02\0\0\x08' and owner == expected, 'exact prepared owner, no inferred transaction')
    out = bytearray(ledger)
    out[OWNER + 44:OWNER + 60] = bytes(16)
    struct.pack_into('<H', out, OWNER + 4, 5)
    struct.pack_into('<I', out, OWNER + 10, 5)
    struct.pack_into('<H', out, OWNER + 14, 5)
    return old.seal(out)


def generate(seed: bytes) -> bytes:
    text = parent.root.generate(seed).decode()
    token = 'int main(int argc,char**argv){'
    need(text.count(token) == 1 and text.count(old.CANDIDATE['sha256']) == 1, 'one inherited main/ROM binding')
    text = text.replace(token, 'int accepted_v1_load_main(int argc,char**argv){')
    text = text.replace(old.CANDIDATE['sha256'], CANDIDATE['sha256'])
    receipts = [fixture(seed, case)[1] for case in CASES]
    header = '\nstatic const char* const PL_FIXTURES[]={' + ','.join('"' + r['fixture']['sha256'] + '"' for r in receipts) + '};\n'
    header += 'static const char* const PL_RECOVERED[]={' + ','.join('"' + r['recovered_ledger']['sha256'] + '"' for r in receipts) + '};\n'
    return (text + header + Path(C).read_text()).encode()


def exact(got, want, label):
    need(isinstance(got, dict) and set(got) == set(want), label + ' closed schema')
    for key, value in want.items():
        need(type(got[key]) is type(value) and got[key] == value, label + ' ' + key)


def expected_trace(stage: str):
    failed = stage == 'failed'
    return {'phase0_load_trace': stage, 'root_calls': 1, 'research_calls': 1, 'mirage_calls': 1, 'qol_calls': 1,
            'save_calls': 1, 'phase0': 1, 'phase1': 0, 'phase2': 0, 'native_returns': 1,
            'native_result': 255 if failed else 1, 'research_result': 0 if failed else 1,
            'root_result': 0 if failed else 1, 'counter_at_save': 2, 'available_at_save': 0 if failed else 1,
            'save_type': 0, 'root_return_pc': parent.root.LOAD_RETURN, 'guarded_host_writes': 0}


def result(case: str):
    return {'status': 'PASS', 'scope': SCOPE, 'case': case, 'candidate_sha256': CANDIDATE['sha256'],
            'fresh_cores': 4, 'availability_fixture_words': 1, 'availability_fixture_byte_writes': 4,
            'host_write_barriers': 7, 'guarded_host_writes': 0, 'ram_ledger_fixture_writes': 0,
            'register_fixture_writes': 0, 'physical_flash_fault_accepted': False,
            'same_core_menu_retry_accepted': False, 'normal_new_game_accepted': False,
            'transaction_ui_accepted': False, 'warnings_errors': 0}


def validate(raw: bytes, case: str, save: bytes, baseline: dict):
    need(case in CASES and 0 < len(raw) <= 32000, 'bounded declared native output')
    need(len(save) == 131072, 'full private Flash input')
    rows = [old.old.load(line) for line in raw.decode('utf-8').splitlines()]
    need(len(rows) == 20, 'exact failure/recovery/two idempotence observations')
    source = save[OFFSET:OFFSET + 2048]
    target = recovered(source, case)
    first = parent.root.root_expectations(old.CASES[0])[0]
    exact(rows[0], first, 'first boot root')
    exact(rows[1], {'fault_fixture': 'availability_word_only', 'address': AVAILABLE, 'pc': PHASE0,
                    'before': 1, 'after': 0, 'word_writes': 1, 'byte_writes': 4,
                    'ewram_unchanged': True, 'iwram_except_word_unchanged': True,
                    'registers_unchanged': True, 'flash_unchanged': True, 'guard_rearmed': True}, 'fixture')
    failed_root = dict(first, result=0, counter=2, version=1 if case == CASES[0] else 2, last=13, root_lr=parent.root.LOAD_RETURN)
    exact(rows[2], failed_root, 'failed root')
    exact(rows[7], first, 'recovery boot root')
    exact(rows[8], dict(first, result=1, counter=3, version=2, last=0, root_lr=parent.root.LOAD_RETURN), 'recovered root')
    for index, stage, ledger, counter, blocked, last in ((3, 'failed', source, 2, 1, 13), (9, 'recovered', target, 3, 0, 0)):
        exact(rows[index], {'load_state': stage, 'counter': counter, 'version': int.from_bytes(ledger[4:6], 'little'),
                           'checksum_valid': True, 'migration_dirty': 0, 'recovery_blocked': blocked,
                           'last_result': last, 'ledger_sha256': identity(ledger)['sha256']}, stage + ' ledger')
        trace = rows[index + 1]
        old.old.integer(trace.get('steps'), 1, 400000000, 'bounded observed steps')
        exact(trace, dict(expected_trace(stage), steps=trace['steps']), stage + ' trace')
        invariants = {'phase0_load_invariants': stage, 'input_ledger_restored': stage == 'failed',
                      'full_flash_unchanged': stage == 'failed', 'other_private_owners_unchanged': True,
                      'durable_matches_ram': True, 'flash_sha256': identity(save)['sha256'] if stage == 'failed' else rows[index + 2].get('flash_sha256')}
        if stage == 'recovered':
            old.old.need(isinstance(invariants['flash_sha256'], str) and len(invariants['flash_sha256']) == 64 and all(c in '0123456789abcdef' for c in invariants['flash_sha256']), 'recovered Flash digest')
            need(invariants['flash_sha256'] != identity(save)['sha256'], 'real Flash change on recovery')
        exact(rows[index + 2], invariants, stage + ' invariants')
    # Failed root still loaded the stock save; bag/party and complete preimage owner remain unchanged.
    def event(ev, stage, ledger, allow_minutes):
        need(set(ev) == old.lc.EVENT_FIELDS and ev['event'] == stage, 'exact inventory event')
        for key in ('inventory_sha256', 'other_inventory_sha256', 'party_sha256', 'item_quantity', 'party_count'):
            need(type(ev[key]) is type(baseline[key]) and ev[key] == baseline[key], 'stock save unchanged ' + key)
        need(type(ev['counter']) is int and ev['counter'] == (2 if stage == 'failed' else 3), 'exact durable counter')
        owner = bytes.fromhex(ev['owner'])
        need(len(owner) == 64, 'full owner')
        normalized = bytearray(owner)
        if allow_minutes:
            need(owner[7] <= 2, 'bounded real play-time minute')
            normalized[7] = ledger[OWNER + 7]
        need(normalized == ledger[OWNER:OWNER + 64], 'complete expected owner and exactly-once reward')
        return owner
    event(rows[6], 'failed', source, False)
    observations = []
    for i, stage in enumerate(('continued', 'continued_again', 'continued_third')):
        ev, le = rows[12 + i * 2:14 + i * 2]
        owner = event(ev, stage, target, True)
        modeled = bytearray(target); modeled[OWNER:OWNER + 64] = owner; modeled = old.seal(modeled)
        unrelated = bytearray(modeled); unrelated[4:6] = bytes(2); unrelated[8:12] = bytes(4); unrelated[OWNER:OWNER + 64] = bytes(64)
        exact(le, {'ledger_event': stage, 'version': 2, 'size': 2048, 'checksum_valid': True,
                   'ledger_sha256': identity(modeled)['sha256'], 'unrelated_ledger_sha256': identity(unrelated)['sha256'],
                   'migration_dirty': 0, 'recovery_blocked': 0}, 'field ledger')
        if observations:
            need({k:v for k,v in ev.items() if k != 'event'} == {k:v for k,v in observations[0].items() if k != 'event'}, 'cold Continue idempotent all owner/bag/party')
        observations.append(ev)
    exact(rows[18], {'cold_recovery': 'PASS', 'normal_loads_after_failure': 3, 'additional_saves_after_recovery': 0,
                     'complete_ledger_equal': True, 'availability_restored_by_cold_boot': True}, 'recovery receipt')
    exact(rows[19], result(case), 'final receipt')
    return dict(result(case), failure_state=rows[3], recovery_state=rows[9], observations=observations, stdout=identity(raw))
