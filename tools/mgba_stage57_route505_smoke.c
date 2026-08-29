/*
 * Stage57 Route 505 Research-profile regression smoke.
 *
 * The fixture starts from a blank flash save, reaches logical T505 (3/23)
 * through the stock warp/save path, reopens that save through Continue, and
 * then uses only GBA walking/flee input for 66 natural encounters.  Direct ROM
 * calls are limited to deterministic fixture preparation and read-only
 * identity inspection.
 */
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

#include <sys/stat.h>

enum {
    WORLD_FLAG_GET = 0x0806DEC5U,
    WORLD_FLAG_SET = 0x0806DE75U,
    WORLD_MAP_GRID_FIELD = 0x08058805U,
    WORLD_FIELD_CONTROLS_LOCKED = 0x03000F9CU,
    WORLD_OBJECT_EVENTS = 0x02036D6CU,
    WORLD_PLAYER_AVATAR = 0x02036FACU,
    WORLD_PLAYER_RUNNING_STATE_OFFSET = 2U,
    WORLD_PLAYER_TILE_TRANSITION_STATE_OFFSET = 3U,
    WORLD_QUEST_LOG_STATE = 0x0203AD72U,
    WORLD_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    WORLD_PLAYER_MOVING = 2U,
    WORLD_PLAYER_TILE_CENTER = 2U,
    WORLD_KEY_A = 1U,
    WORLD_KEY_B = 2U,
    WORLD_KEY_RIGHT = 16U,
    WORLD_KEY_LEFT = 32U,
    WORLD_KEY_UP = 64U,
    WORLD_FIELD_BORDER = 7U,
    WORLD_ENCOUNTER_ATTRIBUTE = 4U,
    WORLD_ENCOUNTER_TILE = 1U,
    WORLD_QA_MOVE_DARK_PULSE = 369U,
};

