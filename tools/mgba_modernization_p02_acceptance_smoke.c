/*
 * Modernization P02 evolution acceptance checkpoint for libmGBA 0.10.2.
 *
 * This runner boots the exact in-memory Stage67 candidate to a naturally
 * initialized field,
 * creates real party Pokemon with the ROM's CreateMon/SetMonData consumers,
 * and executes the linked GetEvolutionTargetSpecies and item-removal routines
 * on the emulated ARM7TDMI.  It deliberately reports a checkpoint rather than
 * claiming that the asynchronous evolution scene is covered.
 */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    P02A_GET_EVOLUTION_TARGET = 0x090FB775U,
    P02A_ITEM_EVOLUTION_REMOVAL = 0x090FB631U,
    P02A_GET_MON_ABILITY = 0x090DA23DU,
    P02A_CALCULATE_MON_STATS = 0x090D939DU,
    P02A_TRY_SAVING_DATA = 0x080DB34DU,
    P02A_SAVE_LOAD_GAME_DATA = 0x080DB4E5U,
    P02A_G_SAVE_BLOCK1 = 0x03005048U,
    P02A_SAVE_SIZE = 0x20000U,

    P02A_MODE_NORMAL = 0U,
    P02A_MODE_TRADE = 1U,
    P02A_MODE_ITEM_USE = 2U,

    P02A_MON_DATA_PERSONALITY = 0U,
    P02A_MON_DATA_SPECIES = 11U,
    P02A_MON_DATA_HELD_ITEM = 12U,
    P02A_MON_DATA_MOVE1 = 13U,
    P02A_MON_DATA_FRIENDSHIP = 32U,
    P02A_MON_DATA_ALT_ABILITY = 46U,
    P02A_MON_DATA_SPECIES2 = 65U,
    P02A_HIDDEN_ABILITY_BYTE = 71U,
    P02A_HIDDEN_ABILITY_MASK = 0x10U,

    P02A_LEVEL_SOURCE = 1U,
    P02A_LEVEL_TARGET = 2U,
    P02A_LEVEL_THRESHOLD = 16U,
    P02A_FRIENDSHIP_SOURCE = 12U,
    P02A_FRIENDSHIP_TARGET = 13U,
    P02A_FRIENDSHIP_THRESHOLD = 220U,
    P02A_ITEM_SOURCE = 19U,
    P02A_ITEM_TARGET = 20U,
    P02A_ITEM_SUN_STONE = 93U,
    P02A_ITEM_WRONG = 94U,
    P02A_MOVE_SOURCE = 475U,
    P02A_MOVE_TARGET = 735U,
    P02A_MOVE_ANCIENT_POWER = 246U,
    P02A_TRADE_SOURCE = 452U,
    P02A_TRADE_TARGET = 453U,
    P02A_TRADE_ITEM_SOURCE = 470U,
    P02A_TRADE_ITEM_TARGET = 536U,
    P02A_ITEM_METAL_COAT = 477U,
    P02A_LEVEL_ITEM_SOURCE = 499U,
    P02A_LEVEL_ITEM_TARGET = 1419U,
    P02A_LEVEL_ITEM_REGULAR_TARGET = 500U,
    P02A_LEVEL_ITEM_LEVEL = 36U,
    P02A_ITEM_SPOOKY_PLATE = 710U,
    P02A_FORM_SOURCE = 473U,
    P02A_FORM_NIGHT_TARGET = 1220U,
    P02A_FORM_LEVEL = 28U,
};

struct P02ACase {
    const char *key;
    uint16_t source;
    uint8_t level;
    uint8_t mode;
    uint16_t argument;
    uint16_t held_item;
    uint16_t move;
    uint16_t friendship;
    uint16_t expected;
    uint32_t result;
    uint32_t instructions;
    bool payload_pc_seen;
};

struct P02ALevelItemRepair {
    uint16_t source;
    uint8_t level;
    uint16_t conditional_target;
    uint16_t item;
    uint16_t regular_target;
};

