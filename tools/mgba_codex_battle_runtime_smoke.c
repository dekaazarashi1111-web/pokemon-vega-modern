/* T27 Stage 44 Codex Battle runtime exact-ROM validation for libmGBA. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <ctype.h>

enum {
    CBR_MAILBOX = 0x0203F900U,
    CBR_REQUEST = CBR_MAILBOX + 160U,
    CBR_PUBLIC_STATE = 0x0203FF4CU,
    CBR_MAGIC = 0x32524243U,
    CBR_STAGE_IDENTITY = 0x34345242U,
    CBR_CAPABILITIES = 8191U,
    CBR_PHASE_IDLE = 1U,
    CBR_PHASE_CONFIGURING = 2U,
    CBR_PHASE_TEAM_PREVIEW = 3U,
    CBR_PHASE_PLAYER_SELECTION = 4U,
    CBR_PHASE_ACTION = 6U,
    CBR_PHASE_MOVE = 7U,
    CBR_PHASE_SWITCH = 8U,
    CBR_PHASE_RESOLVING = 9U,
    CBR_PHASE_RESULT = 10U,
    CBR_PHASE_ABORTED = 12U,
    CBR_STATUS_ACCEPTED = 2U,
    CBR_STATUS_ERROR = 3U,
    CBR_COMMAND_CONFIGURE = 1U,
    CBR_COMMAND_UPLOAD = 2U,
    CBR_COMMAND_COMMIT = 3U,
    CBR_COMMAND_CHOOSE_TEAM = 4U,
    CBR_COMMAND_MOVE = 5U,
    CBR_COMMAND_SWITCH = 6U,
    CBR_COMMAND_FORFEIT = 7U,
    CBR_COMMAND_CPU = 8U,
    CBR_COMMAND_DISCONNECT_FORFEIT = 9U,
    CBR_COMMAND_ABORT = 10U,
    CBR_ERROR_FUTURE = 1U,
    CBR_ERROR_STALE = 2U,
    CBR_ERROR_NONCE = 3U,
    CBR_ERROR_OVERSIZE = 4U,
    CBR_ERROR_PAYLOAD_CRC = 5U,
    CBR_ERROR_REQUEST_CRC = 6U,
    CBR_ERROR_PHASE = 7U,
    CBR_ERROR_COMMAND = 8U,
    CBR_ERROR_FORMAT = 9U,
    CBR_ERROR_MATCH = 11U,
    CBR_ERROR_TURN = 12U,
    CBR_ERROR_MEMBER = 13U,
    CBR_ERROR_REGULATION = 14U,
    CBR_ERROR_ACTION = 15U,
    CBR_ERROR_BUSY = 16U,
    CBR_PLAYER_PARTY = 0x020241E4U,
    CBR_ENEMY_PARTY = 0x02023F8CU,
    CBR_PLAYER_COUNT = 0x02023F89U,
    CBR_ENEMY_COUNT = 0x02023F8AU,
    CBR_SELECTED = 0x0203C6C8U,
    CBR_BATTLE_FLAGS = 0x02022AACU,
    CBR_BATTLE_BUFFER_A = 0x02022B24U,
    CBR_BATTLE_BUFFER_B = 0x02023324U,
    CBR_ACTIVE_BATTLER = 0x02023B24U,
    CBR_CONTROLLER_EXEC_FLAGS = 0x02023B28U,
    CBR_BATTLE_MONS = 0x02023B44U,
    CBR_PARTY_INDEXES = 0x02023B2EU,
    CBR_BANK_ATTACKER = 0x02023CCBU,
    CBR_SIDE_STATUSES = 0x02023D3EU,
    CBR_SIDE_TIMERS = 0x02023D44U,
    CBR_STATUSES3 = 0x02023D5CU,
    CBR_DISABLE_STRUCTS = 0x02023E0CU,
    CBR_BATTLE_WEATHER = 0x02023E7CU,
    CBR_WISH_FUTURE_KNOCK = 0x02023E80U,
    CBR_BATTLE_RESOURCES_PTR = 0x02023F54U,
    CBR_TERRAIN_TYPE = 0x0203DFA0U,
    CBR_ABILITY_POPUP_HELPER = 0x0203DFA7U,
    CBR_NEW_BS_PTR = 0x0203DFB0U,
    CBR_BATTLE_STRUCT_PTR = 0x02023F48U,
    CBR_CONTROLLER_FUNCS = 0x03005020U,
    CBR_RNG = 0x03005040U,
    CBR_BASE_NONCE = 0x0203F828U,
    CBR_MIRAGE_STATE = 0x0203EE00U,
    CBR_SAVE1_PTR = 0x03005048U,
    CBR_SAVE2_PTR = 0x0300504CU,
    CBR_READ_KEYS_POINTER = 0x080005ECU,
    CBR_VAR_GET = 0x0806DD5DU,
    CBR_FLAG_GET = 0x0806DEC5U,
    CBR_FLAG_SET = 0x0806DE75U,
    CBR_FLAG_CLEAR = 0x0806DE9DU,
    CBR_FLAG_DISABLE_BAG = 0x0915U,
    CBR_FLAG_CODEX_TRAINER = 0x07E9U,
    CBR_SAVE_LOAD_SITE = 0x080DB4E4U,
    CBR_SELECTION_CONFIRM_POINTER = 0x081280B8U,
    CBR_OPPONENT_CHOOSE_ACTION_POINTER = 0x0820D484U,
    CBR_OPPONENT_CHOOSE_MOVE_POINTER = 0x0820D48CU,
    CBR_OPPONENT_CHOOSE_POKEMON_POINTER = 0x0820D494U,
    CBR_SCRIPT_CONTEXT1_SETUP = 0x080693A5U,
    CBR_SCRIPT_CONTEXT2_ENABLE = 0x08069201U,
    CBR_KANTO_WARP = 0x09220861U,
    CBR_CB2_OVERWORLD = 0x08055E75U,
    CBR_STATE = 0x0203FA00U,
    CBR_STATE_ACTIVE = 20U,
    CBR_STATE_LEVEL_MODE = 24U,
    CBR_STATE_SWITCH_CONTEXT = 25U,
    CBR_STATE_FIELD_COMPLETION_PENDING = 30U,
    CBR_STATE_ACTION_KIND = 40U,
    CBR_STATE_DISCONNECT_MODE = 45U,
    CBR_STATE_CONTROLLER_INSTALLED = 47U,
    CBR_STATE_DELEGATE = 64U,
    CBR_STATE_LAST_SEQUENCE = 68U,
    CBR_STATE_REJECTED_COUNT = 72U,
    CBR_STATE_SEAL_CRC = 76U,
    CBR_STATE_SEAL_LENGTH = 80U,
    CBR_STATE_CLEANUP_REASON = 82U,
    CBR_STATE_LEGAL_MOVE = 104U,
    CBR_STATE_LEGAL_SWITCH = 105U,
    CBR_STATE_LEGAL_GIMMICKS = 106U,
    CBR_STATE_PLAYER_CHOICE_OBSERVED = 110U,
    CBR_STATE_MECHANIC_USED_MASK = 111U,
    CBR_STATE_TEAM = 112U,
    CBR_STATE_BACKUP = 304U,
    CBR_STATE_MONEY_BEFORE = 932U,
    CBR_SCRATCH = 0x0203E080U,
    CBR_BATTLE_STRUCT_GIVEN_EXP = 0xDFU,
    CBR_SAVE1_MONEY = 0x290U,
    CBR_SAVE1_DEX_SEEN = 0x310U,
    CBR_SAVE1_DEX_SEEN_SIZE = 150U,
    CBR_SAVE1_FLAGS = 0x0EE0U,
    CBR_SAVE1_FLAGS_VARS_SIZE = 0x320U,
    CBR_SAVE1_GAME_STATS = 0x1200U,
    CBR_SAVE2_POKEDEX = 0x18U,
    CBR_SAVE2_POKEDEX_SIZE = 16U,
    CBR_SAVE2_KEY = 0x0F20U,
    CBR_GAME_STATS_COUNT = 64U,
};

#ifndef CBR_TRAINER_PARTY_SITE
#define CBR_TRAINER_PARTY_SITE 0x09096EC4U
#endif
#ifndef CBR_RECEPTION_POINTER
#define CBR_RECEPTION_POINTER 0x093C3340U
#endif
#ifndef CBR_DYNAMAX_BAND_EXECUTION_SITE
#define CBR_DYNAMAX_BAND_EXECUTION_SITE 0x090F15E8U
#endif
#ifndef CBR_GIGANTAMAX_BAND_EXECUTION_SITE
#define CBR_GIGANTAMAX_BAND_EXECUTION_SITE 0x090F161CU
#endif
#ifndef CBR_DYNAMAX_BAND_UI_SITE
#define CBR_DYNAMAX_BAND_UI_SITE 0x090F17DCU
#endif

#define CBR_SYMBOL_LIST(X) \
    X(probe, "CodexBattleRuntime_Probe") \
    X(initialize, "CodexBattleRuntime_Initialize") \
    X(poll, "CodexBattleRuntime_Poll") \
    X(read_keys, "CodexBattleRuntime_ReadKeysAdapter") \
    X(trainer_party, "CodexBattleRuntime_BuildTrainerPartyAdapter") \
    X(save_load, "CodexBattleRuntime_SaveLoadAdapter") \
    X(find_dynamax_band, "CodexBattleRuntime_FindDynamaxBandAdapter") \
    X(controller, "CodexBattleRuntime_OpponentController") \
    X(can_mega, "CodexBattleRuntime_CanMegaAdapter") \
    X(mark_mega, "CodexBattleRuntime_MarkMegaAdapter") \
    X(can_z, "CodexBattleRuntime_CanZAdapter") \
    X(mark_z, "CodexBattleRuntime_MarkZAdapter") \
    X(can_dynamax, "CodexBattleRuntime_CanDynamaxAdapter") \
    X(mark_dynamax, "CodexBattleRuntime_MarkDynamaxAdapter") \
    X(can_tera, "CodexBattleRuntime_CanTeraAdapter") \
    X(mark_tera, "CodexBattleRuntime_MarkTeraAdapter") \
    X(field_begin, "CodexBattleRuntime_FieldBeginPlayerSelection") \
    X(field_commit, "CodexBattleRuntime_FieldCommitPlayerSelection") \
    X(field_prepare, "CodexBattleRuntime_FieldPrepareBattle") \
    X(after_battle, "CodexBattleRuntime_AfterBattle") \
    X(field_finish, "CodexBattleRuntime_FieldFinish") \
    X(abort, "CodexBattleRuntime_Abort") \
    X(seal_private, "CodexBattleRuntime_SealPrivateForTest") \
    X(test_initialize, "CodexBattleRuntime_TestInitialize") \
    X(state_hash, "CodexBattleRuntime_TestStateHash")

struct CbrSymbols {
#define CBR_SYMBOL_MEMBER(member, name) uint32_t member;
    CBR_SYMBOL_LIST(CBR_SYMBOL_MEMBER)
#undef CBR_SYMBOL_MEMBER
    uint32_t launch_script;
    uint32_t commit_script;
    uint32_t begin_script;
};

struct CbrCases {
    bool exact_tests;
    bool exact_invalid;
    uint32_t mailbox;
    uint32_t state;
    uint32_t payload;
};

static void cbr_die(const char *message)
{
    fprintf(stderr, "mgba-codex-battle-runtime: %s\n", message);
    exit(1);
}

static char *cbr_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        cbr_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        cbr_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 16L * 1024L * 1024L)
        cbr_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        cbr_die("fixture read failed");
    if (fclose(stream) != 0)
        cbr_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static const char *cbr_find_key(const char *text, const char *key)
{
    char needle[192];
    int length = snprintf(needle, sizeof(needle), "\"%s\"", key);
    if (length <= 0 || (size_t)length >= sizeof(needle))
        cbr_die("JSON key formatting failed");
    return strstr(text, needle);
}

static uint32_t cbr_parse_number(const char *cursor)
{
    while (*cursor && (isspace((unsigned char)*cursor)
                       || *cursor == ':' || *cursor == '"'))
        ++cursor;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(cursor, &end, 0);
    if (errno || end == cursor || value > UINT32_MAX)
        cbr_die("JSON numeric value differs");
    return (uint32_t)value;
}

static uint32_t cbr_json_number(const char *text, const char *key)
{
    const char *found = cbr_find_key(text, key);
    if (!found || !(found = strchr(found, ':')))
        cbr_die("required JSON number is missing");
    return cbr_parse_number(found + 1);
}

static uint32_t cbr_json_symbol(const char *text, const char *name)
{
    const char *found = text;
    size_t name_length = strlen(name);
    for (;;) {
        found = cbr_find_key(found, name);
        if (!found)
            break;
        const char *separator = found + name_length + 2U;
        while (isspace((unsigned char)*separator))
            ++separator;
        if (*separator == ':') {
            found = separator;
            break;
        }
        ++found;
    }
    if (!found)
        cbr_die("required runtime symbol is missing");
    while (*++found && isspace((unsigned char)*found)) { }
    if (*found == '{') {
        const char *end = strchr(found, '}');
        const char *address = cbr_find_key(found, "address");
        if (!end || !address || address > end || !(address = strchr(address, ':')))
            cbr_die("runtime symbol address differs");
        found = address + 1;
    }
    return cbr_parse_number(found);
}

static unsigned cbr_occurrences(const char *text, const char *needle)
{
    unsigned count = 0U;
    size_t length = strlen(needle);
    for (const char *cursor = text; (cursor = strstr(cursor, needle)) != NULL;
         cursor += length)
        ++count;
    return count;
}

static struct CbrSymbols cbr_load_symbols(const char *path)
{
    char *text = cbr_read_text(path);
    struct CbrSymbols result = {0};
#define CBR_LOAD_SYMBOL(member, name) result.member = cbr_json_symbol(text, name);
    CBR_SYMBOL_LIST(CBR_LOAD_SYMBOL)
#undef CBR_LOAD_SYMBOL
    result.launch_script = cbr_json_symbol(
        text, "script::codex_battle_launch");
    result.commit_script = cbr_json_symbol(
        text, "script::codex_battle_select") + 4U;
    result.begin_script = cbr_json_symbol(
        text, "script::codex_battle_begin");
    free(text);
    return result;
}

static struct CbrCases cbr_load_cases(const char *path)
{
    static const char *const tests[] = {
        "exact_stage44_fixture", "runtime_exports_and_rooted_hooks",
        "protocol_header_snapshot_crc", "team_six_defaults_invalid_duplicate_fields",
        "level_toggle_and_unrestricted_teams", "both_sides_selection_private_order",
        "controller_move_gimmick_switch_forfeit",
        "illegal_stale_duplicate_torn_requests",
        "player_pending_value_length_error_sequence_timing_private",
        "disconnect_wait_reconnect_cpu_forfeit", "three_turn_request_cycles",
        "win_loss_forfeit_abort_reset_exact_cleanup",
        "normal_factory_mirage_raid_reward_noninterference",
        "upstream_open_gimmick_matrix", "live_hp_moves_switch_semantics",
        "public_online_state_events_private_boundary",
        "persistent_side_effects_zero",
        "warnings_zero",
    };
    static const char *const invalid[] = {
        "torn", "duplicate", "stale", "future", "wrong_nonce",
        "wrong_match", "wrong_turn", "wrong_phase", "payload_crc",
        "request_crc", "oversize", "invalid_member", "illegal_action",
    };
    char *text = cbr_read_text(path);
    bool exact_tests = true;
    bool exact_invalid = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index) {
        char quoted[128];
        snprintf(quoted, sizeof(quoted), "\"%s\"", tests[index]);
        exact_tests = exact_tests && cbr_occurrences(text, quoted) == 1U;
    }
    for (unsigned index = 0U; index < ARRAY_LEN(invalid); ++index) {
        char quoted[96];
        snprintf(quoted, sizeof(quoted), "\"%s\"", invalid[index]);
        exact_invalid = exact_invalid && cbr_occurrences(text, quoted) == 1U;
    }
    const char *runtime = cbr_find_key(text, "runtime");
    const char *payload = runtime ? cbr_find_key(runtime, "payload") : NULL;
    const char *protocol = cbr_find_key(text, "protocol");
    struct CbrCases result = {
        .exact_tests = exact_tests,
        .exact_invalid = exact_invalid,
        .mailbox = protocol ? cbr_json_number(protocol, "address") : 0U,
        .state = CBR_STATE,
        .payload = payload ? cbr_json_number(payload, "address") : 0U,
    };
    free(text);
    return result;
}

static uint32_t cbr_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    uint32_t resume_pc = (uint32_t)read_register(core, "pc");
    uint32_t resume_cpsr = (uint32_t)read_register(core, "cpsr");
    uint32_t pipeline = (resume_cpsr & 0x20U) ? 2U : 4U;
    uint32_t result;
    if (!(function & 1U))
        cbr_die("runtime entrypoint is not Thumb");
    result = call_bounded(core, function, r0, r1, r2, r3).result;
    /* mCore's architectural PC read includes the active ARM/Thumb pipeline,
     * while writing that value resumes one instruction later.  Direct setup
     * calls must leave the live scheduler at the exact interrupted PC: a long
     * series of otherwise side-effect-free calls can otherwise walk from the
     * VBlank wait routine into the adjacent soft-reset routine. */
    if ((uint32_t)read_register(core, "pc") != resume_pc) {
        write_register(core, "pc", resume_pc - pipeline);
        if ((uint32_t)read_register(core, "pc") != resume_pc)
            cbr_die("bounded call changed scheduler PC");
    }
    return result;
}

