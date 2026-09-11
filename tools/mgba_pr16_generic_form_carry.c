/* Real authored FORM host -> paged menu -> native party picker -> Shaymin
 * roundtrip. Starting map, progress and individual are fixtures. No injected
 * script, special, form call, task, flag, or host-memory write after guard. */
#include "pr16_form_breeding_helpers.c"
#define M_SHA "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e"
#define M_STATE 0x0203F720U
#define M_CURSOR 0x0203AD5EU
#define M_PARTY_SLOT 0x0203B01DU
#define M_TARGET (QOL_PLAYER_PARTY+100U)
#define M_SCOPE "PR16_P03_GENERIC_FORM_CARRY_PHYSICAL"
#define M_FORM_INDEX 43U
#define M_ORDINAL 6U
#define M_PAGE 1U
#define M_PAGE_CURSOR 1U
#define M_BASE_SPECIES 749U
#define M_TARGET_SPECIES 900U
#define M_GENERIC_ROWS_SHA "66cd203079d2a6d8ef1eb0fca6b5156c7bccbc1c720786df4953311491b5592e"

struct MCase {const char *name; unsigned action;};
static const struct MCase m_cases[]={
    {"shaymin-four-slot-roundtrip",0U},
    {"shaymin-party-cancel",1U},
};
static const unsigned m_moves[4]={98U,235U,552U,33U};
static const unsigned m_pp[4]={11U,3U,4U,7U};
static const char *m_route_ids[3]={
    "bca6fe62e4b8925d73c8238a",
    "830d0124e9ca952d41d4a7f0",
    "57e91d3ffeb04c9795a8b6a1",
};
struct MTrace {unsigned interaction,root,service,page,party,selection,returned,species_after,saved,reloaded;};

