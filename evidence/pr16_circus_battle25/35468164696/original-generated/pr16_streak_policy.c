static unsigned ta_lead(unsigned,const unsigned[3],const unsigned[6]);
static unsigned ta_move(struct mCore *c,unsigned);
static void tp_consider(struct mCore *c);
#ifndef VEGA_CIRCUS_RELIABILITY_H
#define VEGA_CIRCUS_RELIABILITY_H
#include <stdint.h>
/* 期待値差10%以内では命中率を優先。無効技・PP切れ・paid無進展を復活させない。
 * scoreは読取専用の既存評価値。勝敗、乱数、能力、ownerには介入しない。 */
static unsigned rl_pick(unsigned selected, unsigned blocked,
    const uint64_t score[4], const unsigned accuracy[4])
{
    if (selected >= 4U || !score[selected]) return selected;
    unsigned best=selected;
    uint64_t floor=score[selected]-score[selected]/10U;
    for (unsigned i=0;i<4U;++i) {
        if ((blocked&(1U<<i)) || !score[i] || score[i]<floor || !accuracy[i] || accuracy[i]>100U) continue;
        if (accuracy[i]>accuracy[best] || (accuracy[i]==accuracy[best] && score[i]>score[best])) best=i;
    }
    return best;
}
#endif

#ifndef VEGA_CIRCUS_COVERAGE_H
#define VEGA_CIRCUS_COVERAGE_H
/* 初回3戦の既受入順位はそのまま。再入場では補助技の一律2倍加点を外す。
 * party生成/能力/選択結果へのhost書込みはせず、通常chooser入力で選ぶ。 */
static unsigned cv_utility(unsigned streak,unsigned utility)
{
    return streak<3U?utility:0U;
}
#endif

static unsigned rr_move_slot(struct mCore *c);
#define CIRCUS_ACCURACY_VARIANT 1U
static unsigned fp_move_slot(struct mCore *c);
static unsigned sc_events;
static unsigned wx_effect(unsigned attack,unsigned defense) {
    static const unsigned char table[19][19]={
        {10,10,10,10,10,5,10,0,5,10,10,10,10,10,10,10,10,10,10},
        {20,10,5,5,10,20,5,0,20,10,10,10,10,10,5,20,10,20,5},
        {10,20,10,10,10,5,20,10,5,10,10,10,20,5,10,10,10,10,10},
        {10,10,10,5,5,5,10,5,0,10,10,10,20,10,10,10,10,10,20},
        {10,10,0,20,10,20,5,10,20,10,20,10,5,20,10,10,10,10,10},
        {10,5,20,10,5,10,20,10,5,10,20,10,10,10,10,20,10,10,10},
        {10,5,5,5,10,10,10,5,5,10,5,10,20,10,20,10,10,20,5},
        {0,10,10,10,10,10,10,20,10,10,10,10,10,10,20,10,10,5,10},
        {10,10,10,10,10,20,10,10,5,10,5,5,10,5,10,20,10,10,20},
        {10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10},
        {10,10,10,10,10,5,20,10,20,10,5,5,20,10,10,20,5,10,10},
        {10,10,10,10,20,20,10,10,10,10,20,5,5,10,10,10,5,10,10},
        {10,10,5,5,20,20,5,10,5,10,5,20,5,10,10,10,5,10,10},
        {10,10,20,10,0,10,10,10,10,10,10,20,5,5,10,10,5,10,10},
        {10,20,10,20,10,10,10,10,5,10,10,10,10,10,5,10,10,0,10},
        {10,10,20,10,20,10,10,10,5,10,5,5,20,10,10,5,20,10,10},
        {10,10,10,10,10,10,10,10,5,10,10,10,10,10,10,10,20,10,0},
        {10,5,10,10,10,10,10,20,10,10,10,10,10,10,20,10,10,5,5},
        {10,20,10,5,10,10,10,10,5,10,5,10,10,10,10,10,20,20,10},
    };
    return attack<19U && defense<19U?table[attack][defense]:10U;
}

static unsigned wx_move_slot(struct mCore *c) {
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"win move table ABI differs");
    unsigned best=4U;uint64_t top=0;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*i);
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        bp_require(c,move<=1062U,"win move ID out of canonical range");
        uint32_t row=table+12U*move;
        unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
        bp_require(c,split<=2U && type<=24U,"win move type/split ABI differs");
        if(split==2U || !power)continue;
        unsigned attack=read16(c,ADDR_BATTLE_MONS+(split==0U?2U:8U));
        unsigned defense=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+(split==0U?4U:10U));
        uint64_t score=(uint64_t)power*(accuracy?accuracy:100U)*(attack?attack:1U)*100U/(defense?defense:1U);
        if(type==read8(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_TYPE1) || type==read8(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_TYPE2))score=score*3U/2U;
        unsigned t1=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE1);
        unsigned t2=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE2);
        unsigned effect=wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2));
        score=score*effect/100U;
        fprintf(stderr,"BP_WIN_MOVE frame=%u slot=%u move=%u pp=%u power=%u type=%u split=%u score=%llu\n",b_frames,i,move,pp,power,type,split,(unsigned long long)score);
        if(best==4U || score>top){best=i;top=score;}
    }
    bp_require(c,best<4U,"win policy has no damaging move; do not inject Struggle");
    return best;
}

