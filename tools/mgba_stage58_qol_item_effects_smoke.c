/*
 * Stage58 exact-ROM QOL item effect/consume/fresh-core validation.
 *
 * Phase1 resolves all 36 items through the live Item table and installed
 * gItemUseCB, then proves five representative families through physical
 * Start/Bag/Use/party/confirm-or-cancel/field-return input. Host writes are
 * limited to fixture creation/progression; effects, consumption and saved
 * results are ROM-owned. Reload is a separate process over the same sidecars.
 */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
/*
 * Test-only EWRAM gap: the tracked collection owner ends at 0x0203db00;
 * CFRU's next live field globals begin at 0x0203dfa0.  Leave 0x20 bytes below
 * those globals.  Unlike the facility rollback owner at 0x0203e400, this
 * range cannot alias the TrySavingData calls exercised by this runner.
 */
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

enum {
    S58E_STAGE = 58U,
    S58E_EFFECT_COUNT = 36U,
    S58E_CANDY_COUNT = 5U,
    S58E_EV_COUNT = 6U,
    S58E_HYPER_COUNT = 2U,
    S58E_ABILITY_COUNT = 2U,
    S58E_MINT_COUNT = 21U,
    S58E_BOX_FIRST = 12U,
    S58E_BOX_CAPACITY = 30U,
    S58E_STORAGE_POINTER = 0x03005050U,
    S58E_STORAGE_HEADER = 4U,
    S58E_BOX_MON_SIZE = 80U,
    S58E_NATURE_MINT_OFFSET = 0x0FU,
    S58E_HYPER_TRAIN_OFFSET = 0x10U,
    S58E_MON_DATA_ALT_ABILITY = 46U,
    S58E_BOX_FLAGS_OFFSET = 0x47U,
    S58E_HIDDEN_ABILITY_MASK = 0x10U,
    S58E_GET_MON_ABILITY = 0x090DA23DU,
    S58E_GET_ABILITY1 = 0x0913135DU,
    S58E_GET_ABILITY2 = 0x0913136DU,
    S58E_GET_HIDDEN_ABILITY = 0x0913137DU,
    S58E_DESTROY_TASK = 0x08076CA1U,
    S58E_REMOVE_BAG_ITEM = 0x08099BE1U,
    S58E_SAVE_BLOCK1_POINTER = 0x03005048U,
    S58E_SAVE_BLOCK2_POINTER = 0x0300504CU,
    S58E_SAVE_ITEMS_OFFSET = 0x0310U,
    S58E_SAVE_ITEMS_SLOTS = 42U,
    S58E_SAVE_ENCRYPTION_KEY_OFFSET = 0x0F20U,
    S58E_SET_SAVE_BLOCK_POINTERS = 0x0804B811U,
    S58E_SET_BAG_POCKETS_POINTERS = 0x0809984DU,
    S58E_BAG_MENU_STATE = 0x0203AC74U,
    S58E_BAG_MENU_DISPLAY = 0x0203AC88U,
    S58E_BAG_MAIN_CALLBACK = 0x081089E5U,
    S58E_FIELD_LOCK = 0x03000F9CU,
    S58E_QUEST_LOG_STATE = 0x0203AD72U,
    S58E_QUEST_LOG_PLAYBACK_STATE = 0x03005ED8U,
    S58E_FIELD_FRAMES = 1800U,
    S58E_PARTY_MAIN_CALLBACK = 0x0811F3A9U,
    S58E_PARTY_MENU_USE_EXIT = 0x0203B034U,
    S58E_SHOW_START_MENU = 0x0806EA4DU,
    S58E_SPECIES_BULBASAUR = 1U,
    S58E_SPECIES_RATTATA = 19U,
    S58E_SPECIES_DITTO = 183U,
    S58E_LEVEL_EFFECT = 50U,
    S58E_LEVEL_CAP = 100U,
    S58E_SPECIES_COUNT = 1621U,
    S58E_NORMAL_FAMILY_COUNT = 5U,
    S58E_BOTTLE_BOUNDARY_COUNT = 9U,
    S58E_WINDOWS = 0x02020430U,
    S58E_WINDOW_SIZE = 12U,
    S58E_BG0_CONTROL = 0x04000008U,
    S58E_VRAM = 0x06000000U,
    S58E_BOTTLE_CONTENT_BASE = 0x02BFU,
    S58E_BOTTLE_CONTENT_LAST = 0x038EU,
    S58E_STD_FRAME_BASE = 0x0214U,
    S58E_STD_FRAME_LAST = 0x021CU,
};

enum S58eKind {
    S58E_CANDY,
    S58E_EV_RESET,
    S58E_HYPER,
    S58E_ABILITY,
    S58E_MINT,
};

struct S58eCase {
    uint16_t item;
    uint8_t kind;
    uint8_t parameter;
};

static const struct S58eCase s58e_cases[S58E_EFFECT_COUNT] = {
    {988U, S58E_CANDY, 0U}, {989U, S58E_CANDY, 0U},
    {990U, S58E_CANDY, 0U}, {991U, S58E_CANDY, 0U},
    {992U, S58E_CANDY, 0U},
    {993U, S58E_EV_RESET, 0U}, {994U, S58E_EV_RESET, 1U},
    {995U, S58E_EV_RESET, 2U}, {996U, S58E_EV_RESET, 3U},
    {997U, S58E_EV_RESET, 4U}, {998U, S58E_EV_RESET, 5U},
    {853U, S58E_HYPER, 0U}, {854U, S58E_HYPER, 6U},
    {942U, S58E_ABILITY, 0U}, {943U, S58E_ABILITY, 1U},
    {967U, S58E_MINT, 1U}, {968U, S58E_MINT, 3U},
    {969U, S58E_MINT, 4U}, {970U, S58E_MINT, 2U},
    {971U, S58E_MINT, 5U}, {972U, S58E_MINT, 8U},
    {973U, S58E_MINT, 9U}, {974U, S58E_MINT, 7U},
    {975U, S58E_MINT, 15U}, {976U, S58E_MINT, 16U},
    {977U, S58E_MINT, 19U}, {978U, S58E_MINT, 17U},
    {979U, S58E_MINT, 20U}, {980U, S58E_MINT, 21U},
    {981U, S58E_MINT, 23U}, {982U, S58E_MINT, 22U},
    {983U, S58E_MINT, 10U}, {984U, S58E_MINT, 11U},
    {985U, S58E_MINT, 13U}, {986U, S58E_MINT, 14U},
    {987U, S58E_MINT, 12U},
};

static color_t s58e_video[240U * 160U];
static color_t s58e_bottle_frame_before[104U * 128U];

static bool s58e_rom_pointer(uint32_t address)
{
    address &= ~1U;
    return address >= 0x08000000U && address < 0x0A000000U;
}

static bool s58e_bag_exact(struct mCore *core, uint16_t item,
                           uint16_t quantity)
{
    return (quantity == 0U || call_preserving(
                core, QOL_CHECK_BAG_ITEM, item, quantity, 0U, 0U) == 1U)
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           item, (uint32_t)quantity + 1U, 0U, 0U) == 0U;
}

static bool s58e_saved_items_exact(struct mCore *core, uint16_t item,
                                    uint16_t quantity)
{
    uint32_t save1 = read32(core, S58E_SAVE_BLOCK1_POINTER);
    uint32_t save2 = read32(core, S58E_SAVE_BLOCK2_POINTER);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return false;
    uint16_t key = read16(core, save2 + S58E_SAVE_ENCRYPTION_KEY_OFFSET);
    unsigned matches = 0U;
    uint16_t found = 0U;
    for (unsigned slot = 0U; slot < S58E_SAVE_ITEMS_SLOTS; ++slot) {
        uint32_t entry = save1 + S58E_SAVE_ITEMS_OFFSET + slot * 4U;
        if (read16(core, entry) == item) {
            ++matches;
            found = read16(core, entry + 2U) ^ key;
        }
    }
    return matches == 1U && found == quantity;
}

static uint32_t s58e_box_address(struct mCore *core, unsigned index)
{
    uint32_t storage = read32(core, S58E_STORAGE_POINTER);
    unsigned box = S58E_BOX_FIRST + index / S58E_BOX_CAPACITY;
    unsigned slot = index % S58E_BOX_CAPACITY;
    if (storage < 0x02000000U || storage >= 0x02040000U)
        return 0U;
    return storage + S58E_STORAGE_HEADER
        + (box * S58E_BOX_CAPACITY + slot) * S58E_BOX_MON_SIZE;
}

static bool s58e_store_result(struct mCore *core, unsigned index)
{
    uint32_t box = S58E_BOX_FIRST + index / S58E_BOX_CAPACITY;
    uint32_t slot = index % S58E_BOX_CAPACITY;
    uint32_t species = qol_get_party_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_SPECIES);
    (void)call_preserving(core, QOL_SET_BOX_MON, box, slot,
                          QOL_PLAYER_PARTY, 0U);
    return species != 0U && call_preserving(
        core, QOL_GET_BOX_MON_DATA_AT, box, slot,
        QOL_MON_DATA_SPECIES, 0U) == species;
}

