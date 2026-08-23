/* Focused exact-ROM smoke for USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define FIRST_BATTLE_EMBEDDED
#include "mgba_first_battle_loop_smoke.c"

#include <errno.h>

#define TV32_TRY_SAVING_DATA UINT32_C(0x080DB34D)
#define TV32_LOAD_GAME_DATA UINT32_C(0x080DB4E5)
#define TV32_SAVE_SIZE (128U * 1024U)
#define TV32_LOSS_OUTCOME 2U
#define TV32_TABLE_RECORD_SIZE 32U
#define TV32_MON_NATURE_MINT 0x0FU
#define TV32_MON_SPECIES 0x20U
#define TV32_MON_EV_HP 0x38U
#define TV32_MON_MET_BITS 0x46U
#define TV32_MON_IV_BITS 0x48U
#define TV32_HIDDEN_ABILITY_MASK 0x1000U
#define TV32_ABILITY_NUM_MASK UINT32_C(0x80000000)
#define TV32_DOUBLE_SCRIPT UINT32_C(0x08E032C0)
#define TV32_CONFIGURE_TRAINER_BATTLE UINT32_C(0x0807F949)
#define TV32_EXPECTED_DOUBLE_BATTLE_SCRIPT UINT32_C(0x08192E2B)
#define TV32_SCRIPT_CONTEXT1_SETUP UINT32_C(0x080693A5)
#define TV32_SCRIPT_CONTEXT2_ENABLE UINT32_C(0x08069201)
#define TV32_TRAINER_MESSAGE_CONTINUATION UINT32_C(0x08192F09)

static const uint32_t TV32_HOOK_SITES[] = {
    UINT32_C(0x0807FB04), UINT32_C(0x0807FB1C),
    UINT32_C(0x0807FB30), UINT32_C(0x0807FB44),
    UINT32_C(0x0807FB5C), UINT32_C(0x0807FB70),
    UINT32_C(0x0810D93C), UINT32_C(0x090DD2A4),
    UINT32_C(0x0807F948),
};
static const uint32_t TV32_GLOBAL_FLAG_SITES[] = {
    UINT32_C(0x0806DE74), UINT32_C(0x0806DE9C), UINT32_C(0x0806DEC4),
};
static const uint8_t TV32_GLOBAL_FLAG_PROLOGUES[][8] = {
    {0x10, 0xB5, 0x00, 0x04, 0x04, 0x0C, 0x20, 0x1C},
    {0x10, 0xB5, 0x00, 0x04, 0x04, 0x0C, 0x20, 0x1C},
    {0x10, 0xB5, 0x00, 0x04, 0x04, 0x0C, 0x20, 0x1C},
};

static void tv32_die(const char *message) {
    fprintf(stderr, "mgba-trainer-v5-stage31: %s\n", message);
    exit(1);
}

static struct mCore *tv32_log_core;

static void tv32_bounded_log(struct mLogger *logger, int category,
                             enum mLogLevel level, const char *format,
                             va_list args) {
    (void)logger;
    if (!(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN))) return;
    ++log_problem_count;
    if (log_problem_count > 8U) return;
    fprintf(stderr, "mGBA[%s][0x%02x] pc=%08" PRIx32 " cpsr=%08" PRIx32 ": ",
            mLogCategoryName(category), (unsigned)level,
            tv32_log_core ? (uint32_t)read_register(tv32_log_core, "pc") : 0U,
            tv32_log_core ? (uint32_t)read_register(tv32_log_core, "cpsr") : 0U);
    vfprintf(stderr, format, args);
    fputc('\n', stderr);
    if (log_problem_count == 8U)
        fputs("mGBA: further warnings/errors suppressed\n", stderr);
}

static void tv32_trace(const char *phase) {
    if (!getenv("TV32_TRACE")) return;
    fprintf(stderr, "mgba-trainer-v5-stage31 phase: %s\n", phase);
    fflush(stderr);
}

static void tv32_initialize_save(const char *path) {
    FILE *stream = fopen(path, "wb");
    if (!stream) tv32_die("save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    for (size_t written = 0; written < TV32_SAVE_SIZE; written += sizeof(block)) {
        if (fwrite(block, 1, sizeof(block), stream) != sizeof(block)) {
            fclose(stream);
            tv32_die("save initialization failed");
        }
    }
    if (fclose(stream) != 0) tv32_die("save close failed");
}

static uint32_t tv32_parse(const char *text, const char *label) {
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 0);
    if (errno || !end || *end || value > UINT32_MAX) {
        fprintf(stderr, "mgba-trainer-v5-stage31: invalid %s\n", label);
        exit(2);
    }
    return (uint32_t)value;
}

static struct mCore *tv32_open_core(const char *rom, const char *save) {
    static struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(rom);
    if (!core || !core->init(core)) tv32_die("core initialization failed");
    if (!mCoreLoadFile(core, rom)) tv32_die("ROM load failed");
    if (!mCoreLoadSaveFile(core, save, false)) tv32_die("save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    return core;
}

static void tv32_close_core(struct mCore *core) {
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
}

static bool tv32_repeated_iv(uint32_t bits, uint8_t expected) {
    for (unsigned index = 0; index < 6; ++index) {
        if (((bits >> (index * 5U)) & 31U) != expected) return false;
    }
    return true;
}

static struct CallObservation tv32_setup_trainer(
    struct mCore *core, const struct Snapshot *field, uint16_t trainer_id,
    unsigned player_count, uint16_t trainer_mode
) {
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    create_mon(core, ADDR_PLAYER_PARTY, 7, 12);
    if (player_count > 1U)
        create_mon(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, 4, 12);
    write8(core, ADDR_PLAYER_PARTY_COUNT, (uint8_t)player_count);
    write16(core, BATTLE_CORE_TRAINER_MODE, trainer_mode);
    write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, trainer_id);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0);
    if (!setup.payload_pc_seen) tv32_die("normal trainer setup missed CFRU payload");
    run_fixed_frames(core);
    return setup;
}

static bool tv32_single_sidecar(struct mCore *core, const struct Snapshot *field) {
    (void)tv32_setup_trainer(core, field, 93, 1, 0);
    uint8_t party_count = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT);
    uint8_t battlers_count = read8(core, ADDR_BATTLERS_COUNT);
    uint32_t first = ADDR_ENEMY_PARTY;
    uint32_t third = ADDR_ENEMY_PARTY + 2U * POKEMON_SIZE;
    uint32_t first_species =
        call_preserving(core, BATTLE_CORE_GET_MON_DATA, first, 11, 0, 0);
    uint32_t third_species =
        call_preserving(core, BATTLE_CORE_GET_MON_DATA, third, 11, 0, 0);
    uint32_t first_iv = read32(core, first + TV32_MON_IV_BITS);
    uint32_t third_iv = read32(core, third + TV32_MON_IV_BITS);
    uint8_t first_nature = read8(core, first + TV32_MON_NATURE_MINT);
    uint8_t third_nature = read8(core, third + TV32_MON_NATURE_MINT);
    uint16_t first_met = read16(core, first + TV32_MON_MET_BITS);
    uint16_t third_met = read16(core, third + TV32_MON_MET_BITS);
    bool ev_ok = true;
    for (unsigned ev = 0; ev < 6; ++ev) {
        if (read8(core, first + TV32_MON_EV_HP + ev) != 0U
            || read8(core, third + TV32_MON_EV_HP + ev) != 0U)
            ev_ok = false;
    }
    /* Active Pawmi's resolved battle ability proves the primary-slot path. */
    uint16_t battle_ability =
        read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x38U);
    bool passed = battlers_count == 2U
        && first_species == 1491U && third_species == 953U
        && first_nature == 14U && third_nature == 6U
        && tv32_repeated_iv(first_iv, 9U)
        && tv32_repeated_iv(third_iv, 10U)
        && (first_iv & TV32_ABILITY_NUM_MASK) == 0U
        && (third_iv & TV32_ABILITY_NUM_MASK) != 0U
        && (first_met & TV32_HIDDEN_ABILITY_MASK) == 0U
        && (third_met & TV32_HIDDEN_ABILITY_MASK) == 0U
        && ev_ok && battle_ability == 9U;
    if (!passed) {
        fprintf(stderr,
                "single-sidecar actual: party=%u battlers=%u species=%" PRIu32
                "/%" PRIu32 " nature=%u/%u iv=0x%08" PRIx32
                "/0x%08" PRIx32 " met=0x%04x/0x%04x ev=%s ability=%u\n",
                party_count, battlers_count, first_species, third_species,
                first_nature, third_nature, first_iv, third_iv,
                first_met, third_met, ev_ok ? "PASS" : "FAIL",
                battle_ability);
    }
    return passed;
}

