/* Stage61 runtime hotfix: exact-ROM tables, consumers, and physical Bag paths. */
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
    S61_GBA_BASE = 0x08000000U,
    S61_ROM_END = 0x0A000000U,
    S61_SPECIES_COUNT = 1621U,
    S61_TMHM_COUNT = 128U,
    S61_TUTOR_COUNT = 64U,
    S61_COMPAT_STRIDE = 16U,
    S61_TM_ROOT_SITE = 0x081263D8U,
    S61_TUTOR_ROOT_SITE = 0x081213D4U,
    S61_TM_COMPAT_SITE = 0x080432B4U,
    S61_TUTOR_COMPAT_SITE = 0x08121420U,
    S61_ITEM_TABLE_SITE = 0x080001C8U,
    S61_CAN_LEARN_TM = 0x08043279U,
    S61_CAN_LEARN_TM_TUTOR = 0x08121311U,
    S61_ITEM_TO_MOVE = 0x081263C5U,
    S61_GET_TUTOR_MOVE = 0x08121399U,
    S61_LOAD_TM_NAME = 0x08132549U,
    S61_CHECK_HM = 0x081263DDU,
    S61_CAN_LEARN_TUTOR_DIRECT = 0x09110229U,
    S61_VAR_GET = 0x0806DD5DU,
    S61_VAR_SET = 0x0806DD79U,
    S61_ECOLOGY_MODE_VAR = 0x51FFU,
    S61_MOVE_MEMORY_ITEM = 347U,
    S61_ECOLOGY_ITEM = 348U,
    S61_CANONICAL_TM01 = 289U,
    S61_CANONICAL_TM50 = 338U,
    S61_CANONICAL_HM01 = 339U,
    S61_CANONICAL_HM08 = 346U,
    S61_ALIAS_TM01 = 520U,
    S61_EXPANDED_TM51 = 590U,
    S61_EXPANDED_TM120 = 659U,
    S61_ITEM_ROW_SIZE = 40U,
    S61_ITEM_MYSTERY = 21U,
    S61_ITEM_POCKET = 22U,
    S61_ITEM_TYPE = 23U,
    S61_BAG_MENU_STATE = 0x0203AC74U,
    S61_BAG_MENU_DISPLAY = 0x0203AC88U,
    S61_BAG_MAIN_CALLBACK = 0x081089E5U,
    S61_FIELD_MAIN_CALLBACK = 0x08055E75U,
    S61_FIELD_RETURN_CALLBACK = 0x0805609DU,
    S61_FIELD_ITEM_CALLBACK = 0x080A2359U,
    S61_FIELD_ITEM_WAITER = 0x080A2371U,
    S61_ITEM_USE_ON_FIELD_CB = 0x02039910U,
    S61_MOVE_MEMORY_ITEM_CB = 0x092D04F1U,
    S61_ECOLOGY_ITEM_CB = 0x092205B5U,
    S61_MOVE_MEMORY_MENU_TASK = 0x092D0589U,
    S61_ECOLOGY_MENU_TASK = 0x09220745U,
    S61_SPECIAL_RESULT = 0x02037004U,
    S61_PARTY_MAIN_CALLBACK = 0x0811F3A9U,
    S61_FRAME_LIMIT = 1800U,
};

struct S61Hook {
    uint32_t site;
    uint32_t target;
    uint8_t reg;
};

struct S61MenuTrace {
    bool opened;
    bool item_selected;
    bool primary_callback;
    bool return_callback;
    bool waiter_task;
    bool menu_task;
    bool secondary_callback_zero;
    bool window_created;
};

static const struct S61Hook S61_HOOKS[] = {
    {0x08043278U, 0x09110185U, 2U},
    {0x08121310U, 0x09110741U, 3U},
    {0x081263C4U, 0x0911047DU, 1U},
    {0x08126910U, 0x09098769U, 2U},
    {0x08132548U, 0x09110505U, 2U},
    {0x0809A02CU, 0x090987D1U, 1U},
    {0x08133EA8U, 0x090987F1U, 0U},
    {0x08134040U, 0x09098805U, 0U},
    {0x08133F84U, 0x09098845U, 2U},
    {0x08133F34U, 0x09098819U, 1U},
    {0x081263DCU, 0x09110829U, 1U},
    {0x08043800U, 0x09110829U, 1U},
    {0x0809AE94U, 0x09098779U, 0U},
    {0x08121398U, 0x091103A9U, 1U},
    {0x0813268AU, 0x09098789U, 1U},
    {0x08132D08U, 0x090987B5U, 0U},
};

