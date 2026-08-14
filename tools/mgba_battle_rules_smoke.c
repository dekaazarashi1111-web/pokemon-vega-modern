/*
 * USER-20260814-BATTLE-RULES exact-ROM fixture for libmGBA 0.10.2.
 *
 * The runner boots the reviewed natural Vega field state, enters the real
 * CFRU battle setup, and then exercises the active command table and hook
 * targets with fixed RNG seeds.  Direct calls are bounded ARM7TDMI calls;
 * the double-battle route uses the ordinary battle controllers.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    RULES_MAIN_COMMAND_TABLE = 0x0903F450,
    RULES_SECONDARY_COMMAND_TABLE = 0x0903F850,
    RULES_BATTLE_STRUCT_POINTER = 0x02023F48,
    RULES_BANKS_BY_TURN_ORDER = 0x02023B3E,
    RULES_CURRENT_MOVE = 0x02023CAA,
    RULES_BATTLE_MOVE_DAMAGE = 0x02023CB0,
    RULES_BANK_ATTACKER = 0x02023CCB,
    RULES_BANK_TARGET = 0x02023CCC,
    RULES_CRIT_MULTIPLIER = 0x02023CD1,
    RULES_BATTLE_SCRIPT = 0x02023CD4,
    RULES_MOVE_RESULT_FLAGS = 0x02023D2C,
    RULES_HIT_MARKER = 0x02023D30,
    RULES_BATTLE_WEATHER = 0x02023E7C,
    RULES_WEATHER_DURATION = 0x02023EA8,

    RULES_MON_SPEED = 0x06,
    RULES_MON_SP_ATTACK = 0x08,
    RULES_MON_SP_DEFENSE = 0x0A,
    RULES_MON_TYPE3 = 0x18,
    RULES_MON_STAT_STAGES = 0x19,
    RULES_MON_TYPE1 = 0x21,
    RULES_MON_TYPE2 = 0x22,
    RULES_MON_HP = 0x28,
    RULES_MON_MAX_HP = 0x2C,
    RULES_MON_ITEM = 0x2E,
    RULES_MON_ABILITY = 0x38,
    RULES_MON_STATUS1 = 0x4C,
    RULES_MON_STATUS2 = 0x50,

    RULES_BATTLE_STRUCT_ATTACK_CANCELLER = 0xB7,
    RULES_CANCELLER_ASLEEP = 2,
    RULES_CANCELLER_FROZEN = 3,
    RULES_CANCELLER_PARALYSED = 17,
    RULES_END_TURN_WEATHER = 2,
    RULES_END_TURN_POISON = 12,
    RULES_END_TURN_BURN = 15,

    RULES_MOVE_TACKLE = 33,
    RULES_MOVE_EMBER = 52,
    RULES_TYPE_NORMAL = 0,
    RULES_STATUS_SLEEP_3 = 3,
    RULES_STATUS_POISON = 0x08,
    RULES_STATUS_BURN = 0x10,
    RULES_STATUS_FREEZE = 0x20,
    RULES_STATUS_PARALYSIS = 0x40,
    RULES_STATUS_TOXIC = 0x80,
    RULES_STATUS_TOXIC_COUNTER_1 = 0x100,
    RULES_HITMARKER_UNABLE_TO_USE_MOVE = 0x00080000,
    RULES_WEATHER_RAIN = 1 << 0,
    RULES_WEATHER_SAND = 1 << 3,
    RULES_WEATHER_SUN = 1 << 5,
    RULES_WEATHER_HAIL = 1 << 7,
    RULES_ITEM_NONE = 0,

    RULES_SEED_HIT = 0,
    RULES_SEED_MISS = 1,
    RULES_RNG_AFTER_HIT = 0x00006073,
    RULES_RNG_AFTER_MISS = 0x41C6AEE0,
};

static const uint32_t RULES_COMMAND_ROOTS[] = {
    0x0801443C, 0x08015240, 0x08015480, 0x080154AC, 0x0801C864,
};

struct RulesCommand {
    const char *name;
    uint8_t index;
};

static const struct RulesCommand RULES_COMMANDS[] = {
    {"attack_canceler", 0x00},
    {"critical", 0x04},
    {"damage", 0x05},
    {"rain", 0x7D},
    {"sand", 0x95},
    {"sun", 0xBB},
    {"hail", 0xC8},
    {"secondary_dispatch", 0xFF},
};

static const struct HookContract RULES_SPEED_HOOK = {
    "paralysis_speed", "DIRECT_CALL_BOUNDED", "GetWhoStrikesFirst",
    0x080144F8, 3, true,
};

static const struct HookContract RULES_END_TURN_HOOK = {
    "residual_and_weather", "DIRECT_CALL_BOUNDED", "TurnBasedEffects",
    0x08017A68, 0, true,
};

static const struct HookContract RULES_STATUS_HOOK = {
    "status_application", "OWNER_ONLY", "SetMoveEffect",
    0x0801F730, 2, false,
};

struct RulesOwnerObservation {
    uint32_t commands[ARRAY_LEN(RULES_COMMANDS)];
    struct HookObservation speed;
    struct HookObservation end_turn;
    struct HookObservation status;
};

struct RulesSpeedObservation {
    uint8_t clear_vs_60;
    uint8_t paralysis_vs_60;
    uint8_t paralysis_vs_30;
};

struct RulesCancelObservation {
    uint32_t seed;
    uint32_t rng_after;
    uint32_t status_before;
    uint32_t status_after;
    bool unable;
    bool payload_seen;
};

struct RulesCritObservation {
    uint32_t seed;
    uint32_t rng_after;
    uint8_t multiplier;
    bool payload_seen;
};

struct RulesResidualObservation {
    uint32_t status_before;
    uint32_t status_after;
    uint32_t queued_damage;
    uint16_t hp_before;
    uint16_t hp_after;
    uint8_t tracker_after;
    uint8_t bank_after;
    bool payload_seen;
};

struct RulesWeatherObservation {
    const char *name;
    uint8_t command;
    uint32_t flag;
    uint8_t duration;
    bool payload_seen;
};

struct RulesWeatherDamageObservation {
    uint32_t clear;
    uint32_t rain;
    uint32_t sun;
};

static void rules_die(const char *message)
{
    fprintf(stderr, "mgba-battle-rules-smoke: %s\n", message);
    exit(1);
}

static uint32_t rules_command(struct mCore *core, uint8_t index)
{
    uint32_t target = read32(core, RULES_MAIN_COMMAND_TABLE + index * 4U);
    if (!(target & 1U) || !payload_address(target))
        rules_die("battle command table entry does not target CFRU payload");
    return target;
}

static struct RulesOwnerObservation observe_rules_owner(struct mCore *core)
{
    struct RulesOwnerObservation result = {0};
    for (unsigned root = 0; root < ARRAY_LEN(RULES_COMMAND_ROOTS); ++root) {
        if (read32(core, RULES_COMMAND_ROOTS[root]) != RULES_MAIN_COMMAND_TABLE)
            rules_die("stock battle-script root is not bound to CFRU main table");
    }
    for (unsigned command = 0; command < ARRAY_LEN(RULES_COMMANDS); ++command)
        result.commands[command] = rules_command(core, RULES_COMMANDS[command].index);
    if (result.commands[ARRAY_LEN(RULES_COMMANDS) - 1] != 0x0911A955U)
        rules_die("secondary command dispatch entry changed");
    if (read32(core, RULES_SECONDARY_COMMAND_TABLE) != 0)
        rules_die("secondary command table null boundary changed");
    result.speed = observe_hook(core, &RULES_SPEED_HOOK);
    result.end_turn = observe_hook(core, &RULES_END_TURN_HOOK);
    result.status = observe_hook(core, &RULES_STATUS_HOOK);
    return result;
}

static void prepare_rule_battlers(struct mCore *core)
{
    for (unsigned battler = 0; battler < 2; ++battler) {
        uint32_t mon = ADDR_BATTLE_MONS + battler * BATTLE_MON_SIZE;
        for (unsigned stat = 0; stat < 7; ++stat)
            write8(core, mon + RULES_MON_STAT_STAGES + stat, 6);
        write16(core, mon + RULES_MON_ITEM, RULES_ITEM_NONE);
        write16(core, mon + RULES_MON_ABILITY, 0);
        write32_bytes(core, mon + RULES_MON_STATUS1, 0);
        write32_bytes(core, mon + RULES_MON_STATUS2, 0);
        write8(core, mon + RULES_MON_TYPE3, 0xFF);
    }
    write8(core, RULES_BANK_ATTACKER, 0);
    write8(core, RULES_BANK_TARGET, 1);
    write16(core, RULES_CURRENT_MOVE, RULES_MOVE_TACKLE);
    write8(core, 0x02023CA8, 0);
    write8(core, ADDR_BATTLERS_COUNT, 2);
    write8(core, BATTLE_CORE_BATTLE_OUTCOME, 0);
    write32_bytes(core, RULES_MOVE_RESULT_FLAGS, 0);
    write32_bytes(core, RULES_HIT_MARKER, 0);
    write8(core, RULES_BANKS_BY_TURN_ORDER, 0);
    write8(core, RULES_BANKS_BY_TURN_ORDER + 1, 1);
}

static struct RulesSpeedObservation observe_paralysis_speed(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t speed_function
)
{
    struct RulesSpeedObservation result = {0};
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    write16(core, ADDR_BATTLE_MONS + RULES_MON_SPEED, 100);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + RULES_MON_SPEED, 60);
    result.clear_vs_60 = (uint8_t)call_bounded(
        core, speed_function, 0, 1, 1, 0).result;
    write32_bytes(core, ADDR_BATTLE_MONS + RULES_MON_STATUS1,
                  RULES_STATUS_PARALYSIS);
    result.paralysis_vs_60 = (uint8_t)call_bounded(
        core, speed_function, 0, 1, 1, 0).result;
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + RULES_MON_SPEED, 30);
    result.paralysis_vs_30 = (uint8_t)call_bounded(
        core, speed_function, 0, 1, 1, 0).result;
    if (result.clear_vs_60 != 0 || result.paralysis_vs_60 != 1
        || result.paralysis_vs_30 != 0) {
        rules_die("paralysis speed boundary is not the CFRU 1/2 default");
    }
    return result;
}

static struct RulesCancelObservation observe_canceller(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t command,
    uint8_t tracker,
    uint32_t status,
    uint32_t seed
)
{
    struct RulesCancelObservation result = {0};
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    uint32_t battle_struct = read32(core, RULES_BATTLE_STRUCT_POINTER);
    if (battle_struct < 0x02000000U || battle_struct >= 0x02040000U)
        rules_die("gBattleStruct is not initialized");
    write8(core, battle_struct + RULES_BATTLE_STRUCT_ATTACK_CANCELLER, tracker);
    write32_bytes(core, ADDR_BATTLE_MONS + RULES_MON_STATUS1, status);
    write32_bytes(core, BATTLE_CORE_GLOBAL_RNG, seed);
    result.seed = seed;
    result.status_before = status;
    struct CallObservation call = call_bounded(core, command, 0, 0, 0, 0);
    result.payload_seen = call.payload_pc_seen;
    result.rng_after = read32(core, BATTLE_CORE_GLOBAL_RNG);
    result.status_after = read32(core, ADDR_BATTLE_MONS + RULES_MON_STATUS1);
    result.unable = (read32(core, RULES_HIT_MARKER)
                     & RULES_HITMARKER_UNABLE_TO_USE_MOVE) != 0;
    if (!result.payload_seen)
        rules_die("status canceller call never executed CFRU payload");
    return result;
}

static struct RulesCritObservation observe_crit(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t command,
    uint32_t seed
)
{
    struct RulesCritObservation result = {0};
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    write32_bytes(core, BATTLE_CORE_GLOBAL_RNG, seed);
    result.seed = seed;
    struct CallObservation call = call_bounded(core, command, 0, 0, 0, 0);
    result.payload_seen = call.payload_pc_seen;
    result.rng_after = read32(core, BATTLE_CORE_GLOBAL_RNG);
    result.multiplier = read8(core, RULES_CRIT_MULTIPLIER);
    if (!result.payload_seen)
        rules_die("critical command never executed CFRU payload");
    return result;
}

static struct RulesResidualObservation observe_residual(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t function,
    uint8_t tracker,
    uint32_t status
)
{
    struct RulesResidualObservation result = {0};
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    uint32_t battle_struct = read32(core, RULES_BATTLE_STRUCT_POINTER);
    write8(core, battle_struct, tracker);
    write8(core, battle_struct + 1, 0);
    write16(core, ADDR_BATTLE_MONS + RULES_MON_HP, 160);
    write16(core, ADDR_BATTLE_MONS + RULES_MON_MAX_HP, 160);
    write32_bytes(core, ADDR_BATTLE_MONS + RULES_MON_STATUS1, status);
    result.status_before = status;
    result.hp_before = read16(core, ADDR_BATTLE_MONS + RULES_MON_HP);
    struct CallObservation call = call_bounded(core, function, 0, 0, 0, 0);
    result.payload_seen = call.payload_pc_seen;
    result.status_after = read32(core, ADDR_BATTLE_MONS + RULES_MON_STATUS1);
    result.queued_damage = read32(core, RULES_BATTLE_MOVE_DAMAGE);
    result.hp_after = read16(core, ADDR_BATTLE_MONS + RULES_MON_HP);
    result.tracker_after = read8(core, battle_struct);
    result.bank_after = read8(core, battle_struct + 1);
    if (!result.payload_seen || call.result != 1 || result.hp_after != result.hp_before
        || result.tracker_after != tracker || result.bank_after != 1) {
        rules_die("end-turn residual did not queue exactly one battle-script update");
    }
    return result;
}

static struct RulesWeatherObservation observe_weather_start(
    struct mCore *core,
    const struct Snapshot *battle,
    const char *name,
    uint8_t command,
    uint32_t expected_flag
)
{
    struct RulesWeatherObservation result = {0};
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    write32_bytes(core, RULES_BATTLE_WEATHER, 0);
    write8(core, RULES_WEATHER_DURATION, 0);
    uint32_t target = rules_command(core, command);
    struct CallObservation call = call_bounded(core, target, 0, 0, 0, 0);
    result.name = name;
    result.command = command;
    result.flag = read32(core, RULES_BATTLE_WEATHER);
    result.duration = read8(core, RULES_WEATHER_DURATION);
    result.payload_seen = call.payload_pc_seen;
    if (!result.payload_seen || result.flag != expected_flag || result.duration != 5)
        rules_die("move-started weather does not use the CFRU five-turn default");
    return result;
}

static void observe_weather_end(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t function
)
{
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    uint32_t battle_struct = read32(core, RULES_BATTLE_STRUCT_POINTER);
    write8(core, battle_struct, RULES_END_TURN_WEATHER);
    write8(core, battle_struct + 1, 0);
    write32_bytes(core, RULES_BATTLE_WEATHER, RULES_WEATHER_RAIN);
    write8(core, RULES_WEATHER_DURATION, 1);
    struct CallObservation call = call_bounded(core, function, 0, 0, 0, 0);
    if (!call.payload_pc_seen || call.result != 1
        || read32(core, RULES_BATTLE_WEATHER) != 0
        || read8(core, RULES_WEATHER_DURATION) != 0) {
        rules_die("finite weather did not expire exactly at duration zero");
    }
}

static uint32_t observe_weather_damage_case(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t crit_command,
    uint32_t damage_command,
    uint32_t weather
)
{
    restore_snapshot(core, battle);
    prepare_rule_battlers(core);
    uint32_t attacker = ADDR_BATTLE_MONS;
    uint32_t defender = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    write16(core, RULES_CURRENT_MOVE, RULES_MOVE_EMBER);
    write16(core, attacker + BATTLE_MON_MOVES_OFFSET, RULES_MOVE_EMBER);
    write16(core, attacker + RULES_MON_SP_ATTACK, 100);
    write16(core, defender + RULES_MON_SP_DEFENSE, 100);
    write8(core, attacker + 0x2A, 50);
    write8(core, attacker + RULES_MON_TYPE1, RULES_TYPE_NORMAL);
    write8(core, attacker + RULES_MON_TYPE2, RULES_TYPE_NORMAL);
    write8(core, defender + RULES_MON_TYPE1, RULES_TYPE_NORMAL);
    write8(core, defender + RULES_MON_TYPE2, RULES_TYPE_NORMAL);
    write32_bytes(core, RULES_BATTLE_WEATHER, weather);
    write32_bytes(core, BATTLE_CORE_GLOBAL_RNG, RULES_SEED_MISS);
    struct CallObservation crit = call_bounded(core, crit_command, 0, 0, 0, 0);
    if (!crit.payload_pc_seen || read8(core, RULES_CRIT_MULTIPLIER) != 10)
        rules_die("weather damage fixture failed to establish non-critical damage");
    struct CallObservation damage = call_bounded(core, damage_command, 0, 0, 0, 0);
    uint32_t value = read32(core, RULES_BATTLE_MOVE_DAMAGE);
    if (!damage.payload_pc_seen || value == 0)
        rules_die("weather damage command produced no CFRU damage");
    return value;
}

static struct RulesWeatherDamageObservation observe_weather_damage(
    struct mCore *core,
    const struct Snapshot *battle,
    uint32_t crit_command,
    uint32_t damage_command
)
{
    struct RulesWeatherDamageObservation result = {0};
    result.clear = observe_weather_damage_case(
        core, battle, crit_command, damage_command, 0);
    result.rain = observe_weather_damage_case(
        core, battle, crit_command, damage_command, RULES_WEATHER_RAIN);
    result.sun = observe_weather_damage_case(
        core, battle, crit_command, damage_command, RULES_WEATHER_SUN);
    if (result.rain != result.clear / 2U
        || result.sun != (result.clear * 15U) / 10U)
        rules_die("rain/sun damage modifiers differ from CFRU 1/2 and 3/2");
    return result;
}

static void print_cancel(const struct RulesCancelObservation *value)
{
    printf("{\"seed\":%" PRIu32 ",\"rng_after\":%" PRIu32
           ",\"status_before\":%" PRIu32 ",\"status_after\":%" PRIu32
           ",\"unable\":%s}",
           value->seed, value->rng_after, value->status_before,
           value->status_after, value->unable ? "true" : "false");
}

static void print_residual(const struct RulesResidualObservation *value)
{
    printf("{\"status_before\":%" PRIu32 ",\"status_after\":%" PRIu32
           ",\"queued_damage\":%" PRIu32 ",\"hp_before\":%u,\"hp_after\":%u"
           ",\"tracker_after\":%u,\"bank_after\":%u}",
           value->status_before, value->status_after, value->queued_damage,
           value->hp_before, value->hp_after, value->tracker_after,
           value->bank_after);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0)
        rules_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) rules_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) rules_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    struct RulesOwnerObservation owner = observe_rules_owner(core);
    run_trace_prefix(core);
    if (log_problem_count) rules_die("mGBA warned/errored during field boot");
    struct Snapshot field = take_snapshot(core);

    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        RULES_MOVE_TACKLE, RULES_MOVE_EMBER, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 25, 0, 0};
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        RULES_MOVE_TACKLE, 0, 0, 0,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    (void)setup_custom_wild(core, &field, 4, 10, player_moves, player_pp,
                            enemy_moves, enemy_pp);
    struct Snapshot battle = take_snapshot(core);

    struct RulesSpeedObservation speed = observe_paralysis_speed(
        core, &battle, owner.speed.target);
    uint32_t cancel_command = owner.commands[0];
    struct RulesCancelObservation paralysis_hit = observe_canceller(
        core, &battle, cancel_command, RULES_CANCELLER_PARALYSED,
        RULES_STATUS_PARALYSIS, RULES_SEED_HIT);
    struct RulesCancelObservation paralysis_miss = observe_canceller(
        core, &battle, cancel_command, RULES_CANCELLER_PARALYSED,
        RULES_STATUS_PARALYSIS, RULES_SEED_MISS);
    struct RulesCancelObservation sleep = observe_canceller(
        core, &battle, cancel_command, RULES_CANCELLER_ASLEEP,
        RULES_STATUS_SLEEP_3, RULES_SEED_MISS);
    struct RulesCancelObservation freeze_hit = observe_canceller(
        core, &battle, cancel_command, RULES_CANCELLER_FROZEN,
        RULES_STATUS_FREEZE, RULES_SEED_HIT);
    struct RulesCancelObservation freeze_miss = observe_canceller(
        core, &battle, cancel_command, RULES_CANCELLER_FROZEN,
        RULES_STATUS_FREEZE, RULES_SEED_MISS);
    if (!paralysis_hit.unable || paralysis_miss.unable
        || paralysis_hit.rng_after != RULES_RNG_AFTER_HIT
        || paralysis_miss.rng_after != RULES_RNG_AFTER_MISS
        || sleep.status_after != 2 || !sleep.unable
        || freeze_hit.status_after != 0 || freeze_hit.unable
        || freeze_miss.status_after != RULES_STATUS_FREEZE || !freeze_miss.unable
        || freeze_hit.rng_after != RULES_RNG_AFTER_HIT
        || freeze_miss.rng_after != RULES_RNG_AFTER_MISS) {
        rules_die("fixed-RNG paralysis/sleep/freeze boundary changed");
    }

    struct RulesCritObservation crit_hit = observe_crit(
        core, &battle, owner.commands[1], RULES_SEED_HIT);
    struct RulesCritObservation crit_miss = observe_crit(
        core, &battle, owner.commands[1], RULES_SEED_MISS);
    if (crit_hit.multiplier != 15 || crit_miss.multiplier != 10
        || crit_hit.rng_after != RULES_RNG_AFTER_HIT
        || crit_miss.rng_after != RULES_RNG_AFTER_MISS) {
        rules_die("critical 1/24 chance or 1.5x multiplier boundary changed");
    }

    struct RulesResidualObservation poison = observe_residual(
        core, &battle, owner.end_turn.target, RULES_END_TURN_POISON,
        RULES_STATUS_POISON);
    struct RulesResidualObservation toxic = observe_residual(
        core, &battle, owner.end_turn.target, RULES_END_TURN_POISON,
        RULES_STATUS_TOXIC);
    struct RulesResidualObservation burn = observe_residual(
        core, &battle, owner.end_turn.target, RULES_END_TURN_BURN,
        RULES_STATUS_BURN);
    if (poison.queued_damage != 20 || poison.status_after != RULES_STATUS_POISON
        || toxic.queued_damage != 20
        || toxic.status_after != (RULES_STATUS_TOXIC | RULES_STATUS_TOXIC_COUNTER_1)
        || burn.queued_damage != 10 || burn.status_after != RULES_STATUS_BURN) {
        rules_die("poison/toxic/burn residual differs from pinned CFRU runtime");
    }

    struct RulesWeatherObservation weather[4];
    weather[0] = observe_weather_start(
        core, &battle, "RAIN", 0x7D, RULES_WEATHER_RAIN);
    weather[1] = observe_weather_start(
        core, &battle, "SAND", 0x95, RULES_WEATHER_SAND);
    weather[2] = observe_weather_start(
        core, &battle, "SUN", 0xBB, RULES_WEATHER_SUN);
    weather[3] = observe_weather_start(
        core, &battle, "HAIL", 0xC8, RULES_WEATHER_HAIL);
    observe_weather_end(core, &battle, owner.end_turn.target);
    struct RulesWeatherDamageObservation weather_damage = observe_weather_damage(
        core, &battle, owner.commands[1], owner.commands[2]);

    (void)setup_trainer(core, &field);
    uint32_t trainer_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    uint8_t trainer_battlers = read8(core, ADDR_BATTLERS_COUNT);
    if (!(trainer_flags & BATTLE_TYPE_TRAINER) || trainer_battlers != 2)
        rules_die("trainer route did not enter the shared battle runtime");
    struct MultiTargetObservation double_route = run_multi_target_double(core, &field);
    if (!double_route.both_opponents_hit || !double_route.four_controllers_initialized)
        rules_die("double route did not complete through shared controllers");
    if (log_problem_count) rules_die("mGBA warned/errored during battle-rule fixtures");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"cfru_pinned_battle_rules_v1\","
           "\"rom_sha256\":\"%s\",\"read_only\":true,"
           "\"warnings_errors\":0,\"owner\":{\"main_table\":\"0x%08X\","
           "\"secondary_table\":\"0x%08X\",\"root_count\":%zu,"
           "\"commands\":[",
           rom_sha256, RULES_MAIN_COMMAND_TABLE, RULES_SECONDARY_COMMAND_TABLE,
           ARRAY_LEN(RULES_COMMAND_ROOTS));
    for (unsigned index = 0; index < ARRAY_LEN(RULES_COMMANDS); ++index) {
        if (index) putchar(',');
        printf("{\"name\":\"%s\",\"index\":%u,\"target\":\"0x%08" PRIX32 "\"}",
               RULES_COMMANDS[index].name, RULES_COMMANDS[index].index,
               owner.commands[index]);
    }
    printf("],\"hooks\":{\"speed\":\"0x%08" PRIX32
           "\",\"end_turn\":\"0x%08" PRIX32
           "\",\"status\":\"0x%08" PRIX32 "\"}},"
           "\"paralysis\":{\"speed\":{\"clear_vs_60\":%u,"
           "\"paralysis_vs_60\":%u,\"paralysis_vs_30\":%u},"
           "\"immobile\":",
           owner.speed.target, owner.end_turn.target, owner.status.target,
           speed.clear_vs_60, speed.paralysis_vs_60, speed.paralysis_vs_30);
    print_cancel(&paralysis_hit);
    printf(",\"mobile\":");
    print_cancel(&paralysis_miss);
    printf("},\"sleep\":");
    print_cancel(&sleep);
    printf(",\"freeze\":{\"thaw\":");
    print_cancel(&freeze_hit);
    printf(",\"frozen\":");
    print_cancel(&freeze_miss);
    printf("},\"critical\":{\"hit\":{\"seed\":%" PRIu32
           ",\"rng_after\":%" PRIu32 ",\"multiplier\":%u},"
           "\"miss\":{\"seed\":%" PRIu32 ",\"rng_after\":%" PRIu32
           ",\"multiplier\":%u}},\"residual\":{\"poison\":",
           crit_hit.seed, crit_hit.rng_after, crit_hit.multiplier,
           crit_miss.seed, crit_miss.rng_after, crit_miss.multiplier);
    print_residual(&poison);
    printf(",\"toxic\":");
    print_residual(&toxic);
    printf(",\"burn\":");
    print_residual(&burn);
    printf("},\"weather\":{\"start\":[");
    for (unsigned index = 0; index < ARRAY_LEN(weather); ++index) {
        if (index) putchar(',');
        printf("{\"name\":\"%s\",\"command\":%u,\"flag\":%" PRIu32
               ",\"duration\":%u}", weather[index].name,
               weather[index].command, weather[index].flag,
               weather[index].duration);
    }
    printf("],\"end_at_zero\":true,\"damage\":{\"clear\":%" PRIu32
           ",\"rain\":%" PRIu32 ",\"sun\":%" PRIu32 "}},"
           "\"modes\":{\"wild\":true,\"trainer\":{\"flags\":%" PRIu32
           ",\"battlers\":%u},\"double\":{\"flags\":%" PRIu32
           ",\"battlers\":%u,\"both_opponents_hit\":true}}}\n",
           weather_damage.clear, weather_damage.rain, weather_damage.sun,
           trainer_flags, trainer_battlers, double_route.type_flags,
           double_route.battler_count);

    free(battle.bytes);
    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
