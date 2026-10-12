#ifndef VEGA_CIRCUS_DROUGHT_LAUNCH_H
#define VEGA_CIRCUS_DROUGHT_LAUNCH_H
#include "circus_drought.h"
/* 正規party chooserからfieldへ戻る同型3経路。実outcome=0をWINへ偽装しない。
 * 旧WIN predicate/初期化はそのまま保持し、新しいlaunch境界だけを追加する。 */
static inline int CircusDroughtLaunchAllowed(const CircusDroughtContext *c)
{
    return c != NULL && c->armed == 1u && c->ledger_valid == 1u && c->circus == 1u
        && c->marker == 2u && c->snapshot == 1u && c->count == 3u && c->outcome == 0u
        && c->weather == 12u && c->next_weather == 12u && c->ready == 1u
        && c->graphics_loaded == 1u && c->callback == 0x08055E75u
        && (c->script == 0x09FF4CEBu || c->script == 0x09FF4D4Cu || c->script == 0x09FF4DADu);
}
static inline void CircusDroughtInitializeLaunch(const CircusDroughtContext *c,
    volatile uint8_t *w, void (*original)(void), void (*init_vars)(void), void (*step)(void))
{
    unsigned i;
    if (!CircusDroughtLaunchAllowed(c)) {
        CircusDroughtInitialize(c,w,original,init_vars,step);
        return;
    }
    init_vars();
    for (i = 0u; i < 256u && w[0x6D2] == 0u; ++i) {
        CircusDroughtEmptyLoader(w);
        step();
    }
}
#endif
