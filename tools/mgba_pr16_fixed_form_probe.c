/* Native fixed-FORM menu probe for the four finite P03 transition targets.
 * Starting map, progress and party are fixtures.  After the observation
 * barrier the controller uses only ordinary GBA input and read-only state.
 * This probe deliberately does not claim physical acceptance or close P03. */
#include "pr16_form_breeding_helpers.c"
#define F_SHA "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e"
#define F_STATE 0x0203F720U
#define F_CURSOR 0x0203AD5EU
#define F_PARTY_SLOT 0x0203B01DU
#define F_TARGET (QOL_PLAYER_PARTY+100U)
#define F_SCOPE "PR16_P03_FIXED_FORM_TRANSITION_NATIVE_PROBE"
#define F_ROWS_PER_PAGE 5U
#define F_MAX_PAGES 80U
#define F_NAVIGATION "canonical-ordinal-native-input"

struct FCase {
    const char *name;
    const char *family;
    const char *route_id;
    unsigned form_index;
    unsigned base_species;
    unsigned target_species;
    unsigned project_move;
};

static const struct FCase f_cases[] = {
    {"necrozma-dusk-mane-native-probe", "necrozma_fixed_transition",
     "667255b406678096a7fa9344", 245U, 1198U, 1260U, 690U},
    {"necrozma-dawn-wings-native-probe", "necrozma_fixed_transition",
     "a79bbbec71c9a6be03a7d1e4", 246U, 1198U, 1261U, 669U},
    {"zacian-crowned-native-probe", "crowned_battle_transition",
     "371ffcca84ed4eb8fbb6d56b", 280U, 1361U, 1386U, 768U},
    {"zamazenta-crowned-native-probe", "crowned_battle_transition",
     "2a8a2a856af40ec96087c9a7", 281U, 1362U, 1387U, 769U},
};

static const unsigned f_moves[4] = {98U, 235U, 552U, 33U};
static const unsigned f_pp[4] = {11U, 3U, 4U, 7U};

static void f_shot(const char *prefix, const char *suffix) {
    char path[4096];
    int n = snprintf(path, sizeof(path), "%s-%s.ppm", prefix, suffix);
    a_require(n > 0 && n < (int)sizeof(path), "fixed form screenshot path too long");
    FILE *file = fopen(path, "wb");
    a_require(file != NULL, "fixed form screenshot open failed");
    a_require(fprintf(file, "P6\n240 160\n255\n") > 0,
              "fixed form screenshot header failed");
    for (unsigned i = 0; i < 240U * 160U; ++i) {
        uint32_t pixel = (uint32_t)b_video[i];
        uint8_t rgb[3] = {
            (uint8_t)pixel,
            (uint8_t)(pixel >> 8),
            (uint8_t)(pixel >> 16),
        };
        a_require(fwrite(rgb, 1, 3, file) == 3,
                  "fixed form screenshot write failed");
    }
    a_require(!fclose(file), "fixed form screenshot close failed");
}

static void f_state(struct mCore *core, const char *label) {
    b_state(core, label);
    fprintf(stderr,
            "FIXFORM state=%08x result=%u host=%u service=%u mode=%u page=%u "
            "window=%u cursor=%u pending=%u slot=%u test=%u save=%u cb2=%08x\n",
            read32(core, F_STATE), read16(core, F_STATE + 8U),
            read8(core, F_STATE + 18U), read8(core, F_STATE + 20U),
            read8(core, F_STATE + 19U), read8(core, F_STATE + 21U),
            read8(core, F_STATE + 22U), read8(core, F_CURSOR),
            read16(core, F_STATE + 10U), read8(core, F_PARTY_SLOT),
            read8(core, F_STATE + 27U), read32(core, P03_SAVE_COUNTER),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2));
}

static bool f_menu(struct mCore *core, unsigned mode, unsigned page) {
    return read16(core, F_STATE + 8U) == 9U
        && read8(core, F_STATE + 18U) == 3U
        && read8(core, F_STATE + 20U) == 3U
        && read8(core, F_STATE + 19U) == mode
        && read8(core, F_STATE + 21U) == page
        && read8(core, F_STATE + 22U) < 32U
        && read8(core, P02S_FIELD_LOCK)
        && !read8(core, F_STATE + 27U);
}

