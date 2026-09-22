#include "pr16_learnset_conditional_bindings.h"
uint8_t pr16_condition_cursor, pr16_condition_mode;
uint16_t pr16_condition_pending;
uint32_t pr16_condition_gives, pr16_condition_archives;
static const uint8_t levels[] = {10,0,1,20,0,50,30,0,100};
static const uint8_t evolution[] = {40,0,20,0};
static const uint8_t reminder[] = {50,0,40,0};
static const uint8_t egg[] = {60,0,70,0};
static const uint8_t shared[] = {70,0,80,0};
uint32_t Pr16ConditionData(const void *mon, int field, uint8_t *ignored)
{
    (void)ignored;
    return mon && field >= 0 && field < 66 ? ((const uint32_t *)mon)[field] : 0;
}
uint16_t Pr16ConditionGive(void *mon, uint16_t move)
{
    uint32_t *fields = mon;
    uint8_t i;
    ++pr16_condition_gives;
    for (i = 0; i < 4; ++i) if (fields[13+i] == move) return 0xFFFEu;
    for (i = 0; i < 4; ++i) if (!fields[13+i]) {
        fields[13+i] = move; fields[17+i] = 5; return move;
    }
    return 0xFFFFu;
}
uint8_t Pr16ConditionView(const uint8_t *image, uint32_t size, uint16_t species,
                         uint8_t family, struct Pr16RuntimeView *view)
{
    (void)image; (void)size;
    view->bytes = (const uint8_t *)0; view->count = 0; view->owner = species;
    if (species != 1u && species != 2u) return species < 1671u ? 2u : 0u;
    if (species == 2u) return 1u; /* 明示空owner。species1の表へ逃がさない。 */
    switch (family) {
    case PR16_CONSUMER_LEVEL_UP: view->bytes=levels; view->count=3; break;
    case PR16_CONSUMER_EVOLUTION: view->bytes=evolution; view->count=2; break;
    case PR16_CONSUMER_REMINDER: view->bytes=reminder; view->count=2; break;
    case PR16_CONSUMER_EGG: view->bytes=egg; view->count=2; break;
    case PR16_CONSUMER_SHARED_EGG: view->bytes=shared; view->count=2; break;
    default: return 0;
    }
    return 1;
}
uint8_t Pr16ConditionArchive(void *mon, uint16_t *moves)
{
    (void)mon;
    ++pr16_condition_archives;
    moves[0] = (uint16_t)(100u + pr16_condition_mode);
    return 1;
}
