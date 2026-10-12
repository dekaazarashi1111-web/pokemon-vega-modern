#!/usr/bin/env python3
"""初期化/V1移行の限定原本validator。試験の再実行や状態の生成は行わない。"""
from __future__ import annotations
import json
import re
import pr16_research_save_impact as old

need, identity = old.need, old.identity
CANDIDATE = old.bag.CANDIDATE
CASES = ('new-zero', 'new-erased', 'v1-valid', 'v1-bad-checksum', 'v1-nonzero-tail')
STAGES = ('fixture', 'returned', 'continued', 'continued_again')
SCOPE = 'RESEARCH_LIFECYCLE_RAM_FIXTURE_REAL_PHASE0_FLASH'
EVENT_FIELDS = {'event','counter','item_quantity','inventory_sha256','other_inventory_sha256','party_sha256','party_count','owner'}
LEDGER_FIELDS = {'ledger_event','version','size','checksum_valid','ledger_sha256','unrelated_ledger_sha256','migration_dirty','recovery_blocked'}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def owner_initial(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{128}', value), 'owner hex')
    raw = bytearray.fromhex(value)
    need(raw[7] <= 2, 'bounded ordinary minute')
    raw[7] = 0
    expected = bytearray(64)
    expected[0], expected[1], expected[6], expected[36] = 1, 64, 1, 1
    need(raw == expected, 'all initialized owner bytes')


def validate(raw: bytes, case: str):
    need(case in CASES and len(raw) <= 24000, 'bounded declared case')
    lines = raw.decode('utf-8').splitlines()
    need(len(lines) == 9, 'four paired observations and one result')
    rows = [old.load(line) for line in lines]
    reject = case in CASES[3:]
    saves = 0 if reject else 1
    expected = {'status':'PASS','scope':SCOPE,'case':case,'candidate_sha256':CANDIDATE['sha256'],
                'result':7 if reject else 5,'delegate_saves':saves,'delegate_loads':0,'phase0':saves,
                'fresh_cores':3,'host_write_barriers':7,'normal_new_game_or_transaction_ui_accepted':False,
                'v1_load_adapter_accepted':False,'phase0_failure_accepted':False,'warnings_errors':0}
    result = rows[-1]
    need(set(result) == set(expected), 'exact result fields')
    for key, value in expected.items():
        need(type(result[key]) is type(value) and result[key] == value, 'result '+key)
    events, ledgers = rows[0:8:2], rows[1:8:2]
    first = events[0]
    for n, (stage, event, ledger) in enumerate(zip(STAGES, events, ledgers)):
        need(set(event)==EVENT_FIELDS and event['event']==stage, 'event fields/order')
        need(set(ledger)==LEDGER_FIELDS and ledger['ledger_event']==stage, 'ledger fields/order')
        old.integer(event['counter'],1,100,'save counter')
        old.integer(event['item_quantity'],0,999,'item quantity')
        old.integer(event['party_count'],1,6,'party count')
        for key in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            old.digest(event[key]);need(event[key]==first[key], 'unrelated '+key)
        need(event['item_quantity']==first['item_quantity'] and event['party_count']==first['party_count'], 'no item/party mutation')
        need(event['counter']==first['counter']+(saves if n else 0), 'exact save count')
        need(isinstance(event['owner'],str) and re.fullmatch('[0-9a-f]{128}',event['owner']), 'complete owner hex')
        for key in ('ledger_sha256','unrelated_ledger_sha256'):old.digest(ledger[key])
        old.integer(ledger['version'],0,65535,'version')
        old.integer(ledger['size'],0,65535,'size')
        need(type(ledger['checksum_valid']) is bool, 'checksum boolean')
        for key in ('migration_dirty','recovery_blocked'):
            need(type(ledger[key]) is int and ledger[key]==0, 'cleared volatile '+key)
        if n and not reject:
            owner_initial(event['owner'])
            need(ledger['version']==2 and ledger['size']==2048 and ledger['checksum_valid'], 'valid V2')
        if n and case=='v1-valid':
            need(ledger['unrelated_ledger_sha256']==ledgers[0]['unrelated_ledger_sha256'], 'all migration-external ledger bytes')
    if reject:
        need(events[0]['owner']==events[1]['owner'] and ledgers[0]['ledger_sha256']==ledgers[1]['ledger_sha256'], 'invalid V1 not normalized')
    else:
        need(ledgers[1]['unrelated_ledger_sha256']==ledgers[2]['unrelated_ledger_sha256'], 'Continue unrelated ledger')
    need({k:v for k,v in events[2].items() if k!='event'}=={k:v for k,v in events[3].items() if k!='event'}, 'second Continue owner/Bag/party idempotence')
    need({k:v for k,v in ledgers[2].items() if k!='ledger_event'}=={k:v for k,v in ledgers[3].items() if k!='ledger_event'}, 'second Continue complete ledger idempotence')
    return dict(result, observations=events, ledger_observations=ledgers, stdout=identity(raw))