static uint32_t s58e_task(struct mCore *core)
{
    uint32_t task = call_preserving(
        core, QOL_CREATE_TASK, QOL_TASK_DUMMY, 0x50U, 0U, 0U);
    return task < 16U ? task : UINT32_MAX;
}

static void s58e_destroy_task(struct mCore *core, uint32_t task)
{
    /* Some quantity callbacks recycle/destroy the synthetic caller before
     * control returns, so invoking DestroyTask a second time is unsafe.  This
     * is task-fixture cleanup only: effect fields and Bag state remain owned
     * by ROM callbacks. */
    if (task < 16U) {
        uint32_t address = QOL_TASKS + task * QOL_TASK_SIZE;
        if (read8(core, address + 4U) != 0U
            && read32(core, address) == QOL_TASK_DUMMY)
            write8(core, address + 4U, 0U);
    }
}

static bool s58e_begin_item_callback(struct mCore *core, uint16_t item,
                                     uint32_t *task_out,
                                     uint32_t *handler_out)
{
    uint32_t task = s58e_task(core);
    uint32_t entry = QOL_ITEM_TABLE
        + (uint32_t)item * QOL_ITEM_ROW_SIZE + QOL_ITEM_CALLBACK_OFFSET;
    uint32_t field = read32(core, entry);
    if (task == UINT32_MAX || !s58e_rom_pointer(field))
        return false;
    write16(core, QOL_SPECIAL_VAR_ITEM, item);
    write8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT, 0U);
    write8(core, QOL_PARTY_MENU + 11U, 0U);
    call_preserving(core, field, task, 0U, 0U, 0U);
    uint32_t callback = read32(core, QOL_ITEM_USE_CALLBACK);
    if (!s58e_rom_pointer(callback)) {
        s58e_destroy_task(core, task);
        return false;
    }
    call_preserving(core, callback, task, QOL_TASK_DUMMY, 0U, 0U);
    *task_out = task;
    *handler_out = read32(core, QOL_TASKS + task * QOL_TASK_SIZE);
    return true;
}

static bool s58e_offer_attempt(struct mCore *core, uint16_t item,
                               uint16_t key, bool expect_offer)
{
    uint32_t task = UINT32_MAX, handler = 0U;
    if (!s58e_begin_item_callback(core, item, &task, &handler))
        return false;
    bool offered = s58e_rom_pointer(handler) && handler != QOL_TASK_DUMMY;
    if (offered != expect_offer) {
        s58e_destroy_task(core, task);
        return false;
    }
    if (expect_offer) {
        /* The exhaustive lane dispatches the live yes/no task itself so the
         * result can be sampled before Task_ClosePartyMenuAfterText tears
         * down its synthetic caller.  The separate normal-Bag lane below is
         * the physical GBA-input proof.  gMain.newKeys is input-fixture state,
         * never an item/effect/result field.  The pinned CFRU Task_Offer*
         * stubs have an exact two-halfword signature and store their paired
         * Task_Handle* pointer at +0x30; each paired handler similarly stores
         * Task_Change* at +0x4c.  These live literals keep the runner bound to
         * the exact installed task family without hard-coding one family. */
        uint32_t offer = handler & ~1U;
        if (read16(core, offer) != 0xB510U
            || read16(core, offer + 2U) != 0x4B08U)
            return false;
        uint32_t choice = read32(core, offer + 0x30U);
        uint32_t change = read32(core, (choice & ~1U) + 0x4CU);
        if (!s58e_rom_pointer(choice) || !s58e_rom_pointer(change)
            || read16(core, choice & ~1U) != 0xB510U
            || read16(core, (choice & ~1U) + 2U) != 0x4B0EU)
            return false;
        write16(core, 0x0300315EU, key);
        call_preserving(core, choice, task, 0U, 0U, 0U);
        write16(core, 0x0300315EU, 0U);
        if (key == QOL_KEY_A) {
            handler = read32(core, QOL_TASKS + task * QOL_TASK_SIZE);
            if (handler != change)
                return false;
            call_preserving(core, handler, task, 0U, 0U, 0U);
        } else if (read32(core, QOL_TASKS + task * QOL_TASK_SIZE) == choice
                   || read32(core, QOL_TASKS + task * QOL_TASK_SIZE) == change) {
            return false;
        }
    }
    s58e_destroy_task(core, task);
    return true;
}

static bool s58e_quantity_attempt(struct mCore *core, uint16_t item,
                                  uint16_t key)
{
    uint32_t task = UINT32_MAX, handler = 0U;
    if (!s58e_begin_item_callback(core, item, &task, &handler)
        || !s58e_rom_pointer(handler)) {
        s58e_destroy_task(core, task);
        return false;
    }
    qol_press(core, key, 180U);
    s58e_destroy_task(core, task);
    return true;
}

static bool s58e_enter_party(struct mCore *core)
{
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != 0x08055E75U)
        return false;
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_DH_CLEAR,
                          0U, 0U, 0U);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_POKEMON_GET,
                          0U, 0U, 0U);
    (void)call_preserving(core, S58E_SHOW_START_MENU,
                          0U, 0U, 0U, 0U);
    run_key_frames(core, 0U, 90U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT) {
        /* A saved button-mode/shortcut state can route the same physical
         * START pulse directly into the stock party initializer. */
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != 0x08055E75U) {
            run_key_frames(core, 0U, S58E_FIELD_FRAMES);
            bool entered = read8(
                    core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT) == 0U
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58E_PARTY_MAIN_CALLBACK;
            return entered;
        }
        return false;
    }
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    uint8_t pokemon = 0xFFU;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == 1U) {
            pokemon = index;
            break;
        }
    }
    if (pokemon == 0xFFU || count == 0U)
        return false;
    while (cursor != pokemon) {
        qol_press(core, QOL_KEY_DOWN, 4U);
        cursor = (uint8_t)((cursor + 1U) % count);
    }
    qol_press(core, QOL_KEY_A, 600U);
    bool entered = read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT) == 0U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) != 0x08055E75U;
    return entered;
}

static bool s58e_enter_bag_physical(struct mCore *core)
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
    for (unsigned frame = 0U; frame < S58E_FIELD_FRAMES; ++frame) {
        run_key_frames(core, 0U, 1U);
        uint32_t display = read32(core, S58E_BAG_MENU_DISPLAY);
        if (read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58E_BAG_MAIN_CALLBACK
            && display >= 0x02000000U && display < 0x02040000U)
            return true;
    }
    return false;
}

static bool s58e_keep_only_bag_item(struct mCore *core, uint16_t keep)
{
    uint32_t save1 = read32(core, S58E_SAVE_BLOCK1_POINTER);
    uint32_t save2 = read32(core, S58E_SAVE_BLOCK2_POINTER);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return false;
    uint16_t key = read16(core, save2 + S58E_SAVE_ENCRYPTION_KEY_OFFSET);
    for (unsigned slot = 0U; slot < S58E_SAVE_ITEMS_SLOTS; ++slot) {
        uint32_t entry = save1 + S58E_SAVE_ITEMS_OFFSET + slot * 4U;
        uint16_t item = read16(core, entry);
        uint16_t quantity = read16(core, entry + 2U) ^ key;
        if (item != 0U && item != keep && quantity != 0U
            && call_preserving(core, S58E_REMOVE_BAG_ITEM,
                               item, quantity, 0U, 0U) != 1U)
            return false;
    }
    return true;
}

static bool s58e_prepare_mint_target(struct mCore *core, uint8_t target)
{
    for (unsigned attempt = 0U; attempt < 64U; ++attempt) {
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_BULBASAUR, S58E_LEVEL_EFFECT);
        uint8_t nature = (uint8_t)(read32(core, QOL_PLAYER_PARTY) % 25U);
        if (nature == 0U || nature == 6U || nature == 18U || nature == 24U)
            nature = 12U;
        if (nature != target
            && read8(core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET) == 0U)
            return true;
    }
    return false;
}

static bool s58e_prepare_patch_target(struct mCore *core)
{
    for (uint16_t species = 1U; species < S58E_SPECIES_COUNT; ++species) {
        uint32_t first = call_preserving(
            core, S58E_GET_ABILITY1, species, 0U, 0U, 0U);
        uint32_t second = call_preserving(
            core, S58E_GET_ABILITY2, species, 0U, 0U, 0U);
        uint32_t hidden = call_preserving(
            core, S58E_GET_HIDDEN_ABILITY, species, 0U, 0U, 0U);
        if (hidden != 0U && hidden != first && hidden != second) {
            create_mon(core, QOL_PLAYER_PARTY, species, S58E_LEVEL_EFFECT);
            qol_set_mon_data(core, QOL_PLAYER_PARTY,
                             S58E_MON_DATA_ALT_ABILITY, 0U, 1U);
            write8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET,
                   read8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET)
                       & (uint8_t)~S58E_HIDDEN_ABILITY_MASK);
            return true;
        }
    }
    return false;
}

