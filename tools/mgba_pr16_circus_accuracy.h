#ifndef VEGA_CIRCUS_ACCURACY_POLICY_H
#define VEGA_CIRCUS_ACCURACY_POLICY_H
#include <stdint.h>
/* 各方策は通常入力のみ。前回のToxic/個体再解決を継承し、命中と不成立Seedを分離。 */
static unsigned fp_select(unsigned variant,unsigned slot,unsigned move,unsigned flame,unsigned damage,
    unsigned own_type,unsigned foe_type,uint32_t own_status)
{
    if(move==126U && flame<4U)return flame;
    if(variant>=2U && damage<4U && move==182U && (own_status&0x88U))return damage;
    if(variant>=3U && damage<4U && own_type==12U && foe_type==10U && (move==73U || move==182U))return damage;
    return slot;
}
#ifndef CIRCUS_ACCURACY_HOST_TEST
#ifndef CIRCUS_ACCURACY_VARIANT
#error CIRCUS_ACCURACY_VARIANT_required
#endif
static unsigned fp_damage(struct mCore *c)
{
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE,table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus accuracy table ABI");
    unsigned best=4U,t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);uint64_t top=0U;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i),pp=read8(c,own+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"Circus accuracy move ABI");uint32_t row=table+move*12U;
        unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
        bp_require(c,type<=24U && accuracy<=100U && split<=2U,"Circus accuracy move fields");
        if(!power || split==2U)continue;
        unsigned atk=read16(c,own+(split?8U:2U)),def=read16(c,foe+(split?10U:4U));
        uint64_t score=(uint64_t)power*(accuracy?accuracy:100U)*(atk?atk:1U)*100U/(def?def:1U);
        if(type==read8(c,own+BATTLE_CORE_MON_TYPE1) || type==read8(c,own+BATTLE_CORE_MON_TYPE2))score=score*3U/2U;
        score=score*wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/100U;
        if(score>top){top=score;best=i;}
    }
    return best;
}
static unsigned fp_move_slot(struct mCore *c)
{
    unsigned selected=cd_move_slot(c);
    if(read16(c,0x0203DB20U)!=2U)return selected;
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE;
    unsigned flame=4U,confuse=4U;
    for(unsigned i=0;i<4U;++i){
        if(!read8(c,own+BATTLE_MON_PP_OFFSET+i))continue;
        unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i);
        if(move==53U)flame=i;
        if(move==109U)confuse=i;
    }
    unsigned before=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*selected);
    unsigned actual=fp_select(CIRCUS_ACCURACY_VARIANT,selected,before,flame,fp_damage(c),
        read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE1),read32(c,own+BATTLE_CORE_MON_STATUS1));
    if(CIRCUS_ACCURACY_VARIANT==4U && before==92U && confuse<4U && mt_memory.spent>=2U
        && !(read32(c,foe+BATTLE_CORE_MON_STATUS2)&7U))actual=confuse;
    unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*actual);
    if(actual!=selected){
        if(before==73U && su_memory.seed)--su_memory.seed;
        if(before==92U && su_memory.toxic)--su_memory.toxic;
        su_memory.last=move;mt_memory.last_slot=actual;mt_memory.last_move=move;
        mt_memory.last_pp=read8(c,own+BATTLE_MON_PP_OFFSET+actual);
    }
    fprintf(stderr,"CIRCUS_ACCURACY variant=%u frame=%u previous=%u actual=%u move=%u own_hp=%u enemy_hp=%u own_status=%08x own_confusion=%u enemy_status=%08x enemy_confusion=%u\n",
        CIRCUS_ACCURACY_VARIANT,b_frames,selected,actual,move,read16(c,own+BATTLE_CORE_MON_HP),read16(c,foe+BATTLE_CORE_MON_HP),
        read32(c,own+BATTLE_CORE_MON_STATUS1),read32(c,own+BATTLE_CORE_MON_STATUS2)&7U,
        read32(c,foe+BATTLE_CORE_MON_STATUS1),read32(c,foe+BATTLE_CORE_MON_STATUS2)&7U);
    return actual;
}
#endif
#endif
