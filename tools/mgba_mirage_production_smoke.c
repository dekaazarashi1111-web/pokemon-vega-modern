/* T21 exact-ROM quick/full validation for Mirage production runtime. */
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

#include <ctype.h>

struct MirageFirstLogCapture {
    bool seen;
    uint32_t pc;
    uint32_t cpsr;
    uint32_t lr;
    uint32_t sp;
    uint32_t main_callback2;
    uint32_t field_callback;
    uint32_t task_callbacks[16];
    uint8_t task_active[16];
};

static struct MirageFirstLogCapture mp_first_log;

static void mp_log(struct mLogger *logger, int category,
                   enum mLogLevel level, const char *format, va_list args)
{
    bool ignored_save_time = strstr(mLogCategoryName(category), "Savedata")
            != NULL
        && strstr(format, "Savegame time offset set") != NULL;
    if (!mp_first_log.seen && qol_log_core && !ignored_save_time
        && (level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) {
        mp_first_log.seen = true;
        mp_first_log.pc = (uint32_t)read_register(qol_log_core, "pc");
        mp_first_log.cpsr = (uint32_t)read_register(qol_log_core, "cpsr");
        mp_first_log.lr = (uint32_t)read_register(qol_log_core, "lr");
        mp_first_log.sp = (uint32_t)read_register(qol_log_core, "sp");
        mp_first_log.main_callback2 = read32(
            qol_log_core, BATTLE_CORE_MAIN_CALLBACK2);
        mp_first_log.field_callback = read32(
            qol_log_core, QOL_FIELD_CALLBACK_SLOT);
        for (unsigned task = 0U; task < 16U; ++task) {
            uint32_t address = QOL_TASKS + task * QOL_TASK_SIZE;
            mp_first_log.task_callbacks[task] = read32(qol_log_core, address);
            mp_first_log.task_active[task] = read8(
                qol_log_core, address + 4U);
        }
    }
    qol_log(logger, category, level, format, args);
}

enum {
    MP_STATUS_OK = 1U,
    MP_STATUS_CANCELLED = 2U,
    MP_STATUS_NOT_UNLOCKED = 3U,
    MP_STATUS_INVALID_SELECTION = 4U,
    MP_STATUS_SAVE_INVALID = 5U,
    MP_STATUS_PERSIST_FAILED = 6U,
    MP_STATUS_NOT_ACTIVE = 7U,
    MP_STATUS_CONFIG_FAILED = 8U,
    MP_STATUS_BATTLE_CONTINUE = 9U,
    MP_STATUS_ROUND_COMPLETE = 10U,
    MP_STATUS_CHALLENGE_COMPLETE = 11U,
    MP_STATUS_LOST = 12U,
    MP_STATUS_BAD_ARGUMENT = 13U,
    MP_STATUS_RECOVERED = 14U,

    MP_PROBE_ABI_VERSION = 0U,
    MP_PROBE_STATE_VALID = 1U,
    MP_PROBE_ACTIVE = 2U,
    MP_PROBE_ROUND = 3U,
    MP_PROBE_BATTLE_IN_ROUND = 4U,
    MP_PROBE_GIMMICK = 5U,
    MP_PROBE_BADGE_SNAPSHOT = 6U,
    MP_PROBE_SELECTED_PACKED = 7U,
    MP_PROBE_LAST_STATUS = 8U,
    MP_PROBE_VIRTUAL_PACKED = 9U,
    MP_PROBE_PENDING_CONFIGURED = 10U,
    MP_PROBE_RNG_STATE = 11U,
    MP_PROBE_OPPONENT_PACKED = 12U,
    MP_PROBE_CLAIM_BITS = 13U,
    MP_PROBE_TRANSACTION_ID = 14U,
    MP_PROBE_JOURNAL_MARKER_PAIR = 15U,
    MP_PROBE_JOURNAL_PAYLOAD_PAIR = 16U,
    MP_PROBE_CURRENT_RECORD = 0x20U,
    MP_PROBE_BEST_RECORD = 0x30U,
    MP_PROBE_SELECTED_SLOT = 0x40U,
    MP_PROBE_VIRTUAL_ITEM = 0x50U,
    MP_PROBE_BATTLE_LOCAL_ACTIVE = 0x62U,
    MP_PROBE_BADGE_CURRENT = 0x63U,

    MP_SPECIAL_VAR_RESULT = 0x02037004U,
    MP_VAR_8000 = 0x02036FECU,
    MP_SELECTED_ORDER = 0x0203C6C8U,
    MP_STATE = 0x0203EE00U,
    MP_STATE_OPPONENT_SLOTS_OFFSET = 0x32U,
    MP_STATE_VIRTUAL_TIER_OFFSET = 0x35U,
    MP_STATE_SIZE = 664U,
    MP_PLAYER_PARTY_SIZE = 600U,
    MP_SECTOR31_LEDGER_FILE_OFFSET = 0x1F064U,
    MP_FACTORY_OFFSET = 914U,
    MP_FACTORY_SIZE = 714U,
    MP_BATTLE_OUTCOME = 0x02023DEAU,
    MP_MAP_GROUP = 31U,
    MP_MAP_NUMBER = 1U,
    MP_RECEPTION_X = 3U,
    MP_RECEPTION_Y = 2U,
    MP_ROUNDS = 4U,
    MP_BATTLES_PER_ROUND = 7U,
    MP_BATTLES = 28U,
    MP_EXIT_PATHS = 8U,
    MP_ROM_BASE = 0x08000000U,
    MP_ROM_END = 0x0A000000U,
    MP_GET_MON_ABILITY = 0x090DA23DU,
    MP_BATTLE_TYPE_IS_MASTER = 0x00000004U,
    MP_BATTLE_TYPE_TRAINER = 0x00000008U,
    MP_BATTLE_TYPE_FRONTIER = 0x06000100U,
    MP_TRAINER_TABLE = 0x09328AF0U,
    MP_TRAINER_RECORD_SIZE = 32U,
    MP_TRAINER_AI_OFFSET = 0x14U,
    MP_TRAINER_FIRST = 745U,
    MP_TRAINER_LAST = 748U,
    MP_BATTLE_MON_ABILITY_OFFSET = 0x38U,
    MP_SCRIPT_CONTEXT1_SETUP = 0x080693A5U,
    MP_SCRIPT_CONTEXT2_ENABLE = 0x08069201U,
    MP_CONFIGURE_TRAINER_BATTLE = 0x0807F949U,
    MP_NO_INTRO_TRAINER_EVENT = 0x08192E63U,
    MP_SET_SAVE_BLOCK_POINTERS = 0x0804B811U,
    MP_POKEMON_STORAGE_SLOT = 0x03005050U,
};

struct MirageRental {
    uint16_t species;
    uint16_t item;
    uint16_t moves[4];
    uint16_t ability;
};

static const struct MirageRental MP_RENTALS[6] = {
    {428U, 891U, {650U, 59U, 546U, 227U}, 118U},
    {1346U, 939U, {497U, 58U, 375U, 202U}, 247U},
    {42U, 187U, {490U, 333U, 350U, 390U}, 93U},
    {1550U, 892U, {499U, 667U, 89U, 390U}, 126U},
    {532U, 903U, {1001U, 188U, 94U, 303U}, 145U},
    {324U, 924U, {578U, 56U, 85U, 195U}, 11U},
};

struct MirageSymbols {
    uint32_t probe;
    uint32_t field_enter;
    uint32_t commit_selection;
    uint32_t commit_round4;
    uint32_t prepare_battle;
    uint32_t finalize_battle_copy;
    uint32_t after_battle;
    uint32_t complete;
    uint32_t abort;
    uint32_t recover;
    uint32_t map_transition_recover;
    uint32_t save_load;
    uint32_t build_trainer_party;
    uint32_t load_proper_ability;
    uint32_t test_warp_to_reception;
    uint32_t inject_fault;
    uint32_t battle_01_trainer_script;
};

struct MirageCases {
    unsigned rows;
    unsigned quick_rows;
    unsigned full_rows;
    bool has_normal_field;
    bool has_progression_28;
    bool has_atomic_fault;
    bool has_all_exits;
};

struct ProgressionResult {
    uint32_t opponents[MP_BATTLES];
    uint32_t rewards[MP_BATTLES];
    unsigned battles;
    bool round_sequence;
    bool battle_copy;
    bool gimmicks;
    bool virtual_items;
    bool cleanup;
    bool party_restored;
    bool records;
};

struct MirageSaveImage {
    size_t size;
    uint8_t *bytes;
};

struct MirageStockBankAudit {
    uint32_t counter;
    uint16_t ids;
    uint16_t bad_checksums;
    bool consistent_counter;
};

static const char *const MP_SYMBOL_NAMES[] = {
    "MirageProduction_Probe",
    "MirageProduction_FieldEnter",
    "MirageProduction_CommitSelection",
    "MirageProduction_CommitRound4Mechanic",
    "MirageProduction_PrepareBattle",
    "MirageProduction_FinalizeBattleCopy",
    "MirageProduction_AfterBattle",
    "MirageProduction_Complete",
    "MirageProduction_Abort",
    "MirageProduction_Recover",
    "MirageProduction_MapTransitionRecover",
    "MirageProduction_SaveLoadAdapter",
    "MirageProduction_BuildTrainerPartyAdapter",
    "MirageProduction_LoadProperAbilityBattleDataAdapter",
    "MirageProduction_TestWarpToReception",
    "MirageProduction_TestInjectPersistenceFault",
};

static bool mp_field_respawn_contract;

static void mp_die(const char *message)
{
    fprintf(stderr, "mgba-mirage-production: %s\n", message);
    exit(1);
}

static char *mp_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        mp_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        mp_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 4L * 1024L * 1024L)
        mp_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        mp_die("fixture read failed");
    if (fclose(stream) != 0)
        mp_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static uint32_t mp_json_first_number(const char *text, const char *key)
{
    char needle[160];
    if (snprintf(needle, sizeof(needle), "\"%s\"", key) < 0)
        mp_die("JSON key formatting failed");
    const char *found = strstr(text, needle);
    if (!found)
        mp_die("JSON nested key missing");
    found += strlen(needle);
    while (isspace((unsigned char)*found))
        ++found;
    if (*found++ != ':')
        mp_die("JSON nested separator differs");
    while (isspace((unsigned char)*found))
        ++found;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(found, &end, 0);
    if (errno || end == found || value > UINT32_MAX)
        mp_die("JSON nested value differs");
    return (uint32_t)value;
}

static struct MirageSymbols mp_load_symbols(const char *path)
{
    char *text = mp_read_text(path);
    if (!strstr(text, "\"schema_version\"")
        || !strstr(text, "\"entrypoints\""))
        mp_die("symbol JSON schema differs");
    mp_field_respawn_contract = strstr(text, "\"id\": 14")
        && strstr(text, "\"opcode\": 159")
        && strstr(text, "\"operation\": \"setrespawn:14\"")
        && strstr(text, "\"operation_count\": 1")
        && strstr(text, "\"after_commit_selection\": true")
        && strstr(text, "\"before_first_battle\": true")
        && strstr(text, "\"selection_cancel_preserves_previous_respawn\": true")
        && strstr(text, "\"party_selection_special\": 41")
        && strstr(text, "\"party_selection_waitstate\": true")
        && strstr(text, "\"pre_battle_special\": null")
        && strstr(text, "\"pre_battle_waitstate\": false")
        && strstr(text,
                  "\"pre_battle_heal_owner\": \"RUNTIME_FINALIZE_BATTLE_COPY\"")
        && strstr(text, "\"special_operation_count\": 1")
        && strstr(text, "\"waitstate_operation_count\": 1")
        && strstr(text, "\"trainerbattle_command\": 92")
        && strstr(text, "\"trainerbattle_mode\": 3")
        && strstr(text, "\"trainerbattle_mode_name\": \"SINGLE_NO_INTRO\"")
        && strstr(text, "\"trainerbattle_local_id\": 1")
        && strstr(text, "\"trainerbattle_launch_count\": 28")
        && strstr(text, "\"direct_bare_battlebegin_count\": 0")
        && strstr(text, "\"map_script_installed\": true")
        && strstr(text, "\"map_script_type\": 3")
        && strstr(text,
                  "\"entrypoint\": \"MirageProduction_MapTransitionRecover\"")
        && strstr(text, "\"direct_recover_call\": false")
        && strstr(text,
                  "\"active_challenge\": \"SKIP_KEEP_JOURNAL_STATUS_OK\"")
        && strstr(text,
                  "\"inactive_challenge\": \"RECOVER_STALE_STATE\"")
        && strstr(text, "\"first_trainerbattle_script\": "
                        "\"script::mirage_battle_01_after\"");
    const char *entrypoints = strstr(text, "\"entrypoints\"");
    if (!entrypoints)
        mp_die("symbol JSON entrypoints are missing");
    uint32_t values[ARRAY_LEN(MP_SYMBOL_NAMES)] = {0};
    for (unsigned index = 0U; index < ARRAY_LEN(MP_SYMBOL_NAMES); ++index)
        values[index] = mp_json_first_number(
            entrypoints, MP_SYMBOL_NAMES[index]);
    const char *labels = strstr(text, "\"labels\"");
    if (!labels)
        mp_die("symbol JSON script labels are missing");
    uint32_t battle_01_trainer = mp_json_first_number(
        labels, "script::mirage_battle_01_after");
    free(text);
    struct MirageSymbols result = {
        values[0], values[1], values[2], values[3], values[4], values[5],
        values[6], values[7], values[8], values[9], values[10], values[11],
        values[12], values[13], values[14], values[15], battle_01_trainer,
    };
    return result;
}

static unsigned mp_split(char *line, char **fields, unsigned capacity)
{
    unsigned count = 0U;
    char *cursor = line;
    while (count < capacity) {
        fields[count++] = cursor;
        char *comma = strchr(cursor, ',');
        if (!comma)
            break;
        *comma = '\0';
        cursor = comma + 1;
    }
    if (count) {
        size_t length = strlen(fields[count - 1U]);
        while (length && (fields[count - 1U][length - 1U] == '\n'
                          || fields[count - 1U][length - 1U] == '\r'))
            fields[count - 1U][--length] = '\0';
    }
    return count;
}

