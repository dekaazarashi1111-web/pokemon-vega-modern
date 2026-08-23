/* Exact-ROM quick/full validation for the final 1,302-battle ChangeKit. */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define FIRST_BATTLE_EMBEDDED
#include "mgba_first_battle_loop_smoke.c"

#include <errno.h>

enum {
    TCF_SAVE_SIZE = 128U * 1024U,
    TCF_TRY_SAVING_DATA = 0x080DB34D,
    TCF_LOAD_GAME_DATA = 0x080DB4E5,
    TCF_ACTIVE_BATTLER = 0x02023B24,
    TCF_BATTLER_PARTY_INDEXES = 0x02023B2E,
    TCF_ABSENT_BATTLER_FLAGS = 0x02023CD0,
    TCF_TRAINER_RECORD_SIZE = 32U,
    TCF_PARTY_MEMBER_SIZE = 16U,
    TCF_NATURE_MINT_OFFSET = 0x0FU,
    TCF_TERA_TYPE_OFFSET = 0x11U,
    TCF_EV_OFFSET = 0x38U,
    TCF_MET_BITS_OFFSET = 0x46U,
    TCF_IV_BITS_OFFSET = 0x48U,
    TCF_HIDDEN_ABILITY_MASK = 0x1000U,
    TCF_ABILITY_NUM_MASK = 0x80000000U,
    TCF_BATTLE_MON_ABILITY_OFFSET = 0x38U,
    TCF_BATTLE_TYPE_TRAINER = 0x00000008U,
    TCF_SCRIPT_CONTEXT1_SETUP = 0x080693A5U,
    TCF_SCRIPT_CONTEXT2_ENABLE = 0x08069201U,
    TCF_TRAINER_MESSAGE_CONTINUATION = 0x08192F09U,
    TCF_RUNTIME_STATE_STORAGE = 0x0203EDC0U,
    TCF_RUNTIME_STATE_PHASE_OFFSET = 17U,
    TCF_APPROACHING_TRAINER_ID = 0x03000F29U,
};

struct TcfCase {
    char encounter[48];
    char binding[16];
    uint32_t quick;
    uint32_t trainer;
    uint32_t slot;
    uint32_t party_size;
    uint32_t is_double;
    uint32_t species;
    uint32_t level;
    uint32_t held_item;
    uint32_t moves[4];
    uint32_t ability;
    uint32_t ability_native;
    uint32_t nature;
    uint32_t ability_mode;
    uint32_t iv;
    uint32_t evs[6];
    uint32_t command;
    uint32_t data;
    uint32_t source;
    uint32_t kind;
    uint32_t archive;
    uint32_t physical_flag;
    uint32_t gimmick;
    uint32_t gimmick_slot;
    uint32_t tera_type;
    uint32_t ai_flags;
    uint32_t trainer_items[4];
};

struct TcfSymbols {
    uint32_t probe, trainer_set, trainer_clear, trainer_has, rematch;
    uint32_t configure, build_party, select_archive, battle_begin, battle_end;
    uint32_t policy_begin, policy_end, save_adapter, ability_adapter;
    uint32_t can[5], mark[5];
    uint32_t table;
};

struct TcfCounts {
    uint32_t encounters, members, parties, direct_abilities;
    uint32_t doubles, kind8, rematches, gimmicks[5];
};

static struct mCore *tcf_log_core;

static void tcf_die(const char *message) {
    fprintf(stderr, "mgba-trainer-changekit-final: %s\n", message);
    exit(1);
}

static void tcf_log(struct mLogger *logger, int category,
                    enum mLogLevel level, const char *format, va_list args) {
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    ++log_problem_count;
    if (log_problem_count > 12U) return;
    fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32 ": ",
            mLogCategoryName(category), (unsigned)level,
            tcf_log_core ? (uint32_t)read_register(tcf_log_core, "pc") : 0U);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static uint32_t tcf_number(const char *text, const char *label) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value > UINT32_MAX) {
        fprintf(stderr, "invalid %s: %s\n", label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static void tcf_initialize_save(const char *path) {
    FILE *stream = fopen(path, "wb");
    if (!stream) tcf_die("save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    for (size_t done = 0; done < TCF_SAVE_SIZE; done += sizeof(block)) {
        if (fwrite(block, 1, sizeof(block), stream) != sizeof(block))
            tcf_die("save initialization failed");
    }
    if (fclose(stream) != 0) tcf_die("save close failed");
}

static struct mCore *tcf_open(const char *rom, const char *save) {
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom);
    if (!core || !core->init(core)) tcf_die("core initialization failed");
    if (!mCoreLoadFile(core, rom)) tcf_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save, false)) tcf_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    return core;
}

static void tcf_close(struct mCore *core) {
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
}

