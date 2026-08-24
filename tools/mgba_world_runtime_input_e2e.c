/*
 * Stage52 world runtime input E2E.
 *
 * Each fixture is created from a natural new game and stock warp/save, then
 * reopened in a fresh core through the title-screen Continue path.  All
 * interaction, sight, message, battle, and encounter transitions after that
 * point use only GBA keys.  Direct calls only prepare saves or read results.
 */
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

#include <sys/stat.h>

enum {
    WORLD_SCRIPT_CONTEXT_ENABLED = 0x08069219U,
    WORLD_FLAG_GET = 0x0806DEC5U,
    WORLD_MAP_GRID_FIELD = 0x08058805U,
    WORLD_MAP_GRID_COLLISION = 0x08058681U,
    WORLD_TRAINER_OPPONENT_A = 0x020385E2U,
    WORLD_OBJECT_EVENTS = 0x02036E38U,
    WORLD_KEY_A = 1U,
    WORLD_KEY_B = 2U,
    WORLD_KEY_RIGHT = 16U,
    WORLD_KEY_LEFT = 32U,
    WORLD_KEY_UP = 64U,
    WORLD_KEY_DOWN = 128U,
    WORLD_FIELD_BORDER = 7U,
    WORLD_ENCOUNTER_ATTRIBUTE = 4U,
    WORLD_ENCOUNTER_TILE = 1U,
};

enum FixtureKind {
    FIXTURE_ITEM,
    FIXTURE_HIDDEN,
    FIXTURE_CUT,
    FIXTURE_DIALOGUE,
    FIXTURE_RAID_REMOVED,
    FIXTURE_TRAINER,
    FIXTURE_WILD,
};

struct Fixture {
    const char *name;
    enum FixtureKind kind;
    uint8_t group;
    uint8_t map;
    uint16_t x;
    uint16_t y;
    uint16_t action_key;
    uint16_t item;
    uint16_t flag;
    uint16_t trainer;
    uint8_t local_id;
};