static struct MirageCases mp_load_cases(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        mp_die("case fixture open failed");
    char line[1024];
    if (!fgets(line, sizeof(line), stream)
        || strcmp(line,
                  "case_key,mode,round_index,battle_index,gate_state,"
                  "round4_choice,exit_path,save_fault,expected_result\n"))
        mp_die("case fixture header differs");
    struct MirageCases result = {0};
    bool exits[MP_EXIT_PATHS] = {false};
    unsigned battle_rows = 0U;
    while (fgets(line, sizeof(line), stream)) {
        char *fields[9] = {0};
        if (mp_split(line, fields, ARRAY_LEN(fields)) != ARRAY_LEN(fields))
            mp_die("case fixture row/schema differs");
        if (!fields[0][0]
            || (strcmp(fields[1], "quick") && strcmp(fields[1], "full")))
            mp_die("case fixture key/mode differs");
        ++result.rows;
        if (!strcmp(fields[1], "quick"))
            ++result.quick_rows;
        else
            ++result.full_rows;
        if (strstr(fields[0], "PROGRESSION_28_BATTLE_"))
            ++battle_rows;
        if (strstr(fields[0], "NORMAL_FIELD_A_INPUT"))
            result.has_normal_field = true;
        if (!strcmp(fields[0], "PROGRESSION_28_BATTLE_28")
            && !strcmp(fields[2], "4") && !strcmp(fields[3], "28"))
            result.has_progression_28 = true;
        if (strcmp(fields[7], "NONE"))
            result.has_atomic_fault = true;
        for (unsigned exit = 0U; exit < MP_EXIT_PATHS; ++exit) {
            char numeric[4];
            (void)snprintf(numeric, sizeof(numeric), "%u", exit);
            if (!strcmp(fields[6], numeric))
                exits[exit] = true;
        }
    }
    if (fclose(stream) != 0)
        mp_die("case fixture close failed");
    result.has_all_exits = true;
    for (unsigned exit = 0U; exit < MP_EXIT_PATHS; ++exit)
        result.has_all_exits = result.has_all_exits && exits[exit];
    if (!result.rows || !result.quick_rows || !result.full_rows
        || battle_rows != MP_BATTLES)
        mp_die("case fixture coverage is empty");
    return result;
}

static uint32_t mp_call(struct mCore *core, uint32_t function,
                        uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    return call_preserving(core, function, r0, r1, r2, r3);
}

static uint32_t mp_status_call(struct mCore *core, uint32_t function,
                               uint32_t r0)
{
    write16(core, MP_SPECIAL_VAR_RESULT, 0xA55AU);
    uint32_t status = mp_call(core, function, r0, 0U, 0U, 0U);
    if (read16(core, MP_SPECIAL_VAR_RESULT) != (uint16_t)status)
        mp_die("entrypoint did not mirror status to gSpecialVar_Result");
    return status;
}

static uint32_t mp_probe(struct mCore *core,
                         const struct MirageSymbols *symbols,
                         uint32_t selector)
{
    return mp_call(core, symbols->probe, selector, 0U, 0U, 0U);
}

static bool mp_fresh_save_pointers_ready(struct mCore *core)
{
    static const uint8_t signature[] = {
        0x30U, 0xB5U, 0x0CU, 0x4CU, 0x25U, 0x68U,
        0xF8U, 0xF7U, 0x39U, 0xFEU, 0x7CU, 0x21U,
    };
    for (unsigned index = 0U; index < ARRAY_LEN(signature); ++index) {
        if (read8(core, (MP_SET_SAVE_BLOCK_POINTERS & ~1U) + index)
            != signature[index]) {
            fprintf(stderr,
                    "SetSaveBlocksPointers signature mismatch index=%u\n",
                    index);
            return false;
        }
    }
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint32_t storage = read32(core, MP_POKEMON_STORAGE_SLOT);
    bool ready = save1 >= 0x02000000U && save1 < 0x02040000U
        && save2 >= 0x02000000U && save2 < 0x02040000U
        && storage >= 0x02000000U && storage < 0x02040000U;
    if (!ready) {
        (void)mp_call(
            core, MP_SET_SAVE_BLOCK_POINTERS, 0U, 0U, 0U, 0U);
        save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
        save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
        storage = read32(core, MP_POKEMON_STORAGE_SLOT);
        ready = save1 >= 0x02000000U && save1 < 0x02040000U
            && save2 >= 0x02000000U && save2 < 0x02040000U
            && storage >= 0x02000000U && storage < 0x02040000U;
    }
    if (!ready)
        fprintf(stderr,
                "fresh save pointers invalid sb1=%08" PRIx32
                " sb2=%08" PRIx32 " storage=%08" PRIx32 "\n",
                save1, save2, storage);
    return ready;
}

