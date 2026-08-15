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
    STRING_COPY = 0x08008901,
    STRING_APPEND = 0x08008921,
    STRING_COPY_PADDED = 0x08008DAD,
    STRING_GET_END_10 = 0x080088A5,
    UPDATE_NICK_IN_HEALTHBOX = 0x08048CC1,
    BUFFER_STRING_BATTLE = 0x090D2031,
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
    NAME_COMPAT_POINTER = 0x08000144,
    NAME_COMPAT_STRIDE = 8,
    NAME_MAX_GLYPHS = 6,
    DISPLAYED_BATTLE_STRING = 0x020228FC,
    HEALTHBOX_SPRITE_IDS = 0x03005030,
    SPRITES = 0x020205B8,
    SPRITE_SIZE = 68,
    OBJ_VRAM = 0x06010000,
    MON_DATA_NICKNAME = 2,
    PIC_SCRATCH = 0x0203A000,
    PIC_EXPECTED = 0x0203A800,
    PIC_SIZE = 2048,
};

static void clear_runtime_bytes(struct mCore *core, uint32_t address,
                                unsigned size);

static unsigned runtime_string_length(struct mCore *core, uint32_t address,
                                      unsigned bound)
{
    for (unsigned index = 0; index < bound; ++index) {
        if (read8(core, address + index) == 0xFFU) return index;
    }
    battle_core_die("bounded Species name is unterminated");
    return 0;
}

static void require_runtime_name(struct mCore *core, uint32_t address,
                                 const uint8_t *expected, unsigned length,
                                 const char *label)
{
    for (unsigned index = 0; index < length; ++index) {
        if (read8(core, address + index) != expected[index]) {
            fprintf(stderr,
                    "mgba-species-runtime-smoke: %s differs at %u\n",
                    label, index);
            exit(1);
        }
    }
    if (read8(core, address + length) != 0xFFU)
        battle_core_die("Species name EOS differs");
}

static void verify_stock_string_routes(struct mCore *core, uint16_t species,
                                       const uint8_t *expected)
{
    uint32_t compatibility = read32(core, NAME_COMPAT_POINTER)
        + (uint32_t)species * NAME_COMPAT_STRIDE;
    uint32_t destination = NAME_SCRATCH + 4U;

    clear_runtime_bytes(core, NAME_SCRATCH, 32);
    (void)call_preserving(core, STRING_COPY,
                          destination, compatibility, 0, 0);
    require_runtime_name(core, destination, expected, NAME_MAX_GLYPHS,
                         "stock StringCopy");
    for (unsigned index = 0; index < 4; ++index) {
        if (read8(core, NAME_SCRATCH + index) != 0xA5U
            || read8(core, destination + 7U + index) != 0xA5U)
            battle_core_die("stock StringCopy crossed its canary");
    }

    clear_runtime_bytes(core, NAME_SCRATCH, 32);
    (void)call_preserving(core, STRING_COPY_PADDED,
                          destination, compatibility, 0, NAME_MAX_GLYPHS);
    require_runtime_name(core, destination, expected, NAME_MAX_GLYPHS,
                         "PC StringCopyPadded");
    for (unsigned index = 0; index < 4; ++index) {
        if (read8(core, NAME_SCRATCH + index) != 0xA5U
            || read8(core, destination + 7U + index) != 0xA5U)
            battle_core_die("PC padded copy crossed its canary");
    }

    clear_runtime_bytes(core, NAME_SCRATCH, 32);
    write8(core, destination, 0x00U);
    write8(core, destination + 1U, 0xFFU);
    (void)call_preserving(core, STRING_APPEND,
                          destination, compatibility, 0, 0);
    if (read8(core, destination) != 0x00U)
        battle_core_die("notification prefix differs");
    require_runtime_name(core, destination + 1U, expected, NAME_MAX_GLYPHS,
                         "stock StringAppend");

    clear_runtime_bytes(core, NAME_SCRATCH, 32);
    (void)call_preserving(core, STRING_COPY,
                          destination, compatibility, 0, 0);
    (void)call_preserving(core, STRING_GET_END_10,
                          destination, 0, 0, 0);
    require_runtime_name(core, destination, expected, NAME_MAX_GLYPHS,
                         "party/summary/item StringGetEnd10");
}

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

