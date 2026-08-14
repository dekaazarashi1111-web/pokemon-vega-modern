/*
 * T06 battle policy/integration smoke for libmGBA 0.10.2.
 *
 * The scheduler fixture supplies the reviewed natural Vega field trace and
 * real battle setup helpers.  Direct ARM7TDMI calls cover bounded ABI units
 * and side-effect-free observations; completion evidence uses the ordinary
 * battle scheduler/controllers, including the five-shield Raid boss, capture
 * menu, bag, end, and subsequent normal battles.  It never opens a save file
 * and never writes the ROM or any host artifact.
 */
#define BATTLE_CORE_EMBEDDED
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "mgba_battle_core_smoke.c"

enum {
    POLICY_SCRATCH = 0x0203FC00,
    POLICY_SCRATCH_SIZE = 0x300,
    POLICY_VAR_8000 = 0x02036FEC,
    POLICY_VAR_8001 = 0x02036FEE,
    POLICY_G_SAVE_BLOCK3_POINTER = 0x03005050,
    POLICY_G_RAID_BATTLE_STARS = 0x0203DFC6,
    POLICY_SPECIAL_VAR_MON_BOX_ID = 0x0203700A,
    POLICY_SPECIAL_VAR_MON_BOX_POSITION = 0x0203700C,
    POLICY_EWRAM_START = 0x02000000,
    POLICY_EWRAM_END = 0x02040000,
    POLICY_MON_DATA_SPECIES = 11,
    POLICY_MON_DATA_HELD_ITEM = 12,
    POLICY_MON_DATA_MOVE1 = 13,
    POLICY_MON_DATA_PP1 = 17,
    POLICY_BATTLE_MON_ITEM_OFFSET = 0x2E,
    POLICY_BATTLE_TYPE_DOUBLE = 0x00000001,
    POLICY_BATTLE_TYPE_TRAINER = 0x00000008,
    POLICY_BATTLE_TYPE_FRONTIER = 0x06000100,
    POLICY_BATTLE_TYPE_TWO_OPPONENTS = 0x00200000,
    POLICY_BATTLE_TYPE_INGAME_PARTNER = 0x00400000,
    POLICY_BATTLE_TYPE_DYNAMAX = 0x40000000,
    POLICY_MAX_ARGS = 8,
    POLICY_STAT_INPUT_SIZE = 11,
    POLICY_CANDY_TARGET_SIZE = 8,
    POLICY_CANDY_RESULT_SIZE = 8,
    POLICY_TRAINER_MON_SIZE = 28,
    POLICY_TRAINER_PATCH_SIZE = 30,
    POLICY_EXIT_COUNT = 7,
    POLICY_MECHANIC_FIRST = 1,
    POLICY_MECHANIC_LAST = 4,
    POLICY_FACILITY_FORMAT_COUNT = 3,
    POLICY_FACILITY_RULE_COUNT = 8,
    POLICY_PERSIST_EFFECT_COUNT = 7,
    POLICY_RAID_STATE_INPUT_LIMIT = 20000,
    POLICY_RAID_INTRO_PRESS_INTERVAL = 27,
    POLICY_RAID_BOSS_SPECIES = 150,
    POLICY_SIX_STAR_RAID = 6,
    POLICY_NEWBS_BATTLE_ACTIVE_OFFSET = 0x588,
    POLICY_NEWBS_DYNAMAX_SHIELD_COUNT_OFFSET = 0x25D,
    POLICY_NEWBS_DYNAMAX_SHIELDS_DESTROYED_OFFSET = 0x25E,
    POLICY_NEWBS_DYNAMAX_FLAGS_OFFSET = 0x261,
    POLICY_NEWBS_DYNAMAX_RAID_SHIELDS_UP = 1U << 2,
    POLICY_BATTLE_MON_ATTACK_OFFSET = 0x02,
    POLICY_NEWBS_RAID_ACTIVE_OFFSET = 0x8D0,
    POLICY_NEWBS_RAID_SHIELD_TOTAL_OFFSET = 0x8D4,
    POLICY_NEWBS_RAID_SHIELD_BROKEN_OFFSET = 0x8D5,
    POLICY_NEWBS_RAID_CAPTURE_ALLOWED_OFFSET = 0x8D6,
    POLICY_NEWBS_RAID_TURNS_ELAPSED_OFFSET = 0x8DA,
    POLICY_PC_BOX_COUNT = 14,
    POLICY_PC_BOX_MON_COUNT = 30,
    POLICY_PC_BOX_MON_SIZE = 80,
    POLICY_PC_BOX_MON_SPECIES_OFFSET = 0x20,
    POLICY_PC_BOX_HEADER_SIZE = 4,
    POLICY_PC_BOX_STRIDE = POLICY_PC_BOX_MON_COUNT * POLICY_PC_BOX_MON_SIZE,
    POLICY_PC_TOTAL_SLOTS = POLICY_PC_BOX_COUNT * POLICY_PC_BOX_MON_COUNT,

    POLICY_G_BATTLE_MAIN_FUNC = 0x03004FC4,
    POLICY_G_BATTLER_CONTROLLER_FUNCS = 0x03005020,
    POLICY_G_BATTLE_CONTROLLER_EXEC_FLAGS = 0x02023B28,
    POLICY_G_BATTLE_BUFFER_A = 0x02022B24,
    POLICY_BATTLE_MAIN_INTRO = 0x08015489,
    POLICY_BATTLE_MAIN_ACTION_SELECTION = 0x08013861,
    POLICY_CONTROLLER_INTRO_ACK = 0x0802FD91,
    POLICY_CONTROLLER_ACTION_STOCK = 0x0802DC15,
    POLICY_CONTROLLER_ACTION_CFRU = 0x09118B85,
    POLICY_CONTROLLER_MOVE_STOCK = 0x0802E1ED,
    POLICY_CONTROLLER_MOVE_CFRU = 0x09116E59,
    POLICY_CONTROLLER_TARGET_CFRU = 0x09115D05,
    POLICY_CONTROLLER_PRINT_STRING = 0x08035959,
    POLICY_COMMAND_PRINT_STRING = 0x10,
    POLICY_COMMAND_CHOOSE_ACTION = 0x12,
    POLICY_COMMAND_CHOOSE_MOVE = 0x14,
    POLICY_CB2_OVERWORLD = 0x08055E75,
    POLICY_CB2_EVOLUTION_SCENE_UPDATE = 0x080CF869,
    POLICY_FIELD_RETURN_INPUT_PULSES = 30,
};

struct PolicySymbol {
    const char *name;
    uint32_t address;
    bool seen;
};

#define POLICY_SYMBOL_LIST(X) \
    X(stat_valid, "cfru_integration_stat_inputs_are_valid") \
    X(effective_nature, "cfru_integration_effective_nature") \
    X(effective_iv, "cfru_integration_effective_iv") \
    X(ability_slot, "cfru_integration_ability_slot") \
    X(receives_exp, "cfru_integration_receives_battle_exp") \
    X(apply_candy, "cfru_integration_apply_exp_candy") \
    X(trainer_build, "cfru_integration_trainer_build_apply") \
    X(configure_policy, "VegaConfigureNextBattlePolicy") \
    X(configure_facility, "VegaConfigureNextFacility") \
    X(configure_mirage, "VegaConfigureNextMirageItem") \
    X(configure_raid, "VegaConfigureNextRaid") \
    X(policy_end, "VegaBattlePolicyEnd") \
    X(facility_active, "VegaFacilityStateIsActive") \
    X(facility_get, "VegaFacilityStateGet") \
    X(facility_set, "VegaFacilityStateSet") \
    X(can_mega, "VegaBattlePolicyCanMega") \
    X(mark_mega, "VegaBattlePolicyMarkMega") \
    X(can_z, "VegaBattlePolicyCanZ") \
    X(mark_z, "VegaBattlePolicyMarkZ") \
    X(can_dynamax, "VegaBattlePolicyCanDynamax") \
    X(mark_dynamax, "VegaBattlePolicyMarkDynamax") \
    X(can_tera, "VegaBattlePolicyCanTera") \
    X(mark_tera, "VegaBattlePolicyMarkTera") \
    X(mechanic_can, "cfru_integration_mechanic_can_use") \
    X(mechanic_try, "cfru_integration_mechanic_try_use") \
    X(mechanic_forced, "cfru_integration_mechanic_is_forced") \
    X(persistent_allowed, "cfru_integration_persistent_effect_allowed") \
    X(mirage_current, "cfru_integration_mirage_current") \
    X(mirage_set, "cfru_integration_mirage_set_battle_value") \
    X(raid_begin, "cfru_integration_raid_begin") \
    X(raid_partner, "cfru_integration_raid_partner_is_active") \
    X(raid_shields, "cfru_integration_raid_shields_remaining") \
    X(raid_break, "cfru_integration_raid_break_shield") \
    X(raid_hp, "cfru_integration_raid_set_boss_hp") \
    X(raid_turn, "cfru_integration_raid_advance_turn") \
    X(raid_capture, "cfru_integration_raid_try_capture") \
    X(raid_end, "cfru_integration_raid_end") \
    X(raid_ui_shields, "GetNumRaidShieldsUp") \
    X(is_raid, "IsRaidBattle") \
    X(is_catchable_raid, "IsCatchableRaidBattle") \
    X(rental_generate, "sp067_GenerateRandomBattleTowerTeam") \
    X(controller_action, "HandleInputChooseAction") \
    X(controller_move, "HandleInputChooseMove") \
    X(controller_target, "HandleInputChooseTarget")

struct PolicySymbols {
#define POLICY_FIELD(field, text) struct PolicySymbol field;
    POLICY_SYMBOL_LIST(POLICY_FIELD)
#undef POLICY_FIELD
};

struct PolicyEvidence {
    uint32_t direct_calls;
    uint64_t instructions;
    uint32_t actual_battle_setups;
    uint32_t payload_calls;
};

struct PolicyCall {
    uint32_t result;
    uint32_t instructions;
    bool payload_pc_seen;
};

struct FacilityEndEvidence {
    uint32_t experience_before;
    uint32_t experience_after;
    uint16_t item_before;
    uint16_t item_after;
    uint8_t outcome;
    bool enemy_fainted;
    bool runtime_cleaned;
};

struct RaidEndEvidence {
    uint32_t controller_turns;
    uint32_t frames;
    uint8_t initial_shields;
    uint8_t shield_breaks;
    uint8_t outcome;
    uint8_t chosen_capture_action;
    uint8_t player_pp_before;
    uint8_t player_pp_after;
    uint16_t boss_hp_initial;
    uint16_t boss_hp_min;
    bool boss_fainted;
    bool catch_phase_seen;
    bool bag_opened;
    bool ball_consumed;
    bool runtime_cleaned;
    bool policy_state_cleaned;
    bool normal_wild_no_leak;
    bool normal_trainer_no_leak;
    bool turn_limit_scheduler_end;
    uint16_t pc_box_id;
    uint16_t pc_box_position;
    uint16_t pc_captured_species;
    uint8_t party_count_after_capture;
    bool pc_storage_pointer_dynamic;
    bool full_party_pc_routed;
    bool party_species_unchanged;
    bool stock_pc_box_stride_80;
    bool adjacent_pc_slot_unchanged;
    bool partner_spread_moves_preserved;
};

struct PolicyRaidPcFixture {
    uint32_t storage;
    uint32_t target_slot_address;
    uint32_t adjacent_slot_address;
    uint16_t player_species[PARTY_SIZE];
    uint8_t expected_box;
    uint8_t expected_position;
    uint8_t adjacent_before[POLICY_PC_BOX_MON_SIZE];
};