static bool tcf_repeated_iv(uint32_t bits, uint8_t expected) {
    for (unsigned index = 0; index < 6U; ++index)
        if (((bits >> (index * 5U)) & 31U) != expected) return false;
    return true;
}

static char *tcf_token(char **cursor) {
    char *value = *cursor;
    if (!value) tcf_die("fixture row is truncated");
    char *comma = strchr(value, ',');
    if (comma) {
        *comma = '\0';
        *cursor = comma + 1;
    } else {
        char *newline = strpbrk(value, "\r\n");
        if (newline) *newline = '\0';
        *cursor = NULL;
    }
    return value;
}

static struct TcfCase *tcf_load_cases(const char *path, size_t *count) {
    FILE *stream = fopen(path, "r");
    if (!stream) tcf_die("case fixture open failed");
    char line[4096];
    if (!fgets(line, sizeof(line), stream)) tcf_die("case fixture header missing");
    size_t used = 0, capacity = 1024;
    struct TcfCase *rows = calloc(capacity, sizeof(*rows));
    if (!rows) tcf_die("case allocation failed");
    while (fgets(line, sizeof(line), stream)) {
        if (used == capacity) {
            capacity *= 2U;
            rows = realloc(rows, capacity * sizeof(*rows));
            if (!rows) tcf_die("case reallocation failed");
        }
        struct TcfCase *row = &rows[used++];
        char *cursor = line;
#define TEXT(field) do { \
    const char *token = tcf_token(&cursor); \
    if (strlen(token) >= sizeof(row->field)) tcf_die("fixture text too long"); \
    strcpy(row->field, token); \
} while (0)
#define NUM(field) row->field = tcf_number(tcf_token(&cursor), #field)
        TEXT(encounter); TEXT(binding); NUM(quick); NUM(trainer); NUM(slot);
        NUM(party_size);
        row->is_double = strcmp(tcf_token(&cursor), "DOUBLE") == 0;
        NUM(species); NUM(level); NUM(held_item);
        NUM(moves[0]); NUM(moves[1]); NUM(moves[2]); NUM(moves[3]);
        NUM(ability); NUM(ability_native); NUM(nature); NUM(ability_mode);
        NUM(iv); NUM(evs[0]); NUM(evs[1]); NUM(evs[2]);
        NUM(evs[3]); NUM(evs[4]); NUM(evs[5]);
        NUM(command); NUM(data); NUM(source); NUM(kind); NUM(archive);
        NUM(physical_flag); NUM(gimmick); NUM(gimmick_slot); NUM(tera_type);
        NUM(ai_flags); NUM(trainer_items[0]); NUM(trainer_items[1]);
        NUM(trainer_items[2]); NUM(trainer_items[3]);
        if (cursor != NULL && *cursor != '\0') tcf_die("fixture row has extra fields");
#undef NUM
#undef TEXT
    }
    if (fclose(stream) != 0) tcf_die("case fixture close failed");
    if (used != 6490U) tcf_die("case fixture member count differs");
    *count = used;
    return rows;
}

static uint32_t tcf_decode_bl_target(struct mCore *core, uint32_t site) {
    uint16_t first = read16(core, site);
    uint16_t second = read16(core, site + 2U);
    if ((first & 0xF800U) != 0xF000U || (second & 0xF800U) != 0xF800U)
        return 0U;
    int32_t delta = (int32_t)(((first & 0x7FFU) << 12)
        | ((second & 0x7FFU) << 1));
    if (delta & 0x00400000) delta |= (int32_t)0xFF800000;
    return (uint32_t)((int32_t)(site + 4U) + delta) | 1U;
}

static bool tcf_hook_contract(struct mCore *core, const struct TcfSymbols *s) {
    const uint32_t jump_sites[][2] = {
        {0x0807F948U, s->configure},
        {0x090DD2A4U, s->build_party},
        {0x080DB4E4U, s->save_adapter},
    };
    for (unsigned index = 0; index < ARRAY_LEN(jump_sites); ++index) {
        uint32_t site = jump_sites[index][0];
        if (read16(core, site) != 0x4B00U || read16(core, site + 2U) != 0x4718U
            || read32(core, site + 4U) != jump_sites[index][1]) return false;
    }
    if (tcf_decode_bl_target(core, 0x090CDBACU) != s->policy_begin
        || tcf_decode_bl_target(core, 0x090F6FC4U) != s->policy_end
        || tcf_decode_bl_target(core, 0x090973FCU) != s->ability_adapter)
        return false;
    const uint32_t can_sites[5] = {0U, 0x090D04AEU, 0x0912C2D8U,
                                   0x090F1546U, 0x091304A2U};
    const uint32_t mark_sites[5] = {0U, 0x090CED36U, 0x090BE838U,
                                    0x090CF04CU, 0x090CEF2CU};
    for (unsigned mode = 1; mode <= 4U; ++mode) {
        if (tcf_decode_bl_target(core, can_sites[mode]) != s->can[mode]
            || tcf_decode_bl_target(core, mark_sites[mode]) != s->mark[mode])
            return false;
    }
    return true;
}

