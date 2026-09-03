/*
 * Stage62 Wisdom Cave story/puzzle E2E.
 *
 * Fixture construction uses audited stock calls, but every cave transition,
 * puzzle trigger, story trigger, battle, fossil interaction, and menu save is
 * reached with ordinary GBA keys.  Save states are used only to discover a
 * route through the one-way ledges; every discovered segment is replayed from
 * its untouched segment-start snapshot before it is accepted as evidence.
 */
#define WORLD_BATTLE_MENU_INPUT_WAIT 40U
#define WORLD_RUNTIME_ENTRY_POINT mgba_world_runtime_input_e2e_embedded_main
#include "mgba_world_runtime_input_e2e.c"
#undef WORLD_RUNTIME_ENTRY_POINT

enum {
    SC_VAR_GET = 0x0806DD5DU,
    SC_VAR_SET = 0x0806DD79U,
    SC_FLAG_CLEAR = 0x0806DE9DU,
    SC_SCENE_VAR = 0x4071U,
    SC_REPEL_STEP_VAR = 0x4020U,
    SC_PUZZLE_FLAG = 0x110FU,
    SC_DH_HIDE_FLAG = 0x1110U,
    SC_RIVAL_HIDE_FLAG = 0x1111U,
    SC_DIGLETT_HIDE_FLAG = 0x110EU,
    SC_FOSSIL_FLAG = 0x1113U,
    SC_ROOT_FOSSIL = 286U,
    SC_RIVAL_TRAINER = 360U,
    SC_MAP_HEADER = 0x02036D30U,
    SC_EXPANDED_FLAG_RAM = 0x0203B0E8U,
    SC_EXPANDED_FLAG_FIRST = 0x0900U,
    SC_EXPANDED_FLAG_END = 0x1900U,
    SC_START_MENU_CALLBACK = 0x02037024U,
    SC_START_MENU_INPUT = 0x0806EA75U,
    SC_START_MENU_SAVE_CALLBACK = 0x0806EDB9U,
    SC_START_MENU_CURSOR = 0x02037028U,
    SC_START_MENU_COUNT = 0x02037029U,
    SC_START_MENU_ORDER = 0x0203702AU,
    SC_START_MENU_SAVE_ACTION = 4U,
    SC_KEY_START = 8U,
    SC_MAX_NODES = 1024U,
    SC_MAX_PATH = 1024U,
};

struct ScNode {
    void *state;
    int parent;
    uint16_t key;
    uint16_t x;
    uint16_t y;
    uint16_t scene;
    uint8_t elevation;
    uint8_t puzzle_flag;
    uint8_t mechanism_mask;
    uint8_t trainer_mask;
};

struct ScRoute {
    uint16_t keys[SC_MAX_PATH];
    unsigned count;
    unsigned explored_nodes;
    uint8_t mechanism_mask;
};

static const struct Fixture SC_FIXTURE = {
    "wisdom_cave_story", FIXTURE_DIALOGUE,
    3U, 21U, 15U, 57U, WORLD_KEY_UP,
    0U, 0U, SC_RIVAL_TRAINER, 1U,
};

static uint8_t sc_last_battle_bit;
static bool sc_replaying_route;

static uint16_t sc_var(struct mCore *core, uint16_t id)
{
    if (id < 0x4000U || id >= 0x4100U)
        world_die(SC_FIXTURE.name, "stock variable ID is out of range");
    return read16(core, world_save1(core, SC_FIXTURE.name)
                        + 0x1000U + (uint32_t)(id - 0x4000U) * 2U);
}

static bool sc_flag(struct mCore *core, uint16_t id)
{
    if (id >= 0x4000U)
        world_die(SC_FIXTURE.name, "stock flag ID is out of range");
    uint32_t address = id >= SC_EXPANDED_FLAG_FIRST
        && id < SC_EXPANDED_FLAG_END
        ? SC_EXPANDED_FLAG_RAM
            + ((uint32_t)(id - SC_EXPANDED_FLAG_FIRST) >> 3U)
        : world_save1(core, SC_FIXTURE.name)
            + 0x0EE0U + ((uint32_t)id >> 3U);
    uint8_t raw = read8(core, address);
    return (raw & (uint8_t)(1U << (id & 7U))) != 0U;
}

