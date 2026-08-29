/* Focused Stage59 land/water, fishing, and hidden wild-identity smoke. */

#define main stage17_regression_unused_main
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_regression_smoke.c"
#pragma GCC diagnostic pop
#undef main

enum {
    STAGE59_SPECIES_COUNT = 1621U,
    STAGE59_LAND_CALLS = 96U,
    STAGE59_FISHING_CALLS = 96U,
};

static void stage59_clear_enemy(struct mCore *core)
{
    for (unsigned byte = 0U; byte < PARTY_BYTES; ++byte)
        write8(core, ENEMY_PARTY + byte, 0U);
    write8(core, ENEMY_PARTY_COUNT, 0U);
}

static uint16_t stage59_generated_species(struct mCore *core,
                                          const char *label)
{
    uint16_t species = (uint16_t)call_thumb(
        core, GET_MON_DATA, ENEMY_PARTY, 11U, 0U, 0U);
    if (species == 0U || species >= STAGE59_SPECIES_COUNT) {
        fprintf(stderr,
                "mgba-stage59-wild-methods: %s Species out of range: %u\n",
                label, species);
        exit(1);
    }
    verify_canonical_nickname(core, ENEMY_PARTY, species);
    return species;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM LAND FISH HIDDEN SET_MODE\n", argv[0]);
        return 2;
    }
    uint32_t land = parse_u32(argv[2], "land adapter") | 1U;
    uint32_t fishing = parse_u32(argv[3], "fishing adapter") | 1U;
    uint32_t hidden = parse_u32(argv[4], "hidden adapter") | 1U;
    uint32_t set_mode = parse_u32(argv[5], "mode setter") | 1U;
    if (!rom_code_pointer(land) || !rom_code_pointer(fishing)
        || !rom_code_pointer(hidden) || !rom_code_pointer(set_mode)) {
        die("Stage59 wild-method argument contract failed");
    }

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core) || !mCoreLoadFile(core, argv[1]))
        die("Stage59 wild-method core/ROM initialization failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        die("Stage59 wild-method video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);
    uint32_t transitions = run_natural_new_game(core, video);

    uint32_t save1 = read32(core, G_SAVE_BLOCK1);
    uint32_t wild_root = read32(core, ROM_BASE + UINT32_C(0x8257C));
    if (save1 < UINT32_C(0x02000000) || save1 >= UINT32_C(0x02040000)
        || !rom_pointer(wild_root)) {
        die("Stage59 wild-method field state is invalid");
    }

    uint32_t route_land_info = 0U;
    uint32_t fishing_info = 0U;
    for (unsigned index = 0U; index < 1024U; ++index) {
        uint32_t header = wild_root + index * 20U;
        uint8_t group = read8(core, header);
        uint8_t map = read8(core, header + 1U);
        if (group == 0xFFU && map == 0xFFU)
            break;
        if (group == 3U && map == 19U)
            route_land_info = read32(core, header + 4U);
        if (group == 11U && map == 3U)
            fishing_info = read32(core, header + 16U);
    }
    if (!rom_pointer(route_land_info) || !rom_pointer(fishing_info))
        die("Stage59 wild-method native fixtures are missing");

    write8(core, save1 + 4U, 3U);
    write8(core, save1 + 5U, 19U);
    (void)call_thumb(core, set_mode, 1U, 0U, 0U, 0U);
    write32(core, GLOBAL_RNG, UINT32_C(0x12345678));
    uint16_t land_first = 0U;
    uint16_t land_last = 0U;
    for (unsigned call = 0U; call < STAGE59_LAND_CALLS; ++call) {
        stage59_clear_enemy(core);
        if (call_thumb(core, land, route_land_info, 0U, 0U, 0U) != 1U)
            die("Stage59 land/water adapter rejected valid info");
        uint16_t species = stage59_generated_species(core, "land/water");
        if (call == 0U)
            land_first = species;
        land_last = species;
    }

    write8(core, save1 + 4U, 11U);
    write8(core, save1 + 5U, 3U);
    (void)call_thumb(core, set_mode, 2U, 0U, 0U, 0U);
    write32(core, GLOBAL_RNG, UINT32_C(0x24681357));
    uint16_t fishing_first = 0U;
    uint16_t fishing_last = 0U;
    for (unsigned call = 0U; call < STAGE59_FISHING_CALLS; ++call) {
        stage59_clear_enemy(core);
        uint16_t returned = (uint16_t)call_thumb(
            core, fishing, fishing_info, 2U, 0U, 0U);
        uint16_t generated = stage59_generated_species(core, "fishing");
        if (returned != generated)
            die("Stage59 fishing return/party Species differ");
        if (call == 0U)
            fishing_first = generated;
        fishing_last = generated;
    }

    write8(core, save1 + 4U, 3U);
    write8(core, save1 + 5U, 63U);
    (void)call_thumb(core, set_mode, 4U, 0U, 0U, 0U);
    write32(core, GLOBAL_RNG, UINT32_C(0x10293847));
    stage59_clear_enemy(core);
    if (call_thumb(core, hidden, 0U, 0U, 0U, 0U) != 1U)
        die("Stage59 hidden adapter rejected an authored indoor map");
    uint16_t hidden_species = stage59_generated_species(core, "hidden");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"framebuffer_transitions\":%" PRIu32 ","
        "\"methods_checked\":3,\"warnings_errors\":0,"
        "\"land_water\":{\"calls\":%u,\"name_checks\":%u,"
        "\"first_species\":%u,\"last_species\":%u},"
        "\"fishing\":{\"calls\":%u,\"name_checks\":%u,"
        "\"first_species\":%u,\"last_species\":%u},"
        "\"hidden\":{\"calls\":1,\"name_checks\":1,"
        "\"species\":%u},"
        "\"claims\":{\"land_water_canonical_name\":true,"
        "\"fishing_canonical_name\":true,"
        "\"hidden_canonical_name\":true,"
        "\"all_generated_species_in_range\":true}}\n",
        transitions, STAGE59_LAND_CALLS, STAGE59_LAND_CALLS,
        land_first, land_last,
        STAGE59_FISHING_CALLS, STAGE59_FISHING_CALLS,
        fishing_first, fishing_last, hidden_species);

    free(video);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
