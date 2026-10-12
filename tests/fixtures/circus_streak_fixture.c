/* 実ROM受入とは別のhost状態遷移・保存失敗検証。 */
#include "overlays/circus_streak/circus_streak.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

struct Store {
    unsigned calls;
    int fail;
    CircusStreakOwner disk;
    CircusStreakOwner *ram;
    CircusStreakOwner before;
};
static int persist(const CircusStreakOwner *next, void *context)
{
    struct Store *s = context;
    assert(CircusStreakValid(next));
    assert(memcmp(s->ram, &s->before, sizeof(s->before)) == 0);
    ++s->calls;
    if (s->fail)
        return 0;
    s->disk = *next;
    return 1;
}
#define SNAP() do { store.before = owner; } while (0)
#define CALL(expr, expected) do { SNAP(); int result = (expr); assert(result == (expected)); \
    if (result != CIRCUS_OK) assert(memcmp(&owner, &store.before, sizeof(owner)) == 0); } while (0)
#define INIT() CALL(CircusStreakInitialize(&owner, persist, &store), CIRCUS_OK)
#define BEGIN() CALL(CircusStreakBegin(&owner, persist, &store), CIRCUS_OK)
#define ARM() CALL(CircusStreakArm(&owner, persist, &store), CIRCUS_OK)
#define WIN() CALL(CircusStreakSettle(&owner, owner.prepared, CIRCUS_WIN, persist, &store), CIRCUS_OK)
#define END(ok) CALL(CircusStreakEnd(&owner, ok, persist, &store), CIRCUS_OK)

