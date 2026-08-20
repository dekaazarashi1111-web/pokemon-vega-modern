/* T19 exact-ROM quick/full validation for production QOL user paths. */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <errno.h>

enum {
    QOL_SAVE_SIZE = 128U * 1024U,
    QOL_MAGIC = 0x51504F4CU,
    QOL_FEATURE_COUNT = 35U,
    QOL_BOX_COUNT = 14U,
    QOL_SERVICE_PROBE = 0U,
    QOL_SERVICE_FEATURE_UNLOCKED = 1U,
    QOL_SERVICE_PC_CLEAR = 2U,
    QOL_SERVICE_PC_TOGGLE = 3U,
    QOL_SERVICE_PC_SEARCH = 4U,
    QOL_SERVICE_PC_MOVE = 5U,
    QOL_SERVICE_PC_RELEASE = 6U,
    QOL_SERVICE_PC_TAKE_ITEMS = 7U,
    QOL_SERVICE_PC_RELEARN = 8U,
    QOL_SERVICE_FIELD_PC_ALLOWED = 9U,
    QOL_SERVICE_EGG_QUEUE_CLAIM = 10U,
    QOL_SERVICE_AUTO_ALLOWED = 11U,
    QOL_SERVICE_SET_TEXT_SPEED = 12U,
    QOL_SERVICE_SET_EXP_SHARE = 13U,
    QOL_SERVICE_SET_HATCH_MODE = 14U,
    QOL_SERVICE_SET_RESEARCH_PROFILE = 15U,
    QOL_SERVICE_SELECTION_COUNT = 16U,
    QOL_SERVICE_HYPER_TRAIN = 17U,
    QOL_SERVICE_EV_RESET_ALL = 18U,
    QOL_SERVICE_SET_DAYCARE_QUEST = 19U,
    QOL_SERVICE_SET_EGG_BASKET = 20U,
    QOL_SERVICE_CLAIM_REWARD = 21U,
    QOL_SERVICE_PURCHASE_SUPPLY = 22U,
    QOL_SERVICE_SUPPLY_AVAILABLE = 23U,
    QOL_SERVICE_CONFIGURE_HIGH_RAID = 24U,
    QOL_STATUS_OK = 0U,
    QOL_STATUS_LOCKED = 1U,
    QOL_STATUS_CANCELLED = 2U,
    QOL_STATUS_INVALID_ARGUMENT = 3U,
    QOL_STATUS_EMPTY_SELECTION = 4U,
    QOL_STATUS_CAPACITY = 5U,
    QOL_STATUS_FORBIDDEN_MON = 6U,
    QOL_STATUS_FORBIDDEN_ITEM = 7U,
    QOL_STATUS_EFFECTLESS = 8U,
    QOL_STATUS_CONTEXT_FORBIDDEN = 10U,
    QOL_STATUS_PERSIST_FAILED = 11U,
    QOL_STATUS_INSUFFICIENT_CURRENCY = 14U,
    QOL_STATUS_ALREADY_CLAIMED = 15U,
    QOL_SUPPLY_RESULT_BUSY = 9U,
    QOL_KEY_A = 0x0001U,
    QOL_KEY_B = 0x0002U,
    QOL_KEY_SELECT = 0x0004U,
    QOL_KEY_START = 0x0008U,
    QOL_KEY_RIGHT = 0x0010U,
    QOL_KEY_UP = 0x0040U,
    QOL_KEY_DOWN = 0x0080U,
    QOL_KEY_L = 0x0200U,
    QOL_KEY_R = 0x0100U,
    QOL_FLAG_DH_CLEAR = 0x114BU,
    QOL_FLAG_BADGE_1 = 0x0820U,
    QOL_FLAG_BADGE_2 = 0x0821U,
    QOL_FLAG_BADGE_3 = 0x0822U,
    QOL_FLAG_BADGE_5 = 0x0824U,
    QOL_FLAG_BADGE_6 = 0x0825U,
    QOL_FLAG_BADGE_7 = 0x0826U,
    QOL_FLAG_BADGE_8 = 0x0827U,
    QOL_FLAG_HALL_OF_FAME = 0x082CU,
    QOL_FLAG_EXP_SHARE = 0x0906U,
    QOL_FLAG_EXP_SHARE_INITIALIZED = 0x12FDU,
    QOL_FLAG_DAYCARE_QUEST = 0x12FEU,
    QOL_FLAG_EGG_BASKET = 0x12FFU,
    QOL_FLAG_POKEMON_GET = 0x0828U,
    QOL_FLAG_POKEDEX_GET = 0x0829U,
    QOL_START_MENU_CALLBACK = 0x02037024U,
    QOL_START_MENU_INPUT = 0x0806EA75U,
    QOL_PSS_DATA = 0x020396FCU,
    QOL_PSS_CURSOR_AREA = 0x0203976CU,
    QOL_PSS_CURSOR_POSITION = 0x0203976DU,
    QOL_SAVE_BLOCK1_SLOT = 0x03005048U,
    QOL_SAVE_BLOCK2_SLOT = 0x0300504CU,
    QOL_SAVE_LOCATION_OFFSET = 4U,
    QOL_SAVE_OPTIONS_BUTTON_MODE_OFFSET = 0x13U,
    QOL_LEDGER = 0x0203D000U,
    QOL_LEDGER_KANTO_UNLOCKED = 16U,
    QOL_LEDGER_KANTO_VISITED = 17U,
    QOL_LEDGER_HALL_OF_FAME = 18U,
    QOL_LEDGER_LEAGUE_II = 21U,
    QOL_LEDGER_CURRENT_REGION = 23U,
    QOL_LEDGER_CERTIFICATIONS = 24U,
    QOL_LEDGER_TEXT_SPEED = 28U,
    QOL_LEDGER_HATCH_MODE = 29U,
    QOL_LEDGER_EXP_SHARE = 30U,
    QOL_LEDGER_ENCOUNTER_PROFILE = 31U,
    QOL_LEDGER_EGG_COUNT = 512U,
    QOL_LEDGER_EGG_HEAD = 513U,
    QOL_LEDGER_EGG_DATA = 514U,
    QOL_LEDGER_FACTORY_BP = 914U,
    QOL_LEDGER_CLAIM_FLAGS = 1730U,
    QOL_STATE = 0x0203B5E8U,
    QOL_STATE_SELECTION = 8U,
    QOL_STATE_SEARCH_MODES = 64U,
    QOL_STATE_AUTO_ACTIVE = 85U,
    QOL_STATE_WILD_TOKEN_ARMED = 89U,
    QOL_STATE_BATTLE_AUTO_ELIGIBLE = 90U,
    QOL_STATE_WILD_TOKEN_PID = 92U,
    QOL_STATE_BATTLE_TOKEN_PID = 96U,
    QOL_STATE_PSS_OPERATION = 248U,
    QOL_BASKET_COUNTER = 0x0203B6E4U,
    QOL_PLAYER_PARTY = 0x020241E4U,
    QOL_PLAYER_PARTY_COUNT = 0x02023F89U,
    QOL_PARTY_SCRATCH = 0x0203E300U,
    QOL_PARTY_MON_SIZE = 100U,
    QOL_BOX_MON_SIZE = 80U,
    QOL_DAYCARE_OFFSET = 0x2F80U,
    QOL_DAYCARE_PARENT_STRIDE = 140U,
    QOL_ENEMY_PARTY = 0x02023F8CU,
    QOL_BATTLE_TRAINER = 0x00000008U,
    QOL_BATTLE_DOUBLE = 0x00000001U,
    QOL_SET_BOX_MON = 0x0808B651U,
    QOL_GET_BOX_MON_DATA_AT = 0x0808B4B5U,
    QOL_GET_BOX_MON_DATA = 0x0803F4B1U,
    QOL_SET_BOX_MON_DATA = 0x0803FBC5U,
    QOL_ZERO_BOX_MON = 0x0808B751U,
    QOL_FLAG_SET = 0x0806DE75U,
    QOL_FLAG_CLEAR = 0x0806DE9DU,
    QOL_FLAG_GET = 0x0806DEC5U,
    QOL_CHECK_BAG_ITEM = 0x08099949U,
    QOL_ADD_BAG_ITEM = 0x08099A8DU,
    QOL_TRY_SAVING_DATA = 0x080DB34DU,
    QOL_SAVE_FINALIZE = 0x092D2605U,
    QOL_SAVE_INIT = 0x092D2649U,
    QOL_LOAD_GAME_DATA = 0x080DB4E5U,
    QOL_SCRIPT_CONTEXT_ENABLED = 0x08069219U,
    QOL_SET_WARP_DESTINATION = 0x08054C4DU,
    QOL_RESET_INITIAL_AVATAR = 0x080552A5U,
    QOL_WARP_INTO_MAP = 0x08054C39U,
    QOL_SET_MAIN_CALLBACK2 = 0x08000545U,
    QOL_CB2_LOAD_MAP = 0x08055FDDU,
    QOL_FIELD_CALLBACK_SLOT = 0x03005060U,
    QOL_DEFAULT_WARP_EXIT = 0x0807D695U,
    QOL_B_RETURN_WARP = 0x09220C81U,
    QOL_RANDOM_SEED = 0x03005040U,
    QOL_BATTLE_SCRIPTED_1 = 0x00002000U,
    QOL_BATTLE_SCRIPTED_2 = 0x00020000U,
    QOL_BATTLE_LEGENDARY = 0x00040000U,
    QOL_BATTLE_FRONTIER = 0x06000100U,
    QOL_BATTLE_DYNAMAX = 0x40000000U,
    QOL_BATTLE_INGAME_PARTNER = 0x00400000U,
    QOL_STAGE35_TRAINER_PROBE = 0x09302811U,
    QOL_TRAINER_OPPONENT_A = 0x020385E2U,
    QOL_DYNAMAX_COMMAND_DATA = 0x0936BF8DU,
    QOL_TERA_COMMAND_DATA = 0x0936D95CU,
    QOL_MON_DATA_NICKNAME = 2U,
    QOL_MON_DATA_SPECIES = 11U,
    QOL_MON_DATA_HELD_ITEM = 12U,
    QOL_MON_DATA_MOVE1 = 13U,
    QOL_MON_DATA_PP1 = 17U,
    QOL_MON_DATA_EXP = 25U,
    QOL_MON_DATA_HP_EV = 26U,
    QOL_MON_DATA_HP_IV = 39U,
    QOL_MON_DATA_IS_EGG = 45U,
    QOL_MON_DATA_LEVEL = 56U,
    QOL_MON_DATA_STATUS = 55U,
    QOL_SPECIES_PIKACHU = 25U,
    QOL_SPECIES_DITTO = 183U,
    QOL_ITEM_TABLE = 0x0904D108U,
    QOL_ITEM_ROW_SIZE = 40U,
    QOL_ITEM_CALLBACK_OFFSET = 24U,
    QOL_SHOW_SUMMARY = 0x08134CE5U,
    QOL_SUMMARY_DATA_SLOT = 0x0203B0B4U,
    QOL_SUMMARY_WINDOW_IDS = 0x3000U,
    QOL_SUMMARY_PAGE = 0x31C0U,
    QOL_SUMMARY_INPUT_STATE = 0x321CU,
    QOL_CB2_RETURN_TO_FIELD = 0x0805609DU,
    QOL_STATE_FILTER_MODE = 84U,
    QOL_STATE_JUDGE_IV = 132U,
    QOL_CREATE_TASK = 0x08076BB5U,
    QOL_TASK_DUMMY = 0x08076D7DU,
    QOL_TASKS = 0x030050D0U,
    QOL_TASK_SIZE = 40U,
    QOL_ITEM_USE_CALLBACK = 0x03005EE8U,
    QOL_SPECIAL_VAR_ITEM = 0x0203ACA8U,
    QOL_PARTY_MENU = 0x0203B014U,
    QOL_PARTY_MENU_SLOT = 9U,
    QOL_START_MENU_CURSOR = 0x02037028U,
    QOL_START_MENU_COUNT = 0x02037029U,
    QOL_START_MENU_ORDER = 0x0203702AU,
    QOL_CALCULATE_MON_STATS = 0x090D93A9U,
    QOL_IS_MON_SHINY = 0x08043AB9U,
    QOL_MON_DATA_HP = 57U,
    QOL_MON_DATA_MAX_HP = 58U,
};

struct QolSymbols {
    uint32_t probe;
    uint32_t dispatch;
    uint32_t read_keys;
    uint32_t pss_input;
    uint32_t text_delay;
    uint32_t should_hatch;
    uint32_t action;
    uint32_t panel;
    uint32_t save_load;
    uint32_t wild_land;
    uint32_t wild_fishing;
    uint32_t wild_begin;
    uint32_t move;
    uint32_t feature_unlocked;
    uint32_t claim_reward;
    uint32_t purchase_supply;
    uint32_t reusable_tm;
    uint32_t modify_breeding;
    uint32_t hidden;
    uint32_t common_quantity;
    uint32_t summary_input;
    uint32_t print_skills;
    uint32_t hatch_presentation;
    uint32_t give_egg;
    uint32_t give_egg_special;
    uint32_t party_count;
    uint32_t run_text;
    uint32_t apply_quantity;
    uint32_t inject_persist_fault;
    uint32_t open_supply_shop;
    uint32_t configure_trainer;
};

static const char *const QOL_FEATURE_KEYS[QOL_FEATURE_COUNT] = {
    "TEXT_SPEED_INSTANT", "FAST_MOVEMENT", "IV_EV_JUDGE",
    "PC_SEARCH_MULTISELECT", "EXP_SHARE", "EVERSTONE_SUPPLY",
    "EGG_PC_TRANSFER", "EGG_QUEUE_5", "FREE_MOVE_RELEARN",
    "PC_MOVE_EDIT", "EXP_CANDY_XS_S", "EXP_CANDY_M_ONCE",
    "ABILITY_CAPSULE_MINTS", "EV_RESET_ALL", "FIELD_PC",
    "PC_HELD_ITEM_BULK", "AUTO_BATTLE", "DESTINY_KNOT",
    "EGG_BASKET", "OVAL_CHARM", "POWER_ITEMS",
    "EXP_CANDY_M_REPEAT", "EXP_CANDY_L_SILVER_CAP",
    "ABILITY_PATCH_ALL_MINTS", "EV_RESET_ITEMS",
    "STANDARD_TRAINING_SHOP", "EXP_CANDY_XL_ONCE",
    "RESEARCH_PROFILE", "TM_REUSE_LICENSE", "HIDDEN_ABILITY_DEXNAV",
    "COMPETITIVE_ITEM_SUPPLY", "HIGH_DIFFICULTY_RAID",
    "TERA_DYNAMAX_STORY", "BOOST_ENERGY_UB_PARADOX",
    "EXP_CANDY_XL_GOLD_CAP",
};

static struct mCore *qol_log_core;

static bool qol_prepare_loaded_field(struct mCore *core);

static void qol_die(const char *message) {
    fprintf(stderr, "mgba-qol-production: %s\n", message);
    exit(1);
}

static void qol_log(struct mLogger *logger, int category,
                    enum mLogLevel level, const char *format, va_list args) {
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    /* Reattaching the same deterministic .sav to a fresh core reports the
     * host/RTC offset as a library diagnostic.  It is not a ROM warning. */
    if (strstr(mLogCategoryName(category), "Savedata") != NULL
        && strstr(format, "Savegame time offset set") != NULL)
        return;
    ++log_problem_count;
    if (log_problem_count > 12U) return;
    fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32 ": ",
            mLogCategoryName(category), (unsigned)level,
            qol_log_core ? (uint32_t)read_register(qol_log_core, "pc") : 0U);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
}

static uint32_t qol_number(const char *text, const char *label) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !text[0] || !end || *end || value > UINT32_MAX) {
        fprintf(stderr, "invalid %s: %s\n", label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static void qol_initialize_save(const char *path) {
    FILE *stream = fopen(path, "wb");
    if (!stream) qol_die("save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    for (size_t done = 0; done < QOL_SAVE_SIZE; done += sizeof(block)) {
        if (fwrite(block, 1, sizeof(block), stream) != sizeof(block))
            qol_die("save initialization failed");
    }
    if (fclose(stream) != 0) qol_die("save close failed");
}

static struct mCore *qol_open(const char *rom, const char *save) {
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom);
    if (!core || !core->init(core)) qol_die("core initialization failed");
    if (!mCoreLoadFile(core, rom)) qol_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save, false)) qol_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    return core;
}

static void qol_close(struct mCore *core) {
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
}

static uint32_t qol_stub_target(struct mCore *core, uint32_t site) {
    if (read8(core, site) != 0x00U || read8(core, site + 1U) != 0x4BU
        || read8(core, site + 2U) != 0x18U
        || read8(core, site + 3U) != 0x47U)
        return 0U;
    return read32(core, site + 4U);
}