enum FixtureKind {
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

struct FixtureResult {
    bool battle_seen;
    bool battle_completed;
    bool encounter_found;
    bool duplicate_prevented;
    unsigned key_pulses;
    unsigned successful_steps;
    unsigned encounters;
    uint8_t battle_outcome;
};

static const char *world_phase = "startup";
static color_t world_video[240U * 160U];

static void world_die(const char *fixture, const char *message)
{
    fprintf(stderr, "mgba-stage57-route505[%s][%s]: %s\n",
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

static void world_continue(struct mCore *core, const struct Fixture *fixture)
{
    world_phase = "fresh-core-continue";
    run_key_frames(core, 0U, BOOTSTRAP_TITLE_FRAMES);
    for (unsigned pulse = 0U; pulse < BOOTSTRAP_CONTINUE_PULSES; ++pulse) {
        world_pulse(core, pulse == 0U ? 8U : WORLD_KEY_A,
                    2U, BOOTSTRAP_CONTINUE_WAIT_FRAMES);
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (world_overworld(core)
            && save1 >= 0x02000000U && save1 < 0x02040000U
            && !(save1 & 3U)
            && read8(core, save1 + 4U) == fixture->group
            && read8(core, save1 + 5U) == fixture->map) {
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

static void world_wait_player_ready(struct mCore *core,
                                    const struct Fixture *fixture)
{
    unsigned stable_frames = 0U;
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
    world_die(fixture->name, "Continue did not settle on an input-ready field");
}

static bool world_encounter_tile(struct mCore *core, uint16_t x, uint16_t y)
{
    return (call_preserving(core, WORLD_MAP_GRID_FIELD,
                            x + WORLD_FIELD_BORDER, y + WORLD_FIELD_BORDER,
                            WORLD_ENCOUNTER_ATTRIBUTE, 0U)
            & WORLD_ENCOUNTER_TILE) != 0U;
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
    world_phase = "gba-run-from-wild";
    for (unsigned pulse = 0U; pulse < 1200U; ++pulse) {
        if (read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0U)
            result->battle_outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            || read8(core, ADDR_BATTLERS_COUNT) != 0U)
            battle_initialized = true;
        if (battle_initialized && world_overworld(core)) {
            run_key_frames(core, 0U, 180U);
            if (world_overworld(core) && !world_script_enabled(core)) {
                result->battle_completed = true;
                return;
            }
        }
        if (flee && pulse % 5U == 0U) {
            world_pulse(core, WORLD_KEY_RIGHT, 2U, 16U);
            world_pulse(core, 128U, 2U, 16U);
        }
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
    world_die(fixture->name, "battle did not return to field through keys");
}

static void world_generate_wild_save(const char *rom_path,
                                     const char *save_path,
                                     const struct Fixture *fixture,
                                     uint16_t *x, uint16_t *y,
                                     uint16_t *turn_key)
{
    bootstrap_write_blank_save(save_path);
    struct mCore *core = bootstrap_open_core(rom_path, save_path, NULL);
    run_trace_prefix(core);
    run_fixed_frames(core);
    *x = 21U;
    *y = 14U;
    *turn_key = 0U;
    (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                          fixture->group, fixture->map, *x, *y);
    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
    uint32_t save1 = world_save1(core, fixture->name);
    if (read8(core, save1 + 4U) != fixture->group
        || read8(core, save1 + 5U) != fixture->map
        || read16(core, save1) != *x || read16(core, save1 + 2U) != *y
        || !world_overworld(core))
        world_die(fixture->name, "stock warp did not reach T505");
    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot) {
        uint32_t mon = BOOTSTRAP_PLAYER_PARTY + slot * BOOTSTRAP_MON_SIZE;
        create_mon(core, mon, 150U, 100U);
        set_mon_data_u32(core, mon, MON_DATA_MOVE1,
                         WORLD_QA_MOVE_DARK_PULSE);
        set_mon_data_u32(core, mon, MON_DATA_PP1, 63U);
    }
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);
    /* Persist the post-game Research profile with the generated route save.
     * Badge 1 is deliberately set only after the final Continue: loading T505
     * with that flag already persisted changes the blocked-turn field probe. */
    (void)call_preserving(core, WORLD_FLAG_SET, 0x082CU, 0U, 0U, 0U);
    if (call_preserving(core, WORLD_FLAG_GET, 0x082CU, 0U, 0U, 0U) != 1U
        || call_preserving(core, 0x09378799U, 15U, 1U, 0U, 0U) != 0U)
        world_die(fixture->name, "Research profile preparation failed");
    bootstrap_prepare_save_map_view(core);
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        world_die(fixture->name, "T505 save failed");
    bootstrap_close_core(core);
}

#ifndef S57_ROUTE505_ENCOUNTER_TARGET
#define S57_ROUTE505_ENCOUNTER_TARGET 66U
#endif

#ifndef S57_ROUTE505_MIN_POST_FLEE_STREAK
#define S57_ROUTE505_MIN_POST_FLEE_STREAK 10U
#endif

enum {
    S57_ENCOUNTER_TARGET = S57_ROUTE505_ENCOUNTER_TARGET,
    S57_MINIMUM_POST_FLEE_STREAK = S57_ROUTE505_MIN_POST_FLEE_STREAK,
    S57_ATTEMPT_LIMIT = 8000U,
    S57_QOL_DISPATCH = 0x09378799U,
    S57_FLAG_BADGE_1 = 0x0820U,
    S57_FLAG_HALL_OF_FAME = 0x082CU,
    S57_SERVICE_SET_RESEARCH_PROFILE = 15U,
    S57_PROFILE_RESEARCH = 1U,
    S57_GET_SPECIES_NAME = 0x080406C5U,
    S57_FRONT_TABLE_POINTER = 0x08000128U,
    S57_LZ77_UNCOMP_WRAM = 0x081C7A91U,
    S57_NICKNAME_SCRATCH = 0x0203E800U,
    S57_CANONICAL_NAME_SCRATCH = 0x0203E820U,
    S57_PIC_EXPECTED = 0x0203A800U,
    S57_NAME_SIZE = 11U,
    S57_PIC_SIZE = 2048U,
    S57_MON_DATA_NICKNAME = 2U,
    S57_MON_DATA_SPECIES = 11U,
    S57_MON_DATA_SPECIES2 = 65U,
    S57_BATTLE_NICKNAME_OFFSET = 0x30U,
    S57_BATTLER_SPRITE_IDS = 0x02023CA4U,
    S57_SPRITES = 0x020205B8U,
    S57_SPRITE_SIZE = 68U,
    S57_OBJ_VRAM = 0x06010000U,
};

static const uint16_t s57_allowed_species[] = {
    14U, 24U, 29U, 32U, 89U, 97U,
    431U, 511U, 521U, 535U, 540U, 784U,
    809U, 953U, 990U, 1003U, 1316U, 1524U,
};

static const uint16_t s57_forbidden_old_t503_species[] = {
    524U, 585U, 619U, 717U, 763U, 820U,
    860U, 870U, 956U, 1300U, 1489U,
};

static const uint16_t s57_identity_targets[] = {92U, 717U, 804U};

struct S57RouteAudit {
    unsigned counts[ARRAY_LEN(s57_allowed_species)];
    unsigned encounters;
    unsigned natural_species_checks;
    unsigned natural_name_checks;
    unsigned direct_species_checks;
    unsigned direct_name_checks;
    unsigned direct_front_checks;
    unsigned successful_steps;
    unsigned key_pulses;
    unsigned maximum_post_flee_streak;
    uint8_t minimum_level;
    uint8_t maximum_level;
    uint16_t first_species;
    uint8_t first_level;
    uint64_t direct_front_digests[ARRAY_LEN(s57_identity_targets)];
};

static void s57_die(const char *phase, const char *message)
{
    fprintf(stderr, "mgba-stage57-route505[%s]: %s\n", phase, message);
    exit(1);
}

static int s57_species_index(const uint16_t *values, size_t count,
                             uint16_t species)
{
    for (size_t index = 0U; index < count; ++index) {
        if (values[index] == species)
            return (int)index;
    }
    return -1;
}

static uint64_t s57_digest(struct mCore *core, uint32_t address, unsigned size)
{
    uint64_t digest = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < size; ++index) {
        digest ^= read8(core, address + index);
        digest *= UINT64_C(1099511628211);
    }
    return digest;
}

static uint64_t s57_host_digest(const uint8_t *bytes, unsigned size)
{
    uint64_t digest = UINT64_C(14695981039346656037);
    for (unsigned index = 0U; index < size; ++index) {
        digest ^= bytes[index];
        digest *= UINT64_C(1099511628211);
    }
    return digest;
}

static void s57_clear(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0U; index < size; ++index)
        write8(core, address + index, 0U);
}

static void s57_verify_name(struct mCore *core, uint32_t mon,
                            uint16_t species, bool check_battle)
{
    uint32_t battle_nickname = ADDR_BATTLE_MONS + BATTLE_MON_SIZE
        + S57_BATTLE_NICKNAME_OFFSET;
    bool terminated = false;
    uint8_t preserved_nickname[S57_NAME_SIZE];
    uint8_t preserved_canonical[S57_NAME_SIZE];

    for (unsigned index = 0U; index < S57_NAME_SIZE; ++index) {
        preserved_nickname[index] = read8(
            core, S57_NICKNAME_SCRATCH + index);
        preserved_canonical[index] = read8(
            core, S57_CANONICAL_NAME_SCRATCH + index);
    }

    s57_clear(core, S57_NICKNAME_SCRATCH, S57_NAME_SIZE);
    s57_clear(core, S57_CANONICAL_NAME_SCRATCH, S57_NAME_SIZE);
    if (mon != 0U) {
        (void)call_preserving(core, BATTLE_CORE_GET_MON_DATA, mon,
                              S57_MON_DATA_NICKNAME,
                              S57_NICKNAME_SCRATCH, 0U);
    }
    (void)call_preserving(core, S57_GET_SPECIES_NAME,
                          S57_CANONICAL_NAME_SCRATCH, species, 0U, 0U);
    for (unsigned index = 0U; index < S57_NAME_SIZE; ++index) {
        uint8_t canonical = read8(core, S57_CANONICAL_NAME_SCRATCH + index);
        if ((mon != 0U
             && read8(core, S57_NICKNAME_SCRATCH + index) != canonical)
            || (check_battle
                && read8(core, battle_nickname + index) != canonical)) {
            fprintf(stderr,
                    "identity name mismatch species=%u byte=%u party=%02X "
                    "battle=%02X canonical=%02X\n",
                    species, index,
                    read8(core, S57_NICKNAME_SCRATCH + index),
                    read8(core, battle_nickname + index), canonical);
            s57_die("identity-name", "nickname/canonical Species name differs");
        }
        if (canonical == 0xFFU) {
            terminated = true;
            break;
        }
    }
    if (!terminated)
        s57_die("identity-name", "canonical Species name is unterminated");
    for (unsigned index = 0U; index < S57_NAME_SIZE; ++index) {
        write8(core, S57_NICKNAME_SCRATCH + index,
               preserved_nickname[index]);
        write8(core, S57_CANONICAL_NAME_SCRATCH + index,
               preserved_canonical[index]);
    }
}

static uint64_t s57_verify_front(struct mCore *core, uint16_t species)
{
    uint32_t root = read32(core, S57_FRONT_TABLE_POINTER);
    uint32_t row = root + (uint32_t)species * 8U;
    uint32_t compressed = read32(core, row);

    if (root < 0x08000000U || root >= 0x0A000000U
        || compressed < 0x08000000U || compressed >= 0x0A000000U
        || read16(core, row + 6U) != species)
        s57_die("identity-front", "front resource row is invalid");
    uint8_t preserved[S57_PIC_SIZE];
    uint8_t expected[S57_PIC_SIZE];
    for (unsigned byte = 0U; byte < S57_PIC_SIZE; ++byte)
        preserved[byte] = read8(core, S57_PIC_EXPECTED + byte);
    s57_clear(core, S57_PIC_EXPECTED, S57_PIC_SIZE);
    (void)call_preserving(core, S57_LZ77_UNCOMP_WRAM,
                          compressed, S57_PIC_EXPECTED, 0U, 0U);
    for (unsigned byte = 0U; byte < S57_PIC_SIZE; ++byte) {
        expected[byte] = read8(core, S57_PIC_EXPECTED + byte);
        write8(core, S57_PIC_EXPECTED + byte, preserved[byte]);
    }
    uint64_t expected_digest = s57_host_digest(expected, S57_PIC_SIZE);
    uint64_t loaded_digest = 0U;
    uint8_t last_sprite_id = 0xFFU;
    uint32_t last_tile = 0U;

    for (unsigned frame = 0U; frame < 720U; ++frame) {
        uint8_t sprite_id = read8(core, S57_BATTLER_SPRITE_IDS + 1U);
        if (sprite_id < 128U) {
            last_sprite_id = sprite_id;
            uint32_t sprite = S57_SPRITES
                + (uint32_t)sprite_id * S57_SPRITE_SIZE;
            uint8_t flags = read8(core, sprite + 0x3EU);
            uint32_t tile = read16(core, sprite + 4U) & 0x03FFU;
            uint32_t loaded = S57_OBJ_VRAM + tile * 32U;
            last_tile = tile;
            loaded_digest = s57_digest(core, loaded, S57_PIC_SIZE);
            if ((flags & 1U) != 0U && (flags & 4U) == 0U) {
                bool equal = true;
                for (unsigned byte = 0U; byte < S57_PIC_SIZE; ++byte) {
                    if (read8(core, loaded + byte) != expected[byte]) {
                        equal = false;
                        break;
                    }
                }
                if (equal)
                    return expected_digest;
            }
        }
        run_key_frames(core, 0U, 1U);
    }
    fprintf(stderr, "front OBJ VRAM mismatch species=%u sprite=%u tile=%u "
            "expected=%016" PRIx64 " loaded=%016" PRIx64
            " sprite_ids=%u/%u/%u/%u positions=%u/%u/%u/%u callback=%08"
            PRIx32 "\n",
            species, last_sprite_id, last_tile,
            expected_digest, loaded_digest,
            read8(core, S57_BATTLER_SPRITE_IDS),
            read8(core, S57_BATTLER_SPRITE_IDS + 1U),
            read8(core, S57_BATTLER_SPRITE_IDS + 2U),
            read8(core, S57_BATTLER_SPRITE_IDS + 3U),
            read8(core, ADDR_BATTLER_POSITIONS),
            read8(core, ADDR_BATTLER_POSITIONS + 1U),
            read8(core, ADDR_BATTLER_POSITIONS + 2U),
            read8(core, ADDR_BATTLER_POSITIONS + 3U),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2));
    s57_die("identity-front", "battle OBJ VRAM differs from front resource");
    return 0U;
}

static void s57_wait_for_enemy(struct mCore *core,
                               uint16_t *species, uint8_t *level)
{
    uint32_t enemy = ADDR_BATTLE_MONS + BATTLE_MON_SIZE;
    for (unsigned frames = 0U; frames < 1800U; frames += 15U) {
        *species = read16(core, enemy);
        *level = read8(core, enemy + BATTLE_CORE_MON_LEVEL);
        if (!world_overworld(core)
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U
            && read8(core, ADDR_BATTLERS_COUNT) >= 2U
            && read16(core, enemy + BATTLE_CORE_MON_HP) != 0U
            && *species != 0U && *level != 0U)
            return;
        run_key_frames(core, 0U, 15U);
    }
    fprintf(stderr,
            "enemy wait timeout battle_species=%u level=%u callback=%08" PRIx32
            " newbs=%08" PRIx32 " battlers=%u count=%u\n",
            *species, *level, read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read8(core, ADDR_BATTLERS_COUNT),
            read8(core, BATTLE_CORE_ENEMY_PARTY_COUNT));
    s57_die("encounter", "natural wild battle did not create an enemy");
}

static void s57_record_natural_encounter(struct mCore *core,
                                         struct S57RouteAudit *audit)
{
    uint16_t species = 0U;
    uint8_t level = 0U;
    s57_wait_for_enemy(core, &species, &level);

