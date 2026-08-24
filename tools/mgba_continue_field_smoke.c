/*
 * Natural-Continue field probe for the Codex reception save.
 *
 * This deliberately reuses the proven iPad bootstrap's title/Continue path
 * but never generates or saves data.  Each direction is tested in a fresh
 * core so a broken field state cannot contaminate the next observation.
 */
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

enum {
    CONTINUE_SCRIPT_CONTEXT_ENABLED = 0x08069219U,
    CONTINUE_PLAYER_AVATAR = 0x02036FACU,
    CONTINUE_OBJECT_EVENTS = 0x02036E38U,
    CONTINUE_OBJECT_EVENT_SIZE = 0x24U,
    CONTINUE_OBJECT_EVENT_COUNT = 16U,
    CONTINUE_KEY_RIGHT = 0x10U,
    CONTINUE_KEY_LEFT = 0x20U,
    CONTINUE_KEY_UP = 0x40U,
    CONTINUE_KEY_DOWN = 0x80U,
};

struct ContinueSnapshot {
    uint32_t callback;
    uint32_t save1;
    uint32_t save2;
    uint32_t script_enabled;
    uint32_t map_view_hash;
    uint32_t map_view_distinct;
    uint32_t object_hash;
    uint16_t x;
    uint16_t y;
    uint8_t map_group;
    uint8_t map_number;
    uint8_t avatar_flags;
    uint8_t running_state;
};

struct ContinueDirectionResult {
    struct ContinueSnapshot initial;
    struct ContinueSnapshot first;
    struct ContinueSnapshot second;
    bool first_moved;
    bool second_moved;
};

static uint32_t continue_hash_bytes(struct mCore *core, uint32_t address,
                                    unsigned size)
{
    uint32_t hash = UINT32_C(2166136261);
    for (unsigned index = 0U; index < size; ++index) {
        hash ^= read8(core, address + index);
        hash *= UINT32_C(16777619);
    }
    return hash;
}

static void continue_live_map_view(struct mCore *core, uint32_t save1,
                                   uint32_t *hash_out,
                                   uint32_t *distinct_out)
{
    uint32_t width = read32(core, BOOTSTRAP_VMAP);
    uint32_t height = read32(core, BOOTSTRAP_VMAP + 4U);
    uint32_t map = read32(core, BOOTSTRAP_VMAP + 8U);
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    uint16_t values[BOOTSTRAP_MAP_VIEW_COUNT];
    uint32_t hash = UINT32_C(2166136261);
    uint32_t distinct = 0U;
    unsigned count = 0U;
    if (map < 0x02000000U || map >= 0x02040000U || (map & 1U)
        || width < BOOTSTRAP_MAP_VIEW_WIDTH
        || height < BOOTSTRAP_MAP_VIEW_HEIGHT
        || (uint32_t)x + BOOTSTRAP_MAP_VIEW_WIDTH > width
        || (uint32_t)y + BOOTSTRAP_MAP_VIEW_HEIGHT > height)
        return;
    for (unsigned row = 0U; row < BOOTSTRAP_MAP_VIEW_HEIGHT; ++row) {
        for (unsigned column = 0U; column < BOOTSTRAP_MAP_VIEW_WIDTH;
             ++column) {
            uint16_t live = read16(
                core, map + 2U * (width * ((uint32_t)y + row)
                                + (uint32_t)x + column));
            bool first = true;
            for (unsigned prior = 0U; prior < count; ++prior) {
                if (values[prior] == live) {
                    first = false;
                    break;
                }
            }
            values[count++] = live;
            distinct += first;
            hash ^= (uint8_t)live;
            hash *= UINT32_C(16777619);
            hash ^= (uint8_t)(live >> 8U);
            hash *= UINT32_C(16777619);
        }
    }
    *hash_out = hash;
    *distinct_out = distinct;
}

static struct ContinueSnapshot continue_snapshot(struct mCore *core)
{
    struct ContinueSnapshot result = {0};
    result.callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
    result.save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    result.save2 = read32(core, BOOTSTRAP_SAVE_BLOCK2_PTR);
    result.script_enabled = call_preserving(
        core, CONTINUE_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U);
    result.object_hash = continue_hash_bytes(
        core, CONTINUE_OBJECT_EVENTS,
        CONTINUE_OBJECT_EVENT_SIZE * CONTINUE_OBJECT_EVENT_COUNT);
    result.avatar_flags = read8(core, CONTINUE_PLAYER_AVATAR);
    result.running_state = read8(core, CONTINUE_PLAYER_AVATAR + 2U);
    if (result.save1 >= 0x02000000U && result.save1 < 0x02040000U
        && !(result.save1 & 3U)) {
        result.x = read16(core, result.save1);
        result.y = read16(core, result.save1 + 2U);
        result.map_group = read8(core, result.save1 + 4U);
        result.map_number = read8(core, result.save1 + 5U);
    }
    continue_live_map_view(core, result.save1,
                           &result.map_view_hash, &result.map_view_distinct);
    return result;
}