static bool qol_hook_contract(struct mCore *core, const struct QolSymbols *s) {
    const uint32_t pairs[][2] = {
        {0x080DB4E4U, s->save_load},
        {0x080005E8U, s->read_keys},
        {0x080F8908U, s->text_delay},
        {0x0808CD48U, 0U},
        {0x0802DC14U, s->action},
        {0x0802E1ECU, s->move},
        {0x080826D8U, s->wild_land},
        {0x08082750U, s->wild_fishing},
        {0x09220198U, s->hidden},
        {0x0807EE70U, s->wild_begin},
        {0x081378B4U, s->print_skills},
        {0x080468C0U, s->hatch_presentation},
        {0x08045698U, s->give_egg},
        {0x0806CEF8U, 0U},
        {0x08127048U, 0U},
    };
    for (unsigned index = 0; index < ARRAY_LEN(pairs); ++index) {
        uint32_t target = qol_stub_target(core, pairs[index][0]);
        if (!target || (pairs[index][1] && target != pairs[index][1]))
            return false;
    }
    if (qol_stub_target(core, 0x0808CD48U) == s->pss_input
        || qol_stub_target(core, 0x0806CEF8U) == s->should_hatch)
        return false;
    if (read32(core, 0x08137570U) != s->summary_input
        || read32(core, 0x08135C0CU) != s->summary_input
        || read32(core, 0x08163274U) != s->party_count)
        return false;
    /* The unaligned printer hook owns ten bytes: a six-byte Thumb stub and
     * an aligned literal.  Its local veneer calls run_text and replays the
     * overwritten ldrb before returning to 0x08002DDC. */
    if (read8(core, 0x08002DD2U) != 0x01U
        || read8(core, 0x08002DD3U) != 0x4BU
        || read8(core, 0x08002DD4U) != 0x18U
        || read8(core, 0x08002DD5U) != 0x47U
        || read16(core, 0x08002DD6U) != 0x46C0U
        || !(read32(core, 0x08002DD8U) & 1U))
        return false;
    const uint16_t quantity_items[] = {
        63U, 64U, 65U, 66U, 67U, 68U, 70U,
        386U, 387U, 388U, 389U, 390U, 391U,
        988U, 989U, 990U, 991U, 992U,
        993U, 994U, 995U, 996U, 997U, 998U,
    };
    for (unsigned index = 0; index < ARRAY_LEN(quantity_items); ++index) {
        uint32_t callback = read32(core, QOL_ITEM_TABLE
            + (uint32_t)quantity_items[index] * QOL_ITEM_ROW_SIZE
            + QOL_ITEM_CALLBACK_OFFSET);
        if (callback != s->common_quantity)
            return false;
    }
    return true;
}

static bool qol_probe_contract(struct mCore *core, const struct QolSymbols *s) {
    const uint32_t expected[] = {QOL_MAGIC, 1U, QOL_FEATURE_COUNT,
                                 QOL_BOX_COUNT};
    for (unsigned selector = 0; selector < ARRAY_LEN(expected); ++selector) {
        if (call_preserving(core, s->probe, selector, 0, 0, 0)
            != expected[selector]) return false;
    }
    return true;
}

static bool qol_case_fixture(const char *path, bool full) {
    (void)full;
    FILE *stream = fopen(path, "r");
    if (!stream) qol_die("case fixture open failed");
    char line[256];
    if (!fgets(line, sizeof(line), stream)) qol_die("case fixture header missing");
    unsigned rows = 0;
    while (fgets(line, sizeof(line), stream)) {
        char *first = strchr(line, ',');
        char *second = first ? strchr(first + 1, ',') : NULL;
        if (!first || !second) qol_die("case fixture row malformed");
        *first = '\0';
        *second = '\0';
        char *mode = second + 1;
        mode[strcspn(mode, "\r\n")] = '\0';
        if (rows >= QOL_FEATURE_COUNT
            || strcmp(line, QOL_FEATURE_KEYS[rows]) != 0
            || first[1] == '\0' || strcmp(mode, "quick") != 0) {
            fclose(stream);
            return false;
        }
        ++rows;
    }
    if (fclose(stream) != 0) qol_die("case fixture close failed");
    return rows == QOL_FEATURE_COUNT;
}

static void qol_press(struct mCore *core, uint16_t key, uint32_t settle) {
    run_key_frames(core, key, 2U);
    run_key_frames(core, 0U, settle);
}

static void qol_pss_chord(struct mCore *core, uint16_t chord) {
    run_key_frames(core, chord, 8U);
    run_key_frames(core, 0U, 60U);
}

static bool qol_run_field_trace(struct mCore *core) {
    /* Preserve the reviewed T04/T06 natural-new-game timing exactly.  Changing
     * text speed during the recorded trace, or accepting an earlier transient
     * CB2_Overworld frame, leaves story tasks alive and is not a valid field
     * baseline for normal Start/PSS input. */
    bool default_instant = false;
    for (size_t index = 0; index < BATTLE_CORE_FIELD_TRACE_SEGMENTS; ++index) {
        unsigned problems_before = log_problem_count;
        if (index == 2U) {
            /* Assert the production default, then replay the pre-existing
             * T04/T06 boot trace at its reviewed stock/fast timing.  The
             * stable field baseline is returned to INSTANT below, where real
             * UI and battle prompt controls are exercised independently. */
            (void)call_preserving(core, QOL_SAVE_INIT, QOL_LEDGER, 0, 0, 0);
            default_instant = read8(
                core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED) == 0U;
            write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 1U);
            (void)call_preserving(core, QOL_SAVE_FINALIZE,
                                  QOL_LEDGER, 0, 0, 0);
        }
        core->setKeys(core, BOOT_TRACE[index].keys);
        for (uint32_t frame = 0; frame < BOOT_TRACE[index].frames; ++frame) {
            core->runFrame(core);
            if (log_problem_count != problems_before) {
                for (unsigned printer = 0; printer < 32U; ++printer) {
                    uint32_t address = 0x02020030U + printer * 32U;
                    if (read8(core, address + 27U))
                        fprintf(stderr, "printer=%u state=%u callback=%08" PRIx32
                                " text=%08" PRIx32 "\n", printer,
                                read8(core, address + 28U),
                                read32(core, address + 16U),
                                read32(core, address));
                }
                fprintf(stderr, "field trace first bad frame segment=%zu frame=%" PRIu32 "\n",
                        index, frame);
                break;
            }
        }
        if (log_problem_count != problems_before) {
            fprintf(stderr, "field trace segment=%zu added_logs=%u pc=%08" PRIx32 "\n",
                    index, log_problem_count - problems_before,
                    (uint32_t)read_register(core, "pc"));
            break;
        }
    }
    core->setKeys(core, 0U);
    bool loaded = qol_prepare_loaded_field(core);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    bool stable = default_instant && loaded && log_problem_count == 0U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == 0x08055E75U
        && save >= 0x02000000U && save < 0x02040000U
        && (int16_t)read16(core, save) == 8
        && (int16_t)read16(core, save + 2U) == 5
        && read8(core, QOL_PLAYER_PARTY_COUNT) >= 1U
        && read8(core, QOL_PLAYER_PARTY_COUNT) <= 6U
        && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                           0, 0, 0, 0) == 0U;
    if (!stable) {
        fprintf(stderr, "field baseline cb=%08" PRIx32 " save=%08" PRIx32
                " x=%d y=%d party=%u script=%u logs=%u\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2), save,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int16_t)read16(core, save) : -32768,
                save >= 0x02000000U && save < 0x02040000U
                    ? (int16_t)read16(core, save + 2U) : -32768,
                read8(core, QOL_PLAYER_PARTY_COUNT),
                (unsigned)call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                                          0, 0, 0, 0),
                log_problem_count);
    }
    return stable;
}

static bool qol_start_panel_user_path(struct mCore *core,
                                      const struct QolSymbols *s) {
    /* Use a progressed field fixture so the stock Start-menu action table is
     * available; the QOL text-speed row itself remains a start-unlocked row. */
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    uint32_t before = call_preserving(core, s->probe, 8U, 0, 0, 0);
    qol_press(core, QOL_KEY_START, 90U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT) {
        fprintf(stderr, "panel after START callback=%08" PRIx32 " main=%08" PRIx32 "\n",
                read32(core, QOL_START_MENU_CALLBACK),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    qol_press(core, QOL_KEY_SELECT, 10U);
    if (read32(core, QOL_START_MENU_CALLBACK) != s->panel) {
        fprintf(stderr, "panel after SELECT callback=%08" PRIx32
                " expected=%08" PRIx32 " new=%04x held=%04x\n",
                read32(core, QOL_START_MENU_CALLBACK), s->panel,
                read16(core, 0x0300315EU), read16(core, 0x0300315CU));
        return false;
    }
    qol_press(core, QOL_KEY_A, 20U);
    uint32_t changed = call_preserving(core, s->probe, 8U, 0, 0, 0);
    /* A successful action shows its visible status.  The first B dismisses
     * that status; the second returns through the stock Start-menu owner. */
    qol_press(core, QOL_KEY_B, 30U);
    qol_press(core, QOL_KEY_B, 30U);
    uint32_t after = call_preserving(core, s->probe, 8U, 0, 0, 0);
    bool returned = changed == (before + 1U) % 3U && after == changed
        && read32(core, QOL_START_MENU_CALLBACK) == QOL_START_MENU_INPUT;
    qol_press(core, QOL_KEY_B, 60U);
    return returned;
}

static void qol_copy(struct mCore *core, uint32_t destination,
                     uint32_t source, unsigned size) {
    for (unsigned index = 0; index < size; ++index)
        write8(core, destination + index, read8(core, source + index));
}

static void qol_write32(struct mCore *core, uint32_t address, uint32_t value) {
    write16(core, address, (uint16_t)value);
    write16(core, address + 2U, (uint16_t)(value >> 16));
}

static uint32_t qol_call5_preserving(struct mCore *core, uint32_t function,
                                     uint32_t r0, uint32_t r1, uint32_t r2,
                                     uint32_t r3, uint32_t stack0) {
    struct CpuState original = capture_cpu_state(core);
    uint32_t call_sp = ((uint32_t)original.registers[13] - 8U) & ~7U;
    qol_write32(core, call_sp, stack0);
    write_register(core, "sp", call_sp);
    uint32_t result = call_rom_args(core, function, r0, r1, r2, r3).return_value;
    restore_cpu_state(core, &original);
    return result;
}

static bool qol_prepare_loaded_field(struct mCore *core)
{
    /* Fixture setup only: install a valid starter and enter the authored
     * group 4/map 0 research-town host through the stock warp/load callbacks.
     * Every feature action after this point is driven through normal input. */
    create_mon(core, QOL_PLAYER_PARTY, 1U, 5U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    /* The linked Stage17 wrapper owns the five-argument ABI and the complete
     * SetWarp/ResetAvatar/Warp/FieldCallback/CB2 sequence. */
    (void)call_preserving(core, QOL_B_RETURN_WARP, 0, 0, 0, 0);
    run_key_frames(core, 0U, 1200U);
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == 0x08055E75U
        && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                           0, 0, 0, 0) == 0U;
}

static uint32_t qol_get_mon_data(struct mCore *core, uint32_t mon,
                                 uint32_t field) {
    return call_preserving(core, QOL_GET_BOX_MON_DATA, mon, field, 0, 0);
}

static uint32_t qol_get_party_data(struct mCore *core, uint32_t mon,
                                   uint32_t field) {
    return call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                           mon, field, 0, 0);
}

static void qol_set_mon_data(struct mCore *core, uint32_t mon,
                             uint32_t field, uint32_t value, unsigned size) {
    uint32_t scratch = QOL_PARTY_SCRATCH + 0x100U;
    if (size == 1U) write8(core, scratch, (uint8_t)value);
    else if (size == 2U) write16(core, scratch, (uint16_t)value);
    else qol_write32(core, scratch, value);
    (void)call_preserving(core, QOL_SET_BOX_MON_DATA, mon, field, scratch, 0);
}

static bool qol_movement_user_path(struct mCore *core) {
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    static const uint16_t directions[] = {0x0010U, 0x0020U, 0x0040U, 0x0080U};
    if (save < 0x02000000U || save >= 0x02040000U)
        return false;
    struct Snapshot base = take_snapshot(core);
    int16_t x = (int16_t)read16(core, save);
    int16_t y = (int16_t)read16(core, save + 2U);
    uint8_t group = read8(core, save + 4U);
    uint8_t map = read8(core, save + 5U);
    bool moved_with_one_hatch_check_per_tile = false;
    for (unsigned index = 0; index < ARRAY_LEN(directions); ++index) {
        restore_snapshot(core, &base);
        /* Observe the real overworld step owner without manufacturing a
         * daycare result: an empty active basket increments once in the
         * ShouldEggHatch callsite for every completed tile. */
        write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
        write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
        (void)call_preserving(core, QOL_SAVE_FINALIZE,
                              QOL_LEDGER, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET,
                              QOL_FLAG_DAYCARE_QUEST, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET,
                              QOL_FLAG_EGG_BASKET, 0, 0, 0);
        write16(core, QOL_BASKET_COUNTER, 0U);
        run_key_frames(core, directions[index], 40U);
        run_key_frames(core, 0U, 8U);
        int16_t moved_x = (int16_t)read16(core, save);
        int16_t moved_y = (int16_t)read16(core, save + 2U);
        unsigned tiles = (unsigned)(moved_x > x ? moved_x - x : x - moved_x)
            + (unsigned)(moved_y > y ? moved_y - y : y - moved_y);
        if (tiles != 0U
            && read8(core, save + 4U) == group
            && read8(core, save + 5U) == map
            && read16(core, QOL_BASKET_COUNTER) == tiles) {
            moved_with_one_hatch_check_per_tile = true;
            break;
        }
    }
    restore_snapshot(core, &base);
    free(base.bytes);
    return moved_with_one_hatch_check_per_tile;
}

static bool qol_prepare_box_mon(struct mCore *core, uint8_t box,
                                uint8_t slot, uint16_t species) {
    create_mon(core, QOL_PARTY_SCRATCH, species, 20U);
    (void)call_preserving(core, QOL_SET_BOX_MON, box, slot,
                          QOL_PARTY_SCRATCH, 0);
    return call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           box, slot, 11U, 0) == species;
}

static bool qol_prepare_box_mon_full(struct mCore *core, uint8_t box,
                                     uint8_t slot, uint16_t species,
                                     uint16_t item, bool egg,
                                     const uint8_t nickname[7]) {
    uint32_t value = QOL_PARTY_SCRATCH + 0x100U;
    create_mon(core, QOL_PARTY_SCRATCH, species, 20U);
    if (nickname) {
        for (unsigned index = 0; index < 7U; ++index)
            write8(core, value + index, nickname[index]);
        (void)call_preserving(core, QOL_SET_BOX_MON_DATA, QOL_PARTY_SCRATCH,
                              QOL_MON_DATA_NICKNAME, value, 0);
    }
    if (item != 0U)
        qol_set_mon_data(core, QOL_PARTY_SCRATCH,
                         QOL_MON_DATA_HELD_ITEM, item, 2U);
    if (egg)
        qol_set_mon_data(core, QOL_PARTY_SCRATCH,
                         QOL_MON_DATA_IS_EGG, 1U, 1U);
    (void)call_preserving(core, QOL_SET_BOX_MON, box, slot,
                          QOL_PARTY_SCRATCH, 0);
    return call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           box, slot, QOL_MON_DATA_SPECIES, 0) == species;
}

