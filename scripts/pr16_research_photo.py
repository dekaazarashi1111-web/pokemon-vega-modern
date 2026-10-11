#!/usr/bin/env python3
"""0RPから実写真イベントを観測。進行/開始座標fixtureと自然稼得を区別する。"""
from pathlib import Path
import pr16_research_catalog as catalog
import pr16_research_purchase as purchase
need, identity, load, exact = catalog.need, catalog.identity, catalog.load, catalog.exact
ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_photo.c'
CASE = 'photo-zero-earn-duplicate-cold-continue'
CANDIDATE = catalog.CANDIDATE
STAGES = ('fixture','declined','earned','duplicate','continued','duplicate_after_continue')
BINDING = dict(binding='map96/37-background0', events=0x09413750, backgrounds=0x09413708,
               script=0x093C05E4, x=48, y=4, activity=5, points=6, cap=6)

def fixture(seed):
    original, _ = purchase.fixture(seed)
    old = purchase.prior.prior.old
    offset = purchase.prior.prior.OFFSET
    ledger = bytearray(original[offset:offset+2048]);ledger[0x743:0x745]=bytes(2)
    ledger = old.seal(ledger)
    out = original[:offset]+ledger+original[offset+2048:]
    need(out[:offset]==seed[:offset] and out[offset+2048:]==seed[offset+2048:], 'ledger以外は原本不変')
    return out, dict(seed=identity(seed),fixture=identity(out),ledger=identity(ledger),offset=offset,
                    initial_rp=0, initial_lifetime=0, progression_is_fixture=True,
                    balance_credit_injected=False,outside_ledger_changes=0,natural_arrival_claimed=False)

def generate(seed):
    source=catalog.generate(seed).decode();previous,_=purchase.fixture(seed);current,_=fixture(seed)
    token='int main(int argc,char**argv){'
    need(source.count(token)==1 and source.count(identity(previous)['sha256'])==1,'唯一のmain/fixture')
    source=source.replace(token,'int accepted_catalog_main(int argc,char**argv){').replace(identity(previous)['sha256'],identity(current)['sha256'])
    return (source+'\n'+(ROOT/C).read_text()).encode()

def closing():
    return dict(status='PASS',case=CASE,candidate_sha256=CANDIDATE['sha256'],fresh_cores=2,
                initial_rp=0,earned_rp=6,daily_photo=6,simple_claims=4,transaction_saves=2,
                manual_saves=0,guarded_host_writes=0,real_photo_earning_accepted=True,
                all_activities_accepted=False,natural_arrival_accepted=False,
                shop_connection_accepted=False,accepted_case_reruns=0,warnings_errors=0)

SCREENS = {
    'photo-decline-prompt.ppm':'b7bed16f0c7216dea297a2c408332b193f26272bd90ded4efc38259516784895',
    'photo-earn-prompt.ppm':'b7bed16f0c7216dea297a2c408332b193f26272bd90ded4efc38259516784895',
    'photo-earn-outcome.ppm':'080a24f32325bfa0bb11451545bd36fed684f0d869b7cb9da04e81fcedc82b3b',
    'photo-duplicate-prompt.ppm':'b7bed16f0c7216dea297a2c408332b193f26272bd90ded4efc38259516784895',
    'photo-duplicate-outcome.ppm':'c0165cbdc34c4dc31b3001f45f3115dae123e7605fb97221a9c66eca0c2f356a',
    'photo-duplicate_after_continue-prompt.ppm':'b508cb0b06119028b846352208d12d84949e99b8b4cb0d39e8959adb8ae62a37',
    'photo-duplicate_after_continue-outcome.ppm':'9e5f6272bbfc690a35b2eb2cfe242d2c23953dba1d22f7f82b2798ec3031971f',
}

def physical(rom):
    import struct
    need(identity(rom)==CANDIDATE, '現候補full SHA')
    def rd(a):return struct.unpack('<I',catalog.span(rom,a,4))[0]
    events=rd(0x092C0B20);bgs=rd(events+16);script=rd(bgs+8)
    need((events,bgs,script)==(BINDING['events'],BINDING['backgrounds'],BINDING['script']), '正規photo root chain')
    need(catalog.span(rom,bgs,8)==bytes.fromhex('3000040000000000'), '指定viewpoint座標/type')
    model=load((ROOT/catalog.MODEL).read_bytes())
    row=model['activities'][5]
    need(row['activity']=='PHOTOGRAPHY' and row['points_awarded']==6 and row['daily_cap']==6
         and row['completion_semantics']=='VIEWPOINT_CONFIRM_AND_DAILY_CLAIM_CLEAR', 'photo policy正本')
    dialogues=[r for r in model['dialogue'] if r['binding_key']=='BINDING_KEY_ACTIVITY_PHOTO']
    need(len(dialogues)==3,'photo 3会話')
    for r in dialogues:
        raw=catalog.encoded(r['encoded_hex']);need(catalog.span(rom,r['runtime_address'],len(raw))==raw,'photo文言byte')
    return dict(binding=BINDING,script=identity(catalog.span(rom,script,94)),dialogues=dialogues,
                candidate=identity(rom),points_injected=False,natural_arrival_claimed=False)