static const struct Fixture WORLD_FIXTURES[] = {
    {"item_ball", FIXTURE_ITEM, 96U, 1U, 17U, 4U, WORLD_KEY_A, 13U, 0x140DU, 0U, 6U},
    {"hidden_item", FIXTURE_HIDDEN, 96U, 2U, 6U, 2U, WORLD_KEY_A, 988U, 0x134CU, 0U, 0U},
    {"cut_tree", FIXTURE_CUT, 3U, 3U, 11U, 17U, WORLD_KEY_A, 0U, 0U, 0U, 9U},
    {"hisui_general", FIXTURE_DIALOGUE, 3U, 5U, 4U, 20U, WORLD_KEY_A, 0U, 0U, 0U, 4U},
    {"kanto_authored_dialogue", FIXTURE_DIALOGUE, 98U, 96U, 12U, 5U, WORLD_KEY_A, 0U, 0U, 0U, 6U},
    {"stage49_raid_removed", FIXTURE_RAID_REMOVED, 3U, 19U, 19U, 7U, WORLD_KEY_A, 0U, 0U, 0U, 0U},
    {"trainer_vertical", FIXTURE_TRAINER, 3U, 19U, 27U, 11U, WORLD_KEY_UP, 0U, 1369U, 89U, 6U},
    {"trainer_horizontal", FIXTURE_TRAINER, 3U, 19U, 50U, 10U, WORLD_KEY_RIGHT, 0U, 1373U, 93U, 3U},
    {"kanto_route1_land", FIXTURE_WILD, 96U, 12U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave", FIXTURE_WILD, 3U, 59U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
};

struct FixtureResult {
    bool natural_continue;
    bool script_seen;
    bool field_returned;
    bool state_committed;
    bool battle_seen;
    bool battle_completed;
    bool sight_triggered;
    bool old_raid_absent;
    bool encounter_found;
    bool fled_and_moved;
    bool duplicate_prevented;
    unsigned key_pulses;
    unsigned successful_steps;
    unsigned encounters;
    unsigned rotations;
    uint16_t start_x;
    uint16_t start_y;
    uint16_t end_x;
    uint16_t end_y;
};

static const char *world_phase = "startup";
static color_t world_video[240U * 160U];

static void world_die(const char *fixture, const char *message)
{
    fprintf(stderr, "mgba-world-runtime-input[%s][%s]: %s\n",
            fixture, world_phase, message);
    exit(1);
}

static uint32_t world_save1(struct mCore *core, const char *fixture)
{
    uint32_t pointer = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (pointer < 0x02000000U || pointer >= 0x02040000U || (pointer & 3U))
        world_die(fixture, "SaveBlock1 pointer differs");
    return pointer;
}

static bool world_script_enabled(struct mCore *core)
{
    return call_preserving(core, WORLD_SCRIPT_CONTEXT_ENABLED,
                           0U, 0U, 0U, 0U) != 0U;
}

static bool world_overworld(struct mCore *core)
{
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == BOOTSTRAP_CB2_OVERWORLD;
}

static void world_pulse(struct mCore *core, uint16_t key,
                        unsigned pressed, unsigned released)
{
    run_key_frames(core, key, pressed);
    run_key_frames(core, 0U, released);
}

static void world_generate_save(const char *rom_path, const char *save_path,
                                const struct Fixture *fixture,
                                uint16_t x, uint16_t y)
{
    struct mCore *core;
    uint32_t save1;
    world_phase = "natural-new-game";
    bootstrap_write_blank_save(save_path);
    core = bootstrap_open_core(rom_path, save_path, NULL);
    run_trace_prefix(core);
    run_fixed_frames(core);
    save1 = world_save1(core, fixture->name);
    (void)save1;

    world_phase = "stock-warp-save";
    (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                          fixture->group, fixture->map, x, y);
    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
    save1 = world_save1(core, fixture->name);
    if (read8(core, save1 + 4U) != fixture->group
        || read8(core, save1 + 5U) != fixture->map
        || read16(core, save1) != x || read16(core, save1 + 2U) != y
        || !world_overworld(core)) {
        fprintf(stderr, "warp debug: wanted=%u/%u %u,%u got=%u/%u %u,%u callback=%08" PRIX32 "\n",
                fixture->group, fixture->map, x, y,
                read8(core, save1 + 4U), read8(core, save1 + 5U),
                read16(core, save1), read16(core, save1 + 2U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        world_die(fixture->name, "stock warp did not reach fixture");
    }

    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        create_mon(core, mon, 150U, 100U);
        set_mon_data_u32(core, mon, MON_DATA_MOVE1, BATTLE_CORE_MOVE_TACKLE);
        set_mon_data_u32(core, mon, MON_DATA_PP1, 35U);
    }
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);
    bootstrap_prepare_save_map_view(core);
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        world_die(fixture->name, "two-generation save failed");
    bootstrap_close_core(core);
}

static void world_continue(struct mCore *core, const struct Fixture *fixture)
{
    uint32_t save1;
    world_phase = "fresh-core-continue";
    run_key_frames(core, 0U, BOOTSTRAP_TITLE_FRAMES);
    for (unsigned pulse = 0U; pulse < BOOTSTRAP_CONTINUE_PULSES; ++pulse) {
        world_pulse(core, pulse == 0U ? 8U : WORLD_KEY_A,
                    2U, BOOTSTRAP_CONTINUE_WAIT_FRAMES);
        save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (world_overworld(core)
            && save1 >= 0x02000000U && save1 < 0x02040000U
            && !(save1 & 3U)
            && read8(core, save1 + 4U) == fixture->group
            && read8(core, save1 + 5U) == fixture->map) {
            run_key_frames(core, 0U, 900U);
            return;
        }
    }
    world_die(fixture->name, "natural Continue did not reach fixture");
}

static bool world_wait_script_release(struct mCore *core,
                                      struct FixtureResult *result)
{
    for (unsigned pulse = 0U; pulse < 80U; ++pulse) {
        if (world_script_enabled(core))
            result->script_seen = true;
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
        if (result->script_seen && !world_script_enabled(core)
            && world_overworld(core)) {
            run_key_frames(core, 0U, 90U);
            return true;
        }
    }
    return false;
}

static void world_print_object_debug(struct mCore *core,
                                     const struct Fixture *fixture)
{
    uint32_t save1 = world_save1(core, fixture->name);
    fprintf(stderr, "player debug: map=%u/%u pos=%u,%u\n",
            read8(core, save1 + 4U), read8(core, save1 + 5U),
            read16(core, save1), read16(core, save1 + 2U));
    for (unsigned index = 0U; index < 16U; ++index) {
        uint32_t row = WORLD_OBJECT_EVENTS + index * 0x24U;
        if ((read8(core, row) & 1U) != 0U
            && read8(core, row + 8U) == fixture->local_id
            && read8(core, row + 9U) == fixture->map
            && read8(core, row + 10U) == fixture->group) {
            fprintf(stderr,
                    "object debug: slot=%u local=%u current=%u,%u facing=%u active=%u\n",
                    index, fixture->local_id, read16(core, row + 0x10U),
                    read16(core, row + 0x12U), read8(core, row + 0x18U) & 0xFU,
                    read8(core, row) & 1U);
            return;
        }
        if ((read8(core, row) & 1U) != 0U) {
            fprintf(stderr, "active object: slot=%u local=%u map=%u/%u current=%u,%u\n",
                    index, read8(core, row + 8U), read8(core, row + 10U),
                    read8(core, row + 9U), read16(core, row + 0x10U),
                    read16(core, row + 0x12U));
        }
    }
    fprintf(stderr, "object debug: local=%u is not active\n", fixture->local_id);
}

static void world_interaction(struct mCore *core,
                              const struct Fixture *fixture,
                              struct FixtureResult *result)
{
    uint32_t bag_before = 0U;
    uint32_t flag_before = 0U;
    if (fixture->item != 0U)
        bag_before = call_preserving(core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
                                     fixture->item, 1U, 0U, 0U);
    if (fixture->flag != 0U)
        flag_before = call_preserving(core, WORLD_FLAG_GET,
                                      fixture->flag, 0U, 0U, 0U);
    if (bag_before || flag_before)
        world_die(fixture->name, "fixture starts already committed");

    world_phase = "gba-a-interaction";
    world_pulse(core, fixture->action_key, 2U, 8U);
    result->key_pulses++;
    result->script_seen = world_script_enabled(core);
    result->field_returned = world_wait_script_release(core, result);
    if (!result->script_seen || !result->field_returned) {
        world_print_object_debug(core, fixture);
        world_die(fixture->name, "A interaction did not start and release finite script");
    }
    if (fixture->item != 0U) {
        uint32_t bag_after = call_preserving(
            core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
            fixture->item, 1U, 0U, 0U);
        uint32_t flag_after = call_preserving(
            core, WORLD_FLAG_GET, fixture->flag, 0U, 0U, 0U);
        result->state_committed = bag_after == 1U && flag_after == 1U;
        if (!result->state_committed)
            world_die(fixture->name, "item/flag did not commit after input flow");
        world_phase = "gba-item-duplicate-negative";
        world_pulse(core, fixture->action_key, 2U, 8U);
        ++result->key_pulses;
        if (world_script_enabled(core)
            && !world_wait_script_release(core, result))
            world_die(fixture->name, "collected item script did not release");
        result->duplicate_prevented = call_preserving(
            core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
            fixture->item, 2U, 0U, 0U) == 0U
            && call_preserving(core, WORLD_FLAG_GET,
                               fixture->flag, 0U, 0U, 0U) == 1U;
        if (!result->duplicate_prevented)
            world_die(fixture->name, "collected item was duplicated");
    } else {
        result->state_committed = true;
        result->duplicate_prevented = true;
    }
}

static bool world_walk_to_new_tile(struct mCore *core, uint16_t key,
                                   uint16_t *x, uint16_t *y,
                                   struct FixtureResult *result)
{
    for (unsigned pulse = 0U; pulse < 30U; ++pulse) {
        world_pulse(core, key, 2U, 4U);
        ++result->key_pulses;
        if (!world_overworld(core))
            return false;
        uint32_t save1 = world_save1(core, "walk");
        uint16_t next_x = read16(core, save1);
        uint16_t next_y = read16(core, save1 + 2U);
        if (next_x != *x || next_y != *y) {
            *x = next_x;
            *y = next_y;
            ++result->successful_steps;
            run_key_frames(core, 0U, 45U);
            return true;
        }
    }
    return false;
}

static void world_finish_battle(struct mCore *core,
                                const struct Fixture *fixture,
                                struct FixtureResult *result,
                                bool flee)
{
    result->battle_seen = true;
    world_phase = flee ? "gba-run-from-wild" : "gba-complete-trainer-battle";
    for (unsigned pulse = 0U; pulse < 250U; ++pulse) {
        if (flee && pulse % 5U == 0U) {
            world_pulse(core, WORLD_KEY_RIGHT, 2U, 16U);
            world_pulse(core, WORLD_KEY_DOWN, 2U, 16U);
        }
        if (!flee && read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                            + BATTLE_CORE_MON_HP) == 0U)
            world_pulse(core, WORLD_KEY_B, 2U, 24U);
        world_pulse(core, WORLD_KEY_A, 2U, BATTLE_CORE_MENU_INPUT_WAIT);
        ++result->key_pulses;
        if (world_overworld(core) && !world_script_enabled(core)) {
            run_key_frames(core, 0U, 120U);
            result->battle_completed = true;
            return;
        }
        if (flee && pulse % 7U == 6U)
            world_pulse(core, WORLD_KEY_B, 2U, 30U);
    }
    fprintf(stderr,
            "battle debug: callback=%08" PRIX32 " outcome=%u newbs=%08" PRIX32
            " opponent=%u script=%u\n",
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, BATTLE_CORE_BATTLE_OUTCOME),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read16(core, WORLD_TRAINER_OPPONENT_A),
            world_script_enabled(core) ? 1U : 0U);
    fprintf(stderr,
            "battle mons: player=%u hp=%u pp=%u enemy=%u hp=%u chosen=%u cursor=%u/%u\n",
            read16(core, ADDR_BATTLE_MONS),
            read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
            read8(core, ADDR_BATTLE_MONS + BATTLE_MON_PP_OFFSET),
            read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE),
            read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE + BATTLE_CORE_MON_HP),
            read8(core, BATTLE_CORE_CHOSEN_ACTIONS),
            read8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR),
            read8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR));
    fprintf(stderr, "enemy party count=%u indexes=%u/%u species=",
            read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT),
            read16(core, ADDR_BATTLER_PARTY_INDEXES),
            read16(core, ADDR_BATTLER_PARTY_INDEXES + 2U));
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot)
        fprintf(stderr, "%s%u", slot ? "/" : "",
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA,
                    ADDR_ENEMY_PARTY + slot * POKEMON_SIZE, 11U, 0U, 0U));
    fputc('\n', stderr);
    char screenshot[256];
    if (snprintf(screenshot, sizeof(screenshot), "/tmp/%s", fixture->name) > 0)
        bootstrap_write_ppm(screenshot, world_video);
    world_die(fixture->name, "battle did not return to field through keys");
}