static bool qol_pss_user_path(struct mCore *core,
                              const struct QolSymbols *s) {
    (void)s;
    if (!qol_prepare_box_mon_full(core, 0U, 0U, 1U, 195U, false, NULL))
        return false;
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_2, 0, 0, 0);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save >= 0x02040000U) return false;
    write8(core, save + QOL_SAVE_LOCATION_OFFSET, 4U);
    write8(core, save + QOL_SAVE_LOCATION_OFFSET + 1U, 0U);
    qol_press(core, QOL_KEY_START, 90U);
    qol_press(core, QOL_KEY_SELECT, 10U);
    for (unsigned index = 0; index < 4U; ++index)
        qol_press(core, 0x0010U, 6U);
    qol_press(core, QOL_KEY_A, 360U);
    /* The field-PC action opens the stock withdraw/deposit/move menu. */
    qol_press(core, QOL_KEY_A, 600U);
    uint32_t pss = read32(core, QOL_PSS_DATA);
    if (pss < 0x02000000U || pss >= 0x02040000U
        || read8(core, QOL_PSS_CURSOR_AREA) != 0U
        || read8(core, QOL_PSS_CURSOR_POSITION) != 0U) {
        fprintf(stderr, "pss init data=%08" PRIx32 " area=%u pos=%u cb=%08" PRIx32 "\n",
                pss, read8(core, QOL_PSS_CURSOR_AREA),
                read8(core, QOL_PSS_CURSOR_POSITION),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    qol_pss_chord(core, QOL_KEY_SELECT);
    bool selected = (read32(core, QOL_STATE + QOL_STATE_SELECTION) & 1U) != 0U;
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    bool judge_iv = (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) & 3U) == 1U
        && save2 >= 0x02000000U && save2 < 0x02040000U
        && read8(core, save2 + QOL_SAVE_OPTIONS_BUTTON_MODE_OFFSET) == 1U;
    uint8_t state_after_select = read8(core, pss);
    core->setKeys(core, QOL_KEY_R);
    for (unsigned frame = 0U; frame < 8U; ++frame) {
        core->runFrame(core);
    }
    run_key_frames(core, 0U, 60U);
    bool judge_ev = (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) & 3U) == 2U;
    uint8_t state_after_r = read8(core, pss);
    qol_pss_chord(core, QOL_KEY_L);
    bool judge_back = (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) & 3U) == 1U;
    /* Bare SELECT toggles both the visible marker and judge overlay back off.
     * HELP remains suppressed until the stock PSS consumes its B exit. */
    qol_pss_chord(core, QOL_KEY_SELECT);
    bool cleared = read32(core, QOL_STATE + QOL_STATE_SELECTION) == 0U
        && (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) & 3U) == 0U
        && read8(core, save2 + QOL_SAVE_OPTIONS_BUTTON_MODE_OFFSET) == 1U;
    if (!selected || !judge_iv || !judge_ev || !judge_back || !cleared)
        fprintf(stderr, "pss select=%u iv=%u ev=%u back=%u cleared=%u count=%u area=%u pos=%u state=%u/%u raw=%04x/%04x keys=%04x/%04x\n",
                selected, judge_iv, judge_ev, judge_back, cleared,
                (unsigned)(read32(core, QOL_STATE + QOL_STATE_SELECTION) & 1U),
                read8(core, QOL_PSS_CURSOR_AREA),
                read8(core, QOL_PSS_CURSOR_POSITION), state_after_select,
                state_after_r, read16(core, 0x03003158U),
                read16(core, 0x0300315AU), read16(core, 0x0300315CU),
                read16(core, 0x0300315EU));
    if (!selected || !judge_iv || !judge_ev || !judge_back || !cleared)
        return false;

    /* Search is opened from the real PSS callsite.  Select the Type category
     * and its first stock ListMenu row, then verify that the production
     * filter (rather than a host-only fixture) owns the result. */
    qol_pss_chord(core, QOL_KEY_SELECT | QOL_KEY_L);
    bool search_category =
        (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 4) == 1U;
    qol_pss_chord(core, QOL_KEY_DOWN);
    qol_pss_chord(core, QOL_KEY_A);
    bool search_type =
        (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 4) == 2U;
    qol_pss_chord(core, QOL_KEY_A);
    bool search_applied =
        (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 4) == 0U
        && (read8(core, QOL_STATE + QOL_STATE_SEARCH_MODES) & 2U) != 0U;

    /* The PC relearn list and all three destructive/bulk operations must use
     * a visible stock ListMenu and accept B without mutating the BoxPokemon. */
    qol_pss_chord(core, QOL_KEY_SELECT | QOL_KEY_UP);
    bool relearn_open = read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION)
        == 0x40U;
    qol_pss_chord(core, QOL_KEY_B);
    bool relearn_cancelled =
        read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION) == 0U;

    qol_pss_chord(core, QOL_KEY_SELECT);
    bool reselected =
        (read32(core, QOL_STATE + QOL_STATE_SELECTION) & 1U) != 0U;
    qol_pss_chord(core, QOL_KEY_SELECT | QOL_KEY_A);
    bool items_confirm = read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION)
        == 0x45U;
    qol_pss_chord(core, QOL_KEY_B);
    bool items_cancelled =
        read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION) == 0U;

    qol_pss_chord(core, QOL_KEY_SELECT | QOL_KEY_R);
    bool move_confirm = read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION)
        == 0x44U;
    qol_pss_chord(core, QOL_KEY_B);
    bool move_cancelled =
        read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION) == 0U;

    qol_pss_chord(core, QOL_KEY_SELECT | QOL_KEY_START);
    bool release_confirm = read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION)
        == 0x43U;
    qol_pss_chord(core, QOL_KEY_B);
    bool release_cancelled =
        read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION) == 0U;
    qol_pss_chord(core, QOL_KEY_SELECT);
    bool final_clear = read32(core, QOL_STATE + QOL_STATE_SELECTION) == 0U
        && (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) & 3U) == 0U
        && read8(core, save2 + QOL_SAVE_OPTIONS_BUTTON_MODE_OFFSET) == 1U;
    qol_pss_chord(core, QOL_KEY_B);
    run_key_frames(core, 0U, 180U);
    bool help_restored =
        read8(core, save2 + QOL_SAVE_OPTIONS_BUTTON_MODE_OFFSET) == 0U;
    bool box_unchanged =
        call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                        0U, 0U, QOL_MON_DATA_HELD_ITEM, 0) == 195U
        && call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 0U, QOL_MON_DATA_SPECIES, 0) == 1U;
    if (!search_category || !search_type || !search_applied
        || !relearn_open || !relearn_cancelled || !reselected
        || !items_confirm || !items_cancelled
        || !move_confirm || !move_cancelled
        || !release_confirm || !release_cancelled || !final_clear
        || !help_restored || !box_unchanged) {
        fprintf(stderr, "pss menus search=%u/%u/%u relearn=%u/%u "
                "selected=%u items=%u/%u move=%u/%u release=%u/%u "
                "clear=%u restored=%u unchanged=%u op=%u mode=%02x\n",
                search_category, search_type, search_applied,
                relearn_open, relearn_cancelled, reselected,
                items_confirm, items_cancelled, move_confirm, move_cancelled,
                release_confirm, release_cancelled, final_clear,
                help_restored, box_unchanged,
                read8(core, QOL_STATE + QOL_STATE_PSS_OPERATION),
                read8(core, QOL_STATE + QOL_STATE_FILTER_MODE));
        return false;
    }
    return true;
}

static bool qol_real_box_matrix(struct mCore *core,
                                const struct QolSymbols *s) {
    if (!qol_prepare_box_mon(core, 0U, 1U, 4U)
        || !qol_prepare_box_mon(core, 1U, 0U, 7U)) return false;
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE, 0, 1, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE, 1, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_MOVE, 2, 0, 0)
            != QOL_STATUS_OK)
        return false;
    return call_preserving(core, QOL_GET_BOX_MON_DATA_AT, 0, 1, 11U, 0) == 0U
        && call_preserving(core, QOL_GET_BOX_MON_DATA_AT, 1, 0, 11U, 0) == 0U
        && call_preserving(core, QOL_GET_BOX_MON_DATA_AT, 2, 0, 11U, 0) != 0U
        && call_preserving(core, QOL_GET_BOX_MON_DATA_AT, 2, 1, 11U, 0) != 0U;
}

static bool qol_pc_atomic_matrix(struct mCore *core,
                                 const struct QolSymbols *s, bool full) {
    static const uint8_t six_char_name[7] = {
        0xA1U, 0xA2U, 0xA3U, 0xA4U, 0xA5U, 0xA6U, 0xFFU,
    };
    const uint32_t filter = QOL_PARTY_SCRATCH + 0x180U;
    if (!qol_prepare_box_mon_full(core, 3U, 1U, 1U, 0U, false,
                                  six_char_name)
        || !qol_prepare_box_mon_full(core, 9U, 29U, 500U, 0U, false,
                                     six_char_name))
        return false;
    for (unsigned index = 0; index < 16U; ++index)
        write8(core, filter + index, 0U);
    write8(core, filter, 1U);
    for (unsigned index = 0; index < 7U; ++index)
        write8(core, filter + 4U + index, six_char_name[index]);
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_SEARCH,
                        filter, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch,
                           QOL_SERVICE_SELECTION_COUNT, 0, 0, 0) != 2U)
        return false;
    /* Cancel must preserve both cross-box source slots byte-for-byte. */
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_MOVE,
                        10U, 1U, 0) != QOL_STATUS_CANCELLED
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           3U, 1U, QOL_MON_DATA_SPECIES, 0) != 1U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           9U, 29U, QOL_MON_DATA_SPECIES, 0) != 500U)
        return false;
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_MOVE,
                        10U, 0U, 0) != QOL_STATUS_OK)
        return false;
    bool added_species_moved =
        call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                        10U, 1U, QOL_MON_DATA_SPECIES, 0) == 500U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           10U, 0U, QOL_MON_DATA_SPECIES, 0) == 500U;
    if (!added_species_moved)
        return false;

    /* Egg and canonical special-event species are never released. */
    if (!qol_prepare_box_mon_full(core, 4U, 2U, 4U, 0U, true, NULL)
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                           0, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           4U, 2U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_RELEASE,
                           0U, 0U, 0) != QOL_STATUS_FORBIDDEN_MON
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           4U, 2U, QOL_MON_DATA_SPECIES, 0) != 4U)
        return false;
    if (!qol_prepare_box_mon(core, 5U, 3U, 136U)
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                           0, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           5U, 3U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_RELEASE,
                           0U, 0U, 0) != QOL_STATUS_FORBIDDEN_MON)
        return false;

    /* Held-item collection preflights all targets, preserves key items, and
     * writes the modified 80-byte scratch copy back into real PC storage. */
    if (!qol_prepare_box_mon_full(core, 6U, 4U, 7U, 195U, false, NULL)
        || !qol_prepare_box_mon_full(core, 7U, 5U, 10U, 195U, false, NULL)
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                           0, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           6U, 4U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           7U, 5U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TAKE_ITEMS,
                           1U, 0U, 0) != QOL_STATUS_CANCELLED
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           6U, 4U, QOL_MON_DATA_HELD_ITEM, 0) != 195U
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TAKE_ITEMS,
                           0U, 0U, 0) != QOL_STATUS_OK
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           6U, 4U, QOL_MON_DATA_HELD_ITEM, 0) != 0U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           7U, 5U, QOL_MON_DATA_HELD_ITEM, 0) != 0U
        || !call_preserving(core, QOL_CHECK_BAG_ITEM, 195U, 2U, 0, 0))
        return false;
    if (!qol_prepare_box_mon_full(core, 8U, 6U, 13U, 684U, false, NULL)
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                           0, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           8U, 6U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TAKE_ITEMS,
                           0U, 0U, 0) != QOL_STATUS_FORBIDDEN_ITEM
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           8U, 6U, QOL_MON_DATA_HELD_ITEM, 0) != 684U)
        return false;
    if (!full)
        return true;
    /* A full destination box fails before any source mutation. */
    for (unsigned slot = 0; slot < 30U; ++slot) {
        if (!qol_prepare_box_mon(core, 13U, (uint8_t)slot, 16U))
            return false;
    }
    if (!qol_prepare_box_mon(core, 12U, 0U, 19U)
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                           0, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           12U, 0U, 0) != QOL_STATUS_OK
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_MOVE,
                           13U, 0U, 0) != QOL_STATUS_CAPACITY
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           12U, 0U, QOL_MON_DATA_SPECIES, 0) != 19U)
        return false;
    return true;
}

static bool qol_auto_guard_matrix(struct mCore *core,
                                  const struct QolSymbols *s) {
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    uint32_t normal = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, 0U, 0U, 1U);
    uint32_t trainer = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_TRAINER, 0U, 1U);
    uint32_t shiny = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, 0U, 1U, 1U);
    uint32_t scripted_1 = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_SCRIPTED_1, 0U, 1U);
    uint32_t scripted_2 = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_SCRIPTED_2, 0U, 1U);
    uint32_t legendary = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_LEGENDARY, 0U, 1U);
    uint32_t factory = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_FRONTIER, 0U, 1U);
    uint32_t raid = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, QOL_BATTLE_DYNAMAX, 0U, 1U);
    uint32_t fainted = call_preserving(core, s->dispatch,
        QOL_SERVICE_AUTO_ALLOWED, 0U, 0U, 0U);
    return normal == QOL_STATUS_OK
        && trainer == QOL_STATUS_CONTEXT_FORBIDDEN
        && shiny == QOL_STATUS_CONTEXT_FORBIDDEN
        && scripted_1 == QOL_STATUS_CONTEXT_FORBIDDEN
        && scripted_2 == QOL_STATUS_CONTEXT_FORBIDDEN
        && legendary == QOL_STATUS_CONTEXT_FORBIDDEN
        && factory == QOL_STATUS_CONTEXT_FORBIDDEN
        && raid == QOL_STATUS_CONTEXT_FORBIDDEN
        && fainted == QOL_STATUS_CONTEXT_FORBIDDEN;
}

static bool qol_create_shiny_mon_image(
    struct mCore *core, uint16_t species, uint8_t level,
    const uint16_t moves[BATTLE_CORE_MOVE_SLOTS],
    const uint8_t pp[BATTLE_CORE_MOVE_SLOTS], uint8_t output[POKEMON_SIZE])
{
    const uint32_t identity = 0x12345678U;
    struct Snapshot original = take_snapshot(core);
    struct CpuState cpu = capture_cpu_state(core);
    uint32_t call_sp = ((uint32_t)cpu.registers[13] - 16U) & ~7U;
    /* CreateMon stack ABI: fixed personality, personality, OT-ID mode,
     * fixed OT-ID.  Equal PID/OT-ID is deterministically shiny. */
    qol_write32(core, call_sp, 1U);
    qol_write32(core, call_sp + 4U, identity);
    qol_write32(core, call_sp + 8U, 1U);
    qol_write32(core, call_sp + 12U, identity);
    write_register(core, "sp", call_sp);
    (void)call_rom_args(core, BATTLE_CORE_CREATE_MON,
                        ADDR_PLAYER_PARTY, species, level, 0x20U);
    restore_cpu_state(core, &cpu);
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                         QOL_MON_DATA_MOVE1 + slot, moves[slot]);
        set_mon_data_u32(core, ADDR_PLAYER_PARTY,
                         QOL_MON_DATA_PP1 + slot, pp[slot]);
    }
    bool valid = call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                 ADDR_PLAYER_PARTY,
                                 QOL_MON_DATA_SPECIES, 0, 0) == species
        && call_preserving(core, QOL_IS_MON_SHINY,
                           ADDR_PLAYER_PARTY, 0, 0, 0) == 1U;
    for (unsigned byte = 0U; byte < POKEMON_SIZE; ++byte)
        output[byte] = read8(core, ADDR_PLAYER_PARTY + byte);
    restore_snapshot(core, &original);
    free(original.bytes);
    return valid;
}

static bool qol_setup_shiny_auto_battle(
    struct mCore *core, const struct Snapshot *field)
{
    static const uint16_t moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0U, 0U, 0U,
    };
    static const uint8_t pp[BATTLE_CORE_MOVE_SLOTS] = {
        35U, 0U, 0U, 0U,
    };
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    create_mon_image(core, 4U, 20U, moves, pp, player);
    if (!qol_create_shiny_mon_image(core, 10U, 20U, moves, pp, enemy))
        return false;
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1U);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1U);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0U, 0U, 0U, 0U);
    run_fixed_frames(core);
    return setup.payload_pc_seen
        && read8(core, ADDR_BATTLERS_COUNT) == 2U;
}

static bool qol_auto_live_forbidden_case(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field, const char *label,
    uint32_t forbidden_flags, bool trainer, bool shiny)
{
    const uint32_t action_veneer = 0x0802DC15U;
    if (trainer) {
        struct CallObservation setup = setup_trainer(core, field);
        if (!setup.payload_pc_seen)
            return false;
    } else if (shiny) {
        if (!qol_setup_shiny_auto_battle(core, field))
            return false;
    } else {
        struct CallObservation setup = setup_wild(core, field);
        if (!setup.payload_pc_seen)
            return false;
    }
    for (unsigned prompt = 0U; prompt < 12U; ++prompt) {
        for (unsigned frame = 0U; frame < 240U; ++frame) {
            uint32_t controller = read32(core, 0x03005020U);
            if (controller != action_veneer && controller != s->action) {
                core->runFrame(core);
                continue;
            }
            uint32_t pid = read32(core, QOL_ENEMY_PARTY);
            write8(core, QOL_STATE + QOL_STATE_BATTLE_AUTO_ELIGIBLE, 1U);
            qol_write32(core, QOL_STATE + QOL_STATE_BATTLE_TOKEN_PID, pid);
            qol_write32(core, ADDR_BATTLE_TYPE_FLAGS,
                        read32(core, ADDR_BATTLE_TYPE_FLAGS)
                            | forbidden_flags);
            write8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE, 1U);
            core->setKeys(core, QOL_KEY_SELECT);
            core->runFrame(core);
            core->runFrame(core);
            core->setKeys(core, 0U);
            for (unsigned release = 0U; release < 4U; ++release)
                core->runFrame(core);
            bool blocked = read8(
                core, QOL_STATE + QOL_STATE_AUTO_ACTIVE) == 0U;
            if (!blocked)
                fprintf(stderr, "auto forbidden live %s flags=%08" PRIx32
                        " active=%u shiny=%u controller=%08" PRIx32 "\n",
                        label, read32(core, ADDR_BATTLE_TYPE_FLAGS),
                        read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE),
                        shiny, controller);
            return blocked;
        }
        run_key_frames(core, QOL_KEY_A, 2U);
        run_key_frames(core, 0U, 4U);
    }
    fprintf(stderr, "auto forbidden live %s action controller missing\n",
            label);
    return false;
}

static bool qol_auto_live_forbidden_matrix(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field)
{
    restore_snapshot(core, field);
    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_DH_CLEAR, 0, 0, 0);
    struct Snapshot unlocked = take_snapshot(core);
    bool trainer = qol_auto_live_forbidden_case(
        core, s, &unlocked, "trainer", QOL_BATTLE_TRAINER, true, false);
    bool static_wild = qol_auto_live_forbidden_case(
        core, s, &unlocked, "static", QOL_BATTLE_SCRIPTED_1, false, false);
    bool story = qol_auto_live_forbidden_case(
        core, s, &unlocked, "story", QOL_BATTLE_SCRIPTED_2, false, false);
    bool legendary = qol_auto_live_forbidden_case(
        core, s, &unlocked, "legendary", QOL_BATTLE_LEGENDARY, false, false);
    bool shiny = qol_auto_live_forbidden_case(
        core, s, &unlocked, "shiny", 0U, false, true);
    bool factory = qol_auto_live_forbidden_case(
        core, s, &unlocked, "factory", QOL_BATTLE_FRONTIER, false, false);
    bool raid = qol_auto_live_forbidden_case(
        core, s, &unlocked, "raid", QOL_BATTLE_DYNAMAX, false, false);
    free(unlocked.bytes);
    return trainer && static_wild && story && legendary
        && shiny && factory && raid;
}

static uint32_t qol_find_random_land_info(struct mCore *core)
{
    uint32_t root = read32(core, 0x0808257CU);
    if (root < 0x08000000U || root >= 0x0A000000U)
        return 0U;
    for (unsigned index = 0U; index < 1024U; ++index) {
        uint32_t header = root + index * 20U;
        uint8_t group = read8(core, header);
        uint8_t map = read8(core, header + 1U);
        if (group == 0xFFU && map == 0xFFU)
            break;
        if (group == 3U && map == 19U)
            return read32(core, header + 4U);
    }
    return 0U;
}

static uint32_t qol_mon_ev_total_live(struct mCore *core, uint32_t mon)
{
    uint32_t total = 0U;
    for (unsigned stat = 0U; stat < 6U; ++stat)
        total += read8(core, mon + 0x38U + stat);
    return total;
}