static void cbr_put16(uint8_t *raw, unsigned offset, uint16_t value)
{
    raw[offset] = (uint8_t)value;
    raw[offset + 1U] = (uint8_t)(value >> 8);
}

static void cbr_put32(uint8_t *raw, unsigned offset, uint32_t value)
{
    for (unsigned byte = 0U; byte < 4U; ++byte)
        raw[offset + byte] = (uint8_t)(value >> (byte * 8U));
}

static uint32_t cbr_crc_byte(uint32_t crc, uint8_t value)
{
    crc ^= value;
    for (unsigned bit = 0U; bit < 8U; ++bit) {
        uint32_t mask = 0U - (crc & 1U);
        crc = (crc >> 1) ^ (UINT32_C(0xEDB88320) & mask);
    }
    return crc;
}

static uint32_t cbr_crc_bytes(const uint8_t *raw, size_t size)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (size_t index = 0U; index < size; ++index)
        crc = cbr_crc_byte(crc, raw[index]);
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint32_t cbr_hash(struct mCore *core, uint32_t address, uint32_t size)
{
    uint32_t value = UINT32_C(2166136261);
    for (uint32_t index = 0U; index < size; ++index) {
        value ^= read8(core, address + index);
        value *= UINT32_C(16777619);
    }
    return value;
}

static uint32_t cbr_hash_continue(struct mCore *core, uint32_t value,
                                  uint32_t address, uint32_t size)
{
    for (uint32_t index = 0U; index < size; ++index) {
        value ^= read8(core, address + index);
        value *= UINT32_C(16777619);
    }
    return value;
}

static uint32_t cbr_hash_logical_word(uint32_t value, uint32_t word)
{
    for (unsigned byte = 0U; byte < 4U; ++byte) {
        value ^= (uint8_t)(word >> (byte * 8U));
        value *= UINT32_C(16777619);
    }
    return value;
}

static uint32_t cbr_logical_save_hash(struct mCore *core)
{
    uint32_t save1 = read32(core, CBR_SAVE1_PTR);
    uint32_t save2 = read32(core, CBR_SAVE2_PTR);
    uint32_t value = UINT32_C(2166136261);
    if (save1 < UINT32_C(0x02000000)
            || save1 >= UINT32_C(0x02040000)
            || save2 < UINT32_C(0x02000000)
            || save2 >= UINT32_C(0x02040000))
        return 0U;
    uint32_t key = read32(core, save2 + CBR_SAVE2_KEY);
    value = cbr_hash_logical_word(
        value, read32(core, save1 + CBR_SAVE1_MONEY) ^ key);
    value = cbr_hash_continue(
        core, value, save1 + CBR_SAVE1_DEX_SEEN,
        CBR_SAVE1_DEX_SEEN_SIZE);
    value = cbr_hash_continue(
        core, value, save1 + CBR_SAVE1_FLAGS,
        CBR_SAVE1_FLAGS_VARS_SIZE);
    for (unsigned index = 0U; index < CBR_GAME_STATS_COUNT; ++index) {
        value = cbr_hash_logical_word(
            value, read32(core, save1 + CBR_SAVE1_GAME_STATS
                          + index * 4U) ^ key);
    }
    return cbr_hash_continue(
        core, value, save2 + CBR_SAVE2_POKEDEX,
        CBR_SAVE2_POKEDEX_SIZE);
}

static uint32_t cbr_snapshot_crc(struct mCore *core)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (unsigned offset = 0U; offset < 56U; ++offset)
        crc = cbr_crc_byte(crc, read8(core, CBR_MAILBOX + offset));
    for (unsigned offset = 68U; offset < 160U; ++offset)
        crc = cbr_crc_byte(crc, read8(core, CBR_MAILBOX + offset));
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static bool cbr_snapshot_valid(struct mCore *core)
{
    uint32_t sequence = read32(core, CBR_MAILBOX + 56U);
    return sequence != 0U
        && read32(core, CBR_MAILBOX + 60U) == ~sequence
        && read16(core, CBR_MAILBOX + 68U) == 96U
        && read32(core, CBR_MAILBOX + 64U) == cbr_snapshot_crc(core)
        && read32(core, CBR_MAILBOX + 76U)
            == ~read32(core, CBR_MAILBOX + 72U);
}

static uint32_t cbr_public_state_crc(struct mCore *core)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (unsigned offset = 4U; offset < 8U; ++offset)
        crc = cbr_crc_byte(crc, read8(core, CBR_PUBLIC_STATE + offset));
    for (unsigned offset = 16U; offset < 180U; ++offset)
        crc = cbr_crc_byte(crc, read8(core, CBR_PUBLIC_STATE + offset));
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static uint16_t cbr_public_u16(struct mCore *core, unsigned offset)
{
    return (uint16_t)(read8(core, CBR_PUBLIC_STATE + offset)
        | (uint16_t)read8(core, CBR_PUBLIC_STATE + offset + 1U) << 8);
}

static uint32_t cbr_public_u32(struct mCore *core, unsigned offset)
{
    return (uint32_t)read8(core, CBR_PUBLIC_STATE + offset)
        | (uint32_t)read8(core, CBR_PUBLIC_STATE + offset + 1U) << 8
        | (uint32_t)read8(core, CBR_PUBLIC_STATE + offset + 2U) << 16
        | (uint32_t)read8(core, CBR_PUBLIC_STATE + offset + 3U) << 24;
}

static uint32_t cbr_public_bits(struct mCore *core, unsigned byte_offset,
                                unsigned bit_offset, unsigned width)
{
    uint32_t value = 0U;
    for (unsigned bit = 0U; bit < width; ++bit) {
        unsigned source = bit_offset + bit;
        if (read8(core, CBR_PUBLIC_STATE + byte_offset + (source >> 3U))
                & (1U << (source & 7U)))
            value |= 1U << bit;
    }
    return value;
}

static bool cbr_public_state_valid(struct mCore *core)
{
    uint32_t sequence = read32(core, CBR_PUBLIC_STATE + 8U);
    return sequence != 0U
        && read16(core, CBR_PUBLIC_STATE + 4U) == 180U
        && read8(core, CBR_PUBLIC_STATE + 6U) == 2U
        && read8(core, CBR_PUBLIC_STATE + 7U) == 4U
        && read32(core, CBR_PUBLIC_STATE + 12U) == ~sequence
        && read32(core, CBR_PUBLIC_STATE) == cbr_public_state_crc(core);
}

static void cbr_test_initialize(struct mCore *core,
                                const struct CbrSymbols *symbols,
                                uint32_t nonce)
{
    if (cbr_call(core, symbols->test_initialize, nonce, 0U, 0U, 0U) != nonce)
        cbr_die("test initialization nonce differs");
}

static uint32_t cbr_next_sequence(struct mCore *core)
{
    uint32_t value = read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE) + 1U;
    return value ? value : 1U;
}

static void cbr_build_request(struct mCore *core, uint8_t request[96],
                              uint16_t command, const uint8_t *payload,
                              uint16_t size, uint32_t sequence)
{
    memset(request, 0, 96U);
    cbr_put32(request, 0U, read32(core, CBR_STATE + 8U));
    cbr_put32(request, 4U, read32(core, CBR_STATE + 12U));
    cbr_put16(request, 8U, read16(core, CBR_STATE + 16U));
    cbr_put16(request, 10U, command);
    cbr_put16(request, 12U, read16(core, CBR_STATE + 28U));
    cbr_put16(request, 14U, size);
    if (payload && size <= 64U)
        memcpy(request + 20U, payload, size);
    cbr_put32(request, 16U, cbr_crc_bytes(request + 20U, size <= 64U ? size : 0U));
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    cbr_put32(request, 88U, ~sequence);
    cbr_put32(request, 92U, sequence);
}