static struct PolicyEvidence policy_evidence;
static const uint16_t policy_raid_player_species[PARTY_SIZE] = {
    115, 123, 127, 128, 131, 143
};
static const uint16_t policy_raid_partner_moves[3][BATTLE_CORE_MOVE_SLOTS] = {
    {202, 188, 73, 182},
    {53, 126, 332, 182},
    {55, 58, 352, 182},
};
static const uint8_t policy_raid_partner_pp[3][BATTLE_CORE_MOVE_SLOTS] = {
    {16, 16, 16, 16},
    {24, 8, 32, 16},
    {40, 16, 32, 16},
};

static void policy_die(const char *message) {
    fprintf(stderr, "mgba-battle-policy-smoke: %s\n", message);
    exit(1);
}

static struct mCore *policy_log_core;

static void policy_log(
    struct mLogger *logger,
    int category,
    enum mLogLevel level,
    const char *format,
    va_list args
) {
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    ++log_problem_count;
    uint32_t pc = 0;
    if (policy_log_core != NULL) {
        (void)policy_log_core->readRegister(policy_log_core, "pc", &pc);
    }
    fprintf(
        stderr,
        "mGBA[%s][0x%02x][pc=%08" PRIX32 "]: ",
        mLogCategoryName(category), (unsigned)level, pc);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static void policy_write32(struct mCore *core, uint32_t address, uint32_t value) {
    write32_bytes(core, address, value);
}

static void policy_clear(struct mCore *core, uint32_t address, uint32_t size) {
    for (uint32_t index = 0; index < size; ++index) write8(core, address + index, 0);
}

static uint32_t policy_parse_address(const char *text) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value < BATTLE_CORE_PAYLOAD_START
        || value >= BATTLE_CORE_PAYLOAD_END || (value & 1UL)) {
        policy_die("invalid/even linked policy symbol address");
    }
    return (uint32_t)value;
}

static void policy_parse_symbols(
    struct PolicySymbols *symbols,
    int argc,
    char **argv,
    int first
) {
#define POLICY_INIT(field, text) symbols->field = (struct PolicySymbol){text, 0, false};
    POLICY_SYMBOL_LIST(POLICY_INIT)
#undef POLICY_INIT

    for (int argument = first; argument < argc; ++argument) {
        const char *equals = strchr(argv[argument], '=');
        if (!equals || equals == argv[argument] || equals[1] == '\0') {
            policy_die("symbol arguments must use NAME=ADDRESS");
        }
        size_t name_size = (size_t)(equals - argv[argument]);
        bool matched = false;
#define POLICY_MATCH(field, text) \
        if (!matched && strlen(symbols->field.name) == name_size \
            && memcmp(argv[argument], symbols->field.name, name_size) == 0) { \
            if (symbols->field.seen) policy_die("duplicate policy symbol argument"); \
            symbols->field.address = policy_parse_address(equals + 1); \
            symbols->field.seen = true; \
            matched = true; \
        }
        POLICY_SYMBOL_LIST(POLICY_MATCH)
#undef POLICY_MATCH
        if (!matched) policy_die("unknown policy symbol argument");
    }

#define POLICY_REQUIRE(field, text) \
    if (!symbols->field.seen) policy_die("required policy symbol argument is missing");
    POLICY_SYMBOL_LIST(POLICY_REQUIRE)
#undef POLICY_REQUIRE
}

static struct PolicyCall policy_call_raw(
    struct mCore *core,
    uint32_t function,
    const uint32_t *args,
    size_t count
) {
    struct PolicyCall result = {0};
    if (!payload_address(function) || count > POLICY_MAX_ARGS) {
        policy_die("invalid bounded policy call contract");
    }
    struct CpuState original = capture_cpu_state(core);
    uint32_t cpsr = (uint32_t)original.registers[16];
    uint32_t extra = count > 4 ? (uint32_t)(count - 4) : 0;
    uint32_t call_sp = ((uint32_t)original.registers[13] - extra * 4U) & ~7U;
    for (uint32_t index = 0; index < extra; ++index) {
        policy_write32(core, call_sp + index * 4U, args[index + 4U]);
    }
    write_register(core, "cpsr", cpsr | 0xA0U);
    write_register(core, "sp", call_sp);
    write_register(core, "lr", 0x08000001U);
    for (unsigned index = 0; index < 4; ++index) {
        write_register(core, CPU_REGISTER_NAMES[index], index < count ? args[index] : 0);
    }
    write_register(core, "pc", function | 1U);
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != 0x08000002U) {
        uint32_t pc = ((uint32_t)read_register(core, "pc")) & ~1U;
        if (payload_address(pc)) result.payload_pc_seen = true;
        if (++result.instructions > BATTLE_CORE_DIRECT_CALL_LIMIT) {
            policy_die("bounded policy call exceeded instruction limit");
        }
        core->step(core);
    }
    result.result = (uint32_t)read_register(core, "r0");
    restore_cpu_state(core, &original);
    if (!result.payload_pc_seen || result.instructions == 0) {
        policy_die("bounded policy call did not execute payload code");
    }
    ++policy_evidence.direct_calls;
    ++policy_evidence.payload_calls;
    policy_evidence.instructions += result.instructions;
    return result;
}

static uint32_t policy_call(
    struct mCore *core,
    const struct PolicySymbol *symbol,
    const uint32_t *args,
    size_t count
) {
    return policy_call_raw(core, symbol->address, args, count).result;
}

#define POLICY_CALL0(core, symbol) \
    policy_call((core), &(symbol), NULL, 0)
#define POLICY_CALL1(core, symbol, a0) \
    policy_call((core), &(symbol), (uint32_t[]){(a0)}, 1)
#define POLICY_CALL2(core, symbol, a0, a1) \
    policy_call((core), &(symbol), (uint32_t[]){(a0), (a1)}, 2)
#define POLICY_CALL3(core, symbol, a0, a1, a2) \
    policy_call((core), &(symbol), (uint32_t[]){(a0), (a1), (a2)}, 3)

static uint32_t policy_observe(
    struct mCore *core,
    const struct PolicySymbol *symbol,
    const uint32_t *args,
    size_t count
) {
    struct Snapshot before = take_snapshot(core);
    uint32_t result = policy_call(core, symbol, args, count);
    restore_snapshot(core, &before);
    free(before.bytes);
    return result;
}

static uint32_t policy_observe_raw(
    struct mCore *core,
    uint32_t function,
    uint32_t r0,
    uint32_t r1,
    uint32_t r2,
    uint32_t r3
) {
    struct Snapshot before = take_snapshot(core);
    uint32_t result = call_preserving(core, function, r0, r1, r2, r3);
    restore_snapshot(core, &before);
    free(before.bytes);
    return result;
}

#define POLICY_OBSERVE0(core, symbol) \
    policy_observe((core), &(symbol), NULL, 0)
#define POLICY_OBSERVE1(core, symbol, a0) \
    policy_observe((core), &(symbol), (uint32_t[]){(a0)}, 1)

static struct CallObservation policy_start_configured_trainer(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbol *configure,
    const uint32_t *args,
    size_t count
) {
    uint8_t player[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 7, 20, NULL, NULL, player);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write16(core, BATTLE_CORE_TRAINER_MODE, 0);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 328);
    if (policy_call(core, configure, args, count) != 1) {
        policy_die("pending policy configuration was rejected");
    }
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) policy_die("configured trainer setup missed payload");
    run_fixed_frames(core);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || !(read32(core, ADDR_BATTLE_TYPE_FLAGS) & POLICY_BATTLE_TYPE_TRAINER)
        || read16(core, ADDR_BATTLE_MONS) == 0
        || read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE) == 0
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        policy_die("configured actual trainer context was not initialized");
    }
    ++policy_evidence.actual_battle_setups;
    return setup;
}

static struct CallObservation policy_start_configured_wild_with_item(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbol *configure,
    const uint32_t *args,
    size_t count,
    uint16_t enemy_held_item
) {
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 4, 20, NULL, NULL, player);
    create_mon_image(core, 10, 20, NULL, NULL, enemy);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    set_mon_data_u32(
        core, ADDR_ENEMY_PARTY, POLICY_MON_DATA_HELD_ITEM, enemy_held_item);
    if (policy_call(core, configure, args, count) != 1) {
        policy_die("item-bearing pending policy configuration was rejected");
    }
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) policy_die("item-bearing wild setup missed payload");
    run_fixed_frames(core);
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0
        || call_preserving(
            core, BATTLE_CORE_GET_MON_DATA,
            ADDR_PLAYER_PARTY, POLICY_MON_DATA_HELD_ITEM, 0, 0) != 0) {
        policy_die("item-bearing actual battle context was not initialized");
    }
    ++policy_evidence.actual_battle_setups;
    return setup;
}

static struct CallObservation policy_start_facility_trainer(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols,
    uint8_t format,
    uint8_t rule,
    uint16_t held_item
) {
    static const uint16_t player_species[4] = {4, 7, 11, 25};
    static const uint16_t enemy_species[4] = {10, 12, 14, 16};
    uint8_t player[4][POKEMON_SIZE];
    uint8_t enemy[4][POKEMON_SIZE];
    const uint32_t configure[] = {format, rule, 0};

    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    for (uint32_t slot = 0; slot < 4; ++slot) {
        create_mon_image(core, player_species[slot], 50, NULL, NULL, player[slot]);
        create_mon_image(core, enemy_species[slot], 50, NULL, NULL, enemy[slot]);
        install_mon_image(
            core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE, player[slot]);
        install_mon_image(
            core, ADDR_ENEMY_PARTY + slot * POKEMON_SIZE, enemy[slot]);
    }
    write8(core, ADDR_PLAYER_PARTY_COUNT, 4);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 4);
    set_mon_data_u32(
        core, ADDR_PLAYER_PARTY, POLICY_MON_DATA_HELD_ITEM, held_item);

    /*
     * The vanilla trainer entry rewrites gBattleTypeFlags while scheduling
     * its callback.  The linked BuildTrainerPartySetup hook must recover the
     * pending format before controllers are initialized; the runner does not
     * repair those flags itself.
     */
    if (policy_call(
            core, &symbols->configure_facility,
            configure, ARRAY_LEN(configure)) != 1) {
        policy_die("pre-entry facility configuration was rejected");
    }
    write16(core, BATTLE_CORE_TRAINER_MODE, 0);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) policy_die("facility trainer entry missed payload");
    uint32_t required = POLICY_BATTLE_TYPE_TRAINER | POLICY_BATTLE_TYPE_FRONTIER;
    uint32_t forbidden = POLICY_BATTLE_TYPE_DOUBLE
                       | POLICY_BATTLE_TYPE_TWO_OPPONENTS
                       | POLICY_BATTLE_TYPE_INGAME_PARTNER;
    if (format == 1) {
        required |= POLICY_BATTLE_TYPE_DOUBLE;
        forbidden &= ~POLICY_BATTLE_TYPE_DOUBLE;
    } else if (format == 2) {
        required |= POLICY_BATTLE_TYPE_DOUBLE
                  | POLICY_BATTLE_TYPE_TWO_OPPONENTS
                  | POLICY_BATTLE_TYPE_INGAME_PARTNER;
        forbidden = 0;
    }
    run_fixed_frames(core);
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    uint8_t expected_battlers = format == 0 ? 2 : 4;
    uint8_t expected_mask = (uint8_t)((1U << expected_battlers) - 1U);
    if (read8(core, ADDR_BATTLERS_COUNT) != expected_battlers
        || (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & expected_mask) != 0
        || (flags & required) != required
        || (flags & forbidden) != 0
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0
        || read32(core, ADDR_BATTLE_RESOURCES_POINTER) == 0) {
        policy_die("facility format did not initialize real battle controllers");
    }
    for (uint32_t battler = 0; battler < expected_battlers; ++battler) {
        if (read8(core, ADDR_BATTLER_POSITIONS + battler) != battler
            || read16(core, ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE) == 0) {
            policy_die("facility format controller/party mapping is incomplete");
        }
    }
    ++policy_evidence.actual_battle_setups;
    return setup;
}