static void sc_set_flag(struct mCore *core, uint16_t id, bool set)
{
    (void)call_preserving(
        core, set ? WORLD_FLAG_SET : SC_FLAG_CLEAR, id, 0U, 0U, 0U);
    if (sc_flag(core, id) != set)
        world_die(SC_FIXTURE.name, "fixture flag preparation failed");
}

static void sc_set_var(struct mCore *core, uint16_t id, uint16_t value)
{
    (void)call_preserving(core, SC_VAR_SET, id, value, 0U, 0U);
    if (sc_var(core, id) != value)
        world_die(SC_FIXTURE.name, "fixture variable preparation failed");
}

static uint8_t sc_player_elevation(struct mCore *core)
{
    uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
    if (object_id >= 16U)
        return 0xFFU;
    return read8(core, WORLD_OBJECT_EVENTS + object_id * 0x24U + 0x0BU)
        & 0x0FU;
}

static uint32_t sc_active_object(struct mCore *core, uint8_t local_id)
{
    for (unsigned index = 0U; index < 16U; ++index) {
        uint32_t object = WORLD_OBJECT_EVENTS + index * 0x24U;
        if ((read8(core, object) & 1U)
            && read8(core, object + 8U) == local_id
            && read8(core, object + 9U) == 73U
            && read8(core, object + 10U) == 1U)
            return object;
    }
    return 0U;
}

static bool sc_field_ready(struct mCore *core, uint8_t group, uint8_t map)
{
    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U))
        return false;
    uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
    if (object_id >= 16U
        || !(read8(core, WORLD_OBJECT_EVENTS + object_id * 0x24U) & 1U))
        return false;
    return world_overworld(core) && !world_script_enabled(core)
        && read8(core, save1 + 4U) == group
        && read8(core, save1 + 5U) == map
        && read8(core, WORLD_PLAYER_AVATAR
                       + WORLD_PLAYER_RUNNING_STATE_OFFSET) == 0U
        && read8(core, WORLD_PLAYER_AVATAR
                       + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET) == 0U;
}

static void sc_prepare_save(const char *rom_path, const char *save_path)
{
    world_generate_save(
        rom_path, save_path, &SC_FIXTURE, SC_FIXTURE.x, SC_FIXTURE.y);
    struct mCore *core = bootstrap_open_core(rom_path, save_path, NULL);
    world_continue(core, &SC_FIXTURE);
    world_wait_player_ready(core, &SC_FIXTURE);
    sc_set_var(core, SC_SCENE_VAR, 6U);
    sc_set_var(core, SC_REPEL_STEP_VAR, 0xFFFFU);
    sc_set_flag(core, SC_PUZZLE_FLAG, false);
    sc_set_flag(core, SC_DH_HIDE_FLAG, false);
    sc_set_flag(core, SC_RIVAL_HIDE_FLAG, false);
    sc_set_flag(core, SC_DIGLETT_HIDE_FLAG, true);
    sc_set_flag(core, SC_FOSSIL_FLAG, false);
    bootstrap_prepare_save_map_view(core);
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        world_die(SC_FIXTURE.name, "prepared two-generation save failed");
    bootstrap_close_core(core);
}

static void sc_enter_b1f(struct mCore *core, struct FixtureResult *result)
{
    world_wait_player_ready(core, &SC_FIXTURE);
    world_take_warp(core, &SC_FIXTURE, result, WORLD_KEY_UP, 1U, 36U);
    world_walk_one(core, &SC_FIXTURE, result, WORLD_KEY_RIGHT);
    world_walk_one(core, &SC_FIXTURE, result, WORLD_KEY_RIGHT);
    world_take_warp(core, &SC_FIXTURE, result, WORLD_KEY_UP, 1U, 73U);
    if (!sc_field_ready(core, 1U, 73U))
        world_die(SC_FIXTURE.name, "north entrance did not settle on B1F");
    if (sc_var(core, SC_SCENE_VAR) != 6U
        || sc_flag(core, SC_PUZZLE_FLAG)
        || read16(core, WORLD_TRAINER_OPPONENT_A) == SC_RIVAL_TRAINER)
        world_die(SC_FIXTURE.name,
                  "rival event triggered before the B1F puzzle");
    if (getenv("SC_TRACE") != NULL)
        fprintf(stderr, "B1F entry temp0=%u scene=%u elevation=%u"
                " events=%08" PRIX32 " coords=%u/%08" PRIX32 "\n",
                sc_var(core, 0x4000U), sc_var(core, SC_SCENE_VAR),
                sc_player_elevation(core),
                read32(core, SC_MAP_HEADER + 4U),
                read8(core, read32(core, SC_MAP_HEADER + 4U) + 2U),
                read32(core, read32(core, SC_MAP_HEADER + 4U) + 12U));
    uint32_t rival = sc_active_object(core, 1U);
    if (rival != 0U
        && (read16(core, rival + 0x10U) != 4U + WORLD_FIELD_BORDER
            || read16(core, rival + 0x12U) != 11U + WORLD_FIELD_BORDER)) {
        fprintf(stderr, "B1F objects:");
        for (unsigned index = 0U; index < 16U; ++index) {
            uint32_t object = WORLD_OBJECT_EVENTS + index * 0x24U;
            if (read8(core, object) & 1U)
                fprintf(stderr, " %u=%u@%u/%u:%u,%u", index,
                        read8(core, object + 8U),
                        read8(core, object + 10U),
                        read8(core, object + 9U),
                        read16(core, object + 0x10U),
                        read16(core, object + 0x12U));
        }
        fputc('\n', stderr);
        world_die(SC_FIXTURE.name,
                  "loaded rival actor differs from the original B1F origin");
    }
}