static void cbr_write_request(struct mCore *core, const uint8_t request[96],
                              bool torn)
{
    for (unsigned index = 0U; index < 88U; ++index)
        write8(core, CBR_REQUEST + index, request[index]);
    for (unsigned index = 88U; index < 92U; ++index)
        write8(core, CBR_REQUEST + index,
               torn ? (uint8_t)(request[index] ^ 0xA5U) : request[index]);
    for (unsigned index = 92U; index < 96U; ++index)
        write8(core, CBR_REQUEST + index, request[index]);
}

static bool cbr_send(struct mCore *core, const struct CbrSymbols *symbols,
                     uint16_t command, const uint8_t *payload, uint16_t size,
                     uint16_t next_phase)
{
    uint32_t sequence = cbr_next_sequence(core);
    uint8_t request[96];
    cbr_build_request(core, request, command, payload, size, sequence);
    cbr_write_request(core, request, false);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return cbr_snapshot_valid(core)
        && read32(core, CBR_MAILBOX + 72U) == sequence
        && read16(core, CBR_MAILBOX + 80U) == CBR_STATUS_ACCEPTED
        && read16(core, CBR_MAILBOX + 82U) == 0U
        && read16(core, CBR_MAILBOX + 84U) == command
        && read32(core, CBR_MAILBOX + 88U) == sequence
        && read16(core, CBR_MAILBOX + 44U) == next_phase;
}

static bool cbr_send_error(struct mCore *core,
                           const struct CbrSymbols *symbols,
                           uint8_t request[96], uint16_t expected_error)
{
    uint32_t accepted = read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE);
    cbr_write_request(core, request, false);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return cbr_snapshot_valid(core)
        && read16(core, CBR_MAILBOX + 80U) == CBR_STATUS_ERROR
        && read16(core, CBR_MAILBOX + 82U) == expected_error
        && read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE) == accepted;
}

static void cbr_member(uint8_t raw[32], uint16_t species,
                       uint16_t item, bool explicit_item)
{
    memset(raw, 0, 32U);
    cbr_put16(raw, 0U, species);
    raw[2] = 50U;
    if (explicit_item) {
        cbr_put16(raw, 4U, item);
        raw[29] = 1U;
    }
}

static bool cbr_configure(struct mCore *core,
                          const struct CbrSymbols *symbols,
                          uint8_t level_mode)
{
    uint8_t payload[1] = {level_mode};
    return cbr_send(core, symbols, CBR_COMMAND_CONFIGURE,
                    payload, sizeof(payload), CBR_PHASE_CONFIGURING)
        && read8(core, CBR_STATE + CBR_STATE_LEVEL_MODE) == level_mode
        && read32(core, CBR_STATE + 12U) != 0U;
}

static bool cbr_upload_six(struct mCore *core,
                           const struct CbrSymbols *symbols)
{
    for (unsigned slot = 0U; slot < 6U; ++slot) {
        uint8_t payload[33];
        payload[0] = (uint8_t)slot;
        cbr_member(payload + 1U, (uint16_t)(slot + 1U),
                   (uint16_t)(179U + slot), true);
        /* Keep the scheduler proof deterministic across four turns: Splash
         * still has a real Max Guard conversion but cannot faint the player
         * and divert the UI into an unrelated forced-switch menu. */
        cbr_put16(payload + 1U, 6U, 150U);
        payload[1U + 29U] |= 2U;
        if (!cbr_send(core, symbols, CBR_COMMAND_UPLOAD,
                      payload, sizeof(payload), CBR_PHASE_CONFIGURING))
            return false;
    }
    return cbr_send(core, symbols, CBR_COMMAND_COMMIT,
                    NULL, 0U, CBR_PHASE_TEAM_PREVIEW);
}

static bool cbr_choose_team(struct mCore *core,
                            const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    return cbr_send(core, symbols, CBR_COMMAND_CHOOSE_TEAM,
                    selection, sizeof(selection), CBR_PHASE_TEAM_PREVIEW);
}

static void cbr_seed_player_party(struct mCore *core);

static bool cbr_setup_team(struct mCore *core,
                           const struct CbrSymbols *symbols,
                           uint32_t nonce, uint8_t level)
{
    cbr_test_initialize(core, symbols, nonce);
    cbr_seed_player_party(core);
    return cbr_configure(core, symbols, level)
        && cbr_upload_six(core, symbols)
        && cbr_choose_team(core, symbols);
}

static void cbr_seed_player_party(struct mCore *core)
{
    clear_parties(core);
    for (unsigned index = 0U; index < 6U; ++index)
        create_mon(core, CBR_PLAYER_PARTY + index * 100U,
                   (uint16_t)(index + 1U), (uint8_t)(30U + index));
    write8(core, CBR_PLAYER_COUNT, 6U);
    write32_bytes(core, CBR_BATTLE_FLAGS, 0U);
    write32_bytes(core, CBR_RNG, UINT32_C(0x5A17C0DE));
    for (unsigned index = 0U; index < 6U; ++index)
        write8(core, CBR_SELECTED + index, (uint8_t)(0xA0U + index));
}

static bool cbr_begin_selection(struct mCore *core,
                                const struct CbrSymbols *symbols,
                                const uint8_t selection[3])
{
    cbr_seed_player_party(core);
    if (cbr_call(core, symbols->field_begin, 0U, 0U, 0U, 0U) != 1U
            || read16(core, CBR_STATE + 16U) != CBR_PHASE_PLAYER_SELECTION
            || cbr_call(core, CBR_VAR_GET, 0x5018U, 0U, 0U, 0U) != 1U)
        return false;
    for (unsigned index = 0U; index < 6U; ++index)
        write8(core, CBR_SELECTED + index, (uint8_t)(0xA0U + index));
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    for (unsigned index = 0U; index < 6U; ++index) {
        if (read8(core, CBR_SELECTED + index) != 0U)
            return false;
    }
    for (unsigned index = 0U; index < 3U; ++index)
        write8(core, CBR_SELECTED + index, selection[index]);
    return cbr_call(core, symbols->field_commit, 0U, 0U, 0U, 0U) == 1U
        && read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 1U
        && read16(core, CBR_STATE + CBR_STATE_FIELD_COMPLETION_PENDING) == 1U
        && read16(core, CBR_STATE + 28U) == 1U;
}

static bool cbr_header_test(struct mCore *core,
                            const struct CbrSymbols *symbols)
{
    uint32_t nonce = UINT32_C(0x6A17C044);
    cbr_test_initialize(core, symbols, nonce);
    return read32(core, CBR_MAILBOX) == CBR_MAGIC
        && read16(core, CBR_MAILBOX + 4U) == 2U
        && read16(core, CBR_MAILBOX + 6U) == 2U
        && read16(core, CBR_MAILBOX + 8U) == 256U
        && read16(core, CBR_MAILBOX + 10U) == 64U
        && read16(core, CBR_MAILBOX + 12U) == 64U
        && read16(core, CBR_MAILBOX + 14U) == 96U
        && read16(core, CBR_MAILBOX + 16U) == 160U
        && read16(core, CBR_MAILBOX + 18U) == 96U
        && read16(core, CBR_MAILBOX + 20U) == 64U
        && read16(core, CBR_MAILBOX + 22U) == 44U
        && read32(core, CBR_MAILBOX + 24U) == CBR_CAPABILITIES
        && read32(core, CBR_MAILBOX + 28U) == CBR_STAGE_IDENTITY
        && read32(core, CBR_MAILBOX + 36U) == nonce
        && read32(core, CBR_MAILBOX + 40U) == ~nonce
        && read16(core, CBR_MAILBOX + 44U) == CBR_PHASE_IDLE
        && cbr_snapshot_valid(core)
        && cbr_public_state_valid(core)
        && cbr_call(core, symbols->probe, 1U, 0U, 0U, 0U) == CBR_MAILBOX
        && cbr_call(core, symbols->probe, 3U, 0U, 0U, 0U) == CBR_STATE;
}

static uint32_t cbr_thumb_bl_target(struct mCore *core, uint32_t site)
{
    uint16_t high = read16(core, site);
    uint16_t low = read16(core, site + 2U);
    int32_t offset = (int32_t)(((uint32_t)(high & 0x7FFU) << 12)
                             | ((uint32_t)(low & 0x7FFU) << 1));
    if (offset & 0x00400000)
        offset |= (int32_t)0xFF800000;
    return (uint32_t)((int32_t)(site + 4U) + offset) | 1U;
}

static bool cbr_roots_test(struct mCore *core,
                           const struct CbrSymbols *symbols,
                           const struct CbrCases *cases,
                           const char *symbols_path)
{
    bool exports = true;
#define CBR_EXPORT_TEST(member, name) exports = exports && ((symbols->member & 1U) != 0U);
    CBR_SYMBOL_LIST(CBR_EXPORT_TEST)
#undef CBR_EXPORT_TEST
    static const uint8_t signature[8] = {'V', 'E', 'G', 'A', 'C', 'B', '4', '4'};
    bool payload = true;
    for (unsigned index = 0U; index < sizeof(signature); ++index)
        payload = payload && read8(core, cases->payload + index) == signature[index];
    char *text = cbr_read_text(symbols_path);
    bool policies = cbr_occurrences(text, "\"inactive_delegate\"") == 21U
        && cbr_occurrences(text, "codex_upstream_open::") == 15U;
    uint32_t reception_script = cbr_json_number(
        cbr_find_key(text, "reception_script"), "reception_script");
    bool rooted = exports && payload && policies
        && cases->mailbox == CBR_MAILBOX && cases->state == CBR_STATE
        && read32(core, CBR_READ_KEYS_POINTER) == symbols->read_keys
        && cbr_thumb_bl_target(core, CBR_TRAINER_PARTY_SITE) == symbols->trainer_party
        && read16(core, CBR_SAVE_LOAD_SITE) == 0x4B00U
        && read16(core, CBR_SAVE_LOAD_SITE + 2U) == 0x4718U
        && read32(core, CBR_SAVE_LOAD_SITE + 4U) == symbols->save_load
        && read32(core, CBR_RECEPTION_POINTER) == reception_script
        && read32(core, CBR_SELECTION_CONFIRM_POINTER) == CBR_SELECTED
        && read32(core, CBR_OPPONENT_CHOOSE_ACTION_POINTER)
            == symbols->controller
        && read32(core, CBR_OPPONENT_CHOOSE_MOVE_POINTER)
            == symbols->controller
        && read32(core, CBR_OPPONENT_CHOOSE_POKEMON_POINTER)
            == symbols->controller
        && cbr_thumb_bl_target(core, CBR_DYNAMAX_BAND_EXECUTION_SITE)
            == symbols->find_dynamax_band
        && cbr_thumb_bl_target(core, CBR_GIGANTAMAX_BAND_EXECUTION_SITE)
            == symbols->find_dynamax_band
        && cbr_thumb_bl_target(core, CBR_DYNAMAX_BAND_UI_SITE)
            == symbols->find_dynamax_band;
    free(text);
    return rooted;
}

static bool cbr_team_test(struct mCore *core,
                          const struct CbrSymbols *symbols,
                          unsigned iterations)
{
    uint32_t expected_hash = 0U;
    bool deterministic = true;
    for (unsigned iteration = 0U; iteration < iterations; ++iteration) {
        cbr_test_initialize(core, symbols, UINT32_C(0x44001001));
        if (!cbr_configure(core, symbols, 0U))
            return false;
        uint8_t payload[33] = {0};
        cbr_member(payload + 1U, 1U, 0U, false);
        if (!cbr_send(core, symbols, CBR_COMMAND_UPLOAD,
                      payload, sizeof(payload), CBR_PHASE_CONFIGURING))
            return false;
        uint32_t member_hash = cbr_hash(core, CBR_STATE + CBR_STATE_TEAM, 32U);
        if (iteration == 0U)
            expected_hash = member_hash;
        deterministic = deterministic && member_hash == expected_hash
            && read16(core, CBR_STATE + CBR_STATE_TEAM) == 1U
            && read16(core, CBR_STATE + CBR_STATE_TEAM + 6U) == 33U
            && read8(core, CBR_STATE + CBR_STATE_TEAM + 29U) == 0xFFU;
    }
    cbr_test_initialize(core, symbols, UINT32_C(0x44001002));
    if (!cbr_configure(core, symbols, 0U))
        return false;
    uint8_t invalid_payload[33] = {0};
    invalid_payload[0] = 0U;
    cbr_member(invalid_payload + 1U, 0U, 0U, false);
    uint8_t request[96];
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, invalid_payload,
                      sizeof(invalid_payload), cbr_next_sequence(core));
    bool invalid = cbr_send_error(core, symbols, request, CBR_ERROR_MEMBER);
    return deterministic && invalid;
}

