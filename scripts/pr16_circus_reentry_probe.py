"""実敗北→Settle(LOSS)→End(0)/ABORTを世代差まで照合する連続検証。"""
from pr16_circus_continuous_probe import CASE, SHA, LAUNCH, need, strict, owner, parse

def settlement(value,expected,armed,local):
    """snapshotがSettle直後かEnd直後かを区別し、勝敗は実outcomeから決める。"""
    phase,outcome,delta=value['phase'],value['outcome'],value['generation']-armed['generation']
    if expected==2:
        return (phase,outcome,delta) in ((1,2,1),(0,3,2))
    return (phase,outcome,delta)==(1,1,1) or (local==2 and (phase,outcome,delta)==(0,1,2))

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
    need(initial['generation']==1,'initial owner generation')
    offset=1;observed=0;previous_session=0;previous_generation=initial['generation'];last_return=None
    for admission in range(r['admissions']):
        selected=events[offset];offset+=1
        need(selected['label']=='selected' and selected['battle']==observed and selected['count']==6,'actual rental admission')
        s=owner(bytes.fromhex(selected['owner']))
        need(s['current']==s['best']==s['prepared']==s['settled']==observed and s['phase']==1
             and s['session']==previous_session+1 and s['identity']==initial['identity'],'new session did not preserve earned streak')
        need(s['generation']==previous_generation+1,'admission generation')
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
                need(v['generation']==s['generation']+2*local+1,'armed owner generation')
                need(e['count']==3 and e['snapshot']==1 and e['bp']==9*admission,'armed rental/BP')
            expected=2 if losses and observed==battles-1 else 1
            need(outcome['outcome']==expected,'real win/loss absent')
            v=owner(bytes.fromhex(settled['owner']))
            best=observed+(expected==1)
            need(v['current']==(best if expected==1 else 0) and v['best']==best and settlement(v,expected,owner(bytes.fromhex(confirm['owner'])),local)
                and v['prepared']==v['settled']==observed+1 and v['phase']!=2 and v['session']==s['session']
                and v['identity']==initial['identity'] and not settled['newbs'],'unique settle/streak')
            observed+=1
        returned=events[offset];offset+=1
        need(returned['label']=='returned' and returned['battle']==observed,'batch return')
        last_loss=losses and observed==battles
        restored(returned,0 if last_loss else observed,wins if last_loss else observed,9*((wins if last_loss else observed)//3))
        rv=owner(bytes.fromhex(returned['owner']))
        need(rv['prepared']==rv['settled']==observed and rv['session']==s['session']
             and rv['identity']==initial['identity'] and rv['generation']==s['generation']+2*batch_battles+1
             and rv['outcome']==(3 if last_loss else 1),'returned owner lifecycle')
        previous_generation=rv['generation'];last_return=returned
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