static bool s61_task(struct mCore *core, uint32_t function, uint8_t *task_out)
{
    for (uint8_t task = 0U; task < 16U; ++task) {
        uint32_t row = QOL_TASKS + (uint32_t)task * QOL_TASK_SIZE;
        if (read8(core, row + 4U) && read32(core, row) == function) {
            if (task_out) *task_out = task;
            return true;
        }
    }
    return false;
}

static bool s61_hooks(struct mCore *core)
{
    for (unsigned index = 0U; index < ARRAY_LEN(S61_HOOKS); ++index) {
        const struct S61Hook *hook = &S61_HOOKS[index];
        uint32_t literal;
        if (hook->site & 2U) {
            if (read16(core, hook->site) != (uint16_t)(0x4801U | hook->reg << 8)
                || read16(core, hook->site + 2U)
                    != (uint16_t)(0x4700U | hook->reg << 3)
                || read16(core, hook->site + 4U) != 0U)
                return false;
            literal = read32(core, hook->site + 6U);
        } else {
            if (read16(core, hook->site) != (uint16_t)(0x4800U | hook->reg << 8)
                || read16(core, hook->site + 2U)
                    != (uint16_t)(0x4700U | hook->reg << 3))
                return false;
            literal = read32(core, hook->site + 4U);
        }
        if (literal != hook->target)
            return false;
    }
    return true;
}

static bool s61_continue_to_field(struct mCore *core)
{
    run_key_frames(core, 0U, 1200U);
    for (unsigned pulse = 0U; pulse < 24U; ++pulse) {
        qol_press(core, pulse == 0U ? QOL_KEY_START : QOL_KEY_A, 180U);
        uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S61_FIELD_MAIN_CALLBACK
            && save1 >= 0x02000000U && save1 < 0x02040000U) {
            run_key_frames(core, 0U, 300U);
            for (unsigned attempt = 0U; attempt < 8U; ++attempt) {
                if (read8(core, 0x0203AD72U) == 0U
                    && read8(core, 0x03005ED8U) == 0U) {
                    run_key_frames(core, 0U, 420U);
                    if (read8(core, 0x0203AD72U) == 0U
                        && read8(core, 0x03005ED8U) == 0U)
                        return true;
                }
                qol_press(core, QOL_KEY_B, 180U);
            }
        }
    }
    return false;
}

static bool s61_field_ready(struct mCore *core)
{
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S61_FIELD_MAIN_CALLBACK
        && read8(core, 0x0203AD72U) == 0U
        && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED, 0U, 0U, 0U, 0U) == 0U;
}

static bool s61_return_to_field(struct mCore *core)
{
    for (unsigned pulse = 0U; pulse < 24U; ++pulse) {
        run_key_frames(core, 0U, 60U);
        if (s61_field_ready(core))
            return true;
        qol_press(core, QOL_KEY_B, 60U);
    }
    return s61_field_ready(core);
}

static bool s61_enter_bag(struct mCore *core)
{
    run_key_frames(core, 0U, 2U);
    qol_press(core, QOL_KEY_START, 90U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT)
        return false;
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    uint8_t bag = 0xFFU;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == 2U) {
            bag = index;
            break;
        }
    }
    if (bag == 0xFFU || count == 0U)
        return false;
    while (cursor != bag) {
        qol_press(core, QOL_KEY_DOWN, 4U);
        uint8_t next = read8(core, QOL_START_MENU_CURSOR);
        if (next == cursor)
            return false;
        cursor = next;
    }
    run_key_frames(core, QOL_KEY_A, 2U);
    for (unsigned frame = 0U; frame < S61_FRAME_LIMIT; ++frame) {
        run_key_frames(core, 0U, 1U);
        uint32_t display = read32(core, S61_BAG_MENU_DISPLAY);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S61_BAG_MAIN_CALLBACK
            && display >= 0x02000000U && display < 0x02040000U)
            return true;
    }
    return false;
}