def validate(raw, save):
    old=purchase.prior.prior.old
    need(type(raw) is bytes and 0<len(raw)<24000 and len(save)==131072,'有界の原本/fixture')
    rows=[load(line) for line in raw.splitlines()]
    order=['binding','event','ledger_event','prompt','visit','event','ledger_event',
           'prompt','outcome','visit','event','ledger_event','prompt','outcome','visit',
           'event','ledger_event','event','ledger_event','prompt','outcome','visit',
           'event','ledger_event','status']
    need(len(rows)==len(order) and all(k in row for k,row in zip(order,rows)), '全25行の順序')
    need(exact(rows[0],BINDING) and exact(rows[-1],closing()),'固定scope/root/result')
    visits=[r for r in rows if 'visit' in r];labels=['decline','earn','duplicate','duplicate_after_continue']
    need([r['visit'] for r in visits]==labels,'4回の実event')
    last=900
    for i,r in enumerate(visits):
        frame=catalog.integer(r['frame'],last+1,10000);last=frame
        need(exact(r,dict(visit=labels[i],confirmed=i!=0,activity_result=0 if i<2 else 4,frame=frame)),'event結果の型/値')
    screens={}
    for r in rows:
        if 'prompt' not in r and 'outcome' not in r:continue
        kind='prompt' if 'prompt' in r else 'outcome';stage=r[kind]
        name=f'photo-{stage}-{kind}.ppm';need(name in SCREENS and name not in screens,'screen scope/重複')
        expected={kind:stage,'screen_sha256':SCREENS[name]}
        if kind=='prompt':expected['entry_keys']=64 if stage=='decline' else 1
        need(exact(r,expected),'目視済み実画面とキー境界');screens[name]=r['screen_sha256']
    need(set(screens)==set(SCREENS),'全7実画像')
    events=[r for r in rows if 'event' in r];ledgers=[r for r in rows if 'ledger_event' in r]
    need([r['event'] for r in events]==list(STAGES) and [r['ledger_event'] for r in ledgers]==list(STAGES),'6状態の順序')
    source=save[purchase.prior.prior.OFFSET:purchase.prior.prior.OFFSET+2048]
    baseline=bytearray(64);baseline[0],baseline[1],baseline[6],baseline[36]=1,64,1,1
    need(source[:8]==b'VGS1\x02\0\0\x08' and old.checksum(source)==int.from_bytes(source[8:12],'little'),'fixture checksum')
    need(source[0x73f:0x77f]==baseline,'0RP/未稼得/未claimを全ownerで要求')
    first=events[0]
    for i,(event,ledger) in enumerate(zip(events,ledgers)):
        earned=i>=2
        need(set(event)==old.lc.EVENT_FIELDS and set(ledger)==old.lc.LEDGER_FIELDS,'全観測field')
        catalog.integer(event['counter'],1,100);need(event['counter']==first['counter']+2*earned,'取引だけの2保存')
        catalog.integer(event['party_count'],1,6);catalog.integer(event['item_quantity'],0,999)
        for key in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            old.old.digest(event[key]);need(event[key]==first[key],'全Bag/party不変 '+key)
        need(event['party_count']==first['party_count'] and event['item_quantity']==first['item_quantity'],'同一party/所持数')
        text=event['owner'];need(type(text) is str and len(text)==128 and all(c in '0123456789abcdef' for c in text),'全64byte owner')
        owner=bytes.fromhex(text);expected=bytearray(baseline);expected[7]=owner[7]
        need(owner[7]<=2,'有界自然minute')
        if earned:
            expected[4]=6;expected[10]=6;expected[24]=6;expected[27]=4;expected[36]=2
        need(owner==expected,'残高/日内/生涯/claim/取引/予約の全byte')
        modeled=bytearray(source);modeled[0x73f:0x77f]=owner;modeled=old.seal(modeled)
        unrelated=bytearray(modeled);unrelated[4:6]=bytes(2);unrelated[8:12]=bytes(4);unrelated[0x73f:0x77f]=bytes(64)
        need(exact(ledger,dict(ledger_event=STAGES[i],version=2,size=2048,checksum_valid=True,
             ledger_sha256=identity(modeled)['sha256'],unrelated_ledger_sha256=identity(unrelated)['sha256'],
             migration_dirty=0,recovery_blocked=0)),'全ledger2048と独立checksum')
    return dict(closing(),screens=screens,visits=visits,observations=events,ledger_observations=ledgers,stdout=identity(raw))
