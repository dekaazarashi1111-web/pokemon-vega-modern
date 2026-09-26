#ifndef VEGA_CIRCUS_DRAIN_H
#define VEGA_CIRCUS_DRAIN_H
#include <stdint.h>
/* 既に毒が効いている低HP相手へ追加Seedをせず、通常攻撃で決着を早める。 */
static unsigned cd_choose(unsigned selected,unsigned move,unsigned drain,unsigned type,
    uint32_t status,unsigned hp,unsigned maxhp)
{
    if(move==73U && drain<4U && type==12U && (status&0x88U)
       && hp>0U && maxhp>0U && (uint64_t)hp*2U<=maxhp)return drain;
    return selected;
}
#ifndef CIRCUS_DRAIN_HOST_TEST
#include "mgba_pr16_circus_matchup.h"
static unsigned cd_move_slot(struct mCore *c)
{
    unsigned selected=mt_move_slot(c);
    if(read16(c,0x0203DB20U)!=2U)return selected;
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE;
    unsigned drain=4U,move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*selected);
    for(unsigned i=0;i<4U;++i)
        if(read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i)==202U && read8(c,own+BATTLE_MON_PP_OFFSET+i))drain=i;
    unsigned actual=cd_choose(selected,move,drain,read8(c,own+BATTLE_CORE_MON_TYPE1),
        read32(c,foe+BATTLE_CORE_MON_STATUS1),read16(c,foe+BATTLE_CORE_MON_HP),read16(c,foe+0x2CU));
    if(actual!=selected){
        su_memory.seed=0U;su_memory.last=202U;
        mt_memory.last_slot=actual;mt_memory.last_move=202U;mt_memory.last_pp=read8(c,own+BATTLE_MON_PP_OFFSET+actual);
        fprintf(stderr,"CIRCUS_DRAIN frame=%u selected=%u actual=%u enemy_hp=%u/%u\n",b_frames,selected,actual,
            read16(c,foe+BATTLE_CORE_MON_HP),read16(c,foe+0x2CU));
    }
    return actual;
}
#endif
#endif