static void world_trainer(struct mCore *core,
                          const struct Fixture *fixture,
                          struct FixtureResult *result)
{
    uint32_t save1 = world_save1(core, fixture->name);
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    world_phase = "gba-step-into-trainer-sight";
    if (!world_walk_to_new_tile(core, fixture->action_key, &x, &y, result))
        world_die(fixture->name, "player did not enter trainer sight tile");
    for (unsigned frame = 0U; frame < 1200U; frame += 30U) {
        run_key_frames(core, 0U, 30U);
        if (world_script_enabled(core)) {
            result->script_seen = true;
            result->sight_triggered = true;
            break;
        }
    }
    if (!result->sight_triggered)
        world_die(fixture->name, "trainer sight did not start approach script");
    for (unsigned pulse = 0U; pulse < 80U && world_overworld(core); ++pulse) {
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
        if (read16(core, WORLD_TRAINER_OPPONENT_A) != 0U
            && read16(core, WORLD_TRAINER_OPPONENT_A) != fixture->trainer)
            world_die(fixture->name, "wrong trainer command reached from object");
    }
    if (world_overworld(core)
        || read16(core, WORLD_TRAINER_OPPONENT_A) != fixture->trainer)
        world_die(fixture->name, "trainer battle did not start through sight/input");
    world_finish_battle(core, fixture, result, false);
    result->field_returned = result->battle_completed;
    result->state_committed = call_preserving(
        core, WORLD_FLAG_GET, fixture->flag, 0U, 0U, 0U) == 1U;
    if (!result->state_committed)
        world_die(fixture->name, "trainer defeat flag was not committed");
}

