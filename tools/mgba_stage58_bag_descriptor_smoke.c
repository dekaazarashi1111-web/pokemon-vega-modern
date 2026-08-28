/*
 * Stage58 full gBagPockets descriptor/key-rotation validation.
 *
 * The fixture writes one legal sentinel to each current SaveBlock1 pocket.
 * Product results are then owned by the unchanged stock save-block/key
 * lifecycle, normal Start-menu Save and normal Bag input.
 * In particular this runner never calls SetBagPocketsPointers: doing so just
 * before an assertion would hide the stale-descriptor defect under test.
 */
#define _POSIX_C_SOURCE 200809L
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include <mgba/flags.h>
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

enum {
    BD_STAGE = 58U,
    BD_POCKET_COUNT = 5U,
    BD_DESCRIPTOR_STRIDE = 8U,
    BD_FIELD_LOCK = 0x03000F9CU,
    BD_BAG_MENU_STATE = 0x0203AC74U,
    BD_STARTMENU_SAVE = 4U,
    BD_SAVE_LOCATION_OFFSET = 4U,
    BD_FIELD_WAIT_FRAMES = 2400U,
    BD_IRQ_FRAMES = 8U,
};

static const uint16_t BD_SENTINEL_ITEMS[BD_POCKET_COUNT] = {
    19U, 48U, 2U, 289U, 133U,
};
static const uint16_t BD_SENTINEL_QUANTITIES[BD_POCKET_COUNT] = {
    11U, 1U, 13U, 2U, 15U,
};

struct BdDescriptor {
    uint32_t offset;
    uint8_t capacity;
};

struct BdContract {
    uint32_t move_save_blocks;
    uint32_t callback_restore_site;
    uint32_t apply_all_call_site;
    uint32_t apply_all;
    uint32_t bag_encryption_call_site;
    uint32_t bag_encryption;
    uint32_t set_bag_pockets;
    uint32_t save1_slot;
    uint32_t save2_slot;
    uint32_t bag_pockets;
    uint32_t encryption_key_offset;
    uint32_t expected_previous_save1;
    uint32_t expected_previous_key;
    uint32_t expected_field_callback;
    struct BdDescriptor descriptor[BD_POCKET_COUNT];
};

struct BdLifecycle {
    bool stock_rom_call_graph_exact;
    bool descriptors_exact_before;
    bool descriptors_exact_after;
    bool sentinels_exact_before;
    bool sentinels_exact_after;
    bool savedata_changed;
    uint32_t save1_before;
    uint32_t save1_after;
    uint32_t key_before;
    uint32_t key_after;
    uint16_t raw_before[BD_POCKET_COUNT];
    uint16_t raw_after[BD_POCKET_COUNT];
    uint32_t pointer_before[BD_POCKET_COUNT];
    uint32_t pointer_after[BD_POCKET_COUNT];
    uint8_t capacity_before[BD_POCKET_COUNT];
    uint8_t capacity_after[BD_POCKET_COUNT];
};

static bool bd_ewram(uint32_t value)
{
    return value >= 0x02000000U && value < 0x02040000U;
}

static uint32_t bd_thumb(uint32_t value)
{
    return value & ~1U;
}

static bool bd_descriptor_exact(struct mCore *core,
                                const struct BdContract *contract,
                                unsigned pocket)
{
    uint32_t save1 = read32(core, contract->save1_slot);
    uint32_t row = contract->bag_pockets
        + pocket * BD_DESCRIPTOR_STRIDE;
    return pocket < BD_POCKET_COUNT && bd_ewram(save1)
        && read32(core, row) == save1 + contract->descriptor[pocket].offset
        && read8(core, row + 4U) == contract->descriptor[pocket].capacity;
}

static bool bd_descriptors_exact(struct mCore *core,
                                 const struct BdContract *contract)
{
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket)
        if (!bd_descriptor_exact(core, contract, pocket))
            return false;
    return true;
}

static void bd_capture_descriptors(struct mCore *core,
                                   const struct BdContract *contract,
                                   uint32_t pointers[BD_POCKET_COUNT],
                                   uint8_t capacities[BD_POCKET_COUNT])
{
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        uint32_t row = contract->bag_pockets
            + pocket * BD_DESCRIPTOR_STRIDE;
        pointers[pocket] = read32(core, row);
        capacities[pocket] = read8(core, row + 4U);
    }
}