static bool qol_setup_random_auto_battle(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field, bool exp_share, bool poisoned)
{
    uint32_t land_info;
    static const uint16_t lead_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0U, 0U, 0U,
    };
    static const uint8_t lead_pp[BATTLE_CORE_MOVE_SLOTS] = {
        35U, 0U, 0U, 0U,
    };
    uint8_t lead[POKEMON_SIZE];
    uint8_t bench[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, 4U, 20U, lead_moves, lead_pp, lead);
    create_mon_image(core, 7U, 20U, NULL, NULL, bench);
    clear_parties(core);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    uint32_t exp_status = call_preserving(
        core, s->dispatch, QOL_SERVICE_SET_EXP_SHARE,
        exp_share ? 1U : 0U, 0, 0);
    if (exp_status != QOL_STATUS_OK) {
        fprintf(stderr, "auto setup exp status=%" PRIu32 "\n", exp_status);
        return false;
    }
    install_mon_image(core, QOL_PLAYER_PARTY, lead);
    install_mon_image(core, QOL_PLAYER_PARTY + QOL_PARTY_MON_SIZE, bench);
    if (poisoned)
        set_mon_data_u32(core, QOL_PLAYER_PARTY, QOL_MON_DATA_STATUS, 8U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 2U);
    land_info = qol_find_random_land_info(core);
    if (land_info < 0x08000000U || land_info >= 0x0A000000U) {
        fprintf(stderr, "auto setup land info=%08" PRIx32 "\n", land_info);
        return false;
    }
    /* This deterministic seed selects species 10 from the authored 3/19 land
     * table in one physical generation call.  It is also the T06-reviewed
     * faint/EXP scheduler fixture. */
    qol_write32(core, QOL_RANDOM_SEED, 0xC8923B53U);
    uint32_t generated = call_preserving(
        core, s->wild_land, land_info, 0U, 0U, 0U);
    uint32_t generated_species = qol_get_party_data(
        core, QOL_ENEMY_PARTY, QOL_MON_DATA_SPECIES);
    if (generated != 1U || generated_species != 10U) {
        fprintf(stderr, "auto setup generated=%" PRIu32 " species=%" PRIu32
                " info=%08" PRIx32 "\n", generated, generated_species,
                land_info);
        return false;
    }
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1U);
    uint32_t pre_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    uint32_t pre_player_species = qol_get_party_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_SPECIES);
    uint32_t pre_player_hp = qol_get_party_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_HP);
    uint32_t pre_enemy_species = qol_get_party_data(
        core, QOL_ENEMY_PARTY, QOL_MON_DATA_SPECIES);
    uint32_t pre_enemy_hp = qol_get_party_data(
        core, QOL_ENEMY_PARTY, QOL_MON_DATA_HP);
    uint8_t pre_player_count = read8(core, QOL_PLAYER_PARTY_COUNT);
    uint8_t pre_enemy_count = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT);
    /* Enter through BattleSetup_StartWildBattle.  Its patched callsite then
     * reaches s->wild_begin with the stock transition/setup context intact. */
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0U, 0U, 0U, 0U);
    if (!setup.payload_pc_seen) {
        fprintf(stderr, "auto setup did not execute battle payload\n");
        return false;
    }
    run_key_frames(core, 0U, BATTLE_CORE_FIXED_FRAMES);
    bool result = read8(core, ADDR_BATTLERS_COUNT) == 2U
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
        && (read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER) == 0U
        && read16(core, ADDR_BATTLE_MONS) == 4U
        && read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE) != 0U;
    if (!result)
        fprintf(stderr, "auto setup battle battlers=%u newbs=%08" PRIx32
                " flags=%08" PRIx32 " species=%u/%u cb=%08" PRIx32
                " pre_cb=%08" PRIx32 " counts=%u/%u pre=%" PRIu32
                "/%" PRIu32 " hp=%" PRIu32 "/%" PRIu32 "\n",
                read8(core, ADDR_BATTLERS_COUNT),
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                read32(core, ADDR_BATTLE_TYPE_FLAGS),
                read16(core, ADDR_BATTLE_MONS),
                read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2), pre_callback,
                pre_player_count, pre_enemy_count,
                pre_player_species, pre_enemy_species,
                pre_player_hp, pre_enemy_hp);
    return result;
}

static bool qol_activate_auto_from_controller(struct mCore *core,
                                               const struct QolSymbols *s)
{
    const uint32_t action_veneer = 0x0802DC15U;
    for (unsigned prompt = 0U; prompt < 12U; ++prompt) {
        /* Wait for the real player-controller function installed by the
         * ChooseAction command.  Polling its persistent callback avoids
         * guessing at the short handoff from battle text to input. */
        for (unsigned frame = 0U; frame < 240U; ++frame) {
            uint32_t controller = read32(core, 0x03005020U);
            if (controller != action_veneer && controller != s->action) {
                core->runFrame(core);
                continue;
            }
            write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR, 0U);
            write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0U);
            run_key_frames(core, QOL_KEY_SELECT, 2U);
            run_key_frames(core, 0U, 4U);
            if (read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE) == 1U)
                return true;
        }
        /* No action callback yet: advance exactly one stock opening prompt. */
        run_key_frames(core, QOL_KEY_A, 2U);
        run_key_frames(core, 0U, 4U);
    }
    fprintf(stderr, "auto activation failed active=%u eligible=%u armed=%u "
            "active_battler=%u flags=%08" PRIx32 " hp=%u pid=%08" PRIx32
            "/%08" PRIx32 " unlocked=%" PRIu32 "\n",
            read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE),
            read8(core, QOL_STATE + QOL_STATE_BATTLE_AUTO_ELIGIBLE),
            read8(core, QOL_STATE + QOL_STATE_WILD_TOKEN_ARMED),
            read8(core, 0x02023B24U),
            read32(core, ADDR_BATTLE_TYPE_FLAGS),
            read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
            read32(core, QOL_STATE + QOL_STATE_WILD_TOKEN_PID),
            read32(core, QOL_STATE + QOL_STATE_BATTLE_TOKEN_PID),
            call_preserving(core, s->feature_unlocked, 16U, 0, 0, 0));
    return false;
}

static bool qol_auto_live_turn_cancel(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field)
{
    if (!qol_setup_random_auto_battle(core, s, field, false, true))
        return false;
    uint8_t pp_before = read8(core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    uint32_t status_before = read32(
        core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_STATUS1);
    if ((status_before & 8U) == 0U
        || !qol_activate_auto_from_controller(core, s))
        return false;
    for (unsigned frame = 0U; frame < 2400U
         && read8(core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET) == pp_before;
         ++frame)
        core->runFrame(core);
    uint8_t pp_after = read8(core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET);
    for (unsigned pulse = 0U; pulse < 16U
         && read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE) != 0U;
         ++pulse) {
        run_key_frames(core, QOL_KEY_B, 2U);
        run_key_frames(core, 0U, 80U);
    }
    bool result = pp_after < pp_before
        && (read32(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_STATUS1) & 8U) != 0U
        && read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE) == 0U;
    if (!result)
        fprintf(stderr, "auto live cancel pp=%u/%u status=%08" PRIx32
                " active=%" PRIu32 " outcome=%u\n",
                pp_before, pp_after,
                read32(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_STATUS1),
                read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE),
                read8(core, BATTLE_CORE_BATTLE_OUTCOME));
    return result;
}

static bool qol_auto_live_exp_case(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field, bool exp_share)
{
    if (!qol_setup_random_auto_battle(core, s, field, exp_share, false))
        return false;
    /* T06 established the linked flat Pokemon ABI.  Passive RAM reads keep
     * the live battle scheduler untouched while EXP/EV are observed. */
    uint32_t lead_exp_before = read32(core, QOL_PLAYER_PARTY + 0x24U);
    uint32_t bench_exp_before = read32(
        core, QOL_PLAYER_PARTY + QOL_PARTY_MON_SIZE + 0x24U);
    uint32_t lead_ev_before = qol_mon_ev_total_live(core, QOL_PLAYER_PARTY);
    uint32_t bench_ev_before = qol_mon_ev_total_live(
        core, QOL_PLAYER_PARTY + QOL_PARTY_MON_SIZE);
    write16(core, ADDR_ENEMY_PARTY + POKEMON_CURRENT_HP_OFFSET, 1U);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                  + BATTLE_CORE_MON_HP, 1U);
    if (!qol_activate_auto_from_controller(core, s))
        return false;
    bool fainted = false;
    bool cleaned = false;
    uint8_t outcome = 0U;
    for (unsigned pulse = 0U; pulse < BATTLE_CORE_END_INPUT_PULSES; ++pulse) {
        core->setKeys(core, QOL_KEY_A);
        for (unsigned held = 0U; held < 10U; ++held)
            core->runFrame(core);
        for (unsigned frame = 0U; frame < BATTLE_CORE_END_INPUT_WAIT; ++frame) {
            core->setKeys(core, 0U);
            core->runFrame(core);
            if (read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                             + BATTLE_CORE_MON_HP) == 0U)
                fainted = true;
            if (outcome == 0U)
                outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
            if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U) {
                cleaned = true;
                break;
            }
        }
        if (cleaned)
            break;
    }
    run_key_frames(core, 0U, 60U);
    uint32_t lead_exp_after = read32(core, QOL_PLAYER_PARTY + 0x24U);
    uint32_t bench_exp_after = read32(
        core, QOL_PLAYER_PARTY + QOL_PARTY_MON_SIZE + 0x24U);
    uint32_t lead_ev_after = qol_mon_ev_total_live(core, QOL_PLAYER_PARTY);
    uint32_t bench_ev_after = qol_mon_ev_total_live(
        core, QOL_PLAYER_PARTY + QOL_PARTY_MON_SIZE);
    bool lead_gain = lead_exp_after > lead_exp_before
        && lead_ev_after > lead_ev_before;
    bool bench_gain = bench_exp_after > bench_exp_before
        && bench_ev_after > bench_ev_before;
    bool result = fainted && outcome == BATTLE_CORE_OUTCOME_WON && cleaned
        && lead_gain && bench_gain == exp_share
        && read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE) == 0U;
    if (!result) {
        fprintf(stderr, "auto live exp share=%u faint=%u outcome=%u clean=%u "
                "lead_exp=%" PRIu32 "/%" PRIu32 " bench_exp=%" PRIu32
                "/%" PRIu32 " lead_ev=%" PRIu32 "/%" PRIu32
                " bench_ev=%" PRIu32 "/%" PRIu32 " active=%u cb=%08"
                PRIx32 " newbs=%08" PRIx32 " ctl=%08" PRIx32
                "/%08" PRIx32 " battler=%u hp=%u/%u\n",
                exp_share, fainted, outcome, cleaned,
                lead_exp_before, lead_exp_after, bench_exp_before,
                bench_exp_after, lead_ev_before, lead_ev_after,
                bench_ev_before, bench_ev_after,
                read8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                read32(core, 0x03005020U), read32(core, 0x03005024U),
                read8(core, 0x02023B24U),
                read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
                read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                             + BATTLE_CORE_MON_HP));
    }
    return result;
}

static bool qol_auto_live_battle_matrix(
    struct mCore *core, const struct QolSymbols *s,
    const struct Snapshot *field, bool *forbidden_result)
{
    bool forbidden = qol_auto_live_forbidden_matrix(core, s, field);
    *forbidden_result = forbidden;
    bool turn_cancel = qol_auto_live_turn_cancel(core, s, field);
    bool exp_off = qol_auto_live_exp_case(core, s, field, false);
    bool exp_on = qol_auto_live_exp_case(core, s, field, true);
    if (!forbidden || !turn_cancel || !exp_off || !exp_on)
        fprintf(stderr, "auto live matrix forbidden=%u turn=%u exp_off=%u "
                "exp_on=%u\n", forbidden, turn_cancel, exp_off, exp_on);
    return forbidden && turn_cancel && exp_off && exp_on;
}

static void qol_clear_progression(struct mCore *core) {
    static const uint16_t flags[] = {
        QOL_FLAG_BADGE_1, QOL_FLAG_BADGE_2, QOL_FLAG_BADGE_3,
        QOL_FLAG_BADGE_5, QOL_FLAG_BADGE_6, QOL_FLAG_BADGE_7,
        QOL_FLAG_BADGE_8, QOL_FLAG_HALL_OF_FAME, QOL_FLAG_DH_CLEAR,
        QOL_FLAG_EXP_SHARE, QOL_FLAG_EXP_SHARE_INITIALIZED,
        QOL_FLAG_DAYCARE_QUEST, QOL_FLAG_EGG_BASKET,
    };
    for (unsigned index = 0; index < ARRAY_LEN(flags); ++index)
        (void)call_preserving(core, QOL_FLAG_CLEAR, flags[index], 0, 0, 0);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_ENCOUNTER_PROFILE, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
}

static bool qol_expect_feature_range(struct mCore *core,
                                     const struct QolSymbols *s,
                                     unsigned first, unsigned last,
                                     uint32_t expected) {
    for (unsigned feature = first; feature <= last; ++feature) {
        uint32_t actual = call_preserving(core, s->feature_unlocked,
                                          feature, 0, 0, 0);
        if (actual != expected) {
            fprintf(stderr, "unlock feature=%u actual=%" PRIu32
                    " expected=%" PRIu32 "\n", feature, actual, expected);
            return false;
        }
    }
    return true;
}

static bool qol_unlock_matrix(struct mCore *core,
                              const struct QolSymbols *s) {
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET + 280U >= 0x02040000U) {
        fprintf(stderr, "unlock invalid saveblock=%08" PRIx32 "\n", save);
        return false;
    }
    for (unsigned index = 0; index < 280U; ++index)
        write8(core, save + QOL_DAYCARE_OFFSET + index, 0U);
    qol_clear_progression(core);
    bool initial_live = qol_expect_feature_range(core, s, 0U, 3U, 1U);
    bool initial_locked = qol_expect_feature_range(core, s, 4U, 34U, 0U);
    uint32_t initial_purchase = call_preserving(
        core, s->purchase_supply, 0U, 0, 0, 0);
    if (!initial_live || !initial_locked
        || initial_purchase != QOL_STATUS_LOCKED) {
        fprintf(stderr, "unlock initial live=%u locked=%u purchase=%" PRIu32 "\n",
                initial_live, initial_locked, initial_purchase);
        return false;
    }

    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    bool badge1_features = qol_expect_feature_range(core, s, 4U, 6U, 1U);
    uint32_t free_relearn = call_preserving(
        core, s->feature_unlocked, 8U, 0, 0, 0);
    uint32_t exp_ledger = read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE);
    uint32_t exp_flag = call_preserving(
        core, QOL_FLAG_GET, QOL_FLAG_EXP_SHARE, 0, 0, 0);
    if (!badge1_features || free_relearn != 1U
        || exp_ledger != 1U || !exp_flag) {
        fprintf(stderr, "unlock badge1 features=%u relearn=%" PRIu32
                " ledger=%" PRIu32 " flag=%" PRIu32 "\n",
                badge1_features, free_relearn, exp_ledger, exp_flag);
        return false;
    }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_2, 0, 0, 0);
    if (call_preserving(core, s->feature_unlocked, 9U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock badge2 boundary failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    if (!qol_expect_feature_range(core, s, 10U, 16U, 1U))
        { fprintf(stderr, "unlock DH boundary failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_5, 0, 0, 0);
    if (call_preserving(core, s->feature_unlocked, 20U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock badge5 boundary failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_6, 0, 0, 0);
    if (call_preserving(core, s->feature_unlocked, 21U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock badge6 boundary failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_7, 0, 0, 0);
    if (call_preserving(core, s->feature_unlocked, 22U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock badge7 boundary failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_8, 0, 0, 0);
    if (!qol_expect_feature_range(core, s, 23U, 25U, 1U))
        { fprintf(stderr, "unlock badge8 boundary failed\n"); return false; }
    if (call_preserving(core, s->reusable_tm, 289U, 0, 0, 0) != 0U)
        { fprintf(stderr, "unlock pre-HOF TM failed\n"); return false; }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
    if (!qol_expect_feature_range(core, s, 26U, 29U, 1U)
        || call_preserving(core, s->reusable_tm, 289U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock HOF boundary failed\n"); return false; }
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    if (!qol_expect_feature_range(core, s, 30U, 31U, 1U))
        { fprintf(stderr, "unlock cert4 boundary failed\n"); return false; }
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    if (!qol_expect_feature_range(core, s, 32U, 34U, 1U))
        { fprintf(stderr, "unlock league boundary failed\n"); return false; }

    /* First real parent activates the shared five-egg queue owner. */
    create_mon(core, QOL_PARTY_SCRATCH, QOL_SPECIES_PIKACHU, 20U);
    qol_copy(core, save + QOL_DAYCARE_OFFSET,
             QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
    if (call_preserving(core, s->feature_unlocked, 7U, 0, 0, 0) != 1U)
        { fprintf(stderr, "unlock daycare-first boundary failed\n"); return false; }
    if (call_preserving(core, s->dispatch, QOL_SERVICE_SET_DAYCARE_QUEST,
                        1U, 0, 0) != QOL_STATUS_OK
        || !qol_expect_feature_range(core, s, 17U, 19U, 1U))
        { fprintf(stderr, "unlock daycare quest boundary failed\n"); return false; }
    return true;
}

static bool qol_raid_story_consumers(struct mCore *core,
                                     const struct QolSymbols *s,
                                     const struct Snapshot *base)
{
    const uint32_t route_mask = QOL_BATTLE_DYNAMAX | QOL_BATTLE_DOUBLE
                              | QOL_BATTLE_INGAME_PARTNER;
    restore_snapshot(core, base);
    qol_clear_progression(core);
    uint32_t flags_before = read32(core, 0x02022AACU);
    if (call_preserving(core, s->dispatch,
                        QOL_SERVICE_CONFIGURE_HIGH_RAID, 0U, 0, 0)
            != QOL_STATUS_LOCKED
        || read32(core, 0x02022AACU) != flags_before
        || call_preserving(core, s->probe, 10U, 0, 0, 0) != 0U) {
        fprintf(stderr, "raid-story locked raid failed flags=%08" PRIx32
                " before=%08" PRIx32 " probe=%" PRIu32 "\n",
                read32(core, 0x02022AACU), flags_before,
                call_preserving(core, s->probe, 10U, 0, 0, 0));
        return false;
    }

    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    if (call_preserving(core, s->dispatch,
                        QOL_SERVICE_CONFIGURE_HIGH_RAID, 0U, 0, 0)
            != QOL_STATUS_OK
        || (read32(core, 0x02022AACU) & route_mask) != route_mask
        || call_preserving(core, s->probe, 10U, 0, 0, 0) != 1U
        || call_preserving(core, s->dispatch, QOL_SERVICE_AUTO_ALLOWED,
                           read32(core, 0x02022AACU), 0U, 1U)
               != QOL_STATUS_CONTEXT_FORBIDDEN
        || call_preserving(core, s->save_load, 0U, 0, 0, 0) != 1U
        || (read32(core, 0x02022AACU) & route_mask) != 0U
        || call_preserving(core, s->probe, 10U, 0, 0, 0) != 0U) {
        fprintf(stderr, "raid-story live raid failed flags=%08" PRIx32
                " probe=%" PRIu32 "\n", read32(core, 0x02022AACU),
                call_preserving(core, s->probe, 10U, 0, 0, 0));
        return false;
    }

    restore_snapshot(core, base);
    qol_clear_progression(core);
    uint32_t next = call_preserving(core, s->configure_trainer,
                                    QOL_DYNAMAX_COMMAND_DATA, 0, 0, 0);
    if (next == 0U
        || read16(core, QOL_TRAINER_OPPONENT_A) != 130U
        || call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           9U, 0, 0, 0) != 0U
        || call_preserving(core, s->probe, 11U, 0, 0, 0) != 0U) {
        fprintf(stderr, "raid-story locked trainer failed next=%08" PRIx32
                " phase=%" PRIu32 " probe=%" PRIu32 "\n", next,
                call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                                9U, 0, 0, 0),
                call_preserving(core, s->probe, 11U, 0, 0, 0));
        return false;
    }

    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    next = call_preserving(core, s->configure_trainer,
                           QOL_DYNAMAX_COMMAND_DATA, 0, 0, 0);
    if (next == 0U
        || call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           9U, 0, 0, 0) != 1U
        || call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           12U, 0, 0, 0) != 130U
        || call_preserving(core, s->probe, 11U, 0, 0, 0) != 1U
        || call_preserving(core, s->save_load, 0U, 0, 0, 0) != 1U
        || call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           9U, 0, 0, 0) != 0U
        || call_preserving(core, s->probe, 11U, 0, 0, 0) != 0U) {
        fprintf(stderr, "raid-story live dyna failed next=%08" PRIx32
                " phase=%" PRIu32 " trainer=%" PRIu32
                " probe=%" PRIu32 "\n", next,
                call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                                9U, 0, 0, 0),
                call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                                12U, 0, 0, 0),
                call_preserving(core, s->probe, 11U, 0, 0, 0));
        return false;
    }

    restore_snapshot(core, base);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    next = call_preserving(core, s->configure_trainer,
                           QOL_TERA_COMMAND_DATA, 0, 0, 0);
    bool result = next != 0U
        && call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           9U, 0, 0, 0) == 1U
        && call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           12U, 0, 0, 0) == 208U
        && call_preserving(core, s->probe, 11U, 0, 0, 0) == 1U
        && call_preserving(core, s->save_load, 0U, 0, 0, 0) == 1U
        && call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                           9U, 0, 0, 0) == 0U;
    if (!result)
        fprintf(stderr, "raid-story tera failed next=%08" PRIx32
                " phase=%" PRIu32 " trainer=%" PRIu32
                " probe=%" PRIu32 "\n", next,
                call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                                9U, 0, 0, 0),
                call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                                12U, 0, 0, 0),
                call_preserving(core, s->probe, 11U, 0, 0, 0));
    return result;
}