static unsigned wx_party_score(struct mCore *c,unsigned slot) {
    uint32_t p=QOL_PLAYER_PARTY+100U*slot;unsigned score=0;
    /* 固定100byte Party ABIのmaxHPと5能力値。現在HP/PPは変更しない。 */
    for(unsigned at=0x58U;at<100U;at+=2U)score+=read16(c,p+at);
    return score;
}

static void wx_cursor(struct mCore *c,unsigned target) {
    bp_require(c,target<6U,"win party target out of bounds");
    for(unsigned tries=0;tries<16U && read8(c,SP_PARTY_SLOT)!=target;++tries){
        unsigned at=read8(c,SP_PARTY_SLOT);
        bp_require(c,at<8U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"win chooser disappeared");
        unsigned key=at>=6U?QOL_KEY_UP:target==0U?QOL_KEY_LEFT:at==0U?QOL_KEY_RIGHT:at<target?QOL_KEY_DOWN:QOL_KEY_UP;
        b_press(c,key,60U);
    }
    bp_require(c,read8(c,SP_PARTY_SLOT)==target,"win party cursor did not follow keys");
}

static void wx_team(struct mCore *c) {
    unsigned used=0U;
    for(unsigned n=0;n<3U;++n){
        unsigned best=6U,score=0U;
        for(unsigned i=0;i<6U;++i){
            unsigned value=wx_party_score(c,i);
            if(!(used&(1U<<i)) && (best==6U || value>score)){best=i;score=value;}
        }
        bp_require(c,best<6U,"win rental ranking has no candidate");used|=1U<<best;
        fprintf(stderr,"BP_WIN_TEAM index=%u original_slot=%u score=%u\n",n,best,score);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}

static unsigned wx_reserve(struct mCore *c,unsigned active) {
    bp_require(c,active<3U,"active native index out of bounds");
    unsigned best=6U;uint64_t top=0U;
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    unsigned t1=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE1);
    unsigned t2=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE2);
    for(unsigned i=0;i<3U;++i){
        uint32_t mon=QOL_PLAYER_PARTY+100U*i;
        if(!read16(c,mon+0x56U))continue;
        uint64_t strongest=0U;
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+0x2CU+2U*j),pp=read8(c,mon+0x34U+j);
            bp_require(c,move<=1062U,"reserve move ABI differs");
            if(!move || !pp)continue;
            uint32_t row=table+12U*move;
            unsigned power=read8(c,row+1U),type=read8(c,row+2U),accuracy=read8(c,row+3U),split=read8(c,row+10U);
            bp_require(c,split<=2U,"reserve split ABI differs");
            if(split==2U || !power)continue;
            unsigned attack=read16(c,mon+(split==0U?0x5AU:0x60U));
            unsigned defense=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+(split==0U?4U:10U));
            uint64_t value=(uint64_t)power*(accuracy?accuracy:100U)*attack
                *wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/(defense?defense:1U);
            if(value>strongest)strongest=value;
        }
        fprintf(stderr,"BP_WIN_RESERVE frame=%u slot=%u score=%llu\n",b_frames,i,(unsigned long long)strongest);
        if(best==6U || strongest>top){best=i;top=strongest;}
    }
    return best;
}

struct BPReturn {
    unsigned start,turns,switches,pp_events,outcome,outcome_frame,facility_frame;
    unsigned final_count,marker,snapshot,pending,streak,script,callback2;
};

static void br_trace(struct mCore *c,const char *label) {
    fprintf(stderr,"BP_RETURN label=%s frame=%u cb2=%08x main=%08x command=%u ctrl=%08x exec=%x newbs=%08x outcome=%u index=%u hp=%u enemy_hp=%u slot=%u script=%08x pending=%u streak=%u snapshot=%u marker=%u count=%u bp=%u save=%u\n",
        label,b_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,0x03004FC4U),
        read8(c,0x02022B24U),read32(c,0x03005020U),read32(c,0x02023B28U),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BATTLE_CORE_BATTLE_OUTCOME),
        read16(c,ADDR_BATTLER_PARTY_INDEXES),read16(c,ADDR_BATTLE_MONS+BATTLE_CORE_MON_HP),
        read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP),read8(c,SP_PARTY_SLOT),
        read32(c,SP_SCRIPT_PTR),read8(c,BP_F(reward_pending)),read16(c,BP_F(current_streak)),
        read8(c,BP_F(snapshot_valid)),read8(c,BP_F(marker)),read8(c,QOL_PLAYER_PARTY_COUNT),
        read16(c,BP_F(battle_points)),read32(c,P03_SAVE_COUNTER));
}

static bool br_move_menu(struct mCore *c) {
    return read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U);
}

