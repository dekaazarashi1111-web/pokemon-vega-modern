/*
 * Stage61 League/Seafoam progression lifecycle E2E.
 *
 * Fixture construction and state preparation may use audited stock ROM calls.
 * Every progression owner is nevertheless reached by the live player: walking,
 * direction+A, battle win/loss, blackout, room warps, Strength, the boulder
 * push, the fall warp, START-save and title-screen Continue are real GBA input.
 * No object/map script address is ever called by the host.
 */
#ifndef S61_PROGRESSION_EMBEDDED_HARNESS
#error "compile through scripts/run_stage61_progression_lifecycle_e2e.py"
#endif
#include S61_PROGRESSION_EMBEDDED_HARNESS

#include <limits.h>

enum {
    PL_GROUP = 97U,
    PL_ROUTE20_GROUP = 96U,
    PL_ROUTE20_MAP = 31U,
    PL_LEAGUE_SCENE_VAR = 0x516CU,
    PL_LEAGUE_GATE_FLAG = 0x1407U,
    PL_LEAGUE_FIRST_COMPLETE_FLAG = 0x1408U,
    PL_LEAGUE_FINAL_COMPLETE_FLAG = 0x140CU,
    PL_GAME_CLEAR_FLAG = 0x082CU,
    PL_REPEL_STEP_VAR = 0x4020U,
    PL_B4_SCENE_VAR = 0x5167U,
    /* Badge state is project-relocated, but FLAG_SYS_USE_STRENGTH is a native
     * field-engine ABI shared by script, push, warp/reset, and Continue. */
    PL_BADGE_4_FLAG = 0x18B7U,
    PL_SYS_USE_STRENGTH = 0x0805U,
    PL_HM03_SURF = 341U,
    PL_HM04_STRENGTH = 342U,
    PL_MOVE_STRENGTH = 70U,
    PL_MOVE_SPLASH = 150U,
    PL_1F_BOULDER_1_HIDE = 0x162DU,
    PL_1F_BOULDER_2_HIDE = 0x162EU,
    PL_B1_BOULDER_1_HIDE = 0x162FU,
    PL_B1_BOULDER_2_HIDE = 0x1630U,
    PL_B2_BOULDER_1_HIDE = 0x1631U,
    PL_B2_BOULDER_2_HIDE = 0x1632U,
    PL_B3_ARRIVAL_1_HIDE = 0x1633U,
    PL_B3_ARRIVAL_2_HIDE = 0x1634U,
    PL_B3_SOURCE_HIDE = 0x1635U,
    PL_B3_OBSTACLE_1_HIDE = 0x1636U,
    PL_B3_SOURCE_2_HIDE = 0x1637U,
    PL_B3_OBSTACLE_2_HIDE = 0x1638U,
    PL_B4_BOULDER_1_HIDE = 0x1639U,
    PL_B4_BOULDER_2_HIDE = 0x163AU,
    PL_B3_STOPPED = 0x163DU,
    PL_B4_STOPPED = 0x163EU,
    PL_FALL_WARP_BEHAVIOR = 0x066U,
    PL_FALL_WARP_EFFECT_7 = 0x080842F4U,
    PL_TRY_PUSH_BOULDER = 0x0805B5A8U,
    PL_MAX_MAP_WIDTH = 40U,
    PL_MAX_MAP_HEIGHT = 32U,
    PL_MAX_NAV_DEPTH = 2048U,
};

struct PlPoint {
    uint16_t x;
    uint16_t y;
};

struct PlMap {
    const char *name;
    uint8_t map;
    uint16_t width;
    uint16_t height;
    struct PlPoint object;
    uint8_t local_id;
    struct PlPoint forward_warp;
};

struct PlPushSegment {
    uint16_t key;
    unsigned count;
};

struct PlBoulderStage {
    const char *name;
    const struct PlMap *map;
    uint8_t local_id;
    struct PlPoint start;
    struct PlPoint hole;
    uint16_t source_hide;
    uint16_t destination_hide;
    const struct PlPushSegment *segments;
    unsigned segment_count;
};

static const struct PlMap PL_LEAGUE[] = {
    {"lorelei", 75U, 13U, 13U, {6U, 5U}, 1U, {6U, 2U}},
    {"bruno", 76U, 13U, 13U, {6U, 5U}, 1U, {6U, 2U}},
    {"agatha", 77U, 13U, 13U, {6U, 5U}, 1U, {6U, 2U}},
    {"lance", 78U, 28U, 24U, {6U, 8U}, 1U, {6U, 5U}},
    {"champion", 79U, 13U, 20U, {6U, 8U}, 1U, {6U, 2U}},
};

/* Stage60 trainerbattle proxies suspend at their trainerbattle command.  On
 * WIN the engine first runs the room's tag-5 map script, then resumes the
 * proxy at its post text/goto.  These are opcode addresses, not inferred
 * labels: the four pointer operands are the safe Stage61 repoint sites. */
static const uint32_t PL_LEAGUE_PROXY_GOTO[] = {
    0x0936B442U, 0x0936B45EU, 0x0936B47AU, 0x0936B496U,
    0x0936B4B2U,
};

static const uint32_t PL_LEAGUE_SOURCE_COMPLETION[] = {
    0x0936B2A5U, 0x0936B2CDU, 0x0936B2F5U, 0x0936B31DU,
    0x0936B345U,
};

static const uint32_t PL_LEAGUE_TAG5_ROOT[] = {
    0x09447734U, 0x094477FBU, 0x094478C3U, 0x094479BAU, 0U,
};

static const struct PlMap PL_HALL = {
    "hall_of_fame", 80U, 11U, 13U, {6U, 4U}, 1U, {5U, 12U},
};

static const struct PlMap PL_SAFE = {
    "progression_safe", 83U, 38U, 24U, {11U, 8U}, 1U, {10U, 6U},
};

static const struct PlMap PL_SEAFOAM_1F = {
    "seafoam_1f", 83U, 38U, 24U, {22U, 12U}, 2U, {21U, 8U},
};

static const struct PlMap PL_SEAFOAM_B1 = {
    "seafoam_b1", 84U, 38U, 23U, {22U, 8U}, 3U, {23U, 8U},
};

static const struct PlMap PL_SEAFOAM_B2 = {
    "seafoam_b2", 85U, 38U, 24U, {22U, 8U}, 2U, {24U, 8U},
};

static const struct PlMap PL_B3 = {
    "seafoam_b3", 86U, 38U, 24U, {6U, 17U}, 6U, {6U, 18U},
};

static const struct PlMap PL_B4 = {
    "seafoam_b4", 87U, 38U, 24U, {8U, 18U}, 1U, {8U, 17U},
};

static const struct PlPoint PL_B3_WARPS[] = {
    {8U, 14U}, {31U, 4U}, {31U, 16U}, {12U, 9U}, {29U, 5U},
    {23U, 9U}, {24U, 9U}, {6U, 18U}, {9U, 18U},
};

static const struct PlPoint PL_B4_WARPS[] = {
    {15U, 9U}, {32U, 5U}, {8U, 17U}, {9U, 17U},
};

static const struct PlPushSegment PL_UPPER_1F_FIRST_MOVES[] = {
    {WORLD_KEY_LEFT, 1U}, {WORLD_KEY_UP, 4U},
};
static const struct PlPushSegment PL_UPPER_B1_FIRST_MOVES[] = {
    {WORLD_KEY_RIGHT, 1U},
};
static const struct PlPushSegment PL_UPPER_B2_FIRST_MOVES[] = {
    {WORLD_KEY_RIGHT, 2U},
};
static const struct PlPushSegment PL_UPPER_1F_SECOND_MOVES[] = {
    {WORLD_KEY_LEFT, 2U}, {WORLD_KEY_UP, 1U},
};
static const struct PlPushSegment PL_UPPER_B1_SECOND_MOVES[] = {
    {WORLD_KEY_LEFT, 2U},
};
static const struct PlPushSegment PL_UPPER_B2_SECOND_MOVES[] = {
    {WORLD_KEY_LEFT, 3U},
};
static const struct PlPushSegment PL_B3_FIRST_MOVES[] = {
    {WORLD_KEY_DOWN, 1U},
};
static const struct PlPushSegment PL_B3_SECOND_MOVES[] = {
    {WORLD_KEY_DOWN, 2U}, {WORLD_KEY_LEFT, 3U},
};

static const struct PlBoulderStage PL_UPPER_FIRST[] = {
    {"upper-first-1f", &PL_SEAFOAM_1F, 2U, {22U, 12U}, {21U, 8U},
     PL_1F_BOULDER_1_HIDE, PL_B1_BOULDER_1_HIDE,
     PL_UPPER_1F_FIRST_MOVES, 2U},
    {"upper-first-b1", &PL_SEAFOAM_B1, 3U, {22U, 8U}, {23U, 8U},
     PL_B1_BOULDER_1_HIDE, PL_B2_BOULDER_1_HIDE,
     PL_UPPER_B1_FIRST_MOVES, 1U},
    {"upper-first-b2", &PL_SEAFOAM_B2, 2U, {22U, 8U}, {24U, 8U},
     PL_B2_BOULDER_1_HIDE, PL_B3_ARRIVAL_1_HIDE,
     PL_UPPER_B2_FIRST_MOVES, 1U},
};

static const struct PlBoulderStage PL_UPPER_SECOND[] = {
    {"upper-second-1f", &PL_SEAFOAM_1F, 3U, {32U, 9U}, {30U, 8U},
     PL_1F_BOULDER_2_HIDE, PL_B1_BOULDER_2_HIDE,
     PL_UPPER_1F_SECOND_MOVES, 2U},
    {"upper-second-b1", &PL_SEAFOAM_B1, 4U, {30U, 8U}, {28U, 8U},
     PL_B1_BOULDER_2_HIDE, PL_B2_BOULDER_2_HIDE,
     PL_UPPER_B1_SECOND_MOVES, 1U},
    {"upper-second-b2", &PL_SEAFOAM_B2, 3U, {30U, 8U}, {27U, 8U},
     PL_B2_BOULDER_2_HIDE, PL_B3_ARRIVAL_2_HIDE,
     PL_UPPER_B2_SECOND_MOVES, 1U},
};

static const struct PlBoulderStage PL_B3_FIRST_STAGE = {
    "b3-first-to-b4", &PL_B3, 6U, {6U, 17U}, {6U, 18U},
    PL_B3_SOURCE_HIDE, PL_B4_BOULDER_1_HIDE, PL_B3_FIRST_MOVES, 1U,
};

static const struct PlBoulderStage PL_B3_SECOND_STAGE = {
    "b3-second-to-b4", &PL_B3, 5U, {12U, 16U}, {9U, 18U},
    PL_B3_SOURCE_2_HIDE, PL_B4_BOULDER_2_HIDE, PL_B3_SECOND_MOVES, 2U,
};

struct PlNav {
    uint8_t group;
    uint8_t map;
    uint16_t width;
    uint16_t height;
    struct PlPoint target;
    bool exact_target;
    bool visited[PL_MAX_MAP_HEIGHT][PL_MAX_MAP_WIDTH];
    unsigned steps;
};

struct PlFallResult {
    bool destination_seen;
    bool callback_transition;
    bool coordinate_motion;
    bool surf_seen;
    bool field_recovered;
    unsigned owner_hits;
};

struct PlSavePosition {
    uint16_t x;
    uint16_t y;
    uint8_t warp_id;
};

struct PlCheckpointEvidence {
    struct PlSavePosition save_before;
    struct PlSavePosition cold_continue;
    uint64_t cold_framebuffer_hash;
};

struct PlSeafoamBranchResult {
    uint32_t layout;
    unsigned walk_steps;
    unsigned strength_owner_hits;
    unsigned fall_owner_hits;
    unsigned push_owner_hits;
    unsigned strength_cases;
    unsigned fall_cases;
    unsigned push_cases;
    unsigned push_steps;
    unsigned topology_transitions;
    unsigned bootstrap_warps;
    unsigned route20_owner_hits;
    bool current_motion;
    bool surf_seen;
    bool callback_chain;
    bool b3_stopped;
    bool b4_stopped;
    bool obstacle_controls_preserved;
    struct PlCheckpointEvidence checkpoint;
};

struct PlLeagueInstructionTrace {
    uint64_t ordinal;
    uint64_t outcome_ordinal;
    uint64_t tag5_ordinal;
    uint64_t proxy_goto_ordinal;
    uint64_t completion_target_ordinal;
    uint64_t completion_flag_ordinal;
    uint32_t completion_target;
    uint8_t outcome;
};