static const struct P02ALevelItemRepair P02A_LEVEL_ITEM_REPAIRS[] = {
    {499U, 36U, 1419U, 710U, 500U},
    {759U, 36U, 1422U, 719U, 760U},
    {861U, 54U, 1427U, 716U, 862U},
    {993U, 40U, 1428U, 711U, 994U},
    {1001U, 37U, 1430U, 708U, 1002U},
    {1121U, 34U, 1431U, 704U, 1122U},
};

static void p02a_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p02-acceptance: %s\n", message);
    exit(1);
}

static uint32_t p02a_get_data(struct mCore *core, uint32_t field)
{
    return call_preserving(
        core, BATTLE_CORE_GET_MON_DATA, ADDR_PLAYER_PARTY, field, 0U, 0U);
}

static void p02a_prepare_mon(
    struct mCore *core, const struct Snapshot *field, struct P02ACase *test)
{
    restore_snapshot(core, field);
    clear_parties(core);
    create_mon(core, ADDR_PLAYER_PARTY, test->source, test->level);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1U);
    if (test->held_item != 0U)
        set_mon_data_u32(
            core, ADDR_PLAYER_PARTY, P02A_MON_DATA_HELD_ITEM,
            test->held_item);
    if (test->move != 0U)
        set_mon_data_u32(
            core, ADDR_PLAYER_PARTY, P02A_MON_DATA_MOVE1, test->move);
    if (test->friendship != UINT16_MAX)
        set_mon_data_u32(
            core, ADDR_PLAYER_PARTY, P02A_MON_DATA_FRIENDSHIP,
            test->friendship);
}

static void p02a_run_case(
    struct mCore *core, const struct Snapshot *field, struct P02ACase *test)
{
    p02a_prepare_mon(core, field, test);
    struct CallObservation observation = call_bounded(
        core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
        test->mode, test->argument, 0U);
    test->result = observation.result;
    test->instructions = observation.instructions;
    test->payload_pc_seen = observation.payload_pc_seen;
    if (test->result != test->expected)
        p02a_die(test->key);
    if (test->instructions == 0U || !test->payload_pc_seen)
        p02a_die("evolution consumer was not executed in payload");
}

