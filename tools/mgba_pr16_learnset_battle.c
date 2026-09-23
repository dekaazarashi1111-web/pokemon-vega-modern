/* Issue19: saved physical-learning witness -> explicit initial party fixture ->
 * natural walking encounter -> learned move -> ordinary Save/fresh Continue.
 * No target, RNG, HP/PP, battle function or outcome injection while observed. */
#include "pr16_gameplay_driver.c"
#include "pr16_learnset_battle_fixture.h"
static unsigned lb_steps,lb_frames,lb_spent,lb_damage,lb_chosen,lb_outcome;
static unsigned lb_before_pp,lb_after_pp,lb_enemy_hp,lb_min_hp;
static bool lb_observe;
static void lb_frame(struct mCore *c,unsigned key) {
    c->setKeys(c,key);c->runFrame(c);++lb_frames;
    if(lb_observe && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)) {
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+1U);
        unsigned hp=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP);
        unsigned current=read16(c,0x02023CAAU),chosen=read16(c,BATTLE_CORE_CHOSEN_MOVES);
        if(chosen==420U && !lb_chosen)lb_chosen=lb_frames;
        if(pp<lb_before_pp && !lb_spent){lb_spent=lb_frames;lb_after_pp=pp;}
        if(current==420U && hp<lb_min_hp){lb_min_hp=hp;if(!lb_damage)lb_damage=lb_frames;}
    }
}
static void lb_wait(struct mCore *c,unsigned n){for(unsigned i=0;i<n;++i)lb_frame(c,0);}
static void lb_press(struct mCore *c,unsigned key,unsigned n){lb_frame(c,key);lb_wait(c,n);}
static unsigned lb_save1(struct mCore *c){unsigned p=read32(c,QOL_SAVE_BLOCK1_SLOT);a_require(p02s_ewram_pointer(p),"battle save block");return p;}
static bool lb_field(struct mCore *c) {
    unsigned id=read8(c,P02S_PLAYER_AVATAR+5);
    return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD && read8(c,P02S_FIELD_LOCK)==0
        && !read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE) && id<16
        && (read8(c,P02S_OBJECT_EVENTS+id*0x24)&1U)
        && !read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET)
        && !read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET);
}
static bool lb_action(struct mCore *c) {
    unsigned ctrl=read32(c,0x03005020U);
    return read32(c,0x03004FC4U)==0x08013861U && (read32(c,0x02023B28U)&1U)
        && read8(c,0x02022B24U)==0x12U && (ctrl==0x0802DC15U || ctrl==0x09118B85U);
}
static void lb_wait_action(struct mCore *c) {
    for(unsigned i=0;i<12000U;++i){if(lb_action(c)){c->setKeys(c,0);return;}lb_frame(c,i%60U==0?QOL_KEY_A:0);}
    a_die("natural learned-move action controller timeout");
}
static void lb_position(struct mCore *c,unsigned group,unsigned map,unsigned x,unsigned y) {
    unsigned s=lb_save1(c);
    a_require(read8(c,s+4)==group && read8(c,s+5)==map && read16(c,s)==x && read16(c,s+2)==y,"learned-move physical position differs");
}
static void lb_step(struct mCore *c,unsigned key) {
    a_require(lb_field(c),"walking outside field");unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);bool moved=false;
    for(unsigned i=0;i<90;++i){lb_frame(c,key);s=lb_save1(c);if(read16(c,s)!=x || read16(c,s+2)!=y){moved=true;break;}}
    c->setKeys(c,0);a_require(moved,"learned-move walk blocked");++lb_steps;unsigned stable=0;
    for(unsigned i=0;i<12000;++i){
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){lb_wait_action(c);return;}
        if(lb_field(c)){if(++stable==12)return;}else stable=0;
        lb_frame(c,0);
    }
    a_die("learned-move walking timeout");
}
static void lb_path(struct mCore *c,unsigned map,const unsigned path[][2],unsigned count,bool grass) {
    for(unsigned i=0;i<count;++i){
        unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2),tx=path[i][0],ty=path[i][1];
        lb_position(c,96,map,x,y);
        a_require((x==tx && (y+1==ty || ty+1==y)) || (y==ty && (x+1==tx || tx+1==x)),"nonadjacent path");
        lb_step(c,x<tx?QOL_KEY_RIGHT:x>tx?QOL_KEY_LEFT:y<ty?QOL_KEY_DOWN:QOL_KEY_UP);
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(grass,"unexpected town encounter");return;}
        lb_position(c,96,map,tx,ty);
    }
}
static void lb_cursor(struct mCore *c,unsigned address,unsigned target) {
    for(unsigned i=0;i<6;++i){unsigned at=read8(c,address);a_require(at<4,"battle cursor invalid");if(at==target)return;
        lb_press(c,(at&1)!=(target&1)?((target&1)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((target&2)?QOL_KEY_DOWN:QOL_KEY_UP),12);}
    a_die("battle cursor did not follow physical input");
}
static void lb_return(struct mCore *c) {
    unsigned stable=0;
    for(unsigned i=0;i<24000;++i){
        unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(outcome)lb_outcome=outcome;
        if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable==30){c->setKeys(c,0);return;}}else stable=0;
        if(lb_action(c)){lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,3);lb_press(c,QOL_KEY_A,60);continue;}
        lb_frame(c,i%60==0?QOL_KEY_B:0);
    }
    a_die("learned-move battle did not return");
}
static unsigned lb_resume_x,lb_resume_y;
static bool lb_resume_position(struct mCore *c) {
    unsigned s=lb_save1(c);
    return read8(c,s+4)==96 && read8(c,s+5)==17 && read16(c,s)==lb_resume_x && read16(c,s+2)==lb_resume_y;
}
static bool lb_normal_continue(struct mCore*c) {
    run_key_frames(c,0,P02S_TITLE_FRAMES);
    for(unsigned p=0;p<P02S_CONTINUE_PULSES;p++) {
        qol_press(c,p==0?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD || !lb_resume_position(c))continue;
        run_key_frames(c,0,300);
        for(unsigned r=0;r<8;r++) {
            if(!read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) {
                run_key_frames(c,0,P02S_FIELD_SETTLE_FRAMES);unsigned stable=0;
                for(unsigned f=0;f<3600;f++) {
                    if(lb_field(c)){if(++stable>=P02S_INPUT_READY_FRAMES)return true;}else stable=0;
                    run_key_frames(c,0,1);
                }
            }
            qol_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);
        }
        return false;
    }
    return false;
}
static bool lb_normal_save(struct mCore*c) {
    unsigned counter=read32(c,P03_SAVE_COUNTER);qol_press(c,QOL_KEY_START,120);
    if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;
    if(!count || count>9 || cursor>=count)return false;
    for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==P03_SAVE_ACTION)target=i;
    if(target==count)return false;
    for(unsigned i=0,n=(target+count-cursor)%count;i<n;i++)qol_press(c,QOL_KEY_DOWN,30);
    if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;
    qol_press(c,QOL_KEY_A,120);bool seen=false;
    for(unsigned i=0;i<32;i++) {
        unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==P03_SAVE_CALLBACK)seen=true;
        if(seen && cb==P03_SAVE_CALLBACK && read32(c,P03_SAVE_COUNTER)==counter+1 && lb_field(c)) {
            run_key_frames(c,0,180);return lb_field(c);
        }
        qol_press(c,QOL_KEY_A,180);
    }
    return false;
}
int main(int argc,char **argv) {
    if(argc!=7 || strcmp(argv[5],"floette-learned-420-natural-battle"))return 2;
    a_require(!strcmp(projectVersion,"0.10.2"),"battle mGBA version");
    g_prefix=argv[6];char rh[65],sh[65],after[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(rh,LB_ROM_SHA) && !strcmp(sh,argv[4]) && !strcmp(sh,LB_SEED_SHA),"battle fixed input hashes");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t pixels[240*160];g_video=pixels;
    c->setVideoBuffer(c,pixels,240);c->reset(c);a_require(a_continue(c),"battle initial Continue");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"battle initial field fixture");p02s_enable_national_dex(c);
    clear_parties(c);for(unsigned i=0;i<100;++i)write8(c,QOL_PLAYER_PARTY+i,lb_fixture_party[i]);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    (void)call_preserving(c,QOL_FLAG_SET,A_HOF,0,0,0);a_key_item(c);
    const struct GCase *v=G_CASES+LB_SOURCE_CASE;
    a_require(v->species==1029 && v->expected==420 && v->slot==1 && v->after[1]==420,"accepted learning vector");
    a_slots(c,1029,v->level,v->after,v->after_pp);lb_before_pp=lb_after_pp=v->after_pp[1];
    unsigned char party[100],again[100];g_party(c,party,"battle_fixture");a_require(!memcmp(party,lb_fixture_party,100),"accepted party bytes");
    lb_position(c,96,5,20,20);g_shot("battle-fixture");
    struct mCore saved=*c;a_guard(c); /* No host writes/calls through walking and battle. */
    lb_path(c,5,lb_town_path,sizeof(lb_town_path)/sizeof(*lb_town_path),false);
    lb_step(c,QOL_KEY_UP);lb_position(c,96,17,11,39);unsigned boundary=lb_frames;
    lb_path(c,17,lb_grass_path,sizeof(lb_grass_path)/sizeof(*lb_grass_path),true);
    for(unsigned i=0;i<128 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){
        unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);a_require(y==30 && (x==14 || x==15),"audited grass pair");
        lb_step(c,x==14?QOL_KEY_RIGHT:QOL_KEY_LEFT);
    }
    a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==0 && read16(c,ADDR_BATTLE_MONS)==1029
        && read16(c,ADDR_BATTLER_PARTY_INDEXES)==0 && read32(c,ADDR_BATTLE_MONS+0x48)==read32(c,QOL_PLAYER_PARTY),"natural nonfacility learned battler");
    unsigned encounter=lb_frames,enemy=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE);
    for(unsigned i=0;i<4;++i)a_require(read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2*i)==v->after[i]
        && read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+i)==v->after_pp[i],"learned moves/PP did not enter native battler");
    lb_enemy_hp=lb_min_hp=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP);a_require(lb_enemy_hp>0,"natural enemy HP");
    g_shot("natural-battle");lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,60);
    a_require(read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U),"physical move menu missing");
    lb_cursor(c,BATTLE_CORE_MOVE_SELECTION_CURSOR,1);g_shot("learned-move-selected");unsigned selection=lb_frames;
    lb_observe=true;lb_press(c,QOL_KEY_A,2);
    for(unsigned i=0;i<18000;++i){
        if(lb_spent && (lb_action(c) || (!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c))))break;
        lb_frame(c,i%60==0?QOL_KEY_B:0);
    }
    a_require(lb_chosen && lb_spent && lb_damage && lb_min_hp<lb_enemy_hp && lb_after_pp<lb_before_pp
        && lb_before_pp-lb_after_pp<=2,"learned move chosen/PP/damage witness absent");
    lb_observe=false;g_shot("learned-native-turn");lb_return(c);unsigned returned=lb_frames;
    a_require(lb_outcome==1 || lb_outcome==4,"normal battle outcome");a_restore(c,&saved);
    unsigned pp[4];memcpy(pp,v->after_pp,sizeof(pp));pp[1]=lb_after_pp;
    a_slots(c,1029,v->level,v->after,pp);
    for(unsigned i=0;i<8;++i)a_require(read8(c,QOL_PLAYER_PARTY+i)==party[i],"individual changed in battle");
    g_party(c,party,"battle_returned");g_shot("battle-field");
    lb_resume_x=read16(c,lb_save1(c));lb_resume_y=read16(c,lb_save1(c)+2);
    /* Generic-field Save uses the reviewed menu driver, not a fixed map check. */
    a_guard(c);a_require(lb_normal_save(c),"battle normal Save failed");a_restore(c,&saved);
    g_party(c,again,"battle_saved");a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3,"battle save bytes");
    g_shot("battle-saved");qol_close(c);qol_log_core=NULL;
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,pixels,240);c->reset(c);saved=*c;
    a_guard(c);a_require(lb_normal_continue(c),"battle fresh Continue failed");a_restore(c,&saved);
    a_slots(c,1029,v->level,v->after,pp);g_party(c,again,"battle_continued");
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER),"battle fresh persistence");
    g_shot("battle-continued");qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(rh,after) && !log_problem_count,"battle ROM/log change");
    printf("{\"status\":\"PASS\",\"scope\":\"LEARNED_PARTY_FIXTURE_NATURAL_BATTLE_SAVE_CONTINUE\",\"candidate_sha256\":\"%s\",\"species\":1029,\"move\":420,\"slot\":1,\"enemy_species\":%u,\"walking_steps\":%u,\"boundary\":%u,\"encounter\":%u,\"selection\":%u,\"chosen\":%u,\"pp_spent\":%u,\"damage\":%u,\"returned\":%u,\"pp_before\":%u,\"pp_after\":%u,\"enemy_hp_before\":%u,\"enemy_hp_min\":%u,\"outcome\":%u,\"initial_party_fixture\":true,\"bag_reruns\":0,\"host_write_barriers\":3,\"fresh_cores\":2,\"manual_saves\":1,\"party_preserved_bytes\":100,\"warnings_errors\":0,\"story_acquisition_verified\":false,\"issue19_complete\":false,\"release_ready\":false}\n",rh,enemy,lb_steps,boundary,encounter,selection,lb_chosen,lb_spent,lb_damage,returned,lb_before_pp,lb_after_pp,lb_enemy_hp,lb_min_hp,lb_outcome);
    return 0;
}