struct PlLeagueEvidence {
    unsigned walk_steps;
    unsigned owner_hits;
    unsigned battle_resume_trace_cases;
    unsigned elite_completion_adapter_cases;
    bool champion_no_geometry_control;
};

static struct Fixture pl_fixture(const char *name, const struct PlMap *map,
                                 uint16_t x, uint16_t y)
{
    struct Fixture fixture = {
        .name = name,
        .kind = FIXTURE_FACING_DIALOGUE,
        .group = PL_GROUP,
        .map = map->map,
        .x = x,
        .y = y,
        .action_key = WORLD_KEY_UP,
    };
    return fixture;
}

static void pl_path(char *destination, size_t size, const char *directory,
                    const char *stem, const char *extension)
{
    int count = snprintf(destination, size, "%s/%s.%s",
                         directory, stem, extension);
    if (count <= 0 || (size_t)count >= size)
        s61_die("progression artifact path formatting failed");
}

/* bootstrap_write_ppm owns the trailing ".ppm".  Pass an extension-free
 * prefix so the retained artifact is exactly <directory>/<stem>.ppm. */
static void pl_artifact_prefix(char *destination, size_t size,
                               const char *directory, const char *stem)
{
    int count = snprintf(destination, size, "%s/%s", directory, stem);
    if (count <= 0 || (size_t)count >= size)
        s61_die("progression artifact prefix formatting failed");
}

static unsigned pl_flag(struct mCore *core, uint16_t flag)
{
    return (unsigned)s61_call_synced(
        core, WORLD_FLAG_GET, flag, 0U, 0U, 0U);
}

static bool pl_flag_direct(struct mCore *core, uint16_t flag)
{
    if (flag < 0x0900U) {
        uint32_t save1 = world_save1(core, "flag-direct");
        return (read8(core, save1 + WORLD_LEGACY_FLAGS_VARS_OFFSET
                            + (flag >> 3U))
                & (1U << (flag & 7U))) != 0U;
    }
    if (flag <= 0x18FFU)
        return (read8(core, WORLD_EXPANDED_FLAGS_VARS
                            + ((flag - 0x0900U) >> 3U))
                & (1U << (flag & 7U))) != 0U;
    s61_die("direct flag read outside persistent namespaces");
    return false;
}

static void pl_set_flag(struct mCore *core, uint16_t flag, bool set)
{
    (void)s61_call_synced(core, set ? WORLD_FLAG_SET : WORLD_FLAG_CLEAR,
                          flag, 0U, 0U, 0U);
    if (pl_flag(core, flag) != (set ? 1U : 0U))
        s61_die("progression flag preparation/readback failed");
}

static unsigned pl_var(struct mCore *core, uint16_t variable)
{
    if (variable >= 0x4000U && variable <= 0x40FFU) {
        uint32_t save1 = world_save1(core, "legacy-var-read");
        return read16(core, save1 + 0x1000U
                            + (variable - 0x4000U) * 2U);
    }
    if (variable >= 0x5000U && variable <= 0x51FFU)
        return read16(core, WORLD_EXPANDED_FLAGS_VARS + 0x200U
                            + (variable - 0x5000U) * 2U);
    s61_die("progression var ID is outside persistent namespaces");
    return 0U;
}

static void pl_set_var(struct mCore *core, uint16_t variable, uint16_t value)
{
    if (variable >= 0x4000U && variable <= 0x40FFU) {
        uint32_t save1 = world_save1(core, "legacy-var-write");
        write16(core, save1 + 0x1000U
                      + (variable - 0x4000U) * 2U, value);
    } else if (variable >= 0x5000U && variable <= 0x51FFU) {
        write16(core, WORLD_EXPANDED_FLAGS_VARS + 0x200U
                      + (variable - 0x5000U) * 2U, value);
    } else {
        s61_die("progression var ID is outside persistent namespaces");
    }
    unsigned actual = pl_var(core, variable);
    if (actual != value) {
        fprintf(stderr, "var readback variable=0x%04X expected=%u actual=%u\n",
                variable, value, actual);
        s61_die("progression var preparation/readback failed");
    }
}

static void pl_assert_map(struct mCore *core, const char *case_id,
                          uint8_t map)
{
    uint32_t save1 = world_save1(core, case_id);
    if (read8(core, save1 + 4U) != PL_GROUP
        || read8(core, save1 + 5U) != map) {
        fprintf(stderr, "map mismatch case=%s actual=%u/%u expected=%u/%u\n",
                case_id, read8(core, save1 + 4U), read8(core, save1 + 5U),
                PL_GROUP, map);
        s61_die("progression live map identity drifted");
    }
}

static struct PlSavePosition pl_save_position(struct mCore *core,
                                              const char *case_id)
{
    uint32_t save1 = world_save1(core, case_id);
    struct PlSavePosition position = {
        .x = read16(core, save1),
        .y = read16(core, save1 + 2U),
        .warp_id = read8(core, save1 + 6U),
    };
    return position;
}

static uint64_t pl_framebuffer_rgb_fnv1a64(const color_t *video)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < 240U * 160U; ++index) {
        uint32_t pixel = (uint32_t)video[index];
        for (unsigned byte = 0U; byte < 3U; ++byte) {
            hash ^= (uint8_t)(pixel >> (byte * 8U));
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static void pl_close_to_exact_srm(struct mCore *core, const char *path)
{
    uint8_t *raw = s61_cow_clone_savedata(core);
    bootstrap_close_core(core);
    s61_diagnostic_core = NULL;
    s61_write_exact_binary(path, raw, BOOTSTRAP_SAVE_SIZE);
    free(raw);
}

static bool pl_wait_field(struct mCore *core, uint8_t map,
                          struct S61Capture *capture, bool advance)
{
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 7200U; ++frame) {
        uint16_t keys = advance && frame > 1800U && frame % 90U < 2U
            ? WORLD_KEY_A : 0U;
        if (capture != NULL)
            s61_step_capture_frames(core, keys, 1U, capture);
        else
            run_key_frames(core, keys, 1U);
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        bool exact = save1 >= 0x02000000U && save1 < 0x02040000U
            && read8(core, save1 + 4U) == PL_GROUP
            && read8(core, save1 + 5U) == map
            && s61_field_terminal(core)
            && read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U;
        if (exact) {
            if (++stable >= 30U) {
                core->setKeys(core, 0U);
                return true;
            }
        } else {
            stable = 0U;
        }
    }
    core->setKeys(core, 0U);
    return false;
}

/* A stock warp is only a fixture/player placement operation.  Map scripts
 * still run in the emulator, and the final coordinate is intentionally not
 * written or asserted because authored entry movement owns it. */
static void pl_bootstrap_warp(struct mCore *core, const char *case_id,
                              uint8_t map, uint16_t x, uint16_t y)
{
    (void)s61_call_synced(core, BOOTSTRAP_KANTO_WARP,
                          PL_GROUP, map, x, y);
    if (!pl_wait_field(core, map, NULL, false)
        && !pl_wait_field(core, map, NULL, true)) {
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        fprintf(stderr, "bootstrap warp did not settle case=%s map=%u"
                " save1=%08" PRIX32 " actual=%u/%u xy=%u,%u"
                " callback=%08" PRIX32 " script=%u message=%u controls=%u"
                " pc=%08" PRIX32 "\n",
                case_id, map, save1,
                save1 >= 0x02000000U && save1 < 0x02040000U
                    ? read8(core, save1 + 4U) : 0xFFU,
                save1 >= 0x02000000U && save1 < 0x02040000U
                    ? read8(core, save1 + 5U) : 0xFFU,
                save1 >= 0x02000000U && save1 < 0x02040000U
                    ? read16(core, save1) : 0U,
                save1 >= 0x02000000U && save1 < 0x02040000U
                    ? read16(core, save1 + 2U) : 0U,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core) ? 1U : 0U,
                read8(core, WORLD_FIELD_MESSAGE_STATE),
                read8(core, WORLD_FIELD_CONTROLS_LOCKED),
                (uint32_t)read_register(core, "pc"));
        s61_die("stock player warp did not reach an input-ready field");
    }
    pl_assert_map(core, case_id, map);
}

static void pl_bootstrap_warp_group(struct mCore *core, const char *case_id,
                                    uint8_t group, uint8_t map,
                                    uint16_t x, uint16_t y,
                                    struct S61Capture *capture)
{
    (void)s61_call_synced(core, BOOTSTRAP_KANTO_WARP, group, map, x, y);
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 14400U; ++frame) {
        uint16_t keys = frame > 7200U && frame % 90U < 2U
            ? WORLD_KEY_A : 0U;
        if (capture != NULL)
            s61_step_capture_frames(core, keys, 1U, capture);
        else
            run_key_frames(core, keys, 1U);
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        bool exact = save1 >= 0x02000000U && save1 < 0x02040000U
            && read8(core, save1 + 4U) == group
            && read8(core, save1 + 5U) == map
            && s61_field_terminal(core)
            && read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U;
        if (exact) {
            if (++stable >= 30U) {
                core->setKeys(core, 0U);
                return;
            }
        } else {
            stable = 0U;
        }
    }
    core->setKeys(core, 0U);
    fprintf(stderr, "group warp did not settle case=%s expected=%u/%u\n",
            case_id, group, map);
    s61_die("stock player group warp did not reach an input-ready field");
}

static uint16_t pl_opposite(uint16_t key)
{
    if (key == WORLD_KEY_LEFT) return WORLD_KEY_RIGHT;
    if (key == WORLD_KEY_RIGHT) return WORLD_KEY_LEFT;
    if (key == WORLD_KEY_UP) return WORLD_KEY_DOWN;
    return WORLD_KEY_UP;
}

static void pl_delta(uint16_t key, int *dx, int *dy)
{
    *dx = key == WORLD_KEY_RIGHT ? 1 : key == WORLD_KEY_LEFT ? -1 : 0;
    *dy = key == WORLD_KEY_DOWN ? 1 : key == WORLD_KEY_UP ? -1 : 0;
}

static bool pl_same_point(uint16_t x, uint16_t y,
                          const struct PlPoint *point)
{
    return x == point->x && y == point->y;
}

static bool pl_forbidden(uint8_t map, uint16_t x, uint16_t y)
{
    if (map >= 75U && map <= 79U) {
        unsigned index = (unsigned)(map - 75U);
        const struct PlMap *room = &PL_LEAGUE[index];
        struct PlPoint back = {
            room->map == 78U ? 23U : 6U,
            room->map == 78U ? 13U : room->map == 79U ? 19U : 12U,
        };
        return pl_same_point(x, y, &room->forward_warp)
            || pl_same_point(x, y, &back);
    }
    if (map == PL_B3.map) {
        for (unsigned index = 0U;
             index < sizeof(PL_B3_WARPS) / sizeof(PL_B3_WARPS[0]); ++index) {
            if (pl_same_point(x, y, &PL_B3_WARPS[index])) return true;
        }
    }
    if (map == PL_B4.map) {
        for (unsigned index = 0U;
             index < sizeof(PL_B4_WARPS) / sizeof(PL_B4_WARPS[0]); ++index) {
            if (pl_same_point(x, y, &PL_B4_WARPS[index])) return true;
        }
        if (y == 19U && x >= 26U && x <= 28U) return true;
    }
    return false;
}

static bool pl_walk_one(struct mCore *core, uint16_t key,
                        uint16_t *x, uint16_t *y, unsigned *steps,
                        struct S61Capture *capture)
{
    uint16_t old_x = *x, old_y = *y;
    uint8_t group = read8(core, world_save1(core, "walk-one") + 4U);
    uint8_t map = read8(core, world_save1(core, "walk-one") + 5U);
    for (unsigned frame = 0U; frame < 48U; ++frame) {
        if (capture != NULL)
            s61_step_capture_frames(core, key, 1U, capture);
        else
            run_key_frames(core, key, 1U);
        uint32_t save1 = world_save1(core, "walk-one");
        if (read8(core, save1 + 4U) != group
            || read8(core, save1 + 5U) != map || !world_overworld(core)) {
            core->setKeys(core, 0U);
            return false;
        }
        uint16_t next_x = read16(core, save1);
        uint16_t next_y = read16(core, save1 + 2U);
        if (next_x != old_x || next_y != old_y) {
            core->setKeys(core, 0U);
            *x = next_x;
            *y = next_y;
            ++*steps;
            if (capture != NULL)
                s61_step_capture_frames(core, 0U, 45U, capture);
            else
                run_key_frames(core, 0U, 45U);
            return s61_field_terminal(core);
        }
    }
    core->setKeys(core, 0U);
    if (capture != NULL)
        s61_step_capture_frames(core, 0U, 4U, capture);
    else
        run_key_frames(core, 0U, 4U);
    return false;
}

