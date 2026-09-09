/*
 * P02 Stage71 exact-ROM acceptance runner.
 *
 * Fixture construction is host-driven, but the observed evolution, item
 * consumption, scene cancellation, save and load transitions are performed
 * by the ROM's production callbacks and ordinary GBA input scheduler.
 */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

enum {
    P02S_GET_EVOLUTION_TARGET = 0x090FB775U,
    P02S_ITEM_EVOLUTION_REMOVAL = 0x090FB631U,
    P02S_GET_MON_ABILITY = 0x090DA23DU,
    P02S_GET_ABILITY1 = 0x0913135DU,
    P02S_GET_ABILITY2 = 0x0913136DU,
    P02S_GET_HIDDEN_ABILITY = 0x0913137DU,
    P02S_VAR_SET = 0x0806DD79U,

    P02S_CB2_FIELD = 0x08055E75U,
    P02S_CB2_EVOLUTION_BEGIN = 0x080CEE71U,
    P02S_CB2_EVOLUTION_UPDATE = 0x080CF869U,
    P02S_CB2_BAG = 0x081089E5U,
    P02S_CB2_PARTY = 0x0811F3A9U,

    P02S_REMOVE_BAG_ITEM = 0x08099BE1U,
    P02S_SAVE_ITEMS_OFFSET = 0x0310U,
    P02S_SAVE_ITEMS_SLOTS = 42U,
    P02S_SAVE_ENCRYPTION_KEY_OFFSET = 0x0F20U,
    P02S_BAG_MENU_DISPLAY = 0x0203AC88U,
    P02S_FIELD_LOCK = 0x03000F9CU,
    P02S_QUEST_LOG_STATE = 0x0203AD72U,
    P02S_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    P02S_PLAYER_AVATAR = 0x02036FACU,
    P02S_OBJECT_EVENTS = 0x02036D6CU,
    P02S_PLAYER_RUNNING_STATE_OFFSET = 2U,
    P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET = 3U,
    P02S_MENU_WAIT_FRAMES = 1800U,
    P02S_TITLE_FRAMES = 1200U,
    P02S_CONTINUE_WAIT_FRAMES = 180U,
    P02S_CONTINUE_PULSES = 24U,
    P02S_FIELD_SETTLE_FRAMES = 1800U,
    P02S_INPUT_READY_FRAMES = 120U,
    P02S_CONTINUE_MAP_GROUP = 96U,
    P02S_CONTINUE_MAP_NUM = 5U,
    P02S_CONTINUE_X = 20U,
    P02S_CONTINUE_Y = 20U,

    P02S_MODE_NORMAL = 0U,
    P02S_MODE_TRADE = 1U,
    P02S_MODE_ITEM_USE = 2U,
    P02S_MON_DATA_FRIENDSHIP = 32U,
    P02S_MON_DATA_ALT_ABILITY = 46U,
    P02S_MON_DATA_SPECIES2 = 65U,
    P02S_HIDDEN_ABILITY_BYTE = 71U,
    P02S_HIDDEN_ABILITY_MASK = 0x10U,

    P02S_FLAG_NATIONAL_DEX = 0x0840U,
    P02S_VAR_NATIONAL_DEX = 0x404EU,
    P02S_NATIONAL_MAGIC_OFFSET = 0x001BU,
    P02S_ITEM_RARE_CANDY = 68U,
    P02S_ITEM_SUN_STONE = 93U,
    P02S_SPECIES_VEGA_001_LEEPUN = 1U,
    P02S_SPECIES_VEGA_002_LEETIN = 2U,
    P02S_SPECIES_TOGETIC = 19U,
    P02S_SPECIES_TOGEKISS = 20U,
    P02S_SPECIES_QUILAVA = 499U,
    P02S_SPECIES_TYPHLOSION_H = 1419U,
    P02S_ITEM_SPOOKY_PLATE = 710U,
    P02S_MAX_SCENE_FRAMES = 24000U,
};

static const uint16_t p02s_retained_moves[BATTLE_CORE_MOVE_SLOTS] = {
    246U, 33U, 45U, 52U,
};

struct P02SScene {
    bool normal_input;
    bool begin_seen;
    bool update_seen;
    bool physical_b;
    uint32_t frames;
};

_Noreturn static void p02s_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p02-stage71: %s\n", message);
    exit(1);
}

static bool p02s_ewram_pointer(uint32_t value)
{
    return value >= 0x02000000U && value < 0x02040000U
        && (value & 3U) == 0U;
}

