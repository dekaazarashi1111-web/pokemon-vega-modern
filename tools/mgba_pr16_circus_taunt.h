#ifndef VEGA_CIRCUS_TAUNT_H
#define VEGA_CIRCUS_TAUNT_H
#include <stdint.h>
/* 正規選出の3個体を増減せずTaunt持ちを先頭へ移す。15勝までは順序不変。 */
static unsigned ta_lead(unsigned streak,const unsigned chosen[3],const unsigned capable[6])
{
    unsigned used=0U;
    for(unsigned i=0;i<3U;++i){
        if(chosen[i]>=6U || (used&(1U<<chosen[i])))return 3U;
        used|=1U<<chosen[i];
    }
    if(streak>=15U)for(unsigned i=0;i<3U;++i)if(capable[chosen[i]])return i;
    return 0U;
}
struct ta_history {unsigned attempts,pending,pp,cooldown,paid;};
/* PP消費は試行の証拠であってTaunt着弾/特性抑制の証明ではない。
 * 同一対面は最大2試行。成功/無効/混乱を勝敗と混同せず最終rawで判定。 */
static unsigned ta_attempt(struct ta_history *h,unsigned slot,unsigned pp,unsigned status_moves,
    unsigned hp,unsigned maxhp,unsigned normal)
{
    if(h->pending){
        if(pp<h->pp){++h->paid;h->cooldown=3U;}
        h->pending=0U;
    }
    if(h->cooldown){--h->cooldown;return normal;}
    if(slot>=4U || !pp || status_moves<2U || hp<=maxhp/4U || !maxhp || hp>maxhp || h->attempts>=2U)return normal;
    ++h->attempts;h->pending=1U;h->pp=pp;return slot;
}
#ifndef CIRCUS_TAUNT_HOST_TEST
static struct {uint32_t pid,ot,enemy,enemy_ot;unsigned streak,seen;struct ta_history h;} ta_memory;
static unsigned ta_move(struct mCore *c,unsigned normal)
{
    unsigned streak=read16(c,0x0203DB20U);if(streak<15U)return normal;
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE,table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    uint32_t pid=read32(c,own+0x48U),ot=read32(c,own+0x54U),enemy=read32(c,foe+0x48U),enemy_ot=read32(c,foe+0x54U);
    if(!ta_memory.seen || ta_memory.streak!=streak || ta_memory.pid!=pid || ta_memory.ot!=ot
        || ta_memory.enemy!=enemy || ta_memory.enemy_ot!=enemy_ot){
        ta_memory.pid=pid;ta_memory.ot=ot;ta_memory.enemy=enemy;ta_memory.enemy_ot=enemy_ot;
        ta_memory.seen=1U;ta_memory.streak=streak;ta_memory.h=(struct ta_history){0};
    }
    unsigned slot=4U,pp=0U,status_moves=0U;
    for(unsigned i=0;i<4U;++i){
        if(read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i)==269U){slot=i;pp=read8(c,own+BATTLE_MON_PP_OFFSET+i);}
        unsigned move=read16(c,foe+BATTLE_MON_MOVES_OFFSET+2U*i);
        bp_require(c,move<=1062U,"Circus Taunt foe move ABI");
        if(move && read8(c,foe+BATTLE_MON_PP_OFFSET+i) && read8(c,table+12U*move+10U)==2U)++status_moves;
    }
    unsigned actual=ta_attempt(&ta_memory.h,slot,pp,status_moves,read16(c,foe+BATTLE_CORE_MON_HP),read16(c,foe+0x2CU),normal);
    if(actual!=normal || ta_memory.h.attempts)
        fprintf(stderr,"CIRCUS_TAUNT frame=%u streak=%u own=%u ot=%u foe=%u foe_ot=%u slot=%u actual=%u pp=%u status_moves=%u attempts=%u paid=%u cooldown=%u\n",b_frames,streak,pid,ot,enemy,enemy_ot,slot,actual,pp,status_moves,ta_memory.h.attempts,ta_memory.h.paid,ta_memory.h.cooldown);
    return actual;
}
#endif
#endif