static bool tv32_ai_records(struct mCore *core, uint32_t table) {
    uint32_t r327 = table + 327U * TV32_TABLE_RECORD_SIZE;
    uint32_t r116 = table + 116U * TV32_TABLE_RECORD_SIZE;
    uint32_t r1342 = table + 1342U * TV32_TABLE_RECORD_SIZE;
    return read32(core, r327 + 0x14U) == 1U
        && read32(core, r116 + 0x14U) == 3U
        && read32(core, r1342 + 0x14U) == 3U
        && read8(core, r327 + 0x12U) == 0U
        && read8(core, r116 + 0x12U) == 0U
        && read8(core, r1342 + 0x12U) == 1U
        && read8(core, r1342 + 0x18U) == 4U
        && read32(core, r327 + 0x1CU) >= UINT32_C(0x09200000)
        && read32(core, r1342 + 0x1CU) >= UINT32_C(0x09200000);
}

static bool tv32_double_entry(
    struct mCore *core, const struct Snapshot *field, uint32_t trainer_clear
) {
    restore_snapshot(core, field);
    clear_parties(core);
    seed_fixture(core);
    create_mon(core, ADDR_PLAYER_PARTY, 7, 12);
    create_mon(core, ADDR_PLAYER_PARTY + POKEMON_SIZE, 4, 12);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 2U);
    (void)call_preserving(core, trainer_clear, 1342U, 0, 0, 0);
    uint16_t rooted_source_id = read16(core, TV32_DOUBLE_SCRIPT + 2U);

    /* Exercise the rooted kind-4 trainerbattle arguments through CFRU's
     * public configuration entry.  Calling StartTrainerBattle directly cannot
     * model a double encounter because mode and speech fields are owned here. */
    uint32_t battle_script = call_preserving(
        core, TV32_CONFIGURE_TRAINER_BATTLE, TV32_DOUBLE_SCRIPT + 1U, 0, 0, 0);
    uint16_t configured_mode = read16(core, BATTLE_CORE_TRAINER_MODE);
    uint16_t configured_opponent = read16(core, BATTLE_CORE_TRAINER_OPPONENT_A);
    uint16_t player_one_hp = read16(
        core, ADDR_PLAYER_PARTY + POKEMON_CURRENT_HP_OFFSET);
    uint16_t player_two_hp = read16(
        core, ADDR_PLAYER_PARTY + POKEMON_SIZE + POKEMON_CURRENT_HP_OFFSET);
    (void)call_preserving(core, TV32_SCRIPT_CONTEXT2_ENABLE, 0, 0, 0, 0);
    (void)call_preserving(
        core, TV32_SCRIPT_CONTEXT1_SETUP,
        TV32_TRAINER_MESSAGE_CONTINUATION, 0, 0, 0);
    uint32_t observed_flags = 0U;
    uint8_t observed_battlers = 0U;
    uint8_t observed_party_count = 0U;
    uint32_t observed_first = 0U;
    uint32_t observed_fourth = 0U;
    for (unsigned press = 0; press < 160U; ++press) {
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 30U);
        observed_flags |= read32(core, ADDR_BATTLE_TYPE_FLAGS);
        uint8_t count = read8(core, ADDR_BATTLERS_COUNT);
        if (count > observed_battlers) observed_battlers = count;
        count = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT);
        if (count > observed_party_count) {
            observed_party_count = count;
            observed_first = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY, 11, 0, 0);
            observed_fourth = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA,
                ADDR_ENEMY_PARTY + 3U * POKEMON_SIZE, 11, 0, 0);
        }
        if ((read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_DOUBLE) != 0U
            && read8(core, ADDR_BATTLERS_COUNT) == 4U
            && read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE) == 1487U
            && read16(core, ADDR_BATTLE_MONS + 3U * BATTLE_MON_SIZE) == 4U)
            break;
    }
    uint8_t party_count = read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT);
    uint32_t battle_flags = read32(core, ADDR_BATTLE_TYPE_FLAGS);
    uint8_t battlers_count = read8(core, ADDR_BATTLERS_COUNT);
    uint8_t absent_flags = read8(core, ADDR_ABSENT_BATTLER_FLAGS);
    const uint16_t expected_party[] = {1487, 4, 7, 649};
    uint32_t actual_party[4] = {0};
    bool party_ok = true;
    for (unsigned index = 0; index < 4; ++index) {
        uint32_t mon = ADDR_ENEMY_PARTY + index * POKEMON_SIZE;
        actual_party[index] =
            call_preserving(core, BATTLE_CORE_GET_MON_DATA, mon, 11, 0, 0);
        if (actual_party[index] != expected_party[index]) party_ok = false;
    }
    uint16_t battler_one =
        read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE);
    uint16_t battler_three =
        read16(core, ADDR_BATTLE_MONS + 3U * BATTLE_MON_SIZE);
    uint32_t first_iv = read32(core, ADDR_ENEMY_PARTY + TV32_MON_IV_BITS);
    uint32_t fourth_iv = read32(
        core, ADDR_ENEMY_PARTY + 3U * POKEMON_SIZE + TV32_MON_IV_BITS);
    uint8_t first_nature = read8(
        core, ADDR_ENEMY_PARTY + TV32_MON_NATURE_MINT);
    uint8_t fourth_nature = read8(
        core, ADDR_ENEMY_PARTY + 3U * POKEMON_SIZE + TV32_MON_NATURE_MINT);
    uint16_t battler_one_ability =
        read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + 0x38U);
    uint16_t battler_three_ability =
        read16(core, ADDR_BATTLE_MONS + 3U * BATTLE_MON_SIZE + 0x38U);
    bool passed = rooted_source_id == 702U
        && battle_script == TV32_EXPECTED_DOUBLE_BATTLE_SCRIPT
        && configured_mode == 4U && configured_opponent == 1342U
        && (battle_flags & BATTLE_TYPE_DOUBLE) != 0U
        && battlers_count == 4U
        && (absent_flags & 0x0FU) == 0U
        && party_ok && battler_one == 1487U && battler_three == 4U
        && first_nature == 9U && fourth_nature == 1U
        && tv32_repeated_iv(first_iv, 8U)
        && tv32_repeated_iv(fourth_iv, 8U)
        && battler_one_ability == 15U && battler_three_ability == 66U;
    if (!passed) {
        fprintf(stderr,
                "double-entry actual: party=%u flags=0x%08" PRIx32
                " battlers=%u absent=0x%02x species=%" PRIu32 "/%" PRIu32
                "/%" PRIu32 "/%" PRIu32 " active=%u/%u"
                " nature=%u/%u iv=0x%08" PRIx32 "/0x%08" PRIx32
                " ability=%u/%u\n",
                party_count, battle_flags, battlers_count, absent_flags,
                actual_party[0], actual_party[1], actual_party[2],
                actual_party[3], battler_one, battler_three,
                first_nature, fourth_nature, first_iv, fourth_iv,
                battler_one_ability, battler_three_ability);
        fprintf(stderr,
                "double-entry setup: script=0x%08" PRIx32
                " configured_mode=%u configured_opponent=%u rooted_source=%u"
                " observed_flags=0x%08" PRIx32
                " observed_battlers=%u final_mode=%u final_opponent=%u"
                " player_hp=%u/%u observed_party=%u observed_species=%"
                PRIu32 "/%" PRIu32 "\n",
                battle_script, configured_mode, configured_opponent,
                rooted_source_id,
                observed_flags, observed_battlers,
                read16(core, BATTLE_CORE_TRAINER_MODE),
                read16(core, BATTLE_CORE_TRAINER_OPPONENT_A),
                player_one_hp, player_two_hp, observed_party_count,
                observed_first, observed_fourth);
    }
    return passed;
}

