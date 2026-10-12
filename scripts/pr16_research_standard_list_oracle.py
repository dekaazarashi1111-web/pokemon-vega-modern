#!/usr/bin/env python3
"""生traceから標準リストの状態・所有資源・非取引不変条件を独立照合する。"""
from pathlib import Path
import re
import struct
from pr16_research_counter_oracle import need, exact, identity, load, STATE_FIELDS, BAG, PARTY
ROOT=Path(__file__).resolve().parents[1]
FIXTURE={'size':131072,'sha256':'434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'}
COMMAND={'size':637,'sha256':'119142a17842f459735db933be963bb70c05464375364fca1032900c8471aac8'}
CANDIDATE={'size':33554432,'sha256':'37f73b807c452165c37764a2b80811d2779f456e451175402a7d93ae6a746113'}
MENUS={'menu_first','menu_after_balance','guide_cursor','menu_after_guide','menu_revisit','exit_cursor','menu_third'}
TEXTS={'counter_intro':'COUNTER_INTRO','revisit_intro':'COUNTER_INTRO','third_intro':'COUNTER_INTRO',
       'guide_one':'COUNTER_ACTIVITY_1','guide_two':'COUNTER_ACTIVITY_2',
       'b_cancel_message':'COUNTER_REVISIT','exit_message':'COUNTER_REVISIT','third_cancel_message':'COUNTER_REVISIT'}
FIELDS={'fixture','door_entered','counter_approach','b_cancel_closed','exit_closed','third_closed','end','final'}
MENU_FIELDS={'menu','result','task_count','tasks','last_window','window_descriptor','stock_menu','rp','rank','buffers'}


