"""29戦目の実対面変更を読み、要求技のない控え選択を入力だけで補完する。"""
from __future__ import annotations
import hashlib
import json
import re

OLD_TRACE = {'size': 964542, 'sha256': '37ed442f4ed6c658e489f900d2993d2fd8b745364b9dffc96bd4a154de9de1a7'}
OLD_POLICY_SHA = '2945ac370e24a3b1035e8c5fa007fbaa0d21787f677d6cdef285ae3369c30c8c'
MARKER = b'CIRCUS_RESERVE_FALLBACK '
PURE = r'''
/* 要求されたDark技が控えにない新対面だけを補完。種族名・RNG・frameで選ばない。 */
static unsigned rf_needed(unsigned streak,unsigned wanted,unsigned own1,unsigned own2,
    unsigned foe1,unsigned foe2,uint32_t attacks)
{
    return streak>=28U && wanted==17U && own1!=0U && own2!=0U
        && foe1==0U && foe2==0U && attacks==(1U<<7U);
}
static uint64_t rf_rank(unsigned power,unsigned accuracy,unsigned attack,unsigned defense,
    unsigned effect,unsigned hp,unsigned maxhp)
{
    if(!power || power>255U || accuracy>100U || !attack || attack>65535U || !defense
        || defense>65535U || effect>400U || !hp || !maxhp || hp>maxhp || maxhp>65535U)return 0U;
    return (uint64_t)power*(accuracy?accuracy:100U)*attack*effect/defense*hp/maxhp;
}
static unsigned rf_pick(uint64_t active,const uint64_t scores[3])
{
    unsigned target=3U;uint64_t best=active+active/4U;
    for(unsigned i=0;i<3U;++i)if(scores[i]>best){best=scores[i];target=i;}
    return target;
}
'''
NATIVE = r'''
static unsigned rf_fallback(struct mCore *c,unsigned streak,unsigned wanted,uint32_t attacks)
{
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE;
    unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    unsigned o1=read8(c,own+BATTLE_CORE_MON_TYPE1),o2=read8(c,own+BATTLE_CORE_MON_TYPE2);
    if(!rf_needed(streak,wanted,o1,o2,t1,t2,attacks))return 3U;
    uint32_t pid=read32(c,own+0x48U),ot=read32(c,own+0x54U),table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    uint64_t scores[3]={0U},active=0U;
    /* 控え自身のtype/STABを技から推測しない。場の相手typeと実能力/HP/PPのみ。 */
    for(unsigned i=0;i<4U;++i){
        uint32_t mon=i==3U?own:QOL_PLAYER_PARTY+100U*i;
        if(i<3U && read32(c,mon)==pid && read32(c,mon+4U)==ot)continue;
        unsigned hp=read16(c,mon+(i==3U?BATTLE_CORE_MON_HP:0x56U));
        unsigned maxhp=read16(c,mon+(i==3U?0x2CU:0x58U));
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+(i==3U?BATTLE_MON_MOVES_OFFSET:0x2CU)+2U*j);
            unsigned pp=read8(c,mon+(i==3U?BATTLE_MON_PP_OFFSET:0x34U)+j);
            bp_require(c,move<=1062U,"Circus fallback move ABI");if(!move || !pp)continue;
            uint32_t row=table+12U*move;
            unsigned power=read8(c,row+1U),type=read8(c,row+2U),acc=read8(c,row+3U),split=read8(c,row+10U);
            bp_require(c,type<=24U && acc<=100U && split<=2U,"Circus fallback fields");
            if(!power || split==2U)continue;
            unsigned atk=read16(c,mon+(i==3U?(split?8U:2U):(split?0x60U:0x5AU)));
            unsigned def=read16(c,foe+(split?10U:4U));
            unsigned effect=wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2));
            uint64_t score=rf_rank(power,acc,atk,def,effect,hp,maxhp);
            if(i==3U){if(type==o1 || type==o2)score=score*3U/2U;if(score>active)active=score;}
            else if(score>scores[i])scores[i]=score;
        }
    }
    unsigned target=rf_pick(active,scores);if(target==3U)return target;
    fprintf(stderr,"CIRCUS_RESERVE_FALLBACK {\"frame\":%u,\"streak\":%u,\"wanted\":%u,\"attacks\":%u,\"foe_types\":[%u,%u],\"own_types\":[%u,%u],\"hp\":%u,\"maxhp\":%u,\"target\":%u,\"active_score\":%llu,\"scores\":[%llu,%llu,%llu]}\n",
        b_frames,streak,wanted,attacks,t1,t2,o1,o2,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU),target,
        (unsigned long long)active,(unsigned long long)scores[0],(unsigned long long)scores[1],(unsigned long long)scores[2]);
    return target;
}
'''


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw): return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def rows(raw, marker):
    return [json.loads(line[len(marker):]) for line in raw.splitlines() if line.startswith(marker)]


