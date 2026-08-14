/*
 * USER-20260814-BATTLE-UI exact-ROM fixture for libmGBA 0.10.2.
 *
 * The runner verifies the two physical CFRU move-menu hooks, exercises the
 * stage-24 adapter through those hooks, and then completes ordinary wild,
 * trainer, and double move-input routes.  Factory/Raid use the separate
 * current-stage policy runner.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    UI_TYPE_HOOK = 0x080300D0,
    UI_EFFECT_HOOK = 0x08030024,
    UI_TYPE_ENTRY = 0x09115724,
    UI_EFFECT_ENTRY = 0x09116E08,
    UI_BATTLE_BUFFER_A = 0x02022B24,
    UI_ACTIVE_BATTLER = 0x02023B24,
    UI_BATTLERS_COUNT = 0x02023B2C,
    UI_BATTLER_POSITIONS = 0x02023B36,
    UI_MOVE_CURSOR = 0x02023F5C,
    UI_CONTROLLER_FUNCS = 0x03005020,
    UI_MULTI_CURSOR = 0x03005034,
    UI_DISPLAYED_STRING = 0x020228FC,
    UI_PLTT_UNFADED = 0x0203712C,
    UI_NEW_BATTLE_STRUCT_PTR = 0x0203DFB0,
    UI_TYPE_PALETTE = 0x091B66B8,
    UI_TEXT_SUPER = 0x091430FB,
    UI_TEXT_RESISTED = 0x091430FE,
    UI_TEXT_NONE = 0x09143101,
    UI_TEXT_STAB = 0x09143103,
    UI_TYPE_MATRIX = 0x09164AA4,
    UI_HANDLE_CHOOSE_TARGET = 0x09115D05,
    UI_VISUAL_TYPE_CALC = 0x090E5DC1,

    UI_INFO_MOVES = 0x00,
    UI_INFO_MON_TYPE1 = 0x12,
    UI_INFO_MON_TYPE2 = 0x13,
    UI_INFO_MOVE_TYPES = 0x14,
    UI_INFO_MOVE_RESULTS = 0x18,
    UI_INFO_Z_MOVE_RESULTS = 0x28,
    UI_INFO_MOVE_SPLIT = 0x48,
    UI_INFO_MON_TYPE3 = 0x50,
    UI_INFO_MON_TERA_TYPE = 0x51,
    UI_INFO_SIZE = 0x78,

    UI_EFFECT_NORMAL = 0,
    UI_EFFECT_SUPER = 1,
    UI_EFFECT_RESISTED = 2,
    UI_EFFECT_NONE = 3,
    UI_MOVE_RESULT_SUPER = 1 << 1,
    UI_MOVE_RESULT_RESISTED = 1 << 2,
    UI_MOVE_RESULT_NONE = 1 << 3,
    UI_BATTLE_TYPE_DOUBLE = 1 << 0,
    UI_TYPE_FIRE = 10,
    UI_TYPE_WATER = 11,
    UI_TYPE_GRASS = 12,
    UI_TYPE_ELECTRIC = 13,
    UI_TYPE_GROUND = 4,
    UI_TYPE_ROCK = 5,
    UI_TYPE_BUG = 6,
    UI_TYPE_STELLAR = 24,
    UI_MOVE_TACKLE = 33,
    UI_MOVE_TERA_BLAST = 1037,
    UI_STAB_PALETTE_INDEX = 86,
    UI_EFFECT_PALETTE_INDEX = 88,
};

struct UIEffectObservation {
    const char *name;
    uint8_t result_flags;
    uint8_t expected_class;
    uint8_t actual_class;
    uint8_t palette_group;
    bool expected_stab;
    bool saw_effect_label;
    bool saw_stab_label;
    bool entry_completed;
};

static void ui_die(const char *message)
{
    fprintf(stderr, "mgba-battle-ui-smoke: %s\n", message);
    exit(1);
}

static uint32_t ui_parse_address(const char *raw)
{
    char *end = NULL;
    unsigned long value = strtoul(raw, &end, 0);
    if (!raw[0] || !end || *end || value > UINT32_MAX || !(value & 1U))
        ui_die("invalid Thumb entry argument");
    return (uint32_t)value;
}

static uint32_t hook_target(struct mCore *core, uint32_t address)
{
    uint8_t first = read8(core, address);
    uint8_t second = read8(core, address + 1U);
    uint8_t third = read8(core, address + 2U);
    uint8_t fourth = read8(core, address + 3U);
    unsigned reg = second & 7U;
    if (first != 0 || (second & 0xF8U) != 0x48U
        || third != reg * 8U || fourth != 0x47U) {
        ui_die("Thumb absolute hook shape differs");
    }
    uint32_t target = read32(core, address + 4U);
    if (!(target & 1U)) ui_die("Thumb absolute hook target is not odd");
    return target;
}

static bool contains_string(struct mCore *core, uint32_t buffer,
                            uint32_t source)
{
    uint8_t expected[32];
    size_t length = 0;
    while (length < ARRAY_LEN(expected)) {
        uint8_t value = read8(core, source + (uint32_t)length);
        if (value == 0xFFU) break;
        expected[length++] = value;
    }
    if (length == 0 || length == ARRAY_LEN(expected)) return false;
    for (size_t offset = 0; offset + length <= 96U; ++offset) {
        bool equal = true;
        for (size_t index = 0; index < length; ++index) {
            if (read8(core, buffer + (uint32_t)offset + (uint32_t)index)
                != expected[index]) {
                equal = false;
                break;
            }
        }
        if (equal) return true;
    }
    return false;
}

static void clear_move_info(struct mCore *core)
{
    uint32_t info = UI_BATTLE_BUFFER_A + 4U;
    for (unsigned index = 0; index < UI_INFO_SIZE; ++index)
        write8(core, info + index, 0);
    write8(core, UI_ACTIVE_BATTLER, 0);
    write8(core, UI_MOVE_CURSOR, 0);
    write8(core, UI_BATTLERS_COUNT, 2);
    for (unsigned bank = 0; bank < 4; ++bank)
        write8(core, UI_BATTLER_POSITIONS + bank, (uint8_t)bank);
    write16(core, info + UI_INFO_MOVES, UI_MOVE_TACKLE);
    write8(core, info + UI_INFO_MOVE_TYPES, UI_TYPE_FIRE);
    write8(core, info + UI_INFO_MOVE_SPLIT, 0);
    write8(core, info + UI_INFO_MON_TYPE1, UI_TYPE_WATER);
    write8(core, info + UI_INFO_MON_TYPE2, UI_TYPE_WATER);
    write8(core, info + UI_INFO_MON_TYPE3, 20); /* CFRU blank type */
    write8(core, info + UI_INFO_MON_TERA_TYPE, UI_TYPE_STELLAR);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP, 20);
}