static bool tcf_probe_contract(struct mCore *core, const struct TcfSymbols *s) {
    const uint32_t expected[] = {
        0x54434631U, 1302U, 6490U, 227U, 372U,
        4284U, 1302U, 71U, 1302U,
    };
    for (unsigned selector = 0; selector < ARRAY_LEN(expected); ++selector)
        if (call_preserving(core, s->probe, selector, 0, 0, 0) != expected[selector])
            return false;
    return true;
}

static bool tcf_selected(const struct TcfCase *row, bool full) {
    return full || row->quick != 0U;
}

static bool tcf_binding_checks(struct mCore *core, const struct TcfCase *rows,
                               size_t count, bool full,
                               const struct TcfSymbols *s,
                               struct TcfCounts *seen) {
    bool passed = true;
    for (size_t index = 0; index < count;) {
        size_t next = index + 1U;
        while (next < count && rows[next].trainer == rows[index].trainer) ++next;
        const struct TcfCase *row = &rows[index];
        if (tcf_selected(row, full)) {
            ++seen->encounters;
            if (row->is_double) ++seen->doubles;
            if (row->kind == 8U) ++seen->kind8;
            if (row->kind == 5U || row->kind == 7U) ++seen->rematches;
            if (read8(core, row->command) != 0x5CU
                || read8(core, row->data) != row->kind
                || read8(core, row->data + 1U) != (row->source & 0xFFU)
                || read8(core, row->data + 2U) != (row->source >> 8)) {
                fprintf(stderr, "binding bytes fail: %s\n", row->encounter);
                passed = false;
            }
            if (row->archive
                && call_preserving(core, s->select_archive, row->archive, 0, 0, 0) != 1U) {
                fprintf(stderr, "archive selection fail: %s\n", row->encounter);
                passed = false;
            }
            write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 0U);
            (void)call_preserving(core, s->configure, row->data, 0, 0, 0);
            if (read16(core, BATTLE_CORE_TRAINER_OPPONENT_A) != row->trainer) {
                fprintf(stderr, "binding target fail: %s expected=%u actual=%u\n",
                        row->encounter, (unsigned)row->trainer,
                        read16(core, BATTLE_CORE_TRAINER_OPPONENT_A));
                passed = false;
            }
            (void)call_preserving(core, s->battle_end, 2U, 0, 0, 0);
        }
        index = next;
    }
    return passed;
}

static bool tcf_member_matches(struct mCore *core, const struct TcfCase *row) {
    uint32_t mon = ADDR_ENEMY_PARTY + row->slot * POKEMON_SIZE;
    uint32_t species = call_preserving(core, BATTLE_CORE_GET_MON_DATA, mon, 11U, 0, 0);
    uint32_t level = call_preserving(core, BATTLE_CORE_GET_MON_DATA, mon, 56U, 0, 0);
    uint32_t item = call_preserving(core, BATTLE_CORE_GET_MON_DATA, mon, 12U, 0, 0);
    uint32_t moves[4];
    for (unsigned move = 0; move < 4U; ++move)
        moves[move] = call_preserving(
            core, BATTLE_CORE_GET_MON_DATA, mon, 13U + move, 0, 0);
    uint8_t nature = read8(core, mon + TCF_NATURE_MINT_OFFSET);
    uint32_t raw_iv = read32(core, mon + TCF_IV_BITS_OFFSET);
    uint32_t iv_bits = read32(core, mon + TCF_IV_BITS_OFFSET);
    uint16_t met_bits = read16(core, mon + TCF_MET_BITS_OFFSET);
    bool passed = species == row->species && level == row->level
        && item == row->held_item && nature == row->nature + 1U
        && tcf_repeated_iv(raw_iv, (uint8_t)row->iv)
        && ((iv_bits & TCF_ABILITY_NUM_MASK) != 0U) == (row->ability_mode == 1U)
        && ((met_bits & TCF_HIDDEN_ABILITY_MASK) != 0U) == (row->ability_mode == 2U);
    for (unsigned move = 0; move < 4U; ++move)
        if (moves[move] != row->moves[move]) passed = false;
    for (unsigned ev = 0; ev < 6U; ++ev)
        if (read8(core, mon + TCF_EV_OFFSET + ev) != row->evs[ev]) passed = false;
    if (!passed) {
        fprintf(stderr,
            "member actual %s[%u]: species=%u/%u level=%u/%u item=%u/%u "
            "moves=%u,%u,%u,%u/%u,%u,%u,%u nature=%u/%u iv=%08" PRIx32
            "/%u mode=%u/%u ev=%u,%u,%u,%u,%u,%u/%u,%u,%u,%u,%u,%u\n",
            row->encounter, (unsigned)row->slot,
            (unsigned)species, (unsigned)row->species,
            (unsigned)level, (unsigned)row->level,
            (unsigned)item, (unsigned)row->held_item,
            (unsigned)moves[0], (unsigned)moves[1], (unsigned)moves[2], (unsigned)moves[3],
            (unsigned)row->moves[0], (unsigned)row->moves[1],
            (unsigned)row->moves[2], (unsigned)row->moves[3],
            nature, (unsigned)(row->nature + 1U), raw_iv, (unsigned)row->iv,
            (unsigned)((iv_bits & TCF_ABILITY_NUM_MASK) ? 1U
                       : ((met_bits & TCF_HIDDEN_ABILITY_MASK) ? 2U : 0U)),
            (unsigned)row->ability_mode,
            read8(core, mon + TCF_EV_OFFSET), read8(core, mon + TCF_EV_OFFSET + 1U),
            read8(core, mon + TCF_EV_OFFSET + 2U), read8(core, mon + TCF_EV_OFFSET + 3U),
            read8(core, mon + TCF_EV_OFFSET + 4U), read8(core, mon + TCF_EV_OFFSET + 5U),
            (unsigned)row->evs[0], (unsigned)row->evs[1], (unsigned)row->evs[2],
            (unsigned)row->evs[3], (unsigned)row->evs[4], (unsigned)row->evs[5]);
    }
    return passed;
}