static bool f_wait_menu(struct mCore *core, unsigned mode, unsigned page) {
    for (unsigned frame = 0; frame < 1800U; ++frame) {
        if (f_menu(core, mode, page)) {
            b_frames_run(core, 0U, 30U);
            return true;
        }
        b_frame(core, 0U);
    }
    return false;
}

static bool f_native_terminal(struct mCore *core, unsigned page) {
    return b_field(core)
        && read16(core, F_STATE + 8U) == 2U
        && read8(core, F_STATE + 18U) == 3U
        && read8(core, F_STATE + 20U) == 3U
        && read8(core, F_STATE + 19U) == 2U
        && read8(core, F_STATE + 21U) == page
        && read8(core, F_STATE + 22U) == 0xFFU;
}

/* Return 1 for party picker, 2 for a native terminal item, 0 for timeout. */
static unsigned f_wait_party(struct mCore *core, unsigned page) {
    unsigned terminal_frames = 0U;
    for (unsigned frame = 0; frame < 1800U; ++frame) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY) {
            b_frames_run(core, 0U, 120U);
            return 1U;
        }
        if (frame >= 30U && f_native_terminal(core, page)) {
            if (++terminal_frames == 12U) {
                return 2U;
            }
        } else {
            terminal_frames = 0U;
        }
        b_frame(core, 0U);
    }
    return 0U;
}

static bool f_open_location(struct mCore *core, unsigned page, unsigned cursor,
                            const char *prefix) {
    if (page >= F_MAX_PAGES || cursor >= F_ROWS_PER_PAGE) {
        return false;
    }
    b_position(core, 1U, 36U, 6U, 4U);
    unsigned object = read8(core, P02S_PLAYER_AVATAR + 5U);
    if (object >= 16U) {
        return false;
    }
    if ((read8(core, P02S_OBJECT_EVENTS + object * 0x24U + 0x18U) & 15U) != 2U) {
        b_frame(core, QOL_KEY_UP);
    }
    b_frames_run(core, 0U, 30U);
    b_position(core, 1U, 36U, 6U, 4U);
    b_press(core, QOL_KEY_A, 90U);
    if (!f_wait_menu(core, 0U, 0U)) {
        f_shot(prefix, "root-absent");
        return false;
    }
    if (read8(core, F_CURSOR) != 0U) {
        return false;
    }
    b_press(core, QOL_KEY_DOWN, 30U);
    if (read8(core, F_CURSOR) != 1U) {
        return false;
    }
    b_press(core, QOL_KEY_A, 60U);
    if (!f_wait_menu(core, 2U, 0U)) {
        f_shot(prefix, "forms-absent");
        return false;
    }
    for (unsigned current = 0U; current < page; ++current) {
        if (!f_menu(core, 2U, current) || read8(core, F_CURSOR) != 0U) {
            return false;
        }
        for (unsigned row = 0U; row < F_ROWS_PER_PAGE; ++row) {
            b_press(core, QOL_KEY_DOWN, 30U);
        }
        if (read8(core, F_CURSOR) != F_ROWS_PER_PAGE) {
            return false;
        }
        b_press(core, QOL_KEY_A, 60U);
        if (!f_wait_menu(core, 2U, current + 1U)) {
            f_shot(prefix, "page-navigation-failed");
            return false;
        }
    }
    if (!f_menu(core, 2U, page) || read8(core, F_CURSOR) != 0U) {
        return false;
    }
    for (unsigned row = 0U; row < cursor; ++row) {
        b_press(core, QOL_KEY_DOWN, 30U);
    }
    return read8(core, F_CURSOR) == cursor;
}