static void sc_delta(uint16_t key, int *dx, int *dy)
{
    *dx = key == WORLD_KEY_RIGHT ? 1 : key == WORLD_KEY_LEFT ? -1 : 0;
    *dy = key == WORLD_KEY_DOWN ? 1 : key == WORLD_KEY_UP ? -1 : 0;
}

static uint8_t sc_trainer_mask(struct mCore *core)
{
    static const uint16_t trainers[] = {351U, 352U, 353U, 378U};
    uint8_t mask = 0U;
    for (unsigned index = 0U;
         index < sizeof(trainers) / sizeof(trainers[0]); ++index) {
        if (sc_flag(core, (uint16_t)(0x0500U + trainers[index])))
            mask |= (uint8_t)(1U << index);
    }
    return mask;
}

static bool sc_puzzle_trainer(uint16_t trainer)
{
    return trainer == 351U || trainer == 352U
        || trainer == 353U || trainer == 378U;
}

static uint8_t sc_puzzle_trainer_bit(uint16_t trainer)
{
    if (trainer == 351U) return 1U;
    if (trainer == 352U) return 2U;
    if (trainer == 353U) return 4U;
    if (trainer == 378U) return 8U;
    return 0U;
}

static bool sc_step_and_settle(
    struct mCore *core, uint16_t key, uint8_t *mask, bool reject_story)
{
    sc_last_battle_bit = 0U;
    bool trace = getenv("SC_TRACE") != NULL;
    uint32_t save1 = world_save1(core, SC_FIXTURE.name);
    uint16_t start_x = read16(core, save1);
    uint16_t start_y = read16(core, save1 + 2U);
    uint16_t old_x = start_x;
    uint16_t old_y = start_y;
    int dx = 0, dy = 0;
    sc_delta(key, &dx, &dy);
    int entered_x = (int)start_x + dx;
    int entered_y = (int)start_y + dy;
    bool puzzle_flag_before = sc_flag(core, SC_PUZZLE_FLAG);
    if (reject_story && sc_var(core, SC_SCENE_VAR) == 7U
        && entered_x == 7 && entered_y == 5)
        return false;

