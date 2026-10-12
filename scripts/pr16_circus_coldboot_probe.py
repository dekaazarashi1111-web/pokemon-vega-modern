"""Cold boot修復: 自動復旧Save2回/通常Save1回/CRC64/未完戦非加算を検証。"""
import json
import struct
import zlib
CASE='circus-interrupt-second-battle'
SHA='3b5f919958bf72bad9aa5b466215f33311f9c8c19e1f7f409303416eab952d5d'
LAUNCH=(0x09FF4CEB,0x09FF4D4C)
KEYS={'label','frame','battle','callback2','script','newbs','outcome','flags','types','count','bp','save_counter','pending','snapshot','marker','order','owner','party','factory'}


def need(value,message):
    if not value:raise ValueError(message)


def strict(raw):
    def unique(pairs):
        result={}
        for k,v in pairs:
            need(k not in result,'duplicate JSON key');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:need(False,'nonfinite JSON'))


def owner(raw):
    need(type(raw) is bytes and len(raw)==64,'owner size')
    fields=struct.unpack('<IIHHIIIIIHHBBBBI',raw[:44])
    magic,inverse,version,size,crc,generation,session,prepared,settled,current,best,phase,fmt,outcome,reserved,save_id=fields
    check=bytearray(raw);check[12:16]=bytes(4)
    need(magic==0x31534356 and inverse==magic^0xffffffff and version==1 and size==64,'owner schema')
    need(zlib.crc32(check)&0xffffffff==crc,'owner CRC')
    need(generation>0 and raw[44:]==bytes(20) and fmt==reserved==0 and phase in (0,1,2)
         and outcome<=3 and current<=best and prepared==settled+(phase==2),'owner invariants')
    need(phase==0 or session>0,'active owner session')
    need(session!=0 or prepared==current==best==outcome==0,'uninitialized owner progress')
    return dict(generation=generation,session=session,prepared=prepared,settled=settled,
        current=current,best=best,phase=phase,outcome=outcome,identity=save_id)


def parse(stderr):
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA diagnostics')
    events=[strict(line[14:]) for line in stderr.splitlines() if line.startswith(b'CIRCUS_STREAK ')]
    need(len(events)==11,'interruption event count')
    for i,row in enumerate(events):
        need(type(row) is dict and set(row)==KEYS,'event schema')
        for k in KEYS-{'label','order','owner','party','factory'}:
            need(type(row[k]) is int and 0<=row[k]<=0xffffffff,'event integer')
        need(type(row['label']) is str and (row['frame']>0 or i==0 and row['label']=='fixture')
             and (i==0 or row['frame']>events[i-1]['frame']),'event frame chain')
        need(type(row['order']) is list and len(row['order'])==3
             and all(type(v) is int and 0<=v<=6 for v in row['order']),'selection order')
        for key,size in (('owner',64),('party',600),('factory',104)):
            text=row[key]
            need(type(text) is str and len(text)==size*2 and all(c in '0123456789abcdef' for c in text),'event bytes')
        owner(bytes.fromhex(row['owner']))
    return events


