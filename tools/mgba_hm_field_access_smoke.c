/*
 * USER-20260814-HM-FIELD-ACCESS exact-ROM fixture for libmGBA 0.10.2.
 *
 * The runner boots the reviewed natural field snapshot and calls the physically
 * bound CFRU field capability entry.  It varies HM ownership, party contents,
 * learned moves, and Surf state without writing a move into a Pokemon.
 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

enum {
    HM_FIELD_CAPABILITY = 0x0911F749,
    HM_FIELD_CALLBACK_TABLE = 0x09168F9C,
    HM_FIELD_PLAYER_AVATAR_FLAGS = 0x02036FAC,
    HM_FIELD_SHOULD_NOT_BE_SURFING = 1,
    HM_FIELD_SHOULD_BE_SURFING = 2,
};

struct HMCase {
    const char *name;
    uint16_t move;
    uint16_t item;
    unsigned callback_index;
    uint32_t original_callback;
};

static const struct HMCase HM_CASES[] = {
    {"HM01_CUT", 15, 339, 1, 0x080972C5},
    {"HM02_FLY", 19, 340, 2, 0x0912083D},
    {"HM03_SURF", 57, 341, 4, 0x091208F5},
    {"HM04_STRENGTH", 70, 342, 3, 0x080D18AD},
    {"HM05_FLASH", 148, 343, 0, 0x080CACF9},
    {"HM06_ROCK_SMASH", 249, 344, 5, 0x080CABA5},
    {"HM07_WATERFALL", 127, 345, 6, 0x09120879},
    {"HM08_DIVE", 291, 346, 14, 0x09120951},
};

enum HMPartyKind {
    HM_PARTY_EMPTY,
    HM_PARTY_UNLEARNED,
    HM_PARTY_LEARNED,
    HM_PARTY_KIND_COUNT,
};

static const char *const HM_PARTY_NAMES[] = {
    "EMPTY",
    "UNLEARNED",
    "LEARNED",
};

struct HMObservation {
    uint32_t before;
    uint32_t after;
    uint32_t after_restore;
    uint32_t add_result;
    uint32_t bag_count;
    bool payload_seen;
};

struct HMCallbackObservation {
    uint32_t missing_result;
    uint32_t owned_result;
    uint32_t original_result;
    uint32_t wrapper;
};

static void hm_die(const char *message)
{
    fprintf(stderr, "mgba-hm-field-access-smoke: %s\n", message);
    exit(1);
}

static void install_party_variant(
    struct mCore *core,
    enum HMPartyKind kind,
    uint16_t move
)
{
    static const uint8_t pp[BATTLE_CORE_MOVE_SLOTS] = {35, 0, 0, 0};
    uint16_t moves[BATTLE_CORE_MOVE_SLOTS] = {0, 0, 0, 0};
    uint8_t mon[POKEMON_SIZE];

    clear_parties(core);
    if (kind == HM_PARTY_EMPTY)
        return;
    if (kind == HM_PARTY_LEARNED)
        moves[0] = move;
    create_mon_image(core, 1, 25, moves, pp, mon);
    install_mon_image(core, ADDR_PLAYER_PARTY, mon);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 1);
}

static struct HMObservation observe_capability(
    struct mCore *core,
    const struct Snapshot *field,
    const struct HMCase *fixture,
    enum HMPartyKind kind
)
{
    struct HMObservation result = {0};
    struct Snapshot owned;

    restore_snapshot(core, field);
    install_party_variant(core, kind, fixture->move);
    struct CallObservation before = call_bounded(
        core, HM_FIELD_CAPABILITY, fixture->move, 0xFFFF, 0, 0);
    result.before = before.result;
    result.payload_seen = before.payload_pc_seen;
    struct CallObservation add = call_bounded(
        core, BATTLE_CORE_ADD_BAG_ITEM, fixture->item, 1, 0, 0);
    result.add_result = add.result;
    result.bag_count = call_bounded(
        core, BATTLE_CORE_CHECK_BAG_HAS_ITEM, fixture->item, 1, 0, 0).result;
    result.after = call_bounded(
        core, HM_FIELD_CAPABILITY, fixture->move, 0xFFFF, 0, 0).result;

    owned = take_snapshot(core);
    write8(core, ADDR_PLAYER_PARTY_COUNT, 6);
    write8(core, HM_FIELD_PLAYER_AVATAR_FLAGS,
           (uint8_t)(read8(core, HM_FIELD_PLAYER_AVATAR_FLAGS) ^ 8U));
    restore_snapshot(core, &owned);
    result.after_restore = call_bounded(
        core, HM_FIELD_CAPABILITY, fixture->move, 0, 0, 0).result;
    free(owned.bytes);

    if (result.before != 6 || result.add_result == 0 || result.bag_count == 0
        || result.after != 0 || result.after_restore != 0
        || !result.payload_seen) {
        hm_die("HM ownership/party/save-derived capability contract failed");
    }
    return result;
}

static struct HMCallbackObservation observe_callback(
    struct mCore *core,
    const struct Snapshot *field,
    const struct HMCase *fixture
)
{
    struct HMCallbackObservation result = {0};
    result.wrapper = read32(
        core, HM_FIELD_CALLBACK_TABLE + fixture->callback_index * 8U);
    if (!(result.wrapper & 1U) || result.wrapper == fixture->original_callback)
        hm_die("field callback table was not routed through HM ownership guard");

    restore_snapshot(core, field);
    result.missing_result = call_bounded(core, result.wrapper, 0, 0, 0, 0).result;
    if (result.missing_result != 0)
        hm_die("field callback accepted a missing HM");

    restore_snapshot(core, field);
    if (call_bounded(core, BATTLE_CORE_ADD_BAG_ITEM,
                     fixture->item, 1, 0, 0).result == 0) {
        hm_die("failed to add HM for callback fixture");
    }
    result.owned_result = call_bounded(core, result.wrapper, 0, 0, 0, 0).result;

    restore_snapshot(core, field);
    result.original_result = call_bounded(
        core, fixture->original_callback, 0, 0, 0, 0).result;
    if (result.owned_result != result.original_result)
        hm_die("owned HM callback no longer preserves original map/terrain gate");
    return result;
}

static void observe_surf_boundaries(
    struct mCore *core,
    const struct Snapshot *field,
    uint32_t results[4]
)
{
    const struct HMCase *surf = &HM_CASES[2];
    restore_snapshot(core, field);
    if (call_bounded(core, BATTLE_CORE_ADD_BAG_ITEM, surf->item, 1, 0, 0).result == 0)
        hm_die("failed to add Surf HM");
    write8(core, HM_FIELD_PLAYER_AVATAR_FLAGS,
           (uint8_t)(read8(core, HM_FIELD_PLAYER_AVATAR_FLAGS) & ~8U));
    results[0] = call_bounded(core, HM_FIELD_CAPABILITY, surf->move, 0,
                              HM_FIELD_SHOULD_NOT_BE_SURFING, 0).result;
    results[1] = call_bounded(core, HM_FIELD_CAPABILITY, surf->move, 0,
                              HM_FIELD_SHOULD_BE_SURFING, 0).result;
    write8(core, HM_FIELD_PLAYER_AVATAR_FLAGS,
           (uint8_t)(read8(core, HM_FIELD_PLAYER_AVATAR_FLAGS) | 8U));
    results[2] = call_bounded(core, HM_FIELD_CAPABILITY, surf->move, 0,
                              HM_FIELD_SHOULD_NOT_BE_SURFING, 0).result;
    results[3] = call_bounded(core, HM_FIELD_CAPABILITY, surf->move, 0,
                              HM_FIELD_SHOULD_BE_SURFING, 0).result;
    if (results[0] != 0 || results[1] != 6
        || results[2] != 6 || results[3] != 0) {
        hm_die("Surf state boundary changed");
    }
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64 || strcmp(rom_sha256, argv[2]) != 0)
        hm_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) hm_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) hm_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    if (log_problem_count) hm_die("mGBA warned/errored during field boot");
    struct Snapshot field = take_snapshot(core);

    struct HMObservation observations[ARRAY_LEN(HM_CASES)][HM_PARTY_KIND_COUNT];
    struct HMCallbackObservation callbacks[ARRAY_LEN(HM_CASES)];
    uint32_t surf_boundaries[4];
    for (unsigned hm = 0; hm < ARRAY_LEN(HM_CASES); ++hm) {
        for (unsigned party = 0; party < HM_PARTY_KIND_COUNT; ++party) {
            observations[hm][party] = observe_capability(
                core, &field, &HM_CASES[hm], (enum HMPartyKind)party);
        }
        callbacks[hm] = observe_callback(core, &field, &HM_CASES[hm]);
    }
    observe_surf_boundaries(core, &field, surf_boundaries);
    if (log_problem_count) hm_die("mGBA warned/errored during HM fixtures");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"hm_item_owned_field_capability_v1\","
           "\"rom_sha256\":\"%s\",\"read_only\":true,"
           "\"warnings_errors\":0,\"hm_cases\":[", rom_sha256);
    for (unsigned hm = 0; hm < ARRAY_LEN(HM_CASES); ++hm) {
        if (hm) putchar(',');
        printf("{\"name\":\"%s\",\"move\":%u,\"item\":%u,"
               "\"party_variants\":[",
               HM_CASES[hm].name, HM_CASES[hm].move, HM_CASES[hm].item);
        for (unsigned party = 0; party < HM_PARTY_KIND_COUNT; ++party) {
            const struct HMObservation *row = &observations[hm][party];
            if (party) putchar(',');
            printf("{\"party\":\"%s\",\"before\":%" PRIu32
                   ",\"after\":%" PRIu32 ",\"after_restore\":%" PRIu32
                   ",\"bag_count\":%" PRIu32 "}",
                   HM_PARTY_NAMES[party], row->before, row->after,
                   row->after_restore, row->bag_count);
        }
        printf("],\"callback\":{\"wrapper\":\"0x%08" PRIX32
               "\",\"missing\":%" PRIu32 ",\"owned\":%" PRIu32
               ",\"original_map_gate\":%" PRIu32 "}}",
               callbacks[hm].wrapper, callbacks[hm].missing_result,
               callbacks[hm].owned_result, callbacks[hm].original_result);
    }
    printf("],\"surf_state_boundary\":{\"land_not_surfing\":%" PRIu32
           ",\"land_requires_surfing\":%" PRIu32
           ",\"surf_rejects_land_only\":%" PRIu32
           ",\"surf_requires_surfing\":%" PRIu32
           "},\"move_writes\":0,\"new_story_flags\":0}\n",
           surf_boundaries[0], surf_boundaries[1],
           surf_boundaries[2], surf_boundaries[3]);

    free(field.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