    if (s57_species_index(s57_forbidden_old_t503_species,
                          ARRAY_LEN(s57_forbidden_old_t503_species),
                          species) >= 0) {
        fprintf(stderr, "old T503 species leaked into T505: %u\n", species);
        s57_die("encounter-species", "forbidden old-binding Species observed");
    }
    int allowed = s57_species_index(s57_allowed_species,
                                    ARRAY_LEN(s57_allowed_species), species);
    if (allowed < 0 || level < 6U || level > 14U) {
        fprintf(stderr, "unexpected T505 encounter species=%u level=%u\n",
                species, level);
        s57_die("encounter-species", "Species/level is outside T505 contract");
    }
    /* Natural encounters must prove the same identity contract as the
     * direct fixtures.  This specifically covers Collection Supply's
     * post-generation form replacement, which the old species/level-only
     * assertion could not detect. */
    s57_verify_name(core, ADDR_ENEMY_PARTY, species, true);
    ++audit->natural_name_checks;
    ++audit->counts[(unsigned)allowed];
    ++audit->encounters;
    ++audit->natural_species_checks;
    if (audit->first_species == 0U) {
        audit->first_species = species;
        audit->first_level = level;
        audit->minimum_level = level;
        audit->maximum_level = level;
    }
    if (level < audit->minimum_level)
        audit->minimum_level = level;
    if (level > audit->maximum_level)
        audit->maximum_level = level;
}

static void s57_prepare_research_save(const char *rom_path,
                                      const char *save_path,
                                      const struct Fixture *fixture,
                                      uint16_t *x, uint16_t *y)
{
    uint16_t unused_turn_key = 0U;
    /* Match the reviewed world-E2E lifecycle: validate one generated save
     * through a real Continue before regenerating the independent fixture
     * consumed by the measured run.  Besides checking the title/recap path,
     * this keeps libmGBA's core lifecycle identical to the established
     * runner from which this focused smoke was derived. */
    world_generate_wild_save(rom_path, save_path, fixture,
                             x, y, &unused_turn_key);
    memset(world_video, 0, sizeof(world_video));
    struct mCore *core = bootstrap_open_core(
        rom_path, save_path, world_video);
    world_continue(core, fixture);
    world_wait_player_ready(core, fixture);
    if (!world_encounter_tile(core, *x, *y)
        || !world_encounter_tile(core, *x + 1U, *y))
        s57_die("prepare", "validated save lacks adjacent encounter terrain");
    bootstrap_close_core(core);
    world_generate_wild_save(rom_path, save_path, fixture,
                             x, y, &unused_turn_key);
}

static void s57_run_natural_encounters(struct mCore *core,
                                       const struct Fixture *fixture,
                                       struct S57RouteAudit *audit)
{
    struct FixtureResult world_result = {0};
    world_result.duplicate_prevented = true;
    world_wait_player_ready(core, fixture);
    uint32_t save1 = world_save1(core, fixture->name);
    uint16_t x = read16(core, save1);
    uint16_t y = read16(core, save1 + 2U);
    if (!world_encounter_tile(core, x, y)
        || !world_encounter_tile(core, x + 1U, y))
        s57_die("field", "prepared route is not adjacent encounter terrain");