static uint32_t policy_pc_slot_address(
    uint32_t storage,
    uint8_t box,
    uint8_t position
) {
    return storage + POLICY_PC_BOX_HEADER_SIZE
        + (uint32_t)box * POLICY_PC_BOX_STRIDE
        + (uint32_t)position * POLICY_PC_BOX_MON_SIZE;
}

static void policy_prepare_raid_party_fixture(
    struct mCore *core,
    struct PolicyRaidPcFixture *fixture
) {
    *fixture = (struct PolicyRaidPcFixture){0};
    if (read8(core, ADDR_PLAYER_PARTY_COUNT) != PARTY_SIZE) {
        policy_die("Raid PC fixture did not retain the full player party");
    }
    for (uint32_t slot = 0; slot < PARTY_SIZE; ++slot) {
        fixture->player_species[slot] = read16(
            core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE
                + POLICY_PC_BOX_MON_SPECIES_OFFSET);
        if (fixture->player_species[slot] != policy_raid_player_species[slot]) {
            policy_die("Raid PC fixture player party identity differs");
        }
    }
}

static void policy_prepare_raid_pc_fixture(
    struct mCore *core,
    struct PolicyRaidPcFixture *fixture
) {
    uint32_t storage = read32(core, POLICY_G_SAVE_BLOCK3_POINTER);
    uint64_t boxes_end = (uint64_t)storage + POLICY_PC_BOX_HEADER_SIZE
        + (uint64_t)POLICY_PC_TOTAL_SLOTS * POLICY_PC_BOX_MON_SIZE;
    uint8_t current_box;
    bool found = false;

    if ((storage & 3U) != 0 || storage < POLICY_EWRAM_START
        || boxes_end > POLICY_EWRAM_END) {
        policy_die("Raid PC fixture has an invalid dynamic gSaveBlock3 pointer");
    }
    fixture->storage = storage;
    current_box = read8(core, storage);
    if (current_box >= POLICY_PC_BOX_COUNT) {
        policy_die("Raid PC fixture has an invalid current box");
    }
    for (uint32_t offset = 0;
         offset < POLICY_PC_BOX_COUNT && !found;
         ++offset) {
        uint8_t box = (uint8_t)(
            (current_box + offset) % POLICY_PC_BOX_COUNT);
        for (uint32_t position = 0;
             position < POLICY_PC_BOX_MON_COUNT;
             ++position) {
            uint32_t slot_address = policy_pc_slot_address(
                storage, box, (uint8_t)position);
            if (read16(
                    core,
                    slot_address + POLICY_PC_BOX_MON_SPECIES_OFFSET) == 0) {
                fixture->expected_box = box;
                fixture->expected_position = (uint8_t)position;
                found = true;
                break;
            }
        }
    }
    if (!found) policy_die("Raid PC fixture has no stock 80-byte box slot");

    fixture->target_slot_address = policy_pc_slot_address(
        storage, fixture->expected_box, fixture->expected_position);
    if (read16(
            core, fixture->target_slot_address
                + POLICY_PC_BOX_MON_SPECIES_OFFSET) != 0) {
        policy_die("Raid PC fixture stock/raw empty-slot views differ");
    }

    uint32_t linear = (uint32_t)fixture->expected_box * POLICY_PC_BOX_MON_COUNT
        + fixture->expected_position;
    uint32_t adjacent = linear + 1U < POLICY_PC_TOTAL_SLOTS
        ? linear + 1U : linear - 1U;
    fixture->adjacent_slot_address = storage + POLICY_PC_BOX_HEADER_SIZE
        + adjacent * POLICY_PC_BOX_MON_SIZE;
    for (uint32_t byte = 0; byte < POLICY_PC_BOX_MON_SIZE; ++byte) {
        fixture->adjacent_before[byte] = read8(
            core, fixture->adjacent_slot_address + byte);
    }
}

static void policy_verify_raid_pc_capture(
    struct mCore *core,
    const struct PolicyRaidPcFixture *fixture,
    struct RaidEndEvidence *evidence
) {
    uint16_t box = read16(core, POLICY_SPECIAL_VAR_MON_BOX_ID);
    uint16_t position = read16(core, POLICY_SPECIAL_VAR_MON_BOX_POSITION);
    uint32_t storage = read32(core, POLICY_G_SAVE_BLOCK3_POINTER);
    uint64_t boxes_end = (uint64_t)storage + POLICY_PC_BOX_HEADER_SIZE
        + (uint64_t)POLICY_PC_TOTAL_SLOTS * POLICY_PC_BOX_MON_SIZE;

    evidence->pc_storage_pointer_dynamic =
        (storage & 3U) == 0 && storage >= POLICY_EWRAM_START
        && boxes_end <= POLICY_EWRAM_END;
    evidence->pc_box_id = box;
    evidence->pc_box_position = position;
    if (box >= POLICY_PC_BOX_COUNT || position >= POLICY_PC_BOX_MON_COUNT) {
        policy_die("Raid capture reported an invalid stock PC destination");
    }
    uint32_t target_slot_address = policy_pc_slot_address(
        storage, fixture->expected_box, fixture->expected_position);
    evidence->pc_captured_species = read16(
        core, target_slot_address + POLICY_PC_BOX_MON_SPECIES_OFFSET);
    evidence->party_count_after_capture = read8(core, ADDR_PLAYER_PARTY_COUNT);
    evidence->party_species_unchanged =
        evidence->party_count_after_capture == PARTY_SIZE;
    for (uint32_t slot = 0; slot < PARTY_SIZE; ++slot) {
        uint16_t species = read16(
            core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE
                + POLICY_PC_BOX_MON_SPECIES_OFFSET);
        if (species != fixture->player_species[slot]) {
            evidence->party_species_unchanged = false;
        }
    }
    evidence->adjacent_pc_slot_unchanged = true;
    uint32_t linear = (uint32_t)fixture->expected_box * POLICY_PC_BOX_MON_COUNT
        + fixture->expected_position;
    uint32_t adjacent = linear + 1U < POLICY_PC_TOTAL_SLOTS
        ? linear + 1U : linear - 1U;
    uint32_t adjacent_slot_address = storage + POLICY_PC_BOX_HEADER_SIZE
        + adjacent * POLICY_PC_BOX_MON_SIZE;
    for (uint32_t byte = 0; byte < POLICY_PC_BOX_MON_SIZE; ++byte) {
        if (read8(core, adjacent_slot_address + byte)
            != fixture->adjacent_before[byte]) {
            evidence->adjacent_pc_slot_unchanged = false;
        }
    }
    evidence->stock_pc_box_stride_80 =
        evidence->pc_captured_species == POLICY_RAID_BOSS_SPECIES;
    evidence->full_party_pc_routed =
        box == fixture->expected_box
        && position == fixture->expected_position
        && evidence->pc_captured_species == POLICY_RAID_BOSS_SPECIES
        && evidence->party_species_unchanged;
    if (!evidence->pc_storage_pointer_dynamic
        || !evidence->full_party_pc_routed
        || !evidence->stock_pc_box_stride_80
        || !evidence->adjacent_pc_slot_unchanged) {
        char detail[320];
        (void)snprintf(
            detail, sizeof(detail),
            "Raid full-party capture did not use the stock 80-byte PC ABI: "
            "storage=%u box=%u pos=%u species=%u party=%u unchanged=%u "
            "stride=%u adjacent=%u target=%08" PRIX32,
            evidence->pc_storage_pointer_dynamic, box, position,
            evidence->pc_captured_species,
            evidence->party_count_after_capture,
            evidence->party_species_unchanged,
            evidence->stock_pc_box_stride_80,
            evidence->adjacent_pc_slot_unchanged,
            target_slot_address);
        policy_die(detail);
    }
}

