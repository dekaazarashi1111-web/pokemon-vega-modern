#!/usr/bin/env python3
"""実保存V1 fixtureと通常ロードの閉じたoracle。旧native/ARMの再実行なし。"""
from __future__ import annotations
import hashlib
import re
import struct
import pr16_research_retry as retry
lc=retry.lc; old=lc.old; need=old.need; identity=old.identity
CASES=('v1-load-valid','v1-load-checksum','v1-load-tail')
CANDIDATE={'size':33554432,'sha256':'58079dfbdbe15899d9b86f53ad3a21fe46ddcebf5fed231c85dcd2332ddd2d75'}
OFFSET=0x1F064
SCOPE='V1_FLASH_FIXTURE_ORDINARY_LOAD_CHAIN'
STATES={'load_state','counter','version','checksum_valid','migration_dirty','recovery_blocked','last_result','ledger_sha256','ledger_hex'}


def checksum(raw):
    need(len(raw)==2048,'full ledger checksum')
    value=2166136261
    for i,byte in enumerate(raw):value=((value^(0 if 8<=i<12 else byte))*16777619)&0xFFFFFFFF
    return value


def seal(raw):
    out=bytearray(raw);struct.pack_into('<I',out,8,checksum(out));return bytes(out)


def fixture(seed,case):
    need(identity(seed)==old.SEED and case in CASES,'fixed seed/closed fixture')
    ledger=bytearray(seed[OFFSET:OFFSET+2048]);need(ledger[:8]==b'VGS1\x02\0\0\x08' and checksum(ledger)==int.from_bytes(ledger[8:12],'little'),'valid seed ledger')
    ledger[4:6]=b'\x01\0';ledger[0x73f:]=bytes(193)
    if case==CASES[2]:ledger[0x77f]=1
    ledger=bytearray(seal(ledger))
    if case==CASES[1]:ledger[8]^=1
    ledger=bytes(ledger);out=seed[:OFFSET]+ledger+seed[OFFSET+2048:]
    need(len(out)==131072 and out[:OFFSET]==seed[:OFFSET] and out[OFFSET+2048:]==seed[OFFSET+2048:],'only private ledger fixture changed')
    return out,{'case':case,'seed':old.SEED,'fixture':identity(out),'ledger':identity(ledger),'offset':OFFSET,'size':2048,
                'outside_ledger_changes':0,'stock_sectors_changed':0,'other_private_owners_changed':0,
                'checksum_valid':checksum(ledger)==int.from_bytes(ledger[8:12],'little'),
                'reserved_tail_valid':not any(ledger[0x73f:]),'private_fixture_not_historical_user_save':True}


def migrated(ledger):
    need(len(ledger)==2048 and ledger[:8]==b'VGS1\x01\0\0\x08' and not any(ledger[0x73f:]) and checksum(ledger)==int.from_bytes(ledger[8:12],'little'),'valid complete V1')
    out=bytearray(ledger);out[4:6]=b'\x02\0';out[0x73f]=1;out[0x740]=64;out[0x745]=1;out[0x763]=1
    return seal(out)


def expected_trace(case):
    valid=case==CASES[0];n=int(valid)
    return {'trace':'ordinary_load','root_calls':1,'research_calls':1,'mirage_calls':1,'qol_load_calls':1,
            'save_calls':n,'phase0':n,'phase1':0,'phase2':0,'native_returns':n,'native_result':n,
            'research_result':n,'root_result':n,'counter_at_save':2*n,'available_at_save':n,'host_writes':0}


def validate(raw,case,save,baseline):
    need(case in CASES and 0<len(raw)<=20000,'bounded declared load case')
    rows=[old.load(x) for x in raw.decode('utf-8').splitlines()];valid=case==CASES[0]
    need(len(rows)==(9 if valid else 3),'exact load observations')
    state,trace=rows[:2];result=rows[-1]
    need(set(state)==STATES and state['load_state']=='adapter_return','state schema')
    need(isinstance(state['ledger_hex'],str) and re.fullmatch('[0-9a-f]{4096}',state['ledger_hex']),'complete all-byte loaded ledger')
    ledger=bytes.fromhex(state['ledger_hex']);input_ledger=save[OFFSET:OFFSET+2048]
    target=migrated(input_ledger) if valid else input_ledger
    need(ledger==target,'exact migrated ledger / invalid preimage unchanged')
    want={'counter':3 if valid else 2,'version':2 if valid else 1,
          'checksum_valid':checksum(target)==int.from_bytes(target[8:12],'little'),
          'migration_dirty':0,'recovery_blocked':0,'last_result':0 if valid else 7,
          'ledger_sha256':hashlib.sha256(target).hexdigest()}
    for k,v in want.items():need(type(state[k]) is type(v) and state[k]==v,'state '+k)
    want=expected_trace(case)
    need(set(trace)==set(want)|{'steps','save_type'},'exact trace schema')
    old.integer(trace['steps'],1,400000000,'bounded actual instruction observation');old.integer(trace['save_type'],0,255,'native save type')
    for k,v in want.items():need(type(trace[k]) is type(v) and trace[k]==v,'trace '+k)
    events=[];ledgers=[]
    if valid:
        prefix=bytearray(target);prefix[4:6]=bytes(2);prefix[8:12]=bytes(4);prefix[0x73f:0x77f]=bytes(64)
        stable=hashlib.sha256(prefix).hexdigest()
        for i,stage in enumerate(('continued','continued_again','continued_third')):
            ev,le=rows[2+2*i:4+2*i];events.append(ev);ledgers.append(le)
            need(set(ev)==lc.EVENT_FIELDS and ev['event']==stage and set(le)==lc.LEDGER_FIELDS and le['ledger_event']==stage,'field schema/order')
            old.integer(ev['counter'],3,3,'one committed migration');old.integer(ev['party_count'],1,6,'party');old.integer(ev['item_quantity'],0,999,'item')
            for key in ('inventory_sha256','other_inventory_sha256','party_sha256','item_quantity','party_count'):
                need(type(ev[key]) is type(baseline[key]) and ev[key]==baseline[key],'unchanged baseline '+key)
            lc.owner_initial(ev['owner'])
            modeled=bytearray(target);modeled[0x73f:0x77f]=bytes.fromhex(ev['owner']);modeled=seal(modeled)
            lw={'version':2,'size':2048,'checksum_valid':True,'migration_dirty':0,'recovery_blocked':0,
                'ledger_sha256':hashlib.sha256(modeled).hexdigest(),'unrelated_ledger_sha256':stable}
            for k,v in lw.items():need(type(le[k]) is type(v) and le[k]==v,'field '+k)
            if i:
                need({k:v for k,v in ev.items() if k!='event'}=={k:v for k,v in events[0].items() if k!='event'},'full owner/Bag/party idempotence')
                need({k:v for k,v in le.items() if k!='ledger_event'}=={k:v for k,v in ledgers[0].items() if k!='ledger_event'},'full ledger idempotence')
    want={'status':'PASS','scope':SCOPE,'case':case,'candidate_sha256':CANDIDATE['sha256'],'fresh_cores':3 if valid else 1,
          'host_write_barriers':7,'ram_fixture_writes':0,'physical_flash_fault_accepted':False,
          'normal_new_game_accepted':False,'transaction_ui_accepted':False,'warnings_errors':0}
    need(set(result)==set(want),'result exact schema')
    for k,v in want.items():need(type(result[k]) is type(v) and result[k]==v,'result '+k)
    return dict(result,load_state=state,trace=trace,observations=events,ledger_observations=ledgers,stdout=identity(raw))
