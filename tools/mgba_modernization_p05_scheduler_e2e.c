/* P05 real first-turn scheduler acceptance, not natural acquisition/full P05.
 * Native boot and battle construction precede a documented RAM fixture.
 * After the fixture barrier only keys, frames and passive reads are allowed;
 * all seven mCore memory/register write APIs are trapped until observation ends.
 */
#include "p05_p02_embedded.c"

#define P05_MAIN 0x03004FC4U
#define P05_EXEC 0x02023B28U
#define P05_BUFFER 0x02022B24U
#define P05_ACTION 0x08013861U
#define P05_END_PHASE 0x0801333DU
#define P05_CIRCUS_FLAGS 0x0203DFBCU
#define P05_MON(n) (ADDR_BATTLE_MONS + (n) * BATTLE_MON_SIZE)
#define P05_ROM_SHA "6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3"
#define P05_SCOPE "P05_PREINPUT_FIXTURE_REAL_FIRST_TURN_6_ABILITIES"
#define P05_LIMIT 8000U

static const char *p05_cases[] = {
    "dragonize", "eelevate_ground", "fire_mane", "mega_sol",
    "piercing_drill", "spicy_spray", "eelevate_final_ko", "eelevate_remaining_foe_ko"
};
static const char *p05_modes[] = {"absent", "active", "circus"};
static const unsigned p05_abilities[] = {312, 313, 314, 315, 316, 317, 313, 313};
static const uint16_t p05_player_moves[] = {33, 150, 52, 76, 33, 150, 33, 33};
static const uint16_t p05_enemy_moves[] = {150, 89, 150, 150, 182, 33, 150, 150};