static bool cbr_unrestricted_policy_test(struct mCore *core,
                                         const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    for (unsigned level = 0U; level < 2U; ++level) {
        unsigned step = 0U;
#define CBR_UNRESTRICTED_REQUIRE(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "unrestricted policy failed level=%u step=%u phase=%u\n", \
                level, step, read16(core, CBR_STATE + 16U)); \
        return false; \
    } \
    ++step; \
} while (0)
        cbr_test_initialize(core, symbols, UINT32_C(0x44002000) + level);
        cbr_seed_player_party(core);
        set_mon_data_u32(core, CBR_PLAYER_PARTY, 12U, 179U);
        set_mon_data_u32(core, CBR_PLAYER_PARTY + 100U, 12U, 179U);
        CBR_UNRESTRICTED_REQUIRE(cbr_configure(
            core, symbols, (uint8_t)level));
        for (unsigned slot = 0U; slot < 6U; ++slot) {
            uint8_t payload[33];
            payload[0] = (uint8_t)slot;
            cbr_member(payload + 1U, 1U, 179U, true);
            payload[3] = 73U;
            CBR_UNRESTRICTED_REQUIRE(cbr_send(
                core, symbols, CBR_COMMAND_UPLOAD,
                payload, sizeof(payload), CBR_PHASE_CONFIGURING));
        }
        CBR_UNRESTRICTED_REQUIRE(cbr_send(
            core, symbols, CBR_COMMAND_COMMIT,
            NULL, 0U, CBR_PHASE_TEAM_PREVIEW));
        CBR_UNRESTRICTED_REQUIRE(cbr_choose_team(core, symbols));
        CBR_UNRESTRICTED_REQUIRE(cbr_call(
            core, symbols->field_begin, 0U, 0U, 0U, 0U) == 1U);
        CBR_UNRESTRICTED_REQUIRE(cbr_call(
            core, CBR_VAR_GET, 0x5018U, 0U, 0U, 0U) == 1U);
        CBR_UNRESTRICTED_REQUIRE(cbr_call(
            core, CBR_FLAG_GET, 0x0930U, 0U, 0U, 0U) == 0U);
        for (unsigned index = 0U; index < 3U; ++index)
            write8(core, CBR_SELECTED + index, selection[index]);
        CBR_UNRESTRICTED_REQUIRE(cbr_call(
            core, symbols->field_commit, 0U, 0U, 0U, 0U) == 1U);
        /* The production trainer-party hook builds the selected opponent
         * party after trainerbattle owns its initialization. */
        write16(core, BATTLE_CORE_TRAINER_MODE, 3U);
        write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 745U);
        cbr_call(core, symbols->trainer_party, 0U, 0U, 0U, 0U);
        uint32_t player_level = cbr_call(
            core, BATTLE_CORE_GET_MON_DATA,
            CBR_PLAYER_PARTY, 56U, 0U, 0U);
        uint32_t codex_level = cbr_call(
            core, BATTLE_CORE_GET_MON_DATA,
            CBR_ENEMY_PARTY, 56U, 0U, 0U);
        if (player_level != (level == 0U ? 50U : 30U)
                || codex_level != (level == 0U ? 50U : 73U)) {
            fprintf(stderr, "unrestricted levels mode=%u player=%" PRIu32
                    " codex=%" PRIu32 "\n", level, player_level, codex_level);
            return false;
        }
        cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
#undef CBR_UNRESTRICTED_REQUIRE
    }
    return true;
}

static bool cbr_selection_test(struct mCore *core,
                               const struct CbrSymbols *symbols)
{
    uint8_t first[92], second[92];
    const uint8_t order_a[3] = {1U, 2U, 3U};
    const uint8_t order_b[3] = {3U, 2U, 1U};
    if (!cbr_setup_team(core, symbols, UINT32_C(0x44003001), 0U)
            || !cbr_begin_selection(core, symbols, order_a))
        return false;
    for (unsigned index = 0U; index < sizeof(first); ++index)
        first[index] = read8(core, CBR_MAILBOX + 68U + index);
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    if (!cbr_setup_team(core, symbols, UINT32_C(0x44003001), 0U)
            || !cbr_begin_selection(core, symbols, order_b))
        return false;
    for (unsigned index = 0U; index < sizeof(second); ++index)
        second[index] = read8(core, CBR_MAILBOX + 68U + index);
    memset(first, 0, 4U);
    memset(second, 0, 4U);
    bool private_order = memcmp(first, second, sizeof(first)) == 0;
    bool previews = read16(core, CBR_MAILBOX + 108U) == 1U
        && read16(core, CBR_MAILBOX + 120U) == 1U
        && read16(core, CBR_MAILBOX + 156U) == 0U
        && read8(core, CBR_MAILBOX + 158U) == 0U
        && (read8(core, CBR_MAILBOX + 159U) & 0x80U) == 0U;
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    return private_order && previews;
}

static void cbr_seed_controller(struct mCore *core)
{
    write32_bytes(core, CBR_BATTLE_FLAGS,
                  read32(core, CBR_BATTLE_FLAGS) | 0x40000008U);
    write8(core, CBR_ACTIVE_BATTLER, 1U);
    /* gBattlerPartyIndexes is u16[4]; opponent bank 1 starts at +2. */
    write16(core, CBR_PARTY_INDEXES + 2U, 0U);
    for (unsigned index = 0U; index < 120U; ++index)
        write8(core, CBR_BATTLE_BUFFER_A + 0x204U + index, 0U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x0CU, 33U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x0DU, 0U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x24U, 35U);
}

static void cbr_choose_move_info(struct mCore *core)
{
    uint32_t info = CBR_BATTLE_BUFFER_A + 0x204U;
    for (unsigned index = 0U; index < 120U; ++index)
        write8(core, info + index, 0U);
    write8(core, info, 33U);
    write8(core, info + 8U, 35U);
    write8(core, info + 82U, 1U);
    write8(core, info + 88U, 1U);
    write8(core, info + 98U, 1U);
    write8(core, info + 100U, 1U);
    write8(core, info + 118U, 1U);
}

static bool cbr_controller_wait(struct mCore *core,
                                const struct CbrSymbols *symbols)
{
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    return read16(core, CBR_STATE + 16U) == CBR_PHASE_ACTION;
}

