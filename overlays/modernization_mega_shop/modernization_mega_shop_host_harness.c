/* Host failure-injection harness for the exact Mega shop transaction code. */

#define MODERNIZATION_MEGA_SHOP_HOST_TEST 1
#include "modernization_mega_shop.c"

#include <stdio.h>
#include <string.h>

enum {
    HOST_ITEM_CAPACITY = 2048,
    HOST_FLAG_CAPACITY = 0x1900
};

u8 gMegaShopHostVolatileState[128];
volatile u16 gMegaShopHostSpecialResult;
volatile u16 gMegaShopHostSpecialVar8004;
struct Task gMegaShopHostTasks[MEGA_SHOP_NUM_TASKS];
VegaModernSaveData gMegaShopHostModernSave;
VegaModernSaveData gMegaShopHostFlashRead;

static VegaModernSaveData sDurableLedger;
static u16 sBag[HOST_ITEM_CAPACITY];
static u16 sDurableBag[HOST_ITEM_CAPACITY];
static u8 sFlags[HOST_FLAG_CAPACITY];
static u8 sDurableFlags[HOST_FLAG_CAPACITY];
static unsigned sStandardCalls;
static unsigned sSectorCalls;
static unsigned sFailStandardCall;
static unsigned sFailSectorCall;
static u8 sForceBagFull;
static u8 sSectorValid;
static unsigned sAssertions;
static unsigned sFailures;

#define EXPECT(condition) do { \
    ++sAssertions; \
    if (!(condition)) { \
        ++sFailures; \
        fprintf(stderr, "FAIL line=%d condition=%s\n", __LINE__, #condition); \
    } \
} while (0)

u8 MegaShopHost_FlagSet(u16 flag)
{
    if (flag >= HOST_FLAG_CAPACITY)
        return 0u;
    sFlags[flag] = 1u;
    return 1u;
}

u8 MegaShopHost_FlagClear(u16 flag)
{
    if (flag >= HOST_FLAG_CAPACITY)
        return 0u;
    sFlags[flag] = 0u;
    return 1u;
}

u8 MegaShopHost_FlagGet(u16 flag)
{
    return flag < HOST_FLAG_CAPACITY ? sFlags[flag] : 0u;
}

u8 MegaShopHost_CheckBagHasItem(u16 item, u16 quantity)
{
    return (u8)(item < HOST_ITEM_CAPACITY && sBag[item] >= quantity);
}

u8 MegaShopHost_AddBagItem(u16 item, u16 quantity)
{
    if (sForceBagFull || item >= HOST_ITEM_CAPACITY
            || quantity == 0u || sBag[item] > (u16)(999u - quantity))
        return 0u;
    sBag[item] = (u16)(sBag[item] + quantity);
    return 1u;
}

u8 MegaShopHost_RemoveBagItem(u16 item, u16 quantity)
{
    if (item >= HOST_ITEM_CAPACITY || quantity == 0u || sBag[item] < quantity)
        return 0u;
    sBag[item] = (u16)(sBag[item] - quantity);
    return 1u;
}

u8 MegaShopHost_TryWriteSector(u16 sector, const void *source)
{
    ++sSectorCalls;
    if (sector != MEGA_SHOP_SAVE_SECTOR
            || (sFailSectorCall != 0u && sSectorCalls == sFailSectorCall))
        return 0u;
    memcpy(&sDurableLedger, source, sizeof(sDurableLedger));
    sSectorValid = 1u;
    return 1u;
}

u8 MegaShopHost_TrySavingData(u8 save_type)
{
    ++sStandardCalls;
    if (save_type != 0u
            || (sFailStandardCall != 0u
                && sStandardCalls == sFailStandardCall))
        return 0u;
    memcpy(sDurableBag, sBag, sizeof(sDurableBag));
    memcpy(sDurableFlags, sFlags, sizeof(sDurableFlags));
    return 1u;
}

void MegaShopHost_ReadFlash(u16 sector, u32 offset, void *destination,
                            u32 size)
{
    if (sector == MEGA_SHOP_SAVE_SECTOR && offset == 0u && sSectorValid) {
        u32 copied = size < sizeof(sDurableLedger)
            ? size : (u32)sizeof(sDurableLedger);
        memcpy(destination, &sDurableLedger, copied);
        if (copied < size)
            memset((u8 *)destination + copied, 0, size - copied);
    } else {
        memset(destination, 0, size);
    }
}

void MegaShopHost_Void(void) {}

u8 MegaShopHost_CreateTask(TaskFunc func, u8 priority)
{
    (void)func;
    (void)priority;
    return MEGA_SHOP_NUM_TASKS;
}

void MegaShopHost_TaskId(u8 task_id) { (void)task_id; }

u16 MegaShopHost_AddWindow(const struct WindowTemplate *template)
{
    (void)template;
    return MEGA_SHOP_WINDOW_INVALID;
}

void MegaShopHost_WindowU8(u8 window_id) { (void)window_id; }
void MegaShopHost_WindowPair(u8 window_id, u8 value)
{
    (void)window_id;
    (void)value;
}