static bool s58e_prepare_capsule_ineligible_target(struct mCore *core)
{
    for (uint16_t species = 1U; species < S58E_SPECIES_COUNT; ++species) {
        uint32_t first = call_preserving(
            core, S58E_GET_ABILITY1, species, 0U, 0U, 0U);
        uint32_t second = call_preserving(
            core, S58E_GET_ABILITY2, species, 0U, 0U, 0U);
        if (first != 0U && (second == 0U || second == first)) {
            create_mon(core, QOL_PLAYER_PARTY, species, S58E_LEVEL_EFFECT);
            qol_set_mon_data(core, QOL_PLAYER_PARTY,
                             S58E_MON_DATA_ALT_ABILITY, 0U, 1U);
            write8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET,
                   read8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET)
                       & (uint8_t)~S58E_HIDDEN_ABILITY_MASK);
            return true;
        }
    }
    return false;
}

static bool s58e_field_ready(struct mCore *core)
{
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == 0x08055E75U
        && read8(core, S58E_FIELD_LOCK) == 0U
        && call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                           0U, 0U, 0U, 0U) == 0U;
}

static bool s58e_return_to_field(struct mCore *core)
{
    /* Short release boundaries keep the asynchronous party->Bag->field
     * owners observable.  A 240-frame settle can run through a transient
     * owner before the next readiness sample, especially for Mint cancel. */
    for (unsigned pulse = 0U; pulse < 24U; ++pulse) {
        run_key_frames(core, 0U, 60U);
        if (s58e_field_ready(core))
            return true;
        qol_press(core, QOL_KEY_B, 60U);
    }
    return s58e_field_ready(core);
}

static bool s58e_enter_item_party(struct mCore *core, uint16_t item)
{
    if (!s58e_enter_bag_physical(core)) {
        fprintf(stderr,
                "item party bag entry item=%u cb=%08" PRIx32
                " startcb=%08" PRIx32 " bagdisplay=%08" PRIx32 "\n",
                item, read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read32(core, QOL_START_MENU_CALLBACK),
                read32(core, S58E_BAG_MENU_DISPLAY));
        return false;
    }
    qol_press(core, QOL_KEY_A, 120U);
    for (unsigned move = 0U; move < 8U; ++move)
        qol_press(core, QOL_KEY_UP, 20U);
    for (unsigned attempt = 0U; attempt < 10U; ++attempt) {
        qol_press(core, QOL_KEY_A, 120U);
        if (read16(core, QOL_SPECIAL_VAR_ITEM) == item
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58E_PARTY_MAIN_CALLBACK
            && read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT) == 0U)
            return true;
    }
    fprintf(stderr,
            "item party selection item=%u special=%u cb=%08" PRIx32
            " slot=%u pocket=%u cursor=%u\n",
            item, read16(core, QOL_SPECIAL_VAR_ITEM),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, QOL_PARTY_MENU + QOL_PARTY_MENU_SLOT),
            read8(core, S58E_BAG_MENU_STATE),
            read8(core, S58E_BAG_MENU_STATE + 8U));
    return false;
}

static bool s58e_normal_target(struct mCore *core,
                               const struct S58eCase *row,
                               uint32_t *before_out)
{
    struct Snapshot field_base = take_snapshot(core);
    bool prepared = true;
    if (row->kind == S58E_CANDY) {
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_DITTO, S58E_LEVEL_EFFECT);
        *before_out = qol_get_mon_data(
            core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP);
    } else if (row->kind == S58E_EV_RESET) {
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_BULBASAUR, S58E_LEVEL_EFFECT);
        for (unsigned stat = 0U; stat < 6U; ++stat)
            set_mon_data_u32(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat, 40U);
        *before_out = 40U;
    } else if (row->kind == S58E_HYPER) {
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_BULBASAUR, S58E_LEVEL_CAP);
        for (unsigned stat = 0U; stat < 6U; ++stat)
            set_mon_data_u32(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_IV + stat, 0U);
        *before_out = read8(
            core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET);
    } else if (row->kind == S58E_ABILITY) {
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_RATTATA, S58E_LEVEL_EFFECT);
        set_mon_data_u32(core, QOL_PLAYER_PARTY,
                         S58E_MON_DATA_ALT_ABILITY, 0U);
        write8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET,
               read8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET)
                   & (uint8_t)~S58E_HIDDEN_ABILITY_MASK);
        *before_out = call_preserving(
            core, S58E_GET_MON_ABILITY, QOL_PLAYER_PARTY, 0U, 0U, 0U);
    } else {
        if (!s58e_prepare_mint_target(core, row->parameter))
            prepared = false;
        *before_out = read8(
            core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET);
    }
    uint8_t image[QOL_PARTY_MON_SIZE];
    for (unsigned byte = 0U; byte < sizeof(image); ++byte)
        image[byte] = read8(core, QOL_PLAYER_PARTY + byte);
    restore_snapshot(core, &field_base);
    free(field_base.bytes);
    if (!prepared)
        return false;
    install_mon_image(core, QOL_PLAYER_PARTY, image);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    return true;
}

static bool s58e_normal_effect(struct mCore *core,
                               const struct S58eCase *row,
                               uint32_t before)
{
    if (row->kind == S58E_CANDY)
        return qol_get_mon_data(core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP)
            > before;
    if (row->kind == S58E_EV_RESET)
        return qol_get_mon_data(
            core, QOL_PLAYER_PARTY,
            QOL_MON_DATA_HP_EV + row->parameter) == 0U;
    if (row->kind == S58E_HYPER)
        return (read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET)
                & (row->parameter == 6U ? 0x3FU : 0x01U))
            == (row->parameter == 6U ? 0x3FU : 0x01U);
    if (row->kind == S58E_ABILITY)
        return call_preserving(core, S58E_GET_MON_ABILITY,
                               QOL_PLAYER_PARTY, 0U, 0U, 0U) != before;
    return read8(core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET)
        == (uint8_t)(row->parameter + 1U);
}

static bool s58e_ui_sidecar_path(char *path, size_t size,
                                 const char *base, unsigned scenario)
{
    int length = snprintf(path, size, "%s.qol-ui-%u.sav", base, scenario);
    return length > 0 && (size_t)length < size;
}

static struct mCore *s58e_normal_fixture(const char *rom_path,
                                         const char *save_base,
                                         unsigned scenario,
                                         const struct S58eCase *row,
                                         uint32_t *before)
{
    char save_path[4096];
    if (!s58e_ui_sidecar_path(save_path, sizeof(save_path),
                              save_base, scenario))
        return NULL;
    qol_initialize_save(save_path);
    struct mCore *core = qol_open(rom_path, save_path);
    qol_log_core = core;
    memset(s58e_video, 0, sizeof(s58e_video));
    core->setVideoBuffer(core, s58e_video, 240U);
    core->reset(core);
    bool ready = qol_run_field_trace(core);
    qol_set_badges_through(core, 7U);
    (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME,
                          0U, 0U, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE,
                          QOL_LEDGER, 0U, 0U, 0U);
    ready = ready && s58e_normal_target(core, row, before)
        && s58e_keep_only_bag_item(core, row->item)
        && call_preserving(core, QOL_ADD_BAG_ITEM,
                           row->item, 3U, 0U, 0U) == 1U;
    if (!ready) {
        qol_close(core);
        return NULL;
    }
    return core;
}

static bool s58e_normal_scenario(const char *rom_path, const char *save_base,
                                 unsigned scenario,
                                 const struct S58eCase *row,
                                 bool cancel_path)
{
    uint32_t before = 0U;
    struct mCore *core = s58e_normal_fixture(
        rom_path, save_base, scenario, row, &before);
    if (core == NULL)
        return false;
    uint8_t cancel_mon[QOL_PARTY_MON_SIZE];
    for (unsigned byte = 0U; byte < sizeof(cancel_mon); ++byte)
        cancel_mon[byte] = read8(core, QOL_PLAYER_PARTY + byte);

    bool passed = s58e_enter_item_party(core, row->item);
    if (passed && cancel_path) {
        qol_press(core, QOL_KEY_A, 180U);
        qol_press(core, QOL_KEY_B, 240U);
        passed = s58e_return_to_field(core);
        if (passed)
            run_key_frames(core, 0U, 2U);
        passed = passed && s58e_bag_exact(core, row->item, 3U)
            && !s58e_normal_effect(core, row, before);
        for (unsigned byte = 0U;
             passed && byte < sizeof(cancel_mon); ++byte)
            passed = cancel_mon[byte]
                == read8(core, QOL_PLAYER_PARTY + byte);
    } else if (passed) {
        qol_press(core, QOL_KEY_A, 180U);
        qol_press(core, QOL_KEY_A, 240U);
        passed = s58e_return_to_field(core);
        if (passed)
            run_key_frames(core, 0U, 2U);
        passed = passed && s58e_bag_exact(core, row->item, 2U)
            && s58e_normal_effect(core, row, before);
        if (passed && row->kind == S58E_HYPER)
            passed = call_preserving(core, QOL_TRY_SAVING_DATA,
                                     0U, 0U, 0U, 0U) == 1U
                && call_preserving(core, QOL_TRY_SAVING_DATA,
                                   0U, 0U, 0U, 0U) == 1U;
    }
    qol_close(core);
    return passed;
}

