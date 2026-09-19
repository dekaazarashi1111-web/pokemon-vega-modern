#ifndef VEGA_CIRCUS_SUSTAIN_POLICY_H
#define VEGA_CIRCUS_SUSTAIN_POLICY_H
#include <stdint.h>
/* 検証controllerの読取専用方策。seed/結果/能力/partyの変更は禁止。 */
struct su_view {
    uint32_t player, enemy, status1, status2;
    unsigned hp, maxhp, enemy_hp, enemy_maxhp, type1, type2, spatk_stage;
    unsigned moves[4], pp[4], best;
};
struct su_memory {
    uint32_t player, enemy;
    unsigned seen, last, toxic, seed, confuse, setup;
};
static uint64_t su_bulk_score(unsigned power, unsigned accuracy, unsigned attack,
    unsigned hp, unsigned defense, unsigned special_defense, unsigned utility)
{
    /* 最大255*100*65535*65535*(65535+65535)もuint64_t範囲内。 */
    uint64_t value=(uint64_t)power*(accuracy?accuracy:100U)*attack*hp
        *((uint64_t)defense+special_defense)/100U;
    return utility?value*2U:value;
}
static unsigned su_slot(const struct su_view *v, unsigned move)
{
    for(unsigned i=0;i<4U;++i)if(v->moves[i]==move && v->pp[i])return i;
    return 4U;
}
static unsigned su_choose(const struct su_view *v, struct su_memory *m)
{
    if(!m->seen || m->player!=v->player || m->enemy!=v->enemy){
        *m=(struct su_memory){.player=v->player,.enemy=v->enemy,.seen=1U};
    }
    unsigned slot=4U;
    /* 連続Protectを避け、正規状態の毒または実入力済みSeedのターンを稼ぐ。
     * Seedの試行を着弾証明には用いない。勝敗/保存受入は別validatorで判定。 */
    if(((v->status1&0x88U) || m->seed) && m->last!=182U)slot=su_slot(v,182U);
    if(slot==4U && !v->status1 && v->type1!=3U && v->type2!=3U
       && v->type1!=8U && v->type2!=8U && m->toxic<2U
       && v->enemy_hp>v->enemy_maxhp/4U){
        slot=su_slot(v,92U);if(slot<4U)++m->toxic;
    }
    if(slot==4U && !m->seed && v->type1!=12U && v->type2!=12U
       && v->enemy_hp>v->enemy_maxhp/4U){
        slot=su_slot(v,73U);if(slot<4U)++m->seed;
    }
    if(slot==4U && !(v->status2&7U) && !m->confuse
       && v->enemy_hp>v->enemy_maxhp/2U){
        slot=su_slot(v,109U);if(slot<4U)++m->confuse;
    }
    if(slot==4U && v->spatk_stage<8U && m->setup<2U
       && (uint64_t)v->hp*3U>(uint64_t)v->maxhp*2U){
        slot=su_slot(v,347U);if(slot<4U)++m->setup;
    }
    if(slot==4U)slot=v->best;
    if(slot<4U)m->last=v->moves[slot];
    return slot;
}
#ifndef CIRCUS_SUSTAIN_HOST_TEST
static struct su_memory su_memory;
static unsigned su_move_slot(struct mCore *c)
{
    uint32_t own=ADDR_BATTLE_MONS, foe=own+BATTLE_MON_SIZE;
    struct su_view v={.player=read32(c,own+0x48U),.enemy=read32(c,foe+0x48U),
        .status1=read32(c,foe+BATTLE_CORE_MON_STATUS1),.status2=read32(c,foe+BATTLE_CORE_MON_STATUS2),
        .hp=read16(c,own+BATTLE_CORE_MON_HP),.maxhp=read16(c,own+0x2CU),
        .enemy_hp=read16(c,foe+BATTLE_CORE_MON_HP),.enemy_maxhp=read16(c,foe+0x2CU),
        .type1=read8(c,foe+BATTLE_CORE_MON_TYPE1),.type2=read8(c,foe+BATTLE_CORE_MON_TYPE2),
        .spatk_stage=read8(c,own+BATTLE_CORE_MON_STAT_STAGES+4U),.best=wx_move_slot(c)};
    bp_require(c,v.hp && v.maxhp && v.hp<=v.maxhp && v.enemy_hp<=v.enemy_maxhp
        && v.spatk_stage<=12U,"Circus sustain battle ABI");
    for(unsigned i=0;i<4U;++i){v.moves[i]=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i);
        v.pp[i]=read8(c,own+BATTLE_MON_PP_OFFSET+i);}
    unsigned slot=su_choose(&v,&su_memory);
    bp_require(c,slot<4U && v.moves[slot] && v.pp[slot],"Circus sustain selected unusable move");
    fprintf(stderr,"CIRCUS_SUSTAIN frame=%u move=%u slot=%u hp=%u/%u enemy_hp=%u/%u types=%u,%u status1=%08x status2=%08x spatk_stage=%u player=%08x enemy=%08x battle=",
        b_frames,v.moves[slot],slot,v.hp,v.maxhp,v.enemy_hp,v.enemy_maxhp,v.type1,v.type2,v.status1,v.status2,v.spatk_stage,v.player,v.enemy);
    for(unsigned i=0;i<2U*BATTLE_MON_SIZE;++i)fprintf(stderr,"%02x",read8(c,own+i));
    fprintf(stderr,"\n");return slot;
}
static void su_team(struct mCore *c)
{
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT),types[6]={0U};
    uint64_t scores[6]={0U};unsigned used=0U;uint32_t covered=0U;
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus sustain move table");
    for(unsigned i=0;i<6U;++i){
        uint32_t mon=QOL_PLAYER_PARTY+100U*i;unsigned utility=0U;
        for(unsigned j=0;j<4U;++j){unsigned move=read16(c,mon+0x2CU+2U*j);
            if(read8(c,mon+0x34U+j) && (move==92U || move==73U))utility=1U;}
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+0x2CU+2U*j),pp=read8(c,mon+0x34U+j);
            bp_require(c,move<=1062U,"Circus sustain rental move");if(!move || !pp)continue;
            uint32_t row=table+12U*move;unsigned power=read8(c,row+1U),accuracy=read8(c,row+3U),split=read8(c,row+10U),type=read8(c,row+2U);
            bp_require(c,split<=2U && type<=24U && accuracy<=100U,"Circus sustain move fields");
            if(!power || split==2U)continue;
            types[i]|=1U<<type;
            uint64_t value=su_bulk_score(power,accuracy,read16(c,mon+(split?0x60U:0x5AU)),
                read16(c,mon+0x58U),read16(c,mon+0x5CU),read16(c,mon+0x62U),utility);
            if(value>scores[i])scores[i]=value;
        }
        fprintf(stderr,"CIRCUS_SUSTAIN_RENTAL slot=%u score=%llu types=%08x\n",i,(unsigned long long)scores[i],types[i]);
    }
    for(unsigned n=0;n<3U;++n){unsigned best=6U;uint64_t top=0U;
        for(unsigned i=0;i<6U;++i){uint64_t score=scores[i];
            if(!(types[i]&~covered))score/=4U;
            if(!(used&(1U<<i)) && (best==6U || score>top)){best=i;top=score;}}
        bp_require(c,best<6U && top>0U,"Circus sustain needs damaging rentals");used|=1U<<best;covered|=types[best];
        fprintf(stderr,"CIRCUS_SUSTAIN_TEAM index=%u original_slot=%u score=%llu\n",n,best,(unsigned long long)top);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}
#ifdef wx_team
#undef wx_team
#endif
#define wx_team su_team
#endif
#endif