static bool runtime_buffer_contains(struct mCore *core, uint32_t buffer,
                                    unsigned buffer_size,
                                    uint32_t source, unsigned length)
{
    for (unsigned offset = 0; offset + length <= buffer_size; ++offset) {
        bool equal = true;
        for (unsigned index = 0; index < length; ++index) {
            if (read8(core, buffer + offset + index)
                != read8(core, source + index)) {
                equal = false;
                break;
            }
        }
        if (equal) return true;
    }
    return false;
}

static uint64_t runtime_range_digest(struct mCore *core, uint32_t address,
                                     unsigned size)
{
    uint64_t digest = 1469598103934665603ULL;
    for (unsigned index = 0; index < size; ++index) {
        digest ^= read8(core, address + index);
        digest *= 1099511628211ULL;
    }
    return digest;
}

static void install_level100_name_battle(
    struct mCore *core, const struct Snapshot *field,
    uint16_t player_species, uint16_t enemy_species
) {
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_SCRATCH, 0, 0, 0,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0, 0, 0,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint8_t player[POKEMON_SIZE];
    uint8_t enemy[POKEMON_SIZE];
    restore_snapshot(core, field);
    create_mon_image(core, player_species, 100, player_moves, player_pp, player);
    create_mon_image(core, enemy_species, 100, enemy_moves, enemy_pp, enemy);
    clear_parties(core);
    seed_fixture(core);
    install_mon_image(core, ADDR_PLAYER_PARTY, player);
    install_mon_image(core, ADDR_ENEMY_PARTY, enemy);
    clear_runtime_bytes(core, NAME_SCRATCH, NAME_LENGTH);
    (void)call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                          ADDR_ENEMY_PARTY, MON_DATA_NICKNAME,
                          NAME_SCRATCH, 0);
    uint32_t expected_name = read32(core, NAME_COMPAT_POINTER)
        + (uint32_t)enemy_species * NAME_COMPAT_STRIDE;
    unsigned expected_length = runtime_string_length(
        core, expected_name, NAME_COMPAT_STRIDE);
    for (unsigned index = 0; index <= expected_length; ++index) {
        if (read8(core, NAME_SCRATCH + index)
            != read8(core, expected_name + index)) {
            battle_core_die("party nickname lacks complete Species name");
        }
    }
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1);
    struct CallObservation setup = call_bounded(
        core, BATTLE_CORE_START_WILD, 0, 0, 0, 0);
    if (!setup.payload_pc_seen)
        battle_core_die("name battle did not execute CFRU payload code");
}

static void verify_healthbox_name(
    struct mCore *core, unsigned battler, uint32_t mon,
    uint16_t species, bool prove_sixth_glyph
) {
    uint32_t compatibility = read32(core, NAME_COMPAT_POINTER)
        + (uint32_t)species * NAME_COMPAT_STRIDE;
    unsigned length = runtime_string_length(
        core, compatibility, NAME_COMPAT_STRIDE);
    uint8_t sprite_id = read8(core, HEALTHBOX_SPRITE_IDS + battler);
    if (sprite_id >= 128U)
        battle_core_die("healthbox sprite ID is outside sprite storage");
    uint32_t sprite = SPRITES + (uint32_t)sprite_id * SPRITE_SIZE;
    uint32_t tile = (uint32_t)(read16(core, sprite + 4U) & 0x03FFU);
    uint32_t name_tiles = OBJ_VRAM + tile * 32U
        + (battler & 1U ? 0x20U : 0x40U);

    (void)call_preserving(core, UPDATE_NICK_IN_HEALTHBOX,
                          sprite_id, mon, 0, 0);
    if (!runtime_buffer_contains(core, DISPLAYED_BATTLE_STRING, 96,
                                 compatibility, length))
        battle_core_die("healthbox text buffer lacks complete Species name");
    uint64_t complete_digest = runtime_range_digest(
        core, name_tiles, 15U * 32U);
    if (complete_digest == 1469598103934665603ULL)
        battle_core_die("healthbox name tiles are blank");

    if (prove_sixth_glyph) {
        clear_runtime_bytes(core, NAME_SCRATCH, NAME_LENGTH);
        for (unsigned index = 0; index <= NAME_MAX_GLYPHS; ++index)
            write8(core, NAME_SCRATCH + index,
                   read8(core, compatibility + index));
        write8(core, NAME_SCRATCH + NAME_MAX_GLYPHS - 1U,
               read8(core, compatibility));
        (void)call_preserving(core, ROM_SET_MON_DATA,
                              mon, MON_DATA_NICKNAME, NAME_SCRATCH, 0);
        clear_runtime_bytes(core, NAME_SCRATCH, NAME_LENGTH);
        (void)call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                              mon, MON_DATA_NICKNAME, NAME_SCRATCH, 0);
        if (runtime_string_length(core, NAME_SCRATCH, NAME_LENGTH)
                != NAME_MAX_GLYPHS
            || read8(core, NAME_SCRATCH + NAME_MAX_GLYPHS - 1U)
                != read8(core, compatibility))
            battle_core_die("sixth-glyph healthbox mutation readback differs");
        (void)call_preserving(core, UPDATE_NICK_IN_HEALTHBOX,
                              sprite_id, mon, 0, 0);
        uint64_t mutated_digest = runtime_range_digest(
            core, name_tiles, 15U * 32U);
        if (mutated_digest == complete_digest)
            battle_core_die("sixth Species glyph did not affect healthbox tiles");

        (void)call_preserving(core, ROM_SET_MON_DATA,
                              mon, MON_DATA_NICKNAME, compatibility, 0);
        (void)call_preserving(core, UPDATE_NICK_IN_HEALTHBOX,
                              sprite_id, mon, 0, 0);
        if (runtime_range_digest(core, name_tiles, 15U * 32U)
            != complete_digest)
            battle_core_die("complete healthbox name did not restore exactly");
    }
}