static bool tv32_loss_path(struct mCore *core, const struct Snapshot *field) {
    (void)tv32_setup_trainer(core, field, 328, 1, 0);
    write16(core, ADDR_PLAYER_PARTY + POKEMON_CURRENT_HP_OFFSET, 1U);
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP, 1U);
    uint32_t enemy = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    write16(core, enemy + BATTLE_MON_MOVES_OFFSET, BATTLE_CORE_MOVE_TACKLE);
    for (unsigned slot = 1; slot < 4; ++slot)
        write16(core, enemy + BATTLE_MON_MOVES_OFFSET + slot * 2U, 0U);
    write8(core, enemy + BATTLE_MON_PP_OFFSET, 35U);
    for (unsigned slot = 1; slot < 4; ++slot)
        write8(core, enemy + BATTLE_MON_PP_OFFSET + slot, 0U);

    uint8_t outcome_seen = 0;
    bool cleaned = false;
    for (unsigned pulse = 0; pulse < 96U && !cleaned; ++pulse) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0U);
        run_key_frames(core, 1U, 2U);
        run_key_frames(core, 0U, 120U);
        uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
        if (outcome != 0U && outcome_seen == 0U) outcome_seen = outcome;
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U) cleaned = true;
    }
    return outcome_seen == TV32_LOSS_OUTCOME && cleaned;
}

