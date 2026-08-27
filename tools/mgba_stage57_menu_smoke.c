/*
 * Stage57 exact-ROM field-menu lifecycle smoke for libmGBA.
 *
 * The runner starts from a natural Continue field, calls every Stage57 menu
 * owner through its real ROM entry point, and drives the registered engine
 * task with GBA keys.  It checks cursor movement, B cancellation, script/task
 * ownership, framebuffer restoration, and mGBA diagnostics.  Collection
 * Supply is exercised through all fourteen authored hosts.
 */
#define CODEX_IPAD_BOOTSTRAP_EMBEDDED
#include "mgba_codex_battle_ipad_bootstrap.c"

#include <errno.h>
#include <sys/stat.h>

enum {
    WORLD_KEY_A = 1U,
    WORLD_KEY_B = 2U,
    WORLD_KEY_START = 8U,
    WORLD_KEY_UP = 64U,
    WORLD_KEY_DOWN = 128U,

    S57_TASKS = 0x030050D0U,
    S57_TASK_SIZE = 40U,
    S57_TASK_ACTIVE = 4U,
    S57_TASK_DATA = 8U,
    S57_FIELD_LOCK = 0x03000F9CU,
    S57_QUEST_LOG_STATE = 0x0203AD72U,
    S57_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    S57_SPECIAL_VAR_8004 = 0x02036FF4U,
    S57_MENU_CURSOR = 0x0203AD5EU,
    S57_CREATE_TASK = 0x08076BB5U,
    S57_DESTROY_TASK = 0x08076CA1U,
    S57_TASK_DUMMY = 0x08076D7DU,
    S57_FLAG_SET = 0x0806DE75U,
    S57_SCRIPT_CONTEXT2_ENABLE = 0x08069201U,
    S57_ENABLE_BOTH_CONTEXTS = 0x080693F5U,
    S57_ADD_BAG_ITEM = 0x08099A8DU,

    S57_WILD_OPEN_TASK = 0x092205B5U,
    S57_MOVE_OPEN = 0x092CFFF1U,
    S57_ACQUISITION_OPEN_HOST = 0x092D0DB9U,
    S57_BP_OPEN = 0x092DC385U,
    S57_QOL_SUPPLY_OPEN = 0x093774C9U,
    S57_QOL_QUANTITY_ADAPTER = 0x093777C9U,
    S57_RESEARCH_OPEN = 0x093BE729U,
    S57_RESEARCH_TEST_INITIALIZE = 0x093BEC69U,
    S57_RESEARCH_TEST_UNLOCK_ALL = 0x093BEC9DU,
    S57_REWARD_FIELD_SCIENTIST = 0x093C10E9U,
    S57_REWARD_TEST_INITIALIZE = 0x093C12EDU,
    S57_FACTORY_FIELD_RECEPTION = 0x093C4489U,
    S57_FACTORY_TEST_INITIALIZE = 0x093C45C9U,
    S57_FACTORY_STATE = 0x0203F220U,
    S57_FACTORY_MENU_ACTIVE_OFFSET = 109U,
    S57_FACTORY_MENU_STAGE_OFFSET = 110U,
    S57_COLLECTION_FIELD_HOST = 0x09405B11U,
    S57_COLLECTION_TEST_INITIALIZE = 0x09405F15U,

    S57_QOL_ITEM_USE_CALLBACK = 0x03005EE8U,
    S57_QOL_SPECIAL_ITEM = 0x0203ACA8U,
    S57_QOL_PARTY_MENU = 0x0203B014U,
    S57_QOL_PARTY_MENU_SLOT = 9U,
    S57_QOL_START_MENU_CALLBACK = 0x02037024U,
    S57_QOL_START_MENU_INPUT = 0x0806EA75U,
    S57_QOL_START_MENU_CURSOR = 0x02037028U,
    S57_QOL_START_MENU_COUNT = 0x02037029U,
    S57_QOL_START_MENU_ORDER = 0x0203702AU,
    S57_QOL_ITEM_TABLE_CALLBACKS = 0x0904D120U,
    S57_QOL_ITEM_ROW_SIZE = 40U,
    S57_QOL_CANDY_TASK_MENU = 10U,
    S57_QOL_TEST_ITEM = 993U,

    S57_MAIN = 0x03003130U,
    S57_MAIN_NEW_KEYS_RAW_OFFSET = 0x2AU,
    S57_MAIN_NEW_KEYS_OFFSET = 0x2EU,

    S57_FLAG_BADGE_1 = 0x0820U,
    S57_FLAG_POKEMON_GET = 0x0828U,
    S57_FLAG_DH_CLEAR = 0x114BU,
    S57_ACQUISITION_MINING_HOST = 5U,
    S57_COLLECTION_HOST_COUNT = 14U,
    S57_TASK_COUNT = 16U,
    S57_MENU_TILE_BASE = 0x38U,
    S57_BACKGROUND_TOLERANCE = 1024U,
    S57_OPEN_VISIBLE_MINIMUM = 1000U,
    S57_KEY_PRESS_FRAMES = 8U,
};

#define S57_EXPECTED_ROM_SHA256 \
    "546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d"

enum S57OpenKind {
    S57_OPEN_WILD,
    S57_OPEN_MOVE,
    S57_OPEN_ACQUISITION,
    S57_OPEN_BP,
    S57_OPEN_QOL_SUPPLY,
    S57_OPEN_RESEARCH,
    S57_OPEN_REWARD,
    S57_OPEN_FACTORY,
};

struct S57MenuSpec {
    const char *name;
    enum S57OpenKind kind;
    uint32_t callsite;
    uint8_t width;
    uint8_t height;
};

struct S57MenuResult {
    const char *name;
    int host;
    uint32_t open_return;
    uint16_t task_mask_before;
    uint16_t task_mask_open;
    uint16_t task_mask_after;
    unsigned cursor_before;
    unsigned cursor_down;
    unsigned cursor_up;
    unsigned cursor_after_a;
    unsigned cursor_after_back;
    unsigned open_pixel_difference;
    unsigned restored_pixel_difference;
    unsigned warnings_delta;
    uint16_t b_new_keys_raw;
    uint16_t b_new_keys;
    uint16_t task_mask_before_b;
    unsigned menu_task;
    uint32_t menu_task_func;
    uint8_t menu_task_prev;
    uint8_t menu_task_next;
    uint8_t menu_task_priority;
    uint16_t owner_status_before_b;
    unsigned auxiliary_task;
    uint16_t task_mask_after_b;
    uint16_t packed_after_b;
    uint32_t menu_task_func_after_b;
    bool open;
    bool down;
    bool up;
    bool a_transition;
    bool b_back;
    bool b_cancel;
    bool cursor_255_forbidden;
    bool field_background_restored;
    bool pass;
};