int main(int argc, char **argv)
{
    CircusStreakOwner owner = {0};
    struct Store store = { .ram = &owner };
    unsigned i, bit;
    assert(argc == 2);
    if (!strcmp(argv[1], "roundtrip")) {
        INIT(); BEGIN();
        for (i = 1; i <= 33; ++i) {
            ARM(); WIN();
            assert(owner.current == i && owner.best == i);
            assert(owner.prepared == owner.settled && owner.phase == CIRCUS_READY);
            unsigned calls = store.calls;
            CALL(CircusStreakSettle(&owner, owner.prepared, CIRCUS_WIN, persist, &store), CIRCUS_DUPLICATE);
            assert(calls == store.calls);
            if (i % 3 == 0) {
                END(1);
                memset(&owner, 0, sizeof(owner));
                owner = store.disk;
                assert(CircusStreakValid(&owner));
                CALL(CircusStreakRecover(&owner, persist, &store), CIRCUS_DUPLICATE);
                assert(owner.current == i);
                BEGIN();
            }
        }
        ARM();
        CALL(CircusStreakSettle(&owner, owner.prepared, CIRCUS_LOSS, persist, &store), CIRCUS_OK);
        assert(owner.current == 0 && owner.best == 33);
        END(0);
    } else if (!strcmp(argv[1], "rollback")) {
        store.fail = 1;
        CALL(CircusStreakInitialize(&owner, persist, &store), CIRCUS_PERSIST_FAILED);
        store.fail = 0; INIT();
        store.fail = 1;
        CALL(CircusStreakBegin(&owner, persist, &store), CIRCUS_PERSIST_FAILED);
        store.fail = 0; BEGIN();
        store.fail = 1;
        CALL(CircusStreakArm(&owner, persist, &store), CIRCUS_PERSIST_FAILED);
        store.fail = 0; ARM();
        store.fail = 1;
        CALL(CircusStreakSettle(&owner, owner.prepared, CIRCUS_WIN, persist, &store), CIRCUS_PERSIST_FAILED);
        store.fail = 0; WIN();
        store.fail = 1;
        CALL(CircusStreakEnd(&owner, 1, persist, &store), CIRCUS_PERSIST_FAILED);
        store.fail = 0; END(1);
        assert(owner.current == 1 && owner.best == 1);
    } else if (!strcmp(argv[1], "corruption")) {
        INIT();
        CircusStreakOwner good = owner;
        for (i = 0; i < sizeof(owner); ++i)
            for (bit = 0; bit < 8; ++bit) {
                owner = good;
                ((unsigned char *)&owner)[i] ^= (unsigned char)(1u << bit);
                assert(!CircusStreakValid(&owner));
                CALL(CircusStreakInitialize(&owner, persist, &store), CIRCUS_INVALID);
            }
        owner = good; owner.version = 2; owner.crc32 = CircusStreakCrc(&owner);
        assert(!CircusStreakValid(&owner));
        CALL(CircusStreakBegin(&owner, persist, &store), CIRCUS_INVALID);
        owner = good; owner.reserved[19] = 1; owner.crc32 = CircusStreakCrc(&owner);
        assert(!CircusStreakValid(&owner));
        owner = good; owner.current = 1; owner.crc32 = CircusStreakCrc(&owner);
        assert(!CircusStreakValid(&owner));
        memset(&owner, 0xFF, sizeof(owner)); INIT();
        assert(owner.current == 0 && owner.best == 0);
    } else if (!strcmp(argv[1], "interruption")) {
        INIT(); BEGIN(); ARM(); WIN(); END(1);
        assert(owner.current == 1);
        BEGIN(); ARM();
        owner = store.disk;
        CALL(CircusStreakRecover(&owner, persist, &store), CIRCUS_OK);
        assert(owner.current == 0 && owner.best == 1 && owner.phase == CIRCUS_IDLE);
        CALL(CircusStreakSettle(&owner, owner.prepared, CIRCUS_WIN, persist, &store), CIRCUS_WRONG_PHASE);
        BEGIN(); ARM(); WIN();
        CALL(CircusStreakRecover(&owner, persist, &store), CIRCUS_OK);
        assert(owner.current == 0 && owner.best == 1);
    } else if (!strcmp(argv[1], "boundaries")) {
        INIT(); BEGIN();
        for (i = 0; i < 65537u; ++i) { ARM(); WIN(); }
        assert(owner.current == UINT16_MAX && owner.best == UINT16_MAX);
        owner.prepared = owner.settled = UINT32_MAX;
        owner.crc32 = CircusStreakCrc(&owner);
        CALL(CircusStreakArm(&owner, persist, &store), CIRCUS_EXHAUSTED);
        owner.generation = UINT32_MAX; owner.crc32 = CircusStreakCrc(&owner);
        CALL(CircusStreakEnd(&owner, 1, persist, &store), CIRCUS_EXHAUSTED);
    } else if (!strcmp(argv[1], "ordering")) {
        INIT();
        CALL(CircusStreakArm(&owner, persist, &store), CIRCUS_WRONG_PHASE);
        BEGIN();
        CALL(CircusStreakBegin(&owner, persist, &store), CIRCUS_WRONG_PHASE);
        CALL(CircusStreakSettle(&owner, 1, CIRCUS_WIN, persist, &store), CIRCUS_WRONG_PHASE);
        ARM();
        CALL(CircusStreakArm(&owner, persist, &store), CIRCUS_WRONG_PHASE);
        CALL(CircusStreakSettle(&owner, 0, CIRCUS_WIN, persist, &store), CIRCUS_STALE_BATTLE);
        CALL(CircusStreakSettle(&owner, 2, CIRCUS_WIN, persist, &store), CIRCUS_STALE_BATTLE);
        CALL(CircusStreakSettle(&owner, 1, CIRCUS_ABORT, persist, &store), CIRCUS_INVALID);
        CALL(CircusStreakEnd(&owner, 1, persist, &store), CIRCUS_WRONG_PHASE);
        WIN(); ARM();
        CALL(CircusStreakSettle(&owner, 1, CIRCUS_WIN, persist, &store), CIRCUS_STALE_BATTLE);
        WIN(); END(1);
        CALL(CircusStreakInitialize(&owner, persist, &store), CIRCUS_DUPLICATE);
    } else { return 2; }
    printf("{\"scenario\":\"%s\",\"persist_calls\":%u,\"host_only\":true,\"native_processes\":0}\n", argv[1], store.calls);
    return 0;
}