static struct CallObservation policy_start_raid_wild(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols,
    uint8_t shield_count,
    uint8_t turn_limit,
    uint8_t capture_allowed,
    struct PolicyRaidPcFixture *pc_fixture
) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    static const uint16_t boss_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_SCRATCH, 0, 0, 0
    };
    static const uint8_t boss_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint8_t players[PARTY_SIZE][POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    if (call_preserving(
            core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
            BATTLE_CORE_MASTER_BALL, 1, 0, 0) != 0
        || call_bounded(
            core, BATTLE_CORE_ADD_BAG_ITEM,
            BATTLE_CORE_MASTER_BALL, 1, 0, 0).result != 1) {
        policy_die("Raid fixture could not provision exactly one capture ball");
    }
    write16(core, BATTLE_CORE_BAG_STATE + 6U, BATTLE_CORE_BAG_BALL_POCKET);
    for (uint32_t cursor = 0; cursor < 6; ++cursor) {
        write16(core, BATTLE_CORE_BAG_STATE + 8U + cursor * 2U, 0);
    }
    create_mon_image(
        core, POLICY_RAID_BOSS_SPECIES, 40, boss_moves, boss_pp, enemy);
    clear_parties(core);
    seed_fixture(core);
    /* The field encounter owns Raid rank before BuildRaidMultiParty runs. */
    write8(core, POLICY_G_RAID_BATTLE_STARS, POLICY_SIX_STAR_RAID);
    for (uint32_t slot = 0; slot < PARTY_SIZE; ++slot) {
        create_mon_image(
            core, policy_raid_player_species[slot], 30,
            player_moves, player_pp, players[slot]);
        install_mon_image(core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE, players[slot]);
    }
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, PARTY_SIZE);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    if (pc_fixture != NULL) {
        policy_prepare_raid_party_fixture(core, pc_fixture);
    }
    const uint32_t configure[] = {
        0, (1U << 1) | (1U << 2), shield_count, turn_limit, capture_allowed
    };
    if (shield_count == 5) {
        const uint32_t above_limit[] = {
            0, (1U << 1) | (1U << 2), 6, turn_limit, capture_allowed
        };
        if (policy_call(
                core, &symbols->configure_raid,
                above_limit, ARRAY_LEN(above_limit)) != 0) {
            policy_die("Raid shield count above the fixed UI limit was accepted");
        }
    }
    if (policy_call(
            core, &symbols->configure_raid, configure, ARRAY_LEN(configure)) != 1) {
        policy_die("pending Raid configuration was rejected");
    }
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) policy_die("Raid wild setup missed payload");
    /* Reach BattleMon creation without injecting action/menu input.  This is
     * the earliest stable boundary where the party spread and battler copy
     * can be checked before an invalid move reaches a controller command. */
    for (uint32_t wait = 0; wait < BATTLE_CORE_FIXED_FRAMES * 3U; ++wait) {
        core->runFrame(core);
        if (read8(core, ADDR_BATTLERS_COUNT) == 3
            && read16(core, ADDR_BATTLE_MONS + 2U * BATTLE_MON_SIZE) != 0) {
            break;
        }
    }
    if (read8(core, ADDR_BATTLERS_COUNT) != 3
        || read16(core, ADDR_BATTLE_MONS + 2U * BATTLE_MON_SIZE) == 0) {
        policy_die("Raid BattleMon creation did not become observable before input");
    }
    /* StartWild relocates gSaveBlock3 while allocating battle runtime state.
     * Capture the stock-PC fixture only after that relocation, but still at
     * the pre-input boundary used for the partner spread ABI assertions. */
    if (pc_fixture != NULL) {
        policy_prepare_raid_pc_fixture(core, pc_fixture);
    }
    for (uint32_t partner = 0; partner < 3; ++partner) {
        uint32_t party = ADDR_PLAYER_PARTY + (partner + 3U) * POKEMON_SIZE;
        for (uint32_t slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            uint32_t move = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, party,
                POLICY_MON_DATA_MOVE1 + slot, 0, 0);
            uint32_t pp = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, party,
                POLICY_MON_DATA_PP1 + slot, 0, 0);
            if (move != policy_raid_partner_moves[partner][slot]
                || pp != policy_raid_partner_pp[partner][slot]) {
                policy_die("Raid partner spread moves/PP changed before controller input");
            }
            if (partner == 0
                && (read16(
                        core, ADDR_BATTLE_MONS + 2U * BATTLE_MON_SIZE
                            + BATTLE_MON_MOVES_OFFSET + slot * 2U) != move
                    || read8(
                        core, ADDR_BATTLE_MONS + 2U * BATTLE_MON_SIZE
                            + BATTLE_MON_PP_OFFSET + slot) != pp)) {
                policy_die("Raid partner party-to-BattleMon moves/PP ABI differs");
            }
        }
    }
    run_fixed_frames(core);
    run_fixed_frames(core);
    for (uint32_t press = 0; press < 4; ++press) {
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, 120);
    }
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    if (read8(core, ADDR_BATTLERS_COUNT) != 3
        || (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & 0x07U) != 0
        || (flags & POLICY_BATTLE_TYPE_DYNAMAX) == 0
        || (flags & POLICY_BATTLE_TYPE_INGAME_PARTNER) == 0
        || read8(core, POLICY_G_RAID_BATTLE_STARS) != POLICY_SIX_STAR_RAID
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0
        || read32(core, ADDR_BATTLE_RESOURCES_POINTER) == 0) {
        char detail[256];
        (void)snprintf(
            detail, sizeof(detail),
            "pending Raid did not initialize the existing three-controller UI path: "
                "battlers=%u absent=%02x flags=%08" PRIX32 " newbs=%08" PRIX32
                " resources=%08" PRIX32 " callback=%08" PRIX32
                " exec=%08" PRIX32 " outcome=%u bufferA2=%02x,%02x,%02x,%02x"
                " bufferB2=%02x,%02x,%02x,%02x",
            read8(core, ADDR_BATTLERS_COUNT),
            read8(core, ADDR_ABSENT_BATTLER_FLAGS), flags,
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read32(core, ADDR_BATTLE_RESOURCES_POINTER),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, 0x02023B28),
                read8(core, BATTLE_CORE_BATTLE_OUTCOME),
                read8(core, 0x02022F24), read8(core, 0x02022F25),
                read8(core, 0x02022F26), read8(core, 0x02022F27),
                read8(core, 0x02023724), read8(core, 0x02023725),
                read8(core, 0x02023726), read8(core, 0x02023727));
        policy_die(detail);
    }
    for (uint32_t battler = 0; battler < 3; ++battler) {
        if (read8(core, ADDR_BATTLER_POSITIONS + battler) != battler
            || read16(core, ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE) == 0) {
            char detail[384];
            (void)snprintf(
                detail, sizeof(detail),
                "Raid three-controller UI has an absent party mapping: "
                "battler=%u pos=%u species=%u callback=%08" PRIX32
                " exec=%08" PRIX32 " outcome=%u bufferA=%02x,%02x,%02x,%02x"
                " funcs=%08" PRIX32 ",%08" PRIX32 ",%08" PRIX32
                " partyidx=%u,%u,%u enemy=%u active=%u spriteflag=%02x"
                " anim=%u animcb=%08" PRIX32 " battlemain=%08" PRIX32,
                battler, read8(core, ADDR_BATTLER_POSITIONS + battler),
                read16(core, ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, 0x02023B28),
                read8(core, BATTLE_CORE_BATTLE_OUTCOME),
                read8(core, 0x02022B24 + battler * 0x200U),
                read8(core, 0x02022B25 + battler * 0x200U),
                read8(core, 0x02022B26 + battler * 0x200U),
                read8(core, 0x02022B27 + battler * 0x200U),
                read32(core, 0x03005020), read32(core, 0x03005024),
                read32(core, 0x03005028),
                read16(core, ADDR_BATTLER_PARTY_INDEXES),
                read16(core, ADDR_BATTLER_PARTY_INDEXES + 2U),
                read16(core, ADDR_BATTLER_PARTY_INDEXES + 4U),
                read16(core, ADDR_ENEMY_PARTY + 0x20U),
                read8(core, 0x02023B24),
                read8(core, read32(core, read32(core, 0x02023F78) + 4U)
                            + 12U),
                read8(core, 0x02037E15), read32(core, 0x02037E10),
                read32(core, 0x03004FC4));
            for (uint32_t task = 0; task < 16; ++task) {
                uint32_t address = 0x030050D0U + task * 40U;
                if (read8(core, address + 4U) != 0) {
                    fprintf(
                        stderr, "task%u=%08" PRIX32 " priority=%u data0=%d\n",
                        task, read32(core, address), read8(core, address + 7U),
                        (int16_t)read16(core, address + 8U));
                }
            }
            policy_die(detail);
        }
    }
    if (read16(core, ADDR_BATTLER_PARTY_INDEXES + 4U) != 3) {
        policy_die("Raid partner controller did not select the partner party half");
    }
    ++policy_evidence.actual_battle_setups;
    return setup;
}

static void policy_finish_direct(
    struct mCore *core,
    const struct PolicySymbols *symbols,
    uint8_t outcome
) {
    write8(core, BATTLE_CORE_BATTLE_OUTCOME, outcome);
    if (POLICY_CALL0(core, symbols->policy_end) != 1) {
        policy_die("policy cleanup rejected a valid active battle");
    }
}

static void policy_test_stat_inputs(
    struct mCore *core,
    const struct PolicySymbols *symbols
) {
    const uint32_t inputs = POLICY_SCRATCH;
    policy_clear(core, inputs, POLICY_STAT_INPUT_SIZE);
    write8(core, inputs + 0, 1);       /* stored nature */
    write8(core, inputs + 1, 6);       /* mint nature */
    write8(core, inputs + 2, 2);       /* hidden ability slot */
    for (uint32_t stat = 0; stat < 6; ++stat) write8(core, inputs + 3 + stat, stat + 1);
    write8(core, inputs + 9, 1U << 3); /* hyper-trained speed */
    write8(core, inputs + 10, 0);      /* EXP Share off */

    if (POLICY_CALL1(core, symbols->stat_valid, inputs) != 1
        || POLICY_CALL1(core, symbols->effective_nature, inputs) != 6
        || POLICY_CALL2(core, symbols->effective_iv, inputs, 3) != 31
        || POLICY_CALL2(core, symbols->effective_iv, inputs, 2) != 3
        || POLICY_CALL1(core, symbols->ability_slot, inputs) != 2
        || POLICY_CALL2(core, symbols->receives_exp, inputs, 0) != 0
        || POLICY_CALL2(core, symbols->receives_exp, inputs, 1) != 1) {
        policy_die("linked stat-input semantics differ");
    }
    write8(core, inputs + 10, 1);
    if (POLICY_CALL2(core, symbols->receives_exp, inputs, 0) != 1) {
        policy_die("EXP Share enabled semantics differ");
    }
}

static void policy_write_candy_target(
    struct mCore *core,
    uint32_t address,
    uint8_t level,
    uint32_t experience
) {
    policy_clear(core, address, POLICY_CANDY_TARGET_SIZE);
    write8(core, address, level);
    policy_write32(core, address + 4, experience);
}

static void policy_apply_candy(
    struct mCore *core,
    const struct PolicySymbol *symbol,
    uint32_t result,
    uint32_t target,
    uint32_t amount,
    uint32_t growth
) {
    policy_clear(core, result, POLICY_CANDY_RESULT_SIZE);
    const uint32_t args[] = {result, target, amount, 4, growth, 5};
    (void)policy_call(core, symbol, args, ARRAY_LEN(args));
}

static void policy_test_candy(
    struct mCore *core,
    const struct PolicySymbols *symbols
) {
    const uint32_t selected = POLICY_SCRATCH + 0x20;
    const uint32_t untouched = POLICY_SCRATCH + 0x28;
    const uint32_t result = POLICY_SCRATCH + 0x30;
    const uint32_t growth = POLICY_SCRATCH + 0x40;
    const uint32_t levels[] = {0, 0, 100, 300, 600};
    for (uint32_t index = 0; index < ARRAY_LEN(levels); ++index) {
        policy_write32(core, growth + index * 4U, levels[index]);
    }
    policy_write_candy_target(core, selected, 1, 0);
    policy_write_candy_target(core, untouched, 2, 100);
    policy_apply_candy(core, &symbols->apply_candy, result, selected, 350, growth);
    if (read8(core, result) != 1 || read8(core, result + 1) != 1
        || read8(core, result + 2) != 2 || read8(core, result + 3) != 0
        || read32(core, result + 4) != 350
        || read8(core, selected) != 3 || read32(core, selected + 4) != 350
        || read8(core, untouched) != 2 || read32(core, untouched + 4) != 100) {
        policy_die("EXP candy selected-target isolation differs");
    }

    policy_apply_candy(core, &symbols->apply_candy, result, selected, 0, growth);
    if (read8(core, result) != 2 || read8(core, result + 1) != 0
        || read8(core, selected) != 3 || read32(core, selected + 4) != 350) {
        policy_die("zero EXP candy should have no effect/not consume");
    }

    policy_write_candy_target(core, selected, 3, 590);
    policy_apply_candy(core, &symbols->apply_candy, result, selected, 1000, growth);
    if (read8(core, result) != 1 || read8(core, result + 1) != 1
        || read8(core, result + 3) != 1 || read32(core, result + 4) != 10
        || read8(core, selected) != 4 || read32(core, selected + 4) != 600) {
        policy_die("EXP candy cap/clamp semantics differ");
    }
    policy_apply_candy(core, &symbols->apply_candy, result, selected, 10, growth);
    if (read8(core, result) != 3 || read8(core, result + 1) != 0
        || read8(core, selected) != 4 || read32(core, selected + 4) != 600) {
        policy_die("at-cap EXP candy should not consume");
    }
}

static void policy_fill_trainer_base(struct mCore *core, uint32_t base) {
    policy_clear(core, base, POLICY_TRAINER_MON_SIZE);
    write16(core, base + 0, 25);
    write16(core, base + 2, 41);
    for (uint32_t move = 0; move < 4; ++move) write16(core, base + 4 + move * 2, 10 + move);
    write8(core, base + 12, 20);
    write8(core, base + 13, 8);
    write8(core, base + 14, 0);
    for (uint32_t stat = 0; stat < 6; ++stat) {
        write8(core, base + 15 + stat, 10 + stat);
        write8(core, base + 21 + stat, 0);
    }
}

