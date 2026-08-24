/*
 * Stage53 world runtime input E2E.
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
    WORLD_FLAG_GET = 0x0806DEC5U,
    WORLD_MAP_GRID_FIELD = 0x08058805U,
    WORLD_MAP_GRID_COLLISION = 0x08058681U,
    WORLD_TRAINER_OPPONENT_A = 0x020385E2U,
    WORLD_OBJECT_EVENTS = 0x02036D6CU,
    WORLD_CODEX_STATE = 0x0203FA00U,
    WORLD_CODEX_PHASE_OFFSET = 16U,
    WORLD_CODEX_ACTIVE_OFFSET = 20U,
    WORLD_QUEST_LOG_STATE = 0x0203AD72U,
    WORLD_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    WORLD_FIELD_CONTROLS_LOCKED = 0x03000F9CU,
    WORLD_PLAYER_AVATAR = 0x02036FACU,
    WORLD_PLAYER_RUNNING_STATE_OFFSET = 2U,
    WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET = 3U,
    WORLD_PLAYER_MOVING = 2U,
    WORLD_PLAYER_TILE_CENTER = 2U,
    WORLD_KEY_A = 1U,
    WORLD_KEY_B = 2U,
    WORLD_KEY_RIGHT = 16U,
    WORLD_KEY_LEFT = 32U,
    WORLD_KEY_UP = 64U,
    WORLD_KEY_DOWN = 128U,
    WORLD_FIELD_BORDER = 7U,
    WORLD_ENCOUNTER_ATTRIBUTE = 4U,
    WORLD_ENCOUNTER_TILE = 1U,
    WORLD_QA_MOVE_DARK_PULSE = 369U,
    WORLD_BATTLE_COMMAND_CHOOSE_POKEMON = 22U,
};

enum FixtureKind {
    FIXTURE_ITEM,
    FIXTURE_HIDDEN,
    FIXTURE_CUT,
    FIXTURE_DIALOGUE,
    FIXTURE_FACING_DIALOGUE,
    FIXTURE_RAID_REMOVED,
    FIXTURE_TRAINER,
    FIXTURE_WILD,
    FIXTURE_WILD_WALK_ONLY,
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
    {"item_ball", FIXTURE_ITEM, 96U, 1U, 17U, 4U, WORLD_KEY_DOWN, 13U, 0x140DU, 0U, 6U},
    {"hidden_item", FIXTURE_HIDDEN, 96U, 2U, 6U, 2U, WORLD_KEY_DOWN, 988U, 0x134CU, 0U, 0U},
    {"cut_tree", FIXTURE_CUT, 3U, 3U, 11U, 17U, WORLD_KEY_A, 0U, 0U, 0U, 9U},
    {"hisui_general", FIXTURE_DIALOGUE, 3U, 5U, 4U, 20U, WORLD_KEY_A, 0U, 0U, 0U, 4U},
    {"hisui_506_untalkable", FIXTURE_FACING_DIALOGUE, 3U, 2U, 3U, 15U, WORLD_KEY_DOWN, 0U, 0U, 0U, 5U},
    {"hisui_506_scientist", FIXTURE_FACING_DIALOGUE, 3U, 2U, 5U, 16U, WORLD_KEY_LEFT, 0U, 0U, 0U, 9U},
    {"kanto_authored_dialogue", FIXTURE_DIALOGUE, 98U, 96U, 12U, 5U, WORLD_KEY_A, 0U, 0U, 0U, 6U},
    {"stage49_raid_removed", FIXTURE_RAID_REMOVED, 3U, 19U, 19U, 7U, WORLD_KEY_A, 0U, 0U, 0U, 0U},
    {"trainer_vertical", FIXTURE_TRAINER, 3U, 19U, 27U, 11U, WORLD_KEY_UP, 0U, 1369U, 89U, 6U},
    {"trainer_horizontal", FIXTURE_TRAINER, 3U, 19U, 50U, 10U, WORLD_KEY_RIGHT, 0U, 1373U, 93U, 3U},
    {"route506_double", FIXTURE_TRAINER, 3U, 24U, 11U, 8U, WORLD_KEY_UP, 0U, 0x07ADU, 1338U, 10U},
    {"waterway_511_land", FIXTURE_WILD, 3U, 29U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_entrance", FIXTURE_WILD, 1U, 83U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_b1f", FIXTURE_WILD, 1U, 84U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_deep", FIXTURE_WILD, 1U, 85U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_old_man_room_a", FIXTURE_WILD_WALK_ONLY, 1U, 11U, 10U, 5U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_old_man_room_b", FIXTURE_WILD_WALK_ONLY, 1U, 100U, 10U, 5U, 0U, 0U, 0U, 0U, 0U},
    {"wisdom_cave_upper", FIXTURE_WILD, 3U, 59U, 10U, 10U, 0U, 0U, 0U, 0U, 0U},
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
    uint16_t first_wild_species;
    uint8_t first_wild_level;
    uint8_t minimum_wild_level;
    uint8_t maximum_wild_level;
    uint8_t battle_outcome;
    uint8_t trainer_flag_seen;
    uint16_t trainer_external_flag;
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

static uint32_t world_trainer_flag_address(struct mCore *core,
                                           const struct Fixture *fixture)
{
    return world_save1(core, fixture->name) + 0x0EE0U
           + ((uint32_t)fixture->flag >> 3);
}

static bool world_script_enabled(struct mCore *core)
{
    return read8(core, WORLD_FIELD_CONTROLS_LOCKED) != 0U;
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

static uint8_t world_direction_for_key(uint16_t key)
{
    if (key == WORLD_KEY_UP)
        return 2U;
    if (key == WORLD_KEY_DOWN)
        return 1U;
    if (key == WORLD_KEY_LEFT)
        return 3U;
    if (key == WORLD_KEY_RIGHT)
        return 4U;
    return 0U;
}

static uint8_t world_player_facing(struct mCore *core)
{
    uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
    if (object_id >= 16U)
        world_die("player-facing", "player object ID is out of range");
    uint32_t object = WORLD_OBJECT_EVENTS + object_id * 0x24U;
    if ((read8(core, object) & 1U) == 0U)
        world_die("player-facing", "player object is not active");
    return read8(core, object + 0x18U) & 0xFU;
}

static void world_wait_player_ready(struct mCore *core,
                                    const struct Fixture *fixture)
{
    unsigned stable_frames = 0U;
    /* Continue briefly exposes the field callback before the preview handoff
     * creates the player object.  Confirm that final stock handoff only while
     * the player object is still absent. */
    uint8_t first_object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
    if (first_object_id >= 16U
        || !(read8(core, WORLD_OBJECT_EVENTS
                   + first_object_id * 0x24U) & 1U))
        world_pulse(core, WORLD_KEY_UP, 1U, 180U);
    for (unsigned frames = 0U; frames < 3600U; frames += 15U) {
        uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
        uint32_t object = WORLD_OBJECT_EVENTS + object_id * 0x24U;
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        bool save_ready = save1 >= 0x02000000U && save1 < 0x02040000U
            && (save1 & 3U) == 0U;
        bool object_ready = object_id < 16U
            && (read8(core, object) & 1U)
            && (read8(core, object + 0x18U) & 0xFU) >= 1U
            && (read8(core, object + 0x18U) & 0xFU) <= 4U
            && read16(core, object + 0x10U) != 0U
            && read16(core, object + 0x12U) != 0U;
        bool stationary = read8(
            core, WORLD_PLAYER_AVATAR + WORLD_PLAYER_RUNNING_STATE_OFFSET) == 0U
            && read8(core, WORLD_PLAYER_AVATAR
                     + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET) == 0U;
        if (world_overworld(core) && save_ready && object_ready && stationary
            && !world_script_enabled(core)) {
            stable_frames += 15U;
            if (stable_frames >= 120U)
                return;
        } else {
            stable_frames = 0U;
        }
        run_key_frames(core, 0U, 15U);
    }
    uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
    uint32_t object = WORLD_OBJECT_EVENTS + object_id * 0x24U;
    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    fprintf(stderr,
            "field-ready debug: callback=%08" PRIX32 " lock=%u"
            " avatar=%u/%u/%u object=%u flags=%02X/%02X"
            " facing=%u object_pos=%u,%u save=%08" PRIX32 "/%u,%u\n",
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, WORLD_FIELD_CONTROLS_LOCKED),
            object_id,
            read8(core, WORLD_PLAYER_AVATAR
                  + WORLD_PLAYER_RUNNING_STATE_OFFSET),
            read8(core, WORLD_PLAYER_AVATAR
                  + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET),
            object_id, read8(core, object), read8(core, object + 2U),
            read8(core, object + 0x18U) & 0xFU,
            read16(core, object + 0x10U), read16(core, object + 0x12U),
            save1, read16(core, save1), read16(core, save1 + 2U));
    world_die(fixture->name,
              "Continue did not settle on an input-ready field");
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
        set_mon_data_u32(core, mon, MON_DATA_MOVE1,
                         WORLD_QA_MOVE_DARK_PULSE);
        /* This is an input-path fixture, not a damage/PP balance test.  Keep
         * enough PP for long authored doubles whose defensive matchups can
         * otherwise outlive the deterministic A-button driver. */
        set_mon_data_u32(core, mon, MON_DATA_PP1, 63U);
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
            /* Continue first enters the FireRed recap while callback2 already
             * reports the overworld.  Dismiss it before treating object/event
             * state as field-ready. */
            run_key_frames(core, 0U, 300U);
            for (unsigned attempt = 0U; attempt < 8U; ++attempt) {
                if (read8(core, WORLD_QUEST_LOG_STATE) == 0U
                    && read8(core, WORLD_QUEST_LOG_PLAYBACK_STATE) == 0U) {
                    run_key_frames(core, 0U, 420U);
                    if (read8(core, WORLD_QUEST_LOG_STATE) == 0U
                        && read8(core, WORLD_QUEST_LOG_PLAYBACK_STATE) == 0U)
                        return;
                }
                world_pulse(core, WORLD_KEY_B, 2U, 180U);
            }
            world_die(fixture->name,
                      "Continue recap did not return to field state");
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
    if (fixture->kind == FIXTURE_FACING_DIALOGUE
        || fixture->kind == FIXTURE_ITEM) {
        world_pulse(core, fixture->action_key, 2U, 8U);
        ++result->key_pulses;
    } else if (fixture->kind == FIXTURE_HIDDEN) {
        uint8_t facing = world_player_facing(core);
        uint8_t wanted = world_direction_for_key(fixture->action_key);
        if (facing != wanted) {
            uint32_t save1 = world_save1(core, fixture->name);
            uint16_t before_x = read16(core, save1);
            uint16_t before_y = read16(core, save1 + 2U);
            world_pulse(core, fixture->action_key, 1U, 30U);
            ++result->key_pulses;
            if (read16(core, save1) != before_x
                || read16(core, save1 + 2U) != before_y)
                world_die(fixture->name,
                          "hidden-item facing input moved the player");
        }
    }
    world_pulse(core, WORLD_KEY_A, 2U, 8U);
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
        if (!result->state_committed) {
            fprintf(stderr,
                    "item commit debug: bag=%" PRIu32 " flag=%" PRIu32
                    " script_seen=%u field=%u context=%u mode=%u"
                    " status=%u quest=%u quest_playback=%u pos=%u,%u\n",
                    bag_after, flag_after,
                    result->script_seen ? 1U : 0U,
                    result->field_returned ? 1U : 0U,
                    world_script_enabled(core) ? 1U : 0U,
                    read8(core, 0x03000EB0U), read8(core, 0x03000EA8U),
                    read8(core, WORLD_QUEST_LOG_STATE),
                    read8(core, WORLD_QUEST_LOG_PLAYBACK_STATE),
                    read16(core, world_save1(core, fixture->name)),
                    read16(core, world_save1(core, fixture->name) + 2U));
            world_print_object_debug(core, fixture);
            bootstrap_write_ppm("/tmp/world-item-commit", world_video);
            world_die(fixture->name, "item/flag did not commit after input flow");
        }
        world_phase = "gba-item-duplicate-negative";
        world_pulse(core, WORLD_KEY_A, 2U, 8U);
        ++result->key_pulses;
        if (world_script_enabled(core)
            && !world_wait_script_release(core, result))
            world_die(fixture->name, "collected item script did not release");
        uint32_t bag_two = call_preserving(
            core, BATTLE_CORE_CHECK_BAG_HAS_ITEM,
            fixture->item, 2U, 0U, 0U);
        uint32_t committed_flag = call_preserving(
            core, WORLD_FLAG_GET, fixture->flag, 0U, 0U, 0U);
        result->duplicate_prevented = bag_two == 0U && committed_flag == 1U;
        if (!result->duplicate_prevented) {
            fprintf(stderr, "duplicate debug: item=%u bag_two=%" PRIu32
                    " flag=%04X value=%" PRIu32 "\n",
                    fixture->item, bag_two, fixture->flag, committed_flag);
            world_die(fixture->name, "collected item was duplicated");
        }
    } else {
        result->state_committed = true;
        result->duplicate_prevented = true;
    }
}