static bool tv32_probe_and_hooks(
    struct mCore *core, uint32_t probe, uint32_t trainer_set,
    uint32_t trainer_clear, uint32_t trainer_has, uint32_t rematch
) {
    const uint32_t expected[] = {UINT32_C(0x56353231), 25U, 71U, 11U, 11U, 1367U};
    for (unsigned selector = 0; selector < 6; ++selector) {
        if (call_preserving(core, probe, selector, 0, 0, 0) != expected[selector])
            return false;
    }
    uint32_t targets[ARRAY_LEN(TV32_HOOK_SITES)] = {0};
    for (unsigned index = 0; index < ARRAY_LEN(TV32_HOOK_SITES); ++index) {
        uint32_t site = TV32_HOOK_SITES[index];
        if (read16(core, site) != 0x4B00U || read16(core, site + 2U) != 0x4718U)
            return false;
        targets[index] = read32(core, site + 4U);
        if ((targets[index] & 1U) == 0U
            || targets[index] < UINT32_C(0x09200000)
            || targets[index] >= UINT32_C(0x09600000)) return false;
    }
    if (targets[1] != targets[2]
        || targets[3] != trainer_has
        || targets[4] != trainer_set
        || targets[5] != trainer_clear
        || targets[6] != rematch)
        return false;
    for (unsigned index = 0; index < ARRAY_LEN(TV32_GLOBAL_FLAG_SITES); ++index) {
        for (unsigned byte = 0; byte < 8U; ++byte) {
            if (read8(core, TV32_GLOBAL_FLAG_SITES[index] + byte)
                != TV32_GLOBAL_FLAG_PROLOGUES[index][byte])
                return false;
        }
    }
    return true;
}

