#!/usr/bin/env python3
"""限定native取消のfixture・source生成・閉じた証拠validator。"""
from __future__ import annotations
import json
from pathlib import Path
import pr16_research_phase0_load as prior
need, identity = prior.need, prior.identity
CANDIDATE = prior.CANDIDATE
CASE = 'shop-two-cancels-save-continue'
C = 'tools/mgba_pr16_research_shop_cancel.c'
STAGES = ('fixture','cancel_b','cancel_row','saved','continued','continued_again')
SCOPE = 'NATIVE_RESEARCH_SHOP_TWO_CANCELS_AND_SAVE_CONTINUE'

def fixture(seed):
    need(identity(seed)==prior.old.old.SEED and len(seed)==131072,'exact private seed')
    at=prior.OFFSET; body=bytearray(seed[at:at+2048])
    need(body[:8]==b'VGS1\x02\0\0\x08' and prior.old.checksum(body)==int.from_bytes(body[8:12],'little'),'valid seed ledger')
    for i in (16,17,18,21):body[i]=1
    body[24]|=15
    owner=bytearray(64);owner[0],owner[1],owner[6],owner[36]=1,64,1,1
    owner[4:6]=(100).to_bytes(2,'little');body[0x73f:0x77f]=owner
    body=prior.old.seal(body);out=seed[:at]+body+seed[at+2048:]
    need(out[:at]==seed[:at] and out[at+2048:]==seed[at+2048:],'only private ledger fixture')
    return out,{'seed':identity(seed),'fixture':identity(out),'ledger':identity(body),'offset':at,'size':2048,'progress_and_balance_are_fixtures':True,'natural_progress_claimed':False,'outside_ledger_changes':0}

def generate(seed):
    import pr16_research_lifecycle_v2 as base
    text=base.generate().read_text();token='int main(int argc,char**argv){'
    need(text.count(token)==1,'one inherited main declaration')
    save,_=fixture(seed)
    header='#define UC_ROM "'+CANDIDATE['sha256']+'"\n#define UC_FIXTURE "'+identity(save)['sha256']+'"\n'
    return (header+text.replace(token,'int accepted_lifecycle_main(int argc,char**argv){')+'\n'+Path(C).read_text()).encode()

def result(count,pages,frames):
    return {'status':'PASS','scope':SCOPE,'case':CASE,'candidate_sha256':CANDIDATE['sha256'],'fresh_cores':3,'cancel_routes':2,'eligible_count':count,'pages':pages,'manual_saves':1,'transaction_saves':0,'host_write_barriers':7,'guarded_host_writes':0,'frames_after_warp':frames,'fixture_warp_calls':4,'fixture_field_callback_writes':1,'normal_new_game_accepted':False,'purchase_accepted':False,'natural_progress_accepted':False,'warnings_errors':0}

def validate(raw):
    need(0<len(raw)<=20000,'bounded native observations')
    rows=[prior.old.old.load(line) for line in raw.decode().splitlines()]
    need(len(rows)==17,'exact native rows')
    binding,setup=rows[:2]
    need(set(binding)=={'binding','events','backgrounds','script','x','y'} and binding['binding']=='map98/3-background0' and type(binding['x']) is int and binding['x']==2 and type(binding['y']) is int and binding['y']==1,'authored background')
    for k in ('events','backgrounds','script'):prior.old.old.integer(binding[k],0x08000000,0x09ffffff,'ROM pointer '+k)
    prior.exact(setup,{'fixture':'stock-warp-only','map_group':98,'map_num':3,'x':2,'y':2,'shop_dispatch_injected':False,'guarded_host_writes':0},'setup')
    opens=[r for r in rows if 'shop_open' in r]
    need(len(opens)==2 and [r['shop_open'] for r in opens]==['b','row'],'two real menu opens')
    for r in opens:
        need(set(r)=={'shop_open','eligible_count','window','callback','native_tasks'},'menu fields')
        prior.old.old.integer(r['eligible_count'],1,23,'eligible count');prior.old.old.integer(r['window'],0,31,'native window');prior.old.old.integer(r['callback'],0x093bd001,0x093bffff,'Research callback')
        need(type(r['native_tasks']) is int and r['native_tasks']==1,'one native menu task')
    need(opens[0]['eligible_count']==opens[1]['eligible_count'] and opens[0]['callback']==opens[1]['callback'],'stable native menu route')
    events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
    need([r['event'] for r in events]==list(STAGES) and [r['ledger_event'] for r in ledgers]==list(STAGES),'closed stage sequence')
    count=opens[0]['eligible_count'];frames=rows[-1].get('frames_after_warp');prior.old.old.integer(frames,900,20000,'bounded observed frames')
    prior.exact(rows[-1],result(count,(count+4)//5,frames),'native result')
    for i,(ev,le) in enumerate(zip(events,ledgers)):
        need(set(ev)==prior.old.lc.EVENT_FIELDS and set(le)==prior.old.lc.LEDGER_FIELDS,'complete inventory/ledger evidence')
        prior.old.old.integer(ev['counter'],1,100,'counter')
        need(ev['counter']==events[0]['counter']+int(i>=3),'cancel zero saves then exactly one normal Save')
        for key in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            prior.old.old.digest(ev[key]);need(ev[key]==events[0][key],'unchanged '+key)
        for key in ('item_quantity','party_count'):
            prior.old.old.integer(ev[key],0,999,'quantity');need(ev[key]==events[0][key],'unchanged '+key)
        need(1<=ev['party_count']<=6,'valid party')
        owner=bytes.fromhex(ev['owner']);need(len(owner)==64 and owner[7]<=2,'complete bounded owner')
        expected=bytearray(64);expected[0],expected[1],expected[6],expected[36]=1,64,1,1;expected[4]=100;expected[7]=owner[7]
        need(owner==expected,'no RP spending/earning/claims/transaction')
        for key in ('ledger_sha256','unrelated_ledger_sha256'):prior.old.old.digest(le[key])
        need(le['unrelated_ledger_sha256']==ledgers[0]['unrelated_ledger_sha256'],'all unrelated ledger bytes')
        for key,value in {'version':2,'size':2048,'checksum_valid':True,'migration_dirty':0,'recovery_blocked':0}.items():need(type(le[key]) is type(value) and le[key]==value,'ledger '+key)
    return dict(rows[-1],binding=binding,fixture=setup,menu_observations=opens,observations=events,ledger_observations=ledgers,stdout=identity(raw))