static bool world_encounter_tile(struct mCore *core, uint16_t x, uint16_t y)
{
    return (call_preserving(core, WORLD_MAP_GRID_FIELD,
                            x + WORLD_FIELD_BORDER, y + WORLD_FIELD_BORDER,
                            WORLD_ENCOUNTER_ATTRIBUTE, 0U)
            & WORLD_ENCOUNTER_TILE) != 0U;
}

static bool world_collision(struct mCore *core, uint16_t x, uint16_t y)
{
    return call_preserving(core, WORLD_MAP_GRID_COLLISION,
                           x + WORLD_FIELD_BORDER, y + WORLD_FIELD_BORDER,
                           0U, 0U) != 0U;
}

static bool world_find_encounter_pair(struct mCore *core,
                                      uint16_t *x, uint16_t *y)
{
    uint32_t width = read32(core, BOOTSTRAP_VMAP);
    uint32_t height = read32(core, BOOTSTRAP_VMAP + 4U);
    if (width < 18U || height < 17U)
        return false;
    for (uint16_t row = 1U; row + 1U < height - 14U; ++row) {
        for (uint16_t column = 1U; column + 1U < width - 15U; ++column) {
            if (world_encounter_tile(core, column, row)
                && world_encounter_tile(core, column + 1U, row)
                && !world_collision(core, column, row)
                && !world_collision(core, column + 1U, row)
                && (world_collision(core, column - 1U, row)
                    || world_collision(core, column, row - 1U)
                    || world_collision(core, column, row + 1U))) {
                *x = column;
                *y = row;
                return true;
            }
        }
    }
    return false;
}