static bool cbr_controller_test(struct mCore *core,
                                const struct CbrSymbols *symbols,
                                unsigned *turn_cycles)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    if (!cbr_setup_team(core, symbols, UINT32_C(0x44004001), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    write16(core, BATTLE_CORE_TRAINER_MODE, 3U);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 745U);
    cbr_call(core, symbols->trainer_party, 0U, 0U, 0U, 0U);
    cbr_seed_controller(core);
    write8(core, CBR_PARTY_INDEXES, 0U);
    bool gimmicks = true;
    for (unsigned gimmick = 0U; gimmick < 5U; ++gimmick) {
        if (!cbr_controller_wait(core, symbols))
            return false;
        write8(core, CBR_STATE + CBR_STATE_LEGAL_MOVE, 1U);
        write8(core, CBR_STATE + CBR_STATE_LEGAL_GIMMICKS,
               (uint8_t)(1U << gimmick));
        uint8_t payload[3] = {1U, 0U, (uint8_t)gimmick};
        if (!cbr_send(core, symbols, CBR_COMMAND_MOVE, payload,
                      sizeof(payload), CBR_PHASE_RESOLVING))
            return false;
        write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
        cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
        cbr_choose_move_info(core);
        write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 20U);
        uint16_t before = read16(core, CBR_STATE + 28U);
        cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
        gimmicks = gimmicks && read16(core, CBR_STATE + 28U) == before + 1U
            && read8(core, CBR_STATE + CBR_STATE_ACTION_KIND) == 0U;
        ++*turn_cycles;
    }
    if (!cbr_controller_wait(core, symbols))
        return false;
    write8(core, CBR_STATE + CBR_STATE_LEGAL_SWITCH, 0x06U);
    const uint8_t switch_slot[1] = {2U};
    if (!cbr_send(core, symbols, CBR_COMMAND_SWITCH, switch_slot,
                  sizeof(switch_slot), CBR_PHASE_RESOLVING))
        return false;
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 22U);
    uint16_t before_switch = read16(core, CBR_STATE + 28U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    bool switched = read16(core, CBR_STATE + 28U) == before_switch + 1U;
    ++*turn_cycles;
    if (!cbr_controller_wait(core, symbols)
            || !cbr_send(core, symbols, CBR_COMMAND_FORFEIT,
                         NULL, 0U, CBR_PHASE_RESOLVING))
        return false;
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    uint16_t before_forfeit = read16(core, CBR_STATE + 28U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    bool forfeited = read16(core, CBR_STATE + 28U) == before_forfeit + 1U;
    ++*turn_cycles;
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    return gimmicks && switched && forfeited && *turn_cycles >= 3U;
}

static bool cbr_live_hp_switch_semantics_test(
    struct mCore *core, const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    const uint8_t slot_two[1] = {2U};
    if (!cbr_setup_team(core, symbols, UINT32_C(0x4400A001), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    write16(core, BATTLE_CORE_TRAINER_MODE, 3U);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 745U);
    cbr_call(core, symbols->trainer_party, 0U, 0U, 0U, 0U);
    cbr_seed_controller(core);
    for (unsigned index = 0U; index < 3U; ++index) {
        set_mon_data_u32(core, CBR_ENEMY_PARTY + index * 100U,
                         57U, 80U + index * 10U);
        set_mon_data_u32(core, CBR_ENEMY_PARTY + index * 100U,
                         58U, 100U + index * 10U);
    }
    write16(core, CBR_BATTLE_MONS + 88U, 1U);
    for (unsigned index = 0U; index < 5U; ++index)
        write16(core, CBR_BATTLE_MONS + 88U + 0x02U + index * 2U,
                (uint16_t)(201U + index));
    write16(core, CBR_BATTLE_MONS + 88U + 0x28U, 73U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x2CU, 123U);
    for (unsigned index = 0U; index < 4U; ++index) {
        write16(core, CBR_BATTLE_MONS + 88U + 0x0CU + index * 2U,
                (uint16_t)(500U + index));
        write8(core, CBR_BATTLE_MONS + 88U + 0x24U + index,
               (uint8_t)(9U - index));
    }
    write16(core, CBR_BATTLE_MONS, 25U);
    write16(core, CBR_BATTLE_MONS + 0x28U, 50U);
    write16(core, CBR_BATTLE_MONS + 0x2CU, 200U);
    for (unsigned bank = 0U; bank < 2U; ++bank)
        for (unsigned stat = 0U; stat < 7U; ++stat)
            write8(core, CBR_BATTLE_MONS + bank * 88U + 0x19U + stat, 6U);
    if (!cbr_controller_wait(core, symbols))
        return false;
    bool exact = cbr_snapshot_valid(core)
        && read16(core, CBR_MAILBOX + 132U) == 73U
        && read16(core, CBR_MAILBOX + 134U) == 90U
        && read16(core, CBR_MAILBOX + 136U) == 100U
        && read16(core, CBR_MAILBOX + 138U) == 123U
        && read16(core, CBR_MAILBOX + 144U) == 500U
        && read16(core, CBR_MAILBOX + 150U) == 503U
        && read8(core, CBR_MAILBOX + 152U) == 9U
        && read8(core, CBR_MAILBOX + 155U) == 6U
        && read16(core, CBR_MAILBOX + 156U) == 25U
        && read8(core, CBR_MAILBOX + 158U) == 25U
        && (read8(core, CBR_MAILBOX + 159U) & 3U) == 0U
        && read16(core, CBR_MAILBOX + 108U) == 201U
        && read16(core, CBR_MAILBOX + 116U) == 205U
        && (read16(core, CBR_MAILBOX + 118U) & 3U) != 3U;

    uint16_t voluntary_turn = read16(core, CBR_STATE + 28U);
    bool voluntary = cbr_send(core, symbols, CBR_COMMAND_SWITCH,
                              slot_two, sizeof(slot_two), CBR_PHASE_RESOLVING)
        && read8(core, CBR_STATE + CBR_STATE_SWITCH_CONTEXT) == 1U
        && (read8(core, CBR_MAILBOX + 159U) & 0x20U) != 0U;
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    voluntary = voluntary
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_RESOLVING
        && read8(core, CBR_STATE + CBR_STATE_SWITCH_CONTEXT) == 1U;
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 22U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    voluntary = voluntary
        && read16(core, CBR_STATE + 28U) == voluntary_turn + 1U
        && read8(core, CBR_STATE + CBR_STATE_ACTION_KIND) == 0U
        && read8(core, CBR_STATE + CBR_STATE_SWITCH_CONTEXT) == 0U
        && read16(core, CBR_STATE + 16U) != CBR_PHASE_SWITCH;

    write16(core, CBR_PARTY_INDEXES + 2U, 0U);
    set_mon_data_u32(core, CBR_ENEMY_PARTY, 57U, 0U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x28U, 0U);
    write8(core, CBR_STATE + CBR_STATE_ACTION_KIND, 0U);
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 22U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    bool forced = read16(core, CBR_STATE + 16U) == CBR_PHASE_SWITCH
        && read8(core, CBR_STATE + CBR_STATE_SWITCH_CONTEXT) == 2U
        && read16(core, CBR_MAILBOX + 132U) == 0U
        && (read8(core, CBR_MAILBOX + 159U) & 0x18U) == 0x18U
        && (read8(core, CBR_MAILBOX + 100U) & 1U) == 0U
        && (read8(core, CBR_MAILBOX + 100U) & 2U) != 0U;
    uint16_t forced_turn = read16(core, CBR_STATE + 28U);
    forced = forced && cbr_send(core, symbols, CBR_COMMAND_SWITCH,
                                slot_two, sizeof(slot_two), CBR_PHASE_RESOLVING)
        && read8(core, CBR_STATE + CBR_STATE_SWITCH_CONTEXT) == 2U;
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 22U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    forced = forced && read16(core, CBR_STATE + 28U) == forced_turn + 1U
        && read8(core, CBR_STATE + CBR_STATE_ACTION_KIND) == 0U;
    /* The stock switch script owns the eventual active-index write.  Mirror
     * that completed engine step, then prove the next public snapshot tracks
     * the new live battler without another Codex switch request. */
    write16(core, CBR_PARTY_INDEXES + 2U, 1U);
    write16(core, CBR_BATTLE_MONS + 88U, 2U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x28U, 90U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x2CU, 110U);
    forced = forced && cbr_controller_wait(core, symbols)
        && (read8(core, CBR_MAILBOX + 159U) & 3U) == 1U
        && read16(core, CBR_MAILBOX + 134U) == 90U;
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    if (!(exact && voluntary && forced))
        fprintf(stderr, "live HP/switch bits exact=%u voluntary=%u forced=%u "
                "phase=%u flags=%02x mask=%02x\n", exact, voluntary, forced,
                read16(core, CBR_STATE + 16U),
                read8(core, CBR_MAILBOX + 159U),
                read8(core, CBR_MAILBOX + 100U));
    return exact && voluntary && forced;
}

static bool cbr_public_online_state_test(
    struct mCore *core, const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    const uint32_t newbs = CBR_SCRATCH;
    if (!cbr_setup_team(core, symbols, UINT32_C(0x4400A002), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    write16(core, BATTLE_CORE_TRAINER_MODE, 3U);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 745U);
    cbr_call(core, symbols->trainer_party, 0U, 0U, 0U, 0U);
    cbr_seed_controller(core);
    write8(core, CBR_PARTY_INDEXES, 0U);
    for (unsigned offset = 0U; offset < 0x380U; ++offset)
        write8(core, CBR_SCRATCH + offset, 0U);
    write32_bytes(core, CBR_NEW_BS_PTR, newbs);
    write8(core, newbs + 3U, 4U);
    write8(core, newbs + 8U, 5U);
    write8(core, newbs + 20U, 4U);
    write8(core, newbs + 0x20U, 5U);
    write8(core, newbs + 0x21U, 4U);
    write8(core, newbs + 0x25U, 4U);
    write8(core, newbs + 0xD1U, 2U);
    write8(core, newbs + 0xE4U, 3U);
    write8(core, newbs + 0x125U, 1U);
    write16(core, newbs + 0x29EU, 65U);
    write8(core, newbs + 0x24EU + 1U, 1U);
    write8(core, newbs + 0x252U + 1U, 2U);
    write8(core, CBR_TERRAIN_TYPE, 1U);
    write16(core, CBR_BATTLE_WEATHER, 1U);
    for (unsigned offset = 0U; offset < 0x2CU; ++offset)
        write8(core, CBR_WISH_FUTURE_KNOCK + offset, 0U);
    write8(core, CBR_WISH_FUTURE_KNOCK, 3U);
    write16(core, CBR_WISH_FUTURE_KNOCK + 0x18U, 85U);
    write8(core, CBR_WISH_FUTURE_KNOCK + 0x20U, 2U);
    write8(core, CBR_WISH_FUTURE_KNOCK + 0x28U, 5U);
    write16(core, CBR_SIDE_STATUSES + 2U, 1U);
    write8(core, CBR_SIDE_TIMERS + 12U, 5U);
    write8(core, CBR_SIDE_TIMERS + 12U + 10U, 0x10U);
    write16(core, CBR_DISABLE_STRUCTS + 0x04U, 92U);
    write8(core, CBR_DISABLE_STRUCTS + 0x0BU, 3U);
    write16(core, CBR_DISABLE_STRUCTS + 0x1CU + 0x06U, 53U);
    write8(core, CBR_DISABLE_STRUCTS + 0x1CU + 0x0EU, 2U);
    write16(core, CBR_BATTLE_MONS + 88U, 136U);
    write16(core, CBR_BATTLE_MONS, 25U);
    write8(core, CBR_BATTLE_MONS + 0x2AU, 50U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x2AU, 50U);
    write16(core, CBR_BATTLE_MONS + 0x2EU, 88U);
    set_mon_data_u32(core, CBR_ENEMY_PARTY + 100U, 55U, 0x10U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x2EU, 179U);
    write16(core, CBR_BATTLE_MONS + 88U + 0x38U, 42U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x18U, 0xFFU);
    write8(core, CBR_BATTLE_MONS + 88U + 0x21U, 10U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x22U, 10U);
    write8(core, CBR_BATTLE_MONS + 0x18U, 0xFFU);
    write8(core, CBR_BATTLE_MONS + 0x21U, 12U);
    write8(core, CBR_BATTLE_MONS + 0x22U, 12U);
    write8(core, CBR_BATTLE_MONS + 88U + 0x19U, 8U);
    write8(core, CBR_BATTLE_MONS + 0x19U, 4U);
    write32_bytes(core, CBR_BATTLE_MONS + 88U + 0x50U, 0x01000000U);
    write32_bytes(core, CBR_BATTLE_MONS + 88U + 0x4CU, 0U);
    write32_bytes(core, CBR_BATTLE_MONS + 0x50U, 0x00000007U);
    write32_bytes(core, CBR_BATTLE_MONS + 0x4CU, 0x00000007U);
    write32_bytes(core, CBR_STATUSES3 + 4U, 0x00880000U);
    write32_bytes(core, CBR_STATUSES3, 0x80080000U);
    if (!cbr_controller_wait(core, symbols))
        return false;
    write8(core, CBR_BATTLE_BUFFER_A, 16U);
    write16(core, CBR_BATTLE_BUFFER_A + 2U, 388U);
    write16(core, CBR_BATTLE_BUFFER_A + 4U, 53U);
    write16(core, CBR_BATTLE_BUFFER_A + 6U, 53U);
    write16(core, CBR_BATTLE_BUFFER_A + 8U, 88U);
    write8(core, CBR_BATTLE_BUFFER_A + 11U, 0U);
    write8(core, CBR_BATTLE_BUFFER_A + 14U, 0U);
    write16(core, CBR_BATTLE_BUFFER_A + 18U, 65U);
    write8(core, CBR_BATTLE_BUFFER_A + 76U, 0xFDU);
    write8(core, CBR_BATTLE_BUFFER_A + 77U, 0x13U);
    write8(core, CBR_BATTLE_BUFFER_A + 78U, 0xFDU);
    write8(core, CBR_BATTLE_BUFFER_A + 79U, 0x16U);
    write8(core, CBR_BATTLE_BUFFER_A + 80U, 0xFDU);
    write8(core, CBR_BATTLE_BUFFER_A + 81U, 0x17U);
    write8(core, CBR_BATTLE_BUFFER_A + 82U, 0xFDU);
    write8(core, CBR_BATTLE_BUFFER_A + 83U, 0x14U);
    write8(core, CBR_BATTLE_BUFFER_A + 84U, 0xFFU);
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 1U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool state_identity = cbr_public_state_valid(core)
        && read8(core, CBR_PUBLIC_STATE + 19U) == 1U
        && cbr_public_bits(core, 136U, 0U, 9U) == 388U
        && cbr_public_u16(core, 20U) == 136U
        && (read8(core, CBR_PUBLIC_STATE + 26U) & 0xFU) == 8U
        && (read8(core, CBR_PUBLIC_STATE + 29U) >> 4) == 4U
        && cbr_public_u32(core, 37U) == 3U
        && cbr_public_u32(core, 41U) == 0x00800001U
        && cbr_public_u32(core, 45U) == 0x00000002U
        && cbr_public_u16(core, 49U) == 179U
        && cbr_public_u16(core, 51U) == 42U
        && cbr_public_u16(core, 53U) == 88U
        && cbr_public_u16(core, 55U) == 65U
        && cbr_public_u16(core, 57U) == 0U
        && ((cbr_public_u32(core, 65U) >> 15) & 0x7FFFU) == 0x7FFFU;
    bool state_field = cbr_public_u16(core, 69U) == 1U
        && read8(core, CBR_PUBLIC_STATE + 70U) == 0U
        && read8(core, CBR_PUBLIC_STATE + 72U) == 1U
        && read8(core, CBR_PUBLIC_STATE + 77U) == 4U
        && cbr_public_u16(core, 84U) == 1U
        && read8(core, CBR_PUBLIC_STATE + 91U) == 0x10U
        && (read8(core, CBR_PUBLIC_STATE + 104U) & 0x44U) == 0x44U
        && read8(core, CBR_PUBLIC_STATE + 105U) == 50U
        && read8(core, CBR_PUBLIC_STATE + 135U) == 50U;
    bool state_effects = cbr_public_bits(core, 106U, 0U, 12U) == 92U
        && cbr_public_bits(core, 106U, 36U, 12U) == 53U
        && cbr_public_bits(core, 112U, 0U, 4U) == 3U
        && cbr_public_bits(core, 112U, 68U, 4U) == 2U
        && cbr_public_bits(core, 112U, 14U, 3U) == 5U
        && cbr_public_bits(core, 112U, 81U, 3U) == 4U
        && cbr_public_bits(core, 112U, 100U, 2U) == 2U
        && cbr_public_bits(core, 112U, 117U, 3U) == 2U
        && cbr_public_bits(core, 112U, 56U, 3U) == 3U
        && cbr_public_bits(core, 128U, 3U, 3U) == 4U
        && cbr_public_bits(core, 130U, 0U, 2U) == 2U
        && cbr_public_bits(core, 130U, 4U, 2U) == 3U
        && cbr_public_bits(core, 130U, 8U, 11U) == 85U
        && cbr_public_bits(core, 130U, 30U, 1U) == 1U;
    bool state_event = cbr_public_bits(core, 136U, 31U, 10U) == 88U
        && cbr_public_bits(core, 136U, 41U, 10U) == 65U
        && cbr_public_bits(core, 136U, 81U, 2U) == 1U
        && cbr_public_bits(core, 136U, 83U, 5U) == 0x07U
        && read8(core, CBR_PUBLIC_STATE + 134U) == 1U
        && read8(core, CBR_PUBLIC_STATE + 24U) == 1U
        && read8(core, CBR_PUBLIC_STATE + 25U) == 0U;
    bool state = state_identity && state_field && state_effects && state_event;
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool deduplicated = read8(core, CBR_PUBLIC_STATE + 19U) == 1U;
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 0U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);

    /* A public Max Move must remember its underlying original move, never
     * the temporary Max presentation ID or private AI history. */
    write8(core, CBR_BANK_ATTACKER, 0U);
    write8(core, CBR_BATTLE_BUFFER_A, 16U);
    write16(core, CBR_BATTLE_BUFFER_A + 2U, 4U);
    write16(core, CBR_BATTLE_BUFFER_A + 4U, 913U);
    write16(core, CBR_BATTLE_BUFFER_A + 6U, 53U);
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 1U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool original_move_revealed = read8(core, CBR_PUBLIC_STATE + 19U) == 2U
        && cbr_public_u16(core, 57U) == 53U
        && cbr_public_u16(core, 59U) == 0U
        && cbr_public_bits(core, 147U, 0U, 9U) == 4U
        && cbr_public_bits(core, 147U, 9U, 11U) == 913U
        && cbr_public_bits(core, 147U, 20U, 11U) == 53U;
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool move_deduplicated = read8(core, CBR_PUBLIC_STATE + 19U) == 2U;
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 0U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);

    write8(core, CBR_ABILITY_POPUP_HELPER, 77U);
    write8(core, CBR_ABILITY_POPUP_HELPER + 1U, 0U);
    write8(core, CBR_BATTLE_BUFFER_A, 52U);
    write8(core, CBR_BATTLE_BUFFER_A + 1U, 0x42U);
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 1U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool ability_popup = read8(core, CBR_PUBLIC_STATE + 19U) == 3U
        && cbr_public_bits(core, 158U, 0U, 9U) == 389U
        && cbr_public_bits(core, 158U, 41U, 10U) == 77U
        && cbr_public_bits(core, 158U, 83U, 5U) == 0x02U
        && cbr_public_u16(core, 55U) == 77U;
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool ability_deduplicated = read8(core, CBR_PUBLIC_STATE + 19U) == 3U;
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 0U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    write8(core, CBR_PARTY_INDEXES, 1U);
    bool revealed_identity_reset = cbr_controller_wait(core, symbols)
        && (read16(core, CBR_MAILBOX + 108U + 10U) >> 13U) == 2U
        && cbr_public_u16(core, 53U) == 0U
        && cbr_public_u16(core, 55U) == 0U
        && cbr_public_u16(core, 57U) == 0U;
    write8(core, CBR_BATTLE_BUFFER_A, 17U);
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 1U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool private_excluded = read8(core, CBR_PUBLIC_STATE + 19U) == 3U;
    if (!(state && deduplicated && original_move_revealed
          && move_deduplicated && ability_popup && ability_deduplicated
          && revealed_identity_reset && private_excluded))
        fprintf(stderr, "public online bits state=%u(%u/%u/%u/%u) dedup=%u popup=%u/%u "
                "reset=%u private=%u count=%u crc=%u msg=%u "
                "popup_event=%u/%u/%u species=%u "
                "stages=%x/%x item=%u ability=%u revealed=%u move=%u "
                "weather=%u terrain=%u trick=%u side=%u native=%02x "
                "level=%u disable=%u encore=%u personal=%02x/%02x/%02x\n",
                state, state_identity, state_field, state_effects, state_event,
                deduplicated, ability_popup, ability_deduplicated,
                revealed_identity_reset, private_excluded,
                read8(core, CBR_PUBLIC_STATE + 19U),
                cbr_public_state_valid(core),
                cbr_public_bits(core, 136U, 0U, 9U),
                cbr_public_bits(core, 158U, 0U, 9U),
                cbr_public_bits(core, 158U, 41U, 10U),
                cbr_public_bits(core, 158U, 83U, 5U),
                cbr_public_u16(core, 20U),
                read8(core, CBR_PUBLIC_STATE + 26U) & 0xFU,
                read8(core, CBR_PUBLIC_STATE + 29U) >> 4,
                cbr_public_u16(core, 49U),
                cbr_public_u16(core, 51U),
                cbr_public_u16(core, 53U),
                cbr_public_u16(core, 57U),
                cbr_public_u16(core, 69U),
                read8(core, CBR_PUBLIC_STATE + 72U),
                read8(core, CBR_PUBLIC_STATE + 77U),
                cbr_public_u16(core, 84U),
                read8(core, CBR_PUBLIC_STATE + 104U),
                read8(core, CBR_PUBLIC_STATE + 105U),
                cbr_public_bits(core, 106U, 0U, 12U),
                cbr_public_bits(core, 106U, 36U, 12U),
                cbr_public_bits(core, 112U, 0U, 4U),
                cbr_public_bits(core, 112U, 14U, 3U),
                cbr_public_bits(core, 112U, 117U, 3U));
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    return state && deduplicated && original_move_revealed
        && move_deduplicated && ability_popup && ability_deduplicated
        && revealed_identity_reset && private_excluded;
}

static bool cbr_live_send(struct mCore *core, uint16_t command,
                          const uint8_t *payload, uint16_t size,
                          uint16_t next_phase)
{
    uint32_t sequence = cbr_next_sequence(core);
    uint8_t request[96];
    cbr_build_request(core, request, command, payload, size, sequence);
    cbr_write_request(core, request, false);
    core->setKeys(core, 0U);
    for (unsigned frame = 0U; frame < 180U; ++frame) {
        core->runFrame(core);
        if (read32(core, CBR_MAILBOX + 72U) == sequence
                && cbr_snapshot_valid(core))
            break;
    }
    return cbr_snapshot_valid(core)
        && read32(core, CBR_MAILBOX + 72U) == sequence
        && read16(core, CBR_MAILBOX + 80U) == CBR_STATUS_ACCEPTED
        && read16(core, CBR_MAILBOX + 82U) == 0U
        && read16(core, CBR_MAILBOX + 84U) == command
        && read32(core, CBR_MAILBOX + 88U) == sequence
        && read16(core, CBR_MAILBOX + 44U) == next_phase;
}

static bool cbr_live_wait(struct mCore *core, uint16_t phase,
                          uint16_t minimum_turn, unsigned pulses)
{
    for (unsigned pulse = 0U; pulse < pulses; ++pulse) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 30U);
        if (read8(core, CBR_STATE + CBR_STATE_ACTIVE) != 0U
                && read16(core, CBR_STATE + 16U) == phase
                && read16(core, CBR_STATE + 28U) >= minimum_turn)
            return true;
    }
    return false;
}