static bool qol_exp_share_matrix(struct mCore *core,
                                 const struct QolSymbols *s) {
    if (!call_preserving(core, QOL_FLAG_GET, QOL_FLAG_EXP_SHARE, 0, 0, 0)
        || read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) != 1U)
        return false;
    (void)call_preserving(core, QOL_FLAG_CLEAR, QOL_FLAG_EXP_SHARE, 0, 0, 0);
    if (call_preserving(core, QOL_FLAG_GET, QOL_FLAG_EXP_SHARE, 0, 0, 0)
        || read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) != 0U)
        return false;
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_EXP_SHARE, 0, 0, 0);
    if (!call_preserving(core, QOL_FLAG_GET, QOL_FLAG_EXP_SHARE, 0, 0, 0)
        || read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) != 1U)
        return false;
    if (call_preserving(core, s->dispatch, QOL_SERVICE_SET_EXP_SHARE,
                        0U, 0, 0) != QOL_STATUS_OK
        || call_preserving(core, QOL_FLAG_GET,
                           QOL_FLAG_EXP_SHARE, 0, 0, 0) != 0U
        || read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) != 0U)
        return false;
    return call_preserving(core, s->dispatch, QOL_SERVICE_SET_EXP_SHARE,
                           1U, 0, 0) == QOL_STATUS_OK
        && call_preserving(core, QOL_FLAG_GET,
                           QOL_FLAG_EXP_SHARE, 0, 0, 0) == 1U
        && read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) == 1U;
}

static bool qol_quantity_matrix(struct mCore *core,
                                const struct QolSymbols *s) {
    const uint8_t choices[] = {0U, 1U, 2U, 3U};
    const uint16_t available[] = {10U, 10U, 10U, 3U};
    const uint16_t expected[] = {1U, 5U, 10U, 3U};
    const uint32_t result = QOL_PARTY_SCRATCH + 0x180U;
    (void)s;
    for (unsigned test = 0; test < ARRAY_LEN(choices); ++test) {
        create_mon(core, QOL_PARTY_SCRATCH, 1U, 5U);
        for (unsigned index = 0; index < 24U; ++index)
            write8(core, result + index, 0U);
        uint32_t ok = qol_call5_preserving(core, s->apply_quantity,
            QOL_PARTY_SCRATCH, 988U, choices[test], available[test], result);
        if (ok != 1U || read16(core, result + 12U) != expected[test]
            || read16(core, result + 14U) != expected[test]
            || read32(core, result + 8U) == 0U
            || qol_get_mon_data(core, QOL_PARTY_SCRATCH,
                                QOL_MON_DATA_EXP) != read32(core, result + 4U))
            return false;
    }
    /* Eggs and cap-level targets consume nothing. */
    create_mon(core, QOL_PARTY_SCRATCH, 1U, 5U);
    qol_set_mon_data(core, QOL_PARTY_SCRATCH,
                     QOL_MON_DATA_IS_EGG, 1U, 1U);
    for (unsigned index = 0; index < 24U; ++index)
        write8(core, result + index, 0U);
    if (qol_call5_preserving(core, s->apply_quantity,
            QOL_PARTY_SCRATCH, 988U, 3U, 10U, result) != 0U
        || read16(core, result + 14U) != 0U)
        return false;
    return true;
}

static bool qol_training_matrix(struct mCore *core,
                                const struct QolSymbols *s) {
    create_mon(core, QOL_PLAYER_PARTY, 1U, 100U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    for (unsigned stat = 0; stat < 6U; ++stat) {
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_IV + stat, 0U, 1U);
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_EV + stat, 40U, 1U);
    }
    uint8_t trained_before = read8(core, QOL_PLAYER_PARTY + 0x10U);
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, 853U, 1U, 0, 0)
        || call_preserving(core, s->dispatch, QOL_SERVICE_HYPER_TRAIN,
                           0U, 0U, 1U) != QOL_STATUS_CANCELLED
        || read8(core, QOL_PLAYER_PARTY + 0x10U) != trained_before
        || !call_preserving(core, QOL_CHECK_BAG_ITEM, 853U, 1U, 0, 0))
        return false;
    if (call_preserving(core, s->dispatch, QOL_SERVICE_HYPER_TRAIN,
                        0U, 0U, 0U) != QOL_STATUS_OK
        || (read8(core, QOL_PLAYER_PARTY + 0x10U) & 1U) == 0U
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 853U, 1U, 0, 0))
        return false;
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, 854U, 1U, 0, 0)
        || call_preserving(core, s->dispatch, QOL_SERVICE_HYPER_TRAIN,
                           0U, 6U, 0U) != QOL_STATUS_OK
        || (read8(core, QOL_PLAYER_PARTY + 0x10U) & 0x3FU) != 0x3FU)
        return false;
    uint8_t ev_before[6];
    for (unsigned stat = 0; stat < 6U; ++stat)
        ev_before[stat] = (uint8_t)qol_get_mon_data(
            core, QOL_PLAYER_PARTY, QOL_MON_DATA_HP_EV + stat);
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EV_RESET_ALL,
                        0U, 1U, 0U) != QOL_STATUS_CANCELLED)
        return false;
    for (unsigned stat = 0; stat < 6U; ++stat) {
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat) != ev_before[stat])
            return false;
    }
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EV_RESET_ALL,
                        0U, 0U, 0U) != QOL_STATUS_OK)
        return false;
    for (unsigned stat = 0; stat < 6U; ++stat) {
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat) != 0U)
            return false;
    }
    return true;
}

static bool qol_supply_matrix(struct mCore *core,
                              const struct QolSymbols *s) {
    const uint16_t reward_items[] = {195U, 990U, 861U, 992U};
    for (unsigned reward = 0; reward < 4U; ++reward) {
        if (call_preserving(core, s->claim_reward,
                            reward, 0, 0, 0) != QOL_STATUS_OK
            || !call_preserving(core, QOL_CHECK_BAG_ITEM,
                                reward_items[reward], 1U, 0, 0)
            || call_preserving(core, s->claim_reward,
                               reward, 0, 0, 0) != QOL_STATUS_ALREADY_CLAIMED)
            return false;
    }
    if (call_preserving(core, s->claim_reward, 4U, 0, 0, 0)
        != QOL_STATUS_ALREADY_CLAIMED)
        return false;
    for (unsigned index = 0; index < 49U; ++index) {
        if (call_preserving(core, s->dispatch, QOL_SERVICE_SUPPLY_AVAILABLE,
                            index, 0, 0) != QOL_STATUS_OK)
            return false;
    }
    write16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP, 100U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    if (call_preserving(core, s->purchase_supply, 0U, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->purchase_supply, 0U, 0, 0, 0)
            != QOL_STATUS_OK
        || read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) != 92U
        || !call_preserving(core, QOL_CHECK_BAG_ITEM, 195U, 2U, 0, 0))
        return false;
    write16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP, 1000U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    if (call_preserving(core, s->purchase_supply, 35U, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->purchase_supply, 35U, 0, 0, 0)
            != QOL_STATUS_ALREADY_CLAIMED
        || call_preserving(core, s->dispatch, QOL_SERVICE_SUPPLY_AVAILABLE,
                           35U, 0, 0) != QOL_STATUS_LOCKED
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 943U, 1U, 0, 0) != 1U
        || call_preserving(core, s->purchase_supply, 42U, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->purchase_supply, 42U, 0, 0, 0)
            != QOL_STATUS_ALREADY_CLAIMED
        || call_preserving(core, s->open_supply_shop, 0, 0, 0, 0)
            != QOL_SUPPLY_RESULT_BUSY
        || call_preserving(core, s->purchase_supply, 42U, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->purchase_supply, 43U, 0, 0, 0)
            != QOL_STATUS_OK
        || call_preserving(core, s->purchase_supply, 43U, 0, 0, 0)
            != QOL_STATUS_ALREADY_CLAIMED
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 853U, 2U, 0, 0) != 1U
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 854U, 1U, 0, 0) != 1U
        || read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) != 744U)
        return false;
    write16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    return call_preserving(core, s->purchase_supply, 48U, 0, 0, 0)
               == QOL_STATUS_INSUFFICIENT_CURRENCY
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) == 0U;
}

static bool qol_basket_boundary(struct mCore *core,
                                const struct QolSymbols *s) {
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET >= 0x02040000U) {
        fprintf(stderr, "basket invalid save=%08" PRIx32 "\n", save);
        return false;
    }
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t quest_status = call_preserving(
        core, s->dispatch, QOL_SERVICE_SET_DAYCARE_QUEST, 1U, 0, 0);
    uint32_t basket_status = quest_status == QOL_STATUS_OK
        ? call_preserving(core, s->dispatch,
                          QOL_SERVICE_SET_EGG_BASKET, 1U, 0, 0)
        : UINT32_MAX;
    if (quest_status != QOL_STATUS_OK || basket_status != QOL_STATUS_OK) {
        fprintf(stderr, "basket setup quest=%" PRIu32 " basket=%" PRIu32
                " kanto=%u/%u flags=%" PRIu32 "/%" PRIu32 "\n",
                quest_status, basket_status,
                read8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED),
                read8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED),
                call_preserving(core, QOL_FLAG_GET,
                                QOL_FLAG_DAYCARE_QUEST, 0, 0, 0),
                call_preserving(core, QOL_FLAG_GET,
                                QOL_FLAG_EGG_BASKET, 0, 0, 0));
        return false;
    }
    /* No parents: the 256-step boundary resets once without producing. */
    for (unsigned index = 0; index < 280U; ++index)
        write8(core, save + QOL_DAYCARE_OFFSET + index, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_HEAD, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    write16(core, QOL_BASKET_COUNTER, 255U);
    (void)call_preserving(core, s->should_hatch, 0, 0, 0, 0);
    if (read16(core, QOL_BASKET_COUNTER) != 0U
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 0U) {
        fprintf(stderr, "basket empty boundary counter=%u count=%u\n",
                read16(core, QOL_BASKET_COUNTER),
                read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT));
        return false;
    }

    create_mon(core, QOL_PARTY_SCRATCH, QOL_SPECIES_PIKACHU, 20U);
    qol_copy(core, save + QOL_DAYCARE_OFFSET,
             QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
    /* Vega freezes legacy Species IDs: Ditto is 183, not the DPE source ID
     * 132 (which is Garchomp in this ROM).  Use two manifest-backed parents
     * so the exact compatibility routine, rather than a zero-score fixture,
     * owns the 255/256 boundary evidence. */
    create_mon(core, QOL_PARTY_SCRATCH, QOL_SPECIES_DITTO, 20U);
    qol_copy(core, save + QOL_DAYCARE_OFFSET + QOL_DAYCARE_PARENT_STRIDE,
             QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
    qol_write32(core, QOL_RANDOM_SEED, 0U);
    write16(core, QOL_BASKET_COUNTER, 254U);
    (void)call_preserving(core, s->should_hatch, 0, 0, 0, 0);
    bool at_255 = read16(core, QOL_BASKET_COUNTER) == 255U;
    (void)call_preserving(core, s->should_hatch, 0, 0, 0, 0);
    bool at_256 = read16(core, QOL_BASKET_COUNTER) == 0U
        && read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) == 1U;
    if (!at_255 || !at_256) {
        fprintf(stderr, "basket generation at255=%u at256=%u counter=%u count=%u\n",
                at_255, at_256, read16(core, QOL_BASKET_COUNTER),
                read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT));
        fprintf(stderr, "basket parents=%" PRIu32 "/%" PRIu32
                " offspring=%u rng=%08" PRIx32
                " party=%u\n",
                call_preserving(core, QOL_GET_BOX_MON_DATA,
                                save + QOL_DAYCARE_OFFSET,
                                QOL_MON_DATA_SPECIES, 0, 0),
                call_preserving(core, QOL_GET_BOX_MON_DATA,
                                save + QOL_DAYCARE_OFFSET
                                    + QOL_DAYCARE_PARENT_STRIDE,
                                QOL_MON_DATA_SPECIES, 0, 0),
                read16(core, save + QOL_DAYCARE_OFFSET
                            + 2U * QOL_DAYCARE_PARENT_STRIDE),
                read32(core, QOL_RANDOM_SEED),
                read8(core, QOL_PLAYER_PARTY_COUNT));
        return false;
    }

    /* A full queue consumes neither a slot nor compatibility/generation RNG. */
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT, 5U);
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_HEAD, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    write16(core, QOL_BASKET_COUNTER, 255U);
    qol_write32(core, QOL_RANDOM_SEED, 0x12345678U);
    (void)call_preserving(core, s->should_hatch, 0, 0, 0, 0);
    bool result = read16(core, QOL_BASKET_COUNTER) == 0U
        && read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) == 5U
        && read32(core, QOL_RANDOM_SEED) == 0x12345678U
        && s->modify_breeding != 0U
        && call_preserving(core, s->modify_breeding, 20U, 0, 0, 0) == 40U
        && call_preserving(core, s->modify_breeding, 50U, 0, 0, 0) == 100U
        && call_preserving(core, s->modify_breeding, 70U, 0, 0, 0) == 100U;
    if (!result)
        fprintf(stderr, "basket full boundary counter=%u count=%u rng=%08" PRIx32
                " modify=%08" PRIx32 "\n",
                read16(core, QOL_BASKET_COUNTER),
                read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT),
                read32(core, QOL_RANDOM_SEED), s->modify_breeding);
    return result;
}

static bool qol_profile_hatch_matrix(struct mCore *core,
                                     const struct QolSymbols *s) {
    if (call_preserving(core, s->dispatch, QOL_SERVICE_SET_RESEARCH_PROFILE,
                        1U, 0, 0) != QOL_STATUS_OK
        || read8(core, QOL_LEDGER + QOL_LEDGER_ENCOUNTER_PROFILE) != 1U)
        return false;
    for (uint32_t mode = 0U; mode <= 2U; ++mode) {
        if (call_preserving(core, s->dispatch, QOL_SERVICE_SET_HATCH_MODE,
                            mode, 0, 0) != QOL_STATUS_OK
            || read8(core, QOL_LEDGER + QOL_LEDGER_HATCH_MODE) != mode)
            return false;
    }
    return call_preserving(core, s->dispatch, QOL_SERVICE_SET_TEXT_SPEED,
                           0U, 0, 0) == QOL_STATUS_OK
        && read8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED) == 0U;
}

