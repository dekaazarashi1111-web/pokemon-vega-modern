#ifndef VEGA_CIRCUS_REENTRY_POLICY_H
#define VEGA_CIRCUS_REENTRY_POLICY_H
#include <stdint.h>
/* 実PP消費に対してHP減少なしを2回観測した攻撃は、別の有効攻撃へ切り替える。
 * Protect/回復も含む入力上の無進展であり、特性抑制の証明には使用しない。 */
static unsigned rr_stalls(unsigned previous,unsigned pp_before,unsigned pp_after,unsigned hp_before,unsigned hp_after)
{
    if(pp_after>=pp_before)return previous;
    return hp_after<hp_before?0U:(previous<2U?previous+1U:2U);
}
static unsigned rr_pick(unsigned selected,unsigned blocked,const uint64_t score[4])
{
    if(selected>=4U || !(blocked&(1U<<selected)))return selected;
    unsigned best=selected;uint64_t top=0U;
    for(unsigned i=0;i<4U;++i)if(!(blocked&(1U<<i)) && score[i]>top){best=i;top=score[i];}
    return best;
}
#ifndef CIRCUS_REENTRY_HOST_TEST
static struct {
    uint32_t own,foe,own_ot,foe_ot;
    unsigned seen,streak,slot,pp,hp,damaging,blocked,stalls[4];
} rr_memory;
static unsigned rr_move_slot(struct mCore *c)
{
    unsigned selected=fp_move_slot(c),streak=read16(c,0x0203DB20U);
    if(streak<4U)return selected; /* 受入prefix4戦の入力は完全に維持。 */
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE;
    uint32_t pid=read32(c,own+0x48U),enemy=read32(c,foe+0x48U);
    uint32_t ot=read32(c,own+0x54U),enemy_ot=read32(c,foe+0x54U);
    unsigned hp=read16(c,foe+BATTLE_CORE_MON_HP);
    if(!rr_memory.seen || rr_memory.streak!=streak || rr_memory.own!=pid || rr_memory.foe!=enemy
        || rr_memory.own_ot!=ot || rr_memory.foe_ot!=enemy_ot){
        rr_memory.own=pid;rr_memory.foe=enemy;rr_memory.own_ot=ot;rr_memory.foe_ot=enemy_ot;
        rr_memory.streak=streak;rr_memory.seen=1U;rr_memory.damaging=0U;rr_memory.blocked=0U;
        for(unsigned i=0;i<4U;++i)rr_memory.stalls[i]=0U;
    }else if(rr_memory.damaging){
        unsigned i=rr_memory.slot,pp=read8(c,own+BATTLE_MON_PP_OFFSET+i);
        rr_memory.stalls[i]=rr_stalls(rr_memory.stalls[i],rr_memory.pp,pp,rr_memory.hp,hp);
        if(rr_memory.stalls[i]>=2U)rr_memory.blocked|=1U<<i;
    }
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus reentry move table ABI");
    uint64_t scores[4]={0};unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i),pp=read8(c,own+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"Circus reentry move ABI");uint32_t row=table+12U*move;
        unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
        bp_require(c,type<=24U && accuracy<=100U && split<=2U,"Circus reentry move fields");
        if(!power || split==2U)continue;
        unsigned atk=read16(c,own+(split?8U:2U)),def=read16(c,foe+(split?10U:4U));
        uint64_t score=(uint64_t)power*(accuracy?accuracy:100U)*(atk?atk:1U)*100U/(def?def:1U);
        if(type==read8(c,own+BATTLE_CORE_MON_TYPE1) || type==read8(c,own+BATTLE_CORE_MON_TYPE2))score=score*3U/2U;
        scores[i]=score*wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/100U;
    }
    unsigned actual=rr_pick(selected,rr_memory.blocked,scores);
    bp_require(c,actual<4U,"Circus reentry selected slot");
    unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*actual);
    rr_memory.slot=actual;rr_memory.pp=read8(c,own+BATTLE_MON_PP_OFFSET+actual);rr_memory.hp=hp;
    rr_memory.damaging=read8(c,table+12U*move+1U)>0U && read8(c,table+12U*move+10U)<2U;
    if(actual!=selected){su_memory.last=move;mt_memory.last_slot=actual;mt_memory.last_move=move;mt_memory.last_pp=rr_memory.pp;}
    fprintf(stderr,"CIRCUS_REENTRY frame=%u streak=%u selected=%u actual=%u move=%u blocked=%u pp=%u foe_hp=%u\n",
        b_frames,streak,selected,actual,move,rr_memory.blocked,rr_memory.pp,hp);
    return actual;
}
#endif
#endif