struct S57StaticResult {
    bool menu_callsites;
    bool factory_adapter;
    bool bg0_charblock;
    unsigned bg0_charblock_index;
    uint16_t bg0_control;
};

static const struct S57MenuSpec S57_MENU_SPECS[] = {
    {"wild_overlay", S57_OPEN_WILD, 0x09220610U, 20U, 19U},
    {"move_memory", S57_OPEN_MOVE, 0x092D001EU, 17U, 10U},
    {"acquisition", S57_OPEN_ACQUISITION, 0x092D18BCU, 18U, 14U},
    {"bp_shop", S57_OPEN_BP, 0x092DC67AU, 21U, 16U},
    {"qol_supply", S57_OPEN_QOL_SUPPLY, 0x09378E8AU, 21U, 16U},
    {"qol_quantity", S57_OPEN_QOL_SUPPLY, 0x0937A0DAU, 11U, 10U},
    {"research_economy", S57_OPEN_RESEARCH, 0x093BF05AU, 21U, 16U},
    {"reward_encounters", S57_OPEN_REWARD, 0x093C2084U, 22U, 15U},
    {"factory_high_modes", S57_OPEN_FACTORY, 0x093C4CACU, 20U, 20U},
    {"collection_supply", S57_OPEN_QOL_SUPPLY, 0x09406DB4U, 22U, 14U},
};

static const struct S57MenuSpec S57_STANDARD_SPECS[] = {
    {"wild_overlay", S57_OPEN_WILD, 0x09220610U, 20U, 19U},
    {"move_memory", S57_OPEN_MOVE, 0x092D001EU, 17U, 10U},
    {"acquisition", S57_OPEN_ACQUISITION, 0x092D18BCU, 18U, 14U},
    {"bp_shop", S57_OPEN_BP, 0x092DC67AU, 21U, 16U},
    {"qol_supply", S57_OPEN_QOL_SUPPLY, 0x09378E8AU, 21U, 16U},
    {"research_economy", S57_OPEN_RESEARCH, 0x093BF05AU, 21U, 16U},
    {"reward_encounters", S57_OPEN_REWARD, 0x093C2084U, 22U, 15U},
    {"factory_high_modes", S57_OPEN_FACTORY, 0x093C4CACU, 20U, 20U},
};

static color_t s57_field_pixels[240U * 160U];
static color_t s57_transition_pixels[240U * 160U];
static color_t world_video[240U * 160U];

static void s57_die(const char *message);
static uint16_t s57_task_mask(struct mCore *core);

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

static void s57_probe_b_pulse(struct mCore *core,
                              struct S57MenuResult *result)
{
    bool captured = false;
    for (unsigned frame = 0U; frame < S57_KEY_PRESS_FRAMES; ++frame) {
        run_key_frames(core, WORLD_KEY_B, 1U);
        uint16_t raw = read16(
            core, S57_MAIN + S57_MAIN_NEW_KEYS_RAW_OFFSET);
        uint16_t keys = read16(
            core, S57_MAIN + S57_MAIN_NEW_KEYS_OFFSET);
        result->b_new_keys_raw |= raw;
        result->b_new_keys |= keys;
        if (!captured && ((raw | keys) & WORLD_KEY_B) != 0U) {
            result->task_mask_after_b = s57_task_mask(core);
            if (result->menu_task < S57_TASK_COUNT) {
                uint32_t address = S57_TASKS
                    + result->menu_task * S57_TASK_SIZE;
                result->menu_task_func_after_b = read32(core, address);
                result->packed_after_b = read16(
                    core, address + S57_TASK_DATA
                        + S57_QOL_CANDY_TASK_MENU * 2U);
            }
            captured = true;
        }
    }
    run_key_frames(core, 0U, 60U);
}

static void s57_traceable_pulse(struct mCore *core, uint16_t key,
                                unsigned pressed, unsigned released,
                                unsigned task, const char *label)
{
    bool trace = getenv("MGBA_STAGE57_MENU_TRACE") != NULL;
    unsigned total = pressed + released;
    for (unsigned frame = 0U; frame < total; ++frame) {
        core->setKeys(core, frame < pressed ? key : 0U);
        core->runFrame(core);
        if (trace) {
            uint32_t task_address = task < S57_TASK_COUNT
                ? S57_TASKS + task * S57_TASK_SIZE : 0U;
            fprintf(stderr,
                    "trace %s frame=%u keys=%u raw=%u new=%u mask=%u"
                    " task_active=%u func=%08" PRIx32
                    " cursor=%u supply_result=%u\n",
                    label, frame, frame < pressed ? key : 0U,
                    read16(core, S57_MAIN + S57_MAIN_NEW_KEYS_RAW_OFFSET),
                    read16(core, S57_MAIN + S57_MAIN_NEW_KEYS_OFFSET),
                    s57_task_mask(core),
                    task_address == 0U ? 0U
                        : read8(core, task_address + S57_TASK_ACTIVE),
                    task_address == 0U ? 0U : read32(core, task_address),
                    read8(core, 0x0203AD5EU),
                    read16(core, 0x0203EDA4U));
        }
    }
}