static void world_generate_wild_save(const char *rom_path,
                                     const char *save_path,
                                     const struct Fixture *fixture,
                                     uint16_t *x, uint16_t *y)
{
    struct mCore *core;
    world_generate_save(rom_path, save_path, fixture, fixture->x, fixture->y);
    core = bootstrap_open_core(rom_path, save_path, NULL);
    world_continue(core, fixture);
    if (!world_find_encounter_pair(core, x, y))
        world_die(fixture->name, "map has no adjacent encounter terrain pair");
    bootstrap_close_core(core);
    world_generate_save(rom_path, save_path, fixture, *x, *y);
}

static void world_wild(struct mCore *core, const struct Fixture *fixture,
                       struct FixtureResult *result)
{
    uint32_t save1 = world_save1(core, fixture->name);
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    result->start_x = x;
    result->start_y = y;
    if (!world_encounter_tile(core, x, y)
        || !world_encounter_tile(core, x + 1U, y))
        world_die(fixture->name, "saved path is not encounter terrain");

    world_phase = "gba-direction-only";
    size_t state_size = core->stateSize(core);
    void *state = malloc(state_size);
    if (!state || !core->saveState(core, state))
        world_die(fixture->name, "rotation state capture failed");
    static const uint16_t turn_keys[] = {
        WORLD_KEY_UP, WORLD_KEY_DOWN, WORLD_KEY_LEFT, WORLD_KEY_RIGHT,
    };
    bool rotation_found = false;
    for (unsigned key_index = 0U; key_index < 4U; ++key_index) {
        if (!core->loadState(core, state))
            world_die(fixture->name, "rotation state restore failed");
        uint16_t before_x = read16(core, save1);
        uint16_t before_y = read16(core, save1 + 2U);
        world_pulse(core, turn_keys[key_index], 1U, 3U);
        run_key_frames(core, 0U, 30U);
        if (world_overworld(core)
            && read16(core, save1) == before_x
            && read16(core, save1 + 2U) == before_y) {
            rotation_found = true;
            for (unsigned count = 0U; count < 32U; ++count) {
                world_pulse(core, turn_keys[key_index], 1U, 3U);
                run_key_frames(core, 0U, 8U);
                ++result->rotations;
                if (!world_overworld(core))
                    world_die(fixture->name, "direction-only input started encounter");
            }
            break;
        }
    }
    free(state);
    if (!rotation_found)
        world_die(fixture->name, "no direction-only input fixture found");