static unsigned pl_distance(uint16_t x, uint16_t y,
                            const struct PlPoint *point)
{
    unsigned dx = x > point->x ? x - point->x : point->x - x;
    unsigned dy = y > point->y ? y - point->y : point->y - y;
    return dx + dy;
}

static bool pl_nav_dfs(struct mCore *core, struct PlNav *nav,
                       uint16_t x, uint16_t y, unsigned depth)
{
    if ((nav->exact_target && pl_same_point(x, y, &nav->target))
        || (!nav->exact_target && pl_distance(x, y, &nav->target) == 1U))
        return true;
    if (depth >= PL_MAX_NAV_DEPTH) return false;
    uint16_t horizontal = nav->target.x >= x ? WORLD_KEY_RIGHT : WORLD_KEY_LEFT;
    uint16_t vertical = nav->target.y >= y ? WORLD_KEY_DOWN : WORLD_KEY_UP;
    uint16_t order[4] = {horizontal, vertical,
                         pl_opposite(horizontal), pl_opposite(vertical)};
    unsigned distance_x = x > nav->target.x
        ? (unsigned)(x - nav->target.x)
        : (unsigned)(nav->target.x - x);
    unsigned distance_y = y > nav->target.y
        ? (unsigned)(y - nav->target.y)
        : (unsigned)(nav->target.y - y);
    if (distance_y > distance_x) {
        order[0] = vertical; order[1] = horizontal;
    }
    for (unsigned index = 0U; index < 4U; ++index) {
        uint16_t key = order[index];
        int dx = 0, dy = 0; pl_delta(key, &dx, &dy);
        int nx = (int)x + dx, ny = (int)y + dy;
        if (nx < 0 || ny < 0 || nx >= (int)nav->width
            || ny >= (int)nav->height
            || nav->visited[ny][nx]
            || pl_forbidden(nav->map, (uint16_t)nx, (uint16_t)ny))
            continue;
        uint16_t actual_x = x, actual_y = y;
        unsigned before = nav->steps;
        if (!pl_walk_one(core, key, &actual_x, &actual_y,
                         &nav->steps, NULL))
            continue;
        if (actual_x != (uint16_t)nx || actual_y != (uint16_t)ny)
            s61_die("natural navigation moved by more than one tile");
        nav->visited[actual_y][actual_x] = true;
        if (pl_nav_dfs(core, nav, actual_x, actual_y, depth + 1U))
            return true;
        if (!pl_walk_one(core, pl_opposite(key), &actual_x, &actual_y,
                         &nav->steps, NULL)
            || actual_x != x || actual_y != y)
            s61_die("natural navigation physical backtrack failed");
        if (nav->steps <= before)
            s61_die("natural navigation step accounting failed");
    }
    return false;
}

static void pl_navigate_exact(struct mCore *core, const char *case_id,
                              const struct PlMap *map,
                              struct PlPoint target, unsigned *walk_steps)
{
    pl_assert_map(core, case_id, map->map);
    uint32_t save1 = world_save1(core, case_id);
    uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
    if (x >= map->width || y >= map->height
        || target.x >= map->width || target.y >= map->height)
        s61_die("exact navigation coordinate is outside map dimensions");
    struct PlNav nav = {
        .group = PL_GROUP, .map = map->map,
        .width = map->width, .height = map->height,
        .target = target, .exact_target = true,
    };
    nav.visited[y][x] = true;
    if (!pl_nav_dfs(core, &nav, x, y, 0U)) {
        fprintf(stderr, "exact navigation failed case=%s map=%u"
                " start=(%u,%u) target=(%u,%u) steps=%u\n",
                case_id, map->map, x, y, target.x, target.y, nav.steps);
        s61_die("no naturally walkable route to exact push position");
    }
    *walk_steps += nav.steps;
    save1 = world_save1(core, case_id);
    if (read16(core, save1) != target.x
        || read16(core, save1 + 2U) != target.y)
        s61_die("exact navigation ended at the wrong coordinate");
}

static uint16_t pl_navigate_adjacent(struct mCore *core, const char *case_id,
                                     const struct PlMap *map,
                                     struct PlPoint target,
                                     unsigned *walk_steps)
{
    pl_assert_map(core, case_id, map->map);
    uint32_t save1 = world_save1(core, case_id);
    uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
    if (x >= map->width || y >= map->height)
        s61_die("navigation player coordinate is outside map dimensions");
    struct PlNav nav = {
        .group = PL_GROUP, .map = map->map,
        .width = map->width, .height = map->height, .target = target,
    };
    nav.visited[y][x] = true;
    if (!pl_nav_dfs(core, &nav, x, y, 0U)) {
        fprintf(stderr, "navigation failed case=%s map=%u start=(%u,%u) target=(%u,%u) steps=%u\n",
                case_id, map->map, x, y, target.x, target.y, nav.steps);
        s61_die("no naturally walkable route to progression owner");
    }
    *walk_steps += nav.steps;
    save1 = world_save1(core, case_id);
    x = read16(core, save1); y = read16(core, save1 + 2U);
    int dx = (int)target.x - (int)x, dy = (int)target.y - (int)y;
    if (dx == 1 && dy == 0) return WORLD_KEY_RIGHT;
    if (dx == -1 && dy == 0) return WORLD_KEY_LEFT;
    if (dx == 0 && dy == 1) return WORLD_KEY_DOWN;
    if (dx == 0 && dy == -1) return WORLD_KEY_UP;
    s61_die("navigation did not stop adjacent to target");
    return 0U;
}

static bool pl_actual_warp(struct mCore *core, const char *case_id,
                           const struct PlMap *source,
                           struct PlPoint warp, uint8_t destination,
                           unsigned *walk_steps)
{
    uint16_t key = pl_navigate_adjacent(
        core, case_id, source, warp, walk_steps);
    uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    bool callback_changed = false, destination_seen = false;
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        run_key_frames(core, frame < 48U ? key : 0U, 1U);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != callback)
            callback_changed = true;
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (save1 >= 0x02000000U && save1 < 0x02040000U
            && read8(core, save1 + 4U) == PL_GROUP
            && read8(core, save1 + 5U) == destination) {
            destination_seen = true;
            break;
        }
    }
    core->setKeys(core, 0U);
    bool field = destination_seen
        && pl_wait_field(core, destination, NULL, false);
    if (!destination_seen || !field || !callback_changed) {
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        fprintf(stderr, "warp case=%s source=%u target=%u,%u dest=%u"
                " seen=%u field=%u callback_changed=%u callback=%08" PRIX32
                "/%08" PRIX32 " actual=%u/%u xy=%u,%u script=%u\n",
                case_id, source->map, warp.x, warp.y, destination,
                destination_seen ? 1U : 0U, field ? 1U : 0U,
                callback_changed ? 1U : 0U, callback,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                world_script_enabled(core) ? 1U : 0U);
        s61_die("physical warp/callback transition did not complete");
    }
    ++*walk_steps;
    return true;
}

static bool pl_actual_warp_any(struct mCore *core, const char *case_id,
                               const struct PlMap *source,
                               const struct PlPoint *warps, unsigned count,
                               uint8_t destination, unsigned *walk_steps)
{
    for (unsigned index = 0U; index < count; ++index) {
        uint32_t save1 = world_save1(core, case_id);
        uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
        struct PlNav probe = {
            .group = PL_GROUP, .map = source->map,
            .width = source->width, .height = source->height,
            .target = warps[index],
        };
        if (x >= source->width || y >= source->height) continue;
        probe.visited[y][x] = true;
        if (!pl_nav_dfs(core, &probe, x, y, 0U)) continue;
        *walk_steps += probe.steps;
        uint16_t key;
        save1 = world_save1(core, case_id);
        x = read16(core, save1); y = read16(core, save1 + 2U);
        int dx = (int)warps[index].x - (int)x;
        int dy = (int)warps[index].y - (int)y;
        if (dx == 1 && dy == 0) key = WORLD_KEY_RIGHT;
        else if (dx == -1 && dy == 0) key = WORLD_KEY_LEFT;
        else if (dx == 0 && dy == 1) key = WORLD_KEY_DOWN;
        else if (dx == 0 && dy == -1) key = WORLD_KEY_UP;
        else s61_die("warp-any route did not end adjacent");
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        bool changed = false, seen = false;
        for (unsigned frame = 0U; frame < 1800U; ++frame) {
            run_key_frames(core, frame < 48U ? key : 0U, 1U);
            if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != callback)
                changed = true;
            uint32_t current = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
            if (current >= 0x02000000U && current < 0x02040000U
                && read8(core, current + 4U) == PL_GROUP
                && read8(core, current + 5U) == destination) {
                seen = true; break;
            }
        }
        core->setKeys(core, 0U);
        if (!seen || !changed || !pl_wait_field(core, destination, NULL, false))
            s61_die("reachable physical exit/re-entry warp did not complete");
        ++*walk_steps;
        return true;
    }
    return false;
}

static uint32_t pl_object_script_root(struct mCore *core, uint8_t local_id,
                                      uint16_t expected_x,
                                      uint16_t expected_y)
{
    uint32_t events = read32(core, WORLD_MAP_HEADER + 4U);
    unsigned count = read8(core, events);
    uint32_t objects = read32(core, events + 4U);
    for (unsigned index = 0U; index < count; ++index) {
        uint32_t object = objects + index * 24U;
        if (read8(core, object) == local_id
            && read16(core, object + 4U) == expected_x
            && read16(core, object + 6U) == expected_y) {
            uint32_t script = read32(core, object + 16U);
            if (script < 0x08000000U || script >= 0x0A000000U)
                s61_die("object script root is outside ROM");
            return script;
        }
    }
    s61_die("expected progression object template is absent");
    return 0U;
}

static unsigned pl_start_object_battle(struct mCore *core,
                                       const char *directory,
                                       const char *case_id,
                                       const struct PlMap *map,
                                       unsigned *walk_steps)
{
    struct S61Interaction object = {
        .group = PL_GROUP, .map = map->map, .local_id = map->local_id,
    };
    if (!s61_object_visible(core, &object))
        s61_die("trainer owner is not a live object event");
    uint16_t key = pl_navigate_adjacent(
        core, case_id, map, map->object, walk_steps);
    uint32_t root = pl_object_script_root(
        core, map->local_id, map->object.x, map->object.y);
    char artifact[4096];
    struct S61Capture capture = s61_new_capture(
        directory, case_id, artifact, sizeof(artifact));
    capture.event_root_script_pointer = root;
    bool driven = s61_drive_interaction(
        core, key, S61_CHOICE_YES, &capture, true);
    if (!driven || !s61_battle_active(core)
        || capture.event_root_script_pointer_hits == 0U) {
        uint32_t save1 = world_save1(core, case_id);
        fprintf(stderr, "trainer start case=%s driven=%u battle=%u root=%08" PRIX32
                " hits=%u map=%u/%u xy=%u,%u scene=%u callback=%08" PRIX32
                " script=%u message=%u\n",
                case_id, driven ? 1U : 0U, s61_battle_active(core) ? 1U : 0U,
                root, capture.event_root_script_pointer_hits,
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                pl_var(core, PL_LEAGUE_SCENE_VAR),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core) ? 1U : 0U,
                read8(core, WORLD_FIELD_MESSAGE_STATE));
        s61_die("direction+A did not reach trainer script owner/battle");
    }
    return capture.event_root_script_pointer_hits;
}

static void pl_prepare_strong_party(struct mCore *core)
{
    if (read8(core, BOOTSTRAP_PLAYER_COUNT) != BOOTSTRAP_TEAM_SIZE)
        s61_die("strong fixture party count is not six");
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        /* Party battle stats are the final 14 bytes of struct Pokemon.
         * Direct fixture amplification avoids invoking a progression owner;
         * move/species/PP remain the naturally generated six-Mewtwo save. */
        write16(core, mon + 86U, 60000U);
        write16(core, mon + 88U, 60000U);
        write16(core, mon + 90U, 60000U);
        write16(core, mon + 92U, 60000U);
        write16(core, mon + 94U, 60000U);
        write16(core, mon + 96U, 60000U);
        write16(core, mon + 98U, 60000U);
    }
}

static void pl_prepare_weak_party(struct mCore *core)
{
    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);
    s61_create_mon_synced(core, BOOTSTRAP_PLAYER_PARTY, 10U, 1U);
    set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                     WORLD_MON_DATA_MOVE1, PL_MOVE_SPLASH);
    set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY, MON_DATA_PP1, 40U);
    set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY, WORLD_MON_DATA_HP, 1U);
    write8(core, BOOTSTRAP_PLAYER_COUNT, 1U);
}

