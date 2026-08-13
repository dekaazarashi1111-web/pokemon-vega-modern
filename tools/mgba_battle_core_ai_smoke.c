/*
 * T06 CFRU-on-Vega AI acceptance runner for libmGBA 0.10.2.
 *
 * The runner is deliberately read-only.  It embeds the reviewed T01/T06
 * lifecycle helpers, enters a real Vega trainer battle, and then exercises the
 * linked CFRU AI entry points on the emulated ARM7TDMI.  Every reported route
 * has a hard assertion; an unavailable route terminates before PASS is
 * printed.  Every strategy fixture contains at least one available competing
 * move, so a one-legal-move route can never be presented as AI evidence.
 */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    T06_AI_SCHEMA_VERSION = 1,
    T06_AI_PROFILE_BASIC = 1,
    T06_AI_PROFILE_SEMI_SMART = 3,
    T06_AI_PROFILE_FULL_SMART = 5,

    T06_AI_MODE_STANDARD = 0,
    T06_AI_MODE_MEGA = 1,
    T06_AI_MODE_Z_MOVE = 2,
    T06_AI_MODE_DYNAMAX = 3,
    T06_AI_MODE_TERASTAL = 4,

    T06_AI_ACTION_USE_MOVE = 0,
    T06_AI_ACTION_USE_ITEM = 1,
    T06_AI_ACTION_SWITCH = 2,

    T06_AI_BATTLE_TYPE_BATTLE_TOWER = 0x00000100,
    T06_AI_BATTLE_TYPE_DYNAMAX = 0x40000000,

    T06_AI_MOVE_SWORDS_DANCE = 14,
    T06_AI_MOVE_TACKLE = 33,
    T06_AI_MOVE_GROWL = 45,
    T06_AI_MOVE_EMBER = 52,
    T06_AI_MOVE_WATER_GUN = 55,
    T06_AI_MOVE_SURF = 57,
    T06_AI_MOVE_THUNDERBOLT = 85,
    T06_AI_MOVE_EARTHQUAKE = 89,
    T06_AI_MOVE_RECOVER = 105,
    T06_AI_MOVE_PROTECT = 182,
    T06_AI_MOVE_SPIKES = 191,
    T06_AI_MOVE_RAPID_SPIN = 229,
    T06_AI_MOVE_RAIN_DANCE = 240,
    T06_AI_MOVE_FOLLOW_ME = 266,
    T06_AI_MOVE_HELPING_HAND = 270,
    T06_AI_MOVE_U_TURN = 530,
    T06_AI_MOVE_STEALTH_ROCK = 550,
    T06_AI_MOVE_TAILWIND = 554,
    T06_AI_MOVE_ELECTRIC_TERRAIN = 696,
    T06_AI_MOVE_TRICK_ROOM = 703,
    T06_AI_MOVE_WIDE_GUARD = 709,

    T06_AI_TYPE_NORMAL = 0,
    T06_AI_TYPE_FLYING = 2,
    T06_AI_TYPE_GROUND = 4,
    T06_AI_TYPE_GHOST = 7,
    T06_AI_TYPE_FIRE = 10,
    T06_AI_TYPE_WATER = 11,
    T06_AI_TYPE_BLANK = 20,

    T06_AI_ITEM_FULL_RESTORE = 19,
    T06_AI_ITEM_CHARIZARDITE_X = 748,
    T06_AI_ITEM_FIRIUM_Z = 803,
    T06_AI_MEGA_SOURCE_ITEM = 534,
    T06_AI_MEGA_METHOD = 0xFE,
    T06_AI_MEGA_VARIANT = 0,
    T06_AI_MON_DATA_HELD_ITEM = 12,
    T06_AI_PARTY_SIZE = 6,
    T06_AI_MEGA_FIXTURE_SPECIES = 157,
    T06_AI_BATTLE_MON_ATTACK = 0x02,
    T06_AI_BATTLE_MON_DEFENSE = 0x04,
    T06_AI_BATTLE_MON_SPEED = 0x06,
    T06_AI_BATTLE_MON_SP_ATTACK = 0x08,
    T06_AI_BATTLE_MON_SP_DEFENSE = 0x0A,
    T06_AI_BATTLE_MON_TYPE3 = 0x18,
    T06_AI_BATTLE_MON_TYPE1 = 0x21,
    T06_AI_BATTLE_MON_TYPE2 = 0x22,
    T06_AI_BATTLE_MON_MAX_HP = 0x2C,
    T06_AI_BATTLE_MON_ITEM = 0x2E,
    T06_AI_BATTLE_MON_ABILITY = 0x38,
    T06_AI_ABILITY_SWIFT_SWIM = 33,

    T06_AI_NEWBS_DYNAMAX_MON_ID = 0x500,
    T06_AI_NEWBS_DYNAMAX_POTENTIAL = 0x522,
    T06_AI_NEWBS_TERASTAL_POTENTIAL = 0x532,
    T06_AI_NEWBS_TERASTAL_MON_ID = 0x542,
    T06_AI_NEWBS_MEGA_POTENTIAL = 0x544,
    T06_AI_POLICY_OFFSET = 0x558,
    T06_AI_PENDING_SHADOW = 0x0203E040,
    T06_AI_PENDING_MAGIC = 0x54303650,
    T06_AI_PENDING_ACTIVE = 4,
    T06_AI_PENDING_PROFILE = 6,
    /* NewBattleStruct.ai.zMoveHelper (ARM offsetof); despite the following
     * u32 randSeed alignment, this u16 begins at ai + 0x00. */
    T06_AI_NEWBS_TRANSFORMED_MOVE_SOURCE = 0x288,
    /* NewBattleStruct.vegaBattlePolicy.ai_cache_snapshot.  ARM offsetof:
     * policy=0x558, snapshot=0x3C, sizeof(snapshot)=0x2D0. */
    T06_AI_POLICY_CACHE_SNAPSHOT = 0x594,
    T06_AI_POLICY_CACHE_SNAPSHOT_SIZE = 0x2D0,
    T06_AI_HISTORY_ITEMS = 0x24,
    T06_AI_HISTORY_ITEM_COUNT = 0x2C,
    T06_AI_RESOURCES_HISTORY_POINTER = 24,
    T06_AI_BATTLE_STRUCT_MON_TO_SWITCH = 92,
    T06_AI_BATTLE_STRUCT_SWITCHOUT_INDEX = 0x92,
    T06_AI_BATTLE_STRUCT_CHOSEN_ITEM = 192,
    T06_AI_SIDE_STATUSES = 0x02023D3E,
    T06_AI_SIDE_TIMERS = 0x02023D44,
    T06_AI_SIDE_TIMER_SIZE = 0x0C,
    T06_AI_SIDE_TIMER_HAZARDS = 0x0A,
    T06_AI_SIDE_STATUS_SPIKES = 0x10,
    T06_AI_STATUSES3 = 0x02023D5C,
    T06_AI_DISABLE_STRUCTS = 0x02023D6C,
    T06_AI_BATTLE_WEATHER = 0x02023E7C,
    T06_AI_TERRAIN_TYPE = 0x0203DFA0,
    T06_AI_DISABLE_STRUCT_SIZE = 0x1C,
    T06_AI_PERISH_TIMER_OFFSET = 0x0F,
    T06_AI_STATUS3_PERISH_SONG = 0x20,
    T06_AI_STATUS3_YAWN = 0x0800,

    T06_AI_CANONICAL_MOVE_REPOINT = 0x080001CC,
    T06_AI_CANONICAL_MOVE_COUNT = 1063,
    T06_AI_CANONICAL_MOVE_STRIDE = 12,
    T06_AI_SECONDARY_CHANCE_OFFSET = 5,

    T06_AI_SINGLE_COLD_LIMIT = 3300000,
    T06_AI_SINGLE_WARM_LIMIT = 450000,
    T06_AI_DOUBLE_COLD_LIMIT = 8000000,
    T06_AI_DOUBLE_WARM_LIMIT = 800000,
};

struct T06AiSymbols {
    uint32_t try_action;
    uint32_t setup;
    uint32_t choose_move;
    uint32_t clear_cache;
    uint32_t configure_policy;
    uint32_t resolve_profile;
};

struct T06AiProfileObservation {
    uint8_t requested;
    uint32_t resolved;
    uint32_t effective;
    uint8_t chosen_slot;
    uint16_t chosen_move;
    uint8_t target;
};