static void p02s_diagnostic(struct mCore *core, const char *stage,
                            const char *reason, uint32_t frame,
                            uint16_t expected_item)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint8_t object_id = read8(core, P02S_PLAYER_AVATAR + 5U);
    uint32_t object = object_id < 16U
        ? P02S_OBJECT_EVENTS + (uint32_t)object_id * 0x24U : 0U;
    uint16_t x = p02s_ewram_pointer(save1) ? read16(core, save1) : 0U;
    uint16_t y = p02s_ewram_pointer(save1) ? read16(core, save1 + 2U) : 0U;
    uint8_t group = p02s_ewram_pointer(save1)
        ? read8(core, save1 + QOL_SAVE_LOCATION_OFFSET) : 0U;
    uint8_t map = p02s_ewram_pointer(save1)
        ? read8(core, save1 + QOL_SAVE_LOCATION_OFFSET + 1U) : 0U;
    fprintf(stderr,
            "p02-stage-diagnostic stage=%s reason=%s frame=%u"
            " pc=%08x cb1=%08x cb2=%08x save1=%08x save2=%08x"
            " map=%u/%u pos=%u,%u lock=%u quest=%u/%u"
            " avatar=%u object_flags=%02x/%02x move=%u/%u"
            " party_count=%u startcb=%08x cursor=%u count=%u"
            " order=%u,%u,%u,%u,%u,%u,%u,%u"
            " bagdisplay=%08x special_item=%u expected_item=%u"
            " party_slot=%u log_problems=%u\n",
            stage, reason, (unsigned)frame,
            (unsigned)read_register(core, "pc"),
            (unsigned)read32(core, BATTLE_CORE_MAIN_CALLBACK2 - 4U),
            (unsigned)read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            (unsigned)save1, (unsigned)save2,
            (unsigned)group, (unsigned)map, (unsigned)x, (unsigned)y,
            (unsigned)read8(core, P02S_FIELD_LOCK),
            (unsigned)read8(core, P02S_QUEST_LOG_STATE),
            (unsigned)read8(core, P02S_QUEST_LOG_PLAYBACK_STATE),
            (unsigned)object_id,
            object == 0U ? 0U : (unsigned)read8(core, object),
            object == 0U ? 0U : (unsigned)read8(core, object + 2U),
            (unsigned)read8(
                core, P02S_PLAYER_AVATAR + P02S_PLAYER_RUNNING_STATE_OFFSET),
            (unsigned)read8(
                core, P02S_PLAYER_AVATAR
                    + P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET),
            (unsigned)read8(core, QOL_PLAYER_PARTY_COUNT),
            (unsigned)read32(core, QOL_START_MENU_CALLBACK),
            (unsigned)read8(core, QOL_START_MENU_CURSOR),
            (unsigned)read8(core, QOL_START_MENU_COUNT),
            (unsigned)read8(core, QOL_START_MENU_ORDER),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 1U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 2U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 3U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 4U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 5U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 6U),
            (unsigned)read8(core, QOL_START_MENU_ORDER + 7U),
            (unsigned)read32(core, P02S_BAG_MENU_DISPLAY),
            (unsigned)read16(core, QOL_SPECIAL_VAR_ITEM),
            (unsigned)expected_item,
            (unsigned)read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT),
            log_problem_count);
}

static bool p02s_bag_exact(struct mCore *core, uint16_t item,
                           uint16_t quantity)
{
    return (quantity == 0U || call_preserving(
                core, QOL_CHECK_BAG_ITEM, item, quantity, 0U, 0U) == 1U)
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           item, (uint32_t)quantity + 1U, 0U, 0U) == 0U;
}

static bool p02s_keep_only_bag_item(struct mCore *core, uint16_t keep)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return false;
    uint16_t key = read16(core, save2 + P02S_SAVE_ENCRYPTION_KEY_OFFSET);
    for (unsigned slot = 0U; slot < P02S_SAVE_ITEMS_SLOTS; ++slot) {
        uint32_t entry = save1 + P02S_SAVE_ITEMS_OFFSET + slot * 4U;
        uint16_t item = read16(core, entry);
        uint16_t quantity = read16(core, entry + 2U) ^ key;
        if (item != 0U && item != keep && quantity != 0U
            && call_preserving(core, P02S_REMOVE_BAG_ITEM,
                               item, quantity, 0U, 0U) != 1U)
            return false;
    }
    return true;
}

static bool p02s_enter_bag_physical(struct mCore *core, const char *stage,
                                    uint16_t expected_item)
{
    run_key_frames(core, 0U, 2U);
    qol_press(core, QOL_KEY_START, 90U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT) {
        p02s_diagnostic(
            core, stage, "start_menu_callback_not_input", 0U, expected_item);
        return false;
    }
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    uint8_t bag = 0xFFU;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == 2U) {
            bag = index;
            break;
        }
    }
    if (bag == 0xFFU || count == 0U) {
        p02s_diagnostic(
            core, stage, "bag_missing_from_start_order", 0U, expected_item);
        return false;
    }
    while (cursor != bag) {
        qol_press(core, QOL_KEY_DOWN, 4U);
        uint8_t next = read8(core, QOL_START_MENU_CURSOR);
        if (next == cursor) {
            p02s_diagnostic(
                core, stage, "start_cursor_did_not_advance", 0U,
                expected_item);
            return false;
        }
        cursor = next;
    }
    run_key_frames(core, QOL_KEY_A, 2U);
    for (unsigned frame = 0U; frame < P02S_MENU_WAIT_FRAMES; ++frame) {
        run_key_frames(core, 0U, 1U);
        uint32_t display = read32(core, P02S_BAG_MENU_DISPLAY);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_BAG
            && display >= 0x02000000U && display < 0x02040000U)
            return true;
    }
    p02s_diagnostic(
        core, stage, "bag_callback_timeout", P02S_MENU_WAIT_FRAMES,
        expected_item);
    return false;
}