def amend(text):
    need(hashlib.sha256(text.encode()).hexdigest()==OLD_POLICY_SHA, 'saved policy identity')
    anchor='static void tp_consider(struct mCore *c)\n{'
    need(text.count(anchor)==1, 'tactical definition anchor')
    text=text.replace(anchor, PURE+NATIVE+'\n'+anchor, 1)
    anchor='    if(target==3U)return;\n    uint32_t p=QOL_PLAYER_PARTY+100U*target'
    need(text.count(anchor)==1, 'missing-reserve boundary')
    text=text.replace(anchor, '    if(target==3U)target=rf_fallback(c,streak,wanted,attacks);\n'+anchor, 1)
    return text


def adapt(text, header):
    import pr16_circus_battle29_recheck_policy as parent
    return amend(parent.adapt(text, header))


def original(raw):
    need(identity(raw)==OLD_TRACE, 'previous trace identity')
    events=rows(raw,b'CIRCUS_CONTINUOUS ');holds=rows(raw,b'CIRCUS_HOLD_RECHECK ')
    need(len(events)==139 and len(holds)==6, 'previous event/hold count')
    settled=[e for e in events if e['label']=='settled']
    need(sum(e['outcome']==1 for e in settled)==28 and sum(e['outcome']==2 for e in settled)==1, 'previous outcome')
    need([e['hp'] for e in holds]==[182,157,146,135,124,113]
         and holds[-1]['frame']==466572 and len({e['foe'] for e in holds})==1, 'actual hold boundary')
    line=next(l for l in raw.splitlines() if l.startswith(b'CIRCUS_RELIABILITY frame=468129 streak=28 '))
    own,foe=[bytes.fromhex(re.search(k+rb'=([0-9a-f]+)',line)[1].decode()) for k in (b'own',b'foe')]
    need(list(foe[0x21:0x23])==[0,0] and list(own[0x21:0x23])==[11,11]
         and int.from_bytes(own[0x28:0x2a],'little')==102, 'actual changed matchup')
    need(events[-2]['label']=='saved' and events[-1]['label']=='reloaded'
         and events[-1]['save_counter']==3 and events[-1]['bp']==81, 'original save boundary')
    return dict(events=139,wins=28,losses=1,holds=holds,next_frame=468129,next_foe_types=[0,0],
                next_own_hp=102,original_conclusion='failure',legacy_validator_failure_preserved=True,
                reason_ja='水対面は6回目の攻撃で終了。468129は別個体の実type0/0。HP半分まで同じ水相手という予測は原本と不一致。')


def prefix_proof(old,new):
    original(old)
    before,found,tail=new.partition(MARKER)
    need(found and old.startswith(before), 'changed before new matchup')
    first=json.loads(tail.splitlines()[0]);events=rows(new,b'CIRCUS_CONTINUOUS ')
    need(events[:134]==rows(old,b'CIRCUS_CONTINUOUS ')[:134], 'accepted action29 prefix changed')
    need(rows(new,b'CIRCUS_HOLD_RECHECK ')[:6]==rows(old,b'CIRCUS_HOLD_RECHECK '), 'six holds changed')
    need(first['frame']==468129 and first['streak']==28 and first['wanted']==17
         and first['foe_types']==[0,0] and first['own_types']==[11,11]
         and first['hp']==102 and first['maxhp']==182 and first['target']==2, 'fallback input boundary')
    need(first['scores'][2]>first['active_score']+first['active_score']//4, 'fallback not justified')
    need(b'CIRCUS_TACTICAL begin frame=468129 streak=28 ' in new, 'normal switch absent')
    return dict(exact_event_count=134,byte_prefix=identity(before),first_fallback=first,
                accepted_standalone_replays=0,continuation_prefix_wins=28)
