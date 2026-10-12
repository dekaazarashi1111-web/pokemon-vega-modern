/* Real authored BG host -> root/service -> party picker -> form operation.
 * Starting map, progress and individual are fixtures. No injected script,
 * special, form call, task, flag, or host-memory write during observation. */
#include "pr16_form_breeding_helpers.c"
#define M_SHA "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e"
#define M_STATE 0x0203F720U
#define M_CURSOR 0x0203AD5EU
#define M_PARTY_SLOT 0x0203B01DU
#define M_TARGET (QOL_PLAYER_PARTY+100U)
#define M_SCOPE "PR16_PHYSICAL_ROTOM_HOST_PARTY_FORM_SAVE"
struct MCase {const char *name; unsigned choice,action;};
static const struct MCase m_cases[]={
    {"heat-roundtrip",0,0},{"wash-roundtrip",1,0},{"frost-roundtrip",2,0},
    {"fan-roundtrip",3,0},{"mow-roundtrip",4,0},{"compact-removal",0,1},
    {"full-denied",0,2},{"root-cancel",0,3},{"forms-cancel",0,4},{"party-cancel",0,5}
};
static const unsigned m_sig[]={315,56,59,373,401};
struct MTrace {unsigned interaction,root,service,party,selection,returned,saved,reloaded;};
static void m_shot(const char *prefix,unsigned round,const char *suffix){
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%u-%s.ppm",prefix,round,suffix);
    a_require(n>0 && n<(int)sizeof(path),"form screenshot path too long");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"form screenshot open failed");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"form screenshot header failed");
    for(unsigned i=0;i<240U*160U;++i){uint32_t p=(uint32_t)b_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};a_require(fwrite(rgb,1,3,f)==3,"form screenshot write failed");}
    a_require(!fclose(f),"form screenshot close failed");
}
static void m_state(struct mCore *c,const char *name){
    b_state(c,name);fprintf(stderr,"FORM state=%08x result=%u host=%u service=%u mode=%u page=%u window=%u cursor=%u pending=%u slot=%u test=%u save=%u\n",
        read32(c,M_STATE),read16(c,M_STATE+8U),read8(c,M_STATE+18U),read8(c,M_STATE+20U),read8(c,M_STATE+19U),read8(c,M_STATE+21U),read8(c,M_STATE+22U),read8(c,M_CURSOR),read16(c,M_STATE+10U),read8(c,M_PARTY_SLOT),read8(c,M_STATE+27U),read32(c,P03_SAVE_COUNTER));
}
static bool m_menu(struct mCore *c,unsigned mode){
    return read16(c,M_STATE+8U)==9U && read8(c,M_STATE+18U)==3U && read8(c,M_STATE+20U)==3U
        && read8(c,M_STATE+19U)==mode && read8(c,M_STATE+21U)==0U
        && read8(c,M_STATE+22U)<32U && read8(c,P02S_FIELD_LOCK) && !read8(c,M_STATE+27U);
}
static void m_waitmenu(struct mCore *c,unsigned mode,const char *prefix,unsigned round){
    for(unsigned f=0;f<1200U;++f){if(m_menu(c,mode)){b_frames_run(c,0,30);return;}b_frame(c,0);}
    m_shot(prefix,round,"menu-timeout");m_state(c,"menu-timeout");a_die("physical form service menu absent");
}
static struct MTrace m_service(struct mCore *c,const struct MCase *v,const char *prefix,unsigned round){
    struct MTrace t={0};m_state(c,"approach-start");b_position(c,1,36,6,4);
    unsigned object=read8(c,P02S_PLAYER_AVATAR+5U);a_require(object<16U,"form avatar unavailable");
    if((read8(c,P02S_OBJECT_EVENTS+object*0x24U+0x18U)&15U)!=2U)b_frame(c,QOL_KEY_UP);
    b_frames_run(c,0U,30U);m_state(c,"approach-end");b_position(c,1,36,6,4);
    t.interaction=b_frames+1U;b_press(c,QOL_KEY_A,90);m_waitmenu(c,0,prefix,round);
    t.root=b_frames;m_shot(prefix,round,"root");m_state(c,"root");
    a_require(read8(c,M_CURSOR)==0U,"form root cursor differs");
    if(v->action==3U){b_press(c,QOL_KEY_B,60);b_wait(c);t.returned=b_frames;return t;}
    b_press(c,QOL_KEY_DOWN,30);a_require(read8(c,M_CURSOR)==1U,"physical service cursor differs");
    b_press(c,QOL_KEY_A,60);m_waitmenu(c,2,prefix,round);t.service=b_frames;
    m_shot(prefix,round,"forms");m_state(c,"forms");
    if(v->action==4U){b_press(c,QOL_KEY_B,60);b_wait(c);t.returned=b_frames;return t;}
    for(unsigned k=0;k<v->choice;++k)b_press(c,QOL_KEY_DOWN,30);
    a_require(read8(c,M_CURSOR)==v->choice,"physical form choice differs");b_press(c,QOL_KEY_A,30);
    bool party=false;for(unsigned f=0;f<1800U;++f){if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY){party=true;break;}b_frame(c,0);}
    a_require(party,"authored host did not open native party selection");b_frames_run(c,0,180);
    t.party=b_frames;m_shot(prefix,round,"party");m_state(c,"party");
    a_require(read16(c,M_STATE+10U)==37U+v->choice && read16(c,M_STATE+8U)==20U,"pending physical form differs");
    if(v->action==5U){b_press(c,QOL_KEY_B,180);b_wait(c);t.returned=b_frames;return t;}
    for(unsigned k=0;k<8U && read8(c,M_PARTY_SLOT)!=1U;++k)b_press(c,QOL_KEY_DOWN,30);
    a_require(read8(c,M_PARTY_SLOT)==1U,"native picker did not select second individual");
    t.selection=b_frames+1U;b_press(c,QOL_KEY_A,180);b_wait(c);t.returned=b_frames;
    m_shot(prefix,round,"returned");m_state(c,"returned");return t;
}
static void m_check(struct mCore *c,unsigned species,const unsigned *moves,const unsigned *pp,unsigned bonus,const uint8_t *decoy,unsigned pid,unsigned ot){
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U && b_data(c,M_TARGET,11U)==species
        && b_data(c,M_TARGET,0U)==pid && b_data(c,M_TARGET,1U)==ot && b_data(c,M_TARGET,21U)==bonus,
        "form species/identity/PP Ups differs");
    for(unsigned k=0;k<4U;++k){unsigned actual=b_data(c,M_TARGET,13U+k),p=b_data(c,M_TARGET,17U+k);
        fprintf(stderr,"FORM slot=%u move=%u/%u pp=%u/%u bonus=%u\n",k,actual,moves[k],p,pp[k],bonus);
        a_require(actual==moves[k] && p==pp[k],"form moves/PP differ");}
    uint8_t now[100];b_copy(c,QOL_PLAYER_PARTY,now,100U);a_require(!memcmp(now,decoy,100U),"nonselected party individual changed");
    a_require(!read8(c,M_STATE+27U),"form test mode was enabled");
}
static void m_trace(const struct MTrace *t){
    printf("{\"interaction\":%u,\"root\":%u,\"service\":%u,\"party\":%u,\"selection\":%u,\"returned\":%u,\"saved\":%u,\"reloaded\":%u}",
        t->interaction,t->root,t->service,t->party,t->selection,t->returned,t->saved,t->reloaded);
}
int main(int argc,char **argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    const struct MCase *v=NULL;for(unsigned k=0;k<sizeof(m_cases)/sizeof(m_cases[0]);++k)if(!strcmp(argv[5],m_cases[k].name))v=&m_cases[k];
    if(!v)return 2;
    char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,M_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"form input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"form initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,1U,36U,6U,4U);run_key_frames(c,0U,1800U);
    m_state(c,"fixture-warp");m_shot(argv[6],0U,"fixture-warp");
    for(unsigned k=0;k<12U && !b_field(c);++k)b_press(c,QOL_KEY_B,180U);
    m_state(c,"fixture-settled");b_position(c,1,36,6,4);
    clear_parties(c);b_create(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U);
    create_mon(c,M_TARGET,v->action==1U?894U:742U,30U);write8(c,QOL_PLAYER_PARTY_COUNT,2U);
    unsigned before[4]={84,109,86,0},before_pp[4]={7,8,9,0},bonus=37U;
    if(v->action==1U){before[1]=315U;before[2]=109U;before[3]=86U;before_pp[1]=2U;before_pp[2]=8U;before_pp[3]=9U;bonus=229U;}
    if(v->action==2U){before[3]=33U;before_pp[3]=6U;bonus=229U;}
    for(unsigned k=0;k<4U;++k){set_mon_data_u32(c,M_TARGET,13U+k,before[k]);set_mon_data_u32(c,M_TARGET,17U+k,before_pp[k]);}
    set_mon_data_u32(c,M_TARGET,21U,bonus);
    /* Research progress is a prerequisite fixture, not a tested unlock route. */
    write8(c,QOL_LEDGER+0x73FU,1U);write8(c,QOL_LEDGER+0x745U,1U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0U,0U,0U);
    unsigned pid=b_data(c,M_TARGET,0U),ot=b_data(c,M_TARGET,1U),canonical=b_pp(c,m_sig[v->choice]);
    uint8_t decoy[100];b_copy(c,QOL_PLAYER_PARTY,decoy,100U);
    unsigned rounds=v->action==0U?2U:1U,initial_counter=read32(c,P03_SAVE_COUNTER),expected_auto=0U;
    unsigned result=0,final_moves[4],final_pp[4],final_species=742U,final_bonus=bonus;
    struct MTrace traces[2]={{0},{0}};struct mCore saved=*c;
    for(unsigned r=0;r<rounds;++r){
        /* After this barrier, only GBA input and read-only observations. */
        a_guard(c);unsigned counter=read32(c,P03_SAVE_COUNTER);traces[r]=m_service(c,v,argv[6],r);
        result=read16(c,M_STATE+8U);unsigned autos=v->action<=1U?1U:0U;
        a_require(result==(v->action<=1U?0U:v->action==2U?1U:v->action==5U?20U:2U),"physical form result differs");
        a_require(read32(c,P03_SAVE_COUNTER)==counter+autos,"form automatic persistence differs");expected_auto+=autos;
        a_restore(c,&saved);memcpy(final_moves,before,sizeof(before));memcpy(final_pp,before_pp,sizeof(before_pp));final_species=742U;final_bonus=bonus;
        if(v->action==0U && r==0U){final_moves[3]=m_sig[v->choice];final_pp[3]=canonical;final_species=894U+v->choice;}
        if(v->action==1U){final_moves[1]=109U;final_moves[2]=86U;final_moves[3]=0U;final_pp[1]=8U;final_pp[2]=9U;final_pp[3]=0U;final_bonus=57U;}
        m_check(c,final_species,final_moves,final_pp,final_bonus,decoy,pid,ot);
        uint8_t party[200];b_copy(c,QOL_PLAYER_PARTY,party,200U);
        a_guard(c);a_require(b_save(c),"form normal Start Save failed");traces[r].saved=b_frames;
        a_restore(c,&saved);c=b_restart(c,argv[1],argv[2]);c->reset(c);saved=*c;a_guard(c);
        a_require(b_continue(c),"form cold Continue failed");traces[r].reloaded=b_frames;
        b_position(c,1,36,6,4);uint8_t restored[200];b_copy(c,QOL_PLAYER_PARTY,restored,200U);
        a_require(!memcmp(party,restored,200U) && read32(c,P03_SAVE_COUNTER)==counter+autos+1U,"form persisted individual differs");
        a_restore(c,&saved);m_check(c,final_species,final_moves,final_pp,final_bonus,decoy,pid,ot);
        m_shot(argv[6],r,"continued");
    }
    a_require(read32(c,P03_SAVE_COUNTER)==initial_counter+expected_auto+rounds && !log_problem_count,"form save totals or emulator diagnostic differs");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after),"form changed ROM");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",M_SCOPE,v->name,hash);
    printf("\"species\":%u,\"moves\":",final_species);a_array(final_moves);printf(",\"pp\":");a_array(final_pp);
    printf(",\"pp_bonuses\":%u,\"signature_pp\":%u,\"result\":%u,\"rounds\":%u,\"fresh_cores\":%u,\"automatic_saves\":%u,\"manual_saves\":%u,\"total_frames\":%u,",final_bonus,canonical,result,rounds,rounds+1U,expected_auto,rounds,b_frames);
    printf("\"physical_host\":[1,36,6,3],\"host_index\":3,\"selected_party_slot\":%u,\"host_write_barriers\":7,\"rtc_flash_bytes_preserved\":131072,\"test_mode\":false,\"party_byte_preserved_on_reload\":true,\"nonselected_preserved\":true,",v->action<=2U?1U:6U);
    printf("\"starting_progress_individual_map_are_fixtures\":true,\"release_ready\":false,\"warnings_errors\":0,\"traces\":[");
    for(unsigned r=0;r<rounds;++r){if(r)putchar(',');m_trace(&traces[r]);}printf("]}\n");return 0;
}