static void policy_test_trainer_build(
    struct mCore *core,
    const struct PolicySymbols *symbols
) {
    const uint32_t base = POLICY_SCRATCH + 0x80;
    const uint32_t output = POLICY_SCRATCH + 0xA0;
    const uint32_t patch = POLICY_SCRATCH + 0xC0;
    policy_fill_trainer_base(core, base);
    policy_clear(core, output, POLICY_TRAINER_MON_SIZE);
    policy_clear(core, patch, POLICY_TRAINER_PATCH_SIZE);
    if (POLICY_CALL3(core, symbols->trainer_build, output, base, patch) != 1) {
        policy_die("identity trainer-build patch was rejected");
    }
    for (uint32_t index = 0; index < POLICY_TRAINER_MON_SIZE; ++index) {
        if (read8(core, output + index) != read8(core, base + index)) {
            policy_die("unspecified trainer-build fields lost identity");
        }
    }

    policy_clear(core, output, POLICY_TRAINER_MON_SIZE);
    policy_clear(core, patch, POLICY_TRAINER_PATCH_SIZE);
    write8(core, patch + 0, 0x0F); /* all scalar fields */
    write8(core, patch + 1, 0x3F); /* all IVs */
    write8(core, patch + 2, 0x3F); /* all EVs */
    write8(core, patch + 3, 0x0F); /* all moves */
    write8(core, patch + 4, 50);
    write8(core, patch + 5, 6);
    write8(core, patch + 6, 2);
    write16(core, patch + 8, 998);
    for (uint32_t move = 0; move < 4; ++move) write16(core, patch + 10 + move * 2, 1059 + move);
    for (uint32_t stat = 0; stat < 6; ++stat) {
        write8(core, patch + 18 + stat, 31);
        write8(core, patch + 24 + stat, stat == 0 ? 252 : (stat == 1 ? 252 : (stat == 2 ? 6 : 0)));
    }
    if (POLICY_CALL3(core, symbols->trainer_build, output, base, patch) != 1
        || read16(core, output) != 25 || read16(core, output + 2) != 998
        || read8(core, output + 12) != 50 || read8(core, output + 13) != 6
        || read8(core, output + 14) != 2) {
        policy_die("fully specified trainer-build scalar semantics differ");
    }
    for (uint32_t move = 0; move < 4; ++move) {
        if (read16(core, output + 4 + move * 2) != 1059 + move) {
            policy_die("fully specified trainer-build moves differ");
        }
    }
    for (uint32_t stat = 0; stat < 6; ++stat) {
        uint8_t expected_ev = stat == 0 ? 252 : (stat == 1 ? 252 : (stat == 2 ? 6 : 0));
        if (read8(core, output + 15 + stat) != 31
            || read8(core, output + 21 + stat) != expected_ev) {
            policy_die("fully specified trainer-build IV/EV semantics differ");
        }
    }
}

static const struct PolicySymbol *policy_can_symbol(
    const struct PolicySymbols *symbols,
    uint32_t mode
) {
    switch (mode) {
        case 1: return &symbols->can_mega;
        case 2: return &symbols->can_z;
        case 3: return &symbols->can_dynamax;
        case 4: return &symbols->can_tera;
        default: policy_die("invalid mechanic mode");
    }
    return NULL;
}

static const struct PolicySymbol *policy_mark_symbol(
    const struct PolicySymbols *symbols,
    uint32_t mode
) {
    switch (mode) {
        case 1: return &symbols->mark_mega;
        case 2: return &symbols->mark_z;
        case 3: return &symbols->mark_dynamax;
        case 4: return &symbols->mark_tera;
        default: policy_die("invalid mechanic mode");
    }
    return NULL;
}

static void policy_test_mechanics(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    for (uint32_t mode = POLICY_MECHANIC_FIRST; mode <= POLICY_MECHANIC_LAST; ++mode) {
        const uint32_t configure[] = {5, mode};
        (void)policy_start_configured_trainer(
            core, field, &symbols->configure_policy, configure, ARRAY_LEN(configure));
        write8(core, ADDR_BATTLERS_COUNT, 4);
        for (uint32_t battler = 0; battler < 4; ++battler) {
            write8(core, ADDR_BATTLER_POSITIONS + battler, (uint8_t)battler);
        }
        const struct PolicySymbol *can = policy_can_symbol(symbols, mode);
        const struct PolicySymbol *mark = policy_mark_symbol(symbols, mode);
        if (POLICY_CALL2(core, *can, 0, 0) != 0
            || POLICY_CALL2(core, *can, 0, 1) != 1
            || POLICY_CALL1(core, *mark, 0) != 1
            || POLICY_CALL2(core, *can, 0, 1) != 0
            || POLICY_CALL2(core, *can, 2, 1) != 0
            || POLICY_CALL1(core, *mark, 2) != 0
            || POLICY_CALL2(core, *can, 1, 1) != 1
            || POLICY_CALL1(core, *mark, 1) != 1
            || POLICY_CALL2(core, *can, 3, 1) != 0) {
            policy_die("mechanic side-wide/one-use gate differs");
        }
        for (uint32_t other = POLICY_MECHANIC_FIRST; other <= POLICY_MECHANIC_LAST; ++other) {
            if (other != mode
                && POLICY_CALL2(core, *policy_can_symbol(symbols, other), 0, 1) != 0) {
                policy_die("simultaneous mechanic was not excluded");
            }
        }
        policy_finish_direct(core, symbols, BATTLE_CORE_OUTCOME_WON);
        if (POLICY_CALL2(core, *can, 0, 1) != 0
            || POLICY_CALL2(core, symbols->mechanic_can, 0, mode) != 0) {
            policy_die("mechanic state leaked after battle cleanup");
        }
    }
}

static void policy_test_facility_matrix(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    static const uint8_t tier_by_rule[POLICY_FACILITY_RULE_COUNT] = {0, 4, 6, 1, 2, 3, 7, 5};
    for (uint32_t format = 0; format < POLICY_FACILITY_FORMAT_COUNT; ++format) {
        for (uint32_t rule = 0; rule < POLICY_FACILITY_RULE_COUNT; ++rule) {
            (void)policy_start_facility_trainer(
                core, field, symbols, (uint8_t)format, (uint8_t)rule, 0);
            const uint32_t active = POLICY_CALL0(core, symbols->facility_active);
            const uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
            uint32_t state[6];
            for (uint32_t field = 1; field <= 6; ++field)
                state[field - 1] = POLICY_CALL1(core, symbols->facility_get, field);
            const uint32_t expected_size = format == 0 ? 3U : (format == 1 ? 4U : 2U);
            const uint32_t expected_route = format + (rule == 0 ? 4U : 0U);
            if (active != 1
                || !(flags & POLICY_BATTLE_TYPE_FRONTIER)
                || state[0] != expected_size
                || state[1] != 50
                || state[2] != expected_route
                || state[3] != tier_by_rule[rule]
                /* Natural controller setup resolves the first displayed
                 * trainer name.  NPC-partner multi resolves the second;
                 * single and ordinary double keep its sentinel. */
                || state[4] == 0xFFFF || state[4] >= 100
                || (format != 2
                    ? state[5] != 0xFFFF
                    : (state[5] == 0xFFFF || state[5] >= 100))) {
                char detail[256];
                (void)snprintf(
                    detail, sizeof(detail),
                    "facility format/rule/flag state differs: format=%u rule=%u "
                    "active=%u flags=%08" PRIX32 " state=%u,%u,%u,%u,%u,%u",
                    format, rule, active, flags,
                    state[0], state[1], state[2], state[3], state[4], state[5]);
                policy_die(detail);
            }
            (void)POLICY_CALL2(core, symbols->facility_set, 8, 123);
            if (POLICY_CALL1(core, symbols->facility_get, 8) != 123) {
                policy_die("facility battle-local state roundtrip differs");
            }
            for (uint32_t effect = 0; effect < POLICY_PERSIST_EFFECT_COUNT; ++effect) {
                if (POLICY_CALL1(core, symbols->persistent_allowed, effect) != 0) {
                    policy_die("facility allowed a persistent battle effect");
                }
            }
            policy_finish_direct(core, symbols, BATTLE_CORE_OUTCOME_WON);
            if (POLICY_CALL0(core, symbols->facility_active) != 0) {
                policy_die("facility state leaked after cleanup");
            }
        }
    }
}