static uint8_t palette_group(struct mCore *core)
{
    uint16_t value = read16(core, UI_PLTT_UNFADED
                            + UI_EFFECT_PALETTE_INDEX * 2U);
    static const uint8_t starts[] = {12, 0, 4, 8};
    for (unsigned effect = 0; effect < ARRAY_LEN(starts); ++effect) {
        if (value == read16(core, UI_TYPE_PALETTE + starts[effect] * 2U))
            return (uint8_t)effect;
    }
    ui_die("effect palette does not match a fixed CFRU group");
    return 0;
}

static struct UIEffectObservation observe_effect(
    struct mCore *core, uint32_t effect_entry, uint32_t classify_entry,
    const char *name, uint8_t flags, uint8_t expected_class, bool stab)
{
    struct UIEffectObservation result = {
        .name = name,
        .result_flags = flags,
        .expected_class = expected_class,
        .expected_stab = stab,
    };
    clear_move_info(core);
    uint32_t info = UI_BATTLE_BUFFER_A + 4U;
    if (stab) write8(core, info + UI_INFO_MON_TYPE1, UI_TYPE_FIRE);
    write8(core, info + UI_INFO_MOVE_RESULTS + 1U * 4U, flags);
    write8(core, info + UI_INFO_Z_MOVE_RESULTS + 1U * 4U, flags);
    result.actual_class = (uint8_t)call_bounded(
        core, classify_entry, flags, 0, 0, 0).result;
    struct CallObservation call = call_bounded(
        core, effect_entry, 0, 0, 0, 0);
    result.entry_completed = call.instructions > 0;
    result.palette_group = palette_group(core);
    result.saw_effect_label = expected_class == UI_EFFECT_SUPER
        ? contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_SUPER)
        : expected_class == UI_EFFECT_RESISTED
        ? contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_RESISTED)
        : expected_class == UI_EFFECT_NONE
        ? contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_NONE)
        : !contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_SUPER)
            && !contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_RESISTED)
            && !contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_NONE);
    result.saw_stab_label = contains_string(
        core, UI_DISPLAYED_STRING, UI_TEXT_STAB);
    if (result.actual_class != expected_class
        || result.palette_group != expected_class
        || !result.saw_effect_label
        || result.saw_stab_label != stab
        || !result.entry_completed) {
        ui_die("effect label/palette/STAB contract failed");
    }
    return result;
}