static bool s58e_normal_family(const char *rom_path, const char *save_base,
                               unsigned family, unsigned case_index)
{
    const struct S58eCase *row = &s58e_cases[case_index];
    return s58e_normal_scenario(
               rom_path, save_base, family * 2U, row, true)
        && s58e_normal_scenario(
               rom_path, save_base, family * 2U + 1U, row, false);
}

static bool s58e_vram_any_nonzero(struct mCore *core,
                                  uint32_t address, unsigned size)
{
    for (unsigned byte = 0U; byte < size; ++byte)
        if (read8(core, address + byte) != 0U)
            return true;
    return false;
}

static uint64_t s58e_bottle_framebuffer_hash(unsigned *transitions,
                                              bool capture)
{
    uint64_t hash = UINT64_C(1469598103934665603);
    color_t previous = 0U;
    bool have_previous = false;
    *transitions = 0U;
    for (unsigned y = 8U; y < 136U; ++y) {
        for (unsigned x = 128U; x < 232U; ++x) {
            color_t pixel = s58e_video[y * 240U + x];
            if (capture)
                s58e_bottle_frame_before[(y - 8U) * 104U + x - 128U]
                    = pixel;
            if (have_previous && pixel != previous)
                ++*transitions;
            previous = pixel;
            have_previous = true;
            for (unsigned byte = 0U; byte < sizeof(pixel); ++byte) {
                hash ^= (uint8_t)(pixel >> (byte * 8U));
                hash *= UINT64_C(1099511628211);
            }
        }
    }
    return hash;
}

static bool s58e_bottle_menu_vram_contract(struct mCore *core,
                                            bool *framebuffer_stable)
{
    run_key_frames(core, 0U, 30U);
    unsigned window = 32U;
    for (unsigned candidate = 0U; candidate < 32U; ++candidate) {
        uint32_t descriptor = S58E_WINDOWS
            + candidate * S58E_WINDOW_SIZE;
        if (read8(core, descriptor) == 0U
            && read8(core, descriptor + 1U) == 16U
            && read8(core, descriptor + 2U) == 1U
            && read8(core, descriptor + 3U) == 13U
            && read8(core, descriptor + 4U) == 16U
            && read16(core, descriptor + 6U)
                == S58E_BOTTLE_CONTENT_BASE) {
            if (window != 32U)
                return false;
            window = candidate;
        }
    }
    if (window == 32U)
        return false;
    bool task_owner = false;
    for (unsigned task = 0U; task < 16U; ++task) {
        uint32_t address = QOL_TASKS + task * QOL_TASK_SIZE;
        uint16_t handles = read16(core, address + 8U + 10U * 2U);
        if (read8(core, address + 4U) != 0U
            && (handles & 0xFFU) == window
            && (handles >> 8) < 16U
            && s58e_rom_pointer(read32(core, address))) {
            task_owner = true;
            break;
        }
    }
    uint16_t bg0 = read16(core, S58E_BG0_CONTROL);
    uint32_t char_base = S58E_VRAM + ((bg0 >> 2U) & 3U) * 0x4000U;
    uint32_t map_base = S58E_VRAM + ((bg0 >> 8U) & 0x1FU) * 0x800U;
    for (unsigned y = 0U; y < 16U; ++y) {
        for (unsigned x = 0U; x < 13U; ++x) {
            uint16_t tile = read16(
                core, map_base + ((1U + y) * 32U + 16U + x) * 2U)
                & 0x03FFU;
            if (tile != S58E_BOTTLE_CONTENT_BASE + y * 13U + x)
                return false;
        }
    }
    static const uint16_t corners[4] = {
        S58E_STD_FRAME_BASE, S58E_STD_FRAME_BASE + 2U,
        S58E_STD_FRAME_BASE + 6U, S58E_STD_FRAME_LAST,
    };
    static const uint8_t corner_x[4] = {15U, 29U, 15U, 29U};
    static const uint8_t corner_y[4] = {0U, 0U, 17U, 17U};
    for (unsigned index = 0U; index < 4U; ++index) {
        uint16_t tile = read16(
            core, map_base
                + (corner_y[index] * 32U + corner_x[index]) * 2U)
            & 0x03FFU;
        if (tile != corners[index])
            return false;
    }
    uint32_t frame_start = char_base + S58E_STD_FRAME_BASE * 32U;
    uint32_t frame_end = char_base + (S58E_STD_FRAME_LAST + 1U) * 32U;
    uint32_t content_start = char_base + S58E_BOTTLE_CONTENT_BASE * 32U;
    uint32_t content_end = char_base
        + (S58E_BOTTLE_CONTENT_LAST + 1U) * 32U;
    unsigned transitions_before = 0U, transitions_after = 0U;
    uint64_t framebuffer_before = s58e_bottle_framebuffer_hash(
        &transitions_before, true);
    run_key_frames(core, 0U, 2U);
    uint64_t framebuffer_after = s58e_bottle_framebuffer_hash(
        &transitions_after, false);
    unsigned unchanged = 0U;
    for (unsigned y = 8U; y < 136U; ++y)
        for (unsigned x = 128U; x < 232U; ++x)
            unchanged += s58e_video[y * 240U + x]
                == s58e_bottle_frame_before[(y - 8U) * 104U + x - 128U];
    *framebuffer_stable = transitions_before > 16U
        && transitions_after > 16U
        && framebuffer_before != 0U && framebuffer_after != 0U
        && unchanged * 100U >= 104U * 128U * 90U;
    return task_owner && frame_end <= content_start
        && s58e_vram_any_nonzero(
            core, frame_start, (unsigned)(frame_end - frame_start))
        && s58e_vram_any_nonzero(
            core, content_start, (unsigned)(content_end - content_start));
}

static bool s58e_normal_bottle_reopen(
    const char *rom_path, const char *save_base,
    bool *cancelled, bool *successful, bool *reopened, bool *vram_contract,
    bool *framebuffer_stable)
{
    const struct S58eCase *row = &s58e_cases[11U];
    uint32_t before = 0U;
    struct mCore *core = s58e_normal_fixture(
        rom_path, save_base, 4U, row, &before);
    if (core == NULL)
        return false;
    uint8_t mon_before[QOL_PARTY_MON_SIZE];
    for (unsigned byte = 0U; byte < sizeof(mon_before); ++byte)
        mon_before[byte] = read8(core, QOL_PLAYER_PARTY + byte);

    bool passed = s58e_enter_item_party(core, row->item);
    if (passed) {
        qol_press(core, QOL_KEY_A, 180U);
        *vram_contract = s58e_bottle_menu_vram_contract(
            core, framebuffer_stable);
        qol_press(core, QOL_KEY_B, 240U);
        passed = s58e_return_to_field(core);
    }
    if (passed)
        run_key_frames(core, 0U, 2U);
    bool cancel_bag = passed && s58e_bag_exact(core, row->item, 3U);
    bool cancel_effect_unchanged = passed
        && !s58e_normal_effect(core, row, before);
    *cancelled = passed && cancel_bag && cancel_effect_unchanged;
    unsigned cancel_first_difference = sizeof(mon_before);
    for (unsigned byte = 0U;
         *cancelled && byte < sizeof(mon_before); ++byte) {
        if (mon_before[byte] != read8(core, QOL_PLAYER_PARTY + byte)) {
            cancel_first_difference = byte;
            *cancelled = false;
        }
    }
    if (!*cancelled)
        fprintf(stderr,
                "bottle cancel passed=%u bag=%u effect_unchanged=%u "
                "first_mon_diff=%u party_exit=%u cb=%08" PRIx32 "\n",
                passed, cancel_bag, cancel_effect_unchanged,
                cancel_first_difference,
                read8(core, S58E_PARTY_MENU_USE_EXIT),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));

    *reopened = *cancelled && s58e_enter_item_party(core, row->item);
    passed = *reopened;
    if (passed) {
        qol_press(core, QOL_KEY_A, 180U);
        bool success_framebuffer = false;
        *vram_contract = *vram_contract
            && s58e_bottle_menu_vram_contract(
                core, &success_framebuffer);
        *framebuffer_stable = *framebuffer_stable && success_framebuffer;
        qol_press(core, QOL_KEY_A, 240U);
        passed = s58e_return_to_field(core);
    }
    if (passed)
        run_key_frames(core, 0U, 2U);
    *successful = passed && s58e_bag_exact(core, row->item, 2U)
        && s58e_normal_effect(core, row, before);
    if (*successful)
        *successful = call_preserving(core, QOL_TRY_SAVING_DATA,
                                      0U, 0U, 0U, 0U) == 1U
            && call_preserving(core, QOL_TRY_SAVING_DATA,
                               0U, 0U, 0U, 0U) == 1U;
    qol_close(core);
    return *cancelled && *successful && *reopened && *vram_contract
        && *framebuffer_stable;
}

