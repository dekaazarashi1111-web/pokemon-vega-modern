#!/usr/bin/env python3
"""屋外からの物理入口と未確認会話だけ。既受入の旧native mainは呼ばない。"""
from pathlib import Path
import struct
import pr16_research_bug as prior
ROOT=Path(__file__).resolve().parents[1]
C='tools/mgba_pr16_research_connection.c'
CANDIDATE=prior.CANDIDATE
need,identity,load,exact=prior.need,prior.identity,prior.load,prior.exact
NAMES=('lab','fishing','game','ecology')
PROGRAMS={
'lab':[(64,40,'step'),(0,200,'door_entered'),(64,128,'step'),(0,60,'counter_approach'),(1,2,'step'),(0,120,'counter_intro'),(1,2,'step'),(0,120,'counter_balance'),(1,2,'step'),(0,120,'counter_activity_one'),(1,2,'step'),(0,120,'counter_activity_two'),(1,2,'step'),(0,120,'counter_revisit'),(1,2,'step'),(0,120,'counter_closed'),(128,16,'step'),(32,64,'step'),(64,48,'step'),(0,60,'shop_approach'),(32,16,'step'),(0,30,'step'),(64,2,'step'),(0,30,'shop_stance'),(1,2,'step'),(0,120,'shop_intro'),(1,2,'step'),(0,120,'shop_open'),(2,2,'step'),(0,120,'shop_closed'),(128,128,'step'),(16,80,'step'),(0,40,'exit_approach'),(32,24,'step'),(128,144,'step'),(0,40,'exit_corridor'),(16,40,'step'),(128,100,'step'),(0,180,'end')],
'fishing':[(64,40,'step'),(0,180,'door_entered'),(16,24,'step'),(64,40,'step'),(0,40,'guide_approach'),(1,2,'step'),(0,120,'guide_message'),(1,2,'step'),(0,120,'guide_cap'),(1,2,'step'),(0,60,'guide_closed'),(128,80,'step'),(0,180,'end')],
'game':[(64,40,'step'),(0,180,'door_entered'),(64,176,'step'),(16,40,'step'),(64,2,'step'),(0,40,'guide_approach'),(32,16,'step'),(0,32,'step'),(64,32,'step'),(0,32,'guide_stance'),(1,2,'step'),(0,120,'guide_message'),(1,2,'step'),(0,120,'guide_cap'),(1,2,'step'),(0,60,'end')],
'ecology':[(64,40,'step'),(0,180,'door_entered'),(32,16,'step'),(0,32,'step'),(64,64,'step'),(0,32,'guide_stance'),(1,2,'step'),(0,120,'guide_message'),(0,0,'end')]
}
# start outdoors, ordinary door target, actual host header/record/script.
ROOTS={
'lab':((96,0,16,14),(98,3,6,12),0x092C2ADC,0x09413B9C,0x093C02A4,0),
'fishing':((96,23,12,87),(98,110,3,7),0x092C4AF4,0x09413F44,0x093C0644,0),
'game':((96,6,34,22),(98,56,9,13),0x092C3A8C,0x09413D74,0x093C0660,3),
'ecology':((97,63,29,26),(97,67,4,9),0x092C209C,0x09400928,0x093C067C,0)}
DIALOGUES={
'lab':{'counter_intro':'DIALOGUE_KEY_COUNTER_INTRO','counter_balance':'DIALOGUE_KEY_COUNTER_BALANCE','counter_activity_one':'DIALOGUE_KEY_COUNTER_ACTIVITY_1','counter_activity_two':'DIALOGUE_KEY_COUNTER_ACTIVITY_2','counter_revisit':'DIALOGUE_KEY_COUNTER_REVISIT'},
'fishing':{'guide_message':'DIALOGUE_KEY_FISHING_GUIDE','guide_cap':'DIALOGUE_KEY_FISHING_CAP'},
'game':{'guide_message':'DIALOGUE_KEY_GAME_GUIDE','guide_cap':'DIALOGUE_KEY_GAME_CAP'},
'ecology':{'guide_message':'DIALOGUE_KEY_ECOLOGY_GUIDE','guide_cap':'DIALOGUE_KEY_ECOLOGY_CAP'}}


def commands(case):
    need(case in NAMES,'closed case')
    rows=PROGRAMS[case]
    need(0<len(rows)<=400 and rows[-1][2]=='end','bounded complete input')
    need(all(type(k) is int and k in (0,1,2,16,32,64,128) and type(n) is int and 0<=n<=1200 for k,n,_ in rows),'physical keys only')
    need(sum(n for _,n,_ in rows)+900<=50000,'frame limit')
    return ''.join(f'{k} {n} {label}\n' for k,n,label in rows).encode()


