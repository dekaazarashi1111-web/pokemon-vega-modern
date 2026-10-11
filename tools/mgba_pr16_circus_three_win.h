#ifndef VEGA_CIRCUS_THREE_WIN_POLICY_H
#define VEGA_CIRCUS_THREE_WIN_POLICY_H
#include <stdint.h>
/* ダメージ技・実能力・素早さだけで候補を順位付け。ROM/RAMを書き換えない。 */
static uint64_t cw_move_score(unsigned power,unsigned accuracy,unsigned split,
    unsigned attack,unsigned special_attack,unsigned speed)
{
    if(!power || split>1U)return 0U;
    return (uint64_t)power*(accuracy?accuracy:100U)
        *(split?special_attack:attack)*(128U+speed);
}
#ifndef CIRCUS_TEAM_HOST_TEST
static void cw_team(struct mCore *c)
{
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus move table boundary");
    uint64_t scores[6]={0};unsigned used=0U;
    for(unsigned i=0;i<6U;++i){
        uint32_t mon=QOL_PLAYER_PARTY+100U*i;
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+0x2CU+2U*j),pp=read8(c,mon+0x34U+j);
            bp_require(c,move<=1062U,"Circus team move boundary");
            if(!move || !pp)continue;
            uint32_t row=table+12U*move;unsigned split=read8(c,row+10U);
            bp_require(c,split<=2U,"Circus team split boundary");
            uint64_t value=cw_move_score(read8(c,row+1U),read8(c,row+3U),split,
                read16(c,mon+0x5AU),read16(c,mon+0x60U),read16(c,mon+0x5EU));
            if(value>scores[i])scores[i]=value;
        }
    }
    for(unsigned n=0;n<3U;++n){
        unsigned best=6U;
        for(unsigned i=0;i<6U;++i)if(!(used&(1U<<i)) && (best==6U || scores[i]>scores[best]))best=i;
        bp_require(c,best<6U && scores[best]>0U,"Circus has fewer than three damaging rentals");used|=1U<<best;
        fprintf(stderr,"CIRCUS_TEAM index=%u original_slot=%u score=%llu\n",n,best,(unsigned long long)scores[best]);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}
#define wx_team cw_team
#endif
#endif
