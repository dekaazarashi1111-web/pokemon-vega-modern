"""連続入場の実outcome→固有owner→報酬→保存を検査。3勝を30勝には昇格しない。"""
import json
import struct
import zlib
CASE='circus-continuous-30-save'
SHA='3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399'
LAUNCH=(0x09FF4CEB,0x09FF4D4C,0x09FF4DAD)

def need(ok,message):
    if not ok:raise ValueError(message)

def strict(raw):
    def pairs(items):
        result={}
        for k,v in items:
            need(k not in result,'duplicate JSON key');result[k]=v
        return result
    def bad(_):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def owner(raw,empty=False):
    need(type(raw) is bytes and len(raw)==64,'owner size')
    if empty and raw==bytes(64):return dict(current=0,best=0,phase=0,prepared=0,settled=0,session=0,identity=0,generation=0,outcome=0)
    magic,inverse,version,size,crc,generation,session,prepared,settled,current,best,phase,fmt,outcome,reserved,save_id=struct.unpack('<IIHHIIIIIHHBBBBI',raw[:44])
    check=bytearray(raw);check[12:16]=bytes(4)
    need(magic==0x31534356 and inverse==magic^0xffffffff and version==1 and size==64,'owner schema')
    need(zlib.crc32(check)&0xffffffff==crc,'owner CRC')
    need(raw[44:]==bytes(20) and fmt==reserved==0 and phase in (0,1,2) and outcome<=3 and current<=best,'owner invariant')
    need(prepared==settled+(phase==2),'owner prepared/settled invariant')
    return dict(current=current,best=best,phase=phase,prepared=prepared,settled=settled,session=session,identity=save_id,generation=generation,outcome=outcome)

def parse(stderr):
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA diagnostics')
    prefix=b'CIRCUS_CONTINUOUS '
    events=[strict(line[len(prefix):]) for line in stderr.splitlines() if line.startswith(prefix)]
    need(9<=len(events)<=160,'continuous event bound')
    keys={'label','frame','battle','callback2','script','newbs','outcome','flags','types','count','bp','save_counter','pending','snapshot','marker','order','owner','party','factory'}
    for i,row in enumerate(events):
        need(type(row) is dict and set(row)==keys,'event schema')
        for k in keys-{'label','order','owner','party','factory'}:need(type(row[k]) is int and 0<=row[k]<=0xffffffff,'event integer')
        need(type(row['label']) is str and (row['frame']==0 and row['label']=='fixture' if i==0 else row['frame']>events[i-1]['frame']),'event order')
        need(type(row['order']) is list and len(row['order'])==3 and all(type(v) is int and 0<=v<=6 for v in row['order']),'party selection')
        for k,size in (('owner',64),('party',600),('factory',104)):
            text=row[k];need(type(text) is str and len(text)==size*2 and all(c in '0123456789abcdef' for c in text),'event raw bytes')
        owner(bytes.fromhex(row['owner']),empty=i==0)
    return events