static uint32_t matrix_multiplier(struct mCore *core, uint8_t attack,
                                  uint8_t type1, uint8_t type2)
{
    uint32_t first = read16(core, UI_TYPE_MATRIX
                            + ((uint32_t)attack * 25U + type1) * 2U);
    uint32_t second = type1 == type2 ? 1000U : read16(
        core, UI_TYPE_MATRIX + ((uint32_t)attack * 25U + type2) * 2U);
    if (first == 1U || second == 1U) return 0;
    if (first == 0U) first = 1000U;
    if (second == 0U) second = 1000U;
    return first * second / 1000U;
}

static void print_effect(const struct UIEffectObservation *row)
{
    printf("{\"name\":\"%s\",\"result_flags\":%u,"
           "\"class\":%u,\"palette_group\":%u,"
           "\"effect_label\":%s,\"stab\":%s,\"entry_completed\":%s}",
           row->name, row->result_flags, row->actual_class,
           row->palette_group, row->saw_effect_label ? "true" : "false",
           row->saw_stab_label ? "true" : "false",
           row->entry_completed ? "true" : "false");
}

int main(int argc, char **argv)
{
    if (argc != 7) {
        fprintf(stderr, "usage: %s ROM SHA TYPE EFFECT CLASSIFY GETTYPE\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0)
        ui_die("ROM SHA-256 mismatch");
    uint32_t type_runtime = ui_parse_address(argv[3]);
    uint32_t effect_runtime = ui_parse_address(argv[4]);
    uint32_t classify_runtime = ui_parse_address(argv[5]);
    uint32_t get_type_runtime = ui_parse_address(argv[6]);

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) ui_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) ui_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    if (hook_target(core, UI_TYPE_HOOK) != (UI_TYPE_ENTRY | 1U)
        || hook_target(core, UI_EFFECT_HOOK) != (UI_EFFECT_ENTRY | 1U)
        || hook_target(core, UI_TYPE_ENTRY) != type_runtime
        || hook_target(core, UI_EFFECT_ENTRY) != effect_runtime) {
        ui_die("physical move-menu ownership chain differs");
    }

    run_trace_prefix(core);
    if (log_problem_count) ui_die("mGBA warned/errored during field boot");
    struct Snapshot field = take_snapshot(core);
    (void)setup_wild(core, &field);
    if (read32(core, UI_NEW_BATTLE_STRUCT_PTR) == 0)
        ui_die("battle UI fixture has no CFRU battle state");

    struct UIEffectObservation effects[] = {
        observe_effect(core, UI_EFFECT_ENTRY | 1U, classify_runtime,
                       "NORMAL_1X", 0, UI_EFFECT_NORMAL, false),
        observe_effect(core, UI_EFFECT_ENTRY | 1U, classify_runtime,
                       "SUPER_2X_OR_MORE", UI_MOVE_RESULT_SUPER,
                       UI_EFFECT_SUPER, false),
        observe_effect(core, UI_EFFECT_ENTRY | 1U, classify_runtime,
                       "RESISTED_HALF_OR_LESS", UI_MOVE_RESULT_RESISTED,
                       UI_EFFECT_RESISTED, false),
        observe_effect(core, UI_EFFECT_ENTRY | 1U, classify_runtime,
                       "NO_EFFECT_0X", UI_MOVE_RESULT_NONE,
                       UI_EFFECT_NONE, false),
        observe_effect(core, UI_EFFECT_ENTRY | 1U, classify_runtime,
                       "SUPER_AND_STAB", UI_MOVE_RESULT_SUPER,
                       UI_EFFECT_SUPER, true),
    };

    clear_move_info(core);
    uint32_t info = UI_BATTLE_BUFFER_A + 4U;
    write8(core, info + UI_INFO_MOVE_TYPES, UI_TYPE_STELLAR);
    uint32_t stellar_type = call_bounded(
        core, get_type_runtime, 0, 0, 0, 0).result;
    if (stellar_type != UI_TYPE_STELLAR) ui_die("Stellar type display differs");
    if (!call_bounded(core, UI_TYPE_ENTRY | 1U, 0, 0, 0, 0).instructions)
        ui_die("type-window adapter did not return");

    clear_move_info(core);
    write16(core, info + UI_INFO_MOVES, UI_MOVE_TERA_BLAST);
    write8(core, info + UI_INFO_MOVE_TYPES, UI_TYPE_FIRE);
    write8(core, info + UI_INFO_MON_TERA_TYPE, UI_TYPE_STELLAR);
    uint32_t new_battle = read32(core, UI_NEW_BATTLE_STRUCT_PTR);
    write8(core, new_battle + 0x268U, 1);
    uint32_t tera_selected_type = call_bounded(
        core, get_type_runtime, 0, 0, 0, 0).result;
    write8(core, new_battle + 0x268U, 0);
    uint32_t tera_clear_type = call_bounded(
        core, get_type_runtime, 0, 0, 0, 0).result;
    if (tera_selected_type != UI_TYPE_STELLAR
        || tera_clear_type != UI_TYPE_FIRE) {
        ui_die("Tera Blast selected/clear type display differs");
    }

    /* Double target selection uses the chosen target's precomputed result. */
    clear_move_info(core);
    write32_bytes(core, ADDR_BATTLE_TYPE_FLAGS,
                  read32(core, ADDR_BATTLE_TYPE_FLAGS) | UI_BATTLE_TYPE_DOUBLE);
    write8(core, UI_BATTLERS_COUNT, 4);
    write32_bytes(core, UI_CONTROLLER_FUNCS, UI_HANDLE_CHOOSE_TARGET);
    write8(core, UI_MULTI_CURSOR, 3);
    write8(core, info + UI_INFO_MOVE_RESULTS + 3U * 4U,
           UI_MOVE_RESULT_RESISTED);
    struct CallObservation double_call = call_bounded(
        core, UI_EFFECT_ENTRY | 1U, 0, 0, 0, 0);
    bool double_target_specific = double_call.instructions > 0
        && palette_group(core) == UI_EFFECT_RESISTED
        && contains_string(core, UI_DISPLAYED_STRING, UI_TEXT_RESISTED);
    if (!double_target_specific) ui_die("double target-specific display differs");

    uint32_t multipliers[] = {
        matrix_multiplier(core, UI_TYPE_FIRE, UI_TYPE_WATER, UI_TYPE_WATER),
        matrix_multiplier(core, UI_TYPE_FIRE, UI_TYPE_GRASS, UI_TYPE_GRASS),
        matrix_multiplier(core, UI_TYPE_FIRE, UI_TYPE_GRASS, UI_TYPE_BUG),
        matrix_multiplier(core, UI_TYPE_FIRE, UI_TYPE_WATER, UI_TYPE_ROCK),
        matrix_multiplier(core, UI_TYPE_ELECTRIC, UI_TYPE_GROUND, UI_TYPE_GROUND),
    };
    const uint32_t expected_multipliers[] = {500, 2000, 4000, 250, 0};
    if (memcmp(multipliers, expected_multipliers, sizeof(multipliers)) != 0)
        ui_die("fixed CFRU type matrix multiplier fixture differs");

    struct BattleObservation wild = run_wild(core, &field, 0);
    struct BattleObservation trainer = run_trainer(core, &field);
    struct MultiTargetObservation double_route = run_multi_target_double(core, &field);
    bool input_return = wild.turn.pp_spent && trainer.turn.pp_spent
        && double_route.both_opponents_hit;
    if (!input_return || log_problem_count)
        ui_die("wild/trainer/double input or screen return failed");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"cfru_move_menu_effectiveness_v1\","
           "\"rom_sha256\":\"%s\",\"read_only\":true,"
           "\"warnings_errors\":0,\"owner\":{"
           "\"type_hook\":\"0x%08X\",\"type_entry\":\"0x%08X\","
           "\"effect_hook\":\"0x%08X\",\"effect_entry\":\"0x%08X\"},"
           "\"effect_cases\":[",
           rom_sha256, UI_TYPE_HOOK, type_runtime, UI_EFFECT_HOOK, effect_runtime);
    for (unsigned index = 0; index < ARRAY_LEN(effects); ++index) {
        if (index) putchar(',');
        print_effect(&effects[index]);
    }
    printf("],\"type_cases\":{\"stellar\":%" PRIu32
           ",\"tera_blast_selected\":%" PRIu32
           ",\"tera_blast_clear\":%" PRIu32 "},"
           "\"matrix_multipliers\":[%" PRIu32 ",%" PRIu32
           ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 "],"
           "\"double_target_specific\":true,\"routes\":{"
           "\"wild\":{\"pp_spent\":true,\"outcome\":%u},"
           "\"trainer\":{\"pp_spent\":true,\"outcome\":%u},"
           "\"double\":{\"both_opponents_hit\":true,\"battlers\":%u}},"
           "\"input_return\":true,\"artifacts_written\":[]}",
           stellar_type, tera_selected_type, tera_clear_type,
           multipliers[0], multipliers[1], multipliers[2], multipliers[3],
           multipliers[4], wild.turn.outcome_after, trainer.turn.outcome_after,
           double_route.battler_count);
    putchar('\n');

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