static bool world_walk_to_new_tile(struct mCore *core, uint16_t key,
                                   uint16_t *x, uint16_t *y,
                                   struct FixtureResult *result)
{
    uint16_t next_x = *x;
    uint16_t next_y = *y;
    bool coordinate_changed = false;
    ++result->key_pulses;
    for (unsigned frame = 0U; frame < 40U; ++frame) {
        run_key_frames(core, key, 1U);
        if (!world_overworld(core)) {
            core->setKeys(core, 0U);
            if (coordinate_changed) {
                *x = next_x;
                *y = next_y;
                ++result->successful_steps;
            }
            return false;
        }
        uint32_t save1 = world_save1(core, "walk");
        next_x = read16(core, save1);
        next_y = read16(core, save1 + 2U);
        coordinate_changed = next_x != *x || next_y != *y;
        /* SaveBlock coordinates change at step start.  Keep the key held
         * until the avatar reaches the tile center while still MOVING; that
         * is the frame FieldGetPlayerInput marks as a completed step. */
        if (coordinate_changed
            && read8(core, WORLD_PLAYER_AVATAR
                           + WORLD_PLAYER_RUNNING_STATE_OFFSET)
                   == WORLD_PLAYER_MOVING
            && read8(core, WORLD_PLAYER_AVATAR
                           + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET)
                   == WORLD_PLAYER_TILE_CENTER) {
            core->setKeys(core, 0U);
            *x = next_x;
            *y = next_y;
            ++result->successful_steps;
            run_key_frames(core, 0U, 45U);
            return world_overworld(core);
        }
    }
    run_key_frames(core, 0U, 4U);
    return false;
}