static void pl_prepare_league_state(struct mCore *core)
{
    pl_set_var(core, PL_REPEL_STEP_VAR, 0xFFFFU);
    pl_set_flag(core, PL_GAME_CLEAR_FLAG, true);
    pl_set_flag(core, PL_LEAGUE_GATE_FLAG, true);
    for (uint16_t flag = PL_LEAGUE_FIRST_COMPLETE_FLAG;
         flag <= PL_LEAGUE_FINAL_COMPLETE_FLAG; ++flag)
        pl_set_flag(core, flag, false);
    pl_set_var(core, PL_LEAGUE_SCENE_VAR, 0U);
}

static void pl_sample_league_instruction(
    struct mCore *core, unsigned index, uint16_t completion,
    struct PlLeagueInstructionTrace *trace)
{
    ++trace->ordinal;
    uint32_t raw_pc = (uint32_t)read_register(core, "pc");
    uint32_t instruction_pc = (raw_pc - 4U) & ~1U;
    uint8_t outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
    if (outcome != 0U && trace->outcome_ordinal == 0U) {
        trace->outcome = outcome;
        trace->outcome_ordinal = trace->ordinal;
    }
    if (world_script_enabled(core)) {
        uint32_t script = read32(core, WORLD_SCRIPT_CONTEXT1_POINTER);
        if (script == PL_LEAGUE_PROXY_GOTO[index]
            && trace->proxy_goto_ordinal == 0U)
            trace->proxy_goto_ordinal = trace->ordinal;
        if (script == trace->completion_target
            && trace->completion_target_ordinal == 0U)
            trace->completion_target_ordinal = trace->ordinal;
    }
    /* Tag-5 is an immediate map script and is not installed in
     * ScriptContext1.  Observe its exact RunOnTransitionMapScript callsite;
     * r0 is the resolved root operand at this instruction boundary. */
    if (PL_LEAGUE_TAG5_ROOT[index] != 0U
        && instruction_pc == 0x0806948EU
        && (uint32_t)read_register(core, "r0")
            == PL_LEAGUE_TAG5_ROOT[index]
        && trace->tag5_ordinal == 0U)
        trace->tag5_ordinal = trace->ordinal;
    if (pl_flag_direct(core, completion)
        && trace->completion_flag_ordinal == 0U)
        trace->completion_flag_ordinal = trace->ordinal;
}

static void pl_trace_frames(struct mCore *core, uint16_t keys,
                            unsigned frames, unsigned index,
                            uint16_t completion,
                            struct PlLeagueInstructionTrace *trace)
{
    core->setKeys(core, keys);
    uint32_t first_frame = core->frameCounter(core);
    while ((uint32_t)(core->frameCounter(core) - first_frame) < frames) {
        /* Battle animation/input is intentionally run at frame granularity.
         * Switch to instruction stepping at the first frame boundary that
         * exposes a nonzero battle outcome; the map-resume/tag-5 path occurs
         * afterwards and is then observed without a single frame skip. */
        if (trace->outcome_ordinal == 0U) {
            core->runFrame(core);
            if (read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0U)
                pl_sample_league_instruction(
                    core, index, completion, trace);
            continue;
        }
        pl_sample_league_instruction(core, index, completion, trace);
        core->step(core);
    }
    if (trace->outcome_ordinal != 0U)
        pl_sample_league_instruction(core, index, completion, trace);
}

static void pl_trace_pulse(struct mCore *core, uint16_t key,
                           unsigned pressed, unsigned released,
                           unsigned index, uint16_t completion,
                           struct PlLeagueInstructionTrace *trace)
{
    pl_trace_frames(core, key, pressed, index, completion, trace);
    pl_trace_frames(core, 0U, released, index, completion, trace);
}

static void pl_print_league_trace(
    const char *case_id, unsigned index,
    const struct PlLeagueInstructionTrace *trace)
{
    fprintf(stderr,
            "league instruction trace case=%s room=%s outcome=%u"
            " outcome_ord=%" PRIu64 " tag5=%08" PRIX32
            " tag5_ord=%" PRIu64 " proxy_goto=%08" PRIX32
            " proxy_ord=%" PRIu64 " target=%08" PRIX32
            " target_ord=%" PRIu64 " flag_ord=%" PRIu64 "\n",
            case_id, PL_LEAGUE[index].name, trace->outcome,
            trace->outcome_ordinal, PL_LEAGUE_TAG5_ROOT[index],
            trace->tag5_ordinal, PL_LEAGUE_PROXY_GOTO[index],
            trace->proxy_goto_ordinal, trace->completion_target,
            trace->completion_target_ordinal,
            trace->completion_flag_ordinal);
}

static void pl_complete_league_win(
    struct mCore *core, const char *case_id, unsigned index,
    uint16_t completion, struct PlLeagueInstructionTrace *trace)
{
    if (!s61_battle_active(core)
        || (read32(core, ADDR_BATTLE_TYPE_FLAGS)
            & WORLD_BATTLE_TYPE_TRAINER) == 0U)
        s61_die("League trace did not begin in a trainer battle");
    if (read8(core, PL_LEAGUE_PROXY_GOTO[index]) != 0x05U)
        s61_die("League proxy goto opcode drifted");
    uint32_t operand = PL_LEAGUE_PROXY_GOTO[index] + 1U;
    trace->completion_target = (uint32_t)read8(core, operand)
        | ((uint32_t)read8(core, operand + 1U) << 8U)
        | ((uint32_t)read8(core, operand + 2U) << 16U)
        | ((uint32_t)read8(core, operand + 3U) << 24U);
    if (trace->completion_target < 0x08000000U
        || trace->completion_target >= 0x0A000000U)
        s61_die("League proxy completion target is outside ROM");

    bool initialized = false;
    bool completed = false;
    world_phase = "gba-complete-league-battle-traced";
    for (unsigned pulse = 0U; pulse < 1200U; ++pulse) {
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            initialized = true;
        if (initialized && world_overworld(core)) {
            pl_trace_frames(core, 0U, 30U, index, completion, trace);
            if (pl_flag_direct(core, completion)
                && s61_field_terminal(core)
                && read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U) {
                completed = true;
                break;
            }
        }
        if (!initialized) {
            pl_trace_frames(core, 0U, 30U, index, completion, trace);
            if (pulse % 6U == 5U)
                pl_trace_pulse(core, WORLD_KEY_A, 2U, 30U,
                               index, completion, trace);
            continue;
        }
        bool handled_switch = false;
        for (unsigned bank = 0U; bank < 4U; bank += 2U) {
            if (read8(core, 0x02022B24U + bank * 0x200U)
                    != WORLD_BATTLE_COMMAND_CHOOSE_POKEMON)
                continue;
            if (read16(core, ADDR_BATTLE_MONS
                             + bank * BATTLE_MON_SIZE
                             + BATTLE_CORE_MON_HP) == 0U)
                s61_die("boosted League fixture unexpectedly required switch");
            pl_trace_pulse(core, WORLD_KEY_B, 2U, 30U,
                           index, completion, trace);
            handled_switch = true;
            break;
        }
        if (!handled_switch)
            pl_trace_pulse(core, WORLD_KEY_A, 2U,
                           BATTLE_CORE_MENU_INPUT_WAIT,
                           index, completion, trace);
    }
    core->setKeys(core, 0U);
    bool elite = PL_LEAGUE_TAG5_ROOT[index] != 0U;
    bool ordered = trace->outcome == WORLD_BATTLE_OUTCOME_WON
        && trace->outcome_ordinal != 0U
        && trace->proxy_goto_ordinal > trace->outcome_ordinal
        && trace->completion_target_ordinal > trace->proxy_goto_ordinal
        && trace->completion_flag_ordinal
            > trace->completion_target_ordinal;
    if (elite)
        ordered = ordered
            && trace->tag5_ordinal > trace->outcome_ordinal
            && trace->proxy_goto_ordinal > trace->tag5_ordinal;
    else
        ordered = ordered && trace->tag5_ordinal == 0U;
    if (!completed || !ordered) {
        pl_print_league_trace(case_id, index, trace);
        s61_die("League battle-resume instruction order is incomplete");
    }
    if ((elite
         && trace->completion_target == PL_LEAGUE_SOURCE_COMPLETION[index])
        || (!elite
            && trace->completion_target != PL_LEAGUE_SOURCE_COMPLETION[index])) {
        pl_print_league_trace(case_id, index, trace);
        s61_die(elite
            ? "Elite completion proxy still targets flag-only source tail"
            : "Champion negative-control completion target changed");
    }
    if (getenv("S61_TRACE_LEAGUE") != NULL)
        pl_print_league_trace(case_id, index, trace);
    struct S61FieldRoundtripResult field = s61_field_roundtrip(
        core, case_id, PL_GROUP, PL_LEAGUE[index].map);
    if (!s61_field_roundtrip_exact(&field))
        s61_die("traced League WIN did not recover START/B field input");
}

static unsigned pl_win_current_trainer(struct mCore *core,
                                       const char *directory,
                                       const char *case_id,
                                       const struct PlMap *map,
                                       struct PlLeagueEvidence *evidence)
{
    unsigned index = (unsigned)(map - PL_LEAGUE);
    if (index >= sizeof(PL_LEAGUE) / sizeof(PL_LEAGUE[0]))
        s61_die("League map is outside progression table");
    unsigned hits = pl_start_object_battle(
        core, directory, case_id, map, &evidence->walk_steps);
    uint16_t completion = (uint16_t)(
        PL_LEAGUE_FIRST_COMPLETE_FLAG + index);
    struct PlLeagueInstructionTrace trace = {0};
    pl_complete_league_win(
        core, case_id, index, completion, &trace);
    if (!pl_flag_direct(core, completion)
        || !pl_wait_field(core, map->map, NULL, true))
        s61_die("trainer post-battle owner did not commit completion");
    ++evidence->battle_resume_trace_cases;
    if (index < 4U)
        ++evidence->elite_completion_adapter_cases;
    else
        evidence->champion_no_geometry_control = true;
    return hits;
}

static void pl_assert_league_checkpoint_state(
    struct mCore *core, const char *case_id, uint8_t expected_map,
    unsigned completion_count, unsigned scene)
{
    pl_assert_map(core, case_id, expected_map);
    if (pl_flag(core, PL_LEAGUE_GATE_FLAG) != 1U
        || pl_var(core, PL_LEAGUE_SCENE_VAR) != scene)
        s61_die("League checkpoint gate/scene differs");
    for (unsigned index = 0U; index < 5U; ++index) {
        unsigned expected = index < completion_count ? 1U : 0U;
        if (pl_flag(core, (uint16_t)(PL_LEAGUE_FIRST_COMPLETE_FLAG + index))
                != expected)
            s61_die("League checkpoint completion set differs");
    }
}

static bool pl_checkpoint_continue(const char *rom_path, const char *save_path,
                                   const char *directory, const char *stem,
                                   uint8_t expected_map,
                                   unsigned completion_count, unsigned scene,
                                   struct PlCheckpointEvidence *checkpoint)
{
    struct PlMap map = PL_SAFE; map.map = expected_map;
    struct Fixture fixture = pl_fixture(stem, &map, 0U, 0U);
    struct mCore *fresh = s61_open_fresh(rom_path, save_path, &fixture);
    pl_assert_league_checkpoint_state(
        fresh, stem, expected_map, completion_count, scene);
    checkpoint->cold_continue = pl_save_position(fresh, stem);
    struct S61FieldRoundtripResult roundtrip = s61_field_roundtrip(
        fresh, stem, PL_GROUP, expected_map);
    if (!s61_field_roundtrip_exact(&roundtrip))
        s61_die("fresh Continue field START/B callback recovery failed");
    checkpoint->cold_framebuffer_hash = pl_framebuffer_rgb_fnv1a64(s61_video);
    char ppm_prefix[4096];
    pl_artifact_prefix(ppm_prefix, sizeof(ppm_prefix), directory, stem);
    bootstrap_write_ppm(ppm_prefix, s61_video);
    pl_close_to_exact_srm(fresh, save_path);
    return true;
}

static void pl_generate_safe(const char *rom_path, const char *save_path,
                             const char *case_id)
{
    struct Fixture safe = pl_fixture(case_id, &PL_SAFE, 11U, 9U);
    s61_generate(rom_path, save_path, &safe);
}