static bool s58e_normal_bottle_no_effect(
    const char *rom_path, const char *save_base, unsigned scenario,
    unsigned mode)
{
    const struct S58eCase *row = &s58e_cases[11U];
    uint32_t before = 0U;
    struct mCore *core = s58e_normal_fixture(
        rom_path, save_base, scenario, row, &before);
    if (core == NULL)
        return false;
    if (mode == 0U) {
        write8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET,
               read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET)
                   | 0x01U);
    } else if (mode == 1U) {
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_IS_EGG, 1U, 1U);
    } else if (mode == 2U) {
        struct CpuState scheduler = capture_cpu_state(core);
        qol_clear_progression(core);
        restore_cpu_state(core, &scheduler);
    } else {
        qol_close(core);
        return false;
    }
    uint8_t mon_before[QOL_PARTY_MON_SIZE];
    for (unsigned byte = 0U; byte < sizeof(mon_before); ++byte)
        mon_before[byte] = read8(core, QOL_PLAYER_PARTY + byte);

    bool passed = s58e_enter_item_party(core, row->item);
    if (passed) {
        qol_press(core, QOL_KEY_A, 180U);
        qol_press(core, QOL_KEY_A, 240U);
        passed = s58e_return_to_field(core);
    }
    if (passed)
        run_key_frames(core, 0U, 2U);
    passed = passed && s58e_bag_exact(core, row->item, 3U);
    for (unsigned byte = 0U;
         passed && byte < sizeof(mon_before); ++byte)
        passed = mon_before[byte]
            == read8(core, QOL_PLAYER_PARTY + byte);
    qol_close(core);
    return passed;
}

static bool s58e_normal_bottle_family(
    const char *rom_path, const char *save_base,
    bool boundaries[S58E_BOTTLE_BOUNDARY_COUNT])
{
    (void)s58e_normal_bottle_reopen(
        rom_path, save_base, &boundaries[0], &boundaries[1],
        &boundaries[6], &boundaries[7], &boundaries[8]);
    boundaries[2] = s58e_normal_scenario(
        rom_path, save_base, 10U, &s58e_cases[12U], false);
    boundaries[3] = s58e_normal_bottle_no_effect(
        rom_path, save_base, 11U, 0U);
    boundaries[4] = s58e_normal_bottle_no_effect(
        rom_path, save_base, 12U, 1U);
    boundaries[5] = s58e_normal_bottle_no_effect(
        rom_path, save_base, 13U, 2U);
    for (unsigned index = 0U; index < S58E_BOTTLE_BOUNDARY_COUNT; ++index)
        if (!boundaries[index])
            return false;
    return true;
}

static unsigned s58e_normal_families(const char *rom_path,
                                      const char *save_base,
                                      bool results[S58E_NORMAL_FAMILY_COUNT],
                                      bool bottle[S58E_BOTTLE_BOUNDARY_COUNT])
{
    /* Separate entry rows prove the shared Candy/EV callback through both
     * normal Bag entries, plus Bottle Cap service, Ability and Mint. */
    static const unsigned case_indices[S58E_NORMAL_FAMILY_COUNT] = {
        0U, 5U, 11U, 13U, 15U,
    };
    unsigned passed = 0U;
    for (unsigned family = 0U;
         family < S58E_NORMAL_FAMILY_COUNT; ++family) {
        results[family] = family == 2U
            ? s58e_normal_bottle_family(rom_path, save_base, bottle)
            : s58e_normal_family(
                rom_path, save_base, family, case_indices[family]);
        if (results[family])
            ++passed;
    }
    return passed;
}

static bool s58e_candy_case(struct mCore *core, unsigned index,
                            const struct S58eCase *row,
                            unsigned *cancelled, unsigned *successful,
                            unsigned *effectless)
{
    create_mon(core, QOL_PLAYER_PARTY,
               S58E_SPECIES_DITTO, S58E_LEVEL_EFFECT);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    uint32_t before = qol_get_mon_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP);
    bool added = call_preserving(
        core, QOL_ADD_BAG_ITEM, row->item, 3U, 0U, 0U) != 0U;
    struct Snapshot attempt_base = take_snapshot(core);
    bool cancel_path = added
        && s58e_quantity_attempt(core, row->item, QOL_KEY_B);
    bool cancel_bag = cancel_path && s58e_bag_exact(core, row->item, 3U);
    uint32_t cancel_exp = qol_get_mon_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP);
    if (!added || !cancel_path || !cancel_bag || cancel_exp != before) {
        fprintf(stderr, "candy cancel item=%u add=%u path=%u bag=%u exp=%" PRIu32 "/%" PRIu32 "\n",
                row->item, added, cancel_path, cancel_bag, before, cancel_exp);
        free(attempt_base.bytes);
        return false;
    }
    ++*cancelled;
    restore_snapshot(core, &attempt_base);
    bool success_path = s58e_quantity_attempt(core, row->item, QOL_KEY_A);
    bool success_bag = s58e_bag_exact(core, row->item, 2U);
    uint32_t success_exp = qol_get_mon_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP);
    bool stored = success_exp > before && s58e_store_result(core, index);
    if (!success_path || !success_bag || success_exp <= before || !stored) {
        fprintf(stderr, "candy success item=%u path=%u bag=%u exp=%" PRIu32 "/%" PRIu32 " stored=%u\n",
                row->item, success_path, success_bag, before, success_exp,
                stored);
        free(attempt_base.bytes);
        return false;
    }
    ++*successful;
    struct Snapshot success_state = take_snapshot(core);
    restore_snapshot(core, &attempt_base);
    if (call_preserving(core, S58E_REMOVE_BAG_ITEM,
                        row->item, 1U, 0U, 0U) != 1U) {
        free(attempt_base.bytes);
        free(success_state.bytes);
        return false;
    }
    create_mon(core, QOL_PLAYER_PARTY,
               S58E_SPECIES_DITTO, S58E_LEVEL_CAP);
    before = qol_get_mon_data(core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP);
    if (!s58e_quantity_attempt(core, row->item, QOL_KEY_A)
        || !s58e_bag_exact(core, row->item, 2U)
        || qol_get_mon_data(core, QOL_PLAYER_PARTY, QOL_MON_DATA_EXP) != before) {
        free(attempt_base.bytes);
        free(success_state.bytes);
        return false;
    }
    ++*effectless;
    restore_snapshot(core, &success_state);
    free(attempt_base.bytes);
    free(success_state.bytes);
    return true;
}

static bool s58e_ev_case(struct mCore *core, unsigned index,
                         const struct S58eCase *row,
                         unsigned *cancelled, unsigned *successful,
                         unsigned *effectless)
{
    create_mon(core, QOL_PLAYER_PARTY,
               S58E_SPECIES_BULBASAUR, S58E_LEVEL_EFFECT);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    for (unsigned stat = 0U; stat < 6U; ++stat)
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_EV + stat, 40U, 1U);
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, row->item, 3U, 0U, 0U))
        return false;
    struct Snapshot attempt_base = take_snapshot(core);
    if (!s58e_quantity_attempt(core, row->item, QOL_KEY_B)
        || !s58e_bag_exact(core, row->item, 3U))
        goto fail_base;
    for (unsigned stat = 0U; stat < 6U; ++stat)
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat) != 40U)
            goto fail_base;
    ++*cancelled;
    restore_snapshot(core, &attempt_base);
    if (!s58e_quantity_attempt(core, row->item, QOL_KEY_A)
        || !s58e_bag_exact(core, row->item, 2U))
        goto fail_base;
    for (unsigned stat = 0U; stat < 6U; ++stat)
        if (qol_get_mon_data(core, QOL_PLAYER_PARTY,
                             QOL_MON_DATA_HP_EV + stat)
            != (stat == row->parameter ? 0U : 40U))
            goto fail_base;
    ++*successful;
    bool stored = s58e_store_result(core, index);
    struct Snapshot success_state = take_snapshot(core);
    restore_snapshot(core, &attempt_base);
    if (call_preserving(core, S58E_REMOVE_BAG_ITEM,
                        row->item, 1U, 0U, 0U) != 1U)
        goto fail_both;
    qol_set_mon_data(core, QOL_PLAYER_PARTY,
                     QOL_MON_DATA_HP_EV + row->parameter, 0U, 1U);
    bool no_effect = s58e_quantity_attempt(core, row->item, QOL_KEY_A);
    bool retained = s58e_bag_exact(core, row->item, 2U);
    if (!stored || !no_effect || !retained) {
        fprintf(stderr, "ev effectless item=%u stored=%u path=%u bag=%u\n",
                row->item, stored, no_effect, retained);
        goto fail_both;
    }
    ++*effectless;
    restore_snapshot(core, &success_state);
    free(attempt_base.bytes);
    free(success_state.bytes);
    return true;