def generate(seed):
    import pr16_research_lifecycle_v2 as gen
    gen.OUT.mkdir(parents=True,exist_ok=True)
    source=prior.generate(seed).decode();token='int main(int argc,char**argv){'
    need(source.count(token)==1,'one inherited main')
    source=source.replace(token,'int accepted_bug_main(int argc,char**argv){')
    # Object positions are observation only; needed for the still-open moving guide.
    helper='''\nstatic void cn_objects(struct mCore*c){
 printf("{\\"objects\\":[");unsigned n=0;
 for(unsigned i=0;i<16;++i){unsigned a=0x02036D6CU+36*i;if(!(read8(c,a)&1))continue;
 printf("%s[%u,%u,%u,%u,%u,%u]",n++?",":"",i,read8(c,a+8),read8(c,a+10),read8(c,a+9),read16(c,a+16),read16(c,a+18));}
 printf("]}\\n");fflush(stdout);
}
'''
    body=(ROOT/C).read_text();mark='lc_event(c,label);fflush(stdout);'
    need(body.count(mark)==1,'one readonly observation extension')
    body=body.replace(mark,mark+'cn_objects(c);')
    return (source+helper+'\n'+body).encode()


def audit(rom):
    need(identity(rom)==CANDIDATE,'unchanged current candidate')
    def span(a,n):
        need(0x08000000<=a and a+n<=0x0a000000,'ROM range')
        return rom[a-0x08000000:a-0x08000000+n]
    def rd(a):return struct.unpack('<I',span(a,4))[0]
    model=load((ROOT/'content/research_economy_v1/canonical_model.json').read_bytes())
    by={r['dialogue_key']:r for r in model['dialogue']}
    table=rd(0x08054B0C);proof={}
    for case,(outside,inside,header,record,script,kind) in ROOTS.items():
        need(rd(rd(table+inside[0]*4)+inside[1]*4)==header,'actual grouped map root')
        e=rd(header+4);base=rd(e+(4 if kind==0 else 16));size=24 if kind==0 else 12
        need(base<=record<base+span(e,4)[kind]*size and (record-base)%size==0,'actual event record')
        need(rd(record+(16 if kind==0 else 8))==script,'physical host target')
        oh=rd(rd(table+outside[0]*4)+outside[1]*4);oe=rd(oh+4);warps=rd(oe+8);matches=[]
        for i in range(span(oe,4)[1]):
            x,y,level,index,num,group=struct.unpack('<HHBBBB',span(warps+8*i,8))
            if (x,y,group,num)==(outside[2],outside[3]-1,inside[0],inside[1]):matches.append((i,index))
        need(len(matches)==1,'ordinary door on adjacent outdoor tile')
        texts={}
        for label,key in DIALOGUES[case].items():
            r=by[key];raw=bytes.fromhex(r['encoded_hex']);need(span(r['runtime_address'],len(raw))==raw,'native text bytes')
            texts[label]=r
        proof[case]=dict(outdoor=list(outside),inside=list(inside),header=header,record=record,script=script,kind=kind,door=matches[0],dialogues=texts)
    return dict(candidate=CANDIDATE,roots=proof,rom_changes=0,arm_compiles=0)


def inspect(raw,case,audit_result):
    """Preliminary observation classification, not an independent acceptance oracle."""
    need(type(raw) is bytes and 0<len(raw)<100000,'bounded text trace')
    rows=[load(line) for line in raw.splitlines()]
    states={r['state']:r for r in rows if 'state' in r}
    need(rows[-1].get('status')=='MEASURED' and rows[-1].get('case')==NAMES.index(case),'terminal measurement, not PASS')
    need(states['fixture']['map']==list(ROOTS[case][0]) and states['door_entered']['map']==list(ROOTS[case][1]),'physical door transition')
    found={label:(label in states and states[label]['text']==r['encoded_hex'] and states[label]['field'] is False) for label,r in audit_result['roots'][case]['dialogues'].items()}
    if case=='lab':
        need(states['shop_open']['shop_active'] is True and states['shop_open']['eligible']==19 and states['shop_open']['result']==9,'actual native menu')
        need(states['final']['map']==list(ROOTS[case][0]) and states['final']['field'] and not states['final']['shop_active'],'ordinary lab return')
    return dict(physical_door_observed=True,dialogues=found,complete=all(found.values()),independent_oracle_accepted=False,numeric_counter_balance_displayed=False if case=='lab' else None,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False)