static void br_move(struct mCore *c,struct BPReturn *w) {
    unsigned slot=4U,move=0U,pp=0U;
    bp_require(c,n_action(c),"return move outside native action");
    slot=rr_move_slot(c);
    move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot);
    pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot);
    br_trace(c,"turn-start");
    bp_require(c,slot<4U,"return has no native move with PP; do not fabricate Struggle");
    n_cursor(c,0U);
    for(unsigned f=0;f<600U && !br_move_menu(c);++f)
        b_frame(c,f%90U==0U && n_action(c)?QOL_KEY_A:0U);
    b_frames_run(c,0U,60U);
    bp_require(c,br_move_menu(c),"return native move menu absent");
    for(unsigned i=0;i<6U && read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)!=slot;++i){
        unsigned at=read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);
        bp_require(c,at<4U,"return invalid native move cursor");
        b_press(c,(at&1U)!=(slot&1U)?((slot&1U)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((slot&2U)?QOL_KEY_DOWN:QOL_KEY_UP),12U);
    }
    bp_require(c,read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)==slot,"return move cursor did not follow keys");
    unsigned chosen=b_frames+1U,index=read16(c,ADDR_BATTLER_PARTY_INDEXES),spent=0U;
    b_press(c,QOL_KEY_A,2U);++w->turns;
    for(unsigned f=0;f<18000U;++f){
        if(!spent && read16(c,ADDR_BATTLER_PARTY_INDEXES)==index
            && read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*slot)==move
            && read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+slot)<pp){
            spent=b_frames;++w->pp_events;
        }
        if(read8(c,BATTLE_CORE_BATTLE_OUTCOME) || !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)
            || read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY || n_action(c)){
            fprintf(stderr,"BP_RETURN_MOVE turn=%u chosen=%u returned=%u move=%u slot=%u pp_before=%u pp_event=%u\n",w->turns,chosen,b_frames,move,slot,pp,spent);
            br_trace(c,"turn-stop");return;
        }
        b_frame(c,f%60U==0U?QOL_KEY_B:0U);
    }
    br_trace(c,"turn-timeout");bp_require(c,false,"return turn reached unchanged 18000-frame bound");
}

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
    uint64_t scores[6]={0U},planned_scores[3]={0U};unsigned used=0U,planned[3],capable[6]={0U};uint32_t covered=0U;
    bp_require(c,table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus sustain move table");
    for(unsigned i=0;i<6U;++i){
        uint32_t mon=QOL_PLAYER_PARTY+100U*i;unsigned utility=0U;
        for(unsigned j=0;j<4U;++j){unsigned move=read16(c,mon+0x2CU+2U*j);
            if(read8(c,mon+0x34U+j) && (move==92U || move==73U))utility=1U;
            if(move==269U && read8(c,mon+0x34U+j))capable[i]=1U;}
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,mon+0x2CU+2U*j),pp=read8(c,mon+0x34U+j);
            bp_require(c,move<=1062U,"Circus sustain rental move");if(!move || !pp)continue;
            uint32_t row=table+12U*move;unsigned power=read8(c,row+1U),accuracy=read8(c,row+3U),split=read8(c,row+10U),type=read8(c,row+2U);
            bp_require(c,split<=2U && type<=24U && accuracy<=100U,"Circus sustain move fields");
            if(!power || split==2U)continue;
            types[i]|=1U<<type;
            uint64_t value=su_bulk_score(power,accuracy,read16(c,mon+(split?0x60U:0x5AU)),
                read16(c,mon+0x58U),read16(c,mon+0x5CU),read16(c,mon+0x62U),cv_utility(read16(c,0x0203DB20U),utility));
            if(value>scores[i])scores[i]=value;
        }
        fprintf(stderr,"CIRCUS_SUSTAIN_RENTAL slot=%u score=%llu types=%08x\n",i,(unsigned long long)scores[i],types[i]);
    }
    for(unsigned n=0;n<3U;++n){unsigned best=6U;uint64_t top=0U;
        for(unsigned i=0;i<6U;++i){uint64_t score=scores[i];
            if(!(types[i]&~covered))score/=4U;
            if(!(used&(1U<<i)) && (best==6U || score>top)){best=i;top=score;}}
        bp_require(c,best<6U && top>0U,"Circus sustain needs damaging rentals");used|=1U<<best;covered|=types[best];
        planned[n]=best;planned_scores[n]=top;
    }
    unsigned lead=ta_lead(read16(c,0x0203DB20U),planned,capable);
    bp_require(c,lead<3U,"Circus Taunt selection permutation");
    unsigned order[3],j=0U;order[j++]=lead;
    for(unsigned i=0;i<3U;++i)if(i!=lead)order[j++]=i;
    for(unsigned n=0;n<3U;++n){unsigned k=order[n],best=planned[k];
        fprintf(stderr,"CIRCUS_SUSTAIN_TEAM index=%u original_slot=%u score=%llu\n",n,best,(unsigned long long)planned_scores[k]);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}
#ifdef wx_team
#undef wx_team
#endif
#define wx_team su_team
#endif
#endif

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