static bool p02s_enter_item_party(struct mCore *core, uint16_t item,
                                  const char *stage)
{
    if (!p02s_enter_bag_physical(core, stage, item))
        return false;
    qol_press(core, QOL_KEY_A, 120U);
    for (unsigned move = 0U; move < 8U; ++move)
        qol_press(core, QOL_KEY_UP, 20U);
    for (unsigned attempt = 0U; attempt < 10U; ++attempt) {
        qol_press(core, QOL_KEY_A, 120U);
        if (read16(core, QOL_SPECIAL_VAR_ITEM) == item
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY
            && read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT) == 0U)
            return true;
    }
    p02s_diagnostic(
        core, stage, "bag_use_did_not_reach_party", 10U, item);
    return false;
}

static uint32_t p02s_data(struct mCore *core, uint32_t field)
{
    return qol_get_party_data(core, QOL_PLAYER_PARTY, field);
}

static void p02s_set_data(struct mCore *core, uint32_t field, uint32_t value)
{
    set_mon_data_u32(core, QOL_PLAYER_PARTY, field, value);
}

static bool p02s_hidden(struct mCore *core)
{
    return (read8(core, QOL_PLAYER_PARTY + P02S_HIDDEN_ABILITY_BYTE)
            & P02S_HIDDEN_ABILITY_MASK) != 0U;
}

static void p02s_set_hidden(struct mCore *core, bool enabled)
{
    uint8_t value = read8(
        core, QOL_PLAYER_PARTY + P02S_HIDDEN_ABILITY_BYTE);
    value = enabled
        ? (uint8_t)(value | P02S_HIDDEN_ABILITY_MASK)
        : (uint8_t)(value & (uint8_t)~P02S_HIDDEN_ABILITY_MASK);
    write8(core, QOL_PLAYER_PARTY + P02S_HIDDEN_ABILITY_BYTE, value);
}

static bool p02s_moves_equal(struct mCore *core)
{
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        if (p02s_data(core, QOL_MON_DATA_MOVE1 + slot)
                != p02s_retained_moves[slot])
            return false;
    }
    return true;
}

static void p02s_enable_national_dex(struct mCore *core)
{
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (save2 < 0x02000000U || save2 >= 0x02040000U)
        p02s_die("SaveBlock2 is unavailable");
    write8(core, save2 + P02S_NATIONAL_MAGIC_OFFSET, 0xB9U);
    (void)call_preserving(
        core, P02S_VAR_SET, P02S_VAR_NATIONAL_DEX, 0x6258U, 0U, 0U);
    (void)call_preserving(
        core, QOL_FLAG_SET, P02S_FLAG_NATIONAL_DEX, 0U, 0U, 0U);
}

static bool p02s_continue_position(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    return p02s_ewram_pointer(save1)
        && read8(core, save1 + QOL_SAVE_LOCATION_OFFSET)
            == P02S_CONTINUE_MAP_GROUP
        && read8(core, save1 + QOL_SAVE_LOCATION_OFFSET + 1U)
            == P02S_CONTINUE_MAP_NUM
        && read16(core, save1) == P02S_CONTINUE_X
        && read16(core, save1 + 2U) == P02S_CONTINUE_Y;
}

static bool p02s_input_ready_field(struct mCore *core)
{
    uint8_t object_id = read8(core, P02S_PLAYER_AVATAR + 5U);
    uint32_t object = object_id < 16U
        ? P02S_OBJECT_EVENTS + (uint32_t)object_id * 0x24U : 0U;
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_FIELD
        && p02s_continue_position(core)
        && read8(core, P02S_FIELD_LOCK) == 0U
        && read8(core, P02S_QUEST_LOG_STATE) == 0U
        && read8(core, P02S_QUEST_LOG_PLAYBACK_STATE) == 0U
        && object != 0U && (read8(core, object) & 1U) != 0U
        && read8(core, P02S_PLAYER_AVATAR
                       + P02S_PLAYER_RUNNING_STATE_OFFSET) == 0U
        && read8(core, P02S_PLAYER_AVATAR
                       + P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET) == 0U
        && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                           0U, 0U, 0U, 0U) == 0U;
}

static bool p02s_wait_input_ready_field(struct mCore *core)
{
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 3600U; frame += 15U) {
        if (p02s_input_ready_field(core)) {
            stable += 15U;
            if (stable >= P02S_INPUT_READY_FRAMES)
                return true;
        } else {
            stable = 0U;
        }
        run_key_frames(core, 0U, 15U);
    }
    return false;
}

static bool p02s_continue_to_field(struct mCore *core, const char *stage)
{
    /* The caller attaches a private byte-for-byte copy of the pinned Stage60
     * QA save.  Only ordinary title/Continue/recap input may load it. */
    run_key_frames(core, 0U, P02S_TITLE_FRAMES);
    for (unsigned pulse = 0U; pulse < P02S_CONTINUE_PULSES; ++pulse) {
        qol_press(
            core, pulse == 0U ? QOL_KEY_START : QOL_KEY_A,
            P02S_CONTINUE_WAIT_FRAMES);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != P02S_CB2_FIELD
            || !p02s_continue_position(core))
            continue;
        run_key_frames(core, 0U, 300U);
        for (unsigned recap = 0U; recap < 8U; ++recap) {
            if (read8(core, P02S_QUEST_LOG_STATE) == 0U
                && read8(core, P02S_QUEST_LOG_PLAYBACK_STATE) == 0U) {
                run_key_frames(core, 0U, P02S_FIELD_SETTLE_FRAMES);
                if (p02s_wait_input_ready_field(core))
                    return true;
                p02s_diagnostic(
                    core, stage, "field_seen_but_not_input_ready", recap, 0U);
            }
            qol_press(core, QOL_KEY_B, P02S_CONTINUE_WAIT_FRAMES);
        }
        p02s_diagnostic(
            core, stage, "continue_recap_not_released", pulse, 0U);
        return false;
    }
    p02s_diagnostic(
        core, stage, "normal_continue_never_reached_pinned_field",
        P02S_CONTINUE_PULSES, 0U);
    return false;
}