struct T06AiScenario {
    const char *name;
    const char *category;
    bool is_double;
    uint16_t moves[4];
    uint8_t pp[4];
    uint8_t expected_slots;
    uint8_t expected_targets;
    uint8_t attacker_hp_percent;
    uint8_t target_hp_percent;
    uint8_t target_type1;
    uint8_t target_type2;
};

struct T06AiScenarioObservation {
    uint8_t chosen_slot;
    uint16_t chosen_move;
    uint8_t target;
    uint32_t effective_flags;
    uint64_t cycles;
    uint64_t instructions;
    uint8_t legal_competing_moves;
};

struct T06AiActionObservation {
    uint8_t action;
    uint16_t parameter;
    uint8_t target;
    uint64_t cycles;
    uint64_t instructions;
};

struct T06AiPerformanceObservation {
    bool is_double;
    uint64_t cold_cycles;
    uint64_t warm_cycles;
    uint64_t cold_instructions;
    uint64_t warm_instructions;
    uint8_t action;
    uint16_t parameter;
    uint8_t target;
    uint64_t state_digest;
};

struct T06AiMechanicObservation {
    uint8_t mode;
    uint8_t dynamax_candidate;
    uint8_t dynamax_potential;
    uint8_t terastal_candidate;
    uint8_t terastal_potential;
    uint32_t mega_candidate;
    uint16_t transformed_move_source;
    uint32_t effective_flags;
    uint8_t action;
    uint16_t parameter;
    uint8_t target;
    uint8_t chosen_slot;
    uint16_t chosen_move;
};

static unsigned t06_ai_scenario_contract_failures;

static const struct T06AiScenario T06_AI_SCENARIOS[] = {
    {
        "ko_damage_choice", "KO", false,
        {T06_AI_MOVE_EMBER, T06_AI_MOVE_TACKLE, 0, 0},
        {25, 35, 0, 0}, 0x01, 0x01, 100, 25,
        T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "two_hit_damage_choice", "TWO_HIT_KO", false,
        {T06_AI_MOVE_WATER_GUN, T06_AI_MOVE_TACKLE, 0, 0},
        {25, 35, 0, 0}, 0x01, 0x01, 100, 70,
        T06_AI_TYPE_FIRE, T06_AI_TYPE_FIRE,
    },
    {
        "normal_immunity_avoidance", "IMMUNITY", false,
        {T06_AI_MOVE_TACKLE, T06_AI_MOVE_EMBER, 0, 0},
        {35, 25, 0, 0}, 0x02, 0x01, 100, 100,
        T06_AI_TYPE_GHOST, T06_AI_TYPE_GHOST,
    },
    {
        "hazard_install", "HAZARD", false,
        {T06_AI_MOVE_STEALTH_ROCK, T06_AI_MOVE_TACKLE, 0, 0},
        {20, 35, 0, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "hazard_remove", "HAZARD_REMOVE", false,
        {T06_AI_MOVE_RAPID_SPIN, T06_AI_MOVE_EMBER, 0, 0},
        {40, 25, 0, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "setup_attack", "SETUP", false,
        {T06_AI_MOVE_SWORDS_DANCE, T06_AI_MOVE_TACKLE, 0, 0},
        {20, 35, 0, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "self_recovery", "RECOVERY", false,
        {T06_AI_MOVE_RECOVER, T06_AI_MOVE_EMBER, 0, 0},
        {10, 25, 0, 0},
        0x01, 0x01, 25, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "pivot_u_turn", "PIVOT", false,
        {T06_AI_MOVE_U_TURN, T06_AI_MOVE_EMBER, T06_AI_MOVE_TACKLE, 0},
        {20, 25, 35, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_WATER, T06_AI_TYPE_WATER,
    },
    {
        "weather_rain", "WEATHER", false,
        {T06_AI_MOVE_RAIN_DANCE, T06_AI_MOVE_WATER_GUN, 0, 0},
        {5, 25, 0, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_FIRE, T06_AI_TYPE_FIRE,
    },
    {
        "field_electric", "FIELD", false,
        {T06_AI_MOVE_ELECTRIC_TERRAIN, T06_AI_MOVE_THUNDERBOLT, 0, 0},
        {10, 15, 0, 0},
        0x01, 0x01, 100, 100, T06_AI_TYPE_WATER, T06_AI_TYPE_WATER,
    },
    {
        "double_target", "DOUBLE_TARGET", true,
        {T06_AI_MOVE_THUNDERBOLT, T06_AI_MOVE_SURF, 0, 0},
        {15, 15, 0, 0},
        0x01, 0x05, 100, 100, T06_AI_TYPE_WATER, T06_AI_TYPE_WATER,
    },
    {
        "double_ally_harm_avoidance", "ALLY_HARM_AVOIDANCE",
        true,
        {T06_AI_MOVE_EARTHQUAKE, T06_AI_MOVE_THUNDERBOLT, 0, 0},
        {10, 15, 0, 0}, 0x02, 0x05, 100, 100,
        T06_AI_TYPE_WATER, T06_AI_TYPE_FLYING,
    },
    {
        "double_protect", "PROTECT", true,
        {T06_AI_MOVE_PROTECT, T06_AI_MOVE_THUNDERBOLT, 0, 0},
        {10, 15, 0, 0},
        0x01, 0x0F, 30, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "double_wide_guard", "WIDE_GUARD", true,
        {T06_AI_MOVE_WIDE_GUARD, T06_AI_MOVE_PROTECT, 0, 0},
        {10, 10, 0, 0},
        0x01, 0x0F, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "double_tailwind", "TAILWIND", true,
        {T06_AI_MOVE_TAILWIND, T06_AI_MOVE_THUNDERBOLT, 0, 0},
        {15, 15, 0, 0},
        0x01, 0x0F, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "double_trick_room", "TRICK_ROOM", true,
        {T06_AI_MOVE_TRICK_ROOM, T06_AI_MOVE_THUNDERBOLT, 0, 0},
        {5, 15, 0, 0},
        0x01, 0x0F, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "double_follow_me", "FOLLOW_ME", true,
        {T06_AI_MOVE_FOLLOW_ME, T06_AI_MOVE_TACKLE, 0, 0},
        {20, 35, 0, 0},
        0x01, 0x0F, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
    {
        "double_helping_hand", "HELPING_HAND", true,
        {T06_AI_MOVE_HELPING_HAND, T06_AI_MOVE_TACKLE, 0, 0},
        {20, 35, 0, 0},
        0x01, 0x08, 100, 100, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL,
    },
};

static void t06_ai_die(const char *message)
{
    fprintf(stderr, "mgba-battle-core-ai-smoke: %s\n", message);
    exit(1);
}

static void t06_ai_write32(struct mCore *core, uint32_t address, uint32_t value)
{
    for (unsigned byte = 0; byte < 4; ++byte)
        write8(core, address + byte, (uint8_t)(value >> (byte * 8)));
}

static void t06_ai_set_hp_percent(struct mCore *core, unsigned battler,
                                  uint8_t percent)
{
    uint32_t mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
    uint16_t max_hp = read16(core, mon + T06_AI_BATTLE_MON_MAX_HP);
    uint16_t hp;
    if (max_hp < 100) {
        max_hp = 100;
        write16(core, mon + T06_AI_BATTLE_MON_MAX_HP, max_hp);
    }
    hp = (uint16_t)((max_hp * percent) / 100U);
    if (hp == 0 && percent != 0) hp = 1;
    write16(core, mon + BATTLE_CORE_MON_HP, hp);
}

static void t06_ai_set_types(struct mCore *core, unsigned battler,
                             uint8_t type1, uint8_t type2)
{
    uint32_t mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
    write8(core, mon + T06_AI_BATTLE_MON_TYPE1, type1);
    write8(core, mon + T06_AI_BATTLE_MON_TYPE2, type2);
    write8(core, mon + T06_AI_BATTLE_MON_TYPE3, T06_AI_TYPE_BLANK);
}

static void t06_ai_set_active_moves(struct mCore *core, unsigned battler,
                                    const uint16_t moves[4],
                                    const uint8_t pp[4])
{
    uint32_t mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
    for (unsigned slot = 0; slot < 4; ++slot) {
        write16(core, mon + BATTLE_MON_MOVES_OFFSET + slot * 2, moves[slot]);
        write8(core, mon + BATTLE_MON_PP_OFFSET + slot, pp[slot]);
    }
}

static void t06_ai_seed(struct mCore *core, uint32_t salt)
{
    t06_ai_write32(core, BATTLE_CORE_GLOBAL_RNG,
                   UINT32_C(0x12345678) ^ (salt * UINT32_C(0x9E3779B9)));
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (!newbs) t06_ai_die("gNewBS is unavailable while seeding AI");
    t06_ai_write32(core, newbs + NEWBS_AI_RAND_SEED_OFFSET,
                   UINT32_C(0xA5A55A5A) ^ salt);
}

static void t06_ai_clear_cold_cache(struct mCore *core,
                                    const struct T06AiSymbols *symbols)
{
    (void)call_preserving(core, symbols->clear_cache, 0, 0, 0, 0);
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    uint8_t flags = read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE);
    if (flags & NEWBS_CALCULATED_PREDICTIONS_BIT)
        t06_ai_die("ClearCachedAIData left prediction-cache flag set");
}

static size_t t06_ai_prediction_cache_size(void)
{
    return (NEWBS_AI_END - NEWBS_AI_CACHE_OFFSET) + 5
        + T06_AI_POLICY_CACHE_SNAPSHOT_SIZE;
}

static uint8_t *t06_ai_capture_prediction_cache(struct mCore *core)
{
    const size_t upstream_size = (NEWBS_AI_END - NEWBS_AI_CACHE_OFFSET) + 5;
    uint8_t *upstream = capture_prediction_cache(core);
    uint8_t *combined = malloc(t06_ai_prediction_cache_size());
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    if (!combined) t06_ai_die("T06 prediction-cache allocation failed");
    memcpy(combined, upstream, upstream_size);
    free(upstream);
    for (size_t byte = 0; byte < T06_AI_POLICY_CACHE_SNAPSHOT_SIZE; ++byte) {
        combined[upstream_size + byte] = read8(
            core, newbs + T06_AI_POLICY_CACHE_SNAPSHOT + byte);
    }
    return combined;
}

static void t06_ai_overlay_prediction_cache(struct mCore *core,
                                             const uint8_t *cache)
{
    const size_t upstream_size = (NEWBS_AI_END - NEWBS_AI_CACHE_OFFSET) + 5;
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    overlay_prediction_cache(core, cache);
    for (size_t byte = 0; byte < T06_AI_POLICY_CACHE_SNAPSHOT_SIZE; ++byte) {
        write8(core, newbs + T06_AI_POLICY_CACHE_SNAPSHOT + byte,
               cache[upstream_size + byte]);
    }
}

static void t06_ai_verify_trainer_runtime(struct mCore *core)
{
    if (!(read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER)
        || read8(core, ADDR_BATTLERS_COUNT) != 2
        || (read8(core, ADDR_ABSENT_BATTLER_FLAGS) & 3U)
        || !read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER)
        || !read32(core, ADDR_BATTLE_STRUCT_POINTER)
        || !read32(core, ADDR_BATTLE_RESOURCES_POINTER)) {
        t06_ai_die("real Vega trainer battle runtime was not initialized");
    }
    if (read16(core, ADDR_BATTLE_MONS) != 7
        || read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE) != 4) {
        t06_ai_die("trainer 328 identity differs from the real Vega setup path");
    }
}

static void t06_ai_setup_profile_battle(struct mCore *core,
                                        const struct Snapshot *field,
                                        const struct T06AiSymbols *symbols,
                                        uint8_t profile, uint8_t mode)
{
    uint8_t player[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 7, 5, NULL, NULL, player);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write16(core, BATTLE_CORE_TRAINER_MODE, 0);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 328);
    if (call_preserving(core, symbols->configure_policy,
                        profile, mode, 0, 0) != 1) {
        t06_ai_die("VegaConfigureNextBattlePolicy rejected a named profile/mode");
    }
    if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0
        || read32(core, T06_AI_PENDING_SHADOW) != T06_AI_PENDING_MAGIC
        || read8(core, T06_AI_PENDING_SHADOW + T06_AI_PENDING_ACTIVE) != 1
        || read8(core, T06_AI_PENDING_SHADOW + T06_AI_PENDING_PROFILE)
               != profile) {
        t06_ai_die("named profile was not retained in pre-battle shadow");
    }
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen)
        t06_ai_die("trainer setup did not execute CFRU payload code");
    run_fixed_frames(core);
    t06_ai_verify_trainer_runtime(core);
    make_max_party(core);
    configure_party_moves(core);
    sync_active_moves(core);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, T06_AI_PARTY_SIZE);
    write8(core, ADDR_ACTIVE_BATTLER, 1);
    verify_fixture(core, false);
}