#ifndef VEGA_CIRCUS_PIVOT_POLICY_H
#define VEGA_CIRCUS_PIVOT_POLICY_H
/* 入力controllerのみ。第3戦の先発を通常PARTYコマンドで温存する。 */
static unsigned pv_allowed(unsigned streak,unsigned done,unsigned own_type1,unsigned own_type2,
    unsigned enemy_type1,unsigned enemy_type2)
{
    return streak==2U && !done && own_type1!=0U && own_type2!=0U
        && enemy_type1==0U && enemy_type2==0U;
}
#ifndef CIRCUS_PIVOT_HOST_TEST
static unsigned pv_done;
static unsigned pv_move_slot(struct mCore *c)
{
    uint32_t mon=ADDR_BATTLE_MONS,foe=mon+BATTLE_MON_SIZE;
    if(pv_allowed((read16(c,0x0203DB20U)%3U),pv_done,read8(c,mon+BATTLE_CORE_MON_TYPE1),
        read8(c,mon+BATTLE_CORE_MON_TYPE2),read8(c,foe+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE2))){
        unsigned active=read16(c,ADDR_BATTLER_PARTY_INDEXES),target=3U;
        for(unsigned i=0;i<3U;++i){
            uint32_t p=QOL_PLAYER_PARTY+100U*i;unsigned toxic=0U,shadow=0U;
            for(unsigned j=0;j<4U;++j){unsigned move=read16(c,p+0x2CU+2U*j);
                if(read8(c,p+0x34U+j)){toxic|=move==92U;shadow|=move==247U;}}
            if(i!=active && read16(c,p+0x56U)>0U && toxic && shadow){
                bp_require(c,target==3U,"Circus pivot ambiguous rental");target=i;}
        }
        bp_require(c,target<3U && n_action(c),"Circus pivot requires living Toxic/Shadow Ball rental");
        uint32_t p=QOL_PLAYER_PARTY+100U*target,pid=read32(c,p),ot=read32(c,p+4U);
        unsigned species=read16(c,p+0x20U),before=b_frames;
        fprintf(stderr,"CIRCUS_PIVOT {\"label\":\"begin\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u}\n",before,active,target,pid,ot,species);
        n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
        for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
        bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus pivot normal PARTY menu absent");
        b_frames_run(c,0U,60U);wx_cursor(c,target);g_shot("pivot-party");
        b_press(c,QOL_KEY_A,80U);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
        for(unsigned f=0;f<18000U;++f){
            if(n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
                && read16(c,mon)==species)break;
            bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus pivot ended battle unexpectedly");
            b_frame(c,f%90U==0U?QOL_KEY_B:0U);
        }
        bp_require(c,n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
            && read16(c,mon)==species && read16(c,mon+BATTLE_CORE_MON_HP)>0U
            && read8(c,mon+BATTLE_CORE_MON_TYPE1)==0U && read8(c,mon+BATTLE_CORE_MON_TYPE2)==0U,
            "Circus pivot actual selected Normal individual absent");
        pv_done=1U;g_shot("pivot-action");
        fprintf(stderr,"CIRCUS_PIVOT {\"label\":\"done\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u}\n",b_frames,active,target,pid,ot,species);
    }
    return ef_move_slot(c);
}
#endif
#endif

#ifndef VEGA_CIRCUS_MENU_IDENTITY_H
#define VEGA_CIRCUS_MENU_IDENTITY_H
#include <stdint.h>
/* メニューを開く前のslotは保持しない。開いた後の実個体から一意に再解決。 */
static inline unsigned mi_find(unsigned count,const uint32_t *pid,const uint32_t *ot,
    const uint16_t *species,uint32_t wanted_pid,uint32_t wanted_ot,unsigned wanted_species)
{
    unsigned found=3U;
    if(count!=3U || !wanted_species || wanted_species>65535U)return 3U;
    for(unsigned i=0;i<count;++i)
        if(pid[i]==wanted_pid && ot[i]==wanted_ot && species[i]==wanted_species){
            if(found!=3U)return 3U;
            found=i;
        }
    return found;
}
#endif