static uint32_t bd_key(struct mCore *core,
                       const struct BdContract *contract)
{
    uint32_t save2 = read32(core, contract->save2_slot);
    if (!bd_ewram(save2))
        return 0U;
    return read32(core, save2 + contract->encryption_key_offset);
}

static bool bd_find_sentinel(struct mCore *core,
                             const struct BdContract *contract,
                             unsigned pocket, uint16_t *raw_out)
{
    uint32_t save1 = read32(core, contract->save1_slot);
    if (pocket >= BD_POCKET_COUNT || !bd_ewram(save1))
        return false;
    uint32_t slots = save1 + contract->descriptor[pocket].offset;
    unsigned matches = 0U;
    uint16_t raw = 0U;
    for (unsigned slot = 0U;
         slot < contract->descriptor[pocket].capacity; ++slot) {
        uint32_t row = slots + slot * 4U;
        if (read16(core, row) == BD_SENTINEL_ITEMS[pocket]) {
            ++matches;
            raw = read16(core, row + 2U);
        }
    }
    if (raw_out != NULL)
        *raw_out = raw;
    return matches == 1U
        && (uint16_t)(raw ^ (uint16_t)bd_key(core, contract))
            == BD_SENTINEL_QUANTITIES[pocket];
}

static bool bd_sentinels_exact(struct mCore *core,
                               const struct BdContract *contract)
{
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket)
        if (!bd_find_sentinel(core, contract, pocket, NULL))
            return false;
    return true;
}

static bool bd_seed_sentinels(struct mCore *core,
                              const struct BdContract *contract)
{
    if (!bd_descriptors_exact(core, contract))
        return false;
    uint32_t save1 = read32(core, contract->save1_slot);
    uint16_t key = (uint16_t)bd_key(core, contract);
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        uint32_t slots = save1 + contract->descriptor[pocket].offset;
        uint32_t target = 0U;
        for (unsigned slot = 0U;
             slot < contract->descriptor[pocket].capacity; ++slot) {
            uint32_t row = slots + slot * 4U;
            uint16_t item = read16(core, row);
            if (item == BD_SENTINEL_ITEMS[pocket]) {
                target = row;
                break;
            }
            if (target == 0U && item == 0U)
                target = row;
        }
        if (target == 0U)
            return false;
        write16(core, target, BD_SENTINEL_ITEMS[pocket]);
        write16(core, target + 2U,
                (uint16_t)(BD_SENTINEL_QUANTITIES[pocket] ^ key));
    }
    return bd_sentinels_exact(core, contract);
}

static void bd_repair_wait_pc(struct mCore *core)
{
    uint32_t pc = (uint32_t)read_register(core, "pc");
    if (pc >= 0x080008B8U && pc <= 0x080008C0U) {
        write_register(core, "pc", 0x080008AAU);
        if ((uint32_t)read_register(core, "pc") != 0x080008ACU)
            qol_die("wait-loop scheduler PC repair failed");
    }
}

static bool bd_field(struct mCore *core,
                     const struct BdContract *contract,
                     uint32_t field_callback)
{
    return read32(core, BATTLE_CORE_MAIN_CALLBACK2) == field_callback
        && field_callback >= 0x08000000U && field_callback < 0x0A000000U
        && read8(core, BD_FIELD_LOCK) == 0U
        && bd_ewram(read32(core, contract->save1_slot))
        && bd_ewram(read32(core, contract->save2_slot));
}

static bool bd_irq_boundary(struct mCore *core,
                            const struct BdContract *contract,
                            uint32_t field_callback)
{
    uint32_t before = core->frameCounter(core);
    run_key_frames(core, 0U, BD_IRQ_FRAMES);
    return core->frameCounter(core) >= before + BD_IRQ_FRAMES
        && bd_field(core, contract, field_callback)
        && bd_descriptors_exact(core, contract)
        && bd_sentinels_exact(core, contract);
}

