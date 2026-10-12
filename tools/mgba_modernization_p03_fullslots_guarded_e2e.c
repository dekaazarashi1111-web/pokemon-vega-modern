/* Full-slot P03 learning UI and persistence. The mon/item are a pre-input
 * fixture. Learning itself uses only keys, frames and reads; seven mCore
 * host-write APIs are trapped across the entire learning/evolution scene.
 * Existing P03/P02 sources remain unmodified and are separately bound. */
#include "p03f_learning_embedded.c"

#define P03F_ROM_SHA "6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3"
#define P03F_FIXED_SHA "521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579"
#define P03F_SAVE_SHA "2ee9436a43e64225ec7940e29057f8dee423f00345a41ea5cd833c449841cd13"
#define P03F_SCOPE "P03_FULLSLOTS_GUARDED_UI_SAVE_RELOAD_REPRESENTATIVE"
#define P03F_ASK 0x08126705U
#define P03F_STOP 0x08126AB9U
#define P03F_SUMMARY 0x0813868DU
#define P03F_SELECT 0x08139BA9U
#define P03F_REPLACED 0x081269C5U
#define P03F_PP_BONUSES 21U

static const char *const p03f_modes[] = {
    "replace-0", "replace-1", "replace-2", "replace-3",
    "refuse", "cancel-selection", "below-level", "empty-learn", "empty-below-level"
};
static const uint16_t p03f_before_moves[4] = {33U,81U,45U,52U};
static const uint8_t p03f_before_pp[4] = {7U,8U,9U,10U};