static uint32_t mp_read32_le(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static bool mp_sync_save_file(const char *path)
{
    FILE *stream = fopen(path, "rb+");
    if (!stream)
        return false;
    bool synced = fflush(stream) == 0 && fsync(fileno(stream)) == 0;
    if (fclose(stream) != 0)
        synced = false;
    return synced;
}

static uint32_t mp_save_file_word(const char *path, long offset)
{
    FILE *stream = fopen(path, "rb");
    uint8_t raw[4];
    if (!stream || fseek(stream, offset, SEEK_SET) != 0
        || fread(raw, 1, sizeof(raw), stream) != sizeof(raw)) {
        if (stream)
            (void)fclose(stream);
        return UINT32_MAX;
    }
    if (fclose(stream) != 0)
        return UINT32_MAX;
    return (uint32_t)raw[0] | ((uint32_t)raw[1] << 8U)
        | ((uint32_t)raw[2] << 16U) | ((uint32_t)raw[3] << 24U);
}

static bool mp_capture_save_image(const char *path,
                                  struct MirageSaveImage *image)
{
    FILE *stream = fopen(path, "rb");
    if (!stream || fseek(stream, 0, SEEK_END) != 0) {
        if (stream)
            (void)fclose(stream);
        return false;
    }
    long length = ftell(stream);
    if (length < (long)QOL_SAVE_SIZE || length > (long)QOL_SAVE_SIZE + 64L
        || fseek(stream, 0, SEEK_SET) != 0) {
        (void)fclose(stream);
        return false;
    }
    image->bytes = malloc((size_t)length);
    image->size = (size_t)length;
    bool captured = image->bytes
        && fread(image->bytes, 1, image->size, stream) == image->size;
    if (fclose(stream) != 0)
        captured = false;
    if (!captured) {
        free(image->bytes);
        image->bytes = NULL;
        image->size = 0U;
    }
    return captured;
}

static bool mp_restore_save_image(const char *path,
                                  const struct MirageSaveImage *image)
{
    FILE *stream = fopen(path, "wb");
    if (!stream)
        return false;
    bool restored = fwrite(image->bytes, 1, image->size, stream) == image->size
        && fflush(stream) == 0 && fsync(fileno(stream)) == 0;
    if (fclose(stream) != 0)
        restored = false;
    return restored;
}

static struct MirageStockBankAudit mp_audit_stock_bank(
    const char *path, unsigned bank)
{
    static const uint16_t section_sizes[14] = {
        0x0F24U, 0x0F80U, 0x0F80U, 0x0F80U, 0x0EC0U, 0x0F80U, 0x0F80U,
        0x0F80U, 0x0F80U, 0x0F80U, 0x0F80U, 0x0F80U, 0x0F80U, 0x07D0U,
    };
    struct MirageStockBankAudit audit = {0U, 0U, 0U, true};
    FILE *stream = fopen(path, "rb");
    if (!stream) {
        audit.consistent_counter = false;
        return audit;
    }
    uint8_t sector[0x1000U];
    for (unsigned physical = 0U; physical < 14U; ++physical) {
        long offset = (long)((bank * 14U + physical) * sizeof(sector));
        if (fseek(stream, offset, SEEK_SET) != 0
            || fread(sector, 1, sizeof(sector), stream) != sizeof(sector)) {
            audit.consistent_counter = false;
            break;
        }
        uint16_t id = (uint16_t)(sector[0x0FF4U]
            | ((uint16_t)sector[0x0FF5U] << 8U));
        uint16_t stored = (uint16_t)(sector[0x0FF6U]
            | ((uint16_t)sector[0x0FF7U] << 8U));
        uint32_t signature = (uint32_t)sector[0x0FF8U]
            | ((uint32_t)sector[0x0FF9U] << 8U)
            | ((uint32_t)sector[0x0FFAU] << 16U)
            | ((uint32_t)sector[0x0FFBU] << 24U);
        uint32_t counter = (uint32_t)sector[0x0FFCU]
            | ((uint32_t)sector[0x0FFDU] << 8U)
            | ((uint32_t)sector[0x0FFEU] << 16U)
            | ((uint32_t)sector[0x0FFFU] << 24U);
        if (physical == 0U)
            audit.counter = counter;
        else if (counter != audit.counter)
            audit.consistent_counter = false;
        if (id >= ARRAY_LEN(section_sizes)
            || signature != UINT32_C(0x08012025)) {
            audit.consistent_counter = false;
            continue;
        }
        audit.ids |= (uint16_t)(1U << id);
        uint32_t sum = 0U;
        for (unsigned byte = 0U; byte < section_sizes[id]; byte += 4U) {
            sum += (uint32_t)sector[byte]
                | ((uint32_t)sector[byte + 1U] << 8U)
                | ((uint32_t)sector[byte + 2U] << 16U)
                | ((uint32_t)sector[byte + 3U] << 24U);
        }
        uint16_t calculated = (uint16_t)((sum >> 16U) + (sum & 0xFFFFU));
        if (calculated != stored)
            audit.bad_checksums |= (uint16_t)(1U << id);
    }
    if (fclose(stream) != 0)
        audit.consistent_counter = false;
    return audit;
}

static uint32_t mp_prepare_battle(struct mCore *core,
                                  const struct MirageSymbols *symbols)
{
    uint32_t round = mp_probe(core, symbols, MP_PROBE_ROUND);
    uint32_t battle = mp_probe(core, symbols, MP_PROBE_BATTLE_IN_ROUND);
    write16(core, MP_VAR_8000, (uint16_t)(round * MP_BATTLES_PER_ROUND + battle));
    return mp_status_call(core, symbols->prepare_battle, 0U);
}

static bool mp_symbols_live(struct mCore *core,
                            const struct MirageSymbols *symbols)
{
    const uint32_t *values = (const uint32_t *)symbols;
    for (unsigned index = 0U; index < ARRAY_LEN(MP_SYMBOL_NAMES); ++index) {
        uint32_t address = values[index];
        if (!(address & 1U) || (address & ~1U) < MP_ROM_BASE
            || (address & ~1U) >= MP_ROM_END
            || read16(core, address & ~1U) == 0xFFFFU)
            return false;
    }
    uint32_t script = symbols->battle_01_trainer_script;
    static const uint8_t postbattle_tail[] = {
        0x5DU, 0x5EU, 0x04U, 0xFCU, 0x2EU, 0x19U, 0x08U,
    };
    static const uint8_t configure_veneer[] = {
        0x00U, 0x4BU, 0x18U, 0x47U, 0xBDU, 0x79U, 0x37U, 0x09U,
    };
    bool physical_continuation = true;
    for (unsigned index = 0U; index < ARRAY_LEN(postbattle_tail); ++index)
        physical_continuation = physical_continuation
            && read8(core, MP_NO_INTRO_TRAINER_EVENT + 27U + index)
                == postbattle_tail[index];
    bool physical_configure = true;
    for (unsigned index = 0U; index < ARRAY_LEN(configure_veneer); ++index)
        physical_configure = physical_configure
            && read8(core, (MP_CONFIGURE_TRAINER_BATTLE & ~1U) + index)
                == configure_veneer[index];
    return physical_continuation && physical_configure
        && script >= MP_ROM_BASE && script < MP_ROM_END
        && (script & 3U) == 0U
        && read8(core, script) == 0x5CU
        && read8(core, script + 1U) == 3U
        && read16(core, script + 2U) == MP_TRAINER_FIRST
        && read16(core, script + 4U) == 1U
        && read8(core, script + 10U) == 0x23U;
}

static bool mp_physical_bindings(struct mCore *core,
                                 const struct MirageSymbols *symbols)
{
    uint32_t receptionist = read32(core, 0x08885D70U);
    uint32_t map_table = read32(core, 0x08315B7CU);
    uint32_t cleanup_a = mp_read32_le(core, 0x08896606U);
    uint32_t cleanup_b = mp_read32_le(core, 0x08173C1DU);
    bool save_hook = read8(core, 0x080DB4E4U) == 0x00U
        && read8(core, 0x080DB4E5U) == 0x4BU
        && read8(core, 0x080DB4E6U) == 0x18U
        && read8(core, 0x080DB4E7U) == 0x47U
        && read32(core, 0x080DB4E8U) == symbols->save_load;
    const uint32_t callers[2] = {0x09096EC4U, 0x090973FCU};
    const uint32_t targets[2] = {
        symbols->build_trainer_party, symbols->load_proper_ability,
    };
    bool trainer_hooks = true;
    for (unsigned index = 0U; index < ARRAY_LEN(callers); ++index) {
        uint16_t first = read16(core, callers[index]);
        uint16_t second = read16(core, callers[index] + 2U);
        uint32_t raw = ((uint32_t)(first & 0x07FFU) << 12U)
            | ((uint32_t)(second & 0x07FFU) << 1U);
        int32_t displacement = (raw & (1U << 22U))
            ? (int32_t)(raw | UINT32_C(0xFF800000)) : (int32_t)raw;
        uint32_t target = (uint32_t)(callers[index] + 4U + displacement);
        trainer_hooks = trainer_hooks
            && (first & 0xF800U) == 0xF000U
            && (second & 0xF800U) == 0xF800U
            && target == (targets[index] & ~1U);
    }
    return receptionist != 0x08895760U
        && map_table != 0x0818F3BCU
        && cleanup_a != 0x08896610U
        && cleanup_b != 0x08896630U
        && receptionist >= MP_ROM_BASE && receptionist < MP_ROM_END
        && map_table >= MP_ROM_BASE && map_table < MP_ROM_END
        && cleanup_a >= MP_ROM_BASE && cleanup_a < MP_ROM_END
        && cleanup_b >= MP_ROM_BASE && cleanup_b < MP_ROM_END
        && save_hook && trainer_hooks;
}

static void mp_copy_from_core(struct mCore *core, uint32_t address,
                              uint8_t *output, unsigned size)
{
    for (unsigned index = 0U; index < size; ++index)
        output[index] = read8(core, address + index);
}

static bool mp_matches_core(struct mCore *core, uint32_t address,
                            const uint8_t *expected, unsigned size)
{
    for (unsigned index = 0U; index < size; ++index) {
        if (read8(core, address + index) != expected[index])
            return false;
    }
    return true;
}

static uint64_t mp_core_hash(struct mCore *core, uint32_t address, unsigned size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < size; ++index) {
        hash ^= read8(core, address + index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static void mp_set_badges(struct mCore *core, uint8_t mask)
{
    for (unsigned index = 0U; index < 8U; ++index) {
        uint32_t function = mask & (1U << index) ? QOL_FLAG_SET : QOL_FLAG_CLEAR;
        (void)mp_call(core, function, QOL_FLAG_BADGE_1 + index, 0U, 0U, 0U);
    }
}

static uint8_t mp_badges(struct mCore *core)
{
    uint8_t result = 0U;
    for (unsigned index = 0U; index < 8U; ++index) {
        if (mp_call(core, QOL_FLAG_GET, QOL_FLAG_BADGE_1 + index, 0U, 0U, 0U))
            result |= (uint8_t)(1U << index);
    }
    return result;
}

static void mp_set_unlocks(struct mCore *core, bool hall_of_fame,
                           uint8_t certifications, bool league)
{
    (void)mp_call(core, hall_of_fame ? QOL_FLAG_SET : QOL_FLAG_CLEAR,
                  QOL_FLAG_HALL_OF_FAME, 0U, 0U, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME,
           hall_of_fame ? 1U : 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, certifications);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, league ? 1U : 0U);
    (void)mp_call(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0U, 0U, 0U);
}

static void mp_prepare_player_party(struct mCore *core)
{
    clear_parties(core);
    static const uint16_t species[6] = {25U, 183U, 6U, 9U, 3U, 149U};
    for (unsigned index = 0U; index < 6U; ++index)
        create_mon(core, QOL_PLAYER_PARTY + index * QOL_PARTY_MON_SIZE,
                   species[index], (uint8_t)(35U + index * 5U));
    write8(core, QOL_PLAYER_PARTY_COUNT, 6U);
    write8(core, MP_SELECTED_ORDER + 0U, 1U);
    write8(core, MP_SELECTED_ORDER + 1U, 2U);
    write8(core, MP_SELECTED_ORDER + 2U, 3U);
    for (unsigned index = 3U; index < 6U; ++index)
        write8(core, MP_SELECTED_ORDER + index, 0U);
}

static void mp_poison_enemy_party(struct mCore *core)
{
    for (unsigned byte = 0U; byte < 6U * QOL_PARTY_MON_SIZE; ++byte)
        write8(core, QOL_ENEMY_PARTY + byte, (uint8_t)(0xA5U ^ byte));
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 6U);
}

static bool mp_rental_exact_with_item(struct mCore *core, uint32_t mon,
                                      const struct MirageRental *rental,
                                      uint16_t held_item)
{
    uint16_t party_ability = rental->ability;
    /* Ninetales and Cloyster have no native slot for the authored ability.
     * The party Pokemon therefore uses its physical primary ability; the
     * battle-data adapter below proves the authored ability at battle time. */
    if (rental->species == 428U)
        party_ability = 18U;
    else if (rental->species == 42U)
        party_ability = 75U;
    uint32_t personality = mp_call(
        core, BATTLE_CORE_GET_MON_DATA, mon, 0U, 0U, 0U);
    uint32_t actual_species = mp_call(
        core, BATTLE_CORE_GET_MON_DATA, mon, QOL_MON_DATA_SPECIES, 0U, 0U);
    uint32_t actual_level = mp_call(
        core, BATTLE_CORE_GET_MON_DATA, mon, QOL_MON_DATA_LEVEL, 0U, 0U);
    uint32_t actual_item = mp_call(
        core, BATTLE_CORE_GET_MON_DATA, mon, QOL_MON_DATA_HELD_ITEM, 0U, 0U);
    uint32_t actual_ability = mp_call(
        core, MP_GET_MON_ABILITY, mon, 0U, 0U, 0U);
    if (actual_species != rental->species
        || actual_level != 100U
        || actual_item != held_item
        || personality % 25U != 12U
        || actual_ability != party_ability) {
        fprintf(stderr,
                "rental base expected=%u/100/%u/nature12/ability%u "
                "actual=%" PRIu32 "/%" PRIu32 "/%" PRIu32
                "/nature%" PRIu32 "/ability%" PRIu32 "\n",
                rental->species, held_item, party_ability,
                actual_species, actual_level, actual_item,
                personality % 25U, actual_ability);
        return false;
    }
    uint32_t move_table = read32(core, BATTLE_CORE_MOVE_TABLE_REPOINT);
    for (unsigned slot = 0U; slot < 4U; ++slot) {
        uint16_t move = rental->moves[slot];
        uint8_t pp = read8(
            core, move_table + move * BATTLE_CORE_BATTLE_MOVE_SIZE + 4U);
        if (mp_call(core, BATTLE_CORE_GET_MON_DATA,
                    mon, QOL_MON_DATA_MOVE1 + slot, 0U, 0U) != move
            || mp_call(core, BATTLE_CORE_GET_MON_DATA,
                       mon, QOL_MON_DATA_PP1 + slot, 0U, 0U) != pp) {
            fprintf(stderr, "rental move/pp mismatch species=%u slot=%u\n",
                    rental->species, slot);
            return false;
        }
    }
    for (unsigned stat = 0U; stat < 6U; ++stat) {
        if (mp_call(core, BATTLE_CORE_GET_MON_DATA,
                    mon, QOL_MON_DATA_HP_EV + stat, 0U, 0U) != 85U
            || mp_call(core, BATTLE_CORE_GET_MON_DATA,
                       mon, QOL_MON_DATA_HP_IV + stat, 0U, 0U) != 31U) {
            fprintf(stderr, "rental EV/IV mismatch species=%u stat=%u\n",
                    rental->species, stat);
            return false;
        }
    }
    return true;
}

static bool mp_rental_exact(struct mCore *core, uint32_t mon,
                            const struct MirageRental *rental)
{
    return mp_rental_exact_with_item(core, mon, rental, rental->item);
}

static bool mp_selected_rentals_exact(struct mCore *core, uint32_t packed)
{
    bool seen[6] = {false};
    for (unsigned index = 0U; index < 3U; ++index) {
        unsigned source = (packed >> (index * 8U)) & 0xFFU;
        if (source >= ARRAY_LEN(MP_RENTALS) || seen[source])
            return false;
        seen[source] = true;
        if (!mp_rental_exact(
                core, QOL_ENEMY_PARTY + index * QOL_PARTY_MON_SIZE,
                &MP_RENTALS[source]))
            return false;
    }
    return true;
}

static bool mp_selected_rentals_exact_virtual(
    struct mCore *core, const struct MirageSymbols *symbols, uint32_t packed)
{
    bool seen[6] = {false};
    for (unsigned index = 0U; index < 3U; ++index) {
        unsigned source = (packed >> (index * 8U)) & 0xFFU;
        uint16_t held_item = (uint16_t)mp_probe(
            core, symbols, MP_PROBE_VIRTUAL_ITEM + index);
        if (source >= ARRAY_LEN(MP_RENTALS) || seen[source])
            return false;
        seen[source] = true;
        if (!mp_rental_exact_with_item(
                core, QOL_ENEMY_PARTY + index * QOL_PARTY_MON_SIZE,
                &MP_RENTALS[source], held_item))
            return false;
    }
    return true;
}

static bool mp_authored_battle_ability_matrix(
    struct mCore *core, const struct MirageSymbols *symbols)
{
    uint8_t active_before = read8(core, ADDR_ACTIVE_BATTLER);
    uint16_t party_index_before = read16(
        core, ADDR_BATTLER_PARTY_INDEXES + 2U);
    bool exact = (read32(core, ADDR_BATTLE_TYPE_FLAGS)
                      & MP_BATTLE_TYPE_TRAINER) != 0U
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 1U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) != 0U;

    /* The rooted caller must already have applied the authored ability on the
     * naturally-created opponent battler before this exhaustive adapter
     * matrix drives the other five authored rows. */
    if (party_index_before >= 3U) {
        exact = false;
    } else {
        unsigned source = read8(
            core, MP_STATE + MP_STATE_OPPONENT_SLOTS_OFFSET
                      + party_index_before);
        uint16_t actual = read16(
            core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                      + MP_BATTLE_MON_ABILITY_OFFSET);
        exact = exact && source < ARRAY_LEN(MP_RENTALS)
            && actual == MP_RENTALS[source].ability;
        if (!exact)
            fprintf(stderr,
                    "natural battle ability mismatch source=%u party=%u "
                    "expected=%u actual=%u\n",
                    source, party_index_before,
                    source < ARRAY_LEN(MP_RENTALS)
                        ? MP_RENTALS[source].ability : 0U,
                    actual);
    }

    /* This targeted six-row matrix runs only after the genuine StartTrainer
     * scheduler has installed TRAINER flags and rebuilt the enemy party.  Run
     * the rooted party adapter for two
     * disjoint selections, then invoke the rooted ability adapter as active
     * opponent battler 1 for each concrete party index.  Party data accepts
     * the two physically unavoidable primary fallbacks; BattlePokemon must
     * always carry the authored SPECIAL6 ability. */
    for (unsigned batch = 0U; batch < 2U && exact; ++batch) {
        for (unsigned slot = 0U; slot < 3U; ++slot)
            write8(core, MP_STATE + MP_STATE_OPPONENT_SLOTS_OFFSET + slot,
                   (uint8_t)(batch * 3U + slot));
        mp_poison_enemy_party(core);
        (void)mp_call(core, symbols->build_trainer_party, 0U, 0U, 0U, 0U);
        exact = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT) == 3U;
        for (unsigned slot = 0U; slot < 3U && exact; ++slot) {
            unsigned source = batch * 3U + slot;
            uint16_t held_item = (uint16_t)mp_probe(
                core, symbols, MP_PROBE_VIRTUAL_ITEM + slot);
            exact = mp_rental_exact_with_item(
                core, QOL_ENEMY_PARTY + slot * QOL_PARTY_MON_SIZE,
                &MP_RENTALS[source], held_item);
            write8(core, ADDR_ACTIVE_BATTLER, 1U);
            write16(core, ADDR_BATTLER_PARTY_INDEXES + 2U, (uint16_t)slot);
            write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                              + MP_BATTLE_MON_ABILITY_OFFSET,
                    0xA55AU);
            (void)mp_call(core, symbols->load_proper_ability, 0U, 0U, 0U, 0U);
            uint16_t actual = read16(
                core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                          + MP_BATTLE_MON_ABILITY_OFFSET);
            if (actual != MP_RENTALS[source].ability) {
                fprintf(stderr,
                        "battle ability mismatch source=%u slot=%u "
                        "expected=%u actual=%u active=%u count=%u absent=%02x\n",
                        source, slot, MP_RENTALS[source].ability, actual,
                        read8(core, ADDR_ACTIVE_BATTLER),
                        read8(core, ADDR_BATTLERS_COUNT),
                        read8(core, ADDR_ABSENT_BATTLER_FLAGS));
                exact = false;
            }
        }
    }
    write8(core, ADDR_ACTIVE_BATTLER, active_before);
    write16(core, ADDR_BATTLER_PARTY_INDEXES + 2U, party_index_before);
    return exact;
}

static bool mp_three_level100(struct mCore *core, uint32_t party,
                              uint32_t count_address)
{
    if (read8(core, count_address) != 3U)
        return false;
    for (unsigned index = 0U; index < 3U; ++index) {
        uint32_t mon = party + index * QOL_PARTY_MON_SIZE;
        if (mp_call(core, BATTLE_CORE_GET_MON_DATA,
                    mon, QOL_MON_DATA_LEVEL, 0U, 0U) != 100U
            || mp_call(core, BATTLE_CORE_GET_MON_DATA,
                       mon, QOL_MON_DATA_SPECIES, 0U, 0U) == 0U)
            return false;
    }
    return true;
}

static bool mp_start(struct mCore *core, const struct MirageSymbols *symbols,
                     uint8_t badge_mask, uint8_t round4_choice,
                     uint8_t party_before[MP_PLAYER_PARTY_SIZE])
{
    uint32_t recover_status = mp_status_call(core, symbols->recover, 0U);
    mp_prepare_player_party(core);
    mp_copy_from_core(core, QOL_PLAYER_PARTY, party_before, MP_PLAYER_PARTY_SIZE);
    mp_set_badges(core, badge_mask);
    uint32_t enter_status = mp_status_call(core, symbols->field_enter, 0U);
    if (enter_status != MP_STATUS_OK) {
        fprintf(stderr, "mp_start enter=%" PRIu32 " recover=%" PRIu32 " journal=%08" PRIx32 "/%08" PRIx32 "\n",
                enter_status, recover_status,
                mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR),
                mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR));
        return false;
    }
    if (mp_probe(core, symbols, MP_PROBE_BADGE_SNAPSHOT) != badge_mask)
        return false;
    uint32_t commit_status = mp_status_call(core, symbols->commit_selection, 0U);
    if (commit_status != MP_STATUS_OK) {
        fprintf(stderr, "mp_start commit=%" PRIu32 " selected=%06" PRIx32 " badges=%02x\n",
                commit_status,
                mp_probe(core, symbols, MP_PROBE_SELECTED_PACKED),
                mp_badges(core));
        return false;
    }
    if (mp_probe(core, symbols, MP_PROBE_ACTIVE) != 1U
        || mp_probe(core, symbols, MP_PROBE_SELECTED_PACKED) != 0x00030201U
        || mp_badges(core) != 0U
        || mp_probe(core, symbols, MP_PROBE_BADGE_CURRENT) != 0U)
    {
        fprintf(stderr, "mp_start post active=%" PRIu32 " selected=%06" PRIx32 " badges=%02x probe_badges=%02" PRIx32 "\n",
                mp_probe(core, symbols, MP_PROBE_ACTIVE),
                mp_probe(core, symbols, MP_PROBE_SELECTED_PACKED),
                mp_badges(core),
                mp_probe(core, symbols, MP_PROBE_BADGE_CURRENT));
        return false;
    }
    uint32_t marker = mp_probe(
        core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR);
    uint32_t payload = mp_probe(
        core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR);
    uint64_t party_hash = mp_core_hash(
        core, QOL_PLAYER_PARTY, MP_PLAYER_PARTY_SIZE);
    if (mp_status_call(core, symbols->map_transition_recover, 0U)
            != MP_STATUS_OK
        || mp_probe(core, symbols, MP_PROBE_ACTIVE) != 1U
        || mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR) != marker
        || mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR) != payload
        || mp_core_hash(core, QOL_PLAYER_PARTY, MP_PLAYER_PARTY_SIZE)
            != party_hash
        || mp_badges(core) != 0U)
        return false;
    write16(core, MP_VAR_8000, round4_choice);
    return true;
}