static bool p02s_install_field_fixture(struct mCore *core)
{
    /* Runtime state before this boundary comes only from normal Continue.
     * From here on direct writes are limited to deterministic test fixtures. */
    clear_parties(core);
    create_mon(core, QOL_PLAYER_PARTY, P02S_SPECIES_VEGA_001_LEEPUN, 5U);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    (void)call_preserving(
        core, QOL_FLAG_SET, QOL_FLAG_POKEMON_GET, 0U, 0U, 0U);
    (void)call_preserving(
        core, QOL_FLAG_SET, QOL_FLAG_POKEDEX_GET, 0U, 0U, 0U);
    return qol_get_party_data(
               core, QOL_PLAYER_PARTY, P02S_MON_DATA_SPECIES2)
            == P02S_SPECIES_VEGA_001_LEEPUN
        && read8(core, QOL_PLAYER_PARTY_COUNT) == 1U
        && p02s_input_ready_field(core);
}

static void p02s_prepare_mon(struct mCore *core, uint16_t species,
                             uint8_t level, uint16_t held_item,
                             bool hidden, uint8_t ability_slot)
{
    clear_parties(core);
    create_mon(core, QOL_PLAYER_PARTY, species, level);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    p02s_set_data(core, QOL_MON_DATA_HELD_ITEM, held_item);
    p02s_set_data(core, P02S_MON_DATA_ALT_ABILITY, ability_slot);
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot)
        p02s_set_data(
            core, QOL_MON_DATA_MOVE1 + slot, p02s_retained_moves[slot]);
    p02s_set_hidden(core, hidden);
    (void)call_preserving(
        core, QOL_CALCULATE_MON_STATS, QOL_PLAYER_PARTY, 0U, 0U, 0U);
}

static void p02s_prepare_item(struct mCore *core, uint16_t item)
{
    uint32_t present = call_preserving(
        core, QOL_CHECK_BAG_ITEM, item, 1U, 0U, 0U);
    if (present == 0U
        && call_preserving(
               core, QOL_ADD_BAG_ITEM, item, 1U, 0U, 0U) != 1U)
        p02s_die("could not add fixture Bag item");
    if (!p02s_keep_only_bag_item(core, item)
        || !p02s_bag_exact(core, item, 1U))
        p02s_die("fixture Bag item is not exact");
}

static uint16_t p02s_scene_key(uint32_t callback, uint32_t species,
                               bool cancel, bool scene_started,
                               uint16_t source, uint16_t target, uint32_t frame,
                               struct P02SScene *trace)
{
    if (callback == P02S_CB2_EVOLUTION_BEGIN)
        trace->begin_seen = true;
    if (callback == P02S_CB2_EVOLUTION_UPDATE)
        trace->update_seen = true;

    if (cancel && callback == P02S_CB2_EVOLUTION_UPDATE
        && species == source) {
        /* Cancellation is edge-triggered after the animation's input gate.
         * Release between presses, so an early B does not consume the edge. */
        if (frame % 120U < 2U) {
            trace->physical_b = true;
            return QOL_KEY_B;
        }
        return 0U;
    }
    if (!scene_started)
        return frame % 120U < 2U ? QOL_KEY_A : 0U;
    /* Returning from Bag leaves the Start menu open on the field callback.
     * Close all three menus before optional-move dialog input can reopen Bag. */
    if (callback == P02S_CB2_PARTY || callback == P02S_CB2_BAG
        || callback == P02S_CB2_FIELD)
        return frame % 120U < 2U ? QOL_KEY_B : 0U;
    if (!cancel && species == target) {
        /* Reject optional evolution moves without changing the four slots. */
        uint32_t phase = frame % 240U;
        if (phase < 2U)
            return QOL_KEY_B;
        if (phase >= 120U && phase < 122U)
            return QOL_KEY_A;
    }
    return frame % 180U < 2U ? QOL_KEY_A : 0U;
}

