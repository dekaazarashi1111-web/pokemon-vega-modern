#ifndef VEGA_CIRCUS_DROUGHT_SELECTION_H
#define VEGA_CIRCUS_DROUGHT_SELECTION_H
#include "circus_drought.h"
/* c->countは退場時に戻すsnapshotの人数。現在選出中の人数と混同しない。
 * snapshot/ledgerの値は変更せず、現在の3体は別の読取値で検証する。 */
static inline int CircusDroughtSelectionAllowed(const CircusDroughtContext *c, uint8_t selected_count)
{
    return c != NULL && c->armed == 1u && c->ledger_valid == 1u && c->circus == 1u
        && c->marker == 2u && c->snapshot == 1u && c->count >= 1u && c->count <= 6u
        && selected_count == 3u && c->outcome == 0u
        && c->weather == 12u && c->next_weather == 12u && c->ready == 1u
        && c->graphics_loaded == 1u && c->callback == 0x08055E75u
        && (c->script == 0x09FF4CEBu || c->script == 0x09FF4D4Cu || c->script == 0x09FF4DADu);
}
static inline void CircusDroughtInitializeSelection(const CircusDroughtContext *c, uint8_t selected_count,
    volatile uint8_t *w, void (*original)(void), void (*init_vars)(void), void (*step)(void))
{
    unsigned i;
    if (!CircusDroughtSelectionAllowed(c, selected_count)) {
        CircusDroughtInitialize(c, w, original, init_vars, step);
        return;
    }
    init_vars();
    for (i = 0u; i < 256u && w[0x6D2] == 0u; ++i) {
        CircusDroughtEmptyLoader(w);
        step();
    }
}
#endif