static uint32_t bd_thumb_bl_target(struct mCore *core, uint32_t site)
{
    uint16_t high = read16(core, site);
    uint16_t low = read16(core, site + 2U);
    if ((high & 0xF800U) != 0xF000U || (low & 0xF800U) != 0xF800U)
        return 0U;
    int32_t offset = (int32_t)(((uint32_t)(high & 0x07FFU) << 12)
                               | ((uint32_t)(low & 0x07FFU) << 1));
    if (offset & 0x00400000)
        offset |= (int32_t)0xFF800000U;
    return (uint32_t)((int32_t)(site + 4U) + offset);
}

static bool bd_stock_rom_contract(struct mCore *core,
                                  const struct BdContract *contract)
{
    return bd_thumb_bl_target(core, contract->apply_all_call_site)
            == bd_thumb(contract->apply_all)
        && bd_thumb_bl_target(core, contract->bag_encryption_call_site)
            == bd_thumb(contract->bag_encryption)
        && read16(core, contract->move_save_blocks & ~1U) == 0xB5F0U
        && read16(core, contract->callback_restore_site) == 0x9801U;
}

static bool bd_wait_bag(struct mCore *core,
                        const struct BdContract *contract,
                        uint32_t field_callback)
{
    uint32_t candidate = 0U;
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < BD_FIELD_WAIT_FRAMES; ++frame) {
        bd_repair_wait_pc(core);
        run_key_frames(core, 0U, 1U);
        uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (callback != field_callback
            && callback >= 0x08000000U && callback < 0x0A000000U
            && read8(core, BD_FIELD_LOCK) != 0U
            && bd_descriptors_exact(core, contract)
            && bd_sentinels_exact(core, contract)) {
            if (callback == candidate)
                ++stable;
            else {
                candidate = callback;
                stable = 1U;
            }
            if (stable >= 60U)
                return true;
        } else {
            candidate = 0U;
            stable = 0U;
        }
    }
    return false;
}

static bool bd_open_bag(struct mCore *core,
                        const struct BdContract *contract,
                        uint32_t field_callback)
{
    if (!bd_field(core, contract, field_callback))
        return false;
    bd_repair_wait_pc(core);
    run_key_frames(core, 0U, 2U);
    qol_press(core, QOL_KEY_START, 90U);
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count)
        return false;
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index)
        if (read8(core, QOL_START_MENU_ORDER + index) == 2U) {
            target = index;
            break;
        }
    if (target >= count)
        return false;
    while (cursor != target) {
        qol_press(core, QOL_KEY_DOWN, 8U);
        uint8_t next = read8(core, QOL_START_MENU_CURSOR);
        if (next == cursor)
            return false;
        cursor = next;
    }
    run_key_frames(core, QOL_KEY_A, 2U);
    return bd_wait_bag(core, contract, field_callback);
}

static bool bd_close_bag(struct mCore *core,
                         const struct BdContract *contract,
                         uint32_t field_callback)
{
    for (unsigned pulse = 0U; pulse < 12U; ++pulse) {
        qol_press(core, QOL_KEY_B, 60U);
        if (bd_field(core, contract, field_callback))
            return true;
    }
    return false;
}

static bool bd_same_core_bag_reentry(struct mCore *core,
                                     const struct BdContract *contract,
                                     uint32_t field_callback)
{
    for (unsigned pass = 0U; pass < 2U; ++pass) {
        bool opened = bd_open_bag(core, contract, field_callback);
        bool descriptors = opened && bd_descriptors_exact(core, contract);
        bool sentinels = descriptors && bd_sentinels_exact(core, contract);
        bool closed = sentinels
            && bd_close_bag(core, contract, field_callback);
        bool irq = closed && bd_irq_boundary(
            core, contract, field_callback);
        if (!opened || !descriptors || !sentinels || !closed || !irq) {
            fprintf(stderr, "Bag reentry pass=%u open=%u desc=%u sentinel=%u "
                    "close=%u irq=%u pc=%08" PRIx32 " cb=%08" PRIx32
                    " lock=%u count=%u cursor=%u bag_state=%u\n", pass,
                    opened ? 1U : 0U, descriptors ? 1U : 0U,
                    sentinels ? 1U : 0U, closed ? 1U : 0U,
                    irq ? 1U : 0U, (uint32_t)read_register(core, "pc"),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, BD_FIELD_LOCK),
                    read8(core, QOL_START_MENU_COUNT),
                    read8(core, QOL_START_MENU_CURSOR),
                    read8(core, BD_BAG_MENU_STATE));
            return false;
        }
    }
    return true;
}

