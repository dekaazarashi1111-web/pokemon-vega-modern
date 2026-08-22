/* T28 focused Summary UI regression for the exact Stage 45 ROM. */
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

enum {
    CWR_UI_SPECIES_DRAGONITE = 494U,
    CWR_UI_ABILITY_MULTISCALE = 137U,
    CWR_UI_GET_MON_ABILITY = 0x090DA23DU,
    CWR_UI_ABILITY_NAMES = 0x0904B770U,
    CWR_UI_ABILITY_DESCRIPTIONS = 0x0904CC28U,
    CWR_UI_MOVE_NAMES = 0x090453C8U,
    CWR_UI_ABILITY_NAME_OFFSET = 0x318CU,
    CWR_UI_ABILITY_DESC_OFFSET = 0x3195U,
    CWR_UI_MOVE_NAMES_OFFSET = 0x3110U,
    CWR_UI_IS_EGG_OFFSET = 0x31ACU,
    CWR_UI_IS_BAD_EGG_OFFSET = 0x31B0U,
    CWR_UI_MODE_OFFSET = 0x31B4U,
    CWR_UI_CURRENT_MON_OFFSET = 0x323CU,
    CWR_UI_MAILBOX = 0x0203F900U,
    CWR_UI_REQUEST = CWR_UI_MAILBOX + 160U,
    CWR_UI_RUNTIME_STATE = 0x0203FA00U,
    CWR_UI_RUNTIME_PHASE_RESULT = 10U,
    CWR_UI_COMMAND_MON = 13U,
    CWR_UI_STATUS_ACCEPTED = 2U,
    CWR_UI_BALL_PARK = 16U,
    CWR_UI_OWNER = 0x0203D800U,
    CWR_UI_OWNER_SIZE = 128U,
    CWR_UI_OWNER_MAGIC = 0x31525743U,
    CWR_UI_OWNER_CRC_OFFSET = 12U,
    CWR_UI_OWNER_WINDOW_OFFSET = 20U,
    CWR_UI_OWNER_PHASE_OFFSET = 21U,
    CWR_UI_OWNER_SPECIES_OFFSET = 70U,
    CWR_UI_OWNER_COMMITTED_OFFSET = 104U,
    CWR_UI_OWNER_RECOVERY_OFFSET = 108U,
    CWR_UI_WINDOW_OPEN = 1U,
    CWR_UI_PHASE_COMMITTED = 3U,
    CWR_UI_FIELD_CALLBACK = 0x08055E75U,
};

static const uint16_t CWR_UI_MOVES[4] = {200U, 53U, 85U, 157U};

struct CwrUiSymbols {
    uint32_t qol_probe;
    uint32_t reward_test_open;
    uint32_t reward_poll;
};

static void cwr_ui_put16(uint8_t *raw, unsigned offset, uint16_t value)
{
    raw[offset] = (uint8_t)value;
    raw[offset + 1U] = (uint8_t)(value >> 8U);
}

static void cwr_ui_put32(uint8_t *raw, unsigned offset, uint32_t value)
{
    for (unsigned byte = 0U; byte < 4U; ++byte)
        raw[offset + byte] = (uint8_t)(value >> (byte * 8U));
}