_Noreturn static void p03f_die(const char *message) {
    fprintf(stderr,"P03 fullslots: %s\n",message); exit(1);
}
static void p03f_require(bool value, const char *message) {
    if (!value) p03f_die(message);
}
#define P03F_DENY(name,type) \
static void name(struct mCore *c,uint32_t a,type v) { \
    (void)c; (void)a; (void)v; p03f_die("host write after learning barrier"); \
}
P03F_DENY(p03f_deny8,uint8_t)
P03F_DENY(p03f_deny16,uint16_t)
P03F_DENY(p03f_deny32,uint32_t)
#define P03F_DENY_RAW(name,type) \
static void name(struct mCore *c,uint32_t a,int s,type v) { \
    (void)c; (void)a; (void)s; (void)v; p03f_die("host write after learning barrier"); \
}
P03F_DENY_RAW(p03f_deny_raw8,uint8_t)
P03F_DENY_RAW(p03f_deny_raw16,uint16_t)
P03F_DENY_RAW(p03f_deny_raw32,uint32_t)
static bool p03f_deny_register(struct mCore *c,const char *n,const void *v) {
    (void)c; (void)n; (void)v; p03f_die("host write after learning barrier");
}
static void p03f_guard(struct mCore *c) {
    c->busWrite8=p03f_deny8; c->busWrite16=p03f_deny16; c->busWrite32=p03f_deny32;
    c->rawWrite8=p03f_deny_raw8; c->rawWrite16=p03f_deny_raw16; c->rawWrite32=p03f_deny_raw32;
    c->writeRegister=p03f_deny_register;
}
static void p03f_unguard(struct mCore *c,const struct mCore *saved) {
    c->busWrite8=saved->busWrite8; c->busWrite16=saved->busWrite16; c->busWrite32=saved->busWrite32;
    c->rawWrite8=saved->rawWrite8; c->rawWrite16=saved->rawWrite16; c->rawWrite32=saved->rawWrite32;
    c->writeRegister=saved->writeRegister;
}
static void p03f_guard_test(const char *api) {
    struct mCore c={0}; uint32_t value=0; p03f_guard(&c);
    if (!strcmp(api,"bus8")) c.busWrite8(&c,0,0);
    else if (!strcmp(api,"bus16")) c.busWrite16(&c,0,0);
    else if (!strcmp(api,"bus32")) c.busWrite32(&c,0,0);
    else if (!strcmp(api,"raw8")) c.rawWrite8(&c,0,0,0);
    else if (!strcmp(api,"raw16")) c.rawWrite16(&c,0,0,0);
    else if (!strcmp(api,"raw32")) c.rawWrite32(&c,0,0,0);
    else if (!strcmp(api,"register")) (void)c.writeRegister(&c,"pc",&value);
    exit(2);
}
static bool p03f_task(struct mCore *core,uint32_t function) {
    for (unsigned i=0;i<16;++i) {
        uint32_t task=QOL_TASKS+i*QOL_TASK_SIZE;
        if (read8(core,task+4U) && read32(core,task)==function) return true;
    }
    return false;
}
/* No native getter calls here: even a preserved ROM call writes CPU/RAM. */
static bool p03f_field_passive(struct mCore *core) {
    uint8_t id=read8(core,P02S_PLAYER_AVATAR+5U);
    return read32(core,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD
        && p02s_continue_position(core) && read8(core,P02S_FIELD_LOCK)==0U
        && read8(core,P02S_QUEST_LOG_STATE)==0U
        && read8(core,P02S_QUEST_LOG_PLAYBACK_STATE)==0U
        && id<16U && (read8(core,P02S_OBJECT_EVENTS+id*0x24U)&1U)
        && read8(core,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET)==0U
        && read8(core,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET)==0U;
}
struct P03FTrace {
    unsigned frames,downs,selection_presses,evolution_b_presses;
    unsigned ask_frame,summary_frame,stop_frame,replaced_frame,begin_frame,update_frame,field_frame;
};
static struct P03FTrace p03f_scene(struct mCore *core,unsigned mode) {
    struct P03FTrace t={0}; unsigned stable=0,held=0,last_cb=0;
    for (unsigned f=0;f<P02S_MAX_SCENE_FRAMES;++f) {
        uint32_t cb=read32(core,BATTLE_CORE_MAIN_CALLBACK2);
        bool ask=cb==P02S_CB2_PARTY && p03f_task(core,P03F_ASK);
        bool stop=cb==P02S_CB2_PARTY && p03f_task(core,P03F_STOP);
        bool select=cb==P03F_SUMMARY && p03f_task(core,P03F_SELECT);
        if (ask && !t.ask_frame) t.ask_frame=f+1U;
        if (select && !t.summary_frame) t.summary_frame=f+1U;
        if (stop && !t.stop_frame) t.stop_frame=f+1U;
        if (cb==P02S_CB2_PARTY && p03f_task(core,P03F_REPLACED) && !t.replaced_frame)
            t.replaced_frame=f+1U;
        if (cb==P02S_CB2_EVOLUTION_BEGIN && !t.begin_frame) t.begin_frame=f+1U;
        if (cb==P02S_CB2_EVOLUTION_UPDATE && !t.update_frame) t.update_frame=f+1U;
        if (cb!=last_cb) {
            fprintf(stderr,"P03F frame=%u callback=%08x\n",f,cb); last_cb=cb;
        }
        if (t.update_frame && p03f_field_passive(core)) {
            if (++stable>=120U) { t.field_frame=f+1U; t.frames=f+1U; core->setKeys(core,0); return t; }
        } else stable=0;
        if (f%120U==0U) {
            held=QOL_KEY_A;
            if (cb==P02S_CB2_EVOLUTION_UPDATE) { held=QOL_KEY_B; ++t.evolution_b_presses; }
            else if (t.begin_frame && (cb==P02S_CB2_PARTY || cb==P02S_CB2_BAG || cb==P02S_CB2_FIELD))
                held=QOL_KEY_B;
            else if (ask) held=mode==4U?QOL_KEY_B:QOL_KEY_A;
            else if (stop) held=QOL_KEY_A;
            else if (select) {
                if (mode<4U && t.downs<mode) { held=QOL_KEY_DOWN; ++t.downs; }
                else { held=mode==5U?QOL_KEY_B:QOL_KEY_A; ++t.selection_presses; }
            }
        }
        core->setKeys(core,f%120U<2U?held:0U); core->runFrame(core);
    }
    core->setKeys(core,0); p03f_die("learning scene timeout");
}
static void p03f_read_slots(struct mCore *core,uint16_t moves[4],uint8_t pp[4]) {
    for (unsigned i=0;i<4;++i) {
        moves[i]=(uint16_t)p02s_data(core,QOL_MON_DATA_MOVE1+i);
        pp[i]=(uint8_t)p02s_data(core,MON_DATA_PP1+i);
    }
}
static void p03f_array16(const uint16_t a[4]) { printf("[%u,%u,%u,%u]",a[0],a[1],a[2],a[3]); }
static void p03f_array8(const uint8_t a[4]) { printf("[%u,%u,%u,%u]",a[0],a[1],a[2],a[3]); }
int main(int argc,char **argv) {
    if (argc==3 && !strcmp(argv[1],"--guard-check")) p03f_guard_test(argv[2]);
    if (argc!=6 || (strcmp(argv[3],P03F_ROM_SHA) && strcmp(argv[3],P03F_FIXED_SHA)) || strcmp(argv[4],P03F_SAVE_SHA)) return 2;
    unsigned mode=9;
    for (unsigned i=0;i<9;++i) if (!strcmp(argv[5],p03f_modes[i])) mode=i;
    if (mode==9) return 2;
    char rom_sha[65],save_sha[65]; sha256_file(argv[1],rom_sha); sha256_file(argv[2],save_sha);
    p03f_require(!strcmp(rom_sha,argv[3]) && !strcmp(save_sha,P03F_SAVE_SHA),"input identity mismatch");
    struct mLogger logger={.log=qol_log,.filter=NULL}; mLogSetDefaultLogger(&logger);
    struct mCore *core=qol_open(argv[1],argv[2]); qol_log_core=core;
    static color_t video[240U*160U]; core->setVideoBuffer(core,video,240U);
    p03f_require(p02s_continue_to_field(core,"p03f_initial"),"initial Continue failed");
    p03f_require(p02s_install_field_fixture(core),"field fixture failed"); p02s_enable_national_dex(core);
    unsigned initial_level=(mode==6U || mode==8U)?7U:8U;
    int replaced_slot=mode<4U?(int)mode:(mode==7U?2:-1);
    clear_parties(core); create_mon(core,QOL_PLAYER_PARTY,649U,(uint8_t)initial_level);
    write8(core,QOL_PLAYER_PARTY_COUNT,1U);
    for (unsigned i=0;i<4;++i) {
        p02s_set_data(core,QOL_MON_DATA_MOVE1+i,mode>=7U && i>=2U?0U:p03f_before_moves[i]);
        p02s_set_data(core,MON_DATA_PP1+i,mode>=7U && i>=2U?0U:p03f_before_pp[i]);
    }
    p03f_require(p02s_data(core,P03F_PP_BONUSES)==0U,"fixture has PP Ups");
    uint16_t before[4],after[4],loaded[4]; uint8_t before_pp[4],after_pp[4],loaded_pp[4];
    p03f_read_slots(core,before,before_pp);
    for (unsigned i=0;i<4;++i)
        p03f_require(before[i]==(mode>=7U && i>=2U?0U:p03f_before_moves[i])
            && before_pp[i]==(mode>=7U && i>=2U?0U:p03f_before_pp[i]),"fixture slots differ");
    p02s_prepare_item(core,P02S_ITEM_RARE_CANDY);
    p03f_require(p02s_data(core,QOL_MON_DATA_LEVEL)==initial_level,"fixture level differs");
    uint32_t table=read32(core,BATTLE_CORE_MOVE_TABLE_REPOINT);
    p03f_require(table>=0x08000000U && table<0x09FFE000U,"move table invalid");
    unsigned canonical_pp=read8(core,table+535U*BATTLE_CORE_BATTLE_MOVE_SIZE+4U);
    p03f_require(canonical_pp>0U && canonical_pp<=64U,"canonical PP invalid");
    p03f_require(p02s_enter_item_party(core,P02S_ITEM_RARE_CANDY,"p03f_party"),"normal Bag/Party input failed");
    struct mCore saved_apis=*core; p03f_guard(core);
    struct P03FTrace t=p03f_scene(core,mode);
    p03f_unguard(core,&saved_apis);
    p03f_require(t.begin_frame && t.update_frame && t.evolution_b_presses && t.field_frame,"evolution cancellation missing");
    p03f_require((t.ask_frame!=0U)==(mode<6U),"learning prompt differs");
    p03f_require((t.summary_frame!=0U)==(mode<4U || mode==5U),"summary selection route differs");
    p03f_require((t.stop_frame!=0U)==(mode==4U || mode==5U),"refusal confirmation route differs");
    p03f_require((t.replaced_frame!=0U)==(mode<4U),"native replacement route differs");
    p03f_require(t.downs==(mode<4U?mode:0U) && t.selection_presses==(mode<4U || mode==5U?1U:0U),"selection input differs");
    p03f_read_slots(core,after,after_pp);
    for (unsigned i=0;i<4;++i) {
        p03f_require(after[i]==(replaced_slot==(int)i?535U:before[i]),"wrong move/slot after input");
        p03f_require(replaced_slot==(int)i?(after_pp[i]>0U && after_pp[i]<=64U):after_pp[i]==before_pp[i],"retained PP changed or learned PP invalid");
    }
    p03f_require(p02s_data(core,P03F_PP_BONUSES)==0U && p02s_data(core,QOL_MON_DATA_LEVEL)==initial_level+1U
        && p02s_data(core,P02S_MON_DATA_SPECIES2)==649U && p02s_bag_exact(core,P02S_ITEM_RARE_CANDY,0U),"mon/item boundary differs");
    p03f_require(p02s_wait_input_ready_field(core) && p03_menu_save(core),"normal menu save failed");
    uint32_t counter=read32(core,P03_SAVE_COUNTER);
    qol_close(core); core=NULL; qol_log_core=NULL;
    core=qol_open(argv[1],argv[2]); qol_log_core=core; core->setVideoBuffer(core,video,240U);
    p03f_require(p02s_continue_to_field(core,"p03f_fresh"),"fresh-core Continue failed");
    p03f_read_slots(core,loaded,loaded_pp);
    p03f_require(!memcmp(loaded,after,sizeof(after)) && !memcmp(loaded_pp,after_pp,sizeof(after_pp))
        && p02s_data(core,P03F_PP_BONUSES)==0U && p02s_data(core,P02S_MON_DATA_SPECIES2)==649U
        && p02s_data(core,QOL_MON_DATA_LEVEL)==initial_level+1U && p02s_bag_exact(core,P02S_ITEM_RARE_CANDY,0U)
        && read32(core,P03_SAVE_COUNTER)==counter,"fresh-core persistence differs");
    qol_close(core); qol_log_core=NULL; sha256_file(argv[1],save_sha);
    p03f_require(!strcmp(save_sha,rom_sha) && log_problem_count==0U,"ROM mutation or mGBA warning/error");
    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\",\"mode\":\"%s\","
        "\"rom_sha256\":\"%s\",\"private_save_initial_sha256\":\"%s\",\"species\":649,"
        "\"initial_level\":%u,\"final_level\":%u,\"canonical_move_pp\":%u,\"before_moves\":",P03F_SCOPE,argv[5],rom_sha,P03F_SAVE_SHA,initial_level,initial_level+1U,canonical_pp);
    p03f_array16(before); printf(",\"before_pp\":"); p03f_array8(before_pp);
    printf(",\"after_moves\":"); p03f_array16(after); printf(",\"after_pp\":"); p03f_array8(after_pp);
    printf(",\"reloaded_moves\":"); p03f_array16(loaded); printf(",\"reloaded_pp\":"); p03f_array8(loaded_pp);
    printf(",\"trace\":{\"frames\":%u,\"down_presses\":%u,\"selection_presses\":%u,\"evolution_b_presses\":%u,"
        "\"ask_frame\":%u,\"summary_frame\":%u,\"stop_frame\":%u,\"replaced_frame\":%u,"
        "\"begin_frame\":%u,\"update_frame\":%u,\"field_frame\":%u},"
        "\"host_write_guard\":true,\"host_write_guard_phase\":\"LEARNING_SCENE\","
        "\"normal_bag_party_input\":true,\"normal_save_menu\":true,\"fresh_core_normal_continue\":true,"
        "\"breeding_e2e\":false,\"full_p03_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0}\n",
        t.frames,t.downs,t.selection_presses,t.evolution_b_presses,t.ask_frame,t.summary_frame,t.stop_frame,t.replaced_frame,t.begin_frame,t.update_frame,t.field_frame);
    return 0;
}