static bool bd_savedata_hash(struct mCore *core, uint64_t *hash_out)
{
    void *sram = NULL;
    size_t size = core->savedataClone(core, &sram);
    if (sram == NULL || size != QOL_SAVE_SIZE) {
        free(sram);
        return false;
    }
    uint64_t hash = UINT64_C(14695981039346656037);
    const uint8_t *bytes = sram;
    for (size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    free(sram);
    *hash_out = hash;
    return true;
}

static bool bd_normal_save(struct mCore *core,
                           const struct BdContract *contract,
                           uint32_t field_callback,
                           uint32_t *key_before_out,
                           uint32_t *key_after_out,
                           struct BdLifecycle *lifecycle)
{
    /* No SetBagPocketsPointers call is allowed here. */
    if (!bd_field(core, contract, field_callback)
        || !bd_descriptors_exact(core, contract)
        || !bd_sentinels_exact(core, contract))
        return false;
    uint64_t before = 0U;
    if (!bd_savedata_hash(core, &before))
        return false;
    *key_before_out = bd_key(core, contract);
    lifecycle->stock_rom_call_graph_exact =
        bd_stock_rom_contract(core, contract);
    lifecycle->save1_before = read32(core, contract->save1_slot);
    lifecycle->key_before = *key_before_out;
    lifecycle->descriptors_exact_before =
        bd_descriptors_exact(core, contract);
    bd_capture_descriptors(core, contract, lifecycle->pointer_before,
                           lifecycle->capacity_before);
    lifecycle->sentinels_exact_before = true;
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket)
        lifecycle->sentinels_exact_before = bd_find_sentinel(
            core, contract, pocket, &lifecycle->raw_before[pocket])
            && lifecycle->sentinels_exact_before;
    qol_press(core, QOL_KEY_START, 90U);
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count) {
        fprintf(stderr, "stock save start menu count=%u cursor=%u cb=%08" PRIx32
                "\n", count, cursor,
                read32(core, QOL_START_MENU_CALLBACK));
        return false;
    }
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index)
        if (read8(core, QOL_START_MENU_ORDER + index)
                == BD_STARTMENU_SAVE) {
            target = index;
            break;
        }
    if (target >= count) {
        fprintf(stderr, "stock save menu action missing count=%u\n", count);
        return false;
    }
    while (cursor != target) {
        qol_press(core, QOL_KEY_DOWN, 30U);
        uint8_t next = read8(core, QOL_START_MENU_CURSOR);
        if (next == cursor) {
            fprintf(stderr, "stock save cursor stuck=%u target=%u\n",
                    cursor, target);
            return false;
        }
        cursor = next;
    }
    qol_press(core, QOL_KEY_A, 120U);
    for (unsigned prompt = 0U; prompt < 32U; ++prompt) {
        if (bd_field(core, contract, field_callback)
            && lifecycle->stock_rom_call_graph_exact
            && lifecycle->descriptors_exact_before
            && lifecycle->sentinels_exact_before
            && bd_descriptors_exact(core, contract)
            && bd_sentinels_exact(core, contract)) {
            uint64_t current = 0U;
            if (!bd_savedata_hash(core, &current) || current == before)
                return false;
            *key_after_out = bd_key(core, contract);
            lifecycle->savedata_changed = true;
            lifecycle->save1_after = read32(core, contract->save1_slot);
            lifecycle->key_after = *key_after_out;
            lifecycle->descriptors_exact_after =
                bd_descriptors_exact(core, contract);
            bd_capture_descriptors(core, contract,
                                   lifecycle->pointer_after,
                                   lifecycle->capacity_after);
            lifecycle->sentinels_exact_after = true;
            for (unsigned pocket = 0U;
                 pocket < BD_POCKET_COUNT; ++pocket)
                lifecycle->sentinels_exact_after = bd_find_sentinel(
                    core, contract, pocket,
                    &lifecycle->raw_after[pocket])
                    && lifecycle->sentinels_exact_after;
            return lifecycle->descriptors_exact_after
                && lifecycle->sentinels_exact_after
                && bd_irq_boundary(core, contract, field_callback);
        }
        bd_repair_wait_pc(core);
        qol_press(core, QOL_KEY_A, 180U);
    }
    fprintf(stderr, "stock save timeout pc=%08" PRIx32 " cb=%08" PRIx32
            " lock=%u start=%08" PRIx32 " key=%08" PRIx32
            " graph=%u descriptor_before=%u sentinel_before=%u\n",
            (uint32_t)read_register(core, "pc"),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, BD_FIELD_LOCK),
            read32(core, QOL_START_MENU_CALLBACK), bd_key(core, contract),
            lifecycle->stock_rom_call_graph_exact ? 1U : 0U,
            lifecycle->descriptors_exact_before ? 1U : 0U,
            lifecycle->sentinels_exact_before ? 1U : 0U);
    return false;
}

