/* Issue19: 開始個体/EXP/戦闘能力値はfixture。観測開始後は通常キー入力のみ。
 * 自然な野生生成と戦闘EXP習得を原本表で照合し、通常Save/fresh Continue。
 * 既存のアメ/Bag/egg/ARMの受入を繰り返さない。 */
#include "pr16_progression_archive.c"
#include <mgba/core/version.h>
#include "pr16_natural_vectors.h"
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#pragma GCC diagnostic ignored "-Wunused-variable"
#include "pr16_natural_trace_walking.h"
#pragma GCC diagnostic pop
static void n_array(const unsigned a[4]) {printf("[%u,%u,%u,%u]",a[0],a[1],a[2],a[3]);}
static void n_copy(struct mCore *c,unsigned char out[100]){for(unsigned i=0;i<100;++i)out[i]=read8(c,QOL_PLAYER_PARTY+i);}
static void n_party(struct mCore *c,const char *stage,unsigned char out[100]) {
    n_copy(c,out);fprintf(stderr,"NATURAL_PARTY stage=%s counter=%u hex=",stage,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<100;++i){fprintf(stderr,"%02x",out[i]);}
    fputc('\n',stderr);
}
static void n_slots(struct mCore *c,const unsigned moves[4],const unsigned pp[4],unsigned level) {
    a_require(p02s_data(c,11)==414 && p02s_data(c,56)==level && p02s_data(c,21)==0,"natural owner/level/PP bonuses");
    for(unsigned i=0;i<4;++i){unsigned m=p02s_data(c,13+i),p=p02s_data(c,17+i);
        fprintf(stderr,"NATURAL_SLOT level=%u slot=%u move=%u pp=%u expected=%u expected_pp=%u\n",level,i,m,p,moves[i],pp[i]);
        a_require(m==moves[i] && p==pp[i],"natural party move/PP mismatch");}
}
static void n_initial(unsigned sid,unsigned level,unsigned out[4]) {
    a_require(sid<1671 && n_count[sid] && level>=1 && level<=100,"unbound natural species/level");
    unsigned eligible=0,start=n_start[sid],count=n_count[sid];
    while(eligible<count && n_rows[start+eligible][1]<=level)++eligible;
    unsigned used=0;for(unsigned i=eligible>4?eligible-4:0;i<eligible;++i){unsigned mid=n_rows[start+i][0];bool known=false;
        for(unsigned j=0;j<used;++j){if(out[j]==mid)known=true;}
        if(!known)out[used++]=mid;}
}
int main(int argc,char **argv) {
    if(argc!=5)return 2;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rh[65],sh[65],endhash[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(rh,N_ROM_SHA) && !strcmp(sh,argv[4]) && !strcmp(sh,N_SEED_SHA),"natural input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);c->reset(c);
    a_require(a_continue(c),"natural initial Continue");a_flash_prepare(c);a_require(p02s_install_field_fixture(c),"natural initial field fixture");p02s_enable_national_dex(c);
    /* 閾値は実候補の成長曲線から事前fixtureとして取得。観測中はEXP書込禁止。 */
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,414,44);unsigned threshold=p02s_data(c,25);
    create_mon(c,QOL_PLAYER_PARTY,414,43);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    unsigned floor=p02s_data(c,25);a_require(floor<threshold && threshold<2000000,"EXP fixture bounds");
    p02s_set_data(c,25,threshold-1);p02s_set_data(c,21,0);p02s_set_data(c,12,0);
    unsigned known[4]={53,89,0,0},points[4]={n_pp[53],n_pp[89],0,0};
    for(unsigned i=0;i<4;++i){p02s_set_data(c,13+i,known[i]);p02s_set_data(c,17+i,points[i]);}
    /* 開始戦闘能力値だけ強化fixture。野生/RNG/勝敗/EXP付与を操作しない。 */
    for(unsigned offset=86;offset<=98;offset+=2)write16(c,QOL_PLAYER_PARTY+offset,999);
    n_slots(c,known,points,43);a_require(p02s_data(c,25)==threshold-1,"fixture EXP");
    unsigned char before[100],party[100],again[100];n_party(c,"fixture",before);lb_position(c,96,5,20,20);
    struct mCore saved=*c;a_guard(c);
    lb_path(c,5,lb_town_path,sizeof(lb_town_path)/sizeof(*lb_town_path),false);lb_step(c,QOL_KEY_UP);lb_position(c,96,17,11,39);unsigned boundary=lb_frames;
    lb_path(c,17,lb_grass_path,sizeof(lb_grass_path)/sizeof(*lb_grass_path),true);
    for(unsigned i=0;i<128 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);
        a_require(y==30 && (x==14 || x==15),"natural grass pair");lb_step(c,x==14?QOL_KEY_RIGHT:QOL_KEY_LEFT);}
    a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==4 && read16(c,ADDR_BATTLE_MONS)==414,"ordinary wild action entry");
    unsigned encounter=lb_frames,eb=ADDR_BATTLE_MONS+BATTLE_MON_SIZE,enemy=read16(c,eb),enemy_level=read8(c,eb+0x2A);
    unsigned actual[4],enemypp[4],expected[4]={0};n_initial(enemy,enemy_level,expected);
    fprintf(stderr,"NATURAL_ENEMY species=%u level=%u frame=%u\n",enemy,enemy_level,encounter);
    for(unsigned i=0;i<4;++i){actual[i]=read16(c,eb+BATTLE_MON_MOVES_OFFSET+2*i);enemypp[i]=read8(c,eb+BATTLE_MON_PP_OFFSET+i);
        fprintf(stderr,"NATURAL_INITIAL slot=%u move=%u pp=%u expected=%u expected_pp=%u\n",i,actual[i],enemypp[i],expected[i],n_pp[expected[i]]);}
    for(unsigned i=0;i<4;++i)a_require(actual[i]==expected[i] && enemypp[i]==n_pp[expected[i]],"natural initial moves differ from locked original");
    unsigned hp_before=read16(c,eb+BATTLE_CORE_MON_HP),hp_min=hp_before,spent=0,level_frame=0,turns=0,stable=0;
    a_require(hp_before>0,"natural live enemy");
    for(unsigned f=0;f<48000;++f){
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){
            unsigned hp=read16(c,eb+BATTLE_CORE_MON_HP);if(hp<hp_min)hp_min=hp;
            if(read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET)<points[0] && !spent)spent=lb_frames;
        }
        if(read8(c,QOL_PLAYER_PARTY+84)>43 && !level_frame)level_frame=lb_frames;
        if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable>=60)break;}else stable=0;
        if(lb_action(c)){
            a_require(++turns<=8,"bounded normal battle turns");lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,60);
            a_require(read8(c,0x02022B24)==0x14 && (read32(c,0x02023B28)&1),"normal move menu");
            lb_cursor(c,BATTLE_CORE_MOVE_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,2);continue;
        }
        lb_frame(c,f%30==0?QOL_KEY_A:0);
        if(f%3000==0)fprintf(stderr,"NATURAL_PROGRESS frame=%u callback=%08x command=%u controller=%08x outcome=%u level=%u hp=%u\n",lb_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2),read8(c,0x02022B24),read32(c,0x03005020),lb_outcome,read8(c,QOL_PLAYER_PARTY+84),hp_min);
    }
    unsigned returned=lb_frames;a_require(stable>=60 && lb_outcome==1 && hp_min==0 && spent && level_frame,"natural victory/EXP/field witness");
    a_restore(c,&saved);unsigned xp=p02s_data(c,25),level=p02s_data(c,56);
    a_require(level==44 && xp>=threshold,"native EXP level threshold");
    unsigned after[4]={53,89,497,0},afterpp[4]={p02s_data(c,17),points[1],n_pp[497],0};
    a_require(afterpp[0]<points[0] && points[0]-afterpp[0]<=2*turns,"attack PP usage");n_slots(c,after,afterpp,44);
    n_party(c,"returned",party);a_require(!memcmp(before,party,8) && read32(c,P03_SAVE_COUNTER)==2,"individual/Save before normal Save");
    lb_resume_x=read16(c,lb_save1(c));lb_resume_y=read16(c,lb_save1(c)+2);
    a_guard(c);a_require(lb_normal_save(c),"natural ordinary Save");a_restore(c,&saved);n_party(c,"saved",again);
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3,"natural saved bytes");qol_close(c);qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);c->reset(c);saved=*c;
    a_guard(c);a_require(lb_normal_continue(c),"natural fresh Continue");a_restore(c,&saved);n_party(c,"continued",again);
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3 && p02s_data(c,25)==xp,"natural continued bytes/EXP");n_slots(c,after,afterpp,44);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],endhash);a_require(!strcmp(rh,endhash) && !log_problem_count,"ROM/log unchanged");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"case\":\"wild-initial-butterfree-exp-empty\",\"candidate_sha256\":\"%s\",\"enemy_species\":%u,\"enemy_level\":%u,\"enemy_moves\":",rh,enemy,enemy_level);n_array(actual);
    printf(",\"enemy_pp\":");n_array(enemypp);printf(",\"moves_after\":");n_array(after);printf(",\"pp_after\":");n_array(afterpp);
    printf(",\"xp_before\":%u,\"xp_threshold\":%u,\"xp_after\":%u,\"level_before\":43,\"level_after\":44,\"boundary\":%u,\"encounter\":%u,\"pp_spent\":%u,\"level_frame\":%u,\"returned\":%u,\"turns\":%u,\"walking_steps\":%u,\"enemy_hp_before\":%u,\"enemy_hp_min\":%u,\"outcome\":%u,\"guarded_phases\":3,\"denied_host_write_apis\":7,\"fresh_cores\":2,\"save_counters\":[2,3,3],\"party_preserved_bytes\":100,\"initial_party_exp_stats_progress_are_fixtures\":true,\"all_owners_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0}\n",threshold-1,threshold,xp,boundary,encounter,spent,level_frame,returned,turns,lb_steps,hp_before,hp_min,lb_outcome);
    return 0;
}