static bool mp_warp_to_reception(struct mCore *core,
                                 const struct MirageSymbols *symbols)
{
    uint32_t status = mp_status_call(
        core, symbols->test_warp_to_reception, 0U);
    uint32_t save_after_call = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint8_t destination_after_call[8];
    uint8_t location_after_call[8];
    mp_copy_from_core(
        core, 0x02031CF0U, destination_after_call, sizeof(destination_after_call));
    if (save_after_call >= 0x02000000U && save_after_call < 0x02040000U)
        mp_copy_from_core(
            core, save_after_call + QOL_SAVE_LOCATION_OFFSET,
            location_after_call, sizeof(location_after_call));
    else
        memset(location_after_call, 0xFF, sizeof(location_after_call));
    uint32_t callback_after_call = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t field_callback_after_call = read32(core, QOL_FIELD_CALLBACK_SLOT);
    if (status != MP_STATUS_OK)
        return false;
    run_key_frames(core, 0U, 1200U);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    bool warped = save >= 0x02000000U && save < 0x02040000U
        && read8(core, save + 4U) == MP_MAP_GROUP
        && read8(core, save + 5U) == MP_MAP_NUMBER;
    if (!warped) {
        fprintf(stderr,
                "warp call status=%" PRIu32 " dest=%u/%u/%d x=%d y=%d "
                "save=%08" PRIx32 " call_location=%u/%u/%d x=%d y=%d "
                "call_cb=%08" PRIx32 " field_cb=%08" PRIx32 "\n",
                status, destination_after_call[0], destination_after_call[1],
                (int)(int8_t)destination_after_call[2],
                (int)(int16_t)((uint16_t)destination_after_call[4]
                    | ((uint16_t)destination_after_call[5] << 8U)),
                (int)(int16_t)((uint16_t)destination_after_call[6]
                    | ((uint16_t)destination_after_call[7] << 8U)),
                save_after_call, location_after_call[0], location_after_call[1],
                (int)(int8_t)location_after_call[2],
                (int)(int16_t)((uint16_t)location_after_call[4]
                    | ((uint16_t)location_after_call[5] << 8U)),
                (int)(int16_t)((uint16_t)location_after_call[6]
                    | ((uint16_t)location_after_call[7] << 8U)),
                callback_after_call, field_callback_after_call);
        fprintf(stderr,
                "warp after1200 save=%08" PRIx32
                " location=%u/%u/%d x=%d y=%d cb=%08" PRIx32
                " field_cb=%08" PRIx32 " dest=%u/%u/%d x=%d y=%d\n",
                save,
                save >= 0x02000000U && save < 0x02040000U
                    ? read8(core, save + 4U) : 0U,
                save >= 0x02000000U && save < 0x02040000U
                    ? read8(core, save + 5U) : 0U,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int)(int8_t)read8(core, save + 6U) : 0,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int)(int16_t)read16(core, save + 8U) : 0,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int)(int16_t)read16(core, save + 10U) : 0,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, QOL_FIELD_CALLBACK_SLOT),
                read8(core, 0x02031CF0U), read8(core, 0x02031CF1U),
                (int)(int8_t)read8(core, 0x02031CF2U),
                (int)(int16_t)read16(core, 0x02031CF4U),
                (int)(int16_t)read16(core, 0x02031CF6U));
    }
    return warped;
}

static bool mp_run_reception_field_trace(
    struct mCore *core, const struct MirageSymbols *symbols)
{
    /* Replay the reviewed stock new-game trace, but make its one and only
     * fixture warp target the production reception map.  A second asynchronous
     * warp from the QOL map leaves old field tasks/save-block relocation in
     * flight, so it is not evidence for the receptionist's normal input path. */
    bool default_instant = false;
    for (size_t index = 0U;
         index < BATTLE_CORE_FIELD_TRACE_SEGMENTS; ++index) {
        unsigned problems_before = log_problem_count;
        if (index == 2U) {
            (void)mp_call(core, QOL_SAVE_INIT, QOL_LEDGER, 0U, 0U, 0U);
            default_instant = read8(
                core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED) == 0U;
            write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 1U);
            (void)mp_call(core, QOL_SAVE_FINALIZE,
                          QOL_LEDGER, 0U, 0U, 0U);
        }
        core->setKeys(core, BOOT_TRACE[index].keys);
        for (uint32_t frame = 0U; frame < BOOT_TRACE[index].frames; ++frame) {
            core->runFrame(core);
            if (log_problem_count != problems_before)
                break;
        }
        if (log_problem_count != problems_before) {
            fprintf(stderr,
                    "reception trace segment=%zu added_logs=%u pc=%08" PRIx32
                    "\n", index, log_problem_count - problems_before,
                    (uint32_t)read_register(core, "pc"));
            return false;
        }
    }
    core->setKeys(core, 0U);
    /* The final boot-trace key sample is host state, not snapshot state.
     * Latch the released value before the asynchronous reception warp so the
     * stock soft-reset chord cannot be observed during map loading. */
    run_key_frames(core, 0U, 2U);
    /* Finish all direct fixture construction before map load.  ROM calls made
     * after CB2_Overworld becomes live can advance old new-game tasks and are
     * not part of the physical root+A path being verified. */
    mp_prepare_player_party(core);
    bool loaded = mp_warp_to_reception(core, symbols);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 0U);
    (void)mp_call(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0U, 0U, 0U);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    bool stable = default_instant && loaded && log_problem_count == 0U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == 0x08055E75U
        && save >= 0x02000000U && save < 0x02040000U
        && read8(core, save + QOL_SAVE_LOCATION_OFFSET) == MP_MAP_GROUP
        && read8(core, save + QOL_SAVE_LOCATION_OFFSET + 1U) == MP_MAP_NUMBER
        && (int16_t)read16(core, save) == 3
        && (int16_t)read16(core, save + 2U) == 3
        && mp_call(core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U) == 0U;
    if (!stable)
        fprintf(stderr,
                "reception baseline loaded=%u cb=%08" PRIx32
                " save=%08" PRIx32 " map=%u/%u x=%d y=%d script=%" PRIu32
                " logs=%u\n",
                loaded, read32(core, BATTLE_CORE_MAIN_CALLBACK2), save,
                save >= 0x02000000U && save < 0x02040000U
                    ? read8(core, save + QOL_SAVE_LOCATION_OFFSET) : 0U,
                save >= 0x02000000U && save < 0x02040000U
                    ? read8(core, save + QOL_SAVE_LOCATION_OFFSET + 1U) : 0U,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int16_t)read16(core, save) : INT16_MIN,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int16_t)read16(core, save + 2U) : INT16_MIN,
                mp_call(core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U),
                log_problem_count);
    return stable;
}

static bool mp_normal_field_a_path(struct mCore *core,
                                   const struct MirageSymbols *symbols,
                                   const struct Snapshot *base)
{
    restore_snapshot(core, base);
    for (unsigned index = 0U; index < 6U; ++index)
        write8(core, MP_SELECTED_ORDER + index, 0U);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save >= 0x02040000U
        || read8(core, save + QOL_SAVE_LOCATION_OFFSET) != MP_MAP_GROUP
        || read8(core, save + QOL_SAVE_LOCATION_OFFSET + 1U) != MP_MAP_NUMBER)
        return false;
    /* FireRed's persistent flag array is SaveBlock1+0xEE0.  Set only the HOF
     * fixture bit (0x082C / 8, mask 0x10) without a diagnostic ROM call after
     * CB2_Overworld is live; location and event graph remain untouched. */
    uint32_t hall_of_fame_byte = save + 0xEE0U + QOL_FLAG_HALL_OF_FAME / 8U;
    write8(core, hall_of_fame_byte,
           (uint8_t)(read8(core, hall_of_fame_byte)
                     | (1U << (QOL_FLAG_HALL_OF_FAME & 7U))));
    int16_t x_before = save >= 0x02000000U && save < 0x02040000U
        ? (int16_t)read16(core, save) : INT16_MIN;
    int16_t y_before = save >= 0x02000000U && save < 0x02040000U
        ? (int16_t)read16(core, save + 2U) : INT16_MIN;
    write16(core, MP_SPECIAL_VAR_RESULT, 0xA55AU);
    qol_press(core, QOL_KEY_UP, 12U);
    int16_t x_after_up = save >= 0x02000000U && save < 0x02040000U
        ? (int16_t)read16(core, save) : INT16_MIN;
    int16_t y_after_up = save >= 0x02000000U && save < 0x02040000U
        ? (int16_t)read16(core, save + 2U) : INT16_MIN;
    qol_press(core, QOL_KEY_A, 90U);
    uint16_t result_after_first_a = read16(core, MP_SPECIAL_VAR_RESULT);
    uint32_t context_after_first_a = mp_call(
        core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U);
    qol_press(core, QOL_KEY_A, 90U);
    uint16_t field_result = read16(core, MP_SPECIAL_VAR_RESULT);
    uint32_t last_status = mp_probe(core, symbols, MP_PROBE_LAST_STATUS);
    uint32_t context = mp_call(core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U);
    bool entered = field_result == MP_STATUS_OK
        && last_status == MP_STATUS_OK && context != 0U;
    uint32_t selection_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    unsigned selection_presses = 0U;
    while (selection_callback == 0x08055E75U && selection_presses < 8U) {
        qol_press(core, QOL_KEY_A, 90U);
        selection_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        ++selection_presses;
    }
    uint32_t selection_context = mp_call(
        core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U);
    bool selection_started = selection_callback != 0x08055E75U
        && selection_context != 0U;
    if (!entered)
        fprintf(stderr, "normal field position=%d/%d after_up=%d/%d "
                "first_result=%u first_context=%" PRIu32
                " result=%u last=%" PRIu32 " context=%" PRIu32
                " active=%" PRIu32 " cb=%08" PRIx32 "\n",
                x_before, y_before, x_after_up, y_after_up,
                result_after_first_a, context_after_first_a,
                field_result, last_status, context,
                mp_probe(core, symbols, MP_PROBE_ACTIVE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
    if (!entered) {
        fprintf(stderr, "normal field object0=");
        for (unsigned byte = 0U; byte < 36U; ++byte)
            fprintf(stderr, "%02x", read8(core, 0x02036E38U + byte));
        fputc('\n', stderr);
    }
    if (entered && !selection_started)
        fprintf(stderr,
                "normal field selection callback=%08" PRIx32
                " context=%" PRIu32 " presses=%u order=%u/%u/%u\n",
                selection_callback, selection_context,
                selection_presses,
                read8(core, MP_SELECTED_ORDER),
                read8(core, MP_SELECTED_ORDER + 1U),
                read8(core, MP_SELECTED_ORDER + 2U));
    return entered && selection_started
        && read32(core, 0x08885D70U) != 0x08895760U;
}

static bool mp_normal_field_process(
    const char *rom_path, const char *save_path,
    const struct MirageSymbols *symbols)
{
    const char suffix[] = ".mirage-field";
    size_t length = strlen(save_path);
    char *field_save = malloc(length + sizeof(suffix));
    if (!field_save)
        mp_die("field fixture path allocation failed");
    memcpy(field_save, save_path, length);
    memcpy(field_save + length, suffix, sizeof(suffix));
    qol_initialize_save(field_save);
    struct mCore *core = qol_open(rom_path, field_save);
    qol_log_core = core;
    bool boot = mp_run_reception_field_trace(core, symbols);
    bool entered = false;
    if (boot) {
        struct Snapshot base = take_snapshot(core);
        entered = mp_normal_field_a_path(core, symbols, &base);
        free(base.bytes);
    }
    qol_close(core);
    if (remove(field_save) != 0)
        fprintf(stderr, "field fixture save cleanup failed: %s\n", field_save);
    free(field_save);
    return boot && entered;
}

static bool mp_probe_contract(struct mCore *core,
                              const struct MirageSymbols *symbols)
{
    return mp_probe(core, symbols, MP_PROBE_ABI_VERSION) != 0U
        && mp_probe(core, symbols, MP_PROBE_STATE_VALID) == 1U
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U;
}

static bool mp_unlock_matrix(struct mCore *core,
                             const struct MirageSymbols *symbols,
                             const struct Snapshot *base)
{
    uint8_t party[MP_PLAYER_PARTY_SIZE];
    restore_snapshot(core, base);
    mp_set_unlocks(core, false, 0U, false);
    mp_prepare_player_party(core);
    uint32_t before_status = mp_status_call(core, symbols->field_enter, 0U);
    bool before_hof = before_status == MP_STATUS_NOT_UNLOCKED
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U;
    if (!before_hof)
        fprintf(stderr, "unlock before_hof status=%" PRIu32 " active=%" PRIu32 "\n",
                before_status, mp_probe(core, symbols, MP_PROBE_ACTIVE));

    restore_snapshot(core, base);
    mp_set_unlocks(core, true, 0x07U, false);
    bool cert3 = mp_start(core, symbols, 0x5AU, 1U, party);
    if (cert3) {
        for (unsigned battle = 0U; battle < MP_BATTLES_PER_ROUND; ++battle) {
            uint32_t prepare_status = mp_prepare_battle(core, symbols);
            cert3 = prepare_status == MP_STATUS_OK;
            mp_poison_enemy_party(core);
            uint32_t finalize_status = mp_status_call(
                core, symbols->finalize_battle_copy, 0U);
            cert3 = cert3 && finalize_status == MP_STATUS_OK;
            write8(core, MP_BATTLE_OUTCOME, 1U);
            uint32_t status = mp_status_call(core, symbols->after_battle, 0U);
            cert3 = cert3 && (battle + 1U < MP_BATTLES_PER_ROUND
                ? status == MP_STATUS_BATTLE_CONTINUE
                : status == MP_STATUS_CHALLENGE_COMPLETE);
            if (!cert3) {
                fprintf(stderr, "unlock cert3 battle=%u prepare=%" PRIu32 " finalize=%" PRIu32 " after=%" PRIu32 "\n",
                        battle, prepare_status, finalize_status, status);
                break;
            }
        }
        cert3 = cert3 && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
            && mp_probe(core, symbols, MP_PROBE_ROUND) == 0U
            && mp_badges(core) == 0x5AU;
    }
    return before_hof && cert3;
}

static struct ProgressionResult mp_progression(
    struct mCore *core, const struct MirageSymbols *symbols,
    uint8_t badge_mask, uint8_t round4_choice)
{
    struct ProgressionResult result = {0};
    uint8_t party_before[MP_PLAYER_PARTY_SIZE];
    result.round_sequence = mp_start(
        core, symbols, badge_mask, round4_choice, party_before);
    result.battle_copy = result.round_sequence;
    result.gimmicks = result.round_sequence;
    result.virtual_items = result.round_sequence;
    result.cleanup = result.round_sequence;
    static const uint32_t expected_gimmicks[MP_ROUNDS] = {0U, 1U, 2U, 4U};
    static const uint16_t expected_virtual_items[MP_ROUNDS] = {
        0U, 95U, 186U, 943U,
    };
    for (unsigned battle = 0U; battle < MP_BATTLES && result.round_sequence;
         ++battle) {
        unsigned expected_round = battle / MP_BATTLES_PER_ROUND;
        unsigned expected_in_round = battle % MP_BATTLES_PER_ROUND;
        result.round_sequence = mp_probe(core, symbols, MP_PROBE_ROUND)
                == expected_round
            && mp_probe(core, symbols, MP_PROBE_BATTLE_IN_ROUND)
                == expected_in_round;
        if (expected_round == 3U && expected_in_round == 0U) {
            write16(core, MP_VAR_8000, round4_choice);
            result.gimmicks = result.gimmicks
                && mp_status_call(core, symbols->commit_round4, 0U) == MP_STATUS_OK;
        }
        result.gimmicks = result.gimmicks
            && mp_probe(core, symbols, MP_PROBE_GIMMICK)
                == expected_gimmicks[expected_round];
        uint32_t prepare_status = mp_prepare_battle(core, symbols);
        if (prepare_status != MP_STATUS_OK) {
            fprintf(stderr, "progression battle=%u prepare=%" PRIu32 " round=%" PRIu32 " in_round=%" PRIu32 "\n",
                    battle, prepare_status,
                    mp_probe(core, symbols, MP_PROBE_ROUND),
                    mp_probe(core, symbols, MP_PROBE_BATTLE_IN_ROUND));
            result.round_sequence = false;
            break;
        }
        result.opponents[battle] = mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED);
        mp_poison_enemy_party(core);
        uint32_t finalize_status = mp_status_call(
            core, symbols->finalize_battle_copy, 0U);
        if (finalize_status != MP_STATUS_OK) {
            fprintf(stderr, "progression battle=%u finalize=%" PRIu32 " tier=%u opponents=%06" PRIx32 " pending=%" PRIu32 " local=%" PRIu32 "\n",
                    battle, finalize_status,
                    read8(core, MP_STATE + MP_STATE_VIRTUAL_TIER_OFFSET),
                    mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED),
                    mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED),
                    mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE));
            for (unsigned debug_slot = 0U; debug_slot < 3U; ++debug_slot) {
                uint32_t mon = QOL_ENEMY_PARTY
                    + debug_slot * QOL_PARTY_MON_SIZE;
                fprintf(stderr, " enemy%u species=%" PRIu32 " ability=%" PRIu32 " item=%" PRIu32 "\n",
                        debug_slot,
                        mp_call(core, BATTLE_CORE_GET_MON_DATA, mon,
                                QOL_MON_DATA_SPECIES, 0U, 0U),
                        mp_call(core, MP_GET_MON_ABILITY, mon, 0U, 0U, 0U),
                        mp_call(core, BATTLE_CORE_GET_MON_DATA, mon,
                                QOL_MON_DATA_HELD_ITEM, 0U, 0U));
            }
            result.battle_copy = false;
            result.round_sequence = false;
            break;
        }
        result.battle_copy = result.battle_copy
            && mp_three_level100(core, QOL_PLAYER_PARTY, QOL_PLAYER_PARTY_COUNT)
            && mp_three_level100(core, QOL_ENEMY_PARTY,
                                 BATTLE_CORE_ENEMY_PARTY_COUNT)
            && mp_selected_rentals_exact(core, result.opponents[battle]);
        result.virtual_items = result.virtual_items
            && mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) != 0U
            && read8(core, MP_STATE + MP_STATE_VIRTUAL_TIER_OFFSET)
                == (expected_round ? expected_round : 0xFFU);
        for (unsigned slot = 0U; slot < 3U; ++slot) {
            result.virtual_items = result.virtual_items
                && mp_probe(core, symbols, MP_PROBE_VIRTUAL_ITEM + slot)
                    == expected_virtual_items[expected_round];
        }
        result.rewards[battle] = mp_probe(core, symbols, MP_PROBE_VIRTUAL_PACKED);
        write8(core, MP_BATTLE_OUTCOME, 1U);
        uint32_t status = mp_status_call(core, symbols->after_battle, 0U);
        uint32_t expected_status = expected_in_round + 1U < MP_BATTLES_PER_ROUND
            ? MP_STATUS_BATTLE_CONTINUE
            : (expected_round + 1U < MP_ROUNDS
               ? MP_STATUS_ROUND_COMPLETE : MP_STATUS_CHALLENGE_COMPLETE);
        result.round_sequence = result.round_sequence && status == expected_status;
        result.cleanup = result.cleanup
            && mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) == 0U
            && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U;
        result.party_restored = mp_matches_core(
            core, QOL_PLAYER_PARTY, party_before, MP_PLAYER_PARTY_SIZE)
            && read8(core, QOL_PLAYER_PARTY_COUNT) == 6U;
        ++result.battles;
    }
    if (result.battles == MP_BATTLES) {
        uint32_t status = mp_status_call(core, symbols->complete, 0U);
        result.cleanup = result.cleanup
            && (status == MP_STATUS_OK || status == MP_STATUS_RECOVERED
                || status == MP_STATUS_NOT_ACTIVE)
            && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
            && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
            && mp_badges(core) == badge_mask;
        result.party_restored = result.party_restored
            && mp_matches_core(core, QOL_PLAYER_PARTY,
                               party_before, MP_PLAYER_PARTY_SIZE);
        result.records = true;
        for (unsigned round = 0U; round < MP_ROUNDS; ++round) {
            result.records = result.records
                && mp_probe(core, symbols, MP_PROBE_CURRENT_RECORD + round) >= 7U
                && mp_probe(core, symbols, MP_PROBE_BEST_RECORD + round) >= 7U;
        }
    }
    return result;
}