static void tcf_start_trainer_fixture(
    struct mCore *core,
    const struct Snapshot *field,
    const struct TcfCase *row,
    const struct TcfSymbols *s
) {
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    create_mon(core, ADDR_PLAYER_PARTY, 7U, 20U);
    if (row->is_double)
        create_mon(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, 4U, 20U);
    write8(core, ADDR_PLAYER_PARTY_COUNT, row->is_double ? 2U : 1U);
    if (row->archive)
        (void)call_preserving(core, s->select_archive, row->archive, 0, 0, 0);
    (void)call_preserving(core, s->configure, row->data, 0, 0, 0);
    /* The production wrapper is the synchronous boundary actually patched
     * into CreateNPCTrainerParty's caller.  Exercising it directly avoids
     * pretending that a bare StartTrainerBattle call supplies the speech and
     * continuation state owned by kinds 4/6/7/8.  The real kind-4 scheduler
     * route is covered separately below. */
    write32_bytes(core, ADDR_BATTLE_TYPE_FLAGS,
                  TCF_BATTLE_TYPE_TRAINER
                      | (row->is_double ? BATTLE_TYPE_DOUBLE : 0U));
    write16(core, BATTLE_CORE_TRAINER_MODE, 0U);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, (uint16_t)row->trainer);
    (void)call_preserving(core, s->build_party, 0, 0, 0, 0);
}

