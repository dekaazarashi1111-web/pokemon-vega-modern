/*
 * Stage56+ standard test-ready save generator and exact-ROM verifier.
 *
 * A blank physical flash image is initialized by the ROM, then only public
 * ROM functions are used to set progression, construct the party, and save
 * two alternating generations.  The host never patches serialized party or
 * checksum bytes.  Historical Stage44 bootstrap behavior remains in its own
 * runner; this file embeds its reviewed boot/save/Continue helpers only.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

enum {
    QA_SCHEMA_VERSION = 1U,
    QA_FLAG_SET = 0x0806DE75U,
    QA_FLAG_GET = 0x0806DEC5U,
    QA_CALCULATE_STATS = 0x0803DBE9U,
    QA_CALCULATE_PP = 0x0804070DU,
    QA_SPECIES_TO_NATIONAL = 0x08042989U,
    QA_GET_SET_POKEDEX = 0x08088A51U,
    QA_SCRIPT_CONTEXT_ENABLED = 0x08069219U,
    QA_RECEPTION_POINTER = 0x093C3340U,
    QA_RECEPTION_SCRIPT = 0x093CDA80U,
    QA_MON_DATA_HELD_ITEM = 12U,
    QA_MON_DATA_MOVE1 = 13U,
    QA_MON_DATA_PP1 = 17U,
    QA_MON_DATA_LEVEL = 56U,
    QA_POKEDEX_GET_CAUGHT = 1U,
    QA_POKEDEX_SET_SEEN = 2U,
    QA_POKEDEX_SET_CAUGHT = 3U,
    QA_SPECIES_MEWTWO = 150U,
    QA_ITEM_MEWTWONITE_Y = 761U,
    QA_LEVEL_MEWTWO = 100U,
    QA_MOVE_PSYCHIC = 94U,
    QA_MOVE_ICE_BEAM = 58U,
    QA_MOVE_THUNDERBOLT = 85U,
    QA_MOVE_AURA_SPHERE = 366U,
    QA_FLAG_POKEMON_GET = 0x0828U,
    QA_FLAG_POKEDEX_GET = 0x0829U,
    QA_FLAG_B_DASH = 0x082FU,
};

static const uint16_t qa_party_species[BOOTSTRAP_TEAM_SIZE] = {
    QA_SPECIES_MEWTWO, 7U, 1U, 4U, 10U, 13U,
};

static const uint8_t qa_party_levels[BOOTSTRAP_TEAM_SIZE] = {
    QA_LEVEL_MEWTWO, 5U, 50U, 50U, 50U, 50U,
};

static const uint16_t qa_mewtwo_moves[BATTLE_CORE_MOVE_SLOTS] = {
    QA_MOVE_PSYCHIC,
    QA_MOVE_ICE_BEAM,
    QA_MOVE_THUNDERBOLT,
    QA_MOVE_AURA_SPHERE,
};

static const uint16_t qa_progression_flags[] = {
    QA_FLAG_POKEMON_GET,
    QA_FLAG_POKEDEX_GET,
    QA_FLAG_B_DASH,
};

static const uint16_t qa_badge_flags[] = {
    0x0820U, 0x0821U, 0x0822U, 0x0823U,
    0x0824U, 0x0825U, 0x0826U, 0x0827U,
};

static uint8_t qa_move_pp(struct mCore *core, uint16_t move, unsigned slot)
{
    return (uint8_t)call_preserving(
        core, QA_CALCULATE_PP, move, 0U, slot, 0U);
}

static void qa_set_and_require_flag(struct mCore *core, uint16_t flag)
{
    (void)call_preserving(core, QA_FLAG_SET, flag, 0U, 0U, 0U);
    if (call_preserving(core, QA_FLAG_GET, flag, 0U, 0U, 0U) != 1U)
        bootstrap_die("standard QA progression flag did not latch");
}

static void qa_mark_caught(struct mCore *core, uint16_t species)
{
    uint32_t national = call_preserving(
        core, QA_SPECIES_TO_NATIONAL, species, 0U, 0U, 0U);
    if (national == 0U)
        return;
    (void)call_preserving(
        core, QA_GET_SET_POKEDEX, national, QA_POKEDEX_SET_SEEN, 0U, 0U);
    (void)call_preserving(
        core, QA_GET_SET_POKEDEX, national, QA_POKEDEX_SET_CAUGHT, 0U, 0U);
    if (call_preserving(core, QA_GET_SET_POKEDEX,
                        national, QA_POKEDEX_GET_CAUGHT, 0U, 0U) != 1U)
        bootstrap_die("standard QA Pokédex caught state differs");
}

static void qa_install_profile(struct mCore *core)
{
    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);

    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        create_mon(core, mon, qa_party_species[slot], qa_party_levels[slot]);
        qa_mark_caught(core, qa_party_species[slot]);
    }
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);

    set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                     QA_MON_DATA_HELD_ITEM, QA_ITEM_MEWTWONITE_Y);
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        uint8_t pp = qa_move_pp(core, qa_mewtwo_moves[slot], slot);
        if (pp == 0U)
            bootstrap_die("standard QA move PP is zero");
        set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                         QA_MON_DATA_MOVE1 + slot, qa_mewtwo_moves[slot]);
        set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                         QA_MON_DATA_PP1 + slot, pp);
    }
    (void)call_preserving(core, QA_CALCULATE_STATS,
                          BOOTSTRAP_PLAYER_PARTY, 0U, 0U, 0U);

    for (unsigned index = 0U; index < ARRAY_LEN(qa_progression_flags); ++index)
        qa_set_and_require_flag(core, qa_progression_flags[index]);
    for (unsigned index = 0U; index < ARRAY_LEN(qa_badge_flags); ++index)
        qa_set_and_require_flag(core, qa_badge_flags[index]);
}

static void qa_verify_resident_profile(struct mCore *core)
{
    if (read8(core, BOOTSTRAP_PLAYER_COUNT) != BOOTSTRAP_TEAM_SIZE)
        bootstrap_die("standard QA party count differs");
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                            mon, 11U, 0U, 0U) != qa_party_species[slot]
            || call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                               mon, QA_MON_DATA_LEVEL, 0U, 0U)
                   != qa_party_levels[slot])
            bootstrap_die("standard QA party identity differs");
    }
    if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                        BOOTSTRAP_PLAYER_PARTY,
                        QA_MON_DATA_HELD_ITEM, 0U, 0U)
            != QA_ITEM_MEWTWONITE_Y)
        bootstrap_die("standard QA Mewtwo held item differs");
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                            BOOTSTRAP_PLAYER_PARTY,
                            QA_MON_DATA_MOVE1 + slot, 0U, 0U)
                != qa_mewtwo_moves[slot]
            || call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                               BOOTSTRAP_PLAYER_PARTY,
                               QA_MON_DATA_PP1 + slot, 0U, 0U)
                   != qa_move_pp(core, qa_mewtwo_moves[slot], slot))
            bootstrap_die("standard QA Mewtwo move or PP differs");
    }
    for (unsigned index = 0U; index < ARRAY_LEN(qa_progression_flags); ++index) {
        if (call_preserving(core, QA_FLAG_GET,
                            qa_progression_flags[index], 0U, 0U, 0U) != 1U)
            bootstrap_die("standard QA progression flag reload differs");
    }
    for (unsigned index = 0U; index < ARRAY_LEN(qa_badge_flags); ++index) {
        if (call_preserving(core, QA_FLAG_GET,
                            qa_badge_flags[index], 0U, 0U, 0U) != 1U)
            bootstrap_die("standard QA badge flag reload differs");
    }
    if (call_preserving(core, QA_GET_SET_POKEDEX,
                        150U, QA_POKEDEX_GET_CAUGHT, 0U, 0U) != 1U)
        bootstrap_die("standard QA Mewtwo Pokédex state differs");
}

static void qa_verify_loaded(struct mCore *core)
{
    uint32_t save1;
    uint32_t save2;
    run_fixed_frames(core);
    if (call_preserving(core, BOOTSTRAP_LOAD_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        bootstrap_die("standard QA fresh-core Save_LoadGameData failed");
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    save2 = read32(core, BOOTSTRAP_SAVE_BLOCK2_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U)
        || save2 < 0x02000000U || save2 >= 0x02040000U || (save2 & 3U)
        || read8(core, save1 + 4U) != BOOTSTRAP_MAP_GROUP
        || read8(core, save1 + 5U) != BOOTSTRAP_MAP_NUMBER
        || read16(core, save1) != BOOTSTRAP_X
        || read16(core, save1 + 2U) != BOOTSTRAP_Y)
        bootstrap_die("standard QA field reload differs");
    for (unsigned index = 0U; index < BOOTSTRAP_MAP_VIEW_COUNT; ++index) {
        if (read16(core, save2 + BOOTSTRAP_MAP_VIEW_OFFSET + index * 2U)
                != bootstrap_expected_map_view[index])
            bootstrap_die("standard QA saved map view differs");
    }
    qa_verify_resident_profile(core);
}

static void qa_generate(const char *rom_path, const char *save_path)
{
    struct mCore *core;
    uint32_t save1;
    bootstrap_phase = "qa-generate-blank";
    bootstrap_write_blank_save(save_path);
    core = bootstrap_open_core(rom_path, save_path, NULL);
    bootstrap_phase = "qa-generate-natural-new-game";
    run_trace_prefix(core);
    run_fixed_frames(core);
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U))
        bootstrap_die("standard QA natural new game did not initialize");

    bootstrap_phase = "qa-generate-field-warp";
    (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                          BOOTSTRAP_MAP_GROUP, BOOTSTRAP_MAP_NUMBER,
                          BOOTSTRAP_X, BOOTSTRAP_Y);
    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U)
        || read8(core, save1 + 4U) != BOOTSTRAP_MAP_GROUP
        || read8(core, save1 + 5U) != BOOTSTRAP_MAP_NUMBER
        || read16(core, save1) != BOOTSTRAP_X
        || read16(core, save1 + 2U) != BOOTSTRAP_Y
        || read32(core, BATTLE_CORE_MAIN_CALLBACK2) != BOOTSTRAP_CB2_OVERWORLD
        || read32(core, QA_RECEPTION_POINTER) != QA_RECEPTION_SCRIPT)
        bootstrap_die("standard QA Codex reception field differs");

    qa_install_profile(core);
    bootstrap_prepare_save_map_view(core);
    bootstrap_phase = "qa-generate-two-saves";
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        bootstrap_die("standard QA two-generation TrySavingData failed");
    bootstrap_close_core(core);
}

static bool qa_verify_codex_reception(struct mCore *core, color_t *video,
                                      uint64_t *before, uint64_t *after)
{
    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    /* The reception NPC is immediately north of the saved tile. */
    run_key_frames(core, 0x0040U, 2U);
    run_key_frames(core, 0U, 30U);
    if (read16(core, save1) != BOOTSTRAP_X
        || read16(core, save1 + 2U) != BOOTSTRAP_Y)
        return false;
    *before = bootstrap_framebuffer_hash(video);
    run_key_frames(core, 1U, 2U);
    run_key_frames(core, 0U, 180U);
    *after = bootstrap_framebuffer_hash(video);
    return *before != *after
        && call_preserving(core, QA_SCRIPT_CONTEXT_ENABLED,
                           0U, 0U, 0U, 0U) != 0U;
}