def analyze(events,r):
    want=['fixture','selected','confirmation','action','outcome','settled','confirmation','action','recovered','saved','reloaded']
    need([e['label'] for e in events]==want,'interruption lifecycle')
    need([e['battle'] for e in events]==[0,0,0,0,0,0,1,1,2,2,2],'battle ordinal')
    base,selected=events[:2];start=owner(bytes.fromhex(base['owner']));choice=owner(bytes.fromhex(selected['owner']))
    need(base['count']==1 and selected['count']==6 and base['bp']==0 and base['save_counter']==2,'initial state')
    need(start['current']==start['best']==start['phase']==start['session']==start['prepared']==start['settled']==0,'initial owner')
    need(choice['session']==start['session']+1 and choice['prepared']==choice['settled']==0
         and choice['current']==choice['best']==0 and choice['phase']==1
         and choice['generation']==start['generation']+1,'native begin')
    order=selected['order'];need(len(set(order))==3 and min(order)>=1,'distinct rentals')
    pool=bytes.fromhex(selected['party']);chosen=b''.join(pool[100*(i-1):100*i] for i in order)
    def ids(raw):return sorted(raw[i:i+8]+raw[i+0x20:i+0x22] for i in range(0,300,100))
    for e in events:
        v=owner(bytes.fromhex(e['owner']))
        need(v['identity']==start['identity'] and e['factory']==base['factory'] and e['bp']==0,'identity/Factory/BP changed')
        need(e['save_counter']==(5 if e['label'] in ('saved','reloaded') else 4 if e['label']=='recovered' else 2),'unexpected standard Save')
    for battle,index in ((0,2),(1,6)):
        confirm,action=events[index:index+2]
        a=bytes.fromhex(confirm['party'])[:300];b=bytes.fromhex(action['party'])[:300]
        need(a==b and (a==chosen if battle==0 else ids(a)==ids(chosen)),'selected individual retention')
        need(confirm['script']==LAUNCH[battle] and not confirm['newbs'] and action['script']==LAUNCH[battle]+43
             and action['newbs']!=0 and action['types']&0x04000000,'native launch')
        for e in (confirm,action):
            v=owner(bytes.fromhex(e['owner']))
            need(v['phase']==2 and v['prepared']==battle+1 and v['settled']==battle
                 and v['current']==v['best']==battle and v['session']==choice['session']
                 and v['generation']==choice['generation']+1+2*battle,'native armed owner')
            need(e['count']==3 and e['snapshot']==1 and e['marker']==2,'rental snapshot/marker')
    outcome,settled=events[4:6]
    need(outcome['outcome']==1 and outcome['newbs']!=0 and outcome['owner']==events[3]['owner'],'real first win absent')
    done=owner(bytes.fromhex(settled['owner']))
    need(done['phase']==1 and done['prepared']==done['settled']==done['current']==done['best']==done['outcome']==1
         and done['session']==choice['session'] and done['generation']==choice['generation']+2 and not settled['newbs'],'win not settled')
    armed=owner(bytes.fromhex(events[7]['owner']));recovered,saved,reloaded=events[8:]
    restored=owner(bytes.fromhex(recovered['owner']))
    need(restored==dict(armed,phase=0,current=0,settled=2,outcome=3,generation=armed['generation']+1),'interruption abort missing, repeated, or inflated')
    need(recovered['owner']==saved['owner']==reloaded['owner'],'persisted64 not stable')
    for e in (recovered,saved,reloaded):
        need(e['party']==base['party'] and e['count']==1 and not e['snapshot'] and not e['pending']
             and not e['marker'] and not e['newbs'],'original party/session recovery')
    need(reloaded['frame']==r['total_frames'],'terminal frame differs')
    return dict(classification='CIRCUS_SECOND_BATTLE_INTERRUPTION_RECOVERY_SAVE_CONTINUE',
        real_wins_before_interruption=1,unfinished_battles_not_counted=1,current_after=0,best_after=1,
        normal_saves=1,automatic_recovery_saves=2,fresh_cores=3,owner_bytes_verified=64,party_bytes_verified=600,
        factory_streak_and_claim_unchanged=True,bp_earned=0,physical_admission_accepted=False,
        suppression_accepted=False,release_ready=False)


def validate(raw,stderr,code,case):
    need(type(code) is int and code==0 and case==CASE,'native process failed')
    r=strict(raw)
    fixed=dict(schema_version=1,status='PASS_CIRCUS_INTERRUPTION_NATIVE',case=CASE,candidate_sha256=SHA,
        wins=1,losses=0,battles_started=2,battles_finished=1,interruptions=1,
        save_counter_before=2,save_counter_after=5,manual_saves=1,automatic_recovery_saves=2,fresh_cores=3,
        owner_bytes_verified=64,party_bytes_verified=600,host_write_barriers=7,events=11,
        input_only_after_guard=True,physical_admission_accepted=False,suppression_accepted=False,
        release_ready=False,warnings_errors=0)
    dynamic={'turns','switches','forced_identity_checks','total_frames'}
    need(type(r) is dict and set(r)==set(fixed)|dynamic,'native result schema')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'native result '+k)
    for k in dynamic:need(type(r[k]) is int and r[k]>=0,'native result counters')
    need(0<r['turns']<=64 and r['switches']==r['forced_identity_checks']<=2
         and 0<r['total_frames']<160000,'native result bounds')
    analyze(parse(stderr),r);return r