static void pl_league_full_chain(const char *rom_path, const char *directory,
                                 struct PlLeagueEvidence *evidence,
                                 struct PlCheckpointEvidence *checkpoint)
{
    char save_path[4096];
    pl_path(save_path, sizeof(save_path), directory,
            "league_full_chain", "srm");
    pl_generate_safe(rom_path, save_path, "league_full_chain");
    struct Fixture safe = pl_fixture("league_full_chain", &PL_SAFE, 11U, 9U);
    struct mCore *core = s61_open_fresh(rom_path, save_path, &safe);
    pl_prepare_league_state(core);
    pl_bootstrap_warp(core, "league_full_chain", 75U, 6U, 10U);
    pl_prepare_strong_party(core);
    if (pl_var(core, PL_LEAGUE_SCENE_VAR) != 1U)
        s61_die("Lorelei physical entry did not advance scene 0->1");

    for (unsigned index = 0U; index < 5U; ++index) {
        char case_id[64];
        int count = snprintf(case_id, sizeof(case_id),
                             "league-full-%s", PL_LEAGUE[index].name);
        if (count <= 0 || (size_t)count >= sizeof(case_id))
            s61_die("League case label formatting failed");
        if (pl_var(core, PL_LEAGUE_SCENE_VAR) != index + 1U)
            s61_die("League room scene sequence is not exact");
        evidence->owner_hits += pl_win_current_trainer(
            core, directory, case_id, &PL_LEAGUE[index], evidence);
        for (unsigned flag_index = 0U; flag_index < 5U; ++flag_index) {
            bool expected = flag_index <= index;
            unsigned actual = pl_flag(
                core, (uint16_t)(PL_LEAGUE_FIRST_COMPLETE_FLAG + flag_index));
            if (actual != (expected ? 1U : 0U)) {
                fprintf(stderr, "completion sequence room=%u flag=0x%04X"
                        " expected=%u actual=%u scene=%u\n",
                        index, PL_LEAGUE_FIRST_COMPLETE_FLAG + flag_index,
                        expected ? 1U : 0U, actual,
                        pl_var(core, PL_LEAGUE_SCENE_VAR));
                s61_die("League completion flag sequence is not exact");
            }
        }
        uint8_t destination = index < 4U
            ? PL_LEAGUE[index + 1U].map : PL_HALL.map;
        (void)pl_actual_warp(core, case_id, &PL_LEAGUE[index],
                             PL_LEAGUE[index].forward_warp,
                             destination, &evidence->walk_steps);
        if (index < 4U
            && pl_var(core, PL_LEAGUE_SCENE_VAR) != index + 2U)
            s61_die("next League room entry did not advance scene");
    }
    if (!s61_field_terminal(core)
        || pl_var(core, PL_LEAGUE_SCENE_VAR) != 5U)
        s61_die("Hall-of-Fame tag-3 owner did not return field control");
    pl_assert_league_checkpoint_state(
        core, "league_full_chain", PL_HALL.map, 5U, 5U);
    checkpoint->save_before = pl_save_position(core, "league_full_chain");
    if (!s61_normal_input_save(core))
        s61_die("full League chain START save failed");
    pl_close_to_exact_srm(core, save_path);
    (void)pl_checkpoint_continue(rom_path, save_path, directory,
                                 "league_full_chain", PL_HALL.map,
                                 5U, 5U, checkpoint);
}

static void pl_league_blackout_retry(
    const char *rom_path, const char *directory,
    struct PlLeagueEvidence *evidence,
    struct PlCheckpointEvidence *checkpoint)
{
    char save_path[4096];
    pl_path(save_path, sizeof(save_path), directory,
            "league_blackout_retry", "srm");
    pl_generate_safe(rom_path, save_path, "league_blackout_retry");
    struct Fixture safe = pl_fixture(
        "league_blackout_retry", &PL_SAFE, 11U, 9U);
    struct mCore *core = s61_open_fresh(rom_path, save_path, &safe);
    pl_prepare_league_state(core);
    uint8_t strong_party[BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE];
    for (unsigned byte = 0U; byte < sizeof(strong_party); ++byte)
        strong_party[byte] = read8(core, BOOTSTRAP_PLAYER_PARTY + byte);
    pl_prepare_weak_party(core);
    uint32_t save1 = world_save1(core, "league_blackout_retry");
    struct S61WarpSnapshot heal = s61_snapshot_warp(core, save1 + 0x1CU);
    pl_bootstrap_warp(core, "league_blackout_retry", 75U, 6U, 10U);
    if (pl_var(core, PL_LEAGUE_SCENE_VAR) != 1U)
        s61_die("blackout branch Lorelei entry scene mismatch");
    evidence->owner_hits += pl_start_object_battle(
        core, directory, "league-lorelei-loss", &PL_LEAGUE[0],
        &evidence->walk_steps);
    struct Fixture battle_fixture = pl_fixture(
        "league-lorelei-loss", &PL_LEAGUE[0], 0U, 0U);
    struct FixtureResult loss = {0};
    world_finish_battle(core, &battle_fixture, &loss, false);
    if (!loss.battle_completed
        || loss.battle_outcome != WORLD_BATTLE_OUTCOME_LOST)
        s61_die("weak party did not reach the natural trainer LOSS outcome");
    if (!pl_wait_field(core, heal.map, NULL, true))
        s61_die("trainer LOSS did not recover through blackout");
    save1 = world_save1(core, "league_blackout_retry");
    bool coordinate_matches = heal.x < 0 || heal.y < 0
        || (read16(core, save1) == (uint16_t)heal.x
            && read16(core, save1 + 2U) == (uint16_t)heal.y);
    if (read8(core, save1 + 4U) != heal.group
        || read8(core, save1 + 5U) != heal.map || !coordinate_matches)
        s61_die("blackout destination differs from the saved heal location");
    struct S61FieldRoundtripResult blackout = s61_field_roundtrip(
        core, "league-blackout-field", heal.group, heal.map);
    if (!s61_field_roundtrip_exact(&blackout)
        || pl_var(core, PL_LEAGUE_SCENE_VAR) != 1U
        || pl_flag(core, PL_LEAGUE_FIRST_COMPLETE_FLAG) != 0U)
        s61_die("blackout did not preserve scene high-water/absence of WIN");

    for (unsigned byte = 0U; byte < sizeof(strong_party); ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, strong_party[byte]);
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);
    pl_set_var(core, PL_REPEL_STEP_VAR, 0xFFFFU);
    pl_bootstrap_warp(core, "league_blackout_retry", 75U, 6U, 10U);
    pl_prepare_strong_party(core);
    if (pl_var(core, PL_LEAGUE_SCENE_VAR) != 1U)
        s61_die("actual Lorelei retry did not preserve high-water scene");
    evidence->owner_hits += pl_win_current_trainer(
        core, directory, "league-lorelei-retry",
        &PL_LEAGUE[0], evidence);
    if (pl_flag(core, PL_LEAGUE_FIRST_COMPLETE_FLAG) != 1U)
        s61_die("Lorelei retry WIN did not commit completion");
    (void)pl_actual_warp(core, "league-lorelei-retry", &PL_LEAGUE[0],
                         PL_LEAGUE[0].forward_warp, PL_LEAGUE[1].map,
                         &evidence->walk_steps);
    if (pl_var(core, PL_LEAGUE_SCENE_VAR) != 2U)
        s61_die("retry WIN did not permit actual Bruno entry");
    pl_assert_league_checkpoint_state(
        core, "league_blackout_retry", PL_LEAGUE[1].map, 1U, 2U);
    checkpoint->save_before = pl_save_position(
        core, "league_blackout_retry");
    if (!s61_normal_input_save(core))
        s61_die("blackout/retry START save failed");
    pl_close_to_exact_srm(core, save_path);
    (void)pl_checkpoint_continue(rom_path, save_path, directory,
                                 "league_blackout_retry", PL_LEAGUE[1].map,
                                 1U, 2U, checkpoint);
}

static void pl_probe_league(const char *rom_path, const char *directory)
{
    struct PlLeagueEvidence evidence = {0};
    struct PlCheckpointEvidence full_checkpoint = {0};
    struct PlCheckpointEvidence retry_checkpoint = {0};
    pl_league_full_chain(
        rom_path, directory, &evidence, &full_checkpoint);
    pl_league_blackout_retry(
        rom_path, directory, &evidence, &retry_checkpoint);
    if (evidence.walk_steps == 0U || evidence.owner_hits < 7U
        || evidence.battle_resume_trace_cases != 6U
        || evidence.elite_completion_adapter_cases != 5U
        || !evidence.champion_no_geometry_control)
        s61_die("League lifecycle evidence counters are incomplete");
    printf("{\"schema_version\":3,\"status\":\"PASS\","
           "\"case\":\"league_progression_lifecycle_complete\","
           "\"room_order\":[\"097/075\",\"097/076\",\"097/077\","
           "\"097/078\",\"097/079\",\"097/080\"],"
           "\"scene_var\":\"0x516C\","
           "\"scene_sequence_exact\":[1,2,3,4,5,5],"
           "\"completion_sequence_exact\":[\"0x1408\",\"0x1409\","
           "\"0x140A\",\"0x140B\",\"0x140C\"],"
           "\"trainer_battle_wins\":6,\"trainer_battle_losses\":1,"
           "\"blackout_exercised\":true,\"last_heal_match\":true,"
           "\"blackout_field_recovered\":true,"
           "\"blackout_scene_high_water_preserved\":true,"
           "\"completion_absent_after_loss\":true,"
           "\"actual_reentry_after_blackout\":true,"
           "\"retry_win_committed\":true,"
           "\"physical_room_warp_transitions\":6,"
           "\"actual_walk_steps\":%u,\"face_a_battle_cases\":7,"
           "\"owner_pc_cases\":7,\"owner_pc_hits\":%u,"
           "\"battle_resume_instruction_trace_cases\":6,"
           "\"elite_completion_adapter_cases\":5,"
           "\"champion_no_geometry_negative_control\":true,"
           "\"field_recovery_cases\":6,"
           "\"hall_of_fame_tag3_field_terminal\":true,"
           "\"checkpoint_positions\":{"
           "\"league_full_chain\":{"
           "\"save_before\":{\"x\":%u,\"y\":%u,\"warp_id\":%u},"
           "\"cold_continue\":{\"x\":%u,\"y\":%u,\"warp_id\":%u}},"
           "\"league_blackout_retry\":{"
           "\"save_before\":{\"x\":%u,\"y\":%u,\"warp_id\":%u},"
           "\"cold_continue\":{\"x\":%u,\"y\":%u,\"warp_id\":%u}}},"
           "\"checkpoint_framebuffer_fnv1a64\":{"
           "\"league_full_chain\":\"%016" PRIX64 "\","
           "\"league_blackout_retry\":\"%016" PRIX64 "\"},"
           "\"start_save_cases\":2,\"fresh_continue_cases\":2,"
           "\"bootstrap_stock_warp_calls\":3,"
           "\"direct_owner_or_script_calls\":0,"
           "\"failed\":0,\"untested\":0,\"warnings\":0}\n",
           evidence.walk_steps, evidence.owner_hits,
           full_checkpoint.save_before.x, full_checkpoint.save_before.y,
           full_checkpoint.save_before.warp_id,
           full_checkpoint.cold_continue.x,
           full_checkpoint.cold_continue.y,
           full_checkpoint.cold_continue.warp_id,
           retry_checkpoint.save_before.x,
           retry_checkpoint.save_before.y,
           retry_checkpoint.save_before.warp_id,
           retry_checkpoint.cold_continue.x,
           retry_checkpoint.cold_continue.y,
           retry_checkpoint.cold_continue.warp_id,
           full_checkpoint.cold_framebuffer_hash,
           retry_checkpoint.cold_framebuffer_hash);
}

static unsigned pl_metatile_behavior(struct mCore *core,
                                     uint16_t x, uint16_t y)
{
    uint32_t layout = read32(core, WORLD_MAP_HEADER);
    uint32_t width = read32(core, layout);
    uint32_t height = read32(core, layout + 4U);
    if (x >= width || y >= height)
        s61_die("metatile behavior coordinate outside layout");
    uint32_t blocks = read32(core, layout + 12U);
    unsigned metatile = read16(core, blocks + (y * width + x) * 2U) & 0x3FFU;
    uint32_t tileset = read32(core, layout + (metatile >= 640U ? 20U : 16U));
    unsigned local = metatile >= 640U ? metatile - 640U : metatile;
    uint32_t attributes = read32(core, tileset + 20U);
    return read32(core, attributes + local * 4U) & 0x1FFU;
}