static bool tcf_start_live_trainer_fixture(
    struct mCore *core,
    const struct Snapshot *field,
    const struct TcfCase *row,
    const struct TcfSymbols *s
) {
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    create_mon(core, ADDR_PLAYER_PARTY, 7U, 20U);
    if (row->is_double)
        create_mon(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, 4U, 20U);
    write8(core, ADDR_PLAYER_PARTY_COUNT, row->is_double ? 2U : 1U);
    (void)call_preserving(core, s->trainer_clear, row->trainer, 0, 0, 0);
    if (row->archive
        && call_preserving(core, s->select_archive,
                           row->archive, 0, 0, 0) != 1U)
        return false;
    write8(core, TCF_APPROACHING_TRAINER_ID, row->is_double ? 2U : 0U);
    /* Run the generated trainerbattle opcode through the same script-engine
     * boundary used by map objects.  Calling ConfigureTrainerBattle followed
     * by StartTrainerBattle is not equivalent: kinds 3/4/6/7/8 also own
     * speech, continuation and scheduler state at the opcode boundary. */
    if (row->is_double) {
        uint32_t battle_script = call_preserving(
            core, s->configure, row->data, 0, 0, 0);
        if (battle_script < 0x08000000U || battle_script >= 0x0A000000U)
            return false;
        /* Stock kind-4/6/7/8 setup returns a battle script, while the field
         * command advances through the trainer-message continuation before
         * the scheduled battle starts.  This is the reviewed Stage 31--34
         * production scheduler route, now reached through the final hook. */
        (void)call_preserving(core, TCF_SCRIPT_CONTEXT2_ENABLE, 0, 0, 0, 0);
        (void)call_preserving(core, TCF_SCRIPT_CONTEXT1_SETUP,
                              TCF_TRAINER_MESSAGE_CONTINUATION, 0, 0, 0);
    } else {
        (void)call_preserving(core, TCF_SCRIPT_CONTEXT1_SETUP,
                              row->command, 0, 0, 0);
    }

    uint32_t observed_flags = 0U;
    uint32_t observed_phase = 0U;
    uint8_t observed_battlers = 0U;
    uint8_t observed_party_count = 0U;
    for (unsigned press = 0; press < 160U; ++press) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 30U);
        observed_flags |= read32(core, ADDR_BATTLE_TYPE_FLAGS);
        uint8_t battlers = read8(core, ADDR_BATTLERS_COUNT);
        if (battlers > observed_battlers) observed_battlers = battlers;
        uint8_t party_count = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT);
        if (party_count > observed_party_count)
            observed_party_count = party_count;
        observed_phase = read8(
            core, TCF_RUNTIME_STATE_STORAGE + TCF_RUNTIME_STATE_PHASE_OFFSET);
        if (observed_phase == 2U
            && (observed_flags & TCF_BATTLE_TYPE_TRAINER) != 0U
            && observed_battlers == (row->is_double ? 4U : 2U)
            && (!row->is_double
                || (observed_flags & BATTLE_TYPE_DOUBLE) != 0U))
            return tcf_member_matches(core, row);
    }
    fprintf(stderr, "live fixture fail: %s command=%08x mode=%u opponent=%u "
            "phase=%u flags=%08x battlers=%u party_runtime=%u/table=%u\n",
            row->encounter, row->command,
            (unsigned)read16(core, BATTLE_CORE_TRAINER_MODE),
            (unsigned)read16(core, BATTLE_CORE_TRAINER_OPPONENT_A),
            (unsigned)observed_phase, (unsigned)observed_flags,
            (unsigned)observed_battlers, (unsigned)observed_party_count,
            (unsigned)row->party_size);
    fprintf(stderr, "live policy state: probe_phase=%u current=%u dispatch=%u "
            "policy_failures=%u\n",
            (unsigned)call_preserving(core, s->probe, 9U, 0, 0, 0),
            (unsigned)call_preserving(core, s->probe, 12U, 0, 0, 0),
            (unsigned)call_preserving(core, s->probe, 13U, 0, 0, 0),
            (unsigned)call_preserving(core, s->probe, 11U, 0, 0, 0));
    return false;
}

static bool tcf_party_checks(struct mCore *core, const struct TcfCase *rows,
                             size_t count, bool full,
                             const struct Snapshot *field,
                             const struct TcfSymbols *s,
                             struct TcfCounts *seen) {
    bool passed = true;
    for (size_t index = 0; index < count;) {
        size_t next = index + 1U;
        while (next < count && rows[next].trainer == rows[index].trainer) ++next;
        const struct TcfCase *first = &rows[index];
        if (tcf_selected(first, full)) {
            ++seen->parties;
            uint32_t record = s->table + first->trainer * TCF_TRAINER_RECORD_SIZE;
            if (read8(core, record) != 3U
                || read8(core, record + 0x12U) != first->is_double
                || read32(core, record + 0x14U) != first->ai_flags
                || read8(core, record + 0x18U) != first->party_size) {
                fprintf(stderr, "trainer record fail: %s flags=%u double=%u/%u "
                        "ai=%u/%u size=%u/%u\n", first->encounter,
                        (unsigned)read8(core, record),
                        (unsigned)read8(core, record + 0x12U),
                        (unsigned)first->is_double,
                        (unsigned)read32(core, record + 0x14U),
                        (unsigned)first->ai_flags,
                        (unsigned)read8(core, record + 0x18U),
                        (unsigned)first->party_size);
                passed = false;
            }
            for (unsigned item = 0; item < 4U; ++item)
                if (read16(core, record + 0x0AU + item * 2U)
                    != first->trainer_items[item]) passed = false;
            uint32_t pointer = read32(core, record + 0x1CU);
            if (pointer < 0x08000000U || pointer >= 0x0A000000U) passed = false;

            tcf_start_trainer_fixture(core, field, first, s);
            for (size_t member = index; member < next; ++member) {
                ++seen->members;
                if (!tcf_member_matches(core, &rows[member])) {
                    fprintf(stderr, "party member fail: %s slot=%u\n",
                            rows[member].encounter, (unsigned)rows[member].slot);
                    passed = false;
                }
            }
        }
        index = next;
    }
    return passed;
}