static bool s61_prepare_key_item(struct mCore *core, uint16_t item)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return false;
    uint16_t key = read16(core, save2 + 0x0F20U);
    for (unsigned slot = 0U; slot < 30U; ++slot) {
        uint32_t row = save1 + 0x03B8U + slot * 4U;
        write16(core, row, 0U);
        write16(core, row + 2U, key);
    }
    write16(core, save1 + 0x03B8U, item);
    write16(core, save1 + 0x03BAU, (uint16_t)(1U ^ key));
    return true;
}

static struct S61MenuTrace s61_open_item_menu(
    struct mCore *core, const struct Snapshot *field, uint16_t item,
    uint32_t expected_item_callback, uint32_t expected_menu_task)
{
    struct S61MenuTrace trace = {0};
    trace.secondary_callback_zero = true;
    restore_snapshot(core, field);
    if (!s61_prepare_key_item(core, item) || !s61_enter_bag(core))
        return trace;
    for (unsigned attempt = 0U; attempt < 6U
         && read8(core, S61_BAG_MENU_STATE + 6U) != 1U; ++attempt)
        qol_press(core, QOL_KEY_RIGHT, 120U);
    if (read8(core, S61_BAG_MENU_STATE + 6U) != 1U)
        return trace;
    qol_press(core, QOL_KEY_A, 60U);
    uint32_t first_frame = core->frameCounter(core);
    core->setKeys(core, QOL_KEY_A);
    while (core->frameCounter(core) - first_frame < S61_FRAME_LIMIT) {
        core->step(core);
        uint32_t elapsed = core->frameCounter(core) - first_frame;
        if (elapsed >= 2U)
            core->setKeys(core, 0U);
        if (read16(core, QOL_SPECIAL_VAR_ITEM) == item)
            trace.item_selected = true;
        if (read32(core, QOL_FIELD_CALLBACK_SLOT) == S61_FIELD_ITEM_CALLBACK)
            trace.primary_callback = true;
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S61_FIELD_RETURN_CALLBACK)
            trace.return_callback = true;
        if (s61_task(core, S61_FIELD_ITEM_WAITER, NULL))
            trace.waiter_task = true;
        if (read32(core, S61_ITEM_USE_ON_FIELD_CB) == expected_item_callback)
            trace.opened = true;
        if (read32(core, QOL_FIELD_CALLBACK_SLOT + 4U) != 0U)
            trace.secondary_callback_zero = false;
        uint8_t task = 0U;
        if (s61_task(core, expected_menu_task, &task)) {
            uint16_t window = read16(
                core, QOL_TASKS + (uint32_t)task * QOL_TASK_SIZE + 8U);
            trace.menu_task = true;
            trace.window_created = window < 32U;
            break;
        }
    }
    core->setKeys(core, 0U);
    run_key_frames(core, 0U, 20U);
    return trace;
}

static bool s61_cancel_path(struct mCore *core, const struct Snapshot *menu)
{
    restore_snapshot(core, menu);
    qol_press(core, QOL_KEY_B, 30U);
    return s61_return_to_field(core);
}

static bool s61_move_memory_selection(
    struct mCore *core, const struct Snapshot *menu, bool *result_zero,
    bool *party_opened)
{
    restore_snapshot(core, menu);
    qol_press(core, QOL_KEY_A, 20U);
    *result_zero = read16(core, S61_SPECIAL_RESULT) == 0U;
    for (unsigned pulse = 0U; pulse < 16U; ++pulse) {
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S61_PARTY_MAIN_CALLBACK) {
            *party_opened = true;
            break;
        }
        qol_press(core, QOL_KEY_A, 60U);
    }
    if (!*party_opened)
        return false;
    qol_press(core, QOL_KEY_B, 120U);
    return s61_return_to_field(core);
}

static bool s61_ecology_selection(struct mCore *core, const struct Snapshot *menu)
{
    restore_snapshot(core, menu);
    qol_press(core, QOL_KEY_DOWN, 12U);
    qol_press(core, QOL_KEY_DOWN, 12U);
    qol_press(core, QOL_KEY_A, 30U);
    bool selected = call_preserving(
        core, S61_VAR_GET, S61_ECOLOGY_MODE_VAR, 0U, 0U, 0U) == 2U;
    return selected && s61_return_to_field(core);
}