static uint32_t cwr_ui_crc(const uint8_t *raw, size_t size)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (size_t index = 0U; index < size; ++index) {
        crc ^= raw[index];
        for (unsigned bit = 0U; bit < 8U; ++bit) {
            uint32_t mask = 0U - (crc & 1U);
            crc = (crc >> 1U) ^ (UINT32_C(0xEDB88320) & mask);
        }
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static bool cwr_ui_owner_valid(struct mCore *core)
{
    uint8_t raw[CWR_UI_OWNER_SIZE];
    for (unsigned index = 0U; index < sizeof(raw); ++index)
        raw[index] = read8(core, CWR_UI_OWNER + index);
    uint32_t expected = read32(core, CWR_UI_OWNER + CWR_UI_OWNER_CRC_OFFSET);
    memset(raw + CWR_UI_OWNER_CRC_OFFSET, 0, sizeof(uint32_t));
    return read32(core, CWR_UI_OWNER) == CWR_UI_OWNER_MAGIC
        && read32(core, CWR_UI_OWNER + 4U)
            == ~(uint32_t)CWR_UI_OWNER_MAGIC
        && read16(core, CWR_UI_OWNER + 8U) == 1U
        && read16(core, CWR_UI_OWNER + 10U) == CWR_UI_OWNER_SIZE
        && expected == cwr_ui_crc(raw, sizeof(raw));
}

static void cwr_ui_reward_payload(uint8_t raw[32])
{
    memset(raw, 0, 32U);
    cwr_ui_put16(raw, 0U, CWR_UI_SPECIES_DRAGONITE);
    raw[2] = 50U;
    raw[3] = 2U; /* hidden ability */
    for (unsigned index = 0U; index < 4U; ++index)
        cwr_ui_put16(raw, 6U + index * 2U, CWR_UI_MOVES[index]);
    raw[14] = 3U; /* Adamant */
    memset(raw + 15U, 31, 6U);
    raw[23] = 252U;
    raw[25] = 252U;
    raw[26] = 4U;
    raw[27] = 1U; /* shiny */
    raw[28] = 16U; /* Dragon Tera type */
    raw[29] = 0xFFU; /* all optional fields present */
    cwr_ui_put16(raw, 30U, 510U); /* Park Ball item ID */
}

static bool cwr_ui_deliver_reward(struct mCore *core,
                                  const struct CwrUiSymbols *symbols)
{
    const uint32_t nonce = UINT32_C(0x4500A101);
    const uint32_t match = UINT32_C(0x4500A102);
    const uint32_t sequence = 31U;
    uint8_t payload[32];
    uint8_t request[96];
    for (unsigned index = 0U; index < 6U * QOL_PARTY_MON_SIZE; ++index)
        write8(core, QOL_PLAYER_PARTY + index, 0U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 0U);
    if (call_preserving(core, symbols->reward_test_open,
                        nonce, match, 30U, 2U) != nonce)
        return false;
    cwr_ui_reward_payload(payload);
    memset(request, 0, sizeof(request));
    cwr_ui_put32(request, 0U, read32(core, CWR_UI_RUNTIME_STATE + 8U));
    cwr_ui_put32(request, 4U, read32(core, CWR_UI_RUNTIME_STATE + 12U));
    cwr_ui_put16(request, 8U,
                 read16(core, CWR_UI_RUNTIME_STATE + 16U));
    cwr_ui_put16(request, 10U, CWR_UI_COMMAND_MON);
    cwr_ui_put16(request, 12U,
                 read16(core, CWR_UI_RUNTIME_STATE + 28U));
    cwr_ui_put16(request, 14U, sizeof(payload));
    memcpy(request + 20U, payload, sizeof(payload));
    cwr_ui_put32(request, 16U, cwr_ui_crc(payload, sizeof(payload)));
    cwr_ui_put32(request, 84U, cwr_ui_crc(request, 84U));
    cwr_ui_put32(request, 88U, ~sequence);
    cwr_ui_put32(request, 92U, sequence);
    for (unsigned index = 0U; index < sizeof(request); ++index)
        write8(core, CWR_UI_REQUEST + index, request[index]);
    (void)call_preserving(core, symbols->reward_poll, 0U, 0U, 0U, 0U);
    bool exact = read32(core, CWR_UI_MAILBOX + 72U) == sequence
        && read16(core, CWR_UI_MAILBOX + 80U) == CWR_UI_STATUS_ACCEPTED
        && read16(core, CWR_UI_MAILBOX + 82U) == 0U
        && read16(core, CWR_UI_MAILBOX + 84U) == CWR_UI_COMMAND_MON
        && read8(core, QOL_PLAYER_PARTY_COUNT) == 1U
        && call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                           QOL_PLAYER_PARTY, QOL_MON_DATA_SPECIES, 0U, 0U)
                == CWR_UI_SPECIES_DRAGONITE
        && call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                           QOL_PLAYER_PARTY, QOL_MON_DATA_LEVEL, 0U, 0U) == 50U
        && call_preserving(core, CWR_UI_GET_MON_ABILITY,
                           QOL_PLAYER_PARTY, 0U, 0U, 0U)
                == CWR_UI_ABILITY_MULTISCALE;
    if (!exact) {
        fprintf(stderr, "reward delivery response=%u/%u command=%u count=%u "
                "species=%" PRIu32 " level=%" PRIu32 " ability=%" PRIu32
                "\n", read16(core, CWR_UI_MAILBOX + 80U),
                read16(core, CWR_UI_MAILBOX + 82U),
                read16(core, CWR_UI_MAILBOX + 84U),
                read8(core, QOL_PLAYER_PARTY_COUNT),
                call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                QOL_PLAYER_PARTY, QOL_MON_DATA_SPECIES,
                                0U, 0U),
                call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                QOL_PLAYER_PARTY, QOL_MON_DATA_LEVEL,
                                0U, 0U),
                call_preserving(core, CWR_UI_GET_MON_ABILITY,
                                QOL_PLAYER_PARTY, 0U, 0U, 0U));
    }
    return exact;
}