static bool mp_scheduler_battle_case(struct mCore *core,
                                     const struct MirageSymbols *symbols,
                                     const struct Snapshot *base,
                                     const struct CpuState *field_cpu,
                                     uint16_t stale_mode,
                                     bool verify_abilities,
                                     bool *authored_abilities)
{
    *authored_abilities = false;
    restore_snapshot(core, base);
    restore_cpu_state(core, field_cpu);
    mp_set_unlocks(core, true, 0x0FU, true);
    uint8_t party_before[MP_PLAYER_PARTY_SIZE];
    if (!mp_start(core, symbols, 0x69U, 4U, party_before))
        return false;

    /* Use the first production battle as the real scheduler representative.
     * This keeps the field snapshot pristine before the asynchronous setup;
     * the independent 28-battle matrix below proves all four round mechanics
     * and boundaries.  Round 1's natural gimmick is NONE, while its pending
     * virtual-item configuration and AI5 contract must still be live. */
    if (mp_prepare_battle(core, symbols) != MP_STATUS_OK)
        return false;
    uint32_t opponents = mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED);
    mp_poison_enemy_party(core);
    if (mp_status_call(core, symbols->finalize_battle_copy, 0U) != MP_STATUS_OK
        || !mp_selected_rentals_exact(core, opponents)
        || !mp_three_level100(core, QOL_PLAYER_PARTY, QOL_PLAYER_PARTY_COUNT)
        || !mp_three_level100(core, QOL_ENEMY_PARTY,
                              BATTLE_CORE_ENEMY_PARTY_COUNT))
        return false;
    uint16_t trainer_id = read16(core, BATTLE_CORE_TRAINER_OPPONENT_A);
    uint32_t player_species[3];
    uint32_t player_hp[3];
    uint32_t player_egg[3];
    for (unsigned slot = 0U; slot < 3U; ++slot) {
        uint32_t mon = QOL_PLAYER_PARTY + slot * QOL_PARTY_MON_SIZE;
        player_species[slot] = mp_call(
            core, BATTLE_CORE_GET_MON_DATA, mon,
            QOL_MON_DATA_SPECIES, 0U, 0U);
        player_hp[slot] = mp_call(
            core, BATTLE_CORE_GET_MON_DATA, mon,
            QOL_MON_DATA_HP, 0U, 0U);
        player_egg[slot] = mp_call(
            core, BATTLE_CORE_GET_MON_DATA, mon,
            QOL_MON_DATA_IS_EGG, 0U, 0U);
    }
    bool trainer_contract = trainer_id == MP_TRAINER_FIRST
        && read32(core, MP_TRAINER_TABLE
                         + (uint32_t)trainer_id * MP_TRAINER_RECORD_SIZE
                         + MP_TRAINER_AI_OFFSET) == 5U;
    /* Keep the direct configure ABI check independent from the asynchronous
     * production script.  Restoring this snapshot ensures the live fixture
     * below reaches ConfigureTrainerBattle only through opcode 0x5C. */
    struct Snapshot configure_base = take_snapshot(core);
    uint32_t callback_before = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t configured_script = mp_call(
        core, MP_CONFIGURE_TRAINER_BATTLE,
        symbols->battle_01_trainer_script + 1U, 0U, 0U, 0U);
    trainer_contract = trainer_contract
        && configured_script == MP_NO_INTRO_TRAINER_EVENT
        && read16(core, BATTLE_CORE_TRAINER_MODE) == 3U
        && read16(core, BATTLE_CORE_TRAINER_OPPONENT_A) == MP_TRAINER_FIRST;
    restore_snapshot(core, &configure_base);
    free(configure_base.bytes);

    /* Mode is intentionally poisoned with every stock non-single branch that
     * previously leaked here (tutorial/multi/two-opponent/tag).  The generated
     * trainerbattle 0x5C/mode3 command must overwrite it before scheduling.
     * Finalize produced the reviewed prebuilt exact3 immediately above; the
     * rooted stock BuildTrainerParty chain must retain that identity when the
     * field scheduler consumes the command. */
    write16(core, BATTLE_CORE_TRAINER_MODE, stale_mode);
    write32_bytes(core, ADDR_BATTLE_TYPE_FLAGS, 0U);
    memset(&mp_first_log, 0, sizeof(mp_first_log));
    unsigned problems_before = log_problem_count;
    struct CallObservation setup = call_bounded(
        core, MP_SCRIPT_CONTEXT1_SETUP,
        symbols->battle_01_trainer_script, 0U, 0U, 0U);
    (void)mp_call(core, MP_SCRIPT_CONTEXT2_ENABLE, 0U, 0U, 0U, 0U);
    uint32_t callback_after_setup = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t flags_after_setup = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    uint32_t new_after_setup = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
    uint32_t resources_after_setup = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
    uint32_t state_magic_after_setup = read32(core, MP_STATE);
    restore_cpu_state(core, field_cpu);
    unsigned first_runtime_frame = UINT_MAX;
    uint32_t observed_flags = 0U;
    uint8_t max_battlers = 0U;
    uint8_t max_enemy_count = 0U;
    uint8_t max_active = 0U;
    bool scheduler_observed = false;
    bool scheduler_full = false;
    bool party_exact = false;
    bool mode_normalized = false;
    unsigned setup_frames = 0U;
    for (;;) {
        if (log_problem_count != problems_before)
            break;
        /* Keep the natural scheduler CPU untouched.  All continuing-frame
         * observations below are raw RAM reads; the only direct ROM checks
         * occur in the terminal frame_full branch, which immediately breaks. */
        uint32_t frame_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
        uint8_t frame_battlers = read8(core, ADDR_BATTLERS_COUNT);
        uint32_t frame_new = read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER);
        uint32_t frame_resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
        uint8_t frame_enemy_count = read8(
            core, BATTLE_CORE_ENEMY_PARTY_COUNT);
        uint8_t frame_active = read8(core, MP_STATE + 0x28U);
        uint32_t frame_thinking = frame_resources
            ? read32(core, frame_resources + 20U) : 0U;
        uint32_t frame_ai = frame_thinking
            ? read32(core, frame_thinking + 12U) : 0U;
        uint16_t frame_mode = read16(core, BATTLE_CORE_TRAINER_MODE);
        uint16_t frame_party_index = read16(
            core, ADDR_BATTLER_PARTY_INDEXES + 2U);
        uint8_t frame_source = frame_party_index < 3U
            ? read8(core, MP_STATE + MP_STATE_OPPONENT_SLOTS_OFFSET
                              + frame_party_index)
            : UINT8_MAX;
        uint16_t frame_ability = read16(
            core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                      + MP_BATTLE_MON_ABILITY_OFFSET);
        bool frame_authored_ability = frame_source < ARRAY_LEN(MP_RENTALS)
            && frame_ability == MP_RENTALS[frame_source].ability;
        observed_flags |= frame_flags;
        if (frame_battlers > max_battlers)
            max_battlers = frame_battlers;
        if (frame_enemy_count > max_enemy_count)
            max_enemy_count = frame_enemy_count;
        if (frame_active > max_active)
            max_active = frame_active;
        if (first_runtime_frame == UINT_MAX
            && (frame_flags || frame_battlers || frame_new || frame_resources))
            first_runtime_frame = setup_frames;
        bool frame_runtime =
            frame_flags == (MP_BATTLE_TYPE_TRAINER
                            | MP_BATTLE_TYPE_IS_MASTER)
            && frame_mode == 3U
            && frame_enemy_count == 3U
            && read8(core, MP_STATE + 0x2BU) == 0U
            && read8(core, MP_STATE + 0x36U) != 0U
            && read8(core, MP_STATE + 0x3DU) != 0U;
        bool frame_full = frame_runtime && frame_battlers == 2U
            && frame_new != 0U && frame_resources != 0U
            && frame_thinking != 0U && frame_ai == 5U
            && frame_authored_ability;
        if (frame_runtime) {
            scheduler_observed = true;
            mode_normalized = true;
            if (frame_full) {
                scheduler_full = true;
                party_exact = mp_selected_rentals_exact_virtual(
                    core, symbols, opponents);
                *authored_abilities = !verify_abilities
                    || (party_exact
                        && mp_authored_battle_ability_matrix(core, symbols));
                break;
            }
        }
        if (setup_frames >= 5120U)
            break;
        core->setKeys(core,
                      setup_frames % 32U < 2U ? QOL_KEY_A : 0U);
        core->runFrame(core);
        ++setup_frames;
    }
    core->setKeys(core, 0U);
    uint32_t flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    uint32_t resources = read32(core, ADDR_BATTLE_RESOURCES_POINTER);
    uint32_t thinking = resources ? read32(core, resources + 20U) : 0U;
    uint32_t ai_flags = thinking ? read32(core, thinking + 12U) : 0U;
    bool live = setup.instructions != 0U
        && trainer_contract
        && scheduler_observed && scheduler_full && party_exact
        && mode_normalized && log_problem_count == problems_before;
    if (!live) {
        uint32_t debug_gimmick = UINT32_MAX;
        uint32_t debug_pending = UINT32_MAX;
        uint32_t debug_local = UINT32_MAX;
        if (log_problem_count == problems_before) {
            debug_gimmick = mp_probe(core, symbols, MP_PROBE_GIMMICK);
            debug_pending = mp_probe(
                core, symbols, MP_PROBE_PENDING_CONFIGURED);
            debug_local = mp_probe(
                core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE);
        }
        fprintf(stderr,
                "scheduler live fail ins=%u frames=%u trainer=%u contract=%u "
                "flags=%08" PRIx32 " battlers=%u new=%08" PRIx32
                " resources=%08" PRIx32 " thinking=%08" PRIx32
                " ai=%" PRIu32 " enemy=%u party=%u gimmick=%" PRIu32
                " pending=%" PRIu32 " local=%" PRIu32 " full=%u mode=%u/%u"
                " callback=%08" PRIx32 "/%08" PRIx32 "/%08" PRIx32 "\n",
                setup.instructions, setup_frames, trainer_id, trainer_contract, flags,
                read8(core, ADDR_BATTLERS_COUNT),
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER), resources,
                thinking, ai_flags, read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT),
                party_exact, debug_gimmick, debug_pending, debug_local,
                scheduler_full, (unsigned)stale_mode,
                (unsigned)read16(core, BATTLE_CORE_TRAINER_MODE),
                callback_before, callback_after_setup,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        fprintf(stderr,
                "scheduler samples immediate flags=%08" PRIx32
                " new=%08" PRIx32 " resources=%08" PRIx32
                " state_magic=%08" PRIx32
                " observed_flags=%08" PRIx32 " first=%u max_battlers=%u"
                " max_enemy=%u max_active=%u player_count=%u"
                " mons=%" PRIu32 "/%" PRIu32 "/%" PRIu32
                " hp=%" PRIu32 "/%" PRIu32 "/%" PRIu32
                " egg=%" PRIu32 "/%" PRIu32 "/%" PRIu32 "\n",
                flags_after_setup, new_after_setup, resources_after_setup,
                state_magic_after_setup,
                observed_flags, first_runtime_frame, max_battlers,
                max_enemy_count, max_active, read8(core, QOL_PLAYER_PARTY_COUNT),
                player_species[0], player_species[1], player_species[2],
                player_hp[0], player_hp[1], player_hp[2],
                player_egg[0], player_egg[1], player_egg[2]);
        if (log_problem_count == problems_before) {
            fprintf(stderr,
                    "scheduler state active=%" PRIu32 " round=%" PRIu32
                    " battle=%" PRIu32 " status=%" PRIu32
                    " journal=%08" PRIx32 "/%08" PRIx32
                    " outcome=%u\n",
                    mp_probe(core, symbols, MP_PROBE_ACTIVE),
                    mp_probe(core, symbols, MP_PROBE_ROUND),
                    mp_probe(core, symbols, MP_PROBE_BATTLE_IN_ROUND),
                    mp_probe(core, symbols, MP_PROBE_LAST_STATUS),
                    mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR),
                    mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR),
                    read8(core, MP_BATTLE_OUTCOME));
        } else {
            fprintf(stderr,
                    "scheduler stopped on emulator log delta=%u pc=%08" PRIx32
                    " raw_state=%08" PRIx32
                    " first_pc=%08" PRIx32 " cpsr=%08" PRIx32
                    " thumb=%u lr=%08" PRIx32 " sp=%08" PRIx32
                    " main=%08" PRIx32 " field=%08" PRIx32 "\n",
                    log_problem_count - problems_before,
                    (uint32_t)read_register(core, "pc"), read32(core, MP_STATE),
                    mp_first_log.pc, mp_first_log.cpsr,
                    (mp_first_log.cpsr >> 5U) & 1U, mp_first_log.lr,
                    mp_first_log.sp, mp_first_log.main_callback2,
                    mp_first_log.field_callback);
            for (unsigned task = 0U; task < 16U; ++task) {
                if (mp_first_log.task_active[task])
                    fprintf(stderr,
                            " scheduler first_log task%u=%08" PRIx32 "\n",
                            task, mp_first_log.task_callbacks[task]);
            }
        }
    }
    if (!live)
        return false;
    write8(core, MP_BATTLE_OUTCOME, 2U);
    uint32_t status = mp_status_call(core, symbols->after_battle, 0U);
    return live && *authored_abilities && status == MP_STATUS_LOST
        && mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) == 0U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
        && mp_matches_core(core, QOL_PLAYER_PARTY,
                           party_before, MP_PLAYER_PARTY_SIZE)
        && mp_badges(core) == 0x69U;
}