static struct T06AiProfileObservation t06_ai_run_profile(
    struct mCore *core, const struct Snapshot *field,
    const struct T06AiSymbols *symbols, uint8_t profile)
{
    struct T06AiProfileObservation result = {.requested = profile};
    static const uint16_t only_tackle[4] = {T06_AI_MOVE_TACKLE, 0, 0, 0};
    static const uint8_t only_tackle_pp[4] = {35, 0, 0, 0};
    t06_ai_setup_profile_battle(core, field, symbols, profile,
                                T06_AI_MODE_STANDARD);
    result.resolved = call_preserving(core, symbols->resolve_profile,
                                      1, 7, 0, 0);
    if (result.resolved != profile)
        t06_ai_die("runtime profile resolver did not return the requested bits");
    if (call_preserving(core, symbols->resolve_profile,
                        1, UINT32_C(1) << 30, 0, 0)
        != (UINT32_C(1) << 30)) {
        t06_ai_die("profile resolver overrode an authoritative high-bit AI mode");
    }
    t06_ai_set_active_moves(core, 1, only_tackle, only_tackle_pp);
    t06_ai_seed(core, profile);
    t06_ai_clear_cold_cache(core, symbols);
    (void)call_rom(core, symbols->setup, 0xF);
    result.effective = effective_ai_flags(core);
    if (result.effective != profile)
        t06_ai_die("BattleAI_SetupAIData effective bits differ from named profile");
    struct Measurement choice = call_rom(core, symbols->choose_move, 0);
    result.chosen_slot = (uint8_t)choice.return_value;
    result.target = read8(core, ADDR_BANK_TARGET);
    if (result.chosen_slot != 0 || result.target != 0)
        t06_ai_die("named-profile deterministic move fixture chose an unexpected route");
    result.chosen_move = read16(core,
        ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_MON_MOVES_OFFSET);
    return result;
}