static struct FacilityEndEvidence policy_test_facility_scheduler_end(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    struct FacilityEndEvidence evidence = {0};
    (void)policy_start_facility_trainer(core, field, symbols, 0, 4, 41);
    if (read16(core, ADDR_BATTLE_MONS + POLICY_BATTLE_MON_ITEM_OFFSET) != 41) {
        policy_die("facility held item was not copied into the actual battle mon");
    }
    /* Flat Pokemon ABI is part of this final ROM contract.  Passive RAM reads
     * avoid perturbing active controller timing with a diagnostic ROM call. */
    evidence.experience_before = read32(
        core, ADDR_PLAYER_PARTY + BATTLE_CORE_PARTY_EXPERIENCE_OFFSET);
    evidence.item_before = read16(core, ADDR_PLAYER_PARTY + 0x22U);
    const uint32_t policy_newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    /* Keep the setup turn deliberately non-finishing regardless of damage
     * rolls; the second turn below is the one that exercises faint/end. */
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t party = side == 0 ? ADDR_PLAYER_PARTY : ADDR_ENEMY_PARTY;
        write16(core, party + POKEMON_CURRENT_HP_OFFSET, 1000);
        write16(core, party + POKEMON_CURRENT_HP_OFFSET + 2U, 1000);
        write16(core, ADDR_BATTLE_MONS + side * BATTLE_MON_SIZE
                      + BATTLE_CORE_MON_HP, 1000);
        write16(core, ADDR_BATTLE_MONS + side * BATTLE_MON_SIZE + 0x2CU, 1000);
    }
    /* The CFRU backup is taken by BattleBeginFirstTurn, immediately before
     * the first natural action.  Complete one non-finishing controller turn
     * before simulating a later consume/swap; mutating the party beforehand
     * would make the runner itself overwrite the value being tested. */
    uint32_t startup_pulses = 0;
    uint16_t item_backup_before = read16(core, policy_newbs + 0x1B4U);
    while (startup_pulses < BATTLE_CORE_TURN_INPUT_PRESSES
           && item_backup_before != evidence.item_before) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, BATTLE_CORE_TURN_INPUT_WAIT);
        ++startup_pulses;
        item_backup_before = read16(core, policy_newbs + 0x1B4U);
    }
    if (item_backup_before != evidence.item_before)
        policy_die("facility item backup was not initialized by the first turn");
    for (uint32_t press = startup_pulses;
         press < BATTLE_CORE_TURN_INPUT_PRESSES;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_key_frames(core, 1, 2);
        run_key_frames(core, 0, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    run_key_frames(core, 0, BATTLE_CORE_TURN_SETTLE_FRAMES);
    if (read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0)
        policy_die("facility item-backup setup turn unexpectedly ended battle");

    /* Simulate consume/swap state before the ordinary faint/end restoration. */
    set_mon_data_u32(core, ADDR_PLAYER_PARTY, POLICY_MON_DATA_HELD_ITEM, 0);
    write16(core, ADDR_BATTLE_MONS + POLICY_BATTLE_MON_ITEM_OFFSET, 0);
    policy_clear(
        core, ADDR_ENEMY_PARTY + POKEMON_SIZE,
        (PARTY_SIZE - 1U) * POKEMON_SIZE);
    write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP, 1);
    struct EndObservation end = {0};
    end.battle_runtime_initialized = true;
    for (unsigned press = 0;
         press < BATTLE_CORE_TURN_INPUT_PRESSES && !end.enemy_fainted_seen;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_end_frames(core, &end, 1, 2);
        run_end_frames(core, &end, 0, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    /* Do not let a surplus A pulse dismiss the short Frontier result path in
     * the same frame in which it is produced. */
    run_end_frames(core, &end, 0, 120);
    for (unsigned pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES && !end.battle_runtime_cleaned;
         ++pulse) {
        run_end_frames(core, &end, 1, 2);
        run_end_frames(core, &end, 0, BATTLE_CORE_END_INPUT_WAIT);
    }
    run_end_frames(core, &end, 0, 60);
    evidence.experience_after = read32(
        core, ADDR_PLAYER_PARTY + BATTLE_CORE_PARTY_EXPERIENCE_OFFSET);
    evidence.item_after = read16(core, ADDR_PLAYER_PARTY + 0x22U);
    evidence.outcome = end.outcome_seen;
    evidence.enemy_fainted = end.enemy_fainted_seen;
    evidence.runtime_cleaned = end.battle_runtime_cleaned;
    if (!evidence.enemy_fainted || evidence.outcome != BATTLE_CORE_OUTCOME_WON
        || !evidence.runtime_cleaned
        || evidence.experience_after != evidence.experience_before
        || evidence.item_before != 41 || evidence.item_after != evidence.item_before) {
        char detail[256];
        (void)snprintf(
            detail, sizeof(detail),
            "actual facility faint/end leaked EXP or held-item mutation: "
            "fainted=%u outcome=%u cleaned=%u exp=%" PRIu32 "->%" PRIu32
            " item=%u->%u",
            evidence.enemy_fainted, evidence.outcome, evidence.runtime_cleaned,
            evidence.experience_before, evidence.experience_after,
            evidence.item_before, evidence.item_after);
        if (item_backup_before != evidence.item_before) {
            size_t used = strlen(detail);
            (void)snprintf(detail + used, sizeof(detail) - used,
                           " backup=%u", item_backup_before);
        }
        policy_die(detail);
    }
    return evidence;
}

static uint32_t policy_test_rental_generation(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols,
    uint16_t species[PARTY_SIZE]
) {
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    const uint32_t configure[] = {0, 0, 0};
    if (policy_call(
            core, &symbols->configure_facility, configure, ARRAY_LEN(configure)) != 1) {
        policy_die("rental facility configuration was rejected");
    }
    write16(core, POLICY_VAR_8000, 0);
    write16(core, POLICY_VAR_8001, 0);
    (void)POLICY_CALL0(core, symbols->rental_generate);
    uint32_t count = 0;
    for (uint32_t slot = 0; slot < PARTY_SIZE; ++slot) {
        species[slot] = (uint16_t)call_preserving(
            core, BATTLE_CORE_GET_MON_DATA,
            ADDR_PLAYER_PARTY + slot * POKEMON_SIZE, 11, 0, 0);
        if (species[slot] != 0) ++count;
        if (species[slot] > BATTLE_CORE_MAX_VEGA_SPECIES) {
            policy_die("rental generator emitted non-Vega species");
        }
    }
    if (count < 3) policy_die("rental generator produced fewer than three mons");
    return count;
}

static void policy_test_mirage(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    static const uint8_t outcomes[POLICY_EXIT_COUNT] = {
        1, 2, 4, 9, 7, 0, 0x7F
    };
    for (uint32_t exit_path = 0; exit_path < POLICY_EXIT_COUNT; ++exit_path) {
        const uint32_t configure[] = {0, 900};
        (void)policy_start_configured_wild_with_item(
            core, field, &symbols->configure_mirage,
            configure, ARRAY_LEN(configure), 41);
        if (call_preserving(
                core, BATTLE_CORE_CHECK_BAG_HAS_ITEM, 900, 1, 0, 0) != 0
            || POLICY_CALL1(core, symbols->mirage_current, 0) != 900
            || read16(
                core, ADDR_BATTLE_MONS + POLICY_BATTLE_MON_ITEM_OFFSET) != 0
            || read16(
                core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                    + POLICY_BATTLE_MON_ITEM_OFFSET) != 900
            || call_preserving(
                core, BATTLE_CORE_GET_MON_DATA,
                ADDR_PLAYER_PARTY, POLICY_MON_DATA_HELD_ITEM, 0, 0) != 0
            || POLICY_CALL2(core, symbols->mirage_set, 0, 0) != 1) {
            policy_die("pending Mirage opponent item was not isolated in the actual battle");
        }
        /* Consume/swap-equivalent changes must remain battle-local. */
        write16(
            core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                + POLICY_BATTLE_MON_ITEM_OFFSET, 0);
        set_mon_data_u32(core, ADDR_ENEMY_PARTY, POLICY_MON_DATA_HELD_ITEM, 777);
        write8(core, BATTLE_CORE_BATTLE_OUTCOME, outcomes[exit_path]);
        if (POLICY_CALL0(core, symbols->policy_end) != 1
            || call_preserving(
                core, BATTLE_CORE_GET_MON_DATA,
                ADDR_PLAYER_PARTY, POLICY_MON_DATA_HELD_ITEM, 0, 0) != 0
            || call_preserving(
                core, BATTLE_CORE_GET_MON_DATA,
                ADDR_ENEMY_PARTY, POLICY_MON_DATA_HELD_ITEM, 0, 0) != 41
            || call_preserving(
                core, BATTLE_CORE_CHECK_BAG_HAS_ITEM, 900, 1, 0, 0) != 0
            || call_preserving(
                core, BATTLE_CORE_CHECK_BAG_HAS_ITEM, 777, 1, 0, 0) != 0
            || POLICY_CALL1(core, symbols->mirage_current, 0) != 41) {
            policy_die("Mirage opponent item leaked on a battle exit path");
        }
    }
}

static void policy_sample_raid_end(
    struct mCore *core,
    struct RaidEndEvidence *evidence
) {
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    if (outcome != 0 && evidence->outcome == 0) evidence->outcome = outcome;
    if (read8(core, BATTLE_CORE_BAG_STATE + 5U) != 0) {
        evidence->bag_opened = true;
        if (read8(core, BATTLE_CORE_CHOSEN_ACTIONS)
            == BATTLE_CORE_ACTION_USE_ITEM) {
            evidence->chosen_capture_action = BATTLE_CORE_ACTION_USE_ITEM;
        }
    }
    if (newbs != 0) {
        uint16_t boss_hp = read16(
            core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP);
        if (boss_hp == 0) evidence->boss_fainted = true;
        if (boss_hp != 0) {
            if (evidence->boss_hp_initial == 0)
                evidence->boss_hp_initial = boss_hp;
            if (evidence->boss_hp_min == 0 || boss_hp < evidence->boss_hp_min)
                evidence->boss_hp_min = boss_hp;
        }
        uint8_t total = read8(
            core, newbs + POLICY_NEWBS_DYNAMAX_SHIELD_COUNT_OFFSET);
        uint8_t destroyed = read8(
            core, newbs + POLICY_NEWBS_DYNAMAX_SHIELDS_DESTROYED_OFFSET);
        uint8_t policy_total = read8(
            core, newbs + POLICY_NEWBS_RAID_SHIELD_TOTAL_OFFSET);
        uint8_t policy_broken = read8(
            core, newbs + POLICY_NEWBS_RAID_SHIELD_BROKEN_OFFSET);
        uint8_t turns_elapsed = read8(
            core, newbs + POLICY_NEWBS_RAID_TURNS_ELAPSED_OFFSET);
        if (turns_elapsed > evidence->controller_turns)
            evidence->controller_turns = turns_elapsed;
        if (total != 0) {
            if (total > 5 || destroyed > total
                || policy_total != total || policy_broken != destroyed) {
                policy_die("natural Raid shield/UI and policy state diverged");
            }
            if (evidence->initial_shields == 0)
                evidence->initial_shields = total;
            if (evidence->initial_shields == total
                && destroyed > evidence->shield_breaks)
                evidence->shield_breaks = destroyed;
        }
    } else if (outcome == 0 && !evidence->catch_phase_seen) {
        policy_die("Raid runtime disappeared before a natural outcome");
    } else {
        evidence->runtime_cleaned = true;
    }
}

static void policy_run_raid_frames(
    struct mCore *core,
    struct RaidEndEvidence *evidence,
    uint16_t keys,
    uint32_t frames
) {
    core->setKeys(core, keys);
    for (uint32_t frame = 0; frame < frames; ++frame) {
        core->runFrame(core);
        ++evidence->frames;
        policy_sample_raid_end(core, evidence);
    }
}

static void policy_run_raid_controller_round(
    struct mCore *core,
    struct RaidEndEvidence *evidence,
    const struct PolicySymbols *symbols,
    bool stop_at_shields
) {
    uint8_t latched_gate = 0;
    bool intro_active = true;
    uint32_t next_intro_press = evidence->frames;
    uint32_t next_message_press = evidence->frames;

    for (uint32_t frame = 0;
         frame < POLICY_RAID_STATE_INPUT_LIMIT
             && !evidence->runtime_cleaned
             && !(stop_at_shields
                 ? evidence->initial_shields != 0
                     && evidence->shield_breaks >= evidence->initial_shields
                 : evidence->boss_fainted);) {
        uint32_t main = read32(core, POLICY_G_BATTLE_MAIN_FUNC);
        uint32_t controller = read32(
            core, POLICY_G_BATTLER_CONTROLLER_FUNCS);
        uint32_t exec = read32(
            core, POLICY_G_BATTLE_CONTROLLER_EXEC_FLAGS);
        uint8_t command = read8(core, POLICY_G_BATTLE_BUFFER_A);
        uint8_t gate = 0;

        if (main != POLICY_BATTLE_MAIN_INTRO) intro_active = false;
        if (intro_active
            && main == POLICY_BATTLE_MAIN_INTRO
            && (exec & 1U) != 0
            && controller == POLICY_CONTROLLER_INTRO_ACK
            && evidence->frames >= next_intro_press) {
            gate = 4;
        } else if (main == POLICY_BATTLE_MAIN_ACTION_SELECTION
                   && (exec & 1U) != 0
                   && command == POLICY_COMMAND_CHOOSE_ACTION
                   && (controller == POLICY_CONTROLLER_ACTION_STOCK
                       || controller == (symbols->controller_action.address | 1U))) {
            gate = 1;
        } else if (main == POLICY_BATTLE_MAIN_ACTION_SELECTION
                   && (exec & 1U) != 0
                   && command == POLICY_COMMAND_CHOOSE_MOVE
                   && (controller == POLICY_CONTROLLER_MOVE_STOCK
                       || controller == (symbols->controller_move.address | 1U))) {
            gate = 2;
        } else if (main == POLICY_BATTLE_MAIN_ACTION_SELECTION
                   && (exec & 1U) != 0
                   && command == POLICY_COMMAND_CHOOSE_MOVE
                   && controller == (symbols->controller_target.address | 1U)) {
            gate = 3;
        } else if (main == 0x08014DE9U
                   && (exec & (1U << 1)) != 0
                   && read8(core, POLICY_G_BATTLE_BUFFER_A + 0x200U)
                       == POLICY_COMMAND_PRINT_STRING
                   && read32(core, POLICY_G_BATTLER_CONTROLLER_FUNCS + 4U)
                       == POLICY_CONTROLLER_PRINT_STRING
                   && evidence->frames >= next_message_press) {
            gate = 5;
        }

        if (gate != 0 && (gate == 4 || gate == 5 || gate != latched_gate)) {
            uint32_t pulse_start = evidence->frames;
            write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR, 0);
            write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
            policy_run_raid_frames(core, evidence, 1, 2);
            policy_run_raid_frames(core, evidence, 0, 2);
            frame += 4;
            if (gate == 4) {
                next_intro_press = pulse_start + POLICY_RAID_INTRO_PRESS_INTERVAL;
            } else if (gate == 5) {
                next_message_press = pulse_start + POLICY_RAID_INTRO_PRESS_INTERVAL;
            } else {
                latched_gate = gate;
            }
        } else {
            if (gate == 0) latched_gate = 0;
            policy_run_raid_frames(core, evidence, 0, 1);
            ++frame;
        }
    }
}

static bool policy_normal_battle_after_raid(
    struct mCore *core,
    const struct PolicySymbols *symbols,
    bool trainer
) {
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    static const uint16_t moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0
    };
    static const uint8_t pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    struct EndObservation end = {0};

    for (uint32_t pulse = 0;
         pulse < POLICY_FIELD_RETURN_INPUT_PULSES
             && read32(core, BATTLE_CORE_MAIN_CALLBACK2) != POLICY_CB2_OVERWORLD;
         ++pulse) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
            == POLICY_CB2_EVOLUTION_SCENE_UPDATE) {
            run_key_frames(core, 1, 2);
        } else {
            run_key_frames(core, 0, 2);
        }
        run_key_frames(core, 0, BATTLE_CORE_END_INPUT_WAIT);
    }
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != POLICY_CB2_OVERWORLD) {
        policy_die("post-Raid field callback did not become ready");
    }

    create_mon_image(core, 4, 30, moves, pp, player);
    create_mon_image(core, 10, 5, moves, pp, enemy);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    if (trainer) {
        write16(core, BATTLE_CORE_TRAINER_MODE, 0);
        write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 328);
        end.setup_call = call_bounded(
            core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    } else {
        install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
        write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
        end.setup_call = call_bounded(
            core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    }
    if (!end.setup_call.payload_pc_seen) {
        policy_die("post-Raid normal battle setup missed payload");
    }
    run_fixed_frames(core);
    ++policy_evidence.actual_battle_setups;
    if (read8(core, ADDR_BATTLERS_COUNT) != 2
        || (read32(core, ADDR_BATTLE_TYPE_FLAGS)
            & (POLICY_BATTLE_TYPE_DYNAMAX | POLICY_BATTLE_TYPE_DOUBLE
               | POLICY_BATTLE_TYPE_INGAME_PARTNER)) != 0
        || POLICY_OBSERVE0(core, symbols->is_raid) != 0
        || POLICY_OBSERVE0(core, symbols->is_catchable_raid) != 0
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0) {
        char detail[256];
        (void)snprintf(
            detail, sizeof(detail),
            "Raid flag/state leaked into a subsequent normal battle: "
            "trainer=%u count=%u flags=%08" PRIX32 " israid=%u catch=%u"
            " newbs=%08" PRIX32 " cb2=%08" PRIX32,
            trainer, read8(core, ADDR_BATTLERS_COUNT),
            read32(core, ADDR_BATTLE_TYPE_FLAGS),
            POLICY_OBSERVE0(core, symbols->is_raid),
            POLICY_OBSERVE0(core, symbols->is_catchable_raid),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        policy_die(detail);
    }

    policy_clear(
        core, ADDR_ENEMY_PARTY + POKEMON_SIZE,
        (PARTY_SIZE - 1U) * POKEMON_SIZE);
    write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP, 1);
    end.battle_runtime_initialized = true;
    for (uint32_t press = 0; press < BATTLE_CORE_TURN_INPUT_PRESSES; ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0);
        run_end_frames(core, &end, 1, 2);
        run_end_frames(core, &end, 0, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    for (uint32_t pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES && !end.battle_runtime_cleaned;
         ++pulse) {
        run_end_frames(core, &end, 1, 2);
        run_end_frames(core, &end, 0, BATTLE_CORE_END_INPUT_WAIT);
    }
    run_end_frames(core, &end, 0, 60);
    if (!end.enemy_fainted_seen || end.outcome_seen != BATTLE_CORE_OUTCOME_WON
        || !end.battle_runtime_cleaned) {
        char detail[384];
        (void)snprintf(
            detail, sizeof(detail),
            "post-Raid normal battle did not naturally complete: trainer=%u "
            "fainted=%u outcome=%u cleaned=%u flags=%08" PRIX32
            " newbs=%08" PRIX32 " main=%08" PRIX32 " func0=%08" PRIX32
            " exec=%08" PRIX32 " cmd0=%02x party=%u enemyhp=%u",
            trainer, end.enemy_fainted_seen, end.outcome_seen,
            end.battle_runtime_cleaned, read32(core, ADDR_BATTLE_TYPE_FLAGS),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read32(core, POLICY_G_BATTLE_MAIN_FUNC),
            read32(core, POLICY_G_BATTLER_CONTROLLER_FUNCS),
            read32(core, POLICY_G_BATTLE_CONTROLLER_EXEC_FLAGS),
            read8(core, POLICY_G_BATTLE_BUFFER_A),
            read8(core, ADDR_PLAYER_PARTY_COUNT),
            read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                + BATTLE_CORE_MON_HP));
        policy_die(detail);
    }
    return true;
}

