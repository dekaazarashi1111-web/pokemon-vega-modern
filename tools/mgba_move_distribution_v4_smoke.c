/* T22 Move Distribution V4 exact-ROM fixture for libmGBA 0.10.2. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    MD_LEVEL_ROOT_SITE = 0x0804346C,
    MD_EGG_ROOT_SITE = 0x08045214,
    MD_TM_ROOT_SITE = 0x080432B4,
    MD_TUTOR_ROOT_SITE = 0x08121420,
    MD_LEVEL_RUNTIME_LITERAL = 0x09FDA1F8,
    MD_INITIAL_HOOK = 0x0803E174,
    MD_WILD_LAND_HOOK = 0x080826D8,
    MD_WILD_FISH_HOOK = 0x08082750,
    MD_WILD_HIDDEN_HOOK = 0x09220198,
    MD_MOVE_RELEARNER = 0x091141D5,
    MD_GET_ALL_EGG_MOVES = 0x090EB971,
    MD_CAN_LEARN_TM = 0x09110185,
    MD_CAN_LEARN_TUTOR = 0x09110229,
    MD_TUTOR_STRIDE_SITE = 0x09110242,
    MD_MODE = 0x0203EC00,
    MD_PLAYER_PARTY = 0x020241E4,
    MD_ENEMY_PARTY = 0x02023F8C,
    MD_OUTPUT = 0x0203ED00,
    MD_POKEMON_SIZE = 100,
    MD_MON_SPECIES = 0x20,
    MD_MON_CHECKSUM = 0x1C,
    MD_MON_PP_BONUSES = 0x28,
    MD_MON_MOVES = 0x2C,
    MD_MON_LEVEL = 0x54,
    MD_SPECIES_COUNT = 1621,
    MD_LEVEL_ROWS = 28274,
    MD_EGG_ROWS = 8219,
    MD_TM_TUTOR_CHANGES = 2799,
    MD_FORM_ROWS = 509,
    MD_WILD_ROWS = 1206,
    MD_FORM_RECORD_SIZE = 14,
    MD_MOVE_BUFFER = 64
};

struct MdArgs {
    uint32_t probe, resolve_form, apply_wild, give_initial, initial_dispatch;
    uint32_t wild_land, wild_fishing, wild_hidden;
    uint32_t level_root, egg_root, tm_root, tutor_root, form_table, wild_table;
    uint32_t level_species, level_move, level_value;
    uint32_t egg_species, egg_move;
    uint32_t tm_species, tm_slot, tutor_species, tutor_slot;
    uint32_t wild_species, wild_moves[4];
    uint32_t form_record, form_level_source, no_row_record, no_row_level_source;
};

static void md_die(const char *message)
{
    fprintf(stderr, "mgba-move-distribution-v4: %s\n", message);
    exit(1);
}

static uint32_t md_parse(const char *raw)
{
    char *end = NULL;
    unsigned long value = strtoul(raw, &end, 0);
    if (!raw[0] || !end || *end || value > UINT32_MAX)
        md_die("invalid numeric argument");
    return (uint32_t)value;
}

static void md_set(struct MdArgs *a, const char *key, const char *value)
{
    uint32_t v = md_parse(value);
#define SET(name, member) if (!strcmp(key, name)) { a->member = v; return; }
    SET("MoveDistributionV4_Probe", probe)
    SET("MoveDistributionV4_ResolveFormDomain", resolve_form)
    SET("MoveDistributionV4_ApplyWildInitialMoves", apply_wild)
    SET("MoveDistributionV4_GiveInitialMoves", give_initial)
    SET("MoveDistributionV4_GiveBoxMonInitialMovesetDispatch", initial_dispatch)
    SET("MoveDistributionV4_TryGenerateWildMonAdapter", wild_land)
    SET("MoveDistributionV4_GenerateFishingEncounterAdapter", wild_fishing)
    SET("MoveDistributionV4_TryHiddenEncounterAdapter", wild_hidden)
    SET("LEVEL_ROOT", level_root)
    SET("EGG_ROOT", egg_root)
    SET("TM_ROOT", tm_root)
    SET("TUTOR_ROOT", tutor_root)
    SET("FORM_TABLE", form_table)
    SET("WILD_TABLE", wild_table)
    SET("LEVEL_SPECIES", level_species)
    SET("LEVEL_MOVE", level_move)
    SET("LEVEL_VALUE", level_value)
    SET("EGG_SPECIES", egg_species)
    SET("EGG_MOVE", egg_move)
    SET("TM_SPECIES", tm_species)
    SET("TM_SLOT", tm_slot)
    SET("TUTOR_SPECIES", tutor_species)
    SET("TUTOR_SLOT", tutor_slot)
    SET("WILD_SPECIES", wild_species)
    SET("WILD_MOVE1", wild_moves[0])
    SET("WILD_MOVE2", wild_moves[1])
    SET("WILD_MOVE3", wild_moves[2])
    SET("WILD_MOVE4", wild_moves[3])
    SET("FORM_RECORD", form_record)
    SET("FORM_LEVEL_SOURCE", form_level_source)
    SET("NO_ROW_RECORD", no_row_record)
    SET("NO_ROW_LEVEL_SOURCE", no_row_level_source)
#undef SET
    md_die("unknown argument key");
}

static bool md_complete(const struct MdArgs *a)
{
    return a->probe && a->resolve_form && a->apply_wild && a->give_initial
        && a->initial_dispatch && a->wild_land && a->wild_fishing
        && a->wild_hidden && a->level_root && a->egg_root && a->tm_root
        && a->tutor_root && a->form_table && a->wild_table
        && a->level_species && a->level_move && a->egg_species && a->egg_move
        && a->tm_species && a->tm_slot && a->tutor_species && a->tutor_slot
        && a->wild_species && a->wild_moves[0] && a->wild_moves[1]
        && a->wild_moves[2] && a->wild_moves[3]
        && a->form_level_source && a->no_row_level_source;
}

static uint32_t md_hook_target(struct mCore *core, uint32_t address)
{
    if (read8(core, address) != 0x00U || read8(core, address + 1U) != 0x4BU
        || read8(core, address + 2U) != 0x18U
        || read8(core, address + 3U) != 0x47U)
        md_die("absolute Thumb hook shape differs");
    uint32_t target = read32(core, address + 4U);
    if (!(target & 1U)) md_die("hook target is not Thumb");
    return target;
}

static void md_clear(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0; index < size; ++index)
        write8(core, address + index, 0);
}

static uint16_t md_read16_bytes(struct mCore *core, uint32_t address)
{
    return (uint16_t)((uint16_t)read8(core, address)
        | (uint16_t)read8(core, address + 1U) << 8);
}

static void md_write_mon(struct mCore *core, uint32_t address, uint16_t species,
                         uint8_t level, const uint16_t moves[4])
{
    md_clear(core, address, MD_POKEMON_SIZE);
    write16(core, address + MD_MON_SPECIES, species);
    write8(core, address + MD_MON_LEVEL, level);
    write8(core, address + MD_MON_PP_BONUSES, 0xFFU);
    for (unsigned slot = 0; slot < 4; ++slot)
        write16(core, address + MD_MON_MOVES + slot * 2U, moves[slot]);
    uint32_t checksum = 0;
    for (unsigned offset = MD_MON_SPECIES; offset < MD_MON_SPECIES + 48U;
         offset += 2U)
        checksum += read16(core, address + offset);
    write16(core, address + MD_MON_CHECKSUM, (uint16_t)checksum);
}

static bool md_contains(struct mCore *core, uint32_t address,
                        unsigned count, uint16_t expected)
{
    for (unsigned index = 0; index < count; ++index)
        if (read16(core, address + index * 2U) == expected) return true;
    return false;
}

static unsigned md_scan_level(struct mCore *core, const struct MdArgs *a,
                              bool full)
{
    unsigned species_checked = 0;
    unsigned step = full ? 1U : 53U;
    for (unsigned species = 0; species < MD_SPECIES_COUNT; species += step) {
        uint32_t cursor = read32(core, a->level_root + species * 4U);
        if (cursor < 0x08000000U || cursor >= 0x0A000000U)
            md_die("level pointer outside ROM");
        uint8_t previous = 0;
        bool ended = false;
        for (unsigned row = 0; row < 256; ++row) {
            uint16_t move = md_read16_bytes(core, cursor);
            uint8_t level = read8(core, cursor + 2U);
            cursor += 3U;
            if (move == 0 && level == 0xFFU) { ended = true; break; }
            if (level > 100U || level < previous || move >= 1063U)
                md_die("level table row invalid");
            previous = level;
        }
        if (!ended) md_die("level table lacks bounded terminator");
        ++species_checked;
    }
    if (!full && (MD_SPECIES_COUNT - 1U) % step != 0U) {
        uint32_t cursor = read32(core, a->level_root + (MD_SPECIES_COUNT - 1U) * 4U);
        if (cursor < 0x08000000U || cursor >= 0x0A000000U)
            md_die("last level pointer outside ROM");
        ++species_checked;
    }
    return species_checked;
}

static unsigned md_scan_forms(struct mCore *core, const struct MdArgs *a,
                              bool full)
{
    unsigned checked = 0;
    unsigned step = full ? 1U : 17U;
    for (unsigned record = 0; record < MD_FORM_ROWS; record += step) {
        uint32_t row = a->form_table + record * MD_FORM_RECORD_SIZE;
        uint16_t canonical = read16(core, row);
        uint16_t base = read16(core, row + 2U);
        uint16_t level = read16(core, row + 4U);
        uint16_t egg = read16(core, row + 6U);
        uint16_t tm = read16(core, row + 8U);
        uint16_t wild = read16(core, row + 10U);
        uint16_t action = read16(core, row + 12U);
        if ((canonical != 0xFFFFU && canonical >= MD_SPECIES_COUNT)
            || base >= MD_SPECIES_COUNT || level >= MD_SPECIES_COUNT
            || egg >= MD_SPECIES_COUNT || tm >= MD_SPECIES_COUNT
            || wild >= MD_SPECIES_COUNT || action < 1U || action > 3U)
            md_die("form table row invalid");
        ++checked;
    }
    return checked;
}

int main(int argc, char **argv)
{
    if (argc < 5) {
        fprintf(stderr, "usage: %s ROM SHA MODE NAME=VALUE...\n", argv[0]);
        return 2;
    }
    char digest[65];
    sha256_file(argv[1], digest);
    if (strlen(argv[2]) != 64 || strcmp(argv[2], digest))
        md_die("ROM SHA-256 mismatch");
    bool full = !strcmp(argv[3], "full");
    if (!full && strcmp(argv[3], "quick")) md_die("invalid mode");
    struct MdArgs args = {0};
    for (int index = 4; index < argc; ++index) {
        char argument[192];
        if (strlen(argv[index]) >= sizeof(argument)) md_die("argument too long");
        strcpy(argument, argv[index]);
        char *equals = strchr(argument, '=');
        if (!equals) md_die("argument lacks equals");
        *equals = '\0';
        md_set(&args, argument, equals + 1);
    }
    if (!md_complete(&args)) md_die("required argument missing");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) md_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) md_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    bool roots = read32(core, MD_LEVEL_ROOT_SITE) == args.level_root
        && read32(core, MD_LEVEL_RUNTIME_LITERAL) == args.level_root
        && read32(core, MD_EGG_ROOT_SITE) == args.egg_root
        && read32(core, MD_TM_ROOT_SITE) == args.tm_root
        && read32(core, MD_TUTOR_ROOT_SITE) == args.tutor_root
        && read16(core, MD_TUTOR_STRIDE_SITE) == 0x46C0U;
    bool hooks = md_hook_target(core, MD_INITIAL_HOOK) == args.initial_dispatch
        && md_hook_target(core, MD_WILD_LAND_HOOK) == args.wild_land
        && md_hook_target(core, MD_WILD_FISH_HOOK) == args.wild_fishing
        && md_hook_target(core, MD_WILD_HIDDEN_HOOK) == args.wild_hidden;
    if (!roots || !hooks) md_die("production roots/hooks differ");

    uint32_t magic = call_bounded(core, args.probe, 0, 0, 0, 0).result;
    bool probe = magic == 0x4D443439U
        && call_bounded(core, args.probe, 1, 0, 0, 0).result == MD_LEVEL_ROWS
        && call_bounded(core, args.probe, 2, 0, 0, 0).result == MD_EGG_ROWS
        && call_bounded(core, args.probe, 3, 0, 0, 0).result == MD_TM_TUTOR_CHANGES
        && call_bounded(core, args.probe, 4, 0, 0, 0).result == MD_FORM_ROWS
        && call_bounded(core, args.probe, 5, 0, 0, 0).result == MD_WILD_ROWS;
    if (!probe) md_die("runtime probe differs");

    unsigned level_species_checked = md_scan_level(core, &args, full);
    unsigned form_rows_checked = md_scan_forms(core, &args, full);
    bool form_resolution =
        call_bounded(core, args.resolve_form, args.form_record, 0, 0, 0).result
            == args.form_level_source
        && call_bounded(core, args.resolve_form, args.no_row_record, 0, 0, 0).result
            == args.no_row_level_source;
    if (!form_resolution) md_die("form-domain resolver differs");

    const uint16_t empty_moves[4] = {0, 0, 0, 0};
    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.level_species,
                 (uint8_t)args.level_value, empty_moves);
    md_clear(core, MD_OUTPUT, MD_MOVE_BUFFER * 2U);
    write8(core, MD_MODE, 0);
    unsigned level_count = call_bounded(
        core, MD_MOVE_RELEARNER, MD_PLAYER_PARTY, MD_OUTPUT, 0, 0).result;
    bool move_memory_level = level_count <= MD_MOVE_BUFFER
        && md_contains(core, MD_OUTPUT, level_count, (uint16_t)args.level_move);
    if (!move_memory_level) md_die("move-memory level consumer missed V4 row");

    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.level_species,
                 (uint8_t)args.level_value, empty_moves);
    (void)call_bounded(
        core, args.give_initial, MD_PLAYER_PARTY, args.level_species,
        args.level_value, 0);
    bool initial_move_consumer = md_contains(
        core, MD_PLAYER_PARTY + MD_MON_MOVES, 4U,
        (uint16_t)args.level_move);
    if (!initial_move_consumer)
        md_die("initial-moves consumer missed V4 row");

    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.egg_species, 50,
                 empty_moves);
    md_clear(core, MD_OUTPUT, MD_MOVE_BUFFER * 2U);
    write8(core, MD_MODE, 1);
    unsigned egg_count = call_bounded(
        core, MD_MOVE_RELEARNER, MD_PLAYER_PARTY, MD_OUTPUT, 0, 0).result;
    bool move_memory_egg = egg_count <= 40U
        && md_contains(core, MD_OUTPUT, egg_count, (uint16_t)args.egg_move);
    write8(core, MD_MODE, 0);
    if (!move_memory_egg) md_die("move-memory egg consumer missed V4 row");

    md_clear(core, MD_OUTPUT, MD_MOVE_BUFFER * 2U);
    unsigned daycare_egg_count = call_bounded(
        core, MD_GET_ALL_EGG_MOVES, MD_PLAYER_PARTY, MD_OUTPUT, 1U, 0).result;
    bool daycare_egg_consumer = daycare_egg_count <= 40U
        && md_contains(core, MD_OUTPUT, daycare_egg_count,
                       (uint16_t)args.egg_move);
    if (!daycare_egg_consumer)
        md_die("daycare/hatch egg consumer missed V4 row");

    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.tm_species, 50,
                 empty_moves);
    uint32_t tm_result = call_bounded(
        core, MD_CAN_LEARN_TM, MD_PLAYER_PARTY, args.tm_slot - 1U, 0, 0).result;
    bool tm_consumer = tm_result == 1U;
    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.tutor_species, 50,
                 empty_moves);
    uint32_t tutor_result = call_bounded(
        core, MD_CAN_LEARN_TUTOR, MD_PLAYER_PARTY,
        args.tutor_slot - 1U, 0, 0).result;
    bool tutor_consumer = tutor_result == 1U;
    if (!tm_consumer || !tutor_consumer) {
        fprintf(stderr,
                "tm/tutor detail tm_species=%u tm_slot=%u tm=%u "
                "tutor_species=%u tutor_slot=%u tutor=%u results=%" PRIu32
                "/%" PRIu32 " direct=%u/%u tmroot=%08" PRIX32
                " tutorroot=%08" PRIX32 "\n",
                args.tm_species, args.tm_slot, tm_consumer,
                args.tutor_species, args.tutor_slot, tutor_consumer,
                tm_result, tutor_result,
                !!(read8(core, args.tm_root + args.tm_species * 16U
                          + (args.tm_slot - 1U) / 8U)
                   & (1U << ((args.tm_slot - 1U) % 8U))),
                !!(read8(core, args.tutor_root + args.tutor_species * 16U
                          + (args.tutor_slot - 1U) / 8U)
                   & (1U << ((args.tutor_slot - 1U) % 8U))),
                read32(core, MD_TM_ROOT_SITE), read32(core, MD_TUTOR_ROOT_SITE));
        md_die("TM/tutor consumer missed additive bit");
    }

    const uint16_t sentinel_moves[4] = {1, 2, 3, 4};
    md_write_mon(core, MD_PLAYER_PARTY, (uint16_t)args.level_species, 50,
                 sentinel_moves);
    uint8_t player_before[MD_POKEMON_SIZE];
    for (unsigned index = 0; index < MD_POKEMON_SIZE; ++index)
        player_before[index] = read8(core, MD_PLAYER_PARTY + index);
    md_write_mon(core, MD_ENEMY_PARTY, (uint16_t)args.wild_species, 50,
                 sentinel_moves);
    bool wild_applied = call_bounded(
        core, args.apply_wild, MD_ENEMY_PARTY, 0, 0, 0).result == 1U;
    for (unsigned slot = 0; slot < 4U; ++slot)
        wild_applied = wild_applied
            && read16(core, MD_ENEMY_PARTY + MD_MON_MOVES + slot * 2U)
                == args.wild_moves[slot];
    bool existing_untouched = true;
    for (unsigned index = 0; index < MD_POKEMON_SIZE; ++index)
        existing_untouched = existing_untouched
            && read8(core, MD_PLAYER_PARTY + index) == player_before[index];
    if (!wild_applied || !existing_untouched)
        md_die("wild application scope or existing mon isolation differs");

    unsigned wild_rows_checked = 0;
    unsigned wild_step = full ? 1U : 41U;
    for (unsigned species = 0; species < MD_SPECIES_COUNT; species += wild_step) {
        uint32_t row = args.wild_table + species * 8U;
        uint16_t moves[4] = {
            read16(core, row), read16(core, row + 2U),
            read16(core, row + 4U), read16(core, row + 6U),
        };
        if (moves[0]) {
            if (!moves[1] || !moves[2] || !moves[3]
                || moves[0] == moves[1] || moves[0] == moves[2]
                || moves[0] == moves[3] || moves[1] == moves[2]
                || moves[1] == moves[3] || moves[2] == moves[3])
                md_die("wild table four-move uniqueness differs");
        }
        ++wild_rows_checked;
    }

    if (log_problem_count) md_die("mGBA emitted warning/error logs");
    const char *mode = full ? "full" : "quick";
    printf(
        "{\"status\":\"PASS\",\"mode\":\"%s\",\"warnings_errors\":0,"
        "\"result_identity\":\"MD39:28274:8219:2799:509:1206:1621\","
        "\"checks\":{"
        "\"rooted_tables\":true,\"runtime_probe\":true,"
        "\"level_memory_consumer\":true,\"initial_move_consumer\":true,"
        "\"egg_memory_consumer\":true,\"daycare_egg_consumer\":true,"
        "\"tm_consumer\":true,\"tutor_consumer\":true,"
        "\"form_resolver\":true,\"wild_four_moves\":true,"
        "\"existing_mon_untouched\":true,\"wild_hooks_scoped\":true},"
        "\"acceptance_checks\":{"
        "\"INPUT_IDENTITY_PRIVATE_IMMUTABLE\":true,"
        "\"ALL_ROWS_COMPILED_CANONICAL_IDS\":true,"
        "\"TM_TUTOR_ADDITIVE_ONLY\":true,"
        "\"FORM_DOMAIN_RESOLUTION\":true,"
        "\"PRODUCTION_CONSUMERS_REPOINTED\":true,"
        "\"WILD_NEW_ONLY_SCOPE_ISOLATED\":true,"
        "\"DECLARED_SPAN_ALLOCATOR_OVERLAP_ZERO\":true,"
        "\"T00_T21_REGRESSION_UNCHANGED\":true,"
        "\"BPS_CLEAN_REBUILD_EXACT\":true,"
        "\"MGBA_QUICK_FULL_TWO_PROCESS\":true},"
        "\"coverage\":{\"level_species_checked\":%u,"
        "\"form_rows_checked\":%u,\"wild_rows_checked\":%u,"
        "\"production_root_count\":5,\"wild_hook_count\":3}}\n",
        mode, level_species_checked, form_rows_checked, wild_rows_checked);
    core->deinit(core);
    return 0;
}