    for (unsigned frame = 0U; frame < 90U; ++frame) {
        run_key_frames(core, key, 1U);
        save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (save1 < 0x02000000U || save1 >= 0x02040000U
            || (save1 & 3U))
            break;
        old_x = read16(core, save1);
        old_y = read16(core, save1 + 2U);
        if (old_x != start_x || old_y != start_y
            || !world_overworld(core) || world_script_enabled(core)
            || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U)
            break;
    }
    core->setKeys(core, 0U);
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 7200U; ++frame) {
        save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (save1 >= 0x02000000U && save1 < 0x02040000U
            && (read8(core, save1 + 4U) != 1U
                || read8(core, save1 + 5U) != 73U)
            && (read8(core, save1 + 4U) != 0U
                || read8(core, save1 + 5U) != 0U)) {
            if (trace) fprintf(stderr,
                               "step %u,%u key=%u changed map to %u/%u:%u,%u\n",
                               start_x, start_y, key,
                               read8(core, save1 + 4U),
                               read8(core, save1 + 5U),
                               read16(core, save1),
                               read16(core, save1 + 2U));
            return false;
        }
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || (!world_overworld(core)
                && read8(core, ADDR_BATTLERS_COUNT) != 0U)) {
            uint16_t trainer = read16(core, WORLD_TRAINER_OPPONENT_A);
            if (!sc_puzzle_trainer(trainer)) {
                if (trace) fprintf(stderr,
                                   "step %u,%u key=%u unexpected battle %u\n",
                                   start_x, start_y, key, trainer);
                return false;
            }
            uint8_t trainer_bit = sc_puzzle_trainer_bit(trainer);
            struct Fixture battle_fixture = SC_FIXTURE;
            struct FixtureResult battle_result = {0};
            battle_fixture.trainer = trainer;
            battle_fixture.flag = (uint16_t)(0x0500U + trainer);
            world_finish_battle(
                core, &battle_fixture, &battle_result, false);
            if (!battle_result.battle_completed
                || battle_result.battle_outcome != 1U)
                world_die(SC_FIXTURE.name,
                          "puzzle trainer battle did not finish as a win");
            sc_last_battle_bit |= trainer_bit;
            stable = 0U;
            continue;
        }
        if (reject_story && world_script_enabled(core)
            && read16(core, save1) == 7U && read16(core, save1 + 2U) == 5U
            && sc_var(core, SC_SCENE_VAR) == 7U)
            return false;
        if (sc_field_ready(core, 1U, 73U)) {
            if (++stable >= 120U)
                break;
        } else {
            stable = 0U;
            uint16_t advance = world_script_enabled(core)
                && frame % 90U < 2U ? WORLD_KEY_A : 0U;
            run_key_frames(core, advance, 1U);
        }
    }
    core->setKeys(core, 0U);
    if (stable < 120U) {
        if (trace) fprintf(stderr,
                           "step %u,%u key=%u timeout callback=%08" PRIX32
                           " lock=%u pos=%u,%u run=%u/%u\n",
                           start_x, start_y, key,
                           read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                           world_script_enabled(core) ? 1U : 0U,
                           read16(core, save1), read16(core, save1 + 2U),
                           read8(core, WORLD_PLAYER_AVATAR
                                      + WORLD_PLAYER_RUNNING_STATE_OFFSET),
                           read8(core, WORLD_PLAYER_AVATAR
                                      + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET));
        return false;
    }
    save1 = world_save1(core, SC_FIXTURE.name);
    uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
    if (entered_x == 19 && entered_y == 14
        && ((!puzzle_flag_before && x == 27U && y == 7U)
            || (puzzle_flag_before && x == 8U && y == 10U)))
        *mask |= 1U;
    if (entered_x == 27 && entered_y == 7 && x == 19U && y == 14U)
        *mask |= 2U;
    if (entered_x == 8 && entered_y == 10 && x == 27U && y == 7U)
        *mask |= 4U;
    bool moved = x != start_x || y != start_y;
    if (trace) fprintf(stderr,
                       "step %u,%u key=%u -> %u,%u moved=%u scene=%u"
                       " elev=%u flag=%u mask=%u\n",
                       start_x, start_y, key, x, y, moved ? 1U : 0U,
                       sc_var(core, SC_SCENE_VAR), sc_player_elevation(core),
                       sc_flag(core, SC_PUZZLE_FLAG) ? 1U : 0U, *mask);
    return moved;
}

static bool sc_node_dominated(
    const struct ScNode *nodes, unsigned count, const struct ScNode *candidate)
{
    for (unsigned index = 0U; index < count; ++index) {
        const struct ScNode *node = &nodes[index];
        if (node->x == candidate->x && node->y == candidate->y
            && node->scene == candidate->scene
            && node->elevation == candidate->elevation
            && node->puzzle_flag == candidate->puzzle_flag
            && node->trainer_mask == candidate->trainer_mask
            && (node->mechanism_mask & candidate->mechanism_mask)
                == candidate->mechanism_mask)
            return true;
    }
    return false;
}

static unsigned sc_node_path(
    const struct ScNode *nodes, unsigned index, uint16_t *keys)
{
    unsigned count = 0U;
    for (int cursor = (int)index; nodes[cursor].parent >= 0;
         cursor = nodes[cursor].parent) {
        if (count >= SC_MAX_PATH)
            world_die(SC_FIXTURE.name, "route path bound exhausted");
        keys[count++] = nodes[cursor].key;
    }
    for (unsigned left = 0U, right = count == 0U ? 0U : count - 1U;
         left < right; ++left, --right) {
        uint16_t key = keys[left];
        keys[left] = keys[right];
        keys[right] = key;
    }
    return count;
}