static struct T06AiScenarioObservation t06_ai_run_scenario(
    struct mCore *core, const struct Snapshot *full_profile,
    const struct T06AiSymbols *symbols,
    const struct T06AiScenario *scenario, unsigned index)
{
    struct T06AiScenarioObservation result = {0};
    unsigned available_moves = 0;
    unsigned available_competitors = 0;
    for (unsigned slot = 0; slot < 4; ++slot) {
        if (scenario->moves[slot] != 0 && scenario->pp[slot] != 0) {
            ++available_moves;
            if (!(scenario->expected_slots & (1U << slot)))
                ++available_competitors;
        }
    }
    if (available_moves < 2 || available_competitors == 0)
        t06_ai_die("differential AI scenario lacks a legal competing move");
    result.legal_competing_moves = (uint8_t)available_competitors;
    restore_snapshot(core, full_profile);
    if (scenario->is_double) {
        make_double(core);
        sync_active_moves(core);
        uint32_t battle_struct = read32(core, ADDR_BATTLE_STRUCT_POINTER);
        for (unsigned battler = 0; battler < 4; ++battler) {
            write8(core, battle_struct + T06_AI_BATTLE_STRUCT_MON_TO_SWITCH
                         + battler,
                   T06_AI_PARTY_SIZE);
        }
    }
    write8(core, ADDR_ACTIVE_BATTLER, 1);
    t06_ai_set_active_moves(core, 1, scenario->moves, scenario->pp);
    t06_ai_set_hp_percent(core, 1, scenario->attacker_hp_percent);
    t06_ai_set_hp_percent(core, 0, scenario->target_hp_percent);
    t06_ai_set_types(core, 0, scenario->target_type1, scenario->target_type2);

    /* Stable stats make KO/2HKO and immunity comparisons independent of the
     * low-level story trainer's incidental IV/personality rolls. */
    uint32_t attacker = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    uint32_t defender = ADDR_BATTLE_MONS;
    /* At level 50 against 100 defence, 120 SpA makes STAB Ember a clean
     * one-hit KO at 25 HP and super-effective Water Gun a clean two-hit KO at
     * 70 HP.  The 100 Attack Tackle remains outside both boundaries. */
    write16(core, attacker + T06_AI_BATTLE_MON_ATTACK, 100);
    write16(core, attacker + T06_AI_BATTLE_MON_SP_ATTACK, 120);
    write16(core, attacker + T06_AI_BATTLE_MON_SPEED, 140);
    write16(core, defender + T06_AI_BATTLE_MON_DEFENSE, 100);
    write16(core, defender + T06_AI_BATTLE_MON_SP_DEFENSE, 100);
    write16(core, defender + T06_AI_BATTLE_MON_SPEED, 100);
    write8(core, attacker + BATTLE_CORE_MON_LEVEL, 50);
    write8(core, defender + BATTLE_CORE_MON_LEVEL, 50);
    if (scenario->is_double) {
        /* Both foes are Flying while the ally is grounded: Earthquake cannot
         * damage either foe and would only hurt the ally, whereas the focused
         * Electric move has a valid opposing target. */
        if (strcmp(scenario->category, "ALLY_HARM_AVOIDANCE") == 0) {
            t06_ai_set_types(core, 2, T06_AI_TYPE_WATER, T06_AI_TYPE_FLYING);
            t06_ai_set_types(core, 3, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL);
        }
        if (strcmp(scenario->category, "PROTECT") == 0) {
            static const uint16_t threat_moves[4] = {
                T06_AI_MOVE_THUNDERBOLT, T06_AI_MOVE_SURF, 0, 0,
            };
            static const uint8_t threat_pp[4] = {15, 15, 0, 0};
            t06_ai_set_active_moves(core, 0, threat_moves, threat_pp);
            t06_ai_set_active_moves(core, 2, threat_moves, threat_pp);
            write16(core, defender + T06_AI_BATTLE_MON_ATTACK, 300);
            write16(core, defender + T06_AI_BATTLE_MON_SP_ATTACK, 300);
            write16(core, attacker + T06_AI_BATTLE_MON_DEFENSE, 50);
            write16(core, attacker + T06_AI_BATTLE_MON_SP_DEFENSE, 50);
        }
        if (strcmp(scenario->category, "WIDE_GUARD") == 0) {
            static const uint16_t spread_moves[4] = {
                T06_AI_MOVE_SURF, T06_AI_MOVE_EARTHQUAKE, 0, 0,
            };
            static const uint8_t spread_pp[4] = {15, 10, 0, 0};
            t06_ai_set_active_moves(core, 0, spread_moves, spread_pp);
            t06_ai_set_active_moves(core, 2, spread_moves, spread_pp);
        }
        if (strcmp(scenario->category, "TAILWIND") == 0
            || strcmp(scenario->category, "TRICK_ROOM") == 0) {
            write16(core, ADDR_BATTLE_MONS
                          + 0 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_SPEED, 220);
            write16(core, ADDR_BATTLE_MONS
                          + 2 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_SPEED, 200);
            write16(core, ADDR_BATTLE_MONS
                          + 1 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_SPEED, 40);
            write16(core, ADDR_BATTLE_MONS
                          + 3 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_SPEED, 50);
        }
        if (strcmp(scenario->category, "FOLLOW_ME") == 0) {
            static const uint16_t focused_moves[4] = {
                T06_AI_MOVE_THUNDERBOLT, T06_AI_MOVE_TACKLE, 0, 0,
            };
            static const uint8_t focused_pp[4] = {15, 35, 0, 0};
            t06_ai_set_active_moves(core, 0, focused_moves, focused_pp);
            t06_ai_set_active_moves(core, 2, focused_moves, focused_pp);
            /* Keep a legal damaging competitor, but make its Normal damage
             * ineffective against both opposing Ghosts.  The naturally
             * populated Thunderbolt prediction can then exercise the real
             * Follow Me partner-protection rule without a forced-only row. */
            t06_ai_set_types(core, 0, T06_AI_TYPE_GHOST, T06_AI_TYPE_GHOST);
            t06_ai_set_types(core, 2, T06_AI_TYPE_GHOST, T06_AI_TYPE_GHOST);
            t06_ai_set_hp_percent(core, 3, 10);
        }
        if (strcmp(scenario->category, "HELPING_HAND") == 0) {
            static const uint16_t partner_moves[4] = {
                T06_AI_MOVE_THUNDERBOLT, T06_AI_MOVE_TACKLE, 0, 0,
            };
            static const uint8_t partner_pp[4] = {15, 35, 0, 0};
            t06_ai_set_active_moves(core, 3, partner_moves, partner_pp);
            write16(core, BATTLE_CORE_CHOSEN_MOVES + 3U * 2U,
                    T06_AI_MOVE_THUNDERBOLT);
            write8(core, read32(core, ADDR_BATTLE_STRUCT_POINTER) + 12U + 3U,
                   0);
            write16(core, ADDR_BATTLE_MONS
                          + 3 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_ATTACK, 300);
            write16(core, ADDR_BATTLE_MONS
                          + 3 * BATTLE_MON_SIZE + T06_AI_BATTLE_MON_SP_ATTACK, 300);
        }
    }
    if (strcmp(scenario->category, "RECOVERY") == 0) {
        static const uint16_t pressure_moves[4] = {
            T06_AI_MOVE_WATER_GUN, 0, 0, 0,
        };
        static const uint8_t pressure_pp[4] = {25, 0, 0, 0};
        t06_ai_set_active_moves(core, 0, pressure_moves, pressure_pp);
        write16(core, defender + T06_AI_BATTLE_MON_SP_ATTACK, 120);
        write16(core, attacker + T06_AI_BATTLE_MON_SP_DEFENSE, 100);
    }
    if (strcmp(scenario->category, "PIVOT") == 0) {
        static const uint16_t pressure_moves[4] = {
            T06_AI_MOVE_WATER_GUN, 0, 0, 0,
        };
        static const uint8_t pressure_pp[4] = {25, 0, 0, 0};
        t06_ai_set_active_moves(core, 0, pressure_moves, pressure_pp);
        write16(core, attacker + T06_AI_BATTLE_MON_ATTACK, 200);
        write16(core, attacker + T06_AI_BATTLE_MON_SP_ATTACK, 40);
        write16(core, attacker + T06_AI_BATTLE_MON_SP_DEFENSE, 100);
        write16(core, defender + T06_AI_BATTLE_MON_SP_ATTACK, 300);
    }
    if (strcmp(scenario->category, "WEATHER") == 0) {
        write16(core, attacker + T06_AI_BATTLE_MON_ABILITY,
                T06_AI_ABILITY_SWIFT_SWIM);
    }
    if (strcmp(scenario->category, "HAZARD_REMOVE") == 0) {
        write16(core, T06_AI_SIDE_STATUSES + 2,
                (uint16_t)(read16(core, T06_AI_SIDE_STATUSES + 2)
                           | T06_AI_SIDE_STATUS_SPIKES));
        uint32_t hazards = T06_AI_SIDE_TIMERS + T06_AI_SIDE_TIMER_SIZE
            + T06_AI_SIDE_TIMER_HAZARDS;
        write8(core, hazards, (uint8_t)(read8(core, hazards) | 1U));
    }
    if (strcmp(scenario->category, "FIELD") == 0) {
        t06_ai_write32(core, T06_AI_STATUSES3 + 4,
                       read32(core, T06_AI_STATUSES3 + 4)
                           | T06_AI_STATUS3_YAWN);
    }

    t06_ai_seed(core, UINT32_C(0x100) + index);
    t06_ai_clear_cold_cache(core, symbols);
    if (strcmp(scenario->category, "WIDE_GUARD") == 0
        || strcmp(scenario->category, "FOLLOW_ME") == 0
        || strcmp(scenario->category, "HELPING_HAND") == 0) {
        (void)call_rom(core, symbols->try_action, 0);
    }
    struct Measurement setup = call_rom(core, symbols->setup, 0xF);
    result.effective_flags = effective_ai_flags(core);
    struct Measurement choice = call_rom(core, symbols->choose_move, 0);
    result.chosen_slot = (uint8_t)choice.return_value;
    result.target = read8(core, ADDR_BANK_TARGET);
    result.cycles = setup.cycles + choice.cycles;
    result.instructions = setup.instructions + choice.instructions;
    if (result.effective_flags != T06_AI_PROFILE_FULL_SMART
        || result.chosen_slot >= 4
        || !(scenario->expected_slots & (1U << result.chosen_slot))
        || !(scenario->expected_targets & (1U << result.target))) {
        uint32_t resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
        uint32_t thinking = resources
            ? read32(core, resources + 20U) : 0;
        fprintf(stderr,
                "mgba-battle-core-ai-smoke: scenario=%s category=%s "
                "flags=%" PRIu32 " slot=%u target=%u expected=%u/%u "
                "scores=%d,%d,%d,%d\n",
                scenario->name, scenario->category, result.effective_flags,
                result.chosen_slot, result.target, scenario->expected_slots,
                scenario->expected_targets,
                thinking ? (int8_t)read8(core, thinking + 4U) : -128,
                thinking ? (int8_t)read8(core, thinking + 5U) : -128,
                thinking ? (int8_t)read8(core, thinking + 6U) : -128,
                thinking ? (int8_t)read8(core, thinking + 7U) : -128);
        ++t06_ai_scenario_contract_failures;
    }
    result.chosen_move = result.chosen_slot < 4
        ? scenario->moves[result.chosen_slot] : 0;
    if (result.chosen_slot >= 4 || result.chosen_move == 0
        || scenario->pp[result.chosen_slot] == 0)
        t06_ai_die("AI scenario selected an unavailable move");
    return result;
}

