/* Exhaustive exact-ROM smoke for the canonical 1,621-Species creation surface. */

#define BATTLE_CORE_EMBEDDED
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    SPECIES_RUNTIME_COUNT = 1621,
    SPECIES_RUNTIME_EGG = 412,
    SPECIES_RUNTIME_PIDGEY = 418,
    SPECIES_RUNTIME_CATERPIE = 649,
    SPECIES_RUNTIME_LECHONK = 1484,
    GET_SPECIES_NAME = 0x080406C5,
    NATIONAL_DEX_TO_SPECIES = 0x080428F1,
    SPECIES_TO_NATIONAL_DEX = 0x08042989,
    DECOMPRESS_PIC_FROM_TABLE = 0x0800EA95,
    HANDLE_LOAD_SPECIAL_POKE_PIC = 0x0800EABD,
    GET_MON_SPRITE_PALETTE = 0x0804373D,
    GET_MON_SPRITE_PALETTE_STRUCT = 0x080437C9,
    GET_ICON_SPECIES = 0x08096989,
    GET_ICON_PALETTE_INDEX = 0x08096C25,
    LZ77_UNCOMP_WRAM = 0x081C7A91,
    FRONT_TABLE_POINTER = 0x08000128,
    BACK_TABLE_POINTER = 0x0800012C,
    PALETTE_TABLE_POINTER = 0x08000130,
    SHINY_PALETTE_TABLE_POINTER = 0x08000134,
    ICON_TABLE_POINTER = 0x08000138,
    ICON_PALETTE_TABLE_POINTER = 0x0800013C,
    NAME_SCRATCH = 0x0203E800,
    NAME_LENGTH = 11,
    PIC_SCRATCH = 0x0203A000,
    PIC_EXPECTED = 0x0203A800,
    PIC_SIZE = 2048,
};

static void clear_runtime_bytes(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0; index < size; ++index) {
        write8(core, address + index, 0xA5U);
    }
}

static void require_equal_runtime_bytes(struct mCore *core,
                                        uint32_t left, uint32_t right,
                                        unsigned size, const char *label)
{
    for (unsigned index = 0; index < size; ++index) {
        if (read8(core, left + index) != read8(core, right + index)) {
            fprintf(stderr, "mgba-species-runtime-smoke: %s differs at %u\n",
                    label, index);
            exit(1);
        }
    }
}

static void verify_pic_path(struct mCore *core, uint16_t species,
                            uint32_t table_pointer_site, const char *label)
{
    uint32_t table = read32(core, table_pointer_site);
    uint32_t row = table + (uint32_t)species * 8U;
    uint32_t compressed = read32(core, row);

    if (compressed < 0x08000000U || compressed >= 0x0A000000U) {
        battle_core_die("canonical picture pointer is outside ROM");
    }
    clear_runtime_bytes(core, PIC_SCRATCH, PIC_SIZE);
    clear_runtime_bytes(core, PIC_EXPECTED, PIC_SIZE);
    (void)call_preserving(core, LZ77_UNCOMP_WRAM,
                          compressed, PIC_EXPECTED, 0, 0);
    (void)call_preserving(core, HANDLE_LOAD_SPECIAL_POKE_PIC,
                          row, PIC_SCRATCH, species, 0x12345678U);
    require_equal_runtime_bytes(core, PIC_SCRATCH, PIC_EXPECTED, PIC_SIZE, label);

    clear_runtime_bytes(core, PIC_SCRATCH, PIC_SIZE);
    (void)call_preserving(core, DECOMPRESS_PIC_FROM_TABLE,
                          row, PIC_SCRATCH, species, 0);
    require_equal_runtime_bytes(core, PIC_SCRATCH, PIC_EXPECTED, PIC_SIZE, label);
}