static bool bd_continue(struct mCore *core,
                        const struct BdContract *contract,
                        uint32_t *field_callback_out)
{
    run_key_frames(core, 0U, 900U);
    for (unsigned pulse = 0U; pulse < 16U; ++pulse) {
        qol_press(core, pulse == 0U ? QOL_KEY_START : QOL_KEY_A, 180U);
        uint32_t save1 = read32(core, contract->save1_slot);
            uint32_t callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        if (bd_ewram(save1) && callback >= 0x08000000U
            && callback < 0x0A000000U
            && (contract->expected_field_callback == 0U
                || callback == contract->expected_field_callback)
            && read8(core, save1 + BD_SAVE_LOCATION_OFFSET) == 4U
            && read8(core, save1 + BD_SAVE_LOCATION_OFFSET + 1U) == 0U
            && read8(core, BD_FIELD_LOCK) == 0U) {
            run_key_frames(core, 0U, 300U);
            if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) == callback
                && read8(core, BD_FIELD_LOCK) == 0U) {
                *field_callback_out = callback;
                return true;
            }
        }
        qol_press(core, QOL_KEY_B, 60U);
    }
    return false;
}

static void bd_print_descriptors(struct mCore *core,
                                 const struct BdContract *contract)
{
    uint32_t save1 = read32(core, contract->save1_slot);
    putchar('[');
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        uint32_t row = contract->bag_pockets
            + pocket * BD_DESCRIPTOR_STRIDE;
        uint32_t actual_pointer = read32(core, row);
        uint8_t actual_capacity = read8(core, row + 4U);
        if (pocket != 0U)
            putchar(',');
        printf("{\"pocket\":%u,\"save1\":%" PRIu32 ","
               "\"expected_pointer\":%" PRIu32 ","
               "\"actual_pointer\":%" PRIu32 ","
               "\"expected_capacity\":%u,\"actual_capacity\":%u,"
               "\"exact\":%s}", pocket + 1U, save1,
               save1 + contract->descriptor[pocket].offset,
               actual_pointer, contract->descriptor[pocket].capacity,
               actual_capacity,
               actual_pointer == save1 + contract->descriptor[pocket].offset
                   && actual_capacity == contract->descriptor[pocket].capacity
                   ? "true" : "false");
    }
    putchar(']');
}

static void bd_print_u32_array(const uint32_t values[BD_POCKET_COUNT])
{
    putchar('[');
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        if (pocket != 0U)
            putchar(',');
        printf("%" PRIu32, values[pocket]);
    }
    putchar(']');
}

static void bd_print_u16_array(const uint16_t values[BD_POCKET_COUNT])
{
    putchar('[');
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        if (pocket != 0U)
            putchar(',');
        printf("%u", values[pocket]);
    }
    putchar(']');
}

static void bd_print_u8_array(const uint8_t values[BD_POCKET_COUNT])
{
    putchar('[');
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        if (pocket != 0U)
            putchar(',');
        printf("%u", values[pocket]);
    }
    putchar(']');
}