static void s57_generate_field_save(const char *rom_path,
                                    const char *save_path)
{
    bootstrap_phase = "stage57-menu-natural-new-game";
    bootstrap_write_blank_save(save_path);
    struct mCore *core = bootstrap_open_core(rom_path, save_path, NULL);
    run_trace_prefix(core);
    run_fixed_frames(core);
    uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U))
        s57_die("natural new game did not initialize SaveBlock1");

    bootstrap_phase = "stage57-menu-stock-warp-save";
    (void)call_preserving(core, BOOTSTRAP_KANTO_WARP,
                          1U, 36U, 6U, 4U);
    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
    save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
    if (save1 < 0x02000000U || save1 >= 0x02040000U || (save1 & 3U)
        || read8(core, save1 + 4U) != 1U
        || read8(core, save1 + 5U) != 36U
        || read16(core, save1) != 6U || read16(core, save1 + 2U) != 4U
        || !world_overworld(core))
        s57_die("stock warp did not reach the stable field fixture");

    for (unsigned byte = 0U;
         byte < BOOTSTRAP_TEAM_SIZE * BOOTSTRAP_MON_SIZE; ++byte)
        write8(core, BOOTSTRAP_PLAYER_PARTY + byte, 0U);
    for (unsigned slot = 0U; slot < BOOTSTRAP_TEAM_SIZE; ++slot)
        create_mon(core, BOOTSTRAP_PLAYER_PARTY
                         + slot * BOOTSTRAP_MON_SIZE,
                   bootstrap_species[slot], 50U);
    write8(core, BOOTSTRAP_PLAYER_COUNT, BOOTSTRAP_TEAM_SIZE);
    bootstrap_prepare_save_map_view(core);
    if (call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK
        || call_preserving(core, BOOTSTRAP_TRY_SAVE, 0U, 0U, 0U, 0U)
            != BOOTSTRAP_STATUS_OK)
        s57_die("two-generation fixture save failed");
    bootstrap_close_core(core);
}

static void s57_continue_to_field(struct mCore *core)
{
    bootstrap_phase = "stage57-menu-fresh-core-continue";
    run_key_frames(core, 0U, BOOTSTRAP_TITLE_FRAMES);
    for (unsigned pulse = 0U; pulse < BOOTSTRAP_CONTINUE_PULSES; ++pulse) {
        world_pulse(core, pulse == 0U ? 8U : WORLD_KEY_A,
                    2U, BOOTSTRAP_CONTINUE_WAIT_FRAMES);
        uint32_t save1 = read32(core, BOOTSTRAP_SAVE_BLOCK1_PTR);
        if (world_overworld(core)
            && save1 >= 0x02000000U && save1 < 0x02040000U
            && (save1 & 3U) == 0U
            && read8(core, save1 + 4U) == 1U
            && read8(core, save1 + 5U) == 36U) {
            run_key_frames(core, 0U, 300U);
            for (unsigned attempt = 0U; attempt < 8U; ++attempt) {
                if (read8(core, S57_QUEST_LOG_STATE) == 0U
                    && read8(core, S57_QUEST_LOG_PLAYBACK_STATE) == 0U) {
                    /* Continue can expose CB2_Overworld and zero recap flags
                     * before the final stock map/task rebuild.  The shared
                     * Stage44 bootstrap already defines the conservative
                     * authored-field settle used by production smoke tests;
                     * wait through that boundary so a late ResetTasks cannot
                     * orphan a newly opened overlay menu. */
                    run_key_frames(core, 0U, BOOTSTRAP_FIELD_FRAMES);
                    if (read8(core, S57_QUEST_LOG_STATE) == 0U
                        && read8(core, S57_QUEST_LOG_PLAYBACK_STATE) == 0U
                        && world_overworld(core)
                        && read8(core, S57_FIELD_LOCK) == 0U)
                        return;
                }
                world_pulse(core, WORLD_KEY_B, 2U, 180U);
            }
            s57_die("Continue recap did not release the stable field");
        }
    }
    s57_die("natural Continue did not reach the stable field fixture");
}

static uint8_t *s57_read_save_image(const char *save_path)
{
    uint8_t *image = malloc(BOOTSTRAP_SAVE_SIZE);
    FILE *stream = fopen(save_path, "rb");
    if (image == NULL || stream == NULL
        || fread(image, 1U, BOOTSTRAP_SAVE_SIZE, stream)
            != BOOTSTRAP_SAVE_SIZE
        || fgetc(stream) != EOF) {
        if (stream != NULL)
            (void)fclose(stream);
        free(image);
        s57_die("base save image read failed");
    }
    if (fclose(stream) != 0) {
        free(image);
        s57_die("base save image close failed");
    }
    return image;
}

static void s57_write_save_image(const char *save_path, const uint8_t *image)
{
    FILE *stream = fopen(save_path, "wb");
    if (stream == NULL
        || fwrite(image, 1U, BOOTSTRAP_SAVE_SIZE, stream)
            != BOOTSTRAP_SAVE_SIZE) {
        if (stream != NULL)
            (void)fclose(stream);
        s57_die("isolated save image write failed");
    }
    if (fclose(stream) != 0)
        s57_die("isolated save image close failed");
}

static struct mCore *s57_open_isolated_core(const char *rom_path,
                                            const char *save_path,
                                            const uint8_t *save_image,
                                            const char *phase)
{
    s57_write_save_image(save_path, save_image);
    bootstrap_phase = phase;
    struct mCore *core = bootstrap_open_core(rom_path, save_path, world_video);
    s57_continue_to_field(core);
    run_key_frames(core, 0U, 30U);
    if (!world_overworld(core) || read8(core, S57_FIELD_LOCK) != 0U)
        s57_die("isolated Continue field preparation failed");
    return core;
}

static void s57_die(const char *message)
{
    fprintf(stderr, "mgba-stage57-menu-smoke: %s\n", message);
    exit(1);
}

static const char *s57_bool(bool value)
{
    return value ? "true" : "false";
}

static uint16_t s57_task_mask(struct mCore *core)
{
    uint16_t mask = 0U;
    for (unsigned task = 0U; task < S57_TASK_COUNT; ++task) {
        if (read8(core, S57_TASKS + task * S57_TASK_SIZE
                        + S57_TASK_ACTIVE) != 0U)
            mask |= (uint16_t)(1U << task);
    }
    return mask;
}

static unsigned s57_first_task(uint16_t mask)
{
    for (unsigned task = 0U; task < S57_TASK_COUNT; ++task) {
        if ((mask & (uint16_t)(1U << task)) != 0U)
            return task;
    }
    return S57_TASK_COUNT;
}

static void s57_observe_menu_task(struct mCore *core,
                                  struct S57MenuResult *result,
                                  unsigned task)
{
    result->task_mask_before_b = s57_task_mask(core);
    result->menu_task = task;
    if (task >= S57_TASK_COUNT)
        return;
    uint32_t address = S57_TASKS + task * S57_TASK_SIZE;
    result->menu_task_func = read32(core, address);
    result->menu_task_prev = read8(core, address + 5U);
    result->menu_task_next = read8(core, address + 6U);
    result->menu_task_priority = read8(core, address + 7U);
}