def analyze(events,r):
    wins,losses,battles=r['wins'],r['losses'],r['battles']
    need(0<=wins<=30 and losses in (0,1) and 1<=battles<=30 and battles==wins+losses,'real battle accounting')
    need(wins==30 if not losses else wins<30,'terminal outcome is neither target nor first loss')
    need(r['admissions']==(battles+2)//3 and r['completed_batches']==wins//3 and r['bp_earned']==9*(wins//3),'batch/BP accounting')
    need(len(events)==r['events'] and events[0]['label']=='fixture','continuous start/count')
    base=events[0];initial=owner(bytes.fromhex(base['owner']),True)
    need(base['count']==1 and base['bp']==0 and base['save_counter']==r['save_counter_before'],'initial fixture')
    need(initial['current']==initial['best']==initial['phase']==initial['prepared']==initial['settled']==initial['session']==0,'not a genuine zero streak')
    for e in events:need(e['factory']==base['factory'],'Factory claim/streak alias')
    def restored(e,current,best,bp):
        v=owner(bytes.fromhex(e['owner']))
        need(v['phase']==0 and v['current']==current and v['best']==best,'returned current/best')
        need(e['party']==base['party'] and e['count']==1 and not e['snapshot'] and not e['pending'] and not e['marker']
             and not e['newbs'] and e['bp']==bp,'returned original600/BP')
    def ids(raw):return sorted(raw[n:n+8]+raw[n+0x20:n+0x22] for n in range(0,300,100))
    offset=1;observed=0;previous_session=0;last_return=None
    for admission in range(r['admissions']):
        selected=events[offset];offset+=1
        need(selected['label']=='selected' and selected['battle']==observed and selected['count']==6,'actual rental admission')
        s=owner(bytes.fromhex(selected['owner']))
        need(s['current']==s['best']==s['prepared']==s['settled']==observed and s['phase']==1
             and s['session']==previous_session+1 and s['identity']==initial['identity'],'new session did not preserve earned streak')
        previous_session=s['session'];need(selected['bp']==9*admission and selected['snapshot']==1 and selected['marker']==1,'admission snapshot/BP')
        order=selected['order'];need(len(set(order))==3 and min(order)>=1,'distinct selected three')
        pool=bytes.fromhex(selected['party']);chosen=b''.join(pool[100*(n-1):100*n] for n in order)
        batch_battles=min(3,battles-observed)
        for local in range(batch_battles):
            rows=events[offset:offset+4];offset+=4
            need(len(rows)==4 and [e['label'] for e in rows]==['confirmation','action','outcome','settled'],'battle lifecycle')
            confirm,action,outcome,settled=rows
            need(all(e['battle']==observed for e in rows),'global battle ordinal')
            a=bytes.fromhex(confirm['party'])[:300];b=bytes.fromhex(action['party'])[:300]
            need(a==b and (a==chosen if not local else ids(a)==ids(chosen)),'selected individual retained')
            need(confirm['script']==LAUNCH[local] and not confirm['newbs'] and action['script']==LAUNCH[local]+43
                and action['newbs'] and action['types']&0x04000000,'actual script launch')
            for e in (confirm,action,outcome):
                v=owner(bytes.fromhex(e['owner']))
                need(v['current']==v['best']==observed and v['phase']==2 and v['prepared']==observed+1
                    and v['settled']==observed and v['session']==s['session'] and v['identity']==initial['identity'],'owner arm/real outcome')
                need(e['count']==3 and e['snapshot']==1 and e['bp']==9*admission,'armed rental/BP')
            expected=2 if losses and observed==battles-1 else 1
            need(outcome['outcome']==expected,'real win/loss absent')
            v=owner(bytes.fromhex(settled['owner']))
            best=observed+(expected==1)
            need(v['current']==(best if expected==1 else 0) and v['best']==best and v['outcome']==expected
                and v['prepared']==v['settled']==observed+1 and v['phase']!=2 and v['session']==s['session']
                and v['identity']==initial['identity'] and not settled['newbs'],'unique settle/streak')
            observed+=1
        returned=events[offset];offset+=1
        need(returned['label']=='returned' and returned['battle']==observed,'batch return')
        last_loss=losses and observed==battles
        restored(returned,0 if last_loss else observed,wins if last_loss else observed,9*((wins if last_loss else observed)//3))
        last_return=returned
    need(observed==battles and offset+2==len(events),'missing/extra continuation events')
    saved,reloaded=events[offset:];need([saved['label'],reloaded['label']]==['saved','reloaded'],'final standard Save/fresh Continue')
    need(last_return['owner']==saved['owner']==reloaded['owner'],'persistent dedicated64')
    for e in (saved,reloaded):restored(e,0 if losses else wins,wins,r['bp_earned'])
    for e in events[:-2]:need(e['save_counter']==r['save_counter_before'],'unexpected automatic standard Save')
    need(saved['save_counter']==reloaded['save_counter']==r['save_counter_after'] and reloaded['frame']==r['total_frames'],'Save counter/frame')
    return dict(classification='CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE' if wins==30 else 'CIRCUS_CONTINUOUS_FIRST_LOSS_DIAGNOSTIC',
        wins=wins,losses=losses,admissions=r['admissions'],completed_batches=r['completed_batches'],bp_earned=r['bp_earned'],
        genuine_30_wins_verified=wins==30,later_battle_launches_verified=battles-r['admissions'],
        owner_bytes_verified=64,original_party_bytes_verified=600,factory_streak_and_claim_unchanged=True,
        accepted_prefix_battles_reexecuted_for_continuation=min(3,battles),physical_admission_accepted=False,suppression_accepted=False,release_ready=False)

def require_target(result):
    need(result['wins']==30 and result['losses']==0 and result['battles']==30 and result['admissions']==10
        and result['bp_earned']==90,'genuine 30-win target remains open')
    return result

def validate(raw,stderr,code,case):
    need(type(code) is int and code==0 and case==CASE,'continuous process failed')
    r=strict(raw)
    fixed=dict(schema_version=1,status='PASS_CIRCUS_CONTINUOUS_LIFECYCLE',case=CASE,candidate_sha256=SHA,target_wins=30,
        save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=2,owner_bytes_verified=64,party_bytes_verified=600,
        host_write_barriers=7,input_only_after_guard=True,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0)
    dynamic={'wins','losses','battles','turns','switches','forced_identity_checks','total_frames','events','admissions','completed_batches','bp_earned'}
    need(type(r) is dict and set(r)==set(fixed)|dynamic,'continuous result schema')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'continuous result '+k)
    for k in dynamic:need(type(r[k]) is int and r[k]>=0,'continuous counter type')
    need(0<r['total_frames']<3200000 and 0<r['turns']<=64*r['battles'] and r['switches']==r['forced_identity_checks']<=2*r['battles'],'continuous execution bound')
    analyze(parse(stderr),r);return r