static uint16_t s61_find_species(
    struct mCore *core, uint32_t table, uint8_t slot, bool wanted)
{
    for (uint16_t species = 1U; species < S61_SPECIES_COUNT; ++species) {
        if (species == 412U)
            continue;
        bool bit = (read8(core, table + (uint32_t)species * S61_COMPAT_STRIDE
                          + slot / 8U) & (1U << (slot % 8U))) != 0U;
        if (bit == wanted)
            return species;
    }
    return 0U;
}

static bool s61_tm_runtime(struct mCore *core, uint32_t tm_table,
                           uint32_t tm_compat)
{
    const uint16_t items[] = {
        S61_CANONICAL_TM01, S61_CANONICAL_TM50, S61_ALIAS_TM01,
        S61_EXPANDED_TM51, S61_EXPANDED_TM120,
        S61_CANONICAL_HM01, S61_CANONICAL_HM08,
    };
    const uint8_t slots[] = {0U, 49U, 0U, 50U, 119U, 120U, 127U};
    for (unsigned index = 0U; index < ARRAY_LEN(items); ++index) {
        if (call_preserving(core, S61_ITEM_TO_MOVE, items[index], 0U, 0U, 0U)
            != read16(core, tm_table + (uint32_t)slots[index] * 2U))
            return false;
    }
    const uint8_t probes[] = {0U, 49U, 50U, 51U, 58U, 119U, 120U, 127U};
    for (unsigned index = 0U; index < ARRAY_LEN(probes); ++index) {
        uint8_t slot = probes[index];
        uint16_t yes = s61_find_species(core, tm_compat, slot, true);
        uint16_t no = s61_find_species(core, tm_compat, slot, false);
        if (slot == 51U) {
            if (yes != 0U)
                return false;
        } else if (!yes) {
            return false;
        }
        if (!no)
            return false;
        if (yes) {
            create_mon(core, QOL_PLAYER_PARTY, yes, 5U);
            if (call_preserving(core, S61_CAN_LEARN_TM,
                                QOL_PLAYER_PARTY, slot, 0U, 0U) != 1U)
                return false;
        }
        create_mon(core, QOL_PLAYER_PARTY, no, 5U);
        if (call_preserving(core, S61_CAN_LEARN_TM,
                            QOL_PLAYER_PARTY, slot, 0U, 0U) != 0U)
            return false;
    }
    if (call_preserving(core, S61_CHECK_HM,
                        read16(core, tm_table + 119U * 2U), 0U, 0U, 0U) != 0U)
        return false;
    for (uint8_t slot = 120U; slot < 128U; ++slot)
        if (call_preserving(core, S61_CHECK_HM,
                            read16(core, tm_table + (uint32_t)slot * 2U),
                            0U, 0U, 0U) != 1U)
            return false;
    uint32_t scratch = QOL_PARTY_SCRATCH + 0x280U;
    for (unsigned index = 0U; index < 64U; ++index)
        write8(core, scratch + index, 0xFFU);
    (void)call_preserving(core, S61_LOAD_TM_NAME,
                          scratch, S61_EXPANDED_TM120, 0U, 0U);
    return read8(core, scratch) != 0xFFU;
}

