#include "species_surface.h"

#include <assert.h>
#include <string.h>

int main(void)
{
    struct VegaBreedParent a = {0}, b = {0};
    struct VegaBreedRules rules = {0};
    struct VegaEgg egg = {0};
    struct VegaEggQueue queue = {0};
    uint32_t rng = 7;
    uint8_t party = 6;
    uint16_t pc = 0;
    unsigned i;
    a.species = 25; a.form = 2; a.trainer_id = 1; a.nature = 3; a.ball = 4;
    b.species = 25; b.trainer_id = 2; b.nature = 9;
    a.egg_moves[0] = 10; b.egg_moves[0] = 11;
    a.level_moves[0] = b.level_moves[0] = 12;
    for (i = 0; i < VEGA_BREED_STATS; ++i) { a.iv[i] = 31; b.iv[i] = (uint8_t)i; }
    rules.everstone_a = true; rules.destiny_knot = true; rules.regional_form_from_a = true;
    rules.power_stat_a = 0; rules.power_stat_b = 0xFF;
    assert(VegaBreed(&a, &b, &rules, &rng, &egg));
    assert(egg.species == 25 && egg.form == 2 && egg.nature == 3 && egg.iv[0] == 31);
    assert(egg.moves[0] == 10 && egg.moves[1] == 11 && egg.moves[2] == 12);
    for (i = 0; i < VEGA_EGG_QUEUE_CAPACITY; ++i) assert(VegaEggQueuePush(&queue, &egg));
    assert(!VegaEggQueuePush(&queue, &egg));
    assert(VegaEggQueueDeliver(&queue, &party, &pc, 1) == VEGA_EGG_TO_PC);
    assert(party == 6 && pc == 1 && queue.count == 4);
    assert(VegaEggQueueDeliver(&queue, &party, &pc, 1) == VEGA_EGG_RETAINED);
    assert(queue.count == 4); /* full party/box loses and duplicates nothing */
    assert(!VegaOvalCharmUnlocked(99, false));
    assert(VegaOvalCharmUnlocked(100, false));
    assert(VegaOvalCharmUnlocked(0, true));
    assert(VegaOvalCharmUnlocked(100, true));
    assert(VegaEggSuccessPercent(20, true) == 40);
    assert(VegaEggSuccessPercent(80, true) == 100);
    assert(VegaHatchAnimationFrames(VEGA_HATCH_NORMAL) == 240);
    assert(VegaHatchAnimationFrames(VEGA_HATCH_SHORT) == 72);
    assert(VegaHatchAnimationFrames(VEGA_HATCH_SKIP) == 0);
    assert(VegaCompactIvEvPanel(true, false, 5, 31, 252));
    assert(VegaCompactIvEvPanel(false, true, 5, 31, 0));
    assert(!VegaCompactIvEvPanel(false, true, 6, 31, 0));
    return 0;
}
