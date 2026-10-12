#!/usr/bin/env python3
"""phase0既存native保存不可3件の閉じた原本validatorと生成器。"""
from __future__ import annotations
import re
import pr16_research_lifecycle as lc
m=lc.old;need=m.need;identity=m.identity
CASES=('init-zero-save-unavailable','init-erased-save-unavailable','v1-save-unavailable')
STAGES=('baseline','fixture','failed','continued','continued_again')
SCOPE='PHASE0_EXISTING_NATIVE_UNAVAILABLE_RAM_FIXTURE'
OBSERVE='if(pc==0x09377660U)++si_saves;if(pc==0x09377694U)++si_loads;'
RANGES=((0x09377660,52,'bf430c8e1e3986e52e62134a46aa4dbdf1df288ed6d40b4a3dc17f0889212ac6'),
        (0x093789E4,24,'626e744d61249d7c81dee24da68faa741c98b80083136dfe9a1e68dca1601e42'),
        (0x09378B28,8,'9957af7c56f8ec97159c4f0eb4115ab83a62456cd8c7bb9e549abe65c9ed452e'),
        (0x080DB356,64,'f49a20b995c6469ce9e647b18237f7e856821dab0f53afe98d57b564a0c23652'))


def generate(base: str, addition: str) -> str:
    token='int main(int argc,char**argv){'
    need(base.count(token)==1 and addition.count(token)==1 and base.count(OBSERVE)==1,'exact generation boundaries')
    text=base.replace(token,'int lifecycle_accepted_main(int argc,char**argv){')
    text=text.replace(OBSERVE,OBSERVE+'if(pc==0x0937767AU){++ph_native_returns;ph_native_last=(unsigned)read_register(c,"r0");}')
    return 'static unsigned ph_native_returns,ph_native_last;\n'+text+'\n'+addition


def expected_result(case):
    need(case in CASES,'declared case')
    return {'status':'PASS','scope':SCOPE,'case':case,'candidate_sha256':lc.CANDIDATE['sha256'],
            'result':7,'delegate_saves':1,'delegate_loads':0,'phase0':1,'native_returns':1,'native_result':255,
            'fresh_cores':3,'host_write_barriers':7,'physical_flash_fault_accepted':False,
            'same_core_retry_accepted':False,'v1_load_adapter_accepted':False,'normal_ui_accepted':False,'warnings_errors':0}


def validate(raw,case):
    need(len(raw)<=30000,'bounded stdout');lines=raw.decode('utf-8').splitlines()
    need(len(lines)==11,'five paired observations and result')
    rows=[m.load(line) for line in lines];result=rows[-1];expected=expected_result(case)
    need(set(result)==set(expected),'exact result fields')
    for key,value in expected.items():need(type(result[key]) is type(value) and result[key]==value,'result '+key)
    events,ledgers=rows[0:10:2],rows[1:10:2]
    for i,(stage,event,ledger) in enumerate(zip(STAGES,events,ledgers)):
        need(set(event)==lc.EVENT_FIELDS and event['event']==stage,'event schema/order')
        need(set(ledger)==lc.LEDGER_FIELDS and ledger['ledger_event']==stage,'ledger schema/order')
        m.integer(event['counter'],1,100,'counter');m.integer(event['item_quantity'],0,999,'item quantity');m.integer(event['party_count'],1,6,'party count')
        for key in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            m.digest(event[key]);need(event[key]==events[0][key],'unchanged '+key)
        for key in ('counter','item_quantity','party_count'):need(event[key]==events[0][key],'unchanged '+key)
        need(isinstance(event['owner'],str) and re.fullmatch('[0-9a-f]{128}',event['owner']),'all owner bytes')
        for key in ('ledger_sha256','unrelated_ledger_sha256'):m.digest(ledger[key])
        m.integer(ledger['version'],0,65535,'version');m.integer(ledger['size'],0,65535,'size')
        need(type(ledger['checksum_valid']) is bool,'checksum boolean')
        need(type(ledger['migration_dirty']) is int and ledger['migration_dirty']==0,'dirty flag clear')
        need(type(ledger['recovery_blocked']) is int and ledger['recovery_blocked']==(1 if i==2 else 0),'blocked only after failed phase0')
    if case==CASES[2]:
        need(ledgers[1]['version']==ledgers[2]['version']==1 and ledgers[1]['checksum_valid'] and ledgers[2]['checksum_valid'],'valid V1 fixture and rollback')
        need(ledgers[1]['ledger_sha256']==ledgers[2]['ledger_sha256'] and events[1]['owner']==events[2]['owner'],'all-byte V1 rollback')
    else:
        lc.owner_initial(events[2]['owner'])
        need(ledgers[2]['version']==2 and ledgers[2]['size']==2048 and ledgers[2]['checksum_valid'],'initialized RAM valid but blocked')
    for i in (3,4):
        need({k:v for k,v in events[i].items() if k!='event'}=={k:v for k,v in events[0].items() if k!='event'},'fresh Continue restores original complete owner/Bag/party')
        need({k:v for k,v in ledgers[i].items() if k!='ledger_event'}=={k:v for k,v in ledgers[0].items() if k!='ledger_event'},'fresh Continue restores complete prior durable ledger')
    return dict(result,observations=events,ledger_observations=ledgers,stdout=identity(raw))