static void bd_print_lifecycle(const struct BdLifecycle *lifecycle)
{
    printf("{\"stock_rom_call_graph_exact\":%s,"
           "\"descriptor_before_exact\":%s,"
           "\"descriptor_after_exact\":%s,"
           "\"sentinel_before_exact\":%s,"
           "\"sentinel_after_exact\":%s,"
           "\"savedata_changed\":%s,"
           "\"save1_before\":%" PRIu32 ","
           "\"save1_after\":%" PRIu32 ","
           "\"key_before\":%" PRIu32 ","
           "\"key_after\":%" PRIu32 ",\"raw_before\":",
           lifecycle->stock_rom_call_graph_exact ? "true" : "false",
           lifecycle->descriptors_exact_before ? "true" : "false",
           lifecycle->descriptors_exact_after ? "true" : "false",
           lifecycle->sentinels_exact_before ? "true" : "false",
           lifecycle->sentinels_exact_after ? "true" : "false",
           lifecycle->savedata_changed ? "true" : "false",
           lifecycle->save1_before, lifecycle->save1_after,
           lifecycle->key_before, lifecycle->key_after);
    bd_print_u16_array(lifecycle->raw_before);
    printf(",\"raw_after\":");
    bd_print_u16_array(lifecycle->raw_after);
    printf(",\"pointer_before\":");
    bd_print_u32_array(lifecycle->pointer_before);
    printf(",\"pointer_after\":");
    bd_print_u32_array(lifecycle->pointer_after);
    printf(",\"capacity_before\":");
    bd_print_u8_array(lifecycle->capacity_before);
    printf(",\"capacity_after\":");
    bd_print_u8_array(lifecycle->capacity_after);
    putchar('}');
}

static void bd_print_sentinels(struct mCore *core,
                              const struct BdContract *contract)
{
    putchar('[');
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        uint16_t raw = 0U;
        bool exact = bd_find_sentinel(core, contract, pocket, &raw);
        if (pocket != 0U)
            putchar(',');
        printf("{\"pocket\":%u,\"item\":%u,\"quantity\":%u,"
               "\"raw\":%u,\"exact\":%s}", pocket + 1U,
               BD_SENTINEL_ITEMS[pocket], BD_SENTINEL_QUANTITIES[pocket],
               raw, exact ? "true" : "false");
    }
    putchar(']');
}