void MegaShopHost_TextPrinter(u8 window_id, u8 font_id, const u8 *text,
                              u8 x, u8 y, u8 speed, void *callback)
{
    (void)window_id;
    (void)font_id;
    (void)text;
    (void)x;
    (void)y;
    (void)speed;
    (void)callback;
}

u8 MegaShopHost_MenuInitCursor(u8 window_id, u8 font_id, u8 left, u8 top,
                               u8 cursor_height, u8 count, u8 cursor)
{
    (void)window_id;
    (void)font_id;
    (void)left;
    (void)top;
    (void)cursor_height;
    (void)count;
    (void)cursor;
    return 0u;
}

s8 MegaShopHost_MenuInput(void) { return MEGA_SHOP_MENU_B; }
u16 MegaShopHost_GetBaseTile(void) { return 0u; }
void MegaShopHost_PlaySe(u16 song) { (void)song; }

static void reset_common(void)
{
    memset(gMegaShopHostVolatileState, 0, sizeof(gMegaShopHostVolatileState));
    memset(gMegaShopHostTasks, 0, sizeof(gMegaShopHostTasks));
    memset(&gMegaShopHostModernSave, 0, sizeof(gMegaShopHostModernSave));
    memset(&gMegaShopHostFlashRead, 0, sizeof(gMegaShopHostFlashRead));
    memset(&sDurableLedger, 0, sizeof(sDurableLedger));
    memset(sBag, 0, sizeof(sBag));
    memset(sDurableBag, 0, sizeof(sDurableBag));
    memset(sFlags, 0, sizeof(sFlags));
    memset(sDurableFlags, 0, sizeof(sDurableFlags));
    gMegaShopHostSpecialResult = 0u;
    gMegaShopHostSpecialVar8004 = 0u;
    sStandardCalls = 0u;
    sSectorCalls = 0u;
    sFailStandardCall = 0u;
    sFailSectorCall = 0u;
    sForceBagFull = 0u;
    sSectorValid = 0u;
}

static void reset_valid(u16 bp, u8 ring)
{
    reset_common();
    VegaSaveInitNew(&gMegaShopHostModernSave, 0u);
    gMegaShopHostModernSave.factory.battle_points = bp;
    VegaSaveFinalize(&gMegaShopHostModernSave);
    sDurableLedger = gMegaShopHostModernSave;
    sSectorValid = 1u;
    if (ring)
        sBag[MEGA_SHOP_KEY_STONE_ITEM] = 1u;
    memcpy(sDurableBag, sBag, sizeof(sBag));
    memcpy(sDurableFlags, sFlags, sizeof(sFlags));
}

static void expect_rolled_back(u16 bp, u16 index)
{
    const u16 item = (u16)(MODERNIZATION_MEGA_SHOP_ITEM_FIRST + index);
    const u16 flag = (u16)(MODERNIZATION_MEGA_SHOP_CLAIM_FLAG_FIRST + index);
    EXPECT(gMegaShopHostModernSave.factory.battle_points == bp);
    EXPECT(VegaSaveValidate(&gMegaShopHostModernSave,
                            sizeof(gMegaShopHostModernSave)) == VEGA_SAVE_OK);
    EXPECT(sBag[item] == 0u);
    EXPECT(sFlags[flag] == 0u);
    EXPECT(sDurableBag[item] == 0u);
    EXPECT(sDurableFlags[flag] == 0u);
    EXPECT(sDurableLedger.factory.battle_points == bp);
    EXPECT(VegaSaveValidate(&sDurableLedger,
                            sizeof(sDurableLedger)) == VEGA_SAVE_OK);
}

static void test_locked_and_invalid_are_pure_on_empty_save(void)
{
    VegaModernSaveData before;
    reset_common();
    before = gMegaShopHostModernSave;
    EXPECT(MegaShop_PurchaseByIndex(0u) == MEGA_SHOP_RESULT_LOCKED);
    EXPECT(memcmp(&before, &gMegaShopHostModernSave, sizeof(before)) == 0);
    EXPECT(sStandardCalls == 0u && sSectorCalls == 0u);
    sBag[MEGA_SHOP_KEY_STONE_ITEM] = 1u;
    EXPECT(MegaShop_PurchaseByIndex(45u)
           == MEGA_SHOP_RESULT_INVALID_SELECTION);
    EXPECT(memcmp(&before, &gMegaShopHostModernSave, sizeof(before)) == 0);
    EXPECT(sStandardCalls == 0u && sSectorCalls == 0u);
}

static void test_all_45_success(void)
{
    u16 index;
    reset_valid(1000u, 1u);
    for (index = 0u; index < MODERNIZATION_MEGA_SHOP_ENTRY_COUNT; ++index) {
        EXPECT(MegaShop_PurchaseByIndex(index) == MEGA_SHOP_RESULT_SUCCESS);
        EXPECT(sBag[MODERNIZATION_MEGA_SHOP_ITEM_FIRST + index] == 1u);
        EXPECT(sFlags[MODERNIZATION_MEGA_SHOP_CLAIM_FLAG_FIRST + index] == 1u);
        EXPECT(gMegaShopHostModernSave.factory.battle_points
               == (u16)(1000u - 16u * (index + 1u)));
    }
    EXPECT(gMegaShopHostModernSave.factory.battle_points == 280u);
    EXPECT(sDurableLedger.factory.battle_points == 280u);
    EXPECT(sStandardCalls == 45u && sSectorCalls == 45u);
    EXPECT(memcmp(sBag, sDurableBag, sizeof(sBag)) == 0);
    EXPECT(memcmp(sFlags, sDurableFlags, sizeof(sFlags)) == 0);
}