    uint16_t key = WORLD_KEY_RIGHT;
    unsigned post_flee_streak = 0U;
    for (unsigned attempt = 0U;
         attempt < S57_ATTEMPT_LIMIT
             && audit->encounters < S57_ENCOUNTER_TARGET;
         ++attempt) {
        bool moved = world_walk_to_new_tile(core, key, &x, &y, &world_result);
        if (!moved && !world_overworld(core)) {
            s57_record_natural_encounter(core, audit);
            world_result.encounters = audit->encounters;
            world_result.encounter_found = true;
            world_finish_battle(core, fixture, &world_result, true);
            x = read16(core, save1);
            y = read16(core, save1 + 2U);
            post_flee_streak = 0U;
        } else if (moved && audit->encounters != 0U) {
            ++post_flee_streak;
            if (post_flee_streak > audit->maximum_post_flee_streak)
                audit->maximum_post_flee_streak = post_flee_streak;
        }
        key = key == WORLD_KEY_RIGHT ? WORLD_KEY_LEFT : WORLD_KEY_RIGHT;
    }
    if (audit->encounters != S57_ENCOUNTER_TARGET)
        s57_die("encounter-count", "natural encounter target was not reached");
    if (!world_overworld(core) || !world_result.battle_completed)
        s57_die("field-return", "flee/field movement cadence did not recover");
#if S57_ROUTE505_MIN_POST_FLEE_STREAK > 0
    if (audit->maximum_post_flee_streak < S57_MINIMUM_POST_FLEE_STREAK)
        s57_die("field-return", "post-flee movement streak was too short");
#endif
    audit->successful_steps = world_result.successful_steps;
    audit->key_pulses = world_result.key_pulses;
}

static void s57_verify_direct_identity_targets(struct mCore *core,
                                               struct S57RouteAudit *audit)
{
    static const uint16_t player_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_SCRATCH, 0U, 0U, 0U,
    };
    static const uint8_t player_pp[BATTLE_CORE_MOVE_SLOTS] = {
        35U, 0U, 0U, 0U,
    };
    static const uint16_t enemy_moves[BATTLE_CORE_MOVE_SLOTS] = {
        BATTLE_CORE_MOVE_TACKLE, 0U, 0U, 0U,
    };
    static const uint8_t enemy_pp[BATTLE_CORE_MOVE_SLOTS] = {
        35U, 0U, 0U, 0U,
    };
    struct Snapshot field = take_snapshot(core);