static struct RaidEndEvidence policy_test_raid_scheduler_e2e(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    struct RaidEndEvidence evidence = {0};
    struct PolicyRaidPcFixture pc_fixture = {0};
    (void)policy_start_raid_wild(
        core, field, symbols, 5, 10, 1, &pc_fixture);

    policy_sample_raid_end(core, &evidence);
    for (uint32_t wait = 0; wait < 40; ++wait) {
        if (evidence.initial_shields == 5) break;
        policy_run_raid_frames(core, &evidence, 0, 60);
    }
    uint32_t raid_newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (evidence.initial_shields != 5 || raid_newbs == 0
        || read8(core, raid_newbs + POLICY_NEWBS_BATTLE_ACTIVE_OFFSET) != 1
        || (read8(core, raid_newbs + POLICY_NEWBS_DYNAMAX_FLAGS_OFFSET)
            & POLICY_NEWBS_DYNAMAX_RAID_SHIELDS_UP) == 0
        || read8(core, raid_newbs + POLICY_NEWBS_RAID_ACTIVE_OFFSET) != 1
        || read8(
            core, raid_newbs + POLICY_NEWBS_RAID_CAPTURE_ALLOWED_OFFSET) != 1) {
        policy_die("configured high-difficulty Raid did not expose five existing-UI shields");
    }

    evidence.partner_spread_moves_preserved = true;

    /* Raid barriers divide ordinary damage by roughly one eighth of the
     * boss's current HP.  Give both friendly real controllers deterministic
     * fixture Attack values so their selected damaging moves reach the
     * native TOOK_DAMAGE/shield-break command instead of rounding to zero. */
    write16(
        core, ADDR_BATTLE_MONS + POLICY_BATTLE_MON_ATTACK_OFFSET, 2000);
    write16(
        core, ADDR_BATTLE_MONS + 2U * BATTLE_MON_SIZE
            + POLICY_BATTLE_MON_ATTACK_OFFSET, 2000);

    evidence.player_pp_before = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    uint8_t remaining = (uint8_t)(
        evidence.initial_shields - evidence.shield_breaks);
    policy_run_raid_controller_round(core, &evidence, symbols, true);
    remaining = (uint8_t)(evidence.initial_shields - evidence.shield_breaks);
    evidence.player_pp_after = read8(
        core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    if (remaining != 0 || evidence.shield_breaks != 5
        || evidence.player_pp_after >= evidence.player_pp_before) {
        char detail[256];
        (void)snprintf(
            detail, sizeof(detail),
            "real controller attacks did not deplete all five Raid UI shields: "
            "initial=%u broken=%u remaining=%u turns=%u pp=%u->%u "
            "hp=%u->%u fainted=%u cleaned=%u outcome=%u",
            evidence.initial_shields, evidence.shield_breaks, remaining,
            evidence.controller_turns,
            evidence.player_pp_before, evidence.player_pp_after,
            evidence.boss_hp_initial, evidence.boss_hp_min,
            evidence.boss_fainted, evidence.runtime_cleaned, evidence.outcome);
        size_t used = strlen(detail);
        (void)snprintf(
            detail + used, sizeof(detail) - used,
            " main=%08" PRIX32 " func0=%08" PRIX32 " exec=%08" PRIX32
            " cmd0=%02x active=%u",
            read32(core, POLICY_G_BATTLE_MAIN_FUNC),
            read32(core, POLICY_G_BATTLER_CONTROLLER_FUNCS),
            read32(core, POLICY_G_BATTLE_CONTROLLER_EXEC_FLAGS),
            read8(core, POLICY_G_BATTLE_BUFFER_A), read8(core, 0x02023B24));
        policy_die(detail);
    }

    if (!evidence.boss_fainted) {
        write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1);
        write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP, 1);
        policy_run_raid_controller_round(core, &evidence, symbols, false);
    }
    if (!evidence.boss_fainted
        || (!evidence.runtime_cleaned
            && read8(
                core,
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER)
                    + POLICY_NEWBS_RAID_CAPTURE_ALLOWED_OFFSET) != 1)) {
        policy_die("real Raid controller damage did not reach the boss capture phase");
    }
    evidence.catch_phase_seen = true;
    policy_run_raid_frames(core, &evidence, 0, BATTLE_CORE_MENU_READY_FRAMES);
    for (uint32_t press = 0; press < 4; ++press) {
        write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR, 0);
        policy_run_raid_frames(core, &evidence, 1, 2);
        policy_run_raid_frames(core, &evidence, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    if (read8(core, BATTLE_CORE_CHOSEN_ACTIONS)
        == BATTLE_CORE_ACTION_USE_ITEM) {
        evidence.chosen_capture_action = BATTLE_CORE_ACTION_USE_ITEM;
    }
    policy_run_raid_frames(core, &evidence, 0, BATTLE_CORE_MENU_READY_FRAMES);
    for (uint32_t pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES
             && (!evidence.runtime_cleaned
                 || (read32(core, ADDR_BATTLE_TYPE_FLAGS)
                     & (POLICY_BATTLE_TYPE_DYNAMAX | POLICY_BATTLE_TYPE_DOUBLE
                        | POLICY_BATTLE_TYPE_INGAME_PARTNER)) != 0);
         ++pulse) {
        policy_run_raid_frames(core, &evidence, 1, 2);
        policy_run_raid_frames(core, &evidence, 0, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    policy_run_raid_frames(core, &evidence, 0, 60);
    evidence.ball_consumed = policy_observe_raw(
        core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
        BATTLE_CORE_MASTER_BALL, 1, 0, 0) == 0;
    evidence.policy_state_cleaned =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0
        && (read32(core, ADDR_BATTLE_TYPE_FLAGS)
            & (POLICY_BATTLE_TYPE_DYNAMAX | POLICY_BATTLE_TYPE_DOUBLE
               | POLICY_BATTLE_TYPE_INGAME_PARTNER)) == 0;
    if (evidence.chosen_capture_action != BATTLE_CORE_ACTION_USE_ITEM
        || !evidence.catch_phase_seen || !evidence.bag_opened
        || evidence.outcome != BATTLE_CORE_OUTCOME_CAUGHT
        || !evidence.ball_consumed || !evidence.runtime_cleaned
        || !evidence.policy_state_cleaned) {
        char detail[320];
        (void)snprintf(
            detail, sizeof(detail),
            "Raid existing-UI capture/end path did not naturally clean up: "
            "action=%u catch=%u bag=%u outcome=%u ball=%u runtime=%u "
            "policy=%u newbs=%08" PRIX32 " flags=%08" PRIX32,
            evidence.chosen_capture_action, evidence.catch_phase_seen,
            evidence.bag_opened, evidence.outcome, evidence.ball_consumed,
            evidence.runtime_cleaned, evidence.policy_state_cleaned,
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read32(core, ADDR_BATTLE_TYPE_FLAGS));
        policy_die(detail);
    }
    policy_verify_raid_pc_capture(core, &pc_fixture, &evidence);

    evidence.normal_wild_no_leak = policy_normal_battle_after_raid(
        core, symbols, false);
    evidence.normal_trainer_no_leak = policy_normal_battle_after_raid(
        core, symbols, true);
    return evidence;
}

static bool policy_test_raid_turn_limit_scheduler(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    struct RaidEndEvidence evidence = {0};
    (void)policy_start_raid_wild(core, field, symbols, 0, 1, 0, NULL);
    if (POLICY_OBSERVE0(core, symbols->is_raid) != 1
        || POLICY_OBSERVE0(core, symbols->is_catchable_raid) != 0
        || POLICY_OBSERVE0(core, symbols->raid_ui_shields) != 0
        || POLICY_OBSERVE0(core, symbols->raid_shields) != 0) {
        policy_die("no-capture one-turn Raid setup semantics differ");
    }
    policy_run_raid_controller_round(core, &evidence, symbols, false);
    for (uint32_t pulse = 0;
         pulse < BATTLE_CORE_END_INPUT_PULSES && !evidence.runtime_cleaned;
         ++pulse) {
        policy_run_raid_frames(core, &evidence, 1, 2);
        policy_run_raid_frames(core, &evidence, 0, BATTLE_CORE_END_INPUT_WAIT);
    }
    policy_run_raid_frames(core, &evidence, 0, 60);
    if (evidence.outcome != 5 || !evidence.runtime_cleaned
        || POLICY_OBSERVE0(core, symbols->is_raid) != 0
        || POLICY_OBSERVE0(core, symbols->is_catchable_raid) != 0) {
        policy_die("Raid turn-limit/no-capture cleanup semantics differ");
    }
    return true;
}

static void policy_test_raid_contracts(
    struct mCore *core,
    const struct Snapshot *field,
    const struct PolicySymbols *symbols
) {
    (void)policy_start_raid_wild(core, field, symbols, 5, 4, 1, NULL);
    const uint32_t duplicate_begin[] = {
        1, 0, (1U << 1) | (1U << 2), 5, 500, 500, 4, 1
    };
    if (policy_call(
            core, &symbols->raid_begin,
            duplicate_begin, ARRAY_LEN(duplicate_begin)) != 0
        || POLICY_CALL1(core, symbols->raid_partner, 1) != 1
        || POLICY_CALL1(core, symbols->raid_partner, 2) != 1
        || POLICY_CALL1(core, symbols->raid_partner, 3) != 0
        || POLICY_CALL0(core, symbols->raid_shields) != 5
        || POLICY_CALL1(core, symbols->mechanic_forced, 1) != 1
        || POLICY_CALL2(core, symbols->mechanic_can, 1, 3) != 1
        || POLICY_CALL2(core, symbols->mechanic_try, 1, 3) != 1
        || POLICY_CALL2(core, symbols->mechanic_try, 1, 3) != 0) {
        policy_die("Raid boss/partner/shield/capture/cleanup semantics differ");
    }
    for (uint32_t expected = 5; expected > 0; --expected) {
        if (POLICY_CALL0(core, symbols->raid_break) != 1
            || POLICY_CALL0(core, symbols->raid_shields) != expected - 1U) {
            policy_die("Raid fixed-UI shield depletion semantics differ");
        }
    }
    if (POLICY_CALL0(core, symbols->raid_break) != 0
        || POLICY_CALL0(core, symbols->raid_turn) != 1
        || POLICY_CALL1(core, symbols->raid_hp, 0) != 1
        || POLICY_CALL0(core, symbols->raid_capture) != 1
        || POLICY_CALL1(core, symbols->raid_end, 5) != 1) {
        policy_die("Raid boss/partner/shield/capture/cleanup semantics differ");
    }
    policy_finish_direct(core, symbols, BATTLE_CORE_OUTCOME_CAUGHT);
}

static void policy_print_species(const uint16_t species[PARTY_SIZE]) {
    putchar('[');
    for (uint32_t slot = 0; slot < PARTY_SIZE; ++slot) {
        if (slot) putchar(',');
        printf("%u", species[slot]);
    }
    putchar(']');
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256 NAME=ADDRESS...\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0) {
        policy_die("ROM SHA-256 mismatch");
    }
    struct PolicySymbols symbols;
    policy_parse_symbols(&symbols, argc, argv, 3);

    struct mLogger logger = {.log = policy_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) policy_die("mGBA core initialization failed");
    policy_log_core = core;
    if (!mCoreLoadFile(core, argv[1])) policy_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    if (log_problem_count) policy_die("mGBA warned/errored during natural field boot");
    struct Snapshot field = take_snapshot(core);

    policy_test_stat_inputs(core, &symbols);
    policy_test_candy(core, &symbols);
    policy_test_trainer_build(core, &symbols);
    policy_test_mechanics(core, &field, &symbols);
    policy_test_facility_matrix(core, &field, &symbols);
    struct FacilityEndEvidence facility_end = policy_test_facility_scheduler_end(
        core, &field, &symbols);
    uint16_t rental_species[PARTY_SIZE] = {0};
    uint32_t rental_count = policy_test_rental_generation(
        core, &field, &symbols, rental_species);
    policy_test_mirage(core, &field, &symbols);
    struct RaidEndEvidence raid_end = policy_test_raid_scheduler_e2e(
        core, &field, &symbols);
    policy_test_raid_contracts(core, &field, &symbols);
    raid_end.turn_limit_scheduler_end = policy_test_raid_turn_limit_scheduler(
        core, &field, &symbols);
    if (log_problem_count) policy_die("mGBA warned/errored during policy fixtures");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"t06_battle_policy_integration_v1\","
           "\"rom_sha256\":\"%s\",\"fixed_rtc_unix\":946684800,"
           "\"read_only\":true,\"boot_trace_segments\":%u,"
           "\"warnings_errors\":0,\"direct_calls\":%u,"
           "\"direct_call_instructions\":%" PRIu64 ","
           "\"payload_calls\":%u,\"actual_battle_setups\":%u,"
           "\"stat_inputs\":{\"exp_share_off_participant_only\":true,"
           "\"exp_share_on_unparticipated\":true,\"mint_nature\":6,"
           "\"ability_slot\":2,\"hyper_trained_iv\":31},"
           "\"exp_candy\":{\"selected_target_only\":true,"
           "\"zero_no_effect_not_consumed\":true,"
           "\"cap_clamped\":true,\"at_cap_not_consumed\":true},"
           "\"trainer_build\":{\"fully_specified\":true,"
           "\"unspecified_identity\":true,\"ev_total\":510},"
           "\"mechanics\":{\"modes\":[\"MEGA\",\"Z_MOVE\","
           "\"DYNAMAX\",\"TERASTAL\"],\"side_wide_exclusive\":true,"
           "\"one_use\":true,\"cross_mode_exclusive\":true,"
           "\"cleanup\":true},"
           "\"facility\":{\"formats\":3,\"rules\":8,"
           "\"matrix_cases\":24,\"frontier_flag\":true,"
           "\"persistent_effects_denied\":7,\"capture_denied\":true,"
           "\"scheduler_faint_end\":true,\"experience_before\":%u,"
           "\"experience_after\":%u,\"held_item_before\":%u,"
           "\"held_item_after\":%u,\"outcome\":%u,"
           "\"enemy_fainted\":%s,\"runtime_cleaned\":%s,"
           "\"rental_generation\":{\"bounded_call\":true,"
           "\"party_count\":%u,\"species\":",
           rom_sha256, BATTLE_CORE_FIELD_TRACE_SEGMENTS,
           policy_evidence.direct_calls, policy_evidence.instructions,
           policy_evidence.payload_calls, policy_evidence.actual_battle_setups,
           facility_end.experience_before, facility_end.experience_after,
           facility_end.item_before, facility_end.item_after, facility_end.outcome,
           facility_end.enemy_fainted ? "true" : "false",
           facility_end.runtime_cleaned ? "true" : "false", rental_count);
    policy_print_species(rental_species);
    printf("}},\"mirage\":{\"virtual_item\":900,"
           "\"pending_configure_actual_battle\":true,"
           "\"owner\":\"opponent_party_slot_0\","
           "\"opponent_battle_mon_virtualized\":true,"
           "\"opponent_original_restored_each_exit\":true,"
           "\"player_party_unchanged_each_exit\":true,"
           "\"battle_mon_virtualized\":true,"
           "\"consume_swap_mutation\":true,\"exit_paths\":7,"
           "\"party_original_restored_each_exit\":true,"
           "\"virtual_or_mutated_item_leaked_to_bag\":false,"
           "\"leaked_to_bag\":false},"
           "\"raid\":{\"high_difficulty_policy\":true,"
           "\"pending_configure_actual_battle\":true,"
           "\"existing_three_controller_ui_initialized\":true,"
           "\"boss_side\":1,"
           "\"partner_mask\":6,\"shield_boundary_max\":5,"
           "\"initial_shields\":%u,\"shield_breaks\":%u,"
           "\"controller_turns\":%u,\"player_pp_before\":%u,"
           "\"player_pp_after\":%u,\"boss_fainted\":%s,"
           "\"catch_phase_seen\":%s,\"capture_action\":%u,"
           "\"bag_opened\":%s,\"ball_consumed\":%s,"
           "\"pc_storage_pointer_dynamic\":%s,"
           "\"full_party_pc_routed\":%s,"
           "\"pc_box_id\":%u,\"pc_box_position\":%u,"
           "\"pc_captured_species\":%u,"
           "\"party_count_after_capture\":%u,"
           "\"party_species_unchanged\":%s,"
           "\"stock_pc_box_stride_80\":%s,"
           "\"adjacent_pc_slot_unchanged\":%s,"
           "\"outcome\":%u,\"runtime_cleaned\":%s,"
           "\"policy_state_cleaned\":%s,"
           "\"normal_wild_no_leak\":%s,"
           "\"normal_trainer_no_leak\":%s,"
           "\"partner_spread_moves_preserved\":%s,"
           "\"turn_limit_checked\":true,"
           "\"turn_limit_scheduler_end\":%s,"
           "\"capture_allowed_path\":true,\"capture_denied_path\":true,"
           "\"contract_unit_direct_calls\":true,"
           "\"cleanup\":true,\"raid_state_completion_scheduler_e2e\":true},"
           "\"non_e2e_routes\":[],"
           "\"unreached_routes\":[],\"artifacts_written\":[]}\n",
           raid_end.initial_shields, raid_end.shield_breaks,
           raid_end.controller_turns, raid_end.player_pp_before,
           raid_end.player_pp_after,
           raid_end.boss_fainted ? "true" : "false",
           raid_end.catch_phase_seen ? "true" : "false",
           raid_end.chosen_capture_action,
           raid_end.bag_opened ? "true" : "false",
           raid_end.ball_consumed ? "true" : "false",
           raid_end.pc_storage_pointer_dynamic ? "true" : "false",
           raid_end.full_party_pc_routed ? "true" : "false",
           (unsigned)raid_end.pc_box_id,
           (unsigned)raid_end.pc_box_position,
           (unsigned)raid_end.pc_captured_species,
           (unsigned)raid_end.party_count_after_capture,
           raid_end.party_species_unchanged ? "true" : "false",
           raid_end.stock_pc_box_stride_80 ? "true" : "false",
           raid_end.adjacent_pc_slot_unchanged ? "true" : "false",
           raid_end.outcome,
           raid_end.runtime_cleaned ? "true" : "false",
           raid_end.policy_state_cleaned ? "true" : "false",
           raid_end.normal_wild_no_leak ? "true" : "false",
           raid_end.normal_trainer_no_leak ? "true" : "false",
           raid_end.partner_spread_moves_preserved ? "true" : "false",
           raid_end.turn_limit_scheduler_end ? "true" : "false");

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
