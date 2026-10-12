#!/usr/bin/env python3
"""稼得・保存・支出・UIを独立に結合。表示修正で成功した取引を再実行しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import pr16_research_photo as fixture_model
import pr16_research_shop_ui as patch
ROOT=Path(__file__).resolve().parents[1]
BASE='content/modernization/pr16_research_natural_spending_evidence'
EARN='cc097fbcb05f57ebb3ed99404cf88e10de1abba6838e43b3f82c5f5c8b1d6ac7'
SPEND='985f5897214830b8db4cd0c9afc4a1c5dadf1ecb19f3b03bf2f9d9e958699d51'
EARNED_SAVE='b51c88f69600a8cbf85a152bb96aec5c6844df7cf299e9c0a464f324dba3ebba'
SPENT_SAVE='f4309eaa866100ee4cafef4f4980bad98e3b05d1eea11393727d2e0c6624c434'
ZERO='434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'
EARNED_FLASH='4b3ab306a49b58ef43a6b0c35a5fc6442dce2cb90283391fd5606536797571a0'
SPENT_FLASH='ee0789ac11cd05fccc659c902e877cb71cbbed0ea1cad98283b672c958c1f27d'
PARTY='d87f63c3bf5fa33e6b0702923541fd5e502f8b19f8f1c30f527effe9388102bc'
BASE_BAG='688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
BOUGHT_BAG='2ab0f0bb993a1c3f12489a087a65dfac2cb65c0adf6b61649ee5d79cd1bf84bf'
STAGES={
 'earn':('earning_fixture','earned'),
 'spend':('earned_continue','outside','door_entered','shop_stance','page_0','page_1','page_2','page_3','pages_closed','buy_open','selected','confirmation','purchased','purchase_continue','zero_balance_menu','end'),
 'ui':('earned_continue','outside','door_entered','shop_stance','page_0','page_1','page_2','page_3','pages_closed','selected','confirmation','declined','purchase_continue','zero_balance_menu','end')}
STATE=set('kind stage frame map field shop_active page eligible window counter rp lifetime next_transaction selected result item4 inventory_sha256 other_inventory_sha256 flash_sha256 window0 shop_descriptor text'.split())
EVENT=set('event counter item_quantity inventory_sha256 other_inventory_sha256 party_sha256 party_count owner'.split())
LEDGER=set('ledger_event version size checksum_valid ledger_sha256 unrelated_ledger_sha256 migration_dirty recovery_blocked'.split())
INPUT=set('kind keys frames start_frame'.split())
SCREEN=set('kind stage name sha256 frame'.split())
SUMMARIES={
 'earn':dict(kind='summary',status='PASS_EARNING_PREFIX',fresh_cores=1,earned_rp=10,automatic_saves=2,manual_saves=0,old_matrix_executions=0,retained_earned_input=True,natural_story_progress_accepted=False,warnings_errors=0),
 'spend':dict(kind='summary',status='PASS_NATURALLY_EARNED_SPENDING_MEASURED',fresh_cores=2,initial_earned_rp=10,spent_rp=10,final_rp=0,lifetime_rp=10,catalog=0,item=4,quantity=5,automatic_spend_saves=2,manual_saves=0,pages=4,guarded_host_writes=0,old_matrix_executions=0,natural_travel_accepted=False,natural_story_progress_accepted=False,warnings_errors=0),
 'ui':dict(kind='summary',status='PASS_SHOP_UI_ONLY_IMPACT',fresh_cores=2,new_earnings=0,new_purchases=0,new_saves=0,pages=4,confirmation_declined=True,zero_balance_revisit=True,old_matrix_executions=0,natural_travel_accepted=False,natural_story_progress_accepted=False,warnings_errors=0)}

def need(ok,why):
    if not ok:raise ValueError(why)

def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))

def integer(n,low,high):need(type(n) is int and low<=n<=high,'bounded integer/type');return n

def load(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def parse(raw):
    need(type(raw) is bytes and 0<len(raw)<40000 and raw.endswith(b'\n'),'complete bounded transcript')
    return [load(x) for x in raw.splitlines()]

def observations(rows,key):return [r for r in rows if key in r]

def validate_rows(rows,mode,zero):
    """Semantic oracle: mutation tests call this before outer file/hash checks."""
    need(mode in STAGES and type(rows) is list and all(type(r) is dict for r in rows),'known evidence mode')
    need(identity(zero)==dict(size=131072,sha256=ZERO),'immutable zero-credit fixture not post-close file')
    need(len(rows)=={'earn':12,'spend':97,'ui':93}[mode], 'closed original row count')
    need(sum(r.get('kind')=='summary' for r in rows)==1, 'one terminal summary')
    need(exact(rows[-1],SUMMARIES[mode]),'scope/counts/native terminal')
    states=[r for r in rows if r.get('kind')=='state'];events=observations(rows,'event');ledgers=observations(rows,'ledger_event')
    stages=STAGES[mode]
    need([r['stage'] for r in states]==list(stages) and [r['event'] for r in events]==list(stages)
         and [r['ledger_event'] for r in ledgers]==list(stages),'complete ordered stages without duplicates')
    # Each state must be immediately followed by its full owner and ledger observation.
    for i,row in enumerate(rows):
        if row.get('kind')=='state':need(i+2<len(rows) and rows[i+1].get('event')==row['stage'] and rows[i+2].get('ledger_event')==row['stage'],'owner/ledger interleaving')
    old=fixture_model.purchase.prior.prior.old;at=fixture_model.purchase.prior.prior.OFFSET
    source=zero[at:at+2048];baseline=bytearray(64);baseline[0]=1;baseline[1]=64;baseline[6]=1;baseline[36]=1
    need(source[:8]==b'VGS1\x02\0\0\x08' and source[0x73f:0x77f]==baseline and old.seal(source)==source,'independent source ledger and checksum')
    flash_zero=identity(zero)['sha256'];last=0
    for s,e,l in zip(states,events,ledgers):
        stage=s['stage'];need(set(s)==STATE and set(e)==EVENT and set(l)==LEDGER,'closed complete observation schemas')
        frame=integer(s['frame'],last,20000);last=frame
        earned=stage!='earning_fixture';bought=stage in ('purchased','purchase_continue','zero_balance_menu','end') and mode!='earn'
        minute=0 if not earned else 2 if stage in ('zero_balance_menu','end') else 1
        owner=bytearray(baseline);owner[7]=minute
        if earned:owner[4]=10;owner[10]=10;owner[22]=10;owner[27]=2;owner[36]=2
        if bought:owner[4]=0;owner[36]=3
        count=2+2*int(earned)+2*int(bought);bag=BOUGHT_BAG if bought else BASE_BAG
        want=dict(event=stage,counter=count,item_quantity=5*int(bought),inventory_sha256=bag,other_inventory_sha256=BASE_BAG,
                  party_sha256=PARTY,party_count=1,owner=owner.hex())
        need(exact(e,want),'complete owner64/Bag2048/party600/counter '+stage)
        modeled=bytearray(source);modeled[0x73f:0x77f]=owner;modeled=old.seal(modeled)
        unrelated=bytearray(modeled);unrelated[4:6]=bytes(2);unrelated[8:12]=bytes(4);unrelated[0x73f:0x77f]=bytes(64)
        need(exact(l,dict(ledger_event=stage,version=2,size=2048,checksum_valid=True,ledger_sha256=identity(modeled)['sha256'],
            unrelated_ledger_sha256=identity(unrelated)['sha256'],migration_dirty=0,recovery_blocked=0)),'whole independent ledger2048 '+stage)
        for key,val in dict(counter=count,rp=owner[4],lifetime=10*int(earned),next_transaction=owner[36],item4=5*int(bought),
                             inventory_sha256=bag,other_inventory_sha256=BASE_BAG).items():need(exact(s[key],val),'independent state '+key)
        need(s['flash_sha256']==(SPENT_FLASH if bought else EARNED_FLASH if earned else flash_zero),'exact flash boundary '+stage)
        # Native user activity cannot alter or delete the shared dialogue window.
        need(s['window0']=='00020f1a040f980150200002','dialogue window owns original pixel allocation')
        menu=stage.startswith('page_') or stage in ('buy_open','zero_balance_menu')
        need(type(s['field']) is bool and type(s['shop_active']) is bool and s['shop_active']==menu,'native window/task state')
        if menu:
            page=int(stage[-1]) if stage.startswith('page_') else 0
            need(exact([s['field'],s['page'],s['eligible'],s['window'],s['selected'],s['result']],[False,page,19,1,65535,9]),'stock menu state')
            need(s['shop_descriptor']==('000801150e0f3800602d0002' if page==3 else '00080115100f3800602d0002'),'pixel/frame separation and visible top margin')
        else:
            need(s['shop_descriptor']=='' and type(s['window']) is int and s['window']==255,'owned window released')
            expected_field=stage not in ('earned','selected','confirmation')
            need(s['field'] is expected_field,'field/script lock')
        if mode!='earn':
            loc=[97,82,13,27] if stage=='earned_continue' else [96,0,16,14] if stage=='outside' else [98,3,6,12] if stage=='door_entered' else [98,3,2,2]
            # The earned snapshot may be on the completed rock tile; exact location is a declared fixture contract.
            if stage!='earned_continue':need(exact(s['map'],loc),'physical outdoor/door/shop route')
        text=s['text'];need(type(text) is str and len(text)%2==0 and 2<=len(text)<=384,'bounded text buffer')
        if stage in ('selected','confirmation','declined'):
            need(text=='0a2a140a03062efe0c1f0d06acff' and s['selected']==0 and s['result']==10,'stock confirmation text/selection')
        if stage=='purchased':need(s['selected']==0 and s['result']==0,'actual transaction success')
    candidates={'earn':EARN,'spend':SPEND,'ui':patch.CANDIDATE['sha256']}
    ins=[r for r in rows if r.get('kind')=='input_save']
    expected=[dict(kind='input_save',mode={'earn':'earn','spend':'spend','ui':'ui-only'}[mode],sha256=ZERO if mode=='earn' else EARNED_SAVE,candidate=candidates[mode])]
    if mode=='ui':expected.append(dict(kind='input_save',mode='ui-spent',sha256=SPENT_SAVE,candidate=candidates[mode]))
    need(exact(ins,expected) and rows[0]==ins[0],'saved input chain/candidate, no fixture credit')
    if mode!='earn':
        rel=[r for r in rows if r.get('kind')=='relocation_fixture']
        need(exact(rel,[dict(kind='relocation_fixture',stock_warp_calls=4,field_callback_writes=1,rp_injected=False,natural_travel_accepted=False)]),'declare geographic fixture honestly')
        opens=observations(rows,'shop_open');names=['pages','purchase','after_spend'] if mode=='spend' else ['ui_pages','ui_decline','ui_zero']
        need(exact(opens,[dict(shop_open=n,eligible_count=19,window=1,callback=0x093bf5a5,native_tasks=1) for n in names]),'one owned menu task for each opening')
    else:
        setup=observations(rows,'setup');visits=observations(rows,'visit')
        need(len(visits)==1 and exact(setup,[dict(setup='mining',events=155269952,record=155269500,script=154928396,badge=1,move=249,party_count=1,progression_is_fixture=True,rp_injected=False)]),'explicit original root/progression fixture')
        need(exact(visits[0],dict(visit='spending_input',confirmed=True,eligible=True,result=0,rp=10,counter=4,rock_count=0,frame=2578,stopped_before_wild_tail=True)),'real mining event, not injected reward')
    allowed={'state','input','screen','input_save','relocation_fixture','summary'}
    lastinput=0
    for r in rows:
        if 'kind' in r:
            need(r['kind'] in allowed,'unknown row kind')
            if r['kind']=='input':
                need(set(r)==INPUT,'input fields');integer(r['keys'],0,128);need(r['keys'] in (0,1,2,16,32,64,128),'physical key only');integer(r['frames'],1,1200);lastinput=integer(r['start_frame'],lastinput,20000)
            if r['kind']=='screen':
                need(set(r)==SCREEN and r['stage'] in stages and r['name']==r['stage']+'.ppm','closed real screen');integer(r['frame'],0,20000)
        else:need(any(k in r for k in ('event','ledger_event','shop_open','setup','visit','screen')),'unknown raw row')
    screens=[r for r in rows if r.get('kind')=='screen']
    names=[s['name'] for s in screens] if mode!='earn' else [r['screen'] for r in rows if 'screen' in r]
    need(len(names)==len(set(names))=={'earn':2,'spend':14,'ui':12}[mode],'complete unique native screenshots')
    return dict(mode=mode,observed_stages=len(states),candidate=candidates[mode],screens=len(names),status='PASS_SCOPED_SEMANTIC_ORACLE')

def validate(root,zero):
    root=Path(root);result={}
    for folder,mode in [('earn-1','earn'),('spend-3','spend'),('ui-final','ui')]:
        execution=load((root/folder/'execution.json').read_bytes());raw=(root/folder/'stdout.txt').read_bytes();err=(root/folder/'stderr.txt').read_bytes()
        need(type(execution['returncode']) is int and execution['returncode']==0 and err==b'' and identity(raw)==execution['stdout'] and identity(err)==execution['stderr'],'original clean native stdout/stderr')
        rows=parse(raw);result[mode]=validate_rows(rows,mode,zero)
        measured={r['name']:dict(size=115215,sha256=r['sha256']) for r in rows if r.get('kind')=='screen'}
        if mode=='earn':measured={r['screen']:dict(size=115215,sha256=r['sha256']) for r in rows if 'screen' in r}
        need(exact(measured,execution['screens']),'original screen identity set')
    e=load((root/'earn-1/execution.json').read_bytes());s=load((root/'spend-3/execution.json').read_bytes());u=load((root/'ui-final/execution.json').read_bytes())
    need(e['output']==s['input']==u['inputs']['earned.srm']==dict(size=131088,sha256=EARNED_SAVE),'retained earned save, no repeat/injection')
    need(s['output']==u['inputs']['spent.srm']==dict(size=131088,sha256=SPENT_SAVE) and u['inputs']==u['outputs'],'UI-only changed no save byte, footer included')
    review=load((root/'visual-review.json').read_bytes())
    need(review['completed'] is True and review['screens']==u['screens'] and review['reviewed_screens']==12
         and review['candidate']==patch.CANDIDATE and review['method']=='ASSISTANT_VISUAL_REVIEW_NO_OCR'
         and review['natural_story_progress_accepted'] is False and review['whole_game_visual_quality_accepted'] is False,'independent visual review with limited scope')
    return dict(status='PASS_NATURALLY_EARNED_RP_SPENDING_AND_SHOP_UI_SCOPED',candidate=patch.CANDIDATE,
        observations=result,naturally_earned_spending_accepted=True,shop_ui_accepted=True,natural_travel_accepted=False,
        natural_story_progress_accepted=False,release_ready=False,active_baseline_changed=False,issue19_complete=False,
        new_recording_native_processes=0,accepted_case_reruns=0)