static unsigned s57_frame_difference(const color_t *before)
{
    unsigned changed = 0U;
    for (unsigned pixel = 0U; pixel < 240U * 160U; ++pixel) {
        if (world_video[pixel] != before[pixel])
            ++changed;
    }
    return changed;
}

static unsigned s57_cursor(struct mCore *core)
{
    return read8(core, S57_MENU_CURSOR);
}

static bool s57_wait_field(struct mCore *core, uint16_t expected_tasks)
{
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 1200U; ++frame) {
        run_key_frames(core, 0U, 1U);
        if (s57_task_mask(core) == expected_tasks
            && read8(core, S57_FIELD_LOCK) == 0U
            && world_overworld(core)) {
            if (++stable >= 30U)
                return true;
        } else {
            stable = 0U;
        }
    }
    return false;
}

static bool s57_wait_any_field(struct mCore *core)
{
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 1800U; ++frame) {
        run_key_frames(core, 0U, 1U);
        if (read8(core, S57_FIELD_LOCK) == 0U && world_overworld(core)) {
            if (++stable >= 30U)
                return true;
        } else {
            stable = 0U;
        }
    }
    return false;
}

static bool s57_enter_party_menu(struct mCore *core)
{
    if (!world_overworld(core))
        return false;
    (void)call_preserving(core, S57_FLAG_SET, S57_FLAG_DH_CLEAR,
                          0U, 0U, 0U);
    (void)call_preserving(core, S57_FLAG_SET, S57_FLAG_POKEMON_GET,
                          0U, 0U, 0U);
    world_pulse(core, WORLD_KEY_START, 2U, 90U);
    if (read32(core, S57_QOL_START_MENU_CALLBACK)
            != S57_QOL_START_MENU_INPUT)
        return false;
    uint8_t count = read8(core, S57_QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, S57_QOL_START_MENU_CURSOR);
    uint8_t pokemon = 0xFFU;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, S57_QOL_START_MENU_ORDER + index) == 1U) {
            pokemon = index;
            break;
        }
    }
    if (pokemon == 0xFFU || count == 0U)
        return false;
    for (unsigned step = 0U; cursor != pokemon && step < count; ++step) {
        world_pulse(core, WORLD_KEY_DOWN, 2U, 4U);
        cursor = (uint8_t)((cursor + 1U) % count);
    }
    world_pulse(core, WORLD_KEY_A, 2U, 600U);
    return read8(core, S57_QOL_PARTY_MENU + S57_QOL_PARTY_MENU_SLOT) == 0U
        && !world_overworld(core);
}

static unsigned s57_list_cursor(struct mCore *core, unsigned task)
{
    uint32_t data = S57_TASKS + task * S57_TASK_SIZE + S57_TASK_DATA;
    return (unsigned)read16(core, data + 0x18U)
        + (unsigned)read16(core, data + 0x1AU);
}

static void s57_prepare_case(struct mCore *core, enum S57OpenKind kind)
{
    switch (kind) {
    case S57_OPEN_ACQUISITION:
        write16(core, S57_SPECIAL_VAR_8004, S57_ACQUISITION_MINING_HOST);
        break;
    case S57_OPEN_BP:
    case S57_OPEN_QOL_SUPPLY:
        (void)call_preserving(core, S57_FLAG_SET, S57_FLAG_BADGE_1,
                              0U, 0U, 0U);
        break;
    case S57_OPEN_RESEARCH:
        (void)call_preserving(core, S57_RESEARCH_TEST_INITIALIZE,
                              0U, 0U, 0U, 0U);
        (void)call_preserving(core, S57_RESEARCH_TEST_UNLOCK_ALL,
                              1U, 0U, 0U, 0U);
        break;
    case S57_OPEN_REWARD:
        (void)call_preserving(core, S57_REWARD_TEST_INITIALIZE,
                              0U, 0U, 0U, 0U);
        break;
    case S57_OPEN_FACTORY:
        (void)call_preserving(core, S57_FACTORY_TEST_INITIALIZE,
                              0U, 0U, 0U, 0U);
        break;
    case S57_OPEN_WILD:
    case S57_OPEN_MOVE:
        break;
    }
}

static uint32_t s57_open_case(struct mCore *core, enum S57OpenKind kind)
{
    uint32_t old_task;
    switch (kind) {
    case S57_OPEN_WILD:
        old_task = call_preserving(core, S57_CREATE_TASK,
                                   S57_TASK_DUMMY, 0x50U, 0U, 0U);
        if (old_task >= S57_TASK_COUNT)
            return UINT32_MAX;
        (void)call_preserving(core, S57_WILD_OPEN_TASK,
                              old_task, 0U, 0U, 0U);
        return old_task;
    case S57_OPEN_MOVE:
        return call_preserving(core, S57_MOVE_OPEN, 0U, 0U, 0U, 0U);
    case S57_OPEN_ACQUISITION:
        return call_preserving(core, S57_ACQUISITION_OPEN_HOST,
                               S57_ACQUISITION_MINING_HOST, 0U, 0U, 0U);
    case S57_OPEN_BP:
        return call_preserving(core, S57_BP_OPEN, 0U, 0U, 0U, 0U);
    case S57_OPEN_QOL_SUPPLY:
        return call_preserving(core, S57_QOL_SUPPLY_OPEN,
                               0U, 0U, 0U, 0U);
    case S57_OPEN_RESEARCH:
        return call_preserving(core, S57_RESEARCH_OPEN, 0U, 0U, 0U, 0U);
    case S57_OPEN_REWARD:
        return call_preserving(core, S57_REWARD_FIELD_SCIENTIST,
                               0U, 0U, 0U, 0U);
    case S57_OPEN_FACTORY:
        return call_preserving(core, S57_FACTORY_FIELD_RECEPTION,
                               0U, 0U, 0U, 0U);
    }
    return UINT32_MAX;
}