static void qol_set_badges_through(struct mCore *core, unsigned milestone)
{
    static const uint16_t badge_flags[] = {
        QOL_FLAG_BADGE_1, QOL_FLAG_BADGE_2, QOL_FLAG_BADGE_3,
        QOL_FLAG_BADGE_5, QOL_FLAG_BADGE_6, QOL_FLAG_BADGE_7,
        QOL_FLAG_BADGE_8,
    };
    if (milestone > ARRAY_LEN(badge_flags))
        milestone = ARRAY_LEN(badge_flags);
    for (unsigned index = 0U; index < milestone; ++index)
        (void)call_preserving(core, QOL_FLAG_SET,
                              badge_flags[index], 0, 0, 0);
}

static bool qol_enable_feature_boundary(struct mCore *core,
                                        const struct QolSymbols *s,
                                        unsigned feature) {
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET + 280U >= 0x02040000U)
        return false;
    for (unsigned index = 0; index < 280U; ++index)
        write8(core, save + QOL_DAYCARE_OFFSET + index, 0U);
    qol_clear_progression(core);
    uint32_t before = call_preserving(core, s->feature_unlocked,
                                      feature, 0, 0, 0);
    if (feature < 4U)
        return before == 1U;
    if (before != 0U)
        return false;
    switch (feature) {
    case 4U: case 5U: case 6U: case 8U:
        qol_set_badges_through(core, 1U);
        break;
    case 7U:
        qol_set_badges_through(core, 1U);
        create_mon(core, QOL_PARTY_SCRATCH, 1U, 20U);
        qol_copy(core, save + QOL_DAYCARE_OFFSET,
                 QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
        break;
    case 9U:
        qol_set_badges_through(core, 2U);
        break;
    case 10U: case 11U: case 12U: case 13U: case 14U: case 15U: case 16U:
        qol_set_badges_through(core, 3U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        break;
    case 17U: case 18U: case 19U:
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET,
                              QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
        write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
        write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
        (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
        if (call_preserving(core, s->dispatch, QOL_SERVICE_SET_DAYCARE_QUEST,
                            1U, 0, 0) != QOL_STATUS_OK)
            return false;
        break;
    case 20U:
        qol_set_badges_through(core, 4U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        break;
    case 21U:
        qol_set_badges_through(core, 5U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        break;
    case 22U:
        qol_set_badges_through(core, 6U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        break;
    case 23U: case 24U: case 25U:
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        break;
    case 26U: case 27U: case 28U: case 29U:
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME,
                              0, 0, 0);
        break;
    case 30U: case 31U:
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME,
                              0, 0, 0);
        write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
        (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
        break;
    case 32U: case 33U: case 34U:
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
        (void)call_preserving(core, QOL_FLAG_SET,
                              QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
        write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
        write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
        (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
        break;
    default:
        return false;
    }
    return call_preserving(core, s->feature_unlocked,
                           feature, 0, 0, 0) == 1U;
}

static bool qol_purchase_case(struct mCore *core,
                              const struct QolSymbols *s,
                              uint8_t catalog_index, uint16_t item,
                              uint16_t price, uint8_t purchases) {
    const uint16_t starting_bp = 1000U;
    write16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP, starting_bp);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    for (uint8_t count = 0U; count < purchases; ++count) {
        uint32_t status = call_preserving(core, s->purchase_supply,
                                          catalog_index, 0, 0, 0);
        if (status != QOL_STATUS_OK) {
            fprintf(stderr, "purchase index=%u item=%u pass=%u status=%" PRIu32
                    " bp=%u bag=%" PRIu32 "\n",
                    catalog_index, item, count, status,
                    read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP),
                    call_preserving(core, QOL_CHECK_BAG_ITEM,
                                    item, 1U, 0, 0));
            return false;
        }
    }
    bool result = read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
                      == (uint16_t)(starting_bp - price * purchases)
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           item, purchases, 0, 0) == 1U;
    if (!result)
        fprintf(stderr, "purchase verify index=%u item=%u bp=%u expected=%u "
                "bag=%" PRIu32 "\n", catalog_index, item,
                read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP),
                (uint16_t)(starting_bp - price * purchases),
                call_preserving(core, QOL_CHECK_BAG_ITEM,
                                item, purchases, 0, 0));
    return result;
}

static bool qol_reward_case(struct mCore *core,
                            const struct QolSymbols *s,
                            uint8_t reward, uint16_t item) {
    uint32_t first = call_preserving(core, s->claim_reward,
                                     reward, 0, 0, 0);
    uint32_t second = call_preserving(core, s->claim_reward,
                                      reward, 0, 0, 0);
    return first == QOL_STATUS_OK && second == QOL_STATUS_ALREADY_CLAIMED
        && call_preserving(core, QOL_CHECK_BAG_ITEM, item, 1U, 0, 0) == 1U;
}

static bool qol_reload_from_flash(struct mCore *core)
{
    return call_preserving(core, QOL_LOAD_GAME_DATA, 0, 0, 0, 0) == 1U;
}

static bool qol_fault_reward_single(struct mCore *core,
                                    const struct QolSymbols *s,
                                    const struct Snapshot *base,
                                    uint8_t fault_mode)
{
    restore_snapshot(core, base);
    if (!qol_enable_feature_boundary(core, s, 5U)
        || call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U
        || call_preserving(core, s->inject_persist_fault,
                           fault_mode, 0, 0, 0) != 1U
        || call_preserving(core, s->claim_reward, 0U, 0, 0, 0)
               != QOL_STATUS_PERSIST_FAILED
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 195U, 1U, 0, 0) != 0U
        || !qol_reload_from_flash(core)
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 195U, 1U, 0, 0) != 0U
        || call_preserving(core, s->claim_reward, 0U, 0, 0, 0)
               != QOL_STATUS_OK
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 195U, 1U, 0, 0) != 1U
        || call_preserving(core, s->claim_reward, 0U, 0, 0, 0)
               != QOL_STATUS_ALREADY_CLAIMED)
        return false;
    return true;
}

static bool qol_fault_reward_power(struct mCore *core,
                                   const struct QolSymbols *s,
                                   const struct Snapshot *base,
                                   uint8_t fault_mode)
{
    static const uint16_t items[6] = {861U, 856U, 857U, 858U, 859U, 860U};
    restore_snapshot(core, base);
    if (!qol_enable_feature_boundary(core, s, 20U)
        || call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U
        || call_preserving(core, s->inject_persist_fault,
                           fault_mode, 0, 0, 0) != 1U
        || call_preserving(core, s->claim_reward, 2U, 0, 0, 0)
               != QOL_STATUS_PERSIST_FAILED)
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(items); ++index) {
        if (call_preserving(core, QOL_CHECK_BAG_ITEM,
                            items[index], 1U, 0, 0) != 0U)
            return false;
    }
    if (!qol_reload_from_flash(core))
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(items); ++index) {
        if (call_preserving(core, QOL_CHECK_BAG_ITEM,
                            items[index], 1U, 0, 0) != 0U)
            return false;
    }
    if (call_preserving(core, s->claim_reward, 2U, 0, 0, 0)
            != QOL_STATUS_OK)
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(items); ++index) {
        if (call_preserving(core, QOL_CHECK_BAG_ITEM,
                            items[index], 1U, 0, 0) != 1U)
            return false;
    }
    return call_preserving(core, s->claim_reward, 2U, 0, 0, 0)
               == QOL_STATUS_ALREADY_CLAIMED;
}

static bool qol_fault_reward_daycare(struct mCore *core,
                                     const struct QolSymbols *s,
                                     const struct Snapshot *base,
                                     uint8_t fault_mode)
{
    uint32_t status = UINT32_MAX;
    restore_snapshot(core, base);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_DAYCARE_QUEST, 0, 0, 0);
    if (call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U)
        goto failed;
    if (call_preserving(core, s->inject_persist_fault,
                        fault_mode, 0, 0, 0) != 1U)
        goto failed;
    status = call_preserving(core, s->claim_reward, 4U, 0, 0, 0);
    if (status != QOL_STATUS_PERSIST_FAILED
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 902U, 1U, 0, 0) != 0U
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 684U, 1U, 0, 0) != 0U)
        goto failed;
    if (!qol_reload_from_flash(core)
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 902U, 1U, 0, 0) != 0U
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 684U, 1U, 0, 0) != 0U)
        goto failed;
    status = call_preserving(core, s->claim_reward, 4U, 0, 0, 0);
    if (status != QOL_STATUS_OK
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 902U, 1U, 0, 0) != 1U
        || call_preserving(core, QOL_CHECK_BAG_ITEM, 684U, 1U, 0, 0) != 1U
        || call_preserving(core, s->claim_reward, 4U, 0, 0, 0)
               != QOL_STATUS_ALREADY_CLAIMED)
        goto failed;
    return true;
failed:
    fprintf(stderr, "daycare fault detail mode=%u status=%" PRIu32
            " flag=%" PRIu32 " knot=%" PRIu32 " oval=%" PRIu32
            " kanto=%u/%u\n", fault_mode, status,
            call_preserving(core, QOL_FLAG_GET,
                            QOL_FLAG_DAYCARE_QUEST, 0, 0, 0),
            call_preserving(core, QOL_CHECK_BAG_ITEM, 902U, 1U, 0, 0),
            call_preserving(core, QOL_CHECK_BAG_ITEM, 684U, 1U, 0, 0),
            read8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED),
            read8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED));
    return false;
}

static void qol_seed_egg_queue(struct mCore *core, uint8_t count) {
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT, count);
    write8(core, QOL_LEDGER + QOL_LEDGER_EGG_HEAD, 0U);
    for (uint8_t index = 0U; index < count; ++index) {
        create_mon(core, QOL_PARTY_SCRATCH, (uint16_t)(1U + index), 5U);
        qol_copy(core, QOL_LEDGER + QOL_LEDGER_EGG_DATA
                         + (uint32_t)index * QOL_BOX_MON_SIZE,
                 QOL_PARTY_SCRATCH, QOL_BOX_MON_SIZE);
    }
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
}

static bool qol_fault_queue_bulk(struct mCore *core,
                                 const struct QolSymbols *s,
                                 const struct Snapshot *base,
                                 uint8_t fault_mode)
{
    restore_snapshot(core, base);
    (void)call_preserving(core, QOL_ZERO_BOX_MON, 0U, 0U, 0, 0);
    (void)call_preserving(core, QOL_ZERO_BOX_MON, 0U, 1U, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    qol_seed_egg_queue(core, 2U);
    if (call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U
        || call_preserving(core, s->inject_persist_fault,
                           fault_mode, 0, 0, 0) != 1U
        || call_preserving(core, s->dispatch, QOL_SERVICE_EGG_QUEUE_CLAIM,
                           0U, 0, 0) != QOL_STATUS_PERSIST_FAILED
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 2U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 0U, QOL_MON_DATA_SPECIES, 0) != 0U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 1U, QOL_MON_DATA_SPECIES, 0) != 0U
        || !qol_reload_from_flash(core)
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 2U
        || call_preserving(core, s->dispatch, QOL_SERVICE_EGG_QUEUE_CLAIM,
                           0U, 0, 0) != QOL_STATUS_OK
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 0U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 0U, QOL_MON_DATA_SPECIES, 0) == 0U
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 1U, QOL_MON_DATA_SPECIES, 0) == 0U)
        return false;
    return true;
}

static void qol_prepare_party_count(struct mCore *core, uint8_t count)
{
    for (unsigned slot = 0U; slot < 6U; ++slot) {
        uint32_t mon = QOL_PLAYER_PARTY + slot * 100U;
        for (unsigned byte = 0U; byte < 100U; ++byte)
            write8(core, mon + byte, 0U);
        if (slot < count)
            create_mon(core, mon, (uint16_t)(1U + slot), 20U);
    }
    write8(core, QOL_PLAYER_PARTY_COUNT, count);
}

static bool qol_fault_queue_receive(struct mCore *core,
                                    const struct QolSymbols *s,
                                    const struct Snapshot *base,
                                    uint8_t fault_mode, bool pc_delivery)
{
    restore_snapshot(core, base);
    (void)call_preserving(core, QOL_ZERO_BOX_MON, 0U, 0U, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    qol_prepare_party_count(core, pc_delivery ? 6U : 1U);
    qol_seed_egg_queue(core, 1U);
    uint32_t save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET >= 0x02040000U
        || call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) != 1U
        || call_preserving(core, s->inject_persist_fault,
                           fault_mode, 0, 0, 0) != 1U)
        return false;
    uint32_t failed_status = call_preserving(
        core, s->give_egg_special, 0, 0, 0, 0);
    if (failed_status != QOL_STATUS_PERSIST_FAILED
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 1U
        || read8(core, QOL_PLAYER_PARTY_COUNT) != (pc_delivery ? 6U : 1U)
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 0U, QOL_MON_DATA_SPECIES, 0) != 0U
        || (!pc_delivery
            && qol_get_party_data(core, QOL_PLAYER_PARTY + 100U,
                                  QOL_MON_DATA_SPECIES) != 0U)
        || !qol_reload_from_flash(core)
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 1U)
        return false;
    save = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save < 0x02000000U || save + QOL_DAYCARE_OFFSET >= 0x02040000U
        || call_preserving(core, s->give_egg_special, 0, 0, 0, 0)
               != QOL_STATUS_OK
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 0U)
        return false;
    if (pc_delivery)
        return call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                               0U, 0U, QOL_MON_DATA_SPECIES, 0) != 0U;
    return read8(core, QOL_PLAYER_PARTY_COUNT) == 2U
        && qol_get_party_data(core, QOL_PLAYER_PARTY + 100U,
                              QOL_MON_DATA_SPECIES) != 0U;
}

static bool qol_cross_store_fault_matrix(struct mCore *core,
                                         const struct QolSymbols *s,
                                         const struct Snapshot *base)
{
    for (uint8_t fault = 1U; fault <= 2U; ++fault) {
        if (!qol_fault_reward_single(core, s, base, fault)) {
            fprintf(stderr, "cross-store single failed mode=%u\n", fault);
            return false;
        }
        if (!qol_fault_reward_power(core, s, base, fault)) {
            fprintf(stderr, "cross-store power failed mode=%u\n", fault);
            return false;
        }
        if (!qol_fault_reward_daycare(core, s, base, fault)) {
            fprintf(stderr, "cross-store daycare failed mode=%u\n", fault);
            return false;
        }
        if (!qol_fault_queue_bulk(core, s, base, fault)) {
            fprintf(stderr, "cross-store bulk failed mode=%u\n", fault);
            return false;
        }
        if (!qol_fault_queue_receive(core, s, base, fault, false)) {
            fprintf(stderr, "cross-store party failed mode=%u\n", fault);
            return false;
        }
        if (!qol_fault_queue_receive(core, s, base, fault, true)) {
            fprintf(stderr, "cross-store pc failed mode=%u\n", fault);
            return false;
        }
    }
    return true;
}

static bool qol_egg_transfer_case(struct mCore *core,
                                  const struct QolSymbols *s,
                                  uint8_t count, bool full) {
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    qol_seed_egg_queue(core, count);
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EGG_QUEUE_CLAIM,
                        1U, 0, 0) != QOL_STATUS_CANCELLED
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != count)
        return false;
    if (full) {
        for (uint8_t box = 0U; box < QOL_BOX_COUNT; ++box) {
            for (uint8_t slot = 0U; slot < 30U; ++slot) {
                if (!qol_prepare_box_mon(core, box, slot, 16U))
                    return false;
            }
        }
        return call_preserving(core, s->dispatch,
                               QOL_SERVICE_EGG_QUEUE_CLAIM,
                               0U, 0, 0) == QOL_STATUS_CAPACITY
            && read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) == count;
    }
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EGG_QUEUE_CLAIM,
                        0U, 0, 0) != QOL_STATUS_OK
        || read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) != 0U)
        return false;
    for (uint8_t index = 0U; index < count; ++index) {
        if (call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                            0U, index, QOL_MON_DATA_SPECIES, 0) == 0U)
            return false;
    }
    return true;
}

static bool qol_quantity_item_case(struct mCore *core,
                                   const struct QolSymbols *s,
                                   uint16_t item, uint8_t choice,
                                   uint16_t available, uint16_t expected) {
    const uint32_t result = QOL_PARTY_SCRATCH + 0x180U;
    create_mon(core, QOL_PARTY_SCRATCH, 1U, 5U);
    for (unsigned index = 0U; index < 24U; ++index)
        write8(core, result + index, 0U);
    return qol_call5_preserving(core, s->apply_quantity,
                                QOL_PARTY_SCRATCH, item, choice,
                                available, result) == 1U
        && read16(core, result + 12U) == expected
        && read16(core, result + 14U) == expected
        && read32(core, result + 8U) != 0U;
}

static bool qol_pc_relearn_case(struct mCore *core,
                                const struct QolSymbols *s) {
    if (!qol_prepare_box_mon(core, 0U, 0U, 1U))
        return false;
    uint32_t before = call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                                      0U, 0U, 16U, 0);
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_RELEARN,
                        0U, (3U << 8) | (1U << 16), 33U)
            != QOL_STATUS_CANCELLED
        || call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                           0U, 0U, 16U, 0) != before)
        return false;
    for (uint16_t move = 1U; move <= BATTLE_CORE_CANONICAL_MOVE_MAX; ++move) {
        uint32_t status = call_preserving(core, s->dispatch,
                                          QOL_SERVICE_PC_RELEARN,
                                          0U, 3U << 8, move);
        if (status != QOL_STATUS_OK)
            continue;
        return call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                               0U, 0U, 16U, 0) == move;
    }
    return false;
}