static struct ScRoute sc_find_route(
    struct mCore *core, uint16_t target_x, uint16_t target_y,
    uint8_t required_mask, bool reject_story)
{
    struct ScNode nodes[SC_MAX_NODES] = {{0}};
    size_t state_size = core->stateSize(core);
    void *replay_root = malloc(state_size);
    if (replay_root == NULL || !core->saveState(core, replay_root))
        world_die(SC_FIXTURE.name, "route replay root capture failed");
    static const uint16_t search_trainers[] = {351U, 352U, 353U, 378U};
    for (unsigned index = 0U;
         index < sizeof(search_trainers) / sizeof(search_trainers[0]); ++index)
        sc_set_flag(core, (uint16_t)(0x0500U + search_trainers[index]), true);
    nodes[0].state = malloc(state_size);
    if (nodes[0].state == NULL || !core->saveState(core, nodes[0].state))
        world_die(SC_FIXTURE.name, "route root state capture failed");
    uint32_t save1 = world_save1(core, SC_FIXTURE.name);
    nodes[0].parent = -1;
    nodes[0].x = read16(core, save1);
    nodes[0].y = read16(core, save1 + 2U);
    nodes[0].scene = sc_var(core, SC_SCENE_VAR);
    nodes[0].elevation = sc_player_elevation(core);
    nodes[0].puzzle_flag = sc_flag(core, SC_PUZZLE_FLAG) ? 1U : 0U;
    nodes[0].trainer_mask = sc_trainer_mask(core);
    unsigned count = 1U, head = 0U;
    sc_replaying_route = false;
    int goal = -1;
    static const uint16_t keys[] = {
        WORLD_KEY_DOWN, WORLD_KEY_LEFT, WORLD_KEY_RIGHT, WORLD_KEY_UP,
    };
    while (head < count && goal < 0) {
        if (getenv("SC_TRACE") != NULL && head % 25U == 0U)
            fprintf(stderr, "route progress head=%u count=%u\n",
                    head, count);
        const struct ScNode base = nodes[head];
        for (unsigned direction = 0U;
             direction < sizeof(keys) / sizeof(keys[0]); ++direction) {
            if (!core->loadState(core, base.state))
                world_die(SC_FIXTURE.name, "route branch state restore failed");
            struct ScNode candidate = {0};
            candidate.parent = (int)head;
            candidate.key = keys[direction];
            candidate.mechanism_mask = base.mechanism_mask;
            if (!sc_step_and_settle(
                    core, candidate.key, &candidate.mechanism_mask,
                    reject_story))
                continue;
            save1 = world_save1(core, SC_FIXTURE.name);
            candidate.x = read16(core, save1);
            candidate.y = read16(core, save1 + 2U);
            candidate.elevation = sc_player_elevation(core);
            if (count >= SC_MAX_NODES)
                world_die(SC_FIXTURE.name, "route search node bound exhausted");
            candidate.state = malloc(state_size);
            if (candidate.state == NULL
                || !core->saveState(core, candidate.state))
                world_die(SC_FIXTURE.name, "route branch state capture failed");
            candidate.scene = sc_var(core, SC_SCENE_VAR);
            candidate.puzzle_flag = sc_flag(core, SC_PUZZLE_FLAG) ? 1U : 0U;
            candidate.trainer_mask =
                (uint8_t)(base.trainer_mask | sc_last_battle_bit);
            if (candidate.x == base.x && candidate.y == base.y
                && candidate.scene == base.scene
                && candidate.puzzle_flag == base.puzzle_flag
                && candidate.trainer_mask == base.trainer_mask) {
                free(candidate.state);
                continue;
            }
            if (sc_node_dominated(nodes, count, &candidate)) {
                free(candidate.state);
                continue;
            }
            nodes[count] = candidate;
            if (candidate.x == target_x && candidate.y == target_y
                && (candidate.mechanism_mask & required_mask) == required_mask)
                goal = (int)count;
            ++count;
            if (goal >= 0)
                break;
        }
        ++head;
    }
    if (goal < 0) {
        fprintf(stderr,
                "route search failed target=%u,%u mask=%u nodes=%u\n",
                target_x, target_y, required_mask, count);
        for (unsigned index = 0U; index < count; ++index)
            fprintf(stderr,
                    " node[%u]=%u,%u scene=%u elev=%u flag=%u mask=%u trainers=%u\n",
                    index, nodes[index].x, nodes[index].y,
                    nodes[index].scene, nodes[index].elevation,
                    nodes[index].puzzle_flag, nodes[index].mechanism_mask,
                    nodes[index].trainer_mask);
        world_die(SC_FIXTURE.name, "normal-input puzzle route not found");
    }
    struct ScRoute route = {.explored_nodes = count};
    route.count = sc_node_path(
        nodes, (unsigned)goal, route.keys);
    route.mechanism_mask = nodes[goal].mechanism_mask;
    if (!core->loadState(core, replay_root))
        world_die(SC_FIXTURE.name, "route replay root restore failed");
    free(replay_root);
    for (unsigned index = 0U; index < count; ++index)
        free(nodes[index].state);
    uint8_t replay_mask = 0U;
    sc_replaying_route = true;
    for (unsigned index = 0U; index < route.count; ++index) {
        if (!sc_step_and_settle(
                core, route.keys[index], &replay_mask, reject_story))
            world_die(SC_FIXTURE.name, "discovered route did not replay");
    }
    sc_replaying_route = false;
    save1 = world_save1(core, SC_FIXTURE.name);
    if (read16(core, save1) != target_x || read16(core, save1 + 2U) != target_y
        || (replay_mask & required_mask) != required_mask)
        world_die(SC_FIXTURE.name, "route replay ended at wrong state");
    route.mechanism_mask = replay_mask;
    return route;
}