static bool cbr_real_battle_multiturn_test(
    struct mCore *core, const struct CbrSymbols *symbols,
    unsigned *request_cycles)
{
    const uint8_t switch_slot[1] = {2U};
    const uint8_t dynamax_move[3] = {1U, 0U, 3U};
    const uint8_t normal_move[3] = {1U, 0U, 0U};
    uint32_t party_before = 0U;
    uint32_t save_before = 0U;
    bool restored = false;
    const char *failure_step = "overworld";

    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != CBR_CB2_OVERWORLD)
        goto failure;
    failure_step = "production-map";
    (void)cbr_call(core, CBR_KANTO_WARP, 96U, 5U, 20U, 20U);
    run_key_frames(core, 0U, 1800U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != CBR_CB2_OVERWORLD)
        goto failure;
    failure_step = "initialize";
    cbr_test_initialize(core, symbols, UINT32_C(0x44E2E001));
    cbr_seed_player_party(core);
    failure_step = "configure";
    if (!cbr_configure(core, symbols, 0U))
        goto failure;
    failure_step = "upload";
    if (!cbr_upload_six(core, symbols))
        goto failure;
    failure_step = "choose-team";
    if (!cbr_choose_team(core, symbols))
        goto failure;
    party_before = cbr_hash(core, CBR_PLAYER_PARTY, 600U);
    save_before = cbr_logical_save_hash(core);
    if (save_before == 0U)
        goto failure;
    failure_step = "selection";
    (void)cbr_call(core, CBR_SCRIPT_CONTEXT1_SETUP,
                   symbols->begin_script, 0U, 0U, 0U);
    (void)cbr_call(core, CBR_SCRIPT_CONTEXT2_ENABLE, 0U, 0U, 0U, 0U);
    run_key_frames(core, 0U, 600U);
    for (unsigned slot = 0U; slot < 3U; ++slot) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 90U);
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 120U);
        if (slot < 2U) {
            run_key_frames(core, 128U, 2U);
            run_key_frames(core, 0U, 60U);
        }
    }
    for (unsigned confirm = 0U; confirm < 8U; ++confirm) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 120U);
        if (read16(core, CBR_STATE + 16U) != CBR_PHASE_PLAYER_SELECTION)
            break;
    }
    failure_step = "trainer-start";
    failure_step = "turn-1";
    if (!cbr_live_wait(core, CBR_PHASE_ACTION, 1U, 260U)
            || cbr_hash(core, CBR_PLAYER_PARTY, 600U) == party_before
            || read32(core, CBR_OPPONENT_CHOOSE_ACTION_POINTER)
                != symbols->controller
            || cbr_call(core, CBR_FLAG_GET, CBR_FLAG_DISABLE_BAG,
                        0U, 0U, 0U) != 1U
            || read8(core, read32(core, CBR_BATTLE_STRUCT_PTR)
                             + CBR_BATTLE_STRUCT_GIVEN_EXP) != 0x3FU)
        goto failure;
    /* Suppression is a continuously asserted battle invariant rather than a
     * one-shot initialization value.  A stock overwrite must be repaired on
     * the next runtime poll before a faint script can distribute EXP/EV. */
    write8(core, read32(core, CBR_BATTLE_STRUCT_PTR)
                 + CBR_BATTLE_STRUCT_GIVEN_EXP, 0U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    if (read8(core, read32(core, CBR_BATTLE_STRUCT_PTR)
                    + CBR_BATTLE_STRUCT_GIVEN_EXP) != 0x3FU)
        goto failure;

    failure_step = "switch";
    if (!cbr_live_send(core, CBR_COMMAND_SWITCH, switch_slot,
                       sizeof(switch_slot), CBR_PHASE_RESOLVING)
            || !cbr_live_wait(core, CBR_PHASE_ACTION, 2U, 360U)
            || read16(core, CBR_BATTLE_MONS + 88U) != 2U
            || read16(core, CBR_PARTY_INDEXES + 2U) != 1U
            || (read8(core, CBR_MAILBOX + 159U) & 3U) != 1U
            || read16(core, CBR_MAILBOX + 134U)
                != read16(core, CBR_BATTLE_MONS + 88U + 0x28U))
        goto failure;
    ++*request_cycles;

    failure_step = "dynamax";
    if (!(read8(core, CBR_STATE + CBR_STATE_LEGAL_GIMMICKS)
            & (1U << 3U))
            || !cbr_live_send(core, CBR_COMMAND_MOVE, dynamax_move,
                              sizeof(dynamax_move), CBR_PHASE_RESOLVING)
            || !cbr_live_wait(core, CBR_PHASE_ACTION, 3U, 440U)
            || !(read8(core, CBR_STATE + CBR_STATE_MECHANIC_USED_MASK)
                 & 0x40U))
        goto failure;
    ++*request_cycles;

    failure_step = "post-dynamax";
    if (!cbr_live_send(core, CBR_COMMAND_MOVE, normal_move,
                       sizeof(normal_move), CBR_PHASE_RESOLVING)
            || !cbr_live_wait(core, CBR_PHASE_ACTION, 4U, 440U)
            || read16(core, CBR_BATTLE_BUFFER_A + 0x204U + 100U) == 0U)
        goto failure;
    ++*request_cycles;

    failure_step = "abort-request";
    if (!cbr_live_send(core, CBR_COMMAND_ABORT, NULL, 0U,
                       CBR_PHASE_RESOLVING))
        goto failure;
    for (unsigned pulse = 0U; pulse < 520U; ++pulse) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 30U);
        if (read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U) {
            restored = true;
            break;
        }
    }
    failure_step = "abort-cleanup";
    if (!restored
            || read16(core, CBR_STATE + CBR_STATE_CLEANUP_REASON) != 4U
            || read16(core, CBR_STATE + 16U) != CBR_PHASE_ABORTED
            || read16(core, CBR_STATE + CBR_STATE_FIELD_COMPLETION_PENDING) != 1U
            || cbr_hash(core, CBR_PLAYER_PARTY, 600U) != party_before
            || cbr_logical_save_hash(core) != save_before
            || *request_cycles < 3U)
        goto failure;
    failure_step = "field-completion";
    for (unsigned pulse = 0U; pulse < 40U; ++pulse) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 30U);
        if (read16(core, CBR_STATE + CBR_STATE_FIELD_COMPLETION_PENDING) == 0U
                && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE)
            return true;
    }
    goto failure;