static bool qol_enter_party_menu(struct mCore *core,
                                 const struct QolSymbols *s)
{
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != 0x08055E75U) {
        fprintf(stderr, "party initial cb=%08" PRIx32 " count=%u\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, QOL_PLAYER_PARTY_COUNT));
        return false;
    }
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_POKEMON_GET, 0, 0, 0);
    (void)call_preserving(core, s->probe, 8U, 0, 0, 0);
    qol_press(core, QOL_KEY_START, 90U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT) {
        fprintf(stderr, "party start cb=%08" PRIx32 " main=%08" PRIx32 "\n",
                read32(core, QOL_START_MENU_CALLBACK),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    uint8_t pokemon = 0xFFU;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == 1U) {
            pokemon = index;
            break;
        }
    }
    if (pokemon == 0xFFU || count == 0U) {
        fprintf(stderr, "party menu order pokemon=%u count=%u cursor=%u\n",
                pokemon, count, cursor);
        for (uint8_t index = 0U; index < count; ++index)
            fprintf(stderr, " order[%u]=%u", index,
                    read8(core, QOL_START_MENU_ORDER + index));
        fputc('\n', stderr);
        return false;
    }
    while (cursor != pokemon) {
        qol_press(core, QOL_KEY_DOWN, 4U);
        cursor = (uint8_t)((cursor + 1U) % count);
    }
    qol_press(core, QOL_KEY_A, 600U);
    bool entered = read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT) == 0U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) != 0x08055E75U;
    if (!entered)
        fprintf(stderr, "party enter cb=%08" PRIx32 " start=%08" PRIx32 "\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, QOL_START_MENU_CALLBACK));
    return entered;
}

static bool qol_summary_user_path(struct mCore *core,
                                  const struct QolSymbols *s)
{
    /* The deterministic warp fixture carries only a minimal level-0 party
     * placeholder.  Replace it with a valid mon before traversing the normal
     * party/Summary UI; CreateMon also initializes encrypted substructures. */
    create_mon(core, QOL_PLAYER_PARTY, 1U, 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    if (qol_get_party_data(core, QOL_PLAYER_PARTY,
                           QOL_MON_DATA_SPECIES) != 1U
        || qol_get_party_data(core, QOL_PLAYER_PARTY,
                              QOL_MON_DATA_LEVEL) != 50U)
        return false;
    if (!qol_enter_party_menu(core, s))
        return false;
    uint32_t summary = 0U;
    /* First A opens the visible mon action menu.  UP fixes the cursor at its
     * first row (Summary) even if another party-menu case left a remembered
     * cursor, then the second physical A selects it. */
    qol_press(core, QOL_KEY_A, 240U);
    qol_press(core, QOL_KEY_UP, 12U);
    qol_press(core, QOL_KEY_A, 30U);
    bool summary_seen = false;
    bool summary_ready = false;
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        core->runFrame(core);
        uint32_t live = read32(core, QOL_SUMMARY_DATA_SLOT);
        if (live >= 0x02000000U && live + 0x3240U < 0x02040000U) {
            summary_seen = true;
            summary = live;
            if (read8(core, live + QOL_SUMMARY_INPUT_STATE) == 2U) {
                summary_ready = true;
                break;
            }
        }
    }
    if (!summary_seen || summary < 0x02000000U
        || summary + 0x3240U >= 0x02040000U) {
        fprintf(stderr, "summary init pointer=%08" PRIx32 " cb=%08" PRIx32 "\n",
                summary, read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    if (!summary_ready) {
        fprintf(stderr, "summary did not reach input state page=%u state=%u "
                "cb=%08" PRIx32 " task=%08" PRIx32 " fade=%02x ptr=%08" PRIx32
                "\n",
                read8(core, summary + QOL_SUMMARY_PAGE),
                read8(core, summary + QOL_SUMMARY_INPUT_STATE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, QOL_TASKS), read8(core, 0x020379F3U),
                read32(core, QOL_SUMMARY_DATA_SLOT));
        return false;
    }
    qol_press(core, QOL_KEY_RIGHT, 120U);
    if (read8(core, summary + QOL_SUMMARY_PAGE) != 1U
        || read8(core, summary + QOL_SUMMARY_INPUT_STATE) != 2U) {
        fprintf(stderr, "summary page=%u state=%u cb=%08" PRIx32 "\n",
                read8(core, summary + QOL_SUMMARY_PAGE),
                read8(core, summary + QOL_SUMMARY_INPUT_STATE),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    qol_press(core, QOL_KEY_SELECT, 20U);
    if (((read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U) != 1U
        || read8(core, QOL_STATE + QOL_STATE_JUDGE_IV) == 0xFFU) {
        fprintf(stderr, "summary select mode=%u judge=%02x\n",
                (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U,
                read8(core, QOL_STATE + QOL_STATE_JUDGE_IV));
        return false;
    }
    qol_press(core, QOL_KEY_R, 20U);
    if (((read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U) != 2U) {
        fprintf(stderr, "summary R mode=%u page=%u state=%u\n",
                (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U,
                read8(core, summary + QOL_SUMMARY_PAGE),
                read8(core, summary + QOL_SUMMARY_INPUT_STATE));
        return false;
    }
    qol_press(core, QOL_KEY_L, 20U);
    if (((read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U) != 1U) {
        fprintf(stderr, "summary L mode=%u\n",
                (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U);
        return false;
    }
    qol_press(core, QOL_KEY_SELECT, 20U);
    bool toggled_off = ((read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2)
                        & 3U) == 0U;
    if (!toggled_off)
        fprintf(stderr, "summary final mode=%u\n",
                (read8(core, QOL_STATE + QOL_STATE_FILTER_MODE) >> 2) & 3U);
    qol_press(core, QOL_KEY_B, 240U);
    return toggled_off;
}

static bool qol_hyper_case(struct mCore *core, const struct QolSymbols *s,
                           uint16_t item, uint8_t stat, uint8_t expected_mask)
{
    create_mon(core, QOL_PLAYER_PARTY, 1U, 100U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    for (unsigned index = 0U; index < 6U; ++index)
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_IV + index, 0U, 1U);
    write8(core, QOL_PLAYER_PARTY + 0x10U,
           (uint8_t)(read8(core, QOL_PLAYER_PARTY + 0x10U) & ~0x3FU));
    uint32_t added = call_preserving(core, QOL_CHECK_BAG_ITEM,
                                     item, 1U, 0, 0);
    if (!added)
        added = call_preserving(core, QOL_ADD_BAG_ITEM, item, 1U, 0, 0);
    uint32_t cancelled = call_preserving(core, s->dispatch,
                                         QOL_SERVICE_HYPER_TRAIN,
                                         0U, stat, 1U);
    if (!added || cancelled != QOL_STATUS_CANCELLED
        || !call_preserving(core, QOL_CHECK_BAG_ITEM, item, 1U, 0, 0)
        || (read8(core, QOL_PLAYER_PARTY + 0x10U) & 0x3FU) != 0U) {
        fprintf(stderr, "hyper pre item=%u added=%" PRIu32
                " cancel=%" PRIu32 " mask=%02x\n", item, added, cancelled,
                read8(core, QOL_PLAYER_PARTY + 0x10U) & 0x3FU);
        return false;
    }
    uint32_t trained = call_preserving(core, s->dispatch,
                                       QOL_SERVICE_HYPER_TRAIN,
                                       0U, stat, 0U);
    if (trained != QOL_STATUS_OK
        || (read8(core, QOL_PLAYER_PARTY + 0x10U) & 0x3FU) != expected_mask
        || call_preserving(core, QOL_CHECK_BAG_ITEM, item, 1U, 0, 0)) {
        fprintf(stderr, "hyper apply item=%u stat=%u status=%" PRIu32
                " mask=%02x expected=%02x bag=%" PRIu32 "\n",
                item, stat, trained,
                read8(core, QOL_PLAYER_PARTY + 0x10U) & 0x3FU,
                expected_mask, call_preserving(core, QOL_CHECK_BAG_ITEM,
                                                item, 1U, 0, 0));
        return false;
    }
    for (unsigned index = 0U; index < 6U; ++index) {
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_IV + index) != 0U)
            return false;
    }
    return true;
}

static bool qol_ev_reset_all_case(struct mCore *core,
                                  const struct QolSymbols *s)
{
    create_mon(core, QOL_PLAYER_PARTY, 1U, 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    for (unsigned stat = 0U; stat < 6U; ++stat)
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_EV + stat, 40U, 1U);
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EV_RESET_ALL,
                        0U, 1U, 0U) != QOL_STATUS_CANCELLED)
        return false;
    for (unsigned stat = 0U; stat < 6U; ++stat) {
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat) != 40U)
            return false;
    }
    if (call_preserving(core, s->dispatch, QOL_SERVICE_EV_RESET_ALL,
                        0U, 0U, 0U) != QOL_STATUS_OK)
        return false;
    for (unsigned stat = 0U; stat < 6U; ++stat) {
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat) != 0U)
            return false;
    }
    return call_preserving(core, s->dispatch, QOL_SERVICE_EV_RESET_ALL,
                           0U, 0U, 0U) == QOL_STATUS_EFFECTLESS;
}

static bool qol_common_quantity_user_path(struct mCore *core,
                                          const struct QolSymbols *s,
                                          uint16_t item)
{
    create_mon(core, QOL_PLAYER_PARTY, 1U, 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    if (!qol_enter_party_menu(core, s))
        return false;
    for (unsigned stat = 0U; stat < 6U; ++stat)
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_EV + stat, 40U, 1U);
    uint32_t hp_before = qol_get_mon_data(core, QOL_PLAYER_PARTY,
                                          QOL_MON_DATA_HP_EV);
    uint32_t atk_before = qol_get_mon_data(core, QOL_PLAYER_PARTY,
                                           QOL_MON_DATA_HP_EV + 1U);
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, item, 5U, 0, 0)) {
        fprintf(stderr, "quantity add failed item=%u\n", item);
        return false;
    }
    write16(core, QOL_SPECIAL_VAR_ITEM, item);
    write8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT, 0U);
    uint32_t task_id = call_preserving(core, QOL_CREATE_TASK,
                                       QOL_TASK_DUMMY, 0x50U, 0, 0);
    if (task_id >= 16U) {
        fprintf(stderr, "quantity task id=%" PRIu32 "\n", task_id);
        return false;
    }
    /* Resolve and execute the callback installed in the real Item table. */
    uint32_t item_entry = 0x0904D120U + (uint32_t)item * 40U;
    uint32_t field_use = read32(core, item_entry);
    if (field_use != s->common_quantity) {
        fprintf(stderr, "quantity item entry=%08" PRIx32
                " callback=%08" PRIx32 " expected=%08" PRIx32 "\n",
                item_entry, field_use, s->common_quantity);
        return false;
    }
    call_preserving(core, field_use, task_id, 0, 0, 0);
    uint32_t callback = read32(core, QOL_ITEM_USE_CALLBACK);
    if ((callback & 1U) == 0U) {
        fprintf(stderr, "quantity callback=%08" PRIx32 "\n", callback);
        return false;
    }
    call_preserving(core, callback, task_id, QOL_TASK_DUMMY, 0, 0);
    uint32_t task = QOL_TASKS + task_id * QOL_TASK_SIZE;
    uint32_t handler = read32(core, task);
    if ((handler & 1U) == 0U) {
        fprintf(stderr, "quantity handler=%08" PRIx32 "\n", handler);
        return false;
    }
    /* x1 -> x5 is one visible DOWN action in the stock ListMenu, then A
     * applies the selection through the actual Item-table consumer task. */
    qol_press(core, QOL_KEY_DOWN, 8U);
    qol_press(core, QOL_KEY_A, 60U);
    bool result = qol_get_mon_data(core, QOL_PLAYER_PARTY,
                                   QOL_MON_DATA_HP_EV) == 0U
        && qol_get_mon_data(core, QOL_PLAYER_PARTY,
                            QOL_MON_DATA_HP_EV + 1U) == 40U
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           item, 4U, 0, 0) == 1U
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           item, 5U, 0, 0) == 0U;
    if (!result)
        fprintf(stderr, "quantity user item=%u callback=%08" PRIx32
                " handler=%08" PRIx32 " before=%" PRIu32 "/%" PRIu32
                " hp=%" PRIu32 " atk=%" PRIu32
                " bag4=%" PRIu32 " bag5=%" PRIu32 "\n", item, callback,
                handler, hp_before, atk_before,
                qol_get_mon_data(core, QOL_PLAYER_PARTY,
                                          QOL_MON_DATA_HP_EV),
                qol_get_mon_data(core, QOL_PLAYER_PARTY,
                                 QOL_MON_DATA_HP_EV + 1U),
                call_preserving(core, QOL_CHECK_BAG_ITEM, item, 4U, 0, 0),
                call_preserving(core, QOL_CHECK_BAG_ITEM, item, 5U, 0, 0));
    return result;
}

static bool qol_feature_case(struct mCore *core,
                             const struct QolSymbols *s,
                             const struct Snapshot *field_base,
                             unsigned feature, bool full,
                             unsigned *physical_paths) {
    restore_snapshot(core, field_base);
    if (!qol_enable_feature_boundary(core, s, feature)) {
        fprintf(stderr, "feature boundary failed index=%u unlocked=%" PRIu32 "\n",
                feature, call_preserving(core, s->feature_unlocked,
                                         feature, 0, 0, 0));
        return false;
    }
    switch (feature) {
    case 0U: {
        /* Boundary checks deliberately clear progression.  Return to the
         * captured playable field before exercising the normal Start-menu
         * path; the path itself applies only the fixture progression it owns. */
        restore_snapshot(core, field_base);
        bool path = qol_start_panel_user_path(core, s);
        if (path) ++*physical_paths;
        return path
            && call_preserving(core, s->dispatch, QOL_SERVICE_SET_TEXT_SPEED,
                               0U, 0, 0) == QOL_STATUS_OK
            && call_preserving(core, s->text_delay, 0, 0, 0, 0) == 0x7FU;
    }
    case 1U: {
        /* The boundary audit intentionally clears progression fields.  The
         * physical event cadence is measured from the same stable authored
         * field snapshot as the top-level movement route. */
        restore_snapshot(core, field_base);
        bool path = qol_movement_user_path(core);
        if (path) ++*physical_paths;
        return path;
    }
    case 2U: {
        restore_snapshot(core, field_base);
        bool path = qol_summary_user_path(core, s);
        bool symbols = s->summary_input != 0U && s->print_skills != 0U;
        if (!path || !symbols)
            fprintf(stderr, "feature2 summary path=%u input=%08" PRIx32
                    " print=%08" PRIx32 "\n", path, s->summary_input,
                    s->print_skills);
        return path && symbols;
    }
    case 3U: {
        restore_snapshot(core, field_base);
        bool path = qol_pss_user_path(core, s);
        if (path) ++*physical_paths;
        return path && qol_pc_atomic_matrix(core, s, full);
    }
    case 4U:
        return qol_exp_share_matrix(core, s);
    case 5U:
        return qol_reward_case(core, s, 0U, 195U)
            && qol_purchase_case(core, s, 0U, 195U, 4U, 2U);
    case 6U:
        return qol_egg_transfer_case(core, s, 1U, full);
    case 7U:
        return qol_egg_transfer_case(core, s, 5U, full);
    case 8U:
        return read32(core, QOL_ITEM_TABLE
                           + 347U * QOL_ITEM_ROW_SIZE
                           + QOL_ITEM_CALLBACK_OFFSET) != 0U;
    case 9U:
        return qol_pc_relearn_case(core, s);
    case 10U:
        return qol_quantity_item_case(core, s, 988U, 0U, 10U, 1U)
            && qol_quantity_item_case(core, s, 989U, 2U, 10U, 10U);
    case 11U:
        return qol_reward_case(core, s, 1U, 990U);
    case 12U:
        return qol_purchase_case(core, s, 13U, 985U, 8U, 1U)
            && qol_purchase_case(core, s, 14U, 942U, 16U, 1U);
    case 13U:
        return qol_ev_reset_all_case(core, s);
    case 14U: {
        restore_snapshot(core, field_base);
        bool path = qol_pss_user_path(core, s);
        if (path) ++*physical_paths;
        return path;
    }
    case 15U:
        return qol_pc_atomic_matrix(core, s, full);
    case 16U:
        return qol_auto_guard_matrix(core, s);
    case 17U:
        return call_preserving(core, QOL_CHECK_BAG_ITEM, 902U, 1U, 0, 0)
            && call_preserving(core, s->claim_reward, 4U, 0, 0, 0)
                   == QOL_STATUS_ALREADY_CLAIMED;
    case 18U:
        return qol_basket_boundary(core, s);
    case 19U:
        return call_preserving(core, QOL_CHECK_BAG_ITEM, 684U, 1U, 0, 0)
            && call_preserving(core, s->modify_breeding, 20U, 0, 0, 0) == 40U
            && call_preserving(core, s->modify_breeding, 70U, 0, 0, 0) == 100U;
    case 20U:
        return qol_reward_case(core, s, 2U, 861U)
            && qol_purchase_case(core, s, 7U, 861U, 8U, 1U)
            && qol_purchase_case(core, s, 12U, 860U, 8U, 1U);
    case 21U:
        return qol_purchase_case(core, s, 3U, 990U, 4U, 2U);
    case 22U:
        return qol_purchase_case(core, s, 4U, 991U, 8U, 1U)
            && qol_purchase_case(core, s, 42U, 853U, 32U, 1U)
            && qol_hyper_case(core, s, 853U, 0U, 1U);
    case 23U:
        return qol_purchase_case(core, s, 35U, 943U, 64U, 1U)
            && qol_purchase_case(core, s, 15U, 967U, 8U, 1U)
            && qol_purchase_case(core, s, 34U, 987U, 8U, 1U);
    case 24U:
        restore_snapshot(core, field_base);
        {
        bool consumer = qol_common_quantity_user_path(core, s, 993U);
        restore_snapshot(core, field_base);
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET,
                              QOL_FLAG_DH_CLEAR, 0, 0, 0);
        bool hp = qol_purchase_case(core, s, 36U, 993U, 8U, 1U);
        bool spe = qol_purchase_case(core, s, 41U, 998U, 8U, 1U);
        if (!consumer || !hp || !spe)
            fprintf(stderr, "feature24 consumer=%u hp=%u spe=%u\n",
                    consumer, hp, spe);
        return consumer && hp && spe;
        }
    case 25U:
        return qol_purchase_case(core, s, 14U, 942U, 16U, 1U)
            && qol_purchase_case(core, s, 42U, 853U, 32U, 1U)
            && qol_purchase_case(core, s, 36U, 993U, 8U, 1U);
    case 26U:
        return qol_reward_case(core, s, 3U, 992U)
            && qol_quantity_item_case(core, s, 992U, 0U, 1U, 1U);
    case 27U:
        return qol_profile_hatch_matrix(core, s);
    case 28U:
        return call_preserving(core, s->reusable_tm, 289U, 0, 0, 0) == 1U;
    case 29U:
        return s->hidden != 0U && call_preserving(core, s->feature_unlocked,
                                                  29U, 0, 0, 0) == 1U;
    case 30U:
        return qol_purchase_case(core, s, 44U, 186U, 24U, 1U)
            && qol_purchase_case(core, s, 47U, 925U, 24U, 1U);
    case 31U:
        return qol_auto_guard_matrix(core, s)
            && call_preserving(core, s->dispatch,
                               QOL_SERVICE_CONFIGURE_HIGH_RAID, 0U, 0, 0)
                   == QOL_STATUS_OK
            && call_preserving(core, s->probe, 10U, 0, 0, 0) == 1U
            && call_preserving(core, s->save_load, 0U, 0, 0, 0) == 1U
            && call_preserving(core, s->probe, 10U, 0, 0, 0) == 0U;
    case 32U:
        return call_preserving(core, s->configure_trainer,
                               QOL_DYNAMAX_COMMAND_DATA, 0, 0, 0)
                   != 0U
            && call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                               9U, 0, 0, 0) == 1U
            && call_preserving(core, s->probe, 11U, 0, 0, 0) == 1U
            && call_preserving(core, s->save_load, 0U, 0, 0, 0) == 1U
            && call_preserving(core, QOL_STAGE35_TRAINER_PROBE,
                               9U, 0, 0, 0) == 0U;
    case 33U:
        return qol_purchase_case(core, s, 48U, 957U, 64U, 1U);
    case 34U:
        return qol_purchase_case(core, s, 5U, 992U, 12U, 1U)
            && qol_purchase_case(core, s, 43U, 854U, 128U, 1U)
            && qol_hyper_case(core, s, 854U, 6U, 0x3FU);
    default:
        return false;
    }
}