fail_both:
    free(success_state.bytes);
fail_base:
    free(attempt_base.bytes);
    return false;
}

static bool s58e_hyper_case(struct mCore *core, uint32_t dispatch,
                            unsigned index, const struct S58eCase *row,
                            unsigned *cancelled, unsigned *successful,
                            unsigned *effectless)
{
    create_mon(core, QOL_PLAYER_PARTY,
               S58E_SPECIES_BULBASAUR, S58E_LEVEL_CAP);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    for (unsigned stat = 0U; stat < 6U; ++stat)
        qol_set_mon_data(core, QOL_PLAYER_PARTY,
                         QOL_MON_DATA_HP_IV + stat, 0U, 1U);
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, row->item, 3U, 0U, 0U)
        || call_preserving(core, dispatch, QOL_SERVICE_HYPER_TRAIN,
                           0U, row->parameter, 1U) != QOL_STATUS_CANCELLED
        || !s58e_bag_exact(core, row->item, 3U)
        || read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET) != 0U)
        return false;
    ++*cancelled;
    uint32_t applied = call_preserving(
        core, dispatch, QOL_SERVICE_HYPER_TRAIN,
        0U, row->parameter, 0U);
    bool bag2 = s58e_bag_exact(core, row->item, 2U);
    if (applied != QOL_STATUS_OK || !bag2) {
        fprintf(stderr, "hyper apply item=%u stat=%u status=%" PRIu32
                " mask=%02x bag=%u\n", row->item, row->parameter, applied,
                read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET),
                bag2);
        return false;
    }
    uint8_t mask = row->parameter == 6U ? 0x3FU : 0x01U;
    if ((read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET) & mask)
            != mask
        || !s58e_store_result(core, index))
        return false;
    ++*successful;
    uint32_t repeated = call_preserving(
        core, dispatch, QOL_SERVICE_HYPER_TRAIN,
        0U, row->parameter, 0U);
    if (repeated != QOL_STATUS_EFFECTLESS
        || !s58e_bag_exact(core, row->item, 2U)) {
        fprintf(stderr, "hyper repeat item=%u stat=%u status=%" PRIu32
                " mask=%02x\n", row->item, row->parameter, repeated,
                read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET));
        return false;
    }
    ++*effectless;
    return true;
}

static bool s58e_ability_case(struct mCore *core, unsigned index,
                              const struct S58eCase *row,
                              unsigned *cancelled, unsigned *successful,
                              unsigned *effectless)
{
    create_mon(core, QOL_PLAYER_PARTY,
               S58E_SPECIES_RATTATA, S58E_LEVEL_EFFECT);
    qol_set_mon_data(core, QOL_PLAYER_PARTY,
                     S58E_MON_DATA_ALT_ABILITY, 0U, 1U);
    /* Deterministic eligible fixture: use Rattata's first normal ability.
     * The ROM callback remains the sole writer on all measured result paths. */
    write8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET,
           read8(core, QOL_PLAYER_PARTY + S58E_BOX_FLAGS_OFFSET)
               & (uint8_t)~S58E_HIDDEN_ABILITY_MASK);
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    if (row->parameter != 0U && !s58e_prepare_patch_target(core))
        return false;
    uint32_t ability_before = call_preserving(
        core, S58E_GET_MON_ABILITY, QOL_PLAYER_PARTY, 0U, 0U, 0U);
    uint32_t alt_before = qol_get_mon_data(
        core, QOL_PLAYER_PARTY, S58E_MON_DATA_ALT_ABILITY);
    bool added = call_preserving(
        core, QOL_ADD_BAG_ITEM, row->item, 3U, 0U, 0U) != 0U;
    if (!added)
        return false;
    struct Snapshot attempt_base = take_snapshot(core);
    bool offered = s58e_offer_attempt(core, row->item, QOL_KEY_B, true);
    bool bag3 = s58e_bag_exact(core, row->item, 3U);
    uint32_t cancel_ability = call_preserving(
        core, S58E_GET_MON_ABILITY, QOL_PLAYER_PARTY, 0U, 0U, 0U);
    uint32_t cancel_alt = qol_get_mon_data(
        core, QOL_PLAYER_PARTY, S58E_MON_DATA_ALT_ABILITY);
    if (!offered || !bag3 || cancel_ability != ability_before
        || cancel_alt != alt_before) {
        fprintf(stderr, "ability cancel item=%u add=%u offer=%u bag=%u "
                "ability=%" PRIu32 "/%" PRIu32 " alt=%" PRIu32
                "/%" PRIu32 "\n", row->item, added, offered, bag3,
                ability_before, cancel_ability, alt_before, cancel_alt);
        goto fail_base;
    }
    ++*cancelled;
    restore_snapshot(core, &attempt_base);
    if (!s58e_offer_attempt(core, row->item, QOL_KEY_A, true)
        || !s58e_bag_exact(core, row->item, 2U))
        goto fail_base;
    uint32_t ability_after = call_preserving(
        core, S58E_GET_MON_ABILITY, QOL_PLAYER_PARTY, 0U, 0U, 0U);
    if (ability_after == ability_before
        || (row->parameter == 0U && qol_get_mon_data(
            core, QOL_PLAYER_PARTY, S58E_MON_DATA_ALT_ABILITY) == alt_before)
        || !s58e_store_result(core, index))
        goto fail_base;
    ++*successful;
    struct Snapshot success_state = take_snapshot(core);
    if (row->parameter == 0U) {
        restore_snapshot(core, &attempt_base);
        if (call_preserving(core, S58E_REMOVE_BAG_ITEM,
                            row->item, 1U, 0U, 0U) != 1U)
            goto fail_both;
        if (!s58e_prepare_capsule_ineligible_target(core))
            goto fail_both;
    }
    bool no_effect = s58e_offer_attempt(
        core, row->item, QOL_KEY_A, false);
    bool retained = s58e_bag_exact(core, row->item, 2U);
    if (!no_effect || !retained) {
        fprintf(stderr, "ability effectless item=%u path=%u bag=%u "
                "species=%" PRIu32 "\n", row->item, no_effect, retained,
                qol_get_party_data(core, QOL_PLAYER_PARTY,
                                   QOL_MON_DATA_SPECIES));
        goto fail_both;
    }
    ++*effectless;
    restore_snapshot(core, &success_state);
    free(attempt_base.bytes);
    free(success_state.bytes);
    return true;

fail_both:
    free(success_state.bytes);
fail_base:
    free(attempt_base.bytes);
    return false;
}

static bool s58e_mint_case(struct mCore *core, unsigned index,
                           const struct S58eCase *row,
                           unsigned *cancelled, unsigned *successful,
                           unsigned *effectless)
{
    uint32_t table = QOL_ITEM_TABLE + (uint32_t)row->item * QOL_ITEM_ROW_SIZE;
    if (read8(core, table + 21U) != row->parameter
        || !s58e_prepare_mint_target(core, row->parameter))
        return false;
    write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
    uint32_t personality = read32(core, QOL_PLAYER_PARTY);
    if (!call_preserving(core, QOL_ADD_BAG_ITEM, row->item, 3U, 0U, 0U))
        return false;
    struct Snapshot attempt_base = take_snapshot(core);
    if (!s58e_offer_attempt(core, row->item, QOL_KEY_B, true)
        || !s58e_bag_exact(core, row->item, 3U)
        || read32(core, QOL_PLAYER_PARTY) != personality
        || read8(core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET) != 0U)
        goto mint_fail_base;
    ++*cancelled;
    restore_snapshot(core, &attempt_base);
    if (!s58e_offer_attempt(core, row->item, QOL_KEY_A, true)
        || !s58e_bag_exact(core, row->item, 2U)
        || read32(core, QOL_PLAYER_PARTY) != personality
        || read8(core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET)
            != (uint8_t)(row->parameter + 1U)
        || !s58e_store_result(core, index))
        goto mint_fail_base;
    ++*successful;
    struct Snapshot success_state = take_snapshot(core);
    if (!s58e_offer_attempt(core, row->item, QOL_KEY_A, false)
        || !s58e_bag_exact(core, row->item, 2U)
        || read32(core, QOL_PLAYER_PARTY) != personality
        || read8(core, QOL_PLAYER_PARTY + S58E_NATURE_MINT_OFFSET)
            != (uint8_t)(row->parameter + 1U))
        goto mint_fail_both;
    ++*effectless;
    restore_snapshot(core, &success_state);
    free(attempt_base.bytes);
    free(success_state.bytes);
    return true;

mint_fail_both:
    free(success_state.bytes);
mint_fail_base:
    free(attempt_base.bytes);
    return false;
}

