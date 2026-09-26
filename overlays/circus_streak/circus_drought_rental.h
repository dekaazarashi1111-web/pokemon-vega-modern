#ifndef VEGA_CIRCUS_DROUGHT_RENTAL_H
#define VEGA_CIRCUS_DROUGHT_RENTAL_H
#include "circus_drought_selection.h"

/* 6体レンタル確定後、最初の3体選出画面へ戻る前のfield境界。
 * owner READYは保存ownerを読む別predicateで検証し、既存ARMED/3体guardと混同しない。 */
static inline int CircusDroughtRentalBoundaryAllowed(const CircusDroughtContext *c,
    uint8_t owner_ready, uint8_t active_count)
{
    return c != NULL && owner_ready == 1u && c->armed == 0u
        && c->ledger_valid == 1u && c->circus == 1u
        && c->marker == 1u && c->snapshot == 1u
        && c->count >= 1u && c->count <= 6u && active_count == 6u
        && c->outcome <= 1u && c->weather == 12u && c->next_weather == 12u
        && c->ready == 1u && c->graphics_loaded == 1u
        && c->callback == 0x08055E75u && c->script == 0x09FF4CB5u;
}

static inline void CircusDroughtInitializeRentalBoundary(const CircusDroughtContext *c,
    uint8_t owner_ready, uint8_t active_count, volatile uint8_t *w,
    void (*original)(void), void (*init_vars)(void), void (*step)(void))
{
    unsigned i;
    if (!CircusDroughtRentalBoundaryAllowed(c, owner_ready, active_count)) {
        CircusDroughtInitializeSelection(c, active_count, w, original, init_vars, step);
        return;
    }
    init_vars();
    for (i = 0u; i < 256u && w[0x6D2] == 0u; ++i) {
        CircusDroughtEmptyLoader(w);
        step();
    }
}
#endif
