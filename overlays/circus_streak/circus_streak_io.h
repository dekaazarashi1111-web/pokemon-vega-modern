#ifndef VEGA_CIRCUS_STREAK_IO_H
#define VEGA_CIRCUS_STREAK_IO_H
#include "circus_streak.h"
#define CIRCUS_SECTOR_PAYLOAD 4080u
#define CIRCUS_SECTOR_SIZE 4096u
int CircusStreakLoadBytes(CircusStreakOwner *owner, const CircusStreakOwner *saved,
                         uint32_t save_identity);
int CircusStreakMergeSector(uint8_t *output, const uint8_t *image,
                           const CircusStreakOwner *next);
int CircusStreakPersistedEqual(const CircusStreakOwner *next,
                              const CircusStreakOwner *readback);
#endif
