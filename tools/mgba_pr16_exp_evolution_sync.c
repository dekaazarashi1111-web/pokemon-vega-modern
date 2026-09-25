/* Issue19: 戦闘EXP進化承認/取消と控え共有EXP。開始個体/EXP/能力/進行だけfixture。
 * 野生遭遇以降は通常キーのみ、全3区間で7書込APIを禁止する。
 * 既受入boundary/natural mainは呼ばず、固定・保存済みhelperだけを継承する。 */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "pr16_boundaries_helpers.h"
#pragma GCC diagnostic pop
struct XCase { const char *name; unsigned level,mode,slot,min_delta,moves[4],points[4]; };
#include "pr16_boundaries_vectors.h"
#include "pr16_exp_multilevel_trace.h"
static unsigned x_cube(unsigned n){return n*n*n;}
static unsigned e_count,e_sid,e_samples,e_reserve_entries;
static void (*e_original_frame)(struct mCore *);
/* Fixed candidate stores its unencrypted substructures in this order. The first
 * failed run's native GetMonData observations independently bind these offsets.
 * Observation must not advance CPU/timers merely to read another party member. */
static unsigned e_get(struct mCore *c,unsigned index,unsigned field){
    unsigned mon=QOL_PLAYER_PARTY+100*index;
    if(field==11)return read16(c,mon+0x20);
    if(field==12)return read16(c,mon+0x22);
    if(field>=13 && field<=16)return read16(c,mon+0x2c+2*(field-13));
    if(field>=17 && field<=20)return read8(c,mon+0x34+field-17);
    if(field==21)return read8(c,mon+0x28);
    if(field==25)return read32(c,mon+0x24);
    if(field==56)return read8(c,mon+84);
    a_die("unbound read-only mon field");
}
static void e_choose(struct mCore *c){
    unsigned ready=0;
    for(unsigned i=0;i<1200 && ready<12;++i){
        if(lb_action(c))++ready;else ready=0;
        lb_frame(c,0);
    }
    a_require(ready==12,"stable ordinary action menu");
    lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,0);
    unsigned pulses=0;
    for(unsigned i=0;i<900;++i){
        if(read8(c,0x02022B24)==0x14 && (read32(c,0x02023B28)&1)){
            fprintf(stderr,"ESHARE_FIGHT frame=%u pulses=%u\n",lb_frames,pulses);
            lb_cursor(c,BATTLE_CORE_MOVE_SELECTION_CURSOR,0);lb_press(c,QOL_KEY_A,2);return;
        }
        unsigned key=lb_action(c) && i%30==0?QOL_KEY_A:0;
        if(key)++pulses;
        lb_frame(c,key);
    }
    a_die("normal move menu readiness timeout");
}
static void e_frame(struct mCore *c){
    e_original_frame(c);x_trace(c);
    if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && read32(c,0x03004FC4U)==0x08013861U){
        unsigned index=read16(c,ADDR_BATTLER_PARTY_INDEXES);++e_samples;
        if(index!=0)++e_reserve_entries;
        a_require(index==0,"only the original lead may participate");
    }
}
static void e_party(struct mCore *c,const char *stage,unsigned char out[200]){
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==e_count,"party count preservation");
    fprintf(stderr,"ESHARE_PARTY stage=%s count=%u counter=%u hex=",stage,e_count,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<100*e_count;++i){out[i]=read8(c,QOL_PLAYER_PARTY+i);fprintf(stderr,"%02x",out[i]);}fputc('\n',stderr);
    for(unsigned i=0;i<e_count;++i){
        unsigned mon=QOL_PLAYER_PARTY+100*i;
        unsigned hp=read16(c,mon+86),maximum=read16(c,mon+88);
        a_require(0<hp && hp<=maximum && maximum<999,"all-party health bounds");
        fprintf(stderr,"ESHARE_MON stage=%s index=%u species=%u level=%u xp=%u hp=%u maxhp=%u held=%u bonus=%u moves=",stage,i,e_get(c,i,11),e_get(c,i,56),e_get(c,i,25),hp,maximum,e_get(c,i,12),e_get(c,i,21));
        for(unsigned j=0;j<4;++j)fprintf(stderr,"%s%u",j?",":"",e_get(c,i,13+j));
        fprintf(stderr," pp=");for(unsigned j=0;j<4;++j)fprintf(stderr,"%s%u",j?",":"",e_get(c,i,17+j));fputc('\n',stderr);
    }
}
static void e_expect(unsigned sid,unsigned before,unsigned after,bool evolved,unsigned moves[4],unsigned points[4]){
    unsigned sequence[129],used=0;
    for(unsigned i=n_start[sid];i<n_start[sid]+n_count[sid];++i)
        if(before<n_rows[i][1] && n_rows[i][1]<=after){a_require(used<128,"bounded eligible rows");sequence[used++]=n_rows[i][0];}
    if(evolved)sequence[used++]=16; /* payload evolution span is independently hash-checked by Python. */
    for(unsigned i=0;i<used;++i){unsigned mid=sequence[i],empty=4;bool known=false;
        for(unsigned j=0;j<4;++j){if(moves[j]==mid)known=true;if(!moves[j] && empty==4)empty=j;}
        if(known)continue;
        a_require(empty<4,"this scope must not need a full-slot summary");moves[empty]=mid;points[empty]=n_pp[mid];
    }
}
static void e_slots(struct mCore *c,unsigned index,unsigned species,unsigned level,const unsigned moves[4],const unsigned points[4]){
    a_require(e_get(c,index,11)==species && e_get(c,index,56)==level && e_get(c,index,21)==0 && e_get(c,index,12)==0,"owner/level/held/bonus");
    for(unsigned j=0;j<4;++j)a_require(e_get(c,index,13+j)==moves[j] && e_get(c,index,17+j)==points[j],"original move/PP oracle");
}
int main(int argc,char **argv){
    if(argc!=6)return 2;
    unsigned index=qol_number(argv[5],"EXP boundary case");if(index>=sizeof(X_CASES)/sizeof(*X_CASES))return 2;
    const struct XCase *v=X_CASES+index;
    e_count=v->mode==2?2:1;e_sid=v->mode==2?414:413;
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rh[65],sh[65],endhash[65];sha256_file(argv[1],rh);sha256_file(argv[2],sh);
    a_require(!strcmp(rh,argv[3]) && !strcmp(rh,N_ROM_SHA) && !strcmp(sh,argv[4]) && !strcmp(sh,N_SEED_SHA),"boundary input identity");
    struct mLogger logger={.log=x_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);c->reset(c);
    a_require(a_continue(c),"boundary initial Continue");a_flash_prepare(c);a_require(p02s_install_field_fixture(c),"boundary field fixture");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,e_sid,v->level+1);unsigned threshold=p02s_data(c,25);
    create_mon(c,QOL_PLAYER_PARTY,e_sid,v->level);write8(c,QOL_PLAYER_PARTY_COUNT,e_count);
    a_require(p02s_data(c,25)==x_cube(v->level) && threshold==x_cube(v->level+1),"fixed owner growth curve");
    p02s_set_data(c,25,threshold-1);p02s_set_data(c,21,0);p02s_set_data(c,12,0);
    for(unsigned i=0;i<4;++i){p02s_set_data(c,13+i,v->moves[i]);p02s_set_data(c,17+i,v->points[i]);}
    /* Multiple native level-ups recalculate max HP. Keep HP/max HP generated;
     * inflate only combat stats, not a health value that would overrun summary. */
    for(unsigned offset=90;offset<=98;offset+=2)write16(c,QOL_PLAYER_PARTY+offset,999);
    a_require(read16(c,QOL_PLAYER_PARTY+86)>0 && read16(c,QOL_PLAYER_PARTY+86)==read16(c,QOL_PLAYER_PARTY+88) && read16(c,QOL_PLAYER_PARTY+88)<999,"native initial HP/max HP fixture");
    e_slots(c,0,e_sid,v->level,v->moves,v->points);
    if(e_count==2){
        unsigned mon=QOL_PLAYER_PARTY+100;create_mon(c,mon,414,v->level);
        set_mon_data_u32(c,mon,25,threshold-1);set_mon_data_u32(c,mon,21,0);set_mon_data_u32(c,mon,12,0);
        for(unsigned i=0;i<4;++i){set_mon_data_u32(c,mon,13+i,v->moves[i]);set_mon_data_u32(c,mon,17+i,v->points[i]);}
        (void)call_preserving(c,QOL_FLAG_SET,QOL_FLAG_EXP_SHARE,0,0,0);
        (void)call_preserving(c,QOL_FLAG_SET,QOL_FLAG_EXP_SHARE_INITIALIZED,0,0,0);
        a_require(call_preserving(c,QOL_FLAG_GET,QOL_FLAG_EXP_SHARE,0,0,0)==1,"initial EXP Share flag fixture");
        e_slots(c,1,414,v->level,v->moves,v->points);
    }
    unsigned char before[200]={0},party[200]={0},again[200]={0};e_party(c,"fixture",before);lb_position(c,96,5,20,20);
    e_original_frame=c->runFrame;c->runFrame=e_frame;
    struct mCore saved=*c;a_guard(c);
    lb_path(c,5,lb_town_path,sizeof(lb_town_path)/sizeof(*lb_town_path),false);lb_step(c,QOL_KEY_UP);lb_position(c,96,17,11,39);unsigned boundary=lb_frames;
    lb_path(c,17,lb_grass_path,sizeof(lb_grass_path)/sizeof(*lb_grass_path),true);
    for(unsigned i=0;i<128 && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER);++i){unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);
        a_require(y==30 && (x==14 || x==15),"boundary grass pair");lb_step(c,x==14?QOL_KEY_RIGHT:QOL_KEY_LEFT);}
    a_require(lb_action(c) && read32(c,ADDR_BATTLE_TYPE_FLAGS)==4 && read16(c,ADDR_BATTLE_MONS)==e_sid,"ordinary action entry");
    unsigned encounter=lb_frames,eb=ADDR_BATTLE_MONS+BATTLE_MON_SIZE,enemy=read16(c,eb),enemy_level=read8(c,eb+0x2A);
    unsigned hp_before=read16(c,eb+BATTLE_CORE_MON_HP),hp_min=hp_before,spent=0,level_frame=0,turns=0,stable=0;
    unsigned evo_begin=0,evo_update=0,evo_pulses=0,reserve_level_frame=0;
    a_require(hp_before>0,"live enemy");
    for(unsigned f=0;f<48000;++f){
        x_trace(c);unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb==P02S_CB2_EVOLUTION_BEGIN && !evo_begin){evo_begin=lb_frames;fprintf(stderr,"ESHARE_EVOLUTION phase=begin frame=%u callback=%08x\n",lb_frames,cb);}
        if(cb==P02S_CB2_EVOLUTION_UPDATE && !evo_update){evo_update=lb_frames;fprintf(stderr,"ESHARE_EVOLUTION phase=update frame=%u callback=%08x\n",lb_frames,cb);}
        a_require(cb!=P03F_SUMMARY_CB,"unexpected full-slot summary");
        if(e_count==2 && read8(c,QOL_PLAYER_PARTY+184)>v->level && !reserve_level_frame)reserve_level_frame=lb_frames;
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){
            unsigned hp=read16(c,eb+BATTLE_CORE_MON_HP);if(hp<hp_min)hp_min=hp;
            if(read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET)<v->points[0] && !spent)spent=lb_frames;
        }
        if(read8(c,QOL_PLAYER_PARTY+84)>v->level && !level_frame)level_frame=lb_frames;
        if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable>=60)break;}else stable=0;
        if(lb_action(c)){
            a_require(++turns<=8,"bounded battle turns");e_choose(c);continue;
        }
        unsigned key=0;
        if(f%30==0){
            key=QOL_KEY_A;
            if(cb==P02S_CB2_EVOLUTION_UPDATE){key=v->mode==1?QOL_KEY_B:QOL_KEY_A;++evo_pulses;
                fprintf(stderr,"ESHARE_EVOLUTION_INPUT frame=%u key=%u\n",lb_frames,key);}
        }
        lb_frame(c,key);
        if(f%3000==0)fprintf(stderr,"BOUNDARY_PROGRESS frame=%u callback=%08x command=%u outcome=%u level=%u hp=%u pending=%u\n",lb_frames,cb,read8(c,0x02022B24),lb_outcome,read8(c,QOL_PLAYER_PARTY+84),hp_min,read16(c,0x02023F82));
    }
    unsigned returned=lb_frames;a_require(stable>=60 && lb_outcome==1 && hp_min==0 && spent && level_frame,"ordinary victory/EXP/field witness");
    a_restore(c,&saved);c->runFrame=e_original_frame;unsigned xp=e_get(c,0,25),level=e_get(c,0,56);
    a_require(level>=v->level+v->min_delta && level<100 && x_cube(level)<=xp && xp<x_cube(level+1),"native EXP level curve");
    unsigned after[4],afterpp[4];memcpy(after,v->moves,sizeof(after));memcpy(afterpp,v->points,sizeof(afterpp));
    afterpp[0]=e_get(c,0,17);a_require(afterpp[0]<v->points[0] && v->points[0]-afterpp[0]<=2*turns,"attack PP use");
    e_expect(e_sid,v->level,level,v->mode==0,after,afterpp);
    e_slots(c,0,v->mode==0?414:e_sid,level,after,afterpp);
    unsigned reserve_level=0,reserve_xp=0,reserve_moves[4]={0},reserve_pp[4]={0};
    if(e_count==2){
        reserve_level=e_get(c,1,56);reserve_xp=e_get(c,1,25);
        a_require(reserve_level>v->level && reserve_level<100 && x_cube(reserve_level)<=reserve_xp && reserve_xp<x_cube(reserve_level+1) && reserve_level_frame,"native reserve EXP curve");
        memcpy(reserve_moves,v->moves,sizeof(reserve_moves));memcpy(reserve_pp,v->points,sizeof(reserve_pp));
        e_expect(414,v->level,reserve_level,false,reserve_moves,reserve_pp);e_slots(c,1,414,reserve_level,reserve_moves,reserve_pp);
        a_require(!evo_begin && !evo_update && !evo_pulses && e_samples>0 && !e_reserve_entries,"nonparticipant shared EXP only");
    }else a_require(level_frame<evo_begin && evo_begin<evo_update && evo_update<returned && evo_pulses,"battle EXP evolution scene");
    e_party(c,"returned",party);a_require(!memcmp(before,party,8) && read32(c,P03_SAVE_COUNTER)==2,"individual and unsaved counter");
    if(e_count==2)a_require(!memcmp(before+100,party+100,8),"reserve individual preserved");
    lb_resume_x=read16(c,lb_save1(c));lb_resume_y=read16(c,lb_save1(c)+2);
    a_guard(c);a_require(lb_normal_save(c),"boundary ordinary Save");a_restore(c,&saved);c->runFrame=e_original_frame;e_party(c,"saved",again);
    a_require(!memcmp(party,again,100*e_count) && read32(c,P03_SAVE_COUNTER)==3,"boundary saved bytes");qol_close(c);qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);c->reset(c);saved=*c;
    a_guard(c);a_require(lb_normal_continue(c),"boundary fresh Continue");a_restore(c,&saved);e_party(c,"continued",again);
    a_require(!memcmp(party,again,100*e_count) && read32(c,P03_SAVE_COUNTER)==3 && p02s_data(c,25)==xp,"continued bytes/EXP");e_slots(c,0,v->mode==0?414:e_sid,level,after,afterpp);
    if(e_count==2)e_slots(c,1,414,reserve_level,reserve_moves,reserve_pp);
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],endhash);a_require(!strcmp(rh,endhash) && !log_problem_count,"ROM/log unchanged");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"enemy_species\":%u,\"enemy_level\":%u,\"moves_after\":",v->name,rh,enemy,enemy_level);n_array(after);
    printf(",\"pp_after\":");n_array(afterpp);printf(",\"reserve_moves_after\":");n_array(reserve_moves);printf(",\"reserve_pp_after\":");n_array(reserve_pp);
    printf(",\"species_before\":%u,\"species_after\":%u,\"party_count\":%u,\"xp_before\":%u,\"xp_after\":%u,\"level_before\":%u,\"level_after\":%u,\"reserve_level_after\":%u,\"reserve_xp_after\":%u,\"boundary\":%u,\"encounter\":%u,\"pp_spent\":%u,\"level_frame\":%u,\"reserve_level_frame\":%u,\"returned\":%u,\"turns\":%u,\"walking_steps\":%u,\"enemy_hp_before\":%u,\"enemy_hp_min\":%u,\"outcome\":%u,\"evolution_begin\":%u,\"evolution_update\":%u,\"evolution_input_pulses\":%u,\"active_party_index_samples\":%u,\"reserve_battle_entries\":%u,\"guarded_phases\":3,\"denied_host_write_apis\":7,\"fresh_cores\":2,\"save_counters\":[2,3,3],\"party_preserved_bytes\":%u,\"initial_party_exp_stats_progress_share_are_fixtures\":true,\"all_owners_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0}\n",e_sid,v->mode==0?414:e_sid,e_count,threshold-1,xp,v->level,level,reserve_level,reserve_xp,boundary,encounter,spent,level_frame,reserve_level_frame,returned,turns,lb_steps,hp_before,hp_min,lb_outcome,evo_begin,evo_update,evo_pulses,e_samples,e_reserve_entries,100*e_count);
    return 0;
}