static bool s58e_callback_table(struct mCore *core)
{
    uint32_t candy = 0U, ev = 0U, ability = 0U, mint = 0U;
    for (unsigned index = 0U; index < S58E_EFFECT_COUNT; ++index) {
        const struct S58eCase *row = &s58e_cases[index];
        uint32_t callback = read32(core, QOL_ITEM_TABLE
            + (uint32_t)row->item * QOL_ITEM_ROW_SIZE
            + QOL_ITEM_CALLBACK_OFFSET);
        if (!s58e_rom_pointer(callback))
            return false;
        if (row->kind == S58E_CANDY) {
            if (candy != 0U && callback != candy)
                return false;
            candy = callback;
        } else if (row->kind == S58E_EV_RESET) {
            if (ev != 0U && callback != ev)
                return false;
            ev = callback;
        } else if (row->kind == S58E_ABILITY) {
            if (ability != 0U && callback != ability)
                return false;
            ability = callback;
        } else if (row->kind == S58E_MINT) {
            if (mint != 0U && callback != mint)
                return false;
            mint = callback;
        }
    }
    return candy != 0U && candy == ev && ability != 0U && mint != 0U;
}

static bool s58e_reload_record(struct mCore *core, unsigned index);

static bool s58e_sidecar_path(char *path, size_t size,
                              const char *base, unsigned index)
{
    int length = snprintf(path, size, "%s.qol-item-%02u.sav", base, index);
    return length > 0 && (size_t)length < size;
}

static bool s58e_phase1(const char *rom_path, const char *save_base,
                        uint32_t probe, uint32_t dispatch, bool *table,
                        unsigned *cancelled,
                        unsigned *successful, unsigned *effectless,
                        bool *saved,
                        bool normal[S58E_NORMAL_FAMILY_COUNT],
                        unsigned *normal_count,
                        bool bottle[S58E_BOTTLE_BOUNDARY_COUNT])
{
    (void)probe;
    *normal_count = s58e_normal_families(
        rom_path, save_base, normal, bottle);
    for (unsigned index = 0U; index < S58E_EFFECT_COUNT; ++index) {
        char save_path[4096];
        if (!s58e_sidecar_path(
                save_path, sizeof(save_path), save_base, index))
            return false;
        qol_initialize_save(save_path);
        struct mCore *core = qol_open(rom_path, save_path);
        qol_log_core = core;
        const struct S58eCase *row = &s58e_cases[index];
        bool ready = qol_run_field_trace(core) && s58e_callback_table(core);
        *table = *table && ready;
        qol_set_badges_through(core, 7U);
        (void)call_preserving(core, QOL_FLAG_SET, QOL_FLAG_HALL_OF_FAME,
                              0U, 0U, 0U);
        write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
        write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
        write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
        (void)call_preserving(core, QOL_SAVE_FINALIZE,
                              QOL_LEDGER, 0U, 0U, 0U);
        create_mon(core, QOL_PLAYER_PARTY,
                   S58E_SPECIES_BULBASAUR, S58E_LEVEL_EFFECT);
        write8(core, QOL_PLAYER_PARTY_COUNT, 1U);
        if (!ready || !s58e_enter_party(core)) {
            qol_close(core);
            return false;
        }
        bool passed = row->kind == S58E_CANDY
            ? s58e_candy_case(core, index, row, cancelled,
                              successful, effectless)
            : row->kind == S58E_EV_RESET
            ? s58e_ev_case(core, index, row, cancelled,
                           successful, effectless)
            : row->kind == S58E_HYPER
            ? s58e_hyper_case(core, dispatch, index, row, cancelled,
                              successful, effectless)
            : row->kind == S58E_ABILITY
            ? s58e_ability_case(core, index, row, cancelled,
                                successful, effectless)
            : s58e_mint_case(core, index, row, cancelled,
                             successful, effectless);
        if (!passed) {
            qol_close(core);
            return false;
        }
        if (call_preserving(core, QOL_TRY_SAVING_DATA,
                            0U, 0U, 0U, 0U) != 1U
            || call_preserving(core, QOL_TRY_SAVING_DATA,
                               0U, 0U, 0U, 0U) != 1U) {
            qol_close(core);
            return false;
        }
        qol_close(core);
    }
    *saved = true;
    bool passed = *cancelled == S58E_EFFECT_COUNT
        && *successful == S58E_EFFECT_COUNT
        && *effectless == S58E_EFFECT_COUNT
        && *normal_count == S58E_NORMAL_FAMILY_COUNT && *saved;
    return passed;
}

static bool s58e_reload_record(struct mCore *core, unsigned index)
{
    const struct S58eCase *row = &s58e_cases[index];
    uint32_t box = S58E_BOX_FIRST + index / S58E_BOX_CAPACITY;
    uint32_t slot = index % S58E_BOX_CAPACITY;
    uint32_t address = s58e_box_address(core, index);
    if (address == 0U || call_preserving(
            core, QOL_GET_BOX_MON_DATA_AT, box, slot,
            QOL_MON_DATA_SPECIES, 0U) == 0U)
        return false;
    if (row->kind == S58E_CANDY) {
        create_mon(core, QOL_PARTY_SCRATCH,
                   S58E_SPECIES_DITTO, S58E_LEVEL_EFFECT);
        return call_preserving(core, QOL_GET_BOX_MON_DATA_AT, box, slot,
                               QOL_MON_DATA_EXP, 0U)
            > qol_get_mon_data(core, QOL_PARTY_SCRATCH, QOL_MON_DATA_EXP);
    }
    if (row->kind == S58E_EV_RESET) {
        for (unsigned stat = 0U; stat < 6U; ++stat)
            if (call_preserving(core, QOL_GET_BOX_MON_DATA_AT, box, slot,
                                QOL_MON_DATA_HP_EV + stat, 0U)
                != (stat == row->parameter ? 0U : 40U))
                return false;
        return true;
    }
    if (row->kind == S58E_HYPER) {
        uint8_t mask = row->parameter == 6U ? 0x3FU : 0x01U;
        return (read8(core, address + S58E_HYPER_TRAIN_OFFSET) & mask) == mask;
    }
    if (row->kind == S58E_ABILITY) {
        if (row->parameter == 0U)
            return call_preserving(core, QOL_GET_BOX_MON_DATA_AT, box, slot,
                                   S58E_MON_DATA_ALT_ABILITY, 0U) == 1U;
        return (read8(core, address + S58E_BOX_FLAGS_OFFSET)
                & S58E_HIDDEN_ABILITY_MASK) != 0U;
    }
    return read8(core, address + S58E_NATURE_MINT_OFFSET)
        == (uint8_t)(row->parameter + 1U);
}

static bool s58e_reload_normal_bottle(
    const char *rom_path, const char *save_base, unsigned scenario,
    const struct S58eCase *row, bool *record, bool *bag)
{
    char save_path[4096];
    if (!s58e_ui_sidecar_path(save_path, sizeof(save_path),
                              save_base, scenario))
        return false;
    struct mCore *core = qol_open(rom_path, save_path);
    qol_log_core = core;
    run_key_frames(core, 0U, 240U);
    (void)call_preserving(core, S58E_SET_SAVE_BLOCK_POINTERS,
                          0U, 0U, 0U, 0U);
    bool loaded = call_preserving(
        core, QOL_LOAD_GAME_DATA, 0U, 0U, 0U, 0U) == 1U;
    if (loaded) {
        (void)call_preserving(core, S58E_SET_BAG_POCKETS_POINTERS,
                              0U, 0U, 0U, 0U);
        run_key_frames(core, 0U, 2U);
    }
    uint8_t mask = row->parameter == 6U ? 0x3FU : 0x01U;
    *record = loaded && qol_get_party_data(
        core, QOL_PLAYER_PARTY, QOL_MON_DATA_SPECIES) != 0U
        && (read8(core, QOL_PLAYER_PARTY + S58E_HYPER_TRAIN_OFFSET)
            & 0x3FU) == mask;
    *bag = loaded && s58e_saved_items_exact(core, row->item, 2U)
        && s58e_bag_exact(core, row->item, 2U);
    qol_close(core);
    return *record && *bag;
}

