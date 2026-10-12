"""Circus実戦traceのowner CRC・勝敗来歴・保存復帰を独立再検証する。"""
import struct
import zlib
from scripts.pr16_circus_identity import need, strict, identity
CASE='circus-streak-batch-save'
SHA='3f377dbc745aa3ac6c07f8177bba2dd20b8d9cbb34203364826a87771fd02da6'
LAUNCH=(0x09FF4CEB,0x09FF4D4C,0x09FF4DAD)

def owner(raw,empty=False):
    need(type(raw) is bytes and len(raw)==64,'owner size')
    if empty and raw==bytes(64):return dict(current=0,best=0,phase=0,prepared=0,settled=0,session=0,identity=0,generation=0)
    magic,inverse,version,size,crc,generation,session,prepared,settled,current,best,phase,fmt,outcome,reserved,save_id=struct.unpack('<IIHHIIIIIHHBBBBI',raw[:44])
    check=bytearray(raw);check[12:16]=bytes(4)
    need(magic==0x31534356 and inverse==magic^0xffffffff and version==1 and size==64,'owner schema')
    need(zlib.crc32(check)&0xffffffff==crc,'owner CRC')
    need(raw[44:]==bytes(20) and fmt==reserved==0 and phase in (0,1,2) and outcome<=3 and current<=best,'owner invariant')
    need(prepared==settled+(phase==2),'owner prepared/settled invariant')
    return dict(current=current,best=best,phase=phase,prepared=prepared,settled=settled,session=session,identity=save_id,generation=generation)

def parse(stderr):
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA diagnostics')
    events=[strict(line[len(b'CIRCUS_STREAK '):]) for line in stderr.splitlines() if line.startswith(b'CIRCUS_STREAK ')]
    need(9<=len(events)<=64,'native event bound')
    keys={'label','frame','battle','callback2','script','newbs','outcome','flags','types','count','bp','save_counter','pending','snapshot','marker','order','owner','party','factory'}
    for i,row in enumerate(events):
        need(type(row) is dict and set(row)==keys,'event schema')
        for k in keys-{'label','order','owner','party','factory'}:need(type(row[k]) is int and 0<=row[k]<=0xffffffff,'event integer')
        need(type(row['label']) is str and row['frame']>0 and (i==0 or row['frame']>events[i-1]['frame']),'event order')
        need(type(row['order']) is list and len(row['order'])==3 and all(type(v) is int and 0<=v<=6 for v in row['order']),'party selection')
        for k,size in (('owner',64),('party',600),('factory',104)):
            text=row[k];need(type(text) is str and len(text)==size*2 and all(c in '0123456789abcdef' for c in text),'event raw bytes')
        owner(bytes.fromhex(row['owner']),empty=row['label']=='fixture')
    return events

