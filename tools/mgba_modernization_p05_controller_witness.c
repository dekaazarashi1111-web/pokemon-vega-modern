/* P05 representative scheduler coverage, not full P05 acceptance.
 * Fixture boundary: native new-game field and native wild-battle setup; explicit
 * BattleMon ability/type/HP overrides BEFORE observation starts. Thereafter the
 * host only reads state, advances frames and sends keys. It never calls a ROM
 * function, writes memory, restores snapshots, or supplies engine stubs while
 * observing the turn. Species acquisition, Mega activation and save are NOT
 * covered by this isolated ability-mechanism fixture.
 */
#define BATTLE_CORE_EMBEDDED
#if defined(__GNUC__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "mgba_battle_core_smoke.c"
#if defined(__GNUC__)
#pragma GCC diagnostic pop
#endif
#include "modernization_p05_turn_observer.h"

enum {
    P05_G_BATTLE_MAIN = 0x03004FC4,
    P05_G_CONTROLLERS = 0x03005020,
    P05_G_EXEC_FLAGS = 0x02023B28,
    P05_G_BUFFER_A = 0x02022B24,
    P05_MAIN_SELECTION = 0x08013861,
    P05_ACTION_STOCK = 0x0802DC15,
    P05_ACTION_CFRU = 0x09118B85,
    P05_MOVE_STOCK = 0x0802E1ED,
    P05_MOVE_CFRU = 0x09116E59,
    P05_CURRENT_MOVE = 0x02023CAA,
    P05_ATTACKER = 0x02023CCB,
    P05_RESULT_FLAGS = 0x02023D2C,
    P05_ABILITY_OFFSET = 0x38,
    P05_TYPE_GHOST = 7,
    P05_TYPE_WATER = 11,
    P05_ABILITY_DRAGONIZE = 312,
    P05_TURN_LIMIT = 18000,
    P05_READY_LIMIT = 12000,
};
struct P05Scenario { const char *name; uint16_t ability; uint8_t target_type; bool hit; };
static const struct P05Scenario P05_CASES[] = {
    {"dragonize_ghost", P05_ABILITY_DRAGONIZE, P05_TYPE_GHOST, true},
    {"no_ability_ghost", 0, P05_TYPE_GHOST, false},
    {"no_ability_normal", 0, 0, true},
    {"dragonize_normal", P05_ABILITY_DRAGONIZE, 0, true},
};
static struct P05TurnSample p05_sample(struct mCore *core, uint32_t frame)
{
    struct P05TurnSample s = {0};
    s.frame = frame;
    s.warnings = log_problem_count;
    s.battle_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    s.count = read8(core, ADDR_BATTLERS_COUNT);
    s.absent = read8(core, ADDR_ABSENT_BATTLER_FLAGS);
    s.outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    s.attacker = read8(core, P05_ATTACKER);
    s.current_move = read16(core, P05_CURRENT_MOVE);
    s.result_flags = read8(core, P05_RESULT_FLAGS);
    s.chosen_move = read16(core, BATTLE_CORE_CHOSEN_MOVES);
    s.chosen_action = read8(core, BATTLE_CORE_CHOSEN_ACTIONS);
    uint32_t controller = read32(core, P05_G_CONTROLLERS);
    bool active = (read32(core, P05_G_EXEC_FLAGS) & 1U) != 0;
    bool selecting = read32(core, P05_G_BATTLE_MAIN) == P05_MAIN_SELECTION;
    uint8_t command = read8(core, P05_G_BUFFER_A);
    s.action_ready = active && selecting && command == 0x12
        && (controller == P05_ACTION_STOCK || controller == P05_ACTION_CFRU);
    s.move_ready = active && selecting && command == 0x14
        && (controller == P05_MOVE_STOCK || controller == P05_MOVE_CFRU);
    for (unsigned b = 0; b < 2; ++b) {
        uint32_t mon = ADDR_BATTLE_MONS + b * BATTLE_MON_SIZE;
        s.species[b] = read16(core, mon);
        s.moves[b] = read16(core, mon + BATTLE_MON_MOVES_OFFSET);
        s.abilities[b] = read16(core, mon + P05_ABILITY_OFFSET);
        s.hp[b] = read16(core, mon + BATTLE_CORE_MON_HP);
        s.pp[b] = read8(core, mon + BATTLE_MON_PP_OFFSET);
        s.types[b][0] = read8(core, mon + BATTLE_CORE_MON_TYPE1);
        s.types[b][1] = read8(core, mon + BATTLE_CORE_MON_TYPE2);
    }
    return s;
}
static void p05_wait_action(struct mCore *core)
{
    for (uint32_t frame = 0; frame < P05_READY_LIMIT; ++frame) {
        struct P05TurnSample s = p05_sample(core, frame);
        if (s.warnings || s.outcome)
            battle_core_die("P05 battle failed before action selection");
        if (s.action_ready) { core->setKeys(core, 0); return; }
        /* Acknowledge introduction/text only; the observed turn has not begun. */
        core->setKeys(core, frame % 30U == 0 ? 1U : 0U);
        core->runFrame(core);
    }
    battle_core_die("P05 did not reach the ordinary action controller");
}
static void p05_fixture(struct mCore *core, const struct Snapshot *field,
                        const struct P05Scenario *scenario)
{
    const uint16_t player_moves[4] = {33, 0, 0, 0};
    const uint8_t player_pp[4] = {35, 0, 0, 0};
    const uint16_t enemy_moves[4] = {150, 0, 0, 0};
    const uint8_t enemy_pp[4] = {40, 0, 0, 0};
    (void)setup_custom_wild(core, field, 1, 1,
        player_moves, player_pp, enemy_moves, enemy_pp);
    p05_wait_action(core);
    uint32_t battle_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    fprintf(stderr, "P05 native setup flags=%08" PRIx32 " count=%u\n",
            battle_flags, read8(core, ADDR_BATTLERS_COUNT));
    if (!p05_ordinary_single_wild(battle_flags))
        battle_core_die("P05 fixture is not an ordinary single wild battle");
    /* Isolated mechanism fixture, NOT a species/ability-allocation assertion. */
    for (unsigned b = 0; b < 2; ++b) {
        uint32_t mon = ADDR_BATTLE_MONS + b * BATTLE_MON_SIZE;
        write16(core, mon + 0x02, 40); /* attack */
        write16(core, mon + 0x04, 80); /* defense */
        write16(core, mon + 0x06, b == 0 ? 100 : 10); /* speed */
        write16(core, mon + 0x28, 1000); /* HP */
        write16(core, mon + 0x2C, 1000); /* max HP */
        write16(core, mon + 0x2E, 0); /* no held item */
        write16(core, mon + P05_ABILITY_OFFSET, b == 0 ? scenario->ability : 0);
        uint8_t type = b == 0 ? P05_TYPE_WATER : scenario->target_type;
        write8(core, mon + BATTLE_CORE_MON_TYPE1, type);
        write8(core, mon + BATTLE_CORE_MON_TYPE2, type);
        write32_bytes(core, mon + BATTLE_CORE_MON_STATUS1, 0);
        write32_bytes(core, mon + BATTLE_CORE_MON_STATUS2, 0);
    }
    write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR, 0);
    write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
    seed_fixture(core);
}
/* Auditable boundary: no writes or direct calls in this function. */
static struct P05TurnObserver p05_observe_turn(struct mCore *core,
    const struct P05Scenario *scenario, struct P05TurnSample *last)
{
    struct P05TurnSample initial = p05_sample(core, 0);
    struct P05TurnObserver observer;
    p05_turn_init(&observer, &initial, scenario->hit, P05_TURN_LIMIT);
    uint32_t last_press = 0;
    struct P05TurnSample previous = initial;
    for (uint32_t frame = 1; frame <= P05_TURN_LIMIT + 1U; ++frame) {
        *last = p05_sample(core, frame);
        if (frame == 1 || frame % 300U == 0
            || last->action_ready != previous.action_ready
            || last->move_ready != previous.move_ready
            || last->pp[0] != previous.pp[0] || last->pp[1] != previous.pp[1]
            || last->hp[1] != previous.hp[1]) {
            fprintf(stderr, "P05 sample frame=%u action=%d move_ui=%d "
                "pp=%u/%u hp=%u/%u move=%u attacker=%u flags=%u "
                "controller=%08" PRIx32 " main=%08" PRIx32 "\n",
                frame, last->action_ready, last->move_ready,
                last->pp[0], last->pp[1], last->hp[0], last->hp[1],
                last->current_move, last->attacker, last->result_flags,
                read32(core, P05_G_CONTROLLERS), read32(core, P05_G_BATTLE_MAIN));
        }
        previous = *last;
        enum P05TurnState state = p05_turn_observe(&observer, last);
        if (state != P05_TURN_RUNNING) break;
        bool selection = last->action_ready || last->move_ready;
        bool can_press = selection ? !observer.player_spent_frame : true;
        uint16_t keys = 0;
        if (can_press && (last_press == 0 || frame - last_press >= 30U)) {
            keys = 1;
            last_press = frame;
        }
        core->setKeys(core, keys);
        core->runFrame(core);
    }
    core->setKeys(core, 0);
    return observer;
}
static void p05_print_sample(const struct P05TurnSample *s)
{
    printf("{\"frame\":%u,\"battle_flags\":%u,\"pp\":[%u,%u],\"hp\":[%u,%u],"
           "\"abilities\":[%u,%u],\"types\":[[%u,%u],[%u,%u]]}",
           s->frame, s->battle_flags, s->pp[0], s->pp[1], s->hp[0], s->hp[1],
           s->abilities[0], s->abilities[1],
           s->types[0][0], s->types[0][1], s->types[1][0], s->types[1][1]);
}
int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256 CASE\n", argv[0]);
        return 2;
    }
    const struct P05Scenario *scenario = NULL;
    for (unsigned i = 0; i < ARRAY_LEN(P05_CASES); ++i)
        if (strcmp(P05_CASES[i].name, argv[3]) == 0) scenario = &P05_CASES[i];
    if (!scenario) battle_core_die("unknown P05 scheduler case");
    char before[65], after[65];
    sha256_file(argv[1], before);
    if (strlen(argv[2]) != 64 || strcmp(before, argv[2]) != 0)
        battle_core_die("P05 ROM identity mismatch");
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                            .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) battle_core_die("P05 core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) battle_core_die("P05 ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    uint32_t table = read32(core, BATTLE_CORE_MOVE_TABLE_REPOINT);
    if (table != 0x090421F4U || read8(core, table + 33U * 12U + 2U) != 0
        || read8(core, table + 33U * 12U + 1U) == 0
        || read8(core, table + 150U * 12U + 1U) != 0)
        battle_core_die("P05 move-table ABI mismatch");
    run_trace_prefix(core);
    if (log_problem_count) battle_core_die("P05 natural field boot warned");
    struct Snapshot field = take_snapshot(core);
    p05_fixture(core, &field, scenario);
    free(field.bytes);
    struct P05TurnSample final;
    struct P05TurnObserver observed = p05_observe_turn(core, scenario, &final);
    fprintf(stderr, "P05 case=%s state=%d frame=%u reason=%s\n",
            scenario->name, observed.state, final.frame,
            observed.error ? observed.error : "none");
    mCoreConfigDeinit(&core->config);
    core->deinit(core); /* mGBA owns/frees this core; do not free it twice. */
    sha256_file(argv[1], after);
    if (strcmp(before, after) != 0 || log_problem_count
        || observed.state != P05_TURN_PASS) return 1;
    /* Emit PASS only after teardown and the final ROM identity check. */
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"scope\":\"P05_DRAGONIZE_CONTROLLER_TURN_REPRESENTATIVE\","
           "\"case\":\"%s\",\"rom_sha256\":\"%s\","
           "\"normal_controller_input\":true,\"passive_after_fixture\":true,"
           "\"fixture_battle_ram_overrides\":true,\"native_battle_setup\":true,"
           "\"representative_scheduler_e2e\":true,\"full_p05_acceptance\":false,"
           "\"species_ability_assignment_e2e\":false,\"save_reload_e2e\":false,"
           "\"release_ready\":false,\"warnings_errors\":0,\"initial\":",
           scenario->name, before);
    p05_print_sample(&observed.initial);
    printf(",\"final\":"); p05_print_sample(&final);
    printf(",\"events\":{\"action\":%u,\"move\":%u,\"player_pp_spent\":%u,"
           "\"enemy_pp_spent\":%u,\"returned\":%u,\"hit\":%u,\"immune\":%u},"
           "\"frames\":%u}\n", observed.action_frame, observed.move_frame,
           observed.player_spent_frame, observed.enemy_spent_frame,
           observed.returned_frame, observed.hit_frame, observed.immune_frame,
           final.frame);
    return 0;
}