static bool continue_attempt_tile(struct mCore *core, uint16_t key,
                                  uint16_t start_x, uint16_t start_y)
{
    for (unsigned pulse = 0U; pulse < 24U; ++pulse) {
        run_key_frames(core, key, 2U);
        run_key_frames(core, 0U, 4U);
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (save1 >= 0x02000000U && save1 < 0x02040000U
            && !(save1 & 3U)
            && (read16(core, save1) != start_x
                || read16(core, save1 + 2U) != start_y)) {
            run_key_frames(core, 0U, 90U);
            return true;
        }
    }
    run_key_frames(core, 0U, 90U);
    return false;
}

static struct ContinueDirectionResult continue_probe_direction(
    const char *rom_path, const char *save_path, uint16_t key,
    color_t *video, bool render_initial, const char *image_prefix)
{
    struct ContinueDirectionResult result = {0};
    struct mCore *core = bootstrap_open_core(rom_path, save_path, video);
    bootstrap_continue_to_field(core);
    result.initial = continue_snapshot(core);
    if (render_initial)
        bootstrap_write_ppm(image_prefix, video);
    result.first_moved = continue_attempt_tile(
        core, key, result.initial.x, result.initial.y);
    result.first = continue_snapshot(core);
    result.second_moved = continue_attempt_tile(
        core, key, result.first.x, result.first.y);
    result.second = continue_snapshot(core);
    bootstrap_close_core(core);
    return result;
}

static void continue_print_snapshot(const struct ContinueSnapshot *snapshot)
{
    printf("{\"callback\":\"%08" PRIx32 "\",\"script\":%" PRIu32
           ",\"map\":\"%u/%u\",\"x\":%u,\"y\":%u,"
           "\"map_view_hash\":\"%08" PRIx32 "\","
           "\"map_view_distinct\":%" PRIu32
           ",\"object_hash\":\"%08" PRIx32 "\","
           "\"avatar_flags\":%u,\"running_state\":%u}",
           snapshot->callback, snapshot->script_enabled,
           snapshot->map_group, snapshot->map_number,
           snapshot->x, snapshot->y, snapshot->map_view_hash,
           snapshot->map_view_distinct,
           snapshot->object_hash, snapshot->avatar_flags,
           snapshot->running_state);
}

int main(int argc, char **argv)
{
    static const struct {
        const char *name;
        uint16_t key;
    } directions[] = {
        {"right", CONTINUE_KEY_RIGHT},
        {"left", CONTINUE_KEY_LEFT},
        {"down", CONTINUE_KEY_DOWN},
    };
    struct ContinueDirectionResult results[3];
    color_t *video;
    unsigned stable_two_step_paths = 0U;
    if (argc != 4) {
        fprintf(stderr, "usage: %s ROM SAVE IMAGE_PREFIX\n", argv[0]);
        return 2;
    }
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    video = calloc(240U * 160U, sizeof(*video));
    if (!video)
        bootstrap_die("framebuffer allocation failed");
    for (unsigned index = 0U; index < 3U; ++index) {
        memset(video, 0, 240U * 160U * sizeof(*video));
        bootstrap_phase = directions[index].name;
        results[index] = continue_probe_direction(
            argv[1], argv[2], directions[index].key, video,
            index == 0U, argv[3]);
        bool stable = results[index].first_moved
            && results[index].second_moved
            && results[index].second.callback == BOOTSTRAP_CB2_OVERWORLD
            && results[index].second.script_enabled == 0U;
        stable_two_step_paths += stable;
    }
    free(video);
    printf("{\"schema_version\":1,\"status\":\"%s\","
           "\"stable_two_step_paths\":%u,\"directions\":[",
           stable_two_step_paths != 0U ? "PASS" : "FAIL",
           stable_two_step_paths);
    for (unsigned index = 0U; index < 3U; ++index) {
        if (index != 0U)
            putchar(',');
        printf("{\"name\":\"%s\",\"first_moved\":%s,"
               "\"second_moved\":%s,\"initial\":",
               directions[index].name,
               results[index].first_moved ? "true" : "false",
               results[index].second_moved ? "true" : "false");
        continue_print_snapshot(&results[index].initial);
        printf(",\"first\":");
        continue_print_snapshot(&results[index].first);
        printf(",\"second\":");
        continue_print_snapshot(&results[index].second);
        putchar('}');
    }
    printf("],\"warnings\":%u}\n", log_problem_count);
    return stable_two_step_paths != 0U && log_problem_count == 0U ? 0 : 1;
}
