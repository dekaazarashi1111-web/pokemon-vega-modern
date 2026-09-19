#ifndef VEGA_CIRCUS_EFFECTIVE_POLICY_H
#define VEGA_CIRCUS_EFFECTIVE_POLICY_H
#include <stdint.h>
/* 低HPでも無効な攻撃を連打しない。実技/PP/タイプ/状態の読取だけで選ぶ。 */
static unsigned ef_choose(unsigned selected, unsigned immune_damage, unsigned toxic_slot,
    unsigned toxic_attempts, uint32_t status1, unsigned type1, unsigned type2)
{
    if(immune_damage && toxic_slot<4U && toxic_attempts<2U && !status1
       && type1!=3U && type2!=3U && type1!=8U && type2!=8U)
        return toxic_slot;
    return selected;
}
#ifndef CIRCUS_EFFECTIVE_HOST_TEST
static unsigned ef_move_slot(struct mCore *c)
{
    /* 既存方策を保持し、ダメージ0の通常攻撃が選ばれた時だけ介入する。 */
    unsigned selected=su_move_slot(c),toxic=4U;
    uint32_t mon=ADDR_BATTLE_MONS,foe=mon+BATTLE_MON_SIZE;
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    unsigned move=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*selected);
    uint32_t row=table+12U*move;
    unsigned type=read8(c,row+2U),t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    unsigned immune=read8(c,row+1U)>0U && read8(c,row+10U)<2U
        && (!wx_effect(type,t1) || !wx_effect(type,t2));
    for(unsigned i=0;i<4U;++i)
        if(read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*i)==92U && read8(c,mon+BATTLE_MON_PP_OFFSET+i))toxic=i;
    unsigned slot=ef_choose(selected,immune,toxic,su_memory.toxic,
        read32(c,foe+BATTLE_CORE_MON_STATUS1),t1,t2);
    if(slot!=selected){++su_memory.toxic;su_memory.last=92U;}
    fprintf(stderr,"CIRCUS_EFFECTIVE frame=%u selected=%u actual=%u immune_damage=%u toxic_slot=%u attempts=%u\n",
        b_frames,selected,slot,immune,toxic,su_memory.toxic);
    return slot;
}
#endif
#endif