def validate(raw,commands,fixture,screens):
    need(type(raw) is bytes and 0<len(raw)<150000 and raw.endswith(b'\n'),'complete bounded transcript')
    need(type(commands) is bytes and exact(identity(commands),COMMAND),'independent fixed physical command binding')
    need(type(fixture) is bytes and exact(identity(fixture),FIXTURE),'immutable preboot zero-RP fixture')
    program=[(int(k),int(n),l) for k,n,l in (line.split() for line in commands.decode('ascii').splitlines())]
    labels=[l for _,_,l in program if l!='step']
    need(type(screens) is dict and set(screens)=={l+'.ppm' for l in labels} and len(labels)==22,'complete 22-screen matrix')
    for b in screens.values():
        need(type(b) is dict and set(b)=={'size','sha256'} and exact(b['size'],115215)
             and type(b['sha256']) is str and re.fullmatch('[a-f0-9]{64}',b['sha256']) is not None,'canonical PPM identity')
    model=load((ROOT/'content/research_economy_v1/canonical_model.json').read_bytes())
    texts={r['dialogue_key']:r['encoded_hex'] for r in model['dialogue']}
    ledger=bytearray(fixture[0x1f064:0x1f064+2048]);owner=bytearray(ledger[0x73f:0x77f]);owner[7]=1
    ledger[0x73f:0x77f]=owner
    import pr16_research_photo as photo
    ledger=photo.purchase.prior.prior.old.seal(ledger)
    rest=bytearray(ledger);rest[4:6]=bytes(2);rest[8:12]=bytes(4);rest[0x73f:0x77f]=bytes(64)
    rows=[load(line) for line in raw.splitlines()];cursor=0;last_text='00'*128;owned_window=None
    def row():
        nonlocal cursor
        need(cursor<len(rows),'missing ordered row');v=rows[cursor];cursor+=1;need(type(v) is dict,'object row');return v
    def stage(label,command,frame,screen=False):
        nonlocal last_text,owned_window
        state=row();need(set(state)==STATE_FIELDS,'closed native state schema')
        position=[96,0,16,14] if label=='fixture' else [98,3,6,12] if label=='door_entered' else [98,3,6,4]
        expected={'state':label,'command':command,'frame':frame,'map':position,'field':label in FIELDS,
                  'callback':0x08055e75,'result':0,'shop_active':False,'eligible':0,'window':255,'flash_sha256':FIXTURE['sha256']}
        for k,v in expected.items():need(exact(state[k],v),'state invariant '+k+' at '+label)
        need(type(state['facing']) is int and 1<=state['facing']<=4,'typed facing')
        if label in TEXTS:last_text=texts['DIALOGUE_KEY_'+TEXTS[label]]
        if label=='balance_selected':last_text='ccca00a1fe777e5800a2ff'
        need(exact(state['text'],last_text),'full expanded dialogue at '+label)
        need(exact(row(),{'event':label,'counter':2,'item_quantity':0,'inventory_sha256':BAG,'other_inventory_sha256':BAG,
                         'party_sha256':PARTY,'party_count':6,'owner':bytes(owner).hex()}),'complete owner/Bag/party/counter invariant')
        need(exact(row(),{'ledger_event':label,'version':2,'size':2048,'checksum_valid':True,
                         'ledger_sha256':identity(ledger)['sha256'],'unrelated_ledger_sha256':identity(rest)['sha256'],
                         'migration_dirty':0,'recovery_blocked':0}),'complete ledger and no recovery effects')
        ob=row();need(set(ob)=={'objects'} and type(ob['objects']) is list and 1<=len(ob['objects'])<=16,'object snapshot')
        ids=[];player=[];host=[]
        for v in ob['objects']:
            need(type(v) is list and len(v)==6 and all(type(x) is int and 0<=x<=65535 for x in v),'typed object')
            need(v[0]<16 and v[1]<=255 and v[2:4]==position[:2],'object map');ids.append(v[0])
            if v[1]==255:player.append(v)
            if v[1]==4:host.append(v)
        need(len(ids)==len(set(ids)) and len(player)==1 and player[0][4:]==[position[2]+7,position[3]+7],'physical player')
        if label not in FIELDS:
            dx,dy={1:(0,1),2:(0,-1),3:(-1,0),4:(1,0)}[state['facing']]
            need(len(host)==1 and host[0][4:]==[player[0][4]+dx,player[0][5]+dy],'facing actual local4')
        menu=row();need(set(menu)==MENU_FIELDS and exact(menu['menu'],label),'closed menu schema')
        active=label in MENUS
        need(exact(menu['task_count'],int(active)) and type(menu['tasks']) is list and len(menu['tasks'])==int(active),'single owned native task')
        need(exact(menu['rp'],0) and exact(menu['rank'],1),'zero-credit list fixture unchanged')
        need(type(menu['result']) is int and 0<=menu['result']<=65535,'typed engine result')
        if command>=8:need(menu['result']==(65535 if active else 0),'async busy/selection result')
        if active:
            task=menu['tasks'][0]
            need(set(task)=={'id','window','debounce'} and type(task['id']) is int and 0<=task['id']<16
                 and type(task['window']) is int and 0<=task['window']<32 and exact(task['debounce'],0),'task state after debounce')
            if owned_window is None:owned_window=task['window']
            need(task['window']==owned_window,'revisit reuses released window')
        need(exact(menu['last_window'],255 if owned_window is None else owned_window),'observer window binding')
        desc=menu['window_descriptor'];need(type(desc) is str,'window descriptor type')
        if owned_window is None:need(desc=='','no window before first open')
        elif active:
            need(re.fullmatch('[a-f0-9]{24}',desc) is not None,'full active descriptor')
            b=bytes.fromhex(desc);tile=struct.unpack_from('<I',b,8)[0]
            need(b[:6]==bytes([0,9,1,20,6,15]) and 0<struct.unpack_from('<H',b,6)[0]<0x400
                 and 0x02000000<=tile<0x02040000 and tile%4==0,'standard three-row window allocation')
        else:need(desc=='ff0000000000000000000000','window resources released between messages and on exit')
        need(type(menu['stock_menu']) is str and re.fullmatch('[a-f0-9]{32}',menu['stock_menu']) is not None,'bounded stock menu observation')
        bs=menu['buffers'];need(type(bs) is list and len(bs)==2,'two native buffers')
        for v in bs:need(type(v) is str and re.fullmatch(r'(?:[a-f0-9]{2}){1,20}',v) is not None,'bounded native buffer')
        if command>=10:need(exact(bs,['a1ff','a2ff']),'selected balance/rank uses native buffers')
        if screen:need(exact(row(),{'screen':label,'command':command,'frame':frame,'sha256':screens[label+'.ppm']['sha256']}),'same-frame screenshot')
    frame=900;stage('fixture',0,frame)
    for i,(key,frames,label) in enumerate(program,1):
        need(exact(row(),{'input':i,'keys':key,'frames':frames,'label':label}),'ordered physical input')
        frame+=frames
        if label!='step':stage(label,i,frame,True)
    stage('final',len(program),frame)
    terminal={'status':'MEASURED','scope':'COUNTER_STANDARD_LIST_ONLY','case':0,'fresh_cores':1,'commands':45,'screens':22,
              'guarded_host_writes':0,'manual_saves':0,'transaction_saves':0,'accepted_case_reruns':0,
              'natural_story_progress_accepted':False,'naturally_earned_spending_accepted':False,'warnings_errors':0}
    need(exact(row(),terminal) and cursor==len(rows),'terminal with no unsupported promotion/trailing rows')
    return {'status':'PASS_STANDARD_LIST_NATIVE_OBSERVATIONS','candidate':CANDIDATE,'stdout':identity(raw),'commands':identity(commands),
            'ledger':identity(ledger),'screens':screens,'visits':3,'functional_rows_selected':2,'b_cancels':2,'exit_row_selections':1,
            'single_task_and_window_lifecycle':True,'all_owner_ledger_bag_party_flash_counter_unchanged':True,
            'native_processes':1,'accepted_case_reruns':0,'standard_list_accepted':False,'visual_review_completed':False,
            'naturally_earned_spending_accepted':False,'natural_story_progress_accepted':False,'release_ready':False}