static bool s61_tutor_runtime(struct mCore *core, uint32_t tutor_table,
                              uint32_t tutor_compat)
{
    for (uint8_t slot = 0U; slot < S61_TUTOR_COUNT; ++slot) {
        uint16_t move = read16(core, tutor_table + (uint32_t)slot * 2U);
        if (move == 0U || move >= 1063U
            || call_preserving(core, S61_GET_TUTOR_MOVE,
                               slot, 0U, 0U, 0U) != move)
            return false;
    }
    if (call_preserving(core, S61_GET_TUTOR_MOVE, 64U, 0U, 0U, 0U) != 0U
        || call_preserving(core, S61_GET_TUTOR_MOVE, 151U, 0U, 0U, 0U) != 0U
        || call_preserving(core, S61_GET_TUTOR_MOVE, 152U, 0U, 0U, 0U) == 0U)
        return false;
    uint16_t yes = s61_find_species(core, tutor_compat, 63U, true);
    uint16_t no = s61_find_species(core, tutor_compat, 63U, false);
    if (!yes || !no)
        return false;
    create_mon(core, QOL_PLAYER_PARTY, yes, 5U);
    if (call_preserving(core, S61_CAN_LEARN_TUTOR_DIRECT,
                        QOL_PLAYER_PARTY, 63U, 0U, 0U) != 1U)
        return false;
    uint32_t combined = call_preserving(
        core, S61_CAN_LEARN_TM_TUTOR, QOL_PLAYER_PARTY, 0U, 63U, 0U);
    if (combined == 1U)
        return false;
    create_mon(core, QOL_PLAYER_PARTY, no, 5U);
    if (call_preserving(core, S61_CAN_LEARN_TUTOR_DIRECT,
                        QOL_PLAYER_PARTY, 63U, 0U, 0U) != 0U
        || call_preserving(core, S61_CAN_LEARN_TM_TUTOR,
                           QOL_PLAYER_PARTY, 0U, 63U, 0U) != 1U
        || call_preserving(core, S61_CAN_LEARN_TUTOR_DIRECT,
                           QOL_PLAYER_PARTY, 64U, 0U, 0U) != 0U
        || call_preserving(core, S61_CAN_LEARN_TM_TUTOR,
                           QOL_PLAYER_PARTY, 0U, 64U, 0U) != 1U)
        return false;
    return true;
}

static bool s61_item_rows(struct mCore *core, uint32_t item_table)
{
    for (uint16_t item = S61_CANONICAL_TM01; item <= S61_CANONICAL_TM50; ++item)
        if (read8(core, item_table + (uint32_t)item * S61_ITEM_ROW_SIZE
                  + S61_ITEM_MYSTERY) != (uint8_t)(item - S61_CANONICAL_TM01 + 1U))
            return false;
    for (uint16_t item = S61_CANONICAL_HM01; item <= S61_CANONICAL_HM08; ++item)
        if (read8(core, item_table + (uint32_t)item * S61_ITEM_ROW_SIZE
                  + S61_ITEM_MYSTERY) != (uint8_t)(item - S61_CANONICAL_HM01 + 121U))
            return false;
    for (uint16_t item = S61_MOVE_MEMORY_ITEM; item <= S61_ECOLOGY_ITEM; ++item) {
        uint32_t row = item_table + (uint32_t)item * S61_ITEM_ROW_SIZE;
        if (read8(core, row + S61_ITEM_POCKET) != 2U
            || read8(core, row + S61_ITEM_TYPE) != 2U)
            return false;
    }
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 3)
        return 2;
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    static color_t video[240U * 160U];
    core->setVideoBuffer(core, video, 240U);

    bool boot = s61_continue_to_field(core);
    uint32_t tm_table = read32(core, S61_TM_ROOT_SITE);
    uint32_t tutor_table = read32(core, S61_TUTOR_ROOT_SITE);
    uint32_t tm_compat = read32(core, S61_TM_COMPAT_SITE);
    uint32_t tutor_compat = read32(core, S61_TUTOR_COMPAT_SITE);
    uint32_t item_table = read32(core, S61_ITEM_TABLE_SITE);
    bool roots = tm_table >= S61_GBA_BASE && tm_table + S61_TMHM_COUNT * 2U < S61_ROM_END
        && tutor_table >= S61_GBA_BASE && tutor_table + S61_TUTOR_COUNT * 2U < S61_ROM_END
        && tm_compat >= S61_GBA_BASE
        && tm_compat + S61_SPECIES_COUNT * S61_COMPAT_STRIDE < S61_ROM_END
        && tutor_compat >= S61_GBA_BASE
        && tutor_compat + S61_SPECIES_COUNT * S61_COMPAT_STRIDE < S61_ROM_END
        && item_table >= S61_GBA_BASE && item_table < S61_ROM_END;
    bool hooks = roots && s61_hooks(core);
    bool tables = roots;
    if (tables) {
        for (uint8_t slot = 0U; slot < S61_TMHM_COUNT; ++slot) {
            uint16_t move = read16(core, tm_table + (uint32_t)slot * 2U);
            if (move == 0U || move >= 1063U) {
                tables = false;
                break;
            }
        }
    }
    struct Snapshot field = take_snapshot(core);
    bool item_rows = roots && s61_item_rows(core, item_table);
    bool tm_runtime = roots && s61_tm_runtime(core, tm_table, tm_compat);
    restore_snapshot(core, &field);
    bool tutor_runtime = roots && s61_tutor_runtime(core, tutor_table, tutor_compat);
    restore_snapshot(core, &field);

    struct S61MenuTrace move = s61_open_item_menu(
        core, &field, S61_MOVE_MEMORY_ITEM,
        S61_MOVE_MEMORY_ITEM_CB, S61_MOVE_MEMORY_MENU_TASK);
    struct Snapshot move_menu = take_snapshot(core);
    bool move_cancel = move.menu_task && s61_cancel_path(core, &move_menu);
    bool move_result_zero = false;
    bool move_party = false;
    bool move_select = move.menu_task && s61_move_memory_selection(
        core, &move_menu, &move_result_zero, &move_party);
    free(move_menu.bytes);

    restore_snapshot(core, &field);
    (void)call_preserving(core, S61_VAR_SET,
                          S61_ECOLOGY_MODE_VAR, 0U, 0U, 0U);
    struct Snapshot ecology_field = take_snapshot(core);
    struct S61MenuTrace ecology = s61_open_item_menu(
        core, &ecology_field, S61_ECOLOGY_ITEM,
        S61_ECOLOGY_ITEM_CB, S61_ECOLOGY_MENU_TASK);
    struct Snapshot ecology_menu = take_snapshot(core);
    bool ecology_cancel = ecology.menu_task && s61_cancel_path(core, &ecology_menu)
        && call_preserving(core, S61_VAR_GET,
                           S61_ECOLOGY_MODE_VAR, 0U, 0U, 0U) == 0U;
    bool ecology_select = ecology.menu_task
        && s61_ecology_selection(core, &ecology_menu);
    free(ecology_menu.bytes);
    free(ecology_field.bytes);
    free(field.bytes);

    bool move_open = move.opened && move.item_selected && move.primary_callback
        && move.return_callback && move.waiter_task && move.menu_task
        && move.secondary_callback_zero && move.window_created;
    bool ecology_open = ecology.opened && ecology.item_selected
        && ecology.primary_callback && ecology.return_callback
        && ecology.waiter_task && ecology.menu_task
        && ecology.secondary_callback_zero && ecology.window_created;
    bool logs = log_problem_count == 0U;
    bool passed = boot && roots && hooks && tables && item_rows && tm_runtime
        && tutor_runtime && move_open && move_cancel && move_result_zero
        && move_party && move_select && ecology_open && ecology_cancel
        && ecology_select && logs;
    qol_close(core);