static bool tcf_ability_checks(struct mCore *core, const struct TcfCase *rows,
                               size_t count, bool full,
                               const struct Snapshot *field,
                               const struct TcfSymbols *s,
                               struct TcfCounts *seen) {
    bool passed = true;
    for (size_t index = 0; index < count; ++index) {
        const struct TcfCase *row = &rows[index];
        if (!tcf_selected(row, full) || row->ability_native || row->ability == 0U)
            continue;
        ++seen->direct_abilities;
        tcf_start_trainer_fixture(core, field, row, s);
        write32_bytes(core, ADDR_BATTLE_TYPE_FLAGS, TCF_BATTLE_TYPE_TRAINER);
        write8(core, ADDR_BATTLERS_COUNT, 2U);
        write8(core, TCF_ABSENT_BATTLER_FLAGS, 0U);
        write16(core, TCF_BATTLER_PARTY_INDEXES + 2U, (uint16_t)row->slot);
        write8(core, TCF_ACTIVE_BATTLER, 1U);
        (void)call_preserving(core, s->ability_adapter, 0, 0, 0, 0);
        uint16_t actual = read16(core,
            ADDR_BATTLE_MONS + BATTLE_MON_SIZE + TCF_BATTLE_MON_ABILITY_OFFSET);
        if (actual != row->ability) {
            fprintf(stderr, "direct ability fail: %s slot=%u expected=%u actual=%u "
                    "phase=%u current=%u dispatch=%u policy_failures=%u\n",
                    row->encounter, (unsigned)row->slot,
                    (unsigned)row->ability, actual,
                    (unsigned)call_preserving(core, s->probe, 9U, 0, 0, 0),
                    (unsigned)call_preserving(core, s->probe, 12U, 0, 0, 0),
                    (unsigned)call_preserving(core, s->probe, 13U, 0, 0, 0),
                    (unsigned)call_preserving(core, s->probe, 11U, 0, 0, 0));
            passed = false;
        }
        (void)call_preserving(core, s->battle_end, 2U, 0, 0, 0);
    }
    return passed;
}

static bool tcf_gimmick_checks(struct mCore *core, const struct TcfCase *rows,
                               size_t count, bool full,
                               const struct Snapshot *field,
                               const struct TcfSymbols *s,
                               struct TcfCounts *seen) {
    bool passed = true;
    bool exercised[5] = {false, false, false, false, false};
    for (size_t index = 0; index < count;) {
        size_t next = index + 1U;
        while (next < count && rows[next].trainer == rows[index].trainer) ++next;
        const struct TcfCase *row = &rows[index];
        if (tcf_selected(row, full) && row->gimmick != 0U) {
            ++seen->gimmicks[row->gimmick];
            if (exercised[row->gimmick]) {
                index = next;
                continue;
            }
            exercised[row->gimmick] = true;
            uint8_t tera_before = 0U;
            if (row->gimmick == 4U) {
                tcf_start_trainer_fixture(core, field, row, s);
                tera_before = read8(core,
                    ADDR_ENEMY_PARTY + row->gimmick_slot * POKEMON_SIZE
                    + TCF_TERA_TYPE_OFFSET);
            }
            bool live = tcf_start_live_trainer_fixture(core, field, row, s);
            write8(core, ADDR_BATTLERS_COUNT, 2U);
            write8(core, TCF_ABSENT_BATTLER_FLAGS, 0U);
            write16(core, TCF_BATTLER_PARTY_INDEXES + 2U,
                    (uint16_t)row->gimmick_slot);
            uint32_t phase = call_preserving(core, s->probe, 9U, 0, 0, 0);
            if (!live || phase != 2U
                || call_preserving(core, s->can[row->gimmick], 1U, 1U, 0, 0) != 1U
                || call_preserving(core, s->mark[row->gimmick], 1U, 0, 0, 0) != 1U
                || call_preserving(core, s->can[row->gimmick], 1U, 1U, 0, 0) != 0U) {
                fprintf(stderr, "gimmick activation fail: %s mode=%u phase=%u "
                        "current=%u dispatch=%u policy_failures=%u\n",
                        row->encounter, (unsigned)row->gimmick,
                        (unsigned)call_preserving(core, s->probe, 9U, 0, 0, 0),
                        (unsigned)call_preserving(core, s->probe, 12U, 0, 0, 0),
                        (unsigned)call_preserving(core, s->probe, 13U, 0, 0, 0),
                        (unsigned)call_preserving(core, s->probe, 11U, 0, 0, 0));
                passed = false;
            }
            uint8_t tera_active = read8(core,
                ADDR_ENEMY_PARTY + row->gimmick_slot * POKEMON_SIZE
                + TCF_TERA_TYPE_OFFSET);
            if (row->gimmick == 4U && tera_active != row->tera_type) {
                fprintf(stderr, "gimmick Tera apply fail: %s before=%u "
                        "active=%u expected=%u\n",
                        row->encounter, tera_before, tera_active,
                        (unsigned)row->tera_type);
                passed = false;
            }
            /* VegaBattlePolicyEnd's production return register is not an ABI
             * result; the caller ignores it.  Cleanup is proven by the
             * runtime phase and the authored Tera byte restoration below. */
            (void)call_preserving(core, s->policy_end, 0, 0, 0, 0);
            uint8_t tera_after = read8(core,
                ADDR_ENEMY_PARTY + row->gimmick_slot * POKEMON_SIZE
                + TCF_TERA_TYPE_OFFSET);
            uint32_t cleanup_phase = call_preserving(
                core, s->probe, 9U, 0, 0, 0);
            if ((row->gimmick == 4U && tera_after != tera_before)
                || cleanup_phase != 0U) {
                fprintf(stderr, "gimmick cleanup fail: %s mode=%u phase=%u "
                        "tera=%u/%u\n", row->encounter,
                        (unsigned)row->gimmick, (unsigned)cleanup_phase,
                        tera_after, tera_before);
                passed = false;
            }
        }
        index = next;
    }
    return passed;
}