static void world_finish_battle(struct mCore *core,
                                const struct Fixture *fixture,
                                struct FixtureResult *result,
                                bool flee)
{
    bool battle_initialized = false;
    result->battle_seen = true;
    world_phase = flee ? "gba-run-from-wild" : "gba-complete-trainer-battle";
    for (unsigned pulse = 0U; pulse < 1200U; ++pulse) {
        if (read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0U) {
            result->battle_outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
            if (fixture->flag >= 0x0500U && fixture->flag < 0x0800U) {
                uint16_t offset = (uint16_t)(fixture->flag - 0x0500U);
                uint8_t byte = read8(
                    core, world_trainer_flag_address(core, fixture));
                if ((byte >> (offset & 7U)) & 1U)
                    result->trainer_flag_seen = 1U;
            }
        }
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            battle_initialized = true;
        if (!battle_initialized) {
            /* Trainer approach, intro text and palette transition still use
             * field callbacks after battle flags are reserved.  Do not feed
             * battle-menu A presses into that stock transition; confirm an
             * authored intro only at a human-scale interval. */
            run_key_frames(core, 0U, 30U);
            if (pulse % 6U == 5U) {
                world_pulse(core, WORLD_KEY_A, 2U, 30U);
                ++result->key_pulses;
            }
            continue;
        }
        if (battle_initialized && world_overworld(core)) {
            /* The opponent ID is persistent trainerbattle state and is not a
             * field-return sentinel.  Let the stock return script release
             * naturally before sending another A press, which could
             * immediately retrigger the adjacent trainer. */
            run_key_frames(core, 0U, 180U);
            if (world_overworld(core) && !world_script_enabled(core)) {
                result->battle_completed = true;
                return;
            }
        }
        if (battle_initialized
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
            && read8(core, ADDR_BATTLERS_COUNT) == 0U
            && read16(core, WORLD_TRAINER_OPPONENT_A) == 0U) {
            /* Battle teardown can still enter stock post-battle scenes which
             * require confirmation.  Give the transition a quiet window,
             * then resume ordinary A/B input if it has not reached field. */
            run_key_frames(core, 0U, 180U);
            if (world_overworld(core) && !world_script_enabled(core)) {
                run_key_frames(core, 0U, 120U);
                result->battle_completed = true;
                return;
            }
        }
        if (flee && pulse % 5U == 0U) {
            world_pulse(core, WORLD_KEY_RIGHT, 2U, 16U);
            world_pulse(core, WORLD_KEY_DOWN, 2U, 16U);
        }
        /* In SHIFT mode the stock engine offers the player a voluntary
         * switch after an opposing party member faints.  Repeated A would
         * accept that offer and then keep selecting the active Pokemon.
         * Decline only a ChoosePokemon command for a still-conscious player
         * battler; a real player faint continues through the normal A path. */
        bool declined_optional_switch = false;
        for (unsigned bank = 0U; bank < 4U; bank += 2U) {
            if (read8(core, 0x02022B24U + bank * 0x200U)
                    == WORLD_BATTLE_COMMAND_CHOOSE_POKEMON
                && read16(core, ADDR_BATTLE_MONS
                                + bank * BATTLE_MON_SIZE
                                + BATTLE_CORE_MON_HP) != 0U) {
                world_pulse(core, WORLD_KEY_B, 2U, 30U);
                ++result->key_pulses;
                declined_optional_switch = true;
            }
        }
        if (declined_optional_switch)
            continue;
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
            " opponent=%u script=%u flags=%08" PRIX32 " battlers=%u"
            " codex_active=%u codex_phase=%u fieldcb=%08" PRIX32
            " main1=%08" PRIX32 " saved=%08" PRIX32
            " quest=%u playback=%u\n",
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, BATTLE_CORE_BATTLE_OUTCOME),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read16(core, WORLD_TRAINER_OPPONENT_A),
            world_script_enabled(core) ? 1U : 0U,
            read32(core, ADDR_BATTLE_TYPE_FLAGS),
            read8(core, ADDR_BATTLERS_COUNT),
            read8(core, WORLD_CODEX_STATE + WORLD_CODEX_ACTIVE_OFFSET),
            read16(core, WORLD_CODEX_STATE + WORLD_CODEX_PHASE_OFFSET),
            read32(core, BOOTSTRAP_FIELD_CALLBACK),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2 - 4U),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2 + 4U),
            read8(core, WORLD_QUEST_LOG_STATE),
            read8(core, WORLD_QUEST_LOG_PLAYBACK_STATE));
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
    fprintf(stderr,
            "battle controllers: active=%u exec=%08" PRIX32
            " funcs=%08" PRIX32 "/%08" PRIX32 "/%08" PRIX32 "/%08" PRIX32
            " commands=%u/%u/%u/%u choices=%u/%u/%u/%u\n",
            read8(core, 0x02023B24U), read32(core, 0x02023B28U),
            read32(core, 0x03005020U), read32(core, 0x03005024U),
            read32(core, 0x03005028U), read32(core, 0x0300502CU),
            read8(core, 0x02022B24U), read8(core, 0x02022D24U),
            read8(core, 0x02022F24U), read8(core, 0x02023124U),
            read8(core, BATTLE_CORE_CHOSEN_ACTIONS),
            read8(core, BATTLE_CORE_CHOSEN_ACTIONS + 1U),
            read8(core, BATTLE_CORE_CHOSEN_ACTIONS + 2U),
            read8(core, BATTLE_CORE_CHOSEN_ACTIONS + 3U));
    fprintf(stderr, "enemy party count=%u indexes=%u/%u species/hp=",
            read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT),
            read16(core, ADDR_BATTLER_PARTY_INDEXES),
            read16(core, ADDR_BATTLER_PARTY_INDEXES + 2U));
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot)
        fprintf(stderr, "%s%u/%u", slot ? "," : "",
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA,
                    ADDR_ENEMY_PARTY + slot * POKEMON_SIZE, 11U, 0U, 0U),
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA,
                    ADDR_ENEMY_PARTY + slot * POKEMON_SIZE,
                    BATTLE_CORE_MON_DATA_HP, 0U, 0U));
    fputc('\n', stderr);
    fprintf(stderr, "player party count=%u species/level/hp=",
            read8(core, BOOTSTRAP_PLAYER_COUNT));
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        fprintf(stderr, "%s%u/%u/%u", slot ? "," : "",
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA, mon, 11U, 0U, 0U),
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA, mon, 56U, 0U, 0U),
                (unsigned)call_preserving(
                    core, BATTLE_CORE_GET_MON_DATA, mon,
                    BATTLE_CORE_MON_DATA_HP, 0U, 0U));
    }
    fputc('\n', stderr);
    fprintf(stderr, "tasks:");
    for (unsigned task = 0U; task < 16U; ++task) {
        uint32_t row = 0x030050D0U + task * 40U;
        if (read8(core, row + 4U) != 0U)
            fprintf(stderr, " %u=%08" PRIX32 "(p%u,s%u,d1=%u)", task,
                    read32(core, row), read8(core, row + 5U),
                    read16(core, row + 8U), read16(core, row + 10U));
    }
    fputc('\n', stderr);
    fprintf(stderr, "objects avatar=%u/%u/%u:",
            read8(core, WORLD_PLAYER_AVATAR + 5U),
            read8(core, WORLD_PLAYER_AVATAR
                  + WORLD_PLAYER_RUNNING_STATE_OFFSET),
            read8(core, WORLD_PLAYER_AVATAR
                  + WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET));
    for (unsigned object_index = 0U; object_index < 16U; ++object_index) {
        uint32_t object = WORLD_OBJECT_EVENTS + object_index * 0x24U;
        if (read8(core, object) & 1U)
            fprintf(stderr,
                    " %u[local=%u map=%u/%u cur=%u,%u prev=%u,%u"
                    " face=%02X action=%u flags=%02X]",
                    object_index, read8(core, object + 8U),
                    read8(core, object + 10U), read8(core, object + 9U),
                    read16(core, object + 0x10U),
                    read16(core, object + 0x12U),
                    read16(core, object + 0x14U),
                    read16(core, object + 0x16U),
                    read8(core, object + 0x18U),
                    read8(core, object + 0x1CU), read8(core, object));
    }
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
    if (getenv("WORLD_TRAINER_TRACE") != NULL) {
        uint32_t script = fixture->trainer == 1338U
            ? 0x09375A9FU
            : (fixture->trainer == 1369U ? 0x09376713U : 0x09376993U);
        size_t preflight_size = core->stateSize(core);
        void *preflight_state = malloc(preflight_size);
        if (!preflight_state || !core->saveState(core, preflight_state))
            world_die(fixture->name, "trainer preflight state capture failed");
        uint32_t defeated = call_preserving(
            core, 0x0807FA99U, script, 0U, 0U, 0U);
        uint32_t configured_next = call_preserving(
            core, 0x0807F949U, script + 1U, 0U, 0U, 0U);
        uint16_t configured_opponent = read16(core, WORLD_TRAINER_OPPONENT_A);
        fprintf(stderr,
                "trainer preflight: script=%08" PRIX32 " defeated=%" PRIu32
                " configured_next=%08" PRIX32 " configured_opponent=%u"
                " callback=%08" PRIX32 " pos=%u,%u\n",
                script, defeated, configured_next, configured_opponent,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read16(core, save1), read16(core, save1 + 2U));
        if (!core->loadState(core, preflight_state))
            world_die(fixture->name, "trainer preflight state restore failed");
        free(preflight_state);
    }
    world_phase = "gba-step-into-trainer-sight";
    if (!world_walk_to_new_tile(core, fixture->action_key, &x, &y, result)) {
        /* A corrected sight scanner may lock controls on the same frame that
         * the step finishes, before the generic walker can sample the new
         * coordinates.  That transition is the expected success path. */
        if (!world_overworld(core) || world_script_enabled(core)) {
            result->script_seen = true;
            result->sight_triggered = true;
        } else {
            world_die(fixture->name, "player did not enter trainer sight tile");
        }
    }
    for (unsigned frame = 0U; frame < 1200U; frame += 30U) {
        run_key_frames(core, 0U, 30U);
        if (!world_overworld(core) || world_script_enabled(core)) {
            result->script_seen = true;
            result->sight_triggered = true;
            break;
        }
    }
    if (!result->sight_triggered) {
        fprintf(stderr,
                "trainer sight debug: pos=%u,%u callback=%08" PRIX32
                " controls=%u opponent=%u flag=%" PRIu32 " tasks:",
                read16(core, world_save1(core, fixture->name)),
                read16(core, world_save1(core, fixture->name) + 2U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                world_script_enabled(core) ? 1U : 0U,
                read16(core, WORLD_TRAINER_OPPONENT_A),
                call_preserving(core, WORLD_FLAG_GET,
                                fixture->flag, 0U, 0U, 0U));
        for (unsigned task = 0U; task < 16U; ++task) {
            uint32_t row = 0x030050D0U + task * 40U;
            if (read8(core, row + 4U) != 0U)
                fprintf(stderr, " %u=%08" PRIX32 "(p%u,s%u)", task,
                        read32(core, row), read8(core, row + 5U),
                        read16(core, row + 8U));
        }
        fputc('\n', stderr);
        bootstrap_write_ppm("/tmp/world-trainer-sight", world_video);
        world_die(fixture->name, "trainer sight did not start approach script");
    }
    for (unsigned pulse = 0U; pulse < 80U && world_overworld(core); ++pulse) {
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
    }
    if (world_overworld(core)
        || read16(core, WORLD_TRAINER_OPPONENT_A) != fixture->trainer) {
        fprintf(stderr, "trainer start debug: callback=%08" PRIX32
                " main1=%08" PRIX32 " save1=%08" PRIX32
                " script=%u opponent=%u battleflags=%08" PRIX32
                " newbs=%08" PRIX32 " flag=%02X has=%" PRIu32
                " pos=%u,%u\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2 - 4U),
                read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR),
                world_script_enabled(core) ? 1U : 0U,
                read16(core, WORLD_TRAINER_OPPONENT_A),
                read32(core, ADDR_BATTLE_TYPE_FLAGS),
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                read8(core, world_trainer_flag_address(core, fixture)),
                call_preserving(core, 0x0807FB45U,
                                fixture->trainer, 0U, 0U, 0U),
                read16(core, world_save1(core, fixture->name)),
                read16(core, world_save1(core, fixture->name) + 2U));
        world_die(fixture->name, "trainer battle did not start through sight/input");
    }
    result->trainer_external_flag = (uint16_t)call_preserving(
        core, 0x0807F7D9U, 0U, 0U, 0U, 0U);
    world_finish_battle(core, fixture, result, false);
    result->field_returned = result->battle_completed;
    if (result->battle_outcome != 1U) {
        fprintf(stderr, "trainer outcome debug: %u\n", result->battle_outcome);
        world_die(fixture->name, "trainer input driver did not win battle");
    }
    for (unsigned pulse = 0U; pulse < 40U; ++pulse) {
        if (call_preserving(core, WORLD_FLAG_GET,
                            fixture->flag, 0U, 0U, 0U) == 1U)
            break;
        world_pulse(core, WORLD_KEY_A, 2U, 45U);
        ++result->key_pulses;
    }
    result->state_committed = call_preserving(
        core, WORLD_FLAG_GET, fixture->flag, 0U, 0U, 0U) == 1U;
    if (!result->state_committed) {
        fprintf(stderr, "trainer flag storage debug: owner=%04X seen=%u finalbyte=%02X\n",
                result->trainer_external_flag, result->trainer_flag_seen,
                read8(core, world_trainer_flag_address(core, fixture)));
        world_die(fixture->name, "trainer defeat flag was not committed");
    }
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
                                      uint16_t *x, uint16_t *y,
                                      uint16_t *turn_key)
{
    uint32_t width = read32(core, BOOTSTRAP_VMAP);
    uint32_t height = read32(core, BOOTSTRAP_VMAP + 4U);
    if (width < 18U || height < 17U)
        return false;
    /* Avoid authored edge warps: collision alone does not distinguish a cave
     * entrance warp from an ordinary wall.  Keep the direction-only probe in
     * the interior while retaining a two-tile encounter path. */
    for (uint16_t row = 5U; row + 3U < height - 14U; ++row) {
        for (uint16_t column = 5U; column + 3U < width - 15U; ++column) {
                bool blocked_left = world_collision(core, column - 1U, row);
                bool blocked_up = world_collision(core, column, row - 1U);
                bool blocked_down = world_collision(core, column, row + 1U);
                uint16_t blocked_turn = 0U;
                if (blocked_left)
                    blocked_turn |= WORLD_KEY_LEFT;
                if (blocked_up)
                    blocked_turn |= WORLD_KEY_UP;
                if (blocked_down)
                    blocked_turn |= WORLD_KEY_DOWN;
                if (world_encounter_tile(core, column, row)
                    && world_encounter_tile(core, column + 1U, row)
                    && !world_collision(core, column, row)
                    && !world_collision(core, column + 1U, row)
                    && blocked_turn != 0U) {
                    *x = column;
                    *y = row;
                    *turn_key = blocked_turn;
                    return true;
                }
        }
    }
    return false;
}