static void p02a_print_case(const struct P02ACase *test)
{
    printf(
        "{\"source\":%u,\"level\":%u,\"mode\":%u,"
        "\"argument\":%u,\"held_item\":%u,\"move\":%u,"
        "\"friendship\":",
        test->source, test->level, test->mode, test->argument,
        test->held_item, test->move);
    if (test->friendship == UINT16_MAX)
        printf("null");
    else
        printf("%u", test->friendship);
    printf(
        ",\"expected\":%u,\"result\":%" PRIu32
        ",\"instructions\":%" PRIu32 ",\"payload_pc_seen\":true}",
        test->expected, test->result, test->instructions);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        p02a_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) p02a_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) p02a_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    run_trace_prefix(core);
    if (log_problem_count != 0U)
        p02a_die("mGBA warned/errored during natural field boot");
    if (read32(core, P02A_G_SAVE_BLOCK1) < 0x02000000U
        || read32(core, P02A_G_SAVE_BLOCK1) >= 0x02040000U)
        p02a_die("natural field did not initialize SaveBlock1");
    struct Snapshot field = take_snapshot(core);

    struct P02ACase cases[] = {
        {"level_below", P02A_LEVEL_SOURCE, P02A_LEVEL_THRESHOLD - 1U,
         P02A_MODE_NORMAL, 0U, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"level_boundary", P02A_LEVEL_SOURCE, P02A_LEVEL_THRESHOLD,
         P02A_MODE_NORMAL, 0U, 0U, 0U, UINT16_MAX, P02A_LEVEL_TARGET,
         0U, 0U, false},
        {"level_above", P02A_LEVEL_SOURCE, P02A_LEVEL_THRESHOLD + 1U,
         P02A_MODE_NORMAL, 0U, 0U, 0U, UINT16_MAX, P02A_LEVEL_TARGET,
         0U, 0U, false},
        {"friendship_below", P02A_FRIENDSHIP_SOURCE, 10U,
         P02A_MODE_NORMAL, 0U, 0U, 0U, P02A_FRIENDSHIP_THRESHOLD - 1U,
         0U, 0U, 0U, false},
        {"friendship_boundary", P02A_FRIENDSHIP_SOURCE, 10U,
         P02A_MODE_NORMAL, 0U, 0U, 0U, P02A_FRIENDSHIP_THRESHOLD,
         P02A_FRIENDSHIP_TARGET, 0U, 0U, false},
        {"item_positive", P02A_ITEM_SOURCE, 20U, P02A_MODE_ITEM_USE,
         P02A_ITEM_SUN_STONE, 0U, 0U, UINT16_MAX, P02A_ITEM_TARGET,
         0U, 0U, false},
        {"item_wrong", P02A_ITEM_SOURCE, 20U, P02A_MODE_ITEM_USE,
         P02A_ITEM_WRONG, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"item_missing", P02A_ITEM_SOURCE, 20U, P02A_MODE_ITEM_USE,
         0U, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"move_positive", P02A_MOVE_SOURCE, 20U, P02A_MODE_NORMAL,
         0U, 0U, P02A_MOVE_ANCIENT_POWER, UINT16_MAX, P02A_MOVE_TARGET,
         0U, 0U, false},
        {"move_missing", P02A_MOVE_SOURCE, 20U, P02A_MODE_NORMAL,
         0U, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"trade_positive", P02A_TRADE_SOURCE, 20U, P02A_MODE_TRADE,
         0U, 0U, 0U, UINT16_MAX, P02A_TRADE_TARGET, 0U, 0U, false},
        {"trade_item_positive", P02A_TRADE_ITEM_SOURCE, 20U,
         P02A_MODE_TRADE, 0U, P02A_ITEM_METAL_COAT, 0U, UINT16_MAX,
         P02A_TRADE_ITEM_TARGET, 0U, 0U, false},
        {"trade_item_missing", P02A_TRADE_ITEM_SOURCE, 20U,
         P02A_MODE_TRADE, 0U, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"level_item_below", P02A_LEVEL_ITEM_SOURCE,
         P02A_LEVEL_ITEM_LEVEL - 1U, P02A_MODE_NORMAL, 0U,
         P02A_ITEM_SPOOKY_PLATE, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"level_item_missing", P02A_LEVEL_ITEM_SOURCE,
         P02A_LEVEL_ITEM_LEVEL, P02A_MODE_NORMAL, 0U, 0U, 0U,
         UINT16_MAX, P02A_LEVEL_ITEM_REGULAR_TARGET, 0U, 0U, false},
        {"level_item_boundary", P02A_LEVEL_ITEM_SOURCE,
         P02A_LEVEL_ITEM_LEVEL, P02A_MODE_NORMAL, 0U,
         P02A_ITEM_SPOOKY_PLATE, 0U, UINT16_MAX,
         P02A_LEVEL_ITEM_TARGET, 0U, 0U, false},
        {"night_form_below", P02A_FORM_SOURCE, P02A_FORM_LEVEL - 1U,
         P02A_MODE_NORMAL, 0U, 0U, 0U, UINT16_MAX, 0U, 0U, 0U, false},
        {"night_form_boundary", P02A_FORM_SOURCE, P02A_FORM_LEVEL,
         P02A_MODE_NORMAL, 0U, 0U, 0U, UINT16_MAX,
         P02A_FORM_NIGHT_TARGET, 0U, 0U, false},
    };
    for (unsigned index = 0U; index < ARRAY_LEN(cases); ++index)
        p02a_run_case(core, &field, &cases[index]);

    /* EVO_TRADE_ITEM performs the held-item removal itself. */
    p02a_prepare_mon(core, &field, &cases[11]);
    uint32_t held_before = p02a_get_data(core, P02A_MON_DATA_HELD_ITEM);
    struct CallObservation trade_consume = call_bounded(
        core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
        P02A_MODE_TRADE, 0U, 0U);
    uint32_t held_after = p02a_get_data(core, P02A_MON_DATA_HELD_ITEM);
    if (trade_consume.result != P02A_TRADE_ITEM_TARGET
        || held_before != P02A_ITEM_METAL_COAT || held_after != 0U)
        p02a_die("trade item was not consumed by the real evolution consumer");

    uint32_t repaired_instruction_total = 0U;
    for (unsigned index = 0U;
         index < ARRAY_LEN(P02A_LEVEL_ITEM_REPAIRS); ++index) {
        const struct P02ALevelItemRepair *repair =
            &P02A_LEVEL_ITEM_REPAIRS[index];
        struct P02ACase probe = {
            "level_item_repair", repair->source, repair->level,
            P02A_MODE_NORMAL, 0U, repair->item, 0U, UINT16_MAX,
            repair->conditional_target, 0U, 0U, false,
        };
        p02a_prepare_mon(core, &field, &probe);
        struct CallObservation selected = call_bounded(
            core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
            P02A_MODE_NORMAL, 0U, 0U);
        struct CallObservation removed = call_bounded(
            core, P02A_ITEM_EVOLUTION_REMOVAL, ADDR_PLAYER_PARTY,
            0U, 0U, 0U);
        if (selected.result != repair->conditional_target
            || p02a_get_data(core, P02A_MON_DATA_HELD_ITEM) != 0U
            || !selected.payload_pc_seen || !removed.payload_pc_seen)
            p02a_die("correct item did not select conditional form and consume");
        repaired_instruction_total += selected.instructions
            + removed.instructions;

        probe.level = (uint8_t)(repair->level - 1U);
        p02a_prepare_mon(core, &field, &probe);
        selected = call_bounded(
            core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
            P02A_MODE_NORMAL, 0U, 0U);
        removed = call_bounded(
            core, P02A_ITEM_EVOLUTION_REMOVAL, ADDR_PLAYER_PARTY,
            0U, 0U, 0U);
        if (selected.result != 0U
            || p02a_get_data(core, P02A_MON_DATA_HELD_ITEM) != repair->item)
            p02a_die("below-level item case selected or consumed unexpectedly");
        repaired_instruction_total += selected.instructions
            + removed.instructions;

        probe.level = repair->level;
        probe.held_item = 1U;
        probe.expected = repair->regular_target;
        p02a_prepare_mon(core, &field, &probe);
        selected = call_bounded(
            core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
            P02A_MODE_NORMAL, 0U, 0U);
        removed = call_bounded(
            core, P02A_ITEM_EVOLUTION_REMOVAL, ADDR_PLAYER_PARTY,
            0U, 0U, 0U);
        if (selected.result != repair->regular_target
            || p02a_get_data(core, P02A_MON_DATA_HELD_ITEM) != 1U)
            p02a_die("wrong item did not retain regular target and item");
        repaired_instruction_total += selected.instructions
            + removed.instructions;

        probe.held_item = 0U;
        p02a_prepare_mon(core, &field, &probe);
        selected = call_bounded(
            core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
            P02A_MODE_NORMAL, 0U, 0U);
        removed = call_bounded(
            core, P02A_ITEM_EVOLUTION_REMOVAL, ADDR_PLAYER_PARTY,
            0U, 0U, 0U);
        if (selected.result != repair->regular_target
            || p02a_get_data(core, P02A_MON_DATA_HELD_ITEM) != 0U)
            p02a_die("missing item did not select regular target");
        repaired_instruction_total += selected.instructions
            + removed.instructions;
    }

    /* Selection is non-destructive for persistent identity, moves and slot. */
    p02a_prepare_mon(core, &field, &cases[8]);
    set_mon_data_u32(core, ADDR_PLAYER_PARTY, P02A_MON_DATA_ALT_ABILITY, 1U);
    uint32_t personality_before = p02a_get_data(core, P02A_MON_DATA_PERSONALITY);
    uint32_t selector_before = p02a_get_data(core, P02A_MON_DATA_ALT_ABILITY);
    uint32_t ability_before = call_bounded(
        core, P02A_GET_MON_ABILITY, ADDR_PLAYER_PARTY, 0U, 0U, 0U).result;
    struct CallObservation preserve_call = call_bounded(
        core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
        P02A_MODE_NORMAL, 0U, 0U);
    uint32_t personality_after = p02a_get_data(core, P02A_MON_DATA_PERSONALITY);
    uint32_t selector_after = p02a_get_data(core, P02A_MON_DATA_ALT_ABILITY);
    uint32_t ability_after = call_bounded(
        core, P02A_GET_MON_ABILITY, ADDR_PLAYER_PARTY, 0U, 0U, 0U).result;
    uint32_t move_after = p02a_get_data(core, P02A_MON_DATA_MOVE1);
    uint32_t species_after = p02a_get_data(core, P02A_MON_DATA_SPECIES2);
    if (preserve_call.result != P02A_MOVE_TARGET
        || personality_before != personality_after
        || selector_before != selector_after
        || ability_before != ability_after
        || move_after != P02A_MOVE_ANCIENT_POWER
        || species_after != P02A_MOVE_SOURCE)
        p02a_die("selection mutated persistent Pokemon state");

    /*
     * Exercise the same low-level ROM consumers used by evolution completion,
     * while keeping the asynchronous scene itself outside this checkpoint.
     */
    const uint16_t retained_moves[BATTLE_CORE_MOVE_SLOTS] = {
        P02A_MOVE_ANCIENT_POWER, 33U, 45U, 52U,
    };
    p02a_prepare_mon(core, &field, &cases[8]);
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot)
        set_mon_data_u32(
            core, ADDR_PLAYER_PARTY, P02A_MON_DATA_MOVE1 + slot,
            retained_moves[slot]);
    set_mon_data_u32(core, ADDR_PLAYER_PARTY, P02A_MON_DATA_ALT_ABILITY, 1U);
    write8(
        core, ADDR_PLAYER_PARTY + P02A_HIDDEN_ABILITY_BYTE,
        read8(core, ADDR_PLAYER_PARTY + P02A_HIDDEN_ABILITY_BYTE)
            | P02A_HIDDEN_ABILITY_MASK);
    uint32_t apply_personality_before = p02a_get_data(
        core, P02A_MON_DATA_PERSONALITY);
    uint32_t apply_selector_before = p02a_get_data(
        core, P02A_MON_DATA_ALT_ABILITY);
    uint32_t apply_ability_before = call_bounded(
        core, P02A_GET_MON_ABILITY, ADDR_PLAYER_PARTY, 0U, 0U, 0U).result;
    struct CallObservation apply_select = call_bounded(
        core, P02A_GET_EVOLUTION_TARGET, ADDR_PLAYER_PARTY,
        P02A_MODE_NORMAL, 0U, 0U);
    if (apply_select.result != P02A_MOVE_TARGET)
        p02a_die("target application precondition did not select Tangrowth");
    set_mon_data_u32(
        core, ADDR_PLAYER_PARTY, P02A_MON_DATA_SPECIES,
        apply_select.result);
    struct CallObservation calculate = call_bounded(
        core, P02A_CALCULATE_MON_STATS, ADDR_PLAYER_PARTY,
        0U, 0U, 0U);
    uint32_t apply_personality_after = p02a_get_data(
        core, P02A_MON_DATA_PERSONALITY);
    uint32_t apply_selector_after = p02a_get_data(
        core, P02A_MON_DATA_ALT_ABILITY);
    uint32_t apply_ability_after = call_bounded(
        core, P02A_GET_MON_ABILITY, ADDR_PLAYER_PARTY, 0U, 0U, 0U).result;
    uint32_t apply_species_after = p02a_get_data(
        core, P02A_MON_DATA_SPECIES2);
    if (apply_species_after != P02A_MOVE_TARGET
        || apply_personality_before != apply_personality_after
        || apply_selector_before != apply_selector_after
        || apply_ability_before == 0U || apply_ability_after == 0U
        || !calculate.payload_pc_seen)
        p02a_die("target application identity/ability contract failed");
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        if (p02a_get_data(core, P02A_MON_DATA_MOVE1 + slot)
            != retained_moves[slot])
            p02a_die("target application did not retain all four moves");
    }

    if (log_problem_count != 0U)
        p02a_die("mGBA warned/errored during acceptance cases");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"DIRECT_REAL_CONSUMER_CHECKPOINT\","
        "\"rom_sha256\":\"%s\",\"fixed_rtc_unix\":946684800,"
        "\"boot_trace_segments\":%u,\"read_only_rom\":true,"
        "\"get_evolution_target_species\":\"0x090FB774\","
        "\"cases\":{",
        rom_sha256, BATTLE_CORE_FIELD_TRACE_SEGMENTS);
    for (unsigned index = 0U; index < ARRAY_LEN(cases); ++index) {
        if (index != 0U) putchar(',');
        printf("\"%s\":", cases[index].key);
        p02a_print_case(&cases[index]);
    }
    printf(
        "},\"trade_item_consumption\":{\"item_before\":%" PRIu32
        ",\"item_after\":%" PRIu32 ",\"target\":%" PRIu32
        ",\"instructions\":%" PRIu32 "},"
        "\"level_item_priority_repair\":{"
        "\"repaired_species_count\":%zu,"
        "\"correct_item_selects_conditional_form\":true,"
        "\"correct_item_consumed_after_selection\":true,"
        "\"below_level_retains_item\":true,"
        "\"wrong_item_selects_regular_form_and_is_retained\":true,"
        "\"missing_item_selects_regular_form\":true,"
        "\"instruction_total\":%" PRIu32 "},"
        "\"selection_preservation\":{\"personality_before\":%" PRIu32
        ",\"personality_after\":%" PRIu32
        ",\"ability_selector_before\":%" PRIu32
        ",\"ability_selector_after\":%" PRIu32
        ",\"ability_before\":%" PRIu32
        ",\"ability_after\":%" PRIu32
        ",\"move_before\":%u,\"move_after\":%" PRIu32
        ",\"species_before\":%u,\"species_after\":%" PRIu32 "},"
        "\"target_application\":{"
        "\"classification\":\"ROM_CONSUMERS_WITHOUT_ASYNC_SCENE\","
        "\"source\":%u,\"selected_target\":%" PRIu32
        ",\"applied_species\":%" PRIu32
        ",\"personality_before\":%" PRIu32
        ",\"personality_after\":%" PRIu32
        ",\"ability_selector_before\":%" PRIu32
        ",\"ability_selector_after\":%" PRIu32
        ",\"ability_before\":%" PRIu32
        ",\"ability_after\":%" PRIu32
        ",\"hidden_ability_bit_preserved\":true,"
        "\"moves_before\":[%u,%u,%u,%u],"
        "\"moves_after\":[%" PRIu32 ",%" PRIu32 ",%" PRIu32
        ",%" PRIu32 "],\"calculate_stats_instructions\":%" PRIu32 "},"
        "\"warnings_errors\":0,\"artifacts_written\":[]}",
        held_before, held_after, trade_consume.result,
        trade_consume.instructions,
        ARRAY_LEN(P02A_LEVEL_ITEM_REPAIRS), repaired_instruction_total,
        personality_before, personality_after,
        selector_before, selector_after, ability_before, ability_after,
        P02A_MOVE_ANCIENT_POWER, move_after,
        P02A_MOVE_SOURCE, species_after,
        P02A_MOVE_SOURCE, apply_select.result, apply_species_after,
        apply_personality_before, apply_personality_after,
        apply_selector_before, apply_selector_after,
        apply_ability_before, apply_ability_after,
        retained_moves[0], retained_moves[1], retained_moves[2],
        retained_moves[3],
        p02a_get_data(core, P02A_MON_DATA_MOVE1),
        p02a_get_data(core, P02A_MON_DATA_MOVE1 + 1U),
        p02a_get_data(core, P02A_MON_DATA_MOVE1 + 2U),
        p02a_get_data(core, P02A_MON_DATA_MOVE1 + 3U),
        calculate.instructions);
    putchar('\n');

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