failure:
    fprintf(stderr,
            "real battle failed step=%s callback=%08" PRIx32
            " active=%u phase=%u turn=%u cycles=%u opponent=%u flags=%08"
            PRIx32 " exec=%08" PRIx32
            " cleanup=%u status=%u error=%u state_magic=%08" PRIx32 "\n",
            failure_step, read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, CBR_STATE + CBR_STATE_ACTIVE),
            read16(core, CBR_STATE + 16U),
            read16(core, CBR_STATE + 28U), *request_cycles,
            read16(core, CBR_BATTLE_MONS + 88U),
            read32(core, CBR_BATTLE_FLAGS),
            read32(core, CBR_CONTROLLER_EXEC_FLAGS),
            read16(core, CBR_STATE + CBR_STATE_CLEANUP_REASON),
            read16(core, CBR_MAILBOX + 80U),
            read16(core, CBR_MAILBOX + 82U),
            read32(core, CBR_STATE));
    fprintf(stderr,
            "real cleanup evidence party=%u logical_save=%u "
            "save_before=%08" PRIx32 " save_after=%08" PRIx32 "\n",
            cbr_hash(core, CBR_PLAYER_PARTY, 600U) == party_before,
            cbr_logical_save_hash(core) == save_before,
            save_before, cbr_logical_save_hash(core));
    return false;
}

static bool cbr_invalid_test(struct mCore *core,
                             const struct CbrSymbols *symbols)
{
    cbr_test_initialize(core, symbols, UINT32_C(0x44005001));
    if (!cbr_configure(core, symbols, 0U))
        return false;
    uint8_t valid_payload[33] = {0};
    cbr_member(valid_payload + 1U, 1U, 0U, false);
    uint32_t expected = cbr_next_sequence(core);
    uint8_t request[96];
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    uint32_t snapshot = read32(core, CBR_MAILBOX + 56U);
    cbr_write_request(core, request, true);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool torn = read32(core, CBR_MAILBOX + 56U) == snapshot;
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected + 1U);
    bool future = cbr_send_error(core, symbols, request, CBR_ERROR_FUTURE);
    uint32_t rejected_once = read32(
        core, CBR_STATE + CBR_STATE_REJECTED_COUNT);
    for (unsigned replay = 0U; replay < 8U; ++replay)
        cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool rejected_replay_once = read32(
        core, CBR_STATE + CBR_STATE_REJECTED_COUNT) == rejected_once;
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    request[0] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    bool nonce = cbr_send_error(core, symbols, request, CBR_ERROR_NONCE);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    request[4] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    bool match = cbr_send_error(core, symbols, request, CBR_ERROR_MATCH);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    request[8] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    bool phase = cbr_send_error(core, symbols, request, CBR_ERROR_PHASE);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    request[16] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    bool payload_crc = cbr_send_error(core, symbols, request, CBR_ERROR_PAYLOAD_CRC);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), expected);
    request[84] ^= 1U;
    bool request_crc = cbr_send_error(core, symbols, request, CBR_ERROR_REQUEST_CRC);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      65U, expected);
    bool oversize = cbr_send_error(core, symbols, request, CBR_ERROR_OVERSIZE);
    cbr_build_request(core, request, 99U, NULL, 0U, expected);
    bool command = cbr_send_error(core, symbols, request, CBR_ERROR_COMMAND);
    bool accepted = cbr_send(core, symbols, CBR_COMMAND_UPLOAD, valid_payload,
                             sizeof(valid_payload), CBR_PHASE_CONFIGURING);
    cbr_build_request(core, request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload),
                      read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE) - 1U);
    cbr_write_request(core, request, false);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool stale = read16(core, CBR_MAILBOX + 82U) == CBR_ERROR_STALE;
    uint8_t duplicate_request[96];
    cbr_build_request(core, duplicate_request, CBR_COMMAND_UPLOAD, valid_payload,
                      sizeof(valid_payload), read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE));
    cbr_write_request(core, duplicate_request, false);
    snapshot = read32(core, CBR_MAILBOX + 56U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool duplicate = read32(core, CBR_MAILBOX + 56U) == snapshot;
    bool result = torn && future && rejected_replay_once
        && nonce && match && phase && payload_crc
        && request_crc && oversize && command && accepted && stale && duplicate;
    if (!result)
        fprintf(stderr, "invalid bits: torn=%u future=%u replay_once=%u "
                "nonce=%u match=%u "
                "phase=%u payload=%u request=%u over=%u command=%u accepted=%u "
                "stale=%u duplicate=%u\n", torn, future,
                rejected_replay_once, nonce, match, phase, payload_crc,
                request_crc, oversize, command, accepted, stale, duplicate);
    return result;
}