#define JSON_BOOL(value) ((value) ? "true" : "false")
    printf("{\"schema_version\":1,\"status\":\"%s\",\"tests\":{"
           "\"field_boot\":%s,\"runtime_roots\":%s,\"runtime_hooks\":%s,"
           "\"table_bounds\":%s,\"item_rows\":%s,\"tm_hm_runtime\":%s,"
           "\"tutor_runtime\":%s,\"move_memory_menu\":%s,"
           "\"move_memory_cancel_return\":%s,\"move_memory_selection_result\":%s,"
           "\"move_memory_party_return\":%s,\"ecology_menu\":%s,"
           "\"ecology_cancel_return\":%s,\"ecology_night_return\":%s,"
           "\"warnings_errors_zero\":%s},"
           "\"coverage\":{\"tm\":120,\"hm\":8,\"tutor\":64,"
           "\"runtime_hooks\":16,\"physical_bag_items\":2,"
           "\"selection_paths\":2,\"cancel_paths\":2},"
           "\"warnings_errors\":%u}\n",
           passed ? "PASS" : "FAIL", JSON_BOOL(boot), JSON_BOOL(roots),
           JSON_BOOL(hooks), JSON_BOOL(tables), JSON_BOOL(item_rows),
           JSON_BOOL(tm_runtime), JSON_BOOL(tutor_runtime), JSON_BOOL(move_open),
           JSON_BOOL(move_cancel), JSON_BOOL(move_result_zero),
           JSON_BOOL(move_party && move_select), JSON_BOOL(ecology_open),
           JSON_BOOL(ecology_cancel), JSON_BOOL(ecology_select), JSON_BOOL(logs),
           log_problem_count);
#undef JSON_BOOL
    return passed ? 0 : 1;
}