static void world_print_encounter_terrain_debug(struct mCore *core,
                                                const struct Fixture *fixture)
{
    uint32_t width = read32(core, BOOTSTRAP_VMAP);
    uint32_t height = read32(core, BOOTSTRAP_VMAP + 4U);
    unsigned terrain = 0U;
    unsigned passable = 0U;
    for (uint16_t row = 0U; row < height - 14U; ++row) {
        for (uint16_t column = 0U; column < width - 15U; ++column) {
            if (world_encounter_tile(core, column, row)) {
                ++terrain;
                if (!world_collision(core, column, row))
                    ++passable;
            }
        }
    }
    fprintf(stderr,
            "encounter terrain debug: fixture=%s dimensions=%" PRIu32
            "x%" PRIu32 " terrain=%u passable=%u\n",
            fixture->name, width - 15U, height - 14U, terrain, passable);
}

static void world_generate_wild_save(const char *rom_path,
                                     const char *save_path,
                                     const struct Fixture *fixture,
                                     uint16_t *x, uint16_t *y,
                                     uint16_t *turn_key)
{
    struct mCore *core;
    world_generate_save(rom_path, save_path, fixture, fixture->x, fixture->y);
    memset(world_video, 0, sizeof(world_video));
    core = bootstrap_open_core(rom_path, save_path, world_video);
    world_continue(core, fixture);
    if (!world_find_encounter_pair(core, x, y, turn_key)) {
        char screenshot[256];
        if (snprintf(screenshot, sizeof(screenshot), "/tmp/%s-terrain",
                     fixture->name) > 0)
            bootstrap_write_ppm(screenshot, world_video);
        world_print_encounter_terrain_debug(core, fixture);
        world_die(fixture->name, "map has no adjacent encounter terrain pair");
    }
    bootstrap_close_core(core);
    world_generate_save(rom_path, save_path, fixture, *x, *y);
}