int main(int argc, char **argv) {
    if (argc == 3 && !strcmp(argv[1], "--guard-check")) {
        a_guard_check(argv[2]);
    }
    if (argc != 8) {
        return 2;
    }
    const struct FCase *selected = NULL;
    for (unsigned i = 0U; i < sizeof(f_cases) / sizeof(f_cases[0]); ++i) {
        if (!strcmp(argv[5], f_cases[i].name)) {
            selected = &f_cases[i];
        }
    }
    if (selected == NULL) {
        return 2;
    }
    char *end = NULL;
    unsigned long ordinal_raw = strtoul(argv[6], &end, 10);
    if (end == argv[6] || *end || ordinal_raw >= F_MAX_PAGES * F_ROWS_PER_PAGE) {
        return 2;
    }
    unsigned ordinal = (unsigned)ordinal_raw;
    unsigned page = ordinal / F_ROWS_PER_PAGE;
    unsigned cursor = ordinal % F_ROWS_PER_PAGE;
    const char *prefix = argv[7];

    char hash[65], seed[65], after[65];
    sha256_file(argv[1], hash);
    sha256_file(argv[2], seed);
    a_require(!strcmp(hash, F_SHA) && !strcmp(hash, argv[3])
                  && !strcmp(seed, B_SEED_SHA) && !strcmp(seed, argv[4]),
              "fixed form probe input identity differs");

    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    core->setVideoBuffer(core, b_video, 240U);
    core->reset(core);
    a_require(a_continue(core), "fixed form probe initial Continue failed");
    a_flash_prepare(core);

    /* Exact FINAL_LEAGUE and authored-host fixture, before map load. */
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME, 0U, 0U, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    write8(core, QOL_LEDGER + 0x73FU, 1U);
    write8(core, QOL_LEDGER + 0x745U, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0U, 0U, 0U);
    (void)call_preserving(core, 0x09220861U, 1U, 36U, 6U, 4U);
    run_key_frames(core, 0U, 1800U);
    for (unsigned i = 0U; i < 12U && !b_field(core); ++i) {
        b_press(core, QOL_KEY_B, 180U);
    }
    b_position(core, 1U, 36U, 6U, 4U);

    clear_parties(core);
    b_create(core, QOL_PLAYER_PARTY, 0x123456F0U, 0x11223344U);
    create_mon(core, F_TARGET, selected->base_species, 50U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 2U);
    for (unsigned i = 0U; i < 4U; ++i) {
        set_mon_data_u32(core, F_TARGET, 13U + i, f_moves[i]);
        set_mon_data_u32(core, F_TARGET, 17U + i, f_pp[i]);
    }
    set_mon_data_u32(core, F_TARGET, 21U, 229U);
    unsigned pid = b_data(core, F_TARGET, 0U);
    unsigned ot = b_data(core, F_TARGET, 1U);
    uint8_t decoy[100];
    b_copy(core, QOL_PLAYER_PARTY, decoy, 100U);
    unsigned save_before = read32(core, P03_SAVE_COUNTER);

    struct mCore saved = *core;
    bool menu_opened = false;
    bool party_opened = false;
    bool target_match = false;
    bool selection_sent = false;
    bool field_returned = false;
    unsigned wait_kind = 0U;
    unsigned pending = 0U;

    /* Observation barrier: only native GBA input and read-only observations. */
    a_guard(core);
    menu_opened = f_open_location(core, page, cursor, prefix);
    if (menu_opened) {
        f_shot(prefix, "predicted-row");
        f_state(core, "predicted-row");
        b_press(core, QOL_KEY_A, 30U);
        wait_kind = f_wait_party(core, page);
        party_opened = wait_kind == 1U;
        pending = read16(core, F_STATE + 10U);
        target_match = party_opened && pending == selected->form_index;
        if (target_match) {
            for (unsigned i = 0U; i < 8U && read8(core, F_PARTY_SLOT) != 1U; ++i) {
                b_press(core, QOL_KEY_DOWN, 30U);
            }
            if (read8(core, F_PARTY_SLOT) == 1U) {
                selection_sent = true;
                b_press(core, QOL_KEY_A, 180U);
                b_frames_run(core, 0U, 300U);
                field_returned = b_field(core);
            }
        } else if (party_opened) {
            b_press(core, QOL_KEY_B, 180U);
            b_wait(core);
            field_returned = b_field(core);
        } else {
            field_returned = b_field(core);
        }
    }
    f_shot(prefix, "observed");
    f_state(core, "observed");

    unsigned result = read16(core, F_STATE + 8U);
    unsigned callback2 = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    unsigned window = read8(core, F_STATE + 22U);
    unsigned save_after = read32(core, P03_SAVE_COUNTER);
    unsigned total_frames = b_frames;
    a_restore(core, &saved);

    unsigned species_after = b_data(core, F_TARGET, 11U);
    unsigned held_item_after = b_data(core, F_TARGET, 12U);
    unsigned pp_bonuses_after = b_data(core, F_TARGET, 21U);
    unsigned moves_after[4], pp_after[4];
    for (unsigned i = 0U; i < 4U; ++i) {
        moves_after[i] = b_data(core, F_TARGET, 13U + i);
        pp_after[i] = b_data(core, F_TARGET, 17U + i);
    }
    bool identity_preserved = b_data(core, F_TARGET, 0U) == pid
        && b_data(core, F_TARGET, 1U) == ot;
    uint8_t decoy_after[100];
    b_copy(core, QOL_PLAYER_PARTY, decoy_after, 100U);
    bool nonselected_preserved = !memcmp(decoy, decoy_after, 100U);
    const char *outcome = !menu_opened ? "menu-navigation-failed"
        : wait_kind == 2U ? "native-terminal"
        : !party_opened ? "party-not-opened"
        : !target_match ? "pending-mismatch"
        : selection_sent ? "selected-target" : "party-slot-not-selected";

    a_require(!read8(core, F_STATE + 27U), "fixed form test mode was enabled");
    a_require(identity_preserved, "fixed form probe changed individual identity");
    a_require(nonselected_preserved, "fixed form probe changed nonselected individual");
    a_require(!log_problem_count, "fixed form probe emulator diagnostic differs");

    qol_close(core);
    qol_log_core = NULL;
    sha256_file(argv[1], after);
    a_require(!strcmp(hash, after), "fixed form probe changed ROM");

    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\",", F_SCOPE);
    printf("\"case\":\"%s\",\"family\":\"%s\",\"route_id\":\"%s\",", selected->name, selected->family, selected->route_id);
    printf("\"rom_sha256\":\"%s\",\"form_index\":%u,\"canonical_ordinal\":%u,", hash, selected->form_index, ordinal);
    printf("\"menu_page\":%u,\"menu_cursor\":%u,\"menu_navigation\":\"%s\",", page, cursor, F_NAVIGATION);
    printf("\"base_species\":%u,\"target_species\":%u,\"project_move\":%u,", selected->base_species, selected->target_species, selected->project_move);
    printf("\"menu_opened\":%s,\"party_opened\":%s,\"target_match\":%s,\"selection_sent\":%s,\"field_returned\":%s,",
           menu_opened ? "true" : "false", party_opened ? "true" : "false",
           target_match ? "true" : "false", selection_sent ? "true" : "false",
           field_returned ? "true" : "false");
    printf("\"probe_outcome\":\"%s\",\"wait_kind\":%u,\"pending_form\":%u,\"result\":%u,\"main_callback2\":%u,\"window\":%u,", outcome, wait_kind, pending, result, callback2, window);
    printf("\"species_after\":%u,\"held_item_after\":%u,\"moves_after\":[%u,%u,%u,%u],\"pp_after\":[%u,%u,%u,%u],\"pp_bonuses_after\":%u,",
           species_after, held_item_after, moves_after[0], moves_after[1], moves_after[2], moves_after[3],
           pp_after[0], pp_after[1], pp_after[2], pp_after[3], pp_bonuses_after);
    printf("\"identity_preserved\":true,\"nonselected_preserved\":true,\"save_counter_before\":%u,\"save_counter_after\":%u,\"total_frames\":%u,", save_before, save_after, total_frames);
    printf("\"starting_progress_individual_map_are_fixtures\":true,\"fresh_core\":true,\"input_only_after_guard\":true,\"warnings_errors\":0,");
    printf("\"acceptance_claimed\":false,\"p03_fixed_form_gap_closed\":false,\"full_p03_acceptance\":false,\"release_ready\":false}\n");
    return 0;
}
