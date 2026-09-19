#ifndef VEGA_CIRCUS_FINISH_POLICY_H
#define VEGA_CIRCUS_FINISH_POLICY_H
#include <stdint.h>
/* 入力controllerだけの決着優先方策。未確認SeedをProtectの根拠にしない。 */
static unsigned fw_prefer(unsigned best,unsigned reliable,uint64_t best_score,uint64_t reliable_score)
{
    /* 5%以内の期待差なら命中95%以上を優先。乗算overflowなし。 */
    return reliable<4U && reliable_score>=best_score-best_score/20U?reliable:best;
}
static unsigned fw_protect(uint32_t own_status,uint32_t foe_status,unsigned last,
    unsigned own_hp,unsigned own_max,unsigned foe_hp,unsigned foe_max)
{
    if(last==182U || !own_hp || !own_max || !foe_hp || !foe_max || (own_status&0x88U))return 0U;
    if(foe_status&0x80U){unsigned ticks=(foe_status>>8U)&15U;
        return ticks>0U && (uint64_t)foe_hp*16U<=(uint64_t)foe_max*ticks;}
    return (foe_status&8U) && (uint64_t)foe_hp*8U<=foe_max;
}
#ifndef CIRCUS_FINISH_HOST_TEST
#include "mgba_pr16_circus_matchup.h"
static unsigned fw_last;
static uint32_t fw_player,fw_enemy;
static unsigned fw_move_slot(struct mCore *c)
{
    if(read16(c,0x0203DB20U)!=2U)return su_move_slot(c);
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE;
    /* 先発を無効技だけのNormalへ交換しない。実タイプ不利の交代だけを継承。 */
    unsigned role=mt_role(2U,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE1),
        0U,0U,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU));
    if(role)(void)mt_shift(c,role);
    uint32_t player=read32(c,own+0x48U),enemy=read32(c,foe+0x48U);
    if(player!=fw_player || enemy!=fw_enemy){fw_last=0U;fw_player=player;fw_enemy=enemy;}
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus finish move table ABI");
    unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    unsigned hp=read16(c,own+BATTLE_CORE_MON_HP),maxhp=read16(c,own+0x2CU);
    unsigned enemy_hp=read16(c,foe+BATTLE_CORE_MON_HP),enemy_max=read16(c,foe+0x2CU);
    uint32_t status=read32(c,own+BATTLE_CORE_MON_STATUS1),enemy_status=read32(c,foe+BATTLE_CORE_MON_STATUS1);
    unsigned best=4U,reliable=4U,toxic=4U,protect=4U,confuse=4U;
    uint64_t top=0U,safe=0U;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*i),pp=read8(c,own+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"Circus finish move range");
        if(move==92U)toxic=i;
        if(move==182U)protect=i;
        if(move==109U)confuse=i;
        uint32_t row=table+12U*move;
        unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
        bp_require(c,type<=24U && split<=2U && accuracy<=100U,"Circus finish move fields");
        if(!power || split==2U)continue;
        unsigned attack=read16(c,own+(split?8U:2U)),defense=read16(c,foe+(split?10U:4U));
        uint64_t score=(uint64_t)power*(accuracy?accuracy:100U)*(attack?attack:1U)*100U/(defense?defense:1U);
        if(type==read8(c,own+BATTLE_CORE_MON_TYPE1) || type==read8(c,own+BATTLE_CORE_MON_TYPE2))score=score*3U/2U;
        score=score*wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/100U;
        if(move==202U && (uint64_t)hp*3U<(uint64_t)maxhp*2U)score=score*3U/2U;
        if(score>top){top=score;best=i;}
        if((!accuracy || accuracy>=95U) && score>safe){safe=score;reliable=i;}
    }
    unsigned slot=fw_prefer(best,reliable,top,safe);
    if(protect<4U && fw_protect(status,enemy_status,fw_last,hp,maxhp,enemy_hp,enemy_max))slot=protect;
    if(slot==4U && toxic<4U && !enemy_status && t1!=3U && t2!=3U && t1!=8U && t2!=8U)slot=toxic;
    if(slot==4U && confuse<4U && !(read32(c,foe+BATTLE_CORE_MON_STATUS2)&7U))slot=confuse;
    if(slot==4U)slot=wx_move_slot(c); /* 全攻撃無効でも結果を注入せず実入力を続ける。 */
    bp_require(c,slot<4U && read8(c,own+BATTLE_MON_PP_OFFSET+slot),"Circus finish no legal move");
    fw_last=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*slot);
    fprintf(stderr,"CIRCUS_FINISH frame=%u move=%u slot=%u hp=%u/%u enemy_hp=%u/%u own_status=%08x enemy_status=%08x top=%llu reliable=%llu\n",
        b_frames,fw_last,slot,hp,maxhp,enemy_hp,enemy_max,status,enemy_status,(unsigned long long)top,(unsigned long long)safe);
    return slot;
}
#endif
#endif