#ifndef VEGA_CIRCUS_MATCHUP_H
#define VEGA_CIRCUS_MATCHUP_H
#include <stdint.h>
/* 上で固定原本を展開済み。 */
/* 純粋な入力選択。施設/RNG/能力/owner/partyへhost書込みは行わない。 */
static unsigned mt_role(unsigned streak,unsigned own,unsigned foe,uint32_t status,uint32_t foe_status,unsigned hp,unsigned maxhp)
{
    if(streak!=2U)return 0U;
    if(own==12U && foe==10U)return 10U;
    if(own==10U && foe==11U)return 12U;
    if(own==0U && foe==0U && (status&0x88U) && (foe_status&0x88U)
        && (uint64_t)hp*3U<(uint64_t)maxhp*2U)return 12U;
    return 0U;
}
static unsigned mt_toxic(unsigned immune,unsigned spent,unsigned pp,uint32_t status,unsigned t1,unsigned t2)
{
    return immune && spent<4U && pp && !status && t1!=3U && t2!=3U && t1!=8U && t2!=8U;
}
struct mt_feedback {uint32_t own,foe;unsigned seen,toxic_pp,spent,last_slot,last_move,last_pp;};
static unsigned mt_spent(struct mt_feedback *m,uint32_t own,uint32_t foe,unsigned pp)
{
    if(!m->seen || own!=m->own || foe!=m->foe || pp>m->toxic_pp)
        *m=(struct mt_feedback){.own=own,.foe=foe,.seen=1U,.toxic_pp=pp};
    else if(pp<m->toxic_pp)++m->spent;
    m->toxic_pp=pp;return m->spent;
}
#ifndef CIRCUS_MATCHUP_HOST_TEST
static struct mt_feedback mt_memory;
static unsigned mt_shifts;
static unsigned mt_party_move(struct mCore *c,uint32_t p,unsigned move)
{
    for(unsigned i=0;i<4U;++i)
        if(read16(c,p+0x2CU+2U*i)==move && read8(c,p+0x34U+i))return 1U;
    return 0U;
}
static unsigned mt_shift(struct mCore *c,unsigned role)
{
    unsigned active=read16(c,ADDR_BATTLER_PARTY_INDEXES),target=3U;
    for(unsigned i=0;i<3U;++i){uint32_t p=QOL_PLAYER_PARTY+100U*i;
        if(i!=active && read16(c,p+0x56U) && mt_party_move(c,p,role==10U?53U:202U)){
            bp_require(c,target==3U,"Circus matchup ambiguous reserve");target=i;}}
    if(target==3U)return 0U;
    bp_require(c,mt_shifts<6U && n_action(c),"Circus matchup switch bound");
    uint32_t p=QOL_PLAYER_PARTY+100U*target,pid=read32(c,p),ot=read32(c,p+4U),mon=ADDR_BATTLE_MONS;
    unsigned species=read16(c,p+0x20U);
    fprintf(stderr,"CIRCUS_MATCHUP {\"label\":\"begin\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u,\"type\":%u}\n",b_frames,active,target,pid,ot,species,role);
    n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
    for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus matchup normal party menu absent");
    b_frames_run(c,0U,60U);
    /* メニュー表示時のparty並替えに追従。battle前slotをUIへ流用しない。 */
    uint32_t menu_pid[3],menu_ot[3];uint16_t menu_species[3];
    for(unsigned i=0;i<3U;++i){uint32_t q=QOL_PLAYER_PARTY+100U*i;
        menu_pid[i]=read32(c,q);menu_ot[i]=read32(c,q+4U);menu_species[i]=read16(c,q+0x20U);}
    unsigned menu_slot=mi_find(read8(c,QOL_PLAYER_PARTY_COUNT),menu_pid,menu_ot,menu_species,pid,ot,species);
    bp_require(c,menu_slot<3U,"Circus menu selected individual absent or ambiguous");
    fprintf(stderr,"CIRCUS_MENU frame=%u requested=%u resolved=%u pid=%u ot=%u species=%u\n",b_frames,target,menu_slot,pid,ot,species);
    wx_cursor(c,menu_slot);
    char shot[64];snprintf(shot,sizeof(shot),"matchup-%u-party",mt_shifts+1U);g_shot(shot);
    b_press(c,QOL_KEY_A,80U);
    if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        if(n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot && read16(c,mon)==species)break;
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus matchup switch ended unexpectedly");
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,n_action(c) && read32(c,mon+0x48U)==pid && read32(c,mon+0x54U)==ot
        && read16(c,mon)==species && read16(c,mon+BATTLE_CORE_MON_HP)>0U
        && read8(c,mon+BATTLE_CORE_MON_TYPE1)==role && read8(c,mon+BATTLE_CORE_MON_TYPE2)==role,
        "Circus matchup actual selected individual/type absent");
    ++mt_shifts;snprintf(shot,sizeof(shot),"matchup-%u-action",mt_shifts);g_shot(shot);
    fprintf(stderr,"CIRCUS_MATCHUP {\"label\":\"done\",\"frame\":%u,\"from\":%u,\"target\":%u,\"pid\":%u,\"ot\":%u,\"species\":%u,\"type\":%u}\n",b_frames,active,target,pid,ot,species,role);
    return 1U;
}
static unsigned mt_move_slot(struct mCore *c)
{
    uint32_t mon=ADDR_BATTLE_MONS,foe=mon+BATTLE_MON_SIZE;
    unsigned streak=(read16(c,0x0203DB20U)%3U);
    if(streak==2U && mt_memory.seen && mt_memory.own==read32(c,mon+0x48U)
        && mt_memory.foe==read32(c,foe+0x48U) && mt_memory.last_move==73U
        && read8(c,mon+BATTLE_MON_PP_OFFSET+mt_memory.last_slot)==mt_memory.last_pp)
        su_memory.seed=0U; /* 混乱等でPP未消費ならSeed試行として数えない。 */
    unsigned selected=pv_move_slot(c);
    if(streak!=2U)return selected;
    unsigned role=mt_role(streak,read8(c,mon+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE1),
        read32(c,mon+BATTLE_CORE_MON_STATUS1),read32(c,foe+BATTLE_CORE_MON_STATUS1),
        read16(c,mon+BATTLE_CORE_MON_HP),read16(c,mon+0x2CU));
    if(role && mt_shift(c,role))selected=pv_move_slot(c);
    unsigned toxic=4U,drain=4U,damaging=0U,effective=0U;
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*i),pp=read8(c,mon+BATTLE_MON_PP_OFFSET+i);
        if(!move || !pp)continue;
        if(move==92U)toxic=i;
        if(move==202U)drain=i;
        uint32_t row=table+12U*move;
        if(read8(c,row+1U)>0U && read8(c,row+10U)<2U){
            ++damaging;unsigned type=read8(c,row+2U);
            if(wx_effect(type,t1) && wx_effect(type,t2))++effective;
        }
    }
    unsigned pp=toxic<4U?read8(c,mon+BATTLE_MON_PP_OFFSET+toxic):0U;
    unsigned spent=mt_spent(&mt_memory,read32(c,mon+0x48U),read32(c,foe+0x48U),pp),old=selected;
    if(mt_toxic(damaging && !effective,spent,pp,read32(c,foe+BATTLE_CORE_MON_STATUS1),t1,t2))selected=toxic;
    if(drain<4U && read8(c,mon+BATTLE_CORE_MON_TYPE1)==12U && t1==11U && t2==11U)selected=drain;
    unsigned before=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*old),move=read16(c,mon+BATTLE_MON_MOVES_OFFSET+2U*selected);
    if(selected!=old){
        if(before==92U && su_memory.toxic)--su_memory.toxic;
        if(before==73U && su_memory.seed)--su_memory.seed;
        if(before==109U && su_memory.confuse)--su_memory.confuse;
        if(before==347U && su_memory.setup)--su_memory.setup;
        su_memory.last=move;
    }
    mt_memory.last_slot=selected;mt_memory.last_move=move;mt_memory.last_pp=read8(c,mon+BATTLE_MON_PP_OFFSET+selected);
    fprintf(stderr,"CIRCUS_MATCHUP_MOVE frame=%u old=%u actual=%u move=%u toxic_paid=%u toxic_pp=%u shifts=%u\n",b_frames,old,selected,move,spent,pp,mt_shifts);
    return selected;
}
#endif
#endif

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
/* 上で固定原本を展開済み。 */
static unsigned cd_move_slot(struct mCore *c)
{
    unsigned selected=mt_move_slot(c);
    if((read16(c,0x0203DB20U)%3U)!=2U)return selected;
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
    if((read16(c,0x0203DB20U)%3U)!=2U)return selected;
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

/* controllerの履歴だけを再入場境界で消去する。game ownerやRNGは触らない。 */
static void cp_policy_reset(void){
    su_memory=(struct su_memory){0};mt_memory=(struct mt_feedback){0};pv_done=0U;mt_shifts=0U;
}

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
    tp_consider(c);
    unsigned streak=read16(c,0x0203DB20U),selected=streak<3U?fp_move_slot(c):wx_move_slot(c);
    if(streak<3U)return selected; /* 受入prefix3戦の入力は完全に維持。 */
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
    uint64_t scores[4]={0};unsigned reliability[4]={0};unsigned t1=read8(c,foe+BATTLE_CORE_MON_TYPE1),t2=read8(c,foe+BATTLE_CORE_MON_TYPE2);
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
        reliability[i]=accuracy?accuracy:100U;
        scores[i]=score*wx_effect(type,t1)*(t1==t2?10U:wx_effect(type,t2))/100U;
    }
    unsigned actual=rr_pick(selected,rr_memory.blocked,scores);
    if(streak>=8U)actual=rl_pick(actual,rr_memory.blocked,scores,reliability);
    actual=ta_move(c,actual);
    bp_require(c,actual<4U,"Circus reentry selected slot");
    unsigned move=read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*actual);
    rr_memory.slot=actual;rr_memory.pp=read8(c,own+BATTLE_MON_PP_OFFSET+actual);rr_memory.hp=hp;
    rr_memory.damaging=read8(c,table+12U*move+1U)>0U && read8(c,table+12U*move+10U)<2U;
    if(actual!=selected){su_memory.last=move;mt_memory.last_slot=actual;mt_memory.last_move=move;mt_memory.last_pp=rr_memory.pp;}
    fprintf(stderr,"CIRCUS_REENTRY frame=%u streak=%u selected=%u actual=%u move=%u blocked=%u pp=%u foe_hp=%u\n",
        b_frames,streak,selected,actual,move,rr_memory.blocked,rr_memory.pp,hp);
    if(streak>=8U){
        fprintf(stderr,"CIRCUS_RELIABILITY frame=%u streak=%u selected=%u actual=%u blocked=%u accuracy=%u score=%llu own=",b_frames,streak,selected,actual,rr_memory.blocked,reliability[actual],(unsigned long long)scores[actual]);
        for(unsigned i=0;i<BATTLE_MON_SIZE;++i)fprintf(stderr,"%02x",read8(c,own+i));
        fprintf(stderr," foe=");for(unsigned i=0;i<BATTLE_MON_SIZE;++i)fprintf(stderr,"%02x",read8(c,foe+i));
        fprintf(stderr,"\n");
    }
    return actual;
}
#endif
#endif