static struct S57MenuResult s57_run_standard(
    struct mCore *core, const struct Snapshot *field,
    const struct S57MenuSpec *spec)
{
    struct S57MenuResult result = {
        .name = spec->name,
        .host = -1,
        .cursor_before = 255U,
        .cursor_down = 255U,
        .cursor_up = 255U,
        .cursor_after_a = 255U,
        .cursor_after_back = 255U,
    };
    restore_snapshot(core, field);
    run_key_frames(core, 0U, 3U);
    s57_prepare_case(core, spec->kind);
    run_key_frames(core, 0U, 3U);
    result.task_mask_before = s57_task_mask(core);
    memcpy(s57_field_pixels, world_video, sizeof(s57_field_pixels));
    unsigned warnings_before = log_problem_count;
    result.open_return = s57_open_case(core, spec->kind);
    run_key_frames(core, 0U, 60U);
    result.task_mask_open = s57_task_mask(core);
    result.cursor_before = s57_cursor(core);
    result.open_pixel_difference = s57_frame_difference(s57_field_pixels);
    result.open = result.task_mask_open != result.task_mask_before
        && (result.task_mask_open & (uint16_t)~result.task_mask_before) != 0U
        && read8(core, S57_FIELD_LOCK) != 0U
        && world_overworld(core)
        && result.cursor_before != 255U
        && result.open_pixel_difference >= S57_OPEN_VISIBLE_MINIMUM;
    unsigned opened_task = s57_first_task(
        (uint16_t)(result.task_mask_open
                   & (uint16_t)~result.task_mask_before));

    s57_traceable_pulse(core, WORLD_KEY_DOWN, S57_KEY_PRESS_FRAMES, 60U,
                        opened_task, "down");
    result.cursor_down = s57_cursor(core);
    if (result.cursor_down == 255U
        || result.cursor_down == result.cursor_before) {
        s57_traceable_pulse(core, WORLD_KEY_DOWN, S57_KEY_PRESS_FRAMES, 60U,
                            opened_task, "down_retry");
        result.cursor_down = s57_cursor(core);
    }
    result.down = result.cursor_down != 255U
        && result.cursor_down != result.cursor_before;
    s57_traceable_pulse(core, WORLD_KEY_UP, S57_KEY_PRESS_FRAMES, 60U,
                        opened_task, "up");
    result.cursor_up = s57_cursor(core);
    if (result.cursor_up != result.cursor_before) {
        s57_traceable_pulse(core, WORLD_KEY_UP, S57_KEY_PRESS_FRAMES, 60U,
                            opened_task, "up_retry");
        result.cursor_up = s57_cursor(core);
    }
    result.up = result.cursor_up != 255U
        && result.cursor_up == result.cursor_before;
    s57_observe_menu_task(
        core, &result,
        opened_task);
    if (spec->kind == S57_OPEN_QOL_SUPPLY)
        result.owner_status_before_b = read16(core, 0x0203EDA4U);

    if (spec->kind == S57_OPEN_FACTORY) {
        memcpy(s57_transition_pixels, world_video,
               sizeof(s57_transition_pixels));
        world_pulse(core, WORLD_KEY_A, S57_KEY_PRESS_FRAMES, 60U);
        result.cursor_after_a = s57_cursor(core);
        result.a_transition = s57_task_mask(core) == result.task_mask_open
            && read8(core, S57_FIELD_LOCK) != 0U
            && read8(core, S57_FACTORY_STATE
                           + S57_FACTORY_MENU_STAGE_OFFSET) == 1U
            && result.cursor_after_a != 255U
            && s57_frame_difference(s57_transition_pixels) != 0U;
        s57_observe_menu_task(core, &result, result.menu_task);
        for (unsigned attempt = 0U; attempt < 3U; ++attempt) {
            if (attempt == 0U)
                s57_probe_b_pulse(core, &result);
            else
                world_pulse(core, WORLD_KEY_B, S57_KEY_PRESS_FRAMES, 60U);
            if (read8(core, S57_FACTORY_STATE
                            + S57_FACTORY_MENU_STAGE_OFFSET) == 0U)
                break;
        }
        result.cursor_after_back = s57_cursor(core);
        result.b_back = s57_task_mask(core) == result.task_mask_open
            && read8(core, S57_FIELD_LOCK) != 0U
            && read8(core, S57_FACTORY_STATE
                           + S57_FACTORY_MENU_STAGE_OFFSET) == 0U
            && result.cursor_after_back != 255U;
    } else {
        result.a_transition = true;
        result.b_back = true;
    }

    for (unsigned attempt = 0U; attempt < 3U; ++attempt) {
        if (attempt == 0U && result.b_new_keys_raw == 0U
            && result.b_new_keys == 0U)
            s57_probe_b_pulse(core, &result);
        else
            world_pulse(core, WORLD_KEY_B, S57_KEY_PRESS_FRAMES, 60U);
        if (s57_task_mask(core) == result.task_mask_before
            && read8(core, S57_FIELD_LOCK) == 0U)
            break;
        if (spec->kind == S57_OPEN_FACTORY
            && read8(core, S57_FACTORY_STATE
                           + S57_FACTORY_MENU_ACTIVE_OFFSET) == 0U)
            break;
    }
    result.b_cancel = s57_wait_field(core, result.task_mask_before);
    result.task_mask_after = s57_task_mask(core);
    result.restored_pixel_difference = s57_frame_difference(s57_field_pixels);
    result.field_background_restored = result.b_cancel
        && result.restored_pixel_difference <= S57_BACKGROUND_TOLERANCE;
    result.warnings_delta = log_problem_count - warnings_before;
    result.cursor_255_forbidden = result.cursor_before != 255U
        && result.cursor_down != 255U && result.cursor_up != 255U
        && (spec->kind != S57_OPEN_FACTORY
            || (result.cursor_after_a != 255U
                && result.cursor_after_back != 255U));
    result.pass = result.open && result.down && result.up
        && result.a_transition && result.b_back && result.b_cancel
        && result.cursor_255_forbidden && result.field_background_restored
        && result.warnings_delta == 0U;
    return result;
}