static struct T06AiActionObservation t06_ai_run_switch(
    struct mCore *core, const struct Snapshot *full_profile,
    const struct T06AiSymbols *symbols)
{
    struct T06AiActionObservation result = {0};
    static const uint16_t active_moves[4] = {
        T06_AI_MOVE_TACKLE, T06_AI_MOVE_GROWL, 0, 0,
    };
    static const uint8_t active_pp[4] = {35, 40, 0, 0};
    restore_snapshot(core, full_profile);
    write8(core, ADDR_ACTIVE_BATTLER, 1);
    t06_ai_set_active_moves(core, 1, active_moves, active_pp);
    t06_ai_set_types(core, 0, T06_AI_TYPE_GHOST, T06_AI_TYPE_GHOST);
    t06_ai_set_hp_percent(core, 1, 15);
    t06_ai_write32(core, T06_AI_STATUSES3 + 4,
                   read32(core, T06_AI_STATUSES3 + 4)
                       | T06_AI_STATUS3_PERISH_SONG);
    write8(core, T06_AI_DISABLE_STRUCTS + T06_AI_DISABLE_STRUCT_SIZE
                     + T06_AI_PERISH_TIMER_OFFSET,
           (uint8_t)(read8(core, T06_AI_DISABLE_STRUCTS
                                  + T06_AI_DISABLE_STRUCT_SIZE
                                  + T06_AI_PERISH_TIMER_OFFSET)
                     & 0xF0U));
    uint32_t battle_struct = read32(core, ADDR_BATTLE_STRUCT_POINTER);
    /* Both selectors may retain the previous fixture's bank-1 zero.  PARTY_SIZE
     * is the upstream sentinel that asks the AI to calculate a live switch. */
    write8(core, battle_struct + T06_AI_BATTLE_STRUCT_MON_TO_SWITCH + 1,
           T06_AI_PARTY_SIZE);
    write8(core, battle_struct + T06_AI_BATTLE_STRUCT_SWITCHOUT_INDEX + 1,
           T06_AI_PARTY_SIZE);
    t06_ai_seed(core, UINT32_C(0x5157));
    t06_ai_clear_cold_cache(core, symbols);
    (void)call_rom(core, symbols->setup, 0xF);
    struct Measurement value = call_rom(core, symbols->try_action, 0);
    result.action = value.action;
    result.parameter = value.parameter;
    result.target = value.target;
    result.cycles = value.cycles;
    result.instructions = value.instructions;
    uint8_t chosen = read8(
        core, battle_struct + T06_AI_BATTLE_STRUCT_MON_TO_SWITCH + 1);
    result.parameter = chosen;
    if (result.action != T06_AI_ACTION_SWITCH
        || chosen == 0 || chosen >= T06_AI_PARTY_SIZE
        || read16(core, ADDR_ENEMY_PARTY + chosen * POKEMON_SIZE
                        + POKEMON_CURRENT_HP_OFFSET) == 0) {
        t06_ai_die("Perish Song optimal-switch fixture did not emit ACTION_SWITCH");
    }
    return result;
}

static struct T06AiActionObservation t06_ai_run_item(
    struct mCore *core, const struct Snapshot *full_profile,
    const struct T06AiSymbols *symbols)
{
    struct T06AiActionObservation result = {0};
    restore_snapshot(core, full_profile);
    write8(core, ADDR_ACTIVE_BATTLER, 1);
    for (unsigned member = 1; member < T06_AI_PARTY_SIZE; ++member)
        write16(core, ADDR_ENEMY_PARTY + member * POKEMON_SIZE
                      + POKEMON_CURRENT_HP_OFFSET, 0);
    t06_ai_set_hp_percent(core, 1, 1);
    uint32_t resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
    uint32_t history = read32(core,
        resources + T06_AI_RESOURCES_HISTORY_POINTER);
    if (!history) t06_ai_die("BattleHistory is unavailable");
    for (unsigned slot = 0; slot < 4; ++slot)
        write16(core, history + T06_AI_HISTORY_ITEMS + slot * 2, 0);
    write16(core, history + T06_AI_HISTORY_ITEMS, T06_AI_ITEM_FULL_RESTORE);
    write8(core, history + T06_AI_HISTORY_ITEM_COUNT, 1);
    t06_ai_seed(core, UINT32_C(0x17E0));
    t06_ai_clear_cold_cache(core, symbols);
    (void)call_rom(core, symbols->setup, 0xF);
    struct Measurement value = call_rom(core, symbols->try_action, 0);
    result.action = value.action;
    result.parameter = value.parameter;
    result.target = value.target;
    result.cycles = value.cycles;
    result.instructions = value.instructions;
    uint32_t battle_struct = read32(core, ADDR_BATTLE_STRUCT_POINTER);
    result.parameter = read16(
        core, battle_struct + T06_AI_BATTLE_STRUCT_CHOSEN_ITEM);
    if (result.action != T06_AI_ACTION_USE_ITEM
        || result.parameter != T06_AI_ITEM_FULL_RESTORE
        || read16(core, history + T06_AI_HISTORY_ITEMS) != 0) {
        t06_ai_die("trainer-item fixture did not consume its battle-local item slot");
    }
    return result;
}

static struct T06AiPerformanceObservation t06_ai_run_performance(
    struct mCore *core, const struct Snapshot *full_profile,
    const struct T06AiSymbols *symbols, bool is_double)
{
    struct T06AiPerformanceObservation result = {.is_double = is_double};
    restore_snapshot(core, full_profile);
    if (is_double) make_double(core);
    make_max_party(core);
    sync_active_moves(core);
    write8(core, ADDR_ACTIVE_BATTLER, 1);
    verify_fixture(core, is_double);
    t06_ai_seed(core, is_double ? UINT32_C(0xD0B1E) : UINT32_C(0x51A61E));
    t06_ai_clear_cold_cache(core, symbols);
    struct Snapshot base = take_snapshot(core);
    result.state_digest = fnv1a64_ram(core);
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    uint32_t base_rand_seed = read32(core, newbs + NEWBS_AI_RAND_SEED_OFFSET);

    struct Measurement cold_action = call_rom(core, symbols->try_action, 0);
    if (!(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE)
          & NEWBS_CALCULATED_PREDICTIONS_BIT)) {
        t06_ai_die("cold worst-case call did not populate prediction cache");
    }
    uint8_t *cache = t06_ai_capture_prediction_cache(core);
    restore_snapshot(core, &base);
    t06_ai_overlay_prediction_cache(core, cache);
    if (read32(core, newbs + NEWBS_AI_RAND_SEED_OFFSET) != base_rand_seed)
        t06_ai_die("warm cache overlay changed non-cache AI RNG state");
    struct Measurement warm_action = call_rom(core, symbols->try_action, 0);

    if (cold_action.action != warm_action.action
        || cold_action.parameter != warm_action.parameter
        || cold_action.target != warm_action.target) {
        t06_ai_die("cold/warm worst-case action differs");
    }
    restore_snapshot(core, &base);
    struct Measurement cold_setup = call_rom(core, symbols->setup, 0xF);
    uint32_t cold_flags = effective_ai_flags(core);
    struct Measurement cold_move = call_rom(core, symbols->choose_move, 0);
    uint8_t cold_target = read8(core, ADDR_BANK_TARGET);
    restore_snapshot(core, &base);
    t06_ai_overlay_prediction_cache(core, cache);
    struct Measurement warm_setup = call_rom(core, symbols->setup, 0xF);
    uint32_t warm_flags = effective_ai_flags(core);
    struct Measurement warm_move = call_rom(core, symbols->choose_move, 0);
    uint8_t warm_target = read8(core, ADDR_BANK_TARGET);
    if (cold_flags != T06_AI_PROFILE_FULL_SMART
        || warm_flags != T06_AI_PROFILE_FULL_SMART
        || cold_move.return_value != warm_move.return_value
        || cold_target != warm_target) {
        t06_ai_die("cold/warm worst-case move decision differs");
    }
    result.cold_cycles = cold_action.cycles
        + cold_setup.cycles + cold_move.cycles;
    result.warm_cycles = warm_action.cycles
        + warm_setup.cycles + warm_move.cycles;
    result.cold_instructions = cold_action.instructions
        + cold_setup.instructions + cold_move.instructions;
    result.warm_instructions = warm_action.instructions
        + warm_setup.instructions + warm_move.instructions;
    result.action = cold_action.action;
    result.parameter = cold_action.parameter;
    result.target = cold_action.target;
    if (result.action != T06_AI_ACTION_USE_MOVE)
        t06_ai_die("worst-case fixture selected switch/item instead of a move");
    if ((!is_double && (result.cold_cycles > T06_AI_SINGLE_COLD_LIMIT
                        || result.warm_cycles > T06_AI_SINGLE_WARM_LIMIT))
        || (is_double && (result.cold_cycles > T06_AI_DOUBLE_COLD_LIMIT
                         || result.warm_cycles > T06_AI_DOUBLE_WARM_LIMIT))) {
        t06_ai_die("T01 worst-case AI cycle threshold exceeded");
    }
    free(cache);
    free(base.bytes);
    return result;
}