static void sc_append_route(struct ScRoute *route,
                            const struct ScRoute *segment)
{
    if (route->count + segment->count > SC_MAX_PATH)
        world_die(SC_FIXTURE.name, "combined puzzle route bound exhausted");
    memcpy(&route->keys[route->count], segment->keys,
           segment->count * sizeof(segment->keys[0]));
    route->count += segment->count;
    route->explored_nodes += segment->explored_nodes;
    route->mechanism_mask |= segment->mechanism_mask;
}

static bool sc_normal_input_save(struct mCore *core)
{
    if (!world_overworld(core) || world_script_enabled(core))
        return false;
    world_pulse(core, SC_KEY_START, 2U, 120U);
    if (read32(core, SC_START_MENU_CALLBACK) != SC_START_MENU_INPUT)
        return false;
    uint8_t count = read8(core, SC_START_MENU_COUNT);
    uint8_t cursor = read8(core, SC_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count)
        return false;
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, SC_START_MENU_ORDER + index)
                == SC_START_MENU_SAVE_ACTION) {
            target = index;
            break;
        }
    }
    if (target >= count)
        return false;
    unsigned down = (unsigned)(target + count - cursor) % count;
    unsigned up = (unsigned)(cursor + count - target) % count;
    uint16_t key = down <= up ? WORLD_KEY_DOWN : WORLD_KEY_UP;
    unsigned steps = down <= up ? down : up;
    for (unsigned step = 0U; step < steps; ++step)
        world_pulse(core, key, 2U, 30U);
    if (read8(core, SC_START_MENU_CURSOR) != target)
        return false;
    world_pulse(core, WORLD_KEY_A, 2U, 120U);
    bool callback_seen = false;
    for (unsigned prompt = 0U; prompt < 32U; ++prompt) {
        if (read32(core, SC_START_MENU_CALLBACK)
                == SC_START_MENU_SAVE_CALLBACK)
            callback_seen = true;
        if (callback_seen && world_overworld(core)
            && !world_script_enabled(core)) {
            run_key_frames(core, 0U, 180U);
            return world_overworld(core) && !world_script_enabled(core);
        }
        world_pulse(core, WORLD_KEY_A, 2U, 180U);
    }
    return false;
}

static bool sc_rival_moved_from(
    struct mCore *core, uint16_t start_x, uint16_t start_y)
{
    uint32_t rival = sc_active_object(core, 1U);
    return rival != 0U
        && (read16(core, rival + 0x10U) != start_x
            || read16(core, rival + 0x12U) != start_y);
}

