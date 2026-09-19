/* Native Mega input -> ability assignment -> first turn -> Run/revert ->
 * native Save -> independent core Continue on exact Stage82. Species/gear,
 * policy selection and the opponent are an isolated pre-input fixture, NOT
 * natural capture, shop acquisition or physical facility admission. Seven
 * host memory/register APIs are trapped from first action through Save and
 * cold Continue. This is representative P05 progress, not full acceptance. */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "m5_scheduler_embedded.c"
#pragma GCC diagnostic pop
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/savedata.h>
#include <mgba-util/vfs.h>

static void m5_need(bool yes, const char *why) { if (!yes) p05_die(why); }
static const unsigned m5_bases[]={503,411,957,497,787,1526};
static const unsigned m5_stones[]={1016,1012,1031,1029,1014,1035};
static const unsigned m5_megas[]={1638,1634,1655,1652,1636,1659};
static const unsigned m5_base_abilities[]={67,26,128,65,160,15};
static const char *const m5_modes[]={"active","no-toggle","no-ring","no-stone","wrong-stone","policy-denied","cancel-toggle"};
#define M5_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"
#define M5_SEED_SHA "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
#define M5_SCOPE "P05_NATIVE_MEGA_INPUT_TURN_REVERT_COLD_SAVE"
#define M5_ACTION_CURSOR 0x02023F58U
#define M5_CONFIGURE_POLICY 0x091261F5U
#define M5_CAN_MEGA 0x09114BE5U