static bool bd_contract_valid(const struct BdContract *contract)
{
    if (contract->move_save_blocks < 0x08000000U
        || contract->callback_restore_site < 0x08000000U
        || contract->apply_all_call_site < 0x08000000U
        || contract->apply_all < 0x08000000U
        || contract->bag_encryption_call_site < 0x08000000U
        || contract->bag_encryption < 0x08000000U
        || contract->set_bag_pockets < 0x08000000U
        || contract->save1_slot < 0x03000000U
        || contract->save2_slot < 0x03000000U
        || contract->bag_pockets < 0x02000000U)
        return false;
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket)
        if (contract->descriptor[pocket].capacity == 0U
            || contract->descriptor[pocket].offset == 0U)
            return false;
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 29) {
        fprintf(stderr, "usage: %s ROM SAVE SHA phase1|reload "
                "MOVE CALLBACK_SITE APPLY_SITE APPLY_ALL BAG_SITE BAG_OWNER "
                "SET_BAG SAVE1_SLOT SAVE2_SLOT "
                "BAG_POCKETS KEY_OFFSET PREVIOUS_SAVE1 PREVIOUS_KEY FIELD_CB "
                "5xOFFSET/CAPACITY\n", argv[0]);
        return 2;
    }
    bool phase1 = strcmp(argv[4], "phase1") == 0;
    if (!phase1 && strcmp(argv[4], "reload") != 0)
        return 2;
    char digest[65];
    sha256_file(argv[1], digest);
    if (strlen(argv[3]) != 64U || strcmp(digest, argv[3]) != 0)
        qol_die("ROM SHA-256 identity invalid");

    struct BdContract contract = {0};
    unsigned arg = 5U;
    contract.move_save_blocks = qol_number(argv[arg++], "move_save_blocks");
    contract.callback_restore_site =
        qol_number(argv[arg++], "callback_restore_site");
    contract.apply_all_call_site =
        qol_number(argv[arg++], "apply_all_call_site");
    contract.apply_all = qol_number(argv[arg++], "apply_all");
    contract.bag_encryption_call_site =
        qol_number(argv[arg++], "bag_encryption_call_site");
    contract.bag_encryption = qol_number(argv[arg++], "bag_encryption");
    contract.set_bag_pockets = qol_number(argv[arg++], "set_bag_pockets");
    contract.save1_slot = qol_number(argv[arg++], "save1_slot");
    contract.save2_slot = qol_number(argv[arg++], "save2_slot");
    contract.bag_pockets = qol_number(argv[arg++], "bag_pockets");
    contract.encryption_key_offset = qol_number(argv[arg++], "key_offset");
    contract.expected_previous_save1 =
        qol_number(argv[arg++], "expected_previous_save1");
    contract.expected_previous_key =
        qol_number(argv[arg++], "expected_previous_key");
    contract.expected_field_callback =
        qol_number(argv[arg++], "expected_field_callback");
    for (unsigned pocket = 0U; pocket < BD_POCKET_COUNT; ++pocket) {
        contract.descriptor[pocket].offset =
            qol_number(argv[arg++], "descriptor_offset");
        uint32_t capacity = qol_number(argv[arg++], "descriptor_capacity");
        if (capacity > UINT8_MAX)
            qol_die("descriptor capacity out of range");
        contract.descriptor[pocket].capacity = (uint8_t)capacity;
    }
    if (arg != (unsigned)argc || !bd_contract_valid(&contract))
        qol_die("metadata contract invalid");

    if (phase1)
        qol_initialize_save(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;

    bool passed = false;
    bool natural_field = false;
    bool descriptors = false;
    bool seeded = false;
    bool stock_lifecycle = false;
    bool lifecycle_descriptors = false;
    bool lifecycle_sentinels = false;
    bool irq = false;
    bool bag_reentry = false;
    bool same_core_relocation = false;
    bool normal_save = false;
    bool fresh_continue = false;
    bool fresh_relocation = false;
    uint32_t field_callback = 0U;
    uint32_t normal_key_before = 0U, normal_key_after = 0U;
    uint32_t fresh_entry_save1 = 0U, fresh_entry_key = 0U;
    struct BdLifecycle lifecycle = {0};

    if (phase1) {
        natural_field = qol_run_field_trace(core);
        field_callback = read32(core, BATTLE_CORE_MAIN_CALLBACK2);
        descriptors = natural_field && bd_descriptors_exact(core, &contract);
        seeded = descriptors && bd_seed_sentinels(core, &contract);
        normal_save = seeded && bd_normal_save(
            core, &contract, field_callback,
            &normal_key_before, &normal_key_after, &lifecycle);
        stock_lifecycle = normal_save
            && lifecycle.stock_rom_call_graph_exact
            && lifecycle.savedata_changed;
        lifecycle_descriptors = stock_lifecycle
            && lifecycle.descriptors_exact_before
            && lifecycle.descriptors_exact_after
            && bd_descriptors_exact(core, &contract);
        lifecycle_sentinels = stock_lifecycle
            && lifecycle.sentinels_exact_before
            && lifecycle.sentinels_exact_after
            && bd_sentinels_exact(core, &contract);
        irq = lifecycle_sentinels && bd_irq_boundary(
            core, &contract, field_callback);
        bag_reentry = irq && bd_same_core_bag_reentry(
            core, &contract, field_callback);
        same_core_relocation = bag_reentry
            && (read32(core, contract.save1_slot) != lifecycle.save1_after
                || bd_key(core, &contract) != lifecycle.key_after);
        passed = natural_field && descriptors && seeded && normal_save
            && stock_lifecycle && lifecycle_descriptors
            && lifecycle_sentinels && irq && bag_reentry
            && same_core_relocation
            && log_problem_count == 0U;
    } else {
        fresh_continue = bd_continue(core, &contract, &field_callback);
        fresh_entry_save1 = read32(core, contract.save1_slot);
        fresh_entry_key = bd_key(core, &contract);
        fresh_relocation = fresh_continue
            && contract.expected_previous_save1 != 0U
            && contract.expected_previous_key != 0U
            && (read32(core, contract.save1_slot)
                    != contract.expected_previous_save1
                || bd_key(core, &contract) != contract.expected_previous_key);
        seeded = fresh_continue && bd_sentinels_exact(core, &contract);
        bag_reentry = seeded && bd_same_core_bag_reentry(
            core, &contract, field_callback);
        descriptors = bag_reentry && bd_descriptors_exact(core, &contract);
        irq = bag_reentry && bd_irq_boundary(
            core, &contract, field_callback);
        passed = fresh_continue && fresh_relocation && descriptors
            && seeded && bag_reentry && irq && log_problem_count == 0U;
    }

    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG\","
           "\"stage\":%u,\"phase\":\"%s\",\"status\":\"%s\","
           "\"rom_sha256\":\"%s\",\"tests\":{",
           BD_STAGE, argv[4], passed ? "PASS" : "FAIL", digest);
    if (phase1) {
        printf("\"natural_field_descriptor_owner\":%s,"
               "\"five_pocket_sentinels_seeded\":%s,"
               "\"stock_normal_save_persistence_observed\":%s,"
               "\"all_five_descriptors_exact_across_lifecycle\":%s,"
               "\"all_five_encrypted_quantities_preserved\":%s,"
               "\"post_save_irq_no_reset\":%s,"
               "\"same_core_bag_reentry\":%s,"
               "\"same_core_stock_saveblock_relocation_observed\":%s,"
               "\"normal_start_menu_save_persisted\":%s",
               descriptors ? "true" : "false", seeded ? "true" : "false",
               stock_lifecycle ? "true" : "false",
               lifecycle_descriptors ? "true" : "false",
               lifecycle_sentinels ? "true" : "false",
               irq ? "true" : "false",
               bag_reentry ? "true" : "false",
               same_core_relocation ? "true" : "false",
               normal_save ? "true" : "false");
    } else {
        printf("\"fresh_process_continue\":%s,"
               "\"fresh_process_stock_saveblock_relocation_observed\":%s,"
               "\"fresh_process_five_descriptors_exact\":%s,"
               "\"fresh_process_five_sentinels_exact\":%s,"
               "\"fresh_process_same_core_bag_reentry\":%s,"
               "\"fresh_process_irq_no_reset\":%s",
               fresh_continue ? "true" : "false",
               fresh_relocation ? "true" : "false",
               descriptors ? "true" : "false", seeded ? "true" : "false",
               bag_reentry ? "true" : "false", irq ? "true" : "false");
    }
    printf("},\"coverage\":{\"bag_pockets\":5,"
           "\"descriptor_pointer_fields\":5,"
           "\"descriptor_capacity_fields\":5,"
           "\"stock_save_lifecycles\":%u,\"same_core_bag_reentries\":%u,"
           "\"process_contract\":2},"
           "\"evidence\":{"
           "\"current_key\":%" PRIu32 ","
           "\"current_save1\":%" PRIu32 ","
           "\"expected_previous_save1\":%" PRIu32 ","
           "\"expected_previous_key\":%" PRIu32 ","
           "\"field_callback\":%" PRIu32 ","
           "\"fresh_entry_save1\":%" PRIu32 ","
           "\"fresh_entry_key\":%" PRIu32 ","
           "\"normal_key_before\":%u,\"normal_key_after\":%u,"
           "\"descriptors\":",
           phase1 ? 1U : 0U, 2U,
           bd_key(core, &contract), read32(core, contract.save1_slot),
           contract.expected_previous_save1,
           contract.expected_previous_key,
           field_callback,
           fresh_entry_save1, fresh_entry_key,
           normal_key_before, normal_key_after);
    bd_print_descriptors(core, &contract);
    printf(",\"sentinels\":");
    bd_print_sentinels(core, &contract);
    printf(",\"stock_lifecycle\":");
    if (phase1)
        bd_print_lifecycle(&lifecycle);
    else
        printf("null");
    printf("},\"warnings_errors\":%u}\n", log_problem_count);
    qol_close(core);
    return passed ? 0 : 1;
}