static uint32_t pl_map_script_root(struct mCore *core, uint8_t group,
                                   uint8_t map, uint8_t tag)
{
    uint32_t groups = read32(core, 0x08054B0CU);
    uint32_t group_table = read32(core, groups + group * 4U);
    uint32_t header = read32(core, group_table + map * 4U);
    uint32_t table = read32(core, header + 8U);
    for (unsigned index = 0U; index < 12U; ++index) {
        uint32_t entry = table + index * 5U;
        uint8_t actual_tag = read8(core, entry);
        if (actual_tag == 0U) break;
        if (actual_tag == tag) {
            /* Map-script table entries are packed at five-byte strides.  A
             * busRead32 on entry+1 follows ARM unaligned-rotate semantics,
             * so decode the serialized pointer bytewise. */
            uint32_t root = (uint32_t)read8(core, entry + 1U)
                | ((uint32_t)read8(core, entry + 2U) << 8U)
                | ((uint32_t)read8(core, entry + 3U) << 16U)
                | ((uint32_t)read8(core, entry + 4U) << 24U);
            if (root < 0x08000000U || root >= 0x0A000000U)
                s61_die("map script root is outside ROM");
            return root;
        }
    }
    s61_die("required map script tag root is absent");
    return 0U;
}

static void pl_prepare_seafoam_player(struct mCore *core)
{
    pl_set_var(core, PL_REPEL_STEP_VAR, 0xFFFFU);
    pl_set_flag(core, PL_BADGE_4_FLAG, true);
    if (s61_call_synced(core, BATTLE_CORE_ADD_BAG_ITEM,
                        PL_HM03_SURF, 1U, 0U, 0U) == 0U
        || s61_call_synced(core, BATTLE_CORE_ADD_BAG_ITEM,
                           PL_HM04_STRENGTH, 1U, 0U, 0U) == 0U)
        s61_die("Seafoam HM fixture inventory preparation failed");
    s61_set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY,
                         WORLD_MON_DATA_MOVE1, PL_MOVE_STRENGTH);
    s61_set_mon_data_u32(core, BOOTSTRAP_PLAYER_PARTY, MON_DATA_PP1, 63U);
}

static void pl_route20_topology_reset(struct mCore *core,
                                      const char *directory,
                                      const char *case_id,
                                      struct PlSeafoamBranchResult *evidence)
{
    char artifact[4096];
    struct S61Capture capture = s61_new_capture(
        directory, case_id, artifact, sizeof(artifact));
    capture.event_root_script_pointer = pl_map_script_root(
        core, PL_ROUTE20_GROUP, PL_ROUTE20_MAP, 3U);
    pl_bootstrap_warp_group(core, case_id, PL_ROUTE20_GROUP, PL_ROUTE20_MAP,
                            60U, 8U, &capture);
    ++evidence->bootstrap_warps;
    if (capture.event_root_script_pointer_hits == 0U)
        s61_die("Route20 reset tag-3 owner PC was not observed");
    evidence->route20_owner_hits += capture.event_root_script_pointer_hits;
    const uint16_t visible[] = {
        PL_1F_BOULDER_1_HIDE, PL_1F_BOULDER_2_HIDE,
        PL_B3_SOURCE_HIDE, PL_B3_OBSTACLE_1_HIDE,
        PL_B3_SOURCE_2_HIDE, PL_B3_OBSTACLE_2_HIDE,
    };
    const uint16_t hidden[] = {
        PL_B1_BOULDER_1_HIDE, PL_B1_BOULDER_2_HIDE,
        PL_B2_BOULDER_1_HIDE, PL_B2_BOULDER_2_HIDE,
        PL_B3_ARRIVAL_1_HIDE, PL_B3_ARRIVAL_2_HIDE,
        PL_B4_BOULDER_1_HIDE, PL_B4_BOULDER_2_HIDE,
    };
    for (unsigned index = 0U;
         index < sizeof(visible) / sizeof(visible[0]); ++index) {
        if (pl_flag(core, visible[index]) != 0U
            || pl_flag_direct(core, visible[index]))
            s61_die("Route20 reset did not reveal a source boulder");
    }
    for (unsigned index = 0U;
         index < sizeof(hidden) / sizeof(hidden[0]); ++index) {
        if (pl_flag(core, hidden[index]) != 1U
            || !pl_flag_direct(core, hidden[index]))
            s61_die("Route20 reset did not hide a destination boulder");
    }
    if (pl_flag(core, PL_B3_STOPPED) != 0U
        || pl_flag(core, PL_B4_STOPPED) != 0U)
        s61_die("fresh Seafoam topology unexpectedly has a stopped latch");
}

static void pl_assert_pre_puzzle_topology(struct mCore *core,
                                          const char *phase)
{
    const uint16_t visible[] = {
        PL_1F_BOULDER_1_HIDE, PL_1F_BOULDER_2_HIDE,
        PL_B3_SOURCE_HIDE, PL_B3_OBSTACLE_1_HIDE,
        PL_B3_SOURCE_2_HIDE, PL_B3_OBSTACLE_2_HIDE,
    };
    const uint16_t hidden[] = {
        PL_B1_BOULDER_1_HIDE, PL_B1_BOULDER_2_HIDE,
        PL_B2_BOULDER_1_HIDE, PL_B2_BOULDER_2_HIDE,
        PL_B3_ARRIVAL_1_HIDE, PL_B3_ARRIVAL_2_HIDE,
        PL_B4_BOULDER_1_HIDE, PL_B4_BOULDER_2_HIDE,
    };
    for (unsigned index = 0U;
         index < sizeof(visible) / sizeof(visible[0]); ++index) {
        if (pl_flag(core, visible[index]) != 0U
            || pl_flag_direct(core, visible[index])) {
            fprintf(stderr, "pre-puzzle phase=%s visible flag=0x%04X"
                    " engine=%u direct=%u\n", phase, visible[index],
                    pl_flag(core, visible[index]),
                    pl_flag_direct(core, visible[index]) ? 1U : 0U);
            s61_die("pre-puzzle visible topology did not persist");
        }
    }
    for (unsigned index = 0U;
         index < sizeof(hidden) / sizeof(hidden[0]); ++index) {
        if (pl_flag(core, hidden[index]) != 1U
            || !pl_flag_direct(core, hidden[index])) {
            fprintf(stderr, "pre-puzzle phase=%s hidden flag=0x%04X"
                    " engine=%u direct=%u\n", phase, hidden[index],
                    pl_flag(core, hidden[index]),
                    pl_flag_direct(core, hidden[index]) ? 1U : 0U);
            s61_die("pre-puzzle hidden topology did not persist");
        }
    }
}

static unsigned pl_enable_strength(
    struct mCore *core, const char *directory, const char *case_id,
    const struct PlBoulderStage *stage, unsigned *walk_steps)
{
    struct S61Interaction source = {
        .group = PL_GROUP, .map = stage->map->map,
        .local_id = stage->local_id,
    };
    if (!s61_object_visible(core, &source)
        || pl_flag_direct(core, PL_SYS_USE_STRENGTH)
        || pl_flag(core, PL_SYS_USE_STRENGTH) != 0U)
        s61_die("Strength source/native flag precondition differs");
    uint16_t facing = pl_navigate_adjacent(
        core, case_id, stage->map, stage->start, walk_steps);
    uint32_t root = pl_object_script_root(
        core, stage->local_id, stage->start.x, stage->start.y);
    char artifact[4096];
    struct S61Capture strength = s61_new_capture(
        directory, case_id, artifact, sizeof(artifact));
    strength.event_root_script_pointer = root;
    strength.watched_instruction_pc = WORLD_FLAG_SET & ~1U;
    strength.lifecycle_flag_owner_address = world_save1(core, case_id)
        + WORLD_LEGACY_FLAGS_VARS_OFFSET + (PL_SYS_USE_STRENGTH >> 3U);
    strength.lifecycle_flag_mask = (uint8_t)(
        1U << (PL_SYS_USE_STRENGTH & 7U));
    write16(core, WORLD_SPECIAL_RESULT, 0xFFFFU);
    s61_pulse(core, facing, 2U, 10U, &strength);
    s61_pulse(core, WORLD_KEY_A, 2U, 20U, &strength);
    bool strength_set = false;
    for (unsigned pulse = 0U; pulse < 160U; ++pulse) {
        if (pl_flag_direct(core, PL_SYS_USE_STRENGTH)) {
            strength_set = true;
            if (s61_field_terminal(core)) break;
        }
        s61_pulse(core, WORLD_KEY_UP, 2U, 8U, &strength);
        s61_pulse(core, WORLD_KEY_A, 1U, 45U, &strength);
        if (pulse >= 1U && !pl_flag_direct(core, PL_SYS_USE_STRENGTH)
            && strength.count != 0U && s61_field_terminal(core))
            break;
    }
    bool driven = strength.event_root_script_pointer_hits != 0U
        && strength.watched_instruction_hits != 0U
        && strength.lifecycle_flag_set_observed
        && strength.event_first_root_ordinal != 0U
        && strength.lifecycle_first_flag_set_ordinal
            > strength.event_first_root_ordinal
        && strength_set && s61_field_terminal(core);
    if (!driven || pl_flag(core, PL_SYS_USE_STRENGTH) != 1U) {
        uint32_t save1 = world_save1(core, case_id);
        fprintf(stderr, "strength case=%s driven=%u root=%08" PRIX32
                " root_hits=%u native_set_pc_hits=%u transition=%u"
                " flag=%u map=%u/%u xy=%u,%u messages=%u\n",
                case_id, driven ? 1U : 0U, root,
                strength.event_root_script_pointer_hits,
                strength.watched_instruction_hits,
                strength.lifecycle_flag_set_observed ? 1U : 0U,
                pl_flag(core, PL_SYS_USE_STRENGTH),
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                strength.count);
        s61_die("actual direction+A/Yes did not enable Strength owner");
    }
    return strength.watched_instruction_hits;
}

static uint16_t pl_push_boulder_stage(
    struct mCore *core, const char *directory, const char *case_id,
    const struct PlBoulderStage *stage,
    struct PlSeafoamBranchResult *evidence)
{
    unsigned source_flag = pl_flag(core, stage->source_hide);
    unsigned destination_flag = pl_flag(core, stage->destination_hide);
    bool source_direct = pl_flag_direct(core, stage->source_hide);
    bool destination_direct = pl_flag_direct(core, stage->destination_hide);
    unsigned hole_behavior = pl_metatile_behavior(
        core, stage->hole.x, stage->hole.y);
    if (source_flag != 0U || source_direct
        || destination_flag != 1U || !destination_direct
        || hole_behavior != PL_FALL_WARP_BEHAVIOR) {
        fprintf(stderr, "boulder precondition case=%s local=%u"
                " source=0x%04X:%u/%u destination=0x%04X:%u/%u"
                " hole=%u,%u behavior=0x%03X expected=0x%03X\n",
                case_id, stage->local_id, stage->source_hide, source_flag,
                source_direct ? 1U : 0U,
                stage->destination_hide, destination_flag,
                destination_direct ? 1U : 0U,
                stage->hole.x, stage->hole.y, hole_behavior,
                PL_FALL_WARP_BEHAVIOR);
        s61_die("boulder source/destination/hole precondition differs");
    }
    evidence->strength_owner_hits += pl_enable_strength(
        core, directory, case_id, stage, &evidence->walk_steps);
    ++evidence->strength_cases;

    char artifact[4096];
    struct S61Capture push = s61_new_capture(
        directory, case_id, artifact, sizeof(artifact));
    push.watched_instruction_pc = PL_TRY_PUSH_BOULDER;
    struct PlPoint boulder = stage->start;
    uint16_t final_key = 0U;
    unsigned completed_steps = 0U;
    unsigned total_steps = 0U;
    for (unsigned segment = 0U; segment < stage->segment_count; ++segment)
        total_steps += stage->segments[segment].count;
    for (unsigned segment = 0U; segment < stage->segment_count; ++segment) {
        uint16_t key = stage->segments[segment].key;
        int dx = 0, dy = 0; pl_delta(key, &dx, &dy);
        int player_x = (int)boulder.x - dx;
        int player_y = (int)boulder.y - dy;
        if (player_x < 0 || player_y < 0)
            s61_die("boulder push stance is outside map");
        struct PlPoint stance = {
            (uint16_t)player_x, (uint16_t)player_y,
        };
        pl_navigate_exact(
            core, case_id, stage->map, stance, &evidence->walk_steps);
        for (unsigned step = 0U;
             step < stage->segments[segment].count; ++step) {
            uint32_t save1 = world_save1(core, case_id);
            uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
            if (!pl_walk_one(core, key, &x, &y,
                             &evidence->walk_steps, &push))
                s61_die("real direction input did not push authored boulder");
            boulder.x = (uint16_t)((int)boulder.x + dx);
            boulder.y = (uint16_t)((int)boulder.y + dy);
            ++completed_steps;
            ++evidence->push_steps;
            bool final = completed_steps == total_steps;
            if (!final) {
                struct S61Interaction object = {
                    .group = PL_GROUP, .map = stage->map->map,
                    .local_id = stage->local_id,
                };
                struct S61ObjectSnapshot snapshot = {0};
                s61_snapshot_object(core, &object, &snapshot);
                if (!snapshot.active || snapshot.invisible
                    || snapshot.current_x != (int16_t)boulder.x
                    || snapshot.current_y != (int16_t)boulder.y)
                    s61_die("runtime boulder object did not move one tile exactly");
            }
            final_key = key;
        }
    }
    if (!pl_same_point(boulder.x, boulder.y, &stage->hole)
        || pl_flag(core, stage->source_hide) != 1U
        || pl_flag(core, stage->destination_hide) != 0U
        || push.watched_instruction_hits == 0U)
        s61_die("boulder hole owner/hide-arrival flag transition differs");
    evidence->push_owner_hits += push.watched_instruction_hits;
    ++evidence->push_cases;
    ++evidence->topology_transitions;
    return final_key;
}