static bool qol_write_persistent_state(struct mCore *core,
                                       const struct QolSymbols *s) {
    if (call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                        10U, 0U, QOL_MON_DATA_SPECIES, 0) == 0U
        && !qol_prepare_box_mon(core, 10U, 0U, 25U))
        return false;
    if (call_preserving(core, s->dispatch, QOL_SERVICE_PC_CLEAR,
                        0, 0, 0) != QOL_STATUS_OK)
        return false;
    if (call_preserving(core, QOL_GET_BOX_MON_DATA_AT,
                        10U, 0U, QOL_MON_DATA_SPECIES, 0) == 0U
        || call_preserving(core, s->dispatch, QOL_SERVICE_PC_TOGGLE,
                           10U, 0U, 0) != QOL_STATUS_OK)
        return false;
    write8(core, QOL_STATE + QOL_STATE_AUTO_ACTIVE, 1U);
    if (call_preserving(core, s->probe, 4U, 0, 0, 0) != 1U
        || call_preserving(core, s->probe, 6U, 0, 0, 0) != 1U)
        return false;
    return call_preserving(core, QOL_TRY_SAVING_DATA, 0, 0, 0, 0) == 1U;
}

static bool qol_verify_persistent_state(struct mCore *core,
                                        const struct QolSymbols *s) {
    run_key_frames(core, 0U, 180U);
    uint32_t load_result = call_preserving(
        core, QOL_LOAD_GAME_DATA, 0, 0, 0, 0);
    if (load_result != 1U) {
        fprintf(stderr, "save reload load_result=%" PRIu32 "\n", load_result);
        return false;
    }
    bool result = read8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED) == 0U
        && read8(core, QOL_LEDGER + QOL_LEDGER_HATCH_MODE) == 2U
        && read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE) == 1U
        && read8(core, QOL_LEDGER + QOL_LEDGER_ENCOUNTER_PROFILE) == 1U
        && read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT) == 5U
        && read8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS) == 0x0FU
        && read8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II) == 1U
        && call_preserving(core, s->probe, 4U, 0, 0, 0) == 0U
        && call_preserving(core, s->probe, 6U, 0, 0, 0) == 0U
        && call_preserving(core, QOL_FLAG_GET,
                           QOL_FLAG_EXP_SHARE, 0, 0, 0) == 1U;
    if (!result) {
        fprintf(stderr, "save reload text=%u hatch=%u exp=%u profile=%u "
                "eggs=%u cert=%u league=%u selection=%u auto=%u flag=%u\n",
                read8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED),
                read8(core, QOL_LEDGER + QOL_LEDGER_HATCH_MODE),
                read8(core, QOL_LEDGER + QOL_LEDGER_EXP_SHARE),
                read8(core, QOL_LEDGER + QOL_LEDGER_ENCOUNTER_PROFILE),
                read8(core, QOL_LEDGER + QOL_LEDGER_EGG_COUNT),
                read8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS),
                read8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II),
                (unsigned)call_preserving(core, s->probe, 4U, 0, 0, 0),
                (unsigned)call_preserving(core, s->probe, 6U, 0, 0, 0),
                (unsigned)call_preserving(core, QOL_FLAG_GET,
                                          QOL_FLAG_EXP_SHARE, 0, 0, 0));
    }
    return result;
}

#ifndef QOL_PRODUCTION_EMBEDDED
int main(int argc, char **argv) {
    if (argc != 36) {
        fprintf(stderr, "usage: %s ROM SAVE CASES quick|full 31_SYMBOLS\n", argv[0]);
        return 2;
    }
    bool full = strcmp(argv[4], "full") == 0;
    if (!full && strcmp(argv[4], "quick") != 0) return 2;
    struct QolSymbols s = {0};
    unsigned arg = 5U;
    s.probe = qol_number(argv[arg++], "probe");
    s.dispatch = qol_number(argv[arg++], "dispatch");
    s.read_keys = qol_number(argv[arg++], "read_keys");
    s.pss_input = qol_number(argv[arg++], "pss_input");
    s.text_delay = qol_number(argv[arg++], "text_delay");
    s.should_hatch = qol_number(argv[arg++], "should_hatch");
    s.action = qol_number(argv[arg++], "action");
    s.panel = qol_number(argv[arg++], "panel");
    s.save_load = qol_number(argv[arg++], "save_load");
    s.wild_land = qol_number(argv[arg++], "wild_land");
    s.wild_fishing = qol_number(argv[arg++], "wild_fishing");
    s.wild_begin = qol_number(argv[arg++], "wild_begin");
    s.move = qol_number(argv[arg++], "move");
    s.feature_unlocked = qol_number(argv[arg++], "feature_unlocked");
    s.claim_reward = qol_number(argv[arg++], "claim_reward");
    s.purchase_supply = qol_number(argv[arg++], "purchase_supply");
    s.reusable_tm = qol_number(argv[arg++], "reusable_tm");
    s.modify_breeding = qol_number(argv[arg++], "modify_breeding");
    s.hidden = qol_number(argv[arg++], "hidden");
    s.common_quantity = qol_number(argv[arg++], "common_quantity");
    s.summary_input = qol_number(argv[arg++], "summary_input");
    s.print_skills = qol_number(argv[arg++], "print_skills");
    s.hatch_presentation = qol_number(argv[arg++], "hatch_presentation");
    s.give_egg = qol_number(argv[arg++], "give_egg");
    s.give_egg_special = qol_number(argv[arg++], "give_egg_special");
    s.party_count = qol_number(argv[arg++], "party_count");
    s.run_text = qol_number(argv[arg++], "run_text");
    s.apply_quantity = qol_number(argv[arg++], "apply_quantity");
    s.inject_persist_fault = qol_number(argv[arg++], "inject_persist_fault");
    s.open_supply_shop = qol_number(argv[arg++], "open_supply_shop");
    s.configure_trainer = qol_number(argv[arg++], "configure_trainer");
    if (arg != (unsigned)argc) return 2;

    qol_initialize_save(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    bool boot = qol_run_field_trace(core);
    bool fixture = qol_case_fixture(argv[3], full);
    bool hooks = qol_hook_contract(core, &s);
    bool probe = qol_probe_contract(core, &s);

    /* Every scenario starts from the same stable overworld state.  A QOL case
     * is allowed to change callbacks, tasks, menus, party/box data and the
     * production ledger; none of that volatile state may leak into the next
     * case and turn a later result into an order-dependent false failure. */
    struct Snapshot field_base = take_snapshot(core);

    restore_snapshot(core, &field_base);
    bool movement = qol_movement_user_path(core);

    restore_snapshot(core, &field_base);
    bool panel = qol_start_panel_user_path(core, &s);

    restore_snapshot(core, &field_base);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t instant_delay = call_preserving(core, s.text_delay, 0, 0, 0, 0);
    unsigned text_logs_before = log_problem_count;
    run_key_frames(core, 0U, 2U);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t fast_delay = call_preserving(core, s.text_delay, 0, 0, 0, 0);
    run_key_frames(core, 0U, 2U);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 2U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    uint32_t normal_delay = call_preserving(core, s.text_delay, 0, 0, 0, 0);
    run_key_frames(core, 0U, 2U);
    write8(core, QOL_LEDGER + QOL_LEDGER_TEXT_SPEED, 0U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    bool text = instant_delay == 0x7FU && fast_delay == 1U
        && normal_delay == 2U && log_problem_count == text_logs_before;

    restore_snapshot(core, &field_base);
    bool unlock = qol_unlock_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool exp_share = qol_unlock_matrix(core, &s)
        && qol_exp_share_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool profile_hatch = qol_unlock_matrix(core, &s)
        && qol_profile_hatch_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool supply = qol_unlock_matrix(core, &s)
        && qol_supply_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool quantity = qol_quantity_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool training = qol_unlock_matrix(core, &s)
        && qol_training_matrix(core, &s);

    restore_snapshot(core, &field_base);
    bool pss = qol_pss_user_path(core, &s);

    restore_snapshot(core, &field_base);
    bool boxes = qol_real_box_matrix(core, &s);

    restore_snapshot(core, &field_base);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR, 0, 0, 0);
    bool pc_atomic = qol_pc_atomic_matrix(core, &s, full);

    restore_snapshot(core, &field_base);
    bool auto_guard = qol_auto_guard_matrix(core, &s);

    bool auto_forbidden_live = false;
    bool auto_live = qol_auto_live_battle_matrix(
        core, &s, &field_base, &auto_forbidden_live);

    bool raid_story = qol_raid_story_consumers(core, &s, &field_base);

    restore_snapshot(core, &field_base);
    bool basket = qol_basket_boundary(core, &s);

    bool cross_store_faults = qol_cross_store_fault_matrix(
        core, &s, &field_base);

    bool feature_checks[QOL_FEATURE_COUNT] = {false};
    unsigned physical_input_paths = 0U;
    for (unsigned index = 0U; index < QOL_FEATURE_COUNT; ++index) {
        feature_checks[index] = qol_feature_case(
            core, &s, &field_base, index, full, &physical_input_paths);
    }

    restore_snapshot(core, &field_base);
    bool save_basket = qol_basket_boundary(core, &s);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_BADGE_1, 0, 0, 0);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME, 0, 0, 0);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
    bool save_exp = save_basket && qol_exp_share_matrix(core, &s);
    bool save_profile = save_exp && qol_profile_hatch_matrix(core, &s);
    bool save_setup = save_profile;
    bool save_write = save_setup && qol_write_persistent_state(core, &s);
    free(field_base.bytes);
    qol_close(core);

    core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    bool save_reload = save_write && qol_verify_persistent_state(core, &s);
    if (!save_write)
        fprintf(stderr, "save write/setup failed exp=%u profile=%u basket=%u\n",
                save_exp, save_profile, save_basket);
    bool warnings = log_problem_count == 0U;
    qol_close(core);

    bool all_features = true;
    for (unsigned index = 0; index < QOL_FEATURE_COUNT; ++index)
        all_features = all_features && feature_checks[index];

    bool acceptance[10] = {
        pss && boxes && pc_atomic && save_reload,
        panel && pss && movement && text && hooks,
        unlock && exp_share && profile_hatch && save_reload,
        pc_atomic && training && supply && cross_store_faults,
        pc_atomic && boxes,
        basket && save_reload,
        auto_guard && auto_live && raid_story && hooks,
        text && movement && boot && hooks,
        quantity && exp_share && training && profile_hatch && save_reload,
        supply && unlock && save_reload,
    };
    static const char *const acceptance_keys[10] = {
        "REAL_BOX_PSS_SAVE",
        "NORMAL_USER_ENTRY",
        "UNLOCK_SAVE_RELOAD",
        "ATOMIC_CANCEL_CAPACITY_FORBIDDEN",
        "PC_MULTI_BOX_EGG_SPECIAL_ADDED_SPECIES",
        "BASKET_255_256_QUEUE_SAVE",
        "AUTO_RANDOM_ONLY",
        "TEXT_CONTROL_AND_MOVEMENT_EVENTS",
        "TRAINING_STATS_DISPLAY_SAVE",
        "SUPPLY_UNLOCK_ONCE_REPEAT",
    };
    bool all_acceptance = true;
    for (unsigned index = 0; index < ARRAY_LEN(acceptance); ++index)
        all_acceptance = all_acceptance && acceptance[index];

    bool passed = boot && fixture && hooks && probe && movement && panel
        && text && unlock && exp_share && profile_hatch && supply && quantity
        && training && pss && boxes && pc_atomic && auto_guard && auto_live
        && raid_story
        && basket
        && cross_store_faults && save_reload && all_features
        && all_acceptance && warnings;
    fprintf(stderr,
        "mgba-qol-production %s: boot=%u fixture=%u hooks=%u probe=%u "
        "movement=%u panel=%u text=%u unlock=%u exp=%u profile=%u "
        "supply=%u quantity=%u training=%u pss=%u boxes=%u pc_atomic=%u "
        "auto=%u auto_live=%u raid_story=%u basket=%u faults=%u "
        "save_reload=%u logs=%u\n",
        full ? "full" : "quick", boot, fixture, hooks, probe, movement,
        panel, text, unlock, exp_share, profile_hatch, supply, quantity,
        training, pss, boxes, pc_atomic, auto_guard, auto_live, raid_story, basket,
        cross_store_faults, save_reload, log_problem_count);
    printf("{\"schema_version\":1,\"status\":\"%s\",\"mode\":\"%s\","
           "\"checks\":{\"field_boot\":%s,\"case_fixture\":%s,"
           "\"physical_hooks\":%s,\"probe\":%s,"
           "\"physical_movement\":%s,\"movement_step_hatch_exact\":%s,"
           "\"start_select_a_user_path\":%s,"
           "\"text_control\":%s,\"instant_text_battle_prompt\":%s,"
           "\"unlock_matrix\":%s,"
           "\"exp_share_single_owner\":%s,\"research_hatch_settings\":%s,"
           "\"supply_once_repeat\":%s,\"quantity_consumers\":%s,"
           "\"training_atomic\":%s,\"physical_pss_select_path\":%s,"
           "\"real_box_cross_move\":%s,\"pc_atomic_matrix\":%s,"
           "\"auto_forbidden_matrix\":%s,"
           "\"auto_physical_forbidden_contexts\":%s,"
           "\"auto_live_battle\":%s,"
           "\"basket_255_256\":%s,"
           "\"raid_story_consumers\":%s,"
           "\"cross_store_fault_injection\":%s,"
           "\"fresh_core_save_reload\":%s},",
           passed ? "PASS" : "FAIL", full ? "full" : "quick",
           boot ? "true" : "false", fixture ? "true" : "false",
           hooks ? "true" : "false", probe ? "true" : "false",
           movement ? "true" : "false", movement ? "true" : "false",
           panel ? "true" : "false",
           text ? "true" : "false", (text && auto_live) ? "true" : "false",
           unlock ? "true" : "false",
           exp_share ? "true" : "false", profile_hatch ? "true" : "false",
           supply ? "true" : "false", quantity ? "true" : "false",
           training ? "true" : "false", pss ? "true" : "false",
           boxes ? "true" : "false", pc_atomic ? "true" : "false",
           auto_guard ? "true" : "false",
           auto_forbidden_live ? "true" : "false",
           auto_live ? "true" : "false",
           basket ? "true" : "false",
           raid_story ? "true" : "false",
           cross_store_faults ? "true" : "false",
           save_reload ? "true" : "false");
    printf("\"feature_checks\":{");
    for (unsigned index = 0; index < QOL_FEATURE_COUNT; ++index) {
        printf("%s\"%s\":%s", index ? "," : "", QOL_FEATURE_KEYS[index],
               feature_checks[index] ? "true" : "false");
    }
    printf("},\"acceptance_checks\":{");
    for (unsigned index = 0; index < ARRAY_LEN(acceptance); ++index) {
        printf("%s\"%s\":%s", index ? "," : "", acceptance_keys[index],
               acceptance[index] ? "true" : "false");
    }
    printf("},\"coverage\":{\"features\":35,\"boxes\":14,"
           "\"case_rows\":35,\"physical_input_paths\":%u},"
           "\"warnings_errors\":%u}\n", physical_input_paths,
           log_problem_count);
    return passed ? 0 : 1;
}
#endif
