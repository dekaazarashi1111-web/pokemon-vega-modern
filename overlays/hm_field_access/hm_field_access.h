#ifndef POKEMON_VEGA_HM_FIELD_ACCESS_H
#define POKEMON_VEGA_HM_FIELD_ACCESS_H

#include <stdint.h>

#if defined(__GNUC__)
#define VEGA_HM_EXPORT __attribute__((used, externally_visible))
#else
#define VEGA_HM_EXPORT
#endif

/*
 * CFRUのfield-move ABIは、0..5を演出主体、6を使用不可として扱う。
 * 解禁の正本はVega既存HMのバッグ所持であり、手持ちは演出主体の選択にだけ使う。
 */
VEGA_HM_EXPORT uint8_t VegaHM_FieldCapability(
    uint16_t move,
    uint16_t ignored_item,
    uint8_t surfing_type
);

VEGA_HM_EXPORT uint8_t VegaHM_SetUpFlash(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpCut(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpFly(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpStrength(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpSurf(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpRockSmash(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpWaterfall(void);
VEGA_HM_EXPORT uint8_t VegaHM_SetUpDive(void);

#endif /* POKEMON_VEGA_HM_FIELD_ACCESS_H */