static struct P02SScene p02s_run_item_scene(
    struct mCore *core, uint16_t item, uint16_t source, uint16_t target,
    bool cancel, const char *stage)
{
    struct P02SScene trace = {0};
    if (!p02s_enter_item_party(core, item, stage))
        p02s_die("normal Start/Bag/party input did not reach party menu");
    trace.normal_input = true;

    bool scene_started = false;
    uint32_t species = source;
    for (uint32_t frame = 0U; frame < P02S_MAX_SCENE_FRAMES; ++frame) {
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (callback == P02S_CB2_EVOLUTION_BEGIN) {
            trace.begin_seen = true;
            scene_started = true;
        }
        if (callback == P02S_CB2_EVOLUTION_UPDATE) {
            trace.update_seen = true;
            scene_started = true;
        }
        if (frame % 30U == 0U)
            species = p02s_data(core, P02S_MON_DATA_SPECIES2);
        uint16_t key = p02s_scene_key(
            callback, species, cancel, scene_started,
            source, target, frame, &trace);
        core->setKeys(core, key);
        core->runFrame(core);
        trace.frames = frame + 1U;
        if (scene_started && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == P02S_CB2_FIELD
            && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                               0U, 0U, 0U, 0U) == 0U) {
            core->setKeys(core, 0U);
            return trace;
        }
    }
    core->setKeys(core, 0U);
    p02s_diagnostic(
        core, stage, "evolution_scene_field_return_timeout",
        P02S_MAX_SCENE_FRAMES, item);
    p02s_die("evolution scene did not return to field");
}

static bool p02s_scene_seen(const struct P02SScene *trace)
{
    return trace->begin_seen && trace->update_seen;
}

struct P02SRepair {
    uint16_t source;
    uint8_t level;
    uint16_t target;
    uint16_t item;
    uint16_t regular;
};

static const struct P02SRepair p02s_repairs[] = {
    {499U, 36U, 1419U, 710U, 500U},
    {759U, 36U, 1422U, 719U, 760U},
    {861U, 54U, 1427U, 716U, 862U},
    {993U, 40U, 1428U, 711U, 994U},
    {1001U, 37U, 1430U, 708U, 1002U},
    {1121U, 34U, 1431U, 704U, 1122U},
};

struct P02SMatrix {
    unsigned conditional_selected;
    unsigned conditional_consumed;
    unsigned below_rejected;
    unsigned regular_selected;
    unsigned hidden_preserved;
    bool payload_seen;
};

static struct CallObservation p02s_target(struct mCore *core,
                                          uint32_t mode, uint32_t argument)
{
    struct CallObservation call = call_bounded(
        core, P02S_GET_EVOLUTION_TARGET, QOL_PLAYER_PARTY,
        mode, argument, 0U);
    if (call.instructions == 0U || !call.payload_pc_seen)
        p02s_die("GetEvolutionTargetSpecies missed production payload");
    return call;
}

static void p02s_expect_target(struct mCore *core,
                               uint32_t mode, uint32_t argument,
                               uint16_t expected, const char *label)
{
    struct CallObservation call = p02s_target(core, mode, argument);
    if (call.result != expected)
        p02s_die(label);
}

static struct P02SMatrix p02s_direct_matrix(
    struct mCore *core, const struct Snapshot *field)
{
    restore_snapshot(core, field);
    p02s_prepare_mon(
        core, P02S_SPECIES_VEGA_001_LEEPUN, 16U, 0U, false, 0U);
    p02s_expect_target(
        core, P02S_MODE_NORMAL, 0U, P02S_SPECIES_VEGA_002_LEETIN,
                       "level evolution representative failed");

    restore_snapshot(core, field);
    p02s_prepare_mon(core, 12U, 10U, 0U, false, 0U);
    p02s_set_data(core, P02S_MON_DATA_FRIENDSHIP, 220U);
    p02s_expect_target(core, P02S_MODE_NORMAL, 0U, 13U,
                       "friendship evolution representative failed");

    restore_snapshot(core, field);
    p02s_prepare_mon(core, 475U, 20U, 0U, false, 0U);
    p02s_set_data(core, QOL_MON_DATA_MOVE1, 246U);
    p02s_expect_target(core, P02S_MODE_NORMAL, 0U, 735U,
                       "known-move evolution representative failed");

    restore_snapshot(core, field);
    p02s_prepare_mon(core, 452U, 20U, 0U, false, 0U);
    p02s_expect_target(core, P02S_MODE_TRADE, 0U, 453U,
                       "trade evolution representative failed");

    restore_snapshot(core, field);
    p02s_prepare_mon(core, 473U, 28U, 0U, false, 0U);
    p02s_expect_target(core, P02S_MODE_NORMAL, 0U, 1220U,
                       "night-form evolution representative failed");