static struct S57MenuResult s57_run_quantity(
    struct mCore *core, const struct Snapshot *field)
{
    struct S57MenuResult result = {
        .name = "qol_quantity",
        .host = -1,
        .cursor_before = 255U,
        .cursor_down = 255U,
        .cursor_up = 255U,
        .cursor_after_a = 255U,
        .cursor_after_back = 255U,
        .a_transition = true,
        .b_back = true,
    };
    restore_snapshot(core, field);
    run_key_frames(core, 0U, 3U);
    unsigned warnings_before = log_problem_count;
    result.task_mask_before = s57_task_mask(core);
    memcpy(s57_field_pixels, world_video, sizeof(s57_field_pixels));
    if (!s57_enter_party_menu(core)) {
        result.warnings_delta = log_problem_count - warnings_before;
        return result;
    }
    if (call_preserving(core, S57_ADD_BAG_ITEM, S57_QOL_TEST_ITEM,
                        5U, 0U, 0U) == 0U) {
        result.warnings_delta = log_problem_count - warnings_before;
        return result;
    }
    write16(core, S57_QOL_SPECIAL_ITEM, S57_QOL_TEST_ITEM);
    write8(core, S57_QOL_PARTY_MENU + S57_QOL_PARTY_MENU_SLOT, 0U);
    uint32_t caller = call_preserving(core, S57_CREATE_TASK,
                                      S57_TASK_DUMMY, 0x50U, 0U, 0U);
    if (caller >= S57_TASK_COUNT) {
        result.warnings_delta = log_problem_count - warnings_before;
        return result;
    }
    uint32_t item_callback = read32(
        core, S57_QOL_ITEM_TABLE_CALLBACKS
            + S57_QOL_TEST_ITEM * S57_QOL_ITEM_ROW_SIZE);
    if (item_callback != S57_QOL_QUANTITY_ADAPTER) {
        (void)call_preserving(core, S57_DESTROY_TASK,
                              caller, 0U, 0U, 0U);
        result.warnings_delta = log_problem_count - warnings_before;
        return result;
    }
    (void)call_preserving(core, item_callback, caller, 0U, 0U, 0U);
    uint32_t callback = read32(core, S57_QOL_ITEM_USE_CALLBACK);
    if (callback < 0x08000001U || callback >= 0x0A000000U
        || (callback & 1U) == 0U) {
        (void)call_preserving(core, S57_DESTROY_TASK,
                              caller, 0U, 0U, 0U);
        result.warnings_delta = log_problem_count - warnings_before;
        return result;
    }
    (void)call_preserving(core, callback, caller, S57_TASK_DUMMY, 0U, 0U);
    run_key_frames(core, 0U, 60U);
    uint16_t packed = read16(core, S57_TASKS + caller * S57_TASK_SIZE
                                  + S57_TASK_DATA
                                  + S57_QOL_CANDY_TASK_MENU * 2U);
    unsigned list_task = packed >> 8U;
    result.auxiliary_task = list_task;
    result.task_mask_open = s57_task_mask(core);
    if (list_task < S57_TASK_COUNT) {
        result.cursor_before = s57_list_cursor(core, list_task);
        result.open_pixel_difference = s57_frame_difference(s57_field_pixels);
        result.open = list_task != caller
            && (result.task_mask_open & (uint16_t)(1U << list_task)) != 0U
            && !world_overworld(core)
            && result.cursor_before < 4U
            && result.open_pixel_difference >= S57_OPEN_VISIBLE_MINIMUM;
        world_pulse(core, WORLD_KEY_DOWN, S57_KEY_PRESS_FRAMES, 60U);
        result.cursor_down = s57_list_cursor(core, list_task);
        result.down = result.cursor_down != 255U
            && result.cursor_down != result.cursor_before;
        world_pulse(core, WORLD_KEY_UP, S57_KEY_PRESS_FRAMES, 60U);
        result.cursor_up = s57_list_cursor(core, list_task);
        result.up = result.cursor_up != 255U
            && result.cursor_up == result.cursor_before;
        s57_observe_menu_task(core, &result, caller);
        s57_probe_b_pulse(core, &result);
        result.b_cancel = (result.task_mask_after_b
                           & (uint16_t)(1U << list_task)) == 0U
            && (result.task_mask_after_b
                & (uint16_t)(1U << caller)) != 0U
            && result.packed_after_b == 0xFFFFU
            && result.menu_task_func_after_b == S57_TASK_DUMMY;
    }
    (void)call_preserving(core, S57_DESTROY_TASK, caller, 0U, 0U, 0U);
    bool field_ready = false;
    for (unsigned attempt = 0U; attempt < 8U; ++attempt) {
        world_pulse(core, WORLD_KEY_B, S57_KEY_PRESS_FRAMES, 240U);
        if (world_overworld(core)) {
            field_ready = s57_wait_any_field(core);
            break;
        }
    }
    result.task_mask_after = s57_task_mask(core);
    result.restored_pixel_difference = s57_frame_difference(s57_field_pixels);
    result.field_background_restored = field_ready
        && result.restored_pixel_difference <= S57_BACKGROUND_TOLERANCE;
    result.cursor_255_forbidden = result.cursor_before != 255U
        && result.cursor_down != 255U && result.cursor_up != 255U;
    result.warnings_delta = log_problem_count - warnings_before;
    result.pass = result.open && result.down && result.up && result.b_cancel
        && result.cursor_255_forbidden && result.field_background_restored
        && result.warnings_delta == 0U;
    return result;
}

static struct S57MenuResult s57_run_collection(
    struct mCore *core, const struct Snapshot *field, unsigned host)
{
    struct S57MenuResult result = {
        .name = "collection_supply",
        .host = (int)host,
        .cursor_before = 255U,
        .cursor_down = 255U,
        .cursor_up = 255U,
        .cursor_after_a = 255U,
        .cursor_after_back = 255U,
        .a_transition = true,
        .b_back = true,
    };
    restore_snapshot(core, field);
    run_key_frames(core, 0U, 3U);
    unsigned warnings_before = log_problem_count;
    (void)call_preserving(core, S57_COLLECTION_TEST_INITIALIZE,
                          0U, 0U, 0U, 0U);
    write16(core, S57_SPECIAL_VAR_8004, (uint16_t)host);
    result.task_mask_before = s57_task_mask(core);
    memcpy(s57_field_pixels, world_video, sizeof(s57_field_pixels));
    result.open_return = call_preserving(core, S57_COLLECTION_FIELD_HOST,
                                         0U, 0U, 0U, 0U);
    run_key_frames(core, 0U, 60U);
    result.task_mask_open = s57_task_mask(core);
    result.cursor_before = s57_cursor(core);
    result.open_pixel_difference = s57_frame_difference(s57_field_pixels);
    result.open = result.open_return == 9U
        && result.task_mask_open != result.task_mask_before
        && (result.task_mask_open & (uint16_t)~result.task_mask_before) != 0U
        && read8(core, S57_FIELD_LOCK) != 0U
        && world_overworld(core)
        && result.cursor_before != 255U
        && result.open_pixel_difference >= S57_OPEN_VISIBLE_MINIMUM;
    world_pulse(core, WORLD_KEY_DOWN, S57_KEY_PRESS_FRAMES, 60U);
    result.cursor_down = s57_cursor(core);
    result.down = result.cursor_down != 255U
        && result.cursor_down != result.cursor_before;
    world_pulse(core, WORLD_KEY_UP, S57_KEY_PRESS_FRAMES, 60U);
    result.cursor_up = s57_cursor(core);
    result.up = result.cursor_up != 255U
        && result.cursor_up == result.cursor_before;
    s57_observe_menu_task(
        core, &result,
        s57_first_task((uint16_t)(result.task_mask_open
                                  & (uint16_t)~result.task_mask_before)));
    s57_probe_b_pulse(core, &result);
    result.b_cancel = s57_wait_field(core, result.task_mask_before);
    result.task_mask_after = s57_task_mask(core);
    result.restored_pixel_difference = s57_frame_difference(s57_field_pixels);
    result.field_background_restored = result.b_cancel
        && result.restored_pixel_difference <= S57_BACKGROUND_TOLERANCE;
    result.cursor_255_forbidden = result.cursor_before != 255U
        && result.cursor_down != 255U && result.cursor_up != 255U;
    result.warnings_delta = log_problem_count - warnings_before;
    result.pass = result.open && result.down && result.up && result.b_cancel
        && result.cursor_255_forbidden && result.field_background_restored
        && result.warnings_delta == 0U;
    return result;
}