static bool tv32_flag_mapping(
    struct mCore *core, uint32_t trainer_set, uint32_t trainer_clear,
    uint32_t trainer_has
) {
    const uint16_t high = 1354U;
    const uint16_t physical = 89U;
    (void)call_preserving(core, trainer_clear, high, 0, 0, 0);
    (void)call_preserving(core, trainer_clear, physical, 0, 0, 0);
    (void)call_preserving(core, trainer_set, high, 0, 0, 0);
    bool set = call_preserving(core, trainer_has, high, 0, 0, 0) == 1U
        && call_preserving(core, trainer_has, physical, 0, 0, 0) == 1U;
    (void)call_preserving(core, trainer_clear, high, 0, 0, 0);
    bool clear = call_preserving(core, trainer_has, high, 0, 0, 0) == 0U
        && call_preserving(core, trainer_has, physical, 0, 0, 0) == 0U;
    return set && clear;
}

int main(int argc, char **argv) {
    if (argc != 9) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE TRAINER_SET TRAINER_CLEAR "
                "TRAINER_HAS REMATCH TABLE\n", argv[0]);
        return 2;
    }
    uint32_t probe = tv32_parse(argv[3], "probe");
    uint32_t trainer_set = tv32_parse(argv[4], "trainer set");
    uint32_t trainer_clear = tv32_parse(argv[5], "trainer clear");
    uint32_t trainer_has = tv32_parse(argv[6], "trainer has");
    uint32_t rematch = tv32_parse(argv[7], "rematch");
    uint32_t table = tv32_parse(argv[8], "trainer table");

    tv32_initialize_save(argv[2]);
    struct mLogger logger = {.log = tv32_bounded_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = tv32_open_core(argv[1], argv[2]);
    tv32_log_core = core;
    tv32_trace("field_boot");
    run_trace_prefix(core);
    if (log_problem_count) tv32_die("mGBA warned/errored during field boot");
    struct Snapshot field = take_snapshot(core);

    tv32_trace("probe_and_hooks");
    bool probe_and_hook_binding = tv32_probe_and_hooks(
        core, probe, trainer_set, trainer_clear, trainer_has, rematch);
    tv32_trace("rematch_mapping");
    bool rematch_mapping = call_preserving(core, rematch, 89U, 0, 0, 0) == 1354U
        && call_preserving(core, rematch, 702U, 0, 0, 0) == 702U;
    tv32_trace("flag_mapping");
    bool flag_mapping =
        tv32_flag_mapping(core, trainer_set, trainer_clear, trainer_has);
    tv32_trace("ai_records");
    bool ai_records = tv32_ai_records(core, table);

    tv32_trace("normal_entry");
    struct NaturalFirstBattleObservation natural =
        run_natural_actashi_first_battle(core, &field);
    bool normal_entry = natural.selected_actashi && natural.trainer_327_started
        && natural.battle.opponent_species == 1U
        && natural.battle.pp_spent_once && natural.battle.hp_changed;
    tv32_trace("single_party_sidecar");
    bool single_party_sidecar = tv32_single_sidecar(core, &field);
    tv32_trace("double_entry");
    bool double_entry = tv32_double_entry(core, &field, trainer_clear);
    tv32_trace("win_path");
    struct EndObservation win = run_trainer_battle_end(core, &field);
    bool win_path = win.outcome_seen == BATTLE_CORE_OUTCOME_WON
        && win.enemy_fainted_seen && win.battle_runtime_cleaned;
    tv32_trace("loss_path");
    bool loss_path = tv32_loss_path(core, &field);

    tv32_trace("save_write");
    restore_snapshot(core, &field);
    const uint16_t saved_high = 1354U;
    (void)call_preserving(core, trainer_clear, saved_high, 0, 0, 0);
    (void)call_preserving(core, trainer_set, saved_high, 0, 0, 0);
    bool save_ok = call_preserving(core, TV32_TRY_SAVING_DATA, 0, 0, 0, 0) == 1U;
    free(field.bytes);
    tv32_close_core(core);

    tv32_trace("save_reload");
    core = tv32_open_core(argv[1], argv[2]);
    tv32_log_core = core;
    run_key_frames(core, 0, 180U);
    bool load_ok = call_preserving(core, TV32_LOAD_GAME_DATA, 0, 0, 0, 0) == 1U;
    bool save_reload = save_ok && load_ok
        && call_preserving(core, trainer_has, saved_high, 0, 0, 0) == 1U
        && call_preserving(core, trainer_has, 89U, 0, 0, 0) == 1U;
    tv32_close_core(core);

    tv32_trace("final_assertions");
    fprintf(stderr,
            "mgba-trainer-v5-stage31 checks: "
            "probe_and_hook_binding=%s normal_entry=%s "
            "single_party_sidecar=%s ai_records=%s double_entry=%s "
            "win_path=%s loss_path=%s rematch_mapping=%s "
            "flag_mapping=%s save_reload=%s warnings_errors=%u\n",
            probe_and_hook_binding ? "PASS" : "FAIL",
            normal_entry ? "PASS" : "FAIL",
            single_party_sidecar ? "PASS" : "FAIL",
            ai_records ? "PASS" : "FAIL",
            double_entry ? "PASS" : "FAIL",
            win_path ? "PASS" : "FAIL",
            loss_path ? "PASS" : "FAIL",
            rematch_mapping ? "PASS" : "FAIL",
            flag_mapping ? "PASS" : "FAIL",
            save_reload ? "PASS" : "FAIL",
            log_problem_count);
    if (log_problem_count) tv32_die("mGBA warned/errored during Trainer V5 fixtures");
    if (!(probe_and_hook_binding && normal_entry && single_party_sidecar
          && ai_records && double_entry && win_path && loss_path
          && rematch_mapping && flag_mapping && save_reload))
        tv32_die("one or more focused checks failed");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"trainer_v5_stage31_exact_rom\","
           "\"checks\":{"
           "\"probe_and_hook_binding\":true,"
           "\"normal_entry\":true,"
           "\"single_party_sidecar\":true,"
           "\"ai_records\":true,"
           "\"double_entry\":true,"
           "\"win_path\":true,"
           "\"loss_path\":true,"
           "\"rematch_mapping\":true,"
           "\"flag_mapping\":true,"
           "\"save_reload\":true},"
           "\"warnings_errors\":0}\n");
    return 0;
}