static void verify_battle_name_surface(
    struct mCore *core, const struct Snapshot *field,
    uint16_t player_species, uint16_t enemy_species
) {
    uint32_t enemy_name = read32(core, NAME_COMPAT_POINTER)
        + (uint32_t)enemy_species * NAME_COMPAT_STRIDE;
    unsigned enemy_length = runtime_string_length(
        core, enemy_name, NAME_COMPAT_STRIDE);
    install_level100_name_battle(
        core, field, player_species, enemy_species);
    run_fixed_frames(core);
    (void)call_preserving(core, BUFFER_STRING_BATTLE, 0, 0, 0, 0);
    if (!runtime_buffer_contains(
            core, DISPLAYED_BATTLE_STRING, 96,
            enemy_name, enemy_length)) {
        fprintf(stderr, "mgba-species-runtime-smoke: message=");
        for (unsigned index = 0; index < 96; ++index)
            fprintf(stderr, "%02x", read8(core, DISPLAYED_BATTLE_STRING + index));
        fprintf(stderr, " battle-nick=");
        for (unsigned index = 0; index < 8; ++index)
            fprintf(stderr, "%02x", read8(core, ADDR_BATTLE_MONS
                                           + BATTLE_MON_SIZE + 0x30U + index));
        fprintf(stderr, " expected=");
        for (unsigned index = 0; index < enemy_length; ++index)
            fprintf(stderr, "%02x", read8(core, enemy_name + index));
        fputc('\n', stderr);
        battle_core_die("wild battle message lacks complete six-glyph name");
    }
    if (read16(core, ADDR_BATTLE_MONS) != player_species
        || read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE) != enemy_species
        || read8(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_LEVEL) != 100U
        || read8(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                 + BATTLE_CORE_MON_LEVEL) != 100U) {
        battle_core_die("Lv.100 form/name battle identity differs");
    }
    verify_healthbox_name(core, 0, ADDR_PLAYER_PARTY,
                          player_species, false);
    verify_healthbox_name(core, 1, ADDR_ENEMY_PARTY,
                          enemy_species, true);
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
    struct Snapshot field = take_snapshot(core);

    unsigned created = 0;
    unsigned named = 0;
    unsigned with_moves = 0;
    unsigned compatibility_checked = 0;
    unsigned six_glyph_names = 0;
    uint32_t compatibility_root = read32(core, NAME_COMPAT_POINTER);
    if (compatibility_root < 0x08000000U
        || compatibility_root >= 0x0A000000U) {
        battle_core_die("compatibility Species name root is outside ROM");
    }
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

        clear_runtime_bytes(core, NAME_SCRATCH - 4U, NAME_LENGTH + 8U);
        (void)call_preserving(core, GET_SPECIES_NAME,
                              NAME_SCRATCH, species, 0, 0);
        unsigned visible = runtime_string_length(core, NAME_SCRATCH, NAME_LENGTH);
        if (visible == 0 || visible > NAME_MAX_GLYPHS) {
            battle_core_die("canonical Species name visible length differs");
        }
        for (unsigned index = 0; index < 4U; ++index) {
            if (read8(core, NAME_SCRATCH - 4U + index) != 0xA5U
                || read8(core, NAME_SCRATCH + NAME_LENGTH + index) != 0xA5U) {
                battle_core_die("canonical GetSpeciesName crossed its canary");
            }
        }
        uint32_t compatibility = compatibility_root
            + (uint32_t)species * NAME_COMPAT_STRIDE;
        for (unsigned index = 0; index <= visible; ++index) {
            if (read8(core, compatibility + index)
                != read8(core, NAME_SCRATCH + index)) {
                battle_core_die("compatibility/canonical Species name differs");
            }
        }
        for (unsigned index = visible + 1U;
             index < NAME_COMPAT_STRIDE; ++index) {
            if (read8(core, compatibility + index) != 0xFFU)
                battle_core_die("compatibility Species name padding differs");
        }
        six_glyph_names += visible == NAME_MAX_GLYPHS;
        ++compatibility_checked;
        ++named;
    }
    if (six_glyph_names != 134U)
        battle_core_die("six-glyph Species name count differs");

    static const uint8_t cinderace_name[] = {
        0x54, 0xAE, 0x5D, 0x96, 0xAE, 0x7E,
    };
    static const uint8_t eternatus_name[] = {
        0x71, 0x8A, 0x7E, 0x91, 0x52, 0x65,
    };
    const struct {
        uint16_t species;
        const uint8_t *name;
    } six_glyph_canaries[] = {
        {1288, cinderace_name},
        {1363, eternatus_name},
    };
    for (unsigned index = 0; index < ARRAY_LEN(six_glyph_canaries); ++index) {
        clear_runtime_bytes(core, NAME_SCRATCH, NAME_LENGTH + 4U);
        (void)call_preserving(core, GET_SPECIES_NAME, NAME_SCRATCH,
                              six_glyph_canaries[index].species, 0, 0);
        require_runtime_name(core, NAME_SCRATCH,
                             six_glyph_canaries[index].name,
                             NAME_MAX_GLYPHS, "canonical six-glyph canary");
        verify_stock_string_routes(core, six_glyph_canaries[index].species,
                                   six_glyph_canaries[index].name);
    }

    const uint16_t form_name_pairs[][2] = {
        {420, 1055},  /* Pidgeot / Mega Pidgeot */
        {65, 1058},   /* Gengar / Mega Gengar */
        {65, 1448},   /* Gengar / Gigantamax Gengar */
    };
    for (unsigned pair = 0; pair < ARRAY_LEN(form_name_pairs); ++pair) {
        uint32_t base = compatibility_root
            + (uint32_t)form_name_pairs[pair][0] * NAME_COMPAT_STRIDE;
        uint32_t form = compatibility_root
            + (uint32_t)form_name_pairs[pair][1] * NAME_COMPAT_STRIDE;
        require_equal_runtime_bytes(core, base, form, NAME_COMPAT_STRIDE,
                                    "form base Species name");
    }
    const uint16_t display_samples[] = {
        SPECIES_RUNTIME_EGG,
        SPECIES_RUNTIME_PIDGEY,
        SPECIES_RUNTIME_CATERPIE,
        SPECIES_RUNTIME_LECHONK,
        1055, /* Mega Pidgeot */
        1448, /* Gigantamax Gengar */
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
    verify_battle_name_surface(core, &field, 1055, 1288);
    verify_battle_name_surface(core, &field, 1448, 1363);
    printf(
        "{\"status\":\"PASS\",\"species_created\":%u,"
        "\"species_named\":%u,\"species_with_level5_moves\":%u,"
        "\"compatibility_names_checked\":%u,"
        "\"six_glyph_names\":%u,\"buffer_canaries\":true,"
        "\"stock_string_routes\":4,\"surface_name_routes\":7,"
        "\"form_base_names_checked\":%zu,"
        "\"battle_name_cases\":2,\"battle_messages\":2,"
        "\"healthbox_tile_cases\":2,\"level100_form_cases\":2,"
        "\"display_species_checked\":%zu,\"egg_species\":%u,"
        "\"dex_species_checked\":%zu,"
        "\"caterpie_species\":%u,\"canonical_species_count\":%u}\n",
        created, named, with_moves, compatibility_checked, six_glyph_names,
        ARRAY_LEN(form_name_pairs), ARRAY_LEN(display_samples),
        SPECIES_RUNTIME_EGG, ARRAY_LEN(dex_samples), SPECIES_RUNTIME_CATERPIE,
        SPECIES_RUNTIME_COUNT
    );
    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
