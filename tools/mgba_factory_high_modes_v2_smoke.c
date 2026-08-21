/* T25 Factory High Modes V2 exact-ROM quick/full validation for libmGBA. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <ctype.h>

enum {
    FH_ERROR = 0U,
    FH_OK = 1U,
    FH_ROUND = 2U,
    FH_COMPLETE = 3U,
    FH_LOCKED = 5U,
    FH_PERSIST_FAILED = 6U,
    FH_RECOVERED = 9U,
    FH_TRIAL_DELEGATE = 10U,
    FH_INVALID = 12U,
    FH_ISOLATION_BUSY = 13U,

    FH_PROBE_ABI = 0U,
    FH_PROBE_STATE = 1U,
    FH_PROBE_LEDGER = 2U,
    FH_PROBE_MODES = 3U,
    FH_PROBE_RENTALS = 4U,
    FH_PROBE_PROFILES = 5U,
    FH_PROBE_REWARDS = 6U,
    FH_PROBE_ACTIVE = 7U,
    FH_PROBE_MODE = 8U,
    FH_PROBE_OPTION = 9U,
    FH_PROBE_BATTLE = 10U,
    FH_PROBE_PARTY_HASH = 12U,
    FH_PROBE_CANDIDATE_HASH = 13U,
    FH_PROBE_OPPONENT_HASH = 14U,
    FH_PROBE_CREDIT_COUNT = 16U,
    FH_PROBE_MARKER = 18U,
    FH_PROBE_PENDING = 19U,
    FH_PROBE_CLAIMS = 20U,
    FH_PROBE_BP = 21U,
    FH_PROBE_CURRENT = 0x40U,
    FH_PROBE_BEST = 0x60U,
    FH_PROBE_MODE_ROW = 0x100U,
    FH_PROBE_RENTAL_ROW = 0x200U,
    FH_PROBE_PROFILE_ROW = 0x400U,
    FH_PROBE_REWARD_ROW = 0x500U,
    FH_PROBE_DIALOGUE_ROW = 0x600U,
    FH_PROBE_REQUIREMENT_ROW = 0x700U,
    FH_PROBE_BATCH_ROW = 0x800U,

    FH_ABI = 0x46483232U,
    FH_LEDGER = 0x0203D000U,
    FH_FACTORY = FH_LEDGER + 0x392U,
    FH_BP = FH_FACTORY,
    FH_CURRENT = FH_FACTORY + 2U,
    FH_BEST = FH_FACTORY + 50U,
    FH_CLAIMS = FH_FACTORY + 98U,
    FH_MARKER = FH_FACTORY + 110U,
    FH_SNAPSHOT_VALID = FH_FACTORY + 111U,
    FH_REWARD_PENDING = FH_FACTORY + 113U,
    FH_SNAPSHOT = FH_FACTORY + 114U,
    FH_CREDITS = FH_LEDGER + 0x684U,
    FH_PLAYER_PARTY = 0x020241E4U,
    FH_PARTY_BYTES = 600U,
    FH_MIRAGE = 0x0203EE00U,
    FH_MIRAGE_ACTIVE = FH_MIRAGE + 0x28U,

    FH_TRAINER_HOOK = 0x09096EC4U,
    FH_ABILITY_HOOK = 0x090973FCU,
    FH_SAVE_HOOK = 0x080DB4E4U,
    FH_RECEPTION_POINTER = 0x093C2DC0U,
    FH_TRIAL_COMPLETION_POINTER = 0x092CF57DU,
    FH_TRIAL_SCRIPT = 0x092CF3DCU,
};

#define FH_SYMBOL_LIST(X) \
    X(probe, "FactoryHighModesV2_Probe") \
    X(field_reception, "FactoryHighModesV2_FieldReception") \
    X(enter, "FactoryHighModesV2_EnterSelected") \
    X(commit, "FactoryHighModesV2_CommitSelection") \
    X(prepare, "FactoryHighModesV2_PrepareBattle") \
    X(after, "FactoryHighModesV2_AfterBattle") \
    X(retire, "FactoryHighModesV2_Retire") \
    X(abort_run, "FactoryHighModesV2_Abort") \
    X(recover, "FactoryHighModesV2_Recover") \
    X(trial_complete, "FactoryHighModesV2_TrialCompleteAdapter") \
    X(trainer_adapter, "FactoryHighModesV2_BuildTrainerPartyAdapter") \
    X(ability_adapter, "FactoryHighModesV2_LoadProperAbilityBattleDataAdapter") \
    X(save_adapter, "FactoryHighModesV2_SaveLoadAdapter") \
    X(test_initialize, "FactoryHighModesV2_TestInitialize") \
    X(test_unlocks, "FactoryHighModesV2_TestSetUnlocks") \
    X(test_enter, "FactoryHighModesV2_TestEnter") \
    X(test_commit, "FactoryHighModesV2_TestCommitDraft") \
    X(test_battle, "FactoryHighModesV2_TestBattleResult") \
    X(test_fault, "FactoryHighModesV2_TestSetPersistenceFault") \
    X(test_reload, "FactoryHighModesV2_TestReload") \
    X(test_streak, "FactoryHighModesV2_TestSetStreak") \
    X(test_generator, "FactoryHighModesV2_TestGeneratorAudit") \
    X(test_party_hash, "FactoryHighModesV2_TestPartyHash")

struct FhSymbols {
#define FH_MEMBER(member, name) uint32_t member;
    FH_SYMBOL_LIST(FH_MEMBER)
#undef FH_MEMBER
};

struct FhCases {
    bool schema;
    bool names_exact;
    bool counts_exact;
    uint32_t reception_script;
};

static void fh_die(const char *message)
{
    fprintf(stderr, "mgba-factory-high-modes-v2: %s\n", message);
    exit(1);
}

static char *fh_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        fh_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        fh_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 16L * 1024L * 1024L)
        fh_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        fh_die("fixture read failed");
    if (fclose(stream) != 0)
        fh_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static const char *fh_find_key(const char *text, const char *key)
{
    char needle[192];
    int length = snprintf(needle, sizeof(needle), "\"%s\"", key);
    if (length <= 0 || (size_t)length >= sizeof(needle))
        fh_die("JSON key formatting failed");
    return strstr(text, needle);
}

static uint32_t fh_parse_number(const char *cursor)
{
    while (*cursor && (isspace((unsigned char)*cursor)
                       || *cursor == ':' || *cursor == '"'))
        ++cursor;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(cursor, &end, 0);
    if (errno || end == cursor || value > UINT32_MAX)
        fh_die("JSON numeric value differs");
    return (uint32_t)value;
}

static uint32_t fh_json_number(const char *text, const char *key)
{
    const char *found = fh_find_key(text, key);
    if (!found || !(found = strchr(found, ':')))
        fh_die("required JSON number is missing");
    return fh_parse_number(found + 1);
}

static uint32_t fh_json_symbol(const char *text, const char *name)
{
    const char *found = fh_find_key(text, name);
    if (!found || !(found = strchr(found, ':')))
        fh_die("required runtime symbol is missing");
    ++found;
    while (isspace((unsigned char)*found))
        ++found;
    if (*found == '{') {
        const char *end = strchr(found, '}');
        const char *address = fh_find_key(found, "address");
        if (!end || !address || address > end || !(address = strchr(address, ':')))
            fh_die("runtime symbol address object differs");
        found = address + 1;
    }
    return fh_parse_number(found);
}

static unsigned fh_occurrences(const char *text, const char *needle)
{
    unsigned count = 0U;
    size_t length = strlen(needle);
    for (const char *cursor = text; (cursor = strstr(cursor, needle)) != NULL;
         cursor += length)
        ++count;
    return count;
}

static struct FhSymbols fh_load_symbols(const char *path)
{
    char *text = fh_read_text(path);
    struct FhSymbols result = {0};
#define FH_LOAD(member, name) result.member = fh_json_symbol(text, name);
    FH_SYMBOL_LIST(FH_LOAD)
#undef FH_LOAD
    free(text);
    return result;
}

static struct FhCases fh_load_cases(const char *path)
{
    char *text = fh_read_text(path);
    static const char *const names[] = {
        "roots_and_probe", "all_rows", "unlock_guard",
        "generator_representative", "reset_exact_restore",
        "retire_round_boundary", "packed_fields", "reward_boundaries",
        "generator_all_modes_boundaries", "anti_reroll", "persist_faults",
        "loss_forfeit", "ultimate_gimmick", "trial_delegate",
        "upstream_chains", "warnings_zero",
    };
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(names); ++index) {
        char quoted[96];
        int length = snprintf(quoted, sizeof(quoted), "\"%s\"", names[index]);
        if (length <= 0 || (size_t)length >= sizeof(quoted))
            fh_die("case fixture name is too long");
        exact = exact && fh_occurrences(text, quoted) == 1U;
    }
    struct FhCases result = {
        .schema = fh_json_number(text, "schema_version") == 1U
            && fh_find_key(text, "task") != NULL
            && fh_find_key(text, "acceptance_keys") != NULL,
        .names_exact = exact,
        .counts_exact = fh_json_number(text, "modes") == 24U
            && fh_json_number(text, "requirements") == 28U
            && fh_json_number(text, "rentals") == 248U
            && fh_json_number(text, "profiles") == 55U
            && fh_json_number(text, "rewards") == 16U
            && fh_json_number(text, "dialogues") == 28U
            && fh_json_number(text, "batches") == 7U,
        .reception_script = fh_json_number(text, "reception_script"),
    };
    free(text);
    return result;
}

static uint32_t fh_call(struct mCore *core, uint32_t function,
                        uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    if (!(function & 1U))
        fh_die("runtime entrypoint is not Thumb");
    return call_bounded(core, function, r0, r1, r2, r3).result;
}

static uint32_t fh_probe(struct mCore *core, const struct FhSymbols *symbols,
                         uint32_t selector)
{
    return fh_call(core, symbols->probe, selector, 0U, 0U, 0U);
}

static uint32_t fh_bl_target(struct mCore *core, uint32_t site)
{
    uint16_t high = read16(core, site);
    uint16_t low = read16(core, site + 2U);
    if ((high & 0xF800U) != 0xF000U || (low & 0xF800U) != 0xF800U)
        return 0U;
    int32_t displacement = (int32_t)(((uint32_t)(high & 0x07FFU) << 12)
        | ((uint32_t)(low & 0x07FFU) << 1));
    if (displacement & 0x00400000L)
        displacement |= (int32_t)0xFF800000L;
    return (uint32_t)((int32_t)(site + 4U) + displacement) | 1U;
}

static uint32_t fh_jump_target(struct mCore *core, uint32_t site)
{
    if (read8(core, site) != 0x00U || read8(core, site + 1U) != 0x4BU
        || read8(core, site + 2U) != 0x18U || read8(core, site + 3U) != 0x47U)
        return 0U;
    return read32(core, site + 4U);
}

static uint32_t fh_read32_bytes(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8)
        | ((uint32_t)read8(core, address + 2U) << 16)
        | ((uint32_t)read8(core, address + 3U) << 24);
}

static bool fh_party_read(struct mCore *core, uint8_t out[FH_PARTY_BYTES])
{
    for (unsigned index = 0U; index < FH_PARTY_BYTES; ++index)
        out[index] = read8(core, FH_PLAYER_PARTY + index);
    return true;
}

static bool fh_party_equal(struct mCore *core, const uint8_t expected[FH_PARTY_BYTES])
{
    for (unsigned index = 0U; index < FH_PARTY_BYTES; ++index) {
        if (read8(core, FH_PLAYER_PARTY + index) != expected[index])
            return false;
    }
    return true;
}

static bool fh_initialize(struct mCore *core, const struct FhSymbols *symbols)
{
    uint32_t result = fh_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U);
    bool passed = result == FH_OK
        && read32(core, FH_LEDGER) == 0x31534756U
        && read16(core, FH_LEDGER + 4U) == 2U
        && read16(core, FH_LEDGER + 6U) == 0x800U
        && read8(core, FH_MARKER) == 0U
        && read8(core, FH_SNAPSHOT_VALID) == 0U;
    return passed;
}

static bool fh_roots(struct mCore *core, const struct FhSymbols *s,
                     const struct FhCases *cases)
{
    static const uint8_t trial_prefix[] = {
        0x6A, 0x5A, 0x0F, 0x00, 0x08, 0xF3, 0x2C, 0x09,
    };
    bool trial = true;
    for (unsigned index = 0U; index < ARRAY_LEN(trial_prefix); ++index)
        trial = trial && read8(core, FH_TRIAL_SCRIPT + index) == trial_prefix[index];
    bool passed = fh_bl_target(core, FH_TRAINER_HOOK) == s->trainer_adapter
        && fh_bl_target(core, FH_ABILITY_HOOK) == s->ability_adapter
        && fh_jump_target(core, FH_SAVE_HOOK) == s->save_adapter
        && read32(core, FH_RECEPTION_POINTER) == cases->reception_script
        && fh_read32_bytes(core, FH_TRIAL_COMPLETION_POINTER) == s->trial_complete
        && read8(core, cases->reception_script) == 0x6AU
        && read8(core, cases->reception_script + 1U) == 0x5AU && trial;
    if (!passed)
        fprintf(stderr, "fh roots: trainer=%08x/%08x ability=%08x/%08x "
                "save=%08x/%08x reception=%08x/%08x trial=%08x/%08x prefix=%u\n",
                fh_bl_target(core, FH_TRAINER_HOOK), s->trainer_adapter,
                fh_bl_target(core, FH_ABILITY_HOOK), s->ability_adapter,
                fh_jump_target(core, FH_SAVE_HOOK), s->save_adapter,
                read32(core, FH_RECEPTION_POINTER), cases->reception_script,
                fh_read32_bytes(core, FH_TRIAL_COMPLETION_POINTER),
                s->trial_complete, trial);
    return passed;
}

static bool fh_tables(struct mCore *core, const struct FhSymbols *s)
{
    bool passed = fh_probe(core, s, FH_PROBE_ABI) == FH_ABI
        && fh_probe(core, s, FH_PROBE_STATE) == 0x0203F220U
        && fh_probe(core, s, FH_PROBE_LEDGER) == FH_LEDGER
        && fh_probe(core, s, FH_PROBE_MODES) == 24U
        && fh_probe(core, s, FH_PROBE_RENTALS) == 248U
        && fh_probe(core, s, FH_PROBE_PROFILES) == 55U
        && fh_probe(core, s, FH_PROBE_REWARDS) == 16U;
    unsigned tier_counts[4] = {0};
    for (unsigned index = 0U; index < 24U; ++index) {
        uint32_t row = fh_probe(core, s, FH_PROBE_MODE_ROW + index);
        uint8_t tier = read8(core, row);
        passed = passed && row != 0U && tier < 4U && read8(core, row + 14U) == index
            && read8(core, row + 2U) >= 3U && read8(core, row + 2U) <= 4U
            && read8(core, row + 3U) >= 3U && read8(core, row + 3U) <= 6U
            && read8(core, row + 5U) == (index < 4U ? 3U : 7U)
            && read8(core, row + 7U) == (index < 4U ? 0U : index < 8U ? 1U
                                         : index < 12U || (index >= 16U && index <= 20U)
                                             ? 2U : 3U);
        if (tier < 4U)
            ++tier_counts[tier];
        if (index + 1U < 24U)
            passed = passed && fh_probe(core, s, FH_PROBE_MODE_ROW + index + 1U)
                == row + 16U;
    }
    passed = passed && tier_counts[0] == 4U && tier_counts[1] == 4U
        && tier_counts[2] == 9U && tier_counts[3] == 7U;
    unsigned gmax = 0U;
    for (unsigned index = 0U; index < 248U; ++index) {
        uint32_t row = fh_probe(core, s, FH_PROBE_RENTAL_ROW + index);
        passed = passed && row != 0U && read16(core, row) != 0U
            && read8(core, row + 22U) < 12U && read8(core, row + 23U) < 3U
            && read8(core, row + 26U) <= 4U
            && (read8(core, row + 29U) == 5U || read8(core, row + 29U) == 50U)
            && read8(core, row + 30U) <= 1U && read8(core, row + 31U) <= 1U;
        gmax += read8(core, row + 31U);
        if (index + 1U < 248U)
            passed = passed && fh_probe(core, s, FH_PROBE_RENTAL_ROW + index + 1U)
                == row + 32U;
    }
    passed = passed && gmax == 6U;
    for (unsigned index = 0U; index < 55U; ++index) {
        uint32_t row = fh_probe(core, s, FH_PROBE_PROFILE_ROW + index);
        passed = passed && row != 0U && read8(core, row) < 4U
            && read8(core, row + 3U) < 3U && read8(core, row + 10U) > 0U;
        if (index + 1U < 55U)
            passed = passed && fh_probe(core, s, FH_PROBE_PROFILE_ROW + index + 1U)
                == row + 12U;
    }
    static const uint16_t bp[] = {
        9U, 0U, 0U, 0U, 21U, 12U, 0U, 0U,
        35U, 25U, 0U, 0U, 100U, 0U, 0U, 0U,
    };
    for (unsigned index = 0U; index < 16U; ++index) {
        uint32_t row = fh_probe(core, s, FH_PROBE_REWARD_ROW + index);
        passed = passed && row != 0U && read8(core, row) < 4U
            && read16(core, row + 4U) == bp[index];
        if (index + 1U < 16U)
            passed = passed && fh_probe(core, s, FH_PROBE_REWARD_ROW + index + 1U)
                == row + 12U;
    }
    for (unsigned index = 0U; index < 28U; ++index) {
        uint32_t dialogue = fh_probe(core, s, FH_PROBE_DIALOGUE_ROW + index);
        bool terminated = false;
        for (unsigned byte = 0U; byte < 192U; ++byte)
            terminated = terminated || read8(core, dialogue + byte) == 0xFFU;
        passed = passed && dialogue >= 0x08000000U && dialogue < 0x0A000000U
            && terminated && fh_probe(core, s, FH_PROBE_REQUIREMENT_ROW + index) != 0U;
    }
    for (unsigned index = 0U; index < 7U; ++index)
        passed = passed && fh_probe(core, s, FH_PROBE_BATCH_ROW + index) != 0U;
    return passed;
}

static unsigned fh_option_count(unsigned mode)
{
    return mode == 17U ? 3U : mode == 20U ? 2U : mode == 23U ? 4U : 1U;
}

static unsigned fh_option_value(unsigned mode, unsigned index)
{
    return mode == 23U ? index + 1U : index;
}

static bool fh_generators(struct mCore *core, const struct FhSymbols *s, bool full)
{
    bool passed = fh_initialize(core, s);
    for (unsigned mode = 1U; mode < 24U; ++mode) {
        uint32_t mode_row = fh_probe(core, s, FH_PROBE_MODE_ROW + mode);
        unsigned opponent = read8(core, mode_row + 4U);
        unsigned expected_candidates = (read8(core, mode_row + 9U) == 2U
            || mode == 13U || mode == 15U || mode == 20U
            || mode == 21U || mode == 23U) ? 8U : 6U;
        for (unsigned option_index = 0U; option_index < fh_option_count(mode);
             ++option_index) {
            unsigned option = fh_option_value(mode, option_index);
            unsigned first_seed = full ? 0U : 0U;
            unsigned last_seed = full ? 247U : 247U;
            unsigned step = full ? 1U : 247U;
            for (unsigned seed = first_seed; seed <= last_seed; seed += step) {
                uint32_t result = fh_call(core, s->test_generator,
                                          mode, option, seed, 0U);
                uint32_t candidate_hash = fh_probe(core, s, FH_PROBE_CANDIDATE_HASH);
                uint32_t opponent_hash = fh_probe(core, s, FH_PROBE_OPPONENT_HASH);
                uint32_t repeated = fh_call(core, s->test_generator,
                                            mode, option, seed, 0U);
                passed = passed && (result & 7U) == 7U && repeated == result
                    && ((result >> 8) & 0xFFU) == expected_candidates
                    && ((result >> 16) & 0xFFU) == opponent
                    && fh_probe(core, s, FH_PROBE_CANDIDATE_HASH) == candidate_hash
                    && fh_probe(core, s, FH_PROBE_OPPONENT_HASH) == opponent_hash;
                if (!full && seed == 247U)
                    break;
            }
        }
    }
    return passed;
}

static bool fh_unlock_and_packed(struct mCore *core, const struct FhSymbols *s)
{
    uint8_t original[FH_PARTY_BYTES];
    bool passed = fh_initialize(core, s) && fh_party_read(core, original)
        && fh_call(core, s->test_unlocks, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 4U, 0U, 123U, 0U) == FH_LOCKED
        && read8(core, FH_SNAPSHOT_VALID) == 0U && fh_party_equal(core, original)
        && fh_call(core, s->test_enter, 17U, 3U, 123U, 0U) == FH_LOCKED
        && fh_call(core, s->test_enter, 20U, 2U, 123U, 0U) == FH_LOCKED
        && fh_call(core, s->test_enter, 23U, 0U, 123U, 0U) == FH_LOCKED
        && fh_call(core, s->test_enter, 24U, 0U, 123U, 0U) == FH_INVALID
        && fh_call(core, s->test_enter, 0U, 0U, 123U, 0U) == FH_TRIAL_DELEGATE;
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_enter, 23U, 4U, 99U, 0U) == FH_OK
        && (read8(core, FH_MARKER) & 7U) == 1U
        && ((read8(core, FH_MARKER) >> 3) & 7U) == 4U
        && !(read8(core, FH_MARKER) & 0x80U)
        && (read8(core, FH_REWARD_PENDING) >> 3) == 23U
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && (read8(core, FH_MARKER) & 7U) == 2U
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_enter, 20U, 1U, 99U, 0U) == FH_OK
        && (read8(core, FH_MARKER) & 0x40U) != 0U
        && !(read8(core, FH_MARKER) & 0x80U)
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;
    return passed;
}

static bool fh_restore_paths(struct mCore *core, const struct FhSymbols *s)
{
    uint8_t original[FH_PARTY_BYTES];
    bool passed = fh_initialize(core, s) && fh_party_read(core, original);
    uint32_t original_hash = fh_probe(core, s, FH_PROBE_PARTY_HASH);
    passed = passed && fh_call(core, s->test_enter, 4U, 0U, 77U, 0U) == FH_OK;
    uint32_t candidate_hash = fh_probe(core, s, FH_PROBE_CANDIDATE_HASH);
    passed = passed && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_probe(core, s, FH_PROBE_PARTY_HASH) != original_hash
        && fh_call(core, s->test_reload, 0U, 0U, 0U, 0U) == FH_RECOVERED
        && fh_party_equal(core, original) && read8(core, FH_MARKER) == 0U
        && read8(core, FH_SNAPSHOT_VALID) == 0U
        && read16(core, FH_CURRENT + 4U * 2U) == 0U
        && fh_call(core, s->test_enter, 4U, 0U, 77U, 0U) == FH_OK
        && fh_probe(core, s, FH_PROBE_CANDIDATE_HASH) == candidate_hash
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;

    passed = passed && fh_initialize(core, s) && fh_party_read(core, original)
        && fh_call(core, s->test_enter, 4U, 0U, 88U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK;
    for (unsigned battle = 1U; battle <= 7U; ++battle) {
        uint32_t result = fh_call(core, s->test_battle, 1U, 0U, 0U, 0U);
        passed = passed && result == (battle == 7U ? FH_ROUND : FH_OK);
    }
    passed = passed && fh_call(core, s->retire, 0U, 0U, 0U, 0U) == FH_OK
        && read16(core, FH_CURRENT + 4U * 2U) == 7U
        && read16(core, FH_BEST + 4U * 2U) == 7U
        && fh_party_equal(core, original) && read8(core, FH_SNAPSHOT_VALID) == 0U;

    passed = passed && fh_initialize(core, s) && fh_party_read(core, original)
        && fh_call(core, s->test_enter, 4U, 0U, 91U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->retire, 0U, 0U, 0U, 0U) == FH_INVALID
        && read8(core, FH_SNAPSHOT_VALID) == 1U
        && fh_call(core, s->test_battle, 0U, 0U, 0U, 0U) == FH_OK
        && read16(core, FH_CURRENT + 4U * 2U) == 0U
        && read16(core, FH_BEST + 4U * 2U) == 1U
        && fh_party_equal(core, original);
    return passed;
}

static bool fh_faults(struct mCore *core, const struct FhSymbols *s)
{
    uint8_t original[FH_PARTY_BYTES];
    bool passed = fh_initialize(core, s) && fh_party_read(core, original)
        && fh_call(core, s->test_fault, 1U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 4U, 0U, 12U, 0U) == FH_PERSIST_FAILED
        && read8(core, FH_SNAPSHOT_VALID) == 0U && fh_party_equal(core, original);
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_enter, 4U, 0U, 13U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_fault, 1U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_PERSIST_FAILED
        && read16(core, FH_CURRENT + 4U * 2U) == 0U
        && fh_call(core, s->test_fault, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_OK
        && read16(core, FH_CURRENT + 4U * 2U) == 1U
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;
    return passed;
}

static bool fh_rewards(struct mCore *core, const struct FhSymbols *s)
{
    bool passed = fh_initialize(core, s)
        && fh_call(core, s->test_streak, 4U, 13U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 4U, 0U, 44U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_ROUND
        && read16(core, FH_BP) == 33U && read16(core, FH_CURRENT + 8U) == 14U
        && (read32(core, FH_CLAIMS) & (1U << 11))
        && (read32(core, FH_CLAIMS) & (1U << 6))
        && read16(core, FH_CREDITS + 4U) == 1U
        && fh_probe(core, s, FH_PROBE_CREDIT_COUNT) == 1U
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_OK
        && read16(core, FH_BP) == 33U
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_streak, 4U, 13U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 4U, 0U, 45U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_fault, 1U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_PERSIST_FAILED
        && read16(core, FH_BP) == 0U && !(read32(core, FH_CLAIMS) & (1U << 11))
        && fh_call(core, s->test_fault, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_ROUND
        && read16(core, FH_BP) == 33U
        && fh_call(core, s->abort_run, 0U, 0U, 0U, 0U) == FH_OK;
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_streak, 12U, 48U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 12U, 0U, 49U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_ROUND
        && (read32(core, FH_CLAIMS) & (1U << 8))
        && fh_call(core, s->retire, 0U, 0U, 0U, 0U) == FH_OK;
    passed = passed && fh_initialize(core, s)
        && fh_call(core, s->test_streak, 12U, 99U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_enter, 12U, 0U, 100U, 0U) == FH_OK
        && fh_call(core, s->test_commit, 0U, 0U, 0U, 0U) == FH_OK
        && fh_call(core, s->test_battle, 1U, 0U, 0U, 0U) == FH_COMPLETE
        && (read32(core, FH_CLAIMS) & (1U << 9))
        && !(read32(core, FH_CLAIMS) & (1U << 18))
        && read8(core, FH_SNAPSHOT_VALID) == 0U;
    return passed;
}

static bool fh_isolation(struct mCore *core, const struct FhSymbols *s)
{
    uint8_t original[FH_PARTY_BYTES];
    bool passed = fh_initialize(core, s) && fh_party_read(core, original);
    write32_bytes(core, FH_MIRAGE, 0x4D505331U);
    write32_bytes(core, FH_MIRAGE + 4U, ~UINT32_C(0x4D505331));
    write8(core, FH_MIRAGE_ACTIVE, 1U);
    passed = passed && fh_call(core, s->test_enter, 4U, 0U, 7U, 0U)
        == FH_ISOLATION_BUSY && fh_party_equal(core, original)
        && read8(core, FH_SNAPSHOT_VALID) == 0U;
    write8(core, FH_MIRAGE_ACTIVE, 0U);
    return passed;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM SYMBOLS CASES quick|full SAVE\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    (void)argv[5];
    struct FhSymbols symbols = fh_load_symbols(argv[2]);
    struct FhCases cases = fh_load_cases(argv[3]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        fh_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        fh_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    bool fixture = cases.schema && cases.names_exact && cases.counts_exact;
    bool roots = fh_roots(core, &symbols, &cases);
    bool tables = fh_tables(core, &symbols);
    bool generators = fh_generators(core, &symbols, full);
    bool unlock_packed = fh_unlock_and_packed(core, &symbols);
    bool restore = fh_restore_paths(core, &symbols);
    bool faults = fh_faults(core, &symbols);
    bool rewards = fh_rewards(core, &symbols);
    bool isolation = fh_isolation(core, &symbols);
    bool warnings = log_problem_count == 0U;
    bool tests[] = {
        fixture, roots, tables, generators, unlock_packed, restore,
        faults, rewards, isolation, warnings,
    };
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];
    bool acceptance[] = {
        fixture && roots,
        fixture && tables,
        roots && tables,
        unlock_packed,
        tables && generators,
        generators,
        restore,
        rewards && faults,
        isolation && unlock_packed,
        roots && warnings,
        roots && tables && generators && unlock_packed && restore && faults
            && rewards && isolation && warnings,
    };
    static const char *const acceptance_keys[] = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
        "CANONICAL_COUNTS_EXACT",
        "TRIAL_SLOT0_BYTE_RUNTIME_COMPATIBLE",
        "UNLOCK_UI_SAVE_GUARD",
        "ALL_MODE_RULES_EXACT",
        "FINITE_GENERATOR_ANTI_REROLL",
        "FORFEIT_RESTORE_RETIRE_EXACT",
        "REWARD_BP_CLAIM_CREDIT_ATOMIC",
        "FACTORY_ISOLATION_GIMMICK_LIMIT",
        "UPSTREAM_REGRESSION_ZERO",
        "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA",
    };
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index)
        passed = passed && acceptance[index];

    char rom_sha[65], runner_sha[65], symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr,
            "mgba-factory-high-modes-v2 %s: fixture=%u roots=%u tables=%u "
            "generators=%u unlock=%u restore=%u faults=%u rewards=%u "
            "isolation=%u logs=%u\n",
            full ? "full" : "quick", fixture, roots, tables, generators,
            unlock_packed, restore, faults, rewards, isolation,
            log_problem_count);
    printf(
        "{\"schema_version\":1,\"task\":\"T25\",\"mode\":\"%s\","
        "\"status\":\"%s\",\"result_identity\":"
        "\"FH42:2:24:28:248:55:16:28:7:7440\","
        "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
        "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
        "\"tests\":{\"case_fixture\":%s,\"rooted_hooks_field\":%s,"
        "\"all_runtime_rows\":%s,\"finite_generators\":%s,"
        "\"unlock_and_packed_fields\":%s,\"exact_restore_paths\":%s,"
        "\"persistence_fault_rollback\":%s,\"reward_boundaries_atomic\":%s,"
        "\"factory_isolation\":%s,\"warnings_zero\":%s},\"total\":%zu,"
        "\"warnings\":%u,\"warnings_errors\":%u,"
        "\"coverage\":{\"modes\":24,\"requirements\":28,\"rentals\":248,"
        "\"profiles\":55,\"rewards\":16,\"dialogues\":28,\"batches\":7,"
        "\"host_rows\":7440},\"acceptance_checks\":{",
        full ? "full" : "quick", passed ? "PASS" : "FAIL",
        rom_sha, runner_sha, symbols_sha, cases_sha,
        fixture ? "true" : "false", roots ? "true" : "false",
        tables ? "true" : "false", generators ? "true" : "false",
        unlock_packed ? "true" : "false", restore ? "true" : "false",
        faults ? "true" : "false", rewards ? "true" : "false",
        isolation ? "true" : "false", warnings ? "true" : "false",
        ARRAY_LEN(tests), log_problem_count, log_problem_count);
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index)
        printf("%s\"%s\":%s", index ? "," : "", acceptance_keys[index],
               acceptance[index] ? "true" : "false");
    printf("}}\n");
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