    world_phase = "gba-encounter-walk";
    x = read16(core, save1);
    y = read16(core, save1 + 2U);
    uint16_t key = WORLD_KEY_RIGHT;
    for (unsigned attempt = 0U; attempt < 400U; ++attempt) {
        uint16_t before_x = x;
        uint16_t before_y = y;
        bool moved = world_walk_to_new_tile(core, key, &x, &y, result);
        if (!moved && !world_overworld(core)) {
            ++result->encounters;
            result->encounter_found = true;
            world_finish_battle(core, fixture, result, true);
            x = read16(core, save1);
            y = read16(core, save1 + 2U);
            key = x == result->start_x ? WORLD_KEY_RIGHT : WORLD_KEY_LEFT;
            break;
        }
        if (!moved) {
            key = key == WORLD_KEY_RIGHT ? WORLD_KEY_LEFT : WORLD_KEY_RIGHT;
            x = before_x;
            y = before_y;
            continue;
        }
        key = key == WORLD_KEY_RIGHT ? WORLD_KEY_LEFT : WORLD_KEY_RIGHT;
    }
    if (!result->encounter_found)
        world_die(fixture->name, "sufficient normal walking produced zero encounters");

    unsigned post_flee_steps = 0U;
    unsigned post_flee_no_encounter = 0U;
    for (unsigned attempt = 0U; attempt < 80U && post_flee_steps < 20U; ++attempt) {
        bool moved = world_walk_to_new_tile(core, key, &x, &y, result);
        if (!moved && !world_overworld(core)) {
            ++result->encounters;
            world_finish_battle(core, fixture, result, true);
            x = read16(core, save1);
            y = read16(core, save1 + 2U);
        } else if (moved) {
            ++post_flee_steps;
            ++post_flee_no_encounter;
        }
        key = key == WORLD_KEY_RIGHT ? WORLD_KEY_LEFT : WORLD_KEY_RIGHT;
    }
    result->fled_and_moved = result->battle_completed
        && post_flee_steps >= 10U && post_flee_no_encounter != 0U
        && result->encounters < result->successful_steps;
    if (!result->fled_and_moved)
        world_die(fixture->name, "post-flee cadence prevented ordinary movement");
    if (!world_overworld(core)) {
        ++result->encounters;
        world_finish_battle(core, fixture, result, true);
    }
    result->field_returned = world_overworld(core);
    if (!result->field_returned)
        world_die(fixture->name, "wild fixture did not finish on the field");
    result->state_committed = true;
    result->duplicate_prevented = true;
    result->end_x = read16(core, save1);
    result->end_y = read16(core, save1 + 2U);
}

static struct FixtureResult world_run_fixture(const char *rom_path,
                                              const char *directory,
                                              const struct Fixture *fixture)
{
    struct FixtureResult result = {0};
    result.duplicate_prevented = true;
    char save_path[4096];
    uint16_t x = fixture->x;
    uint16_t y = fixture->y;
    if (snprintf(save_path, sizeof(save_path), "%s/%s.srm",
                 directory, fixture->name) <= 0)
        world_die(fixture->name, "save path formatting failed");
    if (fixture->kind == FIXTURE_WILD)
        world_generate_wild_save(rom_path, save_path, fixture, &x, &y);
    else
        world_generate_save(rom_path, save_path, fixture, x, y);

    world_phase = "fresh-core";
    memset(world_video, 0, sizeof(world_video));
    struct mCore *core = bootstrap_open_core(rom_path, save_path, world_video);
    world_continue(core, fixture);
    result.natural_continue = true;
    result.start_x = read16(core, world_save1(core, fixture->name));
    result.start_y = read16(core, world_save1(core, fixture->name) + 2U);
    if (fixture->kind == FIXTURE_TRAINER) {
        world_trainer(core, fixture, &result);
    } else if (fixture->kind == FIXTURE_WILD) {
        world_wild(core, fixture, &result);
    } else if (fixture->kind == FIXTURE_RAID_REMOVED) {
        world_phase = "gba-removed-raid-negative";
        world_pulse(core, fixture->action_key, 2U, 120U);
        ++result.key_pulses;
        result.old_raid_absent = !world_script_enabled(core)
            && world_overworld(core);
        result.field_returned = result.old_raid_absent;
        result.state_committed = true;
        if (!result.old_raid_absent)
            world_die(fixture->name, "removed Stage49 Raid host still captures input");
    } else {
        world_interaction(core, fixture, &result);
    }
    uint32_t save1 = world_save1(core, fixture->name);
    result.end_x = read16(core, save1);
    result.end_y = read16(core, save1 + 2U);
    bootstrap_close_core(core);
    return result;
}

