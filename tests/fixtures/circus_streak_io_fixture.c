#include "overlays/circus_streak/circus_streak_io.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int accept(const CircusStreakOwner *p, void *unused) {(void)unused; return CircusStreakValid(p);}
int main(void)
{
    CircusStreakOwner owner = {0}, loaded = {0}, bad;
    uint8_t image[CIRCUS_SECTOR_PAYLOAD], output[CIRCUS_SECTOR_SIZE], before[CIRCUS_SECTOR_PAYLOAD];
    unsigned i;
    assert(CircusStreakInitializeFor(&owner, 0x12345678u, accept, NULL) == CIRCUS_OK);
    assert(CircusStreakBegin(&owner, accept, NULL) == CIRCUS_OK);
    for (i = 0; i < 33; ++i) {
        assert(CircusStreakArm(&owner, accept, NULL) == CIRCUS_OK);
        assert(CircusStreakSettle(&owner, owner.prepared, CIRCUS_WIN, accept, NULL) == CIRCUS_OK);
    }
    assert(CircusStreakEnd(&owner, 1, accept, NULL) == CIRCUS_OK);
    for (i = 0; i < sizeof(image); ++i) image[i] = (uint8_t)(i * 29u + 7u);
    memcpy(before, image, sizeof(image));
    assert(CircusStreakMergeSector(output, image, &owner) == CIRCUS_OK);
    for (i = 0; i < sizeof(output); ++i) {
        if (i >= CIRCUS_STREAK_SECTOR_OFFSET && i < CIRCUS_STREAK_SECTOR_OFFSET + CIRCUS_STREAK_SIZE)
            assert(output[i] == ((uint8_t *)&owner)[i - CIRCUS_STREAK_SECTOR_OFFSET]);
        else assert(output[i] == (i < sizeof(image) ? image[i] : 0u));
    }
    assert(!memcmp(image, before, sizeof(image)));
    memcpy(&loaded, output + CIRCUS_STREAK_SECTOR_OFFSET, sizeof(loaded));
    assert(CircusStreakPersistedEqual(&owner, &loaded));
    assert(CircusStreakLoadBytes(&loaded, &owner, 0x12345678u) == CIRCUS_OK);
    assert(loaded.current == 33 && loaded.best == 33 && loaded.phase == CIRCUS_IDLE);
    assert(CircusStreakLoadBytes(&loaded, &owner, 0x87654321u) == CIRCUS_OK);
    assert(loaded.current == 0 && loaded.best == 0 && loaded.session == 0 && loaded.save_identity == 0x87654321u);
    bad = owner; bad.current ^= 1;
    assert(!CircusStreakPersistedEqual(&owner, &bad));
    assert(CircusStreakLoadBytes(&loaded, &bad, 0x12345678u) == CIRCUS_INVALID);
    assert(!memcmp(&loaded, &bad, sizeof(bad)));
    assert(CircusStreakMergeSector(output, image, &bad) == CIRCUS_INVALID);
    memset(&bad, 0xFF, sizeof(bad));
    assert(CircusStreakLoadBytes(&loaded, &bad, 0x11223344u) == CIRCUS_OK);
    assert(loaded.current == 0 && loaded.save_identity == 0x11223344u);
    puts("PASS_CIRCUS_IO_HOST_ONLY untouched_payload_bytes=4016 native_processes=0");
    return 0;
}