static void world_record_wild(struct mCore *core,
                              const struct Fixture *fixture,
                              struct FixtureResult *result)
{
    uint16_t species = 0U;
    uint8_t level = 0U;
    for (unsigned frames = 0U; frames < 1800U; frames += 15U) {
        uint32_t enemy = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
        species = read16(core, enemy);
        level = read8(core, enemy + BATTLE_CORE_MON_LEVEL);
        if (read8(core, ADDR_BATTLERS_COUNT) >= 2U
            && read16(core, enemy + BATTLE_CORE_MON_HP) != 0U
            && species != 0U && level != 0U)
            break;
        run_key_frames(core, 0U, 15U);
    }
    if (species == 0U || level == 0U) {
        fprintf(stderr,
                "wild debug: map=%u/%u flags=%08" PRIX32
                " opponent=%u enemy_count=%u callback=%08" PRIX32
                " species=%u level=%u raw=",
                fixture->group, fixture->map,
                read32(core, ADDR_BATTLE_TYPE_FLAGS),
                read16(core, WORLD_TRAINER_OPPONENT_A),
                read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2), species, level);
        for (unsigned byte = 0U; byte < 24U; ++byte)
            fprintf(stderr, "%02X", read8(core, ADDR_ENEMY_PARTY + byte));
        fputc('\n', stderr);
        char screenshot[256];
        if (snprintf(screenshot, sizeof(screenshot), "/tmp/%s-wild-empty",
                     fixture->name) > 0)
            bootstrap_write_ppm(screenshot, world_video);
        world_die(fixture->name, "wild battle has an empty generated enemy");
    }
    if (result->first_wild_species == 0U) {
        result->first_wild_species = species;
        result->first_wild_level = level;
        result->minimum_wild_level = level;
        result->maximum_wild_level = level;
    }
    if (level < result->minimum_wild_level)
        result->minimum_wild_level = level;
    if (level > result->maximum_wild_level)
        result->maximum_wild_level = level;
    unsigned minimum = 0U;
    unsigned maximum = 0U;
    if (strcmp(fixture->name, "waterway_511_land") == 0) {
        minimum = 25U;
        maximum = 31U;
    } else if (strcmp(fixture->name, "wisdom_cave_entrance") == 0
               || strcmp(fixture->name, "wisdom_cave_b1f") == 0) {
        minimum = 34U;
        maximum = 38U;
    } else if (strncmp(fixture->name, "wisdom_cave_", 12U) == 0) {
        minimum = 48U;
        maximum = 51U;
    }
    if (species == 50U || level == 100U
        || (minimum != 0U && (level < minimum || level > maximum)))
        world_die(fixture->name, "wild species/level differs from the native map table");
}