    struct P02SMatrix matrix = {0};
    matrix.payload_seen = true;
    for (unsigned index = 0U; index < ARRAY_LEN(p02s_repairs); ++index) {
        const struct P02SRepair *row = &p02s_repairs[index];

        restore_snapshot(core, field);
        p02s_prepare_mon(
            core, row->source, row->level, row->item, true, 1U);
        struct CallObservation selected = p02s_target(
            core, P02S_MODE_NORMAL, 0U);
        struct CallObservation removed = call_bounded(
            core, P02S_ITEM_EVOLUTION_REMOVAL,
            QOL_PLAYER_PARTY, 0U, 0U, 0U);
        if (selected.result != row->target || !removed.payload_pc_seen
            || p02s_data(core, QOL_MON_DATA_HELD_ITEM) != 0U
            || !p02s_hidden(core))
            p02s_die("six-form correct item branch failed");
        ++matrix.conditional_selected;
        ++matrix.conditional_consumed;
        ++matrix.hidden_preserved;

        restore_snapshot(core, field);
        p02s_prepare_mon(
            core, row->source, (uint8_t)(row->level - 1U),
            row->item, true, 1U);
        selected = p02s_target(core, P02S_MODE_NORMAL, 0U);
        removed = call_bounded(
            core, P02S_ITEM_EVOLUTION_REMOVAL,
            QOL_PLAYER_PARTY, 0U, 0U, 0U);
        if (selected.result != 0U || !removed.payload_pc_seen
            || p02s_data(core, QOL_MON_DATA_HELD_ITEM) != row->item
            || !p02s_hidden(core))
            p02s_die("six-form below-level branch failed");
        ++matrix.below_rejected;
        ++matrix.hidden_preserved;

        restore_snapshot(core, field);
        p02s_prepare_mon(core, row->source, row->level, 1U, true, 1U);
        selected = p02s_target(core, P02S_MODE_NORMAL, 0U);
        removed = call_bounded(
            core, P02S_ITEM_EVOLUTION_REMOVAL,
            QOL_PLAYER_PARTY, 0U, 0U, 0U);
        if (selected.result != row->regular || !removed.payload_pc_seen
            || p02s_data(core, QOL_MON_DATA_HELD_ITEM) != 1U
            || !p02s_hidden(core))
            p02s_die("six-form wrong-item regular branch failed");
        ++matrix.regular_selected;
        ++matrix.hidden_preserved;

        restore_snapshot(core, field);
        p02s_prepare_mon(core, row->source, row->level, 0U, true, 1U);
        selected = p02s_target(core, P02S_MODE_NORMAL, 0U);
        removed = call_bounded(
            core, P02S_ITEM_EVOLUTION_REMOVAL,
            QOL_PLAYER_PARTY, 0U, 0U, 0U);
        if (selected.result != row->regular || !removed.payload_pc_seen
            || p02s_data(core, QOL_MON_DATA_HELD_ITEM) != 0U
            || !p02s_hidden(core))
            p02s_die("six-form missing-item regular branch failed");
        ++matrix.regular_selected;
        ++matrix.hidden_preserved;
    }
    if (matrix.conditional_selected != 6U
        || matrix.conditional_consumed != 6U
        || matrix.below_rejected != 6U
        || matrix.regular_selected != 12U
        || matrix.hidden_preserved != 24U)
        p02s_die("six-form matrix count failed");
    return matrix;
}

static bool p02s_remove_all_item(struct mCore *core, uint16_t item)
{
    for (unsigned count = 0U; count < 999U; ++count) {
        if (call_preserving(
                core, QOL_CHECK_BAG_ITEM, item, 1U, 0U, 0U) == 0U)
            return true;
        if (call_preserving(
                core, P02S_REMOVE_BAG_ITEM, item, 1U, 0U, 0U) != 1U)
            return false;
    }
    return false;
}