#ifndef TEST_READY_SAVE_EMBEDDED
int main(int argc, char **argv)
{
    color_t *video;
    struct mCore *core;
    char rom_sha256[65];
    char save_sha256[65];
    uint64_t field_framebuffer;
    uint64_t reception_framebuffer;
    uint8_t lead_pp[BATTLE_CORE_MOVE_SLOTS];
    unsigned transitions;
    bool reception_visible;
    if (argc != 3) {
        fprintf(stderr, "usage: %s STAGE_ROM OUTPUT_SAVE\n", argv[0]);
        return 2;
    }
    if (snprintf(bootstrap_slot_paths[0], sizeof(bootstrap_slot_paths[0]),
                 "%s.slot0-only.tmp", argv[2]) <= 0
        || snprintf(bootstrap_slot_paths[1], sizeof(bootstrap_slot_paths[1]),
                    "%s.slot1-only.tmp", argv[2]) <= 0)
        bootstrap_die("standard QA temporary path formatting failed");
    atexit(bootstrap_cleanup);
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);

    qa_generate(argv[1], argv[2]);
    video = calloc(240U * 160U, sizeof(*video));
    if (!video)
        bootstrap_die("standard QA framebuffer allocation failed");
    bootstrap_phase = "qa-verify-full-save";
    core = bootstrap_open_core(argv[1], argv[2], video);
    qa_verify_loaded(core);
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot)
        lead_pp[slot] = qa_move_pp(core, qa_mewtwo_moves[slot], slot);
    bootstrap_close_core(core);

    memset(video, 0, 240U * 160U * sizeof(*video));
    bootstrap_phase = "qa-verify-natural-continue";
    core = bootstrap_open_core(argv[1], argv[2], video);
    bootstrap_continue_to_field(core);
    transitions = bootstrap_pixel_transitions(video);
    reception_visible = qa_verify_codex_reception(
        core, video, &field_framebuffer, &reception_framebuffer);
    bootstrap_write_ppm(argv[2], video);
    bootstrap_close_core(core);
    free(video);
    if (transitions < 100U || !reception_visible)
        bootstrap_die("standard QA natural Codex reception differs");

    bootstrap_copy_with_blank_slot(argv[2], bootstrap_slot_paths[0], 1U);
    bootstrap_copy_with_blank_slot(argv[2], bootstrap_slot_paths[1], 0U);
    for (unsigned slot = 0U; slot < 2U; ++slot) {
        bootstrap_phase = slot == 0U ? "qa-verify-slot0" : "qa-verify-slot1";
        core = bootstrap_open_core(argv[1], bootstrap_slot_paths[slot], NULL);
        qa_verify_loaded(core);
        bootstrap_close_core(core);
    }
    if (log_problem_count != 0U)
        bootstrap_die("standard QA mGBA emitted warning/error diagnostics");

    sha256_file(argv[1], rom_sha256);
    sha256_file(argv[2], save_sha256);
    printf("{\"schema_version\":%u,\"task\":\"USER-20260827-STAGE56-TEST-READY-SAVE\","
           "\"status\":\"PASS\",\"rom_sha256\":\"%s\",\"save_sha256\":\"%s\","
           "\"save_size\":%u,\"save_generations\":2,"
           "\"slot0_fresh_load\":true,\"slot1_fresh_load\":true,"
           "\"natural_continue\":true,\"codex_reception_visible\":true,"
           "\"map\":{\"group\":%u,\"number\":%u,\"x\":%u,\"y\":%u},"
           "\"progression_flags\":[2088,2089,2095],"
           "\"badge_flags\":[2080,2081,2082,2083,2084,2085,2086,2087],"
           "\"party_species\":[150,7,1,4,10,13],"
           "\"party_levels\":[100,5,50,50,50,50],"
           "\"lead\":{\"species_id\":150,\"level\":100,\"held_item_id\":761,"
           "\"moves\":[94,58,85,366],\"pp\":[%u,%u,%u,%u]},"
           "\"field_framebuffer_fnv1a64\":\"%016" PRIx64 "\","
           "\"reception_framebuffer_fnv1a64\":\"%016" PRIx64 "\","
           "\"pixel_transitions\":%u,\"warnings\":0}\n",
           QA_SCHEMA_VERSION, rom_sha256, save_sha256,
           BOOTSTRAP_SAVE_SIZE, BOOTSTRAP_MAP_GROUP, BOOTSTRAP_MAP_NUMBER,
           BOOTSTRAP_X, BOOTSTRAP_Y,
           lead_pp[0], lead_pp[1], lead_pp[2], lead_pp[3],
           field_framebuffer, reception_framebuffer, transitions);
    return 0;
}
#endif