static bool tcf_double_entry(struct mCore *core, const struct Snapshot *field,
                             const struct TcfCase *rows, size_t count,
                             bool full, const struct TcfSymbols *s) {
    const struct TcfCase *chosen[2] = {NULL, NULL};
    for (size_t index = 0; index < count; ++index) {
        if (!tcf_selected(&rows[index], full) || !rows[index].is_double)
            continue;
        if (rows[index].kind == 4U && chosen[0] == NULL)
            chosen[0] = &rows[index];
        if (rows[index].kind == 8U && chosen[1] == NULL)
            chosen[1] = &rows[index];
    }
    if (!chosen[0] || !chosen[1]) return false;
    for (unsigned route = 0; route < 2U; ++route) {
        if (!tcf_start_live_trainer_fixture(core, field, chosen[route], s)
            || (read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_DOUBLE) == 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 4U
            || call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                               ADDR_ENEMY_PARTY, 11U, 0, 0)
                != chosen[route]->species)
            return false;
        (void)call_preserving(core, s->policy_end, 0, 0, 0, 0);
    }
    return true;
}

static const struct TcfCase *tcf_saved_case(const struct TcfCase *rows,
                                             size_t count, bool full) {
    for (size_t index = count; index-- > 0;)
        if (tcf_selected(&rows[index], full)) return &rows[index];
    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 28) {
        fprintf(stderr, "usage: %s ROM SAVE CASES quick|full 23_SYMBOLS\n", argv[0]);
        return 2;
    }
    bool full = strcmp(argv[4], "full") == 0;
    if (!full && strcmp(argv[4], "quick") != 0) return 2;
    struct TcfSymbols s = {0};
    unsigned arg = 5U;
    s.probe = tcf_number(argv[arg++], "probe");
    s.trainer_set = tcf_number(argv[arg++], "trainer_set");
    s.trainer_clear = tcf_number(argv[arg++], "trainer_clear");
    s.trainer_has = tcf_number(argv[arg++], "trainer_has");
    s.rematch = tcf_number(argv[arg++], "rematch");
    s.configure = tcf_number(argv[arg++], "configure");
    s.build_party = tcf_number(argv[arg++], "build_party");
    s.select_archive = tcf_number(argv[arg++], "select_archive");
    s.battle_begin = tcf_number(argv[arg++], "battle_begin");
    s.battle_end = tcf_number(argv[arg++], "battle_end");
    s.policy_begin = tcf_number(argv[arg++], "policy_begin");
    s.policy_end = tcf_number(argv[arg++], "policy_end");
    s.save_adapter = tcf_number(argv[arg++], "save_adapter");
    s.ability_adapter = tcf_number(argv[arg++], "ability_adapter");
    for (unsigned mode = 1; mode <= 4U; ++mode) {
        s.can[mode] = tcf_number(argv[arg++], "can");
        s.mark[mode] = tcf_number(argv[arg++], "mark");
    }
    s.table = tcf_number(argv[arg++], "table");
    if (arg != (unsigned)argc) return 2;

    size_t case_count = 0;
    struct TcfCase *cases = tcf_load_cases(argv[3], &case_count);
    tcf_initialize_save(argv[2]);
    struct mLogger logger = {.log = tcf_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = tcf_open(argv[1], argv[2]);
    tcf_log_core = core;
    run_trace_prefix(core);
    if (log_problem_count) tcf_die("field boot emitted warnings/errors");
    struct Snapshot field = take_snapshot(core);
    struct TcfCounts seen = {0};

    bool probe = tcf_probe_contract(core, &s);
    bool hooks = tcf_hook_contract(core, &s);
    bool bindings = tcf_binding_checks(core, cases, case_count, full, &s, &seen);
    bool parties = tcf_party_checks(core, cases, case_count, full, &field, &s, &seen);
    bool abilities = tcf_ability_checks(core, cases, case_count, full, &field, &s, &seen);
    bool gimmicks = tcf_gimmick_checks(core, cases, case_count, full, &field, &s, &seen);
    bool double_entry = tcf_double_entry(core, &field, cases, case_count, full, &s);

    restore_snapshot(core, &field);
    const struct TcfCase *saved = tcf_saved_case(cases, case_count, full);
    if (!saved) tcf_die("save case missing");
    (void)call_preserving(core, s.trainer_clear, saved->trainer, 0, 0, 0);
    (void)call_preserving(core, s.trainer_set, saved->trainer, 0, 0, 0);
    bool save_write = call_preserving(core, TCF_TRY_SAVING_DATA, 0, 0, 0, 0) == 1U;
    free(field.bytes);
    tcf_close(core);

    core = tcf_open(argv[1], argv[2]);
    tcf_log_core = core;
    run_key_frames(core, 0, 180U);
    bool load_ok = call_preserving(core, TCF_LOAD_GAME_DATA, 0, 0, 0, 0) == 1U;
    bool save_reload = save_write && load_ok
        && call_preserving(core, s.trainer_has, saved->trainer, 0, 0, 0) == 1U
        && call_preserving(core, s.probe, 9U, 0, 0, 0) == 0U;
    tcf_close(core);

    uint32_t expected_encounters = full ? 1302U : 0U;
    uint32_t expected_members = full ? 6490U : 0U;
    if (!full) {
        for (size_t index = 0; index < case_count;) {
            size_t next = index + 1U;
            while (next < case_count && cases[next].trainer == cases[index].trainer) ++next;
            if (cases[index].quick) {
                ++expected_encounters;
                expected_members += (uint32_t)(next - index);
            }
            index = next;
        }
    }
    bool counts = seen.encounters == expected_encounters
        && seen.parties == expected_encounters && seen.members == expected_members
        && (!full || (seen.direct_abilities == 924U && seen.doubles == 74U
                      && seen.kind8 == 3U && seen.rematches == 227U
                      && seen.gimmicks[1] == 86U && seen.gimmicks[2] == 111U
                      && seen.gimmicks[3] == 4U && seen.gimmicks[4] == 67U));

    fprintf(stderr,
        "mgba-trainer-changekit-final %s: probe=%s hooks=%s bindings=%s "
        "parties=%s abilities=%s gimmicks=%s double=%s save_reload=%s counts=%s "
        "encounters=%u members=%u direct_abilities=%u warnings_errors=%u\n",
        full ? "full" : "quick", probe ? "PASS" : "FAIL", hooks ? "PASS" : "FAIL",
        bindings ? "PASS" : "FAIL", parties ? "PASS" : "FAIL",
        abilities ? "PASS" : "FAIL", gimmicks ? "PASS" : "FAIL",
        double_entry ? "PASS" : "FAIL", save_reload ? "PASS" : "FAIL",
        counts ? "PASS" : "FAIL", seen.encounters, seen.members,
        seen.direct_abilities, log_problem_count);

    bool passed = probe && hooks && bindings && parties && abilities && gimmicks
        && double_entry && save_reload && counts && log_problem_count == 0U;
    printf("{\"schema_version\":1,\"status\":\"%s\",\"mode\":\"%s\","
           "\"checks\":{\"probe\":%s,\"hooks\":%s,\"bindings\":%s,"
           "\"parties_members\":%s,\"direct_abilities\":%s,"
           "\"gimmick_ai\":%s,\"double_entry\":%s,\"save_reload\":%s,"
           "\"coverage_counts\":%s},\"coverage\":{\"encounters\":%u,"
           "\"members\":%u,\"direct_abilities\":%u,\"doubles\":%u,"
           "\"kind8\":%u,\"rematches\":%u,\"mega\":%u,\"z_move\":%u,"
           "\"dynamax\":%u,\"terastal\":%u},\"warnings_errors\":%u}\n",
           passed ? "PASS" : "FAIL", full ? "full" : "quick",
           probe ? "true" : "false", hooks ? "true" : "false",
           bindings ? "true" : "false", parties ? "true" : "false",
           abilities ? "true" : "false", gimmicks ? "true" : "false",
           double_entry ? "true" : "false", save_reload ? "true" : "false",
           counts ? "true" : "false", seen.encounters, seen.members,
           seen.direct_abilities, seen.doubles, seen.kind8, seen.rematches,
           seen.gimmicks[1], seen.gimmicks[2], seen.gimmicks[3], seen.gimmicks[4],
           log_problem_count);
    free(cases);
    return passed ? 0 : 1;
}