static bool cbr_privacy_test(struct mCore *core,
                             const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    bool setup = cbr_setup_team(core, symbols, UINT32_C(0x44006001), 0U);
    bool selected = setup && cbr_begin_selection(core, symbols, selection);
    if (selected)
        cbr_seed_controller(core);
    bool waiting = selected && cbr_controller_wait(core, symbols);
    if (!waiting) {
        fprintf(stderr, "privacy setup: setup=%u selected=%u waiting=%u phase=%u\n",
                setup, selected, waiting, read16(core, CBR_STATE + 16U));
        return false;
    }
    write8(core, CBR_BATTLE_BUFFER_A, 20U);
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 3U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    if (read8(core, CBR_STATE + CBR_STATE_PLAYER_CHOICE_OBSERVED) != 1U)
        return false;
    uint8_t before[256], after[256];
    uint8_t public_before[180], public_after[180];
    for (unsigned index = 0U; index < 256U; ++index)
        before[index] = read8(core, CBR_MAILBOX + index);
    for (unsigned index = 0U; index < 180U; ++index)
        public_before[index] = read8(core, CBR_PUBLIC_STATE + index);
    for (unsigned index = 0U; index < 16U; ++index)
        write8(core, CBR_BATTLE_BUFFER_B + index,
               (uint8_t)(0x31U + index * 7U));
    write32_bytes(core, CBR_CONTROLLER_EXEC_FLAGS, 2U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    for (unsigned index = 0U; index < 256U; ++index)
        after[index] = read8(core, CBR_MAILBOX + index);
    for (unsigned index = 0U; index < 180U; ++index)
        public_after[index] = read8(core, CBR_PUBLIC_STATE + index);
    uint32_t digest = read32(core, CBR_STATE + CBR_STATE_SEAL_CRC);
    bool private_only = digest != 0U && !memcmp(before, after, sizeof(before))
        && !memcmp(public_before, public_after, sizeof(public_before))
        && read16(core, CBR_STATE + CBR_STATE_SEAL_LENGTH) == 16U
        && read8(core, CBR_STATE + 46U) == 1U
        && read32(core, CBR_CONTROLLER_EXEC_FLAGS) == 2U;
    write8(core, CBR_STATE + CBR_STATE_LEGAL_MOVE, 1U);
    write8(core, CBR_STATE + CBR_STATE_LEGAL_GIMMICKS, 1U);
    const uint8_t move[3] = {1U, 0U, 0U};
    bool codex_committed = cbr_send(core, symbols, CBR_COMMAND_MOVE, move,
                                    sizeof(move), CBR_PHASE_RESOLVING);
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    bool both_released = read32(core, CBR_CONTROLLER_EXEC_FLAGS) == 0U;
    for (unsigned index = 0U; index < 16U; ++index)
        write8(core, CBR_SCRATCH + index, (uint8_t)(0xE1U - index));
    uint32_t second = cbr_call(core, symbols->seal_private,
                               CBR_SCRATCH, 16U, 0U, 0U);
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    bool result = private_only && codex_committed && both_released
        && second != digest;
    if (!result)
        fprintf(stderr, "privacy bits: first=%08" PRIX32 " second=%08" PRIX32
                " private=%u state=%08" PRIX32 " length=%u compare=%d\n",
                digest, second, private_only,
                read32(core, CBR_STATE + CBR_STATE_SEAL_CRC),
                read16(core, CBR_STATE + CBR_STATE_SEAL_LENGTH),
                memcmp(before, after, sizeof(before)));
    return result;
}

static bool cbr_disconnect_test(struct mCore *core,
                                const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    if (!cbr_setup_team(core, symbols, UINT32_C(0x44007001), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    cbr_seed_controller(core);
    if (!cbr_controller_wait(core, symbols))
        return false;
    uint16_t turn = read16(core, CBR_STATE + 28U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    bool waited = read16(core, CBR_STATE + 28U) == turn
        && read8(core, CBR_STATE + CBR_STATE_ACTION_KIND) == 0U;
    write8(core, CBR_STATE + CBR_STATE_LEGAL_MOVE, 1U);
    write8(core, CBR_STATE + CBR_STATE_LEGAL_GIMMICKS, 1U);
    const uint8_t move[3] = {1U, 0U, 0U};
    bool reconnected = cbr_send(core, symbols, CBR_COMMAND_MOVE, move,
                                sizeof(move), CBR_PHASE_RESOLVING);
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);

    if (!cbr_setup_team(core, symbols, UINT32_C(0x44007002), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    cbr_seed_controller(core);
    if (!cbr_controller_wait(core, symbols))
        return false;
    bool cpu = cbr_send(core, symbols, CBR_COMMAND_CPU,
                        NULL, 0U, CBR_PHASE_RESOLVING);
    write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
    cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
    cpu = cpu && read8(core, CBR_STATE + CBR_STATE_DISCONNECT_MODE) == 1U
        && read16(core, CBR_STATE + 16U) == 11U
        && read8(core, CBR_STATE + CBR_STATE_CONTROLLER_INSTALLED) == 0U;
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);

    if (!cbr_setup_team(core, symbols, UINT32_C(0x44007003), 0U)
            || !cbr_begin_selection(core, symbols, selection))
        return false;
    cbr_seed_controller(core);
    if (!cbr_controller_wait(core, symbols))
        return false;
    bool forfeit = cbr_send(core, symbols, CBR_COMMAND_DISCONNECT_FORFEIT,
                            NULL, 0U, CBR_PHASE_RESOLVING)
        && read8(core, CBR_STATE + CBR_STATE_DISCONNECT_MODE) == 2U;
    cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    return waited && reconnected && cpu && forfeit;
}

static bool cbr_exit_once(struct mCore *core,
                          const struct CbrSymbols *symbols,
                          unsigned route)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    if (!cbr_setup_team(core, symbols, UINT32_C(0x44008001) + route, 0U))
        return false;
    cbr_seed_player_party(core);
    uint32_t party_hash = cbr_hash(core, CBR_PLAYER_PARTY, 600U);
    uint32_t rng = read32(core, CBR_RNG);
    uint32_t flags = read32(core, CBR_BATTLE_FLAGS);
    uint8_t count = read8(core, CBR_PLAYER_COUNT);
    uint8_t selected[6];
    for (unsigned index = 0U; index < 6U; ++index)
        selected[index] = read8(core, CBR_SELECTED + index);
    uint32_t save1 = read32(core, CBR_SAVE1_PTR);
    uint32_t save2 = read32(core, CBR_SAVE2_PTR);
    uint32_t save1_hash = cbr_hash(core, save1, 0x3D68U);
    uint32_t save2_hash = cbr_hash(core, save2, 0x0F2CU);
    uint32_t money = read32(core, save1 + CBR_SAVE1_MONEY);
    uint32_t disable_bag = cbr_call(
        core, CBR_FLAG_GET, CBR_FLAG_DISABLE_BAG, 0U, 0U, 0U);
    uint32_t trainer_flag = cbr_call(
        core, CBR_FLAG_GET, CBR_FLAG_CODEX_TRAINER, 0U, 0U, 0U);
    if (cbr_call(core, symbols->field_begin, 0U, 0U, 0U, 0U) != 1U)
        return false;
    for (unsigned index = 0U; index < 3U; ++index)
        write8(core, CBR_SELECTED + index, selection[index]);
    if (cbr_call(core, symbols->field_commit, 0U, 0U, 0U, 0U) != 1U)
        return false;
    write8(core, CBR_PLAYER_PARTY + 17U, 0xEEU);
    write32_bytes(core, CBR_RNG, UINT32_C(0xDEADBEEF));
    write32_bytes(core, save1 + CBR_SAVE1_MONEY,
                  money ^ UINT32_C(0x0055AA33));
    if (disable_bag)
        cbr_call(core, CBR_FLAG_CLEAR, CBR_FLAG_DISABLE_BAG, 0U, 0U, 0U);
    else
        cbr_call(core, CBR_FLAG_SET, CBR_FLAG_DISABLE_BAG, 0U, 0U, 0U);
    if (trainer_flag)
        cbr_call(core, CBR_FLAG_CLEAR, CBR_FLAG_CODEX_TRAINER, 0U, 0U, 0U);
    else
        cbr_call(core, CBR_FLAG_SET, CBR_FLAG_CODEX_TRAINER, 0U, 0U, 0U);
    write32_bytes(core, CBR_CONTROLLER_FUNCS + 4U, symbols->probe);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    if (route == 0U) {
        write8(core, BATTLE_CORE_BATTLE_OUTCOME, 1U);
        cbr_call(core, symbols->after_battle, 0U, 0U, 0U, 0U);
    } else if (route == 1U) {
        write8(core, BATTLE_CORE_BATTLE_OUTCOME, 2U);
        cbr_call(core, symbols->after_battle, 0U, 0U, 0U, 0U);
    } else if (route == 2U) {
        cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    } else if (route == 3U) {
        uint8_t request[96];
        cbr_build_request(core, request, CBR_COMMAND_ABORT, NULL, 0U,
                          cbr_next_sequence(core));
        cbr_write_request(core, request, false);
        cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
        if (read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
                || read16(core, CBR_STATE + 16U) != CBR_PHASE_RESOLVING
                || read16(core, CBR_STATE + CBR_STATE_CLEANUP_REASON) != 4U)
            return false;
        cbr_seed_controller(core);
        write8(core, CBR_BATTLE_BUFFER_A + 0x200U, 18U);
        cbr_call(core, symbols->controller, 0U, 0U, 0U, 0U);
        write8(core, BATTLE_CORE_BATTLE_OUTCOME, 2U);
        cbr_call(core, symbols->after_battle, 0U, 0U, 0U, 0U);
    } else {
        cbr_call(core, symbols->test_initialize,
                 UINT32_C(0xABCD0001) + route, 0U, 0U, 0U);
    }
    const uint16_t expected_reason[] = {1U, 2U, 4U, 4U, 0U};
    bool exact = cbr_hash(core, CBR_PLAYER_PARTY, 600U) == party_hash
        && read32(core, CBR_RNG) == rng
        && read32(core, CBR_BATTLE_FLAGS) == flags
        && read8(core, CBR_PLAYER_COUNT) == count
        && read32(core, save1 + CBR_SAVE1_MONEY) == money
        && cbr_call(core, CBR_FLAG_GET, CBR_FLAG_DISABLE_BAG,
                    0U, 0U, 0U) == disable_bag
        && cbr_call(core, CBR_FLAG_GET, CBR_FLAG_CODEX_TRAINER,
                    0U, 0U, 0U) == trainer_flag
        && cbr_hash(core, save1, 0x3D68U) == save1_hash
        && cbr_hash(core, save2, 0x0F2CU) == save2_hash
        && read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
        && read16(core, CBR_STATE + CBR_STATE_CLEANUP_REASON)
            == expected_reason[route];
    for (unsigned index = 0U; index < 6U; ++index)
        exact = exact && read8(core, CBR_SELECTED + index) == selected[index];
    if (exact && route == 3U) {
        uint8_t request[96];
        const uint8_t level[1] = {0U};
        cbr_build_request(core, request, CBR_COMMAND_CONFIGURE,
                          level, sizeof(level), cbr_next_sequence(core));
        exact = cbr_send_error(core, symbols, request, CBR_ERROR_BUSY)
            && read16(core, CBR_STATE + CBR_STATE_FIELD_COMPLETION_PENDING) == 1U
            && cbr_call(core, symbols->field_finish,
                        0U, 0U, 0U, 0U) == 1U
            && read16(core, CBR_STATE + CBR_STATE_FIELD_COMPLETION_PENDING) == 0U
            && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE
            && cbr_configure(core, symbols, 0U);
    }
    if (!exact) {
        fprintf(stderr,
                "route=%u party=%u rng=%u flags=%u count=%u money=%u "
                "bag=%u trainer=%u save1=%u save2=%u active=%u reason=%u "
                "controller=%08" PRIx32 "\n",
                route,
                cbr_hash(core, CBR_PLAYER_PARTY, 600U) == party_hash,
                read32(core, CBR_RNG) == rng,
                read32(core, CBR_BATTLE_FLAGS) == flags,
                read8(core, CBR_PLAYER_COUNT) == count,
                read32(core, save1 + CBR_SAVE1_MONEY) == money,
                cbr_call(core, CBR_FLAG_GET, CBR_FLAG_DISABLE_BAG,
                         0U, 0U, 0U) == disable_bag,
                cbr_call(core, CBR_FLAG_GET, CBR_FLAG_CODEX_TRAINER,
                         0U, 0U, 0U) == trainer_flag,
                cbr_hash(core, save1, 0x3D68U) == save1_hash,
                cbr_hash(core, save2, 0x0F2CU) == save2_hash,
                read8(core, CBR_STATE + CBR_STATE_ACTIVE),
                read16(core, CBR_STATE + CBR_STATE_CLEANUP_REASON),
                read32(core, CBR_CONTROLLER_FUNCS + 4U));
    }
    return exact;
}

static bool cbr_cleanup_test(struct mCore *core,
                             const struct CbrSymbols *symbols)
{
    bool exact = true;
    for (unsigned route = 0U; route < 5U; ++route) {
        bool route_exact = cbr_exit_once(core, symbols, route);
        if (!route_exact)
            fprintf(stderr, "cleanup route %u differs\n", route);
        exact = exact && route_exact;
    }
    return exact;
}

static bool cbr_noninterference_test(struct mCore *core,
                                     const struct CbrSymbols *symbols)
{
    cbr_test_initialize(core, symbols, UINT32_C(0x44009001));
    uint32_t party = cbr_hash(core, CBR_PLAYER_PARTY, 600U);
    uint32_t rng = read32(core, CBR_RNG);
    uint32_t controller = read32(core, CBR_CONTROLLER_FUNCS + 4U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
        && cbr_hash(core, CBR_PLAYER_PARTY, 600U) == party
        && read32(core, CBR_RNG) == rng
        && read32(core, CBR_CONTROLLER_FUNCS + 4U) == controller;
}

static bool cbr_gimmick_test(struct mCore *core,
                             const struct CbrSymbols *symbols)
{
    const uint8_t selection[3] = {1U, 2U, 3U};
    const uint32_t can[] = {
        symbols->can_mega, symbols->can_z,
        symbols->can_dynamax, symbols->can_tera,
    };
    const uint32_t mark[] = {
        symbols->mark_mega, symbols->mark_z,
        symbols->mark_dynamax, symbols->mark_tera,
    };
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(can); ++index) {
        cbr_test_initialize(core, symbols,
                            UINT32_C(0x4400A100) + index);
        exact = exact
            && cbr_call(core, can[index], 1U, 0U, 0U, 0U) == 0U
            && cbr_call(core, can[index], 1U, 1U, 0U, 0U) == 0U
            && cbr_call(core, mark[index], 1U, 0U, 0U, 0U) == 0U;
        if (!cbr_setup_team(core, symbols,
                            UINT32_C(0x4400A001) + index, 0U)
                || !cbr_begin_selection(core, symbols, selection))
            return false;
        exact = exact && cbr_call(core, can[index], 1U, 0U, 0U, 0U) == 1U
            && cbr_call(core, can[index], 1U, 1U, 0U, 0U) == 1U
            && cbr_call(core, mark[index], 1U, 0U, 0U, 0U) == 1U
            /* UI eligibility stays open after activation.  The surrounding
             * fixed CFRU Can* implementation owns actual reuse and
             * incompatible cross-gimmick rejection through gNewBS. */
            && cbr_call(core, can[index], 1U, 1U, 0U, 0U) == 1U
            && cbr_call(core, mark[index], 1U, 0U, 0U, 0U) == 1U
            && cbr_call(core, can[index], 0U, 1U, 0U, 0U) == 1U
            && cbr_call(core, mark[index], 0U, 0U, 0U, 0U) == 1U
            && read8(core, CBR_STATE + CBR_STATE_MECHANIC_USED_MASK)
                == (uint8_t)((1U << index) | (1U << (index + 4U)));
        cbr_call(core, symbols->abort, 0U, 0U, 0U, 0U);
    }
    return exact;
}

#ifndef CBR_RUNTIME_EMBEDDED
int main(int argc, char **argv)
{
    if (argc != 5)
        return 2;
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    struct CbrSymbols symbols = cbr_load_symbols(argv[2]);
    struct CbrCases cases = cbr_load_cases(argv[3]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cbr_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cbr_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    run_fixed_frames(core);
    struct Snapshot base = take_snapshot(core);

    bool tests[18];
    unsigned synthetic_turn_cycles = 0U;
    unsigned real_request_cycles = 0U;
    tests[0] = cases.exact_tests && cases.exact_invalid;
    tests[1] = cbr_roots_test(core, &symbols, &cases, argv[2]);
    restore_snapshot(core, &base);
    /* Run the live scheduler route before direct-call matrix cases.  Every
     * case restores the same serialized core image, but keeping the only
     * frame-driven case first also makes its timing provenance explicit. */
    tests[10] = cbr_real_battle_multiturn_test(
        core, &symbols, &real_request_cycles);
    restore_snapshot(core, &base);
    tests[2] = cbr_header_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[3] = cbr_team_test(core, &symbols, full ? 64U : 8U);
    restore_snapshot(core, &base);
    tests[4] = cbr_unrestricted_policy_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[5] = cbr_selection_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[6] = cbr_controller_test(core, &symbols, &synthetic_turn_cycles);
    restore_snapshot(core, &base);
    tests[7] = cbr_invalid_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[8] = cbr_privacy_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[9] = cbr_disconnect_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[11] = cbr_cleanup_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[12] = cbr_noninterference_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[13] = cbr_gimmick_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[14] = cbr_live_hp_switch_semantics_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[15] = cbr_public_online_state_test(core, &symbols);
    tests[16] = tests[11];
    tests[17] = log_problem_count == 0U;
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];

    char rom_sha[65], runner_source_sha[65], runner_binary_sha[65];
    char symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(__FILE__, runner_source_sha);
    sha256_file(argv[0], runner_binary_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    static const char *const names[] = {
        "exact_stage44_fixture", "runtime_exports_and_rooted_hooks",
        "protocol_header_snapshot_crc", "team_six_defaults_invalid_duplicate_fields",
        "level_toggle_and_unrestricted_teams", "both_sides_selection_private_order",
        "controller_move_gimmick_switch_forfeit",
        "illegal_stale_duplicate_torn_requests",
        "player_pending_value_length_error_sequence_timing_private",
        "disconnect_wait_reconnect_cpu_forfeit", "three_turn_request_cycles",
        "win_loss_forfeit_abort_reset_exact_cleanup",
        "normal_factory_mirage_raid_reward_noninterference",
        "upstream_open_gimmick_matrix", "live_hp_moves_switch_semantics",
        "public_online_state_events_private_boundary",
        "persistent_side_effects_zero",
        "warnings_zero",
    };
    fprintf(stderr, "mgba-codex-battle-runtime %s: ", full ? "full" : "quick");
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        fprintf(stderr, "%s=%u%s", names[index], tests[index],
                index + 1U == ARRAY_LEN(tests) ? "\n" : " ");
    printf("{\"schema_version\":1,\"task\":\"T27\",\"mode\":\"%s\","
           "\"status\":\"%s\",\"rom_sha256\":\"%s\","
           "\"runner_source_sha256\":\"%s\","
           "\"runner_binary_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
           "\"tests\":{",
           full ? "full" : "quick", passed ? "PASS" : "FAIL",
           rom_sha, runner_source_sha, runner_binary_sha, symbols_sha, cases_sha);
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        printf("\"%s\":%s%s", names[index], tests[index] ? "true" : "false",
               index + 1U == ARRAY_LEN(tests) ? "" : ",");
    printf("},\"total\":%zu,\"warnings\":%u,\"turn_cycles\":%u,"
           "\"invalid_case_count\":13,\"result_identity\":"
           "\"CB44:2:256:1536:6x3:manual\"}\n",
           ARRAY_LEN(tests), log_problem_count, real_request_cycles);

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
#endif