static bool cwr_ui_string_equal(struct mCore *core, uint32_t destination,
                                uint32_t source, unsigned capacity)
{
    for (unsigned index = 0U; index < capacity; ++index) {
        uint8_t expected = read8(core, source + index);
        if (read8(core, destination + index) != expected)
            return false;
        if (expected == 0xFFU)
            return true;
    }
    return false;
}

static bool cwr_ui_summary_path(struct mCore *core,
                                const struct CwrUiSymbols *symbols)
{
    struct QolSymbols qol = {0};
    qol.probe = symbols->qol_probe;
    if (!cwr_ui_deliver_reward(core, symbols)
        || !qol_enter_party_menu(core, &qol))
        return false;
    qol_press(core, QOL_KEY_A, 240U);
    qol_press(core, QOL_KEY_UP, 12U);
    qol_press(core, QOL_KEY_A, 30U);
    uint32_t summary = 0U;
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        core->runFrame(core);
        uint32_t candidate = read32(core, QOL_SUMMARY_DATA_SLOT);
        if (candidate >= 0x02000000U && candidate + 0x3308U < 0x02040000U
            && read8(core, candidate + QOL_SUMMARY_INPUT_STATE) == 2U) {
            summary = candidate;
            break;
        }
    }
    if (summary == 0U)
        return false;
    uint32_t description = read32(
        core, CWR_UI_ABILITY_DESCRIPTIONS
            + CWR_UI_ABILITY_MULTISCALE * 4U);
    bool strings = cwr_ui_string_equal(
        core, summary + CWR_UI_ABILITY_NAME_OFFSET,
        CWR_UI_ABILITY_NAMES + CWR_UI_ABILITY_MULTISCALE * 17U, 9U)
        && cwr_ui_string_equal(core, summary + CWR_UI_ABILITY_DESC_OFFSET,
                               description, 23U);
    for (unsigned index = 0U; index < 4U; ++index) {
        strings = strings && cwr_ui_string_equal(
            core, summary + CWR_UI_MOVE_NAMES_OFFSET + index * 9U,
            CWR_UI_MOVE_NAMES + CWR_UI_MOVES[index] * 16U, 9U);
    }
    bool controls = read8(core, summary + CWR_UI_IS_EGG_OFFSET) == 0U
        && read8(core, summary + CWR_UI_IS_BAD_EGG_OFFSET) == 0U
        && read8(core, summary + CWR_UI_MODE_OFFSET) == 0U
        && call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                           summary + CWR_UI_CURRENT_MON_OFFSET,
                           QOL_MON_DATA_LEVEL, 0U, 0U) == 50U;
    qol_press(core, QOL_KEY_RIGHT, 120U);
    bool page = read8(core, summary + QOL_SUMMARY_PAGE) == 1U
        && read8(core, summary + QOL_SUMMARY_INPUT_STATE) == 2U;
    qol_press(core, QOL_KEY_B, 240U);
    if (!(strings && controls && page)) {
        fprintf(stderr, "summary checks strings=%u controls=%u page=%u "
                "state=%u current_page=%u\n", strings, controls, page,
                read8(core, summary + QOL_SUMMARY_INPUT_STATE),
                read8(core, summary + QOL_SUMMARY_PAGE));
    }
    return strings && controls && page;
}

