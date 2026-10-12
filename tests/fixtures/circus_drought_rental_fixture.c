#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../../overlays/circus_streak/circus_drought_rental.h"

static uint8_t weather[0x800];
static unsigned originals, inits, steps, stuck;

static CircusDroughtContext rental(void)
{
    CircusDroughtContext c = {0,1,1,1,1,1,1,12,12,1,1,0x08055E75u,0x09FF4CB5u};
    return c;
}
static CircusDroughtContext selection(void)
{
    CircusDroughtContext c = {1,1,1,2,1,1,0,12,12,1,1,0x08055E75u,0x09FF4DADu};
    return c;
}
static void original(void) { ++originals; }
static void init(void) { ++inits; weather[0x6CC] = 0u; weather[0x6D2] = 0u; }
static void step(void)
{
    assert(++steps <= 256u);
    if (stuck) return;
    switch (weather[0x6CC]) {
    case 0: ++weather[0x6CC]; break;
    case 1: weather[0x74D] = 1u; weather[0x74E] = 1u; ++weather[0x6CC]; break;
    case 2: assert(weather[0x74D] == 32u && weather[0x74E] == 32u); ++weather[0x6CC]; break;
    case 3: ++weather[0x6CC]; break;
    case 4: weather[0x6D2] = 1u; ++weather[0x6CC]; break;
    default: assert(0);
    }
}
static void reset(void)
{
    memset(weather, 0, sizeof(weather)); originals = inits = steps = stuck = 0u;
}
static void completed(const CircusDroughtContext *c, uint8_t ready, uint8_t count)
{
    CircusDroughtContext before = *c;
    reset();
    CircusDroughtInitializeRentalBoundary(c, ready, count, weather, original, init, step);
    assert(originals == 0u && inits == 1u && steps == 5u);
    assert(weather[0x6CC] == 5u && weather[0x6D2] == 1u);
    assert(!memcmp(c, &before, sizeof(*c)));
}
static void rejected(const CircusDroughtContext *c, uint8_t ready, uint8_t count)
{
    uint8_t before[sizeof(weather)];
    memset(weather, 0xA5, sizeof(weather)); memcpy(before, weather, sizeof(weather));
    originals = inits = steps = 0u;
    CircusDroughtInitializeRentalBoundary(c, ready, count, weather, original, init, step);
    assert(originals == 1u && inits == 0u && steps == 0u);
    assert(!memcmp(weather, before, sizeof(weather)));
}
int main(void)
{
    unsigned combinations = 0u;
    CircusDroughtContext c = rental();
    assert(!CircusDroughtRentalBoundaryAllowed(NULL, 1u, 6u));
    for (unsigned saved = 1u; saved <= 6u; ++saved) {
        c.count = (uint8_t)saved;
        for (unsigned ready = 0u; ready < 256u; ++ready)
            for (unsigned count = 0u; count < 256u; ++count) {
                int allowed = ready == 1u && count == 6u;
                assert(CircusDroughtRentalBoundaryAllowed(&c, (uint8_t)ready, (uint8_t)count) == allowed);
                ++combinations;
            }
        completed(&c, 1u, 6u);
    }
    c = rental();
    for (unsigned outcome = 0u; outcome < 256u; ++outcome) {
        c.outcome = (uint8_t)outcome;
        assert(CircusDroughtRentalBoundaryAllowed(&c, 1u, 6u) == (outcome <= 1u));
        ++combinations;
    }
    c = rental();
    c.armed = 1u; rejected(&c, 1u, 6u);
    c = rental(); c.marker = 2u; rejected(&c, 1u, 6u);
    c = rental(); c.snapshot = 0u; rejected(&c, 1u, 6u);
    c = rental(); c.ledger_valid = 0u; rejected(&c, 1u, 6u);
    c = rental(); c.circus = 0u; rejected(&c, 1u, 6u);
    c = rental(); c.weather = 11u; rejected(&c, 1u, 6u);
    c = rental(); c.next_weather = 11u; rejected(&c, 1u, 6u);
    c = rental(); c.ready = 0u; rejected(&c, 1u, 6u);
    c = rental(); c.graphics_loaded = 0u; rejected(&c, 1u, 6u);
    c = rental(); c.callback ^= 1u; rejected(&c, 1u, 6u);
    c = rental(); c.script ^= 1u; rejected(&c, 1u, 6u);
    c = selection(); completed(&c, 0u, 3u); /* 既存phase2/3体guardを委譲。 */
    c.script = 0x09FF4D77u; c.outcome = 1u; completed(&c, 0u, 1u); /* 既存WIN guard。 */
    c = rental(); reset(); stuck = 1u;
    CircusDroughtInitializeRentalBoundary(&c, 1u, 6u, weather, original, init, step);
    assert(originals == 0u && inits == 1u && steps == 256u && weather[0x6D2] == 0u);
    printf("rental_drought_guard combinations=%u ready6-field-boundary PASS\n", combinations);
    return 0;
}