#ifndef VEGA_CIRCUS_TACTICAL_H
#define VEGA_CIRCUS_TACTICAL_H
#include <stdint.h>
/* 16戦目の毒/混乱＋Ghost攻撃と、その後の炎対面から限定追加した通常交代。
 * species/RNG/勝敗は使わない。場のtypeと技種を読み、控えの使用可能技から選ぶ。
 * 技typeから控えの種族typeを断定しない。交代後の実個体/typeも別に記録する。 */
static unsigned tp_request(unsigned streak,unsigned own1,unsigned own2,
    unsigned foe1,unsigned foe2,uint32_t attacks)
{
    if(streak<15U)return 25U;
    unsigned target=25U;
    if(foe1==10U && foe2==10U)target=11U;
    else if(foe1==11U && foe2==11U)target=12U;
    else if(foe1==12U && foe2==12U)target=10U;
    else if(attacks==(1U<<7U))target=17U;
    return own1==target || own2==target?25U:target;
}
static uint64_t tp_rank(unsigned power,unsigned accuracy,unsigned attack,
    unsigned hp,unsigned maxhp)
{
    if(!power || !hp || !maxhp || hp>maxhp || accuracy>100U)return 0U;
    return (uint64_t)power*(accuracy?accuracy:100U)*attack*hp/maxhp;
}
#ifndef CIRCUS_TACTICAL_HOST_TEST
static unsigned tp_streak=65535U,tp_switches,tp_seen;
static uint32_t tp_foe,tp_foe_ot;
static void tp_consider(struct mCore *c)
{
    unsigned streak=read16(c,0x0203DB20U);if(streak<15U)return;
    uint32_t own=ADDR_BATTLE_MONS,foe=own+BATTLE_MON_SIZE,table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    bp_require(c,n_action(c) && table>=0x08000000U && table+1063U*12U<=0x0A000000U && !(table&3U),"Circus tactical action/table boundary");
    uint32_t pid=read32(c,foe+0x48U),ot=read32(c,foe+0x54U),attacks=0U;
    if(tp_streak!=streak){tp_streak=streak;tp_switches=tp_seen=0U;}
    if(tp_seen && pid==tp_foe && ot==tp_foe_ot)return;
    if(tp_switches>=6U)return;
    for(unsigned i=0;i<4U;++i){
        unsigned move=read16(c,foe+BATTLE_MON_MOVES_OFFSET+2U*i);
        bp_require(c,move<=1062U,"Circus tactical foe move ABI");
        if(!move || !read8(c,foe+BATTLE_MON_PP_OFFSET+i))continue;
        uint32_t row=table+12U*move;unsigned type=read8(c,row+2U);
        bp_require(c,type<=24U,"Circus tactical foe type ABI");
        if(read8(c,row+1U) && read8(c,row+10U)<2U)attacks|=1U<<type;
    }
    unsigned wanted=tp_request(streak,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,own+BATTLE_CORE_MON_TYPE2),
        read8(c,foe+BATTLE_CORE_MON_TYPE1),read8(c,foe+BATTLE_CORE_MON_TYPE2),attacks);
    if(wanted==25U)return;
    uint32_t active=read32(c,own+0x48U),active_ot=read32(c,own+0x54U);
    unsigned target=3U;uint64_t best=0U;
    for(unsigned i=0;i<3U;++i){
        uint32_t p=QOL_PLAYER_PARTY+100U*i;
        if(read32(c,p)==active && read32(c,p+4U)==active_ot)continue;
        for(unsigned j=0;j<4U;++j){
            unsigned move=read16(c,p+0x2CU+2U*j);
            bp_require(c,move<=1062U,"Circus tactical reserve move ABI");
            if(!move || !read8(c,p+0x34U+j))continue;
            uint32_t row=table+12U*move;unsigned split=read8(c,row+10U);
            if(split>1U || read8(c,row+2U)!=wanted)continue;
            uint64_t score=tp_rank(read8(c,row+1U),read8(c,row+3U),read16(c,p+(split?0x60U:0x5AU)),
                read16(c,p+0x56U),read16(c,p+0x58U));
            if(score>best){best=score;target=i;}
        }
    }
    if(target==3U)return;
    uint32_t p=QOL_PLAYER_PARTY+100U*target,target_pid=read32(c,p),target_ot=read32(c,p+4U);
    unsigned species=read16(c,p+0x20U);
    tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;++tp_switches;
    fprintf(stderr,"CIRCUS_TACTICAL begin frame=%u streak=%u foe=%u foe_ot=%u target_pid=%u target_ot=%u species=%u attack_type=%u count=%u\n",b_frames,streak,pid,ot,target_pid,target_ot,species,wanted,tp_switches);
    n_cursor(c,2U);b_press(c,QOL_KEY_A,120U);
    for(unsigned f=0;f<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++f)b_frame(c,0U);
    bp_require(c,read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"Circus tactical normal party menu absent");
    b_frames_run(c,0U,60U);
    uint32_t menu_pid[3],menu_ot[3];uint16_t menu_species[3];
    for(unsigned i=0;i<3U;++i){uint32_t q=QOL_PLAYER_PARTY+100U*i;
        menu_pid[i]=read32(c,q);menu_ot[i]=read32(c,q+4U);menu_species[i]=read16(c,q+0x20U);}
    unsigned slot=mi_find(read8(c,QOL_PLAYER_PARTY_COUNT),menu_pid,menu_ot,menu_species,target_pid,target_ot,species);
    bp_require(c,slot<3U,"Circus tactical menu individual absent/ambiguous");wx_cursor(c,slot);
    b_press(c,QOL_KEY_A,80U);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY)b_press(c,QOL_KEY_A,80U);
    for(unsigned f=0;f<18000U;++f){
        if(n_action(c) && read32(c,own+0x48U)==target_pid && read32(c,own+0x54U)==target_ot && read16(c,own)==species)break;
        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus tactical switch ended unexpectedly");
        b_frame(c,f%90U==0U?QOL_KEY_B:0U);
    }
    bp_require(c,n_action(c) && read32(c,own+0x48U)==target_pid && read32(c,own+0x54U)==target_ot
        && read16(c,own)==species && read16(c,own+BATTLE_CORE_MON_HP),"Circus tactical selected individual did not survive to action");
    fprintf(stderr,"CIRCUS_TACTICAL done frame=%u streak=%u foe=%u foe_ot=%u target_pid=%u target_ot=%u species=%u attack_type=%u count=%u types=%u,%u\n",b_frames,streak,pid,ot,target_pid,target_ot,species,wanted,tp_switches,read8(c,own+BATTLE_CORE_MON_TYPE1),read8(c,own+BATTLE_CORE_MON_TYPE2));
}
#endif
#endif

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