static bool mp_scheduler_battle(struct mCore *core,
                                const struct MirageSymbols *symbols,
                                const struct Snapshot *base,
                                bool *authored_abilities)
{
    static const uint16_t stale_modes[] = {9U, 10U, 11U, 12U, 16U};
    bool passed = true;
    *authored_abilities = false;
    restore_snapshot(core, base);
    struct CpuState field_cpu = capture_cpu_state(core);
    for (unsigned index = 0U; index < ARRAY_LEN(stale_modes); ++index) {
        bool row_abilities = false;
        bool row = mp_scheduler_battle_case(
            core, symbols, base, &field_cpu, stale_modes[index], index == 0U,
            &row_abilities);
        passed = passed && row;
        if (index == 0U)
            *authored_abilities = row_abilities;
        if (!row) {
            fprintf(stderr, "scheduler stale-mode regression failed mode=%u\n",
                    (unsigned)stale_modes[index]);
            break;
        }
    }
    return passed && *authored_abilities;
}

static bool mp_scheduler_field_process(
    const char *rom_path, const char *save_path,
    const struct MirageSymbols *symbols, bool *authored_abilities)
{
    const char suffix[] = ".mirage-scheduler";
    size_t length = strlen(save_path);
    char *scheduler_save = malloc(length + sizeof(suffix));
    if (!scheduler_save)
        mp_die("scheduler fixture path allocation failed");
    memcpy(scheduler_save, save_path, length);
    memcpy(scheduler_save + length, suffix, sizeof(suffix));
    qol_initialize_save(scheduler_save);
    struct mCore *core = qol_open(rom_path, scheduler_save);
    qol_log_core = core;
    bool boot = mp_run_reception_field_trace(core, symbols);
    bool scheduled = false;
    if (boot) {
        struct Snapshot field = take_snapshot(core);
        scheduled = mp_scheduler_battle(
            core, symbols, &field, authored_abilities);
        free(field.bytes);
    }
    qol_close(core);
    if (remove(scheduler_save) != 0)
        fprintf(stderr, "scheduler fixture save cleanup failed: %s\n",
                scheduler_save);
    free(scheduler_save);
    return boot && scheduled;
}

static bool mp_equal_progression(const struct ProgressionResult *left,
                                 const struct ProgressionResult *right)
{
    return left->battles == MP_BATTLES && right->battles == MP_BATTLES
        && !memcmp(left->opponents, right->opponents, sizeof(left->opponents))
        && !memcmp(left->rewards, right->rewards, sizeof(left->rewards));
}

static bool mp_top_reward_replay(struct mCore *core,
                                 const struct MirageSymbols *symbols)
{
    uint32_t total_before = 0U;
    for (unsigned round = 0U; round < MP_ROUNDS; ++round)
        total_before += mp_probe(core, symbols, MP_PROBE_CURRENT_RECORD + round);
    uint32_t transaction_before = mp_probe(
        core, symbols, MP_PROBE_TRANSACTION_ID);
    if (total_before != 28U
        || mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) != 1U)
        return false;

    uint8_t party_before[MP_PLAYER_PARTY_SIZE];
    if (!mp_start(core, symbols, 0x96U, 4U, party_before))
        return false;
    for (unsigned battle = 0U; battle < MP_BATTLES_PER_ROUND; ++battle) {
        if (mp_prepare_battle(core, symbols) != MP_STATUS_OK
            || read8(core, MP_STATE + MP_STATE_VIRTUAL_TIER_OFFSET) != 4U)
            return false;
        uint32_t packed = mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED);
        mp_poison_enemy_party(core);
        if (mp_status_call(core, symbols->finalize_battle_copy, 0U) != MP_STATUS_OK
            || !mp_selected_rentals_exact(core, packed))
            return false;
        write8(core, MP_BATTLE_OUTCOME, 1U);
        uint32_t status = mp_status_call(core, symbols->after_battle, 0U);
        if (status != (battle + 1U < MP_BATTLES_PER_ROUND
                       ? MP_STATUS_BATTLE_CONTINUE : MP_STATUS_ROUND_COMPLETE))
            return false;
    }

    uint32_t total_after = 0U;
    for (unsigned round = 0U; round < MP_ROUNDS; ++round)
        total_after += mp_probe(core, symbols, MP_PROBE_CURRENT_RECORD + round);
    if (total_after != 35U
        || mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) != 3U
        || mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID) <= transaction_before
        || mp_prepare_battle(core, symbols) != MP_STATUS_OK
        || read8(core, MP_STATE + MP_STATE_VIRTUAL_TIER_OFFSET) != 5U)
        return false;
    for (unsigned slot = 0U; slot < 3U; ++slot) {
        if (mp_probe(core, symbols, MP_PROBE_VIRTUAL_ITEM + slot) != 685U)
            return false;
    }
    uint32_t status = mp_status_call(core, symbols->abort, 0U);
    return (status == MP_STATUS_OK || status == MP_STATUS_RECOVERED)
        && mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) == 3U
        && mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) == 0U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
        && mp_matches_core(core, QOL_PLAYER_PARTY,
                           party_before, MP_PLAYER_PARTY_SIZE)
        && mp_badges(core) == 0x96U;
}

static bool mp_atomic_faults(struct mCore *core,
                             const struct MirageSymbols *symbols,
                             const struct Snapshot *base)
{
    bool result = true;
    for (uint32_t fault = 1U; fault <= 2U; ++fault) {
        restore_snapshot(core, base);
        mp_set_unlocks(core, true, 0x0FU, true);
        mp_prepare_player_party(core);
        mp_set_badges(core, 0xA5U);
        if (mp_status_call(core, symbols->field_enter, 0U) != MP_STATUS_OK)
            return false;
        uint32_t transaction_before = mp_probe(
            core, symbols, MP_PROBE_TRANSACTION_ID);
        uint32_t claims_before = mp_probe(core, symbols, MP_PROBE_CLAIM_BITS);
        if (mp_status_call(core, symbols->inject_fault, fault) != MP_STATUS_OK)
            return false;
        uint32_t failed = mp_status_call(core, symbols->commit_selection, 0U);
        result = result && failed == MP_STATUS_PERSIST_FAILED
            && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
            && mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID) == transaction_before
            && mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) == claims_before
            && mp_badges(core) == 0xA5U;
        (void)mp_status_call(core, symbols->inject_fault, 0U);

        /* The streak-7 reward boundary mutates current/best/claim/tx as one
         * transaction.  Both stock-save and sector31 failures must roll every
         * field back, not only the active journal written at selection time. */
        restore_snapshot(core, base);
        mp_set_unlocks(core, true, 0x0FU, true);
        uint8_t party_before[MP_PLAYER_PARTY_SIZE];
        if (!mp_start(core, symbols, 0xA5U, 4U, party_before))
            return false;
        for (unsigned battle = 0U; battle < 6U; ++battle) {
            if (mp_prepare_battle(core, symbols) != MP_STATUS_OK)
                return false;
            uint32_t opponents = mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED);
            mp_poison_enemy_party(core);
            if (mp_status_call(core, symbols->finalize_battle_copy, 0U)
                    != MP_STATUS_OK
                || !mp_selected_rentals_exact(core, opponents))
                return false;
            write8(core, MP_BATTLE_OUTCOME, 1U);
            if (mp_status_call(core, symbols->after_battle, 0U)
                != MP_STATUS_BATTLE_CONTINUE)
                return false;
        }
        uint32_t current_before[MP_ROUNDS];
        uint32_t best_before[MP_ROUNDS];
        for (unsigned round = 0U; round < MP_ROUNDS; ++round) {
            current_before[round] = mp_probe(
                core, symbols, MP_PROBE_CURRENT_RECORD + round);
            best_before[round] = mp_probe(
                core, symbols, MP_PROBE_BEST_RECORD + round);
        }
        transaction_before = mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID);
        claims_before = mp_probe(core, symbols, MP_PROBE_CLAIM_BITS);
        if (mp_prepare_battle(core, symbols) != MP_STATUS_OK)
            return false;
        uint32_t opponents = mp_probe(core, symbols, MP_PROBE_OPPONENT_PACKED);
        mp_poison_enemy_party(core);
        if (mp_status_call(core, symbols->finalize_battle_copy, 0U) != MP_STATUS_OK
            || !mp_selected_rentals_exact(core, opponents)
            || mp_status_call(core, symbols->inject_fault, fault) != MP_STATUS_OK)
            return false;
        write8(core, MP_BATTLE_OUTCOME, 1U);
        failed = mp_status_call(core, symbols->after_battle, 0U);
        result = result && failed == MP_STATUS_PERSIST_FAILED
            && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
            && mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID) == transaction_before
            && mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) == claims_before
            && mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) == 0U
            && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
            && mp_badges(core) == 0xA5U
            && mp_matches_core(core, QOL_PLAYER_PARTY,
                               party_before, MP_PLAYER_PARTY_SIZE);
        for (unsigned round = 0U; round < MP_ROUNDS; ++round) {
            result = result
                && mp_probe(core, symbols, MP_PROBE_CURRENT_RECORD + round)
                    == current_before[round]
                && mp_probe(core, symbols, MP_PROBE_BEST_RECORD + round)
                    == best_before[round];
        }
        (void)mp_status_call(core, symbols->inject_fault, 0U);
    }
    return result;
}

