#ifndef VEGA_CIRCUS_DROUGHT_H
#define VEGA_CIRCUS_DROUGHT_H
#include <stdint.h>
#include <stddef.h>
/* native weather構造の読取と空loaderのcursor2byteだけを所有する。 */
typedef struct {
    uint8_t armed, ledger_valid, circus, marker, snapshot, count, outcome;
    uint8_t weather, next_weather, ready, graphics_loaded;
    uint32_t callback, script;
} CircusDroughtContext;
static inline int CircusDroughtAllowed(const CircusDroughtContext *c)
{
    return c != NULL && c->armed == 1u && c->ledger_valid == 1u && c->circus == 1u
        && c->marker == 2u && c->snapshot == 1u && c->count >= 1u && c->count <= 6u
        && c->outcome == 1u && c->weather == 12u && c->next_weather == 12u
        && c->ready == 1u && c->graphics_loaded == 1u && c->callback == 0x08055E75u
        && (c->script == 0x09FF4D16u || c->script == 0x09FF4D77u || c->script == 0x09FF4DD8u);
}
static inline int CircusDroughtEmptyLoader(volatile uint8_t *w)
{
    /* 0x0807A350のBX LRのみというROM preimageをbuildで確認する。
     * native ResetDroughtWeatherPaletteLoadingが初期化した未処理cursorに限定。
     * 存在しないpaletteを完了扱いにするだけで、weather完了flagは書かない。 */
    if (w[0x6CC] != 2u || w[0x6CD] != 0u || w[0x74D] != 1u || w[0x74E] != 1u)
        return 0;
    w[0x74D] = 32u;
    w[0x74E] = 32u;
    return 1;
}
static inline void CircusDroughtInitialize(const CircusDroughtContext *c,
    volatile uint8_t *w, void (*original)(void), void (*init_vars)(void), void (*step)(void))
{
    unsigned i;
    if (!CircusDroughtAllowed(c)) {
        original();
        return;
    }
    init_vars();
    /* 完了flag/brightnessはnative stepだけが更新する。異常時も無限busy-loopにしない。
     * 上限後は既存Task_WeatherMainの通常frame更新へ委譲し、完了を注入しない。 */
    for (i = 0u; i < 256u && w[0x6D2] == 0u; ++i) {
        CircusDroughtEmptyLoader(w);
        step();
    }
}
#endif
