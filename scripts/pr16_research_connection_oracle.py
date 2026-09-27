#!/usr/bin/env python3
"""入力traceと2048byte ledgerを別計算し、入口と会話の限定範囲だけ判定する。"""
from pathlib import Path
import hashlib
import json
import re
import pr16_research_photo as photo
ROOT=Path(__file__).resolve().parents[1]
FIXTURE={'size':131072,'sha256':'434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'}
COMMANDS={'lab':'048cb565a024a5f008fe40c42254685271bdcaf705d10da009406e2c6f22e776','fishing':'0cbe04754bbac7792d530ba02760df574b270864a33100ae74a8d2cedc52becd','game':'f7bd8f234ec498e1a9c50a83047a182405aafae4afca5b6e3cd996c18f019bd5','ecology':'7bd5e7a21909fd81053c08f5692b11d7a76f9e63eefe523da39209b5f52c8c91'}
OUTSIDE={'lab':[96,0,16,14],'fishing':[96,23,12,87],'game':[96,6,34,22],'ecology':[97,63,29,26]}
INSIDE={'lab':[98,3,6,12],'fishing':[98,110,3,7],'game':[98,56,9,13],'ecology':[97,67,4,9]}
DIALOGUES={'lab':{'counter_intro':'COUNTER_INTRO','counter_balance':'COUNTER_BALANCE','counter_activity_one':'COUNTER_ACTIVITY_1','counter_activity_two':'COUNTER_ACTIVITY_2','counter_revisit':'COUNTER_REVISIT','shop_intro':'SHOP_OPEN'},'fishing':{'guide_message':'FISHING_GUIDE','guide_cap':'FISHING_CAP'},'game':{'guide_message':'GAME_GUIDE','guide_cap':'GAME_CAP'},'ecology':{'guide_message':'ECOLOGY_GUIDE','guide_cap':'ECOLOGY_CAP'}}
STANCE={'lab':[98,3,6,4],'fishing':[98,110,4,5],'game':[98,56,11,2],'ecology':[97,67,3,5]}
STATE_FIELDS={'state','command','frame','map','facing','field','callback','result','shop_active','eligible','window','flash_sha256','text'}
BAG='688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
PARTY='55514c6b16a517c723e3cdfe4826075020b214905950ada9cd65b41a97419430'

def need(ok,reason):
    if not ok:raise ValueError(reason)
def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b