def analyze(events,r):
    wins,losses,battles=r['wins'],r['losses'],r['battles']
    need(0<=wins<=3 and losses in (0,1) and 1<=battles<=3 and battles==wins+losses,'native battle accounting')
    need(wins==3 if not losses else wins<3,'native terminal outcome')
    want=['fixture','selected']+['confirmation','action','outcome','settled']*battles+['returned','saved','reloaded']
    need([e['label'] for e in events]==want and len(events)==r['events'],'native event lifecycle')
    base,selected=events[:2];need(base['count']==1 and selected['count']==6,'native fixture/rental counts')
    need(base['bp']==0 and base['save_counter']==r['save_counter_before'],'initial BP/save')
    initial=owner(bytes.fromhex(base['owner']),True);need(initial['current']==initial['best']==initial['phase']==0,'initial dedicated streak')
    order=selected['order'];need(len(set(order))==3 and min(order)>=1,'three distinct chosen rentals')
    pool=bytes.fromhex(selected['party']);chosen=b''.join(pool[100*(n-1):100*n] for n in order)
    def ids(raw):return sorted(raw[n:n+8]+raw[n+0x20:n+0x22] for n in range(0,300,100))
    prepared=owner(bytes.fromhex(selected['owner']))['prepared'];session=owner(bytes.fromhex(selected['owner']))['session']
    for e in events:need(e['factory']==base['factory'],'Factory streak/claim/unlock alias')
    for battle in range(battles):
        confirm,action,outcome,settled=events[2+battle*4:6+battle*4]
        need(all(e['battle']==battle for e in (confirm,action,outcome,settled)),'battle ordinal')
        a=bytes.fromhex(confirm['party'])[:300];b=bytes.fromhex(action['party'])[:300]
        need(a==b and (a==chosen if battle==0 else ids(a)==ids(chosen)),'rental individual retention')
        need(confirm['script']==LAUNCH[battle] and not confirm['newbs'] and action['script']==LAUNCH[battle]+43
             and action['newbs']!=0 and action['types']&0x04000000,'native launch continuation')
        for e in (confirm,action):
            v=owner(bytes.fromhex(e['owner']))
            need(v['phase']==2 and v['current']==v['best']==battle and v['prepared']==prepared+battle+1
                 and v['settled']==prepared+battle and v['session']==session,'native arm/draw owner')
            need(e['count']==3 and e['snapshot']==1,'rental battle snapshot')
        expected=2 if losses and battle==battles-1 else 1
        need(outcome['outcome']==expected,'unobserved real outcome')
        v=owner(bytes.fromhex(settled['owner']))
        need(v['current']==(battle+1 if expected==1 else 0) and v['best']==(battle+1 if expected==1 else battle)
             and v['settled']==v['prepared']==prepared+battle+1 and v['phase']!=2 and v['session']==session,'native settle owner')
        need(not settled['newbs'],'native battle still allocated')
    returned,saved,reloaded=events[-3:];final=owner(bytes.fromhex(returned['owner']))
    need(returned['owner']==saved['owner']==reloaded['owner'],'Save/fresh Continue dedicated64')
    need(final['phase']==0 and final['current']==(0 if losses else 3) and final['best']==wins,'final streak')
    for e in (returned,saved,reloaded):
        need(e['party']==base['party'] and e['count']==1 and not e['snapshot'] and not e['pending'] and not e['marker']
             and not e['newbs'] and e['bp']==(0 if losses else 9),'return/save original party/BP')
    for e in events[:-2]:need(e['save_counter']==r['save_counter_before'],'unexpected automatic standard Save')
    need(saved['save_counter']==reloaded['save_counter']==r['save_counter_after'] and reloaded['frame']==r['total_frames'],'Save counter/end frame')
    return dict(classification='CIRCUS_THREE_WIN_SAVE_CONTINUE' if not losses else 'CIRCUS_NATIVE_LOSS_SAVE_CONTINUE',
        wins=wins,losses=losses,later_battle_launches_verified=battles-1,owner_bytes_verified=64,original_party_bytes_verified=600,
        factory_streak_and_claim_unchanged=True,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)

def validate(raw,stderr,code,case):
    need(type(code) is int and code==0 and case==CASE,'native process failed')
    r=strict(raw)
    fixed=dict(schema_version=1,status='PASS_CIRCUS_STREAK_NATIVE',case=CASE,candidate_sha256=SHA,
        save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=2,owner_bytes_verified=64,party_bytes_verified=600,
        host_write_barriers=7,input_only_after_guard=True,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0)
    dynamic={'wins','losses','battles','turns','switches','forced_identity_checks','total_frames','events'}
    need(type(r) is dict and set(r)==set(fixed)|dynamic,'native result schema')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'native result '+k)
    for k in dynamic:need(type(r[k]) is int and r[k]>=0,'native result counter')
    need(0<r['total_frames']<320000 and 0<r['turns']<=192 and r['switches']==r['forced_identity_checks']<=6,'native execution bound')
    analyze(parse(stderr),r);return r