static void verify_display_species(struct mCore *core, uint16_t species)
{
    uint32_t front = read32(core, FRONT_TABLE_POINTER);
    uint32_t back = read32(core, BACK_TABLE_POINTER);
    uint32_t palette = read32(core, PALETTE_TABLE_POINTER);
    uint32_t shiny = read32(core, SHINY_PALETTE_TABLE_POINTER);
    uint32_t icon = read32(core, ICON_TABLE_POINTER);
    uint32_t icon_palette = read32(core, ICON_PALETTE_TABLE_POINTER);
    uint32_t personality = 0x12345678U;
    uint32_t expected_palette = read32(core, palette + (uint32_t)species * 8U);
    uint32_t actual_palette;
    uint32_t actual_palette_struct;
    uint32_t actual_icon_species;
    uint32_t actual_icon_palette;

    if (read16(core, front + (uint32_t)species * 8U + 6U) != species
        || read16(core, back + (uint32_t)species * 8U + 6U) != species
        || read16(core, palette + (uint32_t)species * 8U + 4U) != species
        || read16(core, shiny + (uint32_t)species * 8U + 4U)
               != SPECIES_RUNTIME_COUNT + species) {
        battle_core_die("canonical sprite/palette resource tag differs");
    }
    if (read32(core, icon + (uint32_t)species * 4U) == 0U) {
        battle_core_die("canonical icon pointer is NULL");
    }

    verify_pic_path(core, species, FRONT_TABLE_POINTER, "front picture");
    verify_pic_path(core, species, BACK_TABLE_POINTER, "back picture");
    actual_palette = call_preserving(
        core, GET_MON_SPRITE_PALETTE, species, 0U, personality, 0U);
    actual_palette_struct = call_preserving(
        core, GET_MON_SPRITE_PALETTE_STRUCT, species, 0U, personality, 0U);
    actual_icon_species = call_preserving(
        core, GET_ICON_SPECIES, species, personality, 0U, 0U);
    actual_icon_palette = call_preserving(
        core, GET_ICON_PALETTE_INDEX, species, 0U, 0U, 0U);
    if (actual_palette != expected_palette
        || actual_palette_struct != palette + (uint32_t)species * 8U
        || actual_icon_species != species
        || actual_icon_palette != read8(core, icon_palette + species)) {
        battle_core_die("canonical palette/icon runtime result differs");
    }
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s ROM\n", argv[0]);
        return 2;
    }
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core) || !mCoreLoadFile(core, argv[1])) {
        battle_core_die("Species runtime core/ROM initialization failed");
    }
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);

    unsigned created = 0;
    unsigned named = 0;
    unsigned with_moves = 0;
    for (unsigned species = 1; species < SPECIES_RUNTIME_COUNT; ++species) {
        if (species != SPECIES_RUNTIME_EGG) {
            clear_parties(core);
            seed_fixture(core);
            create_mon(core, ADDR_PLAYER_PARTY, (uint16_t)species, 5);

            bool has_move = false;
            for (unsigned slot = 0; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
                uint32_t move = call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA, ADDR_PLAYER_PARTY,
                    MON_DATA_MOVE1 + slot, 0, 0);
                if (move > BATTLE_CORE_CANONICAL_MOVE_MAX) {
                    battle_core_die("created Species has a move outside canonical ABI");
                }
                has_move |= move != 0;
            }
            with_moves += has_move;
            ++created;
        }

        for (unsigned index = 0; index < NAME_LENGTH; ++index) {
            write8(core, NAME_SCRATCH + index, 0);
        }
        (void)call_preserving(core, GET_SPECIES_NAME,
                              NAME_SCRATCH, species, 0, 0);
        bool terminated = false;
        for (unsigned index = 0; index < NAME_LENGTH; ++index) {
            if (read8(core, NAME_SCRATCH + index) == 0xFFU) {
                terminated = true;
                break;
            }
        }
        if (!terminated || read8(core, NAME_SCRATCH) == 0xFFU) {
            battle_core_die("canonical Species name is blank or unterminated");
        }
        ++named;
    }
    const uint16_t display_samples[] = {
        SPECIES_RUNTIME_EGG,
        SPECIES_RUNTIME_PIDGEY,
        SPECIES_RUNTIME_CATERPIE,
        SPECIES_RUNTIME_LECHONK,
        SPECIES_RUNTIME_COUNT - 1,
    };
    for (unsigned index = 0; index < ARRAY_LEN(display_samples); ++index) {
        verify_display_species(core, display_samples[index]);
    }
    const uint16_t dex_samples[][3] = {
        {7, 7, 0},
        {SPECIES_RUNTIME_EGG, 0, 0},
        {SPECIES_RUNTIME_PIDGEY, 16, SPECIES_RUNTIME_PIDGEY},
        {SPECIES_RUNTIME_CATERPIE, 10, SPECIES_RUNTIME_CATERPIE},
        {SPECIES_RUNTIME_LECHONK, 915, SPECIES_RUNTIME_LECHONK},
    };
    for (unsigned index = 0; index < ARRAY_LEN(dex_samples); ++index) {
        uint16_t species = dex_samples[index][0];
        uint16_t national = dex_samples[index][1];
        uint16_t inverse = dex_samples[index][2];
        uint32_t actual_national = call_preserving(
            core, SPECIES_TO_NATIONAL_DEX, species, 0, 0, 0);
        uint32_t actual_inverse = inverse == 0 ? 0 : call_preserving(
            core, NATIONAL_DEX_TO_SPECIES, national, 0, 0, 0);
        if (actual_national != national || actual_inverse != inverse) {
            fprintf(stderr,
                    "mgba-species-runtime-smoke: Dex species=%u "
                    "national=%u/%u inverse=%u/%u\n",
                    species, actual_national, national,
                    actual_inverse, inverse);
            battle_core_die("canonical National Dex conversion differs");
        }
    }
    uint32_t front = read32(core, FRONT_TABLE_POINTER);
    if (read32(core, front + SPECIES_RUNTIME_EGG * 8U)
        == read32(core, front + SPECIES_RUNTIME_CATERPIE * 8U)) {
        battle_core_die("Egg and Caterpie front pictures collide");
    }
    printf(
        "{\"status\":\"PASS\",\"species_created\":%u,"
        "\"species_named\":%u,\"species_with_level5_moves\":%u,"
        "\"display_species_checked\":%zu,\"egg_species\":%u,"
        "\"dex_species_checked\":%zu,"
        "\"caterpie_species\":%u,\"canonical_species_count\":%u}\n",
        created, named, with_moves, ARRAY_LEN(display_samples),
        SPECIES_RUNTIME_EGG, ARRAY_LEN(dex_samples), SPECIES_RUNTIME_CATERPIE,
        SPECIES_RUNTIME_COUNT
    );
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