static void m_shot(const char *prefix,unsigned round,const char *suffix){
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%u-%s.ppm",prefix,round,suffix);
    a_require(n>0 && n<(int)sizeof(path),"generic form screenshot path too long");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"generic form screenshot open failed");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"generic form screenshot header failed");
    for(unsigned i=0;i<240U*160U;++i){uint32_t p=(uint32_t)b_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};a_require(fwrite(rgb,1,3,f)==3,"generic form screenshot write failed");}
    a_require(!fclose(f),"generic form screenshot close failed");
}
static void m_state(struct mCore *c,const char *name){
    b_state(c,name);fprintf(stderr,"GENFORM state=%08x result=%u host=%u service=%u mode=%u page=%u window=%u cursor=%u pending=%u slot=%u test=%u save=%u\n",
        read32(c,M_STATE),read16(c,M_STATE+8U),read8(c,M_STATE+18U),read8(c,M_STATE+20U),read8(c,M_STATE+19U),read8(c,M_STATE+21U),read8(c,M_STATE+22U),read8(c,M_CURSOR),read16(c,M_STATE+10U),read8(c,M_PARTY_SLOT),read8(c,M_STATE+27U),read32(c,P03_SAVE_COUNTER));
}
static bool m_menu(struct mCore *c,unsigned mode,unsigned page){
    return read16(c,M_STATE+8U)==9U && read8(c,M_STATE+18U)==3U && read8(c,M_STATE+20U)==3U
        && read8(c,M_STATE+19U)==mode && read8(c,M_STATE+21U)==page
        && read8(c,M_STATE+22U)<32U && read8(c,P02S_FIELD_LOCK) && !read8(c,M_STATE+27U);
}
static void m_waitmenu(struct mCore *c,unsigned mode,unsigned page,const char *prefix,unsigned round,const char *label){
    for(unsigned f=0;f<1800U;++f){if(m_menu(c,mode,page)){b_frames_run(c,0,30);return;}b_frame(c,0);}
    m_shot(prefix,round,label);m_state(c,label);a_die("generic physical form service menu absent");
}
static void m_to_page_one(struct mCore *c,const char *prefix,unsigned round,struct MTrace *t){
    a_require(read8(c,M_CURSOR)==0U && read8(c,M_STATE+21U)==0U,"generic form page zero precondition differs");
    for(unsigned k=0;k<5U;++k)b_press(c,QOL_KEY_DOWN,30);
    a_require(read8(c,M_CURSOR)==5U,"generic form next cursor differs");
    b_press(c,QOL_KEY_A,60);m_waitmenu(c,2U,M_PAGE,prefix,round,"page-timeout");
    t->page=b_frames;m_shot(prefix,round,"page-1");m_state(c,"page-1");
    b_press(c,QOL_KEY_DOWN,30);
    a_require(read8(c,M_CURSOR)==M_PAGE_CURSOR,"generic form page-one cursor differs");
}
static struct MTrace m_service(struct mCore *c,const struct MCase *v,const char *prefix,unsigned round){
    struct MTrace t={0};m_state(c,"approach-start");b_position(c,1,36,6,4);
    unsigned object=read8(c,P02S_PLAYER_AVATAR+5U);a_require(object<16U,"generic form avatar unavailable");
    if((read8(c,P02S_OBJECT_EVENTS+object*0x24U+0x18U)&15U)!=2U)b_frame(c,QOL_KEY_UP);
    b_frames_run(c,0U,30U);m_state(c,"approach-end");b_position(c,1,36,6,4);
    t.interaction=b_frames+1U;b_press(c,QOL_KEY_A,90);m_waitmenu(c,0U,0U,prefix,round,"root-timeout");
    t.root=b_frames;m_shot(prefix,round,"root");m_state(c,"root");
    a_require(read8(c,M_CURSOR)==0U,"generic form root cursor differs");
    b_press(c,QOL_KEY_DOWN,30);a_require(read8(c,M_CURSOR)==1U,"generic physical service cursor differs");
    b_press(c,QOL_KEY_A,60);m_waitmenu(c,2U,0U,prefix,round,"forms-timeout");t.service=b_frames;
    m_shot(prefix,round,"forms-page-0");m_state(c,"forms-page-0");m_to_page_one(c,prefix,round,&t);
    b_press(c,QOL_KEY_A,30);
    bool party=false;for(unsigned f=0;f<1800U;++f){if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY){party=true;break;}b_frame(c,0);}
    a_require(party,"generic authored host did not open native party selection");b_frames_run(c,0,180);
    t.party=b_frames;m_shot(prefix,round,"party");m_state(c,"party");
    a_require(read16(c,M_STATE+10U)==M_FORM_INDEX && read16(c,M_STATE+8U)==20U,"pending generic form differs");
    if(v->action==1U){b_press(c,QOL_KEY_B,180);b_wait(c);t.returned=b_frames;t.species_after=b_data(c,M_TARGET,11U);return t;}
    for(unsigned k=0;k<8U && read8(c,M_PARTY_SLOT)!=1U;++k)b_press(c,QOL_KEY_DOWN,30);
    a_require(read8(c,M_PARTY_SLOT)==1U,"generic native picker did not select second individual");
    t.selection=b_frames+1U;b_press(c,QOL_KEY_A,180);b_wait(c);t.returned=b_frames;t.species_after=b_data(c,M_TARGET,11U);
    m_shot(prefix,round,"returned");m_state(c,"returned");return t;
}
static void m_check(struct mCore *c,unsigned species,const uint8_t *decoy,unsigned pid,unsigned ot){
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U && b_data(c,M_TARGET,11U)==species
        && b_data(c,M_TARGET,0U)==pid && b_data(c,M_TARGET,1U)==ot && b_data(c,M_TARGET,21U)==229U,
        "generic form species/identity/PP Ups differs");
    for(unsigned k=0;k<4U;++k){unsigned actual=b_data(c,M_TARGET,13U+k),p=b_data(c,M_TARGET,17U+k);
        fprintf(stderr,"GENFORM slot=%u move=%u/%u pp=%u/%u bonus=229\n",k,actual,m_moves[k],p,m_pp[k]);
        a_require(actual==m_moves[k] && p==m_pp[k],"generic form moves/PP differ");}
    uint8_t now[100];b_copy(c,QOL_PLAYER_PARTY,now,100U);a_require(!memcmp(now,decoy,100U),"generic nonselected party individual changed");
    a_require(!read8(c,M_STATE+27U),"generic form test mode was enabled");
}
static void m_trace(const struct MTrace *t){
    printf("{\"interaction\":%u,\"root\":%u,\"service\":%u,\"page\":%u,\"party\":%u,\"selection\":%u,\"returned\":%u,\"species_after\":%u,\"saved\":%u,\"reloaded\":%u}",
        t->interaction,t->root,t->service,t->page,t->party,t->selection,t->returned,t->species_after,t->saved,t->reloaded);
}
int main(int argc,char **argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    const struct MCase *v=NULL;for(unsigned k=0;k<sizeof(m_cases)/sizeof(m_cases[0]);++k)if(!strcmp(argv[5],m_cases[k].name))v=&m_cases[k];
    if(!v)return 2;
    char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
    a_require(!strcmp(hash,M_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"generic form input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
    a_require(a_continue(c),"generic form initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,1U,36U,6U,4U);run_key_frames(c,0U,1800U);
    m_state(c,"fixture-warp");m_shot(argv[6],0U,"fixture-warp");
    for(unsigned k=0;k<12U && !b_field(c);++k)b_press(c,QOL_KEY_B,180U);
    m_state(c,"fixture-settled");b_position(c,1,36,6,4);
    clear_parties(c);b_create(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U);
    create_mon(c,M_TARGET,M_BASE_SPECIES,30U);write8(c,QOL_PLAYER_PARTY_COUNT,2U);
    for(unsigned k=0;k<4U;++k){set_mon_data_u32(c,M_TARGET,13U+k,m_moves[k]);set_mon_data_u32(c,M_TARGET,17U+k,m_pp[k]);}
    set_mon_data_u32(c,M_TARGET,21U,229U);
    /* Unlocks are prerequisite fixtures; the service interaction itself is native. */
    write8(c,QOL_LEDGER+18U,1U);write8(c,QOL_LEDGER+20U,1U);write8(c,QOL_LEDGER+21U,1U);
    write8(c,QOL_LEDGER+0x73FU,1U);write8(c,QOL_LEDGER+0x745U,1U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0U,0U,0U);
    unsigned pid=b_data(c,M_TARGET,0U),ot=b_data(c,M_TARGET,1U);
    uint8_t decoy[100];b_copy(c,QOL_PLAYER_PARTY,decoy,100U);
    unsigned rounds=v->action==0U?2U:1U,initial_counter=read32(c,P03_SAVE_COUNTER),expected_auto=0U;
    unsigned result=0,final_species=M_BASE_SPECIES;struct MTrace traces[2]={{0},{0}};struct mCore saved=*c;
    for(unsigned r=0;r<rounds;++r){
        /* After this barrier, only GBA input and read-only observations. */
        a_guard(c);unsigned counter=read32(c,P03_SAVE_COUNTER);traces[r]=m_service(c,v,argv[6],r);
        result=read16(c,M_STATE+8U);unsigned autos=v->action==0U?1U:0U;
        a_require(result==(v->action==0U?0U:20U),"generic physical form result differs");
        a_require(read32(c,P03_SAVE_COUNTER)==counter+autos,"generic form automatic persistence differs");expected_auto+=autos;
        a_restore(c,&saved);final_species=v->action==0U?(r==0U?M_TARGET_SPECIES:M_BASE_SPECIES):M_BASE_SPECIES;
        a_require(traces[r].species_after==final_species,"generic observed species differs");m_check(c,final_species,decoy,pid,ot);
        uint8_t party[200];b_copy(c,QOL_PLAYER_PARTY,party,200U);
        a_guard(c);a_require(b_save(c),"generic form normal Start Save failed");traces[r].saved=b_frames;
        a_restore(c,&saved);c=b_restart(c,argv[1],argv[2]);c->reset(c);saved=*c;a_guard(c);
        a_require(b_continue(c),"generic form cold Continue failed");traces[r].reloaded=b_frames;
        b_position(c,1,36,6,4);uint8_t restored[200];b_copy(c,QOL_PLAYER_PARTY,restored,200U);
        a_require(!memcmp(party,restored,200U) && read32(c,P03_SAVE_COUNTER)==counter+autos+1U,"generic persisted individual differs");
        a_restore(c,&saved);m_check(c,final_species,decoy,pid,ot);m_shot(argv[6],r,"continued");
    }
    a_require(read32(c,P03_SAVE_COUNTER)==initial_counter+expected_auto+rounds && !log_problem_count,"generic form save totals or emulator diagnostic differs");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after),"generic form changed ROM");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",M_SCOPE,v->name,hash);
    printf("\"form_index\":%u,\"eligible_ordinal\":%u,\"menu_page\":%u,\"menu_cursor\":%u,\"base_species\":%u,\"target_species\":%u,\"final_species\":%u,",M_FORM_INDEX,M_ORDINAL,M_PAGE,M_PAGE_CURSOR,M_BASE_SPECIES,M_TARGET_SPECIES,final_species);
    printf("\"moves\":[%u,%u,%u,%u],\"pp\":[%u,%u,%u,%u],\"pp_bonuses\":229,",m_moves[0],m_moves[1],m_moves[2],m_moves[3],m_pp[0],m_pp[1],m_pp[2],m_pp[3]);
    printf("\"representative_route_ids\":[\"%s\",\"%s\",\"%s\"],\"generic_owner_rows_sha256\":\"%s\",",m_route_ids[0],m_route_ids[1],m_route_ids[2],M_GENERIC_ROWS_SHA);
    printf("\"result\":%u,\"rounds\":%u,\"fresh_cores\":%u,\"automatic_saves\":%u,\"manual_saves\":%u,\"total_frames\":%u,",result,rounds,rounds+1U,expected_auto,rounds,b_frames);
    printf("\"physical_host\":[1,36,6,3],\"host_index\":3,\"selected_party_slot\":%u,\"host_write_barriers\":7,\"rtc_flash_bytes_preserved\":131072,\"test_mode\":false,\"party_byte_preserved_on_reload\":true,\"four_move_slots_preserved\":true,\"nonselected_preserved\":true,",v->action==0U?1U:6U);
    printf("\"starting_progress_individual_map_are_fixtures\":true,\"native_acceptance_claimed_for_all_61_individual_rows\":false,\"generic_owner_representative_accepted\":true,\"release_ready\":false,\"warnings_errors\":0,\"traces\":[");
    for(unsigned r=0;r<rounds;++r){if(r)putchar(',');m_trace(&traces[r]);}printf("]}\n");return 0;
}
