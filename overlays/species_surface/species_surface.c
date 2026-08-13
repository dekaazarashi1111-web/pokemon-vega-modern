#include "species_surface.h"

#include <string.h>

enum { HOLD_NONE, HOLD_EVERSTONE, HOLD_DESTINY_KNOT, HOLD_POWER_BASE };

uint32_t VegaBreedNext(uint32_t *state)
{
    *state = *state * 1103515245u + 24691u;
    return *state;
}

static uint8_t roll(uint32_t *state, uint8_t limit)
{
    return limit == 0 ? 0 : (uint8_t)(VegaBreedNext(state) % limit);
}

static void add_move(uint16_t moves[VEGA_EGG_MOVES], uint16_t move)
{
    uint8_t i;
    if (move == 0)
        return;
    for (i = 0; i < VEGA_EGG_MOVES; ++i) {
        if (moves[i] == move)
            return;
        if (moves[i] == 0) {
            moves[i] = move;
            return;
        }
    }
}

bool VegaBreed(const struct VegaBreedParent *a, const struct VegaBreedParent *b,
               const struct VegaBreedRules *rules, uint32_t *rng, struct VegaEgg *egg)
{
    const struct VegaBreedParent *line;
    bool chosen[VEGA_BREED_STATS] = {false};
    uint8_t inherited, i, stat;
    if (a == NULL || b == NULL || rules == NULL || rng == NULL || egg == NULL ||
        (a->is_ditto && b->is_ditto))
        return false;
    line = a->is_ditto ? b : a;
    memset(egg, 0, sizeof(*egg));
    egg->species = rules->incense_baby_species != 0 ? rules->incense_baby_species : line->species;
    egg->form = rules->regional_form_from_a ? a->form : line->form;
    egg->nature = rules->everstone_a ? a->nature : (rules->everstone_b ? b->nature : roll(rng, 25));
    egg->ball = line->ball;
    egg->ability_slot = line->hidden_ability && roll(rng, 100) < 60 ? 2 : roll(rng, 2);
    for (i = 0; i < VEGA_BREED_STATS; ++i)
        egg->iv[i] = roll(rng, 32);

    inherited = rules->destiny_knot ? 5 : 3;
    if (rules->power_stat_a < VEGA_BREED_STATS) {
        stat = rules->power_stat_a;
        chosen[stat] = true;
        egg->iv[stat] = a->iv[stat];
        --inherited;
    } else if (rules->power_stat_b < VEGA_BREED_STATS) {
        stat = rules->power_stat_b;
        chosen[stat] = true;
        egg->iv[stat] = b->iv[stat];
        --inherited;
    }
    while (inherited != 0) {
        stat = roll(rng, VEGA_BREED_STATS);
        if (chosen[stat])
            continue;
        chosen[stat] = true;
        egg->iv[stat] = roll(rng, 2) == 0 ? a->iv[stat] : b->iv[stat];
        --inherited;
    }
    for (i = 0; i < VEGA_EGG_MOVES; ++i) {
        add_move(egg->moves, a->egg_moves[i]);
        add_move(egg->moves, b->egg_moves[i]);
        if (a->level_moves[i] != 0 && a->level_moves[i] == b->level_moves[i])
            add_move(egg->moves, a->level_moves[i]);
    }
    /* Masuda-style: different trainer IDs receive six bounded personality rolls. */
    for (i = 0; i < (a->trainer_id != b->trainer_id ? 6 : 1); ++i)
        egg->shiny |= (VegaBreedNext(rng) & 0xFFFFu) == 0;
    return true;
}

bool VegaEggQueuePush(struct VegaEggQueue *queue, const struct VegaEgg *egg)
{
    if (queue == NULL || egg == NULL || queue->count >= VEGA_EGG_QUEUE_CAPACITY)
        return false;
    queue->eggs[queue->count++] = *egg;
    return true;
}

enum VegaEggDelivery VegaEggQueueDeliver(struct VegaEggQueue *queue, uint8_t *party_count,
                                         uint16_t *pc_count, uint16_t pc_capacity)
{
    enum VegaEggDelivery result;
    if (queue == NULL || party_count == NULL || pc_count == NULL || queue->count == 0 ||
        *party_count > VEGA_PARTY_CAPACITY || *pc_count > pc_capacity)
        return VEGA_EGG_INVALID;
    if (*party_count < VEGA_PARTY_CAPACITY) {
        ++*party_count;
        result = VEGA_EGG_TO_PARTY;
    } else if (*pc_count < pc_capacity) {
        ++*pc_count;
        result = VEGA_EGG_TO_PC;
    } else {
        return VEGA_EGG_RETAINED;
    }
    --queue->count;
    if (queue->count != 0)
        memmove(&queue->eggs[0], &queue->eggs[1], queue->count * sizeof(queue->eggs[0]));
    memset(&queue->eggs[queue->count], 0, sizeof(queue->eggs[0]));
    return result;
}

bool VegaOvalCharmUnlocked(uint16_t distinct_official_caught, bool quest_complete)
{
    return distinct_official_caught >= 100 || quest_complete;
}

uint8_t VegaEggSuccessPercent(uint8_t base_percent, bool oval_charm)
{
    uint16_t result = oval_charm ? (uint16_t)base_percent * 2u : base_percent;
    return (uint8_t)(result > 100 ? 100 : result);
}

uint16_t VegaHatchAnimationFrames(enum VegaHatchMode mode)
{
    static const uint16_t frames[] = {240, 72, 0};
    return (unsigned)mode < 3u ? frames[mode] : frames[VEGA_HATCH_NORMAL];
}

bool VegaCompactIvEvPanel(bool pc_right_pane, bool egg, uint8_t stat_index,
                          uint8_t iv, uint16_t ev)
{
    (void)pc_right_pane;
    return stat_index < VEGA_BREED_STATS && iv <= 31 && ev <= 252 && (!egg || ev == 0);
}