def load(raw):
    def pairs(rows):
        result={}
        for k,v in rows:
            need(k not in result,'duplicate JSON key');result[k]=v
        return result
    def bad(x):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def validate(raw,case,commands,fixture,screen_bindings):
    need(type(raw) is bytes and 0<len(raw)<100000 and raw.endswith(b'\n'),'bounded complete raw transcript')
    need(case in COMMANDS and type(commands) is bytes and identity(commands)['sha256']==COMMANDS[case],'closed reviewed physical input')
    need(type(fixture) is bytes and exact(identity(fixture),FIXTURE),'original-derived complete zero RP fixture')
    program=[]
    for line in commands.decode('ascii').splitlines():
        need(re.fullmatch(r'(0|1|2|16|32|64|128) [0-9]{1,4} [a-z_]+',line) is not None,'safe input')
        k,n,label=line.split();program.append((int(k),int(n),label))
    need(program[-1][2]=='end' and len(program)<=400,'explicit bounded ending')
    labels=[v[2] for v in program if v[2]!='step']
    need(len(labels)==len(set(labels)) and len(labels)<=40,'unique screenshots')
    need(type(screen_bindings) is dict and set(screen_bindings)=={k+'.ppm' for k in labels},'complete screen set')
    for binding in screen_bindings.values():
        need(type(binding) is dict and set(binding)=={'size','sha256'} and type(binding['size']) is int and binding['size']==115215 and type(binding['sha256']) is str and re.fullmatch('[0-9a-f]{64}',binding['sha256']) is not None,'canonical native PPM identity')
    model=load((ROOT/'content/research_economy_v1/canonical_model.json').read_bytes())
    text={r['dialogue_key']:r['encoded_hex'] for r in model['dialogue']}
    rows=[load(line) for line in raw.splitlines()];cursor=0;states={};objects={};last_text='00'*128
    def row():
        nonlocal cursor
        need(cursor<len(rows),'missing ordered row');r=rows[cursor];cursor+=1;need(type(r) is dict,'object row');return r
    ledger=bytearray(fixture[0x1f064:0x1f064+2048]);need(ledger[:8]==b'VGS1\x02\0\0\x08','source ledger v2')
    owner=bytearray(64);owner[0],owner[1],owner[6],owner[36]=1,64,1,1
    need(ledger[0x73f:0x77f]==owner,'no initial credit/rank injection')
    owner[7]=1;ledger[0x73f:0x77f]=owner;ledger=photo.purchase.prior.prior.old.seal(ledger)
    rest=bytearray(ledger);rest[4:6]=bytes(2);rest[8:12]=bytes(4);rest[0x73f:0x77f]=bytes(64)
    def stage(label,index,frame,screen=False):
        nonlocal last_text
        s=row();need(set(s)==STATE_FIELDS,'closed state schema')
        need(exact(s['state'],label) and exact(s['command'],index) and exact(s['frame'],frame),'stage order/frame/input binding')
        need(type(s['map']) is list and len(s['map'])==4 and all(type(x) is int and 0<=x<=4095 for x in s['map']) and s['map'][0]<=255 and s['map'][1]<=255,'physical map')
        need(type(s['facing']) is int and 1<=s['facing']<=4 and type(s['field']) is bool and type(s['shop_active']) is bool,'typed engine state')
        need(type(s['callback']) is int and s['callback']==0x08055e75,'ordinary field callback')
        for key,maximum in (('result',65535),('eligible',23),('window',255)):
            need(type(s[key]) is int and 0<=s[key]<=maximum,'bounded native '+key)
        need(s['flash_sha256']==FIXTURE['sha256'],'Flash remains exact fixture')
        need(type(s['text']) is str and re.fullmatch(r'(?:[0-9a-f]{2}){1,128}',s['text']) is not None,'native text canonical bytes')
        if label=='fixture':need(exact(s['map'],OUTSIDE[case]) and s['field'] and s['text']=='00'*128,'outdoor setup scope')
        elif label=='door_entered':need(exact(s['map'],INSIDE[case]) and s['field'],'actual physical door arrival')
        else:need(s['map'][:2]==INSIDE[case][:2] or (case=='lab' and label in ('end','final') and exact(s['map'],OUTSIDE[case])),'no unrelated warp in observation')
        need(s['field']==(label not in DIALOGUES[case] and label!='shop_open'),'exact dialogue lock/release state')
        expected_result=9 if label=='shop_open' else 2 if case=='lab' and index>=30 else 0
        need(s['result']==expected_result and s['eligible']==(19 if case=='lab' and index>=28 else 0),'complete result/menu eligibility sequence')
        if label in DIALOGUES[case]:
            last_text=text['DIALOGUE_KEY_'+DIALOGUES[case][label]]
            need(not s['field'] and s['text']==text['DIALOGUE_KEY_'+DIALOGUES[case][label]],'exact complete displayed native dialogue')
            expected=[98,3,2,2] if label=='shop_intro' else STANCE[case]
            need(exact(s['map'],expected),'actual talk stance')
        need(s['text']==last_text,'text buffer complete sequence, including closed stages')
        if case=='lab' and label=='shop_open':
            need(exact(s['map'],[98,3,2,2]) and not s['field'] and s['shop_active'] and s['eligible']==19 and s['window']==1 and s['result']==9,'physical first menu and native busy result')
        else:need(s['shop_active'] is False and s['window']==255,'no hidden menu/window')
        if label in ('end','final'):
            expected=OUTSIDE[case] if case=='lab' else {'fishing':[98,110,4,7],'game':[98,56,11,2],'ecology':[97,67,3,5]}[case]
            need(exact(s['map'],expected) and s['field'],'ordinary close/return within claimed scope')
        ev=row();need(exact(ev,dict(event=label,counter=2,item_quantity=0,inventory_sha256=BAG,other_inventory_sha256=BAG,party_sha256=PARTY,party_count=6,owner=bytes(owner).hex())),'entire owner/Bag/party/counter invariant')
        le=row();need(exact(le,dict(ledger_event=label,version=2,size=2048,checksum_valid=True,ledger_sha256=identity(ledger)['sha256'],unrelated_ledger_sha256=identity(rest)['sha256'],migration_dirty=0,recovery_blocked=0)),'independent complete 2048byte ledger reconstruction')
        ob=row();need(set(ob)=={'objects'} and type(ob['objects']) is list and 1<=len(ob['objects'])<=16,'live object observation')
        ids=[];player=[]
        for v in ob['objects']:
            need(type(v) is list and len(v)==6 and all(type(x) is int and 0<=x<=65535 for x in v),'typed object row')
            need(v[0]<16 and v[1]<=255 and v[2:4]==s['map'][:2],'actual object map');ids.append(v[0])
            if v[1]==255:player.append(v)
        need(len(ids)==len(set(ids)) and len(player)==1 and player[0][4:]==[s['map'][2]+7,s['map'][3]+7],'player live coordinate agreement')
        if label in DIALOGUES[case] and label!='shop_intro' and case!='game':
            local=4 if case=='lab' else 1
            hosts=[v for v in ob['objects'] if v[1]==local]
            need(len(hosts)==1,'actual local NPC active')
            delta={1:(0,1),2:(0,-1),3:(-1,0),4:(1,0)}[s['facing']]
            need(hosts[0][4:]==[player[0][4]+delta[0],player[0][5]+delta[1]],'talk to physical host, not script injection')
        if screen:
            sc=row();need(exact(sc,dict(screen=label,command=index,frame=frame,sha256=screen_bindings[label+'.ppm']['sha256'])),'same-frame native screen proof')
        states[label]=s;objects[label]=ob
    frame=900;stage('fixture',0,frame)
    for i,(keys,n,label) in enumerate(program,1):
        need(exact(row(),dict(input=i,keys=keys,frames=n,label=label)),'complete exact key sequence')
        frame+=n;need(frame<=50000,'bounded frame budget')
        if label!='step':stage(label,i,frame,True)
    stage('final',len(program),frame)
    terminal=dict(status='MEASURED',scope='PHYSICAL_DOOR_AND_NATIVE_WORDING',case=list(COMMANDS).index(case),fresh_cores=1,commands=len(program),screens=len(labels),guarded_host_writes=0,manual_saves=0,transaction_saves=0,accepted_case_reruns=0,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,warnings_errors=0)
    need(exact(row(),terminal) and cursor==len(rows),'complete closed terminal, no promoted claims')
    need(set(DIALOGUES[case])<=states.keys(),'all required dialogues observed')
    return dict(status='PASS_PHYSICAL_DOOR_AND_STATIC_GUIDE_SCOPED',case=case,stdout=identity(raw),commands=identity(commands),ledger_sha256=identity(ledger)['sha256'],native_screens=screen_bindings,dialogues=list(DIALOGUES[case]),physical_outdoor_entry_accepted=True,lab_counter_shop_exit_accepted=case=='lab',counter_numeric_display_accepted=False,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,accepted_case_reruns=0)