static bool cwr_ui_owner_cache_rehydrate(struct mCore *core)
{
    for (unsigned attempt = 0U; attempt < 3U
         && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                != CWR_UI_FIELD_CALLBACK; ++attempt)
        qol_press(core, QOL_KEY_B, 240U);
    bool before = read32(core, BATTLE_CORE_MAIN_CALLBACK2)
            == CWR_UI_FIELD_CALLBACK
        && cwr_ui_owner_valid(core)
        && read8(core, CWR_UI_OWNER + CWR_UI_OWNER_WINDOW_OFFSET)
            == CWR_UI_WINDOW_OPEN
        && read8(core, CWR_UI_OWNER + CWR_UI_OWNER_PHASE_OFFSET)
            == CWR_UI_PHASE_COMMITTED
        && read16(core, CWR_UI_OWNER + CWR_UI_OWNER_SPECIES_OFFSET)
            == CWR_UI_SPECIES_DRAGONITE
        && read16(core, CWR_UI_OWNER + CWR_UI_OWNER_COMMITTED_OFFSET) == 1U;
    /* Model the observed PC Storage teardown without changing flash.  The
     * hooked natural field input path, not a direct helper call, must restore
     * the independently checksummed owner. */
    write8(core, CWR_UI_REQUEST + 10U, 0U);
    write8(core, CWR_UI_REQUEST + 11U, 0U);
    for (unsigned index = 0U; index < CWR_UI_OWNER_SIZE; ++index)
        write8(core, CWR_UI_OWNER + index, 0U);
    bool restored = false;
    for (unsigned frame = 0U; frame < 600U; ++frame) {
        core->runFrame(core);
        if (cwr_ui_owner_valid(core)
            && read8(core, CWR_UI_OWNER + CWR_UI_OWNER_WINDOW_OFFSET)
                == CWR_UI_WINDOW_OPEN
            && read8(core, CWR_UI_OWNER + CWR_UI_OWNER_PHASE_OFFSET)
                == CWR_UI_PHASE_COMMITTED
            && read16(core, CWR_UI_OWNER + CWR_UI_OWNER_SPECIES_OFFSET)
                == CWR_UI_SPECIES_DRAGONITE
            && read16(core, CWR_UI_OWNER + CWR_UI_OWNER_COMMITTED_OFFSET) == 1U
            && read16(core, CWR_UI_OWNER + CWR_UI_OWNER_RECOVERY_OFFSET) >= 1U
            && read32(core, CWR_UI_MAILBOX + 88U) == 31U) {
            restored = true;
            break;
        }
    }
    if (!(before && restored))
        fprintf(stderr, "owner cache rehydrate before=%u restored=%u "
                "callback=%08" PRIx32 " owner=%u/%u/%u recovery=%u\n",
                before, restored,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, CWR_UI_OWNER + CWR_UI_OWNER_WINDOW_OFFSET),
                read8(core, CWR_UI_OWNER + CWR_UI_OWNER_PHASE_OFFSET),
                read16(core, CWR_UI_OWNER + CWR_UI_OWNER_COMMITTED_OFFSET),
                read16(core, CWR_UI_OWNER + CWR_UI_OWNER_RECOVERY_OFFSET));
    return before && restored;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM SAVE QOL_PROBE REWARD_TEST_OPEN "
                        "REWARD_POLL\n", argv[0]);
        return 2;
    }
    struct CwrUiSymbols symbols = {
        .qol_probe = qol_number(argv[3], "qol_probe"),
        .reward_test_open = qol_number(argv[4], "reward_test_open"),
        .reward_poll = qol_number(argv[5], "reward_poll"),
    };
    qol_initialize_save(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    bool boot = qol_run_field_trace(core);
    bool summary = boot && cwr_ui_summary_path(core, &symbols);
    bool rehydrate = summary && cwr_ui_owner_cache_rehydrate(core);
    bool warnings = log_problem_count == 0U;
    qol_close(core);
    bool pass = boot && summary && rehydrate && warnings;
    printf("{\"schema_version\":1,\"status\":\"%s\","
           "\"field_boot\":%s,\"summary_ui\":%s,"
           "\"owner_cache_rehydrate\":%s,"
           "\"warnings_zero\":%s}\n",
           pass ? "PASS" : "FAIL", boot ? "true" : "false",
           summary ? "true" : "false", rehydrate ? "true" : "false",
           warnings ? "true" : "false");
    return pass ? 0 : 1;
}
