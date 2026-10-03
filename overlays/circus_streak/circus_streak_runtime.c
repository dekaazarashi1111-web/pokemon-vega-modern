/* 既存read-keys/save-loadへ一度だけ委譲。Circus固有の64byteのみ復元する。 */
#include "circus_streak_runtime.h"
#include "circus_streak_io.h"
#include "circus_streak_loss.h"
#include "circus_streak_return.h"
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

static void resume_loss_fade_if_waiting(void)
{
    const volatile VegaFactoryState *f = &gVegaModernSaveData->factory;
    const volatile uint8_t *tasks = (const volatile uint8_t *)(uintptr_t)0x030050D0u;
    uint8_t weather_waiter = 0u, script_waiter = 0u;
    uint32_t callback = *(volatile uint32_t *)(uintptr_t)0x03003134u;
    uint32_t script = *(volatile uint32_t *)(uintptr_t)0x03000EB8u;
    uint8_t ready = *(volatile uint8_t *)(uintptr_t)0x02038530u;
    unsigned i;
    if (callback != 0x08055E75u || ready != 0u)
        return;
    for (i = 0; i < 16u; ++i) {
        const volatile uint8_t *task = tasks + 40u * i;
        uint32_t function;
        if (task[4] != 1u)
            continue;
        function = *(const volatile uint32_t *)(const volatile void *)task;
        if (function == 0x0807951Du) weather_waiter = 1u;
        if (function == 0x0807D465u) script_waiter = 1u;
    }
    if (CircusStreakReturnFadeAllowed((uint8_t)CircusStreakRuntimeArmed(),
            (uint8_t)((*(volatile uint32_t *)(uintptr_t)0x02022AACu & 0x04000000u) != 0u),
            f->marker, f->snapshot_valid, f->party_count,
            *(volatile uint8_t *)(uintptr_t)0x02023DEAu, script, callback, ready,
            weather_waiter, script_waiter)
        && VegaSaveValidate(gVegaModernSaveData, VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK) {
        /* 両待機taskの実観測に限定。通常のFadeInFromBlackでreadyForInitを立てる。
         * Task_WeatherInit/Task_ContinueScriptが本来の初期化と再開を完了する。
         * readyForInitとtask遷移が再実行を抑止。hostからの状態注入は不要。 */
        ((void (*)(void))(uintptr_t)0x0807D361u)();
    }
}

EXPORT void CircusStreakRuntimeReadKeys(void)
{
    /* 下流ownerの復旧がsector31を書いてもCircus領域をゼロで上書きしない。 */
    restore_cache_if_field();
    ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_READ_KEYS)();
    restore_cache_if_field();
    resume_loss_fade_if_waiting();
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

/* VegaFacilityStateGetはVarGetではなく、T06の0..10 field ABI。 */
enum CircusFacilityStateField {
    CIRCUS_FIELD_NUMBER = 0, CIRCUS_FIELD_PARTY_SIZE = 1,
    CIRCUS_FIELD_LEVEL = 2, CIRCUS_FIELD_BATTLE_TYPE = 3, CIRCUS_FIELD_TIER = 4
};

EXPORT uint16_t CircusStreakRuntimeGet(uint8_t current_or_max, uint16_t style,
                                      uint16_t tier, uint16_t size, uint8_t level)
{
    if (STATE_GET(CIRCUS_FIELD_NUMBER) == 3u && CircusStreakRuntimeArmed() && current_or_max <= 1u
        && (style == 0xFFFFu ? STATE_GET(CIRCUS_FIELD_BATTLE_TYPE) : style) == 4u
        && (tier == 0xFFFFu ? STATE_GET(CIRCUS_FIELD_TIER) : tier) == 0u
        && (size == 0xFFFFu ? STATE_GET(CIRCUS_FIELD_PARTY_SIZE) : size) == 3u
        && (level == 0u ? STATE_GET(CIRCUS_FIELD_LEVEL) : level) == 50u)
        return current_or_max == 0u ? OWNER->current : OWNER->best;
    return ((uint16_t (*)(uint8_t, uint16_t, uint16_t, uint16_t, uint8_t))
        (uintptr_t)0x091025EDu)(current_or_max, style, tier, size, level);
}

EXPORT void CircusStreakRuntimeLossReturn(void)
{
    const volatile VegaFactoryState *f = &gVegaModernSaveData->factory;
    uint8_t outcome = *(volatile uint8_t *)(uintptr_t)0x02023DEAu;
    uint32_t script = *(volatile uint32_t *)(uintptr_t)0x03000EB8u;
    if (CircusStreakLossAllowed((uint8_t)CircusStreakRuntimeArmed(), 1u,
            f->marker, f->snapshot_valid, f->party_count, outcome, script)
        && VegaSaveValidate(gVegaModernSaveData, VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK) {
        /* 既存EndTrainerBattleの復帰経路。集計と復元はscriptのAfterBattleが所有。 */
        ((void (*)(void))(uintptr_t)0x080561A1u)();
    } else {
        ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_LOSS_RETURN)();
    }
}