/* native完了を読むだけ。勝数/CPU/register/inputには書き込まない。 */
static unsigned dw_seen;
static void wr_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(dw_seen || read16(c,0x0203DB20U)!=16U || read8(c,BATTLE_CORE_BATTLE_OUTCOME)!=1U
       || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U || read8(c,0x02038538U)!=12U
       || read8(c,0x0203853AU)!=1U || read8(c,0x020385B5U)!=32U || read8(c,0x020385B6U)!=32U)return;
    ++dw_seen;
    fprintf(stderr,"CIRCUS_DROUGHT_RETURN {\"frame\":%u,\"state\":%u,\"complete\":%u,\"index\":%u,\"offset\":%u,\"brightness\":%u,\"current\":%u,\"outcome\":%u,\"script\":%u}\n",
        b_frames,read16(c,0x02038534U),read8(c,0x0203853AU),read8(c,0x020385B5U),read8(c,0x020385B6U),
        read16(c,0x020385A4U),read16(c,0x0203DB20U),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,SP_SCRIPT_PTR));
}

/* フェード修復前後を読み取るだけ。既存入力列を変更しない。 */
static uint32_t fw_previous[5];
static unsigned fw_seen,fw_rows;
static void fw_frame(struct mCore *c,uint32_t keys){
    wr_frame(c,keys);
    if((read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU)!=2U)return;
    uint32_t now[5]={read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read8(c,0x02038530U),read8(c,0x0203852EU),read8(c,0x0203DB24U)};
    if(fw_seen && !memcmp(now,fw_previous,sizeof(now)))return;
    bp_require(c,fw_rows++<64U,"weather trace bound");fw_seen=1;memcpy(fw_previous,now,sizeof(now));
    fprintf(stderr,"CIRCUS_WEATHER {\"frame\":%u,\"callback2\":%u,\"script\":%u,\"ready\":%u,\"palette_state\":%u,\"owner_phase\":%u}\n",
        b_frames,now[0],now[1],now[2],now[3],now[4]);
}
#define b_frame fw_frame