static void p05_die(const char *message) {
    fprintf(stderr, "P05 scheduler: %s\n", message);
    exit(1);
}
#define P05_DENY(name, type) \
static void name(struct mCore *c, uint32_t a, type v) { \
    (void)c; (void)a; (void)v; p05_die("host write after fixture barrier"); \
}
P05_DENY(p05_deny8, uint8_t)
P05_DENY(p05_deny16, uint16_t)
P05_DENY(p05_deny32, uint32_t)
#define P05_DENY_RAW(name, type) \
static void name(struct mCore *c, uint32_t a, int s, type v) { \
    (void)s; (void)c; (void)a; (void)v; p05_die("host write after fixture barrier"); \
}
P05_DENY_RAW(p05_deny_raw8, uint8_t)
P05_DENY_RAW(p05_deny_raw16, uint16_t)
P05_DENY_RAW(p05_deny_raw32, uint32_t)
static bool p05_deny_register(struct mCore *c, const char *n, const void *v) {
    (void)c; (void)n; (void)v; p05_die("host write after fixture barrier"); return false;
}
static void p05_arm_write_guard(struct mCore *c) {
    c->busWrite8=p05_deny8; c->busWrite16=p05_deny16; c->busWrite32=p05_deny32;
    c->rawWrite8=p05_deny_raw8; c->rawWrite16=p05_deny_raw16; c->rawWrite32=p05_deny_raw32;
    c->writeRegister=p05_deny_register;
}
static void p05_restore_write_apis(struct mCore *c, const struct mCore *saved) {
    c->busWrite8=saved->busWrite8; c->busWrite16=saved->busWrite16; c->busWrite32=saved->busWrite32;
    c->rawWrite8=saved->rawWrite8; c->rawWrite16=saved->rawWrite16; c->rawWrite32=saved->rawWrite32;
    c->writeRegister=saved->writeRegister;
}
static unsigned p05_lookup(const char *value, const char *const *choices, unsigned size) {
    for (unsigned i=0; i<size; ++i) if (strcmp(value, choices[i])==0) return i;
    p05_die("unknown case/mode"); return 0;
}
static void p05_test_guard(const char *api) {
    struct mCore c={0}; uint32_t value=0;
    p05_arm_write_guard(&c);
    if (!strcmp(api,"bus8")) c.busWrite8(&c,0,0);
    else if (!strcmp(api,"bus16")) c.busWrite16(&c,0,0);
    else if (!strcmp(api,"bus32")) c.busWrite32(&c,0,0);
    else if (!strcmp(api,"raw8")) c.rawWrite8(&c,0,0,0);
    else if (!strcmp(api,"raw16")) c.rawWrite16(&c,0,0,0);
    else if (!strcmp(api,"raw32")) c.rawWrite32(&c,0,0,0);
    else if (!strcmp(api,"register")) (void)c.writeRegister(&c,"pc",&value);
    exit(2); /* unknown/untrapped API is NOT the expected negative result */
}
static bool p05_action_ready(struct mCore *core) {
    return read32(core,P05_MAIN)==P05_ACTION && (read32(core,P05_EXEC)&1U)
        && read8(core,P05_BUFFER)==0x12U;
}
static void p05_wait_action(struct mCore *core) {
    for (unsigned f=0; f<P05_LIMIT; ++f) {
        if (p05_action_ready(core)) { core->setKeys(core,0); return; }
        core->setKeys(core,(f%30U<2U)?1U:0U); core->runFrame(core);
    }
    p05_die("first action menu timeout");
}
static void p05_double_fixture(struct mCore *core, const uint16_t moves[4], const uint8_t pp[4]) {
    uint8_t images[4][POKEMON_SIZE];
    const uint16_t splash[4]={150,0,0,0};
    const uint16_t species[4]={4,10,7,11};
    for (unsigned b=0; b<4; ++b)
        create_mon_image(core,species[b],20,b?splash:moves,pp,images[b]);
    clear_parties(core);
    install_mon_image(core,ADDR_PLAYER_PARTY,images[0]);
    install_mon_image(core,ADDR_PLAYER_PARTY+POKEMON_SIZE,images[2]);
    install_mon_image(core,ADDR_ENEMY_PARTY,images[1]);
    install_mon_image(core,ADDR_ENEMY_PARTY+POKEMON_SIZE,images[3]);
    write8(core,ADDR_PLAYER_PARTY_COUNT,2); write8(core,BATTLE_CORE_ENEMY_PARTY_COUNT,2);
    seed_fixture(core);
    struct CallObservation entry=call_bounded(core,BATTLE_CORE_START_WILD,0,0,0,0);
    if (!entry.payload_pc_seen) p05_die("native double battle entry did not execute payload");
    write32_bytes(core,ADDR_BATTLE_TYPE_FLAGS,read32(core,ADDR_BATTLE_TYPE_FLAGS)|BATTLE_TYPE_DOUBLE);
    run_key_frames(core,0,BATTLE_CORE_MENU_READY_FRAMES);
}
static void p05_install_fixture(struct mCore *core, const struct Snapshot *field, unsigned c, unsigned mode) {
    uint16_t pm[4]={p05_player_moves[c],0,0,0}, em[4]={p05_enemy_moves[c],0,0,0};
    uint8_t pp[4]={20,0,0,0};
    if (c==7) p05_double_fixture(core,pm,pp);
    else (void)setup_custom_wild(core,field,4,10,pm,pp,em,pp);
    p05_wait_action(core);
    unsigned count=c==7?4U:2U;
    if (read8(core,ADDR_BATTLERS_COUNT)!=count) p05_die("wrong battler count");
    for (unsigned b=0; b<count; ++b) {
        write16(core,P05_MON(b)+2,100); write16(core,P05_MON(b)+4,100);
        write16(core,P05_MON(b)+6,b?50:200); write16(core,P05_MON(b)+8,100); write16(core,P05_MON(b)+10,100);
        write16(core,P05_MON(b)+0x28,500); write16(core,P05_MON(b)+0x2c,500);
        write16(core,P05_MON(b)+0x38,0); write16(core,P05_MON(b)+0x2e,0);
        write8(core,P05_MON(b)+0x21,0); write8(core,P05_MON(b)+0x22,0);
        write32_bytes(core,P05_MON(b)+0x4c,0); write32_bytes(core,P05_MON(b)+0x50,0);
        for (unsigned s=0; s<8; ++s) write8(core,P05_MON(b)+0x18+s,6);
    }
    write16(core,P05_MON(0)+0x38,mode?p05_abilities[c]:0);
    if (c==0) { write8(core,P05_MON(1)+0x21,7); write8(core,P05_MON(1)+0x22,7); }
    if (c>=6) { write16(core,P05_MON(1)+0x28,1); write16(core,P05_MON(0)+2,300); }
    if (mode==2) {
        write32_bytes(core,ADDR_BATTLE_TYPE_FLAGS,read32(core,ADDR_BATTLE_TYPE_FLAGS)|0x04000000U);
        write32_bytes(core,P05_CIRCUS_FLAGS,0x80000000U);
    }
    if (read16(core,P05_MON(0)+0x0c)!=p05_player_moves[c]
        || read16(core,P05_MON(1)+0x0c)!=p05_enemy_moves[c]
        || read8(core,P05_MON(0)+0x24)!=20 || read8(core,P05_MON(1)+0x24)!=20)
        p05_die("move/PP fixture readback failed");
}
struct P05Observation {
    unsigned frames, presses, player_hp, enemy_hp, player_pp, enemy_pp, player_status, enemy_status;
    unsigned attack_stage, ability, outcome, remaining_foe_hp, remaining_foe_pp, partner_pp;
    bool end_phase;
};
/* Observation phase: deliberately NO fixture calls, snapshots, memory writes,
 * ROM direct calls, callbacks, PC writes, or cursor/state forcing here. */