static uint32_t t06_ai_read_cache_snapshot_field(struct mCore *core,
                                                  unsigned offset,
                                                  unsigned width)
{
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    uint32_t value = 0;
    if (!newbs || (width != 1 && width != 2 && width != 4) || offset + width >
            T06_AI_POLICY_CACHE_SNAPSHOT_SIZE) {
        t06_ai_die("cache snapshot field descriptor is invalid");
    }
    for (unsigned byte = 0; byte < width; ++byte) {
        value |= (uint32_t)read8(
            core, newbs + T06_AI_POLICY_CACHE_SNAPSHOT + offset + byte)
            << (8 * byte);
    }
    return value;
}

static void t06_ai_verify_lazy_cache_invalidation(
    struct mCore *core, const struct Snapshot *full_profile,
    const struct T06AiSymbols *symbols)
{
    struct T06AiCacheMutation {
        const char *name;
        uint16_t snapshot_offset;
        uint8_t width;
        uint32_t expected;
    };
    static const struct T06AiCacheMutation mutations[] = {
        /* ARM layout: battlers=0x40/stride=0x38; party rows=0x24. */
        {"switch", 0x98, 2, 1},      /* battler[1].party_index */
        {"faint", 0x224, 2, 0},      /* enemy_party[1].hp */
        {"form", 0x4C, 2, 8},        /* battler[0].species */
        {"item", 0x96, 2, 1},        /* battler[1].item */
        {"weather", 0x1C, 2, 1},
        {"terrain", 0x03, 1, 1},
        {"status", 0x78, 4, 8},      /* battler[1].status1=poison */
        {"stat_stages", 0xAA, 1, 7}, /* battler[1].Attack stage */
        {"pp", 0xA2, 1, 34},         /* battler[1].move[0] PP */
        {"side_condition", 0x20, 2, T06_AI_SIDE_STATUS_SPIKES},
    };
    for (unsigned event = 0; event < ARRAY_LEN(mutations); ++event) {
        restore_snapshot(core, full_profile);
        write8(core, ADDR_ACTIVE_BATTLER, 1);
        uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
        t06_ai_seed(core, UINT32_C(0xCA00) + event);

        /* No ClearCachedAIData call is allowed in this fixture.  The first
         * action populates the ROM-owned lazy snapshot from the battle state. */
        (void)call_rom(core, symbols->try_action, 0);
        if (!(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE)
              & NEWBS_CALCULATED_PREDICTIONS_BIT)
            || read8(core, newbs + T06_AI_POLICY_CACHE_SNAPSHOT) != 1) {
            t06_ai_die("lazy cache fixture failed to establish a valid snapshot");
        }
        uint32_t old_value = t06_ai_read_cache_snapshot_field(
            core, mutations[event].snapshot_offset, mutations[event].width);

        switch (event) {
        case 0:
            write16(core, ADDR_BATTLER_PARTY_INDEXES + 2, 1);
            break;
        case 1:
            write16(core, ADDR_ENEMY_PARTY + POKEMON_SIZE
                          + POKEMON_CURRENT_HP_OFFSET, 0);
            break;
        case 2:
            write16(core, ADDR_BATTLE_MONS, 8);
            break;
        case 3:
            write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                          + T06_AI_BATTLE_MON_ITEM, 1);
            break;
        case 4:
            write16(core, T06_AI_BATTLE_WEATHER, 1);
            break;
        case 5:
            write8(core, T06_AI_TERRAIN_TYPE, 1);
            break;
        case 6:
            t06_ai_write32(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                                 + BATTLE_CORE_MON_STATUS1, 8);
            break;
        case 7:
            write8(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                         + BATTLE_CORE_MON_STAT_STAGES + 1, 7);
            break;
        case 8:
            write8(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                         + BATTLE_MON_PP_OFFSET, 34);
            break;
        case 9:
            write16(core, T06_AI_SIDE_STATUSES + 2,
                    T06_AI_SIDE_STATUS_SPIKES);
            write8(core, T06_AI_SIDE_TIMERS + T06_AI_SIDE_TIMER_SIZE
                         + T06_AI_SIDE_TIMER_HAZARDS, 1);
            break;
        default:
            t06_ai_die("cache event index escaped table");
        }

        if (old_value == mutations[event].expected
            || !(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE)
                 & NEWBS_CALCULATED_PREDICTIONS_BIT)) {
            t06_ai_die("cache mutation did not create a live stale snapshot");
        }
        struct Measurement recalculated = call_rom(
            core, symbols->try_action, 0);
        if (!(read8(core, newbs + NEWBS_CALCULATED_PREDICTIONS_BYTE)
              & NEWBS_CALCULATED_PREDICTIONS_BIT)
            || recalculated.cycles == 0 || recalculated.instructions == 0
            || t06_ai_read_cache_snapshot_field(
                   core, mutations[event].snapshot_offset,
                   mutations[event].width) != mutations[event].expected) {
            (void)mutations[event].name;
            t06_ai_die("ROM lazy snapshot did not recalculate after mutation");
        }
        if (event == 9
            && t06_ai_read_cache_snapshot_field(core, 0x3E, 1) != 1) {
            t06_ai_die("ROM lazy snapshot did not capture side timer mutation");
        }
    }
}

