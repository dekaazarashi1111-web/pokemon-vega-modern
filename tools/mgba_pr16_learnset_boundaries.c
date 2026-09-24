/* Issue19: 未受入の戦闘EXP境界。開始個体/EXP/能力/進行だけfixture。
 * 野生遭遇以降は通常キーのみ、全3区間で7書込APIを禁止する。
 * 既受入natural mainは呼ばず、固定・保存済みhelperだけを継承する。 */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "pr16_boundaries_helpers.h"
#pragma GCC diagnostic pop
struct XCase { const char *name; unsigned level,mode,slot,min_delta,moves[4],points[4]; };
#include "pr16_boundaries_vectors.h"
static unsigned x_cube(unsigned n){return n*n*n;}
static void x_expect(unsigned before,unsigned after,unsigned mode,unsigned slot,unsigned moves[4],unsigned points[4],unsigned *prompts) {
    *prompts=0;
    for(unsigned i=n_start[414];i<n_start[414]+n_count[414];++i){
        unsigned mid=n_rows[i][0],level=n_rows[i][1];if(level<=before || level>after)continue;
        bool known=false;unsigned empty=4;
        for(unsigned j=0;j<4;++j){if(moves[j]==mid)known=true;if(!moves[j] && empty==4)empty=j;}
        if(known)continue;
        if(empty==4){++*prompts;if(mode)continue;empty=slot;}
        moves[empty]=mid;points[empty]=n_pp[mid];
    }
}
int main(int argc,char **argv){
    if(argc!=6)return 2;
    unsigned index=qol_number(argv[5],"EXP boundary case");if(index>=sizeof(X_CASES)/sizeof(*X_CASES))return 2;
    const struct XCase *v=X_CASES+index;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rh[65],sh[65],endhash[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(rh,N_ROM_SHA) && !strcmp(sh,argv[4]) && !strcmp(sh,N_SEED_SHA),"boundary input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);c->reset(c);
    a_require(a_continue(c),"boundary initial Continue");a_flash_prepare(c);a_require(p02s_install_field_fixture(c),"boundary field fixture");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,414,v->level+1);unsigned threshold=p02s_data(c,25);
    create_mon(c,QOL_PLAYER_PARTY,414,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    a_require(p02s_data(c,25)==x_cube(v->level) && threshold==x_cube(v->level+1),"fixed owner growth curve");
    p02s_set_data(c,25,threshold-1);p02s_set_data(c,21,0);p02s_set_data(c,12,0);
    for(unsigned i=0;i<4;++i){p02s_set_data(c,13+i,v->moves[i]);p02s_set_data(c,17+i,v->points[i]);}
    for(unsigned offset=86;offset<=98;offset+=2)write16(c,QOL_PLAYER_PARTY+offset,999);
    n_slots(c,v->moves,v->points,v->level);
    unsigned char before[100],party[100],again[100];n_party(c,"fixture",before);lb_position(c,96,5,20,20);
    struct mCore saved=*c;a_guard(c);
    lb_path(c,5,lb_town_path,sizeof(lb_town_path)/sizeof(*lb_town_path),false);lb_step(c,QOL_KEY_UP);lb_position(c,96,17,11,39);unsigned boundary=lb_frames;
    lb_path(c,17,lb_grass_path,sizeof(lb_grass_path)/sizeof(*lb_grass_path),true);
    for(unsigned i=0;i<128 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);
        a_require(y==30 && (x==14 || x==15),"boundary grass pair");lb_step(c,x==14?QOL_KEY_RIGHT:QOL_KEY_LEFT);}
    a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==4 && read16(c,ADDR_BATTLE_MONS)==414,"ordinary action entry");
    unsigned encounter=lb_frames,eb=ADDR_BATTLE_MONS+BATTLE_MON_SIZE,enemy=read16(c,eb),enemy_level=read8(c,eb+0x2A);
    unsigned hp_before=read16(c,eb+BATTLE_CORE_MON_HP),hp_min=hp_before,spent=0,level_frame=0,turns=0,stable=0;
    unsigned summaries=0,selections=0,last_cb=0,summary_frame=0,selection_frame=0;bool chosen=false;
    a_require(hp_before>0,"live enemy");
    for(unsigned f=0;f<48000;++f){
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb!=last_cb){fprintf(stderr,"BOUNDARY_CALLBACK frame=%u callback=%08x\n",lb_frames,cb);last_cb=cb;if(cb!=P03F_SUMMARY_CB)chosen=false;}
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){
            unsigned hp=read16(c,eb+BATTLE_CORE_MON_HP);if(hp<hp_min)hp_min=hp;
            if(read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET)<v->points[0] && !spent)spent=lb_frames;
        }
        if(read8(c,QOL_PLAYER_PARTY+84)>v->level && !level_frame)level_frame=lb_frames;
        if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable>=60)break;}else stable=0;
        if(lb_action(c)){
            a_require(++turns<=8,"bounded battle turns");lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,60);
            a_require(read8(c,0x02022B24)==0x14 && (read32(c,0x02023B28)&1),"normal move menu");
            lb_cursor(c,BATTLE_CORE_MOVE_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,2);continue;
        }
        unsigned key=0;
        if(f%30==0){
            if(cb==P03F_SUMMARY_CB){
                if(!summary_frame)summary_frame=lb_frames;
                unsigned s=read32(c,QOL_SUMMARY_DATA_SLOT);
                a_require(p02s_ewram_pointer(s) && s+P03F_SUMMARY_STATE<0x02040000,"summary bounds");
                if(p03f_task(c,P03F_SUMMARY_TASK) && read8(c,s+P03F_SUMMARY_STATE)==2 && !chosen){
                    unsigned cursor=read8(c,P03F_SUMMARY_CURSOR);a_require(cursor<5,"summary cursor");
                    if(v->mode || cursor==v->slot){key=v->mode?QOL_KEY_B:QOL_KEY_A;chosen=true;++summaries;++selections;selection_frame=lb_frames;
                        fprintf(stderr,"BOUNDARY_SELECTION frame=%u cursor=%u key=%u mode=%u\n",lb_frames,cursor,key,v->mode);
                    }else key=QOL_KEY_DOWN;
                }
            }else key=QOL_KEY_A;
        }
        lb_frame(c,key);
        if(f%3000==0)fprintf(stderr,"BOUNDARY_PROGRESS frame=%u callback=%08x command=%u outcome=%u level=%u hp=%u pending=%u\n",lb_frames,cb,read8(c,0x02022B24),lb_outcome,read8(c,QOL_PLAYER_PARTY+84),hp_min,read16(c,0x02023F82));
    }
    unsigned returned=lb_frames;a_require(stable>=60 && lb_outcome==1 && hp_min==0 && spent && level_frame,"ordinary victory/EXP/field witness");
    a_restore(c,&saved);unsigned xp=p02s_data(c,25),level=p02s_data(c,56);
    a_require(level>=v->level+v->min_delta && level<100 && x_cube(level)<=xp && xp<x_cube(level+1),"native EXP level curve");
    unsigned after[4],afterpp[4],prompts;memcpy(after,v->moves,sizeof(after));memcpy(afterpp,v->points,sizeof(afterpp));
    afterpp[0]=p02s_data(c,17);a_require(afterpp[0]<v->points[0] && v->points[0]-afterpp[0]<=2*turns,"attack PP use");
    x_expect(v->level,level,v->mode,v->slot,after,afterpp,&prompts);
    a_require(summaries==prompts && selections==prompts,"native summary count");n_slots(c,after,afterpp,level);
    n_party(c,"returned",party);a_require(!memcmp(before,party,8) && read32(c,P03_SAVE_COUNTER)==2,"individual and unsaved counter");
    lb_resume_x=read16(c,lb_save1(c));lb_resume_y=read16(c,lb_save1(c)+2);
    a_guard(c);a_require(lb_normal_save(c),"boundary ordinary Save");a_restore(c,&saved);n_party(c,"saved",again);
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3,"boundary saved bytes");qol_close(c);qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);c->reset(c);saved=*c;
    a_guard(c);a_require(lb_normal_continue(c),"boundary fresh Continue");a_restore(c,&saved);n_party(c,"continued",again);
    a_require(!memcmp(party,again,100) && read32(c,P03_SAVE_COUNTER)==3 && p02s_data(c,25)==xp,"continued bytes/EXP");n_slots(c,after,afterpp,level);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],endhash);a_require(!strcmp(rh,endhash) && !log_problem_count,"ROM/log unchanged");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"enemy_species\":%u,\"enemy_level\":%u,\"moves_after\":",v->name,rh,enemy,enemy_level);n_array(after);
    printf(",\"pp_after\":");n_array(afterpp);
    printf(",\"xp_before\":%u,\"xp_threshold\":%u,\"xp_after\":%u,\"level_before\":%u,\"level_after\":%u,\"boundary\":%u,\"encounter\":%u,\"pp_spent\":%u,\"level_frame\":%u,\"returned\":%u,\"turns\":%u,\"walking_steps\":%u,\"enemy_hp_before\":%u,\"enemy_hp_min\":%u,\"outcome\":%u,\"summaries\":%u,\"selections\":%u,\"summary_frame\":%u,\"selection_frame\":%u,\"guarded_phases\":3,\"denied_host_write_apis\":7,\"fresh_cores\":2,\"save_counters\":[2,3,3],\"party_preserved_bytes\":100,\"initial_party_exp_stats_progress_are_fixtures\":true,\"all_owners_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0}\n",threshold-1,threshold,xp,v->level,level,boundary,encounter,spent,level_frame,returned,turns,lb_steps,hp_before,hp_min,lb_outcome,summaries,selections,summary_frame,selection_frame);
    return 0;
}