static void sc_run_story(
    struct mCore *core, struct FixtureResult *result, bool *rival_moved)
{
    uint32_t rival = sc_active_object(core, 1U);
    if (rival == 0U)
        world_die(SC_FIXTURE.name, "rival missing immediately before story");
    uint16_t rival_x = read16(core, rival + 0x10U);
    uint16_t rival_y = read16(core, rival + 0x12U);
    uint32_t save1 = world_save1(core, SC_FIXTURE.name);
    uint16_t x = read16(core, save1), y = read16(core, save1 + 2U);
    if (x != 8U || y != 5U || sc_var(core, SC_SCENE_VAR) != 7U)
        world_die(SC_FIXTURE.name, "story approach state differs");
    world_phase = "wisdom-story-coordinate-input";
    (void)world_walk_to_new_tile(core, WORLD_KEY_LEFT, &x, &y, result);
    bool battle_started = false;
    for (unsigned pulse = 0U; pulse < 240U; ++pulse) {
        if (sc_rival_moved_from(core, rival_x, rival_y))
            *rival_moved = true;
        if (read16(core, WORLD_TRAINER_OPPONENT_A) == SC_RIVAL_TRAINER
            && (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
                || read8(core, ADDR_BATTLERS_COUNT) != 0U
                || !world_overworld(core))) {
            battle_started = true;
            break;
        }
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
    }
    if (!battle_started || !*rival_moved)
        world_die(SC_FIXTURE.name,
                  "coord 9 did not move rival and start trainer 360");
    world_finish_battle(core, &SC_FIXTURE, result, false);
    for (unsigned pulse = 0U;
         pulse < 120U && !sc_field_ready(core, 1U, 73U); ++pulse) {
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
    }
    if (!sc_field_ready(core, 1U, 73U)
        || sc_var(core, SC_SCENE_VAR) != 8U
        || !sc_flag(core, SC_DH_HIDE_FLAG)
        || !sc_flag(core, SC_RIVAL_HIDE_FLAG)
        || !sc_flag(core, SC_DIGLETT_HIDE_FLAG)
        || sc_active_object(core, 1U) != 0U
        || sc_active_object(core, 2U) != 0U
        || sc_active_object(core, 3U) != 0U
        || sc_active_object(core, 4U) != 0U)
        world_die(SC_FIXTURE.name,
                  "story actor removal/final state differs");
}

static void sc_take_south_exit(
    struct mCore *core, struct FixtureResult *result,
    struct ScRoute *route)
{
    *route = sc_find_route(core, 4U, 20U, 0U, false);
    world_take_warp(core, &SC_FIXTURE, result, WORLD_KEY_UP, 1U, 38U);
    if (!sc_field_ready(core, 1U, 38U))
        world_die(SC_FIXTURE.name, "south exit did not reach map 1/38");
}

static void sc_receive_fossil(
    struct mCore *core, struct FixtureResult *result)
{
    if (call_preserving(core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
                        SC_ROOT_FOSSIL, 1U, 0U, 0U) != 0U
        || sc_flag(core, SC_FOSSIL_FLAG))
        world_die(SC_FIXTURE.name, "fossil was already acquired");
    world_walk_one(core, &SC_FIXTURE, result, WORLD_KEY_DOWN);
    world_walk_one(core, &SC_FIXTURE, result, WORLD_KEY_LEFT);
    world_walk_one(core, &SC_FIXTURE, result, WORLD_KEY_LEFT);
    world_pulse(core, WORLD_KEY_UP, 1U, 8U);
    world_pulse(core, WORLD_KEY_A, 2U, 90U);
    ++result->key_pulses;
    if (!world_wait_script_release(core, result)
        || call_preserving(core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
                           SC_ROOT_FOSSIL, 1U, 0U, 0U) != 1U
        || !sc_flag(core, SC_FOSSIL_FLAG))
        world_die(SC_FIXTURE.name,
                  "elder did not grant and commit the Root Fossil");
}