static struct T06AiMechanicObservation t06_ai_run_mechanic_mode(
    struct mCore *core, const struct Snapshot *field,
    const struct T06AiSymbols *symbols, uint8_t mode)
{
    struct T06AiMechanicObservation result = {.mode = mode};
    static const uint16_t only_ember[4] = {
        T06_AI_MOVE_EMBER, 0, 0, 0,
    };
    static const uint8_t only_ember_pp[4] = {25, 0, 0, 0};
    uint16_t held_item = 0;
    if (mode == T06_AI_MODE_STANDARD || mode == T06_AI_MODE_MEGA)
        held_item = T06_AI_ITEM_CHARIZARDITE_X;
    else if (mode == T06_AI_MODE_Z_MOVE)
        held_item = T06_AI_ITEM_FIRIUM_Z;

    t06_ai_setup_profile_battle(core, field, symbols,
                                T06_AI_PROFILE_FULL_SMART, mode);
    uint8_t mechanic_mon[POKEMON_SIZE];
    create_mon_image(core, T06_AI_MEGA_FIXTURE_SPECIES, 50,
                     only_ember, only_ember_pp, mechanic_mon);
    install_mon_image(core, ADDR_ENEMY_PARTY, mechanic_mon);
    set_mon_data_u32(core, ADDR_ENEMY_PARTY,
                     T06_AI_MON_DATA_HELD_ITEM, held_item);
    for (unsigned member = 1; member < T06_AI_PARTY_SIZE; ++member) {
        write16(core, ADDR_ENEMY_PARTY + member * POKEMON_SIZE
                      + POKEMON_CURRENT_HP_OFFSET, 0);
    }
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE,
            T06_AI_MEGA_FIXTURE_SPECIES);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + T06_AI_BATTLE_MON_ITEM, held_item);
    t06_ai_set_active_moves(core, 1, only_ember, only_ember_pp);
    t06_ai_set_types(core, 1, T06_AI_TYPE_FIRE, T06_AI_TYPE_FLYING);
    t06_ai_set_types(core, 0, T06_AI_TYPE_NORMAL, T06_AI_TYPE_NORMAL);
    t06_ai_set_hp_percent(core, 0, 100);
    t06_ai_set_hp_percent(core, 1, 100);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + T06_AI_BATTLE_MON_SP_ATTACK, 100);
    write16(core, ADDR_BATTLE_MONS + T06_AI_BATTLE_MON_SP_DEFENSE, 250);
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    if (mode == T06_AI_MODE_STANDARD || mode == T06_AI_MODE_MEGA
        || mode == T06_AI_MODE_Z_MOVE) {
        flags |= T06_AI_BATTLE_TYPE_BATTLE_TOWER;
    }
    if (mode == T06_AI_MODE_DYNAMAX)
        flags |= T06_AI_BATTLE_TYPE_DYNAMAX;
    t06_ai_write32(core, ADDR_BATTLE_TYPE_FLAGS, flags);
    uint32_t resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
    uint32_t history = read32(core,
        resources + T06_AI_RESOURCES_HISTORY_POINTER);
    if (!history) t06_ai_die("BattleHistory is unavailable in mechanic fixture");
    for (unsigned slot = 0; slot < 4; ++slot)
        write16(core, history + T06_AI_HISTORY_ITEMS + slot * 2, 0);
    write8(core, history + T06_AI_HISTORY_ITEM_COUNT, 0);

    t06_ai_seed(core, UINT32_C(0x600D) + mode);
    t06_ai_clear_cold_cache(core, symbols);
    (void)call_rom(core, symbols->setup, 0xF);
    result.effective_flags = effective_ai_flags(core);
    struct Measurement action = call_rom(core, symbols->try_action, 0);
    result.action = action.action;
    result.parameter = action.parameter;
    result.target = action.target;
    (void)call_rom(core, symbols->setup, 0xF);
    struct Measurement choice = call_rom(core, symbols->choose_move, 0);
    result.chosen_slot = (uint8_t)choice.return_value;
    result.chosen_move = only_ember[result.chosen_slot < 4
                                    ? result.chosen_slot : 0];
    uint32_t newbs = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    result.dynamax_candidate = read8(
        core, newbs + T06_AI_NEWBS_DYNAMAX_MON_ID + 1);
    result.dynamax_potential = read8(
        core, newbs + T06_AI_NEWBS_DYNAMAX_POTENTIAL + 4);
    result.terastal_candidate = read8(
        core, newbs + T06_AI_NEWBS_TERASTAL_MON_ID + 1);
    result.terastal_potential = read8(
        core, newbs + T06_AI_NEWBS_TERASTAL_POTENTIAL + 4);
    result.mega_candidate = read32(
        core, newbs + T06_AI_NEWBS_MEGA_POTENTIAL + 4);
    result.transformed_move_source = read16(
        core, newbs + T06_AI_NEWBS_TRANSFORMED_MOVE_SOURCE);
    bool mega_present = result.mega_candidate != 0;
    bool expected_mega = mode == T06_AI_MODE_MEGA;
    uint8_t expected_dynamax_candidate = mode == T06_AI_MODE_DYNAMAX
        ? 0 : 0xFF;
    uint8_t expected_terastal_candidate =
        (mode == T06_AI_MODE_DYNAMAX || mode == T06_AI_MODE_TERASTAL)
        ? 0 : 0xFF;
    uint16_t expected_transformed_source =
        (mode == T06_AI_MODE_Z_MOVE || mode == T06_AI_MODE_DYNAMAX)
        ? T06_AI_MOVE_EMBER : 0;
    if (result.effective_flags != T06_AI_PROFILE_FULL_SMART
        || result.action != T06_AI_ACTION_USE_MOVE
        || result.parameter != 0 || result.target != 0
        || result.chosen_slot != 0 || result.chosen_move != T06_AI_MOVE_EMBER
        || result.dynamax_candidate != expected_dynamax_candidate
        || result.dynamax_potential != (mode == T06_AI_MODE_DYNAMAX)
        || result.terastal_candidate != expected_terastal_candidate
        || result.terastal_potential != (mode == T06_AI_MODE_TERASTAL)
        || mega_present != expected_mega
        || (mega_present
            && (result.mega_candidate < 0x08000000U
                || result.mega_candidate > 0x09FFFFFFU
                || read16(core, result.mega_candidate + 0U)
                    != T06_AI_MEGA_METHOD
                || read16(core, result.mega_candidate + 2U)
                    != T06_AI_MEGA_SOURCE_ITEM
                || read16(core, result.mega_candidate + 4U)
                    != T06_AI_MEGA_FIXTURE_SPECIES
                || read16(core, result.mega_candidate + 6U)
                    != T06_AI_MEGA_VARIANT))
        || result.transformed_move_source != expected_transformed_source) {
        t06_ai_die("mechanic mode candidate/action differs from exact contract");
    }
    return result;
}

static void t06_ai_count_secondary_chances(struct mCore *core,
                                           uint32_t counts[3])
{
    uint32_t table = read32(core, T06_AI_CANONICAL_MOVE_REPOINT) & ~1U;
    if (table < 0x08000000U
        || table + T06_AI_CANONICAL_MOVE_COUNT * T06_AI_CANONICAL_MOVE_STRIDE
               > BATTLE_CORE_ROM_END) {
        t06_ai_die("canonical move table pointer is outside the ROM");
    }
    const uint8_t values[3] = {10, 20, 30};
    for (unsigned move = 0; move < T06_AI_CANONICAL_MOVE_COUNT; ++move) {
        uint8_t chance = read8(core,
            table + move * T06_AI_CANONICAL_MOVE_STRIDE
                  + T06_AI_SECONDARY_CHANCE_OFFSET);
        for (unsigned boundary = 0; boundary < 3; ++boundary)
            if (chance == values[boundary]) ++counts[boundary];
    }
    if (!counts[0] || !counts[1] || !counts[2])
        t06_ai_die("canonical 10/20/30 secondary-effect chance inventory is incomplete");
}

static void t06_ai_print_profile(const struct T06AiProfileObservation *value)
{
    printf("{\"requested_bits\":%u,\"resolved_bits\":%" PRIu32
           ",\"effective_bits\":%" PRIu32 ",\"chosen_slot\":%u,"
           "\"chosen_move\":%u,\"target\":%u}",
           value->requested, value->resolved, value->effective,
           value->chosen_slot, value->chosen_move, value->target);
}

static void t06_ai_print_action(const struct T06AiActionObservation *value)
{
    printf("{\"action\":%u,\"parameter\":%u,\"target\":%u,"
           "\"cycles\":%" PRIu64 ",\"instructions\":%" PRIu64 "}",
           value->action, value->parameter, value->target,
           value->cycles, value->instructions);
}

static void t06_ai_print_performance(
    const struct T06AiPerformanceObservation *value)
{
    uint64_t cold_limit = value->is_double
        ? T06_AI_DOUBLE_COLD_LIMIT : T06_AI_SINGLE_COLD_LIMIT;
    uint64_t warm_limit = value->is_double
        ? T06_AI_DOUBLE_WARM_LIMIT : T06_AI_SINGLE_WARM_LIMIT;
    printf("{\"active_battlers\":%u,\"party_size_per_side\":6,"
           "\"state_fnv1a64\":\"%016" PRIx64 "\",\"action\":%u,"
           "\"parameter\":%u,\"target\":%u,\"cold\":{\"cycles\":%" PRIu64
           ",\"instructions\":%" PRIu64 ",\"limit\":%" PRIu64 "},"
           "\"warm\":{\"cycles\":%" PRIu64 ",\"instructions\":%" PRIu64
           ",\"limit\":%" PRIu64 "},\"threshold_status\":\"PASS\"}",
           value->is_double ? 4 : 2, value->state_digest,
           value->action, value->parameter, value->target,
           value->cold_cycles, value->cold_instructions, cold_limit,
           value->warm_cycles, value->warm_instructions, warm_limit);
}