static struct S57StaticResult s57_static_contract(struct mCore *core)
{
    struct S57StaticResult result = {
        .menu_callsites = true,
        .factory_adapter = true,
    };
    for (unsigned index = 0U; index < ARRAY_LEN(S57_MENU_SPECS); ++index) {
        uint32_t site = S57_MENU_SPECS[index].callsite;
        if (read16(core, site) != 0x2038U
            || read16(core, site + 2U) != 0x46C0U)
            result.menu_callsites = false;
    }
    static const uint8_t adapter_call[] = {0x4FU, 0xF0U, 0x6FU, 0xFAU};
    for (unsigned byte = 0U; byte < ARRAY_LEN(adapter_call); ++byte) {
        if (read8(core, 0x093C4D02U + byte) != adapter_call[byte])
            result.factory_adapter = false;
    }
    result.bg0_control = read16(core, 0x04000008U);
    result.bg0_charblock_index = (result.bg0_control >> 2U) & 3U;
    result.bg0_charblock = result.bg0_charblock_index == 2U;
    return result;
}

static void s57_print_result(const struct S57MenuResult *result)
{
    printf("{\"name\":\"%s\"", result->name);
    if (result->host >= 0)
        printf(",\"host\":%d", result->host);
    printf(",\"status\":\"%s\",\"open_return\":%" PRIu32
           ",\"open\":%s,\"down\":%s,\"up\":%s"
           ",\"a_transition\":%s,\"b_back\":%s,\"b_cancel\":%s"
           ",\"cursor_255_forbidden\":%s"
           ",\"cursor\":{\"before\":%u,\"down\":%u,\"up\":%u"
           ",\"after_a\":%u,\"after_back\":%u}"
           ",\"task_mask\":{\"before\":%u,\"open\":%u,\"after\":%u}"
           ",\"pixels\":{\"open_difference\":%u"
           ",\"restored_difference\":%u,\"restore_tolerance\":%u}"
           ",\"b_input\":{\"new_keys_raw\":%u,\"new_keys\":%u}"
           ",\"menu_task\":{\"id\":%u,\"mask_before_b\":%u"
           ",\"func\":\"0x%08" PRIX32 "\",\"prev\":%u"
           ",\"next\":%u,\"priority\":%u}"
           ",\"owner_status_before_b\":%u"
           ",\"post_b\":{\"auxiliary_task\":%u,\"task_mask\":%u"
           ",\"packed\":%u,\"menu_func\":\"0x%08" PRIX32 "\"}"
           ",\"field_background_restored\":%s,\"warnings_delta\":%u}",
           result->pass ? "PASS" : "FAIL", result->open_return,
           s57_bool(result->open), s57_bool(result->down),
           s57_bool(result->up), s57_bool(result->a_transition),
           s57_bool(result->b_back), s57_bool(result->b_cancel),
           s57_bool(result->cursor_255_forbidden),
           result->cursor_before, result->cursor_down, result->cursor_up,
           result->cursor_after_a, result->cursor_after_back,
           result->task_mask_before, result->task_mask_open,
           result->task_mask_after, result->open_pixel_difference,
           result->restored_pixel_difference, S57_BACKGROUND_TOLERANCE,
           result->b_new_keys_raw, result->b_new_keys,
           result->menu_task, result->task_mask_before_b,
           result->menu_task_func, result->menu_task_prev,
           result->menu_task_next, result->menu_task_priority,
           result->owner_status_before_b,
           result->auxiliary_task, result->task_mask_after_b,
           result->packed_after_b, result->menu_task_func_after_b,
           s57_bool(result->field_background_restored),
           result->warnings_delta);
}

static void s57_print_window_contracts(void)
{
    printf("[ ");
    for (unsigned index = 0U; index < ARRAY_LEN(S57_MENU_SPECS); ++index) {
        const struct S57MenuSpec *spec = &S57_MENU_SPECS[index];
        unsigned tiles = (unsigned)spec->width * spec->height;
        if (index != 0U)
            putchar(',');
        printf("{\"name\":\"%s\",\"callsite\":\"0x%08" PRIX32
               "\",\"width\":%u,\"height\":%u,\"tiles\":%u"
               ",\"base_block\":%u,\"last_content_tile\":%u}",
               spec->name, spec->callsite, spec->width, spec->height,
               tiles, S57_MENU_TILE_BASE,
               S57_MENU_TILE_BASE + tiles - 1U);
    }
    putchar(']');
}

static bool s57_case_selected(const char *filter, const char *name, int host)
{
    if (filter == NULL || strcmp(filter, "all") == 0)
        return true;
    if (strcmp(filter, name) == 0)
        return true;
    if (host < 0 || strcmp(name, "collection_supply") != 0)
        return false;
    char selected[40];
    int length = snprintf(selected, sizeof(selected),
                          "collection_supply:%d", host);
    return length > 0 && (size_t)length < sizeof(selected)
        && strcmp(filter, selected) == 0;
}