    for (unsigned index = 0U; index < ARRAY_LEN(s57_identity_targets);
         ++index) {
        uint16_t species = s57_identity_targets[index];
        (void)setup_custom_wild(core, &field, 150U, species,
                                player_moves, player_pp,
                                enemy_moves, enemy_pp);
        uint16_t party_species = (uint16_t)call_preserving(
            core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
            S57_MON_DATA_SPECIES2, 0U, 0U);
        uint16_t battle_species = read16(
            core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE);
        if (party_species != species || battle_species != species)
            s57_die("direct-identity", "target Species identity differs");
        ++audit->direct_species_checks;
        s57_verify_name(core, ADDR_ENEMY_PARTY, species, true);
        ++audit->direct_name_checks;
        audit->direct_front_digests[index] = s57_verify_front(core, species);
        ++audit->direct_front_checks;
    }
    free(field.bytes);
}

static void s57_print_u16_array(const uint16_t *values, size_t count)
{
    putchar('[');
    for (size_t index = 0U; index < count; ++index) {
        if (index != 0U)
            putchar(',');
        printf("%u", values[index]);
    }
    putchar(']');
}

static void s57_print_result(const char *rom_sha256,
                             const struct S57RouteAudit *audit)
{
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"rom_sha256\":\"%s\",\"fixed_rtc_unix\":946684800,"
           "\"fixture\":{\"name\":\"stage57_route505_research\","
           "\"logical_map\":\"T505\",\"physical_map\":\"3/23\","
           "\"profile\":\"research\",\"profile_service\":15,"
           "\"unlock_flags\":[\"badge_1\",\"hall_of_fame\"],"
           "\"encounter_target\":%u,\"allowed_species\":",
           rom_sha256, S57_ENCOUNTER_TARGET);
    s57_print_u16_array(s57_allowed_species,
                        ARRAY_LEN(s57_allowed_species));
    printf(",\"forbidden_old_t503_species\":");
    s57_print_u16_array(s57_forbidden_old_t503_species,
                        ARRAY_LEN(s57_forbidden_old_t503_species));
    printf(",\"identity_targets\":");
    s57_print_u16_array(s57_identity_targets,
                        ARRAY_LEN(s57_identity_targets));
    printf(",\"identity_contract\":{\"natural_encounters\":["
           "\"battlemon_species_in_t505_allowlist\","
           "\"old_t503_species_forbidden\","
           "\"party_nickname_equals_canonical_species_name\"],"
           "\"direct_targets\":["
           "\"party_and_battlemon_species_equal_target\","
           "\"party_and_battle_nickname_equal_canonical_species_name\","
           "\"front_table_lz77_equals_battle_obj_vram\"]}},"
           "\"result\":{\"encounters\":%u,\"successful_steps\":%u,"
           "\"key_pulses\":%u,\"maximum_post_flee_streak\":%u,"
           "\"first_species\":%u,\"first_level\":%u,"
           "\"minimum_level\":%u,\"maximum_level\":%u,"
           "\"natural_species_checks\":%u,\"natural_name_checks\":%u,"
           "\"direct_species_checks\":%u,\"direct_name_checks\":%u,"
           "\"direct_front_checks\":%u,\"observed_species\":[",
           audit->encounters, audit->successful_steps, audit->key_pulses,
           audit->maximum_post_flee_streak, audit->first_species,
           audit->first_level, audit->minimum_level, audit->maximum_level,
           audit->natural_species_checks, audit->natural_name_checks,
           audit->direct_species_checks, audit->direct_name_checks,
           audit->direct_front_checks);
    bool first = true;
    for (unsigned index = 0U; index < ARRAY_LEN(s57_allowed_species);
         ++index) {
        if (audit->counts[index] == 0U)
            continue;
        if (!first)
            putchar(',');
        first = false;
        printf("{\"species\":%u,\"count\":%u}",
               s57_allowed_species[index], audit->counts[index]);
    }
    printf("],\"direct_front_fnv1a64\":[");
    for (unsigned index = 0U; index < ARRAY_LEN(s57_identity_targets);
         ++index) {
        if (index != 0U)
            putchar(',');
        printf("{\"species\":%u,\"digest\":\"%016" PRIx64 "\"}",
               s57_identity_targets[index],
               audit->direct_front_digests[index]);
    }
    printf("],\"warnings\":0}}\n");
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr,
                "usage: %s ROM EXPECTED_ROM_SHA256 WORK_DIRECTORY\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        s57_die("identity", "ROM SHA-256 mismatch");
    if (mkdir(argv[3], 0700) != 0 && errno != EEXIST) {
        perror("mkdir");
        return 2;
    }
    char save_path[4096];
    if (snprintf(save_path, sizeof(save_path), "%s/route505_research.srm",
                 argv[3]) <= 0)
        s57_die("path", "save path formatting failed");

    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    bootstrap_phase = "stage57-route505";
    world_phase = "prepare";
    const struct Fixture fixture = {
        "stage57_route505_research", FIXTURE_WILD_WALK_ONLY,
        3U, 23U, 10U, 10U, 0U, 0U, 0U, 0U, 0U,
    };
    struct S57RouteAudit audit = {0};
    uint16_t x = fixture.x;
    uint16_t y = fixture.y;
    s57_prepare_research_save(argv[1], save_path, &fixture, &x, &y);

    memset(world_video, 0, sizeof(world_video));
    struct mCore *core = bootstrap_open_core(argv[1], save_path, world_video);
    world_continue(core, &fixture);
    (void)call_preserving(core, WORLD_FLAG_SET,
                          S57_FLAG_BADGE_1, 0U, 0U, 0U);
    if (call_preserving(core, WORLD_FLAG_GET,
                        S57_FLAG_HALL_OF_FAME, 0U, 0U, 0U) != 1U
        || call_preserving(core, WORLD_FLAG_GET,
                           S57_FLAG_BADGE_1, 0U, 0U, 0U) != 1U)
        s57_die("fresh-continue", "Research unlock flags differ");
    s57_run_natural_encounters(core, &fixture, &audit);
    s57_verify_direct_identity_targets(core, &audit);
    bootstrap_close_core(core);

    if (audit.natural_species_checks != S57_ENCOUNTER_TARGET
        || audit.natural_name_checks != S57_ENCOUNTER_TARGET
        || audit.direct_species_checks != ARRAY_LEN(s57_identity_targets)
        || audit.direct_name_checks != ARRAY_LEN(s57_identity_targets)
        || audit.direct_front_checks != ARRAY_LEN(s57_identity_targets))
        s57_die("contract", "identity check counts differ");
    if (log_problem_count != 0U)
        s57_die("logging", "mGBA emitted warning/error diagnostics");
    s57_print_result(rom_sha256, &audit);
    return 0;
}