static struct P05Observation p05_observe_turn(struct mCore *core, unsigned c) {
    struct P05Observation o={0};
    unsigned last_main=0, last_hp=500, last_pp=20, last_stage=6, previous_keys=0;
    for (o.frames=0; o.frames<P05_LIMIT; ++o.frames) {
        uint32_t main=read32(core,P05_MAIN);
        unsigned hp=read16(core,P05_MON(1)+0x28), pp=read8(core,P05_MON(0)+0x24);
        unsigned stage=read8(core,P05_MON(0)+0x19);
        if (main!=last_main || hp!=last_hp || pp!=last_pp || stage!=last_stage) {
            fprintf(stderr,"frame=%u main=%08x hp=%u/%u pp=%u/%u attack_stage=%u\n",
                o.frames,main,read16(core,P05_MON(0)+0x28),hp,pp,read8(core,P05_MON(1)+0x24),stage);
            last_main=main; last_hp=hp; last_pp=pp; last_stage=stage;
        }
        if (main==P05_END_PHASE) o.end_phase=true;
        /* Stop before the next runFrame, even for a charge-locked Solar Beam.
         * Requiring another ChooseAction command incorrectly executes turn 2. */
        if (pp==19 && o.end_phase && main==P05_ACTION) break;
        if (read8(core,BATTLE_CORE_BATTLE_OUTCOME)) break;
        unsigned keys=(o.frames%30U<2U && (main==P05_ACTION || o.frames%90U<2U))?1U:0U;
        if (keys && !previous_keys) ++o.presses;
        previous_keys=keys; core->setKeys(core,keys); core->runFrame(core);
    }
    core->setKeys(core,0);
    o.player_hp=read16(core,P05_MON(0)+0x28); o.enemy_hp=read16(core,P05_MON(1)+0x28);
    o.player_pp=read8(core,P05_MON(0)+0x24); o.enemy_pp=read8(core,P05_MON(1)+0x24);
    o.player_status=read32(core,P05_MON(0)+0x4c); o.enemy_status=read32(core,P05_MON(1)+0x4c);
    o.attack_stage=read8(core,P05_MON(0)+0x19); o.ability=read16(core,P05_MON(0)+0x38);
    o.outcome=read8(core,BATTLE_CORE_BATTLE_OUTCOME);
    if (c==7) {
        o.remaining_foe_hp=read16(core,P05_MON(3)+0x28);
        o.remaining_foe_pp=read8(core,P05_MON(3)+0x24); o.partner_pp=read8(core,P05_MON(2)+0x24);
    }
    if (o.frames==P05_LIMIT || !o.presses || o.player_pp!=19) p05_die("first turn did not finish");
    if (c==6 ? o.outcome!=BATTLE_CORE_OUTCOME_WON : (!o.end_phase || o.outcome))
        p05_die("wrong turn/victory boundary");
    return o;
}
int main(int argc, char **argv) {
    if (argc==3 && !strcmp(argv[1],"--guard-check")) p05_test_guard(argv[2]);
    if (argc!=6 || strcmp(argv[3],P05_ROM_SHA)) return 2;
    unsigned c=p05_lookup(argv[4],p05_cases,ARRAY_LEN(p05_cases));
    unsigned mode=p05_lookup(argv[5],p05_modes,ARRAY_LEN(p05_modes));
    struct mLogger logger={.log=qol_log,.filter=NULL}; mLogSetDefaultLogger(&logger);
    struct mCore *core=qol_open(argv[1],argv[2]); qol_log_core=core;
    static color_t video[240*160]; core->setVideoBuffer(core,video,240);
    if (!p02s_continue_to_field(core,"p05_boot")) p05_die("normal Continue failed");
    struct Snapshot field=take_snapshot(core);
    p05_install_fixture(core,&field,c,mode);
    fprintf(stderr,"fixture sealed: case=%s mode=%s; host writes trapped\n",p05_cases[c],p05_modes[mode]);
    struct mCore saved_apis=*core;
    p05_arm_write_guard(core);
    struct P05Observation o=p05_observe_turn(core,c);
    p05_restore_write_apis(core,&saved_apis);
    free(field.bytes); qol_close(core); qol_log_core=NULL;
    if (log_problem_count) p05_die("emulator warnings/errors");
    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\","
        "\"rom_sha256\":\"%s\",\"case\":\"%s\",\"mode\":\"%s\","
        "\"ability_id\":%u,\"ability_after\":%u,\"player_move\":%u,\"enemy_move\":%u,"
        "\"battlers\":%u,\"frames\":%u,\"key_presses\":%u,"
        "\"player_hp\":%u,\"enemy_hp\":%u,\"player_pp\":%u,\"enemy_pp\":%u,"
        "\"player_status\":%u,\"enemy_status\":%u,\"attack_stage\":%u,"
        "\"remaining_foe_hp\":%u,\"remaining_foe_pp\":%u,\"partner_pp\":%u,"
        "\"end_phase_seen\":%s,\"battle_outcome\":%u,"
        "\"fixture_boundary\":\"PRE_FIRST_ACTION\",\"host_write_guard\":true,"
        "\"normal_battle_input\":true,\"full_p05_acceptance\":false,\"release_ready\":false,"
        "\"warnings_errors\":0}\n",
        P05_SCOPE,P05_ROM_SHA,p05_cases[c],p05_modes[mode],p05_abilities[c],o.ability,
        p05_player_moves[c],p05_enemy_moves[c],c==7?4U:2U,o.frames,o.presses,
        o.player_hp,o.enemy_hp,o.player_pp,o.enemy_pp,o.player_status,o.enemy_status,o.attack_stage,
        o.remaining_foe_hp,o.remaining_foe_pp,o.partner_pp,o.end_phase?"true":"false",o.outcome);
    return 0;
}