static void world_wild(struct mCore *core, const struct Fixture *fixture,
                       struct FixtureResult *result, uint16_t turn_key)
{
    world_phase = "fresh-core-field-ready";
    world_wait_player_ready(core, fixture);
    uint32_t save1 = world_save1(core, fixture->name);
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    result->start_x = x;
    result->start_y = y;
    if (!world_encounter_tile(core, x, y)
        || !world_encounter_tile(core, x + 1U, y))
        world_die(fixture->name, "saved path is not encounter terrain");

    if (fixture->kind == FIXTURE_WILD) {
        world_phase = "gba-direction-only";
        if (turn_key == 0U)
            world_die(fixture->name, "direction-only key was not prepared");
        static const uint16_t turn_options[] = {
            WORLD_KEY_UP, WORLD_KEY_DOWN, WORLD_KEY_LEFT, WORLD_KEY_RIGHT,
        };
        uint8_t facing = world_player_facing(core);
        uint16_t selected_turn = 0U;
        uint16_t probe_x[4] = {0};
        uint16_t probe_y[4] = {0};
        uint32_t probe_callback[4] = {0};
        size_t state_size = core->stateSize(core);
        void *state = malloc(state_size);
        if (!state || !core->saveState(core, state))
            world_die(fixture->name, "direction-only state capture failed");
        for (unsigned pass = 0U; pass < 2U && selected_turn == 0U; ++pass) {
            for (unsigned option = 0U; option < 4U; ++option) {
                uint16_t candidate = turn_options[option];
                bool same_facing = world_direction_for_key(candidate) == facing;
                if ((turn_key & candidate) == 0U || same_facing != (pass != 0U))
                    continue;
                if (!core->loadState(core, state))
                    world_die(fixture->name, "direction-only state restore failed");
                bool stationary = true;
                for (unsigned probe = 0U; probe < 4U; ++probe) {
                    world_pulse(core, candidate, 1U, 8U);
                    save1 = world_save1(core, fixture->name);
                    if (!world_overworld(core)
                        || read16(core, save1) != x
                        || read16(core, save1 + 2U) != y) {
                        stationary = false;
                        probe_x[option] = read16(core, save1);
                        probe_y[option] = read16(core, save1 + 2U);
                        probe_callback[option] = read32(
                            core, BATTLE_CORE_MAIN_CALLBACK2);
                        break;
                    }
                }
                if (stationary) {
                    selected_turn = candidate;
                    break;
                }
            }
        }
        if (selected_turn == 0U) {
            uint8_t object_id = read8(core, WORLD_PLAYER_AVATAR + 5U);
            uint32_t object = WORLD_OBJECT_EVENTS + object_id * 0x24U;
            fprintf(stderr,
                    "direction probe debug: pos=%u,%u mask=%04X facing=%u"
                    " save=%08" PRIX32 " object=%u/%u,%u"
                    " up=%u,%u/%08" PRIX32
                    " down=%u,%u/%08" PRIX32
                    " left=%u,%u/%08" PRIX32
                    " right=%u,%u/%08" PRIX32 "\n",
                    x, y, turn_key, facing, save1, object_id,
                    read16(core, object + 0x10U),
                    read16(core, object + 0x12U),
                    probe_x[0], probe_y[0], probe_callback[0],
                    probe_x[1], probe_y[1], probe_callback[1],
                    probe_x[2], probe_y[2], probe_callback[2],
                    probe_x[3], probe_y[3], probe_callback[3]);
            world_die(fixture->name, "no stationary direction-only input found");
        }
        if (!core->loadState(core, state))
            world_die(fixture->name, "direction-only final state restore failed");
        free(state);
        for (unsigned count = 0U; count < 32U; ++count) {
            world_pulse(core, selected_turn, 1U, 8U);
            ++result->rotations;
            save1 = world_save1(core, fixture->name);
            if (!world_overworld(core))
                world_die(fixture->name,
                          "direction-only input started encounter");
            if (read16(core, save1) != x || read16(core, save1 + 2U) != y)
                world_die(fixture->name, "direction-only input moved the player");
        }
    }

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
            world_record_wild(core, fixture, result);
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
    if (!result->encounter_found) {
        fprintf(stderr,
                "encounter walk debug: map=%u/%u steps=%u rotations=%u"
                " pos=%u,%u terrain=%u/%u callback=%08" PRIX32
                " header=%" PRIu32 " cooldown=%" PRIu32
                " attrs=%08" PRIX32 " wild_data=",
                fixture->group, fixture->map, result->successful_steps,
                result->rotations, x, y,
                world_encounter_tile(core, x, y),
                world_encounter_tile(core, x + 1U, y),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                call_preserving(core, 0x08082521U, 0U, 0U, 0U, 0U),
                call_preserving(core, 0x08082E39U, 1U, 0U, 0U, 0U),
                call_preserving(core, WORLD_MAP_GRID_FIELD,
                                x, y, 0xFFU, 0U));
        for (unsigned byte = 0U; byte < 16U; ++byte)
            fprintf(stderr, "%02X", read8(core, 0x0203861CU + byte));
        fputc('\n', stderr);
        world_die(fixture->name, "sufficient normal walking produced zero encounters");
    }

