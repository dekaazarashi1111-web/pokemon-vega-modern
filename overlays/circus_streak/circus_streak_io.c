/* sector31の既存ownerを維持する、アドレス非依存のserializer。 */
#include "circus_streak_io.h"

static int accept_load(const CircusStreakOwner *owner, void *unused)
{
    (void)unused;
    return CircusStreakValid(owner);
}

int CircusStreakLoadBytes(CircusStreakOwner *owner, const CircusStreakOwner *saved,
                         uint32_t save_identity)
{
    size_t i;
    if (owner == NULL || saved == NULL)
        return CIRCUS_INVALID;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
        ((uint8_t *)owner)[i] = ((const uint8_t *)saved)[i];
    if (CircusStreakValid(owner)) {
        if (owner->save_identity == save_identity)
            return CIRCUS_OK;
        /* 別の主人公で始めた新規ゲームに旧セーブの連勝を引き継がない。 */
        for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
            ((uint8_t *)owner)[i] = 0u;
    }
    return CircusStreakInitializeFor(owner, save_identity, accept_load, NULL);
}

int CircusStreakMergeSector(uint8_t *output, const uint8_t *image,
                           const CircusStreakOwner *next)
{
    size_t i;
    if (output == NULL || image == NULL || !CircusStreakValid(next))
        return CIRCUS_INVALID;
    for (i = 0; i < CIRCUS_SECTOR_SIZE; ++i)
        output[i] = i < CIRCUS_SECTOR_PAYLOAD ? image[i] : 0u;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
        output[CIRCUS_STREAK_SECTOR_OFFSET + i] = ((const uint8_t *)next)[i];
    return CIRCUS_OK;
}

int CircusStreakPersistedEqual(const CircusStreakOwner *next,
                              const CircusStreakOwner *readback)
{
    size_t i;
    if (!CircusStreakValid(next) || !CircusStreakValid(readback))
        return 0;
    for (i = 0; i < CIRCUS_STREAK_SIZE; ++i)
        if (((const uint8_t *)next)[i] != ((const uint8_t *)readback)[i])
            return 0;
    return 1;
}
