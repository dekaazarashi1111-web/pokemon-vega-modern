/* USER-20260814-MOVE-MEMORY exact-ROM fixture for libmGBA 0.10.2. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    MM_LEVEL_ROOT_SITE = 0x0803E1E8,
    MM_RELEARNER_ENTRY = 0x091140A0,
    MM_GET_ALL_EGG_MOVES = 0x090EB839,
    MM_ITEM_DATA = 0x0904D108,
    MM_ITEM_STRIDE = 40,
    MM_ITEM_ID = 347,
    MM_ITEM_CALLBACK_OFFSET = 24,
    MM_SHIOU_POINTER = 0x08382628,
    MM_KARASUBA_POINTER = 0x0838047C,
    MM_BADGE_POINTER = 0x0817F893,
    MM_MODE = 0x0203EC00,
    MM_PARTY = 0x020241E4,
    MM_VAR_8004 = 0x02036FF4,
    MM_VAR_8005 = 0x02036FF6,
    MM_RESULT = 0x02037004,
    MM_OUTPUT = 0x0203ED00,
    MM_OUTPUT_DIRECT = 0x0203ED80,
    MM_POKEMON_SIZE = 100,
    MM_MON_SPECIES = 0x20,
    MM_MON_CHECKSUM = 0x1C,
    MM_MON_PP_BONUSES = 0x28,
    MM_MON_MOVES = 0x2C,
    MM_MON_LEVEL = 0x54,
    MM_SPECIES_COUNT = 1621,
    MM_VEGA_SPECIES_COUNT = 412,
    MM_MAX_MOVES = 40,
    MM_EGG_BUFFER = 50,
    MM_MOVE_SURF = 57,
    MM_MOVE_SECRET_SWORD = 619,
    MM_MOVE_BEHEMOTH_BLADE = 768,
    MM_MOVE_BEHEMOTH_BASH = 769,
    MM_SPECIES_KELDEO = 0x2BC,
    MM_SPECIES_KELDEO_RESOLUTE = 0x2F5,
};

struct MmSymbols {
    uint32_t field_use;
    uint32_t get_moves;
    uint32_t set_normal;
    uint32_t set_egg;
    uint32_t reset_mode;
    uint32_t context_policy;
    uint32_t egg_policy;
    uint32_t can_forget;
    uint32_t selected_empty;
    uint32_t selected_pp;
    uint32_t selected_forget;
    uint32_t delete_selected;
    uint32_t shiou_script;
    uint32_t karasuba_script;
    uint32_t badge_script;
    uint32_t forget_select_script;
    uint32_t pp_warning_script;
    uint32_t forget_delete_script;
    uint32_t egg_select_script;
    uint32_t finish_script;
};

struct MmLearnMove {
    uint16_t move;
    uint8_t level;
};

static void mm_die(const char *message)
{
    fprintf(stderr, "mgba-move-memory-smoke: %s\n", message);
    exit(1);
}

static uint32_t mm_parse_address(const char *raw, bool thumb)
{
    char *end = NULL;
    unsigned long value = strtoul(raw, &end, 0);
    if (!raw[0] || !end || *end || value > UINT32_MAX)
        mm_die("invalid address argument");
    if (thumb && !(value & 1U)) mm_die("function address is not Thumb");
    if (!thumb && (value < 0x08000000U || value >= 0x0A000000U))
        mm_die("script address is outside ROM");
    return (uint32_t)value;
}

static void mm_set_symbol(struct MmSymbols *symbols, const char *key,
                          const char *value)
{
#define MM_FUNCTION(name, member) \
    if (!strcmp(key, name)) { symbols->member = mm_parse_address(value, true); return; }
#define MM_SCRIPT(name, member) \
    if (!strcmp(key, name)) { symbols->member = mm_parse_address(value, false); return; }
    MM_FUNCTION("VegaMoveMemory_FieldUse", field_use)
    MM_FUNCTION("VegaMoveMemory_GetMoveRelearnerMoves", get_moves)
    MM_FUNCTION("VegaMoveMemory_SetNormalMode", set_normal)
    MM_FUNCTION("VegaMoveMemory_SetEggMode", set_egg)
    MM_FUNCTION("VegaMoveMemory_ResetMode", reset_mode)
    MM_FUNCTION("VegaMoveMemory_ContextAllowedFromState", context_policy)
    MM_FUNCTION("VegaMoveMemory_EvaluateEggPolicy", egg_policy)
    MM_FUNCTION("VegaMoveMemory_CanForgetMove", can_forget)
    MM_FUNCTION("VegaMoveMemory_SelectedMonHasEmptySlot", selected_empty)
    MM_FUNCTION("VegaMoveMemory_SelectedMoveHasPpUps", selected_pp)
    MM_FUNCTION("VegaMoveMemory_SelectedMoveCanForget", selected_forget)
    MM_FUNCTION("VegaMoveMemory_DeleteSelectedMove", delete_selected)
    MM_SCRIPT("script_shiou_npc", shiou_script)
    MM_SCRIPT("script_karasuba_npc", karasuba_script)
    MM_SCRIPT("script_badge1_reward", badge_script)
    MM_SCRIPT("script_forget_select", forget_select_script)
    MM_SCRIPT("script_forget_pp_warning", pp_warning_script)
    MM_SCRIPT("script_forget_delete", forget_delete_script)
    MM_SCRIPT("script_egg_select", egg_select_script)
    MM_SCRIPT("script_finish", finish_script)
#undef MM_FUNCTION
#undef MM_SCRIPT
    mm_die("unknown symbol argument");
}

static bool mm_symbols_complete(const struct MmSymbols *symbols)
{
    const uint32_t *values = (const uint32_t *)symbols;
    for (size_t index = 0; index < sizeof(*symbols) / sizeof(*values); ++index) {
        if (!values[index]) return false;
    }
    return true;
}

static uint32_t mm_hook_target(struct mCore *core, uint32_t address)
{
    if (read8(core, address) != 0x00U || read8(core, address + 1U) != 0x4BU
        || read8(core, address + 2U) != 0x18U
        || read8(core, address + 3U) != 0x47U) {
        mm_die("move-relearner hook shape differs");
    }
    uint32_t target = read32(core, address + 4U);
    if (!(target & 1U)) mm_die("move-relearner target is not Thumb");
    return target;
}

static uint32_t mm_read_u32_bytes(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | (uint32_t)read8(core, address + 1U) << 8
        | (uint32_t)read8(core, address + 2U) << 16
        | (uint32_t)read8(core, address + 3U) << 24;
}

static uint16_t mm_read_u16_bytes(struct mCore *core, uint32_t address)
{
    return (uint16_t)((uint16_t)read8(core, address)
        | (uint16_t)read8(core, address + 1U) << 8);
}

static void mm_clear(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0; index < size; ++index)
        write8(core, address + index, 0);
}

static void mm_write_mon(struct mCore *core, uint16_t species, uint8_t level,
                         const uint16_t moves[4], uint8_t pp_bonuses)
{
    mm_clear(core, MM_PARTY, MM_POKEMON_SIZE);
    write16(core, MM_PARTY + MM_MON_SPECIES, species);
    write8(core, MM_PARTY + MM_MON_LEVEL, level);
    write8(core, MM_PARTY + MM_MON_PP_BONUSES, pp_bonuses);
    for (unsigned slot = 0; slot < 4; ++slot)
        write16(core, MM_PARTY + MM_MON_MOVES + slot * 2U, moves[slot]);
    uint32_t checksum = 0;
    for (unsigned offset = MM_MON_SPECIES; offset < MM_MON_SPECIES + 48U;
         offset += 2U) {
        checksum += read16(core, MM_PARTY + offset);
    }
    write16(core, MM_PARTY + MM_MON_CHECKSUM, (uint16_t)checksum);
}

static unsigned mm_read_learnset(struct mCore *core, uint16_t species,
                                 struct MmLearnMove moves[MM_MAX_MOVES])
{
    uint32_t root = read32(core, MM_LEVEL_ROOT_SITE);
    uint32_t cursor = read32(core, root + (uint32_t)species * 4U);
    if (root < 0x08000000U || root >= 0x0A000000U
        || cursor < 0x08000000U || cursor >= 0x0A000000U) {
        return 0;
    }
    unsigned count = 0;
    while (count < MM_MAX_MOVES) {
        uint16_t move;
        uint8_t level;
        if (species < MM_VEGA_SPECIES_COUNT) {
            uint16_t packed = read16(core, cursor);
            cursor += 2U;
            if (packed == 0xFFFFU) break;
            move = packed & 0x01FFU;
            level = (uint8_t)(packed >> 9);
        } else {
            move = mm_read_u16_bytes(core, cursor);
            level = read8(core, cursor + 2U);
            cursor += 3U;
            if (move == 0 && level == 0xFFU) break;
        }
        if (move) {
            moves[count].move = move;
            moves[count].level = level;
            ++count;
        }
    }
    return count;
}

static bool mm_contains(const uint16_t *values, unsigned count, uint16_t value)
{
    for (unsigned index = 0; index < count; ++index)
        if (values[index] == value) return true;
    return false;
}

static uint16_t mm_find_fixture_species(struct mCore *core,
                                        struct MmLearnMove fixture[MM_MAX_MOVES],
                                        unsigned *fixture_count,
                                        uint16_t *known_move)
{
    for (uint16_t species = MM_VEGA_SPECIES_COUNT;
         species < MM_SPECIES_COUNT; ++species) {
        struct MmLearnMove rows[MM_MAX_MOVES];
        unsigned count = mm_read_learnset(core, species, rows);
        uint16_t low[MM_MAX_MOVES] = {0};
        unsigned low_count = 0;
        bool level_zero = false;
        bool level_one = false;
        bool future = false;
        for (unsigned index = 0; index < count; ++index) {
            if (rows[index].level <= 1) {
                if (!mm_contains(low, low_count, rows[index].move))
                    low[low_count++] = rows[index].move;
                if (rows[index].level == 0) level_zero = true;
                if (rows[index].level == 1) level_one = true;
            } else if (rows[index].level <= 100) {
                future = true;
            }
        }
        if (level_zero && level_one && future && low_count >= 3) {
            memcpy(fixture, rows, sizeof(rows));
            *fixture_count = count;
            *known_move = low[low_count - 1U];
            return species;
        }
    }
    mm_die("no mixed-ABI level-boundary fixture species found");
    return 0;
}

static bool mm_output_has_level(const uint16_t *output, unsigned output_count,
                                const struct MmLearnMove *rows,
                                unsigned row_count, uint8_t level)
{
    for (unsigned index = 0; index < row_count; ++index)
        if (rows[index].level == level
            && mm_contains(output, output_count, rows[index].move)) return true;
    return false;
}

static bool mm_no_output_above_level(const uint16_t *output, unsigned output_count,
                                     const struct MmLearnMove *rows,
                                     unsigned row_count, uint8_t level)
{
    for (unsigned out = 0; out < output_count; ++out) {
        uint8_t minimum = 0xFF;
        for (unsigned index = 0; index < row_count; ++index)
            if (rows[index].move == output[out] && rows[index].level < minimum)
                minimum = rows[index].level;
        if (minimum > level) return false;
    }
    return true;
}

static bool mm_no_duplicates(const uint16_t *moves, unsigned count)
{
    for (unsigned left = 0; left < count; ++left)
        for (unsigned right = left + 1U; right < count; ++right)
            if (moves[left] == moves[right]) return false;
    return true;
}

static bool mm_script_contains(struct mCore *core, uint32_t script,
                               unsigned limit, const uint8_t *needle,
                               unsigned needle_size)
{
    if (!needle_size || needle_size > limit) return false;
    for (unsigned offset = 0; offset + needle_size <= limit; ++offset) {
        bool equal = true;
        for (unsigned index = 0; index < needle_size; ++index) {
            if (read8(core, script + offset + index) != needle[index]) {
                equal = false;
                break;
            }
        }
        if (equal) return true;
    }
    return false;
}

static bool mm_script_has_native(struct mCore *core, uint32_t script,
                                 unsigned limit, uint32_t target)
{
    uint8_t needle[5] = {
        0x23, (uint8_t)target, (uint8_t)(target >> 8),
        (uint8_t)(target >> 16), (uint8_t)(target >> 24),
    };
    return mm_script_contains(core, script, limit, needle, sizeof(needle));
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "usage: %s ROM SHA NAME=ADDRESS...\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0)
        mm_die("ROM SHA-256 mismatch");
    struct MmSymbols symbols = {0};
    for (int index = 3; index < argc; ++index) {
        char argument[160];
        if (strlen(argv[index]) >= sizeof(argument)) mm_die("symbol argument too long");
        strcpy(argument, argv[index]);
        char *equals = strchr(argument, '=');
        if (!equals) mm_die("symbol argument lacks equals");
        *equals = '\0';
        mm_set_symbol(&symbols, argument, equals + 1);
    }
    if (!mm_symbols_complete(&symbols)) mm_die("required symbol argument missing");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) mm_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) mm_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    if (log_problem_count) mm_die("mGBA warned/errored during field boot");

    bool physical =
        mm_hook_target(core, MM_RELEARNER_ENTRY) == symbols.get_moves
        && read32(core, MM_ITEM_DATA + MM_ITEM_ID * MM_ITEM_STRIDE
                         + MM_ITEM_CALLBACK_OFFSET) == symbols.field_use
        && read32(core, MM_SHIOU_POINTER) == symbols.shiou_script
        && read32(core, MM_KARASUBA_POINTER) == symbols.karasuba_script
        && mm_read_u32_bytes(core, MM_BADGE_POINTER) == symbols.badge_script;
    if (!physical) mm_die("physical move-memory patch chain differs");

    struct MmLearnMove rows[MM_MAX_MOVES] = {{0}};
    unsigned row_count = 0;
    uint16_t known_move = 0;
    uint16_t species = mm_find_fixture_species(
        core, rows, &row_count, &known_move);
    uint16_t mon_moves[4] = {known_move, 0, 0, 0};
    mm_write_mon(core, species, 1, mon_moves, 0);
    mm_clear(core, MM_OUTPUT, MM_MAX_MOVES * 2U);
    call_bounded(core, symbols.set_normal, 0, 0, 0, 0);
    unsigned low_count = call_bounded(
        core, MM_RELEARNER_ENTRY | 1U, MM_PARTY, MM_OUTPUT, 0, 0).result;
    if (low_count > MM_MAX_MOVES) mm_die("normal candidate count overflow");
    uint16_t low[MM_MAX_MOVES] = {0};
    for (unsigned index = 0; index < low_count; ++index)
        low[index] = read16(core, MM_OUTPUT + index * 2U);
    bool level_zero_one = mm_output_has_level(low, low_count, rows, row_count, 0)
        && mm_output_has_level(low, low_count, rows, row_count, 1);
    bool future_rejected = mm_no_output_above_level(
        low, low_count, rows, row_count, 1);
    bool known_filtered = !mm_contains(low, low_count, known_move)
        && mm_no_duplicates(low, low_count);

    mm_write_mon(core, species, 100, mon_moves, 0);
    mm_clear(core, MM_OUTPUT_DIRECT, MM_MAX_MOVES * 2U);
    unsigned high_count = call_bounded(
        core, symbols.get_moves, MM_PARTY, MM_OUTPUT_DIRECT, 0, 0).result;
    bool future_exists = false;
    for (unsigned index = 0; index < row_count; ++index) {
        for (unsigned out = 0; out < high_count; ++out) {
            if (rows[index].level > 1 && rows[index].level <= 100
                && read16(core, MM_OUTPUT_DIRECT + out * 2U) == rows[index].move)
                future_exists = true;
        }
    }
    future_rejected = future_rejected && future_exists;
    if (!level_zero_one || !future_rejected || !known_filtered) {
        fprintf(stderr,
                "normal detail species=%u rows=%u low=%u high=%u known=%u "
                "level01=%u future=%u filtered=%u mode=%u\n",
                species, row_count, low_count, high_count, known_move,
                level_zero_one, future_rejected, known_filtered,
                read8(core, MM_MODE));
        fprintf(stderr, "root=%08" PRIX32 " cursor=%08" PRIX32 " rows:",
                read32(core, MM_LEVEL_ROOT_SITE),
                read32(core, read32(core, MM_LEVEL_ROOT_SITE)
                             + (uint32_t)species * 4U));
        for (unsigned index = 0; index < row_count; ++index)
            fprintf(stderr, " %u@%u", rows[index].move, rows[index].level);
        fprintf(stderr, " high:");
        for (unsigned index = 0; index < high_count; ++index)
            fprintf(stderr, " %u", read16(core, MM_OUTPUT_DIRECT + index * 2U));
        fputc('\n', stderr);
        mm_die("normal learnset boundary fixture failed");
    }

    uint16_t egg_mon_moves[4] = {0, 0, 0, 0};
    mm_write_mon(core, 1, 50, egg_mon_moves, 0);
    mm_clear(core, MM_OUTPUT, MM_EGG_BUFFER * 2U);
    mm_clear(core, MM_OUTPUT_DIRECT, MM_EGG_BUFFER * 2U);
    unsigned direct_egg_count = call_bounded(
        core, MM_GET_ALL_EGG_MOVES, MM_PARTY, MM_OUTPUT_DIRECT, 1, 0).result;
    call_bounded(core, symbols.set_egg, 0, 0, 0, 0);
    unsigned adapter_egg_count = call_bounded(
        core, symbols.get_moves, MM_PARTY, MM_OUTPUT, 0, 0).result;
    unsigned expected_egg_count = direct_egg_count > MM_MAX_MOVES
        ? MM_MAX_MOVES : direct_egg_count;
    bool egg_owner = adapter_egg_count == expected_egg_count;
    for (unsigned index = 0; index < expected_egg_count && egg_owner; ++index)
        egg_owner = read16(core, MM_OUTPUT + index * 2U)
            == read16(core, MM_OUTPUT_DIRECT + index * 2U);
    call_bounded(core, symbols.reset_mode, 0, 0, 0, 0);
    bool mode_reset = read8(core, MM_MODE) == 0;
    if (!egg_owner || !mode_reset) mm_die("egg owner/reset fixture failed");

    const uint32_t egg_cases[][5] = {
        {0, 0, 0, 0, 0}, {1, 0, 0, 1, 2}, {1, 0, 1, 0, 3},
        {1, 0, 1, 1, 1}, {1, 1, 0, 0, 1},
    };
    for (unsigned index = 0; index < ARRAY_LEN(egg_cases); ++index) {
        uint32_t observed = call_bounded(
            core, symbols.egg_policy, egg_cases[index][0], egg_cases[index][1],
            egg_cases[index][2], egg_cases[index][3]).result;
        if (observed != egg_cases[index][4]) mm_die("egg policy matrix differs");
    }
    const uint32_t context_cases[][4] = {
        {0, 0, 0, 1}, {1, 0, 0, 0}, {0, 1, 0, 0}, {0, 0, 1, 0},
    };
    for (unsigned index = 0; index < ARRAY_LEN(context_cases); ++index) {
        uint32_t observed = call_bounded(
            core, symbols.context_policy, context_cases[index][0],
            context_cases[index][1], context_cases[index][2], 0).result;
        if (observed != context_cases[index][3]) mm_die("context matrix differs");
    }

    bool hm_allowed = call_bounded(
        core, symbols.can_forget, MM_MOVE_SURF, 0, 0, 0).result == 1;
    bool form_rejected = call_bounded(
        core, symbols.can_forget, MM_MOVE_BEHEMOTH_BLADE, 0, 0, 0).result == 0
        && call_bounded(core, symbols.can_forget,
                        MM_MOVE_BEHEMOTH_BASH, 0, 0, 0).result == 0;
    bool secret_allowed = call_bounded(
        core, symbols.can_forget, MM_MOVE_SECRET_SWORD, 0, 0, 0).result == 1;

    uint16_t helper_moves[4] = {33, 45, 0, 0};
    mm_write_mon(core, 1, 20, helper_moves, (uint8_t)(2U << 2));
    write16(core, MM_VAR_8004, 0);
    write16(core, MM_VAR_8005, 1);
    call_bounded(core, symbols.selected_empty, 0, 0, 0, 0);
    bool empty_helper = read16(core, MM_RESULT) == 1;
    call_bounded(core, symbols.selected_pp, 0, 0, 0, 0);
    bool pp_helper = read16(core, MM_RESULT) == 1;
    write16(core, MM_VAR_8005, 0);
    call_bounded(core, symbols.selected_forget, 0, 0, 0, 0);
    bool forget_helper = read16(core, MM_RESULT) == 1;

    uint16_t delete_moves[4] = {
        MM_MOVE_SECRET_SWORD, 33, 45, MM_MOVE_SURF,
    };
    mm_write_mon(core, MM_SPECIES_KELDEO_RESOLUTE, 50, delete_moves, 0x1B);
    write16(core, MM_VAR_8004, 0);
    write16(core, MM_VAR_8005, 0);
    call_bounded(core, symbols.delete_selected, 0, 0, 0, 0);
    bool delete_path = read16(core, MM_RESULT) == 1
        && read16(core, MM_PARTY + MM_MON_SPECIES) == MM_SPECIES_KELDEO
        && read16(core, MM_PARTY + MM_MON_MOVES) == 33
        && read16(core, MM_PARTY + MM_MON_MOVES + 2U) == 45
        && read16(core, MM_PARTY + MM_MON_MOVES + 4U) == MM_MOVE_SURF
        && read16(core, MM_PARTY + MM_MON_MOVES + 6U) == 0
        && read8(core, MM_PARTY + MM_MON_PP_BONUSES) == 0x06;

    const uint8_t special_count[] = {0x25, 0xDF, 0x00};
    bool last_guard = mm_script_contains(
        core, symbols.forget_select_script, 160,
        special_count, sizeof(special_count));
    bool pp_guard = mm_script_has_native(
        core, symbols.forget_select_script, 160, symbols.selected_pp)
        && read8(core, symbols.pp_warning_script) == 0x0F;
    bool delete_script = mm_script_has_native(
        core, symbols.forget_delete_script, 64, symbols.delete_selected);
    bool form_guard = mm_script_has_native(
        core, symbols.forget_select_script, 160, symbols.selected_forget);
    if (!hm_allowed || !form_rejected || !secret_allowed || !empty_helper
        || !pp_helper || !forget_helper || !last_guard || !pp_guard
        || !delete_path || !delete_script || !form_guard || log_problem_count) {
        fprintf(stderr,
                "forget detail hm=%u form=%u secret=%u empty=%u pp=%u "
                "helper=%u last=%u ppguard=%u delete=%u script=%u "
                "formguard=%u result=%u species=%u moves=%u,%u,%u,%u "
                "bonuses=%u logs=%u\n",
                hm_allowed, form_rejected, secret_allowed, empty_helper,
                pp_helper, forget_helper, last_guard, pp_guard, delete_path,
                delete_script, form_guard, read16(core, MM_RESULT),
                read16(core, MM_PARTY + MM_MON_SPECIES),
                read16(core, MM_PARTY + MM_MON_MOVES),
                read16(core, MM_PARTY + MM_MON_MOVES + 2U),
                read16(core, MM_PARTY + MM_MON_MOVES + 4U),
                read16(core, MM_PARTY + MM_MON_MOVES + 6U),
                read8(core, MM_PARTY + MM_MON_PP_BONUSES),
                log_problem_count);
        mm_die("forget/helper/script fixture failed");
    }

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"move_memory_runtime_v1\","
           "\"rom_sha256\":\"%s\",\"read_only\":true,"
           "\"warnings_errors\":0,\"physical_patches\":{\"all_match\":true},"
           "\"normal\":{\"fixture_species\":%u,\"low_count\":%u,"
           "\"high_count\":%u,\"future_level_rejected\":true,"
           "\"level_zero_one_included\":true,"
           "\"known_and_duplicate_filtered\":true,\"candidate_cap\":40},"
           "\"egg\":{\"direct_count\":%u,\"adapter_count\":%u,"
           "\"direct_owner_match\":true,\"mode_reset\":true,"
           "\"policy_matrix_cases\":5},"
           "\"forget\":{\"last_move_script_guard\":true,"
           "\"pp_up_warning_script_guard\":true,\"hm_allowed\":true,"
           "\"form_only_rejected\":true,"
           "\"secret_sword_form_link_allowed\":true,"
           "\"set_mon_move_slot_native_path\":true},"
           "\"context\":{\"matrix_cases\":4,\"matrix_pass\":true},"
           "\"helpers\":{\"empty_slot\":true,\"pp_up\":true,"
           "\"selected_move\":true},\"artifacts_written\":[]}",
           rom_sha256, species, low_count, high_count,
           direct_egg_count, adapter_egg_count);
    putchar('\n');

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