    unsigned post_flee_steps = 0U;
    unsigned post_flee_no_encounter = 0U;
    unsigned post_flee_streak = 0U;
    unsigned maximum_post_flee_streak = 0U;
    for (unsigned attempt = 0U; attempt < 80U && post_flee_steps < 20U; ++attempt) {
        bool moved = world_walk_to_new_tile(core, key, &x, &y, result);
        if (!moved && !world_overworld(core)) {
            ++result->encounters;
            world_record_wild(core, fixture, result);
            world_finish_battle(core, fixture, result, true);
            x = read16(core, save1);
            y = read16(core, save1 + 2U);
            post_flee_streak = 0U;
        } else if (moved) {
            ++post_flee_steps;
            ++post_flee_no_encounter;
            ++post_flee_streak;
            if (post_flee_streak > maximum_post_flee_streak)
                maximum_post_flee_streak = post_flee_streak;
        }
        key = key == WORLD_KEY_RIGHT ? WORLD_KEY_LEFT : WORLD_KEY_RIGHT;
    }
    result->fled_and_moved = result->battle_completed
        && post_flee_steps >= 10U && post_flee_no_encounter != 0U
        && maximum_post_flee_streak >= 10U
        && result->encounters < result->successful_steps;
    if (!result->fled_and_moved)
        world_die(fixture->name, "post-flee cadence prevented ordinary movement");
    if (!world_overworld(core)) {
        ++result->encounters;
        world_record_wild(core, fixture, result);
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
    uint16_t turn_key = 0U;
    if (snprintf(save_path, sizeof(save_path), "%s/%s.srm",
                 directory, fixture->name) <= 0)
        world_die(fixture->name, "save path formatting failed");
    if (fixture->kind == FIXTURE_WILD)
        world_generate_wild_save(rom_path, save_path, fixture,
                                 &x, &y, &turn_key);
    else
        world_generate_save(rom_path, save_path, fixture, x, y);

    world_phase = "fresh-core";
    memset(world_video, 0, sizeof(world_video));
    struct mCore *core = bootstrap_open_core(rom_path, save_path, world_video);
    world_continue(core, fixture);
    const char *capture_directory = getenv("WORLD_CAPTURE_DIR");
    if (capture_directory != NULL && capture_directory[0] != '\0') {
        char screenshot[512];
        if (snprintf(screenshot, sizeof(screenshot), "%s/%s",
                     capture_directory, fixture->name) > 0)
            bootstrap_write_ppm(screenshot, world_video);
    }
    result.natural_continue = true;
    result.start_x = read16(core, world_save1(core, fixture->name));
    result.start_y = read16(core, world_save1(core, fixture->name) + 2U);
    if (fixture->kind == FIXTURE_TRAINER) {
        world_trainer(core, fixture, &result);
    } else if (fixture->kind == FIXTURE_WILD
               || fixture->kind == FIXTURE_WILD_WALK_ONLY) {
        world_wild(core, fixture, &result, turn_key);
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
           "\"encounters\":%u,\"rotations\":%u,"
           "\"first_wild_species\":%u,\"first_wild_level\":%u,"
           "\"minimum_wild_level\":%u,\"maximum_wild_level\":%u,"
           "\"battle_outcome\":%u,\"trainer_flag_seen\":%u,"
           "\"trainer_external_flag\":%u}",
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
           result->encounters, result->rotations,
           result->first_wild_species, result->first_wild_level,
           result->minimum_wild_level, result->maximum_wild_level,
           result->battle_outcome, result->trainer_flag_seen,
           result->trainer_external_flag);
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