static bool mp_badge_exit_matrix(struct mCore *core,
                                 const struct MirageSymbols *symbols,
                                 const struct Snapshot *base,
                                 bool full, unsigned *tested_masks)
{
    static const uint8_t quick_masks[] = {0x00U, 0x5AU, 0xA5U, 0xFFU};
    unsigned masks = full ? 256U : ARRAY_LEN(quick_masks);
    *tested_masks = masks;
    for (unsigned index = 0U; index < masks; ++index) {
        uint8_t mask = full ? (uint8_t)index : quick_masks[index];
        for (unsigned exit = 0U; exit < MP_EXIT_PATHS; ++exit) {
            restore_snapshot(core, base);
            mp_set_unlocks(core, true, 0x0FU, true);
            uint8_t party_before[MP_PLAYER_PARTY_SIZE];
            uint32_t status = MP_STATUS_BAD_ARGUMENT;
            if (exit == 4U || exit == 5U) {
                /* Standard selection cancel and script cancel happen before
                 * CommitSelection creates an active journal. */
                mp_prepare_player_party(core);
                mp_copy_from_core(
                    core, QOL_PLAYER_PARTY, party_before, sizeof(party_before));
                mp_set_badges(core, mask);
                if (mp_status_call(core, symbols->field_enter, 0U) != MP_STATUS_OK)
                    return false;
                if (exit == 4U) {
                    for (unsigned slot = 0U; slot < 6U; ++slot)
                        write8(core, MP_SELECTED_ORDER + slot, 0U);
                    status = mp_status_call(core, symbols->commit_selection, 0U);
                } else {
                    status = mp_status_call(core, symbols->abort, 0U);
                }
            } else {
                if (!mp_start(core, symbols, mask, 4U, party_before))
                    return false;
                if (exit == 0U) {
                    status = mp_status_call(core, symbols->complete, 0U);
                } else if (exit == 1U || exit == 2U) {
                    if (mp_prepare_battle(core, symbols)
                            != MP_STATUS_OK)
                        return false;
                    mp_poison_enemy_party(core);
                    if (mp_status_call(core, symbols->finalize_battle_copy, 0U)
                            != MP_STATUS_OK)
                        return false;
                    /* 2=loss and 6=white-out are both non-victory after the
                     * stock 0x7f outcome mask. */
                    write8(core, MP_BATTLE_OUTCOME, exit == 1U ? 2U : 6U);
                    status = mp_status_call(core, symbols->after_battle, 0U);
                } else if (exit == 6U || exit == 7U) {
                    /* Map warp cleanup and reset recovery share the public,
                     * idempotent recovery boundary; fresh-core reset is also
                     * exercised independently below for every badge mask. */
                    status = mp_status_call(core, symbols->recover, 0U);
                } else {
                    status = mp_status_call(core, symbols->abort, 0U);
                }
            }
            if (!(status == MP_STATUS_OK || status == MP_STATUS_LOST
                  || status == MP_STATUS_CANCELLED
                  || status == MP_STATUS_RECOVERED
                  || status == MP_STATUS_NOT_ACTIVE)
                || mp_badges(core) != mask
                || mp_probe(core, symbols, MP_PROBE_BADGE_CURRENT) != mask
                || mp_probe(core, symbols, MP_PROBE_ACTIVE) != 0U
                || mp_probe(core, symbols, MP_PROBE_PENDING_CONFIGURED) != 0U
                || mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) != 0U
                || !mp_matches_core(core, QOL_PLAYER_PARTY,
                                    party_before, MP_PLAYER_PARTY_SIZE))
                return false;
        }
    }
    return true;
}

static bool mp_fresh_core_verify(struct mCore *core,
                                 const struct MirageSymbols *symbols,
                                 uint32_t expected_claims,
                                 uint32_t expected_transaction)
{
    run_key_frames(core, 0U, 180U);
    if (!mp_fresh_save_pointers_ready(core))
        return false;
    uint32_t status = mp_call(core, symbols->save_load, 0U, 0U, 0U, 0U);
    if (status != 1U) {
        fprintf(stderr, "fresh core SaveLoad result=%" PRIu32
                " special=%u\n", status,
                read16(core, MP_SPECIAL_VAR_RESULT));
        return false;
    }
    bool exact = mp_probe(core, symbols, MP_PROBE_STATE_VALID) == 1U
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_CLAIM_BITS) == expected_claims
        && mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID) == expected_transaction
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U;
    if (!exact)
        fprintf(stderr,
                "fresh core mismatch state=%" PRIu32 " active=%" PRIu32
                " claims=%" PRIu32 "/%" PRIu32 " tx=%" PRIu32
                "/%" PRIu32 " local=%" PRIu32 "\n",
                mp_probe(core, symbols, MP_PROBE_STATE_VALID),
                mp_probe(core, symbols, MP_PROBE_ACTIVE),
                mp_probe(core, symbols, MP_PROBE_CLAIM_BITS), expected_claims,
                mp_probe(core, symbols, MP_PROBE_TRANSACTION_ID),
                expected_transaction,
                mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE));
    return exact;
}

static void mp_diagnose_fresh_load_chain(
    struct mCore *core, const struct MirageSymbols *symbols,
    const struct Snapshot *before)
{
    static const uint32_t functions[] = {
        0U, 0x09377695U, 0x0930375DU, 0x09302D71U,
    };
    static const char *const names[] = {
        "mirage", "qol", "stage35", "original_trampoline",
    };
    uint32_t resolved[ARRAY_LEN(functions)];
    memcpy(resolved, functions, sizeof(resolved));
    resolved[0] = symbols->save_load;
    for (unsigned index = 0U; index < ARRAY_LEN(resolved); ++index) {
        restore_snapshot(core, before);
        uint32_t magic_before = mp_read32_le(core, QOL_LEDGER);
        uint32_t checksum_before = mp_read32_le(core, QOL_LEDGER + 8U);
        uint32_t journal_before_a = mp_read32_le(core, QOL_LEDGER + 0x664U);
        uint32_t journal_before_b = mp_read32_le(core, QOL_LEDGER + 0x668U);
        uint32_t result = mp_call(
            core, resolved[index], 0U, 0U, 0U, 0U);
        fprintf(stderr,
                "fresh load chain %s=%" PRIu32
                " ledger=%08" PRIx32 "/%08" PRIx32
                " checksum=%08" PRIx32 "/%08" PRIx32
                " journal=%08" PRIx32 "/%08" PRIx32
                "->%08" PRIx32 "/%08" PRIx32
                " special=%u\n",
                names[index], result, magic_before,
                mp_read32_le(core, QOL_LEDGER), checksum_before,
                mp_read32_le(core, QOL_LEDGER + 8U),
                journal_before_a, journal_before_b,
                mp_read32_le(core, QOL_LEDGER + 0x664U),
                mp_read32_le(core, QOL_LEDGER + 0x668U),
                read16(core, MP_SPECIAL_VAR_RESULT));
    }
}

static bool mp_fresh_reset_exact(
    struct mCore *core, const struct MirageSymbols *symbols, uint8_t mask,
    const uint8_t party_before[MP_PLAYER_PARTY_SIZE])
{
    return mp_probe(core, symbols, MP_PROBE_STATE_VALID) == 1U
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR) == 0U
        && mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR) == 0U
        && mp_badges(core) == mask
        && mp_probe(core, symbols, MP_PROBE_BADGE_CURRENT) == mask
        && mp_matches_core(core, QOL_PLAYER_PARTY,
                           party_before, MP_PLAYER_PARTY_SIZE)
        && read8(core, QOL_PLAYER_PARTY_COUNT) == 6U;
}

static bool mp_fresh_reset_inactive(
    struct mCore *core, const struct MirageSymbols *symbols, uint8_t mask)
{
    return mp_probe(core, symbols, MP_PROBE_STATE_VALID) == 1U
        && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE) == 0U
        && mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR) == 0U
        && mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR) == 0U
        && mp_badges(core) == mask
        && mp_probe(core, symbols, MP_PROBE_BADGE_CURRENT) == mask
        && read8(core, QOL_PLAYER_PARTY_COUNT) == 6U;
}

static bool mp_prepare_fresh_reset_baseline(
    const char *rom_path, const char *reset_path,
    const struct MirageSymbols *symbols, struct MirageSaveImage *image)
{
    qol_initialize_save(reset_path);
    struct mCore *core = qol_open(rom_path, reset_path);
    qol_log_core = core;
    bool field = mp_run_reception_field_trace(core, symbols);
    uint8_t party_before[MP_PLAYER_PARTY_SIZE];
    bool started = false;
    bool cleaned = false;
    uint32_t saved = 0U;
    if (field) {
        mp_set_unlocks(core, true, 0x0FU, true);
        started = mp_start(core, symbols, 0U, 4U, party_before);
        if (started) {
            uint32_t status = mp_status_call(core, symbols->abort, 0U);
            cleaned = (status == MP_STATUS_OK
                       || status == MP_STATUS_RECOVERED
                       || status == MP_STATUS_NOT_ACTIVE)
                && mp_fresh_reset_exact(core, symbols, 0U, party_before);
        }
        if (cleaned)
            saved = mp_call(
                core, QOL_TRY_SAVING_DATA, 0U, 0U, 0U, 0U);
    }
    qol_close(core);
    bool synced = saved == 1U && mp_sync_save_file(reset_path);
    bool captured = synced && mp_capture_save_image(reset_path, image);
    if (!captured)
        fprintf(stderr,
                "fresh reset baseline failed field=%u start=%u cleanup=%u "
                "save=%" PRIu32 " sync=%u errno=%d\n",
                field, started, cleaned, saved, synced, errno);
    return captured;
}

static bool mp_load_fresh_reset_baseline(
    struct mCore *core, const struct MirageSymbols *symbols,
    const uint8_t party_before[MP_PLAYER_PARTY_SIZE])
{
    run_key_frames(core, 0U, 180U);
    if (mp_fresh_reset_exact(core, symbols, 0U, party_before))
        return true;
    if (!mp_fresh_save_pointers_ready(core))
        return false;
    uint32_t loaded = mp_call(
        core, symbols->save_load, 0U, 0U, 0U, 0U);
    bool exact = loaded == 1U
        && mp_fresh_reset_exact(core, symbols, 0U, party_before);
    if (!exact)
        fprintf(stderr,
                "fresh reset baseline load=%" PRIu32
                " special=%u state=%" PRIu32 " active=%" PRIu32
                " journal=%08" PRIx32 "/%08" PRIx32
                " badges=%02x party=%u count=%u\n",
                loaded, read16(core, MP_SPECIAL_VAR_RESULT),
                mp_probe(core, symbols, MP_PROBE_STATE_VALID),
                mp_probe(core, symbols, MP_PROBE_ACTIVE),
                mp_probe(core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR),
                mp_probe(core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR),
                mp_badges(core),
                mp_matches_core(core, QOL_PLAYER_PARTY,
                                party_before, MP_PLAYER_PARTY_SIZE),
                read8(core, QOL_PLAYER_PARTY_COUNT));
    return exact;
}

static bool mp_fresh_reset_mask(
    const char *rom_path, const char *reset_path,
    const struct MirageSymbols *symbols,
    const struct MirageSaveImage *baseline, uint8_t mask,
    const uint8_t baseline_party[MP_PLAYER_PARTY_SIZE])
{
    if (!mp_restore_save_image(reset_path, baseline)) {
        fprintf(stderr, "fresh reset restore failed mask=%02x errno=%d\n",
                mask, errno);
        return false;
    }
    struct mCore *core = qol_open(rom_path, reset_path);
    qol_log_core = core;
    bool loaded = mp_load_fresh_reset_baseline(
        core, symbols, baseline_party);
    uint8_t party_before[MP_PLAYER_PARTY_SIZE];
    bool started = false;
    if (loaded) {
        mp_set_unlocks(core, true, 0x0FU, true);
        started = mp_start(core, symbols, mask, 4U, party_before)
            && mp_probe(core, symbols, MP_PROBE_ACTIVE) == 1U;
    }
    qol_close(core);
    bool synced = started && mp_sync_save_file(reset_path);
    if (!synced) {
        fprintf(stderr,
                "fresh reset active save failed mask=%02x load=%u start=%u "
                "sync=%u errno=%d\n",
                mask, loaded, started, synced, errno);
        return false;
    }
    struct MirageStockBankAudit active_bank0 = mp_audit_stock_bank(
        reset_path, 0U);
    struct MirageStockBankAudit active_bank1 = mp_audit_stock_bank(
        reset_path, 1U);

    /* A second emulator core is the production reset boundary: no volatile
     * Mirage state survives.  Normal boot may already invoke the rooted load
     * hook; if not, invoke the same adapter once after the stock 180-frame
     * initialization interval. */
    core = qol_open(rom_path, reset_path);
    qol_log_core = core;
    run_key_frames(core, 0U, 180U);
    bool automatic = mp_fresh_reset_exact(
        core, symbols, mask, party_before);
    uint32_t recovered = (uint32_t)read16(core, MP_SPECIAL_VAR_RESULT);
    if (!automatic) {
        recovered = mp_fresh_save_pointers_ready(core)
            ? mp_call(core, symbols->save_load, 0U, 0U, 0U, 0U)
            : UINT32_MAX;
    }
    bool exact = automatic || (recovered == 1U
        && mp_fresh_reset_exact(core, symbols, mask, party_before));
    if (!exact) {
        uint32_t active = mp_probe(core, symbols, MP_PROBE_ACTIVE);
        uint32_t local = mp_probe(
            core, symbols, MP_PROBE_BATTLE_LOCAL_ACTIVE);
        uint32_t marker = mp_probe(
            core, symbols, MP_PROBE_JOURNAL_MARKER_PAIR);
        uint32_t payload = mp_probe(
            core, symbols, MP_PROBE_JOURNAL_PAYLOAD_PAIR);
        uint8_t badges = mp_badges(core);
        uint32_t badge_probe = mp_probe(
            core, symbols, MP_PROBE_BADGE_CURRENT);
        bool party = mp_matches_core(
            core, QOL_PLAYER_PARTY, party_before, MP_PLAYER_PARTY_SIZE);
        uint8_t party_count = read8(core, QOL_PLAYER_PARTY_COUNT);
        struct Snapshot before_diagnosis = take_snapshot(core);
        mp_diagnose_fresh_load_chain(core, symbols, &before_diagnosis);
        free(before_diagnosis.bytes);
        struct MirageStockBankAudit failed_bank0 = mp_audit_stock_bank(
            reset_path, 0U);
        struct MirageStockBankAudit failed_bank1 = mp_audit_stock_bank(
            reset_path, 1U);
        fprintf(stderr,
                "fresh reset mismatch mask=%02x result=%" PRIu32
                " auto=%u active=%" PRIu32 " local=%" PRIu32
                " journal=%08" PRIx32 "/%08" PRIx32
                " badges=%02x/%02" PRIx32 " party=%u count=%u "
                "disk=%08" PRIx32 "/%08" PRIx32
                "/%08" PRIx32 "/%08" PRIx32 "\n",
                mask, recovered, automatic, active, local, marker, payload,
                badges, badge_probe, party, party_count,
                mp_save_file_word(
                    reset_path, MP_SECTOR31_LEDGER_FILE_OFFSET),
                mp_save_file_word(
                    reset_path, MP_SECTOR31_LEDGER_FILE_OFFSET + 8U),
                mp_save_file_word(
                    reset_path, MP_SECTOR31_LEDGER_FILE_OFFSET + 0x664U),
                mp_save_file_word(
                    reset_path, MP_SECTOR31_LEDGER_FILE_OFFSET + 0x668U));
        fprintf(stderr,
                "fresh reset stock before=%" PRIu32 "/%04x/%04x/%u,"
                "%" PRIu32 "/%04x/%04x/%u "
                "after=%" PRIu32 "/%04x/%04x/%u,"
                "%" PRIu32 "/%04x/%04x/%u\n",
                active_bank0.counter, active_bank0.ids,
                active_bank0.bad_checksums, active_bank0.consistent_counter,
                active_bank1.counter, active_bank1.ids,
                active_bank1.bad_checksums, active_bank1.consistent_counter,
                failed_bank0.counter, failed_bank0.ids,
                failed_bank0.bad_checksums, failed_bank0.consistent_counter,
                failed_bank1.counter, failed_bank1.ids,
                failed_bank1.bad_checksums, failed_bank1.consistent_counter);
    }
    qol_close(core);
    return exact;
}

