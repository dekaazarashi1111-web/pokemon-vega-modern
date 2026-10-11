#!/usr/bin/env python3
"""実UI選択/購入/残高不足の限定fixtureとfail-closed原本validator。"""
from __future__ import annotations
from pathlib import Path
import pr16_research_shop_cancel as prior
need, identity = prior.need, prior.identity
CANDIDATE = prior.CANDIDATE
C = 'tools/mgba_pr16_research_purchase.c'
CASE = 'shop-select-purchase-insufficient-save-continue'
SCOPE = 'NATIVE_RESEARCH_SELECTION_PURCHASE_INSUFFICIENT_AND_SAVE_CONTINUE'
STAGES = ('fixture','selected_decline','declined','selected_buy','purchased','transaction_continue','selected_insufficient','insufficient','saved','continued','continued_again')
CATALOG = {'address':0x093BF9EC,'size':368,'sha256':'5f27149befecf94ea7adf054fde2865c3fb75ead165c2e30b7a38a5e2b842286'}


def fixture(seed):
    original,_ = prior.fixture(seed)
    at = prior.prior.OFFSET
    ledger = bytearray(original[at:at+2048]);ledger[0x743:0x745]=(10).to_bytes(2,'little')
    ledger = prior.prior.old.seal(ledger)
    out = original[:at]+ledger+original[at+2048:]
    return out, {'seed':identity(seed),'fixture':identity(out),'ledger':identity(ledger),'offset':at,'size':2048,'outside_ledger_changes':0,'progress_and_balance_are_fixtures':True,'natural_progress_claimed':False}


def generate(seed):
    original,_=prior.fixture(seed);current,_=fixture(seed)
    text=prior.generate(seed).decode();token='int main(int argc,char**argv){'
    need(text.count(token)==1 and text.count(identity(original)['sha256'])==1,'unique inherited main/fixture')
    text=text.replace(token,'int accepted_shop_cancel_main(int argc,char**argv){').replace(identity(original)['sha256'],identity(current)['sha256'])
    return (text+'\n'+Path(C).read_text()).encode()


def result(frames):
    return {'status':'PASS','scope':SCOPE,'case':CASE,'candidate_sha256':CANDIDATE['sha256'],'fresh_cores':4,'catalog':0,'item':4,'price':10,'quantity':5,'manual_saves':1,'transaction_saves':2,'host_write_barriers':7,'guarded_host_writes':0,'frames_after_warp':frames,'fixture_warp_calls':4,'fixture_field_callback_writes':1,'normal_new_game_accepted':False,'purchase_accepted':True,'natural_progress_accepted':False,'warnings_errors':0}


def validate(raw, save):
    need(0<len(raw)<=32000 and len(save)==131072,'bounded complete observations/fixture')
    old=prior.prior.old;closed=prior.prior.exact
    rows=[old.old.load(line) for line in raw.decode().splitlines()]
    need(len(rows)==27,'closed native row count')
    closed(rows[0],{'binding':'map98/3-background0','events':0x09413C50,'backgrounds':0x09413C14,'script':0x093C0328,'catalog':0,'item':4,'price':10,'quantity':5},'authored root/catalog')
    frames=rows[-1].get('frames_after_warp');old.old.integer(frames,900,30000,'bounded frame count');closed(rows[-1],result(frames),'native result')
    opens=[r for r in rows if 'shop_open' in r];need([r['shop_open'] for r in opens]==['decline','buy','insufficient'],'three distinct menus')
    for r in opens:
        need(set(r)=={'shop_open','eligible_count','window','callback','native_tasks'},'closed native menu')
        old.old.integer(r['eligible_count'],1,23,'eligible count');old.old.integer(r['window'],0,31,'window');old.old.integer(r['callback'],0x093BD001,0x093BFFFF,'callback')
        need(type(r['native_tasks']) is int and r['native_tasks']==1,'one menu task')
        need((r['eligible_count'],r['callback'])==(opens[0]['eligible_count'],opens[0]['callback']),'same catalog route')
    events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
    need([r['event'] for r in events]==list(STAGES) and [r['ledger_event'] for r in ledgers]==list(STAGES),'closed stage order')
    expected_order=['binding']
    for i in range(len(STAGES)):
        if i in (1,3,6):expected_order.append('shop_open')
        expected_order.extend(('event','ledger_event'))
    expected_order.append('status')
    need(all(k in row for k,row in zip(expected_order,rows)),'interleaving order')
    source=save[old.OFFSET:old.OFFSET+2048]
    need(source[:8]==b'VGS1\x02\0\0\x08' and old.checksum(source)==int.from_bytes(source[8:12],'little'),'fixture full ledger/checksum')
    baseline=bytearray(64);baseline[0],baseline[1],baseline[4],baseline[6],baseline[36]=1,64,10,1,1
    need(source[0x73f:0x77f]==baseline,'exact initial owner')
    first=events[0]
    for i,(ev,le) in enumerate(zip(events,ledgers)):
        bought=i>=4;delta=2*int(bought)+int(i>=8)
        need(set(ev)==old.lc.EVENT_FIELDS and set(le)==old.lc.LEDGER_FIELDS,'complete event schemas')
        old.old.integer(ev['counter'],1,100,'counter');need(ev['counter']==first['counter']+delta,'exact persistence boundary')
        old.old.integer(ev['item_quantity'],0,999,'item quantity');need(ev['item_quantity']==first['item_quantity']+5*int(bought),'exact purchased quantity')
        old.old.integer(ev['party_count'],1,6,'party count');need(ev['party_count']==first['party_count'],'party count preserved')
        for key in ('inventory_sha256','other_inventory_sha256','party_sha256'):old.old.digest(ev[key])
        for key in ('other_inventory_sha256','party_sha256'):need(ev[key]==first[key],'unrelated '+key)
        need(ev['inventory_sha256']==events[4 if bought else 0]['inventory_sha256'],'inventory stage unchanged')
        if bought:need(ev['inventory_sha256']!=first['inventory_sha256'],'real Bag changed')
        need(isinstance(ev['owner'],str) and len(ev['owner'])==128 and all(c in '0123456789abcdef' for c in ev['owner']),'canonical complete owner')
        owner=bytes.fromhex(ev['owner']);want=bytearray(baseline);want[7]=owner[7]
        need(owner[7]<=2,'bounded natural minute')
        if bought:want[4]=0;want[36]=2
        need(owner==want,'exact balance/transaction/claim/pending state')
        modeled=bytearray(source);modeled[0x73f:0x77f]=owner;modeled=old.seal(modeled)
        unrelated=bytearray(modeled);unrelated[4:6]=bytes(2);unrelated[8:12]=bytes(4);unrelated[0x73f:0x77f]=bytes(64)
        closed(le,{'ledger_event':STAGES[i],'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':identity(modeled)['sha256'],'unrelated_ledger_sha256':identity(unrelated)['sha256'],'migration_dirty':0,'recovery_blocked':0},'full ledger '+STAGES[i])
    return dict(rows[-1],binding=rows[0],menu_observations=opens,observations=events,ledger_observations=ledgers,stdout=identity(raw))