static struct PlFallResult pl_actual_fall_chain(
    struct mCore *core, const char *directory, const char *case_id,
    uint16_t key, uint8_t first_map, uint8_t final_map,
    bool require_motion, bool require_surf)
{
    char artifact[4096];
    struct S61Capture capture = s61_new_capture(
        directory, case_id, artifact, sizeof(artifact));
    capture.watched_instruction_pc = PL_FALL_WARP_EFFECT_7;
    uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    struct PlFallResult result = {0};
    bool final_coordinate_seen = false;
    uint16_t final_x = 0U, final_y = 0U;
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 14400U; ++frame) {
        s61_step_capture_frames(core, frame < 48U ? key : 0U, 1U, &capture);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != callback)
            result.callback_transition = true;
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (save1 < 0x02000000U || save1 >= 0x02040000U)
            continue;
        uint8_t group = read8(core, save1 + 4U);
        uint8_t map = read8(core, save1 + 5U);
        if (group == PL_GROUP && map == first_map)
            result.destination_seen = true;
        if ((read8(core, WORLD_PLAYER_AVATAR) & 8U) != 0U)
            result.surf_seen = true;
        if (group != PL_GROUP || map != final_map) {
            stable = 0U;
            continue;
        }
        uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
        if (!final_coordinate_seen) {
            final_x = x; final_y = y; final_coordinate_seen = true;
        } else if (x != final_x || y != final_y) {
            result.coordinate_motion = true;
            final_x = x; final_y = y;
        }
        bool terminal = s61_field_terminal(core)
            && read8(core, WORLD_FIELD_CONTROLS_LOCKED) == 0U;
        stable = terminal ? stable + 1U : 0U;
        if (stable >= 30U) break;
    }
    core->setKeys(core, 0U);
    result.owner_hits = capture.watched_instruction_hits;
    result.field_recovered = result.destination_seen
        && final_coordinate_seen && stable >= 30U;
    if (!result.destination_seen || !result.callback_transition
        || !result.field_recovered || result.owner_hits == 0U
        || (require_motion && !result.coordinate_motion)
        || (require_surf && !result.surf_seen)) {
        uint32_t save1 = world_save1(core, case_id);
        fprintf(stderr, "fall case=%s first=%u final=%u actual=%u/%u"
                " xy=%u,%u owner=%u callback=%u motion=%u surf=%u"
                " field=%u\n", case_id, first_map, final_map,
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                result.owner_hits, result.callback_transition ? 1U : 0U,
                result.coordinate_motion ? 1U : 0U,
                result.surf_seen ? 1U : 0U,
                result.field_recovered ? 1U : 0U);
        s61_die("physical hole/fall/current callback lifecycle is incomplete");
    }
    return result;
}

static struct PlFallResult pl_execute_boulder_stage(
    struct mCore *core, const char *directory, const char *case_id,
    const struct PlBoulderStage *stage, uint8_t first_map,
    uint8_t final_map, bool require_motion, bool require_surf,
    struct PlSeafoamBranchResult *evidence)
{
    uint16_t final_key = pl_push_boulder_stage(
        core, directory, case_id, stage, evidence);
    struct PlFallResult fall = pl_actual_fall_chain(
        core, directory, case_id, final_key, first_map, final_map,
        require_motion, require_surf);
    evidence->fall_owner_hits += fall.owner_hits;
    ++evidence->fall_cases;
    evidence->current_motion = evidence->current_motion
        || fall.coordinate_motion;
    evidence->surf_seen = evidence->surf_seen || fall.surf_seen;
    evidence->callback_chain = evidence->callback_chain
        || (fall.callback_transition && fall.field_recovered);
    if (pl_flag_direct(core, PL_SYS_USE_STRENGTH)
        || pl_flag(core, PL_SYS_USE_STRENGTH) != 0U)
        s61_die("fall/warp consumer did not clear native Strength flag");
    return fall;
}

static void pl_snapshot_b3_obstacles(struct mCore *core, const char *case_id)
{
    const struct {
        uint8_t local_id; int16_t x; int16_t y; uint16_t flag;
    } obstacles[] = {
        {3U, 13, 16, PL_B3_OBSTACLE_2_HIDE},
        {4U, 9, 16, PL_B3_OBSTACLE_1_HIDE},
    };
    for (unsigned index = 0U;
         index < sizeof(obstacles) / sizeof(obstacles[0]); ++index) {
        struct S61Interaction interaction = {
            .group = PL_GROUP, .map = PL_B3.map,
            .local_id = obstacles[index].local_id,
        };
        struct S61ObjectSnapshot snapshot = {0};
        s61_snapshot_object(core, &interaction, &snapshot);
        if (pl_flag(core, obstacles[index].flag) != 0U
            || !snapshot.active || snapshot.invisible
            || snapshot.current_x != obstacles[index].x
            || snapshot.current_y != obstacles[index].y) {
            fprintf(stderr, "obstacle case=%s local=%u active=%u hidden=%u"
                    " xy=%d,%d flag=%u\n", case_id,
                    obstacles[index].local_id, snapshot.active ? 1U : 0U,
                    snapshot.invisible ? 1U : 0U,
                    snapshot.current_x, snapshot.current_y,
                    pl_flag(core, obstacles[index].flag));
            s61_die("non-producer B3 obstacle moved or changed visibility");
        }
    }
}

static void pl_seafoam_exit_reentry(
    struct mCore *core, const char *case_id,
    struct PlSeafoamBranchResult *evidence, bool inspect_obstacles)
{
    if (!pl_actual_warp_any(
            core, case_id, &PL_B4, PL_B4_WARPS,
            sizeof(PL_B4_WARPS) / sizeof(PL_B4_WARPS[0]),
            PL_B3.map, &evidence->walk_steps))
        s61_die("Seafoam physical B4 exit route is unreachable");
    if (inspect_obstacles)
        pl_snapshot_b3_obstacles(core, case_id);
    if (!pl_actual_warp_any(
            core, case_id, &PL_B3, PL_B3_WARPS,
            sizeof(PL_B3_WARPS) / sizeof(PL_B3_WARPS[0]),
            PL_B4.map, &evidence->walk_steps))
        s61_die("Seafoam physical B4 re-entry route is unreachable");
}

static void pl_assert_seafoam_checkpoint_state(
    struct mCore *core, const char *case_id, bool stopped)
{
    const struct {
        uint16_t flag;
        bool active_value;
        bool stopped_value;
    } states[] = {
        {PL_SYS_USE_STRENGTH, false, false},
        {PL_1F_BOULDER_1_HIDE, false, true},
        {PL_1F_BOULDER_2_HIDE, false, true},
        {PL_B1_BOULDER_1_HIDE, true, true},
        {PL_B1_BOULDER_2_HIDE, true, true},
        {PL_B2_BOULDER_1_HIDE, true, true},
        {PL_B2_BOULDER_2_HIDE, true, true},
        {PL_B3_ARRIVAL_1_HIDE, true, false},
        {PL_B3_ARRIVAL_2_HIDE, true, false},
        {PL_B3_SOURCE_HIDE, true, true},
        {PL_B3_OBSTACLE_1_HIDE, false, false},
        {PL_B3_SOURCE_2_HIDE, false, true},
        {PL_B3_OBSTACLE_2_HIDE, false, false},
        {PL_B4_BOULDER_1_HIDE, false, false},
        {PL_B4_BOULDER_2_HIDE, true, false},
        {PL_B3_STOPPED, false, true},
        {PL_B4_STOPPED, false, true},
    };
    pl_assert_map(core, case_id, PL_B4.map);
    for (unsigned index = 0U;
         index < sizeof(states) / sizeof(states[0]); ++index) {
        bool expected = stopped
            ? states[index].stopped_value : states[index].active_value;
        if (pl_flag(core, states[index].flag) != (expected ? 1U : 0U)) {
            fprintf(stderr, "checkpoint case=%s flag=0x%04X"
                    " expected=%u actual=%u\n", case_id,
                    states[index].flag, expected ? 1U : 0U,
                    pl_flag(core, states[index].flag));
            s61_die("Seafoam checkpoint topology flag differs");
        }
    }
    if (pl_var(core, PL_B4_SCENE_VAR) != 0U)
        s61_die("Seafoam checkpoint B4 scene var is not quiescent");
}

static void pl_checkpoint_continue_seafoam(
    const char *rom_path, const char *save_path, const char *directory,
    const char *stem, bool stopped, uint32_t expected_layout,
    struct PlCheckpointEvidence *checkpoint)
{
    struct Fixture fixture = pl_fixture(stem, &PL_B4, 0U, 0U);
    struct mCore *fresh = s61_open_fresh(rom_path, save_path, &fixture);
    pl_assert_map(fresh, stem, PL_B4.map);
    checkpoint->cold_continue = pl_save_position(fresh, stem);
    pl_assert_seafoam_checkpoint_state(fresh, stem, stopped);
    if (read32(fresh, WORLD_MAP_HEADER) != expected_layout)
        s61_die("cold Continue did not restore exact Seafoam topology state");
    struct S61FieldRoundtripResult roundtrip = s61_field_roundtrip(
        fresh, stem, PL_GROUP, PL_B4.map);
    if (!s61_field_roundtrip_exact(&roundtrip))
        s61_die("Seafoam cold Continue START/B field recovery failed");
    checkpoint->cold_framebuffer_hash = pl_framebuffer_rgb_fnv1a64(s61_video);
    char ppm_prefix[4096];
    pl_artifact_prefix(ppm_prefix, sizeof(ppm_prefix), directory, stem);
    bootstrap_write_ppm(ppm_prefix, s61_video);
    pl_close_to_exact_srm(fresh, save_path);
}

static struct PlSeafoamBranchResult pl_seafoam_active_branch(
    const char *rom_path, const char *directory)
{
    const char *stem = "seafoam_active_current";
    char save_path[4096];
    pl_path(save_path, sizeof(save_path), directory, stem, "srm");
    pl_generate_safe(rom_path, save_path, stem);
    struct Fixture safe = pl_fixture(stem, &PL_SAFE, 11U, 9U);
    struct mCore *core = s61_open_fresh(rom_path, save_path, &safe);
    struct PlSeafoamBranchResult result = {0};
    pl_route20_topology_reset(core, directory, stem, &result);
    pl_bootstrap_warp(core, stem, PL_B3.map, 6U, 16U);
    ++result.bootstrap_warps;
    pl_assert_pre_puzzle_topology(core, "active-post-warp");
    pl_prepare_seafoam_player(core);
    pl_assert_pre_puzzle_topology(core, "active-post-player-setup");
    struct PlFallResult fall = pl_execute_boulder_stage(
        core, directory, "seafoam-active-b3-first", &PL_B3_FIRST_STAGE,
        PL_B4.map, PL_B4.map, true, true, &result);
    if (!fall.coordinate_motion || pl_flag(core, PL_B4_BOULDER_1_HIDE) != 0U
        || pl_flag(core, PL_B4_BOULDER_2_HIDE) != 1U
        || pl_flag(core, PL_B4_STOPPED) != 0U)
        s61_die("single physical B4 producer did not preserve active current");
    result.layout = read32(core, WORLD_MAP_HEADER);
    pl_seafoam_exit_reentry(core, stem, &result, true);
    if (pl_flag(core, PL_B4_STOPPED) != 0U
        || read32(core, WORLD_MAP_HEADER) != result.layout)
        s61_die("active Seafoam state/layout did not persist on re-entry");
    pl_assert_seafoam_checkpoint_state(core, stem, false);
    struct S61FieldRoundtripResult field = s61_field_roundtrip(
        core, stem, PL_GROUP, PL_B4.map);
    if (!s61_field_roundtrip_exact(&field))
        s61_die("active Seafoam field callback failed before START save");
    result.checkpoint.save_before = pl_save_position(core, stem);
    if (!s61_normal_input_save(core))
        s61_die("active Seafoam START save/field callback failed");
    pl_close_to_exact_srm(core, save_path);
    pl_checkpoint_continue_seafoam(
        rom_path, save_path, directory, stem, false, result.layout,
        &result.checkpoint);
    return result;
}