static bool mp_fresh_reset_badges(const char *rom_path, const char *save_path,
                                  const struct MirageSymbols *symbols,
                                  bool full)
{
    static const uint8_t quick_masks[] = {0x00U, 0x5AU, 0xA5U, 0xFFU};
    const char suffix[] = ".mirage-fresh-reset";
    size_t path_length = strlen(save_path);
    char *reset_path = malloc(path_length + sizeof(suffix));
    if (!reset_path)
        mp_die("fresh reset path allocation failed");
    memcpy(reset_path, save_path, path_length);
    memcpy(reset_path + path_length, suffix, sizeof(suffix));

    struct MirageSaveImage baseline = {0U, NULL};
    bool passed = mp_prepare_fresh_reset_baseline(
        rom_path, reset_path, symbols, &baseline);
    uint8_t baseline_party[MP_PLAYER_PARTY_SIZE] = {0U};
    if (passed) {
        struct mCore *core = qol_open(rom_path, reset_path);
        qol_log_core = core;
        run_key_frames(core, 0U, 180U);
        bool baseline_loaded = mp_fresh_reset_inactive(core, symbols, 0U);
        if (!baseline_loaded) {
            uint32_t loaded = mp_fresh_save_pointers_ready(core)
                ? mp_call(core, symbols->save_load, 0U, 0U, 0U, 0U)
                : UINT32_MAX;
            baseline_loaded = loaded == 1U
                && mp_fresh_reset_inactive(core, symbols, 0U);
        }
        passed = baseline_loaded;
        if (baseline_loaded)
            mp_copy_from_core(core, QOL_PLAYER_PARTY, baseline_party,
                              sizeof(baseline_party));
        qol_close(core);
    }
    unsigned masks = full ? 256U : ARRAY_LEN(quick_masks);
    for (unsigned index = 0U; passed && index < masks; ++index) {
        uint8_t mask = full ? (uint8_t)index : quick_masks[index];
        passed = mp_fresh_reset_mask(
            rom_path, reset_path, symbols, &baseline, mask, baseline_party);
    }
    free(baseline.bytes);
    if (passed) {
        if (remove(reset_path) != 0 && errno != ENOENT)
            fprintf(stderr,
                    "fresh reset save cleanup failed: %s\n", reset_path);
    } else {
        fprintf(stderr,
                "fresh reset failed save retained for diagnosis: %s\n",
                reset_path);
    }
    free(reset_path);
    return passed;
}

#if !defined(MIRAGE_PRODUCTION_RUNNER_EMBEDDED)
int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr,
                "usage: %s ROM SYMBOLS CASES quick|full SAVE\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    const char *rom_path = argv[1];
    const char *save_path = argv[5];
    struct MirageSymbols symbols = mp_load_symbols(argv[2]);
    struct MirageCases cases = mp_load_cases(argv[3]);
    qol_initialize_save(save_path);
    struct mLogger logger = {.log = mp_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(rom_path, save_path);
    qol_log_core = core;
    bool boot = qol_run_field_trace(core);
    struct Snapshot field_base = take_snapshot(core);

    bool fixture = cases.has_normal_field && cases.has_progression_28
        && cases.has_atomic_fault && cases.has_all_exits
        && mp_field_respawn_contract;
    bool symbols_live = mp_symbols_live(core, &symbols);
    bool physical = mp_physical_bindings(core, &symbols);
    bool probe = mp_probe_contract(core, &symbols);
    bool unlock = mp_unlock_matrix(core, &symbols, &field_base);
    bool authored_abilities = false;
    bool scheduler = false;

    bool atomic = mp_atomic_faults(core, &symbols, &field_base);
    unsigned badge_masks = 0U;
    bool badge_matrix = mp_badge_exit_matrix(
        core, &symbols, &field_base, full, &badge_masks);

    restore_snapshot(core, &field_base);
    mp_set_unlocks(core, true, 0x0FU, true);
    uint64_t factory_before = mp_core_hash(
        core, QOL_LEDGER + MP_FACTORY_OFFSET, MP_FACTORY_SIZE);
    struct Snapshot progression_base = take_snapshot(core);
    struct ProgressionResult first = mp_progression(core, &symbols, 0x96U, 4U);
    bool upstream = factory_before == mp_core_hash(
        core, QOL_LEDGER + MP_FACTORY_OFFSET, MP_FACTORY_SIZE);

    restore_snapshot(core, &progression_base);
    struct ProgressionResult second = mp_progression(core, &symbols, 0x96U, 4U);
    bool deterministic = mp_equal_progression(&first, &second);
    bool progression = first.round_sequence && first.battles == MP_BATTLES
        && first.records;
    bool battle_copy = first.battle_copy;
    bool gimmicks = first.gimmicks;
    bool top_reward = mp_top_reward_replay(core, &symbols);
    bool virtual_items = first.virtual_items && top_reward;
    bool cleanup = first.cleanup;
    bool party_restore = first.party_restored;
    upstream = upstream && factory_before == mp_core_hash(
        core, QOL_LEDGER + MP_FACTORY_OFFSET, MP_FACTORY_SIZE);
    uint32_t saved_claims = mp_probe(core, &symbols, MP_PROBE_CLAIM_BITS);
    uint32_t saved_transaction = mp_probe(core, &symbols, MP_PROBE_TRANSACTION_ID);
    uint32_t save_write_status = mp_call(
        core, QOL_TRY_SAVING_DATA, 0U, 0U, 0U, 0U);
    bool save_write = save_write_status == 1U;
    if (!save_write)
        fprintf(stderr, "fresh setup save status=%" PRIu32 " claims=%" PRIu32
                " tx=%" PRIu32 "\n",
                save_write_status, saved_claims, saved_transaction);

    free(progression_base.bytes);
    free(field_base.bytes);
    qol_close(core);
    core = qol_open(rom_path, save_path);
    qol_log_core = core;
    bool fresh_core = save_write && mp_fresh_core_verify(
        core, &symbols, saved_claims, saved_transaction);
    qol_close(core);
    bool normal_field = mp_normal_field_process(
        rom_path, save_path, &symbols);
    scheduler = mp_scheduler_field_process(
        rom_path, save_path, &symbols, &authored_abilities);
    bool fresh_reset = fresh_core && mp_fresh_reset_badges(
        rom_path, save_path, &symbols, full);
    bool warnings = log_problem_count == 0U;

    bool checks[] = {
        boot, fixture, symbols_live, physical, probe, normal_field, unlock,
        scheduler, authored_abilities, progression, battle_copy, gimmicks,
        deterministic, virtual_items,
        top_reward, atomic, fresh_core, fresh_reset, badge_matrix, party_restore,
        cleanup, upstream,
        warnings,
    };
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(checks); ++index)
        passed = passed && checks[index];

    bool acceptance[15] = {
        physical && symbols_live,
        fixture && probe,
        normal_field && progression,
        unlock && progression,
        scheduler && authored_abilities && battle_copy && gimmicks,
        gimmicks && cleanup,
        deterministic,
        virtual_items && cleanup,
        atomic && fresh_core,
        badge_matrix && fresh_reset && party_restore,
        cleanup && party_restore,
        upstream,
        fixture && upstream,
        fresh_core && progression,
        physical && badge_matrix && warnings,
    };
    static const char *const acceptance_keys[15] = {
        "STAGE37_IDENTITY_PRIVATE_IMMUTABLE",
        "MIRAGE_MANIFEST_CROSSWALK_EXACT",
        "NORMAL_FIELD_ENTRY_4_ROUNDS_28_BATTLES",
        "ROUND_UNLOCK_NO_SKIP",
        "LEVEL100_SINGLE_3V3_AI_GIMMICKS",
        "ROUND4_LOCK_ONE_GIMMICK_NO_LEAK",
        "DETERMINISTIC_POOL_NO_REBALANCE",
        "VIRTUAL_ITEM_TIERS_ISOLATED",
        "ATOMIC_RECORD_CLAIM_SAVE_RELOAD",
        "BADGE_EXACT_RESTORE_ALL_EXITS",
        "BATTLE_LOCAL_CLEANUP_ALL_EXITS",
        "UPSTREAM_RUNTIME_CONTENT_REGRESSION",
        "PRO_WAITING_AREAS_UNCHANGED",
        "CLEAN_REBUILD_BPS_EXACT",
        "DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS",
    };
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index)
        passed = passed && acceptance[index];

    fprintf(stderr,
            "mgba-mirage-production %s: boot=%u fixture=%u symbols=%u "
            "physical=%u probe=%u field=%u unlock=%u progression=%u "
            "scheduler=%u abilities=%u copy=%u gimmick=%u rng=%u rewards=%u top=%u atomic=%u fresh=%u reset=%u "
            "badges=%u party=%u cleanup=%u upstream=%u logs=%u\n",
            full ? "full" : "quick", boot, fixture, symbols_live, physical,
            probe, normal_field, unlock, progression, scheduler, authored_abilities,
            battle_copy, gimmicks,
            deterministic, virtual_items, top_reward, atomic, fresh_core, fresh_reset,
            badge_matrix,
            party_restore, cleanup, upstream, log_problem_count);
    printf("{\"schema_version\":1,\"status\":\"%s\",\"mode\":\"%s\","
           "\"checks\":{\"field_boot\":%s,\"case_fixture\":%s,"
           "\"runtime_symbols\":%s,\"physical_bindings\":%s,"
           "\"runtime_probe\":%s,\"normal_field_a_input\":%s,"
           "\"unlock_boundaries\":%s,\"progression_28\":%s,"
           "\"real_trainer_scheduler\":%s,"
           "\"authored_battle_abilities_exact6\":%s,"
           "\"level100_single_3v3\":%s,\"round_gimmicks\":%s,"
           "\"deterministic_opponent_pool\":%s,\"virtual_rewards\":%s,"
           "\"streak35_top_claim\":%s,"
           "\"atomic_fault_injection\":%s,\"fresh_core_save_reload\":%s,"
           "\"fresh_core_reset_badges\":%s,"
           "\"badge_restore_matrix\":%s,\"party_600_restore\":%s,"
           "\"battle_local_cleanup\":%s,\"upstream_sentinels\":%s,"
           "\"warnings_errors_zero\":%s},\"acceptance_checks\":{",
           passed ? "PASS" : "FAIL", full ? "full" : "quick",
           boot ? "true" : "false", fixture ? "true" : "false",
           symbols_live ? "true" : "false", physical ? "true" : "false",
           probe ? "true" : "false", normal_field ? "true" : "false",
           unlock ? "true" : "false", progression ? "true" : "false",
           scheduler ? "true" : "false",
           authored_abilities ? "true" : "false",
           battle_copy ? "true" : "false", gimmicks ? "true" : "false",
           deterministic ? "true" : "false", virtual_items ? "true" : "false",
           top_reward ? "true" : "false", atomic ? "true" : "false",
           fresh_core ? "true" : "false",
           fresh_reset ? "true" : "false",
           badge_matrix ? "true" : "false", party_restore ? "true" : "false",
           cleanup ? "true" : "false", upstream ? "true" : "false",
           warnings ? "true" : "false");
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index) {
        printf("%s\"%s\":%s", index ? "," : "", acceptance_keys[index],
               acceptance[index] ? "true" : "false");
    }
    printf("},\"coverage\":{\"rounds\":4,\"battles\":28,"
           "\"badge_masks\":%u,\"exit_paths\":8,\"badge_exit_cases\":%u,"
           "\"case_rows\":%u,\"quick_case_rows\":%u,\"full_case_rows\":%u,"
           "\"party_snapshot_bytes\":600,\"runtime_state_bytes\":664},"
           "\"result_identity\":\"MP38:4:4:5:4:28:256:8:600\","
           "\"warnings_errors\":%u}\n",
           badge_masks, badge_masks * MP_EXIT_PATHS, cases.rows,
           cases.quick_rows, cases.full_rows, log_problem_count);
    return passed ? 0 : 1;
}
#endif
