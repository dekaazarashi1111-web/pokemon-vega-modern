#ifndef VEGA_CIRCUS_STREAK_H
#define VEGA_CIRCUS_STREAK_H

#include <stddef.h>
#include <stdint.h>

/* Circus標準・Lv50・random single・3体専用。Factory24枠を共有しない。 */
#define CIRCUS_STREAK_ADDRESS 0x0203DB00u
#define CIRCUS_STREAK_IMAGE_OFFSET 0x2A18u
#define CIRCUS_STREAK_SECTOR_OFFSET 0x0B64u
#define CIRCUS_STREAK_SIZE 64u
#define CIRCUS_STREAK_MAGIC 0x31534356u /* "VCS1" */
#define CIRCUS_STREAK_VERSION 1u

enum CircusStreakPhase { CIRCUS_IDLE = 0, CIRCUS_READY = 1, CIRCUS_ARMED = 2 };
enum CircusStreakOutcome { CIRCUS_WIN = 1, CIRCUS_LOSS = 2, CIRCUS_ABORT = 3 };
enum CircusStreakResult {
    CIRCUS_OK = 0, CIRCUS_DUPLICATE = 1, CIRCUS_INVALID = 2,
    CIRCUS_WRONG_PHASE = 3, CIRCUS_STALE_BATTLE = 4,
    CIRCUS_PERSIST_FAILED = 5, CIRCUS_EXHAUSTED = 6
};

typedef struct CircusStreakOwner {
    uint32_t magic;
    uint32_t magic_inverse;
    uint16_t version;
    uint16_t size;
    uint32_t crc32;
    uint32_t generation;
    uint32_t session;
    uint32_t prepared;
    uint32_t settled;
    uint16_t current;
    uint16_t best;
    uint8_t phase;
    uint8_t format;
    uint8_t last_outcome;
    uint8_t reserved[25];
} CircusStreakOwner;

_Static_assert(sizeof(CircusStreakOwner) == CIRCUS_STREAK_SIZE, "Circus owner ABI");
_Static_assert(offsetof(CircusStreakOwner, crc32) == 12u, "Circus CRC ABI");
_Static_assert(offsetof(CircusStreakOwner, current) == 32u, "Circus streak ABI");
_Static_assert(CIRCUS_STREAK_ADDRESS - 0x0203CF9Cu == CIRCUS_STREAK_SECTOR_OFFSET,
               "Circus sector31 offset");

/* callbackは候補の全64byteを永続化してから1を返す。失敗時RAMは変更しない。 */
typedef int (*CircusStreakPersist)(const CircusStreakOwner *, void *);
uint32_t CircusStreakCrc(const CircusStreakOwner *owner);
int CircusStreakValid(const CircusStreakOwner *owner);
int CircusStreakInitialize(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx);
int CircusStreakBegin(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx);
int CircusStreakArm(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx);
int CircusStreakSettle(CircusStreakOwner *owner, uint32_t battle, uint8_t outcome,
                      CircusStreakPersist persist, void *ctx);
int CircusStreakEnd(CircusStreakOwner *owner, int completed,
                   CircusStreakPersist persist, void *ctx);
int CircusStreakRecover(CircusStreakOwner *owner, CircusStreakPersist persist, void *ctx);
#endif
