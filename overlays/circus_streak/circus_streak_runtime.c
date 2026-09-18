/* 既存read-keys/save-loadへ一度だけ委譲。Circus固有の64byteのみ復元する。 */
#include "circus_streak_runtime.h"
#include "circus_streak_io.h"
#include "../save_migration/save_migration.h"
#include "circus_streak_addresses.h"

#define OWNER ((CircusStreakOwner *)(uintptr_t)CIRCUS_STREAK_ADDRESS)
#define BUFFER ((uint8_t *)(uintptr_t)0x020399B0u)
#define IMAGE ((const uint8_t *)(uintptr_t)0x0203CF9Cu)
#define RESULT (*(volatile uint16_t *)(uintptr_t)0x02037004u)
#define READ_FLASH ((void (*)(uint16_t, uint32_t, void *, uint32_t))(uintptr_t)0x081C2A55u)
#define WRITE_SECTOR ((uint8_t (*)(uint16_t, const void *))(uintptr_t)0x080DA9C1u)
#define STATE_GET ((uint16_t (*)(uint16_t))(uintptr_t)0x091269B9u)
#define SCRIPT_LOCK ((uint16_t (*)(void))(uintptr_t)0x08069219u)
#define EXPORT __attribute__((used, noinline, externally_visible))

/* 複製したCircus側の復旧だけを呼ぶ。旧Factory entrypointは不変。 */
extern void CircusRuntime_Recover(void);

static uint32_t save_identity(void)
{
    const volatile uint8_t *save2 = *(const volatile uint8_t * volatile *)(uintptr_t)0x0300504Cu;
    if ((uintptr_t)save2 < 0x02000000u || (uintptr_t)save2 > 0x0203F000u)
        return 0u;
    /* SaveBlock2.playerTrainerIdは+0xA。非整列u32 loadは禁止。 */
    return (uint32_t)save2[10] | ((uint32_t)save2[11] << 8)
        | ((uint32_t)save2[12] << 16) | ((uint32_t)save2[13] << 24);
}

static int persist(const CircusStreakOwner *next, void *unused)
{
    CircusStreakOwner readback;
    (void)unused;
    VegaSaveFinalize(gVegaModernSaveData);
    if (CircusStreakMergeSector(BUFFER, IMAGE, next) != CIRCUS_OK
        || WRITE_SECTOR(31u, BUFFER) != 1u)
        return 0;
    READ_FLASH(31u, CIRCUS_STREAK_SECTOR_OFFSET, &readback, CIRCUS_STREAK_SIZE);
    return CircusStreakPersistedEqual(next, &readback);
}

static int load(void)
{
    CircusStreakOwner saved;
    READ_FLASH(31u, CIRCUS_STREAK_SECTOR_OFFSET, &saved, CIRCUS_STREAK_SIZE);
    return CircusStreakLoadBytes(OWNER, &saved, save_identity()) == CIRCUS_OK;
}

static int valid(void)
{
    return CircusStreakValid(OWNER) && OWNER->save_identity == save_identity();
}

static int succeeded(int result)
{
    return result == CIRCUS_OK || result == CIRCUS_DUPLICATE;
}

int CircusStreakRuntimeRecover(void)
{
    if (!valid() && !load())
        return 0;
    return succeeded(CircusStreakRecover(OWNER, persist, NULL));
}

int CircusStreakRuntimeBegin(void)
{
    if (!valid() && !load())
        return 0;
    return CircusStreakBegin(OWNER, persist, NULL) == CIRCUS_OK;
}

int CircusStreakRuntimeArm(void)
{
    return valid() && CircusStreakArm(OWNER, persist, NULL) == CIRCUS_OK;
}

int CircusStreakRuntimeArmed(void)
{
    return valid() && OWNER->phase == CIRCUS_ARMED;
}

int CircusStreakRuntimeRecord(uint8_t outcome)
{
    return valid() && CircusStreakSettle(OWNER, OWNER->prepared,
        outcome == 1u ? CIRCUS_WIN : CIRCUS_LOSS, persist, NULL) == CIRCUS_OK;
}

int CircusStreakRuntimeEnd(int completed)
{
    int result;
    if (!valid())
        return 0;
    result = CircusStreakEnd(OWNER, completed, persist, NULL);
    /* 既にIDLEでも、今回の原party復旧/T08更新は同じsectorへ保存する。 */
    if (result == CIRCUS_DUPLICATE)
        return persist(OWNER, NULL);
    return result == CIRCUS_OK;
}

static void restore_cache_if_field(void)
{
    if (*(volatile uint32_t *)(uintptr_t)0x03003134u != 0x08055E75u || SCRIPT_LOCK())
        return;
    if (OWNER->magic == CIRCUS_STREAK_MAGIC && OWNER->magic_inverse == ~CIRCUS_STREAK_MAGIC
        && OWNER->save_identity == save_identity())
        return;
    if (load() && OWNER->phase != CIRCUS_IDLE)
        CircusRuntime_Recover();
}

EXPORT void CircusStreakRuntimeReadKeys(void)
{
    /* 下流ownerの復旧がsector31を書いてもCircus領域をゼロで上書きしない。 */
    restore_cache_if_field();
    ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_READ_KEYS)();
    restore_cache_if_field();
}

EXPORT uint8_t CircusStreakRuntimeSaveLoad(uint8_t save_type)
{
    uint8_t result = ((uint8_t (*)(uint8_t))(uintptr_t)CIRCUS_PREVIOUS_SAVE_LOAD)(save_type);
    size_t i;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
        ((uint8_t *)OWNER)[i] = 0u;
    return result;
}

EXPORT void CircusStreakRuntimeSelect(void)
{
    if (!CircusStreakRuntimeArmed()) {
        RESULT = 0u;
        return;
    }
    ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_SELECTOR)();
}

EXPORT uint16_t CircusStreakRuntimeGet(uint8_t current_or_max, uint16_t style,
                                      uint16_t tier, uint16_t size, uint8_t level)
{
    if (STATE_GET(0x403Au) == 3u && CircusStreakRuntimeArmed() && current_or_max <= 1u
        && (style == 0xFFFFu ? STATE_GET(0x5017u) : style) == 4u
        && (tier == 0xFFFFu ? STATE_GET(0x5018u) : tier) == 0u
        && (size == 0xFFFFu ? STATE_GET(0x5015u) : size) == 3u
        && (level == 0u ? STATE_GET(0x5016u) : level) == 50u)
        return current_or_max == 0u ? OWNER->current : OWNER->best;
    return ((uint16_t (*)(uint8_t, uint16_t, uint16_t, uint16_t, uint8_t))
        (uintptr_t)0x091025EDu)(current_or_max, style, tier, size, level);
}