int main(int argc, char **argv)
{
    if (argc < 2 || argc > 4) {
        fprintf(stderr, "usage: %s ROM [WORKDIR [CASE]]\n", argv[0]);
        return 2;
    }
    const char *filter = argc == 4 ? argv[3] : NULL;
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strcmp(rom_sha256, S57_EXPECTED_ROM_SHA256) != 0)
        s57_die("Stage57 exact candidate SHA-256 mismatch");

    char automatic_workdir[] = "/tmp/mgba-stage57-menu-smoke.XXXXXX";
    const char *workdir = argc == 3 ? argv[2] : mkdtemp(automatic_workdir);
    bool remove_workdir = argc == 2;
    if (workdir == NULL)
        s57_die("temporary work directory creation failed");
    if (argc == 3 && mkdir(workdir, 0700) != 0 && errno != EEXIST)
        s57_die("work directory creation failed");
    char save_path[4096];
    int length = snprintf(save_path, sizeof(save_path), "%s/stage57-menu.srm",
                          workdir);
    if (length <= 0 || (size_t)length >= sizeof(save_path))
        s57_die("save path is too long");
    (void)unlink(save_path);

    struct mLogger logger = {.log = bootstrap_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    s57_generate_field_save(argv[1], save_path);
    uint8_t *save_image = s57_read_save_image(save_path);
    if (log_problem_count != 0U)
        s57_die("mGBA warned/errored during natural field save generation");
    struct S57StaticResult static_result = {0};
    bool static_checked = false;

    struct S57MenuResult overlays[9];
    unsigned overlay_count = 0U;
    for (unsigned index = 0U; index < ARRAY_LEN(S57_STANDARD_SPECS); ++index) {
        if (!s57_case_selected(filter, S57_STANDARD_SPECS[index].name, -1))
            continue;
        struct mCore *core = s57_open_isolated_core(
            argv[1], save_path, save_image, S57_STANDARD_SPECS[index].name);
        struct Snapshot field = take_snapshot(core);
        if (!static_checked) {
            static_result = s57_static_contract(core);
            static_checked = true;
        }
        overlays[overlay_count++] = s57_run_standard(
            core, &field, &S57_STANDARD_SPECS[index]);
        free(field.bytes);
        bootstrap_close_core(core);
    }
    if (s57_case_selected(filter, "qol_quantity", -1)) {
        struct mCore *core = s57_open_isolated_core(
            argv[1], save_path, save_image, "qol_quantity");
        struct Snapshot field = take_snapshot(core);
        if (!static_checked) {
            static_result = s57_static_contract(core);
            static_checked = true;
        }
        overlays[overlay_count++] = s57_run_quantity(core, &field);
        free(field.bytes);
        bootstrap_close_core(core);
    }
    if (filter == NULL && overlay_count != ARRAY_LEN(overlays))
        s57_die("non-Collection overlay inventory differs");

    struct S57MenuResult collection[S57_COLLECTION_HOST_COUNT];
    unsigned collection_count = 0U;
    for (unsigned host = 0U; host < S57_COLLECTION_HOST_COUNT; ++host) {
        if (!s57_case_selected(filter, "collection_supply", (int)host))
            continue;
        struct mCore *core = s57_open_isolated_core(
            argv[1], save_path, save_image, "collection_supply");
        struct Snapshot field = take_snapshot(core);
        if (!static_checked) {
            static_result = s57_static_contract(core);
            static_checked = true;
        }
        collection[collection_count++] = s57_run_collection(
            core, &field, host);
        free(field.bytes);
        bootstrap_close_core(core);
    }
    if (!static_checked || overlay_count + collection_count == 0U)
        s57_die("CASE did not select a Stage57 menu smoke");

    bool pass = static_result.menu_callsites && static_result.factory_adapter
        && static_result.bg0_charblock && log_problem_count == 0U;
    for (unsigned index = 0U; index < overlay_count; ++index)
        pass = pass && overlays[index].pass;
    for (unsigned index = 0U; index < collection_count; ++index)
        pass = pass && collection[index].pass;

    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260827-STAGE57-MENU-SMOKE\",\"stage\":57"
           ",\"status\":\"%s\",\"rom_sha256\":\"%s\""
           ",\"expected_rom_sha256\":\"%s\",\"menu_tile_base\":%u"
           ",\"static_contract\":{\"menu_callsites\":%s"
           ",\"factory_cursor_adapter\":%s,\"bg0_control\":%u"
           ",\"bg0_charblock_index\":%u,\"bg0_charblock_2\":%s"
           ",\"window_templates\":",
           pass ? "PASS" : "FAIL", rom_sha256, S57_EXPECTED_ROM_SHA256,
           S57_MENU_TILE_BASE, s57_bool(static_result.menu_callsites),
           s57_bool(static_result.factory_adapter), static_result.bg0_control,
           static_result.bg0_charblock_index,
           s57_bool(static_result.bg0_charblock));
    s57_print_window_contracts();
    printf("},\"overlays\":[");
    for (unsigned index = 0U; index < overlay_count; ++index) {
        if (index != 0U)
            putchar(',');
        s57_print_result(&overlays[index]);
    }
    printf("],\"collection_hosts\":[");
    for (unsigned index = 0U; index < collection_count; ++index) {
        if (index != 0U)
            putchar(',');
        s57_print_result(&collection[index]);
    }
    printf("],\"coverage\":{\"menu_callsites\":10"
           ",\"non_collection_overlays\":%u,\"collection_hosts\":%u"
           ",\"full_inventory\":%s}"
           ",\"checks\":{\"open\":true,\"down_up\":true"
           ",\"b_cancel\":true,\"field_background_restore\":true"
           ",\"cursor_255_forbidden\":true}"
           ",\"warnings_errors\":%u}\n", overlay_count, collection_count,
           s57_bool(overlay_count == ARRAY_LEN(overlays)
                    && collection_count == S57_COLLECTION_HOST_COUNT),
           log_problem_count);

    free(save_image);
    if (unlink(save_path) != 0 && errno != ENOENT)
        fprintf(stderr, "mgba-stage57-menu-smoke: save cleanup warning\n");
    if (remove_workdir && rmdir(workdir) != 0)
        fprintf(stderr, "mgba-stage57-menu-smoke: workdir cleanup warning\n");
    return pass ? 0 : 1;
}