static bool s58e_reload(const char *rom_path, const char *save_base,
                        bool *table, unsigned *records, unsigned *bags,
                        bool ui_bottle[2], unsigned *ui_records,
                        unsigned *ui_bags)
{
    for (unsigned index = 0U; index < S58E_EFFECT_COUNT; ++index) {
        char save_path[4096];
        if (!s58e_sidecar_path(
                save_path, sizeof(save_path), save_base, index))
            return false;
        struct mCore *core = qol_open(rom_path, save_path);
        qol_log_core = core;
        run_key_frames(core, 0U, 240U);
        (void)call_preserving(core, S58E_SET_SAVE_BLOCK_POINTERS,
                              0U, 0U, 0U, 0U);
        bool loaded = call_preserving(
            core, QOL_LOAD_GAME_DATA, 0U, 0U, 0U, 0U) == 1U;
        if (loaded) {
            (void)call_preserving(core, S58E_SET_BAG_POCKETS_POINTERS,
                                  0U, 0U, 0U, 0U);
            run_key_frames(core, 0U, 2U);
        }
        *table = *table && s58e_callback_table(core);
        if (loaded && s58e_reload_record(core, index))
            ++*records;
        if (loaded
            && s58e_saved_items_exact(core, s58e_cases[index].item, 2U)
            && s58e_bag_exact(core, s58e_cases[index].item, 2U))
            ++*bags;
        qol_close(core);
    }
    bool silver_record = false, silver_bag = false;
    bool gold_record = false, gold_bag = false;
    ui_bottle[0] = s58e_reload_normal_bottle(
        rom_path, save_base, 4U, &s58e_cases[11U],
        &silver_record, &silver_bag);
    ui_bottle[1] = s58e_reload_normal_bottle(
        rom_path, save_base, 10U, &s58e_cases[12U],
        &gold_record, &gold_bag);
    *ui_records = (unsigned)silver_record + (unsigned)gold_record;
    *ui_bags = (unsigned)silver_bag + (unsigned)gold_bag;
    return *records == S58E_EFFECT_COUNT && *bags == S58E_EFFECT_COUNT
        && ui_bottle[0] && ui_bottle[1]
        && *ui_records == 2U && *ui_bags == 2U;
}

int main(int argc, char **argv)
{
    if (argc != 7 || (strcmp(argv[4], "phase1") != 0
                      && strcmp(argv[4], "reload") != 0
                      && strcmp(argv[4], "bottle") != 0)) {
        fprintf(stderr,
                "usage: %s ROM SAVE EXPECTED_SHA256 phase1|reload|bottle "
                "PROBE DISPATCH\n",
                argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[3]) != 64U || strcmp(rom_sha256, argv[3]) != 0) {
        fprintf(stderr, "stage58-item-effects: exact ROM SHA-256 mismatch\n");
        return 2;
    }
    uint32_t probe = qol_number(argv[5], "probe");
    uint32_t dispatch = qol_number(argv[6], "dispatch");
    if (!s58e_rom_pointer(probe) || !s58e_rom_pointer(dispatch))
        return 2;

    bool phase1 = strcmp(argv[4], "phase1") == 0;
    bool bottle_only = strcmp(argv[4], "bottle") == 0;
    log_problem_count = 0U;
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    bool table = true;
    unsigned cancelled = 0U, successful = 0U, effectless = 0U;
    unsigned records = 0U, bags = 0U;
    unsigned ui_records = 0U, ui_bags = 0U;
    bool normal[S58E_NORMAL_FAMILY_COUNT] = {false};
    bool bottle[S58E_BOTTLE_BOUNDARY_COUNT] = {false};
    bool reload_bottle[2] = {false};
    unsigned normal_count = 0U;
    bool saved = false;
    if (bottle_only) {
        bool bottle_pass = s58e_normal_bottle_family(
            argv[1], argv[2], bottle);
        printf("{\"status\":\"%s\",\"rom_sha256\":\"%s\","
               "\"boundaries\":[%s,%s,%s,%s,%s,%s,%s,%s,%s],"
               "\"warnings_errors\":%u}\n",
               bottle_pass && log_problem_count == 0U ? "PASS" : "FAIL",
               rom_sha256,
               bottle[0] ? "true" : "false",
               bottle[1] ? "true" : "false",
               bottle[2] ? "true" : "false",
               bottle[3] ? "true" : "false",
               bottle[4] ? "true" : "false",
               bottle[5] ? "true" : "false",
               bottle[6] ? "true" : "false",
               bottle[7] ? "true" : "false",
               bottle[8] ? "true" : "false",
               log_problem_count);
        return bottle_pass && log_problem_count == 0U ? 0 : 1;
    }
    bool dynamic = phase1
        ? s58e_phase1(argv[1], argv[2], probe, dispatch, &table,
                      &cancelled, &successful, &effectless, &saved,
                      normal, &normal_count, bottle)
        : s58e_reload(argv[1], argv[2], &table, &records, &bags,
                      reload_bottle, &ui_records, &ui_bags);
    bool passed = table && dynamic && log_problem_count == 0U;

    if (phase1) {
        printf("{\"schema_version\":1,"
               "\"task\":\"USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG\","
               "\"stage\":%u,\"phase\":\"phase1\","
               "\"status\":\"%s\",\"rom_sha256\":\"%s\",\"tests\":{"
               "\"live_item_table_callbacks\":%s,"
               "\"cancel_no_consume_36\":%s,"
               "\"effect_and_consume_36\":%s,"
               "\"ineligible_no_consume_36\":%s,"
               "\"normal_save_two_slots\":%s,"
               "\"normal_bag_ui_family_paths\":%s,"
               "\"normal_bag_ui_candy\":%s,"
               "\"normal_bag_ui_ev_reset\":%s,"
               "\"normal_bag_ui_bottle_cap\":%s,"
               "\"normal_bag_ui_bottle_silver_cancel\":%s,"
               "\"normal_bag_ui_bottle_silver_hp\":%s,"
               "\"normal_bag_ui_bottle_gold_all\":%s,"
               "\"normal_bag_ui_bottle_effectless_no_consume\":%s,"
               "\"normal_bag_ui_bottle_egg_no_consume\":%s,"
               "\"normal_bag_ui_bottle_locked_no_consume\":%s,"
               "\"normal_bag_ui_bottle_same_core_reopen\":%s,"
               "\"normal_bag_ui_bottle_vram_nonalias\":%s,"
               "\"normal_bag_ui_bottle_framebuffer_stable\":%s,"
               "\"normal_bag_ui_ability\":%s,"
               "\"normal_bag_ui_mint\":%s},\"coverage\":{"
               "\"effect_items\":36,\"exp_candy\":5,\"ev_reset\":6,"
               "\"hyper_training\":2,\"ability\":2,\"mints\":21,"
               "\"normal_bag_ui_families\":5,"
               "\"normal_bag_ui_bottle_boundaries\":9,"
               "\"host_result_writes\":0,\"process_contract\":2},"
               "\"counts\":{\"cancelled\":%u,\"successful\":%u,"
               "\"effectless\":%u,\"normal_bag_ui_families\":%u},"
               "\"warnings_errors\":%u}\n",
               S58E_STAGE, passed ? "PASS" : "FAIL", rom_sha256,
               table ? "true" : "false",
               cancelled == S58E_EFFECT_COUNT ? "true" : "false",
               successful == S58E_EFFECT_COUNT ? "true" : "false",
               effectless == S58E_EFFECT_COUNT ? "true" : "false",
               saved ? "true" : "false",
               normal_count == S58E_NORMAL_FAMILY_COUNT ? "true" : "false",
               normal[0] ? "true" : "false",
               normal[1] ? "true" : "false",
               normal[2] ? "true" : "false",
               bottle[0] ? "true" : "false",
               bottle[1] ? "true" : "false",
               bottle[2] ? "true" : "false",
               bottle[3] ? "true" : "false",
               bottle[4] ? "true" : "false",
               bottle[5] ? "true" : "false",
               bottle[6] ? "true" : "false",
               bottle[7] ? "true" : "false",
               bottle[8] ? "true" : "false",
               normal[3] ? "true" : "false",
               normal[4] ? "true" : "false",
               cancelled, successful, effectless, normal_count,
               log_problem_count);
    } else {
        printf("{\"schema_version\":1,"
               "\"task\":\"USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG\","
               "\"stage\":%u,\"phase\":\"reload\","
               "\"status\":\"%s\",\"rom_sha256\":\"%s\",\"tests\":{"
               "\"live_item_table_callbacks\":%s,"
               "\"fresh_core_effect_records_36\":%s,"
               "\"fresh_core_bag_counts_36\":%s,"
               "\"fresh_core_normal_bag_ui_bottle_silver_hp\":%s,"
               "\"fresh_core_normal_bag_ui_bottle_gold_all\":%s},"
               "\"coverage\":{"
               "\"effect_items\":36,\"host_result_writes\":0,"
               "\"normal_bag_ui_bottle_saved_cases\":2,"
               "\"process_contract\":2},\"counts\":{"
               "\"reload_records\":%u,\"reload_bags\":%u,"
               "\"normal_bag_ui_bottle_records\":%u,"
               "\"normal_bag_ui_bottle_bags\":%u},"
               "\"warnings_errors\":%u}\n",
               S58E_STAGE, passed ? "PASS" : "FAIL", rom_sha256,
               table ? "true" : "false",
               records == S58E_EFFECT_COUNT ? "true" : "false",
               bags == S58E_EFFECT_COUNT ? "true" : "false",
               reload_bottle[0] ? "true" : "false",
               reload_bottle[1] ? "true" : "false",
               records, bags, ui_records, ui_bags, log_problem_count);
    }
    return passed ? 0 : 1;
}
