#!/usr/bin/env python3
"""数値受付の独立bytecode/実測oracle。実装のexpected-output関数は呼ばない。"""
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ('434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38',
            '95646d927206354df5f2ad4b0bfca85bc26bd3d1a90811df9988e3ccb0357046')
VALUES = ((0,0,1),(9999,2200,7))
TEXT_KEYS = {'counter_intro':'COUNTER_INTRO','counter_activity_one':'COUNTER_ACTIVITY_1',
             'counter_activity_two':'COUNTER_ACTIVITY_2','counter_revisit':'COUNTER_REVISIT'}
STATE_FIELDS = {'state','command','frame','map','facing','field','callback','result',
                'shop_active','eligible','window','flash_sha256','text'}
BAG = '688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
PARTY = '55514c6b16a517c723e3cdfe4826075020b214905950ada9cd65b41a97419430'


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(raw):
    return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def exact(a,b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a) is list: return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b


def load(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            need(k not in out,'duplicate key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,
                      parse_constant=lambda _: need(False,'nonfinite JSON'))


def digits(n):
    need(type(n) is int and 0<=n<=9999,'display value range')
    return bytes(0xa1+int(c) for c in str(n))


def walk(code, outcome, rp, rank):
    """実ROMのevent命令を解釈。VM限定試験を実ROM/native実行と呼ばない。"""
    need(type(code) is bytes and len(code)==132,'existing event window')
    pc=0;result=0;compare=False;messages=[];calls=[];buffers={};released=False
    def take(n):
        nonlocal pc
        need(0<=pc and pc+n<=len(code),'bounded complete opcode')
        b=code[pc:pc+n];pc+=n;return b
    def jump(address):
        nonlocal pc
        need(0x093c02a4<=address<0x093c0328,'local branch target')
        pc=address-0x093c02a4
    for _ in range(64):
        op=take(1)[0]
        if op in (0x6a,0x5a): continue
        if op==0x23:
            address=struct.unpack('<I',take(4))[0];calls.append(address)
            need(address in (0x093be8a1,0x093be033,0x093be057),'bound native getter/entry')
            result={0x093be8a1:outcome,0x093be033:rp,0x093be057:rank}[address]
        elif op==0x21:
            variable,value=struct.unpack('<HH',take(4));need(variable==0x800d,'result compare')
            compare=result==value
        elif op==0x06:
            condition=take(1)[0];address=struct.unpack('<I',take(4))[0]
            need(condition==1,'equality branch')
            if compare: jump(address)
        elif op==0x05: jump(struct.unpack('<I',take(4))[0])
        elif op==0x83:
            slot=take(1)[0];variable=struct.unpack('<H',take(2))[0]
            need(slot in (0,1) and variable==0x800d and slot not in buffers,'native number slots')
            buffers[slot]=(digits(result)+b'\xff').hex()
        elif op==0x16:
            variable,result=struct.unpack('<HH',take(4));need(variable==0x800d,'result restoration only')
        elif op==0x0f:
            need(take(1)==b'\0','message bank');address=struct.unpack('<I',take(4))[0]
            need(take(2)==b'\x09\x04','native msgbox wait');messages.append(address)
        elif op==0x6c: released=True
        elif op==0x02:
            need(released,'release before end')
            return dict(result=result,messages=messages,calls=calls,buffers=buffers)
        else: need(False,'unsupported opcode')
    raise ValueError('bounded event termination')


def validate(raw,index,commands,fixture,screens):
    need(type(index) is int and index in (0,1),'closed numeric case')
    need(type(raw) is bytes and 0<len(raw)<100000 and raw.endswith(b'\n'),'complete bounded transcript')
    need(type(fixture) is bytes and exact(identity(fixture),dict(size=131072,sha256=FIXTURES[index])),'exact full fixture')
    # Independent immutable input, not generated from the probe PROGRAM.
    expected=b'64 40 step\n0 200 door_entered\n64 128 step\n0 60 counter_approach\n1 2 step\n0 120 counter_intro\n1 2 step\n0 120 counter_balance\n1 2 step\n0 120 counter_activity_one\n1 2 step\n0 120 counter_activity_two\n1 2 step\n0 120 counter_revisit\n1 2 step\n0 120 counter_closed\n0 0 end\n'
    need(type(commands) is bytes and commands==expected,'closed physical input sequence')
    program=[(int(k),int(n),l) for k,n,l in (line.split() for line in commands.decode().splitlines())]
    labels=[l for _,_,l in program if l!='step']
    need(type(screens) is dict and set(screens)=={l+'.ppm' for l in labels},'exact screenshot set')
    for v in screens.values():
        need(type(v) is dict and set(v)=={'size','sha256'} and type(v['size']) is int and v['size']==115215
             and type(v['sha256']) is str and re.fullmatch('[a-f0-9]{64}',v['sha256']) is not None,'native PPM identity')
    rp,lifetime,rank=VALUES[index];number_buffers=[(digits(rp)+b'\xff').hex(),(digits(rank)+b'\xff').hex()]
    numeric_text=(b'\xcc\xca\0'+digits(rp)+b'\xfe\x77\x7e\x58\0'+digits(rank)+b'\xff').hex()
    model=load((ROOT/'content/research_economy_v1/canonical_model.json').read_bytes())
    text={r['dialogue_key']:r['encoded_hex'] for r in model['dialogue']}
    ledger=bytearray(fixture[0x1f064:0x1f064+2048]);owner=bytearray(ledger[0x73f:0x77f]);owner[7]=1
    ledger[0x73f:0x77f]=owner
    # Reuse the checksum algorithm only, not the fixture construction or expected owner.
    import pr16_research_photo as photo
    ledger=photo.purchase.prior.prior.old.seal(ledger)
    rest=bytearray(ledger);rest[4:6]=bytes(2);rest[8:12]=bytes(4);rest[0x73f:0x77f]=bytes(64)
    rows=[load(line) for line in raw.splitlines()];cursor=0;last='00'*128
    def row():
        nonlocal cursor
        need(cursor<len(rows),'missing row');r=rows[cursor];cursor+=1;need(type(r) is dict,'object row');return r
    def stage(label,command,frame,screen=False):
        nonlocal last
        s=row();need(set(s)==STATE_FIELDS,'closed state schema')
        need(exact(s['state'],label) and exact(s['command'],command) and exact(s['frame'],frame),'exact stage/input/frame')
        position=[96,0,16,14] if label=='fixture' else [98,3,6,12] if label=='door_entered' else [98,3,6,4]
        need(exact(s['map'],position),'physical position')
        dialogue=label in TEXT_KEYS or label=='counter_balance'
        for k,v in dict(field=not dialogue,callback=0x08055e75,result=0,shop_active=False,eligible=0,window=255,flash_sha256=FIXTURES[index]).items():
            need(exact(s[k],v),'engine invariant '+k)
        need(type(s['facing']) is int and 1<=s['facing']<=4,'facing')
        if label in TEXT_KEYS: last=text['DIALOGUE_KEY_'+TEXT_KEYS[label]]
        if label=='counter_balance': last=numeric_text
        need(exact(s['text'],last),'complete native expanded text')
        need(exact(row(),dict(event=label,counter=2,item_quantity=0,inventory_sha256=BAG,other_inventory_sha256=BAG,
             party_sha256=PARTY,party_count=6,owner=bytes(owner).hex())),'all owner/Bag/party/save invariants')
        need(exact(row(),dict(ledger_event=label,version=2,size=2048,checksum_valid=True,
             ledger_sha256=identity(ledger)['sha256'],unrelated_ledger_sha256=identity(rest)['sha256'],migration_dirty=0,recovery_blocked=0)),
             'complete independently reconstructed ledger')
        ob=row();need(set(ob)=={'objects'} and type(ob['objects']) is list and 1<=len(ob['objects'])<=16,'object snapshot')
        ids=[];player=[];host=[]
        for v in ob['objects']:
            need(type(v) is list and len(v)==6 and all(type(x) is int and 0<=x<=65535 for x in v),'typed object')
            need(v[0]<16 and v[1]<=255 and v[2:4]==position[:2],'object map');ids.append(v[0])
            if v[1]==255: player.append(v)
            if v[1]==4: host.append(v)
        need(len(ids)==len(set(ids)) and len(player)==1 and player[0][4:]==[position[2]+7,position[3]+7],'live player')
        if dialogue:
            delta={1:(0,1),2:(0,-1),3:(-1,0),4:(1,0)}[s['facing']]
            need(len(host)==1 and host[0][4:]==[player[0][4]+delta[0],player[0][5]+delta[1]],'actual local4 facing')
        numbers=row();need(set(numbers)=={'numeric','rp','lifetime','rank','buffers'},'closed number observation')
        for k,v in dict(numeric=label,rp=rp,lifetime=lifetime,rank=rank).items(): need(exact(numbers[k],v),'owner number '+k)
        bs=numbers['buffers'];need(type(bs) is list and len(bs)==2,'two buffers')
        for b in bs:
            need(type(b) is str and re.fullmatch(r'(?:[0-9a-f]{2}){1,20}',b) is not None,'bounded buffer')
        if command>=8: need(exact(bs,number_buffers),'native decimal buffers')
        if screen: need(exact(row(),dict(screen=label,command=command,frame=frame,sha256=screens[label+'.ppm']['sha256'])),'same-frame screen')
    frame=900;stage('fixture',0,frame)
    for i,(key,n,label) in enumerate(program,1):
        need(exact(row(),dict(input=i,keys=key,frames=n,label=label)),'ordered physical input')
        frame+=n
        if label!='step': stage(label,i,frame,True)
    stage('final',len(program),frame)
    terminal=dict(status='MEASURED',scope='COUNTER_NUMERIC_TEXT_NOT_STANDARD_LIST',case=0,fresh_cores=1,
        commands=len(program),screens=len(labels),guarded_host_writes=0,manual_saves=0,transaction_saves=0,
        accepted_case_reruns=0,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,warnings_errors=0)
    need(exact(row(),terminal) and cursor==len(rows),'closed terminal/no unsupported promotion')
    return dict(status='PASS_COUNTER_NUMERIC_TEXT_SCOPED',fixture_index=index,rp=rp,rank=rank,lifetime=lifetime,
        stdout=identity(raw),commands=identity(commands),numeric_text=numeric_text,ledger=identity(ledger),screens=screens,
        counter_numeric_display_accepted=True,counter_rank_number_accepted=True,standard_list_accepted=False,
        natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,accepted_case_reruns=0)