int main(int argc, char **argv)
{
    if (argc != 9) {
        fprintf(stderr,
            "usage: %s ROM EXPECTED_ROM_SHA256 AI_TrySwitchOrUseItem "
            "BattleAI_SetupAIData BattleAI_ChooseMoveOrAction "
            "ClearCachedAIData VegaConfigureNextBattlePolicy "
            "VegaBattlePolicyResolveAIProfileBits\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0)
        t06_ai_die("ROM SHA-256 mismatch");
    struct T06AiSymbols symbols = {
        .try_action = parse_address(argv[3]),
        .setup = parse_address(argv[4]),
        .choose_move = parse_address(argv[5]),
        .clear_cache = parse_address(argv[6]),
        .configure_policy = parse_address(argv[7]),
        .resolve_profile = parse_address(argv[8]),
    };

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        t06_ai_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) t06_ai_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    if (log_problem_count) t06_ai_die("mGBA warned/errored during field boot");
    struct Snapshot field = take_snapshot(core);

    const uint8_t profile_bits[3] = {
        T06_AI_PROFILE_BASIC,
        T06_AI_PROFILE_SEMI_SMART,
        T06_AI_PROFILE_FULL_SMART,
    };
    struct T06AiProfileObservation profiles[3];
    for (unsigned i = 0; i < ARRAY_LEN(profiles); ++i)
        profiles[i] = t06_ai_run_profile(core, &field, &symbols, profile_bits[i]);

    t06_ai_setup_profile_battle(core, &field, &symbols,
                                T06_AI_PROFILE_FULL_SMART,
                                T06_AI_MODE_STANDARD);
    struct Snapshot full_profile = take_snapshot(core);
    struct T06AiScenarioObservation scenarios[ARRAY_LEN(T06_AI_SCENARIOS)];
    for (unsigned i = 0; i < ARRAY_LEN(T06_AI_SCENARIOS); ++i)
        scenarios[i] = t06_ai_run_scenario(
            core, &full_profile, &symbols, &T06_AI_SCENARIOS[i], i);
    if (t06_ai_scenario_contract_failures)
        t06_ai_die("table-driven AI scenarios differed from exact contracts");

    struct T06AiActionObservation switch_route = t06_ai_run_switch(
        core, &full_profile, &symbols);
    struct T06AiActionObservation item_route = t06_ai_run_item(
        core, &full_profile, &symbols);
    t06_ai_verify_lazy_cache_invalidation(core, &full_profile, &symbols);
    struct T06AiPerformanceObservation performance[2] = {
        t06_ai_run_performance(core, &full_profile, &symbols, false),
        t06_ai_run_performance(core, &full_profile, &symbols, true),
    };
    struct T06AiMechanicObservation mechanics[5];
    for (unsigned mode = 0; mode < ARRAY_LEN(mechanics); ++mode)
        mechanics[mode] = t06_ai_run_mechanic_mode(
            core, &field, &symbols, (uint8_t)mode);
    uint32_t chance_counts[3] = {0};
    t06_ai_count_secondary_chances(core, chance_counts);
    if (log_problem_count) t06_ai_die("mGBA warned/errored during AI fixtures");

    printf("{\"schema_version\":%u,\"status\":\"PASS\","
           "\"fixture\":\"t06_cfru_vega_ai_v1\",\"rom_sha256\":\"%s\","
           "\"fixed_rtc_unix\":946684800,\"read_only\":true,"
           "\"warnings_errors\":0,\"provenance\":{\"symbols\":{"
           "\"AI_TrySwitchOrUseItem\":\"0x%08" PRIX32 "\","
           "\"BattleAI_SetupAIData\":\"0x%08" PRIX32 "\","
           "\"BattleAI_ChooseMoveOrAction\":\"0x%08" PRIX32 "\","
           "\"ClearCachedAIData\":\"0x%08" PRIX32 "\","
           "\"VegaConfigureNextBattlePolicy\":\"0x%08" PRIX32 "\","
           "\"VegaBattlePolicyResolveAIProfileBits\":\"0x%08" PRIX32
           "\"}},\"profiles\":{",
           T06_AI_SCHEMA_VERSION, rom_sha256,
           symbols.try_action, symbols.setup, symbols.choose_move,
           symbols.clear_cache, symbols.configure_policy,
           symbols.resolve_profile);
    const char *const profile_names[3] = {
        "AI_BASIC", "AI_SEMI_SMART", "AI_FULL_SMART",
    };
    for (unsigned i = 0; i < ARRAY_LEN(profiles); ++i) {
        if (i) putchar(',');
        printf("\"%s\":", profile_names[i]);
        t06_ai_print_profile(&profiles[i]);
    }
    printf("},\"decision_scenarios\":[");
    for (unsigned i = 0; i < ARRAY_LEN(T06_AI_SCENARIOS); ++i) {
        if (i) putchar(',');
        printf("{\"name\":\"%s\",\"category\":\"%s\","
               "\"classification\":\"%s\",\"battle\":\"%s\","
               "\"chosen_slot\":%u,\"chosen_move\":%u,\"target\":%u,"
               "\"legal_competing_moves\":%u,"
               "\"effective_ai_flags\":%" PRIu32 ",\"cycles\":%" PRIu64
               ",\"instructions\":%" PRIu64 ",\"status\":\"PASS\"}",
               T06_AI_SCENARIOS[i].name, T06_AI_SCENARIOS[i].category,
               "DIFFERENTIAL_DECISION",
               T06_AI_SCENARIOS[i].is_double ? "DOUBLE" : "SINGLE",
               scenarios[i].chosen_slot, scenarios[i].chosen_move,
               scenarios[i].target, scenarios[i].legal_competing_moves,
               scenarios[i].effective_flags,
               scenarios[i].cycles, scenarios[i].instructions);
    }
    printf("],\"action_scenarios\":{\"switch\":");
    t06_ai_print_action(&switch_route);
    printf(",\"trainer_item\":");
    t06_ai_print_action(&item_route);
    printf("},\"mechanic_policy_observations\":[");
    const char *const mode_names[5] = {
        "STANDARD", "MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL",
    };
    for (unsigned i = 0; i < ARRAY_LEN(mechanics); ++i) {
        if (i) putchar(',');
        printf("{\"mode\":\"%s\",\"effective_ai_flags\":%" PRIu32
               ",\"dynamax_candidate\":%u,\"dynamax_potential\":%u,"
               "\"terastal_candidate\":%u,\"terastal_potential\":%u,"
               "\"mega_candidate\":\"0x%08" PRIX32
               "\",\"transformed_move_source\":%u,\"action\":%u,"
               "\"parameter\":%u,\"target\":%u,\"chosen_slot\":%u,"
               "\"chosen_move\":%u,"
               "\"classification\":\"MODE_SPECIFIC_EXACT_CANDIDATE_ACTION\","
               "\"status\":\"PASS\"}",
               mode_names[i], mechanics[i].effective_flags,
               mechanics[i].dynamax_candidate,
               mechanics[i].dynamax_potential,
               mechanics[i].terastal_candidate,
               mechanics[i].terastal_potential,
               mechanics[i].mega_candidate,
               mechanics[i].transformed_move_source,
               mechanics[i].action, mechanics[i].parameter,
               mechanics[i].target, mechanics[i].chosen_slot,
               mechanics[i].chosen_move);
    }
    printf("],\"cache_history\":{\"entry\":\"CalculateAIPredictions\","
           "\"mutations\":[\"switch\",\"faint\",\"form\",\"item\","
           "\"weather\",\"terrain\",\"status\",\"stat_stages\",\"pp\","
           "\"side_condition\"],\"snapshot_size_bytes\":720,"
           "\"runner_clear_after_mutation\":false,"
           "\"stale_snapshot_detected_before_each\":true,"
           "\"lazy_recalculated_after_each\":true,"
           "\"scope\":\"rom_lazy_snapshot_recalculation_without_runner_clear\","
           "\"status\":\"PASS\"},\"performance\":{"
           "\"single_max_party\":");
    t06_ai_print_performance(&performance[0]);
    printf(",\"double_four_battler\":");
    t06_ai_print_performance(&performance[1]);
    printf("},\"secondary_effect_chance_inventory\":{"
           "\"10\":%" PRIu32 ",\"20\":%" PRIu32 ",\"30\":%" PRIu32
           ",\"comparison_semantics\":\"NOT_INFERRED_FROM_TABLE_INVENTORY\"},"
           "\"repeatability\":{\"independent_process_runs_required\":2,"
           "\"byte_identical_stdout_required\":true},"
           "\"unreached_scenarios\":[],\"artifacts_written\":[]}\n",
           chance_counts[0], chance_counts[1], chance_counts[2]);

    free(full_profile.bytes);
    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