/* 元party人数と選出人数を同時に読む。入力・ledger・CPUには書き込まない。 */
static unsigned lb_seen;
static void lb_frame(struct mCore *c,uint32_t keys)
{
    b_frame(c,keys);
    if(lb_seen || read16(c,0x0203DB20U)!=17U || read8(c,0x0203DB24U)!=2U
       || read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x08055E75U || read32(c,SP_SCRIPT_PTR)!=0x09FF4DADU
       || read8(c,0x02038538U)!=12U || read8(c,0x02038530U)!=1U)return;
    lb_seen=1U;
    fprintf(stderr,"CIRCUS_SELECTION_CONTEXT {\"frame\":%u,\"saved_count\":%u,\"selected_count\":%u,\"marker\":%u,\"snapshot\":%u,\"outcome\":%u,\"script\":%u,\"current\":%u,\"phase\":%u}\n",
        b_frames,read8(c,BP_F(party_count)),read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(marker)),
        read8(c,BP_F(snapshot_valid)),read8(c,BATTLE_CORE_BATTLE_OUTCOME),read32(c,SP_SCRIPT_PTR),
        read16(c,0x0203DB20U),read8(c,0x0203DB24U));
}
#undef b_frame
#define b_frame lb_frame

/* 保存済み100events後のREADY/6体/Drought境界だけを観測。ゲーム状態へ書かない。 */
static unsigned rd_started, rd_elapsed, rd_transition, rd_done;
static void rd_emit(struct mCore *c, const char *label, uint32_t keys)
{
    fprintf(stderr,"CIRCUS_RENTAL_DROUGHT {\"label\":\"%s\",\"elapsed\":%u,\"frame\":%u,\"events\":%u,\"keys\":%u,\"current\":%u,\"phase\":%u,\"count\":%u,\"saved_count\":%u,\"marker\":%u,\"snapshot\":%u,\"callback2\":%u,\"script\":%u,\"newbs\":%u,\"outcome\":%u,\"state\":%u,\"complete\":%u,\"index\":%u,\"offset\":%u}\n",
        label,rd_elapsed,b_frames,sc_events,keys,read16(c,0x0203DB20U),read8(c,0x0203DB24U),
        read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,BP_F(party_count)),read8(c,BP_F(marker)),
        read8(c,BP_F(snapshot_valid)),read32(c,BATTLE_CORE_MAIN_CALLBACK2),read32(c,SP_SCRIPT_PTR),
        read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),read8(c,BATTLE_CORE_BATTLE_OUTCOME),
        read8(c,0x02038534U),read8(c,0x0203853AU),read8(c,0x020385B5U),read8(c,0x020385B6U));
}
static int rd_exact_entry(struct mCore *c)
{
    return sc_events==100U && read16(c,0x0203DB20U)==21U && read8(c,0x0203DB24U)==1U
        && read8(c,QOL_PLAYER_PARTY_COUNT)==6U && read8(c,BP_F(party_count))>=1U
        && read8(c,BP_F(party_count))<=6U && read8(c,BP_F(marker))==1U
        && read8(c,BP_F(snapshot_valid))==1U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08055E75U
        && read32(c,SP_SCRIPT_PTR)==0x09FF4CB5U && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)==0U;
}
static void rd_frame(struct mCore *c,uint32_t keys)
{
    /* underlying frameを進める前に、event100直後の一瞬の境界を採取する。 */
    if(!rd_done && !rd_started && rd_exact_entry(c)){
        rd_started=1U;rd_emit(c,"entered",keys);
    }
    b_frame(c,keys);
    if(rd_done)return;
    if(!rd_started){
        /* 修復が1frame内でevent101へ直行しても、accepted prefix照合後なら見失わない。 */
        if(sc_events>100U){rd_started=1U;rd_elapsed=1U;rd_emit(c,"event-crossed-direct",keys);rd_done=1U;}
        return;
    }
    ++rd_elapsed;
    if(!rd_transition && (read8(c,0x02038534U)==5U || read8(c,0x0203853AU)==1U
       || read8(c,0x020385B5U)==32U || read8(c,0x020385B6U)==32U
       || read32(c,SP_SCRIPT_PTR)!=0x09FF4CB5U)){
        rd_transition=1U;rd_emit(c,"weather-returned",keys);
    }
    if(sc_events>100U){rd_emit(c,"event-crossed",keys);rd_done=1U;return;}
    if(rd_elapsed==600U){rd_emit(c,"bounded-stop",keys);g_shot("rental-drought-bounded-stop");bp_require(c,false,"rental Drought boundary did not advance");}
}
#undef b_frame
#define b_frame rd_frame