static void world_print_result(const struct Fixture *fixture,
                               const struct FixtureResult *result)
{
    printf("{\"name\":\"%s\",\"map\":\"%u/%u\","
           "\"start\":[%u,%u],\"end\":[%u,%u],"
           "\"natural_continue\":%s,\"script_seen\":%s,"
           "\"field_returned\":%s,\"state_committed\":%s,"
           "\"battle_seen\":%s,\"battle_completed\":%s,"
           "\"sight_triggered\":%s,\"old_raid_absent\":%s,"
           "\"encounter_found\":%s,\"fled_and_moved\":%s,"
           "\"duplicate_prevented\":%s,"
           "\"key_pulses\":%u,\"successful_steps\":%u,"
           "\"encounters\":%u,\"rotations\":%u}",
           fixture->name, fixture->group, fixture->map,
           result->start_x, result->start_y, result->end_x, result->end_y,
           result->natural_continue ? "true" : "false",
           result->script_seen ? "true" : "false",
           result->field_returned ? "true" : "false",
           result->state_committed ? "true" : "false",
           result->battle_seen ? "true" : "false",
           result->battle_completed ? "true" : "false",
           result->sight_triggered ? "true" : "false",
           result->old_raid_absent ? "true" : "false",
           result->encounter_found ? "true" : "false",
           result->fled_and_moved ? "true" : "false",
           result->duplicate_prevented ? "true" : "false",
           result->key_pulses, result->successful_steps,
           result->encounters, result->rotations);
}

int main(int argc, char **argv)
{
    if (argc != 3 && argc != 4) {
        fprintf(stderr, "usage: %s ROM WORK_DIRECTORY [FIXTURE]\n", argv[0]);
        return 2;
    }
    if (mkdir(argv[2], 0700) != 0 && errno != EEXIST) {
        perror("mkdir");
        return 2;
    }
    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct FixtureResult results[sizeof(WORLD_FIXTURES) / sizeof(WORLD_FIXTURES[0])];
    bool selected = false;
    for (unsigned index = 0U;
         index < sizeof(WORLD_FIXTURES) / sizeof(WORLD_FIXTURES[0]); ++index) {
        if (argc == 4 && strcmp(argv[3], WORLD_FIXTURES[index].name) != 0)
            continue;
        selected = true;
        bootstrap_phase = WORLD_FIXTURES[index].name;
        results[index] = world_run_fixture(argv[1], argv[2], &WORLD_FIXTURES[index]);
    }
    if (!selected)
        world_die("selection", "unknown fixture name");
    if (log_problem_count != 0U)
        world_die("all", "mGBA emitted warning/error diagnostics");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"fixtures\":[");
    bool first = true;
    for (unsigned index = 0U;
         index < sizeof(WORLD_FIXTURES) / sizeof(WORLD_FIXTURES[0]); ++index) {
        if (argc == 4 && strcmp(argv[3], WORLD_FIXTURES[index].name) != 0)
            continue;
        if (!first)
            putchar(',');
        first = false;
        world_print_result(&WORLD_FIXTURES[index], &results[index]);
    }
    printf("],\"warnings\":0}\n");
    return 0;
}
