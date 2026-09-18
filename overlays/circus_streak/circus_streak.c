/* USER-20260919-CIRCUS-STREAK: 正規battle境界でのみ更新する独立保存owner。 */
#include "circus_streak.h"

static void copy_owner(CircusStreakOwner *to, const CircusStreakOwner *from)
{
    size_t i;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
        ((uint8_t *)to)[i] = ((const uint8_t *)from)[i];
}

uint32_t CircusStreakCrc(const CircusStreakOwner *owner)
{
    const uint8_t *bytes = (const uint8_t *)owner;
    uint32_t crc = UINT32_MAX;
    size_t i;
    unsigned bit;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i) {
        crc ^= i >= 12u && i < 16u ? 0u : bytes[i];
        for (bit = 0; bit < 8u; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return crc ^ UINT32_MAX;
}

int CircusStreakValid(const CircusStreakOwner *owner)
{
    size_t i;
    if (owner == NULL || owner->magic != CIRCUS_STREAK_MAGIC
        || owner->magic_inverse != (uint32_t)~CIRCUS_STREAK_MAGIC
        || owner->version != CIRCUS_STREAK_VERSION || owner->size != CIRCUS_STREAK_SIZE
        || owner->generation == 0u || owner->format != 0u
        || owner->phase > CIRCUS_ARMED || owner->last_outcome > CIRCUS_ABORT
        || owner->current > owner->best || owner->crc32 != CircusStreakCrc(owner))
        return 0;
    for (i = 0; i < sizeof(owner->reserved); ++i)
        if (owner->reserved[i] != 0u)
            return 0;
    if (owner->phase == CIRCUS_ARMED) {
        if (owner->settled == UINT32_MAX || owner->prepared != owner->settled + 1u)
            return 0;
    } else if (owner->prepared != owner->settled) {
        return 0;
    }
    if (owner->phase != CIRCUS_IDLE && owner->session == 0u)
        return 0;
    if (owner->session == 0u && (owner->prepared != 0u || owner->current != 0u
        || owner->best != 0u || owner->last_outcome != 0u))
        return 0;
    return 1;
}

static int commit(CircusStreakOwner *owner, CircusStreakOwner *next,
                  CircusStreakPersist persist, void *ctx)
{
    if (persist == NULL)
        return CIRCUS_INVALID;
    if (next->generation == UINT32_MAX)
        return CIRCUS_EXHAUSTED;
    ++next->generation;
    next->crc32 = CircusStreakCrc(next);
    if (!CircusStreakValid(next))
        return CIRCUS_INVALID;
    if (persist(next, ctx) != 1)
        return CIRCUS_PERSIST_FAILED;
    copy_owner(owner, next);
    return CIRCUS_OK;
}

int CircusStreakInitialize(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx)
{
    CircusStreakOwner next;
    size_t i;
    int zero = 1, erased = 1;
    if (owner == NULL)
        return CIRCUS_INVALID;
    if (CircusStreakValid(owner))
        return CIRCUS_DUPLICATE;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i) {
        uint8_t byte = ((const uint8_t *)owner)[i];
        zero &= byte == 0u;
        erased &= byte == 0xFFu;
        ((uint8_t *)&next)[i] = 0u;
    }
    /* CRC不正／未知schemaは旧セーブ扱いで上書きしない。 */
    if (!zero && !erased)
        return CIRCUS_INVALID;
    next.magic = CIRCUS_STREAK_MAGIC;
    next.magic_inverse = ~CIRCUS_STREAK_MAGIC;
    next.version = CIRCUS_STREAK_VERSION;
    next.size = CIRCUS_STREAK_SIZE;
    return commit(owner, &next, persist, ctx);
}

int CircusStreakBegin(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx)
{
    CircusStreakOwner next;
    if (!CircusStreakValid(owner))
        return CIRCUS_INVALID;
    if (owner->phase != CIRCUS_IDLE)
        return CIRCUS_WRONG_PHASE;
    if (owner->session == UINT32_MAX)
        return CIRCUS_EXHAUSTED;
    copy_owner(&next, owner);
    ++next.session;
    next.phase = CIRCUS_READY;
    return commit(owner, &next, persist, ctx);
}

int CircusStreakArm(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx)
{
    CircusStreakOwner next;
    if (!CircusStreakValid(owner))
        return CIRCUS_INVALID;
    if (owner->phase != CIRCUS_READY)
        return CIRCUS_WRONG_PHASE;
    if (owner->settled == UINT32_MAX)
        return CIRCUS_EXHAUSTED;
    copy_owner(&next, owner);
    ++next.prepared;
    next.phase = CIRCUS_ARMED;
    return commit(owner, &next, persist, ctx);
}

int CircusStreakSettle(CircusStreakOwner *owner, uint32_t battle, uint8_t outcome,
                      CircusStreakPersist persist, void *ctx)
{
    CircusStreakOwner next;
    if (!CircusStreakValid(owner) || (outcome != CIRCUS_WIN && outcome != CIRCUS_LOSS))
        return CIRCUS_INVALID;
    if (owner->phase == CIRCUS_READY && battle != 0u && battle == owner->settled
        && outcome == owner->last_outcome)
        return CIRCUS_DUPLICATE;
    if (owner->phase != CIRCUS_ARMED)
        return CIRCUS_WRONG_PHASE;
    if (battle != owner->prepared)
        return CIRCUS_STALE_BATTLE;
    copy_owner(&next, owner);
    next.settled = battle;
    next.last_outcome = outcome;
    next.phase = CIRCUS_READY;
    if (outcome == CIRCUS_WIN) {
        if (next.current != UINT16_MAX)
            ++next.current;
        if (next.best < next.current)
            next.best = next.current;
    } else {
        next.current = 0u;
    }
    return commit(owner, &next, persist, ctx);
}

int CircusStreakEnd(CircusStreakOwner *owner, int completed,
                   CircusStreakPersist persist, void *ctx)
{
    CircusStreakOwner next;
    if (!CircusStreakValid(owner))
        return CIRCUS_INVALID;
    if (owner->phase == CIRCUS_IDLE)
        return CIRCUS_DUPLICATE;
    if (completed && owner->phase != CIRCUS_READY)
        return CIRCUS_WRONG_PHASE;
    copy_owner(&next, owner);
    if (!completed) {
        next.current = 0u;
        next.last_outcome = CIRCUS_ABORT;
        next.settled = next.prepared;
    }
    next.phase = CIRCUS_IDLE;
    return commit(owner, &next, persist, ctx);
}

int CircusStreakRecover(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx)
{
    /* 中断した挑戦は失格。未完battleを勝利に変換しない。bestは保持する。 */
    return CircusStreakEnd(owner, 0, persist, ctx);
}