static bool p02s_missing_item_input(struct mCore *core, uint16_t item,
                                    bool *party_opened_for_item)
{
    if (!p02s_remove_all_item(core, item)
        || !p02s_keep_only_bag_item(core, item)
        || !p02s_bag_exact(core, item, 0U)
        || !p02s_enter_bag_physical(
            core, "bag_item_missing_entry", item))
        return false;
    *party_opened_for_item = false;
    for (unsigned frame = 0U; frame < 600U; ++frame) {
        uint16_t key = frame % 120U < 2U ? QOL_KEY_A : 0U;
        core->setKeys(core, key);
        core->runFrame(core);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == P02S_CB2_PARTY
            && read16(core, QOL_SPECIAL_VAR_ITEM) == item)
            *party_opened_for_item = true;
    }
    core->setKeys(core, 0U);
    if (*party_opened_for_item)
        p02s_diagnostic(
            core, "bag_item_missing_entry",
            "absent_item_unexpectedly_opened_party", 600U, item);
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 5) {
        fprintf(stderr,
                "usage: %s ROM SAVE EXPECTED_ROM_SHA256 EXPECTED_SEED_SHA256\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    char seed_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[3]) != 64U || strcmp(rom_sha256, argv[3]) != 0)
        p02s_die("ROM SHA-256 mismatch");
    sha256_file(argv[2], seed_sha256);
    if (strlen(argv[4]) != 64U || strcmp(seed_sha256, argv[4]) != 0)
        p02s_die("private seed-save SHA-256 mismatch before boot");

    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    static color_t video[240U * 160U];
    core->setVideoBuffer(core, video, 240U);
    if (!p02s_continue_to_field(core, "initial_normal_continue"))
        p02s_die("pinned save normal Continue failed");
    if (!p02s_install_field_fixture(core)) {
        p02s_diagnostic(
            core, "fixture_replacement", "post_continue_fixture_failed",
            0U, 0U);
        p02s_die("post-Continue RAM fixture replacement failed");
    }
    p02s_enable_national_dex(core);
    struct Snapshot field = take_snapshot(core);

    struct P02SMatrix matrix = p02s_direct_matrix(core, &field);

    restore_snapshot(core, &field);
    p02s_prepare_mon(
        core, P02S_SPECIES_VEGA_001_LEEPUN, 15U, 0U, false, 1U);
    p02s_prepare_item(core, P02S_ITEM_RARE_CANDY);
    struct P02SScene cancel = p02s_run_item_scene(
        core, P02S_ITEM_RARE_CANDY, P02S_SPECIES_VEGA_001_LEEPUN,
        P02S_SPECIES_VEGA_002_LEETIN, true, "rare_candy_cancel_entry");
    bool cancel_ok = p02s_scene_seen(&cancel) && cancel.physical_b
        && p02s_data(core, QOL_MON_DATA_LEVEL) == 16U
        && p02s_data(core, QOL_MON_DATA_EXP) == 2535U
        && p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)
        && p02s_data(core, P02S_MON_DATA_SPECIES2)
            == P02S_SPECIES_VEGA_001_LEEPUN
        && p02s_moves_equal(core)
        && p02s_data(core, P02S_MON_DATA_ALT_ABILITY) == 1U;
    if (!cancel_ok)
        p02s_die("normal evolution physical-B cancel failed");

    restore_snapshot(core, &field);
    p02s_prepare_mon(
        core, P02S_SPECIES_VEGA_001_LEEPUN, 15U, 0U, false, 1U);
    p02s_prepare_item(core, P02S_ITEM_RARE_CANDY);
    struct P02SScene success = p02s_run_item_scene(
        core, P02S_ITEM_RARE_CANDY, P02S_SPECIES_VEGA_001_LEEPUN,
        P02S_SPECIES_VEGA_002_LEETIN, false,
        "rare_candy_success_entry");
    uint32_t ability2 = call_preserving(
        core, P02S_GET_ABILITY2,
        P02S_SPECIES_VEGA_002_LEETIN, 0U, 0U, 0U);
    uint32_t expected_ability = ability2 != 0U ? ability2 : call_preserving(
        core, P02S_GET_ABILITY1,
        P02S_SPECIES_VEGA_002_LEETIN, 0U, 0U, 0U);
    bool success_ok = p02s_scene_seen(&success)
        && p02s_data(core, QOL_MON_DATA_LEVEL) == 16U
        && p02s_data(core, QOL_MON_DATA_EXP) == 2535U
        && p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)
        && p02s_data(core, P02S_MON_DATA_SPECIES2)
            == P02S_SPECIES_VEGA_002_LEETIN
        && p02s_moves_equal(core)
        && p02s_data(core, P02S_MON_DATA_ALT_ABILITY) == 1U
        && call_preserving(core, P02S_GET_MON_ABILITY,
                           QOL_PLAYER_PARTY, 0U, 0U, 0U)
            == expected_ability;
    if (!success_ok)
        p02s_die("normal evolution success/ability retention failed");

    restore_snapshot(core, &field);
    p02s_prepare_mon(core, P02S_SPECIES_TOGETIC, 20U, 0U, false, 0U);
    p02s_prepare_item(core, P02S_ITEM_SUN_STONE);
    struct P02SScene bag = p02s_run_item_scene(
        core, P02S_ITEM_SUN_STONE, P02S_SPECIES_TOGETIC,
        P02S_SPECIES_TOGEKISS, false, "sun_stone_success_entry");
    bool bag_ok = bag.normal_input && p02s_scene_seen(&bag)
        && p02s_data(core, P02S_MON_DATA_SPECIES2) == P02S_SPECIES_TOGEKISS
        && p02s_bag_exact(core, P02S_ITEM_SUN_STONE, 0U)
        && p02s_moves_equal(core);
    if (!bag_ok)
        p02s_die("Bag evolution-stone success failed");

    restore_snapshot(core, &field);
    p02s_prepare_mon(core, P02S_SPECIES_TOGETIC, 20U, 0U, false, 0U);
    bool missing_party_opened = false;
    bool missing_input = p02s_missing_item_input(
        core, P02S_ITEM_SUN_STONE, &missing_party_opened);
    bool missing_ok = missing_input
        && p02s_bag_exact(core, P02S_ITEM_SUN_STONE, 0U)
        && !missing_party_opened
        && p02s_data(core, P02S_MON_DATA_SPECIES2) == P02S_SPECIES_TOGETIC;
    if (!missing_ok)
        p02s_die("missing evolution-stone normal input failed closed");

    restore_snapshot(core, &field);
    p02s_prepare_mon(
        core, P02S_SPECIES_QUILAVA, 35U,
        P02S_ITEM_SPOOKY_PLATE, true, 1U);
    p02s_prepare_item(core, P02S_ITEM_RARE_CANDY);
    struct P02SScene form = p02s_run_item_scene(
        core, P02S_ITEM_RARE_CANDY, P02S_SPECIES_QUILAVA,
        P02S_SPECIES_TYPHLOSION_H, false,
        "conditional_form_success_entry");
    uint32_t expected_hidden = call_preserving(
        core, P02S_GET_HIDDEN_ABILITY,
        P02S_SPECIES_TYPHLOSION_H, 0U, 0U, 0U);
    bool form_ok = form.normal_input && p02s_scene_seen(&form)
        && p02s_data(core, P02S_MON_DATA_SPECIES2)
            == P02S_SPECIES_TYPHLOSION_H
        && p02s_data(core, QOL_MON_DATA_HELD_ITEM) == 0U
        && p02s_moves_equal(core) && p02s_hidden(core)
        && expected_hidden != 0U
        && call_preserving(core, P02S_GET_MON_ABILITY,
                           QOL_PLAYER_PARTY, 0U, 0U, 0U)
            == expected_hidden;
    if (!form_ok)
        p02s_die("conditional form scene/hidden ability failed");

    bool saved = call_preserving(
            core, QOL_TRY_SAVING_DATA, 0U, 0U, 0U, 0U) == 1U
        && call_preserving(
            core, QOL_TRY_SAVING_DATA, 0U, 0U, 0U, 0U) == 1U;
    if (!saved)
        p02s_die("stock save failed");
    qol_close(core);
    core = NULL;

    core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    core->setVideoBuffer(core, video, 240U);
    bool loaded = p02s_continue_to_field(core, "fresh_core_normal_continue");
    bool reload_ok = loaded
        && p02s_data(core, P02S_MON_DATA_SPECIES2)
            == P02S_SPECIES_TYPHLOSION_H
        && p02s_moves_equal(core)
        && p02s_data(core, QOL_MON_DATA_HELD_ITEM) == 0U
        && p02s_data(core, P02S_MON_DATA_ALT_ABILITY) == 1U
        && p02s_hidden(core)
        && call_preserving(core, P02S_GET_MON_ABILITY,
                           QOL_PLAYER_PARTY, 0U, 0U, 0U)
            == expected_hidden;
    if (!reload_ok)
        p02s_die("fresh-core stock load did not retain evolved mon");

    if (log_problem_count != 0U)
        p02s_die("mGBA emitted warning/error diagnostics");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"STAGE71_EXACT_ROM_NORMAL_INPUT_AND_FRESH_CORE\","
        "\"rom_sha256\":\"%s\","
        "\"known_good_seed_sha256\":\"%s\","
        "\"boot_route\":\"NORMAL_TITLE_CONTINUE_PINNED_SAVE\","
        "\"initial_normal_continue_field\":true,"
        "\"fixture_replacement_after_field\":true,"
        "\"warnings_errors\":0,\"temporary_save_only\":true,"
        "\"direct_conditions\":{\"level\":true,\"friendship\":true,"
        "\"known_move\":true,\"trade\":true,\"night_form\":true,"
        "\"level_held_item_six\":{\"species_count\":%zu,"
        "\"conditional_selected\":%u,\"conditional_item_consumed\":%u,"
        "\"below_level_rejected\":%u,"
        "\"wrong_or_missing_item_regular\":%u,"
        "\"hidden_ability_preserved\":%u,\"payload_pc_seen\":%s}},"
        "\"normal_evolution_cancel\":{\"normal_bag_party_input\":%s,"
        "\"scene_callbacks_seen\":%s,\"physical_b_cancel\":%s,"
        "\"source_retained\":true,\"four_moves_retained\":true,"
        "\"ability_slot_retained\":true},"
        "\"normal_evolution_success\":{\"normal_bag_party_input\":%s,"
        "\"scene_callbacks_seen\":%s,\"target_applied\":true,"
        "\"four_moves_retained\":true,\"ability_slot_retained\":true,"
        "\"ability_matches_slot\":true},"
        "\"conditional_form_success\":{\"normal_bag_party_input\":%s,"
        "\"scene_callbacks_seen\":%s,\"exact_form_applied\":true,"
        "\"condition_item_consumed\":true,\"four_moves_retained\":true,"
        "\"hidden_ability_preserved\":true,"
        "\"ability_matches_hidden\":true},"
        "\"bag_item_use\":{\"normal_start_bag_party_input\":%s,"
        "\"scene_callbacks_seen\":%s,\"target_applied\":true,"
        "\"bag_item_consumed\":true,\"four_moves_retained\":true},"
        "\"bag_item_missing\":{\"normal_start_bag_input_attempted\":%s,"
        "\"item_absent\":true,\"party_not_opened_for_item\":true,"
        "\"species_unchanged\":true},"
        "\"save_reload\":{\"stock_save_twice\":true,"
        "\"original_core_destroyed\":true,\"fresh_core_created\":true,"
        "\"stock_load_succeeded\":true,"
        "\"normal_continue_load_succeeded\":true,"
        "\"exact_form_reloaded\":true,"
        "\"four_moves_reloaded\":true,"
        "\"condition_item_still_consumed\":true,"
        "\"hidden_ability_reloaded\":true,"
        "\"ability_matches_hidden\":true}}\n",
        rom_sha256, argv[4],
        ARRAY_LEN(p02s_repairs), matrix.conditional_selected,
        matrix.conditional_consumed, matrix.below_rejected,
        matrix.regular_selected, matrix.hidden_preserved,
        matrix.payload_seen ? "true" : "false",
        cancel.normal_input ? "true" : "false",
        p02s_scene_seen(&cancel) ? "true" : "false",
        cancel.physical_b ? "true" : "false",
        success.normal_input ? "true" : "false",
        p02s_scene_seen(&success) ? "true" : "false",
        form.normal_input ? "true" : "false",
        p02s_scene_seen(&form) ? "true" : "false",
        bag.normal_input ? "true" : "false",
        p02s_scene_seen(&bag) ? "true" : "false",
        missing_input ? "true" : "false");
    qol_close(core);
    free(field.bytes);
    return log_problem_count == 0U ? 0 : 1;
}