static void m5_flash_prepare(struct mCore*c) {
    /* Rebind mGBA 0.10.2's bank after reserving RTC metadata, before the
     * observation barrier. Keep every byte of both game-flash banks intact. */
    struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
    m5_need(s->type==SAVEDATA_FLASH1M && s->data && s->currentBank,"flash type/bank unavailable");
    uintptr_t offset=(uintptr_t)s->currentBank-(uintptr_t)s->data;
    m5_need(offset==0 || offset==0x10000,"flash bank offset invalid");
    uint8_t*before=malloc(0x20000);m5_need(before!=NULL,"flash snapshot allocation");
    memcpy(before,s->data,0x20000);GBASavedataRTCWrite(s);s->currentBank=s->data+offset;
    m5_need(!memcmp(before,s->data,0x20000),"RTC preparation changed game flash");
    m5_need(s->vf->size(s->vf)==0x20010,"RTC trailer not reserved");free(before);
}
static bool m5_field(struct mCore*c) {
    unsigned id=read8(c,P02S_PLAYER_AVATAR+5);
    return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD && p02s_continue_position(c)
        && read8(c,P02S_FIELD_LOCK)==0 && read8(c,P02S_QUEST_LOG_STATE)==0
        && read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)==0 && id<16
        && (read8(c,P02S_OBJECT_EVENTS+id*0x24)&1U)
        && read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET)==0
        && read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET)==0;
}
static bool m5_continue(struct mCore*c) {
    run_key_frames(c,0,P02S_TITLE_FRAMES);
    for(unsigned p=0;p<P02S_CONTINUE_PULSES;p++) {
        qol_press(c,p==0?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD || !p02s_continue_position(c))continue;
        run_key_frames(c,0,300);
        for(unsigned r=0;r<8;r++) {
            if(!read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) {
                run_key_frames(c,0,P02S_FIELD_SETTLE_FRAMES);unsigned stable=0;
                for(unsigned f=0;f<3600;f++) {
                    if(m5_field(c)){if(++stable>=P02S_INPUT_READY_FRAMES)return true;}else stable=0;
                    run_key_frames(c,0,1);
                }
            }
            qol_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);
        }
        return false;
    }
    return false;
}
static bool m5_save(struct mCore *core) {
    uint32_t counter=read32(core,0x030053E0U);
    qol_press(core,QOL_KEY_START,120U);
    if(read32(core,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    uint8_t count=read8(core,QOL_START_MENU_COUNT),cursor=read8(core,QOL_START_MENU_CURSOR);
    if(count==0 || count>9 || cursor>=count)return false;
    uint8_t target=count;
    for(uint8_t i=0;i<count;i++)if(read8(core,QOL_START_MENU_ORDER+i)==4U)target=i;
    if(target==count)return false;
    unsigned steps=(unsigned)(target+count-cursor)%count;
    for(unsigned i=0;i<steps;i++)qol_press(core,QOL_KEY_DOWN,30U);
    if(read8(core,QOL_START_MENU_CURSOR)!=target)return false;
    qol_press(core,QOL_KEY_A,120U);
    bool callback_seen=false;
    for(unsigned prompt=0;prompt<32;prompt++) {
        uint32_t cb=read32(core,QOL_START_MENU_CALLBACK);
        if(cb==0x0806EDB9U)callback_seen=true;
        if(callback_seen && cb==0x0806EDB9U && read32(core,0x030053E0U)==counter+1U && m5_field(core)) {
            run_key_frames(core,0U,180U);return m5_field(core);
        }
        qol_press(core,QOL_KEY_A,180U);
    }
    fprintf(stderr,"native Save failed: counter=%u/%u\n",read32(core,0x030053E0U),counter);
    return false;
}
static void m5_mon_bytes(struct mCore *core,uint8_t out[100]) {
    for(unsigned i=0;i<100;i++)out[i]=read8(core,ADDR_PLAYER_PARTY+i);
}
static unsigned m5_u16(const uint8_t*p) {return p[0]|((unsigned)p[1]<<8);}
/* This exact Vega product stores the 48-byte mon payload in native plain
 * order. Match the fixture to native data before the observation barrier;
 * do not impose an encrypted Gen3 layout or checksum on this product. */
static void m5_plain(const uint8_t mon[100],uint8_t out[48]) {memcpy(out,mon+32,48);}

int main(int argc, char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))p05_test_guard(argv[2]);
    if(argc!=7 || strcmp(argv[3],M5_ROM_SHA) || strcmp(argv[4],M5_SEED_SHA))return 2;
    unsigned c=p05_lookup(argv[5],p05_cases,6),mode=p05_lookup(argv[6],m5_modes,7);
    char rom_sha[65],seed_sha[65];sha256_file(argv[1],rom_sha);sha256_file(argv[2],seed_sha);
    m5_need(!strcmp(rom_sha,M5_ROM_SHA) && !strcmp(seed_sha,M5_SEED_SHA),"fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore *core=qol_open(argv[1],argv[2]);qol_log_core=core;
    static color_t video[240*160];core->setVideoBuffer(core,video,240);
    m5_need(p02s_continue_to_field(core,"m5_boot"),"Continue failed");
    m5_flash_prepare(core);
    uint8_t player[POKEMON_SIZE],enemy[POKEMON_SIZE];
    uint16_t pm[4]={p05_player_moves[c],0,0,0},em[4]={p05_enemy_moves[c],0,0,0};
    const uint8_t pp[4]={20,0,0,0};
    create_mon_image(core,m5_bases[c],20,pm,pp,player);
    create_mon_image(core,10,20,em,pp,enemy);
    clear_parties(core);install_mon_image(core,ADDR_PLAYER_PARTY,player);install_mon_image(core,ADDR_ENEMY_PARTY,enemy);
    write8(core,ADDR_PLAYER_PARTY_COUNT,1);write8(core,BATTLE_CORE_ENEMY_PARTY_COUNT,1);
    set_mon_data_u32(core,ADDR_PLAYER_PARTY,12,mode==3?0:(mode==4?m5_stones[(c+1)%6]:m5_stones[c]));
    m5_need(call_preserving(core,QOL_CHECK_BAG_ITEM,580,1,0,0)==0,"seed already contains ring");
    if(mode!=2)m5_need(call_preserving(core,QOL_ADD_BAG_ITEM,580,1,0,0)==1,"ring add failed");
    m5_need(call_preserving(core,M5_CONFIGURE_POLICY,5,mode==5?0:1,0,0)==1,"policy config failed");
    seed_fixture(core);
    (void)call_bounded(core,BATTLE_CORE_START_WILD,0,0,0,0);
    p05_wait_action(core);
    /* Opponent-only pre-input fixture. Native Mega supplies player form,
     * types, stats and ability; those values are never injected here. */
    write16(core,P05_MON(1)+0x28,1000);write16(core,P05_MON(1)+0x2c,1000);
    write16(core,P05_MON(1)+2,20);write16(core,P05_MON(1)+4,200);write16(core,P05_MON(1)+6,c==4?500:5);
    write8(core,P05_MON(1)+0x21,c==0?7:0);write8(core,P05_MON(1)+0x22,c==0?7:0);
    unsigned initial_ability=read16(core,P05_MON(0)+0x38),initial_hp=read16(core,P05_MON(0)+0x28);
    unsigned eligible=call_preserving(core,M5_CAN_MEGA,0,0,0,0)!=0;
    m5_need(eligible==(mode==0 || mode==1 || mode==6),"native Mega eligibility differs");
    m5_need(initial_ability==m5_base_abilities[c] && read16(core,P05_MON(0))==m5_bases[c],"native base form/ability differs");
    uint8_t baseline[100],plain[48];m5_mon_bytes(core,baseline);m5_plain(baseline,plain);
    unsigned growth=99,attack=99,ng=0,na=0;
    for(unsigned i=0;i<4;i++) {
        if(m5_u16(plain+12*i)==m5_bases[c] && m5_u16(plain+12*i+2)==read16(core,P05_MON(0)+0x2e)){growth=12*i;ng++;}
        if(m5_u16(plain+12*i)==p05_player_moves[c] && plain[12*i+8]==20){attack=12*i;na++;}
    }
    m5_need(ng==1 && na==1 && growth!=attack,"native fixture substructure identity invalid");
    struct mCore apis=*core;p05_arm_write_guard(core);
    unsigned select_frame=0,mega_frame=0,spent=0,end=0,returned=0,last_keys=0,toggles=0,last_toggle=0;
    for(unsigned f=1;f<16000;f++) {
        unsigned main=read32(core,P05_MAIN),cmd=read8(core,P05_BUFFER),ctl=read32(core,0x03005020);
        unsigned sp=read16(core,P05_MON(0)),ab=read16(core,P05_MON(0)+0x38),p=read8(core,P05_MON(0)+0x24);
        if(!mega_frame && sp==m5_megas[c]){mega_frame=f;fprintf(stderr,"mega at %u ability=%u\n",f,ab);}
        if(!spent && p==19)spent=f;
        if(main==P05_END_PHASE && !end)end=f;
        if(spent && end && main==P05_ACTION){returned=f;break;}
        if(p==19 && f==spent)fprintf(stderr,"f=%u main=%08x ctl=%08x cmd=%u sp=%u ab=%u pp=%u hp=%u/%u\n",f,main,ctl,cmd,sp,ab,p,read16(core,P05_MON(0)+0x28),read16(core,P05_MON(1)+0x28));
        unsigned keys=0;
        if(f%30==1) {
            if(main==P05_ACTION && cmd==0x14 && (read32(core,P05_EXEC)&1U) && toggles<(mode==6?2U:1U) && mode!=1) {
                keys=QOL_KEY_START;if(!select_frame)select_frame=f;last_toggle=f;toggles++;
            } else keys=QOL_KEY_A;
        }
        if(keys)last_keys=f;
        core->setKeys(core,keys);core->runFrame(core);
    }
    core->setKeys(core,0);
    unsigned final_sp=read16(core,P05_MON(0)),final_ab=read16(core,P05_MON(0)+0x38);
    unsigned php=read16(core,P05_MON(0)+0x28),ehp=read16(core,P05_MON(1)+0x28);
    unsigned player_pp=read8(core,P05_MON(0)+0x24);
    unsigned ep=read8(core,P05_MON(1)+0x24),ps=read32(core,P05_MON(0)+0x4c),es=read32(core,P05_MON(1)+0x4c);
    m5_need(returned && spent && end>spent && returned>end && player_pp==19 && ep==19,"first turn boundary/PP differs");
    m5_need(final_sp==(mode==0?m5_megas[c]:m5_bases[c]) && final_ab==(mode==0?p05_abilities[c]:initial_ability),"native Mega form/ability differs");
    m5_need(mode==0?(select_frame && mega_frame>select_frame && spent>mega_frame):mega_frame==0,"native Mega input ordering differs");
    unsigned flee_frame=0,flee_outcome=0,run_presses=0;
    if(mode==0) {
        unsigned stable=0;
        for(unsigned f=1;f<=10000;f++) {
            unsigned cb=read32(core,BATTLE_CORE_MAIN_CALLBACK2),cur=read8(core,M5_ACTION_CURSOR);
            if(m5_field(core))stable++;else stable=0;
            if(stable>=240){flee_frame=f;flee_outcome=read8(core,BATTLE_CORE_BATTLE_OUTCOME);break;}
            unsigned keys=0;
            if(f%30==1) {
                if(p05_action_ready(core)) {
                    m5_need(cur<=3,"invalid action cursor");keys=cur==3?QOL_KEY_A:((cur&1)?QOL_KEY_DOWN:QOL_KEY_RIGHT);if(cur==3)run_presses++;
                } else keys=QOL_KEY_A;
            }
            if(f%300==1)fprintf(stderr,"exit f=%u cb=%08x cursor=%u outcome=%u\n",f,cb,cur,read8(core,BATTLE_CORE_BATTLE_OUTCOME));
            core->setKeys(core,keys);core->runFrame(core);
        }
        m5_need(stable>=240 && flee_outcome==4 && run_presses>0,"native flee did not return to field");
    }
    unsigned reverted=0,save_counter=0,save_before=0;
    if(mode==0) {
        uint8_t after[100],loaded[100];m5_mon_bytes(core,after);m5_plain(after,plain);
        reverted=m5_u16(plain+growth);
        m5_need(reverted==m5_bases[c] && plain[attack+8]==19 && after[84]==20 && m5_u16(plain+growth+2)==m5_stones[c],"native revert species/PP/level differs");
        m5_need(!memcmp(baseline,after,8),"native battle changed identity");
        save_before=read32(core,0x030053E0U);
        m5_need(m5_save(core),"native save failed");save_counter=read32(core,0x030053E0U);
        m5_mon_bytes(core,after);
        p05_restore_write_apis(core,&apis);mCoreConfigDeinit(&core->config);core->deinit(core);qol_log_core=NULL;
        core=qol_open(argv[1],argv[2]);qol_log_core=core;core->setVideoBuffer(core,video,240);
        m5_flash_prepare(core);apis=*core;p05_arm_write_guard(core);
        m5_need(m5_continue(core),"fresh core Continue failed");m5_mon_bytes(core,loaded);
        m5_need(!memcmp(after,loaded,100) && read32(core,0x030053E0U)==save_counter,"native cold-save byte snapshot mismatch");
        fprintf(stderr,"saved and reloaded species=%u counter=%u\n",reverted,save_counter);
    }
    p05_restore_write_apis(core,&apis);mCoreConfigDeinit(&core->config);core->deinit(core);qol_log_core=NULL;
    sha256_file(argv[1],seed_sha);m5_need(!strcmp(rom_sha,seed_sha),"ROM modified");
    m5_need(log_problem_count==0,"mGBA warnings/errors");
    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\","
        "\"rom_sha256\":\"%s\",\"case\":\"%s\",\"mode\":\"%s\","
        "\"initial_species\":%u,\"initial_ability\":%u,\"final_species\":%u,\"final_ability\":%u,"
        "\"eligible\":%s,\"initial_hp\":%u,\"player_hp\":%u,\"enemy_hp\":%u,"
        "\"player_pp\":%u,\"enemy_pp\":%u,\"player_status\":%u,\"enemy_status\":%u,"
        "\"toggle_first\":%u,\"toggle_last\":%u,\"toggle_count\":%u,\"mega_frame\":%u,"
        "\"spent_frame\":%u,\"end_frame\":%u,\"return_frame\":%u,\"last_key_frame\":%u,"
        "\"flee_frame\":%u,\"flee_outcome\":%u,\"run_presses\":%u,\"reverted_species\":%u,"
        "\"save_counter_before\":%u,\"save_counter_after\":%u,\"cold_core_count\":%u,"
        "\"cold_save_all_100_party_bytes_equal\":%s,\"host_write_guard\":true,"
        "\"player_ability_injected\":false,\"natural_capture_or_facility_entry\":false,"
        "\"full_p05_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0}\n",
        M5_SCOPE,M5_ROM_SHA,p05_cases[c],m5_modes[mode],m5_bases[c],initial_ability,final_sp,final_ab,
        eligible?"true":"false",initial_hp,php,ehp,player_pp,ep,ps,es,select_frame,last_toggle,toggles,mega_frame,
        spent,end,returned,last_keys,flee_frame,flee_outcome,run_presses,reverted,save_before,save_counter,
        mode==0?2:1,mode==0?"true":"false");
    return 0;
}