static struct PlSeafoamBranchResult pl_seafoam_stopped_branch(
    const char *rom_path, const char *directory)
{
    const char *stem = "seafoam_stopped_current";
    char save_path[4096];
    pl_path(save_path, sizeof(save_path), directory, stem, "srm");
    pl_generate_safe(rom_path, save_path, stem);
    struct Fixture safe = pl_fixture(stem, &PL_SAFE, 11U, 9U);
    struct mCore *core = s61_open_fresh(rom_path, save_path, &safe);
    struct PlSeafoamBranchResult result = {0};
    pl_route20_topology_reset(core, directory, stem, &result);
    pl_bootstrap_warp(core, stem, PL_SEAFOAM_1F.map, 23U, 12U);
    ++result.bootstrap_warps;
    pl_assert_pre_puzzle_topology(core, "stopped-post-warp");
    pl_prepare_seafoam_player(core);
    pl_assert_pre_puzzle_topology(core, "stopped-post-player-setup");

    for (unsigned index = 0U; index < 3U; ++index) {
        uint8_t first = index == 0U ? PL_SEAFOAM_B1.map
            : index == 1U ? PL_SEAFOAM_B2.map : PL_B3.map;
        uint8_t final = index == 2U ? PL_B4.map : first;
        (void)pl_execute_boulder_stage(
            core, directory, PL_UPPER_FIRST[index].name,
            &PL_UPPER_FIRST[index], first, final,
            index == 2U, index == 2U, &result);
    }
    if (pl_flag(core, PL_B3_ARRIVAL_1_HIDE) != 0U
        || pl_flag(core, PL_B3_ARRIVAL_2_HIDE) != 1U
        || pl_flag(core, PL_B3_STOPPED) != 0U)
        s61_die("first upper chain did not leave B3 current active");
    pl_bootstrap_warp(core, stem, PL_SEAFOAM_1F.map, 33U, 9U);
    ++result.bootstrap_warps;
    for (unsigned index = 0U; index < 3U; ++index) {
        uint8_t destination = index == 0U ? PL_SEAFOAM_B1.map
            : index == 1U ? PL_SEAFOAM_B2.map : PL_B3.map;
        (void)pl_execute_boulder_stage(
            core, directory, PL_UPPER_SECOND[index].name,
            &PL_UPPER_SECOND[index], destination, destination,
            false, false, &result);
    }
    if (pl_flag(core, PL_B3_ARRIVAL_1_HIDE) != 0U
        || pl_flag(core, PL_B3_ARRIVAL_2_HIDE) != 0U
        || pl_flag(core, PL_B3_STOPPED) != 1U
        || pl_flag(core, PL_B4_STOPPED) != 0U)
        s61_die("two upper physical chains did not stop B3 current exactly");
    result.b3_stopped = true;
    pl_snapshot_b3_obstacles(core, stem);

    (void)pl_execute_boulder_stage(
        core, directory, "seafoam-stopped-b3-first", &PL_B3_FIRST_STAGE,
        PL_B4.map, PL_B4.map, true, true, &result);
    if (pl_flag(core, PL_B4_BOULDER_1_HIDE) != 0U
        || pl_flag(core, PL_B4_BOULDER_2_HIDE) != 1U
        || pl_flag(core, PL_B4_STOPPED) != 0U)
        s61_die("first B3 producer did not leave B4 current active");
    if (!pl_actual_warp_any(
            core, stem, &PL_B4, PL_B4_WARPS,
            sizeof(PL_B4_WARPS) / sizeof(PL_B4_WARPS[0]),
            PL_B3.map, &result.walk_steps))
        s61_die("first B4 producer could not physically return to B3");
    pl_snapshot_b3_obstacles(core, stem);

    (void)pl_execute_boulder_stage(
        core, directory, "seafoam-stopped-b3-second", &PL_B3_SECOND_STAGE,
        PL_B4.map, PL_B4.map, false, true, &result);
    if (pl_flag(core, PL_B4_BOULDER_1_HIDE) != 0U
        || pl_flag(core, PL_B4_BOULDER_2_HIDE) != 0U
        || pl_flag(core, PL_B4_STOPPED) != 1U)
        s61_die("two B3 physical producers did not stop B4 current exactly");
    result.b4_stopped = true;
    result.layout = read32(core, WORLD_MAP_HEADER);
    pl_seafoam_exit_reentry(core, stem, &result, true);
    result.obstacle_controls_preserved = true;
    if (pl_flag(core, PL_B3_STOPPED) != 1U
        || pl_flag(core, PL_B4_STOPPED) != 1U
        || read32(core, WORLD_MAP_HEADER) != result.layout)
        s61_die("stopped Seafoam latches/layout did not persist on re-entry");
    pl_assert_seafoam_checkpoint_state(core, stem, true);
    struct S61FieldRoundtripResult field = s61_field_roundtrip(
        core, stem, PL_GROUP, PL_B4.map);
    if (!s61_field_roundtrip_exact(&field))
        s61_die("stopped Seafoam field callback failed before START save");
    result.checkpoint.save_before = pl_save_position(core, stem);
    if (!s61_normal_input_save(core))
        s61_die("stopped Seafoam START save/field callback failed");
    pl_close_to_exact_srm(core, save_path);
    pl_checkpoint_continue_seafoam(
        rom_path, save_path, directory, stem, true, result.layout,
        &result.checkpoint);
    return result;
}

static void pl_probe_seafoam(const char *rom_path, const char *directory)
{
    struct PlSeafoamBranchResult active = pl_seafoam_active_branch(
        rom_path, directory);
    struct PlSeafoamBranchResult stopped = pl_seafoam_stopped_branch(
        rom_path, directory);
    unsigned walk_steps = active.walk_steps + stopped.walk_steps;
    unsigned strength_hits = active.strength_owner_hits
        + stopped.strength_owner_hits;
    unsigned fall_hits = active.fall_owner_hits + stopped.fall_owner_hits;
    unsigned push_hits = active.push_owner_hits + stopped.push_owner_hits;
    unsigned strength_cases = active.strength_cases + stopped.strength_cases;
    unsigned fall_cases = active.fall_cases + stopped.fall_cases;
    unsigned push_cases = active.push_cases + stopped.push_cases;
    unsigned push_steps = active.push_steps + stopped.push_steps;
    unsigned topology_transitions = active.topology_transitions
        + stopped.topology_transitions;
    unsigned bootstrap_warps = active.bootstrap_warps
        + stopped.bootstrap_warps;
    unsigned route20_owner_hits = active.route20_owner_hits
        + stopped.route20_owner_hits;
    if (active.layout == stopped.layout || walk_steps == 0U
        || strength_cases != 9U || fall_cases != 9U || push_cases != 9U
        || push_steps != 23U || topology_transitions != 9U
        || bootstrap_warps != 5U || strength_hits < strength_cases
        || fall_hits < fall_cases || push_hits < push_cases
        || route20_owner_hits < 2U
        || !active.current_motion || !active.surf_seen
        || !stopped.b3_stopped || !stopped.b4_stopped
        || !stopped.obstacle_controls_preserved)
        s61_die("Seafoam lifecycle evidence counters/layouts are incomplete");
    printf("{\"schema_version\":3,\"status\":\"PASS\","
           "\"case\":\"seafoam_progression_lifecycle_complete\","
           "\"static_maps_83_through_87\":5,\"runtime_maps_b3_b4\":2,"
           "\"flag_state_variants\":2,"
           "\"runtime_maps_1f_through_b4\":5,"
           "\"route20_reset_owner_cases\":2,"
           "\"route20_reset_owner_pc_hits\":%u,"
           "\"upper_b3_physical_chain_cases\":2,"
           "\"distinct_b3_b4_physical_chain_cases\":2,"
           "\"active_current_control_chain_cases\":1,"
           "\"actual_strength_prompt_cases\":9,"
           "\"strength_zero_to_one_transition_cases\":9,"
           "\"native_strength_clear_after_fall_cases\":9,"
           "\"actual_boulder_push_cases\":9,"
           "\"actual_boulder_push_steps\":23,"
           "\"actual_hole_fall_cases\":9,"
           "\"topology_hide_arrival_transition_cases\":9,"
           "\"fall_owner_pc_cases\":9,\"fall_owner_pc_hits\":%u,"
           "\"push_owner_pc_cases\":9,\"push_owner_pc_hits\":%u,"
           "\"strength_owner_pc_cases\":9,"
           "\"strength_owner_pc_hits\":%u,"
           "\"surf_observed_cases\":4,"
           "\"active_current_motion_cases\":3,"
           "\"active_current_motion_observed\":true,"
           "\"b3_current_stop_observed\":true,"
           "\"b4_current_stop_observed\":true,"
           "\"stopped_current_flag_observed\":true,"
           "\"non_producer_obstacle_controls\":2,"
           "\"topology_direct_flag_writes\":0,"
           "\"active_stopped_layouts_distinct\":true,"
           "\"physical_exit_reentry_cases\":2,"
           "\"checkpoint_positions\":{"
           "\"seafoam_active_current\":{"
           "\"save_before\":{\"x\":%u,\"y\":%u,\"warp_id\":%u},"
           "\"cold_continue\":{\"x\":%u,\"y\":%u,\"warp_id\":%u}},"
           "\"seafoam_stopped_current\":{"
           "\"save_before\":{\"x\":%u,\"y\":%u,\"warp_id\":%u},"
           "\"cold_continue\":{\"x\":%u,\"y\":%u,\"warp_id\":%u}}},"
           "\"checkpoint_framebuffer_fnv1a64\":{"
           "\"seafoam_active_current\":\"%016" PRIX64 "\","
           "\"seafoam_stopped_current\":\"%016" PRIX64 "\"},"
           "\"start_save_cases\":2,\"fresh_continue_cases\":2,"
           "\"field_callback_chain_cases\":2,"
           "\"actual_walk_steps\":%u,"
           "\"bootstrap_stock_warp_calls\":5,"
           "\"direct_owner_or_script_calls\":0,"
           "\"failed\":0,\"untested\":0,\"warnings\":0}\n",
           route20_owner_hits, fall_hits, push_hits, strength_hits,
           active.checkpoint.save_before.x,
           active.checkpoint.save_before.y,
           active.checkpoint.save_before.warp_id,
           active.checkpoint.cold_continue.x,
           active.checkpoint.cold_continue.y,
           active.checkpoint.cold_continue.warp_id,
           stopped.checkpoint.save_before.x,
           stopped.checkpoint.save_before.y,
           stopped.checkpoint.save_before.warp_id,
           stopped.checkpoint.cold_continue.x,
           stopped.checkpoint.cold_continue.y,
           stopped.checkpoint.cold_continue.warp_id,
           active.checkpoint.cold_framebuffer_hash,
           stopped.checkpoint.cold_framebuffer_hash,
           walk_steps);
}

int main(int argc, char **argv)
{
    if (argc != 4 || (strcmp(argv[3], "league") != 0
        && strcmp(argv[3], "seafoam") != 0)) {
        fprintf(stderr, "usage: %s ROM WORK_DIRECTORY league|seafoam\n",
                argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0700) != 0 && errno != EEXIST) {
        perror("mkdir"); return 2;
    }
    s61_case_name = argv[3]; bootstrap_phase = s61_case_name;
    s61_artifact_directory = argv[2];
    struct mLogger logger = {.log = s61_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    /* Generated saves carry libmGBA's deterministic RTC footer.  Permit only
     * its exact reopen notice; every other warning/error remains fatal. */
    s61_allow_savedata_time_offset_notice = true;
    if (strcmp(argv[3], "league") == 0)
        pl_probe_league(argv[1], argv[2]);
    else
        pl_probe_seafoam(argv[1], argv[2]);
    s61_allow_savedata_time_offset_notice = false;
    if (log_problem_count != 0U)
        s61_die("mGBA emitted warning/error diagnostics");
    return 0;
}