static void sc_verify_reloaded(struct mCore *core)
{
    if (!sc_field_ready(core, 1U, 38U)
        || sc_var(core, SC_SCENE_VAR) != 8U
        || !sc_flag(core, SC_DH_HIDE_FLAG)
        || !sc_flag(core, SC_RIVAL_HIDE_FLAG)
        || !sc_flag(core, SC_DIGLETT_HIDE_FLAG)
        || !sc_flag(core, SC_FOSSIL_FLAG)
        || call_preserving(core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
                           SC_ROOT_FOSSIL, 1U, 0U, 0U) != 1U)
        world_die(SC_FIXTURE.name,
                  "fresh Continue did not preserve cave/fossil state");
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM WORK_DIRECTORY\n", argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0700) != 0 && errno != EEXIST) {
        perror("mkdir");
        return 2;
    }
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    bootstrap_phase = SC_FIXTURE.name;
    char save_path[4096];
    if (snprintf(save_path, sizeof(save_path), "%s/%s.srm",
                 argv[2], SC_FIXTURE.name) <= 0)
        world_die(SC_FIXTURE.name, "save path formatting failed");
    sc_prepare_save(argv[1], save_path);

    memset(world_video, 0, sizeof(world_video));
    struct mCore *core = bootstrap_open_core(argv[1], save_path, world_video);
    world_continue(core, &SC_FIXTURE);
    struct FixtureResult result = {.natural_continue = true};
    sc_enter_b1f(core, &result);
    struct ScRoute puzzle = {0};
    struct ScRoute segment = sc_find_route(core, 27U, 7U, 1U, true);
    sc_append_route(&puzzle, &segment);
    segment = sc_find_route(core, 19U, 14U, 2U, true);
    sc_append_route(&puzzle, &segment);
    segment = sc_find_route(core, 27U, 7U, 5U, true);
    sc_append_route(&puzzle, &segment);
    segment = sc_find_route(core, 8U, 5U, 0U, true);
    sc_append_route(&puzzle, &segment);
    if ((puzzle.mechanism_mask & 7U) != 7U)
        world_die(SC_FIXTURE.name, "puzzle route omitted a teleport mechanism");
    if (sc_var(core, SC_SCENE_VAR) != 7U
        || read16(core, WORLD_TRAINER_OPPONENT_A) == SC_RIVAL_TRAINER)
        world_die(SC_FIXTURE.name,
                  "puzzle completion did not stop before coord 9");
    bool rival_moved = false;
    sc_run_story(core, &result, &rival_moved);
    struct ScRoute exit_route = {0};
    sc_take_south_exit(core, &result, &exit_route);
    sc_receive_fossil(core, &result);
    if (!sc_normal_input_save(core) || !sc_normal_input_save(core))
        world_die(SC_FIXTURE.name, "normal-input two-generation save failed");
    bootstrap_close_core(core);

    struct Fixture reload = SC_FIXTURE;
    reload.group = 1U;
    reload.map = 38U;
    core = bootstrap_open_core(argv[1], save_path, world_video);
    world_continue(core, &reload);
    world_wait_player_ready(core, &reload);
    sc_verify_reloaded(core);
    world_pulse(core, SC_KEY_START, 2U, 120U);
    bool start_menu_after_reload =
        read32(core, SC_START_MENU_CALLBACK) == SC_START_MENU_INPUT;
    if (start_menu_after_reload)
        world_pulse(core, WORLD_KEY_B, 2U, 180U);
    bool field_after_reload = start_menu_after_reload
        && sc_field_ready(core, 1U, 38U);
    bootstrap_close_core(core);
    if (!field_after_reload || log_problem_count != 0U)
        world_die(SC_FIXTURE.name,
                  "post-Continue field/menu or mGBA diagnostics failed");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"case\":\"wisdom_cave_story\","
        "\"north_entrance_to_b1f_by_keys\":true,"
        "\"pre_puzzle_rival_battle_absent\":true,"
        "\"puzzle_route_key_steps\":%u,"
        "\"puzzle_search_nodes\":%u,"
        "\"teleport_mechanism_mask\":%u,"
        "\"three_teleport_holes_traversed\":true,"
        "\"ledge_and_coordinate_progression_to_scene_7\":true,"
        "\"coord_9_story_triggered_by_key\":true,"
        "\"rival_actor_movement_observed\":%s,"
        "\"rival_trainer_id\":%u,"
        "\"rival_battle_completed\":%s,"
        "\"story_actor_ids_removed\":[1,2,3,4],"
        "\"story_scene_after\":8,"
        "\"south_exit_route_key_steps\":%u,"
        "\"south_exit_to_map_1_38\":true,"
        "\"root_fossil_item_id\":%u,"
        "\"root_fossil_received_from_elder_by_keys\":true,"
        "\"normal_start_menu_save_generations\":2,"
        "\"fresh_core_continue\":true,"
        "\"post_reload_start_menu_and_field\":true,"
        "\"warnings\":0}\n",
        puzzle.count, puzzle.explored_nodes, puzzle.mechanism_mask,
        rival_moved ? "true" : "false", SC_RIVAL_TRAINER,
        result.battle_completed ? "true" : "false",
        exit_route.count, SC_ROOT_FOSSIL);
    return 0;
}