static void test_once_survives_fresh_load(void)
{
    unsigned standard_before;
    unsigned sector_before;
    reset_valid(100u, 1u);
    EXPECT(MegaShop_PurchaseByIndex(22u) == MEGA_SHOP_RESULT_SUCCESS);
    EXPECT(gMegaShopHostModernSave.factory.battle_points == 84u);
    standard_before = sStandardCalls;
    sector_before = sSectorCalls;
    EXPECT(MegaShop_PurchaseByIndex(22u)
           == MEGA_SHOP_RESULT_ALREADY_CLAIMED);
    EXPECT(sStandardCalls == standard_before && sSectorCalls == sector_before);

    memset(&gMegaShopHostModernSave, 0, sizeof(gMegaShopHostModernSave));
    memset(sBag, 0, sizeof(sBag));
    memset(sFlags, 0, sizeof(sFlags));
    gMegaShopHostModernSave = sDurableLedger;
    memcpy(sBag, sDurableBag, sizeof(sBag));
    memcpy(sFlags, sDurableFlags, sizeof(sFlags));
    EXPECT(MegaShop_PurchaseByIndex(22u)
           == MEGA_SHOP_RESULT_ALREADY_CLAIMED);
    EXPECT(sBag[1021] == 1u && sFlags[0x14B6] == 1u);
    EXPECT(gMegaShopHostModernSave.factory.battle_points == 84u);
    EXPECT(sStandardCalls == standard_before && sSectorCalls == sector_before);
}

static void test_insufficient_and_bag_full_are_pure_when_initialized(void)
{
    reset_valid(15u, 1u);
    EXPECT(MegaShop_PurchaseByIndex(44u)
           == MEGA_SHOP_RESULT_INSUFFICIENT_BP);
    expect_rolled_back(15u, 44u);
    EXPECT(sStandardCalls == 0u && sSectorCalls == 0u);

    reset_valid(100u, 1u);
    sForceBagFull = 1u;
    EXPECT(MegaShop_PurchaseByIndex(0u) == MEGA_SHOP_RESULT_BAG_FULL);
    expect_rolled_back(100u, 0u);
    EXPECT(sStandardCalls == 0u && sSectorCalls == 0u);
}

static void test_standard_save_failure_compensates_both_stores(void)
{
    reset_valid(100u, 1u);
    sFailStandardCall = 1u;
    EXPECT(MegaShop_PurchaseByIndex(0u)
           == MEGA_SHOP_RESULT_PERSIST_FAILED);
    expect_rolled_back(100u, 0u);
    EXPECT(sStandardCalls == 2u && sSectorCalls == 1u);
}

static void test_sector_failure_compensates_both_stores(void)
{
    reset_valid(100u, 1u);
    sFailSectorCall = 1u;
    EXPECT(MegaShop_PurchaseByIndex(44u)
           == MEGA_SHOP_RESULT_PERSIST_FAILED);
    expect_rolled_back(100u, 44u);
    EXPECT(sStandardCalls == 2u && sSectorCalls == 2u);
}

static void test_empty_unlocked_save_initializes_before_bp_rejection(void)
{
    reset_common();
    sBag[MEGA_SHOP_KEY_STONE_ITEM] = 1u;
    EXPECT(MegaShop_PurchaseByIndex(0u)
           == MEGA_SHOP_RESULT_INSUFFICIENT_BP);
    EXPECT(VegaSaveValidate(&gMegaShopHostModernSave,
                            sizeof(gMegaShopHostModernSave)) == VEGA_SAVE_OK);
    EXPECT(sStandardCalls == 1u && sSectorCalls == 1u);
    EXPECT(sBag[MODERNIZATION_MEGA_SHOP_ITEM_FIRST] == 0u);
    EXPECT(sFlags[MODERNIZATION_MEGA_SHOP_CLAIM_FLAG_FIRST] == 0u);
}

int main(void)
{
    test_locked_and_invalid_are_pure_on_empty_save();
    test_all_45_success();
    test_once_survives_fresh_load();
    test_insufficient_and_bag_full_are_pure_when_initialized();
    test_standard_save_failure_compensates_both_stores();
    test_sector_failure_compensates_both_stores();
    test_empty_unlocked_save_initializes_before_bp_rejection();
    printf("{\"status\":\"%s\",\"assertions\":%u,\"failures\":%u,"
           "\"catalog_entries\":45,\"failure_injection_cases\":2}\n",
           sFailures == 0u ? "PASS" : "FAIL", sAssertions, sFailures);
    return sFailures == 0u ? 0 : 1;
}
